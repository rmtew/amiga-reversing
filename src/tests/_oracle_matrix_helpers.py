from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MMU_ORACLE_MATRIX_PATH = ROOT / "src" / "tests" / "generated" / "vasm_mmu_oracle_matrix.json"


@lru_cache(maxsize=1)
def load_mmu_oracle_matrix() -> dict[str, object]:
    return json.loads(MMU_ORACLE_MATRIX_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def unsupported_mmu_oracle_mnemonics() -> tuple[str, ...]:
    matrix = load_mmu_oracle_matrix()
    return tuple(sorted({
        str(case["mnemonic"])
        for case in matrix["cases"]
        if case["vasm"]["accepted"] and not case["ours_matches_oracle"]
    }))


@lru_cache(maxsize=1)
def unsupported_mmu_round_trip_mnemonics_upper() -> frozenset[str]:
    return frozenset(
        mnemonic.upper()
        for mnemonic in (*unsupported_mmu_oracle_mnemonics(), "PFLUSH PFLUSHA", "PFLUSHA")
    )
