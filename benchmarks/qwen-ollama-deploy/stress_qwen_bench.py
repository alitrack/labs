#!/usr/bin/env python3
"""
Rigorous Ollama benchmark for qwen3.6:27b-coding-mxfp8.

Uses the native /api/generate endpoint so the benchmark can report
load, prefill, and decode timings separately.
"""

from __future__ import annotations

import argparse
import json
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://10.10.10.8:11434"
DEFAULT_MODEL = "qwen3.6:27b-coding-mxfp8"
DEFAULT_KEEP_ALIVE = "24h"
DEFAULT_TIMEOUT = 600

PROMPTS = {
    "short": "Write a Python function that reverses a linked list iteratively.",
    "medium": (
        "Design a Rust HTTP service with structured logging, graceful shutdown, "
        "health checks, and connection pooling. Provide a concise code skeleton."
    ),
    "long": (
        "You are reviewing a coding assistant backend. Produce a compact but "
        "specific design for request routing, sandbox execution, retries, "
        "streaming response assembly, and observability. Include interface "
        "boundaries and failure handling."
    ),
}


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(len(ordered) * ratio)
    if index >= len(ordered):
        index = len(ordered) - 1
    return ordered[index]


def ns_to_s(value: Any) -> float:
    if not value:
        return 0.0
    return float(value) / 1_000_000_000.0


def build_generate_payload(
    model: str,
    prompt: str,
    num_predict: int,
    think: bool,
    num_ctx: int,
    temperature: float,
    keep_alive: str,
) -> dict[str, Any]:
    return {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": think,
        "keep_alive": keep_alive,
        "options": {
            "num_predict": num_predict,
            "num_ctx": num_ctx,
            "temperature": temperature,
        },
    }


def build_run_matrix(
    parallels: list[int],
    contexts: list[int],
    think_values: list[bool],
) -> list[dict[str, Any]]:
    return [
        {"parallel": parallel, "num_ctx": num_ctx, "think": think}
        for parallel in parallels
        for num_ctx in contexts
        for think in think_values
    ]


def pick_prompt(prompt_kind: str, prompt_file: str | None) -> str:
    if prompt_file:
        return Path(prompt_file).read_text(encoding="utf-8")
    return PROMPTS[prompt_kind]


def check_connectivity(base_url: str, timeout: int) -> dict[str, Any]:
    request = Request(f"{base_url.rstrip('/')}/api/tags")
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body


def call_generate(
    request_id: int,
    base_url: str,
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    request = Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
            elapsed = time.monotonic() - started
            return {
                "id": request_id,
                "status": response.status,
                "elapsed": round(elapsed, 3),
                "prompt_eval_count": body.get("prompt_eval_count", 0),
                "eval_count": body.get("eval_count", 0),
                "total_duration_s": ns_to_s(body.get("total_duration")),
                "load_duration_s": ns_to_s(body.get("load_duration")),
                "prompt_eval_duration_s": ns_to_s(body.get("prompt_eval_duration")),
                "eval_duration_s": ns_to_s(body.get("eval_duration")),
                "done_reason": body.get("done_reason", ""),
                "response_chars": len(body.get("response", "") or ""),
            }
    except HTTPError as exc:
        elapsed = time.monotonic() - started
        return {
            "id": request_id,
            "status": exc.code,
            "elapsed": round(elapsed, 3),
            "error": str(exc),
        }
    except (URLError, TimeoutError, OSError) as exc:
        elapsed = time.monotonic() - started
        return {
            "id": request_id,
            "status": 0,
            "elapsed": round(elapsed, 3),
            "error": str(exc),
        }


def aggregate_phase(name: str, results: list[dict[str, Any]], wall_seconds: float) -> dict[str, Any]:
    success = [item for item in results if item["status"] == 200]
    failures = [item for item in results if item["status"] != 200]
    latencies = sorted(item["elapsed"] for item in success)
    prompt_eval_durations = [item.get("prompt_eval_duration_s", 0.0) for item in success]
    eval_durations = [item.get("eval_duration_s", 0.0) for item in success]
    load_durations = [item.get("load_duration_s", 0.0) for item in success]
    output_tokens = sum(item.get("eval_count", 0) for item in success)
    prompt_tokens = sum(item.get("prompt_eval_count", 0) for item in success)

    summary = {
        "name": name,
        "requests": len(results),
        "success": len(success),
        "failures": len(failures),
        "success_rate": (len(success) / len(results)) if results else 0.0,
        "wall_seconds": wall_seconds,
        "req_per_s": (len(success) / wall_seconds) if wall_seconds > 0 else 0.0,
        "out_tok_per_s": (output_tokens / wall_seconds) if wall_seconds > 0 else 0.0,
        "prompt_tok_per_s": (prompt_tokens / wall_seconds) if wall_seconds > 0 else 0.0,
        "output_tokens": output_tokens,
        "prompt_tokens": prompt_tokens,
        "p50_latency_s": percentile(latencies, 0.50),
        "p95_latency_s": percentile(latencies, 0.95),
        "p99_latency_s": percentile(latencies, 0.99),
        "avg_latency_s": statistics.mean(latencies) if latencies else 0.0,
        "min_latency_s": min(latencies) if latencies else 0.0,
        "max_latency_s": max(latencies) if latencies else 0.0,
        "avg_load_duration_s": statistics.mean(load_durations) if load_durations else 0.0,
        "avg_prompt_eval_duration_s": (
            statistics.mean(prompt_eval_durations) if prompt_eval_durations else 0.0
        ),
        "avg_eval_duration_s": statistics.mean(eval_durations) if eval_durations else 0.0,
        "errors": failures[:5],
    }
    return summary


def run_benchmark(
    *,
    base_url: str,
    model: str,
    prompt: str,
    concurrency: int,
    requests: int,
    num_predict: int,
    num_ctx: int,
    temperature: float,
    think: bool,
    keep_alive: str,
    timeout: int,
    phase_name: str,
) -> dict[str, Any]:
    payload = build_generate_payload(
        model=model,
        prompt=prompt,
        num_predict=num_predict,
        think=think,
        num_ctx=num_ctx,
        temperature=temperature,
        keep_alive=keep_alive,
    )

    results: list[dict[str, Any]] = []
    results_lock = threading.Lock()
    wall_start = time.monotonic()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(call_generate, request_id, base_url, payload, timeout)
            for request_id in range(requests)
        ]
        for future in as_completed(futures):
            result = future.result()
            with results_lock:
                results.append(result)

    wall_seconds = time.monotonic() - wall_start
    summary = aggregate_phase(phase_name, results, wall_seconds=wall_seconds)
    summary["config"] = {
        "base_url": base_url,
        "model": model,
        "concurrency": concurrency,
        "requests": requests,
        "num_predict": num_predict,
        "num_ctx": num_ctx,
        "temperature": temperature,
        "think": think,
        "keep_alive": keep_alive,
    }
    return summary


def text_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"{summary['name']}",
        f"  requests={summary['requests']} success={summary['success']} failures={summary['failures']} success_rate={summary['success_rate'] * 100:.1f}%",
        f"  wall={summary['wall_seconds']:.2f}s req/s={summary['req_per_s']:.2f} out_tok/s={summary['out_tok_per_s']:.2f} prompt_tok/s={summary['prompt_tok_per_s']:.2f}",
        f"  latency p50={summary['p50_latency_s']:.2f}s p95={summary['p95_latency_s']:.2f}s p99={summary['p99_latency_s']:.2f}s avg={summary['avg_latency_s']:.2f}s",
        f"  durations load={summary['avg_load_duration_s']:.2f}s prefill={summary['avg_prompt_eval_duration_s']:.2f}s decode={summary['avg_eval_duration_s']:.2f}s",
    ]
    if summary["errors"]:
        lines.append("  errors:")
        for item in summary["errors"]:
            lines.append(f"    [{item['id']}] status={item['status']} {item.get('error', '')[:160]}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rigorous Ollama benchmark")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt-kind", choices=sorted(PROMPTS.keys()), default="medium")
    parser.add_argument("--prompt-file")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--requests", type=int, default=8)
    parser.add_argument("--num-predict", type=int, default=128)
    parser.add_argument("--num-ctx", type=int, default=8192)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--keep-alive", default=DEFAULT_KEEP_ALIVE)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--phase-name", default="bench")
    parser.add_argument("--think", action="store_true", help="Enable model thinking")
    parser.add_argument("--skip-connectivity-check", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompt = pick_prompt(args.prompt_kind, args.prompt_file)

    if not args.skip_connectivity_check:
        check_connectivity(args.base_url, args.timeout)

    summary = run_benchmark(
        base_url=args.base_url,
        model=args.model,
        prompt=prompt,
        concurrency=args.concurrency,
        requests=args.requests,
        num_predict=args.num_predict,
        num_ctx=args.num_ctx,
        temperature=args.temperature,
        think=args.think,
        keep_alive=args.keep_alive,
        timeout=args.timeout,
        phase_name=args.phase_name,
    )

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(text_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
