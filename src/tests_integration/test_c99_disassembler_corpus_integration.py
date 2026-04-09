from __future__ import annotations

import unittest

from src.tests.test_c99_disassembler_corpus import C99DisassemblerCorpusTests


class C99DisassemblerCorpusIntegrationTests(unittest.TestCase):
    def test_negative_indexed_displacements_render_signed(self) -> None:
        C99DisassemblerCorpusTests(methodName="test_negative_indexed_displacements_render_signed")\
            .test_negative_indexed_displacements_render_signed()

    def test_signed_displacement_families_render_signed(self) -> None:
        C99DisassemblerCorpusTests(methodName="test_signed_displacement_families_render_signed")\
            .test_signed_displacement_families_render_signed()

    def test_full_extension_word_displacements_render_signed(self) -> None:
        C99DisassemblerCorpusTests(methodName="test_full_extension_word_displacements_render_signed")\
            .test_full_extension_word_displacements_render_signed()

    def test_bulk_round_trip_corpus_by_cpu(self) -> None:
        C99DisassemblerCorpusTests(methodName="runTest")._bulk_round_trip_corpus_by_cpu()

    def test_pc_relative_indexed_representatives_round_trip(self) -> None:
        C99DisassemblerCorpusTests(methodName="runTest")._pc_relative_indexed_representatives_round_trip()

    def test_pc_relative_full_extension_representatives_round_trip(self) -> None:
        C99DisassemblerCorpusTests(methodName="runTest")._pc_relative_full_extension_representatives_round_trip()

    def test_move16_round_trip_representatives(self) -> None:
        C99DisassemblerCorpusTests(methodName="runTest")._move16_round_trip_representatives()

    def test_cache_control_round_trip_representatives(self) -> None:
        C99DisassemblerCorpusTests(methodName="runTest")._cache_control_round_trip_representatives()
