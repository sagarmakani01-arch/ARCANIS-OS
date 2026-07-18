from enum import Enum, auto

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QTimer

from .theme import SurfaceTheme as T
from .event_bus import EventBus


class SurfaceState(Enum):
    COMPACT = "compact"
    STANDARD = "standard"
    EXPANDED = "expanded"
    IMMERSIVE = "immersive"


class DockPosition(Enum):
    LEFT = "left"
    RIGHT = "right"
    BOTTOM = "bottom"
    FLOAT = "float"
    FULL = "full"


class SurfaceFlags:
    NONE = 0
    DOCKABLE = 1
    COLLAPSIBLE = 2
    PINNABLE = 4
    DETACHABLE = 8
    KEYBOARD_NAV = 16
    RESIZABLE = 32
    ALL = DOCKABLE | COLLAPSIBLE | PINNABLE | DETACHABLE | KEYBOARD_NAV | RESIZABLE


class Header(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title = QLabel(title.upper())
        self.title.setStyleSheet(
            f"font-size: {T.font_size_xs}px; font-weight: 600; "
            f"color: {T.text_muted.name()}; letter-spacing: 1px; "
            f"font-family: '{T.font_family}'; border: none;"
        )
        layout.addWidget(self.title)
        layout.addStretch()
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def set_title(self, text):
        self.title.setText(text.upper())


class SurfaceContent(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")


class BaseSurface(QFrame):
    focused = Signal(str)
    state_changed = Signal(str, object)

    def __init__(self, title, surface_id, flags=SurfaceFlags.DOCKABLE, parent=None):
        super().__init__(parent)
        self._surface_id = surface_id
        self._title = title
        self._flags = flags
        self._state = SurfaceState.STANDARD
        self._dock = DockPosition.FLOAT
        self._bus = EventBus()
        self._timer = QTimer(self)

        self.setStyleSheet(f"""
            BaseSurface {{
                background: {T.surface.name()};
                border: 1px solid {T.border.name()};
                border-radius: 0px;
            }}
        """)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        self.header = Header(title, self)
        self._outer.addWidget(self.header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {T.border_light.name()}; border: none;")
        self._outer.addWidget(sep)

        self.content = SurfaceContent(self)
        self._outer.addWidget(self.content, 1)

        self._init_content()
        self._setup_events()

    def _init_content(self):
        pass

    def _setup_events(self):
        pass

    def surface_id(self):
        return self._surface_id

    def surface_title(self):
        return self._title

    def set_state(self, state):
        old = self._state
        self._state = state
        self.state_changed.emit(self._surface_id, state)
        self._bus.emit(EventBus.SURFACE_STATE_CHANGED, {
            "surface_id": self._surface_id,
            "from": old.value if old else None,
            "to": state.value,
        })
        self._on_state_changed(state)

    def get_state(self):
        return self._state

    def set_dock(self, pos):
        self._dock = pos

    def get_dock(self):
        return self._dock

    def _on_state_changed(self, state):
        pass

    def on_event(self, event_type, data):
        pass

    def send_message(self, target_id, message_type, payload=None):
        self._bus.emit(EventBus.SURFACE_MESSAGE, {
            "from": self._surface_id,
            "to": target_id,
            "type": message_type,
            "payload": payload,
        })

    def broadcast_message(self, message_type, payload=None):
        self._bus.emit(EventBus.SURFACE_MESSAGE, {
            "from": self._surface_id,
            "to": "*",
            "type": message_type,
            "payload": payload,
        })

    def query_surface(self, target_id, query_type, payload=None):
        self._bus.emit(EventBus.SURFACE_QUERY, {
            "from": self._surface_id,
            "to": target_id,
            "type": query_type,
            "payload": payload,
        })

    def respond_to_query(self, target_id, query_type, payload=None):
        self._bus.emit(EventBus.SURFACE_RESPONSE, {
            "from": self._surface_id,
            "to": target_id,
            "type": query_type,
            "payload": payload,
        })

    def update_interval(self, ms):
        self._timer.setInterval(ms)
        self._timer.timeout.connect(self._on_tick)

    def _on_tick(self):
        pass

    def focusSurface(self):
        super().focusWidget()
        self.focused.emit(self._surface_id)

    def set_focus(self):
        self.setFocus()
        self.focusSurface()

    def enterEvent(self, event):
        self.setStyleSheet(f"""
            BaseSurface {{
                background: {T.surface.name()};
                border: 1px solid {T.border.name()};
                border-radius: 0px;
            }}
        """)
        super().enterEvent(event)
