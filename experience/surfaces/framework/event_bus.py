import time
from collections import defaultdict


class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = defaultdict(list)
            cls._instance._history = []
            cls._instance._max_history = 200
        return cls._instance

    def subscribe(self, event_type, callback, surface_id=None):
        self._subscribers[event_type].append({
            "callback": callback,
            "surface_id": surface_id,
        })

    def unsubscribe(self, event_type, callback):
        self._subscribers[event_type] = [
            s for s in self._subscribers[event_type]
            if s["callback"] != callback
        ]

    def emit(self, event_type, data=None):
        entry = {
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        }
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        for sub in self._subscribers.get(event_type, []):
            try:
                sub["callback"](event_type, data)
            except Exception as e:
                print(f"[EventBus] Error in subscriber: {e}")

    def history(self, count=20):
        return self._history[-count:]

    def clear_history(self):
        self._history.clear()

    # Intelligence Core events
    REASONING_UPDATE = "intelligence.reasoning"
    CAPABILITY_UPDATE = "intelligence.capability"
    OBJECTIVE_UPDATE = "intelligence.objective"

    # Mission events
    MISSION_UPDATE = "mission.update"
    MISSION_PROGRESS = "mission.progress"
    TASK_UPDATE = "mission.task"

    # Agent events
    AGENT_ACTIVATED = "agent.activated"
    AGENT_DEACTIVATED = "agent.deactivated"
    AGENT_ACTIVITY = "agent.activity"
    AGENT_HEALTH = "agent.health"

    # Knowledge events
    KNOWLEDGE_UPDATED = "knowledge.updated"
    KNOWLEDGE_LINKED = "knowledge.linked"
    CONCEPT_CREATED = "knowledge.concept"

    # Memory events
    MEMORY_WRITTEN = "memory.written"
    MEMORY_RECALLED = "memory.recalled"
    SESSION_UPDATED = "memory.session"

    # System events
    SYSTEM_HEALTH = "system.health"
    SYSTEM_EVENT = "system.event"
    SYSTEM_RESOURCE = "system.resource"

    # Workspace events
    WORKSPACE_FOCUS = "workspace.focus"
    SURFACE_STATE_CHANGED = "surface.state"
    SURFACE_FOCUSED = "surface.focused"

    # Capability events
    CAPABILITY_REGISTERED = "capability.registered"
    CAPABILITY_STATE = "capability.state"

    # Inter-surface messaging
    SURFACE_MESSAGE = "surface.message"
    SURFACE_QUERY = "surface.query"
    SURFACE_RESPONSE = "surface.response"
