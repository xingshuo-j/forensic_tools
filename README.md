# Forensic Toolkit (FTK)

跨平台数字取证工具集 — 纯 Python 标准库，零外部依赖。

## 概览

FTK 是一个面向数字取证的命令行工具集，覆盖磁盘分析、文件雕刻、元数据提取、PCAP 网络解析、已删除文件恢复、Windows Registry 离线解析、内存分析等场景。

核心功能完全基于 Python 标准库实现，**无需安装任何第三方依赖**。仅在 Windows 块设备枚举、E01/AFF 证据包读写、TUI 交互界面等可选场景下才需要额外的包。

## 功能模块

| 模块 | CLI 命令 | 说明 |
| --- | --- | --- |
| disk | `ftk disk list / info / analyze` | 块设备枚举与 MBR/GPT 分区解析 |
| filesystem | `ftk filesystem info <path>` | 文件系统 stat 元数据分析 |
| timeline | `ftk filesystem timeline <path> [--bodyfile]` | MAC 时间线 + TSK Bodyfile 格式 |
| carving | `ftk carving scan <path> [--extract]` | 基于 11 种 Magic Bytes 签名的文件雕刻 |
| metadata | `ftk metadata extract <path>` | EXIF / Office XML / PDF 元数据提取 |
| network | `ftk network analyze <pcap>` | PCAP/PCAPNG 全栈解析（IP/TCP/UDP/DNS） |
| recovery | `ftk recovery scan <device> [--fs-type]` | 已删除文件恢复（NTFS/ext4/FAT/APFS） |
| registry | `ftk registry dump <hive>` | Windows Registry Hive 离线解析 |
| strings | `ftk strings dump [path] [--min-len N]` | 流式可打印字符串提取（无文件大小限制） |
| hash | `ftk hash compute <path> [--algo]` | 取证哈希（MD5/SHA-1/SHA-256） |
| hunt | `ftk hunt secrets <path> [--patterns]` | 敏感信息搜索 + Luhn 校验 |
| memory | `ftk memory {processes\|connections\|dump}` | 进程枚举 / 网络连接 / 内存转储分析 |

## 安装

要求 Python >= 3.11。

```bash
git clone https://github.com/xingshuo-j/forensic_tools
cd forensic_toolkit
pip install -e .
```

安装后提供两个命令：

- `ftk` — 命令行工具
- `ftk-gui` — 图形界面（需要 `textual` 包）

## 快速开始

```bash
# 列出所有可用模块
ftk list-modules

# 枚举块设备
ftk disk list

# 分析 PCAP 网络包
ftk network analyze capture.pcapng

# 扫描已删除文件（NTFS 分区）
ftk recovery scan /dev/sdb1 --fs-type ntfs

# 文件雕刻（实际提取 JPEG 和 PDF）
ftk carving scan disk.img --types jpeg,pdf --extract

# 提取文件元数据
ftk metadata extract suspicious.docx

# 哈希计算
ftk hash compute evidence.img --algo sha256

# 敏感信息搜索
ftk hunt secrets dump.txt --patterns all

# 输出为 JSON 格式
ftk filesystem info /home --output-format json
```

## 输出格式

CLI 支持三种输出格式，通过 `--output-format` 指定：

- `table` — 终端表格（默认）
- `json` — JSON 结构化输出，便于管道处理
- `csv` — CSV 格式，适合外部工具导入

## 平台支持

| 功能 | Linux | macOS | Windows |
| --- | :-: | :-: | :-: |
| 块设备枚举 | Y | Y | Y（需 pywin32） |
| 文件系统分析 | ext4 | APFS | NTFS/FAT |
| 已删除恢复 | ext4 | APFS | NTFS/FAT |
| Registry 解析 | 离线 | 离线 | 离线 |
| 内存进程 | Y（/proc） | — | — |
| PCAP 网络 | Y | Y | Y |
| 哈希 / 字符串 / 时间线 | Y | Y | Y |
| 文件雕刻 | Y | Y | Y |

## 项目结构

```
forensic_toolkit/
├── cli/          # argparse CLI 入口
├── core/         # 核心框架（平台抽象、证据链、哈希、格式化）
├── modules/      # 11 个取证模块
│   ├── carving/      # 文件雕刻
│   ├── disk/         # 磁盘/分区解析
│   ├── filesystem/   # 文件系统元数据
│   ├── hunt/         # 敏感信息搜索 + 哈希
│   ├── memory/       # 内存分析
│   ├── metadata/     # 元数据提取
│   ├── network/      # PCAP 网络分析
│   ├── recovery/     # 已删除恢复
│   ├── registry/     # Registry 解析
│   ├── strings/      # 字符串提取
│   └── timeline/     # MAC 时间线
├── gui/          # Textual TUI 界面（可选）
├── utils/        # hexdump / 时间戳 / 二进制工具
├── bin/          # 辅助脚本
├── docs/         # 架构文档
├── examples/     # 使用示例
└── tests/        # 单元测试（16 个）
```

## 可选依赖

| 功能 | 依赖包 | 说明 |
| --- | --- | --- |
| Windows 设备枚举 | `pywin32` | 访问 `\\.\PhysicalDriveN` |
| E01 证据包 | `libewf-python` | E01 格式读写 |
| AFF 证据包 | `pyaff` | AFF 格式读写 |
| TUI 界面 | `textual` | `ftk-gui` 终端交互界面 |

## 许可

MIT License — 详见 [LICENSE](LICENSE)。
