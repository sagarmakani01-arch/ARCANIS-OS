"""AI workflow capabilities: generate, optimize, failure detection."""

from __future__ import annotations

import re
from typing import Any

from arcanis_automation.core.models import (
    Workflow,
    Step,
    Trigger,
    TriggerType,
    ActionSpec,
    Schedule,
)
from arcanis_automation.ai.providers import BaseAIProvider, LocalHeuristicProvider


class WorkflowAI:
    """High-level AI features layered on top of an AI provider."""

    def __init__(self, provider: BaseAIProvider):
        self.provider = provider

    # ------------------------------------------------------------------
    # Generate a workflow from a natural-language description
    # ------------------------------------------------------------------
    def generate(self, description: str, owner: str = "ai") -> Workflow:
        prompt = (
            "You are ArcanisAutomation. Convert the user request into a JSON "
            "workflow with keys: name, description, triggers[], steps[] where "
            "each step has id, name, action{action,params}, run_after[]. "
            "Use action kinds like file.organize, app.launch, data.transform, "
            "research.query, notify. Request:\n" + description
        )
        raw = self.provider.complete(prompt)
        parsed = self._extract_json(raw)
        if parsed:
            wf = Workflow.from_dict(parsed)
        else:
            # Heuristic fallback so generation always returns something useful.
            wf = self._heuristic_generate(description)
        wf.owner = owner
        return wf

    # ------------------------------------------------------------------
    # Optimize an existing workflow
    # ------------------------------------------------------------------
    def optimize(self, workflow: Workflow) -> Workflow:
        prompt = (
            "Optimize this workflow for fewer steps and better chaining. "
            "Return improved JSON. Current:\n" + str(workflow.to_dict())
        )
        raw = self.provider.complete(prompt)
        parsed = self._extract_json(raw)
        if parsed:
            optimized = Workflow.from_dict(parsed)
            optimized.id = workflow.id
            return optimized
        return self._heuristic_optimize(workflow)

    def suggest_optimizations(self, workflow: Workflow) -> list[str]:
        suggestions: list[str] = []
        ids = {s.id for s in workflow.steps}
        for s in workflow.steps:
            for dep in s.run_after:
                if dep not in ids:
                    suggestions.append(f"Step '{s.id}' references missing step '{dep}'.")
        if not workflow.triggers and not workflow.schedule:
            suggestions.append("No trigger or schedule: workflow can only run manually.")
        if any(s.on_failure == "stop" for s in workflow.steps) and len(workflow.steps) > 3:
            suggestions.append("Many steps stop on failure; consider 'continue' for resilience.")
        return suggestions

    # ------------------------------------------------------------------
    # Failure detection / health analysis
    # ------------------------------------------------------------------
    def detect_failures(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        failed = [r for r in results if not r.get("success", True)]
        return {
            "total": len(results),
            "failed": len(failed),
            "healthy": len(failed) == 0,
            "failures": [
                {"step_id": r.get("step_id"), "error": r.get("error")}
                for r in failed
            ],
            "diagnosis": self._diagnose(failed) if failed else "No failures detected.",
        }

    def _diagnose(self, failed: list[dict[str, Any]]) -> str:
        reasons = [str(r.get("error", "")) for r in failed]
        prompt = (
            "Diagnose why these automation steps failed and suggest fixes:\n"
            + "\n".join(reasons)
        )
        return self.provider.complete(prompt)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            import json
            return json.loads(match.group(0))
        except Exception:
            return None

    @staticmethod
    def _heuristic_generate(description: str) -> Workflow:
        desc = description.lower()
        steps: list[Step] = []
        idx = 0
        if "organize" in desc or "sort" in desc:
            steps.append(Step(id="s%d" % idx, name="Organize files",
                              action=ActionSpec("file.organize",
                                                {"source": ".", "by_extension": True})))
            idx += 1
        if "launch" in desc or "open" in desc and "app" in desc:
            steps.append(Step(id="s%d" % idx, name="Launch application",
                              action=ActionSpec("app.launch", {"command": "notepad"}),
                              run_after=[steps[-1].id] if steps else []))
            idx += 1
        if "research" in desc or "search" in desc:
            steps.append(Step(id="s%d" % idx, name="Research",
                              action=ActionSpec("research.query",
                                                {"query": description})))
            idx += 1
        if "notify" in desc or "alert" in desc:
            steps.append(Step(id="s%d" % idx, name="Notify",
                              action=ActionSpec("notify",
                                                {"message": "Workflow complete"}),
                              run_after=[s.id for s in steps]))
            idx += 1
        if not steps:
            steps.append(Step(id="s0", name="Notify",
                              action=ActionSpec("notify",
                                                {"message": description})))
        return Workflow(
            id="wf_ai_" + str(abs(hash(description)) % 10**8),
            name="Generated: " + description[:40],
            description=description,
            triggers=[Trigger(TriggerType.MANUAL)],
            steps=steps,
        )

    @staticmethod
    def _heuristic_optimize(workflow: Workflow) -> Workflow:
        # Remove steps with no action params that equal a prior step.
        seen = set()
        pruned = []
        for s in workflow.steps:
            key = (s.action.action, tuple(sorted(s.action.params.items())))
            if key in seen:
                continue
            seen.add(key)
            pruned.append(s)
        workflow.steps = pruned
        return workflow
