"""Tests for disassembly output generation helpers.

Tests data region format selection from access patterns (Feature 4)
and app memory offset comment generation (Feature 3).
"""

import struct

from m68k.m68k_executor import analyze
from scripts.gen_disasm import (collect_data_access_sizes,
                                emit_data_region, format_app_offset_comment)


# ── Feature 3: App memory offset comments ────────────────────────────

def test_app_offset_comment_hex():
    """Unnamed d(A6) offset gets hex comment."""
    comment = format_app_offset_comment("move.l  568(a6),d0", 6, {"3286": "app_dos_base"})
    assert comment == "app+$238"


def test_app_offset_comment_named_no_duplicate():
    """Named offset (already substituted) gets no comment."""
    comment = format_app_offset_comment("move.l  app_dos_base(a6),d0", 6, {"3286": "app_dos_base"})
    assert comment is None


def test_app_offset_comment_non_base_reg():
    """d(A0) reference does not get app offset comment."""
    comment = format_app_offset_comment("move.l  100(a0),d0", 6, {})
    assert comment is None


# ── Feature 4: Data region format from access patterns ───────────────

def test_collect_word_access():
    """MOVE.W from a data address via d(An) marks it as word-sized."""
    code = b''
    # $00: lea $0C(pc),a0 -> a0 = $02 + $0C = $0E (data table)
    code += struct.pack('>HH', 0x41FA, 0x000C)
    # $04: move.w 0(a0),d0  (reads word from $0E+0)
    code += struct.pack('>HH', 0x3028, 0x0000)
    # $08: move.w 2(a0),d1  (reads word from $0E+2)
    code += struct.pack('>HH', 0x3228, 0x0002)
    # $0C: rts
    code += struct.pack('>H', 0x4E75)
    # $0E: data table (4 words)
    code += struct.pack('>HHHH', 0x0010, 0x0020, 0x0030, 0x0040)

    platform = {"scratch_regs": []}
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    sizes = collect_data_access_sizes(result["blocks"], result.get("exit_states", {}))
    # Address $0E should be marked as word access
    assert sizes.get(0x0E) == 2, (
        f"Expected word access at $0E, got {sizes}")


def test_collect_long_access():
    """MOVE.L from a data address marks it as long-sized."""
    code = b''
    # $00: lea $08(pc),a0 -> a0 = $02 + $08 = $0A
    code += struct.pack('>HH', 0x41FA, 0x0008)
    # $04: move.l (a0),d0  (reads long from $0A)
    code += struct.pack('>H', 0x2010)
    # $06: rts
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>H', 0x4E71)
    # $0A: data (2 longs)
    code += struct.pack('>II', 0x12345678, 0xDEADBEEF)

    platform = {"scratch_regs": []}
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    sizes = collect_data_access_sizes(result["blocks"], result.get("exit_states", {}))
    assert sizes.get(0x0A) == 4, (
        f"Expected long access at $0A, got {sizes}")


def test_emit_data_word_format():
    """Data region with word access emits dc.w instead of dc.b."""
    import io
    code = struct.pack('>HHHH', 0x0010, 0x0020, 0x0030, 0x0040)
    f = io.StringIO()
    access_sizes = {0: 2}  # offset 0 accessed as word
    emit_data_region(f, code, 0, 8, {}, {}, set(),
                     access_sizes=access_sizes)
    output = f.getvalue()
    assert "dc.w" in output, f"Expected dc.w in output, got:\n{output}"
    assert "$0010" in output or "16" in output


def test_emit_data_long_format():
    """Data region with long access emits dc.l instead of dc.b."""
    import io
    code = struct.pack('>II', 0x12345678, 0xDEADBEEF)
    f = io.StringIO()
    access_sizes = {0: 4}
    emit_data_region(f, code, 0, 8, {}, {}, set(),
                     access_sizes=access_sizes)
    output = f.getvalue()
    assert "dc.l" in output, f"Expected dc.l in output, got:\n{output}"
