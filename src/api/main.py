from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.loader import ModelNotReadyError, load_orchestrator, predict_transaction
from src.api.schemas import PredictionResponse, TransactionRequest
from src.services.redis_cache import RedisCache
from src.utils.config import load_config

cfg = load_config()
cache = RedisCache(
    redis_url=cfg["serving"]["redis_url"],
    ttl_seconds=cfg["serving"]["redis_ttl_seconds"],
    enabled=cfg["serving"]["cache_enabled"],
)

app = FastAPI(
    title="Multi-Agent Online Fraud Detection System",
    description="4-agent orchestration: XGBoost + Autoencoder + LSTM + DistilBERT-style NLP",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    try:
        load_orchestrator()
    except ModelNotReadyError:
        # API can still boot; /predict will explain how to train
        pass


@app.get("/health")
def health() -> dict:
    ready = True
    detail = "ok"
    try:
        load_orchestrator()
    except ModelNotReadyError as exc:
        ready = False
        detail = str(exc)
    return {
        "status": "ok" if ready else "models_missing",
        "models_ready": ready,
        "detail": detail,
        "redis": "connected" if cache.client is not None else "memory_fallback",
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(req: TransactionRequest) -> PredictionResponse:
    features = req.to_feature_dict()
    key = cache.make_key(features)
    cached = cache.get(key)
    if cached:
        return PredictionResponse(**cached, cached=True)

    try:
        result = predict_transaction(features)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    payload = {
        "agent_scores": result["agent_scores"],
        "final_score": result["final_score"],
        "decision": result["decision"],
        "explanation": result.get("explanation"),
    }
    cache.set(key, payload)
    return PredictionResponse(**payload, cached=False)


@app.get("/")
def root() -> dict:
    return {
        "project": "Multi-Agent Online Fraud Detection System",
        "endpoints": ["/health", "/predict", "/docs"],
    }
