"""Test instruction effect handlers in the executor.

Validates that each compute_formula.op handler produces correct
abstract state changes. Each test constructs a minimal code sequence,
runs the executor with propagation, and checks the exit state.

These tests exercise the KB-driven dispatch in _apply_instruction:
binary ops (add/sub/and/or/xor), unary ops (neg/not/swap/ext),
assign (move/moveq/clr), LEA, PEA, MOVEM, EXG, and the
compare-no-write path.

Also tests subroutine summaries: register preservation through
push/pop patterns, SP delta computation, and how summaries interact
with the propagation engine.
"""

import struct
import pytest

from m68k.m68k_executor import (analyze, _concrete, _unknown, _symbolic,
                                CPUState, AbstractMemory)


def _run(code):
    """Analyze code with propagation, return exit state of block 0."""
    result = analyze(code, propagate=True)
    cpu, mem = result["exit_states"][0]
    return cpu, mem


# ── Binary ops: add, sub, and, or, xor ──────────────────────────────

def test_add_reg_reg():
    """ADD.W D1,D0 with known values."""
    code = struct.pack('>HHH', 0x7005, 0x720A, 0xD041)  # moveq#5, moveq#10, add.w d1,d0
    code += struct.pack('>H', 0x4E75)  # rts
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 15

def test_sub_reg_reg():
    """SUB.W D1,D0: 20 - 5 = 15."""
    code = struct.pack('>HHH', 0x7014, 0x7205, 0x9041)  # moveq#20, moveq#5, sub.w d1,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 15

def test_and_reg_reg():
    """AND.W D1,D0: 0xFF & 0x0F = 0x0F."""
    code = b''
    code += struct.pack('>HH', 0x303C, 0x00FF)  # move.w #$FF,d0
    code += struct.pack('>HH', 0x323C, 0x000F)  # move.w #$0F,d1
    code += struct.pack('>H', 0xC041)            # and.w d1,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 0x0F

def test_or_reg_reg():
    """OR.W D1,D0: 0xF0 | 0x0F = 0xFF."""
    code = b''
    code += struct.pack('>HH', 0x303C, 0x00F0)  # move.w #$F0,d0
    code += struct.pack('>HH', 0x323C, 0x000F)  # move.w #$0F,d1
    code += struct.pack('>H', 0x8041)            # or.w d1,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 0xFF

def test_eor_reg_reg():
    """EOR.W D1,D0: 0xFF ^ 0x0F = 0xF0."""
    code = b''
    code += struct.pack('>HH', 0x303C, 0x00FF)  # move.w #$FF,d0
    code += struct.pack('>H', 0x720F)            # moveq #$0F,d1
    # EOR.W D1,D0: 1011 001 101 000 000 = $B340
    code += struct.pack('>H', 0xB340)            # eor.w d1,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 0xF0

def test_addi():
    """ADDI.W #$10,D0."""
    code = struct.pack('>H', 0x7005)             # moveq #5,d0
    code += struct.pack('>HHH', 0x0640, 0x0010, 0x4E75)  # addi.w #$10,d0; rts
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 0x15

def test_subi():
    """SUBI.W #3,D0."""
    code = struct.pack('>H', 0x700A)             # moveq #10,d0
    code += struct.pack('>HHH', 0x0440, 0x0003, 0x4E75)  # subi.w #3,d0; rts
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 7

def test_addq():
    """ADDQ.L #4,A0."""
    # lea 6(pc),a0 at offset 0: a0 = 0 + 2 + 6 = 8
    code = struct.pack('>HH', 0x41FA, 0x0006)   # lea 6(pc),a0 -> a0=$08
    code += struct.pack('>H', 0x5888)            # addq.l #4,a0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.a[0].concrete == 8 + 4

def test_cmp_no_write():
    """CMP.W D1,D0 should NOT modify D0."""
    code = struct.pack('>HHH', 0x7005, 0x720A, 0xB041)  # moveq#5, moveq#10, cmp.w d1,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 5  # unchanged
    assert cpu.d[1].concrete == 10  # unchanged


# ── Unary ops ────────────────────────────────────────────────────────

def test_neg():
    """NEG.L D0: 0 - 5 = -5."""
    code = struct.pack('>HH', 0x7005, 0x4480)   # moveq #5,d0; neg.l d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == (-5) & 0xFFFFFFFF

def test_not():
    """NOT.L D0: ~0x0000000F = 0xFFFFFFF0."""
    code = struct.pack('>HH', 0x700F, 0x4680)   # moveq #$F,d0; not.l d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 0xFFFFFFF0


# ── Assign: MOVE, MOVEQ, CLR ────────────────────────────────────────

def test_moveq():
    """MOVEQ #42,D0."""
    code = struct.pack('>HH', 0x702A, 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 42

def test_moveq_negative():
    """MOVEQ #-1,D0 -> sign-extended to $FFFFFFFF."""
    code = struct.pack('>HH', 0x70FF, 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 0xFFFFFFFF

def test_clr():
    """CLR.L D0 after MOVEQ."""
    code = struct.pack('>HHH', 0x702A, 0x4280, 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 0

def test_move_reg_reg():
    """MOVE.L D0,D1."""
    code = struct.pack('>HHH', 0x702A, 0x2200, 0x4E75)  # moveq#42, move.l d0,d1, rts
    cpu, _ = _run(code)
    assert cpu.d[1].concrete == 42


# ── LEA ──────────────────────────────────────────────────────────────

def test_lea_pcdisp():
    """LEA d(PC),A0 computes address, not memory value."""
    # lea $10(pc),a0 at offset 0: a0 = 0 + 2 + $10 = $12
    code = struct.pack('>HH', 0x41FA, 0x0010)
    code += struct.pack('>H', 0x4E75)
    code += b'\x00' * 16
    cpu, _ = _run(code)
    assert cpu.a[0].concrete == 0x12


# ── SWAP ─────────────────────────────────────────────────────────────

def test_swap():
    """SWAP D0: exchange upper and lower words.

    SWAP's encoding has a REGISTER field but no MODE field, so the
    operand decoder produces ea_op=None. The SWAP handler must extract
    the register directly from the encoding.
    """
    code = b''
    code += struct.pack('>HI', 0x203C, 0x00010002)  # move.l #$00010002,d0
    code += struct.pack('>H', 0x4840)                # swap d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 0x00020001


# ── EXT ──────────────────────────────────────────────────────────────

def test_ext_w():
    """EXT.W D0: sign-extend byte to word."""
    code = struct.pack('>H', 0x70FF)       # moveq #-1,d0 (=$FFFFFFFF)
    code += struct.pack('>HH', 0x7000 | 0x80, 0x4880)  # moveq #$80,d0; ext.w d0
    # Actually moveq #-128 = $FFFFFF80. ext.w should give $FF80 in lower word.
    # Let me use a clearer value.
    code = b''
    code += struct.pack('>HI', 0x203C, 0x0000FF80)  # move.l #$0000FF80,d0
    code += struct.pack('>H', 0x4880)                # ext.w d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    # ext.w sign-extends byte $80 to word $FF80, upper word unchanged
    assert cpu.d[0].concrete == 0x0000FF80


# ── EXG ──────────────────────────────────────────────────────────────

def test_exg_data():
    """EXG D0,D1."""
    code = struct.pack('>HHH', 0x700A, 0x7214, 0xC141)  # moveq#10, moveq#20, exg d0,d1
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].concrete == 20
    assert cpu.d[1].concrete == 10


# ── ADDA/SUBA (source sign-extend) ──────────────────────────────────

def test_adda_w():
    """ADDA.W D0,A0: source word sign-extended to long before add."""
    code = b''
    code += struct.pack('>HH', 0x41FA, 0x0010)  # lea $10(pc),a0 -> a0=$12
    code += struct.pack('>H', 0x70FC)            # moveq #-4,d0
    code += struct.pack('>H', 0xD0C0)            # adda.w d0,a0
    code += struct.pack('>H', 0x4E75)
    code += b'\x00' * 16
    cpu, _ = _run(code)
    # a0 = $12 + sign_extend_w(-4) = $12 + (-4) = $0E
    assert cpu.a[0].concrete == 0x0E


# ── Rotate: should compute via KB ────────────────────────────────────

def test_rol_immediate():
    """ROL.L #2,D0: rotate left 2 bits."""
    code = b''
    code += struct.pack('>HI', 0x203C, 0x80000001)  # move.l #$80000001,d0
    # ROL.L #2,D0: 1110 010 1 10 1 11 000 = $E598
    code += struct.pack('>H', 0xE598)                # rol.l #2,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "ROL should produce a concrete result"
    assert cpu.d[0].concrete == 0x00000006


def test_ror_immediate():
    """ROR.L #1,D0: rotate right 1 bit."""
    code = b''
    code += struct.pack('>H', 0x7001)                # moveq #1,d0
    # ROR.L #1,D0: 1110 001 0 10 1 11 000 = $E298
    code += struct.pack('>H', 0xE298)                # ror.l #1,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "ROR should produce a concrete result"
    assert cpu.d[0].concrete == 0x80000000


# ── Divide: should compute via KB ────────────────────────────────────

def test_divu_w():
    """DIVU.W D1,D0: 35 / 7 = 5 remainder 0."""
    code = b''
    code += struct.pack('>H', 0x7023)                # moveq #35,d0
    code += struct.pack('>H', 0x7207)                # moveq #7,d1
    # DIVU.W D1,D0: 1000 000 011 000 001 = $80C1
    code += struct.pack('>H', 0x80C1)                # divu.w d1,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "DIVU should produce a concrete result"
    assert cpu.d[0].concrete == 5, f"35/7=5, got {cpu.d[0].concrete}"


# ── Unknown operand: invalidate path ─────────────────────────────────

def test_shift_unknown_count_invalidates():
    """LSL with unknown count should invalidate the destination."""
    code = b''
    code += struct.pack('>H', 0x7005)                # moveq #5,d0
    # D1 is unknown (not set), LSL.W D1,D0
    # 1110 001 1 01 1 00 000 = $E368
    code += struct.pack('>H', 0xE368)                # lsl.w d1,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert not cpu.d[0].is_known, (
        f"LSL with unknown count should invalidate, got {cpu.d[0]}")


def test_multiply_unknown_operand_invalidates():
    """MULU with unknown source should invalidate the destination."""
    code = b''
    code += struct.pack('>H', 0x7005)                # moveq #5,d0
    # D1 unknown, MULU.W D1,D0: $C0C1
    code += struct.pack('>H', 0xC0C1)                # mulu.w d1,d0
    code += struct.pack('>H', 0x4E75)
    cpu, _ = _run(code)
    assert not cpu.d[0].is_known, (
        f"MULU with unknown source should invalidate, got {cpu.d[0]}")


# ── Register preservation through calls ──────────────────────────────

def test_register_preserved_through_push_pop_call():
    """Register saved/restored around a call should survive on fallthrough.

    Pattern:
        move.l  a5,-(sp)       ; save A5
        bsr.w   sub            ; call (may clobber A5)
        movea.l (sp)+,a5       ; restore A5
        jmp     d(a5)          ; dispatch using preserved A5

    The subroutine summary should detect that A5 is NOT in the
    scratch register set (it was pushed before the call and popped
    after). On the fallthrough path, A5 should retain its pre-call
    value, enabling the dispatch to resolve.

    This models the Amiga pattern of saving registers around ExecBase
    calls where the calling convention clobbers address registers.
    """
    code = b''
    # Entry: set A5 to a known value via LEA
    # lea $30(pc),a5 -> a5 = $00+2+$30 = $32
    code += struct.pack('>HH', 0x4BFA, 0x0030)          # [0x00] lea $30(pc),a5
    # Save A5: move.l a5,-(sp)
    code += struct.pack('>H', 0x2F0D)                    # [0x04] move.l a5,-(sp)
    # BSR to sub (sub may clobber a5 -- it's a scratch reg)
    # bsr.w $10  (PC=$08, disp=$08, target=$08+$08=$10)
    code += struct.pack('>HH', 0x6100, 0x0008)          # [0x06] bsr.w $10
    # Restore A5: movea.l (sp)+,a5
    code += struct.pack('>H', 0x2A5F)                    # [0x0a] movea.l (sp)+,a5
    # Use A5: jmp 4(a5) -> target should be $32 + 4 = $36
    code += struct.pack('>HH', 0x4EED, 0x0004)          # [0x0c] jmp 4(a5)
    # Sub at $10: just RTS (clobbers nothing, but scratch invalidation
    # would kill A5 if it's in the scratch set)
    code += struct.pack('>H', 0x4E75)                    # [0x10] rts
    # Padding to $32
    code += b'\x4e\x71' * 16                             # [0x12..$31] nop
    # Data at $32
    code += b'\x4e\x71' * 4                              # [0x32..$39] nop
    # Target at $36
    code += struct.pack('>H', 0x4E75)                    # [0x36] rts (target)

    platform = {
        "scratch_regs": [("an", 5)],  # A5 is a scratch register
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)
    blocks = result["blocks"]
    exit_states = result.get("exit_states", {})

    # The block at $0a (restore + dispatch) should have A5 = $32
    # because the push/pop preserved it across the call.
    # Without preservation: A5 would be unknown (scratch-clobbered).
    from m68k.indirect_analysis import resolve_indirect_targets
    resolved = resolve_indirect_targets(blocks, exit_states, len(code))
    targets = sorted(r["target"] for r in resolved)
    assert 0x36 in targets, (
        f"Expected $0036 from jmp 4(a5) with preserved a5=$32, "
        f"got {targets}")


def test_library_base_survives_push_pop_exec_call():
    """Library base register preserved through push/pop around call.

    Pattern (common in Amiga code):
        lea     table(pc),a5     ; a5 = concrete code address
        move.l  a5,-(sp)         ; save a5
        bsr.w   sub              ; call (a5 in scratch set, clobbered)
        movea.l (sp)+,a5         ; restore a5
        movea.l (a5),a0          ; load function pointer from table
        jsr     (a0)             ; dispatch using value from preserved a5

    After the call + restore, A5 should have its original concrete
    value, enabling the memory read and dispatch to resolve.
    """
    code = b''
    # lea $20(pc),a5 -> a5 = $00+2+$20 = $22 (table)
    code += struct.pack('>HH', 0x4BFA, 0x0020)          # [0x00] lea $20(pc),a5
    # Save A5: move.l a5,-(sp)
    code += struct.pack('>H', 0x2F0D)                    # [0x04] move.l a5,-(sp)
    # BSR to sub at $10
    # bsr.w: PC=$08, disp=$08, target=$08+$08=$10
    code += struct.pack('>HH', 0x6100, 0x0008)          # [0x06] bsr.w $10
    # Restore A5: movea.l (sp)+,a5
    code += struct.pack('>H', 0x2A5F)                    # [0x0a] movea.l (sp)+,a5
    # Load fn ptr: movea.l (a5),a0 -> a0 = long at $22
    code += struct.pack('>H', 0x2055)                    # [0x0c] movea.l (a5),a0
    # Dispatch: jsr (a0)
    code += struct.pack('>H', 0x4E90)                    # [0x0e] jsr (a0)
    # Sub at $10: just RTS
    code += struct.pack('>H', 0x4E75)                    # [0x10] rts
    # Padding
    code += b'\x4e\x71' * 8                              # [0x12..$21] nop
    # Table at $22: longword pointer to handler at $2a
    code += struct.pack('>I', 0x0000002A)                # [0x22] -> $2a
    # Padding
    code += struct.pack('>HH', 0x4E71, 0x4E71)          # [0x26..$29] nop
    # Handler at $2a
    code += struct.pack('>H', 0x4E75)                    # [0x2a] rts

    platform = {
        "scratch_regs": [("an", 5), ("an", 0), ("dn", 0)],
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)
    blocks = result["blocks"]
    exit_states = result.get("exit_states", {})

    from m68k.indirect_analysis import resolve_indirect_targets
    resolved = resolve_indirect_targets(blocks, exit_states, len(code))
    targets = sorted(r["target"] for r in resolved)
    assert 0x2a in targets, (
        f"Expected $002a from jsr (a0) where a0 loaded via preserved a5, "
        f"got {targets}")


def test_base_register_survives_merge():
    """App base register restored after merge kills it.

    When multiple paths converge and one has the base register unknown
    (e.g. after a call that clobbers it), the conservative join makes
    the register unknown. Since the app base register is set once in
    init and never changes, the propagator should restore it after
    any merge that loses it.

    Layout:
        $00: lea data(pc),a6   ; a6 = base (concrete)
        $04: tst.b d0
        $06: beq.s $0A         ; path A: a6 survives
        $08: movea.l d7,a6     ; path B: a6 clobbered
        $0A: (merge)           ; a6 should be restored to base
        $0C: jsr -6(a6)        ; should resolve to base + (-6)
    """
    code = b''
    # lea $30(pc),a6 -> a6 = $00+2+$30 = $32
    code += struct.pack('>HH', 0x4DFA, 0x0030)          # [0x00] lea $30(pc),a6
    code += struct.pack('>H', 0x4A00)                    # [0x04] tst.b d0
    code += struct.pack('>H', 0x6702)                    # [0x06] beq.s $0A
    # Clobber path: movea.l d7,a6
    code += struct.pack('>H', 0x2C47)                    # [0x08] movea.l d7,a6
    # Merge at $0A: dispatch
    code += struct.pack('>HH', 0x4EAE, 0xFFFA)          # [0x0a] jsr -6(a6)
    code += struct.pack('>H', 0x4E75)                    # [0x0e] rts
    # Padding
    code += b'\x4e\x71' * 18                             # [0x10..$31] nop
    # Target at $32 + (-6) = $2c
    code += b'\x4e\x71' * 2                              # [0x32..$35] pad
    # But we need target at $2c
    # Recalculate: a6=$32, jsr -6(a6) -> $32-6 = $2c
    # Put RTS at $2c
    # Code is: $00-$0f = instructions, $10-$31 = nop padding
    # $2c is at offset $2c = 44. We have 16 bytes of code ($00-$0f)
    # then nop padding. Position $2c is within the nop padding.
    # Let's rebuild with exact layout:

    code = b''
    # $00: lea $30(pc),a6 -> a6 = $32
    code += struct.pack('>HH', 0x4DFA, 0x0030)          # [0x00]
    code += struct.pack('>H', 0x4A00)                    # [0x04] tst.b d0
    code += struct.pack('>H', 0x6702)                    # [0x06] beq.s $0A
    code += struct.pack('>H', 0x2C47)                    # [0x08] movea.l d7,a6
    # $0A: merge + dispatch
    code += struct.pack('>HH', 0x4EAE, 0xFFFA)          # [0x0a] jsr -6(a6)
    code += struct.pack('>H', 0x4E75)                    # [0x0e] rts
    # Pad to $2c (target = $32 - 6 = $2c)
    code += b'\x4e\x71' * 15                             # [0x10..$2b]
    code += struct.pack('>H', 0x4E75)                    # [0x2c] rts (target!)
    code += b'\x4e\x71' * 3                              # pad

    platform = {
        "initial_base_reg": (6, 0x32),  # A6 is always $32
        "scratch_regs": [],
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)
    blocks = result["blocks"]
    exit_states = result.get("exit_states", {})

    from m68k.indirect_analysis import resolve_indirect_targets
    resolved = resolve_indirect_targets(blocks, exit_states, len(code))
    targets = sorted(r["target"] for r in resolved)
    assert 0x2c in targets, (
        f"Expected $002c from jsr -6(a6) with base a6=$32 restored "
        f"after merge, got {targets}")


# ── Shift/rotate: currently invalidated, should compute ──────────────

def test_lsl_immediate():
    """LSL.W #2,D0: 5 << 2 = 20."""
    code = b''
    code += struct.pack('>H', 0x7005)       # moveq #5,d0
    # LSL.W #2,D0: 1110 010 1 01 0 00 000 = $E548
    code += struct.pack('>H', 0xE548)       # lsl.w #2,d0
    code += struct.pack('>H', 0x4E75)       # rts
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "LSL should produce a concrete result"
    assert cpu.d[0].concrete == 20, f"5 << 2 = 20, got {cpu.d[0].concrete}"


def test_lsr_immediate():
    """LSR.L #3,D0: 40 >> 3 = 5."""
    code = b''
    code += struct.pack('>H', 0x7028)       # moveq #40,d0
    # LSR.L #3,D0: 1110 011 0 10 0 01 000 = $E688
    code += struct.pack('>H', 0xE688)       # lsr.l #3,d0
    code += struct.pack('>H', 0x4E75)       # rts
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "LSR should produce a concrete result"
    assert cpu.d[0].concrete == 5


def test_asr_immediate():
    """ASR.L #1,D0: -4 >> 1 = -2 (arithmetic, sign-preserving)."""
    code = b''
    code += struct.pack('>H', 0x70FC)       # moveq #-4,d0
    # ASR.L #1,D0: 1110 001 0 10 0 00 000 = $E280
    code += struct.pack('>H', 0xE280)       # asr.l #1,d0
    code += struct.pack('>H', 0x4E75)       # rts
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "ASR should produce a concrete result"
    assert cpu.d[0].concrete == (-2) & 0xFFFFFFFF


def test_asl_immediate():
    """ASL.W #1,D0: 3 << 1 = 6."""
    code = b''
    code += struct.pack('>H', 0x7003)       # moveq #3,d0
    # ASL.W #1,D0: 1110 001 1 01 1 00 000 = $E340
    code += struct.pack('>H', 0xE340)       # asl.w #1,d0
    code += struct.pack('>H', 0x4E75)       # rts
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "ASL should produce a concrete result"
    assert cpu.d[0].concrete == 6


# ── Multiply: currently invalidated, should compute ──────────────────

def test_mulu_w():
    """MULU.W D1,D0: 5 * 7 = 35 (unsigned word multiply -> long result)."""
    code = b''
    code += struct.pack('>H', 0x7005)       # moveq #5,d0
    code += struct.pack('>H', 0x7207)       # moveq #7,d1
    # MULU.W D1,D0: 1100 000 011 000 001 = $C0C1
    code += struct.pack('>H', 0xC0C1)       # mulu.w d1,d0
    code += struct.pack('>H', 0x4E75)       # rts
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "MULU should produce a concrete result"
    assert cpu.d[0].concrete == 35


def test_muls_w():
    """MULS.W D1,D0: -3 * 4 = -12 (signed word multiply -> long result)."""
    code = b''
    code += struct.pack('>H', 0x70FD)       # moveq #-3,d0
    code += struct.pack('>H', 0x7204)       # moveq #4,d1
    # MULS.W D1,D0: 1100 000 111 000 001 = $C1C1
    code += struct.pack('>H', 0xC1C1)       # muls.w d1,d0
    code += struct.pack('>H', 0x4E75)       # rts
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "MULS should produce a concrete result"
    assert cpu.d[0].concrete == (-12) & 0xFFFFFFFF


# ── Bit ops: currently invalidated, should compute ───────────────────

def test_btst_reg():
    """BTST D1,D0: test bit, should NOT modify D0."""
    code = b''
    code += struct.pack('>H', 0x70FF)       # moveq #-1,d0 ($FFFFFFFF)
    code += struct.pack('>H', 0x7203)       # moveq #3,d1
    # BTST D1,D0: 0000 001 100 000 000 = $0300
    code += struct.pack('>H', 0x0300)       # btst d1,d0
    code += struct.pack('>H', 0x4E75)       # rts
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "BTST should not clobber destination"
    assert cpu.d[0].concrete == 0xFFFFFFFF


def test_bclr_reg():
    """BCLR D1,D0: clear bit 3 of D0."""
    code = b''
    code += struct.pack('>H', 0x70FF)       # moveq #-1,d0 ($FFFFFFFF)
    code += struct.pack('>H', 0x7203)       # moveq #3,d1
    # BCLR D1,D0: 0000 001 110 000 000 = $0380
    code += struct.pack('>H', 0x0380)       # bclr d1,d0
    code += struct.pack('>H', 0x4E75)       # rts
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "BCLR should produce a concrete result"
    assert cpu.d[0].concrete == 0xFFFFFFF7


def test_bset_reg():
    """BSET D1,D0: set bit 0 of D0."""
    code = b''
    code += struct.pack('>H', 0x7000)       # moveq #0,d0
    code += struct.pack('>H', 0x7200)       # moveq #0,d1
    # BSET D1,D0: 0000 001 111 000 000 = $03C0
    code += struct.pack('>H', 0x03C0)       # bset d1,d0
    code += struct.pack('>H', 0x4E75)       # rts
    cpu, _ = _run(code)
    assert cpu.d[0].is_known, "BSET should produce a concrete result"
    assert cpu.d[0].concrete == 1


# ── Summary overrides scratch invalidation ───────────────────────────

def test_summary_preserves_scratch_register():
    """Summary-preserved registers survive even if in scratch set.

    Caller sets D0=42, BSRs to sub that doesn't touch D0.
    Sub's summary should say D0 is preserved. After return,
    D0 should still be 42 at the fallthrough block -- scratch
    invalidation should NOT override a summary-preserved register.
    """
    sentinel = 0x80000002
    code = b''
    # $00: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $02: bsr.w $08 (sub that preserves D0)
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $06: rts (D0 should still be 42 here)
    code += struct.pack('>H', 0x4E75)
    # sub at $08: moveq #99,d1 (only modifies D1, not D0)
    code += struct.pack('>H', 0x7263)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    platform = {
        "scratch_regs": [("dn", 0), ("dn", 1), ("an", 0), ("an", 1)],
        "initial_base_reg": (6, sentinel),  # needed for summary computation
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)
    exit_states = result.get("exit_states", {})

    # Check the fallthrough block ($06), not the caller block ($00)
    assert 0x06 in exit_states, (
        f"Fallthrough block $06 should have exit state, "
        f"got {sorted(hex(a) for a in exit_states)}")
    cpu, _ = exit_states[0x06]
    assert cpu.d[0].is_known, (
        f"D0 should be preserved across call (summary overrides scratch), "
        f"got {cpu.d[0]}")
    assert cpu.d[0].concrete == 42, (
        f"D0 should be 42, got {cpu.d[0].concrete}")


def test_summary_produced_value_propagates():
    """Callee that always produces a concrete return value in D0.

    Sub computes D0=99 regardless of input. The summary should capture
    this as a 'produced' value, and the caller's fallthrough should
    have D0=99 (not unknown).
    """
    sentinel = 0x80000002
    code = b''
    # $00: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $02: bsr.w $08
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $06: rts (D0 should be 99 here -- produced by callee)
    code += struct.pack('>H', 0x4E75)
    # sub at $08: moveq #99,d0 (always produces D0=99)
    code += struct.pack('>H', 0x7063)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    platform = {
        "scratch_regs": [("dn", 0), ("dn", 1)],
        "initial_base_reg": (6, sentinel),
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    cpu, _ = result["exit_states"][0x06]
    assert cpu.d[0].is_known, (
        f"D0 should be 99 (produced by callee), got {cpu.d[0]}")
    assert cpu.d[0].concrete == 99, (
        f"D0 should be 99, got {cpu.d[0].concrete}")


def test_summary_produced_address_enables_dispatch():
    """Callee produces a concrete code address in A0, caller dispatches.

    Sub always sets A0 = LEA target(pc),a0. After return, caller does
    jsr (a0) which should resolve to the target address.

    This models the $3ED6 pattern in GenAm where a utility sub computes
    a function pointer and the caller dispatches through it.
    """
    sentinel = 0x80000002
    code = b''
    # $00: bsr.w $08
    code += struct.pack('>HH', 0x6100, 0x0006)
    # $04: jsr (a0)  -- should resolve to $10
    code += struct.pack('>H', 0x4E90)
    # $06: rts
    code += struct.pack('>H', 0x4E75)
    # sub at $08: lea $10(pc),a0 -> a0 = $0A + 6 = $10
    code += struct.pack('>HH', 0x41FA, 0x0006)
    # $0C: rts
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>H', 0x4E71)
    # target at $10: rts
    code += struct.pack('>H', 0x4E75)

    platform = {
        "scratch_regs": [("an", 0), ("an", 1)],
        "initial_base_reg": (6, sentinel),
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    from m68k.indirect_analysis import resolve_indirect_targets
    resolved = resolve_indirect_targets(
        result["blocks"], result.get("exit_states", {}), len(code))
    targets = sorted(r["target"] for r in resolved)
    assert 0x10 in targets, (
        f"Expected $0010 from jsr (a0) with callee-produced A0, "
        f"got {targets}")


def test_summary_input_dependent_stays_unknown():
    """Callee return value depends on input -- should NOT be in summary.

    Sub adds 1 to D0 and returns. Different callers get different results.
    The summary should NOT capture a concrete produced value.
    """
    sentinel = 0x80000002
    code = b''
    # $00: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $02: bsr.w $08
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $06: rts
    code += struct.pack('>H', 0x4E75)
    # sub at $08: addq.l #1,d0 (input-dependent result)
    code += struct.pack('>H', 0x5280)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    platform = {
        "scratch_regs": [("dn", 0)],
        "initial_base_reg": (6, sentinel),
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    # D0 should be unknown at fallthrough -- the summary can't know it's 43
    # because the sub's output depends on the input (not constant)
    cpu, _ = result["exit_states"][0x06]
    assert not cpu.d[0].is_known, (
        f"D0 should be unknown (input-dependent return), got {cpu.d[0]}")


def test_summary_unknown_return_stays_unknown():
    """Callee clobbers D0 with an unknown value -- stays unknown.

    Sub reads D0 from memory (unknown address), producing an unknown
    return value. This should NOT be captured as a produced value.
    """
    sentinel = 0x80000002
    code = b''
    # $00: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $02: bsr.w $08
    code += struct.pack('>HH', 0x6100, 0x0004)
    # $06: rts
    code += struct.pack('>H', 0x4E75)
    # sub at $08: move.l (a0),d0 (reads from unknown address -> D0 unknown)
    code += struct.pack('>H', 0x2010)
    # $0A: rts
    code += struct.pack('>H', 0x4E75)

    platform = {
        "scratch_regs": [("dn", 0)],
        "initial_base_reg": (6, sentinel),
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    cpu, _ = result["exit_states"][0x06]
    assert not cpu.d[0].is_known, (
        f"D0 should be unknown (callee reads from unknown addr), "
        f"got {cpu.d[0]}")


# ── Multi-entry propagation ──────────────────────────────────────────

def test_all_entry_points_get_exit_states():
    """Every entry point should be seeded with initial state for propagation.

    Entry point 0 has a BSR to sub_a at $04.
    Entry point $0C (e.g. from a jump table) is a separate subroutine.
    Both should have exit states after propagation.
    """
    code = b''
    # $00: bsr.w $04
    code += struct.pack('>HH', 0x6100, 0x0002)
    # $04: rts (sub_a, called from entry 0)
    code += struct.pack('>H', 0x4E75)
    # $06: nop (padding)
    code += struct.pack('>H', 0x4E71)
    # $08: nop
    code += struct.pack('>H', 0x4E71)
    # $0A: nop
    code += struct.pack('>H', 0x4E71)
    # $0C: moveq #99,d0 (separate entry point, e.g. jump table target)
    code += struct.pack('>H', 0x7063)
    # $0E: rts
    code += struct.pack('>H', 0x4E75)

    platform = {"scratch_regs": []}
    result = analyze(code, propagate=True, entry_points=[0, 0x0C],
                     platform=platform)
    exit_states = result.get("exit_states", {})

    # Entry 0 and its callee ($04) should have exit states
    assert 0 in exit_states, "Entry 0 should have exit state"

    # Entry $0C should ALSO have exit state -- it's a valid entry point
    assert 0x0C in exit_states, (
        f"Entry $0C should have exit state (seeded as entry point), "
        f"got states for: {sorted(hex(a) for a in exit_states)}")

    # And D0 should be 99 at exit of $0C
    cpu, _ = exit_states[0x0C]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 99, (
        f"D0 should be 99 at exit of $0C, got {cpu.d[0]}")


# ── Init memory join semantics ───────────────────────────────────────

def test_init_mem_value_survives_join():
    """Init memory pointer survives merge of two paths.

    Two paths converge, neither touches the init mem slot.
    After merge, movea.l 100(a6),a0; jsr (a0) should resolve.
    """
    sentinel = 0x80000002
    target = 0x10  # address of target rts

    code = b''
    # $00: tst.b d0
    code += struct.pack('>H', 0x4A00)
    # $02: beq.s $08 (offset = 4)
    code += struct.pack('>H', 0x6704)
    # $04: moveq #1,d1
    code += struct.pack('>H', 0x7201)
    # $06: bra.s $0A (offset = 2)
    code += struct.pack('>H', 0x6002)
    # $08: moveq #2,d1
    code += struct.pack('>H', 0x7402)
    # $0A: movea.l 100(a6),a0
    code += struct.pack('>HH', 0x206E, 0x0064)
    # $0E: jsr (a0)
    code += struct.pack('>H', 0x4E90)
    # $10: rts (target)
    code += struct.pack('>H', 0x4E75)

    init_mem = AbstractMemory()
    init_mem.write(sentinel + 100, _concrete(target), "l")

    platform = {
        "initial_base_reg": (6, sentinel),
        "_initial_mem": init_mem,
        "scratch_regs": [],
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    from m68k.indirect_analysis import resolve_indirect_targets
    resolved = resolve_indirect_targets(
        result["blocks"], result.get("exit_states", {}), len(code))
    targets = sorted(r["target"] for r in resolved)
    assert target in targets, (
        f"Expected ${target:04X} from jsr (a0) via init mem, got {targets}")


def test_store_in_one_sub_load_in_another():
    """Value stored by one sub, loaded and dispatched in another.

    Sub A stores LEA-computed address to d(A6).
    Sub B loads and dispatches. Init_mem seeded with the stored value.
    """
    sentinel = 0x80000002
    handler_addr = 0x1E

    code = b''
    # $00: bsr.w sub_store ($0A)
    code += struct.pack('>HH', 0x6100, 0x0008)
    # $04: bsr.w sub_load ($14)
    code += struct.pack('>HH', 0x6100, 0x000E)
    # $08: rts
    code += struct.pack('>H', 0x4E75)
    # sub_store ($0A): lea handler(pc),a0
    # PC=$0C, disp=$12, target=$0C+$12=$1E
    code += struct.pack('>HH', 0x41FA, 0x0012)
    # $0E: move.l a0,100(a6)
    code += struct.pack('>HH', 0x2D48, 0x0064)
    # $12: rts
    code += struct.pack('>H', 0x4E75)
    # sub_load ($14): movea.l 100(a6),a0
    code += struct.pack('>HH', 0x206E, 0x0064)
    # $18: jsr (a0)
    code += struct.pack('>H', 0x4E90)
    # $1A: rts
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>H', 0x4E71)
    # handler ($1E): rts
    code += struct.pack('>H', 0x4E75)

    # Seed init_mem with the value that sub_store would write
    init_mem = AbstractMemory()
    init_mem.write(sentinel + 100, _concrete(handler_addr), "l")

    platform = {
        "initial_base_reg": (6, sentinel),
        "_initial_mem": init_mem,
        "scratch_regs": [],
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    from m68k.indirect_analysis import resolve_indirect_targets
    resolved = resolve_indirect_targets(
        result["blocks"], result.get("exit_states", {}), len(code))
    targets = sorted(r["target"] for r in resolved)
    assert handler_addr in targets, (
        f"Expected ${handler_addr:04X} from jsr (a0) via init mem, "
        f"got {targets}")


def test_local_write_overrides_init_mem():
    """Block-local write overrides init memory value.

    A block writes unknown to d(A6) then reads it. The read should get
    unknown, not the init_mem value. No join involved — single path.
    """
    sentinel = 0x80000002
    code_target = 0x20

    code = b''
    # $00: move.l d0,100(a6)  -- d0 is unknown, overwrites init_mem slot
    code += struct.pack('>HH', 0x2D40, 0x0064)
    # $04: movea.l 100(a6),a0  -- should get unknown (d0 was unknown)
    code += struct.pack('>HH', 0x206E, 0x0064)
    # $08: rts
    code += struct.pack('>H', 0x4E75)

    init_mem = AbstractMemory()
    init_mem.write(sentinel + 100, _concrete(code_target), "l")

    platform = {
        "initial_base_reg": (6, sentinel),
        "_initial_mem": init_mem,
        "scratch_regs": [],
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    cpu, _ = result["exit_states"][0]
    assert not cpu.a[0].is_known, (
        f"A0 should be unknown after local write of unknown D0, "
        f"got {cpu.a[0]}")


def test_unknown_write_kills_init_mem_at_join():
    """Explicit unknown write on one path must NOT be restored at join.

    Path A: writes unknown d0 to init mem slot 100(a6).
    Path B: doesn't touch the slot (has init value).
    After merge: slot should be unknown (one path explicitly killed it).

    This is the soundness test — post-join restoration would incorrectly
    bring back the init value, producing a wrong concrete dispatch target.
    """
    sentinel = 0x80000002
    init_target = 0x20  # init mem has this, but path A kills it

    code = b''
    # $00: tst.b d0
    code += struct.pack('>H', 0x4A00)
    # $02: beq.s $0A  (path B: skip to nop)
    code += struct.pack('>H', 0x6706)
    # $04: move.l d0,100(a6)  (path A: write unknown d0 to slot)
    code += struct.pack('>HH', 0x2D40, 0x0064)
    # $08: bra.s $0C  (skip to merge)
    code += struct.pack('>H', 0x6002)
    # $0A: nop  (path B: no-op)
    code += struct.pack('>H', 0x4E71)
    # $0C: movea.l 100(a6),a0  (merge point: load from slot)
    code += struct.pack('>HH', 0x206E, 0x0064)
    # $10: rts
    code += struct.pack('>H', 0x4E75)

    init_mem = AbstractMemory()
    init_mem.write(sentinel + 100, _concrete(init_target), "l")

    platform = {
        "initial_base_reg": (6, sentinel),
        "_initial_mem": init_mem,
        "scratch_regs": [],
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    # A0 must be unknown: path A wrote unknown, path B has init value.
    # The join of (unknown, concrete) = unknown.
    cpu, _ = result["exit_states"][0x0C]
    assert not cpu.a[0].is_known, (
        f"A0 should be unknown (one path wrote unknown to slot), "
        f"got {cpu.a[0]}")


def test_concrete_overwrite_on_one_path_kills_init_at_join():
    """One path writes a different concrete value to an init mem slot.

    Path A: writes concrete 0x30 to slot (init had 0x20).
    Path B: doesn't touch the slot (has init value 0x20).
    After merge: slot should be unknown (disagreeing concrete values).

    Layout:
        $00: moveq  #$30,d1
        $02: tst.b  d0
        $04: beq.s  $0E          ; path B -> merge
        $06: move.l d1,100(a6)   ; path A: write 0x30
        $0A: bra.s  $0E          ; -> merge
        $0C: nop                 ; padding
        $0E: movea.l 100(a6),a0  ; merge point
        $12: rts
    """
    sentinel = 0x80000002
    init_target = 0x20
    other_target = 0x30

    code = b''
    # $00: moveq #$30,d1
    code += struct.pack('>H', 0x7230)
    # $02: tst.b d0
    code += struct.pack('>H', 0x4A00)
    # $04: beq.s $0E  (PC=$06, disp=8)
    code += struct.pack('>H', 0x6708)
    # $06: move.l d1,100(a6)  (path A: write 0x30)
    code += struct.pack('>HH', 0x2D41, 0x0064)
    # $0A: bra.s $0E  (PC=$0C, disp=2)
    code += struct.pack('>H', 0x6002)
    # $0C: nop  (padding)
    code += struct.pack('>H', 0x4E71)
    # $0E: movea.l 100(a6),a0  (merge point)
    code += struct.pack('>HH', 0x206E, 0x0064)
    # $12: rts
    code += struct.pack('>H', 0x4E75)

    init_mem = AbstractMemory()
    init_mem.write(sentinel + 100, _concrete(init_target), "l")

    platform = {
        "initial_base_reg": (6, sentinel),
        "_initial_mem": init_mem,
        "scratch_regs": [],
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    # A0 must be unknown: path A has 0x30, path B has 0x20.
    cpu, _ = result["exit_states"][0x0E]
    assert not cpu.a[0].is_known, (
        f"A0 should be unknown (paths disagree: ${init_target:02X} vs "
        f"${other_target:02X}), got {cpu.a[0]}")


def test_both_paths_agree_on_non_init_value():
    """Both paths write the same concrete value to an init mem slot.

    Both paths overwrite init value 0x20 with 0x30. After merge the
    slot should be concrete 0x30 (both agree, join preserves it).
    """
    sentinel = 0x80000002
    new_target = 0x30

    code = b''
    # $00: moveq #$30,d1
    code += struct.pack('>H', 0x7230)
    # $02: tst.b d0
    code += struct.pack('>H', 0x4A00)
    # $04: beq.s $0C  (path B)
    code += struct.pack('>H', 0x6706)
    # $06: move.l d1,100(a6)  (path A: write 0x30)
    code += struct.pack('>HH', 0x2D41, 0x0064)
    # $0A: bra.s $10  (skip to merge)
    code += struct.pack('>H', 0x6004)
    # $0C: move.l d1,100(a6)  (path B: also write 0x30)
    code += struct.pack('>HH', 0x2D41, 0x0064)
    # $10: movea.l 100(a6),a0  (merge point)
    code += struct.pack('>HH', 0x206E, 0x0064)
    # $14: rts
    code += struct.pack('>H', 0x4E75)

    init_mem = AbstractMemory()
    init_mem.write(sentinel + 100, _concrete(0x20), "l")

    platform = {
        "initial_base_reg": (6, sentinel),
        "_initial_mem": init_mem,
        "scratch_regs": [],
    }
    result = analyze(code, propagate=True, entry_points=[0],
                     platform=platform)

    # A0 should be 0x30: both paths wrote it, overriding init value
    cpu, _ = result["exit_states"][0x10]
    assert cpu.a[0].is_known, (
        f"A0 should be concrete (both paths wrote ${new_target:02X})")
    assert cpu.a[0].concrete == new_target, (
        f"A0 should be ${new_target:02X}, got ${cpu.a[0].concrete:02X}")


# ── Extended arithmetic: ADDX, SUBX ─────────────────────────────────

def test_addx_reg_reg():
    """ADDX.B D1,D1: D1 = D1 + D1 + X. Classic bit-reverse building block."""
    # moveq #0,d1; moveq #1,d0 (sets X via prior add)
    # We can't easily set X flag, so test with known values where X=0
    # moveq #5,d0; moveq #3,d1; addx.l d0,d1 -> d1 = 3 + 5 + 0 = 8
    code = b''
    code += struct.pack('>H', 0x7005)  # moveq #5,d0
    code += struct.pack('>H', 0x7203)  # moveq #3,d1
    # ADDX.L D0,D1: 1101 001 1 10 0 00 000 = 0xD380
    # Rx=1(D1=dest), Size=10(.L), R/M=0(reg), Ry=0(D0=src)
    code += struct.pack('>H', 0xD380)
    code += struct.pack('>H', 0x4E75)  # rts
    cpu, _ = _run(code)
    assert cpu.d[1].is_known, f"D1 should be concrete after ADDX, got {cpu.d[1]}"
    # X flag starts unknown (cleared by moveq), so result depends on X
    # moveq clears X, N, Z, V, C. So X=0 after moveq #3,d1
    # ADDX.L D0,D1 = 3 + 5 + 0 = 8
    assert cpu.d[1].concrete == 8, f"D1 should be 8 (3+5+X=0), got {cpu.d[1].concrete}"


def test_subx_reg_reg():
    """SUBX.L D0,D1: D1 = D1 - D0 - X."""
    code = b''
    code += struct.pack('>H', 0x7005)  # moveq #5,d0
    code += struct.pack('>H', 0x720A)  # moveq #10,d1
    # SUBX.L D0,D1: 1001 001 1 10 0 00 000 = 0x9380
    code += struct.pack('>H', 0x9380)
    code += struct.pack('>H', 0x4E75)  # rts
    cpu, _ = _run(code)
    assert cpu.d[1].is_known, f"D1 should be concrete after SUBX, got {cpu.d[1]}"
    # moveq clears X, so SUBX = 10 - 5 - 0 = 5
    assert cpu.d[1].concrete == 5, f"D1 should be 5 (10-5-X=0), got {cpu.d[1].concrete}"


def test_addx_predecrement():
    """ADDX.W -(A0),-(A1): memory-to-memory with predecrement."""
    # Set up: A0 points past source word, A1 points past dest word
    # Source word at $10: $0003. Dest word at $20: $0005.
    # ADDX.W -(A0),-(A1) -> A0=$10, A1=$20, read src=$0003, dst=$0005
    # Result = $0005 + $0003 = $0008, written to $20
    code = b''
    # $00: movea.l #$12,a0 (source at $10, A0 points past it)
    code += struct.pack('>HHH', 0x207C, 0x0000, 0x0012)
    # $06: movea.l #$22,a1 (dest at $20, A1 points past it)
    code += struct.pack('>HHH', 0x227C, 0x0000, 0x0022)
    # $0C: addx.w -(a0),-(a1)
    # 1101 001 1 01 1 00 000 = Rx=1(A1), Size=01(.W), R/M=1, Ry=0(A0)
    code += struct.pack('>H', 0xD348)
    # $0E: rts
    code += struct.pack('>H', 0x4E75)
    # Pad to $10
    code += struct.pack('>H', 0x0003)  # $10: source word = 3
    # Pad to $20
    code += b'\x00' * (0x20 - 0x12)
    code += struct.pack('>H', 0x0005)  # $20: dest word = 5

    cpu, mem = _run(code)
    # A0 should be decremented by 2 (word size) to $10
    assert cpu.a[0].is_known and cpu.a[0].concrete == 0x10
    # A1 should be decremented by 2 to $20
    assert cpu.a[1].is_known and cpu.a[1].concrete == 0x20


def test_trap_no_register_modification():
    """TRAP instruction should not modify data/address registers."""
    code = b''
    # $00: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $02: trap #0
    code += struct.pack('>H', 0x4E40)

    result = analyze(code, propagate=True, entry_points=[0])
    # Block 0 ends at trap (flow-terminating).
    # D0 should still be 42 at exit.
    cpu, _ = result["exit_states"][0]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 42, (
        f"D0 should be 42 (trap should not modify registers), got {cpu.d[0]}")
