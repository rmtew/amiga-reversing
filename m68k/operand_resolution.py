"""Low-level M68K operand address resolution helpers."""

from __future__ import annotations

from .abstract_values import AbstractValue, _concrete
from .instruction_primitives import Operand
from .m68k_compute import _to_signed
from .typing_protocols import CpuStateLike, MemoryLike


def _index_offset(operand: Operand, state: CpuStateLike) -> int | None:
    if operand.index_suppressed:
        return 0
    if operand.index_reg is None:
        assert operand.index_reg is not None, "Indexed operand missing index register"
    idx = state.get_reg("an" if operand.index_is_addr else "dn", operand.index_reg)
    if not idx.is_known:
        return None
    idx_val = idx.concrete
    if operand.index_size == "w":
        idx_val = int(_to_signed(idx_val & 0xFFFF, "w"))
    return int(idx_val * operand.index_scale)


def _full_extension_base_addr(operand: Operand, state: CpuStateLike) -> int | None:
    if operand.mode == "index":
        if operand.base_suppressed:
            return 0
        if operand.reg is None:
            assert operand.reg is not None, "Indexed operand missing base register"
        base = state.get_reg("an", operand.reg)
        if not base.is_known:
            return None
        return int(base.concrete)
    if operand.mode == "pcindex":
        if operand.base_suppressed:
            return 0
        if operand.value is None:
            return None
        return int(operand.value - (operand.base_displacement or 0))
    return None


def _resolve_full_extension_ea(operand: Operand, state: CpuStateLike, mem: MemoryLike | None) -> int | None:
    base_addr = _full_extension_base_addr(operand, state)
    if base_addr is None:
        return None
    index_offset = _index_offset(operand, state)
    if index_offset is None:
        return None
    base_disp = operand.base_displacement or 0

    if not operand.memory_indirect:
        return (base_addr + base_disp + index_offset) & 0xFFFFFFFF
    if mem is None:
        return None

    if operand.postindexed:
        pointer_addr = (base_addr + base_disp) & 0xFFFFFFFF
    else:
        pointer_addr = (base_addr + base_disp + index_offset) & 0xFFFFFFFF

    pointer = mem.read(pointer_addr, "l")
    if not pointer.is_known:
        return None

    final_addr = pointer.concrete + (operand.outer_displacement or 0)
    if operand.postindexed:
        final_addr += index_offset
    return final_addr & 0xFFFFFFFF


def resolve_ea(operand: Operand, state: CpuStateLike, size: str, mem: MemoryLike | None = None) -> AbstractValue | None:
    """Resolve an EA operand to its effective address or value."""
    if operand.mode == "dn":
        if operand.reg is None:
            assert operand.reg is not None, "Dn operand missing register"
        return state.get_reg("dn", operand.reg)
    if operand.mode == "an":
        if operand.reg is None:
            assert operand.reg is not None, "An operand missing register"
        return state.get_reg("an", operand.reg)
    if operand.mode == "ind":
        if operand.reg is None:
            assert operand.reg is not None, "Indirect operand missing register"
        return state.get_reg("an", operand.reg)
    if operand.mode in ("postinc", "predec"):
        if operand.reg is None:
            assert operand.reg is not None, "Auto-modify operand missing register"
        return state.get_reg("an", operand.reg)
    if operand.mode == "disp":
        if operand.reg is None or operand.value is None:
            assert operand.reg is not None and operand.value is not None, (
                "Displacement operand missing register or value")
        base = state.get_reg("an", operand.reg)
        if base.is_known:
            return _concrete(base.concrete + operand.value)
        return None
    if operand.mode == "index":
        if operand.full_extension:
            ea = _resolve_full_extension_ea(operand, state, mem)
            if ea is not None:
                return _concrete(ea)
            if operand.memory_indirect:
                return None
        if operand.reg is None:
            assert operand.reg is not None, "Indexed operand missing base register"
        if operand.index_reg is None or operand.value is None:
            assert operand.index_reg is not None and operand.value is not None, (
                "Indexed operand missing index register or displacement")
        base = state.get_reg("an", operand.reg)
        if operand.memory_indirect or operand.base_suppressed or operand.index_suppressed:
            return None
        idx = state.get_reg("an" if operand.index_is_addr else "dn", operand.index_reg)
        if base.is_known and idx.is_known:
            idx_val = idx.concrete
            if operand.index_size == "w":
                idx_val = _to_signed(idx_val & 0xFFFF, "w")
                idx_val &= 0xFFFFFFFF
            return _concrete(base.concrete + idx_val * operand.index_scale + operand.value)
        return None
    if operand.mode == "absw":
        if operand.value is None:
            assert operand.value is not None, "abs.w operand missing value"
        return _concrete(operand.value)
    if operand.mode == "absl":
        if operand.value is None:
            assert operand.value is not None, "abs.l operand missing value"
        return _concrete(operand.value)
    if operand.mode == "pcdisp":
        if operand.value is None:
            assert operand.value is not None, "pcdisp operand missing value"
        return _concrete(operand.value)
    if operand.mode == "pcindex":
        if operand.full_extension:
            ea = _resolve_full_extension_ea(operand, state, mem)
            if ea is not None:
                return _concrete(ea)
            if operand.memory_indirect:
                return None
        if operand.memory_indirect or operand.base_suppressed or operand.index_suppressed:
            return None
        if operand.index_reg is None or operand.value is None:
            assert operand.index_reg is not None and operand.value is not None, (
                "pcindex operand missing index register or value")
        idx = state.get_reg("an" if operand.index_is_addr else "dn", operand.index_reg)
        if idx.is_known:
            idx_val = idx.concrete
            if operand.index_size == "w":
                idx_val = _to_signed(idx_val & 0xFFFF, "w")
                idx_val &= 0xFFFFFFFF
            return _concrete(operand.value + idx_val * operand.index_scale)
        return None
    if operand.mode == "imm":
        if operand.value is None:
            assert operand.value is not None, "Immediate operand missing value"
        return _concrete(operand.value)
    return None
