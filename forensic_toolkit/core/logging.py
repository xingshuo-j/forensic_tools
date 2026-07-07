"""
取证日志器 (ForensicLogger)
============================
提供统一的带时间戳日志输出，支持 verbose 级别控制。
区别于 Python logging —— 这里不做复杂的 handler 管理，
而是直接的函数调用，确保每条日志都格式化为取证可读。
"""

from __future__ import annotations
import sys
from datetime import datetime, timezone
from typing import TextIO


class ForensicLogger:
    """结构化取证日志。输出到 stderr，不污染 stdout (JSON 结果)。"""

    LEVELS: dict[str, int] = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}

    def __init__(self, verbose: bool = False, stream: TextIO | None = None) -> None:
        self._verbose = verbose
        self._stream: TextIO = stream or sys.stderr

    def _log(self, level: str, msg: str) -> None:
        if self.LEVELS.get(level, 1) < self.LEVELS.get("INFO", 1) and not self._verbose:
            return
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(f"[{ts}] [{level:5s}] {msg}", file=self._stream)

    def info(self, msg: str) -> None:
        self._log("INFO", msg)

    def warn(self, msg: str) -> None:
        self._log("WARN", msg)

    def error(self, msg: str) -> None:
        self._log("ERROR", msg)

    def debug(self, msg: str) -> None:
        self._log("DEBUG", msg)
