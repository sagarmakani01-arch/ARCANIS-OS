"""ArcanisShell — permission policy.

A declarative policy that decides whether an action may run based on its
risk level, command category, and an explicit allow/deny list. The default
policy is permissive for SAFE/LOW actions and requires approval for MEDIUM+,
which matches the design goal of a safe-by-default AI shell.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..errors import PermissionDeniedError
from ..types import CommandSource, RiskLevel


@dataclass
class PermissionPolicy:
    """Policy controlling which actions may execute without approval."""

    auto_approve_below: RiskLevel = RiskLevel.LOW
    require_explicit_approval: set[RiskLevel] = field(
        default_factory=lambda: {RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL}
    )
    deny_list: set[str] = field(default_factory=set)
    allow_list: set[str] = field(default_factory=set)
    require_approval_for_ai: bool = True

    def _level_order(self) -> list[RiskLevel]:
        return list(RiskLevel)

    def is_denied(self, command: str) -> bool:
        return command in self.deny_list

    def is_explicitly_allowed(self, command: str) -> bool:
        return command in self.allow_list

    def needs_approval(
        self,
        command: str,
        risk: RiskLevel,
        source: CommandSource,
    ) -> bool:
        """Return True if the action requires interactive approval."""
        if self.is_denied(command):
            return True
        if self.is_explicitly_allowed(command):
            return False
        if source == CommandSource.AI_GENERATED and self.require_approval_for_ai:
            return True
        order = self._level_order()
        return order.index(risk) >= order.index(self.auto_approve_below)

    def check(
        self,
        command: str,
        risk: RiskLevel,
        source: CommandSource,
    ) -> None:
        """Raise PermissionDeniedError if the action is forbidden outright."""
        if self.is_denied(command):
            raise PermissionDeniedError(command, "command is on the deny list")
