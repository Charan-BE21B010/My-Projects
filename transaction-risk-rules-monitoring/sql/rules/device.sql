-- Device anomaly: device shared across many users / high-risk burst activity

SELECT
    p.txn_id,
    p.device_id,
    p.user_id,
    p.ts,
    p.is_fraud,
    (
        SELECT COUNT(DISTINCT p2.user_id)
        FROM payments p2
        WHERE p2.device_id = p.device_id
          AND p2.ts <= p.ts
          AND p2.ts >= datetime(p.ts, ?)
    ) AS distinct_users_on_device,
    (
        SELECT COUNT(*)
        FROM payments p3
        WHERE p3.device_id = p.device_id
          AND p3.ts <= p.ts
          AND p3.ts >= datetime(p.ts, ?)
    ) AS device_txn_count_window
FROM payments p;
