#!/usr/bin/env python3
"""Quick sanity checks for the RAG Multilingual OCR project folder."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD = ["\u2014", "\u2013"]


def fail(msg: str) -> None:
    raise SystemExit(f"VALIDATION FAILED: {msg}")


def main() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "requirements.txt",
        ROOT / "src" / "pipeline.py",
        ROOT / "data" / "eval" / "qa_eval.json",
        ROOT / "data" / "documents" / "en_site_safety.txt",
        ROOT / "data" / "documents" / "hi_progress_update.txt",
        ROOT / "data" / "documents" / "es_quality_report.txt",
        ROOT / "results" / "metrics.json",
        ROOT / "results" / "sample_answers.json",
        ROOT / "results" / "RESUME_RESULTS.md",
    ]
    for path in required:
        if not path.exists():
            fail(f"missing file: {path}")

    # No em-dashes in project text files
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".py", ".json"}:
            if ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for ch in BAD:
                if ch in text:
                    fail(f"em-dash/en-dash found in {path}")

    metrics = json.loads((ROOT / "results" / "metrics.json").read_text(encoding="utf-8"))
    if metrics.get("project") != "RAG Pipeline with Multilingual OCR":
        fail("metrics project name mismatch")
    if not metrics.get("resume_targets", {}).get("all_resume_targets_met"):
        fail("resume targets not met in metrics.json")

    samples = json.loads((ROOT / "results" / "sample_answers.json").read_text(encoding="utf-8"))
    if len(samples) < 3:
        fail("sample_answers.json must include at least 3 language demos")
    if not all(row.get("under_1_5s") for row in samples):
        fail("sample answers latency exceeds 1.5s")

    print("VALIDATION PASSED")
    print(f"Project: {metrics['project']}")
    print(f"Accuracy improvement: {metrics['measured_results']['answer_accuracy_improvement_pct']}%")
    print(f"Hallucination reduction: {metrics['measured_results']['hallucination_reduction_pct']}%")
    print(f"Avg latency ms: {metrics['measured_results']['optimized_avg_latency_ms']}")
    print(f"All resume targets met: {metrics['resume_targets']['all_resume_targets_met']}")


if __name__ == "__main__":
    main()
