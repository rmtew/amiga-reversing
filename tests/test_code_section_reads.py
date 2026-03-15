"""Test that the executor resolves indirect calls through code-section data.

When a register holds a concrete address within the code section, memory
reads from that address should return the actual bytes from the code buffer.
This lets the executor resolve indirect jumps/calls through data pointers,
function tables, and dispatch structures without format-specific parsers.

Examples:
    lea table(pc),a0    ; a0 = concrete address in code section
    movea.l (a0),a0     ; reads longword from code -> a0 = handler addr
    jsr (a0)            ; resolved through propagation

    lea table(pc),a0    ; a0 = concrete address
    move.w (a0),d0      ; reads word offset from code -> d0 = concrete
    jsr 0(a0,d0.w)      ; resolved: a0 + d0 = handler addr
"""
import struct


def _assemble(*words):
    """Pack 16-bit words into bytes."""
    return struct.pack(">" + "H" * len(words), *words)


def test_resolve_jsr_through_longword_pointer():
    """jsr (a0) where a0 was loaded from a longword in the code section."""
    from m68k.m68k_executor import analyze
    from m68k.jump_tables import resolve_indirect_targets

    code = bytearray(0x60)

    # 0x0000: lea 0x1e(pc),a0  -> a0 = 0x0020 (data)
    code[0x00:0x04] = _assemble(0x41FA, 0x001E)
    # 0x0004: movea.l (a0),a0  -> a0 = longword at 0x0020 = 0x0040
    code[0x04:0x06] = _assemble(0x2050)
    # 0x0006: jsr (a0)         -> call handler at 0x0040
    code[0x06:0x08] = _assemble(0x4E90)
    # 0x0008: rts
    code[0x08:0x0A] = _assemble(0x4E75)

    # Data at 0x0020: longword pointer to handler
    struct.pack_into(">I", code, 0x0020, 0x00000040)

    # Handler at 0x0040: moveq #1,d0; rts
    code[0x40:0x44] = _assemble(0x7001, 0x4E75)

    code = bytes(code)
    result = analyze(code, base_addr=0, entry_points=[0], propagate=True)

    resolved = resolve_indirect_targets(
        result["blocks"], result.get("exit_states", {}), len(code))

    targets = {r["target"] for r in resolved}
    assert 0x0040 in targets, (
        f"handler at 0x0040 not resolved; got targets: "
        f"{[hex(t) for t in targets]}")


def test_resolve_jsr_through_pointer_table():
    """jsr (a1) where a1 loaded from a table of longword pointers."""
    from m68k.m68k_executor import analyze
    from m68k.jump_tables import resolve_indirect_targets

    code = bytearray(0x80)

    # 0x0000: lea 0x1e(pc),a0   -> a0 = 0x0020 (pointer table)
    code[0x00:0x04] = _assemble(0x41FA, 0x001E)
    # 0x0004: movea.l (a0),a1   -> a1 = longword at 0x0020 = 0x0060
    code[0x04:0x06] = _assemble(0x2250)
    # 0x0006: jsr (a1)          -> call handler at 0x0060
    code[0x06:0x08] = _assemble(0x4E91)
    # 0x0008: movea.l 4(a0),a1  -> a1 = longword at 0x0024 = 0x0070
    code[0x08:0x0C] = _assemble(0x2268, 0x0004)
    # 0x000c: jsr (a1)          -> call handler at 0x0070
    code[0x0C:0x0E] = _assemble(0x4E91)
    # 0x000e: rts
    code[0x0E:0x10] = _assemble(0x4E75)

    # Pointer table at 0x0020
    struct.pack_into(">I", code, 0x0020, 0x00000060)  # -> handler1
    struct.pack_into(">I", code, 0x0024, 0x00000070)  # -> handler2

    # Handlers
    code[0x60:0x64] = _assemble(0x7001, 0x4E75)  # moveq #1,d0; rts
    code[0x70:0x74] = _assemble(0x7002, 0x4E75)  # moveq #2,d0; rts

    code = bytes(code)
    result = analyze(code, base_addr=0, entry_points=[0], propagate=True)

    resolved = resolve_indirect_targets(
        result["blocks"], result.get("exit_states", {}), len(code))

    targets = {r["target"] for r in resolved}
    assert 0x0060 in targets, (
        f"handler1 at 0x0060 not resolved; got: "
        f"{[hex(t) for t in targets]}")
    assert 0x0070 in targets, (
        f"handler2 at 0x0070 not resolved; got: "
        f"{[hex(t) for t in targets]}")


def test_handler_becomes_block():
    """Resolved handler should become a block when fed back as entry point."""
    from m68k.m68k_executor import analyze
    from m68k.jump_tables import resolve_indirect_targets

    code = bytearray(0x60)

    # Same as test_resolve_jsr_through_longword_pointer
    code[0x00:0x04] = _assemble(0x41FA, 0x001E)
    code[0x04:0x06] = _assemble(0x2050)
    code[0x06:0x08] = _assemble(0x4E90)
    code[0x08:0x0A] = _assemble(0x4E75)
    struct.pack_into(">I", code, 0x0020, 0x00000040)
    code[0x40:0x44] = _assemble(0x7001, 0x4E75)
    code = bytes(code)

    # First pass
    result = analyze(code, base_addr=0, entry_points=[0], propagate=True)
    resolved = resolve_indirect_targets(
        result["blocks"], result.get("exit_states", {}), len(code))

    # Feed resolved targets as entry points
    entries = {0} | {r["target"] for r in resolved}
    result2 = analyze(code, base_addr=0,
                      entry_points=sorted(entries), propagate=True)

    assert 0x0040 in result2["blocks"], (
        "handler at 0x0040 should be a block after re-analysis")
