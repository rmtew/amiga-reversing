from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import tool_graph


def test_tool_graph_registry_v2_load_save_missing_empty_and_populated(tmp_path: Path) -> None:
    assert tool_graph.load_tool_registry(project_root=tmp_path) == {
        "version": 2,
        "runtime_tools": {},
        "functional_tools": {},
    }

    payload = {
        "version": 2,
        "runtime_tools": {"vamos": {"path": "tools/vamos"}},
        "functional_tools": {"vasm": {"path": "tools/vasm"}},
    }
    path = tool_graph.save_tool_registry(payload, project_root=tmp_path)

    assert path == tmp_path / ".amiga_reversing" / "tool_registry.json"
    assert tool_graph.load_tool_registry(project_root=tmp_path) == payload
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["runtime_tools"]["vamos"]["path"] == "tools/vamos"
    assert saved["functional_tools"]["vasm"]["path"] == "tools/vasm"


def test_tool_graph_rejects_v1_and_invalid_payloads(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported tool registry version"):
        tool_graph.save_tool_registry({"version": 1, "tools": {"vasm": {}}}, project_root=tmp_path)

    with pytest.raises(ValueError, match="unsupported functional tool id"):
        tool_graph.save_tool_registry({"version": 2, "functional_tools": {"bad": {}}}, project_root=tmp_path)

    with pytest.raises(ValueError, match="host runtime is synthetic"):
        tool_graph.save_tool_registry({"version": 2, "runtime_tools": {"host": {}}}, project_root=tmp_path)

    with pytest.raises(ValueError, match="must be a string"):
        tool_graph.save_tool_registry({"version": 2, "functional_tools": {"vasm": {"path": 3}}}, project_root=tmp_path)


def test_genam_artifact_available_missing_vamos_is_not_runnable(tmp_path: Path) -> None:
    genam = tmp_path / "bin" / "GenAm"
    genam.parent.mkdir()
    genam.write_bytes(b"genam")

    record = tool_graph.functional_tool_record("genam", project_root=tmp_path, env_path="")

    assert record["artifact_status"] == "available"
    assert record["runnable_status"] == "missing"
    assert record["missing_runtime_ids"] == ["vamos"]
    assert record["probe_evidence"]["probe_method"] == "hash_only"
    assert record["probe_evidence"]["version_text"] is None


def test_assemble_devpac_source_resolves_genam_through_vamos(tmp_path: Path) -> None:
    genam = tmp_path / "GenAm"
    vamos = tmp_path / "vamos.exe"
    genam.write_bytes(b"genam")
    vamos.write_bytes(b"vamos")
    tool_graph.save_tool_registry(
        {
            "version": 2,
            "runtime_tools": {"vamos": {"path": str(vamos)}},
            "functional_tools": {"genam": {"path": str(genam)}},
        },
        project_root=tmp_path,
    )

    resolution = tool_graph.resolve_capability("assemble_devpac_source", project_root=tmp_path)

    selected = resolution["selected"]
    assert resolution["available"] is True
    assert selected["functional_tool_id"] == "genam"
    assert selected["runtime_tool_id"] == "vamos"
    assert selected["tool_chain"] == ["vamos", "genam"]
    assert selected["runnable_status"] == "available"


def test_assemble_vasm_source_resolves_vasm_through_host(tmp_path: Path) -> None:
    vasm = tmp_path / "vasmm68k_mot.exe"
    vasm.write_bytes(b"vasm")
    tool_graph.save_tool_registry(
        {"version": 2, "functional_tools": {"vasm": {"path": str(vasm)}}},
        project_root=tmp_path,
    )

    resolution = tool_graph.resolve_capability("assemble_vasm_source", project_root=tmp_path)

    selected = resolution["selected"]
    assert resolution["available"] is True
    assert selected["functional_tool_id"] == "vasm"
    assert selected["runtime_tool_id"] == "host"
    assert selected["tool_chain"] == ["vasm"]
    assert selected["runtime_status"] == "available"


def test_capability_availability_uses_runnable_status(tmp_path: Path) -> None:
    genam = tmp_path / "bin" / "GenAm"
    genam.parent.mkdir()
    genam.write_bytes(b"genam")
    tool_graph.save_tool_registry(
        {"version": 2, "runtime_tools": {"vamos": {"path": str(tmp_path / "missing-vamos.exe")}}},
        project_root=tmp_path,
    )

    records = tool_graph.capability_availability_for_modes(["devpac"], project_root=tmp_path)

    assert records[0]["capability_id"] == "assemble_devpac_source"
    assert records[0]["tool_id"] == "genam"
    assert records[0]["artifact_status"] == "available"
    assert records[0]["status"] == "missing"
    assert records[0]["missing_runtime_ids"] == ["vamos"]
