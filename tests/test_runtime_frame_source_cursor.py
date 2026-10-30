"""Numeric runtime frames must remain separate from source/semantic pointees."""
import pytest
from amiga_reversing.disasm import c_backend
from tests.test_source_pointer_loop_domain import header_table_artifact


@pytest.mark.parametrize('setup', [
    'lea.l $60000.l,a6',
    'lea.l $60000.l,a6\nmove.l a6,saved_frame.l\nmovea.l saved_frame.l,a6',
    'lea.l $68000.l,a6\nadda.l #$8000,a6\nsuba.l #$6998,a6',
    'tst.w d7\nbeq alternative\nlea.l $60000.l,a6\nbra save\nalternative:lea.l $68000.l,a6\nsave:move.l a6,saved_frame.l\nmovea.l saved_frame.l,a6',
])
def test_proved_external_frame_write_does_not_alias_source_directory(tmp_path, setup):
    artifact, original = header_table_artifact(tmp_path, count=104, setup=setup,
        record_access='move.w (a0)+,d0\nmove.w (a0),d1\nmove.w d0,$40(a6)\n',
        code_tail='saved_frame:dc.l 0\n')
    try:
        payload = artifact.analysis_payload()[0]
        assert not payload['incomplete_analysis']
        section = payload['sections'][0]
        assert {r['field_name'] for r in section['recovered_platform_typed_accesses']} == {'count', 'flags'}
        assert any(r['resolution'] == 'type_domain' for r in section['address_values'])
        source = artifact.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    finally:
        artifact.close()


@pytest.mark.parametrize('setup', [
    '',  # No frame provenance.
    'lea.l $70000.l,sp\nlea.l $60000.l,a6\nmove.l a6,saved_frame.l\nmovea.l saved_frame.l,a6\nbsr initialize\nrts\ninitialize:',  # No callable input/effect contract.
    'lea.l directory-$40(pc),a6',  # Proven alias is not disjoint.
    'tst.w d7\nbeq alias\nlea.l $60000.l,a6\nbra save\nalias:lea.l directory-$40(pc),a6\nsave:move.l a6,saved_frame.l\nmovea.l saved_frame.l,a6',
    'lea.l $60000.l,a6\nmove.l a6,saved_frame.l\nmove.w #0,saved_frame+2.l\nmovea.l saved_frame.l,a6',
    'lea.l $60000.l,a6\nmove.l a6,saved_frame.l\nmove.b #0,saved_frame+1.l\nmovea.l saved_frame.l,a6',
    'lea.l $60000.l,a6\nmove.l a6,saved_frame.l\nmove.b #0,(a2)\nmovea.l saved_frame.l,a6',
    'lea.l $60000.l,a6\nmove.l a6,saved_frame.l\njsr unknown\nmovea.l saved_frame.l,a6',
    # An unreachable writer must not seed the reader from its global summary.
    'bra reader\nwriter:lea.l $60000.l,a6\nmove.l a6,saved_frame.l\nrts\nreader:movea.l saved_frame.l,a6',
])
def test_unproved_or_clobbered_runtime_frame_refuses_directory_domain(tmp_path, setup):
    artifact, _ = header_table_artifact(tmp_path, count=104, setup=setup,
        record_access='move.w (a0)+,d0\nmove.w (a0),d1\nmove.w d0,$40(a6)\n',
        code_tail='unknown:move.b #0,(a2)\nrts\nsaved_frame:dc.l 0\n')
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        assert not any(r['resolution'] == 'type_domain' for r in section['address_values'])
    finally:
        artifact.close()


def test_uncontracted_call_does_not_preserve_runtime_frame(tmp_path):
    artifact, original = header_table_artifact(tmp_path, count=104,
        setup='lea.l $70000.l,sp\nlea.l $60000.l,a6\nmove.l a6,saved_frame.l\nmovea.l saved_frame.l,a6\nbsr preserve\n',
        record_access='move.w (a0)+,d0\nmove.w (a0),d1\nmove.w d0,$40(a6)\n',
        code_tail='preserve:rts\nsaved_frame:dc.l 0\n')
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',artifact.inline_source_text_with_profile()[0])[0] == original
    finally:
        artifact.close()
