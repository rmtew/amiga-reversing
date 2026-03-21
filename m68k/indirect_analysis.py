"""Shared KB-driven indirect target analysis for M68K code."""

import copy
from dataclasses import dataclass

from m68k_kb import runtime_m68k_analysis

from .instruction_kb import instruction_flow, instruction_kb
from .instruction_decode import decode_inst_operands
from .instruction_decode import decode_inst_destination
from .instruction_primitives import extract_branch_target
from .m68k_executor import BasicBlock, CallSummary, propagate_states
from . import indirect_core
from . import subroutine_summary


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
    entry_states: tuple = ()


def _indirect_resolution(target: int,
                         source_addr: int,
                         kind: indirect_core.IndirectSiteStatus,
                         caller_addr: int | None = None,
                         entry_states: tuple = ()) -> IndirectResolution:
    return IndirectResolution(
        target=target,
        source_addr=source_addr,
        kind=kind,
        caller_addr=caller_addr,
        entry_states=entry_states,
    )


def _terminal_site_addr(blocks: dict[int, BasicBlock], block_addr: int) -> int:
    block = blocks[block_addr]
    if not block.instructions:
        raise KeyError(f"missing terminal instruction for block ${block_addr:06x}")
    return block.instructions[-1].offset


def _summary_signature(summary: CallSummary) -> tuple:
    return (
        tuple(sorted(summary.preserved_d)),
        tuple(sorted(summary.preserved_a)),
        summary.produced_d,
        summary.produced_d_tags,
        summary.produced_a,
        summary.produced_a_tags,
        summary.sp_delta,
    )


def _inline_summaries_signature(summaries: dict[int, CallSummary]) -> tuple:
    return tuple(
        sorted((callee_entry, _summary_signature(summary))
               for callee_entry, summary in summaries.items())
    )


def resolve_indirect_targets(blocks: dict[int, BasicBlock],
                             exit_states: dict, code_size: int) -> list[IndirectResolution]:
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


def collect_call_entry_states(blocks: dict[int, BasicBlock],
                              exit_states: dict,
                              code: bytes,
                              source_addr: int,
                              platform: dict | None = None,
                              seed_entry_states: dict[int, list[tuple]] | None = None,
                              trail: frozenset[int] = frozenset(),
                              ) -> list[tuple]:
    """Collect full CPU/memory states at an indirect call site per caller."""
    if source_addr not in blocks:
        raise KeyError(f"missing block for indirect source ${source_addr:06x}")
    if source_addr not in exit_states:
        return []
    if source_addr in trail:
        return []

    call_targets = set()
    for block in blocks.values():
        for xref in block.xrefs:
            if xref.type == "call":
                call_targets.add(xref.dst)
    owned_entries = set(call_targets)
    if seed_entry_states:
        owned_entries.update(seed_entry_states)

    sub_blocks_cache = {}
    block_owner = {}

    def _sub_blocks(entry):
        if entry not in sub_blocks_cache:
            sub_blocks_cache[entry] = subroutine_summary.find_sub_blocks(
                entry, blocks, owned_entries)
            for addr in sub_blocks_cache[entry]:
                block_owner.setdefault(addr, entry)
        return sub_blocks_cache[entry]

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
    inline_cache = {}
    states = []

    def _collect(init_cpu, init_mem):
        init_cpu = subroutine_summary.restore_base_reg(init_cpu.copy(), platform)
        pass1_exits = propagate_states(
            expanded if nested_callees else sub_dict,
            code, sub_entry,
            initial_state=init_cpu,
            initial_mem=init_mem.copy(),
            platform=pc_platform,
        )
        inline_sums = {}
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
        if source_addr in exits:
            states.append(exits[source_addr])

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
                    trail=next_trail)
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
    return states


def resolve_per_caller(blocks: dict[int, BasicBlock],
                       exit_states: dict, code: bytes,
                       code_size: int,
                       platform: dict | None = None,
                       seed_entry_states: dict[int, list[tuple]] | None = None) -> list[IndirectResolution]:
    """Resolve indirect targets that require per-caller analysis."""
    unresolved = indirect_core._find_unresolved(blocks, exit_states, code_size)
    if not unresolved:
        return []

    call_targets = set()
    for block in blocks.values():
        for xref in block.xrefs:
            if xref.type == "call":
                call_targets.add(xref.dst)
    owned_entries = set(call_targets)

    sub_blocks_cache = {}
    block_owner = {}
    sub_info_cache = {}
    caller_ctx_cache = {}
    per_exit_cache = {}
    resolved_exit_cache = {}
    caller_regs_cache = {}
    call_entry_state_cache = {}
    synthetic_entry_states = seed_entry_states if seed_entry_states is not None else {}
    owned_entries.update(synthetic_entry_states)

    def _sub_blocks(entry):
        if entry not in sub_blocks_cache:
            sub_blocks_cache[entry] = subroutine_summary.find_sub_blocks(
                entry, blocks, owned_entries)
            for addr in sub_blocks_cache[entry]:
                block_owner.setdefault(addr, entry)
        return sub_blocks_cache[entry]

    def _sub_info(entry):
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
        info = {
            "sub_blocks": sub_blocks,
            "sub_dict": sub_dict,
            "nested_callees": nested_callees,
            "expanded": expanded,
            "pc_platform": pc_platform,
            "callers": blocks[entry].predecessors if entry in blocks else [],
        }
        sub_info_cache[entry] = info
        return info

    def _build_caller_ctx(entry, info, init_cpu, caller_mem):
        init_cpu = subroutine_summary.restore_base_reg(init_cpu.copy(), platform)
        pass1_exits = propagate_states(
            info["expanded"] if info["nested_callees"] else info["sub_dict"],
            code, entry,
            initial_state=init_cpu,
            initial_mem=caller_mem.copy(),
            platform=info["pc_platform"],
        )
        inline_sums = {}
        if info["nested_callees"]:
            for callee_entry in info["nested_callees"]:
                isum = subroutine_summary._inline_summary(
                    callee_entry, blocks, call_targets, pass1_exits)
                if isum is not None:
                    inline_sums[callee_entry] = isum
        ctx = {
            "init_cpu": init_cpu,
            "caller_mem": caller_mem,
            "pass1_exits": pass1_exits,
            "inline_sums": inline_sums,
        }
        return ctx

    def _caller_ctx(entry, caller_addr):
        key = (entry, caller_addr)
        if key in caller_ctx_cache:
            return caller_ctx_cache[key]
        caller_cpu, caller_mem = exit_states[caller_addr]
        info = _sub_info(entry)
        ctx = _build_caller_ctx(entry, info, caller_cpu, caller_mem)
        caller_ctx_cache[key] = ctx
        return ctx

    def _caller_block_states(caller_addr):
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
        states = []
        for outer_caller in info["callers"]:
            if outer_caller not in exit_states:
                continue
            ctx = _caller_ctx(owner, outer_caller)
            states.extend(_states_from_ctx(info, owner, outer_caller, ctx, [], caller_addr))
        return states

    def _per_exit_summaries(entry, caller_addr, callee_entry, pass1_exits):
        key = (entry, caller_addr, callee_entry)
        if key not in per_exit_cache:
            per_exit_cache[key] = subroutine_summary._inline_summaries_per_exit(
                callee_entry, blocks, call_targets, pass1_exits)
        return per_exit_cache[key]

    def _propagated_with_summaries(info, sub_entry, caller_addr, init_cpu, caller_mem, summaries):
        key = (sub_entry, caller_addr, _inline_summaries_signature(summaries))
        if key not in resolved_exit_cache:
            resolved_exit_cache[key] = propagate_states(
                info["sub_dict"], code, sub_entry,
                initial_state=init_cpu,
                initial_mem=caller_mem.copy(),
                platform=info["pc_platform"],
                summaries=summaries)
        return resolved_exit_cache[key]

    def _states_from_ctx(info, sub_entry, caller_addr, ctx, needed_regs, target_addr):
        pass1_exits = ctx["pass1_exits"]
        inline_sums = dict(ctx["inline_sums"])
        fork_callee = None
        fork_exits = []
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

        states = []

        def _collect(exits):
            if target_addr in exits:
                states.append(exits[target_addr])

        if fork_callee and fork_exits:
            for exit_sum in fork_exits[:_MAX_FORK_EXITS]:
                trial_sums = dict(inline_sums)
                trial_sums[fork_callee] = exit_sum
                _collect(_propagated_with_summaries(
                    info, sub_entry, caller_addr,
                    ctx["init_cpu"], ctx["caller_mem"], trial_sums))
        elif inline_sums:
            _collect(_propagated_with_summaries(
                info, sub_entry, caller_addr,
                ctx["init_cpu"], ctx["caller_mem"], inline_sums))
        else:
            _collect(pass1_exits)
        return states

    def _regs_known(cpu, needed_regs):
        return all(cpu.get_reg(mode, num).is_known for mode, num in needed_regs)

    def _simple_register_copy(inst, ikb):
        if runtime_m68k_analysis.OPERATION_TYPES[ikb] != runtime_m68k_analysis.OperationType.MOVE:
            return None
        decoded = decode_inst_operands(inst, ikb)
        src = decoded.ea_op
        dst = decode_inst_destination(inst, ikb)
        if src is None or dst is None:
            return None
        if src.mode not in ("an", "dn") or dst[0] not in ("an", "dn"):
            return None
        src_mode = "an" if src.mode == "an" else "dn"
        return (src_mode, src.reg), dst

    def _needed_reg_sources_before_terminal_call(block, needed_regs):
        source_map = {reg: reg for reg in needed_regs}
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

    def _project_needed_regs(cpu, source_map):
        projected = cpu.copy()
        for needed, source in source_map.items():
            projected.set_reg(needed[0], needed[1], cpu.get_reg(source[0], source[1]))
        return projected

    def _direct_call_into_dispatch_preserves(sub_entry, dispatch_addr, reg):
        block = blocks.get(sub_entry)
        if block is None:
            return False
        for inst in block.instructions:
            ikb = instruction_kb(inst)
            dst = decode_inst_destination(inst, ikb)
            if dst == reg:
                return False
            if instruction_flow(inst)[0] == _FLOW_CALL:
                return extract_branch_target(inst, inst.offset) == dispatch_addr
        return False

    def _caller_register_states(caller_addr, needed_regs, trail=frozenset()):
        key = (caller_addr, tuple(needed_regs))
        if key in caller_regs_cache:
            return caller_regs_cache[key]
        if caller_addr not in exit_states:
            return []
        caller_cpu, _ = exit_states[caller_addr]
        states = [caller_cpu]
        if not needed_regs or _regs_known(caller_cpu, needed_regs):
            caller_regs_cache[key] = states
            return states

        owner = block_owner.get(caller_addr)
        block = blocks.get(caller_addr)
        source_map = None
        if block is not None and caller_addr == owner:
            source_map = _needed_reg_sources_before_terminal_call(block, needed_regs)
            if source_map is not None:
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
        if not owner_info["callers"]:
            caller_regs_cache[key] = states
            return states

        nested_states = []
        next_trail = set(trail)
        next_trail.add(owner)
        outer_needed = list(dict.fromkeys(source_map.values()))
        for outer_caller in owner_info["callers"]:
            for outer_cpu in _caller_register_states(outer_caller, outer_needed, frozenset(next_trail)):
                nested_states.append(_project_needed_regs(outer_cpu, source_map))
        if nested_states:
            states = nested_states
        caller_regs_cache[key] = states
        return states

    def _call_entry_states(source_addr):
        if source_addr not in call_entry_state_cache:
            call_entry_state_cache[source_addr] = collect_call_entry_states(
                blocks, exit_states, code, source_addr,
                platform=platform,
                seed_entry_states=synthetic_entry_states,
            )
        return call_entry_state_cache[source_addr]

    resolved = []
    for unres_addr, unres_type in unresolved:
        sub_entry = block_owner.get(unres_addr)
        if sub_entry is None:
            for entry in owned_entries:
                if unres_addr in _sub_blocks(entry):
                    sub_entry = entry
                    break
        if sub_entry is None:
            continue

        info = _sub_info(sub_entry)
        callers = info["callers"]
        entry_states = synthetic_entry_states.get(sub_entry, [])
        if not callers and not entry_states:
            continue

        operand = None
        if unres_type == _FLOW_JUMP:
            last = blocks[unres_addr].instructions[-1]
            operand, _ = indirect_core.decode_jump_ea(last)
        needed_regs = indirect_core._needed_registers(operand, unres_type)

        sub_dict = info["sub_dict"]

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
                        entry_states = ()
                        if source_ft == _FLOW_CALL:
                            target_states = _call_entry_states(unres_addr)
                            if not target_states:
                                target_states = [(test_cpu, merged_mem.copy())]
                            entry_states = tuple(
                                (cpu.copy(), mem.copy()) for cpu, mem in target_states)
                        resolved.append(_indirect_resolution(
                            target, _terminal_site_addr(blocks, unres_addr),
                            indirect_core.IndirectSiteStatus.PER_CALLER,
                            caller_addr=caller_addr,
                            entry_states=entry_states))
            for entry_cpu, entry_mem in entry_states:
                test_cpu = merged_cpu.copy()
                for mode, num in unknown_regs:
                    test_cpu.set_reg(mode, num, entry_cpu.get_reg(mode, num))
                subroutine_summary.restore_base_reg(test_cpu, platform)

                target = indirect_core._try_resolve_block(
                    unres_addr, unres_type, blocks, test_cpu, merged_mem or entry_mem, code_size)
                if target is not None:
                    resolved.append(_indirect_resolution(
                        target, _terminal_site_addr(blocks, unres_addr),
                        indirect_core.IndirectSiteStatus.PER_CALLER,
                        entry_states=(((entry_cpu.copy(), entry_mem.copy()),)
                                      if source_ft == _FLOW_CALL else ())))
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
                        resolved.append(_indirect_resolution(
                            target, _terminal_site_addr(blocks, unres_addr),
                            indirect_core.IndirectSiteStatus.PER_CALLER,
                            caller_addr=caller_addr,
                            entry_states=(((cpu.copy(), mem.copy()),)
                                          if source_ft == _FLOW_CALL else ())))
            for entry_cpu, entry_mem in entry_states:
                ctx = _build_caller_ctx(sub_entry, info, entry_cpu, entry_mem)
                for cpu, mem in _states_from_ctx(
                        info, sub_entry, sub_entry, ctx, needed_regs, unres_addr):
                    target = indirect_core._try_resolve_block(
                        unres_addr, unres_type, blocks, cpu, mem, code_size)
                    if target is not None:
                        resolved.append(_indirect_resolution(
                            target, _terminal_site_addr(blocks, unres_addr),
                            indirect_core.IndirectSiteStatus.PER_CALLER,
                            entry_states=(((cpu.copy(), mem.copy()),)
                                          if source_ft == _FLOW_CALL else ())))

    return resolved


def resolve_backward_slice(blocks: dict[int, BasicBlock],
                           exit_states: dict, code: bytes,
                           code_size: int,
                           platform: dict | None = None,
                           max_depth: int = 8) -> list[IndirectResolution]:
    """Resolve indirect targets by backward-slicing predecessor chains."""
    unresolved = indirect_core._find_unresolved(blocks, exit_states, code_size)
    if not unresolved:
        return []

    resolved = []
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
