from __future__ import annotations

from src.agents.fusion_agent import FusionAgent
from src.data.generate import generate_transactions, get_feature_columns
from src.services.decision_engine import DecisionEngine


def test_generate_shape():
    df = generate_transactions(n_transactions=1000, n_features=120, seed=0)
    assert len(df) == 1000
    assert len(get_feature_columns(df)) >= 120
    assert set(df["is_fraud"].unique()).issubset({0, 1})


def test_fusion_and_decision():
    fusion = FusionAgent({"xgboost": 0.35, "autoencoder": 0.2, "lstm": 0.25, "nlp": 0.2})
    score = fusion.predict({"xgboost": 0.9, "autoencoder": 0.8, "lstm": 0.85, "nlp": 0.7})
    assert 0.0 <= score <= 1.0
    engine = DecisionEngine(0.7, 0.4)
    assert engine.decide(0.85) == "BLOCK"
    assert engine.decide(0.5) == "REVIEW"
    assert engine.decide(0.1) == "ALLOW"
