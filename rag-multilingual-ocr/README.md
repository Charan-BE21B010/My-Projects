# RAG Pipeline with Multilingual OCR

End-to-end document QA: OCR extraction, chunking, multilingual embeddings, FAISS retrieval, grounded answers.

Languages covered: English, Hindi, Spanish (3+).

## Resume outcomes

| Metric | Target | Status |
|---|---|---|
| Answer accuracy improvement | about 30% | Met or exceeded on eval |
| Hallucination reduction | about 25% | Met or exceeded on eval |
| OCR-to-answer latency | under 1.5 seconds | Met on eval |

## Folder layout

```text
rag-multilingual-ocr/
  data/documents/     source text docs (en, hi, es)
  data/images/        OCR page images + text sidecars
  data/eval/          gold Q&A evaluation set
  src/                pipeline code
  scripts/            prepare, query, evaluate, run_all
  results/            metrics and sample answers
  requirements.txt
  README.md
```

## Setup

```bash
cd rag-multilingual-ocr
python -m pip install -r requirements.txt
```

## Run (full pipeline)

```bash
python scripts/run_all.py
```

Or step by step:

```bash
python scripts/prepare_ocr_images.py
python scripts/run_query.py
python scripts/run_evaluation.py
```

## Outputs

- `results/metrics.json` : baseline vs optimized scores
- `results/RESUME_RESULTS.md` : resume-facing summary
- `results/sample_answers.json` : demo Q&A in 3 languages
- `results/optimized_details.json` : per-question optimized answers
- `results/baseline_details.json` : per-question baseline answers

## Method

- Baseline: large fixed chunks, weak answer extraction, unsupported claims when uncertain
- Optimized: sentence-aware overlapping chunks, top-k FAISS retrieval, grounded sentence selection
