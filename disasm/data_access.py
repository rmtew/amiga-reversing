from __future__ import annotations

from m68k_kb import runtime_m68k_decode

from m68k.instruction_decode import decode_inst_operands


def collect_data_access_sizes(blocks: dict, exit_states: dict) -> dict[int, int]:
    """Collect concrete data access sizes from analyzed code blocks."""
    sizes = {}
    size_map = runtime_m68k_decode.SIZE_BYTE_COUNT
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
            decoded = decode_inst_operands(inst)

            for op in (decoded.ea_op, decoded.dst_op):
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
