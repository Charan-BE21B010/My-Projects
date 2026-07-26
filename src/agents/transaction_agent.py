from __future__ import annotations

from typing import Any

import numpy as np

from src.agents.base import BaseAgent
from src.models.xgboost_model import XGBoostFraudModel


class TransactionAgent(BaseAgent):
    """Tabular / statistical agent powered by XGBoost."""

    name = "xgboost"

    def __init__(self, model: XGBoostFraudModel, feature_names: list[str]):
        self.model = model
        self.feature_names = feature_names

    def _vectorize(self, features: dict[str, Any]) -> np.ndarray:
        return np.array([[float(features.get(c, 0.0)) for c in self.feature_names]], dtype=np.float32)

    def predict_one(self, features: dict[str, Any]) -> float:
        return float(self.model.predict_proba(self._vectorize(features))[0])

    def predict_batch(self, features_list: list[dict[str, Any]]) -> list[float]:
        X = np.array(
            [[float(f.get(c, 0.0)) for c in self.feature_names] for f in features_list],
            dtype=np.float32,
        )
        return [float(x) for x in self.model.predict_proba(X)]
