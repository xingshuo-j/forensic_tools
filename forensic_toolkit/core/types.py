"""Core type definitions used across the toolkit."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BlockDevice:
    """物理或逻辑块设备描述。"""
    path: str                    # 平台原生路径，如 /dev/sda, \\.\PHYSICALDRIVE0
    model: str = ""              # 设备型号
    serial: str = ""             # 序列号
    size_bytes: int = 0          # 总字节数
    block_size: int = 512        # 逻辑块大小
    readonly: bool = True        # 默认只读
    partition_table: Optional[str] = None  # "mbr" | "gpt" | None
    mount_point: Optional[str] = None      # 当前挂载点（若有）


class ForensicError(Exception):
    """取证操作中发生的可恢复错误。"""
    pass


class ForensicWarning(Warning):
    """不影响整体但值得记录的情况。"""
    pass
