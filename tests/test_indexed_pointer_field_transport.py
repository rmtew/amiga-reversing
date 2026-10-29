"""Closed indexed pointer fields transport the declared type, never a guessed target."""
from contextlib import contextmanager

import pytest

from amiga_reversing.disasm import c_backend
from tests.test_base_candidates import candidate_artifact


@contextmanager
def pointer_array(tmp_path, code, *, padded=False, conflict=False, count=4):
    fields = [dict(name='node', type='LONG', offset=4 if padded else 0, size=4,
                   value_kind='struct_pointer', pointer_struct='Node')]
    size = 8 if padded or conflict else 4
    if padded:
        fields.insert(0, dict(name='prefix', type='LONG', offset=0, size=4))
    if conflict:
        fields.append(dict(name='other', type='LONG', offset=4, size=4,
                           value_kind='struct_pointer', pointer_struct='Other'))
    extra = dict(custom_structs=[dict(name='Node', size=4, fields=[
        dict(name='tag', type='WORD', offset=0, size=2),
        dict(name='payload', type='WORD', offset=2, size=2)]),
        dict(name='Other', size=4, fields=[dict(name='different', type='LONG', offset=0, size=4)]),
        dict(name='Reference', size=size, fields=fields)],
        entry_register_seeds=[dict(hunk=0, entry_offset=0, register='A0', kind='struct_ptr',
                                  struct_name='Reference', array_length=count,
                                  note='A bounded array of declared pointer fields')])
    with candidate_artifact(tmp_path, code, [], extra) as (artifact, original):
        analysis = artifact.analysis_payload()[0]
        assert not analysis['incomplete_analysis']
        inline = artifact.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', inline)[0] == original
        yield analysis['sections'][0]['recovered_platform_typed_accesses'], inline


@pytest.mark.parametrize('index,ea,padded', [
    ('moveq.l #0,d0', '0(a0,d0.w)', False),
    pytest.param('andi.w #3,d0\n lsl.w #2,d0', '0(a0,d0.w)', False, marks=pytest.mark.xfail(strict=True, reason='closed mask domain is solved after typed propagation')),
    pytest.param('andi.w #3,d0\n lsl.w #3,d0', '4(a0,d0.w)', True, marks=pytest.mark.xfail(strict=True, reason='closed mask domain is solved after typed propagation')),
    pytest.param('andi.w #3,d0\n lsl.w #3,d0\n addq.w #4,d0', '0(a0,d0.w)', True, marks=pytest.mark.xfail(strict=True, reason='closed mask domain is solved after typed propagation')),
    ('moveq.l #4,d0\n movea.l d0,a2', '0(a0,a2.w)', False),
    ('moveq.l #8,d0', '4(a0,d0.w)', True),
    ('moveq.l #12,d0', '0(a0,d0.w)', True),
])
def test_closed_indexed_field_reaches_later_pointee_access(tmp_path, index, ea, padded):
    with pointer_array(tmp_path, index + f'\n movea.l {ea},a1\n move.w 2(a1),d1\n rts\n',
                       padded=padded) as (accesses, inline):
        payload = [r for r in accesses if r['field_name'] == 'payload']
        assert len(payload) == 1 and payload[0]['root_struct_name'] == 'Node'
        assert payload[0]['type_provenance_kind'] == 'field_pointer'
        assert 'Node_payload(a1)' in inline


@pytest.mark.parametrize('index,load,options', [
    ('', 'movea.l 0(a0,d0.w),a1', {}),
    ('moveq.l #-4,d0', 'movea.l 0(a0,d0.w),a1', {}),
    ('moveq.l #16,d0', 'movea.l 0(a0,d0.w),a1', {}),
    ('moveq.l #2,d0', 'movea.l 0(a0,d0.w),a1', {}),
    ('moveq.l #0,d0', 'movea.w 0(a0,d0.w),a1', {}),
    ('andi.w #1,d0\n lsl.w #2,d0', 'movea.l 0(a0,d0.w),a1', {'conflict': True}),
    ('andi.w #7,d0\n lsl.w #2,d0', 'movea.l 0(a0,d0.w),a1', {}),
    ('moveq.l #0,d0\n movea.l #$1234,a0', 'movea.l 0(a0,d0.w),a1', {}),
    ('moveq.l #0,d0', 'movea.l 0(a0,d0.l),a1', {}),
])
def test_missing_bounds_conflicts_partial_reads_and_clobbers_refuse(tmp_path, index, load, options):
    with pointer_array(tmp_path, index + '\n ' + load + '\n move.w 2(a1),d1\n rts\n',
                       **options) as (accesses, inline):
        assert not [r for r in accesses if r['field_name'] == 'payload']
        assert 'Node_payload(a1)' not in inline
