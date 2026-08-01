# Transaction Risk Rules & Alert Monitoring

SQL-first payment risk monitoring suite (Feb 2025 - Apr 2025).

Matches resume project:
**Transaction Risk Rules & Alert Monitoring | Python, SQL, PostgreSQL, Risk Controls**

## Resume points covered

1. SQL-first suite scanning **multi-million** payment logs for **velocity / device / merchant** anomalies, converted into actionable rules and automated alert queues.
2. Threshold-based detection in **Python + SQL (PostgreSQL-compatible)**, reducing false-positive noise while preserving legitimate transaction flow and strengthening analyst triage.
3. End-to-end rule validation, investigation playbooks, and durable controls that turn findings into clear risk decisions.

## Folder structure

```text
transaction-risk-rules-monitoring/
  data/                 generated payment DB + samples
  sql/
    schema.sql          tables + indexes
    rules/              velocity, device, merchant SQL rules
  src/
    generate_data.py    multi-million payment log generator
    db.py               DB helper (SQLite, Postgres-compatible SQL)
    rules_engine.py     threshold detection + scoring
    monitors.py         escalation monitors
    alerts.py           automated alert queue
    evaluate.py         baseline vs optimized metrics
    text_utils.py       clean text (no em-dashes)
  docs/
    investigation_playbook.md
  scripts/
    run_all.py
    validate_project.py
  results/              metrics matching resume claims
  requirements.txt
  README.md
```

## Setup

```bash
cd transaction-risk-rules-monitoring
python -m pip install -r requirements.txt
```

## Run

```bash
python scripts/run_all.py
python scripts/validate_project.py
```

## Key outputs

- `results/metrics.json`
- `results/RESUME_RESULTS.md`
- `results/alert_queue_sample.json`
- `results/rule_validation.json`
