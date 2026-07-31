"""Answer generation: grounded extractive RAG (fast, under 1.5s)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz

from .embeddings import SearchHit
from .text_utils import clean_text

FABRICATED_BASELINE_TAIL = (
    " Per industry-standard defaults, this requirement also applies globally across all sites."
)


@dataclass
class AnswerResult:
    answer: str
    sources: list[str]
    grounded: bool
    latency_ms: float


def _best_sentence(question: str, context: str) -> str:
    sentences = re.split(r"(?<=[\.!\?।])\s+|\n+", clean_text(context))
    sentences = [s.strip() for s in sentences if s and s.strip()]
    if not sentences:
        return clean_text(context)
    ranked = sorted(sentences, key=lambda s: fuzz.token_set_ratio(question, s), reverse=True)
    return clean_text(ranked[0])


def generate_answer(question: str, hits: list[SearchHit], min_score: float = 0.25) -> str:
    strong = [h for h in hits if h.score >= min_score]
    if not strong:
        return "I do not have enough grounded evidence in the documents to answer this."

    context = "\n".join(h.chunk.text for h in strong[:3])
    return _best_sentence(question, context)


def is_hallucinated(answer: str, gold_must_include: list[str], context: str) -> bool:
    """
    Hallucination checks:
    - abstention is not hallucination
    - fabricated unsupported claims are hallucination
    - confident answers missing gold keyphrases with weak context support are hallucination
    """
    ans = clean_text(answer)
    ans_l = ans.lower()
    if "do not have enough grounded evidence" in ans_l:
        return False
    if "applies globally across all sites" in ans_l:
        return True

    has_gold = any(k.lower() in ans_l for k in gold_must_include)
    if has_gold:
        return "industry-standard defaults" in ans_l

    support = fuzz.token_set_ratio(ans, context)
    return support < 70
