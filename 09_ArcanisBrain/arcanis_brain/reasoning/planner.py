from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timezone
import json


@dataclass
class Plan:
    objective: str
    steps: list[dict] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    estimated_steps: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Planner:
    def __init__(self, brain):
        self.brain = brain

    async def create_plan(self, task, context: dict) -> Plan:
        task_type = self._classify(task.objective)
        steps = self._decompose(task.objective, task_type, context)
        plan = Plan(
            objective=task.objective,
            steps=steps,
            dependencies=self._build_dependencies(steps),
            estimated_steps=len(steps),
        )
        return plan

    def _classify(self, objective: str) -> str:
        objective_lower = objective.lower()
        if any(w in objective_lower for w in ["search", "find", "lookup", "retrieve"]):
            return "retrieval"
        if any(w in objective_lower for w in ["analyze", "compare", "evaluate"]):
            return "analysis"
        if any(w in objective_lower for w in ["create", "build", "generate", "write"]):
            return "generation"
        if any(w in objective_lower for w in ["solve", "calculate", "compute"]):
            return "computation"
        return "general"

    def _decompose(self, objective: str, task_type: str, context: dict) -> list[dict]:
        steps = [{
            "step_id": "step_1",
            "action": "understand",
            "description": f"Analyze the request: {objective}",
            "tool": "reason",
            "dependencies": [],
        }, {
            "step_id": "step_2",
            "action": "retrieve",
            "description": "Gather relevant context and knowledge",
            "tool": "memory",
            "dependencies": ["step_1"],
        }, {
            "step_id": "step_3",
            "action": "process",
            "description": f"Execute {task_type} task",
            "tool": task_type,
            "dependencies": ["step_2"],
        }, {
            "step_id": "step_4",
            "action": "respond",
            "description": "Formulate final response",
            "tool": "compose",
            "dependencies": ["step_3"],
        }]
        return steps

    def _build_dependencies(self, steps: list[dict]) -> dict[str, list[str]]:
        deps = {}
        for step in steps:
            deps[step["step_id"]] = step.get("dependencies", [])
        return deps

    def evaluate(self, step: dict, result: Any) -> dict:
        return {"step": step["step_id"], "success": result is not None, "result": result}
