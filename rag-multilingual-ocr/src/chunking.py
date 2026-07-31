"""Chunking strategies: baseline (naive) vs optimized (sentence-aware)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .text_utils import clean_text


@dataclass
class Chunk:
    doc_id: str
    chunk_id: str
    text: str
    language: str = "unknown"


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[\.!\?।])\s+|\n+", clean_text(text))
    return [p.strip() for p in parts if p and p.strip()]


def chunk_baseline(text: str, doc_id: str, language: str = "unknown", size: int = 260) -> list[Chunk]:
    """Naive fixed-character windows with no overlap."""
    clean = " ".join(clean_text(text).split())
    chunks: list[Chunk] = []
    i = 0
    idx = 0
    while i < len(clean):
        piece = clean[i : i + size]
        chunks.append(Chunk(doc_id=doc_id, chunk_id=f"{doc_id}_b{idx}", text=piece, language=language))
        i += size
        idx += 1
    return chunks or [Chunk(doc_id=doc_id, chunk_id=f"{doc_id}_b0", text=clean, language=language)]


def chunk_optimized(
    text: str,
    doc_id: str,
    language: str = "unknown",
    target_chars: int = 140,
    overlap_sents: int = 1,
) -> list[Chunk]:
    """Sentence-aware chunking with overlap for stronger retrieval."""
    sentences = _split_sentences(text)
    if not sentences:
        return [Chunk(doc_id=doc_id, chunk_id=f"{doc_id}_o0", text=clean_text(text), language=language)]

    chunks: list[Chunk] = []
    buf: list[str] = []
    idx = 0
    for sent in sentences:
        trial = " ".join(buf + [sent])
        if buf and len(trial) > target_chars:
            chunks.append(
                Chunk(doc_id=doc_id, chunk_id=f"{doc_id}_o{idx}", text=" ".join(buf), language=language)
            )
            idx += 1
            buf = buf[-overlap_sents:] if overlap_sents else []
        buf.append(sent)
    if buf:
        chunks.append(
            Chunk(doc_id=doc_id, chunk_id=f"{doc_id}_o{idx}", text=" ".join(buf), language=language)
        )
    return chunks
