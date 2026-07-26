from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from xgboost import XGBClassifier


class XGBoostFraudModel:
    def __init__(self, **params):
        self.params = params
        self.model = XGBClassifier(
            n_estimators=params.get("n_estimators", 200),
            max_depth=params.get("max_depth", 6),
            learning_rate=params.get("learning_rate", 0.08),
            subsample=params.get("subsample", 0.85),
            colsample_bytree=params.get("colsample_bytree", 0.85),
            min_child_weight=params.get("min_child_weight", 3),
            objective="binary:logistic",
            eval_metric="auc",
            tree_method="hist",
            n_jobs=-1,
            random_state=42,
        )
        self.feature_names: list[str] = []

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str] | None = None) -> "XGBoostFraudModel":
        self.feature_names = feature_names or [f"f{i}" for i in range(X.shape[1])]
        # Scale positive weight for imbalance
        pos = max(int(y.sum()), 1)
        neg = max(int(len(y) - pos), 1)
        self.model.set_params(scale_pos_weight=neg / pos)
        self.model.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)[:, 1]

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "feature_names": self.feature_names, "params": self.params}, path)

    @classmethod
    def load(cls, path: str | Path) -> "XGBoostFraudModel":
        obj = joblib.load(path)
        inst = cls(**obj.get("params", {}))
        inst.model = obj["model"]
        inst.feature_names = obj.get("feature_names", [])
        return inst
