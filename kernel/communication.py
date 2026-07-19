import json
import time
import uuid
from collections import defaultdict
from datetime import datetime
from threading import RLock


class MessageBus:
    _instance = None
    _lock = RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._subscribers = defaultdict(list)
        self._history = []
        self._max_history = 500
        self._pending = {}
        self._lock = RLock()

    # ── Structured Message Protocol ──────────────────────────
    def create_message(self, sender, msg_type, payload, recipient="*",
                       correlation_id=None, priority=5):
        msg = {
            "id": str(uuid.uuid4())[:8],
            "sender": sender,
            "recipient": recipient,
            "type": msg_type,
            "payload": payload,
            "priority": priority,
            "timestamp": time.time(),
            "correlation_id": correlation_id or str(uuid.uuid4())[:8],
        }
        return msg

    def send(self, message):
        callbacks = []
        with self._lock:
            self._history.append(message)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

            for sub in self._subscribers.get(message["type"], []):
                target = sub.get("identity", "*")
                if message["recipient"] in ("*", target):
                    callbacks.append((sub["callback"], message, target))

        delivered = []
        for cb, msg, target in callbacks:
            try:
                cb(msg)
                delivered.append(target)
            except Exception:
                pass

        with self._lock:
            if message["recipient"] != "*" and not delivered:
                self._pending[message["id"]] = message

        return message["id"]

    def subscribe(self, msg_type, callback, identity=None):
        with self._lock:
            self._subscribers[msg_type].append({
                "callback": callback,
                "identity": identity,
            })

    def unsubscribe(self, msg_type, callback):
        with self._lock:
            self._subscribers[msg_type] = [
                s for s in self._subscribers[msg_type]
                if s["callback"] != callback
            ]

    def reply(self, original_msg, payload):
        reply = self.create_message(
            sender=original_msg["recipient"],
            msg_type=f"{original_msg['type']}.reply",
            payload=payload,
            recipient=original_msg["sender"],
            correlation_id=original_msg["correlation_id"],
        )
        return self.send(reply)

    # ── Communication Patterns ───────────────────────────────

    # Request-Response
    def request(self, sender, recipient, payload, msg_type="request", timeout=5.0):
        correlation_id = str(uuid.uuid4())[:8]
        msg = self.create_message(sender, msg_type, payload, recipient, correlation_id)
        result = {"value": None, "received": False}

        def handler(response):
            if response.get("correlation_id") == correlation_id:
                result["value"] = response.get("payload")
                result["received"] = True

        self.subscribe(f"{msg_type}.reply", handler, sender)
        self.send(msg)

        waited = 0
        while not result["received"] and waited < timeout:
            time.sleep(0.05)
            waited += 0.05

        self.unsubscribe(f"{msg_type}.reply", handler)
        return result["value"]

    # Task Delegation
    def delegate(self, sender, recipient, task_type, task_data, priority=5):
        msg = self.create_message(
            sender, "task.delegate", task_data, recipient, priority=priority
        )
        msg["task_type"] = task_type
        return self.send(msg)

    def delegate_result(self, original_msg, result_data):
        return self.reply(original_msg, {
            "status": "completed",
            "result": result_data,
            "delegation_id": original_msg["id"],
        })

    # Broadcast
    def broadcast(self, sender, msg_type, payload):
        msg = self.create_message(sender, msg_type, payload, "*")
        return self.send(msg)

    # ── Agent Discovery ──────────────────────────────────────
    def register_agent(self, agent_id, capabilities=None):
        self.broadcast("kernel", "agent.registered", {
            "agent_id": agent_id,
            "capabilities": capabilities or [],
            "timestamp": time.time(),
        })

    def discover_agents(self, searcher_id, capability=None, timeout=2.0):
        results = []

        def handler(msg):
            agent_info = msg.get("payload", {})
            if capability:
                caps = agent_info.get("capabilities", [])
                if capability not in caps:
                    return
            results.append(agent_info)

        self.subscribe("agent.announce", handler, searcher_id)
        self.broadcast(searcher_id, "agent.discover", {"searcher": searcher_id, "capability": capability})

        waited = 0
        while waited < timeout:
            time.sleep(0.1)
            waited += 0.1

        self.unsubscribe("agent.announce", handler)
        return results

    # ── Event Types ──────────────────────────────────────────
    # Agent events
    AGENT_REGISTERED = "agent.registered"
    AGENT_DISCOVER = "agent.discover"
    AGENT_ANNOUNCE = "agent.announce"
    AGENT_ACTIVATED = "agent.activated"
    AGENT_DEACTIVATED = "agent.deactivated"
    AGENT_ACTIVITY = "agent.activity"
    AGENT_MESSAGE = "agent.message"

    # Task events
    TASK_DELEGATE = "task.delegate"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_PROGRESS = "task.progress"

    # Knowledge events
    KNOWLEDGE_UPDATED = "knowledge.updated"
    KNOWLEDGE_LINKED = "knowledge.linked"
    KNOWLEDGE_REQUEST = "knowledge.request"

    # System events
    SYSTEM_EVENT = "system.event"
    SYSTEM_HEALTH = "system.health"
    SYSTEM_ERROR = "system.error"

    # Memory events
    MEMORY_STORED = "memory.stored"
    MEMORY_RECALLED = "memory.recalled"
    MEMORY_SYNC = "memory.sync"

    # Governance events
    APPROVAL_REQUESTED = "governance.approval.requested"
    APPROVAL_GRANTED = "governance.approval.granted"
    APPROVAL_DENIED = "governance.approval.denied"
    OVERSIGHT_ALERT = "governance.alert"

    # History
    def get_history(self, msg_type="", limit=50):
        if msg_type:
            return [m for m in self._history if m["type"] == msg_type][-limit:]
        return self._history[-limit:]

    def get_pending_count(self):
        return len(self._pending)

    def get_stats(self):
        return {
            "total_messages": len(self._history),
            "pending": len(self._pending),
            "subscriber_count": sum(len(s) for s in self._subscribers.values()),
        }
