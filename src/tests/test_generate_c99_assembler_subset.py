from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src" / "scripts" / "generate_c99_assembler_subset.py"
STYLE_CHECKER = ROOT / "src" / "scripts" / "check_c_style.py"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


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
        result = subprocess.run(
            [str(PYTHON), str(SCRIPT), "--output-dir", str(cls._outdir)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            cls._tmp.cleanup()
            raise AssertionError(result.stdout + result.stderr)
        cls._tables_c = (cls._outdir / "m68k_asm_tables.c").read_text(encoding="ascii")
        cls._tables_h = (cls._outdir / "m68k_asm_tables.h").read_text(encoding="ascii")
        cls._checker = _load_module(STYLE_CHECKER, "src_test_generate_c99_assembler_style_checker")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_generates_dense_multiline_table_wrapping(self) -> None:
        self.assertIn(
            "    { \"pack\", \"PACK -(Ax),-(Ay),# <adjustment>\", M68K_ASM_MNEMONIC_PACK, 0, 3,\n",
            self._tables_c,
        )
        self.assertIn(
            "const M68kAsmFormDef *m68k_asm_find_form_for_operands(const char *mnemonic, const M68kAsmOperandValue *operands, size_t operand_count,\n",
            self._tables_h,
        )
        self.assertNotIn("const M68kAsmFormDef *m68k_asm_find_form_for_operands(\n", self._tables_h)

    def test_generates_table_api(self) -> None:
        self.assertIn("typedef struct {", self._tables_h)
        self.assertIn(
            "int m68k_asm_assemble_instruction(const M68kAsmInstructionSpec *spec, uint8_t *out_bytes, size_t max_bytes, size_t *out_byte_count);\n",
            self._tables_h,
        )
        self.assertIn(
            "const M68kAsmFormDef *m68k_asm_find_form_for_operands(const char *mnemonic, const M68kAsmOperandValue *operands, size_t operand_count,\n",
            self._tables_h,
        )

    def test_generated_files_pass_style_checker(self) -> None:
        issues = []
        for path in (self._outdir / "m68k_asm_tables.c", self._outdir / "m68k_asm_tables.h"):
            issues.extend(self._checker.check_file(path, self._checker.DEFAULT_LINE_LENGTH))
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
