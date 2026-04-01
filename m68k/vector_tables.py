from __future__ import annotations

from collections.abc import Mapping

from .instruction_decode import decode_inst_operands
from .instruction_kb import instruction_kb
from .m68k_disasm import Instruction
from .m68k_executor import AbstractMemory, StatePair
from .typing_protocols import BasicBlockLike

VECTOR_TABLE_LIMIT = 0x400
_OPERAND_SIZE_BYTES = {"b": 1, "w": 2, "l": 4}


def is_vector_table_slot(addr: int) -> bool:
    return 0 <= addr < VECTOR_TABLE_LIMIT and (addr % 4) == 0


def immediate_absolute_store(inst: Instruction) -> tuple[int, int] | None:
    mnemonic = instruction_kb(inst)
    if mnemonic not in {"MOVE", "MOVEA"}:
        return None
    decoded = decode_inst_operands(inst, mnemonic)
    source = decoded.ea_op
    dest = decoded.dst_op
    if source is None or dest is None or source.mode != "imm":
        return None
    if dest.mode not in {"absw", "absl"} or source.value is None or dest.value is None:
        return None
    dest_value = int(dest.value & 0xFFFF if dest.mode == "absw" else dest.value)
    return int(source.value), dest_value


def immediate_vector_table_store(inst: Instruction) -> tuple[int, int] | None:
    write = immediate_absolute_store(inst)
    if write is None or inst.operand_size != "l":
        return None
    value, vector_slot = write
    if not is_vector_table_slot(vector_slot):
        return None
    return value, vector_slot


def copy_loop_info(inst: Instruction) -> tuple[int, int, int] | None:
    mnemonic = instruction_kb(inst)
    decoded = decode_inst_operands(inst, mnemonic)
    src = decoded.ea_op
    dst = decoded.dst_op
    if src is None or dst is None or src.mode != "postinc" or dst.mode != "postinc":
        return None
    if src.reg is None or dst.reg is None or inst.operand_size not in _OPERAND_SIZE_BYTES:
        return None
    return src.reg, dst.reg, _OPERAND_SIZE_BYTES[inst.operand_size]


def trap_number(inst: Instruction) -> int | None:
    if instruction_kb(inst) != "TRAP" or len(inst.raw) < 2:
        return None
    return int.from_bytes(inst.raw[:2], "big") & 0xF


def _concrete_long_at(mem: AbstractMemory, addr: int) -> int | None:
    bytes_out: list[int] = []
    for i in range(4):
        byte = mem._bytes.get(addr + i)
        if byte is None or not byte.is_known:
            return None
        bytes_out.append(byte.concrete & 0xFF)
    return int.from_bytes(bytes(bytes_out), "big")


def collect_installed_vector_targets(
    exit_states: Mapping[int, StatePair],
    *,
    code_start: int,
    code_end: int,
) -> set[int]:
    targets: set[int] = set()
    for _addr, (_cpu, mem) in exit_states.items():
        slots = {
            byte_addr & ~0x3
            for byte_addr in mem._bytes
            if 0 <= byte_addr < VECTOR_TABLE_LIMIT
        }
        for slot in slots:
            if not is_vector_table_slot(slot):
                continue
            target = _concrete_long_at(mem, slot)
            if target is None:
                continue
            if code_start <= target < code_end:
                targets.add(target)
    return targets


def simple_register_value_before(
    *,
    blocks: Mapping[int, BasicBlockLike],
    before_addr: int,
    register_kind: str,
    register_num: int,
) -> int | None:
    for block_addr in sorted((addr for addr in blocks if addr < before_addr), reverse=True):
        block = blocks[block_addr]
        for inst in reversed(block.instructions):
            mnemonic = instruction_kb(inst)
            decoded = decode_inst_operands(inst, mnemonic)
            if register_kind == "an":
                opcode = int.from_bytes(inst.raw[:2], "big") if len(inst.raw) >= 2 else 0
                if mnemonic == "LEA" and ((opcode >> 9) & 0x7) == register_num:
                    source = decoded.ea_op
                    if source is not None and source.value is not None:
                        return int(source.value)
                dst = decoded.dst_op
                if mnemonic == "MOVEA" and dst is not None and dst.mode == "an" and dst.reg == register_num:
                    source = decoded.ea_op
                    if source is not None and source.mode == "imm" and source.value is not None:
                        return int(source.value)
            elif register_kind == "dn":
                dst = decoded.dst_op
                if dst is not None and dst.mode in {"dn", "dreg"} and dst.reg == register_num:
                    source = decoded.ea_op
                    if source is not None and source.mode == "imm" and source.value is not None:
                        return int(source.value)
                if mnemonic == "MOVEQ" and len(inst.raw) >= 2:
                    opcode = int.from_bytes(inst.raw[:2], "big")
                    if ((opcode >> 9) & 0x7) == register_num:
                        immediate = opcode & 0xFF
                        if immediate & 0x80:
                            immediate -= 0x100
                        return immediate
    return None


def collect_postincrement_vector_fill_targets(
    blocks: Mapping[int, BasicBlockLike],
    *,
    code_start: int,
    code_end: int,
) -> set[int]:
    targets: set[int] = set()
    for block_addr in sorted(blocks):
        block = blocks[block_addr]
        for inst in block.instructions:
            if instruction_kb(inst) != "MOVE" or inst.operand_size != "l":
                continue
            decoded = decode_inst_operands(inst, "MOVE")
            source = decoded.ea_op
            dest = decoded.dst_op
            if source is None or dest is None:
                continue
            if source.mode not in {"dn", "dreg"} or dest.mode != "postinc":
                continue
            if source.reg is None or dest.reg is None:
                continue
            dest_start = simple_register_value_before(
                blocks=blocks,
                before_addr=inst.offset,
                register_kind="an",
                register_num=dest.reg,
            )
            if dest_start is None or not is_vector_table_slot(dest_start):
                continue
            target = simple_register_value_before(
                blocks=blocks,
                before_addr=inst.offset,
                register_kind="dn",
                register_num=source.reg,
            )
            if target is None or not (code_start <= target < code_end):
                continue
            targets.add(target)
    return targets
