"""Arcanis Experiments — sandboxed environment for testing new features safely."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class ExperimentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ExperimentConfig:
    name: str = ""
    description: str = ""
    target_system: str = ""
    rollback_on_failure: bool = True
    timeout_seconds: float = 300.0
    variables: dict[str, Any] = field(default_factory=dict)
    pre_check: Optional[Callable] = None
    execute: Optional[Callable] = None
    validate: Optional[Callable] = None
    rollback: Optional[Callable] = None


@dataclass
class ExperimentResult:
    experiment_id: str = ""
    status: ExperimentStatus = ExperimentStatus.PENDING
    start_time: float = 0.0
    end_time: float = 0.0
    output: Any = None
    error: Optional[str] = None
    metrics: dict[str, Any] = field(default_factory=dict)


class ExperimentRunner:
    def __init__(self):
        self._experiments: dict[str, ExperimentConfig] = {}
        self._results: dict[str, ExperimentResult] = {}
        self._snapshots: dict[str, dict[str, Any]] = {}

    def register(self, config: ExperimentConfig) -> str:
        experiment_id = f"exp_{uuid.uuid4().hex[:12]}"
        self._experiments[experiment_id] = config
        return experiment_id

    def snapshot(self, experiment_id: str, state: dict[str, Any]) -> None:
        self._snapshots[experiment_id] = dict(state)

    def run(self, experiment_id: str) -> ExperimentResult:
        config = self._experiments.get(experiment_id)
        if not config:
            return ExperimentResult(experiment_id=experiment_id, status=ExperimentStatus.FAILED,
                                   error="Experiment not found")

        result = ExperimentResult(experiment_id=experiment_id, start_time=time.time())

        try:
            if config.pre_check and not config.pre_check():
                result.status = ExperimentStatus.FAILED
                result.error = "Pre-check failed"
                return result

            result.status = ExperimentStatus.RUNNING
            if config.execute:
                result.output = config.execute()

            if config.validate and not config.validate(result.output):
                raise ValueError("Validation failed")

            result.status = ExperimentStatus.COMPLETED

        except Exception as e:
            result.status = ExperimentStatus.FAILED
            result.error = str(e)
            if config.rollback_on_failure and config.rollback:
                try:
                    config.rollback(self._snapshots.get(experiment_id, {}))
                    result.status = ExperimentStatus.ROLLED_BACK
                except Exception as rb_err:
                    result.error = f"Rollback failed: {rb_err}"

        result.end_time = time.time()
        self._results[experiment_id] = result
        return result

    def get_result(self, experiment_id: str) -> Optional[ExperimentResult]:
        return self._results.get(experiment_id)

    def list_experiments(self) -> list[dict[str, Any]]:
        return [{"id": eid, "name": cfg.name, "status": self._results.get(eid, ExperimentResult()).status.value}
                for eid, cfg in self._experiments.items()]

    def get_stats(self) -> dict:
        statuses = {}
        for r in self._results.values():
            statuses[r.status.value] = statuses.get(r.status.value, 0) + 1
        return {
            "total_experiments": len(self._experiments),
            "total_runs": len(self._results),
            "status_breakdown": statuses,
        }
