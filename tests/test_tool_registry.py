from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import tool_registry


def test_tool_registry_load_save_missing_empty_and_populated(tmp_path: Path) -> None:
    assert tool_registry.load_tool_registry(project_root=tmp_path) == {"version": 1, "tools": {}}

    payload = {"version": 1, "tools": {"vasm": {"path": "tools/vasm", "hints": ["local"]}}}
    path = tool_registry.save_tool_registry(payload, project_root=tmp_path)

    assert path == tmp_path / ".amiga_reversing" / "tool_registry.json"
    assert tool_registry.load_tool_registry(project_root=tmp_path) == payload
    assert json.loads(path.read_text(encoding="utf-8"))["tools"]["vasm"]["path"] == "tools/vasm"
    tool_registry.save_tool_registry({"tools": {}}, project_root=tmp_path)
    assert tool_registry.load_tool_registry(project_root=tmp_path) == {"version": 1, "tools": {}}


def test_tool_registry_rejects_invalid_payloads(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported tool id"):
        tool_registry.save_tool_registry({"version": 1, "tools": {"bad": {}}}, project_root=tmp_path)

    with pytest.raises(ValueError, match="must be a string"):
        tool_registry.save_tool_registry({"version": 1, "tools": {"vasm": {"path": 3}}}, project_root=tmp_path)


def test_tool_availability_prefers_configured_path_over_path_lookup(tmp_path: Path) -> None:
    configured = tmp_path / "configured_vasm.exe"
    configured.write_bytes(b"configured")
    path_dir = tmp_path / "path"
    path_dir.mkdir()
    path_vasm = path_dir / "vasmm68k_mot.exe"
    path_vasm.write_bytes(b"path")
    tool_registry.save_tool_registry(
        {"version": 1, "tools": {"vasm": {"path": str(configured)}}},
        project_root=tmp_path,
    )

    record = tool_registry.tool_availability_record(
        "vasm",
        required=True,
        project_root=tmp_path,
        env_path=str(path_dir),
    )

    assert record["status"] == "available"
    assert record["required"] is True
    assert record["resolved_path"] == str(configured)
    assert record["discovery_source"] == "configured_path"
    assert record["executable_stamp"]


def test_tool_availability_reports_missing_unsupported_and_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing = tmp_path / "missing_vasm.exe"
    unsupported = tmp_path / "dir"
    unsupported.mkdir()
    broken = tmp_path / "broken_vasm.exe"
    broken.write_bytes(b"broken")

    missing_record = tool_registry._availability_for_path(
        "vasm", missing, required=False, discovery_source="configured_path"
    )
    unsupported_record = tool_registry._availability_for_path(
        "vasm", unsupported, required=False, discovery_source="configured_path"
    )
    monkeypatch.setattr(tool_registry, "_executable_stamp", lambda path: (_ for _ in ()).throw(OSError("probe failed")))
    error_record = tool_registry._availability_for_path(
        "vasm", broken, required=False, discovery_source="configured_path"
    )

    assert missing_record["status"] == "missing"
    assert unsupported_record["status"] == "unsupported"
    assert error_record["status"] == "error"
    assert "probe failed" in str(error_record["message"])


def test_oracle_tool_ids_for_modes_are_limited() -> None:
    assert tool_registry.oracle_tool_ids_for_modes(["vasm"]) == ("vasm",)
    assert tool_registry.oracle_tool_ids_for_modes(["devpac"]) == ("genam", "vamos")
    assert tool_registry.oracle_tool_ids_for_modes(["devpac", "vasm", "devpac"]) == ("genam", "vamos", "vasm")
