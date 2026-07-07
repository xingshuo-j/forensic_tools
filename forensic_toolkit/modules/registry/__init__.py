"""
Windows Registry 解析模块
===========================
离线解析 Registry Hive 文件，提取键值结构。

支持: SAM, SYSTEM, SOFTWARE, NTUSER.DAT 等 hive。

格式参考: https://github.com/msuhanov/regf/blob/master/Windows%20registry%20file%20format.md
"""

from __future__ import annotations
import struct
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


# ── Registry Hive 解析 ───────────────────────────────

_HIVE_SIG = b"regf"
_NK_SIG = b"nk"
_VK_SIG = b"vk"
_SK_SIG = b"sk"
_LH_SIG = b"lh"
_LF_SIG = b"lf"
_RI_SIG = b"ri"


def _parse_hive(path: Path, max_keys: int = 5000) -> dict:
    """解析 Registry Hive 文件。"""
    data = path.read_bytes()
    if len(data) < 4096 or data[:4] != _HIVE_SIG:
        return {"error": "不是有效的 Registry Hive 文件"}

    le = True  # Registry 始终是 little-endian

    def g16(off: int) -> int:
        return struct.unpack("<H", data[off:off + 2])[0]

    def g32(off: int) -> int:
        return struct.unpack("<I", data[off:off + 4])[0]

    def g64(off: int) -> int:
        return struct.unpack("<Q", data[off:off + 8])[0]

    # Base block 解析
    seq1 = g32(4)
    seq2 = g32(8)
    timestamp = g64(12)  # Windows FILETIME
    major = g32(28)
    minor = g32(32)
    root_cell = g32(36)
    file_size = g32(40)

    info = {
        "path": str(path.resolve()),
        "sequence": f"{seq1}/{seq2}",
        "version": f"{major}.{minor}",
        "file_size": file_size,
    }

    # HBIN 定位
    hbins = []
    pos = 4096  # 第一个 HBIN 起始
    while pos < min(len(data), file_size):
        if data[pos:pos + 4] == b"hb\x00\x00":
            hbin_size = g32(pos + 4)
            # hbin_size 是 4K 对齐的
            hbins.append({"offset": pos, "size": hbin_size, "end": pos + hbin_size})
            pos += hbin_size
        else:
            pos += 1
            if pos > len(data) - 4:
                break

    # 遍历键树
    keys = []
    _visited = set()

    def _walk_key(cell_off: int, depth: int, path_str: str) -> None:
        if cell_off in _visited or len(keys) >= max_keys:
            return
        _visited.add(cell_off)

        # 读取 cell header
        if cell_off + 4 > len(data):
            return
        cell_size = abs(g32(cell_off))  # 绝对值
        if cell_size < 0x4C or cell_off + cell_size > len(data):
            return
        seg_off = cell_off + 4  # 跳过 cell header

        # NK record
        if data[seg_off:seg_off + 2] != _NK_SIG:
            return

        flags = g16(seg_off + 2)
        key_tm = g64(seg_off + 4)  # last write time
        # parent = g32(seg_off + 24)  # 父键指针
        subkeys_count = g32(seg_off + 28)
        subkeys_list = g32(seg_off + 36)
        values_count = g32(seg_off + 44)
        values_list = g32(seg_off + 48)
        name_len = g16(seg_off + 74)
        key_name = data[seg_off + 76:seg_off + 76 + name_len].decode("utf-16-le", errors="replace") if name_len > 0 else "(default)"

        full_path = f"{path_str}\\{key_name}" if path_str else key_name

        keys.append({
            "path": full_path,
            "name": key_name,
            "last_write": _ft_to_iso(key_tm),
            "subkeys": subkeys_count,
            "values": values_count,
        })

        # 解析值 (VK)
        if values_list and values_count > 0:
            vl_off = values_list & 0x7FFFFFFF
            if vl_off + 4 <= len(data):
                vl_size = abs(g32(vl_off))
                vl_data_off = vl_off + 4
                # 可能是 lh/lf/li 列表
                for vi in range(min(values_count, 100)):
                    voff = vl_data_off + 4 + vi * 4
                    if voff + 4 > len(data) or voff > vl_off + vl_size:
                        break
                    vk_off = g32(voff) & 0x7FFFFFFF
                    _parse_vk(data, vk_off, full_path, keys)

        # 递归子键
        if subkeys_list and subkeys_count > 0:
            sl_off = subkeys_list & 0x7FFFFFFF
            if sl_off + 4 <= len(data):
                sl_cell_size = abs(g32(sl_off))
                sl_data_off = sl_off + 4
                lst_sig = data[sl_data_off:sl_data_off + 2]
                if lst_sig in (_LH_SIG, _LF_SIG, _LI_SIG):
                    count = g16(sl_data_off + 2)
                    for si in range(min(count, min(subkeys_count, 200))):
                        entry_off = sl_data_off + 4 + si * 4
                        if entry_off + 4 > len(data):
                            break
                        sub_cell = g32(entry_off) & 0x7FFFFFFF
                        _walk_key(sub_cell, depth + 1, full_path)

    # 从根键开始
    root_off = root_cell & 0x7FFFFFFF
    _walk_key(root_off, 0, "")

    info["keys"] = keys
    info["key_count"] = len(keys)
    return info


def _parse_vk(data: bytes, vk_off: int, parent_path: str, keys: list) -> None:
    """解析 VK (value) 记录。"""
    if vk_off + 4 > len(data):
        return
    cell_size = abs(struct.unpack("<I", data[vk_off:vk_off + 4])[0])
    if cell_size < 20 or vk_off + cell_size > len(data):
        return
    seg = vk_off + 4
    if data[seg:seg + 2] != _VK_SIG:
        return

    name_len = struct.unpack("<H", data[seg + 2:seg + 4])[0]
    data_size = struct.unpack("<I", data[seg + 4:seg + 8])[0]
    data_offset = struct.unpack("<I", data[seg + 8:seg + 12])[0]
    vtype = struct.unpack("<I", data[seg + 12:seg + 16])[0]

    if name_len > 0:
        vname = data[seg + 20:seg + 20 + name_len].decode("utf-16-le", errors="replace")
    else:
        vname = "(Default)"

    # 类型名称
    type_names = {
        1: "REG_SZ", 2: "REG_EXPAND_SZ", 3: "REG_BINARY", 4: "REG_DWORD",
        7: "REG_MULTI_SZ", 11: "REG_QWORD",
    }
    type_name = type_names.get(vtype, f"REG_0x{vtype:X}")

    # 读取值
    value = ""
    if data_size >= 0 and abs(data_size) < 2048:
        actual_size = abs(data_size)
        d_off = data_offset if (data_size & 0x80000000) == 0 else seg + 20
        if d_off + actual_size <= len(data):
            raw = data[d_off:d_off + actual_size]
            if vtype == 1 or vtype == 2:  # 字符串
                value = raw.decode("utf-16-le", errors="replace").strip("\x00").strip()
            elif vtype == 4:  # DWORD
                value = str(struct.unpack("<I", raw[:4])[0])
            elif vtype == 11:  # QWORD
                value = str(struct.unpack("<Q", raw[:8])[0])
            elif vtype == 3:  # Binary
                value = raw.hex()[:64]
            else:
                value = f"({type_name} {actual_size} bytes)"

    keys.append({
        "path": f"{parent_path} [{vname}]",
        "name": vname,
        "type": type_name,
        "value": value[:128] if value else "",
    })


def _ft_to_iso(ft: int) -> str:
    """Windows FILETIME -> ISO 时间字符串。"""
    if ft == 0:
        return ""
    try:
        from datetime import datetime, timezone
        ts = (ft - 116444736000000000) / 10000000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")
    except Exception:
        return ""


# 注册 SIG 常量，LI 在上面用到
_LI_SIG = b"li"


class RegistryModule(ModuleBase):
    meta = ModuleMeta(
        name="registry",
        description="Windows Registry Hive 离线解析",
        author="Forensic Toolkit",
        version="0.1.0",
        supported_platforms=("linux", "darwin", "windows"),
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])

    _MAX_HIVE_SIZE = 500 * 1024 * 1024            # 500 MiB hive 上限

    def run(self) -> Any:
        if not self._path.exists():
            return {"error": f"文件不存在: {self._path}"}
        size = self._path.stat().st_size
        if size > self._MAX_HIVE_SIZE:
            return {
                "error": f"Hive 文件过大 ({size / (1024*1024):.0f} MiB)，超出解析上限 ({self._MAX_HIVE_SIZE // (1024*1024)} MiB)。",
                "file": str(self._path.resolve()),
                "size": size,
            }
        return _parse_hive(self._path)


ModuleRegistry.register(RegistryModule)
