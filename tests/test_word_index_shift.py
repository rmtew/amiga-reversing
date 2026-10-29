"""Generated zero-fill left-shift metadata serves scalar indexed type recovery."""
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


@pytest.mark.parametrize('setup,operation,expected', [
    ('move.w #1,d0', 'asl.w #2,d0', True),
    ('move.w #1,d0', 'lsl.w #2,d0', True),
    ('move.w #$4001,d0', 'asl.w #2,d0', True),  # WORD truncation, not saturating arithmetic
    ('move.w #1,d0\n move.w #2,d1', 'asl.w d1,d0', True),
    ('move.w #1,d0\n move.w #2,d1', 'lsl.w d1,d0', True),
    ('move.w #1,d0', 'asl.b #2,d0', False),
    ('move.w #1,d0', 'asl.l #2,d0', False),  # existing WORD-domain scope
    ('move.w #1,d0', 'asr.w #2,d0', False),
    ('move.w #1,d0', 'rol.w #2,d0', False),
    ('move.w #1,d0', 'roxl.w #2,d0', False),
    ('move.w #1,d0\n move.w #16,d1', 'asl.w d1,d0', False),
    ('move.w #1,d0', 'asl.w d1,d0', False),
    ('move.w d1,d0', 'asl.w #2,d0', False),
    ('move.w #$7FFF,d0', 'asl.w #1,d0', False),  # signed index -2 is outside prefix
    ('move.w #1,d0', 'asl.w #2,d0\n move.b d1,d0', False),
    ('move.w #1,d0', 'asl.w #2,d0\n jsr (a2)', False),
    ('andi.w #1,d0', 'add.w d0,d0\n add.w d0,d0', True),
    ('andi.w #16384,d0', 'add.w d0,d0\n add.w d0,d0', True),
    ('andi.w #15,d0', 'add.w d0,d0\n add.w d0,d0', False),
    ('move.w d1,d0', 'sub.w d0,d0', True),
    ('move.w d1,d0', 'sub.w d0,d0\n move.b d1,d0', False),
    ('andi.w #1,d0\n andi.w #1,d1', 'sub.w d1,d0\n lsl.w #2,d0', False),
])
def test_word_index_shift_is_shared_and_conservative(tmp_path, setup, operation, expected):
    binary = tmp_path/'input.bin'
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        f' SECTION code,code\n ORG 0\n {setup}\n {operation}\n move.l 0(a0,d0.w),d2\n rts\n',
        output_path=binary)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,load_address=0,entrypoint=0,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    commands=[('target.custom_struct.add',dict(name='Slot',size=4,
        fields=[dict(name='value',type='LONG',offset=0,size=4)])),
        ('target.code.register_seed.add',dict(hunk=0,addr=0,register='A0',struct_name='Slot',array_length=2))]
    actions=[]
    for command,params in commands:
        kind,payload=target_catalog_manual_payload(command,params)
        actions.append((ManualActionKind(kind),payload))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as md:
        a=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=md)[2]
    try:
        analysis=a.analysis_payload()[0]
        accesses=[r for r in analysis['sections'][0]['recovered_platform_typed_accesses']
                  if r['base_register']=='A0' and r['field_expr']=='Slot_value']
        assert bool(accesses)==expected
        assert not analysis['incomplete_analysis']
        rendered=a.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',rendered)[0]==original
    finally:
        a.close()


@pytest.mark.parametrize('index_width,expected',[('w',True),('l',False)])
def test_same_word_subtraction_does_not_zero_extend_unknown_upper_bits(tmp_path,index_width,expected):
    from tests.test_base_candidates import candidate_artifact
    extra=dict(custom_structs=[dict(name='Slot',size=4,fields=[
        dict(name='value',type='LONG',offset=0,size=4)])],
        entry_register_seeds=[dict(hunk=0,entry_offset=0,register='A0',
            kind='struct_ptr',struct_name='Slot',array_length=8,note='Array input')])
    with candidate_artifact(tmp_path,
        f'sub.w d0,d0\n move.l 0(a0,d0.{index_width}),d2\n rts\n',[],extra)as(a,original):
        analysis=a.analysis_payload()[0]
        assert bool(analysis['sections'][0]['recovered_platform_typed_accesses'])==expected
        assert not analysis['incomplete_analysis']
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


def test_self_doubling_keeps_all_eight_values_without_increasing_the_limit(tmp_path):
    from tests.test_base_candidates import candidate_artifact
    extra=dict(custom_structs=[dict(name='Slot',size=4,fields=[
        dict(name='value',type='LONG',offset=0,size=4)])],
        entry_register_seeds=[dict(hunk=0,entry_offset=0,register='A0',
            kind='struct_ptr',struct_name='Slot',array_length=8,note='Array input')])
    with candidate_artifact(tmp_path,
        'andi.w #7,d0\n add.w d0,d0\n add.w d0,d0\n move.l 0(a0,d0.w),d2\n rts\n',[],extra)as(a,original):
        analysis=a.analysis_payload()[0]
        assert any(r['field_name']=='value'for r in analysis['sections'][0]['recovered_platform_typed_accesses'])
        assert not analysis['incomplete_analysis']
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


def test_closed_index_set_cannot_name_one_of_two_different_fields(tmp_path):
    from tests.test_base_candidates import candidate_artifact
    extra=dict(custom_structs=[dict(name='Pair',size=4,fields=[
        dict(name='left',type='WORD',offset=0,size=2),
        dict(name='right',type='WORD',offset=2,size=2)])],
        entry_register_seeds=[dict(hunk=0,entry_offset=0,register='A0',
            kind='struct_ptr',struct_name='Pair',note='Pair input')])
    with candidate_artifact(tmp_path,
        'andi.w #1,d0\n add.w d0,d0\n move.w 0(a0,d0.w),d2\n rts\n',[],extra)as(a,original):
        analysis=a.analysis_payload()[0]
        assert not analysis['sections'][0]['recovered_platform_typed_accesses']
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
