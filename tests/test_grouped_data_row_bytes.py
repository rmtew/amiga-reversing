"""Grouped scalar rows expose bytes from their own canonical source interval."""
import json
import subprocess

import pytest

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    assemble_platform_source_text_with_c_backend,
    build_listing_artifact_profile_from_binary_source,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT


@pytest.mark.parametrize('unit', ['word', 'byte'])
def test_grouped_scalar_array_rows_have_exact_source_bytes(tmp_path, monkeypatch, unit):
    data = (b''.join((0x1101 + i * 0x101).to_bytes(2, 'big') for i in range(24))
            if unit == 'word' else bytes(range(0x80, 0xB0)))
    original = bytes.fromhex('6030') + data + bytes.fromhex('4e75')
    binary = tmp_path / 'input.bin'
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    path = tmp_path / 'metadata.json'
    path.write_text(json.dumps({'seeded_entities': [{'addr': 2, 'end': 50, 'hunk': 0,
        'type': 'data', 'subtype': 'array', 'unit': unit, 'name': 'scalar_values'}]}))
    _, _, artifact = build_listing_artifact_profile_from_binary_source(source, metadata_path=path,
        project_root=PROJECT_ROOT)
    try:
        rows = [artifact.row_for_source_offset(section_index=0, offset=offset) for offset in [2, 18, 34]]
        assert len({row['start_offset'] for row in rows}) == 3
        for row in rows:
            start, end = row['start_offset'], row['end_offset']
            assert row['bytes'] == original[start:end].hex()
            assert bytes.fromhex(row['bytes']) == original[start:end]
        assert rows[1]['bytes'] != rows[0]['bytes']
        assert rows[2]['bytes'] != rows[1]['bytes']
        if unit == 'word':
            from types import SimpleNamespace

            from amiga_reversing.disasm import server

            # The public preparation guard consumes actual native bytes from an
            # interior WORD of row two, against its current canonical owner.
            owner_metadata = {'data_block_layouts': [{'layout_id': 'array', 'hunk': 0,
                'source_start': 2, 'source_end': 50,
                'elements': [{'offset': 0, 'width': 48, 'kind': 'array',
                              'array_count': 24, 'array_stride': 2}]}]}
            monkeypatch.setattr(server, '_command_preparation_metadata', lambda _: owner_metadata)
            ref = {'layout_id': 'array', 'offset': 20, 'width': 2,
                   'source_value': int.from_bytes(original[22:24], 'big')}
            server._validate_data_block_runtime_ref_source_bytes(
                SimpleNamespace(target_dir=tmp_path), artifact, ref)
            with pytest.raises(ValueError, match='source_value must match'):
                server._validate_data_block_runtime_ref_source_bytes(
                    SimpleNamespace(target_dir=tmp_path), artifact,
                    {**ref, 'source_value': int.from_bytes(original[6:8], 'big')})
        rendered, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = assemble_platform_source_text_with_c_backend('amiga-raw', rendered,
            project_root=PROJECT_ROOT)
        assert rebuilt == original
        assembly_path, output = tmp_path / 'rendered.s', tmp_path / 'oracle.bin'
        assembly_path.write_text(rendered)
        oracle = subprocess.run([str(PROJECT_ROOT / 'tools' / 'vasmm68k_mot.exe'), '-quiet', '-Fbin',
            '-o', str(output), str(assembly_path)], capture_output=True, text=True, timeout=10, check=False)
        assert oracle.returncode == 0, oracle.stdout + oracle.stderr
        assert output.read_bytes() == original
    finally:
        artifact.close()


def test_data_row_refill_discards_unprovable_inherited_cache(tmp_path):
    """Exercise the real private finalizer without adding a production test hook."""
    import shutil
    import sys

    compiler = shutil.which('cc')
    if sys.platform != 'linux' or compiler is None:
        pytest.skip('native finalizer bridge uses the Linux host C toolchain')
    bridge = tmp_path / 'row_refill.c'
    bridge.write_text(r'''#include "m68k_render_ir.c"
#include <assert.h>

int main(void) {
  unsigned int scenario;
  const uint8_t stale[] = {0xde, 0xad, 0xbe, 0xef};
  const uint8_t actual[] = {1, 2, 3, 4};
  for (scenario = 0; scenario < 5; ++scenario) {
    M68kRenderIRPreview preview;
    M68kRenderPlanRow *row = NULL;
    M68kDecodeIR decode;
    M68kDecodeSectionIR section;
    memset(&decode, 0, sizeof(decode));
    memset(&section, 0, sizeof(section));
    m68k_render_ir_preview_init(&preview);
    assert(m68k_render_plan_append_text_row(&preview.asm_source_rows,
      M68K_RENDER_PLAN_ROW_DATA, 0, "\tdc.b $01,$02,$03,$04\n", &row) == 0);
    m68k_render_plan_row_set_source_range(row, scenario == 0 ? 7 : 0,
      scenario == 2 ? 4 : 0, scenario == 3 ? 0 : 4);
    m68k_render_plan_row_set_statement_metadata(row, M68K_STATEMENT_DATA,
      NULL, stale, sizeof(stale));
    assert(row->source_byte_count == 4);
    preview.asm_source_bytes = preview.asm_source_rows.total_bytes;
    section.section_index = 0;
    section.size = sizeof(actual);
    section.data = scenario == 1 ? NULL : actual;
    decode.sections = &section;
    decode.section_count = 1;
    assert(assemble_asm_source_plan_regions(&preview, &decode, 0));
    assert(preview.asm_source_plan.row_count == 1);
    row = &preview.asm_source_plan.rows[0];
    assert(row->source_byte_count == (scenario == 4 ? 4 : 0));
    if (scenario == 4) assert(memcmp(row->source_bytes, actual, 4) == 0);
    assert(strcmp(row->text, "\tdc.b $01,$02,$03,$04\n") == 0);
    m68k_render_ir_preview_destroy(&preview);
  }
  return 0;
}
''')
    executable = tmp_path / 'row_refill'
    build_dir = PROJECT_ROOT / 'src' / 'build'
    compiled = subprocess.run([
        compiler, '-std=c99', '-O0', '-I', str(PROJECT_ROOT / 'src'), str(bridge),
        '-L', str(build_dir), '-lamiga_backend', f'-Wl,-rpath,{build_dir}',
        '-lm', '-o', str(executable),
    ], capture_output=True, text=True, timeout=60, check=False)
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    executed = subprocess.run([str(executable)], capture_output=True, text=True,
                              timeout=10, check=False)
    assert executed.returncode == 0, executed.stdout + executed.stderr
