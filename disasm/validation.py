from __future__ import annotations

import struct

from disasm.decode import decode_instruction_for_emit, lookup_instruction_kb
from m68k.kb_util import KB
from m68k.m68k_executor import _extract_branch_target, _extract_mnemonic


def is_valid_encoding(text: str, raw: bytes, offset: int, kb: KB,
                      kb_mnemonic: str) -> bool:
    """Check if instruction EA mode and size are valid per KB constraints."""
    meta = decode_instruction_for_emit(text, raw, offset, kb, kb_mnemonic)
    ikb = meta["inst_kb"]
    ea_modes = ikb.get("ea_modes", {})
    if not ea_modes:
        return True
    sz = meta["size"]
    decoded = meta["decoded"]
    ea_op = decoded["ea_op"]
    dst_op = decoded["dst_op"]

    if ea_op and ea_op.mode:
        if "ea" in ea_modes:
            if ea_op.mode not in ea_modes["ea"]:
                return False
        elif "src" in ea_modes:
            if ea_op.mode not in ea_modes["src"]:
                return False
        elif "dst" in ea_modes:
            if ea_op.mode not in ea_modes["dst"]:
                return False

    if dst_op and dst_op.mode and "dst" in ea_modes:
        if dst_op.mode not in ea_modes["dst"]:
            return False

    an_sizes = ikb.get("constraints", {}).get("an_sizes")
    if an_sizes and sz:
        for op in (ea_op, dst_op):
            if op and op.mode == "an" and sz not in an_sizes:
                return False

    if sz == "b":
        ea_mode_sizes = kb.meta.get("ea_mode_sizes", {})
        an_valid = ea_mode_sizes.get("an", ["w", "l"])
        for op in (ea_op, dst_op):
            if op and op.mode == "an" and "b" not in an_valid:
                return False

    return True


def has_valid_branch_target(inst, kb: KB) -> bool:
    """Check if branch/jump target is word-aligned."""
    if not inst.kb_mnemonic:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing kb_mnemonic")
    ikb = lookup_instruction_kb(inst.kb_mnemonic, kb)
    flow = ikb.get("pc_effects", {}).get("flow", {})
    ftype = flow.get("type")
    if ftype not in ("branch", "jump", "call"):
        return True
    try:
        target = _extract_branch_target(inst, inst.offset)
    except (struct.error, IndexError):
        return False
    if target is None:
        return True
    return target % kb.opword_bytes == 0


def get_processor_min(text: str, kb: KB) -> str:
    """Get minimum processor for instruction from KB."""
    mnemonic = _extract_mnemonic(text)
    if not mnemonic:
        return "68000"
    ikb = lookup_instruction_kb(mnemonic, kb)
    pmin = ikb.get("processor_min", "68000")
    if pmin != "68000":
        return pmin
    mnemonic_upper = mnemonic.upper()
    for variant in ikb.get("variants", []):
        if (variant["mnemonic"].upper() == mnemonic_upper
                and variant.get("processor_020")):
            return "68020"
    return "68000"
