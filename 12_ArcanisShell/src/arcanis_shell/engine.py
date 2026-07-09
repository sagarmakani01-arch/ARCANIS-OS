"""ArcanisShell — shell engine.

The orchestrator. It owns the parser, command registry, AI interface,
permission policy, sandbox, and activity log. The engine exposes a single
`execute(raw_input)` method used by both the interactive REPL and tests.

Flow for traditional commands:
  parse -> permission check -> sandbox check -> run -> log

Flow for natural-language requests:
  parse -> AI.understand -> build plan -> request approval -> run steps
  (each step re-checked by permission/sandbox) -> log
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from .ai_interface import AIInterface
from .commands import CommandContext, Registry, build_registry
from .config import ShellConfig
from .errors import (
    AIUnavailableError,
    ParseError,
    PermissionDeniedError,
    PlanRejectedError,
    SandboxViolationError,
)
from .integration import load_agents, load_brain, load_os
from .parser import CommandParser
from .security import ActivityLog, PermissionPolicy, Sandbox
from .types import CommandResult, CommandSource, ExecutionPlan, RiskLevel


class ShellEngine:
    """Core runtime of ArcanisShell."""

    def __init__(
        self,
        config: Optional[ShellConfig] = None,
        registry: Optional[Registry] = None,
        policy: Optional[PermissionPolicy] = None,
        ai: Optional[AIInterface] = None,
        approval_fn: Optional[Callable[[ExecutionPlan], bool]] = None,
    ) -> None:
        self.config = config or ShellConfig.default()
        self.registry = registry or build_registry()
        self.parser = CommandParser(known_commands=self.registry.names())
        self.policy = policy or PermissionPolicy()
        self.sandbox = Sandbox(
            root=self.config.sandbox_root,
            allow_write=self.config.allow_sandbox_writes,
            allow_network=self.config.enable_network,
        )
        self.log = ActivityLog(path=self.config.log_file)
        self.cwd: Path = self.config.sandbox_root.resolve()
        self.ai = ai or self._default_ai()
        self.approval_fn = approval_fn or self._default_approval
        self._history: list[str] = []

    def _default_ai(self) -> AIInterface:
        brain = load_brain(self.config.ai_backend)
        agents = load_agents()
        os_adapter = load_os()
        return AIInterface(brain, agents, os_adapter, self.config.ai_backend)

    @staticmethod
    def _default_approval(plan: ExecutionPlan) -> bool:
        import sys

        print(f"\nPlan: {plan.intent}")
        print(f"  {plan.summary}")
        for step in plan.steps:
            print(f"  [{step.index}] ({step.risk.value}) {step.description}")
            print(f"       $ {step.command}")
        try:
            if not (sys.stdin is not None and sys.stdin.isatty()):
                # Non-interactive context (piped input / -c mode): do not
                # silently approve AI plans. Reject so the caller can decide.
                print("Approve this plan? [y/N] (non-interactive: rejected)")
                return False
            answer = input("Approve this plan? [y/N] ").strip().lower()
            return answer in ("y", "yes")
        except EOFError:
            print("Approve this plan? [y/N] (non-interactive: rejected)")
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, raw: str) -> CommandResult:
        self._history.append(raw)
        try:
            parsed = self.parser.parse(raw)
        except ParseError as exc:
            self.log.record(
                CommandSource.TRADITIONAL, raw, RiskLevel.SAFE, False, "parse_error", str(exc)
            )
            return CommandResult(success=False, stderr=str(exc), exit_code=2)

        if hasattr(parsed, "text"):
            return self._execute_nl(parsed.text, raw)

        return self._execute_traditional(parsed.name, parsed.args, parsed.flags, raw)

    # ------------------------------------------------------------------
    # Traditional execution
    # ------------------------------------------------------------------

    def _execute_traditional(
        self, name: str, args: list[str], flags: dict[str, Optional[str]], raw: str
    ) -> CommandResult:
        cmd = self.registry.get(name)
        if cmd is None:
            self.log.record(
                CommandSource.TRADITIONAL, raw, RiskLevel.SAFE, False, "unknown_command"
            )
            return CommandResult(success=False, stderr=f"unknown command: {name}", exit_code=127)

        ctx = CommandContext(
            cwd=self.cwd,
            sandbox=self.sandbox,
            source=CommandSource.TRADITIONAL,
            registry=self.registry,
        )

        try:
            self.policy.check(name, cmd.risk, CommandSource.TRADITIONAL)
            needs_approval = self.policy.needs_approval(name, cmd.risk, CommandSource.TRADITIONAL)
        except PermissionDeniedError as exc:
            self.log.record(CommandSource.TRADITIONAL, raw, cmd.risk, False, "denied", str(exc))
            return CommandResult(success=False, stderr=str(exc), exit_code=1)

        if needs_approval:
            plan = ExecutionPlan(
                intent=name,
                summary=cmd.description,
                steps=[
                    __import__("arcanis_shell.types", fromlist=["PlanStep"]).PlanStep(
                        index=0, description=cmd.description, command=raw, risk=cmd.risk
                    )
                ],
            )
            if not self.approval_fn(plan):
                self.log.record(CommandSource.TRADITIONAL, raw, cmd.risk, False, "rejected")
                return CommandResult(success=False, stderr="action rejected by user", exit_code=1)
            self.log.record(CommandSource.TRADITIONAL, raw, cmd.risk, True, "approved")

        try:
            self.sandbox.guard_subprocess(CommandSource.TRADITIONAL, cmd.risk)
            result = cmd.fn(args, flags, ctx)
        except SandboxViolationError as exc:
            self.log.record(
                CommandSource.TRADITIONAL, raw, cmd.risk, True, "sandbox_violation", str(exc)
            )
            return CommandResult(success=False, stderr=str(exc), exit_code=1)
        except Exception as exc:  # noqa: BLE001
            self.log.record(CommandSource.TRADITIONAL, raw, cmd.risk, True, "error", str(exc))
            return CommandResult(success=False, stderr=str(exc), exit_code=1)

        self.cwd = ctx.cwd
        self.log.record(
            CommandSource.TRADITIONAL, raw, cmd.risk, True, "ok" if result.success else "failed"
        )
        return result

    # ------------------------------------------------------------------
    # Natural-language execution
    # ------------------------------------------------------------------

    def _execute_nl(self, text: str, raw: str) -> CommandResult:
        context = {"cwd": str(self.cwd), "sandbox_root": str(self.sandbox.root)}
        try:
            plan = self.ai.understand(text, context)
        except AIUnavailableError as exc:
            self.log.record(
                CommandSource.AI_GENERATED, raw, RiskLevel.LOW, False, "ai_unavailable", str(exc)
            )
            return CommandResult(success=False, stderr=str(exc), exit_code=3)

        self.log.record(
            CommandSource.AI_GENERATED, raw, plan.max_risk, False, "planned", plan.summary
        )

        if plan.requires_approval and not self.approval_fn(plan):
            self.log.record(CommandSource.AI_GENERATED, raw, plan.max_risk, False, "rejected")
            raise PlanRejectedError(len(plan.steps))

        ctx = CommandContext(
            cwd=self.cwd,
            sandbox=self.sandbox,
            source=CommandSource.AI_GENERATED,
            registry=self.registry,
        )
        outputs: list[str] = []
        for step in plan.steps:
            cmd_name = step.command.strip().split()[0] if step.command.strip() else ""
            cmd = self.registry.get(cmd_name)
            if cmd is None:
                self.log.record(
                    CommandSource.AI_GENERATED, step.command, step.risk, True, "unknown_step"
                )
                return CommandResult(
                    success=False, stderr=f"plan step unknown: {cmd_name}", exit_code=127
                )
            try:
                self.policy.check(cmd_name, step.risk, CommandSource.AI_GENERATED)
                self.sandbox.guard_subprocess(CommandSource.AI_GENERATED, step.risk)
                result = cmd.fn(self._step_args(step.command), self._step_flags(step.command), ctx)
            except (PermissionDeniedError, SandboxViolationError) as exc:
                self.log.record(
                    CommandSource.AI_GENERATED, step.command, step.risk, True, "blocked", str(exc)
                )
                return CommandResult(success=False, stderr=str(exc), exit_code=1)
            if not result.success:
                self.log.record(
                    CommandSource.AI_GENERATED,
                    step.command,
                    step.risk,
                    True,
                    "step_failed",
                    result.stderr,
                )
                return CommandResult(
                    success=False, stderr=f"step {step.index} failed: {result.stderr}", exit_code=1
                )
            if result.stdout:
                outputs.append(result.stdout)

        self.cwd = ctx.cwd
        self.log.record(CommandSource.AI_GENERATED, raw, plan.max_risk, True, "executed")
        return CommandResult(success=True, stdout="\n".join(outputs))

    @staticmethod
    def _step_args(command: str) -> list[str]:
        import shlex

        tokens = shlex.split(command)
        args: list[str] = []
        for tok in tokens[1:]:
            if tok.startswith("-"):
                continue
            args.append(tok)
        return args

    @staticmethod
    def _step_flags(command: str) -> dict[str, Optional[str]]:
        import shlex

        tokens = shlex.split(command)
        flags: dict[str, Optional[str]] = {}
        for tok in tokens[1:]:
            if tok.startswith("--"):
                key = tok[2:]
                if "=" in key:
                    k, v = key.split("=", 1)
                    flags[k] = v
                else:
                    flags[key] = None
            elif tok.startswith("-"):
                flags[tok[1:]] = None
        return flags

    # ------------------------------------------------------------------
    # Convenience helpers used by REPL / tooling
    # ------------------------------------------------------------------

    def explain(self, command: str) -> str:
        exp = self.ai.explain(command)
        lines = [exp.summary]
        if exp.effects:
            lines.append("Effects:")
            lines.extend(f"  - {e}" for e in exp.effects)
        if exp.risks:
            lines.append("Risks:")
            lines.extend(f"  - {r}" for r in exp.risks)
        return "\n".join(lines)

    def suggest(self) -> list[str]:
        return self.ai.suggest({"cwd": str(self.cwd)})

    def generate_automation(self, request: str) -> str:
        return self.ai.generate_automation(request, {"cwd": str(self.cwd)})


def repl(engine: Optional[ShellEngine] = None) -> None:
    """Run the interactive read-eval-print loop."""
    eng = engine or ShellEngine()
    print("ArcanisShell 0.1.0 — type 'help' or prefix requests with 'ai '")
    while True:
        try:
            raw = input(f"{eng.config.prompt} ")
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break
        if raw.strip() in ("exit", "quit"):
            break
        if raw.strip() == "help":
            for cmd in sorted(eng.registry.all(), key=lambda c: c.name):
                print(f"  {cmd.name:8} {cmd.description}  [{cmd.risk.value}]")
            continue
        result = eng.execute(raw)
        if result.stdout:
            print(result.stdout)
        if not result.success and result.stderr:
            print(f"error: {result.stderr}")
