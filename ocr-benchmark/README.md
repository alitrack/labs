# OCR Benchmark: Gemma 4 12B vs Qwen3.6 27B

macOS M3 Ultra 256GB | mlx-vlm 0.6.3 | 4-bit quantization

本地中文 OCR 横向评测，5 类文档 × 字符级 CER × RAG 增强。

## Quick Start

```bash
# Prerequisites: macOS with mlx-vlm, Ollama (bge-m3 installed)
uv pip install mlx-vlm turbovec python-Levenshtein

# 1. Generate test images
python3 generate_images.py

# 2. Build RAG index
python3 build_index.py

# 3. Run OCR benchmark (Gemma vs Qwen)
python3 benchmark.py

# 4. Test RAG correction on truncated OCR
python3 qwen_rag_correct.py
```

## Models

| Model | Size | Engine |
|-------|:----:|--------|
| `mlx-community/gemma-4-12B-it-4bit` | ~7.5 GB | mlx-vlm |
| `mlx-community/Qwen3.6-27B-4bit` | ~17 GB | mlx-vlm |
| `bge-m3:latest` (Ollama) | 1.2 GB | Embedding |

## Pipeline

```
文档图片 → OCR (Qwen3.6) → TurboQuant RAG检索 → Qwen3.6修正 → 完整输出
                ↓ 仅裸OCR                               ↓ +RAG
          截断/格式问题                           补全+格式化
```

## Test Set

5 Chinese document types: financial report, VAT invoice, bilingual tech doc, table, contract.

## Results

### Raw OCR

| Document | Qwen3.6 27B CER | Gemma 4 12B CER |
|----------|:--:|:--:|
| 经营报告 | 6.9% | 38.9% |
| 增值税发票 | 0.0% | crash |
| 技术文档 | truncated | 70.4% |
| 性能对比表 | correct (format diff) | hallucinated |
| 合同 | correct (format diff) | crash |

### RAG Correction (Qwen3.6)

| Metric | Raw OCR (512 tok) | RAG Corrected |
|--------|:--:|:--:|
| Time | 14.9s | **10.9s** |
| Truncated content | "1.3" | "1.3-1.8×" ✅ |
| Missing Section 3 | ❌ | ✅ Performance Metrics |
| Missing Section 4 | ❌ | ✅ API Endpoint |

- RAG 将截断输出补全，且速度更快（上下文减少重复 OCR）
- 即使 OCR 已有 93%+ 准确率，RAG 仍能消除最后的截断和格式问题

## Key Findings

1. **Qwen3.6 >> Gemma 4** for Chinese OCR — 0-7% vs 38-70% CER
2. Gemma 4 12B 4-bit 在发票和合同上直接崩溃
3. **Prompt matters**: 必须用 raw prompt，chat template 让模型进入分析模式
4. Qwen3.6: `<|vision_start|><|image_pad|><|vision_end|>OCR:\n`
5. Gemma 4: `<bos><|image|>OCR:\n`
6. DFlash 在 OCR 短文本场景无效（瓶颈在 vision encoding）
7. **RAG 可进一步消除截断和格式问题**，即使基础 OCR 已高精度

## Prompts

```python
# ✅ Qwen3.6 — raw vision prompt
prompt = "<|vision_start|><|image_pad|><|vision_end|>OCR:\n"

# ✅ Gemma 4 — raw prompt with image token
prompt = "<bos><|image|>OCR:\n"

# ❌ Chat template — model analyzes instead of OCRs
messages = [{"role": "user", "content": "识别文字..."}]
```

## Related

- Wiki: [[local-llm-chinese-ocr-benchmark-2026]]
- 公众号: 本地中文OCR实测：Gemma 4 12B vs Qwen3.6 27B
