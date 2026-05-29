from __future__ import annotations

from pathlib import Path
from typing import Any

from amiga_reversing.tools import rendered_source_roundtrip_report as report_tool


def test_roundtrip_report_payload_is_deterministic() -> None:
    payload = report_tool._report_payload(
        {
            "targets": 1,
            "rendered_source_full_file_exact": 0,
            "rendered_source_content_exact_only": 1,
            "unsupported": 0,
            "failures": 0,
        },
        [
            {
                "target": "amiga_hunk_demo",
                "status": "content_exact",
                "rendered_source_full_file_exact": False,
                "rendered_source_content_exact": True,
                "failure_kinds": ["container_shape_mismatch", "size_mismatch"],
                "diff_range_count": 3,
                "tool_error": None,
                "message": None,
                "source_updated": True,
            }
        ],
    )

    assert payload == {
        "schema_version": 1,
        "summary": {
            "targets": 1,
            "rendered_source_full_file_exact": 0,
            "rendered_source_content_exact_only": 1,
            "unsupported": 0,
            "failures": 0,
        },
        "targets": [
            {
                "target": "amiga_hunk_demo",
                "status": "content_exact",
                "rendered_source_full_file_exact": False,
                "rendered_source_content_exact": True,
                "failure_kinds": ["container_shape_mismatch", "size_mismatch"],
                "diff_range_count": 3,
                "tool_error": None,
                "message": None,
            }
        ],
    }


def test_roundtrip_report_drift_is_written_and_reported(tmp_path: Path) -> None:
    report_path = tmp_path / "roundtrip.json"
    payload = {
        "schema_version": 1,
        "summary": {"targets": 0, "rendered_source_full_file_exact": 0, "rendered_source_content_exact_only": 0},
        "targets": [],
    }

    assert report_tool._report_has_drift(report_path, payload) is True
    report_tool._write_report(report_path, payload)
    assert report_tool._report_has_drift(report_path, payload) is False


def test_roundtrip_report_default_flags_and_writes_report_drift(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    report_path = tmp_path / "roundtrip.json"
    report_path.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(
        report_tool,
        "_rendered_source_targets",
        lambda targets_root: [("amiga_hunk_demo", targets_root / "demo" / "asm.s")],
    )
    monkeypatch.setattr(
        report_tool,
        "_run_target",
        lambda target, source_path, update_rendered_source=False: {
            "target": target,
            "status": "exact",
            "rendered_source_full_file_exact": True,
            "rendered_source_content_exact": True,
            "failure_kinds": [],
            "diff_range_count": 0,
            "tool_error": None,
            "message": None,
            "source_updated": update_rendered_source,
        },
    )

    exit_code = report_tool.main(["--targets-root", str(tmp_path), "--report-path", str(report_path)])

    assert exit_code == 1
    assert "report-drift" in capsys.readouterr().out
    assert report_tool._report_has_drift(
        report_path,
        {
            "schema_version": 1,
            "summary": {
                "targets": 1,
                "rendered_source_full_file_exact": 1,
                "rendered_source_content_exact_only": 0,
                "unsupported": 0,
                "failures": 0,
            },
            "targets": [
                {
                    "target": "amiga_hunk_demo",
                    "status": "exact",
                    "rendered_source_full_file_exact": True,
                    "rendered_source_content_exact": True,
                    "failure_kinds": [],
                    "diff_range_count": 0,
                    "tool_error": None,
                    "message": None,
                }
            ],
        },
    ) is False


def test_roundtrip_report_verifies_without_persisting_reproduction_report(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []
    source_path = Path("targets/demo/asm.s")

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
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None: "rts\n")

    row = report_tool._run_target("amiga_hunk_demo", source_path)

    assert row["status"] == "exact"
    assert row["rendered_source_full_file_exact"] is True
    assert calls == [
        {
            "target": "amiga_hunk_demo",
            "kwargs": {
                "assembler": "our",
                "profile": True,
                "persist_report": False,
                "pre_rendered_source_text": "rts\n",
            },
        }
    ]


def test_roundtrip_report_update_mode_writes_then_verifies_pre_rendered_source(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    source_path = tmp_path / "demo.s"

    def update_rendered_source(target: str, path: Path) -> tuple[str, dict[str, object]]:
        assert target == "amiga_hunk_demo"
        assert path == source_path
        path.write_text("rts\n", encoding="utf-8")
        return "rts\n", {"generation": "facts_v2_asm_source"}

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

    monkeypatch.setattr(report_tool, "_update_rendered_source", update_rendered_source)
    monkeypatch.setattr(report_tool, "run_reproduction", run_reproduction)

    row = report_tool._run_target("amiga_hunk_demo", source_path, update_rendered_source=True)

    assert source_path.read_text(encoding="utf-8") == "rts\n"
    assert row["source_updated"] is True
    assert calls == [
        {
            "target": "amiga_hunk_demo",
            "kwargs": {
                "assembler": "our",
                "profile": True,
                "persist_report": False,
                "pre_rendered_source_text": "rts\n",
                "pre_rendered_source_profile": {"generation": "facts_v2_asm_source"},
            },
        }
    ]


def test_roundtrip_report_update_mode_keeps_macos_unsupported(monkeypatch, tmp_path: Path) -> None:
    def update_rendered_source(target: str, path: Path) -> tuple[str, dict[str, object]]:
        raise AssertionError("Mac OS source should not be regenerated by round-trip update mode")

    monkeypatch.setattr(report_tool, "_update_rendered_source", update_rendered_source)

    row = report_tool._run_target(
        "macos_hfs_mpw_gm__macos_file_mpw_tools_asm",
        tmp_path / "targets" / "macos_file_mpw_tools_asm" / "asm.s",
        update_rendered_source=True,
    )

    assert row["status"] == "unsupported"
    assert row["source_updated"] is False
