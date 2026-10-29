"""Conflicting inferred identities must not erase canonical layout declarations."""
import pytest
from tests.test_base_candidates import candidate_artifact
from amiga_reversing.disasm import c_backend


@pytest.mark.parametrize('byte_size,word_size,small_op,large_op',[
    (1,2,'b','w'),(2,4,'w','l'),(2,2,'w','w'),
])
@pytest.mark.parametrize('reverse',[False,True])
def test_same_origin_views_retain_both_declarations_without_selecting_one(
        tmp_path,byte_size,word_size,small_op,large_op,reverse):
    regions=[dict(layout_name='app',offset=0x138,size=byte_size,
                  symbol='event_view',storage_kind='scalar'),
             dict(layout_name='other_phase',base_symbol='__amiga_app_base__',
                  offset=0x138,size=word_size,symbol='coordinate_view',storage_kind='scalar')]
    if reverse:regions.reverse()
    code=f' move.{small_op} d0,$138(a6)\n move.{large_op} d1,$138(a6)\n rts\n'
    with candidate_artifact(tmp_path,code,regions)as(a,original):
        source=a.inline_source_text_with_profile()[0]
        assert f'event_view RS.{small_op.upper()} 1\n'in source
        assert f'coordinate_view RS.{large_op.upper()} 1\n'in source
        # A shared numeric origin and the transfer width do not prove a phase.
        lines=[x for x in source.splitlines()if x.startswith('\tmove.')]
        assert len(lines)==2
        assert all('event_view'not in x and 'coordinate_view'not in x for x in lines)
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
        # Also encode both declarations: a present but displaced label is wrong.
        constants=source+'\tdc.w event_view,coordinate_view\n'
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',constants)[0]==original+bytes.fromhex('01380138')


def test_foreign_base_declaration_is_not_an_app_alias(tmp_path):
    regions=[dict(layout_name='app',offset=0x138,size=1,symbol='event_view',storage_kind='scalar'),
             dict(layout_name='foreign',base_symbol='foreign_base',offset=0x138,size=2,
                  symbol='foreign_coordinate',storage_kind='scalar')]
    with candidate_artifact(tmp_path,' move.b d0,$138(a6)\n rts\n',regions)as(a,original):
        source=a.inline_source_text_with_profile()[0]
        assert 'event_view RS.B 1\n'in source and 'foreign_coordinate RS.W 1\n'in source
        assert '\tmove.b d0,event_view(a6)\n'in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
