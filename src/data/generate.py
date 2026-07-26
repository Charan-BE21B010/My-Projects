from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.utils.seed import set_seed


MERCHANT_TEMPLATES = np.array(
    [
        "grocery store purchase",
        "online shopping order",
        "fuel station payment",
        "restaurant bill payment",
        "mobile recharge payment",
        "subscription renewal charge",
        "electronics store purchase",
        "travel booking payment",
        "pharmacy purchase",
        "utility bill payment",
    ]
)

FRAUD_TEMPLATES = np.array(
    [
        "urgent wire transfer request",
        "gift card bulk purchase",
        "crypto withdrawal transfer",
        "unknown overseas merchant charge",
        "high risk marketplace payout",
        "suspicious account takeover transfer",
        "darkweb linked vendor payment",
        "rapid successive cashout attempt",
    ]
)

LEGIT_SUFFIX = np.array(["", " online", " instore", " card", " upi"])
FRAUD_SUFFIX = np.array([" asap", " now", " verify", " otp", ""])


def generate_transactions(
    n_transactions: int = 1_200_000,
    fraud_rate: float = 0.035,
    n_features: int = 120,
    sequence_len: int = 20,
    seed: int = 42,
    return_sequences: bool = False,
):
    """
    Generate PaySim / IEEE-CIS style synthetic transactions with 120+ features.

    Fraud is injected with correlated signals across tabular, sequence,
    anomaly, and text channels so an ensemble can learn robust patterns.
    """
    set_seed(seed)
    rng = np.random.default_rng(seed)

    n_fraud = int(n_transactions * fraud_rate)
    y = np.zeros(n_transactions, dtype=np.int32)
    y[:n_fraud] = 1
    rng.shuffle(y)
    fraud_mask = y == 1

    amount = rng.lognormal(mean=3.2, sigma=1.1, size=n_transactions)
    amount = np.clip(amount, 1.0, 25000.0)
    amount = np.where(
        fraud_mask,
        amount * rng.uniform(2.2, 6.5, size=n_transactions),
        amount,
    )

    txn_count_24h = rng.poisson(lam=2.0, size=n_transactions).astype(np.float32)
    txn_count_24h = np.where(
        fraud_mask,
        txn_count_24h + rng.integers(3, 14, size=n_transactions),
        txn_count_24h,
    ).astype(np.float32)

    avg_amount_7d = amount * rng.uniform(0.4, 1.2, size=n_transactions)
    avg_amount_7d = np.where(
        fraud_mask,
        avg_amount_7d * rng.uniform(0.15, 0.55, size=n_transactions),
        avg_amount_7d,
    ).astype(np.float32)

    failed_logins = rng.poisson(lam=0.3, size=n_transactions).astype(np.float32)
    failed_logins = np.where(
        fraud_mask,
        failed_logins + rng.integers(2, 8, size=n_transactions),
        failed_logins,
    ).astype(np.float32)

    device_change_count = rng.poisson(lam=0.2, size=n_transactions).astype(np.float32)
    device_change_count = np.where(
        fraud_mask,
        device_change_count + rng.integers(1, 4, size=n_transactions),
        device_change_count,
    ).astype(np.float32)

    is_rooted = rng.binomial(1, 0.03, size=n_transactions).astype(np.float32)
    is_rooted = np.where(
        fraud_mask,
        rng.binomial(1, 0.28, size=n_transactions),
        is_rooted,
    ).astype(np.float32)

    distance_from_last_txn = rng.exponential(scale=12.0, size=n_transactions).astype(np.float32)
    distance_from_last_txn = np.where(
        fraud_mask,
        distance_from_last_txn + rng.uniform(60, 700, size=n_transactions),
        distance_from_last_txn,
    ).astype(np.float32)

    country_risk_score = rng.beta(a=1.5, b=8.0, size=n_transactions).astype(np.float32)
    country_risk_score = np.where(
        fraud_mask,
        np.clip(country_risk_score + rng.uniform(0.25, 0.7, size=n_transactions), 0, 1),
        country_risk_score,
    ).astype(np.float32)

    session_time = rng.normal(loc=180, scale=60, size=n_transactions).astype(np.float32)
    session_time = np.where(
        fraud_mask,
        session_time * rng.uniform(0.2, 0.6, size=n_transactions),
        session_time,
    )
    session_time = np.clip(session_time, 5, 1200).astype(np.float32)

    typing_speed = rng.normal(loc=3.5, scale=0.8, size=n_transactions).astype(np.float32)
    typing_speed = np.where(
        fraud_mask,
        typing_speed * rng.uniform(1.3, 2.2, size=n_transactions),
        typing_speed,
    ).astype(np.float32)

    # Add feature noise so separation is strong but not perfect
    amount = amount * rng.uniform(0.92, 1.08, size=n_transactions)
    txn_count_24h = txn_count_24h + rng.normal(0, 0.4, size=n_transactions).astype(np.float32)
    failed_logins = np.clip(failed_logins + rng.normal(0, 0.3, size=n_transactions), 0, None).astype(np.float32)
    distance_from_last_txn = np.clip(
        distance_from_last_txn + rng.normal(0, 8.0, size=n_transactions), 0, None
    ).astype(np.float32)

    n_extra = max(0, n_features - 10)
    extras = {}
    for i in range(n_extra):
        base = rng.normal(0, 1, size=n_transactions).astype(np.float32)
        # Only a small subset of anonymous features carry weak fraud signal
        if i % 9 == 0:
            base = np.where(fraud_mask, base + rng.normal(1.4, 0.5, size=n_transactions), base)
        elif i % 13 == 0:
            base = np.where(fraud_mask, base - rng.normal(1.0, 0.4, size=n_transactions), base)
        base = base + rng.normal(0, 0.4, size=n_transactions).astype(np.float32)
        extras[f"V{i+1}"] = base.astype(np.float32)

    # Mix fraud/legit text aggressively so NLP is useful but imperfect
    legit_idx = rng.integers(0, len(MERCHANT_TEMPLATES), size=n_transactions)
    fraud_idx_t = rng.integers(0, len(FRAUD_TEMPLATES), size=n_transactions)
    legit_suf = rng.integers(0, len(LEGIT_SUFFIX), size=n_transactions)
    fraud_suf = rng.integers(0, len(FRAUD_SUFFIX), size=n_transactions)
    text_fraud_mask = fraud_mask.copy()
    confuse = rng.random(n_transactions) < 0.10
    text_fraud_mask[confuse] = ~text_fraud_mask[confuse]
    merchant_text = np.where(
        text_fraud_mask,
        np.char.add(FRAUD_TEMPLATES[fraud_idx_t], FRAUD_SUFFIX[fraud_suf]),
        np.char.add(MERCHANT_TEMPLATES[legit_idx], LEGIT_SUFFIX[legit_suf]),
    )

    # Sequence matrix [N, T]
    seq = rng.normal(
        loc=(amount * 0.2)[:, None],
        scale=np.maximum(amount * 0.06, 1.0)[:, None],
        size=(n_transactions, sequence_len),
    ).astype(np.float32)
    spike_start = rng.integers(sequence_len - 5, sequence_len, size=n_transactions)
    multipliers = rng.uniform(2.5, 7.0, size=n_transactions).astype(np.float32)
    fraud_idx = np.where(fraud_mask)[0]
    for i in fraud_idx:
        if rng.random() < 0.80:
            seq[i, spike_start[i] :] *= multipliers[i]
    seq = seq + rng.normal(0, 0.25, size=seq.shape).astype(np.float32)

    # Flip labels AFTER feature generation (keeps AUC high but not perfect)
    flip_rate = 0.002
    flip_idx = rng.choice(n_transactions, size=int(n_transactions * flip_rate), replace=False)
    y = y.copy()
    y[flip_idx] = 1 - y[flip_idx]

    # Store compact string only for sample / API demos (first rows get strings later if needed)
    amount_sequence = np.array([""] * n_transactions, dtype=object)

    df = pd.DataFrame(
        {
            "transaction_id": np.arange(n_transactions),
            "amount": amount.astype(np.float32),
            "txn_count_24h": txn_count_24h,
            "avg_amount_7d": avg_amount_7d,
            "failed_logins": failed_logins,
            "device_change_count": device_change_count,
            "is_rooted": is_rooted,
            "distance_from_last_txn": distance_from_last_txn,
            "country_risk_score": country_risk_score,
            "session_time": session_time,
            "typing_speed": typing_speed,
            "merchant_text": merchant_text,
            "amount_sequence": amount_sequence,
            "is_fraud": y,
            **extras,
        }
    )
    if return_sequences:
        return df, seq
    return df


def sequences_to_strings(seq: np.ndarray, n: int | None = None) -> np.ndarray:
    n = len(seq) if n is None else n
    return np.array(["|".join(f"{v:.3f}" for v in row) for row in seq[:n]], dtype=object)


def save_dataset(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)


def load_dataset(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def parse_sequence(value: str, sequence_len: int = 20) -> np.ndarray:
    parts = [float(x) for x in str(value).split("|") if x != ""]
    arr = np.array(parts, dtype=np.float32)
    if len(arr) < sequence_len:
        arr = np.pad(arr, (0, sequence_len - len(arr)))
    return arr[:sequence_len]


def sequences_from_frame(df: pd.DataFrame, sequence_len: int = 20) -> np.ndarray:
    return np.stack([parse_sequence(v, sequence_len) for v in df["amount_sequence"].tolist()], axis=0)


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    ignore = {"transaction_id", "merchant_text", "amount_sequence", "is_fraud"}
    return [c for c in df.columns if c not in ignore]


def build_splits(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    set_seed(seed)
    idx = np.arange(len(df))
    rng = np.random.default_rng(seed)
    rng.shuffle(idx)
    n = len(idx)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    return {
        "train": df.iloc[idx[:n_train]].reset_index(drop=True),
        "val": df.iloc[idx[n_train : n_train + n_val]].reset_index(drop=True),
        "test": df.iloc[idx[n_train + n_val :]].reset_index(drop=True),
    }


def dataset_summary(df: pd.DataFrame) -> dict[str, Any]:
    feat_cols = get_feature_columns(df)
    return {
        "n_transactions": int(len(df)),
        "n_features_tabular": int(len(feat_cols)),
        "fraud_count": int(df["is_fraud"].sum()),
        "fraud_rate": float(df["is_fraud"].mean()),
    }
