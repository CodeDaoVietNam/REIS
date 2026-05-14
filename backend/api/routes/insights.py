from __future__ import annotations

import logging
from typing import Any

import asyncpg
from fastapi import APIRouter, Request

from backend.api.db import get_pool
from backend.api.routes.provinces import _reading_to_dict, fetch_current_reading, province_meta
from backend.config.constants import STRICT_ALERT_AQI
from backend.insights.insight_cache import get_or_create_insight
from backend.models.predict import DEFAULT_ANOMALY, DEFAULT_FORECAST, run_inference

logger = logging.getLogger(__name__)

router = APIRouter(tags=["insights"])


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


@router.get("/api/insights/{province_id}")
async def get_insight(province_id: int, request: Request) -> dict[str, Any]:
    province_meta(province_id)
    pool = get_pool(request)

    try:
        current = await fetch_current_reading(pool, province_id)
    except Exception as exc:
        logger.warning("Insight current-reading fallback for province %s: %s", province_id, exc)
        current = None

    try:
        inference = await run_inference(province_id) if current else {
            "anomaly": DEFAULT_ANOMALY,
            "forecast": DEFAULT_FORECAST,
        }
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
    pool: asyncpg.Pool | None = get_pool(request)
    if pool is None:
        return []

    try:
        rows = await pool.fetch(
            """
            SELECT
                time, province_id, aqi, pm2_5, pm10, no2, ozone,
                temperature, humidity, wind_speed, precipitation, uv_index,
                is_anomaly, anomaly_score, raw_json
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

    anomalies: list[dict[str, Any]] = []
    for row in rows:
        payload = _reading_to_dict(row)
        if payload is None:
            continue
        try:
            meta = province_meta(int(payload["province_id"]))
        except Exception:
            meta = {"province_id": payload.get("province_id"), "name_vi": "Unknown"}
        anomalies.append({"province": meta, "reading": payload})
    return anomalies
