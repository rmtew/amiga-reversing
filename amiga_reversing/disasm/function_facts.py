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
