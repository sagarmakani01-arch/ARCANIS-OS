"""Agent communication protocol.

The :class:`MessageBus` implements publish/subscribe plus request/reply (RPC).
Messages are routed by agent id or topic. Replies are correlated via
``correlation_id``.
"""

from __future__ import annotations

import asyncio
import enum
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("arcanis.bus")


class MessageType(enum.Enum):
    EVENT = "event"
    REQUEST = "request"
    REPLY = "reply"
    BROADCAST = "broadcast"


@dataclass
class Message:
    sender: str
    kind: str
    payload: Any = None
    receiver: Optional[str] = None
    msg_type: MessageType = MessageType.EVENT
    correlation_id: Optional[str] = None
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "kind": self.kind,
            "msg_type": self.msg_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        return cls(
            message_id=d.get("message_id", uuid.uuid4().hex),
            correlation_id=d.get("correlation_id"),
            sender=d["sender"],
            receiver=d.get("receiver"),
            kind=d["kind"],
            msg_type=MessageType(d.get("msg_type", "event")),
            payload=d.get("payload"),
            timestamp=d.get("timestamp", time.time()),
        )


class MessageBus:
    """In-process pub/sub + RPC message bus."""

    def __init__(self) -> None:
        self._subscribers: dict[str, asyncio.Queue] = {}
        self._topic_subscribers: dict[str, set[str]] = {}
        self._pending: dict[str, asyncio.Future] = {}
        self._log: list[Message] = []
        self._max_log = 1000

    def subscribe(self, agent_id: str, queue: asyncio.Queue) -> None:
        self._subscribers[agent_id] = queue

    def unsubscribe(self, agent_id: str) -> None:
        self._subscribers.pop(agent_id, None)

    def subscribe_topic(self, agent_id: str, topic: str) -> None:
        self._topic_subscribers.setdefault(topic, set()).add(agent_id)

    async def publish(self, msg: Message) -> None:
        self._record(msg)
        # Resolve pending request/reply futures
        if msg.msg_type is MessageType.REPLY and msg.correlation_id:
            fut = self._pending.pop(msg.correlation_id, None)
            if fut is not None and not fut.done():
                fut.set_result(msg)
                return

        targets: set[str] = set()
        if msg.receiver:
            targets.add(msg.receiver)
        if msg.kind in self._topic_subscribers:
            targets |= self._topic_subscribers[msg.kind]

        for target in targets:
            queue = self._subscribers.get(target)
            if queue is not None:
                await queue.put(msg)

    async def request(
        self, sender: str, to: str, kind: str, payload: Any, timeout: float = 10.0
    ) -> Optional[Message]:
        correlation_id = uuid.uuid4().hex
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[correlation_id] = fut
        msg = Message(
            sender=sender,
            receiver=to,
            kind=kind,
            payload=payload,
            msg_type=MessageType.REQUEST,
            correlation_id=correlation_id,
        )
        await self.publish(msg)
        try:
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            self._pending.pop(correlation_id, None)
            logger.warning("Request %s from %s to %s timed out", kind, sender, to)
            return None

    def reply(self, original: Message, sender: str, payload: Any) -> Message:
        return Message(
            sender=sender,
            receiver=original.sender,
            kind=original.kind + ".reply",
            payload=payload,
            msg_type=MessageType.REPLY,
            correlation_id=original.correlation_id,
        )

    def _record(self, msg: Message) -> None:
        self._log.append(msg)
        if len(self._log) > self._max_log:
            self._log = self._log[-self._max_log:]

    def history(self, limit: int = 100) -> list[Message]:
        return self._log[-limit:]
