"""Unknown field purpose is distinct from known scalar initialization bits."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from tests.test_app_cursor_propagation import cursor_artifact


def artifact_for(tmp_path, body):
    return cursor_artifact(tmp_path, body, regions=False, metadata_extra=dict(
        custom_structs=[dict(name='Record', size=68,
                            fields=[dict(name='head', type='LONG', offset=0, size=4)])],
        entry_register_seeds=[dict(hunk=0, entry_offset=0, register='A0',
                                  kind='struct_ptr', struct_name='Record', note='Fixture input contract')]))


@pytest.mark.parametrize(('body', 'expected'), [
    ('move.l #0,8(a0)', True),
    ('move.w #0,8(a0)', True),
    ('move.b #0,8(a0)', True),
    ('moveq #0,d0\nmove.l d0,8(a0)', True),
    ('moveq #0,d0\nmove.l d0,d1\nmove.l d1,8(a0)', True),
    ('moveq #0,d0\nmove.l d0,-(a7)\nmove.l (a7)+,d1\nmove.l d1,8(a0)', True),
    ('move.l #$10000,d0\nmove.w d0,8(a0)', True),
    ('moveq #1,d0\nmove.l d0,8(a0)', False),
    ('move.l d0,8(a0)', False),
    ('moveq #0,d0\nmove.w #1,d0\nmove.l d0,8(a0)', False),
    ('moveq #0,d0\naddq.l #1,d0\nmove.l d0,8(a0)', False),
    ('addi.l #0,8(a0)', False),
    ('moveq #0,d0\nmovem.l d0-d1,8(a0)', False),
    ('move.l 8(a0),d0', False),
    ('lea.l 8(a6),a1\nmove.l a1,8(a0)', False),
    ('tst.w d2\nbeq.s other\nmoveq #0,d0\nbra.s joined\nother:\nmoveq #1,d0\njoined:\nmove.l d0,8(a0)', False),
    ('tst.w d2\nbeq.s joined\nmoveq #0,d0\njoined:\nmove.l d0,8(a0)', False),
    ('tst.w d2\nbeq.s other\nmoveq #0,d0\nbra.s joined\nother:\nmoveq #0,d0\njoined:\nmove.l d0,8(a0)', True),
])
def test_source_zero_write_uses_shared_values_without_resolving_the_field(tmp_path, body, expected):
    artifact, original = artifact_for(tmp_path, body)
    try:
        analysis = artifact.analysis_payload()[0]
        assert not analysis['incomplete_analysis']
        gap, = analysis['sections'][0]['recovered_platform_unresolved_typed_accesses']
        assert gap['classification'] == 'field_gap' and gap['displacement'] == 8
        assert gap.get('source_zero_write', False) is expected
        queried = artifact.query_payload('field_gaps', limit=100)
        assert queried['total'] == 1 and queried['items'][0]['status'] == 'unresolved'
        assert queried['items'][0].get('source_zero_write', False) is expected
        row = artifact.row_for_source_offset(section_index=0, offset=gap['offset'])
        assert row['unresolved_typed_accesses'][0].get('source_zero_write', False) is expected
        assert artifact.query_payload('field_gaps', struct_name='Other', limit=100)['total'] == 0
        assert artifact.query_payload('field_gaps', field_offset=4, limit=100)['total'] == 0
        with pytest.raises(ValueError, match='field_gaps supports source coordinates'):
            artifact.query_payload('field_gaps', symbol='Record')
    finally:
        artifact.close()


def test_unrolled_clear_remains_unresolved_and_field_gap_pages_match_native_records(tmp_path):
    body = 'moveq #0,d0\n' + '\n'.join(['move.l d0,(a0)+'] * 17)
    artifact, _ = artifact_for(tmp_path, body)
    try:
        gaps = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_unresolved_typed_accesses']
        assert len(gaps) == 16 and all(x.get('source_zero_write') for x in gaps)
        assert [x['displacement'] for x in gaps] == list(range(4, 68, 4))
        first = artifact.query_payload('field_gaps', offset=0, limit=7)
        second = artifact.query_payload('field_gaps', offset=7, limit=100)
        assert first['total'] == second['total'] == 16
        assert len(first['items']) == 7 and len(second['items']) == 9
        assert all(x['status'] == 'unresolved' and x['source_zero_write'] for x in first['items'] + second['items'])
    finally:
        artifact.close()


def test_relocation_placeholders_and_pointer_packets_do_not_become_zero_witnesses(tmp_path):
    root = Path(__file__).resolve().parents[1]
    cc = shutil.which('cc'); backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root / 'src/build/libamiga_backend.so'))
    if not cc or not backend.exists():
        pytest.skip('native compiler and backend required')
    source = tmp_path / 'zero-guards.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
int main(void) {
 M68kObject object={0}; M68kRenderLookup lookup={0}; M68kRenderTypedState state={0}; size_t dest=99;
 lookup.object=&object;
 M68kInstructionIR imm=m68k_plain_parse_instruction_to_ir("move.l #0,8(a0)",M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
 assert(typed_source_zero_write_operand(&lookup,&state,&imm,&dest) && dest==1);
 object.fixup_count=1; assert(!typed_source_zero_write_operand(&lookup,&state,&imm,NULL)); object.fixup_count=0;
 M68kInstructionIR reg=m68k_plain_parse_instruction_to_ir("move.l d0,8(a0)",M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
 state.data_regs[0].known=state.data_regs[0].raw_long_value_known=1;
 assert(typed_source_zero_write_operand(&lookup,&state,&reg,NULL));
 state.data_regs[0].pointer_value_known=1; assert(!typed_source_zero_write_operand(&lookup,&state,&reg,NULL));
 state.data_regs[0].pointer_value_known=0; state.data_regs[0].type_conflicted=1;
 assert(!typed_source_zero_write_operand(&lookup,&state,&reg,NULL));
 state.data_regs[0].type_conflicted=0; state.data_regs[0].address_value_candidate_overflow=1;
 assert(!typed_source_zero_write_operand(&lookup,&state,&reg,NULL)); return 0;
}''')
    exe = tmp_path / 'zero-guards'
    built = subprocess.run([cc, '-Isrc', '-D_POSIX_C_SOURCE=200809L', '-std=c11', '-O0', str(source), str(backend),
                            f'-Wl,-rpath,{backend.parent}', '-o', str(exe)], cwd=root, capture_output=True, text=True, timeout=60)
    assert built.returncode == 0, built.stderr
    run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=20)
    assert run.returncode == 0, run.stdout + run.stderr
