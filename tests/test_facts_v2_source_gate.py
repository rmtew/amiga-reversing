from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm.facts_v2_source_gate import (
    FactsV2SourceGateStatus,
    _summary,
    facts_v2_source_gate_report_for_target,
)
from amiga_reversing.disasm.source_rendering import SourceRenderingResult


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


def test_facts_v2_source_gate_uses_source_rendering_module(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    binary_source = SimpleNamespace(read_bytes=lambda: b"\x4e\x75")
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        "amiga_reversing.disasm.facts_v2_source_gate.resolve_project_paths",
        lambda target, project_root: SimpleNamespace(target_dir=target_dir, binary_source=binary_source),
    )

    @contextmanager
    def fake_metadata_file(path: Path):
        assert path == target_dir
        yield path / "effective_metadata.json"

    monkeypatch.setattr(
        "amiga_reversing.disasm.facts_v2_source_gate.effective_metadata_file",
        fake_metadata_file,
    )

    def render_source_from_binary_source(**kwargs: object) -> SourceRenderingResult:
        calls.append(kwargs)
        return SourceRenderingResult(
            status="ok",
            source_text="    rts\n",
            listing_profile={
                "facts_v2": {
                    "asm_source_enabled": True,
                    "asm_source_symbolic_instructions": 1,
                }
            },
            workflow_profile={"workflow_id": "facts_v2_source_gate", "spans": []},
            metadata_hash="metadata",
            target_identity_sha256="identity",
        )

    monkeypatch.setattr(
        "amiga_reversing.disasm.facts_v2_source_gate.render_source_from_binary_source",
        render_source_from_binary_source,
    )

    report = facts_v2_source_gate_report_for_target("demo", project_root=tmp_path)

    assert report["status"] is FactsV2SourceGateStatus.PASSED
    assert report["source_fingerprint"]["line_count"] == 1
    assert calls[0]["workflow_id"] == "facts_v2_source_gate"
    assert calls[0]["binary_source"] is binary_source
