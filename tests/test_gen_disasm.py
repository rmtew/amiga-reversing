from __future__ import annotations

"""Tests for disassembly output generation helpers."""

import io
import struct
from types import SimpleNamespace

import pytest
from _pytest.monkeypatch import MonkeyPatch

from disasm.comments import (
    build_instruction_comment_parts,
    format_app_offset_comment,
    format_ascii_immediate,
)
from disasm.data_access import collect_data_access_sizes
from disasm.data_render import emit_data_region
from disasm.decode import (
    DecodedInstructionForEmit,
    decode_inst_for_emit,
    decode_instruction_for_emit,
    lookup_instruction_kb,
)
from disasm.discovery import (
    add_hint_labels,
    apply_generic_data_label_promotions,
    build_label_map,
    discover_absolute_targets,
    discover_pc_relative_targets,
    filter_internal_absolute_data_targets,
)
from disasm.instruction_rows import (
    make_instruction_row,
    make_text_rows,
    render_instruction_text,
)
from disasm.operands import (
    _apply_field_value_domain_substitutions,
    _operand_types_for_inst,
    build_instruction_semantic_operands,
)
from disasm.types import (
    AppStructFieldOperandMetadata,
    BitfieldOperandMetadata,
    EntityRecord,
    HunkDisassemblySession,
    IndexedOperandMetadata,
    SemanticOperand,
    StructFieldOperandMetadata,
    SymbolOperandMetadata,
)
from m68k.instruction_decode import DecodedBitfield
from m68k.instruction_kb import find_kb_entry
from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import Instruction, _canonical_mnemonic, disassemble
from m68k.m68k_executor import BasicBlock, analyze
from m68k.memory_provenance import (
    MemoryRegionAddressSpace,
    MemoryRegionDerivation,
    MemoryRegionDerivationKind,
    MemoryRegionProvenance,
)
from m68k.os_calls import TypedMemoryRegion
from m68k.subroutine_scan import UnscoredSubroutineCandidate
from m68k_kb import runtime_m68k_analysis, runtime_os
from tests.os_kb_helpers import make_empty_os_kb
from tests.platform_helpers import make_platform

_INIT_STRUCTS = {
    "InitStruct": runtime_os.OsStruct(
        source="exec/initstruct.i",
        base_offset=0,
        base_offset_symbol=None,
        size=20,
        fields=(runtime_os.OsStructField("IS_CODE", "UWORD", 18, 2),),
    ),
}


def _prov_base(address_space: MemoryRegionAddressSpace, base_register: str,
               displacement: int) -> MemoryRegionProvenance:
    return MemoryRegionProvenance(
        address_space=address_space,
        derivation=MemoryRegionDerivation(
            kind=MemoryRegionDerivationKind.BASE_DISPLACEMENT,
            base_register=base_register,
            displacement=displacement,
        ),
    )


# -- Feature 3: App memory offset comments ----------------------------

def test_app_offset_comment_hex() -> None:
    """Unnamed d(A6) offset gets hex comment."""
    from disasm.types import SemanticOperand
    comment = format_app_offset_comment((
        SemanticOperand(kind="base_displacement", text="568(a6)",
                        base_register="a6", displacement=568),
        SemanticOperand(kind="register", text="d0", register="d0"),
    ), 6)
    assert comment == "app+$238"


def test_app_offset_comment_named_no_duplicate() -> None:
    """Named offset (already substituted) gets no comment."""
    from disasm.types import SemanticOperand
    comment = format_app_offset_comment((
        SemanticOperand(kind="base_displacement_symbol", text="app_dos_base(a6)",
                        base_register="a6", displacement=568,
                        metadata=SymbolOperandMetadata(symbol="app_dos_base")),
        SemanticOperand(kind="register", text="d0", register="d0"),
    ), 6)
    assert comment is None


def test_app_offset_comment_non_base_reg() -> None:
    """d(A0) reference does not get app offset comment."""
    from disasm.types import SemanticOperand
    comment = format_app_offset_comment((
        SemanticOperand(kind="base_displacement", text="100(a0)",
                        base_register="a0", displacement=100),
        SemanticOperand(kind="register", text="d0", register="d0"),
    ), 6)
    assert comment is None


# -- Feature 4: Data region format from access patterns ---------------

def test_collect_word_access() -> None:
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

    platform = make_platform(scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    sizes = collect_data_access_sizes(result["blocks"], result.get("exit_states", {}))
    # Address $0E should be marked as word access
    assert sizes.get(0x0E) == 2, (
        f"Expected word access at $0E, got {sizes}")


def test_collect_long_access() -> None:
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

    platform = make_platform(scratch_regs=())
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    sizes = collect_data_access_sizes(result["blocks"], result.get("exit_states", {}))
    assert sizes.get(0x0A) == 4, (
        f"Expected long access at $0A, got {sizes}")


def test_collect_data_access_uses_decoded_operands_not_text() -> None:
    code = b""
    code += struct.pack('>HH', 0x41FA, 0x0008)  # lea $0a(pc),a0
    code += struct.pack('>H', 0x2010)           # move.l (a0),d0
    code += struct.pack('>H', 0x4E75)           # rts
    code += struct.pack('>H', 0x4E71)
    code += struct.pack('>II', 0x12345678, 0xDEADBEEF)

    result = analyze(code, propagate=True, entry_points=[0],
                     platform=make_platform(scratch_regs=()))
    for block in result["blocks"].values():
        for inst in block.instructions:
            inst.text = "corrupted"

    sizes = collect_data_access_sizes(result["blocks"], result.get("exit_states", {}))
    assert sizes.get(0x0A) == 4


def test_emit_data_word_format() -> None:
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


def test_emit_data_word_format_stops_at_unknown_access() -> None:
    """A word run stops once access size metadata stops."""
    import io
    code = bytes([0x00, 0x10, 0x41, 0x42])
    f = io.StringIO()

    emit_data_region(f, code, 0, 4, {}, {}, set(), access_sizes={0: 2})

    output = f.getvalue()
    assert "dc.w    $0010" in output
    assert "$41" in output and "$42" in output


def test_emit_data_raw_chunk_stops_before_later_word_access() -> None:
    """Raw-byte chunking must not swallow a later structured word region."""
    import io
    code = bytes([0xAA, 0xBB, 0x12, 0x34])
    f = io.StringIO()

    emit_data_region(f, code, 0, 4, {}, {}, set(), access_sizes={2: 2})

    output = f.getvalue()
    assert "$aa" in output.lower() and "$bb" in output.lower()
    assert "dc.w    $1234" in output


def test_emit_data_long_format() -> None:
    """Data region with long access emits dc.l instead of dc.b."""
    import io
    code = struct.pack('>II', 0x12345678, 0xDEADBEEF)
    f = io.StringIO()
    access_sizes = {0: 4}
    emit_data_region(f, code, 0, 8, {}, {}, set(),
                     access_sizes=access_sizes)
    output = f.getvalue()
    assert "dc.l" in output, f"Expected dc.l in output, got:\n{output}"


# -- String detection in data regions ---------------------------------

def test_data_region_detects_embedded_string() -> None:
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


def test_data_region_short_printable_not_string() -> None:
    """Short non-null-terminated printable runs stay as hex."""
    data = bytes([0x41, 0x42, 0x43, 0x44, 0xFF])  # "ABCD" + junk, no null
    f = io.StringIO()
    emit_data_region(f, data, 0, len(data), {}, {}, set())
    output = f.getvalue()
    # 4 printable bytes without null terminator is too short (need 6+)
    assert '"ABCD"' not in output


def test_data_region_short_null_terminated_is_string() -> None:
    """Short null-terminated printable runs (4+) ARE strings."""
    data = b'ABCD\x00'
    f = io.StringIO()
    emit_data_region(f, data, 0, len(data), {}, {}, set())
    output = f.getvalue()
    assert '"ABCD"' in output


def test_data_region_null_terminated_string() -> None:
    """Null-terminated printable run emits as string with ,0 terminator."""
    data = b'include_longmac\x00'
    f = io.StringIO()
    emit_data_region(f, data, 0, len(data), {}, {}, set())
    output = f.getvalue()
    assert '"include_longmac"' in output
    assert ",0" in output


def test_data_region_prefers_obvious_string_over_word_access() -> None:
    data = b"3.18 (2.8.94)\x00"
    f = io.StringIO()
    emit_data_region(
        f,
        data,
        0,
        len(data),
        {},
        {},
        set(),
        access_sizes={0: 2},
    )
    output = f.getvalue()
    assert 'dc.b    "3.18 (2.8.94)",0' in output
    assert "dc.w" not in output


def test_data_region_does_not_cross_internal_label_for_string() -> None:
    data = b"HELLO\x00"
    f = io.StringIO()
    emit_data_region(
        f,
        data,
        0,
        len(data),
        {3: "loc_0003"},
        {},
        set(),
    )
    output = f.getvalue()
    assert '"HELLO"' not in output
    assert "loc_0003:" in output


def test_data_region_mixed_hex_and_string() -> None:
    """Data with non-printable bytes, then string, then more non-printable.

    Should emit: dc.b hex... then dc.b "text",0 then dc.b hex...
    """
    data = bytes([0x4A, 0xFB]) + b'hello\x00' + bytes([0xDE, 0xAD])
    f = io.StringIO()
    emit_data_region(f, data, 0, len(data), {}, {}, set())
    output = f.getvalue()
    assert '"hello"' in output
    assert "$4a" in output.lower() or "$4A" in output


# -- ASCII immediate comments -----------------------------------------

def test_ascii_immediate_longword() -> None:
    """4-byte all-printable immediate gets 'ABCD' comment."""
    result = format_ascii_immediate(0x4C494E45)  # 'LINE'
    assert result == "'LINE'"


def test_ascii_immediate_non_printable() -> None:
    """Immediate with non-printable byte returns None."""
    result = format_ascii_immediate(0x4C490045)  # 'LI\x00E'
    assert result is None


def test_ascii_immediate_word_too_short() -> None:
    """Word-sized immediates are too short -- return None."""
    result = format_ascii_immediate(0x4F4B)  # 'OK'
    assert result is None


def test_ascii_immediate_spaces_allowed() -> None:
    """Spaces are valid printable characters."""
    result = format_ascii_immediate(0x54455354)  # 'TEST'
    assert result == "'TEST'"


# -- Subroutine scan gap computation ----------------------------------

def test_scan_uses_hint_blocks_for_gaps() -> None:
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
    from m68k.m68k_executor import BasicBlock, Instruction
    from m68k.subroutine_scan import scan_candidates

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
                        text="moveq   #1,d0", raw=code[0:2],
                        kb_mnemonic="moveq", operand_size="l",
                        operand_texts=("#1", "d0")),
            Instruction(offset=2, size=4, opcode=0x6000,
                        text="bra.w   $20", raw=code[2:6],
                        kb_mnemonic="bra", operand_size="w",
                        operand_texts=("$20",)),
        ],
        is_entry=True,
    )
    candidates_with_hint = scan_candidates({0: hint_block}, code)
    addrs_with_hint = {c["addr"] for c in candidates_with_hint}
    assert 0x06 in addrs_with_hint, (
        f"With hint block at $00-$06, scanner should find $06, "
        f"got {addrs_with_hint}")


def test_scan_candidates_finds_sequential_subroutines_in_one_gap() -> None:
    from m68k.subroutine_scan import scan_candidates

    code = b""
    code += struct.pack(">H", 0x7001)  # $00 moveq #1,d0
    code += struct.pack(">H", 0x4E75)  # $02 rts
    code += struct.pack(">H", 0x7002)  # $04 moveq #2,d0
    code += struct.pack(">H", 0x4E75)  # $06 rts

    candidates = scan_candidates({}, code)

    assert [c["addr"] for c in candidates] == [0x00, 0x04]


def test_try_decode_subroutine_reuses_scan_cache(monkeypatch: MonkeyPatch) -> None:
    from m68k import subroutine_scan

    code = b""
    code += struct.pack(">H", 0x7001)  # moveq #1,d0
    code += struct.pack(">H", 0x4E75)  # rts

    calls: dict[str, int] = {"count": 0}
    real_decode_at = subroutine_scan._decode_at

    def _counting_decode_at(
        code_bytes: bytes,
        pos: int,
        cache: dict[int, Instruction | Exception],
    ) -> Instruction:
        calls["count"] += 1
        return real_decode_at(code_bytes, pos, cache)

    monkeypatch.setattr(subroutine_scan, "_decode_at", _counting_decode_at)

    decode_cache: dict[int, Instruction | Exception] = {}
    scan_cache: dict[tuple[int, int], UnscoredSubroutineCandidate | None] = {}
    flow_cache: dict[str, tuple[runtime_m68k_analysis.FlowType, bool]] = {}

    first = subroutine_scan._try_decode_subroutine(
        code, 0, len(code), decode_cache, scan_cache, flow_cache
    )
    second = subroutine_scan._try_decode_subroutine(
        code, 0, len(code), decode_cache, scan_cache, flow_cache
    )

    assert first == second
    assert calls["count"] == 2


def test_try_decode_subroutine_rejects_immediate_unconditional_branch(monkeypatch: MonkeyPatch) -> None:
    from m68k import subroutine_scan

    code = b""
    code += struct.pack(">H", 0x6002)  # bra.s $04
    code += struct.pack(">H", 0x4E71)  # nop
    code += struct.pack(">H", 0x4E75)  # rts

    calls: dict[str, int] = {"count": 0}
    real_decode_at = subroutine_scan._decode_at

    def _counting_decode_at(
        code_bytes: bytes,
        pos: int,
        cache: dict[int, Instruction | Exception],
    ) -> Instruction:
        calls["count"] += 1
        return real_decode_at(code_bytes, pos, cache)

    monkeypatch.setattr(subroutine_scan, "_decode_at", _counting_decode_at)

    candidate = subroutine_scan._try_decode_subroutine(
        code, 0, len(code), {}, {}, {}
    )

    assert candidate is None
    assert calls["count"] == 1


# -- PC-relative target discovery -------------------------------------

def test_pc_relative_discovers_data_target() -> None:
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
    targets = discover_pc_relative_targets(result["blocks"], code)

    assert 0x0A in targets, (
        f"LEA target $0A (data) should be discovered, got {targets}")


def test_pc_relative_discovers_code_target() -> None:
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
    # $08: moveq #42,d0 (a valid instruction - target of LEA)
    code += struct.pack('>H', 0x702A)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    result = analyze(code, entry_points=[0, 0x08])
    targets = discover_pc_relative_targets(result["blocks"], code)

    assert 0x08 in targets, (
        f"LEA target $08 (instruction start) should be discovered, "
        f"got {targets}")


def test_pc_relative_rejects_mid_instruction() -> None:
    """LEA d(PC),An pointing to the middle of an instruction is rejected.

    e.g. JMP 0(PC,D0.w) where the PC value is the extension word
    address - targeting the middle of the JMP instruction itself.
    """
    code = b''
    # $00: lea $03(pc),a0 -> target = $02 + $03 = $05 (mid-instruction)
    code += struct.pack('>HH', 0x41FA, 0x0003)
    # $04: move.l #$12345678,d0 (6-byte instruction: $04-$09)
    code += struct.pack('>HI', 0x203C, 0x12345678)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    result = analyze(code, entry_points=[0])
    targets = discover_pc_relative_targets(result["blocks"], code)

    assert 0x05 not in targets, (
        f"Target $05 (mid-instruction at $04) should be rejected, "
        f"got {targets}")


# -- Label map: core block entries get loc_ labels --------------------

def test_core_block_entries_get_labels() -> None:
    """All core block start addresses should get loc_ labels.

    This ensures relocation entry points and other non-call/non-branch
    block starts get labels for PC-relative references.
    """
    # Simulate core blocks at $00, $08, $1C (like relocated payload)
    blocks = {0x00: None, 0x08: None, 0x1C: None}
    labels = build_label_map([], blocks, set(), set(), {})

    for addr in (0x00, 0x08, 0x1C):
        assert addr in labels, (
            f"Core block at ${addr:04X} should have a label")
        assert labels[addr] == f"loc_{addr:04x}", (
            f"Expected loc_{addr:04x}, got {labels[addr]}")


def test_label_priority_entity_over_block() -> None:
    """Entity names take priority over loc_ block labels."""
    entities: list[EntityRecord] = [{"addr": "001c", "type": "code", "name": "payload_init"}]
    blocks = {0x00: None, 0x1C: None}
    labels = build_label_map(entities, blocks, set(), set(), {})

    assert labels[0x1C] == "payload_init"
    assert labels[0x00] == "loc_0000"


def test_label_priority_block_over_pcref() -> None:
    """Block loc_ labels take priority over pcref_ labels."""
    blocks = {0x1C: None}
    pc_targets = {0x1C: "pcref_001c"}
    labels = build_label_map([], blocks, set(), set(), pc_targets)

    assert labels[0x1C] == "loc_001c", (
        f"Block label should override pcref, got {labels[0x1C]}")


def test_discover_absolute_targets_finds_internal_data_refs() -> None:
    """Internal absolute operands are decoded from raw instruction bytes."""
    block = BasicBlock(
        start=0x40, end=0x48,
        instructions=[
            Instruction(offset=0x40, size=4, opcode=0x4238,
                        text="clr.b   opaque", raw=struct.pack(">HH", 0x4238, 0x8C1F),
                        kb_mnemonic="clr", operand_size="b",
                        operand_texts=("opaque",)),
            Instruction(offset=0x44, size=4, opcode=0x4238,
                        text="clr.w   opaque", raw=struct.pack(">HH", 0x4278, 0xDFF0),
                        kb_mnemonic="clr", operand_size="w",
                        operand_texts=("opaque",)),
        ],
        is_entry=True,
    )

    targets = discover_absolute_targets({0x40: block}, 0x9000)

    assert targets == {0x8C1F}


def test_build_label_map_adds_core_absolute_data_labels() -> None:
    """Core absolute targets get relocatable data labels."""
    labels = build_label_map([], {}, set(), {0x8C1E}, {})

    assert labels[0x8C1E] == "dat_8c1e"


def test_apply_generic_data_label_promotions_overrides_only_generic_labels() -> None:
    labels = {
        0x004A: "pcref_004a",
        0x0050: "dat_0050",
        0x0060: "entry_point",
    }
    pc_targets = {
        0x004A: "pcref_004a",
        0x0070: "str_0070",
    }

    apply_generic_data_label_promotions(
        labels,
        pc_targets,
        {0x004A, 0x0050},
        {
            0x004A: "openscreen_newscreen",
            0x0050: "openwindow_newwindow",
            0x0060: "should_not_override",
            0x0070: "should_not_override_string",
        },
    )

    assert labels[0x004A] == "openscreen_newscreen"
    assert labels[0x0050] == "openwindow_newwindow"
    assert labels[0x0060] == "entry_point"
    assert pc_targets[0x004A] == "openscreen_newscreen"
    assert pc_targets[0x0070] == "str_0070"


def test_filter_internal_absolute_data_targets_keeps_hint_only_addresses() -> None:
    """Core absolute data refs must not be dropped just because hints cover them."""
    targets = {0x8C1E, 0x8C1F, 0xEE2D}
    filtered = filter_internal_absolute_data_targets(
        targets,
        code_addrs={0x2000, 0x2001},
        reserved_addrs=set(),
    )

    assert filtered == {0x8C1E, 0x8C1F, 0xEE2D}


def test_filter_internal_absolute_data_targets_excludes_fixed_os_addresses() -> None:
    """Fixed system addresses must not become relocatable data labels."""
    filtered = filter_internal_absolute_data_targets(
        targets={runtime_os.META.exec_base_addr.address, 0x8C1E},
        code_addrs=set(),
        reserved_addrs={runtime_os.META.exec_base_addr.address},
    )

    assert filtered == {0x8C1E}


def test_lookup_instruction_kb_normalizes_pmmu_condition_variant() -> None:
    """PMMU condition-coded variants resolve to the PBcc KB entry."""
    inst_kb = lookup_instruction_kb("pb#44")

    assert inst_kb == "PBcc"


def test_decode_instruction_for_emit_requires_kb_mnemonic() -> None:
    """Emission-time decode must reject instructions without KB identity."""
    with pytest.raises(ValueError, match="missing kb_mnemonic"):
        decode_instruction_for_emit(
            struct.pack(">HH", 0x41F8, 0x0400),
            0x0038,
            "",
            "w",
        )


def test_decode_instruction_for_emit_errors_on_mismatched_kb_mnemonic() -> None:
    with pytest.raises(ValueError, match="KB encoding match count 0"):
        decode_instruction_for_emit(
            struct.pack(">HHH", 0x08E9, 0x0006, 0x000C),
            0x0200,
            "BCHG",
            "w",
        )


def test_lookup_instruction_kb_normalizes_pmmu_text_condition_variant() -> None:
    """PMMU textual condition variants resolve to the PBcc KB entry."""
    inst_kb = lookup_instruction_kb("pbbs")

    assert inst_kb == "PBcc"


def test_kb_find_resolves_pmmu_condition_family() -> None:
    """Shared KB lookup resolves mixed-case PMMU condition families."""
    inst_kb = find_kb_entry("PBcc")

    assert inst_kb is not None
    assert inst_kb == "PBcc"


def test_canonical_mnemonic_normalizes_pmmu_numeric_condition() -> None:
    """Disassembler canonicalization maps PMMU numeric conditions to PBcc."""
    assert _canonical_mnemonic("pb#44.w") == "pbcc"


def test_canonical_mnemonic_normalizes_pmmu_text_condition() -> None:
    """Disassembler canonicalization maps PMMU textual conditions to PBcc."""
    assert _canonical_mnemonic("pbbs.w") == "pbcc"


def test_add_hint_labels_adds_hint_block_and_successor_labels() -> None:
    """Hint block labels appear without overriding existing core labels."""
    hint_block = BasicBlock(
        start=0x200, end=0x204,
        instructions=[],
        successors=[0x220],
        is_entry=True,
    )
    labels = {0x220: "loc_0220"}

    add_hint_labels(labels, {0x200: hint_block}, code_addrs={0x220})

    assert labels[0x200] == "hint_0200"
    assert labels[0x220] == "loc_0220"


def test_render_instruction_text_substitutes_absolute_code_operand() -> None:
    """Absolute code operands should use decoded absolute EA targets."""
    inst = Instruction(offset=0x0038, size=4, opcode=0x41F8,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x41F8, 0x0400),
                       kb_mnemonic="lea", operand_size="l",
                       operand_texts=("$00000400", "a0"),
                       opcode_text="lea")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x0400: "loc_0400"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    text, _comment, _comment_parts = render_instruction_text(inst, session, set())

    assert text == "lea loc_0400,a0"


def test_render_instruction_text_substitutes_pc_relative_operand() -> None:
    """PC-relative operands should render labels from decoded targets."""
    inst = Instruction(offset=0x0040, size=4, opcode=0x41FA,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x41FA, 0x0008),
                       kb_mnemonic="lea", operand_size="l",
                       operand_texts=("8(pc)", "a0"),
                       opcode_text="lea")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x004A: "pcref_004a"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    text, _comment, _comment_parts = render_instruction_text(inst, session, set())

    assert text == "lea pcref_004a(pc),a0"


def test_build_instruction_semantic_operands_marks_branch_target() -> None:
    inst = Instruction(offset=0x0040, size=2, opcode=0x6606,
                       text="bne.s   $000048", raw=struct.pack(">H", 0x6606),
                       kb_mnemonic="bcc", operand_size="s",
                       operand_texts=("$000048",))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x0048: "loc_0048"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 1
    assert ops[0].kind == "branch_target"
    assert ops[0].segment_addr == 0x0048
    assert ops[0].text == "loc_0048"


def test_build_instruction_semantic_operands_keeps_numeric_immediate() -> None:
    inst = Instruction(offset=0x0038, size=6, opcode=0x203C,
                       text="move.l  #$00000400,d0",
                       raw=struct.pack(">HI", 0x203C, 0x00000400),
                       kb_mnemonic="move", operand_size="l",
                       operand_texts=("#$00000400", "d0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "immediate"
    assert ops[0].value == 0x400
    assert ops[0].segment_addr is None
    assert ops[1].kind == "register"


def test_build_instruction_semantic_operands_uses_decoded_moveq_immediate() -> None:
    inst = Instruction(offset=0x0000, size=2, opcode=0x7001,
                       text="moveq   #1,d0",
                       raw=struct.pack(">H", 0x7001),
                       kb_mnemonic="moveq", operand_size="l",
                       operand_texts=("#1", "d0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "immediate"
    assert ops[0].value == 1
    assert ops[0].text == "#1"
    assert ops[1].kind == "register"


def test_build_instruction_semantic_operands_uses_decoded_absolute_operand() -> None:
    inst = Instruction(offset=0x0038, size=4, opcode=0x41F8,
                       text="lea     $00000400,a0",
                       raw=struct.pack(">HH", 0x41F8, 0x0400),
                       kb_mnemonic="lea", operand_size="l",
                       operand_texts=("$00000400", "a0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x0400: "loc_0400"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "absolute_target"
    assert ops[0].value == 0x400
    assert ops[0].segment_addr == 0x400
    assert ops[0].text == "loc_0400"
    assert ops[1].kind == "register"


def test_build_instruction_semantic_operands_uses_decoded_pc_relative_target() -> None:
    inst = Instruction(offset=0x0040, size=4, opcode=0x41FA,
                       text="lea     8(pc),a0",
                       raw=struct.pack(">HH", 0x41FA, 0x0008),
                       kb_mnemonic="lea", operand_size="l",
                       operand_texts=("8(pc)", "a0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x004A: "pcref_004a"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "pc_relative_target"
    assert ops[0].segment_addr == 0x004A
    assert ops[0].value == 0x004A
    assert ops[0].text == "pcref_004a(pc)"
    assert ops[1].kind == "register"


def test_build_instruction_semantic_operands_uses_decoded_base_displacement() -> None:
    inst = Instruction(offset=0x0100, size=4, opcode=0x3029,
                       text="move.w  18(a1),d0",
                       raw=struct.pack(">HH", 0x3029, 0x0012),
                       kb_mnemonic="move", operand_size="w",
                       operand_texts=("18(a1)", "d0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0100: {"a1": TypedMemoryRegion(
            struct="InitStruct",
            size=20,
                provenance=MemoryRegionProvenance(
                    address_space=MemoryRegionAddressSpace.ABSOLUTE,
                    absolute_addr=0x100,
                ),
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=SimpleNamespace(
            META=runtime_os.META,
            STRUCTS=_INIT_STRUCTS,
            CONSTANTS={},
            LIBRARIES={},
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    used_structs: set[str] = set()

    ops = build_instruction_semantic_operands(
        inst, session, used_structs=used_structs)

    assert len(ops) == 2
    assert ops[0].kind == "base_displacement_symbol"
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 18
    assert ops[0].value == 18
    assert ops[0].text == "IS_CODE(a1)"
    assert used_structs == {"InitStruct"}
    assert ops[1].kind == "register"


def test_build_instruction_semantic_operands_uses_decoded_indexed_operand() -> None:
    inst = Instruction(offset=0x0100, size=4, opcode=0x3231,
                       text="move.w  8(a1,d0.w),d1",
                       raw=struct.pack(">HH", 0x3231, 0x0008),
                       kb_mnemonic="move", operand_size="w",
                       operand_texts=("8(a1,d0.w)", "d1"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "indexed"
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert ops[0].value == 8
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d0"
    assert ops[0].metadata.index_size == "w"
    assert ops[0].text == "8(a1,d0.w)"
    assert ops[1].kind == "register"


def test_build_instruction_semantic_operands_uses_decoded_quick_immediate_shape() -> None:
    inst = Instruction(offset=0x0046, size=2, opcode=0x598E,
                       text="subq.l  #4,a6",
                       raw=struct.pack(">H", 0x598E),
                       kb_mnemonic="subq", operand_size="l",
                       operand_texts=("#4", "a6"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(app_base=(6, 0)),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "immediate"
    assert ops[0].value == 4
    assert ops[0].text == "#4"
    assert ops[1].kind == "register"
    assert ops[1].register == "a6"
    assert ops[1].text == "a6"


def test_build_instruction_semantic_operands_uses_decoded_dbcc_shape() -> None:
    inst = Instruction(offset=0x0058, size=4, opcode=0x51C8,
                       text="dbf    d0,$56",
                       raw=struct.pack(">HH", 0x51C8, 0x0054),
                       kb_mnemonic="dbcc", operand_size="w",
                       operand_texts=("d0", "$56"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x0056: "loc_0056"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "register"
    assert ops[0].register == "d0"
    assert ops[1].kind == "branch_target"
    assert ops[1].segment_addr == 0xAE
    assert ops[1].text == "$56"


def test_build_instruction_semantic_operands_uses_immediate_bitop_form() -> None:
    inst = Instruction(offset=0x0200, size=6, opcode=0x08E9,
                       text="bset    #6,12(a1)",
                       raw=struct.pack(">HHH", 0x08E9, 0x0006, 0x000C),
                       kb_mnemonic="bset", operand_size="w",
                       operand_texts=("#6", "12(a1)"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "immediate"
    assert ops[0].value == 6
    assert ops[0].text == "#6"
    assert ops[1].kind == "base_displacement"
    assert ops[1].base_register == "a1"
    assert ops[1].displacement == 12


def test_operand_types_for_inst_selects_register_shift_form_from_opcode_bit() -> None:
    inst = Instruction(offset=0x1120, size=2, opcode=0xE1AA,
                       text="lsl.l  d0,d2",
                       raw=b"\xE1\xAA",
                       kb_mnemonic="lsl",
                       operand_size="l",
                       operand_texts=("d0", "d2"))
    meta = decode_instruction_for_emit(inst.raw, inst.offset, "lsl", "l")

    assert isinstance(meta, DecodedInstructionForEmit)
    assert _operand_types_for_inst(inst, meta) == ("dn", "dn")


def test_decode_inst_for_emit_uses_operand_size_not_text() -> None:
    inst = Instruction(offset=0x1120, size=2, opcode=0xE1AA,
                       text="corrupted",
                       raw=b"\xE1\xAA",
                       kb_mnemonic="lsl",
                       operand_size="l",
                       operand_texts=("d0", "d2"))

    meta = decode_inst_for_emit(inst)

    assert isinstance(meta, DecodedInstructionForEmit)
    assert meta.size == "l"


def test_build_instruction_semantic_operands_supports_register_shift_form() -> None:
    inst = Instruction(offset=0x1120, size=2, opcode=0xE1AA,
                       text="lsl.l  d0,d2",
                       raw=b"\xE1\xAA",
                       kb_mnemonic="lsl",
                       operand_size="l",
                       operand_texts=("d0", "d2"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "register"
    assert ops[0].register == "d0"
    assert ops[1].kind == "register"
    assert ops[1].register == "d2"


def test_build_instruction_semantic_operands_supports_immediate_shift_form() -> None:
    inst = Instruction(offset=0x0200, size=2, opcode=0xE900,
                       text="asl.b  #4,d0",
                       raw=b"\xE9\x00",
                       kb_mnemonic="asl", operand_size="b",
                       operand_texts=("#4", "d0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "immediate"
    assert ops[0].value == 4
    assert ops[1].kind == "register"
    assert ops[1].register == "d0"


def test_build_instruction_semantic_operands_supports_zero_encoded_shift_count() -> None:
    inst = disassemble(assemble_instruction("asl.b #8,d0"))[0]
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "immediate"
    assert ops[0].value == 8
    assert ops[1].kind == "register"
    assert ops[1].register == "d0"


def test_build_instruction_semantic_operands_supports_ea_to_dn_form() -> None:
    inst = Instruction(offset=0x0200, size=2, opcode=0x4180,
                       text="chk.w   d0,d0",
                       raw=b"\x41\x80",
                       kb_mnemonic="chk", operand_size="w",
                       operand_texts=("d0", "d0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "register"
    assert ops[0].register == "d0"
    assert ops[1].kind == "register"
    assert ops[1].register == "d0"


def test_build_instruction_semantic_operands_supports_bitfield_ea_form() -> None:
    inst = Instruction(offset=0x0200, size=4, opcode=0xEAC0,
                       text="bfchg    d0{2:8}",
                       raw=bytes.fromhex("eac00088"),
                       kb_mnemonic="bfchg", operand_size="w",
                       operand_texts=("d0{2:8}",))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 1
    assert ops[0].kind == "bitfield_ea"
    assert ops[0].register == "d0"
    assert isinstance(ops[0].metadata, BitfieldOperandMetadata)
    assert isinstance(ops[0].metadata.bitfield, DecodedBitfield)
    assert ops[0].metadata.bitfield.offset_value == 2
    assert ops[0].metadata.bitfield.width_value == 8


def test_build_instruction_semantic_operands_supports_bitfield_extract_form() -> None:
    inst = Instruction(offset=0x0200, size=4, opcode=0xE9C0,
                       text="bfextu   d0{2:8},d1",
                       raw=bytes.fromhex("e9c01088"),
                       kb_mnemonic="bfextu", operand_size="w",
                       operand_texts=("d0{2:8}", "d1"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "bitfield_ea"
    assert ops[1].kind == "register"
    assert ops[1].register == "d1"


def test_build_instruction_semantic_operands_keeps_decoded_value_for_symbolic_immediate() -> None:
    inst = Instruction(offset=0x0038, size=6, opcode=0x203C,
                       text="move.l  #loc_0400,d0",
                       raw=struct.pack(">HI", 0x203C, 0x00000400),
                       kb_mnemonic="move", operand_size="l",
                       operand_texts=("#loc_0400", "d0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={0x003A: 0x0400, 0x003C: 0x0400},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x0400: "loc_0400"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    ops = build_instruction_semantic_operands(inst, session)

    assert len(ops) == 2
    assert ops[0].kind == "immediate_symbol"
    assert ops[0].value == 0x400
    assert ops[0].segment_addr == 0x400
    assert ops[0].text == "#loc_0400"
    assert ops[1].kind == "register"


def test_build_instruction_semantic_operands_rejects_operand_text_count_mismatch() -> None:
    inst = Instruction(offset=0x0000, size=2, opcode=0x7001,
                       text="corrupted",
                       raw=struct.pack(">H", 0x7001),
                       kb_mnemonic="moveq", operand_size="l",
                       operand_texts=("#1", "d0", "d1"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    with pytest.raises(ValueError, match="Operand text count mismatch") as exc_info:
        build_instruction_semantic_operands(inst, session)
    message = str(exc_info.value)
    assert "Operand text count mismatch" in message
    assert "$000000" in message
    assert "corrupted" not in message


def test_build_instruction_semantic_operands_rejects_missing_operand_text_slots() -> None:
    inst = Instruction(offset=0x0000, size=2, opcode=0x7001,
                       text="moveq",
                       raw=struct.pack(">H", 0x7001),
                       kb_mnemonic="moveq", operand_size="l",
                       operand_texts=None)
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    with pytest.raises(ValueError, match="missing operand_texts"):
        build_instruction_semantic_operands(inst, session)


def test_build_instruction_semantic_operands_supports_zero_operand_kb_form() -> None:
    inst = Instruction(offset=0x0000, size=4, opcode=0xF000,
                       text="pflusha", raw=bytes.fromhex("F0002400"),
                       kb_mnemonic="pflusha", operand_size="w",
                       operand_texts=())
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    assert build_instruction_semantic_operands(inst, session) == ()


def test_build_instruction_comment_parts_prefers_ascii_when_no_other_comment() -> None:
    inst = Instruction(offset=0x0038, size=6, opcode=0x203C,
                       text="move.l  #$4C494E45,d0",
                       raw=struct.pack(">HI", 0x203C, 0x4C494E45),
                       kb_mnemonic="move", operand_size="l",
                       operand_texts=("#$4C494E45", "d0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    parts = build_instruction_comment_parts(
        inst,
        session,
        operand_parts=(
            SemanticOperand(kind="immediate", text="#$4C494E45", value=0x4C494E45),
            SemanticOperand(kind="register", text="d0", register="d0"),
        ),
        include_arg_subs=True)

    assert parts == ("'LINE'",)


def test_make_instruction_row_renders_from_semantic_operands_and_comments() -> None:
    inst = Instruction(offset=0x0040, size=2, opcode=0x6606,
                       text="corrupted", raw=struct.pack(">H", 0x6606),
                       kb_mnemonic="bcc", operand_size="s",
                       operand_texts=("$000048",),
                       opcode_text="bne.s")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x0048: "loc_0048"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    row = make_instruction_row(
        "bne.s loc_0048",
        inst,
        session,
        entity_addr=0x0040,
        verified_state="verified",
        comment_parts=("68020+", "branch note"),
    )

    assert row.operand_text == "loc_0048"
    assert row.comment_text == "68020+; branch note"
    assert row.text == "    bne.s loc_0048 ; 68020+; branch note\n"


def test_make_text_rows_uses_text_semantic_operands_for_directives() -> None:
    rows = make_text_rows("directive", "    dc.w $1234,d0\n", addr=0x40)

    assert len(rows) == 1
    assert [part.kind for part in rows[0].operand_parts] == ["text", "text"]
    assert [part.text for part in rows[0].operand_parts] == ["$1234", "d0"]


def test_build_instruction_semantic_operands_substitutes_struct_field() -> None:
    inst = Instruction(offset=0x0100, size=4, opcode=0x3029,
                       text="move.w  18(a1),d0",
                       raw=struct.pack(">HH", 0x3029, 0x0012),
                       kb_mnemonic="move", operand_size="w",
                       operand_texts=("18(a1)", "d0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0100: {"a1": TypedMemoryRegion(
            struct="InitStruct",
            size=20,
                provenance=MemoryRegionProvenance(
                    address_space=MemoryRegionAddressSpace.ABSOLUTE,
                    absolute_addr=0x100,
                ),
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=SimpleNamespace(
            META=runtime_os.META,
            STRUCTS=_INIT_STRUCTS,
            CONSTANTS={},
            LIBRARIES={},
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    used_structs: set[str] = set()

    ops = build_instruction_semantic_operands(
        inst, session, used_structs=used_structs)

    assert used_structs == {"InitStruct"}
    assert ops[0].kind == "base_displacement_symbol"
    assert ops[0].text == "IS_CODE(a1)"
    assert ops[0].metadata == StructFieldOperandMetadata(
        symbol="IS_CODE",
        owner_struct="InitStruct",
        field_symbol="IS_CODE",
        context_name=None,
    )


def test_render_instruction_text_uses_semantic_branch_substitution() -> None:
    inst = Instruction(offset=0x0040, size=2, opcode=0x6606,
                       text="corrupted", raw=struct.pack(">H", 0x6606),
                       kb_mnemonic="bcc", operand_size="s",
                       operand_texts=("$000048",),
                       opcode_text="bne.s")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x0048: "loc_0048"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    text, comment, comment_parts = render_instruction_text(inst, session, set())

    assert text == "bne.s loc_0048"
    assert comment == ""
    assert comment_parts == ()


def test_render_instruction_text_uses_semantic_struct_substitution() -> None:
    inst = Instruction(offset=0x0100, size=4, opcode=0x3029,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x3029, 0x0012),
                       kb_mnemonic="move", operand_size="w",
                       operand_texts=("18(a1)", "d0"),
                       opcode_text="move.w")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0100: {"a1": TypedMemoryRegion(
            struct="InitStruct",
            size=20,
                provenance=MemoryRegionProvenance(
                    address_space=MemoryRegionAddressSpace.ABSOLUTE,
                    absolute_addr=0x100,
                ),
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=SimpleNamespace(
            META=runtime_os.META,
            STRUCTS=_INIT_STRUCTS,
            CONSTANTS={},
            LIBRARIES={},
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    used_structs: set[str] = set()

    text, comment, comment_parts = render_instruction_text(
        inst, session, used_structs)

    assert text == "move.w IS_CODE(a1),d0"
    assert comment == ""
    assert comment_parts == ()
    assert used_structs == {"InitStruct"}


def test_render_instruction_text_uses_custom_relative_register_symbol() -> None:
    inst = Instruction(offset=0x0100, size=4, opcode=0x3028,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x3028, 0x009A),
                       kb_mnemonic="move", operand_size="w",
                       operand_texts=("154(a0)", "d0"),
                       opcode_text="move.w")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        hardware_base_regs={0x0100: {"a0": 0x00DFF000}},
    )

    text, comment, comment_parts = render_instruction_text(inst, session, set())

    assert text == "move.w intena(a0),d0"
    assert comment == ""
    assert comment_parts == ()


def test_build_instruction_semantic_operands_uses_shifted_pointee_struct_substitution() -> None:
    inst = Instruction(offset=0x0100, size=4, opcode=0x2029,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x2029, 0x0000),
                       kb_mnemonic="move", operand_size="l",
                       operand_texts=("0(a1)", "d0"))
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0100: {"a1": TypedMemoryRegion(
            struct="MP",
            size=runtime_os.STRUCTS["MP"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.REGISTER, "a0", 14),
            struct_offset=16,
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    used_structs: set[str] = set()

    ops = build_instruction_semantic_operands(inst, session, used_structs=used_structs)

    assert len(ops) == 2
    assert ops[0].kind == "base_displacement_symbol"
    assert ops[0].text == "MP_SIGTASK(a1)"
    assert ops[0].metadata == StructFieldOperandMetadata(
        symbol="MP_SIGTASK",
        owner_struct="MP",
        field_symbol="MP_SIGTASK",
        context_name=None,
    )
    assert used_structs == {"MP"}


def test_render_instruction_text_uses_shifted_pointee_struct_substitution() -> None:
    inst = Instruction(offset=0x0100, size=4, opcode=0x2029,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x2029, 0x0000),
                       kb_mnemonic="move", operand_size="l",
                       operand_texts=("0(a1)", "d0"),
                       opcode_text="move.l")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0100: {"a1": TypedMemoryRegion(
            struct="MP",
            size=runtime_os.STRUCTS["MP"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.REGISTER, "a0", 14),
            struct_offset=16,
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    used_structs: set[str] = set()

    text, comment, comment_parts = render_instruction_text(inst, session, used_structs)

    assert text == "move.l MP_SIGTASK(a1),d0"
    assert comment == ""
    assert comment_parts == ()
    assert used_structs == {"MP"}


def test_render_instruction_text_uses_app_region_struct_substitution() -> None:
    inst = Instruction(offset=0x0100, size=4, opcode=0x206E,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x206E, 0x0078),
                       kb_mnemonic="movea", operand_size="l",
                       operand_texts=("120(a6)", "a0"),
                       opcode_text="movea.l")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
            app_offsets={100: "app_timer_device_iorequest"},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(app_base=(6, 0)),
        os_kb=SimpleNamespace(
            META=runtime_os.META,
            STRUCTS=runtime_os.STRUCTS,
            CONSTANTS={},
            LIBRARIES={},
            FIELD_CONTEXT_VALUE_DOMAINS={},
            FIELD_VALUE_DOMAINS={},
            VALUE_DOMAINS={},
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        app_struct_regions={
            100: TypedMemoryRegion(
                struct="IO",
                size=runtime_os.STRUCTS["IO"].size,
                provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 100),
            )
        },
    )
    used_structs: set[str] = set()

    text, comment, comment_parts = render_instruction_text(inst, session, used_structs)

    assert text == "movea.l app_timer_device_iorequest+IO_DEVICE(a6),a0"
    assert comment == ""
    assert comment_parts == ()
    assert used_structs == {"IO"}
    ops = build_instruction_semantic_operands(inst, session)
    assert ops[0].metadata == AppStructFieldOperandMetadata(
        base_symbol="app_timer_device_iorequest",
        field_symbol="IO_DEVICE",
    )


def test_render_instruction_text_uses_inherited_pointee_base_field_substitution() -> None:
    inst = Instruction(offset=0x0104, size=4, opcode=0x0C68,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x0C68, 0x0014),
                       kb_mnemonic="cmpi", operand_size="w",
                       operand_texts=("#$24", "20(a0)"),
                       opcode_text="cmpi.w")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0104: {"a0": TypedMemoryRegion(
            struct="DD",
            size=runtime_os.STRUCTS["DD"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.REGISTER, "a6", 120),
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={100: "app_opendevice_iorequest"},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(app_base=(6, 0)),
        os_kb=SimpleNamespace(
            META=runtime_os.META,
            STRUCTS=runtime_os.STRUCTS,
            CONSTANTS={},
            LIBRARIES={},
            FIELD_CONTEXT_VALUE_DOMAINS={},
            FIELD_VALUE_DOMAINS={},
            VALUE_DOMAINS={},
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    used_structs: set[str] = set()

    text, comment, comment_parts = render_instruction_text(inst, session, used_structs)

    assert text == "cmpi.w #$24,LIB_VERSION(a0)"
    assert comment == ""
    assert comment_parts == ()
    assert used_structs == {"LIB"}


def test_render_instruction_text_uses_concrete_named_base_field_substitution() -> None:
    inst = Instruction(offset=0x0104, size=4, opcode=0x2028,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x2028, 0x003A),
                       kb_mnemonic="move", operand_size="l",
                       operand_texts=("58(a0)", "d0"),
                       opcode_text="move.l")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0104: {"a0": TypedMemoryRegion(
            struct="DosLibrary",
            size=runtime_os.STRUCTS["DosLibrary"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 100),
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={100: "app_dos_base"},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(app_base=(6, 0)),
        os_kb=SimpleNamespace(
            META=runtime_os.META,
            STRUCTS=runtime_os.STRUCTS,
            CONSTANTS={},
            LIBRARIES={},
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    used_structs: set[str] = set()

    text, comment, comment_parts = render_instruction_text(inst, session, used_structs)

    assert text == "move.l dl_TimeReq(a0),d0"
    assert comment == ""
    assert comment_parts == ()
    assert used_structs == {"DosLibrary"}


def test_render_instruction_text_does_not_field_substitute_dynamic_indexed_base_calls() -> None:
    inst = Instruction(offset=0x0104, size=4, opcode=0x4EB0,
                       text="corrupted",
                       raw=struct.pack(">HH", 0x4EB0, 0x0000),
                       kb_mnemonic="jsr", operand_size="w",
                       operand_texts=("0(a6,d0.w)",),
                       opcode_text="jsr")
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0104: {"a6": TypedMemoryRegion(
            struct="DosLibrary",
            size=runtime_os.STRUCTS["DosLibrary"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.APP, "a6", 100),
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={100: "app_dos_base"},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(app_base=(6, 0)),
        os_kb=SimpleNamespace(
            META=runtime_os.META,
            STRUCTS=runtime_os.STRUCTS,
            CONSTANTS={},
            LIBRARIES={},
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    used_structs: set[str] = set()

    text, comment, comment_parts = render_instruction_text(inst, session, used_structs)

    assert text == "jsr 0(a6,d0.w)"
    assert comment == ""
    assert comment_parts == ()
    assert used_structs == set()


def test_apply_field_value_domain_substitutions_uses_kb_constant() -> None:
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0104: {"a1": TypedMemoryRegion(
            struct="IO",
            size=runtime_os.STRUCTS["IO"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.REGISTER, "a6", 100),
            context_name="trackdisk.device",
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=SimpleNamespace(
            META=runtime_os.META,
            STRUCTS=runtime_os.STRUCTS,
            CONSTANTS=runtime_os.CONSTANTS,
            LIBRARIES={},
            FIELD_CONTEXT_VALUE_DOMAINS=runtime_os.FIELD_CONTEXT_VALUE_DOMAINS,
            FIELD_VALUE_DOMAINS=runtime_os.FIELD_VALUE_DOMAINS,
            VALUE_DOMAINS=runtime_os.VALUE_DOMAINS,
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    operands = (
        SemanticOperand(
            kind="immediate",
            text="#$0002",
            value=2,
        ),
        SemanticOperand(
            kind="base_displacement_symbol",
            text="IO_COMMAND(a1)",
            base_register="a1",
            displacement=28,
            metadata=StructFieldOperandMetadata(
                symbol="IO_COMMAND",
                owner_struct="IO",
                field_symbol="IO_COMMAND",
                context_name="trackdisk.device",
            ),
        ),
    )

    rewritten = _apply_field_value_domain_substitutions(operands, session)

    assert rewritten[0].text == "#CMD_READ"
    assert rewritten[1] == operands[1]


def test_apply_field_value_domain_substitutions_rejects_unknown_kb_constant() -> None:
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0x0104: {"a1": TypedMemoryRegion(
            struct="IO",
            size=runtime_os.STRUCTS["IO"].size,
            provenance=_prov_base(MemoryRegionAddressSpace.REGISTER, "a6", 100),
            context_name="trackdisk.device",
        )}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=SimpleNamespace(
            META=runtime_os.META,
            STRUCTS=runtime_os.STRUCTS,
            CONSTANTS=runtime_os.CONSTANTS,
            LIBRARIES={},
            FIELD_CONTEXT_VALUE_DOMAINS=runtime_os.FIELD_CONTEXT_VALUE_DOMAINS,
            FIELD_VALUE_DOMAINS=runtime_os.FIELD_VALUE_DOMAINS,
            VALUE_DOMAINS=runtime_os.VALUE_DOMAINS,
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    operands = (
        SemanticOperand(
            kind="immediate",
            text="#$1234",
            value=0x1234,
        ),
        SemanticOperand(
            kind="base_displacement_symbol",
            text="IO_COMMAND(a1)",
            base_register="a1",
            displacement=28,
            metadata=StructFieldOperandMetadata(
                symbol="IO_COMMAND",
                owner_struct="IO",
                field_symbol="IO_COMMAND",
                context_name="trackdisk.device",
            ),
        ),
    )

    with pytest.raises(ValueError, match="No KB value-domain match"):
        _apply_field_value_domain_substitutions(operands, session)

