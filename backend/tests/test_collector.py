"""
tests/test_collector.py — Collector unit tests.

Run:
    pytest backend/tests/test_collector.py -v

Tests:
    1. collect_all_provinces() returns list (not None)
    2. Returns 64 records (hoặc 63 — tùy PROVINCE_COORDS)
    3. All records have required fields
    4. province_id range correct
    5. API response merge correct
"""
from __future__ import annotations

import pytest

from backend.ingestion.collector import collect_all_provinces


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Returns list (not None)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_collector_returns_list():
    """collect_all_provinces() phải trả về list, không phải None."""
    records = await collect_all_provinces()
    assert records is not None
    assert isinstance(records, list)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Returns expected number of records
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_collector_returns_correct_count():
    """
    Số records trả về phải bằng số tỉnh trong PROVINCE_COORDS.
    Đếm keys trong PROVINCE_COORDS thay vì hardcode 64.
    """
    records = await collect_all_provinces()
    from backend.ingestion.collector import PROVINCE_COORDS

    assert len(records) == len(PROVINCE_COORDS), (
        f"Expected {len(PROVINCE_COORDS)} records, got {len(records)}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: All records have required fields
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_all_records_have_required_fields():
    """Mọi record phải có: province_id, time, temperature, humidity, aqi, pm2_5."""
    records = await collect_all_provinces()
    required_fields = ["province_id", "time", "temperature", "humidity", "aqi", "pm2_5"]

    for r in records:
        for field in required_fields:
            assert field in r, f"Missing field '{field}' in record for province {r.get('province_id')}"


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: All province_ids are unique (no duplicates)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_no_duplicate_province_ids():
    """province_id không được trùng lặp."""
    records = await collect_all_provinces()
    province_ids = [r["province_id"] for r in records]

    assert len(province_ids) == len(set(province_ids)), (
        f"Duplicate province_ids found: {province_ids}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Temperature is numeric (not None or string)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_temperature_is_numeric():
    """temperature phải là số, không phải None hoặc string."""
    records = await collect_all_provinces()

    for r in records:
        temp = r.get("temperature")
        if temp is not None:
            assert isinstance(temp, (int, float)), (
                f"Province {r['province_id']}: temperature={temp!r} is not numeric"
            )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: Timestamp is parseable (str hoặc datetime)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_timestamp_is_parseable():
    """time field phải parse được (ISO string hoặc datetime object)."""
    from datetime import datetime

    records = await collect_all_provinces()

    for r in records:
        t = r.get("time")
        assert t is not None, f"Missing time for province {r['province_id']}"

        # Có thể là string hoặc datetime object
        if isinstance(t, str):
            # Thử parse — không raise = OK
            datetime.fromisoformat(t.replace("Z", "+00:00"))
        else:
            assert isinstance(t, datetime)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: AQI is within valid range (0-500 hoặc None)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_aqi_in_valid_range():
    """AQI phải 0-500 (hoặc None cho optional)."""
    records = await collect_all_provinces()

    for r in records:
        aqi = r.get("aqi")
        if aqi is not None:
            assert 0 <= aqi <= 500, (
                f"Province {r['province_id']}: AQI={aqi} out of range [0, 500]"
            )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 8: raw_json field is a dict (được giữ lại cho debug)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_raw_json_is_dict():
    """raw_json phải là dict (chứa response gốc từ API)."""
    records = await collect_all_provinces()

    for r in records:
        raw = r.get("raw_json")
        assert isinstance(raw, dict), (
            f"Province {r['province_id']}: raw_json={type(raw)}, expected dict"
        )
        assert "weather" in raw or "air_quality" in raw, (
            f"Province {r['province_id']}: raw_json missing 'weather' or 'air_quality'"
        )
