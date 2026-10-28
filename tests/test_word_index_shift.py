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
