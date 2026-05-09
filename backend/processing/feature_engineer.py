"""
feature_engineer.py — Shared feature engineering for notebooks and production.

Mục tiêu:
  - Chuẩn hóa dữ liệu env_readings thành frame theo giờ / theo tỉnh
  - Tạo feature set đã được chọn sau quá trình notebook tuning
  - Chuẩn bị input cho anomaly detection và forecasting
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from backend.config.constants import ANOMALY_FEATURES, FEATURE_COLUMNS

NUMERIC_COLUMNS = [
    "temperature",
    "humidity",
    "wind_speed",
    "precipitation",
    "pm2_5",
    "pm10",
    "aqi",
    "no2",
    "ozone",
    "uv_index",
]


@dataclass(slots=True)
class FeatureBuildResult:
    frame: pd.DataFrame
    feature_columns: list[str]
    anomaly_feature_columns: list[str]


def ensure_datetime_utc(series: pd.Series) -> pd.Series:
    """Parse a datetime-like series into tz-aware UTC timestamps."""
    return pd.to_datetime(series, utc=True)


def resample_to_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate raw readings to one row per province per hour."""
    if df.empty:
        return df.copy()

    hourly = df.copy()
    hourly["time"] = ensure_datetime_utc(hourly["time"]).dt.floor("h")

    aggregation_map = {
        "province_name": "first",
        "region": "first",
        "temperature": "mean",
        "humidity": "mean",
        "wind_speed": "mean",
        "precipitation": "sum",
        "pm2_5": "mean",
        "pm10": "mean",
        "aqi": "mean",
        "no2": "mean",
        "ozone": "mean",
        "uv_index": "mean",
    }

    available_map = {
        key: value for key, value in aggregation_map.items() if key in hourly.columns
    }
    grouped = (
        hourly.groupby(["province_id", "time"], as_index=False)
        .agg(available_map)
        .sort_values(["province_id", "time"])
        .reset_index(drop=True)
    )
    return grouped


def fill_hourly_gaps(hourly_df: pd.DataFrame, interpolation_limit: int = 6) -> pd.DataFrame:
    """Fill small gaps inside each province timeline."""
    if hourly_df.empty:
        return hourly_df.copy()

    frames: list[pd.DataFrame] = []
    province_groups = hourly_df.groupby("province_id")

    for province_id, group in province_groups:
        group = group.sort_values("time").copy()
        full_index = pd.date_range(
            group["time"].min(),
            group["time"].max(),
            freq="h",
            tz="UTC",
        )

        group = group.set_index("time").reindex(full_index)
        group.index.name = "time"
        group["province_id"] = province_id

        if "province_name" in group.columns:
            group["province_name"] = group["province_name"].ffill().bfill()
        if "region" in group.columns:
            group["region"] = group["region"].ffill().bfill()
        if "precipitation" in group.columns:
            group["precipitation"] = group["precipitation"].fillna(0)

        cols_to_interpolate = [
            col
            for col in NUMERIC_COLUMNS
            if col in group.columns and col != "precipitation"
        ]
        if cols_to_interpolate:
            group[cols_to_interpolate] = group[cols_to_interpolate].interpolate(
                method="time",
                limit=interpolation_limit,
                limit_direction="both",
            )
            group[cols_to_interpolate] = group[cols_to_interpolate].ffill().bfill()

        frames.append(group.reset_index())

    filled = pd.concat(frames, ignore_index=True)
    filled = filled.rename(columns={"index": "time"})
    return filled.sort_values(["province_id", "time"]).reset_index(drop=True)


def add_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Create anomaly / forecasting features chosen from notebook tuning."""
    if df.empty:
        return df.copy()

    frames: list[pd.DataFrame] = []

    for _, group in df.groupby("province_id"):
        group = group.sort_values("time").copy()

        group["pm2_5_lag_1h"] = group["pm2_5"].shift(1)
        group["pm2_5_lag_3h"] = group["pm2_5"].shift(3)
        group["pm2_5_lag_6h"] = group["pm2_5"].shift(6)
        group["pm2_5_lag_24h"] = group["pm2_5"].shift(24)

        group["pm10_lag_1h"] = group["pm10"].shift(1)
        group["pm10_lag_3h"] = group["pm10"].shift(3)

        group["aqi_lag_1h"] = group["aqi"].shift(1)
        group["aqi_lag_3h"] = group["aqi"].shift(3)
        group["aqi_lag_6h"] = group["aqi"].shift(6)
        group["aqi_lag_24h"] = group["aqi"].shift(24)

        group["aqi_rolling_mean_3h"] = group["aqi"].rolling(window=3, min_periods=3).mean()
        group["aqi_rolling_mean_6h"] = group["aqi"].rolling(window=6, min_periods=6).mean()
        group["aqi_rolling_std_6h"] = group["aqi"].rolling(window=6, min_periods=6).std()
        group["aqi_rolling_max_3h"] = group["aqi"].rolling(window=3, min_periods=3).max()
        group["aqi_rolling_min_3h"] = group["aqi"].rolling(window=3, min_periods=3).min()
        group["aqi_rolling_min_6h"] = group["aqi"].rolling(window=6, min_periods=6).min()

        group["pm2_5_rolling_mean_6h"] = group["pm2_5"].rolling(window=6, min_periods=6).mean()
        group["pm2_5_rolling_std_6h"] = group["pm2_5"].rolling(window=6, min_periods=6).std()
        group["pm10_rolling_std_6h"] = group["pm10"].rolling(window=6, min_periods=6).std()

        group["hour_of_day"] = group["time"].dt.hour
        group["day_of_week"] = group["time"].dt.dayofweek
        group["month"] = group["time"].dt.month
        group["is_weekend"] = group["day_of_week"].isin([5, 6]).astype(int)
        group["is_rush_hour"] = group["hour_of_day"].isin([7, 8, 9, 17, 18, 19]).astype(int)

        group["delta_aqi_1h"] = group["aqi"] - group["aqi_lag_1h"]
        group["delta_pm2_5_1h"] = group["pm2_5"] - group["pm2_5_lag_1h"]
        group["pm2_5_x_wind_speed"] = group["pm2_5"] * group["wind_speed"]
        group["temperature_x_humidity"] = group["temperature"] * group["humidity"]

        group["hour_sin"] = np.sin(2 * np.pi * group["hour_of_day"] / 24)
        group["hour_cos"] = np.cos(2 * np.pi * group["hour_of_day"] / 24)
        group["dow_sin"] = np.sin(2 * np.pi * group["day_of_week"] / 7)
        group["dow_cos"] = np.cos(2 * np.pi * group["day_of_week"] / 7)

        frames.append(group)

    out = pd.concat(frames, ignore_index=True)
    rolling_std_threshold = out["aqi_rolling_std_6h"].quantile(0.95)
    out["heuristic_anomaly_label"] = (
        (out["aqi"] >= 151)
        | (out["pm2_5"] >= 55.5)
        | (out["pm10"] >= 150)
        | (out["aqi_rolling_std_6h"].fillna(0) >= rolling_std_threshold)
    ).astype(int)
    out["strict_domain_alert"] = (
        (out["aqi"] >= 150)
        | (out["pm2_5"] >= 100)
        | (out["delta_pm2_5_1h"] >= 20)
    ).astype(int)
    return out.sort_values(["province_id", "time"]).reset_index(drop=True)


def build_feature_frame(raw_df: pd.DataFrame) -> FeatureBuildResult:
    """Full pipeline: raw readings -> hourly -> filled -> engineered features."""
    hourly = resample_to_hourly(raw_df)
    hourly = fill_hourly_gaps(hourly)
    feature_df = add_feature_engineering(hourly)
    return FeatureBuildResult(
        frame=feature_df,
        feature_columns=list(FEATURE_COLUMNS),
        anomaly_feature_columns=list(ANOMALY_FEATURES),
    )


def select_history_window(
    feature_df: pd.DataFrame,
    province_id: int,
    history_hours: int,
) -> pd.DataFrame:
    """Select the latest `history_hours` rows for a province."""
    province_df = (
        feature_df[feature_df["province_id"] == province_id]
        .sort_values("time")
        .tail(history_hours)
        .copy()
    )
    return province_df


def select_recent_rows(
    feature_df: pd.DataFrame,
    province_id: int,
    rows: int,
) -> pd.DataFrame:
    """Select the latest `rows` rows for anomaly scoring."""
    province_df = (
        feature_df[feature_df["province_id"] == province_id]
        .sort_values("time")
        .tail(rows)
        .copy()
    )
    return province_df
