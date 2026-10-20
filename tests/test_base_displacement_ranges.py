"""Packed source relations keep unsigned bits, scale, and bounded ownership."""
from __future__ import annotations

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
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_base_displacement_integration import _round_trip
from tests.test_c_backend import _requires_c_backend_dlls


def _params(**updates):
    return {"layout_id": "offsets", "offset": 0, "width": 1200,
            "reference_kind": "base_displacement_range", "signed": False, "scale": 1,
            "base_locator": {"hunk": 0, "offset": 2048}, "target_hunk": 0,
            "target_offset": 2048, "source_value": 0, **updates}


@pytest.mark.parametrize("updates", [
    {"width": 1}, {"width": 3}, {"width": 131072}, {"width": True},
    {"signed": None}, {"scale": 0}, {"scale": True}, {"scale": 0x100000000},
    {"base_locator": None}, {"base_locator": {"hunk": 1, "offset": 2048}},
    {"target_offset": 2049}, {"source_value": 0x10000}, {"source_value": True},
    {"runtime_address": 0}, {"runtime_address": None},
])
def test_range_catalog_rejects_ambiguous_or_invalid_encoding(updates):
    with pytest.raises(ValueError, match="base_displacement|interpret_manual_data_block_element_ref"):
        target_catalog_manual_payload("target.data_block.element.interpret_ref", parameters=_params(**updates))


def _fixture(tmp_path, values, signed=False, scale=1, first_override=None):
    _requires_c_backend_dlls()
    start, width = 6, 2 * len(values)
    owner_start = start + width
    base = owner_start + (18 if signed else 0)
    decoded = [v - 65536 if signed and v >= 32768 else v for v in values]
    extent = max(2, max(decoded) * scale + base - owner_start + 2)
    original = bytes.fromhex("60024e714e75") + b"".join(v.to_bytes(2, "big") for v in values) + bytes(extent)
    path = tmp_path / "ranges.bin"
    path.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(path), analysis_cache_path=tmp_path / "binary.analysis")
    write_target_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    specs = [
        ("target.data_block.layout.create", {"layout_id": "offsets", "hunk": 0,
            "source_start": start, "source_end": start+width, "name": "offset_words", "default_unit": "word"}),
        ("target.data_block.element.set", {"layout_id": "offsets", "offset": 0, "width": width,
            "kind": "array", "array_count": len(values), "array_stride": 2}),
        ("target.data_block.layout.create", {"layout_id": "pixels", "hunk": 0,
            "source_start": owner_start, "source_end": len(original), "name": "pixel_bank", "default_unit": "byte"}),
        ("target.data_block.element.set", {"layout_id": "pixels", "offset": 0, "width": extent,
            "kind": "array", "array_count": extent, "array_stride": 1}),
    ]
    if scale != 1:
        specs.append(("target.code_label.add", {"hunk": 0, "addr": base+decoded[-1]*scale, "name": "last_record"}))
    actions = []
    layout_ids = {}
    for command, parameters in specs:
        requested_id = parameters.get("layout_id")
        if command.endswith("element.set"):
            parameters["layout_id"] = layout_ids[requested_id]
        kind, payload = target_catalog_manual_payload(command, parameters=parameters)
        if command.endswith("layout.create"):
            layout_ids[requested_id] = payload["data_block_layout"]["layout_id"]
        actions.append((ManualActionKind(kind), payload))
    append_manual_actions(tmp_path, actions=actions, binary_source=source)
    raw = values[0] if first_override is None else first_override
    first = raw - 65536 if signed and raw >= 32768 else raw
    kind, payload = target_catalog_manual_payload("target.data_block.element.interpret_ref", parameters=_params(
        layout_id=layout_ids["offsets"], width=width, signed=signed, scale=scale, base_locator={"hunk": 0, "offset": base},
        source_value=raw, target_offset=base+first*scale))
    return source, original, (ManualActionKind(kind), payload), base


@pytest.mark.c_backend
@pytest.mark.parametrize(("values", "signed", "scale"), [
    ([0, 0x7FFF, 0x8000, 0xFFFF] * 150, False, 1),  # More than the scalar descriptor cap.
    ([0, 1, 467, 2], False, 18),
    ([0, 1, 0xFFFF, 2], True, 18),
])
def test_native_range_decodes_all_words_and_round_trips_without_splitting_owner(tmp_path, values, signed, scale):
    source, original, action, base = _fixture(tmp_path, values, signed, scale)
    append_manual_actions(tmp_path, actions=[action], binary_source=source)
    metadata = json.loads(effective_metadata_text(tmp_path))
    assert len(metadata["manual_data_references"]) == 1
    assert metadata["manual_data_references"][0]["size"] == 2*len(values)
    assert len(metadata["data_block_layouts"]) == 2
    assert not metadata["target_equates"] and not metadata["manual_runtime_address_refs"]
    with effective_metadata_file(tmp_path) as metadata_path:
        rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(
            source, metadata_path=metadata_path, project_root=PROJECT_ROOT)
        try:
            for index in {0, 1, 2, len(values)-1}:
                refs = artifact.query_payload("references", section_index=0, source_offset=6+index*2,
                                               direction="outgoing")["items"]
                refs = [r for r in refs if r.get("owner_kind") == "data_block_interpreted_ref"]
                assert len(refs) == 2
                assert {r["reference_role"] for r in refs} == {"base", "target"}
                decoded = values[index] - 65536 if signed and values[index] >= 32768 else values[index]
                for ref in refs:
                    assert ref["reference_kind"] == "base_displacement_range"
                    assert ref["source_value"] == values[index] and ref["signed"] == signed and ref["scale"] == scale
                    assert ref["owner_element_offset"] == index*2
                    assert ref["target_offset"] == (base if ref["reference_role"] == "base" else base+decoded*scale)
                incoming = []
                page_offset = 0
                while True:
                    page = artifact.query_payload("references", section_index=0, source_offset=base+decoded*scale,
                                                  direction="incoming", limit=100, offset=page_offset)
                    incoming.extend(page["items"])
                    if not page["has_more"]:
                        break
                    page_offset += 100
                assert any(r.get("source_offset") == 6+index*2 and r.get("reference_role") == "target" for r in incoming)
        finally:
            artifact.close()
    assert "pixel_bank:" in rendered
    assert sum(line.startswith("\tdc.w ") and "pixel_bank" in line for line in rendered.splitlines()) == (len(values) if scale == 1 else 1)
    assert "/18" in rendered if scale == 18 else "/18" not in rendered
    assert "dblk_ref_" not in rendered
    assert "+$" in rendered if scale == 1 else "last_record-pixel_bank" in rendered
    _round_trip(tmp_path, rendered, original)


@pytest.mark.c_backend
def test_native_range_rejects_wrong_first_raw_bits_before_appending(tmp_path):
    source, _, action, _ = _fixture(tmp_path, [0, 1], first_override=1)
    history = (tmp_path / "manual_actions.jsonl").read_bytes()
    with pytest.raises((ValueError, RuntimeError)):
        append_manual_actions(tmp_path, actions=[action], binary_source=source)
    assert (tmp_path / "manual_actions.jsonl").read_bytes() == history


@pytest.mark.c_backend
def test_native_range_checks_later_target_before_appending(tmp_path):
    source, _, action, base = _fixture(tmp_path, [0, 1])
    ref = action[1]["data_block_interpreted_ref"]
    ref["base_locator"]["offset"] = base + 3
    ref["target_offset"] = base + 3
    ref["target_locator"]["offset"] = base + 3
    history = (tmp_path / "manual_actions.jsonl").read_bytes()
    with pytest.raises((ValueError, RuntimeError)):
        append_manual_actions(tmp_path, actions=[action], binary_source=source)
    assert (tmp_path / "manual_actions.jsonl").read_bytes() == history


@pytest.mark.parametrize("fields", [
    [("WORD", 0, 2), ("WORD", 2, 2), ("WORD", 4, 2), ("WORD", 6, 2)],
    [("WORD", 0, 2), ("LONG", 2, 4), ("WORD", 6, 2)],
    [("WORD", 0, 2), ("WORD", 2, 2), ("WORD", 6, 2)],
])
def test_range_requires_complete_declared_word_leaves(tmp_path, fields):
    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    from tests.test_base_displacement_data_refs import _write_log
    from tests.test_base_displacement_struct_fields import _struct_fixture
    _struct_fixture(tmp_path, fields=fields, offset=0, count=2)
    records = [json.loads(line) for line in (tmp_path / "manual_actions.jsonl").read_text().splitlines()]
    ref = records[-1]["data_block_interpreted_ref"]
    ref.update(_params(width=16, base_locator={"hunk": 0, "offset": 0x9000}, target_offset=0x9000))
    ref["target_locator"] = {"hunk": 0, "offset": 0x9000}
    _write_log(tmp_path, records)
    if len(fields) == 4:
        metadata = effective_target_metadata(tmp_path, include_decision_journal=False)
        assert len(metadata.manual_data_references) == 1
        assert metadata.manual_data_references[0].size == 16
        assert metadata.data_block_layouts[0].elements[0].kind == "struct"
    else:
        with pytest.raises(ValueError, match="exact declared WORD leaf"):
            effective_target_metadata(tmp_path, include_decision_journal=False)


@pytest.mark.c_backend
def test_range_duplicate_overlap_and_removal_preserve_storage(tmp_path):
    source, _, action, _ = _fixture(tmp_path, [0, 1, 2])
    append_manual_actions(tmp_path, actions=[action, action], binary_source=source)
    ref = action[1]["data_block_interpreted_ref"]
    metadata = json.loads(effective_metadata_text(tmp_path))
    assert len(metadata["manual_data_references"]) == 1
    history = (tmp_path / "manual_actions.jsonl").read_bytes()
    conflict = json.loads(json.dumps(action[1]))
    conflict["data_block_interpreted_ref"]["data_block_ref_id"] = "overlapping-range"
    with pytest.raises(ValueError, match="overlaps"):
        append_manual_actions(tmp_path, actions=[(action[0], conflict)], binary_source=source)
    assert (tmp_path / "manual_actions.jsonl").read_bytes() == history
    append_manual_actions(tmp_path, actions=[(ManualActionKind.REMOVE_MANUAL_DATA_BLOCK_ELEMENT_REF,
                                            {"data_block_interpreted_ref": ref})], binary_source=source)
    cleaned = json.loads(effective_metadata_text(tmp_path))
    assert not cleaned["manual_data_references"]
    for before, after in zip(metadata["data_block_layouts"], cleaned["data_block_layouts"], strict=True):
        assert before["source_start"] == after["source_start"] and before["source_end"] == after["source_end"]
        for old, new in zip(before["elements"], after["elements"], strict=True):
            assert {k:v for k,v in old.items() if k != "reference_interpretation"} == {k:v for k,v in new.items() if k != "reference_interpretation"}
