"""
Reusable GUI widgets for Forensic Toolkit.

Includes:
  - ResultTreeView: tabular result display with copy/export
  - FilePicker: file/directory selection with Browse button
  - SectionFrame: titled collapsible frame
  - StatusBar: bottom status display
"""

from __future__ import annotations
import csv
import io
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any, Callable


def _fmt(n: int | float) -> str:
    """Human-readable byte size."""
    for u in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PiB"


class ResultTreeView(ttk.Frame):
    """Scrollable table for displaying structured results with copy/export."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self._data: list[dict] = []
        self._columns: list[str] = []
        self._tree: ttk.Treeview | None = None

        # toolbar
        tbar = ttk.Frame(self)
        tbar.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(tbar, text="Copy Selected", command=self._copy_selected).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(tbar, text="Copy All", command=self._copy_all).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(tbar, text="Export JSON", command=lambda: self._export("json")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(tbar, text="Export CSV", command=lambda: self._export("csv")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(tbar, text="Clear", command=self.clear).pack(side=tk.RIGHT, padx=(0, 4))
        ttk.Label(tbar, textvariable=tk.StringVar(value=""), font=("", 9, "italic")).pack(side=tk.RIGHT)

        # treeview container with scrollbars
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(container, orient=tk.HORIZONTAL)
        self._tree = ttk.Treeview(container, yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                  selectmode="extended")
        vsb.config(command=self._tree.yview)
        hsb.config(command=self._tree.xview)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

    @property
    def tree(self) -> ttk.Treeview:
        assert self._tree is not None
        return self._tree

    def load(self, data: Any) -> None:
        """Load a list-of-dict or dict result into the table."""
        self.clear()
        if not data:
            return
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list) or not data:
            return
        if isinstance(data[0], dict):
            self._columns = list(data[0].keys())
            self._data = data
        else:
            self._columns = ["Value"]
            self._data = [{"Value": str(item)} for item in data]

        self.tree["columns"] = self._columns
        self.tree["show"] = "headings"
        for col in self._columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=120, minwidth=60, stretch=True)

        for i, row in enumerate(self._data):
            values = [str(row.get(c, "")) for c in self._columns]
            self.tree.insert("", tk.END, iid=str(i), values=values)
        self._update_count()

    def clear(self) -> None:
        self._data = []
        self._columns = []
        if self._tree is not None:
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = []
            self.tree["show"] = "tree"
        self._update_count()

    def _update_count(self) -> None:
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for c in child.winfo_children():
                    if isinstance(c, ttk.Label):
                        c.config(text=f"{len(self._data)} rows")

    def _sort_by(self, col: str) -> None:
        if col not in self._columns:
            return
        idx = self._columns.index(col)
        self._data.sort(key=lambda r: str(r.get(col, "")))
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self._data):
            values = [str(row.get(c, "")) for c in self._columns]
            self.tree.insert("", tk.END, iid=str(i), values=values)

    def _get_selected_rows(self) -> list[dict]:
        sel = self.tree.selection()
        return [self._data[int(iid)] for iid in sel if iid.isdigit()]

    def _copy_selected(self) -> None:
        rows = self._get_selected_rows()
        if not rows:
            messagebox.showinfo("Copy", "No rows selected.")
            return
        text = json.dumps(rows, indent=2, ensure_ascii=False, default=str)
        self._copy_text(text)

    def _copy_all(self) -> None:
        if not self._data:
            messagebox.showinfo("Copy", "No data.")
            return
        text = json.dumps(self._data, indent=2, ensure_ascii=False, default=str)
        self._copy_text(text)

    @staticmethod
    def _copy_text(text: str) -> None:
        try:
            root = tk.Tk() if not tk._default_root else tk._default_root
            root.clipboard_clear()
            root.clipboard_append(text)
        except Exception:
            pass

    def _export(self, fmt: str) -> None:
        if not self._data:
            messagebox.showinfo("Export", "No data to export.")
            return
        ext = ".json" if fmt == "json" else ".csv"
        path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(fmt.upper(), f"*{ext}")])
        if not path:
            return
        try:
            if fmt == "json":
                with open(path, "w") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False, default=str)
            else:
                with open(path, "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=self._columns)
                    w.writeheader()
                    w.writerows(self._data)
            messagebox.showinfo("Export", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


class FilePicker(ttk.Frame):
    """File path input with Browse button and optional type filters."""

    def __init__(self, parent: tk.Widget, label: str = "Path:",
                 browse_mode: str = "file", filetypes: list[tuple[str, str]] | None = None,
                 default: str = "", **kwargs):
        super().__init__(parent, **kwargs)
        self._browse_mode = browse_mode
        self._filetypes = filetypes or [("All Files", "*")]
        self._var = tk.StringVar(value=default)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text=label).grid(row=0, column=0, padx=(0, 4), sticky="w")
        entry = ttk.Entry(self, textvariable=self._var)
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 4))
        ttk.Button(self, text="Browse", command=self._browse).grid(row=0, column=2, sticky="e")

    def get(self) -> str:
        return self._var.get().strip()

    def set(self, val: str) -> None:
        self._var.set(val)

    def bind_change(self, cb: Callable) -> None:
        self._var.trace_add("write", lambda *_: cb())

    def _browse(self) -> None:
        if self._browse_mode == "dir":
            p = filedialog.askdirectory(title="Select Directory")
        elif self._browse_mode == "save":
            p = filedialog.asksaveasfilename(title="Save As",
                                             filetypes=self._filetypes)
        else:
            p = filedialog.askopenfilename(title="Select File",
                                           filetypes=self._filetypes)
        if p:
            self._var.set(p)


class DirPicker(FilePicker):
    """Directory picker (convenience)."""
    def __init__(self, parent: tk.Widget, label: str = "Directory:", default: str = "", **kwargs):
        super().__init__(parent, label=label, browse_mode="dir", default=default, **kwargs)


class SectionFrame(ttk.LabelFrame):
    """A labeled frame that packs compactly with padding."""

    def __init__(self, parent: tk.Widget, title: str = "", **kwargs):
        super().__init__(parent, text=title, padding=8, **kwargs)


class AsyncRunner:
    """Run a blocking function in a background thread with UI feedback."""

    def __init__(self, parent: tk.Widget, status_var: tk.StringVar | None = None):
        self._parent = parent
        self._status = status_var or tk.StringVar()
        self._progress: ttk.Progressbar | None = None

    def run(self, target: Callable, on_done: Callable[[Any], None],
            args: tuple = (), kwargs: dict | None = None) -> None:
        """Execute *target* in a thread, call *on_done* with result on main thread."""
        import threading

        self._status.set("Running...")
        self._create_progress()

        def _work() -> None:
            try:
                result = target(*args, **(kwargs or {}))
            except Exception as e:
                result = {"error": str(e)}
            self._parent.after(0, lambda: self._finish(result, on_done))

        t = threading.Thread(target=_work, daemon=True)
        t.start()

    def _create_progress(self) -> None:
        if self._progress is None:
            self._progress = ttk.Progressbar(self._parent, mode="indeterminate", length=200)
            self._progress.pack(side=tk.BOTTOM, fill=tk.X, pady=2)
        self._progress.start(10)

    def _finish(self, result: Any, on_done: Callable) -> None:
        if self._progress:
            self._progress.stop()
            self._progress.destroy()
            self._progress = None
        self._status.set("Done" if "error" not in (result or {}) else "Error")
        on_done(result)


def RunButton(parent: tk.Widget, text: str = "Run", command: Callable | None = None, **kwargs):
    """Prominent action button with icon-like styling."""
    btn = ttk.Button(parent, text=f"\u25b6  {text}", command=command, **kwargs)
    return btn
