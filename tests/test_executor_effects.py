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
    from m68k.jump_tables import resolve_indirect_targets
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

    from m68k.jump_tables import resolve_indirect_targets
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

    from m68k.jump_tables import resolve_indirect_targets
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
