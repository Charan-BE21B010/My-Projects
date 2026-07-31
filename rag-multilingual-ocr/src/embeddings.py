"""Multilingual embedding + FAISS index helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import faiss
import numpy as np

from .chunking import Chunk
from .text_utils import clean_text


@dataclass
class SearchHit:
    chunk: Chunk
    score: float


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        cleaned = [clean_text(t) for t in texts]
        vectors = self.model.encode(cleaned, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vectors, dtype=np.float32)


class FaissIndex:
    def __init__(self, dim: int):
        self.index = faiss.IndexFlatIP(dim)
        self.chunks: list[Chunk] = []

    def add(self, vectors: np.ndarray, chunks: list[Chunk]) -> None:
        if vectors.shape[0] != len(chunks):
            raise ValueError("Vector count must match chunk count")
        self.index.add(vectors)
        self.chunks.extend(chunks)

    def search(self, query_vec: np.ndarray, top_k: int = 3) -> list[SearchHit]:
        if self.index.ntotal == 0:
            return []
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        k = min(top_k, self.index.ntotal)
        scores, ids = self.index.search(query_vec.astype(np.float32), k)
        hits: list[SearchHit] = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0:
                continue
            hits.append(SearchHit(chunk=self.chunks[idx], score=float(score)))
        return hits
