from __future__ import annotations

import re

from m68k.kb_util import KB
from m68k.m68k_executor import _extract_mnemonic


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
            text = inst.text.lower()
            mnemonic = _extract_mnemonic(text)
            if not mnemonic:
                continue
            size_match = re.search(rf'{re.escape(mnemonic)}\.([bwl])', text)
            if not size_match:
                continue
            byte_size = size_map.get(size_match.group(1))
            if not byte_size:
                continue

            for index in range(num_addr_regs):
                reg_val = cpu.a[index]
                if not reg_val.is_known:
                    continue
                addr_val = reg_val.concrete
                pat = rf'\(a{index}\)\+?'
                if re.search(pat, text):
                    if addr_val not in sizes or byte_size > sizes[addr_val]:
                        sizes[addr_val] = byte_size

            for index in range(num_addr_regs):
                reg_val = cpu.a[index]
                if not reg_val.is_known:
                    continue
                match = re.search(rf'(-?\d+)\(a{index}\)', text)
                if match:
                    disp = int(match.group(1))
                    ea_addr = (reg_val.concrete + disp) & 0xFFFFFFFF
                    if ea_addr not in sizes or byte_size > sizes[ea_addr]:
                        sizes[ea_addr] = byte_size

    return sizes
