from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.manual_action_catalog import (
    _data_block_element_ref_parameter_schema,
    listing_catalog_manual_payload,
    listing_row_action_catalog,
    target_catalog_manual_payload,
)
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    load_manual_projection,
)
from amiga_reversing.disasm.target_metadata import (
    SuppressedSeededItemKind,
    SuppressedSeededItemMetadata,
    TargetMetadata,
    apply_suppressed_seeded_items,
    target_metadata_json_payload,
    write_target_metadata,
    write_target_seeded_metadata,
)


def _ref(displacement: int = -4, base: int = 0x9000) -> dict[str, object]:
    _, payload = target_catalog_manual_payload(
        "target.data_block.element.interpret_ref",
        parameters={
            "layout_id": "offsets", "offset": 0, "width": 2,
            "reference_kind": "base_displacement", "signed": True, "scale": 1,
            "base_locator": {"hunk": 0, "offset": base},
            "target_hunk": 0, "target_offset": base + displacement,
            "source_value": displacement & 0xFFFF,
        },
    )
    return payload["data_block_interpreted_ref"]


def _records(ref: dict[str, object]) -> list[dict[str, object]]:
    actions = [
        ("create_manual_data_block_layout", "data_block_layout", {
            "layout_id": "offsets", "hunk": 0, "source_start": 0x100,
            "source_end": 0x102, "default_unit": "word",
        }),
        ("set_manual_data_block_element", "data_block_element", {
            "layout_id": "offsets", "offset": 0, "width": 2, "kind": "scalar",
        }),
        ("interpret_manual_data_block_element_ref", "data_block_interpreted_ref", ref),
    ]
    return [{"record": "manual_action_log_header", "version": 1, "target_identity": {}}] + [
        {"record": "manual_action", "action_id": f"a{sequence}", "sequence": sequence,
         "created_at": "2026-10-13T00:00:00+00:00", "kind": kind, field: value}
        for sequence, (kind, field, value) in enumerate(actions, 1)
    ]


def _write_log(target: Path, records: list[dict[str, object]]) -> None:
    (target / MANUAL_ACTION_LOG_FILE_NAME).write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8",
    )


@pytest.mark.parametrize("displacement", [0, 4, -4, -32768, 32767])
def test_signed_word_projection_preserves_encoded_bits(tmp_path: Path, displacement: int) -> None:
    ref = _ref(displacement)
    _write_log(tmp_path, _records(ref))
    projection = load_manual_projection(tmp_path)
    assert projection.data_block_interpreted_refs[0]["source_value"] == displacement & 0xFFFF
    metadata = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert metadata is not None
    assert metadata.target_equates == metadata.manual_representations == metadata.manual_runtime_address_refs == ()
    record = metadata.manual_data_references[0]
    assert record.source_value == displacement & 0xFFFF
    assert record.base_hunk == record.target_hunk == record.hunk == 0
    assert record.base_offset == 0x9000
    assert record.target_offset == 0x9000 + displacement
    assert (record.addr, record.size, record.owner_layout_id, record.owner_element_offset) == (0x100, 2, "offsets", 0)
    payload = json.loads(json.dumps(target_metadata_json_payload(metadata)))
    assert TargetMetadata.from_dict(payload).manual_data_references == metadata.manual_data_references


@pytest.mark.parametrize("updates", [
    {"width": 1}, {"width": 4}, {"signed": False}, {"signed": None},
    {"scale": 2}, {"base_locator": None}, {"base_locator": {"hunk": 1, "offset": 0x9000}},
    {"base_locator": {"hunk": 0, "offset": -1}},
    {"target_offset": 0x1234}, {"source_value": -4}, {"source_value": 0x10000},
    {"runtime_address": 0xFFFC}, {"runtime_address": None}, {"scale": True},
    {"source_value": True}, {"width": True},
    {"base_locator": {"hunk": 0x100000000, "offset": 0x9000}},
    {"base_locator": {"hunk": 0, "offset": 0x100000000}},
    {"base_locator": {"hunk": True, "offset": 0x9000}},
])
def test_replay_rejects_unsupported_relative_forms(tmp_path: Path, updates: dict[str, object]) -> None:
    ref = {**_ref(), **updates}
    if "target_offset" in updates:
        ref["target_locator"] = {"hunk": 0, "offset": updates["target_offset"]}
    _write_log(tmp_path, _records(ref))
    projection = load_manual_projection(tmp_path)
    assert projection.review_state.value == "blocked"
    assert projection.data_block_interpreted_refs == ()


def test_replay_rejects_cross_section_source(tmp_path: Path) -> None:
    records = _records(_ref())
    records[1]["data_block_layout"]["hunk"] = 1
    _write_log(tmp_path, records)
    projection = load_manual_projection(tmp_path)
    assert projection.review_state.value == "blocked"
    assert "same section" in str(projection.diagnostics)


@pytest.mark.parametrize("displacement", [-32769, 32768])
def test_catalog_rejects_signed_word_overflow(displacement: int) -> None:
    with pytest.raises(ValueError, match="signed source_value"):
        _ref(displacement)


def test_listing_bytes_and_removal_preserve_base_identity() -> None:
    ref = _ref()
    row = {
        "kind": "data", "section_index": 0, "start_offset": 0x100, "end_offset": 0x102,
        "bytes": "FFFC", "active_data_block_layout": {
            "layout_id": "offsets", "hunk": 0, "source_start": 0x100, "source_end": 0x102,
        }, "active_data_block_interpreted_ref": ref,
    }
    _, payload = listing_catalog_manual_payload(
        row, "row.data_block.element.interpret_ref", parameters=ref,
    )
    assert payload["data_block_interpreted_ref"] == ref
    _, removal = listing_catalog_manual_payload(row, "row.data_block.element.clear_ref")
    assert removal["data_block_interpreted_ref"] == ref
    clear = next(action for action in listing_row_action_catalog(row) if action["action_id"] == "row.data_block.element.clear_ref")
    assert clear["parameters"]["base_locator"] == ref["base_locator"]
    schema = _data_block_element_ref_parameter_schema()
    assert "base_displacement" in schema["properties"]["reference_kind"]["enum"]
    assert "base_locator" in schema["properties"]


@pytest.mark.parametrize(("kind", "field", "identity"), [
    ("remove_manual_data_block_element_ref", "data_block_interpreted_ref", {"layout_id": "offsets", "offset": 0}),
    ("remove_manual_data_block_element", "data_block_element", {"layout_id": "offsets", "offset": 0}),
    ("remove_manual_data_block_layout", "data_block_layout", {"layout_id": "offsets"}),
])
def test_owner_cleanup_removes_projected_and_existing_references(
    tmp_path: Path, kind: str, field: str, identity: dict[str, object],
) -> None:
    ref = _ref()
    records = _records(ref)
    _write_log(tmp_path, records)
    metadata = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert metadata is not None and len(metadata.manual_data_references) == 1
    write_target_metadata(tmp_path, metadata)
    if field == "data_block_interpreted_ref":
        identity = {**identity, "data_block_ref_id": ref["data_block_ref_id"]}
    records.append({"record": "manual_action", "action_id": "a4", "sequence": 4,
                    "created_at": "2026-10-13T00:00:00+00:00", "kind": kind, field: identity})
    _write_log(tmp_path, records)
    cleaned = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert cleaned is not None
    assert cleaned.manual_data_references == ()


@pytest.mark.parametrize("mode", ["bidirectional", "source_only", "none"])
def test_projection_preserves_xref_mode(tmp_path: Path, mode: str) -> None:
    _write_log(tmp_path, _records({**_ref(), "xref_generation_mode": mode}))
    metadata = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert metadata.manual_data_references[0].xref_generation_mode == mode


def test_old_metadata_defaults_to_empty_data_references() -> None:
    payload = json.loads(json.dumps(target_metadata_json_payload(TargetMetadata(target_type="program", entry_register_seeds=()))))
    payload.pop("manual_data_references")
    assert TargetMetadata.from_dict(payload).manual_data_references == ()


def test_relative_reference_survives_metadata_merge_and_suppression(tmp_path: Path) -> None:
    _write_log(tmp_path, _records(_ref()))
    metadata = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert metadata is not None
    write_target_metadata(tmp_path, metadata)
    write_target_seeded_metadata(tmp_path, TargetMetadata(target_type="program", entry_register_seeds=()))
    merged = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert merged.manual_data_references == metadata.manual_data_references
    suppressed = apply_suppressed_seeded_items(metadata, (
        SuppressedSeededItemMetadata(kind=SuppressedSeededItemKind.SEEDED_ENTITY, hunk=0, addr=0xDEAD),
    ))
    assert suppressed.manual_data_references == metadata.manual_data_references


@pytest.mark.parametrize("source_start", [0xFFFFFFFE, 0x100000000])
def test_replay_rejects_source_span_overflow(tmp_path: Path, source_start: int) -> None:
    records = _records(_ref())
    records[1]["data_block_layout"].update(source_start=source_start, source_end=source_start + 2)
    _write_log(tmp_path, records)
    projection = load_manual_projection(tmp_path)
    assert projection.review_state.value == "blocked"
    assert "32-bit section span" in str(projection.diagnostics)


@pytest.mark.parametrize("updates", [
    {"scale": True}, {"scale": 2}, {"signed": False}, {"width": 4},
    {"base_locator": None}, {"source_value": 0x10000},
    {"runtime_address": None},
    {"base_locator": {"hunk": 1, "offset": 0x9000}},
    {"base_locator": {"hunk": 0, "offset": 0x100000000}},
])
def test_catalog_rejects_unsupported_relative_forms(updates: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="base_displacement|interpret_manual_data_block_element_ref"):
        target_catalog_manual_payload(
            "target.data_block.element.interpret_ref", parameters={**_ref(), **updates},
        )


def test_replay_rejects_noncanonical_target_locator(tmp_path: Path) -> None:
    _write_log(tmp_path, _records({**_ref(), "target_locator": {"hunk": False, "offset": 0x8FFC}}))
    projection = load_manual_projection(tmp_path)
    assert projection.review_state.value == "blocked"


@pytest.mark.parametrize("offset", [0, 2])
def test_replay_rejects_sub_element_relative_references(tmp_path: Path, offset: int) -> None:
    records = _records({**_ref(), "offset": offset})
    records[1]["data_block_layout"]["source_end"] = 0x104
    records[2]["data_block_element"]["width"] = 4
    _write_log(tmp_path, records)
    projection = load_manual_projection(tmp_path)
    assert projection.review_state.value == "blocked"
    assert "aligned word-array entry" in str(projection.diagnostics)


def test_relative_to_absolute_reinterpretation_cleans_persisted_reference(tmp_path: Path) -> None:
    records = _records(_ref())
    _write_log(tmp_path, records)
    metadata = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert metadata is not None
    write_target_metadata(tmp_path, metadata)
    _, payload = target_catalog_manual_payload(
        "target.data_block.element.interpret_ref", parameters={
            "layout_id": "offsets", "offset": 0, "width": 2,
            "data_block_ref_id": _ref()["data_block_ref_id"],
            "reference_kind": "absolute", "source_value": 0xFFFC,
            "target_hunk": 0, "target_offset": 0xFFFC,
        },
    )
    records.append({"record": "manual_action", "action_id": "a4", "sequence": 4,
                    "created_at": "2026-10-13T00:00:00+00:00",
                    "kind": "interpret_manual_data_block_element_ref", **payload})
    _write_log(tmp_path, records)
    reinterpreted = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert reinterpreted.manual_data_references == ()
    assert len(reinterpreted.target_equates) == 1
    assert len(reinterpreted.manual_runtime_address_refs) == 1



def test_array_projects_each_contained_relative_word_and_cleans_owner(tmp_path: Path) -> None:
    records = _records(_ref())
    records[1]["data_block_layout"]["source_end"] = 0x10C
    records[2]["data_block_element"].update(width=12, kind="array", array_count=6, array_stride=2)
    for offset in range(2, 12, 2):
        ref = {**_ref(), "offset": offset, "data_block_ref_id": f"offsets:{offset}:relative"}
        records.append({"record": "manual_action", "action_id": f"a{offset+3}", "sequence": len(records),
                        "created_at": "2026-10-13T00:00:00+00:00", "kind": "interpret_manual_data_block_element_ref",
                        "data_block_interpreted_ref": ref})
    _write_log(tmp_path, records)
    metadata = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert [ref.addr for ref in metadata.manual_data_references] == list(range(0x100, 0x10C, 2))
    assert len(metadata.data_block_layouts[0].elements) == 1
    assert metadata.data_block_layouts[0].elements[0].width == 12
    write_target_metadata(tmp_path, metadata)
    records.append({"record": "manual_action", "action_id": "remove", "sequence": len(records),
                    "created_at": "2026-10-13T00:00:00+00:00", "kind": "remove_manual_data_block_element",
                    "data_block_element": {"layout_id": "offsets", "offset": 0}})
    _write_log(tmp_path, records)
    assert effective_target_metadata(tmp_path, include_decision_journal=False).manual_data_references == ()



def test_absolute_to_relative_reinterpretation_cleans_derived_absolute_facts(tmp_path: Path) -> None:
    _, payload = target_catalog_manual_payload(
        "target.data_block.element.interpret_ref", parameters={
            "layout_id": "offsets", "offset": 0, "width": 2,
            "reference_kind": "absolute", "source_value": 0xFFFC,
            "target_hunk": 0, "target_offset": 0xFFFC,
        },
    )
    records = _records(payload["data_block_interpreted_ref"])
    _write_log(tmp_path, records)
    metadata = effective_target_metadata(tmp_path, include_decision_journal=False)
    write_target_metadata(tmp_path, metadata)
    records.append({"record": "manual_action", "action_id": "a4", "sequence": 4,
                    "created_at": "2026-10-13T00:00:00+00:00",
                    "kind": "interpret_manual_data_block_element_ref", "data_block_interpreted_ref": {**_ref(), "data_block_ref_id": payload["data_block_interpreted_ref"]["data_block_ref_id"]}})
    _write_log(tmp_path, records)
    reinterpreted = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert reinterpreted.target_equates == reinterpreted.manual_runtime_address_refs == reinterpreted.manual_representations == ()
    assert len(reinterpreted.manual_data_references) == 1



@pytest.mark.parametrize(("stride", "offset"), [(1, 0), (4, 0), (2, 1)])
def test_replay_rejects_non_word_array_entries(tmp_path: Path, stride: int, offset: int) -> None:
    records = _records({**_ref(), "offset": offset})
    records[1]["data_block_layout"]["source_end"] = 0x10C
    records[2]["data_block_element"].update(width=12, kind="array", array_count=6, array_stride=stride)
    _write_log(tmp_path, records)
    projection = load_manual_projection(tmp_path)
    assert projection.review_state.value == "blocked"



@pytest.mark.parametrize("absolute_first", [True, False])
@pytest.mark.parametrize("mode", ["none", "bidirectional"])
def test_replay_rejects_different_owner_overlap_across_reference_kinds(
    tmp_path: Path, absolute_first: bool, mode: str,
) -> None:
    relative = {**_ref(4, 8), "xref_generation_mode": mode}
    absolute = {
        **relative, "data_block_ref_id": "absolute-owner", "reference_kind": "absolute",
        "target_hunk": 0, "target_offset": 4, "target_locator": {"hunk": 0, "offset": 4},
    }
    first, second = (absolute, relative) if absolute_first else (relative, absolute)
    records = _records(first)
    records.append({"record": "manual_action", "action_id": "a4", "sequence": 4,
                    "created_at": "2026-10-13T00:00:00+00:00",
                    "kind": "interpret_manual_data_block_element_ref", "data_block_interpreted_ref": second})
    _write_log(tmp_path, records)
    projection = load_manual_projection(tmp_path)
    assert projection.review_state.value == "blocked"
    assert projection.data_block_interpreted_refs == ()
    assert "different interpreted-reference owner" in str(projection.diagnostics)


def test_replay_keeps_absolute_absolute_history_compatible(tmp_path: Path) -> None:
    absolute = {**_ref(4, 8), "reference_kind": "absolute", "target_offset": 4,
                "target_locator": {"hunk": 0, "offset": 4}}
    records = _records(absolute)
    records.append({"record": "manual_action", "action_id": "a4", "sequence": 4,
                    "created_at": "2026-10-13T00:00:00+00:00",
                    "kind": "interpret_manual_data_block_element_ref",
                    "data_block_interpreted_ref": {**absolute, "data_block_ref_id": "second-absolute"}})
    _write_log(tmp_path, records)
    projection = load_manual_projection(tmp_path)
    assert projection.review_state.value == "clear"
    assert len(projection.data_block_interpreted_refs) == 2
