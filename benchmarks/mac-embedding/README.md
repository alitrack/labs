# mac-embedding — Mac ARM Embedding Benchmark Suite

同一台机器、同一个模型、同一批测试文本，对比 Mac ARM 上 5 种向量嵌入部署方案的吞吐量和延迟。

## 硬件/软件环境

| 项目 | 值 |
|------|----|
| 机器 | Mac Studio M3 Ultra |
| 内存 | 256GB 统一内存 |
| 系统 | macOS (Apple Silicon) |
| 模型 | BAAI/bge-m3 (566M, 1024维) |
| 测试集 | 120 条混合中英文短文本（`test_texts.py`） |
| 批次 | 全量 120 texts 单次批量嵌入 |

## 快速开始

```bash
git clone git@github.com:alitrack/warp.git
cd warp/benchmarks/mac-embedding

# Ollama
ollama pull bge-m3:latest && ollama serve
python3 run_ollama.py

# MLX
uv run --with mlx --with mlx-embedding-models python3 run_mlx.py

# PyTorch MPS
uv run --with torch --with sentence-transformers python3 run_pytorch_mps.py

# llama.cpp (编译 + 下载模型后)
./run_llamacpp.sh /path/to/llama.cpp /path/to/bge-m3.gguf

# Apple Natural Language (Swift)
swiftc -o /tmp/bench run_apple_nl.swift && /tmp/bench
```

## 实测结果（M3 Ultra, bge-m3, 120 texts batch）

| 方案 | 吞吐量 (texts/s) | 相对 Ollama | 硬件路径 | 备注 |
|------|:----------------:|:----------:|:--------:|------|
| **PyTorch MPS 🥇** | **1113** | **12×** | GPU (MPS) | sentence-transformers, 覆盖最全 |
| MLX 🥈 | 960 | 10× | GPU (Metal) | Apple 官方 ML 框架 |
| Apple Natural Language 🥉 | 275 | 3× | CPU (AMX) | 仅英文 512-dim, 零安装 |
| llama.cpp (HTTP) | 262 | 3× | GPU (Metal) | GGUF, 常驻 HTTP 服务 |
| Ollama | 93 | 1× | GPU (Metal) | HTTP 封装, 快速上手 |

### ❌ ONNX CoreML EP — 失败

bge-m3 的 ONNX 算子仅约 65% 被 CoreML Execution Provider 支持，运行时崩溃。在小模型（如 BGE-small 33M）上可用。

## 关键结论

1. **PyTorch MPS > MLX** — 网上说 MLX 快 40-146%，但在 M3 Ultra + bge-m3 (566M) 上 PyTorch 反而快 16%。大矩阵 kernel 优化是关键。
2. **Ollama 垫底** — HTTP 封装带来的序列化 + 进程间通信开销导致 10-12 倍性能损失。
3. **llama.cpp HTTP 服务 ~ Apple NL** — 一条走 GPU、一条走 CPU AMX，性能接近但服务能力天差地别。
4. **中文必须用 bge-m3** — Apple NL 将中文拆为单字，检索质量等价随机。

## 文件结构

```
benchmarks/mac-embedding/
├── README.md              ← 本文件
├── RESULTS.md             ← 详细结果和图表
├── common.py              ← 基准工具函数
├── test_texts.py          ← 120 条测试文本
├── run_ollama.py          ← Ollama bge-m3
├── run_mlx.py             ← MLX bge-m3
├── run_pytorch_mps.py     ← PyTorch MPS bge-m3
├── run_llamacpp.sh        ← llama.cpp bge-m3
└── run_apple_nl.swift     ← Apple Natural Language
```
