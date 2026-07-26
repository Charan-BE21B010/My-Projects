# Interview Answers: Multi-Agent Online Fraud Detection System

Use these numbers. They come from `artifacts/metrics/results.json` after training.

## Exact results (source of truth)

| Item | Value |
|------|-------|
| Transactions trained | 200,000 (PaySim / IEEE-CIS style, 120 tabular features) |
| Fraud rate | 3.685% |
| XGBoost test AUC | 0.9682 |
| Autoencoder test AUC | 0.9693 |
| LSTM test AUC | 0.9104 |
| DistilBERT-style NLP test AUC | 0.8755 |
| **Fusion (stacked) test AUC** | **0.9667** |
| Fusion PR-AUC | 0.9412 |
| Fusion precision @0.5 | 0.9953 |
| Fusion recall @0.5 | 0.9387 |
| Fusion F1 @0.5 | 0.9661 |
| Decision thresholds | BLOCK >= 0.70, REVIEW >= 0.40, else ALLOW |
| Serving | FastAPI + Redis (memory fallback if Redis is down) |
| Scale commands | `--n 200000` (reported), `--full` for 1.2M generation/training |

Round aloud as: fusion AUC about **0.967**, PR-AUC about **0.941**, precision about **99.5%**, recall about **93.9%**.

---

## 1) Explain the project (45 seconds)

I built a multi-agent online fraud detection system because fraud rarely looks like one pattern. I used four specialist agents: XGBoost for tabular money and account features, an autoencoder for anomaly score, an LSTM for short amount trajectories, and a DistilBERT-style transformer for merchant text. A fusion layer stacks those four scores with logistic regression into one risk probability, then a decision engine maps it to ALLOW, REVIEW, or BLOCK. On a 200k PaySim/IEEE-CIS style set with 120 features, the fused model reached test AUC 0.9667 and PR-AUC 0.9412, and I served it with FastAPI plus Redis caching for low-latency inference.

---

## 2) Why multi-agent instead of one model?

One model has blind spots. A card-not-present burst may look normal in text but weird in sequence. An account takeover may look normal in amount but weird in device and login failures. Specialists make failures debuggable: I can see which agent fired. In my run, XGBoost and the autoencoder were strongest (about 0.968 to 0.969 AUC), while LSTM and NLP still added complementary signal for the stacker.

---

## 3) Walk through the pipeline

Request comes in with amount, velocity, device, geo, behavior, merchant text, and an amount sequence. Each agent returns a probability in 0 to 1. Fusion combines them (stacked logistic on validation scores). If final score is at least 0.70 we BLOCK, at least 0.40 we REVIEW, otherwise ALLOW. Redis caches repeated payloads so repeated traffic is cheap.

---

## 4) Metrics and what they mean

AUC 0.9667 means if I pick a random fraud and a random genuine payment, the system ranks the fraud higher about 96.7% of the time. PR-AUC 0.941 matters more under imbalance because fraud is only about 3.7% of rows. High precision (about 99.5% at 0.5) means blocked cases are usually real risk; recall about 93.9% means we still catch most fraud at that operating point. In production I would tune the threshold from cost of false positives vs false negatives, not from 0.5 by default.

---

## 5) Datasets

I used a PaySim / IEEE-CIS style generator: 120+ anonymous and behavioral features, text merchant descriptions, and sequences for LSTM. The repo supports `--full` for 1.2M rows. The numbers I quote in interviews are from the reproducible 200k training run checked into `artifacts/metrics/results.json`.

---

## 6) Latency and 50k TPS (say this carefully)

Sub-50ms is the online design target for a warmed inference path with compact features and caching. 50k TPS is an architecture capacity target under multi-worker FastAPI, Redis cache hits, and horizontal scale. On a laptop single process, use `scripts/benchmark_latency.py` for measured p50/p95. Do not claim 50k TPS from a single local uvicorn worker.

---

## 7) Biggest challenge

Class imbalance and conflicting agent opinions. Accuracy alone is misleading when 96% of traffic is genuine. I optimized ranking metrics (AUC / PR-AUC), used class weighting in neural losses, and kept a REVIEW band so uncertain scores do not force a hard block.

---

## 8) What would you improve next?

Online feature store, concept-drift monitors, hybrid retrieval of similar past fraud cases, calibrated probabilities, and shadow-mode A/B before full BLOCK automation. I would also swap the lightweight DistilBERT-style encoder for a production Hugging Face checkpoint if GPU serving budget allows.

---

## 9) One-paragraph resume-aligned answer

I designed a 4-agent orchestration system for real-time fraud analysis on PaySim/IEEE-CIS style data with 120+ features, combining XGBoost, autoencoder, LSTM, and DistilBERT-style NLP signals. The stacked fusion model reached test AUC 0.9667 with PR-AUC 0.9412, precision about 99.5%, and recall about 93.9% at threshold 0.5. I deployed inference with FastAPI and Redis for scalable low-latency scoring with ALLOW / REVIEW / BLOCK decisions.
