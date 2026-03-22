from __future__ import annotations
"""Assemble analysis-derived hunk metadata for disassembly sessions."""

from collections import defaultdict

from disasm.discovery import (add_hint_labels, build_label_map,
                              build_reloc_map, discover_absolute_targets,
                              discover_pc_relative_targets,
                              filter_internal_absolute_data_targets)
from disasm.types import HunkMetadata, JumpTableEntryRef, JumpTableRegion


def build_hunk_metadata(*, code: bytes, code_size: int, hunk_index: int,
                        hunk_entities: list[dict], ha, hf_hunks: list,
                        typed_string_ranges: dict[int, int] | None = None,
                        reserved_absolute_addrs: set[int] | None = None,
                        absolute_labels: dict[int, str] | None = None) -> HunkMetadata:
    typed_string_ranges = {} if typed_string_ranges is None else dict(typed_string_ranges)
    reserved_absolute_addrs = set() if reserved_absolute_addrs is None else reserved_absolute_addrs
    absolute_labels = {} if absolute_labels is None else absolute_labels
    blocks = ha.blocks
    code_addrs = {addr for blk in blocks.values() for addr in range(blk.start, blk.end)}
    string_covered_addrs = {
        addr
        for start, end in typed_string_ranges.items()
        for addr in range(start, end)
    }
    for start, end in typed_string_ranges.items():
        if any(addr in code_addrs for addr in range(start, end)):
            raise ValueError(f"Typed string range overlaps core code: ${start:08X}-${end:08X}")
    hint_blocks = {
        addr: block
        for addr, block in ha.hint_blocks.items()
        if not any(pos in string_covered_addrs for pos in range(block.start, block.end))
    }
    jt_list = ha.jump_tables

    hint_addrs = {
        addr
        for blk in hint_blocks.values()
        for addr in range(blk.start, blk.end)
        if addr not in string_covered_addrs
    }

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
        core_entries.update(table.targets)
    internal_targets = branch_targets | core_entries

    pc_targets = discover_pc_relative_targets(blocks, code)
    internal_absolute_data_targets = discover_absolute_targets(blocks, code_size)
    internal_absolute_data_targets = filter_internal_absolute_data_targets(
        internal_absolute_data_targets, code_addrs, reserved_absolute_addrs)
    hint_pc = discover_pc_relative_targets(hint_blocks, code)
    for addr, name in hint_pc.items():
        if addr not in pc_targets:
            pc_targets[addr] = name
    string_addrs = {addr for addr, name in pc_targets.items() if name.startswith("str_")}
    string_addrs.update(typed_string_ranges)
    generic_data_label_addrs = set(internal_absolute_data_targets)
    generic_data_label_addrs.update(pc_targets)

    jump_table_regions = {}
    jump_table_target_sources = defaultdict(list)
    for table in jt_list:
        table_addr = table.addr
        if table.pattern == "pc_inline_dispatch":
            dispatch_blk = blocks.get(table.dispatch_block)
            if dispatch_blk is None:
                continue
            jump_table_regions[dispatch_blk.end] = JumpTableRegion(
                pattern="pc_inline_dispatch",
                table_end=table.table_end,
                targets=table.targets,
            )
        else:
            entry_refs = (
                [JumpTableEntryRef(table_addr + i * 2, tgt)
                 for i, tgt in enumerate(table.targets)]
                if not table.entries else
                [JumpTableEntryRef(entry.offset_addr, entry.target) for entry in table.entries]
            )
            jump_table_regions[table_addr] = JumpTableRegion(
                pattern=table.pattern,
                table_end=table.table_end,
                entries=tuple(entry_refs),
                base_addr=table.base_addr,
            )

    labels = build_label_map(
        hunk_entities,
        {target: None for target in internal_targets},
        reloc_target_set,
        internal_absolute_data_targets,
        pc_targets,
    )
    for table_addr, table in jump_table_regions.items():
        if table.pattern == "pc_inline_dispatch":
            for target in table.targets:
                if target not in labels:
                    labels[target] = f"loc_{target:04x}"
            continue
        if table_addr not in labels:
            labels[table_addr] = f"jt_{table_addr:04x}"
        base = table.base_addr
        if base is not None and base not in labels:
            labels[base] = f"loc_{base:04x}"
        for entry in table.entries:
            if entry.target not in labels:
                labels[entry.target] = f"loc_{entry.target:04x}"

    for table_addr, table in jump_table_regions.items():
        if table.pattern == "pc_inline_dispatch":
            continue
        base = table.base_addr
        base_label = labels[base] if base is not None else None
        jump_table_regions[table_addr] = JumpTableRegion(
            pattern=table.pattern,
            table_end=table.table_end,
            entries=table.entries,
            targets=table.targets,
            base_addr=table.base_addr,
            base_label=base_label,
        )
        source = base_label or labels[table_addr]
        for entry in table.entries:
            if source not in jump_table_target_sources[entry.target]:
                jump_table_target_sources[entry.target].append(source)

    add_hint_labels(labels, hint_blocks, code_addrs)

    return HunkMetadata(
        code_addrs=code_addrs,
        hint_addrs=hint_addrs,
        hint_blocks=hint_blocks,
        reloc_map=reloc_map,
        reloc_target_set=reloc_target_set,
        reserved_absolute_addrs=reserved_absolute_addrs,
        pc_targets=pc_targets,
        string_addrs=string_addrs,
        string_ranges=typed_string_ranges,
        generic_data_label_addrs=generic_data_label_addrs,
        jump_table_regions=jump_table_regions,
        jump_table_target_sources={
            target: tuple(sources)
            for target, sources in jump_table_target_sources.items()
        },
        labels=labels,
        absolute_labels=absolute_labels,
    )
