"""Bounded inspection of canonical pointer fields and native resolution outcomes.

This module never resolves an address itself and never promotes a scalar field.
The native render plan remains the authority for expressions and their reasons.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping

from amiga_reversing.disasm.target_metadata import TargetMetadata


def typed_pointer_report(
    metadata: TargetMetadata,
    row_lookup: Callable[..., Mapping[str, object] | None],
    *,
    offset: int = 0,
    limit: int = 50,
    struct_name: str | None = None,
    summary_only: bool = False,
    exceptions_only: bool = False,
) -> dict[str, object]:
    """Inspect every explicit bound pointer, retaining at most one result page.

    Counts cover the entire selected population, including interrupted fields.
    Offset and limit select the returned details, not the summary denominator.
    Names and address-looking scalar values do not participate in selection.
    """
    if type(offset) is not int or offset < 0:
        raise ValueError("offset must be a nonnegative integer")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be 1..100")
    if type(exceptions_only) is not bool:
        raise ValueError("exceptions_only must be boolean")
    selected = {}
    for entity in metadata.seeded_entities:
        if not entity.struct_name or not entity.field_name:
            continue
        if struct_name is not None and entity.struct_name != struct_name:
            continue
        if not entity.pointer_struct and entity.value_kind not in {
            "target_pointer", "struct_pointer"
        }:
            continue
        key = (entity.hunk, entity.addr)
        if key in selected and selected[key] != entity:
            raise ValueError(f"Conflicting canonical pointer fields at {key}")
        selected[key] = entity

    counts: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    items = []
    detail_count = 0
    for key, entity in sorted(selected.items()):
        row = row_lookup(section_index=key[0], offset=key[1])
        native = row.get("pointer_resolution") if row else None
        whole_field = bool(row and row.get("start_offset") == entity.addr
                           and entity.end is not None and row.get("end_offset") == entity.end)
        if isinstance(native, Mapping) and whole_field:
            resolution = dict(native)
        else:
            # A missing native result is visible, never reconstructed from text.
            resolution = {
                "outcome": "unresolved",
                "reason": ("missing_native_row" if not row else
                           "missing_native_resolution" if whole_field else "field_boundary"),
            }
        counts[str(resolution.get("outcome", "unresolved"))] += 1
        reasons[str(resolution.get("reason", "missing_native_reason"))] += 1
        if exceptions_only and resolution.get("outcome") in {"symbolic", "null"}:
            continue
        if not summary_only and offset <= detail_count < offset + limit:
            items.append({
                "section_index": entity.hunk,
                "source_offset": entity.addr,
                "end_offset": entity.end,
                "struct_name": entity.struct_name,
                "field_name": entity.field_name,
                "name": entity.name,
                "resolution": resolution,
            })
        detail_count += 1
    total = detail_count
    return {
        "total": total,
        "population_total": len(selected),
        "exceptions_only": exceptions_only,
        "outcomes": dict(sorted(counts.items())),
        "reasons": dict(sorted(reasons.items())),
        "offset": offset,
        "limit": limit,
        "items": items,
        "has_more": not summary_only and offset + limit < total,
        "next_offset": offset + limit if not summary_only and offset + limit < total else None,
        "selection": "Canonical bound fields with explicit pointer semantics; scalar candidates excluded.",
        "limits": [
            "Static encoded fields; no claim about runtime mutations, pointee extent, or lifetime.",
            "Native symbolic resolution establishes an expression, not semantic evidence for the type.",
        ],
    }
