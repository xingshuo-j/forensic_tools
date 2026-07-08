"""
Module GUI panels for Forensic Toolkit.

Each panel wraps a forensic module with input form and result display.
All labels in Simplified Chinese.

Panels:
  - Dashboard, Disk, DiskPartition, Filesystem, Carving, Strings, Hash,
  - Hunt, Metadata, Network, Memory, Registry, Recovery,
  - EvidencePackage, LogViewer, Settings
"""

from __future__ import annotations
import sys
import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Callable

from forensic_toolkit.gui.widgets import (
    ResultTreeView, FilePicker, DirPicker,
    SectionFrame, CollapsibleSection, AsyncRunner, RunButton,
    ToolTip, StatusBadge, _fmt, HeroSection, FeatureCard, RoundedCard, AnimatedButton,
    StaggeredEntrance,
)
from forensic_toolkit.core.platform import Platform
from forensic_toolkit.core.module_base import ModuleRegistry
from forensic_toolkit.gui.theme import Theme, ThemeMode, PANEL_NAMES, PANEL_GROUPS


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


# ── Base Panel ────────────────────────────────────────

class BasePanel(tk.Frame):
    TITLE = "Panel"
    GROUP = "工具"

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=Theme.CONTENT_BG, **kwargs)
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
                  args: tuple = (), kwargs: dict | None = None,
                  progress_text: str = "执行中...") -> None:
        if self._runner is None:
            self._runner = AsyncRunner(self, self._status_var)
        self._runner.run(target, on_done, args=args, kwargs=kwargs,
                         progress_text=progress_text)


# ── Dashboard Panel (Multi-Color Cards) ───────────────

class DashboardPanel(BasePanel):
    TITLE = "Dashboard"
    GROUP = "概览"

    def build_ui(self) -> None:
        # Hero Section
        HeroSection(self,
            title="Forensic Toolkit",
            subtitle="跨平台数字取证工具集。纯 Python 标准库，零外部依赖。",
            cta_text="打开设备列表",
            cta_command=self._cmd_disk_list,
        ).pack(fill=tk.X, pady=(0, 24))

        # Card grid — 3 columns, 3 rows, using grid() layout
        card_data = [
            # (icon, title, desc, accent_color, command)
            ("\u2b23", "磁盘取证", "磁盘设备枚举与分区解析",     Theme.ACCENT,  lambda: self._navigate("Disk")),
            ("\u2b21", "文件系统", "分析文件系统与时间线",     Theme.ACCENT2, lambda: self._navigate("Filesystem")),
            ("\u2299", "哈希校验", "SHA256/MD5/SHA1 哈希",    Theme.ACCENT3, lambda: self._navigate("Hash")),
            ("\u2702", "文件雕刻", "从镜像恢复已删除文件",     Theme.ACCENT4, lambda: self._navigate("Carving")),
            ("\u2298", "敏感搜索", "API密钥/邮箱/信用卡检测",  Theme.ACCENT5, lambda: self._navigate("Hunt")),
            ("\u2b22", "网络取证", "分析 PCAP 网络数据包",    Theme.ACCENT,  lambda: self._navigate("Network")),
            ("\u2b25", "内存分析", "进程枚举与转储分析",       Theme.ACCENT2, lambda: self._navigate("Memory")),
            ("\u2b20", "注册表解析", "解析 Windows 注册表",    Theme.ACCENT3, lambda: self._navigate("Registry")),
            ("\u2b6e", "数据恢复", "扫描并恢复已删除文件",     Theme.ACCENT4, lambda: self._navigate("Recovery")),
        ]

        grid = tk.Frame(self, bg=Theme.CONTENT_BG)
        grid.pack(fill=tk.BOTH, expand=True)

        for col in range(3):
            grid.columnconfigure(col, weight=1, uniform="card_col")
        for row in range(3):
            grid.rowconfigure(row, weight=1, uniform="card_row")

        # Color-accent bars for each card
        cards = []
        for i, (icon, title, desc, accent, cmd) in enumerate(card_data):
            row, col = divmod(i, 3)
            card = FeatureCard(grid, icon=icon, title=title,
                               description=desc, action_text="打开",
                               action_command=cmd, padding=18,
                               accent=accent)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            cards.append(card)

        # Staggered entrance animation
        if cards:
            self.after(100, lambda: StaggeredEntrance.animate(cards, delay_ms=50, duration_ms=250))

    def _navigate(self, title: str) -> None:
        root = self.winfo_toplevel()
        if hasattr(root, '_main_window'):
            root._main_window._show_panel_by_title(title)

    def on_activate(self) -> None:
        pass

    def _cmd_disk_list(self) -> None:
        self._status_var.set("正在枚举块设备...")
        def work():
            devs = Platform.list_block_devices()
            return [{"路径": d.path, "型号": d.model, "大小": _fmt(d.size_bytes),
                     "只读": "是" if d.readonly else "否"} for d in devs]
        def done(result):
            msg = "\n".join([f"{r['路径']}: {r['型号']} ({r['大小']})" for r in result])
            messagebox.showinfo("块设备列表", msg or "(未发现设备)")
        self.run_async(work, done, progress_text="正在枚举块设备...")


# ── Disk Panel ────────────────────────────────────────

class DiskPanel(BasePanel):
    TITLE = "Disk"
    GROUP = "系统分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="磁盘设备").pack(fill=tk.X, padx=14, pady=6)

        # 设备选择行：下拉列表 + 枚举按钮 + 手动输入
        picker_frame = ttk.Frame(self)
        picker_frame.pack(fill=tk.X, padx=14, pady=5)
        picker_frame.columnconfigure(0, weight=1)

        ttk.Label(picker_frame, text="设备路径:", font=("Microsoft YaHei UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self._device_var = tk.StringVar()
        self._device_combo = ttk.Combobox(picker_frame, textvariable=self._device_var,
                                           font=("Consolas", 10))
        self._device_combo.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=4)
        picker_frame.columnconfigure(1, weight=1)
        ToolTip(self._device_combo, "从枚举的设备中选择，或手动输入路径（支持磁盘映像文件）")

        ttk.Button(picker_frame, text="枚举设备", command=self._enumerate_devices,
                   padding=(10, 2)).grid(row=0, column=2, padx=2, pady=4)

        # 操作按钮行
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=14, pady=3)
        ttk.Button(btn_frame, text="查看设备详情", command=self._device_info,
                   padding=(12, 4)).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="选择磁盘映像文件...", command=self._browse_image,
                   padding=(12, 4)).pack(side=tk.LEFT)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _enumerate_devices(self) -> None:
        """枚举块设备并填充下拉列表"""
        def work():
            devs = Platform.list_block_devices()
            return [{"路径": d.path, "型号": d.model, "序列号": d.serial,
                     "大小": _fmt(d.size_bytes), "块大小": d.block_size,
                     "只读": "是" if d.readonly else "否"} for d in devs]
        def done(result):
            self._result.load(result)
            # 用设备路径填充下拉列表
            paths = [r["路径"] for r in result]
            self._device_combo["values"] = paths
            if paths:
                self._device_combo.set(paths[0])
                self._status_var.set(f"已枚举 {len(paths)} 个设备")
        self.run_async(work, done, progress_text="正在枚举磁盘设备...")

    def _browse_image(self) -> None:
        """选择磁盘映像文件（ISO/IMG等）"""
        path = filedialog.askopenfilename(
            title="选择磁盘映像文件",
            filetypes=[("磁盘映像", "*.img *.iso *.vhd *.vhdx *.vmdk *.dd *.raw *.e01 *.aff"),
                       ("所有文件", "*")])
        if path:
            self._device_var.set(path)

    def _device_info(self) -> None:
        path = self._device_var.get().strip()
        if not path:
            messagebox.showwarning("输入", "请选择或输入设备路径。\n\n"
                                    "提示: 点击'枚举设备'自动发现磁盘，"
                                    "或点击'选择磁盘映像文件'选择映像文件。")
            return
        def work():
            # 首先尝试匹配块设备
            for d in Platform.list_block_devices():
                if d.path == path:
                    return {"路径": d.path, "型号": d.model, "序列号": d.serial,
                            "大小": _fmt(d.size_bytes), "块大小": d.block_size}
            # 若不是块设备，尝试作为磁盘映像文件（ISO/IMG等）解析
            from pathlib import Path as _Path
            p = _Path(path)
            if p.is_file():
                from forensic_toolkit.modules.disk import DiskModule
                result = DiskModule(path=path).run()
                if isinstance(result, dict):
                    result["source"] = "disk_image"
                    result["file_size_human"] = _fmt(p.stat().st_size)
                return result
            return {"error": f"未找到设备或磁盘映像: {path}"}
        def done(result):
            self._result.load(result)
        self.run_async(work, done, progress_text=f"正在查询设备 {path}...")


# ── Disk Partition Panel ──────────────────────────────

class DiskPartitionPanel(BasePanel):
    TITLE = "DiskPartition"
    GROUP = "系统分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="分区表解析").pack(fill=tk.X, padx=14, pady=6)

        picker_frame = ttk.Frame(self)
        picker_frame.pack(fill=tk.X, padx=14, pady=3)
        picker_frame.columnconfigure(0, weight=1)

        ttk.Label(picker_frame, text="设备路径:", font=("Microsoft YaHei UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._device_var = tk.StringVar()
        self._device_combo = ttk.Combobox(picker_frame, textvariable=self._device_var,
                                           font=("Consolas", 10))
        self._device_combo.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        picker_frame.columnconfigure(1, weight=1)
        ToolTip(self._device_combo, "从枚举的设备中选择，或手动输入路径")

        ttk.Button(picker_frame, text="枚举", command=self._enumerate_devices,
                   padding=(8, 2)).grid(row=0, column=2, padx=2)
        ttk.Button(picker_frame, text="映像文件...", command=self._browse_image,
                   padding=(8, 2)).grid(row=0, column=3, padx=(2, 0))

        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=14, pady=3)
        ttk.Label(f, text="分区表类型:").pack(side=tk.LEFT)
        self._pt_type = ttk.Combobox(f, values=["auto", "mbr", "gpt"],
                                     state="readonly", width=8)
        self._pt_type.set("auto")
        self._pt_type.pack(side=tk.LEFT, padx=6)
        RunButton(f, text="解析分区表", command=self._run).pack(side=tk.LEFT, padx=12)

        SectionFrame(self, title="分区信息").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _enumerate_devices(self) -> None:
        devs = Platform.list_block_devices()
        paths = [d.path for d in devs]
        self._device_combo["values"] = paths
        if paths:
            self._device_combo.set(paths[0])
            self._status_var.set(f"已枚举 {len(paths)} 个设备")
        else:
            self._status_var.set("未发现块设备")

    def _browse_image(self) -> None:
        path = filedialog.askopenfilename(
            title="选择磁盘映像文件",
            filetypes=[("磁盘映像", "*.img *.iso *.vhd *.vhdx *.vmdk *.dd *.raw *.e01 *.aff"),
                       ("所有文件", "*")])
        if path:
            self._device_var.set(path)

    def _run(self) -> None:
        dev = self._device_var.get().strip()
        if not dev:
            messagebox.showwarning("输入", "请选择或输入设备路径。\n\n"
                                    "提示: 点击'枚举'自动发现磁盘设备，"
                                    "或点击'映像文件'选择磁盘映像。")
            return
        def work():
            # 首先尝试匹配块设备
            devs = Platform.list_block_devices()
            for d in devs:
                if d.path == dev or dev in d.path:
                    return [{
                        "路径": d.path, "型号": d.model,
                        "大小": _fmt(d.size_bytes),
                        "块大小": d.block_size,
                        "类型": self._pt_type.get(),
                    }]
            # 若不是块设备，尝试作为磁盘映像文件（ISO/IMG等）解析
            from pathlib import Path as _Path
            p = _Path(dev)
            if p.is_file():
                from forensic_toolkit.modules.disk import DiskModule
                result = DiskModule(path=dev).run()
                if isinstance(result, dict) and "partitions" in result:
                    out = [{"路径": dev, "分区表类型": result.get("partition_table", "未知"),
                            "来源": "disk_image"}]
                    for pt in result["partitions"]:
                        out.append({
                            "分区号": pt.get("number", ""),
                            "类型": pt.get("type", ""),
                            "可引导": "是" if pt.get("bootable") else "否",
                            "起始LBA": pt.get("start_lba", ""),
                            "扇区数": pt.get("size_sectors", ""),
                        })
                    return out
                if isinstance(result, dict):
                    result["来源"] = "disk_image"
                    return result
            return [{"路径": dev, "状态": "未找到分区信息",
                     "提示": "请确认设备路径正确且具有读取权限（ISO/IMG 镜像请使用磁盘分析面板）"}]
            return partitions
        def done(result):
            self._result.load(result)
        self.run_async(work, done, progress_text="正在解析分区表...")


# ── Filesystem Panel ──────────────────────────────────

class FilesystemPanel(BasePanel):
    TITLE = "Filesystem"
    GROUP = "文件分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="文件系统信息").pack(fill=tk.X, padx=14, pady=6)
        self._fs_picker = FilePicker(self, label="路径:",
                                     tooltip="输入文件或目录路径以获取文件系统元数据")
        self._fs_picker.pack(fill=tk.X, padx=14, pady=3)
        ttk.Button(self, text="获取文件系统信息", command=self._fs_info,
                   padding=(12, 4)).pack(padx=14, pady=3)

        SectionFrame(self, title="时间线").pack(fill=tk.X, padx=14, pady=6)
        self._tl_picker = FilePicker(self, label="路径:",
                                     tooltip="输入目录路径以生成文件时间线")
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
        self.run_async(work, done, progress_text="正在获取文件系统信息...")

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
                txt.configure(bg=Theme.PAPER_BG)
                text = tk.Text(txt, wrap=tk.NONE, font=("Consolas", 9),
                               bg=Theme.PAPER_BG, fg=Theme.TEXT_PRIMARY,
                               insertbackground=Theme.TEXT_PRIMARY)
                text.pack(fill=tk.BOTH, expand=True)
                text.insert("1.0", result)
                text.config(state=tk.DISABLED)
                sb = ttk.Scrollbar(txt, orient=tk.VERTICAL, command=text.yview)
                sb.pack(side=tk.RIGHT, fill=tk.Y)
                text.config(yscrollcommand=sb.set)
            else:
                self._result.load(result)
        self.run_async(work, done, progress_text="正在生成时间线...")


# ── Carving Panel ─────────────────────────────────────

class CarvingPanel(BasePanel):
    TITLE = "Carving"
    GROUP = "文件分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="文件雕刻").pack(fill=tk.X, padx=14, pady=6)
        self._src_picker = FilePicker(self, label="源文件/设备:",
                                      tooltip="选择要扫描的源文件或磁盘设备")
        self._src_picker.pack(fill=tk.X, padx=14, pady=3)
        self._out_picker = DirPicker(self, label="输出目录:", default="./carved",
                                     tooltip="雕刻出的文件保存目录")
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
        self.run_async(work, done, progress_text="正在扫描文件签名...")


# ── Strings Panel ─────────────────────────────────────

class StringsPanel(BasePanel):
    TITLE = "Strings"
    GROUP = "文件分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="字符串提取").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="文件:",
                                  tooltip="选择要提取字符串的二进制文件")
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
        self.run_async(work, done, progress_text="正在提取字符串...")


# ── Hash Panel ────────────────────────────────────────

class HashPanel(BasePanel):
    TITLE = "Hash"
    GROUP = "文件分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="哈希计算").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="文件:",
                                  tooltip="选择要计算哈希值的文件")
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
        self.run_async(work, done, progress_text="正在计算哈希值...")


# ── Hunt Panel ────────────────────────────────────────

class HuntPanel(BasePanel):
    TITLE = "Hunt"
    GROUP = "文件分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="敏感信息搜索").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="文件:",
                                  tooltip="选择要搜索敏感信息的文件")
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
        self.run_async(work, done, progress_text="正在搜索敏感信息...")


# ── Metadata Panel ────────────────────────────────────

class MetadataPanel(BasePanel):
    TITLE = "Metadata"
    GROUP = "文件分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="元数据提取").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="文件 (JPEG/Office/PDF):",
                                  tooltip="选择 JPEG、Office 文档或 PDF 文件以提取元数据",
                                  filetypes=[("支持的文件", "*.jpg *.jpeg *.png *.docx *.xlsx *.pptx *.pdf"),
                                             ("所有文件", "*")])
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
        self.run_async(work, done, progress_text="正在提取元数据...")


# ── Network Panel ─────────────────────────────────────

class NetworkPanel(BasePanel):
    TITLE = "Network"
    GROUP = "网络分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="网络取证分析").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="PCAP 文件:", default="",
                                  tooltip="选择 PCAP 网络抓包文件进行分析",
                                  filetypes=[("PCAP", "*.pcap *.cap *.dump *.pcapng"), ("所有文件", "*")])
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
        self.run_async(work, done, progress_text="正在分析网络数据包...")


# ── Memory Panel ──────────────────────────────────────

class MemoryPanel(BasePanel):
    TITLE = "Memory"
    GROUP = "系统分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="实时内存分析 (Linux)").pack(fill=tk.X, padx=14, pady=6)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=14, pady=3)
        ttk.Button(btn_frame, text="进程枚举", padding=(12, 4),
                   command=lambda: self._run_mode("processes")).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="网络连接", padding=(12, 4),
                   command=lambda: self._run_mode("connections")).pack(side=tk.LEFT, padx=4)

        SectionFrame(self, title="内存转储分析").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="转储文件:",
                                  tooltip="选择内存转储文件进行分析")
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
        self.run_async(work, done, progress_text=f"正在执行内存分析 ({mode})...")


# ── Registry Panel ────────────────────────────────────

class RegistryPanel(BasePanel):
    TITLE = "Registry"
    GROUP = "系统分析"

    def build_ui(self) -> None:
        SectionFrame(self, title="Windows 注册表解析").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="Hive 文件:", default="",
                                  tooltip="选择 Windows 注册表 Hive 文件 (SAM/SYSTEM/SOFTWARE 等)",
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
        self.run_async(work, done, progress_text="正在解析注册表...")


# ── Recovery Panel ────────────────────────────────────

class RecoveryPanel(BasePanel):
    TITLE = "Recovery"
    GROUP = "数据恢复"

    def build_ui(self) -> None:
        SectionFrame(self, title="已删除文件恢复").pack(fill=tk.X, padx=14, pady=6)
        self._picker = FilePicker(self, label="设备路径:",
                                  tooltip="输入要扫描的磁盘设备路径")
        self._picker.pack(fill=tk.X, padx=14, pady=3)
        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=14, pady=3)
        ttk.Label(f, text="文件系统:").pack(side=tk.LEFT)
        self._fs_type = ttk.Combobox(f, values=["auto", "ntfs", "ext4", "fat", "apfs"],
                                     state="readonly", width=8)
        self._fs_type.set("auto")
        self._fs_type.pack(side=tk.LEFT, padx=6)
        ttk.Label(f, text="(需要 root/管理员权限)", font=("Microsoft YaHei UI", 8)).pack(side=tk.LEFT, padx=12)
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
        self.run_async(work, done, progress_text="正在扫描已删除文件...")


# ── Evidence Package Panel ────────────────────────────

class EvidencePackagePanel(BasePanel):
    TITLE = "EvidencePackage"
    GROUP = "数据恢复"

    def build_ui(self) -> None:
        SectionFrame(self, title="证据打包 (E01 / AFF)").pack(fill=tk.X, padx=14, pady=6)

        info = ttk.Label(self, text="生成符合取证标准的证据映像文件。需要安装 libewf-python (E01) 或 pyaff (AFF)。",
                         font=("Microsoft YaHei UI", 9), wraplength=700)
        info.pack(padx=14, pady=4)

        self._src_picker = FilePicker(self, label="源设备/文件:",
                                      tooltip="选择要打包的源设备或文件")
        self._src_picker.pack(fill=tk.X, padx=14, pady=3)

        self._out_picker = FilePicker(self, label="输出文件:", browse_mode="save",
                                      default="evidence.e01",
                                      tooltip="证据映像输出路径",
                                      filetypes=[("E01", "*.e01"), ("AFF", "*.aff"), ("所有文件", "*")])
        self._out_picker.pack(fill=tk.X, padx=14, pady=3)

        f = ttk.Frame(self)
        f.pack(fill=tk.X, padx=14, pady=3)
        ttk.Label(f, text="格式:").pack(side=tk.LEFT)
        self._fmt_var = ttk.Combobox(f, values=["E01", "AFF", "RAW"],
                                     state="readonly", width=8)
        self._fmt_var.set("E01")
        self._fmt_var.pack(side=tk.LEFT, padx=6)

        ttk.Label(f, text="案件编号:").pack(side=tk.LEFT, padx=(12, 0))
        self._case_var = tk.StringVar(value="CASE-001")
        ttk.Entry(f, textvariable=self._case_var, width=12).pack(side=tk.LEFT, padx=6)

        ttk.Label(f, text="取证人员:").pack(side=tk.LEFT, padx=(12, 0))
        self._examiner_var = tk.StringVar(value="Examiner")
        ttk.Entry(f, textvariable=self._examiner_var, width=12).pack(side=tk.LEFT, padx=6)

        RunButton(f, text="打包", command=self._run).pack(side=tk.LEFT, padx=12)

        SectionFrame(self, title="结果").pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        self._result = ResultTreeView(self)
        self._result.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _run(self) -> None:
        src = self._src_picker.get()
        out = self._out_picker.get()
        if not src or not out:
            messagebox.showwarning("输入", "请选择源文件和输出路径。")
            return

        fmt = self._fmt_var.get()
        if fmt == "E01":
            try:
                import libewf
            except ImportError:
                messagebox.showerror("依赖缺失",
                    "E01 格式需要 libewf-python 库。\n请运行: pip install libewf-python")
                return
        elif fmt == "AFF":
            try:
                import pyaff
            except ImportError:
                messagebox.showerror("依赖缺失",
                    "AFF 格式需要 pyaff 库。\n请运行: pip install pyaff")
                return

        def work():
            return {
                "状态": "提示",
                "消息": f"证据打包功能需要安装对应依赖库。\n"
                        f"格式: {fmt}\n"
                        f"源: {src}\n"
                        f"输出: {out}\n"
                        f"案件: {self._case_var.get()}\n"
                        f"取证人员: {self._examiner_var.get()}\n\n"
                        f"安装依赖:\n"
                        f"  E01: pip install libewf-python\n"
                        f"  AFF: pip install pyaff"
            }

        def done(result):
            self._result.load(result)
        self.run_async(work, done, progress_text="正在打包证据...")


# ── Log Viewer Panel ──────────────────────────────────

class LogViewerPanel(BasePanel):
    TITLE = "LogViewer"
    GROUP = "工具"

    def build_ui(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=14, pady=6)

        ttk.Label(toolbar, text="操作日志", font=("Microsoft YaHei UI", 12, "bold")).pack(side=tk.LEFT)

        self._auto_scroll = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar, text="自动滚动", variable=self._auto_scroll).pack(side=tk.RIGHT, padx=8)
        ttk.Button(toolbar, text="清空日志", command=self._clear_log,
                   style="Small.TButton").pack(side=tk.RIGHT, padx=4)
        ttk.Button(toolbar, text="导出日志", command=self._export_log,
                   style="Small.TButton").pack(side=tk.RIGHT, padx=4)

        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)

        self._log_text = tk.Text(container, wrap=tk.WORD,
                                 font=("Consolas", 9),
                                 bg=Theme.PAPER_BG, fg=Theme.TEXT_PRIMARY,
                                 insertbackground=Theme.TEXT_PRIMARY,
                                 relief=tk.FLAT, padx=8, pady=6,
                                 state=tk.DISABLED)
        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=vsb.set)

        self._log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._log_entries: list[str] = []

    def on_activate(self) -> None:
        if not self._log_entries:
            self._append_log("日志查看器已就绪", "info")
            self._append_log(f"平台: {Platform.info.system} {Platform.info.release}", "info")
            self._append_log(f"Python: {sys.version.split()[0]}", "info")
            self._append_log(f"已注册模块: {len(ModuleRegistry.list())} 个", "info")

    def add_log(self, message: str, level: str = "info") -> None:
        """Add a log entry from external sources."""
        self._append_log(message, level)

    def _append_log(self, message: str, level: str = "info") -> None:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        tag = {"info": "[INFO]", "warn": "[WARN]", "error": "[ERROR]", "success": "[OK]  "}.get(level, "[INFO]")
        entry = f"{now} {tag} {message}"
        self._log_entries.append(entry)

        self._log_text.config(state=tk.NORMAL)
        self._log_text.insert(tk.END, entry + "\n")

        # Color tags
        colors = {"info": Theme.TEXT_PRIMARY, "warn": Theme.WARNING,
                  "error": Theme.DANGER, "success": Theme.SUCCESS}
        line_start = self._log_text.index(tk.END + "-2l")
        line_end = self._log_text.index(tk.END + "-1c")
        self._log_text.tag_add(level, line_start, line_end)
        self._log_text.tag_config(level, foreground=colors.get(level, Theme.TEXT_PRIMARY))

        self._log_text.config(state=tk.DISABLED)

        if self._auto_scroll.get():
            self._log_text.see(tk.END)

    def _clear_log(self) -> None:
        self._log_entries.clear()
        self._log_text.config(state=tk.NORMAL)
        self._log_text.delete("1.0", tk.END)
        self._log_text.config(state=tk.DISABLED)

    def _export_log(self) -> None:
        if not self._log_entries:
            messagebox.showinfo("导出", "无日志可导出。")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt")],
            title="导出日志"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self._log_entries))
            messagebox.showinfo("导出", f"日志已保存至 {path}")
        except Exception as e:
            messagebox.showerror("导出错误", str(e))


# ── Settings Panel ────────────────────────────────────

class SettingsPanel(BasePanel):
    TITLE = "Settings"
    GROUP = "工具"

    def build_ui(self) -> None:
        header = ttk.Label(self, text="系统设置", font=("Microsoft YaHei UI", 14, "bold"))
        header.pack(padx=14, pady=(12, 8), anchor="w")

        # Appearance
        sec1 = SectionFrame(self, title="外观")
        sec1.pack(fill=tk.X, padx=14, pady=6)

        f1 = ttk.Frame(sec1)
        f1.pack(fill=tk.X, pady=4)
        ttk.Label(f1, text="当前主题:").pack(side=tk.LEFT)
        self._theme_label = ttk.Label(f1, text="浅色模式",
                                      font=("Microsoft YaHei UI", 10, "bold"))
        self._theme_label.pack(side=tk.LEFT, padx=8)
        self._theme_btn = ttk.Button(f1, text="切换深色模式", command=self._toggle_theme,
                                     padding=(12, 4))
        self._theme_btn.pack(side=tk.LEFT, padx=12)

        # Output
        sec2 = SectionFrame(self, title="输出设置")
        sec2.pack(fill=tk.X, padx=14, pady=6)

        f2 = ttk.Frame(sec2)
        f2.pack(fill=tk.X, pady=4)
        ttk.Label(f2, text="默认输出目录:").pack(side=tk.LEFT)
        self._output_var = tk.StringVar(value="./ftk_output")
        ttk.Entry(f2, textvariable=self._output_var, width=30).pack(side=tk.LEFT, padx=8)
        ttk.Button(f2, text="浏览...", command=self._browse_output,
                   padding=(8, 2)).pack(side=tk.LEFT)
        ToolTip(f2, "取证输出文件的默认保存位置")

        # Default params
        sec3 = SectionFrame(self, title="默认参数")
        sec3.pack(fill=tk.X, padx=14, pady=6)

        f3 = ttk.Frame(sec3)
        f3.pack(fill=tk.X, pady=4)
        ttk.Label(f3, text="默认哈希算法:").pack(side=tk.LEFT)
        self._hash_algo = ttk.Combobox(f3, values=["sha256", "md5", "sha1"],
                                       state="readonly", width=10)
        self._hash_algo.set("sha256")
        self._hash_algo.pack(side=tk.LEFT, padx=8)

        f4 = ttk.Frame(sec3)
        f4.pack(fill=tk.X, pady=4)
        ttk.Label(f4, text="默认字符串最小长度:").pack(side=tk.LEFT)
        self._str_min = ttk.Spinbox(f4, from_=2, to=20, width=5)
        self._str_min.set(4)
        self._str_min.pack(side=tk.LEFT, padx=8)

        f5 = ttk.Frame(sec3)
        f5.pack(fill=tk.X, pady=4)
        ttk.Label(f5, text="默认时间线深度:").pack(side=tk.LEFT)
        self._tl_depth = ttk.Spinbox(f5, from_=1, to=10, width=5)
        self._tl_depth.set(3)
        self._tl_depth.pack(side=tk.LEFT, padx=8)

        # About
        sec4 = SectionFrame(self, title="关于")
        sec4.pack(fill=tk.X, padx=14, pady=6)

        about_text = (
            f"Forensic Toolkit v0.3.0\n"
            f"跨平台数字取证工具集\n"
            f"纯 Python 标准库，零外部依赖\n\n"
            f"平台: {Platform.info.system} {Platform.info.release}\n"
            f"Python: {sys.version.split()[0]}\n"
            f"管理员权限: {'是' if Platform.info.is_admin else '否'}\n"
            f"已注册模块: {len(ModuleRegistry.list())} 个"
        )
        ttk.Label(sec4, text=about_text, font=("Microsoft YaHei UI", 9),
                  justify=tk.LEFT).pack(pady=4, anchor="w")

        # Save button
        ttk.Button(self, text="保存设置", command=self._save_settings,
                   style="Accent.TButton").pack(padx=14, pady=12)

    def _toggle_theme(self) -> None:
        new_mode = Theme.toggle()
        from forensic_toolkit.gui.theme import refresh_ttk_theme
        refresh_ttk_theme()

        if new_mode == ThemeMode.DARK:
            self._theme_label.config(text="深色模式")
            self._theme_btn.config(text="切换浅色模式")
        else:
            self._theme_label.config(text="浅色模式")
            self._theme_btn.config(text="切换深色模式")

        # Update all widget colors
        self._refresh_colors(self)

    def _refresh_colors(self, widget: tk.Widget) -> None:
        """Recursively refresh colors for all child widgets."""
        c = Theme._c()
        for child in widget.winfo_children():
            if isinstance(child, (tk.Frame, tk.LabelFrame)):
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

    def _browse_output(self) -> None:
        p = filedialog.askdirectory(title="选择默认输出目录")
        if p:
            self._output_var.set(p)

    def _save_settings(self) -> None:
        settings = {
            "output_dir": self._output_var.get(),
            "default_hash": self._hash_algo.get(),
            "default_str_min": self._str_min.get(),
            "default_tl_depth": self._tl_depth.get(),
        }
        # Save to a simple config file
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "ftk_config.json")
        try:
            import json
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("设置", "设置已保存。")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def get_output_dir(self) -> str:
        return self._output_var.get()


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
register_panel(DiskPartitionPanel)
register_panel(MemoryPanel)
register_panel(RegistryPanel)
register_panel(FilesystemPanel)
register_panel(StringsPanel)
register_panel(HashPanel)
register_panel(HuntPanel)
register_panel(MetadataPanel)
register_panel(CarvingPanel)
register_panel(NetworkPanel)
register_panel(RecoveryPanel)
register_panel(EvidencePackagePanel)
register_panel(LogViewerPanel)
register_panel(SettingsPanel)