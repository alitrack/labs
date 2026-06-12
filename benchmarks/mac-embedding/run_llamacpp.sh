#!/usr/bin/env bash
# Benchmark: llama.cpp bge-m3 via HTTP server
#
# Requires:
#   - llama.cpp built with Metal: cmake -B build -DGGML_METAL=ON
#   - bge-m3 GGUF: downloaded from HF
#   - Python 3 for the client
#
# Usage:
#   ./run_llamacpp.sh /path/to/llama.cpp /path/to/bge-m3.gguf
#
# Example:
#   ./run_llamacpp.sh ~/llama.cpp ~/.cache/llama.cpp/bge-m3.gguf
#
# The script starts llama-server, runs the benchmark, then stops it.

set -euo pipefail

LLAMA_DIR="${1:-}"
MODEL_PATH="${2:-}"

if [ -z "$LLAMA_DIR" ] || [ -z "$MODEL_PATH" ]; then
    echo "Usage: $0 /path/to/llama.cpp /path/to/bge-m3.gguf"
    echo ""
    echo "Quick start:"
    echo "  git clone https://github.com/ggml-org/llama.cpp"
    echo "  cd llama.cpp && cmake -B build -DGGML_METAL=ON && cmake --build build --config Release"
    echo "  cd /tmp && curl -LO https://huggingface.co/taozhiyuai/bge-m3-gguf/resolve/main/bge-m3-Q4_K_M.gguf"
    echo "  $0 ./llama.cpp /tmp/bge-m3-Q4_K_M.gguf"
    exit 1
fi

SERVER_BIN="$LLAMA_DIR/build/bin/llama-server"
PORT=8080
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check server binary
if [ ! -x "$SERVER_BIN" ]; then
    echo "ERROR: llama-server not found at $SERVER_BIN"
    echo "Build it: cd $LLAMA_DIR && cmake -B build -DGGML_METAL=ON && cmake --build build --config Release"
    exit 1
fi

# Check model
if [ ! -f "$MODEL_PATH" ]; then
    echo "ERROR: Model not found at $MODEL_PATH"
    echo "Download: curl -LO https://huggingface.co/taozhiyuai/bge-m3-gguf/resolve/main/bge-m3-Q4_K_M.gguf"
    exit 1
fi

echo "=== llama.cpp bge-m3 Benchmark ==="
echo "Model: $MODEL_PATH"
echo "Port:  $PORT"

# Start server
echo ""
echo "Starting llama-server..."
"$SERVER_BIN" \
    -m "$MODEL_PATH" \
    --embeddings --pooling mean \
    --host 127.0.0.1 --port $PORT \
    -c 8192 \
    --log-disable > /tmp/llama-server.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server to be ready
echo "Waiting for server..."
for i in $(seq 1 30); do
    if curl -s "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; then
        echo "Server ready after ${i}s"
        break
    fi
    sleep 1
done

# Run benchmark
echo ""
echo "Running benchmark..."
cd "$SCRIPT_DIR"
python3 -c "
import sys, os
sys.path.insert(0, os.path.dirname('$SCRIPT_DIR/mac-embedding'))
from common import benchmark_encode, print_results
from test_texts import TEXTS
import requests

def llamacpp_encode(texts, batch_size):
    resp = requests.post(
        'http://127.0.0.1:$PORT/v1/embeddings',
        json={'input': texts[:batch_size], 'model': 'bge-m3'},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()['data'][0]['embedding']

results = benchmark_encode(llamacpp_encode, TEXTS, batch_size=len(TEXTS), warmup_runs=2, measure_runs=5)
print_results(results, 'llama.cpp bge-m3')
"

# Stop server
kill "$SERVER_PID" 2>/dev/null || true
wait "$SERVER_PID" 2>/dev/null || true
echo ""
echo "Server stopped. Benchmark complete."
