import copy

import pytest

from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble
from m68k.m68k_executor import _load_kb, decode_instruction_ops


def _decoded_ops(asm: str, kb_mnemonic: str):
    raw = assemble_instruction(asm)
    inst = disassemble(raw, max_cpu="68010")[0]
    kb_by_name, _, _ = _load_kb()
    return decode_instruction_ops(inst, kb_by_name[kb_mnemonic], "l")


def test_decode_instruction_ops_uses_shared_kb_decoder_for_move_usp():
    decoded = _decoded_ops("move.l usp,a0", "MOVE USP")
    assert decoded.reg_num == 0
    assert decoded.ea_is_source is True

    decoded = _decoded_ops("move.l a1,usp", "MOVE USP")
    assert decoded.reg_num == 1
    assert decoded.ea_is_source is False


def test_decode_instruction_ops_errors_when_move_usp_kb_field_missing():
    raw = assemble_instruction("move.l usp,a0")
    inst = disassemble(raw, max_cpu="68010")[0]
    kb_by_name, _, _ = _load_kb()
    inst_kb = copy.deepcopy(kb_by_name["MOVE USP"])
    inst_kb["encodings"][0]["fields"] = [
        field
        for field in inst_kb["encodings"][0]["fields"]
        if field["name"] != "dr"
    ]

    with pytest.raises(ValueError, match="direction/register fields missing"):
        decode_instruction_ops(inst, inst_kb, "l")
