from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame, QScrollArea, QWidget
from PySide6.QtCore import Qt, QTimer

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus
from experience.ecosystem import EcosystemCoordinator


class EventLine(QFrame):
    def __init__(self, timestamp, message, kind="info", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        l = QHBoxLayout(self)
        l.setContentsMargins(4, 2, 4, 2)
        l.setSpacing(8)

        ts = QLabel(timestamp)
        ts.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_xs};")
        ts.setFixedWidth(60)
        l.addWidget(ts)

        msg = QLabel(message)
        msg.setStyleSheet(T.label_style() + f"color: {T.text}; font-size: {T.font_size_sm};")
        msg.setWordWrap(True)
        l.addWidget(msg, 1)

        kind_lbl = QLabel(kind.upper())
        color = {"info": T.accent, "error": T.red, "warning": T.amber, "research": T.purple, "analysis": T.cyan, "monitor": T.green}.get(kind, T.text_muted)
        kind_lbl.setStyleSheet(T.mono_style() + f"color: {color}; font-size: {T.font_size_xs};")
        l.addWidget(kind_lbl)


class EventStreamSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self.eco = EcosystemCoordinator()
        self.update_interval(2500)

    def _init_content(self):
        l = QVBoxLayout(self.content)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

        header = QLabel("  EVENT STREAM")
        header.setFixedHeight(28)
        header.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_sm}; color: {T.accent}; background: {T.surface_alt};")
        l.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.stream_layout = QVBoxLayout(scroll_content)
        self.stream_layout.setContentsMargins(8, 4, 8, 4)
        self.stream_layout.setSpacing(2)
        self.stream_layout.addStretch()
        scroll.setWidget(scroll_content)
        l.addWidget(scroll, 1)

        self._refresh_events()

    def _refresh_events(self):
        for i in reversed(range(self.stream_layout.count())):
            w = self.stream_layout.itemAt(i).widget()
            if w and hasattr(w, 'deleteLater'):
                w.deleteLater()

        msgs = self.eco.get_agent_messages(30)
        memories = self.eco.get_memories(20)

        events = []
        for m in msgs:
            ts = m.get("timestamp", "")[11:19] if m.get("timestamp") else "--:--:--"
            events.append((ts, m.get("content", ""), m.get("type", "info")))
        for mem in memories:
            ts = mem.get("timestamp", "")[11:19] if mem.get("timestamp") else "--:--:--"
            events.append((ts, mem.get("content", ""), mem.get("level", "info")))

        events.sort(key=lambda x: x[0], reverse=True)

        for ts, content, kind in events[:25]:
            line = EventLine(ts, content[:80], kind)
            self.stream_layout.addWidget(line)

        self.stream_layout.addStretch()

    def _on_tick(self):
        self._refresh_events()
