from __future__ import annotations

"""KB-driven include-based hardware symbol rendering and base-register analysis."""

from collections.abc import Mapping, Sequence
from typing import Protocol

from m68k.instruction_decode import (
    DecodedOperands,
    decode_inst_destination,
    decode_inst_operands,
)
from m68k.instruction_kb import instruction_kb
from m68k.instruction_primitives import Operand
from m68k.os_calls import PlatformState
from m68k.typing_protocols import InstructionLike
from m68k_kb import runtime_hardware, runtime_m68k_analysis
from m68k_kb.runtime_types import HardwareRegisterDef

_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL


class HardwareBlockLike(Protocol):
    @property
    def predecessors(self) -> Sequence[int]: ...

    @property
    def successors(self) -> Sequence[int]: ...

    @property
    def instructions(self) -> Sequence[InstructionLike]: ...


_REGISTER_DEFS: Mapping[int, HardwareRegisterDef] = runtime_hardware.REGISTER_DEFS
_FAMILY_BASES: dict[str, int] = {}
for addr, register in _REGISTER_DEFS.items():
    family = register["family"]
    offset = register["offset"]
    base_addr = addr - offset
    existing = _FAMILY_BASES.get(family)
    if existing is None:
        _FAMILY_BASES[family] = base_addr
    elif existing != base_addr:
        raise ValueError(
            f"Inconsistent hardware base for family {family!r}: "
            f"${existing:08X} vs ${base_addr:08X}"
        )


def hardware_register_by_addr(addr: int) -> HardwareRegisterDef | None:
    return _REGISTER_DEFS.get(addr)


def hardware_register_by_base_offset(base_addr: int, offset: int) -> HardwareRegisterDef | None:
    if offset < 0:
        return None
    return _REGISTER_DEFS.get(base_addr + offset)


def hardware_absolute_addr(base_addr: int, offset: int) -> int:
    return base_addr + offset


def render_hardware_absolute(addr: int) -> str:
    register_def = hardware_register_by_addr(addr)
    if register_def is None:
        raise ValueError(f"Missing hardware register metadata for ${addr:08X}")
    base_symbol = register_def.get("base_symbol")
    if not base_symbol:
        raise ValueError(f"Missing hardware base symbol for ${addr:08X}")
    return f"{base_symbol}+{register_def['symbol']}"


def render_hardware_relative(base_register: str, base_addr: int, offset: int) -> str:
    register_def = hardware_register_by_base_offset(base_addr, offset)
    if register_def is None:
        raise ValueError(
            f"Missing hardware register metadata for ${base_addr + offset:08X}"
        )
    return f"{register_def['symbol']}({base_register})"


def collect_hardware_base_regs(blocks: Mapping[int, HardwareBlockLike], code: bytes,
                               platform: PlatformState) -> dict[int, dict[str, int]]:
    block_in: dict[int, dict[str, int] | None] = dict.fromkeys(blocks)
    worklist = [addr for addr, block in blocks.items() if not block.predecessors]
    if not worklist:
        worklist = list(blocks)
    for addr in worklist:
        block_in[addr] = {}
    facts_by_inst: dict[int, dict[str, int]] = {}

    while worklist:
        block_addr = worklist.pop()
        block = blocks[block_addr]
        existing = block_in[block_addr]
        current = {} if existing is None else existing.copy()
        for inst in block.instructions:
            facts_by_inst[inst.offset] = dict(current)
            _apply_hardware_base_update(current, inst, code, platform)
        for succ in block.successors:
            if succ not in blocks:
                continue
            merged, changed = _merge_known_addr_regs(block_in[succ], current)
            if changed:
                block_in[succ] = merged
                worklist.append(succ)

    return facts_by_inst


def _merge_known_addr_regs(existing: dict[str, int] | None,
                           incoming: dict[str, int]) -> tuple[dict[str, int], bool]:
    if existing is None:
        return dict(incoming), True
    merged = {
        reg_name: concrete
        for reg_name, concrete in existing.items()
        if incoming.get(reg_name) == concrete
    }
    return merged, merged != existing


def _apply_hardware_base_update(current: dict[str, int], inst: InstructionLike, code: bytes,
                                platform: PlatformState) -> None:
    mnemonic = instruction_kb(inst)
    decoded = decode_inst_operands(inst, mnemonic)
    flow_type = runtime_m68k_analysis.FLOW_TYPES[mnemonic]
    if flow_type == _FLOW_CALL:
        for reg_mode, reg_num in platform.scratch_regs:
            if reg_mode == "an":
                current.pop(_address_reg_name(reg_num), None)
    dst = decode_inst_destination(inst, mnemonic)
    if dst is None or dst[0] != "an":
        return
    reg_name = _address_reg_name(dst[1])
    concrete = _resolve_written_address_reg(mnemonic, decoded, current)
    if concrete is None or concrete not in _FAMILY_BASES.values():
        current.pop(reg_name, None)
    else:
        current[reg_name] = concrete


def _resolve_written_address_reg(mnemonic: str, decoded: DecodedOperands,
                                current: dict[str, int]) -> int | None:
    src = decoded.ea_op
    if mnemonic in {"LEA", "MOVEA"}:
        return _resolve_effective_address(src, current)
    if mnemonic in {"ADDA", "SUBA"}:
        dst_name = _decoded_dest_address_reg(decoded)
        if dst_name is None or dst_name not in current or src is None:
            return None
        if src.mode != "imm":
            return None
        if src.value is None:
            return None
        delta = src.value if mnemonic == "ADDA" else -src.value
        return int((current[dst_name] + delta) & 0xFFFFFFFF)
    if mnemonic in {"ADDQ", "SUBQ"}:
        dst_name = _decoded_dest_address_reg(decoded)
        if dst_name is None or dst_name not in current or decoded.imm_val is None:
            return None
        delta = decoded.imm_val if mnemonic == "ADDQ" else -decoded.imm_val
        return int((current[dst_name] + delta) & 0xFFFFFFFF)
    return None


def _decoded_dest_address_reg(decoded: DecodedOperands) -> str | None:
    if decoded.dst_op is not None and decoded.dst_op.mode == "an":
        if decoded.dst_op.reg is None:
            return None
        return _address_reg_name(decoded.dst_op.reg)
    if decoded.reg_mode == "an" and decoded.reg_num is not None:
        return _address_reg_name(decoded.reg_num)
    return None


def _resolve_effective_address(op: Operand | None, current: dict[str, int]) -> int | None:
    if op is None:
        return None
    if op.mode == "absw":
        if op.value is None:
            return None
        return int(op.value & 0xFFFF)
    if op.mode == "absl":
        if op.value is None:
            return None
        return int(op.value & 0xFFFFFFFF)
    if op.mode == "imm":
        if op.value is None:
            return None
        return int(op.value & 0xFFFFFFFF)
    if op.mode == "an":
        if op.reg is None:
            return None
        return current.get(_address_reg_name(op.reg))
    if op.mode == "disp":
        if op.reg is None or op.value is None:
            return None
        base = current.get(_address_reg_name(op.reg))
        if base is None:
            return None
        return int((base + op.value) & 0xFFFFFFFF)
    if op.mode == "pcdisp":
        if op.value is None:
            return None
        return int(op.value & 0xFFFFFFFF)
    return None


def _address_reg_name(reg: int) -> str:
    return "sp" if reg == 7 else f"a{reg}"
