"""
tests/test_lstm_model.py — Tests for tuned LSTM forecasting module.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backend.config.constants import FEATURE_COLUMNS, FORECAST_HORIZON, HISTORY_WINDOW
from backend.models import lstm_model


pytest.importorskip("tensorflow")


def test_build_model_compiles():
    model = lstm_model.build_model()
    assert model is not None
    assert model.output_shape[-1] == FORECAST_HORIZON


def test_predict_output_shape_and_range(monkeypatch):
    class DummyModel:
        def predict(self, x, verbose=0):
            return np.full((1, FORECAST_HORIZON), 0.5, dtype=np.float32)

    class IdentityScaler:
        def transform(self, x):
            return x

        def inverse_transform(self, x):
            return x * 500

    monkeypatch.setattr(lstm_model, "load_model", lambda *args, **kwargs: DummyModel())
    monkeypatch.setattr(
        lstm_model,
        "load_scalers",
        lambda *args, **kwargs: (IdentityScaler(), IdentityScaler()),
    )
    monkeypatch.setattr(lstm_model, "load_config", lambda *args, **kwargs: lstm_model.LSTMConfig())

    history = np.ones((HISTORY_WINDOW, len(FEATURE_COLUMNS)), dtype=np.float32)
    preds = lstm_model.predict(history)
    assert preds.shape == (FORECAST_HORIZON,)
    assert np.all(preds >= 0)
    assert np.all(preds <= 500)


def test_predict_invalid_shape_raises(monkeypatch):
    monkeypatch.setattr(lstm_model, "load_model", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        lstm_model,
        "load_scalers",
        lambda *args, **kwargs: (object(), object()),
    )
    monkeypatch.setattr(lstm_model, "load_config", lambda *args, **kwargs: lstm_model.LSTMConfig())

    with pytest.raises(ValueError):
        lstm_model.predict(np.ones((48, len(FEATURE_COLUMNS)), dtype=np.float32))


def test_save_and_load_scalers(tmp_path: Path):
    feature_scaler, target_scaler = lstm_model.fit_scalers(
        pd.DataFrame(
            {
                **{col: np.linspace(1, 10, 20) for col in FEATURE_COLUMNS},
                "aqi": np.linspace(50, 120, 20),
            }
        )
    )

    class DummyModel:
        def save(self, path):
            Path(path).write_text("dummy")

    model = DummyModel()
    model_path = tmp_path / "model.keras"
    feature_path = tmp_path / "feature.joblib"
    target_path = tmp_path / "target.joblib"
    meta_path = tmp_path / "meta.json"

    original_model_path = lstm_model.MODEL_PATH
    original_feature_path = lstm_model.FEATURE_SCALER_PATH
    original_target_path = lstm_model.TARGET_SCALER_PATH
    original_meta_path = lstm_model.METADATA_PATH

    try:
        lstm_model.MODEL_PATH = model_path
        lstm_model.FEATURE_SCALER_PATH = feature_path
        lstm_model.TARGET_SCALER_PATH = target_path
        lstm_model.METADATA_PATH = meta_path

        lstm_model.save_artifacts(model, feature_scaler, target_scaler)
        loaded_feature, loaded_target = lstm_model.load_scalers(feature_path, target_path)
        cfg = lstm_model.load_config(meta_path)

        assert feature_path.exists()
        assert target_path.exists()
        assert meta_path.exists()
        assert loaded_feature is not None
        assert loaded_target is not None
        assert cfg.lookback_hours == HISTORY_WINDOW
    finally:
        lstm_model.MODEL_PATH = original_model_path
        lstm_model.FEATURE_SCALER_PATH = original_feature_path
        lstm_model.TARGET_SCALER_PATH = original_target_path
        lstm_model.METADATA_PATH = original_meta_path


def test_make_sample_weights_increases_for_spikes():
    meta_df = pd.DataFrame(
        {
            "aqi_future_t1": [80, 160, 120],
            "delta_pm2_5_1h_t0": [5, 8, 25],
        }
    )
    weights = lstm_model.make_sample_weights(meta_df)
    assert weights.shape == (3,)
    assert weights[1] > weights[0]
    assert weights[2] > weights[0]

