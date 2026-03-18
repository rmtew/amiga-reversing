from __future__ import annotations

from m68k.kb_util import KB, decode_instruction_operands, select_encoding_index
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


def _decode_mnemonic(inst_text: str, kb_mnemonic: str, kb: KB) -> str:
    text_mnemonic = inst_text.strip().split(None, 1)[0].split(".", 1)[0].lower()
    if text_mnemonic:
        text_match = kb.find(text_mnemonic)
        if text_match is not None:
            return text_mnemonic
    return kb_mnemonic


def _specialize_move_mnemonic(opcode: int, kb: KB) -> str | None:
    candidates = [
        "MOVE to CCR",
        "MOVE to SR",
        "MOVE from SR",
        "MOVE from CCR",
        "MOVE USP",
    ]
    matches = []
    for candidate in candidates:
        inst_kb = lookup_instruction_kb(candidate, kb)
        try:
            select_encoding_index(inst_kb, opcode)
        except ValueError:
            continue
        matches.append(candidate)
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError(f"Ambiguous MOVE specialization for opcode ${opcode:04x}: {matches}")
    return matches[0]


def decode_instruction_for_emit(inst_text: str, inst_raw: bytes,
                                inst_offset: int, kb: KB,
                                kb_mnemonic: str) -> dict:
    """Decode an instruction once for emission-time consumers."""
    if not kb_mnemonic:
        raise ValueError(
            f"Instruction at ${inst_offset:06x} is missing kb_mnemonic")
    decode_mnemonic = _decode_mnemonic(inst_text, kb_mnemonic, kb)
    opcode = int.from_bytes(inst_raw[:2], "big")
    if decode_mnemonic == "move":
        specialized = _specialize_move_mnemonic(opcode, kb)
        if specialized is not None:
            decode_mnemonic = specialized
    key = (decode_mnemonic, inst_raw, inst_offset)
    cached = _INSTRUCTION_DECODE_CACHE.get(key)
    if cached is not None:
        return cached

    inst_kb = lookup_instruction_kb(decode_mnemonic, kb)
    size = _extract_size(inst_text)
    decoded = decode_instruction_operands(
        inst_raw, inst_kb, kb.meta, size, inst_offset)
    cached = {
        "mnemonic": decode_mnemonic,
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
