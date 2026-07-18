from PySide6.QtWidgets import QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QFrame
from PySide6.QtCore import Qt

from ..framework.base import BaseSurface, SurfaceState, SurfaceFlags
from ..framework.theme import SurfaceTheme as T
from ..framework.event_bus import EventBus


class ProjectExplorerSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)

    def _init_content(self):
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setAnimated(True)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                outline: none;
                font-size: {T.font_size_sm}px;
                color: {T.text.name()};
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-radius: 0px;
            }}
            QTreeWidget::item:hover {{
                background: {T.surface_alt.name()};
            }}
            QTreeWidget::item:selected {{
                background: {T.accent_bg.name()};
                color: {T.accent.name()};
            }}
        """)

        missions = QTreeWidgetItem(["MISSIONS"])
        missions.setExpanded(True)
        m1 = QTreeWidgetItem(["System Architecture"])
        m2 = QTreeWidgetItem(["Surface Framework"])
        missions.addChildren([m1, m2])

        projects = QTreeWidgetItem(["PROJECTS"])
        projects.setExpanded(True)
        p1 = QTreeWidgetItem(["Core Engine"])
        p2 = QTreeWidgetItem(["Experience Layer"])
        p3 = QTreeWidgetItem(["Agent System"])
        projects.addChildren([p1, p2, p3])

        modules = QTreeWidgetItem(["MODULES"])
        modules.setExpanded(False)
        mods = ["Event Bus", "Knowledge Graph", "Memory System",
                "Capability Manager", "Workspace Controller"]
        for m in mods:
            modules.addChild(QTreeWidgetItem([m]))

        knowledge = QTreeWidgetItem(["KNOWLEDGE"])
        knowledge.setExpanded(False)
        k1 = QTreeWidgetItem(["Architecture Docs"])
        k2 = QTreeWidgetItem(["API Reference"])
        k3 = QTreeWidgetItem(["Research Notes"])
        knowledge.addChildren([k1, k2, k3])

        self.tree.addTopLevelItems([missions, projects, modules, knowledge])

        header = QTreeWidgetItem(["ARCANIS"])
        self.tree.setStyleSheet(self.tree.styleSheet() +
            "QTreeWidget::item:!has-children { padding-left: 24px; }")

        layout.addWidget(self.tree)

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setForeground(0, T.text_sec)
            font = item.font(0)
            font.setBold(True)
            font.setPixelSize(T.font_size_xs)
            item.setFont(0, font)
