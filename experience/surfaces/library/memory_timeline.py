from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus
from experience.ecosystem import EcosystemCoordinator


class MemoryEntry(QFrame):
    def __init__(self, time_str, summary, kind="memory", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(8)

        line = QFrame()
        line.setFixedWidth(1)
        line.setStyleSheet(f"background: {T.border_light}; border: none;")
        l.addWidget(line)

        col = QVBoxLayout()
        col.setSpacing(1)
        t = QLabel(time_str)
        t.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_xs};")
        col.addWidget(t)
        s = QLabel(summary)
        s.setStyleSheet(T.label_style() + f"color: {T.text}; font-size: {T.font_size_sm};")
        col.addWidget(s)
        l.addLayout(col, 1)

        kind_lbl = QLabel(kind.upper())
        kind_lbl.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_xs};")
        l.addWidget(kind_lbl)


class MemoryTimelineSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self.eco = EcosystemCoordinator()
        self.update_interval(3000)

    def _init_content(self):
        l = QVBoxLayout(self.content)
        l.setContentsMargins(12, 8, 12, 12)
        l.setSpacing(4)

        session = QLabel("SESSION: Current")
        session.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_sm}; color: {T.accent};")
        l.addWidget(session)

        stats = self.eco.get_stats()
        count = QLabel(f"TOTAL MEMORIES: {stats.get('memories', 0)}")
        count.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_xs}; color: {T.text_muted};")
        l.addWidget(count)

        l.addSpacing(4)
        hdr = QLabel("RECENT MEMORY")
        hdr.setStyleSheet(T.muted_style())
        l.addWidget(hdr)

        self.entries_layout = QVBoxLayout()
        self.entries_layout.setSpacing(6)
        l.addLayout(self.entries_layout)

        self._refresh_memories()
        l.addStretch()

    def _refresh_memories(self):
        for i in reversed(range(self.entries_layout.count())):
            w = self.entries_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        memories = self.eco.get_memories(12)
        for mem in memories:
            ts = mem.get("timestamp", "")[11:19] if mem.get("timestamp") else "--:--:--"
            entry = MemoryEntry(ts, mem.get("content", ""), mem.get("level", "info"))
            self.entries_layout.addWidget(entry)

    def _on_tick(self):
        self._refresh_memories()

    def _setup_events(self):
        self._bus.subscribe(EventBus.MEMORY_WRITTEN, self._on_memory)

    def _on_memory(self, event, data):
        self._refresh_memories()
