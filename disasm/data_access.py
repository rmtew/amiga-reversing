from __future__ import annotations

from m68k.kb_util import KB, decode_instruction_operands


def collect_data_access_sizes(blocks: dict, exit_states: dict) -> dict[int, int]:
    """Collect concrete data access sizes from analyzed code blocks."""
    kb = KB()
    sizes = {}
    size_map = kb.size_bytes
    num_addr_regs = len(exit_states[next(iter(exit_states))][0].a) if exit_states else 8

    for addr, block in blocks.items():
        if addr not in exit_states:
            continue
        cpu, _mem = exit_states[addr]

        for inst in block.instructions:
            if not inst.operand_size:
                continue
            byte_size = size_map.get(inst.operand_size)
            if not byte_size:
                continue
            inst_kb = kb.instruction_kb(inst)
            decoded = decode_instruction_operands(
                inst.raw, inst_kb, kb.meta, inst.operand_size, inst.offset)

            for op in (decoded.get("ea_op"), decoded.get("dst_op")):
                if op is None or op.reg is None:
                    continue
                if op.mode not in {"ind", "postinc", "disp"}:
                    continue
                if op.reg >= num_addr_regs:
                    raise ValueError(
                        f"Address register index {op.reg} out of range for ${inst.offset:06x}")
                reg_val = cpu.a[op.reg]
                if not reg_val.is_known:
                    continue
                addr_val = reg_val.concrete
                if op.mode == "disp":
                    addr_val = (addr_val + op.value) & 0xFFFFFFFF
                if addr_val not in sizes or byte_size > sizes[addr_val]:
                    sizes[addr_val] = byte_size

    return sizes
