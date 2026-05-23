"""Normal project/API payload assembly for Classic Mac OS projects."""

from __future__ import annotations

import tempfile
from collections.abc import Mapping
from pathlib import Path

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    build_listing_artifact_profile_from_binary_source,
    extract_macos_hfs_code_resource_bytes_with_c_backend,
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

MACOS_CODE_PREVIEW_MAX_BYTES = 64
MACOS_APPLICATION_KB_RECORD_ID = "macos.hfs_resource_fork.code_resources.mpw_application"
MACOS_NON_CODE_RESOURCE_FACT_ID = "macos.resource_fork.non_code_metadata.inventory.candidate"


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
        "binary_container_view": _binary_container_view(
            c_summary,
            project_id=project_id,
            source_image=image_relpath,
            hfs_bytes=hfs_bytes,
            hfs_path=hfs_path,
            project_root=project_root,
        ),
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


def _binary_container_view(
    c_summary: Mapping[str, object],
    *,
    project_id: str,
    source_image: str,
    hfs_bytes: bytes,
    hfs_path: str,
    project_root: Path,
) -> dict[str, object]:
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
        source_image=source_image,
        hfs_bytes=hfs_bytes,
        hfs_path=hfs_path,
        project_root=project_root,
        extraction_cache={},
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
            "non_code_resource_details": _non_code_resource_details(_sequence(resource_summary.get("types"))),
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
    source_image: str,
    hfs_bytes: bytes,
    hfs_path: str,
    project_root: Path,
    extraction_cache: dict[tuple[str, str, int], bytes],
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
        preview_windows = _preview_windows(
            resource,
            code=code,
            selected_id=selected_id,
            source_image=source_image,
            hfs_bytes=hfs_bytes,
            hfs_path=hfs_path,
            project_root=project_root,
            extraction_cache=extraction_cache,
        )
        listing = _listing_descriptor(
            resource,
            code=code,
            selected_id=selected_id,
            project_id=project_id,
            unsupported=unsupported,
            preview_windows=preview_windows,
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
                "preview_windows": preview_windows,
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
    preview_windows: list[dict[str, object]],
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
    if preview_windows:
        return {
            "kind": "candidate_preview",
            "available": True,
            "route": "code_preview",
            "reason": "bounded candidate preview; full listing remains deferred",
            "preview_count": len(preview_windows),
        }
    return {
        "kind": "structured_placeholder",
        "available": False,
        "reason": _no_preview_reason(code),
    }


def _preview_windows(
    resource: Mapping[str, object],
    *,
    code: Mapping[str, object],
    selected_id: object,
    source_image: str,
    hfs_bytes: bytes,
    hfs_path: str,
    project_root: Path,
    extraction_cache: dict[tuple[str, str, int], bytes],
) -> list[dict[str, object]]:
    resource_id = resource.get("id")
    if resource_id == 0 or resource_id == selected_id or not isinstance(resource_id, int):
        return []
    range_info = _first_candidate_code_range(_sequence(code.get("layout_ranges")))
    start = _int_value(range_info.get("start"))
    end = _int_value(range_info.get("end"))
    if start is None or end is None or end <= start:
        return []
    payload = _extract_macos_code_resource_payload(
        hfs_bytes,
        source_image=source_image,
        hfs_path=hfs_path,
        resource_id=resource_id,
        project_root=project_root,
        extraction_cache=extraction_cache,
    )
    payload_end = min(end, len(payload))
    if payload_end <= start:
        return []
    preview_end = min(payload_end, start + MACOS_CODE_PREVIEW_MAX_BYTES)
    preview_bytes = payload[start:preview_end]
    relocation_fixups = _mapping(code.get("relocation_fixups"))
    window = {
        "kind": "candidate_code_preview",
        "available": True,
        "bounded": True,
        "route": "code_preview",
        "resource_type": "CODE",
        "resource_id": resource_id,
        "resource_name": resource.get("name"),
        "payload_size": resource.get("payload_size"),
        "payload_sha256": resource.get("sha256"),
        "start": start,
        "end": preview_end,
        "size": len(preview_bytes),
        "candidate_range_start": start,
        "candidate_range_end": end,
        "candidate_range_size": end - start,
        "range_kind": range_info.get("kind"),
        "evidence": range_info.get("evidence"),
        "kb_record_id": code.get("kb_record_id"),
        "fact_id": range_info.get("fact_id"),
        "fact_status": range_info.get("fact_status"),
        "parser_use": range_info.get("parser_use"),
        "truncated": preview_end < payload_end,
        "max_bytes": MACOS_CODE_PREVIEW_MAX_BYTES,
        "reason": "bounded to candidate_code range; byte-entry and relocation semantics remain unresolved",
        "deferred_reasons": _preview_deferred_reasons(relocation_fixups, code),
        "rows": _preview_decode_rows(
            preview_bytes,
            start=start,
            range_info=range_info,
            code=code,
            resource=resource,
            project_root=project_root,
        ),
    }
    return [window]


def _extract_macos_code_resource_payload(
    hfs_bytes: bytes,
    *,
    source_image: str,
    hfs_path: str,
    resource_id: int,
    project_root: Path,
    extraction_cache: dict[tuple[str, str, int], bytes],
) -> bytes:
    cache_key = (source_image, hfs_path, resource_id)
    if cache_key not in extraction_cache:
        extraction_cache[cache_key] = extract_macos_hfs_code_resource_bytes_with_c_backend(
            hfs_bytes,
            hfs_path,
            resource_id,
            project_root=project_root,
        )
    return extraction_cache[cache_key]


def _preview_decode_rows(
    preview_bytes: bytes,
    *,
    start: int,
    range_info: Mapping[str, object],
    code: Mapping[str, object],
    resource: Mapping[str, object],
    project_root: Path,
) -> list[dict[str, object]]:
    if len(preview_bytes) < 2:
        return _preview_data_rows(
            preview_bytes,
            start=start,
            range_info=range_info,
            code=code,
            fallback_reason="preview shorter than one m68k instruction word",
        )

    temp_path: Path | None = None
    artifact = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".macos-preview.bin") as temp_file:
            temp_file.write(preview_bytes)
            temp_path = Path(temp_file.name)
        resource_id = resource.get("id")
        resource_label = f"CODE {resource_id} {resource.get('name') or ''}".strip()
        binary_source = RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=temp_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=f"Mac OS candidate preview {resource_label}",
            analysis_cache_path=project_root / "targets" / ".macos-code-preview.analysis",
        )
        _total_rows, _profile, artifact = build_listing_artifact_profile_from_binary_source(
            binary_source,
            project_root=project_root,
        )
        window, _window_profile = artifact.window_payload(start=0, count=MACOS_CODE_PREVIEW_MAX_BYTES * 2)
        rows = _decoded_preview_rows(
            _sequence(window.get("rows")),
            preview_bytes=preview_bytes,
            start=start,
            range_info=range_info,
            code=code,
        )
    except Exception as error:
        return _preview_data_rows(
            preview_bytes,
            start=start,
            range_info=range_info,
            code=code,
            fallback_reason=f"preview decode failed: {type(error).__name__}",
        )
    finally:
        if artifact is not None:
            artifact.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    if not any(row.get("decoded") is True for row in rows):
        return _preview_data_rows(
            preview_bytes,
            start=start,
            range_info=range_info,
            code=code,
            fallback_reason="preview decode produced no instruction rows",
        )
    return rows


def _decoded_preview_rows(
    decoded_rows: list[object],
    *,
    preview_bytes: bytes,
    start: int,
    range_info: Mapping[str, object],
    code: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw_row in decoded_rows:
        decoded = _mapping(raw_row)
        row_start = _int_value(decoded.get("start_offset"))
        row_end = _int_value(decoded.get("end_offset"))
        if row_start is None or row_end is None or row_end <= row_start:
            continue
        if row_start >= len(preview_bytes) or row_end > len(preview_bytes):
            continue
        text = str(decoded.get("text") or "").strip()
        if not text or text.lower() == "section code,code":
            continue
        row_kind = str(decoded.get("kind") or "")
        if row_kind not in {"instruction", "data"}:
            continue
        chunk = preview_bytes[row_start:row_end]
        is_instruction = row_kind == "instruction"
        rows.append(
            {
                "offset": start + row_start,
                "end": start + row_end,
                "size": row_end - row_start,
                "bytes": str(decoded.get("bytes") or chunk.hex(" ")),
                "text": text,
                "row_kind": row_kind,
                "decoded": is_instruction,
                "decode_status": "decoded" if is_instruction else "decoded_data",
                "fallback_reason": None,
                "opcode_or_directive": decoded.get("opcode_or_directive"),
                "operand_text": decoded.get("operand_text"),
                "range_kind": range_info.get("kind"),
                "evidence": range_info.get("evidence"),
                "kb_record_id": code.get("kb_record_id"),
                "fact_id": range_info.get("fact_id"),
                "fact_status": range_info.get("fact_status"),
                "parser_use": range_info.get("parser_use"),
            }
        )
    return rows


def _preview_data_rows(
    preview_bytes: bytes,
    *,
    start: int,
    range_info: Mapping[str, object],
    code: Mapping[str, object],
    fallback_reason: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative in range(0, len(preview_bytes), 2):
        chunk = preview_bytes[relative : relative + 2]
        offset = start + relative
        byte_text = chunk.hex(" ")
        value = int.from_bytes(chunk, "big")
        directive = "dc.w" if len(chunk) == 2 else "dc.b"
        rows.append(
            {
                "offset": offset,
                "end": offset + len(chunk),
                "size": len(chunk),
                "bytes": byte_text,
                "directive": directive,
                "value": value,
                "text": f"{directive} ${value:0{len(chunk) * 2}x}",
                "row_kind": "data",
                "decoded": False,
                "decode_status": "fallback_data",
                "fallback_reason": fallback_reason,
                "range_kind": range_info.get("kind"),
                "evidence": range_info.get("evidence"),
                "kb_record_id": code.get("kb_record_id"),
                "fact_id": range_info.get("fact_id"),
                "fact_status": range_info.get("fact_status"),
                "parser_use": range_info.get("parser_use"),
            }
        )
    return rows


def _preview_deferred_reasons(
    relocation_fixups: Mapping[str, object],
    code: Mapping[str, object],
) -> list[dict[str, object]]:
    if not relocation_fixups:
        return [
            {
                "scope": "relocation_fixups",
                "kb_record_id": code.get("kb_record_id"),
                "fact_id": "macos.segment_loader.relocation_fixups.deferred",
                "fact_status": "deferred",
                "parser_use": "deferred_only",
                "reason": "Segment Loader relocation/fixup interpretation is not represented in this preview",
            }
        ]
    return [
        {
            "scope": "relocation_fixups",
            "kb_record_id": code.get("kb_record_id"),
            "fact_id": relocation_fixups.get("fact_id"),
            "fact_status": relocation_fixups.get("fact_status"),
            "parser_use": relocation_fixups.get("parser_use"),
            "reason": relocation_fixups.get("reason")
            or "Segment Loader relocation/fixup interpretation is not represented in this preview",
        }
    ]


def _non_code_resource_details(resource_types: list[object]) -> list[dict[str, object]]:
    return [
        {
            "resource_type": resource_type.get("type"),
            "resource_count": resource_type.get("count"),
            "role": "resource_metadata_inventory",
            "semantic_status": "candidate",
            "payload_decode_status": "unsupported",
            "kb_record_id": MACOS_APPLICATION_KB_RECORD_ID,
            "fact_id": MACOS_NON_CODE_RESOURCE_FACT_ID,
            "fact_status": "candidate",
            "parser_use": "candidate_only",
            "evidence": "resource fork type inventory; payload semantics are not decoded",
            "inventory_source": "platform_file_lib.macos_hfs_code_summary resource_fork.types",
            "reason": "non-CODE resource metadata is inventory-only and not executable CODE",
        }
        for resource_type in (_mapping(value) for value in resource_types)
        if resource_type.get("type") != "CODE"
    ]


def _no_preview_reason(code: Mapping[str, object]) -> str:
    deferred = next(
        (item for item in (_mapping(value) for value in _sequence(code.get("layout_ranges"))) if item.get("kind") == "deferred"),
        {},
    )
    if deferred:
        return f"no candidate preview range; classifier deferred byte-entry evidence: {deferred.get('evidence')}"
    return "no candidate_code range available for a bounded preview"


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
        for raw_candidate in _sequence(segment.get("routine_entry_candidates")):
            candidate_mapping = _mapping(raw_candidate)
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


def _first_candidate_code_range(ranges: list[object]) -> Mapping[str, object]:
    for item in ranges:
        range_info = _mapping(item)
        if range_info.get("kind") == "candidate_code":
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


def _int_value(value: object) -> int | None:
    return value if isinstance(value, int) else None
