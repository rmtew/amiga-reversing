"""A canonical reference inside an array retains its own encoded span."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file, effective_target_metadata
from amiga_reversing.disasm.manual_action_catalog import _data_block_element_ref_payload
from amiga_reversing.disasm.manual_actions import MANUAL_ACTION_LOG_FILE_NAME, load_manual_projection
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def _actions(target: Path, width: int, *, bad_offset: int | None = None,
             remove: int | None = None, pointer_table: bool = False, mismatch: bool = False) -> list[dict]:
    write_target_metadata(target, TargetMetadata(target_type="program", entry_register_seeds=()))
    actions = [("create_manual_data_block_layout", "data_block_layout", {
        "layout_id": "pointers", "hunk": 0, "source_start": 2,
        "source_end": 2 + 8 * width, "role": "pointer_table" if pointer_table else "values", "default_unit": {1: "byte", 2: "word", 4: "long"}[width]}),
        ("set_manual_data_block_element", "data_block_element", {
            "layout_id": "pointers", "offset": 0, "width": 8 * width,
            "kind": "array", "array_count": 8, "array_stride": width})]
    refs = []
    for i in range(8):
        destination = 0 if i % 2 == 0 else 2 + 8 * width
        ref = _data_block_element_ref_payload([], {
            "layout_id": "pointers", "offset": i * width, "width": width,
            "reference_kind": "absolute", "target_hunk": 0, "target_offset": destination,
            "source_value": 0x40 + destination, "runtime_address": 0x40 + destination})
        if mismatch and i == 0:
            ref["target_offset"] = 2 + 8 * width
            ref["target_locator"]["offset"] = 2 + 8 * width
        if bad_offset is not None and i == 7:
            ref["offset"] = bad_offset
        refs.append(ref)
        actions.append(("interpret_manual_data_block_element_ref", "data_block_interpreted_ref", ref))
    if remove is not None:
        actions.append(("remove_manual_data_block_element_ref", "data_block_interpreted_ref", refs[remove]))
    records = [{"record": "manual_action_log_header", "version": 1, "target_identity": {}}]
    records.extend({"record": "manual_action", "action_id": f"a{i}", "sequence": i,
                    "created_at": "2026-10-18T00:00:00+00:00", "kind": kind, key: value}
                   for i, (kind, key, value) in enumerate(actions, 1))
    (target / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "\n".join(json.dumps(record) for record in records) + "\n")
    return refs


@pytest.mark.parametrize("width", [1, 2, 4])
@pytest.mark.parametrize("remove", [None, 3])
def test_each_encoded_span_projects_without_splitting_owner(tmp_path: Path, width: int,
                                                           remove: int | None) -> None:
    refs = _actions(tmp_path, width, remove=remove)
    metadata = effective_target_metadata(tmp_path)
    assert metadata is not None
    owner, = metadata.data_block_layouts[0].elements
    assert (owner.offset, owner.width, owner.array_count, owner.array_stride) == (0, 8 * width, 8, width)
    expected = [ref for i, ref in enumerate(refs) if i != remove]
    native = sorted(metadata.manual_runtime_address_refs, key=lambda ref: ref.addr)
    assert [(ref.addr, ref.size, ref.runtime_address, ref.target_offset, ref.owner_element_offset)
            for ref in native] == [(2 + ref["offset"], width, ref["source_value"], ref["target_offset"], ref["offset"])
                                   for ref in expected]
    representations = sorted(metadata.manual_representations, key=lambda rep: rep.addr)
    assert [(rep.addr, rep.end) for rep in representations] == [
        (2 + ref["offset"], 2 + ref["offset"] + width) for ref in expected]
    values = {equate.name: equate.value for equate in metadata.target_equates}
    assert [values[rep.symbol] for rep in representations] == [ref["source_value"] for ref in expected]


@pytest.mark.parametrize("bad_offset", [-1, 29, 32])
def test_outside_or_crossing_owner_ref_is_rejected(tmp_path: Path, bad_offset: int) -> None:
    _actions(tmp_path, 4, bad_offset=bad_offset)
    projection = load_manual_projection(tmp_path)
    assert projection.review_state.value == "blocked"
    assert not any(ref["offset"] == bad_offset for ref in projection.data_block_interpreted_refs)


@pytest.mark.c_backend
@pytest.mark.parametrize(("width", "pointer_table", "mismatch"), [
    (1, False, False), (2, False, False), (4, False, False), (4, True, False), (4, True, True)])
def test_native_array_renders_all_values_and_bidirectional_xrefs(tmp_path: Path, width: int, pointer_table: bool, mismatch: bool) -> None:
    from tests.test_c_backend import _requires_c_backend_dlls
    _requires_c_backend_dlls()
    refs = _actions(tmp_path, width, pointer_table=pointer_table, mismatch=mismatch)
    original = bytes([0x60, 8 * width]) + b"".join(ref["source_value"].to_bytes(width, "big") for ref in refs) + bytes.fromhex("4e75")
    path = tmp_path / "pointers.bin"
    path.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x40,
        entrypoint=0x40, code_start_offset=0, display_path=str(path),
        analysis_cache_path=tmp_path / "binary.analysis")
    with effective_metadata_file(tmp_path) as metadata_path:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        try:
            for ref in refs:
                address = 2 + ref["offset"]
                row = artifact.row_for_source_offset(section_index=0, offset=address)
                assert row is not None
                native, = [item for item in row["runtime_address_refs"]
                           if item["owner_kind"] == "data_block_interpreted_ref"
                           and item["owner_element_offset"] == ref["offset"]]
                assert native["runtime_address"] == ref["source_value"]
                assert native["target_offset"] == ref["target_offset"]
                incoming = artifact.query_payload("references", section_index=0,
                    source_offset=ref["target_offset"], direction="incoming")
                assert any(item.get("source_offset") == address for item in incoming["items"])
        finally:
            artifact.close()
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
    directive = {1: "dc.b", 2: "dc.w", 4: "dc.l"}[width]
    lines = [line.strip() for line in rendered.splitlines() if line.strip().startswith(directive + " ")]
    assert len(lines) == 8
    assert all("$" not in line.split(";", 1)[0] for line in lines)
    assert all(("dblk_ref_" not in line) == (pointer_table and not (mismatch and i == 0))
               for i, line in enumerate(lines))
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original


@pytest.mark.c_backend
def test_suppressed_discovered_copy_reference_retains_encoded_value(tmp_path: Path) -> None:
    from tests.test_c_backend import _requires_c_backend_dlls
    _requires_c_backend_dlls()
    original_source = """    SECTION section,code
    lea.l payload(pc),a0
    lea.l $10000.l,a2
    move.w #3,d0
copy_loop:
    move.b (a0)+,(a2)+
    dbf.w d0,copy_loop
    jmp $10000.l
    dcb.b 6,0
payload:
    moveq.l #7,d0
    rts
    dcb.l 8,$10000
"""
    path = tmp_path / "copy.bin"
    original, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", original_source, output_path=path, project_root=PROJECT_ROOT)
    _actions(tmp_path, 4, pointer_table=True)
    action_path = tmp_path / MANUAL_ACTION_LOG_FILE_NAME
    records = [json.loads(line) for line in action_path.read_text().splitlines()]
    records[1]["data_block_layout"].update(source_start=0x24, source_end=0x44)
    for record in records[3:]:
        record["data_block_interpreted_ref"].update(
            target_offset=0x20, target_locator={"hunk": 0, "offset": 0x20},
            source_value=0x10000, runtime_address=0x10000)
    action_path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x20000,
        entrypoint=0x20000, code_start_offset=0,
        display_path=str(path), analysis_cache_path=tmp_path / "copy.analysis")
    with effective_metadata_file(tmp_path) as metadata_path:
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        try:
            rendered, _ = artifact.inline_source_text_with_profile()
            for offset in range(0x24, 0x44, 4):
                row = artifact.row_for_source_offset(section_index=0, offset=offset)
                assert row and "dblk_ref_h0_00000020_runtime_00010000" in row["text"]
        finally:
            artifact.close()
    assert "discovered_copy suppressed" in rendered and "ORG $10000" not in rendered
    assert rendered.count("dc.l dblk_ref_h0_00000020_runtime_00010000") == 8
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", rendered, project_root=PROJECT_ROOT)
    assert rebuilt == original
