import json
import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame
from PySide6.QtCore import Qt, QTimer

from .event_bus import EventBus
from .base import BaseSurface, SurfaceState, DockPosition, SurfaceFlags
from .theme import SurfaceTheme as T


class SurfacePanel(QFrame):
    def __init__(self, position, parent=None):
        super().__init__(parent)
        self._position = position
        self._surfaces = []
        self.setStyleSheet("background: transparent; border: none;")

        if position in (DockPosition.LEFT, DockPosition.RIGHT):
            self.setFixedWidth(300)
        elif position == DockPosition.BOTTOM:
            self.setFixedHeight(220)

        self._layout = QVBoxLayout(self) if position in (DockPosition.LEFT, DockPosition.RIGHT) else QHBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(4)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._scroll_layout = QVBoxLayout(self._scroll_content) if position in (DockPosition.LEFT, DockPosition.RIGHT) else QHBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_layout.setSpacing(4)
        self._scroll_layout.addStretch()

        self._scroll.setWidget(self._scroll_content)
        self._layout.addWidget(self._scroll)

    def add_surface(self, surface):
        if self._position in (DockPosition.LEFT, DockPosition.RIGHT):
            self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, surface)
        else:
            surface.setFixedHeight(200)
            self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, surface)
        self._surfaces.append(surface)

    def remove_surface(self, surface):
        if surface in self._surfaces:
            self._surfaces.remove(surface)
            self._scroll_layout.removeWidget(surface)
            surface.setParent(None)


class Workspace(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {T.bg.name()}; border: none;")
        self.setFocusPolicy(Qt.StrongFocus)
        self._controller = None

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.left_panel = SurfacePanel(DockPosition.LEFT)
        self.center = QWidget()
        self.center.setStyleSheet(f"background: {T.bg.name()};")
        self._center_layout = QVBoxLayout(self.center)
        self._center_layout.setContentsMargins(4, 4, 4, 4)
        self._center_layout.setSpacing(4)
        self._center_layout.addStretch()

        self.right_panel = SurfacePanel(DockPosition.RIGHT)
        self.bottom_panel = SurfacePanel(DockPosition.BOTTOM)

        self._layout.addWidget(self.left_panel)
        self._layout.addWidget(self.center, 1)
        self._layout.addWidget(self.right_panel)

        self._left_visible = True
        self._right_visible = True

        self._floating = []

    def set_controller(self, controller):
        self._controller = controller

    def dock_surface(self, surface, position):
        surface.set_dock(position)
        if position == DockPosition.LEFT:
            self.left_panel.add_surface(surface)
        elif position == DockPosition.RIGHT:
            self.right_panel.add_surface(surface)
        elif position == DockPosition.BOTTOM:
            self.bottom_panel.add_surface(surface)
        elif position == DockPosition.FLOAT:
            self._floating.append(surface)
        elif position == DockPosition.FULL:
            self._center_layout.insertWidget(self._center_layout.count() - 1, surface)
            surface.set_state(SurfaceState.IMMERSIVE)

        surface.show()

    def undock_surface(self, surface):
        for panel in [self.left_panel, self.right_panel, self.bottom_panel]:
            panel.remove_surface(surface)

    def toggle_left(self):
        self.left_panel.setVisible(not self.left_panel.isVisible())

    def toggle_right(self):
        self.right_panel.setVisible(not self.right_panel.isVisible())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab and self._controller:
            self._controller.focus_next()
            event.accept()
        elif event.key() == Qt.Key_Backtab and self._controller:
            self._controller.focus_prev()
            event.accept()
        else:
            super().keyPressEvent(event)


class SurfaceController:
    def __init__(self):
        self._workspace = None
        self._surfaces = {}
        self._bus = EventBus()
        self._focus_order = []
        self._dirty_callback = None

    def set_workspace(self, workspace):
        self._workspace = workspace

    def set_dirty_callback(self, callback):
        self._dirty_callback = callback

    def _mark_dirty(self, *args):
        if self._dirty_callback:
            self._dirty_callback()

    def register(self, surface_cls, title, surface_id, position=DockPosition.FLOAT, flags=SurfaceFlags.ALL):
        surface = surface_cls(title, surface_id, flags)
        surface.state_changed.connect(self._on_surface_state)
        surface.focused.connect(self._on_surface_focused)
        surface.pinned_changed.connect(self._mark_dirty)
        surface.state_changed.connect(self._mark_dirty)
        self._surfaces[surface_id] = surface
        return surface

    def dock(self, surface_id, position):
        s = self._surfaces.get(surface_id)
        if s and self._workspace:
            self._workspace.dock_surface(s, position)
            if surface_id not in self._focus_order:
                self._focus_order.append(surface_id)

    def get_surface(self, surface_id):
        return self._surfaces.get(surface_id)

    def all_surfaces(self):
        return list(self._surfaces.values())

    def focus_surface(self, surface_id):
        s = self._surfaces.get(surface_id)
        if s:
            s.set_focus()

    def focus_next(self):
        if not self._focus_order:
            return
        current = None
        for w in self._workspace.findChildren(QFrame):
            if w.hasFocus():
                for sid, s in self._surfaces.items():
                    if s == w or s.isAncestorOf(w):
                        current = sid
                        break
                break
        idx = self._focus_order.index(current) + 1 if current in self._focus_order else 0
        if idx >= len(self._focus_order):
            idx = 0
        self.focus_surface(self._focus_order[idx])

    def focus_prev(self):
        if not self._focus_order:
            return
        current = None
        for w in self._workspace.findChildren(QFrame):
            if w.hasFocus():
                for sid, s in self._surfaces.items():
                    if s == w or s.isAncestorOf(w):
                        current = sid
                        break
                break
        idx = self._focus_order.index(current) - 1 if current in self._focus_order else -1
        if idx < 0:
            idx = len(self._focus_order) - 1
        self.focus_surface(self._focus_order[idx])

    def _on_surface_state(self, surface_id, state):
        pass

    def _on_surface_focused(self, surface_id):
        self._bus.emit(EventBus.SURFACE_FOCUSED, {"surface_id": surface_id})


class WorkspaceManager:
    def __init__(self, workspace_name="default"):
        self.controller = SurfaceController()
        self._bus = EventBus()
        self._workspace = None
        self._workspace_name = workspace_name
        self._config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".workspace")
        self._fallback_path = os.path.join(self._config_dir, f"{workspace_name}.json")
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setInterval(30000)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._dirty = False
        self._db = None

    def _get_db(self):
        if self._db is None:
            try:
                from experience.ecosystem.database import Database
                self._db = Database()
            except Exception:
                pass
        return self._db

    def create_workspace(self, parent=None):
        self._workspace = Workspace(parent)
        self._workspace.set_controller(self.controller)
        self.controller.set_workspace(self._workspace)
        self.controller.set_dirty_callback(self.mark_dirty)
        os.makedirs(self._config_dir, exist_ok=True)
        self._auto_load()
        self._auto_save_timer.start()
        return self._workspace

    def workspace(self):
        return self._workspace

    def mark_dirty(self):
        self._dirty = True

    def _auto_save(self):
        if self._dirty and self._workspace:
            self.save_to_db()
            self._save_fallback()
            self._dirty = False

    def _auto_load(self):
        self.load_from_db()
        # If DB had nothing, try fallback JSON
        if not self.controller._focus_order:
            self._load_fallback()

    # ── SQLite Persistence ─────────────────────────────────────
    def save_to_db(self):
        db = self._get_db()
        if not db:
            return
        surfaces = []
        for s in self.controller.all_surfaces():
            surfaces.append({
                "id": s.surface_id(),
                "dock": s.get_dock().value,
                "state": s.get_state().value,
                "pinned": s.is_pinned(),
            })
            s.save_all_state()
        db.save_layout(self._workspace_name, surfaces)

    def load_from_db(self):
        db = self._get_db()
        if not db:
            return
        try:
            layout = db.load_layout(self._workspace_name)
        except Exception:
            layout = []
        for entry in layout:
            sid = entry.get("surface_id")
            pos = DockPosition(entry.get("dock_position", "float"))
            if sid and sid in self.controller._surfaces:
                self.controller.dock(sid, pos)
            if sid and sid in self.controller._surfaces:
                surface = self.controller._surfaces[sid]
                try:
                    surface._pinned = bool(entry.get("pinned", False))
                except Exception:
                    pass
                surface.restore_all_state()

    # ── JSON Fallback ──────────────────────────────────────────
    def save_workspace(self, path):
        data = {"surfaces": []}
        for s in self.controller.all_surfaces():
            data["surfaces"].append({
                "id": s.surface_id(),
                "dock": s.get_dock().value,
                "state": s.get_state().value,
                "pinned": s.is_pinned(),
            })
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _save_fallback(self):
        self.save_workspace(self._fallback_path)

    def load_workspace(self, path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            for config in data.get("surfaces", []):
                sid = config.get("id")
                pos = DockPosition(config.get("dock", "float"))
                if sid and sid in self.controller._surfaces:
                    self.controller.dock(sid, pos)
                if sid and sid in self.controller._surfaces:
                    surface = self.controller._surfaces[sid]
                    try:
                        surface._pinned = bool(config.get("pinned", False))
                    except Exception:
                        pass
        except Exception:
            pass

    def _load_fallback(self):
        self.load_workspace(self._fallback_path)

    def save_on_exit(self):
        self._auto_save_timer.stop()
        if self._workspace:
            self.save_to_db()
            self._save_fallback()
