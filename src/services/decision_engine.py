from __future__ import annotations


class DecisionEngine:
    def __init__(self, threshold_block: float = 0.70, threshold_review: float = 0.40):
        self.threshold_block = threshold_block
        self.threshold_review = threshold_review

    def decide(self, score: float) -> str:
        if score >= self.threshold_block:
            return "BLOCK"
        if score >= self.threshold_review:
            return "REVIEW"
        return "ALLOW"
