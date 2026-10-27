"""Unknown predecessors cannot acquire facts from a later predecessor."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_native_typed_join_is_unknown_absorbing_and_order_independent(tmp_path):
    compiler = shutil.which('cc')
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', ROOT / 'src/build/libamiga_backend.so'))
    if compiler is None or not backend.exists():
        pytest.skip('host compiler and native backend required')
    source = tmp_path / 'join.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
int main(void) {
  M68kRenderTypedRegValue known, unknown, joined, reverse, second;
  unsigned int pointer, permutation;
  for (pointer = 0; pointer != 2; ++pointer) {
    memset(&known, 0, sizeof(known));
    memset(&unknown, 0, sizeof(unknown));
    known.known = 1;
    if (pointer) { known.pointer_value_known = 1; known.pointer_value = 64; }
    else { known.raw_long_value_known = 1; known.raw_long_value = 64; }
    joined = unknown;
    typed_reg_merge(&joined, &known, NULL);
    assert(typed_reg_values_equal(&joined, &unknown));
    reverse = known;
    typed_reg_merge(&reverse, &unknown, NULL);
    assert(typed_reg_values_equal(&joined, &reverse));
    /* A three-way join must retain the unknown path in every order. */
    second = known;
    if (pointer) second.pointer_value = 80; else second.raw_long_value = 80;
    for (permutation = 0; permutation != 3; ++permutation) {
      joined = permutation == 0 ? unknown : known;
      typed_reg_merge(&joined, permutation == 0 ? &known : permutation == 1 ? &unknown : &second, NULL);
      typed_reg_merge(&joined, permutation == 2 ? &unknown : &second, NULL);
      assert(typed_reg_values_equal(&joined, &unknown));
    }
    /* Known alternatives still retain their bounded union. */
    joined = known;
    typed_reg_merge(&joined, &second, NULL);
    assert(joined.known);
    assert(pointer ? joined.pointer_candidate_count == 2 : joined.raw_long_candidate_count == 2);
    reverse = joined;
    typed_reg_merge(&joined, &second, NULL);
    assert(typed_reg_values_equal(&joined, &reverse));
  }
  {
    M68kRenderTypedProvenance first = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA, 0, 8);
    M68kRenderTypedProvenance other = typed_provenance_make(M68K_PLATFORM_TYPE_PROVENANCE_STATIC_DATA, 0, 12);
    M68kRenderTypedProvenance unknown = {0}, joined, reverse;
    joined = first;
    typed_provenance_merge(&joined, &unknown);
    reverse = unknown;
    typed_provenance_merge(&reverse, &first);
    assert(typed_provenances_equal(&joined, &reverse));
    assert(joined.kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE);
    joined = first;
    typed_provenance_merge(&joined, &other);
    typed_provenance_merge(&joined, &first);
    assert(joined.kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE);
    {
      M68kRenderLookup lookup = {0};
      M68kRenderTypedState state = {0};
      M68kRenderTypedStoredValue stored = {0}, loaded;
      M68kOperandIR operand = {0};
      stored.known = stored.raw_long_value_known = 1;
      stored.raw_long_value = 75;
      stored.provenance = joined;
      assert(stored.provenance.merge_conflicted);
      typed_state_set_stack_slot(&state, 0, 1, M68K_FUNCTION_SUMMARY_ABI_STACK_NONE, &stored, NULL);
      operand.kind = M68K_ASM_OPERAND_POSTINC;
      operand.value.reg = 7;
      assert(typed_value_for_memory_read_operand(&lookup, &state, NULL, 0, &operand,
        M68K_SIM_ACCESS_MEMORY_READ, &loaded, NULL));
      assert(loaded.raw_long_value_known && loaded.raw_long_value == 75);
      assert(loaded.provenance.kind == M68K_PLATFORM_TYPE_PROVENANCE_NONE);
      assert(loaded.provenance.merge_conflicted);
      /* A genuinely unannotated single source still gets its storage witness. */
      typed_provenance_clear(&stored.provenance);
      typed_state_set_stack_slot(&state, 0, 1, M68K_FUNCTION_SUMMARY_ABI_STACK_NONE, &stored, NULL);
      assert(typed_value_for_memory_read_operand(&lookup, &state, NULL, 0, &operand,
        M68K_SIM_ACCESS_MEMORY_READ, &loaded, NULL));
      assert(loaded.provenance.kind == M68K_PLATFORM_TYPE_PROVENANCE_STACK_SLOT);
    }
  }
  {
    M68kRenderTypedRegValue empty = {0}, dead = {0};
    dead.provenance.merge_conflicted = 1;
    assert(typed_reg_values_equal(&empty, &dead));
    empty.known = dead.known = 1;
    empty.raw_long_value_known = dead.raw_long_value_known = 1;
    assert(!typed_reg_values_equal(&empty, &dead));
  }
  return 0;
}
''')
    exe = tmp_path / 'join'
    subprocess.run([compiler, '-Isrc', '-D_POSIX_C_SOURCE=200809L', '-std=c11', '-O0',
                    str(source), str(backend), f'-Wl,-rpath,{backend.parent}', '-o', str(exe)],
                   cwd=ROOT, capture_output=True, text=True, check=True, timeout=60)
    result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


def test_exhausted_typed_worklist_is_reported_without_optional_trace(tmp_path, monkeypatch):
    from tests.test_typed_postincrement_cursor import _artifact
    monkeypatch.delenv('AMIGA_REVERSING_PROFILE_TYPED_FLOW', raising=False)
    monkeypatch.setenv('AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS', '1')
    *_, artifact, original = _artifact(tmp_path, ['move.w (a0),d0', 'move.w 2(a0),d1'])
    try:
        analysis, _ = artifact.analysis_payload()
        warnings = [w for w in analysis['incomplete_analysis']
                    if w['source_kind_name'] == 'typed_flow_worklist']
        assert len(warnings) == 1
        assert warnings[0]['capacity'] == 1
        assert warnings[0]['hit_count'] > 0
        assert warnings[0]['section_index'] == 0
        assert warnings[0]['kind_name'] == 'capacity_exhausted'
    finally:
        artifact.close()


def test_converged_typed_worklist_has_no_exhaustion_record(tmp_path, monkeypatch):
    from tests.test_typed_postincrement_cursor import _artifact
    monkeypatch.delenv('AMIGA_REVERSING_PROFILE_TYPED_FLOW', raising=False)
    monkeypatch.delenv('AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS', raising=False)
    *_, artifact, original = _artifact(tmp_path, ['move.w (a0),d0', 'move.w 2(a0),d1'])
    try:
        analysis, _ = artifact.analysis_payload()
        assert not [w for w in analysis['incomplete_analysis']
                    if w['source_kind_name'] == 'typed_flow_worklist']
    finally:
        artifact.close()


@pytest.mark.parametrize('initial', ['moveq #75,d1', 'move.l #data,d1'])
def test_caller_save_restore_loop_reaches_fixed_point(tmp_path, monkeypatch, capfd, initial):
    import re
    from tests.test_typed_postincrement_cursor import _artifact
    monkeypatch.setenv('AMIGA_REVERSING_PROFILE_TYPED_FLOW', '1')
    monkeypatch.delenv('AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS', raising=False)
    instructions = [initial, 'loop: move.l d1,-(a7)', 'bsr helper', 'move.l (a7)+,d1',
                    'dbf d1,loop', 'rts', 'helper: moveq #0,d1', 'rts', 'data: dc.l 0']
    *_, artifact, original = _artifact(tmp_path, instructions)
    try:
        analysis, _ = artifact.analysis_payload()
        assert not analysis['incomplete_analysis']
        worklists = re.findall(r'typed_flow_worklist .*?visits=(\d+) pending=(\d+) max=(\d+)',
                               capfd.readouterr().err)
        assert worklists
        assert all(int(pending) == 0 and int(visits) < int(limit)
                   for visits, pending, limit in worklists)
    finally:
        artifact.close()


def test_optional_worklist_trace_does_not_change_facts(tmp_path, monkeypatch, capfd):
    from tests.test_typed_postincrement_cursor import _artifact
    monkeypatch.delenv('AMIGA_REVERSING_PROFILE_TYPED_FLOW', raising=False)
    instructions = ['move.w (a0),d0', 'move.w 2(a0),d1']
    *_, artifact, original = _artifact(tmp_path, instructions)
    try:
        before, _ = artifact.analysis_payload()
    finally:
        artifact.close()
    assert 'typed_flow_hot ' not in capfd.readouterr().err
    monkeypatch.setenv('AMIGA_REVERSING_PROFILE_TYPED_FLOW', '1')
    *_, artifact, original = _artifact(tmp_path, instructions)
    try:
        after, _ = artifact.analysis_payload()
        assert before == after
        assert 'typed_flow_hot ' in capfd.readouterr().err
    finally:
        artifact.close()
