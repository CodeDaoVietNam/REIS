from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, HTTPException, Query, Request

from backend.api.db import get_pool
from backend.api.inference_cache import get_cached_anomaly, get_cached_inference
from backend.api.rate_limit import general_limiter
from backend.config.constants import PROVINCES, PROVINCES_BY_ID
from backend.models.predict import DEFAULT_ANOMALY, DEFAULT_FORECAST

logger = logging.getLogger(__name__)

router = APIRouter(tags=["provinces"])

ALLOWED_COMPARE_METRICS = {"aqi", "pm2_5", "pm10", "temperature", "humidity", "wind_speed"}
WARNING_AQI_THRESHOLD = 150
ANOMALY_SCORE_THRESHOLD = 0.7
ANOMALY_SUMMARY_CONCURRENCY = 8
ANOMALY_SUMMARY_TIMEOUT_SECONDS = 8.0


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


def _reading_to_dict(
    row: asyncpg.Record | dict[str, Any] | None,
    *,
    include_raw_json: bool = False,
) -> dict[str, Any] | None:
    if row is None:
        return None

    data = dict(row)
    temperature = data.get("temperature", data.get("temp"))
    precipitation = data.get("precipitation", data.get("rainfall"))
    ozone = data.get("ozone", data.get("o3"))
    payload = {
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
    }
    if include_raw_json:
        payload["raw_json"] = data.get("raw_json") or {}
    return payload


def _radar_from_reading(reading: dict[str, Any] | None) -> dict[str, float]:
    if reading is None:
        return {"aqi": 0, "pm2_5": 0, "pm10": 0, "no2": 0, "ozone": 0, "uv_index": 0}
    return {
        "aqi": float(reading.get("aqi") or 0),
        "pm2_5": float(reading.get("pm2_5") or 0),
        "pm10": float(reading.get("pm10") or 0),
        "no2": float(reading.get("no2") or 0),
        "ozone": float(reading.get("ozone") or reading.get("o3") or 0),
        "uv_index": float(reading.get("uv_index") or 0),
    }


def _is_anomaly_payload_alert(anomaly: dict[str, Any]) -> bool:
    return (
        bool(anomaly.get("strict_alert"))
        or anomaly.get("label") not in (None, "NORMAL")
        or float(anomaly.get("score") or 0) >= ANOMALY_SCORE_THRESHOLD
    )


def _is_persisted_anomaly(reading: dict[str, Any]) -> bool:
    return (
        reading.get("is_anomaly") is True
        or float(reading.get("anomaly_score") or 0) >= ANOMALY_SCORE_THRESHOLD
    )


async def _count_ai_anomalies(
    readings: list[dict[str, Any]],
    pool: asyncpg.Pool | None = None,
) -> int:
    """Count AI anomalies using persisted flags plus anomaly-only cached inference."""
    semaphore = asyncio.Semaphore(ANOMALY_SUMMARY_CONCURRENCY)

    async def classify(reading: dict[str, Any]) -> bool:
        if _is_persisted_anomaly(reading):
            return True

        province_id = reading.get("province_id")
        if not isinstance(province_id, int):
            return False

        async with semaphore:
            try:
                anomaly, _source = await get_cached_anomaly(province_id, pool=pool)
            except Exception as exc:
                logger.debug("Summary anomaly inference skipped for province %s: %s", province_id, exc)
                return False
            return _is_anomaly_payload_alert(anomaly)

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*(classify(reading) for reading in readings)),
            timeout=ANOMALY_SUMMARY_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        logger.warning("Summary anomaly inference timed out; using persisted anomaly flags only.")
        return sum(1 for row in readings if _is_persisted_anomaly(row))

    return sum(1 for item in results if item)


def _merge_anomaly_into_reading(
    reading: dict[str, Any],
    anomaly: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    return {
        **reading,
        "anomaly_score": float(anomaly.get("score") or 0),
        "is_anomaly": _is_anomaly_payload_alert(anomaly),
        "anomaly_source": source,
    }


async def enrich_readings_with_anomaly(
    readings: dict[int, dict[str, Any]],
    pool: asyncpg.Pool | None = None,
) -> dict[int, dict[str, Any]]:
    """Attach cached model anomaly scores to latest readings for API/UI consistency."""
    if not readings:
        return readings

    semaphore = asyncio.Semaphore(ANOMALY_SUMMARY_CONCURRENCY)

    async def enrich_item(province_id: int, reading: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        async with semaphore:
            try:
                anomaly, source = await get_cached_anomaly(province_id, pool=pool)
            except Exception as exc:
                logger.debug("Province anomaly enrichment skipped for province %s: %s", province_id, exc)
                return province_id, reading
            return province_id, _merge_anomaly_into_reading(reading, anomaly, source)

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*(enrich_item(province_id, reading) for province_id, reading in readings.items())),
            timeout=ANOMALY_SUMMARY_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        logger.warning("Province anomaly enrichment timed out; using persisted anomaly fields only.")
        return readings

    return dict(results)


async def fetch_latest_readings(pool: asyncpg.Pool | None) -> dict[int, dict[str, Any]]:
    if pool is None:
        return {}

    rows = await pool.fetch(
        """
        SELECT DISTINCT ON (province_id)
            time, province_id, aqi, pm2_5, pm10, no2, ozone,
            temperature, humidity, wind_speed, precipitation, uv_index,
            is_anomaly, anomaly_score
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
            is_anomaly, anomaly_score
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
            is_anomaly, anomaly_score
        FROM env_readings
        WHERE province_id = $1
          AND time >= NOW() - ($2 * INTERVAL '1 hour')
        ORDER BY time ASC
        """,
        province_id,
        hours,
    )
    return [payload for row in rows if (payload := _reading_to_dict(row)) is not None]


async def build_province_summaries(pool: asyncpg.Pool | None) -> list[dict[str, Any]]:
    latest_by_id = await fetch_latest_readings(pool)
    latest_by_id = await enrich_readings_with_anomaly(latest_by_id, pool=pool)
    return [
        {
            **province_meta(province[0]),
            "current": latest_by_id.get(province[0]),
        }
        for province in PROVINCES
    ]


@router.get("/api/provinces")
async def list_provinces(request: Request) -> list[dict[str, Any]]:
    general_limiter.check(request)
    try:
        return await build_province_summaries(get_pool(request))
    except Exception as exc:
        logger.warning("Failed to load latest province readings: %s", exc)
        return [{**province_meta(province[0]), "current": None} for province in PROVINCES]


@router.get("/api/province/{province_id}")
async def get_province_detail(
    province_id: int,
    request: Request,
    hours: int = Query(default=48, ge=1, le=24 * 60),
) -> dict[str, Any]:
    general_limiter.check(request)
    meta = province_meta(province_id)
    pool = get_pool(request)

    current: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []
    try:
        current = await fetch_current_reading(pool, province_id)
        history = await fetch_history(pool, province_id, hours=hours)
    except Exception as exc:
        logger.warning("Failed to fetch province detail from DB: %s", exc)

    inference = {"anomaly": DEFAULT_ANOMALY, "forecast": DEFAULT_FORECAST}
    inference_source = "default"
    if current is not None:
        try:
            inference, inference_source = await get_cached_inference(province_id, pool=pool)
        except Exception as exc:
            logger.warning("Inference fallback for province %s: %s", province_id, exc)
            inference_source = "fallback"

    anomaly = inference.get("anomaly", DEFAULT_ANOMALY)
    if current is not None and inference_source != "default":
        current = {
            **current,
            "anomaly_score": float(anomaly.get("score") or 0),
            "is_anomaly": _is_anomaly_payload_alert(anomaly),
        }

    return {
        "province": meta,
        "current": current,
        "history": history,
        "anomaly": anomaly,
        "forecast": inference.get("forecast", DEFAULT_FORECAST),
        "data_source": "db" if current is not None else "fallback",
        "inference_source": inference_source,
        "updated_at": (current or {}).get("time"),
    }


@router.get("/api/summary")
async def get_summary(request: Request) -> dict[str, Any]:
    general_limiter.check(request)
    pool = get_pool(request)
    try:
        latest = await fetch_latest_readings(pool)
    except Exception as exc:
        logger.warning("Failed to build summary from DB: %s", exc)
        latest = {}

    latest = await enrich_readings_with_anomaly(latest, pool=pool)
    readings = [reading for reading in latest.values() if reading is not None]
    province_count = len(PROVINCES)
    if not readings:
        return {
            "aqi_avg": 0,
            "pm25_avg": 0,
            "aqi_warning_count": 0,
            "ai_anomaly_count": 0,
            "warning_count": 0,
            "anomaly_count": 0,
            "province_count": province_count,
            "latest_time": None,
        }

    aqi_values = [float(row["aqi"]) for row in readings if row.get("aqi") is not None]
    pm25_values = [float(row["pm2_5"]) for row in readings if row.get("pm2_5") is not None]
    warning_count = sum(1 for row in readings if float(row.get("aqi") or 0) >= WARNING_AQI_THRESHOLD)
    anomaly_count = sum(1 for row in readings if _is_persisted_anomaly(row))
    latest_time = max((row.get("time") for row in readings if row.get("time")), default=None)
    aqi_warning_count = warning_count
    ai_anomaly_count = anomaly_count

    return {
        "aqi_avg": round(sum(aqi_values) / len(aqi_values), 1) if aqi_values else 0,
        "pm25_avg": round(sum(pm25_values) / len(pm25_values), 1) if pm25_values else 0,
        "aqi_warning_count": aqi_warning_count,
        "ai_anomaly_count": ai_anomaly_count,
        "warning_count": aqi_warning_count,
        "anomaly_count": ai_anomaly_count,
        "province_count": province_count,
        "latest_time": latest_time,
    }


@router.get("/api/compare")
async def compare_provinces(
    request: Request,
    province_ids: str = Query(default="1,2,4"),
    days: int = Query(default=7, ge=1, le=60),
    metric: str = Query(default="aqi"),
) -> dict[str, Any]:
    general_limiter.check(request)
    if metric not in ALLOWED_COMPARE_METRICS:
        raise HTTPException(status_code=400, detail=f"Unsupported metric: {metric}")

    try:
        ids = [int(item.strip()) for item in province_ids.split(",") if item.strip()]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="province_ids must be comma-separated integers") from exc

    unique_ids = list(dict.fromkeys(ids))[:6]
    if not unique_ids:
        raise HTTPException(status_code=400, detail="At least one province id is required")

    pool = get_pool(request)
    response_items: list[dict[str, Any]] = []
    for province_id in unique_ids:
        meta = province_meta(province_id)
        try:
            current = await fetch_current_reading(pool, province_id)
            history = await fetch_history(pool, province_id, hours=days * 24)
        except Exception as exc:
            logger.warning("Compare fallback for province %s: %s", province_id, exc)
            current = None
            history = []

        anomaly = DEFAULT_ANOMALY
        if current is not None:
            try:
                anomaly, _source = await get_cached_anomaly(province_id, pool=pool)
            except Exception as exc:
                logger.warning("Compare inference fallback for province %s: %s", province_id, exc)
        if current is not None:
            current = {
                **current,
                "anomaly_score": float(anomaly.get("score") or 0),
                "is_anomaly": _is_anomaly_payload_alert(anomaly),
            }

        response_items.append(
            {
                "province": meta,
                "current": current,
                "history": history,
                "anomaly": {
                    "score": float(anomaly.get("score") or 0),
                    "label": anomaly.get("label") or "NORMAL",
                    "strict_alert": bool(anomaly.get("strict_alert")),
                },
                "radar": _radar_from_reading(current),
            }
        )

    return {"metric": metric, "days": days, "provinces": response_items}
