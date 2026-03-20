from __future__ import annotations

import struct

from m68k_kb import runtime_m68k_analysis
from m68k_kb import runtime_m68k_decode

from disasm.decode import decode_instruction_for_emit, lookup_instruction_kb
from m68k.instruction_kb import instruction_kb
from m68k.instruction_primitives import extract_branch_target


def is_valid_encoding(raw: bytes, offset: int,
                      kb_mnemonic: str, operand_size: str) -> bool:
    """Check if instruction EA mode and size are valid per KB constraints."""
    meta = decode_instruction_for_emit(raw, offset, kb_mnemonic, operand_size)
    mnemonic = meta["mnemonic"]
    ea_mode_table = runtime_m68k_analysis.EA_MODE_TABLES.get(mnemonic)
    if not ea_mode_table:
        return True
    src_modes, dst_modes, ea_modes = ea_mode_table
    sz = meta["size"]
    decoded = meta["decoded"]
    ea_op = decoded["ea_op"]
    dst_op = decoded["dst_op"]

    if ea_op and ea_op.mode:
        if ea_modes:
            if ea_op.mode not in ea_modes:
                return False
        elif src_modes:
            if ea_op.mode not in src_modes:
                return False
        elif dst_modes:
            if ea_op.mode not in dst_modes:
                return False

    if dst_op and dst_op.mode and dst_modes:
        if dst_op.mode not in dst_modes:
            return False

    an_sizes = runtime_m68k_analysis.AN_SIZES.get(mnemonic)
    if an_sizes and sz:
        for op in (ea_op, dst_op):
            if op and op.mode == "an" and sz not in an_sizes:
                return False

    if sz == "b":
        an_valid = runtime_m68k_analysis.EA_MODE_SIZES.get("an", ["w", "l"])
        for op in (ea_op, dst_op):
            if op and op.mode == "an" and "b" not in an_valid:
                return False

    return True


def has_valid_branch_target(inst) -> bool:
    """Check if branch/jump target is word-aligned."""
    if not inst.kb_mnemonic:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing kb_mnemonic")
    mnemonic = lookup_instruction_kb(inst.kb_mnemonic)
    ftype = runtime_m68k_analysis.FLOW_TYPES[mnemonic]
    if ftype not in (
            runtime_m68k_analysis.FlowType.BRANCH,
            runtime_m68k_analysis.FlowType.JUMP,
            runtime_m68k_analysis.FlowType.CALL):
        return True
    try:
        target = extract_branch_target(inst, inst.offset)
    except (struct.error, IndexError):
        return False
    if target is None:
        return True
    return target % runtime_m68k_decode.OPWORD_BYTES == 0

def get_instruction_processor_min(inst) -> str:
    """Get minimum processor for a decoded instruction."""
    pmin = runtime_m68k_analysis.PROCESSOR_MINS.get((inst.kb_mnemonic or "").lower(), "68000")
    if str(pmin) != "68000":
        return str(pmin)
    canonical = instruction_kb(inst)
    mnemonic = (inst.kb_mnemonic or "").upper()
    for variant_mnemonic in runtime_m68k_analysis.PROCESSOR_020_VARIANTS.get(canonical, ()):
        if variant_mnemonic.upper() == mnemonic:
            return "68020"
    return "68000"
