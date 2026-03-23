from __future__ import annotations
"""Build disassembly-time substitution maps."""

from collections.abc import Mapping, Sequence
from typing import Protocol

from m68k.instruction_kb import instruction_kb
from m68k.instruction_decode import decode_inst_destination, decode_inst_operands
from m68k.instruction_primitives import extract_branch_target
from m68k.m68k_disasm import Instruction
from m68k.os_calls import LibraryCall, OsKb
from m68k.registers import parse_reg_name
from m68k.subroutine_ranges import find_containing_sub
from disasm.types import EntityRecord


class _InstructionBlock(Protocol):
    @property
    def instructions(self) -> Sequence[Instruction]: ...



def _immediate_operand_token(inst: Instruction) -> str:
    if inst.operand_texts is None:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} is missing operand_texts")
    if not inst.operand_texts:
        raise ValueError(
            f"Instruction at ${inst.offset:06x} has no operand_texts")
    token = inst.operand_texts[0]
    if not token.startswith("#"):
        raise ValueError(
            f"Instruction at ${inst.offset:06x} first operand is not immediate: {token!r}")
    return str(token)


def _sorted_code_entities(hunk_entities: list[EntityRecord]) -> list[dict[str, int]]:
    return sorted(
        [{"addr": int(e["addr"], 16), "end": int(e["end"], 16)}
         for e in hunk_entities if e["type"] == "code"],
        key=lambda s: s["addr"])


def _call_instruction_index(
    *,
    blk: _InstructionBlock,
    call: LibraryCall,
    sorted_code_ents: list[dict[str, int]],
) -> int | None:
    if call.dispatch is not None:
        dispatch_sub = find_containing_sub(call.dispatch, sorted_code_ents)
        if dispatch_sub is None:
            return None
        for ci, inst in enumerate(blk.instructions):
            if extract_branch_target(inst, inst.offset) == dispatch_sub:
                return ci
        return None

    call_addr = call.addr
    for ci, inst in enumerate(blk.instructions):
        if inst.offset == call_addr:
            return ci
    return None


def build_lvo_substitutions(*, blocks: Mapping[int, _InstructionBlock], lib_calls: list[LibraryCall],
                            hunk_entities: list[EntityRecord]
                            ) -> tuple[dict[str, dict[int, str]], dict[int, tuple[str, str]]]:
    lvo_equs: dict[str, dict[int, str]] = {}
    lvo_substitutions: dict[int, tuple[str, str]] = {}
    sorted_code_ents = _sorted_code_entities(hunk_entities)

    for call in lib_calls:
        lib = call.library
        func = call.function
        lvo = call.lvo
        if not lib or not func or lvo is None or lib == "unknown":
            continue
        if func.startswith("LVO_"):
            continue
        sym = f"_LVO{func}"
        lvo_equs.setdefault(lib, {})[lvo] = sym
        if call.dispatch is not None:
            caller_blk = blocks.get(call.addr)
            if not caller_blk:
                continue
            call_idx = _call_instruction_index(
                blk=caller_blk,
                call=call,
                sorted_code_ents=sorted_code_ents,
            )
            if call_idx is None:
                continue
            for j in range(call_idx - 1, -1, -1):
                prev = caller_blk.instructions[j]
                prev_kb = instruction_kb(prev)
                prev_dec = decode_inst_operands(prev, prev_kb)
                if prev_dec.imm_val is None:
                    continue
                pv = prev_dec.imm_val
                pv_signed = pv - 0x100000000 if pv >= 0x80000000 else pv
                if pv_signed == lvo:
                    imm_token = _immediate_operand_token(prev)
                    lvo_substitutions[prev.offset] = (imm_token, f"#{sym}")
                    break
        else:
            lvo_substitutions[call.addr] = (f"{lvo}(", f"{sym}(")
    return lvo_equs, lvo_substitutions


def build_arg_substitutions(*, blocks: Mapping[int, _InstructionBlock], lib_calls: list[LibraryCall], hunk_entities: list[EntityRecord],
                            os_kb: OsKb) -> tuple[dict[str, int], dict[int, tuple[str, str]]]:
    arg_equs: dict[str, int] = {}
    arg_substitutions: dict[int, tuple[str, str]] = {}
    sorted_code_ents = _sorted_code_entities(hunk_entities)
    const_domains = os_kb.META.constant_domains
    all_consts = os_kb.CONSTANTS
    func_const_map: dict[str, dict[int, str]] = {}
    for func_name, const_names in const_domains.items():
        vmap: dict[int, str] = {}
        for cn in const_names:
            constant = all_consts.get(cn)
            cv = None if constant is None else constant.value
            if cv is not None:
                vmap[cv] = cn
        if vmap:
            func_const_map[func_name] = vmap
    for call in lib_calls:
        func_name = call.function
        if not func_name or func_name.startswith("LVO_"):
            continue
        vmap_opt = func_const_map.get(func_name)
        if not vmap_opt:
            continue
        vmap = vmap_opt
        lib = call.library
        library = os_kb.LIBRARIES.get(lib)
        if library is None:
            continue
        func = library.functions.get(func_name)
        if func is None:
            continue
        inputs = func.inputs
        if not inputs:
            continue
        blk_addr = call.block
        blk = blocks.get(blk_addr)
        if not blk:
            continue
        call_idx = _call_instruction_index(
            blk=blk,
            call=call,
            sorted_code_ents=sorted_code_ents,
        )
        if call_idx is None:
            continue
        for inp in inputs:
            reg = inp.reg.lower()
            reg_mode, reg_n = parse_reg_name(reg)
            for j in range(call_idx - 1, -1, -1):
                prev = blk.instructions[j]
                prev_kb = instruction_kb(prev)
                prev_dec = decode_inst_operands(prev, prev_kb)
                if prev_dec.imm_val is None:
                    continue
                dst = decode_inst_destination(prev, prev_kb)
                if dst is None:
                    continue
                dst_mode, dst_num = dst
                if dst_mode != reg_mode or dst_num != reg_n:
                    continue
                imm_val = prev_dec.imm_val
                const_name = vmap.get(imm_val)
                if const_name is None and imm_val >= 0x80000000:
                    const_name = vmap.get(imm_val - 0x100000000)
                if const_name:
                    equ_val = imm_val - 0x100000000 if imm_val >= 0x80000000 else imm_val
                    arg_equs[const_name] = equ_val
                    imm_token = _immediate_operand_token(prev)
                    arg_substitutions[prev.offset] = (imm_token, f"#{const_name}")
                break
    return arg_equs, arg_substitutions
