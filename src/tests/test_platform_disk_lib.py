from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.tests._platform_disk_test_utils import PlatformDiskTestCaseMixin
from src.tests.test_platform_amiga_disk import _make_ffs_adf
from src.tests.test_platform_atari_st_disk import _make_synthetic_st_disk_with_subdir


class PlatformDiskLibTests(PlatformDiskTestCaseMixin, unittest.TestCase):

    def test_inspects_amiga_disk_buffer(self) -> None:
        actual = self.inspect_disk_buffer("amiga-disk", _make_ffs_adf())
        self.assertEqual(actual["platform"], "amiga-disk")
        self.assertEqual(actual["format_kind"], "dos")
        self.assertEqual(actual["entry_count"], 4)

    def test_inspects_atari_st_disk_buffer(self) -> None:
        actual = self.inspect_disk_buffer("atari-st-disk", _make_synthetic_st_disk_with_subdir())
        self.assertEqual(actual["platform"], "atari-st-disk")
        self.assertEqual(actual["entry_count"], 4)
        self.assertEqual(actual["entries"][1]["path"], "HELLO.PRG")

    def test_alloc_path_api_inspects_amiga_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.adf"
            path.write_bytes(_make_ffs_adf())

            actual = self.inspect_disk_path_alloc("amiga-disk", path)

        self.assertEqual(actual["platform"], "amiga-disk")
        self.assertEqual(actual["format_kind"], "dos")
        self.assertEqual(actual["entry_count"], 4)

    def test_alloc_path_api_extracts_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.adf"
            path.write_bytes(_make_ffs_adf())

            actual = self.extract_disk_entry_path_alloc("amiga-disk", path, "HELLO")

        self.assertEqual(len(actual), 6)

    def test_alloc_path_api_reports_extract_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.adf"
            path.write_bytes(_make_ffs_adf())

            error = self.extract_disk_entry_path_alloc_error("amiga-disk", path, "MISSING")

        self.assertTrue(error)


if __name__ == "__main__":
    unittest.main()
