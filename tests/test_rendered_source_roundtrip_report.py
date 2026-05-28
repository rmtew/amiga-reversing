from __future__ import annotations

from pathlib import Path
from typing import Any

from amiga_reversing.tools import rendered_source_roundtrip_report as report_tool


def test_roundtrip_report_verifies_without_persisting_reproduction_report(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    def run_reproduction(target: str, **kwargs: object) -> dict[str, object]:
        calls.append({"target": target, "kwargs": kwargs})
        return {
            "status": "exact",
            "comparison": {
                "full_file_exact": True,
                "content_exact": True,
                "failure_kinds": [],
                "diff_range_count": 0,
            },
        }

    monkeypatch.setattr(report_tool, "run_reproduction", run_reproduction)

    row = report_tool._run_target("amiga_hunk_demo", Path("targets/demo/asm.s"))

    assert row["status"] == "exact"
    assert row["rendered_source_full_file_exact"] is True
    assert calls == [
        {
            "target": "amiga_hunk_demo",
            "kwargs": {"assembler": "our", "profile": True, "persist_report": False},
        }
    ]
