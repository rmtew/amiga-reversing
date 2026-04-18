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
AMIGA_RUNTIME_HEADER = ROOT / "src" / "generated" / "amiga_os_runtime.h"
AMIGA_RUNTIME_SOURCE = ROOT / "src" / "generated" / "amiga_os_runtime.c"
ATARI_RUNTIME_HEADER = ROOT / "src" / "generated" / "atari_st_os_runtime.h"
ATARI_RUNTIME_SOURCE = ROOT / "src" / "generated" / "atari_st_os_runtime.c"
AMIGA_ASL_ALLOC_REQUEST_SOURCE = """\
_LVOOpenLibrary EQU -552
_LVOAllocAslRequest EQU -48
app_AslBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l asl_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_AslBase(a6)
    move.l a6,-(a7)
    movea.l app_AslBase(a6),a6
    moveq.l #0,d0
    moveq.l #0,d1
    jsr _LVOAllocAslRequest(a6)
    movea.l (a7)+,a6
    rts

asl_name:
    DC.B "asl.library",0
    EVEN
"""


class PlatformFileCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_built_tools()
        cls.file_exe = prepare_test_exe(EXE)
        cls.asm_exe = prepare_test_exe(ASM_EXE)
        cls._real_disassembly_cache: dict[tuple[str, str, str], str] = {}
        cls._real_benchmark_cache: dict[tuple[str, str], dict[str, object]] = {}
        cls._real_inspect_cache: dict[tuple[str, str], dict[str, object]] = {}
        cls._fixture_text_cache: dict[str, str] = {}
        cls._fixture_json_cache: dict[str, dict[str, object]] = {}

    @classmethod
    def _is_cached_real_path(cls, path: Path) -> bool:
        try:
            resolved = path.resolve()
        except OSError:
            return False
        return resolved in {GENAM_BIN.resolve(), BIN_GEN_BIN.resolve()}

    @classmethod
    def _read_fixture_text(cls, path: Path) -> str:
        cache_key = str(path.resolve())
        if cache_key not in cls._fixture_text_cache:
            cls._fixture_text_cache[cache_key] = path.read_text(encoding="utf-8")
        return cls._fixture_text_cache[cache_key]

    @classmethod
    def _read_fixture_json(cls, path: Path) -> dict[str, object]:
        cache_key = str(path.resolve())
        if cache_key not in cls._fixture_json_cache:
            cls._fixture_json_cache[cache_key] = json.loads(path.read_text(encoding="utf-8"))
        return dict(cls._fixture_json_cache[cache_key])

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
        cache_key = (platform_name, str(path.resolve()))
        if self._is_cached_real_path(path) and cache_key in self._real_inspect_cache:
            return dict(self._real_inspect_cache[cache_key])
        result = subprocess.run(
            [str(self.file_exe), "inspect-file", platform_name, str(path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        if self._is_cached_real_path(path):
            self._real_inspect_cache[cache_key] = payload
        return dict(payload)

    def _analyze_file_path(self, platform_name: str, path: Path) -> dict[str, object]:
        result = subprocess.run(
            [str(self.file_exe), "analyze-file", platform_name, str(path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _source_map_file_path(self, platform_name: str, path: Path) -> dict[str, object]:
        result = subprocess.run(
            [str(self.file_exe), "source-map-file", platform_name, str(path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _listing_rows_file_path(
        self, platform_name: str, path: Path, metadata_path: Path | None = None
    ) -> dict[str, object]:
        command = [str(self.file_exe), "listing-rows-file"]
        if metadata_path is not None:
            command.extend(["--target-metadata", str(metadata_path)])
        command.extend([platform_name, str(path)])
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _effective_policy_file_path(
        self, platform_name: str, path: Path, metadata_path: Path | None = None
    ) -> dict[str, object]:
        command = [str(self.file_exe), "effective-policy-file"]
        if metadata_path is not None:
            command.extend(["--target-metadata", str(metadata_path)])
        command.extend([platform_name, str(path)])
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _raw_cli_json(self, command: str, platform_name: str, data: bytes, entry_offset: int,
                      *options: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "raw.bin"
            path.write_bytes(data)
            result = subprocess.run(
                [str(self.file_exe), command, *options, platform_name, str(path), str(entry_offset)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

    def _raw_disassemble(self, platform_name: str, data: bytes, entry_offset: int) -> str:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "raw.bin"
            path.write_bytes(data)
            result = subprocess.run(
                [str(self.file_exe), "disassemble-raw", "--syntax", "vasm", platform_name, str(path), str(entry_offset)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout

    def _type_catalog(self, platform_name: str) -> list[dict[str, object]]:
        result = subprocess.run(
            [str(self.file_exe), "type-catalog", platform_name],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _naming_catalog(self, platform_name: str) -> dict[str, object]:
        result = subprocess.run(
            [str(self.file_exe), "naming-catalog", platform_name],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _os_metadata_catalog(self, platform_name: str) -> dict[str, object]:
        result = subprocess.run(
            [str(self.file_exe), "os-metadata-catalog", platform_name],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _api_input_struct(self, platform_name: str, library: str, function: str, input_name: str,
                          struct_name: str) -> dict[str, object]:
        result = subprocess.run(
            [str(self.file_exe), "api-input-struct", platform_name, library, function, input_name, struct_name],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _disassemble_real_path(self, platform_name: str, path: Path, syntax: str = "genam") -> str:
        cache_key = (platform_name, str(path.resolve()), syntax)
        if self._is_cached_real_path(path) and cache_key in self._real_disassembly_cache:
            return self._real_disassembly_cache[cache_key]
        if self._is_cached_real_path(path) and syntax == "vasm":
            self._disassemble_real_path_with_benchmark(platform_name, path)
            if cache_key in self._real_disassembly_cache:
                return self._real_disassembly_cache[cache_key]
        if self._is_cached_real_path(path) and syntax == "genam":
            text, _ = self._disassemble_real_path_with_benchmark(platform_name, path)
            return text
        result = subprocess.run(
            [str(self.file_exe), "disassemble-file", "--syntax", syntax, platform_name, str(path)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        if self._is_cached_real_path(path):
            self._real_disassembly_cache[cache_key] = result.stdout
        return result.stdout

    def _disassemble_real_path_with_benchmark(self, platform_name: str, path: Path) -> tuple[str, dict[str, object]]:
        cache_key = (platform_name, str(path.resolve()), "genam")
        benchmark_cache_key = (platform_name, str(path.resolve()))
        if (
            self._is_cached_real_path(path)
            and cache_key in self._real_disassembly_cache
            and benchmark_cache_key in self._real_benchmark_cache
        ):
            return self._real_disassembly_cache[cache_key], dict(self._real_benchmark_cache[benchmark_cache_key])
        try:
            cli_path = path.relative_to(ROOT).as_posix()
        except ValueError:
            cli_path = str(path)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            benchmark_path = Path(tmp) / "benchmark.json"
            vasm_path = Path(tmp) / "source.vasm.s"
            command = [
                str(self.file_exe),
                "disassemble-file",
                "--syntax",
                "genam",
                "--benchmark-json-out",
                str(benchmark_path),
            ]
            command.extend(["--also-syntax-output", "vasm", str(vasm_path)])
            command.extend([platform_name, cli_path])
            result = subprocess.run(
                command,
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
            vasm_text = vasm_path.read_text(encoding="utf-8") if vasm_path.exists() else None
        if self._is_cached_real_path(path):
            self._real_disassembly_cache[cache_key] = result.stdout
            if vasm_text is not None:
                self._real_disassembly_cache[(platform_name, str(path.resolve()), "vasm")] = vasm_text
            self._real_benchmark_cache[benchmark_cache_key] = payload
        return result.stdout, dict(payload)

    def _benchmark_real_path(self, platform_name: str, path: Path) -> dict[str, object]:
        cache_key = (platform_name, str(path.resolve()))
        if self._is_cached_real_path(path) and cache_key in self._real_benchmark_cache:
            return dict(self._real_benchmark_cache[cache_key])
        _, payload = self._disassemble_real_path_with_benchmark(platform_name, path)
        return payload

    def _normalized_benchmark(self, payload: dict[str, object]) -> dict[str, object]:
        sections = []
        for section in payload["sections"]:
            normalized_section = dict(section)
            normalized_section.pop("timing", None)
            sections.append(normalized_section)
        return {
            "benchmark_version": payload["benchmark_version"],
            "platform": payload["platform"],
            "path": payload["path"],
            "file": payload["file"],
            "analysis": payload["analysis"],
            "render": payload["render"],
            "sections": sections,
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

    def _assemble_source_text_with_our_assembler(self, backend: str, include_dir: Path, source_text: str,
                                                 output_path: Path) -> subprocess.CompletedProcess[str]:
        source_path = output_path.with_suffix(".s")
        source_path.write_text(source_text, encoding="utf-8")
        return self._assemble_latest_with_our_assembler(backend, include_dir, source_path, output_path)

    def _assemble_synthetic_amiga_hunk_source(self, source_text: str,
                                              output_path: Path) -> subprocess.CompletedProcess[str]:
        source_path = output_path.with_suffix(".s")
        padded_source = source_text
        for _ in range(3):
            source_path.write_text(padded_source, encoding="utf-8")
            result = self._assemble_latest_with_our_assembler("amiga-hunk", GENAM_INCLUDE_DIR, source_path, output_path)
            if result.returncode == 0:
                return result
            if "Current Amiga hunk writer requires longword-aligned section sizes" not in result.stderr:
                return result
            padded_source += "    DC.W 0\n"
        return result

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

    def test_source_map_file_emits_statement_offsets(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.exe"
            path.write_bytes(make_synthetic_hunkexe())
            actual = self._source_map_file_path("amiga-hunk", path)

        self.assertEqual(actual["section_count"], 2)
        first_section = actual["sections"][0]
        self.assertEqual(first_section["section_index"], 0)
        statements = first_section["statements"]
        self.assertGreater(len(statements), 0)
        instruction = next(stmt for stmt in statements if stmt["kind"] == "instruction")
        self.assertIsInstance(instruction["offset"], int)
        self.assertGreater(instruction["byte_count"], 0)
        self.assertEqual(instruction["rendered_line_count"], 1)

    def test_listing_rows_file_emits_rows_with_offsets(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.exe"
            path.write_bytes(make_synthetic_hunkexe())
            actual = self._listing_rows_file_path("amiga-hunk", path)

        rows = actual["rows"]
        instruction = next(row for row in rows if row["kind"] == "instruction")
        self.assertIsInstance(instruction["addr"], int)
        self.assertEqual(instruction["bytes"], "4e75")
        self.assertEqual(instruction["source_context"], {"kind": "c-instruction", "hunk_index": 0})

    def test_analyze_raw_uses_entry_offset(self) -> None:
        payload = self._raw_cli_json("analyze-raw", "amiga-raw", b"\0" * 12 + b"\x4e\x75", 12)
        section = payload["sections"][0]
        self.assertEqual(section["block_count"], 1)
        self.assertEqual(section["blocks"][0]["start_offset"], 12)

    def test_analyze_raw_accepts_additional_entry_offsets(self) -> None:
        payload = self._raw_cli_json(
            "analyze-raw",
            "amiga-raw",
            b"\0" * 12 + b"\x4e\x75" + b"\0" * 6 + b"\x4e\x75",
            12,
            "--entry-offset",
            "20",
        )
        starts = {block["start_offset"] for block in payload["sections"][0]["blocks"]}
        self.assertIn(12, starts)
        self.assertIn(20, starts)

    def test_listing_rows_raw_emits_header_as_data_and_entry_as_code(self) -> None:
        rows = self._raw_cli_json("listing-rows-raw", "amiga-raw", b"\0" * 12 + b"\x4e\x75", 12)["rows"]
        text = "".join(row["text"] for row in rows)
        self.assertIn("dc.b", text.lower())
        self.assertIn("rts", text.lower())

    def test_disassemble_raw_uses_entry_offset(self) -> None:
        text = self._raw_disassemble("amiga-raw", b"\0" * 12 + b"\x4e\x75", 12)
        self.assertIn("rts", text.lower())

    def test_analyze_raw_entry_register_seed_resolves_bootblock_exec_call(self) -> None:
        path = (
            ROOT
            / "targets"
            / "amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5"
            / "targets"
            / "amiga_raw_bootblock"
            / "binary.bin"
        )
        result = subprocess.run(
            [
                str(self.file_exe),
                "analyze-raw",
                "--entry-register-seed",
                "*:A6:library_base:exec.library:LIB:",
                "amiga-raw",
                str(path),
                "12",
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        calls = payload["sections"][0]["recovered_platform_calls"]
        self.assertEqual(calls[0]["library_name"], "exec.library")
        self.assertEqual(calls[0]["function_name"], "FindResident")

    def test_analyze_raw_target_metadata_resolves_seed_and_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            raw_path = Path(tmp) / "raw.bin"
            metadata_path = Path(tmp) / "target_metadata.json"
            raw_path.write_bytes(b"\0" * 12 + b"\x4e\x75" + b"\0" * 6 + b"\x4e\x75")
            metadata_path.write_text(
                """{
  "entry_register_seeds": [
    {"entry_offset": null, "register": "A6", "kind": "library_base", "library_name": "exec.library", "struct_name": "LIB", "context_name": null}
  ],
  "seeded_code_entrypoints": [
    {"addr": 20, "hunk": 0, "name": "extra_entry"}
  ]
}
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "analyze-raw",
                    "--target-metadata",
                    str(metadata_path),
                    "amiga-raw",
                    str(raw_path),
                    "12",
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        starts = {block["start_offset"] for block in payload["sections"][0]["blocks"]}
        self.assertIn(12, starts)
        self.assertIn(20, starts)
        self.assertEqual(payload["analysis_policy"]["entry_point_count"], 1)

    def test_effective_policy_raw_reports_metadata_seeds_and_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            raw_path = Path(tmp) / "raw.bin"
            metadata_path = Path(tmp) / "target_metadata.json"
            raw_path.write_bytes(b"\0" * 12 + b"\x4e\x75" + b"\0" * 6 + b"\x4e\x75")
            metadata_path.write_text(
                """{
  "target_type": "bootblock",
  "entry_register_seeds": [
    {"entry_offset": null, "register": "A6", "kind": "library_base", "library_name": "exec.library", "struct_name": "LIB", "context_name": null}
  ],
  "seeded_code_entrypoints": [
    {"addr": 20, "hunk": 0, "name": "extra_entry"}
  ]
}
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "effective-policy-raw",
                    "--target-metadata",
                    str(metadata_path),
                    "amiga-raw",
                    str(raw_path),
                    "12",
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        policy = payload["analysis_policy"]
        self.assertEqual(payload["source_kind"], "raw")
        self.assertEqual(payload["target_type"], "bootblock")
        self.assertEqual(payload["analysis_start"], 12)
        self.assertIn({"section_index": 0, "offset": 20}, policy["entrypoints"])
        self.assertTrue(
            any(
                seed["section_index"] == 0
                and seed["entry_offset"] is None
                and seed["register"] == "A6"
                and seed["kind"] == "library_base"
                and seed["name"] == "exec.library"
                and seed["type_name"] == "LIB"
                for seed in policy["register_seeds"]
            )
        )

    def test_disassemble_file_scopes_metadata_register_seeds_to_first_hunk_by_default(self) -> None:
        source = """\
SECTION first,code
    rts
    DC.W 0
SECTION second,code
    rts
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "metadata_seed_scope.exe"
            metadata_path = Path(tmp) / "target_metadata.json"
            metadata_path.write_text(
                """{
  "entry_register_seeds": [
    {"entry_offset": 0, "register": "A6", "kind": "library_base", "library_name": "exec.library", "struct_name": "LIB", "context_name": null}
  ]
}
""",
                encoding="utf-8",
            )
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "disassemble-file",
                    "--syntax",
                    "genam",
                    "--target-metadata",
                    str(metadata_path),
                    "amiga-hunk",
                    str(output_path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        h1_start = result.stdout.index("h1_0000:")
        self.assertIn("; KNOWN: base A6=exec.library:LIB\nh0_0000:", result.stdout)
        self.assertNotIn("KNOWN: base A6=exec.library:LIB", result.stdout[h1_start:])

    def test_disassemble_file_scopes_explicit_metadata_hunk_to_intended_section(self) -> None:
        source = (
            "SECTION first,code\n"
            + "".join("    rts\n    DC.W 0,0\n" for _ in range(18))
            + "SECTION second,code\n"
            + "".join("    rts\n    DC.W 0,0\n" for _ in range(18))
        )
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "metadata_explicit_hunk_scope.exe"
            metadata_path = Path(tmp) / "target_metadata.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "target_type": "library",
                        "entry_register_seeds": [
                            {
                                "entry_offset": 0,
                                "hunk": 1,
                                "register": "A6",
                                "kind": "library_base",
                                "library_name": "exec.library",
                                "struct_name": "LIB",
                                "context_name": None,
                            }
                        ],
                        "resident": {
                            "name": "icon.library",
                            "version": 40,
                            "hunk": 1,
                            "autoinit": {"vector_offsets": [index * 6 for index in range(18)]},
                        },
                    }
                ),
                encoding="utf-8",
            )
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "disassemble-file",
                    "--syntax",
                    "genam",
                    "--target-metadata",
                    str(metadata_path),
                    "amiga-hunk",
                    str(output_path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        sections = result.stdout.split("    SECTION section,code\n")
        self.assertEqual(len(sections), 3, result.stdout)
        h0_text = sections[1]
        h1_text = sections[2]
        self.assertNotIn("KNOWN: base A6=exec.library:LIB", h0_text)
        self.assertNotIn("DECL: struct DiskObject *GetDiskObject(UBYTE *name)", h0_text)
        self.assertIn("KNOWN: base A6=exec.library:LIB", h1_text)
        self.assertIn("DECL: struct DiskObject *GetDiskObject(UBYTE *name)", h1_text)

    def test_disassemble_file_declares_amiga_resident_lvo_vectors_from_generated_metadata(self) -> None:
        source = (
            "    SECTION code,code\n"
            "    addq.w #1,32(a6)\n"
            "    rts\n"
            + "".join("    rts\n    DC.W 0,0\n" for _ in range(17))
            + "    DC.W 0\n" * 80
        )
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmp_path = Path(tmp)
            output_path = tmp_path / "icon_vectors.exe"
            metadata_path = tmp_path / "target_metadata.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "target_type": "library",
                        "resident": {
                            "name": "icon.library",
                            "version": 40,
                            "offset": 200,
                            "hunk": 0,
                            "autoinit": {"vector_offsets": [index * 6 for index in range(18)]},
                        },
                    }
                ),
                encoding="utf-8",
            )
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "disassemble-file",
                    "--syntax",
                    "genam",
                    "--target-metadata",
                    str(metadata_path),
                    "amiga-hunk",
                    str(output_path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DECL: struct DiskObject *GetDiskObject(UBYTE *name)", result.stdout)
        self.assertIn("DECL: void FreeDiskObject(struct DiskObject *diskobj)", result.stdout)
        self.assertIn("DECL: char *FindToolType(UBYTE **toolTypeArray, UBYTE *typeName)", result.stdout)
        self.assertIn("DECL: BOOL MatchToolValue(UBYTE *typeString, UBYTE *value)", result.stdout)
        self.assertIn("DECL: char *BumpRevision(char *newbuf, UBYTE *oldname)", result.stdout)
        self.assertIn(
            "KNOWN: base A6=icon.library:LIB; type A0=toolTypeArray:UBYTE **; type A1=typeName:UBYTE *",
            result.stdout,
        )
        self.assertIn("lib_open:\n    addq.w #1,LIB_OPENCNT(a6)", result.stdout)
        self.assertIn('INCLUDE "exec/resident.i"', result.stdout)
        self.assertIn('INCLUDE "exec/libraries.i"', result.stdout)
        self.assertTrue(
            result.stdout.startswith(
                'INCLUDE "exec/libraries.i"\n'
                'INCLUDE "exec/resident.i"\n\n'
                "    SECTION section,code\n"
            ),
            result.stdout,
        )
        self.assertNotIn('INCLUDE "exec/resident.i"\nINCLUDE "exec/libraries.i"\n\nINCLUDE', result.stdout)

    def test_effective_policy_file_reports_resident_library_vectors_from_c(self) -> None:
        source = (
            "    SECTION code,code\n"
            + "".join("    rts\n    DC.W 0,0\n" for _ in range(18))
            + "    DC.W 0\n" * 80
        )
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmp_path = Path(tmp)
            output_path = tmp_path / "icon_vectors_policy.exe"
            metadata_path = tmp_path / "target_metadata.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "target_type": "library",
                        "resident": {
                            "name": "icon.library",
                            "version": 40,
                            "offset": 200,
                            "hunk": 0,
                            "autoinit": {"vector_offsets": [index * 6 for index in range(18)]},
                        },
                    }
                ),
                encoding="utf-8",
            )
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._effective_policy_file_path("amiga-hunk", output_path, metadata_path)
        policy = payload["analysis_policy"]
        self.assertEqual(payload["source_kind"], "file")
        self.assertEqual(payload["target_type"], "library")
        self.assertEqual(payload["analysis_start"], 0)
        self.assertIn({"section_index": 0, "offset": 72}, policy["entrypoints"])
        self.assertIn({"section_index": 0, "offset": 72, "name": "get_disk_object"}, policy["named_labels"])
        self.assertTrue(
            any(
                item["section_index"] == 0
                and item["offset"] == 200
                and item["kind"] == "words"
                and item["comment"] == "NOTE: resident matchword"
                and item["struct_name"] == "RT"
                and item["field_name"] == "RT_MATCHWORD"
                and item["field_type"] == "UWORD"
                and item["c_type"] == "UWORD"
                and item["value_domain"] == "exec.resident.matchword"
                and item["constant_name"] == "RTC_MATCHWORD"
                and item["constant_value"] == 19196
                for item in policy["structured_data_items"]
            )
        )
        self.assertTrue(
            any(
                seed["section_index"] == 0
                and seed["entry_offset"] == 72
                and seed["register"] == "A6"
                and seed["kind"] == "library_base"
                and seed["name"] == "icon.library"
                and seed["type_name"] == "LIB"
                for seed in policy["register_seeds"]
            )
        )
        self.assertIn(
            {
                "section_index": 0,
                "offset": 72,
                "comment": "DECL: struct DiskObject *GetDiskObject(UBYTE *name)",
            },
            policy["entry_comments"],
        )

    def test_effective_policy_file_uses_detected_resident_without_metadata(self) -> None:
        source = """\
    SECTION code,code
    moveq.l #-1,d0
    rts
resident:
    DC.W $4afc
    DC.L resident
    DC.L endskip
    DC.B $80,$22,$09,$46
    DC.L resident_name
    DC.L resident_id
    DC.L resident_autoinit
resident_name:
    DC.B "icon.library",0
resident_id:
    DC.B "icon 34.2 (22 Jun 1988)",13,10,0
    EVEN
resident_autoinit:
    DC.L $2e
    DC.L resident_vectors
    DC.L resident_init_struct
    DC.L resident_init
resident_vectors:
    DC.L lib_open
    DC.L lib_close
    DC.L lib_expunge
    DC.L lib_extfunc
    DC.L -1
resident_init_struct:
    DC.L 0,0,0,0
lib_open:
    rts
lib_close:
    rts
lib_expunge:
    rts
lib_extfunc:
    rts
resident_init:
    rts
endskip:
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "detected_icon_resident.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._effective_policy_file_path("amiga-hunk", output_path)
        policy = payload["analysis_policy"]
        self.assertEqual(payload["target_type"], "library")
        self.assertGreater(policy["entry_point_count"], 0)
        self.assertTrue(any(label["name"] == "resident_init" for label in policy["named_labels"]))
        self.assertTrue(any(label["name"] == "lib_expunge" for label in policy["named_labels"]))
        self.assertTrue(any(item["field_name"] == "RT_MATCHWORD" for item in policy["structured_data_items"]))

    def test_effective_policy_file_rejects_missing_source(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            metadata_path = Path(tmp) / "target_metadata.json"
            metadata_path.write_text(
                json.dumps({"target_type": "library", "resident": {"offset": 200, "hunk": 0}}),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "effective-policy-file",
                    "--target-metadata",
                    str(metadata_path),
                    "amiga-hunk",
                    str(Path(tmp) / "missing.exe"),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)

    def test_effective_policy_file_rejects_out_of_range_metadata_hunk(self) -> None:
        source = "SECTION code,code\n    rts\n"
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmp_path = Path(tmp)
            output_path = tmp_path / "one_hunk.exe"
            metadata_path = tmp_path / "target_metadata.json"
            metadata_path.write_text(
                json.dumps({"target_type": "library", "resident": {"offset": 0, "hunk": 2}}),
                encoding="utf-8",
            )
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "effective-policy-file",
                    "--target-metadata",
                    str(metadata_path),
                    "amiga-hunk",
                    str(output_path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hunk is out of range", result.stderr)

    def test_effective_policy_file_rejects_amiga_policy_on_atari_backend(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmp_path = Path(tmp)
            output_path = tmp_path / "sample.prg"
            metadata_path = tmp_path / "target_metadata.json"
            output_path.write_bytes(make_synthetic_atari_prg(b"\x4e\x75", b"", 0))
            metadata_path.write_text(
                json.dumps(
                    {
                        "target_type": "library",
                        "resident": {"name": "icon.library", "version": 40, "offset": 0, "hunk": 0},
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "effective-policy-file",
                    "--target-metadata",
                    str(metadata_path),
                    "atari-st",
                    str(output_path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Amiga-only policy", result.stderr)

    def test_effective_policy_file_rejects_out_of_range_metadata_offset(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmp_path = Path(tmp)
            output_path = tmp_path / "sample.exe"
            metadata_path = tmp_path / "target_metadata.json"
            output_path.write_bytes(make_synthetic_hunkexe(code_data=b"\x4e\x75"))
            metadata_path.write_text(
                json.dumps(
                    {
                        "target_type": "library",
                        "resident": {"name": "icon.library", "version": 40, "offset": 9999, "hunk": 0},
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "effective-policy-file",
                    "--target-metadata",
                    str(metadata_path),
                    "amiga-hunk",
                    str(output_path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("out of range", result.stderr)

    def test_listing_rows_file_exposes_resident_structured_data_from_policy(self) -> None:
        source = (
            "SECTION code,code\n"
            "    rts\n"
            + "    DC.W 0\n" * 99
            + "resident:\n"
            "    DC.W $4afc\n"
            "    DC.L resident\n"
            "    DC.L 0\n"
            "    DC.B $80,$28,$09,$46\n"
            "    DC.L 0\n"
            "    DC.L 0\n"
            "    DC.L 0\n"
        )
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmp_path = Path(tmp)
            output_path = tmp_path / "resident_listing_rows.exe"
            metadata_path = tmp_path / "target_metadata.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "target_type": "library",
                        "resident": {"name": "icon.library", "version": 40, "offset": 200, "hunk": 0},
                    }
                ),
                encoding="utf-8",
            )
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._listing_rows_file_path("amiga-hunk", output_path, metadata_path)

        rows = payload["rows"]
        matchword = next(row for row in rows if row.get("kind") == "data" and row.get("addr") == 200)
        self.assertEqual(matchword["operand_text"], "RTC_MATCHWORD")
        self.assertEqual(matchword["comment_text"], "UWORD RT_MATCHWORD")
        self.assertEqual(
            matchword["structured_data"],
            {
                "label": "resident_matchword",
                "struct_name": "RT",
                "field_name": "RT_MATCHWORD",
                "field_type": "UWORD",
                "c_type": "UWORD",
                "pointer_struct": None,
                "value_domain": "exec.resident.matchword",
                "constant_name": "RTC_MATCHWORD",
                "has_constant_value": True,
                "constant_value": 19196,
                "semantic_role": "resident_matchword",
                "is_pointer": False,
                "target_section": None,
                "target_offset": None,
            },
        )
        matchtag = next(row for row in rows if row.get("kind") == "data" and row.get("addr") == 202)
        self.assertEqual(matchtag["structured_data"]["field_name"], "RT_MATCHTAG")
        self.assertEqual(matchtag["structured_data"]["target_section"], 0)
        self.assertEqual(matchtag["structured_data"]["target_offset"], 200)
        flags = next(row for row in rows if row.get("kind") == "data" and row.get("addr") == 210)
        self.assertEqual(flags["operand_text"], "RTF_AUTOINIT")
        self.assertEqual(flags["comment_text"], "UBYTE RT_FLAGS")
        node_type = next(row for row in rows if row.get("kind") == "data" and row.get("addr") == 212)
        self.assertEqual(node_type["operand_text"], "NT_LIBRARY")
        self.assertEqual(node_type["comment_text"], "UBYTE RT_TYPE")
        name_pointer = next(row for row in rows if row.get("kind") == "data" and row.get("addr") == 214)
        self.assertEqual(name_pointer["structured_data"]["label"], "resident_name")
        self.assertEqual(name_pointer["structured_data"]["field_name"], "RT_NAME")
        self.assertEqual(name_pointer["structured_data"]["field_type"], "APTR")
        self.assertEqual(name_pointer["structured_data"]["c_type"], "char *")
        self.assertTrue(name_pointer["structured_data"]["is_pointer"])

    def test_disassemble_raw_bootblock_metadata_seeds_iorequest_type(self) -> None:
        target_dir = (
            ROOT
            / "targets"
            / "amiga_disk_ice-1991-06-28-the-silents"
            / "targets"
            / "amiga_raw_bootblock"
        )
        result = subprocess.run(
            [
                str(self.file_exe),
                "disassemble-raw",
                "--syntax",
                "vasm",
                "--target-metadata",
                str(target_dir / "target_metadata.json"),
                "amiga-raw",
                str(target_dir / "binary.bin"),
                "12",
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('INCLUDE "exec/io.i"', result.stdout)
        self.assertRegex(result.stdout, r'DC\.B    "DOS",0\s+; NOTE: boot magic')
        self.assertRegex(result.stdout, r"DC\.L    \$a382070f\s+; NOTE: boot checksum")
        self.assertRegex(result.stdout, r"DC\.L    \$00000370\s+; NOTE: boot root block")
        self.assertNotIn("boot_magic:", result.stdout)
        self.assertIn("move.w #CMD_READ,IO_COMMAND(a1)", result.stdout)
        self.assertIn("move.l #$40000,IO_DATA(a1)", result.stdout)
        self.assertIn("move.l #$5400,IO_LENGTH(a1)", result.stdout)
        self.assertIn("move.l #$400,IO_OFFSET(a1)", result.stdout)

    def test_type_catalog_reports_generated_amiga_structs(self) -> None:
        catalog = self._type_catalog("amiga-hunk")
        by_name = {entry["name"]: entry for entry in catalog}

        self.assertIn("SimpleSprite", by_name)
        self.assertEqual(by_name["SimpleSprite"]["size"], 12)
        self.assertEqual(by_name["SimpleSprite"]["source"], "graphics/sprite.i")
        self.assertEqual(by_name["DosLibrary"]["named_base"], "dos.library")

    def test_naming_catalog_reports_generated_amiga_naming_rules(self) -> None:
        catalog = self._naming_catalog("amiga-hunk")
        patterns = catalog["patterns"]

        self.assertIn("dos.library", catalog["libraries"])
        self.assertIn("AllocMem", catalog["trivial_functions"])
        self.assertEqual(catalog["generic_prefix"], "call_")
        self.assertIn(
            {"functions": ["AllocMem"], "name": "alloc_memory", "partial": False},
            patterns,
        )

    def test_os_metadata_catalog_reports_generated_amiga_resident_rules(self) -> None:
        catalog = self._os_metadata_catalog("amiga-hunk")
        prefix_rows = catalog["resident_vector_prefixes"]
        seed_rows = catalog["resident_entry_register_seeds"]
        structs = {entry["name"]: entry for entry in catalog["structs"]}

        self.assertEqual(catalog["exec_base_library"], "exec.library")
        self.assertEqual(catalog["lvo_slot_size"], 6)
        self.assertIn({"target_type": "library", "slot_index": 0, "symbol": "LIB_OPEN"}, prefix_rows)
        self.assertIn(
            {
                "target_type": "library",
                "role": "init",
                "register": "A6",
                "kind": "library_base",
                "named_base_source": "fixed",
                "named_base_name": "exec.library",
                "struct_name": None,
                "context_name": None,
            },
            seed_rows,
        )
        self.assertEqual(structs["RT"]["size"], 26)

    def test_api_input_struct_validates_generated_amiga_metadata(self) -> None:
        actual = self._api_input_struct(
            "amiga-hunk", "intuition.library", "SetPointer", "pointer", "SimpleSprite"
        )

        self.assertEqual(actual["type"], "struct SimpleSprite *")
        self.assertEqual(actual["i_struct"], "SimpleSprite")
        self.assertEqual(actual["struct_source"], "graphics/sprite.i")

    def test_analyze_file_emits_generated_api_input_type_correction(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOSetPointer EQU -270
app_IntuitionBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l intuition_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_IntuitionBase(a6)
    move.l a6,-(a7)
    movea.l app_IntuitionBase(a6),a6
    lea.l sprite(pc),a1
    moveq.l #0,d0
    moveq.l #0,d1
    moveq.l #0,d2
    moveq.l #0,d3
    moveq.l #0,d4
    jsr _LVOSetPointer(a6)
    movea.l (a7)+,a6
    rts

intuition_name:
    DC.B "intuition.library",0
    EVEN
sprite:
    DC.B 0,0,0,0,0,0,0,0,0,0,0,0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "setpointer.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._analyze_file_path("amiga-hunk", output_path)

        calls = payload["sections"][0]["recovered_platform_calls"]
        set_pointer = next(call for call in calls if call["function_name"] == "SetPointer")
        pointer_input = next(item for item in set_pointer["inputs"] if item["name"] == "pointer")
        self.assertEqual(pointer_input["type"], "struct SimpleSprite *")
        self.assertEqual(pointer_input["i_struct"], "SimpleSprite")
        self.assertEqual(pointer_input["source"], "global correction")

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
            self.assertIn("h0_0000:", default_result.stdout)

            fallback_result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "--no-generated-names", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(fallback_result.returncode, 0, fallback_result.stderr)
            self.assertIn("h0_0000:", fallback_result.stdout)

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
            self.assertIn("h0_0000:", result.stdout)
            self.assertNotIn("blk_0000:", result.stdout)

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

    def test_disassemble_file_enforces_amiga_os_compatibility_floor(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "asl_floor.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(AMIGA_ASL_ALLOC_REQUEST_SOURCE, path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            default_result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(default_result.returncode, 0, default_result.stderr)
            self.assertNotIn("; Minimum OS version:", default_result.stdout)

            compat_result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "--min-os-version", "2.0", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(compat_result.returncode, 0, compat_result.stderr)
            self.assertTrue(compat_result.stdout.startswith("; Minimum OS version: 2.0\n"), compat_result.stdout)

            low_result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "--min-os-version", "1.3", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(low_result.returncode, 1, low_result.stderr)
            self.assertIn("_LVOAllocAslRequest", low_result.stderr)
            self.assertIn("minimum OS version 1.3", low_result.stderr)

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
            self.assertIn("pea.l h0_0004(pc)", result.stdout)
            self.assertNotIn("VIOLATION: invalid overlap", result.stdout)

    def test_analyze_file_reports_orphaned_code_violation_and_benchmark_count(self) -> None:
        source = """\
SECTION section,code
start:
    rts
    DC.W 0
    moveq.l #1,d0
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "orphaned_code.exe"
            benchmark_path = Path(tmp) / "benchmark.json"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._analyze_file_path("amiga-hunk", path)
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "disassemble-file",
                    "--benchmark-json-out",
                    str(benchmark_path),
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
            benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
        violation = {
            "offset": 4,
            "kind": 5,
            "message": "orphaned code island at $0004 is not reached from known entrypoints",
        }
        self.assertIn(violation, payload["sections"][0]["violations"])
        self.assertEqual(1, benchmark["analysis"]["violation_counts"]["orphaned_code"])
        self.assertEqual(1, benchmark["sections"][0]["violation_counts"]["orphaned_code"])
        self.assertIn(
            "VIOLATION: orphaned code island at $0004 is not reached from known entrypoints",
            result.stdout,
        )

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
            self.assertIn("pea.l h0_0004(pc,d0.w)", result.stdout)
            self.assertNotIn("h0_0000+2(pc,d0.w)", result.stdout)

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
            self.assertNotIn("h0_0000+2(pc,d0.w)", result.stdout)

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
            self.assertIn("lea.l h0_0000(pc),a1", result.stdout)
            self.assertNotIn("lea.l h0_0002(pc),a1", result.stdout)

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
            self.assertIn("h0_0004:", result.stdout)
            self.assertIn("h0_0008:", result.stdout)
            self.assertIn("bra.w h0_000C", result.stdout)
            self.assertIn("bra.w h0_000E", result.stdout)
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
            self.assertRegex(
                vasm_result.stdout,
                r"ori\.b #117,-\(a4\)\s+; NOTE: vasm-normalized from exact immediate word \$4E75",
            )

    def test_disassemble_genam_resolves_real_jump_table_dispatch_site(self) -> None:
        text = self._disassemble_real_path("amiga-hunk", GENAM_BIN)
        self.assertIn("dat_0EA2:", text)
        self.assertIn("lea.l dat_0EA2(pc),a1", text)
        self.assertIn("move.w -$8(a1,d1.w),d1", text)
        self.assertIn("jsr $0(a1,d1.w)", text)
        self.assertNotIn("jsr $0(a1,d1.w) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertIn("DC.W    h0_20B4-dat_0EA2", text)
        self.assertIn("DC.W    h0_10A4-dat_0EA2", text)
        self.assertIn("DC.W    h0_2BC0-dat_0EA2", text)
        self.assertIn("DC.W    h0_10DA-dat_0EA2", text)
        self.assertIn("DC.W    h0_1120-dat_0EA2", text)
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
        self.assertIn("movea.l app_timer_device_iorequest+IO_DEVICE(a6),a0", text)
        self.assertIn("cmpi.w #36,LIB_VERSION(a0)", text)
        self.assertRegex(text, r"jsr \(a1\)\s+; KNOWN: callback field \+4 from app_slot_01A2")
        self.assertRegex(text, r"jsr \(a0\)\s+; KNOWN: callback field \+4 from app_slot_01A2")
        self.assertIn("movea.l app_timer_device_iorequest+IO_DEVICE(a6),a6", text)
        self.assertIn("movea.l app_DOSBase(a6),a1", text)
        self.assertIn("movea.l app_DOSBase(a6),a6", text)
        self.assertIn("lea.l app_timer_device_iorequest+IOSTD_SIZE(a6),a1", text)
        self.assertIn("app_file_0CDA RS.L 1", text)
        self.assertIn("app_file_0956 RS.L 1", text)
        self.assertIn("move.l d0,app_file_0CDA+fh_Link(a6)", text)
        self.assertIn("move.l d0,app_file_0956+fh_Link(a6)", text)
        self.assertIn("move.l app_file_0CDA+fh_Link(a6),d1", text)
        self.assertIn("app_fileinfoblock RS.L 1", text)
        self.assertIn("move.l fib_Size(a0),d1", text)
        self.assertIn("app_dest_10B0 EQU 4272", text)
        self.assertIn('INCLUDE "devices/timer.i"', text)
        self.assertIn('INCLUDE "devices/timer_lib.i"', text)
        self.assertIn('INCLUDE "dos/dos.i"', text)
        self.assertIn('INCLUDE "dos/dos_lib.i"', text)
        self.assertIn('INCLUDE "exec/exec_lib.i"', text)
        self.assertIn('INCLUDE "exec/io.i"', text)
        self.assertIn('INCLUDE "exec/libraries.i"', text)
        self.assertIn("move.l app_dest_10B0+TV_SECS(a6),d1", text)
        self.assertIn("move.l app_dest_10B0+TV_MICRO(a6),d1", text)
        self.assertIn("app_slot_01A2 RS.L 1", text)
        self.assertIn("moveq.l #_LVOOutput,d0", text)
        self.assertIn("moveq.l #_LVOWrite,d0", text)
        self.assertIn("move.l #$FFFFFF40,d0", text)
        self.assertNotIn("moveq.l #-60,d0", text)
        self.assertNotIn("moveq.l #196,d0", text)
        self.assertRegex(text, r"bsr\.w h0_B0D6\s+; KNOWN: DOSBase _LVOOutput fallback via local wrapper")
        self.assertRegex(text, r"bsr\.w h0_B0D6\s+; KNOWN: DOSBase _LVOOpen fallback via local wrapper")
        self.assertRegex(text, r"bsr\.w h0_B0D6\s+; KNOWN: DOSBase _LVODateStamp fallback via local wrapper")
        self.assertRegex(text, r"jsr \$0\(a6,d0\.w\)\s+; KNOWN: DOSBase indexed vector via d0")
        self.assertNotIn("jsr (a0) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertNotIn("jsr (a1) ; CANDIDATE: indirect_call index unresolved", text)
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
        self.assertNotIn("move.b $4(pc,d1.w),d1", text)
        self.assertNotIn("move.b $18(pc,d1.w),(a4)+", text)
        self.assertNotIn("dat_0EA4:", text)
        self.assertNotIn("h0_0EA4:", text)
        self.assertNotIn("DC.W    h0_12B8-dat_0EA2", text)
        self.assertNotIn("DC.W    h0_24B6-dat_0EA2", text)
        self.assertNotIn("DC.W    h0_22B6-dat_0EA2", text)
        self.assertNotIn("DC.W    h0_22B4-dat_0EA2", text)
        self.assertNotIn("lea.l dat_0EA4(pc),a1", text)
        self.assertNotIn("jsr -$00C6(a6) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertNotIn("jsr -$00D2(a6) ; CANDIDATE: indirect_call index unresolved", text)
        self.assertIn("jmp h0_13C8-2(pc,d0.w)", text)
        self.assertNotIn("jmp *+2(pc,d0.w)", text)
        self.assertNotIn("jmp h0_13C4+2(pc,d0.w)", text)
        table_idx = text.find("dat_439E:")
        self.assertNotEqual(table_idx, -1)
        table_window = text[table_idx:text.find("h0_43D2:", table_idx)]
        self.assertIn("DC.W    $0000", table_window)
        self.assertNotIn("DC.B    $00,$00", table_window)
        self.assertNotIn("DC.L    $00000000", table_window)
        self.assertNotIn("h0_3F3D:", text)
        self.assertNotIn("h0_3F43:", text)
        string_dispatch_idx = text.find("dat_3F3C:")
        self.assertNotEqual(string_dispatch_idx, -1)
        string_dispatch_window = text[string_dispatch_idx:text.find("h0_432C:", string_dispatch_idx)]
        dispatch_call_idx = text.find("h0_4370:")
        self.assertNotEqual(dispatch_call_idx, -1)
        dispatch_call_window = text[dispatch_call_idx:text.find("h0_4374:", dispatch_call_idx)]
        self.assertIn("jsr (a0)", dispatch_call_window)
        self.assertNotIn("jsr (a0) ; CANDIDATE: indirect_call index unresolved", dispatch_call_window)
        early_dispatch_call_idx = text.find("h0_3AB0:")
        self.assertNotEqual(early_dispatch_call_idx, -1)
        early_dispatch_call_window = text[early_dispatch_call_idx:text.find("h0_3AB2:", early_dispatch_call_idx)]
        self.assertIn("jsr (a0)", early_dispatch_call_window)
        self.assertNotIn("jsr (a0) ; CANDIDATE: indirect_call index unresolved", early_dispatch_call_window)
        self.assertIn('DC.B    "OWZERO"', string_dispatch_window)
        self.assertIn("DC.W    h0_4200-*", string_dispatch_window)
        self.assertIn("DC.W    h0_42A2-*", string_dispatch_window)
        self.assertIn("h0_4200:\n    moveq.l #2,d0", text)
        self.assertIn("h0_4218:\n    st.b $012C(a6)", text)
        self.assertIn("h0_42A2:\n    st.b $0120(a6)", text)
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
        dispatch_idx = text.find("h0_3BBE:")
        self.assertNotEqual(dispatch_idx, -1)
        dispatch_window = text[dispatch_idx:text.find("dat_3C12:", dispatch_idx)]
        self.assertIn("lea.l dat_3C12(pc,d1.w),a2", text)
        self.assertIn("adda.w (a2),a2", text)
        self.assertIn("jmp (a2)", dispatch_window)
        self.assertNotIn("jmp (a2) ; CANDIDATE: indirect_jump index unresolved", dispatch_window)
        self.assertIn("dat_3C12:", text)
        self.assertIn("DC.W    h0_3D00-*", text)
        self.assertIn("DC.W    h0_3C86-*", text)
        self.assertIn("DC.W    h0_3C5C-*", text)
        self.assertIn("DC.W    h0_3E98-*", text)

    def test_disassemble_amiga_open_device_flow_symbols_typed_io_field(self) -> None:
        source = """\
_LVOOpenDevice EQU -444
app_IO EQU 4280

    SECTION section,code
start:
    lea.l dev_name(pc),a0
    lea.l app_IO(a6),a1
    moveq.l #0,d0
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOOpenDevice(a6)
    movea.l (a7)+,a6
    movea.l app_IO(a6),a1
    movea.l $0014(a1),a0
    rts
dev_name:
    DC.B "timer.device",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "open_device.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOOpenDevice(a6)", text)
        self.assertIn("lea.l app_timer_device_iorequest(a6),a1", text)
        self.assertIn("movea.l IO_DEVICE(a1),a0", text)

    def test_disassemble_amiga_open_device_flow_symbols_second_typed_io_field(self) -> None:
        source = """\
_LVOOpenDevice EQU -444
app_IO EQU 4280

    SECTION section,code
start:
    lea.l dev_name(pc),a0
    lea.l app_IO(a6),a1
    moveq.l #0,d0
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOOpenDevice(a6)
    movea.l (a7)+,a6
    movea.l app_IO(a6),a1
    movea.l $0018(a1),a0
    rts
dev_name:
    DC.B "timer.device",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "open_device_unit.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOOpenDevice(a6)", text)
        self.assertIn("movea.l IO_UNIT(a1),a0", text)

    def test_disassemble_amiga_multi_struct_inputs_type_both_slots(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOAbortPkt EQU -264
app_DOSBase EQU 4280
slot_mp EQU 4284
slot_pkt EQU 4320

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    lea.l slot_mp(a6),a1
    lea.l slot_pkt(a6),a2
    move.l a1,d1
    move.l a2,d2
    move.l #_LVOAbortPkt,d0
    bsr.w sub_B0D6
    movea.l slot_mp(a6),a1
    movea.l $0010(a1),a0
    movea.l slot_pkt(a6),a2
    move.l $0004(a2),d1
    rts

sub_B0D6:
    move.l a6,-(a7)
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "abortpkt_multi_input.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("move.l #$FFFFFEF8,d0", text)
        self.assertIn("; KNOWN: DOSBase _LVOAbortPkt fallback via local wrapper", text)
        self.assertIn("app_port EQU 4284", text)
        self.assertIn("app_pkt EQU 4320", text)
        self.assertIn("movea.l app_port(a6),a1", text)
        self.assertIn("movea.l MP_SIGTASK(a1),a0", text)
        self.assertIn("movea.l app_pkt+dp_Link(a6),a2", text)
        self.assertIn("move.l dp_Port(a2),d1", text)

    def test_generated_amiga_runtime_infers_missing_hook_struct_from_input_type(self) -> None:
        text = AMIGA_RUNTIME_SOURCE.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            re.compile(
                r"\{\s*2u,\s*1u,\s*AMIGA_OS_SYMBOL_ID_HANDLER,\s*AMIGA_OS_TYPE_ID_STRUCT_HOOK,\s*"
                r"AMIGA_OS_STRUCT_ID_HOOK,\s*AMIGA_OS_SEMANTIC_KIND_ID_HOOK_PTR,\s*AMIGA_OS_VALUE_DOMAIN_ID_NONE,\s*0u\s*\}"
            ),
        )
        self.assertRegex(
            text,
            re.compile(
                r"\{\s*2u,\s*0u,\s*AMIGA_OS_SYMBOL_ID_IFF,\s*AMIGA_OS_TYPE_ID_STRUCT_IFFHANDLE,\s*"
                r"AMIGA_OS_STRUCT_ID_IFFHANDLE,\s*AMIGA_OS_SEMANTIC_KIND_ID_NONE,\s*AMIGA_OS_VALUE_DOMAIN_ID_NONE,\s*0u\s*\}"
            ),
        )

    def test_generated_amiga_runtime_merges_code_ptr_semantics_and_value_domains(self) -> None:
        text = AMIGA_RUNTIME_SOURCE.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            re.compile(
                r"\{\s*2u,\s*2u,\s*AMIGA_OS_SYMBOL_ID_INITPC,\s*AMIGA_OS_TYPE_ID_APTR,\s*AMIGA_OS_STRUCT_ID_NONE,\s*"
                r"AMIGA_OS_SEMANTIC_KIND_ID_CODE_PTR,\s*AMIGA_OS_VALUE_DOMAIN_ID_NONE,\s*0u\s*\}"
            ),
        )
        self.assertRegex(
            text,
            re.compile(
                r"\{\s*2u,\s*3u,\s*AMIGA_OS_SYMBOL_ID_FINALPC,\s*AMIGA_OS_TYPE_ID_APTR,\s*AMIGA_OS_STRUCT_ID_NONE,\s*"
                r"AMIGA_OS_SEMANTIC_KIND_ID_CODE_PTR,\s*AMIGA_OS_VALUE_DOMAIN_ID_NONE,\s*0u\s*\}"
            ),
        )
        self.assertRegex(
            text,
            re.compile(
                r"\{\s*1u,\s*2u,\s*AMIGA_OS_SYMBOL_ID_ACCESSMODE,\s*AMIGA_OS_TYPE_ID_LONG_3,\s*AMIGA_OS_STRUCT_ID_NONE,\s*AMIGA_OS_SEMANTIC_KIND_ID_NONE,\s*"
                r"AMIGA_OS_VALUE_DOMAIN_ID_DOS_OPEN_ACCESS_MODE,\s*0u\s*\}"
            ),
        )
        self.assertRegex(
            text,
            re.compile(
                r"\{\s*1u,\s*1u,\s*AMIGA_OS_SYMBOL_ID_ATTRIBUTES,\s*AMIGA_OS_TYPE_ID_ULONG,\s*AMIGA_OS_STRUCT_ID_NONE,\s*AMIGA_OS_SEMANTIC_KIND_ID_NONE,\s*"
                r"AMIGA_OS_VALUE_DOMAIN_ID_EXEC_ALLOCMEM_ATTRIBUTES,\s*0u\s*\}"
            ),
        )
        self.assertRegex(
            text,
            re.compile(
                r"\{\s*2u,\s*1u,\s*AMIGA_OS_SYMBOL_ID_LIBNAME,\s*AMIGA_OS_TYPE_ID_UBYTE_2,\s*AMIGA_OS_STRUCT_ID_NONE,\s*"
                r"AMIGA_OS_SEMANTIC_KIND_ID_STRING_PTR,\s*AMIGA_OS_VALUE_DOMAIN_ID_AMIGA_LIBRARY_NAME,\s*0u\s*\}"
            ),
        )
        self.assertIn(
            "{ AMIGA_OS_STRUCT_ID_RT, 0, AMIGA_OS_FIELD_ID_RT_MATCHWORD, "
            "AMIGA_OS_TYPE_ID_NONE, 2u, AMIGA_OS_TYPE_ID_UWORD, "
            "AMIGA_OS_TYPE_ID_UWORD, AMIGA_OS_STRUCT_ID_NONE },",
            text,
        )
        self.assertIn(
            "{ AMIGA_OS_STRUCT_ID_RT, AMIGA_OS_FIELD_ID_RT_MATCHWORD, "
            "AMIGA_OS_SYMBOL_ID_NONE, AMIGA_OS_VALUE_DOMAIN_ID_EXEC_RESIDENT_MATCHWORD },",
            text,
        )
        self.assertIn("{ AMIGA_OS_SYMBOL_ID_LIB_OPEN, -6 },", text)

    def test_generated_amiga_runtime_emits_compatibility_tables_and_versioned_vectors(self) -> None:
        header = AMIGA_RUNTIME_HEADER.read_text(encoding="utf-8")
        source = AMIGA_RUNTIME_SOURCE.read_text(encoding="utf-8")
        self.assertIn("typedef enum AmigaOsCompatVersion {", header)
        self.assertIn("AMIGA_OS_COMPAT_VERSION_1_3 = 1,", header)
        self.assertIn("AMIGA_OS_COMPAT_VERSION_2_0 = 2,", header)
        self.assertIn("uint16_t library_id;", header)
        self.assertIn("uint16_t function_id;", header)
        self.assertIn("uint16_t lvo_symbol_id;", header)
        self.assertIn("uint16_t input_id;", header)
        self.assertIn("uint16_t available_since_version;", header)
        self.assertIn("uint16_t amiga_os_name_id(uint8_t domain_kind, const char *name);", header)
        self.assertIn("const char *amiga_os_name(uint8_t domain_kind, uint16_t id);", header)
        self.assertIn("const char *amiga_os_compatibility_version_name(AmigaOsCompatVersion version);", header)
        self.assertIn("AmigaOsCompatVersion amiga_os_parse_compatibility_version(const char *version);", header)
        self.assertIn("AmigaOsCompatVersion amiga_os_find_include_min_compat_version(const char *include_path);", header)
        self.assertIn("uint16_t amiga_os_name_id(uint8_t domain_kind, const char *name) {", source)
        self.assertIn("const char *amiga_os_name(uint8_t domain_kind, uint16_t id) {", source)
        self.assertIn("static const char *const g_amiga_os_symbol_names[] = {", source)
        self.assertIn("static const char *g_amiga_os_compatibility_version_names[] = {", source)
        self.assertIn('  "1.3",', source)
        self.assertIn("static const uint16_t g_amiga_os_compatibility_version_ranks[] = {", source)
        self.assertIn("{ AMIGA_OS_INCLUDE_ID_DOS_DOS_I, AMIGA_OS_COMPAT_VERSION_2_0 },", source)
        self.assertIn("{ AMIGA_OS_INCLUDE_ID_EXEC_EXEC_LIB_I, AMIGA_OS_COMPAT_VERSION_1_3 },", source)
        self.assertIn(
            "{ AMIGA_OS_LIBRARY_ID_ASL_LIBRARY, AMIGA_OS_BASE_ID_ASLBASE, -48, "
            "AMIGA_OS_FUNCTION_ID_ALLOCASLREQUEST, AMIGA_OS_SYMBOL_ID_LVOALLOCASLREQUEST, 0u, 0u, 0u, 0u, "
            'AMIGA_OS_COMPAT_VERSION_2_0, "36"',
            source,
        )
        self.assertIn(
            "{ AMIGA_OS_LIBRARY_ID_EXEC_LIBRARY, AMIGA_OS_BASE_ID_SYSBASE, -684, "
            "AMIGA_OS_FUNCTION_ID_ALLOCVEC, AMIGA_OS_SYMBOL_ID_LVOALLOCVEC, 0u, 0u, 0u, 0u, "
            'AMIGA_OS_COMPAT_VERSION_2_0, "36"',
            source,
        )

    def test_generated_atari_runtime_emits_name_lookup_helpers(self) -> None:
        header = ATARI_RUNTIME_HEADER.read_text(encoding="utf-8")
        source = ATARI_RUNTIME_SOURCE.read_text(encoding="utf-8")
        self.assertIn("uint16_t atari_st_os_name_id(uint8_t domain_kind, const char *name);", header)
        self.assertIn("const char *atari_st_os_name(uint8_t domain_kind, uint16_t id);", header)
        self.assertIn("uint16_t family_id;", header)
        self.assertIn("uint16_t symbol_id;", header)
        self.assertIn("uint16_t include_id;", header)
        self.assertIn("uint16_t atari_st_os_name_id(uint8_t domain_kind, const char *name) {", source)
        self.assertIn("const char *atari_st_os_name(uint8_t domain_kind, uint16_t id) {", source)
        self.assertIn("static const char *const g_atari_st_os_symbol_names[] = {", source)
        self.assertIn(
            "{ ATARI_ST_OS_FAMILY_ID_GEMDOS, 1u, 9u, ATARI_ST_OS_FUNCTION_ID_CCONWS, "
            "ATARI_ST_OS_SYMBOL_ID_C_CONWS, ATARI_ST_OS_HEADER_ID_BDOSBIND_H, "
            "ATARI_ST_OS_INCLUDE_ID_GEMDOS_I, 0u, 0u, 1u, ATARI_ST_OS_RETURN_LONG }",
            source,
        )

    def test_analyze_amiga_hook_effect_persists_semantic_payload(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOCallHookPkt EQU -102
app_UtilityBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l util_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_UtilityBase(a6)
    lea.l hook_data(pc),a0
    movea.l app_UtilityBase(a6),a2
    jsr _LVOCallHookPkt(a2)
    rts

util_name:
    DC.B "utility.library",0
    EVEN
hook_data:
    DC.L 0,0,0,0,0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "hook_effect_payload.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._analyze_file_path("amiga-hunk", output_path)
        effects = payload["sections"][0]["recovered_platform_effects"]
        hints = payload["sections"][0]["entity_hints"]
        self.assertTrue(
            any(
                effect["kind"] == 4
                and effect["reg_kind"] == 2
                and effect["reg_index"] == 0
                and effect["type_name"] == "HOOK"
                and effect["semantic_kind"] == "hook_ptr"
                and effect["value_domain_name"] is None
                for effect in effects
            ),
            effects,
        )
        self.assertTrue(
            any(
                hint["hint_kind"] == "app_slot"
                and hint["app_slot"]["offset"] == "0x10B8"
                and hint["app_slot"].get("named_base") == "UtilityBase"
                for hint in hints
            ),
            hints,
        )

    def test_analyze_amiga_open_mode_effect_persists_constant_domain_payload(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
app_DOSBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    lea.l file_name(pc),a0
    move.l a0,d1
    movea.l a7,a5
    move.l #$000003ED,d0
    move.l d0,$0010(a5)
    move.l $0010(a5),d2
    moveq.l #_LVOOpen,d0
    bsr.w sub_B0D6
    rts

sub_B0D6:
    move.l a6,-(a7)
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
file_name:
    DC.B "x",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "open_mode_effect_payload.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._analyze_file_path("amiga-hunk", output_path)
        effects = payload["sections"][0]["recovered_platform_effects"]
        self.assertTrue(
            any(
                effect["kind"] == 4
                and effect["reg_kind"] == 1
                and effect["reg_index"] == 0
                and effect["value_domain_name"] == "dos.open.access_mode"
                and effect["has_constant_value"] == 1
                and effect["constant_value"] == 1005
                for effect in effects
            ),
            effects,
        )

    def test_disassemble_amiga_global_library_base_slots_resolve_vectors(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOForbid EQU -132
_LVOOpen EQU -30

    SECTION section,code
start:
    movea.l $0004.w,a6
    move.l a6,exec_slot
    movea.l exec_slot.l,a6
    jsr _LVOForbid(a6)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    move.l d0,dos_slot
    movea.l dos_slot.l,a6
    moveq.l #0,d1
    jsr _LVOOpen(a6)
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
exec_slot:
    DC.L 0
dos_slot:
    DC.L 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "global_bases.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOForbid(a6)", text)
        self.assertIn("jsr _LVOOpen(a6)", text)

    def test_disassemble_amiga_absolute_long_sysbase_resolves_exec_vectors(self) -> None:
        source = """\
_LVOForbid EQU -132

    SECTION section,code
start:
    movea.l $00000004.l,a6
    jsr _LVOForbid(a6)
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "absolute_long_sysbase.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("movea.l $00000004.l,a6", text)
        self.assertIn("jsr _LVOForbid(a6)", text)
        self.assertNotIn("CANDIDATE: indirect_call", text)

    def test_disassemble_amiga_cross_hunk_global_library_base_slots_resolve_vectors(self) -> None:
        source = """\
_LVOForbid EQU -132
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30

    SECTION first,code
start:
    movea.l $0004.w,a6
    move.l a6,exec_slot
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    move.l d0,dos_slot
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
exec_slot:
    DC.L 0
dos_slot:
    DC.L 0
    DC.W 0

    SECTION second,code
exec_wrapper:
    movea.l exec_slot.l,a6
    jsr _LVOForbid(a6)
    rts

    SECTION third,code
dos_wrapper:
    movea.l dos_slot.l,a6
    moveq.l #0,d1
    jsr _LVOOpen(a6)
    rts
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "cross_hunk_global_bases.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("movea.l h0dl_ExecBase.l,a6", text)
        self.assertIn("movea.l h0dl_DOSBase.l,a6", text)
        self.assertNotIn("movea.l h0_", text)
        self.assertIn("jsr _LVOForbid(a6)", text)
        self.assertIn("jsr _LVOOpen(a6)", text)
        self.assertNotIn("CANDIDATE: indirect_call", text)

    def test_disassemble_amiga_branch_join_app_slot_global_base_resolves_vectors(self) -> None:
        source = """\
_LVOForbid EQU -132

    SECTION first,code
    DC.L 0
resident_init:
    movea.l d0,a2
    move.l a0,$002A(a2)
    move.l a6,$0022(a2)
    bra.s ready
failed:
    rts
ready:
    move.l $0022(a2),exec_slot
    move.l $002A(a2),seg_slot
    rts
exec_slot:
    DC.L 0
seg_slot:
    DC.L 0

    SECTION second,code
wrapper:
    movea.l exec_slot.l,a6
    jsr _LVOForbid(a6)
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmp_path = Path(tmp)
            output_path = tmp_path / "branch_join_global_base.exe"
            metadata_path = tmp_path / "target_metadata.json"
            metadata_path.write_text(
                """{
  "entry_register_seeds": [
    {"entry_offset": 4, "register": "D0", "kind": "library_base", "library_name": "__amiga_app_base__", "struct_name": "", "context_name": null},
    {"entry_offset": 4, "register": "D0", "kind": "struct_ptr", "note": "__amiga_app_base__", "struct_name": "LIB", "context_name": null},
    {"entry_offset": 4, "register": "A0", "kind": "struct_ptr", "note": "seglist", "struct_name": "BPTR", "context_name": null},
    {"entry_offset": 4, "register": "A6", "kind": "library_base", "library_name": "exec.library", "struct_name": "", "context_name": null}
  ],
  "seeded_code_entrypoints": [
    {"addr": 4, "hunk": 0, "name": "resident_init"}
  ]
}
""",
                encoding="utf-8",
            )
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            result = subprocess.run(
                [
                    str(self.file_exe),
                    "disassemble-file",
                    "--syntax",
                    "genam",
                    "--target-metadata",
                    str(metadata_path),
                    "amiga-hunk",
                    str(output_path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("move.l a0,app_SegList(a2)", result.stdout)
        self.assertIn("move.l a6,app_ExecBase(a2)", result.stdout)
        self.assertIn("move.l app_ExecBase(a2),h0dl_ExecBase.l", result.stdout)
        self.assertIn("move.l app_SegList(a2),", result.stdout)
        self.assertIn("h0dl_ExecBase:", result.stdout)
        self.assertIn("jsr _LVOForbid(a6)", result.stdout)
        self.assertNotIn("CANDIDATE: indirect_call", result.stdout)

    def test_analyze_amiga_openlibrary_name_effect_persists_string_domain_payload(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "openlibrary_name_effect_payload.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._analyze_file_path("amiga-hunk", output_path)
        effects = payload["sections"][0]["recovered_platform_effects"]
        self.assertTrue(
            any(
                effect["kind"] == 4
                and effect["reg_kind"] == 2
                and effect["reg_index"] == 1
                and effect["type_name"] == "UBYTE *"
                and effect["semantic_kind"] == "string_ptr"
                and effect["value_domain_name"] == "amiga.library_name"
                and effect["has_constant_value"] == 1
                for effect in effects
            ),
            effects,
        )

    def test_analyze_amiga_platform_calls_report_version_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "alloc_asl_request.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(AMIGA_ASL_ALLOC_REQUEST_SOURCE, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._analyze_file_path("amiga-hunk", output_path)
        section = payload["sections"][0]
        calls = section["recovered_platform_calls"]
        self.assertGreater(section["recovered_platform_call_count"], 0)
        self.assertTrue(
            any(
                call["symbol_name"] == "_LVOAllocAslRequest"
                and call["available_since"] == "2.0"
                and call["fd_version"] == "36"
                for call in calls
            ),
            calls,
        )

    def test_disassemble_amiga_code_ptr_input_discovers_worker_code(self) -> None:
        source = """\
_LVOAddTask EQU -282

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    movea.l #$0000001A,a2
    movea.l #$0000001A,a3
    jsr _LVOAddTask(a6)
    movea.l (a7)+,a6
    rts
    moveq.l #0,d0
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "addtask_code_ptr.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOAddTask(a6)", text)
        self.assertRegex(text, r"h0_[0-9A-F]+:\r?\n\s+moveq\.l #0,d0\r?\n\s+rts")

    def test_disassemble_amiga_hook_input_local_frame_reload_resolves_callback(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOCallHookPkt EQU -102
app_UtilityBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l util_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_UtilityBase(a6)
    lea.l hook_data(pc),a0
    movea.l a7,a5
    movea.l app_UtilityBase(a6),a2
    jsr _LVOCallHookPkt(a2)
    move.l a0,$0010(a5)
    movea.l $0010(a5),a1
    movea.l $0008(a1),a2
    jsr (a2)
    rts

util_name:
    DC.B "utility.library",0
    EVEN
hook_data:
    DC.L 0,0,0,0,0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "callhookpkt_frame.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOCallHookPkt(a2)", text)
        self.assertIn("move.l a0,$0010(a5)", text)
        self.assertIn("movea.l $0010(a5),a1", text)
        self.assertIn("movea.l h_Entry(a1),a2", text)
        self.assertRegex(text, r"jsr \(a2\)\s+; KNOWN: callback field h_Entry from HOOK")

    def test_disassemble_amiga_hook_input_movem_restore_resolves_callback(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOCallHookPkt EQU -102
app_UtilityBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l util_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_UtilityBase(a6)
    lea.l hook_data(pc),a0
    movea.l app_UtilityBase(a6),a2
    jsr _LVOCallHookPkt(a2)
    movem.l a0,-(a7)
    movea.l $0004.w,a0
    movem.l (a7)+,a1
    movea.l $0008(a1),a2
    jsr (a2)
    rts

util_name:
    DC.B "utility.library",0
    EVEN
hook_data:
    DC.L 0,0,0,0,0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "callhookpkt_movem.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("movem.l a0,-(a7)", text)
        self.assertIn("movem.l (a7)+,a1", text)
        self.assertIn("movea.l h_Entry(a1),a2", text)
        self.assertRegex(text, r"jsr \(a2\)\s+; KNOWN: callback field h_Entry from HOOK")

    def test_disassemble_amiga_open_access_mode_renders_symbolically(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
app_DOSBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    lea.l file_name(pc),a0
    move.l a0,d1
    move.l #$000003ED,d2
    moveq.l #_LVOOpen,d0
    bsr.w sub_B0D6
    rts

sub_B0D6:
    move.l a6,-(a7)
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
file_name:
    DC.B "x",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "open_mode_domain.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("move.l #MODE_OLDFILE,d2", text)
        self.assertIn("; KNOWN: DOSBase _LVOOpen fallback via local wrapper", text)

    def test_disassemble_amiga_open_access_mode_renders_symbolically_via_local_transport(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
app_DOSBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    lea.l file_name(pc),a0
    move.l a0,d1
    movea.l a7,a5
    move.l #$000003ED,d0
    move.l d0,$0010(a5)
    move.l $0010(a5),d2
    moveq.l #_LVOOpen,d0
    bsr.w sub_B0D6
    rts

sub_B0D6:
    move.l a6,-(a7)
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
file_name:
    DC.B "x",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "open_mode_domain_local.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("move.l #MODE_OLDFILE,d0", text)
        self.assertIn("move.l d0,$0010(a5)", text)
        self.assertIn("move.l $0010(a5),d2", text)
        self.assertIn("; KNOWN: DOSBase _LVOOpen fallback via local wrapper", text)

    def test_disassemble_amiga_open_access_mode_renders_symbolically_via_stack_wrapper(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
app_DOSBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    pea.l $03ED.w
    pea.l file_name(pc)
    jsr open_wrapper
    lea.l 8(a7),a7
    rts

open_wrapper:
    movem.l d2/a6,-(a7)
    movea.l app_DOSBase(a6),a6
    movem.l $000C(a7),d1-d2
    jsr _LVOOpen(a6)
    movem.l (a7)+,d2/a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
file_name:
    DC.B "x",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "open_mode_domain_stack_wrapper.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("pea.l MODE_OLDFILE.w", text)
        self.assertIn("movem.l $000C(a7),d1-d2", text)

    def test_disassemble_amiga_open_access_mode_renders_symbolically_via_cross_hunk_stack_wrapper(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
app_DOSBase EQU 4280

    SECTION caller,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    pea.l $03ED.w
    pea.l file_name(pc)
    jsr open_wrapper
    lea.l 8(a7),a7
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
file_name:
    DC.B "x",0
    EVEN
    DC.W 0

    SECTION wrappers,code
open_wrapper:
    movem.l d2/a6,-(a7)
    movea.l app_DOSBase(a6),a6
    movem.l $000C(a7),d1-d2
    jsr _LVOOpen(a6)
    movem.l (a7)+,d2/a6
    rts
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "open_mode_domain_cross_hunk_stack_wrapper.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("pea.l MODE_OLDFILE.w", text)
        self.assertIn("jsr h1_DOSOpen.l", text)
        self.assertNotIn("; KNOWN: DOSBase _LVOOpen fallback via local wrapper", text)

    def test_analyze_amiga_cross_hunk_success_helper_carries_output_type(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
app_FH EQU 4284

    SECTION caller,code
start:
    jsr helper_open
    move.l d2,app_FH(a6)
    rts
    DC.L 0

    SECTION helper,code
helper_open:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l d0,a6
    lea.l name_buf(pc),a0
    move.l a0,d1
    move.l #$3ED,d2
    jsr _LVOOpen(a6)
    movea.l (a7)+,a6
    tst.l d0
    beq.s helper_open_fail
    move.l d0,d2
    moveq.l #0,d0
    rts
helper_open_fail:
    movea.l (a7)+,a6
    moveq.l #-1,d0
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
name_buf:
    DC.B "x",0
    EVEN
    DC.L 0
    DC.L 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "cross_hunk_success_helper_analysis.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            payload = self._analyze_file_path("amiga-hunk", output_path)
        effects = payload["sections"][0]["recovered_platform_effects"]
        self.assertTrue(
            any(
                effect["displacement"] == 4284
                and effect["type_name"] == "FileHandle"
                for effect in effects
            ),
            effects,
        )

    def test_disassemble_amiga_cross_hunk_stack_wrapper_comments_callee_args(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
MODE_OLDFILE EQU 1005
app_DOSBase EQU 4280

    SECTION caller,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    pea.l MODE_OLDFILE.w
    pea.l file_name(pc)
    jsr open_wrapper
    addq.l #8,a7
    rts
file_name:
    DC.B "s:startup-sequence",0
    EVEN
dos_name:
    DC.B "dos.library",0
    EVEN
    DC.L 0
    DC.W 0

    SECTION wrapper,code
open_wrapper:
    movea.l app_DOSBase(a6),a6
    move.l 4(a7),d1
    move.l 8(a7),d2
    jsr _LVOOpen(a6)
    rts
    DC.L 0
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "cross_hunk_stack_wrapper_args.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
            payload = self._analyze_file_path("amiga-hunk", output_path)
        self.assertIn("movea.l app_DOSBase(a6),a6", text)
        self.assertIn("jsr _LVOOpen(a6)", text)
        self.assertRegex(text, r"move\.l \$0004\(a7\),d1\s+; KNOWN: arg \+4 name STRPTR string_ptr")
        self.assertRegex(text, r"move\.l \$0008\(a7\),d2\s+; KNOWN: arg \+8 accessMode long dos.open.access_mode")
        args = payload["sections"][1]["recovered_function_args"]
        self.assertTrue(any(arg["stack_offset"] == 4 and arg["symbol_name"] == "name" for arg in args), args)
        self.assertTrue(
            any(arg["stack_offset"] == 8 and arg["value_domain_name"] == "dos.open.access_mode" for arg in args),
            args,
        )

    def test_disassemble_amiga_stack_wrapper_args_do_not_cross_function_blocks(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
MODE_OLDFILE EQU 1005
app_DOSBase EQU 4280

    SECTION caller,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    pea.l MODE_OLDFILE.w
    pea.l file_name(pc)
    jsr open_wrapper
    addq.l #8,a7
    jsr other_function
    rts
file_name:
    DC.B "s:startup-sequence",0
    EVEN
dos_name:
    DC.B "dos.library",0
    EVEN
    DC.L 0
    DC.W 0
    DC.W 0

    SECTION wrapper,code
open_wrapper:
    movea.l app_DOSBase(a6),a6
    move.l 4(a7),d1
    move.l 8(a7),d2
    jsr _LVOOpen(a6)
    rts
other_function:
    move.l 4(a7),d1
    rts
    DC.W 0
    DC.L 0
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "stack_wrapper_arg_blocks.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertRegex(text, r"move\.l \$0004\(a7\),d1\s+; KNOWN: arg \+4 name STRPTR string_ptr")
        self.assertGreaterEqual(text.count("move.l $0004(a7),d1"), 2)
        self.assertEqual(2, text.count("KNOWN: arg +4 name STRPTR string_ptr"))

    def test_disassemble_amiga_stack_wrapper_args_flow_through_helper_chain(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
MODE_OLDFILE EQU 1005
app_DOSBase EQU 4280

    SECTION caller,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    pea.l MODE_OLDFILE.w
    pea.l file_name(pc)
    jsr middle_wrapper
    addq.l #8,a7
    rts
file_name:
    DC.B "s:startup-sequence",0
    EVEN
dos_name:
    DC.B "dos.library",0
    EVEN
    DC.L 0
    DC.W 0

    SECTION middle,code
middle_wrapper:
    jsr open_wrapper
    rts
    DC.L 0
    DC.W 0
    DC.W 0

    SECTION wrapper,code
open_wrapper:
    movea.l app_DOSBase(a6),a6
    move.l 4(a7),d1
    move.l 8(a7),d2
    jsr _LVOOpen(a6)
    rts
    DC.L 0
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "stack_wrapper_helper_chain.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
            payload = self._analyze_file_path("amiga-hunk", output_path)
        self.assertIn("movea.l app_DOSBase(a6),a6", text)
        self.assertIn("jsr _LVOOpen(a6)", text)
        self.assertRegex(text, r"move\.l \$0004\(a7\),d1\s+; KNOWN: arg \+4 name STRPTR string_ptr")
        args = payload["sections"][2]["recovered_function_args"]
        self.assertTrue(any(arg["stack_offset"] == 4 and arg["symbol_name"] == "name" for arg in args), args)

    def test_disassemble_amiga_exec_stack_wrapper_gets_inferred_label_and_push_comment(self) -> None:
        source = """\
_LVOFreeEntry EQU -228

    SECTION caller,code
start:
    move.l d0,-(a7)
    jsr exec_free_entry_wrapper
    addq.l #4,a7
    rts

    SECTION wrapper,code
exec_free_entry_wrapper:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    movea.l 8(a7),a0
    jsr _LVOFreeEntry(a6)
    movea.l (a7)+,a6
    rts
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "exec_free_entry_wrapper.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("h1_ExecFreeEntry:", text)
        self.assertIn("jsr h1_ExecFreeEntry", text)
        self.assertRegex(text, r"move\.l d0,-\(a7\)\s+; KNOWN: arg \+4 entry struct MemList \*")
        self.assertRegex(text, r"movea\.l \$0008\(a7\),a0\s+; KNOWN: arg \+8 entry struct MemList \*")

    def test_disassemble_amiga_stack_wrapper_args_stop_on_untracked_sp_adjustment(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
MODE_OLDFILE EQU 1005
app_DOSBase EQU 4280

    SECTION caller,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    pea.l MODE_OLDFILE.w
    pea.l file_name(pc)
    jsr open_wrapper
    addq.l #8,a7
    rts
file_name:
    DC.B "s:startup-sequence",0
    EVEN
dos_name:
    DC.B "dos.library",0
    EVEN
    DC.L 0
    DC.W 0

    SECTION wrapper,code
open_wrapper:
    movea.l app_DOSBase(a6),a6
    subq.l #4,a7
    move.l 8(a7),d1
    move.l 12(a7),d2
    jsr _LVOOpen(a6)
    addq.l #4,a7
    rts
    DC.L 0
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "stack_wrapper_untracked_sp.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
            payload = self._analyze_file_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOOpen(a6)", text)
        self.assertNotIn("KNOWN: arg +4 name", text)
        self.assertNotIn("KNOWN: arg +8 accessMode", text)
        self.assertEqual([], payload["sections"][1]["recovered_function_args"])

    def test_disassemble_amiga_allocmem_flags_render_symbolically(self) -> None:
        source = """\
_LVOAllocMem EQU -198

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    move.l #$00000020,d0
    move.l #$00010001,d1
    jsr _LVOAllocMem(a6)
    movea.l (a7)+,a6
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "allocmem_domain.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("move.l #MEMF_CLEAR|MEMF_PUBLIC,d1", text)
        self.assertIn("jsr _LVOAllocMem(a6)", text)

    def test_disassemble_amiga_io_field_domains_render_symbolically(self) -> None:
        source = """\
_LVOOpenDevice EQU -444
app_IO EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l app_IO(a6),a1
    jsr _LVOOpenDevice(a6)
    movea.l (a7)+,a6
    movea.l app_IO(a6),a1
    move.w #2,$001C(a1)
    move.b #1,$001E(a1)
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "io_field_domains.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("movea.l app_iorequest(a6),a1", text)
        self.assertIn("move.w #CMD_READ,IO_COMMAND(a1)", text)
        self.assertIn("move.b #IOF_QUICK,IO_FLAGS(a1)", text)

    def test_disassemble_amiga_io_field_domain_compare_renders_symbolically_after_reg_load(self) -> None:
        source = """\
_LVOOpenDevice EQU -444
app_IO EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l app_IO(a6),a1
    jsr _LVOOpenDevice(a6)
    movea.l (a7)+,a6
    movea.l app_IO(a6),a1
    move.b $001E(a1),d0
    cmpi.b #1,d0
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "io_field_domain_compare.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("move.b IO_FLAGS(a1),d0", text)
        self.assertIn("cmpi.b #IOF_QUICK,d0", text)

    def test_disassemble_amiga_createiorequest_a0_to_a1_preserves_typed_io_field(self) -> None:
        source = """\
_LVOCreateIORequest EQU -654

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOCreateIORequest(a6)
    movea.l (a7)+,a6
    movea.l a0,a1
    movea.l $0014(a1),a2
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "createiorequest.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOCreateIORequest(a6)", text)
        self.assertIn("movea.l a0,a1", text)
        self.assertIn("movea.l IO_DEVICE(a1),a2", text)

    def test_disassemble_amiga_typed_hook_callback_field_uses_named_field(self) -> None:
        source = """\
_LVOSetIntVector EQU -162

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOSetIntVector(a6)
    movea.l (a7)+,a6
    movea.l d0,a0
    movea.l $0012(a0),a1
    jsr (a1)
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "setedithook.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOSetIntVector(a6)", text)
        self.assertIn("movea.l IS_CODE(a0),a1", text)
        self.assertRegex(text, r"jsr \(a1\)\s+; KNOWN: callback field IS_CODE from IS")

    def test_disassemble_amiga_findport_d0_to_typed_mp_slot_field(self) -> None:
        source = """\
_LVOFindPort EQU -390
app_MP EQU 4284

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOFindPort(a6)
    movea.l (a7)+,a6
    move.l d0,app_MP(a6)
    movea.l app_MP(a6),a1
    movea.l $0010(a1),a0
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "findport.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOFindPort(a6)", text)
        self.assertIn("move.l d0,app_port(a6)", text)
        self.assertIn("movea.l app_port(a6),a1", text)
        self.assertIn("movea.l MP_SIGTASK(a1),a0", text)

    def test_disassemble_amiga_findport_d0_via_d2_to_typed_mp_slot_field(self) -> None:
        source = """\
_LVOFindPort EQU -390
app_MP EQU 4284

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOFindPort(a6)
    movea.l (a7)+,a6
    move.l d0,d2
    move.l d2,app_MP(a6)
    movea.l app_MP(a6),a1
    movea.l $0010(a1),a0
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "findport_d2.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("move.l d0,d2", text)
        self.assertIn("move.l d2,app_port(a6)", text)
        self.assertIn("movea.l app_port(a6),a1", text)
        self.assertIn("movea.l MP_SIGTASK(a1),a0", text)

    def test_disassemble_amiga_findport_d0_to_multiple_typed_mp_slots(self) -> None:
        source = """\
_LVOFindPort EQU -390
app_MP1 EQU 4284
app_MP2 EQU 4288

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOFindPort(a6)
    movea.l (a7)+,a6
    move.l d0,app_MP1(a6)
    move.l d0,app_MP2(a6)
    movea.l app_MP2(a6),a1
    movea.l $0010(a1),a0
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "findport_multi_slot.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("app_port_10BC EQU 4284", text)
        self.assertIn("app_port_10C0 EQU 4288", text)
        self.assertIn("move.l d0,app_port_10BC(a6)", text)
        self.assertIn("move.l d0,app_port_10C0(a6)", text)
        self.assertIn("movea.l app_port_10C0(a6),a1", text)
        self.assertIn("movea.l MP_SIGTASK(a1),a0", text)

    def test_disassemble_amiga_movem_stack_restore_preserves_typed_mp_field(self) -> None:
        source = """\
_LVOFindPort EQU -390

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOFindPort(a6)
    movea.l (a7)+,a6
    movea.l d0,a0
    moveq.l #0,d1
    movem.l d1/a0,-(a7)
    moveq.l #1,d1
    movea.l $0004.w,a0
    movem.l (a7)+,d2/a1
    movea.l $0010(a1),a2
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "findport_movem.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("movem.l d1/a0,-(a7)", text)
        self.assertIn("movem.l (a7)+,d2/a1", text)
        self.assertIn("movea.l MP_SIGTASK(a1),a2", text)

    def test_disassemble_amiga_local_frame_slot_reload_preserves_typed_mp_field(self) -> None:
        source = """\
_LVOFindPort EQU -390

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOFindPort(a6)
    movea.l (a7)+,a6
    movea.l a7,a5
    move.l d0,$0010(a5)
    movea.l $0010(a5),a1
    movea.l $0010(a1),a0
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "findport_frame_slot.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("movea.l a7,a5", text)
        self.assertIn("move.l d0,$0010(a5)", text)
        self.assertIn("movea.l $0010(a5),a1", text)
        self.assertIn("movea.l MP_SIGTASK(a1),a0", text)

    def test_disassemble_amiga_dos_wrapper_examine_types_fileinfoblock_argument(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOExamine EQU -102
app_DOSBase EQU 4280
app_FileInfoBlock EQU 4284

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    lea.l app_FileInfoBlock(a6),a0
    move.l a0,d2
    moveq.l #_LVOExamine,d0
    bsr.w sub_B0D6
    move.l $007C(a0),d1
    rts

sub_B0D6:
    move.l a6,-(a7)
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "dos_wrapper_examine.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("move.l d0,app_DOSBase(a6)", text)
        self.assertIn("lea.l app_fileinfoblock+fib_DiskKey(a6),a0", text)
        self.assertIn("move.l a0,d2", text)
        self.assertIn("moveq.l #_LVOExamine,d0", text)
        self.assertIn("; KNOWN: DOSBase _LVOExamine fallback via local wrapper", text)
        self.assertIn("move.l fib_Size(a0),d1", text)

    def test_disassemble_amiga_dos_wrapper_examine_types_fileinfoblock_argument_via_a1_d2_transport(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOExamine EQU -102
app_DOSBase EQU 4280
app_FileInfoBlock EQU 4284

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    lea.l app_FileInfoBlock(a6),a0
    movea.l a0,a1
    move.l a1,d2
    moveq.l #_LVOExamine,d0
    bsr.w sub_B0D6
    move.l $007C(a0),d1
    rts

sub_B0D6:
    move.l a6,-(a7)
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "dos_wrapper_examine_via_a1_d2.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("move.l d0,app_DOSBase(a6)", text)
        self.assertIn("lea.l app_fileinfoblock+fib_DiskKey(a6),a0", text)
        self.assertIn("movea.l a0,a1", text)
        self.assertIn("move.l a1,d2", text)
        self.assertIn("; KNOWN: DOSBase _LVOExamine fallback via local wrapper", text)
        self.assertIn("move.l fib_Size(a0),d1", text)

    def test_disassemble_amiga_dos_wrapper_output_result_via_d2_to_typed_filehandle_slot(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOutput EQU -60
app_DOSBase EQU 4280
app_FH EQU 4284

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    moveq.l #_LVOOutput,d0
    bsr.w sub_B0D6
    move.l d0,d2
    move.l d2,app_FH(a6)
    move.l app_FH(a6),d1
    rts

sub_B0D6:
    move.l a6,-(a7)
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "dos_wrapper_output_result_via_d2.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("moveq.l #_LVOOutput,d0", text)
        self.assertIn("; KNOWN: DOSBase _LVOOutput fallback via local wrapper", text)
        self.assertIn("move.l d0,d2", text)
        self.assertIn("app_file EQU 4284", text)
        self.assertIn("move.l d2,app_file+fh_Link(a6)", text)
        self.assertIn("move.l app_file+fh_Link(a6),d1", text)

    def test_disassemble_amiga_dos_wrapper_direct_long_immediate_selector(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
app_DOSBase EQU 4280

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    lea.l -$000C(a7),a7
    move.l a7,d1
    move.l #$FFFFFF40,d0
    bsr.w sub_B0D6
    move.l (a7),d0
    lea.l $000C(a7),a7
    rts

sub_B0D6:
    move.l a6,-(a7)
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "dos_wrapper_long_selector.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("move.l #$FFFFFF40,d0", text)
        self.assertIn("; KNOWN: DOSBase _LVODateStamp fallback via local wrapper", text)

    def test_disassemble_amiga_local_success_helper_chain_types_filehandle_slot(self) -> None:
        source = """\
_LVOOpenLibrary EQU -552
_LVOOpen EQU -30
app_DOSBase EQU 4280
app_FH EQU 4284

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    lea.l dos_name(pc),a1
    jsr _LVOOpenLibrary(a6)
    movea.l (a7)+,a6
    move.l d0,app_DOSBase(a6)
    bsr.w helper_outer
    move.l d2,app_FH(a6)
    move.l app_FH(a6),d1
    rts

helper_outer:
    bsr.w helper_open
    tst.l d0
    bne.s helper_fail
    rts
helper_fail:
    rts

helper_open:
    lea.l name_buf(pc),a0
    move.l a0,d1
    move.l #$3EE,d2
    moveq.l #_LVOOpen,d0
    bsr.w sub_B0D6
    tst.l d0
    beq.s helper_open_fail
    move.l d0,d2
    moveq.l #0,d0
    rts
helper_open_fail:
    moveq.l #-1,d0
    rts

sub_B0D6:
    move.l a6,-(a7)
    movea.l app_DOSBase(a6),a6
    jsr $0(a6,d0.w)
    movea.l (a7)+,a6
    rts

dos_name:
    DC.B "dos.library",0
    EVEN
name_buf:
    DC.B "x",0
    EVEN
    DC.W 0
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "dos_wrapper_success_helper_chain.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("; KNOWN: DOSBase _LVOOpen fallback via local wrapper", text)
        self.assertIn("app_file EQU 4284", text)
        self.assertIn("move.l d2,app_file+fh_Link(a6)", text)
        self.assertIn("move.l app_file+fh_Link(a6),d1", text)

    def test_disassemble_amiga_local_success_helper_chain_types_direct_mp_field_use(self) -> None:
        source = """\
_LVOCreateIORequest EQU -654

    SECTION section,code
start:
    bsr.w helper_hook
    movea.l d2,a1
    movea.l $0014(a1),a0
    rts

helper_hook:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOCreateIORequest(a6)
    movea.l (a7)+,a6
    tst.l a0
    beq.s helper_hook_fail
    move.l a0,d2
    moveq.l #0,d0
    rts
helper_hook_fail:
    moveq.l #-1,d0
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "helper_findport_direct_mp_field.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("movea.l d2,a1", text)
        self.assertIn("movea.l IO_DEVICE(a1),a0", text)

    def test_disassemble_amiga_local_success_helper_chain_types_slot_store_after_a1_transport(self) -> None:
        source = """\
_LVOCreateIORequest EQU -654
app_IO EQU 4280

    SECTION section,code
start:
    bsr.w helper_hook
    movea.l d2,a1
    move.l a1,app_IO(a6)
    movea.l app_IO(a6),a2
    movea.l $0014(a2),a3
    rts

helper_hook:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOCreateIORequest(a6)
    movea.l (a7)+,a6
    tst.l a0
    beq.s helper_hook_fail
    move.l a0,d2
    moveq.l #0,d0
    rts
helper_hook_fail:
    moveq.l #-1,d0
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "helper_createiorequest_slot_store.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("movea.l d2,a1", text)
        self.assertIn("move.l a1,app_ioreq(a6)", text)
        self.assertIn("movea.l app_ioreq(a6),a2", text)
        self.assertIn("movea.l IO_DEVICE(a2),a3", text)

    def test_disassemble_amiga_nested_typed_field_propagation_mp_to_lh(self) -> None:
        source = """\
_LVOFindPort EQU -390
app_MP EQU 4284

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOFindPort(a6)
    movea.l (a7)+,a6
    move.l d0,app_MP(a6)
    movea.l app_MP(a6),a1
    movea.l $0014(a1),a2
    movea.l $0000(a2),a3
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "findport_nested.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("jsr _LVOFindPort(a6)", text)
        self.assertIn("movea.l app_port(a6),a1", text)
        self.assertIn("movea.l MP_MSGLIST(a1),a2", text)
        self.assertIn("movea.l LH_HEAD(a2),a3", text)

    def test_disassemble_amiga_typed_a2_store_to_slot_reloads_nested_type(self) -> None:
        source = """\
_LVOFindPort EQU -390
app_MP EQU 4284
app_LH EQU 4288

    SECTION section,code
start:
    move.l a6,-(a7)
    movea.l $0004.w,a6
    jsr _LVOFindPort(a6)
    movea.l (a7)+,a6
    move.l d0,app_MP(a6)
    movea.l app_MP(a6),a1
    movea.l $0014(a1),a2
    move.l a2,app_LH(a6)
    movea.l app_LH(a6),a3
    movea.l $0000(a3),a4
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            output_path = Path(tmp) / "findport_a2_slot_nested.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, output_path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            text = self._disassemble_real_path("amiga-hunk", output_path)
        self.assertIn("movea.l MP_MSGLIST(a1),a2", text)
        self.assertIn("move.l a2,app_LH+LH_HEAD(a6)", text)
        self.assertIn("movea.l app_LH+LH_HEAD(a6),a3", text)
        self.assertIn("movea.l LH_HEAD(a3),a4", text)

    def test_disassemble_genam_flags_current_relative_branches_as_violations(self) -> None:
        text = self._disassemble_real_path("amiga-hunk", GENAM_BIN)
        branch_relative = re.compile(r"^\s*b[a-z]+\.[bwlsg]?\s+\*[+-]?\d*")
        bare = [line for line in text.splitlines()
                if branch_relative.search(line) and "VIOLATION:" not in line]
        self.assertEqual([], bare)

    def test_disassemble_bin_gen_flags_current_relative_branches_as_violations(self) -> None:
        text = self._disassemble_real_path("atari-st", BIN_GEN_BIN)
        branch_relative = re.compile(r"^\s*b[a-z]+\.[bwlsg]?\s+\*[+-]?\d*")
        bare = [line for line in text.splitlines()
                if branch_relative.search(line) and "VIOLATION:" not in line]
        self.assertEqual([], bare)

    def test_genam_latest_fixture_matches_current_disassembly(self) -> None:
        self.assertTrue(GENAM_LATEST.exists(), GENAM_LATEST)
        self.assertEqual(self._disassemble_real_path("amiga-hunk", GENAM_BIN), self._read_fixture_text(GENAM_LATEST))

    def test_genam_latest_does_not_emit_resident_library_rs_block(self) -> None:
        rendered = self._disassemble_real_path("amiga-hunk", GENAM_BIN)
        self.assertNotIn("RSSET LIB_SIZE", rendered)
        self.assertIn("RSSET 0", rendered)
        self.assertIn("app_SIZEOF EQU __RS", rendered)

    def test_bin_gen_latest_fixture_matches_current_disassembly(self) -> None:
        self.assertTrue(BIN_GEN_LATEST.exists(), BIN_GEN_LATEST)
        self.assertEqual(self._disassemble_real_path("atari-st", BIN_GEN_BIN), self._read_fixture_text(BIN_GEN_LATEST))

    def test_genam_benchmark_matches_current_stats(self) -> None:
        self.assertTrue(GENAM_BENCHMARK.exists(), GENAM_BENCHMARK)
        current = self._normalized_benchmark(self._benchmark_real_path("amiga-hunk", GENAM_BIN))
        committed = self._normalized_benchmark(self._read_fixture_json(GENAM_BENCHMARK))
        self.assertEqual(current, committed)

    def test_bin_gen_benchmark_matches_current_stats(self) -> None:
        self.assertTrue(BIN_GEN_BENCHMARK.exists(), BIN_GEN_BENCHMARK)
        current = self._normalized_benchmark(self._benchmark_real_path("atari-st", BIN_GEN_BIN))
        committed = self._normalized_benchmark(self._read_fixture_json(BIN_GEN_BENCHMARK))
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
        self.assertTrue(GENAM_LATEST.exists(), GENAM_LATEST)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            rebuilt_path = Path(tmp) / "GenAm.roundtrip.exe"
            source_path = Path(tmp) / "GenAm.vasm.s"
            source_path.write_text(self._disassemble_real_path("amiga-hunk", GENAM_BIN, syntax="vasm"), encoding="utf-8")
            assemble = subprocess.run(
                [str(vasm), "-m68000", "-Fhunkexe", "-no-opt", "-quiet", f"-I{GENAM_INCLUDE_DIR}", "-o",
                 str(rebuilt_path), str(source_path)],
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
            self.assertIn("bcs.b h0_000A", result.stdout)
            self.assertIn("h0_000A:", result.stdout)
            self.assertIn("moveq.l #98,d0", result.stdout)
            self.assertNotIn("DC.B    $70,$62", result.stdout)

    def test_disassemble_file_revisits_existing_blocks_when_loop_state_widens(self) -> None:
        source = """\
    SECTION section,code
start:
    moveq.l #0,d6
    bra.w loop
loop:
    bsr.w helper
after_call:
    tst.l d6
    bne.w target
    move.l $0004(a7),d6
    bra.w join
target:
    moveq.l #1,d0
join:
    tst.l $0008(a7)
    bne.w loop
    rts
helper:
    rts
"""
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "loop_widen.exe"
            assemble = self._assemble_synthetic_amiga_hunk_source(source, path)
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            result = subprocess.run(
                [str(self.file_exe), "disassemble-file", "amiga-hunk", str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("moveq.l #1,d0", result.stdout)
        self.assertNotIn("DC.B    $70,$01", result.stdout)

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
            self.assertIn('INCLUDE "GEMDOS.I"', result.stdout)
            self.assertNotIn("GEMDOS_Dgetdrv EQU 25", result.stdout)
            self.assertIn("move.w #d_getdrv,-(a7)", result.stdout)
            self.assertIn("trap #1", result.stdout)
            self.assertRegex(result.stdout, r"addq\.l #2,a7\s+; KNOWN: stack cleanup for d_getdrv pop 2")

    def test_disassemble_real_bin_gen_emits_atari_os_symbols(self) -> None:
        text = self._disassemble_real_path("atari-st", BIN_GEN_BIN, "genam")
        self.assertIn('INCLUDE "GEMDOS.I"', text)
        self.assertIn('INCLUDE "XBIOS.I"', text)
        self.assertNotIn("GEMDOS_Cconout EQU 2", text)
        self.assertNotIn("GEMDOS_Cconrs EQU 10", text)
        self.assertNotIn("GEMDOS_Fwrite EQU 64", text)
        self.assertNotIn("GEMDOS_Crawcin EQU 7", text)
        self.assertNotIn("GEMDOS_Super EQU 32", text)
        self.assertNotIn("GEMDOS_Tgetdate EQU 42", text)
        self.assertNotIn("GEMDOS_Tgettime EQU 44", text)
        self.assertNotIn("GEMDOS_Pterm EQU 76", text)
        self.assertNotIn("XBIOS_Supexec EQU 38", text)
        self.assertNotIn("GEMDOS_", text)
        self.assertNotIn("XBIOS_", text)
        self.assertIn("move.w #c_conout,-(a7)", text)
        self.assertIn("trap #1", text)
        self.assertIn("move.w #c_conrs,-(a7)", text)
        self.assertIn("move.w #c_conrs,-(a7)", text)
        self.assertIn("move.w #super,-(a7)", text)
        self.assertIn("move.w #super,-(a7)", text)
        self.assertIn("move.w #p_term,-(a7)", text)
        self.assertIn("move.w #p_term,-(a7)", text)
        self.assertIn("trap #14", text)
        self.assertRegex(text, r"addq\.l #6,a7\s+; KNOWN: stack cleanup for supexec pop 6")
        self.assertIn("move.w #c_rawcin,(a7)", text)
        self.assertIn("move.w #c_rawcin,(a7)", text)
        self.assertIn("move.w #t_getdate,-(a7)", text)
        self.assertIn("move.w #t_getdate,-(a7)", text)
        self.assertIn("move.w #t_gettime,-(a7)", text)
        self.assertIn("move.w #t_gettime,-(a7)", text)
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
        self.assertTrue(BIN_GEN_LATEST.exists(), BIN_GEN_LATEST)
        self.assertTrue(vasm.exists(), vasm)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            rebuilt_path = Path(tmp) / "BIN_GEN.roundtrip.ttp"
            source_path = Path(tmp) / "BIN_GEN.vasm.s"
            source_path.write_text(self._disassemble_real_path("atari-st", BIN_GEN_BIN, syntax="vasm"), encoding="utf-8")
            assemble = subprocess.run(
                [str(vasm), "-Ftos", "-nosym", "-quiet", f"-I{BIN_GEN_INCLUDE_DIR}", "-o", str(rebuilt_path), str(source_path)],
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

    def test_render_source_file_rejects_unknown_minimum_os_version(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / "sample.s"
            path.write_text("SECTION code,code\nstart:\n    rts\n", encoding="utf-8")
            result = subprocess.run(
                [
                    str(self.asm_exe),
                    "render-source-file",
                    "--min-os-version",
                    "2.1",
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
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown minimum os version: 2.1", result.stderr)

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
