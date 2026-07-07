"""
网络取证模块
=============
解析 PCAP / PCAPNG 文件，提取网络连接信息和时间线。

功能:
  - PCAP 全局头部解析
  - PCAPNG 分块结构解析
  - Ethernet / IP / TCP / UDP / IPv6 头部解析
  - DNS 查询提取
  - 连接时间线 (源 IP:端口 -> 目标 IP:端口)
"""

from __future__ import annotations
import struct
import socket
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


# ── 魔数 ──────────────────────────────────────────────

_PCAP_MAGIC = 0xA1B2C3D4
_PCAP_MAGIC_SWAPPED = 0xD4C3B2A1
_PCAPNG_MAGIC = 0x0A0D0D0A  # Section Header Block type (= magic)

# ── PCAPNG 块类型 ─────────────────────────────────────

_BLOCK_SHB = 0x0A0D0D0A       # Section Header Block
_BLOCK_IDB = 0x00000001       # Interface Description Block
_BLOCK_EPB = 0x00000006       # Enhanced Packet Block
_BLOCK_SPB = 0x00000003       # Simple Packet Block

# ── 协议常量 ──────────────────────────────────────────

_ETHERTYPE_IPV4 = 0x0800
_ETHERTYPE_ARP = 0x0806
_ETHERTYPE_IPV6 = 0x86DD
_ETHERTYPE_VLAN = 0x8100

_IPPROTO_TCP = 6
_IPPROTO_UDP = 17
_IPPROTO_ICMPv6 = 58

_DNS_QR_QUERY = 0
_DNS_QR_RESPONSE = 1

# ── PCAPNG 字节序辅助 ────────────────────────────────

_BOM_MATCH = 0x1A2B3C4D       # 与本机同序
_BOM_SWAP = 0x4D3C2B1A        # 与本机反序


def _pcap_parse(path: Path, max_packets: int = 50000) -> dict:
    """解析 PCAP / PCAPNG 文件，返回结构化结果。"""
    with open(path, "rb") as f:
        head = f.read(4)
        if len(head) < 4:
            return {"error": "文件太短"}
        magic = struct.unpack("<I", head)[0]

    if magic in (_PCAP_MAGIC, _PCAP_MAGIC_SWAPPED):
        return _pcap_legacy(path, max_packets)
    if magic == _PCAPNG_MAGIC:
        return _pcapng(path, max_packets)
    return {"error": f"不支持的格式 (魔数: 0x{magic:08X})"}


# ── 遗留 PCAP 解析 ────────────────────────────────────

def _pcap_legacy(path: Path, max_packets: int = 50000) -> dict:
    """解析遗留 PCAP 格式。"""
    result = {
        "file": str(path.resolve()),
        "format": "PCAP (legacy)",
        "packets": [],
        "connections": [],
        "dns_queries": [],
        "stats": {"total": 0, "ipv4": 0, "ipv6": 0, "tcp": 0, "udp": 0, "arp": 0},
    }

    with open(path, "rb") as f:
        gheader = f.read(24)
        if len(gheader) < 24:
            return {"error": "无效的 PCAP 文件 (头过短)"}

        magic, ver_major, ver_minor = struct.unpack("<IHH", gheader[:8])
        le = magic == _PCAP_MAGIC
        snaplen, linktype = struct.unpack("<II" if le else ">II", gheader[16:24])

        result["link_type"] = {1: "Ethernet", 0: "BSD Loopback"}.get(linktype, f"Unknown({linktype})")
        result["snaplen"] = snaplen

        connections: dict[tuple, dict] = {}
        pkt_count = 0

        while pkt_count < max_packets:
            rec = f.read(16)
            if len(rec) < 16:
                break
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack("<IIII" if le else ">IIII", rec)
            pkt_data = f.read(incl_len)
            if len(pkt_data) < incl_len:
                break
            pkt_count += 1
            pkt_info = {"ts": ts_sec + ts_usec / 1e6, "size": orig_len}
            _pkt_process(pkt_data, linktype, pkt_info, result, connections)
            result["packets"].append(pkt_info)

        result = _finalize_connections(result, connections)

    result["stats"]["total"] = pkt_count
    return result


# ── PCAPNG 解析 ───────────────────────────────────────

def _pcapng(path: Path, max_packets: int = 50000) -> dict:
    """解析 PCAPNG 格式。"""
    result = {
        "file": str(path.resolve()),
        "format": "PCAPNG",
        "packets": [],
        "connections": [],
        "dns_queries": [],
        "stats": {"total": 0, "ipv4": 0, "ipv6": 0, "tcp": 0, "udp": 0, "arp": 0},
    }

    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 28:
        return {"error": "PCAPNG 文件太短"}

    # Section Header Block — 确定字节序
    shb_type = struct.unpack("<I", data[0:4])[0]
    if shb_type != _PCAPNG_MAGIC:
        return {"error": f"无效的 PCAPNG Section Header: 0x{shb_type:08X}"}

    shb_length = struct.unpack("<I", data[4:8])[0]
    bom = struct.unpack("<I", data[8:12])[0]

    if bom == _BOM_MATCH:
        le = True
    elif bom == _BOM_SWAP:
        le = False
    else:
        return {"error": f"无法确定 PCAPNG 字节序 (BOM: 0x{bom:08X})"}

    def _g16(off: int) -> int:
        return struct.unpack("<H" if le else ">H", data[off:off + 2])[0]

    def _g32(off: int) -> int:
        return struct.unpack("<I" if le else ">I", data[off:off + 4])[0]

    def _g64(off: int) -> int:
        return struct.unpack("<Q" if le else ">Q", data[off:off + 8])[0]

    # 读取 SHB 字段
    major = _g16(12)
    minor = _g16(14)
    section_len = _g64(16)

    result["version"] = f"{major}.{minor}"
    result["section_length"] = section_len if section_len != -1 else "(unspecified)"

    link_types: dict[int, int] = {}   # interface_id -> link_type
    snaplens: dict[int, int] = {}     # interface_id -> snaplen
    connections: dict[tuple, dict] = {}
    pkt_count = 0

    # 跳过 SHB options + trailing length
    pos = 28  # 跳过 SHB 固定头 (28 字节: 4 type + 4 length + 4 BOM + 2*2 ver + 8 section_len)
    # 跳过 options (简化: 根据 shb_length 跳)
    pos = shb_length  # 下一个块从 SHB 末尾开始

    while pos + 12 <= len(data) and pkt_count < max_packets:
        blk_type = _g32(pos)
        blk_len = _g32(pos + 4)

        if blk_len < 12 or pos + blk_len > len(data):
            pos += 4
            continue

        if blk_type == _BLOCK_IDB:
            # Interface Description Block: link_type(2) + reserved(2) + snaplen(4)
            if blk_len >= 20:
                lt = _g16(pos + 8)
                sl = _g32(pos + 12)
                link_types[0] = lt  # 简化: 单接口
                snaplens[0] = sl
                if result.get("snaplen") is None:
                    result["snaplen"] = sl
                    result["link_type"] = {1: "Ethernet", 0: "BSD Loopback"}.get(lt, f"Unknown({lt})")

        elif blk_type == _BLOCK_EPB:
            if blk_len >= 28:
                iface_id = _g32(pos + 8)
                ts_high = _g32(pos + 12)
                ts_low = _g32(pos + 16)
                cap_len = _g32(pos + 20)
                orig_len = _g32(pos + 24)
                ts = ts_high + ts_low / 1e6
                pkt_start = pos + 28
                if pkt_start + cap_len <= len(data):
                    pkt_data = data[pkt_start:pkt_start + cap_len]
                    pkt_count += 1
                    pkt_info = {"ts": ts, "size": orig_len}
                    lt = link_types.get(iface_id, 1)
                    _pkt_process(pkt_data, lt, pkt_info, result, connections)
                    result["packets"].append(pkt_info)

        elif blk_type == _BLOCK_SPB:
            if blk_len >= 16:
                cap_len = blk_len - 16
                pkt_start = pos + 8
                if cap_len > 0 and pkt_start + cap_len <= len(data):
                    pkt_data = data[pkt_start:pkt_start + cap_len]
                    pkt_count += 1
                    lt = link_types.get(0, 1)
                    pkt_info = {"ts": 0, "size": cap_len}  # SPB 无时间戳
                    _pkt_process(pkt_data, lt, pkt_info, result, connections)
                    result["packets"].append(pkt_info)

        pos += blk_len

    result = _finalize_connections(result, connections)
    result["stats"]["total"] = pkt_count
    return result


# ── 共享: 逐包处理 ────────────────────────────────────

def _pkt_process(pkt_data: bytes, linktype: int, pkt_info: dict,
                 result: dict, connections: dict) -> None:
    """处理单个数据包的链路层 + IP 层。"""
    if linktype == 1 and len(pkt_data) >= 14:
        eth_type = struct.unpack(">H", pkt_data[12:14])[0]
        ip_off = 14
        if eth_type == _ETHERTYPE_VLAN and len(pkt_data) >= 18:
            eth_type = struct.unpack(">H", pkt_data[16:18])[0]
            ip_off = 18
        if eth_type == _ETHERTYPE_IPV4:
            result["stats"]["ipv4"] += 1
            _parse_ipv4(pkt_data, ip_off, pkt_info, result, connections)
        elif eth_type == _ETHERTYPE_IPV6:
            result["stats"]["ipv6"] += 1
            _parse_ipv6(pkt_data, ip_off, pkt_info, result, connections)
        elif eth_type == _ETHERTYPE_ARP:
            result["stats"]["arp"] += 1


# ── 共享: 汇总连接 ────────────────────────────────────

def _finalize_connections(result: dict, connections: dict) -> dict:
    """汇总 connections dict 为 result['connections'] 列表。"""
    for key, info in connections.items():
        result["connections"].append({
            "src": f"{key[0]}:{key[1]}",
            "dst": f"{key[2]}:{key[3]}",
            "protocol": info.get("proto", ""),
            "packets": info.get("packets", 0),
            "start": info.get("start", 0),
            "end": info.get("end", 0),
        })
    result["connections"] = sorted(
        result["connections"], key=lambda x: x.get("start", 0), reverse=True
    )[:200]
    return result


# ── IPv4 解析 ─────────────────────────────────────────

def _parse_ipv4(data: bytes, off: int, pkt_info: dict, result: dict,
                connections: dict) -> None:
    """解析 IPv4 + TCP/UDP 头。"""
    if off + 20 > len(data):
        return
    ver_ihl = data[off]
    ihl = (ver_ihl & 0x0F) * 4
    if ihl < 20 or off + ihl > len(data):
        return
    proto = data[off + 9]
    src_ip = socket.inet_ntoa(data[off + 12:off + 16])
    dst_ip = socket.inet_ntoa(data[off + 16:off + 20])

    pkt_info["src_ip"] = src_ip
    pkt_info["dst_ip"] = dst_ip
    pkt_info["proto"] = {_IPPROTO_TCP: "TCP", _IPPROTO_UDP: "UDP"}.get(proto, str(proto))

    if proto == _IPPROTO_TCP and off + ihl + 20 <= len(data):
        tcp_off = off + ihl
        src_port = struct.unpack(">H", data[tcp_off:tcp_off + 2])[0]
        dst_port = struct.unpack(">H", data[tcp_off + 2:tcp_off + 4])[0]
        pkt_info["src_port"] = src_port
        pkt_info["dst_port"] = dst_port
        result["stats"]["tcp"] += 1

        key = (src_ip, src_port, dst_ip, dst_port)
        if key not in connections:
            connections[key] = {"proto": "TCP", "packets": 0, "start": pkt_info["ts"], "end": pkt_info["ts"]}
        c = connections[key]
        c["packets"] += 1
        c["end"] = max(c["end"], pkt_info["ts"])

        if dst_port == 53 or src_port == 53:
            _parse_dns(data, tcp_off + 20, result)

    elif proto == _IPPROTO_UDP and off + ihl + 8 <= len(data):
        udp_off = off + ihl
        src_port = struct.unpack(">H", data[udp_off:udp_off + 2])[0]
        dst_port = struct.unpack(">H", data[udp_off + 2:udp_off + 4])[0]
        pkt_info["src_port"] = src_port
        pkt_info["dst_port"] = dst_port
        result["stats"]["udp"] += 1

        key = (src_ip, src_port, dst_ip, dst_port)
        if key not in connections:
            connections[key] = {"proto": "UDP", "packets": 0, "start": pkt_info["ts"], "end": pkt_info["ts"]}
        c = connections[key]
        c["packets"] += 1
        c["end"] = max(c["end"], pkt_info["ts"])

        if dst_port == 53 or src_port == 53:
            _parse_dns(data, udp_off + 8, result)


# ── IPv6 解析 ─────────────────────────────────────────

def _parse_ipv6(data: bytes, off: int, pkt_info: dict, result: dict,
                connections: dict) -> None:
    """解析 IPv6 + TCP/UDP 头。"""
    if off + 40 > len(data):
        return
    # IPv6: version|traffic class|flow label (4) | payload_len (2) | next_header (1) | hop_limit (1)
    #       src (16) | dst (16)
    payload_len = struct.unpack(">H", data[off + 4:off + 6])[0]
    next_header = data[off + 6]
    try:
        src_ip = socket.inet_ntop(socket.AF_INET6, data[off + 8:off + 24])
        dst_ip = socket.inet_ntop(socket.AF_INET6, data[off + 24:off + 40])
    except Exception:
        return

    pkt_info["src_ip"] = src_ip
    pkt_info["dst_ip"] = dst_ip
    pkt_info["proto"] = "IPv6"

    # 目前只统计不深入
    result["stats"]["ipv6"] += 1


# ── DNS 解析 ──────────────────────────────────────────

def _parse_dns(data: bytes, off: int, result: dict) -> None:
    """简单 DNS 查询/响应提取。"""
    if off + 12 > len(data):
        return
    try:
        flags = struct.unpack(">H", data[off + 2:off + 4])[0]
        qr = (flags >> 15) & 1
        qcount = struct.unpack(">H", data[off + 4:off + 6])[0]

        pos = off + 12
        for _ in range(min(qcount, 10)):
            qname, pos = _decode_dns_name(data, pos)
            if pos + 4 > len(data):
                break
            qtype = struct.unpack(">H", data[pos:pos + 2])[0]
            pos += 4
            qtype_name = {1: "A", 2: "NS", 5: "CNAME", 15: "MX", 28: "AAAA"}.get(qtype, str(qtype))
            result["dns_queries"].append({
                "query": qname,
                "type": qtype_name,
                "direction": "request" if qr == _DNS_QR_QUERY else "response",
            })
    except Exception:
        pass


def _decode_dns_name(data: bytes, off: int) -> tuple[str, int]:
    """DNS 名称解压。"""
    labels = []
    pos = off
    jumped = False
    jump_off = 0

    while pos < len(data):
        length = data[pos]
        if length == 0:
            if not jumped:
                pos += 1
            break
        if length & 0xC0:
            if pos + 2 > len(data):
                break
            ptr = ((length & 0x3F) << 8) | data[pos + 1]
            if not jumped:
                pos += 2
                jump_off = pos
            pos = ptr
            jumped = True
            continue
        pos += 1
        if pos + length > len(data):
            break
        labels.append(data[pos:pos + length].decode("ascii", errors="replace"))
        pos += length

    if jumped:
        pos = jump_off
    return ".".join(labels), pos


# ── 模块类 ────────────────────────────────────────────

class NetworkModule(ModuleBase):
    meta = ModuleMeta(
        name="network",
        description="PCAP / PCAPNG 网络取证分析 (连接时间线 / DNS 查询)",
        author="Forensic Toolkit",
        version="0.2.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])

    def run(self) -> Any:
        if not self._path.exists():
            return {"error": f"路径不存在: {self._path}"}
        return _pcap_parse(self._path)


ModuleRegistry.register(NetworkModule)
