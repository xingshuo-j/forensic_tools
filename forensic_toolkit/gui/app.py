"""
Forensic Toolkit GUI - Main Application Window

A Tkinter-based cross-platform desktop GUI for digital forensics.
Built entirely on Python stdlib (zero external dependencies).
"""

from __future__ import annotations
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any

from forensic_toolkit.core.platform import Platform
from forensic_toolkit.core.module_base import ModuleRegistry
from forensic_toolkit.gui.panels import get_panels, BasePanel
from forensic_toolkit.core.evidence import EvidenceSession

VERSION = "0.2.0"


class MainWindow:
    """Main application window with sidebar navigation and panel area."""

    NAV_ICONS: dict[str, str] = {
        "Dashboard":  "\U0001f4ca",
        "Disk":       "\U0001f4be",
        "Filesystem": "\U0001f4c1",
        "Carving":    "\U0001f58c",
        "Strings":    "\U0001f521",
        "Hash":       "\U0001f511",
        "Hunt":       "\U0001f50d",
        "Metadata":   "\U0001f4dd",
        "Network":    "\U0001f310",
        "Memory":     "\U0001f4ac",
        "Registry":   "\U0001f4cb",
        "Recovery":   "\U0001f4fa",
    }

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Forensic Toolkit v{VERSION}")
        self.root.geometry("1200x750")
        self.root.minsize(800, 500)

        # Try to set a nicer theme
        style = ttk.Style()
        available = style.theme_names()
        for preferred in ("clam", "alt", "default"):
            if preferred in available:
                style.theme_use(preferred)
                break

        # Status bar variable
        self._status_var = tk.StringVar(value="Ready")
        self._output_dir = tk.StringVar(value="./ftk_output")
        self._session: EvidenceSession | None = None

        # ── Build UI ──
        self._build_menu()
        self._build_layout()

        # ── Bind close ──
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Show dashboard by default
        self._current_panel: BasePanel | None = None
        self._show_panel(0)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Set Output Directory", command=self._set_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="New Evidence Session", command=self._new_session)
        tools_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Tools", menu=tools_menu)

    def _build_layout(self) -> None:
        # Main container
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        self._sidebar = ttk.Frame(main, width=200, relief=tk.RAISED, borderwidth=1)
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        self._sidebar.pack_propagate(False)

        # Header in sidebar
        hdr = ttk.Label(self._sidebar, text="Forensic Toolkit",
                        font=("", 11, "bold"), padding=8)
        hdr.pack(fill=tk.X)

        ttk.Separator(self._sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Navigation buttons canvas with scroll
        nav_canvas = tk.Canvas(self._sidebar, highlightthickness=0, width=190)
        nav_scroll = ttk.Scrollbar(self._sidebar, orient=tk.VERTICAL, command=nav_canvas.yview)
        nav_frame = ttk.Frame(nav_canvas)

        nav_frame.bind("<Configure>", lambda e: nav_canvas.configure(scrollregion=nav_canvas.bbox("all")))
        nav_canvas.create_window((0, 0), window=nav_frame, anchor="nw")
        nav_canvas.configure(yscrollcommand=nav_scroll.set)

        nav_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        nav_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Build nav buttons
        self._panels = get_panels()
        self._nav_btns: list[ttk.Button] = []

        for i, panel_cls in enumerate(self._panels):
            title = panel_cls.TITLE
            icon = self.NAV_ICONS.get(title, "\u25b6")
            btn = ttk.Button(
                nav_frame, text=f"  {icon}  {title}",
                style="Nav.TButton",
                command=lambda idx=i: self._show_panel(idx),
            )
            btn.pack(fill=tk.X, padx=4, pady=1)
            self._nav_btns.append(btn)

        # Content area
        content = ttk.Frame(main)
        content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Panel container (with padding)
        self._panel_container = ttk.Frame(content, padding=6)
        self._panel_container.pack(fill=tk.BOTH, expand=True)

        # Status bar
        status = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status, textvariable=self._status_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(status, text=f"v{VERSION}").pack(side=tk.RIGHT, padx=4)
        ttk.Label(status, text=f"Platform: {Platform.info.system}").pack(side=tk.RIGHT, padx=10)

        # Configure navigation button style
        style = ttk.Style()
        style.configure("Nav.TButton", anchor="w", padding=(6, 4))

    def _set_output_dir(self) -> None:
        from tkinter import filedialog
        d = filedialog.askdirectory(title="Select Output Directory",
                                    initialdir=self._output_dir.get())
        if d:
            self._output_dir.set(d)
            self._status_var.set(f"Output: {d}")

    def _new_session(self) -> None:
        if self._session:
            self._session.close()
        self._session = EvidenceSession(self._output_dir.get())
        self._status_var.set(f"Session: {self._session.session_id[:12]}...")

    def _show_about(self) -> None:
        msg = (
            f"Forensic Toolkit v{VERSION}\n\n"
            "Cross-platform digital forensic toolkit\n"
            "Zero external dependencies\n\n"
            f"Platform: {Platform.info.system} {Platform.info.release}\n"
            f"Admin: {'Yes' if Platform.info.is_admin else 'No'}\n"
            f"Modules: {len(ModuleRegistry.list())}"
        )
        messagebox.showinfo("About Forensic Toolkit", msg)

    def _show_panel(self, idx: int) -> None:
        """Switch to panel by index."""
        # Destroy current panel
        for w in self._panel_container.winfo_children():
            w.destroy()

        panel_cls = self._panels[idx]
        panel = panel_cls(self._panel_container)
        panel.pack(fill=tk.BOTH, expand=True)
        panel.set_status_var(self._status_var)
        panel.on_activate()
        self._current_panel = panel

        # Highlight active nav button
        for i, btn in enumerate(self._nav_btns):
            if i == idx:
                btn.config(state=tk.DISABLED)
            else:
                btn.config(state=tk.NORMAL)

    def _on_close(self) -> None:
        if self._session:
            self._session.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run_gui() -> None:
    """Entry point for the GUI application."""
    # Import modules before starting GUI
    from forensic_toolkit.cli.main import _import_all_modules
    _import_all_modules()

    app = MainWindow()
    app.run()


if __name__ == "__main__":
    run_gui()
