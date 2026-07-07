"""
Modern multi-color theme for Forensic Toolkit GUI.

Color philosophy: rich, vibrant multi-color palette.
- Primary: Teal (#0d9488)
- Secondary: Purple (#7c3aed)
- Warm accent: Orange (#f97316)
- Cool accent: Cyan (#06b6d4)
- Pink accent: Rose (#e11d48)
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from enum import Enum
from typing import Callable


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"


# ── Light Palette ─────────────────────────────────────

class LightColors:
    # Sidebar
    SIDEBAR_BG = "#1e1b4b"
    SIDEBAR_BG_LIGHTER = "#312e81"
    SIDEBAR_HOVER = "#3730a3"
    SIDEBAR_ACTIVE = "#0d9488"
    SIDEBAR_ACTIVE_GLOW = "#14b8a6"
    SIDEBAR_TEXT = "#e0e7ff"
    SIDEBAR_TEXT_ACTIVE = "#ffffff"
    SIDEBAR_MUTED = "#818cf8"
    SIDEBAR_GROUP = "#6366f1"
    SIDEBAR_DIVIDER = "#3730a3"

    # Content
    CONTENT_BG = "#f8fafc"
    CONTENT_BG_ALT = "#f1f5f9"
    PAPER_BG = "#ffffff"
    PAPER_HOVER = "#f8fafc"
    BORDER = "#cbd5e1"
    BORDER_LIGHT = "#e2e8f0"
    BORDER_FOCUS = "#0d9488"

    # Text
    TEXT_PRIMARY = "#0f172a"
    TEXT_SECONDARY = "#475569"
    TEXT_MUTED = "#64748b"
    TEXT_PLACEHOLDER = "#94a3b8"

    # Header
    HEADER_BG = "#1e1b4b"
    HEADER_BG_GRADIENT = "#312e81"
    HEADER_TEXT = "#f1f5f9"
    STATUS_BG = "#f8fafc"
    STATUS_TEXT = "#64748b"
    STATUS_TEXT_ACTIVE = "#0f172a"

    # Accent colors — multi-color palette
    ACCENT = "#0d9488"           # Teal (primary)
    ACCENT_HOVER = "#0f766e"
    ACCENT_ACTIVE = "#115e59"
    ACCENT_LIGHT = "#ccfbf1"
    ACCENT_LIGHTER = "#f0fdfa"
    ACCENT_TEXT = "#ffffff"

    # Secondary accent — Purple
    ACCENT2 = "#7c3aed"
    ACCENT2_HOVER = "#6d28d9"
    ACCENT2_LIGHT = "#ede9fe"
    ACCENT2_TEXT = "#ffffff"

    # Warm accent — Orange
    ACCENT3 = "#f97316"
    ACCENT3_HOVER = "#ea580c"
    ACCENT3_LIGHT = "#fff7ed"
    ACCENT3_TEXT = "#ffffff"

    # Cool accent — Cyan
    ACCENT4 = "#06b6d4"
    ACCENT4_HOVER = "#0891b2"
    ACCENT4_LIGHT = "#ecfeff"
    ACCENT4_TEXT = "#ffffff"

    # Pink accent — Rose
    ACCENT5 = "#e11d48"
    ACCENT5_HOVER = "#be123c"
    ACCENT5_LIGHT = "#fff1f2"
    ACCENT5_TEXT = "#ffffff"

    # Table
    TABLE_STRIPE = "#f8fafc"
    TABLE_STRIPE_ALT = "#f1f5f9"
    TABLE_HEADING_BG = "#e2e8f0"
    TABLE_HEADING_FG = "#0f172a"
    TABLE_SELECTED_BG = "#ccfbf1"
    TABLE_SELECTED_FG = "#0f766e"
    TABLE_ROW_HOVER = "#f0fdfa"

    SEPARATOR = "#3730a3"

    # State colors
    SUCCESS = "#059669"
    SUCCESS_BG = "#d1fae5"
    SUCCESS_BORDER = "#6ee7b7"
    DANGER = "#e11d48"
    DANGER_BG = "#ffe4e6"
    DANGER_BORDER = "#fda4af"
    WARNING = "#f97316"
    WARNING_BG = "#fff7ed"
    WARNING_BORDER = "#fdba74"
    INFO = "#0d9488"
    INFO_BG = "#ccfbf1"
    INFO_BORDER = "#5eead4"

    # Input
    INPUT_BG = "#ffffff"
    INPUT_FG = "#0f172a"
    INPUT_BORDER = "#cbd5e1"
    INPUT_FOCUS_BORDER = "#0d9488"

    TOOLTIP_BG = "#1e1b4b"
    TOOLTIP_FG = "#f1f5f9"

    SCROLLBAR_BG = "#cbd5e1"
    SCROLLBAR_HOVER = "#94a3b8"
    SCROLLBAR_TROUGH = "#f1f5f9"

    SHADOW_SM = "#e2e8f0"
    SHADOW_MD = "#cbd5e1"
    SHADOW_LG = "#94a3b8"

    CARD_BG = "#ffffff"
    CARD_BORDER = "#e2e8f0"
    CARD_HOVER_BORDER = "#cbd5e1"
    CARD_HOVER_BG = "#f8fafc"

    HERO_BG = "#f8fafc"
    HERO_ACCENT = "#0d9488"

    GLASS_BG = "#ffffff"
    GLASS_BORDER = "#e2e8f0"


# ── Dark Palette ──────────────────────────────────────

class DarkColors:
    # Sidebar — deep indigo
    SIDEBAR_BG = "#0f0a2e"
    SIDEBAR_BG_LIGHTER = "#1e1b4b"
    SIDEBAR_HOVER = "#312e81"
    SIDEBAR_ACTIVE = "#0d9488"
    SIDEBAR_ACTIVE_GLOW = "#14b8a6"
    SIDEBAR_TEXT = "#c7d2fe"
    SIDEBAR_TEXT_ACTIVE = "#ffffff"
    SIDEBAR_MUTED = "#6366f1"
    SIDEBAR_GROUP = "#4f46e5"
    SIDEBAR_DIVIDER = "#312e81"

    # Content
    CONTENT_BG = "#0f0a2e"
    CONTENT_BG_ALT = "#1a1640"
    PAPER_BG = "#1a1640"
    PAPER_HOVER = "#221d50"
    BORDER = "#312e81"
    BORDER_LIGHT = "#252060"
    BORDER_FOCUS = "#14b8a6"

    TEXT_PRIMARY = "#e2e8f0"
    TEXT_SECONDARY = "#a5b4fc"
    TEXT_MUTED = "#6366f1"
    TEXT_PLACEHOLDER = "#4f46e5"

    HEADER_BG = "#0a0620"
    HEADER_BG_GRADIENT = "#1e1b4b"
    HEADER_TEXT = "#f1f5f9"
    STATUS_BG = "#0a0620"
    STATUS_TEXT = "#6366f1"
    STATUS_TEXT_ACTIVE = "#a5b4fc"

    # Accent colors — multi-color palette
    ACCENT = "#14b8a6"           # Teal (primary)
    ACCENT_HOVER = "#2dd4bf"
    ACCENT_ACTIVE = "#0d9488"
    ACCENT_LIGHT = "#134e4a"
    ACCENT_LIGHTER = "#042f2e"
    ACCENT_TEXT = "#ffffff"

    # Secondary — Purple
    ACCENT2 = "#8b5cf6"
    ACCENT2_HOVER = "#a78bfa"
    ACCENT2_LIGHT = "#2e1065"
    ACCENT2_TEXT = "#ffffff"

    # Warm — Orange
    ACCENT3 = "#fb923c"
    ACCENT3_HOVER = "#fdba74"
    ACCENT3_LIGHT = "#431407"
    ACCENT3_TEXT = "#ffffff"

    # Cool — Cyan
    ACCENT4 = "#22d3ee"
    ACCENT4_HOVER = "#67e8f9"
    ACCENT4_LIGHT = "#164e63"
    ACCENT4_TEXT = "#ffffff"

    # Pink — Rose
    ACCENT5 = "#fb7185"
    ACCENT5_HOVER = "#fda4af"
    ACCENT5_LIGHT = "#4c0519"
    ACCENT5_TEXT = "#ffffff"

    # Table
    TABLE_STRIPE = "#1a1640"
    TABLE_STRIPE_ALT = "#221d50"
    TABLE_HEADING_BG = "#252060"
    TABLE_HEADING_FG = "#c7d2fe"
    TABLE_SELECTED_BG = "#134e4a"
    TABLE_SELECTED_FG = "#5eead4"
    TABLE_ROW_HOVER = "#1a2540"

    SEPARATOR = "#312e81"

    # State colors
    SUCCESS = "#34d399"
    SUCCESS_BG = "#064e3b"
    SUCCESS_BORDER = "#059669"
    DANGER = "#fb7185"
    DANGER_BG = "#4c0519"
    DANGER_BORDER = "#9f1239"
    WARNING = "#fb923c"
    WARNING_BG = "#431407"
    WARNING_BORDER = "#9a3412"
    INFO = "#14b8a6"
    INFO_BG = "#134e4a"
    INFO_BORDER = "#0d9488"

    INPUT_BG = "#1a1640"
    INPUT_FG = "#e2e8f0"
    INPUT_BORDER = "#312e81"
    INPUT_FOCUS_BORDER = "#14b8a6"

    TOOLTIP_BG = "#312e81"
    TOOLTIP_FG = "#f1f5f9"

    SCROLLBAR_BG = "#312e81"
    SCROLLBAR_HOVER = "#4f46e5"
    SCROLLBAR_TROUGH = "#0f0a2e"

    SHADOW_SM = "#0a0620"
    SHADOW_MD = "#060410"
    SHADOW_LG = "#020108"

    CARD_BG = "#1a1640"
    CARD_BORDER = "#312e81"
    CARD_HOVER_BORDER = "#4f46e5"
    CARD_HOVER_BG = "#221d50"

    HERO_BG = "#0f0a2e"
    HERO_ACCENT = "#14b8a6"

    GLASS_BG = "#1a1640"
    GLASS_BORDER = "#312e81"


# ── Color attribute sync ──────────────────────────────

_COLOR_ATTRS = sorted(
    k for k in dir(LightColors) if k.isupper() and not k.startswith("_")
)


# ── Theme Manager ─────────────────────────────────────

class _ThemeMeta(type):
    def __getattr__(cls, name: str) -> str:
        if name in _COLOR_ATTRS:
            return getattr(cls._colors, name)
        raise AttributeError(name)

    def __setattr__(cls, name: str, value) -> None:
        if name in _COLOR_ATTRS:
            setattr(cls._colors, name, value)
        else:
            super().__setattr__(name, value)


class Theme(metaclass=_ThemeMeta):
    _mode: ThemeMode = ThemeMode.LIGHT
    _colors: type = LightColors

    def __init__(self):
        raise RuntimeError("Use Theme.set_mode() / Theme.get() instead")

    @classmethod
    def set_mode(cls, mode: ThemeMode) -> None:
        cls._mode = mode
        cls._colors = DarkColors if mode == ThemeMode.DARK else LightColors

    @classmethod
    def get_mode(cls) -> ThemeMode:
        return cls._mode

    @classmethod
    def toggle(cls) -> ThemeMode:
        new_mode = ThemeMode.DARK if cls._mode == ThemeMode.LIGHT else ThemeMode.LIGHT
        cls.set_mode(new_mode)
        return new_mode

    @classmethod
    def _c(cls):
        return cls._colors

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        h = hex_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"

    @classmethod
    def interpolate(cls, c1: str, c2: str, t: float) -> str:
        r1, g1, b1 = cls.hex_to_rgb(c1)
        r2, g2, b2 = cls.hex_to_rgb(c2)
        t = max(0.0, min(1.0, t))
        return cls.rgb_to_hex(
            int(r1 + (r2 - r1) * t),
            int(g1 + (g2 - g1) * t),
            int(b1 + (b2 - b1) * t),
        )

    @classmethod
    def lighten(cls, color: str, amount: float = 0.1) -> str:
        r, g, b = cls.hex_to_rgb(color)
        return cls.rgb_to_hex(
            min(255, int(r + (255 - r) * amount)),
            min(255, int(g + (255 - g) * amount)),
            min(255, int(b + (255 - b) * amount)),
        )

    @classmethod
    def darken(cls, color: str, amount: float = 0.1) -> str:
        r, g, b = cls.hex_to_rgb(color)
        return cls.rgb_to_hex(int(r * (1 - amount)), int(g * (1 - amount)), int(b * (1 - amount)))


# ── Animation Engine ──────────────────────────────────

class Animation:
    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        return 1 - (1 - t) ** 3

    @staticmethod
    def _ease_in_out_cubic(t: float) -> float:
        return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2

    EASING = {
        "ease_out": _ease_out_cubic,
        "ease_in_out": _ease_in_out_cubic,
        "linear": lambda t: t,
    }

    @classmethod
    def animate_color(cls, widget: tk.Widget, attr: str,
                      from_color: str, to_color: str,
                      duration_ms: int = 300, easing: str = "ease_out",
                      on_complete: Callable | None = None) -> None:
        if not widget.winfo_exists():
            return
        ease_fn = cls.EASING.get(easing, cls._ease_out_cubic)
        steps = max(8, duration_ms // 16)
        step_ms = duration_ms // steps

        def _step(step: int) -> None:
            if not widget.winfo_exists():
                return
            t = ease_fn(step / steps)
            color = Theme.interpolate(from_color, to_color, t)
            try:
                widget.configure(**{attr: color})
            except Exception:
                return
            if step < steps:
                widget.after(step_ms, lambda: _step(step + 1))
            elif on_complete:
                widget.after(0, on_complete)

        _step(0)

    @classmethod
    def animate_width(cls, widget: tk.Widget, from_w: int, to_w: int,
                      duration_ms: int = 250, easing: str = "ease_out",
                      after_step: Callable[[int], None] | None = None,
                      on_complete: Callable | None = None) -> None:
        if not widget.winfo_exists():
            return
        ease_fn = cls.EASING.get(easing, cls._ease_out_cubic)
        steps = max(10, duration_ms // 16)
        step_ms = duration_ms // steps

        def _step(step: int) -> None:
            if not widget.winfo_exists():
                return
            t = ease_fn(step / steps)
            w = int(from_w + (to_w - from_w) * t)
            try:
                widget.configure(width=w)
                if after_step:
                    after_step(w)
            except Exception:
                return
            if step < steps:
                widget.after(step_ms, lambda: _step(step + 1))
            elif on_complete:
                widget.after(0, on_complete)

        _step(0)

    @classmethod
    def animate_fade(cls, widget: tk.Widget, from_bg: str, to_bg: str,
                     duration_ms: int = 200, easing: str = "ease_out",
                     on_complete: Callable | None = None) -> None:
        cls.animate_color(widget, "bg", from_bg, to_bg, duration_ms, easing, on_complete)


# ── Panel name mappings ───────────────────────────────

PANEL_NAMES: dict[str, tuple[str, str]] = {
    "Dashboard":       ("\u2316", "仪表盘"),
    "Disk":            ("\u2b23", "磁盘取证"),
    "DiskPartition":   ("\u25a6", "分区解析"),
    "Filesystem":      ("\u2b21", "文件系统"),
    "Carving":         ("\u2702", "文件雕刻"),
    "Strings":         ("\u224b", "字符串提取"),
    "Hash":            ("\u2299", "哈希校验"),
    "Hunt":            ("\u2298", "敏感搜索"),
    "Metadata":        ("\u2b24", "元数据提取"),
    "Network":         ("\u2b22", "网络取证"),
    "Memory":          ("\u2b25", "内存分析"),
    "Registry":        ("\u2b20", "注册表解析"),
    "Recovery":        ("\u2b6e", "数据恢复"),
    "EvidencePackage": ("\u2395", "证据打包"),
    "LogViewer":       ("\u2630", "操作日志"),
    "Settings":        ("\u2699", "系统设置"),
}

PANEL_GROUPS: list[dict] = [
    {"name": "概览",     "panels": ["Dashboard"]},
    {"name": "系统分析", "panels": ["Disk", "DiskPartition", "Memory", "Registry"]},
    {"name": "文件分析", "panels": ["Filesystem", "Strings", "Hash", "Hunt", "Metadata", "Carving"]},
    {"name": "网络分析", "panels": ["Network"]},
    {"name": "数据恢复", "panels": ["Recovery", "EvidencePackage"]},
    {"name": "工具",     "panels": ["LogViewer", "Settings"]},
]


# ── ttk style setup ───────────────────────────────────

def _apply_theme_colors(style: ttk.Style) -> None:
    c = Theme._c()
    style.configure(".", font=("Microsoft YaHei UI", 10))

    style.configure("TLabel", background=c.CONTENT_BG, foreground=c.TEXT_PRIMARY)
    style.configure("Sidebar.TLabel", background=c.SIDEBAR_BG, foreground=c.SIDEBAR_TEXT)
    style.configure("Muted.TLabel", foreground=c.TEXT_MUTED)
    style.configure("Hero.TLabel", font=("Microsoft YaHei UI", 28, "bold"),
                    foreground=c.TEXT_PRIMARY, background=c.CONTENT_BG)
    style.configure("Subtitle.TLabel", font=("Microsoft YaHei UI", 14),
                    foreground=c.TEXT_SECONDARY, background=c.CONTENT_BG)

    style.configure("TFrame", background=c.CONTENT_BG)
    style.configure("Sidebar.TFrame", background=c.SIDEBAR_BG)
    style.configure("Header.TFrame", background=c.HEADER_BG)
    style.configure("Status.TFrame", background=c.STATUS_BG)
    style.configure("Paper.TFrame", background=c.PAPER_BG)
    style.configure("Card.TFrame", background=c.CARD_BG)

    style.configure("TLabelframe", background=c.CONTENT_BG,
                    foreground=c.TEXT_SECONDARY, bordercolor=c.BORDER,
                    relief="solid", borderwidth=1,
                    font=("Microsoft YaHei UI", 11, "bold"))
    style.configure("TLabelframe.Label", background=c.CONTENT_BG,
                    foreground=c.TEXT_SECONDARY,
                    font=("Microsoft YaHei UI", 11, "bold"))

    style.configure("TButton", padding=(12, 6), font=("Microsoft YaHei UI", 9))
    style.map("TButton",
              background=[("active", c.ACCENT_HOVER), ("!disabled", c.ACCENT)],
              foreground=[("active", c.ACCENT_TEXT), ("!disabled", c.ACCENT_TEXT)])

    style.configure("Header.TButton", padding=(10, 3), font=("Microsoft YaHei UI", 9),
                    background=c.HEADER_BG, foreground=c.HEADER_TEXT, borderwidth=0)
    style.map("Header.TButton",
              background=[("active", c.SIDEBAR_HOVER)],
              foreground=[("active", c.HEADER_TEXT)])

    style.configure("TEntry", padding=8, font=("Microsoft YaHei UI", 10),
                    fieldbackground=c.INPUT_BG, foreground=c.INPUT_FG)
    style.configure("TCheckbutton", background=c.CONTENT_BG, font=("Microsoft YaHei UI", 9))
    style.configure("TSpinbox", font=("Microsoft YaHei UI", 10),
                    fieldbackground=c.INPUT_BG, foreground=c.INPUT_FG)
    style.configure("TCombobox", font=("Microsoft YaHei UI", 10),
                    fieldbackground=c.INPUT_BG, foreground=c.INPUT_FG)

    style.configure("Treeview", rowheight=32, font=("Microsoft YaHei UI", 9),
                    background=c.PAPER_BG, foreground=c.TEXT_PRIMARY,
                    fieldbackground=c.PAPER_BG)
    style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 9, "bold"),
                    padding=(10, 6), background=c.TABLE_HEADING_BG,
                    foreground=c.TABLE_HEADING_FG)
    style.map("Treeview",
              background=[("selected", c.TABLE_SELECTED_BG)],
              foreground=[("selected", c.TABLE_SELECTED_FG)])

    style.configure("Result.Treeview", rowheight=30, font=("Microsoft YaHei UI", 9))
    style.configure("Result.Treeview.Heading", font=("Microsoft YaHei UI", 9, "bold"),
                    padding=(8, 5))

    style.configure("TNotebook", background=c.CONTENT_BG, borderwidth=0)
    style.configure("TNotebook.Tab", font=("Microsoft YaHei UI", 9), padding=(16, 8))

    style.configure("TProgressbar", thickness=6)

    style.configure("Accent.TButton",
                    background=c.ACCENT, foreground=c.ACCENT_TEXT,
                    font=("Microsoft YaHei UI", 10, "bold"), padding=(16, 8))
    style.map("Accent.TButton",
              background=[("active", c.ACCENT_HOVER), ("!disabled", c.ACCENT)],
              foreground=[("active", c.ACCENT_TEXT), ("!disabled", c.ACCENT_TEXT)])

    style.configure("Small.TButton", padding=(8, 3), font=("Microsoft YaHei UI", 8))
    style.configure("TScrollbar", background=c.SCROLLBAR_TROUGH,
                    troughcolor=c.SCROLLBAR_TROUGH, arrowcolor=c.TEXT_MUTED)


def setup_ttk_theme(style: ttk.Style | None = None) -> ttk.Style:
    if style is None:
        style = ttk.Style()
    available = style.theme_names()
    for pref in ("clam", "alt", "default"):
        if pref in available:
            style.theme_use(pref)
            break
    _apply_theme_colors(style)
    return style


def refresh_ttk_theme(style: ttk.Style | None = None) -> None:
    if style is None:
        style = ttk.Style()
    _apply_theme_colors(style)