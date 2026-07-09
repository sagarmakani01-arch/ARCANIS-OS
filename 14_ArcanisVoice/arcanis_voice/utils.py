"""Shared utilities: logging, timing, events."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("arcanis_voice")


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )


@dataclass
class Timing:
    """Track stage latencies for low-latency monitoring."""

    stages: dict[str, float] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.stages is None:
            self.stages = {}

    def mark(self, name: str) -> float:
        t = time.perf_counter()
        self.stages[name] = t
        return t

    def delta(self, start: str, end: str) -> float:
        return self.stages.get(end, 0) - self.stages.get(start, 0)


class EventBus:
    """Minimal synchronous pub/sub used for inter-stage signaling."""

    def __init__(self) -> None:
        self._subs: dict[str, list[callable]] = {}

    def subscribe(self, topic: str, cb: callable) -> None:
        self._subs.setdefault(topic, []).append(cb)

    def publish(self, topic: str, payload: Any = None) -> None:
        for cb in self._subs.get(topic, []):
            try:
                cb(payload)
            except Exception as exc:  # noqa: BLE001
                logger.warning("event handler for %s failed: %s", topic, exc)
