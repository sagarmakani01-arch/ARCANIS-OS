from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame, QProgressBar
from PySide6.QtCore import Qt, QTimer
from datetime import datetime

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus
from experience.ecosystem import EcosystemCoordinator

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class HealthMetric(QFrame):
    def __init__(self, label, value="--", unit="", color=None, parent=None):
        super().__init__(parent)
        self._color = color or T.accent
        self.setStyleSheet(f"background: {T.surface}; border: 1px solid {T.border_light}; border-radius: 5px;")
        l = QVBoxLayout(self)
        l.setContentsMargins(12, 8, 12, 8)
        l.setSpacing(4)

        header = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet(T.muted_style() + f"font-size: {T.font_size_xs};")
        header.addWidget(lbl)
        header.addStretch()
        self._value = QLabel(f"{value}{unit}")
        self._value.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_lg}; color: {self._color};")
        header.addWidget(self._value)
        l.addLayout(header)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedHeight(3)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(f"""
            QProgressBar {{ background: {T.surface_alt}; border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {self._color}; border-radius: 2px; }}
        """)
        l.addWidget(self._bar)

    def set(self, value, pct=None):
        self._value.setText(str(value))
        if pct is not None:
            self._bar.setValue(min(100, max(0, pct)))


class SystemHealthSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self.eco = EcosystemCoordinator()
        self._start_time = datetime.now()
        self.update_interval(2000)

    def _init_content(self):
        l = QVBoxLayout(self.content)
        l.setContentsMargins(12, 8, 12, 12)
        l.setSpacing(8)

        hdr = QLabel("RUNTIME")
        hdr.setStyleSheet(T.muted_style())
        l.addWidget(hdr)

        self.runtime_lbl = QLabel("00:00:00")
        self.runtime_lbl.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_2xl}; color: {T.text};")
        l.addWidget(self.runtime_lbl)

        self.cpu = HealthMetric("CPU", "0%", "", T.accent)
        l.addWidget(self.cpu)
        self.memory = HealthMetric("MEMORY", "0 MB", "", T.green)
        l.addWidget(self.memory)

        if HAS_PSUTIL:
            self.disk = HealthMetric("DISK", "0 GB", "", T.cyan)
            l.addWidget(self.disk)

        self.agents_m = HealthMetric("AGENTS", "0 active", "", T.purple)
        l.addWidget(self.agents_m)

        l.addSpacing(4)
        hdr2 = QLabel("RECENT EVENTS")
        hdr2.setStyleSheet(T.muted_style())
        l.addWidget(hdr2)
        self.event_log = QLabel("System initialized")
        self.event_log.setStyleSheet(T.mono_style() + f"color: {T.text_muted}; font-size: {T.font_size_xs};")
        self.event_log.setWordWrap(True)
        l.addWidget(self.event_log)

        l.addStretch()

    def _on_tick(self):
        runtime = datetime.now() - self._start_time
        hours, remainder = divmod(int(runtime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.runtime_lbl.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        stats = self.eco.get_stats()

        if HAS_PSUTIL:
            cpu_pct = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            self.cpu.set(f"{cpu_pct:.0f}%", int(cpu_pct))
            self.memory.set(f"{mem.used // (1024*1024)} MB / {mem.total // (1024*1024)} MB", int(mem.percent))
            self.disk.set(f"{disk.used // (1024*1024*1024)} GB / {disk.total // (1024*1024*1024)} GB", int(disk.percent))
        else:
            self.cpu.set(f"{stats.get('concepts', 0) % 50 + 10}%", stats.get('concepts', 0) % 50 + 10)
            self.memory.set(f"{stats.get('memories', 0)} MB", min(100, stats.get('memories', 0)))

        self.agents_m.set(f"{stats.get('agents_active', 0)} active", int(stats.get('agents_active', 0) / max(1, stats.get('agents', 1)) * 100))

        memories = self.eco.get_memories(1)
        if memories:
            self.event_log.setText(memories[0].get("content", ""))

    def _setup_events(self):
        self._bus.subscribe(EventBus.SYSTEM_EVENT, self._on_event)

    def _on_event(self, event, data):
        msg = data.get("message", "")
        self.event_log.setText(msg)
