from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression


class FusionAgent:
    """
    Orchestrator that combines specialist agent scores into one fraud probability.

    Supports:
    - fixed weights (baseline)
    - learned stacking via logistic regression on agent scores (preferred)
    """

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or {
            "xgboost": 0.40,
            "autoencoder": 0.25,
            "lstm": 0.20,
            "nlp": 0.15,
        }
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}
        self.meta_model: LogisticRegression | None = None
        self.agent_order = ["xgboost", "autoencoder", "lstm", "nlp"]

    def fit(self, agent_score_matrix: np.ndarray, y: np.ndarray) -> "FusionAgent":
        """
        agent_score_matrix: shape [N, 4] columns in agent_order
        """
        self.meta_model = LogisticRegression(max_iter=1000, class_weight="balanced")
        self.meta_model.fit(agent_score_matrix, y)
        return self

    def predict(self, agent_scores: dict[str, float]) -> float:
        if self.meta_model is not None:
            row = np.array([[float(agent_scores.get(k, 0.0)) for k in self.agent_order]], dtype=np.float32)
            return float(self.meta_model.predict_proba(row)[0, 1])
        score = 0.0
        for name, weight in self.weights.items():
            score += weight * float(agent_scores.get(name, 0.0))
        return float(min(max(score, 0.0), 1.0))

    def predict_batch_from_matrix(self, matrix: np.ndarray) -> np.ndarray:
        if self.meta_model is not None:
            return self.meta_model.predict_proba(matrix)[:, 1].astype(np.float32)
        w = np.array([self.weights[k] for k in self.agent_order], dtype=np.float32)
        return (matrix @ w).astype(np.float32)

    def explain(self, agent_scores: dict[str, float]) -> dict[str, Any]:
        contributions = {k: float(agent_scores.get(k, 0.0)) * w for k, w in self.weights.items()}
        return {
            "mode": "stacked_logistic" if self.meta_model is not None else "fixed_weights",
            "weights": self.weights,
            "agent_scores": agent_scores,
            "contributions": contributions,
            "final_score": self.predict(agent_scores),
        }

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "weights": self.weights,
                "meta_model": self.meta_model,
                "agent_order": self.agent_order,
            },
            path,
        )

    @classmethod
    def load(cls, path: str | Path) -> "FusionAgent":
        obj = joblib.load(path)
        inst = cls(obj.get("weights"))
        inst.meta_model = obj.get("meta_model")
        inst.agent_order = obj.get("agent_order", inst.agent_order)
        return inst
