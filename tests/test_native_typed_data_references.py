"""Typed data pointers share the frozen native xref catalogue with code."""
from contextlib import contextmanager
import json

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource


@contextmanager
def pointers(tmp_path, *, domain='mapped_source', values=(0x100A, 0x100C), scalar=False,
             ambiguous=False):
    original = bytes.fromhex('4e75') + b''.join(v.to_bytes(4, 'big') for v in values) + bytes.fromhex('12345678')
    binary = tmp_path/'input.bin'; binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x1000,
        entrypoint=0x1000, code_start_offset=0, display_path=str(binary),
        analysis_cache_path=tmp_path/'analysis')
    entities = []
    for offset in (2, 6):
        entity = dict(addr=offset, end=offset+4, hunk=0, unit='long', struct_name='Reference',
            field_name='target', field_type='long', value_kind='scalar' if scalar else 'target_pointer')
        if not scalar and domain is not None:
            entity['pointer_address_domain'] = domain
        if domain == 'runtime_only': entity['pointer_symbol_group'] = 'runtime_buffers'
        entities.append(entity)
    entities += ([dict(addr=10, end=14, hunk=0, unit='word', name='target_bank')] if ambiguous else
                 [dict(addr=offset, end=offset+2, hunk=0, unit='word', name=name)
                  for offset, name in [(10, 'first_target'), (12, 'second_target')]])
    metadata = dict(target_type='program', entry_register_seeds=[], seeded_entities=entities)
    if domain == 'runtime_only':
        metadata['target_equates'] = [dict(name='runtime_buffer', value=0x100A, extent_bytes=4,
            group='runtime_buffers', address_domain='runtime')]
    if ambiguous:
        metadata['execution_views'] = [dict(source_start=start, source_end=14,
            base_addr=0x100A, runtime_view_use='pointer_target') for start in (10, 12)]
    path = tmp_path/'metadata.json'; path.write_text(json.dumps(metadata))
    artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=path)[2]
    try: yield artifact, original
    finally: artifact.close()


@pytest.mark.parametrize('domain', [None, 'mapped_source'])
def test_resolved_data_operands_are_queryable_without_rendering_or_analysis(tmp_path, domain):
    with pointers(tmp_path, domain=domain) as (a, original):
        before = a.inline_source_text_with_profile()[0]
        assert a.row_for_source_offset(section_index=0, offset=2)['pointer_resolution']['target_offset'] == 10
        a.navigation_payload = lambda: pytest.fail('navigation materialized')
        a.analysis_payload = lambda: pytest.fail('whole analysis materialized')
        refs = a.query_payload('references', source_offset=2, direction='outgoing')['items']
        assert len(refs) == 1
        ref = refs[0]
        assert (ref['source_offset'], ref['target_section_index'], ref['target_offset']) == (2, 0, 10)
        assert ref['provenance'] == 'typed_data_pointer' and ref['operand_index'] is None
        assert ref['pointer_width'] == 4 and ref['pointer_address_domain'] == (0 if domain is None else 1)
        assert a.query_payload('references', source_offset=10, direction='incoming')['items'] == refs
        assert a.query_payload('references', symbol=ref['symbol'])['items'] == refs
        assert not a.query_payload('references', section_index=99)['items']
        assert not a.query_payload('references', symbol='different_symbol')['items']
        assert a.inline_source_text_with_profile()[0] == before
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', before)[0] == original


def test_duplicate_targets_keep_distinct_sources_and_stable_pages(tmp_path):
    with pointers(tmp_path, values=(0x100A, 0x100A)) as (a, _):
        whole = a.query_payload('references', source_offset=10, direction='incoming')
        assert [r['source_offset'] for r in whole['items']] == [2, 6]
        first = a.query_payload('references', source_offset=10, direction='incoming', limit=1)
        second = a.query_payload('references', source_offset=10, direction='incoming', offset=1, limit=1)
        assert first['total'] == second['total'] == 2
        assert first['has_more'] and not second['has_more']
        assert first['items'] + second['items'] == whole['items']
        label = next(r for r in a.navigation_payload()[0]['groups']['labels']
                     if r['symbol'] == 'first_target')
        assert label['access_counts'] == {'definition': 1, 'reference': 2}


def test_data_label_navigation_and_reference_query_agree(tmp_path):
    with pointers(tmp_path) as (a, _):
        navigation = a.navigation_payload()[0]
        target = next(label for label in navigation['groups']['labels']
                      if label['symbol'] == 'first_target')
        assert target['access_counts']['reference'] == 1
        assert a.query_payload('references', symbol='first_target')['total'] == 1


@pytest.mark.parametrize('case', ['scalar', 'runtime_only', 'null', 'unmapped', 'ambiguous'])
def test_numeric_coincidence_or_unresolved_mapping_cannot_create_source_edges(tmp_path, case):
    options = {'scalar': dict(scalar=True), 'runtime_only': dict(domain='runtime_only'),
        'null': dict(values=(0, 0)), 'unmapped': dict(values=(0xDEADBEEF, 0xFFFF0000)),
        'ambiguous': dict(ambiguous=True, values=(0x100A, 0x100A))}[case]
    with pointers(tmp_path, **options) as (a, _):
        if case == 'ambiguous':
            assert a.row_for_source_offset(section_index=0, offset=2)['pointer_resolution']['reason'] == 'ambiguous_source'
        assert not a.query_payload('references', source_offset=2, direction='outgoing')['items']
        assert not a.query_payload('references', source_offset=10, direction='incoming')['items']
        labels = a.navigation_payload()[0]['groups']['labels']
        assert all(not r['access_counts'].get('reference', 0) for r in labels
                   if r['symbol'] in {'first_target', 'second_target', 'target_bank'})


def test_existing_analysis_pointer_edges_are_not_duplicated(tmp_path):
    from tests.test_static_pointer_table_cursor import header_table_artifact
    a, original = header_table_artifact(tmp_path, False)
    try:
        refs = a.query_payload('references', source_offset=len(original)-16, direction='outgoing')['items']
        assert len(refs) == 1 and refs[0]['provenance'] == 'native_data_reference'
    finally: a.close()


@pytest.mark.parametrize('mode', ['bidirectional', 'source_only', 'none'])
def test_explicit_interpretation_modes_are_not_bypassed_by_data_operands(tmp_path, mode):
    from tests.test_serialized_runtime_data_refs import _ref, _write_actions
    from amiga_reversing.disasm.effective_metadata import effective_metadata_file
    from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
    original = bytes.fromhex('6004000010064e75')
    binary = tmp_path/'input.bin'; binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x1000,
        entrypoint=0x1000, code_start_offset=0, display_path=str(binary),
        analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    ref = dict(_ref(0x1006, 6), xref_generation_mode=mode)
    _write_actions(tmp_path, ref)
    with effective_metadata_file(tmp_path) as path:
        a = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=path)[2]
    try:
        outgoing = a.query_payload('references', source_offset=2, direction='outgoing')['items']
        incoming = [r for r in a.query_payload('references', source_offset=6, direction='incoming')['items']
                    if r['source_offset'] == 2]
        assert len(outgoing) == (0 if mode == 'none' else 1)
        assert len(incoming) == (1 if mode == 'bidirectional' else 0)
    finally: a.close()
