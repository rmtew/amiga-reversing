from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
import struct
from pathlib import Path

from src.scripts import build_platform_disk_manifest as disk_manifest_builder
from src.scripts import build_platform_file_manifest as file_manifest_builder
from src.tests._build_helpers import require_built_tools
from src.tests._platform_backend_test_utils import make_synthetic_atari_prg
from src.tests.test_platform_amiga_disk import _make_ffs_adf

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _u32(value: int) -> bytes:
    return struct.pack(">I", value)


def _write_file_manifest(disk_manifest_path: Path, file_manifest_path: Path) -> None:
    entries = file_manifest_builder.build_manifest(disk_manifest_path)
    file_manifest_builder.write_manifest(file_manifest_path, entries)


class PlatformFileManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_built_tools()

    def test_builds_in_situ_atari_file_manifest(self) -> None:
        prg = make_synthetic_atari_prg(b"\x4E\x75", b"\x12\x34", 6)
        image = (b"\x00" * 4096) + prg + (b"\x00" * 256)
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmpdir = Path(tmp)
            disk_path = tmpdir / "disk.st"
            disk_path.write_bytes(image)
            disk_relpath = disk_path.relative_to(ROOT).as_posix()
            disk_manifest_path = tmpdir / "platform_disk_manifest.jsonl"
            file_manifest_path = tmpdir / "platform_file_manifest.jsonl"
            disk_entry = {
                "id": f"atari-st-disk/{_sha256(image)[:12]}",
                "platform": "atari-st-disk",
                "sha256": _sha256(image),
                "size": len(image),
                "origin": {
                    "display_name": "synthetic.st",
                    "source_relpath": disk_relpath,
                    "container_relpath": None,
                    "member_name": None,
                },
                "expect": {
                    "summary_version": 1,
                    "status": "ok",
                    "entry_count": 1,
                    "inspect": {
                        "platform": "atari-st-disk",
                        "entry_count": 1,
                        "entries": [
                            {
                                "path": "HELLO.PRG",
                                "kind": 1,
                                "file_size": len(prg),
                                "first_cluster": 2,
                                "attributes": 32,
                                "is_executable_candidate": 1,
                                "extents": [{"image_offset": 4096, "byte_size": len(prg), "cluster_index": 2}],
                            },
                        ],
                    },
                },
            }
            disk_manifest_path.write_text(json.dumps(disk_entry) + "\n", encoding="utf-8")
            _write_file_manifest(disk_manifest_path, file_manifest_path)
            rows = [json.loads(line) for line in file_manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual([row["origin"]["in_image_path"] for row in rows], ["HELLO.PRG"])
            self.assertTrue(all(row["platform"] == "atari-st" for row in rows))
            self.assertTrue(all(row["expect"]["status"] == "ok" for row in rows))
            self.assertEqual(rows[0]["expect"]["inspect"]["file_kind"], "executable")

    def test_keeps_amiga_parse_failures_in_manifest(self) -> None:
        image = _make_ffs_adf()
        bad_bytes = _u32(1011) + b"\x00\x00\x00\x00"
        image = image[: 910 * 512] + bad_bytes + image[910 * 512 + len(bad_bytes) :]
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmpdir = Path(tmp)
            disk_path = tmpdir / "disk.adf"
            disk_path.write_bytes(image)
            disk_relpath = disk_path.relative_to(ROOT).as_posix()
            disk_manifest_path = tmpdir / "platform_disk_manifest.jsonl"
            file_manifest_path = tmpdir / "platform_file_manifest.jsonl"
            disk_entry = {
                "id": f"amiga-disk/{_sha256(image)[:12]}",
                "platform": "amiga-disk",
                "sha256": _sha256(image),
                "size": len(image),
                "origin": {
                    "display_name": "synthetic.adf",
                    "source_relpath": disk_relpath,
                    "container_relpath": None,
                    "member_name": None,
                },
                "expect": {
                    "summary_version": 1,
                    "status": "ok",
                    "entry_count": 1,
                    "inspect": {
                        "platform": "amiga-disk",
                        "entry_count": 1,
                        "entries": [
                            {
                                "path": "HELLO",
                                "kind": 1,
                                "byte_size": len(bad_bytes),
                                "header_block": 900,
                                "extents": [{"block_index": 910, "image_offset": 910 * 512, "byte_size": len(bad_bytes)}],
                            }
                        ],
                    },
                },
            }
            disk_manifest_path.write_text(json.dumps(disk_entry) + "\n", encoding="utf-8")
            _write_file_manifest(disk_manifest_path, file_manifest_path)
            rows = [json.loads(line) for line in file_manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["platform"], "amiga-hunk")
            self.assertEqual(rows[0]["expect"]["status"], "error")
            self.assertTrue(rows[0]["expect"]["error"])

    def test_skips_non_hunk_amiga_files_from_hunk_manifest(self) -> None:
        image = _make_ffs_adf()
        data_bytes = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        image = image[: 910 * 512] + data_bytes + image[910 * 512 + len(data_bytes) :]
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmpdir = Path(tmp)
            disk_path = tmpdir / "disk.adf"
            disk_path.write_bytes(image)
            disk_relpath = disk_path.relative_to(ROOT).as_posix()
            disk_manifest_path = tmpdir / "platform_disk_manifest.jsonl"
            file_manifest_path = tmpdir / "platform_file_manifest.jsonl"
            disk_entry = {
                "id": f"amiga-disk/{_sha256(image)[:12]}",
                "platform": "amiga-disk",
                "sha256": _sha256(image),
                "size": len(image),
                "origin": {
                    "display_name": "synthetic.adf",
                    "source_relpath": disk_relpath,
                    "container_relpath": None,
                    "member_name": None,
                },
                "expect": {
                    "summary_version": 1,
                    "status": "ok",
                    "entry_count": 1,
                    "inspect": {
                        "platform": "amiga-disk",
                        "entry_count": 1,
                        "entries": [
                            {
                                "path": "DATAFILE",
                                "kind": 1,
                                "byte_size": len(data_bytes),
                                "header_block": 900,
                                "extents": [{"block_index": 910, "image_offset": 910 * 512, "byte_size": len(data_bytes)}],
                            }
                        ],
                    },
                },
            }
            disk_manifest_path.write_text(json.dumps(disk_entry) + "\n", encoding="utf-8")
            _write_file_manifest(disk_manifest_path, file_manifest_path)
            rows = [json.loads(line) for line in file_manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(rows, [])

    def test_classifies_amiga_iff_files(self) -> None:
        image = _make_ffs_adf()
        iff_bytes = b"FORM" + _u32(8) + b"ILBM" + b"\x00" * 8
        image = image[: 910 * 512] + iff_bytes + image[910 * 512 + len(iff_bytes) :]
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmpdir = Path(tmp)
            disk_path = tmpdir / "disk.adf"
            disk_path.write_bytes(image)
            disk_relpath = disk_path.relative_to(ROOT).as_posix()
            disk_manifest_path = tmpdir / "platform_disk_manifest.jsonl"
            file_manifest_path = tmpdir / "platform_file_manifest.jsonl"
            disk_entry = {
                "id": f"amiga-disk/{_sha256(image)[:12]}",
                "platform": "amiga-disk",
                "sha256": _sha256(image),
                "size": len(image),
                "origin": {
                    "display_name": "synthetic.adf",
                    "source_relpath": disk_relpath,
                    "container_relpath": None,
                    "member_name": None,
                },
                "expect": {
                    "summary_version": 1,
                    "status": "ok",
                    "entry_count": 1,
                    "inspect": {
                        "platform": "amiga-disk",
                        "entry_count": 1,
                        "entries": [
                            {
                                "path": "PIC.IFF",
                                "kind": 1,
                                "byte_size": len(iff_bytes),
                                "header_block": 900,
                                "extents": [{"block_index": 910, "image_offset": 910 * 512, "byte_size": len(iff_bytes)}],
                            }
                        ],
                    },
                },
            }
            disk_manifest_path.write_text(json.dumps(disk_entry) + "\n", encoding="utf-8")
            _write_file_manifest(disk_manifest_path, file_manifest_path)
            rows = [json.loads(line) for line in file_manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["platform"], "amiga-iff")
            self.assertEqual(rows[0]["expect"]["inspect"]["form_type"], "ILBM")

    def test_classifies_amiga_text_files(self) -> None:
        image = _make_ffs_adf()
        text_bytes = b"echo hello\nlist libs:\n"
        image = image[: 910 * 512] + text_bytes + image[910 * 512 + len(text_bytes) :]
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmpdir = Path(tmp)
            disk_path = tmpdir / "disk.adf"
            disk_path.write_bytes(image)
            disk_relpath = disk_path.relative_to(ROOT).as_posix()
            disk_manifest_path = tmpdir / "platform_disk_manifest.jsonl"
            file_manifest_path = tmpdir / "platform_file_manifest.jsonl"
            disk_entry = {
                "id": f"amiga-disk/{_sha256(image)[:12]}",
                "platform": "amiga-disk",
                "sha256": _sha256(image),
                "size": len(image),
                "origin": {
                    "display_name": "synthetic.adf",
                    "source_relpath": disk_relpath,
                    "container_relpath": None,
                    "member_name": None,
                },
                "expect": {
                    "summary_version": 1,
                    "status": "ok",
                    "entry_count": 1,
                    "inspect": {
                        "platform": "amiga-disk",
                        "entry_count": 1,
                        "entries": [
                            {
                                "path": "SCRIPT",
                                "kind": 1,
                                "byte_size": len(text_bytes),
                                "header_block": 900,
                                "extents": [{"block_index": 910, "image_offset": 910 * 512, "byte_size": len(text_bytes)}],
                            }
                        ],
                    },
                },
            }
            disk_manifest_path.write_text(json.dumps(disk_entry) + "\n", encoding="utf-8")
            _write_file_manifest(disk_manifest_path, file_manifest_path)
            rows = [json.loads(line) for line in file_manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["platform"], "amiga-text")
            self.assertEqual(rows[0]["expect"]["inspect"]["line_count"], 3)

    def test_reports_bad_extents_before_parser_error(self) -> None:
        prg = make_synthetic_atari_prg(b"\x4E\x75", b"\x12\x34", 6)
        image = (b"\x00" * 1024) + prg
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            tmpdir = Path(tmp)
            disk_path = tmpdir / "disk.st"
            disk_path.write_bytes(image)
            disk_relpath = disk_path.relative_to(ROOT).as_posix()
            disk_manifest_path = tmpdir / "platform_disk_manifest.jsonl"
            file_manifest_path = tmpdir / "platform_file_manifest.jsonl"
            disk_entry = {
                "id": f"atari-st-disk/{_sha256(image)[:12]}",
                "platform": "atari-st-disk",
                "sha256": _sha256(image),
                "size": len(image),
                "origin": {
                    "display_name": "synthetic.st",
                    "source_relpath": disk_relpath,
                    "container_relpath": None,
                    "member_name": None,
                },
                "expect": {
                    "summary_version": 1,
                    "status": "ok",
                    "entry_count": 1,
                    "inspect": {
                        "platform": "atari-st-disk",
                        "entry_count": 1,
                        "entries": [
                            {
                                "path": "BROKEN.PRG",
                                "kind": 1,
                                "file_size": len(prg),
                                "first_cluster": 2,
                                "attributes": 32,
                                "is_executable_candidate": 1,
                                "extents": [{"image_offset": len(image) - 4, "byte_size": len(prg), "cluster_index": 2}],
                            },
                        ],
                    },
                },
            }
            disk_manifest_path.write_text(json.dumps(disk_entry) + "\n", encoding="utf-8")
            _write_file_manifest(disk_manifest_path, file_manifest_path)
            rows = [json.loads(line) for line in file_manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["expect"]["status"], "error")
            self.assertEqual(rows[0]["expect"]["error"], "In-image file extent lies outside disk image")

if __name__ == "__main__":
    unittest.main()
