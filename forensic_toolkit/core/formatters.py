"""
输出格式化器 (Output Formatting)
==================================
所有模块的结果统一通过 formatter 输出，支持 table / json / csv。

使用方式：
    formatter = TableFormatter()
    formatter.emit([{"path": "/etc/passwd", "size": 1024}, ...])

扩展：实现 OutputFormatter 接口即可添加新的输出格式。
"""

from __future__ import annotations
import csv
import json
import sys
import io
from abc import ABC, abstractmethod
from typing import Any, TextIO


class OutputFormatter(ABC):
    """输出格式化器接口。"""

    name: str = ""

    @abstractmethod
    def format(self, data: Any) -> str:
        ...

    def emit(self, data: Any, stream: TextIO | None = None) -> None:
        out = self.format(data)
        (stream or sys.stdout).write(out)
        if not out.endswith("\n"):
            (stream or sys.stdout).write("\n")


class JsonFormatter(OutputFormatter):
    name = "json"

    def format(self, data: Any) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)


class CsvFormatter(OutputFormatter):
    name = "csv"

    def format(self, data: Any) -> str:
        if not data:
            return ""
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return str(data)
        if not data:
            return ""

        buf = io.StringIO()
        if isinstance(data[0], dict):
            writer = csv.DictWriter(buf, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        else:
            writer = csv.writer(buf)
            for row in data:
                writer.writerow([row] if not isinstance(row, (list, tuple)) else row)
        return buf.getvalue()


class TableFormatter(OutputFormatter):
    name = "table"

    def format(self, data: Any) -> str:
        if not data:
            return "(empty)"
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return str(data)
        if not data:
            return "(empty)"

        # 提取表头
        if isinstance(data[0], dict):
            headers = list(data[0].keys())
            rows = [[str(r.get(h, "")) for h in headers] for r in data]
        else:
            headers = []
            rows = [[str(item)] for item in data]

        # 计算列宽
        col_widths = [len(h) for h in headers] if headers else [10]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(cell))

        lines: list[str] = []
        if headers:
            sep = "+".join("-" * (w + 2) for w in col_widths)
            lines.append(f"+{sep}+")
            header_row = "| " + " | ".join(
                h.ljust(w) for h, w in zip(headers, col_widths)
            ) + " |"
            lines.append(header_row)
            lines.append(f"+{sep}+")
        for row in rows:
            padded = [cell.ljust(w) for cell, w in zip(row, col_widths)]
            lines.append(f"| {' | '.join(padded)} |")
        if headers:
            lines.append(f"+{sep}+")
        return "\n".join(lines)


_FORMATTER_MAP: dict[str, type[OutputFormatter]] = {
    "json": JsonFormatter,
    "csv": CsvFormatter,
    "table": TableFormatter,
}


def get_formatter(name: str = "table") -> OutputFormatter:
    cls = _FORMATTER_MAP.get(name.lower())
    if cls is None:
        raise ValueError(f"不支持的输出格式: {name}，可选: {list(_FORMATTER_MAP.keys())}")
    return cls()
