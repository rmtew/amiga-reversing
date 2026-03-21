"""Shared KB-driven indirect target resolution helpers."""

import struct
from dataclasses import dataclass
from enum import StrEnum

from m68k_kb import runtime_m68k_analysis
from m68k_kb import runtime_m68k_decode

from .instruction_kb import instruction_flow, instruction_kb
from .instruction_primitives import extract_branch_target
from .operand_resolution import resolve_ea
from .instruction_decode import decode_inst_operands

_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
_FLOW_RETURN = runtime_m68k_analysis.FlowType.RETURN


class IndirectSiteRegion(StrEnum):
    CORE = "core"
    HINT = "hint"


class IndirectSiteStatus(StrEnum):
    UNRESOLVED = "unresolved"
    RESOLVED_RUNTIME = "resolved_runtime"
    RUNTIME = "runtime"
    PER_CALLER = "per_caller"
    BACKWARD_SLICE = "backward_slice"
    JUMP_TABLE = "jump_table"
    EXTERNAL = "external"


@dataclass(slots=True)
class IndirectSite:
    addr: int
    mnemonic: str
    flow_type: runtime_m68k_analysis.FlowType
    shape: str
    status: IndirectSiteStatus
    target: int | None
    region: IndirectSiteRegion | None = None
    detail: str | None = None
    target_count: int | None = None


def decode_jump_ea(last):
    """Decode unresolved indirect JMP/JSR EA operand from typed KB data."""
    ikb = instruction_kb(last)

    ft, _ = instruction_flow(last)
    if ft not in (_FLOW_CALL, _FLOW_JUMP):
        return None, None

    if extract_branch_target(last, last.offset) is not None:
        return None, None

    if len(last.raw) < runtime_m68k_decode.OPWORD_BYTES:
        return None, None

    try:
        decoded = decode_inst_operands(last, ikb)
    except (ValueError, struct.error):
        return None, None

    operand = decoded.ea_op
    if operand is None:
        return None, None
    return operand, ikb


def _needed_registers(operand, unres_type: str) -> list[tuple[str, int]]:
    """Identify registers a typed indirect operand depends on."""
    if unres_type == _FLOW_RETURN or operand is None:
        return []
    regs = []
    if operand.mode in ("ind", "disp", "index", "postinc", "predec"):
        regs.append(("an", operand.reg))
    if operand.mode in ("index", "pcindex") and not operand.index_suppressed:
        idx_mode = "an" if operand.index_is_addr else "dn"
        regs.append((idx_mode, operand.index_reg))
    return regs


def _is_runtime_indirect_operand(operand) -> bool:
    """Return whether the typed operand still needs runtime resolution."""
    if operand is None:
        return False
    if operand.mode in runtime_m68k_decode.REG_INDIRECT_MODES:
        return True
    return operand.mode == "pcindex"


def indirect_operand_shape(operand) -> str:
    """Render a stable searchable shape tag for an indirect operand."""
    shape = operand.mode
    if operand.mode in ("index", "pcindex"):
        if operand.memory_indirect:
            shape += ".memind"
        elif operand.full_extension:
            shape += ".full"
        else:
            shape += ".brief"
    return shape


def _is_valid_target(addr: int, code_size: int, align_mask: int) -> bool:
    """Check if addr is a valid code target."""
    return 0 <= addr < code_size and not (addr & align_mask)


def _read_rts_target(cpu, mem) -> int | None:
    """Read the return target from the post-RTS stack state."""
    if cpu.sp.is_known:
        pre_sp = (cpu.sp.concrete - runtime_m68k_analysis.RTS_SP_INC) & runtime_m68k_analysis.ADDR_MASK
    elif cpu.sp.is_symbolic:
        pre_sp = cpu.sp.sym_add(-runtime_m68k_analysis.RTS_SP_INC)
    else:
        return None
    ret_val = mem.read(pre_sp, runtime_m68k_analysis.ADDR_SIZE)
    if ret_val.is_known:
        return ret_val.concrete
    return None


def _find_unresolved(blocks: dict, exit_states: dict, code_size: int) -> list[tuple]:
    """Find blocks whose indirect jump/return target is still unresolved."""
    unresolved = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions:
            continue
        last = block.instructions[-1]
        ft, _ = instruction_flow(last)

        if ft == _FLOW_RETURN:
            if addr in exit_states:
                cpu, mem = exit_states[addr]
                target = _read_rts_target(cpu, mem)
                if target is not None:
                    continue
            unresolved.append((addr, _FLOW_RETURN))
            continue

        operand, _ = decode_jump_ea(last)
        if operand is None:
            continue
        if not _is_runtime_indirect_operand(operand):
            continue
        if addr in exit_states:
            cpu, mem = exit_states[addr]
            ea_val = resolve_ea(operand, cpu, runtime_m68k_analysis.ADDR_SIZE, mem)
            if ea_val is not None and ea_val.is_known:
                continue
        unresolved.append((addr, _FLOW_JUMP))

    return unresolved


def _try_resolve_block(unres_addr: int, unres_type: str,
                       blocks: dict, cpu, mem,
                       code_size: int) -> int | None:
    """Try to resolve a single unresolved indirect block from a state."""
    if unres_type == _FLOW_RETURN:
        target = _read_rts_target(cpu, mem)
        if target is not None and _is_valid_target(
                target, code_size, runtime_m68k_decode.ALIGN_MASK):
            return target
        return None

    last = blocks[unres_addr].instructions[-1]
    operand, _ = decode_jump_ea(last)
    if operand is None:
        return None
    ea_val = resolve_ea(operand, cpu, runtime_m68k_analysis.ADDR_SIZE, mem)
    if ea_val is not None and ea_val.is_known:
        if _is_valid_target(ea_val.concrete, code_size, runtime_m68k_decode.ALIGN_MASK):
            return ea_val.concrete
    return None


def find_indirect_control_sites(blocks: dict, exit_states: dict,
                                code_size: int) -> list[IndirectSite]:
    """Enumerate non-direct JMP/JSR sites and their current runtime state."""
    sites = []
    for block_addr in sorted(blocks):
        block = blocks[block_addr]
        if not block.instructions:
            continue
        last = block.instructions[-1]
        ft, _ = instruction_flow(last)
        if ft not in (_FLOW_CALL, _FLOW_JUMP):
            continue
        if extract_branch_target(last, last.offset) is not None:
            continue
        operand, ikb = decode_jump_ea(last)
        if operand is None or not _is_runtime_indirect_operand(operand):
            continue
        site_addr = last.offset
        target = None
        if block_addr in exit_states:
            cpu, mem = exit_states[block_addr]
            target = _try_resolve_block(block_addr, ft, blocks, cpu, mem, code_size)
        sites.append(IndirectSite(
            addr=site_addr,
            mnemonic=ikb,
            flow_type=ft,
            shape=indirect_operand_shape(operand),
            status=(
                IndirectSiteStatus.RESOLVED_RUNTIME
                if target is not None
                else IndirectSiteStatus.UNRESOLVED
            ),
            target=target,
        ))
    return sites
