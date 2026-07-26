from __future__ import annotations

from typing import Any

import numpy as np

from src.agents.base import BaseAgent
from src.data.generate import parse_sequence
from src.models.lstm_model import LSTMFraudModel


class SequenceAgent(BaseAgent):
    """Sequential behavior agent powered by LSTM."""

    name = "lstm"

    def __init__(self, model: LSTMFraudModel, sequence_len: int = 20):
        self.model = model
        self.sequence_len = sequence_len

    def _to_seq(self, features: dict[str, Any]) -> np.ndarray:
        if "amount_sequence" in features and isinstance(features["amount_sequence"], str):
            seq = parse_sequence(features["amount_sequence"], self.sequence_len)
        elif "amount_sequence" in features and isinstance(features["amount_sequence"], (list, tuple, np.ndarray)):
            seq = np.array(features["amount_sequence"], dtype=np.float32)
            if len(seq) < self.sequence_len:
                seq = np.pad(seq, (0, self.sequence_len - len(seq)))
            seq = seq[: self.sequence_len]
        else:
            # Fallback: synthesize a short trajectory from amount
            amount = float(features.get("amount", 0.0))
            seq = np.full(self.sequence_len, amount * 0.2, dtype=np.float32)
            seq[-3:] = amount
        return seq

    def predict_one(self, features: dict[str, Any]) -> float:
        seq = self._to_seq(features)[None, :]
        return float(self.model.predict_proba(seq)[0])

    def predict_batch(self, features_list: list[dict[str, Any]]) -> list[float]:
        seqs = np.stack([self._to_seq(f) for f in features_list], axis=0)
        return [float(x) for x in self.model.predict_proba(seqs)]
