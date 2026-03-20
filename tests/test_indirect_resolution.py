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

import struct
from types import SimpleNamespace
from m68k.instruction_kb import instruction_kb
from m68k.m68k_executor import (analyze, CPUState, AbstractMemory,
                                _concrete, _unknown, BasicBlock, XRef)
from m68k.jump_tables import detect_jump_tables, _scan_inline_dispatch, _is_indexed_ea
from m68k.indirect_analysis import (resolve_indirect_targets, resolve_per_caller,
                                    resolve_backward_slice)
from m68k.indirect_core import decode_jump_ea
from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble


# ---- Helpers ----------------------------------------------------------------

# Minimal platform config enabling SP tracking (symbolic SP at entry).
# All propagation-based tests need this for BSR/JSR stack tracking.
_MINIMAL_PLATFORM = {"scratch_regs": []}


def _analyze_and_resolve(code, entry_points=None, platform=None):
    """Run full analysis pipeline: jump tables, direct resolution, per-caller."""
    if platform is None:
        platform = dict(_MINIMAL_PLATFORM)
    result = analyze(code, propagate=True, entry_points=entry_points,
                     platform=platform)
    blocks = result["blocks"]
    exit_states = result.get("exit_states", {})
    resolved = []
    for t in detect_jump_tables(blocks, code):
        for tgt in t["targets"]:
            resolved.append({"target": tgt})
    resolved += resolve_indirect_targets(blocks, exit_states, len(code))
    resolved += resolve_per_caller(
        blocks, exit_states, code, len(code), platform=platform)
    resolved += resolve_backward_slice(
        blocks, exit_states, code, len(code), platform=platform)
    return blocks, exit_states, resolved


def _resolved_targets(resolved):
    """Extract sorted unique target addresses from resolution results."""
    return sorted(set(r["target"] for r in resolved))


def _assemble_with_labels(specs):
    all_labels = {
        payload
        for kind, payload in specs
        if kind == "label"
    }
    labels = {}
    pc = 0
    for kind, payload in specs:
        if kind == "label":
            labels[payload] = pc
            continue
        if kind == "bytes":
            pc += len(payload)
            continue
        if kind != "asm":
            raise AssertionError(f"unknown spec kind {kind!r}")
        text = payload
        if "{table_disp}" in text or "{end_disp}" in text or "{bound_disp}" in text:
            text = text.format(table_disp=0, end_disp=0, bound_disp=0)
        elif "{" in text:
            text = text.format(**{name: 0 for name in all_labels})
        pc += len(assemble_instruction(text, pc=pc))

    code = b""
    pc = 0
    for kind, payload in specs:
        if kind == "label":
            continue
        if kind == "bytes":
            code += payload
            pc += len(payload)
            continue
        text = payload
        if "{table_disp}" in text:
            text = text.format(table_disp=labels["table"] - (pc + 2))
        elif "{bound_disp}" in text:
            text = text.format(bound_disp=labels["bound"] - (pc + 2))
        elif "{end_disp}" in text:
            text = text.format(end_disp=labels["table_end"] - (pc + 2))
        elif "{" in text:
            text = text.format(**labels)
        raw = assemble_instruction(text, pc=pc)
        code += raw
        pc += len(raw)
    return code, labels


def test_is_indexed_ea_uses_shared_decode_for_brief_indexed_mode():
    inst = disassemble(bytes.fromhex("4eb32002"), max_cpu="68020")[0]
    info = _is_indexed_ea(inst, instruction_kb(inst))

    assert info == {
        "base_mode": "an",
        "base_reg": 3,
        "index_is_addr": False,
        "index_reg": 2,
        "displacement": 2,
    }


def test_is_indexed_ea_rejects_full_extension_memory_indirect():
    inst = disassemble(bytes.fromhex("2031212200000004"), max_cpu="68020")[0]

    assert _is_indexed_ea(inst, instruction_kb(inst)) is None




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


def test_full_extension_memory_indirect_indexed_jsr():
    """JSR ([bd,An,Dn.w],od) should resolve through the pointed address."""
    code = b""
    code += struct.pack(">H", 0x7404)                    # [0x00] moveq #4,d2
    code += struct.pack(">HH", 0x43FA, 0x000C)          # [0x02] lea $0c(pc),a1 -> $10
    code += bytes.fromhex("4eb1212200000004")           # [0x06] jsr ([0,a1,d2.w],4)
    code += struct.pack(">H", 0x4E75)                    # [0x0e] rts
    code += struct.pack(">H", 0x4E71)                    # [0x10] nop
    code += struct.pack(">H", 0x4E71)                    # [0x12] nop
    code += struct.pack(">I", 0x0000001C)                # [0x14] dc.l $1c
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x18] nop; nop
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x20 in targets, (
        f"Expected $0020 from jsr ([0,a1,d2.w],4), got {targets}")
    print("  full_extension_memory_indirect_indexed_jsr: OK")


def test_full_extension_pc_memory_indirect_indexed_jsr():
    """JSR ([bd,PC,Dn.w],od) should resolve through the pointed address."""
    code = b""
    code += struct.pack(">H", 0x740C)                    # [0x00] moveq #12,d2
    code += bytes.fromhex("4ebb212200000004")           # [0x02] jsr ([0,pc,d2.w],4)
    code += struct.pack(">H", 0x4E75)                    # [0x0a] rts
    code += struct.pack(">H", 0x4E71)                    # [0x0c] nop
    code += struct.pack(">H", 0x4E71)                    # [0x0e] nop
    code += struct.pack(">I", 0x00000018)                # [0x10] dc.l $18
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x14] nop; nop
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x1C in targets, (
        f"Expected $001c from jsr ([0,pc,d2.w],4), got {targets}")
    print("  full_extension_pc_memory_indirect_indexed_jsr: OK")


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


def test_dispatch_per_caller_multiple_unresolved_in_shared_sub():
    """Two callers, shared dispatch sub, two indirect calls inside the sub."""
    sentinel_a6 = 0x80000000
    lib_base = 0x40

    code = b""
    code += struct.pack(">H", 0x70FA)                    # [0x00] moveq #-6,d0
    code += struct.pack(">HH", 0x6100, 0x000C)          # [0x02] bsr.w $10
    code += struct.pack(">H", 0x70F4)                    # [0x06] moveq #-12,d0
    code += struct.pack(">HH", 0x6100, 0x0006)          # [0x08] bsr.w $10
    code += struct.pack(">H", 0x4E75)                    # [0x0c] rts
    code += struct.pack(">H", 0x4E71)                    # [0x0e] nop
    code += struct.pack(">H", 0x2F0E)                    # [0x10] move.l a6,-(sp)
    code += struct.pack(">HH", 0x2C6E, 0x0064)          # [0x12] movea.l 100(a6),a6
    code += struct.pack(">HH", 0x4EB6, 0x0000)          # [0x16] jsr 0(a6,d0.w)
    code += struct.pack(">HH", 0x4EB6, 0x0002)          # [0x1a] jsr 2(a6,d0.w)
    code += struct.pack(">H", 0x2C5F)                    # [0x1e] movea.l (sp)+,a6
    code += struct.pack(">H", 0x4E75)                    # [0x20] rts
    code += b"\x4e\x71" * 9                              # [0x22..$33] nop
    code += struct.pack(">H", 0x4E75)                    # [0x34] rts
    code += b"\x4e\x71" * 2                              # [$36..$39] nop
    code += struct.pack(">H", 0x4E75)                    # [0x3a] rts
    code += b"\x4e\x71"                                  # [$3c..$3d] nop
    code += struct.pack(">H", 0x4E75)                    # [0x3e] rts
    code += b"\x4e\x71"                                  # [$40..$41] nop

    init_mem = AbstractMemory()
    init_mem.write(sentinel_a6 + 100, _concrete(lib_base), "l")

    platform = {
        "initial_base_reg": (6, sentinel_a6),
        "_initial_mem": init_mem,
        "scratch_regs": [],
    }

    _, _, resolved = _analyze_and_resolve(code, platform=platform)
    targets = _resolved_targets(resolved)
    assert 0x3A in targets, f"Expected $003a, got {targets}"
    assert 0x3C in targets, f"Expected $003c, got {targets}"
    assert 0x34 in targets, f"Expected $0034, got {targets}"
    assert 0x36 in targets, f"Expected $0036, got {targets}"


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


# ---- 7. Data table enumeration ----------------------------------------------

def test_table_single_entry_resolves():
    """Dispatch through a value read from a code-section table (baseline).

    LEA table,A0; MOVE.W (A0),D0; LEA base,A1; ADDA.W D0,A1; JMP (A1)
    The executor reads the first table entry and resolves the target.
    This should already work through code-section memory reads + ADDA.
    """
    code = b''
    # lea $0c(pc),a0  -> a0 = $00+2+$0c = $0e (table)
    code += struct.pack('>HH', 0x41FA, 0x000C)          # [0x00] lea table(pc),a0
    # move.w (a0),d0  -> d0 = word at $0e = 0
    code += struct.pack('>H', 0x3010)                    # [0x04] move.w (a0),d0
    # lea $0c(pc),a1  -> a1 = $06+2+$0c = $14 (handler base)
    code += struct.pack('>HH', 0x43FA, 0x000C)          # [0x06] lea base(pc),a1
    # adda.w d0,a1  -> a1 = $14 + d0
    code += struct.pack('>H', 0xD2C0)                    # [0x0a] adda.w d0,a1
    # jmp (a1)
    code += struct.pack('>H', 0x4ED1)                    # [0x0c] jmp (a1)
    # Table at $0e: 3 word entries (offsets from base)
    code += struct.pack('>HHH', 0, 4, 8)                 # [0x0e] dc.w 0, 4, 8
    # Handler base at $14
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x14] nop; rts (handler 0)
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x18] nop; rts (handler 1)
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x1c] nop; rts (handler 2)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # At minimum, the first entry (target=$14) should resolve
    assert 0x14 in targets, (
        f"Expected $0014 (handler 0: base+0), got {targets}")
    print("  table_single_entry_resolves: OK")


def test_table_all_entries_enumerated():
    """All word-offset table entries should produce dispatch targets.

    Same layout as test_table_single_entry_resolves, but the test
    asserts that ALL three handler addresses are discovered, not just
    the one that the single execution path reads.

    This requires recognising that the dispatch value came from a
    table in the code section and scanning consecutive entries.
    """
    code = b''
    # lea $0c(pc),a0  -> a0 = $0e (table)
    code += struct.pack('>HH', 0x41FA, 0x000C)          # [0x00] lea table(pc),a0
    # move.w (a0),d0
    code += struct.pack('>H', 0x3010)                    # [0x04] move.w (a0),d0
    # lea $0c(pc),a1  -> a1 = $14 (handler base)
    code += struct.pack('>HH', 0x43FA, 0x000C)          # [0x06] lea base(pc),a1
    # adda.w d0,a1
    code += struct.pack('>H', 0xD2C0)                    # [0x0a] adda.w d0,a1
    # jmp (a1)
    code += struct.pack('>H', 0x4ED1)                    # [0x0c] jmp (a1)
    # Table at $0e: 3 word entries
    code += struct.pack('>HHH', 0, 4, 8)                 # [0x0e] dc.w 0, 4, 8
    # Handler base at $14
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x14] handler 0
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x18] handler 1
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x1c] handler 2

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x14 in targets, (
        f"Expected $0014 (handler 0), got {targets}")
    assert 0x18 in targets, (
        f"Expected $0018 (handler 1), got {targets}")
    assert 0x1c in targets, (
        f"Expected $001c (handler 2), got {targets}")
    print("  table_all_entries_enumerated: OK")


def test_table_enumeration_pea_rts():
    """Table enumeration through PEA+RTS dispatch (GenAm $7550 pattern).

    move.w (a0)+,d3; lea base(pc),a1; adda.w d3,a1; move.l a1,-(sp); rts

    The table is read via postincrement, but the scan should enumerate
    all word entries from the table start address.
    """
    code = b''
    # Caller sets a0 to table start
    # lea $18(pc),a0  -> a0 = $00+2+$18 = $1a (table)
    code += struct.pack('>HH', 0x41FA, 0x0018)          # [0x00] lea table(pc),a0
    # move.w (a0)+,d3  -> d3 = first entry, a0 advances
    code += struct.pack('>H', 0x3618)                    # [0x04] move.w (a0)+,d3
    # lea $18(pc),a1  -> a1 = $06+2+$18 = $20 (handler base)
    code += struct.pack('>HH', 0x43FA, 0x0018)          # [0x06] lea base(pc),a1
    # adda.w d3,a1  -> a1 = base + d3
    code += struct.pack('>H', 0xD2C3)                    # [0x0a] adda.w d3,a1
    # move.l a1,-(sp)  -> push handler
    code += struct.pack('>H', 0x2F09)                    # [0x0c] move.l a1,-(sp)
    # rts  -> dispatch
    code += struct.pack('>H', 0x4E75)                    # [0x0e] rts
    # Padding
    code += b'\x4e\x71' * 5                              # [0x10..$19] nop
    # Table at $1a: 3 word entries
    code += struct.pack('>HHH', 0, 6, 12)               # [0x1a] dc.w 0, 6, 12
    # Handler base at $20
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x20] handler 0 (base+0)
    code += struct.pack('>H', 0x4E71)                    # [0x24] nop
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x26] handler 1 (base+6)
    code += struct.pack('>H', 0x4E71)                    # [0x2a] nop
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x2c] handler 2 (base+12)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x20 in targets, (
        f"Expected $0020 (handler 0), got {targets}")
    assert 0x26 in targets, (
        f"Expected $0026 (handler 1), got {targets}")
    assert 0x2c in targets, (
        f"Expected $002c (handler 2), got {targets}")
    print("  table_enumeration_pea_rts: OK")


def test_table_enumeration_stops_at_invalid():
    """Table scan stops when an entry produces an invalid target.

    The table has 3 valid entries followed by a value that would
    produce an out-of-range or odd target. Only the valid entries
    should be resolved.
    """
    code = b''
    # lea $0c(pc),a0  -> a0 = $0e (table)
    code += struct.pack('>HH', 0x41FA, 0x000C)          # [0x00] lea table(pc),a0
    # move.w (a0),d0
    code += struct.pack('>H', 0x3010)                    # [0x04] move.w (a0),d0
    # lea $0c(pc),a1  -> a1 = $14 (handler base)
    code += struct.pack('>HH', 0x43FA, 0x000C)          # [0x06] lea base(pc),a1
    # adda.w d0,a1
    code += struct.pack('>H', 0xD2C0)                    # [0x0a] adda.w d0,a1
    # jmp (a1)
    code += struct.pack('>H', 0x4ED1)                    # [0x0c] jmp (a1)
    # Table at $0e: 2 valid + 1 invalid (odd target)
    code += struct.pack('>HHH', 0, 4, 3)                 # [0x0e] dc.w 0, 4, 3
    # Handler base at $14
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x14] handler 0
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x18] handler 1
    code += b'\x4e\x71' * 4                              # pad

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x14 in targets, (
        f"Expected $0014 (handler 0), got {targets}")
    assert 0x18 in targets, (
        f"Expected $0018 (handler 1), got {targets}")
    # $14 + 3 = $17 (odd) should NOT appear
    assert 0x17 not in targets, (
        f"Should not resolve odd target $0017, got {targets}")
    print("  table_enumeration_stops_at_invalid: OK")


def test_table_stride_multi_field():
    """Table with multi-word entries (stride > 2).

    Each entry has 3 words: [flags, handler_offset, extra].
    Only the handler_offset (second word) is used for dispatch.
    The scan must use the correct stride (6 bytes) and field offset (2).

    Models GenAm: move.w (a0)+,d6; move.w (a0)+,d3; move.w (a0)+,d2
    where d3 is the handler offset.
    """
    code = b''
    # Setup: a0 points to first table entry
    # lea $18(pc),a0  -> a0 = $1a (table)
    code += struct.pack('>HH', 0x41FA, 0x0018)          # [0x00] lea table(pc),a0
    # Read entry: move.w (a0)+,d6 (flags); move.w (a0)+,d3 (offset); move.w (a0)+,d2 (extra)
    code += struct.pack('>H', 0x3C18)                    # [0x04] move.w (a0)+,d6
    code += struct.pack('>H', 0x3618)                    # [0x06] move.w (a0)+,d3
    code += struct.pack('>H', 0x3418)                    # [0x08] move.w (a0)+,d2
    # Dispatch: lea base(pc),a1; adda.w d3,a1; jmp (a1)
    # lea $14(pc),a1  -> a1 = $0a+2+$14 = $20 (handler base)... wait
    # Let me recalculate. lea at $0a: a1 = $0a+2+disp. Need a1=$2c (base after table).
    # Table at $1a has 3 entries * 6 bytes = 18 bytes, ends at $1a+18=$2c.
    # disp = $2c - ($0a+2) = $2c - $0c = $20
    code += struct.pack('>HH', 0x43FA, 0x0020)          # [0x0a] lea base(pc),a1
    code += struct.pack('>H', 0xD2C3)                    # [0x0e] adda.w d3,a1
    code += struct.pack('>H', 0x4ED1)                    # [0x10] jmp (a1)
    # Padding to table
    code += b'\x4e\x71' * 4                              # [0x12..$19] nop
    # Table at $1a: 3 entries, each 6 bytes [flags, offset, extra]
    code += struct.pack('>HHH', 0xFFFF, 0, 0x1234)      # entry 0: offset=0
    code += struct.pack('>HHH', 0xFFFF, 8, 0x5678)      # entry 1: offset=8
    code += struct.pack('>HHH', 0xFFFF, 16, 0x9ABC)     # entry 2: offset=16
    # Handler base at $2c
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x2c] handler 0 (base+0)
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x30] pad
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x34] handler 1 (base+8)
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x38] pad
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x3c] handler 2 (base+16)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x2c in targets, (
        f"Expected $002c (handler 0: base+0), got {targets}")
    assert 0x34 in targets, (
        f"Expected $0034 (handler 1: base+8), got {targets}")
    assert 0x3c in targets, (
        f"Expected $003c (handler 2: base+16), got {targets}")
    print("  table_stride_multi_field: OK")


# ---- 8. Register survival across conditional calls -------------------------

def test_register_survives_conditional_call():
    """Register set before conditional BSR, used in dispatch after merge.

    Models GenAm $748a pattern:
        lea data(pc),a0        ; a0 = concrete address
        tst.b d(a6)            ; test condition
        beq.s skip             ; skip the call if zero
        bsr.w sub              ; clobbers a0 (scratch)
    skip:
        move.w 2(a0),d3        ; read field from a0
        lea base(pc),a1
        adda.w d3,a1
        jmp (a1)               ; dispatch

    A0 survives on the beq path (call skipped) but is clobbered on
    the call path. After merge, A0 is unknown. Per-caller analysis
    of the dispatch block should recover A0 from the skip-path
    predecessor.
    """
    code = b''
    # lea $24(pc),a0  -> a0 = $00+2+$24 = $26 (data record)
    code += struct.pack('>HH', 0x41FA, 0x0024)          # [0x00] lea data(pc),a0
    # tst.b d0 (just to set CC for branch)
    code += struct.pack('>H', 0x4A00)                    # [0x04] tst.b d0
    # beq.s $0C  (skip BSR) disp = $0C - ($06+2) = 4
    code += struct.pack('>H', 0x6704)                    # [0x06] beq.s $0C
    # bsr.w $1E  (sub that clobbers a0) disp = $1E - ($08+2) = $14
    code += struct.pack('>HH', 0x6100, 0x0014)          # [0x08] bsr.w $1E
    # skip: (merge point $0C)
    # move.w 2(a0),d3  -> d3 = word at a0+2
    code += struct.pack('>HH', 0x3628, 0x0002)          # [0x0c] move.w 2(a0),d3
    # lea $1c(pc),a1  -> a1 = $10+2+$1c = $2e (handler base)
    code += struct.pack('>HH', 0x43FA, 0x001C)          # [0x10] lea base(pc),a1
    # adda.w d3,a1
    code += struct.pack('>H', 0xD2C3)                    # [0x14] adda.w d3,a1
    # jmp (a1)
    code += struct.pack('>H', 0x4ED1)                    # [0x16] jmp (a1)
    # Padding
    code += b'\x4e\x71' * 3                              # [0x18..$1d] nop
    # Sub at $1E that clobbers a0
    code += struct.pack('>HH', 0x41FA, 0x0000)          # [0x1e] lea 0(pc),a0 (clobber)
    code += struct.pack('>H', 0x4E75)                    # [0x22] rts
    # Padding
    code += struct.pack('>H', 0x4E71)                    # [0x24] nop
    # Data record at $26: [word0=don't_care, word1=handler_offset, word2=don't_care]
    # handler_offset = 4 -> target = $2e + 4 = $32
    code += struct.pack('>HHH', 0x0000, 0x0004, 0x0000) # [0x26] data record
    # Padding to handler base
    code += struct.pack('>H', 0x4E71)                    # [0x2c] nop
    # Handler base at $2e
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x2e] nop; rts
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x32] handler (target)
    code += struct.pack('>H', 0x4E71)                    # [0x36] pad

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # On the skip path (beq taken): a0=$26, d3=word at $28=4, target=$2e+4=$32
    assert 0x32 in targets, (
        f"Expected $0032 (handler via surviving a0), got {targets}")
    print("  register_survives_conditional_call: OK")


def test_register_clobbered_both_paths():
    """When a register is clobbered on ALL paths, dispatch should NOT resolve.

    Both paths of a conditional branch overwrite A0 with different values.
    After the merge, A0 is unknown, and the dispatch cannot resolve.
    """
    code = b''
    # tst.b d0
    code += struct.pack('>H', 0x4A00)                    # [0x00] tst.b d0
    # beq.s $08
    code += struct.pack('>H', 0x6704)                    # [0x02] beq.s $08
    # Path A: lea $20(pc),a0  -> a0 = $04+2+$20 = $26
    code += struct.pack('>HH', 0x41FA, 0x0020)          # [0x04] lea $20(pc),a0
    # Path B: lea $24(pc),a0  -> a0 = $08+2+$24 = $2e (DIFFERENT value)
    code += struct.pack('>HH', 0x41FA, 0x0024)          # [0x08] lea $24(pc),a0
    # Merge at $0C: a0 is unknown ($26 vs $2e)
    # move.w 2(a0),d3  -> a0 unknown, d3 unknown
    code += struct.pack('>HH', 0x3628, 0x0002)          # [0x0c] move.w 2(a0),d3
    # lea $14(pc),a1  -> a1 = $10+2+$14 = $26
    code += struct.pack('>HH', 0x43FA, 0x0014)          # [0x10] lea base(pc),a1
    # adda.w d3,a1
    code += struct.pack('>H', 0xD2C3)                    # [0x14] adda.w d3,a1
    # jmp (a1)
    code += struct.pack('>H', 0x4ED1)                    # [0x16] jmp (a1)
    # Padding + data
    code += b'\x4e\x71' * 12                             # pad to $2e+

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert len(targets) == 0, (
        f"Should not resolve when a0 differs on all paths, got {targets}")
    print("  register_clobbered_both_paths: OK")


# ---- 9. Backward slice across merges ----------------------------------------

def test_backward_slice_one_level():
    """Register value recovered one merge back from dispatch.

    Block A: LEA data(pc),A0; beq.s C
    Block B: MOVEA.L D7,A0  (clobber, fallthrough to C)
    Block C: (merge) NOP; BEQ.S D  (creates block boundary)
    Block D: (dispatch) MOVE.W 2(A0),D0; LEA base; ADDA; JMP (A1)

    A0 is concrete on path A->C, unknown on B->C.
    Merge at C kills A0. Backward slice from D through C finds A's
    concrete A0 and resolves the dispatch.
    """
    code = b''
    # Block A at $00: set A0, conditional branch to C
    # lea $20(pc),a0  -> a0 = $00+2+$20 = $22 (data record)
    code += struct.pack('>HH', 0x41FA, 0x0020)          # [0x00] lea data(pc),a0
    code += struct.pack('>H', 0x4A00)                    # [0x04] tst.b d0
    code += struct.pack('>H', 0x6702)                    # [0x06] beq.s $0A (skip B)
    # Block B at $08: clobber A0 (fallthrough to C)
    code += struct.pack('>H', 0x2047)                    # [0x08] movea.l d7,a0
    # Block C at $0A: merge (preds: A via beq, B via fallthrough)
    code += struct.pack('>H', 0x4A01)                    # [0x0a] tst.b d1
    code += struct.pack('>H', 0x6702)                    # [0x0c] beq.s $10 (dispatch)
    # Block (fallthrough from C)
    code += struct.pack('>H', 0x4E71)                    # [0x0e] nop
    # Block D at $10: dispatch
    code += struct.pack('>HH', 0x3028, 0x0002)          # [0x10] move.w 2(a0),d0
    # lea $14(pc),a1  -> a1 = $14+2+$14 = $2a (handler base)
    code += struct.pack('>HH', 0x43FA, 0x0014)          # [0x14] lea base(pc),a1
    code += struct.pack('>H', 0xD2C0)                    # [0x18] adda.w d0,a1
    code += struct.pack('>H', 0x4ED1)                    # [0x1a] jmp (a1)
    # Padding
    code += b'\x4e\x71' * 3                              # [0x1c..$21] nop
    # Data record at $22: [word0=0, word1=handler_offset=4, word2=0]
    code += struct.pack('>HHH', 0x0000, 0x0004, 0x0000) # [0x22] data
    # Padding
    code += struct.pack('>H', 0x4E71)                    # [0x28] nop
    # Handler base at $2a
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x2a] handler 0
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x2e] handler 1 (target)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # a0=$22, offset at $24 = 4, base=$2a, target = $2a+4 = $2e
    assert 0x2e in targets, (
        f"Expected $002e (handler via backward slice through merge), "
        f"got {targets}")
    print("  backward_slice_one_level: OK")


def test_backward_slice_two_levels():
    """Register value recovered two merges back from dispatch.

    Block A: LEA data,A0; beq.s C
    Block B: MOVEA.L D7,A0  (clobber, fallthrough to C)
    Block C: (merge1) tst; beq.s E
    Block D: MOVEA.L D6,A0  (clobber, fallthrough to E)
    Block E: (merge2) tst; beq.s G
    Block F: (fallthrough from E)
    Block G: (dispatch) uses A0

    A0 survives only on path A->C->E->G. The backward slice must
    traverse two merge points to find A's concrete value.
    """
    code = b''
    # Block A: set A0
    # lea $28(pc),a0 -> a0 = $00+2+$28 = $2a (data)
    code += struct.pack('>HH', 0x41FA, 0x0028)          # [0x00] lea data(pc),a0
    code += struct.pack('>H', 0x4A00)                    # [0x04] tst.b d0
    code += struct.pack('>H', 0x6702)                    # [0x06] beq.s $0A (skip B)
    # Block B: clobber1 (fallthrough to C)
    code += struct.pack('>H', 0x2047)                    # [0x08] movea.l d7,a0
    # Block C: merge1
    code += struct.pack('>H', 0x4A01)                    # [0x0a] tst.b d1
    code += struct.pack('>H', 0x6702)                    # [0x0c] beq.s $10 (skip D)
    # Block D: clobber2 (fallthrough to E)
    code += struct.pack('>H', 0x2046)                    # [0x0e] movea.l d6,a0
    # Block E: merge2
    code += struct.pack('>H', 0x4A02)                    # [0x10] tst.b d2
    code += struct.pack('>H', 0x6702)                    # [0x12] beq.s $16 (dispatch)
    # Block F: fallthrough
    code += struct.pack('>H', 0x4E71)                    # [0x14] nop
    # Block G at $16: dispatch
    code += struct.pack('>HH', 0x3028, 0x0002)          # [0x16] move.w 2(a0),d0
    # lea $14(pc),a1 -> a1 = $1a+2+$14 = $30 (handler base)
    code += struct.pack('>HH', 0x43FA, 0x0014)          # [0x1a] lea base(pc),a1
    code += struct.pack('>H', 0xD2C0)                    # [0x1e] adda.w d0,a1
    code += struct.pack('>H', 0x4ED1)                    # [0x20] jmp (a1)
    # Padding
    code += b'\x4e\x71' * 4                              # [0x22..$29] nop
    # Data at $2a: [0, offset=6, 0]
    code += struct.pack('>HHH', 0x0000, 0x0006, 0x0000) # [0x2a] data
    # Handler base at $30
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x30] handler 0
    code += struct.pack('>H', 0x4E71)                    # [0x34] pad
    # Target at $30 + 6 = $36
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x36] handler 1 (target)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x36 in targets, (
        f"Expected $0036 (handler via 2-level backward slice), "
        f"got {targets}")
    print("  backward_slice_two_levels: OK")


def test_backward_slice_many_predecessors():
    """Merge point with many predecessors, only one has concrete value.

    Entry splits into 4 paths via cascading conditionals. Only path 1
    sets A0 concretely; paths 2-4 leave it unknown. All merge at the
    dispatch block.
    """
    code = b''
    # Path 1: lea data(pc),a0
    # lea $2c(pc),a0  -> a0 = $00+2+$2c = $2e (data)
    code += struct.pack('>HH', 0x41FA, 0x002C)          # [0x00] lea data(pc),a0
    code += struct.pack('>H', 0x4A00)                    # [0x04] tst.b d0
    # beq.s $0C  -> merge
    code += struct.pack('>H', 0x6716)                    # [0x06] beq.s $1E (merge)
    # Path 2: leave a0 alone (unknown from entry)
    code += struct.pack('>H', 0x4A01)                    # [0x08] tst.b d1
    # beq.s merge
    code += struct.pack('>H', 0x6712)                    # [0x0a] beq.s $1E
    # Path 3: clobber a0
    code += struct.pack('>H', 0x2047)                    # [0x0c] movea.l d7,a0
    code += struct.pack('>H', 0x4A02)                    # [0x0e] tst.b d2
    # beq.s merge
    code += struct.pack('>H', 0x670C)                    # [0x10] beq.s $1E
    # Path 4: different clobber
    code += struct.pack('>H', 0x2046)                    # [0x12] movea.l d6,a0
    # bra.s merge
    code += struct.pack('>H', 0x600A)                    # [0x14] bra.s $20
    # Padding
    code += b'\x4e\x71' * 4                              # [0x16..$1d] nop

    # Merge/dispatch at $1E
    # Actually wait, the beq targets need to be right. Let me recalculate.
    # beq.s $1E at $06: disp = $1E - ($06+2) = $16. That's > 127... too far.
    # Let me make it tighter.

    code = b''
    # Path 1: set a0
    # lea $20(pc),a0 -> a0 = $00+2+$20 = $22 (data)
    code += struct.pack('>HH', 0x41FA, 0x0020)          # [0x00] lea data(pc),a0
    code += struct.pack('>H', 0x4A00)                    # [0x04] tst.b d0
    code += struct.pack('>H', 0x670C)                    # [0x06] beq.s $14 (merge)
    # Path 2: clobber a0
    code += struct.pack('>H', 0x2047)                    # [0x08] movea.l d7,a0
    code += struct.pack('>H', 0x4A01)                    # [0x0a] tst.b d1
    code += struct.pack('>H', 0x6706)                    # [0x0c] beq.s $14 (merge)
    # Path 3: another clobber
    code += struct.pack('>H', 0x2046)                    # [0x0e] movea.l d6,a0
    code += struct.pack('>H', 0x6002)                    # [0x10] bra.s $14 (merge)
    code += struct.pack('>H', 0x4E71)                    # [0x12] nop
    # Merge + dispatch at $14
    code += struct.pack('>HH', 0x3028, 0x0002)          # [0x14] move.w 2(a0),d0
    # lea $14(pc),a1 -> a1 = $18+2+$14 = $2e (handler base)
    code += struct.pack('>HH', 0x43FA, 0x0014)          # [0x18] lea base(pc),a1
    code += struct.pack('>H', 0xD2C0)                    # [0x1c] adda.w d0,a1
    code += struct.pack('>H', 0x4ED1)                    # [0x1e] jmp (a1)
    # Padding
    code += struct.pack('>H', 0x4E71)                    # [0x20] nop
    # Data at $22
    code += struct.pack('>HHH', 0x0000, 0x0004, 0x0000) # [0x22] data
    # Padding
    code += b'\x4e\x71' * 3                              # [0x28..$2d] nop
    # Handler base at $2e
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x2e] handler 0
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x32] handler 1 (target)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # Only path 1 (beq at $06 taken) has A0=$22. offset=4 -> target=$2e+4=$32
    assert 0x32 in targets, (
        f"Expected $0032 (handler via backward slice, 1 of 3 paths), "
        f"got {targets}")
    print("  backward_slice_many_predecessors: OK")


def test_backward_slice_all_paths_clobbered():
    """Backward slice should NOT resolve when no path has the value.

    All predecessors clobber A0 to different unknown values.
    No backward path can recover a concrete A0.
    """
    code = b''
    code += struct.pack('>H', 0x4A00)                    # [0x00] tst.b d0
    code += struct.pack('>H', 0x6704)                    # [0x02] beq.s $08
    # Path A: clobber a0
    code += struct.pack('>H', 0x2047)                    # [0x04] movea.l d7,a0
    code += struct.pack('>H', 0x6002)                    # [0x06] bra.s $0A
    # Path B: different clobber
    code += struct.pack('>H', 0x2046)                    # [0x08] movea.l d6,a0
    # Merge + dispatch at $0A
    code += struct.pack('>HH', 0x3028, 0x0002)          # [0x0a] move.w 2(a0),d0
    code += struct.pack('>HH', 0x43FA, 0x0010)          # [0x0e] lea $10(pc),a1
    code += struct.pack('>H', 0xD2C0)                    # [0x12] adda.w d0,a1
    code += struct.pack('>H', 0x4ED1)                    # [0x14] jmp (a1)
    code += b'\x4e\x71' * 10                             # padding

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert len(targets) == 0, (
        f"Should not resolve when A0 clobbered on all paths, "
        f"got {targets}")
    print("  backward_slice_all_paths_clobbered: OK")


def test_backward_slice_through_non_sub_blocks():
    """Backward slice works for blocks that aren't subroutine entries.

    The dispatch block is reached through normal branches (not BSR),
    so per-caller analysis doesn't apply. Only backward slicing can
    recover the register value.

    Models GenAm $7542: LEA pcref,A0 several blocks before the dispatch,
    with intervening conditionals and merges.
    """
    code = b''
    # Entry: set A0 and branch into processing
    # lea $30(pc),a0 -> a0 = $00+2+$30 = $32 (data)
    code += struct.pack('>HH', 0x41FA, 0x0030)          # [0x00] lea data(pc),a0
    code += struct.pack('>H', 0x4A00)                    # [0x04] tst.b d0
    code += struct.pack('>H', 0x6704)                    # [0x06] beq.s $0C
    # Processing path that doesn't touch A0
    code += struct.pack('>H', 0x7205)                    # [0x08] moveq #5,d1
    code += struct.pack('>H', 0x6006)                    # [0x0a] bra.s $12
    # Skip path
    code += struct.pack('>H', 0x7200)                    # [0x0c] moveq #0,d1
    code += struct.pack('>H', 0x4A01)                    # [0x0e] tst.b d1
    code += struct.pack('>H', 0x6702)                    # [0x10] beq.s $14
    # Merge at $12, second merge at $14
    code += struct.pack('>H', 0x5241)                    # [0x12] addq.w #1,d1
    # Final merge + dispatch at $14
    code += struct.pack('>HH', 0x3028, 0x0002)          # [0x14] move.w 2(a0),d0
    # lea $1c(pc),a1 -> a1 = $18+2+$1c = $36 (handler base)
    code += struct.pack('>HH', 0x43FA, 0x001C)          # [0x18] lea base(pc),a1
    code += struct.pack('>H', 0xD2C0)                    # [0x1c] adda.w d0,a1
    code += struct.pack('>H', 0x4ED1)                    # [0x1e] jmp (a1)
    # Padding
    code += b'\x4e\x71' * 9                              # [0x20..$31] nop
    # Data at $32
    code += struct.pack('>HHH', 0x0000, 0x0008, 0x0000) # [0x32] data
    # Handler base at $36
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x38] pad
    code += b'\x4e\x71' * 2                              # [0x3c..] pad
    # Target at $36 + 8 = $3e
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x3e] handler (target)

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert 0x3e in targets, (
        f"Expected $003e (handler via backward slice through non-sub blocks), "
        f"got {targets}")
    print("  backward_slice_through_non_sub_blocks: OK")


# ---- 10. Edge cases ---------------------------------------------------------

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
    # jsr 0(a1,d0.w)  -- d0 unknown, target unresolvable
    code += struct.pack('>HH', 0x4EB1, 0x0000)          # [0x04] jsr 0(a1,d0.w)
    # No RTS -- only the JSR is under test
    code += b'\x4e\x71' * 26

    _, _, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    assert len(targets) == 0, (
        f"Should not resolve with unknown d0, got {targets}")
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


# ---- 11. Jump table pattern detection (Patterns A-D) -----------------------

def test_pattern_a_word_offset():
    """Pattern A: LEA base(PC),An; JMP disp(An,Dn.w) with word-offset table.

    The table contains signed word offsets from base. Each target =
    base + entry_value.
    """
    code = b''
    # lea table(pc),a0  -> a0 = $00+2+$08 = $0a (table start)
    code += struct.pack('>HH', 0x41FA, 0x0008)          # [0x00] lea $08(pc),a0
    # moveq #0,d0  (index = 0, just to have something in d0)
    code += struct.pack('>H', 0x7000)                    # [0x04] moveq #0,d0
    # jmp 0(a0,d0.w)
    # JMP index(A0): 0100 1110 11 110 000 = $4EF0
    # ext word: D/A=0, REG=000(d0), W/L=0, disp=0 -> $0000
    code += struct.pack('>HH', 0x4EF0, 0x0000)          # [0x06] jmp 0(a0,d0.w)
    # Table at $0a: word offsets from base ($0a)
    # Targets: $0a+0=$0a, $0a+4=$0e, $0a+10=$14
    code += struct.pack('>hhh', 0, 4, 10)                # [0x0a] dc.w 0, 4, 10
    # Handlers
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x10] nop; rts
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x14] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x0a in t["targets"], f"Expected $000a in targets, got {t['targets']}"
    assert 0x0e in t["targets"], f"Expected $000e in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    print("  pattern_a_word_offset: OK")


def test_pattern_b_self_relative():
    """Pattern B: LEA d(PC,Dn),An; ADDA.W (An),An; JMP (An).

    Table entries are self-relative: target = &entry + entry_value.
    """
    code = b''
    # moveq #0,d0
    code += struct.pack('>H', 0x7000)                    # [0x00] moveq #0,d0
    # lea $06(pc,d0.w),a0  -> a0 = $02+2+$06+d0 = $0a (table[d0])
    # LEA pcindex(A0): 0100 0001 11 111 011 = $41FB
    # ext word: D/A=0, REG=000(d0), W/L=0, disp=$06 -> $0006
    code += struct.pack('>HH', 0x41FB, 0x0006)          # [0x02] lea $06(pc,d0.w),a0
    # adda.w (a0),a0
    # ADDA.W (A0),A0: 1101 000 011 010 000 = $D0D0
    code += struct.pack('>H', 0xD0D0)                    # [0x06] adda.w (a0),a0
    # jmp (a0)
    code += struct.pack('>H', 0x4ED0)                    # [0x08] jmp (a0)
    # Table at $0a: self-relative word entries
    # Entry 0 at $0a: target = $0a + 8 = $12
    # Entry 1 at $0c: target = $0c + 10 = $16
    # Entry 2 at $0e: target = $0e + 8 = $16 (same target, that's ok)
    code += struct.pack('>hhh', 8, 10, 8)                # [0x0a] dc.w 8, 10, 8
    # Padding
    code += struct.pack('>H', 0x4E71)                    # [0x10] nop
    # Handlers
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x12] handler 0
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x16] handler 1

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "self_relative_word", (
        f"Expected pattern 'self_relative_word', got {t['pattern']!r}")
    assert 0x12 in t["targets"], f"Expected $0012 in targets, got {t['targets']}"
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    print("  pattern_b_self_relative: OK")


def test_pattern_c_pc_inline_dispatch():
    """Pattern C: JMP disp(PC,Dn.w) with inline BRA.S entries.

    The dispatch table is a series of BRA.S instructions immediately
    after the JMP. Each BRA.S branches to its handler.
    """
    code = b''
    # moveq #0,d0
    code += struct.pack('>H', 0x7000)                    # [0x00] moveq #0,d0
    # jmp 0(pc,d0.w)
    # JMP pcindex: 0100 1110 11 111 011 = $4EFB
    # ext word: D/A=0, REG=000(d0), W/L=0, disp=$00 -> $0000
    code += struct.pack('>HH', 0x4EFB, 0x0000)          # [0x02] jmp 0(pc,d0.w)
    # Inline BRA.S entries starting at $06
    # BRA.S $0e: disp = $0e - ($06+2) = 6 -> $6006
    code += struct.pack('>H', 0x6006)                    # [0x06] bra.s $0e
    # BRA.S $12: disp = $12 - ($08+2) = 8 -> $6008
    code += struct.pack('>H', 0x6008)                    # [0x08] bra.s $12
    # BRA.S $16: disp = $16 - ($0a+2) = 10 -> $600a
    code += struct.pack('>H', 0x600A)                    # [0x0a] bra.s $16
    # Non-BRA terminates scan
    code += struct.pack('>H', 0x4E71)                    # [0x0c] nop
    # Handlers
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x0e] handler 0
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x12] handler 1
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x16] handler 2

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "pc_inline_dispatch", (
        f"Expected pattern 'pc_inline_dispatch', got {t['pattern']!r}")
    assert 0x0e in t["targets"], f"Expected $000e in targets, got {t['targets']}"
    assert 0x12 in t["targets"], f"Expected $0012 in targets, got {t['targets']}"
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    print("  pattern_c_pc_inline_dispatch: OK")


def test_pattern_d_indirect_table_read():
    """Pattern D: LEA d(PC),An; MOVE.W d1(An,Dn),Dn; JSR d2(An,Dn).

    The MOVE reads an offset from a table (at lea+d1), then the JSR
    dispatches using the loaded offset (at lea+d2+entry_value).
    """
    code = b''
    # moveq #0,d0  (table index)
    code += struct.pack('>H', 0x7000)                    # [0x00] moveq #0,d0
    # lea $08(pc),a0 -> a0 = $02+2+$08 = $0c (base)
    code += struct.pack('>HH', 0x41FA, 0x0008)          # [0x02] lea $08(pc),a0
    # move.w 0(a0,d0.w),d0  -- reads table at base+0
    # MOVE.W index(A0) to D0:
    # 0011 000 000 110 000 = $3030
    # ext word: D/A=0, REG=000(d0), W/L=0, disp=0 -> $0000
    code += struct.pack('>HH', 0x3030, 0x0000)          # [0x06] move.w 0(a0,d0.w),d0
    # jsr 6(a0,d0.w)  -- dispatches using loaded d0
    # JSR index(A0): 0100 1110 10 110 000 = $4EB0
    # ext word: D/A=0, REG=000(d0), W/L=0, disp=6 -> $0006
    code += struct.pack('>HH', 0x4EB0, 0x0006)          # [0x0a] jsr 6(a0,d0.w)
    # rts after call returns
    code += struct.pack('>H', 0x4E75)                    # [0x0e] rts
    # Padding (base=$0c, but table is at base+0=$0c for MOVE, dispatch at base+6=$12)
    # Wait: base = $0c, table at base+0 = $0c, dispatch_base = base+6 = $12
    # Hmm, table entries are at $0c but our code is there too...
    # Let me adjust: put the LEA displacement higher.

    code = b''
    # moveq #0,d0
    code += struct.pack('>H', 0x7000)                    # [0x00] moveq #0,d0
    # lea $0c(pc),a0 -> a0 = $02+2+$0c = $10 (base)
    code += struct.pack('>HH', 0x41FA, 0x000C)          # [0x02] lea $0c(pc),a0
    # move.w 0(a0,d0.w),d0  -- table at base+0 = $10
    code += struct.pack('>HH', 0x3030, 0x0000)          # [0x06] move.w 0(a0,d0.w),d0
    # jsr 6(a0,d0.w)  -- dispatch_base = base+6 = $16
    code += struct.pack('>HH', 0x4EB0, 0x0006)          # [0x0a] jsr 6(a0,d0.w)
    # rts
    code += struct.pack('>H', 0x4E75)                    # [0x0e] rts
    # Table at $10: word offsets from dispatch_base ($16)
    # Entry 0: target = $16 + 0 = $16
    # Entry 1: target = $16 + 4 = $1a
    code += struct.pack('>hh', 0, 4)                     # [0x10] dc.w 0, 4
    # Padding
    code += struct.pack('>H', 0x4E71)                    # [0x14] nop
    # Handlers at dispatch_base $16
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x16] handler 0
    code += struct.pack('>HH', 0x4E71, 0x4E75)          # [0x1a] handler 1
    code += struct.pack('>H', 0x4E71)                    # [0x1e] pad

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_table_read", (
        f"Expected pattern 'indirect_table_read', got {t['pattern']!r}")
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    assert 0x1a in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_d_indirect_table_read: OK")


def test_pattern_string_dispatch_self_relative_via_decoder_subroutine():
    specs = [
        ("asm", "moveq #1,d1"),
        ("asm", "bsr.w {sub}"),
        ("asm", "beq.s {skip}"),
        ("asm", "jsr (a0)"),
        ("label", "skip"),
        ("asm", "rts"),
        ("label", "sub"),
        ("asm", "lea {table_disp}(pc),a0"),
        ("asm", "move.b (a0)+,d2"),
        ("label", "loop"),
        ("asm", "beq.s {no_match}"),
        ("asm", "cmp.b (a0),d1"),
        ("asm", "bne.s {skip_entry}"),
        ("asm", "lea 1(a0),a1"),
        ("asm", "move.b (a1)+,d0"),
        ("asm", "lsl.w #8,d0"),
        ("asm", "move.b (a1)+,d0"),
        ("asm", "lea -2(a1,d0.w),a0"),
        ("asm", "lea {end_disp}(pc),a2"),
        ("asm", "cmpa.l a2,a0"),
        ("asm", "rts"),
        ("label", "skip_entry"),
        ("asm", "lea 2(a0,d2.w),a0"),
        ("asm", "bra.s {loop}"),
        ("label", "no_match"),
        ("asm", "moveq #0,d0"),
        ("asm", "rts"),
        ("label", "table"),
        ("bytes", b"\x00" * 9),
        ("label", "table_end"),
        ("bytes", b"\x00"),
        ("label", "handler1"),
        ("asm", "nop"),
        ("asm", "rts"),
        ("label", "handler2"),
        ("asm", "nop"),
        ("asm", "rts"),
    ]
    code, labels = _assemble_with_labels(specs)
    code = bytearray(code)

    entry1_offset_pos = labels["table"] + 2
    entry2_offset_pos = labels["table"] + 6
    code[labels["table"]:labels["table"] + 4] = bytes((
        1,
        1,
        ((labels["handler1"] - entry1_offset_pos) >> 8) & 0xFF,
        (labels["handler1"] - entry1_offset_pos) & 0xFF,
    ))
    code[labels["table"] + 4:labels["table"] + 8] = bytes((
        1,
        2,
        ((labels["handler2"] - entry2_offset_pos) >> 8) & 0xFF,
        (labels["handler2"] - entry2_offset_pos) & 0xFF,
    ))
    code[labels["table"] + 8] = 0

    result = analyze(bytes(code), propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, bytes(code))
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "string_dispatch_self_relative", (
        f"Expected pattern 'string_dispatch_self_relative', got {t['pattern']!r}")
    assert t["addr"] == labels["table"], (
        f"Expected table addr ${labels['table']:04x}, got ${t['addr']:04x}")
    assert t["table_end"] == labels["table_end"], (
        f"Expected table end ${labels['table_end']:04x}, got ${t['table_end']:04x}")
    assert [entry["offset_addr"] for entry in t["entries"]] == [
        labels["table"] + 2,
        labels["table"] + 6,
    ], f"Unexpected entry offsets: {t['entries']}"
    assert labels["handler1"] in t["targets"], (
        f"Expected ${labels['handler1']:04x} in targets, got {t['targets']}")
    assert labels["handler2"] in t["targets"], (
        f"Expected ${labels['handler2']:04x} in targets, got {t['targets']}")
    print("  pattern_string_dispatch_self_relative_via_decoder_subroutine: OK")


def test_pattern_string_dispatch_uses_scanned_table_end_not_target_bound():
    specs = [
        ("asm", "moveq #1,d1"),
        ("asm", "bsr.w {sub}"),
        ("asm", "beq.s {skip}"),
        ("asm", "jsr (a0)"),
        ("label", "skip"),
        ("asm", "rts"),
        ("label", "sub"),
        ("asm", "lea {table_disp}(pc),a0"),
        ("asm", "move.b (a0)+,d2"),
        ("label", "loop"),
        ("asm", "beq.s {no_match}"),
        ("asm", "cmp.b (a0),d1"),
        ("asm", "bne.s {skip_entry}"),
        ("asm", "lea 1(a0),a1"),
        ("asm", "move.b (a1)+,d0"),
        ("asm", "lsl.w #8,d0"),
        ("asm", "move.b (a1)+,d0"),
        ("asm", "lea -2(a1,d0.w),a0"),
        ("asm", "lea {bound_disp}(pc),a2"),
        ("asm", "cmpa.l a2,a0"),
        ("asm", "rts"),
        ("label", "skip_entry"),
        ("asm", "lea 2(a0,d2.w),a0"),
        ("asm", "bra.s {loop}"),
        ("label", "no_match"),
        ("asm", "moveq #0,d0"),
        ("asm", "rts"),
        ("label", "table"),
        ("bytes", b"\x00" * 9),
        ("label", "after_table"),
        ("asm", "nop"),
        ("asm", "rts"),
        ("label", "bound"),
        ("bytes", b"\x00"),
        ("label", "handler1"),
        ("asm", "nop"),
        ("asm", "rts"),
        ("label", "handler2"),
        ("asm", "nop"),
        ("asm", "rts"),
    ]
    code, labels = _assemble_with_labels(specs)
    code = bytearray(code)

    entry1_offset_pos = labels["table"] + 2
    entry2_offset_pos = labels["table"] + 6
    code[labels["table"]:labels["table"] + 4] = bytes((
        1,
        1,
        ((labels["handler1"] - entry1_offset_pos) >> 8) & 0xFF,
        (labels["handler1"] - entry1_offset_pos) & 0xFF,
    ))
    code[labels["table"] + 4:labels["table"] + 8] = bytes((
        1,
        2,
        ((labels["handler2"] - entry2_offset_pos) >> 8) & 0xFF,
        (labels["handler2"] - entry2_offset_pos) & 0xFF,
    ))
    code[labels["table"] + 8] = 0

    result = analyze(bytes(code), propagate=True, platform=dict(_MINIMAL_PLATFORM))
    tables = detect_jump_tables(result["blocks"], bytes(code))
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["table_end"] == labels["after_table"], (
        f"Expected scanned table end ${labels['after_table']:04x}, got ${t['table_end']:04x}")


def test_pattern_pc_sparse_word_offset_dispatch():
    specs = [
        ("asm", "moveq #1,d1"),
        ("asm", "cmpi.b #4,d1"),
        ("asm", "bcc.s {fail}"),
        ("asm", "add.w d1,d1"),
        ("asm", "move.w {table_disp}(pc,d1.w),d0"),
        ("asm", "beq.s {fail}"),
        ("asm", "jsr {table_disp}(pc,d0.w)"),
        ("asm", "rts"),
        ("label", "fail"),
        ("asm", "rts"),
        ("label", "table"),
        ("bytes", b"\x00" * 8),
        ("label", "handler1"),
        ("asm", "nop"),
        ("asm", "rts"),
        ("label", "handler2"),
        ("asm", "nop"),
        ("asm", "rts"),
    ]
    code, labels = _assemble_with_labels(specs)
    code = bytearray(code)

    table = labels["table"]
    handler1_off = labels["handler1"] - table
    handler2_off = labels["handler2"] - table
    code[table:table + 8] = struct.pack(">hhhh", 0, handler1_off, 0, handler2_off)

    result = analyze(bytes(code), propagate=True, platform=dict(_MINIMAL_PLATFORM))
    tables = detect_jump_tables(result["blocks"], bytes(code))
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "pc_sparse_word_offset", (
        f"Expected pattern 'pc_sparse_word_offset', got {t['pattern']!r}")
    assert t["addr"] == table, (
        f"Expected table addr ${table:04x}, got ${t['addr']:04x}")
    assert t["table_end"] == table + 8, (
        f"Expected table end ${table + 8:04x}, got ${t['table_end']:04x}")
    assert [entry["offset_addr"] for entry in t["entries"]] == [table + 2, table + 6]
    assert labels["handler1"] in t["targets"], (
        f"Expected ${labels['handler1']:04x} in targets, got {t['targets']}")
    assert labels["handler2"] in t["targets"], (
        f"Expected ${labels['handler2']:04x} in targets, got {t['targets']}")


def test_pattern_e_full_extension_memory_indirect_pointer_table():
    """Pattern E: LEA d(PC),An; JSR ([bd,An,Dn.w],od) through long pointers."""
    code = b""
    code += struct.pack(">H", 0x7400)                    # [0x00] moveq #0,d2
    code += struct.pack(">HH", 0x43FA, 0x0010)          # [0x02] lea $10(pc),a1 -> $14
    code += bytes.fromhex("4eb1212200000004")           # [0x06] jsr ([0,a1,d2.w],4)
    code += struct.pack(">H", 0x4E75)                    # [0x0e] rts
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x10] nop; nop
    code += struct.pack(">I", 0x0000001C)                # [0x14] dc.l $1c
    code += struct.pack(">I", 0x00000020)                # [0x18] dc.l $20
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x1c] nop; nop
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "memory_indirect_long_pointer", (
        f"Expected pattern 'memory_indirect_long_pointer', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    print("  pattern_e_full_extension_memory_indirect_pointer_table: OK")


def test_pattern_f_pc_full_extension_memory_indirect_pointer_table():
    """Pattern F: JSR ([d,PC,Dn.w],od) through long pointers."""
    code = b""
    code += struct.pack(">H", 0x7400)                    # [0x00] moveq #0,d2
    code += bytes.fromhex("4ebb2122000c0004")           # [0x02] jsr ([12,pc,d2.w],4)
    code += struct.pack(">H", 0x4E75)                    # [0x0a] rts
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x0c] nop; nop
    code += struct.pack(">I", 0x00000018)                # [0x10] dc.l $18
    code += struct.pack(">I", 0x0000001C)                # [0x14] dc.l $1c
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "pc_memory_indirect_long_pointer", (
        f"Expected pattern 'pc_memory_indirect_long_pointer', got {t['pattern']!r}")
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    print("  pattern_f_pc_full_extension_memory_indirect_pointer_table: OK")


def test_pattern_g_full_extension_memory_indirect_pointer_table_via_reg_copy():
    """Pattern G: LEA table,Ax; MOVEA.L Ax,Ay; JSR ([0,Ay,Dn.w],4)."""
    code = b""
    code += struct.pack(">H", 0x7400)                    # [0x00] moveq #0,d2
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x02] lea $10(pc),a0 -> $14
    code += struct.pack(">H", 0x2248)                    # [0x06] movea.l a0,a1
    code += bytes.fromhex("4eb1212200000004")           # [0x08] jsr ([0,a1,d2.w],4)
    code += struct.pack(">H", 0x4E75)                    # [0x10] rts
    code += struct.pack(">H", 0x4E71)                    # [0x12] nop
    code += struct.pack(">I", 0x0000001C)                # [0x14] dc.l $1c
    code += struct.pack(">I", 0x00000020)                # [0x18] dc.l $20
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x1c] nop; nop
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "memory_indirect_long_pointer", (
        f"Expected pattern 'memory_indirect_long_pointer', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    print("  pattern_g_full_extension_memory_indirect_pointer_table_via_reg_copy: OK")


def test_pattern_h_word_offset_via_reg_copy():
    """Pattern H: LEA base,Ax; MOVEA.L Ax,Ay; JMP disp(Ay,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x0008)          # [0x02] lea $08(pc),a0 -> $0c
    code += struct.pack(">H", 0x2248)                    # [0x06] movea.l a0,a1
    code += struct.pack(">HH", 0x4EF1, 0x0000)          # [0x08] jmp 0(a1,d0.w)
    code += struct.pack(">hhh", 0, 4, 10)                # [0x0c] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x12] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x0C in t["targets"], f"Expected $000c in targets, got {t['targets']}"
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    print("  pattern_h_word_offset_via_reg_copy: OK")


def test_pattern_i_indirect_table_read_via_reg_copy():
    """Pattern I: LEA table,Ax; MOVEA.L Ax,Ay; MOVE.W (Ay,Dn),Dn; JSR d(Ay,Dn)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x02] lea $0e(pc),a0 -> $12
    code += struct.pack(">H", 0x2248)                    # [0x06] movea.l a0,a1
    code += struct.pack(">HH", 0x3031, 0x0000)          # [0x08] move.w 0(a1,d0.w),d0
    code += struct.pack(">HH", 0x4EB1, 0x0006)          # [0x0c] jsr 6(a1,d0.w)
    code += struct.pack(">H", 0x4E75)                    # [0x10] rts
    code += struct.pack(">hh", 0, 4)                     # [0x12] dc.w 0,4
    code += struct.pack(">H", 0x4E71)                    # [0x16] nop
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_table_read", (
        f"Expected pattern 'indirect_table_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_i_indirect_table_read_via_reg_copy: OK")


def test_pattern_j_indirect_pointer_read_into_jump_register():
    """Pattern J: LEA table,Ax; MOVEA.L 0(Ax,Dn.w),Ay; JMP (Ay)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x0008)          # [0x02] lea $08(pc),a0 -> $0c
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x4ED1)                    # [0x0a] jmp (a1)
    code += struct.pack(">I", 0x00000014)                # [0x0c] dc.l $14
    code += struct.pack(">I", 0x00000018)                # [0x10] dc.l $18
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x14] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    print("  pattern_j_indirect_pointer_read_into_jump_register: OK")


def test_pattern_k_pc_indirect_pointer_read_into_jump_register():
    """Pattern K: MOVEA.L 0(PC,Dn.w),Ay; JMP (Ay)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x227B, 0x0004)          # [0x02] movea.l 4(pc,d0.w),a1
    code += struct.pack(">H", 0x4ED1)                    # [0x06] jmp (a1)
    code += struct.pack(">I", 0x00000010)                # [0x08] dc.l $10
    code += struct.pack(">I", 0x00000014)                # [0x0c] dc.l $14
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x10] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x14] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    print("  pattern_k_pc_indirect_pointer_read_into_jump_register: OK")


def test_pattern_l_full_extension_pointer_read_into_jump_register():
    """Pattern L: LEA table,Ax; MOVEA.L ([0,Ax,Dn.w],4),Ay; JMP (Ay)."""
    code = b""
    code += struct.pack(">H", 0x7400)                    # [0x00] moveq #0,d2
    code += struct.pack(">HH", 0x41FA, 0x000C)          # [0x02] lea $0c(pc),a0 -> $10
    code += bytes.fromhex("2270212200000004")           # [0x06] movea.l ([0,a0,d2.w],4),a1
    code += struct.pack(">H", 0x4ED1)                    # [0x0e] jmp (a1)
    code += struct.pack(">I", 0x00000010)                # [0x10] dc.l $10
    code += struct.pack(">I", 0x00000014)                # [0x14] dc.l $14
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    print("  pattern_l_full_extension_pointer_read_into_jump_register: OK")


def test_pattern_m_word_offset_via_addq_adjusted_base():
    """Pattern M: LEA base,An; ADDQ.L #imm,An; JMP disp(An,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000A)          # [0x02] lea $0a(pc),a0 -> $0e
    code += struct.pack(">H", 0x5888)                    # [0x06] addq.l #4,a0 -> $12
    code += struct.pack(">HH", 0x4EF0, 0x0000)          # [0x08] jmp 0(a0,d0.w)
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x0c] pad; pad
    code += struct.pack(">hhh", 0, 4, 10)                # [0x10] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    assert 0x1c in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_m_word_offset_via_addq_adjusted_base: OK")


def test_pattern_n_indirect_pointer_read_via_addq_adjusted_base():
    """Pattern N: LEA table-4,An; ADDQ.L #4,An; MOVEA.L 0(An,Dn.w),Ay; JMP (Ay)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000A)          # [0x02] lea $0a(pc),a0 -> $0e
    code += struct.pack(">H", 0x5888)                    # [0x06] addq.l #4,a0 -> $12
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x4ED1)                    # [0x0c] jmp (a1)
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x0e] pad; pad
    code += struct.pack(">I", 0x00000018)                # [0x12] dc.l $18
    code += struct.pack(">I", 0x0000001C)                # [0x16] dc.l $1c
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    print("  pattern_n_indirect_pointer_read_via_addq_adjusted_base: OK")


def test_pattern_o_word_offset_via_adda_adjusted_base():
    """Pattern O: LEA base,An; ADDA.L #imm,An; JMP disp(An,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x0008)          # [0x02] lea $08(pc),a0 -> $0c
    code += bytes.fromhex("d1fc00000004")               # [0x06] adda.l #4,a0 -> $10
    code += struct.pack(">HH", 0x4EF0, 0x0000)          # [0x0c] jmp 0(a0,d0.w)
    code += struct.pack(">hhh", 0, 4, 10)                # [0x10] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1a in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_o_word_offset_via_adda_adjusted_base: OK")


def test_pattern_p_word_offset_via_subq_adjusted_base():
    """Pattern P: LEA base+imm,An; SUBQ.L #imm,An; JMP disp(An,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000C)          # [0x02] lea $0c(pc),a0 -> $10
    code += struct.pack(">H", 0x5988)                    # [0x06] subq.l #4,a0 -> $0c
    code += struct.pack(">HH", 0x4EF0, 0x0000)          # [0x08] jmp 0(a0,d0.w)
    code += struct.pack(">hhh", 6, 10, 14)               # [0x0c] dc.w 6,10,14
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x12] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x12 in t["targets"], f"Expected $0012 in targets, got {t['targets']}"
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    assert 0x1a in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_p_word_offset_via_subq_adjusted_base: OK")


def test_pattern_q_word_offset_via_suba_adjusted_base():
    """Pattern Q: LEA base+imm,An; SUBA.L #imm,An; JMP disp(An,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x02] lea $10(pc),a0 -> $14
    code += bytes.fromhex("91fc00000004")               # [0x06] suba.l #4,a0 -> $10
    code += struct.pack(">HH", 0x4EF0, 0x0000)          # [0x0c] jmp 0(a0,d0.w)
    code += struct.pack(">hhh", 6, 10, 14)               # [0x10] dc.w 6,10,14
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    assert 0x1a in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    assert 0x1e in t["targets"], f"Expected $001e in targets, got {t['targets']}"
    print("  pattern_q_word_offset_via_suba_adjusted_base: OK")


def test_pattern_r_word_offset_via_movea_pcdisp_base():
    """Pattern R: MOVEA.L d(PC),An; JMP disp(An,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x207A, 0x0006)          # [0x02] movea.l 6(pc),a0 -> $0a
    code += struct.pack(">HH", 0x4EF0, 0x0000)          # [0x06] jmp 0(a0,d0.w)
    code += struct.pack(">hhh", 0, 4, 10)                # [0x0a] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x10] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x14] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x0A in t["targets"], f"Expected $000a in targets, got {t['targets']}"
    assert 0x0E in t["targets"], f"Expected $000e in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    print("  pattern_r_word_offset_via_movea_pcdisp_base: OK")


def test_pattern_s_word_offset_via_movea_pcindex_base():
    """Pattern S: MOVEA.L d(PC,Dn.w),An; JMP disp(An,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7008)                    # [0x00] moveq #8,d0
    code += struct.pack(">HH", 0x207B, 0x0000)          # [0x02] movea.l 0(pc,d0.w),a0 -> $0c
    code += struct.pack(">HH", 0x4EF0, 0x0000)          # [0x06] jmp 0(a0,d0.w)
    code += struct.pack(">H", 0x4E71)                    # [0x0a] pad
    code += struct.pack(">hhh", 0, 4, 10)                # [0x0c] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x12] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x0C in t["targets"], f"Expected $000c in targets, got {t['targets']}"
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    print("  pattern_s_word_offset_via_movea_pcindex_base: OK")


def test_pattern_v_word_offset_via_movea_pcindex_base_with_index_copy():
    """Pattern V: MOVEQ -> Dn copy -> MOVEA.L d(PC,Dn),An -> JMP disp(An,Dm)."""
    code = b""
    code += struct.pack(">H", 0x7208)                    # [0x00] moveq #8,d1
    code += struct.pack(">H", 0x3001)                    # [0x02] move.w d1,d0
    code += struct.pack(">H", 0x7400)                    # [0x04] moveq #0,d2
    code += struct.pack(">HH", 0x207B, 0x0000)          # [0x06] movea.l 0(pc,d0.w),a0 -> $10
    code += struct.pack(">HH", 0x4EF0, 0x2000)          # [0x0a] jmp 0(a0,d2.w)
    code += struct.pack(">H", 0x4E71)                    # [0x0e] pad
    code += struct.pack(">hhh", 6, 10, 14)               # [0x10] dc.w 6,10,14
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    assert 0x1E in t["targets"], f"Expected $001e in targets, got {t['targets']}"
    print("  pattern_v_word_offset_via_movea_pcindex_base_with_index_copy: OK")


def test_pattern_w_word_offset_via_movea_pcindex_base_with_cross_bank_index_copy():
    """Pattern W: MOVEQ -> MOVEA.L Dn,An -> MOVEA.L d(PC,An),Ax -> JMP disp(Ax,Dm)."""
    code = b""
    code += struct.pack(">H", 0x7208)                    # [0x00] moveq #8,d1
    code += struct.pack(">H", 0x2041)                    # [0x02] movea.l d1,a0
    code += struct.pack(">H", 0x7400)                    # [0x04] moveq #0,d2
    code += bytes.fromhex("227b8000")                   # [0x06] movea.l 0(pc,a0.w),a1 -> $10
    code += struct.pack(">HH", 0x4EF1, 0x2000)          # [0x0a] jmp 0(a1,d2.w)
    code += struct.pack(">H", 0x4E71)                    # [0x0e] pad
    code += struct.pack(">hhh", 6, 10, 14)               # [0x10] dc.w 6,10,14
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    assert 0x1E in t["targets"], f"Expected $001e in targets, got {t['targets']}"
    print("  pattern_w_word_offset_via_movea_pcindex_base_with_cross_bank_index_copy: OK")


def test_pattern_x_word_offset_via_movea_pcindex_base_with_index_adjustment():
    """Pattern X: MOVEQ -> ADDQ -> Dn copy -> MOVEA.L d(PC,Dn),An -> JMP disp(An,Dm)."""
    code = b""
    code += struct.pack(">H", 0x7207)                    # [0x00] moveq #7,d1
    code += struct.pack(">H", 0x5241)                    # [0x02] addq.w #1,d1 -> 8
    code += struct.pack(">H", 0x3001)                    # [0x04] move.w d1,d0
    code += struct.pack(">H", 0x7400)                    # [0x06] moveq #0,d2
    code += struct.pack(">HH", 0x207B, 0x0000)          # [0x08] movea.l 0(pc,d0.w),a0 -> $12
    code += struct.pack(">HH", 0x4EF0, 0x2000)          # [0x0c] jmp 0(a0,d2.w)
    code += struct.pack(">H", 0x4E71)                    # [0x10] pad
    code += struct.pack(">hhh", 6, 10, 14)               # [0x12] dc.w 6,10,14
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    print("  pattern_x_word_offset_via_movea_pcindex_base_with_index_adjustment: OK")


def test_pattern_y_word_offset_via_movea_pcindex_base_with_clr_index():
    """Pattern Y: CLR Dn -> MOVEA.L d(PC,Dn),An -> JMP disp(An,Dm)."""
    code = b""
    code += struct.pack(">H", 0x4240)                    # [0x00] clr.w d0
    code += struct.pack(">H", 0x7400)                    # [0x02] moveq #0,d2
    code += struct.pack(">HH", 0x207B, 0x0006)          # [0x04] movea.l 6(pc,d0.w),a0 -> $0c
    code += struct.pack(">HH", 0x4EF0, 0x2000)          # [0x08] jmp 0(a0,d2.w)
    code += struct.pack(">hhh", 6, 10, 14)               # [0x0c] dc.w 6,10,14
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x12] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x12 in t["targets"], f"Expected $0012 in targets, got {t['targets']}"
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_y_word_offset_via_movea_pcindex_base_with_clr_index: OK")


def test_pattern_z_indirect_pointer_read_via_data_register_copy():
    """Pattern Z: LEA table,Ax; MOVE.L 0(Ax,Dn.w),Dy; MOVEA.L Dy,Az; JMP (Az)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000C)          # [0x02] lea $0c(pc),a0 -> $10
    code += struct.pack(">HH", 0x2230, 0x0000)          # [0x06] move.l 0(a0,d0.w),d1
    code += struct.pack(">H", 0x2441)                    # [0x0a] movea.l d1,a2
    code += struct.pack(">H", 0x4ED2)                    # [0x0c] jmp (a2)
    code += struct.pack(">H", 0x4E71)                    # [0x0e] nop
    code += struct.pack(">I", 0x00000018)                # [0x10] dc.l $18
    code += struct.pack(">I", 0x0000001C)                # [0x14] dc.l $1c
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_z_indirect_pointer_read_via_data_register_copy: OK")


def test_pattern_aa_postindexed_pointer_read_into_jump_register():
    """Pattern AA: LEA ptr,Ax; MOVEA.L ([0,Ax],Dn.w,4),Ay; JMP (Ay)."""
    code = b""
    code += struct.pack(">H", 0x7400)                    # [0x00] moveq #0,d2
    code += struct.pack(">HH", 0x41FA, 0x000C)          # [0x02] lea $0c(pc),a0 -> $10
    code += bytes.fromhex("2270212600000004")           # [0x06] movea.l ([0,a0],d2.w,4),a1
    code += struct.pack(">H", 0x4ED1)                    # [0x0e] jmp (a1)
    code += struct.pack(">I", 0x00000014)                # [0x10] dc.l $14
    code += struct.pack(">I", 0x00000000)                # [0x14] pad long
    code += struct.pack(">I", 0x00000024)                # [0x18] dc.l $24
    code += struct.pack(">I", 0x00000028)                # [0x1c] dc.l $28
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x20] nop; nop
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x28] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    assert 0x28 in t["targets"], f"Expected $0028 in targets, got {t['targets']}"
    print("  pattern_aa_postindexed_pointer_read_into_jump_register: OK")


def test_pattern_ab_word_offset_via_movea_immediate_base():
    """Pattern AB: MOVEA.L #table,An; JMP disp(An,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += bytes.fromhex("207c00000010")               # [0x02] movea.l #$10,a0
    code += struct.pack(">HH", 0x4EF0, 0x0000)          # [0x08] jmp 0(a0,d0.w)
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x0c] pad; pad
    code += struct.pack(">hhh", 0, 4, 10)               # [0x10] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_ab_word_offset_via_movea_immediate_base: OK")


def test_pattern_ac_indirect_pointer_read_via_movea_immediate_base():
    """Pattern AC: MOVEA.L #table,Ax; MOVEA.L 0(Ax,Dn.w),Ay; JMP (Ay)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += bytes.fromhex("207c00000012")               # [0x02] movea.l #$12,a0
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x4ED1)                    # [0x0c] jmp (a1)
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x0e] pad; pad
    code += struct.pack(">I", 0x00000018)                # [0x12] dc.l $18
    code += struct.pack(">I", 0x0000001C)                # [0x16] dc.l $1c
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_ac_indirect_pointer_read_via_movea_immediate_base: OK")


def test_pattern_ad_indirect_pointer_read_via_two_long_copies():
    """Pattern AD: pointer load flows through two long register copies before JMP."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000C)          # [0x02] lea $0c(pc),a0 -> $10
    code += struct.pack(">HH", 0x2230, 0x0000)          # [0x06] move.l 0(a0,d0.w),d1
    code += struct.pack(">H", 0x2401)                    # [0x0a] move.l d1,d2
    code += struct.pack(">H", 0x2442)                    # [0x0c] movea.l d2,a2
    code += struct.pack(">H", 0x4ED2)                    # [0x0e] jmp (a2)
    code += struct.pack(">I", 0x00000018)                # [0x10] dc.l $18
    code += struct.pack(">I", 0x0000001C)                # [0x14] dc.l $1c
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_ad_indirect_pointer_read_via_two_long_copies: OK")


def test_pattern_ae_indirect_pointer_read_via_adjusted_loaded_pointer():
    """Pattern AE: pointer loaded from table, then adjusted before JMP."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000A)          # [0x02] lea $0a(pc),a0 -> $0e
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x5889)                    # [0x0a] addq.l #4,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x0c] jmp (a1)
    code += struct.pack(">I", 0x00000014)                # [0x0e] dc.l $14
    code += struct.pack(">I", 0x00000018)                # [0x12] dc.l $18
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_ae_indirect_pointer_read_via_adjusted_loaded_pointer: OK")


def test_pattern_af_word_offset_via_constant_register_base_copy():
    """Pattern AF: constant Dn copied into An before indexed word-offset JMP."""
    code = b""
    code += struct.pack(">H", 0x7010)                    # [0x00] moveq #$10,d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">H", 0x2040)                    # [0x04] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x06] jmp 0(a0,d1.w)
    code += struct.pack(">HHH", 0x4E71, 0x4E71, 0x4E71) # [0x0a] pad to $10
    code += struct.pack(">hhh", 0, 4, 10)               # [0x10] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_af_word_offset_via_constant_register_base_copy: OK")


def test_pattern_ag_indirect_pointer_read_via_constant_register_base_copy():
    """Pattern AG: constant Dn copied into An before indexed long pointer load."""
    code = b""
    code += struct.pack(">H", 0x7012)                    # [0x00] moveq #$12,d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">H", 0x2040)                    # [0x04] movea.l d0,a0
    code += struct.pack(">HH", 0x2270, 0x1000)          # [0x06] movea.l 0(a0,d1.w),a1
    code += struct.pack(">H", 0x4ED1)                    # [0x0a] jmp (a1)
    code += struct.pack(">HHH", 0x4E71, 0x4E71, 0x4E71) # [0x0c] pad to $12
    code += struct.pack(">I", 0x0000001A)                # [0x12] dc.l $1a
    code += struct.pack(">I", 0x0000001E)                # [0x16] dc.l $1e
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    assert 0x1E in t["targets"], f"Expected $001e in targets, got {t['targets']}"
    print("  pattern_ag_indirect_pointer_read_via_constant_register_base_copy: OK")


def test_pattern_ah_indirect_pointer_read_via_adjusted_constant_register_base_copy():
    """Pattern AH: adjusted constant Dn copied into An before indexed pointer load."""
    code = b""
    code += struct.pack(">H", 0x7014)                    # [0x00] moveq #$14,d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">H", 0x5880)                    # [0x04] addq.l #4,d0 -> $18
    code += struct.pack(">H", 0x2040)                    # [0x06] movea.l d0,a0
    code += struct.pack(">HH", 0x2270, 0x1000)          # [0x08] movea.l 0(a0,d1.w),a1
    code += struct.pack(">H", 0x4ED1)                    # [0x0c] jmp (a1)
    code += struct.pack(">HHHHH", 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71)  # [0x0e] pad to $18
    code += struct.pack(">I", 0x00000020)                # [0x18] dc.l $20
    code += struct.pack(">I", 0x00000024)                # [0x1c] dc.l $24
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    print("  pattern_ah_indirect_pointer_read_via_adjusted_constant_register_base_copy: OK")


def test_pattern_ai_word_offset_via_clr_seeded_constant_register_base_copy():
    """Pattern AI: CLR-seeded Dn copied into An before indexed word-offset JMP."""
    code = b""
    code += struct.pack(">H", 0x4280)                    # [0x00] clr.l d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">H", 0x5080)                    # [0x04] addq.l #8,d0
    code += struct.pack(">H", 0x5880)                    # [0x06] addq.l #4,d0
    code += struct.pack(">H", 0x5880)                    # [0x08] addq.l #4,d0 -> $10
    code += struct.pack(">H", 0x2040)                    # [0x0a] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0c] jmp 0(a0,d1.w)
    code += struct.pack(">hhh", 0, 4, 10)               # [0x10] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_ai_word_offset_via_clr_seeded_constant_register_base_copy: OK")


def test_pattern_aj_indirect_pointer_read_via_data_register_adjust_after_copy():
    """Pattern AJ: loaded pointer copied through Dn, adjusted, then moved to jump An."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x02] lea $0e(pc),a0 -> $12
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0a] move.l a1,d2
    code += struct.pack(">H", 0x5882)                    # [0x0c] addq.l #4,d2
    code += struct.pack(">H", 0x2642)                    # [0x0e] movea.l d2,a3
    code += struct.pack(">H", 0x4ED3)                    # [0x10] jmp (a3)
    code += struct.pack(">I", 0x00000018)                # [0x12] dc.l $18
    code += struct.pack(">I", 0x0000001C)                # [0x16] dc.l $1c
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    print("  pattern_aj_indirect_pointer_read_via_data_register_adjust_after_copy: OK")


def test_pattern_ak_word_offset_via_register_add_constant_base():
    """Pattern AK: constant Dm added into base Dn before MOVEA and indexed JMP."""
    code = b""
    code += struct.pack(">H", 0x7010)                    # [0x00] moveq #$10,d0
    code += struct.pack(">H", 0x7404)                    # [0x02] moveq #4,d2
    code += struct.pack(">H", 0x7200)                    # [0x04] moveq #0,d1
    code += struct.pack(">H", 0xD082)                    # [0x06] add.l d2,d0 -> $14
    code += struct.pack(">H", 0x2040)                    # [0x08] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0a] jmp 0(a0,d1.w)
    code += struct.pack(">HHH", 0x4E71, 0x4E71, 0x4E71) # [0x0e] pad to $14
    code += struct.pack(">hhh", 0, 4, 10)               # [0x14] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1E in t["targets"], f"Expected $001e in targets, got {t['targets']}"
    print("  pattern_ak_word_offset_via_register_add_constant_base: OK")


def test_pattern_al_indirect_pointer_read_via_register_add_constant_after_copy():
    """Pattern AL: loaded pointer copied through Dn and adjusted by constant Dm."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x43FA, 0x0010)          # [0x02] lea $10(pc),a1 -> $14
    code += struct.pack(">HH", 0x2471, 0x0000)          # [0x06] movea.l 0(a1,d0.w),a2
    code += struct.pack(">H", 0x260A)                    # [0x0a] move.l a2,d3
    code += struct.pack(">H", 0x7804)                    # [0x0c] moveq #4,d4
    code += struct.pack(">H", 0xD684)                    # [0x0e] add.l d4,d3
    code += struct.pack(">H", 0x2A43)                    # [0x10] movea.l d3,a5
    code += struct.pack(">H", 0x4ED5)                    # [0x12] jmp (a5)
    code += struct.pack(">I", 0x0000001C)                # [0x14] dc.l $1c
    code += struct.pack(">I", 0x00000020)                # [0x18] dc.l $20
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    print("  pattern_al_indirect_pointer_read_via_register_add_constant_after_copy: OK")


def test_pattern_am_word_offset_via_register_add_constant_base_adjustment():
    """Pattern AM: LEA base,An; ADDA.L Dn,An with constant Dn; JMP disp(An,Dm.w)."""
    code = b""
    code += struct.pack(">H", 0x7404)                    # [0x00] moveq #4,d2
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x04] lea $0e(pc),a0 -> $14
    code += struct.pack(">H", 0xD1C2)                    # [0x08] adda.l d2,a0 -> $18
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0a] jmp 0(a0,d1.w)
    code += struct.pack(">HHHHH", 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71)  # [0x0e] pad to $18
    code += struct.pack(">hhh", 0, 4, 10)               # [0x18] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    assert 0x22 in t["targets"], f"Expected $0022 in targets, got {t['targets']}"
    print("  pattern_am_word_offset_via_register_add_constant_base_adjustment: OK")


def test_pattern_an_word_offset_via_shifted_constant_register_base():
    """Pattern AN: constant Dn shifted before MOVEA and indexed word-offset JMP."""
    code = b""
    code += struct.pack(">H", 0x7004)                    # [0x00] moveq #4,d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">H", 0xE588)                    # [0x04] lsl.l #2,d0 -> $10
    code += struct.pack(">H", 0x2040)                    # [0x06] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x08] jmp 0(a0,d1.w)
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x0c] pad to $10
    code += struct.pack(">hhh", 0, 4, 10)               # [0x10] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_an_word_offset_via_shifted_constant_register_base: OK")


def test_pattern_ao_word_offset_via_masked_constant_register_base():
    """Pattern AO: constant Dn masked by immediate logical op before MOVEA/JMP."""
    code = b""
    code += struct.pack(">H", 0x701F)                    # [0x00] moveq #$1f,d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += bytes.fromhex("02800000001c")               # [0x04] andi.l #$1c,d0
    code += struct.pack(">H", 0x2040)                    # [0x0a] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0c] jmp 0(a0,d1.w)
    code += struct.pack(">HHHHHH", 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71)  # [0x10] pad to $1c
    code += struct.pack(">hhh", 0, 4, 10)               # [0x1c] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x26] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x26 in t["targets"], f"Expected $0026 in targets, got {t['targets']}"
    print("  pattern_ao_word_offset_via_masked_constant_register_base: OK")


def test_pattern_aq_word_offset_via_register_shifted_constant_register_base():
    """Pattern AQ: constant Dn shifted by constant Dm before MOVEA and indexed JMP."""
    code = b""
    code += struct.pack(">H", 0x7004)                    # [0x00] moveq #4,d0
    code += struct.pack(">H", 0x7402)                    # [0x02] moveq #2,d2
    code += struct.pack(">H", 0x7200)                    # [0x04] moveq #0,d1
    code += struct.pack(">H", 0xE5A8)                    # [0x06] lsl.l d2,d0 -> $10
    code += struct.pack(">H", 0x2040)                    # [0x08] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0a] jmp 0(a0,d1.w)
    code += struct.pack(">H", 0x4E71)                    # [0x0e] pad to $10
    code += struct.pack(">hhh", 0, 4, 10)               # [0x10] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_aq_word_offset_via_register_shifted_constant_register_base: OK")


def test_pattern_ar_word_offset_via_register_or_constant_base():
    """Pattern AR: constant Dn ORed with constant source register before MOVEA/JMP."""
    code = b""
    code += struct.pack(">H", 0x7010)                    # [0x00] moveq #$10,d0
    code += struct.pack(">H", 0x740C)                    # [0x02] moveq #$0c,d2
    code += struct.pack(">H", 0x7200)                    # [0x04] moveq #0,d1
    code += struct.pack(">H", 0x8082)                    # [0x06] or.l d2,d0 -> $1c
    code += struct.pack(">H", 0x2040)                    # [0x08] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0a] jmp 0(a0,d1.w)
    code += struct.pack(">HHHHHH", 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71)  # [0x0e] pad to $1c
    code += struct.pack(">hhh", 0, 4, 10)               # [0x1c] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x26] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x26 in t["targets"], f"Expected $0026 in targets, got {t['targets']}"
    print("  pattern_ar_word_offset_via_register_or_constant_base: OK")


def test_pattern_as_word_offset_via_not_constant_register_base():
    """Pattern AS: constant Dn transformed by NOT before MOVEA/JMP."""
    code = b""
    code += struct.pack(">H", 0x70E3)                    # [0x00] moveq #$e3,d0 -> -29
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">H", 0x4680)                    # [0x04] not.l d0 -> $1c
    code += struct.pack(">H", 0x2040)                    # [0x06] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x08] jmp 0(a0,d1.w)
    code += struct.pack(">HHHHHHHH", 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71)  # [0x0c] pad to $1c
    code += struct.pack(">hhh", 0, 4, 10)               # [0x1c] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x26] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x26 in t["targets"], f"Expected $0026 in targets, got {t['targets']}"
    print("  pattern_as_word_offset_via_not_constant_register_base: OK")


def test_pattern_at_indirect_pointer_read_via_unary_transformed_loaded_pointer():
    """Pattern AT: loaded pointer copied through Dn, unary-transformed, then jumped.""" 
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x02] lea $0e(pc),a0 -> $12
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0a] move.l a1,d2
    code += struct.pack(">H", 0x4682)                    # [0x0c] not.l d2
    code += struct.pack(">H", 0x2242)                    # [0x0e] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x10] jmp (a1)
    code += struct.pack(">I", 0xFFFFFFE7)                # [0x12] dc.l ~$18
    code += struct.pack(">I", 0xFFFFFFE3)                # [0x16] dc.l ~$1c
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_at_indirect_pointer_read_via_unary_transformed_loaded_pointer: OK")


def test_pattern_au_word_offset_via_swapped_constant_register_base():
    """Pattern AU: constant Dn transformed by SWAP before MOVEA/JMP."""
    code = b""
    code += bytes.fromhex("203c00100000")               # [0x00] move.l #$00100000,d0
    code += struct.pack(">H", 0x7200)                    # [0x06] moveq #0,d1
    code += struct.pack(">H", 0x4840)                    # [0x08] swap d0 -> $10
    code += struct.pack(">H", 0x2040)                    # [0x0a] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0c] jmp 0(a0,d1.w)
    code += struct.pack(">hhh", 0, 4, 10)               # [0x10] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_au_word_offset_via_swapped_constant_register_base: OK")


def test_pattern_av_word_offset_via_ext_constant_register_base():
    """Pattern AV: constant Dn sign-extended by EXT before MOVEA/JMP."""
    code = b""
    code += bytes.fromhex("203c00000080")               # [0x00] move.l #$00000080,d0
    code += struct.pack(">H", 0x7200)                    # [0x06] moveq #0,d1
    code += struct.pack(">H", 0x4880)                    # [0x08] ext.w d0 -> $0000ff80
    code += struct.pack(">H", 0x2040)                    # [0x0a] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0c] jmp 0(a0,d1.w)
    code += bytes(0xFF80 - len(code))                    # pad to $ff80
    code += struct.pack(">hhh", 0, 4, 10)               # [$ff80] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [$ff86] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [$ff8a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0xFF80 in t["targets"], f"Expected $ff80 in targets, got {t['targets']}"
    assert 0xFF84 in t["targets"], f"Expected $ff84 in targets, got {t['targets']}"
    assert 0xFF8A in t["targets"], f"Expected $ff8a in targets, got {t['targets']}"
    print("  pattern_av_word_offset_via_ext_constant_register_base: OK")


def test_pattern_aw_indirect_pointer_read_via_swapped_loaded_pointer():
    """Pattern AW: loaded pointer copied through Dn, swapped, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x02] lea $0e(pc),a0 -> $12
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0a] move.l a1,d2
    code += struct.pack(">H", 0x4842)                    # [0x0c] swap d2
    code += struct.pack(">H", 0x2242)                    # [0x0e] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x10] jmp (a1)
    code += struct.pack(">I", 0x00180000)                # [0x12] dc.l $00180000
    code += struct.pack(">I", 0x001C0000)                # [0x16] dc.l $001c0000
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_aw_indirect_pointer_read_via_swapped_loaded_pointer: OK")


def test_pattern_ax_indirect_pointer_read_via_sign_extended_loaded_pointer():
    """Pattern AX: loaded pointer copied through Dn, EXT-transformed, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x02] lea $0e(pc),a0 -> $12
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0a] move.l a1,d2
    code += struct.pack(">H", 0x4882)                    # [0x0c] ext.w d2
    code += struct.pack(">H", 0x2242)                    # [0x0e] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x10] jmp (a1)
    code += struct.pack(">I", 0x000000F8)                # [0x12] dc.l sign-extends to $0000fff8
    code += struct.pack(">I", 0x00000000)                # [0x16] stopper
    code += bytes(0xFFF8 - len(code))                    # pad to $fff8
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [$fff8] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0xFFF8 in t["targets"], f"Expected $fff8 in targets, got {t['targets']}"
    print("  pattern_ax_indirect_pointer_read_via_sign_extended_loaded_pointer: OK")


def test_pattern_ay_full_extension_postindexed_pointer_dispatch():
    """Pattern AY: LEA ptr,Ax; JMP ([0,Ax],Dn.w,4) through long pointers."""
    code = b""
    code += struct.pack(">H", 0x7400)                    # [0x00] moveq #0,d2
    code += struct.pack(">HH", 0x41FA, 0x000C)          # [0x02] lea $0c(pc),a0 -> $10
    code += bytes.fromhex("4ef0212600000004")           # [0x06] jmp ([0,a0],d2.w,4)
    code += struct.pack(">H", 0x4E71)                    # [0x0e] pad to $10
    code += struct.pack(">I", 0x00000014)                # [0x10] dc.l $14
    code += struct.pack(">I", 0x00000000)                # [0x14] pad long
    code += struct.pack(">I", 0x00000024)                # [0x18] dc.l $24
    code += struct.pack(">I", 0x00000028)                # [0x1c] dc.l $28
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x20] nop; nop
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x28] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "memory_indirect_postindexed_long_pointer", (
        f"Expected pattern 'memory_indirect_postindexed_long_pointer', got {t['pattern']!r}")
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    assert 0x28 in t["targets"], f"Expected $0028 in targets, got {t['targets']}"
    print("  pattern_ay_full_extension_postindexed_pointer_dispatch: OK")


def test_pattern_az_pc_full_extension_postindexed_pointer_dispatch():
    """Pattern AZ: JMP ([0,PC],Dn.w,4) through long pointers."""
    code = b""
    code += struct.pack(">H", 0x7400)                    # [0x00] moveq #0,d2
    code += bytes.fromhex("4efb2126000c0004")           # [0x02] jmp ([12,pc],d2.w,4)
    code += struct.pack(">HHH", 0x4E71, 0x4E71, 0x4E71) # [0x0a] pad to $10
    code += struct.pack(">I", 0x00000014)                # [0x10] dc.l $14
    code += struct.pack(">I", 0x00000000)                # [0x14] pad long
    code += struct.pack(">I", 0x00000024)                # [0x18] dc.l $24
    code += struct.pack(">I", 0x00000028)                # [0x1c] dc.l $28
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x20] nop; nop
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x28] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "pc_memory_indirect_postindexed_long_pointer", (
        f"Expected pattern 'pc_memory_indirect_postindexed_long_pointer', got {t['pattern']!r}")
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    assert 0x28 in t["targets"], f"Expected $0028 in targets, got {t['targets']}"
    print("  pattern_az_pc_full_extension_postindexed_pointer_dispatch: OK")


def test_pattern_ba_word_offset_via_multiplied_constant_register_base():
    """Pattern BA: constant Dn multiplied by constant source before MOVEA/JMP."""
    code = b""
    code += struct.pack(">H", 0x7007)                    # [0x00] moveq #7,d0
    code += struct.pack(">H", 0x7404)                    # [0x02] moveq #4,d2
    code += struct.pack(">H", 0x7200)                    # [0x04] moveq #0,d1
    code += struct.pack(">H", 0xC0C2)                    # [0x06] mulu.w d2,d0 -> $1c
    code += struct.pack(">H", 0x2040)                    # [0x08] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0a] jmp 0(a0,d1.w)
    code += struct.pack(">HHHHHH", 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71)  # [0x0e] pad to $1c
    code += struct.pack(">hhh", 0, 4, 10)               # [0x1c] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x26] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x26 in t["targets"], f"Expected $0026 in targets, got {t['targets']}"
    print("  pattern_ba_word_offset_via_multiplied_constant_register_base: OK")


def test_pattern_bb_word_offset_via_divided_constant_register_base():
    """Pattern BB: constant Dn divided by constant source before MOVEA/JMP."""
    code = b""
    code += struct.pack(">H", 0x7070)                    # [0x00] moveq #112,d0
    code += struct.pack(">H", 0x7404)                    # [0x02] moveq #4,d2
    code += struct.pack(">H", 0x7200)                    # [0x04] moveq #0,d1
    code += struct.pack(">H", 0x80C2)                    # [0x06] divu.w d2,d0 -> $1c
    code += struct.pack(">H", 0x2040)                    # [0x08] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0a] jmp 0(a0,d1.w)
    code += struct.pack(">HHHHHH", 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71)  # [0x0e] pad to $1c
    code += struct.pack(">hhh", 0, 4, 10)               # [0x1c] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x26] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x26 in t["targets"], f"Expected $0026 in targets, got {t['targets']}"
    print("  pattern_bb_word_offset_via_divided_constant_register_base: OK")


def test_pattern_bc_indirect_pointer_read_via_multiplied_loaded_pointer():
    """Pattern BC: loaded pointer copied through Dn, multiplied, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x02] lea $10(pc),a0 -> $14
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0a] move.l a1,d2
    code += bytes.fromhex("c4fc0004")                   # [0x0c] mulu.w #$4,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">I", 0x00000006)                # [0x14] dc.l $06
    code += struct.pack(">I", 0x00000007)                # [0x18] dc.l $07
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_bc_indirect_pointer_read_via_multiplied_loaded_pointer: OK")


def test_pattern_bd_indirect_pointer_read_via_divided_loaded_pointer():
    """Pattern BD: loaded pointer copied through Dn, divided, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x02] lea $10(pc),a0 -> $14
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0a] move.l a1,d2
    code += bytes.fromhex("84fc0004")                   # [0x0c] divu.w #$4,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">I", 0x00000080)                # [0x14] dc.l $80
    code += struct.pack(">I", 0x00000090)                # [0x18] dc.l $90
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    print("  pattern_bd_indirect_pointer_read_via_divided_loaded_pointer: OK")


def test_pattern_be_indirect_pointer_read_via_register_multiplied_loaded_pointer():
    """Pattern BE: loaded pointer copied through Dn, multiplied by constant register, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">H", 0x7604)                    # [0x02] moveq #4,d3
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x04] lea $10(pc),a0 -> $16
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0c] move.l a1,d2
    code += struct.pack(">H", 0xC4C3)                    # [0x0e] mulu.w d3,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">H", 0x4E71)                    # [0x14] pad to $16
    code += struct.pack(">I", 0x00000006)                # [0x16] dc.l $06
    code += struct.pack(">I", 0x00000007)                # [0x1a] dc.l $07
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_be_indirect_pointer_read_via_register_multiplied_loaded_pointer: OK")


def test_pattern_bf_indirect_pointer_read_via_register_divided_loaded_pointer():
    """Pattern BF: loaded pointer copied through Dn, divided by constant register, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">H", 0x7604)                    # [0x02] moveq #4,d3
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x04] lea $10(pc),a0 -> $16
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0c] move.l a1,d2
    code += struct.pack(">H", 0x84C3)                    # [0x0e] divu.w d3,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">H", 0x4E71)                    # [0x14] pad to $16
    code += struct.pack(">I", 0x00000080)                # [0x16] dc.l $80
    code += struct.pack(">I", 0x00000090)                # [0x1a] dc.l $90
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x26] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    print("  pattern_bf_indirect_pointer_read_via_register_divided_loaded_pointer: OK")


def test_pattern_bg_indirect_pointer_read_via_register_shifted_loaded_pointer():
    """Pattern BG: loaded pointer copied through Dn, shifted by constant register, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">H", 0x7602)                    # [0x02] moveq #2,d3
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x04] lea $10(pc),a0 -> $16
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0c] move.l a1,d2
    code += struct.pack(">H", 0xE7AA)                    # [0x0e] lsl.l d3,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">H", 0x4E71)                    # [0x14] pad to $16
    code += struct.pack(">I", 0x00000006)                # [0x16] dc.l $06
    code += struct.pack(">I", 0x00000007)                # [0x1a] dc.l $07
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_bg_indirect_pointer_read_via_register_shifted_loaded_pointer: OK")


def test_pattern_bh_indirect_pointer_read_via_register_logical_loaded_pointer():
    """Pattern BH: loaded pointer copied through Dn, ORed with constant register, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">H", 0x7608)                    # [0x02] moveq #8,d3
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x04] lea $10(pc),a0 -> $16
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0c] move.l a1,d2
    code += struct.pack(">H", 0x8483)                    # [0x0e] or.l d3,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">H", 0x4E71)                    # [0x14] pad to $16
    code += struct.pack(">I", 0x00000010)                # [0x16] dc.l $10
    code += struct.pack(">I", 0x00000014)                # [0x1a] dc.l $14
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_bh_indirect_pointer_read_via_register_logical_loaded_pointer: OK")


def test_pattern_bi_indirect_pointer_read_via_register_divided_loaded_pointer():
    """Pattern BI: loaded pointer copied through Dn, divided by constant register, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">H", 0x7604)                    # [0x02] moveq #4,d3
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x04] lea $10(pc),a0 -> $16
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0c] move.l a1,d2
    code += struct.pack(">H", 0x84C3)                    # [0x0e] divu.w d3,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">H", 0x4E71)                    # [0x14] pad to $16
    code += struct.pack(">I", 0x00000080)                # [0x16] dc.l $80
    code += struct.pack(">I", 0x00000090)                # [0x1a] dc.l $90
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x26] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    print("  pattern_bi_indirect_pointer_read_via_register_divided_loaded_pointer: OK")


def test_pattern_bj_word_offset_via_rotated_constant_register_base():
    """Pattern BJ: constant Dn rotated before MOVEA and indexed JMP."""
    code = b""
    code += struct.pack(">H", 0x7001)                    # [0x00] moveq #1,d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">H", 0xE998)                    # [0x04] rol.l #4,d0 -> $10
    code += struct.pack(">H", 0x2040)                    # [0x06] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x08] jmp 0(a0,d1.w)
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x0c] pad to $10
    code += struct.pack(">hhh", 0, 4, 10)               # [0x10] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_bj_word_offset_via_rotated_constant_register_base: OK")


def test_pattern_bk_indirect_pointer_read_via_register_rotated_loaded_pointer():
    """Pattern BK: loaded pointer copied through Dn, rotated by constant register, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">H", 0x7601)                    # [0x02] moveq #1,d3
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x04] lea $10(pc),a0 -> $16
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0c] move.l a1,d2
    code += struct.pack(">H", 0xE7BA)                    # [0x0e] rol.l d3,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">H", 0x4E71)                    # [0x14] pad to $16
    code += struct.pack(">I", 0x0000000C)                # [0x16] dc.l $0c
    code += struct.pack(">I", 0x0000000E)                # [0x1a] dc.l $0e
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_bk_indirect_pointer_read_via_register_rotated_loaded_pointer: OK")


def test_pattern_bl_word_offset_via_exg_base_copy():
    """Pattern BL: LEA base,Ax; EXG Ax,Ay; JMP disp(Ay,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x0008)          # [0x02] lea $08(pc),a0 -> $0c
    code += struct.pack(">H", 0xC149)                    # [0x06] exg a0,a1
    code += struct.pack(">HH", 0x4EF1, 0x0000)          # [0x08] jmp 0(a1,d0.w)
    code += struct.pack(">hhh", 0, 4, 10)               # [0x0c] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x12] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x0C in t["targets"], f"Expected $000c in targets, got {t['targets']}"
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    print("  pattern_bl_word_offset_via_exg_base_copy: OK")


def test_pattern_bm_indirect_pointer_read_via_exg_loaded_pointer_copy():
    """Pattern BM: loaded pointer swapped into Dn with EXG, then moved back to An for jump."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">H", 0x7400)                    # [0x02] moveq #0,d2
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x04] lea $0e(pc),a0 -> $14
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0xC589)                    # [0x0c] exg d2,a1
    code += struct.pack(">H", 0x2442)                    # [0x0e] movea.l d2,a2
    code += struct.pack(">H", 0x4ED2)                    # [0x10] jmp (a2)
    code += struct.pack(">H", 0x4E71)                    # [0x12] pad
    code += struct.pack(">I", 0x0000001C)                # [0x14] dc.l $1c
    code += struct.pack(">I", 0x00000020)                # [0x18] dc.l $20
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    print("  pattern_bm_indirect_pointer_read_via_exg_loaded_pointer_copy: OK")


def test_pattern_bn_word_offset_via_bitset_constant_register_base():
    """Pattern BN: constant Dn bit-set before MOVEA and indexed JMP."""
    code = b""
    code += struct.pack(">H", 0x7002)                    # [0x00] moveq #2,d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += bytes.fromhex("08c00004")                   # [0x04] bset #4,d0 -> $12
    code += struct.pack(">H", 0x2040)                    # [0x08] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0a] jmp 0(a0,d1.w)
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x0e] pad to $12
    code += struct.pack(">hhh", -2, 2, 8)               # [0x12] dc.w table -> $10,$14,$1a
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x18] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_bn_word_offset_via_bitset_constant_register_base: OK")


def test_pattern_bo_indirect_pointer_read_via_bitset_loaded_pointer():
    """Pattern BO: loaded pointer copied through Dn, bit-set, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x0010)          # [0x02] lea $10(pc),a0 -> $14
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0a] move.l a1,d2
    code += bytes.fromhex("08c20002")                   # [0x0c] bset #2,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">I", 0x00000018)                # [0x14] dc.l $18 -> bset #2 => $1c
    code += struct.pack(">I", 0x00000020)                # [0x18] dc.l $20 -> bset #2 => $24
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    print("  pattern_bo_indirect_pointer_read_via_bitset_loaded_pointer: OK")


def test_pattern_bp_word_offset_via_register_bitset_constant_base():
    """Pattern BP: constant Dn bit-set by constant register before MOVEA/JMP."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">H", 0x7604)                    # [0x02] moveq #4,d3
    code += struct.pack(">H", 0x7200)                    # [0x04] moveq #0,d1
    code += struct.pack(">H", 0x07C0)                    # [0x06] bset d3,d0 -> $10
    code += struct.pack(">H", 0x2040)                    # [0x08] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0a] jmp 0(a0,d1.w)
    code += struct.pack(">H", 0x4E71)                    # [0x0e] pad to $10
    code += struct.pack(">hhh", 0, 4, 10)               # [0x10] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_bp_word_offset_via_register_bitset_constant_base: OK")


def test_pattern_bq_indirect_pointer_read_via_register_bitset_loaded_pointer():
    """Pattern BQ: loaded pointer copied through Dn, bit-set by constant register, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">H", 0x7602)                    # [0x02] moveq #2,d3
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x04] lea $0e(pc),a0 -> $14
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x08] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0c] move.l a1,d2
    code += struct.pack(">H", 0x07C2)                    # [0x0e] bset d3,d2
    code += struct.pack(">H", 0x2242)                    # [0x10] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x12] jmp (a1)
    code += struct.pack(">I", 0x00000018)                # [0x14] dc.l $18 -> $1c
    code += struct.pack(">I", 0x00000020)                # [0x18] dc.l $20 -> $24
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1c] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x20] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x24] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    assert 0x24 in t["targets"], f"Expected $0024 in targets, got {t['targets']}"
    print("  pattern_bq_indirect_pointer_read_via_register_bitset_loaded_pointer: OK")


def test_pattern_br_word_offset_via_tas_constant_register_base():
    """Pattern BR: constant Dn TAS-updated before MOVEA/JMP."""
    code = b""
    code += struct.pack(">H", 0x7018)                    # [0x00] moveq #$18,d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">H", 0x4AC0)                    # [0x04] tas d0 -> $98
    code += struct.pack(">H", 0x2040)                    # [0x06] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x08] jmp 0(a0,d1.w)
    code += bytes(0x98 - len(code))                     # pad to $98
    code += struct.pack(">hhh", 0, 4, 10)               # [$98] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [$9e] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [$a2] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x98 in t["targets"], f"Expected $0098 in targets, got {t['targets']}"
    assert 0x9C in t["targets"], f"Expected $009c in targets, got {t['targets']}"
    assert 0xA2 in t["targets"], f"Expected $00a2 in targets, got {t['targets']}"
    print("  pattern_br_word_offset_via_tas_constant_register_base: OK")


def test_pattern_bs_indirect_pointer_read_via_tas_loaded_pointer():
    """Pattern BS: loaded pointer copied through Dn, TAS-updated, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x02] lea $0e(pc),a0 -> $12
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0a] move.l a1,d2
    code += struct.pack(">H", 0x4AC2)                    # [0x0c] tas d2
    code += struct.pack(">H", 0x2242)                    # [0x0e] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x10] jmp (a1)
    code += struct.pack(">I", 0x00000018)                # [0x12] dc.l $18 -> $98
    code += struct.pack(">I", 0x00000020)                # [0x16] dc.l $20 -> $A0
    code += bytes(0x98 - len(code))                     # pad to $98
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [$98] nop; rts
    code += bytes(0xA0 - len(code))                     # pad to $a0
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [$a0] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x98 in t["targets"], f"Expected $0098 in targets, got {t['targets']}"
    assert 0xA0 in t["targets"], f"Expected $00a0 in targets, got {t['targets']}"
    print("  pattern_bs_indirect_pointer_read_via_tas_loaded_pointer: OK")


def test_pattern_bt_word_offset_via_tst_constant_register_base():
    """Pattern BT: constant Dn TSTed before MOVEA/JMP."""
    code = b""
    code += struct.pack(">H", 0x700C)                    # [0x00] moveq #$0c,d0
    code += struct.pack(">H", 0x7200)                    # [0x02] moveq #0,d1
    code += struct.pack(">H", 0x4A80)                    # [0x04] tst.l d0
    code += struct.pack(">H", 0x2040)                    # [0x06] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x08] jmp 0(a0,d1.w)
    code += struct.pack(">hhh", 0, 4, 10)               # [0x0c] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x12] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x0C in t["targets"], f"Expected $000c in targets, got {t['targets']}"
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    print("  pattern_bt_word_offset_via_tst_constant_register_base: OK")


def test_pattern_bu_indirect_pointer_read_via_tst_loaded_pointer():
    """Pattern BU: loaded pointer copied through Dn, TSTed, then jumped."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x41FA, 0x000E)          # [0x02] lea $0e(pc),a0 -> $12
    code += struct.pack(">HH", 0x2270, 0x0000)          # [0x06] movea.l 0(a0,d0.w),a1
    code += struct.pack(">H", 0x2409)                    # [0x0a] move.l a1,d2
    code += struct.pack(">H", 0x4A82)                    # [0x0c] tst.l d2
    code += struct.pack(">H", 0x2242)                    # [0x0e] movea.l d2,a1
    code += struct.pack(">H", 0x4ED1)                    # [0x10] jmp (a1)
    code += struct.pack(">I", 0x00000018)                # [0x12] dc.l $18
    code += struct.pack(">I", 0x0000001C)                # [0x16] dc.l $1c
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1e] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x18 in t["targets"], f"Expected $0018 in targets, got {t['targets']}"
    assert 0x1C in t["targets"], f"Expected $001c in targets, got {t['targets']}"
    print("  pattern_bu_indirect_pointer_read_via_tst_loaded_pointer: OK")


def test_pattern_ap_word_offset_via_register_logical_constant_base():
    """Pattern AP: constant Dn masked by constant register source before MOVEA/JMP."""
    code = b""
    code += struct.pack(">H", 0x701F)                    # [0x00] moveq #$1f,d0
    code += struct.pack(">H", 0x741C)                    # [0x02] moveq #$1c,d2
    code += struct.pack(">H", 0x7200)                    # [0x04] moveq #0,d1
    code += struct.pack(">H", 0xC082)                    # [0x06] and.l d2,d0
    code += struct.pack(">H", 0x2040)                    # [0x08] movea.l d0,a0
    code += struct.pack(">HH", 0x4EF0, 0x1000)          # [0x0a] jmp 0(a0,d1.w)
    code += struct.pack(">HHHHHH", 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71, 0x4E71)  # [0x0e] pad to $1c
    code += struct.pack(">hhh", 0, 4, 10)               # [0x1c] dc.w table
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x22] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x26] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x20 in t["targets"], f"Expected $0020 in targets, got {t['targets']}"
    assert 0x26 in t["targets"], f"Expected $0026 in targets, got {t['targets']}"
    print("  pattern_ap_word_offset_via_register_logical_constant_base: OK")


def test_pattern_t_indirect_pointer_read_via_movea_pcdisp_and_reg_copy():
    """Pattern T: MOVEA.L d(PC),Ax; MOVEA.L Ax,Ay; MOVEA.L 0(Ay,Dn.w),Az; JMP (Az)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x207A, 0x000A)          # [0x02] movea.l 10(pc),a0 -> $0e
    code += struct.pack(">H", 0x2248)                    # [0x06] movea.l a0,a1
    code += struct.pack(">HH", 0x2671, 0x0000)          # [0x08] movea.l 0(a1,d0.w),a3
    code += struct.pack(">H", 0x4ED3)                    # [0x0c] jmp (a3)
    code += struct.pack(">I", 0x00000016)                # [0x0e] dc.l $16
    code += struct.pack(">I", 0x0000001A)                # [0x12] dc.l $1a
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "indirect_pointer_read", (
        f"Expected pattern 'indirect_pointer_read', got {t['pattern']!r}")
    assert 0x16 in t["targets"], f"Expected $0016 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_t_indirect_pointer_read_via_movea_pcdisp_and_reg_copy: OK")


def test_pattern_u_word_offset_via_movea_pcdisp_and_addq():
    """Pattern U: MOVEA.L d(PC),An; ADDQ.L #imm,An; JMP disp(An,Dn.w)."""
    code = b""
    code += struct.pack(">H", 0x7000)                    # [0x00] moveq #0,d0
    code += struct.pack(">HH", 0x207A, 0x0008)          # [0x02] movea.l 8(pc),a0 -> $0c
    code += struct.pack(">H", 0x5888)                    # [0x06] addq.l #4,a0 -> $10
    code += struct.pack(">HH", 0x4EF0, 0x0000)          # [0x08] jmp 0(a0,d0.w)
    code += struct.pack(">HH", 0x4E71, 0x4E71)          # [0x0c] pad; pad
    code += struct.pack(">hhh", 0, 4, 10)                # [0x10] dc.w 0,4,10
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x16] nop; rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)          # [0x1a] nop; rts

    result = analyze(code, propagate=True, platform=dict(_MINIMAL_PLATFORM))
    blocks = result["blocks"]
    tables = detect_jump_tables(blocks, code)
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    t = tables[0]
    assert t["pattern"] == "word_offset", (
        f"Expected pattern 'word_offset', got {t['pattern']!r}")
    assert 0x10 in t["targets"], f"Expected $0010 in targets, got {t['targets']}"
    assert 0x14 in t["targets"], f"Expected $0014 in targets, got {t['targets']}"
    assert 0x1A in t["targets"], f"Expected $001a in targets, got {t['targets']}"
    print("  pattern_u_word_offset_via_movea_pcdisp_and_addq: OK")


# ---- 12. Backward slice skips call predecessors ----------------------------

def test_backward_slice_skips_call_predecessor():
    """Backward slice must NOT use BSR predecessor's exit state for RTS.

    When a BSR block is a predecessor of an RTS block (via call
    fallthrough), the BSR's exit state has the return address on the
    stack. If the backward slice uses this state, re-propagation
    through the BSR block pushes another return address, and the RTS
    reads it -- producing a false positive.

    Layout:
        $00: BSR.W $0A   -> calls sub, fallthrough to $04
        $04: NOP
        $06: RTS         -> should NOT resolve (no outer caller)
        $0A: NOP; RTS    -> sub returns to $04

    Without the fix, backward slice resolves RTS at $04 to $04 itself
    (the BSR's pushed return address). With the fix, call predecessors
    are skipped and the RTS stays unresolved.
    """
    code = b''
    # Block 0: BSR to sub at $0A
    # BSR.W: PC=$02, disp=$08, target=$02+$08=$0A
    code += struct.pack('>HH', 0x6100, 0x0008)          # [0x00] bsr.w $0A
    # Block $04: fallthrough, NOP + RTS
    code += struct.pack('>H', 0x4E71)                    # [0x04] nop
    code += struct.pack('>H', 0x4E75)                    # [0x06] rts
    # Padding
    code += struct.pack('>H', 0x4E71)                    # [0x08] nop
    # Sub at $0A
    code += struct.pack('>H', 0x4E71)                    # [0x0a] nop
    code += struct.pack('>H', 0x4E75)                    # [0x0c] rts

    blocks, exit_states, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # Per-caller resolves sub's RTS -> $04 (correct).
    # Backward slice must NOT produce $04 again from the BSR predecessor.
    # Count how many times $04 appears in resolved results.
    count_04 = sum(1 for r in resolved if r["target"] == 0x04)
    assert count_04 <= 1, (
        f"Target $0004 resolved {count_04} times -- backward slice "
        f"should not duplicate via call predecessor")
    print("  backward_slice_skips_call_predecessor: OK")


# ---- Jump table boundary: must not scan into code ----------------------------

def test_table_scan_stops_at_call_target():
    """_scan_word_offset_table must not read past a known call target.

    Models GenAm's false positive: table at $0E9A has 22 real entries,
    but the scanner reads 29 because sub $0EC6 (a call target) has
    opcodes that decode as valid word offsets.

    Layout: 3 real table entries at $00-$04, then code at $06 that
    is a call target. The code bytes happen to decode as a valid offset.
    """
    from m68k.jump_tables import _scan_word_offset_table
    base = 0x10  # base address for offset computation

    # Build code bytes:
    # $00-$04: 3 real table entries (word offsets from base $10)
    # $06: code (LEA opcode $41EE = offset +16878, target $10 + $41EE = in range)
    data = b''
    data += struct.pack('>h', 0x20 - base)   # $00: entry 0 -> $20
    data += struct.pack('>h', 0x22 - base)   # $02: entry 1 -> $22
    data += struct.pack('>h', 0x24 - base)   # $04: entry 2 -> $24
    # $06: LEA 100(a6),a0 opcode - looks like offset $41EE from base
    data += struct.pack('>HH', 0x41EE, 0x0064)
    # Pad to make false target in range
    data += b'\x4e\x75' * 0x2100  # enough NOPs to make $41FE in range

    code_size = len(data)
    call_targets = {0x06}  # $06 is a known call target

    # Without call_targets guard: scanner reads past $06
    targets_no_guard = _scan_word_offset_table(data, 0x00, base, code_size)
    assert len(targets_no_guard) > 3, (
        f"Without guard, scanner should read past code (got {len(targets_no_guard)})")

    # With call_targets guard: scanner must stop at $06
    targets_guarded = _scan_word_offset_table(
        data, 0x00, base, code_size, call_targets=call_targets)
    assert len(targets_guarded) == 3, (
        f"With guard, scanner should stop at call target $06 "
        f"(got {len(targets_guarded)}: {[hex(t) for t in targets_guarded]})")


def test_table_scan_no_false_positives_from_opcodes():
    """Table scanner stops on invalid target, not on code block overlap.

    The scanner's existing validity checks (target < code_size,
    alignment) are the primary guard against reading into code.
    call_targets provides an additional stop for subroutine boundaries.
    """
    from m68k.jump_tables import _scan_word_offset_table
    base = 0x10

    # 3 valid entries, then a word that produces an odd target (invalid)
    data = b''
    data += struct.pack('>h', 0x20 - base)   # $00: entry 0 -> $20
    data += struct.pack('>h', 0x22 - base)   # $02: entry 1 -> $22
    data += struct.pack('>h', 0x24 - base)   # $04: entry 2 -> $24
    data += struct.pack('>h', 0x03)          # $06: odd target -> stops scan
    data += b'\x00' * 0x30

    targets = _scan_word_offset_table(data, 0x00, base, len(data))
    assert len(targets) == 3, (
        f"Should stop at odd target, got {len(targets)}")


def test_scan_inline_dispatch_stops_quietly_on_decode_error():
    code = bytes.fromhex("6002ffff")

    targets, end_pos = _scan_inline_dispatch(code, 0, len(code), max_entries=4)

    assert targets == []
    assert end_pos == 2


# ---- Inline data skip pattern ------------------------------------------------

def test_inline_data_skip():
    """BSR to sub that pops return addr and jumps past inline data.

    Pattern:
        bsr.w   skip_sub        ; pushes return addr (= addr of inline data)
        dc.w    $1234           ; inline data (skipped)
        moveq   #42,d0          ; execution resumes here
        rts
    skip_sub:
        movea.l (sp)+,a0        ; pop return addr into A0
        jmp     2(a0)           ; jump past 2-byte inline data

    Per-caller resolution should resolve jmp 2(a0) to the instruction
    after the inline data word, because the caller's pushed return address
    is concrete and the callee pops it.
    """
    code = b''
    # $00: bsr.w $0A  (push $04, jump to skip_sub)
    code += struct.pack('>HH', 0x6100, 0x0008)
    # $04: dc.w $1234  (inline data -- NOT an instruction)
    code += struct.pack('>H', 0x1234)
    # $06: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $08: rts
    code += struct.pack('>H', 0x4E75)
    # skip_sub at $0A:
    # $0A: movea.l (sp)+,a0
    code += struct.pack('>H', 0x205F)
    # $0C: jmp 2(a0)
    code += struct.pack('>HH', 0x4EE8, 0x0002)

    blocks, exit_states, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)

    # The jmp 2(a0) should resolve to $06 (return addr $04 + 2)
    assert 0x06 in targets, (
        f"Expected $0006 from jmp 2(a0) with return addr $04, "
        f"got {targets}")
    print("  inline_data_skip: OK")


def test_inline_data_skip_multiple_callers():
    """Multiple callers to inline-data-skip sub, each with different data.

    caller_a:
        bsr.w   skip_sub
        dc.w    $AAAA           ; caller A's inline data
        moveq   #1,d0
        rts
    caller_b:
        bsr.w   skip_sub
        dc.w    $BBBB           ; caller B's inline data
        moveq   #2,d0
        rts
    main:
        bsr.w   caller_a
        bsr.w   caller_b
        rts
    skip_sub:
        movea.l (sp)+,a0
        jmp     2(a0)

    Per-caller should resolve both return addresses.
    """
    code = b''
    # main at $00:
    # $00: bsr.w caller_a ($0C)
    code += struct.pack('>HH', 0x6100, 0x000A)
    # $04: bsr.w caller_b ($16)
    code += struct.pack('>HH', 0x6100, 0x0010)
    # $08: rts
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>H', 0x4E71)
    # caller_a at $0C:
    # $0C: bsr.w skip_sub ($20)
    code += struct.pack('>HH', 0x6100, 0x0012)
    # $10: dc.w $AAAA
    code += struct.pack('>H', 0xAAAA)
    # $12: moveq #1,d0
    code += struct.pack('>H', 0x7001)
    # $14: rts
    code += struct.pack('>H', 0x4E75)
    # caller_b at $16:
    # $16: bsr.w skip_sub ($20)
    code += struct.pack('>HH', 0x6100, 0x0008)
    # $1A: dc.w $BBBB
    code += struct.pack('>H', 0xBBBB)
    # $1C: moveq #2,d0
    code += struct.pack('>H', 0x7201)
    # $1E: rts
    code += struct.pack('>H', 0x4E75)
    # skip_sub at $20:
    # $20: movea.l (sp)+,a0
    code += struct.pack('>H', 0x205F)
    # $22: jmp 2(a0)
    code += struct.pack('>HH', 0x4EE8, 0x0002)

    blocks, exit_states, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)

    # Should resolve both $12 (caller_a's data skip) and $1C (caller_b's)
    assert 0x12 in targets, (
        f"Expected $0012 from caller_a's inline skip, got {targets}")
    assert 0x1C in targets, (
        f"Expected $001C from caller_b's inline skip, got {targets}")


# ---- Nested callee return value resolution ----------------------------------

def test_per_caller_resolves_through_nested_callee():
    """Per-caller resolves dispatch when register comes from nested callee.

    Pattern (models GenAm $3A6C -> $3ED6 -> jsr (a0)):
        main:
            moveq   #$1C,d0         ; input for sub_inner
            bsr.w   sub_outer
            rts
        sub_outer:
            bsr.w   sub_inner       ; sub_inner sets A0 from D0
            jsr     (a0)            ; dispatch -- should resolve
            rts
        sub_inner:
            movea.l d0,a0           ; A0 = D0 (input-dependent)
            rts
        target ($1C):
            rts

    Static summary for sub_inner says A0 is clobbered (input-dependent).
    Per-caller should re-execute sub_inner with D0=$1C to get A0=$1C.
    """
    code = b''
    # main at $00:
    # $00: moveq #$1C,d0
    code += struct.pack('>H', 0x701C)
    # $02: bsr.w sub_outer ($08)
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $06: rts
    code += struct.pack('>H', 0x4E75)
    # sub_outer at $08:
    # $08: bsr.w sub_inner ($10)
    code += struct.pack('>HH', 0x6100, 0x0006)
    # $0C: jsr (a0) -- should resolve to $1C
    code += struct.pack('>H', 0x4E90)
    # $0E: rts
    code += struct.pack('>H', 0x4E75)
    # sub_inner at $10:
    # $10: movea.l d0,a0
    code += struct.pack('>H', 0x2040)
    # $12: rts
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>H', 0x4E71)
    code += struct.pack('>H', 0x4E71)
    code += struct.pack('>H', 0x4E71)
    code += struct.pack('>H', 0x4E71)
    # target at $1C:
    code += struct.pack('>H', 0x4E75)

    blocks, exit_states, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)

    assert 0x1C in targets, (
        f"Expected $001C from jsr (a0) via nested callee, got {targets}")


def test_per_caller_nested_multiple_callers():
    """Multiple callers pass different values through nested callee.

    caller_a passes D0=$20, caller_b passes D0=$24.
    sub_outer calls sub_inner (A0=D0), then jsr (a0).
    Both targets should resolve.
    """
    code = b''
    # main at $00:
    # $00: moveq #$20,d0
    code += struct.pack('>H', 0x7020)
    # $02: bsr.w sub_outer ($0E)
    code += struct.pack('>HH', 0x6100, 0x000A)
    # $06: moveq #$24,d0
    code += struct.pack('>H', 0x7024)
    # $08: bsr.w sub_outer ($0E)
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $0C: rts
    code += struct.pack('>H', 0x4E75)
    # sub_outer at $0E:
    # $0E: bsr.w sub_inner ($16)
    code += struct.pack('>HH', 0x6100, 0x0006)
    # $12: jsr (a0)
    code += struct.pack('>H', 0x4E90)
    # $14: rts
    code += struct.pack('>H', 0x4E75)
    # sub_inner at $16:
    # $16: movea.l d0,a0
    code += struct.pack('>H', 0x2040)
    # $18: rts
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>H', 0x4E71)
    code += struct.pack('>H', 0x4E71)
    code += struct.pack('>H', 0x4E71)
    # target_a at $20:
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>H', 0x4E71)
    # target_b at $24:
    code += struct.pack('>H', 0x4E75)

    blocks, exit_states, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)

    assert 0x20 in targets, (
        f"Expected $0020 from caller_a (D0=$20), got {targets}")
    assert 0x24 in targets, (
        f"Expected $0024 from caller_b (D0=$24), got {targets}")


# ---- Branch forking: per-exit resolution ------------------------------------

def test_branch_forking_resolves_both_paths():
    """Callee branches on unknown input, each path produces different A0.

    sub_outer calls sub_inner with unknown D0.
    sub_inner: lea base(pc),a0; tst.b d0; beq path_b;
               addq.l #4,a0; rts   -- path A: a0 = base+4
    path_b:    addq.l #8,a0; rts   -- path B: a0 = base+8
    sub_outer: jsr (a0)            -- should resolve BOTH targets

    The current inline summary joins both RTS exits (a0 unknown).
    With per-exit resolution, each RTS produces a separate a0 value.
    """
    code = b''
    # main at $00: bsr.w sub_outer ($08)
    code += struct.pack('>HH', 0x6100, 0x0006)
    # $04: rts
    code += struct.pack('>H', 0x4E75)
    # $06: nop (padding)
    code += struct.pack('>H', 0x4E71)
    # sub_outer at $08: bsr.w sub_inner ($10)
    code += struct.pack('>HH', 0x6100, 0x0006)
    # $0C: jsr (a0)
    code += struct.pack('>H', 0x4E90)
    # $0E: rts
    code += struct.pack('>H', 0x4E75)
    # sub_inner at $10: lea $12(pc),a0 -> a0 = $12 + $12 = $24
    code += struct.pack('>HH', 0x41FA, 0x0012)
    # $14: tst.b d0
    code += struct.pack('>H', 0x4A00)
    # $16: beq.s $1C (path B) -- disp = $1C - $18 = 4
    code += struct.pack('>H', 0x6704)
    # $18: addq.l #4,a0 (path A: a0 = $24 + 4 = $28)
    code += struct.pack('>H', 0x5888)
    # $1A: rts
    code += struct.pack('>H', 0x4E75)
    # $1C: addq.l #8,a0 (path B: a0 = $24 + 8 = $2C)
    code += struct.pack('>H', 0x5088)
    # $1E: rts
    code += struct.pack('>H', 0x4E75)
    # padding to $28
    code += struct.pack('>HHHH', 0x4E71, 0x4E71, 0x4E71, 0x4E71)
    # target_a at $28: rts
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>H', 0x4E71)
    # target_b at $2C: rts
    code += struct.pack('>H', 0x4E75)

    blocks, exit_states, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)

    assert 0x28 in targets, (
        f"Expected $0028 (path A: base+4) from branch forking, "
        f"got {targets}")
    assert 0x2C in targets, (
        f"Expected $002C (path B: base+8) from branch forking, "
        f"got {targets}")


def test_branch_forking_single_exit_no_fork():
    """Callee with one RTS exit doesn't trigger forking.

    sub_inner has a single exit path. The joined summary already
    captures the concrete value. No per-exit forking needed.
    """
    code = b''
    # $00: bsr.w $08
    code += struct.pack('>HH', 0x6100, 0x0006)
    # $04: jsr (a0)
    code += struct.pack('>H', 0x4E90)
    # $06: rts
    code += struct.pack('>H', 0x4E75)
    # sub_inner at $08: lea $10(pc),a0 -> a0 = $0A + 6 = $10
    code += struct.pack('>HH', 0x41FA, 0x0006)
    # $0C: rts (single exit)
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>H', 0x4E71)
    # target at $10: rts
    code += struct.pack('>H', 0x4E75)

    blocks, exit_states, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # Should resolve via produced-value summary, not forking
    assert 0x10 in targets, (
        f"Expected $0010 from single-exit callee, got {targets}")


def test_branch_forking_unknown_inputs_no_result():
    """Forking with unknown inputs produces no concrete targets.

    All callers have unknown D0. The callee branches on D0.
    Both paths produce concrete A0, but the dispatch sub's callers
    also have unknown state. No resolution expected.
    """
    code = b''
    # $00: bsr.w $06 (sub_outer, D0 unknown at entry)
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $04: rts
    code += struct.pack('>H', 0x4E75)
    # sub_outer at $06: bsr.w $0E (sub_inner)
    code += struct.pack('>HH', 0x6100, 0x0006)
    # $0A: jsr (a0)
    code += struct.pack('>H', 0x4E90)
    # $0C: rts
    code += struct.pack('>H', 0x4E75)
    # sub_inner at $0E: movea.l d0,a0 (input-dependent, single path)
    code += struct.pack('>H', 0x2040)
    # $10: rts
    code += struct.pack('>H', 0x4E75)

    blocks, exit_states, resolved = _analyze_and_resolve(code)
    targets = _resolved_targets(resolved)
    # D0 is unknown -> A0 is unknown -> jsr (a0) can't resolve
    # The only resolved targets should be RTS return addresses
    assert all(t <= 0x12 for t in targets), (
        f"Expected no dispatch targets (unknown inputs), got {targets}")


def test_resolve_per_caller_caches_summarized_propagation(monkeypatch):
    caller = BasicBlock(start=0x00, end=0x02, instructions=[], successors=[0x10],
                        predecessors=[], xrefs=[XRef(src=0x00, dst=0x10, type="call")])
    sub = BasicBlock(start=0x10, end=0x12,
                     instructions=[SimpleNamespace(offset=0x10)],
                     successors=[0x12, 0x14], predecessors=[0x00],
                     xrefs=[XRef(src=0x10, dst=0x30, type="call")])
    unres_a = BasicBlock(start=0x12, end=0x14,
                         instructions=[SimpleNamespace(offset=0x12)],
                         successors=[], predecessors=[0x10], xrefs=[])
    unres_b = BasicBlock(start=0x14, end=0x16,
                         instructions=[SimpleNamespace(offset=0x14)],
                         successors=[], predecessors=[0x10], xrefs=[])
    callee = BasicBlock(start=0x30, end=0x32, instructions=[],
                        successors=[], predecessors=[], xrefs=[])
    blocks = {0x00: caller, 0x10: sub, 0x12: unres_a, 0x14: unres_b, 0x30: callee}

    cpu = CPUState()
    mem = AbstractMemory()
    exit_states = {0x00: (cpu, mem)}

    calls = {"count": 0}

    def _fake_propagate_states(*args, **kwargs):
        calls["count"] += 1
        return {0x12: (CPUState(), AbstractMemory()), 0x14: (CPUState(), AbstractMemory())}

    monkeypatch.setattr("m68k.indirect_analysis.propagate_states", _fake_propagate_states)
    monkeypatch.setattr("m68k.indirect_analysis.indirect_core._find_unresolved",
                        lambda blocks, exit_states, code_size: [(0x12, "jump"), (0x14, "jump")])
    monkeypatch.setattr("m68k.indirect_analysis.indirect_core.decode_jump_ea",
                        lambda inst: (None, None))
    monkeypatch.setattr("m68k.indirect_analysis.indirect_core._needed_registers",
                        lambda operand, unres_type: [])
    monkeypatch.setattr("m68k.indirect_analysis.indirect_core._try_resolve_block",
                        lambda addr, unres_type, blocks, cpu, mem, code_size: 0x40 + addr)
    monkeypatch.setattr("m68k.indirect_analysis.subroutine_summary.find_sub_blocks",
                        lambda entry, blocks, call_targets: {0x10, 0x12, 0x14})
    monkeypatch.setattr("m68k.indirect_analysis.subroutine_summary.restore_base_reg",
                        lambda cpu, platform: cpu)
    monkeypatch.setattr("m68k.indirect_analysis.subroutine_summary._inline_summary",
                        lambda callee_entry, blocks, call_targets, exit_states: {
                            "preserved_d": set(),
                            "preserved_a": set(),
                            "produced_d": {0: 1},
                            "produced_a": {},
                            "sp_delta": 0,
                        })

    resolved = resolve_per_caller(blocks, exit_states, b"", 0x100, platform={"scratch_regs": []})

    assert sorted(r["target"] for r in resolved) == [0x52, 0x54]
    assert calls["count"] == 2


