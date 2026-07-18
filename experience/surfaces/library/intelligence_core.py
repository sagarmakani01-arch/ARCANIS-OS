from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus
from experience.ecosystem import EcosystemCoordinator


class MetricRow(QFrame):
    def __init__(self, label, value, color=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: transparent; border: none;")
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setFixedWidth(80)
        lbl.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_xs};")
        l.addWidget(lbl)
        self._value = QLabel(value)
        s = f"color: {color};" if color else ""
        self._value.setStyleSheet(T.mono_style() + s + f"font-size: {T.font_size_sm};")
        l.addWidget(self._value)
        l.addStretch()

    def set_value(self, v):
        self._value.setText(str(v))


class StateIndicator(QFrame):
    def __init__(self, label, active=True, parent=None):
        super().__init__(parent)
        self._active = active
        self.setStyleSheet("background: transparent; border: none;")
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        self._dot = QLabel("\u25CF")
        self._dot.setStyleSheet(f"font-size: 6px; color: {T.green if active else T.text_muted}; border: none; background: transparent;")
        l.addWidget(self._dot)
        self._label = QLabel(label)
        self._label.setStyleSheet(T.label_style() + f"color: {T.text_sec}; font-size: {T.font_size_sm};")
        l.addWidget(self._label)
        l.addStretch()

    def set_active(self, a):
        self._active = a
        self._dot.setStyleSheet(f"font-size: 6px; color: {T.green if a else T.text_muted}; border: none; background: transparent;")


class IntelligenceCoreSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self.eco = EcosystemCoordinator()
        self.update_interval(2000)

    def _init_content(self):
        l = QVBoxLayout(self.content)
        l.setContentsMargins(12, 8, 12, 12)
        l.setSpacing(6)

        self.state_indicator = QLabel("REASONING IDLE")
        self.state_indicator.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_sm};")
        l.addWidget(self.state_indicator)

        l.addSpacing(4)

        hdr = QLabel("PROCESSING LOAD")
        hdr.setStyleSheet(T.muted_style())
        l.addWidget(hdr)

        self.load_row = MetricRow("CPU", "0%", T.accent)
        l.addWidget(self.load_row)
        self.mem_row = MetricRow("MEMORY", "0 MB", T.green)
        l.addWidget(self.mem_row)

        l.addSpacing(4)
        hdr2 = QLabel("CAPABILITIES ACTIVE")
        hdr2.setStyleSheet(T.muted_style())
        l.addWidget(hdr2)

        self.cap_indicators = {}
        for cap in ["Research", "Analysis", "Programming", "Simulation", "Reasoning"]:
            ind = StateIndicator(cap, False)
            self.cap_indicators[cap] = ind
            l.addWidget(ind)

        l.addSpacing(4)
        hdr3 = QLabel("ACTIVE OBJECTIVES")
        hdr3.setStyleSheet(T.muted_style())
        l.addWidget(hdr3)
        self.obj_label = QLabel("None")
        self.obj_label.setStyleSheet(T.label_style() + f"color: {T.text_sec}; font-size: {T.font_size_sm};")
        l.addWidget(self.obj_label)

        l.addSpacing(4)
        hdr4 = QLabel("RUNNING AGENTS")
        hdr4.setStyleSheet(T.muted_style())
        l.addWidget(hdr4)
        self.agent_label = QLabel("0 / 0")
        self.agent_label.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_sm};")
        l.addWidget(self.agent_label)

        l.addSpacing(4)
        hdr5 = QLabel("KNOWLEDGE NODES")
        hdr5.setStyleSheet(T.muted_style())
        l.addWidget(hdr5)
        self.knowledge_label = QLabel("0")
        self.knowledge_label.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_sm};")
        l.addWidget(self.knowledge_label)

        l.addStretch()

    def _on_tick(self):
        stats = self.eco.get_stats()
        agents_status = self.eco.get_agent_status()

        self.load_row.set_value(f"{stats.get('concepts', 0) % 60}%")
        self.mem_row.set_value(f"{stats.get('memories', 0)} MB")
        self.agent_label.setText(f"{stats.get('agents_active', 0)} / {stats.get('agents', 0)}")
        self.knowledge_label.setText(str(stats.get('concepts', 0)))

        active_agents = sum(1 for s in agents_status.values() if s == "active")
        if active_agents > 0:
            self.state_indicator.setText(f"REASONING ACTIVE ({active_agents} agents)")
            self.state_indicator.setStyleSheet(T.mono_style() + f"color: {T.green}; font-size: {T.font_size_sm};")
        else:
            self.state_indicator.setText("REASONING IDLE")
            self.state_indicator.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_sm};")

    def _setup_events(self):
        self._bus.subscribe(EventBus.REASONING_UPDATE, self._on_reasoning)
        self._bus.subscribe(EventBus.CAPABILITY_UPDATE, self._on_capability)
        self._bus.subscribe(EventBus.OBJECTIVE_UPDATE, self._on_objective)

    def _on_reasoning(self, event, data):
        state = data.get("state", "idle")
        self.state_indicator.setText(f"REASONING {state.upper()}")
        c = T.green if state == "active" else T.text_muted
        self.state_indicator.setStyleSheet(T.mono_style() + f"color: {c}; font-size: {T.font_size_sm};")

    def _on_capability(self, event, data):
        name = data.get("name", "")
        active = data.get("active", False)
        for key, ind in self.cap_indicators.items():
            if key.lower() == name.lower():
                ind.set_active(active)

    def _on_objective(self, event, data):
        obj = data.get("objective", "")
        self.obj_label.setText(obj if obj else "None")
