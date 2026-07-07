"""
内存分析模块
=============
对操作系统内存/进程数据进行取证分析。

三块能力:
  1. 实时进程枚举 (Linux /proc): 进程列表、内存映射、打开文件
  2. 内存转储分析: 搜索进程结构、连接信息、CMD 历史
  3. Volatility 3 集成提示 (需外部安装 volatility3)

注: 完整的内存分析建议使用 Volatility 3:
    pip install volatility3
    vol -f mem.dump windows.pslist
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


class MemoryModule(ModuleBase):
    meta = ModuleMeta(
        name="memory",
        description="内存数据分析 (进程枚举 / 转储扫描 / Volatility 集成)",
        author="Forensic Toolkit",
        version="0.1.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._target = self.params.get("target")  # dump 文件路径
        self._mode = self.params.get("mode", "processes")

    def run(self) -> Any:
        if self._mode == "processes":
            return self._list_processes()
        elif self._mode == "dump":
            return self._analyze_dump()
        elif self._mode == "connections":
            return self._list_connections()
        return {"error": f"未知模式: {self._mode}"}

    # ── 实时进程枚举 (Linux /proc) ────────────────────

    def _list_processes(self) -> dict:
        """从 /proc 枚举进程 (Linux)。"""
        procs = []
        proc_path = Path("/proc")
        if not proc_path.exists():
            return {"error": "/proc 不可用（仅支持 Linux）",
                     "hint_windows": "Windows 上可使用 tasklist 或 Win32 API",
                     "hint_macos": "macOS 上可使用 ps aux 或 sysctl"}

        for entry in proc_path.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
                info = self._read_proc_info(entry, pid)
                if info:
                    procs.append(info)
            except Exception:
                continue

        procs.sort(key=lambda x: x.get("pid", 0))
        return {
            "source": "/proc",
            "platform": "Linux",
            "processes_found": len(procs),
            "results": procs[:300],
        }

    @staticmethod
    def _read_proc_info(proc_dir: Path, pid: int) -> dict | None:
        """读取单个进程的信息。"""
        info: dict = {"pid": pid}

        try:
            # cmdline
            cmdline = (proc_dir / "cmdline").read_bytes()
            info["cmdline"] = cmdline.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()
        except Exception:
            info["cmdline"] = ""

        try:
            # status
            for line in (proc_dir / "status").read_text().splitlines():
                if line.startswith("Name:"):
                    info["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("State:"):
                    info["state"] = line.split(":", 1)[1].strip()
                elif line.startswith("Uid:"):
                    info["uid"] = line.split(":", 1)[1].strip().split()[0]
                elif line.startswith("VmRSS:"):
                    info["rss"] = line.split(":", 1)[1].strip()
        except Exception:
            info["name"] = f"pid_{pid}"

        try:
            # 内存映射统计
            maps = (proc_dir / "maps").read_text()
            regions = len(maps.splitlines())
            info["memory_regions"] = regions
            # 提取可执行路径
            exe_paths = set()
            for line in maps.splitlines():
                parts = line.strip().split()
                if len(parts) >= 6 and parts[5] != "":
                    exe_paths.add(parts[5])
            info["mapped_files"] = list(exe_paths)[:20]
        except Exception:
            pass

        try:
            # 打开文件描述符
            fd_count = len(list((proc_dir / "fd").iterdir()))
            info["open_fds"] = fd_count
        except Exception:
            pass

        if info.get("name"):
            return info
        return None

    # ── 内存转储分析 ─────────────────────────────────

    _DUMP_MAX_READ = 500 * 1024 * 1024           # 500 MiB 转储分析上限

    def _analyze_dump(self) -> dict:
        """对内存转储文件进行基本分析。"""
        if not self._target:
            return {"error": "请指定内存转储文件路径"}

        path = Path(self._target)
        if not path.exists():
            return {"error": f"文件不存在: {path}"}

        size = path.stat().st_size
        if size > self._DUMP_MAX_READ:
            return {
                "error": f"文件过大 ({size / (1024*1024):.0f} MiB)，超出内存分析上限 ({self._DUMP_MAX_READ // (1024*1024)} MiB)。\n建议使用 Volatility 3: pip install volatility3",
                "file": str(path.resolve()),
                "size": size,
            }

        found: dict = {"file": str(path.resolve()), "size": size, "hints": []}

        try:
            data = path.read_bytes()
        except MemoryError:
            return {"error": "内存不足，请使用 Volatility 3 分析"}

        # 搜索进程结构特征
        # Linux task_struct 特征: 查找常见内核符号
        procs = set()
        for m in re.finditer(rb"/(?:usr/)?sbin/init\b", data):
            procs.add("init")
        for m in re.finditer(rb"/bin/(?:bash|sh|zsh)\b", data):
            procs.add(m.group().decode("latin-1").rsplit("/", 1)[1])
        for m in re.finditer(rb"(sshd|nginx|apache2|httpd|systemd)\x00", data):
            procs.add(m.group(1).decode("latin-1"))

        if procs:
            found["hints"].append({
                "type": "process_names",
                "hits": sorted(procs)[:30],
            })

        # 搜索网络连接
        conns = set()
        for m in re.finditer(rb"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)", data):
            conns.add(m.group().decode("latin-1"))
        if conns:
            found["hints"].append({
                "type": "network_connections",
                "hits": sorted(conns)[:50],
            })

        # 搜索 bash/zsh 历史
        hist_cmds = set()
        for m in re.finditer(rb"history|wget |curl |ssh |nc |nmap ", data):
            try:
                ctx_start = max(0, m.start() - 20)
                ctx = data[ctx_start:m.end() + 40]
                hist_cmds.add(ctx.decode("latin-1", errors="replace").strip())
            except Exception:
                pass
        if hist_cmds:
            found["hints"].append({
                "type": "command_history",
                "hits": sorted(hist_cmds)[:50],
            })

        # 搜索密码/密钥 (简化版)
        secrets = set()
        for m in re.finditer(rb"(?i)(password|secret|passwd)\s*[:=]\s*(\S+)", data):
            secrets.add(m.group().decode("latin-1", errors="replace")[:80])
        if secrets:
            found["hints"].append({
                "type": "credentials",
                "hits": sorted(secrets)[:30],
            })

        found["recommendation"] = (
            "如需深入分析，建议使用 Volatility 3:\n"
            "  pip install volatility3\n"
            "  vol -f mem.dump windows.pslist\n"
            "  vol -f mem.dump linux.bash"
        )
        return found

    # ── 网络连接信息 (Linux /proc) ────────────────────

    def _list_connections(self) -> dict:
        """从 /proc/net/tcp 列出网络连接。"""
        tcp_path = Path("/proc/net/tcp")
        if not tcp_path.exists():
            return {"error": "/proc/net/tcp 不可用（仅限 Linux）"}

        connections = []
        try:
            lines = tcp_path.read_text().splitlines()
            for line in lines[1:]:  # 跳过表头
                parts = line.strip().split()
                if len(parts) < 12:
                    continue
                fields = {
                    "sl": parts[0].rstrip(":"),
                    "local": self._parse_tcp_addr(parts[1]),
                    "remote": self._parse_tcp_addr(parts[2]),
                    "state": self._tcp_state(parts[3]),
                    "uid": parts[7],
                    "inode": parts[9],
                }
                connections.append(fields)
        except Exception as e:
            return {"error": str(e)}

        return {
            "source": "/proc/net/tcp",
            "platform": "Linux",
            "connections_found": len(connections),
            "results": connections[:200],
        }

    @staticmethod
    def _parse_tcp_addr(hex_str: str) -> str:
        """解析 /proc/net/tcp 格式的地址。"""
        try:
            addr_part, port_part = hex_str.split(":")
            addr_bytes = bytes.fromhex(addr_part)
            addr = ".".join(str(b) for b in addr_bytes[:4])
            port = int(port_part, 16)
            return f"{addr}:{port}"
        except Exception:
            return hex_str

    @staticmethod
    def _tcp_state(hex_state: str) -> str:
        states = {
            "01": "ESTABLISHED", "02": "SYN_SENT", "03": "SYN_RECV",
            "04": "FIN_WAIT1", "05": "FIN_WAIT2", "06": "TIME_WAIT",
            "07": "CLOSE", "08": "CLOSE_WAIT", "09": "LAST_ACK",
            "0A": "LISTEN", "0B": "CLOSING",
        }
        return states.get(hex_state.upper(), f"UNKNOWN({hex_state})")


ModuleRegistry.register(MemoryModule)
