"""Test the shared analysis pipeline (m68k.analysis)."""

import struct
import tempfile
from pathlib import Path

from m68k.analysis import (analyze_hunk, HunkAnalysis,
                           detect_relocated_segments)


def _make_simple_hunk():
    """Build a minimal code buffer with known structure for testing."""
    code = b''
    # Entry at $00: lea $10(pc),a0; moveq #0,d0; rts
    code += struct.pack('>HH', 0x41FA, 0x000E)   # [0x00] lea $10(pc),a0
    code += struct.pack('>H', 0x7000)              # [0x04] moveq #0,d0
    code += struct.pack('>H', 0x4E75)              # [0x06] rts
    # Padding
    code += b'\x4e\x71' * 5                        # [0x08..$11] nop
    # Data at $12
    code += struct.pack('>HH', 0x0000, 0x0000)     # [0x12] data
    return code


class _FakeReloc:
    """Minimal reloc object for testing."""
    def __init__(self, reloc_type, offsets):
        self.reloc_type = reloc_type
        self.offsets = offsets


def test_analyze_hunk_returns_dataclass():
    """analyze_hunk returns a HunkAnalysis with expected fields."""
    code = _make_simple_hunk()
    result = analyze_hunk(code, relocs=[], hunk_index=0,
                          print_fn=lambda *a: None)
    assert isinstance(result, HunkAnalysis)
    assert result.code is code
    assert result.hunk_index == 0
    assert isinstance(result.blocks, dict)
    assert isinstance(result.exit_states, dict)
    assert isinstance(result.hint_blocks, dict)
    assert isinstance(result.lib_calls, list)
    assert isinstance(result.os_kb, dict)
    assert 0 in result.blocks  # entry point block exists


def test_analyze_hunk_finds_blocks():
    """analyze_hunk discovers basic blocks from entry point 0."""
    code = _make_simple_hunk()
    result = analyze_hunk(code, relocs=[], hunk_index=0,
                          print_fn=lambda *a: None)
    # Should have at least the entry block
    assert len(result.blocks) >= 1
    entry_block = result.blocks[0]
    assert len(entry_block.instructions) >= 1


def test_analyze_hunk_propagates_state():
    """analyze_hunk produces exit states with propagated register values."""
    code = _make_simple_hunk()
    result = analyze_hunk(code, relocs=[], hunk_index=0,
                          print_fn=lambda *a: None)
    assert len(result.exit_states) > 0
    # Entry block exit state should have D0=0 (from moveq #0,d0)
    cpu, _ = result.exit_states[0]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 0


def test_analyze_hunk_identifies_os_calls():
    """analyze_hunk's os_kb is populated from the OS knowledge base."""
    code = _make_simple_hunk()
    result = analyze_hunk(code, relocs=[], hunk_index=0,
                          print_fn=lambda *a: None)
    # OS KB should have structs and _meta with calling convention
    assert "structs" in result.os_kb
    assert "_meta" in result.os_kb
    assert "calling_convention" in result.os_kb["_meta"]


def test_save_load_roundtrip():
    """HunkAnalysis can be saved and loaded with identical data."""
    code = _make_simple_hunk()
    ha = analyze_hunk(code, relocs=[], hunk_index=0,
                      print_fn=lambda *a: None)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.analysis"
        ha.save(path)
        assert path.exists()
        assert path.stat().st_size > 0

        ha2 = HunkAnalysis.load(path, ha.os_kb)
        assert len(ha2.blocks) == len(ha.blocks)
        assert len(ha2.exit_states) == len(ha.exit_states)
        assert ha2.hunk_index == ha.hunk_index
        assert ha2.code == ha.code
        assert ha2.call_targets == ha.call_targets
        assert ha2.os_kb is ha.os_kb  # re-attached, same object


def test_load_rejects_wrong_version():
    """Loading a cache with mismatched version raises ValueError."""
    import pickle
    code = _make_simple_hunk()
    ha = analyze_hunk(code, relocs=[], hunk_index=0,
                      print_fn=lambda *a: None)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.analysis"
        # Save normally first, then tamper with version
        ha.save(path)
        with open(path, "rb") as f:
            _, saved_ha = pickle.load(f)
        with open(path, "wb") as f:
            pickle.dump((999, saved_ha), f)
        import pytest
        with pytest.raises(ValueError, match="version mismatch"):
            HunkAnalysis.load(path, {})


def test_base_addr_resolves_absolute_targets():
    """Analysis with non-zero base_addr resolves absolute branch targets.

    Models Bloodwych: code runs at $0400, uses absolute addresses.
    BSR $0410 should discover the subroutine at file offset $10
    (which maps to runtime address $0410 with base_addr=$0400).
    """
    code = b''
    # $0400: bsr.w $0410
    # BSR.W: PC=$0402, disp=$000E, target=$0402+$000E=$0410
    code += struct.pack('>HH', 0x6100, 0x000E)
    # $0404: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $0406: rts
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>HHHH', 0x4E71, 0x4E71, 0x4E71, 0x4E71)
    # $0410: sub at file offset $10
    code += struct.pack('>H', 0x7000)  # moveq #0,d0
    code += struct.pack('>H', 0x4E75)  # rts

    base = 0x0400
    ha = analyze_hunk(code, [], base_addr=base)

    # Subroutine at $0410 should be discovered
    assert 0x0410 in ha.call_targets, (
        f"Expected call target $0410, got {sorted(hex(t) for t in ha.call_targets)}")
    # Block at $0410 should have exit state
    assert 0x0410 in ha.blocks, (
        f"Expected block at $0410, got {sorted(hex(a) for a in ha.blocks)[:10]}")


def test_base_addr_with_code_start():
    """Analysis with code_start skips bootstrap prefix.

    Models Bloodwych: first $5C bytes are bootstrap (copy loop),
    real code starts at file offset $5C running at address $0400.
    """
    bootstrap = b'\x4e\x71' * 10  # 20 bytes of NOP (fake bootstrap)
    real_code = b''
    # $0400 (file offset $14): moveq #1,d0
    real_code += struct.pack('>H', 0x7001)
    # $0402: rts
    real_code += struct.pack('>H', 0x4E75)

    full_data = bootstrap + real_code
    base = 0x0400
    code_start = len(bootstrap)

    ha = analyze_hunk(full_data, [], base_addr=base,
                      code_start=code_start)

    # Entry block should be at $0400 (not $0000)
    assert base in ha.blocks, (
        f"Expected block at ${base:04X}, got {sorted(hex(a) for a in ha.blocks)[:10]}")
    # Should have exit state with D0=1
    assert base in ha.exit_states
    cpu, _ = ha.exit_states[base]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 1


# ── Auto-detect relocated segments ───────────────────────────────────

def test_detect_copy_and_jump():
    """Detect copy loop followed by JMP to destination.

    Bootstrap:
        $00: lea     $1C(pc),a6     ; source = $1E
        $04: lea     $0400,a0       ; dest = $0400
        $0A: moveq   #9,d0          ; 10 bytes
    loop:
        $0C: move.b  (a6)+,(a0)+    ; copy
        $0E: dbf     d0,loop
        $12: jmp     $0400           ; enter payload
    payload ($1E in file, runs at $0400):
        $1E: moveq   #42,d0
        $20: rts
    """
    code = b''
    # $00: lea $1C(pc),a6 -> a6 = $02 + $1C = $1E
    code += struct.pack('>HH', 0x4DFA, 0x001C)
    # $04: lea $0400,a0
    code += struct.pack('>HHH', 0x41F9, 0x0000, 0x0400)
    # $0A: moveq #9,d0
    code += struct.pack('>H', 0x7009)
    # $0C: move.b (a6)+,(a0)+
    code += struct.pack('>H', 0x10DE)
    # $0E: dbf d0,$0C (disp = $0C - $10 = -4)
    code += struct.pack('>HH', 0x51C8, 0xFFFC)
    # $12: jmp $0400
    code += struct.pack('>HHH', 0x4EF9, 0x0000, 0x0400)
    # padding to $1E
    code += struct.pack('>HH', 0x4E71, 0x4E71)
    # $1E: payload
    code += struct.pack('>H', 0x702A)  # moveq #42,d0
    code += struct.pack('>H', 0x4E75)  # rts

    segments = detect_relocated_segments(code)
    assert len(segments) >= 1, (
        f"Expected at least 1 relocated segment, got {segments}")
    seg = segments[0]
    assert seg["file_offset"] == 0x1E, (
        f"Expected file_offset=$1E, got ${seg['file_offset']:X}")
    assert seg["base_addr"] == 0x400, (
        f"Expected base_addr=$400, got ${seg['base_addr']:X}")


def test_detect_no_copy_returns_empty():
    """Normal hunk (no copy pattern) returns no relocated segments."""
    code = b''
    code += struct.pack('>H', 0x7000)  # moveq #0,d0
    code += struct.pack('>H', 0x4E75)  # rts

    segments = detect_relocated_segments(code)
    assert segments == []


def _make_relocated_hunk():
    """Build a minimal relocated binary: bootstrap + payload.

    File layout:
        $00-$17: bootstrap (LEA source, LEA dest, copy loop, JMP $0400)
        $18-$1B: padding (NOP)
        $1C-$1F: payload source (moveq #42,d0; rts)

    Runtime layout (after bootstrap copies payload):
        $0400: moveq #42,d0  (copied from file $1C)
        $0402: rts
    """
    code = b''
    # $00: lea $1A(pc),a6 -> a6 = $02 + $1A = $1C (payload source)
    code += struct.pack('>HH', 0x4DFA, 0x001A)
    # $04: lea $0400,a0  (dest)
    code += struct.pack('>HHH', 0x41F9, 0x0000, 0x0400)
    # $0A: moveq #3,d0  (4 bytes: DBF loops 4 times)
    code += struct.pack('>H', 0x7003)
    # $0C: move.b (a6)+,(a0)+
    code += struct.pack('>H', 0x10DE)
    # $0E: dbf d0,$0C
    code += struct.pack('>HH', 0x51C8, 0xFFFC)
    # $12: jmp $0400
    code += struct.pack('>HHH', 0x4EF9, 0x0000, 0x0400)
    # padding to $1C
    code += struct.pack('>HH', 0x4E71, 0x4E71)
    # $1C: payload bytes (copied to $0400 at runtime)
    code += struct.pack('>H', 0x702A)  # moveq #42,d0
    code += struct.pack('>H', 0x4E75)  # rts
    return code


def test_copy_and_jump_flat_image():
    """Bootstrap copies payload to higher address and JMPs to it.

    analyze_hunk builds a flat runtime image for analysis, but the
    output blocks must be at the original file offset (not the runtime
    address).  Flat-image blocks at $0400 are filtered out — the same
    code is at file offset $1C.
    """
    code = _make_relocated_hunk()
    ha = analyze_hunk(code, [])

    # Bootstrap at $00 should be analyzed
    assert 0 in ha.blocks, (
        f"Bootstrap block at $0000 missing, "
        f"got {sorted(hex(a) for a in ha.blocks)[:10]}")
    # Payload at file offset $1C should be core (not at runtime $0400)
    assert 0x1C in ha.blocks, (
        f"Payload at file offset $001C missing, "
        f"got {sorted(hex(a) for a in ha.blocks)[:10]}")
    # Flat-image block at $0400 should be filtered out
    assert 0x0400 not in ha.blocks, (
        f"Flat-image block at $0400 should be excluded")
    # The payload block at file offset should contain moveq #42
    if 0x1C in ha.exit_states:
        cpu, _ = ha.exit_states[0x1C]
        assert cpu.d[0].is_known and cpu.d[0].concrete == 42, (
            f"D0 at $001C should be 42 (payload), got {cpu.d[0]}")


def _make_two_stage_relocated_hunk():
    """Build a two-stage relocated binary (models Bloodwych's bootstrap).

    Stage 1 (bootstrap $00-$1F):
        Copy trap handler stub from $20 to $90, set A6 to payload
        source ($34), TRAP #0 (flow-terminating).

    Stage 2 (trap handler, file offset $20, runs at $90):
        Copy payload from A6 ($34) to $0400, JMP $0400.

    Payload (file offset $34):
        moveq #42,d0; rts

    Key: the payload at $34 is only reachable via the TWO-STAGE
    copy (bootstrap sets A6, handler uses A6).  Unlike the simple
    case where the copy source IS the secondary entry, here $34
    is the file_offset but NOT a secondary entry — $20 is.
    """
    code = b''
    # $00: lea $1E(pc),a0 -> a0 = $02 + $1E = $20 (handler source)
    code += struct.pack('>HH', 0x41FA, 0x001E)
    # $04: lea $90,a1 -> a1 = $90 (handler dest)
    code += struct.pack('>HHH', 0x43F9, 0x0000, 0x0090)
    # $0A: moveq #19,d0 -> copy 20 bytes
    code += struct.pack('>H', 0x7013)
    # $0C: move.b (a0)+,(a1)+
    code += struct.pack('>H', 0x12D8)
    # $0E: dbf d0,$0C (disp = $0C - $10 = -4)
    code += struct.pack('>HH', 0x51C8, 0xFFFC)
    # $12: lea $20(pc),a6 -> a6 = $14 + $20 = $34 (payload source)
    code += struct.pack('>HH', 0x4DFA, 0x0020)
    # $16: nop padding (8 bytes, replaces trap vector setup)
    code += struct.pack('>HHHH', 0x4E71, 0x4E71, 0x4E71, 0x4E71)
    # $1E: trap #0
    code += struct.pack('>H', 0x4E40)
    # -- handler source ($20, 20 bytes, runs at $90) --
    # $20: lea $0400,a0
    code += struct.pack('>HHH', 0x41F9, 0x0000, 0x0400)
    # $26: moveq #3,d0 (4 bytes)
    code += struct.pack('>H', 0x7003)
    # $28: move.b (a6)+,(a0)+
    code += struct.pack('>H', 0x10DE)
    # $2A: dbf d0,$28 (disp = $28 - $2C = -4)
    code += struct.pack('>HH', 0x51C8, 0xFFFC)
    # $2E: jmp $0400
    code += struct.pack('>HHH', 0x4EF9, 0x0000, 0x0400)
    # -- payload source ($34) --
    # $34: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $36: rts
    code += struct.pack('>H', 0x4E75)
    return code  # 56 bytes ($38)


def test_reloc_source_is_core_simple():
    """Single-stage relocation: source offset is already a core entry.

    In the simple case (direct copy + JMP), the copy source register
    value becomes a secondary entry in detect_relocated_segments, so
    it's already in core_entries.  This is the baseline.
    """
    code = _make_relocated_hunk()
    ha = analyze_hunk(code, [])

    assert 0x1C in ha.blocks, (
        f"Payload at file offset $001C should be a core block, "
        f"got core={sorted(hex(a) for a in ha.blocks)}")
    assert 0x1C not in ha.hint_blocks, (
        f"Payload at file offset $001C should NOT be a hint block")


def test_reloc_source_is_core_two_stage():
    """Two-stage relocation: payload source must be core, not hints.

    In the Bloodwych pattern (bootstrap -> TRAP -> handler copies
    payload), the payload file offset ($34) differs from the secondary
    entry ($20 = handler source).  The file_offset from
    detect_relocated_segments must be added as a core entry so
    the .s output reproduces the original file layout as code.
    """
    code = _make_two_stage_relocated_hunk()
    ha = analyze_hunk(code, [])

    # Verify detection found the right segment
    segs = detect_relocated_segments(code)
    assert len(segs) >= 1, f"Expected relocated segment, got {segs}"
    assert segs[0]["file_offset"] == 0x34, (
        f"Expected file_offset=$34, got ${segs[0]['file_offset']:X}")

    # Payload at file offset $34 should be CORE (not hint)
    assert 0x34 in ha.blocks, (
        f"Payload at file offset $0034 should be a core block, "
        f"got core={sorted(hex(a) for a in ha.blocks)}, "
        f"hints={sorted(hex(a) for a in ha.hint_blocks)}")
    assert 0x34 not in ha.hint_blocks, (
        f"Payload at $0034 should NOT be a hint block")


def test_secondary_entries_are_core():
    """Secondary entries (handler stubs) should be core blocks.

    In the two-stage pattern, the handler at $20 is a secondary entry
    discovered by detect_relocated_segments.  It must be analyzed as
    core (with propagation) so the handler code is properly disassembled.
    """
    code = _make_two_stage_relocated_hunk()
    ha = analyze_hunk(code, [])

    # Handler at $20 should be core
    assert 0x20 in ha.blocks, (
        f"Handler at $0020 should be a core block, "
        f"got core={sorted(hex(a) for a in ha.blocks)}")
    assert 0x20 not in ha.hint_blocks, (
        f"Handler at $0020 should NOT be a hint block")

    # Handler's JMP target ($0400) is beyond the 56-byte binary,
    # so no block there — but the handler itself is properly analyzed.
    # The handler may be split into multiple blocks (copy loop boundary).
    handler_instrs = sum(
        len(b.instructions) for a, b in ha.blocks.items()
        if 0x20 <= a < 0x34)
    assert handler_instrs >= 5, (
        f"Handler blocks ($20-$33) should have >= 5 instructions, "
        f"got {handler_instrs}")


def test_no_runtime_blocks_in_core():
    """No core blocks at the relocated runtime address.

    Without a flat image, the runtime address ($0400) is beyond the
    test binary's size, so the executor can't follow JMP $0400.
    The payload is analyzed at its original file offset instead.
    """
    # Simple case: 32-byte binary, runtime addr $0400 is beyond code
    code = _make_relocated_hunk()
    ha = analyze_hunk(code, [])
    assert 0x0400 not in ha.blocks, (
        f"Runtime address $0400 should not be in core blocks, "
        f"got core={sorted(hex(a) for a in ha.blocks)}")

    # Two-stage case: 56-byte binary, runtime addr $0400 is beyond code
    code2 = _make_two_stage_relocated_hunk()
    ha2 = analyze_hunk(code2, [])
    assert 0x0400 not in ha2.blocks, (
        f"Runtime address $0400 should not be in core blocks, "
        f"got core={sorted(hex(a) for a in ha2.blocks)}")


def _assert_no_hint_core_overlap(ha):
    """Assert no hint block overlaps any core block byte range."""
    core_addrs = set()
    for blk in ha.blocks.values():
        for a in range(blk.start, blk.end):
            core_addrs.add(a)
    for addr, hb in ha.hint_blocks.items():
        for a in range(hb.start, hb.end):
            assert a not in core_addrs, (
                f"Hint block ${addr:04X} ({hb.start:X}-{hb.end:X}) "
                f"overlaps with core at ${a:04X}")


def test_hint_blocks_no_core_overlap():
    """Hint blocks must not overlap with core blocks.

    The overlap filter in analyze_hunk removes hints that span into
    core block ranges.  Verify for both single-stage and two-stage
    relocated binaries (two-stage has more gap regions where the
    hint scanner may produce overlapping blocks).
    """
    _assert_no_hint_core_overlap(analyze_hunk(_make_relocated_hunk(), []))
    _assert_no_hint_core_overlap(
        analyze_hunk(_make_two_stage_relocated_hunk(), []))
