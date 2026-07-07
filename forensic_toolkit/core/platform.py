"""
Platform Abstraction Layer (PAL)
=================================
将所有 OS 差异隔离在此模块中。上层模块永远不应直接使用 os.name / sys.platform。

职责:
  - 检测当前操作系统 (Linux / macOS / Windows)
  - 枚举块设备（含权限检查）
  - 以只读方式打开块设备
  - 提权检测（root / Administrator）
  - 路径规范（如 Windows 设备路径规范）
"""

from __future__ import annotations
import os
import platform as _platform
import subprocess
from typing import Iterator, Optional
from forensic_toolkit.core.types import BlockDevice, ForensicError


class PlatformInfo:
    """当前运行环境的平台信息。"""

    def __init__(self) -> None:
        self.system: str = _platform.system().lower()  # linux | darwin | windows
        self.release: str = _platform.release()
        self.is_admin: bool = self._check_admin()
        self.is_linux: bool = self.system == "linux"
        self.is_macos: bool = self.system == "darwin"
        self.is_windows: bool = self.system == "windows"

    @staticmethod
    def _check_admin() -> bool:
        if os.name == "nt":
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore
            except Exception:
                return False
        return os.geteuid() == 0  # type: ignore

    def __repr__(self) -> str:
        return f"Platform({self.system} {self.release}, admin={self.is_admin})"


class Platform:
    """平台相关操作的静态命名空间。"""

    info = PlatformInfo()

    # ── 块设备枚举 ────────────────────────────────────────

    @classmethod
    def list_block_devices(cls) -> list[BlockDevice]:
        """枚举系统可访问的块设备。"""
        if cls.info.is_linux:
            return cls._list_linux()
        if cls.info.is_macos:
            return cls._list_macos()
        if cls.info.is_windows:
            return cls._list_windows()
        return []

    @classmethod
    def _list_linux(cls) -> list[BlockDevice]:
        devices: list[BlockDevice] = []
        for entry in os.listdir("/sys/block/"):
            path = f"/dev/{entry}"
            if not os.path.exists(path):
                continue
            removable = cls._sysfs_read(f"/sys/block/{entry}/removable")
            size_str = cls._sysfs_read(f"/sys/block/{entry}/size")
            size = (int(size_str, 10) * 512) if size_str else 0
            model = cls._sysfs_read(f"/sys/block/{entry}/device/model")
            serial = cls._sysfs_read(f"/sys/block/{entry}/serial")
            devices.append(BlockDevice(
                path=path,
                model=model,
                serial=serial,
                size_bytes=size,
                readonly=not cls.info.is_admin,
            ))
        return devices

    @classmethod
    def _list_macos(cls) -> list[BlockDevice]:
        devices: list[BlockDevice] = []
        try:
            out = subprocess.run(
                ["diskutil", "list", "-plist"],
                capture_output=True, text=True, timeout=10,
            )
            # 简化的解析：只返回 /dev/rdisk* 设备
            for line in out.stdout.splitlines():
                if "rdisk" in line:
                    parts = line.strip().strip("<>").strip()
                    if parts.startswith("/dev/rdisk"):
                        import plistlib
                        data = plistlib.loads(out.stdout.encode())
                        for disk in data.get("AllDisks", []):
                            path = f"/dev/r{disk}"
                            devices.append(BlockDevice(path=path, readonly=True))
                        return devices
        except Exception:
            pass
        # fallback: 枚举 /dev/rdisk*
        for f in os.listdir("/dev"):
            if f.startswith("rdisk") and f[-1].isdigit() is False:
                devices.append(BlockDevice(path=f"/dev/{f}", readonly=True))
        return devices

    @classmethod
    def _list_windows(cls) -> list[BlockDevice]:
        devices: list[BlockDevice] = []
        try:
            import win32file  # type: ignore
            for i in range(16):
                path = rf"\\.\PhysicalDrive{i}"
                try:
                    handle = win32file.CreateFile(
                        path, 0x80000000,  # GENERIC_READ
                        0x1 | 0x2,         # FILE_SHARE_READ | FILE_SHARE_WRITE
                        None, 3,            # OPEN_EXISTING
                        0,
                    )
                    win32file.CloseHandle(handle)
                    devices.append(BlockDevice(path=path, readonly=True))
                except Exception:
                    break
        except ImportError:
            raise ForensicError(
                "Windows 下需要 pywin32 (pip install pywin32)"
            )
        return devices

    # ── 只读打开设备 ──────────────────────────────────────

    @classmethod
    def open_readonly(cls, path: str) -> int:
        """以只读方式打开块设备，返回 fd。"""
        if cls.info.is_windows:
            raise NotImplementedError("Windows 需通过 pywin32 打开设备")
        flags = os.O_RDONLY | os.O_BINARY if hasattr(os, "O_BINARY") else os.O_RDONLY
        return os.open(path, flags)

    # ── 辅助 ──────────────────────────────────────────────

    @staticmethod
    def _sysfs_path(path: str) -> str:
        return path

    @staticmethod
    def _sysfs_read(path: str) -> str:
        try:
            with open(path) as f:
                return f.read().strip()
        except Exception:
            return ""

    @classmethod
    def require_admin(cls) -> None:
        if not cls.info.is_admin:
            raise ForensicError(
                "此操作需要管理员/root 权限。"
                "Linux/macOS: sudo ftk ... | Windows: 以管理员身份运行"
            )

    @classmethod
    def require_platform(cls, *systems: str) -> None:
        if cls.info.system not in systems:
            raise ForensicError(
                f"此模块仅支持 {', '.join(systems)}，当前为 {cls.info.system}"
            )
