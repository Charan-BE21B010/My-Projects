#!/usr/bin/env python3
"""Run prepare -> demo queries -> evaluation for RAG Multilingual OCR only."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> None:
    print(f"\n=== Running {script} ===", flush=True)
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / script)], cwd=str(ROOT))


if __name__ == "__main__":
    run("prepare_ocr_images.py")
    run("run_query.py")
    run("run_evaluation.py")
    print("\nDone. Valid results are in rag-multilingual-ocr/results/", flush=True)
