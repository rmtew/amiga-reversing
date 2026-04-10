from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.tests._build_helpers import require_built_tools
from src.tests._platform_backend_test_utils import FIXTURE_DIR
from src.tests._platform_backend_test_utils import make_synthetic_atari_prg
from src.tests._platform_backend_test_utils import make_synthetic_hunkexe
ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
EXE = BUILD_DIR / "platform_file_cli.exe"
ASM_EXE = BUILD_DIR / "m68k_assembler_app.exe"
AMIGA_INCLUDE_DIR = ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"


class PlatformFileCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_built_tools()

    def _run_cli(self, platform_name: str, suffix: str, data: bytes) -> dict[str, object]:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / f"sample{suffix}"
            path.write_bytes(data)
            result = subprocess.run(
                [str(EXE), "inspect-file", platform_name, str(path)],
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
            [str(EXE), "inspect-file", platform_name, str(path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

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
            [str(ASM_EXE), "assemble-line", "--cpu", cpu, text],
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
                [str(EXE), "disassemble-file", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(default_result.returncode, 0, default_result.stderr)
            self.assertIn("loc_0000:", default_result.stdout)

            fallback_result = subprocess.run(
                [str(EXE), "disassemble-file", "--no-generated-names", "amiga-hunk", str(path)],
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
                    str(EXE),
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
                [str(EXE), "disassemble-file", "--syntax", "canonical", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(canonical.returncode, 0, canonical.stderr)
            self.assertIn("bra.b", canonical.stdout)

            genam = subprocess.run(
                [str(EXE), "disassemble-file", "--syntax", "genam", "amiga-hunk", str(path)],
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
                [str(EXE), "disassemble-file", "atari-st", str(path)],
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
                [str(EXE), "disassemble-file", "atari-st", str(path)],
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
                [str(EXE), "disassemble-file", "atari-st", str(path)],
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
                [str(EXE), "disassemble-file", "atari-st", str(path)],
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
                [str(EXE), "disassemble-file", "atari-st", str(path)],
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
                [str(EXE), "disassemble-file", "atari-st", str(path)],
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

    def test_disassemble_file_preserves_noncanonical_byte_immediate_words(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "byteimm.prg"
            path.write_bytes(make_synthetic_atari_prg(bytes.fromhex("00244e754e75"), b"", 0))
            result = subprocess.run(
                [str(EXE), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "DC.W    $0024,$4e75 ; NOTE: preserved exact bytes for non-canonical byte-immediate encoding: ori.b #117,-(a4)",
                result.stdout,
            )
            self.assertNotIn("\n    ori.b #117,-(a4)\n", result.stdout)

    def test_disassemble_genam_resolves_real_jump_table_dispatch_site(self) -> None:
        path = ROOT / "bin" / "GenAm"
        result = subprocess.run(
            [str(EXE), "disassemble-file", "--syntax", "genam", "amiga-hunk", str(path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        text = result.stdout
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
        self.assertNotIn("move.b $4(pc,d1.w),d1", text)
        self.assertNotIn("move.b $18(pc,d1.w),(a4)+", text)
        self.assertNotIn("dat_0EA4:", text)
        self.assertNotIn("loc_0EA4:", text)
        self.assertNotIn("DC.W    loc_12B8-dat_0EA2", text)
        self.assertNotIn("DC.W    loc_24B6-dat_0EA2", text)
        self.assertNotIn("DC.W    loc_22B6-dat_0EA2", text)
        self.assertNotIn("DC.W    loc_22B4-dat_0EA2", text)
        self.assertNotIn("lea.l dat_0EA4(pc),a1", text)
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

    def test_disassemble_genam_resolves_entry_relative_jump_table_dispatch_site(self) -> None:
        path = ROOT / "bin" / "GenAm"
        result = subprocess.run(
            [str(EXE), "disassemble-file", "--syntax", "genam", "amiga-hunk", str(path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        text = result.stdout
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
        path = ROOT / "bin" / "GenAm"
        result = subprocess.run(
            [str(EXE), "disassemble-file", "--syntax", "genam", "amiga-hunk", str(path)],
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

    def test_disassemble_genam_roundtrips_via_vasm_with_matching_section_bytes_and_fixups(self) -> None:
        path = ROOT / "bin" / "GenAm"
        vasm = ROOT / "ext" / "vasm" / "vasmm68k_mot.exe"
        self.assertTrue(vasm.exists(), vasm)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            source_path = Path(tmp) / "GenAm.roundtrip.s"
            rebuilt_path = Path(tmp) / "GenAm.roundtrip.exe"
            disassemble = subprocess.run(
                [str(EXE), "disassemble-file", "--syntax", "genam", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(disassemble.returncode, 0, disassemble.stderr)
            source_path.write_text(disassemble.stdout, encoding="utf-8")
            assemble = subprocess.run(
                [str(vasm), "-m68000", "-Fhunkexe", "-no-opt", "-quiet", "-o", str(rebuilt_path), str(source_path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            original = self._normalized_file_summary(self._inspect_file_path("amiga-hunk", path))
            rebuilt = self._normalized_file_summary(self._inspect_file_path("amiga-hunk", rebuilt_path))
            self.assertEqual(rebuilt, original)

    def test_disassemble_file_keeps_fallthrough_code_after_known_taken_conditional(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "known_taken.prg"
            code = bytes.fromhex("760e0c03000f650270624e75")
            path.write_bytes(make_synthetic_atari_prg(code, b"", 0))
            result = subprocess.run(
                [str(EXE), "disassemble-file", "atari-st", str(path)],
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
                [str(EXE), "disassemble-file", "atari-st", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("COMMENT HEAD=$7", result.stdout)
            self.assertNotIn("PRGFLAGS", result.stdout)

    def test_render_source_file_preserves_source_names_when_generated_names_are_disabled(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.s"
            path.write_text("SECTION code,code\nstart:\n    bra.b start\n", encoding="utf-8")
            result = subprocess.run(
                [
                    str(ASM_EXE),
                    "render-source-file",
                    "--no-generated-names",
                    "--include-dir",
                    str(AMIGA_INCLUDE_DIR),
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
                    str(ASM_EXE),
                    "render-source-file",
                    "--syntax",
                    "canonical",
                    "--include-dir",
                    str(AMIGA_INCLUDE_DIR),
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
                    str(ASM_EXE),
                    "render-source-file",
                    "--syntax",
                    "genam",
                    "--include-dir",
                    str(AMIGA_INCLUDE_DIR),
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
                    str(ASM_EXE),
                    "render-source-file",
                    "--include-dir",
                    str(AMIGA_INCLUDE_DIR),
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
            [str(EXE), "analyze-file", "amiga-hunk", str(fixture_path)],
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
            [str(EXE), "analyze-file", "amiga-hunk", str(fixture_path)],
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
                [str(EXE), "analyze-file", "amiga-hunk", str(path)],
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
                [str(EXE), "analyze-file", "--max-cpu", "68000", "amiga-hunk", str(path)],
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
