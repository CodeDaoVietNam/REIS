"""
insight_cache.py — Redis-backed cached LLM insights.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from backend.config.settings import settings
from backend.insights.llm_client import generate_insight_with_source
from backend.insights.prompt_builder import build_context_from_inference, build_prompt

logger = logging.getLogger(__name__)


def aqi_bucket(aqi: float | int | None) -> int:
    try:
        value = int(float(aqi))
    except (TypeError, ValueError):
        value = 0
    return max(0, (value // 20) * 20)


def build_cache_key(province_id: int, aqi: float | int | None) -> str:
    return f"insight:{int(province_id)}:{aqi_bucket(aqi)}"


def get_redis_client():
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


async def _read_cache(client, key: str) -> dict[str, Any] | None:
    cached = await client.get(key)
    if not cached:
        return None
    try:
        data = json.loads(cached)
    except json.JSONDecodeError:
        logger.warning("Invalid cached insight payload for key=%s", key)
        return None

    data["source"] = "cache"
    data["cached"] = True
    return data


async def _write_cache(client, key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    await client.set(key, json.dumps(payload, ensure_ascii=False), ex=ttl_seconds)


async def get_or_create_insight(
    province_id: int,
    current: dict[str, Any],
    anomaly: dict[str, Any],
    forecast: dict[str, Any],
    ttl_seconds: int | None = None,
    redis_client=None,
) -> dict[str, Any]:
    """
    Return cached insight or generate a fresh one.

    Redis failures are non-fatal: the function still returns generated/template text.
    """
    ttl_seconds = ttl_seconds or settings.INSIGHT_CACHE_TTL_SECONDS
    context = build_context_from_inference(province_id, current, anomaly, forecast)
    key = build_cache_key(province_id, context.current.get("aqi"))

    owns_client = redis_client is None
    client = redis_client or get_redis_client()

    try:
        try:
            cached = await _read_cache(client, key)
            if cached is not None:
                return cached
        except Exception as exc:
            logger.warning("Insight cache read failed for key=%s: %s", key, exc)

        prompt = build_prompt(context)
        text, source = await generate_insight_with_source(prompt, context=context)
        payload = {
            "text": text,
            "source": source,
            "cached": False,
            "cache_key": key,
            "aqi_bucket": aqi_bucket(context.current.get("aqi")),
        }

        try:
            await _write_cache(client, key, payload, ttl_seconds)
        except Exception as exc:
            logger.warning("Insight cache write failed for key=%s: %s", key, exc)

        return payload
    finally:
        if owns_client:
            try:
                await client.aclose()
            except Exception:
                logger.debug("Redis client close failed", exc_info=True)
