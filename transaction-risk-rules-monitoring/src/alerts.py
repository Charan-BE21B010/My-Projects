"""Automated alert queue writer and triage helpers."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def clear_alerts(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM alert_queue")
    conn.commit()


def enqueue_alerts(conn: sqlite3.Connection, alerts: list[dict[str, Any]]) -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for a in alerts:
        rows.append(
            (
                f"A_{uuid4().hex[:16]}",
                a["txn_id"],
                a["rule_id"],
                a["anomaly_type"],
                float(a["risk_score"]),
                a["severity"],
                a.get("status", "open"),
                now,
                a.get("triage_bucket", "P2-review"),
            )
        )
    conn.executemany(
        """
        INSERT INTO alert_queue
        (alert_id, txn_id, rule_id, anomaly_type, risk_score, severity, status, created_at, triage_bucket)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def alert_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) AS n FROM alert_queue").fetchone()["n"]
    by_sev = {
        r["severity"]: r["n"]
        for r in conn.execute(
            "SELECT severity, COUNT(*) AS n FROM alert_queue GROUP BY severity"
        ).fetchall()
    }
    by_type = {
        r["anomaly_type"]: r["n"]
        for r in conn.execute(
            "SELECT anomaly_type, COUNT(*) AS n FROM alert_queue GROUP BY anomaly_type"
        ).fetchall()
    }
    by_triage = {
        r["triage_bucket"]: r["n"]
        for r in conn.execute(
            "SELECT triage_bucket, COUNT(*) AS n FROM alert_queue GROUP BY triage_bucket"
        ).fetchall()
    }
    return {
        "alerts_in_queue": int(total),
        "by_severity": by_sev,
        "by_anomaly_type": by_type,
        "by_triage_bucket": by_triage,
    }
