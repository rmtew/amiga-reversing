"""Callable effect subjects retain the class of their entry register."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from amiga_reversing.disasm import c_backend


@pytest.mark.parametrize('register', ['a0', 'd0', 'd7'])
def test_write_subject_uses_complete_entry_register_identity(tmp_path, register):
    a, original = cursor_artifact(tmp_path, f'''bsr.w helper
 rts
helper:
 movea.l {register},a2
 move.l a1,(a2)
 rts''')
    try:
        summary, = a.analysis_payload()[0]['sections'][0]['function_summaries']
        inputs = summary['inputs']
        memory = summary['effects']['memory']
        escapes = summary['effects']['escapes']
        assert memory['state'] == escapes['state'] == 'explicit'
        subject, = memory['effects']
        assert inputs[subject['subject']['input_index']]['location']['register'] == register.upper()
        escape, = escapes['escapes']
        assert escape['source_location']['register'] == 'A1'
        assert escape['sink_subject'] == subject['subject']
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw', a.inline_source_text_with_profile()[0])[0] == original
    finally:
        a.close()


@pytest.mark.parametrize('change', ['move.w d1,d0', 'moveq #0,d0',
    'tst.w d1\n beq.s unchanged\n move.l d2,d0\nunchanged:', 'jsr (a3)'])
def test_lost_or_conflicting_entry_identity_keeps_memory_unknown(tmp_path, change):
    a, _ = cursor_artifact(tmp_path, f'''bsr.w helper
 rts
helper:
 {change}
 movea.l d0,a2
 move.l a1,(a2)
 rts''')
    try:
        summaries = a.analysis_payload()[0]['sections'][0]['function_summaries']
        assert not summaries or all(f['effects']['memory']['state'] in {'unknown', 'invalid'} for f in summaries)
    finally:
        a.close()


def test_address_and_data_register_zero_have_distinct_write_subjects(tmp_path):
    a, _ = cursor_artifact(tmp_path, '''bsr.w helper
 rts
helper:
 move.l a1,(a0)
 movea.l d0,a2
 move.l a1,(a2)
 rts''')
    try:
        summary, = a.analysis_payload()[0]['sections'][0]['function_summaries']
        memory = summary['effects']['memory']
        assert memory['state'] == 'explicit'
        assert {summary['inputs'][e['subject']['input_index']]['location']['register']
                for e in memory['effects']} == {'A0', 'D0'}
        escapes = summary['effects']['escapes']
        assert escapes['state'] == 'explicit'
        assert {summary['inputs'][e['sink_subject']['input_index']]['location']['register']
                for e in escapes['escapes']} == {'A0', 'D0'}
        assert all(e['source_location']['register'] == 'A1' for e in escapes['escapes'])
    finally:
        a.close()
