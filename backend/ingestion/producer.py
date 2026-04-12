"""
producer.py — Đẩy validated readings lên Kafka, route failures vào Redis DLQ.

Luồng hoạt động:
    1. Nhận list[EnvironmentReading] từ validator
    2. Serialize mỗi record → JSON → Kafka topic env.readings.raw
    3. Partition key = province_id → ordering guarantee per province
    4. Nếu Kafka lỗi → push record vào Redis DLQ (dlq:env.readings)
    5. Trả về {"published": N, "dlq": M}

Chạy độc lập:
    python producer.py
Chạy như module:
    from ingestion.producer import publish_records, close
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import redis.asyncio as redis
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

if TYPE_CHECKING:
    from ingestion.validator import EnvironmentReading

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# CẤU HÌNH KAFKA + REDIS
# ══════════════════════════════════════════════════════════════════════════════

KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC              = "env.readings.raw"
KAFKA_CLIENT_ID          = "reis-producer"

REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
DLQ_KEY           = "dead_letter_queue"
DLQ_TTL_SECONDS   = 7 * 24 * 60 * 60  # 7 days

# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON — Kafka Producer + Redis Client
# ══════════════════════════════════════════════════════════════════════════════

_producer: AIOKafkaProducer | None = None
_redis_client: redis.Redis | None = None


async def _get_producer() -> AIOKafkaProducer:
    """Lazily start và return AIOKafkaProducer singleton."""
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            client_id=KAFKA_CLIENT_ID,
            # Serialize value thành JSON bytes
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            # Serialize key (province_id) thành bytes
            key_serializer=lambda k: str(k).encode("utf-8"),
            # Đợi acknowledgment từ tất cả replicas
            acks="all",
            retries=3,
        )
        await _producer.start()
        logger.info("Kafka producer started — bootstrap: %s", KAFKA_BOOTSTRAP_SERVERS)
    return _producer


async def _get_redis() -> redis.Redis:
    """Lazily connect và return Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,   # Trả về string thay vì bytes
        )
        logger.info("Redis client connected — %s:%s", REDIS_HOST, REDIS_PORT)
    return _redis_client


# ══════════════════════════════════════════════════════════════════════════════
# HÀM CHÍNH: PUBLISH RECORDS
# ══════════════════════════════════════════════════════════════════════════════

async def publish_records(
    records: list[EnvironmentReading],
) -> dict[str, int]:
    """
    Publish validated readings lên Kafka; route failures vào Redis DLQ.

    Partitioning:
        key = str(province_id) → tất cả readings cho 1 tỉnh cùng partition
        → Consumer nhận đúng thứ tự cho mỗi tỉnh

    Error handling:
        - KafkaError / SerializationError → push to Redis DLQ, continue
        - Redis DLQ push failure → log WARNING, continue (DLQ is best-effort)
        - Record không bị mất — luôn có place để lưu

    Args:
        records: List[EnvironmentReading] từ validator

    Returns:
        {"published": N, "dlq": M}
        - published: số record gửi thành công lên Kafka
        - dlq: số record bị route vào Redis DLQ (Kafka thất bại)
    """
    if not records:
        logger.info("No records to publish")
        return {"published": 0, "dlq": 0}

    producer = await _get_producer()
    redis_client = await _get_redis()

    published = 0
    dlq = 0

    for reading in records:
        # Key = province_id (string bytes) → partition routing
        key   = str(reading.province_id).encode("utf-8")
        # Value = JSON bytes
        value = reading.model_dump_json().encode("utf-8")

        try:
            # send_and_wait: đợi acknowledgment từ Kafka trước khi tiếp tục
            # Nếu không dùng _wait → fire-and-forget (có thể mất message)
            await producer.send_and_wait(KAFKA_TOPIC, value=value, key=key)
            published += 1

        except (KafkaError, TypeError, ValueError) as exc:
            # Kafka gửi thất bại → không drop record → route vào DLQ
            logger.warning(
                "Kafka publish failed for province_id=%d: %s — routing to DLQ",
                reading.province_id, exc,
            )

            dlq_payload = {
                "record":    reading.model_dump(mode="json"),
                "error":     str(exc),
                "pushed_at": datetime.now(timezone.utc).isoformat(),
            }

            try:
                # rpush: thêm vào cuối list (FIFO queue)
                await redis_client.rpush(DLQ_KEY, json.dumps(dlq_payload, default=str))
                # Set TTL: tự động xóa sau 7 ngày
                await redis_client.expire(DLQ_KEY, DLQ_TTL_SECONDS)
            except Exception as redis_exc:
                # Redis DLQ cũng fail → log nhưng KHÔNG retry
                # (tránh infinite loop khi Redis down)
                logger.warning(
                    "Redis DLQ push failed for province_id=%d: %s",
                    reading.province_id, redis_exc,
                )

            dlq += 1

    logger.info(
        "Published %d/%d records to Kafka, %d routed to DLQ",
        published, len(records), dlq,
    )
    return {"published": published, "dlq": dlq}


# ══════════════════════════════════════════════════════════════════════════════
# GRACEFUL SHUTDOWN
# ══════════════════════════════════════════════════════════════════════════════

async def close() -> None:
    """
    Clean shutdown Kafka producer + Redis connection.

    Gọi khi:
        - Scheduler nhận SIGTERM
        - FastAPI app shutdown
        - Bất kỳ graceful exit nào
    """
    global _producer, _redis_client

    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT — Test trực tiếp
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timezone
    from ingestion.validator import EnvironmentReading

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    async def _test():
        # Tạo 2 fake records để test
        test_records = [
            EnvironmentReading(
                province_id=1,
                time=datetime.now(timezone.utc),
                temperature=28.5,
                humidity=75.0,
                wind_speed=12.0,
                precipitation=0.0,
                pm2_5=35.0,
                pm10=60.0,
                aqi=80,
                no2=15.0,
                ozone=45.0,
                uv_index=6.0,
            ),
            EnvironmentReading(
                province_id=48,
                time=datetime.now(timezone.utc),
                temperature=32.0,
                humidity=65.0,
                wind_speed=8.0,
                precipitation=0.0,
                pm2_5=120.0,
                pm10=180.0,
                aqi=165,
                no2=40.0,
                ozone=60.0,
                uv_index=8.0,
            ),
        ]

        print(f"Publishing {len(test_records)} test records...")
        result = await publish_records(test_records)
        print(f"Result: {result}")
        await close()

    asyncio.run(_test())
