from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_engine.models import DiscoveryRequest, DiscoveryResult
from importer_engine.pipeline import run_discovery

app = FastAPI(
    title="Importer Discovery Engine",
    description="Rank relevant foreign importers for an Indian exporter",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/discover", response_model=DiscoveryResult)
def discover(req: DiscoveryRequest) -> DiscoveryResult:
    return run_discovery(req)