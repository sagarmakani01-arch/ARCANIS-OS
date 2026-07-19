from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus
from experience.ecosystem import EcosystemCoordinator


class AgentCard(QFrame):
    clicked = Signal(str, str)

    def __init__(self, name, role, active=True, parent=None):
        super().__init__(parent)
        self._active = active
        self._agent_name = name
        self._agent_role = role
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            AgentCard {{ background: {T.surface}; border: 1px solid {T.border_light}; border-radius: 5px; }}
            AgentCard:hover {{ border-color: {T.accent}; background: {T.accent_bg}; }}
        """)
        l = QHBoxLayout(self)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(8)

        self.dot = QLabel("\u25CF")
        self.dot.setStyleSheet(f"font-size: 8px; color: {T.green if active else T.text_muted}; border: none; background: transparent;")
        l.addWidget(self.dot)

        col = QVBoxLayout()
        col.setSpacing(1)
        self.name_lbl = QLabel(name)
        self.name_lbl.setStyleSheet(T.label_style() + f"font-size: {T.font_size_sm};")
        col.addWidget(self.name_lbl)
        self.role_lbl = QLabel(role)
        self.role_lbl.setStyleSheet(T.label_style() + f"color: {T.text_muted}; font-size: {T.font_size_xs};")
        col.addWidget(self.role_lbl)
        l.addLayout(col, 1)

        self.activity = QLabel("idle")
        self.activity.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_xs};")
        l.addWidget(self.activity)

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit(self._agent_name, self._agent_role)
        super().mousePressEvent(event)

    def set_active(self, a):
        self._active = a
        self.dot.setStyleSheet(f"font-size: 8px; color: {T.green if a else T.text_muted}; border: none; background: transparent;")

    def set_activity(self, a):
        self.activity.setText(a)


class AgentNetworkSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self.eco = EcosystemCoordinator()
        self.cards = {}
        self._selected_agent = None
        self.update_interval(2500)

    def _init_content(self):
        l = QVBoxLayout(self.content)
        l.setContentsMargins(12, 8, 12, 12)
        l.setSpacing(6)

        self.summary_lbl = QLabel("AGENTS ONLINE: 0 / 0")
        self.summary_lbl.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_sm}; color: {T.accent};")
        l.addWidget(self.summary_lbl)

        self.selected_lbl = QLabel("")
        self.selected_lbl.setStyleSheet(T.label_style() + f"font-size: {T.font_size_sm}; color: {T.accent};")
        self.selected_lbl.setVisible(False)
        l.addWidget(self.selected_lbl)

        self.cards_container = QVBoxLayout()
        self.cards_container.setSpacing(4)
        l.addLayout(self.cards_container)

        self._refresh_agents()

        l.addSpacing(8)
        hdr2 = QLabel("COMMUNICATION")
        hdr2.setStyleSheet(T.muted_style())
        l.addWidget(hdr2)
        self.comm_label = QLabel("0 messages")
        self.comm_label.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_sm};")
        l.addWidget(self.comm_label)

        l.addSpacing(4)
        self.msg_container = QVBoxLayout()
        self.msg_container.setSpacing(2)
        l.addLayout(self.msg_container)

        l.addStretch()

    def _refresh_agents(self, highlight=None):
        for i in reversed(range(self.cards_container.count())):
            w = self.cards_container.itemAt(i).widget()
            if w:
                w.deleteLater()
        self.cards = {}

        agents = self.eco.db.get_agents()
        status_map = self.eco.get_agent_status()
        for a in agents:
            active = status_map.get(a["name"], "idle") == "active"
            card = AgentCard(a["name"], a["role"], active)
            card.clicked.connect(self._on_agent_clicked)
            if highlight and a["name"] == highlight:
                card.setStyleSheet(f"""
                    AgentCard {{ background: {T.accent_bg}; border: 1px solid {T.accent}; border-radius: 5px; }}
                    AgentCard:hover {{ border-color: {T.accent}; }}
                """)
            self.cards[a["name"]] = card
            self.cards_container.addWidget(card)

        stats = self.eco.get_stats()
        self.summary_lbl.setText(f"AGENTS ONLINE: {stats.get('agents_active', 0)} / {stats.get('agents', 0)}")

    def _on_agent_clicked(self, name, role):
        self._selected_agent = name
        self.selected_lbl.setText(f"\u25B6 {name} ({role})")
        self.selected_lbl.setVisible(True)
        self._bus.emit(EventBus.AGENT_ACTIVATED, {
            "name": name,
            "role": role,
            "source": self._surface_id,
        })

    def _refresh_messages(self):
        for i in reversed(range(self.msg_container.count())):
            w = self.msg_container.itemAt(i).widget()
            if w:
                w.deleteLater()

        msgs = self.eco.get_agent_messages(8)
        self.comm_label.setText(f"{len(msgs)} messages")
        for m in msgs[:5]:
            ts = m.get("timestamp", "")[11:19] if m.get("timestamp") else ""
            content = m.get("content", "")[:60]
            lbl = QLabel(f"[{ts}] {content}")
            lbl.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_xs};")
            self.msg_container.addWidget(lbl)

    def _on_tick(self):
        self._refresh_agents(self._selected_agent)
        self._refresh_messages()

    def _setup_events(self):
        self._bus.subscribe(EventBus.AGENT_ACTIVATED, self._on_activated)
        self._bus.subscribe(EventBus.AGENT_ACTIVITY, self._on_activity)

    def _on_activated(self, event, data):
        name = data.get("name", "")
        source = data.get("source", "")
        if source != self._surface_id:
            self._selected_agent = name
            self.selected_lbl.setText(f"\u25B6 {name} (selected)")
            self.selected_lbl.setVisible(True)
        self._refresh_agents(self._selected_agent)

    def _on_activity(self, event, data):
        name = data.get("name", "")
        activity = data.get("activity", "")
        for n, card in self.cards.items():
            if n.lower() == name.lower():
                card.set_activity(activity)
