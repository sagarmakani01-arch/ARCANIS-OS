"""System Benchmark Suite — performance measurement across the Arcanis stack."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class BenchmarkResult:
    name: str = ""
    iterations: int = 0
    total_seconds: float = 0.0
    min_ns: float = float("inf")
    max_ns: float = 0.0
    avg_ns: float = 0.0
    median_ns: float = 0.0
    ops_per_sec: float = 0.0
    percentiles: dict[str, float] = field(default_factory=dict)


class BenchmarkSuite:
    def __init__(self):
        self._benchmarks: dict[str, dict[str, Any]] = {}
        self._results: list[BenchmarkResult] = []

    def register(self, name: str, fn: Callable, setup: Optional[Callable] = None,
                 iterations: int = 1000, description: str = "") -> None:
        self._benchmarks[name] = {
            "fn": fn, "setup": setup, "iterations": iterations, "description": description,
        }

    def run(self, name: str) -> BenchmarkResult:
        bench = self._benchmarks.get(name)
        if not bench:
            return BenchmarkResult(name=name)

        fn = bench["fn"]
        setup = bench["setup"]
        iterations = bench["iterations"]

        if setup:
            setup()

        times: list[float] = []
        start_total = time.perf_counter()

        for _ in range(iterations):
            start = time.perf_counter()
            fn()
            end = time.perf_counter()
            times.append((end - start) * 1e9)

        total = time.perf_counter() - start_total
        times.sort()

        result = BenchmarkResult(
            name=name, iterations=iterations, total_seconds=total,
            min_ns=times[0] if times else 0,
            max_ns=times[-1] if times else 0,
            avg_ns=sum(times) / len(times) if times else 0,
            median_ns=times[len(times) // 2] if times else 0,
            ops_per_sec=iterations / total if total > 0 else 0,
        )

        for p in [50, 75, 90, 95, 99]:
            idx = min(int(len(times) * p / 100), len(times) - 1)
            result.percentiles[f"p{p}"] = times[idx] if times else 0

        self._results.append(result)
        return result

    def run_all(self) -> list[BenchmarkResult]:
        for name in self._benchmarks:
            self.run(name)
        return self._results

    def get_results(self) -> list[BenchmarkResult]:
        return list(self._results)

    def summary(self) -> dict:
        return {
            "total_benchmarks": len(self._benchmarks),
            "results": [
                {"name": r.name, "ops/sec": round(r.ops_per_sec, 1),
                 "avg_ns": round(r.avg_ns, 1), "p99_ns": round(r.percentiles.get("p99", 0), 1)}
                for r in self._results
            ],
        }


def create_default_suite() -> BenchmarkSuite:
    suite = BenchmarkSuite()

    suite.register("noop", lambda: None, iterations=100000, description="Empty function call overhead")
    suite.register("integer_add", lambda: 1 + 2, iterations=100000, description="Integer addition")
    suite.register("string_concat", lambda: "a" + "b", iterations=100000, description="String concatenation")
    suite.register("dict_lookup", lambda: {"a": 1}.get("a"), iterations=100000, description="Dictionary lookup")

    data = list(range(1000))
    suite.register("list_sort", lambda: sorted(data), iterations=1000, description="Sort 1000 integers")
    suite.register("list_comprehension", lambda: [x * 2 for x in range(100)], iterations=10000, description="List comprehension 100 items")

    import json
    obj = {"key": "value", "nested": {"a": 1, "b": [1, 2, 3]}}
    suite.register("json_serialize", lambda: json.dumps(obj), iterations=10000, description="JSON serialization")
    suite.register("json_deserialize", lambda: json.loads(json.dumps(obj)), iterations=10000, description="JSON deserialization")

    return suite
