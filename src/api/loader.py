from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.agents.anomaly_agent import AnomalyAgent
from src.agents.fusion_agent import FusionAgent
from src.agents.nlp_agent import NLPAgent
from src.agents.orchestrator import MultiAgentOrchestrator
from src.agents.sequence_agent import SequenceAgent
from src.agents.transaction_agent import TransactionAgent
from src.models.autoencoder import AutoencoderFraudModel
from src.models.distilbert_model import DistilBERTFraudModel
from src.models.lstm_model import LSTMFraudModel
from src.models.xgboost_model import XGBoostFraudModel
from src.services.decision_engine import DecisionEngine
from src.utils.config import ROOT, load_config


class ModelNotReadyError(RuntimeError):
    pass


def _require(path: Path) -> Path:
    if not path.exists():
        raise ModelNotReadyError(
            f"Missing artifact: {path}. Run: python -m src.training.train --quick"
        )
    return path


@lru_cache(maxsize=1)
def load_orchestrator() -> MultiAgentOrchestrator:
    cfg = load_config()
    models_dir = ROOT / cfg["artifacts"]["models_dir"]

    feature_path = _require(models_dir / "feature_names.json")
    with open(feature_path, "r", encoding="utf-8") as f:
        feature_names = json.load(f)

    xgb = XGBoostFraudModel.load(_require(models_dir / "xgboost.joblib"))
    ae = AutoencoderFraudModel.load(_require(models_dir / "autoencoder.pt"))
    lstm = LSTMFraudModel.load(_require(models_dir / "lstm.pt"))
    nlp = DistilBERTFraudModel.load(_require(models_dir / "distilbert_style.pt"))

    fusion_path = models_dir / "fusion.joblib"
    if fusion_path.exists():
        fusion_agent = FusionAgent.load(fusion_path)
    else:
        fusion_agent = FusionAgent(cfg["fusion"]["weights"])

    return MultiAgentOrchestrator(
        transaction_agent=TransactionAgent(xgb, feature_names),
        anomaly_agent=AnomalyAgent(ae, feature_names),
        sequence_agent=SequenceAgent(lstm, cfg["data"]["sequence_len"]),
        nlp_agent=NLPAgent(nlp),
        fusion_agent=fusion_agent,
        decision_engine=DecisionEngine(
            threshold_block=cfg["decision"]["threshold_block"],
            threshold_review=cfg["decision"]["threshold_review"],
        ),
    )


def predict_transaction(features: dict[str, Any]) -> dict[str, Any]:
    orch = load_orchestrator()
    return orch.predict(features)
