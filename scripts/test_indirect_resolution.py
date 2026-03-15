#!/usr/bin/env py.exe
"""Tests for indirect jump/call resolution through register tracing.

Tests drive development of:
1. Displacement-based indirect resolution (jmp/jsr d(An))
2. Indexed indirect resolution (jsr d(An,Xn))
3. Per-caller trampoline resolution (callee reads return address from stack)
4. Per-caller dispatch resolution (callee uses caller's register value)
5. Structure field code pointer resolution

All tests construct synthetic M68K code, run the executor with propagation,
then verify that resolve_indirect_targets produces the expected targets.

GenAm patterns modelled:
- sub_16e0: movea.l (sp),a0; addq.l #2,(sp); ...; movea.l (sp)+,a0; jmp 2(a0)
- dos_dispatch: movea.l app_dos_base(a6),a6; jsr 0(a6,d0.w)
"""

import sys
import struct
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))

from m68k_executor import (analyze, CPUState, AbstractMemory,
                            _concrete, _unknown)
from jump_tables import resolve_indirect_targets, resolve_per_caller


# ---- Helpers ----------------------------------------------------------------

# Minimal platform config enabling SP tracking (symbolic SP at entry).
# All propagation-based tests need this for BSR/JSR stack tracking.
_MINIMAL_PLATFORM = {"scratch_regs": []}


def _analyze_and_resolve(code, entry_points=None, platform=None):
    """Run full analysis pipeline: propagation, direct resolution, per-caller."""
    if platform is None:
        platform = dict(_MINIMAL_PLATFORM)
    result = analyze(code, propagate=True, entry_points=entry_points,
                     platform=platform)
    blocks = result["blocks"]
    exit_states = result.get("exit_states", {})
    resolved = resolve_indirect_targets(blocks, exit_states, len(code))
    resolved += resolve_per_caller(
        blocks, exit_states, code, len(code), platform=platform)
    return blocks, exit_states, resolved


def _resolved_targets(resolved):
    """Extract sorted unique target addresses from resolution results."""
    return sorted(set(r["target"] for r in resolved))


# ---- 1. Displacement indirect: jmp/jsr d(An) with concrete An --------------

def test_disp_indirect_jmp():
    """JMP d(An) where An is concrete should resolve to An + d."""
    code = b''
    # lea $20(pc),a0  -> a0 = $00 + 2 + $20 = $22
    code += struct.pack('>HH', 0x41FA, 0x0020)         # [0x00] lea $20(pc),a0
    # jmp 4(a0)  -> target = $22 + 4 = $26
    code += struct.pack('>HH', 0x4EE8, 0x0004)         # [0x04] jmp 4(a0)
    code += b'\x4e\x71' * 20                            # [0x08..] nop padding

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x26 in targets, (
        f"Expected $0026 from jmp 4(a0) where a0=$0022, got {targets}")
    print("  disp_indirect_jmp: OK")


def test_disp_indirect_jsr():
    """JSR d(An) where An is concrete should resolve to An + d."""
    code = b''
    # lea $18(pc),a2  -> a2 = $00 + 2 + $18 = $1a
    code += struct.pack('>HH', 0x45FA, 0x0018)         # [0x00] lea $18(pc),a2
    # jsr 6(a2)  -> target = $1a + 6 = $20
    code += struct.pack('>HH', 0x4EAA, 0x0006)         # [0x04] jsr 6(a2)
    code += struct.pack('>H', 0x4E75)                   # [0x08] rts
    code += b'\x4e\x71' * 14                            # [0x0a..] nop padding

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x20 in targets, (
        f"Expected $0020 from jsr 6(a2) where a2=$001a, got {targets}")
    print("  disp_indirect_jsr: OK")


# ---- 2. Indexed indirect: jsr d(An,Dn.w) with concrete An + Dn -------------

def test_indexed_indirect_jsr():
    """JSR d(An,Dn.w) where both An and Dn are concrete should resolve."""
    code = b''
    # moveq #-10,d0  -> d0.w = $FFF6 = -10
    code += struct.pack('>H', 0x70F6)                   # [0x00] moveq #-10,d0
    # lea $30(pc),a1  -> a1 = $02 + 2 + $30 = $34
    code += struct.pack('>HH', 0x43FA, 0x0030)          # [0x02] lea $30(pc),a1
    # jsr 0(a1,d0.w)  -> target = $34 + (-10) + 0 = $2a
    # JSR index(A1): 0100 1110 10 110 001 = $4EB1
    # ext word: D/A=0, REG=000(d0), W/L=0, disp=0 -> $0000
    code += struct.pack('>HH', 0x4EB1, 0x0000)          # [0x06] jsr 0(a1,d0.w)
    code += struct.pack('>H', 0x4E75)                    # [0x0a] rts
    code += b'\x4e\x71' * 24                             # [0x0c..] nop padding

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x2a in targets, (
        f"Expected $002a from jsr 0(a1,d0.w), got {targets}")
    print("  indexed_indirect_jsr: OK")


def test_indexed_indirect_with_displacement():
    """JSR d(An,Dn.w) with non-zero extension word displacement."""
    code = b''
    # moveq #4,d2
    code += struct.pack('>H', 0x7404)                   # [0x00] moveq #4,d2
    # lea $28(pc),a3  -> a3 = $02 + 2 + $28 = $2c
    code += struct.pack('>HH', 0x47FA, 0x0028)          # [0x02] lea $28(pc),a3
    # jsr 2(a3,d2.w)  -> target = $2c + 4 + 2 = $32
    # JSR index(A3): 0100 1110 10 110 011 = $4EB3
    # ext word: D/A=0, REG=010(d2), W/L=0, disp=2 -> $2002
    code += struct.pack('>HH', 0x4EB3, 0x2002)          # [0x06] jsr 2(a3,d2.w)
    code += struct.pack('>H', 0x4E75)                    # [0x0a] rts
    code += b'\x4e\x71' * 24                             # [0x0c..] nop padding

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x32 in targets, (
        f"Expected $0032 from jsr 2(a3,d2.w), got {targets}")
    print("  indexed_indirect_with_displacement: OK")


# ---- 3. Trampoline: callee uses return address (models GenAm sub_16e0) ------

def test_trampoline_basic():
    """Single caller, pop return address, jmp d(a0).

    Simplest trampoline: BSR pushes return address, callee pops it
    and jumps past 2-byte inline data via displacement.
    """
    code = b''
    # bsr.w $08  (disp = $08 - ($00+2) = $06)  -> pushes return addr $04
    code += struct.pack('>HH', 0x6100, 0x0006)          # [0x00] bsr.w $08
    code += struct.pack('>H', 0x1234)                    # [0x04] dc.w (inline param)
    code += struct.pack('>H', 0x4E75)                    # [0x06] rts (resume point)
    # Trampoline at $08
    code += struct.pack('>H', 0x205F)                    # [0x08] movea.l (sp)+,a0
    code += struct.pack('>HH', 0x4EE8, 0x0002)          # [0x0a] jmp 2(a0) -> $06

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x06 in targets, (
        f"Expected $0006 (resume past inline data), got {targets}")
    print("  trampoline_basic: OK")


def test_trampoline_modified_return_addr():
    """Single caller, return address modified on stack before pop.

    Models GenAm sub_16e0 faithfully:
    1. movea.l (sp),a0     -- read return addr (non-destructive)
    2. addq.l #2,(sp)      -- modify stack: return_addr += 2
    3. move.w (a0),d0      -- read 2-byte inline param
    4. movea.l (sp)+,a0    -- pop modified addr (original + 2)
    5. jmp 2(a0)           -- target = original + 2 + 2 = original + 4

    Caller has 4 bytes of inline data after BSR.
    """
    code = b''
    # Caller at $00
    # bsr.w $0C  (disp = $0C - ($00+2) = $0A)  -> pushes $04
    code += struct.pack('>HH', 0x6100, 0x000A)          # [0x00] bsr.w $0C
    code += struct.pack('>H', 0x0025)                    # [0x04] dc.w (param)
    code += struct.pack('>H', 0x4E71)                    # [0x06] nop (RTS path)
    code += struct.pack('>H', 0x4E75)                    # [0x08] rts (jmp resume)
    code += struct.pack('>H', 0x4E71)                    # [0x0a] nop
    # Trampoline at $0C
    code += struct.pack('>H', 0x2057)                    # [0x0c] movea.l (sp),a0
    code += struct.pack('>H', 0x5497)                    # [0x0e] addq.l #2,(sp)
    code += struct.pack('>H', 0x3010)                    # [0x10] move.w (a0),d0
    code += struct.pack('>H', 0x205F)                    # [0x12] movea.l (sp)+,a0
    code += struct.pack('>HH', 0x4EE8, 0x0002)          # [0x14] jmp 2(a0)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # BSR pushes $04. addq.l #2 -> $06. jmp 2(a0) -> $06+2 = $08.
    assert 0x08 in targets, (
        f"Expected $0008 (skip 4 bytes inline data), got {targets}")
    print("  trampoline_modified_return_addr: OK")


def test_trampoline_per_caller():
    """Two callers to shared trampoline, must resolve per-caller.

    Both callers are reachable from entry 0 via sequential flow.
    Caller A's jmp-path resume falls through to caller B's BSR.

    Per-caller analysis is required because the merge at the trampoline
    entry joins two different return addresses into unknown.
    """
    code = b''
    # Caller A at $00
    # bsr.w $12  (disp = $12 - $02 = $10)  -> pushes $04
    code += struct.pack('>HH', 0x6100, 0x0010)          # [0x00] bsr.w $12
    code += struct.pack('>H', 0x0025)                    # [0x04] dc.w (param A)
    code += struct.pack('>H', 0x4E71)                    # [0x06] nop (RTS path A)
    # Caller B at $08 (also jmp resume for caller A: $04+2+2 = $08)
    # bsr.w $12  (disp = $12 - $0A = $08)  -> pushes $0C
    code += struct.pack('>HH', 0x6100, 0x0008)          # [0x08] bsr.w $12
    code += struct.pack('>H', 0x003D)                    # [0x0c] dc.w (param B)
    code += struct.pack('>H', 0x4E71)                    # [0x0e] nop (RTS path B)
    # $10 = jmp resume for caller B: $0C+2+2 = $10
    code += struct.pack('>H', 0x4E75)                    # [0x10] rts (end)
    # Trampoline at $12
    code += struct.pack('>H', 0x2057)                    # [0x12] movea.l (sp),a0
    code += struct.pack('>H', 0x5497)                    # [0x14] addq.l #2,(sp)
    code += struct.pack('>H', 0x3010)                    # [0x16] move.w (a0),d0
    code += struct.pack('>H', 0x205F)                    # [0x18] movea.l (sp)+,a0
    code += struct.pack('>HH', 0x4EE8, 0x0002)          # [0x1a] jmp 2(a0)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # Caller A: BSR pushes $04, +2=$06, jmp 2=$08
    # Caller B: BSR pushes $0C, +2=$0E, jmp 2=$10
    assert 0x08 in targets, (
        f"Expected $0008 (caller A resume), got {targets}")
    assert 0x10 in targets, (
        f"Expected $0010 (caller B resume), got {targets}")
    print("  trampoline_per_caller: OK")


# ---- 4. Library dispatch (models GenAm dos_dispatch) ------------------------

def test_indexed_dispatch_single():
    """Single caller, JSR 0(An,Dn.w) with base from platform memory.

    Models the LVO dispatch path: load library base from app memory
    via displacement off the base register, then indexed call.
    """
    sentinel_a6 = 0x80000000
    lib_base = 0x30

    code = b''
    # moveq #-6,d0  -> d0 = $FFFFFFFA, d0.w = -6
    code += struct.pack('>H', 0x70FA)                    # [0x00] moveq #-6,d0
    # movea.l 100(a6),a6  -> a6 = mem[sentinel + 100] = lib_base
    code += struct.pack('>HH', 0x2C6E, 0x0064)          # [0x02] movea.l 100(a6),a6
    # jsr 0(a6,d0.w)  -> target = $30 + (-6) = $2a
    code += struct.pack('>HH', 0x4EB6, 0x0000)          # [0x06] jsr 0(a6,d0.w)
    code += struct.pack('>H', 0x4E75)                    # [0x0a] rts
    code += b'\x4e\x71' * 15                             # [0x0c..$29] nop
    code += struct.pack('>H', 0x4E75)                    # [0x2a] rts (target)
    code += b'\x4e\x71' * 2                              # pad

    init_mem = AbstractMemory()
    init_mem.write(sentinel_a6 + 100, _concrete(lib_base), "l")

    platform = {
        "initial_base_reg": (6, sentinel_a6),
        "_initial_mem": init_mem,
        "scratch_regs": [],
    }

    _, _, resolved = _analyze_and_resolve(code, platform=platform)
    targets = _resolved_targets(resolved)
    assert 0x2a in targets, (
        f"Expected $002a from jsr 0(a6,d0.w), got {targets}")
    print("  indexed_dispatch_single: OK")


def test_dispatch_per_caller():
    """Two callers to shared dispatch sub with different D0 (LVO) values.

    Models GenAm dos_dispatch: each caller sets D0 to a specific LVO
    offset, then BSRs to the shared dispatch routine. Both callers are
    reachable from entry 0 via sequential flow.

    Per-caller analysis is required because D0 differs per caller and
    the merge at the dispatch entry makes D0 unknown.
    """
    sentinel_a6 = 0x80000000
    lib_base = 0x40

    code = b''
    # Caller A: moveq #-6,d0; bsr.w dispatch
    code += struct.pack('>H', 0x70FA)                    # [0x00] moveq #-6,d0
    # bsr.w $0E  (disp = $0E - $04 = $0A)
    code += struct.pack('>HH', 0x6100, 0x000A)          # [0x02] bsr.w $0E
    # Caller B: moveq #-12,d0; bsr.w dispatch (reachable via fallthrough)
    code += struct.pack('>H', 0x70F4)                    # [0x06] moveq #-12,d0
    # bsr.w $0E  (disp = $0E - $0A = $04)
    code += struct.pack('>HH', 0x6100, 0x0004)          # [0x08] bsr.w $0E
    code += struct.pack('>H', 0x4E75)                    # [0x0c] rts
    # Dispatch sub at $0E (models dos_dispatch)
    code += struct.pack('>H', 0x2F0E)                    # [0x0e] move.l a6,-(sp)
    code += struct.pack('>HH', 0x2C6E, 0x0064)          # [0x10] movea.l 100(a6),a6
    code += struct.pack('>HH', 0x4EB6, 0x0000)          # [0x14] jsr 0(a6,d0.w)
    code += struct.pack('>H', 0x2C5F)                    # [0x18] movea.l (sp)+,a6
    code += struct.pack('>H', 0x4E75)                    # [0x1a] rts
    # Padding for targets: $40+(-6)=$3a, $40+(-12)=$34
    code += b'\x4e\x71' * 18                             # [0x1c..$41] nop

    init_mem = AbstractMemory()
    init_mem.write(sentinel_a6 + 100, _concrete(lib_base), "l")

    platform = {
        "initial_base_reg": (6, sentinel_a6),
        "_initial_mem": init_mem,
        "scratch_regs": [],
    }

    _, _, resolved = _analyze_and_resolve(code, platform=platform)
    targets = _resolved_targets(resolved)
    # Caller A: d0=-6,  target = $40 + (-6)  = $3a
    # Caller B: d0=-12, target = $40 + (-12) = $34
    assert 0x3a in targets, (
        f"Expected $003a (caller A: lib_base+(-6)), got {targets}")
    assert 0x34 in targets, (
        f"Expected $0034 (caller B: lib_base+(-12)), got {targets}")
    print("  dispatch_per_caller: OK")


# ---- 5. Structure field access ----------------------------------------------

def test_struct_field_code_pointer():
    """Load a code pointer from a struct field and jump through it.

    An points to a structure in code memory. A field at offset d
    contains a code address. MOVEA.L d(An),Am; JSR (Am) should resolve
    when the struct's field values are known (readable from code bytes).
    """
    code = b''
    # lea $1c(pc),a0  -> a0 = $00 + 2 + $1c = $1e (struct base)
    code += struct.pack('>HH', 0x41FA, 0x001C)          # [0x00] lea $1c(pc),a0
    # movea.l 2(a0),a1  -> a1 = long at $1e+2 = $20
    code += struct.pack('>HH', 0x2268, 0x0002)          # [0x04] movea.l 2(a0),a1
    # jsr (a1)  -> target = value at $20 in code bytes
    code += struct.pack('>H', 0x4E91)                    # [0x08] jsr (a1)
    code += struct.pack('>H', 0x4E75)                    # [0x0a] rts
    # Target subroutine at $0c
    code += struct.pack('>H', 0x4E75)                    # [0x0c] rts
    # Pad to struct at $1e
    code += b'\x4e\x71' * 8                              # [0x0e..$1d] nop
    # Struct at $1e: field+0 = don't care, field+2 = code pointer to $0c
    code += struct.pack('>H', 0x0000)                    # [0x1e] field 0
    code += struct.pack('>I', 0x0000000C)                # [0x20] field 2 = $0c

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x0c in targets, (
        f"Expected $000c loaded from struct field, got {targets}")
    print("  struct_field_code_pointer: OK")


def test_struct_field_disp_indirect():
    """Load base from struct field, then JMP d(An) through it.

    Combines struct field resolution with displacement indirect:
    An points to struct, load base from struct, JMP d(Am) using base.
    """
    code = b''
    # lea $1c(pc),a2  -> a2 = $00 + 2 + $1c = $1e (struct base)
    code += struct.pack('>HH', 0x45FA, 0x001C)          # [0x00] lea $1c(pc),a2
    # movea.l (a2),a3  -> a3 = long at $1e
    code += struct.pack('>H', 0x2652)                    # [0x04] movea.l (a2),a3
    # jmp 4(a3)  -> target = mem[$1e] + 4
    code += struct.pack('>HH', 0x4EEB, 0x0004)          # [0x06] jmp 4(a3)
    code += struct.pack('>H', 0x4E75)                    # [0x0a] rts
    code += struct.pack('>H', 0x4E75)                    # [0x0c] rts (target)
    code += struct.pack('>H', 0x4E75)                    # [0x0e] rts
    # Pad to struct at $1e
    code += b'\x4e\x71' * 7                              # [0x10..$1d] nop
    # Struct at $1e: long value = $08, so target = $08 + 4 = $0c
    code += struct.pack('>I', 0x00000008)                # [0x1e] struct field = $08

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x0c in targets, (
        f"Expected $000c from jmp 4(a3) where a3 from struct, got {targets}")
    print("  struct_field_disp_indirect: OK")


# ---- 6. PEA+RTS dispatch (models GenAm $7550 addressing mode handlers) ------

def test_pea_rts_simple():
    """PEA target(PC); RTS dispatches to the PEA'd address.

    Simplest case: PEA pushes a PC-relative address onto the stack,
    RTS pops and jumps to it.  This is a common pattern for pushing
    a continuation address before calling a subroutine, but also
    used as a computed goto when the PEA'd address is the target.
    """
    code = b''
    # pea $0a(pc)  -> pushes $00 + 2 + $0a = $0c
    # PEA pcdisp: 0100 1000 01 111 010 = $487A
    code += struct.pack('>HH', 0x487A, 0x000A)          # [0x00] pea $0a(pc)
    code += struct.pack('>H', 0x4E71)                    # [0x04] nop
    code += struct.pack('>H', 0x4E75)                    # [0x06] rts -> $0c
    code += struct.pack('>H', 0x4E71)                    # [0x08] nop
    code += struct.pack('>H', 0x4E71)                    # [0x0a] nop
    # Target at $0c
    code += struct.pack('>H', 0x4E75)                    # [0x0c] rts (target)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x0c in targets, (
        f"Expected $000c (PEA'd address), got {targets}")
    print("  pea_rts_simple: OK")


def test_pea_rts_computed():
    """PEA return_point; LEA base; ADDA.W Dn; MOVE.L An,-(SP); RTS.

    Models GenAm $7550: two addresses pushed, RTS dispatches to the
    top one (the computed handler). The handler's own RTS returns to
    the PEA'd continuation point below it on the stack.

    Stack layout before RTS:
        SP   -> handler_addr     (from MOVE.L A0,-(SP))
        SP+4 -> return_point     (from PEA)

    RTS pops handler_addr and jumps to it.
    """
    code = b''
    # moveq #10,d3  -> d3 = 10 (handler offset)
    code += struct.pack('>H', 0x760A)                    # [0x00] moveq #10,d3
    # pea $24(pc)  -> pushes $02 + 2 + $24 = $28 (return point)
    code += struct.pack('>HH', 0x487A, 0x0024)          # [0x02] pea $28(pc)
    # lea $18(pc),a0  -> a0 = $06 + 2 + $18 = $20 (handler base)
    code += struct.pack('>HH', 0x41FA, 0x0018)          # [0x06] lea $18(pc),a0
    # adda.w d3,a0  -> a0 = $20 + 10 = $2a (handler)
    code += struct.pack('>H', 0xD0C3)                    # [0x0a] adda.w d3,a0
    # move.l a0,-(sp)  -> push handler addr $2a
    code += struct.pack('>H', 0x2F08)                    # [0x0c] move.l a0,-(sp)
    # rts  -> pops $2a, jumps to handler
    code += struct.pack('>H', 0x4E75)                    # [0x0e] rts
    # Padding
    code += b'\x4e\x71' * 8                              # [0x10..$1f] nop
    # Handler base at $20, handler at $2a
    code += b'\x4e\x71' * 5                              # [0x20..$29] nop
    code += struct.pack('>H', 0x4E75)                    # [0x2a] rts (handler)
    code += b'\x4e\x71' * 2                              # pad

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # RTS should resolve to $2a (handler) AND $28 (return point via handler RTS)
    assert 0x2a in targets, (
        f"Expected $002a (computed handler), got {targets}")
    print("  pea_rts_computed: OK")


def test_pea_rts_per_caller():
    """PEA+RTS dispatch with varying offset per caller.

    Two callers each set D3 to a different handler offset before
    reaching the shared dispatch code. Per-caller analysis resolves
    each to a different handler address.

    Models GenAm: D3 loaded from a per-instruction data table entry,
    then LEA base + ADDA.W D3 + MOVE.L A0,-(SP) + RTS dispatches.
    """
    code = b''
    # Caller A: moveq #4,d3; bsr.w dispatch
    code += struct.pack('>H', 0x7604)                    # [0x00] moveq #4,d3
    # bsr.w $0C  (disp = $0C - $04 = $08)
    code += struct.pack('>HH', 0x6100, 0x0008)          # [0x02] bsr.w $0C
    # Caller B: moveq #10,d3; bsr.w dispatch (reachable via fallthrough)
    code += struct.pack('>H', 0x760A)                    # [0x06] moveq #10,d3
    # bsr.w $0C  (disp = $0C - $0A = $02)
    code += struct.pack('>HH', 0x6100, 0x0002)          # [0x08] bsr.w $0C
    code += struct.pack('>H', 0x4E75)                    # [0x0c] rts (end)
    # Dispatch sub at $0E -- but wait, $0C is where we want dispatch.
    # Let me recalculate. BSR at $02 to dispatch. dispatch should be
    # after both callers.

    # Recalculate layout:
    code = b''
    # Caller A at $00: moveq #4,d3; bsr.w dispatch($10)
    code += struct.pack('>H', 0x7604)                    # [0x00] moveq #4,d3
    # bsr.w $10  (disp = $10 - $04 = $0C)
    code += struct.pack('>HH', 0x6100, 0x000C)          # [0x02] bsr.w $10
    # Caller B at $06: moveq #10,d3; bsr.w dispatch($10)
    code += struct.pack('>H', 0x760A)                    # [0x06] moveq #10,d3
    # bsr.w $10  (disp = $10 - $0A = $06)
    code += struct.pack('>HH', 0x6100, 0x0006)          # [0x08] bsr.w $10
    code += struct.pack('>H', 0x4E75)                    # [0x0c] rts (end)
    code += struct.pack('>H', 0x4E71)                    # [0x0e] nop
    # Dispatch sub at $10
    # lea $20(pc),a0  -> a0 = $10 + 2 + $20 = $32 (handler base)
    code += struct.pack('>HH', 0x41FA, 0x0020)          # [0x10] lea $20(pc),a0
    # adda.w d3,a0  -> a0 = $32 + d3
    code += struct.pack('>H', 0xD0C3)                    # [0x14] adda.w d3,a0
    # move.l a0,-(sp)  -> push handler address
    code += struct.pack('>H', 0x2F08)                    # [0x16] move.l a0,-(sp)
    # rts  -> dispatch to handler (pops handler, return addr below it)
    code += struct.pack('>H', 0x4E75)                    # [0x18] rts
    # Padding to handler base
    code += b'\x4e\x71' * 12                             # [0x1a..$31] nop
    # Handler base at $32
    # Caller A: $32 + 4 = $36
    # Caller B: $32 + 10 = $3c
    code += b'\x4e\x71' * 6                              # [0x32..$3d] nop
    # Ensure targets are within range
    code += b'\x4e\x71' * 2                              # pad

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # Caller A: d3=4,  handler = $32 + 4  = $36
    # Caller B: d3=10, handler = $32 + 10 = $3c
    assert 0x36 in targets, (
        f"Expected $0036 (caller A handler: base+4), got {targets}")
    assert 0x3c in targets, (
        f"Expected $003c (caller B handler: base+10), got {targets}")
    print("  pea_rts_per_caller: OK")


def test_pea_rts_with_interleaved_call():
    """PEA continuation; BSR processing; RTS dispatches.

    Models GenAm pattern where PEA pushes a return point, then a BSR
    calls a processing subroutine, then RTS pops the PEA'd address
    (not the BSR return address, which was already consumed by the
    subroutine's own RTS).

    Stack evolution:
        PEA target       SP -> target
        BSR sub           SP -> return_addr, target
        (sub's RTS)       SP -> target
        RTS               jumps to target
    """
    code = b''
    # pea $12(pc)  -> pushes $00 + 2 + $12 = $14 (continuation)
    code += struct.pack('>HH', 0x487A, 0x0012)          # [0x00] pea $12(pc)
    # bsr.w $0C  (disp = $0C - $06 = $06)
    code += struct.pack('>HH', 0x6100, 0x0006)          # [0x04] bsr.w $0C
    # nop (fallthrough after bsr returns)
    code += struct.pack('>H', 0x4E71)                    # [0x08] nop
    # rts -> pops PEA'd address $14
    code += struct.pack('>H', 0x4E75)                    # [0x0a] rts -> $14
    # Subroutine at $0C
    code += struct.pack('>H', 0x4E71)                    # [0x0c] nop
    code += struct.pack('>H', 0x4E75)                    # [0x0e] rts (returns to $08)
    # Padding
    code += struct.pack('>H', 0x4E71)                    # [0x10] nop
    code += struct.pack('>H', 0x4E71)                    # [0x12] nop
    # Continuation target at $14
    code += struct.pack('>H', 0x4E75)                    # [0x14] rts (target)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x14 in targets, (
        f"Expected $0014 (PEA'd continuation after BSR cycle), got {targets}")
    print("  pea_rts_with_interleaved_call: OK")


# ---- 7. Edge cases ----------------------------------------------------------

def test_disp_indirect_unknown_register():
    """JMP d(An) where An is unknown should NOT resolve."""
    code = b''
    code += struct.pack('>HH', 0x4EE8, 0x0002)          # [0x00] jmp 2(a0)
    code += b'\x4e\x71' * 8

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert len(targets) == 0, (
        f"Should not resolve with unknown a0, got {targets}")
    print("  disp_indirect_unknown_register: OK")


def test_indexed_indirect_unknown_index():
    """JSR d(An,Dn.w) where Dn is unknown should NOT resolve."""
    code = b''
    # lea $30(pc),a1  -> a1 = $32 (known)
    code += struct.pack('>HH', 0x43FA, 0x0030)          # [0x00] lea $30(pc),a1
    # jsr 0(a1,d0.w)  -- d0 unknown
    code += struct.pack('>HH', 0x4EB1, 0x0000)          # [0x04] jsr 0(a1,d0.w)
    code += struct.pack('>H', 0x4E75)                    # [0x08] rts
    code += b'\x4e\x71' * 24

    _, _, resolved = _analyze_and_resolve(code)
    jsr_resolved = [r for r in resolved
                    if r.get("target", 0) != 0]
    # The JSR at $04 should not resolve (D0 unknown)
    # But other instructions might resolve via other mechanisms
    # Filter: no target in the code range should come from the JSR block
    assert len(jsr_resolved) == 0, (
        f"Should not resolve with unknown d0, got {jsr_resolved}")
    print("  indexed_indirect_unknown_index: OK")


def test_disp_indirect_target_out_of_range():
    """JMP d(An) resolving outside code range should NOT resolve."""
    code = b''
    # lea $10(pc),a0  -> a0 = $12
    code += struct.pack('>HH', 0x41FA, 0x0010)          # [0x00] lea $10(pc),a0
    # jmp $7ffe(a0)  -> target = $12 + $7ffe = $8010 (out of range)
    code += struct.pack('>HH', 0x4EE8, 0x7FFE)          # [0x04] jmp $7ffe(a0)
    code += b'\x4e\x71' * 8

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert len(targets) == 0, (
        f"Should not resolve out-of-range target, got {targets}")
    print("  disp_indirect_target_out_of_range: OK")


def test_odd_target_not_resolved():
    """JMP d(An) resolving to an odd address should NOT resolve."""
    code = b''
    # lea $10(pc),a0  -> a0 = $12
    code += struct.pack('>HH', 0x41FA, 0x0010)          # [0x00] lea $10(pc),a0
    # jmp 1(a0)  -> target = $12 + 1 = $13 (odd)
    code += struct.pack('>HH', 0x4EE8, 0x0001)          # [0x04] jmp 1(a0)
    code += b'\x4e\x71' * 12

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert len(targets) == 0, (
        f"Should not resolve odd target, got {targets}")
    print("  odd_target_not_resolved: OK")


def test_rts_resolution_preserved():
    """RTS resolution via stack tracking still works after refactor."""
    code = b''
    # bsr.w $08  (disp = $08 - $02 = $06)  -> pushes $04
    code += struct.pack('>HH', 0x6100, 0x0006)          # [0x00] bsr.w $08
    code += struct.pack('>H', 0x4E75)                    # [0x04] rts (after call)
    code += struct.pack('>H', 0x4E71)                    # [0x06] nop
    # Subroutine at $08
    code += struct.pack('>H', 0x4E75)                    # [0x08] rts

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x04 in targets, (
        f"Expected $0004 (RTS return to caller), got {targets}")
    print("  rts_resolution_preserved: OK")


# ---- Run all ----------------------------------------------------------------

if __name__ == "__main__":
    print("Testing indirect jump/call resolution...")

    print("\n1. Displacement indirect (EA mechanics):")
    test_disp_indirect_jmp()
    test_disp_indirect_jsr()

    print("\n2. Indexed indirect (EA mechanics):")
    test_indexed_indirect_jsr()
    test_indexed_indirect_with_displacement()

    print("\n3. Trampoline (GenAm sub_16e0 pattern):")
    test_trampoline_basic()
    test_trampoline_modified_return_addr()
    test_trampoline_per_caller()

    print("\n4. Library dispatch (GenAm dos_dispatch pattern):")
    test_indexed_dispatch_single()
    test_dispatch_per_caller()

    print("\n5. Structure field access:")
    test_struct_field_code_pointer()
    test_struct_field_disp_indirect()

    print("\n6. PEA+RTS dispatch:")
    test_pea_rts_simple()
    test_pea_rts_computed()
    test_pea_rts_per_caller()
    test_pea_rts_with_interleaved_call()

    print("\n7. Edge cases:")
    test_disp_indirect_unknown_register()
    test_indexed_indirect_unknown_index()
    test_disp_indirect_target_out_of_range()
    test_odd_target_not_resolved()
    test_rts_resolution_preserved()

    print(f"\nAll tests passed.")
