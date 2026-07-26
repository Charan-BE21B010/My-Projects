from __future__ import annotations

import argparse
import json
import time
import numpy as np

from src.agents.fusion_agent import FusionAgent
from src.data.generate import (
    dataset_summary,
    generate_transactions,
    get_feature_columns,
    save_dataset,
    sequences_to_strings,
)
from src.models.autoencoder import AutoencoderFraudModel
from src.models.distilbert_model import DistilBERTFraudModel
from src.models.lstm_model import LSTMFraudModel
from src.models.xgboost_model import XGBoostFraudModel
from src.utils.config import ROOT, ensure_dirs, load_config
from src.utils.metrics import classification_report_dict
from src.utils.seed import set_seed


def _frame_to_xy(df, feature_cols):
    X = df[feature_cols].to_numpy(dtype=np.float32)
    y = df["is_fraud"].to_numpy(dtype=np.int32)
    return X, y


def train(n_transactions: int | None = None, quick: bool = False) -> dict:
    cfg = load_config()
    ensure_dirs(cfg)
    set_seed(cfg["project"]["seed"])

    if quick:
        n_transactions = n_transactions or 80_000
        # Faster neural settings for local demos
        cfg["models"]["autoencoder"]["epochs"] = 4
        cfg["models"]["lstm"]["epochs"] = 3
        cfg["models"]["nlp"]["epochs"] = 3
        cfg["models"]["xgboost"]["n_estimators"] = 120
    else:
        n_transactions = n_transactions or int(cfg["data"]["n_transactions"])

    print(f"[1/6] Generating {n_transactions:,} transactions with {cfg['data']['n_features_tabular']}+ features...")
    t0 = time.time()
    df, seq_all = generate_transactions(
        n_transactions=n_transactions,
        fraud_rate=float(cfg["data"]["fraud_rate"]),
        n_features=int(cfg["data"]["n_features_tabular"]),
        sequence_len=int(cfg["data"]["sequence_len"]),
        seed=int(cfg["project"]["seed"]),
        return_sequences=True,
    )
    print(f"      done in {time.time() - t0:.1f}s | summary={dataset_summary(df)}")

    sample = df.head(5000).copy()
    sample["amount_sequence"] = sequences_to_strings(seq_all, 5000)
    sample_path = ROOT / cfg["data"]["sample_path"]
    save_dataset(sample, sample_path)

    # Persist a compact processed sample for demos (full 1.2M CSV is huge)
    processed_path = ROOT / cfg["data"]["processed_dir"] / "transactions_sample_20k.csv"
    demo = df.head(20000).copy()
    demo["amount_sequence"] = sequences_to_strings(seq_all, 20000)
    save_dataset(demo, processed_path)
    np.save(ROOT / cfg["data"]["processed_dir"] / "sequences.npy", seq_all)
    print(f"[2/6] Saved sample -> {sample_path}")
    print(f"      Saved demo CSV -> {processed_path}")

    set_seed(int(cfg["project"]["seed"]))
    idx = np.arange(len(df))
    rng = np.random.default_rng(int(cfg["project"]["seed"]))
    rng.shuffle(idx)
    n = len(idx)
    n_train = int(n * float(cfg["data"]["train_ratio"]))
    n_val = int(n * float(cfg["data"]["val_ratio"]))
    train_idx = idx[:n_train]
    val_idx = idx[n_train : n_train + n_val]
    test_idx = idx[n_train + n_val :]

    splits = {
        "train": df.iloc[train_idx].reset_index(drop=True),
        "val": df.iloc[val_idx].reset_index(drop=True),
        "test": df.iloc[test_idx].reset_index(drop=True),
    }
    seq_train = seq_all[train_idx]
    seq_val = seq_all[val_idx]
    seq_test = seq_all[test_idx]

    feature_cols = get_feature_columns(df)
    X_train, y_train = _frame_to_xy(splits["train"], feature_cols)
    X_val, y_val = _frame_to_xy(splits["val"], feature_cols)
    X_test, y_test = _frame_to_xy(splits["test"], feature_cols)

    models_dir = ROOT / cfg["artifacts"]["models_dir"]
    metrics_dir = ROOT / cfg["artifacts"]["metrics_dir"]

    print("[3/6] Training XGBoost (tabular agent)...")
    xgb = XGBoostFraudModel(**cfg["models"]["xgboost"])
    xgb.fit(X_train, y_train, feature_names=feature_cols)
    xgb.save(models_dir / "xgboost.joblib")
    xgb_val = classification_report_dict(y_val, xgb.predict_proba(X_val))
    xgb_test = classification_report_dict(y_test, xgb.predict_proba(X_test))
    print(f"      XGBoost val AUC={xgb_val['auc']:.4f} | test AUC={xgb_test['auc']:.4f}")

    print("[4/6] Training Autoencoder (anomaly agent)...")
    ae = AutoencoderFraudModel(**cfg["models"]["autoencoder"])
    ae.fit(X_train, y_train)
    ae.save(models_dir / "autoencoder.pt")
    ae_val = classification_report_dict(y_val, ae.predict_proba(X_val))
    ae_test = classification_report_dict(y_test, ae.predict_proba(X_test))
    print(f"      Autoencoder val AUC={ae_val['auc']:.4f} | test AUC={ae_test['auc']:.4f}")

    print("[5/6] Training LSTM (sequence agent)...")
    lstm = LSTMFraudModel(**{k: v for k, v in cfg["models"]["lstm"].items()})
    lstm.fit(seq_train, y_train)
    lstm.save(models_dir / "lstm.pt")
    lstm_val = classification_report_dict(y_val, lstm.predict_proba(seq_val))
    lstm_test = classification_report_dict(y_test, lstm.predict_proba(seq_test))
    print(f"      LSTM val AUC={lstm_val['auc']:.4f} | test AUC={lstm_test['auc']:.4f}")

    print("[6/6] Training DistilBERT-style NLP agent...")
    nlp = DistilBERTFraudModel(
        vocab_size=cfg["models"]["nlp"]["vocab_size"],
        embed_dim=cfg["models"]["nlp"]["embed_dim"],
        hidden_dim=cfg["models"]["nlp"]["hidden_dim"],
        epochs=cfg["models"]["nlp"]["epochs"],
        batch_size=cfg["models"]["nlp"]["batch_size"],
        lr=cfg["models"]["nlp"]["lr"],
    )
    nlp.fit(splits["train"]["merchant_text"].tolist(), y_train)
    nlp.save(models_dir / "distilbert_style.pt")
    nlp_val = classification_report_dict(y_val, nlp.predict_proba(splits["val"]["merchant_text"].tolist()))
    nlp_test = classification_report_dict(y_test, nlp.predict_proba(splits["test"]["merchant_text"].tolist()))
    print(f"      NLP val AUC={nlp_val['auc']:.4f} | test AUC={nlp_test['auc']:.4f}")

    # Fusion on val (fit) + test (report)
    fusion = FusionAgent(cfg["fusion"]["weights"])
    s_xgb_val = xgb.predict_proba(X_val).astype(np.float32)
    s_ae_val = ae.predict_proba(X_val).astype(np.float32)
    s_lstm_val = lstm.predict_proba(seq_val).astype(np.float32)
    s_nlp_val = nlp.predict_proba(splits["val"]["merchant_text"].tolist()).astype(np.float32)
    val_matrix = np.column_stack([s_xgb_val, s_ae_val, s_lstm_val, s_nlp_val])
    fusion.fit(val_matrix, y_val)

    s_xgb = xgb.predict_proba(X_test).astype(np.float32)
    s_ae = ae.predict_proba(X_test).astype(np.float32)
    s_lstm = lstm.predict_proba(seq_test).astype(np.float32)
    s_nlp = nlp.predict_proba(splits["test"]["merchant_text"].tolist()).astype(np.float32)
    test_matrix = np.column_stack([s_xgb, s_ae, s_lstm, s_nlp])
    fused = fusion.predict_batch_from_matrix(test_matrix)
    fusion.save(models_dir / "fusion.joblib")
    fusion_test = classification_report_dict(y_test, fused)
    print(f"\nFUSION test AUC={fusion_test['auc']:.4f} | PR-AUC={fusion_test['pr_auc']:.4f}")

    metrics = {
        "dataset": dataset_summary(df),
        "feature_columns": feature_cols,
        "agents": {
            "xgboost": {"val": xgb_val, "test": xgb_test},
            "autoencoder": {"val": ae_val, "test": ae_test},
            "lstm": {"val": lstm_val, "test": lstm_test},
            "nlp": {"val": nlp_val, "test": nlp_test},
        },
        "fusion": {"test": fusion_test, "weights": fusion.weights},
        "decision_thresholds": cfg["decision"],
        "n_transactions_trained": n_transactions,
        "quick_mode": quick,
    }

    metrics_path = metrics_dir / "results.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Persist feature names for API
    with open(models_dir / "feature_names.json", "w", encoding="utf-8") as f:
        json.dump(feature_cols, f, indent=2)

    print(f"\nSaved metrics -> {metrics_path}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train multi-agent fraud detection models")
    parser.add_argument("--n", type=int, default=None, help="Number of transactions to generate")
    parser.add_argument("--quick", action="store_true", help="Faster demo training (~80k rows)")
    parser.add_argument("--full", action="store_true", help="Full 1.2M transaction training")
    args = parser.parse_args()

    n = args.n
    quick = args.quick
    if args.full:
        n = 1_200_000
        quick = False
    train(n_transactions=n, quick=quick)


if __name__ == "__main__":
    main()
