from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus


class CapabilityCard(QFrame):
    def __init__(self, name, version, state, dependencies, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CapabilityCard {{
                background: {T.surface.name()};
                border: 1px solid {T.border_light.name()};
                border-radius: 0px;
            }}
            CapabilityCard:hover {{
                border: 1px solid {T.accent.name()};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(8)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"font-size: {T.font_size_sm}px; font-weight: 600; "
            f"color: {T.text.name()}; font-family: '{T.font_family}';"
        )
        header.addWidget(name_lbl)
        header.addStretch()

        state_colors = {
            "ready": T.green,
            "loading": T.amber,
            "error": T.red,
            "disabled": T.text_muted,
        }
        c = state_colors.get(state, T.text_muted)
        state_lbl = QLabel(state.upper())
        state_lbl.setStyleSheet(
            f"font-size: {T.font_size_xs}px; font-weight: 600; "
            f"color: {c.name()}; font-family: '{T.font_family}';"
        )
        header.addWidget(state_lbl)

        ver_lbl = QLabel(f"v{version}")
        ver_lbl.setStyleSheet(
            f"font-size: {T.font_size_xs}px; color: {T.text_muted.name()}; "
            f"font-family: '{T.font_mono}';"
        )
        header.addWidget(ver_lbl)
        layout.addLayout(header)

        info = QHBoxLayout()
        info.setSpacing(12)
        deps_lbl = QLabel(f"Deps: {dependencies}")
        deps_lbl.setStyleSheet(
            f"font-size: {T.font_size_xs}px; color: {T.text_sec.name()}; "
            f"font-family: '{T.font_mono}';"
        )
        info.addWidget(deps_lbl)
        info.addStretch()
        layout.addLayout(info)

        self.setFixedHeight(56)


class CapabilityLibrarySurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)

    def _init_content(self):
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(6)

        count_lbl = QLabel("CAPABILITIES: 6 AVAILABLE")
        count_lbl.setStyleSheet(T.mono_style())
        layout.addWidget(count_lbl)

        layout.addSpacing(4)

        capabilities = [
            ("Research", "2.1.0", "ready", "3"),
            ("Programming", "1.4.0", "ready", "5"),
            ("Simulation", "1.0.0", "loading", "4"),
            ("Analysis", "2.0.0", "ready", "2"),
            ("Writing", "1.3.0", "ready", "2"),
            ("Design", "1.1.0", "disabled", "4"),
        ]
        for name, ver, state, deps in capabilities:
            card = CapabilityCard(name, ver, state, deps)
            layout.addWidget(card)

        layout.addStretch()

    def _setup_events(self):
        self._bus.subscribe(EventBus.CAPABILITY_STATE, self._on_state)

    def _on_state(self, event, data):
        pass
