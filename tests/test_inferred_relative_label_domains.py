"""Recovered dispatch expressions use address mappings, not label spelling."""
import pytest

from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_base_displacement_integration import _round_trip


@pytest.mark.parametrize('named_base', [False, True])
@pytest.mark.parametrize('named_targets', [False, True])
def test_inferred_relative_names_share_the_actual_runtime_view(
        tmp_path, named_base, named_targets):
    metadata = {}
    if named_base:
        metadata['absolute_code_labels'] = [dict(addr=0x1008, name='named_dispatch_offsets')]
    if named_targets:
        metadata['seeded_code_labels'] = [
            dict(hunk=0, addr=12, name='named_case_zero'),
            dict(hunk=0, addr=14, name='named_case_one')]
    artifact, original = cursor_artifact(tmp_path, '''
 move.w offsets(pc,d1.w),d1
 jmp offsets(pc,d1.w)
offsets:
 dc.w first-offsets,second-offsets
first:
 rts
second:
 rts''', regions=False, metadata_extra=metadata)
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        site, = section['recovered_indirect_sites']
        assert site['status'] == 'jump_table' and site['target_count'] == 2
        text = artifact.inline_source_text_with_profile()[0]
        base = 'named_dispatch_offsets' if named_base else 'abs_0_00001008'
        for index, offset in enumerate([12, 14]):
            target = ['named_case_zero', 'named_case_one'][index] if named_targets else f'abs_0_{0x1000+offset:08X}'
            assert any(line.split(';')[0].rstrip() == f'\tdc.w {target}-{base}' for line in text.splitlines())
        _round_trip(tmp_path, text, original)
    finally:
        artifact.close()


def test_relative_mapping_guard_rejects_partial_or_different_placements(tmp_path):
    """Exercise the shared inferred/manual guard without seeding a relation."""
    import os
    from pathlib import Path
    import shutil
    import subprocess

    root = Path(__file__).resolve().parents[1]
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root / 'src/build/libamiga_backend.so'))
    compiler = shutil.which('cc')
    if compiler is None or not backend.exists():
        pytest.skip('host compiler and native backend required')
    source = tmp_path / 'mapping.c'
    source.write_text('#include "m68k_render_ir.c"\n#include <assert.h>\n' + r'''
int main(void) {
  M68kRenderLookup lookup = {0};
  M68kFact facts[2] = {{0}};
  M68kRenderRuntimeAddressRange ranges[2] = {{0}};
  assert(relative_source_labels_preserve_displacement(&lookup, 0, 8, 12, 4));
  lookup.build_complete = 1;
  lookup.runtime_address_ranges = ranges;
  lookup.runtime_address_range_count = 2;
  for (unsigned i=0; i<2; ++i) {
    facts[i].kind = M68K_FACT_RUNTIME_ADDRESS_RANGE;
    facts[i].has_runtime_address = 1;
    facts[i].offset = 8+4*i;
    facts[i].size = 4;
    facts[i].runtime_address = 0x1008+4*i;
    ranges[i].fact = &facts[i];
    ranges[i].materialization_cached = ranges[i].materialized = 1;
  }
  /* Independent adjacent views with the same translation are compatible. */
  assert(relative_source_labels_preserve_displacement(&lookup, 0, 8, 12, 4));
  assert(relative_source_labels_preserve_displacement(&lookup, 0, 12, 8, -4));
  facts[1].runtime_address = 0x200c;
  assert(!relative_source_labels_preserve_displacement(&lookup, 0, 8, 12, 4));
  assert(!relative_source_labels_preserve_displacement(&lookup, 0, 12, 8, -4));
  /* One view only; retain numeric payload when one endpoint is unmapped. */
  lookup.runtime_address_range_count = 1;
  facts[0].size = 2; /* avoid source-end continuation at the other endpoint */
  assert(!relative_source_labels_preserve_displacement(&lookup, 0, 8, 12, 4));
  assert(!relative_source_labels_preserve_displacement(&lookup, 0, 12, 8, -4));
  return 0;
}
''')
    executable = tmp_path / 'mapping'
    subprocess.run([compiler, '-std=c11', '-O0', '-I', str(root / 'src'),
                    str(source), str(backend), '-lm', '-lcrypto',
                    f'-Wl,-rpath,{backend.parent}', '-o', str(executable)], check=True,
                   capture_output=True, text=True)
    subprocess.run([str(executable)], check=True, capture_output=True, text=True)
