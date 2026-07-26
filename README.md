# Multi-Agent Online Fraud Detection System

Real-time fraud detection with a 4-agent orchestration stack:

1. **XGBoost** tabular / statistical agent  
2. **Autoencoder** anomaly agent  
3. **LSTM** sequential behavior agent  
4. **DistilBERT-style** NLP agent (transformer encoder)

A **Fusion Agent** combines scores into one risk probability. A **Decision Engine** maps the score to `ALLOW` / `REVIEW` / `BLOCK`. Inference is served with **FastAPI** and optional **Redis** caching.

Built to match a production-style portfolio project: 1.2M+ transactions, 120+ features, ensemble AUC target **> 0.96**, low-latency API path.

---

## Architecture

```
Transaction request
        |
        v
 +------+------+------+------+
 | XGB  |  AE  | LSTM | NLP  |
 +------+------+------+------+
        \   |    |   /
         \  |    |  /
          v v    v v
         Fusion Agent
              |
              v
        Decision Engine
        ALLOW / REVIEW / BLOCK
              |
              v
     FastAPI (+ Redis cache)
```

---

## Quick start

```bash
# 1) Create venv
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

# 2) Install
pip install -r requirements.txt

# 3) Train (demo / interview-ready run)
python -m src.training.train --n 250000

# Faster local smoke train
python -m src.training.train --quick

# Full 1.2M scale (longer)
python -m src.training.train --full

# 4) Run API
python scripts/run_api.py
# Docs: http://127.0.0.1:8000/docs

# 5) Latency check
python scripts/benchmark_latency.py --n 200
```

---

## Example request

```bash
curl -X POST http://127.0.0.1:8000/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"amount\":9800,\"txn_count_24h\":11,\"avg_amount_7d\":220,\"failed_logins\":5,\"device_change_count\":3,\"is_rooted\":1,\"distance_from_last_txn\":420,\"country_risk_score\":0.82,\"session_time\":40,\"typing_speed\":7.1,\"merchant_text\":\"urgent wire transfer request asap\"}"
```

Example response shape:

```json
{
  "agent_scores": {
    "xgboost": 0.93,
    "autoencoder": 0.81,
    "lstm": 0.88,
    "nlp": 0.91
  },
  "final_score": 0.89,
  "decision": "BLOCK",
  "cached": false
}
```

---

## Project layout

```
Multi-Agent-Fraud-Detection/
  configs/config.yaml
  src/
    agents/          # specialist + fusion + orchestrator
    models/          # XGBoost, Autoencoder, LSTM, DistilBERT-style
    data/            # PaySim / IEEE-CIS style generator
    api/             # FastAPI app
    services/        # decision engine + Redis cache
    training/        # train + evaluate
  scripts/           # API launcher + latency benchmark
  artifacts/         # saved models + metrics (generated)
  tests/
  INTERVIEW_ANSWERS.md
```

---

## Datasets

The generator creates **PaySim / IEEE-CIS style** synthetic transactions:

- 1.2M+ rows (configurable)
- 120+ tabular features (`amount`, behavior, device, geo, plus `V1..Vn`)
- amount trajectories for LSTM
- merchant text for NLP
- correlated fraud signals so the ensemble is meaningful

You can also plug real PaySim / IEEE-CIS CSVs into `data/raw/` and adapt the loader.

---

## Metrics (from last training run)

Source: `artifacts/metrics/results.json`

| Model | Test AUC | Test PR-AUC |
|-------|----------|-------------|
| XGBoost | 0.9682 | 0.9408 |
| Autoencoder | 0.9693 | 0.9424 |
| LSTM | 0.9104 | 0.7390 |
| DistilBERT-style NLP | 0.8755 | 0.2192 |
| **Fusion (stacked)** | **0.9667** | **0.9412** |

Fusion @ threshold 0.5: precision 0.9953, recall 0.9387, F1 0.9661  
Dataset: 200,000 transactions, 120 tabular features, fraud rate 3.685%

Reproduce:

```bash
python -m src.training.train --n 200000
```

For full 1.2M scale:

```bash
python -m src.training.train --full
```

---

## Design choices (interview ready)

- **Why multi-agent?** Fraud is multi-modal. Tabular spikes, sequence bursts, anomaly drift, and text cues fail in different ways. Specialists reduce blind spots.
- **Why stacked fusion?** Fixed weights are a baseline. A logistic stacker learned on validation agent scores improves calibrated combination (reported fusion AUC 0.9667).
- **Why ALLOW / REVIEW / BLOCK?** Pure binary cutoffs create either missed fraud or angry customers. Mid scores go to review.
- **Why Redis?** Cache repeated feature payloads and keep the online path fast under load.
- **Latency note:** Sub-50ms is the online inference design target for a warmed model path. 50k TPS is an architecture/capacity target with multi-worker serving and caching, not a single-process laptop claim.
- **NLP note:** The NLP agent is a DistilBERT-style transformer encoder (token + positional embeddings + TransformerEncoder). It is offline-friendly and does not require downloading Hugging Face weights.

---

## Tests

```bash
pytest -q
```

---

## License

MIT
