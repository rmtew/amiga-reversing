from __future__ import annotations

import json
from pathlib import Path

from scripts.analyze_per_caller_trace import main


def test_analyze_per_caller_trace_summarizes_sites(capsys: object, tmp_path: Path) -> None:
    trace_path = tmp_path / "per_caller.jsonl"
    trace_path.write_text(
        "\n".join(
            json.dumps(event)
            for event in [
                {"kind": "site_start", "source_addr": 0x100, "needed_regs": ["a2"]},
                {"kind": "collect_call_entry_states", "source_addr": 0x100, "unique_state_signatures": 2},
                {"kind": "site_resolution", "source_addr": 0x100, "target": 0x200, "needed_regs": {"a2": [True, 512, None, None, None, "None"]}},
                {"kind": "site_done", "source_addr": 0x100, "elapsed_seconds": 1.5, "resolution_count": 1},
                {"kind": "build_caller_ctx", "entry": 0x80, "elapsed_seconds": 0.2},
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert main(["analyze_per_caller_trace.py", str(trace_path)]) == 0
    out = capsys.readouterr().out
    assert "$0100: 1.5000s" in out
    assert "unique_targets=1" in out
    assert "needed_regs=['a2']" in out
    assert "reg_projections=1" in out
    assert "$0080: caller_ctx_builds=1" in out
