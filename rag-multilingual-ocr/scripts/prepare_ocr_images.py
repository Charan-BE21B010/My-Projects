#!/usr/bin/env python3
"""Generate scanned-style images + sidecar text for OCR demos."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ocr import render_text_image
from src.text_utils import clean_text


def main() -> None:
    docs = ROOT / "data" / "documents"
    images = ROOT / "data" / "images"
    images.mkdir(parents=True, exist_ok=True)

    files = sorted(docs.glob("*.txt"))
    if not files:
        raise SystemExit(f"No documents found in {docs}")

    for path in files:
        text = clean_text(path.read_text(encoding="utf-8"))
        img_path = images / f"{path.stem}.png"
        side = images / f"{path.stem}.txt"
        render_text_image(text, img_path)
        side.write_text(text, encoding="utf-8")
        print(f"Wrote {img_path.name} + sidecar OCR text")


if __name__ == "__main__":
    main()
