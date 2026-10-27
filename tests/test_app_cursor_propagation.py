"""An app-relative address does not require a pointee struct to propagate."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_native_untyped_app_cursor_transfer_and_refusal(tmp_path):
    compiler = shutil.which('cc')
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', ROOT / 'src/build/libamiga_backend.so'))
    if compiler is None or not backend.exists():
        pytest.skip('host compiler and native backend required')
    implementation = os.environ.get('APP_CURSOR_LOOKUP_SOURCE', 'm68k_analysis_render_lookup.c')
    source = tmp_path / 'cursor.c'
    source.write_text('#include "' + implementation + '"\n' + r'''
#include <assert.h>
#include "m68k_plain_parse.h"
static void lea(M68kRenderTypedState *state, M68kRenderLookup *lookup,
    M68kRenderPlatformState *platform, unsigned int base, int displacement, unsigned int dest) {
  char text[96];
  M68kInstructionIR instruction;
  snprintf(text, sizeof(text), "lea.l %d(a%u),a%u", displacement, base, dest);
  instruction = m68k_plain_parse_instruction_to_ir(text, M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
  assert(m68k_sim_metadata_for_instruction(&instruction) != NULL);
  typed_state_update_after_instruction(state, lookup, platform, 0, &instruction, NULL, NULL, 0, 0);
}
static void copy(M68kRenderTypedState *state, M68kRenderLookup *lookup,
    M68kRenderPlatformState *platform, unsigned int source, unsigned int dest, char size) {
  char text[96];
  M68kInstructionIR instruction;
  snprintf(text, sizeof(text), "movea.%c a%u,a%u", size, source, dest);
  instruction = m68k_plain_parse_instruction_to_ir(text, M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
  assert(m68k_sim_metadata_for_instruction(&instruction) != NULL);
  typed_state_update_after_instruction(state, lookup, platform, 0, &instruction, NULL, NULL, 0, 0);
}
int main(void) {
  M68kRenderLookup lookup = {0};
  M68kRenderTypedState state = {0}, other;
  M68kRenderPlatformState platform = {0};
  lea(&state, &lookup, &platform, 6, 0xBC6, 4);
  assert(state.app_addr_regs[4].known);
  assert(state.app_addr_regs[4].displacement == 0xBC6);
  assert(!state.addr_regs[4].known); /* no pointee type was invented */
  lea(&state, &lookup, &platform, 4, 0x78, 5);
  assert(state.app_addr_regs[5].known);
  assert(state.app_addr_regs[5].displacement == 0xC3E);
  assert(state.app_addr_regs[5].base_evidence_kind == M68K_APP_SLOT_BASE_A6_FALLBACK);
  assert(!state.addr_regs[5].known);
  assert(!state.app_addr_regs[0].known);
  copy(&state, &lookup, &platform, 5, 2, 'l');
  assert(state.app_addr_regs[2].known && state.app_addr_regs[2].displacement == 0xC3E);
  assert(state.app_addr_regs[2].base_evidence_kind == M68K_APP_SLOT_BASE_A6_FALLBACK);
  copy(&state, &lookup, &platform, 5, 1, 'w');
  assert(!state.app_addr_regs[1].known);
  lea(&state, &lookup, &platform, 4, 0x78, 4); /* self-LEA reads before overwrite */
  assert(state.app_addr_regs[4].known && state.app_addr_regs[4].displacement == 0xC3E);
  state.app_addr_regs[4].displacement = INT16_MAX;
  lea(&state, &lookup, &platform, 4, 1, 5);
  assert(!state.app_addr_regs[5].known);
  memset(&state, 0, sizeof(state));
  lea(&state, &lookup, &platform, 4, 0x78, 5);
  assert(!state.app_addr_regs[5].known);
  m68k_bitset_u32_set(&platform.address_hardware_base_known, 6);
  lea(&state, &lookup, &platform, 6, 0xBC6, 5);
  assert(!state.app_addr_regs[5].known);
  memset(&platform, 0, sizeof(platform));
  lea(&state, &lookup, &platform, 6, 0xBC6, 4);
  other = state;
  other.app_addr_regs[4].base_evidence_kind = M68K_APP_SLOT_BASE_REGISTER_STATE;
  typed_state_merge_into(&state, &other, NULL);
  assert(state.app_addr_regs[4].known);
  assert(state.app_addr_regs[4].base_evidence_kind == M68K_APP_SLOT_BASE_UNSPECIFIED);
  memset(&other, 0, sizeof(other));
  typed_state_merge_into(&state, &other, NULL);
  assert(!state.app_addr_regs[4].known);
  {
    M68kInstructionIR direct = m68k_plain_parse_instruction_to_ir(
      "move.w #19,d7", M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
    M68kInstructionIR indirect = m68k_plain_parse_instruction_to_ir(
      "move.w #19,(a0)", M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
    assert(instruction_operand_writes_register_from_metadata(&direct, 1));
    assert(!instruction_operand_writes_register_from_metadata(&indirect, 1));
  }
  {
    M68kInstructionIR store = m68k_plain_parse_instruction_to_ir(
      "movem.l d0-d1,0(a7)", M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
    M68kInstructionIR load = m68k_plain_parse_instruction_to_ir(
      "movem.w (a5)+,a4-a5", M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
    M68kInstructionIR address = m68k_plain_parse_instruction_to_ir(
      "lea.l 4(a0),a1", M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
    uint8_t width = 0U, count = 0U, span = 0U;
    assert(platform_operand_memory_span(&store, 1U, &width, &count, &span));
    assert(width == 4U && count == 2U && span == 8U);
    assert(platform_operand_memory_span(&load, 0U, &width, &count, &span));
    assert(width == 2U && count == 2U && span == 4U);
    assert(platform_operand_register_write_mask(&load, 1U) == 0x3000U);
    assert(platform_operand_register_write_mask(&load, 0U) == 0x2000U);
    assert(platform_operand_register_write_mask(&store, 1U) == 0U);
    assert(!platform_operand_memory_span(&address, 0U, &width, &count, &span));
  }
  /* Multi-transfer affine cursors must not silently advance by one WORD. */
  memset(&state, 0, sizeof(state));
  state.memory_base_regs[0].known = 1;
  state.memory_base_regs[0].offset = 100;
  {
    M68kInstructionIR multi = m68k_plain_parse_instruction_to_ir(
      "movem.w (a0)+,d0-d2", M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
    typed_state_update_after_instruction(&state, &lookup, &platform, 0, &multi, NULL, NULL, 0, 0);
    assert(!state.memory_base_regs[0].known);
  }
  return 0;
}
''')
    executable = tmp_path / 'cursor'
    built = subprocess.run([compiler, '-Isrc', '-D_POSIX_C_SOURCE=200809L', '-std=c11', '-O0',
                            str(source), str(backend), f'-Wl,-rpath,{backend.parent}', '-o', str(executable)],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert built.returncode == 0, built.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


def cursor_artifact(tmp_path, body, *, source_reg='a6', regions=True, seeded=False, metadata_extra=None):
    import json
    from amiga_reversing.disasm import c_backend
    from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
    text = ' SECTION code,code\n ORG $1000\n' + body + '\n rts\n'
    original, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)
    binary = tmp_path / 'input.bin'
    binary.write_bytes(original)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x1000, entrypoint=0x1000,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'analysis')
    metadata = tmp_path / 'metadata.json'
    owners = [dict(layout_name='app', offset=offset, size=120, storage_kind='byte_array', symbol=symbol)
              for offset, symbol in [(0xBC6, 'world_points'), (0xC3E, 'previous_view_points')]]
    payload = dict(rsset_layout_regions=owners if regions else [],
        entry_register_seeds=[dict(hunk=0, entry_offset=0, register=source_reg.upper(),
            kind='library_base', library_name='__amiga_app_base__')] if seeded else [])
    payload.update(metadata_extra or {})
    metadata.write_text(json.dumps(payload))
    artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)[2]
    return artifact, original


def derived_refs(artifact):
    analysis, _ = artifact.analysis_payload()
    return [r for r in analysis['sections'][0]['app_slot_refs'] if r.get('derived')]


@pytest.mark.parametrize(('operation', 'access', 'width'), [
    ('move.l (a5),d0', 'read', 4),
    ('move.w d0,4(a5)', 'write', 2),
    ('addq.w #1,4(a5)', 'read-write', 2),
])
@pytest.mark.parametrize('seeded', [False, True])
def test_derived_app_accesses_keep_target_operand_and_base_coordinates(tmp_path, operation, access, width, seeded):
    from amiga_reversing.disasm import c_backend
    source_reg = 'a2' if seeded else 'a6'
    body = f' lea.l $BC6({source_reg}),a4\n lea.l $78(a4),a5\n {operation}'
    artifact, original = cursor_artifact(tmp_path, body, source_reg=source_reg, seeded=seeded)
    try:
        refs = derived_refs(artifact)
        address, = [r for r in refs if r['access'] == 'address']
        assert address['displacement'] == 0xC3E
        assert address['base_displacement'] == 0xBC6
        assert address['operand_displacement'] == 0x78
        assert address['base_register'] == 'A4'
        assert address['data_access_size'] == 0
        memory, = [r for r in refs if r['access'] != 'address']
        assert memory['access'] == access
        assert memory['displacement'] == 0xC3E + (0 if access == 'read' else 4)
        assert memory['base_displacement'] == 0xC3E
        assert memory['operand_displacement'] == (0 if access == 'read' else 4)
        assert memory['data_access_size'] == width
        assert all(r['base_evidence'] == ('register_state' if seeded else 'a6_fallback') for r in refs)
        for ref in refs:
            row = artifact.row_for_source_offset(section_index=0, offset=ref['offset'])
            item, = [r for r in row['app_slot_refs'] if r.get('derived')]
            for key in ['displacement', 'base_register', 'base_displacement', 'operand_displacement',
                        'data_access_size', 'base_evidence']:
                assert item[key] == ref[key]
        rendered, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered,
            include_dir=c_backend.PROJECT_ROOT / 'ext/amiga_includes/ndk_2.0/include')
        assert rebuilt == original
    finally:
        artifact.close()


@pytest.mark.parametrize('tail', [
    'lea.l $78(a4),a4\n move.l (a4),d0',
    'lea.l $78(a4),a5\n movea.l a5,a2\n move.l (a2),d0',
])
def test_self_and_full_register_copy_retain_untyped_app_address(tmp_path, tail):
    artifact, _ = cursor_artifact(tmp_path, 'lea.l $BC6(a6),a4\n' + tail)
    try:
        reads = [r for r in derived_refs(artifact) if r['access'] == 'read']
        assert len(reads) == 1 and reads[0]['displacement'] == 0xC3E
    finally:
        artifact.close()


@pytest.mark.parametrize('case', ['unknown', 'hardware', 'loaded', 'call', 'word_copy',
                                 'numeric', 'overflow', 'overrun', 'striped'])
def test_unsupported_or_unproved_cursor_use_is_not_a_scalar_app_access(tmp_path, case):
    prefix = 'lea.l $BC6(a6),a4\n'
    tail = 'lea.l $78(a4),a5\n move.l (a5),d0'
    if case == 'unknown': prefix = 'lea.l $BC6(a2),a4\n'
    elif case == 'hardware': prefix = 'lea.l $DFF000.l,a6\n' + prefix
    elif case == 'loaded': prefix += 'movea.l (a0),a4\n'
    elif case == 'call': prefix += 'jsr (a0)\n'
    elif case == 'word_copy': tail = 'lea.l $78(a4),a5\n move.w a5,d1\n movea.l d1,a2\n move.l (a2),d0'
    elif case == 'numeric': prefix = 'movea.l #$BC6,a4\n'
    elif case == 'overflow': tail = 'lea.l $7FFF(a4),a5\n move.l (a5),d0'
    elif case == 'overrun': tail = 'lea.l $78(a4),a5\n move.l 118(a5),d0'
    elif case == 'striped': tail = 'lea.l $78(a4),a5\n movep.l 0(a5),d0'
    artifact, _ = cursor_artifact(tmp_path, prefix + tail)
    try:
        assert not [r for r in derived_refs(artifact) if r['access'] != 'address']
    finally:
        artifact.close()


@pytest.mark.parametrize('same', [False, True])
def test_cfg_join_requires_the_same_app_address_on_both_inputs(tmp_path, same):
    other = '$78' if same else '$70'
    body = f'''lea.l $BC6(a6),a4
 tst.w d0
 beq other
 lea.l $78(a4),a5
 bra joined
other:
 lea.l {other}(a4),a5
joined:
 move.l (a5),d0'''
    artifact, _ = cursor_artifact(tmp_path, body)
    try:
        reads = [r for r in derived_refs(artifact) if r['access'] == 'read']
        assert bool(reads) == same
        if same: assert reads[0]['displacement'] == 0xC3E
    finally:
        artifact.close()


def test_no_declared_owner_or_unfinished_worklist_cannot_admit_derived_access(tmp_path, monkeypatch):
    body = 'lea.l $BC6(a6),a4\n lea.l $78(a4),a5\n move.l (a5),d0'
    artifact, _ = cursor_artifact(tmp_path, body, regions=False, seeded=True)
    try:
        assert not derived_refs(artifact)
    finally:
        artifact.close()
    monkeypatch.setenv('AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS', '1')
    artifact, _ = cursor_artifact(tmp_path, body)
    try:
        assert not derived_refs(artifact)
        assert artifact.analysis_payload()[0]['incomplete_analysis']
    finally:
        artifact.close()
