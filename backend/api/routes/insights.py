from __future__ import annotations

import logging
from typing import Any

import asyncpg
from fastapi import APIRouter, Request

from backend.api.db import get_pool
from backend.api.inference_cache import get_cached_inference
from backend.api.rate_limit import general_limiter, insight_limiter
from backend.api.routes.provinces import (
    ANOMALY_SCORE_THRESHOLD,
    _reading_to_dict,
    enrich_readings_with_anomaly,
    fetch_current_reading,
    fetch_latest_readings,
    province_meta,
)
from backend.config.constants import STRICT_ALERT_AQI
from backend.insights.insight_cache import get_or_create_insight
from backend.models.predict import DEFAULT_ANOMALY, DEFAULT_FORECAST

logger = logging.getLogger(__name__)

router = APIRouter(tags=["insights"])


def _float_or_zero(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _default_current(province_id: int) -> dict[str, Any]:
    meta = province_meta(province_id)
    return {
        "province_id": province_id,
        "province_name": meta["name_vi"],
        "aqi": None,
        "pm2_5": None,
        "pm10": None,
        "temp": None,
        "humidity": None,
        "raw_json": {},
    }


def _classify_alert_event(reading: dict[str, Any], *, forced_ai: bool = False) -> dict[str, Any]:
    aqi = _float_or_zero(reading.get("aqi"))
    pm25 = _float_or_zero(reading.get("pm2_5"))
    anomaly_score = _float_or_zero(reading.get("anomaly_score"))
    is_aqi_warning = aqi >= STRICT_ALERT_AQI
    is_ai_anomaly = forced_ai or reading.get("is_anomaly") is True or anomaly_score >= ANOMALY_SCORE_THRESHOLD

    if is_aqi_warning and is_ai_anomaly:
        event_type = "combined"
    elif is_ai_anomaly:
        event_type = "ai_anomaly"
    else:
        event_type = "aqi_warning"

    if aqi >= 200 or pm25 >= 90 or anomaly_score >= 0.9:
        severity = "critical"
    elif aqi >= STRICT_ALERT_AQI or anomaly_score >= ANOMALY_SCORE_THRESHOLD:
        severity = "high"
    else:
        severity = "moderate"

    if event_type == "combined":
        reason = (
            f"AQI {aqi:.0f} vuot nguong suc khoe va model dong thoi phat hien pattern bat thuong "
            f"(score {anomaly_score:.2f})."
        )
    elif event_type == "ai_anomaly":
        reason = f"Model phat hien pattern moi truong bat thuong voi anomaly score {anomaly_score:.2f}."
    else:
        reason = f"AQI {aqi:.0f} vuot nguong canh bao suc khoe {STRICT_ALERT_AQI}."

    recommendations = _recommendations_for_alert(event_type, severity)
    return {
        "event_type": event_type,
        "severity": severity,
        "reason": reason,
        "recommendations": recommendations,
    }


def _recommendations_for_alert(event_type: str, severity: str) -> list[str]:
    if severity == "critical":
        return [
            "Han che ra ngoai neu khong can thiet, dac biet voi tre em va nguoi co benh ho hap.",
            "Dong cua so, bat may loc khong khi neu co.",
            "Neu phai di chuyen, uu tien khau trang loc bui min PM2.5.",
        ]

    if event_type == "ai_anomaly":
        return [
            "Theo doi them 1-2 chu ky du lieu de xac nhan bat thuong co lap lai khong.",
            "Kiem tra dong thoi AQI, PM2.5, gio va nhiet do truoc khi ket luan nguyen nhan.",
            "Nguoi nhay cam nen giam hoat dong ngoai troi trong giai doan bat thuong.",
        ]

    return [
        "Nguoi nhay cam nen giam thoi gian ngoai troi.",
        "Theo doi AQI trong cac gio cao diem giao thong.",
        "Can nhac dung khau trang loc bui min khi di chuyen.",
    ]


def _build_alert_record(
    province: dict[str, Any],
    reading: dict[str, Any],
    *,
    forced_ai: bool = False,
) -> dict[str, Any]:
    alert = _classify_alert_event(reading, forced_ai=forced_ai)
    return {
        "province": province,
        "reading": reading,
        **alert,
    }


@router.get("/api/insights/{province_id}")
async def get_insight(province_id: int, request: Request) -> dict[str, Any]:
    insight_limiter.check(request)  # 10 req/min — LLM calls are expensive
    province_meta(province_id)
    pool = get_pool(request)

    try:
        current = await fetch_current_reading(pool, province_id)
    except Exception as exc:
        logger.warning("Insight current-reading fallback for province %s: %s", province_id, exc)
        current = None

    try:
        if current:
            inference, _source = await get_cached_inference(province_id, pool=pool)
        else:
            inference, _source = {"anomaly": DEFAULT_ANOMALY, "forecast": DEFAULT_FORECAST}, "default"
    except Exception as exc:
        logger.warning("Insight inference fallback for province %s: %s", province_id, exc)
        inference = {"anomaly": DEFAULT_ANOMALY, "forecast": DEFAULT_FORECAST}

    try:
        insight = await get_or_create_insight(
            province_id=province_id,
            current=current or _default_current(province_id),
            anomaly=inference.get("anomaly", DEFAULT_ANOMALY),
            forecast=inference.get("forecast", DEFAULT_FORECAST),
        )
    except Exception as exc:
        logger.warning("Insight generation fallback for province %s: %s", province_id, exc)
        insight = {
            "summary": "Chua co du lieu thoi gian thuc cho tinh nay.",
            "health_advice": "Theo doi bang dieu khien va kiem tra lai khi pipeline du lieu san sang.",
            "recommended_actions": [
                "Kiem tra ket noi database",
                "Xac minh pipeline thu thap du lieu",
            ],
            "risk_level": "unknown",
        }

    return {"province_id": province_id, "insight": insight}


@router.get("/api/anomalies")
async def list_anomalies(request: Request) -> list[dict[str, Any]]:
    general_limiter.check(request)  # 120 req/min
    pool: asyncpg.Pool | None = get_pool(request)
    if pool is None:
        return []

    try:
        rows = await pool.fetch(
            """
            SELECT
                time, province_id, aqi, pm2_5, pm10, no2, ozone,
                temperature, humidity, wind_speed, precipitation, uv_index,
                is_anomaly, anomaly_score
            FROM env_readings
            WHERE time >= NOW() - INTERVAL '24 hours'
              AND (
                  is_anomaly IS TRUE
                  OR anomaly_score >= $1
                  OR aqi >= $2
              )
            ORDER BY time DESC
            LIMIT 100
            """,
            0.7,
            STRICT_ALERT_AQI,
        )
    except Exception as exc:
        logger.warning("Anomaly listing fallback: %s", exc)
        return []

    try:
        latest = await fetch_latest_readings(pool)
        latest = await enrich_readings_with_anomaly(latest, pool=pool)
    except Exception as exc:
        logger.warning("Latest-reading anomaly enrichment skipped: %s", exc)
        latest = {}

    anomalies: list[dict[str, Any]] = []
    seen_provinces: set[int] = set()
    for row in rows:
        payload = _reading_to_dict(row)
        if payload is None:
            continue
        province_id = int(payload["province_id"])
        enriched_latest = latest.get(province_id)
        if enriched_latest is not None:
            payload = {
                **payload,
                "anomaly_score": enriched_latest.get("anomaly_score", payload.get("anomaly_score")),
                "is_anomaly": enriched_latest.get("is_anomaly", payload.get("is_anomaly")),
                "anomaly_source": enriched_latest.get("anomaly_source"),
            }
        try:
            meta = province_meta(province_id)
        except Exception:
            meta = {"province_id": payload.get("province_id"), "name_vi": "Unknown"}
        seen_provinces.add(province_id)
        anomalies.append(_build_alert_record(meta, payload))

    for province_id, payload in latest.items():
        if province_id in seen_provinces:
            continue
        is_ai_event = payload.get("is_anomaly") is True or float(payload.get("anomaly_score") or 0) >= ANOMALY_SCORE_THRESHOLD
        if not is_ai_event:
            continue

        anomalies.append(
            _build_alert_record(province_meta(province_id), payload, forced_ai=True)
        )

    return anomalies
