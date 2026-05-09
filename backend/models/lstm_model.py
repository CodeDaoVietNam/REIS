"""
lstm_model.py — Tuned LSTM forecasting model for AQI.

Champion config from notebook experiments:
  - lookback: 12h
  - units: 128 -> 64
  - dropout: 0.2
  - optimizer: Adam(lr=1e-3)
  - loss: Huber
  - sample weighting: spike-aware
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from backend.config.constants import FEATURE_COLUMNS, FORECAST_HORIZON, HISTORY_WINDOW, TARGET_COLUMN

logger = logging.getLogger(__name__)

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ARTIFACT_DIR / "lstm_aqi.keras"
FEATURE_SCALER_PATH = ARTIFACT_DIR / "lstm_feature_scaler.joblib"
TARGET_SCALER_PATH = ARTIFACT_DIR / "lstm_target_scaler.joblib"
METADATA_PATH = ARTIFACT_DIR / "lstm_metadata.json"


@dataclass(slots=True)
class LSTMConfig:
    lookback_hours: int = HISTORY_WINDOW
    forecast_horizon: int = FORECAST_HORIZON
    units_1: int = 128
    units_2: int = 64
    dropout: float = 0.20
    learning_rate: float = 1e-3
    batch_size: int = 32
    epochs: int = 50
    patience: int = 6
    loss_name: str = "huber"
    use_sample_weight: bool = True
    aqi_spike_threshold: float = 150.0
    delta_pm25_spike_threshold: float = 20.0


def _import_tf():
    import tensorflow as tf
    from tensorflow.keras import Sequential
    from tensorflow.keras.callbacks import EarlyStopping
    from tensorflow.keras.layers import Dense, Dropout, Input, LSTM

    return tf, Sequential, EarlyStopping, Input, LSTM, Dense, Dropout


def fit_scalers(train_frame: pd.DataFrame) -> tuple[MinMaxScaler, MinMaxScaler]:
    """Fit MinMax scalers on feature and target columns."""
    usable = train_frame.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy()
    if usable.empty:
        raise ValueError("Training frame is empty after dropping missing values.")

    feature_scaler = MinMaxScaler()
    target_scaler = MinMaxScaler()
    feature_scaler.fit(usable[FEATURE_COLUMNS])
    target_scaler.fit(usable[[TARGET_COLUMN]])
    return feature_scaler, target_scaler


def make_sequences(
    frame: pd.DataFrame,
    lookback: int,
    horizon: int,
    feature_scaler: MinMaxScaler,
    target_scaler: MinMaxScaler,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Convert engineered frame into LSTM sequences grouped by province."""
    x_list: list[np.ndarray] = []
    y_list: list[np.ndarray] = []
    meta_rows: list[dict[str, Any]] = []

    for province_id, group in frame.groupby("province_id"):
        group = group.sort_values("time").dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN]).copy()
        if len(group) < lookback + horizon:
            continue

        features_scaled = feature_scaler.transform(group[FEATURE_COLUMNS])
        target_scaled = target_scaler.transform(group[[TARGET_COLUMN]])[:, 0]

        for end_idx in range(lookback, len(group) - horizon + 1):
            x_list.append(features_scaled[end_idx - lookback:end_idx])
            y_list.append(target_scaled[end_idx:end_idx + horizon])
            meta_rows.append(
                {
                    "province_id": int(province_id),
                    "province_name": group.iloc[end_idx]["province_name"]
                    if "province_name" in group.columns
                    else None,
                    "forecast_start": group.iloc[end_idx]["time"],
                    "aqi_future_t1": float(group.iloc[end_idx]["aqi"]),
                    "delta_pm2_5_1h_t0": float(group.iloc[end_idx - 1]["delta_pm2_5_1h"])
                    if end_idx - 1 >= 0 and "delta_pm2_5_1h" in group.columns
                    else 0.0,
                }
            )

    if not x_list:
        return (
            np.empty((0, lookback, len(FEATURE_COLUMNS)), dtype=np.float32),
            np.empty((0, horizon), dtype=np.float32),
            pd.DataFrame(),
        )

    return np.asarray(x_list, dtype=np.float32), np.asarray(y_list, dtype=np.float32), pd.DataFrame(meta_rows)


def make_sample_weights(meta_df: pd.DataFrame, config: LSTMConfig | None = None) -> np.ndarray:
    """Build spike-aware sample weights used by the champion model."""
    cfg = config or LSTMConfig()
    weights = np.ones(len(meta_df), dtype=np.float32)
    if meta_df.empty:
        return weights

    weights += (
        meta_df["aqi_future_t1"].fillna(0).to_numpy() >= cfg.aqi_spike_threshold
    ).astype(np.float32)
    weights += (
        meta_df["delta_pm2_5_1h_t0"].fillna(0).to_numpy() >= cfg.delta_pm25_spike_threshold
    ).astype(np.float32)
    return weights


def build_model(
    lookback: int = HISTORY_WINDOW,
    n_features: int | None = None,
    horizon: int = FORECAST_HORIZON,
    units_1: int = 128,
    units_2: int = 64,
    dropout: float = 0.20,
    learning_rate: float = 1e-3,
    loss_name: str = "huber",
):
    """
    Build a compiled Keras Sequential LSTM model.

    Note:
      Docs originally suggest 64 -> 32; after tuning we use 128 -> 64 by default.
      Caller can still pass 64 -> 32 if muốn bám bản architecture baseline.
    """
    tf, Sequential, _, Input, LSTM, Dense, Dropout = _import_tf()

    n_features = n_features or len(FEATURE_COLUMNS)
    model = Sequential(
        [
            Input(shape=(lookback, n_features)),
            LSTM(units_1, return_sequences=True),
            Dropout(dropout),
            LSTM(units_2),
            Dropout(dropout),
            Dense(horizon),
        ]
    )

    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    loss = tf.keras.losses.Huber() if loss_name == "huber" else "mse"
    model.compile(optimizer=optimizer, loss=loss, metrics=["mae"])
    return model


def inverse_multistep(arr: np.ndarray, scaler: MinMaxScaler) -> np.ndarray:
    """Inverse-transform a 2D multistep output array."""
    return scaler.inverse_transform(arr.reshape(-1, 1)).reshape(arr.shape)


def train(
    train_frame: pd.DataFrame,
    val_frame: pd.DataFrame | None = None,
    config: LSTMConfig | None = None,
    save: bool = True,
) -> dict[str, Any]:
    """
    Train the tuned LSTM model from engineered feature frames.

    Returns a bundle with model, scalers, history, and metrics.
    """
    cfg = config or LSTMConfig()
    tf, _, EarlyStopping, _, _, _, _ = _import_tf()
    tf.keras.utils.set_random_seed(42)

    feature_scaler, target_scaler = fit_scalers(train_frame)
    x_train, y_train, meta_train = make_sequences(
        train_frame,
        cfg.lookback_hours,
        cfg.forecast_horizon,
        feature_scaler,
        target_scaler,
    )
    if len(x_train) == 0:
        raise ValueError("Not enough data to build training sequences.")

    validation_data = None
    fit_kwargs: dict[str, Any] = {
        "x": x_train,
        "y": y_train,
        "epochs": cfg.epochs,
        "batch_size": cfg.batch_size,
        "verbose": 0,
        "callbacks": [
            EarlyStopping(monitor="val_loss" if val_frame is not None else "loss", patience=cfg.patience, restore_best_weights=True)
        ],
    }

    if cfg.use_sample_weight:
        fit_kwargs["sample_weight"] = make_sample_weights(meta_train, cfg)

    if val_frame is not None:
        x_val, y_val, _ = make_sequences(
            val_frame,
            cfg.lookback_hours,
            cfg.forecast_horizon,
            feature_scaler,
            target_scaler,
        )
        if len(x_val) > 0:
            validation_data = (x_val, y_val)
            fit_kwargs["validation_data"] = validation_data

    model = build_model(
        lookback=cfg.lookback_hours,
        n_features=len(FEATURE_COLUMNS),
        horizon=cfg.forecast_horizon,
        units_1=cfg.units_1,
        units_2=cfg.units_2,
        dropout=cfg.dropout,
        learning_rate=cfg.learning_rate,
        loss_name=cfg.loss_name,
    )

    history = model.fit(**fit_kwargs)

    if save:
        save_artifacts(model, feature_scaler, target_scaler, cfg)

    return {
        "model": model,
        "feature_scaler": feature_scaler,
        "target_scaler": target_scaler,
        "history": history.history,
        "config": cfg,
    }


def save_artifacts(
    model,
    feature_scaler: MinMaxScaler,
    target_scaler: MinMaxScaler,
    config: LSTMConfig | None = None,
) -> None:
    """Save Keras model, scalers, and config metadata."""
    cfg = config or LSTMConfig()
    model.save(MODEL_PATH)
    joblib.dump(feature_scaler, FEATURE_SCALER_PATH)
    joblib.dump(target_scaler, TARGET_SCALER_PATH)
    METADATA_PATH.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2))
    logger.info("Saved LSTM artifacts to %s", ARTIFACT_DIR)


def load_model(model_path: Path | str = MODEL_PATH):
    """Load a trained Keras model from disk."""
    tf, _, _, _, _, _, _ = _import_tf()
    return tf.keras.models.load_model(model_path)


def load_scalers(
    feature_scaler_path: Path | str = FEATURE_SCALER_PATH,
    target_scaler_path: Path | str = TARGET_SCALER_PATH,
) -> tuple[MinMaxScaler, MinMaxScaler]:
    """Load saved MinMax scalers."""
    return joblib.load(feature_scaler_path), joblib.load(target_scaler_path)


def load_config(metadata_path: Path | str = METADATA_PATH) -> LSTMConfig:
    """Load saved model config."""
    data = json.loads(Path(metadata_path).read_text())
    return LSTMConfig(**data)


def predict(
    history_48h: np.ndarray,
    model=None,
    feature_scaler: MinMaxScaler | None = None,
    target_scaler: MinMaxScaler | None = None,
    config: LSTMConfig | None = None,
) -> np.ndarray:
    """
    Predict 12-step AQI forecast from an engineered history window.

    Args:
        history_48h: shape (history_window, n_features)
    """
    cfg = config or load_config()
    model = model or load_model()
    feature_scaler, target_scaler = (
        (feature_scaler, target_scaler)
        if feature_scaler is not None and target_scaler is not None
        else load_scalers()
    )

    history = np.asarray(history_48h, dtype=np.float32)
    expected_shape = (cfg.lookback_hours, len(FEATURE_COLUMNS))
    if history.shape != expected_shape:
        raise ValueError(
            f"Expected history shape {expected_shape}, got {history.shape}"
        )

    scaled = feature_scaler.transform(history)
    preds_scaled = model.predict(scaled[np.newaxis, :, :], verbose=0)
    preds = inverse_multistep(preds_scaled, target_scaler)[0]
    preds = np.clip(preds, 0, 500)
    return preds
