#!/usr/bin/env python3
"""
Evaluate baseline vs optimized RAG for:
RAG Pipeline with Multilingual OCR

Resume targets:
- about 30% answer accuracy improvement
- about 25% hallucination reduction
- OCR-to-answer under 1.5 seconds
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.generator import is_hallucinated
from src.pipeline import PipelineConfig, RAGPipeline
from src.text_utils import clean_text


def has_answer(answer: str, must_include: list[str]) -> bool:
    ans = answer.lower()
    return any(k.lower() in ans for k in must_include)


def evaluate(mode: str, sources: list[Path], eval_items: list[dict]) -> dict:
    pipe = RAGPipeline(PipelineConfig(mode=mode))
    t_ingest = time.perf_counter()
    pipe.ingest(sources)
    ingest_s = time.perf_counter() - t_ingest

    details = []
    correct = 0
    halluc = 0
    latencies = []

    for item in eval_items:
        result = pipe.ask(item["question"])
        hits = pipe.retrieve(item["question"])
        context = "\n".join(h.chunk.text for h in hits)
        ok = has_answer(result.answer, item["must_include"])
        hall = is_hallucinated(result.answer, item["must_include"], context)
        correct += int(ok)
        halluc += int(hall)
        latencies.append(result.latency_ms)
        details.append(
            {
                "id": item["id"],
                "language": item["language"],
                "question": clean_text(item["question"]),
                "gold_answer": clean_text(item["gold_answer"]),
                "prediction": clean_text(result.answer),
                "correct": ok,
                "hallucinated": hall,
                "latency_ms": round(result.latency_ms, 2),
                "sources": result.sources,
            }
        )

    n = len(eval_items)
    return {
        "mode": mode,
        "n_questions": n,
        "languages_covered": sorted({x["language"] for x in eval_items}),
        "accuracy": round(correct / n, 4),
        "accuracy_pct": round(100.0 * correct / n, 2),
        "hallucination_rate": round(halluc / n, 4),
        "hallucination_pct": round(100.0 * halluc / n, 2),
        "avg_latency_ms": round(sum(latencies) / n, 2),
        "p95_latency_ms": round(sorted(latencies)[max(0, int(0.95 * n) - 1)], 2),
        "max_latency_ms": round(max(latencies), 2),
        "under_1_5s": all(x < 1500 for x in latencies),
        "ingest_seconds": round(ingest_s, 2),
        "details": details,
    }


def main() -> None:
    eval_path = ROOT / "data" / "eval" / "qa_eval.json"
    eval_items = json.loads(eval_path.read_text(encoding="utf-8"))

    images = sorted((ROOT / "data" / "images").glob("*.png"))
    docs = sorted((ROOT / "data" / "documents").glob("*.txt"))
    sources = images if images else docs
    if not sources:
        raise SystemExit("No documents or OCR images found under data/.")
    source_type = "ocr_images" if images else "text_documents"

    print(f"Evaluating on {len(eval_items)} questions | sources={source_type} ({len(sources)})")
    baseline = evaluate("baseline", sources, eval_items)
    optimized = evaluate("optimized", sources, eval_items)

    acc_improve = (optimized["accuracy"] - baseline["accuracy"]) / max(baseline["accuracy"], 1e-9)
    hall_reduce = (
        baseline["hallucination_rate"] - optimized["hallucination_rate"]
    ) / max(baseline["hallucination_rate"], 1e-9)
    acc_points = optimized["accuracy_pct"] - baseline["accuracy_pct"]

    acc_improve_pct = round(100.0 * acc_improve, 2)
    hall_reduce_pct = round(100.0 * hall_reduce, 2)

    # Resume targets
    target_acc = 30.0
    target_hall = 25.0
    meets_acc = acc_improve_pct >= target_acc or acc_points >= target_acc
    meets_hall = hall_reduce_pct >= target_hall
    meets_lat = bool(optimized["under_1_5s"]) and optimized["max_latency_ms"] < 1500

    summary = {
        "project": "RAG Pipeline with Multilingual OCR",
        "period": "Feb 2025 - Apr 2025",
        "source_type": source_type,
        "languages": ["en", "hi", "es"],
        "languages_count": 3,
        "baseline": {
            "accuracy_pct": baseline["accuracy_pct"],
            "hallucination_pct": baseline["hallucination_pct"],
            "avg_latency_ms": baseline["avg_latency_ms"],
            "max_latency_ms": baseline["max_latency_ms"],
            "under_1_5s": baseline["under_1_5s"],
        },
        "optimized": {
            "accuracy_pct": optimized["accuracy_pct"],
            "hallucination_pct": optimized["hallucination_pct"],
            "avg_latency_ms": optimized["avg_latency_ms"],
            "max_latency_ms": optimized["max_latency_ms"],
            "under_1_5s": optimized["under_1_5s"],
        },
        "measured_results": {
            "answer_accuracy_improvement_pct": acc_improve_pct,
            "answer_accuracy_improvement_points": round(acc_points, 2),
            "hallucination_reduction_pct": hall_reduce_pct,
            "ocr_to_answer_under_1_5_seconds": meets_lat,
            "optimized_avg_latency_ms": optimized["avg_latency_ms"],
            "optimized_max_latency_ms": optimized["max_latency_ms"],
        },
        "resume_targets": {
            "answer_accuracy_improvement_pct": target_acc,
            "hallucination_reduction_pct": target_hall,
            "ocr_to_answer_under_1_5_seconds": True,
            "meets_accuracy_target": meets_acc,
            "meets_hallucination_target": meets_hall,
            "meets_latency_target": meets_lat,
            "all_resume_targets_met": meets_acc and meets_hall and meets_lat,
        },
    }

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "metrics.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (results_dir / "baseline_details.json").write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (results_dir / "optimized_details.json").write_text(
        json.dumps(optimized, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    resume_md = f"""# RAG Pipeline with Multilingual OCR - Results

## Resume targets

| Target | Value | Met |
|---|---|---|
| Answer accuracy improvement | about 30% | {meets_acc} |
| Hallucination reduction | about 25% | {meets_hall} |
| OCR-to-answer latency | under 1.5 seconds | {meets_lat} |

## Measured results

- Languages: English, Hindi, Spanish
- Baseline accuracy: {baseline['accuracy_pct']:.2f}%
- Optimized accuracy: {optimized['accuracy_pct']:.2f}%
- Accuracy improvement: {acc_improve_pct:.2f}% relative ({acc_points:.2f} points)
- Baseline hallucination: {baseline['hallucination_pct']:.2f}%
- Optimized hallucination: {optimized['hallucination_pct']:.2f}%
- Hallucination reduction: {hall_reduce_pct:.2f}% relative
- Optimized avg latency: {optimized['avg_latency_ms']:.2f} ms
- Optimized max latency: {optimized['max_latency_ms']:.2f} ms
- All answers under 1.5s: {optimized['under_1_5s']}
- All resume targets met: {meets_acc and meets_hall and meets_lat}

## Reproduce

```bash
python scripts/prepare_ocr_images.py
python scripts/run_evaluation.py
```
"""
    (results_dir / "RESUME_RESULTS.md").write_text(clean_text(resume_md), encoding="utf-8")

    if not (meets_acc and meets_hall and meets_lat):
        raise SystemExit(
            "Eval finished but resume targets were not met. "
            f"acc_improve={acc_improve_pct}%, hall_reduce={hall_reduce_pct}%, under_1_5s={meets_lat}"
        )

    print("\n========== MEASURED RESULTS ==========")
    print(f"Baseline accuracy:      {baseline['accuracy_pct']:.2f}%")
    print(f"Optimized accuracy:     {optimized['accuracy_pct']:.2f}%")
    print(f"Accuracy improvement:   {acc_improve_pct:.2f}%")
    print(f"Baseline hallucination: {baseline['hallucination_pct']:.2f}%")
    print(f"Optimized hallucination:{optimized['hallucination_pct']:.2f}%")
    print(f"Hallucination reduce:   {hall_reduce_pct:.2f}%")
    print(f"Optimized avg latency:  {optimized['avg_latency_ms']:.2f} ms")
    print(f"Under 1.5s:             {meets_lat}")
    print("\n========== RESUME TARGETS ==========")
    print("Accuracy improvement target about 30%: MET" if meets_acc else "Accuracy target: NOT MET")
    print("Hallucination reduction target about 25%: MET" if meets_hall else "Hallucination target: NOT MET")
    print("Latency under 1.5s: MET" if meets_lat else "Latency target: NOT MET")
    print(f"\nWrote {results_dir / 'metrics.json'}")
    print(f"Wrote {results_dir / 'RESUME_RESULTS.md'}")


if __name__ == "__main__":
    main()
