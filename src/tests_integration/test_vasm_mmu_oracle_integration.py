from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from src.tests._oracle_matrix_helpers import load_mmu_oracle_matrix
from src.tests._oracle_matrix_helpers import unsupported_mmu_oracle_mnemonics

ROOT = Path(__file__).resolve().parents[2]
PROBE_SCRIPT = ROOT / "src" / "scripts" / "probe_vasm_mmu_oracle.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class VasmMmuOracleIntegrationTests(unittest.TestCase):
    def test_checked_in_vasm_mmu_oracle_matrix_is_stable(self) -> None:
        module = _load_module(PROBE_SCRIPT, "src_probe_vasm_mmu_oracle")
        expected = load_mmu_oracle_matrix()
        actual = module.build_matrix()
        self.assertEqual(actual, expected)

    def test_oracle_backed_mmu_support_boundary_is_explicit(self) -> None:
        self.assertEqual(list(unsupported_mmu_oracle_mnemonics()), ["PBcc", "PDBcc", "PMOVE", "PScc", "PTRAPcc"])

    def test_unprobed_coprocessor_families_remain_explicitly_unprobed(self) -> None:
        matrix = load_mmu_oracle_matrix()
        self.assertEqual(
            sorted(matrix["unprobed_mnemonics"]),
            ["cpBcc", "cpDBcc", "cpGEN", "cpRESTORE", "cpSAVE", "cpScc", "cpTRAPcc"],
        )


if __name__ == "__main__":
    unittest.main()
