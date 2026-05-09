"""
train_models.py — Train and export REIS ML models from TimescaleDB.

Usage examples:
    python backend/scripts/train_models.py --model lstm
    python backend/scripts/train_models.py --model prophet
    python backend/scripts/train_models.py --model anomaly
    python backend/scripts/train_models.py --model all
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# Ensure project root is on sys.path when running as a script:
#   python backend/scripts/train_models.py --model all
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.constants import FORECAST_HORIZON
from backend.config.settings import settings
from backend.models import isolation_forest, lstm_model, prophet_model
from backend.processing.feature_engineer import build_feature_frame

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _database_url() -> str:
    return (
        f"postgresql+psycopg://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


def load_raw_data(lookback_days: int | None = None) -> pd.DataFrame:
    engine = create_engine(_database_url())
    filters = ["r.time IS NOT NULL"]
    params: dict[str, str] = {}

    if lookback_days is not None:
        filters.append("r.time >= NOW() - (:lookback_days || ' days')::interval")
        params["lookback_days"] = str(lookback_days)

    query = f"""
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
    WHERE {' AND '.join(filters)}
    ORDER BY r.province_id, r.time
    """

    df = pd.read_sql_query(text(query), engine, params=params, parse_dates=["time"])
    if df.empty:
        raise ValueError("No data found in env_readings. Run backfill first.")

    df["time"] = pd.to_datetime(df["time"], utc=True)
    logger.info("Loaded %d raw rows from DB", len(df))
    return df


def time_based_split(df: pd.DataFrame, train_ratio: float = 0.70, val_ratio: float = 0.15):
    unique_times = sorted(df["time"].dropna().unique())
    if len(unique_times) < 10:
        raise ValueError("Not enough time points to split train/val/test.")

    train_idx = max(1, int(len(unique_times) * train_ratio)) - 1
    val_idx = max(train_idx + 1, int(len(unique_times) * (train_ratio + val_ratio))) - 1
    val_idx = min(val_idx, len(unique_times) - 2)

    train_end = pd.Timestamp(unique_times[train_idx])
    val_end = pd.Timestamp(unique_times[val_idx])

    train_df = df[df["time"] <= train_end].copy()
    val_df = df[(df["time"] > train_end) & (df["time"] <= val_end)].copy()
    test_df = df[df["time"] > val_end].copy()
    return train_df, val_df, test_df, train_end, val_end


def build_prophet_training_frame(feature_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a national-average AQI series as a simple global fallback Prophet model.
    """
    prophet_df = (
        feature_df.groupby("time", as_index=False)
        .agg(y=("aqi", "mean"))
        .rename(columns={"time": "ds"})
        .dropna()
        .sort_values("ds")
        .reset_index(drop=True)
    )
    return prophet_df


def train_lstm(train_df: pd.DataFrame, val_df: pd.DataFrame) -> None:
    result = lstm_model.train(train_df, val_df, save=True)
    logger.info(
        "LSTM exported: lookback=%sh, loss=%s, use_sample_weight=%s",
        result["config"].lookback_hours,
        result["config"].loss_name,
        result["config"].use_sample_weight,
    )


def train_prophet(train_df: pd.DataFrame, val_df: pd.DataFrame) -> None:
    combined = pd.concat([train_df, val_df], ignore_index=True)
    prophet_df = build_prophet_training_frame(combined)
    result = prophet_model.train(prophet_df, save=True)
    logger.info(
        "Prophet exported: horizon=%s",
        result["config"].forecast_horizon,
    )


def train_anomaly(train_df: pd.DataFrame) -> None:
    result = isolation_forest.train(train_df, save=True)
    logger.info(
        "Isolation Forest exported: contamination=%.2f",
        result["config"].contamination,
    )


def main(model_name: str, lookback_days: int | None) -> None:
    raw_df = load_raw_data(lookback_days=lookback_days)
    feature_result = build_feature_frame(raw_df)
    feature_df = feature_result.frame
    train_df, val_df, test_df, train_end, val_end = time_based_split(feature_df)

    logger.info(
        "Split summary | train=%d val=%d test=%d | train_end=%s val_end=%s",
        len(train_df),
        len(val_df),
        len(test_df),
        train_end,
        val_end,
    )

    if model_name in {"lstm", "all"}:
        train_lstm(train_df, val_df)
    if model_name in {"prophet", "all"}:
        train_prophet(train_df, val_df)
    if model_name in {"anomaly", "all"}:
        train_anomaly(train_df)

    logger.info("Artifacts written to %s", Path("backend/models/artifacts").resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and export REIS models")
    parser.add_argument(
        "--model",
        choices=["lstm", "prophet", "anomaly", "all"],
        default="all",
        help="Which model(s) to train and export",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Optional: restrict training data to the latest N days",
    )
    args = parser.parse_args()
    main(model_name=args.model, lookback_days=args.lookback_days)
