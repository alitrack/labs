#!/usr/bin/env python3
"""Qwen3.6 + RAG: OCR truncation fix via TurboQuant retrieval."""
import os, time, re, json, sys
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

import requests
import numpy as np
from turbovec import TurboQuantIndex
from mlx_vlm import load, generate
from mlx_vlm.utils import load_image

OLLAMA = "http://localhost:11434"

# ── Embedding ──
def embed(text: str) -> np.ndarray:
    resp = requests.post(f"{OLLAMA}/api/embed",
                        json={"model": "bge-m3:latest", "input": [text]}, timeout=30)
    return np.array([resp.json()["embeddings"][0]], dtype=np.float32)

# ── Load models once ──
print("Loading Qwen3.6...", file=sys.stderr, flush=True)
model, processor = load("mlx-community/Qwen3.6-27B-4bit")

# ── Step 1: Raw OCR (will be truncated) ──
image = load_image("/tmp/ocr_benchmark/03_tech_doc.png")
prompt = "<|vision_start|><|image_pad|><|vision_end|>OCR:\n"

print("Step 1: Raw OCR...", file=sys.stderr, flush=True)
t0 = time.time()
result = generate(model, processor, prompt=prompt, image=image,
                 max_tokens=512, temperature=0.0, verbose=False)
raw_ocr = result.text if hasattr(result, "text") else str(result)
raw_ocr = re.sub(r'<\|channel\|>thought.*?<channel\|>', '', raw_ocr, flags=re.DOTALL)
raw_ocr = re.sub(r'<\|[^>]+\|?>', '', raw_ocr).strip()
ocr_time = time.time() - t0

print(f"  ⏱ {ocr_time:.1f}s | {len(raw_ocr)} chars")
print(f"  → {raw_ocr[:200]}...")

# ── Step 2: RAG retrieval from existing index ──
index = TurboQuantIndex.load("index/index.tq")
with open("data/docs.txt") as f:
    texts = [line.strip() for line in f.readlines() if line.strip()]

q_vec = embed("TurboQuant RAG Pipeline MTP speculative decoding Gemma 4")
_, indices = index.search(q_vec, k=5)
retrieved = [texts[i] for i in indices[0]]
retrieved = list(dict.fromkeys(retrieved))
context = "\n".join(r for r in retrieved if r)

print(f"\nStep 2: RAG retrieved {len(retrieved)} chunks", file=sys.stderr, flush=True)
for i, r in enumerate(retrieved, 1):
    print(f"  [{i}] {r[:100]}", file=sys.stderr)

# ── Step 3: RAG-corrected generation ──
rag_prompt = f"""<|vision_start|><|image_pad|><|vision_end|>OCR the text in this image. Then correct any truncated or missing parts using this context:

{context}

Output the COMPLETE corrected text, filling in anything truncated."""

print(f"\nStep 3: RAG-corrected OCR...", file=sys.stderr, flush=True)
t0 = time.time()
result2 = generate(model, processor, prompt=rag_prompt, image=image,
                  max_tokens=1024, temperature=0.0, verbose=False)
rag_output = result2.text if hasattr(result2, "text") else str(result2)
rag_output = re.sub(r'<\|channel\|>thought.*?<channel\|>', '', rag_output, flags=re.DOTALL)
rag_output = re.sub(r'<\|[^>]+\|?>', '', rag_output).strip()
rag_time = time.time() - t0

print(f"  ⏱ {rag_time:.1f}s | {len(rag_output)} chars")
print(f"\n{'='*60}")
print("  RAW OCR (truncated):")
print(f"  {raw_ocr[:300]}")
print(f"\n  RAG CORRECTED:")
print(f"  {rag_output[:500]}")
print(f"{'='*60}")
print(f"\n  ✅ Raw: {len(raw_ocr)} chars in {ocr_time:.1f}s")
print(f"  🔧 RAG:  {len(rag_output)} chars in {rag_time:.1f}s")
