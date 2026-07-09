from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .tracker import ProcessRecord, ProcessBehavior


class WorkloadType(Enum):
    COMPUTE_HEAVY = "compute_heavy"
    IO_HEAVY = "io_heavy"
    INTERACTIVE = "interactive"
    BACKGROUND = "background"
    REALTIME = "realtime"
    UNKNOWN = "unknown"


@dataclass
class WorkloadPrediction:
    workload_type: WorkloadType
    confidence: float
    suggested_priority: int
    suggested_quantum: int
    predicted_cpu_pct: float
    predicted_io_pct: float
    reasoning: str


@dataclass
class SchedulingHint:
    pid: int
    action: str  # "boost", "reduce", "extend_quantum", "shrink_quantum", "block", "yield"
    priority_delta: int = 0
    quantum_delta: int = 0
    confidence: float = 0.0
    reasoning: str = ""


PRIORITY_MAP = {
    WorkloadType.REALTIME: 10,
    WorkloadType.INTERACTIVE: 8,
    WorkloadType.COMPUTE_HEAVY: 6,
    WorkloadType.IO_HEAVY: 5,
    WorkloadType.BACKGROUND: 2,
    WorkloadType.UNKNOWN: 5,
}

QUANTUM_MAP = {
    WorkloadType.REALTIME: 20,
    WorkloadType.INTERACTIVE: 5,
    WorkloadType.COMPUTE_HEAVY: 15,
    WorkloadType.IO_HEAVY: 8,
    WorkloadType.BACKGROUND: 3,
    WorkloadType.UNKNOWN: 10,
}


class WorkloadPredictor:
    def __init__(self):
        self._history: deque[WorkloadPrediction] = deque(maxlen=200)
        self._pattern_cache: dict[int, list[float]] = {}

    def predict(self, rec: ProcessRecord) -> WorkloadPrediction:
        cpu = list(rec.cpu_samples)
        io = list(rec.io_samples)

        avg_cpu = sum(cpu[-20:]) / max(len(cpu[-20:]), 1)
        avg_io = sum(io[-20:]) / max(len(io[-20:]), 1)
        total = avg_cpu + avg_io

        if total == 0:
            pred = WorkloadPrediction(
                workload_type=WorkloadType.BACKGROUND,
                confidence=0.9,
                suggested_priority=PRIORITY_MAP[WorkloadType.BACKGROUND],
                suggested_quantum=QUANTUM_MAP[WorkloadType.BACKGROUND],
                predicted_cpu_pct=0.0,
                predicted_io_pct=0.0,
                reasoning="No recent CPU or IO activity detected",
            )
        else:
            cpu_pct = avg_cpu / total
            io_pct = avg_io / total
            sleep_freq = len(rec.wake_times) / max(rec.metrics.total_runtime_ms / 1000, 0.1)
            ctx_rate = rec.metrics.context_switches / max(rec.metrics.total_runtime_ms / 1000, 0.1)

            wtype, conf, reasoning = self._classify(cpu_pct, io_pct, sleep_freq, ctx_rate)
            pred = WorkloadPrediction(
                workload_type=wtype,
                confidence=conf,
                suggested_priority=PRIORITY_MAP[wtype],
                suggested_quantum=QUANTUM_MAP[wtype],
                predicted_cpu_pct=cpu_pct * 100,
                predicted_io_pct=io_pct * 100,
                reasoning=reasoning,
            )

        self._history.append(pred)
        return pred

    def _classify(self, cpu_pct: float, io_pct: float,
                  sleep_freq: float, ctx_rate: float) -> tuple[WorkloadType, float, str]:
        if sleep_freq > 10.0 and io_pct > 0.5:
            return WorkloadType.INTERACTIVE, 0.85, f"High sleep frequency ({sleep_freq:.1f}/s) with IO dominance"
        if cpu_pct > 0.85:
            return WorkloadType.COMPUTE_HEAVY, 0.9, f"CPU ratio {cpu_pct:.0%} indicates compute-bound"
        if io_pct > 0.7:
            return WorkloadType.IO_HEAVY, 0.85, f"IO ratio {io_pct:.0%} indicates IO-bound"
        if ctx_rate > 20.0:
            return WorkloadType.REALTIME, 0.8, f"High context switch rate ({ctx_rate:.1f}/s)"
        if cpu_pct < 0.1 and io_pct < 0.1:
            return WorkloadType.BACKGROUND, 0.7, "Low resource usage"
        return WorkloadType.UNKNOWN, 0.5, f"Mixed workload (CPU {cpu_pct:.0%}, IO {io_pct:.0%})"

    def get_hints(self, rec: ProcessRecord, prediction: WorkloadPrediction) -> list[SchedulingHint]:
        hints: list[SchedulingHint] = []
        current_priority = rec.metrics.priority

        if prediction.suggested_priority > current_priority:
            hints.append(SchedulingHint(
                pid=rec.metrics.pid,
                action="boost",
                priority_delta=prediction.suggested_priority - current_priority,
                confidence=prediction.confidence,
                reasoning=prediction.reasoning,
            ))
        elif prediction.suggested_priority < current_priority:
            hints.append(SchedulingHint(
                pid=rec.metrics.pid,
                action="reduce",
                priority_delta=prediction.suggested_priority - current_priority,
                confidence=prediction.confidence,
                reasoning=prediction.reasoning,
            ))

        current_quantum = 10
        if prediction.suggested_quantum > current_quantum:
            hints.append(SchedulingHint(
                pid=rec.metrics.pid,
                action="extend_quantum",
                quantum_delta=prediction.suggested_quantum - current_quantum,
                confidence=prediction.confidence,
                reasoning=f"Extend quantum for {prediction.workload_type.value} workload",
            ))
        elif prediction.suggested_quantum < current_quantum:
            hints.append(SchedulingHint(
                pid=rec.metrics.pid,
                action="shrink_quantum",
                quantum_delta=prediction.suggested_quantum - current_quantum,
                confidence=prediction.confidence,
                reasoning=f"Shrink quantum for {prediction.workload_type.value} workload",
            ))

        return hints

    def get_history(self, limit: int = 50) -> list[WorkloadPrediction]:
        return list(self._history)[-limit:]

    def get_prediction_stats(self) -> dict:
        if not self._history:
            return {"total": 0}
        by_type: dict[str, int] = {}
        for p in self._history:
            t = p.workload_type.value
            by_type[t] = by_type.get(t, 0) + 1
        avg_conf = sum(p.confidence for p in self._history) / len(self._history)
        return {"total": len(self._history), "by_type": by_type, "avg_confidence": avg_conf}
