from __future__ import annotations

import unittest

from src.tests._platform_backend_test_utils import PlatformBackendTestCaseMixin
from src.tests._platform_backend_test_utils import all_amiga_hunk_corpus_entries
from src.tests._platform_backend_test_utils import all_atari_st_corpus_entries
from src.tests._platform_backend_test_utils import find_corpus_file_entry
from src.tests._platform_backend_test_utils import reconstruct_corpus_file_bytes


class PlatformBackendIntegrationTests(PlatformBackendTestCaseMixin, unittest.TestCase):
    def test_amiga_hunk_backend_roundtrips_real_corpus_samples_exactly(self) -> None:
        samples = (
            (
                "3D Construction Kit II r2.01 (1992)(Domark)(Disk 1 of 2)[h Ministry][construction kit].zip",
                "3DMAKE",
            ),
            (
                "Conqueror (1990)(Rainbow Arts)(de-en)[cr QTX].zip",
                "game",
            ),
            (
                "Workbench v1.3.3 rev 34.34 (1990)(Commodore)(Disk 1 of 2)(Workbench)[m].zip",
                "c/Run",
            ),
            (
                "Workbench v1.3.3 rev 34.34 (1990)(Commodore)(Disk 1 of 2)(Workbench)[m].zip",
                "libs/version.library",
            ),
        )
        for display_name, in_image_path in samples:
            entry = find_corpus_file_entry(display_name, in_image_path)
            sample = reconstruct_corpus_file_bytes(entry)
            self.assertEqual(self.roundtrip_buffer("amiga-hunk", sample), sample, in_image_path)

    def test_amiga_hunk_backend_roundtrips_real_corpus_samples_semantically(self) -> None:
        samples = (
            (
                "3D Construction Kit II r2.01 (1992)(Domark)(Disk 1 of 2)[h Ministry][construction kit].zip",
                "3DMAKE",
            ),
            (
                "Conqueror (1990)(Rainbow Arts)(de-en)[cr QTX].zip",
                "game",
            ),
            (
                "Magicland Dizzy (1991)(Codemasters)[cr TRSI][t +2 LSD].zip",
                "MD",
            ),
            (
                "Workbench v1.3.3 rev 34.34 (1990)(Commodore)(Disk 1 of 2)(Workbench)[m].zip",
                "c/Run",
            ),
            (
                "Workbench v1.3.3 rev 34.34 (1990)(Commodore)(Disk 1 of 2)(Workbench)[m].zip",
                "libs/version.library",
            ),
            (
                "Workbench v1.3.3 rev 34.34 (1990)(Commodore)(Disk 1 of 2)(Workbench)[m].zip",
                "Utilities/Notepad",
            ),
            (
                "Workbench v1.3.3 rev 34.34 (1990)(Commodore)(Disk 1 of 2)(Workbench)[m].zip",
                "Prefs/Preferences",
            ),
        )
        for display_name, in_image_path in samples:
            entry = find_corpus_file_entry(display_name, in_image_path)
            sample = reconstruct_corpus_file_bytes(entry)
            expected = self.inspect_buffer("amiga-hunk", sample)
            actual = self.inspect_buffer("amiga-hunk", self.roundtrip_buffer("amiga-hunk", sample))
            self.assertEqual(actual, expected, in_image_path)

    def test_amiga_hunk_backend_roundtrips_all_real_corpus_semantically(self) -> None:
        for entry in all_amiga_hunk_corpus_entries():
            in_image_path = entry["origin"]["in_image_path"]
            sample = reconstruct_corpus_file_bytes(entry)
            expected = self.inspect_buffer("amiga-hunk", sample)
            actual = self.inspect_buffer("amiga-hunk", self.roundtrip_buffer("amiga-hunk", sample))
            self.assertEqual(actual, expected, in_image_path)

    def test_atari_st_backend_roundtrips_all_real_corpus_semantically(self) -> None:
        for entry in all_atari_st_corpus_entries():
            in_image_path = entry["origin"]["in_image_path"]
            sample = reconstruct_corpus_file_bytes(entry)
            expected = self.inspect_buffer("atari-st", sample)
            actual = self.inspect_buffer("atari-st", self.roundtrip_buffer("atari-st", sample))
            self.assertEqual(actual, expected, in_image_path)


if __name__ == "__main__":
    unittest.main()
