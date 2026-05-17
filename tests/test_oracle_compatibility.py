from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from amiga_reversing.disasm import oracle_compatibility
from amiga_reversing.disasm.binary_source import BinarySourceKind


def _available(tool_id: str, path: Path) -> dict[str, object]:
    return {
        "tool_id": tool_id,
        "status": "available",
        "required": True,
        "resolved_path": str(path),
        "version": None,
        "discovery_source": "configured_path",
        "message": f"{tool_id} is available",
        "executable_stamp": {"sha256": "0" * 64, "size": 1, "mtime_ns": 1},
    }


def _capability(
    capability_id: str,
    functional_tool_id: str,
    path: Path,
    *,
    runtime_tool_id: str = "host",
    runtime_path: Path | None = None,
    status: str = "available",
    artifact_status: str = "available",
    runtime_status: str = "available",
    missing_runtime_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "capability_id": capability_id,
        "status": status,
        "available": status == "available",
        "selected": {
            "capability_id": capability_id,
            "functional_tool_id": functional_tool_id,
            "runtime_tool_id": runtime_tool_id,
            "tool_chain": [functional_tool_id] if runtime_tool_id == "host" else [runtime_tool_id, functional_tool_id],
            "runnable_status": status,
            "artifact_status": artifact_status,
            "runtime_status": runtime_status,
            "missing_runtime_ids": missing_runtime_ids or [],
            "functional_resolved_path": str(path),
            "runtime_resolved_path": str(runtime_path) if runtime_path is not None else None,
            "message": f"{functional_tool_id} is runnable" if status == "available" else f"{functional_tool_id} unavailable",
            "probe_evidence": {
                "probe_method": "hash_only" if functional_tool_id == "genam" else "native_version",
                "probe_status": artifact_status,
                "version_text": None,
                "executable_stamp": {"sha256": "0" * 64, "size": 1, "mtime_ns": 1},
            },
        },
        "candidates": [],
    }


def test_oracle_comparison_levels_are_scoped() -> None:
    assert set(oracle_compatibility.ORACLE_COMPARISON_LEVELS) == {
        "oracle.full_file_match",
        "oracle.content_match",
        "oracle.mismatch",
        "oracle.not_comparable",
        "oracle.missing",
        "oracle.not_run",
    }
    assert "exact" not in oracle_compatibility.ORACLE_COMPARISON_LEVELS


def test_vasm_oracle_reports_full_file_match_with_fake_tool(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    vasm_path = tmp_path / "vasm.exe"
    vasm_path.write_bytes(b"x")
    binary_source = SimpleNamespace(
        kind=BinarySourceKind.HUNK_FILE,
        display_path="bin/Demo",
        read_bytes=lambda: b"\x01\x02",
    )
    monkeypatch.setattr(
        oracle_compatibility,
        "resolve_capability",
        lambda capability_id, project_root=None: _capability("assemble_vasm_source", "vasm", vasm_path),
    )
    monkeypatch.setattr(
        oracle_compatibility,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(target_dir=target_dir, binary_source=binary_source),
    )
    monkeypatch.setattr(oracle_compatibility, "_render_vasm_source", lambda *args: ("    rts\n", {"source": "fake"}))

    def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        output_path = Path(command[command.index("-o") + 1])
        output_path.write_bytes(b"\x01\x02")
        return subprocess.CompletedProcess(command, 0, "ok", "")

    monkeypatch.setattr(oracle_compatibility, "_run_command", run)

    report = oracle_compatibility.run_vasm_oracle("demo", project_root=tmp_path)

    assert report["comparison_level"] == "oracle.full_file_match"
    assert report["assembler_status"] == "accepted"
    assert report["source_profile"] == "vasm"
    assert report["rendered_source_sha256"]
    assert report["availability"][0]["tool_id"] == "vasm"
    assert report["comparison"]["full_file_exact"] is True


def test_vasm_oracle_reports_rejected_source(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    vasm_path = tmp_path / "vasm.exe"
    vasm_path.write_bytes(b"x")
    binary_source = SimpleNamespace(
        kind=BinarySourceKind.HUNK_FILE,
        display_path="bin/Demo",
        read_bytes=lambda: b"\x01\x02",
    )
    monkeypatch.setattr(
        oracle_compatibility,
        "resolve_capability",
        lambda capability_id, project_root=None: _capability("assemble_vasm_source", "vasm", vasm_path),
    )
    monkeypatch.setattr(
        oracle_compatibility,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(target_dir=target_dir, binary_source=binary_source),
    )
    monkeypatch.setattr(oracle_compatibility, "_render_vasm_source", lambda *args: ("bad\n", {}))
    monkeypatch.setattr(
        oracle_compatibility,
        "_run_command",
        lambda command, *, cwd: subprocess.CompletedProcess(command, 1, "", "syntax error"),
    )

    report = oracle_compatibility.run_vasm_oracle("demo", project_root=tmp_path)

    assert report["comparison_level"] == "oracle.not_run"
    assert report["assembler_status"] == "rejected"
    assert report["stderr_excerpt"] == "syntax error"
    assert "exact" not in str(report["comparison_level"]).removeprefix("oracle.")


def test_vasm_oracle_reports_content_match(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    vasm_path = tmp_path / "vasm.exe"
    vasm_path.write_bytes(b"x")
    binary_source = SimpleNamespace(
        kind=BinarySourceKind.HUNK_FILE,
        display_path="bin/Demo",
        read_bytes=lambda: b"\x01\x02",
    )
    monkeypatch.setattr(
        oracle_compatibility,
        "resolve_capability",
        lambda capability_id, project_root=None: _capability("assemble_vasm_source", "vasm", vasm_path),
    )
    monkeypatch.setattr(
        oracle_compatibility,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(target_dir=target_dir, binary_source=binary_source),
    )
    monkeypatch.setattr(oracle_compatibility, "_render_vasm_source", lambda *args: ("    rts\n", {}))
    monkeypatch.setattr(
        oracle_compatibility,
        "reproduction_compare_rebuilt_bytes_with_c_backend_profile",
        lambda *args, **kwargs: {"reproduction_compare_exactness_id": 2},
    )

    def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        Path(command[command.index("-o") + 1]).write_bytes(b"\x01\xff")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(oracle_compatibility, "_run_command", run)

    report = oracle_compatibility.run_vasm_oracle("demo", project_root=tmp_path)

    assert report["comparison_level"] == "oracle.content_match"
    assert report["comparison"]["content_exact"] is True


def test_genam_oracle_reports_missing_vamos(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        oracle_compatibility,
        "resolve_capability",
        lambda capability_id, project_root=None: _capability(
            "assemble_devpac_source",
            "genam",
            tmp_path / "GenAm",
            runtime_tool_id="vamos",
            status="missing",
            artifact_status="available",
            runtime_status="missing",
            missing_runtime_ids=["vamos"],
        ),
    )

    report = oracle_compatibility.run_genam_oracle("demo", project_root=tmp_path)

    assert report["oracle_id"] == "genam-devpac"
    assert report["comparison_level"] == "oracle.missing"
    assert report["assembler_status"] == "not_run"
    assert report["availability"][0]["missing_runtime_ids"] == ["vamos"]
