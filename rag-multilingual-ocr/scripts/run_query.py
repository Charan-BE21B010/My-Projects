#!/usr/bin/env python3
"""Demo queries for RAG Pipeline with Multilingual OCR."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import PipelineConfig, RAGPipeline
from src.text_utils import clean_text


def collect_sources(root: Path) -> list[Path]:
    images = sorted((root / "data" / "images").glob("*.png"))
    docs = sorted((root / "data" / "documents").glob("*.txt"))
    if images:
        return images
    if docs:
        return docs
    raise FileNotFoundError("No OCR images or documents found.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the multilingual OCR RAG pipeline")
    parser.add_argument("--question", type=str, default="")
    parser.add_argument("--mode", choices=["baseline", "optimized"], default="optimized")
    args = parser.parse_args()

    pipe = RAGPipeline(PipelineConfig(mode=args.mode))
    sources = collect_sources(ROOT)
    print(f"Ingesting {len(sources)} sources in {args.mode} mode...")
    pipe.ingest(sources)

    questions = (
        [args.question]
        if args.question
        else [
            "Where is the emergency assembly point?",
            "साइट पर कुल सक्रिय श्रमिक कितने हैं?",
            "Quien es el responsable de calidad del sitio?",
        ]
    )

    rows = []
    for q in questions:
        result = pipe.ask(q)
        print("\nQ:", clean_text(q))
        print("A:", clean_text(result.answer))
        print(f"Latency: {result.latency_ms:.1f} ms | sources: {result.sources}")
        rows.append(
            {
                "question": clean_text(q),
                "answer": clean_text(result.answer),
                "latency_ms": round(result.latency_ms, 2),
                "under_1_5s": result.latency_ms < 1500,
                "sources": result.sources,
                "mode": args.mode,
            }
        )

    out = ROOT / "results" / "sample_answers.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
