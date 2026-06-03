from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

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


def test_roundtrip_report_target_filter_keeps_requested_targets() -> None:
    targets = [
        ("amiga_hunk_alpha", Path("targets/alpha/alpha.s")),
        ("amiga_hunk_beta", Path("targets/beta/beta.s")),
    ]

    assert report_tool._filter_targets(targets, ["amiga_hunk_beta"]) == [
        ("amiga_hunk_beta", Path("targets/beta/beta.s"))
    ]


def test_roundtrip_report_target_filter_rejects_unknown_targets() -> None:
    targets = [("amiga_hunk_alpha", Path("targets/alpha/alpha.s"))]

    with pytest.raises(SystemExit, match="amiga_hunk_missing"):
        report_tool._filter_targets(targets, ["amiga_hunk_missing"])


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
        lambda target, source_path, update_rendered_source=False, **kwargs: {
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


def test_roundtrip_report_analysis_export_writes_failing_rows(monkeypatch, tmp_path: Path) -> None:
    source_path = tmp_path / "demo.s"
    export_dir = tmp_path / "analysis"
    calls: list[dict[str, object]] = []

    def run_reproduction(target: str, **kwargs: object) -> dict[str, object]:
        return {
            "status": "mismatch",
            "comparison": {
                "full_file_exact": False,
                "content_exact": False,
                "failure_kinds": ["content_mismatch"],
                "diff_range_count": 1,
            },
        }

    def export_target_analysis(row: dict[str, object], path: Path, directory: Path) -> Path:
        calls.append({"row": dict(row), "path": path, "directory": directory})
        directory.mkdir(parents=True)
        export_path = directory / "amiga_hunk_demo.analysis.json"
        export_path.write_text("{}\n", encoding="utf-8")
        return export_path

    monkeypatch.setattr(report_tool, "run_reproduction", run_reproduction)
    monkeypatch.setattr(report_tool, "_export_target_analysis", export_target_analysis)
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None: "rts\n")

    row = report_tool._run_target("amiga_hunk_demo", source_path, analysis_export_dir=export_dir)

    assert row["analysis_export_path"].endswith("amiga_hunk_demo.analysis.json")
    assert calls and calls[0]["directory"] == export_dir


def test_roundtrip_report_analysis_export_uses_render_evidence_analysis(monkeypatch, tmp_path: Path) -> None:
    source_path = tmp_path / "demo.s"
    binary_source = object()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    export_dir = tmp_path / "analysis"
    calls: list[dict[str, object]] = []

    class MetadataContext:
        def __enter__(self) -> Path:
            return tmp_path / "target_metadata.json"

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    def analyze(binary_source_arg: object, *, metadata_path: Path, project_root: Path) -> dict[str, object]:
        calls.append(
            {
                "fn": "analyze",
                "binary_source": binary_source_arg,
                "metadata_path": metadata_path,
                "project_root": project_root,
            }
        )
        return {
            "sections": [
                {
                    "rendered_symbol_access_count": 1,
                    "rendered_symbol_accesses": [{"symbol_name": "entry"}],
                }
            ]
        }

    def explain(binary_source_arg: object, *, metadata_path: Path, project_root: Path) -> dict[str, object]:
        calls.append(
            {
                "fn": "explain",
                "binary_source": binary_source_arg,
                "metadata_path": metadata_path,
                "project_root": project_root,
            }
        )
        return {"source_quality_explanations": []}

    paths = SimpleNamespace(binary_source=binary_source, target_dir=target_dir)

    monkeypatch.setattr(report_tool, "resolve_project_paths", lambda target, project_root: paths)
    monkeypatch.setattr(report_tool, "effective_metadata_file", lambda path: MetadataContext())
    monkeypatch.setattr(report_tool, "analyze_project_source_with_render_evidence_from_c_backend", analyze)
    monkeypatch.setattr(report_tool, "source_quality_explain_project_source_with_c_backend", explain)

    export_path = report_tool._export_target_analysis(
        {
            "target": "amiga_hunk_demo",
            "status": "mismatch",
            "rendered_source_full_file_exact": False,
            "rendered_source_content_exact": False,
            "failure_kinds": ["content_mismatch"],
            "diff_range_count": 1,
            "tool_error": None,
            "message": None,
        },
        source_path,
        export_dir,
    )

    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["analysis"]["sections"][0]["rendered_symbol_access_count"] == 1
    assert [call["fn"] for call in calls] == ["analyze", "explain"]


def test_roundtrip_report_analysis_export_skips_success_by_default(monkeypatch, tmp_path: Path) -> None:
    source_path = tmp_path / "demo.s"
    calls: list[object] = []

    def run_reproduction(target: str, **kwargs: object) -> dict[str, object]:
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
    monkeypatch.setattr(report_tool, "_export_target_analysis", lambda *args: calls.append(args))
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None: "rts\n")

    row = report_tool._run_target("amiga_hunk_demo", source_path, analysis_export_dir=tmp_path / "analysis")

    assert "analysis_export_path" not in row
    assert calls == []


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
