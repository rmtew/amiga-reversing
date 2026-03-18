from __future__ import annotations

import struct

from m68k.m68k_executor import _extract_mnemonic

from disasm.decode import lookup_instruction_kb
from disasm.validation import (get_processor_min, has_valid_branch_target,
                               is_valid_encoding)


def hint_block_has_supported_terminal_flow(block, kb) -> bool:
    if not block.instructions:
        return False
    last = block.instructions[-1]
    last_kb = lookup_instruction_kb(_extract_mnemonic(last.text), kb)
    flow = last_kb.get("pc_effects", {}).get("flow", {})
    flow_type = flow.get("type")
    if flow_type in ("return", "jump", "branch"):
        return True
    if flow_type == "call" and not flow.get("conditional"):
        return True
    return False


def is_valid_hint_block(block, kb) -> bool:
    if not hint_block_has_supported_terminal_flow(block, kb):
        return False

    for inst in block.instructions:
        if (len(inst.raw) >= kb.opword_bytes
                and struct.unpack_from(">H", inst.raw, 0)[0] == 0):
            return False
        if not is_valid_encoding(inst.text, inst.raw, inst.offset, kb,
                                 inst.kb_mnemonic):
            return False
        if not has_valid_branch_target(inst, kb):
            return False
        if get_processor_min(inst.text, kb) != "68000":
            return False
    return True
