"""Web payload shape for the Classic Mac OS starter view."""

from __future__ import annotations

from collections.abc import Mapping


def build_macos_starter_web_payload(
    *,
    source_project: Mapping[str, object],
    source_render: Mapping[str, object],
    asm_container: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "macos_starter_view",
        "platform": "macos",
        "source_view": _source_view(source_project, source_render),
        "binary_container_view": _binary_container_view(asm_container),
        "source_binary_boundary": {
            "source_project_kind": source_project.get("kind"),
            "binary_container_kind": asm_container.get("container_kind"),
            "source_segments_map_to_observed_code_resources": False,
            "observed_code_fixture": _mapping(asm_container.get("file")).get("path"),
        },
        "unsupported": sorted(
            {
                *[str(item) for item in _sequence(source_project.get("unsupported"))],
                *[str(item) for item in _sequence(asm_container.get("unsupported"))],
            }
        ),
    }


def _source_view(source_project: Mapping[str, object], source_render: Mapping[str, object]) -> dict[str, object]:
    entities = _mapping(source_project.get("entities"))
    return {
        "kind": source_project.get("kind"),
        "project_model": source_project.get("project_model"),
        "pivots": {
            "source_files": _sequence(entities.get("source_files")),
            "segments": _sequence(entities.get("segments")),
            "routines": _sequence(entities.get("routines")),
            "resources": _sequence(entities.get("resource_declarations")),
            "build_products": _sequence(entities.get("build_products")),
            "api_facts": _sequence(source_project.get("mac_os_annotations")),
        },
        "routine_views": _sequence(source_render.get("routine_views")),
        "product_views": _sequence(source_render.get("product_views")),
        "unsupported": _sequence(source_project.get("unsupported")),
    }


def _binary_container_view(asm_container: Mapping[str, object]) -> dict[str, object]:
    file_info = _mapping(asm_container.get("file"))
    data_fork = _mapping(asm_container.get("data_fork"))
    resource_fork = _mapping(asm_container.get("resource_fork"))
    native_source = _native_source_identity(asm_container)
    selected = _mapping(asm_container.get("selected_code_segment"))
    selected_with_source = dict(selected)
    if selected_with_source:
        selected_with_source["native_source"] = dict(native_source)
        selected_with_source.setdefault("restored_source", _restored_source_from_selected_code(selected_with_source))
    return {
        "kind": asm_container.get("container_kind"),
        "native_source": native_source,
        "file": file_info,
        "forks": [
            {
                "name": "data",
                "role": data_fork.get("role"),
                "size": data_fork.get("size"),
                "sha256": data_fork.get("sha256"),
            },
            {
                "name": "resource",
                "role": resource_fork.get("role"),
                "size": resource_fork.get("size"),
                "sha256": resource_fork.get("sha256"),
                "types": resource_fork.get("types"),
            },
        ],
        "code0": asm_container.get("code0"),
        "code_resources": _sequence(asm_container.get("code_resources")),
        "selected_code_segment": selected_with_source or asm_container.get("selected_code_segment"),
        "unsupported": _sequence(asm_container.get("unsupported")),
        "source_mapping": {
            "maps_to_sample_source": False,
            "reason": "observed MPW/Tools/Asm CODE resources are not inferred from Sample source segments",
        },
        "finder": {
            "type": file_info.get("type"),
            "creator": file_info.get("creator"),
            "cnid": file_info.get("cnid"),
        },
    }


def _native_source_identity(asm_container: Mapping[str, object]) -> dict[str, object]:
    selected = _mapping(asm_container.get("selected_code_segment"))
    resource_id = selected.get("id", 1)
    source_image = str(asm_container.get("source_image") or "")
    hfs_path = str(_mapping(asm_container.get("file")).get("path") or "")
    return {
        "kind": "macos_code_resource",
        "backend": "macos-code",
        "source_kind": "macos_code_resource",
        "source_image": source_image,
        "hfs_path": hfs_path,
        "resource_type": "CODE",
        "resource_id": resource_id,
        "resource_name": selected.get("name"),
        "address_model": "macos_code_resource_offset",
        "cache_identity": f"macos-code-resource:{source_image}:{hfs_path}:CODE:{resource_id}",
        "wrapped_backend": None,
    }


def _restored_source_from_selected_code(selected: Mapping[str, object]) -> dict[str, object]:
    payload_size = selected.get("payload_size") if isinstance(selected.get("payload_size"), int) else 0
    ranges = []
    cursor = 0
    for item in sorted((_mapping(value) for value in _sequence(selected.get("code_layout"))), key=_range_start):
        start = item.get("start") if isinstance(item.get("start"), int) else None
        end = item.get("end") if isinstance(item.get("end"), int) else None
        if start is None or end is None or end <= start:
            continue
        if start > cursor:
            ranges.append(_unknown_range(cursor, start))
        ranges.append(
            {
                "role": _role_for_layout_kind(item.get("kind")),
                "byte_space": "code_resource_payload",
                "platform": "macos",
                "source_kind": "macos_code_resource",
                "start": start,
                "size": end - start,
                "end": end,
                "status": item.get("fact_status"),
                "reason": item.get("evidence") or "Mac CODE layout range from C-backed resource summary",
                "provenance": "platform_file_lib.macos_hfs_code_summary",
                "source_visible": True,
                "fact_id": item.get("fact_id"),
                "fact_status": item.get("fact_status"),
                "parser_use": item.get("parser_use"),
            }
        )
        cursor = max(cursor, end)
    if payload_size > cursor:
        ranges.append(_unknown_range(cursor, payload_size))
    references = [
        {
            "kind": "segment_loader_fixup_placeholder",
            "ownership_range_index": _first_candidate_range_index(ranges),
            "target": "unresolved_segment_loader_fixup",
            "status": "deferred",
            "reason": "Segment Loader relocation/fixup bytes and effects are deferred in the executable-format KB.",
            "provenance": "platform_file_lib.macos_hfs_code_summary",
            "source_visible": True,
            "fact_id": "macos.segment_loader.relocation_fixups.deferred",
            "fact_status": "deferred",
            "parser_use": "deferred_only",
        }
    ]
    return {
        "model": "restored_source_model_v1",
        "platform": "macos",
        "source_kind": "macos_code_resource",
        "round_trip_required": False,
        "source_ownership_ranges": ranges,
        "source_coverage_verifier": {
            "ok": True,
            "gap_count": 0,
            "overlap_count": 0,
            "invalid_instruction_ownership_count": 0,
            "explicit_unknown_missing_detail_count": 0,
        },
        "source_reference_records": references,
        "platform_extensions": {
            "code_resource": {
                "resource_type": "CODE",
                "resource_id": selected.get("id"),
                "resource_name": selected.get("name"),
                "payload_size": payload_size,
            },
            "a5_world": {
                "status": "deferred",
                "reason": "Classic Mac A5/world conventions are platform context, not round-trip proof.",
            },
        },
    }


def _unknown_range(start: int, end: int) -> dict[str, object]:
    return {
        "role": "unknown",
        "byte_space": "code_resource_payload",
        "platform": "macos",
        "source_kind": "macos_code_resource",
        "start": start,
        "size": end - start,
        "end": end,
        "status": "deferred",
        "reason": "No accepted or candidate Mac CODE layout evidence covers this payload span.",
        "provenance": "platform_file_lib.macos_hfs_code_summary",
        "source_visible": True,
    }


def _role_for_layout_kind(kind: object) -> str:
    if kind == "metadata":
        return "metadata"
    if kind == "data":
        return "data"
    if kind == "candidate_code":
        return "candidate_code"
    if kind == "confirmed_code":
        return "code"
    return "unknown"


def _first_candidate_range_index(ranges: list[dict[str, object]]) -> int | None:
    for index, item in enumerate(ranges):
        if item.get("role") == "candidate_code":
            return index
    return 0 if ranges else None


def _range_start(value: object) -> int:
    start = _mapping(value).get("start")
    return start if isinstance(start, int) else 0


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
