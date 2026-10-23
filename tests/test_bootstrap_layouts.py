"""Retained prefix-copy export contracts use canonical identity and native IR."""
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm.c_backend import build_flat_m68k_bytes_listing_artifact_profile
from amiga_reversing.disasm.memory_regions import validate_bootstrap, validate_layout
from tests.test_memory_layouts import region, layout


ORIGINAL = bytes.fromhex('4e71b3ca4e754e75')


def contract(**changes):
    return dict(schema_version=1, kind='retained_prefix_copy', contract_id='boot',
        image_region_id='image', input_sha256=hashlib.sha256(ORIGINAL).hexdigest(),
        load_address=0x20000, file_size=8, copied_source_end=8, helper_source_start=2,
        helper_source_end=6, helper_runtime_address=0x300, continuation_source_offset=6,
        comparison_source_offset=2) | changes


def metadata(moved=True, **changes):
    image = region('image', 0x10000, 8, kind='image') | {'source_domain': 'mapped_source'}
    config = layout([('image', 0x80000)] if moved else [], bootstrap_contract_id='boot',
                    bootstrap_variant='forward_disjoint' if moved else 'native')
    return dict(memory_regions=[image], memory_layouts=[config], bootstrap_contracts=[contract()],
        selected_memory_layout_id='diagnostic',
        execution_views=[dict(source_start=0, source_end=8, base_addr=0x10000),
                         dict(source_start=2, source_end=6, base_addr=0x300)]) | changes


def build(tmp_path, meta, data=ORIGINAL):
    path = tmp_path/'metadata.json'
    path.write_text(json.dumps(meta))
    return build_flat_m68k_bytes_listing_artifact_profile(data,
        display_path='bootstrap-fixture', metadata_path=path)[2]


@pytest.mark.parametrize('moved', [False, True])
def test_retained_bootstrap_native_and_variant_independent_assembly(tmp_path, moved):
    artifact = build(tmp_path, metadata(moved))
    try:
        plan = artifact.memory_layouts_payload()['items'][0]
        assert plan['bootstrap']['input_sha256'] == contract()['input_sha256']
        assert plan['bootstrap']['variant'] == ('forward_disjoint' if moved else 'native')
        assert plan['export_ready'] is False
        source = tmp_path/'bootstrap.s'
        source.write_text(artifact.inline_source_text_with_profile()[0])
        binary = tmp_path/'bootstrap.bin'
        vasm = Path(__file__).resolve().parents[1]/'tools/vasmm68k_mot.exe'
        subprocess.run([str(vasm), '-Fbin', '-m68000', '-no-opt', '-o', str(binary), str(source)],
                       capture_output=True, check=True)
        # Only the explicitly contracted register permutation differs.
        assert binary.read_bytes() == (bytes.fromhex('4e71b5c94e754e75') if moved else ORIGINAL)
    finally:
        artifact.close()


@pytest.mark.parametrize('change', [
    {'file_size': 8.5}, {'file_size': True}, {'schema_version': 1.5},
    {'helper_source_end': 3}, {'comparison_source_offset': 5},
    {'input_sha256': 'x'*64}, {'unknown': 1}, {'kind': 'strip_bootstrap'},
])
def test_bootstrap_authored_and_native_malformed_refusal(tmp_path, change):
    value = contract(**change)
    with pytest.raises(ValueError, match='bootstrap'):
        validate_bootstrap(value)
    with pytest.raises(RuntimeError, match='bootstrap contract'):
        build(tmp_path, metadata(bootstrap_contracts=[value]))


@pytest.mark.parametrize('value', [[1], [contract(), 1], [None], 'not-an-array'])
def test_native_bootstrap_array_strictness(tmp_path, value):
    with pytest.raises(RuntimeError, match='bootstrap'):
        build(tmp_path, metadata(bootstrap_contracts=value))


def test_bootstrap_wrong_input_identity_refused(tmp_path):
    with pytest.raises(RuntimeError, match='bootstrap_input_identity_mismatch'):
        build(tmp_path, metadata(bootstrap_contracts=[contract(input_sha256='0'*64)]))


def test_bootstrap_missing_views_refused(tmp_path):
    meta = metadata()
    meta['execution_views'].pop()
    with pytest.raises(RuntimeError, match='bootstrap_materialized_views_mismatch'):
        build(tmp_path, meta)


def test_bootstrap_missing_contract_refused(tmp_path):
    with pytest.raises(RuntimeError, match='unknown_bootstrap_contract'):
        build(tmp_path, metadata(bootstrap_contracts=[]))


def test_bootstrap_variant_needs_disjoint_high_destination(tmp_path):
    meta = metadata()
    meta['memory_layouts'][0]['placements'][0]['runtime_address'] = 0x20004
    with pytest.raises(RuntimeError, match='bootstrap_forward_variant_requires_disjoint_high_destination'):
        build(tmp_path, meta)


def test_bootstrap_move_needs_reviewed_variant(tmp_path):
    meta = metadata()
    meta['memory_layouts'][0]['bootstrap_variant'] = 'native'
    with pytest.raises(RuntimeError, match='bootstrap_move_requires_reviewed_direction_variant'):
        build(tmp_path, meta)


def test_bootstrap_requires_typed_address_register_pair(tmp_path):
    # A valid but unrelated instruction cannot be silently used as the variant.
    data = bytes.fromhex('4e714e714e754e75')
    meta = metadata(bootstrap_contracts=[contract(input_sha256=hashlib.sha256(data).hexdigest())])
    with pytest.raises(RuntimeError, match='bootstrap_comparison_requires_two_address_registers'):
        build(tmp_path, meta, data)


@pytest.mark.parametrize('changed,reason', [
    ({'copied_source_end': 7}, 'bootstrap_image_extent_mismatch'),
    ({'load_address': 0xffffc}, 'bootstrap_loader_or_helper_bounds'),
    ({'helper_runtime_address': 0x400}, 'bootstrap_materialized_views_mismatch'),
    ({'comparison_source_offset': 3}, 'bootstrap_comparison_not_an_admitted_instruction'),
])
def test_bootstrap_contract_bounds_refused(tmp_path, changed, reason):
    with pytest.raises(RuntimeError, match=reason):
        build(tmp_path, metadata(bootstrap_contracts=[contract(**changed)]))


def test_bootstrap_forward_variant_cannot_change_original_layout(tmp_path):
    meta = metadata(moved=False)
    meta['memory_layouts'][0]['bootstrap_variant'] = 'forward_disjoint'
    with pytest.raises(RuntimeError, match='bootstrap_forward_variant_requires_disjoint_high_destination'):
        build(tmp_path, meta)


def test_layout_bootstrap_variant_is_explicit():
    assert validate_bootstrap(contract()) == contract()
    for value in [layout(bootstrap_contract_id='boot'), layout(bootstrap_variant='native'),
                  layout(bootstrap_contract_id='boot', bootstrap_variant='strip')]:
        with pytest.raises(ValueError, match='bootstrap'):
            validate_layout(value)


def test_bootstrap_catalog_history_and_effective_projection(tmp_path):
    from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
    from amiga_reversing.disasm.effective_metadata import effective_metadata_text
    from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
    from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions, load_manual_projection
    from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
    binary = tmp_path/'original.bin'
    binary.write_bytes(ORIGINAL)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    kind, payload = target_catalog_manual_payload('target.bootstrap.add', parameters=contract())
    assert kind == 'create_manual_bootstrap_contract'
    actions = append_manual_actions(tmp_path, actions=[(ManualActionKind(kind), payload)], binary_source=source)
    assert load_manual_projection(tmp_path).bootstrap_contracts == (contract(),)
    assert json.loads(effective_metadata_text(tmp_path, binary_source=source))['bootstrap_contracts'] == [contract()]
    prefix = (tmp_path/'manual_actions.jsonl').read_bytes()
    append_manual_actions(tmp_path, actions=[(ManualActionKind.UNDO_ACTION,
        {'undoes_action_id': actions[0]['action_id']})], binary_source=source)
    assert load_manual_projection(tmp_path).bootstrap_contracts == ()
    assert (tmp_path/'manual_actions.jsonl').read_bytes().startswith(prefix)
