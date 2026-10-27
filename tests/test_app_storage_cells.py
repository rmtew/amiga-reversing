"""App and absolute cells share local must-values, not a merged writer history."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact, derived_refs


def app_cell(tmp_path, body):
    return cursor_artifact(tmp_path, body)


@pytest.mark.parametrize('middle,expected', [
    ('',0xC3E),('addq.l #6,$200(a6)',0xC44),('subq.l #6,$200(a6)',0xC38),
    ('addq.w #6,$200(a6)',None),('addq.l #6,$202(a6)',None),('clr.l $200(a6)',None),('move.b #0,$201(a6)',None),
    ('move.w #0,$202(a6)',None),('movem.l d0-d1,$1FC(a6)',None),
    ('move.b #0,$1FF(a6)',0xC3E),('move.b #0,$204(a6)',0xC3E),
    ('move.b #0,(a2)',None),('move.w #0,$DFF180.l',0xC3E),
    ('lea.l $DFF000.l,a5\n move.w #0,$180(a5)',0xC3E),
    ('lea.l $DFF000.l,a5\n move.w #0,$2000(a5)',None),('jsr $2000.l',None),
])
def test_app_cell_uses_reaching_store_and_full_write_footprint(tmp_path,middle,expected):
    a,_=app_cell(tmp_path,'lea.l $C3E(a6),a0\n move.l a0,$200(a6)\n '+middle+
        '\n movea.l $200(a6),a1\n move.w (a1),d0')
    try:
        assert [r['displacement']for r in derived_refs(a)if r['base_register']=='A1'and r['access']=='read']==([]if expected is None else[expected])
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()


def test_app_load_before_later_store_has_no_reaching_value(tmp_path):
    a,_=app_cell(tmp_path,'movea.l $200(a6),a1\n move.w (a1),d0\n lea.l $C3E(a6),a0\n move.l a0,$200(a6)')
    try:
        assert not [r for r in derived_refs(a)if r['base_register']=='A1'and r['access']=='read']
    finally:a.close()


@pytest.mark.parametrize('other,expected',[(0xC3E,0xC3E),(0xBC6,None)])
def test_app_cell_join_retains_only_equal_values(tmp_path,other,expected):
    a,_=app_cell(tmp_path,'tst.w d0\n beq.w alternate\n lea.l $C3E(a6),a0\n move.l a0,$200(a6)\n bra.w join\nalternate:\n '+
        f'lea.l ${other:X}(a6),a0\n move.l a0,$200(a6)\njoin:\n movea.l $200(a6),a1\n move.w (a1),d0')
    try:
        assert [r['displacement']for r in derived_refs(a)if r['base_register']=='A1'and r['access']=='read']==([]if expected is None else[expected])
    finally:a.close()


@pytest.mark.parametrize('callee,expected', [('rts',True),('clr.l $200(a6)\n rts',False),('move.b #0,(a2)\n rts',False)])
def test_app_cell_obeys_existing_call_memory_effects(tmp_path,callee,expected):
    a,_=app_cell(tmp_path,'lea.l $C3E(a6),a0\n move.l a0,$200(a6)\n bsr.w helper\n movea.l $200(a6),a1\n move.w (a1),d0\n rts\nhelper:\n '+callee)
    try:
        assert bool([r for r in derived_refs(a)if r['base_register']=='A1'and r['access']=='read'])==expected
    finally:a.close()


def record_cell(tmp_path,body,source_reg='a6'):
    return cursor_artifact(tmp_path,body,source_reg=source_reg,seeded=source_reg!='a6',regions=False,metadata_extra=dict(
        custom_structs=[dict(name='Record',size=8,fields=[dict(name='world_x',type='LONG',offset=4,size=4)])],
        rsset_layout_regions=[dict(layout_name='app',offset=offset,size=4,
            storage_kind='struct_pointer',pointer_struct='Record',symbol=symbol)
            for offset,symbol in [(0x200,'selected'),(0x204,'input_record')]]))


@pytest.mark.parametrize('tail,expected', [('',True),('clr.l $200(a6)',False),
    ('move.b #0,$201(a6)',False),('move.b #0,(a3)',False),
    ('lea.l $201(a6),a3\n move.b #0,(a3)',False)])
def test_app_pointer_type_follows_the_actual_store(tmp_path,tail,expected):
    a,_=record_cell(tmp_path,'movea.l $204(a6),a0\n move.l a0,$200(a6)\n '+tail+
        '\n movea.l $200(a6),a1\n tst.l 4(a1)')
    try:
        assert bool([r for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
                     if r['base_register']=='A1'and r['field_name']=='world_x'])==expected
    finally:a.close()


def test_app_cell_alias_uses_the_same_canonical_identity(tmp_path):
    a,_=app_cell(tmp_path,'lea.l $C3E(a6),a0\n move.l a0,$200(a6)\n lea.l $200(a6),a3\n movea.l (a3),a1\n move.w (a1),d0')
    try:
        assert [r['displacement']for r in derived_refs(a)if r['base_register']=='A1'and r['access']=='read']==[0xC3E]
    finally:a.close()


def test_pointer_saved_before_clear_keeps_its_reaching_value(tmp_path):
    a,_=record_cell(tmp_path,'movea.l $204(a6),a0\n move.l a0,$200(a6)\n movea.l $200(a6),a1\n move.l a1,-(a7)\n clr.l $200(a6)\n movea.l (a7)+,a1\n tst.l 4(a1)')
    try:
        assert any(r['base_register']=='A1'and r['field_name']=='world_x'
            for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses'])
    finally:a.close()


def test_declared_entry_pointer_on_untouched_sibling_path_is_not_a_numeric_target(tmp_path):
    a,_=record_cell(tmp_path,'tst.w d0\n beq.w clear_reference\n movea.l $200(a6),a0\n tst.l 4(a0)\n rts\nclear_reference:\n clr.l $200(a6)')
    try:
        assert any(r['base_register']=='A0'and r['field_name']=='world_x'
            for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses'])
        assert not [r for r in derived_refs(a)if r['base_register']=='A0']
    finally:a.close()


def test_declared_pointer_saved_before_clear_retains_type(tmp_path):
    a,_=record_cell(tmp_path,'movea.l $200(a6),a0\n move.l a0,-(a7)\n clr.l $200(a6)\n movea.l (a7)+,a1\n tst.l 4(a1)')
    try:
        assert any(r['base_register']=='A1'and r['field_name']=='world_x'
            for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses'])
    finally:a.close()


def test_address_of_pointer_slot_is_not_its_pointee(tmp_path):
    a,_=record_cell(tmp_path,'lea.l $204(a6),a0\n tst.l 4(a0)')
    try:
        assert not [r for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
            if r['base_register']=='A0'and r['field_name']=='world_x']
    finally:a.close()


@pytest.mark.parametrize('tail,expected',[('',True),('clr.b $55(a6)',False),('jsr $2000.l',False)])
def test_api_produced_pointer_is_a_local_memory_result(tmp_path,tail,expected):
    body=('lea.l device_name(pc),a0\n lea.l $40(a6),a1\n move.w #9,$1C(a1)\n'
          'move.l a6,-(a7)\n movea.l $4.w,a6\n jsr -444(a6)\n movea.l (a7)+,a6\n '+tail+
          '\n movea.l $54(a6),a0\n cmpi.w #36,$14(a0)\n rts\ndevice_name:\n dc.b "timer.device",0\n even')
    a,_=cursor_artifact(tmp_path,body,source_reg='a6',seeded=True,regions=False)
    try:
        assert ('LIB_VERSION' in a.inline_source_text_with_profile()[0])==expected
    finally:a.close()


def test_foreign_library_extension_is_not_the_app_cell_at_the_same_offset(tmp_path):
    a,_=record_cell(tmp_path,'movea.l $204(a2),a0\n movea.l $4.w,a6\n move.l a0,$200(a6)\n movea.l $200(a2),a1\n tst.l 4(a1)\n movea.l $200(a6),a3\n tst.l 4(a3)',source_reg='a2')
    try:
        fields=a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert not [r for r in fields if r['base_register']=='A1'and r['field_name']=='world_x']
        assert any(r['base_register']=='A3'and r['field_name']=='world_x'for r in fields)
    finally:a.close()


def test_api_results_do_not_come_from_a_future_or_only_first_producer(tmp_path):
    # The partial write forces a later producer to reestablish the pointer,
    # without assuming that an opaque call preserves an incoming base.
    call=('lea.l device_name(pc),a0\n lea.l $40(a6),a1\n move.w #9,$1C(a1)\n'
          'move.l a6,-(a7)\n movea.l $4.w,a6\n jsr -444(a6)\n movea.l (a7)+,a6\n')
    body=('movea.l $54(a6),a3\n cmpi.w #36,$14(a3)\n'+call+
          'clr.b $55(a6)\n movea.l $54(a6),a4\n cmpi.w #36,$14(a4)\n'+call+
          'movea.l $54(a6),a0\n cmpi.w #36,$14(a0)\n rts\ndevice_name:\n dc.b "timer.device",0\n even')
    a,original=cursor_artifact(tmp_path,body,source_reg='a6',seeded=True,regions=False)
    try:
        source=a.inline_source_text_with_profile()[0]
        assert '\tcmpi.w #36,$0014(a3)'in source
        assert '\tcmpi.w #36,$0014(a4)'in source
        assert '\tcmpi.w #36,LIB_VERSION(a0)'in source
        effects=a.analysis_payload()[0]['sections'][0]['recovered_platform_effects']
        assert len({r['offset']for r in effects if r['displacement']==0x54 and r['type_name']})==2
        from amiga_reversing.disasm import c_backend
        from pathlib import Path
        includes=Path(__file__).resolve().parents[1]/'ext/amiga_includes/ndk_2.0/include'
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source,include_dir=includes)[0]==original
    finally:a.close()


def test_read_only_call_preserves_declared_entry_type_without_a_numeric_value(tmp_path):
    a,_=record_cell(tmp_path,'bsr.w helper\n movea.l $204(a6),a0\n tst.l 4(a0)\n rts\nhelper:\n rts')
    try:
        rows=[r for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
              if r['base_register']=='A0'and r['field_name']=='world_x']
        assert rows and all(r['type_provenance_kind']=='policy_seed'for r in rows)
        assert not [r for r in derived_refs(a)if r['base_register']=='A0']
    finally:a.close()


def test_other_named_layout_does_not_declare_an_app_pointee(tmp_path):
    a,_=cursor_artifact(tmp_path,'movea.l $200(a2),a0\n tst.l 4(a0)',source_reg='a2',seeded=True,regions=False,
        metadata_extra=dict(custom_structs=[dict(name='ForeignRecord',size=8,fields=[dict(name='foreign_value',type='LONG',offset=4,size=4)])],
            rsset_layout_regions=[dict(layout_name='other',base_symbol='other_base',offset=0x200,size=4,
                storage_kind='struct_pointer',pointer_struct='ForeignRecord',symbol='other_pointer')]))
    try:
        assert not [r for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
            if r['base_register']=='A0'and r['field_name']=='foreign_value']
    finally:a.close()
