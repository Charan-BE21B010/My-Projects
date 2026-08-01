-- Velocity anomaly: too many txns from same user in a short window
-- Parameterized via app thresholds; this query computes user velocity features.

SELECT
    p.txn_id,
    p.user_id,
    p.ts,
    p.amount,
    p.is_fraud,
    (
        SELECT COUNT(*)
        FROM payments p2
        WHERE p2.user_id = p.user_id
          AND p2.ts <= p.ts
          AND p2.ts >= datetime(p.ts, ?)
    ) AS txn_count_window,
    (
        SELECT COALESCE(SUM(p3.amount), 0)
        FROM payments p3
        WHERE p3.user_id = p.user_id
          AND p3.ts <= p.ts
          AND p3.ts >= datetime(p.ts, ?)
    ) AS amount_sum_window
FROM payments p;
