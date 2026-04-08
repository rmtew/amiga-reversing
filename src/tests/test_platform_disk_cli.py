from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.tests._build_helpers import require_built_tools
from src.tests.test_platform_amiga_disk import _make_ffs_adf, _make_non_dos_adf, _make_non_dos_bootable_adf
from src.tests.test_platform_atari_st_disk import _make_synthetic_st_disk_with_subdir

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
EXE = BUILD_DIR / "platform_disk_cli.exe"


class PlatformDiskCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_built_tools()

    def _run_cli(self, platform_name: str, filename: str, image: bytes) -> dict[str, object]:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            path = Path(tmp) / filename
            path.write_bytes(image)
            result = subprocess.run(
                [str(EXE), "inspect-disk", platform_name, str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

    def test_inspect_disk_amiga_json(self) -> None:
        actual = self._run_cli("amiga-disk", "disk.adf", _make_ffs_adf())
        self.assertEqual(actual["platform"], "amiga-disk")
        self.assertEqual(actual["format_kind"], "dos")
        self.assertEqual(actual["root_block"], 880)
        self.assertEqual(actual["entries"][0]["path"], "Workbench")
        self.assertEqual(actual["entries"][1]["path"], "HELLO")

    def test_inspect_disk_amiga_non_dos_json(self) -> None:
        actual = self._run_cli("amiga-disk", "disk.adf", _make_non_dos_adf())
        self.assertEqual(actual["platform"], "amiga-disk")
        self.assertEqual(actual["format_kind"], "non-dos-blank")
        self.assertEqual(actual["entry_count"], 0)

    def test_inspect_disk_amiga_non_dos_bootable_json(self) -> None:
        actual = self._run_cli("amiga-disk", "disk.adf", _make_non_dos_bootable_adf())
        self.assertEqual(actual["platform"], "amiga-disk")
        self.assertEqual(actual["format_kind"], "non-dos-bootable")
        self.assertEqual(actual["entry_count"], 0)

    def test_inspect_disk_atari_json(self) -> None:
        actual = self._run_cli("atari-st-disk", "disk.st", _make_synthetic_st_disk_with_subdir())
        self.assertEqual(actual["platform"], "atari-st-disk")
        self.assertEqual(actual["bytes_per_sector"], 512)
        self.assertEqual(actual["entries"][1]["path"], "HELLO.PRG")
        self.assertEqual(actual["entries"][3]["path"], "AUTO/BOOT.PRG")


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_HEAVY_UNIT_TESTS") == "1":
        return tests
    return unittest.TestSuite()
