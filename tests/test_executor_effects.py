"""Test instruction effect handlers in the executor.

Validates that each compute_formula.op handler produces correct
abstract state changes. Each test constructs a minimal code sequence,
runs the executor with propagation, and checks the exit state.

These tests exercise the KB-driven dispatch in _apply_instruction:
binary ops (add/sub/and/or/xor), unary ops (neg/not/swap/ext),
assign (move/moveq/clr), LEA, PEA, MOVEM, EXG, and the
compare-no-write path.
"""

import struct
import pytest

from m68k.m68k_executor import analyze, _concrete


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
