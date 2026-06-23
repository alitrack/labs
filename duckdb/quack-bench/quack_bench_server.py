#!/usr/bin/env python3
"""
Quack Benchmark — DuckDB Remote Protocol Performance Test
==========================================================
Compares Quack (DuckDB native remote protocol) vs local DuckDB performance.

Requirements:
    pip install duckdb>=1.5.3

Usage:
    # Terminal 1: Start Quack server
    python quack_bench_server.py

    # Terminal 2: Run benchmarks (server must be running)
    python quack_bench_client.py

Reference:
    DuckDB Quack protocol: https://duckdb.org/docs/current/quack/overview.html
    Official benchmarks: https://duckdb.org/2026/05/12/quack-remote-protocol
"""
import duckdb
import time
import os
import signal
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "quack_bench.db")
TOKEN = "bench_token_2026"

def main():
    con = duckdb.connect(DB_PATH)
    con.execute("LOAD quack")

    # Prepare test data
    print("Preparing test data...", flush=True)
    con.execute("DROP TABLE IF EXISTS t_small")
    con.execute("DROP TABLE IF EXISTS t_medium")
    con.execute("DROP TABLE IF EXISTS t_large")

    con.execute("""
        CREATE TABLE t_small AS
        SELECT range AS id, random() AS val FROM range(10000)
    """)
    con.execute("""
        CREATE TABLE t_medium AS
        SELECT range AS id, random() AS val, hash(range::VARCHAR) AS payload_hash
        FROM range(100000)
    """)
    con.execute("""
        CREATE TABLE t_large AS
        SELECT range AS id, random() AS val, hash(range::VARCHAR) AS payload_hash
        FROM range(1000000)
    """)

    sc = con.execute("SELECT count(*) FROM t_small").fetchone()[0]
    mc = con.execute("SELECT count(*) FROM t_medium").fetchone()[0]
    lc = con.execute("SELECT count(*) FROM t_large").fetchone()[0]
    print(f"Tables ready: small={sc} medium={mc} large={lc}", flush=True)

    # Start Quack server
    result = con.execute(f"CALL quack_serve('quack:localhost', token:='{TOKEN}')").fetchall()
    print(f"Server started: {result[0][1]}", flush=True)
    print(f"Token: {TOKEN}", flush=True)
    print(f"Server PID: {os.getpid()}", flush=True)
    print("\nPress Ctrl+C to stop.", flush=True)

    def shutdown(sig, frame):
        print("\nShutting down...", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped.", flush=True)

if __name__ == "__main__":
    main()
