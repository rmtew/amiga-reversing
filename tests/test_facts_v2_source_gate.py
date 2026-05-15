from __future__ import annotations

import pytest

from amiga_reversing.disasm.facts_v2_source_gate import (
    FactsV2SourceGateStatus,
    _summary,
)


def test_facts_v2_source_gate_summary_uses_typed_statuses() -> None:
    summary = _summary(
        [
            {"status": FactsV2SourceGateStatus.PASSED, "gate_passed": True},
            {
                "status": FactsV2SourceGateStatus.FAILED,
                "gate_passed": False,
                "target": "bad",
                "gate_failures": ["facts_v2_asm_source_refused"],
            },
        ]
    )

    assert summary["passed_count"] == 1
    assert summary["failed_count"] == 1
    assert summary["first_gate_failure_target"] == "bad"


def test_facts_v2_source_gate_summary_rejects_string_statuses() -> None:
    with pytest.raises(TypeError, match="FactsV2SourceGateStatus"):
        _summary([{"status": "passed", "gate_passed": True}])
