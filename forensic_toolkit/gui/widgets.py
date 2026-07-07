"""
Apple-inspired reusable widgets for Forensic Toolkit GUI.

Design language: generous whitespace, rounded corners,
subtle depth, smooth animations, clean typography.
"""

from __future__ import annotations
import csv, json, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any, Callable
from forensic_toolkit.gui.theme import Theme, Animation


# ── Helpers ───────────────────────────────────────────

def _fmt(n: int | float) -> str:
    for u in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PiB"


# ── ToolTip ───────────────────────────────────────────

class ToolTip:
    """Apple-style tooltip with fade-in animation."""
    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self._widget = widget
        self._text = text
        self._delay = delay
        self._tip_window: tk.Toplevel | None = None
        self._after_id: str | None = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, event=None) -> None:
        self._after_id = self._widget.after(self._delay, self._show)

    def _show(self) -> None:
        if self._tip_window:
            return
        x = self._widget.winfo_rootx() + 12
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
        self._tip_window = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-alpha", 0.0)
        label = tk.Label(tw, text=self._text, justify=tk.LEFT,
                         bg=Theme.TOOLTIP_BG, fg=Theme.TOOLTIP_FG,
                         font=("Microsoft YaHei UI", 9), padx=10, pady=5,
                         relief=tk.FLAT, borderwidth=0)
        label.pack()
        self._fade_in(tw, 0)

    def _fade_in(self, tw: tk.Toplevel, step: int) -> None:
        if not self._tip_window or self._tip_window != tw:
            return
        try:
            tw.attributes("-alpha", min(1.0, step / 10))
        except Exception:
            return
        if step < 10:
            tw.after(16, lambda: self._fade_in(tw, step + 1))

    def _hide(self, event=None) -> None:
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        if self._tip_window:
            try:
                self._tip_window.destroy()
            except Exception:
                pass
            self._tip_window = None


# ── RoundedCard ───────────────────────────────────────

class RoundedCard(tk.Frame):
    """Apple-style card: white bg, subtle border, rounded corners, generous padding."""

    def __init__(self, parent: tk.Widget, padding: int = 20, radius: int = 12, **kwargs):
        super().__init__(parent, bg=Theme.CARD_BG, highlightbackground=Theme.CARD_BORDER,
                         highlightthickness=1, **kwargs)
        self._padding = padding
        self._radius = radius
        self._hover = False
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None) -> None:
        if not self._hover:
            self._hover = True
            Animation.animate_color(self, "highlightbackground",
                                    Theme.CARD_BORDER, Theme.CARD_HOVER_BORDER,
                                    duration_ms=200, easing="ease_out")

    def _on_leave(self, event=None) -> None:
        if self._hover:
            self._hover = False
            Animation.animate_color(self, "highlightbackground",
                                    Theme.CARD_HOVER_BORDER, Theme.CARD_BORDER,
                                    duration_ms=200, easing="ease_out")


# ── FeatureCard ───────────────────────────────────────

class FeatureCard(tk.Frame):
    """Multi-color feature card: icon + accent bar + title + description + action."""

    def __init__(self, parent: tk.Widget, icon: str = "\u25a1",
                 title: str = "", description: str = "",
                 action_text: str = "", action_command: Callable | None = None,
                 accent: str = "#0d9488", padding: int = 20, **kwargs):
        super().__init__(parent, bg=Theme.CARD_BG, highlightbackground=Theme.CARD_BORDER,
                         highlightthickness=1, **kwargs)
        self._hover = False
        self._accent = accent
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # Accent color bar at top
        tk.Frame(self, bg=accent, height=3).pack(fill=tk.X)

        # Icon
        icon_lbl = tk.Label(self, text=icon, bg=Theme.CARD_BG, fg=accent,
                            font=("Microsoft YaHei UI", 20))
        icon_lbl.pack(anchor="w", padx=padding, pady=(padding, 2))

        # Title
        tk.Label(self, text=title, bg=Theme.CARD_BG, fg=Theme.TEXT_PRIMARY,
                 font=("Microsoft YaHei UI", 12, "bold"),
                 anchor="w", justify=tk.LEFT, wraplength=200).pack(
            fill=tk.X, padx=padding, pady=(0, 4))

        # Description
        tk.Label(self, text=description, bg=Theme.CARD_BG, fg=Theme.TEXT_SECONDARY,
                 font=("Microsoft YaHei UI", 9),
                 anchor="w", justify=tk.LEFT, wraplength=200).pack(
            fill=tk.X, padx=padding, pady=(0, 10))

        # Action link
        if action_text and action_command:
            link = tk.Label(self, text=action_text + " \u203a", bg=Theme.CARD_BG,
                            fg=accent, font=("Microsoft YaHei UI", 9),
                            cursor="hand2")
            link.pack(anchor="w", padx=padding, pady=(0, padding))
            link.bind("<Button-1>", lambda e: action_command())
            link.bind("<Enter>", lambda e: link.configure(fg=Theme.ACCENT3))
            link.bind("<Leave>", lambda e: link.configure(fg=accent))

    def _on_enter(self, event=None) -> None:
        if not self._hover:
            self._hover = True
            Animation.animate_color(self, "highlightbackground",
                                    Theme.CARD_BORDER, Theme.CARD_HOVER_BORDER,
                                    duration_ms=200, easing="ease_out")

    def _on_leave(self, event=None) -> None:
        if self._hover:
            self._hover = False
            Animation.animate_color(self, "highlightbackground",
                                    Theme.CARD_HOVER_BORDER, Theme.CARD_BORDER,
                                    duration_ms=200, easing="ease_out")


# ── HeroSection ───────────────────────────────────────

class HeroSection(tk.Frame):
    """Apple-style hero banner: large title, subtitle, CTA button."""

    def __init__(self, parent: tk.Widget, title: str = "", subtitle: str = "",
                 cta_text: str = "", cta_command: Callable | None = None, **kwargs):
        super().__init__(parent, bg=Theme.CONTENT_BG, **kwargs)

        # Large title
        tk.Label(self, text=title, bg=Theme.CONTENT_BG, fg=Theme.TEXT_PRIMARY,
                 font=("Microsoft YaHei UI", 32, "bold"),
                 anchor="w", justify=tk.LEFT).pack(anchor="w", pady=(0, 8))

        # Subtitle
        if subtitle:
            tk.Label(self, text=subtitle, bg=Theme.CONTENT_BG, fg=Theme.TEXT_SECONDARY,
                     font=("Microsoft YaHei UI", 15),
                     anchor="w", justify=tk.LEFT).pack(anchor="w", pady=(0, 20))

        # CTA
        if cta_text and cta_command:
            AnimatedButton(self, text=cta_text, command=cta_command,
                           padding=(24, 10), font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")


# ── AnimatedButton ────────────────────────────────────

class AnimatedButton(tk.Button):
    """Apple-style button with hover glow animation."""

    def __init__(self, parent: tk.Widget, text: str = "", command: Callable | None = None,
                 bg: str | None = None, fg: str | None = None,
                 hover_bg: str | None = None, hover_fg: str | None = None,
                 font: tuple | None = None, padding: tuple[int, int] = (14, 6),
                 tooltip: str = "", **kwargs):
        self._base_bg = bg or Theme.ACCENT
        self._base_fg = fg or Theme.ACCENT_TEXT
        self._hover_bg = hover_bg or Theme.ACCENT_HOVER
        self._hover_fg = hover_fg or Theme.ACCENT_TEXT
        self._is_hovering = False

        super().__init__(parent, text=text, command=command,
                         bg=self._base_bg, fg=self._base_fg,
                         font=font or ("Microsoft YaHei UI", 9, "bold"),
                         relief=tk.FLAT, bd=0, cursor="hand2",
                         padx=padding[0], pady=padding[1],
                         activebackground=self._hover_bg,
                         activeforeground=self._hover_fg, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        if tooltip:
            ToolTip(self, tooltip)

    def _on_enter(self, event=None) -> None:
        if not self._is_hovering:
            self._is_hovering = True
            Animation.animate_color(self, "bg", self._base_bg, self._hover_bg,
                                    duration_ms=120, easing="ease_out")

    def _on_leave(self, event=None) -> None:
        if self._is_hovering:
            self._is_hovering = False
            Animation.animate_color(self, "bg", self._hover_bg, self._base_bg,
                                    duration_ms=180, easing="ease_out")


# ── NavButton ─────────────────────────────────────────

class NavButton(tk.Button):
    """Apple-style sidebar navigation button."""

    def __init__(self, parent: tk.Widget, text: str = "", command: Callable | None = None,
                 tooltip: str = "", **kwargs):
        super().__init__(parent, text=text, command=command,
                         bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_TEXT,
                         font=("Microsoft YaHei UI", 10), relief=tk.FLAT, bd=0,
                         anchor="w", padx=18, pady=8, cursor="hand2",
                         activebackground=Theme.SIDEBAR_HOVER,
                         activeforeground=Theme.SIDEBAR_TEXT, **kwargs)
        self._active = False
        self._base_bg = Theme.SIDEBAR_BG
        self._hover_bg = Theme.SIDEBAR_HOVER
        self._active_bg = Theme.SIDEBAR_ACTIVE
        self._active_fg = Theme.SIDEBAR_TEXT_ACTIVE
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        if tooltip:
            ToolTip(self, tooltip)

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self.configure(bg=self._active_bg, fg=self._active_fg)
        else:
            self.configure(bg=self._base_bg, fg=Theme.SIDEBAR_TEXT)

    def _on_enter(self, event=None) -> None:
        if not self._active:
            Animation.animate_color(self, "bg", self._base_bg, self._hover_bg,
                                    duration_ms=100, easing="ease_out")

    def _on_leave(self, event=None) -> None:
        if not self._active:
            Animation.animate_color(self, "bg", self._hover_bg, self._base_bg,
                                    duration_ms=150, easing="ease_out")


# ── SearchBar ─────────────────────────────────────────

class SearchBar(ttk.Frame):
    def __init__(self, parent: tk.Widget, placeholder: str = "搜索...",
                 on_change: Callable[[str], None] | None = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_change = on_change
        self._var = tk.StringVar()
        self.columnconfigure(0, weight=1)
        self._entry = ttk.Entry(self, textvariable=self._var, font=("Microsoft YaHei UI", 9))
        self._entry.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        self._entry.insert(0, placeholder)
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<KeyRelease>", self._on_key)
        self._entry.configure(foreground=Theme.TEXT_MUTED)

        self._clear_btn = tk.Button(self, text="\u2715", font=("", 8),
                                    bg=Theme.CONTENT_BG, fg=Theme.TEXT_MUTED,
                                    relief=tk.FLAT, bd=0, cursor="hand2",
                                    activebackground=Theme.DANGER_BG,
                                    activeforeground=Theme.DANGER, command=self._clear)
        self._clear_btn.grid(row=0, column=1, sticky="e")
        self._clear_btn.grid_remove()
        self._placeholder = placeholder
        self._has_placeholder = True

    def _on_focus_in(self, event=None) -> None:
        if self._has_placeholder:
            self._entry.delete(0, tk.END)
            self._entry.configure(foreground=Theme.TEXT_PRIMARY)
            self._has_placeholder = False

    def _on_focus_out(self, event=None) -> None:
        if not self._var.get().strip():
            self._entry.insert(0, self._placeholder)
            self._entry.configure(foreground=Theme.TEXT_MUTED)
            self._has_placeholder = True

    def _on_key(self, event=None) -> None:
        if self._has_placeholder:
            return
        text = self._var.get()
        if text:
            self._clear_btn.grid()
        else:
            self._clear_btn.grid_remove()
        if self._on_change:
            self._on_change(text)

    def _clear(self) -> None:
        self._var.set("")
        self._clear_btn.grid_remove()
        if self._on_change:
            self._on_change("")
        self._entry.focus_set()

    def get(self) -> str:
        return "" if self._has_placeholder else self._var.get().strip()


# ── StatusBadge ───────────────────────────────────────

class StatusBadge(tk.Frame):
    COLORS = {
        "success": (Theme.SUCCESS_BG, Theme.SUCCESS),
        "warning": (Theme.WARNING_BG, Theme.WARNING),
        "danger": (Theme.DANGER_BG, Theme.DANGER),
        "info": (Theme.INFO_BG, Theme.INFO),
    }

    def __init__(self, parent: tk.Widget, text: str = "", kind: str = "info", **kwargs):
        super().__init__(parent, **kwargs)
        bg, fg = self.COLORS.get(kind, self.COLORS["info"])
        self.configure(bg=bg)
        self._label = tk.Label(self, text=text, bg=bg, fg=fg,
                               font=("Microsoft YaHei UI", 8, "bold"), padx=8, pady=2)
        self._label.pack()

    def set(self, text: str, kind: str = "info") -> None:
        bg, fg = self.COLORS.get(kind, self.COLORS["info"])
        self.configure(bg=bg)
        self._label.configure(text=text, bg=bg, fg=fg)


# ── ResultTreeView ────────────────────────────────────

class ResultTreeView(ttk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self._data: list[dict] = []
        self._all_data: list[dict] = []
        self._columns: list[str] = []
        self._tree: ttk.Treeview | None = None
        self._count_label: ttk.Label | None = None
        self._filter_active = False

        tbar = ttk.Frame(self)
        tbar.pack(fill=tk.X, pady=(0, 6))

        ttk.Button(tbar, text="复制选定", command=self._copy_selected, style="Small.TButton").pack(
            side=tk.LEFT, padx=(0, 3))
        ttk.Button(tbar, text="复制全部", command=self._copy_all, style="Small.TButton").pack(
            side=tk.LEFT, padx=(0, 3))
        ttk.Button(tbar, text="JSON", command=lambda: self._export("json"), style="Small.TButton").pack(
            side=tk.LEFT, padx=(0, 3))
        ttk.Button(tbar, text="CSV", command=lambda: self._export("csv"), style="Small.TButton").pack(
            side=tk.LEFT)

        self._count_label = ttk.Label(tbar, text="", font=("Microsoft YaHei UI", 9),
                                      foreground=Theme.TEXT_MUTED)
        self._count_label.pack(side=tk.RIGHT, padx=(0, 6))
        ttk.Button(tbar, text="清空", command=self.clear, style="Small.TButton").pack(side=tk.RIGHT)

        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(search_frame, text="\U0001f50d", font=("", 9)).pack(side=tk.LEFT, padx=(0, 6))
        self._search = SearchBar(search_frame, placeholder="输入关键词过滤...",
                                 on_change=self._apply_filter)
        self._search.pack(side=tk.LEFT, fill=tk.X, expand=True)

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(container, orient=tk.HORIZONTAL)
        self._tree = ttk.Treeview(container, yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                  selectmode="extended", style="Result.Treeview")
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
        self._all_data = list(self._data)
        self.tree["columns"] = self._columns
        self.tree["show"] = "headings"
        for col in self._columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=130, minwidth=60, stretch=True)
        self._rebuild_rows(self._data)
        self.tree.tag_configure("evenrow", background=Theme.TABLE_STRIPE)
        self.tree.tag_configure("oddrow", background=Theme.TABLE_STRIPE_ALT)
        self._update_count()

    def clear(self) -> None:
        self._data = []
        self._all_data = []
        self._columns = []
        self._filter_active = False
        if self._tree is not None:
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = []
            self.tree["show"] = "tree"
        if hasattr(self, '_search'):
            self._search._clear()
        self._update_count()

    def _update_count(self) -> None:
        if self._count_label:
            total = len(self._all_data)
            shown = len(self._data)
            if self._filter_active and total != shown:
                self._count_label.config(text=f"{shown}/{total} 条记录")
            else:
                self._count_label.config(text=f"{total} 条记录")

    def _rebuild_rows(self, data: list[dict]) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(data):
            values = [str(row.get(c, "")) for c in self._columns]
            iid = str(i)
            tags = ("evenrow",) if i % 2 == 0 else ("oddrow",)
            self.tree.insert("", tk.END, iid=iid, values=values, tags=tags)

    def _apply_filter(self, query: str) -> None:
        if not query:
            self._data = list(self._all_data)
            self._filter_active = False
        else:
            q = query.lower()
            self._data = [row for row in self._all_data
                          if any(q in str(v).lower() for v in row.values())]
            self._filter_active = True
        self._rebuild_rows(self._data)
        self._update_count()

    def _sort_by(self, col: str) -> None:
        if col not in self._columns:
            return
        self._data.sort(key=lambda r: str(r.get(col, "")))
        self._rebuild_rows(self._data)

    def _get_selected_rows(self) -> list[dict]:
        sel = self.tree.selection()
        return [self._data[int(iid)] for iid in sel if iid.isdigit()]

    def _copy_selected(self) -> None:
        rows = self._get_selected_rows()
        if not rows:
            messagebox.showinfo("复制", "未选定任何行。")
            return
        self._copy_text(json.dumps(rows, indent=2, ensure_ascii=False, default=str))

    def _copy_all(self) -> None:
        if not self._data:
            messagebox.showinfo("复制", "无数据可复制。")
            return
        self._copy_text(json.dumps(self._data, indent=2, ensure_ascii=False, default=str))

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
            title=f"导出为 {fmt.upper()}")
        if not path:
            return
        try:
            if fmt == "json":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False, default=str)
            else:
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.DictWriter(f, fieldnames=self._columns)
                    w.writeheader()
                    w.writerows(self._data)
            messagebox.showinfo("导出", f"已保存至 {path}")
        except Exception as e:
            messagebox.showerror("导出错误", str(e))


# ── File / Directory Picker ──────────────────────────

class FilePicker(ttk.Frame):
    def __init__(self, parent: tk.Widget, label: str = "路径:",
                 browse_mode: str = "file", filetypes: list[tuple[str, str]] | None = None,
                 default: str = "", tooltip: str = "", **kwargs):
        super().__init__(parent, **kwargs)
        self._browse_mode = browse_mode
        self._filetypes = filetypes or [("所有文件", "*")]
        self._var = tk.StringVar(value=default)
        self.columnconfigure(1, weight=1)
        lbl = ttk.Label(self, text=label, font=("Microsoft YaHei UI", 10))
        lbl.grid(row=0, column=0, padx=(0, 8), sticky="w")
        if tooltip:
            ToolTip(lbl, tooltip)
        entry = ttk.Entry(self, textvariable=self._var, font=("Microsoft YaHei UI", 10))
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        if tooltip:
            ToolTip(entry, tooltip)
        btn = ttk.Button(self, text="浏览...", command=self._browse, padding=(10, 2))
        btn.grid(row=0, column=2, sticky="e")

    def get(self) -> str:
        return self._var.get().strip()

    def set(self, val: str) -> None:
        self._var.set(val)

    def bind_change(self, cb: Callable) -> None:
        self._var.trace_add("write", lambda *_: cb())

    def _browse(self) -> None:
        if self._browse_mode == "dir":
            p = filedialog.askdirectory(title="选择目录")
        elif self._browse_mode == "save":
            p = filedialog.asksaveasfilename(title="保存为", filetypes=self._filetypes)
        else:
            p = filedialog.askopenfilename(title="选择文件", filetypes=self._filetypes)
        if p:
            self._var.set(p)


class DirPicker(FilePicker):
    def __init__(self, parent: tk.Widget, label: str = "目录:", default: str = "",
                 tooltip: str = "", **kwargs):
        super().__init__(parent, label=label, browse_mode="dir",
                         default=default, tooltip=tooltip, **kwargs)


# ── Section / Collapsible ─────────────────────────────

class SectionFrame(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget, title: str = "", **kwargs):
        super().__init__(parent, text=title, padding=12, **kwargs)


class CollapsibleSection(ttk.Frame):
    def __init__(self, parent: tk.Widget, title: str = "", collapsed: bool = False, **kwargs):
        super().__init__(parent, **kwargs)
        self._collapsed = collapsed
        self._header = tk.Frame(self, bg=Theme.CONTENT_BG, cursor="hand2")
        self._header.pack(fill=tk.X)
        self._toggle_var = tk.StringVar(value="\u25bc" if not collapsed else "\u25b6")
        self._toggle_btn = tk.Label(self._header, textvariable=self._toggle_var,
                                    bg=Theme.CONTENT_BG, fg=Theme.TEXT_MUTED,
                                    font=("", 10), padx=4, pady=2)
        self._toggle_btn.pack(side=tk.LEFT)
        self._title_label = tk.Label(self._header, text=title,
                                     bg=Theme.CONTENT_BG, fg=Theme.TEXT_PRIMARY,
                                     font=("Microsoft YaHei UI", 11, "bold"))
        self._title_label.pack(side=tk.LEFT)
        self._sep = tk.Frame(self._header, bg=Theme.BORDER, height=1)
        self._sep.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(10, 0))
        self._body = tk.Frame(self, bg=Theme.CONTENT_BG)
        if not collapsed:
            self._body.pack(fill=tk.BOTH, expand=True, padx=(18, 0), pady=(6, 0))
        for w in (self._header, self._toggle_btn, self._title_label, self._sep):
            w.bind("<Button-1>", self._toggle)

    def _toggle(self, event=None) -> None:
        self._collapsed = not self._collapsed
        if self._collapsed:
            self._body.pack_forget()
            self._toggle_var.set("\u25b6")
        else:
            self._body.pack(fill=tk.BOTH, expand=True, padx=(18, 0), pady=(6, 0))
            self._toggle_var.set("\u25bc")

    @property
    def body(self) -> tk.Frame:
        return self._body


# ── AsyncRunner ──────────────────────────────────────

class AsyncRunner:
    def __init__(self, parent: tk.Widget, status_var: tk.StringVar | None = None):
        self._parent = parent
        self._status = status_var or tk.StringVar()
        self._progress_frame: ttk.Frame | None = None
        self._progress_bar: ttk.Progressbar | None = None
        self._progress_label: ttk.Label | None = None

    def run(self, target: Callable, on_done: Callable[[Any], None],
            args: tuple = (), kwargs: dict | None = None,
            progress_text: str = "执行中...") -> None:
        self._status.set(progress_text)
        self._create_progress(progress_text)

        def _work() -> None:
            try:
                result = target(*args, **(kwargs or {}))
            except Exception as e:
                result = {"error": str(e)}
            self._parent.after(0, lambda: self._finish(result, on_done))

        t = threading.Thread(target=_work, daemon=True)
        t.start()

    def _create_progress(self, text: str = "执行中...") -> None:
        if self._progress_frame is None:
            self._progress_frame = f = ttk.Frame(self._parent)
            f.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))
            self._progress_label = ttk.Label(f, text=text, font=("Microsoft YaHei UI", 9))
            self._progress_label.pack(side=tk.LEFT, padx=(0, 10))
            self._progress_bar = ttk.Progressbar(f, mode="indeterminate", length=250)
            self._progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        else:
            self._progress_label.configure(text=text)
        self._progress_bar.start(10)

    def _finish(self, result: Any, on_done: Callable) -> None:
        if self._progress_bar:
            self._progress_bar.stop()
        if self._progress_frame:
            self._progress_frame.destroy()
            self._progress_frame = None
            self._progress_bar = None
            self._progress_label = None
        is_error = isinstance(result, dict) and "error" in result
        self._status.set("错误" if is_error else "完成")
        on_done(result)


def RunButton(parent: tk.Widget, text: str = "执行", command: Callable | None = None,
              tooltip: str = "", **kwargs):
    return AnimatedButton(parent, text=f"\u25b6  {text}", command=command, tooltip=tooltip, **kwargs)


# ── ShortcutManager ──────────────────────────────────

class ShortcutManager:
    def __init__(self, root: tk.Tk):
        self._root = root
        self._bindings: dict[str, Callable] = {}

    def bind(self, key: str, callback: Callable, description: str = "") -> None:
        self._root.bind(key, lambda e: callback())
        self._bindings[key] = callback

    def unbind(self, key: str) -> None:
        self._root.unbind(key)
        self._bindings.pop(key, None)