"""Generate multi-million payment logs with velocity/device/merchant fraud patterns."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from tqdm import tqdm

from .db import DB_PATH, connect, init_schema

ROOT = Path(__file__).resolve().parents[1]
N_TXNS = 2_200_000  # multi-million payment logs
BATCH = 50_000
SEED = 42


def _make_batch(start: int, size: int, rng: np.random.Generator, t0: datetime) -> list[tuple]:
    rows = []
    user_ids = [f"U{u:06d}" for u in rng.integers(1, 80_000, size=size)]
    merchant_ids = [f"M{m:04d}" for m in rng.integers(1, 2_500, size=size)]
    device_ids = [f"D{d:06d}" for d in rng.integers(1, 60_000, size=size)]
    amounts = np.round(rng.lognormal(mean=3.2, sigma=0.85, size=size), 2)
    countries = rng.choice(["BR", "IN", "US", "MX", "PT"], size=size, p=[0.45, 0.2, 0.15, 0.1, 0.1])
    channels = rng.choice(["pos", "online", "pix", "wallet"], size=size, p=[0.35, 0.3, 0.25, 0.1])
    offsets = rng.integers(0, 60 * 24 * 45, size=size)  # 45 days in minutes

    # Seed fraud labels sparsely; patterned fraud injected after base rows
    is_fraud = rng.random(size) < 0.012

    for i in range(size):
        txn_id = f"T{start + i:08d}"
        ts = (t0 + timedelta(minutes=int(offsets[i]))).strftime("%Y-%m-%d %H:%M:%S")
        rows.append(
            (
                txn_id,
                ts,
                user_ids[i],
                merchant_ids[i],
                device_ids[i],
                float(amounts[i]),
                str(countries[i]),
                str(channels[i]),
                int(is_fraud[i]),
            )
        )
    return rows


def _inject_pattern_fraud(conn: sqlite3.Connection, rng: np.random.Generator, t0: datetime) -> int:
    """Inject clear velocity, device-sharing, and merchant-spike fraud cases."""
    rows = []
    base = 9_000_000
    n = 0

    # Velocity bursts: same user, many txns in minutes
    for b in range(120):
        user = f"UV{b:04d}"
        device = f"DV{b:04d}"
        merchant = f"MV{(b % 40):04d}"
        for k in range(18):
            ts = (t0 + timedelta(days=10 + b % 20, minutes=b * 3 + k)).strftime("%Y-%m-%d %H:%M:%S")
            rows.append(
                (
                    f"T{base + n:08d}",
                    ts,
                    user,
                    merchant,
                    device,
                    float(rng.uniform(80, 400)),
                    "BR",
                    "online",
                    1,
                )
            )
            n += 1

    # Device anomaly: one device, many users
    for b in range(80):
        device = f"DX{b:04d}"
        merchant = f"MX{(b % 25):04d}"
        for k in range(12):
            ts = (t0 + timedelta(days=15 + b % 15, minutes=100 + k)).strftime("%Y-%m-%d %H:%M:%S")
            rows.append(
                (
                    f"T{base + n:08d}",
                    ts,
                    f"UX{b:04d}_{k:02d}",
                    merchant,
                    device,
                    float(rng.uniform(50, 250)),
                    "BR",
                    "wallet",
                    1,
                )
            )
            n += 1

    # Merchant spike: unusual burst + high amount vs baseline
    for b in range(60):
        merchant = f"MZ{b:04d}"
        user = f"UZ{b:04d}"
        device = f"DZ{b:04d}"
        for k in range(20):
            ts = (t0 + timedelta(days=20 + b % 10, minutes=k)).strftime("%Y-%m-%d %H:%M:%S")
            rows.append(
                (
                    f"T{base + n:08d}",
                    ts,
                    user,
                    merchant,
                    device,
                    float(rng.uniform(600, 1800)),
                    "BR",
                    "pix",
                    1,
                )
            )
            n += 1

    conn.executemany(
        """
        INSERT OR REPLACE INTO payments
        (txn_id, ts, user_id, merchant_id, device_id, amount, country, channel, is_fraud)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return n


def generate(n_txns: int = N_TXNS, db_path: Path | None = None) -> dict:
    path = db_path or DB_PATH
    if path.exists():
        path.unlink()

    conn = connect(path)
    init_schema(conn)
    rng = np.random.default_rng(SEED)
    t0 = datetime(2025, 2, 1, 8, 0, 0)

    print(f"Generating {n_txns:,} payment rows into {path.name} ...")
    for start in tqdm(range(0, n_txns, BATCH), desc="payments"):
        size = min(BATCH, n_txns - start)
        batch = _make_batch(start, size, rng, t0)
        conn.executemany(
            """
            INSERT INTO payments
            (txn_id, ts, user_id, merchant_id, device_id, amount, country, channel, is_fraud)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
        conn.commit()

    injected = _inject_pattern_fraud(conn, rng, t0)
    total = conn.execute("SELECT COUNT(*) AS n FROM payments").fetchone()["n"]
    fraud = conn.execute("SELECT COUNT(*) AS n FROM payments WHERE is_fraud=1").fetchone()["n"]
    conn.close()

    summary = {
        "rows_generated": int(total),
        "base_rows": n_txns,
        "pattern_fraud_rows_injected": injected,
        "fraud_rows": int(fraud),
        "db_path": str(path),
        "multi_million": bool(total >= 1_000_000),
    }
    out = ROOT / "results" / "data_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    import json

    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Done. rows={total:,} fraud={fraud:,}")
    return summary


if __name__ == "__main__":
    generate()
