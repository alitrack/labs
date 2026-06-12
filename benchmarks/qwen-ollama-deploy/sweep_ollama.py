#!/usr/bin/env python3
"""
Autoresearch-style local sweep harness for Ollama benchmark runs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import stress_qwen_bench as bench


def parse_csv_ints(raw: str) -> list[int]:
    return [int(item.strip()) for item in raw.split(",") if item.strip()]


def parse_csv_bools(raw: str) -> list[bool]:
    mapping = {"false": False, "0": False, "true": True, "1": True}
    return [mapping[item.strip().lower()] for item in raw.split(",") if item.strip()]


def resolve_requests(requests: int, *, parallel: int, requests_per_worker: int) -> int:
    return max(requests, parallel * requests_per_worker)


def score_summary(summary: dict[str, Any]) -> tuple[float, float, float]:
    return (
        summary["out_tok_per_s"],
        -summary["p95_latency_s"],
        -summary["avg_load_duration_s"],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sweep Ollama benchmark configs")
    parser.add_argument("--base-url", default=bench.DEFAULT_BASE_URL)
    parser.add_argument("--model", default=bench.DEFAULT_MODEL)
    parser.add_argument("--prompt-kind", choices=sorted(bench.PROMPTS.keys()), default="medium")
    parser.add_argument("--prompt-file")
    parser.add_argument("--parallel-values", default="1,2,4")
    parser.add_argument("--ctx-values", default="8192,16384,65536")
    parser.add_argument("--think-values", default="false")
    parser.add_argument("--requests", type=int, default=6)
    parser.add_argument("--requests-per-worker", type=int, default=3)
    parser.add_argument("--num-predict", type=int, default=96)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--keep-alive", default=bench.DEFAULT_KEEP_ALIVE)
    parser.add_argument("--timeout", type=int, default=bench.DEFAULT_TIMEOUT)
    parser.add_argument("--json-out")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompt = bench.pick_prompt(args.prompt_kind, args.prompt_file)
    bench.check_connectivity(args.base_url, args.timeout)

    matrix = bench.build_run_matrix(
        parse_csv_ints(args.parallel_values),
        parse_csv_ints(args.ctx_values),
        parse_csv_bools(args.think_values),
    )

    summaries = []
    for index, item in enumerate(matrix, start=1):
        requests = resolve_requests(
            args.requests,
            parallel=item["parallel"],
            requests_per_worker=args.requests_per_worker,
        )
        summary = bench.run_benchmark(
            base_url=args.base_url,
            model=args.model,
            prompt=prompt,
            concurrency=item["parallel"],
            requests=requests,
            num_predict=args.num_predict,
            num_ctx=item["num_ctx"],
            temperature=args.temperature,
            think=item["think"],
            keep_alive=args.keep_alive,
            timeout=args.timeout,
            phase_name=f"run-{index}",
        )
        summaries.append(summary)
        if args.format == "text":
            print(bench.text_summary(summary))
            print("")

    ranked = sorted(summaries, key=score_summary, reverse=True)
    output = {
        "runs": summaries,
        "best": ranked[0] if ranked else None,
    }

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Ranked best configs:")
        for index, summary in enumerate(ranked[:5], start=1):
            config = summary["config"]
            print(
                f"  {index}. parallel={config['concurrency']} num_ctx={config['num_ctx']} think={config['think']} "
                f"out_tok/s={summary['out_tok_per_s']:.2f} p95={summary['p95_latency_s']:.2f}s "
                f"req/s={summary['req_per_s']:.2f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
