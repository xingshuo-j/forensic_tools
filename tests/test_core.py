"""核心层 + 新模块单元测试"""

import json, tempfile, os, unittest
from pathlib import Path

from forensic_toolkit.core.evidence import EvidenceSession, ChainOfCustodyEntry
from forensic_toolkit.core.hashing import Hasher
from forensic_toolkit.core.formatters import JsonFormatter, CsvFormatter, TableFormatter
from forensic_toolkit.core.module_base import ModuleMeta, ModuleRegistry, ModuleBase
from forensic_toolkit.core.types import BlockDevice


class TestChainOfCustody(unittest.TestCase):
    def test_entry_creation(self):
        entry = ChainOfCustodyEntry(action="test.run", operator="tester", source="/dev/sda")
        self.assertEqual(entry.action, "test.run")
        self.assertIsNotNone(entry.timestamp)

    def test_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = EvidenceSession(tmp, case_name="test")
            session.log("test.op", notes="单元测试")
            session.close()
            log_files = list(Path(tmp).glob("coc_*.jsonl"))
            self.assertEqual(len(log_files), 1)
            lines = log_files[0].read_text().strip().split("\n")
            self.assertGreaterEqual(len(lines), 2)

    def test_session_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            with EvidenceSession(tmp) as session:
                session.log("test.action")


class TestHashing(unittest.TestCase):
    def _tmpfile(self, data: bytes) -> str:
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as f: f.write(data)
        return path

    def test_file_hash(self):
        path = self._tmpfile(b"hello forensic world")
        try:
            h = Hasher.file_hash(path, "sha256")
            self.assertEqual(len(h), 64)
            self.assertTrue(Hasher.verify(path, h))
        finally: os.unlink(path)

    def test_all_hashes(self):
        path = self._tmpfile(b"data")
        try:
            result = Hasher.all_hashes(path)
            self.assertIn("sha-256", result)
            self.assertEqual(len(result["sha-256"]), 64)
        finally: os.unlink(path)


class TestFormatters(unittest.TestCase):
    def test_json(self):
        out = JsonFormatter().format({"a": 1})
        self.assertIn('"a"', out)
    def test_csv(self):
        out = CsvFormatter().format([{"x": 1}])
        self.assertIn("x", out)
    def test_table(self):
        out = TableFormatter().format([{"n": "alice"}])
        self.assertIn("alice", out)
    def test_empty(self):
        self.assertEqual(TableFormatter().format([]), "(empty)")


class TestModuleBase(unittest.TestCase):
    def test_register(self):
        class M(ModuleBase):
            meta = ModuleMeta(name="ut_test", description="x")
            def run(self): return {"ok": True}
        ModuleRegistry.register(M)
        self.assertIn("ut_test", ModuleRegistry.names())
        self.assertEqual(ModuleRegistry.get("ut_test"), M)
        self.assertEqual(M().run()["ok"], True)


class TestUtils(unittest.TestCase):
    def test_hexdump(self):
        from forensic_toolkit.utils import hexdump
        out = hexdump(b"ABC", length=4)
        self.assertIn("41", out)
        self.assertIn("ABC", out)
    def test_timestamp(self):
        from forensic_toolkit.utils import unix_to_iso, strip_null
        self.assertIn("2023", unix_to_iso(1700000000))
        self.assertEqual(strip_null("ab\x00c"), "abc")
    def test_binary(self):
        from forensic_toolkit.utils import find_bytes, align_up
        self.assertEqual(find_bytes(b"\x00\x01\x02\x01\x00", b"\x01"), [1, 3])
        self.assertEqual(align_up(13, 8), 16)


class TestLuhn(unittest.TestCase):
    def test_luhn_valid(self):
        from forensic_toolkit.modules.hunt import _luhn_check
        self.assertTrue(_luhn_check("4111111111111111"))  # Visa test
        self.assertTrue(_luhn_check("5555555555554444"))  # MC test
    def test_luhn_invalid(self):
        from forensic_toolkit.modules.hunt import _luhn_check
        self.assertFalse(_luhn_check("1234567890123456"))
        self.assertFalse(_luhn_check(""))


class TestStreamingStrings(unittest.TestCase):
    def test_stream_strings(self):
        from forensic_toolkit.modules.strings import StringsModule
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as f:
            f.write(b"hello\x00world\x00this_is_a_test_string_here\x00")
        try:
            m = StringsModule(path=path, min_length=4)
            result = m.run()
            self.assertGreaterEqual(result["strings_found"], 1)
        finally: os.unlink(path)


if __name__ == "__main__":
    unittest.main()
