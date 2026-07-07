"""
Theme / Skinning module for Forensic Toolkit GUI.

Centralizes all visual styling — colors, fonts, ttk style configuration,
and panel name mappings — so that the rest of the GUI code is layout-only.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk


# ── Unified color palette ─────────────────────────────

class Theme:
    """Single source of truth for all app colors."""

    # Sidebar (dark)
    SIDEBAR_BG = "#1a1d23"
    SIDEBAR_HOVER = "#2d3139"
    SIDEBAR_ACTIVE = "#2563eb"
    SIDEBAR_TEXT = "#e2e8f0"
    SIDEBAR_MUTED = "#94a3b8"

    # Content (light)
    CONTENT_BG = "#f0f2f5"
    PAPER_BG = "#ffffff"
    BORDER = "#cbd5e1"

    # Text
    TEXT_PRIMARY = "#1e293b"
    TEXT_SECONDARY = "#334155"
    TEXT_MUTED = "#64748b"

    # Header / Status
    HEADER_BG = "#1e293b"
    HEADER_TEXT = "#f8fafc"
    STATUS_BG = "#0f172a"
    STATUS_TEXT = "#94a3b8"

    # Accent
    ACCENT = "#2563eb"
    ACCENT_HOVER = "#1d4ed8"
    ACCENT_TEXT = "#ffffff"

    # Table
    TABLE_STRIPE = "#f8fafc"
    TABLE_HEADING_BG = "#f1f5f9"

    # Separators
    SEPARATOR = "#374151"

    # States
    SUCCESS = "#16a34a"
    DANGER = "#dc2626"
    WARNING = "#ca8a04"


# ── Panel name mappings (English TITLE → icon + Chinese) ─

PANEL_NAMES: dict[str, tuple[str, str]] = {
    "Dashboard":  ("\u2316", "仪表盘"),
    "Disk":       ("\u2b23", "磁盘取证"),
    "Filesystem": ("\u2b21", "文件系统"),
    "Carving":    ("\u2702", "文件雕刻"),
    "Strings":    ("\u224b", "字符串提取"),
    "Hash":       ("\u2299", "哈希校验"),
    "Hunt":       ("\u2298", "敏感搜索"),
    "Metadata":   ("\u2b24", "元数据提取"),
    "Network":    ("\u2b22", "网络取证"),
    "Memory":     ("\u2b25", "内存分析"),
    "Registry":   ("\u2b20", "注册表解析"),
    "Recovery":   ("\u2b6e", "数据恢复"),
}


# ── ttk style setup ───────────────────────────────────

def setup_ttk_theme(style: ttk.Style | None = None) -> ttk.Style:
    """Configure ttk widget styles. Call once at app startup."""

    if style is None:
        style = ttk.Style()

    # Use best available theme
    available = style.theme_names()
    for pref in ("clam", "alt", "default"):
        if pref in available:
            style.theme_use(pref)
            break

    df = ("", 10)   # default font
    sf = ("", 9)    # small font

    # Global defaults
    style.configure(".", font=df)

    # ttk widgets styled for the light content area
    style.configure("TLabel", background=Theme.CONTENT_BG,
                    foreground=Theme.TEXT_PRIMARY)
    style.configure("TFrame", background=Theme.CONTENT_BG)
    style.configure("TLabelframe", background=Theme.CONTENT_BG,
                    foreground=Theme.TEXT_PRIMARY,
                    bordercolor=Theme.BORDER, relief="solid",
                    borderwidth=1, font=("", 10, "bold"))
    style.configure("TLabelframe.Label", background=Theme.CONTENT_BG,
                    foreground=Theme.TEXT_SECONDARY,
                    font=("", 10, "bold"))
    style.configure("TButton", padding=(10, 4), font=sf)
    style.configure("TEntry", padding=4, font=df)
    style.configure("TCheckbutton", background=Theme.CONTENT_BG, font=sf)
    style.configure("TSpinbox", font=df)

    # Treeview / results table
    style.configure("Treeview", rowheight=28, font=sf)
    style.configure("Treeview.Heading", font=("", 9, "bold"),
                    padding=(6, 4), background=Theme.TABLE_HEADING_BG)

    # Notebook / tabs
    style.configure("TNotebook", background=Theme.CONTENT_BG, borderwidth=0)
    style.configure("TNotebook.Tab", font=sf, padding=(14, 5))

    # Progress bar
    style.configure("TProgressbar", thickness=8)

    # Accent button (blue)
    style.configure("Accent.TButton",
                    background=Theme.ACCENT,
                    foreground=Theme.ACCENT_TEXT,
                    font=df, padding=(14, 5))
    style.map("Accent.TButton",
              background=[("active", Theme.ACCENT_HOVER),
                          ("!disabled", Theme.ACCENT)],
              foreground=[("active", Theme.ACCENT_TEXT),
                          ("!disabled", Theme.ACCENT_TEXT)])

    return style
