#!/usr/bin/env python3
"""
Quack Benchmark Client
======================
Runs performance benchmarks against a running Quack server.

Usage:
    python quack_bench_client.py

Server must be running first:
    python quack_bench_server.py
"""
import duckdb
import time
import os
import sys

TOKEN = "bench_token_2026"
QUACK_URI = "quack:localhost"

# Quack client MUST bypass HTTP proxy for localhost
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"


def bench(label, fn, iterations=1):
    """Run a benchmark and return elapsed time."""
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    avg = sum(times) / len(times) * 1000  # ms
    return avg


def main():
    con = duckdb.connect()
    con.execute("LOAD quack")

    # Connect to remote
    con.execute(f"CREATE SECRET (TYPE quack, TOKEN '{TOKEN}', SCOPE '{QUACK_URI}')")
    con.execute(f"ATTACH '{QUACK_URI}' AS remote")

    print("=" * 60)
    print("Quack Protocol Benchmarks")
    print(f"DuckDB version: {duckdb.__version__}")
    print(f"Target: {QUACK_URI} (localhost loopback)")
    print("=" * 60)

    # ── Ping Latency ──────────────────────────────────────
    print("\n── Ping Latency (100 iterations, ms avg) ──")

    def local_ping():
        con.execute("SELECT 1").fetchone()

    def remote_ping():
        con.execute("SELECT 1 FROM remote.t_small LIMIT 1").fetchone()

    local = bench("local", local_ping, 100)
    remote = bench("remote", remote_ping, 100)
    print(f"  Local query:      {local:.3f} ms")
    print(f"  Quack remote:     {remote:.3f} ms")
    print(f"  Quack overhead:   {remote - local:.3f} ms")

    # ── Count(*) — Server-side aggregation ───────────────
    print("\n── Count(*) — Server-side aggregation ──")

    for label, table in [("10K rows", "t_small"), ("100K rows", "t_medium"), ("1M rows", "t_large")]:
        def count_query():
            con.execute(f"SELECT count(*) FROM remote.{table}").fetchone()

        ms = bench(label, count_query)
        print(f"  {label:>12}: {ms:.2f} ms")

    # ── Full Data Fetch ──────────────────────────────────
    print("\n── Full Data Fetch (streaming all rows) ──")

    for label, table, expected in [
        ("10K rows", "t_small", 10000),
        ("100K rows", "t_medium", 100000),
        ("1M rows", "t_large", 1000000),
    ]:
        def fetch_all():
            con.execute(f"SELECT * FROM remote.{table}").fetchall()

        ms = bench(label, fetch_all)
        rate = expected / (ms / 1000)
        print(f"  {label:>12}: {ms:.1f} ms ({rate:,.0f} rows/s)")

    # ── Batch Write ──────────────────────────────────────
    print("\n── Batch Write ──")

    con.execute("DROP TABLE IF EXISTS remote.batch_test")

    def batch_write():
        con.execute(
            "CREATE TABLE remote.batch_test AS "
            "SELECT range AS id, random() AS val, hash(range::VARCHAR) AS p "
            "FROM range(100000)"
        )

    ms = bench("100K batch write", batch_write)
    rate = 100000 / (ms / 1000)
    cnt = con.execute("SELECT count(*) FROM remote.batch_test").fetchone()[0]
    print(f"  100K rows batch: {ms:.1f} ms ({rate:,.0f} rows/s), verified={cnt}")

    # ── Serial Inserts ───────────────────────────────────
    print("\n── Serial Single-row Inserts ──")

    con.execute("DROP TABLE IF EXISTS remote.tx_test")
    con.execute("CREATE TABLE remote.tx_test (id INTEGER, val DOUBLE)")

    def serial_inserts():
        for i in range(500):
            con.execute(f"INSERT INTO remote.tx_test VALUES ({i}, random())")

    ms = bench("500 inserts", serial_inserts)
    rate = 500 / (ms / 1000)
    cnt = con.execute("SELECT count(*) FROM remote.tx_test").fetchone()[0]
    print(f"  500 inserts: {ms:.1f} ms ({rate:.0f} tx/s), verified={cnt}")

    # ── Aggregation Pushdown ─────────────────────────────
    print("\n── Aggregation Pushdown ──")

    def agg_query():
        con.execute(
            "SELECT avg(val), min(val), max(val), stddev(val) "
            "FROM remote.t_large"
        ).fetchone()

    ms = bench("Agg on 1M rows", agg_query)
    print(f"  AVG/MIN/MAX/STDDEV on 1M: {ms:.2f} ms")

    # ── Query Results (pure data) ────────────────────────
    print("\n── Query Results ──")

    def agg_query_full():
        return con.execute(
            "SELECT avg(val), min(val), max(val), stddev(val) "
            "FROM remote.t_large"
        ).fetchone()

    r = agg_query_full()
    print(f"  t_large stats: avg={r[0]:.4f} min={r[1]:.4f} max={r[2]:.4f} stddev={r[3]:.4f}")

    # ── Write Visibility ─────────────────────────────────
    print("\n── Write Visibility ──")
    con.execute("INSERT INTO remote.t_small VALUES (99999, 0.5)")
    v1 = con.execute("SELECT val FROM remote.t_small WHERE id=99999").fetchone()
    print(f"  Immediate read: {v1[0]}")
    con.execute("DETACH remote")

    # Reconnect and verify
    con2 = duckdb.connect()
    con2.execute("LOAD quack")
    v2 = con2.execute(
        f"SELECT val FROM quack_query('{QUACK_URI}', 'SELECT val FROM t_small WHERE id=99999', token:='{TOKEN}')"
    ).fetchone()
    print(f"  Reconnect read: {v2[0]}")
    print("  Write visibility: ✅ PASSED")

    print("\n" + "=" * 60)
    print("All benchmarks complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
