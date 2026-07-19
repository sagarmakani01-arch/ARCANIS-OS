import sys
import os
import subprocess
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGridLayout, QScrollArea,
    QTextEdit, QLineEdit, QDialog, QSizePolicy, QToolButton,
    QTreeView, QListView, QStackedWidget, QListWidget, QListWidgetItem,
    QSplitter, QTabWidget, QProgressBar, QGroupBox,
    QHeaderView, QStatusBar, QMenu, QSystemTrayIcon, QStyle,
)
from PySide6.QtCore import (
    Qt, QTimer, QProcess, Signal, QSize, QRect, QDir, QPoint,
    QFileSystemWatcher, QStringListModel, QModelIndex,
    QPropertyAnimation, QEasingCurve,
)
from PySide6.QtGui import (
    QFont, QColor, QPalette, QAction, QIcon, QFontDatabase,
    QPainter, QPen, QBrush, QLinearGradient,
)
from PySide6.QtWidgets import QFileSystemModel

from experience.ecosystem import EcosystemCoordinator


# ── Premium SaaS Color Palette ──────────────────────────────────────
C = {
    "bg": "#f1f3f5",
    "surface": "#ffffff",
    "hover": "#eef1f6",
    "active": "#e4e9f2",
    "border": "#dcdfe6",
    "border_focus": "#3b82f6",
    "text": "#0f1724",
    "text_sec": "#475569",
    "text_tert": "#94a3b8",
    "accent": "#3b82f6",
    "accent_bg": "#eff6ff",
    "accent2": "#6366f1",
    "accent_dark": "#2563eb",
    "sidebar": "#0f1117",
    "sidebar_hover": "#1e2028",
    "sidebar_active": "#2a2d38",
    "sidebar_text": "#8b8fa3",
    "sidebar_text_active": "#ffffff",
    "sidebar_accent": "#3b82f6",
    "cyan": "#06b6d4",
    "purple": "#8b5cf6",
    "amber": "#f59e0b",
    "emerald": "#10b981",
    "red": "#ef4444",
    "pink": "#ec4899",
    "green": "#22c55e",
    "surface_dark": "#f8f9fc",
    "border_light": "#e6e8ed",
}


# ── Global style sheet ──────────────────────────────────────────────
STYLE = f"""
QWidget {{
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: 12px;
}}
QScrollBar:vertical {{
    background: {C['bg']};
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {C['border_light']};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C['text_tert']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: {C['bg']};
    height: 6px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {C['border_light']};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {C['text_tert']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QToolTip {{
    background: {C['surface']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}}
QTreeView {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    outline: none;
    font-size: 12px;
}}
QTreeView::item {{
    padding: 4px 6px;
    border-radius: 3px;
}}
QTreeView::item:hover {{ background: {C['hover']}; }}
QTreeView::item:selected {{ background: {C['accent_bg']}; color: {C['accent']}; }}
QTreeView::branch {{ background: transparent; }}
QListView {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    outline: none;
    font-size: 12px;
}}
QListView::item {{
    padding: 6px 10px;
    border-radius: 3px;
}}
QListView::item:hover {{ background: {C['hover']}; }}
QListView::item:selected {{ background: {C['accent_bg']}; color: {C['accent']}; }}
QProgressBar {{
    background: {C['bg']};
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
    font-size: 9px;
}}
QProgressBar::chunk {{
    background: {C['accent']};
    border-radius: 3px;
}}
QTabWidget::pane {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    top: -1px;
}}
QTabBar::tab {{
    background: {C['bg']};
    color: {C['text_sec']};
    border: none;
    padding: 6px 16px;
    font-size: 11px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 2px;
}}
QTabBar::tab:hover {{ background: {C['hover']}; color: {C['text']}; }}
QTabBar::tab:selected {{ background: {C['surface']}; color: {C['accent']}; font-weight: 600; }}
QGroupBox {{
    font-size: 11px;
    font-weight: 600;
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 14px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}}
QStatusBar {{
    background: {C['surface']};
    border-top: 1px solid {C['border']};
    font-size: 11px;
    color: {C['text_sec']};
}}
"""


# ── Ecosystem Bar (top) ─────────────────────────────────────────────
# ── Premium SaaS Header ──────────────────────────────────────────────
class Header(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            Header {{
                background: {C['surface']};
                border-bottom: 1px solid {C['border']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Breadcrumb-style branding
        brand = QLabel("\u26A1 ARCANIS")
        brand.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {C['text']}; letter-spacing: 0.3px; border: none;")
        layout.addWidget(brand)

        sep = QLabel("|")
        sep.setStyleSheet(f"font-size: 10px; color: {C['border_light']}; border: none;")
        layout.addWidget(sep)

        plan = QLabel("Enterprise")
        plan.setStyleSheet(f"""
            font-size: 9px; font-weight: 600; color: {C['accent']};
            background: {C['accent_bg']}; padding: 2px 8px;
            border-radius: 4px; border: none;
        """)
        layout.addWidget(plan)

        layout.addSpacing(24)

        # Zone pills
        for zone in ["cognitive", "knowledge", "agent", "mission", "creation", "system"]:
            lbl = QLabel(zone.upper())
            lbl.setStyleSheet(f"font-size: 9px; font-weight: 500; color: {C['text_tert']}; letter-spacing: 0.8px; border: none;")
            lbl.setCursor(Qt.PointingHandCursor)
            layout.addWidget(lbl)
            layout.addSpacing(10)

        layout.addStretch()

        # Global search
        search = QLineEdit()
        search.setPlaceholderText("Search ecosystem \u2026")
        search.setFixedWidth(200)
        search.setFixedHeight(26)
        search.setStyleSheet(f"""
            QLineEdit {{
                background: {C['bg']}; border: 1px solid {C['border_light']}; border-radius: 5px;
                font-size: 11px; padding: 0 10px; color: {C['text']};
            }}
            QLineEdit::placeholder {{ color: {C['text_tert']}; }}
        """)
        layout.addWidget(search)

        layout.addSpacing(8)

        # Status indicators
        for icon, tip in [("\u25CF", "All systems operational"), ("\U0001F514", "Notifications"), ("\u2699", "Settings")]:
            btn = QToolButton()
            btn.setText(icon)
            btn.setToolTip(tip)
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background: transparent; border: none; border-radius: 5px;
                    font-size: 13px; color: {C['text_tert']};
                }}
                QToolButton:hover {{ background: {C['hover']}; color: {C['text']}; }}
            """)
            layout.addWidget(btn)

        layout.addSpacing(4)

        # User avatar
        avatar = QLabel("SA")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background: {C['accent']}; color: white; border: none;
            border-radius: 14px; font-size: 10px; font-weight: 700;
        """)
        avatar.setToolTip("Sagar Makani")
        layout.addWidget(avatar)

        layout.addSpacing(4)
        self.clock = QLabel()
        self.clock.setStyleSheet(f"font-size: 11px; color: {C['text_sec']}; font-weight: 500; border: none;")
        self.update_clock()
        layout.addWidget(self.clock)

        self._parent_window = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

    def bind_window(self, window):
        self._parent_window = window

    def update_clock(self):
        self.clock.setText(datetime.now().strftime("%H:%M"))

    def update_stats(self, text):
        """Update the live stats label in the header."""
        pass  # Header doesn't have a stats label currently; integrated into status bar


# ── Ecosystem Zone Card ─────────────────────────────────────────────
class ZoneCard(QFrame):
    clicked = Signal(str)

    def __init__(self, zone_id, label, subtitle, accent=C["accent"]):
        super().__init__()
        self.zone_id = zone_id
        self.setFixedSize(180, 72)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            ZoneCard {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-left: 3px solid {accent};
            }}
            ZoneCard:hover {{
                background: {C['hover']};
                border-color: {accent};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        name = QLabel(label.upper())
        name.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {C['text']}; letter-spacing: 1px; border: none;")
        layout.addWidget(name)

        info = QLabel(subtitle)
        info.setStyleSheet(f"font-size: 9px; color: {C['text_tert']}; border: none;")
        layout.addWidget(info)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.zone_id)


# ── Ecosystem Dashboard (center) ────────────────────────────────────
class EcosystemDashboard(QWidget):
    zone_activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 12)
        layout.setSpacing(16)

        heading = QLabel("ECOSYSTEM DASHBOARD")
        heading.setStyleSheet(f"font-size: 20px; font-weight: 300; color: {C['text']}; letter-spacing: 2px;")
        layout.addWidget(heading)

        layout.addSpacing(4)

        grid = QHBoxLayout()
        grid.setSpacing(10)

        self.cards = {}
        zones = [
            ("cognitive",  "COGNITIVE",  "monitoring", C["accent"]),
            ("knowledge",  "KNOWLEDGE",  "ready", C["purple"]),
            ("agent",      "AGENT",      "online", C["cyan"]),
            ("mission",    "MISSION",    "active", C["emerald"]),
            ("creation",   "CREATION",   "tools ready", C["amber"]),
            ("system",     "SYSTEM",     "online", C["text_sec"]),
            ("terminal",   "TERMINAL",   "shell ready", C["pink"]),
            ("surfaces",   "SURFACES",   "workspace ready", C["accent"]),
        ]

        for zid, label, sub, accent in zones:
            card = ZoneCard(zid, label, sub, accent)
            card.clicked.connect(self.zone_activated.emit)
            self.cards[zid] = card
            grid.addWidget(card)

        layout.addLayout(grid)

        layout.addSpacing(20)

        info_row = QHBoxLayout()
        info_row.setSpacing(20)

        self.stat_boxes = {}
        for label, value, color, key in [
            ("AGENTS ONLINE", "0/0", C["cyan"], "agents"),
            ("KNOWLEDGE NODES", "0", C["purple"], "concepts"),
            ("MEMORIES", "0", C["emerald"], "memories"),
            ("PROJECTS", "0", C["accent"], "projects"),
            ("TASKS", "0", C["text_sec"], "tasks"),
        ]:
            box = QFrame()
            box.setStyleSheet(f"background: {C['surface']}; border: 1px solid {C['border']};")
            box.setFixedHeight(48)
            bl = QVBoxLayout(box)
            bl.setContentsMargins(12, 6, 12, 6)
            bl.setSpacing(2)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 8px; color: {C['text_tert']}; letter-spacing: 1px; font-weight: 600; border: none;")
            vl = QLabel(value)
            vl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {color}; border: none;")
            bl.addWidget(lbl)
            bl.addWidget(vl)
            info_row.addWidget(box)
            self.stat_boxes[key] = vl

        layout.addLayout(info_row)
        layout.addStretch()

    def update_stats(self, stats):
        mapping = {
            "agents": f"{stats.get('agents_active', 0)}/{stats.get('agents', 0)}",
            "concepts": str(stats.get("concepts", 0)),
            "memories": str(stats.get("memories", 0)),
            "projects": str(stats.get("projects", 0)),
            "tasks": str(stats.get("tasks", 0)),
        }
        for key, val in mapping.items():
            if key in self.stat_boxes:
                self.stat_boxes[key].setText(val)


# ── SaaS Sidebar ────────────────────────────────────────────────────
class Sidebar(QFrame):
    zone_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet(f"""
            Sidebar {{
                background: {C['sidebar']};
                border-right: 1px solid #1e2028;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo area
        logo_area = QFrame()
        logo_area.setFixedHeight(52)
        logo_area.setStyleSheet(f"background: {C['sidebar']}; border: none;")
        lal = QHBoxLayout(logo_area)
        lal.setContentsMargins(16, 0, 16, 0)
        logo = QLabel("\u26A1")
        logo.setStyleSheet(f"font-size: 18px; border: none; color: {C['sidebar_accent']};")
        lal.addWidget(logo)
        lal.addSpacing(6)
        name = QLabel("ARCANIS")
        name.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {C['sidebar_text_active']}; letter-spacing: 0.5px; border: none;")
        lal.addWidget(name)
        lal.addStretch()
        badge = QLabel("v14")
        badge.setStyleSheet(f"font-size: 9px; color: {C['sidebar_text']}; border: none;")
        lal.addWidget(badge)
        layout.addWidget(logo_area)

        # Nav section header
        nav_header = QLabel("  WORKSPACES")
        nav_header.setFixedHeight(28)
        nav_header.setStyleSheet(f"font-size: 8px; font-weight: 600; color: {C['sidebar_text']}; letter-spacing: 1.2px; border: none; padding-left: 16px;")
        layout.addWidget(nav_header)

        self.nav_buttons = {}
        nav_items = [
            ("ecosystem", "\u26A1", "Ecosystem Dashboard"),
            ("cognitive", "\u2B50", "Cognitive Core"),
            ("knowledge", "\U0001F4DA", "Knowledge Graph"),
            ("agent", "\U0001F916", "Agent Network"),
            ("mission", "\U0001F3AF", "Mission Control"),
            ("creation", "\U0001F527", "Creation Tools"),
            ("system", "\u2699", "System Monitor"),
            ("terminal", "\u2328", "Terminal"),
            ("surfaces", "\u25C7", "Intelligence Surfaces"),
        ]
        for nid, icon, tip in nav_items:
            btn = QToolButton()
            btn.setText(f"  {icon}  {tip.split(' (')[0]}")
            btn.setToolTip(tip)
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background: transparent; border: none; border-radius: 0px;
                    font-size: 11px; color: {C['sidebar_text']}; text-align: left;
                    padding: 0 16px;
                }}
                QToolButton:hover {{ background: {C['sidebar_hover']}; color: {C['sidebar_text_active']}; }}
            """)
            btn.clicked.connect(lambda checked, a=nid: self.zone_selected.emit(a))
            self.nav_buttons[nid] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Bottom section
        bottom = QFrame()
        bottom.setStyleSheet(f"background: {C['sidebar']}; border: none; border-top: 1px solid #1e2028;")
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(16, 8, 16, 8)
        bl.setSpacing(4)

        user = QLabel("SA  Sagar Makani")
        user.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {C['sidebar_text_active']}; border: none;")
        bl.addWidget(user)
        role = QLabel("Enterprise Plan")
        role.setStyleSheet(f"font-size: 9px; color: {C['sidebar_accent']}; border: none;")
        bl.addWidget(role)

        status_row = QHBoxLayout()
        status_row.setSpacing(4)
        dot = QLabel("\u25CF")
        dot.setStyleSheet(f"font-size: 8px; color: {C['green']}; border: none;")
        status_row.addWidget(dot)
        status_text = QLabel("All systems operational")
        status_text.setStyleSheet(f"font-size: 9px; color: {C['sidebar_text']}; border: none;")
        status_row.addWidget(status_text)
        status_row.addStretch()
        bl.addLayout(status_row)

        layout.addWidget(bottom)

    def highlight(self, zone_id):
        for nid, btn in self.nav_buttons.items():
            btn.setStyleSheet(f"""
                QToolButton {{
                    background: {C['sidebar_active'] if nid == zone_id else 'transparent'};
                    border: none; border-radius: 0px;
                    font-size: 11px; color: {C['sidebar_text_active'] if nid == zone_id else C['sidebar_text']};
                    text-align: left; padding: 0 16px;
                    border-left: 2px solid {C['sidebar_accent'] if nid == zone_id else 'transparent'};
                }}
                QToolButton:hover {{ background: {C['sidebar_hover']}; color: {C['sidebar_text_active']}; }}
            """)


# ── Command Bar (bottom) ────────────────────────────────────────────
class CommandBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            CommandBar {{
                background: {C['surface']};
                border-top: 1px solid {C['border']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        prompt = QLabel("\u25B6")
        prompt.setStyleSheet(f"font-size: 10px; color: {C['accent']};")
        layout.addWidget(prompt)

        self.input = QLineEdit()
        self.input.setPlaceholderText("query ecosystem \u2026")
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none; font-size: 11px;
                color: {C['text']}; font-family: 'Segoe UI', sans-serif;
            }}
            QLineEdit::placeholder {{ color: {C['text_tert']}; }}
        """)
        layout.addWidget(self.input, 1)

        self.info = QLabel("agents: 3  \u00B7  kn: 24  \u00B7  mem: 128mb  \u00B7  cap: 6")
        self.info.setStyleSheet(f"font-size: 9px; color: {C['text_tert']}; letter-spacing: 0.3px;")
        layout.addWidget(self.info)


# ── File System Browser ─────────────────────────────────────────────
class FileBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(32)
        toolbar.setStyleSheet(f"background: {C['bg']}; border-bottom: 1px solid {C['border']};")
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(8, 0, 8, 0)
        tl.setSpacing(4)

        btn_style = f"""
            QToolButton {{
                background: transparent; border: 1px solid {C['border_light']}; border-radius: 3px;
                font-size: 10px; color: {C['text_sec']}; padding: 2px 8px;
            }}
            QToolButton:hover {{ background: {C['hover']}; color: {C['text']}; }}
        """
        for text, tip in [("\U0001F4C4", "New File"), ("\U0001F4C1", "New Folder"), ("\u2716", "Delete"), ("\u270F", "Rename"), ("\u23CE", "Open")]:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolTip(tip)
            btn.setStyleSheet(btn_style)
            tl.addWidget(btn)

        tl.addStretch()
        self.path_lbl = QLabel(QDir.homePath())
        self.path_lbl.setStyleSheet(f"font-size: 10px; color: {C['text_tert']}; border: none;")
        tl.addWidget(self.path_lbl)
        layout.addWidget(toolbar)

        # File tree
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.homePath()))
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setSortingEnabled(True)
        self.tree.setHeaderHidden(False)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.setColumnWidth(1, 80)
        self.tree.setColumnWidth(2, 60)
        self.tree.setColumnWidth(3, 100)
        self.tree.setAlternatingRowColors(False)
        self.tree.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree.setDragDropMode(QTreeView.DragDrop)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.tree.doubleClicked.connect(self._open_item)

        layout.addWidget(self.tree, 1)

    def _context_menu(self, pos):
        idx = self.tree.indexAt(pos)
        path = self.model.filePath(idx) if idx.isValid() else QDir.homePath()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {C['surface']}; border: 1px solid {C['border']}; padding: 4px; }}
            QMenu::item {{ padding: 6px 20px; font-size: 11px; border-radius: 3px; }}
            QMenu::item:hover {{ background: {C['hover']}; }}
        """)
        act_open = QAction("\u23CE  Open", self)
        act_open.triggered.connect(lambda: self._open_path(path))
        menu.addAction(act_open)

        act_term = QAction("\u2328  Open in Terminal", self)
        act_term.triggered.connect(lambda: subprocess.Popen(f'start wt -d "{path}"', shell=True))
        menu.addAction(act_term)

        menu.addSeparator()
        act_copy = QAction("\U0001F4CB  Copy Path", self)
        act_copy.triggered.connect(lambda: self._copy_path(path))
        menu.addAction(act_copy)

        act_del = QAction("\u2716  Delete", self)
        act_del.triggered.connect(lambda: self._delete_path(path))
        menu.addAction(act_del)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _open_path(self, path):
        if os.path.isdir(path):
            self.tree.setRootIndex(self.model.index(path))
            self.path_lbl.setText(path)
        else:
            os.startfile(path)

    def _open_item(self, idx):
        path = self.model.filePath(idx)
        self._open_path(path)

    def _copy_path(self, path):
        from PySide6.QtGui import QClipboard
        QApplication.clipboard().setText(path)

    def _delete_path(self, path):
        try:
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as e:
            pass


# ── Terminal ────────────────────────────────────────────────────────
class TerminalWidget(QWidget):
    pa_killed = Signal()

    def __init__(self, parent=None, kill_mode=False):
        super().__init__(parent)
        self.kill_mode = kill_mode
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # PA mode kill banner
        if kill_mode:
            banner = QFrame()
            banner.setFixedHeight(32)
            banner.setStyleSheet(f"background: {C['amber']}; border: none;")
            bl = QHBoxLayout(banner)
            bl.setContentsMargins(12, 0, 12, 0)
            icon = QLabel("\u26A0\uFE0F")
            icon.setStyleSheet(f"font-size: 12px; border: none; color: white;")
            bl.addWidget(icon)
            text = QLabel("Personal Assistant mode active  \u2014  Enter command below to terminate")
            text.setStyleSheet(f"font-size: 10px; color: white; font-weight: 600; border: none;")
            bl.addWidget(text)
            layout.addWidget(banner)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background: {C['terminal_bg'] if hasattr(C, 'terminal_bg') else '#ffffff'};
                color: {C['text']};
                border: none;
                font-family: "Cascadia Code", Consolas, monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)
        self.output.setLineWrapMode(QTextEdit.NoWrap)
        self.output.append("<span style='color:#999'>ARCANIS OS Terminal [v14.0.0]</span>")
        if kill_mode:
            self.output.append("<span style='color:#e67e22'>\u26A0\uFE0F  Personal Assistant mode is active. Kill it with:  <b>arcanis-pa --kill</b></span>")
        else:
            self.output.append("<span style='color:#999'>Type 'help' for commands.</span>")

        input_row = QHBoxLayout()
        input_row.setContentsMargins(8, 4, 8, 8)

        self.prompt = QLabel("arcanis@os:~$ ")
        self.prompt.setStyleSheet(f"color: {C['accent']}; font-family: 'Cascadia Code', Consolas, monospace; font-size: 11px;")

        self.input = QLineEdit()
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: {C['text']};
                border: none;
                font-family: "Cascadia Code", Consolas, monospace;
                font-size: 11px;
            }}
        """)
        if kill_mode:
            self.input.setText("arcanis-pa --kill")
            self.input.selectAll()
        self.input.returnPressed.connect(self.execute)

        input_row.addWidget(self.prompt)
        input_row.addWidget(self.input, 1)

        layout.addWidget(self.output, 1)
        layout.addLayout(input_row)

        self.history = []
        self.history_index = -1

    def execute(self):
        cmd = self.input.text().strip()
        if not cmd:
            return

        self.output.append(f"<span style='color:{C['accent']}'>{cmd}</span>")
        self.history.append(cmd)
        self.history_index = len(self.history)

        parts = cmd.split()
        command = parts[0].lower()
        args = parts[1:]

        output = ""
        if command == "help":
            output = ("  help       Show this help<br>"
                      "  clear      Clear terminal<br>"
                      "  echo       Echo text<br>"
                      "  date       Show date/time<br>"
                      "  whoami     Show user<br>"
                      "  uname      OS info<br>"
                      "  ls         List files<br>"
                      "  exit       Close terminal")
        elif command == "clear":
            self.output.clear()
        elif command == "echo":
            output = " ".join(args)
        elif command == "date":
            output = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        elif command == "whoami":
            output = "arcanis"
        elif command == "uname":
            output = "ARCANIS OS v14.0.0 (build 2026) Windows x64"
        elif command == "exit":
            w = self.window()
            if w and hasattr(w, "close"):
                w.close()
            return
        elif command == "ls":
            output = "Desktop/  Documents/  Downloads/  Music/  Pictures/  Videos/  arc/"
        elif command in ("arcanis-pa", "pkill") and "--kill" in args:
            output = "Personal Assistant process terminated."
            self.pa_killed.emit()
            w = self.window()
            if w and hasattr(w, "close"):
                w.close()
            return
        else:
            output = f"Command not found: {command}"

        if output:
            self.output.append(output)
        self.input.clear()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            if self.history_index > 0:
                self.history_index -= 1
                self.input.setText(self.history[self.history_index])
        elif event.key() == Qt.Key_Down:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.input.setText(self.history[self.history_index])
            else:
                self.history_index = len(self.history)
                self.input.clear()
        super().keyPressEvent(event)


# ── Settings Panel ──────────────────────────────────────────────────
class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.nav = QListWidget()
        self.nav.setFixedWidth(160)
        self.nav.setStyleSheet(f"""
            QListWidget {{
                background: {C['bg']};
                border: none;
                border-right: 1px solid {C['border']};
                border-radius: 0;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                font-size: 11px;
                border-radius: 0;
            }}
            QListWidget::item:hover {{
                background: {C['hover']};
            }}
            QListWidget::item:selected {{
                background: {C['accent_bg']};
                color: {C['accent']};
            }}
        """)

        self.stack = QStackedWidget()

        self.pages = {
            "General": self._make_page("General Settings", [
                ("Startup", "Launch ARCANIS on boot"),
                ("Theme", "Light (default)"),
                ("Language", "English (US)"),
            ]),
            "Appearance": self._make_page("Appearance", [
                ("Accent Color", "Blue #0066cc"),
                ("Font Size", "System default"),
                ("Transparency Effects", "Enabled"),
            ]),
            "Terminal": self._make_page("Terminal", [
                ("Shell", "PowerShell"),
                ("Font", "Cascadia Code"),
                ("Font Size", "11px"),
                ("Scrollback", "10000 lines"),
            ]),
            "System": self._make_page("System", [
                ("Version", "v14.0.0"),
                ("Build", "2026"),
                ("Modules", "126"),
                ("Commands", "278"),
            ]),
        }

        for name in self.pages:
            item = QListWidgetItem(name)
            self.nav.addItem(item)

        self.stack.addWidget(self.pages["General"])
        self.stack.addWidget(self.pages["Appearance"])
        self.stack.addWidget(self.pages["Terminal"])
        self.stack.addWidget(self.pages["System"])

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)

        layout.addWidget(self.nav)
        layout.addWidget(self.stack, 1)

    def _make_page(self, title, items):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 20, 20, 20)
        l.setSpacing(12)

        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {C['text']};")
        l.addWidget(lbl)

        for label, value in items:
            gb = QGroupBox(label)
            gbl = QVBoxLayout(gb)
            gbl.setContentsMargins(10, 16, 10, 10)
            vl = QLabel(value)
            vl.setStyleSheet(f"font-size: 11px; color: {C['text_sec']};")
            gbl.addWidget(vl)
            l.addWidget(gb)

        l.addStretch()
        return w


# ── System Monitor ──────────────────────────────────────────────────
class SystemMonitor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        info = [
            ("ARCANIS OS v14.0.0", True),
            ("", False),
            ("Kernel:", "Windows NT 10.0"),
            ("Build:", "2026"),
            ("Modules Active:", "126"),
            ("Commands Registered:", "278"),
            ("Memory:", "16 GB"),
        ]

        for label, value in info:
            if isinstance(value, bool) and value:
                lbl = QLabel(label)
                lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {C['text']};")
                layout.addWidget(lbl)
            elif label == "":
                layout.addSpacing(4)
            else:
                row = QHBoxLayout()
                row.setSpacing(12)
                lbl = QLabel(label)
                lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {C['text']};")
                lbl.setFixedWidth(130)
                vl = QLabel(str(value))
                vl.setStyleSheet(f"font-size: 11px; color: {C['text_sec']};")
                row.addWidget(lbl)
                row.addWidget(vl, 1)
                layout.addLayout(row)

        # CPU usage bar
        layout.addSpacing(8)
        cpu_lbl = QLabel("CPU Usage")
        cpu_lbl.setStyleSheet(f"font-size: 11px; color: {C['text']};")
        layout.addWidget(cpu_lbl)

        cpu_bar = QProgressBar()
        cpu_bar.setValue(27)
        layout.addWidget(cpu_bar)

        # Memory bar
        mem_lbl = QLabel("Memory Usage")
        mem_lbl.setStyleSheet(f"font-size: 11px; color: {C['text']};")
        layout.addWidget(mem_lbl)

        mem_bar = QProgressBar()
        mem_bar.setValue(43)
        layout.addWidget(mem_bar)

        layout.addStretch()


# ── Title Bar with working controls ────────────────────────────────
class TitleBar(QFrame):
    def __init__(self, title, close_fn, hide_fn, max_fn, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            TitleBar {{
                background: {C['surface']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid {C['border']};
            }}
        """)
        self._close_fn = close_fn
        self._hide_fn = hide_fn
        self._max_fn = max_fn
        self._drag_pos = None
        self._maximized = False
        self._window = parent

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        btn_style = f"""
            QToolButton {{
                background: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px 6px;
                color: {C['text_sec']};
            }}
            QToolButton:hover {{
                background: {C['hover']};
                border: 1px solid {C['accent']};
                color: {C['text']};
            }}
        """

        for symbol, tip, action in [
            ("\u2014", "Minimize", self._hide_fn),
            ("\u25A1", "Maximize", self._max_fn),
            ("\u2715", "Close", self._close_fn),
        ]:
            btn = QToolButton(self)
            btn.setText(symbol)
            btn.setToolTip(tip)
            btn.setFixedHeight(22)
            btn.setCursor(Qt.ArrowCursor)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(action)
            layout.addWidget(btn)

        self.title_lbl = QLabel(title, self)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet(f"color: {C['text']}; font-size: 11px; border: none;")
        layout.addWidget(self.title_lbl, 1)

        spacer = QLabel(self)
        spacer.setFixedWidth(80)
        layout.addWidget(spacer)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.position().toPoint())
            if not isinstance(child, QToolButton):
                self._drag_pos = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
                self._maximized = self._window._maximized
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_pos and not self._maximized:
            self._window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        child = self.childAt(event.position().toPoint())
        if not isinstance(child, QToolButton):
            self._max_fn()
            event.accept()


class AppWindow(QMainWindow):
    def __init__(self, title, content_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._parent_desktop = parent

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(content_widget, 1)

        self.setStyleSheet(f"""
            AppWindow {{
                background: {C['surface']};
            }}
        """)

    def closeEvent(self, event):
        content = self.centralWidget()
        if content and hasattr(content, '_wm'):
            try:
                content._wm.save_on_exit()
            except Exception:
                pass
        if self._parent_desktop and hasattr(self._parent_desktop, '_on_window_closed'):
            self._parent_desktop._on_window_closed(self)
        super().closeEvent(event)


# ── Premium Desktop Icon ──────────────────────────────────────────
class DesktopIcon(QFrame):
    clicked = Signal(str)

    def __init__(self, icon, label, app_id, desc=""):
        super().__init__()
        self.app_id = app_id
        self.setFixedSize(88, 90)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(desc)
        self.setStyleSheet(f"""
            DesktopIcon {{
                background: {C['surface']};
                border: 1px solid {C['border_light']};
                border-radius: 8px;
            }}
            DesktopIcon:hover {{
                background: {C['hover']};
                border-color: {C['accent']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        ic = QLabel(icon)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"font-size: 26px; color: {C['text']}; border: none; background: transparent;")
        layout.addWidget(ic)

        name = QLabel(label)
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet(f"font-size: 9px; font-weight: 500; color: {C['text_sec']}; border: none; background: transparent;")
        layout.addWidget(name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.app_id)


# ── Personal Assistant Overlay ─────────────────────────────────────
class PersonalAssistantOverlay(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.setStyleSheet(f"background: {C['bg']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(16)

        # Top: Assistant branding
        top = QHBoxLayout()
        icon = QLabel("\u26A1")
        icon.setStyleSheet(f"font-size: 28px; border: none;")
        top.addWidget(icon)
        top.addSpacing(8)

        title = QLabel("Personal Assistant")
        title.setStyleSheet(f"font-size: 22px; font-weight: 300; color: {C['text']}; letter-spacing: 1px; border: none;")
        top.addWidget(title)
        top.addStretch()

        self.status_dot = QLabel("\u25CF")
        self.status_dot.setStyleSheet(f"font-size: 10px; color: {C['green']}; border: none;")
        top.addWidget(self.status_dot)
        self.status_text = QLabel("Listening")
        self.status_text.setStyleSheet(f"font-size: 11px; color: {C['text_sec']}; border: none;")
        top.addWidget(self.status_text)

        layout.addLayout(top)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {C['border']}; border: none;")
        layout.addWidget(sep)

        # Active tasks
        layout.addSpacing(8)
        tasks_header = QLabel("ACTIVE TASKS")
        tasks_header.setStyleSheet(f"font-size: 9px; font-weight: 600; color: {C['text_tert']}; letter-spacing: 1px; border: none;")
        layout.addWidget(tasks_header)
        layout.addSpacing(4)

        self.tasks_container = QVBoxLayout()
        self.tasks_container.setSpacing(6)
        sample_tasks = [
            ("\u25B6 Project Alpha analysis", "In progress", C['accent']),
            ("\u23F3 Code review queue", "Pending", C['amber']),
            ("\u2713 System diagnostics", "Complete", C['green']),
            ("\u25B6 Knowledge graph sync", "Processing", C['cyan']),
        ]
        for task, status, color in sample_tasks:
            row = QFrame()
            row.setStyleSheet(f"background: {C['surface']}; border: 1px solid {C['border_light']}; border-radius: 6px;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(12, 8, 12, 8)
            lbl = QLabel(task)
            lbl.setStyleSheet(f"font-size: 11px; color: {C['text']}; border: none;")
            rl.addWidget(lbl)
            rl.addStretch()
            st = QLabel(status)
            st.setStyleSheet(f"font-size: 9px; font-weight: 600; color: {color}; border: none;")
            rl.addWidget(st)
            self.tasks_container.addWidget(row)

        layout.addLayout(self.tasks_container)

        layout.addStretch()

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet(f"background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 8px;")
        il = QHBoxLayout(input_frame)
        il.setContentsMargins(16, 12, 16, 12)

        prompt = QLabel("\u25B6")
        prompt.setStyleSheet(f"font-size: 14px; color: {C['accent']}; border: none;")
        il.addWidget(prompt)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a command or ask anything \u2026")
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none; font-size: 13px;
                color: {C['text']}; font-family: 'Segoe UI', sans-serif;
            }}
            QLineEdit::placeholder {{ color: {C['text_tert']}; }}
        """)
        self.input.returnPressed.connect(self._handle_input)
        il.addWidget(self.input, 1)

        # Send button
        send_btn = QPushButton("\u2192")
        send_btn.setFixedSize(28, 28)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['accent']}; color: white; border: none;
                border-radius: 5px; font-size: 14px;
            }}
            QPushButton:hover {{ background: {C['accent2']}; }}
        """)
        send_btn.clicked.connect(self._handle_input)
        il.addWidget(send_btn)

        # Mic button for voice input
        self.mic_btn = QPushButton("\U0001F3A4")
        self.mic_btn.setFixedSize(28, 28)
        self.mic_btn.setCursor(Qt.PointingHandCursor)
        self.mic_btn.setToolTip("Voice input")
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C['text_sec']}; border: none;
                border-radius: 5px; font-size: 14px;
            }}
            QPushButton:hover {{ background: {C['hover']}; color: {C['text']}; }}
        """)
        self.mic_btn.clicked.connect(self._toggle_voice)
        il.addWidget(self.mic_btn)

        layout.addWidget(input_frame)
        layout.addSpacing(8)

        # Exit info
        info = QLabel("Open Terminal to exit Personal Assistant mode  \u00B7  or type:  arcanis-pa --kill")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(f"font-size: 10px; color: {C['text_tert']}; border: none;")
        layout.addWidget(info)

        layout.addSpacing(12)

        # Terminal button (only tool during PA mode)
        term_btn = QPushButton("  \u2328  Open Terminal  ")
        term_btn.setFixedHeight(32)
        term_btn.setCursor(Qt.PointingHandCursor)
        term_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['accent']}; color: white; border: none; border-radius: 6px;
                font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {C['accent2']}; }}
        """)
        term_btn.clicked.connect(self._open_terminal)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(term_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addSpacing(16)

        # Quick action buttons
        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addStretch()
        for icon, label, cmd in [
            ("\U0001F4CA", "System Stats", "stats"),
            ("\U0001F916", "List Agents", "agents"),
            ("\U0001F4DA", "Concepts", "search"),
            ("\U0001F4CB", "Projects", "projects"),
            ("\U0001F50D", "Search", "search "),
        ]:
            btn = QPushButton(f"{icon} {label}")
            btn.setFixedHeight(28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {C['surface']}; color: {C['text_sec']}; border: 1px solid {C['border_light']};
                    border-radius: 5px; font-size: 10px; padding: 0 10px;
                }}
                QPushButton:hover {{ background: {C['hover']}; border-color: {C['accent']}; }}
            """)
            def make_handler(c=cmd):
                return lambda: (setattr(self.input, 'text', c) if c.endswith(' ') else
                    (self.input.setText(c), self._handle_input()))
            btn.clicked.connect(lambda checked, c=cmd: self._quick_action(c))
            actions.addWidget(btn)
        actions.addStretch()
        layout.addLayout(actions)

        layout.addSpacing(40)

    def _handle_input(self):
        cmd = self.input.text().strip()
        if not cmd:
            return
        if cmd.lower() in ("arcanis-pa --kill", "kill", "exit", "quit"):
            self.desktop._exit_pa_mode()
            self.input.clear()
            return
        # Process through ecosystem coordinator
        result = self.desktop.eco.command(cmd)
        self.status_text.setText("Processing...")
        QTimer.singleShot(500, lambda: self._show_result(result, cmd))

    def _quick_action(self, cmd):
        if cmd.endswith(" "):
            self.input.setText(cmd)
            self.input.setFocus()
        else:
            self.input.setText(cmd)
            self._handle_input()

    def _show_result(self, result, original_cmd=""):
        self.status_text.setText("Listening")
        # Show result in status temporarily
        short = result[:80] + "..." if len(result) > 80 else result
        self.desktop.status_bar.status_text.setText(short)
        QTimer.singleShot(4000, lambda: self.desktop.status_bar.set_pa_mode(True))
        self.input.clear()

    def _open_terminal(self):
        self.desktop._handle_icon_click("terminal")

    # ── Voice Input ──────────────────────────────────────────────
    def _toggle_voice(self):
        if getattr(self, '_listening', False):
            self._listening = False
            self._reset_mic_ui()
        else:
            self._listening = True
            self.mic_btn.setText("\U0001F534")
            self.mic_btn.setToolTip("Listening...")
            self.mic_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {C['red']}; color: white; border: none;
                    border-radius: 5px; font-size: 14px;
                }}
                QPushButton:hover {{ background: #dc2626; }}
            """)
            self.status_text.setText("Voice input...")
            self.status_dot.setStyleSheet(f"font-size: 10px; color: {C['red']}; border: none;")
            threading.Thread(target=self._listen_voice, daemon=True).start()

    def _reset_mic_ui(self):
        self.mic_btn.setText("\U0001F3A4")
        self.mic_btn.setToolTip("Voice input" if self.mic_btn.isEnabled() else "Voice not available")
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C['text_sec']}; border: none;
                border-radius: 5px; font-size: 14px;
            }}
            QPushButton:hover {{ background: {C['hover']}; color: {C['text']}; }}
        """)
        self.status_text.setText("Listening")
        self.status_dot.setStyleSheet(f"font-size: 10px; color: {C['green']}; border: none;")

    def _on_voice_result(self, text):
        if text:
            self.input.setText(text)
            self.input.setFocus()
        self._listening = False
        QTimer.singleShot(0, self._reset_mic_ui)

    def _voice_not_available(self):
        self._listening = False
        QTimer.singleShot(0, lambda: self.mic_btn.setToolTip("Voice not available"))
        QTimer.singleShot(0, lambda: self.mic_btn.setEnabled(False))
        QTimer.singleShot(0, self._reset_mic_ui)

    def _listen_voice(self):
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.3)
                audio = r.listen(source, timeout=5)
            text = r.recognize_google(audio)
            QTimer.singleShot(0, lambda: self._on_voice_result(text))
            return
        except ImportError:
            pass
        except Exception:
            QTimer.singleShot(0, lambda: self._on_voice_result(""))
            return

        try:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                import win32com.client
                recognizer = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
                grammar = recognizer.CreateGrammar()
                grammar.DictationSetState(1)
                result = recognizer.Recognize()
                grammar.DictationSetState(0)
                if result:
                    text = result.PhraseInfo.GetText()
                    QTimer.singleShot(0, lambda t=text: self._on_voice_result(t))
                else:
                    QTimer.singleShot(0, lambda: self._on_voice_result(""))
                return
            finally:
                pythoncom.CoUninitialize()
        except Exception:
            pass

        QTimer.singleShot(0, self._voice_not_available)


# ── Premium Status Bar ────────────────────────────────────────────
class StatusBar(QFrame):
    pa_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            StatusBar {{
                background: {C['surface']};
                border-top: 1px solid {C['border']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Left: running apps / status
        self.running_lbl = QLabel()
        self.running_lbl.setStyleSheet(f"font-size: 10px; color: {C['text_tert']}; border: none;")
        layout.addWidget(self.running_lbl)

        layout.addSpacing(12)
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background: {C['border_light']}; border: none;")
        self._sep1 = sep
        layout.addWidget(sep)
        layout.addSpacing(8)

        # System status dot
        self.status_dot = QLabel("\u25CF")
        self.status_dot.setStyleSheet(f"font-size: 9px; color: {C['green']}; border: none;")
        layout.addWidget(self.status_dot)
        self.status_text = QLabel("All systems operational")
        self.status_text.setStyleSheet(f"font-size: 10px; color: {C['text_sec']}; border: none;")
        layout.addWidget(self.status_text)

        layout.addStretch()

        # Personal Assistant button
        self.pa_btn = QPushButton("\u2B50  PA")
        self.pa_btn.setToolTip("Personal Assistant mode (Ctrl+Shift+P)")
        self.pa_btn.setFixedHeight(26)
        self.pa_btn.setCursor(Qt.PointingHandCursor)
        self.pa_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['accent']}; color: white; border: none;
                border-radius: 5px; font-size: 10px; font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{ background: {C['accent2']}; }}
        """)
        self.pa_btn.clicked.connect(self.pa_clicked.emit)
        layout.addWidget(self.pa_btn)

        layout.addSpacing(8)

        # Live stats
        self.stats_lbl = QLabel("agents 3 \u00B7 kn 24 \u00B7 mem 128mb \u00B7 cap 6")
        self.stats_lbl.setStyleSheet(f"font-size: 10px; color: {C['text_tert']}; border: none;")
        layout.addWidget(self.stats_lbl)

        layout.addSpacing(12)
        self._sep2 = QFrame()
        self._sep2.setFixedWidth(1)
        self._sep2.setStyleSheet(f"background: {C['border_light']}; border: none;")
        layout.addWidget(self._sep2)
        layout.addSpacing(8)

        # Version
        self._version_lbl = QLabel("v14.0.0")
        self._version_lbl.setStyleSheet(f"font-size: 10px; color: {C['text_tert']}; border: none;")
        layout.addWidget(self._version_lbl)

    def update_running(self, app_names):
        self.running_lbl.setText(" \u25CF ".join(app_names) if app_names else "No running services")

    def set_pa_mode(self, active):
        if active:
            self.pa_btn.setText("\u26A1  PA ACTIVE")
            self.pa_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {C['amber']}; color: white; border: none;
                    border-radius: 5px; font-size: 10px; font-weight: 700;
                    padding: 0 10px;
                }}
                QPushButton:hover {{ background: {C['red']}; }}
            """)
            self.status_text.setText("PA mode active")
            self.status_dot.setStyleSheet(f"font-size: 9px; color: {C['amber']}; border: none;")
            # Hide non-essential status bar elements during PA mode
            self.running_lbl.setText("Terminal only")
            self._sep1.hide()
            self.stats_lbl.hide()
            self._sep2.hide()
            self._version_lbl.hide()
        else:
            self.pa_btn.setText("\u2B50  PA")
            self.pa_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {C['accent']}; color: white; border: none;
                    border-radius: 5px; font-size: 10px; font-weight: 600;
                    padding: 0 10px;
                }}
                QPushButton:hover {{ background: {C['accent2']}; }}
            """)
            self.status_text.setText("All systems operational")
            self.status_dot.setStyleSheet(f"font-size: 9px; color: {C['green']}; border: none;")
            self._sep1.show()
            self.stats_lbl.show()
            self._sep2.show()
            self._version_lbl.show()


# ── Main Ecosystem ─────────────────────────────────────────────────
PA_MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".pa_active")

class DesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARCANIS — Enterprise Ecosystem")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setStyleSheet(f"background: {C['bg']};")

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top header
        self.header = Header()
        self.header.bind_window(self)
        root.addWidget(self.header)

        # Stacked content: icons / ecosystem dashboard / PA overlay
        self.stack = QStackedWidget()
        self.desktop_view = self._build_desktop_icons()
        self.stack.addWidget(self.desktop_view)           # index 0
        self.dashboard = EcosystemDashboard()
        self.dashboard.zone_activated.connect(self.open_zone)
        self.stack.addWidget(self.dashboard)              # index 1
        self.pa_overlay = PersonalAssistantOverlay(self)
        self.stack.addWidget(self.pa_overlay)             # index 2
        root.addWidget(self.stack, 1)

        # Bottom status bar
        self.status_bar = StatusBar()
        self.status_bar.pa_clicked.connect(self._toggle_pa_mode)
        root.addWidget(self.status_bar)

        self._pa_active = False
        self.windows = []
        self._window_count = 0

        # Real ecosystem backend
        self.eco = EcosystemCoordinator()

        # Stats refresh timer
        self._stats_timer = QTimer()
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(3000)
        QTimer.singleShot(100, self._refresh_stats)

        self.showMaximized()

        # Check for PA marker (resume after shutdown)
        if os.path.exists(PA_MARKER):
            QTimer.singleShot(500, self._enter_pa_mode)

    def _build_desktop_icons(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(40, 28, 40, 12)
        layout.setSpacing(0)

        heading = QLabel("WORKSPACE")
        heading.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {C['text_tert']}; letter-spacing: 1.5px; border: none;")
        layout.addWidget(heading)
        layout.addSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(12)

        icons = [
            ("\u2328", "Terminal", "terminal", "Command-line interface"),
            ("\U0001F4C1", "Files", "files", "File system browser"),
            ("\u2699", "Settings", "settings", "System configuration"),
            ("\U0001F4CA", "System", "system", "Performance monitor"),
            ("\u25C7", "Surfaces", "surfaces", "Intelligence surface workspace"),
            ("\u269B", "Network", "network", "Ecosystem network status"),
        ]

        from math import ceil
        cols = 4
        for i, (icon, label, app_id, desc) in enumerate(icons):
            di = DesktopIcon(icon, label, app_id, desc)
            di.clicked.connect(self._handle_icon_click)
            row = i // cols
            col = i % cols
            grid.addWidget(di, row, col, Qt.AlignLeft | Qt.AlignTop)

        layout.addLayout(grid)
        layout.addStretch()
        return w

    def _handle_icon_click(self, app_id):
        # During PA mode, only terminal is accessible
        if self._pa_active and app_id != "terminal":
            return
        if app_id == "terminal":
            term = TerminalWidget(kill_mode=self._pa_active)
            self._open_app_window("Terminal", term, 760, 480, "terminal")
        elif app_id == "files":
            self._open_app_window("Files", FileBrowser(), 800, 520, "files")
        elif app_id == "settings":
            self._open_app_window("Settings", SettingsPanel(), 680, 480, "settings")
        elif app_id == "system":
            self._open_app_window("System Monitor", SystemMonitor(), 520, 400, "system")
        elif app_id == "surfaces":
            self.open_surface_workspace()
        elif app_id == "network":
            lbl = QLabel("Network status: connected\nEcosystem agents: 3/5 online\nBandwidth: 1.2 Gbps", alignment=Qt.AlignCenter)
            lbl.setStyleSheet(f"font-size: 12px; color: {C['text_sec']};")
            self._open_app_window("Network", lbl, 360, 200, "network")

    def _on_window_closed(self, win):
        if win in self.windows:
            self.windows.remove(win)
        self._update_status_bar()

    def _refresh_stats(self):
        s = self.eco.get_stats()
        self.status_bar.stats_lbl.setText(
            f"agents {s['agents']} \u00B7 kn {s['concepts']} \u00B7 "
            f"mem {s['memories']} \u00B7 prj {s['projects']} \u00B7 cap {s['tasks']}"
        )
        self.header.update_stats(f"agents {s['agents_active']}/{s['agents']} \u00B7 "
                                 f"knowledge {s['concepts']} \u00B7 memory {s['memories']} MB")
        if hasattr(self, 'dashboard'):
            self.dashboard.update_stats(s)

        # Check for completed task results
        if hasattr(self.eco, 'tasks'):
            results = self.eco.tasks.get_results()
            for task in results:
                if task.status == "completed":
                    self.eco.db.add_memory(f"Task done: {task.name}", "task",
                                          str(task.result)[:100] if task.result else "")

    def _update_status_bar(self):
        names = []
        for w in self.windows:
            t = w.property("app_name") or w.windowTitle()
            if t in ("terminal", "files", "settings", "system", "network", "surfaces"):
                names.append({"terminal": "Terminal", "files": "Files", "settings": "Settings", "system": "System", "network": "Network", "surfaces": "Surfaces"}.get(t, t))
        self.status_bar.update_running(names)

    # ── Personal Assistant Mode ──────────────────────────────────
    def _toggle_pa_mode(self):
        if self._pa_active:
            # Clicking PA button while active just focuses the overlay
            self.stack.setCurrentIndex(2)
        else:
            self._enter_pa_mode()

    def _enter_pa_mode(self):
        self._pa_active = True
        self.stack.setCurrentIndex(2)
        self.status_bar.set_pa_mode(True)
        self.pa_overlay.input.setFocus()
        # Create marker file for persistence across shutdown
        try:
            with open(PA_MARKER, "w") as f:
                f.write("1")
        except Exception:
            pass

    def _exit_pa_mode(self):
        if not self._pa_active:
            return
        self._pa_active = False
        self.stack.setCurrentIndex(0)
        self.status_bar.set_pa_mode(False)
        # Remove marker file
        try:
            if os.path.exists(PA_MARKER):
                os.remove(PA_MARKER)
        except Exception:
            pass

    def open_surface_workspace(self):
        from experience.surfaces.framework import WorkspaceManager, DockPosition
        from experience.surfaces.library import (
            IntelligenceCoreSurface, MissionSurface, AgentNetworkSurface,
            KnowledgeGraphSurface, MemoryTimelineSurface, ProjectExplorerSurface,
            SystemHealthSurface, EventStreamSurface, CapabilityLibrarySurface,
            WorkspaceMapSurface, ProjectWorkspaceSurface,
        )
        from experience.surfaces.framework.event_bus import EventBus
        from experience.surfaces.framework.plugin_loader import discover_plugins

        bus = EventBus()
        wm = WorkspaceManager("default")
        ws = wm.create_workspace()

        surfaces_config = [
            (IntelligenceCoreSurface, "Intelligence Core", "core", DockPosition.LEFT),
            (AgentNetworkSurface, "Agent Network", "agents", DockPosition.LEFT),
            (KnowledgeGraphSurface, "Knowledge Graph", "knowledge", DockPosition.RIGHT),
            (MemoryTimelineSurface, "Memory Timeline", "memory", DockPosition.RIGHT),
            (MissionSurface, "Mission", "mission", DockPosition.FULL),
            (ProjectExplorerSurface, "Project Explorer", "projects", DockPosition.BOTTOM),
            (ProjectWorkspaceSurface, "Project Workspace", "workspace", DockPosition.BOTTOM),
            (SystemHealthSurface, "System Health", "health", DockPosition.BOTTOM),
            (EventStreamSurface, "Event Stream", "events", DockPosition.BOTTOM),
            (CapabilityLibrarySurface, "Capability Library", "capabilities", DockPosition.RIGHT),
            (WorkspaceMapSurface, "Workspace Map", "map", DockPosition.LEFT),
        ]

        # Load plugin surfaces
        for plugin in discover_plugins():
            try:
                cls = plugin["class"]
                sid = plugin["name"]
                title = plugin["title"]
                wm.controller.register(cls, title, sid, DockPosition.RIGHT)
                wm.controller.dock(sid, DockPosition.RIGHT)
                bus.emit(EventBus.SYSTEM_EVENT, {"message": f"Plugin loaded: {title}"})
            except Exception as e:
                print(f"[Plugin] Failed to load {plugin['file']}: {e}")

        for cls, title, sid, pos in surfaces_config:
            s = wm.controller.register(cls, title, sid, pos)
            wm.controller.dock(sid, pos)

        content = QWidget()
        content._wm = wm
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(ws)
        win = AppWindow("Surface Workspace", content, self)
        win.setProperty("app_name", "surfaces")
        win.resize(1280, 720)
        win.show()
        self.windows.append(win)
        self._update_status_bar()

        bus.subscribe(EventBus.WORKSPACE_FOCUS, self._on_workspace_focus)

        QTimer.singleShot(500, lambda: self._simulate_events(bus))

    def _simulate_events(self, bus):
        import random
        from experience.surfaces.framework.event_bus import EventBus as EB
        bus.emit(EB.REASONING_UPDATE, {"state": "active"})
        bus.emit(EB.OBJECTIVE_UPDATE, {"objective": "System architecture analysis"})
        bus.emit(EB.MISSION_UPDATE, {"name": "Design Surface Framework", "progress": 45, "eta": "~2h"})
        bus.emit(EB.AGENT_ACTIVATED, {"name": "Analyzer"})
        bus.emit(EB.AGENT_ACTIVATED, {"name": "Coder"})
        bus.emit(EB.AGENT_ACTIVATED, {"name": "Orchestrator"})
        bus.emit(EB.KNOWLEDGE_UPDATED, {"concepts": 24, "relations": 47})
        bus.emit(EB.SYSTEM_EVENT, {"message": "Surface workspace initialized"})

        agents = ["Analyzer", "Coder", "Simulator", "Orchestrator", "Validator"]
        activities = ["processing", "analyzing", "compiling", "verifying", "idle"]

        def tick():
            if random.random() > 0.4:
                bus.emit(EB.AGENT_ACTIVITY, {
                    "name": random.choice(agents),
                    "activity": random.choice(activities),
                })
            if random.random() > 0.5:
                bus.emit(EB.SYSTEM_EVENT, {
                    "message": f"Agent {random.choice(agents)} {random.choice(activities)}"
                })
            if random.random() > 0.6:
                bus.emit(EB.CAPABILITY_UPDATE, {
                    "name": random.choice(["Research", "Analysis", "Programming"]),
                    "active": True,
                })

        timer = QTimer()
        timer.timeout.connect(tick)
        timer.setInterval(4000)
        timer.start()

    def open_zone(self, zone_id):
        if zone_id == "surfaces":
            self.open_surface_workspace()
            return

        if zone_id == "terminal":
            self._build_window("Terminal", TerminalWidget(), 760, 480)
            return

        from experience.surfaces.framework import WorkspaceManager, DockPosition
        from experience.surfaces.framework.event_bus import EventBus

        zone_surfaces = {
            "cognitive": [("IntelligenceCoreSurface", DockPosition.FULL)],
            "knowledge": [("KnowledgeGraphSurface", DockPosition.LEFT), ("MemoryTimelineSurface", DockPosition.RIGHT)],
            "agent": [("AgentNetworkSurface", DockPosition.FULL)],
            "mission": [("MissionSurface", DockPosition.FULL)],
            "creation": [("CapabilityLibrarySurface", DockPosition.FULL)],
            "system": [("SystemHealthSurface", DockPosition.LEFT)],
        }

        surface_map = {
            "IntelligenceCoreSurface": ("IntelligenceCoreSurface", "Intelligence Core", "core"),
            "KnowledgeGraphSurface": ("KnowledgeGraphSurface", "Knowledge Graph", "knowledge"),
            "MemoryTimelineSurface": ("MemoryTimelineSurface", "Memory Timeline", "memory"),
            "AgentNetworkSurface": ("AgentNetworkSurface", "Agent Network", "agents"),
            "MissionSurface": ("MissionSurface", "Mission", "mission"),
            "CapabilityLibrarySurface": ("CapabilityLibrarySurface", "Capability Library", "capabilities"),
            "SystemHealthSurface": ("SystemHealthSurface", "System Health", "health"),
        }

        from experience.surfaces.library import (
            IntelligenceCoreSurface, MissionSurface, AgentNetworkSurface,
            KnowledgeGraphSurface, MemoryTimelineSurface, ProjectExplorerSurface,
            SystemHealthSurface, EventStreamSurface, CapabilityLibrarySurface,
            WorkspaceMapSurface,
        )

        cls_map = {
            "IntelligenceCoreSurface": IntelligenceCoreSurface,
            "MissionSurface": MissionSurface,
            "AgentNetworkSurface": AgentNetworkSurface,
            "KnowledgeGraphSurface": KnowledgeGraphSurface,
            "MemoryTimelineSurface": MemoryTimelineSurface,
            "SystemHealthSurface": SystemHealthSurface,
            "CapabilityLibrarySurface": CapabilityLibrarySurface,
        }

        config = zone_surfaces.get(zone_id)
        if not config:
            return

        bus = EventBus()
        wm = WorkspaceManager(zone_id)
        ws = wm.create_workspace()

        for cls_name, pos in config:
            info = surface_map.get(cls_name)
            if info and cls_name in cls_map:
                cls = cls_map[cls_name]
                s = wm.controller.register(cls, info[1], info[2], pos)
                wm.controller.dock(info[2], pos)

        zone_titles = {
            "cognitive": "Cognitive Core",
            "knowledge": "Knowledge Graph",
            "agent": "Agent Network",
            "mission": "Mission Control",
            "creation": "Creation Tools",
            "system": "System Monitor",
        }

        content = QWidget()
        content._wm = wm
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(ws)
        win = AppWindow(zone_titles.get(zone_id, zone_id.title()), content, self)
        win.setProperty("app_name", zone_id)
        win.resize(900, 600)
        win.show()
        self.windows.append(win)
        self._update_status_bar()

        bus.emit(EventBus.SYSTEM_EVENT, {"message": f"{zone_titles.get(zone_id, zone_id.title())} zone activated"})
        bus.emit(EventBus.REASONING_UPDATE, {"state": "active"})

    def _make_coming_soon(self):
        lbl = QLabel("This zone is active and monitoring ecosystem state.\nOpen Surfaces workspace for full surface access.", alignment=Qt.AlignCenter)
        lbl.setStyleSheet(f"font-size: 12px; color: {C['text_sec']};")
        return lbl

    def _build_window(self, title, content, w, h):
        self._open_app_window(title, content, w, h)

    def _open_app_window(self, title, widget, w=520, h=360, app_name=None):
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(widget)
        # Connect terminal PA kill signal if applicable
        if hasattr(widget, 'pa_killed'):
            widget.pa_killed.connect(self._exit_pa_mode)
        win = AppWindow(title, content, self)
        win.setProperty("app_name", app_name or title)
        win.resize(w, h)
        win.show()
        self.windows.append(win)
        self._update_status_bar()

    def _on_workspace_focus(self, event, data):
        zone = data.get("zone", "")
        self.open_zone(zone)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_F11:
            self.showNormal() if self.isMaximized() else self.showMaximized()
        elif event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_W:
            if self.windows:
                win = self.windows[-1]
                self._on_window_closed(win)
                win.close()
        elif event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier) and event.key() == Qt.Key_P:
            self._toggle_pa_mode()

    def closeEvent(self, event):
        # If PA mode was active, keep marker for resume on next boot
        if not self._pa_active:
            try:
                if os.path.exists(PA_MARKER):
                    os.remove(PA_MARKER)
            except Exception:
                pass
        for w in self.windows:
            w.close()
        event.accept()


def launch():
    app = QApplication(sys.argv)
    app.setApplicationName("ARCANIS OS")
    app.setOrganizationName("ARCANIS")

    app.setStyleSheet(STYLE)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(C["bg"]))
    palette.setColor(QPalette.WindowText, QColor(C["text"]))
    palette.setColor(QPalette.Base, QColor(C["surface"]))
    palette.setColor(QPalette.Text, QColor(C["text"]))
    palette.setColor(QPalette.Button, QColor(C["surface"]))
    palette.setColor(QPalette.ButtonText, QColor(C["text"]))
    palette.setColor(QPalette.Highlight, QColor(C["accent"]))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.Link, QColor(C["accent"]))
    app.setPalette(palette)

    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    dw = DesktopWindow()
    return app.exec()
