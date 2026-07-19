from PySide6.QtWidgets import QVBoxLayout, QLabel
from experience.surfaces.framework.base import BaseSurface, SurfaceFlags
from experience.surfaces.framework.theme import SurfaceTheme as T


_surface_id = "example_plugin"
_title_hint = "Example Plugin"


class ExamplePluginSurface(BaseSurface):
    def __init__(self, title, surface_id, flags=SurfaceFlags.ALL):
        super().__init__(title, surface_id, flags)

    def _init_content(self):
        l = QVBoxLayout(self.content)
        l.setContentsMargins(12, 8, 12, 12)
        l.setSpacing(6)
        lbl = QLabel("This is an example plugin surface.\nLoaded dynamically from plugins/")
        lbl.setStyleSheet(T.label_style())
        l.addWidget(lbl)
        l.addStretch()
