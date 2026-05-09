"""
tests/test_prophet_model.py — Tests for Prophet fallback model.
"""
from __future__ import annotations

import pandas as pd
import pytest

from backend.models import prophet_model


pytest.importorskip("prophet")


def test_make_prophet_ready_removes_timezone():
    df = pd.DataFrame(
        {
            "ds": pd.date_range("2026-01-01", periods=5, freq="h", tz="UTC"),
            "y": [10, 11, 12, 13, 14],
        }
    )
    ready = prophet_model.make_prophet_ready(df)
    assert ready["ds"].dt.tz is None


def test_train_and_predict_length(tmp_path):
    df = pd.DataFrame(
        {
            "ds": pd.date_range("2026-01-01", periods=48, freq="h", tz="UTC"),
            "y": [50 + (i % 12) for i in range(48)],
        }
    )
    result = prophet_model.train(df, save=False)
    forecast = prophet_model.predict(result["model"], periods=12)
    assert set(forecast.keys()) == {"values", "lower", "upper"}
    assert len(forecast["values"]) == 12
    assert len(forecast["lower"]) == 12
    assert len(forecast["upper"]) == 12


def test_forecast_dataframe_has_required_columns():
    df = pd.DataFrame(
        {
            "ds": pd.date_range("2026-01-01", periods=36, freq="h", tz="UTC"),
            "y": [70 + (i % 6) for i in range(36)],
        }
    )
    result = prophet_model.train(df, save=False)
    forecast_df = prophet_model.forecast_dataframe(result["model"], periods=12)
    assert list(forecast_df.columns) == ["ds", "yhat", "yhat_lower", "yhat_upper"]
    assert len(forecast_df) == 12

