"""Core agent definitions."""

from __future__ import annotations

import abc
import asyncio
import enum
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .message_bus import Message, MessageType

logger = logging.getLogger("arcanis.agent")


class AgentState(enum.Enum):
    IDLE = "idle"
    BUSY = "busy"
    STOPPED = "stopped"
    ERROR = "error"


class AgentCapability(enum.Enum):
    WRITE_CODE = "write_code"
    REVIEW_CODE = "review_code"
    DEBUG = "debug"
    RESEARCH = "research"
    SUMMARIZE = "summarize"
    AUTOMATE = "automate"
    SECURITY_SCAN = "security_scan"
    OS_TASK = "os_task"


Handler = Callable[["Message"], "asyncio.Future[Optional[Message]]"]


@dataclass
class AgentContext:
    agent_id: str
    name: str
    bus: "MessageBus"
    memory: "SharedMemory"
    permissions: "PermissionSystem"
    log: logging.Logger = field(default_factory=lambda: logger)


class Agent(abc.ABC):
    capabilities: set[AgentCapability] = set()
    tick_interval: float = 0.0

    def __init__(self, name: str, agent_id: Optional[str] = None) -> None:
        self.name = name
        self.agent_id = agent_id or f"{name}-{uuid.uuid4().hex[:6]}"
        self.state = AgentState.IDLE
        self._ctx: Optional[AgentContext] = None
        self._task: Optional[asyncio.Task] = None
        self._inbox: asyncio.Queue[Message] = asyncio.Queue()

    def attach(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    @property
    def ctx(self) -> AgentContext:
        if self._ctx is None:
            raise RuntimeError(f"Agent {self.name} not attached")
        return self._ctx

    def start(self) -> None:
        if self._task is not None:
            return
        self.state = AgentState.IDLE
        self.ctx.bus.subscribe(self.agent_id, self._inbox)
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run())

    async def stop(self) -> None:
        self.state = AgentState.STOPPED
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        try:
            while True:
                msg = await self._inbox.get()
                await self._dispatch(msg)
                if self.tick_interval > 0:
                    await self._maybe_tick()
        except asyncio.CancelledError:
            return
        except Exception as exc:
            self.state = AgentState.ERROR
            logger.exception("Agent %s crashed: %s", self.name, exc)

    async def _maybe_tick(self) -> None:
        now = time.monotonic()
        last = getattr(self, "_last_tick", 0.0)
        if now - last >= self.tick_interval:
            self._last_tick = now
            try:
                await self.on_tick()
            except Exception as exc:
                logger.exception("Tick error in %s: %s", self.name, exc)

    async def _dispatch(self, msg: Message) -> None:
        self.state = AgentState.BUSY
        try:
            reply = await self.handle(msg)
            if reply is not None:
                if msg.msg_type == MessageType.REQUEST:
                    reply.msg_type = MessageType.REPLY
                    reply.correlation_id = msg.correlation_id
                await self.ctx.bus.publish(reply)
        finally:
            self.state = AgentState.IDLE

    async def send(self, msg: Message) -> None:
        await self.ctx.bus.publish(msg)

    async def ask(self, to: str, kind: str, payload: Any, timeout: float = 10.0) -> Optional[Message]:
        return await self.ctx.bus.request(self.agent_id, to, kind, payload, timeout)

    @abc.abstractmethod
    async def handle(self, msg: Message) -> Optional[Message]:
        pass

    async def on_tick(self) -> None:
        pass
