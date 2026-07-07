"""
哈希工具 — 取证级哈希计算。

支持 MD5 / SHA-1 / SHA-256，流式读取大文件，
统一返回 Hex 字符串。
"""

from __future__ import annotations
import hashlib
from typing import IO

_CHUNK_SIZE = 1 * 1024 * 1024  # 1 MiB


class Hasher:
    """取证哈希计算器。"""

    @staticmethod
    def file_hash(path: str, algorithm: str = "sha256") -> str:
        """计算文件的哈希值。"""
        h = hashlib.new(algorithm)
        with open(path, "rb") as f:
            while True:
                buf = f.read(_CHUNK_SIZE)
                if not buf:
                    break
                h.update(buf)
        return h.hexdigest()

    @staticmethod
    def stream_hash(stream: IO[bytes], algorithm: str = "sha256") -> str:
        """从流式计算哈希。"""
        h = hashlib.new(algorithm)
        while True:
            buf = stream.read(_CHUNK_SIZE)
            if not buf:
                break
            h.update(buf)
        return h.hexdigest()

    @staticmethod
    def verify(path: str, expected: str, algorithm: str = "sha256") -> bool:
        """验证文件哈希是否匹配。"""
        actual = Hasher.file_hash(path, algorithm)
        return actual.lower() == expected.lower()

    @staticmethod
    def all_hashes(path: str) -> dict[str, str]:
        """一次性计算 MD5 + SHA-1 + SHA-256。"""
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                buf = f.read(_CHUNK_SIZE)
                if not buf:
                    break
                md5.update(buf)
                sha1.update(buf)
                sha256.update(buf)
        return {
            "md5": md5.hexdigest(),
            "sha-1": sha1.hexdigest(),
            "sha-256": sha256.hexdigest(),
        }
