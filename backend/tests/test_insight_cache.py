"""
tests/test_insight_cache.py — Tests for Redis-backed insight cache behavior.
"""
from __future__ import annotations

import json

import pytest

from backend.insights import insight_cache


class FakeRedis:
    def __init__(self, initial=None, fail_get=False, fail_set=False):
        self.store = dict(initial or {})
        self.fail_get = fail_get
        self.fail_set = fail_set
        self.set_calls = []
        self.closed = False

    async def get(self, key):
        if self.fail_get:
            raise RuntimeError("redis get failed")
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        if self.fail_set:
            raise RuntimeError("redis set failed")
        self.store[key] = value
        self.set_calls.append((key, value, ex))

    async def aclose(self):
        self.closed = True


def _inputs(aqi=125):
    current = {
        "province_name": "Hà Nội",
        "aqi": aqi,
        "pm2_5": 45,
        "pm10": 70,
        "temperature": 31,
        "humidity": 70,
        "wind_speed": 4,
    }
    anomaly = {"score": 0.56, "label": "ANOMALY", "strict_alert": True}
    forecast = {"values": [120] * 12, "model_family": "lstm"}
    return current, anomaly, forecast


def test_aqi_bucket_groups_nearby_values():
    assert insight_cache.aqi_bucket(121) == 120
    assert insight_cache.aqi_bucket(125) == 120
    assert insight_cache.build_cache_key(1, 125) == "insight:1:120"


@pytest.mark.asyncio
async def test_cache_hit_skips_llm(monkeypatch):
    key = "insight:1:120"
    redis_client = FakeRedis(
        {
            key: json.dumps(
                {
                    "text": "cached text",
                    "source": "gemini",
                    "cached": False,
                    "cache_key": key,
                    "aqi_bucket": 120,
                }
            )
        }
    )

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM should not be called on cache hit")

    monkeypatch.setattr(insight_cache, "generate_insight_with_source", fail_if_called)

    current, anomaly, forecast = _inputs()
    result = await insight_cache.get_or_create_insight(
        1,
        current,
        anomaly,
        forecast,
        redis_client=redis_client,
    )

    assert result["text"] == "cached text"
    assert result["source"] == "cache"
    assert result["cached"] is True


@pytest.mark.asyncio
async def test_cache_miss_calls_llm_and_sets_ttl(monkeypatch):
    redis_client = FakeRedis()

    async def fake_generate(prompt, context=None):
        assert "Hà Nội" in prompt
        return "(1) Hiện trạng: fresh insight.", "gemini"

    monkeypatch.setattr(insight_cache, "generate_insight_with_source", fake_generate)

    current, anomaly, forecast = _inputs()
    result = await insight_cache.get_or_create_insight(
        1,
        current,
        anomaly,
        forecast,
        ttl_seconds=3600,
        redis_client=redis_client,
    )

    assert result["text"].endswith("fresh insight.")
    assert result["source"] == "gemini"
    assert result["cached"] is False
    assert len(redis_client.set_calls) == 1
    assert redis_client.set_calls[0][2] == 3600


@pytest.mark.asyncio
async def test_redis_failure_still_returns_insight(monkeypatch):
    redis_client = FakeRedis(fail_get=True, fail_set=True)

    async def fake_generate(prompt, context=None):
        return "(1) Hiện trạng: no cache but okay.", "template"

    monkeypatch.setattr(insight_cache, "generate_insight_with_source", fake_generate)

    current, anomaly, forecast = _inputs()
    result = await insight_cache.get_or_create_insight(
        1,
        current,
        anomaly,
        forecast,
        redis_client=redis_client,
    )

    assert result["text"].endswith("no cache but okay.")
    assert result["source"] == "template"
    assert result["cached"] is False
