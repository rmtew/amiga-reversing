"""Shared KB-driven indirect target analysis for M68K code."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter

from m68k_kb import runtime_m68k_analysis

from . import indirect_core, subroutine_summary
from .instruction_decode import decode_inst_destination, decode_inst_operands
from .instruction_kb import instruction_flow, instruction_kb
from .instruction_primitives import extract_branch_target
from .m68k_executor import (
    AbstractMemory,
    BasicBlock,
    CallSummary,
    CPUState,
    StatePair,
    propagate_states,
)
from .os_calls import PlatformState
from .per_caller_trace import (
    cpu_signature,
    get_per_caller_trace,
    register_projection,
    state_signature,
)
from .typing_protocols import InstructionLike

_MAX_FORK_EXITS = 16
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
_FLOW_RETURN = runtime_m68k_analysis.FlowType.RETURN


@dataclass(frozen=True, slots=True)
class IndirectResolution:
    target: int
    source_addr: int
    kind: indirect_core.IndirectSiteStatus
    caller_addr: int | None = None
    entry_states: EntryStates = ()

type EntryStateList = list[StatePair]
type EntryStates = tuple[StatePair, ...]
type ExitStates = Mapping[int, StatePair]
type StateCacheKey = tuple[int, frozenset[int]]
type CpuObjectSignature = tuple[tuple[int, ...], tuple[int, ...], int]
type InlineSummaryCacheKey = tuple[int, int, int]
type PerExitCacheKey = tuple[int, int, int]
type ResolvedExitCacheKey = tuple[int, int, tuple[object, ...]]
type CallerCtxCacheKey = tuple[int, int]
type CallerRegsCacheKey = tuple[int, tuple[tuple[str, int], ...]]
type CollectCacheKey = tuple[CpuObjectSignature, int]
type SubBlocksCache = dict[int, set[int]]
type BlockOwnerMap = dict[int, int]
type SeedEntryStates = dict[int, EntryStateList]
type SummaryDict = dict[int, CallSummary]


@dataclass(frozen=True, slots=True)
class SubroutineInfo:
    sub_blocks: set[int]
    sub_dict: dict[int, BasicBlock]
    nested_callees: set[int]
    expanded: dict[int, BasicBlock]
    pc_platform: PlatformState | None
    callers: list[int]


@dataclass(frozen=True, slots=True)
class CallerContext:
    init_cpu: CPUState
    caller_mem: AbstractMemory
    pass1_exits: ExitStates
    inline_sums: SummaryDict


def _indirect_resolution(target: int,
                         source_addr: int,
                         kind: indirect_core.IndirectSiteStatus,
                         caller_addr: int | None = None,
                         entry_states: EntryStates = ()) -> IndirectResolution:
    return IndirectResolution(
        target=target,
        source_addr=source_addr,
        kind=kind,
        caller_addr=caller_addr,
        entry_states=entry_states,
    )


def _terminal_site_addr(blocks: Mapping[int, BasicBlock], block_addr: int) -> int:
    block = blocks[block_addr]
    if not block.instructions:
        raise KeyError(f"missing terminal instruction for block ${block_addr:06x}")
    return int(block.instructions[-1].offset)


def _trace_needed_regs(
    cpu: CPUState,
    needed_regs: list[tuple[str, int]],
) -> dict[str, tuple[object, ...]]:
    if not needed_regs:
        return {}
    return dict(register_projection(cpu, needed_regs))


def _record_site_resolution(
    site_target_states: dict[int, list[StatePair]],
    site_target_state_keys: dict[int, set[tuple[object, ...]]],
    site_target_caller: dict[int, int | None],
    target: int,
    caller_addr: int | None,
    entry_state_list: EntryStateList | EntryStates = (),
) -> None:
    if target not in site_target_caller:
        site_target_caller[target] = caller_addr
    state_list = site_target_states.setdefault(target, [])
    seen_keys = site_target_state_keys.setdefault(target, set())
    for cpu, mem in entry_state_list:
        key = state_signature(cpu, mem)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        state_list.append((cpu.copy(), mem.copy()))


def _cpu_object_signature(cpu: CPUState) -> CpuObjectSignature:
    return (
        tuple(id(val) for val in cpu.d),
        tuple(id(val) for val in cpu.a),
        id(cpu.sp),
    )


def _summary_signature(summary: CallSummary) -> tuple[object, ...]:
    return (
        tuple(sorted(summary.preserved_d)),
        tuple(sorted(summary.preserved_a)),
        summary.produced_d,
        summary.produced_d_tags,
        summary.produced_a,
        summary.produced_a_tags,
        summary.sp_delta,
    )


def _inline_summaries_signature(summaries: dict[int, CallSummary]) -> tuple[object, ...]:
    return tuple(
        sorted((callee_entry, _summary_signature(summary))
               for callee_entry, summary in summaries.items())
    )


def _find_unresolved_sites(
    blocks: Mapping[int, BasicBlock],
    exit_states: ExitStates,
    code_size: int,
) -> list[tuple[int, runtime_m68k_analysis.FlowType]]:
    return indirect_core._find_unresolved(blocks, exit_states, code_size)


def resolve_indirect_targets(
    blocks: Mapping[int, BasicBlock],
    exit_states: ExitStates,
    code_size: int,
) -> list[IndirectResolution]:
    """Resolve indirect JMP/JSR and RTS via propagated state."""
    resolved = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions or addr not in exit_states:
            continue
        last = block.instructions[-1]
        ft, _ = instruction_flow(last)

        if ft == _FLOW_RETURN:
            unres_type = _FLOW_RETURN
        elif ft in (_FLOW_CALL, _FLOW_JUMP):
            if extract_branch_target(last, last.offset) is not None:
                continue
            unres_type = _FLOW_JUMP
        else:
            continue

        cpu, mem = exit_states[addr]
        target = indirect_core._try_resolve_block(
            addr, unres_type, blocks, cpu, mem, code_size)
        if target is not None:
            resolved.append(_indirect_resolution(
                target, _terminal_site_addr(blocks, addr),
                indirect_core.IndirectSiteStatus.RUNTIME))

    return resolved


def collect_call_entry_states(blocks: Mapping[int, BasicBlock],
                              exit_states: ExitStates,
                              code: bytes,
                              source_addr: int,
                              platform: PlatformState | None = None,
                              seed_entry_states: SeedEntryStates | None = None,
                              trail: frozenset[int] = frozenset(),
                              sub_blocks_cache: SubBlocksCache | None = None,
                              block_owner: BlockOwnerMap | None = None,
                              state_cache: dict[StateCacheKey, EntryStateList] | None = None,
                              owned_entries: set[int] | None = None,
                              ) -> EntryStateList:
    """Collect full CPU/memory states at an indirect call site per caller."""
    if source_addr not in blocks:
        raise KeyError(f"missing block for indirect source ${source_addr:06x}")
    if source_addr not in exit_states:
        return []
    if source_addr in trail:
        return []
    if state_cache is None:
        state_cache = {}
    trace = get_per_caller_trace()
    cache_key = (source_addr, trail)
    cached_states = state_cache.get(cache_key)
    if cached_states is not None:
        if trace is not None:
            trace.event(
                "collect_call_entry_states",
                source_addr=source_addr,
                trail=sorted(trail),
                cache_hit=True,
                state_count=len(cached_states),
            )
        return cached_states

    if owned_entries is None:
        call_targets = set()
        for block in blocks.values():
            for xref in block.xrefs:
                if xref.type == "call":
                    call_targets.add(xref.dst)
        owned_entries = set(call_targets)
        if seed_entry_states:
            owned_entries.update(seed_entry_states)
    else:
        call_targets = set(owned_entries)

    if sub_blocks_cache is None:
        sub_blocks_cache = {}
    if block_owner is None:
        block_owner = {}

    def _sub_blocks(entry: int) -> set[int]:
        return set(subroutine_summary.cached_sub_blocks(
            entry, blocks, owned_entries, sub_blocks_cache, block_owner))

    for entry in owned_entries:
        _sub_blocks(entry)
    sub_entry = block_owner.get(source_addr)
    if sub_entry is None:
        return []

    sub_blocks = _sub_blocks(sub_entry)
    sub_dict = {a: blocks[a] for a in sub_blocks if a in blocks}
    nested_callees = set()
    for addr in sub_blocks:
        blk = blocks.get(addr)
        if not blk:
            continue
        for xref in blk.xrefs:
            if (xref.type == "call"
                    and xref.dst in owned_entries
                    and xref.dst != sub_entry):
                nested_callees.add(xref.dst)
    expanded = dict(sub_dict)
    for callee_entry in nested_callees:
        for addr in _sub_blocks(callee_entry):
            if addr in blocks and addr not in expanded:
                expanded[addr] = blocks[addr]

    pc_platform = copy.copy(platform) if platform else None
    if pc_platform is not None:
        pc_platform.scratch_regs = ()
    callers = list(blocks[sub_entry].predecessors) if sub_entry in blocks else []
    inline_cache: dict[InlineSummaryCacheKey, CallSummary | None] = {}
    collect_cache: dict[CollectCacheKey, EntryStateList] = {}
    states: EntryStateList = []

    def _collect(init_cpu: CPUState, init_mem: AbstractMemory) -> None:
        collect_key = (_cpu_object_signature(init_cpu), id(init_mem))
        cached = collect_cache.get(collect_key)
        if cached is not None:
            states.extend(cached)
            return
        init_cpu = subroutine_summary.restore_base_reg(init_cpu.copy(), platform)
        pass1_exits = propagate_states(
            expanded if nested_callees else sub_dict,
            code, sub_entry,
            initial_state=init_cpu,
            initial_mem=init_mem.copy(),
            platform=pc_platform,
        )
        inline_sums: SummaryDict = {}
        if nested_callees:
            for callee_entry in nested_callees:
                key = (id(init_cpu), id(init_mem), callee_entry)
                if key not in inline_cache:
                    inline_cache[key] = subroutine_summary._inline_summary(
                        callee_entry, blocks, call_targets, pass1_exits)
                isum = inline_cache[key]
                if isum is not None:
                    inline_sums[callee_entry] = isum
        if inline_sums:
            exits = propagate_states(
                sub_dict, code, sub_entry,
                initial_state=init_cpu,
                initial_mem=init_mem.copy(),
                platform=pc_platform,
                summaries=inline_sums,
            )
        else:
            exits = pass1_exits
        collected: EntryStateList = []
        if source_addr in exits:
            collected.append(exits[source_addr])
        collect_cache[collect_key] = collected
        states.extend(collected)

    next_trail = frozenset(set(trail) | {source_addr})
    for caller_addr in callers:
        caller_block = blocks.get(caller_addr)
        if caller_block and caller_block.instructions:
            last = caller_block.instructions[-1]
            if (instruction_flow(last)[0] == _FLOW_CALL
                    and extract_branch_target(last, last.offset) == sub_entry):
                nested_states = collect_call_entry_states(
                    blocks, exit_states, code, caller_addr,
                    platform=platform,
                    seed_entry_states=seed_entry_states,
                    trail=next_trail,
                    sub_blocks_cache=sub_blocks_cache,
                    block_owner=block_owner,
                    state_cache=state_cache,
                    owned_entries=owned_entries)
                if nested_states:
                    for caller_cpu, caller_mem in nested_states:
                        _collect(caller_cpu, caller_mem)
                    continue
        if caller_addr not in exit_states:
            continue
        caller_cpu, caller_mem = exit_states[caller_addr]
        _collect(caller_cpu, caller_mem)
    for entry_cpu, entry_mem in (seed_entry_states or {}).get(sub_entry, []):
        _collect(entry_cpu, entry_mem)
    state_cache[cache_key] = states
    if trace is not None:
        trace.event(
            "collect_call_entry_states",
            source_addr=source_addr,
            sub_entry=sub_entry,
            trail=sorted(trail),
            cache_hit=False,
            caller_count=len(callers),
            seed_state_count=len((seed_entry_states or {}).get(sub_entry, [])),
            state_count=len(states),
            unique_state_signatures=len({repr(state_signature(cpu, mem)) for cpu, mem in states}),
        )
    return states


def resolve_per_caller(blocks: Mapping[int, BasicBlock],
                       exit_states: ExitStates, code: bytes,
                       code_size: int,
                       platform: PlatformState | None = None,
                       seed_entry_states: SeedEntryStates | None = None,
                       skip_site_addrs: frozenset[int] = frozenset()) -> list[IndirectResolution]:
    """Resolve indirect targets that require per-caller analysis."""
    unresolved = _find_unresolved_sites(blocks, exit_states, code_size)
    if not unresolved:
        return []
    trace = get_per_caller_trace()

    call_targets = set()
    for block in blocks.values():
        for xref in block.xrefs:
            if xref.type == "call":
                call_targets.add(xref.dst)
    owned_entries = set(call_targets)

    sub_blocks_cache: SubBlocksCache = {}
    block_owner: BlockOwnerMap = {}
    sub_info_cache: dict[int, SubroutineInfo] = {}
    caller_ctx_cache: dict[CallerCtxCacheKey, CallerContext] = {}
    per_exit_cache: dict[PerExitCacheKey, list[CallSummary]] = {}
    resolved_exit_cache: dict[ResolvedExitCacheKey, ExitStates] = {}
    caller_regs_cache: dict[CallerRegsCacheKey, list[CPUState]] = {}
    call_entry_state_cache: dict[int, EntryStateList] = {}
    collect_state_cache: dict[StateCacheKey, EntryStateList] = {}
    synthetic_entry_states = seed_entry_states if seed_entry_states is not None else {}
    owned_entries.update(synthetic_entry_states)

    def _sub_blocks(entry: int) -> set[int]:
        return set(subroutine_summary.cached_sub_blocks(
            entry, blocks, owned_entries, sub_blocks_cache, block_owner))

    def _sub_info(entry: int) -> SubroutineInfo:
        if entry in sub_info_cache:
            return sub_info_cache[entry]
        sub_blocks = _sub_blocks(entry)
        sub_dict = {a: blocks[a] for a in sub_blocks if a in blocks}
        nested_callees = set()
        for addr in sub_blocks:
            blk = blocks.get(addr)
            if not blk:
                continue
            for xref in blk.xrefs:
                if (xref.type == "call"
                        and xref.dst in owned_entries
                        and xref.dst != entry):
                    nested_callees.add(xref.dst)
        expanded = dict(sub_dict)
        for callee_entry in nested_callees:
            for na in _sub_blocks(callee_entry):
                if na in blocks and na not in expanded:
                    expanded[na] = blocks[na]
        pc_platform = copy.copy(platform) if platform else None
        if pc_platform is not None:
            pc_platform.scratch_regs = ()
        info = SubroutineInfo(
            sub_blocks=sub_blocks,
            sub_dict=sub_dict,
            nested_callees=nested_callees,
            expanded=expanded,
            pc_platform=pc_platform,
            callers=list(blocks[entry].predecessors) if entry in blocks else [],
        )
        sub_info_cache[entry] = info
        return info

    def _build_caller_ctx(entry: int,
                          info: SubroutineInfo,
                          init_cpu: CPUState,
                          caller_mem: AbstractMemory) -> CallerContext:
        started = perf_counter()
        init_cpu = subroutine_summary.restore_base_reg(init_cpu.copy(), platform)
        pass1_exits = propagate_states(
            info.expanded if info.nested_callees else info.sub_dict,
            code, entry,
            initial_state=init_cpu,
            initial_mem=caller_mem.copy(),
            platform=info.pc_platform,
        )
        inline_sums: SummaryDict = {}
        if info.nested_callees:
            for callee_entry in info.nested_callees:
                isum = subroutine_summary._inline_summary(
                    callee_entry, blocks, call_targets, pass1_exits)
                if isum is not None:
                    inline_sums[callee_entry] = isum
        if trace is not None:
            trace.event(
                "build_caller_ctx",
                entry=entry,
                nested_callee_count=len(info.nested_callees),
                pass1_exit_count=len(pass1_exits),
                inline_summary_count=len(inline_sums),
                elapsed_seconds=round(perf_counter() - started, 6),
                init_state_signature=repr(state_signature(init_cpu, caller_mem)),
            )
        return CallerContext(
            init_cpu=init_cpu,
            caller_mem=caller_mem,
            pass1_exits=pass1_exits,
            inline_sums=inline_sums,
        )

    def _caller_ctx(entry: int, caller_addr: int) -> CallerContext:
        key = (entry, caller_addr)
        if key in caller_ctx_cache:
            return caller_ctx_cache[key]
        caller_cpu, caller_mem = exit_states[caller_addr]
        info = _sub_info(entry)
        ctx = _build_caller_ctx(entry, info, caller_cpu, caller_mem)
        caller_ctx_cache[key] = ctx
        return ctx

    def _caller_block_states(caller_addr: int) -> EntryStateList:
        owner = block_owner.get(caller_addr)
        if owner is None:
            if caller_addr in exit_states:
                return [exit_states[caller_addr]]
            return []
        if caller_addr == owner:
            if caller_addr in exit_states:
                return [exit_states[caller_addr]]
            return []
        info = _sub_info(owner)
        states: EntryStateList = []
        for outer_caller in info.callers:
            if outer_caller not in exit_states:
                continue
            ctx = _caller_ctx(owner, outer_caller)
            states.extend(_states_from_ctx(info, owner, outer_caller, ctx, [], caller_addr))
        return states

    def _per_exit_summaries(entry: int,
                            caller_addr: int,
                            callee_entry: int,
                            pass1_exits: ExitStates) -> list[CallSummary]:
        key = (entry, caller_addr, callee_entry)
        if key not in per_exit_cache:
            per_exit_cache[key] = subroutine_summary._inline_summaries_per_exit(
                callee_entry, blocks, call_targets, pass1_exits)
        return per_exit_cache[key]

    def _propagated_with_summaries(info: SubroutineInfo,
                                   sub_entry: int,
                                   caller_addr: int,
                                   init_cpu: CPUState,
                                   caller_mem: AbstractMemory,
                                   summaries: SummaryDict) -> ExitStates:
        key = (sub_entry, caller_addr, _inline_summaries_signature(summaries))
        if key not in resolved_exit_cache:
            resolved_exit_cache[key] = propagate_states(
                info.sub_dict, code, sub_entry,
                initial_state=init_cpu,
                initial_mem=caller_mem.copy(),
                platform=info.pc_platform,
                summaries=summaries)
        return resolved_exit_cache[key]

    def _states_from_ctx(info: SubroutineInfo,
                         sub_entry: int,
                         caller_addr: int,
                         ctx: CallerContext,
                         needed_regs: list[tuple[str, int]],
                         segment_addr: int) -> EntryStateList:
        pass1_exits = ctx.pass1_exits
        inline_sums = dict(ctx.inline_sums)
        fork_callee = None
        fork_exits: list[CallSummary] = []
        for callee_entry, isum in inline_sums.items():
            if fork_callee is not None or not needed_regs:
                continue
            for mode, num in needed_regs:
                produced_regs = (
                    {reg_num for reg_num, _ in isum.produced_a}
                    if mode == "an"
                    else {reg_num for reg_num, _ in isum.produced_d}
                )
                if num not in produced_regs:
                    per_exit = _per_exit_summaries(
                        sub_entry, caller_addr, callee_entry, pass1_exits)
                    if len(per_exit) > 1:
                        fork_callee = callee_entry
                        fork_exits = per_exit
                    break

        states: EntryStateList = []

        def _collect(exits: ExitStates) -> None:
            if segment_addr in exits:
                states.append(exits[segment_addr])

        if fork_callee and fork_exits:
            for exit_sum in fork_exits[:_MAX_FORK_EXITS]:
                trial_sums = dict(inline_sums)
                trial_sums[fork_callee] = exit_sum
                _collect(_propagated_with_summaries(
                    info, sub_entry, caller_addr,
                    ctx.init_cpu, ctx.caller_mem, trial_sums))
        elif inline_sums:
            _collect(_propagated_with_summaries(
                info, sub_entry, caller_addr,
                ctx.init_cpu, ctx.caller_mem, inline_sums))
        else:
            _collect(pass1_exits)
        return states

    def _regs_known(cpu: CPUState, needed_regs: list[tuple[str, int]]) -> bool:
        return all(cpu.get_reg(mode, num).is_known for mode, num in needed_regs)

    def _simple_register_copy(inst: InstructionLike, ikb: str) -> tuple[tuple[str, int], tuple[str, int]] | None:
        if runtime_m68k_analysis.OPERATION_TYPES[ikb] != runtime_m68k_analysis.OperationType.MOVE:
            return None
        decoded = decode_inst_operands(inst, ikb)
        src = decoded.ea_op
        dst = decode_inst_destination(inst, ikb)
        if src is None or dst is None:
            return None
        if src.mode not in ("an", "dn") or src.reg is None or dst[0] not in ("an", "dn"):
            return None
        src_mode = "an" if src.mode == "an" else "dn"
        return (src_mode, src.reg), dst

    def _needed_reg_sources_before_terminal_call(block: BasicBlock,
                                                 needed_regs: list[tuple[str, int]]
                                                 ) -> dict[tuple[str, int], tuple[str, int]] | None | bool:
        source_map: dict[tuple[str, int], tuple[str, int]] = {reg: reg for reg in needed_regs}
        for inst in reversed(block.instructions[:-1]):
            ikb = instruction_kb(inst)
            ft, _ = instruction_flow(inst)
            if ft in (_FLOW_JUMP, _FLOW_RETURN, runtime_m68k_analysis.FlowType.BRANCH):
                continue
            if ft == _FLOW_CALL:
                call_target = extract_branch_target(inst, inst.offset)
                if call_target is None:
                    return False
                global_sums = platform.summary_cache if platform else None
                callee_sum = global_sums.get(call_target) if global_sums else None
                if callee_sum is None:
                    return None
                for mode, num in set(source_map.values()):
                    preserved_regs = (callee_sum.preserved_d
                                      if mode == "dn"
                                      else callee_sum.preserved_a)
                    if num not in preserved_regs:
                        return None
                continue
            reg_copy = _simple_register_copy(inst, ikb)
            dst = decode_inst_destination(inst, ikb)
            if dst and dst in source_map.values():
                if reg_copy is None or reg_copy[1] != dst:
                    return None
                src, _ = reg_copy
                for needed, source in list(source_map.items()):
                    if source == dst:
                        source_map[needed] = src
                continue
            if runtime_m68k_analysis.OPERATION_TYPES[ikb] == runtime_m68k_analysis.OperationType.SWAP:
                return None
            if (runtime_m68k_analysis.OPERATION_CLASSES[ikb]
                    == runtime_m68k_analysis.OperationClass.MULTI_REGISTER_TRANSFER):
                return None
        return source_map

    def _project_needed_regs(cpu: CPUState,
                             source_map: dict[tuple[str, int], tuple[str, int]]) -> CPUState:
        projected = cpu.copy()
        for needed, source in source_map.items():
            projected.set_reg(needed[0], needed[1], cpu.get_reg(source[0], source[1]))
        return projected

    def _direct_call_into_dispatch_preserves(sub_entry: int,
                                             dispatch_addr: int,
                                             reg: tuple[str, int]) -> bool:
        block = blocks.get(sub_entry)
        if block is None:
            return False
        for inst in block.instructions:
            ikb = instruction_kb(inst)
            dst = decode_inst_destination(inst, ikb)
            if dst == reg:
                return False
            if instruction_flow(inst)[0] == _FLOW_CALL:
                return bool(extract_branch_target(inst, inst.offset) == dispatch_addr)
        return False

    def _caller_register_states(caller_addr: int,
                                needed_regs: list[tuple[str, int]],
                                trail: frozenset[int] = frozenset()) -> list[CPUState]:
        key = (caller_addr, tuple(needed_regs))
        if key in caller_regs_cache:
            return caller_regs_cache[key]
        if caller_addr not in exit_states:
            return []
        caller_cpu, _ = exit_states[caller_addr]
        states: list[CPUState] = [caller_cpu]
        if not needed_regs or _regs_known(caller_cpu, needed_regs):
            caller_regs_cache[key] = states
            return states

        owner = block_owner.get(caller_addr)
        block = blocks.get(caller_addr)
        source_map: dict[tuple[str, int], tuple[str, int]] | None = None
        if block is not None and caller_addr == owner:
            source_map_result = _needed_reg_sources_before_terminal_call(block, needed_regs)
            if isinstance(source_map_result, dict):
                source_map = source_map_result
                projected = _project_needed_regs(caller_cpu, source_map)
                states = [projected]
                if _regs_known(projected, needed_regs):
                    caller_regs_cache[key] = states
                    return states
        if (owner is None
                or owner in trail
                or caller_addr != owner
                or block is None
                or source_map is None):
            caller_regs_cache[key] = states
            return states

        owner_info = _sub_info(owner)
        if not owner_info.callers:
            caller_regs_cache[key] = states
            return states

        nested_states: list[CPUState] = []
        next_trail = set(trail)
        next_trail.add(owner)
        outer_needed = list(dict.fromkeys(source_map.values()))
        for outer_caller in owner_info.callers:
            for outer_cpu in _caller_register_states(outer_caller, outer_needed, frozenset(next_trail)):
                nested_states.append(_project_needed_regs(outer_cpu, source_map))
        if nested_states:
            states = nested_states
        caller_regs_cache[key] = states
        return states

    def _call_entry_states(source_addr: int) -> EntryStateList:
        if source_addr not in call_entry_state_cache:
            call_entry_state_cache[source_addr] = collect_call_entry_states(
                blocks, exit_states, code, source_addr,
                platform=platform,
                seed_entry_states=synthetic_entry_states,
                sub_blocks_cache=sub_blocks_cache,
                block_owner=block_owner,
                state_cache=collect_state_cache,
                owned_entries=owned_entries,
            )
        return call_entry_state_cache[source_addr]

    resolved: list[IndirectResolution] = []
    for unres_addr, unres_type in unresolved:
        site_started = perf_counter()
        site_target_states: dict[int, list[StatePair]] = {}
        site_target_state_keys: dict[int, set[tuple[object, ...]]] = {}
        site_target_caller: dict[int, int | None] = {}

        if _terminal_site_addr(blocks, unres_addr) in skip_site_addrs:
            continue
        sub_entry = block_owner.get(unres_addr)
        if sub_entry is None:
            for entry in owned_entries:
                if unres_addr in _sub_blocks(entry):
                    sub_entry = entry
                    break
        if sub_entry is None:
            continue

        info = _sub_info(sub_entry)
        callers = info.callers
        entry_states: EntryStateList = synthetic_entry_states.get(sub_entry, [])
        operand = None
        if unres_type == _FLOW_JUMP:
            last = blocks[unres_addr].instructions[-1]
            operand, _ = indirect_core.decode_jump_ea(last)
        needed_regs = indirect_core._needed_registers(operand, unres_type)
        if trace is not None:
            trace.event(
                "site_start",
                source_addr=unres_addr,
                source_type=unres_type.name,
                sub_entry=sub_entry,
                caller_count=len(callers),
                seed_entry_count=len(entry_states),
                needed_regs=[f"{mode}{num}" for mode, num in needed_regs],
            )
        if not callers and not entry_states:
            continue

        sub_dict = info.sub_dict

        merged_cpu, merged_mem = exit_states.get(unres_addr, (None, None))
        unknown_regs = []
        if needed_regs and unres_type == _FLOW_JUMP and merged_cpu is not None:
            for mode, num in needed_regs:
                val = merged_cpu.get_reg(mode, num)
                if not val.is_known:
                    unknown_regs.append((mode, num))

        use_fast_path = (
            unknown_regs
            and merged_cpu is not None
            and merged_mem is not None
            and (unres_addr != sub_entry
                 or _needed_reg_sources_before_terminal_call(
                     blocks[unres_addr], unknown_regs) is not None)
            and all(
                (not subroutine_summary._reg_modified_in_sub(
                    sub_dict, sub_entry, unres_addr, mode, num,
                    platform_ref=platform))
                or _direct_call_into_dispatch_preserves(sub_entry, unres_addr, (mode, num))
                for mode, num in unknown_regs)
        )

        if use_fast_path:
            assert merged_cpu is not None
            assert merged_mem is not None
            source_ft = None
            last_inst = blocks[unres_addr].instructions[-1]
            if last_inst.kb_mnemonic:
                source_ft = instruction_flow(last_inst)[0]
            for caller_addr in callers:
                owner = block_owner.get(caller_addr)
                block_states = _caller_block_states(caller_addr) if (
                    owner is not None and caller_addr != owner) else []
                if block_states:
                    caller_states = [cpu for cpu, _ in block_states]
                else:
                    caller_states = _caller_register_states(caller_addr, unknown_regs)
                for caller_cpu in caller_states:
                    test_cpu = merged_cpu.copy()
                    for mode, num in unknown_regs:
                        test_cpu.set_reg(mode, num, caller_cpu.get_reg(mode, num))
                    subroutine_summary.restore_base_reg(test_cpu, platform)

                    target = indirect_core._try_resolve_block(
                        unres_addr, unres_type, blocks, test_cpu, merged_mem, code_size)
                    if target is not None:
                        target_states: EntryStateList = []
                        if source_ft == _FLOW_CALL:
                            target_states = _call_entry_states(unres_addr)
                            if not target_states:
                                target_states = [(test_cpu, merged_mem.copy())]
                        _record_site_resolution(
                            site_target_states,
                            site_target_state_keys,
                            site_target_caller,
                            target,
                            caller_addr,
                            target_states,
                        )
                        if trace is not None:
                            trace.event(
                                "site_resolution",
                                source_addr=unres_addr,
                                caller_addr=caller_addr,
                                path="fast",
                                target=target,
                                caller_state_signature=repr(cpu_signature(caller_cpu)),
                                needed_regs=_trace_needed_regs(test_cpu, needed_regs),
                            )
            for entry_cpu, entry_mem in entry_states:
                test_cpu = merged_cpu.copy()
                for mode, num in unknown_regs:
                    test_cpu.set_reg(mode, num, entry_cpu.get_reg(mode, num))
                subroutine_summary.restore_base_reg(test_cpu, platform)

                target = indirect_core._try_resolve_block(
                    unres_addr, unres_type, blocks, test_cpu, merged_mem or entry_mem, code_size)
                if target is not None:
                    _record_site_resolution(
                        site_target_states,
                        site_target_state_keys,
                        site_target_caller,
                        target,
                        None,
                        (((entry_cpu, entry_mem),) if source_ft == _FLOW_CALL else ()),
                    )
                    if trace is not None:
                        trace.event(
                            "site_resolution",
                            source_addr=unres_addr,
                            caller_addr=None,
                            path="fast-seed",
                            target=target,
                            caller_state_signature=repr(state_signature(entry_cpu, entry_mem)),
                            needed_regs=_trace_needed_regs(test_cpu, needed_regs),
                        )
        else:
            source_ft = None
            last_inst = blocks[unres_addr].instructions[-1]
            if last_inst.kb_mnemonic:
                source_ft = instruction_flow(last_inst)[0]
            for caller_addr in callers:
                if caller_addr not in exit_states:
                    continue
                ctx = _caller_ctx(sub_entry, caller_addr)
                for cpu, mem in _states_from_ctx(
                        info, sub_entry, caller_addr, ctx, needed_regs, unres_addr):
                    target = indirect_core._try_resolve_block(
                        unres_addr, unres_type, blocks, cpu, mem, code_size)
                    if target is not None:
                        _record_site_resolution(
                            site_target_states,
                            site_target_state_keys,
                            site_target_caller,
                            target,
                            caller_addr,
                            (((cpu, mem),) if source_ft == _FLOW_CALL else ()),
                        )
                        if trace is not None:
                            trace.event(
                                "site_resolution",
                                source_addr=unres_addr,
                                caller_addr=caller_addr,
                                path="full",
                                target=target,
                                caller_state_signature=repr(state_signature(cpu, mem)),
                                needed_regs=_trace_needed_regs(cpu, needed_regs),
                            )
            for entry_cpu, entry_mem in entry_states:
                ctx = _build_caller_ctx(sub_entry, info, entry_cpu, entry_mem)
                for cpu, mem in _states_from_ctx(
                        info, sub_entry, sub_entry, ctx, needed_regs, unres_addr):
                    target = indirect_core._try_resolve_block(
                        unres_addr, unres_type, blocks, cpu, mem, code_size)
                    if target is not None:
                        _record_site_resolution(
                            site_target_states,
                            site_target_state_keys,
                            site_target_caller,
                            target,
                            None,
                            (((cpu, mem),) if source_ft == _FLOW_CALL else ()),
                        )
                        if trace is not None:
                            trace.event(
                                "site_resolution",
                                source_addr=unres_addr,
                                caller_addr=None,
                                path="full-seed",
                                target=target,
                                caller_state_signature=repr(state_signature(cpu, mem)),
                                needed_regs=_trace_needed_regs(cpu, needed_regs),
                            )
        site_resolutions = [
            _indirect_resolution(
                target,
                _terminal_site_addr(blocks, unres_addr),
                indirect_core.IndirectSiteStatus.PER_CALLER,
                caller_addr=site_target_caller[target],
                entry_states=tuple(site_target_states.get(target, ())),
            )
            for target in sorted(site_target_states)
        ]
        resolved.extend(site_resolutions)
        if trace is not None:
            trace.event(
                "site_done",
                source_addr=unres_addr,
                elapsed_seconds=round(perf_counter() - site_started, 6),
                resolution_count=len(site_resolutions),
                unique_target_count=len({item.target for item in site_resolutions}),
                fast_path=use_fast_path,
            )

    return resolved


def resolve_backward_slice(blocks: Mapping[int, BasicBlock],
                           exit_states: ExitStates, code: bytes,
                           code_size: int,
                           platform: PlatformState | None = None,
                           max_depth: int = 8) -> list[IndirectResolution]:
    """Resolve indirect targets by backward-slicing predecessor chains."""
    unresolved = _find_unresolved_sites(blocks, exit_states, code_size)
    if not unresolved:
        return []

    resolved: list[IndirectResolution] = []
    seen_targets = set()

    call_blocks = set()
    for addr, block in blocks.items():
        if block.instructions:
            ft, _ = instruction_flow(block.instructions[-1])
            if ft == _FLOW_CALL:
                call_blocks.add(addr)

    for unres_addr, unres_type in unresolved:
        work = []
        for pred in blocks[unres_addr].predecessors:
            if pred in exit_states and pred not in call_blocks:
                work.append((pred, [pred, unres_addr]))

        visited = {unres_addr}
        for _ in range(max_depth):
            next_work = []
            for pred_addr, path in work:
                if pred_addr in visited:
                    continue
                visited.add(pred_addr)

                if pred_addr not in exit_states:
                    continue
                pred_cpu, pred_mem = exit_states[pred_addr]
                init_cpu = subroutine_summary.restore_base_reg(pred_cpu.copy(), platform)

                path_blocks = {a: blocks[a] for a in path if a in blocks}
                if not path_blocks or pred_addr not in path_blocks:
                    continue
                per_path_exits = propagate_states(
                    path_blocks, code, pred_addr,
                    initial_state=init_cpu,
                    initial_mem=pred_mem.copy(),
                    platform=platform)
                if unres_addr not in per_path_exits:
                    continue
                p_cpu, p_mem = per_path_exits[unres_addr]
                target = indirect_core._try_resolve_block(
                    unres_addr, unres_type, blocks, p_cpu, p_mem, code_size)
                if target is not None and target not in seen_targets:
                    resolved.append(_indirect_resolution(
                        target, _terminal_site_addr(blocks, unres_addr),
                        indirect_core.IndirectSiteStatus.BACKWARD_SLICE))
                    seen_targets.add(target)
                else:
                    if pred_addr in blocks:
                        for pp in blocks[pred_addr].predecessors:
                            if (pp not in visited and pp in exit_states
                                    and pp not in call_blocks):
                                next_work.append((pp, [pp] + path))
            work = next_work
            if not work:
                break

    return resolved
