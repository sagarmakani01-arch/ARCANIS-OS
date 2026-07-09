from __future__ import annotations

import time
from typing import Optional

from .tracker import ProcessTracker, ProcessRecord
from .predictor import WorkloadPredictor, SchedulingHint, WorkloadPrediction


class AIScheduler:
    def __init__(self):
        self.tracker = ProcessTracker()
        self.predictor = WorkloadPredictor()
        self._hints_history: list[SchedulingHint] = []
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def update(self, pid: int, name: str = "", cpu_ms: float = 0.0,
               io_ms: float = 0.0, sleeping: bool = False,
               context_switch: bool = False, priority: int = 5,
               time_slice_used_pct: float = 0.0) -> list[SchedulingHint]:
        if not self._initialized:
            return []

        rec = self.tracker.track(
            pid=pid, name=name, cpu_ms=cpu_ms, io_ms=io_ms,
            sleeping=sleeping, context_switch=context_switch,
            priority=priority, time_slice_used_pct=time_slice_used_pct,
        )

        prediction = self.predictor.predict(rec)
        hints = self.predictor.get_hints(rec, prediction)

        rec.suggested_priority = prediction.suggested_priority
        rec.suggested_quantum = prediction.suggested_quantum
        rec.predicted_next_wake = self._predict_next_wake(rec)

        self._hints_history.extend(hints)
        return hints

    def _predict_next_wake(self, rec: ProcessRecord) -> Optional[float]:
        wake_times = list(rec.wake_times)
        if len(wake_times) < 3:
            return None
        intervals = [wake_times[i] - wake_times[i - 1] for i in range(1, len(wake_times))]
        avg_interval = sum(intervals) / len(intervals)
        return rec.metrics.last_seen + avg_interval

    def get_scheduling_plan(self) -> dict:
        records = self.tracker.get_all_records()
        plan: dict[int, dict] = {}
        for pid, rec in records.items():
            prediction = self.predictor.predict(rec)
            hints = self.predictor.get_hints(rec, prediction)
            plan[pid] = {
                "name": rec.metrics.name,
                "behavior": rec.behavior.value,
                "prediction": prediction.workload_type.value,
                "confidence": prediction.confidence,
                "suggested_priority": prediction.suggested_priority,
                "suggested_quantum": prediction.suggested_quantum,
                "hints": [
                    {"action": h.action, "priority_delta": h.priority_delta,
                     "quantum_delta": h.quantum_delta, "reasoning": h.reasoning}
                    for h in hints
                ],
            }
        return plan

    def get_stats(self) -> dict:
        return {
            "initialized": self._initialized,
            "tracker": self.tracker.get_global_stats(),
            "behaviors": self.tracker.get_behavior_counts(),
            "predictions": self.predictor.get_prediction_stats(),
            "hints_issued": len(self._hints_history),
        }

    def cleanup(self, max_age: float = 300.0) -> int:
        return self.tracker.cleanup_stale(max_age)
