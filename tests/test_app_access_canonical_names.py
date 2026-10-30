"""Native access names project existing operand bindings, never new base proof."""
import pytest
from tests.test_base_candidates import candidate_artifact
from tests.test_absolute_layout_base import slot
from amiga_reversing.disasm import c_backend


def region(**changes):
    result=dict(layout_name='app',offset=0x100,size=2,symbol='decoded_style',storage_kind='scalar')
    result.update(changes)
    return result


@pytest.mark.parametrize('code,extra,evidence',[
    ('move.w $100(a6),d0\n rts',{},'declared_layout_a6_fallback'),
    ('move.w d0,$100(a6)\n rts',{},'declared_layout_a6_fallback'),
    ('move.b $100(a6),d0\n rts',{},'declared_layout_a6_fallback'),
    ('movea.l $1800.l,a0\n move.w $100(a0),d0\n rts',
        dict(absolute_storage_slots=[slot()]),'register_state'),
])
def test_access_and_listing_keep_the_declared_exact_slot_name(tmp_path,code,extra,evidence):
    with candidate_artifact(tmp_path,code,[region()],extra)as(a,original):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=p['sections'][0]['app_slot_refs'];assert len(refs)==1
        assert refs[0]['symbol_name']=='decoded_style'
        assert refs[0]['base_evidence']==evidence
        row=a.row_for_source_offset(section_index=0,offset=refs[0]['offset'])
        assert row['app_slot_refs'][0]['symbol']=='decoded_style'
        source=a.inline_source_text_with_profile()[0]
        assert 'decoded_style(a'in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original


def test_interior_access_does_not_gain_an_incorrect_base_only_name(tmp_path):
    owner=region();owner.update(size=4,symbol='whole_record')
    with candidate_artifact(tmp_path,'move.w $102(a6),d0\n rts',[owner])as(a,original):
        refs=a.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert refs[0]['displacement']==0x102
        assert refs[0]['symbol_name']=='app_0102'
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original


def test_names_do_not_recreate_a_contradicted_hardware_base(tmp_path):
    with candidate_artifact(tmp_path,'lea.l $dff000.l,a6\n move.w $100(a6),d0\n rts',[region()])as(a,_):
        assert not a.analysis_payload()[0]['sections'][0]['app_slot_refs']


def test_aliases_keep_the_existing_primary_catalog_name(tmp_path):
    r1=region();r1['rsset_layout_region_id']='primary'
    r2=region();r2.update(symbol='selected_alias',rsset_layout_region_id='alias',alias_of='decoded_style')
    extra=dict(rsset_use_site_bindings=[dict(rsset_use_site_binding_id='choice',hunk=0,addr=0,
        operand_index=0,base_register='A6',displacement=0x100,layout_name='app',
        base_symbol='__amiga_app_base__',base_evidence_id='selected-base:A6:__amiga_app_base__',
        access='read',width_bytes=2,render_state='linked_gap_or_raw')])
    with candidate_artifact(tmp_path,'move.w $100(a6),d0\n rts',[r1,r2],extra)as(a,original):
        source=a.inline_source_text_with_profile()[0]
        ref=a.analysis_payload()[0]['sections'][0]['app_slot_refs'][0]
        fields=a.analysis_payload()[0]['base_layout_fields']
        primary=next(f for f in fields if f['offset']==0x100 and f['layout_name']=='app')
        assert ref['symbol_name']==primary['symbol']
        assert ref['symbol_name']in source
        assert ref['base_evidence']=='use_site_binding'
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original


def test_another_layout_at_the_same_offset_does_not_rename_app_view(tmp_path):
    other=region();other.update(layout_name='service',base_symbol='service_base',symbol='service_state')
    with candidate_artifact(tmp_path,'move.w $100(a6),d0\n rts',[other])as(a,original):
        refs=a.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert not refs
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
