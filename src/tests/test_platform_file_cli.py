from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.real_target_fixtures import get_real_target_fixture
from src.tests._build_helpers import prepare_test_exe
from src.tests._build_helpers import require_built_tools
from src.tests._platform_backend_test_utils import FIXTURE_DIR
from src.tests._platform_backend_test_utils import make_synthetic_atari_prg
from src.tests._platform_backend_test_utils import make_synthetic_hunkexe
ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
EXE = BUILD_DIR / "platform_file_cli.exe"
ASM_EXE = BUILD_DIR / "m68k_assembler_app.exe"
GENAM_FIXTURE = get_real_target_fixture("GenAm")
BIN_GEN_FIXTURE = get_real_target_fixture("BIN_GEN")
GENAM_BIN = Path(GENAM_FIXTURE["binary"])
GENAM_LATEST = Path(GENAM_FIXTURE["source"])
GENAM_BENCHMARK = Path(GENAM_FIXTURE["benchmark"])
GENAM_INCLUDE_DIR = Path(GENAM_FIXTURE["include_dir"])
BIN_GEN_BIN = Path(BIN_GEN_FIXTURE["binary"])
BIN_GEN_LATEST = Path(BIN_GEN_FIXTURE["source"])
BIN_GEN_BENCHMARK = Path(BIN_GEN_FIXTURE["benchmark"])
BIN_GEN_INCLUDE_DIR = Path(BIN_GEN_FIXTURE["include_dir"])


class PlatformFileCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_built_tools()
        cls.file_exe = prepare_test_exe(EXE)
        cls.asm_exe = prepare_test_exe(ASM_EXE)

    def _run_cli(self, platform_name: str, suffix: str, data: bytes) -> dict[str, object]:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / f"sample{suffix}"
            path.write_bytes(data)
            result = subprocess.run(
                [str(self.file_exe), "inspect-file", platform_name, str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

    def _inspect_file_path(self, platform_name: str, path: Path) -> dict[str, object]:
        result = subprocess.run(
            [str(self.file_exe), "inspect-file", platform_name, str(path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _disassemble_real_path(self, platform_name: str, path: Path, syntax: str = "genam") -> str:
        result = subprocess.run(
            [str(self.file_exe), "disassemble-file", "--syntax", syntax, platform_name, str(path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def _benchmark_real_path(self, platform_name: str, path: Path) -> dict[str, object]:
        try:
            cli_path = path.relative_to(ROOT).as_posix()
        except ValueError:
            cli_path = str(path)
        result = subprocess.run(
            [str(self.file_exe), "benchmark-file", platform_name, cli_path],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _normalized_benchmark(self, payload: dict[str, object]) -> dict[str, object]:
        return {
            "benchmark_version": payload["benchmark_version"],
            "platform": payload["platform"],
            "path": payload["path"],
            "file": payload["file"],
            "analysis": payload["analysis"],
            "render": payload["render"],
            "sections": payload["sections"],
        }

    def _normalized_file_summary(self, summary: dict[str, object]) -> dict[str, object]:
        return {
            "platform": summary["platform"],
            "file_kind": summary["file_kind"],
            "section_count": summary["section_count"],
            "fixup_count": summary["fixup_count"],
            "sections": [
                {
                    "name": section["name"],
                    "kind": section["kind"],
                    "mem_type": section["mem_type"],
                    "mem_attrs": section["mem_attrs"],
                    "alloc_size": section["alloc_size"],
                    "stored_size": section["stored_size"],
                    "size": section["size"],
                    "data_size": section["data_size"],
                    "data_hex": section["data_hex"],
                    "fixup_count": section["fixup_count"],
                    "debug_size": section["debug_size"],
                }
                for section in summary["sections"]
            ],
        }

    def _normalized_oracle_summary(self, summary: dict[str, object]) -> dict[str, object]:
        return {
            "platform": summary["platform"],
            "file_kind": summary["file_kind"],
            "section_count": summary["section_count"],
            "fixup_count": summary["fixup_count"],
            "sections": [
                {
                    "name": section["name"],
                    "kind": section["kind"],
                    "mem_type": section["mem_type"],
                    "mem_attrs": section["mem_attrs"],
                    "fixup_count": section["fixup_count"],
                    "debug_size": section["debug_size"],
                }
                for section in summary["sections"]
            ],
        }

    def _assemble_latest_with_our_assembler(self, backend: str, include_dir: Path, source_path: Path,
                                            output_path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(self.asm_exe),
                "assemble-platform-file",
                "--backend",
                backend,
                "--include-dir",
                str(include_dir),
                str(source_path),
                str(output_path),
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_inspect_file_atari_prg(self) -> None:
        actual = self._run_cli("atari-st", ".prg", make_synthetic_atari_prg(b"\x4E\x75", b"\x12\x34", 6))
        self.assertEqual(actual["platform"], "atari-st")
        self.assertEqual(actual["file_kind"], "executable")
        self.assertEqual(actual["section_count"], 3)
        self.assertEqual(actual["sections"][0]["name"], "TEXT")
        self.assertEqual(actual["sections"][1]["name"], "DATA")
        self.assertEqual(actual["sections"][2]["name"], "BSS")

    def test_inspect_file_amiga_hunk(self) -> None:
        actual = self._run_cli("amiga-hunk", ".exe", make_synthetic_hunkexe())
        self.assertEqual(actual["platform"], "amiga-hunk")
        self.assertEqual(actual["file_kind"], "executable")
        self.assertEqual(actual["section_count"], 2)
        self.assertEqual(actual["sections"][0]["kind"], "code")
        self.assertEqual(actual["sections"][1]["kind"], "data")

    def _assemble_line_hex(self, cpu: str, text: str) -> bytes:
        result = subprocess.run(
            [str(self.asm_exe), "assemble-line", "--cpu", cpu, text],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return bytes.fromhex(result.stdout.strip())

    def test_disassemble_file_honors_generated_name_policy(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.exe"
            path.write_bytes(make_synthetic_hunkexe())
            default_result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(default_result.returncode, 0, default_result.stderr)
            self.assertIn("loc_0000:", default_result.stdout)

            fallback_result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "--no-generated-names", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(fallback_result.returncode, 0, fallback_result.stderr)
            self.assertIn("L_0000:", fallback_result.stdout)
            self.assertNotIn("loc_0000:", fallback_result.stdout)

    def test_disassemble_file_honors_custom_prefixes(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.exe"
            path.write_bytes(make_synthetic_hunkexe())
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "disassemble-file",
                    "--code-label-prefix",
                    "blk",
                    "--call-label-prefix",
                    "fn",
                    "--data-label-prefix",
                    "obj",
                    "amiga-hunk",
                    str(path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("blk_0000:", result.stdout)

    def test_disassemble_file_syntax_mode_changes_short_branch_suffix(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "branch.exe"
            path.write_bytes(make_synthetic_hunkexe(code_data=b"\x60\x02\x00\x00\x4E\x75\x00\x00"))
            canonical = subprocess.run(
                [str(self.file_exe), "disassemble-file", "--syntax", "canonical", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(canonical.returncode, 0, canonical.stderr)
            self.assertIn("bra.b", canonical.stdout)

            genam = subprocess.run(
                [str(self.file_exe), "disassemble-file", "--syntax", "genam", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(genam.returncode, 0, genam.stderr)
            self.assertIn("bra.s", genam.stdout)

    def test_disassemble_file_emits_overlap_violation_comments(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "overlap.prg"
            path.write_bytes(make_synthetic_atari_prg(b"\x48\x7A\x00\x02\x41\xE9\x00\x10\x4E\x75", b"", 0))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pea.l loc_0004(pc)", result.stdout)
            self.assertNotIn("VIOLATION: invalid overlap", result.stdout)

    def test_disassemble_file_keeps_pc_index_pea_render_explicit(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "pcindex.prg"
            path.write_bytes(make_synthetic_atari_prg(bytes.fromhex("487b00024e75"), b"", 0))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pea.l loc_0004(pc,d0.w)", result.stdout)
            self.assertNotIn("loc_0000+2(pc,d0.w)", result.stdout)

    def test_disassemble_file_uses_current_relative_pc_index_base_for_interior_target(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "pcindex_jump.prg"
            path.write_bytes(make_synthetic_atari_prg(bytes.fromhex("4efb00004e75"), b"", 0))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("jmp dat_0004-2(pc,d0.w)", result.stdout)
            self.assertIn("invalid overlap: pc-relative reference targets +2 into instruction at $0000", result.stdout)
            self.assertIn("dat_0004:", result.stdout)
            self.assertNotIn("jmp *+2(pc,d0.w)", result.stdout)
            self.assertNotIn("loc_0000+2(pc,d0.w)", result.stdout)

    def test_disassemble_file_uses_pc_plus_2_base_for_lea_pc_displacement(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "pcdisp.prg"
            path.write_bytes(make_synthetic_atari_prg(bytes.fromhex("4e7143fafffc4e75"), b"", 0))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("lea.l loc_0000(pc),a1", result.stdout)
            self.assertNotIn("lea.l loc_0002(pc),a1", result.stdout)

    def test_disassemble_file_renders_negative_indexed_displacement_signed(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "negindex.prg"
            code = self._assemble_line_hex("68000", "move.w -8(a1,d1.w),d1") + self._assemble_line_hex("68000", "rts")
            path.write_bytes(make_synthetic_atari_prg(code, b"", 0))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("move.w -$8(a1,d1.w),d1", result.stdout)
            self.assertNotIn("move.w $F8(a1,d1.w),d1", result.stdout)

    def test_disassemble_file_recovers_pc_index_inline_dispatch_entries(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "pcindex_dispatch.prg"
            code = (
                self._assemble_line_hex("68000", "jmp 0(pc,d0.w)")
                + bytes.fromhex("60000006600000044e754e75")
            )
            path.write_bytes(make_synthetic_atari_prg(code, b"", 0))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("loc_0004:", result.stdout)
            self.assertIn("loc_0008:", result.stdout)
            self.assertIn("bra.w loc_000C", result.stdout)
            self.assertIn("bra.w loc_000E", result.stdout)
            self.assertNotIn("ori.b #0,d0", result.stdout)

    def test_disassemble_file_preserves_noncanonical_byte_immediate_mnemonic(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "byteimm.prg"
            path.write_bytes(make_synthetic_atari_prg(bytes.fromhex("00244e754e75"), b"", 0))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("\n    ori.b #$4E75,-(a4)\n", result.stdout)
            self.assertNotIn("NOTE: preserved exact bytes", result.stdout)
            vasm_result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "--syntax", "vasm", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(vasm_result.returncode, 0, vasm_result.stderr)
            self.assertIn("ori.b #117,-(a4) ; NOTE: vasm-normalized from exact immediate word $4E75",
                          vasm_result.stdout)

    def test_disassemble_genam_resolves_real_jump_table_dispatch_site(self) -> None:
        text = self._disassemble_real_path("amiga-hunk", GENAM_BIN)
        self.assertIn("dat_0EA2:", text)
        self.assertIn("lea.l dat_0EA2(pc),a1", text)
        self.assertIn("move.w -$8(a1,d1.w),d1", text)
        self.assertIn("jsr $0(a1,d1.w)", text)
        self.assertNotIn("jsr $0(a1,d1.w) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertIn("DC.W    sub_20B4-dat_0EA2", text)
        self.assertIn("DC.W    loc_10A4-dat_0EA2", text)
        self.assertIn("DC.W    sub_2BC0-dat_0EA2", text)
        self.assertIn("DC.W    sub_10DA-dat_0EA2", text)
        self.assertIn("DC.W    sub_1120-dat_0EA2", text)
        self.assertIn("movea.l #dat_A664,a0", text)
        self.assertIn("movea.l #dat_B21E,a0", text)
        self.assertIn("movea.l #dat_CD3C,a1", text)
        self.assertIn("movea.l #dat_BA08,a2", text)
        self.assertIn("movea.l #dat_E070,a0", text)
        self.assertIn("movea.l #dat_A764,a1", text)
        self.assertIn("move.w dat_439E(pc,d1.w),d0", text)
        self.assertIn("move.l dat_50BA(pc,d0.w),d2", text)
        self.assertIn("move.b dat_5782-1(pc,d2.w),d0", text)
        self.assertIn("and.l dat_7888(pc),d0", text)
        self.assertIn("cmp.l dat_7888(pc),d0", text)
        self.assertIn("move.b dat_87FC(pc,d0.w),d0", text)
        self.assertIn("move.b dat_8EC8(pc,d1.w),d1", text)
        self.assertIn("move.b dat_FB06(pc,d1.w),(a4)+", text)
        self.assertIn("jsr _LVOAllocMem(a6)", text)
        self.assertIn("jsr _LVOFreeMem(a6)", text)
        self.assertIn("jsr _LVOGetSysTime(a6)", text)
        self.assertIn("jsr _LVOSubTime(a6)", text)
        self.assertEqual(text.count("jsr _LVOSetSignal(a6)"), 2)
        self.assertIn("movea.l app_TimerBase(a6),a0", text)
        self.assertIn("movea.l app_TimerBase(a6),a6", text)
        self.assertIn("movea.l app_DOSBase(a6),a1", text)
        self.assertIn("movea.l app_DOSBase(a6),a6", text)
        self.assertIn("_LVOOutput EQU -60", text)
        self.assertIn("_LVOWrite EQU -48", text)
        self.assertIn("moveq.l #_LVOOutput,d0", text)
        self.assertIn("moveq.l #_LVOWrite,d0", text)
        self.assertNotIn("moveq.l #-60,d0", text)
        self.assertNotIn("moveq.l #196,d0", text)
        self.assertIn("bsr.w sub_B0D6 ; KNOWN: DOSBase _LVOOutput fallback via local wrapper", text)
        self.assertIn("bsr.w sub_B0D6 ; KNOWN: DOSBase _LVOOpen fallback via local wrapper", text)
        self.assertIn("jsr $0(a6,d0.w) ; KNOWN: DOSBase indexed vector via d0", text)
        self.assertIn("jsr (a0) ; KNOWN: callback field +4 from $01A2(a6)", text)
        self.assertIn("jsr (a1) ; KNOWN: callback field +4 from $01A2(a6)", text)
        self.assertNotIn("movea.l #$A664,a0", text)
        self.assertNotIn("movea.l #$B21E,a0", text)
        self.assertNotIn("movea.l #$CD3C,a1", text)
        self.assertNotIn("movea.l #$BA08,a2", text)
        self.assertNotIn("movea.l #$E070,a0", text)
        self.assertNotIn("movea.l #$A764,a1", text)
        self.assertNotIn("move.b $42(pc,d1.w),d7", text)
        self.assertNotIn("move.w $18(pc,d1.w),d0", text)
        self.assertNotIn("move.l $20(pc,d0.w),d2", text)
        self.assertNotIn("move.l $16(pc,d0.w),d0", text)
        self.assertNotIn("move.b *+25(pc,d2.w),d0", text)
        self.assertNotIn("and.l -$8(pc),d0", text)
        self.assertNotIn("cmp.l -$E(pc),d0", text)
        self.assertNotIn("move.b -$1C(pc,d0.w),d0", text)
        self.assertNotIn("jsr -$0132(a6)", text)
        self.assertNotIn("jsr (a0) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertNotIn("jsr (a1) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertNotIn("move.b $4(pc,d1.w),d1", text)
        self.assertNotIn("move.b $18(pc,d1.w),(a4)+", text)
        self.assertNotIn("dat_0EA4:", text)
        self.assertNotIn("loc_0EA4:", text)
        self.assertNotIn("DC.W    loc_12B8-dat_0EA2", text)
        self.assertNotIn("DC.W    loc_24B6-dat_0EA2", text)
        self.assertNotIn("DC.W    loc_22B6-dat_0EA2", text)
        self.assertNotIn("DC.W    loc_22B4-dat_0EA2", text)
        self.assertNotIn("lea.l dat_0EA4(pc),a1", text)
        self.assertNotIn("jsr -$00C6(a6) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertNotIn("jsr -$00D2(a6) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertIn("jmp loc_13C8-2(pc,d0.w)", text)
        self.assertNotIn("jmp *+2(pc,d0.w)", text)
        self.assertNotIn("jmp loc_13C4+2(pc,d0.w)", text)
        table_idx = text.find("dat_439E:")
        self.assertNotEqual(table_idx, -1)
        table_window = text[table_idx:text.find("loc_43D2:", table_idx)]
        self.assertIn("DC.W    $0000", table_window)
        self.assertNotIn("DC.B    $00,$00", table_window)
        self.assertNotIn("DC.L    $00000000", table_window)
        self.assertNotIn("loc_3F3D:", text)
        self.assertNotIn("loc_3F43:", text)
        string_dispatch_idx = text.find("dat_3F3C:")
        self.assertNotEqual(string_dispatch_idx, -1)
        string_dispatch_window = text[string_dispatch_idx:text.find("loc_432C:", string_dispatch_idx)]
        dispatch_call_idx = text.find("loc_4370:")
        self.assertNotEqual(dispatch_call_idx, -1)
        dispatch_call_window = text[dispatch_call_idx:text.find("loc_4374:", dispatch_call_idx)]
        self.assertIn("jsr (a0)", dispatch_call_window)
        self.assertNotIn("jsr (a0) ; CANDIDATE: indirect_call index unresolved", dispatch_call_window)
        early_dispatch_call_idx = text.find("loc_3AB0:")
        self.assertNotEqual(early_dispatch_call_idx, -1)
        early_dispatch_call_window = text[early_dispatch_call_idx:text.find("loc_3AB2:", early_dispatch_call_idx)]
        self.assertIn("jsr (a0)", early_dispatch_call_window)
        self.assertNotIn("jsr (a0) ; CANDIDATE: indirect_call index unresolved", early_dispatch_call_window)
        self.assertIn('DC.B    "OWZERO"', string_dispatch_window)
        self.assertIn("DC.W    loc_4200-*", string_dispatch_window)
        self.assertIn("DC.W    loc_42A2-*", string_dispatch_window)
        self.assertIn("loc_4200:\n    moveq.l #2,d0", text)
        self.assertIn("loc_4218:\n    st.b $012C(a6)", text)
        self.assertIn("loc_42A2:\n    st.b $0120(a6)", text)
        self.assertIn("jsr _LVOAllocMem(a6)", text)
        self.assertNotIn("jsr -$00C6(a6) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertIn("jsr _LVOFreeMem(a6)", text)
        self.assertNotIn("jsr -$00D2(a6) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertNotIn("jsr -$0042(a6) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertNotIn("jsr -$0030(a6) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertNotIn("movea.l $0CD6(a6),a1", text)
        self.assertNotIn("movea.l $0CD6(a6),a6", text)
        self.assertNotIn("jsr $0(a6,d0.w) ; CANDIDATE: indirect_call index unresolved", text)

    def test_disassemble_genam_resolves_entry_relative_jump_table_dispatch_site(self) -> None:
        text = self._disassemble_real_path("amiga-hunk", GENAM_BIN)
        dispatch_idx = text.find("loc_3BBE:")
        self.assertNotEqual(dispatch_idx, -1)
        dispatch_window = text[dispatch_idx:text.find("dat_3C12:", dispatch_idx)]
        self.assertIn("lea.l dat_3C12(pc,d1.w),a2", text)
        self.assertIn("adda.w (a2),a2", text)
        self.assertIn("jmp (a2)", dispatch_window)
        self.assertNotIn("jmp (a2) ; CANDIDATE: indirect_jump index unresolved", dispatch_window)
        self.assertIn("dat_3C12:", text)
        self.assertIn("DC.W    loc_3D00-*", text)
        self.assertIn("DC.W    loc_3C86-*", text)
        self.assertIn("DC.W    loc_3C5C-*", text)
        self.assertIn("DC.W    loc_3E98-*", text)

    def test_disassemble_genam_flags_current_relative_branches_as_violations(self) -> None:
        result = subprocess.run(
            [str(self.file_exe), "disassemble-file", "--syntax", "genam", "amiga-hunk", str(GENAM_BIN)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        branch_relative = re.compile(r"^\s*b[a-z]+\.[bwlsg]?\s+\*[+-]?\d*")
        bare = [line for line in result.stdout.splitlines()
                if branch_relative.search(line) and "VIOLATION:" not in line]
        self.assertEqual([], bare)

    def test_disassemble_bin_gen_flags_current_relative_branches_as_violations(self) -> None:
        result = subprocess.run(
            [str(self.file_exe), "disassemble-file", "--syntax", "genam", "atari-st", str(BIN_GEN_BIN)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        branch_relative = re.compile(r"^\s*b[a-z]+\.[bwlsg]?\s+\*[+-]?\d*")
        bare = [line for line in result.stdout.splitlines()
                if branch_relative.search(line) and "VIOLATION:" not in line]
        self.assertEqual([], bare)

    def test_genam_latest_fixture_matches_current_disassembly(self) -> None:
        self.assertTrue(GENAM_LATEST.exists(), GENAM_LATEST)
        self.assertEqual(self._disassemble_real_path("amiga-hunk", GENAM_BIN), GENAM_LATEST.read_text(encoding="utf-8"))

    def test_bin_gen_latest_fixture_matches_current_disassembly(self) -> None:
        self.assertTrue(BIN_GEN_LATEST.exists(), BIN_GEN_LATEST)
        self.assertEqual(self._disassemble_real_path("atari-st", BIN_GEN_BIN), BIN_GEN_LATEST.read_text(encoding="utf-8"))

    def test_genam_benchmark_matches_current_stats(self) -> None:
        self.assertTrue(GENAM_BENCHMARK.exists(), GENAM_BENCHMARK)
        current = self._normalized_benchmark(self._benchmark_real_path("amiga-hunk", GENAM_BIN))
        committed = self._normalized_benchmark(json.loads(GENAM_BENCHMARK.read_text(encoding="utf-8")))
        self.assertEqual(current, committed)

    def test_bin_gen_benchmark_matches_current_stats(self) -> None:
        self.assertTrue(BIN_GEN_BENCHMARK.exists(), BIN_GEN_BENCHMARK)
        current = self._normalized_benchmark(self._benchmark_real_path("atari-st", BIN_GEN_BIN))
        committed = self._normalized_benchmark(json.loads(BIN_GEN_BENCHMARK.read_text(encoding="utf-8")))
        self.assertEqual(current, committed)

    def test_genam_latest_roundtrips_exactly_via_our_assembler(self) -> None:
        self.assertTrue(GENAM_BIN.exists(), GENAM_BIN)
        self.assertTrue(GENAM_LATEST.exists(), GENAM_LATEST)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            rebuilt_path = Path(tmp) / "GenAm.roundtrip.exe"
            assemble = self._assemble_latest_with_our_assembler(
                "amiga-hunk", GENAM_INCLUDE_DIR, GENAM_LATEST, rebuilt_path
            )
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            self.assertEqual(rebuilt_path.read_bytes(), GENAM_BIN.read_bytes())

    def test_genam_latest_roundtrips_via_vasm_with_matching_file_shape(self) -> None:
        vasm = ROOT / "ext" / "vasm" / "vasmm68k_mot.exe"
        self.assertTrue(vasm.exists(), vasm)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            rebuilt_path = Path(tmp) / "GenAm.roundtrip.exe"
            source_path = Path(tmp) / "GenAm.vasm.s"
            source_path.write_text(self._disassemble_real_path("amiga-hunk", GENAM_BIN, syntax="vasm"), encoding="utf-8")
            assemble = subprocess.run(
                [str(vasm), "-m68000", "-Fhunkexe", "-no-opt", "-quiet", "-o", str(rebuilt_path), str(source_path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            original = self._normalized_oracle_summary(self._inspect_file_path("amiga-hunk", GENAM_BIN))
            rebuilt = self._normalized_oracle_summary(self._inspect_file_path("amiga-hunk", rebuilt_path))
            self.assertEqual(rebuilt, original)

    def test_genam_latest_is_parseable_by_our_assembler(self) -> None:
        self.assertTrue(GENAM_LATEST.exists(), GENAM_LATEST)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            rendered_path = Path(tmp) / "GenAm.rendered.s"
            render = subprocess.run(
                [
                    str(self.asm_exe),
                    "render-source-file",
                    "--syntax",
                    "genam",
                    "--include-dir",
                    str(GENAM_INCLUDE_DIR),
                    str(GENAM_LATEST),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(render.returncode, 0, render.stderr)
            rendered_path.write_text(render.stdout, encoding="utf-8")
            self.assertGreater(rendered_path.stat().st_size, 0)

    def test_disassemble_file_keeps_fallthrough_code_after_known_taken_conditional(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "known_taken.prg"
            code = bytes.fromhex("760e0c03000f650270624e75")
            path.write_bytes(make_synthetic_atari_prg(code, b"", 0))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("bcs.b loc_000A", result.stdout)
            self.assertIn("loc_000A:", result.stdout)
            self.assertIn("moveq.l #98,d0", result.stdout)
            self.assertNotIn("DC.B    $70,$62", result.stdout)

    def test_disassemble_file_emits_atari_comment_head_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.prg"
            path.write_bytes(make_synthetic_atari_prg(b"\x4E\x75", b"", 0, program_flags=7))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("COMMENT HEAD=$7", result.stdout)
            self.assertNotIn("PRGFLAGS", result.stdout)

    def test_disassemble_file_symbols_atari_trap_opcode_immediate(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "trap_symbol.prg"
            code = (
                self._assemble_line_hex("68000", "move.w #25,-(sp)")
                + self._assemble_line_hex("68000", "trap #1")
                + self._assemble_line_hex("68000", "addq.l #2,sp")
                + self._assemble_line_hex("68000", "rts")
            )
            path.write_bytes(make_synthetic_atari_prg(code, b"", 0))
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("GEMDOS_Dgetdrv EQU 25", result.stdout)
            self.assertIn("move.w #GEMDOS_Dgetdrv,-(a7)", result.stdout)
            self.assertIn("trap #1 ; KNOWN: direct OS call GEMDOS_Dgetdrv pop 2 return d0.l", result.stdout)
            self.assertIn("addq.l #2,a7 ; KNOWN: stack cleanup for GEMDOS_Dgetdrv pop 2", result.stdout)

    def test_disassemble_real_bin_gen_emits_atari_os_symbols(self) -> None:
        text = self._disassemble_real_path("atari-st", BIN_GEN_BIN, "genam")
        self.assertIn("GEMDOS_Cconout EQU 2", text)
        self.assertIn("GEMDOS_Cconrs EQU 10", text)
        self.assertIn("GEMDOS_Fwrite EQU 64", text)
        self.assertIn("GEMDOS_Crawcin EQU 7", text)
        self.assertIn("GEMDOS_Super EQU 32", text)
        self.assertIn("GEMDOS_Tgetdate EQU 42", text)
        self.assertIn("GEMDOS_Tgettime EQU 44", text)
        self.assertIn("GEMDOS_Pterm EQU 76", text)
        self.assertIn("XBIOS_Supexec EQU 38", text)
        self.assertIn("move.w #GEMDOS_Cconout,-(a7)", text)
        self.assertIn("trap #1 ; KNOWN: direct OS call GEMDOS_Cconout", text)
        self.assertIn("move.w #GEMDOS_Cconrs,-(a7)", text)
        self.assertIn("trap #1 ; KNOWN: direct OS call GEMDOS_Cconrs", text)
        self.assertIn("move.w #GEMDOS_Super,-(a7)", text)
        self.assertIn("trap #1 ; KNOWN: direct OS call GEMDOS_Super", text)
        self.assertIn("move.w #GEMDOS_Pterm,-(a7)", text)
        self.assertIn("trap #1 ; KNOWN: direct OS call GEMDOS_Pterm", text)
        self.assertIn("trap #14 ; KNOWN: direct OS call XBIOS_Supexec pop 6 return d0.l", text)
        self.assertIn("addq.l #6,a7 ; KNOWN: stack cleanup for XBIOS_Supexec pop 6", text)
        self.assertIn("move.w #GEMDOS_Crawcin,(a7)", text)
        self.assertIn("trap #1 ; KNOWN: direct OS call GEMDOS_Crawcin pop 2 return d0.l", text)
        self.assertIn("move.w #GEMDOS_Tgetdate,-(a7)", text)
        self.assertIn("trap #1 ; KNOWN: direct OS call GEMDOS_Tgetdate", text)
        self.assertIn("move.w #GEMDOS_Tgettime,-(a7)", text)
        self.assertIn("trap #1 ; KNOWN: direct OS call GEMDOS_Tgettime", text)
        self.assertIn("movea.l #dat_B65C,a0", text)
        self.assertNotIn("NOTE: preserved exact bytes for non-canonical movea immediate encoding", text)
        self.assertNotIn("DC.W    $207c", text)

    def test_bin_gen_latest_roundtrips_exactly_via_our_assembler(self) -> None:
        self.assertTrue(BIN_GEN_BIN.exists(), BIN_GEN_BIN)
        self.assertTrue(BIN_GEN_LATEST.exists(), BIN_GEN_LATEST)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            rebuilt_path = Path(tmp) / "BIN_GEN.roundtrip.ttp"
            assemble = self._assemble_latest_with_our_assembler(
                "atari-st", BIN_GEN_INCLUDE_DIR, BIN_GEN_LATEST, rebuilt_path
            )
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            self.assertEqual(rebuilt_path.read_bytes(), BIN_GEN_BIN.read_bytes())

    def test_bin_gen_latest_roundtrips_via_vasm_with_matching_file_shape(self) -> None:
        vasm = ROOT / "ext" / "vasm" / "vasmm68k_mot.exe"
        self.assertTrue(BIN_GEN_BIN.exists(), BIN_GEN_BIN)
        self.assertTrue(vasm.exists(), vasm)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            rebuilt_path = Path(tmp) / "BIN_GEN.roundtrip.ttp"
            source_path = Path(tmp) / "BIN_GEN.vasm.s"
            source_path.write_text(self._disassemble_real_path("atari-st", BIN_GEN_BIN, syntax="vasm"), encoding="utf-8")
            assemble = subprocess.run(
                [str(vasm), "-Ftos", "-nosym", "-quiet", "-o", str(rebuilt_path), str(source_path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            original = self._normalized_oracle_summary(self._inspect_file_path("atari-st", BIN_GEN_BIN))
            rebuilt = self._normalized_oracle_summary(self._inspect_file_path("atari-st", rebuilt_path))
            self.assertEqual(rebuilt, original)

    def test_bin_gen_latest_is_parseable_by_our_assembler(self) -> None:
        self.assertTrue(BIN_GEN_BIN.exists(), BIN_GEN_BIN)
        self.assertTrue(BIN_GEN_LATEST.exists(), BIN_GEN_LATEST)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            rendered_path = Path(tmp) / "BIN_GEN.rendered.s"
            render = subprocess.run(
                [
                    str(self.asm_exe),
                    "render-source-file",
                    "--syntax",
                    "genam",
                    "--include-dir",
                    str(BIN_GEN_INCLUDE_DIR),
                    str(BIN_GEN_LATEST),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(render.returncode, 0, render.stderr)
            rendered_path.write_text(render.stdout, encoding="utf-8")
            self.assertGreater(rendered_path.stat().st_size, 0)

    def test_render_source_file_preserves_source_names_when_generated_names_are_disabled(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.s"
            path.write_text("SECTION code,code\nstart:\n    bra.b start\n", encoding="utf-8")
            result = subprocess.run(
                [
                    str(self.asm_exe),
                    "render-source-file",
                    "--no-generated-names",
                    "--include-dir",
                    str(GENAM_INCLUDE_DIR),
                    str(path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("start:", result.stdout)
            self.assertNotIn("L_0000:", result.stdout)

    def test_render_source_file_syntax_mode_changes_short_branch_suffix(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.s"
            path.write_text("SECTION code,code\nstart:\n    bra.b start\n", encoding="utf-8")
            canonical = subprocess.run(
                [
                    str(self.asm_exe),
                    "render-source-file",
                    "--syntax",
                    "canonical",
                    "--include-dir",
                    str(GENAM_INCLUDE_DIR),
                    str(path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(canonical.returncode, 0, canonical.stderr)
            self.assertIn("bra.b start", canonical.stdout)

            genam = subprocess.run(
                [
                    str(self.asm_exe),
                    "render-source-file",
                    "--syntax",
                    "genam",
                    "--include-dir",
                    str(GENAM_INCLUDE_DIR),
                    str(path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(genam.returncode, 0, genam.stderr)
            self.assertIn("bra.s start", genam.stdout)

    def test_render_source_file_preserves_movem_predecrement_semantics(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.s"
            path.write_text("SECTION code,code\nstart:\n    movem.l d1-d2/a0-a2,-(sp)\n", encoding="utf-8")
            result = subprocess.run(
                [
                    str(self.asm_exe),
                    "render-source-file",
                    "--include-dir",
                    str(GENAM_INCLUDE_DIR),
                    str(path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("movem.l d1-d2/a0-a2,-(a7)", result.stdout)

    def test_analyze_file_reports_cfg_for_real_amiga_fixture(self) -> None:
        fixture_path = FIXTURE_DIR / "vasm_hunkexe_databss.exe"
        result = subprocess.run(
            [str(self.file_exe), "analyze-file", "amiga-hunk", str(fixture_path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["file_kind"], 1)
        self.assertEqual(payload["section_count"], 2)
        self.assertEqual(payload["sections"][0]["block_count"], 1)
        self.assertEqual(payload["sections"][0]["edge_count"], 1)
        self.assertEqual(payload["sections"][0]["blocks"][0]["start_offset"], 0)
        self.assertEqual(payload["sections"][0]["blocks"][0]["end_offset"], 4)
        self.assertEqual(payload["sections"][0]["edges"][0]["kind"], 5)
        self.assertEqual(payload["sections"][1]["block_count"], 0)

    def test_analyze_file_reports_object_section_shape_for_real_amiga_fixture(self) -> None:
        fixture_path = FIXTURE_DIR / "vasm_hunk_object.o"
        result = subprocess.run(
            [str(self.file_exe), "analyze-file", "amiga-hunk", str(fixture_path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["file_kind"], 2)
        self.assertEqual(payload["section_count"], 3)
        self.assertEqual(payload["sections"][0]["section_kind"], 1)
        self.assertEqual(payload["sections"][0]["label_count"], 1)
        self.assertEqual(payload["sections"][0]["block_count"], 1)
        self.assertEqual(payload["sections"][1]["section_kind"], 2)
        self.assertEqual(payload["sections"][1]["block_count"], 0)
        self.assertEqual(payload["sections"][2]["section_kind"], 3)
        self.assertEqual(payload["sections"][2]["block_count"], 0)

    def test_analyze_file_splits_blocks_on_branching_synthetic_hunk(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "branch.exe"
            path.write_bytes(make_synthetic_hunkexe(code_data=b"\x60\x02\x00\x00\x4E\x75\x00\x00"))
            result = subprocess.run(
                [str(self.file_exe), "analyze-file", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["sections"][0]["block_count"], 2)
            self.assertEqual(payload["sections"][0]["edge_count"], 2)
            self.assertEqual(payload["sections"][0]["blocks"][0]["start_offset"], 0)
            self.assertEqual(payload["sections"][0]["blocks"][0]["end_offset"], 2)
            self.assertEqual(payload["sections"][0]["blocks"][1]["start_offset"], 4)
            self.assertEqual(payload["sections"][0]["blocks"][1]["end_offset"], 6)
            self.assertEqual(payload["sections"][0]["edges"][0]["kind"], 4)
            self.assertEqual(payload["sections"][0]["edges"][0]["target_offset"], 4)
            self.assertEqual(payload["sections"][0]["edges"][1]["kind"], 5)

    def test_analyze_file_reports_required_cpu_under_permissive_limit(self) -> None:
        code = self._assemble_line_hex("68020", "moves.w d0,(a0)") + self._assemble_line_hex("68000", "rts")
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "cpu20.exe"
            path.write_bytes(make_synthetic_hunkexe(code_data=code))
            result = subprocess.run(
                [str(self.file_exe), "analyze-file", "--max-cpu", "68000", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["analysis_policy"]["max_cpu"], 0)
            self.assertGreater(payload["findings"]["required_cpu"], 0)
            self.assertGreater(payload["findings"]["cpu_violation_count"], 0)
            self.assertGreater(payload["sections"][0]["violation_count"], 0)
            self.assertTrue(any("beyond policy max 68000" in v["message"] for v in payload["sections"][0]["violations"]))


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_HEAVY_UNIT_TESTS") == "1":
        return tests
    return unittest.TestSuite()
