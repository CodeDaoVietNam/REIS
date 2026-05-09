"""
prophet_model.py — Prophet fallback forecasting model.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from backend.config.constants import FORECAST_HORIZON

logger = logging.getLogger(__name__)

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ARTIFACT_DIR / "prophet_aqi.json"
METADATA_PATH = ARTIFACT_DIR / "prophet_metadata.json"


@dataclass(slots=True)
class ProphetConfig:
    forecast_horizon: int = FORECAST_HORIZON
    daily_seasonality: bool = True
    weekly_seasonality: bool = True
    yearly_seasonality: bool = False


def _import_prophet():
    from prophet import Prophet
    from prophet.serialize import model_from_json, model_to_json

    return Prophet, model_to_json, model_from_json


def make_prophet_ready(df: pd.DataFrame) -> pd.DataFrame:
    """Convert ds column to timezone-naive timestamps for Prophet."""
    ready = df.copy()
    ready["ds"] = pd.to_datetime(ready["ds"], utc=True).dt.tz_localize(None)
    ready = ready.sort_values("ds").drop_duplicates(subset=["ds"]).reset_index(drop=True)
    return ready


def train(
    df: pd.DataFrame,
    config: ProphetConfig | None = None,
    save: bool = True,
):
    """Fit Prophet on a dataframe with columns ds, y."""
    cfg = config or ProphetConfig()
    Prophet, model_to_json, _ = _import_prophet()

    train_df = make_prophet_ready(df[["ds", "y"]].dropna().copy())
    if len(train_df) < 2:
        raise ValueError("Prophet requires at least 2 non-null rows.")

    model = Prophet(
        daily_seasonality=cfg.daily_seasonality,
        weekly_seasonality=cfg.weekly_seasonality,
        yearly_seasonality=cfg.yearly_seasonality,
    )
    model.fit(train_df)

    if save:
        MODEL_PATH.write_text(model_to_json(model))
        METADATA_PATH.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2))
        logger.info("Saved Prophet artifacts to %s", ARTIFACT_DIR)

    return {"model": model, "config": cfg}


def load_model(model_path: Path | str = MODEL_PATH):
    """Load Prophet model from serialized JSON."""
    _, _, model_from_json = _import_prophet()
    return model_from_json(Path(model_path).read_text())


def load_config(metadata_path: Path | str = METADATA_PATH) -> ProphetConfig:
    """Load Prophet config metadata."""
    data = json.loads(Path(metadata_path).read_text())
    return ProphetConfig(**data)


def predict(
    model,
    periods: int = FORECAST_HORIZON,
    freq: str = "h",
) -> dict[str, list[float]]:
    """
    Forecast future values and return serializable arrays.
    """
    forecast_df = forecast_dataframe(model, periods=periods, freq=freq)
    return {
        "values": forecast_df["yhat"].round(4).tolist(),
        "lower": forecast_df["yhat_lower"].round(4).tolist(),
        "upper": forecast_df["yhat_upper"].round(4).tolist(),
    }


def forecast_dataframe(model, periods: int = FORECAST_HORIZON, freq: str = "h") -> pd.DataFrame:
    """Return forecast dataframe containing yhat, yhat_lower, yhat_upper."""
    future = model.make_future_dataframe(periods=periods, freq=freq, include_history=False)
    forecast = model.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    return forecast.reset_index(drop=True)
