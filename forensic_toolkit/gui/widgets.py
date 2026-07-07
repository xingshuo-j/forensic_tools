"""
Reusable GUI widgets for Forensic Toolkit.
Includes:
  - ResultTreeView: tabular result display with copy/export
  - FilePicker: file/directory selection with Browse button
  - SectionFrame: titled collapsible frame
  - AsyncRunner: background thread execution
"""

from __future__ import annotations
import csv
import io
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any, Callable

from forensic_toolkit.gui.theme import Theme

# ── Color Palette ─────────────────────────────────────

def _fmt(n: int | float) -> str:
    """Human-readable byte size."""
    for u in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PiB"

# ── Result TreeView ───────────────────────────────────

class ResultTreeView(ttk.Frame):
    """Scrollable table for displaying structured results with copy/export."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self._data: list[dict] = []
        self._columns: list[str] = []
        self._tree: ttk.Treeview | None = None
        self._count_label: ttk.Label | None = None

        # Toolbar
        tbar = ttk.Frame(self)
        tbar.pack(fill=tk.X, pady=(0, 6))

        ttk.Button(tbar, text="复制选定", command=self._copy_selected).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(tbar, text="复制全部", command=self._copy_all).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(tbar, text="导出 JSON", command=lambda: self._export("json")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(tbar, text="导出 CSV", command=lambda: self._export("csv")).pack(side=tk.LEFT, padx=(0, 4))

        self._count_label = ttk.Label(tbar, text="", font=("", 9))
        self._count_label.pack(side=tk.RIGHT, padx=(0, 6))
        ttk.Button(tbar, text="清空", command=self.clear).pack(side=tk.RIGHT, padx=(0, 4))

        # Treeview with scrollbars
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

        # Configure TreeView style
        style = ttk.Style()
        style.configure("Result.Treeview", rowheight=26, font=("", 9))
        style.configure("Result.Treeview.Heading", font=("", 9, "bold"), padding=(6, 4))

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
            iid = str(i)
            tags = ("evenrow",) if i % 2 == 0 else ("oddrow",)
            self.tree.insert("", tk.END, iid=iid, values=values, tags=tags)

        self.tree.tag_configure("evenrow", background=Theme.TABLE_STRIPE)
        self.tree.tag_configure("oddrow", background=Theme.PAPER_BG)
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
        if self._count_label:
            self._count_label.config(text=f"{len(self._data)} 条记录")

    def _sort_by(self, col: str) -> None:
        if col not in self._columns:
            return
        self._data.sort(key=lambda r: str(r.get(col, "")))
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self._data):
            values = [str(row.get(c, "")) for c in self._columns]
            tags = ("evenrow",) if i % 2 == 0 else ("oddrow",)
            self.tree.insert("", tk.END, iid=str(i), values=values, tags=tags)

    def _get_selected_rows(self) -> list[dict]:
        sel = self.tree.selection()
        return [self._data[int(iid)] for iid in sel if iid.isdigit()]

    def _copy_selected(self) -> None:
        rows = self._get_selected_rows()
        if not rows:
            messagebox.showinfo("复制", "未选定任何行。")
            return
        text = json.dumps(rows, indent=2, ensure_ascii=False, default=str)
        self._copy_text(text)

    def _copy_all(self) -> None:
        if not self._data:
            messagebox.showinfo("复制", "无数据可复制。")
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
            messagebox.showinfo("导出", "无数据可导出。")
            return
        ext = ".json" if fmt == "json" else ".csv"
        path = filedialog.asksaveasfilename(
            defaultextension=ext, filetypes=[(fmt.upper(), f"*{ext}")],
            title=f"导出为 {fmt.upper()}"
        )
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
            messagebox.showinfo("导出", f"已保存至 {path}")
        except Exception as e:
            messagebox.showerror("导出错误", str(e))

# ── File / Directory Picker ──────────────────────────

class FilePicker(ttk.Frame):
    """File path input with browse button."""

    def __init__(self, parent: tk.Widget, label: str = "路径:",
                 browse_mode: str = "file", filetypes: list[tuple[str, str]] | None = None,
                 default: str = "", **kwargs):
        super().__init__(parent, **kwargs)
        self._browse_mode = browse_mode
        self._filetypes = filetypes or [("所有文件", "*")]
        self._var = tk.StringVar(value=default)
        self.columnconfigure(1, weight=1)

        lbl = ttk.Label(self, text=label, font=("", 10))
        lbl.grid(row=0, column=0, padx=(0, 6), sticky="w")
        entry = ttk.Entry(self, textvariable=self._var, font=("", 10))
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        ttk.Button(self, text="浏览...", command=self._browse).grid(row=0, column=2, sticky="e")

    def get(self) -> str:
        return self._var.get().strip()

    def set(self, val: str) -> None:
        self._var.set(val)

    def bind_change(self, cb: Callable) -> None:
        self._var.trace_add("write", lambda *_: cb())

    def _browse(self) -> None:
        try:
            import os
            parent = self.winfo_toplevel()
            current = self.get()
            if current and os.path.exists(current):
                if os.path.isdir(current):
                    initialdir = current
                else:
                    initialdir = os.path.dirname(current) or os.path.expanduser("~")
            else:
                initialdir = os.path.expanduser("~")
            if not os.path.isdir(initialdir):
                initialdir = "/"
            self.update_idletasks()
            if self._browse_mode == "dir":
                p = filedialog.askdirectory(title="选择目录", parent=parent,
                                            initialdir=initialdir)
            elif self._browse_mode == "save":
                p = filedialog.asksaveasfilename(
                    title="保存为", filetypes=self._filetypes, parent=parent,
                    initialdir=initialdir)
            else:
                p = filedialog.askopenfilename(
                    title="选择文件", filetypes=self._filetypes, parent=parent,
                    initialdir=initialdir)
            if p:
                self._var.set(p)
        except Exception as e:
            messagebox.showerror("对话框错误", f"无法打开文件选择对话框: {e}")

class DirPicker(FilePicker):
    """Directory picker (convenience)."""
    def __init__(self, parent: tk.Widget, label: str = "目录:", default: str = "", **kwargs):
        super().__init__(parent, label=label, browse_mode="dir", default=default, **kwargs)

# ── Section Frame ────────────────────────────────────

class SectionFrame(ttk.LabelFrame):
    """A labeled frame with consistent padding."""
    def __init__(self, parent: tk.Widget, title: str = "", **kwargs):
        super().__init__(parent, text=title, padding=10, **kwargs)

# ── Progress Runner ──────────────────────────────────

class AsyncRunner:
    """Run a blocking function in a background thread with UI feedback."""

    def __init__(self, parent: tk.Widget, status_var: tk.StringVar | None = None):
        self._parent = parent
        self._status = status_var or tk.StringVar()
        self._progress: ttk.Progressbar | None = None

    def run(self, target: Callable, on_done: Callable[[Any], None],
            args: tuple = (), kwargs: dict | None = None) -> None:
        import threading

        self._status.set("执行中...")
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
            self._progress = ttk.Progressbar(self._parent, mode="indeterminate", length=300)
            self._progress.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 0))
        self._progress.start(10)

    def _finish(self, result: Any, on_done: Callable) -> None:
        if self._progress:
            self._progress.stop()
            self._progress.destroy()
            self._progress = None
        self._status.set("完成" if "error" not in (result or {}) else "错误")
        on_done(result)

# ── Run Button factory ───────────────────────────────

def RunButton(parent: tk.Widget, text: str = "执行", command: Callable | None = None, **kwargs):
    """Prominent action button."""
    btn = ttk.Button(parent, text=f"\u25b6  {text}", command=command)
    return btn
