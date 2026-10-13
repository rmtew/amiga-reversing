"""The normal typed-summary command preserves validated effect contracts."""
from __future__ import annotations

import copy
import json

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_metadata_text,
)
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_c_backend import _requires_c_backend_dlls


def parameters():
    return {
        "hunk": 0, "callable_kind": "direct", "entry_offset": 2,
        "inputs": [{"location": {"kind": "register", "register": "a5", "width": 4},
                    "struct_name": "Node"}],
        "results": [{"kind": "identity_input", "location": {
            "kind": "register", "register": "A5", "width": 4}, "input_index": 0}],
        "effects": {"schema_version": 1, "registers": {
            "state": "explicit", "locations": [{"location": {
                "kind": "register", "register": f"{kind}{i}", "width": 4}, "effect": "preserved"}
                for kind in ("D", "A") for i in range(8)]},
            "memory": {"state": "unknown"}, "escapes": {"state": "unknown"}},
        "note": "Normal returns preserve the input pointer; memory remains unknown.",
    }


def test_catalog_preserves_effects_results_and_note_without_aliasing_parameters():
    p = parameters()
    kind, payload = target_catalog_manual_payload("target.function_summary.add", p)
    assert kind == "create_manual_function_summary"
    summary = payload["function_summary"]
    assert summary["effects"] == p["effects"]
    assert summary["results"] == p["results"]
    assert summary["note"] == p["note"]
    p["effects"]["registers"]["locations"].clear()
    assert len(summary["effects"]["registers"]["locations"]) == 16


@pytest.mark.parametrize("bad", ["partial", "duplicate", "unknown_member", "bad_result", "bad_note"])
def test_catalog_rejects_incomplete_or_inconsistent_contracts(bad):
    p = parameters()
    if bad == "partial":
        p["effects"]["registers"]["locations"] = p["effects"]["registers"]["locations"][-3:]
    elif bad == "duplicate":
        p["effects"]["registers"]["locations"].append(copy.deepcopy(p["effects"]["registers"]["locations"][0]))
    elif bad == "unknown_member":
        p["effects"]["memory"]["effects"] = []
    elif bad == "bad_result":
        p["results"][0]["input_index"] = 1
    else:
        p["note"] = None
    with pytest.raises(ValueError, match="Invalid function summary"):
        target_catalog_manual_payload("target.function_summary.add", p)


@pytest.mark.c_backend
def test_normal_command_contract_replays_through_metadata_and_native_reader(tmp_path):
    _requires_c_backend_dlls()
    binary = tmp_path / "fixture.bin"
    binary.write_bytes(bytes.fromhex("4e754e75"))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / "cache")
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    p = parameters()
    kind, payload = target_catalog_manual_payload("target.function_summary.add", p)
    append_manual_actions(tmp_path, actions=[
        (ManualActionKind.CREATE_MANUAL_CUSTOM_STRUCT, {"custom_struct": {
            "name": "Node", "size": 4, "fields": [{"name": "value", "type": "word", "offset": 2, "size": 2}]}}),
        (ManualActionKind(kind), payload),
    ], binary_source=source)
    metadata = json.loads(effective_metadata_text(tmp_path))
    assert metadata["function_summaries"][0]["effects"] == p["effects"]
    with effective_metadata_file(tmp_path) as path:
        analysis = c_backend.analyze_project_source_with_c_backend(source, metadata_path=path)
        rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=path)
    summaries = [x for section in analysis["sections"] for x in section["function_summaries"]]
    assert len(summaries) == 1
    assert summaries[0]["effects"] == p["effects"]
    assert summaries[0]["results"] == p["results"]
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend("amiga-raw", rendered)
    assert rebuilt == binary.read_bytes()


@pytest.mark.c_backend
@pytest.mark.parametrize("array", ["registers", "memory", "escapes", "results"])
def test_native_contract_arrays_reject_a_final_nonobject_member(tmp_path, array):
    _requires_c_backend_dlls()
    binary = tmp_path / "fixture.bin"
    binary.write_bytes(bytes.fromhex("4e754e75"))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / "cache")
    _, payload = target_catalog_manual_payload("target.function_summary.add", parameters())
    summary = payload["function_summary"]
    metadata = {"target_type": "raw_binary", "function_summaries": [summary],
        "custom_structs": [{"name": "Node", "size": 4,
            "fields": [{"name": "value", "type": "word", "offset": 2, "size": 2}]}]}
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2))
    valid = c_backend.analyze_project_source_with_c_backend(source, metadata_path=path)
    assert sum(len(section["function_summaries"]) for section in valid["sections"]) == 1
    if array == "results":
        summary["results"].append(None)
    elif array == "registers":
        summary["effects"]["registers"]["locations"].append(None)
    else:
        summary["effects"][array] = {"state": "explicit", array if array == "escapes" else "effects": [None]}
    path.write_text(json.dumps(metadata, indent=2))
    with pytest.raises(RuntimeError):
        c_backend.analyze_project_source_with_c_backend(source, metadata_path=path)


@pytest.mark.c_backend
@pytest.mark.parametrize("indent", [None, 0, 2, 4, "\t"])
def test_native_contract_arrays_accept_whitespace_without_losing_members(tmp_path, indent):
    _requires_c_backend_dlls()
    binary = tmp_path / "fixture.bin"
    binary.write_bytes(bytes.fromhex("4e754e75"))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / "cache")
    p = parameters()
    p["effects"]["memory"] = {"state": "explicit", "effects": [{
        "kind": "read", "subject": {"kind": "input", "input_index": 0}}]}
    p["effects"]["escapes"] = {"state": "explicit", "escapes": [{
        "source_kind": "input", "source_location": {"kind": "register", "register": "A5", "width": 4},
        "sink_subject": {"kind": "static_storage", "section_index": 0, "offset": 0}}]}
    _, payload = target_catalog_manual_payload("target.function_summary.add", p)
    metadata = {"target_type": "raw_binary", "function_summaries": [payload["function_summary"]],
        "custom_structs": [{"name": "Node", "size": 4,
            "fields": [{"name": "value", "type": "word", "offset": 2, "size": 2}]}]}
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(metadata, indent=indent))
    analysis = c_backend.analyze_project_source_with_c_backend(source, metadata_path=path)
    summaries = [x for section in analysis["sections"] for x in section["function_summaries"]]
    assert len(summaries) == 1
    assert summaries[0]["effects"] == p["effects"]
    assert summaries[0]["results"] == p["results"]
