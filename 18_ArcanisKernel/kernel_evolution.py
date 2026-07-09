"""Self-evolving kernel — runtime performance optimization hints from AI."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class KernelHint:
    hint_type: str = ""
    target: str = ""
    description: str = ""
    current_value: Any = None
    suggested_value: Any = None
    confidence: float = 0.0
    expected_improvement: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceMetric:
    metric_name: str = ""
    value: float = 0.0
    unit: str = ""
    timestamp: float = field(default_factory=time.time)
    context: dict[str, Any] = field(default_factory=dict)


class PerformanceCollector:
    def __init__(self):
        self._metrics: dict[str, list[PerformanceMetric]] = {}

    def record(self, metric: PerformanceMetric) -> None:
        if metric.metric_name not in self._metrics:
            self._metrics[metric.metric_name] = []
        self._metrics[metric.metric_name].append(metric)
        if len(self._metrics[metric.metric_name]) > 1000:
            self._metrics[metric.metric_name] = self._metrics[metric.metric_name][-500:]

    def get_average(self, metric_name: str, window: int = 100) -> Optional[float]:
        samples = self._metrics.get(metric_name, [])
        if not samples:
            return None
        recent = samples[-window:]
        return sum(s.value for s in recent) / len(recent)

    def get_trend(self, metric_name: str, window: int = 50) -> Optional[str]:
        samples = self._metrics.get(metric_name, [])
        if len(samples) < window * 2:
            return None
        old_avg = sum(s.value for s in samples[-window * 2:-window]) / window
        new_avg = sum(s.value for s in samples[-window:]) / window
        if new_avg > old_avg * 1.1:
            return "increasing"
        if new_avg < old_avg * 0.9:
            return "decreasing"
        return "stable"

    def get_all_metrics(self) -> dict[str, list[PerformanceMetric]]:
        return dict(self._metrics)


class HintGenerator:
    def __init__(self):
        self._rules: list[dict[str, Any]] = []
        self._seed_rules()

    def _seed_rules(self) -> None:
        self._rules = [
            {"metric": "context_switches_per_sec", "condition": "high", "threshold": 1000,
             "hint_type": "scheduling", "description": "High context switch rate — consider increasing time quantum",
             "suggestion": lambda v: int(v * 0.1)},
            {"metric": "cache_miss_rate", "condition": "high", "threshold": 0.3,
             "hint_type": "memory", "description": "High cache miss rate — optimize data locality",
             "suggestion": lambda v: "reorder_structures"},
            {"metric": "heap_fragmentation", "condition": "high", "threshold": 0.4,
             "hint_type": "memory", "description": "Heap fragmentation detected — trigger compaction",
             "suggestion": lambda v: "compact"},
            {"metric": "interrupt_latency_us", "condition": "high", "threshold": 100,
             "hint_type": "interrupts", "description": "High interrupt latency — check ISR efficiency",
             "suggestion": lambda v: "optimize_isr"},
            {"metric": "syscall_overhead_us", "condition": "high", "threshold": 50,
             "hint_type": "syscalls", "description": "High syscall overhead — batch operations if possible",
             "suggestion": lambda v: "batch_syscalls"},
        ]

    def generate(self, collector: PerformanceCollector) -> list[KernelHint]:
        hints: list[KernelHint] = []
        for rule in self._rules:
            avg = collector.get_average(rule["metric"])
            if avg is None:
                continue
            trend = collector.get_trend(rule["metric"])
            if avg > rule["threshold"] or (trend == "increasing" and avg > rule["threshold"] * 0.8):
                suggested = rule["suggestion"](avg)
                hints.append(KernelHint(
                    hint_type=rule["hint_type"],
                    target=rule["metric"],
                    description=rule["description"],
                    current_value=avg,
                    suggested_value=suggested,
                    confidence=min(avg / rule["threshold"], 1.0),
                    expected_improvement=f"Reduce {rule['metric']} from {avg:.2f} towards {rule['threshold']}",
                ))
        return hints


class SelfEvolvingKernel:
    def __init__(self):
        self.collector = PerformanceCollector()
        self.hint_generator = HintGenerator()
        self._hints_history: list[KernelHint] = []
        self._applied_hints: list[KernelHint] = []
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def record_metric(self, name: str, value: float, unit: str = "") -> None:
        self.collector.record(PerformanceMetric(metric_name=name, value=value, unit=unit))

    def analyze(self) -> list[KernelHint]:
        hints = self.hint_generator.generate(self.collector)
        self._hints_history.extend(hints)
        return hints

    def apply_hint(self, hint: KernelHint) -> bool:
        self._applied_hints.append(hint)
        return True

    def get_optimization_report(self) -> dict:
        return {
            "total_metrics": len(self.collector.get_all_metrics()),
            "hints_generated": len(self._hints_history),
            "hints_applied": len(self._applied_hints),
            "pending_hints": len(self._hints_history) - len(self._applied_hints),
        }

    def get_status(self) -> dict:
        return {
            "initialized": self._initialized,
            "metrics_tracked": len(self.collector.get_all_metrics()),
            "hints_generated": len(self._hints_history),
            "hints_applied": len(self._applied_hints),
        }
