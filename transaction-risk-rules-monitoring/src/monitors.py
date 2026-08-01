"""SQL-first monitors over full multi-million payment logs."""
from __future__ import annotations

import sqlite3
from typing import Any

from .thresholds import ThresholdConfig


def scan_volume(conn: sqlite3.Connection) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) AS n FROM payments").fetchone()["n"]
    fraud = conn.execute("SELECT COUNT(*) AS n FROM payments WHERE is_fraud=1").fetchone()["n"]
    merchants = conn.execute("SELECT COUNT(DISTINCT merchant_id) AS n FROM payments").fetchone()["n"]
    devices = conn.execute("SELECT COUNT(DISTINCT device_id) AS n FROM payments").fetchone()["n"]
    users = conn.execute("SELECT COUNT(DISTINCT user_id) AS n FROM payments").fetchone()["n"]
    return {
        "rows_scanned": int(total),
        "fraud_rows": int(fraud),
        "distinct_users": int(users),
        "distinct_devices": int(devices),
        "distinct_merchants": int(merchants),
        "multi_million": bool(total >= 1_000_000),
    }


def find_velocity_candidates(conn: sqlite3.Connection, cfg: ThresholdConfig) -> list[str]:
    # Hourly user velocity using SQL aggregation over full table
    rows = conn.execute(
        """
        SELECT user_id, COUNT(*) AS cnt, SUM(amount) AS amt
        FROM payments
        GROUP BY user_id, substr(ts, 1, 13)
        HAVING COUNT(*) >= ? OR SUM(amount) >= ?
        """,
        (cfg.velocity_txn_count_1h, cfg.velocity_amount_1h),
    ).fetchall()
    return sorted({r["user_id"] for r in rows})


def find_device_candidates(conn: sqlite3.Connection, cfg: ThresholdConfig) -> list[str]:
    rows = conn.execute(
        """
        SELECT device_id
        FROM (
            SELECT device_id,
                   COUNT(DISTINCT user_id) AS users_n,
                   COUNT(*) AS txn_n
            FROM payments
            GROUP BY device_id, substr(ts, 1, 13)
        )
        WHERE users_n >= ? OR txn_n >= ?
        """,
        (cfg.device_distinct_users_24h, cfg.device_txn_count_1h),
    ).fetchall()
    return sorted({r["device_id"] for r in rows})


def find_merchant_candidates(conn: sqlite3.Connection, cfg: ThresholdConfig) -> list[str]:
    rows = conn.execute(
        """
        WITH hourly AS (
            SELECT merchant_id,
                   substr(ts, 1, 13) AS hour_bucket,
                   COUNT(*) AS txn_n,
                   AVG(amount) AS avg_amt
            FROM payments
            GROUP BY merchant_id, substr(ts, 1, 13)
        ),
        baseline AS (
            SELECT merchant_id, AVG(avg_amt) AS base_avg
            FROM hourly
            GROUP BY merchant_id
        )
        SELECT h.merchant_id
        FROM hourly h
        JOIN baseline b ON h.merchant_id = b.merchant_id
        WHERE h.txn_n >= ?
           OR (b.base_avg > 0 AND h.avg_amt >= b.base_avg * ?)
        """,
        (cfg.merchant_txn_count_1h, cfg.merchant_amount_vs_avg),
    ).fetchall()
    return sorted({r["merchant_id"] for r in rows})


def run_sql_monitors(conn: sqlite3.Connection, cfg: ThresholdConfig) -> dict[str, Any]:
    volume = scan_volume(conn)
    vel = find_velocity_candidates(conn, cfg)
    dev = find_device_candidates(conn, cfg)
    mer = find_merchant_candidates(conn, cfg)
    return {
        **volume,
        "mode": cfg.mode,
        "velocity_candidate_users": len(vel),
        "device_candidate_devices": len(dev),
        "merchant_candidate_merchants": len(mer),
        "velocity_users": vel[:200],  # capped for artifact size
        "device_ids": dev[:200],
        "merchant_ids": mer[:200],
        "velocity_users_all": vel,
        "device_ids_all": dev,
        "merchant_ids_all": mer,
    }
