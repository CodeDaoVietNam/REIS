"""
tests/test_validator.py — 8 test cases bắt buộc từ REIS docs.

Run:
    pytest backend/tests/test_validator.py -v

Gate requirement: TẤT CẢ 8 test phải PASS trước khi viết producer.py.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.ingestion.validator import validate_record, EnvironmentReading


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURE — bộ data hợp lệ dùng chung cho tất cả tests
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def valid_data():
    """Base fixture: 1 record hợp lệ cho province_id=48 (Đồng Nai)."""
    return {
        "province_id": 48,
        "time": datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        "temperature": 32.5,
        "humidity": 75.0,
        "wind_speed": 8.2,
        "precipitation": 0.0,
        "pm2_5": 45.2,
        "pm10": 68.0,
        "aqi": 120,
        "uv_index": 7.5,
    }


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Data hoàn toàn hợp lệ → PASS
# ══════════════════════════════════════════════════════════════════════════════

def test_valid_data_passes(valid_data):
    """Record hợp lệ phải trả về is_valid=True, reading object, err=None."""
    is_valid, reading, err = validate_record(valid_data)

    assert is_valid is True
    assert reading is not None
    assert reading.province_id == 48
    assert reading.temperature == 32.5
    assert reading.aqi == 120
    assert err is None


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Nhiệt độ vượt ngưỡng trên (> 60°C) → REJECT
# ══════════════════════════════════════════════════════════════════════════════

def test_temperature_too_high_rejected(valid_data):
    """temperature=999 → không hợp lệ (max = 60°C)."""
    valid_data["temperature"] = 999.0
    is_valid, reading, err = validate_record(valid_data)

    assert is_valid is False
    assert reading is None
    assert "temperature" in err.lower()


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: AQI âm → REJECT
# ══════════════════════════════════════════════════════════════════════════════

def test_aqi_negative_rejected(valid_data):
    """aqi=-10 → không hợp lệ (AQI min = 0)."""
    valid_data["aqi"] = -10
    is_valid, _, _ = validate_record(valid_data)

    assert is_valid is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Province ID ngoài range 1–63 → REJECT
# ══════════════════════════════════════════════════════════════════════════════

def test_invalid_province_id(valid_data):
    """province_id=100 → chỉ có 63 tỉnh VN, reject."""
    valid_data["province_id"] = 100
    is_valid, _, err = validate_record(valid_data)

    assert is_valid is False
    assert "province_id" in err.lower() or "greater" in err.lower()


def test_province_id_zero_rejected(valid_data):
    """province_id=0 → reject (min = 1)."""
    valid_data["province_id"] = 0
    is_valid, _, err = validate_record(valid_data)
    assert is_valid is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Thiếu field bắt buộc → REJECT
# ══════════════════════════════════════════════════════════════════════════════

def test_missing_required_field():
    """Thiếu province_id và time → reject."""
    incomplete = {"temperature": 32.5}   # chỉ có temperature, thiếu required
    is_valid, _, err = validate_record(incomplete)

    assert is_valid is False


def test_missing_time_field(valid_data):
    """Thiếu time field → reject."""
    del valid_data["time"]
    is_valid, _, err = validate_record(valid_data)
    assert is_valid is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: Optional fields có thể là None → PASS
# ══════════════════════════════════════════════════════════════════════════════

def test_optional_fields_can_be_none(valid_data):
    """Optional fields = None → chấp nhận được, không reject."""
    valid_data["pm2_5"]    = None
    valid_data["no2"]      = None
    valid_data["ozone"]    = None
    valid_data["uv_index"] = None

    is_valid, reading, _ = validate_record(valid_data)

    assert is_valid is True
    assert reading is not None
    assert reading.pm2_5 is None
    assert reading.no2 is None


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: Boundary values — biên dưới và biên trên
# ══════════════════════════════════════════════════════════════════════════════

def test_boundary_values(valid_data):
    """Humidity=0 (biên dưới) → PASS. Humidity=100 (biên trên) → PASS."""

    # Biên dưới
    valid_data["humidity"] = 0.0
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is True

    # Biên trên
    valid_data["humidity"] = 100.0
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is True

    # Vượt biên trên → REJECT
    valid_data["humidity"] = 100.1
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is False


def test_temperature_boundary(valid_data):
    """Temperature -20°C (biên dưới) → PASS. -20.1°C → REJECT."""
    valid_data["temperature"] = -20.0
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is True

    valid_data["temperature"] = -20.1
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 8: PM2.5 lớn nhưng hợp lệ (ô nhiễm nặng) → PASS
# ══════════════════════════════════════════════════════════════════════════════

def test_high_but_valid_pm25(valid_data):
    """PM2.5=999.9 µg/m³ (gần limit) → vẫn hợp lệ (làm sạch 999.9 ≤ 1000)."""
    valid_data["pm2_5"] = 999.9
    is_valid, reading, _ = validate_record(valid_data)

    assert is_valid is True
    assert reading.pm2_5 == 999.9


def test_high_but_valid_pm10(valid_data):
    """PM10=999.9 µg/m³ → hợp lệ."""
    valid_data["pm10"] = 999.9
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is True


def test_high_pm25_rejected(valid_data):
    """PM2.5=1000.1 µg/m³ (vượt limit) → REJECT."""
    valid_data["pm2_5"] = 1000.1
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 9: AQI at boundaries
# ══════════════════════════════════════════════════════════════════════════════

def test_aqi_boundary_valid(valid_data):
    """AQI=0 (min) → PASS. AQI=500 (max) → PASS."""
    valid_data["aqi"] = 0
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is True

    valid_data["aqi"] = 500
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is True


def test_aqi_out_of_range(valid_data):
    """AQI=501 → REJECT."""
    valid_data["aqi"] = 501
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 10: Extra fields (raw_json) → preserved thanks to extra="allow"
# ══════════════════════════════════════════════════════════════════════════════

def test_extra_fields_preserved(valid_data):
    """extra='allow' → raw_json được giữ lại, không bị drop."""
    valid_data["raw_json"] = {"weather": {"temperature_2m": 32.5}}
    is_valid, reading, _ = validate_record(valid_data)

    assert is_valid is True
    assert reading.raw_json is not None
    assert reading.raw_json["weather"]["temperature_2m"] == 32.5


# ══════════════════════════════════════════════════════════════════════════════
# TEST 11: Wind speed = 0 (valid, không có gió)
# ══════════════════════════════════════════════════════════════════════════════

def test_wind_speed_zero_valid(valid_data):
    """wind_speed=0 → valid (lặng gió)."""
    valid_data["wind_speed"] = 0.0
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is True


def test_wind_speed_negative_rejected(valid_data):
    """wind_speed=-1 → reject (không âm được)."""
    valid_data["wind_speed"] = -1.0
    is_valid, _, _ = validate_record(valid_data)
    assert is_valid is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 12: Type coercion — string AQI → int (Pydantic auto-convert)
# ══════════════════════════════════════════════════════════════════════════════

def test_type_coercion_string_to_int(valid_data):
    """Pydantic tự động convert '120' → 120 cho int field."""
    valid_data["aqi"] = "120"    # string thay vì int
    is_valid, reading, _ = validate_record(valid_data)

    # Pydantic v2 coerce được string → int
    assert is_valid is True
    assert reading.aqi == 120
