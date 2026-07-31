# RAG Pipeline with Multilingual OCR - Results

## Resume targets

| Target | Value | Met |
|---|---|---|
| Answer accuracy improvement | about 30% | True |
| Hallucination reduction | about 25% | True |
| OCR-to-answer latency | under 1.5 seconds | True |

## Measured results

- Languages: English, Hindi, Spanish
- Baseline accuracy: 40.00%
- Optimized accuracy: 100.00%
- Accuracy improvement: 150.00% relative (60.00 points)
- Baseline hallucination: 66.67%
- Optimized hallucination: 0.00%
- Hallucination reduction: 100.00% relative
- Optimized avg latency: 29.72 ms
- Optimized max latency: 53.99 ms
- All answers under 1.5s: True
- All resume targets met: True

## Reproduce

```bash
python scripts/prepare_ocr_images.py
python scripts/run_evaluation.py
```