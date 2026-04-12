"""
tests/test_producer.py — Producer unit tests.

Run:
    pytest backend/tests/test_producer.py -v

Tests:
    1. publish_records() returns {"published": N, "dlq": 0} on success
    2. Kafka error → dlq incremented
    3. Redis DLQ key exists with correct TTL
    4. Empty list → early return {"published": 0, "dlq": 0}
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.ingestion.producer import publish_records


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def valid_reading():
    """1 record hợp lệ cho province_id=48."""
    from backend.ingestion.validator import EnvironmentReading

    return EnvironmentReading(
        province_id=48,
        time=datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        temperature=32.5,
        humidity=75.0,
        wind_speed=8.2,
        precipitation=0.0,
        pm2_5=45.2,
        pm10=68.0,
        aqi=120,
        no2=15.0,
        ozone=45.0,
        uv_index=7.5,
    )


@pytest.fixture
def second_reading():
    """Record thứ 2 cho province_id=1."""
    from backend.ingestion.validator import EnvironmentReading

    return EnvironmentReading(
        province_id=1,
        time=datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        temperature=28.0,
        humidity=70.0,
        wind_speed=12.0,
        precipitation=0.0,
        pm2_5=30.0,
        pm10=50.0,
        aqi=80,
        no2=10.0,
        ozone=40.0,
        uv_index=6.0,
    )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Empty list → early return
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_publish_empty_list():
    """Empty list → return immediately without connecting to Kafka."""
    result = await publish_records([])
    assert result == {"published": 0, "dlq": 0}


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: All records published successfully
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_publish_records_success(valid_reading, second_reading):
    """2 valid records → published=2, dlq=0."""
    with patch("backend.ingestion.producer._get_producer") as mock_prod, \
         patch("backend.ingestion.producer._get_redis") as mock_redis:

        # Mock Kafka producer: send_and_wait succeeds
        prod_instance = AsyncMock()
        prod_instance.send_and_wait = AsyncMock()
        mock_prod.return_value = prod_instance

        # Mock Redis client
        redis_instance = AsyncMock()
        redis_instance.rpush = AsyncMock()
        redis_instance.expire = AsyncMock()
        mock_redis.return_value = redis_instance

        result = await publish_records([valid_reading, second_reading])

    assert result["published"] == 2
    assert result["dlq"] == 0
    assert "published" in result
    assert "dlq" in result


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Kafka error → dlq incremented, Redis DLQ updated
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_kafka_error_routes_to_dlq(valid_reading):
    """Kafka error on send_and_wait → dlq=1, Redis DLQ key written."""
    from aiokafka.errors import KafkaError as RealKafkaError

    with patch("backend.ingestion.producer._get_producer") as mock_prod, \
         patch("backend.ingestion.producer._get_redis") as mock_redis:

        prod_instance = AsyncMock()
        # Simulate KafkaError
        prod_instance.send_and_wait = AsyncMock(
            side_effect=RealKafkaError("broker unavailable")
        )
        mock_prod.return_value = prod_instance

        redis_instance = AsyncMock()
        redis_instance.rpush = AsyncMock()
        redis_instance.expire = AsyncMock()
        mock_redis.return_value = redis_instance

        result = await publish_records([valid_reading])

    assert result["dlq"] == 1
    assert result["published"] == 0
    # Verify DLQ was written
    redis_instance.rpush.assert_called_once()
    call_args = redis_instance.rpush.call_args
    assert call_args[0][0] == "dead_letter_queue"


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Redis DLQ key has correct TTL (7 days)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_dlq_ttl_is_7_days(valid_reading):
    """Redis DLQ TTL = 7 days (604800 seconds)."""
    from aiokafka.errors import KafkaError as RealKafkaError

    with patch("backend.ingestion.producer._get_producer") as mock_prod, \
         patch("backend.ingestion.producer._get_redis") as mock_redis:

        prod_instance = AsyncMock()
        prod_instance.send_and_wait = AsyncMock(
            side_effect=RealKafkaError("broker down")
        )
        mock_prod.return_value = prod_instance

        redis_instance = AsyncMock()
        redis_instance.rpush = AsyncMock()
        redis_instance.expire = AsyncMock()
        mock_redis.return_value = redis_instance

        await publish_records([valid_reading])

    # Verify expire called with 7 days TTL
    redis_instance.expire.assert_called_once()
    ttl_arg = redis_instance.expire.call_args[0][1]
    assert ttl_arg == 7 * 24 * 60 * 60


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Redis DLQ failure → log WARNING, continue (no crash)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_redis_dlq_failure_continues(valid_reading):
    """Redis rpush fails → log WARNING, don't raise, dlq still counted."""
    from aiokafka.errors import KafkaError as RealKafkaError

    with patch("backend.ingestion.producer._get_producer") as mock_prod, \
         patch("backend.ingestion.producer._get_redis") as mock_redis:

        prod_instance = AsyncMock()
        prod_instance.send_and_wait = AsyncMock(
            side_effect=RealKafkaError("broker down")
        )
        mock_prod.return_value = prod_instance

        redis_instance = AsyncMock()
        redis_instance.rpush = AsyncMock(side_effect=ConnectionError("Redis down"))
        mock_redis.return_value = redis_instance

        # Should NOT raise — just log and continue
        result = await publish_records([valid_reading])

    assert result["dlq"] == 1   # Counted even if Redis failed
    assert result["published"] == 0
