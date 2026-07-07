"""
敏感信息搜索 + 哈希校验模块
=============================
HuntModule:  搜索文件/设备中的敏感模式
  - API 密钥 / Token
  - 电子邮件地址
  - 信用卡号 (含 Luhn 校验)
  - IP 地址 (内网/公网)
  - 加密货币钱包地址
  - 密码 / 私钥片段

HashModule:  计算文件哈希值
"""

from __future__ import annotations
import re
import hashlib
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


# ── Luhn 校验 ─────────────────────────────────────────

def _luhn_check(digits: str) -> bool:
    """Luhn 算法校验信用卡号。只保留数字字符。"""
    clean = re.sub(r"\D", "", digits)
    if len(clean) < 13 or len(clean) > 19:
        return False
    total = 0
    reverse = clean[::-1]
    for i, ch in enumerate(reverse):
        n = ord(ch) - 48
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


# ── 正则模式 ────────────────────────────────────────────

_PATTERNS: dict[str, tuple[str, re.Pattern]] = {
    "api_key": ("API 密钥", re.compile(
        r"(?:api[_-]?key|apikey|secret|token)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,64})['\"]?",
        re.IGNORECASE,
    )),
    "email": ("电子邮件", re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    )),
    "credit_card": ("信用卡号", re.compile(
        r"\b(?:\d[ -]*?){13,19}\b",
    )),
    "ip_address": ("IP 地址", re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    )),
    "bitcoin": ("比特币地址", re.compile(
        r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
    )),
    "ethereum": ("以太坊地址", re.compile(
        r"\b0x[a-fA-F0-9]{40}\b",
    )),
    "private_key": ("私钥片段", re.compile(
        r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
    )),
}


class HuntModule(ModuleBase):
    meta = ModuleMeta(
        name="hunt",
        description="搜索文件中的敏感信息（密钥、邮箱、信用卡等）",
        author="Forensic Toolkit",
        version="0.2.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])
        self._mode = self.params.get("patterns", "all")

    def run(self) -> Any:
        path = self._path
        if not path.exists():
            return {"error": f"路径不存在: {path}"}

        try:
            data = path.read_bytes()
        except Exception as e:
            return {"error": str(e)}

        text = data.decode("utf-8", errors="replace")
        results = []
        for key, (label, pattern) in _PATTERNS.items():
            if self._mode != "all" and key != self._mode:
                continue
            for m in pattern.finditer(text):
                match_text = m.group()[:80]
                # 信用卡号走 Luhn 校验
                if key == "credit_card" and not _luhn_check(match_text):
                    continue
                results.append({
                    "type": label,
                    "pattern": key,
                    "offset": m.start(),
                    "match": match_text,
                })

        return {
            "source": str(path.resolve()),
            "hits": len(results),
            "results": results[:200],
        }


class HashModule(ModuleBase):
    meta = ModuleMeta(
        name="hash",
        description="计算文件哈希值 (MD5 / SHA-1 / SHA-256)",
        author="Forensic Toolkit",
        version="0.1.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])
        self._algo = self.params.get("algorithm", "sha256")

    def run(self) -> Any:
        path = self._path
        if not path.exists():
            return {"error": f"路径不存在: {path}"}

        if self._algo == "all":
            return self._all_hashes(path)
        return self._single_hash(path, self._algo)

    @staticmethod
    def _single_hash(path: Path, algo: str) -> dict:
        h = hashlib.new(algo)
        with open(path, "rb") as f:
            while True:
                buf = f.read(64 * 1024)
                if not buf:
                    break
                h.update(buf)
        return {"file": str(path.resolve()), "algorithm": algo, "hash": h.hexdigest()}

    @staticmethod
    def _all_hashes(path: Path) -> dict:
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                buf = f.read(64 * 1024)
                if not buf:
                    break
                md5.update(buf)
                sha1.update(buf)
                sha256.update(buf)
        return {"file": str(path.resolve()), "md5": md5.hexdigest(),
                "sha-1": sha1.hexdigest(), "sha-256": sha256.hexdigest()}


ModuleRegistry.register(HuntModule)
ModuleRegistry.register(HashModule)
