"""ArcanisShell — activity log.

Immutable, append-only record of every action for audit and accountability.
Entries are persisted as JSON lines so they can be inspected or streamed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from ..types import ActivityEntry, CommandSource, RiskLevel


class ActivityLog:
    """Append-only audit log of shell activity."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._buffer: list[ActivityEntry] = []

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def record(
        self,
        source: CommandSource,
        action: str,
        risk: RiskLevel,
        approved: bool,
        outcome: str,
        detail: str = "",
    ) -> ActivityEntry:
        entry = ActivityEntry(
            timestamp=self._now(),
            source=source,
            action=action,
            risk=risk,
            approved=approved,
            outcome=outcome,
            detail=detail,
        )
        self._buffer.append(entry)
        if self.path is not None:
            self._append_to_disk(entry)
        return entry

    def _append_to_disk(self, entry: ActivityEntry) -> None:
        assert self.path is not None
        line = json.dumps(entry.__dict__, default=str)
        with self.path.open("a", encoding="utf-8") as handle:  # noqa: PTH123
            handle.write(line + "\n")

    def recent(self, limit: int = 50) -> list[ActivityEntry]:
        return self._buffer[-limit:]

    def __iter__(self) -> Iterator[ActivityEntry]:
        return iter(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)
