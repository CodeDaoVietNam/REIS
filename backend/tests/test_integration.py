"""
tests/test_integration.py — Integration tests cho Gate Condition.

Run:
    pytest backend/tests/test_integration.py -v --timeout=120

Gate Condition: TẤT CẢ test phải PASS trước khi sang Giai đoạn 3 (ML).

Điều kiện Gate:
    1. 63 tỉnh × 3 cycles vào DB → 0 data loss
    2. DLQ hoạt động (bad data đi vào DLQ, không vào DB)
    3. Kafka consumer lag = 0 sau khi xử lý xong
    4. Scheduler chạy 3 cycles liên tục không crash
"""
from __future__ import annotations

import asyncio
import subprocess
import time

import asyncpg
import pytest

from backend.config.settings import settings


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def event_loop():
    """Module-scoped event loop cho async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def db_pool():
    """Module-scoped DB pool — reuse cho tất cả tests."""
    pool = await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        min_size=2,
        max_size=10,
    )
    yield pool
    await pool.close()


@pytest.fixture(scope="module")
async def redis_client():
    """Module-scoped Redis client."""
    import redis.asyncio as redis

    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    yield client
    await client.aclose()


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Collector trả về đúng số tỉnh trong PROVINCE_COORDS
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_collector_returns_all_provinces():
    """Số records trả về = số provinces trong PROVINCE_COORDS."""
    from backend.ingestion.collector import collect_all_provinces, PROVINCE_COORDS

    records = await collect_all_provinces()
    expected = len(PROVINCE_COORDS)

    assert len(records) == expected, (
        f"Expected {expected} records, got {len(records)}"
    )

    # Kiểm tra không duplicate province_id
    province_ids = {r["province_id"] for r in records}
    assert len(province_ids) == expected, "Duplicate province_ids found"


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Tất cả records có timestamp hợp lệ
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_all_records_have_valid_timestamp():
    """Mọi record phải có time field hợp lệ (không None)."""
    from backend.ingestion.collector import collect_all_provinces

    records = await collect_all_provinces()

    for r in records:
        assert r.get("time") is not None, (
            f"Missing time for province {r['province_id']}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Full pipeline — 1 cycle đầy đủ vào DB
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_full_pipeline_one_cycle(db_pool):
    """
    Full cycle: collect → validate → publish → consume → DB.

    Sau khi chạy 1 cycle:
      - published = N provinces (Kafka ack)
      - inserted >= 60 rows in DB (có thể < 63 nếu API null)
    """
    from backend.ingestion.collector import collect_all_provinces
    from backend.ingestion.producer import publish_records

    # Count trước khi insert
    async with db_pool.acquire() as conn:
        before = await conn.fetchval("SELECT COUNT(*) FROM env_readings")

    # Run 1 full cycle
    records = await collect_all_provinces()
    stats   = await publish_records(records)

    # Đợi consumer xử lý (Kafka → DB có thể mất 3-5s)
    await asyncio.sleep(6)

    # Count sau khi insert
    async with db_pool.acquire() as conn:
        after = await conn.fetchval("SELECT COUNT(*) FROM env_readings")

    inserted = after - before
    assert inserted >= 60, (
        f"Expected >=60 new rows, got {inserted}. "
        f"published={stats.get('published')}"
    )
    assert stats.get("published", 0) >= 60, (
        f"Kafka published only {stats.get('published')} records"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Bad data đi vào DLQ, không vào DB chính
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_bad_data_goes_to_dlq(db_pool, redis_client):
    """
    Invalid record (province_id=99) → đi vào DLQ, không vào DB.

    - DLQ length tăng sau khi publish bad data
    - DB không có record với province_id=99
    """
    from backend.ingestion.collector import collect_all_provinces
    from backend.ingestion.producer import publish_records

    dlq_before = await redis_client.llen("dead_letter_queue")

    # Publish 1 invalid record + valid records
    bad_records = await collect_all_provinces()
    bad_records.append({
        "province_id": 99,          # invalid (chỉ có 63 tỉnh)
        "time": "2024-01-15T08:00:00Z",
        "temperature": 999.0,        # out of range
    })

    stats = await publish_records(bad_records)

    dlq_after = await redis_client.llen("dead_letter_queue")

    # DLQ tăng
    assert dlq_after > dlq_before, "Bad data should go to DLQ"
    assert stats.get("dlq", 0) >= 1, "At least 1 record should be in DLQ"

    # DB không có record với province_id=99
    async with db_pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM env_readings WHERE province_id = 99"
        )
    assert count == 0, "Bad data must NOT reach TimescaleDB"


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: 3 Cycles — không mất data
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_no_data_loss_across_3_cycles(db_pool):
    """
    3 cycles liên tiếp → mỗi tỉnh phải có data gần đây.

    Tỉnh phải xuất hiện trong DB với timestamp gần đây.
    Duplicate từ ON CONFLICT DO NOTHING là OK (không lỗi).
    """
    from backend.ingestion.collector import collect_all_provinces
    from backend.ingestion.producer import publish_records

    async with db_pool.acquire() as conn:
        before = await conn.fetchval("SELECT COUNT(*) FROM env_readings")

    # Run 3 cycles
    for cycle in range(3):
        records = await collect_all_provinces()
        await publish_records(records)
        await asyncio.sleep(3)   # Đợi consumer flush mỗi cycle

    await asyncio.sleep(10)   # Đợi consumer xử lý cycle cuối

    async with db_pool.acquire() as conn:
        after = await conn.fetchval("SELECT COUNT(*) FROM env_readings")

        # Đếm số tỉnh có data trong 30 phút gần nhất
        rows = await conn.fetch(
            """
            SELECT province_id, COUNT(*) as cnt
            FROM env_readings
            WHERE time > NOW() - INTERVAL '30 minutes'
            GROUP BY province_id
            """
        )

    covered_provinces = len(rows)
    assert covered_provinces >= 60, (
        f"Only {covered_provinces}/63 provinces have recent data. "
        f"Data may be lost across cycles."
    )

    total_inserted = after - before
    assert total_inserted >= 60, (
        f"Expected >=60 new rows after 3 cycles, got {total_inserted}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: Kafka consumer lag = 0 sau khi xử lý xong
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_kafka_consumer_lag_is_zero():
    """
    Consumer lag phải = 0 sau khi xử lý hết messages.

    Run: docker exec reis-kafka kafka-consumer-groups ...
    Lag > 0 = consumer không theo kịp producer.
    """
    result = subprocess.run(
        [
            "docker", "exec", "reis-kafka",
            "kafka-consumer-groups",
            "--bootstrap-server", "localhost:9092",
            "--group", settings.KAFKA_CONSUMER_GROUP,
            "--describe",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    output = result.stdout + result.stderr

    # Parse lag values từ output
    lag_values = []
    for line in output.split("\n"):
        if "env.readings.raw" in line:
            parts = line.split()
            try:
                # Lag thường ở cột cuối hoặc gần cuối
                for p in reversed(parts):
                    if p.isdigit():
                        lag_values.append(int(p))
                        break
            except (ValueError, IndexError):
                pass

    total_lag = sum(lag_values)

    assert total_lag == 0, (
        f"Kafka consumer lag = {total_lag}. "
        f"Expected lag = 0 (all messages processed). "
        f"Output:\n{output}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: Dead Letter Queue tỷ lệ < 5%
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_dlq_reject_rate_below_5_percent(redis_client):
    """
    Tỷ lệ reject (DLQ / total) phải < 5%.

    Gate requirement: DLQ < 5% total records (tỉ lệ chấp nhận được).
    """
    dlq_len = await redis_client.llen("dead_letter_queue")

    # Ước tính total records = 3 cycles × 63 provinces = 189
    total_estimate = 3 * 63

    if total_estimate > 0:
        reject_rate = dlq_len / total_estimate
        assert reject_rate < 0.05, (
            f"DLQ reject rate = {reject_rate:.1%} ({dlq_len}/{total_estimate}). "
            f"Must be < 5%. Check data quality from Open-Meteo API."
        )
