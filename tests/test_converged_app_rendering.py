"""Frozen per-access identities survive rendering's linear call-state reset."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from amiga_reversing.disasm import c_backend


def seeds(app='a4'):
    return [dict(hunk=0, entry_offset=0, register=app.upper(), kind='library_base',
                 library_name='__amiga_app_base__'),
            dict(hunk=0, entry_offset=0, register='A6', kind='library_base',
                 library_name='timer.device')]


@pytest.mark.parametrize('width,delta,field', [('l', 4, 'TV_MICRO'), ('w', 2, 'TV_SECS+2')])
def test_native_app_identity_survives_known_library_call(tmp_path, width, delta, field):
    artifact, original = cursor_artifact(tmp_path,
        f'lea.l $100(a4),a0\n jsr -66(a6)\n move.{width} ${0x100+delta:X}(a4),d0',
        metadata_extra=dict(entry_register_seeds=seeds()))
    try:
        analysis = artifact.analysis_payload()[0]
        ref = next(r for r in analysis['sections'][0]['app_slot_refs'] if r['offset'] == 8)
        assert ref['base_evidence'] == 'register_state'
        source = artifact.inline_source_text_with_profile()[0]
        assert f'app_0100+{field}(a4)' in source
        assert 'INCLUDE "devices/timer.i"' in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source,
            include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')[0] == original
    finally:
        artifact.close()


@pytest.mark.parametrize('change', ['movea.l d0,a4', 'movea.w d0,a4',
    'tst.w d0\n beq.s join\n movea.l d0,a4\njoin:'])
def test_unknown_or_conflicting_base_is_not_recovered_from_old_access(tmp_path, change):
    artifact, original = cursor_artifact(tmp_path,
        f'lea.l $100(a4),a0\n jsr -66(a6)\n {change}\n move.l $104(a4),d0',
        metadata_extra=dict(entry_register_seeds=seeds()))
    try:
        source = artifact.inline_source_text_with_profile()[0]
        line = next(l for l in source.splitlines() if '\tmove.l ' in l and '(a4),d0' in l)
        assert 'app_0100+' not in line
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source,
            include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')[0] == original
    finally:
        artifact.close()


def test_interior_cursor_keeps_its_own_displacement(tmp_path):
    artifact, original = cursor_artifact(tmp_path,
        'lea.l $100(a4),a0\n jsr -66(a6)\n lea.l $100(a4),a3\n move.l 4(a3),d0',
        metadata_extra=dict(entry_register_seeds=seeds()))
    try:
        source = artifact.inline_source_text_with_profile()[0]
        line = next(l for l in source.splitlines() if '\tmove.l ' in l and '(a3),d0' in l)
        assert 'app_0100+TV_MICRO(a3)' not in line
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source,
            include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')[0] == original
    finally:
        artifact.close()


def test_frozen_index_requires_exact_source_operand_and_zero_origin(tmp_path):
    import os
    from pathlib import Path
    import shutil
    import subprocess
    root = Path(__file__).resolve().parents[1]
    cc = shutil.which('cc')
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root/'src/build/libamiga_backend.so'))
    if not cc or not backend.exists():
        pytest.skip('native compiler/backend required')
    probe = tmp_path/'frozen.c'
    probe.write_text('#include "'+str(root/'src/m68k_render_ir.c')+'"\n'+r'''
#include <assert.h>
int main(void) {
  M68kRenderLookup lookup = {0};
  M68kRenderAppSlotRef rows[3] = {0};
  lookup.app_slot_refs = rows; lookup.app_slot_ref_count = 3;
  /* Canonical vectors need not be source ordered or single-section. */
  rows[0].section_index = 1; rows[0].ref.offset = 4;
  rows[1].ref.offset = 12; rows[2].ref.offset = 4;
  for (unsigned i=0; i<3; ++i) {
    rows[i].ref.base_reg=4; rows[i].ref.operand_index=0;
    rows[i].ref.displacement=0x104;
    rows[i].ref.access_kind=M68K_APP_SLOT_ACCESS_READ;
    rows[i].ref.base_evidence_kind=M68K_APP_SLOT_BASE_REGISTER_STATE;
  }
  assert(render_lookup_index_app_accesses(&lookup)==0);
  int proven = 0;
#define RECORDED(s,o,r,d,w) lookup_recorded_app_base_access(&lookup,s,o,0,r,d,M68K_APP_SLOT_ACCESS_READ,w,&proven)
#define PROVEN(s,o,r,d,w) (RECORDED(s,o,r,d,w) && proven)
  assert(PROVEN(0,4,4,0x104,4)); assert(PROVEN(1,4,4,0x104,4));
  assert(!PROVEN(2,4,4,0x104,4)); assert(!PROVEN(0,8,4,0x104,4));
  assert(!PROVEN(0,4,5,0x104,4)); assert(!PROVEN(0,4,4,0x106,4));
  assert(rows[0].section_index==1 && rows[1].ref.offset==12);
  rows[2].ref.base_evidence_kind=M68K_APP_SLOT_BASE_A6_FALLBACK;
  assert(!PROVEN(0,4,4,0x104,4));
  assert(RECORDED(0,4,4,0x104,4) && !proven);
  rows[2].ref.base_evidence_kind=M68K_APP_SLOT_BASE_UNSPECIFIED;
  assert(!RECORDED(0,4,4,0x104,4) && !proven);
  rows[2].ref.base_evidence_kind=M68K_APP_SLOT_BASE_REGISTER_STATE;
  rows[2].ref.has_derived_base=1; rows[2].ref.base_displacement=0x100;
  rows[2].ref.operand_displacement=4; rows[2].ref.access_size=4;
  assert(!PROVEN(0,4,4,0x104,4));
  rows[2].ref.base_displacement=0; rows[2].ref.operand_displacement=0x104;
  assert(PROVEN(0,4,4,0x104,4)); assert(!PROVEN(0,4,4,0x104,2));
  rows[2].ref.loop_iteration_count=3; assert(PROVEN(0,4,4,0x104,4));
  rows[2].ref.loop_iteration_stride=4; assert(!PROVEN(0,4,4,0x104,4));
  rows[2].ref.loop_iteration_stride=0;
  rows[2].ref.base_evidence_kind=M68K_APP_SLOT_BASE_A6_FALLBACK;
  assert(RECORDED(0,4,4,0x104,4) && !proven);
  m68k_render_lookup_destroy(&lookup);
  return 0;
}
''')
    exe = tmp_path/'frozen'
    subprocess.run([cc, '-std=c11', '-D_POSIX_C_SOURCE=200809L', '-O0', '-I'+str(root/'src'),
        str(probe), str(backend), '-Wl,-rpath,'+str(backend.parent), '-lm', '-lcrypto', '-o', str(exe)],
        check=True, capture_output=True, text=True)
    subprocess.run([str(exe)], check=True, capture_output=True, text=True)
