"""
ftk — Forensic Toolkit CLI (零外部依赖, argparse)
用法: ftk <command> [options] [args]
"""

from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleRegistry
from forensic_toolkit.core.platform import Platform
from forensic_toolkit.core.formatters import get_formatter

VERSION = "0.2.0"


# ── 导入所有已注册模块 ───────────────────────────────

def _import_all_modules():
    """导入所有模块，触发 ModuleRegistry.register()。"""
    import importlib
    mod_names = [
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
    ]
    for name in mod_names:
        try:
            importlib.import_module(name)
        except Exception:
            pass


# ── 辅助 ──────────────────────────────────────────────

def _fmt(n: int) -> str:
    for u in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PiB"


def _emit(args: argparse.Namespace, data: Any) -> None:
    get_formatter(args.output_format).emit(data)


# ── 命令处理函数 ─────────────────────────────────────

def run_list_modules(args):
    rows = []
    for m in sorted(ModuleRegistry.list(), key=lambda x: x.name):
        rows.append({"name": m.name, "description": m.description,
                     "platforms": ", ".join(m.supported_platforms) or "all",
                     "admin": "yes" if m.requires_admin else "no"})
    if not rows:
        print("(暂无已注册模块 — 请先运行特定命令按需加载)")
        return
    _emit(args, rows)


def run_disk_list(args):
    devs = Platform.list_block_devices()
    rows = [{"path": d.path, "model": d.model, "size": _fmt(d.size_bytes),
             "readonly": "yes" if d.readonly else "no"} for d in devs]
    _emit(args, rows)


def run_disk_info(args):
    for d in Platform.list_block_devices():
        if d.path == args.path:
            _emit(args, {"path": d.path, "model": d.model, "serial": d.serial,
                         "size": d.size_bytes, "size_human": _fmt(d.size_bytes),
                         "block_size": d.block_size, "source": "block_device"})
            return
    p = Path(args.path)
    if p.is_file():
        from forensic_toolkit.modules.disk import DiskModule
        result = DiskModule(path=str(p)).run()
        if isinstance(result, dict):
            result["source"] = "disk_image"
            result["file_size"] = p.stat().st_size
            result["file_size_human"] = _fmt(p.stat().st_size)
        _emit(args, result)
        return
    print(f"设备未找到: {args.path}", file=sys.stderr)
    sys.exit(1)


def run_disk_analyze(args):
    from forensic_toolkit.modules.disk import DiskModule
    _emit(args, DiskModule(path=args.path).run())


def run_fs_info(args):
    from forensic_toolkit.modules.filesystem import FilesystemModule
    _emit(args, FilesystemModule(path=args.path).run())


def run_fs_timeline(args):
    from forensic_toolkit.modules.timeline import TimelineModule
    r = TimelineModule(path=args.path, depth=args.depth, bodyfile=args.bodyfile).run()
    if args.bodyfile: print(r)
    else: _emit(args, r)


def run_carving(args):
    from forensic_toolkit.modules.carving import CarvingModule
    _emit(args, CarvingModule(path=args.path, output_dir=args.output,
                              types=args.types, dry_run=not args.extract).run())


def run_metadata(args):
    from forensic_toolkit.modules.metadata import MetadataModule
    _emit(args, MetadataModule(path=args.path).run())


def run_network(args):
    from forensic_toolkit.modules.network import NetworkModule
    _emit(args, NetworkModule(path=args.pcap).run())


def run_recovery(args):
    from forensic_toolkit.modules.recovery import RecoveryModule
    _emit(args, RecoveryModule(device=args.device, fs_type=args.fs_type).run())


def run_registry(args):
    from forensic_toolkit.modules.registry import RegistryModule
    _emit(args, RegistryModule(path=args.hive).run())


def run_strings(args):
    from forensic_toolkit.modules.strings import StringsModule
    path = args.path if args.path and args.path != "-" else None
    _emit(args, StringsModule(path=path, min_length=args.min_len,
                              max_results=args.max_results, pipe_input=path is None).run())


def run_hash(args):
    from forensic_toolkit.modules.hunt import HashModule
    _emit(args, HashModule(path=args.path, algorithm=args.algo).run())


def run_hunt(args):
    from forensic_toolkit.modules.hunt import HuntModule
    _emit(args, HuntModule(path=args.path, patterns=args.patterns).run())


def run_memory(args):
    from forensic_toolkit.modules.memory import MemoryModule
    kw = {"mode": args.mem_cmd}
    if args.mem_cmd == "dump": kw["target"] = args.path
    _emit(args, MemoryModule(**kw).run())


# ── 解析器工厂 ───────────────────────────────────────

def _sp(parent, name, handler, **kw):
    p = parent.add_parser(name, **kw)
    p.set_defaults(_handler=handler)
    return p


def build_parser():
    p = argparse.ArgumentParser(
        prog="ftk",
        description=f"Forensic Toolkit v{VERSION} \u2014 跨平台数字取证工具集",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--output-format", choices=("table", "json", "csv"), default="table",
                   help="输出格式: table (默认) | json | csv")
    p.add_argument("-o", "--output-dir", default="./ftk_output",
                   help="输出目录 (默认 ./ftk_output)")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="详细信息")
    p.add_argument("--version", action="version", version=f"ftk v{VERSION}",
                   help="显示版本号")

    sub = p.add_subparsers(dest="command", metavar="<command>", required=False)

    _sp(sub, "list-modules", run_list_modules, help="列出所有已注册模块")

    # disk
    dk = _sp(sub, "disk", None, help="  磁盘取证")
    dks = dk.add_subparsers(dest="disk_cmd", metavar="")
    _sp(dks, "list", run_disk_list, help="  枚举块设备")
    dp = _sp(dks, "info", run_disk_info, help="  设备详情")
    dp.add_argument("path")
    dp = _sp(dks, "analyze", run_disk_analyze, help="  分析磁盘映像(MBR/GPT)")
    dp.add_argument("path")

    # filesystem
    fs = _sp(sub, "filesystem", None, help="  文件系统分析")
    fss = fs.add_subparsers(dest="fs_cmd", metavar="")
    _sp(fss, "info", run_fs_info, help="  文件系统元数据").add_argument("path")
    ft = _sp(fss, "timeline", run_fs_timeline, help="  MAC 时间线")
    ft.add_argument("path")
    ft.add_argument("--depth", type=int, default=3, help="扫描深度")
    ft.add_argument("--bodyfile", action="store_true", help="输出 TSK bodyfile 格式")

    # carving
    cv = _sp(sub, "carving", None, help="  文件雕刻")
    cvs = cv.add_subparsers(dest="carving_cmd", metavar="")
    cs = _sp(cvs, "scan", run_carving, help="  按签名扫描恢复")
    cs.add_argument("path", help="目标文件/设备")
    cs.add_argument("--types", default="all", help="文件类型: jpeg,pdf,zip,...")
    cs.add_argument("--output", default="./carved", help="输出目录")
    cs.add_argument("--extract", action="store_true", help="实际提取文件 (默认 dry-run)")
    cs.add_argument("--max-size", type=int, default=0, help="每文件最大字节数")

    # metadata
    md = _sp(sub, "metadata", None, help="  元数据提取")
    mds = md.add_subparsers(dest="md_cmd", metavar="")
    _sp(mds, "extract", run_metadata, help="  提取文件元数据").add_argument("path")

    # network
    nw = _sp(sub, "network", None, help="  网络取证")
    nws = nw.add_subparsers(dest="net_cmd", metavar="")
    _sp(nws, "analyze", run_network, help="  PCAP 分析").add_argument("pcap")

    # recovery
    rc = _sp(sub, "recovery", None, help="  已删除文件恢复")
    rcs = rc.add_subparsers(dest="recovery_cmd", metavar="")
    rs = _sp(rcs, "scan", run_recovery, help="  扫描已删除文件")
    rs.add_argument("device")
    rs.add_argument("--fs-type", default="auto",
                    help="文件系统: auto/ntfs/ext4/apfs/fat")

    # registry
    rg = _sp(sub, "registry", None, help="  Windows Registry")
    rgs = rg.add_subparsers(dest="reg_cmd", metavar="")
    _sp(rgs, "dump", run_registry, help="  解析 Hive 文件").add_argument("hive")

    # strings
    st = _sp(sub, "strings", None, help="  字符串提取")
    sts = st.add_subparsers(dest="str_cmd", metavar="")
    ss = _sp(sts, "dump", run_strings, help="  提取可打印字符串")
    ss.add_argument("path", nargs="?", default=None, help="文件路径或 - 表示 stdin")
    ss.add_argument("--min-len", type=int, default=4, help="最短字符串长度")
    ss.add_argument("--max-results", type=int, default=500, help="最多返回条数")

    # hash
    hs = _sp(sub, "hash", None, help="  哈希校验")
    hss = hs.add_subparsers(dest="hash_cmd", metavar="")
    hp = _sp(hss, "compute", run_hash, help="  计算哈希")
    hp.add_argument("path")
    hp.add_argument("--algo", default="sha256", help="算法: md5/sha1/sha256/all")

    # hunt
    ht = _sp(sub, "hunt", None, help="  敏感信息搜索")
    hts = ht.add_subparsers(dest="hunt_cmd", metavar="")
    hp2 = _sp(hts, "secrets", run_hunt, help="  搜索敏感模式")
    hp2.add_argument("path")
    hp2.add_argument("--patterns", default="all",
                     help="模式: all/api/email/cc/crypto")

    # memory
    mem = _sp(sub, "memory", None, help="  内存分析")
    mems = mem.add_subparsers(dest="mem_cmd", metavar="")
    _sp(mems, "processes", run_memory, help="  进程枚举 (Linux)")
    _sp(mems, "connections", run_memory, help="  网络连接 (Linux)")
    md2 = _sp(mems, "dump", run_memory, help="  内存转储分析")
    md2.add_argument("path")

    return p


# ── 入口 ──────────────────────────────────────────────

def cli() -> None:
    _import_all_modules()
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    handler = getattr(args, "_handler", None)
    if handler:
        handler(args)
    else:
        parser.parse_args([args.command, "--help"])


if __name__ == "__main__":
    cli()
