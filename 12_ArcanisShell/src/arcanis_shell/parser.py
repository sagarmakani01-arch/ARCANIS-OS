"""ArcanisShell — command parser.

Parses a raw line of input into either:
  * a TraditionalCommand (named command + args + flags), or
  * a NaturalLanguageRequest (free text that should be handled by the AI).

Routing heuristics:
  * Input starting with a known command name (or a registered alias) and
    not wrapped in quotes is treated as traditional.
  * Everything else is treated as natural language.
A leading `:` or `ai ` prefix forces natural-language routing.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Optional

from .errors import ParseError


@dataclass
class TraditionalCommand:
    """A parsed traditional (explicit) shell command."""

    name: str
    args: list[str] = field(default_factory=list)
    flags: dict[str, Optional[str]] = field(default_factory=dict)
    raw: str = ""

    def as_shell_string(self) -> str:
        return self.raw


@dataclass
class NaturalLanguageRequest:
    """A natural-language request to be processed by the AI interface."""

    text: str
    raw: str = ""

    def as_shell_string(self) -> str:
        return self.raw


ParsedInput = TraditionalCommand | NaturalLanguageRequest


class CommandParser:
    """Routes and tokenizes raw user input."""

    def __init__(
        self, known_commands: Optional[set[str]] = None, aliases: Optional[dict[str, str]] = None
    ) -> None:
        self.known_commands = known_commands or set()
        self.aliases = aliases or {}

    def register(self, name: str) -> None:
        self.known_commands.add(name)

    def _split_flags(self, tokens: list[str]) -> tuple[list[str], dict[str, Optional[str]]]:
        args: list[str] = []
        flags: dict[str, Optional[str]] = {}
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.startswith("--"):
                key = tok[2:]
                if "=" in key:
                    k, v = key.split("=", 1)
                    flags[k] = v
                elif i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    flags[key] = tokens[i + 1]
                    i += 1
                else:
                    flags[key] = None
            elif tok.startswith("-") and len(tok) > 1:
                key = tok[1:]
                if len(key) == 1:
                    # Single-letter short flag is boolean; never consumes the
                    # following token as a value (e.g. `rm -r sub`).
                    flags[key] = None
                elif i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    flags[key] = tokens[i + 1]
                    i += 1
                else:
                    flags[key] = None
            else:
                args.append(tok)
            i += 1
        return args, flags

    def parse(self, raw: str) -> ParsedInput:
        stripped = raw.replace("\ufeff", "").strip()
        if not stripped:
            raise ParseError(raw, "empty input")

        lowered = stripped.lower()
        if lowered.startswith("ai ") or stripped.startswith(":"):
            text = stripped[3:] if lowered.startswith("ai ") else stripped[1:]
            return NaturalLanguageRequest(text=text.strip(), raw=raw)

        try:
            tokens = shlex.split(stripped)
        except ValueError as exc:  # unbalanced quotes
            raise ParseError(raw, str(exc)) from exc

        if not tokens:
            raise ParseError(raw, "empty input")

        head = tokens[0]
        name = self.aliases.get(head, head)

        if name in self.known_commands:
            args, flags = self._split_flags(tokens[1:])
            return TraditionalCommand(name=name, args=args, flags=flags, raw=raw)

        # Heuristic: multi-word input without a known leading verb is most
        # likely a natural-language request.
        if " " in stripped:
            return NaturalLanguageRequest(text=stripped, raw=raw)

        raise ParseError(raw, f"unrecognized command or phrase: {head}")
