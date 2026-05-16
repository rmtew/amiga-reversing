from __future__ import annotations

import ctypes
import importlib.util
import json
import subprocess
import sys
import unittest
from functools import lru_cache
from pathlib import Path

from src.tests._build_helpers import prepare_test_exe
from src.tests._build_helpers import require_built_tools
from src.tests._build_helpers import prepare_test_dll

ROOT = Path(__file__).resolve().parents[2]
CORPUS_GENERATOR_PATH = ROOT / "src" / "scripts" / "generate_c99_assembler_corpus.py"
GENERATED_DIR = ROOT / "src" / "tests" / "generated"
ASM_DLL_PATH = ROOT / "src" / "build" / "m68k_assembler_lib.dll"
CLI_EXE = ROOT / "src" / "build" / "m68k_assembler_app.exe"

CPU_CODES = {
    "68000": 0,
    "68010": 1,
    "68020": 2,
    "68030": 3,
    "68040": 4,
    "68060": 5,
}

CPU_MANIFESTS = {
    "68000": GENERATED_DIR / "all_cases.txt",
    "68020": GENERATED_DIR / "all_cases_68020.txt",
    "68040": GENERATED_DIR / "all_cases_68040.txt",
    "68060": GENERATED_DIR / "all_cases_68060.txt",
}

CPU_CASE_JSONS = {
    "68000": GENERATED_DIR / "all_cases.json",
    "68020": GENERATED_DIR / "all_cases_68020.json",
    "68040": GENERATED_DIR / "all_cases_68040.json",
    "68060": GENERATED_DIR / "all_cases_68060.json",
}
M68K_DIAG_SEVERITY_ERROR = 3
M68K_DIAG_MESSAGE_SIZE = 160
M68K_DIAG_LIST_CAPACITY = 8


class M68kDiag(ctypes.Structure):
    _fields_ = [
        ("severity", ctypes.c_uint32),
        ("code", ctypes.c_uint32),
        ("message", ctypes.c_char * M68K_DIAG_MESSAGE_SIZE),
    ]


class M68kDiagList(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_size_t),
        ("dropped_count", ctypes.c_size_t),
        ("items", M68kDiag * M68K_DIAG_LIST_CAPACITY),
    ]


class M68kAssembleResult(ctypes.Structure):
    _fields_ = [
        ("byte_count", ctypes.c_size_t),
        ("diagnostics", M68kDiagList),
    ]


class M68kVerifyResult(ctypes.Structure):
    _fields_ = [("diagnostics", M68kDiagList)]


def _diag_message(diagnostics: M68kDiagList) -> str:
    for index in range(diagnostics.count):
        if diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR:
            return diagnostics.items[index].message.decode("utf-8")
    if diagnostics.count:
        return diagnostics.items[0].message.decode("utf-8")
    return ""


def _diag_has_errors(diagnostics: M68kDiagList) -> bool:
    return any(
        diagnostics.items[index].severity == M68K_DIAG_SEVERITY_ERROR
        for index in range(diagnostics.count)
    )


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _corpus_generator():
    return _load_module(CORPUS_GENERATOR_PATH, "src_c99_assembler_corpus_generator")


@lru_cache(maxsize=None)
def _generate_cases_for_cpu(target_cpu: str):
    return tuple(_corpus_generator().generate_cases(target_cpu))


@lru_cache(maxsize=None)
def _generate_oracle_cases_for_cpu(target_cpu: str):
    return tuple(_corpus_generator().generate_cases(target_cpu, require_oracle_cpu=True))


@lru_cache(maxsize=None)
def _manifest_summary_for_cpu(target_cpu: str) -> tuple[set[str], bool]:
    cases = json.loads(CPU_CASE_JSONS[target_cpu].read_text(encoding="utf-8"))
    mnemonics = {str(case["mnemonic"]).upper() for case in cases}
    has_full = any("{full}" in line for case in cases for line in case["asm_lines"])
    return mnemonics, has_full


@lru_cache(maxsize=1)
def _assembler_library():
    require_built_tools()
    library = ctypes.CDLL(str(prepare_test_dll(ASM_DLL_PATH)))
    class M68kAsmOptions(ctypes.Structure):
        _fields_ = [("target_cpu", ctypes.c_uint8), ("input_mode", ctypes.c_uint8)]

    class M68kAsmVerifyOptions(ctypes.Structure):
        _fields_ = [("target_cpu", ctypes.c_uint8)]

    library._m68k_asm_options_type = M68kAsmOptions
    library._m68k_asm_verify_options_type = M68kAsmVerifyOptions
    library.m68k_assemble.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(M68kAsmOptions),
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
    ]
    library.m68k_assemble.restype = M68kAssembleResult
    library.m68k_verify_manifest.argtypes = [
        ctypes.c_char_p,
        ctypes.POINTER(M68kAsmVerifyOptions),
    ]
    library.m68k_verify_manifest.restype = M68kVerifyResult
    library.m68k_verify_corpus.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.POINTER(M68kAsmVerifyOptions),
    ]
    library.m68k_verify_corpus.restype = M68kVerifyResult
    return library


@lru_cache(maxsize=1)
def _cli_path() -> Path:
    require_built_tools()
    assert CLI_EXE.exists()
    return prepare_test_exe(CLI_EXE)


def _verify_manifest(manifest_path: Path, cpu_name: str) -> tuple[int, str]:
    library = _assembler_library()
    options = library._m68k_asm_verify_options_type(CPU_CODES[cpu_name])
    result = library.m68k_verify_manifest(
        str(manifest_path).encode("utf-8"),
        ctypes.byref(options),
    )
    return (1 if _diag_has_errors(result.diagnostics) else 0), _diag_message(result.diagnostics)


def _verify_corpus(manifest_path: Path, binary_path: Path, cpu_name: str) -> tuple[int, str]:
    library = _assembler_library()
    options = library._m68k_asm_verify_options_type(CPU_CODES[cpu_name])
    result = library.m68k_verify_corpus(
        str(manifest_path).encode("utf-8"),
        str(binary_path).encode("utf-8"),
        ctypes.byref(options),
    )
    return (1 if _diag_has_errors(result.diagnostics) else 0), _diag_message(result.diagnostics)


def _assemble_line(asm_text: str, cpu_name: str = "68000") -> tuple[int, bytes, str]:
    library = _assembler_library()
    options = library._m68k_asm_options_type(CPU_CODES[cpu_name], 0)
    out_buf = (ctypes.c_ubyte * 64)()
    result = library.m68k_assemble(
        asm_text.encode("ascii"),
        ctypes.byref(options),
        out_buf,
        len(out_buf),
    )
    return (
        1 if _diag_has_errors(result.diagnostics) else 0,
        bytes(out_buf[:result.byte_count]),
        _diag_message(result.diagnostics),
    )


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(_cli_path()), *args], cwd=ROOT, capture_output=True, text=True, check=False)


class C99AssemblerCorpusTests(unittest.TestCase):
    def _generated_oracle_binary_matches_current_generated_cases(self) -> None:
        manifest_path = GENERATED_DIR / "all_cases.json"
        binary_path = GENERATED_DIR / "all_cases.bin"
        self.assertTrue(manifest_path.exists(), "generate corpus first: all_cases.json missing")
        self.assertTrue(binary_path.exists(), "generate corpus first: all_cases.bin missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        generated_cases = _generate_oracle_cases_for_cpu("68000")
        self.assertEqual(len(manifest), len(generated_cases))
        rebuilt = b"".join(bytes.fromhex(case.expected_hex) for case in generated_cases)
        self.assertEqual(rebuilt, binary_path.read_bytes())

    def _native_68000_manifest_matches_oracle_binary(self) -> None:
        manifest_path = GENERATED_DIR / "all_cases.txt"
        binary_path = GENERATED_DIR / "all_cases.bin"
        result, error = _verify_corpus(manifest_path, binary_path, "68000")
        self.assertEqual(result, 0, error)

    def _native_68020_manifest_verifies_in_68020_mode(self) -> None:
        manifest_path = GENERATED_DIR / "all_cases_68020.txt"
        result, error = _verify_manifest(manifest_path, "68020")
        self.assertEqual(result, 0, error)

    def _native_68040_manifest_verifies_in_68040_mode(self) -> None:
        manifest_path = GENERATED_DIR / "all_cases_68040.txt"
        result, error = _verify_manifest(manifest_path, "68040")
        self.assertEqual(result, 0, error)

    def _native_68060_manifest_verifies_in_68060_mode(self) -> None:
        manifest_path = GENERATED_DIR / "all_cases_68060.txt"
        result, error = _verify_manifest(manifest_path, "68060")
        self.assertEqual(result, 0, error)

    def _cpu_corpus_stratification(self) -> None:
        mnemonics_68000, has_full_68000 = _manifest_summary_for_cpu("68000")
        mnemonics_68020, has_full_68020 = _manifest_summary_for_cpu("68020")
        mnemonics_68040, has_full_68040 = _manifest_summary_for_cpu("68040")
        self.assertNotIn("MOVES", mnemonics_68000)
        self.assertNotIn("MOVEC", mnemonics_68000)
        self.assertNotIn("CHK2", mnemonics_68000)
        self.assertNotIn("CMP2", mnemonics_68000)
        self.assertNotIn("CINVL", mnemonics_68020)
        self.assertNotIn("CPUSHL", mnemonics_68020)
        self.assertIn("MOVES", mnemonics_68020)
        self.assertIn("MOVEC", mnemonics_68020)
        self.assertIn("CHK2", mnemonics_68020)
        self.assertIn("CMP2", mnemonics_68020)
        self.assertIn("CINVL", mnemonics_68040)
        self.assertIn("CINVP", mnemonics_68040)
        self.assertIn("CINVA", mnemonics_68040)
        self.assertIn("CPUSHL", mnemonics_68040)
        self.assertIn("CPUSHP", mnemonics_68040)
        self.assertIn("CPUSHA", mnemonics_68040)
        self.assertFalse(has_full_68000)
        self.assertTrue(has_full_68020)
        self.assertTrue(has_full_68040)

    def _native_manifest_cpu_gating(self) -> None:
        full_ext_path = GENERATED_DIR / "full_ext_cases.txt"
        manifest_68020_path = GENERATED_DIR / "all_cases_68020.txt"
        self.assertNotEqual(_run_cli("verify-manifest", str(full_ext_path)).returncode, 0)
        self.assertEqual(_run_cli("verify-manifest", "--cpu", "68020", str(full_ext_path)).returncode, 0)
        self.assertNotEqual(_run_cli("verify-manifest", str(manifest_68020_path)).returncode, 0)
        self.assertEqual(_run_cli("verify-manifest", "--cpu", "68020", str(manifest_68020_path)).returncode, 0)

    def test_operand_sample_registry_includes_special_operands(self) -> None:
        registry = {
            entry.operand_kind: entry
            for entry in _corpus_generator().generate_operand_sample_registry("68020")
        }
        self.assertEqual(registry["ctrl_reg"].status, "sampled")
        self.assertTrue(any(sample["asm"] == "vbr" for sample in registry["ctrl_reg"].samples))
        self.assertEqual(registry["rn_pair"].status, "sampled")
        self.assertTrue(any(sample["pair_reg_is_address"] == 1 for sample in registry["rn_pair"].samples))

    def test_operand_sample_registry_reports_missing_schema(self) -> None:
        registry = {
            entry.operand_kind: entry
            for entry in _corpus_generator().generate_operand_sample_registry("68020")
        }
        self.assertEqual(registry["imm"].status, "missing_sample_strategy")
        self.assertIn("no generated sample schema", registry["imm"].reason)

    def test_native_line_cpu_gating_rejects_expected_cases(self) -> None:
        samples = (
            ("68000", "moves.w d0,(a0)"),
            ("68000", "lea $10(a0,d1.w){full},a0"),
            ("68020", "cinvl dc,(a0)"),
            ("68020", "cpusha bc"),
            ("68020", "bftst (a0){256:1}"),
            ("68020", "bftst (a0){0:288}"),
        )
        for cpu_name, asm_text in samples:
            with self.subTest(cpu=cpu_name, asm=asm_text):
                result, _, _ = _assemble_line(asm_text, cpu_name)
                self.assertNotEqual(result, 0)

    def test_native_line_cpu_gating_accepts_expected_cases(self) -> None:
        samples = (
            ("68020", "moves.w d0,(a0)"),
            ("68020", "lea $10(a0,d1.w){full},a0"),
            ("68040", "move16 ($00123456).l,(a0)+"),
            ("68040", "cinvl dc,(a0)"),
            ("68040", "cinvp ic,(a7)"),
            ("68040", "cinva bc"),
            ("68040", "cpushl dc,(a0)"),
            ("68040", "cpushp ic,(a7)"),
            ("68040", "cpusha bc"),
            ("68010", "move ccr,d0"),
            ("68020", "bftst (a0){0:1}"),
            ("68020", "bfextu $0010(a0){d0:8},d1"),
            ("68020", "bfins d1,$10(a0,d2.w){0:d3}"),
        )
        for cpu_name, asm_text in samples:
            with self.subTest(cpu=cpu_name, asm=asm_text):
                result, _, error = _assemble_line(asm_text, cpu_name)
                self.assertEqual(result, 0, error)


if __name__ == "__main__":
    unittest.main()
