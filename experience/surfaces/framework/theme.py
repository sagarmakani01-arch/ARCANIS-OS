from PySide6.QtGui import QColor, QFont


class SurfaceTheme:
    bg = QColor("#f5f6f8")
    surface = QColor("#ffffff")
    surface_alt = QColor("#f0f1f3")
    border = QColor("#e0e2e6")
    border_light = QColor("#e8eaed")
    text = QColor("#1a1a1a")
    text_sec = QColor("#6b7280")
    text_muted = QColor("#9ca3af")
    accent = QColor("#2563eb")
    accent_bg = QColor("#eef2ff")
    green = QColor("#059669")
    green_bg = QColor("#ecfdf5")
    amber = QColor("#d97706")
    amber_bg = QColor("#fffbeb")
    red = QColor("#dc2626")
    red_bg = QColor("#fef2f2")
    purple = QColor("#7c3aed")
    purple_bg = QColor("#f5f3ff")
    cyan = QColor("#0891b2")
    cyan_bg = QColor("#ecfeff")

    font_size_xs = 10
    font_size_sm = 11
    font_size_base = 12
    font_size_lg = 14
    font_size_xl = 18
    font_size_2xl = 24

    font_family = "Segoe UI"
    font_mono = "Cascadia Code, Consolas"

    spacing_xs = 4
    spacing_sm = 8
    spacing_md = 12
    spacing_lg = 16
    spacing_xl = 24

    @classmethod
    def font(cls, size=None, bold=False, mono=False):
        f = QFont(cls.font_mono if mono else cls.font_family)
        f.setPixelSize(size or cls.font_size_base)
        f.setBold(bold)
        return f

    @classmethod
    def header_style(cls, level=1):
        sizes = {1: cls.font_size_2xl, 2: cls.font_size_xl, 3: cls.font_size_lg}
        return f"font-size: {sizes.get(level, cls.font_size_base)}px; font-weight: 600; color: {cls.text.name()}; font-family: '{cls.font_family}';"

    @classmethod
    def label_style(cls, sec=False):
        c = cls.text_sec.name() if sec else cls.text.name()
        return f"font-size: {cls.font_size_sm}px; color: {c}; font-family: '{cls.font_family}';"

    @classmethod
    def mono_style(cls, size=None):
        s = size or cls.font_size_sm
        return f"font-size: {s}px; color: {cls.text.name()}; font-family: '{cls.font_mono}';"

    @classmethod
    def muted_style(cls):
        return f"font-size: {cls.font_size_xs}px; color: {cls.text_muted.name()}; font-family: '{cls.font_family}'; text-transform: uppercase;"
