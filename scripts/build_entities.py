#!/usr/bin/env py.exe
"""Build entities.jsonl from hunk binary analysis.

Parses an Amiga hunk executable, runs the symbolic executor on CODE hunks,
and generates entities with bidirectional cross-references.

Entity granularity: subroutine-level for code (not basic-block-level).
Uncovered regions between subroutines are marked as 'unknown'.

Usage:
    python build_entities.py <binary_path> -t targets/amiga_hunk_genam
    python build_entities.py <binary_path> --output entities.jsonl
"""

import argparse
import json
import sys
from collections import defaultdict
from collections.abc import MutableMapping
from contextlib import nullcontext
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from disasm.analysis_layout import (
    resolved_analysis_start_offset,
    resolved_entry_points,
    resolved_raw_analysis_base_addr,
    target_seeded_entrypoint_offsets,
)
from disasm.analysis_loader import analysis_cache_root, hunk_analysis_cache_path
from disasm.binary_source import BinarySource, HunkFileBinarySource
from disasm.entry_seeds import (
    apply_entry_seed_config,
    build_entry_seed_config,
    scoped_entry_initial_states,
)
from disasm.phase_timing import PhaseTimer
from disasm.target_metadata import (
    SeededCodeEntrypointMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    load_required_target_metadata,
    target_structure_spec,
)
from m68k.analysis import _RELOC_INFO, analyze_hunk, resolve_reloc_target
from m68k.hunk_parser import Hunk, HunkType, MemType, parse
from m68k.indirect_core import IndirectSite
from m68k.instruction_decode import decode_inst_operands
from m68k.instruction_kb import instruction_kb
from m68k.instruction_primitives import Operand
from m68k.m68k_executor import BasicBlock, XRef
from m68k.name_entities import name_subroutines
from m68k.os_calls import AppSlotInfo, build_app_slot_infos, build_target_local_os_kb
from m68k_kb import runtime_m68k_decode

PROJECT_ROOT = Path(__file__).parent.parent
JsonDict = dict[str, Any]


@dataclass(frozen=True, slots=True)
class SubroutineRange:
    addr: int
    end: int
    block_count: int
    instr_count: int
    reached: bool = True


@dataclass(frozen=True, slots=True)
class ReferencedAppSlot:
    offset: int
    symbol: str
    struct: str | None
    size: int | None
    pointer_struct: str | None
    named_base: str | None
    storage_kind: str | None = None
    semantic_type: str | None = None
    parser_role: str | None = None
    parser_routine: str | None = None
    parse_order: int | None = None


@dataclass(frozen=True, slots=True)
class ReferencedIndirectSite:
    addr: int
    shape: str
    status: str
    flow: str
    detail: str | None = None
    target_count: int | None = None


def _rebase_local_addr(addr: int, base_addr: int) -> int:
    rebased = addr - base_addr
    if rebased < 0:
        raise ValueError(f"Cannot rebase address 0x{addr:X} below base 0x{base_addr:X}")
    return rebased


def _maybe_rebase_addr(addr: int, base_addr: int, code_size: int) -> int:
    if base_addr <= addr < base_addr + code_size:
        return _rebase_local_addr(addr, base_addr)
    return addr


def _rebase_instruction_block(block: BasicBlock, base_addr: int, code_size: int) -> BasicBlock:
    return BasicBlock(
        start=_rebase_local_addr(block.start, base_addr),
        end=_rebase_local_addr(block.end, base_addr),
        instructions=[
            replace(inst, offset=_rebase_local_addr(inst.offset, base_addr))
            for inst in block.instructions
        ],
        successors=[_maybe_rebase_addr(addr, base_addr, code_size) for addr in block.successors],
        predecessors=[_maybe_rebase_addr(addr, base_addr, code_size) for addr in block.predecessors],
        xrefs=[
            XRef(
                src=_maybe_rebase_addr(xref.src, base_addr, code_size),
                dst=_maybe_rebase_addr(xref.dst, base_addr, code_size),
                type=xref.type,
                conditional=xref.conditional,
            )
            for xref in block.xrefs
        ],
        is_entry=block.is_entry,
        is_return=block.is_return,
    )


def _rebase_raw_analysis(
    blocks: dict[int, BasicBlock],
    xrefs: list[XRef],
    call_targets: set[int],
    hint_blocks: dict[int, BasicBlock],
    hint_reasons: dict[int, Any],
    lib_calls: list[Any],
    indirect_sites: list[IndirectSite],
    *,
    base_addr: int,
    code_size: int,
) -> tuple[
    dict[int, BasicBlock],
    list[XRef],
    set[int],
    dict[int, BasicBlock],
    dict[int, Any],
    list[Any],
    list[IndirectSite],
]:
    rebased_blocks = {
        _rebase_local_addr(start, base_addr): _rebase_instruction_block(block, base_addr, code_size)
        for start, block in blocks.items()
    }
    rebased_xrefs = [
        XRef(
            src=_maybe_rebase_addr(xref.src, base_addr, code_size),
            dst=_maybe_rebase_addr(xref.dst, base_addr, code_size),
            type=xref.type,
            conditional=xref.conditional,
        )
        for xref in xrefs
    ]
    rebased_call_targets = {
        _maybe_rebase_addr(addr, base_addr, code_size) for addr in call_targets
    }
    rebased_hint_blocks = {
        _rebase_local_addr(start, base_addr): _rebase_instruction_block(block, base_addr, code_size)
        for start, block in hint_blocks.items()
    }
    rebased_hint_reasons = {
        _maybe_rebase_addr(addr, base_addr, code_size): replace(
            reason,
            referenced_from=tuple(
                _maybe_rebase_addr(ref, base_addr, code_size) for ref in reason.referenced_from
            ),
        )
        for addr, reason in hint_reasons.items()
    }
    rebased_lib_calls = [
        replace(
            call,
            addr=_maybe_rebase_addr(call.addr, base_addr, code_size),
            block=_maybe_rebase_addr(call.block, base_addr, code_size),
            dispatch=(
                None if call.dispatch is None else _maybe_rebase_addr(call.dispatch, base_addr, code_size)
            ),
        )
        for call in lib_calls
    ]
    rebased_indirect_sites = [
        replace(
            site,
            addr=_maybe_rebase_addr(site.addr, base_addr, code_size),
            target=None if site.target is None else _maybe_rebase_addr(site.target, base_addr, code_size),
        )
        for site in indirect_sites
    ]
    return (
        rebased_blocks,
        rebased_xrefs,
        rebased_call_targets,
        rebased_hint_blocks,
        rebased_hint_reasons,
        rebased_lib_calls,
        rebased_indirect_sites,
    )


def _filter_pre_entry_blocks(
    blocks: dict[int, BasicBlock],
    entry_point: int | None,
) -> dict[int, BasicBlock]:
    if entry_point is None or entry_point <= 0:
        return dict(blocks)
    keep = {
        addr
        for addr, block in blocks.items()
        if block.end > entry_point
    }
    filtered: dict[int, BasicBlock] = {}
    for _addr, block in blocks.items():
        if block.end <= entry_point:
            continue
        kept_instructions = [inst for inst in block.instructions if inst.offset >= entry_point]
        if not kept_instructions:
            continue
        new_start = entry_point if block.start < entry_point else block.start
        filtered[new_start] = replace(
            block,
            start=new_start,
            instructions=kept_instructions,
            is_entry=(block.is_entry or new_start == entry_point),
            successors=[succ for succ in block.successors if succ in keep],
            predecessors=[pred for pred in block.predecessors if pred in keep and pred >= entry_point],
            xrefs=[xref for xref in block.xrefs if xref.src >= entry_point and xref.dst >= entry_point],
        )
    return filtered


def _filter_hunk_local_call_targets(
    call_targets: set[int],
    *,
    entry_addr: int,
    code_size: int,
) -> set[int]:
    return {
        addr for addr in call_targets
        if entry_addr <= addr < code_size
    }


def fmt_addr(addr: int) -> str:
    return f"0x{addr:04X}"


def fmt_disp(offset: int) -> str:
    if offset < 0:
        return f"-0x{abs(offset):04X}"
    return f"0x{offset:04X}"


def _structured_prefix_entities(
    metadata: TargetMetadata | None,
    hunk_idx: int,
    *,
    include_structure: bool,
) -> list[JsonDict]:
    if not include_structure:
        return []
    structure = target_structure_spec(metadata)
    if structure is None:
        return []
    entities: list[JsonDict] = []
    for region in structure.regions:
        payload: JsonDict = {
            "addr": fmt_addr(region.start),
            "end": fmt_addr(region.end),
            "type": "data",
            "subtype": region.subtype,
            "confidence": "tool-inferred",
            "hunk": hunk_idx,
        }
        if region.struct_name is not None:
            payload["struct"] = region.struct_name
        entities.append(payload)
    return entities


def _entity_range(entity: JsonDict) -> tuple[int, int]:
    return int(cast(str, entity["addr"]), 16), int(cast(str, entity["end"]), 16)


def _ranges_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and end_a > start_b


def _merge_seeded_entity(existing: JsonDict, seeded: SeededEntityMetadata) -> JsonDict:
    merged = dict(existing)
    if seeded.end is not None and fmt_addr(seeded.end) != merged["end"]:
        raise ValueError(
            f"Seeded entity at {fmt_addr(seeded.addr)} conflicts with existing end {merged['end']}"
        )
    if seeded.type is not None and seeded.type != merged["type"]:
        raise ValueError(
            f"Seeded entity at {fmt_addr(seeded.addr)} conflicts with existing type {merged['type']}"
        )
    existing_subtype = cast(str | None, merged.get("subtype"))
    if seeded.subtype is not None and existing_subtype is not None and seeded.subtype != existing_subtype:
        raise ValueError(
            f"Seeded entity at {fmt_addr(seeded.addr)} conflicts with existing subtype {existing_subtype}"
        )
    if seeded.name is not None:
        merged["name"] = seeded.name
    if seeded.comment is not None:
        merged["comment"] = seeded.comment
    if seeded.subtype is not None:
        merged["subtype"] = seeded.subtype
    return merged


def _seeded_entity_payload(seeded: SeededEntityMetadata) -> JsonDict:
    if seeded.end is None:
        raise ValueError(f"Seeded entity at {fmt_addr(seeded.addr)} is missing end")
    if seeded.type is None:
        raise ValueError(f"Seeded entity at {fmt_addr(seeded.addr)} is missing type")
    payload: JsonDict = {
        "addr": fmt_addr(seeded.addr),
        "end": fmt_addr(seeded.end),
        "type": seeded.type,
        "confidence": "seeded",
        "hunk": seeded.hunk,
    }
    if seeded.subtype is not None:
        payload["subtype"] = seeded.subtype
    if seeded.name is not None:
        payload["name"] = seeded.name
    if seeded.comment is not None:
        payload["comment"] = seeded.comment
    return payload


def _apply_seeded_entities(
    entities: list[JsonDict],
    seeded_entities: tuple[SeededEntityMetadata, ...],
    *,
    hunk_idx: int,
) -> list[JsonDict]:
    if not seeded_entities:
        return list(entities)
    merged = list(entities)
    for seeded in seeded_entities:
        if seeded.hunk != hunk_idx:
            continue
        match_index = next(
            (
                index
                for index, entity in enumerate(merged)
                if int(cast(str, entity["addr"]), 16) == seeded.addr
            ),
            None,
        )
        if match_index is not None:
            merged[match_index] = _merge_seeded_entity(merged[match_index], seeded)
            continue
        if seeded.end is None:
            raise ValueError(
                f"Seeded entity at {fmt_addr(seeded.addr)} is missing end and does not match an existing entity"
            )
        seeded_payload = _seeded_entity_payload(seeded)
        seeded_start, seeded_end = _entity_range(seeded_payload)
        replace_indices: list[int] = []
        for index, entity in enumerate(merged):
            entity_start, entity_end = _entity_range(entity)
            if _ranges_overlap(seeded_start, seeded_end, entity_start, entity_end):
                if cast(str, entity.get("confidence", "tool-inferred")) in {"tool-inferred", "hint"}:
                    replace_indices.append(index)
                    continue
                raise ValueError(
                    f"Seeded entity {fmt_addr(seeded_start)}..{fmt_addr(seeded_end)} overlaps "
                    f"existing entity {entity['addr']}..{entity['end']}"
                )
        for index in reversed(replace_indices):
            merged.pop(index)
        merged.append(seeded_payload)
    return merged


def _apply_seeded_code_entrypoints(
    entities: list[JsonDict],
    seeded_entrypoints: tuple[SeededCodeEntrypointMetadata, ...],
    *,
    hunk_idx: int,
) -> list[JsonDict]:
    if not seeded_entrypoints:
        return list(entities)
    merged = list(entities)
    for seeded in seeded_entrypoints:
        if seeded.hunk != hunk_idx:
            continue
        match_index = next(
            (
                index
                for index, entity in enumerate(merged)
                if int(cast(str, entity["addr"]), 16) == seeded.addr
            ),
            None,
        )
        if match_index is None:
            continue
        entity = dict(merged[match_index])
        if entity["type"] != "code":
            raise ValueError(
                f"Seeded code entrypoint at {fmt_addr(seeded.addr)} matches non-code entity {entity['type']}"
            )
        entity["name"] = seeded.name
        comment = seeded.comment
        if comment is None and seeded.role is not None:
            comment = seeded.role
        elif comment is not None and seeded.role is not None:
            comment = f"{seeded.role}: {comment}"
        if comment is not None:
            entity["comment"] = comment
        merged[match_index] = entity
    return merged


def build_subroutine_map(blocks: dict[int, BasicBlock],
                         call_targets: set[int],
                         entry_point: int) -> list[SubroutineRange]:
    """Compute subroutine boundaries from basic blocks and call targets.

    Returns typed subroutine ranges.
    """
    opword_bytes = runtime_m68k_decode.OPWORD_BYTES

    # All subroutine entry points
    entries = sorted({entry_point} | call_targets)

    # Map each block to its owning subroutine.
    # A block belongs to the entry it is reachable from without crossing
    # another entry point.
    block_owner: dict[int, int] = {}

    for entry in entries:
        if entry not in blocks:
            continue
        # BFS from entry, stopping at other entry points
        work = [entry]
        visited = set()
        while work:
            addr = work.pop()
            if addr in visited:
                continue
            if addr != entry and addr in call_targets:
                continue  # different subroutine
            if addr not in blocks:
                continue
            if addr in block_owner:
                continue  # already claimed
            visited.add(addr)
            block_owner[addr] = entry
            for succ in blocks[addr].successors:
                work.append(succ)

    # Group blocks by owner
    sub_blocks: dict[int, list[BasicBlock]] = defaultdict(list)
    for block_addr, owner in block_owner.items():
        sub_blocks[owner].append(blocks[block_addr])

    subroutines: list[SubroutineRange] = []
    for entry in entries:
        if entry in sub_blocks:
            blist = sub_blocks[entry]
            sub_start = min(b.start for b in blist)
            sub_end = max(b.end for b in blist)
            instr_count = sum(len(b.instructions) for b in blist)
            subroutines.append(SubroutineRange(
                addr=sub_start,
                end=sub_end,
                block_count=len(blist),
                instr_count=instr_count,
            ))
        else:
            # Call target not reached by executor - create stub entity.
            # End placeholder: minimum instruction size from KB opword_bytes.
            subroutines.append(SubroutineRange(
                addr=entry,
                end=entry + opword_bytes,
                block_count=0,
                instr_count=0,
                reached=False,
            ))

    # Sort by address
    subroutines.sort(key=lambda s: s.addr)

    # Fix overlaps: truncate earlier subroutine if it overlaps the next
    for i in range(len(subroutines) - 1):
        if subroutines[i].end > subroutines[i + 1].addr:
            subroutines[i] = SubroutineRange(
                addr=subroutines[i].addr,
                end=subroutines[i + 1].addr,
                block_count=subroutines[i].block_count,
                instr_count=subroutines[i].instr_count,
                reached=subroutines[i].reached,
            )

    return subroutines


def build_reloc_references(hunks: list[Any], code_size: int,
                           subroutines: list[SubroutineRange]) -> list[JsonDict]:
    """Extract data references from relocation entries.

    Reloc offsets point to longwords in the code that contain absolute
    addresses. Targets outside known subroutines are potential data regions.
    """
    # Build address lookup for subroutines
    sub_ranges = [(s.addr, s.end) for s in subroutines]

    def in_known_sub(addr: int) -> bool:
        return any(start <= addr < end for start, end in sub_ranges)

    data_refs: list[JsonDict] = []
    for hunk in hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            continue
        for reloc in hunk.relocs:
            if reloc.target_hunk != hunk.index:
                continue
            info = _RELOC_INFO.get(reloc.reloc_type)
            if info is None:
                continue
            for offset in reloc.offsets:
                target = resolve_reloc_target(reloc, offset, hunk.data)
                if target is not None and 0 <= target < code_size and not in_known_sub(target):
                    data_refs.append({
                        "addr": target,
                        "offset": offset,
                        "hunk": hunk.index,
                        "ptr_size": info["bytes"],
                    })

    # Deduplicate by target address
    seen: set[int] = set()
    unique: list[JsonDict] = []
    for ref in data_refs:
        if ref["addr"] not in seen:
            seen.add(ref["addr"])
            unique.append(ref)
    unique.sort(key=lambda r: r["addr"])
    return unique


def fill_gaps(entities: list[JsonDict], total_size: int, hunk_idx: int) -> list[JsonDict]:
    """Add 'unknown' entities for unmapped regions in [0, total_size)."""
    sorted_ents = sorted(entities, key=lambda e: int(e["addr"], 16))
    gaps: list[tuple[int, int]] = []

    # Gap before first entity
    if sorted_ents:
        first_start = int(sorted_ents[0]["addr"], 16)
        if first_start > 0:
            gaps.append((0, first_start))
    else:
        gaps.append((0, total_size))

    # Gaps between entities
    for i in range(len(sorted_ents) - 1):
        curr_end = int(sorted_ents[i]["end"], 16)
        next_start = int(sorted_ents[i + 1]["addr"], 16)
        if next_start > curr_end:
            gaps.append((curr_end, next_start))

    # Gap after last entity
    if sorted_ents:
        last_end = int(sorted_ents[-1]["end"], 16)
        if last_end < total_size:
            gaps.append((last_end, total_size))

    gap_entities: list[JsonDict] = []
    for start, end in gaps:
        gap_entities.append({
            "addr": fmt_addr(start),
            "end": fmt_addr(end),
            "type": "unknown",
            "confidence": "tool-inferred",
            "hunk": hunk_idx,
        })
    return gap_entities


def assign_xrefs(subroutines: list[SubroutineRange], xrefs: list[XRef],
                 ) -> tuple[dict[int, dict[str, set[int]]], dict[int, dict[str, set[int]]]]:
    """Map instruction-level xrefs to subroutine-level entity xrefs.

    Returns (forward_map, reverse_map) where each maps entity addr to
    {field: set(segment_addrs)}.
    Prints count of xrefs dropped due to unmapped src/dst addresses.
    """
    # For fast range lookup, build sorted list
    sorted_subs = sorted(subroutines, key=lambda s: s.addr)

    def find_sub(addr: int) -> int | None:
        """Find which subroutine contains the given address."""
        # Binary search
        lo, hi = 0, len(sorted_subs) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            s = sorted_subs[mid]
            if addr < s.addr:
                hi = mid - 1
            elif addr >= s.end:
                lo = mid + 1
            else:
                return s.addr
        return None

    forward: dict[int, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    reverse: dict[int, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    dropped = 0

    for xref in xrefs:
        if xref.type == "fallthrough":
            continue  # internal control flow

        src_sub = find_sub(xref.src)
        dst_sub = find_sub(xref.dst)

        if src_sub is None or dst_sub is None:
            dropped += 1
            continue
        if src_sub == dst_sub:
            continue  # intra-subroutine

        if xref.type == "call":
            forward[src_sub]["calls"].add(dst_sub)
            reverse[dst_sub]["called_by"].add(src_sub)
        elif xref.type in ("branch", "jump"):
            # Inter-subroutine branches/jumps are treated as calls
            forward[src_sub]["calls"].add(dst_sub)
            reverse[dst_sub]["called_by"].add(src_sub)

    if dropped:
        print(f"  {dropped} xrefs dropped (src or dst outside known subroutines)")
    return forward, reverse


def _operand_app_disp(op: Operand | None, base_reg: int) -> int | None:
    if op is None:
        return None
    if op.reg != base_reg:
        return None
    if op.mode == "disp":
        return cast(int, op.value)
    if op.mode == "index":
        if op.memory_indirect:
            return None
        return cast(int, op.base_displacement if op.full_extension else op.value)
    return None


def _find_app_slot_reference(offset: int,
                             slot_infos: tuple[AppSlotInfo, ...]) -> AppSlotInfo | None:
    for info in slot_infos:
        if info.offset == offset:
            return info
        if info.size is None:
            continue
        if info.offset <= offset < info.offset + info.size:
            return info
    return None


def _os_input_reg_key(regs: tuple[str, ...]) -> str:
    if not regs:
        raise ValueError("OS input must have at least one register")
    return "/".join(regs)


def _typed_call_inputs_payload(inputs: tuple[Any, ...]) -> JsonDict:
    payload: JsonDict = {}
    for inp in inputs:
        if not inp.type:
            continue
        info: JsonDict = {"type": inp.type}
        if inp.i_struct:
            info["i_struct"] = inp.i_struct
        payload[_os_input_reg_key(inp.regs)] = info
    return payload


def collect_subroutine_app_slots(sub: SubroutineRange,
                                 blocks: dict[int, BasicBlock],
                                 slot_infos: tuple[AppSlotInfo, ...],
                                 base_reg: int,
                                 ) -> tuple[ReferencedAppSlot, ...]:
    block_list = [
        block for block in blocks.values()
        if sub.addr <= block.start < sub.end
    ]
    if not block_list:
        return ()
    referenced: dict[int, ReferencedAppSlot] = {}
    for block in sorted(block_list, key=lambda item: item.start):
        for inst in block.instructions:
            kb = instruction_kb(inst)
            decoded = decode_inst_operands(inst, kb)
            for op in (decoded.ea_op, decoded.dst_op):
                offset = _operand_app_disp(op, base_reg)
                if offset is None:
                    continue
                info = _find_app_slot_reference(offset, slot_infos)
                if info is None:
                    continue
                referenced.setdefault(
                    info.offset,
                    ReferencedAppSlot(
                        offset=info.offset,
                        symbol=info.symbol,
                        struct=info.struct,
                        size=info.size,
                        pointer_struct=info.pointer_struct,
                        named_base=info.named_base,
                        storage_kind=info.storage_kind,
                        semantic_type=info.semantic_type,
                        parser_role=info.parser_role,
                        parser_routine=info.parser_routine,
                        parse_order=info.parse_order,
                    ),
                )
    return tuple(referenced[offset] for offset in sorted(referenced))


def app_slot_entity_payloads(app_slots: tuple[ReferencedAppSlot, ...]) -> list[JsonDict]:
    payloads: list[JsonDict] = []
    for slot in app_slots:
        payload: JsonDict = {
            "offset": fmt_disp(slot.offset),
            "symbol": slot.symbol,
            **({"named_base": slot.named_base} if slot.named_base is not None else {}),
            **({"storage_kind": slot.storage_kind} if slot.storage_kind is not None else {}),
            **({"semantic_type": slot.semantic_type} if slot.semantic_type is not None else {}),
            **({"parser_role": slot.parser_role} if slot.parser_role is not None else {}),
            **({"parser_routine": slot.parser_routine} if slot.parser_routine is not None else {}),
            **({"parse_order": slot.parse_order} if slot.parse_order is not None else {}),
        }
        if slot.struct is not None:
            payload["kind"] = "struct_instance"
            payload["struct"] = slot.struct
            if slot.size is None:
                raise ValueError(f"Struct app slot {slot.symbol} is missing size")
            payload["size"] = slot.size
        elif slot.pointer_struct is not None:
            payload["kind"] = "struct_pointer"
            payload["pointer_struct"] = slot.pointer_struct
        payloads.append(payload)
    return payloads


def collect_subroutine_indirect_sites(sub: SubroutineRange,
                                      indirect_sites: list[IndirectSite],
                                      ) -> tuple[ReferencedIndirectSite, ...]:
    sites = [
        ReferencedIndirectSite(
            addr=site.addr,
            shape=site.shape,
            status=site.status.value,
            flow=site.flow_type.value,
            detail=site.detail,
            target_count=site.target_count,
        )
        for site in indirect_sites
        if sub.addr <= site.addr < sub.end
    ]
    return tuple(sorted(sites, key=lambda site: site.addr))


def indirect_site_entity_payloads(
        indirect_sites: tuple[ReferencedIndirectSite, ...]) -> list[JsonDict]:
    return [{
        "addr": fmt_addr(site.addr),
        "shape": site.shape,
        "status": site.status,
        "flow": site.flow,
        **({"detail": site.detail} if site.detail is not None else {}),
        **({"target_count": site.target_count}
           if site.target_count is not None else {}),
    } for site in indirect_sites]


def _slot_struct_refs(slot: JsonDict) -> set[str]:
    refs: set[str] = set()
    struct_name = slot.get("struct")
    if struct_name is not None:
        refs.add(cast(str, struct_name))
    pointer_struct = slot.get("pointer_struct")
    if pointer_struct is not None:
        refs.add(cast(str, pointer_struct))
    return refs


def summarize_entity_app_slots(entities: list[JsonDict]) -> None:
    code_entities = {
        int(ent["addr"], 16): ent
        for ent in entities
        if ent.get("type") == "code"
    }
    summary_cache: dict[int, tuple[set[str], set[str]]] = {}

    def _visit(addr: int, stack: set[int]) -> tuple[set[str], set[str]]:
        cached = summary_cache.get(addr)
        if cached is not None:
            return cached
        if addr in stack:
            return set(), set()
        ent = code_entities[addr]
        direct_named_bases = {
            slot["named_base"]
            for slot in ent.get("app_slots", ())
            if slot.get("named_base") is not None
        }
        direct_struct_refs: set[str] = set()
        for slot in ent.get("app_slots", ()):
            direct_struct_refs.update(_slot_struct_refs(slot))
        all_named_bases = set(direct_named_bases)
        all_struct_refs = set(direct_struct_refs)
        next_stack = set(stack)
        next_stack.add(addr)
        for call_addr in ent.get("calls", ()):
            callee = code_entities.get(int(call_addr, 16))
            if callee is None:
                continue
            callee_named_bases, callee_struct_refs = _visit(int(call_addr, 16), next_stack)
            all_named_bases.update(callee_named_bases)
            all_struct_refs.update(callee_struct_refs)
        ent["named_bases"] = sorted(direct_named_bases)
        ent["struct_refs"] = sorted(direct_struct_refs)
        ent["named_bases_transitive"] = sorted(all_named_bases)
        ent["struct_refs_transitive"] = sorted(all_struct_refs)
        summary_cache[addr] = (all_named_bases, all_struct_refs)
        return summary_cache[addr]

    for addr in sorted(code_entities):
        _visit(addr, set())


def build_entities_from_source(binary_source: BinarySource, output_path: str | None = None,
                               base_addr: int = 0, code_start: int = 0,
                               phase_timer: PhaseTimer | None = None) -> int:
    """Main pipeline: parse binary, run executor, generate entities."""
    if output_path is None:
        output_path = "entities.jsonl"

    print(f"Parsing {binary_source.display_path}...")
    output_target_dir = Path(output_path).parent if output_path is not None else None
    target_metadata = load_required_target_metadata(
        target_dir=output_target_dir,
        source_kind=binary_source.kind,
        parent_disk_id=binary_source.parent_disk_id,
    )
    seed_config = build_entry_seed_config(target_metadata)
    seeded_entities = () if target_metadata is None else target_metadata.seeded_entities
    seeded_code_entrypoints = () if target_metadata is None else target_metadata.seeded_code_entrypoints
    with phase_timer.phase("entities.parse_source") if phase_timer is not None else nullcontext():
        if binary_source.kind == "raw_binary":
            raw_bytes = binary_source.read_bytes()
            hf_hunks = [
                Hunk(
                    index=0,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=len(raw_bytes),
                    data=raw_bytes,
                )
            ]
        else:
            hf = parse(binary_source.read_bytes())
            if not hf.is_executable:
                print("ERROR: not an executable hunk file")
                return 1
            hf_hunks = hf.hunks

    print(f"  {len(hf_hunks)} hunks")
    for h in hf_hunks:
        print(f"    #{h.index}: {h.type_name} {len(h.data)} bytes, "
              f"{len(h.relocs)} reloc groups, {len(h.symbols)} symbols")

    all_entities: list[JsonDict] = []

    custom_entry_points = (
        ()
        if binary_source.kind == "raw_binary"
        else resolved_entry_points(binary_source, target_metadata, ())
    )
    first_code_hunk_seen = False

    for hunk in hf_hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            # DATA/BSS hunks become entities directly
            etype = "data" if hunk.hunk_type == HunkType.HUNK_DATA else "bss"
            all_entities.append({
                "addr": fmt_addr(0),
                "end": fmt_addr(hunk.alloc_size),
                "type": etype,
                "confidence": "tool-inferred",
                "hunk": hunk.index,
            })
            continue

        include_structure = not first_code_hunk_seen
        code = hunk.data
        code_size = len(code)

        print(f"\nAnalyzing hunk #{hunk.index} "
              f"({code_size} bytes)...")

        # Run shared analysis pipeline
        if binary_source.kind == "raw_binary":
            analysis_start_offset = resolved_analysis_start_offset(binary_source, target_metadata)
            entry_points = resolved_entry_points(binary_source, target_metadata, ())
            extra_entry_points = target_seeded_entrypoint_offsets(target_metadata, hunk_index=hunk.index)
            entry_initial_states = scoped_entry_initial_states(seed_config, entry_points)
            ha = analyze_hunk(
                code,
                [],
                hunk.index,
                base_addr=resolved_raw_analysis_base_addr(binary_source, target_metadata),
                code_start=analysis_start_offset,
                entry_points=entry_points,
                extra_entry_points=extra_entry_points,
                initial_state=seed_config.initial_state,
                entry_initial_states=entry_initial_states,
                phase_timer=phase_timer,
            )
        else:
            entry_points = () if first_code_hunk_seen else custom_entry_points
            extra_entry_points = target_seeded_entrypoint_offsets(target_metadata, hunk_index=hunk.index)
            entry_initial_states = scoped_entry_initial_states(seed_config, entry_points)
            ha = analyze_hunk(code, cast(list[Any], hunk.relocs), hunk.index,
                              base_addr=base_addr, code_start=code_start,
                              entry_points=entry_points,
                              extra_entry_points=extra_entry_points,
                              initial_state=seed_config.initial_state,
                              entry_initial_states=entry_initial_states,
                              phase_timer=phase_timer)
        first_code_hunk_seen = True
        apply_entry_seed_config(ha.platform, seed_config)

        # Cache analysis for gen_disasm reuse
        cache_root = analysis_cache_root(
            binary_source.analysis_cache_path,
            seed_key=seed_config.seed_key,
            base_addr=(
                resolved_raw_analysis_base_addr(binary_source, target_metadata)
                if binary_source.kind == "raw_binary"
                else base_addr
            ),
            code_start=(
                resolved_analysis_start_offset(binary_source, target_metadata)
                if binary_source.kind == "raw_binary"
                else code_start
            ),
            entry_points=entry_points,
            extra_entry_points=extra_entry_points,
        )
        cache_path = hunk_analysis_cache_path(cache_root, hunk.index)
        ha.save(cache_path)
        print(f"  Cached analysis to {cache_path.name}")

        blocks = ha.blocks
        xrefs = ha.xrefs
        call_targets = ha.call_targets
        hint_blocks = ha.hint_blocks
        hint_reasons = ha.hint_reasons
        lib_calls = ha.lib_calls
        indirect_sites = ha.indirect_sites
        if binary_source.kind == "raw_binary" and binary_source.address_model == "runtime_absolute":
            raw_base_addr = binary_source.load_address
            (
                blocks,
                xrefs,
                call_targets,
                hint_blocks,
                hint_reasons,
                lib_calls,
                indirect_sites,
            ) = _rebase_raw_analysis(
                blocks,
                xrefs,
                call_targets,
                hint_blocks,
                hint_reasons,
                lib_calls,
                indirect_sites,
                base_addr=raw_base_addr,
                code_size=code_size,
            )
        entry_addr = (
            binary_source.local_entrypoint
            if binary_source.kind == "raw_binary"
            else (0 if not custom_entry_points else custom_entry_points[0])
        )
        blocks = _filter_pre_entry_blocks(blocks, entry_addr)
        hint_blocks = _filter_pre_entry_blocks(hint_blocks, entry_addr)
        xrefs = [
            xref for xref in xrefs
            if xref.src >= entry_addr and xref.dst >= entry_addr
        ]
        call_targets = _filter_hunk_local_call_targets(
            call_targets,
            entry_addr=entry_addr,
            code_size=code_size,
        )
        lib_calls = [
            call for call in lib_calls
            if call.addr >= entry_addr
        ]
        indirect_sites = [
            site for site in indirect_sites
            if site.addr >= entry_addr
        ]
        os_kb = ha.os_kb
        if os_kb is None:
            raise ValueError("OS KB is required for entity typing")
        os_kb = build_target_local_os_kb(os_kb, target_metadata)
        slot_infos = build_app_slot_infos(
            blocks,
            lib_calls,
            code,
            os_kb,
            ha.platform,
            target_metadata,
        )
        # Build subroutine map
        subroutines = build_subroutine_map(blocks, call_targets, entry_addr)
        stubs = sum(1 for s in subroutines if not s.reached)
        print(f"  {len(subroutines)} subroutines ({stubs} stubs - unreached)")

        # Assign cross-references (reports dropped xrefs)
        fwd_xrefs, rev_xrefs = assign_xrefs(subroutines, xrefs)

        # Build library call map: subroutine addr -> list of OS calls
        lib_call_map: defaultdict[int, list[Any]] = defaultdict(list)
        if lib_calls:
            sorted_subs = sorted(subroutines, key=lambda s: s.addr)
            for call in lib_calls:
                for sub in sorted_subs:
                    if sub.addr <= call.addr < sub.end:
                        lib_call_map[sub.addr].append(call)
                        break

        # Build subroutine entities
        stub_count = 0
        for sub in subroutines:
            ent: JsonDict = {
                "addr": fmt_addr(sub.addr),
                "end": fmt_addr(sub.end),
                "type": "code",
                "confidence": "tool-inferred",
                "hunk": hunk.index,
                "block_count": sub.block_count,
                "instr_count": sub.instr_count,
            }
            if not sub.reached:
                ent["stub"] = True
                stub_count += 1
            addr = sub.addr
            # Add forward xrefs
            if addr in fwd_xrefs:
                for field, targets in fwd_xrefs[addr].items():
                    ent[field] = sorted(fmt_addr(t) for t in targets)
            # Add reverse xrefs
            if addr in rev_xrefs:
                for field, sources in rev_xrefs[addr].items():
                    ent[field] = sorted(fmt_addr(s) for s in sources)
            # Add OS library calls made by this subroutine
            if addr in lib_call_map:
                calls = lib_call_map[addr]
                ent["os_calls"] = sorted({f"{c.library}/{c.function}" for c in calls})
                # Collect typed register annotations from KB
                typed_calls: list[JsonDict] = []
                for c in calls:
                    entry: JsonDict = {"call": f"{c.library}/{c.function}"}
                    if c.inputs:
                        inputs = _typed_call_inputs_payload(c.inputs)
                        if inputs:
                            entry["inputs"] = inputs
                    out = c.output
                    if out and out.type:
                        info = {"type": out.type}
                        if out.i_struct:
                            info["i_struct"] = out.i_struct
                        entry["output"] = {out.reg: info}
                    if "inputs" in entry or "output" in entry:
                        typed_calls.append(entry)
                if typed_calls:
                    ent["os_call_types"] = typed_calls
            if ha.platform.app_base is not None:
                app_slots = collect_subroutine_app_slots(
                    sub,
                    blocks,
                    slot_infos,
                    ha.platform.app_base.reg_num,
                )
                if app_slots:
                    ent["app_slots"] = app_slot_entity_payloads(app_slots)
            sub_indirect_sites = collect_subroutine_indirect_sites(
                sub, indirect_sites)
            if sub_indirect_sites:
                ent["indirect_sites"] = indirect_site_entity_payloads(
                    sub_indirect_sites)
            all_entities.append(ent)

        # -- Hint entities --------------------------------------------
        # Build hint subroutines from hint blocks, annotated with
        # source and reachability info.  These are NOT verified -
        # they drive engine improvements.
        if hint_blocks:
            # Build hint entities from contiguous block regions.
            # Each contiguous group of blocks becomes one hint entity.
            sorted_hints = sorted(hint_blocks.values(),
                                  key=lambda b: b.start)
            regions: list[dict[str, int]] = []
            for blk in sorted_hints:
                if (regions and blk.start <= regions[-1]["end"]):
                    # Extend current region
                    r = regions[-1]
                    r["end"] = max(r["end"], blk.end)
                    r["block_count"] += 1
                    r["instr_count"] += len(blk.instructions)
                else:
                    regions.append({
                        "addr": blk.start, "end": blk.end,
                        "block_count": 1,
                        "instr_count": len(blk.instructions),
                    })
            for region in regions:
                hint_ent: JsonDict = {
                    "addr": fmt_addr(region["addr"]),
                    "end": fmt_addr(region["end"]),
                    "type": "unknown",
                    "confidence": "hint",
                    "hunk": hunk.index,
                    "block_count": region["block_count"],
                    "instr_count": region["instr_count"],
                }
                # Find the best-matching hint reason: any hint entry
                # that falls within this region's address range.
                best_reason = None
                for hint_entry_addr, reason in hint_reasons.items():
                    if (
                        region["addr"] <= hint_entry_addr < region["end"]
                        and (best_reason is None or reason.source == "reloc_from_core")
                    ):
                        best_reason = reason
                if best_reason:
                    hint_ent["hint_source"] = best_reason.source
                    if best_reason.referenced_from:
                        hint_ent["hint_refs"] = sorted(
                            fmt_addr(r)
                            for r in best_reason.referenced_from)
                else:
                    hint_ent["hint_source"] = "scan"
                all_entities.append(hint_ent)

        all_entities.extend(
            _structured_prefix_entities(
                target_metadata,
                hunk.index,
                include_structure=include_structure,
            )
        )

        # Build reloc-derived data references for uncovered regions
        data_refs = build_reloc_references(
            [hunk], code_size, subroutines)
        for ref in data_refs:
            ref_end = ref["addr"] + ref["ptr_size"]
            all_entities.append({
                "addr": fmt_addr(ref["addr"]),
                "end": fmt_addr(ref_end),
                "type": "unknown",
                "confidence": "tool-inferred",
                "hunk": hunk.index,
                "source": "reloc32",
            })

        # Remove reloc entities that overlap with subroutines or each other
        all_entities = _remove_overlapping(all_entities)
        all_entities = _apply_seeded_entities(
            all_entities,
            seeded_entities,
            hunk_idx=hunk.index,
        )
        all_entities = _apply_seeded_code_entrypoints(
            all_entities,
            seeded_code_entrypoints,
            hunk_idx=hunk.index,
        )

        # Fill gaps to cover entire hunk
        gap_ents = fill_gaps(
            [e for e in all_entities
             if e.get("hunk") == hunk.index],
            code_size, hunk.index)
        all_entities.extend(gap_ents)

        hunk_entities = [
            ent for ent in all_entities
            if ent.get("hunk") == hunk.index
        ]
        summarize_entity_app_slots(hunk_entities)

        # Name subroutines from OS calls, string references, call graph
        with phase_timer.phase("entities.naming") if phase_timer is not None else nullcontext():
            named = name_subroutines(
                cast(list[MutableMapping[str, object]], hunk_entities),
                blocks,
                code,
                lib_calls,
            )
        if named:
            print(f"  Named {named} subroutines")

    # Sort by address
    def _addr_int(e: JsonDict) -> int:
        a = e["addr"]
        return int(a, 16) if isinstance(a, str) else a
    all_entities.sort(key=_addr_int)

    # Write output
    with (
        phase_timer.phase("entities.write") if phase_timer is not None else nullcontext(),
        open(output_path, "w") as f,
    ):
        for ent in all_entities:
            f.write(json.dumps(ent, separators=(",", ":")) + "\n")

    print(f"\nWrote {len(all_entities)} entities to {output_path}")

    # Summary
    core_ents = [e for e in all_entities
                 if e.get("confidence") not in ("hint",)]
    hint_ents = [e for e in all_entities
                 if e.get("confidence") == "hint"]
    core_code = [e for e in core_ents if e["type"] == "code"]
    hint_regions = hint_ents

    print("\nSummary:")
    print(f"  Core: {len(core_code)} subroutines, "
          f"{sum(1 for e in core_code if e.get('name'))} named")
    if hint_regions:
        by_src: defaultdict[str, int] = defaultdict(int)
        for e in hint_regions:
            by_src[e.get("hint_source", "-")] += 1
        src_str = ", ".join(f"{c} {s}"
                            for s, c in sorted(by_src.items()))
        print(f"  Hints: {len(hint_regions)} regions ({src_str})")
    gap_count = sum(1 for e in all_entities
                    if e.get("type") == "unknown"
                    and e.get("confidence") != "hint")
    print(f"  Gaps: {gap_count} unmapped regions")

    total_calls = sum(len(e.get("calls", [])) for e in all_entities)
    print(f"  Xrefs: {total_calls} calls")

    return 0


def build_entities(binary_path: str, output_path: str | None = None,
                   base_addr: int = 0, code_start: int = 0) -> int:
    return build_entities_from_source(
        HunkFileBinarySource(
            kind="hunk_file",
            path=Path(binary_path),
            display_path=binary_path,
            analysis_cache_path=Path(binary_path).with_suffix(".analysis"),
        ),
        output_path,
        base_addr=base_addr,
        code_start=code_start,
    )


def _remove_overlapping(entities: list[JsonDict]) -> list[JsonDict]:
    """Remove entities that overlap with earlier ones (sorted by addr)."""
    entities.sort(key=lambda e: int(e["addr"], 16))
    result: list[JsonDict] = []
    for ent in entities:
        addr = int(ent["addr"], 16)
        end = int(ent["end"], 16)
        # Check against all existing
        overlap = False
        for existing in result:
            ex_addr = int(existing["addr"], 16)
            ex_end = int(existing["end"], 16)
            if addr < ex_end and end > ex_addr:
                overlap = True
                break
        if not overlap:
            result.append(ent)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build entities.jsonl from hunk binary analysis")
    parser.add_argument("binary", help="Path to Amiga hunk executable")
    parser.add_argument("--output", "-o",
                        help="Output path (default: <target-dir>/entities.jsonl)")
    parser.add_argument("--target-dir", "-t",
                        help="Target output directory (e.g. targets/amiga_hunk_genam)")
    parser.add_argument("--base-addr", type=lambda x: int(x, 0),
                        default=0,
                        help="Runtime base address (e.g. 0x400)")
    parser.add_argument("--code-start", type=lambda x: int(x, 0),
                        default=0,
                        help="Byte offset where code begins (skips bootstrap)")
    args = parser.parse_args()

    output = args.output
    if output is None and args.target_dir:
        output = str(Path(args.target_dir) / "entities.jsonl")

    return build_entities(args.binary, output,
                          base_addr=args.base_addr,
                          code_start=args.code_start)


if __name__ == "__main__":
    sys.exit(main())

