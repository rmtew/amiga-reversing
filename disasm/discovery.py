from __future__ import annotations

import struct
from collections.abc import Iterable, Mapping

from disasm.decode import decode_inst_for_emit
from disasm.types import DisasmBlockLike, EntityRecord
from m68k.hunk_parser import Hunk, HunkType
from m68k.strings import read_string_at


def discover_pc_relative_targets(blocks: Mapping[int, DisasmBlockLike], code: bytes) -> dict[int, str]:
    """Discover PC-relative operand targets in flow-verified blocks."""
    pc_targets, _ = discover_operand_targets(blocks, code)
    return pc_targets


def discover_operand_targets(blocks: Mapping[int, DisasmBlockLike],
                             code: bytes | None) -> tuple[dict[int, str], set[int]]:
    """Discover PC-relative and absolute targets from one decode pass."""
    instr_middles = set()
    for blk in blocks.values():
        for inst in blk.instructions:
            for addr in range(inst.offset + 1, inst.offset + inst.size):
                instr_middles.add(addr)

    pc_targets: dict[int, str] = {}
    absolute_targets: set[int] = set()
    for blk in blocks.values():
        for inst in blk.instructions:
            decoded = decode_inst_for_emit(inst).decoded
            for op in (decoded.ea_op, decoded.dst_op):
                if op is None or op.value is None:
                    continue
                if op.mode in ("pcdisp", "pcindex"):
                    if code is None:
                        continue
                    target = op.value
                    if target < 0 or target >= len(code) or target in pc_targets:
                        continue
                    if target in instr_middles:
                        continue
                    string_value = read_string_at(code, target)
                    if string_value and len(string_value) >= 3:
                        pc_targets[target] = f"str_{target:04x}"
                    else:
                        pc_targets[target] = f"pcref_{target:04x}"
                    continue
                if op.mode == "absw":
                    absolute_targets.add(op.value & 0xFFFF)
                    continue
                if op.mode == "absl":
                    absolute_targets.add(op.value)

    return pc_targets, absolute_targets


def discover_absolute_targets(
    blocks: Mapping[int, DisasmBlockLike],
    code_size: int,
    *,
    segment_start: int = 0,
) -> set[int]:
    """Discover internal absolute-address operands in a block set."""
    _, targets = discover_operand_targets(blocks, None)
    segment_end = segment_start + code_size
    return {target for target in targets if segment_start <= target < segment_end}


def filter_internal_absolute_data_targets(targets: set[int],
                                          code_addrs: set[int],
                                          reserved_addrs: set[int]) -> set[int]:
    """Keep internal absolute data refs unless they hit code or reserved symbols."""
    return set(targets) - code_addrs - reserved_addrs


def build_label_map(entities: list[EntityRecord], block_addrs: Iterable[int],
                    reloc_targets: set[int], internal_absolute_data_targets: set[int],
                    pc_targets: dict[int, str]) -> dict[int, str]:
    """Build label names from entities, blocks, relocations, and PC refs."""
    labels: dict[int, str] = {}

    for ent in entities:
        raw_addr = ent["addr"]
        if not isinstance(raw_addr, str):
            raise TypeError("entity addr must be a hex string")
        addr = int(raw_addr, 16)
        raw_name = ent.get("name")
        if raw_name:
            labels[addr] = raw_name
        elif ent["type"] == "code":
            labels[addr] = f"sub_{addr:04x}"

    for addr in sorted(block_addrs):
        if addr not in labels:
            labels[addr] = f"loc_{addr:04x}"

    for addr in sorted(reloc_targets):
        if addr not in labels:
            labels[addr] = f"dat_{addr:04x}"

    for addr in sorted(internal_absolute_data_targets):
        if addr not in labels:
            labels[addr] = f"dat_{addr:04x}"

    for addr, name in sorted(pc_targets.items()):
        if addr not in labels:
            labels[addr] = name

    return labels


def apply_generic_data_label_promotions(labels: dict[int, str],
                                        pc_targets: dict[int, str],
                                        generic_label_addrs: set[int],
                                        promoted_labels: dict[int, str]) -> None:
    """Promote explicit generic data labels to typed names."""
    for addr, promoted in promoted_labels.items():
        if addr not in generic_label_addrs:
            continue
        labels[addr] = promoted
        if addr in pc_targets:
            pc_targets[addr] = promoted


def apply_generic_data_size_promotions(
    labels: dict[int, str],
    generic_label_addrs: set[int],
    data_access_sizes: Mapping[int, int],
) -> None:
    """Promote generic data labels to neutral size-based names when known."""
    prefixes = {1: "byte", 2: "word", 4: "long"}
    for addr in generic_label_addrs:
        label = labels.get(addr)
        if label is None or not label.startswith("dat_"):
            continue
        size = data_access_sizes.get(addr)
        if size is None:
            continue
        prefix = prefixes.get(size)
        if prefix is None:
            continue
        labels[addr] = f"{prefix}_{addr:04x}"


def add_hint_labels(labels: dict[int, str], hint_blocks: dict[int, DisasmBlockLike],
                    code_addrs: set[int]) -> None:
    """Add hint-only labels without overriding core-derived labels."""
    for addr in sorted(hint_blocks):
        if addr not in labels:
            labels[addr] = f"hint_{addr:04x}"
        blk = hint_blocks[addr]
        for succ in blk.successors:
            if succ == blk.end:
                continue
            if succ not in labels:
                if succ in hint_blocks:
                    labels[succ] = f"hint_{succ:04x}"
                elif succ in code_addrs:
                    labels[succ] = f"loc_{succ:04x}"
        if not blk.instructions:
            continue
        for node in blk.instructions[-1].operand_nodes or ():
            target = node.target
            if target is None or target in labels:
                continue
            if target in hint_blocks:
                labels[target] = f"hint_{target:04x}"
            elif target in code_addrs:
                labels[target] = f"loc_{target:04x}"


def build_reloc_map(hunks: list[Hunk], hunk_idx: int) -> dict[int, int]:
    """Build offset->target map from absolute reloc entries for a hunk."""
    from m68k.hunk_parser import _HUNK_KB

    reloc_sem = _HUNK_KB.RELOCATION_SEMANTICS
    abs_types = set()
    for name, sem in reloc_sem.items():
        if sem[1] == _HUNK_KB.RelocMode.ABSOLUTE and name in HunkType.__members__:
            abs_types.add(HunkType[name])

    reloc_map: dict[int, int] = {}
    for hunk in hunks:
        if hunk.index != hunk_idx:
            continue
        for reloc in hunk.relocs:
            try:
                rtype = HunkType(reloc.reloc_type)
            except ValueError:
                continue
            if rtype not in abs_types:
                continue
            if rtype.name not in reloc_sem:
                raise KeyError(
                    f"relocation_semantics missing for {rtype.name}")
            sem_info = reloc_sem[rtype.name]
            nbytes = sem_info[0]
            fmt = {4: ">I", 2: ">H"}.get(nbytes)
            if fmt is None:
                raise ValueError(
                    f"Unsupported reloc byte width {nbytes} for {rtype.name}")
            for offset in reloc.offsets:
                if offset + nbytes <= len(hunk.data):
                    target = struct.unpack_from(fmt, hunk.data, offset)[0]
                    reloc_map[offset] = target
    return reloc_map


def build_reloc_target_hunk_map(hunks: list[Hunk], hunk_idx: int) -> dict[int, int]:
    """Build offset->target_hunk map from absolute reloc entries for a hunk."""
    from m68k.hunk_parser import _HUNK_KB

    reloc_sem = _HUNK_KB.RELOCATION_SEMANTICS
    abs_types = set()
    for name, sem in reloc_sem.items():
        if sem[1] == _HUNK_KB.RelocMode.ABSOLUTE and name in HunkType.__members__:
            abs_types.add(HunkType[name])

    reloc_target_hunks: dict[int, int] = {}
    for hunk in hunks:
        if hunk.index != hunk_idx:
            continue
        for reloc in hunk.relocs:
            try:
                rtype = HunkType(reloc.reloc_type)
            except ValueError:
                continue
            if rtype not in abs_types:
                continue
            for offset in reloc.offsets:
                reloc_target_hunks[offset] = reloc.target_hunk
    return reloc_target_hunks
