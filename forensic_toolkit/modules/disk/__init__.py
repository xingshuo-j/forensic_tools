"""
磁盘分析模块
=============
扩展的磁盘分析能力 (CLI 基础枚举之外的进阶功能)。

待实现:
  - MBR / GPT 分区表解析
  - 保留扇区扫描
  - 磁盘签名/指纹
"""

from __future__ import annotations
import struct
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


class DiskModule(ModuleBase):
    meta = ModuleMeta(
        name="disk",
        description="磁盘详细分析 (MBR/GPT 分区表)",
        author="Forensic Toolkit",
        version="0.1.0",
        requires_admin=True,
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])

    def run(self) -> Any:
        if not self._path.exists():
            return {"error": f"设备未找到: {self._path}"}

        result = {"device": str(self._path), "partitions": []}

        try:
            data = open(self._path, "rb").read(1024)

            # MBR 检测
            if data[510:512] == b"\x55\xAA":
                result["partition_table"] = "MBR"
                for i in range(4):
                    off = 446 + i * 16
                    entry = data[off:off + 16]
                    if len(entry) < 16:
                        break
                    status = entry[0]
                    ptype = entry[4]
                    if ptype != 0:
                        lba = struct.unpack("<I", entry[8:12])[0]
                        size = struct.unpack("<I", entry[12:16])[0]
                        result["partitions"].append({
                            "number": i + 1,
                            "type": f"0x{ptype:02X}",
                            "bootable": status == 0x80,
                            "start_lba": lba,
                            "size_sectors": size,
                        })

            # GPT 检测 (MBR Protective + GPT header at LBA1)
            if data[450:454] == b"\xEE\x00\x00\x00":
                result["partition_table"] = "GPT (protective MBR)"

        except Exception as e:
            return {"error": str(e)}

        return result


ModuleRegistry.register(DiskModule)
