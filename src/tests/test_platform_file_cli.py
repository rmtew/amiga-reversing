from __future__ import annotations

import json
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
