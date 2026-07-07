"""
Forensic Toolkit GUI - Main Application Window
A Tkinter-based cross-platform desktop GUI for digital forensics.
Built entirely on Python stdlib (zero external dependencies).
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any

from forensic_toolkit.core.platform import Platform
from forensic_toolkit.core.module_base import ModuleRegistry
from forensic_toolkit.gui.panels import get_panels, BasePanel
from forensic_toolkit.gui.theme import Theme, PANEL_NAMES, setup_ttk_theme
from forensic_toolkit.core.evidence import EvidenceSession

VERSION = "0.2.0"

# ── Color Palette ─────────────────────────────────────



class MainWindow:
    """Main application window with dark sidebar navigation and panel area."""

    # Panel name mapping (English TITLE -> Chinese display name)

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Forensic Toolkit v{VERSION} - \u6570\u5b57\u53d6\u8bc1\u5de5\u5177\u96c6")
        self.root.geometry("1200x750")
        self.root.minsize(900, 550)
        self.root.configure(bg=Theme.CONTENT_BG)

        # Theme
        setup_ttk_theme()

        # State
        self._status_var = tk.StringVar(value="就绪")
        self._output_dir = tk.StringVar(value="./ftk_output")
        self._session: EvidenceSession | None = None

        # Build UI
        self._panels = get_panels()
        self._build_layout()

        # Bind close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Show dashboard
        self._current_panel: BasePanel | None = None
        self.root.after(100, lambda: self._show_panel(0))
    def _build_layout(self) -> None:
        # ── Top header bar ──
        header = tk.Frame(self.root, bg=Theme.HEADER_BG, height=44)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(header, text=f"Forensic Toolkit", bg=Theme.HEADER_BG,
                 fg=Theme.HEADER_TEXT, font=("", 12, "bold"), padx=12, pady=8).pack(side=tk.LEFT)
        tk.Label(header, text=f"v{VERSION}", bg=Theme.HEADER_BG,
                 fg="#94a3b8", font=("", 9), padx=6, pady=10).pack(side=tk.LEFT)

        # Quick actions in header
        btn_frame = tk.Frame(header, bg=Theme.HEADER_BG)
        btn_frame.pack(side=tk.RIGHT, padx=8)
        tk.Button(btn_frame, text="关于", bg=Theme.HEADER_BG, fg=Theme.HEADER_TEXT,
                  font=("", 9), relief=tk.FLAT, bd=0, cursor="hand2",
                  activebackground=Theme.SIDEBAR_HOVER, activeforeground=Theme.HEADER_TEXT,
                  command=self._show_about, padx=10).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="退出", bg=Theme.HEADER_BG, fg=Theme.HEADER_TEXT,
                  font=("", 9), relief=tk.FLAT, bd=0, cursor="hand2",
                  activebackground="#dc2626", activeforeground=Theme.HEADER_TEXT,
                  command=self._on_close, padx=10).pack(side=tk.LEFT)

        # ── Main content ──
        main = tk.Frame(self.root, bg=Theme.CONTENT_BG)
        main.pack(fill=tk.BOTH, expand=True)

        # Left sidebar (dark)
        self._sidebar = tk.Frame(main, bg=Theme.SIDEBAR_BG, width=210)
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self._sidebar.pack_propagate(False)

        # Sidebar title
        sb_header = tk.Frame(self._sidebar, bg=Theme.SIDEBAR_BG, height=40)
        sb_header.pack(fill=tk.X)
        sb_header.pack_propagate(False)
        tk.Label(sb_header, text="取证工具", bg=Theme.SIDEBAR_BG, fg="#94a3b8",
                 font=("", 9), padx=14, pady=10).pack(side=tk.LEFT)

        # Separator
        tk.Frame(self._sidebar, bg=Theme.SEPARATOR, height=1).pack(fill=tk.X, padx=10)

        # Scrollable nav buttons
        nav_canvas = tk.Canvas(self._sidebar, bg=Theme.SIDEBAR_BG, highlightthickness=0, width=190)
        nav_scroll = ttk.Scrollbar(self._sidebar, orient=tk.VERTICAL, command=nav_canvas.yview)
        self._nav_frame = tk.Frame(nav_canvas, bg=Theme.SIDEBAR_BG)

        self._nav_frame.bind("<Configure>",
            lambda e: nav_canvas.configure(scrollregion=nav_canvas.bbox("all")))
        nav_canvas.create_window((0, 0), window=self._nav_frame, anchor="nw")
        nav_canvas.configure(yscrollcommand=nav_scroll.set)

        nav_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0)
        nav_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Build nav buttons
        self._nav_btns: list[tk.Button] = []
        for i, panel_cls in enumerate(self._panels):
            title_en = panel_cls.TITLE
            icon, name_cn = PANEL_NAMES.get(title_en, ("\u25b6", title_en))
            btn = tk.Button(
                self._nav_frame, text=f"  {icon}  {name_cn}",
                bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_TEXT,
                font=("", 10), relief=tk.FLAT, bd=0,
                anchor="w", padx=14, pady=8, cursor="hand2",
                activebackground=Theme.SIDEBAR_HOVER,
                activeforeground=Theme.SIDEBAR_TEXT,
                command=lambda idx=i: self._show_panel(idx),
            )
            btn.pack(fill=tk.X)
            self._nav_btns.append(btn)

        # Content area (right side)
        self._content = tk.Frame(main, bg=Theme.CONTENT_BG)
        self._content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel container
        self._panel_container = tk.Frame(self._content, bg=Theme.CONTENT_BG)
        self._panel_container.pack(fill=tk.BOTH, expand=True)

        # ── Status bar ──
        status = tk.Frame(self.root, bg=Theme.STATUS_BG, height=28)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        status.pack_propagate(False)

        tk.Label(status, textvariable=self._status_var, bg=Theme.STATUS_BG,
                 fg=Theme.STATUS_TEXT, font=("", 8), padx=10).pack(side=tk.LEFT)
        tk.Label(status, text=f"v{VERSION}", bg=Theme.STATUS_BG,
                 fg=Theme.STATUS_TEXT, font=("", 8)).pack(side=tk.RIGHT, padx=10)
        tk.Label(status, text=f"平台: {Platform.info.system}", bg=Theme.STATUS_BG,
                 fg=Theme.STATUS_TEXT, font=("", 8)).pack(side=tk.RIGHT, padx=10)
        tk.Label(status, textvariable=self._output_dir, bg=Theme.STATUS_BG,
                 fg=Theme.STATUS_TEXT, font=("", 8)).pack(side=tk.RIGHT, padx=6)

    def _show_about(self) -> None:
        msg = (
            f"Forensic Toolkit v{VERSION}\n\n"
            "跨平台数字取证工具集\n"
            "纯 Python 标准库，零外部依赖\n\n"
            f"平台: {Platform.info.system} {Platform.info.release}\n"
            f"管理员权限: {'是' if Platform.info.is_admin else '否'}\n"
            f"已注册模块: {len(ModuleRegistry.list())} 个"
        )
        messagebox.showinfo("关于 Forensic Toolkit", msg)

    def _show_panel(self, idx: int) -> None:
        """Switch to panel by index."""
        for w in self._panel_container.winfo_children():
            w.destroy()

        panel_cls = self._panels[idx]
        panel = panel_cls(self._panel_container)
        panel.pack(fill=tk.BOTH, expand=True)
        panel.set_status_var(self._status_var)


        panel.on_activate()
        self._current_panel = panel

        # Update nav buttons highlight
        for i, btn in enumerate(self._nav_btns):
            if i == idx:
                btn.config(bg=Theme.SIDEBAR_ACTIVE, fg="#ffffff")
            else:
                btn.config(bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_TEXT)

        self._status_var.set(f"已选择: {PANEL_NAMES.get(panel_cls.TITLE, (panel_cls.TITLE, panel_cls.TITLE))[1]}")

    def _on_close(self) -> None:
        if self._session:
            self._session.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run_gui() -> None:
    """Entry point for the GUI application."""
    from forensic_toolkit.cli.main import _import_all_modules
    _import_all_modules()
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    run_gui()
