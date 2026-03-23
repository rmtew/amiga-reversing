from __future__ import annotations

import struct

from disasm.types import DisasmBlockLike
from disasm.validation import (
    get_instruction_processor_min,
    has_valid_branch_target,
    is_valid_encoding,
)
from m68k.instruction_kb import instruction_flow
from m68k_kb import runtime_m68k_analysis, runtime_m68k_decode

_FLOW_BRANCH = runtime_m68k_analysis.FlowType.BRANCH
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
_FLOW_RETURN = runtime_m68k_analysis.FlowType.RETURN


def hint_block_has_supported_terminal_flow(block: DisasmBlockLike) -> bool:
    if not block.instructions:
        return False
    last = block.instructions[-1]
    flow_type, conditional = instruction_flow(last)
    if flow_type in (_FLOW_RETURN, _FLOW_JUMP, _FLOW_BRANCH):
        return True
    return bool(flow_type == _FLOW_CALL and not conditional)


def is_valid_hint_block(block: DisasmBlockLike) -> bool:
    if not hint_block_has_supported_terminal_flow(block):
        return False

    for inst in block.instructions:
        if (len(inst.raw) >= runtime_m68k_decode.OPWORD_BYTES
                and struct.unpack_from(">H", inst.raw, 0)[0] == 0):
            return False
        if inst.kb_mnemonic is None or inst.operand_size is None:
            return False
        if not is_valid_encoding(inst.raw, inst.offset,
                                 inst.kb_mnemonic, inst.operand_size):
            return False
        if not has_valid_branch_target(inst):
            return False
        if get_instruction_processor_min(inst) != "68000":
            return False
    return True
