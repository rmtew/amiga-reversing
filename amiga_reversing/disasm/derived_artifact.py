"""Exact derived-payload identity for relocation and explicit optional patches.

Relocation rewrites fixed-width operands without moving code. Optional patches
preserve payload extent but may change internal instruction boundaries; those
ranges are excluded from original runtime instruction mappings.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from amiga_reversing.disasm.binary_source import read_binary_source_bytes
from amiga_reversing.disasm.project_paths import resolve_project_paths


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_manifest(manifest_path: Path, target_id: str) -> tuple[dict, Path]:
    manifest = json.loads(manifest_path.read_text())
    if isinstance(manifest, dict) and manifest.get('kind') == 'fixed_size_optional_patch':
        from .optional_artifact import validate
        return validate(manifest, manifest_path.parent, target_id)
    fields = {
        "schema_version",
        "kind",
        "target_id",
        "original_sha256",
        "artifact_sha256",
        "artifact_file",
        "analysis_subject_revision",
        "region",
        "placement",
        "rewrite_ledger",
        "native_plan_sha256",
    }
    if (
        not isinstance(manifest, dict)
        or set(manifest) not in (fields, fields | {"initialization"})
        or manifest["schema_version"] != 1
        or manifest["kind"] != "fixed_width_memory_relocation"
        or manifest["target_id"] != target_id
    ):
        raise ValueError("Invalid derived artifact contract")
    from amiga_reversing.disasm.memory_regions import validate_region

    if not isinstance(manifest["region"], dict):
        raise ValueError("Invalid derived artifact region")
    validate_region(manifest["region"])
    placement = manifest["placement"]
    if (
        not isinstance(placement, dict)
        or set(placement) != {"runtime_address", "memory_class", "reservation"}
        or type(placement["runtime_address"]) is not int
        or not 0 <= placement["runtime_address"] < 0x1000000
        or placement["memory_class"] not in {"chip", "slow"}
        or placement["reservation"] != "exec_allocabs"
    ):
        raise ValueError("Invalid derived artifact placement")
    for key in (
        "original_sha256",
        "artifact_sha256",
        "native_plan_sha256",
        "analysis_subject_revision",
    ):
        if not isinstance(manifest[key], str) or not __import__("re").fullmatch(
            r"[0-9a-f]{64}", manifest[key]
        ):
            raise ValueError("Invalid derived artifact identity hash")
    original = read_binary_source_bytes(resolve_project_paths(target_id).binary_source)
    if sha256(original) != manifest["original_sha256"]:
        raise ValueError("Derived artifact original target identity mismatch")
    initialization = manifest.get("initialization")
    if manifest["region"]["source_domain"] == "mapped_source":
        if (not isinstance(initialization, dict)
                or set(initialization) != {"section_index", "source_offset", "bytes"}
                or initialization["section_index"] != 0
                or type(initialization["source_offset"]) is not int
                or initialization["source_offset"] < 0
                or not isinstance(initialization["bytes"], str)):
            raise ValueError("Mapped artifact requires exact source initialization")
        offset, size = initialization["source_offset"], manifest["region"]["size"]
        if (offset + size > len(original)
                or initialization["bytes"] != original[offset:offset+size].hex()):
            raise ValueError("Mapped initialization differs from original source bytes")
    elif "initialization" in manifest:
        raise ValueError("Runtime-only artifact cannot claim source initialization")
    artifact_file = manifest["artifact_file"]
    if not isinstance(artifact_file, str) or Path(artifact_file).name != artifact_file:
        raise ValueError("Derived artifact requires a sibling payload filename")
    artifact_path = manifest_path.parent / artifact_file
    derived = artifact_path.read_bytes()
    if len(derived) != len(original) or sha256(derived) != manifest["artifact_sha256"]:
        raise ValueError("Derived artifact payload identity mismatch")
    rebuilt = bytearray(original)
    end = 0
    if (
        not isinstance(manifest["rewrite_ledger"], list)
        or not manifest["rewrite_ledger"]
    ):
        raise ValueError("Derived artifact requires a nonempty exact rewrite ledger")
    for item in manifest["rewrite_ledger"]:
        if (
            not isinstance(item, dict)
            or set(item)
            != {
                "section_index",
                "source_offset",
                "before",
                "after",
                "operand_index",
                "region_offset",
            }
            or item["section_index"] != 0
        ):
            raise ValueError("Unsupported derived artifact rewrite")
        offset = item["source_offset"]
        before, after = bytes.fromhex(item["before"]), bytes.fromhex(item["after"])
        if (
            type(offset) is not int
            or offset < end
            or not before
            or len(before) != len(after)
            or offset + len(before) > len(original)
            or original[offset : offset + len(before)] != before
            or before == after
        ):
            raise ValueError(
                "Derived artifact rewrite is overlapping, stale or changes instruction extent"
            )
        rebuilt[offset : offset + len(after)] = after
        end = offset + len(after)
    if bytes(rebuilt) != derived:
        raise ValueError(
            "Derived artifact contains changes outside its exact rewrite ledger"
        )
    # Native plan proof must be checked by the caller against the current artifact.
    return manifest, artifact_path


def verify_native_binding(manifest: dict, artifact) -> None:
    """Re-run the proof against current native facts; manifest claims are not proof."""
    if manifest.get('kind') == 'fixed_size_optional_patch':
        from .optional_artifact import verify_binding
        verify_binding(manifest, artifact)
        return
    region = next(
        (
            r
            for r in artifact.memory_regions_payload()["items"]
            if r["region_id"] == manifest["region"]["region_id"]
        ),
        None,
    )
    if region is None or any(region.get(k) != v for k, v in manifest["region"].items()):
        raise ValueError("Derived artifact region definition is stale")
    placement = manifest["placement"]
    if (
        set(placement) != {"runtime_address", "memory_class", "reservation"}
        or placement["reservation"] != "exec_allocabs"
    ):
        raise ValueError("Unsupported derived artifact placement")
    plan = artifact.memory_region_plan(
        region["region_id"], placement["runtime_address"], placement["memory_class"]
    )
    digest = sha256(json.dumps(plan, sort_keys=True, separators=(",", ":")).encode())
    if (
        plan["status"] != "ready"
        or digest != manifest["native_plan_sha256"]
        or sorted(plan["rewrite_ledger"], key=lambda x: x["source_offset"])
        != manifest["rewrite_ledger"]
        or plan.get("initialization") != manifest.get("initialization")
    ):
        raise ValueError(
            "Derived artifact no longer matches a closed native relocation proof"
        )
