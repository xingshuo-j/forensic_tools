"""
Module GUI panels for Forensic Toolkit.
Each panel wraps a forensic module with input form and result display.
All labels in Simplified Chinese.
"""

from __future__ import annotations
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable

from forensic_toolkit.gui.widgets import (
    ResultTreeView, FilePicker, DirPicker,
    SectionFrame, AsyncRunner, RunButton, _fmt,
)
from forensic_toolkit.core.platform import Platform
from forensic_toolkit.core.module_base import ModuleRegistry


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


class BasePanel(ttk.Frame):
    TITLE = "Panel"

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self._runner: AsyncRunner | None = None
        self._status_var = tk.StringVar(value="就绪")
        self.build_ui()

    def build_ui(self) -> None:
        raise NotImplementedError

    def set_status_var(self, sv: tk.StringVar) -> None:
        self._status_var = sv

    def on_activate(self) -> None:
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
        header = ttk.Label(self, text="Forensic Toolkit", font=("", 18, "bold"))
        header.pack(pady=(12, 2))
        ttk.Label(self, text="跨平台数字取证工具集 | 零外部依赖", font=("", 10)).pack(pady=(0, 12))

        info_frame = SectionFrame(self, title="系统信息")
        info_frame.pack(fill=tk.X, padx=14, pady=6)

        self._info_text = tk.Text(info_frame, height=10, wrap=tk.WORD,
                                  font=("", 10), state=tk.DISABLED,
                                  bg="#ffffff", relief=tk.FLAT, padx=8, pady=6)
        self._info_text.pack(fill=tk.X)

        action_frame = SectionFrame(self, title="快捷操作")
        action_frame.pack(fill=tk.X, padx=14, pady=6)

        ttk.Button(action_frame, text="枚举块设备", command=self._cmd_disk_list,
                   padding=(12, 4)).pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(action_frame, text="查看已注册模块", command=self._cmd_list_mods,
                   padding=(12, 4)).pack(side=tk.LEFT, padx=4, pady=4)

    def on_activate(self) -> None:
        self._refresh_info()

    def _refresh_info(self) -> None:
        _ensure_modules()
        lines = []
        lines.append(f"平台: {Platform.info.system} {Platform.info.release}")
        lines.append(f"管理员权限: {'是' if Platform.info.is_admin else '否'}")
        lines.append(f"Python: {sys.version.split()[0]}")
        lines.append(f"已注册模块: {len(ModuleRegistry.list())} 个")
        lines.append("-" * 40)
        for m in sorted(ModuleRegistry.list(), key=lambda x: x.name):
            lines.append(f"  {m.name}: {m.description}")
        self._info_text.config(state=tk.NORMAL)
        self._info_text.delete("1.0", tk.END)
        self._info_text.insert("1.0", "\n".join(lines))
        self._info_text.config(state=tk.DISABLED)

    def _cmd_disk_list(self) -> None:
        self._status_var.set("正在枚举块设备...")
        def work():
            devs = Platform.list_block_devices()
            return [{"路径": d.path, "型号": d.model, "大小": _fmt(d.size_bytes),
                     "只读": "是" if d.readonly else "否"} for d in devs]
        def done(result):
            msg = "\n".join([f"{r['路径']}: {r['型号']} ({r['大小']})" for r in result])
            messagebox.showinfo("块设备列表", msg or "(未发现设备)")
        self.run_async(work, done)

    def _cmd_list_mods(self) -> None:
        mods = ModuleRegistry.list()
        msg = "\n".join([f"{m.name}: {m.description}" for m in sorted(mods, key=lambda x: x.name)])
        messagebox.showinfo("已注册模块", msg or "(无)")


# ── Disk Panel ────────────────────────────────────────

class DiskPanel(BasePanel):
    TITLE = "Disk"

    def build_ui(self) -> None:
        SectionFrame(self, title="磁盘设备").pack(fill=tk.X, padx=14, pady=6)
        ttk.Button(self, text="枚举所有块设备", command=self._list_devices,
                   padding=(12, 4)).pack(padx=14, pady=3)
        self._device_picker = FilePicker(self, label="设备路径:")
        self._device_picker.pack(fill=tk.X, padx=14, pady=5)
        ttk.Button(self, text="查看设备详情", command=self._device_info,
                   padding=(12, 4)).pack(padx=14, pady=3)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _list_devices(self) -> None:
        def work():
            devs = Platform.list_block_devices()
            return [{"路径": d.path, "型号": d.model, "序列号": d.serial,
                     "大小": _fmt(d.size_bytes), "块大小": d.block_size,
                     "只读": "是" if d.readonly else "否"} for d in devs]
        def done(result):
            self._result.load(result)
        self.run_async(work, done)

    def _device_info(self) -> None:
        path = self._device_picker.get()
        if not path:
            messagebox.showwarning("输入", "请输入设备路径。")
            return
        p = Path(path)
        def work():
            for d in Platform.list_block_devices():
                if d.path == path:
                    return {"路径": d.path, "型号": d.model, "序列号": d.serial,
                            "大小": _fmt(d.size_bytes), "块大小": d.block_size, "来源": "块设备"}
            if p.is_file():
                _import_module("forensic_toolkit.modules.disk")
                from forensic_toolkit.modules.disk import DiskModule
                result = DiskModule(path=str(p)).run()
                if isinstance(result, dict):
                    result["文件大小"] = _fmt(p.stat().st_size)
                    result["来源"] = "磁盘映像"
                return result
            return {"error": f"未找到设备: {path}"}
        def done(result):
            self._result.load(result)
        self.run_async(work, done)


# ── Filesystem Panel ──────────────────────────────────

class FilesystemPanel(BasePanel):
    TITLE = "Filesystem"

    def build_ui(self) -> None:
        SectionFrame(self, title="文件系统信息").pack(fill=tk.X, padx=14, pady=6)
        self._fs_picker = FilePicker(self, label="路径:")
        self._fs_picker.pack(fill=tk.X, padx=14, pady=3)
        ttk.Button(self, text="获取文件系统信息", command=self._fs_info,
                   padding=(12, 4)).pack(padx=14, pady=3)

        SectionFrame(self, title="时间线").pack(fill=tk.X, padx=14, pady=6)
        self._tl_picker = FilePicker(self, label="路径:")
        self._tl_picker.pack(fill=tk.X, padx=14, pady=3)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=14, pady=3)
        ttk.Label(f, text="扫描深度:").pack(side=tk.LEFT)
        self._tl_depth = ttk.Spinbox(f, from_=1, to=10, width=5)
        self._tl_depth.set(3)
        self._tl_depth.pack(side=tk.LEFT, padx=6)
        self._tl_bodyfile = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Bodyfile格式", variable=self._tl_bodyfile).pack(side=tk.LEFT, padx=8)
        ttk.Button(f, text="生成时间线", command=self._timeline,
                   padding=(12, 4)).pack(side=tk.LEFT, padx=10)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _fs_info(self) -> None:
        path = self._fs_picker.get()
        if not path:
            messagebox.showwarning("输入", "请输入路径。")
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
            messagebox.showwarning("输入", "请输入路径。")
            return
        def work():
            _import_module("forensic_toolkit.modules.timeline")
            from forensic_toolkit.modules.timeline import TimelineModule
            return TimelineModule(path=path, depth=int(self._tl_depth.get()),
                                  bodyfile=self._tl_bodyfile.get()).run()
        def done(result):
            if isinstance(result, str):
                txt = tk.Toplevel(self)
                txt.title("Bodyfile 输出")
                txt.geometry("800x500")
                text = tk.Text(txt, wrap=tk.NONE, font=("", 9))
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
        SectionFrame(self, title="文件雕刻").pack(fill=tk.X, padx=14, pady=6)
        self._src_picker = FilePicker(self, label="源文件/设备:")
        self._src_picker.pack(fill=tk.X, padx=14, pady=3)
        self._out_picker = DirPicker(self, label="输出目录:", default="./carved")
        self._out_picker.pack(fill=tk.X, padx=14, pady=3)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=14, pady=3)
        ttk.Label(f, text="文件类型（逗号分隔，或 'all'）:").pack(side=tk.LEFT)
        self._types_var = tk.StringVar(value="all")
        ttk.Entry(f, textvariable=self._types_var, width=22).pack(side=tk.LEFT, padx=6)
        self._extract_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="实际提取文件", variable=self._extract_var).pack(side=tk.LEFT, padx=8)
        RunButton(f, text="扫描", command=self._run).pack(side=tk.LEFT, padx=10)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _run(self) -> None:
        src = self._src_picker.get()
        if not src:
            messagebox.showwarning("输入", "请选择源文件或设备。")
            return
        def work():
            _import_module("forensic_toolkit.modules.carving")
            from forensic_toolkit.modules.carving import CarvingModule
            return CarvingModule(
                path=src, output_dir=self._out_picker.get(),
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
        SectionFrame(self, title="字符串提取").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="文件:")
        self._picker.pack(fill=tk.X, padx=14, pady=3)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=14, pady=3)
        ttk.Label(f, text="最小长度:").pack(side=tk.LEFT)
        self._min_len = ttk.Spinbox(f, from_=2, to=100, width=5)
        self._min_len.set(4)
        self._min_len.pack(side=tk.LEFT, padx=4)
        ttk.Label(f, text="最大结果数:").pack(side=tk.LEFT, padx=(12, 0))
        self._max_res = ttk.Spinbox(f, from_=10, to=50000, width=6)
        self._max_res.set(500)
        self._max_res.pack(side=tk.LEFT, padx=4)
        RunButton(f, text="提取", command=self._run).pack(side=tk.LEFT, padx=12)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("输入", "请选择文件。")
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
        SectionFrame(self, title="哈希计算").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="文件:")
        self._picker.pack(fill=tk.X, padx=14, pady=3)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=14, pady=3)
        ttk.Label(f, text="算法:").pack(side=tk.LEFT)
        self._algo = ttk.Combobox(f, values=["sha256", "md5", "sha1", "all"],
                                  state="readonly", width=10)
        self._algo.set("sha256")
        self._algo.pack(side=tk.LEFT, padx=6)
        RunButton(f, text="计算", command=self._run).pack(side=tk.LEFT, padx=12)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("输入", "请选择文件。")
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
        SectionFrame(self, title="敏感信息搜索").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="文件:")
        self._picker.pack(fill=tk.X, padx=14, pady=3)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=14, pady=3)
        ttk.Label(f, text="搜索模式:").pack(side=tk.LEFT)
        self._pattern = ttk.Combobox(
            f, values=[
                "all", "api_key", "email", "credit_card", "ip_address",
                "bitcoin", "ethereum", "private_key",
            ],
            state="readonly", width=14,
        )
        self._pattern.set("all")
        self._pattern.pack(side=tk.LEFT, padx=6)
        RunButton(f, text="搜索", command=self._run).pack(side=tk.LEFT, padx=12)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("输入", "请选择文件。")
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
        SectionFrame(self, title="元数据提取").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="文件 (JPEG/Office/PDF):")
        self._picker.pack(fill=tk.X, padx=14, pady=3)
        RunButton(self, text="提取元数据", command=self._run).pack(padx=14, pady=5)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("输入", "请选择文件。")
            return
        def work():
            _import_module("forensic_toolkit.modules.metadata")
            from forensic_toolkit.modules.metadata import MetadataModule
            return MetadataModule(path=path).run()
        def done(result):
            if isinstance(result, dict) and "metadata" in result:
                md = result["metadata"]
                self._result.load(md if isinstance(md, dict) else result)
            else:
                self._result.load(result)
        self.run_async(work, done)


# ── Network Panel ─────────────────────────────────────

class NetworkPanel(BasePanel):
    TITLE = "Network"

    def build_ui(self) -> None:
        SectionFrame(self, title="网络取证分析").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="PCAP 文件:", default="",
                                  filetypes=[("PCAP", "*.pcap *.cap *.dump"), ("所有文件", "*")])
        self._picker.pack(fill=tk.X, padx=14, pady=3)
        RunButton(self, text="分析", command=self._run).pack(padx=14, pady=5)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._conn_table = ResultTreeView(self._notebook)
        self._notebook.add(self._conn_table, text="网络连接")
        self._dns_table = ResultTreeView(self._notebook)
        self._notebook.add(self._dns_table, text="DNS 查询")
        self._stats_table = ResultTreeView(self._notebook)
        self._notebook.add(self._stats_table, text="统计信息")

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("输入", "请选择 PCAP 文件。")
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
        SectionFrame(self, title="实时内存分析 (Linux)").pack(fill=tk.X, padx=14, pady=6)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=14, pady=3)
        ttk.Button(btn_frame, text="进程枚举", padding=(12, 4),
                   command=lambda: self._run_mode("processes")).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="网络连接", padding=(12, 4),
                   command=lambda: self._run_mode("connections")).pack(side=tk.LEFT, padx=4)

        SectionFrame(self, title="内存转储分析").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="转储文件:")
        self._picker.pack(fill=tk.X, padx=14, pady=3)
        ttk.Button(self, text="分析转储", command=lambda: self._run_mode("dump"),
                   padding=(12, 4)).pack(padx=14, pady=3)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _run_mode(self, mode: str) -> None:
        def work():
            _import_module("forensic_toolkit.modules.memory")
            from forensic_toolkit.modules.memory import MemoryModule
            kw = {"mode": mode}
            if mode == "dump":
                kw["target"] = self._picker.get()
                if not kw["target"]:
                    return {"error": "请选择转储文件。"}
            return MemoryModule(**kw).run()
        def done(result):
            if isinstance(result, dict) and "results" in result:
                self._result.load(result["results"])
            elif isinstance(result, dict) and "hints" in result:
                flat = []
                for h in result.get("hints", []):
                    flat.append({"类型": h.get("type", ""),
                                 "匹配": ", ".join(h.get("hits", []))[:200]})
                self._result.load(flat if flat else result)
            else:
                self._result.load(result)
        self.run_async(work, done)


# ── Registry Panel ────────────────────────────────────

class RegistryPanel(BasePanel):
    TITLE = "Registry"

    def build_ui(self) -> None:
        SectionFrame(self, title="Windows 注册表解析").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="Hive 文件:", default="",
                                  filetypes=[("Hive", "*"), ("所有文件", "*")])
        self._picker.pack(fill=tk.X, padx=14, pady=3)
        RunButton(self, text="解析 Hive", command=self._run).pack(padx=14, pady=5)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _run(self) -> None:
        path = self._picker.get()
        if not path:
            messagebox.showwarning("输入", "请选择 Hive 文件。")
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
        SectionFrame(self, title="已删除文件恢复").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="设备路径:")
        self._picker.pack(fill=tk.X, padx=14, pady=3)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=14, pady=3)
        ttk.Label(f, text="文件系统:").pack(side=tk.LEFT)
        self._fs_type = ttk.Combobox(f, values=["auto", "ntfs", "ext4", "fat", "apfs"],
                                     state="readonly", width=8)
        self._fs_type.set("auto")
        self._fs_type.pack(side=tk.LEFT, padx=6)
        ttk.Label(f, text="(需要 root/管理员权限)", font=("", 8, "italic")).pack(side=tk.LEFT, padx=12)
        RunButton(f, text="扫描", command=self._run).pack(side=tk.LEFT, padx=12)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _run(self) -> None:
        dev = self._picker.get()
        if not dev:
            messagebox.showwarning("输入", "请输入设备路径。")
            return
        if not Platform.info.is_admin:
            ok = messagebox.askyesno("权限提示", "此操作需要 root/管理员权限，是否继续？")
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
