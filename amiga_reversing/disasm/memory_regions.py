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
    if set(region) != fields:
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
        region["source_domain"] != "runtime_only"
        or region["memory_class"] != "cpu_ram"
        or region["lifetime"] != "persistent"
        or region["dma_access"] not in {"none", "chip"}
    ):
        raise ValueError("unsupported memory_region placement/lifetime contract")
    return dict(region)


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
