"""
Tests for FastAPI route contracts.
"""
from __future__ import annotations

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.main import app


def make_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_app_imports_successfully():
    assert app.title == "REIS API"


@pytest.mark.asyncio
async def test_health_check_returns_expected_payload():
    async with make_client() as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "reis-api",
        "version": "0.1.0",
    }


@pytest.mark.asyncio
async def test_swagger_docs_exist():
    async with make_client() as client:
        response = await client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


@pytest.mark.asyncio
async def test_provinces_returns_all_metadata_with_optional_current():
    async with make_client() as client:
        response = await client.get("/api/provinces")

    payload = response.json()
    assert response.status_code == 200
    assert len(payload) == 63
    assert {"province_id", "name_vi", "name_en", "latitude", "longitude", "region", "current"} <= set(
        payload[0]
    )


@pytest.mark.asyncio
async def test_province_detail_returns_fallback_contract_without_db():
    async with make_client() as client:
        response = await client.get("/api/province/1?hours=168")

    payload = response.json()
    assert response.status_code == 200
    assert payload["province"]["province_id"] == 1
    assert payload["current"] is None
    assert payload["history"] == []
    assert {"score", "label", "strict_alert"} <= set(payload["anomaly"])
    assert {"values", "lower", "upper", "model_family"} <= set(payload["forecast"])
    assert payload["data_source"] == "fallback"
    assert payload["inference_source"] == "default"
    assert payload["updated_at"] is None


@pytest.mark.asyncio
async def test_summary_returns_kpi_contract_without_db():
    async with make_client() as client:
        response = await client.get("/api/summary")

    payload = response.json()
    assert response.status_code == 200
    assert payload == {
        "aqi_avg": 0,
        "pm25_avg": 0,
        "aqi_warning_count": 0,
        "ai_anomaly_count": 0,
        "warning_count": 0,
        "anomaly_count": 0,
        "province_count": 63,
        "latest_time": None,
    }


@pytest.mark.asyncio
async def test_compare_returns_default_province_contract_without_db():
    async with make_client() as client:
        response = await client.get("/api/compare?province_ids=1,2,4&days=7&metric=aqi")

    payload = response.json()
    assert response.status_code == 200
    assert payload["metric"] == "aqi"
    assert payload["days"] == 7
    assert [item["province"]["province_id"] for item in payload["provinces"]] == [1, 2, 4]
    assert {"current", "history", "anomaly", "radar"} <= set(payload["provinces"][0])


@pytest.mark.asyncio
async def test_compare_rejects_invalid_metric():
    async with make_client() as client:
        response = await client.get("/api/compare?province_ids=1,2&metric=bad_metric")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_compare_rejects_invalid_province_id():
    async with make_client() as client:
        response = await client.get("/api/compare?province_ids=1,999&metric=aqi")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_province_returns_404():
    async with make_client() as client:
        response = await client.get("/api/province/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_forecast_route_uses_prediction_contract(monkeypatch: pytest.MonkeyPatch):
    async def fake_get_cached_inference(province_id: int) -> tuple[dict[str, Any], str]:
        assert province_id == 1
        return (
            {
                "forecast": {
                    "values": [42.0],
                    "lower": [37.0],
                    "upper": [47.0],
                    "model_family": "test",
                }
            },
            "cache",
        )

    monkeypatch.setattr("backend.api.routes.forecast.get_cached_inference", fake_get_cached_inference)

    async with make_client() as client:
        response = await client.get("/api/forecast/1")

    assert response.status_code == 200
    assert response.json() == {
        "province_id": 1,
        "values": [42.0],
        "lower": [37.0],
        "upper": [47.0],
        "model_family": "test",
    }


@pytest.mark.asyncio
async def test_inference_cache_reuses_result(monkeypatch: pytest.MonkeyPatch):
    from backend.api import inference_cache

    calls = 0

    async def fake_run_inference(province_id: int) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return {
            "anomaly": {"score": 0.42, "label": "NORMAL", "strict_alert": False},
            "forecast": {"values": [1], "lower": [0], "upper": [2], "model_family": "test"},
        }

    inference_cache.clear_inference_cache()
    monkeypatch.setattr(inference_cache, "run_inference", fake_run_inference)

    first, first_source = await inference_cache.get_cached_inference(1)
    second, second_source = await inference_cache.get_cached_inference(1)

    assert first == second
    assert first_source == "model"
    assert second_source == "cache"
    assert calls == 1


@pytest.mark.asyncio
async def test_insights_route_uses_controlled_fallback(monkeypatch: pytest.MonkeyPatch):
    async def fake_get_or_create_insight(
        province_id: int,
        current: dict[str, Any],
        anomaly: dict[str, Any],
        forecast: dict[str, Any],
    ) -> dict[str, Any]:
        assert province_id == 1
        assert current["province_id"] == 1
        assert anomaly["label"] == "NORMAL"
        assert forecast["model_family"] == "default"
        return {"text": "Insight test", "source": "test", "cached": False}

    monkeypatch.setattr("backend.api.routes.insights.get_or_create_insight", fake_get_or_create_insight)

    async with make_client() as client:
        response = await client.get("/api/insights/1")

    assert response.status_code == 200
    assert response.json() == {
        "province_id": 1,
        "insight": {"text": "Insight test", "source": "test", "cached": False},
    }


@pytest.mark.asyncio
async def test_anomalies_returns_empty_list_without_db():
    async with make_client() as client:
        response = await client.get("/api/anomalies")

    assert response.status_code == 200
    assert response.json() == []
