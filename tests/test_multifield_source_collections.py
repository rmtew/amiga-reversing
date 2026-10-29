"""Rendering fields separately must retain an evidenced native record collection."""
from contextlib import contextmanager
from copy import deepcopy
import json

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from tests.test_compact_struct_arrays import fixture


@pytest.mark.parametrize('count', [2, 3, 7])
def test_struct_and_array_presentations_retain_the_same_cross_record_accesses(tmp_path, count):
    results = []
    for kind in ['array', 'struct']:
        directory = tmp_path/kind; directory.mkdir()
        source, original, _ = fixture(directory, count=count, kind=kind, selected=34)
        with effective_metadata_file(directory) as path:
            a = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=path)[2]
        try:
            section = a.analysis_payload()[0]['sections'][0]
            results.append([(r['offset'], r['field_name']) for r in section['recovered_platform_typed_accesses']])
            assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
                a.inline_source_text_with_profile()[0])[0] == original
        finally: a.close()
    assert results[0] == results[1]
    assert [name for _, name in results[0]] == ['word_1', 'word_2', 'word_0']


@contextmanager
def mixed_records(tmp_path, *, mutation=None, pointer=False):
    instructions = ''' lea.l RECORDS(pc),a0
 move.w (a0)+,d0
 move.l (a0)+,d1
 move.b (a0)+,d2
 move.b (a0)+,d3
 move.w (a0),d4
 rts
'''
    code, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        ' RECORDS EQU $40\n SECTION code,code\n ORG 0\n' + instructions)
    original = code + bytes(64-len(code)) + bytes.fromhex('0102030405060708')*3
    binary = tmp_path/'input.bin'; binary.write_bytes(original)
    fields = [dict(name='first', type='UWORD', offset=0, size=2),
              dict(name='value', type='APTR' if pointer else 'ULONG', offset=2, size=4),
              dict(name='tag', type='UBYTE', offset=6, size=1),
              dict(name='state', type='UBYTE', offset=7, size=1)]
    if pointer: fields[1].update(value_kind='target_pointer', pointer_address_domain='mapped_source')
    entities = []
    for index in range(3):
        for f in fields:
            off = 64+8*index+f['offset']
            leaf = dict(addr=off, end=off+f['size'], hunk=0, struct_name='Record',
                field_name=f['name'], field_type=f['type'],
                unit={1:'byte',2:'word',4:'long'}[f['size']])
            if pointer and f['offset'] == 2:
                leaf.update(value_kind='target_pointer', pointer_address_domain='mapped_source')
            entities.append(leaf)
    entities[0].update(name='records', source_owner_start=64, source_owner_size=24)
    if mutation == 'missing': entities.pop(-2)
    if mutation == 'foreign':
        entities[-2]['struct_name'] = 'Foreign'
    if mutation == 'offset': entities[-2]['field_name'] = 'state'
    if mutation == 'truncated': entities[0]['source_owner_size'] = 23
    if mutation == 'crossing': entities.append(dict(addr=62,end=66,hunk=0,unit='word',name='crossing'))
    if mutation == 'domain':
        entities[5].update(pointer_address_domain='runtime_only', pointer_symbol_group='other')
    if mutation == 'alias':
        alias = deepcopy(entities[2]); alias['name'] = 'same_tag'; entities.append(alias)
    metadata = dict(target_type='program', entry_register_seeds=[], seeded_entities=entities,
        custom_structs=[dict(name='Record',size=8,fields=fields),
                       dict(name='Foreign',size=8,fields=fields)])
    path = tmp_path/'metadata.json'; path.write_text(json.dumps(metadata))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,load_address=0,entrypoint=0,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    a = c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=path)[2]
    try:
        section = a.analysis_payload()[0]['sections'][0]
        assert not a.analysis_payload()[0]['incomplete_analysis']
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
            a.inline_source_text_with_profile()[0])[0] == original
        yield section
    finally: a.close()


@pytest.mark.parametrize('pointer,mutation', [(False,None),(True,None),(False,'alias')])
def test_mixed_width_records_and_compatible_aliases_keep_the_declared_stride(tmp_path,pointer,mutation):
    with mixed_records(tmp_path,pointer=pointer,mutation=mutation) as section:
        assert [r['field_name'] for r in section['recovered_platform_typed_accesses']] == [
            'first','value','tag','state','first']
        assert not section['recovered_platform_unresolved_typed_accesses']


@pytest.mark.parametrize('mutation', ['missing','foreign','offset','truncated','crossing','domain'])
def test_incomplete_conflicting_or_mismatched_members_do_not_widen_the_first_record(tmp_path,mutation):
    with mixed_records(tmp_path,pointer=mutation=='domain',mutation=mutation) as section:
        assert len([r for r in section['recovered_platform_typed_accesses'] if r['field_name']=='first']) == 1
        assert section['recovered_platform_unresolved_typed_accesses']


@pytest.mark.parametrize('trips,conditional', [
    pytest.param(3,False,marks=pytest.mark.xfail(strict=True,reason='record cursor joins lose the array position')),
    pytest.param(3,True,marks=pytest.mark.xfail(strict=True,reason='filtered record writes require a cursor/count invariant')),
    (4,False),
])
def test_loop_transport_boundary_is_separate_from_collection_admission(tmp_path,monkeypatch,trips,conditional):
    assemble = c_backend.assemble_platform_source_text_with_c_backend
    first = True
    def loop_code(platform,text,*args,**kwargs):
        nonlocal first
        if first:
            first = False
            text = text.replace(' move.w (a0)+,d0',f' moveq.l #{trips-1},d7\nagain:\n'+
                (' tst.w d5\n beq.s skipped\n' if conditional else '')+' move.w (a0)+,d0',1)
            text = text.replace(' move.w (a0),d4',('skipped:\n' if conditional else '')+' dbf.w d7,again',1)
        return assemble(platform,text,*args,**kwargs)
    monkeypatch.setattr(c_backend,'assemble_platform_source_text_with_c_backend',loop_code)
    with mixed_records(tmp_path) as section:
        fields = [r['field_name'] for r in section['recovered_platform_typed_accesses']]
        if trips == 3:
            assert fields == ['first','value','tag','state']
        else:
            # A fourth record is outside the declared three-record owner.
            assert not fields
