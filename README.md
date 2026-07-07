# Forensic Toolkit — 跨平台数字取证工具集

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)]()
[![License MIT](https://img.shields.io/badge/License-MIT-green)]()
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen)]()
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

**Forensic Toolkit (ftk)** 是一个用**纯 Python 标准库**编写的模块化数字取证工具集，零外部依赖，支持 Linux / macOS / Windows 三大平台。提供 GUI 桌面应用和 CLI 命令行两种操作方式，覆盖 11 个取证场景。

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

**核心亮点**: 零外部依赖 · 11 个取证模块 · GUI + CLI 双模式 · 内置证据链 · 16 个单元测试

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

# GUI 桌面模式
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

启动图形化界面：

```bash
# 通过 bin/ftk（任何目录下均可）
python3 bin/ftk gui

# 通过 PATH 方式
ftk gui

# 通过 pip 安装后
ftk-gui
```

### 主界面布局

```
+---------------------------------------------------+
|  Forensic Toolkit v0.2.0              [Menu]      |
+----------+----------------------------------------+
|  Sidebar |   Tool Panel                           |
|          |                                        |
|  Dash    |   [Form inputs / parameter area]       |
|  Disk    |                                        |
|  FS      |                                        |
|  Carving |                                        |
|  Strings |                                        |
|  Hash    |                                        |
|  Hunt    |   [Results table with export]          |
|  Meta    |                                        |
|  Network |                                        |
|  Memory  |                                        |
|  Reg     |                                        |
|  Recov   |                                        |
+----------+----------------------------------------+
|  Status: Ready    Platform: linux    v0.2.0       |
+---------------------------------------------------+
```

### 工作流程

1. **左侧导航栏** — 按功能分类选择工具面板（Dashboard、磁盘、文件系统、雕刻等共 12 个面板）
2. **面板表单区** — 每个工具提供路径选择器、参数控件（下拉框、复选框、数值输入）
3. **Run 按钮** — 点击后任务在后台线程执行，不影响界面响应
4. **结果表格** — 结构化数据显示，支持：
   - 列头点击排序
   - 选中行复制 / 全部复制（JSON 格式，直接入剪贴板）
   - 导出 JSON / CSV 文件
5. **状态栏** — 显示当前操作状态和平台信息

### 各面板说明

| 面板 | 输入 | 输出 |
|------|------|------|
| **Dashboard** | 无 | 平台信息、已注册模块列表、快捷操作 |
| **Disk** | 设备路径 | 块设备列表、设备详情（型号/序列号/容量） |
| **Filesystem** | 文件/目录路径、扫描深度、bodyfile 开关 | stat 元数据、MAC 时间线 |
| **Carving** | 源文件/设备、输出目录、文件类型、提取开关 | 发现的签名列表，可提取到目录 |
| **Strings** | 文件路径、最小长度、最大结果数 | ASCII/UTF-16LE 字符串及偏移量 |
| **Hash** | 文件路径、算法选择 | 文件哈希值 |
| **Hunt** | 文件路径、模式选择 | 匹配的敏感信息（API 密钥/邮箱/信用卡等） |
| **Metadata** | 文件路径 | EXIF / Office / PDF 元数据 |
| **Network** | PCAP 文件 | 连接时间线 / DNS 查询 / 统计（三标签页） |
| **Memory** | 模式选择 / dump 文件 | 进程列表 / 网络连接 / 内存扫描结果 |
| **Registry** | Hive 文件 | 键值树及名称、类型、数据 |
| **Recovery** | 设备路径、文件系统类型 | 已删除文件记录列表 |

---

## CLI 使用指南

### 快速上手

```bash
# 查看所有命令
ftk --help

# 列出已注册模块
ftk list-modules

# 示例：计算文件哈希
ftk hash compute --algo all /etc/hosts

# 示例：提取可打印字符串
ftk strings dump /path/to/file --min-len 6 --max-results 1000

# 示例：扫描磁盘镜像中的文件签名
ftk carving scan /path/to/disk.img --types jpeg,pdf --extract --output ./carved

# JSON 格式输出（方便脚本处理）
ftk --output-format json disk list
```

### 全局选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--output-format` | `table` | 输出格式：`table` / `json` / `csv` |
| `-o, --output-dir` | `./ftk_output` | 证据链日志和输出文件目录 |
| `-v, --verbose` | 关闭 | 输出详细 DEBUG 日志 |
| `--version` | — | 打印版本号 |

### 命令参考

#### 磁盘取证

```bash
ftk disk list                                 # 枚举所有块设备
ftk disk info /dev/sda                        # 查看设备详情
```

#### 文件系统分析

```bash
ftk filesystem info /etc/passwd               # stat 元数据
ftk filesystem timeline /var/log --depth 5    # MAC 时间线
ftk filesystem timeline /var/log --bodyfile   # TSK bodyfile 格式
```

#### 文件雕刻

```bash
ftk carving scan disk.img                     # 扫描全部类型 (dry-run)
ftk carving scan disk.img --types jpeg,pdf --extract --output ./carved
# 支持: JPEG, PDF, ZIP, PNG, GIF, ELF, RIFF, XML, HTML, BMP
```

#### 元数据提取

```bash
ftk metadata extract photo.jpg                # EXIF (相机/GPS)
ftk metadata extract doc.docx                 # Office 文档属性
ftk metadata extract report.pdf               # PDF /Info 字典
```

#### 网络取证

```bash
ftk network analyze capture.pcap              # 连接时间线 + DNS 查询
```

#### 删除文件恢复

```bash
sudo ftk recovery scan /dev/sda1              # 自动检测 FS
sudo ftk recovery scan /dev/sdc1 --fs-type ext4
sudo ftk recovery scan /dev/disk0s1 --fs-type apfs
# 支持: ntfs ($MFT), ext4 (inode), fat (0xE5), apfs (NXSB + B-tree)
```

#### Registry 解析

```bash
ftk registry dump /mnt/SOFTWARE               # 离线解析 Hive 文件
ftk registry dump /mnt/NTUSER.DAT
```

#### 字符串提取

```bash
ftk strings dump /path/to/file --min-len 6    # 流式, 无大小限制
cat disk.img | ftk strings dump -             # 从管道读取
```

#### 哈希校验

```bash
ftk hash compute /path/to/file                # SHA-256
ftk hash compute --algo md5 /path/to/file     # MD5
ftk hash compute --algo all /path/to/file     # MD5 + SHA-1 + SHA-256
```

#### 敏感信息搜索

```bash
ftk hunt secrets /path/to/file                           # 全部模式
ftk hunt secrets --patterns email /path/to/file          # 仅邮箱
ftk hunt secrets --patterns api_key /path/to/file        # 仅 API 密钥
# 模式: api_key / email / credit_card / ip_address / bitcoin / ethereum / private_key
```

#### 内存分析

```bash
ftk memory processes                           # 进程枚举 (Linux)
ftk memory connections                         # 网络连接 (Linux)
ftk memory dump /path/to/memdump.bin           # 内存转储分析
```

---

## 输出格式

所有命令共享统一输出格式，通过 `--output-format` 控制：

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
|  12 个面板 · 后台线程 · 结果表格 · 导出 JSON/CSV          |
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
|  platform.py    平台抽象 (Linux/macOS/Windows)            |
|  evidence.py    证据链 (Chain of Custody, JSON Lines)    |
|  hashing.py     取证哈希 (MD5/SHA-1/SHA-256)             |
|  formatters.py  统一输出 (table/json/csv)                 |
|  module_base.py 模块注册与发现 (ModuleBase + Registry)    |
|  logging.py     结构化取证日志                             |
|  types.py       通用类型 (BlockDevice, ForensicError)     |
+-----------------------------------------------------------+
```

**设计原则**:
- 所有 OS 差异集中在 `core/platform.py`，上层不依赖 `os.name` / `sys.platform`
- 每个模块继承 `ModuleBase`，通过 `ModuleRegistry` 自注册，CLI 和 GUI 均可自动发现
- 每次操作可写入 `EvidenceSession`，生成 JSON Lines 日志用于审计追溯
- GUI 中耗时操作自动在后台线程执行，界面保持响应

---

## Python API 用法

```python
from forensic_toolkit.core.hashing import Hasher
from forensic_toolkit.core.evidence import EvidenceSession
from forensic_toolkit.core.platform import Platform

# 计算哈希
h = Hasher.file_hash("/path/to/file", "sha256")
all_hashes = Hasher.all_hashes("/path/to/file")
# -> {"md5": "...", "sha-1": "...", "sha-256": "..."}

# 证据链日志
with EvidenceSession("./output", case_name="case-001") as session:
    session.log("hash.compute", source="/path/to/file",
                source_hash=h, notes="计算文件哈希")

# 调用取证模块
from forensic_toolkit.core.module_base import ModuleRegistry
# 需要先导入模块触发注册
import forensic_toolkit.modules.strings
mod = ModuleRegistry.get("strings")(path="/path/to/file", min_length=6)
result = mod.run()
print(f"找到 {result['strings_found']} 个字符串")

# 平台信息
print(f"系统: {Platform.info.system}")          # linux | darwin | windows
print(f"管理员: {Platform.info.is_admin}")

for dev in Platform.list_block_devices():
    print(f"  {dev.path}: {dev.model}")
```

---

## 跨平台兼容性

| 功能 | Linux | macOS | Windows |
|------|-------|-------|---------|
| 块设备枚举 | `/sys/block` | `diskutil` | `\\.\PhysicalDriveN` |
| 权限检测 | `geteuid()` | `geteuid()` | `IsUserAnAdmin()` |
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
4. CLI 和 GUI 均会自动发现，无需额外注册

```python
from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry

class YourModule(ModuleBase):
    meta = ModuleMeta(name="your_mod", description="...", version="0.1.0")
    def run(self): return {"result": "ok"}

ModuleRegistry.register(YourModule)
```

### 添加 GUI 面板

1. 在 `forensic_toolkit/gui/panels.py` 中新建 `BasePanel` 子类
2. 调用 `register_panel(YourPanel)`
3. 导航栏和面板切换自动生效

---

## 项目文件

```
forensic_toolkit/
├── bin/ftk                       ← 可执行入口
├── pyproject.toml                 ← 项目配置 + 入口点
├── forensic_toolkit/
│   ├── cli/main.py               ← CLI (argparse)
│   ├── gui/                      ← GUI (Tkinter)
│   │   ├── app.py                ← 主窗口 + 导航
│   │   ├── panels.py             ← 12 个工具面板
│   │   └── widgets.py            ← 可复用控件
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
