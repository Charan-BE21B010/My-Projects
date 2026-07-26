from __future__ import annotations

"""
Convenience launcher:

  python scripts/run_api.py
"""

import uvicorn

from src.utils.config import load_config


def main():
    cfg = load_config()
    uvicorn.run(
        "src.api.main:app",
        host=cfg["serving"]["host"],
        port=int(cfg["serving"]["port"]),
        reload=False,
    )


if __name__ == "__main__":
    main()
