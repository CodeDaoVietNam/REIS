"""
tests/test_predict.py — Tests for unified inference interface.
"""
from __future__ import annotations

import pandas as pd
import pytest

from backend.models import predict


def _sample_raw_df() -> pd.DataFrame:
    rows = []
    for i in range(72):
        rows.append(
            {
                "time": pd.Timestamp("2026-05-01T00:00:00Z") + pd.Timedelta(hours=i),
                "province_id": 1,
                "province_name": "Hà Nội",
                "region": "Bac",
                "temperature": 30 + (i % 5),
                "humidity": 70 + (i % 6),
                "wind_speed": 4 + (i % 3),
                "precipitation": 0.0,
                "pm2_5": 40 + (i % 10),
                "pm10": 60 + (i % 12),
                "aqi": 80 + (i % 20),
                "no2": 12 + (i % 4),
                "ozone": 30 + (i % 6),
                "uv_index": 1.0,
            }
        )
    return pd.DataFrame(rows)


@pytest.mark.asyncio
async def test_predict_anomaly_returns_score_in_range(monkeypatch):
    monkeypatch.setattr(predict, "_ensure_anomaly_artifacts_exist", lambda: True)
    monkeypatch.setattr(predict, "fetch_recent_readings", lambda *args, **kwargs: _sample_raw_df())
    monkeypatch.setattr(
        predict.anomaly_model,
        "predict_score",
        lambda *args, **kwargs: [0.61],
    )
    monkeypatch.setattr(
        predict.anomaly_model,
        "classify",
        lambda score, threshold=None: "ANOMALY",
    )
    monkeypatch.setattr(
        predict.anomaly_model,
        "build_strict_alert",
        lambda row, score, threshold=None: True,
    )

    result = await predict.predict_anomaly(1, raw_df=_sample_raw_df())
    assert 0 <= result["score"] <= 1
    assert result["label"] == "ANOMALY"


@pytest.mark.asyncio
async def test_predict_forecast_returns_required_keys(monkeypatch):
    monkeypatch.setattr(predict, "_ensure_lstm_artifacts_exist", lambda: True)
    monkeypatch.setattr(predict, "_ensure_prophet_artifacts_exist", lambda: False)
    monkeypatch.setattr(predict, "fetch_recent_readings", lambda *args, **kwargs: _sample_raw_df())
    monkeypatch.setattr(
        predict.lstm_model,
        "predict",
        lambda history: [100.0] * 12,
    )

    result = await predict.predict_forecast(1, raw_df=_sample_raw_df())
    assert set(result.keys()) == {"values", "lower", "upper", "model_family"}
    assert result["model_family"] == "lstm"
    assert len(result["values"]) == 12


@pytest.mark.asyncio
async def test_predict_forecast_falls_back_to_prophet(monkeypatch):
    monkeypatch.setattr(predict, "_ensure_lstm_artifacts_exist", lambda: True)
    monkeypatch.setattr(predict, "_ensure_prophet_artifacts_exist", lambda: True)
    monkeypatch.setattr(predict, "fetch_recent_readings", lambda *args, **kwargs: _sample_raw_df())
    monkeypatch.setattr(
        predict.lstm_model,
        "predict",
        lambda history: (_ for _ in ()).throw(RuntimeError("LSTM failed")),
    )
    monkeypatch.setattr(predict.prophet_model, "load_model", lambda: object())
    monkeypatch.setattr(
        predict.prophet_model,
        "predict",
        lambda model, periods=12: {"values": [1.0] * 12, "lower": [0.0] * 12, "upper": [2.0] * 12},
    )

    result = await predict.predict_forecast(1, raw_df=_sample_raw_df())
    assert result["model_family"] == "prophet"
    assert len(result["values"]) == 12


@pytest.mark.asyncio
async def test_model_unavailable_returns_default(monkeypatch):
    monkeypatch.setattr(predict, "_ensure_lstm_artifacts_exist", lambda: False)
    monkeypatch.setattr(predict, "_ensure_prophet_artifacts_exist", lambda: False)
    monkeypatch.setattr(predict, "fetch_recent_readings", lambda *args, **kwargs: pd.DataFrame())

    result = await predict.predict_forecast(1)
    assert result["model_family"] == "default"
    assert len(result["values"]) == 12

