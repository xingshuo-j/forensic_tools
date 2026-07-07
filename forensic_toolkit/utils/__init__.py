"""
工具层 — 通用取证工具函数

提供各模块共享的辅助函数，不依赖任何第三方库。
"""

from __future__ import annotations
import struct
import binascii
from datetime import datetime, timezone
from typing import Iterator


# ── Hex Dump ──────────────────────────────────────────

def hexdump(data: bytes, offset: int = 0, length: int = 128, width: int = 16) -> str:
    """生成标准的 hex dump 输出，类似 xxd 格式。"""
    lines = []
    data = data[:length]
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        # pad hex part
        hex_part = hex_part.ljust(width * 3 - 1)
        ascii_part = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in chunk)
        lines.append(f"{offset + i:08x}  {hex_part}  |{ascii_part}|")
    return "\n".join(lines)


# ── Timestamp Utilities ──────────────────────────────

def unix_to_iso(ts: float) -> str:
    """Unix timestamp -> ISO-8601 字符串。"""
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")
    except (OSError, ValueError, OverflowError):
        return "(invalid)"


def windows_filetime_to_unix(ft: int) -> float | None:
    """Windows FILETIME (100-ns intervals since 1601-01-01) -> Unix timestamp。"""
    try:
        return (ft - 116444736000000000) / 10000000.0
    except (OverflowError, TypeError):
        return None


def dos_date_to_unix(dos_date: int, dos_time: int) -> float | None:
    """DOS date/time (FAT) -> Unix timestamp。"""
    try:
        dt = datetime(
            year=((dos_date >> 9) & 0x7F) + 1980,
            month=(dos_date >> 5) & 0x0F,
            day=dos_date & 0x1F,
            hour=(dos_time >> 11) & 0x1F,
            minute=(dos_time >> 5) & 0x3F,
            second=(dos_time & 0x1F) * 2,
        )
        return dt.timestamp()
    except (ValueError, OverflowError):
        return None


# ── Binary Helpers ───────────────────────────────────

def bytes_to_int_le(data: bytes, offset: int = 0, size: int = 4) -> int:
    """Little-endian 字节序读取整数。"""
    return int.from_bytes(data[offset:offset + size], "little")


def bytes_to_int_be(data: bytes, offset: int = 0, size: int = 4) -> int:
    """Big-endian 字节序读取整数。"""
    return int.from_bytes(data[offset:offset + size], "big")


def find_bytes(data: bytes, pattern: bytes, start: int = 0) -> list[int]:
    """查找所有匹配位置。"""
    positions = []
    pos = start
    while True:
        pos = data.find(pattern, pos)
        if pos == -1:
            break
        positions.append(pos)
        pos += 1
    return positions


def align_up(val: int, alignment: int) -> int:
    """向上对齐。"""
    return (val + alignment - 1) // alignment * alignment


# ── Text Utilities ───────────────────────────────────

def strip_null(s: str) -> str:
    """移除字符串中的 null 字符和尾部空白。"""
    return s.replace("\x00", "").strip()


def extract_ascii_null_terminated(data: bytes, offset: int, max_len: int = 256) -> str:
    """从指定偏移提取 null-terminated ASCII 字符串。"""
    end = data.find(b"\x00", offset, offset + max_len)
    if end == -1:
        end = offset + max_len
    return data[offset:end].decode("ascii", errors="replace").strip()


def extract_utf16_null_terminated(data: bytes, offset: int, max_len: int = 512) -> str:
    """从指定偏移提取 null-terminated UTF-16LE 字符串。"""
    raw = data[offset:offset + max_len]
    parts = []
    for i in range(0, len(raw), 2):
        if i + 1 >= len(raw):
            break
        code = raw[i] | (raw[i + 1] << 8)
        if code == 0:
            break
        parts.append(chr(code))
    return "".join(parts).strip()


