from __future__ import annotations

from m68k.kb_util import KB, decode_instruction_operands

_INSTRUCTION_KB_CACHE: dict[str, dict | None] = {}
_INSTRUCTION_DECODE_CACHE: dict[tuple[str, bytes, int], dict] = {}


def lookup_instruction_kb(mnemonic: str, kb: KB) -> dict:
    """Return KB entry for mnemonic or raise if it is missing."""
    if not mnemonic:
        raise ValueError("Instruction mnemonic is missing")
    if mnemonic not in _INSTRUCTION_KB_CACHE:
        inst_kb = kb.find(mnemonic)
        _INSTRUCTION_KB_CACHE[mnemonic] = inst_kb
    inst_kb = _INSTRUCTION_KB_CACHE[mnemonic]
    if inst_kb is None:
        raise KeyError(f"KB missing instruction entry for {mnemonic}")
    return inst_kb

def decode_instruction_for_emit(inst_raw: bytes,
                                inst_offset: int, kb: KB,
                                kb_mnemonic: str,
                                operand_size: str) -> dict:
    """Decode an instruction once for emission-time consumers."""
    if not kb_mnemonic:
        raise ValueError(
            f"Instruction at ${inst_offset:06x} is missing kb_mnemonic")
    if not operand_size:
        raise ValueError(
            f"Instruction at ${inst_offset:06x} is missing operand_size")
    decode_mnemonic = kb_mnemonic
    key = (decode_mnemonic, inst_raw, inst_offset)
    cached = _INSTRUCTION_DECODE_CACHE.get(key)
    if cached is not None:
        return cached

    inst_kb = lookup_instruction_kb(decode_mnemonic, kb)
    decoded = decode_instruction_operands(
        inst_raw, inst_kb, kb.meta, operand_size, inst_offset)
    cached = {
        "mnemonic": decode_mnemonic,
        "size": operand_size,
        "inst_kb": inst_kb,
        "decoded": decoded,
    }
    _INSTRUCTION_DECODE_CACHE[key] = cached
    return cached


def decode_inst_for_emit(inst, kb: KB) -> dict:
    """Decode and cache operand metadata on an Instruction object."""
    if inst.decoded_operands is not None:
        return inst.decoded_operands
    if not inst.kb_mnemonic:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing kb_mnemonic")
    if not inst.operand_size:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing operand_size")
    meta = decode_instruction_for_emit(
        inst.raw, inst.offset, kb, inst.kb_mnemonic, inst.operand_size)
    inst.decoded_operands = meta
    return meta
