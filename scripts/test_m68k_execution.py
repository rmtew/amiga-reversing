"""M68K execution verification — KB predictions vs machine68k (Musashi) oracle.

Verifies that cc_semantics, sp_effects, pc_effects from m68k_instructions.json
match actual M68K execution behavior.

Test loop per instruction:
  1. Set up initial CPU state with deterministic register/flag values
  2. Assemble instruction with vasm
  3. Predict CC flags, PC, SP from KB semantic rules
  4. Execute one instruction in machine68k
  5. Compare predicted vs actual

All instruction selection, form types, and predictions are derived from KB data.
No hardcoded M68K instruction knowledge.

Usage:
    uv run python scripts/test_m68k_execution.py [--verbose] [--filter MNEMONIC]
"""

import json
import sys
import tempfile
from pathlib import Path

from machine68k import CPUType, Machine, Register

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT))
KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"

from m68k.vasm import assemble
from m68k.m68k_disasm import disassemble as disasm_bytes
from m68k.m68k_compute import (predict_cc, predict_sp, _size_mask, _to_signed,
                               _size_from_bits, _RULE_HANDLERS, _compute_result,
                               evaluate_cc_test)


# ── KB loader ─────────────────────────────────────────────────────────────

def _load_kb():
    with open(KNOWLEDGE, encoding="utf-8") as f:
        data = json.load(f)
    instructions = data.get("instructions", [])
    meta = data.get("_meta", {})
    return {inst["mnemonic"]: inst for inst in instructions}, instructions, meta

KB, KB_LIST, KB_META = _load_kb()


def _instr_size(code_bytes):
    """Get actual instruction size from assembled bytes using disassembler.

    Raises RuntimeError if disassembly fails — no silent fallback to
    len(code_bytes) which includes hunk padding and gives wrong answers.
    """
    instrs = disasm_bytes(code_bytes)
    if not instrs:
        raise RuntimeError(f"Disassembler returned no instructions for {code_bytes.hex()}")
    return instrs[0].size


# ── Machine68k wrapper ───────────────────────────────────────────────────

CODE_ADDR = 0x1000
STACK_ADDR = 0x8000  # plenty of room for stack ops
SCRATCH_ADDR = 0x2000  # memory area for EA targets

# Register enum mapping for D0-D7, A0-A6
DATA_REGS = [Register.D0, Register.D1, Register.D2, Register.D3,
             Register.D4, Register.D5, Register.D6, Register.D7]
ADDR_REGS = [Register.A0, Register.A1, Register.A2, Register.A3,
             Register.A4, Register.A5, Register.A6]

# CCR flag bit positions from KB (parser-asserted from PDF p21, Figure 1-8)
_ccr_bits = KB_META.get("ccr_bit_positions")
if _ccr_bits is None:
    raise RuntimeError("KB _meta missing ccr_bit_positions — regenerate KB")
CCR_C = 1 << _ccr_bits["C"]
CCR_V = 1 << _ccr_bits["V"]
CCR_Z = 1 << _ccr_bits["Z"]
CCR_N = 1 << _ccr_bits["N"]
CCR_X = 1 << _ccr_bits["X"]

# NOP opword derived from KB encoding data (not hardcoded)
NOP_OPWORD = KB_META.get("nop_opword")
if NOP_OPWORD is None:
    raise RuntimeError("KB _meta missing nop_opword — regenerate KB")

# Size suffix → byte count from KB (parser-asserted, PDF p29 Table 2-3)
_size_byte_count = KB_META.get("size_byte_count")
if _size_byte_count is None:
    raise RuntimeError("KB _meta missing size_byte_count — regenerate KB")


def _mem_write(mem, addr, value, size_bytes):
    """Write a value to memory at the given size (1/2/4 bytes)."""
    if size_bytes == 1:
        mem.w8(addr, value & 0xFF)
    elif size_bytes == 2:
        mem.w16(addr, value & 0xFFFF)
    else:
        mem.w32(addr, value & 0xFFFFFFFF)


def make_machine():
    """Create a fresh machine68k instance with 64KiB RAM."""
    m = Machine(CPUType.M68000, 64)
    mem = m.mem
    # Set up reset vectors: initial SP and PC
    mem.w32(0, STACK_ADDR)
    mem.w32(4, CODE_ADDR)
    m.cpu.pulse_reset()
    return m


# Mask to clear all CCR bits from SR, derived from KB bit positions
_CCR_MASK = CCR_C | CCR_V | CCR_Z | CCR_N | CCR_X


def set_ccr(cpu, x=0, n=0, z=0, v=0, c=0):
    """Set CCR flags in SR (preserve supervisor bits)."""
    sr = cpu.r_sr()
    sr &= ~_CCR_MASK & 0xFFFF  # clear CCR bits
    if x: sr |= CCR_X
    if n: sr |= CCR_N
    if z: sr |= CCR_Z
    if v: sr |= CCR_V
    if c: sr |= CCR_C
    cpu.w_sr(sr)


def read_ccr(cpu):
    """Read CCR flags from SR, return dict."""
    sr = cpu.r_sr()
    return {
        "X": 1 if sr & CCR_X else 0,
        "N": 1 if sr & CCR_N else 0,
        "Z": 1 if sr & CCR_Z else 0,
        "V": 1 if sr & CCR_V else 0,
        "C": 1 if sr & CCR_C else 0,
    }


def _reset_cpu(machine):
    """Reset CPU to clean state."""
    cpu = machine.cpu
    for r in DATA_REGS:
        cpu.w_reg(r, 0)
    for r in ADDR_REGS:
        cpu.w_reg(r, SCRATCH_ADDR)
    cpu.w_sp(STACK_ADDR)
    set_ccr(cpu, x=0, n=0, z=0, v=0, c=0)


def load_and_execute(machine, code_bytes):
    """Load code at CODE_ADDR, execute one instruction, return new state.

    Uses instruction hook to capture state right after the test instruction
    executes (when the CPU is about to fetch the second instruction).
    This avoids sentinel instructions clobbering CCR via exception processing.
    """
    mem = machine.mem
    cpu = machine.cpu

    # Write code bytes + NOP landing zone (assembled via vasm, cached)
    for i, b in enumerate(code_bytes):
        mem.w8(CODE_ADDR + i, b)
    # Write NOP landing zone after code (opword from KB encoding)
    for offset in range(len(code_bytes), len(code_bytes) + 8, 2):
        mem.w16(CODE_ADDR + offset, NOP_OPWORD)

    # Capture state on the SECOND instruction hook call.
    # First call = about to execute test instruction (PC = CODE_ADDR).
    # Second call = test instruction done, about to execute next (state we want).
    captured = {}
    call_count = [0]

    def on_instr(pc):
        call_count[0] += 1
        if call_count[0] == 2 and not captured:
            captured["pc"] = cpu.r_pc()
            captured["sp"] = cpu.r_sp()
            captured["sr"] = cpu.r_sr()
            captured["ccr"] = read_ccr(cpu)
            captured["d"] = [cpu.r_reg(r) for r in DATA_REGS]
            captured["a"] = [cpu.r_reg(r) for r in ADDR_REGS]

    cpu.set_instr_hook_callback(on_instr)
    cpu.w_pc(CODE_ADDR)
    cpu.execute(300)  # enough for slowest 68000 instructions (DIVS ≤ 158 cycles)
    cpu.set_instr_hook_callback(None)

    if not captured:
        raise RuntimeError(
            f"Instruction hook did not fire for code {code_bytes.hex()} — "
            f"call_count={call_count[0]}, PC=0x{cpu.r_pc():x}"
        )
    return captured


# CC prediction, result computation, SP prediction, and all rule handlers
# are in m68k_compute.py (imported above).


# ── KB-driven test discovery ──────────────────────────────────────────────

# Test value sets: (src, dst) pairs designed to exercise CC edge cases.
# These are arbitrary test inputs (not M68K knowledge).
TEST_VALUES = [
    (0x00000001, 0x00000002, "small positive"),
    (0x00000000, 0x00000000, "both zero"),
    (0x00000001, 0x00000000, "src=1 dst=0"),
    (0x00000000, 0x00000001, "src=0 dst=1"),
    (0xFFFFFFFF, 0x00000001, "src=max dst=1 (carry test)"),
    (0x00000001, 0xFFFFFFFF, "src=1 dst=max (carry test)"),
    (0x7FFFFFFF, 0x00000001, "overflow boundary pos"),
    (0x80000000, 0x80000000, "both msb set"),
    (0x7FFFFFFF, 0x7FFFFFFF, "both max positive"),
    (0x80000000, 0x00000001, "neg + pos"),
    (0x00000055, 0x000000AA, "bit pattern .b"),
    (0x0000FFFF, 0x00000001, "word overflow"),
]

# BCD test values: valid packed BCD bytes (each nibble 0-9).
# These are arbitrary test inputs (not M68K knowledge).
BCD_TEST_VALUES = [
    (0x00, 0x00, "bcd 00+00"),
    (0x01, 0x02, "bcd 01+02"),
    (0x09, 0x01, "bcd low carry"),
    (0x99, 0x01, "bcd max+1 (carry)"),
    (0x50, 0x50, "bcd high carry"),
    (0x99, 0x99, "bcd max+max"),
    (0x00, 0x01, "bcd 00+01"),
    (0x01, 0x00, "bcd 01+00"),
    (0x45, 0x67, "bcd mid values"),
    (0x99, 0x00, "bcd max+00"),
    (0x10, 0x90, "bcd high nibble carry"),
    (0x05, 0x05, "bcd 05+05"),
]

# Initial CCR states to test (exercises X-dependent and Z-dependent paths).
INITIAL_CCR_STATES = [
    {"X": 0, "N": 0, "Z": 0, "V": 0, "C": 0, "desc": "all-clear"},
    {"X": 1, "N": 1, "Z": 1, "V": 1, "C": 1, "desc": "all-set"},
    {"X": 0, "N": 0, "Z": 1, "V": 0, "C": 0, "desc": "Z-only"},
]

# An instruction is compute-testable if it has a compute_formula in the KB.
# This replaces the old _COMPUTE_HANDLERS dict — testability is now data-driven.
_TESTABLE_OP_TYPES = {inst.get("operation_type") for inst in KB_LIST
                      if inst.get("compute_formula")} - {None}


def _has_nontrivial_cc(inst):
    """Return True if instruction affects CC flags (not all unchanged/undefined)."""
    cc_sem = inst.get("cc_semantics", {})
    rules = {v.get("rule") for v in cc_sem.values()}
    return bool(rules - {"unchanged", "undefined"})


def _cc_rules_are_supported(inst):
    """Return True if all CC rules for this instruction are in _RULE_HANDLERS.

    Raises RuntimeError if a flag_spec exists but has no 'rule' key —
    this indicates incomplete KB data that should be fixed upstream.
    """
    cc_sem = inst.get("cc_semantics", {})
    for flag, flag_spec in cc_sem.items():
        rule = flag_spec.get("rule")
        if rule is None:
            raise RuntimeError(
                f"{inst['mnemonic']}: flag {flag} has cc_semantics entry "
                f"but no 'rule' key — fix KB")
        if rule not in _RULE_HANDLERS:
            return False
    return True


def _derive_form_type(inst):
    """Derive test form type from KB instruction forms and ea_modes.

    Returns (form_type, src_reg, dst_reg) or None.
    Form types:
      "two_op"           — Dn,Dn register form
      "single_op"        — single Dn operand
      "imm_dn"           — #imm,Dn
      "postinc_postinc"  — (An)+,(An)+ memory compare (CMPM)
      "dn_an"            — Dn,An (source=data reg, dest=addr reg)
    """
    ea_modes = inst.get("ea_modes", {})
    for form in inst.get("forms", []):
        if form.get("processor_020"):
            continue
        ops = [o["type"] for o in form.get("operands", [])]

        if ops == ["dn", "dn"]:
            return ("two_op", 0, 1)
        if ops == ["postinc", "postinc"]:
            # Memory-to-memory compare with postincrement
            return ("postinc_postinc", 0, 1)
        if ops == ["ea", "an"]:
            # Source from EA, dest is address register
            src_modes = ea_modes.get("src", ea_modes.get("ea", []))
            if "dn" in src_modes:
                return ("dn_an", 0, 1)
        if ops == ["ea", "dn"]:
            src_modes = ea_modes.get("src", ea_modes.get("ea", []))
            if "dn" in src_modes:
                return ("two_op", 0, 1)
        if ops == ["dn", "ea"]:
            dst_modes = ea_modes.get("dst", ea_modes.get("ea", []))
            if "dn" in dst_modes:
                return ("two_op", 0, 1)
        if ops == ["ea", "ea"]:
            src_modes = ea_modes.get("src", ea_modes.get("ea", []))
            dst_modes = ea_modes.get("dst", ea_modes.get("ea", []))
            if "dn" in src_modes and "dn" in dst_modes:
                return ("two_op", 0, 1)
        if ops == ["imm", "dn"]:
            return ("imm_dn", None, 1)
        if ops == ["imm", "ea"]:
            dst_modes = ea_modes.get("dst", ea_modes.get("ea", []))
            if "dn" in dst_modes:
                return ("imm_dn", None, 1)
        if ops == ["dn"]:
            return ("single_op", None, 1)
        if ops == ["ea"]:
            all_modes = ea_modes.get("ea", ea_modes.get("dst", ea_modes.get("src", [])))
            if "dn" in all_modes:
                return ("single_op", None, 1)

    return None


def discover_cc_testable_instructions():
    """Scan KB for instructions testable with register-to-register CC verification.

    An instruction is testable if:
    1. It has non-trivial cc_semantics (not all unchanged/undefined)
    2. It has an operation_type we can compute results for
    3. All its CC rules are supported by _RULE_HANDLERS
    4. It has a Dn,Dn-capable form (two-op or single-op)
    5. It has sizes (b/w/l)
    6. It's a 68000 instruction (processor_min == "68000" or absent)

    Returns list of (mnemonic, inst, form_info) tuples.
    """
    testable = []
    for inst in KB_LIST:
        mnemonic = inst["mnemonic"]
        proc = inst.get("processor_min", "68000")
        if proc != "68000":
            continue
        if not _has_nontrivial_cc(inst):
            continue
        op_type = inst.get("operation_type")
        if op_type not in _TESTABLE_OP_TYPES:
            continue
        if not _cc_rules_are_supported(inst):
            continue
        sizes = inst.get("sizes", [])
        if not sizes:
            continue
        form_info = _derive_form_type(inst)
        if form_info is None:
            continue
        testable.append((mnemonic, inst, form_info))
    return testable


def discover_sp_testable_instructions():
    """Scan KB for instructions with sp_effects that we can test.

    Returns list of (mnemonic, inst) tuples for instructions with non-empty
    sp_effects that are 68000 and have forms we can assemble.
    """
    testable = []
    for inst in KB_LIST:
        mnemonic = inst["mnemonic"]
        proc = inst.get("processor_min", "68000")
        if proc != "68000":
            continue
        sp_effects = inst.get("sp_effects", [])
        # Also include MOVEM-type instructions: no fixed sp_effects but
        # ea_modes include predec/postinc, which affect SP when used with A7.
        # Detected by reglist operand type in forms.
        has_reglist = any("reglist" in [o["type"] for o in f.get("operands", [])]
                         for f in inst.get("forms", []))
        if not sp_effects and not has_reglist:
            continue
        if inst.get("effects", {}).get("privileged"):
            continue  # skip supervisor-mode instructions
        testable.append((mnemonic, inst))
    return testable


def discover_ccr_op_testable_instructions():
    """Scan KB for CCR/SR manipulation instructions testable for CC verification.

    These have operation_type 'ccr_op' or 'sr_op' and directly manipulate
    CCR flags via immediate or source operand bits.
    """
    testable = []
    for inst in KB_LIST:
        mnemonic = inst["mnemonic"]
        proc = inst.get("processor_min", "68000")
        if proc != "68000":
            continue
        op_type = inst.get("operation_type")
        if op_type not in ("ccr_op", "sr_op"):
            continue
        if not _has_nontrivial_cc(inst):
            continue
        if not _cc_rules_are_supported(inst):
            continue
        testable.append((mnemonic, inst))
    return testable


# Test immediates for CCR/SR ops: cover all 5-bit XNZVC combinations.
CCR_OP_IMM_VALUES = [
    0x00,   # no flags affected
    0x1F,   # all flags affected
    0x10,   # X only
    0x08,   # N only
    0x04,   # Z only
    0x02,   # V only
    0x01,   # C only
    0x15,   # X, Z, C
    0x0A,   # N, V
]


def generate_ccr_op_tests(inst, tmpdir):
    """Generate CC tests for CCR/SR manipulation instructions.

    These instructions take an immediate (or EA source for MOVE to CCR)
    and directly modify CCR flags. No Dn-to-Dn computation.

    Yields (asm_text, code_bytes, src_val, initial_ccr, desc) tuples.
    """
    mnemonic = inst["mnemonic"]
    op_type = inst.get("operation_type")

    for form in inst.get("forms", []):
        if form.get("processor_020"):
            continue
        ops = [o["type"] for o in form.get("operands", [])]

        if ops == ["imm", "ccr"]:
            # ANDI/ORI/EORI to CCR: e.g. "andi #$1F,ccr"
            asm_base = mnemonic.split(" to ")[0].lower()
            for imm_val in CCR_OP_IMM_VALUES:
                for ccr_state in INITIAL_CCR_STATES:
                    asm_text = f"{asm_base} #{imm_val},ccr"
                    code_bytes = assemble(asm_text, tmpdir)
                    if code_bytes is None:
                        continue
                    initial_ccr = {k: v for k, v in ccr_state.items() if k != "desc"}
                    desc = f"{mnemonic} #${imm_val:02x} ccr={ccr_state['desc']}"
                    yield (asm_text, code_bytes, imm_val, initial_ccr, desc)

        elif ops == ["imm", "sr"]:
            # ANDI/ORI/EORI to SR (privileged — machine68k runs supervisor)
            asm_base = mnemonic.split(" to ")[0].lower()
            for imm_val in CCR_OP_IMM_VALUES:
                # For ANDI to SR, must preserve supervisor bit (bit 13)
                if "ANDI" in mnemonic:
                    sr_imm = imm_val | 0x2000
                else:
                    sr_imm = imm_val
                for ccr_state in INITIAL_CCR_STATES:
                    asm_text = f"{asm_base} #{sr_imm},sr"
                    code_bytes = assemble(asm_text, tmpdir)
                    if code_bytes is None:
                        continue
                    initial_ccr = {k: v for k, v in ccr_state.items() if k != "desc"}
                    desc = f"{mnemonic} #${sr_imm:04x} ccr={ccr_state['desc']}"
                    # Pass imm_val (not sr_imm) as src — rule handlers only
                    # check CCR bit positions (0-4), same in both
                    yield (asm_text, code_bytes, imm_val, initial_ccr, desc)

        elif ops == ["ea", "ccr"]:
            # MOVE to CCR: source from EA — use Dn
            ea_modes = inst.get("ea_modes", {})
            src_modes = ea_modes.get("src", ea_modes.get("ea", []))
            if "dn" not in src_modes:
                continue
            for imm_val in CCR_OP_IMM_VALUES:
                for ccr_state in INITIAL_CCR_STATES:
                    asm_text = "move d0,ccr"
                    code_bytes = assemble(asm_text, tmpdir)
                    if code_bytes is None:
                        continue
                    initial_ccr = {k: v for k, v in ccr_state.items() if k != "desc"}
                    desc = f"MOVE to CCR #${imm_val:02x} ccr={ccr_state['desc']}"
                    yield (asm_text, code_bytes, imm_val, initial_ccr, desc)


# ── Phase 4: register/flow verification for non-CC instructions ───────────

# Test values for An-destination ops (ADDA.L, SUBA.L, MOVEA.L).
# (src_val in Dn, dst_val in An, description).
AN_DEST_TEST_VALUES = [
    (0x00000000, 0x00002000, "src=0"),
    (0x00000001, 0x00002000, "src=1"),
    (0x00001000, 0x00002000, "src=$1000"),
    (0xFFFFFFFF, 0x00002000, "src=-1"),
    (0x80000000, 0x00002000, "src=msb"),
    (0x00002000, 0x00000000, "dst=0"),
    (0x12345678, 0x87654321, "mixed"),
]

# Test values for EXG: (val_a, val_b, description).
EXG_TEST_VALUES = [
    (0x11111111, 0x22222222, "distinct"),
    (0x00000000, 0xFFFFFFFF, "zero/max"),
    (0xAAAAAAAA, 0x55555555, "bit patterns"),
    (0x12345678, 0x12345678, "same value"),
]


def discover_register_testable_instructions():
    """Scan KB for instructions where register/PC results can be verified.

    Returns list of (mnemonic, inst, test_category) tuples.
    Categories:
      "an_dest"      — Dn→An result via compute_formula (ADDA, SUBA, MOVEA)
      "exg"          — register exchange (EXG)
      "lea"          — load effective address to An (LEA)
      "move_from_sr" — SR→Dn (MOVE from SR)
      "nop"          — PC-only (NOP)
      "branch"       — unconditional flow (BRA, JMP)
      "movep"        — byte-striped register↔memory (MOVEP)
      "chk"          — bounds check, non-trapping path (CHK)
    """
    testable = []
    for inst in KB_LIST:
        mnemonic = inst["mnemonic"]
        proc = inst.get("processor_min", "68000")
        if proc != "68000":
            continue
        op_type = inst.get("operation_type", "")
        has_formula = inst.get("compute_formula") is not None
        cc_sem = inst.get("cc_semantics", {})
        rules = {v.get("rule") for v in cc_sem.values()}
        has_cc = bool(rules - {"unchanged", "undefined"})
        priv = inst.get("effects", {}).get("privileged", False)
        if priv:
            continue
        forms = []
        for f in inst.get("forms", []):
            if not f.get("processor_020"):
                forms.append([o["type"] for o in f.get("operands", [])])
        ea_modes = inst.get("ea_modes", {})

        # An-destination: formula + [ea,an] + no CC + dn in src
        if has_formula and not has_cc and ["ea", "an"] in forms:
            src_modes = ea_modes.get("src", ea_modes.get("ea", []))
            if "dn" in src_modes and mnemonic in ("ADDA", "SUBA", "MOVEA"):
                testable.append((mnemonic, inst, "an_dest"))
                continue

        # EXG: operation_type=swap, no CC, has [dn,dn] form
        if op_type == "swap" and not has_cc and not has_formula:
            if ["dn", "dn"] in forms:
                testable.append((mnemonic, inst, "exg"))
                continue

        # LEA: formula + [ea,an] + no CC, no dn in src
        if mnemonic == "LEA" and has_formula and not has_cc:
            testable.append((mnemonic, inst, "lea"))
            continue

        # MOVE from SR: formula + [sr,ea]
        if mnemonic == "MOVE from SR" and has_formula:
            testable.append((mnemonic, inst, "move_from_sr"))
            continue

        # NOP: no formula, no CC, no operands
        if mnemonic == "NOP" and not has_formula and forms == [[]]:
            testable.append((mnemonic, inst, "nop"))
            continue

        # BRA/JMP: unconditional flow
        pc_effects = inst.get("pc_effects", {})
        flow = pc_effects.get("flow", {})
        if mnemonic == "BRA" and flow.get("type") == "branch" and not flow.get("conditional"):
            testable.append((mnemonic, inst, "branch"))
            continue
        if mnemonic == "JMP" and flow.get("type") == "jump":
            testable.append((mnemonic, inst, "branch"))
            continue

        # MOVEP: byte-striped register↔memory transfer
        if mnemonic == "MOVEP" and op_type == "move":
            testable.append((mnemonic, inst, "movep"))
            continue

        # CHK: bounds check — test non-trapping path only
        if mnemonic == "CHK" and op_type == "bounds_check":
            testable.append((mnemonic, inst, "chk"))
            continue

    return testable


def generate_register_tests(mnemonic, inst, category, tmpdir):
    """Generate register/flow verification tests for non-CC instructions.

    Yields (desc, code_bytes, setup_fn, verify_fn) tuples.
    setup_fn(cpu, mem): sets up registers/memory before execution.
    verify_fn(captured): returns (ok, details_list).
    """
    if category == "an_dest":
        yield from _gen_an_dest_tests(mnemonic, inst, tmpdir)
    elif category == "exg":
        yield from _gen_exg_tests(inst, tmpdir)
    elif category == "lea":
        yield from _gen_lea_tests(inst, tmpdir)
    elif category == "move_from_sr":
        yield from _gen_move_from_sr_tests(inst, tmpdir)
    elif category == "nop":
        yield from _gen_nop_tests(inst, tmpdir)
    elif category == "branch":
        yield from _gen_branch_tests(mnemonic, inst, tmpdir)
    elif category == "movep":
        yield from _gen_movep_tests(inst, tmpdir)
    elif category == "chk":
        yield from _gen_chk_tests(inst, tmpdir)


def _gen_an_dest_tests(mnemonic, inst, tmpdir):
    """ADDA/SUBA/MOVEA Dn,An — verify An result via compute_formula.

    KB field 'source_sign_extend' (from PDF description) indicates .W source
    is sign-extended to 32 bits before the operation. Both sizes produce a
    32-bit An result (KB field 'cc_result_bits' = 32).
    """
    mn_lower = mnemonic.lower()
    sign_ext = inst.get("source_sign_extend", False)
    result_bits = inst.get("cc_result_bits", None)
    for sz in inst.get("sizes", []):
        mask, bits = _size_mask(sz)
        for src_val, dst_val, val_desc in AN_DEST_TEST_VALUES:
            asm_text = f"{mn_lower}.{sz} d0,a1"
            code_bytes = assemble(asm_text, tmpdir)
            if code_bytes is None:
                continue

            # If KB says source is sign-extended and result is always 32-bit,
            # sign-extend the source to the result width before computing.
            if sign_ext and result_bits and bits < result_bits:
                src_masked = src_val & mask
                src_ext = _to_signed(src_masked, sz)
                src_ext &= (1 << result_bits) - 1
                _, predicted = _compute_result(
                    inst, src_ext, dst_val & 0xFFFFFFFF,
                    (1 << result_bits) - 1, result_bits, {})
            else:
                _, predicted = _compute_result(
                    inst, src_val & mask, dst_val & mask, mask, bits, {})
            desc = f"{mnemonic}.{sz} {val_desc}"

            def setup(cpu, mem, _sv=src_val, _dv=dst_val):
                cpu.w_reg(DATA_REGS[0], _sv & 0xFFFFFFFF)
                cpu.w_reg(ADDR_REGS[1], _dv & 0xFFFFFFFF)

            def verify(cap, _pred=predicted):
                a1 = cap["a"][1]
                if a1 != _pred:
                    return False, [f"A1: pred=0x{_pred:08x} actual=0x{a1:08x}"]
                return True, []

            yield (desc, code_bytes, setup, verify)


def _gen_exg_tests(inst, tmpdir):
    """EXG — verify registers are swapped (KB operation_type=swap)."""
    for val_a, val_b, val_desc in EXG_TEST_VALUES:
        # EXG Dx,Dy
        code = assemble("exg d0,d1", tmpdir)
        if code:
            def setup_dd(cpu, mem, _a=val_a, _b=val_b):
                cpu.w_reg(DATA_REGS[0], _a)
                cpu.w_reg(DATA_REGS[1], _b)
            def verify_dd(cap, _a=val_a, _b=val_b):
                ok, details = True, []
                if cap["d"][0] != _b:
                    ok = False
                    details.append(f"D0: expected=0x{_b:08x} actual=0x{cap['d'][0]:08x}")
                if cap["d"][1] != _a:
                    ok = False
                    details.append(f"D1: expected=0x{_a:08x} actual=0x{cap['d'][1]:08x}")
                return ok, details
            yield (f"EXG D0,D1 {val_desc}", code, setup_dd, verify_dd)

        # EXG Ax,Ay
        code = assemble("exg a0,a1", tmpdir)
        if code:
            def setup_aa(cpu, mem, _a=val_a, _b=val_b):
                cpu.w_reg(ADDR_REGS[0], _a)
                cpu.w_reg(ADDR_REGS[1], _b)
            def verify_aa(cap, _a=val_a, _b=val_b):
                ok, details = True, []
                if cap["a"][0] != _b:
                    ok = False
                    details.append(f"A0: expected=0x{_b:08x} actual=0x{cap['a'][0]:08x}")
                if cap["a"][1] != _a:
                    ok = False
                    details.append(f"A1: expected=0x{_a:08x} actual=0x{cap['a'][1]:08x}")
                return ok, details
            yield (f"EXG A0,A1 {val_desc}", code, setup_aa, verify_aa)

        # EXG Dx,Ay
        code = assemble("exg d0,a0", tmpdir)
        if code:
            def setup_da(cpu, mem, _a=val_a, _b=val_b):
                cpu.w_reg(DATA_REGS[0], _a)
                cpu.w_reg(ADDR_REGS[0], _b)
            def verify_da(cap, _a=val_a, _b=val_b):
                ok, details = True, []
                if cap["d"][0] != _b:
                    ok = False
                    details.append(f"D0: expected=0x{_b:08x} actual=0x{cap['d'][0]:08x}")
                if cap["a"][0] != _a:
                    ok = False
                    details.append(f"A0: expected=0x{_a:08x} actual=0x{cap['a'][0]:08x}")
                return ok, details
            yield (f"EXG D0,A0 {val_desc}", code, setup_da, verify_da)


def _gen_lea_tests(inst, tmpdir):
    """LEA ea,An — verify An = effective address."""
    # LEA (A0),A1 — A1 gets value of A0
    code = assemble("lea (a0),a1", tmpdir)
    if code:
        def setup(cpu, mem):
            cpu.w_reg(ADDR_REGS[0], SCRATCH_ADDR)
        def verify(cap):
            if cap["a"][1] != SCRATCH_ADDR:
                return False, [f"A1: expected=0x{SCRATCH_ADDR:08x} actual=0x{cap['a'][1]:08x}"]
            return True, []
        yield ("LEA (A0),A1", code, setup, verify)

    # LEA d(A0),A1 — A1 gets A0+d
    for disp, desc in [(4, "disp=4"), (100, "disp=100"), (-8, "disp=-8")]:
        asm = f"lea {disp}(a0),a1"
        code = assemble(asm, tmpdir)
        if code:
            expected = (SCRATCH_ADDR + disp) & 0xFFFFFFFF
            def setup_d(cpu, mem, _a=SCRATCH_ADDR):
                cpu.w_reg(ADDR_REGS[0], _a)
            def verify_d(cap, _exp=expected):
                if cap["a"][1] != _exp:
                    return False, [f"A1: expected=0x{_exp:08x} actual=0x{cap['a'][1]:08x}"]
                return True, []
            yield (f"LEA {desc}(A0),A1", code, setup_d, verify_d)

    # LEA $addr.L,A1 — absolute address
    code = assemble(f"lea ${SCRATCH_ADDR:x}.l,a1", tmpdir)
    if code:
        def setup_abs(cpu, mem):
            pass
        def verify_abs(cap, _exp=SCRATCH_ADDR):
            if cap["a"][1] != _exp:
                return False, [f"A1: expected=0x{_exp:08x} actual=0x{cap['a'][1]:08x}"]
            return True, []
        yield ("LEA abs.L,A1", code, setup_abs, verify_abs)


def _gen_move_from_sr_tests(inst, tmpdir):
    """MOVE from SR — verify Dn gets SR value."""
    code = assemble("move sr,d0", tmpdir)
    if not code:
        return
    # Test with different CCR states
    for ccr_state in INITIAL_CCR_STATES:
        initial_ccr = {k: v for k, v in ccr_state.items() if k != "desc"}

        def setup(cpu, mem, _ccr=initial_ccr):
            set_ccr(cpu, x=_ccr["X"], n=_ccr["N"], z=_ccr["Z"],
                    v=_ccr["V"], c=_ccr["C"])

        def verify(cap, _ccr=initial_ccr):
            sr = cap["d"][0] & 0xFFFF
            # Check CCR bits in the SR value match what we set
            actual_ccr = {
                "X": 1 if sr & CCR_X else 0,
                "N": 1 if sr & CCR_N else 0,
                "Z": 1 if sr & CCR_Z else 0,
                "V": 1 if sr & CCR_V else 0,
                "C": 1 if sr & CCR_C else 0,
            }
            details = []
            ok = True
            for flag in ("X", "N", "Z", "V", "C"):
                if actual_ccr[flag] != _ccr[flag]:
                    ok = False
                    details.append(f"{flag}: expected={_ccr[flag]} actual={actual_ccr[flag]}")
            return ok, details

        yield (f"MOVE SR,D0 ccr={ccr_state['desc']}", code, setup, verify)


def _gen_nop_tests(inst, tmpdir):
    """NOP — verify PC advances by instruction size."""
    code = assemble("nop", tmpdir)
    if not code:
        return
    instr_sz = _instr_size(code)
    expected_pc = CODE_ADDR + instr_sz

    def setup(cpu, mem):
        pass

    def verify(cap, _exp=expected_pc):
        if cap["pc"] != _exp:
            return False, [f"PC: expected=0x{_exp:08x} actual=0x{cap['pc']:08x}"]
        return True, []

    yield ("NOP", code, setup, verify)


def _gen_branch_tests(mnemonic, inst, tmpdir):
    """BRA/JMP — verify PC goes to target."""
    if mnemonic == "BRA":
        # BRA forward: use .w to get a fixed-size encoding
        asm = "bra.w .t\nnop\n.t:"
        code = assemble(asm, tmpdir)
        if code:
            instrs = disasm_bytes(code)
            # Target is after BRA + NOP
            target = CODE_ADDR + instrs[0].size + instrs[1].size

            def setup(cpu, mem):
                pass
            def verify(cap, _t=target):
                if cap["pc"] != _t:
                    return False, [f"PC: expected=0x{_t:08x} actual=0x{cap['pc']:08x}"]
                return True, []
            yield ("BRA.W forward", code, setup, verify)

    elif mnemonic == "JMP":
        # JMP (An) — jump to address in A0
        target = SCRATCH_ADDR
        code = assemble(f"jmp (a0)", tmpdir)
        if code:
            def setup(cpu, mem, _t=target):
                cpu.w_reg(ADDR_REGS[0], _t)
                mem.w16(_t, NOP_OPWORD)  # NOP at target
            def verify(cap, _t=target):
                if cap["pc"] != _t:
                    return False, [f"PC: expected=0x{_t:08x} actual=0x{cap['pc']:08x}"]
                return True, []
            yield ("JMP (A0)", code, setup, verify)

        # JMP abs.L
        code = assemble(f"jmp ${target:x}.l", tmpdir)
        if code:
            def setup_abs(cpu, mem, _t=target):
                mem.w16(_t, NOP_OPWORD)
            def verify_abs(cap, _t=target):
                if cap["pc"] != _t:
                    return False, [f"PC: expected=0x{_t:08x} actual=0x{cap['pc']:08x}"]
                return True, []
            yield ("JMP abs.L", code, setup_abs, verify_abs)


def _gen_movep_tests(inst, tmpdir):
    """MOVEP — byte-striped register↔memory transfer.

    Uses KB 'transfer_layout' (stride, byte_order) to derive byte positions.
    Tests memory→register direction (pre-fill striped memory, read into Dn).
    Register→memory cannot be verified: load_and_execute captures registers
    only, not memory state.
    """
    layout = inst.get("transfer_layout")
    if not layout:
        raise RuntimeError("MOVEP missing transfer_layout in KB — regenerate KB")
    stride = layout["stride"]
    byte_order = layout["byte_order"]

    disp = 0
    base = SCRATCH_ADDR
    size_bytes = _size_byte_count  # from KB _meta

    for sz in inst.get("sizes", []):
        asm_from_mem = f"movep.{sz} {disp}(a0),d1"
        code = assemble(asm_from_mem, tmpdir)
        if not code:
            continue

        n_bytes = size_bytes[sz]  # 2 for .w, 4 for .l
        bits = n_bytes * 8

        # Build test cases from KB layout parameters:
        # byte_order=big_endian → MSB at offset 0, next at +stride, etc.
        test_values = [0x12345678, 0x00000000, 0xFFFFFFFF, 0xABCD1234]
        for val in test_values:
            val_masked = val & ((1 << bits) - 1)

            # Derive byte positions from KB stride and byte_order
            if byte_order == "big_endian":
                # MSB first: byte 0 of register (highest) at lowest address
                mem_bytes = []
                for i in range(n_bytes):
                    shift = (n_bytes - 1 - i) * 8
                    byte_val = (val_masked >> shift) & 0xFF
                    mem_bytes.append((i * stride, byte_val))
            else:
                raise RuntimeError(
                    f"MOVEP: unsupported byte_order '{byte_order}' in KB")

            def setup(cpu, mem, _bytes=mem_bytes):
                cpu.w_reg(ADDR_REGS[0], base)
                cpu.w_reg(DATA_REGS[1], 0)
                for off in range(n_bytes * stride):
                    mem.w8(base + off, 0)
                for off, b in _bytes:
                    mem.w8(base + off, b)

            def verify(cap, _exp=val_masked, _bits=bits):
                mask = (1 << _bits) - 1
                actual = cap["d"][1] & mask
                if actual != _exp:
                    return False, [f"D1: expected=0x{_exp:0{_bits//4}x} "
                                   f"actual=0x{actual:0{_bits//4}x}"]
                return True, []

            desc = f"MOVEP.{sz.upper()} mem→reg val=0x{val_masked:0{bits//4}x}"
            yield (desc, code, setup, verify)


def _gen_chk_tests(inst, tmpdir):
    """CHK <ea>,Dn — non-trapping path only.

    Uses KB 'trap_condition' to determine which test values will NOT trap.
    KB says: trap if "destination < 0 || destination > source" (signed).
    Non-trapping: lower_bound ≤ destination ≤ source (signed).
    """
    trap_cond = inst.get("trap_condition")
    if not trap_cond:
        raise RuntimeError("CHK missing trap_condition in KB — regenerate KB")

    comparison = trap_cond["comparison"]
    lower_bound = trap_cond["lower_bound"]  # 0 per KB

    # CHK.W only on 68000 (KB constraints.sizes_68000 = ["w"])
    sizes_68k = inst.get("constraints", {}).get("sizes_68000")
    sizes = sizes_68k if sizes_68k else inst.get("sizes", [])

    for sz in sizes:
        code = assemble(f"chk.{sz} d0,d1", tmpdir)
        if not code:
            continue
        instr_sz = _instr_size(code)
        expected_pc = CODE_ADDR + instr_sz
        mask, bits = _size_mask(sz)

        # Generate non-trapping test cases based on KB trap_condition:
        # comparison=signed, lower_bound=0, upper_bound=source
        # Non-trapping when: 0 ≤ destination ≤ source (signed)
        max_pos = (1 << (bits - 1)) - 1  # max positive signed value at this size
        test_cases = [
            (100, 0, "val=0 bound=100"),
            (100, 50, "val=50 bound=100"),
            (100, 100, "val=bound=100"),
            (max_pos, 0, f"val=0 bound={max_pos}"),
            (max_pos, max_pos, f"val=bound={max_pos}"),
            (1, 0, "val=0 bound=1"),
            (1, 1, "val=1 bound=1"),
            (10, 5, "val=5 bound=10"),
        ]

        for bound, val, desc_str in test_cases:
            def setup(cpu, mem, _bound=bound, _val=val, _mask=mask):
                cpu.w_reg(DATA_REGS[0], _bound & _mask)
                cpu.w_reg(DATA_REGS[1], _val & _mask)

            def verify(cap, _exp_pc=expected_pc):
                if cap["pc"] != _exp_pc:
                    return False, [f"PC: expected=0x{_exp_pc:08x} actual=0x{cap['pc']:08x}"]
                return True, []

            yield (f"CHK.{sz.upper()} {desc_str}", code, setup, verify)


# ── Phase 5: Scc/Bcc/DBcc condition test verification ────────────────────

# All 16 CCR states covering all 5-bit combinations of XNZVC that matter
# for condition testing. We test a representative subset (not all 32).
CC_TEST_CCR_STATES = [
    {"X": 0, "N": 0, "Z": 0, "V": 0, "C": 0, "desc": "all_clear"},
    {"X": 0, "N": 0, "Z": 0, "V": 0, "C": 1, "desc": "C"},
    {"X": 0, "N": 0, "Z": 1, "V": 0, "C": 0, "desc": "Z"},
    {"X": 0, "N": 0, "Z": 1, "V": 0, "C": 1, "desc": "ZC"},
    {"X": 0, "N": 1, "Z": 0, "V": 0, "C": 0, "desc": "N"},
    {"X": 0, "N": 1, "Z": 0, "V": 1, "C": 0, "desc": "NV"},
    {"X": 0, "N": 0, "Z": 0, "V": 1, "C": 0, "desc": "V"},
    {"X": 0, "N": 1, "Z": 1, "V": 0, "C": 0, "desc": "NZ"},
    {"X": 0, "N": 0, "Z": 0, "V": 1, "C": 1, "desc": "VC"},
    {"X": 0, "N": 1, "Z": 0, "V": 1, "C": 1, "desc": "NVC"},
    {"X": 1, "N": 0, "Z": 0, "V": 0, "C": 0, "desc": "X"},
    {"X": 1, "N": 1, "Z": 1, "V": 1, "C": 1, "desc": "all_set"},
]


def discover_condition_testable_instructions():
    """Scan KB for Scc, Bcc, DBcc instructions.

    Returns list of (mnemonic, inst, category) tuples.
    Categories: "scc", "bcc", "dbcc"
    """
    cc_test_defs = KB_META.get("cc_test_definitions")
    if not cc_test_defs:
        return []

    testable = []
    for inst in KB_LIST:
        mn = inst["mnemonic"]
        proc = inst.get("processor_min", "68000")
        if proc != "68000":
            continue
        if mn == "Scc":
            testable.append((mn, inst, "scc"))
        elif mn == "Bcc":
            testable.append((mn, inst, "bcc"))
        elif mn == "DBcc":
            testable.append((mn, inst, "dbcc"))
    return testable


def generate_condition_tests(mnemonic, inst, category, tmpdir):
    """Generate condition code test verification tests.

    Yields (desc, code_bytes, setup_fn, verify_fn, indiv_mnemonic) tuples.
    """
    if category == "scc":
        yield from _gen_scc_tests(inst, tmpdir)
    elif category == "bcc":
        yield from _gen_bcc_tests(inst, tmpdir)
    elif category == "dbcc":
        yield from _gen_dbcc_tests(inst, tmpdir)


def _gen_scc_tests(inst, tmpdir):
    """Scc Dn — if condition true, Dn.b=$FF; else Dn.b=$00."""
    cc_test_defs = KB_META["cc_test_definitions"]
    cc_aliases = KB_META.get("cc_aliases", {})

    for cc_name, cc_def in cc_test_defs.items():
        test_expr = cc_def["test"]
        # Skip "t" (always true) and "f" (always false) — fewer interesting states needed
        # But include them with just 2 states each
        states = CC_TEST_CCR_STATES if cc_name not in ("t", "f") else CC_TEST_CCR_STATES[:2]

        asm_mnemonic = f"s{cc_name}"
        # Check if assembler uses an alias (e.g. shs for scc)
        asm_text = f"{asm_mnemonic} d0"
        code = assemble(asm_text, tmpdir)
        if code is None:
            # Try with known aliases
            for alias, target in cc_aliases.items():
                if target == cc_name:
                    asm_text = f"s{alias} d0"
                    code = assemble(asm_text, tmpdir)
                    if code is not None:
                        break
        if code is None:
            print(f"  WARNING: S{cc_name.upper()} could not be assembled", file=sys.stderr)
            continue

        indiv = f"S{cc_name.upper()}"
        for ccr_state in states:
            initial_ccr = {k: v for k, v in ccr_state.items() if k != "desc"}
            cond_met = evaluate_cc_test(test_expr, initial_ccr)
            expected_d0 = 0x000000FF if cond_met else 0x00000000

            def setup(cpu, mem, _ccr=initial_ccr):
                cpu.w_reg(DATA_REGS[0], 0x12345678)  # pre-fill to verify byte write
                set_ccr(cpu, x=_ccr["X"], n=_ccr["N"], z=_ccr["Z"],
                        v=_ccr["V"], c=_ccr["C"])

            def verify(cap, _exp=expected_d0):
                # Scc only affects low byte, upper bytes unchanged
                actual_lo = cap["d"][0] & 0xFF
                exp_lo = _exp & 0xFF
                if actual_lo != exp_lo:
                    return False, [f"D0.b: expected=0x{exp_lo:02x} actual=0x{actual_lo:02x}"]
                return True, []

            desc_flag = ccr_state["desc"]
            yield (f"{indiv} {desc_flag} -> {'$FF' if cond_met else '$00'}",
                   code, setup, verify, indiv)


def _gen_bcc_tests(inst, tmpdir):
    """Bcc — if condition true, PC = target; else PC = next instruction."""
    cc_test_defs = KB_META["cc_test_definitions"]
    cc_aliases = KB_META.get("cc_aliases", {})

    for cc_name, cc_def in cc_test_defs.items():
        test_expr = cc_def["test"]
        # Skip always-true/false for Bcc (BRA already tested, BF doesn't exist as Bcc)
        if cc_name in ("t", "f"):
            continue

        states = CC_TEST_CCR_STATES

        asm_mnemonic = f"b{cc_name}"
        # Assemble: bcc.w .target; nop; .target: nop
        asm_text = f"{asm_mnemonic}.w .t\nnop\n.t:"
        code = assemble(asm_text, tmpdir)
        if code is None:
            for alias, target in cc_aliases.items():
                if target == cc_name:
                    asm_text = f"b{alias}.w .t\nnop\n.t:"
                    code = assemble(asm_text, tmpdir)
                    if code is not None:
                        break
        if code is None:
            print(f"  WARNING: B{cc_name.upper()} could not be assembled", file=sys.stderr)
            continue

        # Disassemble to find instruction sizes
        instrs = disasm_bytes(code)
        bcc_size = instrs[0].size   # Bcc instruction
        nop_size = instrs[1].size   # NOP after Bcc
        target_pc = CODE_ADDR + bcc_size + nop_size  # branch target
        fallthrough_pc = CODE_ADDR + bcc_size         # next after Bcc

        indiv = f"B{cc_name.upper()}"
        for ccr_state in states:
            initial_ccr = {k: v for k, v in ccr_state.items() if k != "desc"}
            cond_met = evaluate_cc_test(test_expr, initial_ccr)
            expected_pc = target_pc if cond_met else fallthrough_pc

            def setup(cpu, mem, _ccr=initial_ccr):
                set_ccr(cpu, x=_ccr["X"], n=_ccr["N"], z=_ccr["Z"],
                        v=_ccr["V"], c=_ccr["C"])

            def verify(cap, _exp=expected_pc):
                if cap["pc"] != _exp:
                    return False, [f"PC: expected=0x{_exp:08x} actual=0x{cap['pc']:08x}"]
                return True, []

            desc_flag = ccr_state["desc"]
            taken = "taken" if cond_met else "not-taken"
            yield (f"{indiv}.W {desc_flag} {taken}",
                   code, setup, verify, indiv)


def _gen_dbcc_tests(inst, tmpdir):
    """DBcc Dn,<label> — if cc false AND Dn-1 != -1, branch; else fall through.

    DBcc behavior:
      1. If condition TRUE → fall through (no decrement)
      2. If condition FALSE → Dn.w -= 1
         a. If Dn.w == -1 → fall through (loop exhausted)
         b. If Dn.w != -1 → branch to target
    """
    cc_test_defs = KB_META["cc_test_definitions"]
    cc_aliases = KB_META.get("cc_aliases", {})

    for cc_name, cc_def in cc_test_defs.items():
        test_expr = cc_def["test"]

        asm_mnemonic = f"db{cc_name}"
        # DBcc D1,.target; nop; .target: nop
        asm_text = f"{asm_mnemonic} d1,.t\nnop\n.t:"
        code = assemble(asm_text, tmpdir)
        if code is None:
            for alias, target in cc_aliases.items():
                if target == cc_name:
                    asm_text = f"db{alias} d1,.t\nnop\n.t:"
                    code = assemble(asm_text, tmpdir)
                    if code is not None:
                        break
        if code is None:
            print(f"  WARNING: DB{cc_name.upper()} could not be assembled", file=sys.stderr)
            continue

        instrs = disasm_bytes(code)
        dbcc_size = instrs[0].size
        nop_size = instrs[1].size
        target_pc = CODE_ADDR + dbcc_size + nop_size
        fallthrough_pc = CODE_ADDR + dbcc_size

        indiv = f"DB{cc_name.upper()}"

        # Test scenarios for each condition:
        # 1. Condition TRUE, Dn=5 → fall through, Dn unchanged
        # 2. Condition FALSE, Dn=5 → branch, Dn.w=4
        # 3. Condition FALSE, Dn=0 → branch, Dn.w=-1... wait, Dn=0→Dn.w=0xFFFF=-1→fall through
        test_cases = []
        for ccr_state in CC_TEST_CCR_STATES[:4]:  # subset for each cc
            initial_ccr = {k: v for k, v in ccr_state.items() if k != "desc"}
            cond_met = evaluate_cc_test(test_expr, initial_ccr)

            if cond_met:
                # Condition TRUE → fall through, Dn unchanged
                test_cases.append((initial_ccr, 5, fallthrough_pc, 5, ccr_state["desc"], "cc-true"))
            else:
                # Condition FALSE, Dn=5 → decrement, branch
                test_cases.append((initial_ccr, 5, target_pc, 4, ccr_state["desc"], "loop"))
                # Condition FALSE, Dn=0 → decrement to -1, fall through
                test_cases.append((initial_ccr, 0, fallthrough_pc, 0xFFFF, ccr_state["desc"], "exhaust"))

        for initial_ccr, dn_val, expected_pc, expected_dn_w, desc_flag, scenario in test_cases:

            def setup(cpu, mem, _ccr=initial_ccr, _dn=dn_val):
                cpu.w_reg(DATA_REGS[1], _dn & 0xFFFFFFFF)
                set_ccr(cpu, x=_ccr["X"], n=_ccr["N"], z=_ccr["Z"],
                        v=_ccr["V"], c=_ccr["C"])

            def verify(cap, _exp_pc=expected_pc, _exp_dn=expected_dn_w):
                ok, details = True, []
                if cap["pc"] != _exp_pc:
                    ok = False
                    details.append(f"PC: expected=0x{_exp_pc:08x} actual=0x{cap['pc']:08x}")
                actual_dn_w = cap["d"][1] & 0xFFFF
                if actual_dn_w != _exp_dn:
                    ok = False
                    details.append(f"D1.w: expected=0x{_exp_dn:04x} actual=0x{actual_dn_w:04x}")
                return ok, details

            yield (f"{indiv} {desc_flag} Dn={dn_val} {scenario}",
                   code, setup, verify, indiv)


# ── Shift/rotate mnemonic helpers ─────────────────────────────────────────

# Test values for shift/rotate: (count, operand, description).
# Count is the shift amount (in D0); operand is the value shifted (in D1).
# Covers count=0 (zero_count rules), boundary counts, and varied operands.
SHIFT_TEST_VALUES = [
    (0, 0x00000000, "cnt=0 val=0"),
    (0, 0x80000000, "cnt=0 val=msb"),
    (0, 0x000000FF, "cnt=0 val=0xFF"),
    (1, 0x00000001, "cnt=1 val=1"),
    (1, 0x80000000, "cnt=1 val=msb"),
    (1, 0x000000FF, "cnt=1 val=0xFF"),
    (1, 0x00000040, "cnt=1 val=0x40"),
    (1, 0x0000FFFF, "cnt=1 val=0xFFFF"),
    (7, 0x000000FF, "cnt=7 val=0xFF"),
    (7, 0x00000001, "cnt=7 val=1"),
    (8, 0x000000AA, "cnt=8 val=0xAA"),
    (8, 0x000000FF, "cnt=8 val=0xFF"),
    (15, 0x0000FFFF, "cnt=15 val=0xFFFF"),
    (16, 0x0000FFFF, "cnt=16 val=0xFFFF"),
    (31, 0xFFFFFFFF, "cnt=31 val=max"),
    (31, 0x80000000, "cnt=31 val=msb"),
    (32, 0xFFFFFFFF, "cnt=32 val=max"),
    (4, 0x12345678, "cnt=4 val=mixed"),
]


# Test values for multiply: (src, dst, description).
# src = multiplier (16-bit), dst = multiplicand (16-bit for .w).
MULTIPLY_TEST_VALUES = [
    (0, 0, "0*0"),
    (1, 1, "1*1"),
    (0, 5, "0*5"),
    (3, 7, "3*7=21"),
    (0x00FF, 0x00FF, "255*255"),
    (0x7FFF, 0x0002, "maxpos*2"),
    (0xFFFF, 0x0001, "-1*1 signed"),
    (0xFFFF, 0xFFFF, "-1*-1 signed"),
    (0x8000, 0x0002, "-32768*2 signed"),
    (0x8000, 0x8000, "-32768*-32768 signed"),
    (0x7FFF, 0x7FFF, "maxpos*maxpos"),
    (0xFFFF, 0xFFFF, "maxunsigned*maxunsigned"),
]

# Test values for divide: (src=divisor, dst=dividend, description).
# src's low 16 bits = divisor. dst = full 32-bit dividend.
# MUST avoid src=0 (divide by zero would trap).
DIVIDE_TEST_VALUES = [
    (1, 0, "0/1=0"),
    (1, 1, "1/1=1"),
    (3, 6, "6/3=2"),
    (7, 100, "100/7=14r2"),
    (2, 0x0000FFFE, "65534/2=32767"),
    (1, 0x0000FFFF, "65535/1=max16 (DIVU boundary)"),
    (1, 0x00010000, "65536/1 (DIVU overflow)"),
    (2, 0x0001FFFE, "131070/2=65535 (DIVU boundary)"),
    (2, 0x00020000, "131072/2=65536 (DIVU overflow)"),
    (1, 0x7FFFFFFF, "maxpos/1 (overflow)"),
    (0xFFFF, 0xFFFFFFFF, "-1/-1=1 DIVS"),
    (3, 0xFFFFFFF4, "-12/3=-4 DIVS"),
    (0xFFFF, 0x00000001, "1/-1=-1 DIVS"),
    (5, 0x00000003, "3/5=0r3"),
]


# Test values for bit test: (bit_number_in_src, destination, description).
# Bit number is in D0; destination is in D1. Bit modulo 32 for Dn dest.
BIT_TEST_VALUES = [
    (0, 0x00000000, "bit0 of 0"),
    (0, 0x00000001, "bit0 of 1"),
    (0, 0xFFFFFFFE, "bit0 of ~1"),
    (1, 0x00000002, "bit1 set"),
    (1, 0xFFFFFFFD, "bit1 clear"),
    (7, 0x00000080, "bit7 set"),
    (7, 0x0000007F, "bit7 clear"),
    (15, 0x00008000, "bit15 set"),
    (16, 0x00010000, "bit16 set"),
    (31, 0x80000000, "bit31 set"),
    (31, 0x7FFFFFFF, "bit31 clear"),
    (31, 0x00000000, "bit31 of 0"),
    (0, 0xFFFFFFFF, "bit0 all-set"),
    (32, 0x00000001, "bit32 mod32=bit0"),
    (33, 0x00000002, "bit33 mod32=bit1"),
    (63, 0x80000000, "bit63 mod32=bit31"),
]


# Test values for instructions with limited immediate range (e.g. MOVEQ: -128..127).
# (src=immediate, dst=ignored, description). Covers sign-extension edge cases.
IMM_BYTE_TEST_VALUES = [
    (0, 0, "imm=0"),
    (1, 0, "imm=1"),
    (127, 0, "imm=127 (max pos)"),
    (-1, 0, "imm=-1 (extends to $FFFFFFFF)"),
    (-128, 0, "imm=-128 (min neg)"),
    (0x55, 0, "imm=$55"),
    (-86, 0, "imm=-86 ($AA extends)"),
]


def _get_variant_props(inst, individual_mnemonic):
    """Look up variant properties for an individual mnemonic from KB 'variants' array.

    Returns the variant dict (with 'direction', 'arithmetic' keys) or raises
    RuntimeError if the variant is not found in the KB.
    """
    variants = inst.get("variants")
    if variants is None:
        raise RuntimeError(
            f"{inst['mnemonic']}: missing 'variants' in KB — regenerate KB")
    for v in variants:
        if v["mnemonic"].upper() == individual_mnemonic.upper():
            return v
    raise RuntimeError(
        f"{inst['mnemonic']}: no variant '{individual_mnemonic}' in KB variants {variants}")


def _split_combined_mnemonic(mnemonic):
    """Split KB combined mnemonics like 'ASL, ASR' into individual mnemonics.

    Returns list of individual mnemonic strings.
    Non-combined mnemonics return a single-element list.
    """
    if ", " in mnemonic:
        return [m.strip() for m in mnemonic.split(",")]
    return [mnemonic]


# ── CC test case generation ───────────────────────────────────────────────

def _find_form_data_sizes(inst, sz):
    """Find data_sizes from KB form matching the given size, skipping 020+ forms.

    Returns the data_sizes dict from the matching form, or None if not found.
    """
    for form in inst.get("forms", []):
        if form.get("processor_020"):
            continue
        form_sizes = form.get("sizes", inst.get("sizes", []))
        if sz in form_sizes or not form_sizes:
            ds = form.get("data_sizes")
            if ds:
                return ds
    return None


def generate_cc_tests(inst, form_info, tmpdir):
    """Generate CC verification test cases for one instruction from KB data.

    For combined mnemonics (e.g. 'ASL, ASR'), generates tests for each
    individual mnemonic. For shift/rotate instructions, uses SHIFT_TEST_VALUES
    and provides direction/arithmetic context for CC prediction.
    For multiply/divide instructions, uses MULTIPLY/DIVIDE_TEST_VALUES
    and provides signed/data_sizes context.

    Yields (asm_text, code_bytes, sz, src_val, dst_val,
            src_reg, dst_reg, initial_ccr, desc, ctx) tuples.
    """
    mnemonic = inst["mnemonic"]
    op_type = inst.get("operation_type")
    sizes = inst.get("sizes", [])
    form_type, src_reg, dst_reg = form_info

    is_shift_rotate = op_type in ("shift", "rotate", "rotate_extend")
    is_mul_div = op_type in ("multiply", "divide")
    individual_mnemonics = _split_combined_mnemonic(mnemonic)

    is_bit_test = op_type == "bit_test"
    is_sign_extend = op_type == "sign_extend"
    is_bcd = op_type in ("add_decimal", "sub_decimal") or (
        op_type == "negx" and inst.get("compute_formula", {}).get("op") == "subtract_decimal"
    )

    # For bit test, get bit_modulus from KB (register modulus for Dn tests)
    if is_bit_test:
        bit_mod_data = inst.get("bit_modulus")
        if bit_mod_data is None:
            raise RuntimeError(
                f"{mnemonic}: missing 'bit_modulus' in KB — regenerate KB")

    # Check for KB immediate range constraint (e.g. MOVEQ: -128..127)
    imm_range = inst.get("constraints", {}).get("immediate_range")

    # Select test values based on operation type
    if is_shift_rotate:
        values = SHIFT_TEST_VALUES
    elif op_type == "multiply":
        values = MULTIPLY_TEST_VALUES
    elif op_type == "divide":
        values = DIVIDE_TEST_VALUES
    elif is_bit_test:
        values = BIT_TEST_VALUES
    elif is_bcd:
        values = BCD_TEST_VALUES
    elif imm_range and imm_range.get("signed") and form_type == "imm_dn":
        values = IMM_BYTE_TEST_VALUES
    else:
        values = TEST_VALUES

    for indiv_mnemonic in individual_mnemonics:
        # Skip 020+ individual mnemonics using KB variant processor_020 flag
        variants = inst.get("variants", [])
        variant_entry = next(
            (v for v in variants if v["mnemonic"].upper() == indiv_mnemonic.upper()),
            None)
        if variant_entry and variant_entry.get("processor_020"):
            continue

        # Build context from KB variant/instruction properties
        if is_shift_rotate:
            variant = _get_variant_props(inst, indiv_mnemonic)
            count_mod = inst.get("shift_count_modulus")
            if count_mod is None:
                raise RuntimeError(
                    f"{mnemonic}: missing shift_count_modulus in KB")
            direction = variant.get("direction")
            if direction is None:
                raise RuntimeError(
                    f"{mnemonic}: variant {indiv_mnemonic} missing 'direction' in KB")
            arithmetic = variant.get("arithmetic")
            if arithmetic is None:
                raise RuntimeError(
                    f"{mnemonic}: variant {indiv_mnemonic} missing 'arithmetic' in KB")
            # Map KB direction names to internal convention used by compute handlers
            dir_map = {"left": "L", "right": "R"}
            fill = variant.get("fill")
            if fill is None:
                raise RuntimeError(
                    f"{mnemonic}: variant {indiv_mnemonic} missing 'fill' in KB — "
                    f"regenerate KB")
            ctx = {
                "direction": dir_map[direction],
                "arithmetic": arithmetic,
                "fill": fill,
                "count_modulus": count_mod,
            }
            # rotate_extend needs extra_bits (from KB rotate_extra_bits)
            if op_type == "rotate_extend":
                extra = inst.get("rotate_extra_bits")
                if extra is None:
                    raise RuntimeError(
                        f"{mnemonic}: missing rotate_extra_bits in KB")
                ctx["extra_bits"] = extra
        elif is_mul_div:
            signed = inst.get("signed")
            if signed is None:
                raise RuntimeError(
                    f"{mnemonic}: missing 'signed' field in KB — regenerate KB")
            ctx = {
                "signed": signed,
            }
        elif is_bit_test:
            # Use register modulus for Dn-destination tests (from KB bit_modulus)
            ctx = {"bit_modulus": bit_mod_data["register"]}
        else:
            ctx = {}

        # For bit test with size_by_ea_category, filter sizes to match
        # the EA category being tested (register Dn → only the register size).
        # KB field extracted from PDF description text.
        if is_bit_test:
            size_by_ea = inst.get("size_by_ea_category")
            if size_by_ea is None:
                raise RuntimeError(
                    f"{mnemonic}: missing 'size_by_ea_category' in KB — regenerate KB")
            # Register-destination tests use only the register size
            valid_sizes = [sz for sz in sizes if sz == size_by_ea["register"]]
        else:
            valid_sizes = sizes

        # CC result width override from KB (e.g. SWAP: Size=Word but CC uses 32-bit)
        cc_result_bits = inst.get("cc_result_bits")
        if cc_result_bits is not None:
            ctx["cc_result_bits"] = cc_result_bits
        # Source sign-extension from KB (e.g. CMPA.W: 16-bit source → 32-bit)
        if inst.get("source_sign_extend"):
            ctx["source_sign_extend"] = True

        for sz in valid_sizes:
            # For multiply/divide, find data_sizes from the matching KB form.
            # If no non-020 form has data_sizes for this size, skip it
            # (the .l forms are 020+ only).
            if is_mul_div:
                ds = _find_form_data_sizes(inst, sz)
                if ds is None:
                    continue
                ctx["data_sizes"] = ds

            # For sign_extend, look up source width from KB formula
            if is_sign_extend:
                formula = inst.get("compute_formula", {})
                sbbs = formula.get("source_bits_by_size", {})
                # Check variant-specific key first (e.g. "extb_l"), then generic
                variant_key = f"{indiv_mnemonic.lower()}_{sz}"
                src_bits = sbbs.get(variant_key, sbbs.get(sz))
                if src_bits is None:
                    raise RuntimeError(
                        f"{indiv_mnemonic}.{sz}: missing source_bits_by_size "
                        f"entry in KB compute_formula — regenerate KB")
                ctx["sign_extend_source_bits"] = src_bits

            for src_val, dst_val, val_desc in values:
                for ccr_state in INITIAL_CCR_STATES:
                    ccr_desc = ccr_state["desc"]

                    if form_type == "two_op":
                        asm_text = f"{indiv_mnemonic.lower()}.{sz} d{src_reg},d{dst_reg}"
                    elif form_type == "single_op":
                        asm_text = f"{indiv_mnemonic.lower()}.{sz} d{dst_reg}"
                    elif form_type == "imm_dn":
                        asm_text = f"{indiv_mnemonic.lower()}.{sz} #{src_val},d{dst_reg}"
                    elif form_type == "postinc_postinc":
                        asm_text = f"{indiv_mnemonic.lower()}.{sz} (a{src_reg})+,(a{dst_reg})+"
                    elif form_type == "dn_an":
                        asm_text = f"{indiv_mnemonic.lower()}.{sz} d{src_reg},a{dst_reg}"
                    else:
                        continue

                    code_bytes = assemble(asm_text, tmpdir)
                    if code_bytes is None:
                        continue

                    # For memory-operand forms, provide a setup function in ctx
                    # that writes values to memory and sets address registers
                    test_ctx = dict(ctx)  # copy so per-test setup doesn't leak
                    if form_type == "postinc_postinc":
                        sz_bytes = _size_byte_count[sz]
                        def _setup_postinc(cpu, mem, _sv=src_val, _dv=dst_val,
                                           _szb=sz_bytes, _sr=src_reg, _dr=dst_reg):
                            addr_src = SCRATCH_ADDR
                            addr_dst = SCRATCH_ADDR + _szb
                            _mem_write(mem, addr_src, _sv, _szb)
                            _mem_write(mem, addr_dst, _dv, _szb)
                            cpu.w_reg(ADDR_REGS[_sr], addr_src)
                            cpu.w_reg(ADDR_REGS[_dr], addr_dst)
                        test_ctx["setup"] = _setup_postinc
                    elif form_type == "dn_an":
                        def _setup_dn_an(cpu, mem, _sv=src_val, _dv=dst_val,
                                         _sr=src_reg, _dr=dst_reg):
                            cpu.w_reg(DATA_REGS[_sr], _sv & 0xFFFFFFFF)
                            cpu.w_reg(ADDR_REGS[_dr], _dv & 0xFFFFFFFF)
                        test_ctx["setup"] = _setup_dn_an

                    desc = f"{indiv_mnemonic}.{sz} {val_desc} ccr={ccr_desc}"
                    initial_ccr = {k: v for k, v in ccr_state.items() if k != "desc"}

                    yield (asm_text, code_bytes, sz, src_val, dst_val,
                           src_reg, dst_reg, initial_ccr, desc, test_ctx)


# ── SP test case generation ───────────────────────────────────────────────

def generate_sp_tests(inst, tmpdir):
    """Generate SP verification test cases for one instruction from KB data.

    Uses predict_sp() for expected SP values where KB sp_effects exist.
    MOVEM has no fixed sp_effects (delta depends on register list count × size),
    so its SP prediction is computed directly from test parameters.

    Yields (asm_text, code_bytes, setup_fn, predicted_sp, predicted_pc, desc,
            predicted_ccr) tuples. predicted_ccr is None except for instructions
    that load CCR from memory (RTR).
    """
    mnemonic = inst["mnemonic"]
    pc_effects = inst.get("pc_effects", {})
    flow_type = pc_effects.get("flow", {}).get("type", "sequential")

    if mnemonic == "PEA":
        for asm, desc_suffix in [("pea (a0)", "ind"), ("pea 4(a0)", "disp")]:
            code = assemble(asm, tmpdir)
            if code:
                def setup(cpu, mem, _a=SCRATCH_ADDR):
                    cpu.w_reg(Register.A0, _a)
                pred_sp = predict_sp(inst, STACK_ADDR)
                yield (asm, code, setup, pred_sp,
                       CODE_ADDR + _instr_size(code), f"pea {desc_suffix}", None)

    elif mnemonic == "JSR":
        target = SCRATCH_ADDR
        asm = f"jsr ${target:x}"
        code = assemble(asm, tmpdir)
        if code:
            def setup(cpu, mem, _t=target):
                mem.w16(_t, NOP_OPWORD)  # NOP at target (from KB)
            pred_sp = predict_sp(inst, STACK_ADDR)
            yield (asm, code, setup, pred_sp, target, "jsr abs", None)

    elif mnemonic == "BSR":
        asm = "bsr.w .t\nnop\n.t:"
        code = assemble(asm, tmpdir)
        if code:
            # Target = after BSR + NOP (first two instructions);
            # remaining bytes are hunk padding, not real code.
            instrs = disasm_bytes(code)
            target = CODE_ADDR + instrs[0].size + instrs[1].size
            pred_sp = predict_sp(inst, STACK_ADDR)
            yield (asm, code, lambda cpu, mem: None, pred_sp, target,
                   "bsr.w forward", None)

    elif mnemonic == "RTS":
        asm = "rts"
        code = assemble(asm, tmpdir)
        if code:
            return_addr = SCRATCH_ADDR
            def setup(cpu, mem, _ra=return_addr):
                cpu.w_sp(STACK_ADDR - 4)
                mem.w32(STACK_ADDR - 4, _ra)
                mem.w16(_ra, NOP_OPWORD)  # NOP at return target (from KB)
            # RTS pops 4 bytes: SP goes from STACK_ADDR-4 to STACK_ADDR
            pred_sp = predict_sp(inst, STACK_ADDR - 4)
            yield (asm, code, setup, pred_sp, return_addr, "rts", None)

    elif mnemonic == "LINK":
        for displacement, desc in [(-8, "link a6,#-8"), (-256, "link a6,#-256"),
                                    (0, "link a6,#0")]:
            asm = f"link a6,#{displacement}"
            code = assemble(asm, tmpdir)
            if code:
                pred_sp = predict_sp(inst, STACK_ADDR, displacement=displacement)
                yield (asm, code, lambda cpu, mem: None, pred_sp,
                       CODE_ADDR + _instr_size(code), desc, None)

    elif mnemonic == "UNLK":
        asm = "unlk a6"
        code = assemble(asm, tmpdir)
        if code:
            frame_ptr = STACK_ADDR - 100
            saved_a6 = 0x12345678
            def setup(cpu, mem, _fp=frame_ptr, _sa=saved_a6):
                cpu.w_reg(Register.A6, _fp)
                mem.w32(_fp, _sa)
            # sp_effects: [load_from_reg An, increment 4]
            # predict_sp resolves load_from_reg via reg_state
            pred_sp = predict_sp(inst, STACK_ADDR,
                                 reg_state={"A6": frame_ptr})
            yield (asm, code, setup, pred_sp,
                   CODE_ADDR + _instr_size(code), "unlk a6", None)

    elif mnemonic == "MOVEM":
        # MOVEM push: reg-to-mem with -(A7) — SP decreases by N × size
        # MOVEM pop: mem-to-reg with (A7)+ — SP increases by N × size
        for sz in inst.get("sizes", []):
            sz_bytes = _size_byte_count[sz]
            # Push 3 registers: D0-D2
            push_asm = f"movem.{sz} d0-d2,-(a7)"
            push_code = assemble(push_asm, tmpdir)
            if push_code:
                n_regs = 3
                def setup_push(cpu, mem):
                    cpu.w_reg(Register.D0, 0x11111111)
                    cpu.w_reg(Register.D1, 0x22222222)
                    cpu.w_reg(Register.D2, 0x33333333)
                pred_sp = STACK_ADDR - n_regs * sz_bytes
                yield (push_asm, push_code, setup_push, pred_sp,
                       CODE_ADDR + _instr_size(push_code),
                       f"movem.{sz} push d0-d2", None)

            # Pop 3 registers: D3-D5 (from pre-pushed data)
            pop_asm = f"movem.{sz} (a7)+,d3-d5"
            pop_code = assemble(pop_asm, tmpdir)
            if pop_code:
                n_regs = 3
                pop_base = STACK_ADDR - n_regs * sz_bytes
                def setup_pop(cpu, mem, _base=pop_base, _szb=sz_bytes):
                    # Write 3 values below stack for popping
                    for i in range(3):
                        _mem_write(mem, _base + i * _szb, 0xAA + i, _szb)
                    cpu.w_sp(_base)
                pred_sp = pop_base + n_regs * sz_bytes
                yield (pop_asm, pop_code, setup_pop, pred_sp,
                       CODE_ADDR + _instr_size(pop_code),
                       f"movem.{sz} pop d3-d5", None)

    elif mnemonic == "RTR":
        # RTR pops CCR (2 bytes) then PC (4 bytes) from stack
        asm = "rtr"
        code = assemble(asm, tmpdir)
        if code:
            return_addr = SCRATCH_ADDR
            # Push a known CCR value (X=1, N=0, Z=1, V=0, C=1 = 0x15)
            test_ccr_word = _CCR_MASK & 0x0015  # X=1, Z=1, C=1
            # KB sp_effects: [increment 2, increment 4] — total 6 bytes
            rtr_base = STACK_ADDR - predict_sp(inst, 0)  # how much RTR pops
            def setup_rtr(cpu, mem, _ra=return_addr, _ccr=test_ccr_word,
                          _base=rtr_base):
                cpu.w_sp(_base)
                mem.w16(_base, _ccr)           # CCR word
                mem.w32(_base + 2, _ra)        # return address
                mem.w16(_ra, NOP_OPWORD)       # NOP at return target
            pred_sp = predict_sp(inst, rtr_base)
            # Predict CCR from the stacked value using KB ccr_bit_positions
            pred_ccr = {
                "X": 1 if test_ccr_word & CCR_X else 0,
                "N": 1 if test_ccr_word & CCR_N else 0,
                "Z": 1 if test_ccr_word & CCR_Z else 0,
                "V": 1 if test_ccr_word & CCR_V else 0,
                "C": 1 if test_ccr_word & CCR_C else 0,
            }
            yield (asm, code, setup_rtr, pred_sp, return_addr, "rtr", pred_ccr)


# ── Main test runner ──────────────────────────────────────────────────────

def run_tests(filter_mnemonic=None, verbose=False):
    """Run execution verification tests."""
    total = 0
    passed = 0
    failed = 0
    cc_mismatches = 0
    sp_mismatches = 0
    pc_mismatches = 0
    failures = []
    tested_mnemonics = set()

    machine = make_machine()

    with tempfile.TemporaryDirectory() as tmpdir:
        # ── Phase 1: CC verification (KB-driven discovery) ──
        cc_testable = discover_cc_testable_instructions()
        if verbose:
            print(f"CC-testable instructions: {len(cc_testable)}")

        for mnemonic, inst, form_info in cc_testable:
            if filter_mnemonic:
                # Match against combined or individual mnemonics
                filter_up = filter_mnemonic.upper()
                indivs = [m.upper() for m in _split_combined_mnemonic(mnemonic)]
                if filter_up != mnemonic.upper() and filter_up not in indivs:
                    continue

            # Track per-individual-mnemonic results for combined entries
            sub_counts = {}  # {indiv_mnemonic: [count, pass]}
            form_type, src_reg, dst_reg = form_info

            for (asm_text, code_bytes, sz, src_val, dst_val,
                 _src_reg, _dst_reg, initial_ccr, desc, ctx) in generate_cc_tests(inst, form_info, tmpdir):

                # Extract individual mnemonic from desc for tracking
                indiv = desc.split(".")[0]
                counts = sub_counts.setdefault(indiv, [0, 0])

                total += 1
                counts[0] += 1

                cpu = machine.cpu
                _reset_cpu(machine)

                # Set up operands — ctx may override default register setup
                setup_fn = ctx.get("setup")
                if setup_fn:
                    setup_fn(cpu, machine.mem)
                else:
                    if _src_reg is not None:
                        cpu.w_reg(DATA_REGS[_src_reg], src_val & 0xFFFFFFFF)
                    cpu.w_reg(DATA_REGS[_dst_reg], dst_val & 0xFFFFFFFF)

                set_ccr(cpu, x=initial_ccr["X"], n=initial_ccr["N"],
                        z=initial_ccr["Z"], v=initial_ccr["V"], c=initial_ccr["C"])
                ccr_before = read_ccr(cpu)

                # Predict CC from KB — single-op uses implicit_operand from KB
                # when the formula references it. If the formula doesn't
                # reference "source" or "implicit", pred_src is unused.
                if form_type == "single_op":
                    formula = inst.get("compute_formula", {})
                    terms = formula.get("terms", [])
                    if "implicit" in terms or "source" in terms:
                        pred_src = inst.get("implicit_operand")
                        if pred_src is None:
                            raise RuntimeError(
                                f"{mnemonic}: formula uses 'implicit'/'source' "
                                f"but no implicit_operand in KB")
                    else:
                        pred_src = 0  # formula doesn't use source value
                else:
                    pred_src = src_val
                predicted_cc = predict_cc(inst, sz, pred_src, dst_val, ccr_before, ctx)

                after = load_and_execute(machine, code_bytes)

                # Compare CC flags
                ok = True
                details = []
                for flag in ["X", "N", "Z", "V", "C"]:
                    pred = predicted_cc[flag]
                    actual = after["ccr"][flag]
                    if pred is None:
                        continue  # undefined rule, skip
                    if pred != actual:
                        ok = False
                        details.append(f"{flag}: pred={pred} actual={actual}")

                if ok:
                    passed += 1
                    counts[1] += 1
                    if verbose:
                        print(f"  OK   {desc}")
                else:
                    failed += 1
                    cc_mismatches += 1
                    failures.append((desc, asm_text, "; ".join(details)))
                    if verbose:
                        print(f"  FAIL {desc}: {'; '.join(details)}")

            for indiv, (count, pass_count) in sorted(sub_counts.items()):
                tested_mnemonics.add(indiv)
                if not verbose:
                    status = "OK" if pass_count == count else "FAIL"
                    print(f"  {status:4s} {indiv}: {pass_count}/{count}")

        # ── Phase 2: SP-effect verification (KB-driven discovery) ──
        sp_testable = discover_sp_testable_instructions()
        sp_by_mnemonic = {}

        for mnemonic, inst in sp_testable:
            if filter_mnemonic and filter_mnemonic.upper() != mnemonic.upper():
                continue

            for (asm_text, code_bytes, setup_fn,
                 predicted_sp, predicted_pc, desc,
                 predicted_ccr) in generate_sp_tests(inst, tmpdir):

                total += 1
                counts = sp_by_mnemonic.setdefault(mnemonic, [0, 0])
                counts[0] += 1

                _reset_cpu(machine)
                cpu = machine.cpu
                mem = machine.mem
                setup_fn(cpu, mem)

                sp_before = cpu.r_sp()
                after = load_and_execute(machine, code_bytes)

                ok = True
                details = []

                if after["sp"] != predicted_sp:
                    ok = False
                    details.append(
                        f"SP: pred=0x{predicted_sp:x} actual=0x{after['sp']:x} "
                        f"(delta pred={predicted_sp - sp_before:+d} "
                        f"actual={after['sp'] - sp_before:+d})"
                    )
                    sp_mismatches += 1

                if after["pc"] != predicted_pc:
                    ok = False
                    details.append(f"PC: pred=0x{predicted_pc:x} actual=0x{after['pc']:x}")
                    pc_mismatches += 1

                if predicted_ccr is not None:
                    for flag in ("X", "N", "Z", "V", "C"):
                        if after["ccr"][flag] != predicted_ccr[flag]:
                            ok = False
                            details.append(
                                f"CCR.{flag}: pred={predicted_ccr[flag]} "
                                f"actual={after['ccr'][flag]}")
                            cc_mismatches += 1

                if ok:
                    passed += 1
                    counts[1] += 1
                    if verbose:
                        print(f"  OK   {desc}")
                else:
                    failed += 1
                    failures.append((desc, asm_text, "; ".join(details)))
                    if verbose:
                        print(f"  FAIL {desc}: {'; '.join(details)}")

        for mnemonic, (count, pass_count) in sorted(sp_by_mnemonic.items()):
            tested_mnemonics.add(mnemonic)
            if not verbose:
                status = "OK" if pass_count == count else "FAIL"
                print(f"  {status:4s} {mnemonic}: {pass_count}/{count}")

        # ── Phase 3: CCR/SR manipulation verification ──
        ccr_op_testable = discover_ccr_op_testable_instructions()
        if verbose:
            print(f"CCR/SR-op-testable instructions: {len(ccr_op_testable)}")

        for mnemonic, inst in ccr_op_testable:
            if filter_mnemonic and filter_mnemonic.upper() != mnemonic.upper():
                continue

            sub_count = [0, 0]
            for (asm_text, code_bytes, src_val,
                 initial_ccr, desc) in generate_ccr_op_tests(inst, tmpdir):

                total += 1
                sub_count[0] += 1

                cpu = machine.cpu
                _reset_cpu(machine)

                # For MOVE to CCR with Dn source, set D0 to the source value
                if "MOVE" in mnemonic:
                    cpu.w_reg(DATA_REGS[0], src_val & 0xFFFF)

                set_ccr(cpu, x=initial_ccr["X"], n=initial_ccr["N"],
                        z=initial_ccr["Z"], v=initial_ccr["V"], c=initial_ccr["C"])
                ccr_before = read_ccr(cpu)

                # Predict CC: src_val is the immediate/source, dst unused
                predicted_cc = predict_cc(inst, "b", src_val, 0, ccr_before)

                after = load_and_execute(machine, code_bytes)

                ok = True
                details = []
                for flag in ["X", "N", "Z", "V", "C"]:
                    pred = predicted_cc[flag]
                    actual = after["ccr"][flag]
                    if pred is None:
                        continue
                    if pred != actual:
                        ok = False
                        details.append(f"{flag}: pred={pred} actual={actual}")

                if ok:
                    passed += 1
                    sub_count[1] += 1
                    if verbose:
                        print(f"  OK   {desc}")
                else:
                    failed += 1
                    cc_mismatches += 1
                    failures.append((desc, asm_text, "; ".join(details)))
                    if verbose:
                        print(f"  FAIL {desc}: {'; '.join(details)}")

            tested_mnemonics.add(mnemonic)
            if not verbose:
                status = "OK" if sub_count[1] == sub_count[0] else "FAIL"
                print(f"  {status:4s} {mnemonic}: {sub_count[1]}/{sub_count[0]}")

        # ── Phase 4: Register/flow verification for non-CC instructions ──
        reg_testable = discover_register_testable_instructions()
        if verbose:
            print(f"Register/flow-testable instructions: {len(reg_testable)}")

        reg_by_mnemonic = {}
        for mnemonic, inst, category in reg_testable:
            if filter_mnemonic and filter_mnemonic.upper() != mnemonic.upper():
                continue

            for (desc, code_bytes, setup_fn,
                 verify_fn) in generate_register_tests(mnemonic, inst, category, tmpdir):

                total += 1
                counts = reg_by_mnemonic.setdefault(mnemonic, [0, 0])
                counts[0] += 1

                _reset_cpu(machine)
                cpu = machine.cpu
                mem = machine.mem
                setup_fn(cpu, mem)

                after = load_and_execute(machine, code_bytes)

                ok, details = verify_fn(after)
                if ok:
                    passed += 1
                    counts[1] += 1
                    if verbose:
                        print(f"  OK   {desc}")
                else:
                    failed += 1
                    failures.append((desc, "", "; ".join(details)))
                    if verbose:
                        print(f"  FAIL {desc}: {'; '.join(details)}")

        for mnemonic, (count, pass_count) in sorted(reg_by_mnemonic.items()):
            tested_mnemonics.add(mnemonic)
            if not verbose:
                status = "OK" if pass_count == count else "FAIL"
                print(f"  {status:4s} {mnemonic}: {pass_count}/{count}")

        # ── Phase 5: Condition test verification (Scc/Bcc/DBcc) ──
        cond_testable = discover_condition_testable_instructions()
        if verbose:
            print(f"Condition-testable instructions: {len(cond_testable)}")

        cond_by_mnemonic = {}
        for mnemonic, inst, category in cond_testable:
            if filter_mnemonic:
                filter_up = filter_mnemonic.upper()
                if filter_up not in (mnemonic.upper(), "SCC", "BCC", "DBCC"):
                    # Also allow filtering by individual condition (e.g. BEQ, SNE)
                    if not any(filter_up == f"{p}{cc.upper()}"
                               for cc in KB_META.get("cc_test_definitions", {})
                               for p in ("S", "B", "DB")):
                        continue

            for (desc, code_bytes, setup_fn,
                 verify_fn, indiv) in generate_condition_tests(mnemonic, inst, category, tmpdir):

                # If filtering by individual condition mnemonic, skip non-matches
                if filter_mnemonic:
                    filter_up = filter_mnemonic.upper()
                    if filter_up != mnemonic.upper() and filter_up != indiv:
                        continue

                total += 1
                counts = cond_by_mnemonic.setdefault(indiv, [0, 0])
                counts[0] += 1

                _reset_cpu(machine)
                cpu = machine.cpu
                mem = machine.mem
                setup_fn(cpu, mem)

                after = load_and_execute(machine, code_bytes)

                ok, details = verify_fn(after)
                if ok:
                    passed += 1
                    counts[1] += 1
                    if verbose:
                        print(f"  OK   {desc}")
                else:
                    failed += 1
                    failures.append((desc, "", "; ".join(details)))
                    if verbose:
                        print(f"  FAIL {desc}: {'; '.join(details)}")

        for indiv, (count, pass_count) in sorted(cond_by_mnemonic.items()):
            tested_mnemonics.add(indiv)
            if not verbose:
                status = "OK" if pass_count == count else "FAIL"
                print(f"  {status:4s} {indiv}: {pass_count}/{count}")

    machine.cleanup()

    # Summary
    print()
    print(f"=== M68K Execution Verification Results ===")
    print(f"Passed: {passed}/{total}  Failed: {failed}")
    print(f"CC mismatches: {cc_mismatches}  SP mismatches: {sp_mismatches}  "
          f"PC mismatches: {pc_mismatches}")
    print(f"Mnemonics tested: {len(tested_mnemonics)}")

    if failures:
        print(f"\n--- Failures ({len(failures)}) ---")
        for desc, asm, reason in failures[:50]:
            print(f"  FAIL {desc}")
            print(f"       asm:    {asm}")
            print(f"       reason: {reason}")

    return failed == 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="M68K execution verification: KB predictions vs Musashi oracle"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--filter", "-f", help="Test only this mnemonic")
    args = parser.parse_args()

    success = run_tests(filter_mnemonic=args.filter, verbose=args.verbose)
    sys.exit(0 if success else 1)
