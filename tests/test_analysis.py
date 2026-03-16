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


def test_copy_and_jump_flat_image():
    """Bootstrap copies payload to higher address and JMPs to it.

    File layout:
        $00-$17: bootstrap (copy loop + JMP $0400)
        $1E-$21: payload source (moveq #42,d0; rts)

    Runtime layout (after copy):
        $00-$17: bootstrap (same)
        $0400:   moveq #42,d0  (copied from file $1E)
        $0402:   rts

    analyze_hunk builds the runtime flat image and analyzes from entry 0.
    The JMP $0400 resolves to the COPIED bytes, not file offset $0400.
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

    ha = analyze_hunk(code, [])

    # Bootstrap at $00 should be analyzed
    assert 0 in ha.blocks, (
        f"Bootstrap block at $0000 missing, "
        f"got {sorted(hex(a) for a in ha.blocks)[:10]}")
    # Payload at $0400 should be analyzed (from flat image with copy applied)
    assert 0x0400 in ha.blocks, (
        f"Payload block at $0400 missing, "
        f"got {sorted(hex(a) for a in ha.blocks)[:10]}")
    # The payload block should contain moveq #42 (from file $1E),
    # NOT whatever random bytes are at file offset $0400
    if 0x0400 in ha.exit_states:
        cpu, _ = ha.exit_states[0x0400]
        assert cpu.d[0].is_known and cpu.d[0].concrete == 42, (
            f"D0 at $0400 should be 42 (from copied payload), "
            f"got {cpu.d[0]}")
