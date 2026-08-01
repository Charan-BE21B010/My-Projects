-- Merchant anomaly: sudden spike vs merchant baseline volume/amount

SELECT
    p.txn_id,
    p.merchant_id,
    p.ts,
    p.amount,
    p.is_fraud,
    (
        SELECT COUNT(*)
        FROM payments p2
        WHERE p2.merchant_id = p.merchant_id
          AND p2.ts <= p.ts
          AND p2.ts >= datetime(p.ts, ?)
    ) AS merchant_txn_count_window,
    (
        SELECT COALESCE(AVG(p3.amount), 0)
        FROM payments p3
        WHERE p3.merchant_id = p.merchant_id
          AND p3.ts < p.ts
          AND p3.ts >= datetime(p.ts, ?)
    ) AS merchant_avg_amount_baseline
FROM payments p;
