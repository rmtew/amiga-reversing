"""Shared KB-driven subroutine CFG and summary helpers."""

from __future__ import annotations

from collections.abc import Mapping

from m68k_kb import runtime_m68k_analysis
from .instruction_kb import instruction_flow, instruction_kb
from .instruction_primitives import extract_branch_target
from .m68k_executor import _join_states, CPUState, CallSummary, StatePair
from .instruction_decode import decode_inst_destination
from .os_calls import AppBaseInfo, PlatformState
from .typing_protocols import SuccessorBlockLike
from .abstract_values import _concrete


_FLOW_BRANCH = runtime_m68k_analysis.FlowType.BRANCH
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
_FLOW_RETURN = runtime_m68k_analysis.FlowType.RETURN


ExitStates = Mapping[int, StatePair]


def find_sub_blocks(entry: int, blocks: Mapping[int, SuccessorBlockLike],
                    call_targets: set[int]) -> set[int]:
    """Find all blocks owned by a subroutine starting at entry."""
    owned = set()
    work = [entry]
    while work:
        a = work.pop()
        if a in owned or a not in blocks:
            continue
        if a != entry and a in call_targets:
            continue
        owned.add(a)
        for succ in blocks[a].successors:
            work.append(succ)
    return owned


def cached_sub_blocks(entry: int,
                      blocks: Mapping[int, SuccessorBlockLike],
                      call_targets: set[int],
                      cache: dict[int, set[int]],
                      owner_map: dict[int, int] | None = None) -> set[int]:
    if entry not in cache:
        owned = find_sub_blocks(entry, blocks, call_targets)
        cache[entry] = owned
        if owner_map is not None:
            for addr in owned:
                owner_map.setdefault(addr, entry)
    return cache[entry]


def _reg_modified_in_sub(blocks: Mapping[int, SuccessorBlockLike], sub_entry: int,
                         dispatch_addr: int,
                         reg_mode: str, reg_num: int,
                         platform_ref: PlatformState | None = None) -> bool:
    """Check whether any path from sub entry to dispatch modifies a register."""
    visited = set()
    work = [sub_entry]

    while work:
        addr = work.pop()
        if addr in visited or addr not in blocks:
            continue
        visited.add(addr)
        block = blocks[addr]

        for inst in block.instructions:
            if inst.offset >= dispatch_addr:
                break

            ikb = instruction_kb(inst)
            ft, _ = instruction_flow(inst)
            if ft in (_FLOW_JUMP, _FLOW_RETURN, _FLOW_BRANCH):
                continue
            if ft == _FLOW_CALL:
                call_target = extract_branch_target(inst, inst.offset)
                if call_target is not None:
                    global_sums = (platform_ref.summary_cache
                                   if platform_ref else None)
                    callee_sum = (global_sums.get(call_target)
                                  if global_sums else None)
                    if callee_sum is not None:
                        preserved_regs = (callee_sum.preserved_d
                                          if reg_mode == "dn"
                                          else callee_sum.preserved_a)
                        if reg_num not in preserved_regs:
                            return True
                continue

            dst = decode_inst_destination(inst, ikb)
            if dst and dst == (reg_mode, reg_num):
                return True

            if runtime_m68k_analysis.OPERATION_TYPES.get(ikb) == runtime_m68k_analysis.OperationType.SWAP:
                return True

            if runtime_m68k_analysis.OPERATION_CLASSES.get(ikb) == runtime_m68k_analysis.OperationClass.MULTI_REGISTER_TRANSFER:
                return True

        for succ in block.successors:
            if succ in blocks and succ != dispatch_addr:
                work.append(succ)

    return False


def _inline_summary(callee_entry: int, blocks: Mapping[int, SuccessorBlockLike],
                    call_targets: set[int], exit_states: ExitStates) -> CallSummary | None:
    """Compute a joined concrete-exit summary for a callee."""
    owned = find_sub_blocks(callee_entry, blocks, call_targets)

    rts_states = []
    for addr in owned:
        blk = blocks.get(addr)
        if not blk or not blk.instructions:
            continue
        last = blk.instructions[-1]
        ft, _ = instruction_flow(last)
        if ft == _FLOW_RETURN and addr in exit_states:
            rts_states.append(exit_states[addr])

    if not rts_states:
        return None

    rts_cpu, _ = _join_states(rts_states)

    produced_d = tuple(
        (i, rts_cpu.d[i].concrete)
        for i in range(len(rts_cpu.d)) if rts_cpu.d[i].is_known
    )
    produced_d_tags = tuple(
        (i, rts_cpu.d[i].tag)
        for i in range(len(rts_cpu.d))
        if rts_cpu.d[i].tag is not None
    )
    produced_a = tuple(
        (i, rts_cpu.a[i].concrete)
        for i in range(len(rts_cpu.a)) if rts_cpu.a[i].is_known
    )
    produced_a_tags = tuple(
        (i, rts_cpu.a[i].tag)
        for i in range(len(rts_cpu.a))
        if rts_cpu.a[i].tag is not None
    )
    sp_delta = 0
    if rts_cpu.sp.is_symbolic and rts_cpu.sp.sym_base == "SP_entry":
        assert rts_cpu.sp.sym_offset is not None
        sp_delta = rts_cpu.sp.sym_offset

    return CallSummary(
        produced_d=produced_d,
        produced_d_tags=produced_d_tags,
        produced_a=produced_a,
        produced_a_tags=produced_a_tags,
        sp_delta=sp_delta,
    )


def _inline_summaries_per_exit(callee_entry: int, blocks: Mapping[int, SuccessorBlockLike],
                               call_targets: set[int], exit_states: ExitStates) -> list[CallSummary]:
    """Compute one concrete summary per RTS exit for a callee."""
    owned = find_sub_blocks(callee_entry, blocks, call_targets)
    summaries = []

    for addr in owned:
        blk = blocks.get(addr)
        if not blk or not blk.instructions:
            continue
        ft, _ = instruction_flow(blk.instructions[-1])
        if ft != _FLOW_RETURN or addr not in exit_states:
            continue

        cpu, _ = exit_states[addr]
        produced_d = tuple(
            (i, cpu.d[i].concrete)
            for i in range(len(cpu.d)) if cpu.d[i].is_known
        )
        produced_d_tags = tuple(
            (i, cpu.d[i].tag)
            for i in range(len(cpu.d))
            if cpu.d[i].tag is not None
        )
        produced_a = tuple(
            (i, cpu.a[i].concrete)
            for i in range(len(cpu.a)) if cpu.a[i].is_known
        )
        produced_a_tags = tuple(
            (i, cpu.a[i].tag)
            for i in range(len(cpu.a))
            if cpu.a[i].tag is not None
        )
        sp_delta = 0
        if cpu.sp.is_symbolic and cpu.sp.sym_base == "SP_entry":
            assert cpu.sp.sym_offset is not None
            sp_delta = cpu.sp.sym_offset

        summaries.append(CallSummary(
            produced_d=produced_d,
            produced_d_tags=produced_d_tags,
            produced_a=produced_a,
            produced_a_tags=produced_a_tags,
            sp_delta=sp_delta,
        ))

    return summaries


def restore_base_reg(cpu: CPUState, platform: PlatformState | None) -> CPUState:
    """Restore configured base register if the current state lost it."""
    if platform:
        base_info = platform.app_base
        if base_info:
            if not cpu.a[base_info.reg_num].is_known:
                cpu.set_reg("an", base_info.reg_num, _concrete(base_info.concrete))
    return cpu
