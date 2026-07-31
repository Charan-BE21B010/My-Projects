#!/usr/bin/env python
"""Convenience entrypoint: python discover.py -p "Ceramic Tiles" -c Germany"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from importer_engine.cli import app

if __name__ == "__main__":
    app()