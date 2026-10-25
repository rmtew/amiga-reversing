"""Stored absolute pointers keep their encoding separate from source identity."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import c_backend, server
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_metadata_text,
)
from amiga_reversing.disasm.manual_action_catalog import _data_block_element_ref_payload
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    load_manual_projection,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import ProjectKind
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def _ref(encoded: int, target: int) -> dict[str, object]:
    parameters = {"layout_id": "pointers", "offset": 0, "width": 4,
                  "reference_kind": "absolute", "target_hunk": 0, "target_offset": target,
                  "source_value": encoded}
    if encoded != target:
        parameters["runtime_address"] = encoded
    return _data_block_element_ref_payload([], parameters)


def _write_actions(target_dir: Path, ref: dict[str, object], cleanup: str | None = None) -> None:
    actions = [("create_manual_data_block_layout", "data_block_layout",
                {"layout_id": "pointers", "hunk": 0, "source_start": 2, "source_end": 6,
                 "default_unit": "long"}),
               ("set_manual_data_block_element", "data_block_element",
                {"layout_id": "pointers", "offset": 0, "width": 4, "kind": "scalar"}),
               ("interpret_manual_data_block_element_ref", "data_block_interpreted_ref", ref)]
    if cleanup == "reference":
        actions.append(("remove_manual_data_block_element_ref", "data_block_interpreted_ref",
                        {"data_block_ref_id": ref["data_block_ref_id"], "layout_id": "pointers", "offset": 0}))
    elif cleanup == "element":
        actions.append(("remove_manual_data_block_element", "data_block_element",
                        {"layout_id": "pointers", "offset": 0}))
    elif cleanup == "layout":
        actions.append(("remove_manual_data_block_layout", "data_block_layout", {"layout_id": "pointers"}))
    records = [{"record": "manual_action_log_header", "version": 1, "target_identity": {}}]
    records.extend({"record": "manual_action", "action_id": f"a{i}", "sequence": i,
                    "created_at": "2026-10-13T00:00:00+00:00", "kind": kind, key: payload}
                   for i, (kind, key, payload) in enumerate(actions, 1))
    (target_dir / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


@pytest.mark.parametrize(("encoded", "target"), [(0, 0), (6, 6), (0x4000, 0), (0x4006, 6)])
def test_encoded_value_and_source_identity_survive_reload_and_projection(tmp_path: Path, encoded: int, target: int) -> None:
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    ref = _ref(encoded, target)
    _write_actions(tmp_path, ref)
    assert load_manual_projection(tmp_path).data_block_interpreted_refs == (ref,)
    metadata = json.loads(effective_metadata_text(tmp_path))
    equate, = metadata["target_equates"]
    native, = metadata["manual_runtime_address_refs"]
    assert equate["value"] == native["runtime_address"] == encoded
    assert native["target_hunk"] == 0 and native["target_offset"] == target
    assert metadata["manual_representations"][0]["symbol"] == equate["name"]
    assert ("_runtime_" in equate["name"]) == (encoded != target)


@pytest.mark.parametrize("cleanup", ["reference", "element", "layout"])
def test_runtime_reference_cleanup_removes_all_owned_projection(tmp_path: Path, cleanup: str) -> None:
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    _write_actions(tmp_path, _ref(0x4006, 6), cleanup)
    assert not load_manual_projection(tmp_path).data_block_interpreted_refs
    metadata = json.loads(effective_metadata_text(tmp_path))
    assert not metadata["manual_runtime_address_refs"]
    assert not metadata["manual_representations"]
    assert not metadata["target_equates"]


@pytest.mark.parametrize(("status", "section", "offset", "accepted"), [
    ("resolved", 0, 0, True), ("resolved", 0, 6, False),
    ("resolved", 1, 0, False), ("unmapped", None, None, False),
    ("ambiguous", None, None, False),
])
def test_command_requires_unique_current_native_mapping(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        status: str, section: int | None, offset: int | None, accepted: bool) -> None:
    ref = _ref(0x4000, 0)
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    _write_actions(tmp_path, ref)
    artifact = SimpleNamespace(source_for_runtime_address=lambda **kwargs:
                               {"status": status, "section_index": section, "source_offset": offset},
                               row_for_source_offset=lambda **kwargs: {"start_offset": 2, "bytes": "00004000"})
    monkeypatch.setattr(server, "get_project", lambda _: SimpleNamespace(
        kind=ProjectKind.BINARY, ready=True, target_dir=str(tmp_path)))
    monkeypatch.setattr(server, "_valid_c_listing_artifact", lambda _: artifact)
    monkeypatch.setattr(server, "target_catalog_manual_payload", lambda *args:
                        ("interpret_manual_data_block_element_ref", {"data_block_interpreted_ref": ref}))
    if accepted:
        result = server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})
        assert result[0][1]["data_block_interpreted_ref"] == ref
    else:
        with pytest.raises(ValueError, match="unique matching active native source mapping"):
            server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})


@pytest.mark.parametrize(("row", "owner_exists", "accepted"), [
    ({"start_offset": 2, "bytes": "00004006"}, True, False),
    ({"start_offset": 2, "bytes": "000040"}, True, False),
    ({"start_offset": 2}, True, False), (None, True, False),
    ({"start_offset": 2, "bytes": "00004000"}, False, False),
    ({"start_offset": 0, "bytes": "ABCD00004000"}, True, True),
])
def test_target_command_checks_current_owner_bytes_before_resolving(tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch, row: dict[str, object] | None,
        owner_exists: bool, accepted: bool) -> None:
    ref = _ref(0x4000, 0)
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    if owner_exists:
        _write_actions(tmp_path, ref)
    calls = []

    def resolve(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"status": "resolved", "section_index": 0, "source_offset": 0}

    artifact = SimpleNamespace(source_for_runtime_address=resolve,
                               row_for_source_offset=lambda **kwargs: row)
    monkeypatch.setattr(server, "get_project", lambda _: SimpleNamespace(
        kind=ProjectKind.BINARY, ready=True, target_dir=str(tmp_path)))
    monkeypatch.setattr(server, "_valid_c_listing_artifact", lambda _: artifact)
    monkeypatch.setattr(server, "target_catalog_manual_payload", lambda *args:
                        ("interpret_manual_data_block_element_ref", {"data_block_interpreted_ref": ref}))
    if accepted:
        result = server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})
        assert result[0][1]["data_block_interpreted_ref"] == ref
        assert calls == [{"address": 0x4000}]
    else:
        with pytest.raises(ValueError, match="data-block runtime reference"):
            server._prepare_manual_action_command("synthetic", "interpret", {"kind": "target"}, [], {})
        assert not calls


def test_runtime_encoding_cannot_disagree_with_selected_bytes() -> None:
    parameters = {**_ref(0x4006, 6), "runtime_address": 0x4007}
    with pytest.raises(ValueError, match="runtime_address must match selected source bytes"):
        _data_block_element_ref_payload([{"bytes": "00004006"}], parameters)


def test_distinct_runtime_views_of_same_source_have_distinct_symbols() -> None:
    from amiga_reversing.disasm.effective_metadata import (
        _data_block_interpreted_ref_equate,
    )
    first = _data_block_interpreted_ref_equate(_ref(0x4006, 6))
    second = _data_block_interpreted_ref_equate(_ref(0x8006, 6))
    assert first and second and first.name != second.name
    assert first.value == 0x4006 and second.value == 0x8006
    assert first.address_domain == second.address_domain == "runtime"
    assert first.extent_bytes == second.extent_bytes == 1
    assert first.group == second.group == "data_block_runtime_reference_points"
    local = _data_block_interpreted_ref_equate(_ref(6, 6))
    assert local and local.address_domain is None and local.extent_bytes is None


@pytest.mark.parametrize("target", [0, 6])
@pytest.mark.c_backend
def test_real_dll_runtime_reference_renders_encoded_bytes_and_source_owned_xref(tmp_path: Path, target: int) -> None:
    from tests.test_c_backend import _requires_c_backend_dlls
    _requires_c_backend_dlls()
    encoded = 0x4000 + target
    original = bytes.fromhex("6004") + encoded.to_bytes(4, "big") + bytes.fromhex("4e75")
    binary_path = tmp_path / "pointer.bin"
    binary_path.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary_path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x4000,
        entrypoint=0x4000, code_start_offset=0, display_path=str(binary_path),
        analysis_cache_path=tmp_path / "binary.analysis")
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    _write_actions(tmp_path, _ref(encoded, target))
    with effective_metadata_file(tmp_path) as metadata_path:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        try:
            assert artifact.source_for_runtime_address(address=encoded) == {
                "status": "resolved", "runtime_address": encoded, "section_index": 0, "source_offset": target}
            assert artifact.source_for_runtime_address(address=0x5000)["status"] == "unmapped"
            row = artifact.row_for_source_offset(section_index=0, offset=2)
            assert row is not None
            ref, = [ref for ref in row["runtime_address_refs"] if ref["owner_kind"] == "data_block_interpreted_ref"]
            assert ref["runtime_address"] == encoded and ref["target_offset"] == target
            # The compact native reference query must own the target in source coordinates.
            incoming = artifact.query_payload("references", section_index=0, source_offset=target, direction="incoming")
            assert any(item.get("source_offset") == 2 and item.get("target_offset") == target
                       for item in incoming["items"])
        finally:
            artifact.close()
        rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    symbol = f"dblk_ref_h0_{target:08X}_runtime_{encoded:08X}"
    equates = [line.split() for line in rendered.splitlines() if line.split()[:1] == [symbol]]
    assert equates == [[symbol, "EQU", f"${encoded:X}"]]
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend("amiga-raw", rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original


@pytest.mark.c_backend
@pytest.mark.parametrize("overlap", [False, True])
def test_real_dll_resolver_refuses_inactive_and_ambiguous_native_views(tmp_path: Path, overlap: bool) -> None:
    from tests.test_c_backend import _requires_c_backend_dlls
    _requires_c_backend_dlls()
    path = tmp_path / "views.bin"
    path.write_bytes(bytes.fromhex("4e754e754e754e75"))
    metadata_path = tmp_path / "views.json"
    views = ([{"source_start": 0, "source_end": 8, "base_addr": 0x4000},
              {"source_start": 0, "source_end": 8, "base_addr": 0x4002}]
             if overlap else [{"source_start": 2, "source_end": 4, "base_addr": 0x4002}])
    metadata_path.write_text(json.dumps({"execution_views": views}), encoding="utf-8")
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(path), analysis_cache_path=tmp_path / "views.analysis")
    _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
        source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    try:
        analysis, _ = artifact.analysis_payload()
        native_views = analysis["sections"][0]["runtime_views"]
        assert sum(view["materialized"] for view in native_views) == (2 if overlap else 0)
        result = artifact.source_for_runtime_address(address=0x4002)
        assert result == {"status": "ambiguous" if overlap else "unmapped", "runtime_address": 0x4002}
        assert "source_offset" not in result
    finally:
        artifact.close()


@pytest.mark.c_backend
@pytest.mark.parametrize("target,label,load", [
    (6, "dialogue_resume", 0x4000),
    (8, "message_bytes", 0x4000),
    (6, None, 0x4000),
    (6, "dialogue_resume", 0x8000),
])
def test_named_fixed_runtime_pointer_uses_only_matching_original_view(
        tmp_path: Path, target: int, label: str | None, load: int) -> None:
    """A meaningful source name cannot silently rebind an explicit runtime value."""
    import subprocess
    from tests.test_c_backend import _requires_c_backend_dlls
    _requires_c_backend_dlls()
    encoded = 0x4000 + target
    original = bytes.fromhex("6004") + encoded.to_bytes(4, "big") + bytes.fromhex("4e75")
    if target == 8:
        original += b"OK\0\0"
    binary = tmp_path / "named.bin"
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=load,
        entrypoint=load, code_start_offset=0, display_path=str(binary),
        analysis_cache_path=tmp_path / "named.analysis")
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    _write_actions(tmp_path, _ref(encoded, target))
    if label:
        record = {"record": "manual_action", "action_id": "named", "sequence": 4,
            "created_at": "2026-10-25T00:00:00+00:00", "kind": "create_manual_label",
            "label": {"label_id": "target", "hunk": 0, "addr": target,
                "name": label, "scope": "global", "address_domain": "source"}}
        with (tmp_path / MANUAL_ACTION_LOG_FILE_NAME).open("a") as stream:
            stream.write(json.dumps(record) + "\n")
    with effective_metadata_file(tmp_path) as metadata:
        artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata, project_root=PROJECT_ROOT)[2]
        try:
            rendered = artifact.source_projection_with_profile()[0]
            incoming = artifact.query_payload("references", section_index=0,
                source_offset=target, direction="incoming")["items"]
            assert any(r.get("source_offset") == 2 and r.get("target_offset") == target
                       for r in incoming)
        finally:
            artifact.close()
    directive = next(line.strip() for line in rendered.splitlines() if "dc.l " in line)
    if label and load == 0x4000:
        assert directive.split(";")[0].strip() == "dc.l " + label
    else:
        assert "dblk_ref_h0_" in directive
        if label:
            assert directive.split(";")[0].strip() != "dc.l " + label
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original
    asm, output = tmp_path / "rendered.s", tmp_path / "vasm.bin"
    asm.write_text(rendered)
    subprocess.run([str(PROJECT_ROOT / "ext/vasm/vasmm68k_mot"), "-quiet", "-Fbin",
        "-m68000", "-no-opt", "-o", str(output), str(asm)], capture_output=True, check=True)
    assert output.read_bytes() == original
