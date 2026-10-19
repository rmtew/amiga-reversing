"""Read-only accounting over native facts and effective target metadata.

These are independent evidence dimensions, never a completion score. In
particular, spelling, authored prose, accepted formatting actions and INCBIN
selection cannot establish purpose or prove a complete object boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict

from .target_metadata import TargetMetadata

SCHEMA = "restoration-accounting/v1"
_UNKNOWN_KINDS = {"residual", "unknown"}
_GENERIC_NAME = re.compile(
    r"^(?:abs|loc|sub|func|function|data|dblk|str|string|table|byte|word|long)(?:_|$)",
    re.I,
)


def _id(kind, *parts):
    return (
        kind
        + ":"
        + hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:20]
    )


def union_size(ranges):
    """Union within ONE coordinate space; aliases never add physical bytes."""
    end = None
    total = 0
    for lo, hi in sorted(set(ranges)):
        if type(lo) is not int or type(hi) is not int or hi <= lo:
            raise ValueError("Invalid accounting interval")
        total += max(0, hi - max(lo, end if end is not None else lo))
        end = max(hi, end if end is not None else hi)
    return total


def partition(start, end, claims):
    """Split an explicit envelope into disjoint, evidence-bearing intervals.

    Claims are (start,end,classification,status,identity). Aliases of the same
    accepted class coalesce; inconsistent accepted classes remain conflicts.
    Candidate/deferred/blocked claims never fill an accepted-classification gap.
    """
    if type(start) is not int or type(end) is not int or end <= start:
        raise ValueError("Invalid accounting envelope")
    events = defaultdict(list)
    events[start]
    events[end]
    for index, (lo, hi, _kind, _status, identity) in enumerate(claims):
        if type(lo) is not int or type(hi) is not int or not start <= lo < hi <= end:
            raise ValueError(f"Claim outside accounting envelope: {identity}")
        events[lo].append((index, True))
        events[hi].append((index, False))
    active = set()
    cells = []
    points = sorted(events)
    for i, lo in enumerate(points[:-1]):
        for index, add in events[lo]:
            if add:
                active.add(index)
            else:
                active.remove(index)
        hi = points[i + 1]
        accepted = {claims[j][2] for j in active if claims[j][3] == "accepted"}
        known = accepted - _UNKNOWN_KINDS
        # Structured data is a broad owner, compatible with an accepted leaf
        # table/string/platform record nested inside it. It is not a rival type.
        if known & {"text", "table", "platform_metadata"}:
            known.discard("structured_data")
        provisional = {claims[j][2] for j in active if claims[j][3] != "accepted"}
        kind = (
            "conflict"
            if any(
                claims[j][2] == "conflict" or claims[j][3] == "conflict" for j in active
            )
            or len(known) > 1
            else next(iter(known))
            if known
            else "unknown"
        )
        signature = (kind, sorted(provisional), sorted({claims[j][4] for j in active}))
        if cells and cells[-1]["_signature"] == signature:
            cells[-1]["end"] = hi
        else:
            cells.append(
                {
                    "start": lo,
                    "end": hi,
                    "classification": kind,
                    "provisional_classes": signature[1],
                    "evidence": signature[2],
                    "_signature": signature,
                }
            )
    for c in cells:
        del c["_signature"]
    return cells


def _summary(cells):
    counts = Counter()
    for cell in cells:
        counts[cell["classification"]] += cell["end"] - cell["start"]
    return dict(sorted(counts.items()))


def _workspace(analysis):
    groups = defaultdict(list)
    for field in analysis.get("base_layout_fields", []):
        # Use the native normalized base identity; do not merge unrelated bases
        # because they happen to use equal numeric offsets or field spellings.
        key = (
            field.get("layout_kind"),
            field.get("layout_name"),
            field.get("base_symbol"),
        )
        groups[key].append(field)
    result = []
    for key, fields in sorted(groups.items(), key=lambda x: str(x[0])):
        name = _id("workspace", *key)
        claims = []
        for f in fields:
            lo, size = f["offset"], f["size"]
            if not size:
                continue
            claims.append(
                (
                    lo,
                    lo + size,
                    "field",
                    "conflict" if f.get("conflicted") else "accepted",
                    _id("base-field", *key, lo, size, f.get("symbol")),
                )
            )
        if not claims:
            continue
        lo = min(c[0] for c in claims)
        hi = max(c[1] for c in claims)
        cells = partition(lo, hi, claims)
        # Conflicted declarations still occupy storage but cannot resolve it.
        for cell in cells:
            overlap = [
                f
                for f in fields
                if f["offset"] < cell["end"] and f["offset"] + f["size"] > cell["start"]
            ]
            cell["overlapping_declarations"] = len(overlap)
            cell["aliases"] = sum(bool(f.get("alias")) for f in overlap)
            if any(f.get("conflicted") for f in overlap):
                cell["classification"] = "conflict"
            cell["gap_intent"] = "unknown" if not overlap else None
            cell["id"] = f"{name}:{cell['start']:x}:{cell['end']:x}"
        result.append(
            {
                "id": name,
                "layout_identity": list(key),
                "observed_start": lo,
                "observed_end": hi,
                "denominator_bytes": None,
                "boundary_status": "observed_envelope_only",
                "observed_envelope_bytes": hi - lo,
                "declared_union_bytes": union_size((c[0], c[1]) for c in claims),
                "field_declarations": len(fields),
                "alias_declarations": sum(bool(f.get("alias")) for f in fields),
                "classification_bytes": _summary(cells),
                "intervals": cells,
                "intent_counts": {
                    "unknown_gaps": sum(
                        c["classification"] == "unknown" for c in cells
                    ),
                    "reserved": None,
                    "padding": None,
                    "unused": None,
                },
            }
        )
    return result


def _data_units(metadata):
    units = []
    for owner in sorted(
        metadata.data_block_layouts, key=lambda o: (o.hunk, o.source_start, o.layout_id)
    ):
        claims = [
            (
                e.offset,
                e.offset + e.width,
                "padding"
                if e.kind.value == "padding"
                else "unknown"
                if e.kind.value in {"gap", "raw"}
                else "element",
                "accepted",
                f"{owner.layout_id}:element:{e.offset:x}",
            )
            for e in owner.elements
        ]
        cells = partition(0, owner.source_end - owner.source_start, claims)
        units.append(
            {
                "id": owner.layout_id,
                "section": owner.hunk,
                "start": owner.source_start,
                "end": owner.source_end,
                "name": owner.name,
                "declared_role": owner.role,
                "review_status": owner.review_status.value,
                "evidence": [owner.citation],
                "purpose": "not_separately_assessed",
                "layout_bytes": _summary(cells),
                "unresolved_layout_intervals": [
                    {**c, "id": f"{owner.layout_id}:layout:{c['start']:x}:{c['end']:x}"}
                    for c in cells
                    if c["classification"] in {"unknown", "conflict"}
                ],
                "array_record_count": sum(e.array_count or 0 for e in owner.elements),
                "declared_type_bindings": sum(
                    e.type_binding is not None for e in owner.elements
                ),
            }
        )
    return units


def _section_cells(section, start, end, domain):
    sid = section["section_index"]
    for claim in section.get("range_ownerships", []):
        if (
            not 0
            <= claim["start_offset"]
            < claim["end_offset"]
            <= section["section_size"]
        ):
            raise ValueError("Native ownership outside analysis section")
    claims = [
        (
            max(start, r["start_offset"]),
            min(end, r["end_offset"]),
            r["kind_name"],
            r["status_name"],
            f"native:ownership:s{sid}:{r['start_offset']:x}:{r['end_offset']:x}:{r['kind_name']}:{r['status_name']}",
        )
        for r in section.get("range_ownerships", [])
        if r["start_offset"] < end and r["end_offset"] > start
    ]
    cells = partition(start, end, claims)
    compact = []
    for cell in cells:
        known = (
            cell["classification"] not in {"unknown", "conflict"}
            and not cell["provisional_classes"]
        )
        if known:
            if (
                compact
                and compact[-1].get("_claims") is not None
                and compact[-1]["classification"] == cell["classification"]
            ):
                compact[-1]["end"] = cell["end"]
                compact[-1]["_claims"].update(cell["evidence"])
            else:
                compact.append({**cell, "_claims": set(cell["evidence"])})
        else:
            compact.append(cell)
    cells = compact
    for cell in cells:
        if "_claims" in cell:
            cell["evidence"] = {
                "kind": "native_ownership_interval",
                "section": sid,
                "start": cell["start"],
                "end": cell["end"],
                "native_claim_count": len(cell.pop("_claims")),
            }
        cell["id"] = f"{domain}:s{sid}:{cell['start']:x}:{cell['end']:x}"
        cell["classification_confidence"] = (
            "native_acceptance_only"
            if cell["classification"] not in {"unknown", "conflict"}
            else "unresolved"
        )
    return cells


def build_accounting(
    *,
    target_id,
    analysis,
    metadata: TargetMetadata,
    functions=None,
    source_plan=None,
    manifest=None,
    memory_regions=None,
    verification=None,
    provenance=None,
    history=None,
):
    """Project canonical DTOs only. No assembly parsing or target writes."""
    functions = functions or {
        "functions": [],
        "unknowns": ["function_projection_not_supplied"],
    }
    source_plan = source_plan or {"rows": [], "labels": []}
    manifest = manifest or {"files": []}
    memory_regions = memory_regions or {"items": []}
    payload = []
    section_allocations = []
    unbounded_sections = []
    storage_by_section = {
        s["section_index"]: s for s in source_plan.get("sections", [])
    }
    for section in sorted(
        analysis.get("sections", []), key=lambda s: s["section_index"]
    ):
        sid, size = section["section_index"], section["section_size"]
        storage = storage_by_section.get(sid)
        if storage is None:
            unbounded_sections.append(
                {
                    "id": f"section:s{sid}",
                    "analysis_envelope_bytes": size,
                    "stored_bytes": None,
                    "reason": "canonical_storage_extents_unavailable",
                }
            )
            continue
        stored, allocated = storage["stored_size"], storage["allocation_size"]
        if not 0 <= stored <= allocated or allocated != size:
            raise ValueError("Native storage and analysis extents disagree")

        if stored:
            cells = _section_cells(section, 0, stored, "payload")
            payload.append(
                {
                    "section": sid,
                    "denominator_bytes": stored,
                    "classification_bytes": _summary(cells),
                    "intervals": cells,
                    "purpose": {
                        "status": "not_separately_assessed",
                        "assessed_bytes": None,
                    },
                }
            )
        if allocated > stored:
            cells = _section_cells(section, stored, allocated, "section-workspace")
            section_allocations.append(
                {
                    "id": f"section-workspace:s{sid}",
                    "section": sid,
                    "start": stored,
                    "end": allocated,
                    "denominator_bytes": allocated - stored,
                    "classification_bytes": _summary(cells),
                    "intervals": cells,
                    "purpose": "not_separately_assessed",
                }
            )
    code = []
    for f in functions["functions"]:
        code.append(
            {
                "id": f"function:s{f['section_index']}:{f['entry_offset']:x}",
                "section": f["section_index"],
                "entry": f["entry_offset"],
                "names": f.get("names", []),
                "ownership_status": f.get("ownership_status"),
                "ranges": f.get("ranges", []),
                "evidence": f.get("entry_evidence", []),
                "unknowns": f.get("unknowns", []),
                "unresolved_transfers": len(f.get("unresolved_transfers", [])),
                "purpose": "not_separately_assessed",
            }
        )
    code.sort(key=lambda f: (f["section"], f["entry"]))
    data = _data_units(metadata)
    assets = []
    for a in manifest["files"]:
        if a.get("kind") != "asset":
            continue
        assets.append(
            {
                k: a[k]
                for k in (
                    "asset_id",
                    "source_section_index",
                    "source_offset",
                    "size",
                    "classification",
                )
                if k in a
            }
        )
    assets.sort(key=lambda a: a["asset_id"])
    asset_bytes = {}
    for sid in sorted({a["source_section_index"] for a in assets}):
        asset_bytes[str(sid)] = union_size(
            (a["source_offset"], a["source_offset"] + a["size"])
            for a in assets
            if a["source_section_index"] == sid
        )
    hardware, absolute_other = [], []
    for r in analysis.get("absolute_address_ranges", []):
        item = {
            "id": _id(
                "absolute", r["start_address"], r["range_end"], r["owner_kind_name"]
            ),
            "start": r["start_address"],
            "end": r["range_end"],
            "owner_kind": r["owner_kind_name"],
            "status": r["status_name"],
            "evidence": f"s{r['source_section_index']}:{r['source_offset']:x}",
        }
        (
            hardware
            if r["owner_kind_name"]
            in {
                "hardware_register",
                "hardware_register_range",
                "cpu_vector",
                "execbase_literal",
            }
            else absolute_other
        ).append(item)
    hardware.sort(key=lambda a: (a["start"], a["end"], a["id"]))
    absolute_other.sort(key=lambda a: (a["start"], a["end"], a["id"]))
    # Absolute observations and base-relative declarations have no generally
    # proved mapping between them. Their byte counts must never be added.
    workspace = _workspace(analysis)
    runtime_regions = sorted(memory_regions["items"], key=lambda r: r["region_id"])
    regions = [
        {
            k: r[k]
            for k in (
                "region_id",
                "runtime_address",
                "size",
                "source_domain",
                "memory_class",
                "lifetime",
                "dma_access",
            )
            if k in r
        }
        for r in runtime_regions
    ]
    accesses = Counter()
    refs = Counter()
    indirect_status = Counter()
    unresolved = []
    for section in analysis.get("sections", []):
        sid = section["section_index"]
        accesses["resolved_native_access_records"] += len(
            section.get("recovered_platform_typed_accesses", [])
        )
        for a in section.get("recovered_platform_unresolved_typed_accesses", []):
            accesses["unresolved_native_access_records"] += 1
            unresolved.append(
                {
                    "id": f"field:s{sid}:{a['offset']:x}:{a.get('operand_index', 0)}",
                    "kind": "field_access",
                    "evidence": a,
                }
            )
        for ref in section.get("data_references", []):
            status = ref.get("target_status_name") or "unknown"
            refs[status] += 1
            if status not in {"accepted_target", "numeric_exact"}:
                unresolved.append(
                    {
                        "id": _id(
                            "reference",
                            sid,
                            ref["source_offset"],
                            ref.get("owner_id"),
                            ref.get("table_entry_index"),
                        ),
                        "kind": "data_reference",
                        "evidence": ref,
                    }
                )
        for site in section.get("recovered_indirect_sites", []):
            status = site.get("status") or "unknown"
            indirect_status[status] += 1
            if status in {"unresolved", "unknown"}:
                unresolved.append(
                    {
                        "id": f"indirect:s{sid}:{site['offset']:x}:{site.get('operand_index', 0)}",
                        "kind": "indirect_site",
                        "evidence": site,
                    }
                )
    labels = source_plan.get("labels", [])
    generic = [
        {
            "section": l["source_section_index"],
            "offset": l["source_offset"],
            "name": l["name"],
        }
        for l in labels
        if _GENERIC_NAME.match(l["name"])
    ]
    generic.sort(key=lambda x: (x["section"], x["offset"], x["name"]))
    emitted = defaultdict(list)
    for row in source_plan.get("rows", []):
        if row.get("has_source_range") and row.get("source_size", 0) > 0:
            emitted[str(row["source_section_index"])].append(
                (row["source_offset"], row["source_offset"] + row["source_size"])
            )
    typed_seeds = Counter(
        e.struct_name for e in metadata.seeded_entities if e.struct_name
    )
    unresolved.sort(key=lambda i: i["id"])
    return {
        "schema": SCHEMA,
        "target_id": target_id,
        "provenance": provenance or {},
        "payload_sections": payload,
        "unbounded_sections": unbounded_sections,
        "workspace": {
            "base_layouts": workspace,
            "section_allocations": section_allocations,
            "runtime_regions": regions,
            "absolute_observations": absolute_other,
            "denominator_bytes": None,
            "coordinate_spaces_must_not_be_added": True,
        },
        "hardware_external": {
            "observed_ranges": hardware,
            "unknown_extent_observations": sum(
                r["end"] <= r["start"] for r in hardware
            ),
            "denominator_bytes": None,
            "observed_union_bytes": union_size(
                (r["start"], r["end"]) for r in hardware if r["end"] > r["start"]
            ),
        },
        "units": {
            "code": {
                "candidate_count": len(code),
                "complete_boundary_denominator": None,
                "candidates": code,
                "limits": functions.get("unknowns", []),
            },
            "data": {
                "owner_count": len(data),
                "owners": data,
                "typed_seed_records": dict(sorted(typed_seeds.items())),
                "string_seed_count": sum(
                    e.subtype == "string" for e in metadata.seeded_entities
                ),
                "complete_object_denominator": None,
            },
            "assets": {
                "emission_chunk_count": len(assets),
                "union_bytes_by_section": asset_bytes,
                "chunks": assets,
                "semantic_resource_denominator": None,
            },
        },
        "purpose": {
            "status": "not_separately_assessed",
            "assessed_unit_denominator": None,
            "confidence": "unknown",
            "reason": "Canonical models have no separate, bounded purpose-completeness assessment; annotation evidence remains available but is not automatically promoted.",
        },
        "structure": {
            "field_access_records": dict(sorted(accesses.items())),
            "data_reference_target_status": dict(sorted(refs.items())),
            "indirect_site_status": dict(sorted(indirect_status.items())),
            "manual_reference_declarations": len(metadata.manual_data_references),
            "unresolved": unresolved,
            "closure_status": "not_established",
        },
        "presentation": {
            "source_union_bytes_by_section": {
                k: union_size(v) for k, v in sorted(emitted.items())
            },
            "generic_label_signals": generic,
            "label_count": len(labels),
            "source_quality_diagnostics": analysis.get(
                "source_quality_diagnostics", []
            ),
            "purpose_inferred": False,
        },
        "annotation_evidence": history or {},
        "verification": verification or {"status": "not_supplied"},
        "final_review": {"status": "not_assessed"},
        "relocation_readiness": {"status": "not_assessed"},
        "limits": [
            "Native classification acceptance is not semantic acceptance.",
            "Candidate function ranges may overlap; counts are discovered candidates, not a complete function denominator.",
            "Layout coverage describes declared elements, not the completeness of nested fields or dynamic references.",
            "INCBIN chunks, names and comments do not establish resource purpose or boundaries.",
            "Workspace gaps are unknown. No missing access establishes unused storage; reserved/padding/unused intent is unavailable unless canonical facts explicitly encode it.",
            "Base-relative envelopes exclude unknown prefix/suffix extents; absolute observations and mapped-source regions are separate coordinate views, not additive bytes.",
            "All semantic purpose assessments remain unassessed; this does not assert that existing restoration evidence is wrong.",
            "Exact original-layout output does not establish final review or changed-layout execution safety.",
        ],
    }


def format_accounting(report):
    """Compact human view; machine output retains every unresolved identity."""
    lines = [
        f"Restoration accounting: {report['target_id']}",
        "",
        "Payload classification (disjoint bytes per source section):",
    ]
    for s in report["payload_sections"]:
        counts = ", ".join(f"{k}={v}" for k, v in s["classification_bytes"].items())
        lines.append(
            f"  section {s['section']}: {s['denominator_bytes']} bytes; {counts}"
        )
    for s in report["unbounded_sections"]:
        lines.append(
            f"  {s['id']}: stored/allocation boundary unknown; analysis envelope {s['analysis_envelope_bytes']} bytes."
        )
    u = report["units"]
    lines += [
        "",
        f"Units: {u['code']['candidate_count']} function candidates; {u['data']['owner_count']} declared data owners; {u['assets']['emission_chunk_count']} asset emission chunks.",
        "Complete function/object/resource denominators: unknown.",
        "Purpose and confidence: not separately assessed; no semantic completion claim.",
        "Workspace (coordinate views are not additive):",
    ]
    for w in report["workspace"]["base_layouts"]:
        lines.append(
            f"  {w['layout_identity']}: envelope [{w['observed_start']},{w['observed_end']}), {w['declared_union_bytes']} declared bytes; {w['classification_bytes']}; full extent unknown."
        )
    for w in report["workspace"]["section_allocations"]:
        lines.append(
            f"  {w['id']}: {w['denominator_bytes']} allocated, non-stored bytes; purpose unassessed."
        )
    lines += [
        f"Hardware/external: {report['hardware_external']['observed_union_bytes']} observed union bytes; denominator unknown.",
        f"Structure: {report['structure']['field_access_records']}; reference target statuses {report['structure']['data_reference_target_status']}.",
        f"Presentation: {len(report['presentation']['generic_label_signals'])} generic label review signals.",
        f"Verification: {report['verification']['status']}; final review: not assessed; relocation readiness: not assessed.",
        "",
        "Selected unresolved identities (full list in JSON):",
    ]
    choices = [
        {"id": c["id"], "kind": c["classification"]}
        for s in report["payload_sections"]
        for c in s["intervals"]
        if c["classification"] in {"unknown", "conflict"}
    ]
    choices += report["structure"]["unresolved"]
    for item in choices[:12]:
        lines.append(f"  {item['id']} ({item['kind']})")
    return "\n".join(lines) + "\n"
