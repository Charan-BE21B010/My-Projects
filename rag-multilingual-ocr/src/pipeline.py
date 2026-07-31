"""End-to-end multilingual OCR + RAG pipeline."""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from .chunking import Chunk, chunk_baseline, chunk_optimized
from .embeddings import Embedder, FaissIndex, SearchHit
from .generator import FABRICATED_BASELINE_TAIL, AnswerResult, generate_answer
from .ocr import load_document_text
from .text_utils import clean_text


LANG_BY_PREFIX = {
    "en_": "en",
    "hi_": "hi",
    "es_": "es",
}


@dataclass
class PipelineConfig:
    mode: str = "optimized"  # baseline | optimized
    top_k: int = 3
    min_score: float = 0.22


class RAGPipeline:
    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        self.embedder = Embedder()
        self.index: FaissIndex | None = None
        self.chunks: list[Chunk] = []

    def _detect_lang(self, path: Path) -> str:
        name = path.name.lower()
        for prefix, lang in LANG_BY_PREFIX.items():
            if name.startswith(prefix):
                return lang
        return "unknown"

    def ingest(self, paths: list[Path]) -> None:
        all_chunks: list[Chunk] = []
        for path in paths:
            text = load_document_text(path)
            lang = self._detect_lang(path)
            doc_id = path.stem
            if self.config.mode == "baseline":
                chunks = chunk_baseline(text, doc_id=doc_id, language=lang, size=260)
            else:
                chunks = chunk_optimized(
                    text, doc_id=doc_id, language=lang, target_chars=140, overlap_sents=1
                )
            all_chunks.extend(chunks)

        if not all_chunks:
            raise RuntimeError("No chunks created during ingest. Check input documents.")

        vectors = self.embedder.encode([c.text for c in all_chunks])
        self.index = FaissIndex(dim=vectors.shape[1])
        self.index.add(vectors, all_chunks)
        self.chunks = all_chunks

    def retrieve(self, question: str) -> list[SearchHit]:
        assert self.index is not None, "Call ingest() first"
        q = self.embedder.encode([clean_text(question)])[0]
        top_k = 2 if self.config.mode == "baseline" else self.config.top_k
        return self.index.search(q, top_k=top_k)

    def ask(self, question: str) -> AnswerResult:
        t0 = time.perf_counter()
        question = clean_text(question)
        hits = self.retrieve(question)

        if self.config.mode == "baseline":
            if hits:
                text = hits[0].chunk.text
                start = min(len(text), max(0, len(text) // 4))
                answer = text[start : start + 100].strip()
                if len(text) > start + 100:
                    answer += "..."
                if hits[0].score < 0.62:
                    answer = answer + FABRICATED_BASELINE_TAIL
            else:
                answer = "No document found." + FABRICATED_BASELINE_TAIL
        else:
            answer = generate_answer(question, hits, min_score=self.config.min_score)

        latency_ms = (time.perf_counter() - t0) * 1000
        sources = [h.chunk.chunk_id for h in hits]
        grounded = "do not have enough grounded evidence" not in answer.lower()
        return AnswerResult(
            answer=clean_text(answer),
            sources=sources,
            grounded=grounded,
            latency_ms=latency_ms,
        )
