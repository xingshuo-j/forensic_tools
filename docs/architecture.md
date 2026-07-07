# 跨平台取证工具集 — 架构设计文档 (v0.2.0)

## 1. 项目概要

| 项目 | 值 |
|------|-----|
| 版本 | 0.2.0 |
| 语言 | Python ≥ 3.11 |
| 外部依赖 | **零** (纯标准库) |
| 模块总数 | 11 |
| 核心框架 | 7 组件 |
| 单元测试 | 16 个 |
| 许可证 | MIT |

## 2. 架构分层

```
┌─────────────────────────────────────────────────────────┐
│  CLI 层 (argparse, 零外部依赖)                           │
│  disk | filesystem | carving | metadata | network        │
│  recovery | registry | strings | hash | hunt | memory   │
├─────────────────────────────────────────────────────────┤
│  模块层 — 11 个已注册模块                                │
│                                                          │
│  carving/    文件雕刻 (11 种 Magic Bytes 签名)           │
│  disk/       磁盘分区解析 (预留)                          │
│  filesystem/ 文件系统 stat 元数据分析                     │
│  hunt/       敏感信息搜索 + Luhn + 哈希                  │
│  memory/     进程枚举 / 网络连接 / 内存转储              │
│  metadata/   EXIF / Office XML / PDF 元数据             │
│  network/    PCAP 全栈解析 (IP/TCP/UDP/DNS)             │
│  recovery/   NTFS / ext4 / FAT / APFS 已删除恢复        │
│  registry/   Windows Registry Hive 离线解析              │
│  strings/    流式字符串提取 (无大小限制)                  │
│  timeline/   MAC 时间线 + TSK Bodyfile 格式              │
├─────────────────────────────────────────────────────────┤
│  核心层 (core/)                                          │
│  platform.py  平台抽象 (Linux/macOS/Windows)             │
│  evidence.py  证据链 (Chain of Custody, JSON Lines)     │
│  hashing.py   取证哈希 (MD5/SHA-1/SHA-256, 流式)        │
│  formatters.py统一输出 (table/json/csv)                  │
│  module_base.py模块注册与发现                             │
│  logging.py   结构化取证日志                              │
│  types.py     通用数据类型 (BlockDevice, ForensicError)  │
├─────────────────────────────────────────────────────────┤
│  工具层 (utils/)                                         │
│  hexdump / 时间戳转换 / binary helpers                   │
└─────────────────────────────────────────────────────────┘
```

## 3. 已实现模块清单

| 模块 | 版本 | CLI 命令 | 功能 |
|------|------|----------|------|
| filesystem | 0.1.0 | `ftk filesystem info <path>` | stat 元数据 |
| timeline | 0.2.0 | `ftk filesystem timeline <path> [--bodyfile]` | MAC 时间线 + TSK bodyfile |
| strings | 0.2.0 | `ftk strings dump [path] [--min-len N]` | 流式字符串提取 (无大小限制) |
| hunt | 0.2.0 | `ftk hunt secrets <path> [--patterns]` | 7 种敏感模式 + Luhn 校验 |
| hash | 0.1.0 | `ftk hash compute <path> [--algo]` | MD5/SHA-1/SHA-256 |
| carving | 0.1.0 | `ftk carving scan <path> [--types] [--extract]` | 11 种文件签名雕刻 |
| metadata | 0.1.0 | `ftk metadata extract <path>` | EXIF/Office/PDF 元数据 |
| network | 0.1.0 | `ftk network analyze <pcap>` | PCAP 解析 (IP/TCP/UDP/DNS) |
| recovery | 0.2.0 | `ftk recovery scan <device> [--fs-type]` | NTFS/ext4/FAT/APFS 已删除恢复 |
| registry | 0.1.0 | `ftk registry dump <hive>` | Windows Registry 解析 |
| memory | 0.1.0 | `ftk memory {processes\|connections\|dump}` | 进程枚举/网络连接/转储分析 |

## 4. 平台覆盖

| 功能 | Linux | macOS | Windows |
|------|-------|-------|---------|
| 块设备枚举 | /sys/block | diskutil | pywin32 |
| 文件系统分析 | ext4 | APFS | NTFS/FAT |
| 已删除恢复 | ext4 | (APFS) | NTFS/FAT |
| Registry 解析 | 离线 | 离线 | 离线 |
| 内存进程 | /proc | — | — |
| PCAP 网络 | ✅ | ✅ | ✅ |
| 哈希/字符串/时间线 | ✅ | ✅ | ✅ |
| 文件雕刻 | ✅ | ✅ | ✅ |

## 5. 外部依赖说明

核心功能 **零外部依赖**，仅以下可选功能需要安装额外包：

| 功能 | 依赖包 | 用途 |
|------|--------|------|
| Windows 设备枚举 | pywin32 | `\\.\PhysicalDriveN` 访问 |
| Evidence Packaging | libewf-python | E01 格式读写 |
| Evidence Packaging | pyaff | AFF 格式读写 |
| TUI 界面 | textual | 终端交互界面 |
