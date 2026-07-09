from typing import Any, Callable
from arcanis_brain.core.types import Message, MessageRole
from arcanis_brain.core.events import Event
import json


class WebSocketAPI:
    def __init__(self, brain):
        self.brain = brain
        self._connections: dict[str, dict] = {}
        self._handlers: dict[str, Callable] = {
            "chat": self._handle_chat,
            "ping": self._handle_ping,
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
        }

    async def on_message(self, connection_id: str, raw_message: str) -> dict:
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            return {"type": "error", "payload": {"message": "Invalid JSON"}}

        msg_type = data.get("type", "")
        handler = self._handlers.get(msg_type)
        if not handler:
            return {"type": "error", "payload": {"message": f"Unknown message type: {msg_type}"}}

        return await handler(connection_id, data.get("payload", {}))

    def on_connect(self, connection_id: str):
        self._connections[connection_id] = {
            "id": connection_id,
            "subscriptions": [],
            "user_id": "anonymous",
        }

    def on_disconnect(self, connection_id: str):
        self._connections.pop(connection_id, None)

    async def _handle_chat(self, conn_id: str, payload: dict) -> dict:
        message = payload.get("message", "")
        conn = self._connections.get(conn_id, {})
        user_id = payload.get("userId") or conn.get("user_id", "anonymous")
        response = await self.brain.process(message, user_id)
        return {"type": "chat", "payload": {"response": response, "messageId": id(message)}}

    async def _handle_ping(self, conn_id: str, payload: dict) -> dict:
        return {"type": "pong", "payload": {"timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}}

    async def _handle_subscribe(self, conn_id: str, payload: dict) -> dict:
        event_type = payload.get("event", "")
        conn = self._connections.get(conn_id)
        if conn and event_type:
            conn["subscriptions"].append(event_type)
            return {"type": "subscribed", "payload": {"event": event_type}}
        return {"type": "error", "payload": {"message": "Invalid subscription"}}

    async def _handle_unsubscribe(self, conn_id: str, payload: dict) -> dict:
        event_type = payload.get("event", "")
        conn = self._connections.get(conn_id)
        if conn and event_type in conn["subscriptions"]:
            conn["subscriptions"].remove(event_type)
            return {"type": "unsubscribed", "payload": {"event": event_type}}
        return {"type": "error", "payload": {"message": "Not subscribed"}}
