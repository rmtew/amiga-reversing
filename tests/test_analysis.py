"""Test the shared analysis pipeline (m68k.analysis)."""

import struct

from m68k.analysis import analyze_hunk, HunkAnalysis


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
