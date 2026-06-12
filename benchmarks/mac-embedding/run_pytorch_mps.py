#!/usr/bin/env python3
"""Benchmark: PyTorch MPS bge-m3 via sentence-transformers.

Requires:
  - Python 3.9+
  - Mac with Apple Silicon (M-series)
  - Dependencies: torch, sentence-transformers

Usage:
  uv run --with torch --with sentence-transformers python3 run_pytorch_mps.py
  # or
  python3 run_pytorch_mps.py  (if deps installed)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
from common import benchmark_encode, print_results
from test_texts import TEXTS


def pt_encode(texts: list[str], batch_size: int = 120) -> list[list[float]]:
    """Encode texts via PyTorch MPS + sentence-transformers."""
    import torch
    from sentence_transformers import SentenceTransformer

    # Lazy-init model singleton (cache across calls)
    if not hasattr(pt_encode, "model"):
        pt_encode.model = SentenceTransformer("BAAI/bge-m3", device="mps")
    
    model = pt_encode.model
    vecs = model.encode(
        texts[:batch_size],
        batch_size=min(batch_size, 32),
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return vecs


if __name__ == "__main__":
    print(f"PyTorch MPS bge-m3 Benchmark")
    print(f"Texts: {len(TEXTS)} | First call downloads model")

    # Warmup + model download
    t0 = time.perf_counter()
    import torch
    print(f"  PyTorch: {torch.__version__}")
    print(f"  MPS available: {torch.backends.mps.is_available()}")
    print(f"  MPS built: {torch.backends.mps.is_built()}")

    dummy = pt_encode(["初始化加载"], batch_size=1)
    load_time = time.perf_counter() - t0
    dim = len(dummy[0])
    print(f"Model loaded in {load_time:.1f}s | Embedding dim: {dim}")

    results = benchmark_encode(
        pt_encode,
        TEXTS,
        batch_size=len(TEXTS),
        warmup_runs=3,
        measure_runs=10,
        label="PyTorch MPS bge-m3",
    )
    print_results(results, "PyTorch MPS bge-m3")
