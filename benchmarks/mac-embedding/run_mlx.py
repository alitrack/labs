#!/usr/bin/env python3
"""Benchmark: MLX bge-m3 via mlx-embedding-models.

Requires:
  - Python 3.9+
  - uv installed: curl -LsSf https://astral.sh/uv/install.sh | sh
  - Or pip: pip install mlx mlx-embedding-models sentence-transformers

Usage:
  uv run --with mlx --with mlx-embedding-models --with sentence-transformers python3 run_mlx.py
  # or
  python3 run_mlx.py  (if deps installed)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
from common import benchmark_encode, print_results
from test_texts import TEXTS


def mlx_encode(texts: list[str], batch_size: int = 120) -> list[list[float]]:
    """Encode texts via MLX on GPU."""
    import mlx.core as mx
    mx.set_default_device(mx.gpu)
    from mlx_embedding_models import EmbeddingModel

    model = EmbeddingModel.from_registry("bge-m3")
    return model.encode(texts[:batch_size])


if __name__ == "__main__":
    print(f"MLX bge-m3 Benchmark")
    print(f"Texts: {len(TEXTS)} | First download caches model")

    # First call downloads the model, so time it
    t0 = time.perf_counter()
    dummy = mlx_encode(["初始化加载"], batch_size=1)
    load_time = time.perf_counter() - t0
    dim = len(dummy[0])
    print(f"Model loaded in {load_time:.1f}s | Embedding dim: {dim}")

    results = benchmark_encode(
        mlx_encode,
        TEXTS,
        batch_size=len(TEXTS),
        warmup_runs=3,
        measure_runs=10,
        label="MLX bge-m3",
    )
    print_results(results, "MLX bge-m3")
