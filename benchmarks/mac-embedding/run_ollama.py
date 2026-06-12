#!/usr/bin/env python3
"""Benchmark: Ollama bge-m3 via HTTP API.

Requires:
  - Ollama installed (brew install ollama or https://ollama.com)
  - bge-m3 model pulled: ollama pull bge-m3:latest
  - Ollama server running: ollama serve

Usage:
  python3 run_ollama.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
from common import benchmark_encode, print_results
from test_texts import TEXTS


def ollama_encode(texts: list[str], batch_size: int = 120) -> list[list[float]]:
    """Encode texts via Ollama /api/embed endpoint."""
    resp = requests.post(
        "http://localhost:11434/api/embed",
        json={"model": "bge-m3", "input": texts[:batch_size]},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["embeddings"]


if __name__ == "__main__":
    print(f"Ollama bge-m3 Benchmark")
    print(f"Texts: {len(TEXTS)} | Batch size: {len(TEXTS)}")
    print(f"Ensure: ollama pull bge-m3:latest && ollama serve")

    # Verify connectivity
    try:
        requests.get("http://localhost:11434/api/tags", timeout=5)
    except requests.ConnectionError:
        print("ERROR: Cannot reach Ollama at localhost:11434. Is ollama serve running?")
        sys.exit(1)

    results = benchmark_encode(
        ollama_encode,
        TEXTS,
        batch_size=len(TEXTS),
        warmup_runs=2,
        measure_runs=5,
        label="Ollama bge-m3",
    )
    print_results(results, "Ollama bge-m3")
