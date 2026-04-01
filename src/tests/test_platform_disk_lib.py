from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
