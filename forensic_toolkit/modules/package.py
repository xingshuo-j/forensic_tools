"""
证据打包模块 (Evidence Packaging) — 外部依赖提示
====================================================
功能: 输出 E01 (Expert Witness Format) 和 AFF (Advanced Forensic Format) 标准证据映像文件。

依赖:
  - E01: 需要 libewf (libewf-python)
  - AFF: 需要 afflib (pyaff)

安装:
  pip install libewf-python   # E01 读写
  pip install pyaff            # AFF 读写

使用方式 (安装依赖后):
  from forensic_toolkit.modules.package import pack_to_e01
  pack_to_e01("/dev/sda", "/evidence/case001.E01", "case-001", "operator_name")

待实现:
  - E01 分段写入 (每段 2 GiB)
  - AFF 加密支持
  - 完整性校验 (MD5/SHA-1 embedded)
  - 元数据嵌入 (case number, examiner, description)
"""

