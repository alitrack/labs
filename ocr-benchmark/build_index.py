#!/usr/bin/env python3
"""Build TurboQuantIndex from documents using Ollama BGE-M3 embeddings."""
import os, time, json, re
import requests
import numpy as np
from turbovec import TurboQuantIndex

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
OLLAMA = "http://localhost:11434"

def embed(texts: list[str]) -> list[list[float]]:
    resp = requests.post(f"{OLLAMA}/api/embed", 
                        json={"model": "bge-m3:latest", "input": texts}, timeout=30)
    resp.raise_for_status()
    return resp.json()["embeddings"]

with open("data/docs.txt") as f:
    texts = [line.strip() for line in f.readlines() if line.strip()]
print(f"Loaded {len(texts)} text chunks")

# Get dim
sample = embed([texts[0]])
dim = len(sample[0])
print(f"Embedding dimension: {dim}")

print(f"Embedding {len(texts)} chunks...")
start = time.time()
vectors = embed(texts)
print(f"Done in {time.time()-start:.1f}s")

vectors_np = np.array(vectors, dtype=np.float32)
print("Building TurboQuantIndex (4-bit)...")
index = TurboQuantIndex(dim=dim, bit_width=4)
index.add(vectors_np)
print(f"Index size: {len(index)} vectors")

index.write("index/index.tq")
print("✅ Index saved to index/index.tq")
