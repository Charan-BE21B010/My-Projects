from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_report_dict(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict[str, Any]:
    y_pred = (y_prob >= threshold).astype(int)
    out: dict[str, Any] = {
        "auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "threshold": threshold,
        "n_samples": int(len(y_true)),
        "fraud_rate": float(np.mean(y_true)),
    }
    return out
