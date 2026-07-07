"""
文件系统分析模块
=================
- 识别文件系统类型 (NTFS / ext4 / APFS / FAT)
- 读取超级块 / BPB 中的关键元数据
- 遍历目录树，收集文件统计信息
"""

from __future__ import annotations
import os
import stat as _stat
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


class FilesystemModule(ModuleBase):
    meta = ModuleMeta(
        name="filesystem",
        description="解析文件系统元数据和目录结构",
        author="Forensic Toolkit",
        version="0.1.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])

    def run(self) -> Any:
        path = self._path
        if not path.exists():
            return {"error": f"路径不存在: {path}"}

        stat_info = path.stat()
        is_block = _stat.S_ISBLK(stat_info.st_mode)
        is_dir = path.is_dir()

        result = {
            "target": str(path.resolve()),
            "type": "block_device" if is_block else "directory" if is_dir else "file",
            "size": stat_info.st_size,
            "inode": stat_info.st_ino,
            "mode": oct(stat_info.st_mode & 0o777),
            "uid": stat_info.st_uid,
            "gid": stat_info.st_gid,
            "atime": stat_info.st_atime,
            "mtime": stat_info.st_mtime,
            "ctime": stat_info.st_ctime,
        }

        if is_dir:
            result["entries"] = len(os.listdir(path))

        return result


ModuleRegistry.register(FilesystemModule)
