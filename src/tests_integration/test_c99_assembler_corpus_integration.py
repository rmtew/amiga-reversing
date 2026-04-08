from __future__ import annotations

import unittest

from src.tests.test_c99_assembler_corpus import C99AssemblerCorpusTests


class C99AssemblerCorpusIntegrationTests(unittest.TestCase):
    def test_generated_oracle_binary_matches_current_generated_cases(self) -> None:
        C99AssemblerCorpusTests(methodName="runTest")._generated_oracle_binary_matches_current_generated_cases()

    def test_native_68000_manifest_matches_oracle_binary(self) -> None:
        C99AssemblerCorpusTests(methodName="runTest")._native_68000_manifest_matches_oracle_binary()

    def test_native_68020_manifest_verifies_in_68020_mode(self) -> None:
        C99AssemblerCorpusTests(methodName="runTest")._native_68020_manifest_verifies_in_68020_mode()

    def test_native_68040_manifest_verifies_in_68040_mode(self) -> None:
        C99AssemblerCorpusTests(methodName="runTest")._native_68040_manifest_verifies_in_68040_mode()

    def test_native_68060_manifest_verifies_in_68060_mode(self) -> None:
        C99AssemblerCorpusTests(methodName="runTest")._native_68060_manifest_verifies_in_68060_mode()

    def test_cpu_corpus_stratification(self) -> None:
        C99AssemblerCorpusTests(methodName="runTest")._cpu_corpus_stratification()

    def test_native_manifest_cpu_gating(self) -> None:
        C99AssemblerCorpusTests(methodName="runTest")._native_manifest_cpu_gating()
