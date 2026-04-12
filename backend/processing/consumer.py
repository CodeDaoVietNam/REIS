"""
consumer.py — Kafka consumer: đọc messages từ topic, insert vào TimescaleDB.

Luồng hoạt động:
    1. Subscribe to Kafka topic: env.readings.raw
    2. Poll messages liên tục
    3. Batch 63 records (1 full cycle) → insert vào TimescaleDB
    4. Commit Kafka offset CHỈ SAU KHI insert thành công (at-least-once)
    5. On shutdown: flush remaining batch trước khi exit

Chạy độc lập:
    python backend/processing/consumer.py
Chạy như module (from FastAPI lifespan):
    from processing.consumer import run_consumer
"""
from __future__ import annotations

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

# ── Add project root to sys.path ───────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.settings import settings

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

KAFKA_TOPIC       = "env.readings.raw"
KAFKA_GROUP_ID    = settings.KAFKA_CONSUMER_GROUP  # "reis-consumer-group"
KAFKA_BOOTSTRAP   = settings.KAFKA_BOOTSTRAP_SERVERS

# TimescaleDB config
DB_HOST     = settings.DB_HOST
DB_PORT     = settings.DB_PORT
DB_USER     = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD
DB_NAME     = settings.DB_NAME

# Batch settings
BATCH_SIZE        = 63    # 1 full cycle = 63 provinces
BATCH_TIMEOUT_SEC = 10    # Flush sau 10s dù batch chưa đầy

# ══════════════════════════════════════════════════════════════════════════════
# SQL — INSERT (docs spec: ON CONFLICT DO NOTHING)
# ══════════════════════════════════════════════════════════════════════════════

INSERT_SQL = """
    INSERT INTO env_readings (
        time, province_id,
        temperature, humidity, wind_speed, precipitation,
        pm2_5, pm10, aqi, no2, ozone, uv_index,
        anomaly_score, is_anomaly,
        raw_json,
        inserted_at
    ) VALUES (
        $1,  $2,  $3,  $4,  $5,  $6,
        $7,  $8,  $9,  $10, $11, $12,
        $13, $14,
        $15,
        $16
    )
    ON CONFLICT DO NOTHING;
"""
# anomaly_score = NULL (set later by ML pipeline)
# is_anomaly    = FALSE  (set later by ML pipeline)
# inserted_at   = NOW()

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

async def _get_pool() -> asyncpg.Pool:
    """Create (or return cached) asyncpg connection pool."""
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            min_size=2,
            max_size=10,
        )
        logger.info(
            "TimescaleDB pool created — %s:%s/%s",
            DB_HOST, DB_PORT, DB_NAME,
        )
    return _pool


_pool: asyncpg.Pool | None = None


def _msg_to_tuple(data: dict) -> tuple:
    """Convert Kafka JSON message → tuple cho executemany."""
    now = datetime.now(timezone.utc)
    return (
        # ── Identifiers ─────────────────────────────────────────────────
        data.get("time"),          # $1  TIMESTAMPTZ
        data.get("province_id"),   # $2  INT
        # ── Weather ─────────────────────────────────────────────────────
        data.get("temperature"),   # $3  FLOAT4
        data.get("humidity"),      # $4  FLOAT4
        data.get("wind_speed"),    # $5  FLOAT4
        data.get("precipitation"),# $6  FLOAT4
        # ── Air quality ──────────────────────────────────────────────────
        data.get("pm2_5"),         # $7  FLOAT4
        data.get("pm10"),          # $8  FLOAT4
        data.get("aqi"),           # $9  INT
        data.get("no2"),           # $10 FLOAT4
        data.get("ozone"),         # $11 FLOAT4
        data.get("uv_index"),      # $12 FLOAT4
        # ── ML pipeline (set later) ──────────────────────────────────────
        None,                      # $13 anomaly_score
        False,                     # $14 is_anomaly
        # ── Audit ────────────────────────────────────────────────────────
        json.dumps(data.get("raw_json")) if data.get("raw_json") else None,  # $15 JSONB
        now,                       # $16 inserted_at TIMESTAMPTZ
    )


async def _flush_batch(
    pool: asyncpg.Pool,
    consumer: AIOKafkaConsumer,
    batch: list[tuple],
) -> None:
    """
    Insert batch vào TimescaleDB, rồi commit Kafka offset.

    CRITICAL: Commit offset CHỈ SAU KHI insert thành công.
    → Nếu DB lỗi, consumer sẽ đọc lại messages từ offset cũ (không mất data).
    → Đây là at-least-once delivery guarantee.
    """
    if not batch:
        return

    async with pool.acquire() as conn:
        await conn.executemany(INSERT_SQL, batch)

    # Commit offset SAU KHI DB insert thành công
    await consumer.commit()
    logger.info("Flushed %d records to TimescaleDB — offset committed", len(batch))


# ══════════════════════════════════════════════════════════════════════════════
# CONSUMER LOOP
# ══════════════════════════════════════════════════════════════════════════════

async def consume() -> None:
    """
    Kafka consumer loop chạy vĩnh viễn cho đến khi SIGTERM.

    Key behaviors:
        - auto_offset_reset="latest" (production rule)
        - enable_auto_commit=False (manual commit only)
        - Skip unparseable messages (log + commit) → không stall
        - Graceful shutdown: flush remaining batch + commit offset
    """
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="latest",    # Production: đọc từ message mới nhất
        enable_auto_commit=False,       # Manual commit only
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        session_timeout_ms=30000,
        heartbeat_interval_ms=10000,
    )
    await consumer.start()
    logger.info(
        "Consumer started — topic=%s, group=%s",
        KAFKA_TOPIC, KAFKA_GROUP_ID,
    )

    pool  = await _get_pool()
    batch: list[tuple] = []
    batch_start_time   = asyncio.get_event_loop().time()

    try:
        async for msg in consumer:
            try:
                # Parse + basic sanity check
                data = msg.value
                if not isinstance(data, dict):
                    raise ValueError(f"Expected dict, got {type(data)}")

            except (json.JSONDecodeError, ValueError) as exc:
                # Unparseable message → skip, commit offset (không stall)
                logger.warning(
                    "Skipping unparseable message at offset %s: %s",
                    msg.offset, exc,
                )
                await consumer.commit()
                continue

            # Thêm vào batch
            batch.append(_msg_to_tuple(data))

            now         = asyncio.get_event_loop().time()
            elapsed     = now - batch_start_time
            is_full     = len(batch) >= BATCH_SIZE
            is_timedout = elapsed >= BATCH_TIMEOUT_SEC

            if is_full or is_timedout:
                await _flush_batch(pool, consumer, batch)
                batch.clear()
                batch_start_time = now

    finally:
        # ── Graceful shutdown: flush remaining ──────────────────────────
        if batch:
            await _flush_batch(pool, consumer, batch)
            logger.info("Flushed %d remaining records on shutdown", len(batch))

        await consumer.stop()
        logger.info("Consumer stopped")


# ══════════════════════════════════════════════════════════════════════════════
# GRACEFUL SHUTDOWN + ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

shutdown_event = asyncio.Event()


def _sigterm_handler(signum, frame) -> None:
    logger.info("SIGTERM received — consumer will flush and exit")
    shutdown_event.set()


async def run_consumer() -> None:
    """
    Chạy consumer như background task (gọi từ FastAPI lifespan).

    Usage:
        task = asyncio.create_task(run_consumer())
        # Consumer chạy nền trong event loop
    """
    signal.signal(signal.SIGTERM, _sigterm_handler)

    try:
        await consume()
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by KeyboardInterrupt")


async def run_standalone() -> None:
    """
    Chạy consumer như standalone process.

    Usage:
        python backend/processing/consumer.py
    """
    logger.info("Starting standalone consumer process...")
    signal.signal(signal.SIGTERM, _sigterm_handler)

    try:
        await consume()
    finally:
        if _pool is not None:
            await _pool.close()
            logger.info("Database pool closed")


if __name__ == "__main__":
    asyncio.run(run_standalone())
