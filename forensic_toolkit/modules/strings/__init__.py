"""
字符串提取模块
===============
从二进制文件/设备中提取可打印字符串。
支持 ASCII 和 Unicode (UTF-16LE) 编码，流式读取无文件大小限制。
"""

from __future__ import annotations
import re
import sys
from pathlib import Path
from typing import Any, Iterator

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


_CHUNK = 1 * 1024 * 1024  # 1 MiB 流式块

# 匹配跨块边界的字符串需要重叠缓冲区
_OVERLAP = 64

_ASCII_RE = re.compile(rb"[\x20-\x7E]{4,}")
_UNICODE_RE = re.compile(rb"(?:[\x20-\x7E]\x00){4,}")


def _stream_strings(file_obj, min_len: int = 4) -> Iterator[dict]:
    """
    流式扫描字符串，使用重叠缓冲区处理跨块边界的匹配。
    Yields: {offset, encoding, string}
    """
    offset = 0
    leftover = b""

    while True:
        chunk = file_obj.read(_CHUNK)
        if not chunk and not leftover:
            break

        data = leftover + chunk
        end_pos = len(data)

        for m in _ASCII_RE.finditer(data):
            s = m.group().decode("ascii")
            if len(s) >= min_len:
                yield {"offset": offset + m.start(), "encoding": "ascii", "string": s}

        for m in _UNICODE_RE.finditer(data):
            s = m.group().decode("utf-16-le", errors="replace")
            if len(s) >= min_len:
                yield {"offset": offset + m.start(), "encoding": "utf-16le", "string": s}

        # 保留尾部重叠字节
        leftover = data[-_OVERLAP:] if len(data) >= _OVERLAP else data
        offset += max(0, len(data) - len(leftover) - (len(leftover) if not chunk else 0))

        if not chunk:
            break


class StringsModule(ModuleBase):
    meta = ModuleMeta(
        name="strings",
        description="从二进制文件中流式提取可打印字符串（无大小限制）",
        author="Forensic Toolkit",
        version="0.2.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = kwargs.get("path")
        self._min_len = int(kwargs.get("min_length", 4))
        self._max_results = int(kwargs.get("max_results", 500))
        self._pipe_input = kwargs.get("pipe_input", False)

    def run(self) -> Any:
        results = []

        if self._pipe_input or self._path is None or str(self._path) == "-":
            # 从 stdin 读取
            src = sys.stdin.buffer
            source_name = "(stdin)"
        else:
            path = Path(self._path)
            if not path.exists():
                return {"error": f"路径不存在: {path}"}
            src = open(path, "rb")
            source_name = str(path.resolve())

        try:
            for item in _stream_strings(src, self._min_len):
                results.append(item)
                if len(results) >= self._max_results:
                    break
        except Exception as e:
            return {"error": str(e)}
        finally:
            if not (self._pipe_input or self._path is None or str(self._path) == "-"):
                src.close()

        results.sort(key=lambda x: x["offset"])
        return {
            "source": source_name,
            "strings_found": len(results),
            "results": results,
        }


ModuleRegistry.register(StringsModule)
