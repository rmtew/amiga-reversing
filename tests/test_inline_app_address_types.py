"""Addressing a declared inline object must retain its type, not load its first LONG."""
import pytest
from tests.test_base_candidates import candidate_artifact
from amiga_reversing.disasm import c_backend


def metadata(regions=None):
    return dict(custom_structs=[dict(name='Record',size=8,fields=[
        dict(name='first',type='WORD',offset=0,size=2),
        dict(name='last',type='WORD',offset=6,size=2)]),
        dict(name='Other',size=8,fields=[dict(name='different',type='WORD',offset=0,size=2)])],
        entry_register_seeds=[dict(hunk=0,entry_offset=0,register='A6',
            kind='library_base',library_name='__amiga_app_base__')])


def instance(**changes):
    return dict(dict(layout_name='app',offset=0x40,size=8,symbol='record',
                     storage_kind='struct_instance',struct_name='Record'),**changes)


def fields(a):
    return a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']


def exact(a,original):
    source=a.inline_source_text_with_profile()[0]
    assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source,
        include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')[0]==original
    return source


@pytest.mark.parametrize('transport',[
    'lea.l $40(a6),a0',
    'lea.l $40(a6),a1\n move.l a1,d1\n movea.l d1,a0',
    'lea.l $40(a6),a0\n move.l a0,-(a7)\n movea.l (a7)+,a0',
])
def test_inline_address_uses_shared_register_and_stack_value_transfers(tmp_path,transport):
    with candidate_artifact(tmp_path,transport+'\n move.w 6(a0),d0\n rts\n',
                            [instance()],metadata())as(a,original):
        assert [(r['root_struct_name'],r['field_name'])for r in fields(a)]==[('Record','last')]
        assert 'Record_last(a0)'in exact(a,original)


@pytest.mark.parametrize('mode',['pointer_cell','scalar','short','foreign','interior','endpoint','loaded_long','clobber'])
def test_inline_address_requires_exact_object_and_surviving_address_value(tmp_path,mode):
    region=instance();address=0x40
    code=None
    if mode=='pointer_cell':
        region.update(storage_kind='struct_pointer',pointer_struct='Record');region.pop('struct_name')
    elif mode=='scalar':
        region.update(storage_kind='scalar');region.pop('struct_name')
    elif mode=='short':region['size']=4
    elif mode=='foreign':region.update(layout_name='foreign',base_symbol='foreign_base')
    elif mode=='interior':address+=2
    elif mode=='endpoint':address+=8
    elif mode=='loaded_long':code='movea.l $40(a6),a0'
    elif mode=='clobber':code='lea.l $40(a6),a0\n movea.l #0,a0'
    code=code or f'lea.l ${address:x}(a6),a0'
    with candidate_artifact(tmp_path,code+'\n move.w (a0),d0\n rts\n',[region],metadata())as(a,original):
        assert not fields(a)
        exact(a,original)


@pytest.mark.parametrize('reverse',[False,True])
@pytest.mark.parametrize('same_type',[False,True])
def test_same_origin_types_join_conservatively_independent_of_declaration_order(tmp_path,reverse,same_type):
    regions=[instance(),instance(symbol='second_view',struct_name='Record'if same_type else'Other',
        **({}if same_type else dict(layout_name='phase',base_symbol='__amiga_app_base__')))]
    if reverse:regions.reverse()
    with candidate_artifact(tmp_path,'lea.l $40(a6),a0\n move.w (a0),d0\n rts\n',regions,metadata())as(a,original):
        assert [(r['root_struct_name'],r['field_name'])for r in fields(a)]==(
            [('Record','first')]if same_type else[])
        exact(a,original)


def test_larger_backing_does_not_imply_a_record_array(tmp_path):
    with candidate_artifact(tmp_path,'lea.l $40(a6),a0\n move.w 8(a0),d0\n rts\n',
                            [instance(size=16)],metadata())as(a,original):
        assert not fields(a)
        gaps=a.analysis_payload()[0]['sections'][0]['recovered_platform_unresolved_typed_accesses']
        assert any(r['root_struct_name']=='Record'and r['displacement']==8 for r in gaps)
        exact(a,original)


def test_library_header_does_not_borrow_same_numeric_app_object(tmp_path):
    extra=metadata();extra['entry_register_seeds'][0]['library_name']='timer.device'
    # Offset zero is the foreign library header, not its permitted app-extension area.
    with candidate_artifact(tmp_path,'lea.l 0(a6),a0\n move.w (a0),d0\n rts\n',
                            [instance(offset=0)],extra)as(a,original):
        assert not any(r['root_struct_name']=='Record'for r in fields(a))
        exact(a,original)


def test_explicit_custom_chip_base_cannot_borrow_app_object(tmp_path):
    with candidate_artifact(tmp_path,'lea.l $DFF000.l,a6\n lea.l $40(a6),a0\n move.w (a0),d0\n rts\n',
                            [instance()],dict(metadata(),entry_register_seeds=[]))as(a,original):
        assert not fields(a)
        exact(a,original)
