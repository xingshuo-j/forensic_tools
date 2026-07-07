"""
Module GUI panels for Forensic Toolkit.

Each panel is a ttk.Frame subclass that implements:
  - build_ui(parent) -> None  (called during init)
  - on_activate() -> None     (called when panel is shown)
"""

from __future__ import annotations
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Any, Callable

from forensic_toolkit.gui.widgets import (
    ResultTreeView, FilePicker, DirPicker,
    SectionFrame, AsyncRunner, RunButton, _fmt,
)
from forensic_toolkit.core.platform import Platform
from forensic_toolkit.core.module_base import ModuleRegistry


# ── Helpers ───────────────────────────────────────────

def _import_module(mod_path: str) -> None:
    import importlib
    try:
        importlib.import_module(mod_path)
    except Exception:
        pass


_MODULES_LOADED = False


def _ensure_modules():
    global _MODULES_LOADED
    if _MODULES_LOADED:
        return
    _MODULES_LOADED = True
    for m in [
        "forensic_toolkit.modules.filesystem",
        "forensic_toolkit.modules.timeline",
        "forensic_toolkit.modules.strings",
        "forensic_toolkit.modules.hunt",
        "forensic_toolkit.modules.carving",
        "forensic_toolkit.modules.metadata",
        "forensic_toolkit.modules.network",
        "forensic_toolkit.modules.recovery",
        "forensic_toolkit.modules.registry",
        "forensic_toolkit.modules.memory",
    ]:
        _import_module(m)


# ── Panel Base ────────────────────────────────────────

class BasePanel(ttk.Frame):
    """Base class for all tool panels."""

    TITLE = "Panel"

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self._runner: AsyncRunner | None = None
        self._status_var = tk.StringVar(value="Ready")
        self.build_ui()

    def build_ui(self) -> None:
        """Override to create panel UI widgets."""
        raise NotImplementedError

    def set_status_var(self, sv: tk.StringVar) -> None:
        self._status_var = sv

    def on_activate(self) -> None:
        """Called when this panel becomes visible."""
        pass

    def run_async(self, target: Callable, on_done: Callable[[Any], None],
                  args: tuple = (), kwargs: dict | None = None) -> None:
        if self._runner is None:
            self._runner = AsyncRunner(self, self._status_var)
        self._runner.run(target, on_done, args=args, kwargs=kwargs)


# ── Dashboard Panel ───────────────────────────────────

class DashboardPanel(BasePanel):
    TITLE = "Dashboard"

    def build_ui(self) -> None:
        header = ttk.Label(self, text="Forensic Toolkit v0.2.0",
                           font=("", 16, "bold"))
        header.pack(pady=(10, 4))

        ttk.Label(self, text="Cross-platform digital forensic toolkit",
                  font=("", 11)).pack(pady=(0, 10))

        info_frame = SectionFrame(self, title="Quick Info")
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self._info_text = tk.Text(info_frame, height=8, wrap=tk.WORD,
                                  font=("", 10), state=tk.DISABLED)
        self._info_text.pack(fill=tk.X, padx=4, pady=4)

        action_frame = SectionFrame(self, title="Quick Actions")
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(action_frame, text="List Block Devices",
                   command=self._cmd_disk_list).pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(action_frame, text="Show Registered Modules",
                   command=self._cmd_list_mods).pack(side=tk.LEFT, padx=4, pady=4)

    def on_activate(self) -> None:
        self._refresh_info()

    def _refresh_info(self) -> None:
        _ensure_modules()
        lines = []
        lines.append(f"Platform: {Platform.info.system} {Platform.info.release}")
        lines.append(f"Admin: {'Yes' if Platform.info.is_admin else 'No'}")
        lines.append(f"Registered modules: {len(ModuleRegistry.list())}")
        for m in sorted(ModuleRegistry.list(), key=lambda x: x.name):
            lines.append(f"  - {m.name}: {m.description}")
        self._info_text.config(state=tk.NORMAL)
        self._info_text.delete("1.0", tk.END)
        self._info_text.insert("1.0", "\n".join(lines))
        self._info_text.config(state=tk.DISABLED)

    def _cmd_disk_list(self) -> None:
        self._status_var.set("Enumerating block devices...")

        def work():
            devs = Platform.list_block_devices()
            rows = []
            for d in devs:
                rows.append({
                    "Path": d.path, "Model": d.model,
                    "Size": _fmt(d.size_bytes),
                    "Readonly": "yes" if d.readonly else "no",
                })
            return rows

        def done(result):
            msg = "\n".join([f"{r['Path']}: {r['Model']} ({r['Size']})" for r in result])
            messagebox.showinfo("Block Devices", msg or "(none found)")

        self.run_async(work, done)

    def _cmd_list_mods(self) -> None:
        mods = ModuleRegistry.list()
        msg = "\n".join([f"{m.name}: {m.description}" for m in sorted(mods, key=lambda x: x.name)])
        messagebox.showinfo("Registered Modules", msg or "(none)")


# ── Disk Panel ────────────────────────────────────────

class DiskPanel(BasePanel):
    TITLE = "Disk"

    def build_ui(self) -> None:
        SectionFrame(self, title="Block Devices").pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self, text="List Block Devices", command=self._list_devices).pack(padx=10, pady=2)
        ttk.Button(self, text="Device Info", command=self._device_info).pack(padx=10, pady=2)

        self._device_picker = FilePicker(self, label="Device Path:", default="")
        self._device_picker.pack(fill=tk.X, padx=10, pady=4)

        SectionFrame(self, title="Results").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _list_devices(self) -> None:
        def work():
            devs = Platform.list_block_devices()
            return [{"Path": d.path, "Model": d.model, "Serial": d.serial,
                     "Size": _fmt(d.size_bytes), "Block Size": d.block_size,
                     "Readonly": "yes" if d.readonly else "no"} for d in devs]

        def done(result):
            self._result.load(result)

        self.run_async(work, done)

    def _device_info(self) -> None:
        path = self._device_picker.get()
        if not path:
            messagebox.showwarning("Input", "Please enter a device path.")
            return

        def work():
            for d in Platform.list_block_devices():
                if d.path == path:
                    return {"Path": d.path, "Model": d.model, "Serial": d.serial,
                            "Size": _fmt(d.size_bytes), "Block Size": d.block_size}
            return {"error": f"Device not found: {path}"}

        def done(result):
            self._result.load(result)

        self.run_async(work, done)


# ── Filesystem Panel ──────────────────────────────────

class FilesystemPanel(BasePanel):
    TITLE = "Filesystem"

    def build_ui(self) -> None:
        SectionFrame(self, title="Filesystem Info").pack(fill=tk.X, padx=10, pady=5)
        self._fs_picker = FilePicker(self, label="Path:")
        self._fs_picker.pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(self, text="Get Filesystem Info", command=self._fs_info).pack(padx=10, pady=2)

        SectionFrame(self, title="Timeline").pack(fill=tk.X, padx=10, pady=5)
        self._tl_picker = FilePicker(self, label="Path:")
        self._tl_picker.pack(fill=tk.X, padx=10, pady=2)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(f, text="Depth:").pack(side=tk.LEFT)
        self._tl_depth = ttk.Spinbox(f, from_=1, to=10, width=5)
        self._tl_depth.set(3)
        self._tl_depth.pack(side=tk.LEFT, padx=4)
        self._tl_bodyfile = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Bodyfile", variable=self._tl_bodyfile).pack(side=tk.LEFT, padx=4)
        ttk.Button(f, text="Generate Timeline", command=self._timeline).pack(side=tk.LEFT, padx=8)

        SectionFrame(self, title="Results").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _fs_info(self) -> None:
        path = self._fs_picker.get()
        if not path:
            messagebox.showwarning("Input", "Please enter a path.")
            return

        def work():
            _import_module("forensic_toolkit.modules.filesystem")
            from forensic_toolkit.modules.filesystem import FilesystemModule
            return FilesystemModule(path=path).run()

        def done(result):
            self._result.load(result)

        self.run_async(work, done)

    def _timeline(self) -> None:
        path = self._tl_picker.get()
        if not path:
            messagebox.showwarning("Input", "Please enter a path.")
            return

        def work():
            _import_module("forensic_toolkit.modules.timeline")
            from forensic_toolkit.modules.timeline import TimelineModule
            return TimelineModule(path=path, depth=int(self._tl_depth.get()),
                                  bodyfile=self._tl_bodyfile.get()).run()

        def done(result):
            if isinstance(result, str):
                from forensic_toolkit.gui.widgets import ResultTreeView
                txt = tk.Toplevel(self)
                txt.title("Bodyfile Output")
                text = tk.Text(txt, wrap=tk.NONE)
                text.pack(fill=tk.BOTH, expand=True)
                text.insert("1.0", result)
                text.config(state=tk.DISABLED)
                sb = ttk.Scrollbar(txt, orient=tk.VERTICAL, command=text.yview)
                sb.pack(side=tk.RIGHT, fill=tk.Y)
                text.config(yscrollcommand=sb.set)
            else:
                self._result.load(result)

        self.run_async(work, done)


# ── Carving Panel ─────────────────────────────────────

class CarvingPanel(BasePanel):
    TITLE = "Carving"

    def build_ui(self) -> None:
        SectionFrame(self, title="File Carving").pack(fill=tk.X, padx=10, pady=5)
        self._src_picker = FilePicker(self, label="Source File/Device:")
        self._src_picker.pack(fill=tk.X, padx=10, pady=2)
        self._out_picker = DirPicker(self, label="Output Dir:", default="./carved")
        self._out_picker.pack(fill=tk.X, padx=10, pady=2)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(f, text="Types (comma, or 'all'):").pack(side=tk.LEFT)
        self._types_var = tk.StringVar(value="all")
        ttk.Entry(f, textvariable=self._types_var, width=20).pack(side=tk.LEFT, padx=4)
        self._extract_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Extract", variable=self._extract_var).pack(side=tk.LEFT, padx=4)
        RunButton(f, text="Scan", command=self._run).pack(side=tk.LEFT, padx=8)

        SectionFrame(self, title="Results").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _run(self) -> None:
        src = self._src_picker.get()
        if not src:
            messagebox.showwarning("Input", "Please select a source.")
            return

        def work():
            _import_module("forensic_toolkit.modules.carving")
            from forensic_toolkit.modules.carving import CarvingModule
            return CarvingModule(
                path=src,
                output_dir=self._out_picker.get(),
                types=self._types_var.get(),
                dry_run=not self._extract_var.get(),
            ).run()

        def done(result):
            if isinstance(result, dict) and "results" in result:
                self._result.load(result["results"])
            else:
                self._result.load(result)

        self.run_async(work, done)


# ── Strings Panel ─────────────────────────────────────

class StringsPanel(BasePanel):
    TITLE = "Strings"

    def build_ui(self) -> None:
        SectionFrame(self, title="String Extraction").pack(fill=tk.X, padx=10, pady=5)
        self._picker = FilePicker(self, label="File:")
        self._picker.pack(fill=tk.X, padx=10, pady=2)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(f, text="Min Length:").pack(side=tk.LEFT)
        self._min_len = ttk.Spinbox(f, from_=2, to=100, width=5)
        self._min_len.set(4)
        self._min_len.pack(side=tk.LEFT, padx=4)
        ttk.Label(f, text="Max Results:").pack(side=tk.LEFT, padx=(10, 0))
        self._max_res = ttk.Spinbox(f, from_=10, to=50000, width=6)
        self._max_res.set(500)
        self._max_res.pack(side=tk.LEFT, padx=4)
        RunButton(f, text="Extract", command=self._run).pack(side=tk.LEFT, padx=10)

        SectionFrame(self, title="Results").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("Input", "Please select a file.")
            return

        def work():
            _import_module("forensic_toolkit.modules.strings")
            from forensic_toolkit.modules.strings import StringsModule
            return StringsModule(path=path, min_length=int(self._min_len.get()),
                                 max_results=int(self._max_res.get())).run()

        def done(result):
            if isinstance(result, dict) and "results" in result:
                self._result.load(result["results"])
            else:
                self._result.load(result)

        self.run_async(work, done)


# ── Hash Panel ────────────────────────────────────────

class HashPanel(BasePanel):
    TITLE = "Hash"

    def build_ui(self) -> None:
        SectionFrame(self, title="Hash Computation").pack(fill=tk.X, padx=10, pady=5)
        self._picker = FilePicker(self, label="File:")
        self._picker.pack(fill=tk.X, padx=10, pady=2)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(f, text="Algorithm:").pack(side=tk.LEFT)
        self._algo = ttk.Combobox(f, values=["sha256", "md5", "sha1", "all"],
                                  state="readonly", width=10)
        self._algo.set("sha256")
        self._algo.pack(side=tk.LEFT, padx=4)
        RunButton(f, text="Compute", command=self._run).pack(side=tk.LEFT, padx=10)

        SectionFrame(self, title="Result").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("Input", "Please select a file.")
            return

        def work():
            _import_module("forensic_toolkit.modules.hunt")
            from forensic_toolkit.modules.hunt import HashModule
            return HashModule(path=path, algorithm=self._algo.get()).run()

        def done(result):
            self._result.load(result)

        self.run_async(work, done)


# ── Hunt Panel ────────────────────────────────────────

class HuntPanel(BasePanel):
    TITLE = "Hunt"

    def build_ui(self) -> None:
        SectionFrame(self, title="Sensitive Info Search").pack(fill=tk.X, padx=10, pady=5)
        self._picker = FilePicker(self, label="File:")
        self._picker.pack(fill=tk.X, padx=10, pady=2)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(f, text="Pattern:").pack(side=tk.LEFT)
        self._pattern = ttk.Combobox(
            f, values=["all", "api_key", "email", "credit_card", "ip_address",
                       "bitcoin", "ethereum", "private_key"],
            state="readonly", width=14,
        )
        self._pattern.set("all")
        self._pattern.pack(side=tk.LEFT, padx=4)
        RunButton(f, text="Search", command=self._run).pack(side=tk.LEFT, padx=10)

        SectionFrame(self, title="Results").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("Input", "Please select a file.")
            return

        def work():
            _import_module("forensic_toolkit.modules.hunt")
            from forensic_toolkit.modules.hunt import HuntModule
            return HuntModule(path=path, patterns=self._pattern.get()).run()

        def done(result):
            if isinstance(result, dict) and "results" in result:
                self._result.load(result["results"])
            else:
                self._result.load(result)

        self.run_async(work, done)


# ── Metadata Panel ────────────────────────────────────

class MetadataPanel(BasePanel):
    TITLE = "Metadata"

    def build_ui(self) -> None:
        SectionFrame(self, title="Metadata Extraction").pack(fill=tk.X, padx=10, pady=5)
        self._picker = FilePicker(self, label="File (JPEG/Office/PDF):")
        self._picker.pack(fill=tk.X, padx=10, pady=2)
        RunButton(self, text="Extract Metadata", command=self._run).pack(padx=10, pady=4)

        SectionFrame(self, title="Result").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("Input", "Please select a file.")
            return

        def work():
            _import_module("forensic_toolkit.modules.metadata")
            from forensic_toolkit.modules.metadata import MetadataModule
            return MetadataModule(path=path).run()

        def done(result):
            if isinstance(result, dict) and "metadata" in result:
                md = result["metadata"]
                if isinstance(md, dict):
                    self._result.load(md)
                else:
                    self._result.load(result)
            else:
                self._result.load(result)

        self.run_async(work, done)


# ── Network Panel ─────────────────────────────────────

class NetworkPanel(BasePanel):
    TITLE = "Network"

    def build_ui(self) -> None:
        SectionFrame(self, title="PCAP Analysis").pack(fill=tk.X, padx=10, pady=5)
        self._picker = FilePicker(self, label="PCAP File:", default="",
                                  filetypes=[("PCAP", "*.pcap *.cap *.dump"), ("All", "*")])
        self._picker.pack(fill=tk.X, padx=10, pady=2)
        RunButton(self, text="Analyze", command=self._run).pack(padx=10, pady=4)

        SectionFrame(self, title="Results").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        self._conn_table = ResultTreeView(self._notebook)
        self._notebook.add(self._conn_table, text="Connections")
        self._dns_table = ResultTreeView(self._notebook)
        self._notebook.add(self._dns_table, text="DNS Queries")
        self._stats_table = ResultTreeView(self._notebook)
        self._notebook.add(self._stats_table, text="Stats")

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("Input", "Please select a PCAP file.")
            return

        def work():
            _import_module("forensic_toolkit.modules.network")
            from forensic_toolkit.modules.network import NetworkModule
            return NetworkModule(path=path).run()

        def done(result):
            if isinstance(result, dict) and "error" not in result:
                self._conn_table.load(result.get("connections", []))
                self._dns_table.load(result.get("dns_queries", []))
                self._stats_table.load([result.get("stats", {})])
            else:
                self._conn_table.load(result)

        self.run_async(work, done)


# ── Memory Panel ──────────────────────────────────────

class MemoryPanel(BasePanel):
    TITLE = "Memory"

    def build_ui(self) -> None:
        SectionFrame(self, title="Memory Analysis").pack(fill=tk.X, padx=10, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(btn_frame, text="List Processes (Linux)",
                   command=lambda: self._run_mode("processes")).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="List Connections (Linux)",
                   command=lambda: self._run_mode("connections")).pack(side=tk.LEFT, padx=4)

        SectionFrame(self, title="Memory Dump Analysis").pack(fill=tk.X, padx=10, pady=5)
        self._picker = FilePicker(self, label="Dump File:")
        self._picker.pack(fill=tk.X, padx=10, pady=2)
        ttk.Button(self, text="Analyze Dump", command=lambda: self._run_mode("dump")).pack(padx=10, pady=2)

        SectionFrame(self, title="Results").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _run_mode(self, mode: str) -> None:
        def work():
            _import_module("forensic_toolkit.modules.memory")
            from forensic_toolkit.modules.memory import MemoryModule
            kw = {"mode": mode}
            if mode == "dump":
                kw["target"] = self._picker.get()
                if not kw["target"]:
                    return {"error": "Please select a dump file."}
            return MemoryModule(**kw).run()

        def done(result):
            if isinstance(result, dict) and "results" in result:
                self._result.load(result["results"])
            elif isinstance(result, dict) and "hints" in result:
                flat = []
                for h in result.get("hints", []):
                    flat.append({"type": h.get("type", ""),
                                 "hits": ", ".join(h.get("hits", []))[:200]})
                self._result.load(flat if flat else result)
            else:
                self._result.load(result)

        self.run_async(work, done)


# ── Registry Panel ────────────────────────────────────

class RegistryPanel(BasePanel):
    TITLE = "Registry"

    def build_ui(self) -> None:
        SectionFrame(self, title="Windows Registry Hive Parser").pack(fill=tk.X, padx=10, pady=5)
        self._picker = FilePicker(self, label="Hive File:", default="",
                                  filetypes=[("Hive", "*"), ("All", "*")])
        self._picker.pack(fill=tk.X, padx=10, pady=2)
        RunButton(self, text="Parse Hive", command=self._run).pack(padx=10, pady=4)

        SectionFrame(self, title="Result").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("Input", "Please select a hive file.")
            return

        def work():
            _import_module("forensic_toolkit.modules.registry")
            from forensic_toolkit.modules.registry import RegistryModule
            return RegistryModule(path=path).run()

        def done(result):
            if isinstance(result, dict) and "keys" in result:
                self._result.load(result["keys"])
            else:
                self._result.load(result)

        self.run_async(work, done)


# ── Recovery Panel ────────────────────────────────────

class RecoveryPanel(BasePanel):
    TITLE = "Recovery"

    def build_ui(self) -> None:
        SectionFrame(self, title="Deleted File Recovery").pack(fill=tk.X, padx=10, pady=5)
        self._picker = FilePicker(self, label="Device:")
        self._picker.pack(fill=tk.X, padx=10, pady=2)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(f, text="FS Type:").pack(side=tk.LEFT)
        self._fs_type = ttk.Combobox(f, values=["auto", "ntfs", "ext4", "fat", "apfs"],
                                     state="readonly", width=8)
        self._fs_type.set("auto")
        self._fs_type.pack(side=tk.LEFT, padx=4)
        ttk.Label(f, text="(Requires admin/root)", font=("", 9, "italic")).pack(side=tk.LEFT, padx=10)
        RunButton(f, text="Scan", command=self._run).pack(side=tk.LEFT, padx=10)

        SectionFrame(self, title="Results").pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

    def _run(self) -> None:
        dev = self._picker.get()
        if not dev:
            messagebox.showwarning("Input", "Please enter a device path.")
            return

        if not Platform.info.is_admin:
            ok = messagebox.askyesno("Permission",
                                     "This operation requires admin/root. Continue?")
            if not ok:
                return

        def work():
            _import_module("forensic_toolkit.modules.recovery")
            from forensic_toolkit.modules.recovery import RecoveryModule
            return RecoveryModule(device=dev, fs_type=self._fs_type.get()).run()

        def done(result):
            if isinstance(result, dict) and "deleted_files" in result:
                self._result.load(result["deleted_files"])
            else:
                self._result.load(result)

        self.run_async(work, done)


# ── Panel Registry ────────────────────────────────────

_PANEL_REGISTRY: list[type[BasePanel]] = []


def register_panel(cls: type[BasePanel]) -> type[BasePanel]:
    _PANEL_REGISTRY.append(cls)
    return cls


def get_panels() -> list[type[BasePanel]]:
    return list(_PANEL_REGISTRY)


# Register all panels
register_panel(DashboardPanel)
register_panel(DiskPanel)
register_panel(FilesystemPanel)
register_panel(CarvingPanel)
register_panel(StringsPanel)
register_panel(HashPanel)
register_panel(HuntPanel)
register_panel(MetadataPanel)
register_panel(NetworkPanel)
register_panel(MemoryPanel)
register_panel(RegistryPanel)
register_panel(RecoveryPanel)
