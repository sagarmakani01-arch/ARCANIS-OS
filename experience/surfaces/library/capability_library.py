from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus


class CapabilityCard(QFrame):
    clicked = Signal(str, str)

    def __init__(self, name, version, state, dependencies, parent=None):
        super().__init__(parent)
        self._cap_name = name
        self._cap_state = state
        self.setStyleSheet(f"""
            CapabilityCard {{
                background: {T.surface.name()};
                border: 1px solid {T.border_light.name()};
                border-radius: 0px;
            }}
            CapabilityCard:hover {{
                border: 1px solid {T.accent.name()};
                background: {T.accent_bg.name()};
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

    def set_state(self, state):
        self._cap_state = state
        state_colors = {
            "ready": T.green,
            "loading": T.amber,
            "error": T.red,
            "disabled": T.text_muted,
        }
        c = state_colors.get(state, T.text_muted)

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit(self._cap_name, self._cap_state)
        super().mousePressEvent(event)


class CapabilityLibrarySurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self._cards = {}

    def _init_content(self):
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(6)

        self.count_lbl = QLabel("CAPABILITIES: 6 AVAILABLE")
        self.count_lbl.setStyleSheet(T.mono_style())
        layout.addWidget(self.count_lbl)

        self.selected_lbl = QLabel("")
        self.selected_lbl.setStyleSheet(T.label_style() + f"font-size: {T.font_size_sm}; color: {T.accent};")
        self.selected_lbl.setVisible(False)
        layout.addWidget(self.selected_lbl)

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
            card.clicked.connect(self._on_capability_clicked)
            self._cards[name.lower()] = card
            layout.addWidget(card)

        layout.addStretch()

    def _on_capability_clicked(self, name, state):
        self.selected_lbl.setText(f"\u25B6 {name} ({state})")
        self.selected_lbl.setVisible(True)
        new_state = "active" if state == "ready" else state
        self._bus.emit(EventBus.CAPABILITY_STATE, {
            "name": name,
            "state": new_state,
            "source": self._surface_id,
        })
        self._bus.emit(EventBus.CAPABILITY_UPDATE, {
            "name": name,
            "active": state == "ready",
        })

    def _setup_events(self):
        self._bus.subscribe(EventBus.CAPABILITY_STATE, self._on_state)

    def _on_state(self, event, data):
        name = data.get("name", "")
        state = data.get("state", "")
        source = data.get("source", "")
        if name.lower() in self._cards and source != self._surface_id:
            self._cards[name.lower()].set_state(state)
            self.selected_lbl.setText(f"\u25B6 {name} -> {state}")
            self.selected_lbl.setVisible(True)
