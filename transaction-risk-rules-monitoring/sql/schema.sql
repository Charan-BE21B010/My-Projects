-- Payment risk schema (PostgreSQL-compatible; runs on SQLite too)

CREATE TABLE IF NOT EXISTS payments (
    txn_id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    user_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    amount REAL NOT NULL,
    country TEXT NOT NULL,
    channel TEXT NOT NULL,
    is_fraud INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_payments_user_ts ON payments(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_payments_device_ts ON payments(device_id, ts);
CREATE INDEX IF NOT EXISTS idx_payments_merchant_ts ON payments(merchant_id, ts);
CREATE INDEX IF NOT EXISTS idx_payments_fraud ON payments(is_fraud);

CREATE TABLE IF NOT EXISTS risk_rules (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    anomaly_type TEXT NOT NULL,
    threshold_value REAL NOT NULL,
    severity TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS alert_queue (
    alert_id TEXT PRIMARY KEY,
    txn_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    anomaly_type TEXT NOT NULL,
    risk_score REAL NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    triage_bucket TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rule_validation_log (
    run_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    precision REAL,
    recall REAL,
    false_positive_rate REAL,
    legitimate_pass_rate REAL,
    alerts_raised INTEGER,
    notes TEXT
);
