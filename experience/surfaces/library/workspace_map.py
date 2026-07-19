from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags, DockPosition
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus


ZONE_MAP = {
    "Intelligence Core": "cognitive",
    "Agent Network": "agent",
    "Knowledge Graph": "knowledge",
    "Mission Control": "mission",
    "Memory Timeline": "memory",
    "System Monitor": "system",
    "Surfaces": "surfaces",
}


class ZoneIndicator(QFrame):
    clicked = Signal(str)

    def __init__(self, name, active=False, parent=None):
        super().__init__(parent)
        self._zone_name = name
        self._active = active
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            ZoneIndicator {{
                background: {T.surface.name()};
                border: 1px solid {T.border_light.name()};
            }}
            ZoneIndicator:hover {{
                border: 1px solid {T.accent.name()};
                background: {T.accent_bg.name()};
            }}
        """)
        self.setFixedHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.dot = QFrame()
        self.dot.setFixedSize(6, 6)
        self._update_dot()
        layout.addWidget(self.dot)

        self.name_lbl = QLabel(name)
        self.name_lbl.setStyleSheet(
            f"font-size: {T.font_size_sm}px; font-weight: 500; "
            f"color: {T.text.name()}; font-family: '{T.font_family}';"
        )
        layout.addWidget(self.name_lbl, 1)

        self.active_lbl = QLabel("ACTIVE" if active else "STAND BY")
        self.active_lbl.setStyleSheet(
            f"font-size: {T.font_size_xs}px; font-weight: 600; "
            f"color: {(T.green if active else T.text_muted).name()}; "
            f"font-family: '{T.font_family}';"
        )
        layout.addWidget(self.active_lbl)

    def _update_dot(self):
        c = T.green.name() if self._active else T.text_muted.name()
        self.dot.setStyleSheet(f"background: {c}; border: none; border-radius: 3px;")

    def set_active(self, a):
        self._active = a
        self._update_dot()
        self.active_lbl.setText("ACTIVE" if a else "STAND BY")
        c = T.green.name() if a else T.text_muted.name()
        self.active_lbl.setStyleSheet(
            f"font-size: {T.font_size_xs}px; font-weight: 600; "
            f"color: {c}; font-family: '{T.font_family}';"
        )

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit(self._zone_name)
        super().mousePressEvent(event)


class WorkspaceMapSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self._indicators = {}

    def _init_content(self):
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(6)

        self.info_lbl = QLabel("WORKSPACE: ACTIVE")
        self.info_lbl.setStyleSheet(T.mono_style())
        layout.addWidget(self.info_lbl)

        self.selected_lbl = QLabel("")
        self.selected_lbl.setStyleSheet(T.label_style() + f"font-size: {T.font_size_sm}; color: {T.accent};")
        self.selected_lbl.setVisible(False)
        layout.addWidget(self.selected_lbl)

        layout.addSpacing(4)

        zones_lbl = QLabel("ZONES")
        zones_lbl.setStyleSheet(T.muted_style())
        layout.addWidget(zones_lbl)

        zone_grid = QVBoxLayout()
        zone_grid.setSpacing(4)

        zones = [
            ("Intelligence Core", True),
            ("Agent Network", True),
            ("Knowledge Graph", True),
            ("Mission Control", False),
            ("Memory Timeline", True),
            ("System Monitor", False),
            ("Surfaces", True),
        ]
        for name, active in zones:
            zi = ZoneIndicator(name, active)
            zi.clicked.connect(self._on_zone_clicked)
            self._indicators[name.lower()] = zi
            zone_grid.addWidget(zi)
        layout.addLayout(zone_grid)

        layout.addSpacing(4)
        nav_lbl = QLabel("QUICK NAVIGATION")
        nav_lbl.setStyleSheet(T.muted_style())
        layout.addWidget(nav_lbl)

        nav_text = QLabel("Ctrl+1  Core\nCtrl+2  Agents\nCtrl+3  Knowledge\nCtrl+4  Memory")
        nav_text.setStyleSheet(
            f"font-size: {T.font_size_xs}px; color: {T.text_sec.name()}; "
            f"font-family: '{T.font_mono}';"
        )
        layout.addWidget(nav_text)

        layout.addStretch()

    def _on_zone_clicked(self, name):
        zone_id = ZONE_MAP.get(name, name.lower().replace(" ", "_"))
        self.selected_lbl.setText(f"\u25B6 Navigating to: {name}")
        self.selected_lbl.setVisible(True)
        self._bus.emit(EventBus.WORKSPACE_FOCUS, {
            "zone": zone_id,
            "name": name,
            "source": self._surface_id,
        })

    def _setup_events(self):
        self._bus.subscribe(EventBus.WORKSPACE_FOCUS, self._on_focus)

    def _on_focus(self, event, data):
        name = data.get("name", "")
        source = data.get("source", "")
        if source != self._surface_id and name.lower() in self._indicators:
            for key, ind in self._indicators.items():
                ind.set_active(key == name.lower())
            self.selected_lbl.setText(f"\u25B6 Focus: {name}")
            self.selected_lbl.setVisible(True)
