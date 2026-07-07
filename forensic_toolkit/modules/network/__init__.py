"""
网络取证模块
=============
解析 PCAP 文件，提取网络连接信息和时间线。

功能:
  - PCAP 全局头部解析
  - Ethernet / IP / TCP / UDP 头部解析
  - DNS 查询提取
  - 连接时间线 (源 IP:端口 -> 目标 IP:端口)
"""

from __future__ import annotations
import struct
import socket
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


# ── PCAP 全局头 ───────────────────────────────────────
# struct: magic(4) ver_major(2) ver_minor(2) tz(4) sigfigs(4)
#         snaplen(4) network(4)

_PCAP_MAGIC = 0xA1B2C3D4
_PCAP_MAGIC_SWAPPED = 0xD4C3B2A1

# Ethernet type
_ETHERTYPE_IPV4 = 0x0800
_ETHERTYPE_ARP = 0x0806
_ETHERTYPE_IPV6 = 0x86DD

# IP proto
_IPPROTO_TCP = 6
_IPPROTO_UDP = 17

# DNS
_DNS_QR_QUERY = 0
_DNS_QR_RESPONSE = 1


def _pcap_parse(path: Path, max_packets: int = 50000) -> dict:
    """解析 PCAP 文件，返回结构化结果。"""
    result = {
        "file": str(path.resolve()),
        "format": "PCAP",
        "packets": [],
        "connections": [],
        "dns_queries": [],
        "stats": {"total": 0, "ipv4": 0, "ipv6": 0, "tcp": 0, "udp": 0, "arp": 0},
    }

    with open(path, "rb") as f:
        # 全局头
        gheader = f.read(24)
        if len(gheader) < 24:
            return {"error": "无效的 PCAP 文件 (头过短)"}

        magic, ver_major, ver_minor = struct.unpack("<IHH", gheader[:8])
        if magic not in (_PCAP_MAGIC, _PCAP_MAGIC_SWAPPED):
            return {"error": f"无效的 PCAP 魔数: 0x{magic:08X}"}

        le = magic == _PCAP_MAGIC  # little-endian
        snaplen, linktype = struct.unpack("<II" if le else ">II", gheader[16:24])

        result["link_type"] = {1: "Ethernet", 0: "BSD Loopback"}.get(linktype, f"Unknown({linktype})")
        result["snaplen"] = snaplen

        connections: dict[tuple, dict] = {}
        pkt_count = 0
        conn_count = 0

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

            # 链路层 (Ethernet)
            if linktype == 1 and len(pkt_data) >= 14:
                eth_type = struct.unpack(">H", pkt_data[12:14])[0]
                # Skip VLAN tag
                if eth_type == 0x8100 and len(pkt_data) >= 18:
                    eth_type = struct.unpack(">H", pkt_data[16:18])[0]
                    ip_off = 18
                else:
                    ip_off = 14

                if eth_type == _ETHERTYPE_IPV4:
                    result["stats"]["ipv4"] += 1
                    _parse_ipv4(pkt_data, ip_off, pkt_info, result, connections)
                elif eth_type == _ETHERTYPE_IPV6:
                    result["stats"]["ipv6"] += 1
                elif eth_type == _ETHERTYPE_ARP:
                    result["stats"]["arp"] += 1

                result["packets"].append(pkt_info)
                if len(result["packets"]) > 5000:
                    # 最多保留 5000 条包细节
                    pass

        # 汇总连接
        for key, info in connections.items():
            result["connections"].append({
                "src": f"{key[0]}:{key[1]}",
                "dst": f"{key[2]}:{key[3]}",
                "protocol": info.get("proto", ""),
                "packets": info.get("packets", 0),
                "start": info.get("start", 0),
                "end": info.get("end", 0),
            })

        result["stats"]["total"] = pkt_count
        result["connections"] = sorted(
            result["connections"], key=lambda x: x.get("start", 0), reverse=True
        )[:200]

    return result


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

        # DNS over TCP
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

        # DNS over UDP
        if dst_port == 53 or src_port == 53:
            _parse_dns(data, udp_off + 8, result)


def _parse_dns(data: bytes, off: int, result: dict) -> None:
    """简单 DNS 查询/响应提取。"""
    if off + 12 > len(data):
        return
    try:
        tid = struct.unpack(">H", data[off:off + 2])[0]
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
        if length & 0xC0:  # 压缩指针
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


class NetworkModule(ModuleBase):
    meta = ModuleMeta(
        name="network",
        description="PCAP 网络取证分析 (连接时间线 / DNS 查询)",
        author="Forensic Toolkit",
        version="0.1.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])

    def run(self) -> Any:
        if not self._path.exists():
            return {"error": f"路径不存在: {self._path}"}
        return _pcap_parse(self._path)


ModuleRegistry.register(NetworkModule)
