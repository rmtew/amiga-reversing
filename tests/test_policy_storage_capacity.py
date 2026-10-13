"""Real native policy storage limits, including expanded array field labels."""
from __future__ import annotations

import ctypes
import json

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    HunkFileBinarySource,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_text
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
    manual_action_log_path,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_c_backend import _requires_c_backend_dlls

pytestmark = pytest.mark.c_backend


def _source(tmp_path):
    _requires_c_backend_dlls()
    dll = c_backend._platform_file_dll(PROJECT_ROOT)
    for name in ('platform_file_structured_data_item_count_capacity', 'platform_file_named_label_count_capacity'):
        if not hasattr(dll, name):
            pytest.skip('coordinated native storage-capacity build has not run yet')
        accessor = getattr(dll, name)
        accessor.argtypes = []
        accessor.restype = ctypes.c_size_t
        assert accessor() == 8192
    binary = tmp_path / 'boundary.bin'
    binary.write_bytes(bytes.fromhex('4e75') + bytes(8193))
    return RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'cache')


def _metadata(tmp_path, collection, count, duplicate=False):
    if collection == 'seeded_entities':
        items = [{'hunk': 0, 'addr': index + 2, 'end': index + 3,
                  'type': 'data', 'subtype': 'raw', 'unit': 'byte'} for index in range(count)]
    else:
        items = [{'hunk': 0, 'addr': index + 2, 'name': f'BOUND_LABEL_{index:04d}'} for index in range(count)]
        if duplicate:
            items.append(dict(items[-1]))
    path = tmp_path / 'metadata.json'
    path.write_text(json.dumps({'target_type': 'raw_binary', collection: items}), encoding='utf-8')
    return path


@pytest.mark.parametrize(('collection', 'count_field', 'output_field'), [
    ('seeded_entities', 'structured_data_item_count', 'structured_data_items'),
    ('seeded_code_labels', 'named_label_count', 'named_labels'),
])
def test_real_storage_boundary_preserves_all_8192_items(tmp_path, collection, count_field, output_field):
    source = _source(tmp_path)
    policy = c_backend.effective_policy_project_source_with_c_backend(
        source, metadata_path=_metadata(tmp_path, collection, 8192))['analysis_policy']
    assert policy[count_field] == 8192
    assert len(policy[output_field]) == 8192
    assert policy[output_field][-1]['offset'] == 8193


@pytest.mark.parametrize(('collection', 'message'), [
    ('seeded_entities', 'structured data item capacity exceeded'),
    ('seeded_code_labels', 'named label capacity exceeded'),
])
def test_real_storage_overflow_rejects_8193_without_partial_policy(tmp_path, collection, message):
    source = _source(tmp_path)
    text = _metadata(tmp_path, collection, 8193).read_text()
    with pytest.raises(ValueError, match=message + r' \(8192\)'):
        c_backend.validate_policy_storage_with_c_backend(source, metadata_text=text)


def test_real_duplicate_label_is_accepted_at_native_capacity(tmp_path):
    source = _source(tmp_path)
    policy = c_backend.effective_policy_project_source_with_c_backend(
        source, metadata_path=_metadata(tmp_path, 'seeded_code_labels', 8192, duplicate=True))['analysis_policy']
    assert policy['named_label_count'] == 8192
    assert len(policy['named_labels']) == 8192


def test_real_expanded_field_array_overflow_is_atomic_before_log_creation(tmp_path):
    source = _source(tmp_path)
    directory = tmp_path / 'target'
    directory.mkdir()
    write_target_metadata(directory, TargetMetadata(target_type='program', entry_register_seeds=()))
    count = 8193
    actions = [
        (ManualActionKind.CREATE_MANUAL_CUSTOM_STRUCT, {'custom_struct': {'name': 'Cell', 'size': 1,
            'fields': [{'name': 'value', 'type': 'byte', 'offset': 0, 'size': 1}]}}),
        (ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT, {'data_block_layout': {'layout_id': 'cells',
            'hunk': 0, 'source_start': 2, 'source_end': 2 + count, 'name': 'cells', 'default_unit': 'byte'}}),
        (ManualActionKind.SET_MANUAL_DATA_BLOCK_ELEMENT, {'data_block_element': {'data_block_element_id': 'cells:0',
            'layout_id': 'cells', 'offset': 0, 'width': count, 'kind': 'struct', 'array_count': count, 'array_stride': 1,
            'type_binding': {'type_binding_id': 'cells-type', 'layout_id': 'cells', 'element_offset': 0,
                'element_width': count, 'binding_kind': 'custom_struct', 'bound_type_id': 'Cell'}}}),
    ]
    before = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    with pytest.raises(ValueError, match=r'capacity exceeded \(8192\)'):
        append_manual_actions(directory, actions=actions, binary_source=source)
    assert not manual_action_log_path(directory).exists()
    after = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file() and p.name != '.target-history.lock'}
    assert after == before


@pytest.mark.parametrize(("collection", "message"), [
    ("seeded_entities", "structured data item capacity exceeded"),
    ("seeded_code_labels", "named label capacity exceeded"),
])
def test_object_enrichment_overflow_rejects_policy_listing_and_render(tmp_path, collection, message):
    _source(tmp_path)  # Require the coordinated native capacity build.
    path = tmp_path / "resident.hunk"
    assembly = (
        "    SECTION library,code\nresident:\n    dc.w $4AFC\n"
        "    dc.l resident\n    dc.l resident_end\n    dc.b 0,1,9,0\n"
        "    dc.l resident_name\n    dc.l resident_id\n    dc.l resident_init\n"
        'resident_name:\n    dc.b "capacity.library",0\n'
        'resident_id:\n    dc.b "capacity 1.0",0\n    EVEN\n'
        "resident_init:\n    moveq.l #0,d0\n    rts\nresident_end:\n"
    )
    c_backend.assemble_platform_source_text_with_c_backend("amiga-hunk", assembly, output_path=path)
    source = HunkFileBinarySource(kind=BinarySourceKind.HUNK_FILE, path=path,
        display_path=str(path), analysis_cache_path=tmp_path / "resident-cache")
    discovered = c_backend.effective_policy_project_source_with_c_backend(source)["analysis_policy"]
    assert discovered["structured_data_item_count"] > 0
    assert discovered["named_label_count"] > 0
    if collection == "seeded_entities":
        items = [{"hunk": 0, "addr": 0, "end": 1, "type": "data", "subtype": "raw", "unit": "byte"}] * 8192
    else:
        items = [{"hunk": 0, "addr": 0, "name": f"BOUND_LABEL_{index:04d}"} for index in range(8192)]
    metadata = tmp_path / "enrichment-metadata.json"
    metadata.write_text(json.dumps({"target_type": "program", collection: items}), encoding="utf-8")
    # Metadata alone fills the limit. Additional resident facts come from the
    # actual object; no source route may silently keep a partial enrichment.
    operations = (
        c_backend.effective_policy_project_source_with_c_backend,
        c_backend.render_project_source_with_c_backend,
        c_backend.build_listing_artifact_profile_from_binary_source,
    )
    for operation in operations:
        with pytest.raises(RuntimeError, match=message + r" \(8192\)"):
            operation(source, metadata_path=metadata)


def _reference_target(tmp_path):
    source = _source(tmp_path)
    accessor = c_backend._platform_file_dll(PROJECT_ROOT).platform_file_manual_data_reference_count_capacity
    accessor.argtypes = []
    accessor.restype = ctypes.c_size_t
    assert accessor() == 512
    source.path.write_bytes(bytes.fromhex("4e75") + bytes.fromhex("0002") * 513)
    directory = tmp_path / "reference-target"
    directory.mkdir()
    write_target_metadata(directory, TargetMetadata(target_type="program", entry_register_seeds=()))
    setup = [
        (ManualActionKind.CREATE_MANUAL_DATA_BLOCK_LAYOUT, {"data_block_layout": {"layout_id": "offsets",
            "hunk": 0, "source_start": 2, "source_end": 1028, "default_unit": "word"}}),
        (ManualActionKind.SET_MANUAL_DATA_BLOCK_ELEMENT, {"data_block_element": {"data_block_element_id": "offsets:0",
            "layout_id": "offsets", "offset": 0, "width": 1026, "kind": "array", "array_count": 513, "array_stride": 2}}),
    ]
    for name, addr in (("base_anchor", 2), ("target_anchor", 4)):
        setup.append((ManualActionKind.CREATE_MANUAL_LABEL, {"label": {
            "label_id": name, "name": name, "scope": "global", "address_domain": "source", "hunk": 0, "addr": addr}}))
    append_manual_actions(directory, actions=setup, binary_source=source)
    return directory, source


def _reference(index):
    kind, payload = target_catalog_manual_payload("target.data_block.element.interpret_ref", {
        "layout_id": "offsets", "offset": index * 2, "width": 2,
        "reference_kind": "base_displacement", "signed": True, "scale": 1,
        "base_locator": {"hunk": 0, "offset": 2}, "target_hunk": 0,
        "target_offset": 4, "source_value": 2, "xref_generation_mode": "bidirectional",
    })
    return ManualActionKind(kind), payload


@pytest.mark.parametrize("count", [244, 512])
def test_real_manual_word_references_beyond_old_limit_preserve_all_native_relations(tmp_path, count):
    directory, source = _reference_target(tmp_path)
    append_manual_actions(directory, actions=[_reference(index) for index in range(count)], binary_source=source)
    text = effective_metadata_text(directory, binary_source=source)
    assert len(json.loads(text)["manual_data_references"]) == count
    c_backend.validate_policy_storage_with_c_backend(source, metadata_text=text)
    path = tmp_path / "references-metadata.json"
    path.write_text(text)
    rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=path)
    # The plain WORD-array bulk formatter currently emits numeric values.
    # Capacity is proved by complete native relations below, without claiming
    # this independent expression-formatting gap has been fixed.
    assert c_backend.assemble_platform_source_text_with_c_backend("amiga-raw", rendered)[0] == source.path.read_bytes()
    _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=path)
    try:
        page = artifact.query_payload("references", section_index=0, source_offset=4, direction="incoming", limit=20)
        assert 0 < len(page["items"]) <= 20
        assert page["has_more"] is True
        assert page["total"] == count
        last_offset = 2 + (count - 1) * 2
        last = artifact.query_payload("references", section_index=0, source_offset=last_offset,
            direction="outgoing", limit=20)
        owned = [item for item in last["items"] if item.get("owner_kind") == "data_block_interpreted_ref"]
        assert {item["reference_role"] for item in owned} == {"base", "target"}
        assert all(item["source_offset"] == last_offset for item in owned)
    finally:
        artifact.close()


def test_real_513th_manual_word_reference_rejected_atomically_and_duplicate_allowed(tmp_path):
    directory, source = _reference_target(tmp_path)
    append_manual_actions(directory, actions=[_reference(index) for index in range(512)], binary_source=source)
    # Updating the same canonical owner at capacity must not consume another slot.
    append_manual_actions(directory, actions=[_reference(511)], binary_source=source)
    assert len(json.loads(effective_metadata_text(directory, binary_source=source))["manual_data_references"]) == 512
    before = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    with pytest.raises(ValueError, match=r"manual data reference capacity exceeded \(512\)"):
        append_manual_actions(directory, actions=[_reference(512)], binary_source=source)
    assert {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()} == before
