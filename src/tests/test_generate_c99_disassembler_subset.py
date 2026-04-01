from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src" / "scripts" / "generate_c99_disassembler_subset.py"
STYLE_CHECKER = ROOT / "src" / "scripts" / "check_c_style.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateC99DisassemblerSubsetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls._outdir = Path(cls._tmp.name)
        cls._generator = _load_module(SCRIPT, "src_test_generate_c99_disassembler_subset")
        cls._tables = cls._generator._emit_tables_include(
            cls._generator._load_forms(),
            cls._generator._load_kb(),
            cls._generator._load_subset_module(),
        )
        (cls._outdir / "m68k_disassembler_tables.inc").write_text(cls._tables, encoding="ascii")
        cls._checker = _load_module(STYLE_CHECKER, "src_test_generate_c99_disassembler_style_checker")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_generates_lookup_tables(self) -> None:
        self.assertIn("static const M68kDisasmBucket g_m68k_disasm_buckets[] = {", self._tables)
        self.assertIn("static const uint16_t g_m68k_disasm_bucket_candidates[] = {", self._tables)

    def test_uses_widened_form_set(self) -> None:
        self.assertIn("static const uint8_t g_m68k_disasm_operand_shapes[][4] = {", self._tables)
        self.assertIn("static const M68kAsmFormDef g_m68k_disasm_forms[", self._tables)

    def test_includes_concrete_coprocessor_condition_forms(self) -> None:
        self.assertIn('"cpbcc"', self._tables)
        self.assertIn('"cpdbcc"', self._tables)
        self.assertIn('"cptrapcc"', self._tables)

    def test_generated_tables_pass_style_checker(self) -> None:
        issues = self._checker.check_file(self._outdir / "m68k_disassembler_tables.inc", self._checker.DEFAULT_LINE_LENGTH)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
