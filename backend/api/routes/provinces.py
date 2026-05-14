from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException, Request

from backend.api.db import get_pool
from backend.config.constants import PROVINCES, PROVINCES_BY_ID
from backend.models.predict import DEFAULT_ANOMALY, DEFAULT_FORECAST, run_inference

logger = logging.getLogger(__name__)

router = APIRouter(tags=["provinces"])


def province_meta(province_id: int) -> dict[str, Any]:
    province = PROVINCES_BY_ID.get(province_id)
    if province is None:
        raise HTTPException(status_code=404, detail=f"Province {province_id} not found")

    return {
        "province_id": province["id"],
        "name_vi": province["name_vi"],
        "name_en": province["name_en"],
        "latitude": province["latitude"],
        "longitude": province["longitude"],
        "region": province["region"],
    }


def _iso(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return value


def _reading_to_dict(row: asyncpg.Record | dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None

    data = dict(row)
    temperature = data.get("temperature", data.get("temp"))
    precipitation = data.get("precipitation", data.get("rainfall"))
    ozone = data.get("ozone", data.get("o3"))
    return {
        "time": _iso(data.get("time")),
        "province_id": data.get("province_id"),
        "aqi": data.get("aqi"),
        "pm2_5": data.get("pm2_5"),
        "pm10": data.get("pm10"),
        "no2": data.get("no2"),
        "so2": data.get("so2"),
        "co": data.get("co"),
        "o3": ozone,
        "ozone": ozone,
        "temp": temperature,
        "temperature": temperature,
        "humidity": data.get("humidity"),
        "wind_speed": data.get("wind_speed"),
        "rainfall": precipitation,
        "precipitation": precipitation,
        "uv_index": data.get("uv_index"),
        "is_anomaly": data.get("is_anomaly"),
        "anomaly_score": data.get("anomaly_score"),
        "raw_json": data.get("raw_json") or {},
    }


async def fetch_latest_readings(pool: asyncpg.Pool | None) -> dict[int, dict[str, Any]]:
    if pool is None:
        return {}

    rows = await pool.fetch(
        """
        SELECT DISTINCT ON (province_id)
            time, province_id, aqi, pm2_5, pm10, no2, ozone,
            temperature, humidity, wind_speed, precipitation, uv_index,
            is_anomaly, anomaly_score, raw_json
        FROM env_readings
        ORDER BY province_id, time DESC
        """
    )
    return {
        int(row["province_id"]): payload
        for row in rows
        if (payload := _reading_to_dict(row)) is not None
    }


async def fetch_current_reading(
    pool: asyncpg.Pool | None,
    province_id: int,
) -> dict[str, Any] | None:
    if pool is None:
        return None

    row = await pool.fetchrow(
        """
        SELECT
            time, province_id, aqi, pm2_5, pm10, no2, ozone,
            temperature, humidity, wind_speed, precipitation, uv_index,
            is_anomaly, anomaly_score, raw_json
        FROM env_readings
        WHERE province_id = $1
        ORDER BY time DESC
        LIMIT 1
        """,
        province_id,
    )
    return _reading_to_dict(row)


async def fetch_history(
    pool: asyncpg.Pool | None,
    province_id: int,
    hours: int = 48,
) -> list[dict[str, Any]]:
    if pool is None:
        return []

    rows = await pool.fetch(
        """
        SELECT
            time, province_id, aqi, pm2_5, pm10, no2, ozone,
            temperature, humidity, wind_speed, precipitation, uv_index,
            is_anomaly, anomaly_score, raw_json
        FROM env_readings
        WHERE province_id = $1
          AND time >= NOW() - ($2::text || ' hours')::interval
        ORDER BY time ASC
        """,
        province_id,
        hours,
    )
    return [payload for row in rows if (payload := _reading_to_dict(row)) is not None]


async def build_province_summaries(pool: asyncpg.Pool | None) -> list[dict[str, Any]]:
    latest_by_id = await fetch_latest_readings(pool)
    return [
        {
            **province_meta(province[0]),
            "current": latest_by_id.get(province[0]),
        }
        for province in PROVINCES
    ]


@router.get("/api/provinces")
async def list_provinces(request: Request) -> list[dict[str, Any]]:
    try:
        return await build_province_summaries(get_pool(request))
    except Exception as exc:
        logger.warning("Failed to load latest province readings: %s", exc)
        return [{**province_meta(province[0]), "current": None} for province in PROVINCES]


@router.get("/api/province/{province_id}")
async def get_province_detail(province_id: int, request: Request) -> dict[str, Any]:
    meta = province_meta(province_id)
    pool = get_pool(request)

    current: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []
    try:
        current = await fetch_current_reading(pool, province_id)
        history = await fetch_history(pool, province_id, hours=48)
    except Exception as exc:
        logger.warning("Failed to fetch province detail from DB: %s", exc)

    inference = {"anomaly": DEFAULT_ANOMALY, "forecast": DEFAULT_FORECAST}
    if current is not None:
        try:
            inference = await run_inference(province_id)
        except Exception as exc:
            logger.warning("Inference fallback for province %s: %s", province_id, exc)

    return {
        "province": meta,
        "current": current,
        "history": history,
        "anomaly": inference.get("anomaly", DEFAULT_ANOMALY),
        "forecast": inference.get("forecast", DEFAULT_FORECAST),
    }
