from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"
GENERATOR = SRC_DIR / "scripts" / "generate_platform_format_runtime.py"
STYLE_CHECKER = SRC_DIR / "scripts" / "check_c_style.py"
PYTHON = Path(sys.executable)

COMMITTED_FILES = {
    "amiga_hunk_file_runtime.h": SRC_DIR / "generated" / "amiga_hunk_file_runtime.h",
    "amiga_hunk_file_runtime.c": SRC_DIR / "generated" / "amiga_hunk_file_runtime.c",
    "amiga_hunk_file_runtime.json": SRC_DIR / "generated" / "amiga_hunk_file_runtime.json",
    "atari_st_prg_file_runtime.h": SRC_DIR / "generated" / "atari_st_prg_file_runtime.h",
    "atari_st_prg_file_runtime.c": SRC_DIR / "generated" / "atari_st_prg_file_runtime.c",
    "atari_st_prg_file_runtime.json": SRC_DIR / "generated" / "atari_st_prg_file_runtime.json",
    "atari_st_disk_file_runtime.h": SRC_DIR / "generated" / "atari_st_disk_file_runtime.h",
    "atari_st_disk_file_runtime.c": SRC_DIR / "generated" / "atari_st_disk_file_runtime.c",
    "atari_st_disk_file_runtime.json": SRC_DIR / "generated" / "atari_st_disk_file_runtime.json",
    "amiga_disk_file_runtime.h": SRC_DIR / "generated" / "amiga_disk_file_runtime.h",
    "amiga_disk_file_runtime.c": SRC_DIR / "generated" / "amiga_disk_file_runtime.c",
    "amiga_disk_file_runtime.json": SRC_DIR / "generated" / "amiga_disk_file_runtime.json",
}

AMIGA_JSON = ROOT / "knowledge" / "amiga_hunk_file.json"
ATARI_JSON = ROOT / "knowledge" / "atari_st_prg_file.json"
ATARI_DISK_JSON = ROOT / "knowledge" / "atari_st_disk_file.json"
AMIGA_DISK_JSON = ROOT / "knowledge" / "amiga_disk_file.json"


class PlatformFormatCodegenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls._outdir = Path(cls._tmp.name)
        result = subprocess.run(
            [str(PYTHON), str(GENERATOR), "--output-dir", str(cls._outdir)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            cls._tmp.cleanup()
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_amiga_kb_semantics(self) -> None:
        payload = json.loads(AMIGA_JSON.read_text(encoding="utf-8"))
        header_fields = payload["record_types"]["HUNK_HEADER"]["fields"]
        header_table = next(field for field in header_fields if field["name"] == "hunk_size_words")
        self.assertEqual(header_table["type"], "repeated_struct")
        self.assertEqual(header_table["element_fields"][1]["name"], "mem_attrs")
        self.assertEqual(header_table["element_fields"][1]["present_if"], "size_word >> 30 == 3")

        ext_record = payload["record_types"]["HUNK_EXT"]
        selector = ext_record["variant_selector"]
        self.assertEqual(selector["variants"]["EXT_DEF"], "definition")
        self.assertEqual(selector["variants"]["EXT_REF32"], "reference")
        self.assertEqual(selector["variants"]["EXT_COMMON"], "common_reference")
        self.assertEqual(payload["ext_reference_kinds"]["EXT_REF16"]["mode"], "pc_relative")
        self.assertEqual(payload["ext_reference_kinds"]["EXT_DEXT32"]["mode"], "data_relative")
        self.assertIn("HUNK_DREL32", payload["constraints"]["load_file_valid_record_types"])

    def test_atari_prg_kb_semantics(self) -> None:
        payload = json.loads(ATARI_JSON.read_text(encoding="utf-8"))
        self.assertEqual(payload["_meta"]["sources"][0]["path"], "resources/platform_atari_st/GEMDOS.TXT")
        self.assertEqual(payload["_meta"]["sources"][2]["path"], "resources/clone_atari_st/emutos/bdos/pghdr.h")
        self.assertEqual(payload["_meta"]["sources"][3]["path"], "resources/clone_atari_st/emutos/bdos/kpgmld.c")

        sequence = payload["containers"]["prg_executable"]["top_level_sequence"]
        self.assertEqual(sequence[3]["type"], "SYMBOL_TABLE")
        self.assertTrue(sequence[3]["optional"])
        self.assertEqual(sequence[4]["type"], "RELOCATION_STREAM")
        self.assertTrue(sequence[4]["optional"])
        self.assertEqual(payload["relocation_kinds"]["PRG_RELOC_32"]["record_type"], "RELOCATION_STREAM")
        self.assertEqual(payload["record_types"]["PRG_HEADER"]["fields"][5]["name"], "symbol_table_type")
        self.assertEqual(payload["record_types"]["PRG_HEADER"]["fields"][6]["name"], "program_flags")
        self.assertEqual(payload["record_types"]["PRG_HEADER"]["fields"][7]["name"], "relocation_flag")
        self.assertTrue(payload["constraints"]["relocation_flag_is_informational_for_classic_prg"])
        self.assertTrue(payload["constraints"]["relocation_stream_may_terminate_at_eof_without_zero_byte"])
        self.assertTrue(payload["constraints"]["zero_only_trailing_padding_after_empty_relocation_stream_is_allowed"])

    def test_disk_kb_semantics(self) -> None:
        atari_disk = json.loads(ATARI_DISK_JSON.read_text(encoding="utf-8"))
        amiga_disk = json.loads(AMIGA_DISK_JSON.read_text(encoding="utf-8"))

        self.assertEqual(atari_disk["_meta"]["endianness"], "little")
        self.assertEqual(atari_disk["constraints"]["supported_fat_types"], ["FAT12"])
        self.assertEqual(atari_disk["constraints"]["root_directory_entry_bytes"], 32)
        self.assertEqual(atari_disk["record_types"]["BOOT_SECTOR"]["fields"][2]["name"], "bytes_per_sector")
        self.assertEqual(atari_disk["record_types"]["DIRECTORY_ENTRY"]["fields"][-2]["name"], "first_cluster")

        self.assertEqual(amiga_disk["_meta"]["endianness"], "big")
        self.assertEqual(amiga_disk["constraints"]["bytes_per_sector"], 512)
        self.assertEqual(amiga_disk["constraints"]["boot_block_sectors"], 2)
        self.assertEqual(amiga_disk["constraints"]["root_hash_table_offset"], 24)
        self.assertEqual(amiga_disk["constraints"]["sec_type_file"], 4294967293)

    def test_generated_outputs_match_checked_in_files(self) -> None:
        for name, committed_path in COMMITTED_FILES.items():
            with self.subTest(file=name):
                generated_path = self._outdir / name
                self.assertEqual(
                    generated_path.read_text(encoding="utf-8"),
                    committed_path.read_text(encoding="utf-8"),
                )

    def test_generated_runtime_json_contract(self) -> None:
        amiga_runtime = json.loads((self._outdir / "amiga_hunk_file_runtime.json").read_text(encoding="utf-8"))
        atari_runtime = json.loads((self._outdir / "atari_st_prg_file_runtime.json").read_text(encoding="utf-8"))
        atari_disk_runtime = json.loads((self._outdir / "atari_st_disk_file_runtime.json").read_text(encoding="utf-8"))
        amiga_disk_runtime = json.loads((self._outdir / "amiga_disk_file_runtime.json").read_text(encoding="utf-8"))

        self.assertEqual(amiga_runtime["meta"]["name"], "amiga_hunk_file")
        self.assertEqual(amiga_runtime["container_magic_wire_ids"], [999, 1011, 1018])
        self.assertEqual(amiga_runtime["meta"]["sources"][1]["provides"][0], "type_ids")

        self.assertEqual(atari_runtime["meta"]["name"], "atari_st_prg_file")
        self.assertEqual(atari_runtime["container_magic_wire_ids"], [])
        self.assertEqual(atari_runtime["meta"]["sources"][2]["path"], "resources/clone_atari_st/emutos/bdos/pghdr.h")

        self.assertEqual(atari_disk_runtime["meta"]["name"], "atari_st_disk_file")
        self.assertEqual(atari_disk_runtime["meta"]["endianness"], "little")
        self.assertEqual(atari_disk_runtime["meta"]["sources"][0]["section"], "~/text/gemdos/diskstruct")

        self.assertEqual(amiga_disk_runtime["meta"]["name"], "amiga_disk_file")
        self.assertEqual(amiga_disk_runtime["meta"]["endianness"], "big")
        self.assertEqual(amiga_disk_runtime["meta"]["sources"][0]["ref"], "amiga_disk/kb.py")

    def test_generated_runtime_sources_pass_style_checker(self) -> None:
        result = subprocess.run(
            [
                str(PYTHON),
                str(STYLE_CHECKER),
                str(self._outdir / "amiga_hunk_file_runtime.h"),
                str(self._outdir / "amiga_hunk_file_runtime.c"),
                str(self._outdir / "atari_st_prg_file_runtime.h"),
                str(self._outdir / "atari_st_prg_file_runtime.c"),
                str(self._outdir / "atari_st_disk_file_runtime.h"),
                str(self._outdir / "atari_st_disk_file_runtime.c"),
                str(self._outdir / "amiga_disk_file_runtime.h"),
                str(self._outdir / "amiga_disk_file_runtime.c"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_EXPLICIT_TESTS") == "1":
        return tests
    suite = unittest.TestSuite()
    skipped = {
        "test_generated_outputs_match_checked_in_files",
        "test_generated_runtime_sources_pass_style_checker",
    }

    def append_filtered(test):
        if isinstance(test, unittest.TestSuite):
          for item in test:
            append_filtered(item)
          return
        if getattr(test, "_testMethodName", "") in skipped:
          return
        suite.addTest(test)

    append_filtered(tests)
    return suite
