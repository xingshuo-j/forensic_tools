"""
时间线分析模块 (MAC Timeline + Bodyfile)
===========================================
递归扫描目录，收集每个文件的 MAC 时间 (Modify / Access / Change / Create)，
输出可排序的时间线。

支持两种输出格式:
  - 默认表格: {path, type, size, mtime, atime, ctime}
  - Bodyfile: 兼容 TSK mactime 的管道分隔格式
"""

from __future__ import annotations
import os
import stat
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


class TimelineModule(ModuleBase):
    meta = ModuleMeta(
        name="timeline",
        description="生成文件系统 MAC 时间线 (支持 bodyfile 格式)",
        author="Forensic Toolkit",
        version="0.3.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])
        self._depth = int(kwargs.get("depth", 3))
        self._bodyfile = bool(kwargs.get("bodyfile", False))

    def run(self) -> Any:
        path = self._path
        if not path.exists():
            return {"error": f"路径不存在: {path}"}

        if path.is_file():
            entries = [self._stat_entry(path)]
        elif path.is_dir():
            entries = []
            self._walk(path, 0, entries)
        else:
            return {"error": f"不支持的路径类型: {path}"}

        if self._bodyfile:
            return self._to_bodyfile(entries)
        return sorted(entries, key=lambda x: x.get("mtime", 0), reverse=True)

    @staticmethod
    def _stat_entry(p: Path) -> dict:
        try:
            st = p.stat()
            try:
                crtime = st.st_birthtime
            except AttributeError:
                crtime = st.st_ctime
            return {
                "path": str(p), "name": p.name,
                "type": "dir" if p.is_dir() else "file",
                "size": st.st_size, "inode": st.st_ino,
                "mode": stat.filemode(st.st_mode),
                "uid": st.st_uid, "gid": st.st_gid,
                "mtime": st.st_mtime, "atime": st.st_atime,
                "ctime": st.st_ctime, "crtime": crtime,
            }
        except (PermissionError, OSError):
            return {"path": str(p), "name": p.name, "type": "?", "size": 0,
                    "inode": 0, "mode": "??????????", "uid": 0, "gid": 0,
                    "mtime": 0, "atime": 0, "ctime": 0, "crtime": 0,
                    "error": "access_denied"}

    def _walk(self, p: Path, depth: int, acc: list) -> None:
        if depth > self._depth:
            return
        try:
            for child in p.iterdir():
                entry = self._stat_entry(child)
                acc.append(entry)
                if child.is_dir() and depth < self._depth:
                    self._walk(child, depth + 1, acc)
        except PermissionError:
            pass

    @staticmethod
    def _to_bodyfile(entries: list[dict]) -> str:
        """转换为 TSK bodyfile 格式 (mtime|name|inode|mode|uid|gid|size|atime|mtime|ctime|crtime)

        bodyfile 格式: MD5|name|inode|mode|UID|GID|size|atime|mtime|ctime|crtime
        """
        lines = []
        for e in entries:
            name = e.get("path", "").replace("|", "_")
            inode = e.get("inode", 0)
            mode = e.get("mode", "??????????")
            uid = e.get("uid", 0)
            gid = e.get("gid", 0)
            size = e.get("size", 0)
            atime = int(e.get("atime", 0))
            mtime = int(e.get("mtime", 0))
            ctime = int(e.get("ctime", 0))
            crtime = int(e.get("crtime", 0))
            # bodyfile: 0|name|inode|mode|uid|gid|size|atime|mtime|ctime|crtime
            lines.append(f"0|{name}|{inode}|{mode}|{uid}|{gid}|{size}|{atime}|{mtime}|{ctime}|{crtime}")
        return "\n".join(lines)


ModuleRegistry.register(TimelineModule)
