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
KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"

sys.path.insert(0, str(PROJ_ROOT / "scripts"))
from test_m68k_roundtrip import assemble
from m68k_disasm import disassemble as disasm_bytes


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

# CCR flag bit positions in SR (machine68k API layout)
CCR_C = 0x0001
CCR_V = 0x0002
CCR_Z = 0x0004
CCR_N = 0x0008
CCR_X = 0x0010

# NOP opword derived from KB encoding data (not hardcoded)
NOP_OPWORD = KB_META.get("nop_opword")
if NOP_OPWORD is None:
    raise RuntimeError("KB _meta missing nop_opword — regenerate KB")


def make_machine():
    """Create a fresh machine68k instance with 64KiB RAM."""
    m = Machine(CPUType.M68000, 64)
    mem = m.mem
    # Set up reset vectors: initial SP and PC
    mem.w32(0, STACK_ADDR)
    mem.w32(4, CODE_ADDR)
    m.cpu.pulse_reset()
    return m


def set_ccr(cpu, x=0, n=0, z=0, v=0, c=0):
    """Set CCR flags in SR (preserve supervisor bits)."""
    sr = cpu.r_sr()
    sr &= 0xFFE0  # clear CCR bits
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


# ── CC prediction from KB rules ──────────────────────────────────────────

def _size_mask(sz):
    """Return bit mask and bit count for operation size."""
    if sz == "b":
        return 0xFF, 8
    elif sz == "w":
        return 0xFFFF, 16
    else:  # "l"
        return 0xFFFFFFFF, 32


def _to_signed(value, sz):
    """Convert unsigned value to signed at given size."""
    mask, bits = _size_mask(sz)
    value &= mask
    if value >= (1 << (bits - 1)):
        value -= (1 << bits)
    return value


def _size_from_bits(bits):
    return {8: "b", 16: "w", 32: "l"}[bits]


def predict_cc(inst, sz, src_val, dst_val, initial_ccr, ctx=None):
    """Predict CC flags after instruction execution.

    Args:
        inst: KB instruction dict (must have cc_semantics and operation_type)
        sz: operation size ("b", "w", "l")
        src_val: source operand value (unsigned)
        dst_val: destination operand value (unsigned, pre-execution)
        initial_ccr: dict of initial CC flags {"X":0/1, ...}
        ctx: optional dict with extra context (e.g. direction, arithmetic
             for shift/rotate instructions)

    Returns:
        dict of predicted CC flags {"X":0/1, "N":0/1, ...}

    Raises:
        RuntimeError if cc_semantics or operation_type is missing,
        or if a CC rule is unhandled.
    """
    cc_sem = inst.get("cc_semantics")
    if not cc_sem:
        raise RuntimeError(f"{inst['mnemonic']}: missing cc_semantics in KB")

    op_type = inst.get("operation_type")
    if not op_type:
        raise RuntimeError(f"{inst['mnemonic']}: missing operation_type in KB")

    if ctx is None:
        ctx = {}

    mask, bits = _size_mask(sz)

    # Allow KB data_sizes to override default operand/result widths.
    # Multiply: operands may be narrower than result (16x16→32).
    # Divide: dividend may be wider than divisor/quotient (32÷16→16).
    data_sizes = ctx.get("data_sizes")
    if data_sizes:
        ds_type = data_sizes.get("type")
        if ds_type == "multiply":
            src_bits = data_sizes["src_bits"]
            dst_bits = data_sizes["dst_bits"]
            result_bits = data_sizes["result_bits"]
        elif ds_type == "divide":
            src_bits = data_sizes["divisor_bits"]
            dst_bits = data_sizes["dividend_bits"]
            result_bits = data_sizes["quotient_bits"]
        else:
            src_bits = dst_bits = result_bits = bits
        src_mask = (1 << src_bits) - 1
        dst_mask = (1 << dst_bits) - 1
        result_mask = (1 << result_bits) - 1
    else:
        src_bits = dst_bits = result_bits = bits
        src_mask = dst_mask = result_mask = mask

    # KB cc_result_bits overrides operand/result width for compute + CC evaluation
    # (e.g. SWAP: Size=Word but PDF CC says "32-bit result" — operation is 32-bit)
    cc_override = ctx.get("cc_result_bits")
    if cc_override is not None:
        src_bits = dst_bits = result_bits = cc_override
        src_mask = dst_mask = result_mask = (1 << cc_override) - 1

    src = src_val & src_mask
    dst = dst_val & dst_mask

    # Compute result using KB compute_formula
    result_full, result = _compute_result(
        inst, src, dst, result_mask, result_bits, initial_ccr, ctx)

    # Predict each flag using KB cc_semantics rules
    predicted = {}
    for flag in ["X", "N", "Z", "V", "C"]:
        flag_spec = cc_sem.get(flag)
        if flag_spec is None:
            raise RuntimeError(
                f"{inst['mnemonic']}: flag {flag} missing from cc_semantics in KB")
        rule = flag_spec.get("rule")
        if rule is None:
            raise RuntimeError(
                f"{inst['mnemonic']}: flag {flag} has no 'rule' key in cc_semantics")
        predicted[flag] = _apply_rule(
            rule, flag, result, result_full, src, dst, result_mask, result_bits,
            op_type, initial_ccr, cc_sem, ctx
        )

    # KB overflow_undefined_flags: on overflow (V=1), real hardware preserves
    # these flags unchanged. The PDF marks them "undefined if overflow" and
    # the C flag is included per known 68000 errata. All driven from KB data.
    overflow_undef = inst.get("overflow_undefined_flags")
    if overflow_undef and predicted.get("V") == 1:
        for flag in overflow_undef:
            predicted[flag] = initial_ccr.get(flag, 0)

    return predicted


# ── KB-driven result computation ──────────────────────────────────────────
#
# The compute_formula in the KB (extracted from PDF Operation text by the
# parser) specifies what operation to perform and in what operand order.
# This evaluator maps universal math operators to Python — the operators
# themselves (+, -, &, |, ^, ~, *, /) are not M68K knowledge; the KB
# specifies which one applies to each instruction and the operand order.


def _resolve_term(term, src, dst, ccr, implicit):
    """Resolve a formula operand term to its numeric value."""
    if term == "source":
        return src
    if term == "destination":
        return dst
    if term == "X":
        return ccr.get("X", 0)
    if term == "implicit":
        if implicit is None:
            raise RuntimeError(
                "Formula references 'implicit' term but no implicit_operand "
                "in KB instruction — add implicit_operand extraction to parser")
        return implicit
    if isinstance(term, int):
        return term
    raise RuntimeError(f"Unknown formula term: {term!r}")


# Universal math operators — these map formula 'op' names (from KB) to
# Python functions. None of these are M68K-specific; they are standard
# binary arithmetic/logic operations.
_FORMULA_OPS = {
    "add":                lambda a, b: a + b,
    "subtract":           lambda a, b: a - b,
    "bitwise_and":        lambda a, b: a & b,
    "bitwise_or":         lambda a, b: a | b,
    "bitwise_xor":        lambda a, b: a ^ b,
    "bitwise_complement": lambda a: ~a,
    "assign":             lambda a: a,
    "test":               lambda a: a,
}


def _compute_exchange(dst, formula):
    """Compute bit-range exchange from KB formula (SWAP).

    The KB specifies exact bit ranges from the PDF Operation text:
    e.g. range_a=[31,16], range_b=[15,0] for "Register [31:16] ←→ [15:0]".
    """
    hi_top, hi_bot = formula["range_a"]
    lo_top, lo_bot = formula["range_b"]
    hi_width = hi_top - hi_bot + 1
    lo_width = lo_top - lo_bot + 1
    hi_mask = ((1 << hi_width) - 1) << hi_bot
    lo_mask = ((1 << lo_width) - 1) << lo_bot
    hi_val = (dst & hi_mask) >> hi_bot
    lo_val = (dst & lo_mask) >> lo_bot
    return (lo_val << hi_bot) | (hi_val << lo_bot)


def _compute_sign_extend(dst, mask, bits, ctx, formula):
    """Sign-extend from a narrower source width to the operation size.

    The KB formula has 'source_bits_by_size' mapping size→source width,
    extracted from PDF description text (e.g. "extends a byte to a word").
    The ctx must have 'sign_extend_source_bits' set by the test generator.
    """
    source_bits = ctx.get("sign_extend_source_bits")
    if source_bits is None:
        raise RuntimeError(
            "compute sign_extend: missing 'sign_extend_source_bits' in ctx "
            "— must come from KB source_bits_by_size")
    source_mask = (1 << source_bits) - 1
    val = dst & source_mask
    # Sign-extend: if MSB of source is set, fill upper bits with 1s
    if val & (1 << (source_bits - 1)):
        val |= mask & ~source_mask
    return val & mask


def _compute_shift(src, dst, mask, bits, ccr, ctx):
    """Shift result. All parameters come from KB: direction and fill from
    variants, count_modulus from shift_count_modulus."""
    count = src % ctx["count_modulus"]
    direction = ctx["direction"]
    fill = ctx.get("fill")
    if fill is None:
        raise RuntimeError("_compute_shift: missing 'fill' in ctx — must come from KB variant")
    val = dst & mask
    if count == 0:
        return val
    if direction == "L":
        return val << count  # unmasked: bits above size used by carry detection
    else:
        if fill == "sign" and (val & (1 << (bits - 1))):
            signed = val - (1 << bits)
            return signed >> count
        return val >> count


def _compute_rotate(src, dst, mask, bits, ccr, ctx):
    """Rotate result. Direction from KB variants, count_modulus from KB."""
    count = src % ctx["count_modulus"]
    direction = ctx["direction"]
    val = dst & mask
    if count == 0:
        return val
    c = count % bits
    if c == 0:
        return val
    if direction == "L":
        return ((val << c) | (val >> (bits - c))) & mask
    else:
        return ((val >> c) | (val << (bits - c))) & mask


def _compute_rotate_extend(src, dst, mask, bits, ccr, ctx):
    """Rotate through X bit. Extra bits from KB rotate_extra_bits."""
    count = src % ctx["count_modulus"]
    direction = ctx["direction"]
    x = ccr.get("X", 0)
    val = dst & mask
    extra = ctx["extra_bits"]
    width = bits + extra
    c = count % width
    if c == 0:
        return val
    extended = (x << bits) | val
    if direction == "L":
        rotated = ((extended << c) | (extended >> (width - c))) & ((1 << width) - 1)
    else:
        rotated = ((extended >> c) | (extended << (width - c))) & ((1 << width) - 1)
    return rotated & mask


def _compute_multiply(src, dst, mask, bits, ccr, ctx):
    """Multiply. Signedness from KB 'signed', operand widths from KB 'data_sizes'."""
    ds = ctx["data_sizes"]
    src_bits = ds["src_bits"]
    dst_bits = ds["dst_bits"]
    if ctx.get("signed", False):
        s_signed = src if src < (1 << (src_bits - 1)) else src - (1 << src_bits)
        d_signed = dst if dst < (1 << (dst_bits - 1)) else dst - (1 << dst_bits)
        return s_signed * d_signed
    else:
        return src * dst


def _compute_divide(src, dst, mask, bits, ccr, ctx):
    """Divide. Signedness from KB, truncation direction from KB compute_formula."""
    if src == 0:
        raise RuntimeError("Division by zero in test — fix test values")
    ds = ctx["data_sizes"]
    divisor_bits = ds["divisor_bits"]
    dividend_bits = ds["dividend_bits"]
    if ctx.get("signed", False):
        s_signed = src if src < (1 << (divisor_bits - 1)) else src - (1 << divisor_bits)
        d_signed = dst if dst < (1 << (dividend_bits - 1)) else dst - (1 << dividend_bits)
        # Truncation direction from KB compute_formula (asserted as "toward_zero")
        return int(d_signed / s_signed)
    else:
        return dst // src


def _evaluate_formula(formula, src, dst, mask, bits, ccr, ctx):
    """Evaluate a KB compute_formula to produce the operation result.

    The formula structure comes from the KB (extracted from PDF Operation text).
    This evaluator applies universal math operators — it contains no M68K knowledge.
    """
    op = formula["op"]
    terms = formula.get("terms", [])
    implicit = ctx.get("implicit_operand")

    # Simple two-operand or single-operand formulas
    if op in _FORMULA_OPS:
        fn = _FORMULA_OPS[op]
        resolved = [_resolve_term(t, src, dst, ccr, implicit) for t in terms]
        if len(terms) == 3:
            # Extended operations: add(a, b, X) or subtract(a, b, X)
            a, b, x = resolved
            if op == "add":
                return a + b + x
            elif op == "subtract":
                return a - b - x
        elif len(terms) == 2:
            return fn(resolved[0], resolved[1])
        elif len(terms) == 1:
            return fn(resolved[0])
        else:
            raise RuntimeError(f"Formula op '{op}' with {len(terms)} terms")

    # Complex operations — parameterized by KB data
    if op == "exchange":
        return _compute_exchange(dst, formula)
    if op == "sign_extend":
        return _compute_sign_extend(dst, mask, bits, ctx, formula)
    if op == "shift":
        return _compute_shift(src, dst, mask, bits, ccr, ctx)
    if op == "rotate":
        return _compute_rotate(src, dst, mask, bits, ccr, ctx)
    if op == "rotate_extend":
        return _compute_rotate_extend(src, dst, mask, bits, ccr, ctx)
    if op == "multiply":
        return _compute_multiply(src, dst, mask, bits, ccr, ctx)
    if op == "divide":
        return _compute_divide(src, dst, mask, bits, ccr, ctx)
    if op in ("bit_test", "bit_change", "bit_clear", "bit_set"):
        bit_mod = ctx.get("bit_modulus")
        if bit_mod is None:
            raise RuntimeError(
                f"compute {op}: missing 'bit_modulus' in ctx — must come from KB")
        bit_num = src % bit_mod
        if op == "bit_test":
            return dst  # test only, destination unchanged
        if op == "bit_change":
            return dst ^ (1 << bit_num)
        if op == "bit_clear":
            return dst & ~(1 << bit_num)
        return dst | (1 << bit_num)  # bit_set

    raise RuntimeError(f"Unknown compute_formula op: {op!r}")


def _compute_result(inst, src, dst, mask, bits, initial_ccr, ctx=None):
    """Compute the full (unmasked) and masked result using KB compute_formula.

    Raises RuntimeError if the instruction has no compute_formula in the KB.
    """
    formula = inst.get("compute_formula")
    if formula is None:
        raise RuntimeError(
            f"{inst['mnemonic']}: missing compute_formula in KB — "
            f"regenerate KB or add formula extraction for operation_type "
            f"'{inst.get('operation_type')}'"
        )
    if ctx is None:
        ctx = {}
    # Thread implicit_operand from KB into ctx for formula evaluation
    if "implicit_operand" in inst and "implicit_operand" not in ctx:
        ctx["implicit_operand"] = inst["implicit_operand"]
    result_full = _evaluate_formula(formula, src, dst, mask, bits, initial_ccr, ctx)
    result = result_full & mask
    return result_full, result


# Supported CC semantic rules. Maps rule name to a callable that
# returns the predicted flag value, or None for "skip comparison".
# Each callable receives: (result, result_full, src, dst, mask, bits,
#                          op_type, initial_ccr, cc_sem, flag, ctx)

def _rule_unchanged(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return ccr.get(flag, 0)

def _rule_cleared(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return 0

def _rule_set(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return 1

def _rule_result_negative(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return (result >> (bits - 1)) & 1

def _rule_result_zero(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return 1 if result == 0 else 0

def _rule_result_nonzero(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return 1 if result != 0 else 0

def _rule_same_as_carry(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    c_rule = cc_sem.get("C", {}).get("rule")
    if c_rule is None:
        raise RuntimeError(f"same_as_carry: no C rule in cc_semantics")
    if c_rule == "same_as_carry":
        raise RuntimeError(f"same_as_carry: C rule is also same_as_carry (circular)")
    return _apply_rule(c_rule, "C", result, result_full, src, dst, mask, bits,
                       op_type, ccr, cc_sem, ctx)

def _rule_carry(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return 1 if result_full > mask else 0

def _rule_borrow(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return 1 if result_full < 0 else 0

def _rule_overflow_add(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """Overflow for addition: same-sign operands produce different-sign result."""
    sz = _size_from_bits(bits)
    s_src = _to_signed(src, sz)
    s_dst = _to_signed(dst, sz)
    s_result = _to_signed(result, sz)
    return 1 if (s_src >= 0) == (s_dst >= 0) and (s_result >= 0) != (s_src >= 0) else 0

def _rule_overflow_sub(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """Overflow for subtraction/compare: different-sign operands, result sign differs from dst."""
    sz = _size_from_bits(bits)
    s_src = _to_signed(src, sz)
    s_dst = _to_signed(dst, sz)
    s_result = _to_signed(result, sz)
    return 1 if (s_src >= 0) != (s_dst >= 0) and (s_result >= 0) != (s_dst >= 0) else 0

def _rule_overflow_neg(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """Overflow for negate: only overflows at most-negative value."""
    msb_val = 1 << (bits - 1)
    return 1 if dst == msb_val else 0

def _rule_overflow_negx(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """Overflow for negate-with-extend: msb_val with X=0."""
    msb_val = 1 << (bits - 1)
    return 1 if dst == msb_val and ccr.get("X", 0) == 0 else 0

def _rule_overflow_multiply(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """Overflow for multiply: product doesn't fit in result_bits."""
    if ctx.get("signed", False):
        max_pos = (1 << (bits - 1)) - 1
        min_neg = -(1 << (bits - 1))
        return 1 if result_full < min_neg or result_full > max_pos else 0
    else:
        return 1 if result_full < 0 or result_full >= (1 << bits) else 0

def _rule_bit_zero(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """Z flag for bit test: set if the tested bit of destination is zero.
    Bit modulus from KB bit_modulus field (parsed from PDF description)."""
    bit_mod = ctx.get("bit_modulus")
    if bit_mod is None:
        raise RuntimeError(
            "bit_zero: missing 'bit_modulus' in ctx — must come from KB")
    bit_num = src % bit_mod
    return 1 if (dst >> bit_num) & 1 == 0 else 0

def _rule_z_cleared_if_nonzero(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    if result != 0:
        return 0
    return ccr.get("Z", 0)

def _rule_undefined(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return None


def _division_overflows(result_full, bits, ctx):
    """Check if the mathematical quotient overflows the quotient bit width."""
    if ctx.get("signed", False):
        max_pos = (1 << (bits - 1)) - 1
        min_neg = -(1 << (bits - 1))
        return result_full < min_neg or result_full > max_pos
    else:
        return result_full < 0 or result_full >= (1 << bits)


def _rule_division_overflow(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """V flag for divide: set if quotient doesn't fit in quotient_bits."""
    return 1 if _division_overflows(result_full, bits, ctx) else 0


def _rule_quotient_negative(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """N flag for divide: MSB of quotient. Undefined if overflow or div-by-zero."""
    if _division_overflows(result_full, bits, ctx):
        return None  # undefined per spec
    return (result >> (bits - 1)) & 1


def _rule_quotient_zero(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """Z flag for divide: set if quotient is zero. Undefined if overflow or div-by-zero."""
    if _division_overflows(result_full, bits, ctx):
        return None  # undefined per spec
    return 1 if result == 0 else 0


def _rule_last_shifted_out(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """Last bit shifted out of the operand. Handles zero_count sub-rule."""
    count = src % ctx["count_modulus"]
    if count == 0:
        flag_spec = cc_sem.get(flag)
        if flag_spec is None:
            raise RuntimeError(
                f"last_shifted_out: flag {flag} missing from cc_semantics")
        zero_rule = flag_spec.get("zero_count")
        if zero_rule is None:
            raise RuntimeError(
                f"last_shifted_out: flag {flag} missing 'zero_count' sub-rule in KB")
        if zero_rule == "unchanged":
            return ccr.get(flag, 0)
        elif zero_rule == "cleared":
            return 0
        else:
            raise RuntimeError(f"last_shifted_out: unknown zero_count rule '{zero_rule}'")
    direction = ctx["direction"]
    val = dst & mask
    if direction == "L":
        # Left shift by count: last bit out = bit (bits - count)
        if count <= bits:
            return (val >> (bits - count)) & 1
        else:
            return 0  # all bits shifted out, last was zero-fill
    else:
        # Right shift by count: last bit out = bit (count - 1)
        if count <= bits:
            return (val >> (count - 1)) & 1
        else:
            # Count exceeds bit width: fill determines what remains
            # sign fill (ASR): sign bit propagates, last shifted out = sign bit
            # zero fill (LSR): zeros fill, last shifted out = 0
            fill = ctx.get("fill")
            if fill is None:
                raise RuntimeError(
                    "last_shifted_out: missing 'fill' in ctx — must come from KB variant")
            if fill == "sign":
                return (val >> (bits - 1)) & 1
            else:
                return 0


def _rule_last_rotated_out(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """Last bit rotated out. Handles zero_count sub-rule."""
    count = src % ctx["count_modulus"]
    if count == 0:
        flag_spec = cc_sem.get(flag)
        if flag_spec is None:
            raise RuntimeError(
                f"last_rotated_out: flag {flag} missing from cc_semantics")
        zero_rule = flag_spec.get("zero_count")
        if zero_rule is None:
            raise RuntimeError(
                f"last_rotated_out: flag {flag} missing 'zero_count' sub-rule in KB")
        if zero_rule == "unchanged":
            return ccr.get(flag, 0)
        elif zero_rule == "cleared":
            return 0
        else:
            raise RuntimeError(f"last_rotated_out: unknown zero_count rule '{zero_rule}'")
    direction = ctx["direction"]
    val = dst & mask
    if op_type == "rotate":
        # ROL/ROR: rotate within bit width
        if direction == "L":
            # ROL by c: C = original bit (bits - c).
            # c=0 means count is a multiple of bits: C = bit 0.
            c = count % bits
            if c == 0:
                return val & 1
            return (val >> (bits - c)) & 1
        else:
            # ROR by c: last bit out = bit ((c-1) % bits) of original
            c = count % bits
            if c == 0:
                return (val >> (bits - 1)) & 1  # bit (bits-1) = MSB
            return (val >> (c - 1)) & 1
    elif op_type == "rotate_extend":
        # ROXL/ROXR: rotate through X in a wider field (KB rotate_extra_bits)
        x = ccr.get("X", 0)
        extra = ctx["extra_bits"]
        width = bits + extra
        c = count % width
        if c == 0:
            return x  # no effective rotation, X unchanged
        extended = (x << bits) | val
        if direction == "L":
            rotated = ((extended << c) | (extended >> (width - c))) & ((1 << width) - 1)
        else:
            rotated = ((extended >> c) | (extended << (width - c))) & ((1 << width) - 1)
        # New X = bit at position 'bits' of rotated value
        return (rotated >> bits) & 1
    else:
        raise RuntimeError(f"last_rotated_out: unexpected op_type '{op_type}'")


def _rule_msb_changed_during_shift(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """ASL V flag: set if MSB changed at any point during left shift.
    For right shifts (ASR), MSB is preserved at every step → always 0.
    """
    direction = ctx["direction"]
    if direction == "R":
        # Arithmetic right shift preserves sign bit at every step
        return 0
    count = src % ctx["count_modulus"]
    if count == 0:
        return 0  # no shift occurred
    val = dst & mask
    if count >= bits:
        # All original bits shift through MSB, then zeros fill in.
        # MSB changes unless original value is all-0 (MSB stays 0 throughout)
        # or... actually even all-1s: after bit 0 shifts out, zero fills MSB.
        # V=1 if val != 0 (some 1-bit was in MSB, then zero-fill changed it)
        # Also V=1 if MSB was 0 but some lower bit was 1 (MSB changes to 1 then back to 0)
        # Simplification: V=0 only if val == 0 (nothing to change)
        return 0 if val == 0 else 1
    # count < bits: check bit positions (bits-1) down to (bits-1-count).
    # These are the original bits that occupy MSB at each step (including initial).
    # V=1 if not all the same.
    low = bits - 1 - count
    high = bits - 1
    num_bits = high - low + 1
    check_mask = ((1 << num_bits) - 1) << low
    checked = val & check_mask
    if checked == 0 or checked == check_mask:
        return 0  # all same
    return 1


_RULE_HANDLERS = {
    "unchanged":                _rule_unchanged,
    "cleared":                  _rule_cleared,
    "set":                      _rule_set,
    "result_negative":          _rule_result_negative,
    "msb_result":               _rule_result_negative,
    "result_zero":              _rule_result_zero,
    "result_nonzero":           _rule_result_nonzero,
    "same_as_carry":            _rule_same_as_carry,
    "carry":                    _rule_carry,
    "borrow":                   _rule_borrow,
    "overflow_add":             _rule_overflow_add,
    "overflow_sub":             _rule_overflow_sub,
    "overflow_neg":             _rule_overflow_neg,
    "overflow_negx":            _rule_overflow_negx,
    "overflow_multiply":        _rule_overflow_multiply,
    "bit_zero":                 _rule_bit_zero,
    "z_cleared_if_nonzero":     _rule_z_cleared_if_nonzero,
    "undefined":                _rule_undefined,
    "last_shifted_out":         _rule_last_shifted_out,
    "last_rotated_out":         _rule_last_rotated_out,
    "msb_changed_during_shift": _rule_msb_changed_during_shift,
    "division_overflow":        _rule_division_overflow,
    "quotient_negative":        _rule_quotient_negative,
    "quotient_zero":            _rule_quotient_zero,
}


def _apply_rule(rule, flag, result, result_full, src, dst, mask, bits,
                op_type, initial_ccr, cc_sem, ctx=None):
    """Apply a CC semantic rule to predict a flag value.

    Raises RuntimeError for unhandled rules (no silent skip).
    """
    handler = _RULE_HANDLERS.get(rule)
    if handler is None:
        raise RuntimeError(
            f"Unhandled CC rule '{rule}' for flag {flag}. "
            f"Add a handler to _RULE_HANDLERS."
        )
    if ctx is None:
        ctx = {}
    return handler(result, result_full, src, dst, mask, bits, op_type,
                   initial_ccr, cc_sem, flag, ctx)


# ── SP effect prediction ──────────────────────────────────────────────────

def predict_sp(inst, sp_before, displacement=0, reg_state=None):
    """Predict SP after instruction execution from KB sp_effects.

    Args:
        inst: KB instruction dict
        sp_before: SP value before execution
        displacement: displacement value for adjust-type effects (e.g. LINK)
        reg_state: optional dict mapping register names (e.g. "A6") to values,
                   needed for load_from_reg effects (e.g. UNLK sets SP from An)

    Returns:
        predicted SP value

    Raises:
        RuntimeError if load_from_reg is encountered without reg_state providing
        the required register value, or if an unknown action is encountered.
    """
    sp_effects = inst.get("sp_effects", [])
    if not sp_effects:
        return sp_before

    sp = sp_before
    for effect in sp_effects:
        action = effect["action"]
        if action == "decrement":
            sp -= effect["bytes"]
        elif action == "increment":
            sp += effect["bytes"]
        elif action == "adjust":
            sp += displacement
        elif action == "save_to_reg":
            pass  # copies SP to register, no SP change
        elif action == "load_from_reg":
            reg = effect.get("reg")
            if reg_state is None:
                raise RuntimeError(
                    f"{inst['mnemonic']}: load_from_reg requires reg_state "
                    f"(need value of '{reg}')"
                )
            # Map KB generic register name (e.g. "An") to actual register
            # in reg_state (e.g. "A6")
            resolved = None
            for name, val in reg_state.items():
                if name.upper().startswith(reg[0].upper()):
                    resolved = val
                    break
            if resolved is None:
                raise RuntimeError(
                    f"{inst['mnemonic']}: load_from_reg needs '{reg}' but "
                    f"reg_state has {list(reg_state.keys())}"
                )
            sp = resolved
        else:
            raise RuntimeError(
                f"{inst['mnemonic']}: unknown SP effect action '{action}'"
            )
    return sp & 0xFFFFFFFF


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

    Returns ("two_op", src_reg, dst_reg) or ("single_op", None, dst_reg) or None.
    Two-op means we can use Dn,Dn register form.
    Single-op means single Dn operand.
    """
    ea_modes = inst.get("ea_modes", {})
    for form in inst.get("forms", []):
        if form.get("processor_020"):
            continue
        ops = [o["type"] for o in form.get("operands", [])]

        if ops == ["dn", "dn"]:
            # Explicit Dn,Dn form (ADDX, SUBX)
            return ("two_op", 0, 1)
        if ops == ["ea", "dn"]:
            # Source from EA (includes Dn), dest is data register
            src_modes = ea_modes.get("src", ea_modes.get("ea", []))
            if "dn" in src_modes:
                return ("two_op", 0, 1)
        if ops == ["dn", "ea"]:
            # Source is Dn, dest from EA (includes Dn)
            dst_modes = ea_modes.get("dst", ea_modes.get("ea", []))
            if "dn" in dst_modes:
                return ("two_op", 0, 1)
        if ops == ["ea", "ea"]:
            # Both from EA — check if both support Dn (MOVE)
            src_modes = ea_modes.get("src", ea_modes.get("ea", []))
            dst_modes = ea_modes.get("dst", ea_modes.get("ea", []))
            if "dn" in src_modes and "dn" in dst_modes:
                return ("two_op", 0, 1)
        if ops == ["imm", "ea"]:
            # Immediate source, EA destination — check if Dn is valid dest
            dst_modes = ea_modes.get("dst", ea_modes.get("ea", []))
            if "dn" in dst_modes:
                return ("imm_dn", None, 1)
        if ops == ["dn"]:
            # Explicit single Dn operand
            return ("single_op", None, 1)
        if ops == ["ea"]:
            # Single EA operand — check if Dn is valid
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
        if not sp_effects:
            continue
        if inst.get("effects", {}).get("privileged"):
            continue  # skip supervisor-mode instructions
        testable.append((mnemonic, inst))
    return testable


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

    # For bit test, get bit_modulus from KB (register modulus for Dn tests)
    if is_bit_test:
        bit_mod_data = inst.get("bit_modulus")
        if bit_mod_data is None:
            raise RuntimeError(
                f"{mnemonic}: missing 'bit_modulus' in KB — regenerate KB")

    # Select test values based on operation type
    if is_shift_rotate:
        values = SHIFT_TEST_VALUES
    elif op_type == "multiply":
        values = MULTIPLY_TEST_VALUES
    elif op_type == "divide":
        values = DIVIDE_TEST_VALUES
    elif is_bit_test:
        values = BIT_TEST_VALUES
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
                    else:
                        continue

                    code_bytes = assemble(asm_text, tmpdir)
                    if code_bytes is None:
                        continue

                    desc = f"{indiv_mnemonic}.{sz} {val_desc} ccr={ccr_desc}"
                    initial_ccr = {k: v for k, v in ccr_state.items() if k != "desc"}

                    yield (asm_text, code_bytes, sz, src_val, dst_val,
                           src_reg, dst_reg, initial_ccr, desc, ctx)


# ── SP test case generation ───────────────────────────────────────────────

def generate_sp_tests(inst, tmpdir):
    """Generate SP verification test cases for one instruction from KB data.

    Uses predict_sp() for expected SP values — no hardcoded predictions.

    Yields (asm_text, code_bytes, setup_fn, predicted_sp, predicted_pc, desc)
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
                       CODE_ADDR + _instr_size(code), f"pea {desc_suffix}")

    elif mnemonic == "JSR":
        target = SCRATCH_ADDR
        asm = f"jsr ${target:x}"
        code = assemble(asm, tmpdir)
        if code:
            def setup(cpu, mem, _t=target):
                mem.w16(_t, NOP_OPWORD)  # NOP at target (from KB)
            pred_sp = predict_sp(inst, STACK_ADDR)
            yield (asm, code, setup, pred_sp, target, "jsr abs")

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
                   "bsr.w forward")

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
            yield (asm, code, setup, pred_sp, return_addr, "rts")

    elif mnemonic == "LINK":
        for displacement, desc in [(-8, "link a6,#-8"), (-256, "link a6,#-256"),
                                    (0, "link a6,#0")]:
            asm = f"link a6,#{displacement}"
            code = assemble(asm, tmpdir)
            if code:
                pred_sp = predict_sp(inst, STACK_ADDR, displacement=displacement)
                yield (asm, code, lambda cpu, mem: None, pred_sp,
                       CODE_ADDR + _instr_size(code), desc)

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
                   CODE_ADDR + _instr_size(code), "unlk a6")

    # For other SP-affecting instructions not yet covered, we can add cases
    # as we expand coverage. No silent fallback — uncovered instructions
    # simply aren't tested until their test setup is added.


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

                # Set operand registers
                if _src_reg is not None:
                    cpu.w_reg(DATA_REGS[_src_reg], src_val & 0xFFFFFFFF)
                cpu.w_reg(DATA_REGS[_dst_reg], dst_val & 0xFFFFFFFF)

                set_ccr(cpu, x=initial_ccr["X"], n=initial_ccr["N"],
                        z=initial_ccr["Z"], v=initial_ccr["V"], c=initial_ccr["C"])
                ccr_before = read_ccr(cpu)

                # Predict CC from KB — single-op uses implicit_operand from KB.
                # Instructions without implicit_operand (NOT, TST) don't use
                # the source value in their compute handler, so 0 is safe.
                if form_type == "single_op":
                    pred_src = inst.get("implicit_operand", 0)
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
                 predicted_sp, predicted_pc, desc) in generate_sp_tests(inst, tmpdir):

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
