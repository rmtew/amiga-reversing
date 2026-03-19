"""Shared KB-driven subroutine CFG and summary helpers."""

from .m68k_executor import _extract_branch_target, _join_states
from .kb_util import decode_destination


def find_sub_blocks(entry: int, blocks: dict, call_targets: set) -> set[int]:
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


def _reg_modified_in_sub(blocks: dict, sub_entry: int,
                         dispatch_addr: int,
                         reg_mode: str, reg_num: int,
                         kb,
                         platform_ref: dict | None = None) -> bool:
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

            ikb = kb.instruction_kb(inst)
            ft = ikb.get("pc_effects", {}).get("flow", {}).get("type")
            if ft in ("jump", "return", "branch"):
                continue
            if ft == "call":
                call_target = _extract_branch_target(inst, inst.offset)
                if call_target is not None:
                    global_sums = (platform_ref.get("_summary_cache")
                                   if platform_ref else None)
                    callee_sum = (global_sums.get(call_target)
                                  if global_sums else None)
                    if callee_sum is not None:
                        pkey = ("preserved_d" if reg_mode == "dn"
                                else "preserved_a")
                        if reg_num not in callee_sum.get(pkey, set()):
                            return True
                continue

            dst = decode_destination(inst.raw, ikb, kb.meta,
                                     inst.operand_size, inst.offset)
            if dst and dst == (reg_mode, reg_num):
                return True

            if ikb.get("operation_type") == "swap":
                return True

            if ikb.get("operation_class") == "multi_register_transfer":
                return True

        for succ in block.successors:
            if succ in blocks and succ != dispatch_addr:
                work.append(succ)

    return False


def _inline_summary(callee_entry: int, blocks: dict,
                    call_targets: set, exit_states: dict,
                    kb) -> dict | None:
    """Compute a joined concrete-exit summary for a callee."""
    owned = find_sub_blocks(callee_entry, blocks, call_targets)

    rts_states = []
    for addr in owned:
        blk = blocks.get(addr)
        if not blk or not blk.instructions:
            continue
        last = blk.instructions[-1]
        ft, _ = kb.flow_type(last)
        if ft == "return" and addr in exit_states:
            rts_states.append(exit_states[addr])

    if not rts_states:
        return None

    rts_cpu, _ = _join_states(rts_states)

    produced_d = {i: rts_cpu.d[i].concrete
                  for i in range(len(rts_cpu.d)) if rts_cpu.d[i].is_known}
    produced_a = {i: rts_cpu.a[i].concrete
                  for i in range(len(rts_cpu.a)) if rts_cpu.a[i].is_known}
    sp_delta = 0
    if rts_cpu.sp.is_symbolic and rts_cpu.sp.sym_base == "SP_entry":
        sp_delta = rts_cpu.sp.sym_offset

    return {
        "preserved_d": set(),
        "preserved_a": set(),
        "produced_d": produced_d,
        "produced_a": produced_a,
        "sp_delta": sp_delta,
    }


def _inline_summaries_per_exit(callee_entry: int, blocks: dict,
                               call_targets: set, exit_states: dict,
                               kb) -> list[dict]:
    """Compute one concrete summary per RTS exit for a callee."""
    owned = find_sub_blocks(callee_entry, blocks, call_targets)
    summaries = []

    for addr in owned:
        blk = blocks.get(addr)
        if not blk or not blk.instructions:
            continue
        ft, _ = kb.flow_type(blk.instructions[-1])
        if ft != "return" or addr not in exit_states:
            continue

        cpu, _ = exit_states[addr]
        produced_d = {i: cpu.d[i].concrete
                      for i in range(len(cpu.d)) if cpu.d[i].is_known}
        produced_a = {i: cpu.a[i].concrete
                      for i in range(len(cpu.a)) if cpu.a[i].is_known}
        sp_delta = 0
        if cpu.sp.is_symbolic and cpu.sp.sym_base == "SP_entry":
            sp_delta = cpu.sp.sym_offset

        summaries.append({
            "preserved_d": set(),
            "preserved_a": set(),
            "produced_d": produced_d,
            "produced_a": produced_a,
            "sp_delta": sp_delta,
        })

    return summaries


def restore_base_reg(cpu, platform: dict | None):
    """Restore configured base register if the current state lost it."""
    if platform:
        base_info = platform.get("initial_base_reg")
        if base_info:
            breg_num, breg_val = base_info
            if not cpu.a[breg_num].is_known:
                from .m68k_executor import _concrete
                cpu.set_reg("an", breg_num, _concrete(breg_val))
    return cpu
