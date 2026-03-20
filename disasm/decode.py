from __future__ import annotations

from types import SimpleNamespace

from m68k.instruction_kb import find_kb_entry
from m68k.instruction_decode import decode_inst_operands

_INSTRUCTION_KB_CACHE: dict[str, str | None] = {}
_INSTRUCTION_DECODE_CACHE: dict[tuple[str, bytes, int, str], dict] = {}


def lookup_instruction_kb(mnemonic: str) -> str:
    """Return canonical KB mnemonic or raise if it is missing."""
    if not mnemonic:
        raise ValueError("Instruction mnemonic is missing")
    if mnemonic not in _INSTRUCTION_KB_CACHE:
        canonical = find_kb_entry(mnemonic)
        _INSTRUCTION_KB_CACHE[mnemonic] = canonical
    canonical = _INSTRUCTION_KB_CACHE[mnemonic]
    if canonical is None:
        raise KeyError(f"KB missing instruction entry for {mnemonic}")
    return canonical

def decode_instruction_for_emit(inst_raw: bytes,
                                inst_offset: int,
                                kb_mnemonic: str,
                                operand_size: str) -> dict:
    """Decode an instruction once for emission-time consumers."""
    if not kb_mnemonic:
        raise ValueError(
            f"Instruction at ${inst_offset:06x} is missing kb_mnemonic")
    if not operand_size:
        raise ValueError(
            f"Instruction at ${inst_offset:06x} is missing operand_size")
    inst = SimpleNamespace(
        raw=inst_raw,
        offset=inst_offset,
        kb_mnemonic=kb_mnemonic,
        operand_size=operand_size,
        decoded_operands=None,
    )
    return decode_inst_for_emit(inst)


def decode_inst_for_emit(inst) -> dict:
    """Decode and cache operand metadata on an Instruction object."""
    if inst.decoded_operands is not None:
        return inst.decoded_operands
    if not inst.kb_mnemonic:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing kb_mnemonic")
    if not inst.operand_size:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing operand_size")
    key = (inst.kb_mnemonic, inst.raw, inst.offset, inst.operand_size)
    cached = _INSTRUCTION_DECODE_CACHE.get(key)
    if cached is not None:
        inst.decoded_operands = cached
        return cached

    mnemonic = lookup_instruction_kb(inst.kb_mnemonic)
    meta = {
        "mnemonic": mnemonic,
        "size": inst.operand_size,
        "decoded": decode_inst_operands(inst, mnemonic),
    }
    _INSTRUCTION_DECODE_CACHE[key] = meta
    inst.decoded_operands = meta
    return meta
