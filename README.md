# Forensic Toolkit — 跨平台数字取证工具集

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)]()
[![License MIT](https://img.shields.io/badge/License-MIT-green)]()
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen)]()
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

**Forensic Toolkit (ftk)** 是一个用**纯 Python 标准库**编写的模块化数字取证工具集，零外部依赖，支持 Linux / macOS / Windows 三大平台。提供 GUI 桌面应用和 CLI 命令行两种操作方式，覆盖 11 个取证场景。GUI 界面默认为简体中文，采用深色侧边栏 + 浅色内容区的专业配色方案。

---

## 功能一览

| 功能 | CLI 命令 | 需要权限 |
|------|----------|---------|
| 磁盘取证 | `ftk disk list` / `disk info <dev>` | 推荐 root |
| 文件系统分析 | `ftk filesystem info <path>` | — |
| MAC 时间线 | `ftk filesystem timeline <path> [--bodyfile]` | — |
| 文件雕刻 | `ftk carving scan <path> [--extract]` | — |
| 元数据提取 | `ftk metadata extract <path>` | — |
| 网络取证 | `ftk network analyze <.pcap>` | — |
| 删除文件恢复 | `ftk recovery scan <device> [--fs-type]` | **需要 root** |
| Registry 解析 | `ftk registry dump <.hive>` | — |
| 字符串提取 | `ftk strings dump [path] [--min-len N]` | — |
| 哈希校验 | `ftk hash compute <path> [--algo ...]` | — |
| 敏感信息搜索 | `ftk hunt secrets <path> [--patterns ...]` | — |
| 内存分析 | `ftk memory processes / connections / dump <path>` | — |

**核心亮点**: 零外部依赖 · 11 个取证模块 · GUI + CLI 双模式 · 简体中文界面 · 内置证据链 · 16 个单元测试

---

## 下载与安装

项目基于纯 Python 标准库，零外部依赖。**绝大多数情况下你甚至不需要 pip install。**

首先获取代码：

```bash
git clone https://github.com/your-org/forensic_toolkit.git
cd forensic_toolkit
```

### 方式一：直接运行（推荐，零安装）

项目根目录下的 `bin/ftk` 是一个自包含入口脚本，自动解析路径，无需任何安装步骤：

```bash
# 命令行模式
python3 bin/ftk --help
python3 bin/ftk hash compute --algo sha256 /etc/hosts

# GUI 桌面模式（简体中文界面）
python3 bin/ftk gui
```

如果想要全局使用 `ftk` 命令（免前缀 `python3 bin/`）：

```bash
# 方案 A：加入 PATH（当前终端）
export PATH="$(pwd)/bin:$PATH"
ftk --version

# 方案 B：符号链接到系统路径（永久）
sudo ln -s "$(pwd)/bin/ftk" /usr/local/bin/ftk
ftk --version
```

### 方式二：pip 安装（通过虚拟环境）

如果希望在虚拟环境中安装，获得 `ftk` 和 `ftk-gui` 两个系统级命令：

```bash
# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 以可编辑模式安装（修改代码即时生效）
pip install -e .

# 现在可以直接使用
ftk --version
ftk-gui
```

> **常见错误**: 如果直接 `pip install -e .` 遇到 `externally-managed-environment` 报错，说明当前是系统级 Python 环境（PEP 668 保护策略）。改用上面的虚拟环境方式即可。**不建议**使用 `--break-system-packages`。

### 环境要求

- Python 3.11 或更高版本
- GUI 模式需要 Tkinter（绝大多数 Python 发行版自带；若缺失，Debian/Ubuntu 下 `sudo apt install python3-tk`）
- 部分磁盘操作需要 root / Administrator 权限

---

## GUI 使用指南

### 启动方式

```bash
python3 bin/ftk gui          # 通过 bin/ftk
ftk gui                       # 加入 PATH 后
ftk-gui                       # pip 安装后
```

GUI 默认语言为**简体中文**，界面采用**深色侧边栏（#1a1d23）+ 浅色内容区（#f0f2f5）**的双色配比，按钮以蓝色（#2563eb）为强调色，结果表格带有交替行底色提升可读性。

### 主界面布局

```
+---------------------------------------------------+
|  Forensic Toolkit      v0.2.0       [关于] [退出]  |
+----------+----------------------------------------+
| 侧边导航  |  工具面板                               |
|          |                                        |
| ⌖ 仪表盘 |   [表单区域：路径选择器、参数控件]      |
| ⬣ 磁盘   |                                        |
| ⬡ 文件   |                                        |
| ✂ 雕刻   |                                        |
| ≋ 字符串 |                                        |
| ⊙ 哈希   |                                        |
| ⊘ 搜索   |   [结果表格：排序/复制/导出]            |
| ⬤ 元数据 |                                        |
| ⬢ 网络   |                                        |
| ⬥ 内存   |                                        |
| ⬠ 注册表 |                                        |
| ⭮ 恢复   |                                        |
+----------+----------------------------------------+
|  就绪     输出: ./ftk_output     平台: linux  v0.2.0 |
+---------------------------------------------------+
```

### 工作流程

1. **左侧导航栏** — 12 个中文标签按钮，点击切换工具面板，当前活跃项以蓝色高亮
2. **面板表单区** — 每个工具提供路径选择器、参数控件（下拉框、复选框、数值输入）
3. **▶ 执行按钮** — 点击后任务在后台线程运行（带动画进度条），界面保持响应
4. **结果表格** — 结构化数据以交替行底色显示，支持列头排序、选定/全部复制（JSON 入剪贴板）、导出 JSON / CSV
5. **底部状态栏** — 实时显示操作状态、输出目录、平台信息

### 各面板中文名称

| 面板标识 | 中文名称 | 输入 | 输出 |
|----------|---------|------|------|
| Dashboard | **仪表盘** | 无 | 平台信息、已注册模块列表、快捷操作 |
| Disk | **磁盘取证** | 设备路径 | 块设备列表、设备详情（型号/序列号/容量） |
| Filesystem | **文件系统** | 文件/目录路径、扫描深度 | stat 元数据、MAC 时间线 |
| Carving | **文件雕刻** | 源文件/设备、输出目录、文件类型 | 发现的签名列表，可提取到目录 |
| Strings | **字符串提取** | 文件路径、最小长度、最大结果数 | ASCII/UTF-16LE 字符串及偏移量 |
| Hash | **哈希校验** | 文件路径、算法选择 | 文件哈希值 |
| Hunt | **敏感搜索** | 文件路径、模式选择 | 匹配的敏感信息（API 密钥/邮箱/信用卡等） |
| Metadata | **元数据提取** | 文件路径 | EXIF / Office / PDF 元数据 |
| Network | **网络取证** | PCAP 文件 | 连接时间线 / DNS 查询 / 统计（三标签页） |
| Memory | **内存分析** | 模式选择 / dump 文件 | 进程列表 / 网络连接 / 内存扫描结果 |
| Registry | **注册表解析** | Hive 文件 | 键值树及名称、类型、数据 |
| Recovery | **数据恢复** | 设备路径 + 文件系统类型 | 已删除文件记录列表 |

---

## CLI 使用指南

### 快速上手

```bash
ftk --help                                    # 查看所有命令
ftk list-modules                              # 列出已注册模块
ftk hash compute --algo all /etc/hosts        # 计算文件哈希
ftk strings dump /path/to/file --min-len 6    # 提取字符串
ftk carving scan disk.img --types jpeg,pdf --extract --output ./carved
ftk --output-format json disk list            # JSON 格式输出
```

### 全局选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--output-format` | `table` | 输出格式：`table` / `json` / `csv` |
| `-o, --output-dir` | `./ftk_output` | 证据链日志和输出文件目录 |
| `-v, --verbose` | 关闭 | 输出详细 DEBUG 日志 |

### 命令参考

```bash
# 磁盘取证
ftk disk list                            # 枚举所有块设备
ftk disk info /dev/sda                   # 查看设备详情

# 文件系统分析
ftk filesystem info /etc/passwd          # stat 元数据
ftk filesystem timeline /var/log --depth 5 --bodyfile

# 文件雕刻（支持 JPEG、PDF、ZIP、PNG、GIF、ELF 等 11 种签名）
ftk carving scan disk.img --types jpeg,pdf --extract --output ./carved

# 元数据提取（EXIF / Office / PDF）
ftk metadata extract photo.jpg

# 网络取证
ftk network analyze capture.pcap

# 删除文件恢复（需要 root）
sudo ftk recovery scan /dev/sda1 --fs-type ntfs

# Windows 注册表解析
ftk registry dump /mnt/SOFTWARE

# 字符串提取（流式，无文件大小限制）
ftk strings dump /path/to/file --min-len 6
cat disk.img | ftk strings dump -

# 哈希校验
ftk hash compute --algo all /path/to/file

# 敏感信息搜索
ftk hunt secrets /path/to/file --patterns email

# 内存分析（Linux）
ftk memory processes
ftk memory dump /path/to/memdump.bin
```

---

## 输出格式

所有命令共享统一输出格式：

```bash
ftk disk list                          # table（默认终端表格）
ftk --output-format json disk list     # JSON（脚本消费）
ftk --output-format csv disk list      # CSV（Excel / Splunk 导入）
```

---

## 架构

```
+-----------------------------------------------------------+
|  GUI 层  (Tkinter, 零依赖)                                |
|  12 个工具面板 · 后台线程 · 深色侧栏 · 中文界面            |
|  结果表格：排序/复制/导出 JSON-CSV · 交替行底色            |
+-----------------------------------------------------------+
|  CLI 层  (argparse, 零外部依赖)                           |
|  17 个子命令 · 全局 --output-format / -o / -v            |
+-----------------------------------------------------------+
|  模块层 — 11 个已注册模块                                  |
|  carving  | filesystem | hash | hunt | memory            |
|  metadata | network | recovery | registry | strings      |
|  timeline | disk (分区表)                                  |
+-----------------------------------------------------------+
|  核心层  (7 个组件, 纯标准库)                              |
|  platform.py    evidence.py    hashing.py                 |
|  formatters.py  module_base.py logging.py  types.py       |
+-----------------------------------------------------------+
```

---

## Python API 用法

```python
from forensic_toolkit.core.hashing import Hasher
from forensic_toolkit.core.evidence import EvidenceSession
from forensic_toolkit.core.platform import Platform
from forensic_toolkit.core.module_base import ModuleRegistry
import forensic_toolkit.modules.strings

# 计算哈希
h = Hasher.file_hash("/path/to/file", "sha256")

# 证据链日志
with EvidenceSession("./output", case_name="case-001") as session:
    session.log("hash.compute", source="/path/to/file", source_hash=h)

# 调用取证模块
mod = ModuleRegistry.get("strings")(path="/path/to/file", min_length=6)
result = mod.run()

# 平台信息
print(f"系统: {Platform.info.system}")
for dev in Platform.list_block_devices():
    print(f"  {dev.path}: {dev.model}")
```

---

## 跨平台兼容性

| 功能 | Linux | macOS | Windows |
|------|-------|-------|---------|
| 块设备枚举 | `/sys/block` | `diskutil` | `\\.\PhysicalDriveN` |
| 文件雕刻 | ✅ | ✅ | ✅ |
| 哈希 / 字符串 | ✅ | ✅ | ✅ |
| MAC 时间线 | ✅ | ✅ | ✅ |
| 元数据提取 | ✅ | ✅ | ✅ |
| PCAP 网络分析 | ✅ | ✅ | ✅ |
| 已删除文件恢复 | ext4 | APFS | NTFS + FAT |
| Registry 解析 | ✅ | ✅ | ✅ |
| 进程 / 连接枚举 | `/proc` | — | — |
| GUI 桌面应用 | ✅ (Tkinter) | ✅ (Tkinter) | ✅ (Tkinter) |

> Windows 设备枚举可选安装 `pywin32`。其余功能无需外部依赖。

---

## 测试与开发

### 运行测试

```bash
cd forensic_toolkit
python3 -m unittest tests.test_core -v
```

### 扩展新模块

1. 在 `modules/` 下创建 `your_module/__init__.py`
2. 继承 `ModuleBase`，设置 `ModuleMeta`，实现 `run()`
3. 调用 `ModuleRegistry.register(YourModule)`
4. CLI 和 GUI 均会自动发现

```python
from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry

class YourModule(ModuleBase):
    meta = ModuleMeta(name="your_mod", description="...", version="0.1.0")
    def run(self): return {"result": "ok"}

ModuleRegistry.register(YourModule)
```

### 添加 GUI 面板

1. 在 `forensic_toolkit/gui/panels.py` 中新建 `BasePanel` 子类
2. 设置 `TITLE` 类变量（英文标识），在 `PANEL_NAMES` 中映射中文名称和图标
3. 调用 `register_panel(YourPanel)`

---

## 项目文件

```
forensic_toolkit/
├── bin/ftk                       ← 可执行入口
├── pyproject.toml                 ← 项目配置 + 入口点
├── forensic_toolkit/
│   ├── cli/main.py               ← CLI (argparse)
│   ├── gui/                      ← GUI (Tkinter, 中文)
│   │   ├── app.py                ← 主窗口 + 深色侧栏导航
│   │   ├── panels.py             ← 12 个中文面板
│   │   └── widgets.py            ← 可复用控件（结果表格等）
│   ├── core/                     ← 核心层 (7 组件)
│   ├── modules/                  ← 取证模块 (11 个)
│   └── utils/                    ← 工具函数
├── tests/                        ← 单元测试
├── docs/architecture.md          ← 架构设计
├── show/                         ← 审计报告示例
└── README.md                     ← 本文件
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
