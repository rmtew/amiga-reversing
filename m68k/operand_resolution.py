"""Low-level M68K operand address resolution helpers."""

from .instruction_primitives import Operand
from .m68k_compute import _to_signed


def _concrete_from_state(state, value: int):
    cls = type(state.get_reg("dn", 0))
    return cls(concrete=value & 0xFFFFFFFF)


def _index_offset(operand: Operand, state) -> int | None:
    if operand.index_suppressed:
        return 0
    idx = state.get_reg("an" if operand.index_is_addr else "dn", operand.index_reg)
    if not idx.is_known:
        return None
    idx_val = idx.concrete
    if operand.index_size == "w":
        idx_val = _to_signed(idx_val & 0xFFFF, "w")
    return idx_val * operand.index_scale


def _full_extension_base_addr(operand: Operand, state) -> int | None:
    if operand.mode == "index":
        if operand.base_suppressed:
            return 0
        base = state.get_reg("an", operand.reg)
        if not base.is_known:
            return None
        return base.concrete
    if operand.mode == "pcindex":
        if operand.base_suppressed:
            return 0
        if operand.value is None:
            return None
        return operand.value - (operand.base_displacement or 0)
    return None


def _resolve_full_extension_ea(operand: Operand, state, mem) -> int | None:
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


def resolve_ea(operand: Operand, state, size: str, mem=None):
    """Resolve an EA operand to its effective address or value."""
    if operand.mode == "dn":
        return state.get_reg("dn", operand.reg)
    if operand.mode == "an":
        return state.get_reg("an", operand.reg)
    if operand.mode == "ind":
        return state.get_reg("an", operand.reg)
    if operand.mode in ("postinc", "predec"):
        return state.get_reg("an", operand.reg)
    if operand.mode == "disp":
        base = state.get_reg("an", operand.reg)
        if base.is_known:
            return _concrete_from_state(state, base.concrete + operand.value)
        return None
    if operand.mode == "index":
        if operand.full_extension:
            ea = _resolve_full_extension_ea(operand, state, mem)
            if ea is not None:
                return _concrete_from_state(state, ea)
            if operand.memory_indirect:
                return None
        base = state.get_reg("an", operand.reg)
        if operand.memory_indirect or operand.base_suppressed or operand.index_suppressed:
            return None
        idx = state.get_reg("an" if operand.index_is_addr else "dn", operand.index_reg)
        if base.is_known and idx.is_known:
            idx_val = idx.concrete
            if operand.index_size == "w":
                idx_val = _to_signed(idx_val & 0xFFFF, "w")
                idx_val &= 0xFFFFFFFF
            return _concrete_from_state(
                state, base.concrete + idx_val * operand.index_scale + operand.value
            )
        return None
    if operand.mode == "absw":
        return _concrete_from_state(state, operand.value)
    if operand.mode == "absl":
        return _concrete_from_state(state, operand.value)
    if operand.mode == "pcdisp":
        return _concrete_from_state(state, operand.value)
    if operand.mode == "pcindex":
        if operand.full_extension:
            ea = _resolve_full_extension_ea(operand, state, mem)
            if ea is not None:
                return _concrete_from_state(state, ea)
            if operand.memory_indirect:
                return None
        if operand.memory_indirect or operand.base_suppressed or operand.index_suppressed:
            return None
        idx = state.get_reg("an" if operand.index_is_addr else "dn", operand.index_reg)
        if idx.is_known:
            idx_val = idx.concrete
            if operand.index_size == "w":
                idx_val = _to_signed(idx_val & 0xFFFF, "w")
                idx_val &= 0xFFFFFFFF
            return _concrete_from_state(state, operand.value + idx_val * operand.index_scale)
        return None
    if operand.mode == "imm":
        return _concrete_from_state(state, operand.value)
    return None
