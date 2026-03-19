"""Shared KB-driven indirect target resolution helpers."""

import struct

from .m68k_executor import _extract_branch_target, resolve_ea
from .kb_util import decode_instruction_operands


def decode_jump_ea(last, kb):
    """Decode unresolved indirect JMP/JSR EA operand from typed KB data."""
    ikb = kb.instruction_kb(last)

    ft, _ = kb.flow_type(last)
    if ft not in ("call", "jump"):
        return None, None

    if _extract_branch_target(last, last.offset) is not None:
        return None, None

    if len(last.raw) < kb.opword_bytes:
        return None, None

    try:
        decoded = decode_instruction_operands(
            last.raw, ikb, kb.meta,
            kb.meta["default_operand_size"], last.offset)
    except (ValueError, struct.error):
        return None, None

    operand = decoded.get("ea_op")
    if operand is None:
        return None, None
    return operand, ikb


def _needed_registers(operand, unres_type: str) -> list[tuple[str, int]]:
    """Identify registers a typed indirect operand depends on."""
    if unres_type == "return" or operand is None:
        return []
    regs = []
    if operand.mode in ("ind", "disp", "index", "postinc", "predec"):
        regs.append(("an", operand.reg))
    if operand.mode in ("index", "pcindex") and not operand.index_suppressed:
        idx_mode = "an" if operand.index_is_addr else "dn"
        regs.append((idx_mode, operand.index_reg))
    return regs


def _is_runtime_indirect_operand(operand, kb) -> bool:
    """Return whether the typed operand still needs runtime resolution."""
    if operand is None:
        return False
    if operand.mode in kb.reg_indirect_modes:
        return True
    return operand.mode == "pcindex"


def _is_valid_target(addr: int, code_size: int, align_mask: int) -> bool:
    """Check if addr is a valid code target."""
    return 0 <= addr < code_size and not (addr & align_mask)


def _read_rts_target(cpu, mem, kb) -> int | None:
    """Read the return target from the post-RTS stack state."""
    if cpu.sp.is_known:
        pre_sp = (cpu.sp.concrete - kb.rts_sp_inc) & kb.addr_mask
    elif cpu.sp.is_symbolic:
        pre_sp = cpu.sp.sym_add(-kb.rts_sp_inc)
    else:
        return None
    ret_val = mem.read(pre_sp, kb.addr_size)
    if ret_val.is_known:
        return ret_val.concrete
    return None


def _find_unresolved(blocks: dict, exit_states: dict, kb,
                     code_size: int) -> list[tuple]:
    """Find blocks whose indirect jump/return target is still unresolved."""
    unresolved = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue
        last = block.instructions[-1]
        ft, _ = kb.flow_type(last)

        if ft == "return":
            if addr in exit_states:
                cpu, mem = exit_states[addr]
                target = _read_rts_target(cpu, mem, kb)
                if target is not None:
                    continue
            unresolved.append((addr, "return"))
            continue

        operand, _ = decode_jump_ea(last, kb)
        if operand is None:
            continue
        if not _is_runtime_indirect_operand(operand, kb):
            continue
        if addr in exit_states:
            cpu, mem = exit_states[addr]
            ea_val = resolve_ea(operand, cpu, kb.addr_size, mem)
            if ea_val is not None and ea_val.is_known:
                continue
        unresolved.append((addr, "jump"))

    return unresolved


def _try_resolve_block(unres_addr: int, unres_type: str,
                       blocks: dict, cpu, mem,
                       kb, code_size: int) -> int | None:
    """Try to resolve a single unresolved indirect block from a state."""
    if unres_type == "return":
        target = _read_rts_target(cpu, mem, kb)
        if target is not None and _is_valid_target(
                target, code_size, kb.align_mask):
            return target
        return None

    last = blocks[unres_addr].instructions[-1]
    operand, _ = decode_jump_ea(last, kb)
    if operand is None:
        return None
    ea_val = resolve_ea(operand, cpu, kb.addr_size, mem)
    if ea_val is not None and ea_val.is_known:
        if _is_valid_target(ea_val.concrete, code_size, kb.align_mask):
            return ea_val.concrete
    return None
