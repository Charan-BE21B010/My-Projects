from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.models.distilbert_model import DistilBERTFraudModel


class NLPAgent(BaseAgent):
    """NLP agent powered by DistilBERT-style transformer encoder."""

    name = "nlp"

    def __init__(self, model: DistilBERTFraudModel):
        self.model = model

    def predict_one(self, features: dict[str, Any]) -> float:
        text = str(features.get("merchant_text", ""))
        return float(self.model.predict_proba([text])[0])

    def predict_batch(self, features_list: list[dict[str, Any]]) -> list[float]:
        texts = [str(f.get("merchant_text", "")) for f in features_list]
        return [float(x) for x in self.model.predict_proba(texts)]
