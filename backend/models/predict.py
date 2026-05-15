"""
predict.py — Unified inference interface for anomaly + forecast.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.config.constants import ANOMALY_FEATURES, FEATURE_COLUMNS, FORECAST_HORIZON, HISTORY_WINDOW
from backend.config.settings import settings
from backend.models import isolation_forest as anomaly_model
from backend.models import lstm_model, prophet_model
from backend.processing.feature_engineer import build_feature_frame, select_history_window, select_recent_rows

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DBConfig:
    host: str = settings.DB_HOST
    port: int = settings.DB_PORT
    user: str = settings.DB_USER
    password: str = settings.DB_PASSWORD
    database: str = settings.DB_NAME


DEFAULT_FORECAST = {
    "values": [0.0] * FORECAST_HORIZON,
    "lower": [0.0] * FORECAST_HORIZON,
    "upper": [0.0] * FORECAST_HORIZON,
    "model_family": "default",
}

DEFAULT_ANOMALY = {
    "score": 0.0,
    "label": "NORMAL",
    "strict_alert": False,
}


async def fetch_recent_readings(
    province_id: int,
    hours: int = 48,
    db_config: DBConfig | None = None,
    pool: Any | None = None,
) -> pd.DataFrame:
    """Query recent readings for one province from TimescaleDB.

    Args:
        pool: Optional asyncpg.Pool (preferred — reuses connections).
              If None, creates a temporary connection (legacy behavior).
    """
    import asyncpg

    query = """
        SELECT
            r.time,
            r.province_id,
            p.name_vi AS province_name,
            p.region,
            r.temperature,
            r.humidity,
            r.wind_speed,
            r.precipitation,
            r.pm2_5,
            r.pm10,
            r.aqi,
            r.no2,
            r.ozone,
            r.uv_index
        FROM env_readings r
        LEFT JOIN provinces p ON p.id = r.province_id
        WHERE r.province_id = $1
          AND r.time >= NOW() - ($2 || ' hours')::interval
        ORDER BY r.time
    """

    if pool is not None:
        # Use shared pool — no connection overhead
        rows = await pool.fetch(query, province_id, str(hours))
    else:
        # Fallback: create temporary connection (for CLI/notebook usage)
        cfg = db_config or DBConfig()
        conn = await asyncpg.connect(
            host=cfg.host,
            port=cfg.port,
            user=cfg.user,
            password=cfg.password,
            database=cfg.database,
        )
        try:
            rows = await conn.fetch(query, province_id, str(hours))
        finally:
            await conn.close()

    if not rows:
        return pd.DataFrame()

    frame = pd.DataFrame([dict(row) for row in rows])
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    return frame


def _ensure_lstm_artifacts_exist() -> bool:
    return (
        lstm_model.MODEL_PATH.exists()
        and lstm_model.FEATURE_SCALER_PATH.exists()
        and lstm_model.TARGET_SCALER_PATH.exists()
        and lstm_model.METADATA_PATH.exists()
    )


def _ensure_prophet_artifacts_exist() -> bool:
    return prophet_model.MODEL_PATH.exists() and prophet_model.METADATA_PATH.exists()


def _ensure_anomaly_artifacts_exist() -> bool:
    return (
        anomaly_model.MODEL_PATH.exists()
        and anomaly_model.SCALER_PATH.exists()
        and anomaly_model.METADATA_PATH.exists()
    )


async def predict_anomaly(
    province_id: int,
    db_config: DBConfig | None = None,
    raw_df: pd.DataFrame | None = None,
    pool: Any | None = None,
) -> dict[str, Any]:
    """Predict anomaly score from recent province history."""
    try:
        if raw_df is None:
            raw_df = await fetch_recent_readings(province_id, hours=48, db_config=db_config, pool=pool)
        if raw_df.empty or not _ensure_anomaly_artifacts_exist():
            logger.warning("Anomaly model unavailable or no data for province_id=%s", province_id)
            return dict(DEFAULT_ANOMALY)

        feature_result = build_feature_frame(raw_df)
        recent = select_recent_rows(feature_result.frame, province_id, rows=1)
        if recent.empty:
            return dict(DEFAULT_ANOMALY)

        row = recent.iloc[-1]
        feature_values = row[ANOMALY_FEATURES].to_numpy(dtype=np.float32)
        score = float(anomaly_model.predict_score(feature_values)[0])
        label = anomaly_model.classify(score)
        strict_alert = anomaly_model.build_strict_alert(row, score)
        return {"score": score, "label": label, "strict_alert": strict_alert}

    except Exception as exc:
        logger.warning("predict_anomaly failed for province_id=%s: %s", province_id, exc)
        return dict(DEFAULT_ANOMALY)


def _build_prophet_series(feature_df: pd.DataFrame, province_id: int) -> pd.DataFrame:
    series = (
        feature_df[feature_df["province_id"] == province_id][["time", "aqi"]]
        .dropna()
        .rename(columns={"time": "ds", "aqi": "y"})
        .sort_values("ds")
        .reset_index(drop=True)
    )
    return series


async def predict_forecast(
    province_id: int,
    db_config: DBConfig | None = None,
    raw_df: pd.DataFrame | None = None,
    pool: Any | None = None,
) -> dict[str, Any]:
    """Forecast future AQI using LSTM, fallback to Prophet, else defaults."""
    try:
        if raw_df is None:
            raw_df = await fetch_recent_readings(province_id, hours=72, db_config=db_config, pool=pool)
        if raw_df.empty:
            logger.warning("No recent readings for province_id=%s", province_id)
            return dict(DEFAULT_FORECAST)

        feature_result = build_feature_frame(raw_df)
        feature_df = feature_result.frame

        if _ensure_lstm_artifacts_exist():
            history_df = select_history_window(feature_df, province_id, history_hours=HISTORY_WINDOW)
            if len(history_df) >= HISTORY_WINDOW:
                history = history_df[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
                preds = np.asarray(lstm_model.predict(history), dtype=np.float32)
                recent_std = float(history_df["aqi"].tail(HISTORY_WINDOW).std() or 0)
                band = float(np.clip(max(5.0, recent_std * 0.35), 5.0, 30.0))
                return {
                    "values": np.round(preds, 4).tolist(),
                    "lower": np.round(np.clip(preds - band, 0, 500), 4).tolist(),
                    "upper": np.round(np.clip(preds + band, 0, 500), 4).tolist(),
                    "model_family": "lstm",
                }

        if _ensure_prophet_artifacts_exist():
            prophet_series = _build_prophet_series(feature_df, province_id)
            if len(prophet_series) >= 2:
                model = prophet_model.load_model()
                forecast = prophet_model.predict(model, periods=FORECAST_HORIZON)
                forecast["model_family"] = "prophet"
                return forecast

        logger.warning("No forecast model artifacts available for province_id=%s", province_id)
        return dict(DEFAULT_FORECAST)

    except Exception as exc:
        logger.warning("predict_forecast failed for province_id=%s: %s", province_id, exc)
        if _ensure_prophet_artifacts_exist():
            try:
                model = prophet_model.load_model()
                forecast = prophet_model.predict(model, periods=FORECAST_HORIZON)
                forecast["model_family"] = "prophet"
                return forecast
            except Exception as prophet_exc:
                logger.warning("Prophet fallback also failed: %s", prophet_exc)
        return dict(DEFAULT_FORECAST)


async def run_inference(
    province_id: int,
    db_config: DBConfig | None = None,
    pool: Any | None = None,
) -> dict[str, Any]:
    """Run anomaly and forecast inference concurrently."""
    raw_df = await fetch_recent_readings(province_id, hours=72, db_config=db_config, pool=pool)
    anomaly_task = predict_anomaly(province_id, db_config=db_config, raw_df=raw_df, pool=pool)
    forecast_task = predict_forecast(province_id, db_config=db_config, raw_df=raw_df, pool=pool)
    anomaly, forecast = await asyncio.gather(anomaly_task, forecast_task)
    return {
        "province_id": province_id,
        "anomaly": anomaly,
        "forecast": forecast,
    }
