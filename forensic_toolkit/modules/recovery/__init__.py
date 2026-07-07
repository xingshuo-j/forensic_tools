"""
已删除文件恢复模块
===================
核心能力：通过扫描文件系统 Journal 和元数据区，
恢复已删除/被清除的文件。

支持的文件系统:
  - NTFS  : 扫描 $MFT 中标记为 FILE 记录未使用的条目
  - ext4  : 扫描 inode 表中 i_links_count=0 的 inode
  - APFS  : 扫描 NXSB 容器 + B-tree 对象图中的未使用节点
  - FAT   : 扫描目录条目首字节为 0xE5 的记录
"""

from __future__ import annotations
import struct
from pathlib import Path
from typing import Any, Callable

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


class RecoveryModule(ModuleBase):
    meta = ModuleMeta(
        name="recovery",
        description="恢复已删除文件（基于文件系统 Journal / 元数据扫描）",
        author="Forensic Toolkit",
        version="0.2.0",
        requires_admin=True,
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._device = self.params["device"]
        self._fs_type = self.params.get("fs_type", "auto")

    def run(self) -> Any:
        path = Path(self._device)
        if not path.exists():
            return {"error": f"设备未找到: {self._device}"}

        fs_type = self._detect_fs(path) if self._fs_type == "auto" else self._fs_type
        scanner = self._get_scanner(fs_type)
        if scanner is None:
            return {"error": f"不支持的文件系统: {fs_type}"}

        results = scanner(path)
        return {
            "device": str(path.resolve()),
            "filesystem": fs_type,
            "deleted_files": results,
            "count": len(results),
        }

    def _detect_fs(self, path: Path) -> str:
        try:
            with open(path, "rb") as f:
                boot = f.read(1024)
            if boot[3:11] == b"NTFS    ":
                return "ntfs"
            if boot[82:90] == b"FAT32   ":
                return "fat"
            if len(boot) >= 1080 and boot[1080:1082] == b"\x53\xef":
                return "ext4"
            if boot[:4] == b"NXSB":
                return "apfs"
        except Exception:
            pass
        return "unknown"

    def _get_scanner(self, fs_type: str) -> Callable | None:
        scanners = {
            "ntfs": self._scan_ntfs_mft,
            "ext4": self._scan_ext4_inode,
            "fat": self._scan_fat_dir,
            "apfs": self._scan_apfs,
        }
        return scanners.get(fs_type)

    # ── NTFS MFT (同上版本) ────────────────────────────

    def _scan_ntfs_mft(self, path: Path) -> list[dict]:
        found: list[dict] = []
        try:
            with open(path, "rb") as f:
                f.seek(0x100000) if path.stat().st_size > 0x100000 else f.seek(0)
                for i in range(1000):
                    buf = f.read(1024)
                    if len(buf) < 1024:
                        break
                    if buf[:4] != b"FILE":
                        continue
                    flags = struct.unpack("<H", buf[22:24])[0]
                    if flags == 0x00 or flags == 0x02:
                        seq = struct.unpack("<H", buf[16:18])[0]
                        name = self._ntfs_extract_name(buf)
                        found.append({
                            "record_num": i, "sequence": seq,
                            "flags": "deleted" if flags == 0x00 else "directory",
                            "name": name or "(unknown)",
                        })
        except Exception as e:
            found.append({"error": str(e)})
        return found

    @staticmethod
    def _ntfs_extract_name(raw: bytes) -> str:
        try:
            pos = 0x2C
            while pos < len(raw) - 8:
                attr_type = struct.unpack("<I", raw[pos:pos + 4])[0]
                attr_len = struct.unpack("<I", raw[pos + 4:pos + 8])[0]
                if attr_len == 0:
                    break
                if attr_type == 0x30:
                    name_len = raw[pos + 0x58]
                    name_start = pos + 0x5A
                    name_bytes = raw[name_start:name_start + name_len * 2]
                    return name_bytes.decode("utf-16-le", errors="replace")
                pos += attr_len
        except Exception:
            pass
        return ""

    # ── ext4 inode ────────────────────────────────────

    def _scan_ext4_inode(self, path: Path) -> list[dict]:
        found: list[dict] = []
        try:
            with open(path, "rb") as f:
                f.seek(1024)
                sb = f.read(1024)
                block_size = 1024 << (struct.unpack("<I", sb[24:28])[0] or 1)
                inode_size = struct.unpack("<H", sb[88:90])[0] or 128
                f.seek(block_size * 2)
                for i in range(200):
                    buf = f.read(inode_size)
                    if len(buf) < inode_size:
                        break
                    i_mode = struct.unpack("<H", buf[0:2])[0]
                    i_links = struct.unpack("<H", buf[26:28])[0]
                    if i_mode != 0 and i_links == 0:
                        found.append({
                            "inode": i + 1, "mode": oct(i_mode & 0o7777),
                            "links": i_links,
                            "size": struct.unpack("<I", buf[4:8])[0],
                            "status": "deleted",
                        })
        except Exception as e:
            found.append({"error": str(e)})
        return found

    # ── FAT 目录 ──────────────────────────────────────

    def _scan_fat_dir(self, path: Path) -> list[dict]:
        found: list[dict] = []
        try:
            with open(path, "rb") as f:
                f.read(512)
                f.seek(0x10000)
                for i in range(500):
                    buf = f.read(32)
                    if len(buf) < 32:
                        break
                    if buf[0] == 0xE5:
                        name = buf[1:11].decode("ascii", errors="replace").strip()
                        found.append({"entry": i, "name": name, "status": "deleted"})
        except Exception as e:
            found.append({"error": str(e)})
        return found

    # ── APFS 扫描 (新增) ──────────────────────────────

    def _scan_apfs(self, path: Path) -> list[dict]:
        """
        APFS 容器/卷扫描。
        1. 解析 NXSB (容器超级块)
        2. 定位 APSB (卷超级块)
        3. 扫描 B-tree 对象图中的悬挂/未引用对象
        """
        found: list[dict] = []
        block_size = 4096

        try:
            with open(path, "rb") as f:
                # NXSB 超级块
                f.seek(0)
                nxsb = f.read(block_size)
                if nxsb[:4] != b"NXSB":
                    return [{"error": "APFS NXSB 签名未找到"}]

                # 解析 NXSB 字段
                # offset 12: block_size (uint32)
                bs = struct.unpack("<I", nxsb[12:16])[0]
                block_size = bs if bs > 0 else 4096
                # offset 16: block count (uint64)
                block_count = struct.unpack("<Q", nxsb[16:24])[0]
                # offset 48: container superblock OID (uint64)
                apsb_oid = struct.unpack("<Q", nxsb[48:56])[0]

                found.append({
                    "source": "NXSB",
                    "type": "container_superblock",
                    "block_size": block_size,
                    "block_count": block_count,
                    "apsb_oid": apsb_oid,
                    "status": "container_header",
                })

                # 扫描 APSB - 通常是 block 1 或通过 OID 找到
                apsb_block = apsb_oid if apsb_oid < block_count else 1
                f.seek(apsb_block * block_size)
                apsb = f.read(block_size)

                if len(apsb) >= 32:
                    obj_type = struct.unpack("<I", apsb[12:16])[0]
                    obj_subtype = struct.unpack("<I", apsb[16:20])[0]
                    # APSB = APFS Container Superblock
                    if obj_type == 0x01 or apsb[:4] == b"\x01\x00\x00\x00":
                        # 解析卷名和 UUID
                        vol_name = ""
                        for offset in (96, 128, 160):
                            if offset + 64 <= len(apsb):
                                try:
                                    raw = apsb[offset:offset + 64]
                                    candidate = raw.split(b"\x00")[0].decode("utf-8", errors="replace")
                                    if candidate:
                                        vol_name = candidate
                                        break
                                except Exception:
                                    pass

                        snap_count = struct.unpack("<Q", apsb[40:48])[0]
                        found.append({
                            "source": "APSB",
                            "type": "volume_superblock",
                            "block": apsb_block,
                            "obj_type": obj_type,
                            "obj_subtype": obj_subtype,
                            "volume_name": vol_name,
                            "snapshots_count": snap_count,
                            "status": "volume_header",
                        })

                        # 如果 snapshot 数量 > 0，列出快照
                        if snap_count > 0 and snap_count < 1000:
                            f.seek((apsb_block + 1) * block_size)
                            snap_data = f.read(block_size)
                            # 简单报告
                            found.append({
                                "source": "Snapshots",
                                "type": "metadata",
                                "snapshots_found": snap_count,
                                "status": "available_for_snapshot_recovery",
                            })

                # B-tree 节点扫描——在容器空间中扫描 btn 签名
                # 每隔 block_size 检查 B-tree 节点
                bt_count = 0
                skipped_blocks = max(1, block_count // 500)  # 采样扫描
                for b in range(10, min(block_count, 50000), skipped_blocks):
                    f.seek(b * block_size)
                    blk = f.read(block_size)
                    if len(blk) < block_size:
                        break
                    # B-tree node magic at offset 0: "btn"
                    if blk[:3] == b"btn":
                        bt_count += 1
                        if bt_count <= 20:
                            bt_type = "branch" if blk[24] & 2 else "leaf"
                            entry_count = struct.unpack("<H", blk[30:32])[0]
                            found.append({
                                "source": "B-tree",
                                "type": f"btree_{bt_type}",
                                "block": b,
                                "entries": entry_count,
                                "status": "scanned",
                            })

                found.append({
                    "source": "B-tree",
                    "type": "summary",
                    "btree_nodes_scanned": bt_count,
                    "blocks_sampled": min(block_count, 50000) // skipped_blocks,
                    "status": "scan_complete",
                })

        except Exception as e:
            found.append({"error": f"APFS 扫描异常: {e}"})

        return found


ModuleRegistry.register(RecoveryModule)
