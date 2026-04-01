from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.scripts import build_platform_disk_manifest as disk_manifest_builder
from src.scripts import build_platform_file_manifest as file_manifest_builder

ROOT = Path(__file__).resolve().parents[2]
DISK_MANIFEST_PATH = ROOT / "corpus" / "platform_disk_manifest.jsonl"
FILE_MANIFEST_PATH = ROOT / "corpus" / "platform_file_manifest.jsonl"


class PlatformManifestIntegrationTests(unittest.TestCase):
    def test_checked_in_disk_manifest_is_stable(self) -> None:
        before = DISK_MANIFEST_PATH.read_text(encoding="utf-8")
        disk_manifest_builder.write_manifest(DISK_MANIFEST_PATH, disk_manifest_builder.build_manifest())
        after = DISK_MANIFEST_PATH.read_text(encoding="utf-8")
        self.assertEqual(after, before)

    def test_checked_in_disk_manifest_has_unique_disk_hashes(self) -> None:
        rows = [json.loads(line) for line in DISK_MANIFEST_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        hashes = [row["sha256"] for row in rows]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_checked_in_file_manifest_is_stable(self) -> None:
        before = FILE_MANIFEST_PATH.read_text(encoding="utf-8")
        file_manifest_builder.write_manifest(FILE_MANIFEST_PATH, file_manifest_builder.build_manifest(DISK_MANIFEST_PATH))
        after = FILE_MANIFEST_PATH.read_text(encoding="utf-8")
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
