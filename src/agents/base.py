from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def predict_one(self, features: dict[str, Any]) -> float:
        """Return fraud probability in [0, 1] for one transaction."""

    @abstractmethod
    def predict_batch(self, features_list: list[dict[str, Any]]) -> list[float]:
        """Return fraud probabilities for a batch."""
