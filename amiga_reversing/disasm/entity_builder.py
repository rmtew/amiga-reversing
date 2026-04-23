"""Build entities.jsonl from C backend binary analysis.

Entity granularity: subroutine-level for code (not basic-block-level).
Uncovered regions between subroutines are marked as 'unknown'.

"""

import json
import re
from collections import defaultdict
from contextlib import nullcontext
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from amiga_reversing.disasm.binary_source import BinarySource, HunkFileBinarySource
from amiga_reversing.disasm.c_backend import (
    amiga_naming_catalog_with_c_backend,
    amiga_type_catalog_with_c_backend,
    analyze_project_source_with_c_backend,
    api_calls_from_c_analysis,
    effective_policy_project_source_with_c_backend,
)
from amiga_reversing.disasm.phase_timing import PhaseTimer
from amiga_reversing.disasm.target_metadata import (
    SeededCodeEntrypointMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    load_required_target_metadata,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
JsonDict = dict[str, Any]
M68K_OPWORD_BYTES = 2


def _target_seeded_entrypoint_offsets(
    target_metadata: TargetMetadata | None,
    *,
    hunk_index: int = 0,
) -> tuple[int, ...]:
    if target_metadata is None:
        return ()
    return tuple(
        entrypoint.addr
        for entrypoint in target_metadata.seeded_code_entrypoints
        if entrypoint.hunk == hunk_index
    )


@dataclass(frozen=True, slots=True)
class SubroutineRange:
    addr: int
    end: int
    block_count: int
    instr_count: int
    reached: bool = True


@dataclass(frozen=True, slots=True)
class EntityXRef:
    src: int
    dst: int
    type: str


def fmt_addr(addr: int) -> str:
    return f"0x{addr:04X}"


def fmt_disp(offset: int) -> str:
    if offset < 0:
        return f"-0x{abs(offset):04X}"
    return f"0x{offset:04X}"


def _structured_prefix_entities(
    effective_policy: JsonDict | None,
    hunk_idx: int,
    *,
    include_structure: bool,
) -> list[JsonDict]:
    if not include_structure:
        return []
    policy = effective_policy.get("analysis_policy") if effective_policy is not None else None
    if not isinstance(policy, dict):
        return []
    items = [
        item
        for item in policy.get("structured_data_items", [])
        if isinstance(item, dict)
        and isinstance(item.get("offset"), int)
        and isinstance(item.get("size"), int)
        and item.get("size", 0) > 0
        and any(isinstance(item.get(key), str) and item.get(key) for key in ("struct_name", "label", "comment"))
        and (item.get("section_index") == hunk_idx or (item.get("section_index") is None and hunk_idx == 0))
    ]
    items.sort(key=lambda item: (cast(int, item["offset"]), str(item.get("struct_name") or "")))
    regions: list[tuple[int, int, str | None]] = []
    for item in items:
        start = cast(int, item["offset"])
        end = start + cast(int, item["size"])
        struct_name = cast(str | None, item.get("struct_name")) or None
        if regions and regions[-1][2] == struct_name and start <= regions[-1][1]:
            prev_start, prev_end, prev_struct = regions[-1]
            regions[-1] = (prev_start, max(prev_end, end), prev_struct)
        else:
            regions.append((start, end, struct_name))
    entities: list[JsonDict] = []
    for start, end, struct_name in regions:
        payload: JsonDict = {
            "addr": fmt_addr(start),
            "end": fmt_addr(end),
            "type": "data",
            "subtype": "struct_instance",
            "confidence": "tool-inferred",
            "hunk": hunk_idx,
        }
        if struct_name is not None:
            payload["struct"] = struct_name
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


def assign_xrefs(subroutines: list[SubroutineRange], xrefs: list[EntityXRef],
                 ) -> tuple[dict[int, dict[str, set[int]]], dict[int, dict[str, set[int]]]]:
    """Map instruction-level xrefs to subroutine-level entity xrefs.

    Returns (forward_map, reverse_map) where each maps entity addr to
    {field: set(segment_addrs)}.
    Prints count of xrefs dropped due to unmapped src/dst addresses.
    """
    sorted_subs = sorted(subroutines, key=lambda s: s.addr)
    forward: dict[int, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    reverse: dict[int, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    dropped = 0

    for xref in xrefs:
        if xref.type == "fallthrough":
            continue  # internal control flow

        src_sub = _find_subroutine_for_offset(sorted_subs, xref.src)
        dst_sub = _find_subroutine_for_offset(sorted_subs, xref.dst)

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


def _os_input_reg_key(regs: tuple[str, ...]) -> str:
    if not regs:
        raise ValueError("OS input must have at least one register")
    return "/".join(regs)


def _slot_struct_refs(slot: JsonDict) -> set[str]:
    refs: set[str] = set()
    struct_name = slot.get("struct")
    if struct_name is not None:
        refs.add(cast(str, struct_name))
    pointer_struct = slot.get("pointer_struct")
    if pointer_struct is not None:
        refs.add(cast(str, pointer_struct))
    return refs


def _library_struct_ref(library_name: str) -> str | None:
    return _c_named_base_structs().get(library_name)


def _indirect_site_libraries(ent: JsonDict) -> set[str]:
    return {
        cast(str, site["library"])
        for site in ent.get("indirect_sites", ())
        if isinstance(site, dict) and isinstance(site.get("library"), str)
    }


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
        direct_named_bases.update(_indirect_site_libraries(ent))
        direct_struct_refs: set[str] = set()
        for slot in ent.get("app_slots", ()):
            direct_struct_refs.update(_slot_struct_refs(slot))
        for library_name in _indirect_site_libraries(ent):
            struct_name = _library_struct_ref(library_name)
            if struct_name is not None:
                direct_struct_refs.add(struct_name)
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


_C_SECTION_CODE = 1
_C_SECTION_DATA = 2
_C_SECTION_BSS = 3
_C_EDGE_FALLTHROUGH = 1
_C_EDGE_BRANCH = 2
_C_EDGE_CALL = 3
_C_EDGE_JUMP = 4
_C_EFFECT_SET_BASE_REG = 1
_C_EFFECT_WRITE_BASE_SLOT = 2
_C_EFFECT_SET_CODE_PTR_REG = 3
_C_EFFECT_SET_TYPED_REG = 4
_C_EFFECT_WRITE_TYPED_SLOT = 5
_C_PLATFORM_CALL_INDEXED_LIBRARY_DISPATCH = 2
_C_PLATFORM_CALL_CALLBACK_FIELD = 3
_C_CALL_NOTE_INDEXED_VECTOR = 1
_C_CALL_NOTE_CALLBACK_FIELD = 2
_C_CALL_NOTE_LOCAL_WRAPPER_SYMBOL = 3
_C_INT16_NONE = -32768


def _json_int(payload: JsonDict, key: str, default: int = 0) -> int:
    value = payload.get(key)
    return value if isinstance(value, int) else default


def _json_str(payload: JsonDict, key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value != "" else None


def _c_sections(analysis: JsonDict) -> list[JsonDict]:
    sections = analysis.get("sections")
    return cast(list[JsonDict], sections if isinstance(sections, list) else [])


def _c_section_blocks(section: JsonDict) -> list[JsonDict]:
    blocks = section.get("blocks")
    return cast(list[JsonDict], blocks if isinstance(blocks, list) else [])


def _c_section_edges(section: JsonDict) -> list[JsonDict]:
    edges = section.get("edges")
    return cast(list[JsonDict], edges if isinstance(edges, list) else [])


def _c_section_effects(section: JsonDict) -> list[JsonDict]:
    effects = section.get("recovered_platform_effects")
    return cast(list[JsonDict], effects if isinstance(effects, list) else [])


def _c_section_platform_calls(section: JsonDict) -> list[JsonDict]:
    calls = section.get("recovered_platform_calls")
    return cast(list[JsonDict], calls if isinstance(calls, list) else [])


def _c_section_indirect_sites(section: JsonDict) -> list[JsonDict]:
    sites = section.get("recovered_indirect_sites")
    return cast(list[JsonDict], sites if isinstance(sites, list) else [])


def _c_section_string_refs(section: JsonDict) -> list[JsonDict]:
    refs = section.get("recovered_string_refs")
    return cast(list[JsonDict], refs if isinstance(refs, list) else [])


def _c_section_entity_hints(section: JsonDict) -> list[JsonDict]:
    hints = section.get("entity_hints")
    return cast(list[JsonDict], hints if isinstance(hints, list) else [])


def _c_section_type(section_kind: int) -> str:
    if section_kind == _C_SECTION_DATA:
        return "data"
    if section_kind == _C_SECTION_BSS:
        return "bss"
    return "unknown"


def _c_call_targets(section: JsonDict) -> set[int]:
    return {
        _json_int(edge, "target_offset")
        for edge in _c_section_edges(section)
        if _json_int(edge, "kind") == _C_EDGE_CALL
    }


def _effective_policy_entries(effective_policy: JsonDict | None, section_index: int) -> set[int]:
    if effective_policy is None:
        return set()
    policy = effective_policy.get("analysis_policy")
    if not isinstance(policy, dict):
        return set()
    entries: set[int] = set()
    for entry in policy.get("entrypoints", []):
        if not isinstance(entry, dict):
            continue
        entry_section = entry.get("section_index")
        offset = entry.get("offset")
        if (entry_section is None or entry_section == section_index) and isinstance(offset, int):
            entries.add(offset)
    for seed in policy.get("register_seeds", []):
        if not isinstance(seed, dict):
            continue
        seed_section = seed.get("section_index")
        offset = seed.get("entry_offset")
        if (seed_section is None or seed_section == section_index) and isinstance(offset, int):
            entries.add(offset)
    return entries


def _effective_policy_names(effective_policy: JsonDict | None, section_index: int) -> dict[int, str]:
    if effective_policy is None:
        return {}
    policy = effective_policy.get("analysis_policy")
    if not isinstance(policy, dict):
        return {}
    names: dict[int, str] = {}
    for label in policy.get("named_labels", []):
        if not isinstance(label, dict):
            continue
        label_section = label.get("section_index")
        offset = label.get("offset")
        name = label.get("name")
        if (label_section is None or label_section == section_index) and isinstance(offset, int) and isinstance(name, str):
            names[offset] = name
    return names


def _effective_policy_has_explicit_section(effective_policy: JsonDict | None, section_index: int) -> bool:
    if effective_policy is None:
        return False
    policy = effective_policy.get("analysis_policy")
    if not isinstance(policy, dict):
        return False
    for key in ("entrypoints", "register_seeds", "structured_data_items", "named_labels", "entry_comments"):
        for item in policy.get(key, []):
            if isinstance(item, dict) and item.get("section_index") == section_index:
                return True
    return False


def _c_section_entry_points(
    binary_source: BinarySource,
    target_metadata: TargetMetadata | None,
    section_index: int,
    *,
    include_structure: bool,
    blocks: list[JsonDict],
    effective_policy: JsonDict | None = None,
) -> set[int]:
    entry_points: set[int] = set()
    if binary_source.kind == "raw_binary":
        entry_points.add(binary_source.local_entrypoint)
    elif include_structure:
        entry_points.update(_effective_policy_entries(effective_policy, section_index))
    entry_points.update(_target_seeded_entrypoint_offsets(target_metadata, hunk_index=section_index))
    if not entry_points and blocks:
        entry_points.add(_json_int(blocks[0], "start_offset"))
    return entry_points


def _find_c_block_index_containing(blocks: list[JsonDict], offset: int) -> int | None:
    for index, block in enumerate(blocks):
        if _json_int(block, "start_offset") <= offset < _json_int(block, "end_offset"):
            return index
    return None


def _build_c_subroutine_map(section: JsonDict, entry_points: set[int]) -> list[SubroutineRange]:
    blocks = _c_section_blocks(section)
    edges = _c_section_edges(section)
    call_targets = _c_call_targets(section)
    entries = set(entry_points) | call_targets
    if not entries and blocks:
        entries.add(_json_int(blocks[0], "start_offset"))

    edges_by_source: defaultdict[int, list[JsonDict]] = defaultdict(list)
    for edge in edges:
        source_index = _json_int(edge, "source_block_index", -1)
        if 0 <= source_index < len(blocks):
            edges_by_source[source_index].append(edge)

    owner_by_block: dict[int, int] = {}
    block_index_by_start = {
        _json_int(block, "start_offset"): index
        for index, block in enumerate(blocks)
    }

    def claim_from_entry(entry: int, start_index: int | None = None) -> None:
        if start_index is None:
            start_index = block_index_by_start.get(entry)
        if start_index is None:
            start_index = _find_c_block_index_containing(blocks, entry)
        if start_index is None:
            return
        work = [start_index]
        visited: set[int] = set()
        while work:
            block_index = work.pop()
            if block_index in visited:
                continue
            block = blocks[block_index]
            block_start = _json_int(block, "start_offset")
            if block_start != entry and block_start in entries:
                continue
            if block_index in owner_by_block:
                continue
            visited.add(block_index)
            owner_by_block[block_index] = entry
            for edge in edges_by_source.get(block_index, ()):
                kind = _json_int(edge, "kind")
                if kind not in (_C_EDGE_FALLTHROUGH, _C_EDGE_BRANCH, _C_EDGE_JUMP):
                    continue
                target_index = _json_int(edge, "target_block_index", -1)
                if 0 <= target_index < len(blocks):
                    work.append(target_index)

    for entry in sorted(entries):
        claim_from_entry(entry)

    for block_index, block in enumerate(blocks):
        if block_index in owner_by_block:
            continue
        entry = _json_int(block, "start_offset")
        entries.add(entry)
        claim_from_entry(entry, block_index)

    grouped: defaultdict[int, list[JsonDict]] = defaultdict(list)
    for block_index, owner in owner_by_block.items():
        grouped[owner].append(blocks[block_index])

    subroutines: list[SubroutineRange] = []
    for entry in sorted(entries):
        owned = grouped.get(entry)
        if owned:
            subroutines.append(
                SubroutineRange(
                    addr=min(_json_int(block, "start_offset") for block in owned),
                    end=max(_json_int(block, "end_offset") for block in owned),
                    block_count=len(owned),
                    instr_count=0,
                )
            )
        else:
            subroutines.append(
                SubroutineRange(
                    addr=entry,
                    end=entry + M68K_OPWORD_BYTES,
                    block_count=0,
                    instr_count=0,
                    reached=False,
                )
            )

    subroutines.sort(key=lambda sub: sub.addr)
    for index in range(len(subroutines) - 1):
        if subroutines[index].end > subroutines[index + 1].addr:
            subroutines[index] = SubroutineRange(
                addr=subroutines[index].addr,
                end=subroutines[index + 1].addr,
                block_count=subroutines[index].block_count,
                instr_count=subroutines[index].instr_count,
                reached=subroutines[index].reached,
            )

    def range_overlaps_existing(start: int, end: int) -> bool:
        return any(start < sub.end and end > sub.addr for sub in subroutines)

    uncovered_ranges: list[SubroutineRange] = []
    current_start: int | None = None
    current_end = 0
    current_count = 0
    for block in sorted(blocks, key=lambda item: _json_int(item, "start_offset")):
        block_start = _json_int(block, "start_offset")
        block_end = _json_int(block, "end_offset")
        if range_overlaps_existing(block_start, block_end):
            continue
        if current_start is not None and block_start == current_end:
            current_end = block_end
            current_count += 1
            continue
        if current_start is not None:
            uncovered_ranges.append(
                SubroutineRange(
                    addr=current_start,
                    end=current_end,
                    block_count=current_count,
                    instr_count=0,
                )
            )
        current_start = block_start
        current_end = block_end
        current_count = 1
    if current_start is not None:
        uncovered_ranges.append(
            SubroutineRange(
                addr=current_start,
                end=current_end,
                block_count=current_count,
                instr_count=0,
            )
        )
    if uncovered_ranges:
        subroutines.extend(uncovered_ranges)
        subroutines.sort(key=lambda sub: sub.addr)
    return subroutines


def _c_xrefs(section: JsonDict) -> list[EntityXRef]:
    kind_names = {
        _C_EDGE_BRANCH: "branch",
        _C_EDGE_CALL: "call",
        _C_EDGE_JUMP: "jump",
    }
    refs: list[EntityXRef] = []
    for edge in _c_section_edges(section):
        kind_name = kind_names.get(_json_int(edge, "kind"))
        if kind_name is None:
            continue
        refs.append(
            EntityXRef(
                src=_json_int(edge, "source_offset"),
                dst=_json_int(edge, "target_offset"),
                type=kind_name,
            )
        )
    return refs


def _c_api_call_type_payload(call_name: str, call: JsonDict) -> JsonDict | None:
    entry: JsonDict = {"call": call_name}
    typed_inputs: JsonDict = {}
    inputs = call.get("inputs")
    if isinstance(inputs, list):
        for raw_input in inputs:
            if not isinstance(raw_input, dict):
                continue
            input_type = raw_input.get("type")
            regs = raw_input.get("regs")
            if not isinstance(input_type, str) or not isinstance(regs, list):
                continue
            reg_tuple = tuple(reg for reg in regs if isinstance(reg, str))
            if not reg_tuple:
                continue
            reg_key = _os_input_reg_key(reg_tuple)
            info: JsonDict = {"type": input_type}
            for field in ("i_struct", "semantic_kind", "value_domain"):
                value = raw_input.get(field)
                if isinstance(value, str):
                    info[field] = value
            typed_inputs[reg_key] = info
    if typed_inputs:
        entry["inputs"] = typed_inputs
    return entry if "inputs" in entry else None


def _c_api_calls_by_section(analysis: JsonDict) -> dict[int, list[tuple[int, JsonDict]]]:
    calls_by_section: defaultdict[int, list[tuple[int, JsonDict]]] = defaultdict(list)
    for (section_index, offset), call in api_calls_from_c_analysis(analysis).items():
        calls_by_section[section_index].append((offset, cast(JsonDict, call)))
    return calls_by_section


def _find_subroutine_for_offset(subroutines: list[SubroutineRange], offset: int) -> int | None:
    lo = 0
    hi = len(subroutines) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        sub = subroutines[mid]
        if offset < sub.addr:
            hi = mid - 1
        elif offset >= sub.end:
            lo = mid + 1
        else:
            return sub.addr
    return None


@lru_cache(maxsize=1)
def _c_type_catalog() -> tuple[JsonDict, ...]:
    return tuple(cast(JsonDict, item) for item in amiga_type_catalog_with_c_backend(project_root=PROJECT_ROOT))


@lru_cache(maxsize=1)
def _c_struct_sizes() -> dict[str, int]:
    result: dict[str, int] = {}
    for item in _c_type_catalog():
        name = item.get("name")
        size = item.get("size")
        if isinstance(name, str) and isinstance(size, int):
            result[name] = size
    return result


@lru_cache(maxsize=1)
def _c_named_base_structs() -> dict[str, str]:
    result: dict[str, str] = {}
    for item in _c_type_catalog():
        name = item.get("name")
        named_base = item.get("named_base")
        if isinstance(name, str) and isinstance(named_base, str):
            result[named_base] = name
    return result


@lru_cache(maxsize=1)
def _c_naming_catalog() -> dict[str, object]:
    return amiga_naming_catalog_with_c_backend(project_root=PROJECT_ROOT)


def _c_known_library_names() -> set[str]:
    libraries = _c_naming_catalog().get("libraries")
    if not isinstance(libraries, list):
        return set()
    return {library for library in libraries if isinstance(library, str)}


def _c_struct_size(type_name: str) -> int | None:
    return _c_struct_sizes().get(type_name)


def _c_app_slot_symbol(effect: JsonDict, displacement: int) -> str:
    for key in ("symbol_name", "base_name", "type_name"):
        value = _json_str(effect, key)
        if value is not None and value.startswith("app_"):
            return value
    return f"app_{displacement & 0xFFFF:04X}"


def _c_effect_app_slot_payload(effect: JsonDict) -> JsonDict | None:
    kind = _json_int(effect, "kind")
    displacement = _json_int(effect, "displacement", _C_INT16_NONE)
    if displacement == _C_INT16_NONE:
        return None
    if kind not in (_C_EFFECT_WRITE_BASE_SLOT, _C_EFFECT_SET_CODE_PTR_REG, _C_EFFECT_WRITE_TYPED_SLOT):
        return None
    payload: JsonDict = {
        "offset": fmt_disp(displacement),
        "symbol": _c_app_slot_symbol(effect, displacement),
    }
    base_name = _json_str(effect, "base_name")
    if base_name is not None:
        payload["named_base"] = base_name
    semantic_kind = _json_str(effect, "semantic_kind")
    if semantic_kind is not None:
        payload["semantic_type"] = semantic_kind
    value_domain = _json_str(effect, "value_domain_name")
    if value_domain is not None:
        payload["value_domain"] = value_domain
    if _json_int(effect, "has_constant_value") != 0:
        payload["constant_value"] = _json_int(effect, "constant_value")

    type_name = _json_str(effect, "type_name")
    if kind == _C_EFFECT_WRITE_TYPED_SLOT and type_name is not None:
        struct_size = _c_struct_size(type_name)
        if struct_size is not None:
            payload["kind"] = "struct_instance"
            payload["struct"] = type_name
            payload["size"] = struct_size
        else:
            payload["storage_kind"] = "scalar"
            payload["value_type"] = type_name
    elif kind == _C_EFFECT_WRITE_TYPED_SLOT:
        payload["storage_kind"] = "scalar"
    elif kind == _C_EFFECT_SET_CODE_PTR_REG:
        payload["kind"] = "code_pointer"
        if type_name is not None:
            payload["owner_type"] = type_name
        field_disp = _json_int(effect, "field_disp", _C_INT16_NONE)
        if field_disp != _C_INT16_NONE:
            payload["field_offset"] = fmt_disp(field_disp)
    return payload


def _dedupe_payloads(payloads: list[JsonDict]) -> list[JsonDict]:
    seen: set[str] = set()
    result: list[JsonDict] = []
    for payload in payloads:
        key = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        result.append(payload)
    return result


def _c_app_slots_by_subroutine(
    section: JsonDict,
    subroutines: list[SubroutineRange],
) -> dict[int, list[JsonDict]]:
    slots_by_sub: defaultdict[int, list[JsonDict]] = defaultdict(list)
    for effect in _c_section_effects(section):
        payload = _c_effect_app_slot_payload(effect)
        if payload is None:
            continue
        sub_addr = _find_subroutine_for_offset(subroutines, _json_int(effect, "offset"))
        if sub_addr is None:
            continue
        slots_by_sub[sub_addr].append(payload)
    return {
        sub_addr: _dedupe_payloads(sorted(payloads, key=lambda item: cast(str, item["offset"])))
        for sub_addr, payloads in slots_by_sub.items()
    }


def _c_entity_hint_payloads_by_subroutine(
    section: JsonDict,
    subroutines: list[SubroutineRange],
    hint_kind: str,
    payload_key: str,
) -> dict[int, list[JsonDict]]:
    payloads_by_sub: defaultdict[int, list[JsonDict]] = defaultdict(list)
    for hint in _c_section_entity_hints(section):
        if _json_str(hint, "hint_kind") != hint_kind:
            continue
        payload = hint.get(payload_key)
        if not isinstance(payload, dict):
            continue
        sub_addr = _find_subroutine_for_offset(subroutines, _json_int(hint, "offset"))
        if sub_addr is None:
            continue
        payloads_by_sub[sub_addr].append(cast(JsonDict, payload))
    return {
        sub_addr: _dedupe_payloads(sorted(payloads, key=lambda item: json.dumps(item, sort_keys=True)))
        for sub_addr, payloads in payloads_by_sub.items()
    }


def _c_indirect_site_payload(call: JsonDict) -> JsonDict | None:
    kind = _json_int(call, "kind")
    note_kind = _json_int(call, "note_kind")
    if kind == _C_PLATFORM_CALL_CALLBACK_FIELD or note_kind == _C_CALL_NOTE_CALLBACK_FIELD:
        shape = "callback_field"
        status = "per_caller"
    elif kind == _C_PLATFORM_CALL_INDEXED_LIBRARY_DISPATCH and note_kind == _C_CALL_NOTE_LOCAL_WRAPPER_SYMBOL:
        shape = "local_wrapper_dispatch"
        status = "external"
    elif kind == _C_PLATFORM_CALL_INDEXED_LIBRARY_DISPATCH and note_kind == _C_CALL_NOTE_INDEXED_VECTOR:
        shape = "indexed_library_dispatch"
        status = "per_caller"
    else:
        return None

    payload: JsonDict = {
        "addr": fmt_addr(_json_int(call, "offset")),
        "shape": shape,
        "status": status,
        "flow": "call",
    }
    base_name = _json_str(call, "note_base_name")
    symbol_name = (
        _json_str(call, "note_symbol_name")
        or _json_str(call, "lvo_symbol_name")
        or _json_str(call, "function_name")
        or _json_str(call, "symbol_name")
    )
    if base_name is not None and symbol_name is not None:
        payload["detail"] = f"{base_name}.{symbol_name}" if shape == "callback_field" else f"{base_name}/{symbol_name}"
    elif base_name is not None:
        payload["detail"] = base_name
    elif symbol_name is not None:
        payload["detail"] = symbol_name

    library_name = _json_str(call, "library_name")
    if library_name is not None:
        payload["library"] = library_name

    note_disp = _json_int(call, "note_disp", _C_INT16_NONE)
    if note_disp != _C_INT16_NONE:
        payload["base_offset"] = fmt_disp(note_disp)
    note_field_disp = _json_int(call, "note_field_disp", _C_INT16_NONE)
    if note_field_disp != _C_INT16_NONE:
        payload["field_offset"] = fmt_disp(note_field_disp)
    return payload


def _c_generic_indirect_site_payload(site: JsonDict) -> JsonDict | None:
    shape = _json_str(site, "shape")
    status = _json_str(site, "status")
    flow = _json_str(site, "flow")
    if shape is None or status is None or flow is None:
        return None
    payload: JsonDict = {
        "addr": fmt_addr(_json_int(site, "offset")),
        "shape": shape,
        "status": status,
        "flow": flow,
    }
    detail = _json_str(site, "detail")
    if detail is not None:
        payload["detail"] = detail
    target_count = site.get("target_count")
    if isinstance(target_count, int):
        payload["target_count"] = target_count
    return payload


def _c_indirect_sites_by_subroutine(
    section: JsonDict,
    subroutines: list[SubroutineRange],
    *,
    include_platform_calls: bool = True,
) -> dict[int, list[JsonDict]]:
    sites_by_sub: defaultdict[int, list[JsonDict]] = defaultdict(list)
    for site in _c_section_indirect_sites(section):
        payload = _c_generic_indirect_site_payload(site)
        if payload is None:
            continue
        sub_addr = _find_subroutine_for_offset(subroutines, _json_int(site, "offset"))
        if sub_addr is None:
            continue
        sites_by_sub[sub_addr].append(payload)
    if include_platform_calls:
        for call in _c_section_platform_calls(section):
            payload = _c_indirect_site_payload(call)
            if payload is None:
                continue
            sub_addr = _find_subroutine_for_offset(subroutines, _json_int(call, "offset"))
            if sub_addr is None:
                continue
            sites_by_sub[sub_addr].append(payload)
    return {
        sub_addr: _dedupe_payloads(sorted(payloads, key=lambda item: cast(str, item["addr"])))
        for sub_addr, payloads in sites_by_sub.items()
    }


def _c_string_refs_by_subroutine(
    section: JsonDict,
    subroutines: list[SubroutineRange],
) -> dict[int, list[JsonDict]]:
    refs_by_sub: defaultdict[int, list[JsonDict]] = defaultdict(list)
    for ref in _c_section_string_refs(section):
        text = _json_str(ref, "text")
        if text is None:
            continue
        sub_addr = _find_subroutine_for_offset(subroutines, _json_int(ref, "offset"))
        if sub_addr is None:
            continue
        refs_by_sub[sub_addr].append({
            "addr": fmt_addr(_json_int(ref, "offset")),
            "target": fmt_addr(_json_int(ref, "target")),
            "text": text,
        })
    return {
        sub_addr: _dedupe_payloads(sorted(payloads, key=lambda item: cast(str, item["addr"])))
        for sub_addr, payloads in refs_by_sub.items()
    }


def _c_os_calls_to_name(os_calls: list[str]) -> str | None:
    if not os_calls:
        return None
    catalog = _c_naming_catalog()
    funcs: set[str] = set()
    for call in os_calls:
        parts = call.split("/")
        if len(parts) == 2 and parts[1]:
            funcs.add(parts[1])
    for pattern in cast(list[dict[str, object]], catalog.get("patterns", [])):
        raw_functions = pattern.get("functions")
        if not isinstance(raw_functions, list):
            continue
        required = {function for function in raw_functions if isinstance(function, str)}
        if pattern.get("partial"):
            if required & funcs:
                name = pattern.get("name")
                return name if isinstance(name, str) else None
        elif required <= funcs and (len(required) > 1 or funcs == required):
            name = pattern.get("name")
            return name if isinstance(name, str) else None
    raw_trivial = catalog.get("trivial_functions")
    trivial = {function for function in raw_trivial if isinstance(function, str)} if isinstance(raw_trivial, list) else set()
    distinctive = funcs - trivial
    if distinctive:
        generic_prefix = catalog.get("generic_prefix")
        return (generic_prefix if isinstance(generic_prefix, str) else "") + re.sub(
            r"[^a-z0-9]+", "_", sorted(distinctive)[0].lower()
        ).strip("_")
    return None


def _dispatch_name_from_base(named_base: str) -> str:
    base = named_base.rsplit(".", 1)[0]
    return re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_") + "_dispatch"


def _string_to_name(text: str) -> str:
    text = text.strip()
    if text in _c_known_library_names():
        base = text.rsplit(".", 1)[0]
        return "open_" + re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_")
    name = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    if len(name) > 40:
        name = name[:40].rstrip("_")
    return name


def _c_string_ref_name(entity: JsonDict) -> str | None:
    refs = entity.get("string_refs")
    if not isinstance(refs, list):
        return None
    strings = [
        text
        for ref in refs
        for text in (ref.get("text") if isinstance(ref, dict) else None,)
        if isinstance(text, str)
    ]
    good = [
        text
        for text in strings
        if len(text) >= 6 and (" " in text or "." in text or "_" in text or text[0].isupper())
    ]
    if not good:
        return None
    return _string_to_name(max(good, key=len))


def _c_dispatch_name(entity: JsonDict) -> str | None:
    named_bases = entity.get("named_bases")
    if not isinstance(named_bases, list) or len(named_bases) != 1:
        return None
    named_base = named_bases[0]
    if not isinstance(named_base, str):
        return None
    indirect_sites = entity.get("indirect_sites")
    if not isinstance(indirect_sites, list):
        return None
    if not any(isinstance(site, dict) and site.get("flow") == "call" for site in indirect_sites):
        return None
    return _dispatch_name_from_base(named_base)


def _apply_structured_entrypoint_names(
    entities: list[JsonDict],
    target_metadata: TargetMetadata | None,
    *,
    hunk_idx: int,
    include_structure: bool,
    effective_policy: JsonDict | None = None,
) -> list[JsonDict]:
    if not include_structure:
        return list(entities)
    names_by_addr = _effective_policy_names(effective_policy, hunk_idx)
    if not names_by_addr:
        return list(entities)
    merged: list[JsonDict] = []
    for entity in entities:
        next_entity = dict(entity)
        if next_entity.get("type") == "code" and next_entity.get("hunk") == hunk_idx:
            name = names_by_addr.get(int(cast(str, next_entity["addr"]), 16))
            if name is not None and "name" not in next_entity:
                next_entity["name"] = name
                next_entity["status"] = "named"
        merged.append(next_entity)
    return merged


def _name_c_hunk_entities(entities: list[JsonDict]) -> int:
    used_names = {
        cast(str, entity["name"])
        for entity in entities
        if isinstance(entity.get("name"), str)
    }
    named = 0
    for entity in sorted(
        (item for item in entities if item.get("type") == "code"),
        key=lambda item: int(cast(str, item["addr"]), 16),
    ):
        if isinstance(entity.get("name"), str):
            continue
        name = None
        raw_os_calls = entity.get("os_calls")
        if isinstance(raw_os_calls, list):
            name = _c_os_calls_to_name([call for call in raw_os_calls if isinstance(call, str)])
        if name is None:
            name = _c_dispatch_name(entity)
        if name is None:
            name = _c_string_ref_name(entity)
        if name is None and int(cast(str, entity["addr"]), 16) == 0:
            name = "entry_point"
        if name is None:
            continue
        final_name = name
        if final_name in used_names:
            final_name = f"{name}_{int(cast(str, entity['addr']), 16):04x}"
        entity["name"] = final_name
        entity["status"] = "named"
        used_names.add(final_name)
        named += 1
    return named


def _build_entities_from_c_analysis(
    binary_source: BinarySource,
    analysis: JsonDict,
    output_path: str,
    target_metadata: TargetMetadata | None,
    seeded_entities: tuple[SeededEntityMetadata, ...],
    seeded_code_entrypoints: tuple[SeededCodeEntrypointMetadata, ...],
    phase_timer: PhaseTimer | None,
    effective_policy: JsonDict | None = None,
) -> int:
    all_entities: list[JsonDict] = []
    api_calls_by_section = _c_api_calls_by_section(analysis)
    first_code_section_seen = False

    sections = _c_sections(analysis)
    print(f"  {len(sections)} sections")
    for section in sections:
        section_index = _json_int(section, "section_index")
        section_kind = _json_int(section, "section_kind")
        section_size = _json_int(section, "section_size")
        if section_kind != _C_SECTION_CODE:
            all_entities.append({
                "addr": fmt_addr(0),
                "end": fmt_addr(section_size),
                "type": _c_section_type(section_kind),
                "confidence": "tool-inferred",
                "hunk": section_index,
            })
            continue

        include_structure = not first_code_section_seen or _effective_policy_has_explicit_section(
            effective_policy, section_index
        )
        first_code_section_seen = True
        blocks = _c_section_blocks(section)
        print(f"\nAnalyzing section #{section_index} ({section_size} bytes)...")
        entry_points = _c_section_entry_points(
            binary_source,
            target_metadata,
            section_index,
            include_structure=include_structure,
            blocks=blocks,
            effective_policy=effective_policy,
        )
        subroutines = _build_c_subroutine_map(section, entry_points)
        stubs = sum(1 for sub in subroutines if not sub.reached)
        print(f"  {len(subroutines)} subroutines ({stubs} stubs - unreached)")
        fwd_xrefs, rev_xrefs = assign_xrefs(subroutines, _c_xrefs(section))
        c_entity_hints = _c_section_entity_hints(section)
        app_slots_by_sub = (
            _c_entity_hint_payloads_by_subroutine(section, subroutines, "app_slot", "app_slot")
            if c_entity_hints
            else _c_app_slots_by_subroutine(section, subroutines)
        )
        indirect_sites_by_sub = _c_indirect_sites_by_subroutine(
            section,
            subroutines,
            include_platform_calls=not c_entity_hints,
        )
        if c_entity_hints:
            hinted_indirect_sites = _c_entity_hint_payloads_by_subroutine(
                section,
                subroutines,
                "indirect_site",
                "indirect_site",
            )
            for sub_addr, payloads in hinted_indirect_sites.items():
                indirect_sites_by_sub[sub_addr] = _dedupe_payloads(
                    sorted(indirect_sites_by_sub.get(sub_addr, []) + payloads, key=lambda item: cast(str, item["addr"]))
                )
        string_refs_by_sub = _c_string_refs_by_subroutine(section, subroutines)

        lib_call_map: defaultdict[int, list[tuple[int, JsonDict]]] = defaultdict(list)
        for call_offset, call in api_calls_by_section.get(section_index, ()):
            call_sub_addr = _find_subroutine_for_offset(subroutines, call_offset)
            if call_sub_addr is not None:
                lib_call_map[call_sub_addr].append((call_offset, call))

        hunk_entities: list[JsonDict] = []
        for sub in subroutines:
            ent: JsonDict = {
                "addr": fmt_addr(sub.addr),
                "end": fmt_addr(sub.end),
                "type": "code",
                "confidence": "tool-inferred",
                "hunk": section_index,
                "block_count": sub.block_count,
                "instr_count": sub.instr_count,
            }
            if not sub.reached:
                ent["stub"] = True
            if sub.addr in fwd_xrefs:
                for field, targets in fwd_xrefs[sub.addr].items():
                    ent[field] = sorted(fmt_addr(target) for target in targets)
            if sub.addr in rev_xrefs:
                for field, sources in rev_xrefs[sub.addr].items():
                    ent[field] = sorted(fmt_addr(source) for source in sources)
            if sub.addr in lib_call_map:
                calls = lib_call_map[sub.addr]
                call_names = sorted({
                    f"{call.get('library', 'unknown')}/{call.get('function', 'unknown')}"
                    for _, call in calls
                })
                ent["os_calls"] = call_names
                typed_calls = [
                    typed
                    for _, call in calls
                    for typed in (
                        _c_api_call_type_payload(
                            f"{call.get('library', 'unknown')}/{call.get('function', 'unknown')}",
                            call,
                        ),
                    )
                    if typed is not None
                ]
                if typed_calls:
                    ent["os_call_types"] = _dedupe_payloads(typed_calls)
            if sub.addr in app_slots_by_sub:
                ent["app_slots"] = app_slots_by_sub[sub.addr]
            if sub.addr in indirect_sites_by_sub:
                ent["indirect_sites"] = indirect_sites_by_sub[sub.addr]
            if sub.addr in string_refs_by_sub:
                ent["string_refs"] = string_refs_by_sub[sub.addr]
            hunk_entities.append(ent)

        hunk_entities.extend(
            _structured_prefix_entities(
                effective_policy,
                section_index,
                include_structure=include_structure,
            )
        )
        hunk_entities = _apply_structured_entrypoint_names(
            hunk_entities,
            target_metadata,
            hunk_idx=section_index,
            include_structure=include_structure,
            effective_policy=effective_policy,
        )
        hunk_entities = _remove_overlapping(hunk_entities)
        hunk_entities = _apply_seeded_entities(
            hunk_entities,
            seeded_entities,
            hunk_idx=section_index,
        )
        hunk_entities = _apply_seeded_code_entrypoints(
            hunk_entities,
            seeded_code_entrypoints,
            hunk_idx=section_index,
        )
        hunk_entities.extend(fill_gaps(hunk_entities, section_size, section_index))
        summarize_entity_app_slots(hunk_entities)
        named = _name_c_hunk_entities(hunk_entities)
        if named:
            print(f"  Named {named} subroutines")
        all_entities.extend(hunk_entities)

    all_entities.sort(key=lambda ent: int(cast(str, ent["addr"]), 16))
    with (
        phase_timer.phase("entities.write") if phase_timer is not None else nullcontext(),
        open(output_path, "w") as f,
    ):
        for ent in all_entities:
            f.write(json.dumps(ent, separators=(",", ":")) + "\n")

    print(f"\nWrote {len(all_entities)} entities to {output_path}")
    core_code = [ent for ent in all_entities if ent.get("type") == "code"]
    gap_count = sum(1 for ent in all_entities if ent.get("type") == "unknown")
    total_calls = sum(len(ent.get("calls", [])) for ent in all_entities)
    print("\nSummary:")
    print(f"  Core: {len(core_code)} subroutines, {sum(1 for ent in core_code if ent.get('name'))} named")
    print(f"  Gaps: {gap_count} unmapped regions")
    print(f"  Xrefs: {total_calls} calls")
    return 0


def build_entities_from_source(binary_source: BinarySource, output_path: str | None = None,
                               base_addr: int = 0, code_start: int = 0,
                               phase_timer: PhaseTimer | None = None) -> int:
    if output_path is None:
        output_path = "entities.jsonl"

    print(f"Parsing {binary_source.display_path}...")
    output_target_dir = Path(output_path).parent if output_path is not None else None
    target_metadata = load_required_target_metadata(
        target_dir=output_target_dir,
        source_kind=binary_source.kind,
        parent_disk_id=binary_source.parent_disk_id,
    )
    seeded_entities = () if target_metadata is None else target_metadata.seeded_entities
    seeded_code_entrypoints = () if target_metadata is None else target_metadata.seeded_code_entrypoints
    metadata_path = None if output_target_dir is None else output_target_dir / "target_metadata.json"
    with phase_timer.phase("entities.effective_policy") if phase_timer is not None else nullcontext():
        effective_policy = effective_policy_project_source_with_c_backend(
            binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
        )
    with phase_timer.phase("entities.analysis") if phase_timer is not None else nullcontext():
        analysis = analyze_project_source_with_c_backend(
            binary_source,
            metadata_path=metadata_path,
            entry_offset_args=(),
            project_root=PROJECT_ROOT,
        )
    return _build_entities_from_c_analysis(
        binary_source,
        cast(JsonDict, analysis),
        output_path,
        target_metadata,
        seeded_entities,
        seeded_code_entrypoints,
        phase_timer,
        effective_policy=cast(JsonDict, effective_policy),
    )


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


