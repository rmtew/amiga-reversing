from __future__ import annotations

import struct

from m68k_kb import runtime_os
from disasm.decode import decode_inst_for_emit
from m68k.hunk_parser import HunkType
from m68k.strings import read_string_at


def discover_pc_relative_targets(blocks: dict, code: bytes) -> dict[int, str]:
    """Discover PC-relative operand targets in flow-verified blocks."""
    pc_targets, _ = discover_operand_targets(blocks, code)
    return pc_targets


def discover_operand_targets(blocks: dict, code: bytes | None) -> tuple[dict[int, str], set[int]]:
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
            decoded = decode_inst_for_emit(inst)["decoded"]
            for op in (decoded["ea_op"], decoded["dst_op"]):
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


def discover_absolute_targets(blocks: dict, code_size: int) -> set[int]:
    """Discover internal absolute-address operands in a block set."""
    _, targets = discover_operand_targets(blocks, None)
    return {target for target in targets if 0 <= target < code_size}


def load_fixed_absolute_addresses() -> set[int]:
    """Return KB-declared fixed system absolute addresses."""
    exec_base = runtime_os.META.get("exec_base_addr")
    if exec_base is None:
        raise KeyError("OS KB missing META.exec_base_addr")
    address = exec_base.get("address")
    if address is None:
        raise KeyError("OS KB missing META.exec_base_addr.address")
    return {address}


def filter_core_absolute_targets(targets: set[int],
                                 code_addrs: set[int],
                                 fixed_addrs: set[int]) -> set[int]:
    """Keep core absolute refs unless they hit code or fixed system addresses."""
    return set(targets) - code_addrs - fixed_addrs


def build_label_map(entities: list[dict], blocks: dict,
                    reloc_targets: set[int], absolute_targets: set[int],
                    pc_targets: dict[int, str]) -> dict[int, str]:
    """Build label names from entities, blocks, relocations, and PC refs."""
    labels = {}

    for ent in entities:
        addr = int(ent["addr"], 16)
        if ent.get("name"):
            labels[addr] = ent["name"]
        elif ent["type"] == "code":
            labels[addr] = f"sub_{addr:04x}"

    for addr in sorted(blocks):
        if addr not in labels:
            labels[addr] = f"loc_{addr:04x}"

    for addr in sorted(reloc_targets):
        if addr not in labels:
            labels[addr] = f"dat_{addr:04x}"

    for addr in sorted(absolute_targets):
        if addr not in labels:
            labels[addr] = f"dat_{addr:04x}"

    for addr, name in sorted(pc_targets.items()):
        if addr not in labels:
            labels[addr] = name

    return labels


def add_hint_labels(labels: dict[int, str], hint_blocks: dict,
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


def build_reloc_map(hunks, hunk_idx: int) -> dict[int, int]:
    """Build offset->target map from absolute reloc entries for a hunk."""
    from m68k.hunk_parser import _HUNK_KB

    reloc_sem = _HUNK_KB.RELOCATION_SEMANTICS
    abs_types = set()
    for name, sem in reloc_sem.items():
        if sem[1] == _HUNK_KB.RelocMode.ABSOLUTE and name in HunkType.__members__:
            abs_types.add(HunkType[name])

    reloc_map = {}
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
            sem = reloc_sem.get(rtype.name)
            if sem is None:
                raise KeyError(
                    f"relocation_semantics missing for {rtype.name}")
            nbytes = sem[0]
            fmt = {4: ">I", 2: ">H"}.get(nbytes)
            if fmt is None:
                raise ValueError(
                    f"Unsupported reloc byte width {nbytes} for {rtype.name}")
            for offset in reloc.offsets:
                if offset + nbytes <= len(hunk.data):
                    target = struct.unpack_from(fmt, hunk.data, offset)[0]
                    reloc_map[offset] = target
    return reloc_map
