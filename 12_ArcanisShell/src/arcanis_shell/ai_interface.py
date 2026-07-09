"""ArcanisShell — AI interface.

Wraps ArcanisBrain (via integration adapter) to provide:
  * Natural-language command understanding
  * Safe, reviewable plan generation
  * Command suggestions (based on current context)
  * Command explanations
  * Automation script generation

The interface is policy-aware: it never executes. It produces plans and
text that the ShellEngine reviews against permissions/sandbox before any
action is taken.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .errors import AIUnavailableError
from .integration import AgentsAdapter, BrainAdapter, OSAdapter
from .types import ExecutionPlan, PlanStep, RiskLevel


@dataclass
class Explanation:
    """Human-readable explanation of a command."""

    command: str
    summary: str
    effects: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


class AIInterface:
    """Natural-language front end for the shell."""

    def __init__(
        self,
        brain: BrainAdapter,
        agents: Optional[AgentsAdapter] = None,
        os_adapter: Optional[OSAdapter] = None,
        backend_name: str = "arcanis_brain",
    ) -> None:
        self.brain = brain
        self.agents = agents
        self.os = os_adapter
        self.backend_name = backend_name

    # ------------------------------------------------------------------
    # Core NL capabilities
    # ------------------------------------------------------------------

    def understand(self, request: str, context: dict[str, Any]) -> ExecutionPlan:
        """Turn a natural-language request into a reviewable plan."""
        try:
            resp = self.brain.understand(request, context)
        except Exception as exc:  # noqa: BLE001
            raise AIUnavailableError(self.backend_name, str(exc)) from exc

        steps = [
            PlanStep(
                index=i,
                description=s.get("description", ""),
                command=s.get("command", ""),
                risk=RiskLevel(s.get("risk", "low")),
                rationale=s.get("rationale", ""),
            )
            for i, s in enumerate(resp.plan_steps)
        ]
        plan = ExecutionPlan(
            intent=resp.intent,
            summary=resp.explanation,
            steps=steps,
            requires_approval=True,
        )
        return plan

    def explain(self, command: str) -> Explanation:
        """Explain what a given command does and its risks."""
        summary, effects, risks = self._static_explain(command)
        return Explanation(command=command, summary=summary, effects=effects, risks=risks)

    def suggest(self, context: dict[str, Any]) -> list[str]:
        """Suggest next commands given the current context."""
        cwd = context.get("cwd", ".")
        suggestions = [
            "ls  — list files in the current directory",
            "sysinfo  — show system information",
            f"tree {cwd}  — visualize the directory structure",
            "ai organize my project files  — let AI tidy this folder",
        ]
        return suggestions

    def generate_automation(self, request: str, context: dict[str, Any]) -> str:
        """Generate an .arc automation script from a request."""
        plan = self.understand(request, context)
        lines = ["# Auto-generated ArcanisShell automation", f"# Intent: {plan.intent}", ""]
        for step in plan.steps:
            lines.append(f"# {step.description}")
            lines.append(step.command)
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def delegate_to_agents(self, plan: ExecutionPlan) -> dict[str, Any]:
        """Hand execution of a plan to ArcanisAgents if available."""
        if self.agents is None:
            return {"status": "no_agents_backend"}
        return self.agents.delegate(
            {"intent": plan.intent, "steps": [s.model_dump() for s in plan.steps]}
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _static_explain(command: str) -> tuple[str, list[str], list[str]]:
        head = command.strip().split()[0] if command.strip() else ""
        table = {
            "rm": (
                "Remove files or directories.",
                ["Deletes the target permanently (unless recoverable)."],
                ["Irreversible data loss", "Use -r for directories"],
            ),
            "mv": (
                "Move or rename a file/directory.",
                ["Changes the file's location or name."],
                ["Overwrites destination if it exists"],
            ),
            "cp": (
                "Copy files or directories.",
                ["Creates a duplicate at the destination."],
                ["May overwrite existing files"],
            ),
            "mkdir": (
                "Create directories.",
                ["Adds new directories."],
                ["Fails if path exists (unless -p)"],
            ),
            "kill": (
                "Terminate a process.",
                ["Sends a termination signal to a PID."],
                ["Can disrupt running services"],
            ),
            "run": (
                "Execute an .arc automation script.",
                ["Runs each line as a command."],
                ["Executes multiple actions at once"],
            ),
        }
        if head in table:
            return table[head]
        return (
            f"Execute '{head}' as a traditional command.",
            ["Runs the command in the sandbox."],
            ["Behavior depends on the command"],
        )
