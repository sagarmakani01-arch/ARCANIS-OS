from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags, DockPosition
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus


class ZoneIndicator(QFrame):
    def __init__(self, name, active=False, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            ZoneIndicator {{
                background: {T.surface.name()};
                border: 1px solid {T.border_light.name()};
            }}
            ZoneIndicator:hover {{
                border: 1px solid {T.accent.name()};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        self._active = active

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        dot_row = QHBoxLayout()
        dot_row.setSpacing(4)
        dot_row.addStretch()
        self.dot = QFrame()
        self.dot.setFixedSize(4, 4)
        self._update_dot()
        dot_row.addWidget(self.dot)
        dot_row.addStretch()
        layout.addLayout(dot_row)

        self.name_lbl = QLabel(name)
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setStyleSheet(
            f"font-size: {T.font_size_xs}px; font-weight: 500; "
            f"color: {T.text.name()}; font-family: '{T.font_family}';"
        )
        layout.addWidget(self.name_lbl)

    def _update_dot(self):
        c = T.green.name() if self._active else T.text_muted.name()
        self.dot.setStyleSheet(f"background: {c}; border: none; border-radius: 2px;")

    def set_active(self, a):
        self._active = a
        self._update_dot()


class WorkspaceMapSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)

    def _init_content(self):
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(6)

        info_lbl = QLabel("WORKSPACE: ACTIVE")
        info_lbl.setStyleSheet(T.mono_style())
        layout.addWidget(info_lbl)

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
        ]
        for name, active in zones:
            zi = ZoneIndicator(name, active)
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

    def _setup_events(self):
        self._bus.subscribe(EventBus.WORKSPACE_FOCUS, self._on_focus)

    def _on_focus(self, event, data):
        pass
