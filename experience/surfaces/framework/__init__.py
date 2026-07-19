from .event_bus import EventBus
from .theme import SurfaceTheme
from .base import BaseSurface, SurfaceState, DockPosition, SurfaceFlags
from .controller import SurfaceController, WorkspaceManager
from .plugin_loader import discover_plugins

__all__ = [
    "EventBus", "SurfaceTheme", "BaseSurface",
    "SurfaceState", "DockPosition", "SurfaceFlags",
    "SurfaceController", "WorkspaceManager",
    "discover_plugins",
]
