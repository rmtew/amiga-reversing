from __future__ import annotations
"""Assemble analysis-derived hunk metadata for disassembly sessions."""

from collections import defaultdict

from disasm.discovery import (add_hint_labels, build_label_map,
                              build_reloc_map, discover_absolute_targets,
                              discover_pc_relative_targets,
                              filter_core_absolute_targets)


def build_hunk_metadata(*, code: bytes, code_size: int, hunk_index: int,
                        hunk_entities: list[dict], ha, hf_hunks: list,
                        fixed_abs_addrs: set[int]) -> dict:
    blocks = ha.blocks
    hint_blocks = ha.hint_blocks
    jt_list = ha.jump_tables

    code_addrs = {addr for blk in blocks.values() for addr in range(blk.start, blk.end)}
    hint_addrs = {addr for blk in hint_blocks.values() for addr in range(blk.start, blk.end)}

    reloc_map = build_reloc_map(hf_hunks, hunk_index)
    reloc_target_set = set(reloc_map.values())

    branch_targets = {
        succ
        for blk in blocks.values()
        for succ in blk.successors
        if succ != blk.end
    }
    core_entries = set(blocks.keys()) | ha.call_targets | ha.branch_targets
    for table in jt_list:
        core_entries.update(table["targets"])
    internal_targets = branch_targets | core_entries

    pc_targets = discover_pc_relative_targets(blocks, code)
    core_absolute_targets = discover_absolute_targets(blocks, code_size)
    core_absolute_targets = filter_core_absolute_targets(
        core_absolute_targets, code_addrs, fixed_abs_addrs)
    hint_pc = discover_pc_relative_targets(hint_blocks, code)
    for addr, name in hint_pc.items():
        if addr not in pc_targets:
            pc_targets[addr] = name
    string_addrs = {addr for addr, name in pc_targets.items() if name.startswith("str_")}

    jump_table_regions = {}
    jump_table_target_sources = defaultdict(list)
    for table in jt_list:
        table_addr = table["addr"]
        if table["pattern"] == "pc_inline_dispatch":
            dispatch_blk = blocks.get(table["dispatch_block"])
            if dispatch_blk is None:
                continue
            jump_table_regions[dispatch_blk.end] = {
                "pattern": "pc_inline_dispatch",
                "table_end": table["table_end"],
                "targets": table["targets"],
            }
        else:
            entries = table.get("entries")
            if entries is None:
                entries = [(table_addr + i * 2, tgt)
                           for i, tgt in enumerate(table["targets"])]
            else:
                entries = [(entry["offset_addr"], entry["target"])
                           for entry in entries]
            jump_table_regions[table_addr] = {
                "base_addr": table["base_addr"],
                "entries": entries,
                "pattern": table["pattern"],
                "table_end": table["table_end"],
            }

    labels = build_label_map(
        hunk_entities,
        {target: None for target in internal_targets},
        reloc_target_set,
        core_absolute_targets,
        pc_targets,
    )
    for table_addr, table in jump_table_regions.items():
        if table["pattern"] == "pc_inline_dispatch":
            for target in table["targets"]:
                if target not in labels:
                    labels[target] = f"loc_{target:04x}"
            continue
        if table_addr not in labels:
            labels[table_addr] = f"jt_{table_addr:04x}"
        base = table["base_addr"]
        if base is not None and base not in labels:
            labels[base] = f"loc_{base:04x}"
        for _entry_addr, target in table["entries"]:
            if target not in labels:
                labels[target] = f"loc_{target:04x}"

    for table_addr, table in jump_table_regions.items():
        if table["pattern"] == "pc_inline_dispatch":
            continue
        base = table["base_addr"]
        base_label = labels[base] if base is not None else None
        table["base_label"] = base_label
        source = base_label or labels[table_addr]
        for _entry_addr, target in table["entries"]:
            if source not in jump_table_target_sources[target]:
                jump_table_target_sources[target].append(source)

    add_hint_labels(labels, hint_blocks, code_addrs)

    return {
        "code_addrs": code_addrs,
        "hint_addrs": hint_addrs,
        "reloc_map": reloc_map,
        "reloc_target_set": reloc_target_set,
        "pc_targets": pc_targets,
        "string_addrs": string_addrs,
        "core_absolute_targets": core_absolute_targets,
        "jump_table_regions": jump_table_regions,
        "jump_table_target_sources": dict(jump_table_target_sources),
        "labels": labels,
    }
