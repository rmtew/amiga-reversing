"""Normal project/API payload assembly for Classic Mac OS projects."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from amiga_reversing.disasm.c_backend import (
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import (
    MPW_ASM_PATH,
    read_macos_hfs_image_bytes,
)
from amiga_reversing.disasm.macos_project_origin import is_macos_project_origin
from amiga_reversing.disasm.macos_source_project import build_macos_source_project
from amiga_reversing.disasm.macos_source_render import render_macos_source_views
from amiga_reversing.disasm.project_paths import PROJECT_ROOT


def build_macos_project_payload(project: object, *, project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    origin = _mapping(getattr(project, "origin", {}))
    if not is_macos_project_origin(origin):
        raise ValueError("Mac OS project payload requires macos_mpw_fixture origin")
    project_id = str(getattr(project, "id", ""))
    source_files = _read_text_files(project_root, origin.get("source_files"))
    resource_files = _read_text_files(project_root, origin.get("resource_files"))
    build_files = _read_text_files(project_root, origin.get("build_files"))
    source_project = build_macos_source_project(
        project_id=project_id,
        source_files=source_files,
        resource_files=resource_files,
        build_files=build_files,
        c_header_text=_join_text_files(project_root, origin.get("c_header_files")),
        asm_include_text=_join_text_files(project_root, origin.get("asm_include_files")),
    )
    source_render = render_macos_source_views(source_project)
    image_relpath = _required_string(origin, "source_image")
    hfs_path = str(origin.get("hfs_path") or MPW_ASM_PATH)
    hfs_bytes = read_macos_hfs_image_bytes(project_root / image_relpath)
    c_summary = inspect_macos_hfs_code_summary_with_c_backend(hfs_bytes, hfs_path)
    return {
        "schema_version": 1,
        "kind": "macos_project",
        "platform": "macos",
        "source_view": _source_view(source_project, source_render),
        "binary_container_view": _binary_container_view(c_summary, project_id=project_id),
        "source_binary_boundary": {
            "source_project_kind": source_project.get("kind"),
            "binary_container_kind": c_summary.get("container_kind"),
            "source_segments_map_to_observed_code_resources": False,
            "observed_code_fixture": _mapping(c_summary.get("file")).get("path"),
        },
        "unsupported": sorted(
            {
                *[str(item) for item in _sequence(source_project.get("unsupported"))],
                *[str(item) for item in _sequence(c_summary.get("unsupported"))],
            }
        ),
        "provenance": {
            "origin_kind": origin.get("kind"),
            "source_image": image_relpath,
            "hfs_path": hfs_path,
            "source_files": _string_list(origin.get("source_files")),
            "resource_files": _string_list(origin.get("resource_files")),
            "build_files": _string_list(origin.get("build_files")),
            "binary_container_source": "platform_file_lib.macos_hfs_code_summary",
        },
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


def _binary_container_view(c_summary: Mapping[str, object], *, project_id: str) -> dict[str, object]:
    file_info = _mapping(c_summary.get("file"))
    forks = _mapping(file_info.get("forks"))
    data_fork = _mapping(forks.get("data"))
    resource_fork = _mapping(forks.get("resource"))
    resource_summary = _mapping(c_summary.get("resource_fork"))
    code_resources = _sequence(resource_summary.get("code_resources"))
    code0 = _code_resource_by_id(code_resources, 0)
    selected = _mapping(c_summary.get("selected_code"))
    selected_code = _mapping(selected.get("code"))
    code_bytes_offset = selected.get("code_bytes_offset")
    payload_offset = selected.get("payload_offset")
    selected_id = selected.get("id", 1)
    selected_resource = _code_resource_by_id(code_resources, selected_id if isinstance(selected_id, int) else 1)
    selected_name = selected_resource.get("name") or selected.get("name")
    code_segment_map = _sequence(resource_summary.get("code_segment_map"))
    code_resource_details = _code_resource_details(
        code_resources,
        code_segment_map=code_segment_map,
        selected_id=selected_id,
        project_id=project_id,
        unsupported=_sequence(c_summary.get("unsupported")),
    )
    return {
        "kind": c_summary.get("container_kind"),
        "file": file_info,
        "forks": [
            {"name": "data", "role": "data_fork", "size": data_fork.get("size"), "sha256": data_fork.get("sha256")},
            {
                "name": "resource",
                "role": "executable_resource_fork",
                "size": resource_fork.get("size"),
                "sha256": resource_fork.get("sha256"),
                "types": resource_summary.get("types"),
            },
        ],
        "resource_fork": {
            "type_count": resource_summary.get("type_count"),
            "resource_count": resource_summary.get("resource_count"),
            "types": resource_summary.get("types"),
        },
        "code0": {"resource": code0, "metadata": _mapping(code0.get("code"))},
        "code_resources": code_resources,
        "code_segment_map": code_segment_map,
        "code_resource_details": code_resource_details,
        "navigation": _code_resource_navigation(code_resource_details),
        "selected_code_segment": {
            "resource_type": "CODE",
            "id": selected_id,
            "name": selected_name,
            "role": "code_segment",
            "kb_record_id": selected_code.get("kb_record_id"),
            "available": selected.get("available"),
            "payload_size": selected.get("payload_size"),
            "code_bytes_offset": code_bytes_offset,
            "code_entry_offset": (
                code_bytes_offset - payload_offset
                if isinstance(code_bytes_offset, int) and isinstance(payload_offset, int)
                else None
            ),
            "code_bytes_size": selected.get("code_bytes_size"),
            "code_layout": _sequence(selected_code.get("layout_ranges")),
            "orphan_ranges": _sequence(selected_code.get("orphan_ranges")),
            "relocation_fixups": _mapping(selected_code.get("relocation_fixups")),
            "sha256": selected.get("payload_sha256"),
            "code_bytes_sha256": selected.get("code_bytes_sha256"),
            "resource": selected_resource,
            "listing": {
                "project_id": project_id,
                "route": "listing",
                "source_range": {"section_index": 0, "start_offset": 0, "size": selected.get("code_bytes_size")},
                "resource_type": "CODE",
                "resource_id": selected_id,
                "resource_name": selected_name,
                "fork": "resource",
                "payload_size": selected.get("payload_size"),
                "payload_sha256": selected.get("payload_sha256"),
                "code_bytes_sha256": selected.get("code_bytes_sha256"),
                "unsupported": _sequence(c_summary.get("unsupported")),
            },
        },
        "unsupported": _sequence(c_summary.get("unsupported")),
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


def _code_resource_details(
    resources: list[object],
    *,
    code_segment_map: list[object],
    selected_id: object,
    project_id: str,
    unsupported: list[object],
) -> list[dict[str, object]]:
    segment_map_by_id = {
        item.get("resource_id"): item for item in (_mapping(value) for value in code_segment_map) if "resource_id" in item
    }
    all_routine_candidates = [
        {
            **candidate,
            "target_resource_id": segment.get("resource_id"),
            "kb_record_id": segment.get("kb_record_id"),
        }
        for segment in segment_map_by_id.values()
        for candidate in (_mapping(value) for value in _sequence(segment.get("routine_entry_candidates")))
    ]
    details: list[dict[str, object]] = []
    for resource_value in sorted(resources, key=_resource_id_sort_key):
        resource = _mapping(resource_value)
        resource_id = resource.get("id")
        code = _mapping(resource.get("code"))
        segment = _mapping(segment_map_by_id.get(resource_id))
        layout_ranges = _sequence(code.get("layout_ranges"))
        orphan_ranges = _sequence(code.get("orphan_ranges"))
        relocation_fixups = _mapping(code.get("relocation_fixups"))
        role = "code0_metadata" if resource_id == 0 else "code_segment"
        listing = _listing_descriptor(
            resource,
            code=code,
            selected_id=selected_id,
            project_id=project_id,
            unsupported=unsupported,
        )
        anchors = _resource_navigation_anchors(
            resource,
            code=code,
            segment=segment,
            all_routine_candidates=all_routine_candidates,
        )
        details.append(
            {
                "resource_type": "CODE",
                "id": resource_id,
                "name": resource.get("name"),
                "role": role,
                "payload_size": resource.get("payload_size"),
                "payload_sha256": resource.get("sha256"),
                "code_kind": code.get("kind"),
                "kb_record_id": code.get("kb_record_id"),
                "fact_id": code.get("fact_id"),
                "fact_status": code.get("fact_status"),
                "parser_use": code.get("parser_use"),
                "segment_map": segment,
                "code_layout": layout_ranges,
                "orphan_ranges": orphan_ranges,
                "relocation_fixups": relocation_fixups,
                "jump_table": _mapping(code.get("jump_table")),
                "navigation_anchors": anchors,
                "listing": listing,
            }
        )
    return details


def _listing_descriptor(
    resource: Mapping[str, object],
    *,
    code: Mapping[str, object],
    selected_id: object,
    project_id: str,
    unsupported: list[object],
) -> dict[str, object]:
    resource_id = resource.get("id")
    if resource_id == 0:
        return {
            "kind": "metadata",
            "available": False,
            "reason": "CODE 0 is jump-table/application metadata, not ordinary m68k code",
        }
    if resource_id == selected_id:
        code_range = _first_code_range(_sequence(code.get("layout_ranges")))
        return {
            "kind": "full_listing",
            "available": True,
            "project_id": project_id,
            "route": "listing",
            "source_range": {
                "section_index": 0,
                "start_offset": 0,
                "size": code_range.get("size"),
            },
            "resource_type": "CODE",
            "resource_id": resource_id,
            "resource_name": resource.get("name"),
            "fork": "resource",
            "payload_size": resource.get("payload_size"),
            "payload_sha256": resource.get("sha256"),
            "unsupported": unsupported,
        }
    return {
        "kind": "structured_placeholder",
        "available": False,
        "reason": "full per-resource listing deferred until relocation/source-boundary context is represented",
    }


def _resource_navigation_anchors(
    resource: Mapping[str, object],
    *,
    code: Mapping[str, object],
    segment: Mapping[str, object],
    all_routine_candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    resource_id = resource.get("id")
    anchors: list[dict[str, object]] = []
    if resource_id == 0:
        if code.get("fact_id"):
            anchors.append(
                {
                    "kind": "accepted_metadata",
                    "label": "CODE 0 metadata",
                    "resource_id": resource_id,
                    "kb_record_id": code.get("kb_record_id"),
                    "fact_id": code.get("fact_id"),
                    "fact_status": code.get("fact_status"),
                    "parser_use": code.get("parser_use"),
                }
            )
        jump_table = _mapping(code.get("jump_table"))
        if jump_table:
            anchors.append(
                {
                    "kind": "accepted_jump_table",
                    "label": "CODE 0 jump table",
                    "resource_id": resource_id,
                    "offset": jump_table.get("start"),
                    "size": jump_table.get("size"),
                    "kb_record_id": code.get("kb_record_id"),
                    "fact_id": jump_table.get("fact_id"),
                    "fact_status": jump_table.get("fact_status"),
                    "parser_use": jump_table.get("parser_use"),
                }
            )
        for candidate in all_routine_candidates:
            anchors.append(
                {
                    "kind": "candidate_routine_jump_table_entry",
                    "label": f"CODE {candidate.get('target_resource_id')} routine candidate {candidate.get('index')}",
                    "resource_id": resource_id,
                    "target_resource_id": candidate.get("target_resource_id"),
                    "offset": candidate.get("code0_payload_offset"),
                    "kb_record_id": candidate.get("kb_record_id"),
                    "fact_id": candidate.get("fact_id"),
                    "fact_status": candidate.get("fact_status"),
                    "parser_use": candidate.get("parser_use"),
                }
            )
        return anchors
    if segment:
        anchors.append(
            {
                "kind": "accepted_segment_metadata",
                "label": f"CODE {resource_id} segment metadata",
                "resource_id": resource_id,
                "offset": 0,
                "kb_record_id": segment.get("kb_record_id"),
                "fact_id": segment.get("fact_id"),
                "fact_status": segment.get("fact_status"),
                "parser_use": segment.get("parser_use"),
            }
        )
        for candidate in _sequence(segment.get("routine_entry_candidates")):
            candidate_mapping = _mapping(candidate)
            anchors.append(
                {
                    "kind": "candidate_routine_entry",
                    "label": f"CODE {resource_id} routine candidate {candidate_mapping.get('index')}",
                    "resource_id": resource_id,
                    "offset": candidate_mapping.get("routine_offset_from_segment"),
                    "jump_table_offset": candidate_mapping.get("jump_table_offset"),
                    "kb_record_id": segment.get("kb_record_id"),
                    "fact_id": candidate_mapping.get("fact_id"),
                    "fact_status": candidate_mapping.get("fact_status"),
                    "parser_use": candidate_mapping.get("parser_use"),
                }
            )
    for item in _sequence(code.get("layout_ranges")):
        range_info = _mapping(item)
        if range_info.get("kind") == "candidate_code":
            anchors.append(
                {
                    "kind": "candidate_code_range",
                    "label": f"CODE {resource_id} candidate code",
                    "resource_id": resource_id,
                    "offset": range_info.get("start"),
                    "size": range_info.get("size"),
                    "kb_record_id": code.get("kb_record_id"),
                    "fact_id": range_info.get("fact_id"),
                    "fact_status": range_info.get("fact_status"),
                    "parser_use": range_info.get("parser_use"),
                }
            )
    return anchors


def _code_resource_navigation(details: list[dict[str, object]]) -> dict[str, object]:
    anchors = [
        anchor
        for detail in details
        for anchor in _sequence(detail.get("navigation_anchors"))
        if isinstance(anchor, dict)
    ]
    return {
        "groups": [
            {
                "id": "macos-code-resources",
                "label": "CODE resources",
                "items": [
                    {
                        "resource_id": detail.get("id"),
                        "label": f"CODE {detail.get('id')} {detail.get('name') or ''}".strip(),
                        "role": detail.get("role"),
                        "code_kind": detail.get("code_kind"),
                        "kb_record_id": detail.get("kb_record_id"),
                        "fact_id": detail.get("fact_id"),
                        "fact_status": detail.get("fact_status"),
                        "parser_use": detail.get("parser_use"),
                    }
                    for detail in details
                ],
            },
            {
                "id": "macos-code-anchors",
                "label": "CODE anchors",
                "items": anchors,
            },
        ]
    }


def _first_code_range(ranges: list[object]) -> Mapping[str, object]:
    for item in ranges:
        range_info = _mapping(item)
        if range_info.get("kind") in {"confirmed_code", "candidate_code"} and range_info.get("entrypoint") is True:
            return range_info
    return {}


def _resource_id_sort_key(value: object) -> tuple[int, object]:
    resource_id = _mapping(value).get("id")
    return (0, resource_id) if isinstance(resource_id, int) else (1, str(resource_id))


def _code_resource_by_id(resources: list[object], resource_id: int) -> Mapping[str, object]:
    for resource in resources:
        mapping = _mapping(resource)
        if mapping.get("id") == resource_id:
            return mapping
    return {}


def _read_text_files(project_root: Path, value: object) -> dict[str, str]:
    return {path: _read_text(project_root / path) for path in _string_list(value)}


def _join_text_files(project_root: Path, value: object) -> str:
    return "\n".join(_read_text(project_root / path) for path in _string_list(value))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="mac_roman")


def _required_string(origin: Mapping[str, object], key: str) -> str:
    value = origin.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Mac OS project origin missing {key}")
    return value


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, str)]
