"""
Backfill hourly historical weather + air-quality data into TimescaleDB.

Default usage:
    python scripts/backfill_historical_data.py --days 50
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp
import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.constants import PROVINCES
from config.settings import settings

logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPEN_METEO_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
WEATHER_VARS = "temperature_2m,wind_speed_10m,relative_humidity_2m,precipitation"
AQ_VARS = "pm10,pm2_5,nitrogen_dioxide,ozone,uv_index,us_aqi"

INSERT_SQL = """
    INSERT INTO env_readings (
        time, province_id,
        temperature, humidity, wind_speed, precipitation,
        pm2_5, pm10, aqi, no2, ozone, uv_index,
        anomaly_score, is_anomaly, raw_json, inserted_at
    ) VALUES (
        $1, $2, $3, $4, $5, $6,
        $7, $8, $9, $10, $11, $12,
        NULL, FALSE, $13, $14
    )
    ON CONFLICT DO NOTHING;
"""


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _float_or_none(value: Any) -> float | None:
    return None if value is None else float(value)


def _int_or_none(value: Any) -> int | None:
    return None if value is None else int(value)


async def _fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    params: dict[str, Any],
    max_retries: int,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                payload = await response.json()
                if not isinstance(payload, dict):
                    raise RuntimeError(f"Unexpected response type: {type(payload)}")
                return payload
        except Exception as exc:
            last_error = exc
            wait = 3 * (2**attempt) if "429" in str(exc) else 2**attempt
            if attempt < max_retries - 1:
                logger.warning("Fetch failed (%s), retrying in %ss", exc, wait)
                await asyncio.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url}") from last_error


async def fetch_province_history(
    session: aiohttp.ClientSession,
    province_id: int,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    max_retries: int,
) -> list[dict[str, Any]]:
    weather_task = _fetch_json(
        session,
        ARCHIVE_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": WEATHER_VARS,
            "timezone": "Asia/Ho_Chi_Minh",
        },
        max_retries=max_retries,
    )
    aq_task = _fetch_json(
        session,
        AQ_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": AQ_VARS,
            "timezone": "Asia/Ho_Chi_Minh",
        },
        max_retries=max_retries,
    )
    weather, air_quality = await asyncio.gather(weather_task, aq_task)

    weather_hourly = weather.get("hourly", {})
    aq_hourly = air_quality.get("hourly", {})
    weather_times = weather_hourly.get("time") or []
    aq_times = aq_hourly.get("time") or []
    if not weather_times or not aq_times:
        return []

    weather_by_time = {
        timestamp: {key: values[index] for key, values in weather_hourly.items() if key != "time"}
        for index, timestamp in enumerate(weather_times)
    }
    aq_by_time = {
        timestamp: {key: values[index] for key, values in aq_hourly.items() if key != "time"}
        for index, timestamp in enumerate(aq_times)
    }

    rows: list[dict[str, Any]] = []
    now_utc = datetime.now(timezone.utc)
    for timestamp in sorted(set(weather_by_time) & set(aq_by_time)):
        weather_row = weather_by_time[timestamp]
        aq_row = aq_by_time[timestamp]
        reading_time = (
            datetime.fromisoformat(timestamp)
            .replace(tzinfo=OPEN_METEO_TIMEZONE)
            .astimezone(timezone.utc)
        )
        if reading_time > now_utc:
            continue
        rows.append(
            {
                "time": reading_time,
                "province_id": province_id,
                "temperature": weather_row.get("temperature_2m"),
                "humidity": weather_row.get("relative_humidity_2m"),
                "wind_speed": weather_row.get("wind_speed_10m"),
                "precipitation": weather_row.get("precipitation"),
                "pm2_5": aq_row.get("pm2_5"),
                "pm10": aq_row.get("pm10"),
                "aqi": aq_row.get("us_aqi"),
                "no2": aq_row.get("nitrogen_dioxide"),
                "ozone": aq_row.get("ozone"),
                "uv_index": aq_row.get("uv_index"),
                "raw_json": {
                    "source": "open_meteo_historical_backfill",
                    "weather": weather_row,
                    "air_quality": aq_row,
                },
            }
        )
    return rows


async def ensure_unique_index(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_env_readings_province_time
            ON env_readings (province_id, time)
            """
        )


async def insert_rows(pool: asyncpg.Pool, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    now = datetime.now(timezone.utc)
    values = [
        (
            row["time"],
            row["province_id"],
            _float_or_none(row.get("temperature")),
            _float_or_none(row.get("humidity")),
            _float_or_none(row.get("wind_speed")),
            _float_or_none(row.get("precipitation")),
            _float_or_none(row.get("pm2_5")),
            _float_or_none(row.get("pm10")),
            _int_or_none(row.get("aqi")),
            _float_or_none(row.get("no2")),
            _float_or_none(row.get("ozone")),
            _float_or_none(row.get("uv_index")),
            json.dumps(row.get("raw_json", {}), ensure_ascii=False),
            now,
        )
        for row in rows
    ]
    async with pool.acquire() as conn:
        before = await conn.fetchval("SELECT COUNT(*) FROM env_readings")
        await conn.executemany(INSERT_SQL, values)
        after = await conn.fetchval("SELECT COUNT(*) FROM env_readings")
    return int(after - before)


async def run_backfill(args: argparse.Namespace) -> dict[str, Any]:
    end_date = _parse_date(args.end_date) if args.end_date else date.today()
    start_date = _parse_date(args.start_date) if args.start_date else end_date - timedelta(days=args.days)
    province_filter = set(args.province_id or [])
    provinces = [row for row in PROVINCES if not province_filter or row[0] in province_filter]

    pool = await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        min_size=1,
        max_size=5,
    )
    await ensure_unique_index(pool)

    result = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "success": 0,
        "failed": 0,
        "rows_fetched": 0,
        "rows_inserted": 0,
        "provinces": [],
    }
    started = time.time()

    connector = aiohttp.TCPConnector(limit=args.concurrency, ttl_dns_cache=300)
    timeout = aiohttp.ClientTimeout(total=args.timeout)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for index, province in enumerate(provinces, start=1):
                province_id, name_vi, _name_en, lat, lon, _region = province
                logger.info("[%02d/%02d] Backfill %s", index, len(provinces), name_vi)
                try:
                    rows = await fetch_province_history(
                        session,
                        province_id=province_id,
                        lat=lat,
                        lon=lon,
                        start_date=start_date,
                        end_date=end_date,
                        max_retries=args.max_retries,
                    )
                    inserted = 0 if args.dry_run else await insert_rows(pool, rows)
                    result["success"] += 1
                    result["rows_fetched"] += len(rows)
                    result["rows_inserted"] += inserted
                    result["provinces"].append(
                        {
                            "province_id": province_id,
                            "name_vi": name_vi,
                            "rows_fetched": len(rows),
                            "rows_inserted": inserted,
                            "status": "success",
                        }
                    )
                    logger.info("OK %s fetched=%s inserted=%s", name_vi, len(rows), inserted)
                except Exception as exc:
                    result["failed"] += 1
                    result["provinces"].append(
                        {
                            "province_id": province_id,
                            "name_vi": name_vi,
                            "rows_fetched": 0,
                            "rows_inserted": 0,
                            "status": "failed",
                            "error": repr(exc),
                        }
                    )
                    logger.exception("Backfill failed for %s", name_vi)

                if args.sleep_between > 0:
                    await asyncio.sleep(args.sleep_between)
    finally:
        await pool.close()

    result["elapsed_seconds"] = round(time.time() - started, 2)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill REIS historical env_readings")
    parser.add_argument("--days", type=int, default=50, help="Number of days to backfill when start-date is omitted")
    parser.add_argument("--start-date", help="Inclusive YYYY-MM-DD start date")
    parser.add_argument("--end-date", help="Inclusive YYYY-MM-DD end date")
    parser.add_argument("--province-id", type=int, action="append", help="Limit to one or more province ids")
    parser.add_argument("--sleep-between", type=float, default=1.5, help="Seconds to sleep between provinces")
    parser.add_argument("--concurrency", type=int, default=5, help="HTTP connector concurrency")
    parser.add_argument("--timeout", type=int, default=90, help="Per-request timeout seconds")
    parser.add_argument("--max-retries", type=int, default=3, help="HTTP retry attempts per API call")
    parser.add_argument("--dry-run", action="store_true", help="Fetch data but do not insert")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    result = await run_backfill(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())
