"""
Premium reusable widgets for Forensic Toolkit GUI.

Design language: rounded corners, smooth animations,
press feedback, lift-on-hover, staggered entrance animations.
Optimized for v0.5.0 — Canvas-based rounded containers, multi-state press/hover effects.
"""

from __future__ import annotations
import csv, json, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Any, Callable
from forensic_toolkit.gui.theme import Theme, Animation


def _fmt(n: int | float) -> str:
    for u in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PiB"


# ── ToolTip ───────────────────────────────────────────

class ToolTip:
    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self._widget = widget; self._text = text; self._delay = delay
        self._tip_window: tk.Toplevel | None = None; self._after_id: str | None = None
        widget.bind("<Enter>", self._schedule); widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, e=None) -> None:
        self._after_id = self._widget.after(self._delay, self._show)

    def _show(self) -> None:
        if self._tip_window: return
        x = self._widget.winfo_rootx() + 12
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
        self._tip_window = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True); tw.wm_geometry(f"+{x}+{y}"); tw.attributes("-alpha", 0.0)
        tk.Label(tw, text=self._text, justify=tk.LEFT, bg=Theme.TOOLTIP_BG,
                 fg=Theme.TOOLTIP_FG, font=("Microsoft YaHei UI", 9), padx=10, pady=5,
                 relief=tk.FLAT, bd=0).pack()
        self._fade_in(tw, 0)

    def _fade_in(self, tw: tk.Toplevel, step: int) -> None:
        if not self._tip_window or self._tip_window != tw: return
        try: tw.attributes("-alpha", min(1.0, step / 10))
        except Exception: return
        if step < 10: tw.after(16, lambda: self._fade_in(tw, step + 1))

    def _hide(self, e=None) -> None:
        if self._after_id: self._widget.after_cancel(self._after_id); self._after_id = None
        if self._tip_window:
            try: self._tip_window.destroy()
            except Exception: pass
            self._tip_window = None


# ── RoundedFrame ─ Canvas-based rounded container ─────

class RoundedFrame(tk.Canvas):
    """Canvas-based frame with true rounded corners, shadow, and hover lift."""

    def __init__(self, parent: tk.Widget, radius: int = 14, shadow: bool = True,
                 padding: int = 0, bg: str | None = None, **kwargs):
        self._radius = radius
        self._shadow = shadow
        self._padding = padding
        self._bg = bg or Theme.CARD_BG
        self._border_color = Theme.CARD_BORDER
        self._hover = False
        self._pressed = False
        self._lift_offset = 0
        self._slide_in = False

        super().__init__(parent, bg=Theme.CONTENT_BG, highlightthickness=0,
                         bd=0, **kwargs)

        # Inner frame for content
        self.content = tk.Frame(self, bg=self._bg)
        self._content_id: int | None = None

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _redraw(self, event=None) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = self._radius
        if w < r * 2 or h < r * 2: return

        off = self._lift_offset

        # Shadow layers
        if self._shadow and not self._pressed:
            for i in range(3, 0, -1):
                shadow_color = Theme.darken(Theme.CONTENT_BG, 0.02 * i)
                self._draw_rounded(off + 2 + i, off + 2 + i, w - 2, h - 2, r, shadow_color, "")

        # Card body
        self._draw_rounded(off, off, w, h, r, self._bg, self._border_color)

        # Top accent line (subtle)
        self._draw_top_accent(off, w, r)

        # Content window
        if self._content_id is None:
            self._content_id = self.create_window(
                r + self._padding, r + self._padding,
                anchor="nw", window=self.content,
                width=w - r * 2 - self._padding * 2,
                height=h - r * 2 - self._padding * 2,
            )
        else:
            self.coords(self._content_id, r + self._padding, r + self._padding)
            self.itemconfig(self._content_id,
                            width=w - r * 2 - self._padding * 2,
                            height=h - r * 2 - self._padding * 2)

    def _draw_rounded(self, x: int, y: int, w: int, h: int, r: int,
                      fill: str, outline: str) -> None:
        """Draw a rounded rectangle on the canvas."""
        self.create_polygon(
            x + r, y, w - r, y, w, y + r,
            w, h - r, w - r, h, x + r, h,
            x, h - r, x, y + r,
            fill=fill, outline=outline, width=1, smooth=True,
        )

    def _draw_top_accent(self, off: int, w: int, r: int) -> None:
        """Draw a subtle top accent line."""
        pass  # No accent line on generic card

    def _on_enter(self, e=None) -> None:
        if self._hover: return
        self._hover = True
        self._lift_offset = 2
        self._redraw()
        self._animate_border(Theme.CARD_BORDER, Theme.CARD_HOVER_BORDER)

    def _on_leave(self, e=None) -> None:
        if not self._hover: return
        self._hover = False
        self._lift_offset = 0
        self._redraw()
        self._animate_border(Theme.CARD_HOVER_BORDER, Theme.CARD_BORDER)

    def _on_press(self, e=None) -> None:
        self._pressed = True
        self._lift_offset = -1
        self._redraw()

    def _on_release(self, e=None) -> None:
        self._pressed = False
        self._lift_offset = 2 if self._hover else 0
        self._redraw()

    def _animate_border(self, frm: str, to: str) -> None:
        self._border_color = to

    def pack_content(self, **kw):
        """Pack the content frame with given kwargs."""
        self.content.pack(**kw)


# ── RoundedCard ─ Simple rounded frame ────────────────

class RoundedCard(tk.Frame):
    """Card with simulated rounded corners via thick padding + outline."""

    def __init__(self, parent: tk.Widget, padding: int = 20, **kwargs):
        super().__init__(parent, bg=Theme.CONTENT_BG, **kwargs)
        self._padding = padding
        self._hover = False; self._pressed = False

        self._inner = tk.Frame(self, bg=Theme.CARD_BG, highlightbackground=Theme.CARD_BORDER,
                               highlightthickness=2, bd=0, relief=tk.FLAT)
        self._inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self._inner.bind("<Enter>", self._on_enter)
        self._inner.bind("<Leave>", self._on_leave)
        self._inner.bind("<Button-1>", self._on_press)
        self._inner.bind("<ButtonRelease-1>", self._on_release)

    @property
    def content(self) -> tk.Frame:
        return self._inner

    def _on_enter(self, e=None) -> None:
        if not self._hover:
            self._hover = True
            Animation.animate_color(self._inner, "highlightbackground",
                                    Theme.CARD_BORDER, Theme.CARD_HOVER_BORDER, 200, "ease_out")

    def _on_leave(self, e=None) -> None:
        if self._hover:
            self._hover = False
            Animation.animate_color(self._inner, "highlightbackground",
                                    Theme.CARD_HOVER_BORDER, Theme.CARD_BORDER, 200, "ease_out")

    def _on_press(self, e=None) -> None:
        self._pressed = True
        self._inner.configure(bg=Theme.darken(Theme.CARD_BG, 0.03))

    def _on_release(self, e=None) -> None:
        self._pressed = False
        self._inner.configure(bg=Theme.CARD_BG)


# ── FeatureCard ───────────────────────────────────────

class FeatureCard(tk.Frame):
    """Feature card with colored accent bar, hover lift, and click ripple."""

    def __init__(self, parent: tk.Widget, icon: str = "\u25a1",
                 title: str = "", description: str = "",
                 action_text: str = "", action_command: Callable | None = None,
                 accent: str = "#0d9488", padding: int = 20, **kwargs):
        super().__init__(parent, bg=Theme.CONTENT_BG, **kwargs)
        self._accent = accent
        self._hover = False; self._pressed = False
        self._command = action_command

        # Card container with thick border
        self._card = tk.Frame(self, bg=Theme.CARD_BG, highlightbackground=Theme.CARD_BORDER,
                              highlightthickness=2, bd=0, relief=tk.FLAT)
        self._card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Colored accent bar at top
        self._bar = tk.Frame(self._card, bg=accent, height=4)
        self._bar.pack(fill=tk.X)

        # Icon
        tk.Label(self._card, text=icon, bg=Theme.CARD_BG, fg=accent,
                 font=("Microsoft YaHei UI", 20)).pack(anchor="w", padx=padding, pady=(padding - 4, 2))

        # Title
        tk.Label(self._card, text=title, bg=Theme.CARD_BG, fg=Theme.TEXT_PRIMARY,
                 font=("Microsoft YaHei UI", 12, "bold"),
                 anchor="w", justify=tk.LEFT).pack(fill=tk.X, padx=padding, pady=(0, 4))

        # Description
        tk.Label(self._card, text=description, bg=Theme.CARD_BG, fg=Theme.TEXT_SECONDARY,
                 font=("Microsoft YaHei UI", 9),
                 anchor="w", justify=tk.LEFT).pack(fill=tk.X, padx=padding, pady=(0, 12))

        # Action link
        if action_text and action_command:
            self._link = tk.Label(self._card, text=action_text + " \u203a", bg=Theme.CARD_BG,
                                  fg=accent, font=("Microsoft YaHei UI", 9), cursor="hand2")
            self._link.pack(anchor="w", padx=padding, pady=(0, padding))
            self._link.bind("<Button-1>", lambda e: action_command())
            self._link.bind("<Enter>", lambda e: self._link.configure(fg=Theme.ACCENT3))
            self._link.bind("<Leave>", lambda e: self._link.configure(fg=accent))

        # Bind hover/press
        self._card.bind("<Enter>", self._on_enter)
        self._card.bind("<Leave>", self._on_leave)
        self._card.bind("<Button-1>", self._on_click)
        self._card.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, e=None) -> None:
        if self._hover: return
        self._hover = True
        Animation.animate_color(self._card, "highlightbackground",
                                Theme.CARD_BORDER, Theme.CARD_HOVER_BORDER, 200, "ease_out")
        # Lift effect
        self._card.configure(bg=Theme.CARD_HOVER_BG)
        for child in self._card.winfo_children():
            try: child.configure(bg=Theme.CARD_HOVER_BG)
            except: pass

    def _on_leave(self, e=None) -> None:
        if not self._hover: return
        self._hover = False
        Animation.animate_color(self._card, "highlightbackground",
                                Theme.CARD_HOVER_BORDER, Theme.CARD_BORDER, 200, "ease_out")
        self._card.configure(bg=Theme.CARD_BG)
        for child in self._card.winfo_children():
            try: child.configure(bg=Theme.CARD_BG)
            except: pass

    def _on_click(self, e=None) -> None:
        self._pressed = True
        # Press effect: accent bar expands
        self._bar.configure(height=6)
        self._card.configure(bg=Theme.darken(Theme.CARD_BG, 0.04))
        if self._command:
            self._command()

    def _on_release(self, e=None) -> None:
        self._pressed = False
        self._bar.configure(height=4)
        self._card.configure(bg=Theme.CARD_HOVER_BG if self._hover else Theme.CARD_BG)


# ── HeroSection ───────────────────────────────────────

class HeroSection(tk.Frame):
    def __init__(self, parent: tk.Widget, title: str = "", subtitle: str = "",
                 cta_text: str = "", cta_command: Callable | None = None, **kwargs):
        super().__init__(parent, bg=Theme.CONTENT_BG, **kwargs)
        tk.Label(self, text=title, bg=Theme.CONTENT_BG, fg=Theme.TEXT_PRIMARY,
                 font=("Microsoft YaHei UI", 32, "bold"),
                 anchor="w", justify=tk.LEFT).pack(anchor="w", pady=(0, 8))
        if subtitle:
            tk.Label(self, text=subtitle, bg=Theme.CONTENT_BG, fg=Theme.TEXT_SECONDARY,
                     font=("Microsoft YaHei UI", 15),
                     anchor="w", justify=tk.LEFT).pack(anchor="w", pady=(0, 20))
        if cta_text and cta_command:
            AnimatedButton(self, text=cta_text, command=cta_command,
                           padding=(24, 10), font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")


# ── AnimatedButton ────────────────────────────────────

class AnimatedButton(tk.Frame):
    """Button with hover glow, press scale-down, and click ripple effect."""

    def __init__(self, parent: tk.Widget, text: str = "", command: Callable | None = None,
                 bg: str | None = None, fg: str | None = None,
                 hover_bg: str | None = None, hover_fg: str | None = None,
                 font: tuple | None = None, padding: tuple[int, int] = (14, 6),
                 tooltip: str = "", **kwargs):
        super().__init__(parent, bg=Theme.CONTENT_BG, **kwargs)
        self._base_bg = bg or Theme.ACCENT
        self._base_fg = fg or Theme.ACCENT_TEXT
        self._hover_bg = hover_bg or Theme.ACCENT_HOVER
        self._hover_fg = hover_fg or Theme.ACCENT_TEXT
        self._command = command
        self._hover = False; self._pressed = False
        self._pad_x, self._pad_y = padding

        self._btn = tk.Label(self, text=text, bg=self._base_bg, fg=self._base_fg,
                             font=font or ("Microsoft YaHei UI", 9, "bold"),
                             padx=self._pad_x, pady=self._pad_y, cursor="hand2",
                             highlightthickness=2, highlightbackground=self._base_bg,
                             bd=0, relief=tk.FLAT)
        self._btn.pack()

        self._btn.bind("<Enter>", self._on_enter)
        self._btn.bind("<Leave>", self._on_leave)
        self._btn.bind("<Button-1>", self._on_press)
        self._btn.bind("<ButtonRelease-1>", self._on_release)
        if tooltip: ToolTip(self._btn, tooltip)

    def _on_enter(self, e=None) -> None:
        if self._hover: return
        self._hover = True
        Animation.animate_color(self._btn, "bg", self._base_bg, self._hover_bg, 120, "ease_out")
        Animation.animate_color(self._btn, "highlightbackground", self._base_bg,
                                Theme.lighten(self._hover_bg, 0.2), 120, "ease_out")

    def _on_leave(self, e=None) -> None:
        if not self._hover: return
        self._hover = False
        Animation.animate_color(self._btn, "bg", self._hover_bg, self._base_bg, 180, "ease_out")
        Animation.animate_color(self._btn, "highlightbackground",
                                Theme.lighten(self._hover_bg, 0.2), self._base_bg, 180, "ease_out")

    def _on_press(self, e=None) -> None:
        self._pressed = True
        self._btn.configure(bg=Theme.darken(self._hover_bg if self._hover else self._base_bg, 0.15),
                            padx=self._pad_x - 2, pady=self._pad_y - 2)

    def _on_release(self, e=None) -> None:
        self._pressed = False
        self._btn.configure(bg=self._hover_bg if self._hover else self._base_bg,
                            padx=self._pad_x, pady=self._pad_y)
        if self._command:
            self._command()


# ── NavButton ─────────────────────────────────────────

class NavButton(tk.Frame):
    """Sidebar nav button with left accent bar, hover glow, press feedback."""

    def __init__(self, parent: tk.Widget, text: str = "", command: Callable | None = None,
                 tooltip: str = "", **kwargs):
        super().__init__(parent, bg=Theme.SIDEBAR_BG, **kwargs)
        self._command = command
        self._active = False
        self._hover = False; self._pressed = False

        # Left accent indicator
        self._indicator = tk.Frame(self, bg=Theme.SIDEBAR_BG, width=3)
        self._indicator.pack(side=tk.LEFT, fill=tk.Y)

        self._btn = tk.Label(self, text=text, bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_TEXT,
                             font=("Microsoft YaHei UI", 10), anchor="w",
                             padx=15, pady=8, cursor="hand2", bd=0)
        self._btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._btn.bind("<Enter>", self._on_enter)
        self._btn.bind("<Leave>", self._on_leave)
        self._btn.bind("<Button-1>", self._on_press)
        self._btn.bind("<ButtonRelease-1>", self._on_release)
        if tooltip: ToolTip(self._btn, tooltip)

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self._indicator.configure(bg=Theme.SIDEBAR_ACTIVE, width=3)
            self._btn.configure(bg=Theme.SIDEBAR_BG_LIGHTER, fg=Theme.SIDEBAR_TEXT_ACTIVE)
            self.configure(bg=Theme.SIDEBAR_BG_LIGHTER)
        else:
            self._indicator.configure(bg=Theme.SIDEBAR_BG, width=3)
            self._btn.configure(bg=Theme.SIDEBAR_BG, fg=Theme.SIDEBAR_TEXT)
            self.configure(bg=Theme.SIDEBAR_BG)

    def _on_enter(self, e=None) -> None:
        if self._hover: return
        self._hover = True
        if not self._active:
            Animation.animate_color(self._btn, "bg", Theme.SIDEBAR_BG, Theme.SIDEBAR_HOVER, 100, "ease_out")
            self.configure(bg=Theme.SIDEBAR_HOVER)

    def _on_leave(self, e=None) -> None:
        if not self._hover: return
        self._hover = False
        if not self._active:
            Animation.animate_color(self._btn, "bg", Theme.SIDEBAR_HOVER, Theme.SIDEBAR_BG, 150, "ease_out")
            self.configure(bg=Theme.SIDEBAR_BG)

    def _on_press(self, e=None) -> None:
        self._pressed = True
        self._btn.configure(padx=13)

    def _on_release(self, e=None) -> None:
        self._pressed = False
        self._btn.configure(padx=15)
        if self._command:
            self._command()


# ── SearchBar ─────────────────────────────────────────

class SearchBar(ttk.Frame):
    def __init__(self, parent: tk.Widget, placeholder: str = "搜索...",
                 on_change: Callable[[str], None] | None = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_change = on_change; self._var = tk.StringVar()
        self.columnconfigure(0, weight=1)
        self._entry = ttk.Entry(self, textvariable=self._var, font=("Microsoft YaHei UI", 9))
        self._entry.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        self._entry.insert(0, placeholder); self._entry.configure(foreground=Theme.TEXT_MUTED)
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<KeyRelease>", self._on_key)
        self._clear_btn = tk.Button(self, text="\u2715", font=("", 8), bg=Theme.CONTENT_BG,
                                    fg=Theme.TEXT_MUTED, relief=tk.FLAT, bd=0, cursor="hand2",
                                    command=self._clear)
        self._clear_btn.grid(row=0, column=1, sticky="e"); self._clear_btn.grid_remove()
        self._placeholder = placeholder; self._has_placeholder = True

    def _on_focus_in(self, e=None) -> None:
        if self._has_placeholder:
            self._entry.delete(0, tk.END); self._entry.configure(foreground=Theme.TEXT_PRIMARY)
            self._has_placeholder = False

    def _on_focus_out(self, e=None) -> None:
        if not self._var.get().strip():
            self._entry.insert(0, self._placeholder); self._entry.configure(foreground=Theme.TEXT_MUTED)
            self._has_placeholder = True

    def _on_key(self, e=None) -> None:
        if self._has_placeholder: return
        t = self._var.get()
        self._clear_btn.grid() if t else self._clear_btn.grid_remove()
        if self._on_change: self._on_change(t)

    def _clear(self) -> None:
        self._var.set(""); self._clear_btn.grid_remove()
        if self._on_change: self._on_change(""); self._entry.focus_set()

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
        self.configure(bg=bg); self._label.configure(text=text, bg=bg, fg=fg)


# ── ResultTreeView ────────────────────────────────────

class ResultTreeView(ttk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self._data: list[dict] = []; self._all_data: list[dict] = []
        self._columns: list[str] = []; self._tree: ttk.Treeview | None = None
        self._count_label: ttk.Label | None = None; self._filter_active = False

        tbar = ttk.Frame(self); tbar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(tbar, text="复制选定", command=self._copy_selected, style="Small.TButton").pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(tbar, text="复制全部", command=self._copy_all, style="Small.TButton").pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(tbar, text="JSON", command=lambda: self._export("json"), style="Small.TButton").pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(tbar, text="CSV", command=lambda: self._export("csv"), style="Small.TButton").pack(side=tk.LEFT)
        self._count_label = ttk.Label(tbar, text="", font=("Microsoft YaHei UI", 9), foreground=Theme.TEXT_MUTED)
        self._count_label.pack(side=tk.RIGHT, padx=(0, 6))
        ttk.Button(tbar, text="清空", command=self.clear, style="Small.TButton").pack(side=tk.RIGHT)

        sf = ttk.Frame(self); sf.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(sf, text="\U0001f50d", font=("", 9)).pack(side=tk.LEFT, padx=(0, 6))
        self._search = SearchBar(sf, placeholder="输入关键词过滤...", on_change=self._apply_filter)
        self._search.pack(side=tk.LEFT, fill=tk.X, expand=True)

        c = ttk.Frame(self); c.pack(fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(c, orient=tk.VERTICAL); hsb = ttk.Scrollbar(c, orient=tk.HORIZONTAL)
        self._tree = ttk.Treeview(c, yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                  selectmode="extended", style="Result.Treeview")
        vsb.config(command=self._tree.yview); hsb.config(command=self._tree.xview)
        self._tree.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        c.grid_rowconfigure(0, weight=1); c.grid_columnconfigure(0, weight=1)

    @property
    def tree(self) -> ttk.Treeview:
        assert self._tree is not None; return self._tree

    def load(self, data: Any) -> None:
        self.clear()
        if not data: return
        if isinstance(data, dict): data = [data]
        if not isinstance(data, list) or not data: return
        if isinstance(data[0], dict):
            self._columns = list(data[0].keys()); self._data = data
        else:
            self._columns = ["Value"]; self._data = [{"Value": str(i)} for i in data]
        self._all_data = list(self._data)
        self.tree["columns"] = self._columns; self.tree["show"] = "headings"
        for col in self._columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=130, minwidth=60, stretch=True)
        self._rebuild_rows(self._data)
        self.tree.tag_configure("evenrow", background=Theme.TABLE_STRIPE)
        self.tree.tag_configure("oddrow", background=Theme.TABLE_STRIPE_ALT)
        self._update_count()

    def clear(self) -> None:
        self._data = []; self._all_data = []; self._columns = []; self._filter_active = False
        if self._tree is not None:
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = []; self.tree["show"] = "tree"
        if hasattr(self, '_search'): self._search._clear()
        self._update_count()

    def _update_count(self) -> None:
        if self._count_label:
            t, s = len(self._all_data), len(self._data)
            self._count_label.config(text=f"{s}/{t} 条记录" if self._filter_active and t != s else f"{t} 条记录")

    def _rebuild_rows(self, data: list[dict]) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(data):
            vals = [str(row.get(c, "")) for c in self._columns]
            tags = ("evenrow",) if i % 2 == 0 else ("oddrow",)
            self.tree.insert("", tk.END, iid=str(i), values=vals, tags=tags)

    def _apply_filter(self, query: str) -> None:
        if not query:
            self._data = list(self._all_data); self._filter_active = False
        else:
            q = query.lower()
            self._data = [r for r in self._all_data if any(q in str(v).lower() for v in r.values())]
            self._filter_active = True
        self._rebuild_rows(self._data); self._update_count()

    def _sort_by(self, col: str) -> None:
        if col not in self._columns: return
        self._data.sort(key=lambda r: str(r.get(col, ""))); self._rebuild_rows(self._data)

    def _get_selected(self) -> list[dict]:
        return [self._data[int(i)] for i in self.tree.selection() if i.isdigit()]

    def _copy_selected(self) -> None:
        rows = self._get_selected()
        if not rows: messagebox.showinfo("复制", "未选定任何行。"); return
        self._copy_text(json.dumps(rows, indent=2, ensure_ascii=False, default=str))

    def _copy_all(self) -> None:
        if not self._data: messagebox.showinfo("复制", "无数据可复制。"); return
        self._copy_text(json.dumps(self._data, indent=2, ensure_ascii=False, default=str))

    @staticmethod
    def _copy_text(text: str) -> None:
        try:
            r = tk.Tk() if not tk._default_root else tk._default_root
            r.clipboard_clear(); r.clipboard_append(text)
        except: pass

    def _export(self, fmt: str) -> None:
        if not self._data: messagebox.showinfo("导出", "无数据可导出。"); return
        ext = ".json" if fmt == "json" else ".csv"
        path = filedialog.asksaveasfilename(defaultextension=ext,
            filetypes=[(fmt.upper(), f"*{ext}")], title=f"导出为 {fmt.upper()}")
        if not path: return
        try:
            if fmt == "json":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False, default=str)
            else:
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.DictWriter(f, fieldnames=self._columns); w.writeheader(); w.writerows(self._data)
            messagebox.showinfo("导出", f"已保存至 {path}")
        except Exception as e: messagebox.showerror("导出错误", str(e))


# ── File / Directory Picker ──────────────────────────

class FilePicker(ttk.Frame):
    def __init__(self, parent: tk.Widget, label: str = "路径:", browse_mode: str = "file",
                 filetypes: list[tuple[str, str]] | None = None,
                 default: str = "", tooltip: str = "", **kwargs):
        super().__init__(parent, **kwargs)
        self._browse_mode = browse_mode; self._filetypes = filetypes or [("所有文件", "*")]
        self._var = tk.StringVar(value=default); self.columnconfigure(1, weight=1)
        lbl = ttk.Label(self, text=label, font=("Microsoft YaHei UI", 10))
        lbl.grid(row=0, column=0, padx=(0, 8), sticky="w")
        if tooltip: ToolTip(lbl, tooltip)
        e = ttk.Entry(self, textvariable=self._var, font=("Microsoft YaHei UI", 10))
        e.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        if tooltip: ToolTip(e, tooltip)
        ttk.Button(self, text="浏览...", command=self._browse, padding=(10, 2)).grid(row=0, column=2, sticky="e")

    def get(self) -> str: return self._var.get().strip()
    def set(self, val: str) -> None: self._var.set(val)
    def bind_change(self, cb: Callable) -> None: self._var.trace_add("write", lambda *_: cb())

    def _browse(self) -> None:
        if self._browse_mode == "dir": p = filedialog.askdirectory(title="选择目录")
        elif self._browse_mode == "save": p = filedialog.asksaveasfilename(title="保存为", filetypes=self._filetypes)
        else: p = filedialog.askopenfilename(title="选择文件", filetypes=self._filetypes)
        if p: self._var.set(p)


class DirPicker(FilePicker):
    def __init__(self, parent: tk.Widget, label: str = "目录:", default: str = "",
                 tooltip: str = "", **kwargs):
        super().__init__(parent, label=label, browse_mode="dir", default=default, tooltip=tooltip, **kwargs)


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
        tk.Label(self._header, textvariable=self._toggle_var, bg=Theme.CONTENT_BG,
                 fg=Theme.TEXT_MUTED, font=("", 10), padx=4, pady=2).pack(side=tk.LEFT)
        tk.Label(self._header, text=title, bg=Theme.CONTENT_BG, fg=Theme.TEXT_PRIMARY,
                 font=("Microsoft YaHei UI", 11, "bold")).pack(side=tk.LEFT)
        tk.Frame(self._header, bg=Theme.BORDER, height=1).pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(10, 0))
        self._body = tk.Frame(self, bg=Theme.CONTENT_BG)
        if not collapsed: self._body.pack(fill=tk.BOTH, expand=True, padx=(18, 0), pady=(6, 0))
        for w in self._header.winfo_children():
            w.bind("<Button-1>", self._toggle)

    def _toggle(self, e=None) -> None:
        self._collapsed = not self._collapsed
        if self._collapsed: self._body.pack_forget(); self._toggle_var.set("\u25b6")
        else: self._body.pack(fill=tk.BOTH, expand=True, padx=(18, 0), pady=(6, 0)); self._toggle_var.set("\u25bc")

    @property
    def body(self) -> tk.Frame: return self._body


# ── AsyncRunner ──────────────────────────────────────

class AsyncRunner:
    def __init__(self, parent: tk.Widget, status_var: tk.StringVar | None = None):
        self._parent = parent; self._status = status_var or tk.StringVar()
        self._progress_frame: ttk.Frame | None = None
        self._progress_bar: ttk.Progressbar | None = None
        self._progress_label: ttk.Label | None = None

    def run(self, target: Callable, on_done: Callable[[Any], None],
            args: tuple = (), kwargs: dict | None = None,
            progress_text: str = "执行中...") -> None:
        self._status.set(progress_text); self._create_progress(progress_text)
        def _work():
            try: result = target(*args, **(kwargs or {}))
            except Exception as e: result = {"error": str(e)}
            self._parent.after(0, lambda: self._finish(result, on_done))
        threading.Thread(target=_work, daemon=True).start()

    def _create_progress(self, text: str = "执行中...") -> None:
        if self._progress_frame is None:
            self._progress_frame = f = ttk.Frame(self._parent)
            f.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))
            self._progress_label = ttk.Label(f, text=text, font=("Microsoft YaHei UI", 9))
            self._progress_label.pack(side=tk.LEFT, padx=(0, 10))
            self._progress_bar = ttk.Progressbar(f, mode="indeterminate", length=250)
            self._progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        else: self._progress_label.configure(text=text)
        self._progress_bar.start(10)

    def _finish(self, result: Any, on_done: Callable) -> None:
        if self._progress_bar: self._progress_bar.stop()
        if self._progress_frame: self._progress_frame.destroy()
        self._progress_frame = None; self._progress_bar = None; self._progress_label = None
        self._status.set("错误" if isinstance(result, dict) and "error" in result else "完成")
        on_done(result)


def RunButton(parent: tk.Widget, text: str = "执行", command: Callable | None = None,
              tooltip: str = "", **kwargs):
    return AnimatedButton(parent, text=f"\u25b6  {text}", command=command, tooltip=tooltip, **kwargs)


# ── ShortcutManager ──────────────────────────────────

class ShortcutManager:
    def __init__(self, root: tk.Tk): self._root = root; self._bindings: dict[str, Callable] = {}
    def bind(self, key: str, callback: Callable, description: str = "") -> None:
        self._root.bind(key, lambda e: callback()); self._bindings[key] = callback
    def unbind(self, key: str) -> None: self._root.unbind(key); self._bindings.pop(key, None)


# ── Staggered Entrance ────────────────────────────────

class StaggeredEntrance:
    """Staggered fade-in entrance animation for multiple widgets."""

    @staticmethod
    def animate(widgets: list[tk.Widget], delay_ms: int = 60,
                duration_ms: int = 200) -> None:
        """Fade in each widget with staggered delay."""
        base_bg = Theme.CONTENT_BG
        for i, w in enumerate(widgets):
            if not w.winfo_exists(): continue
            w.configure(bg=Theme.lighten(base_bg, 0.08))
            offset = i * delay_ms
            w.after(offset, lambda wg=w: Animation.animate_fade(
                wg, Theme.lighten(base_bg, 0.08), base_bg, duration_ms, "ease_out"))