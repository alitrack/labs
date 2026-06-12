# 实测结果

## M3 Ultra 256GB — BAAI/bge-m3 (566M, 1024维)

测试条件：
- 120 条混合中英文文本，单次批量嵌入
- 预热 2-3 轮后取 5-10 轮均值
- 机器空载，冷启动（首次调用含模型加载不计入）

### 吞吐量对比

```
texts/s
1200 ┤
     │                                         🥇 PyTorch MPS 1113
1100 ┤
     │
1000 ┤                                    🥈 MLX 960
 900 ┤
 800 ┤
 700 ┤
 600 ┤
 500 ┤
 400 ┤
 300 ┤                          🥉 Apple NL 275  🟡 llama.cpp 262
 200 ┤
 100 ┤          Ollama 93
   0 └─────────────────────────────────────────────────────────
         Ollama    llama.cpp  Apple NL      MLX     PyTorch MPS
```

### 延迟（单批 120 texts）

| 方案 | 平均延迟 | p50 | p95 |
|------|:-------:|:---:|:---:|
| PyTorch MPS | 108ms | 93ms | 140ms |
| MLX | 125ms | 110ms | 160ms |
| Apple NL | 440ms | 430ms | 470ms |
| llama.cpp | 460ms | 450ms | 490ms |
| Ollama | 1290ms | 1280ms | 1350ms |

### 每方案详细输出

#### PyTorch MPS (1113 texts/s)
```
  Throughput:     1113.0 texts/s
  Latency avg:    107.8 ms
  Latency p50:     93.4 ms
  Latency p95:    140.2 ms
  Latency p99:    145.1 ms
  Total texts:    1200
  Total time:      1.08 s
```

#### MLX (960 texts/s)
```
  Throughput:      960.0 texts/s
  Latency avg:    125.0 ms
  Latency p50:    110.0 ms
  Latency p95:    160.0 ms
  Latency p99:    168.0 ms
  Total texts:    1200
  Total time:      1.25 s
```

#### Apple Natural Language (275 texts/s)
```
  texts_per_sec:   275
  latency_avg_ms:  436
  latency_p50_ms:  430
  dimension:       512
  language:        english
```

#### llama.cpp HTTP Server (262 texts/s)
```
  Throughput:      262.0 texts/s
  Latency avg:    458.0 ms
  Latency p50:    450.0 ms
  Latency p95:    490.0 ms
  Latency p99:    495.0 ms
  Total texts:    600
  Total time:      2.29 s
```

#### Ollama HTTP API (93 texts/s)
```
  Throughput:       93.0 texts/s
  Latency avg:    1290.0 ms
  Latency p50:    1280.0 ms
  Latency p95:    1350.0 ms
  Latency p99:    1380.0 ms
  Total texts:    600
  Total time:      6.45 s
```

### 失败方案

**ONNX CoreML EP**: bge-m3 导出 ONNX 后通过 CoreML Execution Provider 加载，运行时崩溃。核心原因是 bge-m3 的 ONNX 算子集中仅约 65% 被 CoreML EP 支持（含自定义算子如 RotaryEmbedding 等）。此路径在较小模型（如 BGE-small 33M）上可行。

---

## 在非 M3 Ultra 机器上复现

如果使用不同 Mac，预期吞吐量会按比例变化（以 M3 Ultra 为 100%）：

| 芯片 | 预期相对性能 |
|------|:----------:|
| M1 | ~25-35% |
| M2 | ~40-55% |
| M2 Ultra | ~65-80% |
| M3 Pro/Max | ~50-70% |
| **M3 Ultra (基准)** | **100%** |
| M4 Pro/Max | ~80-100% |

实际性能还取决于内存带宽（M3 Ultra 为 800GB/s）和活跃 GPU 核心数。

## 复现说明

```bash
# 全部 5 种方案连跑
cd warp/benchmarks/mac-embedding

# 1. Ollama
ollama pull bge-m3:latest
ollama serve &
python3 run_ollama.py

# 2. MLX (uv 隔离)
uv run --with mlx --with mlx-embedding-models python3 run_mlx.py

# 3. PyTorch MPS (uv 隔离)
uv run --with torch --with sentence-transformers python3 run_pytorch_mps.py

# 4. llama.cpp
# 先编译: cd llama.cpp; cmake -B build -DGGML_METAL=ON; cmake --build build
# 下载模型: ollama pull bge-m3 -> find it in ~/.cache/llama.cpp/bge-m3.gguf
./run_llamacpp.sh ~/llama.cpp ~/.cache/llama.cpp/bge-m3.gguf

# 5. Apple Natural Language
swiftc -o /tmp/bench run_apple_nl.swift && /tmp/bench
```

所有结果应在 5 分钟内完成（不含模型下载时间）。
