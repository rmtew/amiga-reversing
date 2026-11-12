"""Indexed field display uses explicit scalar origins, never equal-number guesses.

The live index and exact displacement encoding remain unchanged. Unsupported
origins retain the raw operand with a separate resolved-field annotation.
"""
import struct
import subprocess

import pytest

from amiga_reversing.disasm import c_backend
from tests.test_base_candidates import candidate_artifact


CASES = [
    ('literal', 'origin: move.w #4,d0\n', [('origin', 'FIELD_INDEX', 4)], 'd0', True),
    ('copy', 'origin: move.w #4,d0\n move.w d0,d2\n nop\n', [('origin', 'FIELD_INDEX', 4)], 'd2', True),
    ('equality', 'origin: cmp.w #4,d0\n beq.s use\n rts\n', [('origin', 'FIELD_INDEX', 4)], 'd0', True),
    ('fallthrough', 'origin: cmp.w #4,d0\n bne.s outside\n bra.s use\noutside: rts\n', [('origin', 'FIELD_INDEX', 4)], 'd0', True),
    ('equality_copy', 'origin: cmp.w #4,d0\n beq.s inside\n rts\ninside: move.l d0,d2\n', [('origin', 'FIELD_INDEX', 4)], 'd2', True),
    ('equal_number_only', 'move.w #4,d0\n', [], 'd0', False),
    ('modified', 'origin: move.w #4,d0\n addq.w #1,d0\n subq.w #1,d0\n', [('origin', 'FIELD_INDEX', 4)], 'd0', False),
    ('byte_assignment', 'origin: move.w #4,d0\n move.b #4,d0\n', [('origin', 'FIELD_INDEX', 4)], 'd0', False),
    ('two_names', 'tst.w d7\n beq.s other\norigin: move.w #4,d0\n bra.s use\nother: move.w #4,d0\n', [('origin', 'FIELD_INDEX', 4), ('other', 'OTHER_INDEX', 4)], 'd0', False),
    ('unrepresented_join', 'tst.w d7\n beq.s other\norigin: move.w #4,d0\n bra.s use\nother: move.w #4,d0\n', [('origin', 'FIELD_INDEX', 4)], 'd0', False),
    ('same_identity_join', 'tst.w d7\n beq.s other\norigin: move.w #4,d0\n bra.s use\nother: move.w #4,d0\n', [('origin', 'FIELD_INDEX', 4), ('other', 'FIELD_INDEX', 4)], 'd0', True),
    ('address_equate', 'origin: move.w #4,d0\n', [('origin', 'FIELD_INDEX', 4)], 'd0', False),
]


def metadata(code, origins, *, address=False, field=4):
    labels = [label for label, _, _ in origins]
    if labels:
        raw = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
            ' SECTION code,code\n ORG 0\n'+code+'\n dc.l '+','.join(labels)+'\n')[0]
        offsets = struct.unpack('>'+'I'*len(labels), raw[-4*len(labels):])
    else: offsets = []
    return dict(custom_structs=[dict(name='IndexedCounts', size=16, fields=[
            dict(name='count', offset=field, size=4, type='LONG')])],
        entry_register_seeds=[dict(hunk=0, entry_offset=0, register='A0', kind='struct_ptr',
            struct_name='IndexedCounts', note='Explicit input record')],
        target_equates=[dict(name=name, value=value, **({'address_domain':'runtime','extent_bytes':1,'group':'fixture'} if address else {}))
            for name,value in dict((n,v) for _,n,v in origins).items()]
            or [dict(name='UNRELATED_FOUR', value=4)],
        manual_representations=[dict(hunk=0, addr=offset, end=offset+4, style='symbol',
            element_kind='immediate', operand_index=0, width_bytes=2, symbol=name, value=value)
            for (_,name,value),offset in zip(origins, offsets)])


def exact(artifact, original, tmp_path):
    source = artifact.inline_source_text_with_profile()[0]
    assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    path, out = tmp_path/'output.s', tmp_path/'output.raw'; path.write_text(source)
    result = subprocess.run([str(c_backend.PROJECT_ROOT/'tools/vasmm68k_mot.exe'), '-quiet',
        '-m68000', '-no-opt', '-Fbin', '-o', str(out), str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    assert out.read_bytes() == original
    return source


@pytest.mark.parametrize('case,prefix,origins,index,symbolic', CASES, ids=[c[0] for c in CASES])
def test_scalar_origin_compensation_and_conservative_display(tmp_path,case,prefix,origins,index,symbolic):
    code = prefix+f'use: move.b 0(a0,{index}.w),d5\n rts\n'
    with candidate_artifact(tmp_path, code, [], metadata(code,origins,address=case=='address_equate')) as (a, original):
        p = a.analysis_payload()[0]; assert not p['incomplete_analysis']
        refs = p['sections'][0]['recovered_platform_typed_accesses']
        # A BYTE literal preserves the proven zero upper byte, but replaces
        # scalar display provenance. The numeric proof does not revive FIELD_INDEX.
        assert len(refs) == 1 and refs[0]['word_index']['byte_offsets'] == [4]
        assert refs[0]['word_index']['encoded_symbol_correction'] == -4
        source = exact(a,original,tmp_path)
        assert ('IndexedCounts_count-FIELD_INDEX(a0,'+index+'.w)' in source) == symbolic
        if not symbolic and refs:
            assert f'$0(a0,{index}.w)' in source
            assert 'operand 1: IndexedCounts_count; live '+index+' index, original displacement 0' in source
            assert 'IndexedCounts_count-4(a0,' not in source


@pytest.mark.parametrize('value,displacement,field', [(-4,8,4),(4,0,4),(65532,8,4)])
def test_signed_word_contribution_must_equal_symbol_value(tmp_path,value,displacement,field):
    code = f'origin: move.w #{value},d0\nuse: move.b {displacement}(a0,d0.w),d5\n rts\n'
    with candidate_artifact(tmp_path,code,[],metadata(code,[('origin','FIELD_INDEX',value)],field=field)) as (a, original):
        source = exact(a,original,tmp_path)
        assert ('IndexedCounts_count-FIELD_INDEX(a0,d0.w)' in source) == (value != 65532)
        assert a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses'][0]['word_index']['byte_offsets'] == ([-4] if value!=4 else [4])


@pytest.mark.parametrize('clobber', ['move.w d7,d0', 'jsr (a2)', 'move.w d7,(a0)\n move.w (a0),d0'])
def test_unknown_index_and_call_never_gain_symbolic_or_field_proof(tmp_path,clobber):
    code = 'origin: move.w #4,d0\n'+clobber+'\nuse: move.b 0(a0,d0.w),d5\n rts\n'
    with candidate_artifact(tmp_path,code,[],metadata(code,[('origin','FIELD_INDEX',4)])) as (a, original):
        assert not a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert 'IndexedCounts_count-FIELD_INDEX(a0,d0.w)' not in exact(a,original,tmp_path)


@pytest.mark.parametrize('setup,index,offsets', [
    ('movea.l #4,a2\n', 'a2', [4]),
    ('andi.w #16,d0\n addq.w #4,d0\n', 'd0', [4,20]),
])
def test_address_index_and_multi_element_domains_keep_raw_encoding_and_field_annotation(tmp_path,setup,index,offsets):
    code = setup+f'use: move.b 0(a0,{index}.w),d5\n rts\n'
    extra = metadata(code, [])
    extra['entry_register_seeds'][0]['array_length'] = 2
    with candidate_artifact(tmp_path,code,[],extra) as (a, original):
        refs = a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert len(refs) == 1 and refs[0]['word_index']['byte_offsets'] == offsets
        source = exact(a,original,tmp_path)
        assert f'$0(a0,{index}.w)' in source
        assert f'operand 1: IndexedCounts_count; live {index} index, original displacement 0' in source
        assert '-UNRELATED_FOUR' not in source


@pytest.mark.parametrize('value,displacement', [(4,0),(-4,8)])
def test_moveq_symbol_obeys_signed_word_index_contribution(tmp_path,value,displacement):
    code = f'origin: moveq #{value},d0\nuse: move.b {displacement}(a0,d0.w),d5\n rts\n'
    extra = metadata(code,[('origin','FIELD_INDEX',value)])
    extra['manual_representations'][0].update(end=2,width_bytes=1)
    with candidate_artifact(tmp_path,code,[],extra) as (a, original):
        source = exact(a,original,tmp_path)
        assert 'IndexedCounts_count-FIELD_INDEX(a0,d0.w)' in source
        assert a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses'][0]['word_index']['byte_offsets']==[value]
