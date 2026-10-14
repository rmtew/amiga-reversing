"""Signed relative words retain their enclosing typed command ownership."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    ManualActionKind,
    append_manual_actions,
    build_target_identity,
    load_manual_projection,
)
from amiga_reversing.disasm.target_metadata import (
    CustomStructFieldMetadata,
    CustomStructMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    write_target_seeded_metadata,
)
from tests.test_base_displacement_data_refs import _records, _ref, _write_log


def _struct_fixture(
    target: Path, *, fields: list[tuple[str, int, int]] | None = None,
    offset: int = 6, count: int = 1, stride: int = 8, declared: bool = True,
) -> None:
    fields = fields if fields is not None else [("WORD", 0, 2), ("LONG", 2, 4), ("WORD", 6, 2)]
    struct = CustomStructMetadata(
        name="RepeatCommand", size=8,
        fields=tuple(CustomStructFieldMetadata(name=f"field_{i}", type=kind, offset=start, size=size)
                     for i, (kind, start, size) in enumerate(fields)),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED, citation="test command declaration",
    )
    write_target_seeded_metadata(target, TargetMetadata(
        target_type="program", entry_register_seeds=(), custom_structs=(struct,) if declared else (),
    ))
    ref = {**_ref(-8, base=0x100), "offset": offset}
    records = _records(ref)
    width = (count - 1) * stride + 8
    records[1]["data_block_layout"]["source_end"] = 0x100 + width
    owner = records[2]["data_block_element"]
    owner.update(width=width, kind="struct", array_count=count, array_stride=stride,
                 type_binding={"type_binding_id": "command-binding", "binding_kind": "custom_struct",
                               "bound_type_id": "RepeatCommand", "layout_id": "offsets",
                               "element_offset": 0, "element_width": width, "array_count": count})
    _write_log(target, records)


@pytest.mark.parametrize(("count", "offset"), [(1, 6), (2, 6), (2, 14)])
def test_seeded_command_word_leaf_projects_without_proxy_or_reclassification(
    tmp_path: Path, count: int, offset: int,
) -> None:
    _struct_fixture(tmp_path, count=count, offset=offset)
    # Replay has no seeded type registry; effective metadata validates the
    # deferred leaf against the complete merged declarations.
    assert len(load_manual_projection(tmp_path).data_block_interpreted_refs) == 1
    metadata = effective_target_metadata(tmp_path, include_decision_journal=False)
    assert metadata.target_equates == metadata.manual_representations == ()
    assert len(metadata.manual_data_references) == 1
    reference = metadata.manual_data_references[0]
    assert (reference.addr, reference.size, reference.source_value) == (0x100 + offset, 2, 0xFFF8)
    owner = metadata.data_block_layouts[0].elements[0]
    assert owner.kind == "struct" and owner.array_count == count
    assert owner.type_binding["bound_type_id"] == "RepeatCommand"


@pytest.mark.parametrize(("fields", "offset", "count", "stride"), [
    ([("BYTE", 6, 1), ("BYTE", 7, 1)], 6, 1, 8),
    ([("BYTE", 6, 2)], 6, 1, 8),
    ([("LONG", 4, 4)], 6, 1, 8),
    ([("LONG", 6, 2)], 6, 1, 8),
    ([("WORD", 0, 2)], 6, 1, 8),  # Padding is not a field.
    ([("WORD", 5, 2)], 5, 1, 8),  # Unaligned declaration.
    ([("WORD", 4, 2), ("WORD", 6, 2)], 5, 1, 8),  # Cross-field word.
    ([("WORD", 6, 2), ("BYTE", 6, 1)], 6, 1, 8),  # Ambiguous overlap.
    ([("WORD", 6, 2)], 6, 2, 7),  # Overlapping instances.
])
def test_merged_registry_rejects_nonword_padding_crossfield_and_ambiguous_leaves(
    tmp_path: Path, fields: list[tuple[str, int, int]], offset: int, count: int, stride: int,
) -> None:
    _struct_fixture(tmp_path, fields=fields, offset=offset, count=count, stride=stride)
    with pytest.raises(ValueError, match="exact declared WORD leaf"):
        effective_target_metadata(tmp_path, include_decision_journal=False)


def test_unresolved_struct_declaration_is_not_a_word_proof(tmp_path: Path) -> None:
    _struct_fixture(tmp_path, declared=False)
    with pytest.raises(ValueError, match="resolved type declaration"):
        effective_target_metadata(tmp_path, include_decision_journal=False)


def test_canonical_append_rejects_nonword_leaf_before_history_or_native_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _struct_fixture(tmp_path, fields=[("BYTE", 6, 2)])
    binary = tmp_path / "command.bin"
    binary.write_bytes(bytes(0x106) + bytes.fromhex("fff8"))
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY, path=binary, address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0, entrypoint=0, code_start_offset=0,
        display_path=str(binary), analysis_cache_path=tmp_path / "command.analysis",
    )
    log = tmp_path / MANUAL_ACTION_LOG_FILE_NAME
    records = [json.loads(line) for line in log.read_text().splitlines()]
    reference_action = records.pop()
    records[0]["target_identity"] = build_target_identity(source)
    _write_log(tmp_path, records)
    before = log.read_bytes()
    monkeypatch.setattr(c_backend, "validate_policy_storage_with_c_backend",
                        lambda *_args, **_kwargs: pytest.fail("invalid leaf reached native preflight"))
    with pytest.raises(ValueError, match="exact declared WORD leaf"):
        append_manual_actions(tmp_path, binary_source=source, actions=[(
            ManualActionKind.INTERPRET_MANUAL_DATA_BLOCK_ELEMENT_REF,
            {"data_block_interpreted_ref": reference_action["data_block_interpreted_ref"]},
        )])
    assert log.read_bytes() == before
