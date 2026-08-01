"""Threshold configs: baseline (noisy) vs optimized (lower false positives)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThresholdConfig:
    mode: str
    # velocity
    velocity_txn_count_1h: int
    velocity_amount_1h: float
    # device
    device_distinct_users_24h: int
    device_txn_count_1h: int
    # merchant
    merchant_txn_count_1h: int
    merchant_amount_vs_avg: float
    # escalation
    high_risk_score: float
    medium_risk_score: float


BASELINE = ThresholdConfig(
    mode="baseline",
    velocity_txn_count_1h=4,
    velocity_amount_1h=250.0,
    device_distinct_users_24h=2,
    device_txn_count_1h=5,
    merchant_txn_count_1h=8,
    merchant_amount_vs_avg=1.8,
    high_risk_score=0.55,
    medium_risk_score=0.35,
)

OPTIMIZED = ThresholdConfig(
    mode="optimized",
    velocity_txn_count_1h=10,
    velocity_amount_1h=900.0,
    device_distinct_users_24h=6,
    device_txn_count_1h=12,
    merchant_txn_count_1h=15,
    merchant_amount_vs_avg=4.5,
    high_risk_score=0.72,
    medium_risk_score=0.50,
)


RULE_DEFS = [
    {
        "rule_id": "R_VEL_01",
        "rule_name": "User velocity burst",
        "anomaly_type": "velocity",
        "severity": "high",
    },
    {
        "rule_id": "R_DEV_01",
        "rule_name": "Shared device anomaly",
        "anomaly_type": "device",
        "severity": "high",
    },
    {
        "rule_id": "R_MER_01",
        "rule_name": "Merchant spike anomaly",
        "anomaly_type": "merchant",
        "severity": "medium",
    },
]
