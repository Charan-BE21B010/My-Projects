# Transaction Risk Rules & Alert Monitoring - Results

## Resume point 1
SQL-first suite scanned **2,204,320** payment logs (multi-million=True) for velocity, device, and merchant anomalies, then wrote actionable rules and an automated alert queue (**11646** alerts).

## Resume point 2
Threshold detection in Python + SQL reduced false-positive noise by **80.90%** (baseline FPR 0.9840 -> optimized FPR 0.1879), preserved legitimate flow (pass proxy 0.999633), and strengthened triage (high-severity share 1.0000 -> 0.9443).

## Resume point 3
Validated rule changes end-to-end (baseline vs optimized), documented investigation playbooks in `docs/investigation_playbook.md`, and shipped durable controls (`R_VEL_01`, `R_DEV_01`, `R_MER_01`).

## All resume points met
True