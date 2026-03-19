"""Shared deterministic register and pointer transform helpers."""


def _apply_known_shift(opcode_text: str, operand_size: str,
                       value: int, count: int) -> int | None:
    """Apply a supported immediate shift to a known data-register value."""
    bits = {"b": 8, "w": 16, "l": 32}.get(operand_size)
    if bits is None:
        return None
    mask = (1 << bits) - 1
    value &= mask
    token = opcode_text.lower()
    if token.startswith("lsl") or token.startswith("asl"):
        return (value << count) & mask
    if token.startswith("lsr"):
        return (value >> count) & mask
    if token.startswith("asr"):
        sign_bit = 1 << (bits - 1)
        if value & sign_bit:
            value -= 1 << bits
        return (value >> count) & mask
    rotate = count % bits
    if token.startswith("rol"):
        if rotate == 0:
            return value
        return ((value << rotate) | (value >> (bits - rotate))) & mask
    if token.startswith("ror"):
        if rotate == 0:
            return value
        return ((value >> rotate) | (value << (bits - rotate))) & mask
    return None


def _apply_known_logical(op_type: str, operand_size: str,
                         value: int, imm: int) -> int | None:
    """Apply a supported immediate logical op to a known register value."""
    bits = {"b": 8, "w": 16, "l": 32}.get(operand_size)
    if bits is None:
        return None
    mask = (1 << bits) - 1
    value &= mask
    imm &= mask
    if op_type == "and":
        return value & imm
    if op_type == "or":
        return value | imm
    if op_type == "xor":
        return value ^ imm
    return None


def _apply_known_bitop(opcode_text: str, value: int, bit: int) -> int | None:
    """Apply supported Dn bit ops to a known 32-bit register value."""
    mask = 0xFFFFFFFF
    value &= mask
    token = opcode_text.lower()
    bit_mask = 1 << (bit % 32)
    if token.startswith("bset"):
        return value | bit_mask
    if token.startswith("bclr"):
        return value & ~bit_mask & mask
    if token.startswith("bchg"):
        return value ^ bit_mask
    if token.startswith("btst"):
        return value
    return None


def _apply_known_test(opcode_text: str, operand_size: str, value: int) -> int | None:
    """Apply supported TEST-class ops to a known register value."""
    token = opcode_text.lower()
    value &= 0xFFFFFFFF
    if token.startswith("tst"):
        return value
    if token.startswith("tas"):
        return (value & 0xFFFFFF00) | ((value | 0x80) & 0xFF)
    return None


def _apply_known_unary(op_type: str, operand_size: str,
                       value: int) -> int | None:
    """Apply a supported unary op to a known register value."""
    bits = {"b": 8, "w": 16, "l": 32}.get(operand_size)
    if bits is None:
        return None
    mask = (1 << bits) - 1
    value &= mask
    if op_type == "not":
        return (~value) & mask
    if op_type == "neg":
        return (-value) & mask
    return None


def _apply_known_swap(value: int) -> int:
    """Apply SWAP to a 32-bit register value."""
    value &= 0xFFFFFFFF
    return ((value & 0xFFFF) << 16) | ((value >> 16) & 0xFFFF)


def _node_reg_ref(node) -> tuple[str, int] | None:
    """Return canonical (mode, reg) for a typed register node."""
    if node.kind != "register" or not node.register:
        return None
    reg = node.register.lower()
    if len(reg) != 2 or reg[1] not in "01234567":
        return None
    if reg[0] == "d":
        return ("dn", int(reg[1]))
    if reg[0] == "a":
        return ("an", int(reg[1]))
    return None


def _swap_partner(inst, current_mode: str, current_reg: int) -> tuple[str, int] | None:
    """Return the pre-EXG register that feeds the tracked register."""
    if len(inst.operand_nodes) != 2:
        return None
    left = _node_reg_ref(inst.operand_nodes[0])
    right = _node_reg_ref(inst.operand_nodes[1])
    if left is None or right is None:
        return None
    current = (current_mode, current_reg)
    if left == current:
        return right
    if right == current:
        return left
    return None


def _apply_known_sign_extend(operand_size: str, value: int) -> int | None:
    """Apply EXT sign-extension using the KB-decoded operand size."""
    value &= 0xFFFFFFFF
    if operand_size == "w":
        low = value & 0xFF
        if low & 0x80:
            low |= 0xFF00
        return (value & 0xFFFF0000) | low
    if operand_size == "l":
        low = value & 0xFFFF
        if low & 0x8000:
            low |= 0xFFFF0000
        return low & 0xFFFFFFFF
    return None


def _apply_known_multiply(opcode_text: str, operand_size: str,
                          dst_value: int, src_value: int) -> int | None:
    """Apply supported MULU/MULS forms to known register values."""
    token = opcode_text.lower()
    if operand_size != "w":
        return None
    lhs = dst_value & 0xFFFF
    rhs = src_value & 0xFFFF
    if token.startswith("muls"):
        if lhs & 0x8000:
            lhs -= 0x10000
        if rhs & 0x8000:
            rhs -= 0x10000
        return (lhs * rhs) & 0xFFFFFFFF
    if token.startswith("mulu"):
        return (lhs * rhs) & 0xFFFFFFFF
    return None


def _apply_known_divide(opcode_text: str, operand_size: str,
                        dst_value: int, src_value: int) -> int | None:
    """Apply supported DIVU/DIVS word forms to known register values."""
    token = opcode_text.lower()
    if operand_size != "w":
        return None
    divisor = src_value & 0xFFFF
    dividend = dst_value & 0xFFFFFFFF
    if token.startswith("divs"):
        if divisor & 0x8000:
            divisor -= 0x10000
        if divisor == 0:
            return None
        if dividend & 0x80000000:
            dividend -= 0x100000000
        quotient = int(dividend / divisor)
        remainder = dividend % divisor
        if not (-0x8000 <= quotient <= 0x7FFF):
            return None
        return (((remainder & 0xFFFF) << 16) | (quotient & 0xFFFF)) & 0xFFFFFFFF
    if token.startswith("divu"):
        if divisor == 0:
            return None
        quotient = dividend // divisor
        remainder = dividend % divisor
        if quotient > 0xFFFF:
            return None
        return (((remainder & 0xFFFF) << 16) | (quotient & 0xFFFF)) & 0xFFFFFFFF
    return None


def _apply_pointer_transforms(value: int, transforms) -> int | None:
    """Apply stored pointer transforms in execution order."""
    out = value
    for kind, *args in reversed(transforms):
        if kind == "shift":
            opcode_text, operand_size, count = args
            out = _apply_known_shift(opcode_text, operand_size, out, count)
        elif kind == "logical":
            op_type, operand_size, imm = args
            out = _apply_known_logical(op_type, operand_size, out, imm)
        elif kind == "bitop":
            opcode_text, bit = args
            out = _apply_known_bitop(opcode_text, out, bit)
        elif kind == "test":
            opcode_text, operand_size = args
            out = _apply_known_test(opcode_text, operand_size, out)
        elif kind == "unary":
            op_type, operand_size = args
            out = _apply_known_unary(op_type, operand_size, out)
        elif kind == "swap":
            out = _apply_known_swap(out)
        elif kind == "sign_extend":
            operand_size, = args
            out = _apply_known_sign_extend(operand_size, out)
        elif kind == "multiply":
            opcode_text, operand_size, src = args
            out = _apply_known_multiply(opcode_text, operand_size, out, src)
        elif kind == "divide":
            opcode_text, operand_size, src = args
            out = _apply_known_divide(opcode_text, operand_size, out, src)
        else:
            return None
        if out is None:
            return None
    return out
