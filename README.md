# labs 🧪

Experiments, benchmarks, and learning scripts.

一个干净的地方放各种测试、学习代码和 benchmark。

## Benchmarks

| 目录 | 内容 | 机器 | 日期 |
|:----|:----|:----:|:----:|
| `benchmarks/mac-embedding/` | 5 种向量嵌入方案吞吐量对比 | M3 Ultra 256GB | 2026-06 |
| `benchmarks/qwen-ollama-deploy/` | Ollama Qwen3.6-27b 调优 + 参数扫描 | M3 Ultra 256GB | 2026-06 |

## 原则

- 每个子目录自包含 README，有明确的运行说明
- Python 脚本用 `uv run --with ...`，不污染系统环境
- benchmark 数据来自实测，标注硬件环境
