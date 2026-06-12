"""Shared utilities for mac-embedding benchmarks."""

import time
import statistics
from typing import Callable


def benchmark_encode(
    encode_fn: Callable,
    texts: list[str],
    batch_size: int = 120,
    warmup_runs: int = 2,
    measure_runs: int = 5,
    label: str = "encode",
) -> dict:
    """Benchmark an embedding encode function.

    Args:
        encode_fn: Function that takes (texts, batch_size?) and returns embeddings.
        texts: Full test corpus.
        batch_size: How many texts to encode per call.
        warmup_runs: How many warmup iterations (not measured).
        measure_runs: How many measured iterations.
        label: Name for display.

    Returns:
        dict with keys: texts_per_sec, latency_avg, latency_p50, latency_p95, latency_p99
    """
    # Warmup
    for _ in range(warmup_runs):
        encode_fn(texts, batch_size)

    # Measure
    latencies = []
    for _ in range(measure_runs):
        t0 = time.perf_counter()
        encode_fn(texts, batch_size)
        t1 = time.perf_counter()
        latencies.append(t1 - t0)

    total_texts = len(texts) * measure_runs
    total_time = sum(latencies)
    texts_per_sec = total_texts / total_time
    sorted_lat = sorted(latencies)

    return {
        "texts_per_sec": round(texts_per_sec, 1),
        "latency_avg_ms": round(statistics.mean(latencies) * 1000, 1),
        "latency_p50_ms": round(sorted_lat[len(sorted_lat) // 2] * 1000, 1),
        "latency_p95_ms": round(sorted_lat[int(len(sorted_lat) * 0.95)] * 1000, 1),
        "latency_p99_ms": round(sorted_lat[int(len(sorted_lat) * 0.99)] * 1000, 1),
        "texts_per_batch": total_texts // measure_runs,
        "num_runs": measure_runs,
        "total_texts": total_texts,
        "total_time_s": round(total_time, 2),
    }


def print_results(results: dict, title: str):
    """Pretty-print benchmark results."""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
    print(f"  Throughput:     {results['texts_per_sec']:>8} texts/s")
    print(f"  Latency avg:    {results['latency_avg_ms']:>8} ms")
    print(f"  Latency p50:    {results['latency_p50_ms']:>8} ms")
    print(f"  Latency p95:    {results['latency_p95_ms']:>8} ms")
    print(f"  Latency p99:    {results['latency_p99_ms']:>8} ms")
    print(f"  Total texts:    {results['total_texts']:>8}")
    print(f"  Total time:     {results['total_time_s']:>8} s")
    print(f"{'='*50}\n")
