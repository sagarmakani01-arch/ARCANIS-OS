"""Error reporting and diagnostic utilities."""

import sys
import traceback
from dataclasses import dataclass, field
from typing import List, Optional


class BuildError(Exception):
    def __init__(self, message: str, target: str = None, file: str = None, line: int = None):
        self.message = message
        self.target = target
        self.file = file
        self.line = line
        super().__init__(self.format())

    def format(self) -> str:
        parts = []
        if self.file:
            parts.append(f"[{self.file}")
            if self.line:
                parts.append(f":{self.line}")
            parts.append("] ")
        if self.target:
            parts.append(f"({self.target}) ")
        parts.append(self.message)
        return "".join(parts)


class CompilationError(BuildError):
    def __init__(self, message: str, target: str = None, file: str = None, line: int = None, code: str = None):
        self.code = code
        super().__init__(message, target, file, line)

    def format(self) -> str:
        parts = []
        if self.file:
            parts.append(f"[{self.file}")
            if self.line:
                parts.append(f":{self.line}")
            parts.append("] ")
        if self.target:
            parts.append(f"({self.target}) ")
        if self.code:
            parts.append(f"[{self.code}] ")
        parts.append(self.message)
        return "".join(parts)


class DependencyError(BuildError):
    def __init__(self, message: str, target: str = None, missing_dep: str = None):
        super().__init__(message, target)
        self.missing_dep = missing_dep


class ConfigError(BuildError):
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


@dataclass
class Diagnostic:
    level: str  # error, warning, info
    message: str
    target: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    code: Optional[str] = None

    def __str__(self):
        parts = []
        if self.file:
            parts.append(self.file)
            if self.line is not None:
                parts.append(f"({self.line}")
                if self.column is not None:
                    parts.append(f",{self.column}")
                parts.append(")")
            parts.append(": ")
        parts.append(f"[{self.level.upper()}]")
        if self.code:
            parts.append(f" {self.code}")
        parts.append(f": {self.message}")
        return "".join(parts)


class ErrorReporter:
    def __init__(self, verbose: bool = False):
        self.diagnostics: List[Diagnostic] = []
        self.verbose = verbose
        self._error_count = 0
        self._warning_count = 0

    def error(self, message: str, target: str = None, file: str = None, line: int = None, code: str = None):
        diag = Diagnostic("error", message, target, file, line, None, code)
        self.diagnostics.append(diag)
        self._error_count += 1
        print(diag, file=sys.stderr)

    def warning(self, message: str, target: str = None, file: str = None, line: int = None, code: str = None):
        diag = Diagnostic("warning", message, target, file, line, None, code)
        self.diagnostics.append(diag)
        self._warning_count += 1
        if self.verbose:
            print(diag, file=sys.stderr)

    def info(self, message: str, target: str = None):
        diag = Diagnostic("info", message, target)
        self.diagnostics.append(diag)
        if self.verbose:
            print(diag)

    def has_errors(self) -> bool:
        return self._error_count > 0

    def summary(self) -> str:
        return f"Build: {self._error_count} error(s), {self._warning_count} warning(s)"

    def print_summary(self):
        print(f"\n{self.summary()}")

    @staticmethod
    def format_exception(e: Exception) -> str:
        return "".join(traceback.format_exception(type(e), e, e.__traceback__))
