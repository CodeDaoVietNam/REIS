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
        response = await client.get("/api/province/1")

    payload = response.json()
    assert response.status_code == 200
    assert payload["province"]["province_id"] == 1
    assert payload["current"] is None
    assert payload["history"] == []
    assert {"score", "label", "strict_alert"} <= set(payload["anomaly"])
    assert {"values", "lower", "upper", "model_family"} <= set(payload["forecast"])


@pytest.mark.asyncio
async def test_invalid_province_returns_404():
    async with make_client() as client:
        response = await client.get("/api/province/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_forecast_route_uses_prediction_contract(monkeypatch: pytest.MonkeyPatch):
    async def fake_predict_forecast(province_id: int) -> dict[str, Any]:
        assert province_id == 1
        return {
            "values": [42.0],
            "lower": [37.0],
            "upper": [47.0],
            "model_family": "test",
        }

    monkeypatch.setattr("backend.api.routes.forecast.predict_forecast", fake_predict_forecast)

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
