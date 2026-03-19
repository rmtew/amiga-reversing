"""Shared KB-driven indirect target analysis for M68K code."""

from .m68k_executor import BasicBlock, _extract_branch_target, propagate_states
from . import indirect_core
from .kb_util import KB
from . import subroutine_summary


_MAX_FORK_EXITS = 16


def resolve_indirect_targets(blocks: dict[int, BasicBlock],
                             exit_states: dict, code_size: int) -> list[dict]:
    """Resolve indirect JMP/JSR and RTS via propagated state."""
    kb = KB()
    resolved = []
    for addr in sorted(blocks):
        block = blocks[addr]
        if not block.instructions or addr not in exit_states:
            continue
        last = block.instructions[-1]
        ft, _ = kb.flow_type(last)

        if ft == "return":
            unres_type = "return"
        elif ft in ("call", "jump"):
            if _extract_branch_target(last, last.offset) is not None:
                continue
            unres_type = "jump"
        else:
            continue

        cpu, mem = exit_states[addr]
        target = indirect_core._try_resolve_block(
            addr, unres_type, blocks, cpu, mem, kb, code_size)
        if target is not None:
            resolved.append({"target": target})

    return resolved


def resolve_per_caller(blocks: dict[int, BasicBlock],
                       exit_states: dict, code: bytes,
                       code_size: int,
                       platform: dict | None = None) -> list[dict]:
    """Resolve indirect targets that require per-caller analysis."""
    kb = KB()
    unresolved = indirect_core._find_unresolved(blocks, exit_states, kb, code_size)
    if not unresolved:
        return []

    call_targets = set()
    for block in blocks.values():
        for xref in block.xrefs:
            if xref.type == "call":
                call_targets.add(xref.dst)

    sub_blocks_cache = {}
    block_owner = {}
    sub_info_cache = {}
    caller_ctx_cache = {}
    per_exit_cache = {}

    def _sub_blocks(entry):
        if entry not in sub_blocks_cache:
            sub_blocks_cache[entry] = subroutine_summary.find_sub_blocks(
                entry, blocks, call_targets)
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
                        and xref.dst in call_targets
                        and xref.dst != entry):
                    nested_callees.add(xref.dst)
        expanded = dict(sub_dict)
        for callee_entry in nested_callees:
            for na in _sub_blocks(callee_entry):
                if na in blocks and na not in expanded:
                    expanded[na] = blocks[na]
        pc_platform = dict(platform) if platform else {}
        pc_platform["scratch_regs"] = []
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

    def _caller_ctx(entry, caller_addr):
        key = (entry, caller_addr)
        if key in caller_ctx_cache:
            return caller_ctx_cache[key]
        caller_cpu, caller_mem = exit_states[caller_addr]
        info = _sub_info(entry)
        init_cpu = subroutine_summary.restore_base_reg(caller_cpu.copy(), platform)
        pass1_exits = propagate_states(
            info["expanded"], code, entry,
            initial_state=init_cpu,
            initial_mem=caller_mem.copy(),
            platform=info["pc_platform"])
        inline_sums = {}
        for callee_entry in info["nested_callees"]:
            isum = subroutine_summary._inline_summary(
                callee_entry, blocks, call_targets, pass1_exits, kb)
            if isum is not None:
                inline_sums[callee_entry] = isum
        ctx = {
            "init_cpu": init_cpu,
            "caller_mem": caller_mem,
            "pass1_exits": pass1_exits,
            "inline_sums": inline_sums,
        }
        caller_ctx_cache[key] = ctx
        return ctx

    def _per_exit_summaries(entry, caller_addr, callee_entry, pass1_exits):
        key = (entry, caller_addr, callee_entry)
        if key not in per_exit_cache:
            per_exit_cache[key] = subroutine_summary._inline_summaries_per_exit(
                callee_entry, blocks, call_targets, pass1_exits, kb)
        return per_exit_cache[key]

    resolved = []
    for unres_addr, unres_type in unresolved:
        sub_entry = block_owner.get(unres_addr)
        if sub_entry is None:
            for entry in call_targets:
                if unres_addr in _sub_blocks(entry):
                    sub_entry = entry
                    break
        if sub_entry is None:
            continue

        info = _sub_info(sub_entry)
        callers = info["callers"]
        if not callers:
            continue

        operand = None
        if unres_type == "jump":
            last = blocks[unres_addr].instructions[-1]
            operand, _ = indirect_core.decode_jump_ea(last, kb)
        needed_regs = indirect_core._needed_registers(operand, unres_type)

        sub_dict = info["sub_dict"]

        merged_cpu, merged_mem = exit_states.get(unres_addr, (None, None))
        unknown_regs = []
        if needed_regs and unres_type == "jump" and merged_cpu is not None:
            for mode, num in needed_regs:
                val = merged_cpu.get_reg(mode, num)
                if not val.is_known:
                    unknown_regs.append((mode, num))

        use_fast_path = (
            unknown_regs
            and merged_cpu is not None
            and unres_addr != sub_entry
            and all(not subroutine_summary._reg_modified_in_sub(
                sub_dict, sub_entry, unres_addr, mode, num, kb,
                platform_ref=platform)
                for mode, num in unknown_regs)
        )

        if use_fast_path:
            for caller_addr in callers:
                if caller_addr not in exit_states:
                    continue
                caller_cpu, _ = exit_states[caller_addr]
                test_cpu = merged_cpu.copy()
                for mode, num in unknown_regs:
                    test_cpu.set_reg(mode, num, caller_cpu.get_reg(mode, num))
                subroutine_summary.restore_base_reg(test_cpu, platform)

                target = indirect_core._try_resolve_block(
                    unres_addr, unres_type, blocks,
                    test_cpu, merged_mem, kb, code_size)
                if target is not None:
                    resolved.append({"target": target})
        else:
            for caller_addr in callers:
                if caller_addr not in exit_states:
                    continue
                ctx = _caller_ctx(sub_entry, caller_addr)
                init_cpu = ctx["init_cpu"]
                caller_mem = ctx["caller_mem"]
                pass1_exits = ctx["pass1_exits"]
                inline_sums = dict(ctx["inline_sums"])
                fork_callee = None
                fork_exits = []
                for callee_entry, isum in inline_sums.items():
                    if fork_callee is not None or not needed_regs:
                        continue
                    for mode, num in needed_regs:
                        pkey = "produced_a" if mode == "an" else "produced_d"
                        if num not in isum.get(pkey, {}):
                            per_exit = _per_exit_summaries(
                                sub_entry, caller_addr, callee_entry, pass1_exits)
                            if len(per_exit) > 1:
                                fork_callee = callee_entry
                                fork_exits = per_exit
                            break

                def _try_resolve_from(exits):
                    if unres_addr not in exits:
                        return
                    cpu, mem = exits[unres_addr]
                    target = indirect_core._try_resolve_block(
                        unres_addr, unres_type, blocks, cpu, mem, kb, code_size)
                    if target is not None:
                        resolved.append({"target": target})

                if fork_callee and fork_exits:
                    for exit_sum in fork_exits[:_MAX_FORK_EXITS]:
                        trial_sums = dict(inline_sums)
                        trial_sums[fork_callee] = exit_sum
                        _try_resolve_from(propagate_states(
                            sub_dict, code, sub_entry,
                            initial_state=init_cpu,
                            initial_mem=caller_mem.copy(),
                            platform=info["pc_platform"],
                            summaries=trial_sums))
                elif inline_sums:
                    _try_resolve_from(propagate_states(
                        sub_dict, code, sub_entry,
                        initial_state=init_cpu,
                        initial_mem=caller_mem.copy(),
                        platform=info["pc_platform"],
                        summaries=inline_sums))
                else:
                    _try_resolve_from(pass1_exits)

    return resolved


def resolve_backward_slice(blocks: dict[int, BasicBlock],
                           exit_states: dict, code: bytes,
                           code_size: int,
                           platform: dict | None = None,
                           max_depth: int = 8) -> list[dict]:
    """Resolve indirect targets by backward-slicing predecessor chains."""
    kb = KB()
    unresolved = indirect_core._find_unresolved(blocks, exit_states, kb, code_size)
    if not unresolved:
        return []

    resolved = []
    seen_targets = set()

    call_blocks = set()
    for addr, block in blocks.items():
        if block.instructions:
            ft, _ = kb.flow_type(block.instructions[-1])
            if ft == "call":
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
                    unres_addr, unres_type, blocks, p_cpu, p_mem, kb, code_size)
                if target is not None and target not in seen_targets:
                    resolved.append({"target": target})
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
