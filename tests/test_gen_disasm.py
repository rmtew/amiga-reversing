"""Tests for disassembly output generation helpers."""

import io
import struct

from m68k.m68k_executor import analyze, BasicBlock, Instruction
from m68k.kb_util import KB
from scripts.gen_disasm import (build_label_map, collect_data_access_sizes,
                                discover_pc_relative_targets,
                                emit_data_region, format_app_offset_comment,
                                format_ascii_immediate)


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


# ── String detection in data regions ─────────────────────────────────

def test_data_region_detects_embedded_string():
    """Printable ASCII run in data region emits dc.b "text" not hex.

    Models GenAm version string: non-printable prefix then
    "VER: GenAm",0 as a null-terminated string.
    """
    data = bytes([0x94, 0x85, 0xC2]) + b'VER: GenAm\x00' + bytes([0xFF])
    f = io.StringIO()
    emit_data_region(f, data, 0, len(data), {}, {}, set())
    output = f.getvalue()
    assert '"VER: GenAm"' in output, (
        f"Expected quoted string in output, got:\n{output}")
    # The non-printable prefix should be hex
    assert "$94" in output


def test_data_region_short_printable_not_string():
    """Short non-null-terminated printable runs stay as hex."""
    data = bytes([0x41, 0x42, 0x43, 0x44, 0xFF])  # "ABCD" + junk, no null
    f = io.StringIO()
    emit_data_region(f, data, 0, len(data), {}, {}, set())
    output = f.getvalue()
    # 4 printable bytes without null terminator is too short (need 6+)
    assert '"ABCD"' not in output


def test_data_region_short_null_terminated_is_string():
    """Short null-terminated printable runs (4+) ARE strings."""
    data = b'ABCD\x00'
    f = io.StringIO()
    emit_data_region(f, data, 0, len(data), {}, {}, set())
    output = f.getvalue()
    assert '"ABCD"' in output


def test_data_region_null_terminated_string():
    """Null-terminated printable run emits as string with ,0 terminator."""
    data = b'include_longmac\x00'
    f = io.StringIO()
    emit_data_region(f, data, 0, len(data), {}, {}, set())
    output = f.getvalue()
    assert '"include_longmac"' in output
    assert ",0" in output


def test_data_region_mixed_hex_and_string():
    """Data with non-printable bytes, then string, then more non-printable.

    Should emit: dc.b hex... then dc.b "text",0 then dc.b hex...
    """
    data = bytes([0x4A, 0xFB]) + b'hello\x00' + bytes([0xDE, 0xAD])
    f = io.StringIO()
    emit_data_region(f, data, 0, len(data), {}, {}, set())
    output = f.getvalue()
    assert '"hello"' in output
    assert "$4a" in output.lower() or "$4A" in output


# ── ASCII immediate comments ─────────────────────────────────────────

def test_ascii_immediate_longword():
    """4-byte all-printable immediate gets 'ABCD' comment."""
    result = format_ascii_immediate(0x4C494E45)  # 'LINE'
    assert result == "'LINE'"


def test_ascii_immediate_non_printable():
    """Immediate with non-printable byte returns None."""
    result = format_ascii_immediate(0x4C490045)  # 'LI\x00E'
    assert result is None


def test_ascii_immediate_word_too_short():
    """Word-sized immediates are too short -- return None."""
    result = format_ascii_immediate(0x4F4B)  # 'OK'
    assert result is None


def test_ascii_immediate_spaces_allowed():
    """Spaces are valid printable characters."""
    result = format_ascii_immediate(0x54455354)  # 'TEST'
    assert result == "'TEST'"


# ── Subroutine scan gap computation ──────────────────────────────────

def test_scan_uses_hint_blocks_for_gaps():
    """Subroutine scanner should use hint blocks when computing gaps.

    A hint block covers $00-$06 (moveq + bra.w). The bytes at $06
    are a separate subroutine (moveq + rts). The scanner should
    find the subroutine at $06 because the hint block makes $00-$06
    not a gap.

    Without this fix, the scanner sees $00-$0A as one gap and the
    candidate at $00 (moveq + bra.w = 2 instrs, unconditional jump)
    is rejected (< 3 instrs), then it tries $02 which is mid-BRA
    and fails, then $04 which is mid-displacement, then $06 where
    it finds the subroutine. But if another larger candidate starting
    before $06 consumes the region, $06 is never tried.
    """
    from m68k.subroutine_scan import scan_candidates
    from m68k.m68k_executor import BasicBlock, Instruction

    code = b''
    # $00: moveq #1,d0
    code += struct.pack('>H', 0x7001)
    # $02: bra.w $20 (far jump, not in our code)
    code += struct.pack('>HH', 0x6000, 0x001C)
    # $06: moveq #2,d0 (separate subroutine)
    code += struct.pack('>H', 0x7002)
    # $08: rts
    code += struct.pack('>H', 0x4E75)

    # With a hint block at $00-$06: gap starts at $06,
    # scanner finds subroutine there
    hint_block = BasicBlock(
        start=0, end=6,
        instructions=[
            Instruction(offset=0, size=2, opcode=0x7001,
                        text="moveq   #1,d0", raw=code[0:2]),
            Instruction(offset=2, size=4, opcode=0x6000,
                        text="bra.w   $20", raw=code[2:6]),
        ],
        is_entry=True,
    )
    candidates_with_hint = scan_candidates({0: hint_block}, code)
    addrs_with_hint = {c["addr"] for c in candidates_with_hint}
    assert 0x06 in addrs_with_hint, (
        f"With hint block at $00-$06, scanner should find $06, "
        f"got {addrs_with_hint}")


# ── PC-relative target discovery ─────────────────────────────────────

def test_pc_relative_discovers_data_target():
    """LEA d(PC),An pointing to data between instructions gets a label."""
    code = b''
    # $00: lea $08(pc),a0 -> target = $02 + $08 = $0A (data)
    code += struct.pack('>HH', 0x41FA, 0x0008)
    # $04: moveq #0,d0
    code += struct.pack('>H', 0x7000)
    # $06: rts
    code += struct.pack('>H', 0x4E75)
    # $08: nop (padding)
    code += struct.pack('>H', 0x4E71)
    # $0A: data (not an instruction)
    code += struct.pack('>HH', 0x0000, 0x0000)

    result = analyze(code, entry_points=[0])
    kb = KB()
    targets = discover_pc_relative_targets(result["blocks"], code, kb)

    assert 0x0A in targets, (
        f"LEA target $0A (data) should be discovered, got {targets}")


def test_pc_relative_discovers_code_target():
    """LEA d(PC),An pointing to an instruction start gets a label.

    Previously, all targets inside instruction ranges were rejected.
    The fix: only reject targets that land mid-instruction, not at
    instruction start addresses.
    """
    code = b''
    # $00: lea $06(pc),a0 -> target = $02 + $06 = $08 (code at $08)
    code += struct.pack('>HH', 0x41FA, 0x0006)
    # $04: moveq #0,d0
    code += struct.pack('>H', 0x7000)
    # $06: rts
    code += struct.pack('>H', 0x4E75)
    # $08: moveq #42,d0 (a valid instruction — target of LEA)
    code += struct.pack('>H', 0x702A)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    result = analyze(code, entry_points=[0, 0x08])
    kb = KB()
    targets = discover_pc_relative_targets(result["blocks"], code, kb)

    assert 0x08 in targets, (
        f"LEA target $08 (instruction start) should be discovered, "
        f"got {targets}")


def test_pc_relative_rejects_mid_instruction():
    """LEA d(PC),An pointing to the middle of an instruction is rejected.

    e.g. JMP 0(PC,D0.w) where the PC value is the extension word
    address — targeting the middle of the JMP instruction itself.
    """
    code = b''
    # $00: lea $03(pc),a0 -> target = $02 + $03 = $05 (mid-instruction)
    code += struct.pack('>HH', 0x41FA, 0x0003)
    # $04: move.l #$12345678,d0 (6-byte instruction: $04-$09)
    code += struct.pack('>HI', 0x203C, 0x12345678)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    result = analyze(code, entry_points=[0])
    kb = KB()
    targets = discover_pc_relative_targets(result["blocks"], code, kb)

    assert 0x05 not in targets, (
        f"Target $05 (mid-instruction at $04) should be rejected, "
        f"got {targets}")


# ── Label map: core block entries get loc_ labels ────────────────────

def test_core_block_entries_get_labels():
    """All core block start addresses should get loc_ labels.

    This ensures relocation entry points and other non-call/non-branch
    block starts get labels for PC-relative references.
    """
    # Simulate core blocks at $00, $08, $1C (like relocated payload)
    blocks = {0x00: None, 0x08: None, 0x1C: None}
    labels = build_label_map([], blocks, set(), {})

    for addr in (0x00, 0x08, 0x1C):
        assert addr in labels, (
            f"Core block at ${addr:04X} should have a label")
        assert labels[addr] == f"loc_{addr:04x}", (
            f"Expected loc_{addr:04x}, got {labels[addr]}")


def test_label_priority_entity_over_block():
    """Entity names take priority over loc_ block labels."""
    entities = [{"addr": "001c", "type": "code", "name": "payload_init"}]
    blocks = {0x00: None, 0x1C: None}
    labels = build_label_map(entities, blocks, set(), {})

    assert labels[0x1C] == "payload_init"
    assert labels[0x00] == "loc_0000"


def test_label_priority_block_over_pcref():
    """Block loc_ labels take priority over pcref_ labels."""
    blocks = {0x1C: None}
    pc_targets = {0x1C: "pcref_001c"}
    labels = build_label_map([], blocks, set(), pc_targets)

    assert labels[0x1C] == "loc_001c", (
        f"Block label should override pcref, got {labels[0x1C]}")
