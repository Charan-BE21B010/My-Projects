#!/usr/bin/env python3
"""Run full Transaction Risk Rules & Alert Monitoring pipeline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluate import evaluate
from src.generate_data import generate


def main() -> None:
    print("=== 1) Generate multi-million payment logs ===", flush=True)
    summary = generate()
    print(json.dumps(summary, indent=2), flush=True)

    print("\n=== 2) Run SQL monitors + rules + alerts + validation ===", flush=True)
    metrics = evaluate()

    p1 = metrics["resume_points"]["point_1_sql_first_multi_million_velocity_device_merchant_alerts"]
    p2 = metrics["resume_points"]["point_2_threshold_detection_fp_reduction_legitimate_flow_triage"]
    p3 = metrics["resume_points"]["point_3_e2e_validation_playbooks_durable_controls"]

    print("\n=== RESUME POINT CHECK ===", flush=True)
    print(f"Point1 multi-million scan + alert queue: met={p1['met']} rows={p1['rows_scanned']:,} alerts={p1['automated_alert_queue_size']}", flush=True)
    print(f"Point2 FP reduction + legitimate flow: met={p2['met']} fp_reduction={p2['false_positive_noise_reduction_pct']}%", flush=True)
    print(f"Point3 e2e validation + playbooks: met={p3['met']}", flush=True)
    print(f"ALL RESUME POINTS MET: {metrics['all_resume_points_met']}", flush=True)

    if not metrics["all_resume_points_met"]:
        raise SystemExit("Resume points not fully met. Re-tune thresholds and re-run.")


if __name__ == "__main__":
    main()
