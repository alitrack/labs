import unittest

import sweep_ollama
import stress_qwen_bench as bench


class TestBenchMath(unittest.TestCase):
    def test_percentile_uses_high_rank_selection(self):
        self.assertEqual(bench.percentile([1.0, 2.0, 3.0, 4.0], 0.95), 4.0)

    def test_aggregate_phase_uses_wall_clock_time(self):
        results = [
            {
                "status": 200,
                "elapsed": 4.0,
                "eval_count": 40,
                "prompt_eval_count": 20,
                "load_duration_s": 0.0,
                "prompt_eval_duration_s": 1.0,
                "eval_duration_s": 2.0,
            },
            {
                "status": 200,
                "elapsed": 5.0,
                "eval_count": 60,
                "prompt_eval_count": 30,
                "load_duration_s": 0.0,
                "prompt_eval_duration_s": 1.2,
                "eval_duration_s": 2.5,
            },
        ]
        summary = bench.aggregate_phase("phase", results, wall_seconds=5.0)
        self.assertAlmostEqual(summary["req_per_s"], 0.4)
        self.assertAlmostEqual(summary["out_tok_per_s"], 20.0)
        self.assertAlmostEqual(summary["p50_latency_s"], 5.0)

    def test_build_generate_payload_respects_request_options(self):
        payload = bench.build_generate_payload(
            model="m",
            prompt="p",
            num_predict=32,
            think=False,
            num_ctx=8192,
            temperature=0.0,
            keep_alive="24h",
        )
        self.assertEqual(payload["options"]["num_ctx"], 8192)
        self.assertEqual(payload["options"]["temperature"], 0.0)
        self.assertEqual(payload["options"]["num_predict"], 32)
        self.assertFalse(payload["think"])

    def test_build_run_matrix_expands_parallel_and_ctx(self):
        matrix = bench.build_run_matrix([1, 4], [8192, 16384], [False, True])
        self.assertEqual(len(matrix), 8)
        self.assertEqual(matrix[0], {"parallel": 1, "num_ctx": 8192, "think": False})
        self.assertEqual(matrix[-1], {"parallel": 4, "num_ctx": 16384, "think": True})

    def test_resolve_requests_scales_with_parallel(self):
        self.assertEqual(sweep_ollama.resolve_requests(4, parallel=6, requests_per_worker=3), 18)
        self.assertEqual(sweep_ollama.resolve_requests(24, parallel=6, requests_per_worker=3), 24)


if __name__ == "__main__":
    unittest.main()
