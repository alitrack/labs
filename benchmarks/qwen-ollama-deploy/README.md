# Qwen3.6 27B Coding MXFP8 Benchmark Notes

Date: 2026-06-03
Host: Mac Studio (Apple M3 Ultra, unified memory 222.7 GiB reported by Ollama)
Service: Ollama 0.23.2
Model: `qwen3.6:27b-coding-mxfp8`

## Current Recommended Ollama Service Settings

Applied via `~/Library/LaunchAgents/homebrew.mxcl.ollama.plist`:

```text
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_NUM_PARALLEL=2
OLLAMA_CONTEXT_LENGTH=65536
OLLAMA_KEEP_ALIVE=24h
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=q8_0
```

Why this setting:

- `NUM_PARALLEL=2` is the best practical point on this machine.
- Higher parallel values barely improve total throughput, but they materially worsen tail latency.
- `CONTEXT_LENGTH=65536` is a good coding-service default without leaving the server at the 256k default.

## Benchmark Scripts

- Strict benchmark: [stress_qwen_bench.py](/Users/sa/tmp/stress_qwen_bench.py)
- Sweep harness: [sweep_ollama.py](/Users/sa/tmp/sweep_ollama.py)
- Unit tests: [test_stress_qwen_bench.py](/Users/sa/tmp/test_stress_qwen_bench.py)
- Sweep output: [qwen_sweep_results.json](/Users/sa/tmp/qwen_sweep_results.json)

## Key Commands

Warm the model:

```bash
python3 /Users/sa/tmp/stress_qwen_bench.py \
  --base-url http://10.10.10.8:11434 \
  --concurrency 1 \
  --requests 2 \
  --num-ctx 65536 \
  --num-predict 32 \
  --format json
```

Steady-state practical benchmark:

```bash
python3 /Users/sa/tmp/stress_qwen_bench.py \
  --base-url http://10.10.10.8:11434 \
  --concurrency 2 \
  --requests 6 \
  --num-ctx 65536 \
  --num-predict 64 \
  --format json
```

Sweep selected configs:

```bash
python3 /Users/sa/tmp/sweep_ollama.py \
  --base-url http://10.10.10.8:11434 \
  --parallel-values 1,2,4,6 \
  --ctx-values 8192,16384,65536 \
  --think-values false \
  --requests 4 \
  --requests-per-worker 3 \
  --num-predict 64 \
  --json-out /Users/sa/tmp/qwen_sweep_results.json
```

## Final Practical Result

After warm-up, with:

```text
concurrency=2
requests=6
num_ctx=65536
num_predict=64
temperature=0
think=false
```

Measured result:

```text
p50 latency      5.73s
p95 latency      5.79s
throughput       22.25 output tok/s
request rate     0.35 req/s
decode duration  2.78s
prefill duration 0.09s
success rate     100%
```

## Comparison By Parallelism

Representative sweep results:

```text
parallel=1, num_ctx=65536 -> 22.10 tok/s, p95=2.90s
parallel=2, num_ctx=65536 -> 22.35 tok/s, p95=5.76s
parallel=4, num_ctx=65536 -> 22.39 tok/s, p95=11.50s
parallel=6, num_ctx=65536 -> 22.44 tok/s, p95=17.16s
```

Interpretation:

- `parallel=1` is best for the lowest latency.
- `parallel=2` is best for real service use on this machine.
- `parallel=4` and `6` are not worth it unless you only care about squeezing out negligible extra aggregate throughput.

## Request-Side Recommendations

For pure speed tests:

```text
temperature=0
think=false
num_ctx=8192 or 16384
```

For a real coding service:

```text
temperature=0
think=false by default
num_ctx=65536
```

Enable thinking only when you explicitly need it, because it is not the fastest default operating mode for this model family.

## Notes

- The benchmark scripts use Ollama native `/api/generate`, not OpenAI-compatible `/v1/chat/completions`, so they can report `load`, `prefill`, and `decode` timing separately.
- The first request after a restart or cold state can include noticeable model load time. Judge service performance from warm runs.
- If maximum performance is the goal, the next likely improvement is upgrading Ollama from `0.23.2` to a newer release and rerunning the same benchmark set.
