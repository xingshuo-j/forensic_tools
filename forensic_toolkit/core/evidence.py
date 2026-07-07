"""
证据链管理 (Chain of Custody)
===============================
记录每次取证操作的时间、操作者、输入输出哈希、处理摘要。
输出为 JSON Lines 日志文件，可追溯、可审计。
"""

from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class ChainOfCustodyEntry:
    """单条证据链记录。"""

    def __init__(
        self,
        action: str,
        operator: str = "",
        source: str = "",
        source_hash: str = "",
        result_hash: str = "",
        notes: str = "",
    ) -> None:
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.action = action
        self.operator = operator or self._default_operator()
        self.source = source
        self.source_hash = source_hash
        self.result_hash = result_hash
        self.notes = notes

    @staticmethod
    def _default_operator() -> str:
        import getpass
        return getpass.getuser()

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "operator": self.operator,
            "source": self.source,
            "source_hash": self.source_hash,
            "result_hash": self.result_hash,
            "notes": self.notes,
        }

    def __repr__(self) -> str:
        return f"[{self.timestamp}] {self.action} by {self.operator}"


class EvidenceSession:
    """一次取证会话，管理证据链日志和输出目录。"""

    def __init__(self, output_dir: str | Path, case_name: str = "") -> None:
        self.case_name = case_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[ChainOfCustodyEntry] = []
        self._session_id = hashlib.sha256(
            datetime.now(timezone.utc).isoformat().encode()
        ).hexdigest()[:16]

        self.log("session.start", notes=f"Case: {case_name or 'unnamed'}")

    @property
    def session_id(self) -> str:
        return self._session_id

    def log(
        self,
        action: str,
        source: str = "",
        source_hash: str = "",
        result_hash: str = "",
        notes: str = "",
    ) -> ChainOfCustodyEntry:
        entry = ChainOfCustodyEntry(
            action=action,
            source=source,
            source_hash=source_hash,
            result_hash=result_hash,
            notes=notes,
        )
        self._entries.append(entry)
        self._append_to_logfile(entry)
        return entry

    def _append_to_logfile(self, entry: ChainOfCustodyEntry) -> None:
        log_path = self.output_dir / f"coc_{self._session_id}.jsonl"
        with open(log_path, "a") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def close(self) -> None:
        self.log("session.end", notes=f"共 {len(self._entries)} 条记录")
        log_path = self.output_dir / f"coc_{self._session_id}.jsonl"
        print(f"[证据链] 日志已保存: {log_path}")

    def __enter__(self) -> EvidenceSession:
        return self

    def __exit__(self, *args) -> None:
        self.close()
