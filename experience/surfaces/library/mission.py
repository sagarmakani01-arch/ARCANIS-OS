from PySide6.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QFrame, QProgressBar
from PySide6.QtCore import Qt

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus
from experience.ecosystem import EcosystemCoordinator


class SubtaskRow(QFrame):
    def __init__(self, name, status="pending", parent=None):
        super().__init__(parent)
        self._status = status
        self.setStyleSheet("background: transparent; border: none;")
        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        self.dot = QLabel("\u25CF")
        self._update_dot()
        l.addWidget(self.dot)
        self.label = QLabel(name)
        self.label.setStyleSheet(T.label_style() + f"color: {T.text}; font-size: {T.font_size_sm};")
        l.addWidget(self.label)
        l.addStretch()

    def _update_dot(self):
        color_map = {"pending": T.text_muted, "active": T.accent, "done": T.green, "failed": T.red}
        c = color_map.get(self._status, T.text_muted)
        self.dot.setStyleSheet(f"font-size: 10px; color: {c}; border: none; background: transparent;")

    def set_status(self, s):
        self._status = s
        self._update_dot()


class MissionSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)
        self.eco = EcosystemCoordinator()
        self.subtask_rows = {}
        self.update_interval(3000)

    def _init_content(self):
        l = QVBoxLayout(self.content)
        l.setContentsMargins(12, 8, 12, 12)
        l.setSpacing(6)

        self.mission_label = QLabel("No active mission")
        self.mission_label.setStyleSheet(T.label_style() + f"font-size: {T.font_size_lg}; color: {T.text};")
        l.addWidget(self.mission_label)

        l.addSpacing(4)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ background: {T.surface_alt}; border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {T.accent}; border-radius: 2px; }}
        """)
        l.addWidget(self.progress_bar)

        l.addSpacing(6)
        hdr = QLabel("PROJECTS")
        hdr.setStyleSheet(T.muted_style())
        l.addWidget(hdr)

        self.projects_container = QVBoxLayout()
        self.projects_container.setSpacing(4)
        l.addLayout(self.projects_container)

        l.addSpacing(6)
        hdr2 = QLabel("TASKS")
        hdr2.setStyleSheet(T.muted_style())
        l.addWidget(hdr2)

        self.tasks_container = QVBoxLayout()
        self.tasks_container.setSpacing(3)
        l.addLayout(self.tasks_container)

        l.addSpacing(4)
        hdr3 = QLabel("STATISTICS")
        hdr3.setStyleSheet(T.muted_style())
        l.addWidget(hdr3)
        self.stats_label = QLabel("--")
        self.stats_label.setStyleSheet(T.mono_style() + f"font-size: {T.font_size_sm};")
        l.addWidget(self.stats_label)

        self._refresh_projects()
        l.addStretch()

    def _refresh_projects(self):
        for i in reversed(range(self.projects_container.count())):
            w = self.projects_container.itemAt(i).widget()
            if w:
                w.deleteLater()
        for i in reversed(range(self.tasks_container.count())):
            w = self.tasks_container.itemAt(i).widget()
            if w:
                w.deleteLater()

        projects = self.eco.get_projects()
        if not projects:
            self.mission_label.setText("No active projects")
            self.stats_label.setText("0 projects")
            return

        p = projects[0]
        self.mission_label.setText(p["name"])
        self.mission_label.setStyleSheet(T.label_style() + f"font-size: {T.font_size_lg}; color: {T.accent};")

        tasks = self.eco.get_tasks(p["id"])
        done = sum(1 for t in tasks if t["status"] == "completed")
        total = len(tasks)
        pct = int((done / total * 100)) if total > 0 else 0
        self.progress_bar.setValue(pct)

        for proj in projects[:3]:
            lbl = QLabel(f"  {proj['name']}  ({proj['status']})")
            lbl.setStyleSheet(T.label_style() + f"color: {T.text}; font-size: {T.font_size_sm};")
            self.projects_container.addWidget(lbl)

        for task in tasks[:6]:
            row = SubtaskRow(task["title"], task["status"])
            self.subtask_rows[task["title"]] = row
            self.tasks_container.addWidget(row)

        stats = self.eco.get_stats()
        self.stats_label.setText(f"{stats.get('projects', 0)} projects  \u00B7  {stats.get('tasks', 0)} tasks  \u00B7  {done}/{total} done")

    def _on_tick(self):
        self._refresh_projects()

    def _setup_events(self):
        self._bus.subscribe(EventBus.MISSION_UPDATE, self._on_mission)
        self._bus.subscribe(EventBus.TASK_UPDATE, self._on_task)

    def _on_mission(self, event, data):
        self._refresh_projects()

    def _on_task(self, event, data):
        name = data.get("name", "")
        status = data.get("status", "")
        for n, row in self.subtask_rows.items():
            if n.lower() == name.lower():
                row.set_status(status)
