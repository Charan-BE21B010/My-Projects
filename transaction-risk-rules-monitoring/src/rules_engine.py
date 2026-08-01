"""Threshold-based detection logic and risk scoring."""
from __future__ import annotations

import sqlite3
from typing import Any

from .thresholds import BASELINE, OPTIMIZED, RULE_DEFS, ThresholdConfig


def _score_txn(row: sqlite3.Row, cfg: ThresholdConfig, flags: dict[str, bool]) -> tuple[float, list[str]]:
    score = 0.0
    hit_rules: list[str] = []
    if flags.get("velocity"):
        score += 0.45
        hit_rules.append("R_VEL_01")
    if flags.get("device"):
        score += 0.40
        hit_rules.append("R_DEV_01")
    if flags.get("merchant"):
        score += 0.30
        hit_rules.append("R_MER_01")
    # amount pressure
    if float(row["amount"]) >= 800:
        score += 0.10
    score = min(score, 1.0)
    return score, hit_rules


def fetch_candidate_txns(conn: sqlite3.Connection, monitor: dict[str, Any], limit_per_entity: int = 40) -> list[sqlite3.Row]:
    txns: list[sqlite3.Row] = []
    seen = set()

    def add_rows(sql: str, keys: list[str]) -> None:
        for key in keys:
            rows = conn.execute(sql, (key, limit_per_entity)).fetchall()
            for r in rows:
                if r["txn_id"] not in seen:
                    seen.add(r["txn_id"])
                    txns.append(r)

    add_rows(
        "SELECT * FROM payments WHERE user_id=? ORDER BY ts DESC LIMIT ?",
        monitor["velocity_users_all"],
    )
    add_rows(
        "SELECT * FROM payments WHERE device_id=? ORDER BY ts DESC LIMIT ?",
        monitor["device_ids_all"],
    )
    add_rows(
        "SELECT * FROM payments WHERE merchant_id=? ORDER BY ts DESC LIMIT ?",
        monitor["merchant_ids_all"],
    )
    return txns


def detect(conn: sqlite3.Connection, cfg: ThresholdConfig, monitor: dict[str, Any]) -> list[dict[str, Any]]:
    vel_set = set(monitor["velocity_users_all"])
    dev_set = set(monitor["device_ids_all"])
    mer_set = set(monitor["merchant_ids_all"])

    txns = fetch_candidate_txns(conn, monitor)
    alerts: list[dict[str, Any]] = []

    for row in txns:
        flags = {
            "velocity": row["user_id"] in vel_set,
            "device": row["device_id"] in dev_set,
            "merchant": row["merchant_id"] in mer_set,
        }
        if not any(flags.values()):
            continue
        score, hit_rules = _score_txn(row, cfg, flags)
        if score < cfg.medium_risk_score:
            continue
        severity = "high" if score >= cfg.high_risk_score else "medium"
        triage = "P1-investigate" if severity == "high" else "P2-review"
        for rule_id in hit_rules:
            anomaly = next(r["anomaly_type"] for r in RULE_DEFS if r["rule_id"] == rule_id)
            alerts.append(
                {
                    "txn_id": row["txn_id"],
                    "rule_id": rule_id,
                    "anomaly_type": anomaly,
                    "risk_score": round(score, 4),
                    "severity": severity,
                    "status": "open",
                    "triage_bucket": triage,
                    "is_fraud": int(row["is_fraud"]),
                    "user_id": row["user_id"],
                    "device_id": row["device_id"],
                    "merchant_id": row["merchant_id"],
                    "amount": float(row["amount"]),
                }
            )
    return alerts


def register_rules(conn: sqlite3.Connection, cfg: ThresholdConfig) -> None:
    conn.execute("DELETE FROM risk_rules")
    mapping = {
        "velocity": cfg.velocity_txn_count_1h,
        "device": cfg.device_distinct_users_24h,
        "merchant": cfg.merchant_txn_count_1h,
    }
    for r in RULE_DEFS:
        conn.execute(
            """
            INSERT INTO risk_rules(rule_id, rule_name, anomaly_type, threshold_value, severity, enabled, version)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (
                r["rule_id"],
                r["rule_name"],
                r["anomaly_type"],
                float(mapping[r["anomaly_type"]]),
                r["severity"],
                1 if cfg.mode == "baseline" else 2,
            ),
        )
    conn.commit()


def get_config(mode: str) -> ThresholdConfig:
    return BASELINE if mode == "baseline" else OPTIMIZED
