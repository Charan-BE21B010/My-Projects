#!/usr/bin/env python3
"""Validate project folder against resume claims."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD = ["\u2014", "\u2013"]


def fail(msg: str) -> None:
    raise SystemExit(f"VALIDATION FAILED: {msg}")


def main() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "requirements.txt",
        ROOT / "sql" / "schema.sql",
        ROOT / "sql" / "rules" / "velocity.sql",
        ROOT / "sql" / "rules" / "device.sql",
        ROOT / "sql" / "rules" / "merchant.sql",
        ROOT / "docs" / "investigation_playbook.md",
        ROOT / "src" / "generate_data.py",
        ROOT / "src" / "monitors.py",
        ROOT / "src" / "rules_engine.py",
        ROOT / "src" / "alerts.py",
        ROOT / "src" / "evaluate.py",
        ROOT / "results" / "metrics.json",
        ROOT / "results" / "RESUME_RESULTS.md",
        ROOT / "results" / "alert_queue_sample.json",
        ROOT / "results" / "rule_validation.json",
    ]
    for p in required:
        if not p.exists():
            fail(f"missing {p}")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or path.suffix.lower() in {".db", ".png"}:
            continue
        if path.suffix.lower() not in {".md", ".txt", ".py", ".sql", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for ch in BAD:
            if ch in text:
                fail(f"em-dash/en-dash in {path}")

    metrics = json.loads((ROOT / "results" / "metrics.json").read_text(encoding="utf-8"))
    if metrics.get("project") != "Transaction Risk Rules & Alert Monitoring":
        fail("project name mismatch")
    if not metrics.get("all_resume_points_met"):
        fail("resume points not met")

    p1 = metrics["resume_points"]["point_1_sql_first_multi_million_velocity_device_merchant_alerts"]
    if not p1["multi_million"] or p1["rows_scanned"] < 1_000_000:
        fail("multi-million scan not proven")
    if set(p1["anomalies_covered"]) != {"velocity", "device", "merchant"}:
        fail("anomaly types incomplete")

    p2 = metrics["resume_points"]["point_2_threshold_detection_fp_reduction_legitimate_flow_triage"]
    if p2["false_positive_noise_reduction_pct"] < 20:
        fail("FP reduction too low vs resume claim intent")

    print("VALIDATION PASSED")
    print(f"Rows scanned: {p1['rows_scanned']:,}")
    print(f"Alert queue: {p1['automated_alert_queue_size']}")
    print(f"FP reduction: {p2['false_positive_noise_reduction_pct']}%")
    print(f"All resume points met: {metrics['all_resume_points_met']}")


if __name__ == "__main__":
    main()
