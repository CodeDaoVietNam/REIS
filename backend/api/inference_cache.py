from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from backend.config.settings import settings
from backend.models.predict import predict_anomaly, run_inference


@dataclass(slots=True)
class CachedInference:
    value: dict[str, Any]
    expires_at: float


_cache: dict[int, CachedInference] = {}
_anomaly_cache: dict[int, CachedInference] = {}
_locks: dict[int, asyncio.Lock] = {}
_anomaly_locks: dict[int, asyncio.Lock] = {}


def clear_inference_cache() -> None:
    _cache.clear()
    _anomaly_cache.clear()


async def get_cached_inference(province_id: int, *, force_refresh: bool = False) -> tuple[dict[str, Any], str]:
    """Return shared province inference with a short demo-friendly TTL."""
    now = time.monotonic()
    cached = _cache.get(province_id)
    if not force_refresh and cached and cached.expires_at > now:
        return cached.value, "cache"

    lock = _locks.setdefault(province_id, asyncio.Lock())
    async with lock:
        now = time.monotonic()
        cached = _cache.get(province_id)
        if not force_refresh and cached and cached.expires_at > now:
            return cached.value, "cache"

        inference = await run_inference(province_id)
        ttl = max(1, settings.INFERENCE_CACHE_TTL_SECONDS)
        _cache[province_id] = CachedInference(value=inference, expires_at=now + ttl)
        if "anomaly" in inference:
            _anomaly_cache[province_id] = CachedInference(value=inference["anomaly"], expires_at=now + ttl)
        return inference, "model"


async def get_cached_anomaly(province_id: int, *, force_refresh: bool = False) -> tuple[dict[str, Any], str]:
    """Return anomaly-only inference without triggering forecast/LSTM work."""
    now = time.monotonic()
    full_cached = _cache.get(province_id)
    if not force_refresh and full_cached and full_cached.expires_at > now and "anomaly" in full_cached.value:
        return full_cached.value["anomaly"], "cache"

    cached = _anomaly_cache.get(province_id)
    if not force_refresh and cached and cached.expires_at > now:
        return cached.value, "cache"

    lock = _anomaly_locks.setdefault(province_id, asyncio.Lock())
    async with lock:
        now = time.monotonic()
        full_cached = _cache.get(province_id)
        if not force_refresh and full_cached and full_cached.expires_at > now and "anomaly" in full_cached.value:
            return full_cached.value["anomaly"], "cache"

        cached = _anomaly_cache.get(province_id)
        if not force_refresh and cached and cached.expires_at > now:
            return cached.value, "cache"

        anomaly = await predict_anomaly(province_id)
        ttl = max(1, settings.INFERENCE_CACHE_TTL_SECONDS)
        _anomaly_cache[province_id] = CachedInference(value=anomaly, expires_at=now + ttl)
        return anomaly, "model"
