from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.tests._build_helpers import prepare_test_exe
from src.tests._build_helpers import require_built_tools
from src.tests.test_platform_amiga_disk import BLOCK_SIZE
from src.tests.test_platform_amiga_disk import ROOT_BLOCK
from src.tests.test_platform_amiga_disk import TOTAL_BLOCKS
from src.tests.test_platform_amiga_disk import _make_boot_block
from src.tests.test_platform_amiga_disk import _make_ffs_adf
from src.tests.test_platform_amiga_disk import _make_file_header
from src.tests.test_platform_amiga_disk import _make_non_dos_adf
from src.tests.test_platform_amiga_disk import _make_non_dos_bootable_adf
from src.tests.test_platform_amiga_disk import _make_root_block
from src.tests.test_platform_amiga_disk import _put_u32
from src.tests.test_platform_atari_st_disk import _make_synthetic_st_disk_with_subdir

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
EXE = BUILD_DIR / "platform_disk_cli.exe"
ASM_EXE = BUILD_DIR / "m68k_assembler_app.exe"


def _make_ffs_adf_with_single_file(name: str, payload: bytes) -> bytes:
    blocks = [bytearray(BLOCK_SIZE) for _ in range(TOTAL_BLOCKS)]
    blocks[0][:] = _make_boot_block(ROOT_BLOCK, 1)[:BLOCK_SIZE]
    blocks[1][:] = _make_boot_block(ROOT_BLOCK, 1)[BLOCK_SIZE:]
    blocks[ROOT_BLOCK][:] = _make_root_block("Workbench", [900])
    file_header = _make_file_header(900, name, len(payload))
    _put_u32(file_header, 8, 1)
    _put_u32(file_header, 24 + 71 * 4, 910)
    blocks[900][:] = file_header
    blocks[910][: len(payload)] = payload
    return b"".join(bytes(block) for block in blocks)


def _make_hunk_executable(code: bytes) -> bytes:
    assert len(code) % 4 == 0
    words = [1011, 0, 1, 0, 0, len(code) // 4, 1001, len(code) // 4]
    return struct.pack(">" + "I" * len(words), *words) + code + struct.pack(">I", 1010)


class PlatformDiskCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_built_tools()
        cls.disk_exe = prepare_test_exe(EXE)

    def _run_cli(self, platform_name: str, filename: str, image: bytes) -> dict[str, object]:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / filename
            path.write_bytes(image)
            result = subprocess.run(
                [str(self.disk_exe), "inspect-disk", platform_name, str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

    def _extract_cli(self, platform_name: str, filename: str, image: bytes, entry_path: str) -> bytes:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / filename
            path.write_bytes(image)
            result = subprocess.run(
                [str(self.disk_exe), "extract-entry", platform_name, str(path), entry_path],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
            return result.stdout

    def _assemble_stage(self, lines: list[str]) -> bytes:
        result = bytearray()
        for line in lines:
            assembled = subprocess.run(
                [str(prepare_test_exe(ASM_EXE)), "assemble-line", line],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(assembled.returncode, 0, assembled.stderr)
            result.extend(bytes.fromhex(assembled.stdout.strip()))
        return bytes(result)

    def _make_non_dos_bootable_adf_with_stage(self) -> bytes:
        image = bytearray(_make_non_dos_bootable_adf())
        stage = self._assemble_stage(
            [
                "move.l #262144,$00dff020.l",
                "move.w #17545,$00dff07e.l",
                "move.w #39686,$00dff024.l",
                "move.w #32767,$00dff096.l",
                "rts",
            ]
        )
        image[1024 : 1024 + len(stage)] = stage
        return bytes(image)

    def test_inspect_disk_amiga_json(self) -> None:
        actual = self._run_cli("amiga-disk", "disk.adf", _make_ffs_adf())
        self.assertEqual(actual["platform"], "amiga-disk")
        self.assertEqual(actual["format_kind"], "dos")
        self.assertEqual(actual["disk_info"]["variant"], "DD")
        self.assertEqual(actual["disk_info"]["total_sectors"], 1760)
        self.assertEqual(actual["disk_info"]["sectors_per_track"], 11)
        self.assertEqual(actual["root_block"], 880)
        self.assertEqual(actual["boot_block"]["magic_ascii"], "DOS")
        self.assertEqual(actual["boot_block"]["magic_bytes"], [68, 79, 83])
        self.assertEqual(actual["boot_block"]["is_dos"], 1)
        self.assertEqual(actual["boot_block"]["flags_byte"], 1)
        self.assertEqual(actual["boot_block"]["fs_type"], "1")
        self.assertEqual(actual["boot_block"]["fs_description"], "DOS\\1 - Fast File System")
        self.assertEqual(actual["boot_block"]["rootblock_ptr"], 880)
        self.assertEqual(actual["boot_block"]["bootcode_size"], 1012)
        boot_import = actual["boot_block"]["import_target"]
        self.assertEqual(boot_import["target_type"], "bootblock")
        self.assertEqual(boot_import["entry_path"], "bootblock")
        self.assertEqual(boot_import["local_target_id"], "amiga_raw_bootblock")
        self.assertEqual(boot_import["source"]["kind"], "asset_data")
        self.assertEqual(boot_import["source"]["byte_offset"], 0)
        self.assertEqual(boot_import["source"]["byte_size"], 1024)
        self.assertEqual(boot_import["source"]["load_address"], 0x70000)
        self.assertEqual(boot_import["source"]["role"], "bootblock")
        self.assertEqual(boot_import["target_metadata"]["target_type"], "bootblock")
        self.assertEqual(boot_import["target_metadata"]["bootblock"]["entrypoint"], 0x7000C)
        self.assertEqual(boot_import["target_metadata"]["bootblock"]["bootcode_has_code"], False)
        self.assertEqual(boot_import["target_metadata"]["entry_register_seeds"], [])
        self.assertEqual(actual["root"]["block_num"], 880)
        self.assertEqual(actual["root"]["hash_table"][:3], [900, 901, 0])
        self.assertEqual(actual["root"]["volume_name"], "Workbench")
        self.assertRegex(actual["root"]["root_date"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertEqual(actual["root"]["bm_pages"], [])
        self.assertEqual(
            actual["bitmap"],
            {
                "allocated_blocks": 2,
                "checksum_valid": 1,
                "free_blocks": 0,
                "percent_used": 0.1,
                "total_blocks": 1760,
            },
        )
        self.assertEqual(
            actual["block_usage"]["summary"],
            {
                "allocated_orphan": 0,
                "bitmap": 0,
                "boot": 2,
                "data": 2,
                "dir_header": 1,
                "extension": 0,
                "file_header": 2,
                "free": 0,
                "root": 1,
                "unknown": 1752,
            },
        )
        self.assertEqual(actual["block_usage"]["orphan_blocks"], [])
        self.assertEqual(actual["entries"][0]["path"], "Workbench")
        self.assertEqual(actual["entries"][0]["kind_name"], "volume")
        self.assertEqual(actual["entries"][1]["path"], "HELLO")
        self.assertEqual(actual["entries"][1]["name"], "HELLO")
        self.assertEqual(actual["entries"][1]["kind_name"], "file")
        self.assertEqual(actual["entries"][1]["byte_size"], 6)
        self.assertRegex(actual["entries"][1]["date"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertRegex(actual["entries"][1]["protection"], r"^[h-][s-][p-][a-][r-][w-][e-][d-]$")
        self.assertEqual(actual["entries"][1]["data_blocks"], [910])
        self.assertEqual(actual["entries"][1]["content"]["kind"], "unknown")
        self.assertEqual(actual["entries"][1]["content"]["size"], 6)
        self.assertEqual(actual["entries"][1]["content"]["sha256"], hashlib.sha256(b"ABCDEF").hexdigest())
        self.assertEqual(actual["entries"][2]["path"], "C")
        self.assertEqual(actual["entries"][2]["kind_name"], "directory")
        self.assertEqual(actual["entries"][3]["path"], "C/RUNME")
        self.assertEqual(actual["entries"][3]["data_blocks"], [911])

    def test_inspect_disk_amiga_classifies_iff_content(self) -> None:
        payload = b"FORM" + (4).to_bytes(4, byteorder="big") + b"ILBM"
        actual = self._run_cli("amiga-disk", "disk.adf", _make_ffs_adf_with_single_file("IMAGE", payload))
        content = actual["entries"][1]["content"]
        self.assertEqual(content["kind"], "iff_container")
        self.assertEqual(content["size"], len(payload))
        self.assertEqual(content["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(content["group_id"], "FORM")
        self.assertEqual(content["form_id"], "ILBM")

    def test_inspect_disk_amiga_classifies_malformed_hunk_content(self) -> None:
        payload = b"\x00\x00\x03\xf3BROKEN"
        actual = self._run_cli("amiga-disk", "disk.adf", _make_ffs_adf_with_single_file("BADHUNK", payload))
        content = actual["entries"][1]["content"]
        self.assertEqual(content["kind"], "amiga_hunk_executable")
        self.assertEqual(content["size"], len(payload))
        self.assertEqual(content["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(content["is_executable"])
        self.assertIsNone(content["hunk_count"])
        self.assertIsNone(content["target_type"])
        self.assertIsNone(content["resident"])
        self.assertIsNone(content["library"])
        self.assertIsNone(content["import_target"])

    def test_inspect_disk_amiga_emits_hunk_import_target_metadata(self) -> None:
        payload = _make_hunk_executable(b"\x4e\x75\x4e\x75")
        actual = self._run_cli("amiga-disk", "disk.adf", _make_ffs_adf_with_single_file("RUN", payload))
        content = actual["entries"][1]["content"]
        self.assertEqual(content["kind"], "amiga_hunk_executable")
        self.assertTrue(content["is_executable"])
        self.assertEqual(content["target_type"], "program")
        self.assertEqual(content["import_target"]["target_type"], "program")
        self.assertEqual(content["import_target"]["entry_path"], "RUN")
        self.assertEqual(content["import_target"]["local_target_id"], "amiga_hunk_run_ad173e04")
        metadata = content["import_target"]["target_metadata"]
        self.assertEqual(metadata["target_type"], "program")
        self.assertEqual(metadata["entry_register_seeds"], [])
        self.assertIsNone(metadata["resident"])
        self.assertIsNone(metadata["library"])

    def test_extract_disk_amiga_entry(self) -> None:
        self.assertEqual(
            self._extract_cli("amiga-disk", "disk.adf", _make_ffs_adf(), "HELLO"),
            b"ABCDEF",
        )

    def test_inspect_disk_amiga_non_dos_json(self) -> None:
        actual = self._run_cli("amiga-disk", "disk.adf", _make_non_dos_adf())
        self.assertEqual(actual["platform"], "amiga-disk")
        self.assertEqual(actual["format_kind"], "non-dos-blank")
        self.assertEqual(actual["boot_block"]["magic_bytes"], [0, 0, 0])
        self.assertEqual(actual["boot_block"]["is_dos"], 0)
        self.assertEqual(actual["boot_block"]["bootcode_has_code"], 0)
        self.assertIsNone(actual["root"])
        self.assertEqual(actual["entry_count"], 0)
        self.assertEqual(actual["track_analysis"]["non_empty_tracks"], 0)
        self.assertEqual(actual["trackloader_analysis"]["candidate_code_tracks"], [])
        self.assertEqual(actual["bootloader_analysis"]["stages"], [])

    def test_inspect_disk_amiga_non_dos_bootable_json(self) -> None:
        actual = self._run_cli("amiga-disk", "disk.adf", _make_non_dos_bootable_adf())
        self.assertEqual(actual["platform"], "amiga-disk")
        self.assertEqual(actual["format_kind"], "non-dos-bootable")
        self.assertEqual(actual["boot_block"]["is_dos"], 0)
        self.assertEqual(actual["boot_block"]["bootcode_has_code"], 1)
        self.assertIsNone(actual["root"])
        self.assertEqual(actual["entry_count"], 0)
        self.assertEqual(actual["track_analysis"]["non_empty_tracks"], 1)
        self.assertEqual(actual["trackloader_analysis"]["boot_ascii_strings"], ["BOOTCODE"])
        stages = {stage["name"]: stage for stage in actual["bootloader_analysis"]["stages"]}
        self.assertIn("boot", stages)
        self.assertNotIn("stage_1", stages)

    def test_inspect_disk_amiga_dos_longword_fill_bootblock_is_asset_data(self) -> None:
        image = bytearray(BLOCK_SIZE * TOTAL_BLOCKS)
        image[0:3] = b"DOS"
        for value in range(0x80, 0x100):
            offset = BLOCK_SIZE + (value - 0x80) * 4
            image[offset : offset + 4] = b"DOS" + bytes([value])

        actual = self._run_cli("amiga-disk", "disk.adf", bytes(image))

        self.assertEqual(actual["boot_block"]["is_dos"], 1)
        self.assertEqual(actual["boot_block"]["bootcode_has_code"], 0)
        boot_import = actual["boot_block"]["import_target"]
        self.assertEqual(boot_import["source"]["kind"], "asset_data")
        self.assertEqual(boot_import["target_metadata"]["bootblock"]["bootcode_has_code"], False)
        self.assertEqual(boot_import["target_metadata"]["entry_register_seeds"], [])
        self.assertEqual(actual["bootloader_analysis"]["stages"], [])

    def test_inspect_disk_amiga_synthetic_stage_read_setup_json(self) -> None:
        actual = self._run_cli("amiga-disk", "disk.adf", self._make_non_dos_bootable_adf_with_stage())
        stage = next(stage for stage in actual["bootloader_analysis"]["stages"] if stage["name"] == "stage_1")
        symbols = {access["symbol"] for access in stage["hardware_accesses"]}
        self.assertIn("dskpt", symbols)
        self.assertIn("dsklen", symbols)
        self.assertIn("dsksync", symbols)
        self.assertIn("dmacon", symbols)
        self.assertEqual(stage["read_setups"][0]["buffer_addr"], 0x40000)
        self.assertEqual(stage["read_setups"][0]["sync_word"], 0x4489)
        self.assertEqual(stage["read_setups"][0]["dsklen_value"], 0x9B06)
        self.assertEqual(stage["read_setups"][0]["dsklen_dma_byte_length"], 13836)
        self.assertTrue(stage["read_setups"][0]["dsklen_dma_enabled"])
        self.assertFalse(stage["read_setups"][0]["dsklen_write"])
        self.assertIn(0x7FFF, stage["read_setups"][0]["dmacon_values"])

    def test_inspect_disk_amiga_ice_bootloader_json(self) -> None:
        fixture = ROOT / "bin" / "Ice (1991-06-28)(The Silents).adf"
        if not fixture.exists():
            self.skipTest("Ice ADF fixture is not present")
        result = subprocess.run(
            [str(self.disk_exe), "inspect-disk", "amiga-disk", str(fixture)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(result.stdout)
        self.assertEqual(actual["disk_info"]["variant"], "DD")
        self.assertGreater(actual["track_analysis"]["non_empty_tracks"], 0)
        self.assertIn(0, actual["trackloader_analysis"]["candidate_code_tracks"])
        stage = next(stage for stage in actual["bootloader_analysis"]["stages"] if stage["name"] == "stage_1")
        self.assertEqual(stage["disk_reads"][0]["disk_offset"], 1024)
        self.assertEqual(stage["disk_reads"][0]["byte_length"], 21504)
        self.assertGreater(stage["reachable_instruction_count"], 100)
        symbols = {access["symbol"] for access in stage["hardware_accesses"]}
        self.assertIn("dskpt", symbols)
        self.assertIn("dsklen", symbols)
        self.assertIn("dsksync", symbols)
        self.assertIn("ciaprb", symbols)
        self.assertIn("dmacon", symbols)
        self.assertIn("intreq", symbols)
        self.assertEqual(stage["read_setups"][0]["buffer_addr"], 0x40000)
        self.assertEqual(stage["read_setups"][0]["dma_byte_length"], 21504)
        self.assertEqual(stage["read_setups"][0]["sync_word"], 0x4489)
        self.assertEqual(stage["read_setups"][0]["dsklen_value"], 0x9B06)
        self.assertEqual(stage["read_setups"][0]["dsklen_dma_byte_length"], 13836)
        self.assertTrue(stage["read_setups"][0]["dsklen_dma_enabled"])
        self.assertFalse(stage["read_setups"][0]["dsklen_write"])
        self.assertEqual(stage["read_setups"][0]["drive"], 0)
        self.assertEqual(stage["read_setups"][0]["cylinder"], 0)
        self.assertEqual(stage["read_setups"][0]["head"], 0)
        self.assertEqual(stage["read_setups"][0]["track"], 0)
        self.assertIn(0x6800, stage["read_setups"][0]["adkcon_values"])
        self.assertIn(0x7FFF, stage["read_setups"][0]["dmacon_values"])
        region = stage["decode_regions"][0]
        self.assertEqual(region["input_source_kind"], "custom_track_dma_buffer")
        self.assertEqual(region["input_required_source_kind"], "raw_custom_track_bytes")
        self.assertEqual(region["input_required_byte_length"], 13836)
        self.assertEqual(region["input_source_candidate_spans"][0]["start_track"], 0)
        self.assertEqual(region["input_source_candidate_spans"][0]["end_track"], 2)
        self.assertEqual(region["input_source_candidate_spans"][0]["start_byte_offset"], 2682)
        self.assertEqual(region["import_target"]["target_type"], "bootloader_raw_span")
        self.assertEqual(region["import_target"]["entry_path"], "bootloader/stage_1/raw_span_0")
        self.assertEqual(region["import_target"]["local_target_id"], "amiga_raw_bootloader_stage_1_raw_span_0")
        self.assertEqual(region["import_target"]["source"]["byte_offset"], 2682)
        self.assertEqual(region["import_target"]["source"]["byte_size"], 13836)
        self.assertEqual(actual["bootloader_analysis"]["transfers"][0]["transfer_kind"], "disk_read")
        self.assertEqual(actual["bootloader_analysis"]["transfers"][0]["disk_offset"], 1024)

    def test_inspect_disk_atari_json(self) -> None:
        actual = self._run_cli("atari-st-disk", "disk.st", _make_synthetic_st_disk_with_subdir())
        self.assertEqual(actual["platform"], "atari-st-disk")
        self.assertEqual(actual["bytes_per_sector"], 512)
        self.assertEqual(actual["entries"][1]["path"], "HELLO.PRG")
        self.assertEqual(actual["entries"][3]["path"], "AUTO/BOOT.PRG")

    def test_extract_disk_atari_entry(self) -> None:
        self.assertEqual(
            self._extract_cli("atari-st-disk", "disk.st", _make_synthetic_st_disk_with_subdir(), "AUTO/BOOT.PRG"),
            b"\x60\x1A\x00\x00",
        )


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_HEAVY_UNIT_TESTS") == "1":
        return tests
    return unittest.TestSuite()
