# Forensic Toolkit (FTK)

跨平台数字取证工具集 — 纯 Python 标准库，零外部依赖。

FTK 提供图形化桌面界面，覆盖磁盘分析、文件雕刻、元数据提取、PCAP 网络解析、已删除文件恢复、Windows 注册表离线解析、内存分析等场景。所有核心功能无需安装任何第三方包即可使用。

## 安装

需要 Python >= 3.11。

```bash
git clone https://github.com/xingshuo-j/forensic_tools
cd forensic_toolkit
pip install -e .
```

## 启动

```bash
ftk-gui
```

首次启动后自动进入仪表盘，点击卡片即可进入对应的取证模块。

## 界面速览

界面分为三个区域：

- **顶栏** — 切换浅色/深色主题、折叠侧栏、关于、退出
- **侧栏** — 按分组组织的模块导航（概览 / 系统分析 / 文件分析 / 网络分析 / 数据恢复 / 工具）
- **主区域** — 当前选中模块的操作面板，包含输入表单和结果视图

### 快捷键

| 快捷键 | 功能 |
| --- | --- |
| `Ctrl + Q` | 退出程序 |
| `Ctrl + D` | 切换浅色 / 深色主题 |
| `Ctrl + B` | 折叠 / 展开侧栏 |
| `Ctrl + N` / `Ctrl + P` | 切换到下一个 / 上一个面板 |
| `Ctrl + E` | 返回仪表盘 |

### 主题

支持浅色和深色双主题，通过顶栏按钮或 `Ctrl + D` 一键切换。UI 采用多色系配色（Teal / Purple / Orange / Cyan / Rose），卡片具有悬停上浮、点击涟漪等微动效。

## 功能模块

打开 `ftk-gui` 后，侧栏和仪表盘均列出以下 16 个面板：

### 概览

**仪表盘** — 9 张彩色功能卡片，点击直接跳转到对应模块。同时提供一键枚举块设备功能。

### 系统分析

**磁盘取证** — 枚举物理磁盘设备详情，支持块设备路径或磁盘映像文件（ISO / IMG / VMDK / E01 等）。自动解析 MBR / GPT 分区表。

**分区解析** — 根据设备路径或磁盘映像文件解析分区表结构，展示各分区的类型、起始 LBA、扇区数等信息。

**内存分析** — 进程枚举、网络连接查看、内存转储分析。

**注册表解析** — 加载 Windows Registry Hive 文件（SAM / SYSTEM / SOFTWARE 等），离线解析注册表键值。

### 文件分析

**文件系统** — 获取任意路径的文件系统元数据；生成 MAC 时间线并支持导出 TSK Bodyfile 格式。

**字符串提取** — 从二进制文件中流式提取可打印字符串，支持设置最小长度和最大结果数，无文件大小限制。

**哈希校验** — 计算文件 MD5 / SHA-1 / SHA-256 哈希值，支持同时输出三种算法。

**敏感搜索** — 内置 7 种敏感信息模式（API 密钥 / 邮箱 / 信用卡号等），支持 Luhn 算法校验信用卡有效性。

**元数据提取** — 提取照片 EXIF、Office Open XML（docx / xlsx）、PDF 文档元数据。

**文件雕刻** — 基于 11 种 Magic Bytes 文件签名扫描磁盘映像，支持 JPEG / PNG / PDF / ZIP / GZIP / RAR / 7z / ELF / PE / SQLite / MP4。可选择 dry-run 模式先预览再实际提取。

### 网络分析

**网络取证** — 解析 PCAP / PCAPNG 抓包文件，统计 IP / TCP / UDP / DNS 流量信息。

### 数据恢复

**数据恢复** — 扫描已删除文件，支持 NTFS / ext4 / FAT / APFS 文件系统（需要 root / 管理员权限）。

**证据打包** — 生成符合取证标准的 E01 / AFF 证据映像文件（需要安装对应的可选依赖）。

### 工具

**操作日志** — 实时记录面板切换和操作过程，支持导出为文本日志文件。

**系统设置** — 配置默认输出目录、默认哈希算法、默认字符串最小长度、默认时间线深度等参数，支持持久化保存。

## 可选依赖

GUI 和核心取证功能均基于 Python 标准库，零外部依赖。仅在以下场景需要安装额外包：

| 功能 | 依赖包 | 用途 |
| --- | --- | --- |
| E01 证据包读写 | `libewf-python` | E01 格式证据映像 |
| AFF 证据包读写 | `pyaff` | AFF 格式证据映像 |

> Windows 块设备枚举需要 `pywin32`，但通常情况下可改用 [WSL](https://learn.microsoft.com/zh-cn/windows/wsl/) 运行。

## 命令行接口

FTK 同时提供 CLI 工具 `ftk`，面向自动化脚本和批处理场景：

```bash
ftk list-modules          # 列出所有模块
ftk disk list             # 枚举块设备
ftk network analyze capture.pcapng
ftk carving scan disk.img --types jpeg,pdf --extract
ftk hash compute evidence.img --algo sha256 --output-format json
```

详细命令参考可通过 `ftk --help` 查看。CLI 支持三种输出格式：`table`（默认）/ `json` / `csv`。

## 项目结构

```
forensic_toolkit/
├── cli/          # argparse CLI 入口
├── core/         # 核心框架（平台抽象、证据链、哈希、格式化）
├── gui/          # Tkinter 图形界面（主题、动画、组件库）
├── modules/      # 11 个取证模块
│   ├── carving/      # 文件雕刻
│   ├── disk/         # 磁盘/分区解析
│   ├── filesystem/   # 文件系统元数据
│   ├── hunt/         # 敏感信息搜索 + 哈希
│   ├── memory/       # 内存分析
│   ├── metadata/     # 元数据提取
│   ├── network/      # PCAP 网络分析
│   ├── recovery/     # 已删除恢复
│   ├── registry/     # 注册表解析
│   ├── strings/      # 字符串提取
│   └── timeline/     # MAC 时间线
├── utils/        # hexdump / 时间戳 / 二进制工具
├── bin/          # 辅助脚本
├── docs/         # 架构文档
├── examples/     # 使用示例
└── tests/        # 单元测试
```

## 许可

MIT License — 详见 [LICENSE](LICENSE)。
