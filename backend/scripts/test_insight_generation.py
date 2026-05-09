"""
test_insight_generation.py — Manual smoke test for LLM insight generation.

Usage:
    python backend/scripts/test_insight_generation.py
    python backend/scripts/test_insight_generation.py --province-id 1 --use-db
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Support `python backend/scripts/test_insight_generation.py`
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import settings
from backend.insights.insight_cache import get_or_create_insight
from backend.insights.llm_client import generate_insight_with_source
from backend.insights.prompt_builder import build_context_from_inference, build_prompt
from backend.models.predict import fetch_recent_readings, run_inference


def sample_payload(province_id: int) -> tuple[dict, dict, dict]:
    current = {
        "province_id": province_id,
        "province_name": "Hà Nội" if province_id == 1 else f"Tỉnh {province_id}",
        "time": "2026-05-10T09:00:00+07:00",
        "aqi": 132,
        "pm2_5": 68.4,
        "pm10": 92.1,
        "temperature": 31.5,
        "humidity": 72.0,
        "wind_speed": 2.8,
    }
    anomaly = {
        "score": 0.61,
        "label": "ANOMALY",
        "strict_alert": True,
    }
    forecast = {
        "values": [130, 132, 134, 136, 138, 140, 142, 145, 147, 149, 151, 153],
        "lower": [125] * 12,
        "upper": [160] * 12,
        "model_family": "lstm",
    }
    return current, anomaly, forecast


async def build_real_payload(province_id: int) -> tuple[dict, dict, dict]:
    inference = await run_inference(province_id)
    raw_df = await fetch_recent_readings(province_id, hours=72)
    if raw_df.empty:
        raise ValueError(f"No recent DB readings found for province_id={province_id}")
    current = raw_df.sort_values("time").iloc[-1].to_dict()
    current.setdefault("province_name", f"Tỉnh {province_id}")
    return current, inference["anomaly"], inference["forecast"]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Manual smoke test for REIS LLM insights")
    parser.add_argument("--province-id", type=int, default=1, help="Province ID to test")
    parser.add_argument(
        "--use-db",
        action="store_true",
        help="Use real DB data + model inference instead of sample payload",
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Run through Redis insight cache instead of direct LLM call",
    )
    args = parser.parse_args()

    print(f"RUNTIME GEMINI_MODEL: {settings.GEMINI_MODEL}")
    print(f"GEMINI KEY PRESENT: {bool(settings.GEMINI_API_KEY or settings.LLM_API_KEY)}")
    print(f"OPENAI KEY PRESENT: {bool(settings.OPENAI_API_KEY)}")
    print(f"USE_DB: {args.use_db}")
    print(f"USE_CACHE: {args.use_cache}")
    print("-" * 80)

    if args.use_db:
        current, anomaly, forecast = await build_real_payload(args.province_id)
    else:
        current, anomaly, forecast = sample_payload(args.province_id)

    if args.use_cache:
        result = await get_or_create_insight(args.province_id, current, anomaly, forecast)
        print("SOURCE:", result["source"])
        print("CACHED:", result["cached"])
        print("CACHE KEY:", result.get("cache_key"))
        print("-" * 80)
        print(result["text"])
        return

    ctx = build_context_from_inference(args.province_id, current, anomaly, forecast)
    prompt = build_prompt(ctx)
    text, source = await generate_insight_with_source(prompt, context=ctx)

    print("SOURCE:", source)
    print("-" * 80)
    print(text)


if __name__ == "__main__":
    asyncio.run(main())
