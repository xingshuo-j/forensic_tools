"""
Forensic Toolkit GUI - Main Application Window
Apple-inspired design: clean, spacious, with deep sidebar
and generous card-based content area.

Features:
  - Animated sidebar with Apple-style depth
  - Panel fade-in transitions
  - Light/Dark theme with Apple color tokens
  - Keyboard shortcuts
  - Feature card dashboard
  - 16 forensic panels
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any

from forensic_toolkit.core.platform import Platform
from forensic_toolkit.core.module_base import ModuleRegistry
from forensic_toolkit.gui.panels import get_panels, BasePanel, LogViewerPanel
from forensic_toolkit.gui.theme import (
    Theme, ThemeMode, PANEL_NAMES, PANEL_GROUPS, setup_ttk_theme, refresh_ttk_theme, Animation
)
from forensic_toolkit.gui.widgets import (
    ToolTip, ShortcutManager, NavButton, AnimatedButton
)
from forensic_toolkit.core.evidence import EvidenceSession

VERSION = "0.5.0"


class MainWindow:
    """Apple-inspired main window with deep sidebar and card-based layout."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Forensic Toolkit v{VERSION}")
        self.root.geometry("1280x800")
        self.root.minsize(960, 600)
        self.root.configure(bg=Theme.CONTENT_BG)
        self.root._main_window = self  # 供面板导航反向引用

        self._style = setup_ttk_theme()
        self._status_var = tk.StringVar(value="")
        self._session: EvidenceSession | None = None
        self._sidebar_collapsed = False
        self._sidebar_width = 220
        self._animating_sidebar = False
        self._log_panel: LogViewerPanel | None = None

        self._panels = get_panels()
        self._panel_map: dict[str, int] = {
            p.TITLE: i for i, p in enumerate(self._panels)
        }
        self._build_layout()
        self._shortcuts = ShortcutManager(self.root)
        self._setup_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._current_panel: BasePanel | None = None
        self.root.after(200, lambda: self._show_panel_by_title("Dashboard"))

    # ── Layout ────────────────────────────────────────

    def _build_layout(self) -> None:
        # ── Header ──
        header = tk.Frame(self.root, bg=Theme.HEADER_BG, height=48)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # Accent indicator
        tk.Frame(header, bg=Theme.ACCENT, width=3, height=48).pack(side=tk.LEFT)

        tk.Label(header, text="  Forensic Toolkit", bg=Theme.HEADER_BG,
                 fg=Theme.HEADER_TEXT, font=("Microsoft YaHei UI", 12, "bold"),
                 padx=0, pady=8).pack(side=tk.LEFT)

        toolbar = tk.Frame(header, bg=Theme.HEADER_BG)
        toolbar.pack(side=tk.RIGHT, padx=8)

        self._theme_btn = tk.Button(toolbar, text="\u263e  深色", bg=Theme.HEADER_BG,
                                    fg=Theme.HEADER_TEXT, font=("Microsoft YaHei UI", 9),
                                    relief=tk.FLAT, bd=0, cursor="hand2",
                                    activebackground=Theme.SIDEBAR_HOVER,
                                    activeforeground=Theme.HEADER_TEXT,
                                    command=self._toggle_theme, padx=10, pady=2)
        self._theme_btn.pack(side=tk.LEFT)
        self._theme_btn.bind("<Enter>", lambda e: self._theme_btn.configure(bg=Theme.SIDEBAR_HOVER))
        self._theme_btn.bind("<Leave>", lambda e: self._theme_btn.configure(bg=Theme.HEADER_BG))
        self._theme_btn.bind("<Button-1>", lambda e: self._theme_btn.configure(bg=Theme.darken(Theme.SIDEBAR_HOVER, 0.1)), add="+")
        self._theme_btn.bind("<ButtonRelease-1>", lambda e: self._theme_btn.configure(bg=Theme.SIDEBAR_HOVER), add="+")
        ToolTip(self._theme_btn, "切换主题 (Ctrl+D)")

        self._sidebar_toggle_btn = tk.Button(toolbar, text="\u2630  收起侧栏",
                                             bg=Theme.HEADER_BG, fg=Theme.HEADER_TEXT,
                                             font=("Microsoft YaHei UI", 9),
                                             relief=tk.FLAT, bd=0, cursor="hand2",
                                             activebackground=Theme.SIDEBAR_HOVER,
                                             activeforeground=Theme.HEADER_TEXT,
                                             command=self._toggle_sidebar, padx=10, pady=2)
        self._sidebar_toggle_btn.pack(side=tk.LEFT)
        self._sidebar_toggle_btn.bind("<Enter>", lambda e: self._sidebar_toggle_btn.configure(bg=Theme.SIDEBAR_HOVER))
        self._sidebar_toggle_btn.bind("<Leave>", lambda e: self._sidebar_toggle_btn.configure(bg=Theme.HEADER_BG))
        self._sidebar_toggle_btn.bind("<Button-1>", lambda e: self._sidebar_toggle_btn.configure(bg=Theme.darken(Theme.SIDEBAR_HOVER, 0.1)), add="+")
        self._sidebar_toggle_btn.bind("<ButtonRelease-1>", lambda e: self._sidebar_toggle_btn.configure(bg=Theme.SIDEBAR_HOVER), add="+")
        ToolTip(self._sidebar_toggle_btn, "折叠侧边栏 (Ctrl+B)")

        tk.Frame(toolbar, bg=Theme.SEPARATOR, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=10)

        about_btn = tk.Button(toolbar, text="关于", bg=Theme.HEADER_BG, fg=Theme.HEADER_TEXT,
                              font=("Microsoft YaHei UI", 9), relief=tk.FLAT, bd=0, cursor="hand2",
                              activebackground=Theme.SIDEBAR_HOVER, activeforeground=Theme.HEADER_TEXT,
                              command=self._show_about, padx=10, pady=2)
        about_btn.pack(side=tk.LEFT)
        about_btn.bind("<Enter>", lambda e: about_btn.configure(bg=Theme.SIDEBAR_HOVER))
        about_btn.bind("<Leave>", lambda e: about_btn.configure(bg=Theme.HEADER_BG))
        about_btn.bind("<Button-1>", lambda e: about_btn.configure(bg=Theme.darken(Theme.SIDEBAR_HOVER, 0.1)), add="+")
        about_btn.bind("<ButtonRelease-1>", lambda e: about_btn.configure(bg=Theme.SIDEBAR_HOVER), add="+")
        ToolTip(about_btn, "关于")

        exit_btn = tk.Button(toolbar, text="退出", bg=Theme.HEADER_BG, fg=Theme.HEADER_TEXT,
                             font=("Microsoft YaHei UI", 9), relief=tk.FLAT, bd=0, cursor="hand2",
                             activebackground=Theme.DANGER, activeforeground=Theme.HEADER_TEXT,
                             command=self._on_close, padx=10, pady=2)
        exit_btn.pack(side=tk.LEFT)
        exit_btn.bind("<Enter>", lambda e: exit_btn.configure(bg=Theme.DANGER))
        exit_btn.bind("<Leave>", lambda e: exit_btn.configure(bg=Theme.HEADER_BG))
        exit_btn.bind("<Button-1>", lambda e: exit_btn.configure(bg=Theme.darken(Theme.DANGER, 0.15)), add="+")
        exit_btn.bind("<ButtonRelease-1>", lambda e: exit_btn.configure(bg=Theme.DANGER), add="+")
        ToolTip(exit_btn, "退出 (Ctrl+Q)")

        # ── Main Content ──
        main = tk.Frame(self.root, bg=Theme.CONTENT_BG)
        main.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        self._sidebar = tk.Frame(main, bg=Theme.SIDEBAR_BG, width=self._sidebar_width)
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self._sidebar.pack_propagate(False)

        # Sidebar inner
        sb_top = tk.Frame(self._sidebar, bg=Theme.SIDEBAR_BG, height=48)
        sb_top.pack(fill=tk.X)
        sb_top.pack_propagate(False)
        tk.Label(sb_top, text="  取证工具", bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_MUTED,
                 font=("Microsoft YaHei UI", 9), padx=14, pady=14).pack(side=tk.LEFT)
        tk.Frame(self._sidebar, bg=Theme.SIDEBAR_DIVIDER, height=1).pack(fill=tk.X, padx=12)

        # Nav canvas
        self._nav_canvas = tk.Canvas(self._sidebar, bg=Theme.SIDEBAR_BG, highlightthickness=0)
        nav_scroll = ttk.Scrollbar(self._sidebar, orient=tk.VERTICAL, command=self._nav_canvas.yview)
        self._nav_frame = tk.Frame(self._nav_canvas, bg=Theme.SIDEBAR_BG)

        self._nav_frame.bind("<Configure>",
            lambda e: self._nav_canvas.configure(scrollregion=self._nav_canvas.bbox("all")))
        self._nav_canvas_win = self._nav_canvas.create_window((0, 0), window=self._nav_frame, anchor="nw")
        def _resize(e):
            self._nav_canvas.itemconfig(self._nav_canvas_win, width=e.width)
        self._nav_canvas.bind("<Configure>", _resize)
        self._nav_canvas.configure(yscrollcommand=nav_scroll.set)
        self._nav_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        nav_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Build nav
        self._nav_btns: list[NavButton] = []
        self._group_labels: list[tk.Frame] = []

        panel_index = {p.TITLE: i for i, p in enumerate(self._panels)}
        for group in PANEL_GROUPS:
            existing = [p for p in group["panels"] if p in panel_index]
            if not existing:
                continue
            grp = tk.Frame(self._nav_frame, bg=Theme.SIDEBAR_BG)
            grp.pack(fill=tk.X, pady=(12, 2))
            tk.Label(grp, text=f"  {group['name']}", bg=Theme.SIDEBAR_BG,
                     fg=Theme.SIDEBAR_GROUP, font=("Microsoft YaHei UI", 8, "bold"),
                     anchor="w", padx=14).pack(fill=tk.X)
            self._group_labels.append(grp)

            for title_en in existing:
                idx = panel_index[title_en]
                icon, name_cn = PANEL_NAMES.get(title_en, ("", title_en))
                btn = NavButton(
                    self._nav_frame, text=f"  {icon}  {name_cn}",
                    command=lambda i=idx: self._show_panel(i),
                    tooltip=name_cn,
                )
                btn.pack(fill=tk.X)
                self._nav_btns.append(btn)

        # Content area
        self._content = tk.Frame(main, bg=Theme.CONTENT_BG)
        self._content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)

        self._panel_container = tk.Frame(self._content, bg=Theme.CONTENT_BG)
        self._panel_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        # ── Status Bar ──
        status = tk.Frame(self.root, bg=Theme.STATUS_BG, height=24)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        status.pack_propagate(False)
        tk.Label(status, textvariable=self._status_var, bg=Theme.STATUS_BG,
                 fg=Theme.STATUS_TEXT, font=("Microsoft YaHei UI", 8),
                 padx=14).pack(side=tk.LEFT)
        tk.Label(status, text=f"v{VERSION}", bg=Theme.STATUS_BG,
                 fg=Theme.STATUS_TEXT, font=("Microsoft YaHei UI", 8),
                 padx=14).pack(side=tk.RIGHT)

    # ── Shortcuts ─────────────────────────────────────

    def _setup_shortcuts(self) -> None:
        self._shortcuts.bind("<Control-q>", self._on_close)
        self._shortcuts.bind("<Control-d>", self._toggle_theme)
        self._shortcuts.bind("<Control-b>", self._toggle_sidebar)
        self._shortcuts.bind("<Control-n>", self._next_panel)
        self._shortcuts.bind("<Control-p>", self._prev_panel)
        self._shortcuts.bind("<Control-e>", self._show_dashboard)

    def _show_dashboard(self) -> None:
        self._show_panel_by_title("Dashboard")

    def _next_panel(self) -> None:
        if self._current_panel:
            idx = self._panel_map.get(self._current_panel.TITLE, 0)
            self._show_panel((idx + 1) % len(self._panels))

    def _prev_panel(self) -> None:
        if self._current_panel:
            idx = self._panel_map.get(self._current_panel.TITLE, 0)
            self._show_panel((idx - 1) % len(self._panels))

    # ── Sidebar Animation ─────────────────────────────

    def _toggle_sidebar(self) -> None:
        if self._animating_sidebar:
            return
        self._animating_sidebar = True
        target = 0 if self._sidebar_collapsed else self._sidebar_width
        from_w = self._sidebar_width if self._sidebar_collapsed else 0
        self._sidebar_collapsed = not self._sidebar_collapsed

        if self._sidebar_collapsed:
            self._sidebar_toggle_btn.config(text="\u2630  展开侧栏")
        else:
            self._sidebar.pack(side=tk.LEFT, fill=tk.Y, before=self._content)

        def _done() -> None:
            if self._sidebar_collapsed:
                self._sidebar.pack_forget()
            else:
                self._sidebar_toggle_btn.config(text="\u2630  收起侧栏")
            self._animating_sidebar = False

        Animation.animate_width(self._sidebar, from_w, target,
                                duration_ms=220, easing="ease_out",
                                on_complete=_done)

    # ── Theme Toggle ─────────────────────────────────

    def _toggle_theme(self) -> None:
        new_mode = Theme.toggle()
        refresh_ttk_theme(self._style)
        self._theme_btn.config(text="\u2600  浅色" if new_mode == ThemeMode.DARK else "\u263e  深色")
        self.root.configure(bg=Theme.CONTENT_BG)
        self.root._main_window = self  # 供面板导航反向引用
        self._content.configure(bg=Theme.CONTENT_BG)
        self._panel_container.configure(bg=Theme.CONTENT_BG)

        self._sidebar.configure(bg=Theme.SIDEBAR_BG)
        self._nav_frame.configure(bg=Theme.SIDEBAR_BG)
        self._nav_canvas.configure(bg=Theme.SIDEBAR_BG)
        for grp in self._group_labels:
            grp.configure(bg=Theme.SIDEBAR_BG)
            for c in grp.winfo_children():
                try:
                    c.configure(bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_GROUP)
                except Exception:
                    pass
        for btn in self._nav_btns:
            btn.set_active(btn._active)

        if self._current_panel:
            self._refresh_colors(self._current_panel)

    def _refresh_colors(self, w: tk.Widget) -> None:
        c = Theme._c()
        for child in w.winfo_children():
            if isinstance(child, tk.Frame):
                try:
                    child.configure(bg=c.CONTENT_BG)
                except Exception:
                    pass
            elif isinstance(child, tk.Label):
                try:
                    child.configure(bg=c.CONTENT_BG, fg=c.TEXT_PRIMARY)
                except Exception:
                    pass
            elif isinstance(child, tk.Text):
                try:
                    child.configure(bg=c.PAPER_BG, fg=c.TEXT_PRIMARY,
                                    insertbackground=c.TEXT_PRIMARY)
                except Exception:
                    pass
            self._refresh_colors(child)

    # ── Panel Navigation ──────────────────────────────

    def _show_panel(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._panels):
            return
        panel_cls = self._panels[idx]

        # Clear
        for w in self._panel_container.winfo_children():
            w.destroy()

        panel = panel_cls(self._panel_container)
        panel.pack(fill=tk.BOTH, expand=True)
        panel.set_status_var(self._status_var)

        # Fade in
        panel.configure(bg=Theme.lighten(Theme.CONTENT_BG, 0.03))
        Animation.animate_fade(panel, Theme.lighten(Theme.CONTENT_BG, 0.03),
                               Theme.CONTENT_BG, duration_ms=180, easing="ease_out")

        panel.on_activate()
        self._current_panel = panel
        if isinstance(panel, LogViewerPanel):
            self._log_panel = panel

        for i, btn in enumerate(self._nav_btns):
            btn.set_active(i == idx)

        name_cn = PANEL_NAMES.get(panel_cls.TITLE, (panel_cls.TITLE, panel_cls.TITLE))[1]
        self._status_var.set(name_cn)

        if self._log_panel and not isinstance(panel, LogViewerPanel):
            self._log_panel.add_log(f"切换到面板: {name_cn}", "info")

    def _show_panel_by_title(self, title: str) -> None:
        self._show_panel(self._panel_map.get(title, 0))

    def _show_about(self) -> None:
        messagebox.showinfo("关于 Forensic Toolkit",
            f"Forensic Toolkit v{VERSION}\n\n"
            f"跨平台数字取证工具集\n"
            f"纯 Python 标准库，零外部依赖\n\n"
            f"快捷键:\n"
            f"  Ctrl+Q  退出    Ctrl+D  切换主题\n"
            f"  Ctrl+B  折叠侧栏  Ctrl+N/P  切换面板\n"
            f"  Ctrl+E  仪表盘")

    def _on_close(self) -> None:
        if self._session:
            self._session.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run_gui() -> None:
    from forensic_toolkit.cli.main import _import_all_modules
    _import_all_modules()
    MainWindow().run()


if __name__ == "__main__":
    run_gui()