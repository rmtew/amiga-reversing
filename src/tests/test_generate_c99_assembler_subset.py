from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src" / "scripts" / "generate_c99_assembler_subset.py"
STYLE_CHECKER = ROOT / "src" / "scripts" / "check_c_style.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateC99AssemblerSubsetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls._outdir = Path(cls._tmp.name)
        generator = _load_module(SCRIPT, "src_test_generate_c99_assembler_subset_generator")
        try:
            generator.generate_files(cls._outdir)
        except Exception as exc:
            cls._tmp.cleanup()
            raise AssertionError(str(exc))
        cls._tables_c = (cls._outdir / "m68k_asm_tables.c").read_text(encoding="ascii")
        cls._tables_h = (cls._outdir / "m68k_asm_tables.h").read_text(encoding="ascii")
        cls._metadata_h = (ROOT / "src" / "m68k_asm_metadata.h").read_text(encoding="ascii")
        cls._checker = _load_module(STYLE_CHECKER, "src_test_generate_c99_assembler_style_checker")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_generates_dense_multiline_table_wrapping(self) -> None:
        self.assertIn(
            "    { \"pack\", \"PACK -(Ax),-(Ay),# <adjustment>\", M68K_ASM_MNEMONIC_PACK,",
            self._tables_c,
        )
        self.assertNotIn("m68k_asm_form_for_operands(", self._tables_h)

    def test_generates_table_api(self) -> None:
        self.assertNotIn("typedef struct {", self._tables_h)
        self.assertIn("    M68K_ASM_MNEMONIC_NONE = 0,\n", self._tables_h)
        self.assertIn("    M68K_ASM_CONTROL_REGISTER_NONE = 255,\n", self._tables_h)
        self.assertIn("    M68K_ASM_CONTROL_REGISTER_USP = 24,\n", self._tables_h)
        self.assertIn("    M68K_ASM_CONTROL_REGISTER_VBR = 26,\n", self._tables_h)
        self.assertIn("    M68K_ASM_FORM_COUNT =", self._tables_h)
        self.assertIn("    M68K_ASM_PATCH_COUNT =", self._tables_h)
        self.assertIn("  uint8_t mnemonic_id;\n", self._metadata_h)
        self.assertIn("  uint16_t asm_form_index;\n", self._metadata_h)
        self.assertIn(
            "extern const char *const g_m68k_asm_mnemonic_names[M68K_ASM_MNEMONIC_COUNT];\n",
            self._metadata_h,
        )
        self.assertIn(
            "extern const M68kAsmMnemonicLookupEntry g_m68k_asm_mnemonic_lookup[];\n",
            self._metadata_h,
        )
        self.assertIn(
            'const char *const g_m68k_asm_mnemonic_names[M68K_ASM_MNEMONIC_COUNT] = {\n    "",\n',
            self._tables_c,
        )
        self.assertIn(
            'const M68kAsmMnemonicLookupEntry g_m68k_asm_mnemonic_lookup[',
            self._tables_c,
        )
        self.assertIn("    M68K_ASM_MNEMONIC_PSCC =", self._tables_h)
        self.assertIn('    { "pscc", M68K_ASM_MNEMONIC_PSCC },', self._tables_c)
        self.assertIn(
            "int m68k_asm_assemble_instruction(const M68kAsmInstructionSpec *spec, uint8_t *out_bytes,\n",
            self._metadata_h,
        )
        self.assertIn(
            "uint16_t m68k_asm_form_index_for_id(uint8_t mnemonic_id, size_t operand_count);\n",
            self._metadata_h,
        )
        self.assertIn(
            "uint16_t m68k_asm_form_index_for_operands_id(uint8_t mnemonic_id,\n",
            self._metadata_h,
        )

    def test_generated_files_pass_style_checker(self) -> None:
        issues = []
        for path in (self._outdir / "m68k_asm_tables.c", self._outdir / "m68k_asm_tables.h"):
            issues.extend(self._checker.check_file(path, self._checker.DEFAULT_LINE_LENGTH))
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
        if getattr(test, "_testMethodName", "") == "test_generated_files_pass_style_checker":
          return
        suite.addTest(test)

    append_filtered(tests)
    return suite
