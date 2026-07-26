from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    cfg_path = Path(path) if path else ROOT / "configs" / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(cfg: dict[str, Any]) -> None:
    for key in ("models_dir", "metrics_dir"):
        Path(ROOT / cfg["artifacts"][key]).mkdir(parents=True, exist_ok=True)
    for key in ("raw_dir", "processed_dir"):
        Path(ROOT / cfg["data"][key]).mkdir(parents=True, exist_ok=True)
