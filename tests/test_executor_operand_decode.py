import copy

import pytest

from m68k_kb import runtime_m68k_analysis
from m68k_kb import runtime_m68k_decode
from m68k_kb import runtime_m68k_executor

from disasm.operands import build_instruction_semantic_operands
from disasm.types import HunkDisassemblySession
from m68k import m68k_executor as executor_mod
from m68k.instruction_decode import decode_inst_destination, decode_inst_operands
from m68k.instruction_primitives import Operand, extract_branch_target
from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble, _resolve_kb_mnemonic
from m68k.m68k_executor import (analyze, decode_instruction_ops,
                                 CPUState, AbstractMemory, _concrete,
                                 _resolve_operand, _write_operand, resolve_ea)

def _decoded_ops(asm: str, kb_mnemonic: str):
    raw = assemble_instruction(asm)
    inst = disassemble(raw, max_cpu="68010")[0]
    return decode_instruction_ops(inst, kb_mnemonic, "l")


def _operand_session() -> HunkDisassemblySession:
    return HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        core_absolute_targets=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        struct_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform={},
        os_kb={"structs": {}},
        fixed_abs_addrs=set(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )


def _reload_executor_with_runtime_tables(monkeypatch, mutate_tables):
    real = runtime_m68k_executor
    attrs = {
        name: copy.deepcopy(getattr(real, name))
        for name in dir(real)
        if name.isupper()
    }
    mutate_tables(attrs)
    real_attrs = {
        name
        for name in dir(runtime_m68k_executor)
        if name.isupper()
    }
    for name in real_attrs - set(attrs):
        monkeypatch.delattr(runtime_m68k_executor, name, raising=False)
    for name, value in attrs.items():
        monkeypatch.setattr(runtime_m68k_executor, name, value, raising=False)
    return executor_mod


@pytest.mark.parametrize(
    ("raw", "group"),
    [
        (assemble_instruction("ori.b #$12,d0"), 0),
        (assemble_instruction("move.w d0,d1"), 1),
        (assemble_instruction("link a2,#-4"), 4),
        (assemble_instruction("addq.w #1,d0"), 5),
        (assemble_instruction("bsr.w $10"), 6),
        (assemble_instruction("moveq #1,d0"), 7),
        (assemble_instruction("divu.w d0,d1"), 8),
        (assemble_instruction("add.w d0,d1"), 13),
        (assemble_instruction("lsl.w #1,d0"), 14),
        (bytes.fromhex("f0800002"), 15),
    ],
)
def test_decode_opcode_returns_structured_instruction_text(raw: bytes, group: int):
    from m68k import m68k_disasm as disasm_mod

    d = disasm_mod._Decoder(raw, 0)
    opcode = d.read_u16()
    decoded = disasm_mod._decode_opcode(d, opcode, group, 0)

    assert isinstance(decoded, disasm_mod.DecodedInstructionText)


def test_decode_instruction_ops_uses_shared_kb_decoder_for_move_usp():
    decoded = _decoded_ops("move.l usp,a0", "MOVE USP")
    assert decoded.reg_num == 0
    assert decoded.ea_is_source is True

    decoded = _decoded_ops("move.l a1,usp", "MOVE USP")
    assert decoded.reg_num == 1
    assert decoded.ea_is_source is False


def test_decode_inst_operands_uses_instruction_fields_directly():
    inst = disassemble(assemble_instruction("move.l usp,a0"), max_cpu="68010")[0]

    decoded = decode_inst_operands(inst, "MOVE USP")

    assert decoded["reg_num"] == 0
    assert decoded["ea_is_source"] is True


def test_decode_inst_destination_uses_instruction_fields_directly():
    inst = disassemble(assemble_instruction("moveq #-1,d3"), max_cpu="68010")[0]

    dst = decode_inst_destination(inst, "MOVEQ")

    assert dst == ("dn", 3)


def test_decode_instruction_ops_errors_when_move_usp_kb_field_missing():
    raw = assemble_instruction("move.l usp,a0")
    inst = disassemble(raw, max_cpu="68010")[0]
    inst_kb = "MOVE USP"
    raw_fields = list(copy.deepcopy(runtime_m68k_decode.RAW_FIELDS))
    raw_fields[0] = dict(raw_fields[0])
    raw_fields[0]["MOVE USP"] = tuple(
        field
        for field in raw_fields[0]["MOVE USP"]
        if field[0] != "dr"
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(runtime_m68k_decode, "RAW_FIELDS", tuple(raw_fields), raising=False)
        with pytest.raises(ValueError, match="direction/register fields missing"):
            decode_instruction_ops(inst, inst_kb, "l")


def test_decode_instruction_ops_requires_runtime_movec_control_registers(monkeypatch):
    inst = disassemble(bytes.fromhex("4e7b0000"), max_cpu="68020")[0]
    real = runtime_m68k_decode
    attrs = {
        name: copy.deepcopy(getattr(real, name))
        for name in dir(real)
        if name.isupper()
    }
    del attrs["CONTROL_REGISTERS"]
    for name in [name for name in dir(runtime_m68k_decode) if name.isupper()]:
        if name not in attrs:
            monkeypatch.delattr(runtime_m68k_decode, name, raising=False)
    for name, value in attrs.items():
        monkeypatch.setattr(runtime_m68k_decode, name, value, raising=False)

    with pytest.raises((AttributeError, KeyError), match="CONTROL_REGISTERS"):
        decode_instruction_ops(inst, "MOVEC", inst.operand_size)


def test_analyze_requires_runtime_opmode_table_for_exg(monkeypatch):
    reloaded = _reload_executor_with_runtime_tables(
        monkeypatch,
        lambda attrs: attrs["OPMODE_TABLES_BY_VALUE"].pop("EXG"),
    )

    with pytest.raises(KeyError, match="opmode table for EXG"):
        reloaded.analyze(
            assemble_instruction("exg d0,d1"),
            propagate=True,
            entry_points=[0],
        )


def test_analyze_requires_runtime_single_register_field_for_swap(monkeypatch):
    reloaded = _reload_executor_with_runtime_tables(
        monkeypatch,
        lambda attrs: attrs["REGISTER_FIELDS"].pop("SWAP"),
    )

    with pytest.raises(KeyError, match="single register field for SWAP"):
        reloaded.analyze(
            assemble_instruction("swap d0"),
            propagate=True,
            entry_points=[0],
        )


def test_analyze_requires_runtime_immediate_range_for_signed_moveq(monkeypatch):
    reloaded = _reload_executor_with_runtime_tables(
        monkeypatch,
        lambda attrs: attrs["IMMEDIATE_RANGES"].pop("MOVEQ"),
    )

    with pytest.raises(KeyError, match="immediate range for MOVEQ"):
        reloaded.analyze(
            assemble_instruction("moveq #-1,d0"),
            propagate=True,
            entry_points=[0],
        )


def test_decode_instruction_ops_skips_immediate_word_before_indexed_ea():
    inst = disassemble(bytes.fromhex("0c72ffff2000"), max_cpu="68010")[0]
    decoded = decode_instruction_ops(inst, "CMPI", inst.operand_size)

    assert decoded.imm_val == 0xFFFF
    assert decoded.ea_op is not None
    assert decoded.ea_op.mode == "index"
    assert decoded.ea_op.reg == 2
    assert decoded.ea_op.value == 0
    assert decoded.ea_op.index_reg == 2
    assert decoded.ea_op.index_size == "w"


def test_decode_instruction_ops_skips_immediate_word_before_full_extension_ea():
    inst = disassemble(bytes.fromhex("0470634e7570004e754e"), max_cpu="68020")[0]
    decoded = decode_instruction_ops(inst, "SUBI", inst.operand_size)

    assert decoded.imm_val == 0x634E
    assert decoded.ea_op is not None
    assert decoded.ea_op.mode == "index"
    assert decoded.ea_op.reg == 0
    assert decoded.ea_op.full_extension is True
    assert decoded.ea_op.base_displacement == 5141838


def test_disassemble_special_move_uses_exact_kb_entry():
    inst = disassemble(bytes.fromhex("44 d2"), max_cpu="68010")[0]
    assert inst.text == "move.w  (a2),ccr"
    assert inst.kb_mnemonic == "MOVE to CCR"
    assert inst.operand_size == "w"

    inst = disassemble(assemble_instruction("move.l usp,a0"), max_cpu="68010")[0]
    assert inst.kb_mnemonic == "MOVE USP"
    assert inst.operand_size == "l"


def test_analyze_handles_special_move_without_text_lookup():
    code = bytes.fromhex("44 d2 4e 75")
    result = analyze(code, propagate=True, entry_points=[0])
    assert 0 in result["blocks"]


def test_disassemble_unsized_instruction_uses_kb_default_operand_size():
    inst = disassemble(assemble_instruction("bset #6,12(a1)"), max_cpu="68010")[0]
    assert inst.kb_mnemonic == "BSET"
    assert inst.operand_size == "w"


def test_extract_branch_target_uses_kb_mnemonic_not_text():
    inst = disassemble(assemble_instruction("bsr.w $10"), max_cpu="68010")[0]
    inst.text = "corrupted"

    assert extract_branch_target(inst, inst.offset) == 0x10


def test_extract_branch_target_uses_runtime_extension_branch_table_for_dbcc():
    inst = disassemble(assemble_instruction("dbf d0,$8"), max_cpu="68010")[0]

    assert extract_branch_target(inst, inst.offset) == 0x8


def test_extract_branch_target_uses_runtime_extension_branch_table_for_pdbcc():
    inst = disassemble(bytes.fromhex("f048000000004e71"), max_cpu="68040")[0]

    assert extract_branch_target(inst, inst.offset) == 0x2


def test_resolve_kb_mnemonic_uses_opcode_not_operand_text():
    opcode = int.from_bytes(assemble_instruction("move.w (a2),ccr")[:2], "big")
    assert _resolve_kb_mnemonic(opcode, "move.w") == "MOVE to CCR"


def test_resolve_kb_mnemonic_prefers_specialized_kb_entry():
    opcode = int.from_bytes(assemble_instruction("andi.b #$1f,ccr")[:2], "big")
    assert _resolve_kb_mnemonic(opcode, "andi.b") == "ANDI to CCR"


def test_resolve_kb_mnemonic_matches_kb_alias_token():
    assert _resolve_kb_mnemonic(0xF000, "pflusha") == "PFLUSH PFLUSHA"


def test_resolve_kb_mnemonic_rejects_non_token_input():
    opcode = int.from_bytes(assemble_instruction("move.w (a2),ccr")[:2], "big")

    with pytest.raises(ValueError, match="opcode token"):
        _resolve_kb_mnemonic(opcode, "move.w  garbage,garbage")




def test_semantic_operands_prefer_typed_nodes_for_simple_moveq():
    inst = disassemble(assemble_instruction("moveq #1,d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "register"]
    assert [op.text for op in ops] == ["#1", "d0"]
    assert ops[0].value == 1
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_simple_branch():
    inst = disassemble(assemble_instruction("bne.s $8"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["branch_target"]
    assert [op.text for op in ops] == ["$8"]
    assert ops[0].target_addr == 0x8


def test_semantic_operands_prefer_typed_nodes_for_lea_pc_relative():
    inst = disassemble(assemble_instruction("lea 8(pc),a0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["pc_relative_target", "register"]
    assert [op.text for op in ops] == ["8(pc)", "a0"]
    assert ops[0].target_addr == 0xA
    assert ops[1].register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_move_base_displacement():
    inst = disassemble(assemble_instruction("move.w 18(a1),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["base_displacement", "register"]
    assert [op.text for op in ops] == ["18(a1)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 18
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_move_immediate_ea():
    inst = disassemble(assemble_instruction("move.w #$1234,d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "register"]
    assert [op.text for op in ops] == ["#$1234", "d0"]
    assert ops[0].value == 0x1234
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_tst_indexed_ea():
    inst = disassemble(assemble_instruction("tst.w 8(a1,d2.w)"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed"]
    assert [op.text for op in ops] == ["8(a1,d2.w)"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert ops[0].metadata["index_register"] == "d2"


def test_semantic_operands_prefer_typed_nodes_for_tas_postincrement():
    inst = disassemble(assemble_instruction("tas (a0)+"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["postincrement"]
    assert [op.text for op in ops] == ["(a0)+"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_addq_indexed_ea():
    inst = disassemble(assemble_instruction("addq.w #1,8(a1,d2.w)"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "indexed"]
    assert [op.text for op in ops] == ["#1", "8(a1,d2.w)"]
    assert ops[0].value == 1
    assert ops[1].base_register == "a1"
    assert ops[1].displacement == 8
    assert ops[1].metadata["index_register"] == "d2"


def test_semantic_operands_prefer_typed_nodes_for_scc_postincrement():
    inst = disassemble(assemble_instruction("seq (a0)+"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["postincrement"]
    assert [op.text for op in ops] == ["(a0)+"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_dynamic_bitop_ea():
    inst = disassemble(assemble_instruction("bchg d0,8(a1,d2.w)"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "indexed"]
    assert [op.text for op in ops] == ["d0", "8(a1,d2.w)"]
    assert ops[0].register == "d0"
    assert ops[1].base_register == "a1"
    assert ops[1].displacement == 8
    assert ops[1].metadata["index_register"] == "d2"


def test_semantic_operands_prefer_typed_nodes_for_static_bitop_ea():
    inst = disassemble(assemble_instruction("bclr #3,(a0)+"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "postincrement"]
    assert [op.text for op in ops] == ["#3", "(a0)+"]
    assert ops[0].value == 3
    assert ops[1].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_or_indexed_ea():
    inst = disassemble(assemble_instruction("or.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert ops[0].metadata["index_register"] == "d2"


def test_semantic_operands_prefer_typed_nodes_for_adda_indexed_ea():
    inst = disassemble(assemble_instruction("adda.w 8(a1,d2.w),a0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "a0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert ops[0].metadata["index_register"] == "d2"
    assert ops[1].register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_divu_indexed_ea():
    inst = disassemble(assemble_instruction("divu.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert ops[0].metadata["index_register"] == "d2"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_mulu_indexed_ea():
    inst = disassemble(assemble_instruction("mulu.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert ops[0].metadata["index_register"] == "d2"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_chk_indexed_ea():
    inst = disassemble(assemble_instruction("chk.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert ops[0].metadata["index_register"] == "d2"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_movem_load_ea():
    inst = disassemble(assemble_instruction("movem.w 8(a1,d2.w),d0-d1"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage0", "garbage1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register_list"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0-d1"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert ops[0].metadata["index_register"] == "d2"
    assert ops[1].metadata["registers"] == ("d0", "d1")


def test_semantic_operands_prefer_typed_nodes_for_movem_store_ea():
    inst = disassemble(assemble_instruction("movem.w d0-d1,-(a7)"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage0", "garbage1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register_list", "predecrement"]
    assert [op.text for op in ops] == ["d0-d1", "-(sp)"]
    assert ops[0].metadata["registers"] == ("d0", "d1")
    assert ops[1].base_register == "sp"


def test_semantic_operands_prefer_typed_nodes_for_moves_store_ea():
    inst = disassemble(bytes.fromhex("0e500800"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "indirect"]
    assert [op.text for op in ops] == ["d0", "(a0)"]
    assert ops[0].register == "d0"
    assert ops[1].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_moves_load_ea():
    inst = disassemble(bytes.fromhex("0e500000"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect", "register"]
    assert [op.text for op in ops] == ["(a0)", "d0"]
    assert ops[0].base_register == "a0"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_callm_ea():
    inst = disassemble(assemble_instruction("callm #3,(a0)"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "indirect"]
    assert [op.text for op in ops] == ["#3", "(a0)"]
    assert ops[0].value == 3
    assert ops[1].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_immediate_indexed_ea():
    inst = disassemble(assemble_instruction("ori.w #$1234,8(a1,d2.w)"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "indexed"]
    assert [op.text for op in ops] == ["#$1234", "8(a1,d2.w)"]
    assert ops[0].value == 0x1234
    assert ops[1].base_register == "a1"
    assert ops[1].displacement == 8
    assert ops[1].metadata["index_register"] == "d2"


def test_semantic_operands_prefer_typed_nodes_for_cmp2_ea():
    inst = disassemble(bytes.fromhex("02d00000"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect", "register"]
    assert [op.text for op in ops] == ["(a0)", "d0"]
    assert ops[0].base_register == "a0"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_chk2_ea():
    inst = disassemble(bytes.fromhex("02d00800"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect", "register"]
    assert [op.text for op in ops] == ["(a0)", "d0"]
    assert ops[0].base_register == "a0"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_cas_ea():
    inst = disassemble(bytes.fromhex("0cd00040"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1", "junk2")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register", "indirect"]
    assert [op.text for op in ops] == ["d0", "d1", "(a0)"]
    assert ops[0].register == "d0"
    assert ops[1].register == "d1"
    assert ops[2].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_memory_shift_ea():
    inst = disassemble(assemble_instruction("asl.w (a0)"), max_cpu="68010")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect"]
    assert [op.text for op in ops] == ["(a0)"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_pscc_ea():
    inst = disassemble(bytes.fromhex("f0500000"), max_cpu="68040")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect"]
    assert [op.text for op in ops] == ["(a0)"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_pflushr_ea():
    inst = disassemble(bytes.fromhex("f010a000"), max_cpu="68040")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect"]
    assert [op.text for op in ops] == ["(a0)"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_bfextu():
    inst = disassemble(bytes.fromhex("e9c01088"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["bitfield_ea", "register"]
    assert [op.text for op in ops] == ["d0{2:8}", "d1"]
    assert ops[0].register == "d0"
    assert ops[0].metadata["bitfield"]["offset_value"] == 2
    assert ops[0].metadata["bitfield"]["width_value"] == 8
    assert ops[1].register == "d1"


def test_semantic_operands_prefer_typed_nodes_for_ext_register():
    inst = disassemble(assemble_instruction("ext.w d0"), max_cpu="68020")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register"]
    assert [op.text for op in ops] == ["d0"]
    assert ops[0].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_rtm_register():
    inst = disassemble(assemble_instruction("rtm d0"), max_cpu="68020")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register"]
    assert [op.text for op in ops] == ["d0"]
    assert ops[0].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_movec():
    inst = disassemble(bytes.fromhex("4e7b0000"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["d0", "sfc"]
    assert ops[0].register == "d0"
    assert ops[1].register == "sfc"


def test_semantic_operands_prefer_typed_nodes_for_move16_postinc_pair():
    inst = disassemble(bytes.fromhex("f6209000"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["postincrement", "postincrement"]
    assert [op.text for op in ops] == ["(a0)+", "(a1)+"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_prefer_typed_nodes_for_move16_absolute_to_postinc():
    inst = disassemble(bytes.fromhex("f60812345678"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["absolute_target", "postincrement"]
    assert ops[0].value == 0x12345678
    assert ops[1].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_move16_postinc_to_absolute():
    inst = disassemble(bytes.fromhex("f60012345678"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["postincrement", "absolute_target"]
    assert ops[0].base_register == "a0"
    assert ops[1].value == 0x12345678


def test_semantic_operands_prefer_typed_nodes_for_divsl_register_pair():
    inst = disassemble(bytes.fromhex("4c401800"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register_pair"]
    assert [op.text for op in ops] == ["d0", "d0:d1"]
    assert ops[1].metadata["registers"] == ["d1", "d0"]


def test_semantic_operands_prefer_typed_nodes_for_mulu_long_register_pair():
    inst = disassemble(bytes.fromhex("4c001402"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register_pair"]
    assert [op.text for op in ops] == ["d0", "d2:d1"]
    assert ops[1].metadata["registers"] == ["d2", "d1"]


def test_semantic_operands_build_addx_register_form():
    inst = disassemble(assemble_instruction("addx.b d0,d1"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["d0", "d1"]
    assert ops[0].register == "d0"
    assert ops[1].register == "d1"


def test_semantic_operands_build_subx_predecrement_form():
    inst = disassemble(assemble_instruction("subx.b -(a0),-(a1)"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["predecrement", "predecrement"]
    assert [op.text for op in ops] == ["-(a0)", "-(a1)"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_build_sbcd_predecrement_form():
    inst = disassemble(assemble_instruction("sbcd -(a0),-(a1)"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["predecrement", "predecrement"]
    assert [op.text for op in ops] == ["-(a0)", "-(a1)"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_build_abcd_predecrement_form():
    inst = disassemble(assemble_instruction("abcd -(a0),-(a1)"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["predecrement", "predecrement"]
    assert [op.text for op in ops] == ["-(a0)", "-(a1)"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_build_pack_register_form():
    inst = disassemble(bytes.fromhex("83400000"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1", "junk2")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register", "immediate"]
    assert [op.text for op in ops] == ["d0", "d1", "#$0"]
    assert ops[0].register == "d0"
    assert ops[1].register == "d1"
    assert ops[2].value == 0


def test_semantic_operands_build_pack_predecrement_form():
    inst = disassemble(bytes.fromhex("83480000"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1", "junk2")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["predecrement", "predecrement", "immediate"]
    assert [op.text for op in ops] == ["-(a0)", "-(a1)", "#$0"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"
    assert ops[2].value == 0


def test_semantic_operands_prefer_typed_nodes_for_movep_load_form():
    inst = disassemble(assemble_instruction("movep.w 2(a0),d1"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["base_displacement", "register"]
    assert [op.text for op in ops] == ["2(a0)", "d1"]
    assert ops[0].base_register == "a0"
    assert ops[0].displacement == 2
    assert ops[1].register == "d1"


def test_semantic_operands_prefer_typed_nodes_for_movep_store_form():
    inst = disassemble(assemble_instruction("movep.w d1,2(a0)"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "base_displacement"]
    assert [op.text for op in ops] == ["d1", "2(a0)"]
    assert ops[0].register == "d1"
    assert ops[1].base_register == "a0"
    assert ops[1].displacement == 2


def test_semantic_operands_build_cmpm_postincrement_form():
    inst = disassemble(assemble_instruction("cmpm.b (a0)+,(a1)+"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["postincrement", "postincrement"]
    assert [op.text for op in ops] == ["(a0)+", "(a1)+"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_build_pdbcc_register_and_target_form():
    inst = disassemble(bytes.fromhex("f048000000004e71"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "branch_target"]
    assert [op.text for op in ops] == ["d0", "$2"]
    assert ops[0].register == "d0"
    assert ops[1].target_addr == 2


def test_semantic_operands_build_pbcc_target_form():
    inst = disassemble(bytes.fromhex("f0800002"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["branch_target"]
    assert [op.text for op in ops] == ["$4"]
    assert ops[0].target_addr == 4


def test_semantic_operands_build_ptrapcc_immediate_form():
    inst = disassemble(bytes.fromhex("f07a000000014e71"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate"]
    assert [op.text for op in ops] == ["#1"]
    assert ops[0].value == 1


def test_semantic_operands_build_link_register_and_immediate_form():
    inst = disassemble(assemble_instruction("link a2,#-4"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "immediate"]
    assert [op.text for op in ops] == ["a2", "#-4"]
    assert ops[0].register == "a2"
    assert ops[1].value == 0xFFFFFFFC


def test_semantic_operands_build_link_long_register_and_immediate_form():
    inst = disassemble(bytes.fromhex("480afffffffc"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "immediate"]
    assert [op.text for op in ops] == ["a2", "#-4"]
    assert ops[0].register == "a2"
    assert ops[1].value == 0xFFFFFFFC


def test_semantic_operands_build_unlk_register_form():
    inst = disassemble(assemble_instruction("unlk a2"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register"]
    assert [op.text for op in ops] == ["a2"]
    assert ops[0].register == "a2"


def test_semantic_operands_build_swap_register_form():
    inst = disassemble(assemble_instruction("swap d3"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register"]
    assert [op.text for op in ops] == ["d3"]
    assert ops[0].register == "d3"


def test_semantic_operands_build_move_usp_register_forms():
    to_reg = disassemble(assemble_instruction("move.l usp,a2"), max_cpu="68010")[0]
    to_reg.operand_texts = ("junk0", "junk1")
    ops = build_instruction_semantic_operands(to_reg, _operand_session())
    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["usp", "a2"]
    assert ops[0].register == "usp"
    assert ops[1].register == "a2"

    from_reg = disassemble(assemble_instruction("move.l a2,usp"), max_cpu="68010")[0]
    from_reg.operand_texts = ("junk0", "junk1")
    ops = build_instruction_semantic_operands(from_reg, _operand_session())
    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["a2", "usp"]
    assert ops[0].register == "a2"
    assert ops[1].register == "usp"


def test_semantic_operands_build_move_usp_sp_alias_form():
    to_sp = disassemble(assemble_instruction("move.l usp,a7"), max_cpu="68010")[0]
    to_sp.operand_texts = ("junk0", "junk1")
    ops = build_instruction_semantic_operands(to_sp, _operand_session())
    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["usp", "sp"]
    assert ops[0].register == "usp"
    assert ops[1].register == "sp"

    from_sp = disassemble(assemble_instruction("move.l a7,usp"), max_cpu="68010")[0]
    from_sp.operand_texts = ("junk0", "junk1")
    ops = build_instruction_semantic_operands(from_sp, _operand_session())
    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["sp", "usp"]
    assert ops[0].register == "sp"
    assert ops[1].register == "usp"


def test_semantic_operands_prefer_typed_nodes_for_long_divmul_single_register():
    mulu = disassemble(bytes.fromhex("4c000000"), max_cpu="68020")[0]
    mulu.operand_texts = ("junk0", "junk1")
    ops = build_instruction_semantic_operands(mulu, _operand_session())
    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["d0", "d0"]
    assert ops[0].register == "d0"
    assert ops[1].register == "d0"

    divu = disassemble(bytes.fromhex("4c400000"), max_cpu="68020")[0]
    divu.operand_texts = ("junk0", "junk1")
    ops = build_instruction_semantic_operands(divu, _operand_session())
    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["d0", "d0"]
    assert ops[0].register == "d0"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_indexed_ea():
    inst = disassemble(assemble_instruction("move.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert ops[0].metadata["index_register"] == "d2"
    assert ops[0].metadata["index_size"] == "w"


def test_semantic_operands_prefer_typed_nodes_for_pc_indexed_ea():
    inst = disassemble(assemble_instruction("lea 8(pc,d2.w),a0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["pc_relative_indexed", "register"]
    assert [op.text for op in ops] == ["8(pc,d2.w)", "a0"]
    assert ops[0].metadata["index_register"] == "d2"
    assert ops[0].metadata["index_size"] == "w"
    assert ops[1].register == "a0"


def test_build_instruction_semantic_operands_use_full_extension_nodes_not_text():
    inst = disassemble(bytes.fromhex("2031212200000004"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "d0")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert ops[0].kind == "memory_indirect_indexed"
    assert ops[0].text == "([0,a1,d2.w],4)"
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 0
    assert ops[0].metadata == {
        "base_register": "a1",
        "index_register": "d2",
        "index_size": "w",
        "index_scale": 1,
        "memory_indirect": True,
        "postindexed": False,
        "preindexed": True,
        "base_suppressed": False,
        "index_suppressed": False,
        "base_displacement": 0,
        "outer_displacement": 4,
    }


def test_build_instruction_semantic_operands_use_postindexed_no_index_full_extension_nodes():
    inst = disassemble(bytes.fromhex("2235535f5e5e5e5f"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "d1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert ops[0].kind == "memory_indirect_indexed"
    assert ops[0].text == "([a5],1583242847)"
    assert ops[0].base_register == "a5"
    assert ops[0].displacement is None
    assert inst.operand_nodes[0].metadata == {
        "base_register": "a5",
        "base_displacement": None,
        "index_register": None,
        "index_size": None,
        "index_scale": None,
        "memory_indirect": True,
        "preindexed": False,
        "postindexed": True,
        "outer_displacement": 1583242847,
        "base_suppressed": False,
        "index_suppressed": True,
    }


def test_build_instruction_semantic_operands_use_full_extension_indexed_nodes_not_text():
    inst = disassemble(bytes.fromhex("20746f204144"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "a0")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert ops[0].kind == "indexed"
    assert ops[0].text == "(16708,a4,d6.l*8)"
    assert ops[0].base_register == "a4"
    assert ops[0].displacement == 16708
    assert ops[0].metadata["index_register"] == "d6"
    assert ops[0].metadata["index_size"] == "l"
    assert inst.operand_nodes[0].metadata["base_displacement"] == 16708
    assert inst.operand_nodes[0].metadata["displacement"] == 16708
    assert inst.operand_nodes[0].metadata["index_scale"] == 8


def test_resolve_operand_reads_full_extension_memory_indirect_indexed_ea():
    inst = disassemble(bytes.fromhex("2031212200000004"), max_cpu="68020")[0]
    decoded = decode_instruction_ops(inst, inst.kb_mnemonic, inst.operand_size)

    cpu = CPUState()
    cpu.set_reg("an", 1, _concrete(0x100))
    cpu.set_reg("dn", 2, _concrete(4))

    mem = AbstractMemory()
    mem.write(0x104, _concrete(0x200), "l")
    mem.write(0x204, _concrete(0x12345678), "l")

    value = _resolve_operand(decoded.ea_op, cpu, mem, "l", 4)

    assert value is not None
    assert value.is_known
    assert value.concrete == 0x12345678


def test_write_operand_writes_full_extension_memory_indirect_indexed_ea():
    inst = disassemble(bytes.fromhex("2031212200000004"), max_cpu="68020")[0]
    decoded = decode_instruction_ops(inst, inst.kb_mnemonic, inst.operand_size)

    cpu = CPUState()
    cpu.set_reg("an", 1, _concrete(0x100))
    cpu.set_reg("dn", 2, _concrete(4))

    mem = AbstractMemory()
    mem.write(0x104, _concrete(0x200), "l")

    _write_operand(decoded.ea_op, cpu, mem, _concrete(0x89ABCDEF), "l", 4)

    written = mem.read(0x204, "l")
    assert written.is_known
    assert written.concrete == 0x89ABCDEF


def test_resolve_ea_handles_full_extension_base_suppressed_indexed_form():
    operand = Operand(
        mode="index",
        reg=1,
        value=8,
        index_reg=2,
        index_is_addr=False,
        index_size="w",
        index_scale=1,
        full_extension=True,
        memory_indirect=False,
        postindexed=False,
        base_suppressed=True,
        index_suppressed=False,
        base_displacement=8,
        outer_displacement=None,
    )
    cpu = CPUState()
    cpu.set_reg("dn", 2, _concrete(4))

    ea = resolve_ea(operand, cpu, "l")

    assert ea is not None
    assert ea.is_known
    assert ea.concrete == 12

