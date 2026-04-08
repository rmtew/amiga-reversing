from __future__ import annotations

import os
import unittest

from src.tests.test_m68k_simulator_oracle import M68kSimulatorOracleTests


class M68kSimulatorOracleIntegrationTests(unittest.TestCase):
    def test_concrete_exception_entry_matches_machine68k(self) -> None:
        M68kSimulatorOracleTests(methodName="runTest")._concrete_exception_entry_matches_machine68k()

    def test_concrete_rte_restore_matches_machine68k(self) -> None:
        M68kSimulatorOracleTests(methodName="runTest")._concrete_rte_restore_matches_machine68k()

    def test_bulk_oracle_manifest(self) -> None:
        oracle = M68kSimulatorOracleTests(methodName="runTest")
        family_filter = os.environ.get("M68K_ORACLE_FAMILY", "").strip().lower()
        case_filter = os.environ.get("M68K_ORACLE_CASE", "").strip().lower()
        cases = oracle._oracle_cases()
        if family_filter:
            cases = [case for case in cases if case.family.lower() == family_filter]
        if case_filter:
            cases = [case for case in cases if case.case_id.lower() == case_filter]
        if not cases:
            self.skipTest("no oracle cases selected")
        oracle._run_oracle_cases(cases)
