"""Agent creation framework."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .agent import Agent, AgentCapability
from .permissions import Role


class Behavior(enum.Enum):
    ECHO = "echo"
    CUSTOM = "custom"


@dataclass
class AgentSpec:
    name: str
    role: Role
    capabilities: list[AgentCapability] = field(default_factory=list)
    behavior: Behavior = Behavior.ECHO
    description: str = ""
    config: dict[str, Any] = field(default_factory=dict)


class AgentFactory:
    def __init__(self) -> None:
        self._registry: dict[Behavior, Callable[[AgentSpec], Agent]] = {}

    def register_behavior(self, behavior: Behavior, builder: Callable[[AgentSpec], Agent]) -> None:
        self._registry[behavior] = builder

    def create(self, spec: AgentSpec) -> Agent:
        builder = self._registry.get(spec.behavior)
        if builder is None:
            raise ValueError(f"No builder for behavior {spec.behavior}")
        return builder(spec)

    @staticmethod
    def default_builder(spec: AgentSpec) -> Agent:
        from ..agents.base_agent import FunctionalAgent
        return FunctionalAgent(name=spec.name, capabilities=set(spec.capabilities), behavior=spec.behavior, description=spec.description)
