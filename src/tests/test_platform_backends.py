from __future__ import annotations

import os
import unittest
from pathlib import Path

from m68k.hunk_parser import parse_file

from src.tests._platform_backend_test_utils import FIXTURE_DIR
from src.tests._platform_backend_test_utils import PlatformBackendTestCaseMixin
from src.tests._platform_backend_test_utils import make_synthetic_atari_prg
from src.tests._platform_backend_test_utils import make_synthetic_extended_mem_hunk_object
from src.tests._platform_backend_test_utils import make_synthetic_hunk_object_with_ext
from src.tests._platform_backend_test_utils import make_synthetic_hunk_object_with_extra_relocs
from src.tests._platform_backend_test_utils import make_synthetic_hunkexe


def _fixture_summary(path: Path) -> dict[str, object]:
    hf = parse_file(path)
    return {
        "file_kind": "executable" if hf.is_executable else "object" if hf.is_object else "library",
        "section_count": len(hf.hunks),
        "sections": [
            {
                "kind": h.type_name.lower(),
                "name": h.name,
                "mem_type": h.mem_type,
                "alloc_size": h.alloc_size,
                "stored_size": h.stored_size,
                "data_hex": h.data.hex(),
                "symbol_count": len(h.symbols) + len(h.ext_defs),
                "fixup_count": sum(len(rel.offsets) for rel in h.relocs) + sum(len(ref.offsets) for ref in h.ext_refs),
                "debug_size": len(h.debug_data),
            }
            for h in hf.hunks
        ],
    }


def _summary_core(summary: dict[str, object]) -> dict[str, object]:
    return {
        "file_kind": summary["file_kind"],
        "section_count": summary["section_count"],
        "sections": [
            {
                "kind": section["kind"],
                "name": section["name"],
                "mem_type": section["mem_type"],
                "alloc_size": section["alloc_size"],
                "stored_size": section["stored_size"],
                "data_hex": section["data_hex"],
                "symbol_count": section["symbol_count"],
                "fixup_count": section["fixup_count"],
                "debug_size": section["debug_size"],
            }
            for section in summary["sections"]
        ],
    }


class PlatformBackendTests(PlatformBackendTestCaseMixin, unittest.TestCase):
    def test_amiga_hunk_backend_roundtrips_synthetic_hunkexe(self) -> None:
        sample = make_synthetic_hunkexe()
        self.assertEqual(self.roundtrip_buffer("amiga-hunk", sample), sample)

    def test_amiga_hunk_backend_roundtrips_synthetic_hunk_object_with_ext(self) -> None:
        sample = make_synthetic_hunk_object_with_ext()
        self.assertEqual(self.roundtrip_buffer("amiga-hunk", sample), sample)

    def test_amiga_hunk_backend_roundtrips_synthetic_extended_mem_object(self) -> None:
        sample = make_synthetic_extended_mem_hunk_object()
        self.assertEqual(self.roundtrip_buffer("amiga-hunk", sample), sample)

    def test_amiga_hunk_backend_roundtrips_synthetic_object_with_extra_relocs(self) -> None:
        sample = make_synthetic_hunk_object_with_extra_relocs()
        self.assertEqual(self.roundtrip_buffer("amiga-hunk", sample), sample)

    def test_amiga_hunk_backend_matches_python_parser_on_small_fixtures(self) -> None:
        for name in (
            "vasm_hunk_object.o",
            "vasm_hunk_linedebug.o",
            "vasm_hunkexe_databss.exe",
            "vasm_hunk_extended_mem.o",
        ):
            path = FIXTURE_DIR / name
            expected = _fixture_summary(path)
            actual = self.inspect_buffer("amiga-hunk", path.read_bytes())
            self.assertEqual(_summary_core(actual), expected, name)

    def test_amiga_hunk_backend_roundtrips_debug_blocks(self) -> None:
        path = FIXTURE_DIR / "vasm_hunk_linedebug.o"
        self.assertEqual(self.roundtrip_buffer("amiga-hunk", path.read_bytes()), path.read_bytes())

    def test_atari_st_backend_reads_minimal_prg(self) -> None:
        sample = make_synthetic_atari_prg(b"\x4E\x75", b"\x12\x34", 6)
        actual = self.inspect_buffer("atari-st", sample)
        self.assertEqual(actual["file_kind"], "executable")
        self.assertEqual(actual["section_count"], 3)
        self.assertEqual(actual["sections"][0]["name"], "TEXT")
        self.assertEqual(actual["sections"][0]["kind"], "code")
        self.assertEqual(actual["sections"][0]["mem_type"], 0)
        self.assertEqual(actual["sections"][0]["alloc_size"], 2)
        self.assertEqual(actual["sections"][0]["stored_size"], 2)
        self.assertEqual(actual["sections"][0]["data_hex"], "4e75")
        self.assertEqual(actual["sections"][1]["name"], "DATA")
        self.assertEqual(actual["sections"][1]["kind"], "data")
        self.assertEqual(actual["sections"][1]["data_hex"], "1234")
        self.assertEqual(actual["sections"][2]["name"], "BSS")
        self.assertEqual(actual["sections"][2]["kind"], "bss")
        self.assertEqual(actual["sections"][2]["alloc_size"], 6)
        self.assertEqual(actual["sections"][2]["stored_size"], 0)
        self.assertEqual(actual["sections"][2]["data_hex"], "")

    def test_atari_st_backend_reads_prg_relocations(self) -> None:
        sample = make_synthetic_atari_prg(b"\x20\x3C\x00\x00\x20\x3C\x00\x00", b"\x00\x00\x00\x00", 0, [4, 8])
        actual = self.inspect_buffer("atari-st", sample)
        self.assertEqual(actual["file_kind"], "executable")
        self.assertEqual(actual["section_count"], 2)
        self.assertEqual(actual["sections"][0]["data_hex"], "203c0000203c0000")
        self.assertEqual(actual["sections"][1]["data_hex"], "00000000")
        self.assertEqual(actual["sections"][0]["fixup_count"], 1)
        self.assertEqual(actual["sections"][1]["fixup_count"], 1)

    def test_atari_st_backend_ignores_nonzero_relocation_flag_when_stream_exists(self) -> None:
        sample = make_synthetic_atari_prg(
            b"\x20\x3C\x00\x00",
            b"\x00\x00\x00\x00",
            0,
            [4],
            symbol_table_type=0x45585431,
            program_flags=0x01000024,
            relocation_flag=0x6F00,
        )
        actual = self.inspect_buffer("atari-st", sample)
        self.assertEqual(actual["sections"][0]["fixup_count"], 0)
        self.assertEqual(actual["sections"][1]["fixup_count"], 1)

    def test_atari_st_backend_accepts_relocation_stream_terminated_by_eof(self) -> None:
        sample = make_synthetic_atari_prg(
            b"\x20\x3C\x00\x00\x20\x3C\x00\x00",
            b"\x00\x00\x00\x00",
            0,
            [4, 8],
            terminate_relocation_stream=False,
        )
        actual = self.inspect_buffer("atari-st", sample)
        self.assertEqual(actual["sections"][0]["fixup_count"], 1)
        self.assertEqual(actual["sections"][1]["fixup_count"], 1)

    def test_atari_st_backend_accepts_zero_padded_no_relocation_tail(self) -> None:
        sample = make_synthetic_atari_prg(b"\x4E\x75", b"\x12\x34", 0) + (b"\x00" * 16)
        actual = self.inspect_buffer("atari-st", sample)
        self.assertEqual(actual["section_count"], 2)
        self.assertEqual(actual["sections"][0]["fixup_count"], 0)
        self.assertEqual(actual["sections"][1]["fixup_count"], 0)

    def test_atari_st_backend_roundtrips_symbol_table_exactly(self) -> None:
        sample = make_synthetic_atari_prg(
            b"\x4E\x75",
            b"\x12\x34",
            0,
            symbol_table=b"SYMBTABL",
            symbol_table_type=0x53594D42,
            program_flags=0x01020304,
            relocation_flag=0x1234,
        )
        self.assertEqual(self.roundtrip_buffer("atari-st", sample), sample)

    def test_atari_st_backend_rejects_multiple_text_sections(self) -> None:
        result = self.run_harness("atari-duplicate-sections")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("single TEXT and single DATA", result.stdout)


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_HEAVY_UNIT_TESTS") == "1":
        return tests
    return unittest.TestSuite()
