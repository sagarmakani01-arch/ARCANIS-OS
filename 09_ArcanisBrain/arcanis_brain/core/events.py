from typing import Any, Callable
from collections import defaultdict
import uuid
from datetime import datetime, timezone


class Event:
    def __init__(self, event_type: str, data: Any = None, source: str = ""):
        self.event_id = uuid.uuid4().hex
        self.event_type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.now(timezone.utc)

    def __repr__(self):
        return f"Event({self.event_type}, source={self.source})"


EventHandler = Callable[[Event], None]


class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = defaultdict(list)
        return cls._instance

    def subscribe(self, event_type: str, handler: EventHandler) -> Callable:
        self._subscribers[event_type].append(handler)
        return lambda: self._subscribers[event_type].remove(handler)

    def publish(self, event: Event) -> None:
        for handler in self._subscribers.get(event.event_type, []):
            handler(event)
        for handler in self._subscribers.get("*", []):
            handler(event)

    def emit(self, event_type: str, data: Any = None, source: str = "") -> None:
        self.publish(Event(event_type, data, source))
