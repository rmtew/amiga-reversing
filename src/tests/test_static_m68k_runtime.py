from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLE_CHECKER = ROOT / "src" / "scripts" / "check_c_style.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class StaticM68kRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._assembler_source = (ROOT / "src" / "m68k_assembler.c").read_text(encoding="ascii")
        cls._assembler_header = (ROOT / "src" / "m68k_assembler.h").read_text(encoding="ascii")
        cls._disassembler_source = (ROOT / "src" / "m68k_disassembler.c").read_text(encoding="ascii")
        cls._disassembler_header = (ROOT / "src" / "m68k_disassembler.h").read_text(encoding="ascii")
        cls._checker = _load_module(STYLE_CHECKER, "src_test_static_m68k_runtime_style_checker")

    def test_assembler_runtime_exposes_expected_api(self) -> None:
        self.assertIn("m68k_asm_assemble_instruction", self._assembler_source)
        self.assertIn("m68k_asm_emit_extensions", self._assembler_source)
        self.assertIn("m68k_asm_operand_extension_word_count", self._assembler_header)
        self.assertIn("m68k_asm_find_form_for_operands", self._assembler_source)

    def test_disassembler_runtime_exposes_expected_api(self) -> None:
        self.assertIn("m68k_disassemble_one", self._disassembler_source)
        self.assertIn("m68k_disasm_match_form", self._disassembler_source)
        self.assertIn("int m68k_disassemble_one(const uint8_t *data, size_t size, M68kDisasmResult *out);", self._disassembler_header)

    def test_static_runtime_files_pass_style_checker(self) -> None:
        issues = []
        for path in (
            ROOT / "src" / "m68k_assembler.c",
            ROOT / "src" / "m68k_assembler.h",
            ROOT / "src" / "m68k_disassembler.c",
            ROOT / "src" / "m68k_disassembler.h",
        ):
            issues.extend(self._checker.check_file(path, self._checker.DEFAULT_LINE_LENGTH))
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
