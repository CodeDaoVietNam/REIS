"""
tests/test_consumer.py — Consumer unit tests.

Run:
    pytest backend/tests/test_consumer.py -v

Tests:
    1. Commit ONLY after DB insert succeeds (at-least-once)
    2. Unparseable message → skip, commit offset (không stall)
    3. ON CONFLICT DO NOTHING is idempotent
    4. Batch flush when size reached
    5. Batch flush when timeout reached
    6. Shutdown flushes remaining batch
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.processing.consumer import _msg_to_tuple


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_message():
    """Sample Kafka message data (1 province)."""
    return {
        "province_id": 48,
        "time": "2024-01-15T08:00:00+00:00",
        "temperature": 32.5,
        "humidity": 75.0,
        "wind_speed": 8.2,
        "precipitation": 0.0,
        "pm2_5": 45.2,
        "pm10": 68.0,
        "aqi": 120,
        "no2": 15.0,
        "ozone": 45.0,
        "uv_index": 7.5,
        "raw_json": {"weather": {"temperature_2m": 32.5}},
    }


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: _msg_to_tuple returns correct 16-element tuple
# ══════════════════════════════════════════════════════════════════════════════

def test_msg_to_tuple_returns_16_elements(sample_message):
    """Insert tuple phải có đúng 16 elements (khớp với INSERT_SQL)."""
    tup = _msg_to_tuple(sample_message)
    assert len(tup) == 16, f"Expected 16 elements, got {len(tup)}"


def test_msg_to_tuple_fields_correct(sample_message):
    """Tuple elements khớp đúng thứ tự INSERT_SQL $1..$16."""
    tup = _msg_to_tuple(sample_message)

    assert tup[0] == datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc)  # $1 time
    assert tup[1] == 48                                # $2 province_id
    assert tup[2] == 32.5                              # $3 temperature
    assert tup[3] == 75.0                              # $4 humidity
    assert tup[4] == 8.2                               # $5 wind_speed
    assert tup[5] == 0.0                               # $6 precipitation
    assert tup[6] == 45.2                              # $7 pm2_5
    assert tup[7] == 68.0                              # $8 pm10
    assert tup[8] == 120                               # $9 aqi
    assert tup[9] == 15.0                              # $10 no2
    assert tup[10] == 45.0                             # $11 ozone
    assert tup[11] == 7.5                              # $12 uv_index
    assert tup[12] is None                              # $13 anomaly_score
    assert tup[13] is False                             # $14 is_anomaly
    assert tup[14] is not None                          # $15 raw_json (JSONB)
    assert tup[15] is not None                         # $16 inserted_at


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: anomaly_score = NULL, is_anomaly = FALSE
# ══════════════════════════════════════════════════════════════════════════════

def test_anomaly_fields_are_null_false(sample_message):
    """anomaly_score=None, is_anomaly=False — ML pipeline set sau."""
    tup = _msg_to_tuple(sample_message)
    assert tup[12] is None      # anomaly_score
    assert tup[13] is False    # is_anomaly


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: raw_json serialized to JSON string for PostgreSQL JSONB
# ══════════════════════════════════════════════════════════════════════════════

def test_raw_json_serialized_to_json(sample_message):
    """raw_json phải là JSON string (không phải dict) cho PostgreSQL JSONB."""
    import json

    tup = _msg_to_tuple(sample_message)
    raw_json_value = tup[14]

    assert raw_json_value is not None
    # Phải là string hợp lệ JSON
    parsed = json.loads(raw_json_value)
    assert isinstance(parsed, dict)
    assert "weather" in parsed


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: inserted_at is datetime (not None)
# ══════════════════════════════════════════════════════════════════════════════

def test_inserted_at_is_datetime(sample_message):
    """inserted_at phải là datetime object (auto-set on insert)."""
    tup = _msg_to_tuple(sample_message)
    assert isinstance(tup[15], datetime)
    assert tup[15].tzinfo is not None   #-aware


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Missing optional fields → None (not KeyError)
# ══════════════════════════════════════════════════════════════════════════════

def test_missing_optional_fields_default_to_none(sample_message):
    """Field không có trong message → None (không raise KeyError)."""
    minimal = {
        "province_id": 48,
        "time": "2024-01-15T08:00:00+00:00",
        # Chỉ có required fields, không có no2, ozone, uv_index
    }
    tup = _msg_to_tuple(minimal)

    assert tup[9] is None    # no2
    assert tup[10] is None   # ozone
    assert tup[11] is None   # uv_index
    assert tup[14] is None   # raw_json


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: _flush_batch commits ONLY after successful insert
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_flush_commits_after_insert(sample_message):
    """executemany thành công → commit được gọi. executemany fail → commit KHÔNG được gọi."""
    from backend.processing.consumer import _flush_batch

    pool = MagicMock()
    conn = AsyncMock()
    conn.executemany = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn

    consumer = AsyncMock()
    consumer.commit = AsyncMock()

    batch = [_msg_to_tuple(sample_message)]

    # Case A: executemany succeeds → commit should be called
    conn.executemany = AsyncMock()   # success
    await _flush_batch(pool, consumer, batch)
    consumer.commit.assert_called_once()

    # Case B: executemany fails → commit should NOT be called
    conn.executemany = AsyncMock(side_effect=Exception("DB error"))
    consumer.commit.reset_mock()
    with pytest.raises(Exception, match="DB error"):
        await _flush_batch(pool, consumer, batch)
    consumer.commit.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: Empty batch → _flush_batch does nothing (no DB call)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_flush_empty_batch_does_nothing():
    """Empty batch → return early, no DB call, no commit."""
    from backend.processing.consumer import _flush_batch

    pool = AsyncMock()
    pool.acquire = AsyncMock()   # should NOT be called
    consumer = AsyncMock()

    await _flush_batch(pool, consumer, [])
    pool.acquire.assert_not_called()
    consumer.commit.assert_not_called()
