# OCR Benchmark: Gemma 4 12B vs Qwen3.6 27B

macOS M3 Ultra 256GB | mlx-vlm 0.6.3 | 4-bit quantization

## Quick Start

```bash
# On macOS with mlx-vlm installed
cd ocr-benchmark
python3 generate_images.py    # Generate test images
python3 benchmark.py          # Run benchmark
```

## Models

- `mlx-community/gemma-4-12B-it-4bit` (~7.5 GB)
- `mlx-community/Qwen3.6-27B-4bit` (~17 GB)

## Test Set

5 Chinese document types: financial report, VAT invoice, bilingual tech doc, table, contract.

## Results

| Document | Qwen3.6 27B CER | Gemma 4 12B CER |
|----------|:--:|:--:|
| 经营报告 | 6.9% | 38.9% |
| 增值税发票 | 0.0% | crash |
| 技术文档 | truncated | 70.4% |
| 性能对比表 | correct (format diff) | hallucinated |
| 合同 | correct (format diff) | crash |

Full analysis: https://github.com/alitrack/labs/tree/main/ocr-benchmark
