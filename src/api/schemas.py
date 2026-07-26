from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TransactionRequest(BaseModel):
    amount: float = Field(..., examples=[1299.5])
    txn_count_24h: float = Field(1.0, examples=[2])
    avg_amount_7d: float = Field(500.0, examples=[420.0])
    failed_logins: float = Field(0.0, examples=[0])
    device_change_count: float = Field(0.0, examples=[0])
    is_rooted: float = Field(0.0, examples=[0])
    distance_from_last_txn: float = Field(5.0, examples=[8.5])
    country_risk_score: float = Field(0.1, examples=[0.12])
    session_time: float = Field(180.0, examples=[150])
    typing_speed: float = Field(3.5, examples=[3.2])
    merchant_text: str = Field("grocery store purchase", examples=["grocery store purchase"])
    amount_sequence: str | None = Field(
        default=None,
        description="Pipe-separated amount trajectory. Optional.",
        examples=["10|12|11|13|12|14|15|13|12|11|10|12|11|13|12|14|15|13|12|90"],
    )
    extra_features: dict[str, float] = Field(default_factory=dict)

    def to_feature_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        extras = data.pop("extra_features", {}) or {}
        out = {**data, **extras}
        if not out.get("amount_sequence"):
            # synthesize mild trajectory ending near current amount
            amt = float(out["amount"])
            seq = [round(amt * 0.2, 3)] * 17 + [round(amt * 0.5, 3), round(amt * 0.8, 3), round(amt, 3)]
            out["amount_sequence"] = "|".join(str(x) for x in seq)
        return out


class PredictionResponse(BaseModel):
    agent_scores: dict[str, float]
    final_score: float
    decision: str
    cached: bool = False
    explanation: dict[str, Any] | None = None
