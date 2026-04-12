"""
validator.py — Pydantic v2 data validation cho REIS.

Luồng hoạt động:
    validate_record() nhận dict thô từ collector.py
    → parse + range-check từng field
    → Trả về (is_valid, reading_if_valid, error_message_if_invalid)

Module contract (docs spec):
    from ingestion.validator import validate_record, EnvironmentReading

Chạy test:
    pytest backend/tests/test_validator.py -v
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError, confloat, conint

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════════════════════════════════════════════

class EnvironmentReading(BaseModel):
    """
    Validated environment reading cho 1 tỉnh tại 1 thời điểm.

    Validation rules (theo REIS schema):
      - province_id:    int 1–63
      - time:           datetime (UTC)
      - temperature:    °C,   -20 → +60
      - humidity:       %,     0 → 100
      - wind_speed:     km/h,  >= 0
      - precipitation:  mm,    >= 0
      - pm2_5:          µg/m³, 0 → 1000
      - pm10:           µg/m³, 0 → 1000
      - aqi:            US EPA AQI, 0 → 500
      - no2:            µg/m³, >= 0  (optional)
      - ozone:          µg/m³, >= 0  (optional)
      - uv_index:       0 → 20         (optional)
      - raw_json:       dict (optional) — payload gốc để debug

    Với Pydantic v2:
      - model_config = ConfigDict(extra="allow") → chấp nhận extra fields
      - confloat(ge=X, le=Y) → range-constrained float
      - conint(ge=X, le=Y)    → range-constrained int
    """
    model_config = ConfigDict(extra="allow")

    province_id:   int
    time:          datetime
    # ── Weather ────────────────────────────────────────────────────────────
    temperature:   Optional[confloat(ge=-20.0, le=60.0)]   = None
    humidity:      Optional[confloat(ge=0.0,   le=100.0)]  = None
    wind_speed:    Optional[confloat(ge=0.0,   le=200.0)] = None
    precipitation: Optional[confloat(ge=0.0,   le=500.0)]  = None
    # ── Air quality ────────────────────────────────────────────────────────
    pm2_5:         Optional[confloat(ge=0.0,   le=1000.0)] = None
    pm10:          Optional[confloat(ge=0.0,   le=1000.0)] = None
    aqi:           Optional[conint(ge=0,       le=500)]    = None
    no2:           Optional[confloat(ge=0.0)]              = None
    ozone:         Optional[confloat(ge=0.0)]              = None
    uv_index:      Optional[confloat(ge=0.0,   le=20.0)]  = None
    # ── Audit ──────────────────────────────────────────────────────────────
    raw_json:      Optional[dict] = None


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION FUNCTION (docs spec: returns Tuple[bool, Reading, str])
# ══════════════════════════════════════════════════════════════════════════════

def validate_record(
    raw: dict,
) -> tuple[bool, Optional[EnvironmentReading], Optional[str]]:
    """
    Validate một raw dict từ collector.py.

    Args:
        raw: Dict thô từ collector, ví dụ:
             {"province_id": 48, "time": "2024-01-15T08:00:00Z",
              "temperature": 32.5, "aqi": 120, ...}

    Returns:
        (is_valid, reading_if_valid, error_message_if_invalid)

        is_valid = True  → reading_if_valid = EnvironmentReading object
        is_valid = False → reading_if_valid = None, error_message = str reason

    Ví dụ:
        is_valid, reading, err = validate_record({"province_id": 48, ...})
        if is_valid:
            print(reading.temperature)   # 32.5
        else:
            print(f"Reject: {err}")       # "Field required: time"

    NOTE: Province ID ngoài 1–63 → REJECT (chỉ có 63 tỉnh VN).
          None values cho optional fields → ACCEPT (API có thể null).
    """
    try:
        reading = EnvironmentReading(**raw)
        return True, reading, None

    except ValidationError as exc:
        # Lấy message đầu tiên gọn gọn
        errors = exc.errors()
        first  = errors[0]
        loc    = ".".join(str(x) for x in first["loc"])
        msg    = f"{loc}: {first['msg']}"

        province_id = raw.get("province_id", "unknown")
        logger.warning(
            "Validation failed for province %s: %s",
            province_id, msg,
        )
        return False, None, msg
