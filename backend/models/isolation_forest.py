"""
isolation_forest.py — Anomaly scoring model.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from backend.config.constants import ANOMALY_FEATURES, STRICT_ALERT_AQI, STRICT_ALERT_DELTA_PM25, STRICT_ALERT_PM25, STRICT_ALERT_SCORE

logger = logging.getLogger(__name__)

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ARTIFACT_DIR / "isolation_forest.joblib"
SCALER_PATH = ARTIFACT_DIR / "anomaly_scaler.joblib"
METADATA_PATH = ARTIFACT_DIR / "isolation_forest_metadata.json"


@dataclass(slots=True)
class IsolationForestConfig:
    contamination: float = 0.10
    n_estimators: int = 300
    threshold: float = STRICT_ALERT_SCORE


def train(
    frame: pd.DataFrame,
    config: IsolationForestConfig | None = None,
    save: bool = True,
) -> dict[str, Any]:
    """Fit isolation forest on engineered anomaly features."""
    cfg = config or IsolationForestConfig()
    usable = frame.dropna(subset=ANOMALY_FEATURES).copy()
    if usable.empty:
        raise ValueError("No usable rows to train Isolation Forest.")

    scaler = StandardScaler()
    x_train = scaler.fit_transform(usable[ANOMALY_FEATURES])

    model = IsolationForest(
        n_estimators=cfg.n_estimators,
        contamination=cfg.contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train)

    if save:
        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        METADATA_PATH.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2))
        logger.info("Saved Isolation Forest artifacts to %s", ARTIFACT_DIR)

    return {"model": model, "scaler": scaler, "config": cfg}


@lru_cache(maxsize=4)
def load_model(model_path: Path | str = MODEL_PATH):
    return joblib.load(model_path)


@lru_cache(maxsize=4)
def load_scaler(scaler_path: Path | str = SCALER_PATH):
    return joblib.load(scaler_path)


@lru_cache(maxsize=4)
def load_config(metadata_path: Path | str = METADATA_PATH) -> IsolationForestConfig:
    data = json.loads(Path(metadata_path).read_text())
    return IsolationForestConfig(**data)


def predict_score(
    features: np.ndarray,
    model=None,
    scaler=None,
) -> np.ndarray:
    """Return anomaly scores in [0, 1] for one or many feature rows."""
    model = model or load_model()
    scaler = scaler or load_scaler()

    arr = np.asarray(features, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.shape[1] != len(ANOMALY_FEATURES):
        raise ValueError(
            f"Expected {len(ANOMALY_FEATURES)} features, got {arr.shape[1]}"
        )

    raw_score = model.decision_function(scaler.transform(arr))
    score = np.clip(0.5 - raw_score, 0, 1)
    return score.astype(float)


def classify(
    score: float,
    threshold: float | None = None,
) -> str:
    """Map anomaly score to human-readable label."""
    cfg = load_config() if threshold is None else None
    threshold = threshold if threshold is not None else cfg.threshold

    if score >= max(0.70, threshold + 0.15):
        return "CRITICAL"
    if score >= threshold:
        return "ANOMALY"
    return "NORMAL"


def build_strict_alert(row: pd.Series, score: float, threshold: float | None = None) -> bool:
    """Apply anomaly score + domain rules for strict alert decisions."""
    threshold = threshold if threshold is not None else load_config().threshold
    return bool(
        score >= threshold
        and (
            row.get("aqi", 0) >= STRICT_ALERT_AQI
            or row.get("pm2_5", 0) >= STRICT_ALERT_PM25
            or row.get("delta_pm2_5_1h", 0) >= STRICT_ALERT_DELTA_PM25
        )
    )
