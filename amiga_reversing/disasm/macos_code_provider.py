"""Native selected Classic Mac OS CODE byte provider."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from amiga_reversing.disasm.binary_source import MacosCodeResourceSource
from amiga_reversing.disasm.c_backend import (
    extract_macos_hfs_code_resource_bytes_with_c_backend,
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import read_macos_hfs_image_bytes


def macos_code_resource_byte_view_with_c_backend(
    descriptor: MacosCodeResourceSource,
) -> tuple[dict[str, object], dict[str, object]]:
    if descriptor.resource_type != "CODE":
        raise ValueError(f"Mac CODE byte provider requires CODE resource type, got {descriptor.resource_type}")
    if descriptor.resource_id == 0:
        raise ValueError("Mac CODE 0 is metadata-only and is not a decodable code byte source")
    image_data = read_macos_hfs_image_bytes(descriptor.source_image)
    summary = inspect_macos_hfs_code_summary_with_c_backend(image_data, descriptor.hfs_path)
    resource = _code_resource(summary, descriptor.resource_id)
    selected_range = _selected_code_range(summary, descriptor.resource_id)
    code_bytes = extract_macos_hfs_code_resource_bytes_with_c_backend(
        image_data,
        descriptor.hfs_path,
        descriptor.resource_id,
    )
    if not code_bytes:
        raise ValueError(f"Mac CODE {descriptor.resource_id} has no selected executable bytes")
    provenance = {
        "platform": "macos",
        "source_kind": "macos_code_resource",
        "source_image": _display_source_image(descriptor),
        "hfs_path": descriptor.hfs_path,
        "fork": "resource",
        "resource_type": descriptor.resource_type,
        "resource_id": descriptor.resource_id,
        "resource_name": resource.get("name") or descriptor.resource_name,
        "address_model": str(descriptor.address_model),
        "cache_identity": descriptor.stable_cache_identity,
        "classified_range": selected_range,
    }
    payload: dict[str, object] = {
        "backend": "macos-code",
        "source_kind": "macos_code_resource",
        "wrapped_backend": None,
        "source_descriptor": {
            "kind": str(descriptor.kind),
            "source_image": _display_source_image(descriptor),
            "hfs_path": descriptor.hfs_path,
            "resource_type": descriptor.resource_type,
            "resource_id": descriptor.resource_id,
            "resource_name": resource.get("name") or descriptor.resource_name,
            "address_model": str(descriptor.address_model),
            "cache_identity": descriptor.stable_cache_identity,
            "display_path": descriptor.display_path,
        },
        "provenance": provenance,
        "code_bytes": code_bytes,
        "executable_model": "platform_executable_summary_v1",
        "executable_ranges": [selected_range],
        "executable_deferred": list(_sequence(summary.get("executable_deferred"))),
    }
    profile = {
        "backend": "macos-code",
        "source_kind": "macos_code_resource",
        "wrapped_backend": None,
        "executable_model": "platform_executable_summary_v1",
        "cache_identity": descriptor.stable_cache_identity,
    }
    return payload, profile


def _display_source_image(descriptor: MacosCodeResourceSource) -> str:
    try:
        return str(descriptor.source_image.resolve().relative_to(descriptor.project_root.resolve()).as_posix())
    except ValueError:
        return str(descriptor.source_image.as_posix())


def _code_resource(summary: Mapping[str, object], resource_id: int) -> Mapping[str, object]:
    resource_fork = _mapping(summary.get("resource_fork"))
    for item in _sequence(resource_fork.get("code_resources")):
        resource = _mapping(item)
        if resource.get("id") == resource_id:
            return resource
    raise ValueError(f"Mac CODE {resource_id} resource is missing")


def _selected_code_range(summary: Mapping[str, object], resource_id: int) -> dict[str, object]:
    if summary.get("executable_model") != "platform_executable_summary_v1":
        raise ValueError("Mac CODE byte provider requires shared executable ranges")
    deferred: list[Mapping[str, object]] = []
    for item in _sequence(summary.get("executable_ranges")):
        range_info = _mapping(item)
        if range_info.get("resource_type") != "CODE" or range_info.get("resource_id") != resource_id:
            continue
        if range_info.get("role") in {"code", "candidate_code"} and range_info.get("entrypoint") is True:
            return dict(range_info)
        if range_info.get("fact_status") == "deferred":
            deferred.append(range_info)
    if deferred:
        raise ValueError(f"Mac CODE {resource_id} has deferred byte-entry evidence and no executable byte view")
    raise ValueError(f"Mac CODE {resource_id} has no shared executable code range")


def _mapping(value: object) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
