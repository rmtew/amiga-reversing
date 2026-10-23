"""Durable region input validation; native analysis owns reference/proof facts."""

from __future__ import annotations

import re


def validate_region(region: dict) -> dict:
    fields = {
        "region_id",
        "name",
        "runtime_address",
        "size",
        "alignment",
        "source_domain",
        "memory_class",
        "lifetime",
        "dma_access",
    }
    optional = {"region_kind", "parent_region_id"}
    if not fields <= set(region) or set(region) - fields - optional:
        raise ValueError(
            "memory_region requires exactly the supported definition fields"
        )
    for key, limit in (("region_id", 95), ("name", 63)):
        if (
            not isinstance(region[key], str)
            or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", region[key])
            or len(region[key]) > limit
        ):
            raise ValueError(
                f"memory_region {key} requires a bounded stable identifier"
            )
    for key in ("runtime_address", "size", "alignment"):
        if type(region[key]) is not int or not 0 <= region[key] <= 0x1000000:
            raise ValueError(f"memory_region {key} requires a 24-bit extent")
    address, size, alignment = (
        region[k] for k in ("runtime_address", "size", "alignment")
    )
    if (
        not size
        or address + size > 0x1000000
        or not alignment
        or alignment & (alignment - 1)
        or address % alignment
    ):
        raise ValueError("memory_region requires a nonempty aligned extent")
    if (
        region["source_domain"] not in {"runtime_only", "mapped_source"}
        or region["memory_class"] != "cpu_ram"
        or region["lifetime"] != "persistent"
        or region["dma_access"] not in {"none", "chip"}
    ):
        raise ValueError("unsupported memory_region placement/lifetime contract")
    if region.get("region_kind", "storage") not in {"storage", "image", "workspace", "display"}:
        raise ValueError("memory_region requires a supported region_kind")
    parent = region.get("parent_region_id", "")
    if not isinstance(parent, str) or (parent and (
        not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", parent) or len(parent) > 95
        or parent == region["region_id"]
    )):
        raise ValueError("memory_region requires a distinct bounded parent identity")
    return dict(region)


def validate_layout(layout: dict) -> dict:
    """Validate authored configuration only; native facts own placement resolution."""
    required = {"schema_version", "layout_id", "chip_bytes", "placements"}
    if (not required <= set(layout) or set(layout) - required - {"bootstrap_contract_id", "bootstrap_variant"}
            or type(layout["schema_version"]) is not int or layout["schema_version"] != 1):
        raise ValueError("memory_layout requires the supported versioned fields")
    identity = layout["layout_id"]
    if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,94}", identity):
        raise ValueError("memory_layout requires a bounded stable identity")
    if type(layout["chip_bytes"]) is not int or layout["chip_bytes"] not in {0x80000, 0x100000}:
        raise ValueError("memory_layout requires an explicit supported Chip RAM extent")
    placements = layout["placements"]
    if not isinstance(placements, list) or len(placements) > 16:
        raise ValueError("memory_layout requires at most sixteen placements")
    seen = set()
    for item in placements:
        if not isinstance(item, dict) or set(item) != {"region_id", "runtime_address"}:
            raise ValueError("memory_layout requires explicit region placements")
        rid = item["region_id"]
        if not isinstance(rid, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,94}", rid) or rid in seen:
            raise ValueError("memory_layout requires unique bounded region identities")
        if type(item["runtime_address"]) is not int or not 0 <= item["runtime_address"] < 0x1000000:
            raise ValueError("memory_layout requires a 24-bit placement")
        seen.add(rid)
    if "bootstrap_contract_id" in layout or "bootstrap_variant" in layout:
        if (not isinstance(layout.get("bootstrap_contract_id"), str)
                or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,94}", layout["bootstrap_contract_id"])
                or layout.get("bootstrap_variant") not in {"native", "forward_disjoint"}):
            raise ValueError("memory_layout requires an explicit bootstrap identity and variant")
    return {**layout, "placements": [dict(p) for p in placements]}


def validate_bootstrap(contract: dict) -> dict:
    numeric = {"load_address", "file_size", "copied_source_end", "helper_source_start",
               "helper_source_end", "helper_runtime_address", "continuation_source_offset",
               "comparison_source_offset"}
    required = numeric | {"schema_version", "contract_id", "image_region_id", "input_sha256", "kind"}
    if (set(contract) != required or type(contract["schema_version"]) is not int
            or contract["schema_version"] != 1 or contract["kind"] != "retained_prefix_copy"):
        raise ValueError("bootstrap requires the versioned retained prefix-copy contract")
    for key in ("contract_id", "image_region_id"):
        if not isinstance(contract[key], str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,94}", contract[key]):
            raise ValueError("bootstrap requires bounded stable identities")
    if not isinstance(contract["input_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", contract["input_sha256"]):
        raise ValueError("bootstrap requires an exact input SHA256")
    if any(type(contract[k]) is not int or not 0 <= contract[k] < 0x1000000 for k in numeric):
        raise ValueError("bootstrap requires integer source/runtime extents")
    if not (0 < contract["copied_source_end"] <= contract["file_size"]
            and 0 <= contract["helper_source_start"] <= contract["comparison_source_offset"]
            and contract["comparison_source_offset"] + 2 <= contract["helper_source_end"] <= contract["copied_source_end"]
            and contract["continuation_source_offset"] < contract["copied_source_end"]):
        raise ValueError("bootstrap requires bounded prefix, helper and comparison extents")
    return dict(contract)


def relocation_plan(
    artifact, region_id: str, destination: int, memory_class: str
) -> dict:
    """Project a native proof/refusal without changing target facts or code."""
    return artifact.memory_region_plan(region_id, destination, memory_class)


def build_derived_artifact(
    target_id: str, artifact, plan: dict, subject_revision: str
) -> dict:
    import json

    from amiga_reversing.disasm.binary_source import read_binary_source_bytes
    from amiga_reversing.disasm.derived_artifact import sha256
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths

    if plan.get("status") != "ready" or plan.get("unresolved_obligations") != 0:
        raise ValueError(
            "Native relocation obligations remain unresolved; no artifact written"
        )
    original = read_binary_source_bytes(resolve_project_paths(target_id).binary_source)
    ledger = sorted(plan["rewrite_ledger"], key=lambda x: x["source_offset"])
    result = bytearray(original)
    end = 0
    for item in ledger:
        offset = item["source_offset"]
        before = bytes.fromhex(item["before"])
        after = bytes.fromhex(item["after"])
        if (
            offset < end
            or original[offset : offset + len(before)] != before
            or len(before) != len(after)
        ):
            raise ValueError("Native rewrite ledger is stale or overlapping")
        result[offset : offset + len(after)] = after
        end = offset + len(after)
    regions = artifact.memory_regions_payload()["items"]
    region = next(r for r in regions if r["region_id"] == plan["region_id"])
    if region.get("region_kind", "storage") != "storage" or region.get("parent_region_id"):
        raise ValueError("Legacy single-region artifacts do not admit hierarchical layout definitions")
    region = {
        k: region[k]
        for k in (
            "region_id",
            "name",
            "runtime_address",
            "size",
            "alignment",
            "source_domain",
            "memory_class",
            "lifetime",
            "dma_access",
        )
    }
    native_hash = sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    )
    manifest = {
        "schema_version": 1,
        "kind": "fixed_width_memory_relocation",
        "target_id": target_id,
        "original_sha256": sha256(original),
        "artifact_sha256": sha256(bytes(result)),
        "artifact_file": "payload.bin",
        "analysis_subject_revision": subject_revision,
        "region": region,
        "placement": {
            "runtime_address": plan["destination"],
            "memory_class": plan["memory_class"],
            "reservation": plan["reservation"],
        },
        "rewrite_ledger": ledger,
        "native_plan_sha256": native_hash,
    }
    if region["source_domain"] == "mapped_source":
        manifest["initialization"] = plan["initialization"]
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    directory = (
        PROJECT_ROOT
        / ".runtime-state"
        / "restoration"
        / "derived"
        / sha256(manifest_bytes)
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "payload.bin").write_bytes(result)
    (directory / "manifest.json").write_bytes(manifest_bytes)
    return {
        "status": "built",
        "manifest_path": str(directory / "manifest.json"),
        "artifact_sha256": manifest["artifact_sha256"],
        "manifest_sha256": sha256(manifest_bytes),
        "rewrite_count": len(ledger),
        "static_plan": plan,
        "runtime_evidence": None,
        "scenario_coverage": None,
    }
