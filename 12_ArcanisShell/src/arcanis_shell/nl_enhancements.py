from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ShellSuggestion:
    command: str
    description: str
    confidence: float = 0.8
    category: str = "general"
    context: str = ""


@dataclass
class CommandHistory:
    command: str
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    duration_ms: float = 0.0
    directory: str = ""


class NLShellBeta:
    def __init__(self):
        self._history: list[CommandHistory] = []
        self._learned_patterns: dict[str, list[str]] = {}
        self._command_descriptions: dict[str, str] = {
            "ls": "List directory contents",
            "cd": "Change current directory",
            "cat": "Display file contents",
            "mkdir": "Create directories",
            "rm": "Remove files or directories",
            "cp": "Copy files or directories",
            "mv": "Move or rename files",
            "find": "Search for files",
            "tree": "Display directory tree",
            "ps": "List running processes",
            "kill": "Terminate a process",
            "sysinfo": "Show system information",
            "pwd": "Print working directory",
            "echo": "Print text to output",
            "run": "Execute an automation script",
            "ai": "AI-powered natural language command",
        }

    def record_command(self, command: str, success: bool = True,
                       duration_ms: float = 0.0, directory: str = "") -> None:
        self._history.append(CommandHistory(
            command=command, success=success,
            duration_ms=duration_ms, directory=directory,
        ))
        self._learn_pattern(command)

    def _learn_pattern(self, command: str) -> None:
        parts = command.strip().split()
        if not parts:
            return
        base = parts[0]
        if base not in self._learned_patterns:
            self._learned_patterns[base] = []
        rest = " ".join(parts[1:])
        if rest and rest not in self._learned_patterns[base]:
            self._learned_patterns[base].append(rest)

    def suggest(self, context: Optional[dict[str, Any]] = None) -> list[ShellSuggestion]:
        suggestions: list[ShellSuggestion] = []
        ctx = context or {}
        cwd = ctx.get("cwd", "")
        last_commands = [h.command for h in self._history[-10:]]

        for cmd, desc in self._command_descriptions.items():
            if cmd not in [c.split()[0] for c in last_commands]:
                suggestions.append(ShellSuggestion(
                    command=cmd, description=desc, confidence=0.6,
                    category="discovery",
                ))

        recent_files = ctx.get("recent_files", [])
        if recent_files:
            suggestions.append(ShellSuggestion(
                command=f"cat {recent_files[0]}",
                description=f"View recently accessed file: {recent_files[0]}",
                confidence=0.85, category="recent",
            ))

        for base, args_list in self._learned_patterns.items():
            for args in args_list[:3]:
                suggestions.append(ShellSuggestion(
                    command=f"{base} {args}",
                    description=f"Frequently used: {base} {args}",
                    confidence=0.7, category="learned",
                ))

        if not last_commands:
            suggestions.append(ShellSuggestion(
                command="sysinfo",
                description="Check system status",
                confidence=0.5, category="starter",
            ))
        elif last_commands[-1].startswith("mkdir"):
            dirname = last_commands[-1].split()[-1] if len(last_commands[-1].split()) > 1 else "new_dir"
            suggestions.append(ShellSuggestion(
                command=f"cd {dirname}",
                description=f"Enter the newly created directory",
                confidence=0.9, category="sequential",
            ))

        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:10]

    def explain_command(self, command: str) -> str:
        parts = command.strip().split()
        if not parts:
            return "Empty command."
        base = parts[0]
        desc = self._command_descriptions.get(base, f"Unknown command: {base}")

        risk_map = {
            "rm": "DANGER: Irreversible file deletion. Use with extreme caution.",
            "kill": "DANGER: Terminates a running process. May cause data loss.",
            "mv": "CAUTION: Moves or renames files. Can overwrite existing files.",
            "cp": "CAUTION: Copies files. May overwrite existing files.",
            "mkdir": "SAFE: Creates new directories.",
            "ls": "SAFE: Lists directory contents, no changes made.",
            "cat": "SAFE: Reads and displays file contents.",
            "find": "SAFE: Searches for files without modifying anything.",
            "ps": "SAFE: Shows running processes.",
            "sysinfo": "SAFE: Displays system information.",
        }
        risk = risk_map.get(base, "RISK: Unknown — verify before executing.")

        usage_map = {
            "rm": "Usage: rm [-r] <path>  (-r for directories)",
            "find": "Usage: find [--name <pattern>] [path]",
            "cat": "Usage: cat <file>",
            "mkdir": "Usage: mkdir [-p] <path>  (-p for nested dirs)",
        }
        usage = usage_map.get(base, "")

        parts_out = [f"{desc}"]
        parts_out.append(f"Risk: {risk}")
        if usage:
            parts_out.append(usage)
        return "\n".join(parts_out)

    def get_history(self, limit: int = 20) -> list[CommandHistory]:
        return self._history[-limit:]

    def get_stats(self) -> dict:
        total = len(self._history)
        success = sum(1 for h in self._history if h.success)
        return {
            "total_commands": total,
            "successful": success,
            "success_rate": success / max(total, 1),
            "unique_commands": len(self._learned_patterns),
            "avg_duration_ms": sum(h.duration_ms for h in self._history) / max(total, 1),
        }
