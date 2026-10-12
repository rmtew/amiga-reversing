"""Canonical function ownership facts derived from accepted CFG analysis."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping

from amiga_reversing.disasm.manual_actions import load_manual_projection
from amiga_reversing.disasm.project_paths import resolve_project_paths

_FLOW_EDGE_KINDS = frozenset({1, 2, 4})  # fallthrough, branch, jump


def _ranges(blocks: list[Mapping[str, object]]) -> list[dict[str, int]]:
    ranges: list[dict[str, int]] = []
    for block in sorted(blocks, key=lambda item: int(item["start_offset"])):
        start, end = int(block["start_offset"]), int(block["end_offset"])
        if ranges and ranges[-1]["end_offset"] == start:
            ranges[-1]["end_offset"] = end
        else:
            ranges.append({"start_offset": start, "end_offset": end})
    return ranges


def canonical_function_facts(target_id: str, analysis: Mapping[str, object], runtime_view: Mapping[str, int]) -> dict[str, object]:
    """Derive accepted/rejected named functions from canonical labels and CFG blocks.

    The result is a fact projection: labels establish candidate entries, while
    accepted blocks and CFG edges establish ownership.  It never uses rendered
    source order or a next-label extent.
    """

    sections = analysis.get("sections")
    if not isinstance(sections, list) or not sections or not isinstance(sections[0], Mapping):
        raise ValueError("Canonical analysis has no primary section for function facts.")
    section = sections[0]
    raw_blocks, raw_edges = section.get("blocks"), section.get("edges")
    if not isinstance(raw_blocks, list) or not isinstance(raw_edges, list):
        raise ValueError("Canonical analysis has no CFG blocks and edges for function facts.")
    blocks = [
        item
        for item in raw_blocks
        if isinstance(item, Mapping)
        and isinstance(item.get("start_offset"), int)
        and isinstance(item.get("end_offset"), int)
    ]
    if len(blocks) != len(raw_blocks) or any(
        int(item["start_offset"]) >= int(item["end_offset"])
        for item in blocks
    ):
        raise ValueError("Canonical CFG contains an invalid basic block.")
    by_start = {int(item["start_offset"]): index for index, item in enumerate(blocks)}
    if len(by_start) != len(blocks):
        raise ValueError("Canonical CFG contains duplicate basic-block entries.")
    edges_by_source: dict[int, list[Mapping[str, object]]] = defaultdict(list)
    for edge in raw_edges:
        if isinstance(edge, Mapping) and isinstance(edge.get("source_block_index"), int):
            edges_by_source[int(edge["source_block_index"])].append(edge)
    projection = load_manual_projection(resolve_project_paths(target_id).target_dir)
    base, source_start = runtime_view["base_addr"], runtime_view["source_start"]
    labels = [
        {"name": item.get("name"), "entry_offset": int(item["addr"]) - base + source_start}
        for item in projection.labels
        if item.get("address_domain") == "runtime" and isinstance(item.get("addr"), int) and isinstance(item.get("name"), str)
    ]
    name_counts: dict[str, int] = defaultdict(int)
    entries: dict[int, list[str]] = defaultdict(list)
    for label in labels:
        name_counts[str(label["name"])] += 1
        entries[int(label["entry_offset"])].append(str(label["name"]))
    def rejected(name: str, entry: int, reason: str) -> dict[str, object]:
        return {
            "name": name,
            "entry_offset": entry,
            "status": "rejected",
            "reason": reason,
            "ranges": [],
            "owned_blocks": [],
            "shared_terminal_blocks": [],
            "source_start": None,
            "source_end": None,
            "evidence": {"entry": "manual_label", "ownership": "rejected_cfg_flow"},
        }

    candidates: list[dict[str, object]] = []
    for label in labels:
        name, entry = str(label["name"]), int(label["entry_offset"])
        if name_counts[name] != 1:
            candidates.append(rejected(name, entry, "duplicate_name"))
        elif len(entries[entry]) != 1:
            candidates.append(rejected(name, entry, "ambiguous_entry_names"))
        elif entry not in by_start:
            candidates.append(rejected(name, entry, "entry_not_accepted_block"))
        else:
            candidates.append({"name": name, "entry_offset": entry, "status": "pending", "reason": None})
    named_entries = {entry for entry, names in entries.items() if names}
    ownership: dict[int, set[int]] = {}
    unresolved_flow: set[int] = set()
    for index, candidate in enumerate(candidates):
        if candidate["status"] != "pending":
            continue
        entry_index = by_start[int(candidate["entry_offset"])]
        owned, pending = {entry_index}, deque([entry_index])
        while pending:
            block_index = pending.popleft()
            for edge in edges_by_source.get(block_index, []):
                target = edge.get("target_block_index")
                if edge.get("kind") not in _FLOW_EDGE_KINDS:
                    continue
                if not isinstance(target, int) or target < 0 or target >= len(blocks):
                    unresolved_flow.add(index)
                    continue
                target_start = int(blocks[target]["start_offset"])
                if target_start != int(candidate["entry_offset"]) and target_start in named_entries:
                    continue
                if target not in owned:
                    owned.add(target)
                    pending.append(target)
        ownership[index] = owned
    block_owners: dict[int, list[int]] = defaultdict(list)
    for candidate_index, owned in ownership.items():
        for block_index in owned:
            block_owners[block_index].append(candidate_index)
    def shared_terminal(block_index: int) -> bool:
        outgoing = edges_by_source.get(block_index, [])
        return bool(outgoing) and all(edge.get("kind") == 5 for edge in outgoing)

    conflicted = {
        owner
        for block_index, owners in block_owners.items()
        if len(owners) > 1 and not shared_terminal(block_index)
        for owner in owners
    }
    named_entry_inside_block = {
        candidate_index
        for candidate_index, owned in ownership.items()
        for block_index in owned
        for named_entry in named_entries
        if named_entry != int(candidates[candidate_index]["entry_offset"])
        and int(blocks[block_index]["start_offset"]) < named_entry < int(blocks[block_index]["end_offset"])
    }
    facts: list[dict[str, object]] = []
    for index, candidate in enumerate(candidates):
        if candidate["status"] != "pending":
            facts.append(candidate)
            continue
        if index in unresolved_flow:
            facts.append(rejected(str(candidate["name"]), int(candidate["entry_offset"]), "unresolved_cfg_flow_target"))
            continue
        if index in conflicted:
            facts.append(rejected(str(candidate["name"]), int(candidate["entry_offset"]), "overlapping_cfg_ownership"))
            continue
        if index in named_entry_inside_block:
            facts.append(rejected(str(candidate["name"]), int(candidate["entry_offset"]), "named_entry_inside_owned_block"))
            continue
        owned_blocks = [blocks[item] for item in sorted(ownership[index])]
        ranges = _ranges(owned_blocks)
        facts.append({
            **candidate,
            "status": "accepted",
            "reason": None,
            "ranges": ranges,
            "owned_blocks": [{"start_offset": int(item["start_offset"]), "end_offset": int(item["end_offset"])} for item in owned_blocks],
            "shared_terminal_blocks": [
                {"start_offset": int(blocks[block_index]["start_offset"]), "end_offset": int(blocks[block_index]["end_offset"])}
                for block_index in sorted(ownership[index])
                if len(block_owners[block_index]) > 1 and shared_terminal(block_index)
            ],
            "source_start": min(item["start_offset"] for item in ranges),
            "source_end": max(item["end_offset"] for item in ranges),
            "evidence": {"entry": "manual_label", "ownership": "accepted_cfg_flow"},
        })
    return {"runtime_view": dict(runtime_view), "functions": facts}


_ENTRY_REASONS = frozenset({
    "section_entry", "policy_entry_offset", "policy_entry_point",
    "runtime_view_entry", "linkage_api_entry", "platform_loadseg_entry",
    "boundary_api_entry",
})
_EDGE_NAMES = {1: "fallthrough", 2: "branch", 3: "call", 4: "jump", 5: "return"}


def analysis_function_facts(target_id: str, analysis: Mapping[str, object]) -> dict[str, object]:
    """Project exploratory function candidates from native entry and CFG facts.

    Names (including accepted manual names) come from native symbol origins;
    names never establish entry points. Ranges are reachable accepted blocks,
    not claimed exact function extents. This deliberately does not relax the
    stricter runtime ownership contract of ``canonical_function_facts``.
    """
    facts: list[dict[str, object]] = []
    limits = ["native_cfg_is_section_local", "indirect_targets_may_be_incomplete",
              "candidate_ranges_are_not_proven_function_boundaries"]
    for section in analysis.get("sections", []):
        section_index = section["section_index"]
        blocks = section.get("blocks", [])
        edges = section.get("edges", [])
        by_start = {block["start_offset"]: index for index, block in enumerate(blocks)}
        if len(by_start) != len(blocks) or any(b["end_offset"] <= b["start_offset"] for b in blocks):
            raise ValueError("Canonical CFG contains invalid or duplicate basic blocks.")
        seeds: dict[int, list[dict[str, object]]] = defaultdict(list)
        outgoing: dict[int, list[Mapping[str, object]]] = defaultdict(list)
        calls_to: dict[int, list[Mapping[str, object]]] = defaultdict(list)
        names: dict[int, list[dict[str, object]]] = defaultdict(list)
        for origin in section.get("symbol_origins", []):
            names[origin["offset"]].append(dict(origin))
        for ref in section.get("code_start_refs", []):
            if ref.get("reason_name") in _ENTRY_REASONS:
                seeds[ref["offset"]].append(dict(ref))
        for edge in edges:
            outgoing[edge["source_block_index"]].append(edge)
            target = edge.get("target_offset")
            if edge.get("kind") == 3 and isinstance(target, int) and 0 <= target < 0xFFFFFFFF:
                seeds[target].append({"reason_name": "native_call_target", "source_offset": edge["source_offset"]})
                calls_to[target].append(edge)
        ownership: dict[int, set[int]] = {}
        for entry in sorted(seeds):
            owned: set[int] = set()
            pending = deque([by_start[entry]]) if entry in by_start else deque()
            while pending:
                index = pending.popleft()
                if index in owned:
                    continue
                owned.add(index)
                for edge in outgoing[index]:
                    target = edge.get("target_block_index")
                    if edge.get("kind") not in _FLOW_EDGE_KINDS or not isinstance(target, int) or not 0 <= target < len(blocks):
                        continue
                    target_start = blocks[target]["start_offset"]
                    if target_start == entry or target_start not in seeds:
                        pending.append(target)
            ownership[entry] = owned
        owners: dict[int, list[int]] = defaultdict(list)
        for entry, owned in ownership.items():
            for index in owned:
                owners[index].append(entry)

        def transfer(edge: Mapping[str, object], section_index: int = section_index,
                     owners: Mapping[int, list[int]] = owners) -> dict[str, object]:
            target = edge.get("target_offset")
            resolved = isinstance(target, int) and 0 <= target < 0xFFFFFFFF
            return {"section_index": section_index, "source_offset": edge["source_offset"],
                    "target_section_index": section_index if resolved else None,
                    "target_offset": target if resolved else None,
                    "kind": _EDGE_NAMES.get(edge.get("kind"), "unknown"),
                    "status": "resolved" if resolved else "dynamic_return" if edge.get("kind") == 5 else "unresolved",
                    "source_entries": sorted(owners.get(edge["source_block_index"], [])),
                    "provenance": "native_cfg"}

        for entry, owned in ownership.items():
            local_edges = [edge for index in sorted(owned) for edge in outgoing[index]]
            unresolved = [transfer(e) for e in local_edges if e.get("kind") != 5 and
                          (not isinstance(e.get("target_offset"), int) or not 0 <= e["target_offset"] < 0xFFFFFFFF)]
            missing_blocks = any(
                e.get("kind") in _FLOW_EDGE_KINDS and
                (not isinstance(e.get("target_block_index"), int) or
                 not 0 <= e["target_block_index"] < len(blocks))
                for e in local_edges
            )
            shared = [index for index in sorted(owned) if len(owners[index]) > 1]
            unknowns = list(limits)
            if not owned:
                unknowns.append("entry_not_accepted_block")
            if shared:
                unknowns.append("shared_cfg_blocks")
            if unresolved:
                unknowns.append("unresolved_control_transfers")
            if missing_blocks:
                unknowns.append("flow_target_not_accepted_block")
            origin_names = names.get(entry, [])
            aliases = sorted({str(n["symbol_name"]) for n in origin_names if n.get("symbol_name")})
            facts.append({
                "section_index": section_index, "source_offset": entry, "entry_offset": entry,
                "name": aliases[0] if aliases else None, "names": aliases,
                "name_evidence": origin_names, "entry_evidence": seeds[entry],
                "status": "candidate", "ownership_status": "unavailable" if not owned else "ambiguous" if shared else "partial" if unresolved or missing_blocks else "cfg_supported",
                "ranges": _ranges([blocks[i] for i in sorted(owned)]),
                "owned_blocks": [{"start_offset": blocks[i]["start_offset"], "end_offset": blocks[i]["end_offset"],
                                  "certainty": blocks[i].get("certainty")} for i in sorted(owned)],
                "shared_block_starts": [blocks[i]["start_offset"] for i in shared],
                "callers": [transfer(e) for e in calls_to[entry]],
                "callees": [transfer(e) for e in local_edges if e.get("kind") == 3],
                "unresolved_transfers": unresolved, "unknowns": unknowns, "provenance": "native_cfg_projection",
            })
    return {"target_id": target_id, "functions": sorted(facts, key=lambda f: (f["section_index"], f["entry_offset"])), "unknowns": limits}
