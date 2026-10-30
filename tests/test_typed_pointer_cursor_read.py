"""Load the pointee of an updated record field, never the container cursor."""
import pytest
from tests.test_base_candidates import candidate_artifact
from amiga_reversing.disasm import c_backend


def metadata():
    return dict(custom_structs=[
        dict(name='Record',size=4,fields=[dict(name='packet',type='APTR',offset=0,size=4,
             value_kind='struct_pointer',pointer_struct='Header',pointer_address_domain='mapped_source')]),
        dict(name='Header',size=4,fields=[dict(name='style',type='WORD',offset=0,size=2),
                                       dict(name='first_row',type='WORD',offset=2,size=2)])],
        entry_register_seeds=[dict(hunk=0,entry_offset=0,register='A2',kind='struct_ptr',
                                  struct_name='Record',note='current record')])


@pytest.mark.parametrize('load', [
    'move.l (a2)+,d3',
    'adda.l #4,a2\n move.l -(a2),d3',
])
def test_updated_pointer_field_transports_pointee_through_data_register(tmp_path,load):
    code=load+'\n bmi.w done\n movea.l d3,a0\n move.w (a0)+,d0\n move.w (a0)+,d1\ndone:\n rts'
    with candidate_artifact(tmp_path,code,[],metadata())as(a,original):
        fields=a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert [(r['field_name'],r['field_offset']) for r in fields if r['root_struct_name']=='Header']==[
            ('style',0),('first_row',2)]
        source=a.inline_source_text_with_profile()[0]
        assert 'Header_style' in source and 'Header_first_row' in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original


@pytest.mark.parametrize('load', [
    'move.w (a2)+,d3',
    'adda.l #2,a2\n move.l (a2)+,d3',
    'move.l (a2)+,a2\n move.l a2,d3',
    'move.l (a2)+,d3\n move.w #0,d3',
    'move.l (a2)+,d3\n jsr (a5)',
])
def test_partial_overrun_shared_base_and_clobbered_pointer_do_not_promote_header(tmp_path,load):
    code=load+'\n movea.l d3,a0\n move.w (a0),d0\n rts'
    with candidate_artifact(tmp_path,code,[],metadata())as(a,_):
        fields=a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert not any(r['root_struct_name']=='Header'for r in fields)
