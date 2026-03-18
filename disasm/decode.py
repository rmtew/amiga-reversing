from __future__ import annotations

from m68k.kb_util import KB, decode_instruction_operands
from m68k.m68k_executor import _extract_size

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


def decode_instruction_for_emit(inst_text: str, inst_raw: bytes,
                                inst_offset: int, kb: KB,
                                kb_mnemonic: str) -> dict:
    """Decode an instruction once for emission-time consumers."""
    if not kb_mnemonic:
        raise ValueError(
            f"Instruction at ${inst_offset:06x} is missing kb_mnemonic")
    key = (kb_mnemonic, inst_raw, inst_offset)
    cached = _INSTRUCTION_DECODE_CACHE.get(key)
    if cached is not None:
        return cached

    inst_kb = lookup_instruction_kb(kb_mnemonic, kb)
    size = _extract_size(inst_text)
    decoded = decode_instruction_operands(
        inst_raw, inst_kb, kb.meta, size, inst_offset)
    cached = {
        "mnemonic": kb_mnemonic,
        "size": size,
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
    meta = decode_instruction_for_emit(
        inst.text, inst.raw, inst.offset, kb, inst.kb_mnemonic)
    inst.decoded_operands = meta
    return meta
