from __future__ import annotations

import argparse
import statistics
import time

import httpx


def run_benchmark(url: str, n: int = 500, warmup: int = 20) -> None:
    payload = {
        "amount": 9800.0,
        "txn_count_24h": 11,
        "avg_amount_7d": 220.0,
        "failed_logins": 5,
        "device_change_count": 3,
        "is_rooted": 1,
        "distance_from_last_txn": 420.0,
        "country_risk_score": 0.82,
        "session_time": 40,
        "typing_speed": 7.1,
        "merchant_text": "urgent wire transfer request asap",
    }

    latencies = []
    with httpx.Client(timeout=30.0) as client:
        for i in range(warmup + n):
            t0 = time.perf_counter()
            r = client.post(f"{url}/predict", json=payload)
            dt = (time.perf_counter() - t0) * 1000
            r.raise_for_status()
            if i >= warmup:
                latencies.append(dt)

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    mean = statistics.mean(latencies)
    tps = 1000.0 / mean if mean > 0 else 0.0

    print(f"Requests: {n}")
    print(f"Mean latency: {mean:.2f} ms")
    print(f"p50: {p50:.2f} ms | p95: {p95:.2f} ms | p99: {p99:.2f} ms")
    print(f"Approx single-client TPS: {tps:.1f}")
    print("Note: 50k TPS is an architecture/target figure under multi-worker + Redis cache load testing.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--n", type=int, default=200)
    args = parser.parse_args()
    run_benchmark(args.url, n=args.n)


if __name__ == "__main__":
    main()
