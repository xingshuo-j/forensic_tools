"""
File Carving — 文件雕刻模块
==============================
通过 Magic Bytes (文件签名) 从原始数据中恢复文件。

支持的格式:
  JPEG     FF D8 FF
  PDF      25 50 44 46
  ZIP      50 4B 03 04  /  50 4B 05 06  /  50 4B 07 08
  PNG      89 50 4E 47 0D 0A 1A 0A
  GIF      47 49 46 38  (37/39)
  ELF      7F 45 4C 46
  RIFF (AVI/WAV)  52 49 46 46
  XML/HTML 3C 3F 78 6D 6C / 3C 68 74 6D 6C
"""

from __future__ import annotations
import struct
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


# ── 文件签名定义 ─────────────────────────────────────
# (name, magic_bytes, ext, min_size, has_footer, footer_bytes, max_size)
_SIGNATURES: list[tuple] = [
    ("JPEG",        b"\xff\xd8\xff",        "jpg",  1024,    True,   b"\xff\xd9",        50 * 1024 * 1024),
    ("PDF",         b"%PDF",                "pdf",  1024,    False,  b"%%EOF",           100 * 1024 * 1024),
    ("ZIP",         b"PK\x03\x04",          "zip",  512,     False,  b"PK\x05\x06",      200 * 1024 * 1024),
    ("PNG",         b"\x89PNG\r\n\x1a\n",   "png",  1024,    True,   b"IEND\xae\x42\x60\x82", 50 * 1024 * 1024),
    ("GIF87a",      b"GIF87a",              "gif",  128,     True,   b"\x00\x3b",        10 * 1024 * 1024),
    ("GIF89a",      b"GIF89a",              "gif",  128,     True,   b"\x00\x3b",        10 * 1024 * 1024),
    ("ELF",         b"\x7fELF",             "elf",  512,     False,  None,               100 * 1024 * 1024),
    ("RIFF",        b"RIFF",                "riff", 512,     False,  None,               100 * 1024 * 1024),
    ("XML",         b"<?xml",               "xml",  128,     False,  None,               10 * 1024 * 1024),
    ("HTML",        b"<html",               "html", 128,     False,  b"</html>",         10 * 1024 * 1024),
    ("BMP",         b"BM",                  "bmp",  128,     False,  None,               50 * 1024 * 1024),
]


class CarvingModule(ModuleBase):
    meta = ModuleMeta(
        name="carving",
        description="通过文件签名 (Magic Bytes) 恢复文件",
        author="Forensic Toolkit",
        version="0.1.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])
        self._output = Path(self.params.get("output_dir", "./carved_output"))
        self._types = self.params.get("types", "all")
        self._max_size = int(self.params.get("max_size", 0))
        self._dry_run = bool(self.params.get("dry_run", True))  # 默认不写入

    def run(self) -> Any:
        if not self._path.exists():
            return {"error": f"路径不存在: {self._path}"}

        data = self._read_data()
        if isinstance(data, dict) and "error" in data:
            return data

        # 选择签名
        sigs = _SIGNATURES
        if self._types != "all":
            types_set = {t.strip().lower() for t in self._types.split(",")}
            sigs = [s for s in sigs if s[0].lower() in types_set]

        found = []
        for sig in sigs:
            name, magic, ext, min_sz, has_footer, footer, max_sz = sig
            max_sz = self._max_size if self._max_size else max_sz
            results = self._scan_signature(data, name, magic, ext, min_sz, max_sz, has_footer, footer)
            found.extend(results)

        found.sort(key=lambda x: x["offset"])

        if not self._dry_run:
            self._extract_files(data, found)

        return {
            "source": str(self._path.resolve()),
            "files_found": len(found),
            "output_dir": str(self._output.resolve()) if not self._dry_run else "(dry-run)",
            "dry_run": self._dry_run,
            "results": found[:200],
        }

    def _read_data(self) -> bytes:
        try:
            size = self._path.stat().st_size
            # 最多读 500 MiB
            read_size = min(size, 500 * 1024 * 1024) if size > 0 else 500 * 1024 * 1024
            with open(self._path, "rb") as f:
                return f.read(read_size)
        except Exception as e:
            return {"error": str(e)}

    def _scan_signature(self, data: bytes, name: str, magic: bytes, ext: str,
                        min_size: int, max_size: int,
                        has_footer: bool, footer: bytes | None) -> list[dict]:
        results = []
        pos = 0
        while True:
            pos = data.find(magic, pos)
            if pos == -1:
                break

            # 预估文件大小
            end = self._find_end(data, pos, has_footer, footer, max_size)

            file_size = end - pos
            if file_size >= min_size and file_size <= max_size:
                results.append({
                    "type": name,
                    "extension": ext,
                    "offset": pos,
                    "size": file_size,
                    "header": data[pos:pos + 16].hex(),
                })
            pos += 1
        return results

    @staticmethod
    def _find_end(data: bytes, start: int, has_footer: bool, footer: bytes | None,
                  max_size: int) -> int:
        """找到文件结束位置：有 footer 则找 footer，否则找下一个签名或 max_size。"""
        if has_footer and footer:
            fpos = data.find(footer, start + 4)
            if fpos != -1:
                return fpos + len(footer)
        return min(start + max_size, len(data))

    def _extract_files(self, data: bytes, found: list[dict]) -> None:
        self._output.mkdir(parents=True, exist_ok=True)
        for i, info in enumerate(found):
            fname = f"carved_{i:05d}_{info['offset']:08x}.{info['extension']}"
            fpath = self._output / fname
            chunk = data[info["offset"]:info["offset"] + info["size"]]
            fpath.write_bytes(chunk)


ModuleRegistry.register(CarvingModule)
