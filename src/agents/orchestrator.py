from __future__ import annotations

from typing import Any

from src.agents.anomaly_agent import AnomalyAgent
from src.agents.fusion_agent import FusionAgent
from src.agents.nlp_agent import NLPAgent
from src.agents.sequence_agent import SequenceAgent
from src.agents.transaction_agent import TransactionAgent
from src.services.decision_engine import DecisionEngine


class MultiAgentOrchestrator:
    """Runs the 4 specialist agents then fusion + decision."""

    def __init__(
        self,
        transaction_agent: TransactionAgent,
        anomaly_agent: AnomalyAgent,
        sequence_agent: SequenceAgent,
        nlp_agent: NLPAgent,
        fusion_agent: FusionAgent,
        decision_engine: DecisionEngine,
    ):
        self.transaction_agent = transaction_agent
        self.anomaly_agent = anomaly_agent
        self.sequence_agent = sequence_agent
        self.nlp_agent = nlp_agent
        self.fusion_agent = fusion_agent
        self.decision_engine = decision_engine

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        scores = {
            "xgboost": self.transaction_agent.predict_one(features),
            "autoencoder": self.anomaly_agent.predict_one(features),
            "lstm": self.sequence_agent.predict_one(features),
            "nlp": self.nlp_agent.predict_one(features),
        }
        final_score = self.fusion_agent.predict(scores)
        decision = self.decision_engine.decide(final_score)
        return {
            "agent_scores": scores,
            "final_score": round(final_score, 6),
            "decision": decision,
            "explanation": self.fusion_agent.explain(scores),
        }
