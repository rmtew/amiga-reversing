"""KB-driven M68K computation engine - pure functions, no machine dependency.

Provides CC flag prediction, result computation, and SP effect prediction,
all driven from structured data in m68k_instructions.json. Contains no
hardcoded M68K instruction knowledge.

Used by:
  - oracle_m68k_exec.py (verification against machine68k oracle)
  - Future: symbolic execution / static analysis engine
"""

from m68k_kb import runtime_m68k_compute


# -- Size utilities --------------------------------------------------------

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


# -- CC prediction from KB rules ------------------------------------------

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

    mnemonic = inst["mnemonic"]
    op_type = runtime_m68k_compute.OPERATION_TYPES.get(mnemonic)
    if not op_type:
        raise RuntimeError(f"{mnemonic}: missing operation_type in runtime KB")

    if ctx is None:
        ctx = {}

    mask, bits = _size_mask(sz)

    # Allow KB data_sizes to override default operand/result widths.
    # Multiply: operands may be narrower than result (16x16->32).
    # Divide: dividend may be wider than divisor/quotient (32/16->16).
    data_sizes = ctx.get("data_sizes")
    if data_sizes:
        ds_type, src_bits, dst_bits, result_bits = data_sizes
        if ds_type not in (
            runtime_m68k_compute.PrimaryDataSizeKind.MULTIPLY,
            runtime_m68k_compute.PrimaryDataSizeKind.DIVIDE,
        ):
            raise RuntimeError(f"unknown primary data size kind: {ds_type!r}")
        src_mask = (1 << src_bits) - 1
        dst_mask = (1 << dst_bits) - 1
        result_mask = (1 << result_bits) - 1
    else:
        src_bits = dst_bits = result_bits = bits
        src_mask = dst_mask = result_mask = mask

    # KB cc_result_bits overrides operand/result width for compute + CC evaluation
    # (e.g. SWAP: Size=Word but PDF CC says "32-bit result" - operation is 32-bit)
    cc_override = ctx.get("cc_result_bits")
    if cc_override is not None:
        # KB source_sign_extend: sign-extend source from declared size to
        # override size (e.g. CMPA.W: 16-bit source -> 32-bit for comparison)
        if ctx.get("source_sign_extend"):
            src_val_masked = src_val & src_mask
            if src_val_masked & (1 << (src_bits - 1)):
                # Sign bit set - extend with 1s
                src_val = src_val_masked | (~src_mask & ((1 << cc_override) - 1))
            else:
                src_val = src_val_masked
        src_bits = dst_bits = result_bits = cc_override
        src_mask = dst_mask = result_mask = (1 << cc_override) - 1

    src = src_val & src_mask
    dst = dst_val & dst_mask

    # CCR/SR manipulation instructions have no compute_formula - they
    # directly modify CC flags via rules that reference the source/immediate.
    # No result computation needed; pass through dummy values.
    if op_type in (runtime_m68k_compute.OperationType.CCR_OP, runtime_m68k_compute.OperationType.SR_OP):
        result_full = 0
        result = 0
    else:
        # Compute result using KB compute_formula
        result_full, result = _compute_result(
            mnemonic, src, dst, result_mask, result_bits, initial_ccr, ctx)

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


# -- KB-driven result computation ------------------------------------------
#
# The compute_formula in the KB (extracted from PDF Operation text by the
# parser) specifies what operation to perform and in what operand order.
# This evaluator maps universal math operators to Python - the operators
# themselves (+, -, &, |, ^, ~, *, /) are not M68K knowledge; the KB
# specifies which one applies to each instruction and the operand order.


def _resolve_term(term, src, dst, ccr, implicit):
    """Resolve a formula operand term to its numeric value."""
    if term == runtime_m68k_compute.FormulaTerm.SOURCE:
        return src
    if term == runtime_m68k_compute.FormulaTerm.DESTINATION:
        return dst
    if term == runtime_m68k_compute.FormulaTerm.EXTEND:
        return ccr.get("X", 0)
    if term == runtime_m68k_compute.FormulaTerm.IMPLICIT:
        if implicit is None:
            raise RuntimeError(
                "Formula references 'implicit' term but no implicit_operand "
                "in KB instruction - add implicit_operand extraction to parser")
        return implicit
    if isinstance(term, int):
        return term
    raise RuntimeError(f"Unknown formula term: {term!r}")


# Universal math operators - these map formula 'op' names (from KB) to
# Python functions. None of these are M68K-specific; they are standard
# binary arithmetic/logic operations.
_FORMULA_OPS = {
    runtime_m68k_compute.ComputeOp.ADD:                lambda a, b: a + b,
    runtime_m68k_compute.ComputeOp.SUBTRACT:           lambda a, b: a - b,
    runtime_m68k_compute.ComputeOp.BITWISE_AND:        lambda a, b: a & b,
    runtime_m68k_compute.ComputeOp.BITWISE_OR:         lambda a, b: a | b,
    runtime_m68k_compute.ComputeOp.BITWISE_XOR:        lambda a, b: a ^ b,
    runtime_m68k_compute.ComputeOp.BITWISE_COMPLEMENT: lambda a: ~a,
    runtime_m68k_compute.ComputeOp.ASSIGN:             lambda a: a,
    runtime_m68k_compute.ComputeOp.TEST:               lambda a: a,
}


def _compute_exchange(dst, range_a, range_b):
    """Compute bit-range exchange from KB formula (SWAP).

    The KB specifies exact bit ranges from the PDF Operation text:
    e.g. range_a=[31,16], range_b=[15,0] for "Register [31:16] <--> [15:0]".
    """
    hi_top, hi_bot = range_a
    lo_top, lo_bot = range_b
    hi_width = hi_top - hi_bot + 1
    lo_width = lo_top - lo_bot + 1
    hi_mask = ((1 << hi_width) - 1) << hi_bot
    lo_mask = ((1 << lo_width) - 1) << lo_bot
    hi_val = (dst & hi_mask) >> hi_bot
    lo_val = (dst & lo_mask) >> lo_bot
    return (lo_val << hi_bot) | (hi_val << lo_bot)


def _compute_sign_extend(dst, mask, bits, ctx):
    """Sign-extend from a narrower source width to the operation size.

    The KB formula has 'source_bits_by_size' mapping size->source width,
    extracted from PDF description text (e.g. "extends a byte to a word").
    The ctx must have 'sign_extend_source_bits' set by the test generator.
    """
    source_bits = ctx.get("sign_extend_source_bits")
    if source_bits is None:
        raise RuntimeError(
            "compute sign_extend: missing 'sign_extend_source_bits' in ctx "
            "- must come from KB source_bits_by_size")
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
        raise RuntimeError("_compute_shift: missing 'fill' in ctx - must come from KB variant")
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
    _kind, src_bits, dst_bits, _result_bits = ds
    if ctx.get("signed", False):
        s_signed = src if src < (1 << (src_bits - 1)) else src - (1 << src_bits)
        d_signed = dst if dst < (1 << (dst_bits - 1)) else dst - (1 << dst_bits)
        return s_signed * d_signed
    else:
        return src * dst


def _compute_divide(src, dst, mask, bits, ccr, ctx):
    """Divide. Signedness from KB, truncation direction from KB compute_formula."""
    if src == 0:
        raise RuntimeError("Division by zero in test - fix test values")
    ds = ctx["data_sizes"]
    _kind, divisor_bits, dividend_bits, _quotient_bits = ds
    if ctx.get("signed", False):
        s_signed = src if src < (1 << (divisor_bits - 1)) else src - (1 << divisor_bits)
        d_signed = dst if dst < (1 << (dividend_bits - 1)) else dst - (1 << dividend_bits)
        # Truncation direction from KB compute_formula (asserted as "toward_zero")
        return int(d_signed / s_signed)
    else:
        return dst // src


def _bcd_add(a, b, x):
    """Packed BCD addition: a + b + x -> (result, carry).

    Standard packed BCD algorithm - correct each nibble by adding 6 when
    the nibble exceeds 9 or produces a binary carry. Returns (result_byte, carry).
    """
    low = (a & 0xF) + (b & 0xF) + x
    low_carry = 0
    if low > 9:
        low += 6
        low_carry = 1
    high = (a >> 4) + (b >> 4) + low_carry
    carry = 0
    if high > 9:
        high += 6
        carry = 1
    return ((high & 0xF) << 4) | (low & 0xF), carry


def _bcd_subtract(a, b, x):
    """Packed BCD subtraction: a - b - x -> (result, borrow).

    Standard packed BCD subtraction - correct each nibble by subtracting 6
    when borrow occurs. Returns (result_byte, borrow).
    """
    low = (a & 0xF) - (b & 0xF) - x
    low_borrow = 0
    if low < 0:
        low += 10
        low_borrow = 1
    high = (a >> 4) - (b >> 4) - low_borrow
    borrow = 0
    if high < 0:
        high += 10
        borrow = 1
    return ((high & 0xF) << 4) | (low & 0xF), borrow


def _evaluate_formula(formula, src, dst, mask, bits, ccr, ctx):
    """Evaluate a KB compute_formula to produce the operation result.

    The formula structure comes from the KB (extracted from PDF Operation text).
    This evaluator applies universal math operators - it contains no M68K knowledge.
    """
    op, terms, range_a, range_b, _source_bits_by_size, _truncation = formula
    implicit = ctx.get("implicit_operand")

    # BCD arithmetic - packed decimal, byte only
    if op == runtime_m68k_compute.ComputeOp.ADD_DECIMAL:
        resolved = [_resolve_term(t, src, dst, ccr, implicit) for t in terms]
        a, b, x = resolved
        result, carry = _bcd_add(a & 0xFF, b & 0xFF, x)
        ctx["_decimal_carry"] = carry
        return result
    if op == runtime_m68k_compute.ComputeOp.SUBTRACT_DECIMAL:
        resolved = [_resolve_term(t, src, dst, ccr, implicit) for t in terms]
        a, b, x = resolved
        result, borrow = _bcd_subtract(a & 0xFF, b & 0xFF, x)
        ctx["_decimal_borrow"] = borrow
        return result

    # Simple two-operand or single-operand formulas
    if op in _FORMULA_OPS:
        fn = _FORMULA_OPS[op]
        resolved = [_resolve_term(t, src, dst, ccr, implicit) for t in terms]
        if len(terms) == 3:
            # Extended operations: add(a, b, X) or subtract(a, b, X)
            a, b, x = resolved
            if op == runtime_m68k_compute.ComputeOp.ADD:
                return a + b + x
            elif op == runtime_m68k_compute.ComputeOp.SUBTRACT:
                return a - b - x
        elif len(terms) == 2:
            return fn(resolved[0], resolved[1])
        elif len(terms) == 1:
            return fn(resolved[0])
        else:
            raise RuntimeError(f"Formula op '{op}' with {len(terms)} terms")

    # Complex operations - parameterized by KB data
    if op == runtime_m68k_compute.ComputeOp.EXCHANGE:
        if range_a is None or range_b is None:
            raise RuntimeError("exchange compute formula missing ranges")
        return _compute_exchange(dst, range_a, range_b)
    if op == runtime_m68k_compute.ComputeOp.SIGN_EXTEND:
        return _compute_sign_extend(dst, mask, bits, ctx)
    if op == runtime_m68k_compute.ComputeOp.SHIFT:
        return _compute_shift(src, dst, mask, bits, ccr, ctx)
    if op == runtime_m68k_compute.ComputeOp.ROTATE:
        return _compute_rotate(src, dst, mask, bits, ccr, ctx)
    if op == runtime_m68k_compute.ComputeOp.ROTATE_EXTEND:
        return _compute_rotate_extend(src, dst, mask, bits, ccr, ctx)
    if op == runtime_m68k_compute.ComputeOp.MULTIPLY:
        return _compute_multiply(src, dst, mask, bits, ccr, ctx)
    if op == runtime_m68k_compute.ComputeOp.DIVIDE:
        return _compute_divide(src, dst, mask, bits, ccr, ctx)
    if op in (
        runtime_m68k_compute.ComputeOp.BIT_TEST,
        runtime_m68k_compute.ComputeOp.BIT_CHANGE,
        runtime_m68k_compute.ComputeOp.BIT_CLEAR,
        runtime_m68k_compute.ComputeOp.BIT_SET,
    ):
        bit_mod = ctx.get("bit_modulus")
        if bit_mod is None:
            raise RuntimeError(
                f"compute {op}: missing 'bit_modulus' in ctx - must come from KB")
        bit_num = src % bit_mod
        if op == runtime_m68k_compute.ComputeOp.BIT_TEST:
            return dst  # test only, destination unchanged
        if op == runtime_m68k_compute.ComputeOp.BIT_CHANGE:
            return dst ^ (1 << bit_num)
        if op == runtime_m68k_compute.ComputeOp.BIT_CLEAR:
            return dst & ~(1 << bit_num)
        return dst | (1 << bit_num)  # bit_set

    raise RuntimeError(f"Unknown compute_formula op: {op!r}")


def _compute_result(mnemonic: str, src, dst, mask, bits, initial_ccr, ctx=None):
    """Compute the full (unmasked) and masked result using KB compute_formula.

    Raises RuntimeError if the instruction has no compute_formula in the KB.
    """
    formula = runtime_m68k_compute.COMPUTE_FORMULAS.get(mnemonic)
    if formula is None:
        op_type = runtime_m68k_compute.OPERATION_TYPES.get(mnemonic)
        raise RuntimeError(
            f"{mnemonic}: missing compute_formula in runtime KB - "
            f"regenerate KB or add formula extraction for operation_type "
            f"'{op_type}'"
        )
    if ctx is None:
        ctx = {}
    # Thread implicit_operand from KB into ctx for formula evaluation
    if "implicit_operand" not in ctx:
        implicit = runtime_m68k_compute.IMPLICIT_OPERANDS.get(mnemonic)
        if implicit is not None:
            ctx["implicit_operand"] = implicit
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

def _rule_msb_operand(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """MSB of operand before the operation (TAS: N reflects pre-set value)."""
    return (dst >> (bits - 1)) & 1

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
            "bit_zero: missing 'bit_modulus' in ctx - must come from KB")
    bit_num = src % bit_mod
    return 1 if (dst >> bit_num) & 1 == 0 else 0

def _rule_z_cleared_if_nonzero(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    if result != 0:
        return 0
    return ccr.get("Z", 0)

def _rule_decimal_carry(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """C flag for BCD addition: set if decimal carry was generated."""
    carry = ctx.get("_decimal_carry")
    if carry is None:
        raise RuntimeError("decimal_carry rule: missing _decimal_carry in ctx - BCD compute needed")
    return carry

def _rule_decimal_borrow(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """C flag for BCD subtraction: set if decimal borrow was generated."""
    borrow = ctx.get("_decimal_borrow")
    if borrow is None:
        raise RuntimeError("decimal_borrow rule: missing _decimal_borrow in ctx - BCD compute needed")
    return borrow

def _rule_undefined(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    return None

def _rule_imm_bit_cleared(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """ANDI to CCR/SR: flag = flag AND imm_bit. KB 'bit' gives the bit position."""
    bit_pos = cc_sem[flag]["bit"]
    if (src >> bit_pos) & 1 == 0:
        return 0
    return ccr.get(flag, 0)

def _rule_imm_bit_set(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """ORI to CCR/SR: flag = flag OR imm_bit. KB 'bit' gives the bit position."""
    bit_pos = cc_sem[flag]["bit"]
    if (src >> bit_pos) & 1 == 1:
        return 1
    return ccr.get(flag, 0)

def _rule_imm_bit_changed(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """EORI to CCR/SR: flag = flag XOR imm_bit. KB 'bit' gives the bit position."""
    bit_pos = cc_sem[flag]["bit"]
    if (src >> bit_pos) & 1 == 1:
        return 1 - ccr.get(flag, 0)
    return ccr.get(flag, 0)

def _rule_source_bit(result, result_full, src, dst, mask, bits, op_type, ccr, cc_sem, flag, ctx):
    """MOVE to CCR: flag = specific bit of source operand. KB 'bit' gives position."""
    bit_pos = cc_sem[flag]["bit"]
    return (src >> bit_pos) & 1


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
                    "last_shifted_out: missing 'fill' in ctx - must come from KB variant")
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
    For right shifts (ASR), MSB is preserved at every step -> always 0.
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
    "msb_operand":              _rule_msb_operand,
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
    "decimal_carry":            _rule_decimal_carry,
    "decimal_borrow":           _rule_decimal_borrow,
    "undefined":                _rule_undefined,
    "imm_bit_cleared":          _rule_imm_bit_cleared,
    "imm_bit_set":              _rule_imm_bit_set,
    "imm_bit_changed":          _rule_imm_bit_changed,
    "source_bit":               _rule_source_bit,
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


# -- SP effect prediction --------------------------------------------------

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
    sp_effects = runtime_m68k_compute.SP_EFFECTS.get(inst["mnemonic"], ())
    if not sp_effects:
        return sp_before

    sp = sp_before
    for effect in sp_effects:
        action, nbytes, aux = effect
        if action == runtime_m68k_compute.SpEffectAction.DECREMENT:
            sp -= nbytes
        elif action == runtime_m68k_compute.SpEffectAction.INCREMENT:
            sp += nbytes
        elif action == runtime_m68k_compute.SpEffectAction.ADJUST:
            sp += displacement
        elif action == runtime_m68k_compute.SpEffectAction.SAVE_TO_REG:
            pass  # copies SP to register, no SP change
        elif action == runtime_m68k_compute.SpEffectAction.LOAD_FROM_REG:
            reg = aux
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


# -- Condition test evaluator ---------------------------------------------

def evaluate_cc_test(test_expr, ccr):
    """Evaluate a condition code test expression against CCR flag values.

    test_expr: Boolean flag expression from KB cc_test_definitions, e.g.
               "!C & !Z", "(N & V) | (!N & !V)", "true", "false"
    ccr:       dict mapping flag names to 0/1, e.g. {"X":0,"N":1,"Z":0,"V":0,"C":0}
    Returns:   True if condition is met, False otherwise.
    """
    if test_expr == "true":
        return True
    if test_expr == "false":
        return False
    return _eval_cc_or(test_expr, ccr)


def _eval_cc_or(expr, ccr):
    """Evaluate OR-separated terms: A | B | C"""
    # Split on | not inside parens
    terms = _split_top_level(expr, '|')
    return any(_eval_cc_and(t.strip(), ccr) for t in terms)


def _eval_cc_and(expr, ccr):
    """Evaluate AND-separated terms: A & B & C"""
    terms = _split_top_level(expr, '&')
    return all(_eval_cc_atom(t.strip(), ccr) for t in terms)


def _eval_cc_atom(expr, ccr):
    """Evaluate a single atom: flag name, !flag, or (sub-expression)."""
    expr = expr.strip()
    if expr.startswith('(') and expr.endswith(')'):
        return _eval_cc_or(expr[1:-1], ccr)
    if expr.startswith('!'):
        flag = expr[1:].strip()
        return ccr.get(flag, 0) == 0
    return ccr.get(expr, 0) == 1


def _split_top_level(expr, sep):
    """Split expression on separator, respecting parentheses."""
    parts = []
    depth = 0
    current = []
    for ch in expr:
        if ch == '(':
            depth += 1
            current.append(ch)
        elif ch == ')':
            depth -= 1
            current.append(ch)
        elif ch == sep and depth == 0:
            parts.append(''.join(current))
            current = []
        else:
            current.append(ch)
    parts.append(''.join(current))
    return parts
