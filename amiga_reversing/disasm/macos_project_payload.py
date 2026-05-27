"""Normal project/API payload assembly for Classic Mac OS projects."""

from __future__ import annotations

import json
import re
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path

from amiga_reversing.disasm.c_backend import (
    build_macos_code_bytes_listing_artifact_profile,
    extract_macos_hfs_code_resource_bytes_with_c_backend,
    extract_macos_hfs_code_resource_payload_bytes_with_c_backend,
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import (
    MPW_ASM_PATH,
    read_macos_hfs_image_bytes,
)
from amiga_reversing.disasm.macos_project_origin import (
    is_macos_project_origin,
    macos_code_source_descriptor_from_project,
)
from amiga_reversing.disasm.macos_source_project import build_macos_source_project
from amiga_reversing.disasm.macos_source_render import render_macos_source_views
from amiga_reversing.disasm.project_paths import PROJECT_ROOT

MACOS_CODE_PREVIEW_MAX_BYTES = 64
MACOS_APPLICATION_KB_RECORD_ID = "macos.hfs_resource_fork.code_resources.mpw_application"
MACOS_NON_CODE_RESOURCE_FACT_ID = "macos.resource_fork.non_code_metadata.inventory.candidate"
MACOS_CURS_RESOURCE_FACT_ID = "macos.resource_fork.curs.layout.accepted"
_RAW_LOCAL_LABEL_RE = re.compile(r"\bloc_0_([0-9A-Fa-f]{8})\b")


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
    source_descriptor = macos_code_source_descriptor_from_project(project, project_root=project_root)
    native_source_identity = _native_source_identity(source_descriptor, source_image=image_relpath)
    hfs_bytes = read_macos_hfs_image_bytes(project_root / image_relpath)
    c_summary = inspect_macos_hfs_code_summary_with_c_backend(hfs_bytes, hfs_path)
    return {
        "schema_version": 1,
        "kind": "macos_project",
        "platform": "macos",
        "native_source": native_source_identity,
        "source_view": _source_view(source_project, source_render),
        "binary_container_view": _binary_container_view(
            c_summary,
            project_id=project_id,
            source_image=image_relpath,
            native_source=native_source_identity,
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
            "native_source_kind": "macos_code_resource",
        },
    }


def _native_source_identity(descriptor: object, *, source_image: str) -> dict[str, object]:
    return {
        "kind": str(descriptor.kind),
        "backend": "macos-code",
        "source_kind": "macos_code_resource",
        "source_image": source_image,
        "hfs_path": descriptor.hfs_path,
        "resource_type": descriptor.resource_type,
        "resource_id": descriptor.resource_id,
        "resource_name": descriptor.resource_name,
        "address_model": str(descriptor.address_model),
        "cache_identity": descriptor.stable_cache_identity,
        "wrapped_backend": None,
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
    native_source: Mapping[str, object],
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
    non_code_details = _non_code_resource_details(_sequence(resource_summary.get("types")))
    executable_placeholders = _executable_resource_placeholders(
        non_code_details,
        source_image=source_image,
        hfs_path=hfs_path,
    )
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
    selected_restored_source = _c_owned_restored_source_packet(selected_code, scope="selected CODE")
    source_body_sections = _code_source_body_sections(
        code_resource_details,
        selected_id=selected_id,
        selected_code_segment={
            "code_entry_offset": (
                code_bytes_offset - payload_offset
                if isinstance(code_bytes_offset, int) and isinstance(payload_offset, int)
                else None
            ),
            "code_bytes_size": selected.get("code_bytes_size"),
            "code_bytes_sha256": selected.get("code_bytes_sha256"),
        },
        native_source=native_source,
    )
    source_quality_gate = _source_quality_gate(source_body_sections, code_resource_details)
    return {
        "kind": c_summary.get("container_kind"),
        "native_source": dict(native_source),
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
            "non_code_resource_details": non_code_details,
            "executable_resource_placeholders": executable_placeholders,
        },
        "code0": {"resource": code0, "metadata": _mapping(code0.get("code"))},
        "code_resources": code_resources,
        "code_segment_map": code_segment_map,
        "code_resource_details": code_resource_details,
        "source_body_sections": source_body_sections,
        "source_quality_gate": source_quality_gate,
        "navigation": _code_resource_navigation(code_resource_details),
        "selected_code_segment": {
            "native_source": dict(native_source),
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
            "restored_source": selected_restored_source,
            "sha256": selected.get("payload_sha256"),
            "code_bytes_sha256": selected.get("code_bytes_sha256"),
            "resource": selected_resource,
            "listing": {
                "backend": "macos-code",
                "source_kind": "macos_code_resource",
                "native_source": dict(native_source),
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
                "restored_source": selected_restored_source,
                "unsupported": _sequence(c_summary.get("unsupported")),
            },
        },
        "unsupported": _sequence(c_summary.get("unsupported")),
        "executable_resource_placeholders": executable_placeholders,
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


def _code_source_body_sections(
    details: list[dict[str, object]],
    *,
    selected_id: object,
    selected_code_segment: Mapping[str, object],
    native_source: Mapping[str, object],
) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    code0_routing_xrefs = _code0_routing_xrefs(details)
    incoming_by_target: dict[object, list[dict[str, object]]] = {}
    for xref in code0_routing_xrefs:
        incoming_by_target.setdefault(xref.get("target_resource_id"), []).append(xref)
    for detail in details:
        resource_id = detail.get("id")
        section = {
            "source_section_id": f"macos-code-CODE-{resource_id}",
            "label": f"CODE_{resource_id}",
            "source_kind": native_source.get("source_kind") or "macos_code_resource",
            "backend": native_source.get("backend") or "macos-code",
            "status": _code_source_section_status(detail, selected_id=selected_id),
            "source_visible": True,
            "resource_type": detail.get("resource_type"),
            "id": resource_id,
            "name": detail.get("name"),
            "role": detail.get("role"),
            "code_kind": detail.get("code_kind"),
            "kb_record_id": detail.get("kb_record_id"),
            "payload_size": detail.get("payload_size"),
            "payload_sha256": detail.get("payload_sha256"),
            "presentation": detail.get("source_presentation_status"),
            "listing": detail.get("listing"),
            "restored_source": detail.get("restored_source"),
            "source_body_ranges": _source_body_ranges(detail),
            "semantic_source": detail.get("semantic_source"),
            "incoming_code0_xrefs": incoming_by_target.get(resource_id, []),
            "preview_windows": detail.get("preview_windows"),
            "source_envelope": _code_source_envelope(detail),
        }
        if resource_id == 0:
            jump_table = _mapping(detail.get("jump_table"))
            section["code0_structured_context"] = {
                "jump_table": {
                    **jump_table,
                    "kb_record_id": jump_table.get("kb_record_id") or detail.get("kb_record_id"),
                },
                "jump_table_rows": _source_jump_table_rows(detail),
                "generated_routing_xrefs": code0_routing_xrefs,
            }
        if resource_id == selected_id:
            section["selected_listing_context"] = dict(selected_code_segment)
            if resource_id == 1:
                section["code1_layout_context"] = _code1_layout_context(detail, selected_code_segment)
        sections.append(section)
    return sections


def _code_source_section_status(detail: Mapping[str, object], *, selected_id: object) -> str:
    if detail.get("id") == selected_id:
        return "selected_full_listing"
    semantic_source = _mapping(detail.get("semantic_source"))
    if semantic_source.get("status") == "decoded":
        return "semantic_source"
    presentation = _mapping(detail.get("source_presentation_status"))
    listing = _mapping(detail.get("listing"))
    if presentation.get("status") == "covered" and listing.get("available") is True:
        return "partial_preview_with_exact_placeholders"
    if presentation.get("status") == "covered":
        return "covered_placeholder"
    return str(presentation.get("status") or "deferred_placeholder")


def _source_body_ranges(detail: Mapping[str, object]) -> list[dict[str, object]]:
    kb_record_id = detail.get("kb_record_id")
    return [_source_body_range(item, kb_record_id=kb_record_id) for item in _sequence(detail.get("code_layout"))]


def _source_body_range(item: object, *, kb_record_id: object) -> dict[str, object]:
    range_info = {**_mapping(item), "kb_record_id": _mapping(item).get("kb_record_id") or kb_record_id}
    if range_info.get("kind") == "candidate_unresolved_prefix":
        range_info.setdefault(
            "reason",
            (
                "bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached "
                "through loader/stack/fixup flow not yet modeled"
            ),
        )
    elif range_info.get("kind") == "data" and range_info.get("evidence") == "prefix_before_stack_entry":
        range_info["parser_range_kind"] = "data"
        range_info["kind"] = "candidate_unresolved_prefix"
        range_info["reason"] = (
            "bytes precede candidate stack-entry boundary; they are not proven data and may contain code reached "
            "through loader/stack/fixup flow not yet modeled"
        )
    return range_info


def _source_jump_table_rows(detail: Mapping[str, object]) -> list[dict[str, object]]:
    kb_record_id = detail.get("kb_record_id")
    rows: list[dict[str, object]] = []
    for item in _sequence(detail.get("jump_table_rows")):
        row = dict(_mapping(item))
        for key in ("accepted_layout", "candidate_target"):
            child = _mapping(row.get(key))
            if child:
                row[key] = {**child, "kb_record_id": child.get("kb_record_id") or kb_record_id}
        rows.append(row)
    return rows


def _code0_routing_xrefs(details: list[dict[str, object]]) -> list[dict[str, object]]:
    code0_detail = next((detail for detail in details if detail.get("id") == 0), None)
    if not code0_detail:
        return []
    details_by_id = {detail.get("id"): detail for detail in details}
    xrefs: list[dict[str, object]] = []
    for row in _source_jump_table_rows(code0_detail):
        code0_offset = _int_value(row.get("code0_payload_offset"))
        target_id = row.get("target_resource_id")
        routine_offset = _int_value(row.get("routine_offset_from_segment"))
        entry_index = _int_value(row.get("entry_index"))
        target_offset = _code0_target_payload_offset(
            details_by_id.get(target_id),
            routine_offset,
            routine_offset_space=_text(row.get("routine_offset_space") or "candidate_code_range"),
        )
        if code0_offset is None or target_id is None or routine_offset is None or target_offset is None:
            continue
        target_detail = details_by_id.get(target_id)
        candidate = _mapping(row.get("candidate_target"))
        accepted = _mapping(row.get("accepted_layout"))
        xrefs.append(
            {
                "kind": "generated_code0_routing_xref",
                "source_resource_id": 0,
                "source_payload_offset": code0_offset,
                "source_label": f"CODE_0_jump_table_entry_{_text(entry_index)}",
                "entry_index": entry_index,
                "target_resource_id": target_id,
                "target_payload_offset": target_offset,
                "routine_offset_from_segment": routine_offset,
                "target_label": _code0_routing_target_label(
                    target_detail,
                    target_id=target_id,
                    target_offset=target_offset,
                ),
                "link_status": "linked_candidate",
                "accepted_layout": accepted,
                "candidate_target": candidate,
            }
        )
    return xrefs


def _code0_routing_target_label(
    target_detail: Mapping[str, object] | None,
    *,
    target_id: object,
    target_offset: int,
) -> str:
    semantic_source = _mapping(_mapping(target_detail).get("semantic_source"))
    for row in _sequence(semantic_source.get("rows")):
        row_info = _mapping(row)
        if row_info.get("kind") != "label":
            continue
        if _int_value(row_info.get("payload_offset")) == target_offset:
            return f"CODE_{_text(target_id)}_loc_{target_offset:08x}"
    return f"CODE_{_text(target_id)}_routine_candidate_{target_offset:08x}"


def _code0_target_payload_offset(
    detail: Mapping[str, object] | None,
    routine_offset: int | None,
    *,
    routine_offset_space: str = "candidate_code_range",
) -> int | None:
    if not detail or routine_offset is None or routine_offset < 0:
        return None
    for item in _sequence(detail.get("code_layout")):
        range_info = _mapping(item)
        if range_info.get("kind") not in {"candidate_code", "confirmed_code", "code"}:
            continue
        start = _int_value(range_info.get("start"))
        end = _int_value(range_info.get("end"))
        if start is None or end is None:
            continue
        if routine_offset_space == "code_resource_payload":
            if start <= routine_offset < end:
                return routine_offset
            continue
        target_offset = start + routine_offset
        if start <= target_offset < end:
            return target_offset
    return None


def _code_source_envelope(detail: Mapping[str, object]) -> dict[str, object]:
    semantic_source = _mapping(detail.get("semantic_source"))
    return {
        "kind": "source_envelope",
        "resource_type": detail.get("resource_type"),
        "resource_id": detail.get("id"),
        "start": 0,
        "end": detail.get("payload_size"),
        "size": detail.get("payload_size"),
        "payload_sha256": detail.get("payload_sha256"),
        "reason": _byte_preserving_envelope_reason(detail, semantic_source),
    }


def _byte_preserving_envelope_reason(
    detail: Mapping[str, object],
    semantic_source: Mapping[str, object],
) -> str:
    if detail.get("id") == 0:
        return "CODE 0 is accepted routing/application metadata; source rows render metadata and jump-table entries."
    if semantic_source.get("status") == "decoded":
        return (
            "semantic source rows are rendered for decoded C-owned ranges; remaining byte gaps stay explicit without "
            "promoting byte-entry, A5, or Segment Loader semantics."
        )
    return (
        "semantic source rows are not available for this CODE resource; the source body keeps exact bytes and evidence "
        "status without promoting byte-entry, A5, or Segment Loader semantics."
    )


def _source_quality_gate(
    sections: list[dict[str, object]],
    details: list[dict[str, object]],
) -> dict[str, object]:
    section_by_id = {section.get("id"): section for section in sections}
    rows = [
        _source_quality_resource_row(detail, section_by_id.get(detail.get("id")))
        for detail in details
    ]
    checklist = {
        "source_first_artifact": True,
        "all_code_sections_visible": all(row["section_visible"] is True for row in rows),
        "range_ownership_complete": all(row["ownership_complete"] is True for row in rows),
        "no_vague_orphan_bucket": all(row["orphan_bucket_present"] is False for row in rows),
        "renderer_uses_durable_rows": all(row["renders_durable_source_rows"] is True for row in rows),
        "stable_labels_present": all(row["stable_labels_present"] is True for row in rows),
        "residuals_explicit": all(row["residuals_explicit"] is True for row in rows),
        "reachable_code_evidence_recorded": all(row["reachable_code_evidence_recorded"] is True for row in rows),
        "xref_target_labels_resolved": all(row["xref_target_labels_resolved"] is True for row in rows),
    }
    semantic_rows = [row for row in rows if row["executable_body_span_count"]]
    checklist["recursive_control_target_xrefs_present"] = any(
        row["recursive_control_target_xrefs"] > 0 for row in semantic_rows
    )
    byte_real_only_bodies = [row for row in semantic_rows if row["semantic_instruction_row_count"] == 0]
    semantic_decode_gap_bodies = [
        row
        for row in semantic_rows
        if any(_mapping(item).get("kind") == "semantic_decode_gap" for item in row["residuals"])
    ]
    semantic_components = {
        "byte_preservation_status": "byte_real_complete" if all(checklist.values()) else "blocked",
        "source_ordering_status": "source_first" if checklist["source_first_artifact"] else "blocked",
        "semantic_disassembly_status": (
            "byte_real_only"
            if byte_real_only_bodies
            else "semantic_instruction_rows_present"
        ),
        "label_xref_status": (
            "generated_labels_without_xrefs"
            if all(row["generated_label_count"] for row in rows)
            and not any(row["generated_xref_count"] for row in rows)
            else "generated_labels_and_xrefs_present"
        ),
        "residual_status": "explicit" if checklist["residuals_explicit"] else "blocked",
    }
    semantic_closeout_status = (
        "blocked_byte_real_only"
        if byte_real_only_bodies
        else "semantic_source_complete_for_known_bounds"
        if all(checklist.values())
        else "blocked"
    )
    return {
        "kind": "macos_source_quality_gate_v1",
        "status": "byte_real_baseline" if all(checklist.values()) else "blocked",
        "semantic_closeout_status": semantic_closeout_status,
        "scope": "current MPW Tools Asm fixture",
        "baseline_status": "passed_with_deferred_semantics",
        "baseline_status_meaning": (
            "byte preservation, source ordering, labels, and residual accounting are present; "
            "this is not semantic source closeout"
        ),
        "semantic_components": semantic_components,
        "semantic_decode_gap_resource_count": len(semantic_decode_gap_bodies),
        "does_not_claim": [
            "accepted byte-entry proof",
            "decoded Segment Loader relocation/fixup semantics",
            "A5 lifetime proof",
            "resource-fork round trip",
        ],
        "non_blocking_for_semantic_disassembly": [
            "missing human semantic names",
            "missing original source symbols",
            "deferred A5 lifetime proof",
            "deferred Segment Loader fixup decoding for current zero-offset fixture spans",
        ],
        "checklist": checklist,
        "resources": rows,
    }


def _source_quality_resource_row(
    detail: Mapping[str, object],
    section: Mapping[str, object] | None,
) -> dict[str, object]:
    section = section or {}
    resource_id = detail.get("id")
    ranges = [_mapping(item) for item in _sequence(section.get("source_body_ranges"))]
    payload_size = _int_value(detail.get("payload_size")) or 0
    labels = _source_quality_labels(detail, section)
    reachable = _source_quality_reachable_evidence(detail, section)
    semantic_source = _mapping(section.get("semantic_source"))
    semantic_rows = [_mapping(item) for item in _sequence(semantic_source.get("rows"))]
    semantic_instruction_count = sum(1 for item in semantic_rows if item.get("kind") == "instruction")
    semantic_data_count = sum(1 for item in semantic_rows if _semantic_row_is_durable_data(item))
    semantic_xref_count = sum(len(_sequence(item.get("xrefs"))) for item in semantic_rows)
    semantic_xref_reason_counts = _semantic_xref_reason_counts(semantic_rows)
    semantic_label_names = _semantic_label_names(semantic_rows)
    semantic_xref_target_labels = _semantic_xref_target_labels(semantic_rows)
    unresolved_xref_target_labels = sorted(semantic_xref_target_labels - semantic_label_names)
    residuals = _source_quality_residuals(
        detail,
        ranges,
        payload_size=payload_size,
        semantic_rows=semantic_rows,
        candidate_residuals=[_mapping(item) for item in _sequence(semantic_source.get("candidate_residuals"))],
        semantic_gap_residuals=[_mapping(item) for item in _sequence(semantic_source.get("semantic_gap_residuals"))],
    )
    executable_body_spans = [
        item
        for item in ranges
        if item.get("kind") in {"confirmed_code", "candidate_code", "code"}
        and _int_value(item.get("end")) is not None
        and (_int_value(item.get("end")) or 0) > (_int_value(item.get("start")) or 0)
    ]
    return {
        "resource_id": resource_id,
        "resource_name": detail.get("name"),
        "section_id": section.get("source_section_id"),
        "section_label": section.get("label"),
        "section_visible": section.get("source_visible") is True,
        "ownership_kinds": sorted({_text(item.get("kind")) for item in ranges}),
        "ownership_complete": _ranges_cover_payload(ranges, payload_size=payload_size),
        "orphan_bucket_present": any("orphan" in str(item.get("kind") or "").lower() for item in ranges),
        "legacy_orphan_ranges_reclassified": len(_sequence(detail.get("orphan_ranges"))),
        "renders_durable_source_rows": True,
        "executable_body_span_count": len(executable_body_spans),
        "semantic_instruction_row_count": semantic_instruction_count,
        "semantic_data_row_count": semantic_data_count,
        "byte_real_only_executable_body": bool(executable_body_spans) and semantic_instruction_count == 0,
        "stable_labels_present": bool(labels),
        "labels": labels,
        "generated_label_count": len(labels),
        "generated_xref_count": semantic_xref_count,
        "generated_xref_reason_counts": semantic_xref_reason_counts,
        "recursive_control_target_xrefs": semantic_xref_reason_counts.get("control_target", 0),
        "xref_target_label_count": len(semantic_xref_target_labels),
        "unresolved_xref_target_label_count": len(unresolved_xref_target_labels),
        "xref_target_labels_resolved": not unresolved_xref_target_labels,
        "unresolved_xref_target_labels": unresolved_xref_target_labels[:20],
        "human_semantic_names_required": False,
        "residuals_explicit": all(item.get("status") in {"candidate", "deferred"} for item in residuals),
        "residuals": residuals,
        "reachable_code_evidence_recorded": bool(reachable),
        "reachable_code_evidence": reachable,
        "next_required_implementation": _source_quality_next_step(
            detail,
            residuals,
            semantic_instruction_count=semantic_instruction_count,
        ),
    }


def _semantic_xref_reason_counts(rows: list[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for xref in (_mapping(value) for value in _sequence(row.get("xrefs"))):
            reason = _text(xref.get("reason"))
            if not reason:
                continue
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def _semantic_label_names(rows: list[Mapping[str, object]]) -> set[str]:
    labels: set[str] = set()
    for row in rows:
        if row.get("kind") != "label":
            continue
        resource_id = row.get("resource_id")
        payload_offset = _int_value(row.get("payload_offset"))
        if resource_id is None or payload_offset is None:
            continue
        labels.add(f"CODE_{_text(resource_id)}_loc_{payload_offset:08x}")
    return labels


def _semantic_xref_target_labels(rows: list[Mapping[str, object]]) -> set[str]:
    labels: set[str] = set()
    for row in rows:
        for xref in (_mapping(value) for value in _sequence(row.get("xrefs"))):
            if _text(xref.get("reason")) == "linkage_api_entry":
                continue
            target_label = xref.get("target_label")
            if isinstance(target_label, str) and target_label:
                labels.add(target_label)
    return labels


def _source_quality_labels(detail: Mapping[str, object], section: Mapping[str, object]) -> list[str]:
    labels = [_text(section.get("label"))] if section.get("label") is not None else []
    resource_id = detail.get("id")
    if resource_id == 0:
        labels.extend(["CODE_0_application_metadata", "CODE_0_jump_table"])
        labels.extend(
            f"CODE_0_jump_table_entry_{_text(row.get('entry_index'))}"
            for row in _sequence(_mapping(section.get("code0_structured_context")).get("jump_table_rows"))
        )
    if resource_id == 1:
        context = _mapping(section.get("code1_layout_context"))
        labels.extend(
            _text(_mapping(context.get(key)).get("label"))
            for key in ("far_model_header", "candidate_entry_stub", "candidate_body_after_stub")
        )
    labels.extend(_text(_mapping(item).get("target_label")) for item in _sequence(section.get("incoming_code0_xrefs")))
    for item in _sequence(section.get("source_body_ranges")):
        range_info = _mapping(item)
        start = _int_value(range_info.get("start")) or 0
        labels.append(f"{_text(section.get('label'))}_{_text(range_info.get('kind'))}_{start:08x}")
    return [label for label in labels if label and label != "unknown"]


def _source_quality_residuals(
    detail: Mapping[str, object],
    ranges: list[Mapping[str, object]],
    *,
    payload_size: int,
    semantic_rows: list[Mapping[str, object]],
    candidate_residuals: list[Mapping[str, object]],
    semantic_gap_residuals: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    residuals: list[dict[str, object]] = []
    for item in ranges:
        kind = str(item.get("kind") or "")
        status = str(item.get("fact_status") or item.get("status") or "")
        if kind in {"candidate_code", "candidate_unresolved_prefix", "confirmed_code", "code"}:
            decoded_residuals = _residuals_in_range(
                semantic_gap_residuals or _semantic_gap_residuals(detail, item, semantic_rows),
                item,
            )
            if semantic_rows:
                residuals.extend(decoded_residuals)
                continue
        if kind in {
            "candidate_code",
            "candidate_unresolved_prefix",
            "deferred",
            "unknown",
            "placeholder",
        } or status in {"candidate", "deferred"}:
            residuals.append(
                {
                    "kind": kind or "unknown",
                    "parser_range_kind": item.get("parser_range_kind"),
                    "start": item.get("start"),
                    "end": item.get("end"),
                    "size": item.get("size"),
                    "status": status or "deferred",
                    "fact_status": status or "deferred",
                    "parser_use": item.get("parser_use"),
                    "fact_id": item.get("fact_id"),
                    "kb_record_id": item.get("kb_record_id") or detail.get("kb_record_id"),
                    "reason": item.get("reason") or item.get("evidence") or "semantic ownership remains unresolved",
                    "next_required_implementation": _source_quality_next_step(detail, []),
                }
            )
    if not residuals and not ranges and payload_size:
        residuals.append(
            {
                "kind": "unknown",
                "start": 0,
                "end": payload_size,
                "size": payload_size,
                "status": "deferred",
                "reason": "no source-body range is available",
                "next_required_implementation": "extend C-owned CODE layout classification",
            }
        )
    existing_spans = {
        (
            _int_value(item.get("start")),
            _int_value(item.get("end")),
            str(item.get("kind") or ""),
        )
        for item in residuals
    }
    for item in candidate_residuals:
        start = _int_value(item.get("start"))
        end = _int_value(item.get("end"))
        kind = str(item.get("kind") or "")
        if start is None or end is None or end <= start:
            continue
        key = (start, end, kind)
        if key in existing_spans:
            continue
        residuals.append(
            {
                "kind": kind or "candidate_unvisited_entry_pattern",
                "start": start,
                "end": end,
                "size": end - start,
                "island_start": item.get("island_start"),
                "island_end": item.get("island_end"),
                "island_size": item.get("island_size"),
                "status": item.get("status") or "candidate",
                "fact_status": item.get("fact_status") or "candidate",
                "parser_use": item.get("parser_use") or "candidate_only",
                "fact_id": item.get("fact_id"),
                "kb_record_id": item.get("kb_record_id") or detail.get("kb_record_id"),
                "reason": item.get("reason") or "unvisited executable-looking bytes remain candidate residuals",
                "next_required_implementation": item.get("next_required_implementation")
                or "prove reachability from loader/CODE0/control-flow evidence before seeding",
            }
        )
        existing_spans.add(key)
    return residuals


def _residuals_in_range(
    residuals: list[Mapping[str, object]],
    range_info: Mapping[str, object],
) -> list[Mapping[str, object]]:
    range_start = _int_value(range_info.get("start"))
    range_end = _int_value(range_info.get("end"))
    if range_start is None or range_end is None:
        return residuals
    filtered: list[Mapping[str, object]] = []
    for residual in residuals:
        start = _int_value(residual.get("start"))
        end = _int_value(residual.get("end"))
        if start is None or end is None:
            continue
        overlap_start = max(start, range_start)
        overlap_end = min(end, range_end)
        if overlap_end <= overlap_start:
            continue
        if overlap_start == start and overlap_end == end:
            filtered.append(residual)
            continue
        clipped = dict(residual)
        clipped["start"] = overlap_start
        clipped["end"] = overlap_end
        clipped["size"] = overlap_end - overlap_start
        filtered.append(clipped)
    return filtered


def _semantic_gap_residuals(
    detail: Mapping[str, object],
    range_info: Mapping[str, object],
    semantic_rows: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    start = _int_value(range_info.get("start"))
    end = _int_value(range_info.get("end"))
    if start is None or end is None or end <= start:
        return []
    gaps: list[dict[str, object]] = []
    covered_end = start
    for row in sorted(semantic_rows, key=lambda item: _int_value(item.get("payload_offset")) or -1):
        row_start = _int_value(row.get("payload_offset"))
        row_end = _int_value(row.get("payload_end"))
        if row_start is None or row_end is None or row_end <= row_start:
            continue
        if row_end <= start or row_start >= end:
            continue
        if row_start > covered_end:
            gaps.append(
                _semantic_gap_residual(
                    detail,
                    range_info,
                    start=covered_end,
                    end=min(row_start, end),
                )
            )
        covered_end = max(covered_end, min(row_end, end))
    if covered_end < end:
        gaps.append(_semantic_gap_residual(detail, range_info, start=covered_end, end=end))
    return gaps


def _semantic_gap_residual(
    detail: Mapping[str, object],
    range_info: Mapping[str, object],
    *,
    start: int,
    end: int,
) -> dict[str, object]:
    return {
        "kind": "semantic_decode_gap",
        "start": start,
        "end": end,
        "size": end - start,
        "status": "candidate",
        "fact_status": range_info.get("fact_status") or "candidate",
        "parser_use": range_info.get("parser_use"),
        "fact_id": range_info.get("fact_id"),
        "kb_record_id": range_info.get("kb_record_id") or detail.get("kb_record_id"),
        "reason": "decoder did not emit an instruction/data row for this exact executable subrange",
        "next_required_implementation": "extend flow/data classification for this exact CODE subrange",
    }


def _source_quality_reachable_evidence(
    detail: Mapping[str, object],
    section: Mapping[str, object],
) -> list[dict[str, object]]:
    resource_id = detail.get("id")
    evidence: list[dict[str, object]] = []
    if resource_id == 0 and _mapping(section.get("code0_structured_context")).get("jump_table_rows"):
        evidence.append(
            {
                "kind": "code0_jump_table",
                "status": "validated_layout_candidate_targets",
                "kb_record_id": detail.get("kb_record_id"),
                "reason": "CODE 0 jump-table layout is accepted; target interpretation remains candidate",
            }
        )
    if resource_id == 1 and section.get("code1_layout_context"):
        evidence.append(
            {
                "kind": "known_entry_stub_pattern",
                "status": "candidate",
                "fact_status": "candidate",
                "parser_use": "candidate_only",
                "kb_record_id": detail.get("kb_record_id"),
                "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
                "reason": "movea.l (a7)+,a0 boundary is candidate-only; accepted byte-entry proof remains deferred",
            }
        )
    for anchor in _sequence(detail.get("navigation_anchors")):
        anchor_map = _mapping(anchor)
        evidence.append(
            {
                "kind": anchor_map.get("kind"),
                "status": anchor_map.get("fact_status"),
                "fact_status": anchor_map.get("fact_status"),
                "parser_use": anchor_map.get("parser_use"),
                "fact_id": anchor_map.get("fact_id"),
                "kb_record_id": anchor_map.get("kb_record_id") or detail.get("kb_record_id"),
                "reason": anchor_map.get("label"),
            }
        )
    return evidence


def _source_quality_next_step(
    detail: Mapping[str, object],
    residuals: list[Mapping[str, object]],
    *,
    semantic_instruction_count: int = 0,
) -> str:
    if detail.get("id") == 0:
        return "decode CODE 0 dispatch target semantics only where accepted target evidence exists"
    if semantic_instruction_count:
        return "extend flow following, generated xrefs, and data/residual classification for remaining CODE body spans"
    if any(_mapping(item).get("kind") == "candidate_code" for item in residuals):
        return "implement accepted Mac CODE entry/reachability proof before rendering semantic instructions"
    return "extend C-owned CODE layout and reference analysis before promoting semantic source rows"


def _ranges_cover_payload(ranges: list[Mapping[str, object]], *, payload_size: int) -> bool:
    if not ranges:
        return payload_size == 0
    cursor = 0
    for item in sorted(ranges, key=_range_start_sort_key):
        start = _int_value(item.get("start"))
        end = _int_value(item.get("end"))
        if start is None or end is None or start != cursor or end < start:
            return False
        cursor = end
    return cursor == payload_size


def _code1_layout_context(
    detail: Mapping[str, object],
    selected_code_segment: Mapping[str, object],
) -> dict[str, object]:
    payload_size = _int_value(detail.get("payload_size"))
    entry_offset = _int_value(selected_code_segment.get("code_entry_offset"))
    stub_size = 22
    stub_end = entry_offset + stub_size if entry_offset is not None else None
    return {
        "far_model_header": {
            "label": "CODE_1_far_model_header",
            "start": 0,
            "end": 40,
            "status": "validated",
            "fact_status": "validated",
            "parser_use": "accepted_parser_output",
            "kb_record_id": MACOS_APPLICATION_KB_RECORD_ID,
            "fact_id": "macos.code_resource.nonzero.segment_header",
            "reason": "far_model_segment_header; documented far-model header, not executable source rows",
        },
        "candidate_entry_stub": {
            "label": "CODE_1_candidate_entry_stub",
            "start": entry_offset,
            "end": stub_end,
            "selected_code_bytes_start": 0,
            "selected_code_bytes_end": stub_size,
            "status": "candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
            "kb_record_id": MACOS_APPLICATION_KB_RECORD_ID,
            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
            "reason": (
                "entry/stub bytes begin at candidate movea.l (a7)+,a0 boundary; "
                "accepted byte-entry proof remains deferred"
            ),
        },
        "candidate_body_after_stub": {
            "label": "CODE_1_candidate_body_after_stub",
            "start": stub_end,
            "end": payload_size,
            "status": "candidate",
            "fact_status": "candidate",
            "parser_use": "candidate_only",
            "kb_record_id": MACOS_APPLICATION_KB_RECORD_ID,
            "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
            "reason": (
                "remaining CODE 1 bytes are owned by candidate executable body; "
                "Segment Loader relocation/fixup semantics remain deferred"
            ),
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
        semantic_source = _semantic_source_rows(
            resource,
            code=code,
            selected_id=selected_id,
            hfs_bytes=hfs_bytes,
            hfs_path=hfs_path,
            project_root=project_root,
            all_routine_candidates=all_routine_candidates,
        )
        analysis_seeds = [_mapping(item) for item in _sequence(semantic_source.get("analysis_seeds"))]
        listing = _listing_descriptor(
            resource,
            code=code,
            selected_id=selected_id,
            project_id=project_id,
            unsupported=unsupported,
            preview_windows=preview_windows,
            analysis_seeds=analysis_seeds,
            semantic_source=semantic_source,
        )
        restored_source = _c_owned_restored_source_packet(code, scope=f"CODE {resource_id}")
        source_presentation_status = _code_source_presentation_status(
            resource,
            restored_source=restored_source,
            listing=listing,
        )
        anchors = _resource_navigation_anchors(
            resource,
            code=code,
            segment=segment,
            all_routine_candidates=all_routine_candidates,
        )
        jump_table_rows = (
            _code0_jump_table_rows(code, all_routine_candidates=all_routine_candidates) if resource_id == 0 else []
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
                "restored_source": restored_source,
                "source_presentation_status": source_presentation_status,
                "semantic_source": semantic_source,
                "jump_table": _mapping(code.get("jump_table")),
                "jump_table_rows": jump_table_rows,
                "navigation_anchors": anchors,
                "listing": listing,
                "preview_windows": preview_windows,
            }
        )
    return details


def _code_source_presentation_status(
    resource: Mapping[str, object],
    *,
    restored_source: Mapping[str, object],
    listing: Mapping[str, object],
) -> dict[str, object]:
    resource_id = resource.get("id")
    stable_identity = f"macos-code:CODE:{resource_id}"
    if restored_source.get("model") == "restored_source_model_v1" and restored_source.get("authority") == "c_owned":
        verifier = _mapping(restored_source.get("source_coverage_verifier"))
        return {
            "kind": "c_owned_restored_source_packet",
            "status": "covered" if verifier.get("ok") is True else "blocked",
            "resource_type": "CODE",
            "resource_id": resource_id,
            "resource_name": resource.get("name"),
            "stable_identity": stable_identity,
            "source_visible": True,
            "verifier_ok": verifier.get("ok") is True,
            "ownership_range_count": len(_sequence(restored_source.get("source_ownership_ranges"))),
            "source_reference_count": len(_sequence(restored_source.get("source_reference_records"))),
            "provenance": "platform_file_lib.macos_hfs_code_summary restored_source",
        }
    return {
        "kind": "typed_deferred_source_placeholder",
        "status": "blocked",
        "resource_type": "CODE",
        "resource_id": resource_id,
        "resource_name": resource.get("name"),
        "stable_identity": stable_identity,
        "source_visible": True,
        "reason": restored_source.get("reason") or listing.get("reason") or "CODE resource has no C-owned source packet",
        "provenance": "macos_project_payload.c_owned_restored_source_packet",
    }


def _semantic_source_rows(
    resource: Mapping[str, object],
    *,
    code: Mapping[str, object],
    selected_id: object,
    hfs_bytes: bytes,
    hfs_path: str,
    project_root: Path,
    all_routine_candidates: list[dict[str, object]],
) -> dict[str, object]:
    resource_id = resource.get("id")
    if resource_id == 0:
        return {
            "kind": "semantic_source_deferred",
            "status": "deferred",
            "reason": "CODE 0 is routing/application metadata, not an executable body",
            "analysis_seed_count": 0,
            "analysis_seeds": [],
            "rows": [],
        }
    code_range = _first_code_range(_sequence(code.get("layout_ranges")))
    code_start = _int_value(code_range.get("start"))
    code_size = _int_value(code_range.get("size"))
    if code_start is None or code_size is None or code_size <= 0:
        return {
            "kind": "semantic_source_blocked",
            "status": "blocked",
            "reason": "CODE resource has no classifiable executable body range",
            "analysis_seed_count": 0,
            "analysis_seeds": [],
            "rows": [],
        }
    analysis_range = _macos_code_semantic_analysis_range(code)
    analysis_start = _int_value(analysis_range.get("start"))
    analysis_end = _int_value(analysis_range.get("end"))
    if analysis_start is None or analysis_end is None or analysis_end <= analysis_start:
        analysis_range = code_range
        analysis_start = code_start
        analysis_end = code_start + code_size
    resource_payload = extract_macos_hfs_code_resource_payload_bytes_with_c_backend(
        hfs_bytes,
        hfs_path,
        int(resource_id),
        project_root=project_root,
    )
    code_bytes = resource_payload[analysis_start:analysis_end]
    if not code_bytes:
        return {
            "kind": "semantic_source_blocked",
            "status": "blocked",
            "reason": "CODE executable body bytes are unavailable from the native C Mac CODE path",
            "analysis_seed_count": 0,
            "analysis_seeds": [],
            "rows": [],
        }
    analysis_seeds = _macos_code_analysis_seeds(
        resource,
        code=code,
        payload_base=analysis_start,
        all_routine_candidates=all_routine_candidates,
    )
    with _macos_code_analysis_seed_metadata_path(analysis_seeds) as metadata_path:
        total_rows, _profile, artifact = build_macos_code_bytes_listing_artifact_profile(
            code_bytes,
            display_path=f"Mac OS semantic source CODE {resource_id} {resource.get('name') or ''}".strip(),
            metadata_path=metadata_path,
            project_root=project_root,
        )
    try:
        window, _window_profile = artifact.window_payload(start=0, count=total_rows)
    finally:
        artifact.close()
    asm_source_includes = _macos_asm_source_includes(_sequence(window.get("rows")))
    rows = [
        _semantic_source_row(row, payload_base=analysis_start, resource=resource, code=code, code_range=analysis_range)
        for row in _sequence(window.get("rows"))
    ]
    rows = [row for row in rows if row]
    rows = [row for row in rows if not _macos_fallback_byte_row(row, code_range=analysis_range)]
    semantic_gap_residuals = _macos_code_semantic_gap_residuals(
        code_bytes,
        payload_base=analysis_start,
        code_range=analysis_range,
        semantic_rows=rows,
        resource=resource,
        code=code,
    )
    semantic_data_rows = _macos_code_semantic_data_rows(
        semantic_gap_residuals,
        code_bytes,
        payload_base=analysis_start,
        resource=resource,
        code=code,
    )
    rows = _sorted_semantic_rows([*rows, *semantic_data_rows])
    semantic_gap_residuals = [
        residual for residual in semantic_gap_residuals if residual.get("kind") == "semantic_decode_gap"
    ]
    candidate_residuals = _macos_code_candidate_residuals(
        code_bytes,
        payload_base=analysis_start,
        code_range=analysis_range,
        semantic_rows=rows,
        semantic_gap_residuals=semantic_gap_residuals,
        resource=resource,
        code=code,
    )
    instruction_count = sum(1 for row in rows if row.get("kind") == "instruction")
    return {
        "kind": "macos_code_semantic_source_v1",
        "status": "decoded" if instruction_count else "blocked",
        "backend": "macos-code",
        "authority": "c_owned_listing_artifact",
        "resource_type": "CODE",
        "resource_id": resource_id,
        "payload_base": analysis_start,
        "payload_size": analysis_end - analysis_start,
        "row_count": len(rows),
        "instruction_row_count": instruction_count,
        "data_row_count": sum(1 for row in rows if _semantic_row_is_durable_data(row)),
        "generated_label_count": sum(1 for row in rows if row.get("kind") == "label"),
        "generated_xref_count": sum(len(_sequence(row.get("xrefs"))) for row in rows),
        "analysis_seed_count": len(analysis_seeds),
        "analysis_seeds": analysis_seeds,
        "asm_source_includes": asm_source_includes,
        "candidate_residual_count": len(candidate_residuals),
        "candidate_residuals": candidate_residuals,
        "semantic_gap_residual_count": len(semantic_gap_residuals),
        "semantic_gap_residuals": semantic_gap_residuals,
        "rows": rows,
    }


def _macos_asm_source_includes(rows: Sequence[object]) -> list[str]:
    includes: list[str] = []
    for row in rows:
        row_map = _mapping(row)
        if row_map.get("kind") != "directive" or row_map.get("opcode_or_directive") != "INCLUDE":
            continue
        operand = str(row_map.get("operand_text") or "").strip()
        if len(operand) >= 2 and operand[0] == '"' and operand[-1] == '"':
            include = operand[1:-1]
        else:
            include = operand
        if include and include not in includes:
            includes.append(include)
    return includes


def _macos_code_analysis_seeds(
    resource: Mapping[str, object],
    *,
    code: Mapping[str, object],
    payload_base: int,
    all_routine_candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    resource_id = resource.get("id")
    if not isinstance(resource_id, int):
        return []
    seeds: dict[int, dict[str, object]] = {}
    for range_info in (_mapping(item) for item in _sequence(code.get("layout_ranges"))):
        if range_info.get("kind") not in {"candidate_code", "confirmed_code", "code"}:
            continue
        start = _int_value(range_info.get("start"))
        end = _int_value(range_info.get("end"))
        if start is None or end is None or end <= start:
            continue
        _add_macos_code_analysis_seed(
            seeds,
            payload_offset=start,
            payload_base=payload_base,
            payload_end=end,
            resource_id=resource_id,
            reason="loader_segment_body_start",
            fact_id=range_info.get("fact_id"),
            fact_status=range_info.get("fact_status"),
            parser_use=range_info.get("parser_use"),
        )
        for candidate in all_routine_candidates:
            if candidate.get("target_resource_id") != resource_id:
                continue
            target_offset = _code0_target_payload_offset(
                {"code_layout": [range_info]},
                _int_value(candidate.get("routine_offset_from_segment")),
                routine_offset_space=_text(candidate.get("routine_offset_space") or "candidate_code_range"),
            )
            if target_offset is None:
                continue
            _add_macos_code_analysis_seed(
                seeds,
                payload_offset=target_offset,
                payload_base=payload_base,
                payload_end=end,
                resource_id=resource_id,
                reason="code0_routine_candidate",
                fact_id=candidate.get("fact_id"),
                fact_status=candidate.get("fact_status"),
                parser_use=candidate.get("parser_use"),
                code0_payload_offset=candidate.get("code0_payload_offset"),
            )
    return [seeds[offset] for offset in sorted(seeds)]


def _macos_code_candidate_residuals(
    code_bytes: bytes,
    *,
    payload_base: int,
    code_range: Mapping[str, object],
    semantic_rows: list[Mapping[str, object]],
    semantic_gap_residuals: list[Mapping[str, object]] | None = None,
    resource: Mapping[str, object],
    code: Mapping[str, object],
) -> list[dict[str, object]]:
    start = _int_value(code_range.get("start"))
    end = _int_value(code_range.get("end"))
    if start is None or end is None or end <= start:
        return []
    residuals: list[dict[str, object]] = []
    for payload_offset, pattern in _macos_candidate_entry_patterns(code_bytes, payload_base=payload_base):
        if payload_offset < start or payload_offset >= end:
            continue
        if _payload_offset_is_covered(payload_offset, semantic_rows):
            continue
        island = _macos_candidate_residual_island(payload_offset, semantic_gap_residuals or [])
        island_start = _int_value(island.get("start")) if island else payload_offset
        island_end = _int_value(island.get("end")) if island else min(payload_offset + 2, end)
        residuals.append(
            {
                "kind": "candidate_unvisited_entry_pattern",
                "resource_id": resource.get("id"),
                "start": payload_offset,
                "end": min(payload_offset + 2, end),
                "size": min(payload_offset + 2, end) - payload_offset,
                "island_start": island_start,
                "island_end": island_end,
                "island_size": (island_end - island_start) if island_start is not None and island_end is not None else None,
                "status": "candidate",
                "fact_status": "candidate",
                "parser_use": "candidate_only",
                "fact_id": "macos.code_resource.orphan_layout_ranges.candidate",
                "kb_record_id": code.get("kb_record_id") or resource.get("kb_record_id"),
                "pattern": pattern,
                "reason": "unvisited executable-looking bytes are explicit residuals, not generated entrypoints",
                "next_required_implementation": "prove reachability from CODE0/loader control flow before seeding",
            }
        )
    return residuals


def _macos_candidate_residual_island(
    payload_offset: int,
    semantic_gap_residuals: list[Mapping[str, object]],
) -> Mapping[str, object] | None:
    for residual in semantic_gap_residuals:
        start = _int_value(residual.get("start"))
        end = _int_value(residual.get("end"))
        if start is None or end is None:
            continue
        if start <= payload_offset < end:
            return residual
    return None


def _macos_code_semantic_gap_residuals(
    code_bytes: bytes,
    *,
    payload_base: int,
    code_range: Mapping[str, object],
    semantic_rows: list[Mapping[str, object]],
    resource: Mapping[str, object],
    code: Mapping[str, object],
) -> list[dict[str, object]]:
    residuals: list[dict[str, object]] = []
    detail = {"kb_record_id": code.get("kb_record_id") or resource.get("kb_record_id")}
    for gap in _semantic_gap_residuals(detail, code_range, semantic_rows):
        start = _int_value(gap.get("start"))
        end = _int_value(gap.get("end"))
        if start is None or end is None or end <= start:
            continue
        local_start = start - payload_base
        local_end = end - payload_base
        if local_start < 0 or local_end > len(code_bytes):
            residuals.append(gap)
            continue
        gap_bytes = code_bytes[local_start:local_end]
        data_kind = _macos_semantic_gap_data_kind(
            gap_bytes,
            payload_start=start,
            payload_end=end,
        )
        if data_kind is None:
            symbol_size = _macos_leading_symbol_record_size(gap_bytes)
            if symbol_size is not None and symbol_size < len(gap_bytes):
                residuals.append(
                    _classified_semantic_gap(
                        gap,
                        kind="semantic_symbol_record_gap",
                        start=start,
                        end=start + symbol_size,
                    )
                )
                trailing = dict(gap)
                trailing["start"] = start + symbol_size
                trailing["size"] = end - (start + symbol_size)
                residuals.append(trailing)
                continue
            residuals.append(gap)
            continue
        residuals.append(_classified_semantic_gap(gap, kind=data_kind, start=start, end=end))
    return residuals


def _macos_code_semantic_data_rows(
    semantic_gap_residuals: list[Mapping[str, object]],
    code_bytes: bytes,
    *,
    payload_base: int,
    resource: Mapping[str, object],
    code: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for residual in semantic_gap_residuals:
        kind = str(residual.get("kind") or "")
        if kind == "semantic_decode_gap":
            continue
        start = _int_value(residual.get("start"))
        end = _int_value(residual.get("end"))
        if start is None or end is None or end <= start:
            continue
        local_start = start - payload_base
        local_end = end - payload_base
        if local_start < 0 or local_end > len(code_bytes):
            continue
        rows.append(
            {
                "kind": "data",
                "resource_type": "CODE",
                "resource_id": resource.get("id"),
                "resource_name": resource.get("name"),
                "payload_offset": start,
                "payload_end": end,
                "size": end - start,
                "bytes": code_bytes[local_start:local_end].hex(),
                "data_kind": kind,
                "opcode_or_directive": "dc.b",
                "stable_key": f"macos-code-{resource.get('id')}-{kind}-{start:08x}",
                "provenance": "macos_semantic_gap_classifier",
                "kb_record_id": residual.get("kb_record_id") or code.get("kb_record_id") or resource.get("kb_record_id"),
                "fact_id": residual.get("fact_id"),
                "fact_status": residual.get("fact_status") or "candidate",
                "parser_use": residual.get("parser_use") or "candidate_only",
            }
        )
    return rows


def _sorted_semantic_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            _int_value(row.get("payload_offset")) if _int_value(row.get("payload_offset")) is not None else -1,
            0 if row.get("kind") == "label" else 1,
            _int_value(row.get("payload_end")) if _int_value(row.get("payload_end")) is not None else -1,
        ),
    )


def _classified_semantic_gap(gap: Mapping[str, object], *, kind: str, start: int, end: int) -> dict[str, object]:
    classified = dict(gap)
    classified["kind"] = kind
    classified["start"] = start
    classified["end"] = end
    classified["size"] = end - start
    classified["reason"] = "semantic decoder left a byte span that matches conservative Mac data syntax"
    classified["next_required_implementation"] = "promote this classified data gap into first-class C-owned data rows"
    return classified


def _macos_semantic_gap_data_kind(data: bytes, *, payload_start: int, payload_end: int) -> str | None:
    if not data:
        return None
    if all(byte == 0 for byte in data):
        if _macos_gap_is_alignment_padding(data, payload_start=payload_start, payload_end=payload_end):
            return "semantic_alignment_padding_gap"
        return "semantic_zero_fill_gap"
    if _macos_gap_is_printable_bytes(data):
        return "semantic_string_data_gap"
    if _macos_gap_is_pascal_identifier(data):
        return "semantic_pascal_string_gap"
    if _macos_gap_is_word_dispatch_table(data):
        return "semantic_dispatch_table_gap"
    return None


def _macos_gap_is_alignment_padding(data: bytes, *, payload_start: int, payload_end: int) -> bool:
    return len(data) <= 8 and payload_start % 4 != 0 and payload_end % 4 == 0


def _macos_leading_symbol_record_size(data: bytes) -> int | None:
    if len(data) < 8:
        return None
    length_offset = 1 if data[0] == 0x80 else 0
    if length_offset == 0 and data[0] & 0x80 == 0:
        return None
    length = data[length_offset] & 0x7F
    text_start = length_offset + 1
    if length < 3 or text_start + length > len(data):
        return None
    text = data[text_start : text_start + length]
    if any(byte < 32 or byte > 126 for byte in text):
        return None
    cursor = text_start + length
    while cursor < len(data) and data[cursor] == 0 and cursor < length + 5:
        cursor += 1
    if cursor % 2 != 0 and cursor < len(data) and data[cursor] == 0:
        cursor += 1
    if cursor + 2 <= len(data) and _macos_gap_looks_like_code_start(data[cursor + 2 :]):
        cursor += 2
    elif _macos_gap_looks_like_code_start(data[cursor:]):
        pass
    elif len(data) - cursor <= 4:
        cursor = len(data)
    else:
        return None
    return cursor if cursor > text_start + length else None


def _macos_gap_looks_like_code_start(data: bytes) -> bool:
    return data.startswith((b"\x4e\x56", b"\x48\xe7", b"\x20\x5f", b"\x2f\x00", b"\x42\x40"))


def _macos_gap_is_printable_bytes(data: bytes) -> bool:
    if len(data) < 4:
        return False
    printable = sum(1 for byte in data if byte in {0, 9, 10, 13} or 32 <= byte <= 126)
    return printable == len(data) and sum(1 for byte in data if 32 <= byte <= 126) >= 4


def _macos_gap_is_pascal_identifier(data: bytes) -> bool:
    if len(data) < 4:
        return False
    length = data[0] & 0x7F
    if length == 0 or length + 1 > len(data):
        return False
    text = data[1 : 1 + length]
    if any(byte < 32 or byte > 126 for byte in text):
        return False
    padding = data[1 + length :]
    return len(text) >= 3 and all(byte == 0 for byte in padding[: min(len(padding), 3)])


def _macos_gap_is_word_dispatch_table(data: bytes) -> bool:
    if len(data) < 8 or len(data) % 2 != 0:
        return False
    words = [int.from_bytes(data[index : index + 2], "big") for index in range(0, len(data), 2)]
    even_offsets = [word for word in words if word != 0 and word % 2 == 0 and word < 0x8000]
    return len(even_offsets) >= 4 and len(even_offsets) >= len(words) // 2


def _macos_candidate_entry_patterns(code_bytes: bytes, *, payload_base: int) -> Iterator[tuple[int, str]]:
    limit = len(code_bytes) - 1
    for local_offset in range(0, max(limit, 0), 2):
        word = code_bytes[local_offset : local_offset + 2]
        pattern: str | None = None
        if word in {b"\x20\x5f", b"\x22\x5f", b"\x24\x5f", b"\x26\x5f"}:
            pattern = "movea_stack"
        elif word == b"\x4e\x56":
            pattern = "link_frame"
        elif word == b"\x48\xe7":
            pattern = "movem_prologue"
        if pattern is not None:
            yield payload_base + local_offset, pattern


def _payload_offset_is_covered(payload_offset: int, semantic_rows: list[Mapping[str, object]]) -> bool:
    for row in semantic_rows:
        if row.get("kind") != "instruction" and not _semantic_row_is_durable_data(row):
            continue
        start = _int_value(row.get("payload_offset"))
        end = _int_value(row.get("payload_end"))
        if start is not None and end is not None and start <= payload_offset < end:
            return True
    return False


def _macos_fallback_byte_row(row: Mapping[str, object], *, code_range: Mapping[str, object]) -> bool:
    if row.get("kind") != "data":
        return False
    if isinstance(row.get("api_call"), Mapping):
        return False
    opcode = str(row.get("opcode_or_directive") or "").lower()
    if opcode and opcode not in {"dc.b", "dcb.b"}:
        return False
    row_start = _int_value(row.get("payload_offset"))
    row_end = _int_value(row.get("payload_end"))
    range_start = _int_value(code_range.get("start"))
    range_end = _int_value(code_range.get("end"))
    return (
        row_start is not None
        and row_end is not None
        and range_start is not None
        and range_end is not None
        and range_start <= row_start
        and row_end <= range_end
    )


def _semantic_row_is_durable_data(row: Mapping[str, object]) -> bool:
    if row.get("data_kind"):
        return row.get("kind") == "data" and _int_value(row.get("payload_offset")) is not None
    if row.get("kind") == "directive":
        return _int_value(row.get("payload_offset")) is not None
    return row.get("kind") == "data" and str(row.get("opcode_or_directive") or "").lower() not in {"dc.b", "dcb.b"}


def _add_macos_code_analysis_seed(
    seeds: dict[int, dict[str, object]],
    *,
    payload_offset: int,
    payload_base: int,
    payload_end: int,
    resource_id: int,
    reason: str,
    fact_id: object,
    fact_status: object,
    parser_use: object,
    code0_payload_offset: object | None = None,
) -> None:
    if payload_offset < payload_base or payload_offset >= payload_end:
        return
    local_offset = payload_offset - payload_base
    existing = seeds.get(local_offset)
    if existing is not None and existing.get("reason") == "code0_routine_candidate":
        return
    seed = {
        "resource_id": resource_id,
        "payload_offset": payload_offset,
        "local_offset": local_offset,
        "analysis_payload_base": payload_base,
        "analysis_payload_end": payload_end,
        "reason": reason,
        "name": f"CODE_{resource_id}_entry_{payload_offset:08x}",
        "fact_id": fact_id,
        "fact_status": fact_status,
        "parser_use": parser_use,
    }
    if code0_payload_offset is not None:
        seed["code0_payload_offset"] = code0_payload_offset
    seeds[local_offset] = seed


@contextmanager
def _macos_code_analysis_seed_metadata_path(seeds: list[dict[str, object]]) -> Iterator[Path | None]:
    if not seeds:
        yield None
        return
    payload = {
        "target_type": "raw_binary",
        "seeded_code_entrypoints": [
            {
                "addr": int(seed["local_offset"]),
                "hunk": 0,
                "name": str(seed["name"]),
                "seed_origin": "primary_doc",
                "review_status": "seeded",
                "citation": str(seed.get("fact_id") or "macos.generated.analysis_seed"),
                "source_id": f"macos-code:{seed.get('resource_id')}",
                "source_path": f"CODE:{seed.get('resource_id')}",
                "source_locator": f"payload+{int(seed['payload_offset'])}",
                "comment": f"generated Mac CODE analysis seed: {seed.get('reason')}",
                "role": str(seed.get("reason") or "generated_entry"),
            }
            for seed in seeds
        ],
    }
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump(payload, temp_file)
            temp_path = Path(temp_file.name)
        yield temp_path
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _semantic_source_row(
    row: object,
    *,
    payload_base: int,
    resource: Mapping[str, object],
    code: Mapping[str, object],
    code_range: Mapping[str, object],
) -> dict[str, object]:
    row_map = _mapping(row)
    kind = str(row_map.get("kind") or "")
    start = _int_value(row_map.get("start_offset"))
    end = _int_value(row_map.get("end_offset"))
    payload_start = payload_base + start if start is not None else None
    payload_end = payload_base + end if end is not None else payload_start
    label = row_map.get("label") if isinstance(row_map.get("label"), str) else None
    resource_id = resource.get("id")
    xrefs = _semantic_source_xrefs(row_map, payload_base=payload_base, resource_id=resource_id, source_payload=payload_start)
    semantic_row = {
        "kind": kind,
        "resource_type": "CODE",
        "resource_id": resource_id,
        "resource_name": resource.get("name"),
        "payload_offset": payload_start,
        "payload_end": payload_end,
        "size": (payload_end - payload_start) if isinstance(payload_start, int) and isinstance(payload_end, int) else 0,
        "bytes": row_map.get("bytes"),
        "text": _macos_semantic_row_text(
            str(row_map.get("text") or "").rstrip(),
            resource_id=resource_id,
            payload_base=payload_base,
        ),
        "label": label,
        "opcode_or_directive": row_map.get("opcode_or_directive"),
        "operand_text": row_map.get("operand_text"),
        "api_call": row_map.get("api_call"),
        "flow": row_map.get("flow"),
        "flow_kind": row_map.get("flow_kind"),
        "control_flow_boundary": row_map.get("control_flow_boundary"),
        "stable_key": row_map.get("stable_key") or row_map.get("row_key"),
        "xrefs": xrefs,
        "provenance": "CListingArtifact.create_macos_code_bytes",
        "kb_record_id": code_range.get("kb_record_id") or code.get("kb_record_id"),
        "fact_id": code_range.get("fact_id"),
        "fact_status": code_range.get("fact_status"),
        "parser_use": code_range.get("parser_use"),
    }
    return {key: value for key, value in semantic_row.items() if value not in (None, "")}


def _macos_semantic_row_text(text: str, *, resource_id: object, payload_base: int) -> str:
    def replace(match: re.Match[str]) -> str:
        return f"CODE_{_text(resource_id)}_loc_{payload_base + int(match.group(1), 16):08x}"

    return _RAW_LOCAL_LABEL_RE.sub(replace, text)


def _semantic_source_xrefs(
    row: Mapping[str, object],
    *,
    payload_base: int,
    resource_id: object,
    source_payload: int | None,
) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    for ref in _sequence(row.get("code_start_refs")):
        ref_map = _mapping(ref)
        offset = _int_value(ref_map.get("offset"))
        target_payload = payload_base + offset if offset is not None else None
        xrefs.append(
            {
                "kind": "code_start_ref",
                "source_payload_offset": source_payload,
                "target_payload_offset": target_payload,
                "target_label": (
                    f"CODE_{_text(resource_id)}_loc_{target_payload:08x}" if target_payload is not None else None
                ),
                "reason": ref_map.get("reason_name"),
                "confidence": ref_map.get("confidence"),
            }
        )
    return xrefs


def _listing_descriptor(
    resource: Mapping[str, object],
    *,
    code: Mapping[str, object],
    selected_id: object,
    project_id: str,
    unsupported: list[object],
    preview_windows: list[dict[str, object]],
    analysis_seeds: list[dict[str, object]],
    semantic_source: Mapping[str, object],
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
            "analysis_seed_count": len(analysis_seeds),
            "analysis_seeds": analysis_seeds,
        }
    if semantic_source.get("status") == "decoded":
        return {
            "kind": "semantic_listing",
            "available": True,
            "route": "listing",
            "reason": "C-owned semantic rows from generated loader/CODE0 entry seeds",
            "row_count": semantic_source.get("row_count"),
            "instruction_row_count": semantic_source.get("instruction_row_count"),
            "candidate_residual_count": semantic_source.get("candidate_residual_count"),
            "analysis_seed_count": len(analysis_seeds),
            "analysis_seeds": analysis_seeds,
            "project_id": project_id,
            "resource_type": resource.get("type") or "CODE",
            "resource_id": resource_id,
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
            "analysis_seed_count": len(analysis_seeds),
            "analysis_seeds": analysis_seeds,
        }
    return {
        "kind": "structured_placeholder",
        "available": False,
        "reason": _no_preview_reason(code),
        "analysis_seed_count": len(analysis_seeds),
        "analysis_seeds": analysis_seeds,
    }


def _c_owned_restored_source_packet(code: Mapping[str, object], *, scope: str) -> dict[str, object]:
    packet = _mapping(code.get("restored_source"))
    if packet.get("model") == "restored_source_model_v1" and packet.get("authority") == "c_owned":
        return dict(packet)
    return {
        "model": "restored_source_missing",
        "status": "blocked",
        "authority": "missing_c_owned_model",
        "reason": f"{scope} restored-source evidence is missing from the C-owned model",
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
    range_info = _first_executable_code_range(_sequence(code.get("layout_ranges")))
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
        "kind": "executable_code_preview",
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
        "executable_range_start": start,
        "executable_range_end": end,
        "executable_range_size": end - start,
        "range_kind": range_info.get("kind"),
        "evidence": range_info.get("evidence"),
        "kb_record_id": code.get("kb_record_id"),
        "fact_id": range_info.get("fact_id"),
        "fact_status": range_info.get("fact_status"),
        "parser_use": range_info.get("parser_use"),
        "truncated": preview_end < payload_end,
        "max_bytes": MACOS_CODE_PREVIEW_MAX_BYTES,
        "reason": "bounded to executable CODE range; unresolved bytes remain candidate residuals",
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

    artifact = None
    try:
        resource_id = resource.get("id")
        resource_label = f"CODE {resource_id} {resource.get('name') or ''}".strip()
        _total_rows, _profile, artifact = build_macos_code_bytes_listing_artifact_profile(
            preview_bytes,
            display_path=f"Mac OS candidate preview {resource_label}",
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


def _code0_jump_table_rows(
    code: Mapping[str, object],
    *,
    all_routine_candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    jump_table = _mapping(code.get("jump_table"))
    table_start = _int_value(jump_table.get("start"))
    entry_size = _int_value(jump_table.get("entry_size"))
    entry_count = _int_value(jump_table.get("entry_count"))
    accepted_layout = {
        "kb_record_id": code.get("kb_record_id"),
        "fact_id": jump_table.get("fact_id"),
        "fact_status": jump_table.get("fact_status"),
        "parser_use": jump_table.get("parser_use"),
    }
    candidates_by_offset = {
        _int_value(candidate.get("code0_payload_offset")): candidate
        for candidate in all_routine_candidates
        if _int_value(candidate.get("code0_payload_offset")) is not None
    }
    rows: list[dict[str, object]] = []
    if table_start is not None and entry_size and entry_count is not None:
        for entry_index in range(entry_count):
            code0_offset = table_start + entry_index * entry_size
            candidate = candidates_by_offset.get(code0_offset, {})
            rows.append(
                _code0_jump_table_row(
                    code0_offset=code0_offset,
                    entry_index=entry_index,
                    entry_size=entry_size,
                    table_start=table_start,
                    accepted_layout=accepted_layout,
                    candidate=candidate,
                )
            )
        return rows
    for candidate in sorted(all_routine_candidates, key=_candidate_code0_offset_sort_key):
        code0_offset = _int_value(candidate.get("code0_payload_offset"))
        entry_index = None
        if code0_offset is not None and table_start is not None and entry_size:
            entry_index = (code0_offset - table_start) // entry_size
        if entry_index is None:
            entry_index = _int_value(candidate.get("index"))
        rows.append(
            _code0_jump_table_row(
                code0_offset=code0_offset,
                entry_index=entry_index,
                entry_size=entry_size,
                table_start=table_start,
                accepted_layout=accepted_layout,
                candidate=candidate,
            )
        )
    return rows


def _code0_jump_table_row(
    *,
    code0_offset: int | None,
    entry_index: int | None,
    entry_size: int | None,
    table_start: int | None,
    accepted_layout: Mapping[str, object],
    candidate: Mapping[str, object],
) -> dict[str, object]:
    row = {
        "kind": "code0_jump_table_entry",
        "entry_index": entry_index,
        "code0_payload_offset": code0_offset,
        "entry_size": entry_size,
        "raw_entry_bytes": None,
        "raw_entry_fields": {
            "jump_table_start": table_start,
            "entry_size": entry_size,
        },
        "accepted_layout": dict(accepted_layout),
    }
    if candidate:
        row.update(
            {
                "target_resource_id": candidate.get("target_resource_id"),
                "jump_table_offset": candidate.get("jump_table_offset"),
                "routine_offset_from_segment": candidate.get("routine_offset_from_segment"),
                "routine_offset_space": candidate.get("routine_offset_space") or "candidate_code_range",
                "candidate_target": {
                    "kb_record_id": candidate.get("kb_record_id"),
                    "fact_id": candidate.get("fact_id"),
                    "fact_status": candidate.get("fact_status"),
                    "parser_use": candidate.get("parser_use"),
                    "classification": candidate.get("classification"),
                },
            }
        )
        platform_call = candidate.get("platform_call")
        if isinstance(platform_call, Mapping):
            row["platform_call"] = dict(platform_call)
        stored_offset_expression = candidate.get("stored_offset_expression")
        if isinstance(stored_offset_expression, Mapping):
            row["stored_offset_expression"] = dict(stored_offset_expression)
    return row


def _candidate_code0_offset_sort_key(candidate: Mapping[str, object]) -> tuple[int, int]:
    offset = _int_value(candidate.get("code0_payload_offset"))
    index = _int_value(candidate.get("index"))
    return (offset if offset is not None else 10**12, index if index is not None else 10**12)


def _non_code_resource_details(resource_types: list[object]) -> list[dict[str, object]]:
    rows = []
    for resource_type in (_mapping(value) for value in resource_types):
        if resource_type.get("type") == "CODE":
            continue
        row = {
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
        if resource_type.get("type") == "CURS":
            row.update(
                {
                    "role": "resource_type_semantic",
                    "semantic_status": "validated",
                    "fact_id": MACOS_CURS_RESOURCE_FACT_ID,
                    "fact_status": "validated",
                    "parser_use": "accepted_parser_output",
                    "evidence": "Inside Macintosh QuickDraw Cursor record; type-level semantics only",
                    "semantic": {
                        "kind": "classic_cursor_16x16",
                        "image_bytes": 32,
                        "mask_bytes": 32,
                        "hotspot_bytes": 4,
                    },
                    "reason": "CURS type-level layout is cited; payload bitmap/hotspot bytes are not decoded",
                }
            )
        rows.append(row)
    return rows


def _executable_resource_placeholders(
    non_code_details: list[dict[str, object]],
    *,
    source_image: str,
    hfs_path: str,
) -> list[dict[str, object]]:
    placeholders: list[dict[str, object]] = []
    for detail in non_code_details:
        resource_type = detail.get("resource_type")
        resource_count = detail.get("resource_count")
        stable_identity = f"macos-resource:{source_image}:{hfs_path}:{resource_type}:*"
        source_context = _placeholder_source_context(stable_identity)
        placeholders.append(
            {
                "kind": "executable_resource_placeholder",
                "resource_type": resource_type,
                "resource_id": None,
                "resource_name": None,
                "resource_count": resource_count,
                "byte_size": None,
                "sha256": None,
                "stable_identity": stable_identity,
                "status": detail.get("fact_status") or detail.get("semantic_status") or "candidate",
                "reason": detail.get("reason") or "resource payload semantics are not decoded",
                "provenance": "platform_file_lib.macos_hfs_code_summary resource_fork.types",
                "source_visible": True,
                "source_context": source_context,
                "reference_sites": _placeholder_reference_sites(detail, stable_identity=stable_identity),
                "kb_record_id": detail.get("kb_record_id"),
                "fact_id": detail.get("fact_id"),
                "fact_status": detail.get("fact_status"),
                "parser_use": detail.get("parser_use"),
            }
        )
    return placeholders


def _placeholder_source_context(stable_identity: str) -> dict[str, object]:
    return {
        "status": "unlinked",
        "stable_identity": stable_identity,
        "link_kind": "resource_type_inventory",
        "reason": "No direct CODE routing, fixup, or restored-source reference targets this resource type yet.",
    }


def _placeholder_reference_sites(
    detail: Mapping[str, object], *, stable_identity: str
) -> list[dict[str, object]]:
    return [
        {
            "kind": "resource_type_inventory",
            "resource_type": detail.get("resource_type"),
            "resource_id": None,
            "stable_identity": stable_identity,
            "link_status": "unlinked",
            "source_offset": None,
            "reason": "No direct CODE routing, fixup, or restored-source reference targets this resource type yet.",
        }
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
        if range_info.get("kind") in {"code", "confirmed_code", "candidate_code"} and range_info.get("entrypoint") is True:
            return range_info
    return {}


def _macos_code_semantic_analysis_range(code: Mapping[str, object]) -> Mapping[str, object]:
    ranges = [_mapping(item) for item in _sequence(code.get("layout_ranges"))]
    starts: list[int] = []
    ends: list[int] = []
    authority: Mapping[str, object] = _first_code_range(list(ranges))
    for range_info in ranges:
        if range_info.get("kind") not in {"candidate_unresolved_prefix", "candidate_code", "confirmed_code", "code"}:
            continue
        start = _int_value(range_info.get("start"))
        end = _int_value(range_info.get("end"))
        if start is None or end is None or end <= start:
            continue
        starts.append(start)
        ends.append(end)
    if not starts or not ends:
        return authority
    return {
        "kind": authority.get("kind") if authority.get("kind") in {"code", "confirmed_code"} else "candidate_code",
        "start": min(starts),
        "end": max(ends),
        "size": max(ends) - min(starts),
        "entrypoint": True,
        "evidence": "macos_code_semantic_analysis_span",
        "fact_id": authority.get("fact_id"),
        "fact_status": authority.get("fact_status"),
        "parser_use": authority.get("parser_use"),
        "kb_record_id": authority.get("kb_record_id") or code.get("kb_record_id"),
    }


def _first_executable_code_range(ranges: list[object]) -> Mapping[str, object]:
    for item in ranges:
        range_info = _mapping(item)
        if range_info.get("kind") in {"code", "confirmed_code", "candidate_code"}:
            return range_info
    return {}


def _resource_id_sort_key(value: object) -> tuple[int, object]:
    resource_id = _mapping(value).get("id")
    return (0, resource_id) if isinstance(resource_id, int) else (1, str(resource_id))


def _range_start_sort_key(value: object) -> int:
    start = _int_value(_mapping(value).get("start"))
    return start if start is not None else 0


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


def _text(value: object) -> str:
    return "unknown" if value is None else str(value)
