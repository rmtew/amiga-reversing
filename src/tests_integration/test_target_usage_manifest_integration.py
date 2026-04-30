from __future__ import annotations

import unittest
import json
from pathlib import Path

from src.scripts import target_usage_manifest

ROOT = Path(__file__).resolve().parents[2]
TARGET_USAGE_MANIFEST_PATH = ROOT / "corpus" / "target_usage_manifest.jsonl"
TARGET_USAGE_XREFS_PATH = ROOT / "corpus" / "target_usage_xrefs.jsonl"
TARGET_USAGE_SNIPPET_ROWS_PATH = ROOT / "corpus" / "target_usage_snippet_rows.jsonl"


class TargetUsageManifestIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows, cls.xrefs, cls.snippet_rows = target_usage_manifest.build_usage_outputs()

    @staticmethod
    def _jsonl_text(rows: list[dict[str, object]]) -> str:
        return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)

    def test_checked_in_target_usage_manifest_is_stable(self) -> None:
        before = TARGET_USAGE_MANIFEST_PATH.read_text(encoding="utf-8")
        after = self._jsonl_text(self.rows)
        self.assertEqual(after, before)

    def test_checked_in_target_usage_xrefs_are_stable_and_consistent(self) -> None:
        before = TARGET_USAGE_XREFS_PATH.read_text(encoding="utf-8")
        after = self._jsonl_text(self.xrefs)
        manifest_ids = {str(row["id"]) for row in self.rows}
        xref_target_ids = {str(row["target_id"]) for row in self.xrefs}
        self.assertEqual(after, before)
        self.assertTrue(self.xrefs)
        self.assertLessEqual(xref_target_ids, manifest_ids)

    def test_checked_in_target_usage_snippet_rows_are_stable_and_consistent(self) -> None:
        before = TARGET_USAGE_SNIPPET_ROWS_PATH.read_text(encoding="utf-8")
        after = self._jsonl_text(self.snippet_rows)
        manifest_ids = {str(row["id"]) for row in self.rows}
        snippet_target_ids = {str(row["target_id"]) for row in self.snippet_rows}
        self.assertEqual(after, before)
        self.assertTrue(self.snippet_rows)
        self.assertLessEqual(snippet_target_ids, manifest_ids)

    def test_checked_in_target_usage_manifest_has_queryable_features(self) -> None:
        rows = target_usage_manifest.read_usage_manifest(TARGET_USAGE_MANIFEST_PATH)
        features = {item["feature"] for item in target_usage_manifest.feature_summary(rows)}
        self.assertIn("format:disk_image", features)
        self.assertIn("analysis:facts_v2", features)


if __name__ == "__main__":
    unittest.main()
