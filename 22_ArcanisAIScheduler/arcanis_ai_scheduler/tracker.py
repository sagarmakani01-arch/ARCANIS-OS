from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProcessBehavior(Enum):
    CPU_BOUND = "cpu_bound"
    IO_BOUND = "io_bound"
    INTERACTIVE = "interactive"
    BATCH = "batch"
    IDLE = "idle"
    UNKNOWN = "unknown"


@dataclass
class ProcessMetrics:
    pid: int = 0
    name: str = ""
    cpu_time_ms: float = 0.0
    io_wait_ms: float = 0.0
    sleep_count: int = 0
    wake_count: int = 0
    context_switches: int = 0
    total_runtime_ms: float = 0.0
    last_seen: float = field(default_factory=time.time)
    priority: int = 5
    time_slice_used_pct: float = 0.0


@dataclass
class ProcessRecord:
    metrics: ProcessMetrics = field(default_factory=ProcessMetrics)
    cpu_samples: deque = field(default_factory=lambda: deque(maxlen=100))
    io_samples: deque = field(default_factory=lambda: deque(maxlen=100))
    wake_times: deque = field(default_factory=lambda: deque(maxlen=50))
    behavior: ProcessBehavior = ProcessBehavior.UNKNOWN
    predicted_next_wake: Optional[float] = None
    suggested_priority: int = 5
    suggested_quantum: int = 10


class ProcessTracker:
    def __init__(self):
        self._records: dict[int, ProcessRecord] = {}
        self._global_stats = {
            "total_context_switches": 0,
            "total_cpu_time_ms": 0.0,
            "total_io_time_ms": 0.0,
            "tracked_processes": 0,
        }

    def track(self, pid: int, name: str = "", cpu_ms: float = 0.0,
              io_ms: float = 0.0, sleeping: bool = False,
              context_switch: bool = False, priority: int = 5,
              time_slice_used_pct: float = 0.0) -> ProcessRecord:
        if pid not in self._records:
            self._records[pid] = ProcessRecord(
                metrics=ProcessMetrics(pid=pid, name=name)
            )
            self._global_stats["tracked_processes"] = len(self._records)

        rec = self._records[pid]
        m = rec.metrics
        m.name = name or m.name
        m.cpu_time_ms += cpu_ms
        m.io_wait_ms += io_ms
        m.total_runtime_ms += cpu_ms + io_ms
        m.last_seen = time.time()
        m.priority = priority
        m.time_slice_used_pct = time_slice_used_pct

        if context_switch:
            m.context_switches += 1
            self._global_stats["total_context_switches"] += 1

        if sleeping:
            m.sleep_count += 1
            rec.wake_times.append(time.time())

        rec.cpu_samples.append(cpu_ms)
        rec.io_samples.append(io_ms)

        self._global_stats["total_cpu_time_ms"] += cpu_ms
        self._global_stats["total_io_time_ms"] += io_ms

        rec.behavior = self._classify_behavior(rec)
        return rec

    def _classify_behavior(self, rec: ProcessRecord) -> ProcessBehavior:
        cpu = list(rec.cpu_samples)
        io = list(rec.io_samples)
        if not cpu:
            return ProcessBehavior.UNKNOWN

        recent_cpu = cpu[-10:] if len(cpu) >= 10 else cpu
        recent_io = io[-10:] if len(io) >= 10 else io

        avg_cpu = sum(recent_cpu) / len(recent_cpu) if recent_cpu else 0
        avg_io = sum(recent_io) / len(recent_io) if recent_io else 0
        total = avg_cpu + avg_io

        if total == 0:
            return ProcessBehavior.IDLE

        cpu_ratio = avg_cpu / total
        io_ratio = avg_io / total

        sleep_freq = len(rec.wake_times) / max(rec.metrics.total_runtime_ms / 1000, 1)

        if io_ratio > 0.7:
            return ProcessBehavior.IO_BOUND
        if cpu_ratio > 0.8 and sleep_freq < 1.0:
            return ProcessBehavior.CPU_BOUND
        if sleep_freq > 5.0:
            return ProcessBehavior.INTERACTIVE
        if avg_cpu > 10 and avg_io > 10:
            return ProcessBehavior.BATCH
        return ProcessBehavior.UNKNOWN

    def get_record(self, pid: int) -> Optional[ProcessRecord]:
        return self._records.get(pid)

    def get_all_records(self) -> dict[int, ProcessRecord]:
        return dict(self._records)

    def get_behavior_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for rec in self._records.values():
            b = rec.behavior.value
            counts[b] = counts.get(b, 0) + 1
        return counts

    def get_global_stats(self) -> dict:
        return dict(self._global_stats)

    def cleanup_stale(self, max_age_seconds: float = 300.0) -> int:
        now = time.time()
        stale = [pid for pid, rec in self._records.items()
                 if now - rec.metrics.last_seen > max_age_seconds]
        for pid in stale:
            del self._records[pid]
        self._global_stats["tracked_processes"] = len(self._records)
        return len(stale)
