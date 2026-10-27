"""A known app cursor uses the full decoded span before a bounded access."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact, derived_refs


def frame_artifact(tmp_path, body, *, seeded=False, extent=16):
    return cursor_artifact(tmp_path, body, source_reg='a2' if seeded else 'a6',
        seeded=seeded, regions=False, metadata_extra=dict(rsset_layout_regions=[
            dict(layout_name='app', offset=0x9C, size=extent,
                 storage_kind='byte_array', symbol='saved_frame')]))


@pytest.mark.parametrize('seeded', [False, True])
def test_predecrement_frame_then_postincrement_read_keeps_exact_cursor(tmp_path, seeded):
    source = 'a2' if seeded else 'a6'
    artifact, original = frame_artifact(tmp_path, f'lea.l $AC({source}),a3\n'
        ' movem.l d0-d1/a1-a2,-(a3)\n'
        ' movem.l (a3)+,d2-d3/a1-a2\n move.w -16(a3),d4', seeded=seeded)
    try:
        refs = [r for r in derived_refs(artifact) if r['access'] != 'address']
        assert [r['displacement'] for r in refs] == [0x9C, 0x9C, 0x9C]
        assert [r['base_displacement'] for r in refs] == [0xAC, 0x9C, 0xAC]
        assert [r['operand_displacement'] for r in refs] == [-16, 0, -16]
        assert [r['data_access_size'] for r in refs] == [16, 16, 2]
        assert [r['element_width'] for r in refs] == [4, 4, 2]
        assert [r['transfer_count'] for r in refs] == [4, 4, 1]
        assert [r['access'] for r in refs] == ['write', 'read', 'read']
        assert len({r['base_evidence'] for r in refs}) == 1
        assert refs[0]['base_evidence'] == ('register_state' if seeded else 'a6_fallback')
        for ref in refs:
            row = artifact.row_for_source_offset(section_index=0, offset=ref['offset'])
            projected, = [x for x in row['app_slot_refs'] if x.get('derived')]
            assert projected['data_access_size'] == ref['data_access_size']
            assert projected['displacement'] == ref['displacement']
        from amiga_reversing.disasm import c_backend
        rendered, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered,
            include_dir=c_backend.PROJECT_ROOT / 'ext/amiga_includes/ndk_2.0/include')
        assert rebuilt == original
    finally:
        artifact.close()


@pytest.mark.parametrize(('operation', 'size', 'access'), [
    ('move.b d0,-(a3)', 1, 'write'),
    ('move.w d0,-(a3)', 2, 'write'),
    ('move.l d0,-(a3)', 4, 'write'),
    ('move.l -(a3),d0', 4, 'read'),
    ('addq.w #1,-(a3)', 2, 'read-write'),
    ('movem.w d0-d1,-(a3)', 4, 'write'),
    ('movem.l d0-d1,-(a3)', 8, 'write'),
    ('movem.l d0-d7/a0-a2/a4-a7,-(a3)', 60, 'write'),
])
def test_full_span_is_applied_once_before_access(tmp_path, operation, size, access):
    artifact, _ = frame_artifact(tmp_path,
        f'lea.l ${0x9C + size:X}(a2),a3\n {operation}\n move.b (a3),d5', seeded=True, extent=size)
    try:
        refs = [r for r in derived_refs(artifact) if r['access'] != 'address']
        assert [r['displacement'] for r in refs] == [0x9C, 0x9C]
        assert [r['data_access_size'] for r in refs] == [size, 1]
        assert refs[0]['operand_displacement'] == -size
        assert refs[0]['access'] == access
    finally:
        artifact.close()


@pytest.mark.parametrize(('end', 'extent'), [(0x9E, 2), (0xA0, 4)])
def test_declared_frame_end_does_not_disambiguate_unknown_hardware_base(tmp_path, end, extent):
    # Both offsets are hardware-register candidates. A one-past address is not
    # inside the declared app owner and cannot establish an otherwise unknown A6.
    artifact, _ = frame_artifact(tmp_path,
        f'lea.l ${end:X}(a6),a3\n move.w d0,-(a3)', extent=extent)
    try:
        assert not [r for r in derived_refs(artifact) if r['access'] != 'address']
    finally:
        artifact.close()


@pytest.mark.parametrize('body', [
    # The whole footprint, not only its starting address, needs an owner.
    'lea.l $A4(a6),a3\n movem.l d0-d3,-(a3)',
    'lea.l $B0(a6),a3\n movem.l d0-d3,-(a3)',
    'lea.l 4(a6),a3\n movem.l d0-d3,-(a3)',
    # Unknown, clobbered, indexed, shared-update and explicit-register conflicts.
    'movem.l d0-d3,-(a3)',
    'lea.l $AC(a6),a3\n movea.l d0,a3\n movem.l d0-d3,-(a3)',
    'lea.l $AC(a6),a3\n movem.l d0-d3,0(a3,d4.w)',
    'lea.l $AC(a6),a3\n move.l -(a3),-(a3)',
    'lea.l $AC(a6),a3\n move.l a3,-(a3)',
    'lea.l $AC(a6),a3\n movem.l d0-d1/a3,-(a3)\n move.w (a3),d0',
    'lea.l $9C(a6),a3\n movem.l (a3)+,d0/a3\n move.w (a3),d0',
    'movea.l #$DFF000,a6\n lea.l $AC(a6),a3\n movem.l d0-d3,-(a3)',
])
def test_unknown_ambiguous_or_unowned_spans_refuse(tmp_path, body):
    artifact, _ = frame_artifact(tmp_path, body)
    try:
        assert not [r for r in derived_refs(artifact) if r['access'] != 'address']
        assert not artifact.analysis_payload()[0]['incomplete_analysis']
    finally:
        artifact.close()


def test_movem_frame_slot_order_and_cursor_against_cpu_oracle():
    """Synthetic CPU evidence for the four stored register roles, not gameplay."""
    machine68k = pytest.importorskip('machine68k')
    from amiga_reversing.disasm import c_backend
    code, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        ' SECTION code,code\n ORG $1000\n'
        ' movem.l d0-d1/a1-a2,-(a3)\n moveq #0,d0\n moveq #0,d1\n'
        ' suba.l a1,a1\n suba.l a2,a2\n movem.l (a3)+,d0-d1/a1-a2\n nop\n')
    cpu = machine68k.Machine(machine68k.CPUType.M68000, 64)
    cpu.mem.w_block(0x1000, code)
    registers = [machine68k.Register.D0, machine68k.Register.D1,
                 machine68k.Register.A1, machine68k.Register.A2]
    values = [0x12345678, 0x00000366, 0x00000D9E, 0x00012F80]
    for reg, value in zip(registers, values):
        cpu.cpu.w_reg(reg, value)
    cpu.cpu.w_reg(machine68k.Register.A3, 0x3010)
    cpu.cpu.w_reg(machine68k.Register.A7, 0xF000)
    cpu.cpu.w_sr(0x2700)
    cpu.cpu.w_pc(0x1000)
    observed = []

    class Finished(Exception):
        pass

    def hook(pc):
        observed.append(pc)
        assert len(observed) <= 8
        if pc == 0x1004:
            assert cpu.cpu.r_reg(machine68k.Register.A3) == 0x3000
            assert cpu.mem.r_block(0x3000, 16) == b''.join(v.to_bytes(4, 'big') for v in values)
        if pc == 0x1000 + len(code) - 2:
            raise Finished

    cpu.cpu.set_instr_hook_callback(hook)
    with pytest.raises(Finished):
        cpu.cpu.execute(1000)
    assert 0x1004 in observed
    assert [cpu.cpu.r_reg(r) for r in registers] == values
    assert cpu.cpu.r_reg(machine68k.Register.A3) == 0x3010
