from __future__ import annotations

import importlib.util
import os
import re
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
        cls._metadata = cls._generator._emit_metadata_header(cls._generator._load_forms())
        (cls._outdir / "m68k_disassembler_tables.h").write_text(cls._tables, encoding="ascii")
        (cls._outdir / "m68k_disassembler_metadata.h").write_text(cls._metadata, encoding="ascii")
        cls._checker = _load_module(STYLE_CHECKER, "src_test_generate_c99_disassembler_style_checker")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_generates_lookup_tables(self) -> None:
        self.assertIn("static const M68kDisasmBucket g_m68k_disasm_buckets[] = {", self._tables)
        self.assertIn("static const uint16_t g_m68k_disasm_bucket_candidates[] = {", self._tables)

    def test_uses_widened_form_set(self) -> None:
        self.assertIn(
            "static const uint8_t g_m68k_disasm_operand_shapes[M68K_DISASM_FORM_SLOT_COUNT][4] = {",
            self._tables,
        )
        self.assertIn(
            "static const uint64_t g_m68k_disasm_operand_ea_mode_masks[M68K_DISASM_FORM_SLOT_COUNT][4] = {",
            self._tables,
        )
        self.assertIn("static const M68kAsmFormDef g_m68k_disasm_forms[M68K_DISASM_FORM_SLOT_COUNT]", self._tables)

    def test_cmp2_ea_mask_excludes_register_direct_modes(self) -> None:
        forms = self._generator._load_forms()
        cmp2_form = next(form for form in forms if form.syntax == "CMP2 <ea>,Rn")
        mask = cmp2_form.ea_mode_masks[0]
        self.assertEqual(mask & 0xFFFF, 0)
        self.assertNotEqual(mask & (1 << (2 * 8)), 0)

    def test_includes_concrete_coprocessor_condition_forms(self) -> None:
        self.assertIn('"cpbcc"', self._tables)
        self.assertIn('"cpdbcc"', self._tables)
        self.assertIn('"cptrapcc"', self._tables)
        self.assertIn('"pscc", "PScc <ea>", M68K_ASM_MNEMONIC_PSCC, M68K_ASM_FORM_NONE', self._tables)
        self.assertNotIn('"pscc", "PScc <ea>", 0u, 65535u', self._tables)

    def test_form_count_matches_initializers(self) -> None:
        match = re.search(r"#define M68K_DISASM_FORM_COUNT (\d+)u", self._metadata)
        self.assertIsNotNone(match)
        assert match is not None
        initializers = re.findall(r'^    \{ "[^"]*", "[^"]*",', self._tables, flags=re.MULTILINE)
        self.assertEqual(int(match.group(1)) + 1, len(initializers))

    def test_generated_tables_pass_style_checker(self) -> None:
        issues = self._checker.check_file(
            self._outdir / "m68k_disassembler_tables.h", self._checker.DEFAULT_LINE_LENGTH
        )
        issues.extend(self._checker.check_file(
            self._outdir / "m68k_disassembler_metadata.h", self._checker.DEFAULT_LINE_LENGTH
        ))
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_EXPLICIT_TESTS") == "1":
        return tests
    suite = unittest.TestSuite()

    def append_filtered(test):
        if isinstance(test, unittest.TestSuite):
          for item in test:
            append_filtered(item)
          return
        if getattr(test, "_testMethodName", "") == "test_generated_tables_pass_style_checker":
          return
        suite.addTest(test)

    append_filtered(tests)
    return suite
