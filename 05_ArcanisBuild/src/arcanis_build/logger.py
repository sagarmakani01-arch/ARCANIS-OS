"""Build logging - structured logging with file and console output."""

import os
import sys
import json
from datetime import datetime, timezone
from typing import Optional, TextIO


class LogEntry:
    def __init__(self, level: str, message: str, target: str = None, phase: str = None):
        self.timestamp = datetime.now(timezone.utc)
        self.level = level
        self.message = message
        self.target = target
        self.phase = phase

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "target": self.target,
            "phase": self.phase,
        }

    def format_console(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        parts = [f"[{ts}]"]
        if self.target:
            parts.append(f"[{self.target}]")
        parts.append(f"[{self.level.upper()}]")
        parts.append(self.message)
        return " ".join(parts)


class BuildLogger:
    def __init__(self, log_dir: str = "build/logs", verbose: bool = False):
        self.log_dir = log_dir
        self.verbose = verbose
        self._entries: list[LogEntry] = []
        self._log_file: Optional[TextIO] = None
        self._phase_start_time: Optional[datetime] = None
        self._current_phase: Optional[str] = None

    def start_phase(self, phase: str):
        self._current_phase = phase
        self._phase_start_time = datetime.now(timezone.utc)
        self.info(f"Starting phase: {phase}")

    def end_phase(self):
        if self._current_phase and self._phase_start_time:
            elapsed = (datetime.now(timezone.utc) - self._phase_start_time).total_seconds()
            self.info(f"Completed phase: {self._current_phase} ({elapsed:.2f}s)")
        self._current_phase = None
        self._phase_start_time = None

    def log(self, level: str, message: str, target: str = None):
        entry = LogEntry(level, message, target, self._current_phase)
        self._entries.append(entry)

        if self._log_file:
            self._log_file.write(json.dumps(entry.to_dict()) + "\n")
            self._log_file.flush()

        if self.verbose or level in ("error", "warning"):
            print(entry.format_console())

    def info(self, message: str, target: str = None):
        self.log("info", message, target)

    def warn(self, message: str, target: str = None):
        self.log("warning", message, target)

    def error(self, message: str, target: str = None):
        self.log("error", message, target)

    def debug(self, message: str, target: str = None):
        if self.verbose:
            self.log("debug", message, target)

    def open_log(self, build_id: str = None):
        os.makedirs(self.log_dir, exist_ok=True)
        if build_id is None:
            build_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(self.log_dir, f"build_{build_id}.jsonl")
        self._log_file = open(log_path, "w", encoding="utf-8")
        self.info(f"Log opened: {log_path}")
        return log_path

    def close_log(self):
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    def get_entries(self, level: str = None) -> list[LogEntry]:
        if level:
            return [e for e in self._entries if e.level == level]
        return self._entries

    def export(self, format: str = "json") -> str:
        if format == "json":
            return json.dumps([e.to_dict() for e in self._entries], indent=2)
        elif format == "text":
            return "\n".join(e.format_console() for e in self._entries)
        raise ValueError(f"Unsupported export format: {format}")

    def summary(self) -> dict:
        return {
            "total_entries": len(self._entries),
            "errors": len([e for e in self._entries if e.level == "error"]),
            "warnings": len([e for e in self._entries if e.level == "warning"]),
            "info": len([e for e in self._entries if e.level == "info"]),
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_log()
