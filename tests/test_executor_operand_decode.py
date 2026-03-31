from __future__ import annotations

import copy
from collections.abc import Callable
from types import ModuleType
from typing import cast

import pytest
from _pytest.monkeypatch import MonkeyPatch

from disasm import operands as operands_mod
from disasm.operands import (
    build_instruction_semantic_operands,
    instruction_operands_render_completely,
)
from disasm.types import (
    BitfieldOperandMetadata,
    FullIndexedOperandMetadata,
    HunkDisassemblySession,
    IndexedOperandMetadata,
    RegisterListOperandMetadata,
    RegisterPairOperandMetadata,
    SemanticOperand,
)
from m68k import m68k_asm as asm_mod
from m68k import m68k_executor as executor_mod
from m68k.abstract_values import _concrete
from m68k.instruction_decode import (
    DecodedBitfield,
    DecodedOperands,
    decode_inst_destination,
    decode_inst_operands,
    instruction_immediate_value,
)
from m68k.instruction_primitives import (
    Operand,
    decode_instruction_ops,
    extract_branch_target,
)
from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import (
    DecodedBaseDisplacementNodeMetadata,
    DecodedBaseRegisterNodeMetadata,
    DecodedBitfieldNodeMetadata,
    DecodedFullExtensionNodeMetadata,
    DecodedIndexedNodeMetadata,
    DecodedOperandNode,
    DecodedRegisterListNodeMetadata,
    DecodedRegisterPairNodeMetadata,
    Instruction,
    _resolve_kb_mnemonic,
    disassemble,
)
from m68k.m68k_executor import (
    AbstractMemory,
    CPUState,
    _resolve_operand,
    _write_operand,
    analyze,
)
from m68k.operand_resolution import resolve_ea
from m68k.typing_protocols import InstructionLike
from m68k_kb import (
    runtime_m68k_analysis,
    runtime_m68k_asm,
    runtime_m68k_decode,
    runtime_m68k_executor,
)
from tests.os_kb_helpers import make_empty_os_kb
from tests.platform_helpers import make_platform

_TestFn = Callable[..., object]
_Decorator = Callable[[_TestFn], _TestFn]
_parametrize = cast(Callable[..., _Decorator], pytest.mark.parametrize)

def _decoded_ops(asm: str, kb_mnemonic: str) -> DecodedOperands:
    raw = assemble_instruction(asm)
    inst = disassemble(raw, max_cpu="68010")[0]
    return _decode_ops(inst, kb_mnemonic, "l")


def _decode_ops(inst: Instruction, kb_mnemonic: str | None, size: str | None) -> DecodedOperands:
    return cast(
        DecodedOperands,
        decode_instruction_ops(cast(InstructionLike, inst), kb_mnemonic, size),
    )


def _operand_session() -> HunkDisassemblySession:
    return HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )


def _operand_nodes(inst: Instruction) -> tuple[DecodedOperandNode, ...]:
    assert inst.operand_nodes is not None
    nodes: tuple[DecodedOperandNode, ...] = inst.operand_nodes
    return nodes


def _reload_executor_with_runtime_tables(
    monkeypatch: MonkeyPatch,
    mutate_tables: Callable[[dict[str, object]], object],
) -> ModuleType:
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
    module: ModuleType = executor_mod
    return module


@_parametrize(
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
def test_decode_opcode_returns_structured_instruction_text(
    raw: bytes,
    group: int,
) -> None:
    from m68k import m68k_disasm as disasm_mod

    d = disasm_mod._Decoder(raw, 0)
    opcode = d.read_u16()
    decoded = disasm_mod._decode_opcode(d, opcode, group, 0)

    assert isinstance(decoded, disasm_mod.DecodedInstructionText)


def test_assemble_instruction_uses_kb_opmode_direction_for_cmp() -> None:
    assert assemble_instruction("cmp.w d1,d0") == bytes.fromhex("b041")


@_parametrize(
    "asm",
    [
        "addi #1,d0",
        "ori #1,d0",
        "clr d0",
        "cmp d1,d0",
    ],
)
def test_assemble_instruction_uses_kb_default_operand_size_when_suffix_omitted(asm: str) -> None:
    mnemonic, rest = asm.split(" ", 1)
    assert assemble_instruction(asm) == assemble_instruction(f"{mnemonic}.w {rest}")


@_parametrize(
    "asm",
    [
        "move a0,sr",
        "move a0,ccr",
        "move sr,a0",
        "move ccr,a0",
    ],
)
def test_assemble_instruction_rejects_invalid_special_move_an_modes(asm: str) -> None:
    with pytest.raises(ValueError, match="invalid .* EA mode an"):
        assemble_instruction(asm)


@_parametrize(
    "asm",
    [
        "callm #3,a0",
        "addi #1,a0",
        "subi #1,a0",
        "ori #1,a0",
        "andi #1,a0",
        "eori #1,a0",
        "cmpi #1,a0",
    ],
)
def test_assemble_instruction_rejects_invalid_immediate_target_an_modes(asm: str) -> None:
    with pytest.raises(ValueError, match="invalid target EA mode an"):
        assemble_instruction(asm)


@_parametrize(
    "asm",
    [
        "clr a0",
        "neg a0",
        "not a0",
        "tas a0",
        "pea d0",
        "lea d0,a0",
        "jsr d0",
        "jmp d0",
    ],
)
def test_assemble_instruction_rejects_invalid_single_ea_modes(asm: str) -> None:
    with pytest.raises(ValueError, match="invalid target EA mode"):
        assemble_instruction(asm)


@_parametrize(
    "asm",
    [
        "bset #1,a0",
        "bclr #1,a0",
        "bchg #1,a0",
        "btst #1,a0",
        "bset d0,a0",
        "bclr d0,a0",
        "bchg d0,a0",
        "btst d0,a0",
    ],
)
def test_assemble_instruction_rejects_invalid_bitop_target_an_modes(asm: str) -> None:
    with pytest.raises(ValueError, match="invalid target EA mode an"):
        assemble_instruction(asm)


@_parametrize(
    "asm",
    [
        "movem.w d0-d1,d0",
        "movem.w d0-d1,a0",
        "movem.w d0,d0-d1",
        "movem.w a0,d0-d1",
    ],
)
def test_assemble_instruction_rejects_invalid_movem_register_direct_modes(asm: str) -> None:
    with pytest.raises(ValueError, match="invalid target EA mode"):
        assemble_instruction(asm)


@_parametrize(
    "asm",
    [
        "chk.w a0,d1",
        "mulu.w a0,d1",
        "muls.w a0,d1",
        "divu.w a0,d1",
        "divs.w a0,d1",
    ],
)
def test_assemble_instruction_rejects_invalid_ea_dn_source_an_modes(asm: str) -> None:
    with pytest.raises(ValueError, match="invalid source EA mode an"):
        assemble_instruction(asm)


def test_decode_instruction_ops_uses_shared_kb_decoder_for_move_usp() -> None:
    decoded = _decoded_ops("move.l usp,a0", "MOVE USP")
    assert decoded.reg_num == 0
    assert decoded.ea_is_source is True

    decoded = _decoded_ops("move.l a1,usp", "MOVE USP")
    assert decoded.reg_num == 1
    assert decoded.ea_is_source is False


def test_decode_instruction_ops_caches_by_instruction(
    monkeypatch: MonkeyPatch,
) -> None:
    inst = disassemble(assemble_instruction("move.l usp,a0"), max_cpu="68010")[0]
    calls = {"count": 0}
    from m68k import instruction_decode as decode_mod
    real = cast(Callable[..., DecodedOperands], decode_mod.decode_instruction_operands)

    def counting_decode(*args: object, **kwargs: object) -> DecodedOperands:
        calls["count"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(decode_mod, "decode_instruction_operands",
                        counting_decode, raising=False)
    from m68k import instruction_primitives as primitives_mod
    primitives_mod._DECODED_OPS_CACHE.clear()

    first = _decode_ops(inst, "MOVE USP", "l")
    second = _decode_ops(inst, "MOVE USP", "l")

    assert first == second
    assert calls["count"] == 1


def test_decode_inst_operands_uses_instruction_fields_directly() -> None:
    inst = disassemble(assemble_instruction("move.l usp,a0"), max_cpu="68010")[0]

    decoded = decode_inst_operands(inst, "MOVE USP")

    assert isinstance(decoded, DecodedOperands)
    assert decoded.reg_num == 0
    assert decoded.ea_is_source is True


def test_decode_inst_destination_uses_instruction_fields_directly() -> None:
    inst = disassemble(assemble_instruction("moveq #-1,d3"), max_cpu="68010")[0]

    dst = decode_inst_destination(inst, "MOVEQ")

    assert dst == ("dn", 3)


def test_decode_inst_destination_preserves_address_register_destination() -> None:
    inst = disassemble(assemble_instruction("lea 4(a6),a1"), max_cpu="68010")[0]

    dst = decode_inst_destination(inst, "LEA")

    assert dst == ("an", 1)


@_parametrize(
    ("asm", "mnemonic", "expected"),
    [
        ("movea.l 4(a6),a2", "MOVEA", ("an", 2)),
        ("adda.l 4(a6),a3", "ADDA", ("an", 3)),
        ("suba.l 4(a6),a4", "SUBA", ("an", 4)),
        ("unlk a5", "UNLK", ("an", 5)),
    ],
)
def test_decode_inst_destination_preserves_kb_register_class_for_address_writers(
    asm: str,
    mnemonic: str,
    expected: tuple[str, int],
) -> None:
    inst = disassemble(assemble_instruction(asm), max_cpu="68010")[0]

    dst = decode_inst_destination(inst, mnemonic)

    assert dst == expected


def test_decode_inst_destination_requires_operand_types_from_decoded_form(
    monkeypatch: MonkeyPatch,
) -> None:
    inst = disassemble(assemble_instruction("lea 4(a6),a1"), max_cpu="68010")[0]
    real = decode_inst_operands(inst, "LEA")
    broken = type("BrokenDecoded", (), {
        "ea_op": real.ea_op,
        "dst_op": real.dst_op,
        "reg_num": real.reg_num,
        "imm_val": real.imm_val,
        "ea_is_source": real.ea_is_source,
        "compare_reg": real.compare_reg,
        "update_reg": real.update_reg,
        "reg_mode": real.reg_mode,
        "secondary_reg": real.secondary_reg,
        "control_register": real.control_register,
        "bitfield": real.bitfield,
    })()

    monkeypatch.setattr(
        "m68k.instruction_decode.decode_instruction_operands",
        lambda *args, **kwargs: broken,
    )

    with pytest.raises(AttributeError, match="operand_types"):
        decode_inst_destination(inst, "LEA")


def test_decode_instruction_ops_errors_when_move_usp_kb_field_missing() -> None:
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
            _decode_ops(inst, inst_kb, "l")


def test_decode_inst_operands_requires_runtime_form_operand_types() -> None:
    inst = disassemble(assemble_instruction("moveq #-1,d3"), max_cpu="68010")[0]
    form_operand_types = copy.deepcopy(runtime_m68k_decode.FORM_OPERAND_TYPES)
    del form_operand_types["MOVEQ"]

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            runtime_m68k_decode,
            "FORM_OPERAND_TYPES",
            form_operand_types,
            raising=False,
        )
        with pytest.raises(KeyError, match="MOVEQ"):
            decode_inst_operands(inst, "MOVEQ")


def test_assemble_instruction_requires_matching_asm_syntax_form() -> None:
    asm_syntax_index = copy.deepcopy(runtime_m68k_asm.ASM_SYNTAX_INDEX)
    form_operand_types = copy.deepcopy(runtime_m68k_asm.FORM_OPERAND_TYPES)
    asm_syntax_index[("move", ("dn", "dn"))] = ("MOVE", ("dn", "dn"))
    form_operand_types["MOVE"] = (("ea", "an"),)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            runtime_m68k_asm,
            "ASM_SYNTAX_INDEX",
            asm_syntax_index,
            raising=False,
        )
        monkeypatch.setattr(
            runtime_m68k_asm,
            "FORM_OPERAND_TYPES",
            form_operand_types,
            raising=False,
        )
        with pytest.raises(KeyError, match="ASM_SYNTAX_INDEX resolved"):
            asm_mod._resolve_by_syntax_index("move", ["d0", "d1"])


def test_decode_instruction_ops_requires_runtime_raw_fields_for_mnemonic() -> None:
    inst = disassemble(assemble_instruction("move.l usp,a0"), max_cpu="68010")[0]
    raw_fields = list(copy.deepcopy(runtime_m68k_decode.RAW_FIELDS))
    raw_fields[0] = dict(raw_fields[0])
    del raw_fields[0]["MOVE USP"]

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(runtime_m68k_decode, "RAW_FIELDS", tuple(raw_fields), raising=False)
        with pytest.raises((KeyError, ValueError), match="MOVE USP"):
            _decode_ops(inst, "MOVE USP", "l")


def test_decode_instruction_ops_requires_runtime_movec_control_registers(
    monkeypatch: MonkeyPatch,
) -> None:
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
        _decode_ops(inst, "MOVEC", inst.operand_size)


def test_analyze_requires_runtime_opmode_table_for_exg(
    monkeypatch: MonkeyPatch,
) -> None:
    reloaded = _reload_executor_with_runtime_tables(
        monkeypatch,
        lambda attrs: cast(dict[str, object], attrs["OPMODE_TABLES_BY_VALUE"]).pop("EXG"),
    )

    with pytest.raises(AssertionError, match="opmode table for EXG"):
        reloaded.analyze(
            assemble_instruction("exg d0,d1"),
            propagate=True,
            entry_points=[0],
        )


def test_analyze_requires_runtime_single_register_field_for_swap(
    monkeypatch: MonkeyPatch,
) -> None:
    reloaded = _reload_executor_with_runtime_tables(
        monkeypatch,
        lambda attrs: cast(dict[str, object], attrs["REGISTER_FIELDS"]).pop("SWAP"),
    )

    with pytest.raises(AssertionError, match="single register field for SWAP"):
        reloaded.analyze(
            assemble_instruction("swap d0"),
            propagate=True,
            entry_points=[0],
        )


def test_analyze_requires_runtime_immediate_range_for_signed_moveq(
    monkeypatch: MonkeyPatch,
) -> None:
    reloaded = _reload_executor_with_runtime_tables(
        monkeypatch,
        lambda attrs: cast(dict[str, object], attrs["IMMEDIATE_RANGES"]).pop("MOVEQ"),
    )

    with pytest.raises(AssertionError, match="immediate range for MOVEQ"):
        reloaded.analyze(
            assemble_instruction("moveq #-1,d0"),
            propagate=True,
            entry_points=[0],
        )


def test_analyze_requires_runtime_compute_formula_for_moveq(
    monkeypatch: MonkeyPatch,
) -> None:
    formulas = copy.deepcopy(runtime_m68k_analysis.COMPUTE_FORMULAS)
    del formulas["MOVEQ"]
    monkeypatch.setattr(runtime_m68k_analysis, "COMPUTE_FORMULAS", formulas, raising=False)

    with pytest.raises(KeyError, match="MOVEQ"):
        analyze(
            assemble_instruction("moveq #-1,d0"),
            propagate=True,
            entry_points=[0],
        )


def test_analyze_does_not_require_runtime_sp_effects_for_rts(
    monkeypatch: MonkeyPatch,
) -> None:
    sp_effects = copy.deepcopy(runtime_m68k_analysis.SP_EFFECTS)
    del sp_effects["RTS"]
    monkeypatch.setattr(runtime_m68k_analysis, "SP_EFFECTS", sp_effects, raising=False)

    analyze(
        assemble_instruction("rts"),
        propagate=True,
        entry_points=[0],
    )


def test_analyze_requires_runtime_flow_type_for_rts(
    monkeypatch: MonkeyPatch,
) -> None:
    flow_types = copy.deepcopy(runtime_m68k_analysis.FLOW_TYPES)
    del flow_types["RTS"]
    monkeypatch.setattr(runtime_m68k_analysis, "FLOW_TYPES", flow_types, raising=False)

    with pytest.raises(KeyError, match="RTS"):
        analyze(
            assemble_instruction("rts"),
            propagate=True,
            entry_points=[0],
        )


def test_analyze_requires_runtime_operation_type_for_exg(
    monkeypatch: MonkeyPatch,
) -> None:
    operation_types = copy.deepcopy(runtime_m68k_executor.OPERATION_TYPES)
    del operation_types["EXG"]
    monkeypatch.setattr(runtime_m68k_executor, "OPERATION_TYPES", operation_types, raising=False)

    with pytest.raises(KeyError, match="EXG"):
        analyze(
            assemble_instruction("exg d0,d1"),
            propagate=True,
            entry_points=[0],
        )


def test_analyze_requires_runtime_operation_class_for_lea(
    monkeypatch: MonkeyPatch,
) -> None:
    operation_classes = copy.deepcopy(runtime_m68k_executor.OPERATION_CLASSES)
    del operation_classes["LEA"]
    monkeypatch.setattr(runtime_m68k_executor, "OPERATION_CLASSES", operation_classes, raising=False)

    with pytest.raises(KeyError, match="LEA"):
        analyze(
            assemble_instruction("lea 8(a0),a1"),
            propagate=True,
            entry_points=[0],
        )


def test_decode_instruction_ops_skips_immediate_word_before_indexed_ea() -> None:
    inst = disassemble(bytes.fromhex("0c72ffff2000"), max_cpu="68010")[0]
    decoded = _decode_ops(inst, "CMPI", inst.operand_size)

    assert decoded.imm_val == 0xFFFF
    assert decoded.ea_op is not None
    assert decoded.ea_op.mode == "index"
    assert decoded.ea_op.reg == 2
    assert decoded.ea_op.value == 0
    assert decoded.ea_op.index_reg == 2
    assert decoded.ea_op.index_size == "w"


def test_decode_instruction_ops_skips_immediate_word_before_full_extension_ea(
) -> None:
    inst = disassemble(bytes.fromhex("0470634e7570004e754e"), max_cpu="68020")[0]
    decoded = _decode_ops(inst, "SUBI", inst.operand_size)

    assert decoded.imm_val == 0x634E
    assert decoded.ea_op is not None
    assert decoded.ea_op.mode == "index"
    assert decoded.ea_op.reg == 0
    assert decoded.ea_op.full_extension is True
    assert decoded.ea_op.base_displacement == 5141838


def test_instruction_immediate_value_reads_moveq_immediate() -> None:
    inst = disassemble(assemble_instruction("moveq #-1,d3"), max_cpu="68010")[0]

    assert instruction_immediate_value(inst, "MOVEQ") == 0xFFFFFFFF


def test_instruction_immediate_value_reads_long_immediate_ea_value() -> None:
    inst = disassemble(assemble_instruction("move.l #$1000,d1"), max_cpu="68010")[0]

    assert instruction_immediate_value(inst, "MOVE") == 0x1000


def test_disassemble_special_move_uses_exact_kb_entry() -> None:
    inst = disassemble(bytes.fromhex("44 d2"), max_cpu="68010")[0]
    assert inst.text == "move.w  (a2),ccr"
    assert inst.kb_mnemonic == "MOVE to CCR"
    assert inst.operand_size == "w"

    inst = disassemble(assemble_instruction("move.l usp,a0"), max_cpu="68010")[0]
    assert inst.kb_mnemonic == "MOVE USP"
    assert inst.operand_size == "l"


def test_analyze_handles_special_move_without_text_lookup() -> None:
    code = bytes.fromhex("44 d2 4e 75")
    result = analyze(code, propagate=True, entry_points=[0])
    assert 0 in result["blocks"]


def test_disassemble_unsized_instruction_uses_kb_default_operand_size() -> None:
    inst = disassemble(assemble_instruction("bset #6,12(a1)"), max_cpu="68010")[0]
    assert inst.kb_mnemonic == "BSET"
    assert inst.operand_size == "w"


def test_extract_branch_target_uses_kb_mnemonic_not_text() -> None:
    inst = disassemble(assemble_instruction("bsr.w $10"), max_cpu="68010")[0]
    inst.text = "corrupted"

    assert extract_branch_target(inst, inst.offset) == 0x10


def test_extract_branch_target_uses_runtime_extension_branch_table_for_dbcc() -> None:
    inst = disassemble(assemble_instruction("dbf d0,$8"), max_cpu="68010")[0]

    assert extract_branch_target(inst, inst.offset) == 0x8


def test_extract_branch_target_uses_runtime_extension_branch_table_for_pdbcc() -> None:
    inst = disassemble(bytes.fromhex("f048000000004e71"), max_cpu="68040")[0]

    assert extract_branch_target(inst, inst.offset) == 0x2


def test_resolve_kb_mnemonic_uses_opcode_not_operand_text() -> None:
    opcode = int.from_bytes(assemble_instruction("move.w (a2),ccr")[:2], "big")
    assert _resolve_kb_mnemonic(opcode, "move.w") == "MOVE to CCR"


def test_resolve_kb_mnemonic_prefers_specialized_kb_entry() -> None:
    opcode = int.from_bytes(assemble_instruction("andi.b #$1f,ccr")[:2], "big")
    assert _resolve_kb_mnemonic(opcode, "andi.b") == "ANDI to CCR"


def test_build_instruction_semantic_operands_supports_immediate_to_ccr() -> None:
    inst = disassemble(assemble_instruction("andi.b #$1f,ccr"), max_cpu="68010")[0]

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.text for op in ops] == ["#$1f", "ccr"]


def test_resolve_kb_mnemonic_matches_kb_alias_token() -> None:
    assert _resolve_kb_mnemonic(0xF000, "pflusha") == "PFLUSH PFLUSHA"


def test_resolve_kb_mnemonic_rejects_non_token_input() -> None:
    opcode = int.from_bytes(assemble_instruction("move.w (a2),ccr")[:2], "big")

    with pytest.raises(ValueError, match="opcode token"):
        _resolve_kb_mnemonic(opcode, "move.w  garbage,garbage")




def test_semantic_operands_prefer_typed_nodes_for_simple_moveq() -> None:
    inst = disassemble(assemble_instruction("moveq #1,d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "register"]
    assert [op.text for op in ops] == ["#1", "d0"]
    assert ops[0].value == 1
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_simple_branch() -> None:
    inst = disassemble(assemble_instruction("bne.s $8"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["branch_target"]
    assert [op.text for op in ops] == ["$8"]
    assert ops[0].segment_addr == 0x8


def test_semantic_operands_prefer_typed_nodes_for_lea_pc_relative() -> None:
    inst = disassemble(assemble_instruction("lea 8(pc),a0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["pc_relative_target", "register"]
    assert [op.text for op in ops] == ["8(pc)", "a0"]
    assert ops[0].segment_addr == 0xA
    assert ops[1].register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_move_base_displacement() -> None:
    inst = disassemble(assemble_instruction("move.w 18(a1),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    metadata = _operand_nodes(inst)[0].metadata
    assert isinstance(metadata, DecodedBaseDisplacementNodeMetadata)
    assert metadata.base_register == "a1"
    assert metadata.displacement == 18

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["base_displacement", "register"]
    assert [op.text for op in ops] == ["18(a1)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 18
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_move_immediate_ea() -> None:
    inst = disassemble(assemble_instruction("move.w #$1234,d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "register"]
    assert [op.text for op in ops] == ["#$1234", "d0"]
    assert ops[0].value == 0x1234
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_tst_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("tst.w 8(a1,d2.w)"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed"]
    assert [op.text for op in ops] == ["8(a1,d2.w)"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d2"


def test_semantic_operands_prefer_typed_nodes_for_tas_postincrement() -> None:
    inst = disassemble(assemble_instruction("tas (a0)+"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage",)

    metadata = _operand_nodes(inst)[0].metadata
    assert isinstance(metadata, DecodedBaseRegisterNodeMetadata)
    assert metadata.base_register == "a0"

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["postincrement"]
    assert [op.text for op in ops] == ["(a0)+"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_addq_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("addq.w #1,8(a1,d2.w)"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "indexed"]
    assert [op.text for op in ops] == ["#1", "8(a1,d2.w)"]
    assert ops[0].value == 1
    assert ops[1].base_register == "a1"
    assert ops[1].displacement == 8
    assert isinstance(ops[1].metadata, IndexedOperandMetadata)
    assert ops[1].metadata.index_register == "d2"


def test_semantic_operands_prefer_typed_nodes_for_scc_postincrement() -> None:
    inst = disassemble(assemble_instruction("seq (a0)+"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["postincrement"]
    assert [op.text for op in ops] == ["(a0)+"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_dynamic_bitop_ea() -> None:
    inst = disassemble(assemble_instruction("bchg d0,8(a1,d2.w)"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "indexed"]
    assert [op.text for op in ops] == ["d0", "8(a1,d2.w)"]
    assert ops[0].register == "d0"
    assert ops[1].base_register == "a1"
    assert ops[1].displacement == 8
    assert isinstance(ops[1].metadata, IndexedOperandMetadata)
    assert ops[1].metadata.index_register == "d2"


def test_semantic_operands_prefer_typed_nodes_for_static_bitop_ea() -> None:
    inst = disassemble(assemble_instruction("bclr #3,(a0)+"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "postincrement"]
    assert [op.text for op in ops] == ["#3", "(a0)+"]
    assert ops[0].value == 3
    assert ops[1].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_or_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("or.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d2"


def test_semantic_operands_prefer_typed_nodes_for_adda_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("adda.w 8(a1,d2.w),a0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "a0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d2"
    assert ops[1].register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_divu_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("divu.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d2"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_mulu_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("mulu.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d2"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_chk_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("chk.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d2"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_movem_load_ea() -> None:
    inst = disassemble(assemble_instruction("movem.w 8(a1,d2.w),d0-d1"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage0", "garbage1")

    metadata = _operand_nodes(inst)[1].metadata
    assert isinstance(metadata, DecodedRegisterListNodeMetadata)
    assert metadata.registers == ("d0", "d1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register_list"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0-d1"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d2"
    assert isinstance(ops[1].metadata, RegisterListOperandMetadata)
    assert ops[1].metadata.registers == ("d0", "d1")


def test_semantic_operands_prefer_typed_nodes_for_movem_store_ea() -> None:
    inst = disassemble(assemble_instruction("movem.w d0-d1,-(a7)"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage0", "garbage1")

    metadata = _operand_nodes(inst)[0].metadata
    assert isinstance(metadata, DecodedRegisterListNodeMetadata)
    assert metadata.registers == ("d0", "d1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register_list", "predecrement"]
    assert [op.text for op in ops] == ["d0-d1", "-(sp)"]
    assert isinstance(ops[0].metadata, RegisterListOperandMetadata)
    assert ops[0].metadata.registers == ("d0", "d1")
    assert ops[1].base_register == "sp"


def test_semantic_operands_prefer_typed_nodes_for_moves_store_ea() -> None:
    inst = disassemble(bytes.fromhex("0e500800"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    metadata = _operand_nodes(inst)[1].metadata
    assert isinstance(metadata, DecodedBaseRegisterNodeMetadata)
    assert metadata.base_register == "a0"

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "indirect"]
    assert [op.text for op in ops] == ["d0", "(a0)"]
    assert ops[0].register == "d0"
    assert ops[1].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_moves_load_ea() -> None:
    inst = disassemble(bytes.fromhex("0e500000"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect", "register"]
    assert [op.text for op in ops] == ["(a0)", "d0"]
    assert ops[0].base_register == "a0"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_callm_ea() -> None:
    inst = disassemble(assemble_instruction("callm #3,(a0)"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "indirect"]
    assert [op.text for op in ops] == ["#3", "(a0)"]
    assert ops[0].value == 3
    assert ops[1].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_immediate_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("ori.w #$1234,8(a1,d2.w)"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate", "indexed"]
    assert [op.text for op in ops] == ["#$1234", "8(a1,d2.w)"]
    assert ops[0].value == 0x1234
    assert ops[1].base_register == "a1"
    assert ops[1].displacement == 8
    assert isinstance(ops[1].metadata, IndexedOperandMetadata)
    assert ops[1].metadata.index_register == "d2"


def test_semantic_operands_prefer_typed_nodes_for_cmp2_ea() -> None:
    inst = disassemble(bytes.fromhex("02d00000"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect", "register"]
    assert [op.text for op in ops] == ["(a0)", "d0"]
    assert ops[0].base_register == "a0"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_chk2_ea() -> None:
    inst = disassemble(bytes.fromhex("02d00800"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "junk")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect", "register"]
    assert [op.text for op in ops] == ["(a0)", "d0"]
    assert ops[0].base_register == "a0"
    assert ops[1].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_cas_ea() -> None:
    inst = disassemble(bytes.fromhex("0cd00040"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1", "junk2")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register", "indirect"]
    assert [op.text for op in ops] == ["d0", "d1", "(a0)"]
    assert ops[0].register == "d0"
    assert ops[1].register == "d1"
    assert ops[2].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_memory_shift_ea() -> None:
    inst = disassemble(assemble_instruction("asl.w (a0)"), max_cpu="68010")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect"]
    assert [op.text for op in ops] == ["(a0)"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_pscc_ea() -> None:
    inst = disassemble(bytes.fromhex("f0500000"), max_cpu="68040")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect"]
    assert [op.text for op in ops] == ["(a0)"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_pflushr_ea() -> None:
    inst = disassemble(bytes.fromhex("f010a000"), max_cpu="68040")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indirect"]
    assert [op.text for op in ops] == ["(a0)"]
    assert ops[0].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_bfextu() -> None:
    inst = disassemble(bytes.fromhex("e9c01088"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    metadata = _operand_nodes(inst)[0].metadata
    assert isinstance(metadata, DecodedBitfieldNodeMetadata)
    assert metadata.offset_value == 2
    assert metadata.width_value == 8

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["bitfield_ea", "register"]
    assert [op.text for op in ops] == ["d0{2:8}", "d1"]
    assert ops[0].register == "d0"
    assert isinstance(ops[0].metadata, BitfieldOperandMetadata)
    assert isinstance(ops[0].metadata.bitfield, DecodedBitfield)
    assert ops[0].metadata.bitfield.offset_value == 2
    assert ops[0].metadata.bitfield.width_value == 8
    assert ops[1].register == "d1"


def test_semantic_operands_prefer_typed_nodes_for_ext_register() -> None:
    inst = disassemble(assemble_instruction("ext.w d0"), max_cpu="68020")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register"]
    assert [op.text for op in ops] == ["d0"]
    assert ops[0].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_rtm_register() -> None:
    inst = disassemble(assemble_instruction("rtm d0"), max_cpu="68020")[0]
    inst.operand_texts = ("junk",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register"]
    assert [op.text for op in ops] == ["d0"]
    assert ops[0].register == "d0"


def test_semantic_operands_prefer_typed_nodes_for_movec() -> None:
    inst = disassemble(bytes.fromhex("4e7b0000"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["d0", "sfc"]
    assert ops[0].register == "d0"
    assert ops[1].register == "sfc"


def test_semantic_operands_prefer_typed_nodes_for_move16_postinc_pair() -> None:
    inst = disassemble(bytes.fromhex("f6209000"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["postincrement", "postincrement"]
    assert [op.text for op in ops] == ["(a0)+", "(a1)+"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_prefer_typed_nodes_for_move16_absolute_to_postinc() -> None:
    inst = disassemble(bytes.fromhex("f60812345678"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0", "junk1")
    session = _operand_session()
    session.labels[0x12345678] = "abs_12345678"

    ops = build_instruction_semantic_operands(inst, session)

    assert [op.kind for op in ops] == ["absolute_target", "postincrement"]
    assert ops[0].value == 0x12345678
    assert ops[1].base_register == "a0"


def test_semantic_operands_prefer_typed_nodes_for_move16_postinc_to_absolute() -> None:
    inst = disassemble(bytes.fromhex("f60012345678"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0", "junk1")
    session = _operand_session()
    session.labels[0x12345678] = "abs_12345678"

    ops = build_instruction_semantic_operands(inst, session)

    assert [op.kind for op in ops] == ["postincrement", "absolute_target"]
    assert ops[0].base_register == "a0"
    assert ops[1].value == 0x12345678


def test_semantic_operands_prefer_typed_nodes_for_divsl_register_pair() -> None:
    inst = disassemble(bytes.fromhex("4c401800"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    metadata = _operand_nodes(inst)[1].metadata
    assert isinstance(metadata, DecodedRegisterPairNodeMetadata)
    assert metadata.registers == ("d1", "d0")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register_pair"]
    assert [op.text for op in ops] == ["d0", "d0:d1"]
    assert isinstance(ops[1].metadata, RegisterPairOperandMetadata)
    assert ops[1].metadata.registers == ("d1", "d0")


def test_semantic_operands_prefer_typed_nodes_for_mulu_long_register_pair() -> None:
    inst = disassemble(bytes.fromhex("4c001402"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    metadata = _operand_nodes(inst)[1].metadata
    assert isinstance(metadata, DecodedRegisterPairNodeMetadata)
    assert metadata.registers == ("d2", "d1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register_pair"]
    assert [op.text for op in ops] == ["d0", "d2:d1"]
    assert isinstance(ops[1].metadata, RegisterPairOperandMetadata)
    assert ops[1].metadata.registers == ("d2", "d1")


def test_semantic_operands_build_addx_register_form() -> None:
    inst = disassemble(assemble_instruction("addx.b d0,d1"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register"]
    assert [op.text for op in ops] == ["d0", "d1"]
    assert ops[0].register == "d0"
    assert ops[1].register == "d1"


def test_semantic_operands_build_subx_predecrement_form() -> None:
    inst = disassemble(assemble_instruction("subx.b -(a0),-(a1)"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    left_metadata = _operand_nodes(inst)[0].metadata
    right_metadata = _operand_nodes(inst)[1].metadata
    assert isinstance(left_metadata, DecodedBaseRegisterNodeMetadata)
    assert left_metadata.base_register == "a0"
    assert isinstance(right_metadata, DecodedBaseRegisterNodeMetadata)
    assert right_metadata.base_register == "a1"

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["predecrement", "predecrement"]
    assert [op.text for op in ops] == ["-(a0)", "-(a1)"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_build_sbcd_predecrement_form() -> None:
    inst = disassemble(assemble_instruction("sbcd -(a0),-(a1)"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["predecrement", "predecrement"]
    assert [op.text for op in ops] == ["-(a0)", "-(a1)"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_build_abcd_predecrement_form() -> None:
    inst = disassemble(assemble_instruction("abcd -(a0),-(a1)"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["predecrement", "predecrement"]
    assert [op.text for op in ops] == ["-(a0)", "-(a1)"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_build_pack_register_form() -> None:
    inst = disassemble(bytes.fromhex("83400000"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1", "junk2")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "register", "immediate"]
    assert [op.text for op in ops] == ["d0", "d1", "#$0"]
    assert ops[0].register == "d0"
    assert ops[1].register == "d1"
    assert ops[2].value == 0


def test_semantic_operands_build_pack_predecrement_form() -> None:
    inst = disassemble(bytes.fromhex("83480000"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1", "junk2")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["predecrement", "predecrement", "immediate"]
    assert [op.text for op in ops] == ["-(a0)", "-(a1)", "#$0"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"
    assert ops[2].value == 0


def test_semantic_operands_prefer_typed_nodes_for_movep_load_form() -> None:
    inst = disassemble(assemble_instruction("movep.w 2(a0),d1"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["base_displacement", "register"]
    assert [op.text for op in ops] == ["2(a0)", "d1"]
    assert ops[0].base_register == "a0"
    assert ops[0].displacement == 2
    assert ops[1].register == "d1"


def test_semantic_operands_prefer_typed_nodes_for_movep_store_form() -> None:
    inst = disassemble(assemble_instruction("movep.w d1,2(a0)"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "base_displacement"]
    assert [op.text for op in ops] == ["d1", "2(a0)"]
    assert ops[0].register == "d1"
    assert ops[1].base_register == "a0"
    assert ops[1].displacement == 2


def test_semantic_operands_build_cmpm_postincrement_form() -> None:
    inst = disassemble(assemble_instruction("cmpm.b (a0)+,(a1)+"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["postincrement", "postincrement"]
    assert [op.text for op in ops] == ["(a0)+", "(a1)+"]
    assert ops[0].base_register == "a0"
    assert ops[1].base_register == "a1"


def test_semantic_operands_build_pdbcc_register_and_target_form() -> None:
    inst = disassemble(bytes.fromhex("f048000000004e71"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "branch_target"]
    assert [op.text for op in ops] == ["d0", "$2"]
    assert ops[0].register == "d0"
    assert ops[1].segment_addr == 2


def test_semantic_operands_build_pbcc_target_form() -> None:
    inst = disassemble(bytes.fromhex("f0800002"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["branch_target"]
    assert [op.text for op in ops] == ["$4"]
    assert ops[0].segment_addr == 4


def test_semantic_operands_build_ptrapcc_immediate_form() -> None:
    inst = disassemble(bytes.fromhex("f07a000000014e71"), max_cpu="68040")[0]
    inst.operand_texts = ("junk0",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["immediate"]
    assert [op.text for op in ops] == ["#1"]
    assert ops[0].value == 1


def test_semantic_operands_build_link_register_and_immediate_form() -> None:
    inst = disassemble(assemble_instruction("link a2,#-4"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "immediate"]
    assert [op.text for op in ops] == ["a2", "#-4"]
    assert ops[0].register == "a2"
    assert ops[1].value == 0xFFFFFFFC


def test_semantic_operands_build_link_long_register_and_immediate_form() -> None:
    inst = disassemble(bytes.fromhex("480afffffffc"), max_cpu="68020")[0]
    inst.operand_texts = ("junk0", "junk1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register", "immediate"]
    assert [op.text for op in ops] == ["a2", "#-4"]
    assert ops[0].register == "a2"
    assert ops[1].value == 0xFFFFFFFC


def test_semantic_operands_build_unlk_register_form() -> None:
    inst = disassemble(assemble_instruction("unlk a2"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register"]
    assert [op.text for op in ops] == ["a2"]
    assert ops[0].register == "a2"


def test_semantic_operands_build_swap_register_form() -> None:
    inst = disassemble(assemble_instruction("swap d3"), max_cpu="68010")[0]
    inst.operand_texts = ("junk0",)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["register"]
    assert [op.text for op in ops] == ["d3"]
    assert ops[0].register == "d3"


def test_semantic_operands_build_move_usp_register_forms() -> None:
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


def test_semantic_operands_build_move_usp_sp_alias_form() -> None:
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


def test_semantic_operands_prefer_typed_nodes_for_long_divmul_single_register() -> None:
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


def test_semantic_operands_prefer_typed_nodes_for_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("move.w 8(a1,d2.w),d0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    metadata = _operand_nodes(inst)[0].metadata
    assert isinstance(metadata, DecodedIndexedNodeMetadata)
    assert metadata.base_register == "a1"
    assert metadata.displacement == 8

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["indexed", "register"]
    assert [op.text for op in ops] == ["8(a1,d2.w)", "d0"]
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 8
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d2"
    assert ops[0].metadata.index_size == "w"


def test_semantic_operands_prefer_typed_nodes_for_pc_indexed_ea() -> None:
    inst = disassemble(assemble_instruction("lea 8(pc,d2.w),a0"), max_cpu="68010")[0]
    inst.operand_texts = ("garbage", "junk")

    metadata = _operand_nodes(inst)[0].metadata
    assert isinstance(metadata, DecodedIndexedNodeMetadata)
    assert metadata.base_register is None
    assert metadata.displacement == 8

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert [op.kind for op in ops] == ["pc_relative_indexed", "register"]
    assert [op.text for op in ops] == ["8(pc,d2.w)", "a0"]
    assert isinstance(ops[0].metadata, IndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d2"
    assert ops[0].metadata.index_size == "w"
    assert ops[1].register == "a0"


def test_build_instruction_semantic_operands_use_full_extension_nodes_not_text() -> None:
    inst = disassemble(bytes.fromhex("2031212200000004"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "d0")

    metadata = _operand_nodes(inst)[0].metadata
    assert isinstance(metadata, DecodedFullExtensionNodeMetadata)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert ops[0].kind == "memory_indirect_indexed"
    assert ops[0].text == "([0,a1,d2.w],4)"
    assert ops[0].base_register == "a1"
    assert ops[0].displacement == 0
    assert isinstance(ops[0].metadata, FullIndexedOperandMetadata)
    assert ops[0].metadata.base_register == "a1"
    assert ops[0].metadata.index_register == "d2"
    assert ops[0].metadata.index_size == "w"
    assert ops[0].metadata.index_scale == 1
    assert ops[0].metadata.memory_indirect is True
    assert ops[0].metadata.postindexed is False
    assert ops[0].metadata.preindexed is True
    assert ops[0].metadata.base_suppressed is False
    assert ops[0].metadata.index_suppressed is False
    assert ops[0].metadata.base_displacement == 0
    assert ops[0].metadata.outer_displacement == 4


def test_build_instruction_semantic_operands_use_postindexed_no_index_full_extension_nodes() -> None:
    inst = disassemble(bytes.fromhex("2235535f5e5e5e5f"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "d1")

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert ops[0].kind == "memory_indirect_indexed"
    assert ops[0].text == "([a5],1583242847)"
    assert ops[0].base_register == "a5"
    assert ops[0].displacement is None
    metadata = _operand_nodes(inst)[0].metadata
    assert isinstance(metadata, DecodedFullExtensionNodeMetadata)
    assert metadata.base_register == "a5"
    assert metadata.base_displacement is None
    assert metadata.index_register is None
    assert metadata.index_size is None
    assert metadata.index_scale is None
    assert metadata.memory_indirect is True
    assert metadata.preindexed is False
    assert metadata.postindexed is True
    assert metadata.outer_displacement == 1583242847
    assert metadata.base_suppressed is False
    assert metadata.index_suppressed is True


def test_assemble_instruction_parses_full_extension_memory_indirect_preindexed() -> None:
    raw = assemble_instruction("move.l ([0,a1,d2.w],4),d0")

    assert raw == bytes.fromhex("2031212200000004")


def test_assemble_instruction_parses_full_extension_memory_indirect_postindexed_no_index() -> None:
    raw = assemble_instruction("move.l ([a5],1583242847),d1")

    assert raw == bytes.fromhex("223501575e5e5e5f")


def test_build_instruction_semantic_operands_use_full_extension_indexed_nodes_not_text() -> None:
    inst = disassemble(bytes.fromhex("20746f204144"), max_cpu="68020")[0]
    inst.operand_texts = ("garbage", "a0")

    metadata = _operand_nodes(inst)[0].metadata
    assert isinstance(metadata, DecodedFullExtensionNodeMetadata)

    ops = build_instruction_semantic_operands(inst, _operand_session())

    assert ops[0].kind == "indexed"
    assert ops[0].text == "(16708,a4,d6.l*8)"
    assert ops[0].base_register == "a4"
    assert ops[0].displacement == 16708
    assert isinstance(ops[0].metadata, FullIndexedOperandMetadata)
    assert ops[0].metadata.index_register == "d6"
    assert ops[0].metadata.index_size == "l"
    assert metadata.base_displacement == 16708
    assert metadata.index_scale == 8


def test_resolve_operand_reads_full_extension_memory_indirect_indexed_ea() -> None:
    inst = disassemble(bytes.fromhex("2031212200000004"), max_cpu="68020")[0]
    decoded = _decode_ops(inst, inst.kb_mnemonic, inst.operand_size)

    cpu = CPUState()
    cpu.set_reg("an", 1, _concrete(0x100))
    cpu.set_reg("dn", 2, _concrete(4))

    mem = AbstractMemory()
    mem.write(0x104, _concrete(0x200), "l")
    mem.write(0x204, _concrete(0x12345678), "l")

    assert decoded.ea_op is not None
    value = _resolve_operand(decoded.ea_op, cpu, mem, "l", 4)

    assert value is not None
    assert value.is_known
    assert value.concrete == 0x12345678


def test_write_operand_writes_full_extension_memory_indirect_indexed_ea() -> None:
    inst = disassemble(bytes.fromhex("2031212200000004"), max_cpu="68020")[0]
    decoded = _decode_ops(inst, inst.kb_mnemonic, inst.operand_size)

    cpu = CPUState()
    cpu.set_reg("an", 1, _concrete(0x100))
    cpu.set_reg("dn", 2, _concrete(4))

    mem = AbstractMemory()
    mem.write(0x104, _concrete(0x200), "l")

    assert decoded.ea_op is not None
    _write_operand(decoded.ea_op, cpu, mem, _concrete(0x89ABCDEF), "l", 4)

    written = mem.read(0x204, "l")
    assert written.is_known
    assert written.concrete == 0x89ABCDEF


def test_resolve_ea_handles_full_extension_base_suppressed_indexed_form() -> None:
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


def test_instruction_operands_render_completely_for_valid_instruction() -> None:
    inst = disassemble(assemble_instruction("ori.b #$12,d0"), max_cpu="68010")[0]
    inst.kb_mnemonic = "ori"
    inst.operand_size = "b"

    assert instruction_operands_render_completely(inst, _operand_session())


def test_instruction_operands_render_completely_rejects_dropped_operand_text(
    monkeypatch: MonkeyPatch,
) -> None:
    inst = disassemble(assemble_instruction("ori.b #$12,d0"), max_cpu="68010")[0]
    inst.kb_mnemonic = "ori"
    inst.operand_size = "b"

    monkeypatch.setattr(
        operands_mod,
        "build_instruction_semantic_operands",
        lambda *args, **kwargs: (
            SemanticOperand(kind="immediate", text=""),
            SemanticOperand(kind="register", text="d0", register="d0"),
        ),
    )
    assert not instruction_operands_render_completely(inst, _operand_session())


