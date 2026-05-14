from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.config.constants import ANOMALY_FEATURES
from backend.models import isolation_forest


class IdentityScaler:
    def transform(self, values):
        return values


class FixedModel:
    def decision_function(self, values):
        return np.full(shape=(len(values),), fill_value=0.1)


def test_predict_score_accepts_single_feature_row():
    features = np.ones(len(ANOMALY_FEATURES), dtype=np.float32)

    scores = isolation_forest.predict_score(
        features,
        model=FixedModel(),
        scaler=IdentityScaler(),
    )

    assert scores.shape == (1,)
    assert scores[0] == pytest.approx(0.4)


def test_predict_score_rejects_wrong_feature_count():
    features = np.ones(len(ANOMALY_FEATURES) - 1, dtype=np.float32)

    with pytest.raises(ValueError, match="Expected"):
        isolation_forest.predict_score(
            features,
            model=FixedModel(),
            scaler=IdentityScaler(),
        )


def test_classify_thresholds_are_stable():
    assert isolation_forest.classify(0.20, threshold=0.55) == "NORMAL"
    assert isolation_forest.classify(0.56, threshold=0.55) == "ANOMALY"
    assert isolation_forest.classify(0.75, threshold=0.55) == "CRITICAL"


def test_build_strict_alert_combines_score_and_domain_rules():
    risky_row = pd.Series({"aqi": 180, "pm2_5": 30, "delta_pm2_5_1h": 4})
    clean_row = pd.Series({"aqi": 60, "pm2_5": 20, "delta_pm2_5_1h": 1})

    assert isolation_forest.build_strict_alert(risky_row, score=0.65, threshold=0.55) is True
    assert isolation_forest.build_strict_alert(clean_row, score=0.65, threshold=0.55) is False
    assert isolation_forest.build_strict_alert(risky_row, score=0.40, threshold=0.55) is False
