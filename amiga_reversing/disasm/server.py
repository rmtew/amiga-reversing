from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import queue
import threading
import time
import uuid
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import NotRequired, TypedDict, cast
from urllib.parse import parse_qs, urlparse

from amiga_reversing.amiga_disk.models import DiskManifest
from amiga_reversing.amiga_disk.project import create_disk_project
from amiga_reversing.disasm.annotations import (
    AnnotationPatchInput,
    get_entities_by_int_addr,
    get_entity,
    patch_entity,
)
from amiga_reversing.disasm.api import (
    ListingWindowPayload,
    SerializedRow,
    listing_index_window_payload,
    listing_window_payload,
)
from amiga_reversing.disasm.binary_source import write_source_descriptor
from amiga_reversing.disasm.c_backend import (
    CListingArtifact,
    build_project_listing_artifact_generation_profile,
    extract_disk_entry_with_c_backend,
    type_catalog_from_c_backend,
    validate_amiga_hunk_executable_with_c_backend,
    validate_api_input_struct_with_c_backend,
)
from amiga_reversing.disasm import corpus_usage, disk_browser
from amiga_reversing.disasm.effective_metadata import effective_metadata_hash
from amiga_reversing.disasm.listing_types import (
    AppSlotRef,
    BlockRowContext,
    ListingRow,
    PlatformUnresolvedTypedAccess,
    SymbolOperandMetadata,
)
from amiga_reversing.disasm.project_ids import derive_disk_id_from_stem, disk_project_id
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from amiga_reversing.disasm.projects import (
    ProjectRecord,
    create_project,
    dedupe_project_name,
    delete_project,
    derive_project_name,
    get_project,
    list_projects,
    mark_project_opened,
    mark_project_updated,
)
from amiga_reversing.disasm.reproduction import (
    issues_by_row_index,
    load_reproduction_report,
    reproduction_input_stamp,
    reproduction_navigation_entries,
    run_reproduction,
    source_renderer_tool_stamps,
)
from amiga_reversing.disasm.target_ui_edits import append_target_ui_edit

WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
LOGGER = logging.getLogger("amiga_reversing.disasm.server")


class EmptyListingPayload(TypedDict):
    anchor_addr: int | None
    start: int
    end: int
    has_more_before: bool
    has_more_after: bool
    total_rows: int
    rows: list[object]


class AsyncJobPayload(TypedDict):
    job_id: str
    job_kind: str
    project_id: str | None
    result_project_id: str | None
    status: str
    phase_id: str
    phase_index: int
    phase_count: int
    progress_mode: str
    progress_current: int
    progress_total: int
    progress_percent: int
    total_rows: int | None
    error: str | None
    created_at: float
    finished_at: float | None
    visible_generation: NotRequired[str | None]
    target_generation: NotRequired[str | None]
    cache_key: NotRequired[str | None]
    reproduction_status: NotRequired[str | None]


class ProjectPayload(TypedDict):
    project: dict[str, object]
    disk_manifest: NotRequired[dict[str, object]]
    reproduction: NotRequired[dict[str, object]]


class ApiResponse(TypedDict):
    ok: bool
    data: object


class StaticResponse(TypedDict):
    content_type: str
    body: bytes
    headers: dict[str, str]


_MISSING = object()
_PROJECT_ROW_CACHE: dict[str, list[ListingRow]] = {}
_PROJECT_C_LISTING_ARTIFACT_CACHE: dict[str, CListingArtifact] = {}
_PROJECT_ROW_GENERATION_CACHE: dict[str, str] = {}
_PROJECT_LISTING_TOTAL_ROWS_CACHE: dict[str, int] = {}
_PROJECT_ROW_CACHE_KEY: dict[str, str] = {}
_PROJECT_APP_SLOT_ANALYSIS_CACHE: dict[str, dict[str, object]] = {}
_PROJECT_TYPE_FLOW_ANALYSIS_CACHE: dict[str, dict[str, object]] = {}
type ApiCallRowKey = tuple[int, int]


_PROJECT_API_CALL_CACHE: dict[str, dict[ApiCallRowKey, dict[str, object]]] = {}
_ASYNC_JOBS: dict[str, AsyncJobPayload] = {}
_JOB_EVENT_SUBSCRIBERS: dict[str, list[queue.Queue[dict[str, object]]]] = {}
_JOB_LOCK = threading.Lock()

_LISTING_PHASE_COUNT = 2
_REPRODUCTION_PHASE_COUNT = 4
_PROJECT_CREATE_EXECUTABLE_PHASE_COUNT = 4
_PROJECT_CREATE_DISK_PHASE_COUNT = 5

_OS_CORRECTIONS_PATH = (
    Path(__file__).resolve().parents[2] / "knowledge" / "amiga_ndk_corrections.json"
)
_API_CALL_NOTE_INDEXED_VECTOR = 1
_API_CALL_NOTE_LOCAL_WRAPPER_SYMBOL = 3
_APP_SLOT_ACCESS_ORDER = ("read", "write", "read-write", "address")


def _os_corrections_payload() -> dict[str, object]:
    with open(_OS_CORRECTIONS_PATH, encoding="utf-8") as handle:
        return cast(dict[str, object], json.load(handle))


def _annotate_api_calls(
    project_name: str, payload: ListingWindowPayload
) -> ListingWindowPayload:
    call_rows = _PROJECT_API_CALL_CACHE.get(project_name, {})
    rows: list[SerializedRow] = []
    for row in payload["rows"]:
        addr = row["addr"]
        source_context = row["source_context"]
        hunk_index = source_context.get("hunk_index")
        if (
            row["kind"] == "instruction"
            and isinstance(hunk_index, int)
            and isinstance(addr, int)
            and (hunk_index, addr) in call_rows
        ):
            rows.append(
                cast(
                    SerializedRow,
                    {**row, "api_call": call_rows[(hunk_index, addr)]},
                )
            )
        else:
            rows.append(row)
    return {**payload, "rows": rows}


def _type_catalog_payload(project_name: str) -> list[dict[str, object]]:
    return type_catalog_from_c_backend(project_name)


def _valid_c_listing_artifact(project_name: str) -> CListingArtifact | None:
    artifact = _PROJECT_C_LISTING_ARTIFACT_CACHE.get(project_name)
    if (
        artifact is not None
        and _PROJECT_ROW_GENERATION_CACHE.get(project_name) == "full"
        and project_name in _PROJECT_ROW_CACHE_KEY
        and _PROJECT_ROW_CACHE_KEY.get(project_name) == _project_listing_cache_key(project_name)
    ):
        return artifact
    return None


def _write_api_input_type_override(
    *, library: str, function: str, input_name: str, struct_name: str
) -> None:
    payload = _os_corrections_payload()
    meta = cast(dict[str, object], payload.setdefault("_meta", {}))
    overrides = cast(
        list[dict[str, object]], meta.setdefault("api_input_type_overrides", [])
    )
    replacement: dict[str, object] = {
        "library": library,
        "function": function,
        "input": input_name,
        "type": f"struct {struct_name} *",
        "i_struct": struct_name,
        "seed_origin": "manual",
        "review_status": "validated",
        "citation": "User-edited via disasm UI",
    }
    replaced = False
    for index, existing in enumerate(overrides):
        if (
            existing.get("library") == library
            and existing.get("function") == function
            and existing.get("input") == input_name
        ):
            overrides[index] = replacement
            replaced = True
            break
    if not replaced:
        overrides.append(replacement)
    overrides.sort(
        key=lambda item: (
            str(item.get("library", "")),
            str(item.get("function", "")),
            str(item.get("input", "")),
        )
    )
    _OS_CORRECTIONS_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _PROJECT_ROW_CACHE.clear()
    for artifact in _PROJECT_C_LISTING_ARTIFACT_CACHE.values():
        artifact.close()
    _PROJECT_C_LISTING_ARTIFACT_CACHE.clear()
    _PROJECT_ROW_GENERATION_CACHE.clear()
    _PROJECT_LISTING_TOTAL_ROWS_CACHE.clear()
    _PROJECT_ROW_CACHE_KEY.clear()
    _PROJECT_APP_SLOT_ANALYSIS_CACHE.clear()
    _PROJECT_TYPE_FLOW_ANALYSIS_CACHE.clear()
    _PROJECT_API_CALL_CACHE.clear()
    _cancel_listing_jobs()


def _validate_api_input_struct(
    project_name: str,
    library: str,
    function: str,
    input_name: str,
    struct_name: str,
) -> dict[str, object]:
    return validate_api_input_struct_with_c_backend(
        project_name, library, function, input_name, struct_name
    )


def _annotate_listing_payload(
    project_name: str, payload: ListingWindowPayload
) -> ListingWindowPayload:
    annotated_rows: list[SerializedRow] = []
    repro_issues = _active_reproduction_issues_by_row_index(project_name)
    window_start = int(payload.get("start") or 0)
    try:
        entities_by_addr = get_entities_by_int_addr(project_name, project_root=PROJECT_ROOT)
    except (FileNotFoundError, ValueError, AssertionError):
        entities_by_addr = {}
    for relative_index, row in enumerate(payload["rows"]):
        annotations: list[str] = []
        entity = None
        entity_addr = row.get("entity_addr")
        if isinstance(entity_addr, int):
            entity = entities_by_addr.get(entity_addr)
            if entity is not None:
                for field_name in ("name", "comment", "type", "subtype", "confidence"):
                    value = entity.get(field_name)
                    if isinstance(value, str) and value:
                        annotations.append(value)
        entity_payload = cast(dict[str, object], entity) if entity is not None else None
        row_issues = repro_issues.get(window_start + relative_index, [])
        if row_issues:
            annotations.append("REPRO: " + str(row_issues[0].get("summary") or row_issues[0].get("message") or "issue"))
        annotated_row = dict(row)
        if entity_payload is not None:
            annotated_row["entity"] = entity_payload
        if annotations:
            annotated_row["view_annotations"] = annotations
        if row_issues:
            annotated_row["repro_issues"] = row_issues
        annotated_rows.append(cast(SerializedRow, annotated_row))
    payload = {
        **payload,
        "rows": annotated_rows,
    }
    return _annotate_api_calls(project_name, payload)


def _active_reproduction_report(project_name: str) -> dict[str, object] | None:
    try:
        report = load_reproduction_report(project_name, project_root=PROJECT_ROOT)
    except (FileNotFoundError, ValueError, RuntimeError):
        return None
    if report.get("stale"):
        return None
    return report


def _active_reproduction_issues_by_row_index(
    project_name: str,
) -> dict[int, list[dict[str, object]]]:
    report = _active_reproduction_report(project_name)
    if report is None:
        return {}
    return issues_by_row_index(report)


def _not_ready_reproduction_payload(
    project_name: str, error: str | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "target": project_name,
        "status": "not_ready",
        "exact": False,
        "stale": False,
        "issues": [],
        "diff_ranges": [],
        "assembler_diagnostics": [],
    }
    if error:
        payload["error"] = error
    return payload


def _active_reproduction_job(
    project_name: str, cache_key: str | None = None
) -> AsyncJobPayload | None:
    with _JOB_LOCK:
        for job in _ASYNC_JOBS.values():
            if (
                job["job_kind"] == "reproduction"
                and job["project_id"] == project_name
                and job["status"] in {"queued", "building"}
                and (cache_key is None or job.get("cache_key") == cache_key)
            ):
                return cast(AsyncJobPayload, dict(job))
    return None


def _reproduction_payload_with_job(
    report: dict[str, object], job: AsyncJobPayload | None
) -> dict[str, object]:
    payload = dict(report)
    if job is not None and job["status"] in {"queued", "building"}:
        payload["refreshing"] = True
        payload["active_job"] = dict(job)
    else:
        payload["refreshing"] = False
    return payload


def _current_reproduction_payload(
    project_name: str, *, auto_start: bool = False
) -> dict[str, object]:
    try:
        report = load_reproduction_report(project_name, project_root=PROJECT_ROOT)
    except Exception as exc:
        report = _not_ready_reproduction_payload(project_name, str(exc))
    cache_key = _reproduction_cache_key(project_name)
    job: AsyncJobPayload | None = None
    if "reproduction-unresolved" not in cache_key:
        job = _active_reproduction_job(project_name, cache_key)
        if (
            job is None
            and auto_start
            and (report.get("status") == "not_ready" or bool(report.get("stale")))
        ):
            job = _start_reproduction_job(project_name, force=False)
            if job["status"] == "ready":
                try:
                    report = load_reproduction_report(project_name, project_root=PROJECT_ROOT)
                except Exception:
                    pass
                job = None
    return _reproduction_payload_with_job(report, job)


def _entity_annotation_values(entity: dict[str, object] | None) -> list[str]:
    if entity is None:
        return []
    annotations: list[str] = []
    for field_name in ("name", "comment", "type", "subtype", "confidence"):
        value = entity.get(field_name)
        if isinstance(value, str) and value:
            annotations.append(value)
    return annotations


def _listing_row_code(row: ListingRow) -> str:
    if row.label:
        return row.label
    if row.opcode_or_directive:
        return " ".join(part for part in (row.opcode_or_directive, row.operand_text) if part).strip()
    return row.text.strip()


def _listing_anchor_code_start(rows: list[ListingRow], anchor_code: str) -> int:
    wanted = anchor_code.strip()
    if not wanted:
        return 0
    for index, row in enumerate(rows):
        if _listing_row_code(row).strip() == wanted:
            return index
    return 0


def _listing_row_has_segment_reference(row: ListingRow) -> bool:
    return any(operand.segment_addr is not None for operand in row.operand_parts)


def _listing_row_has_typed_data(row: ListingRow) -> bool:
    if row.typed_accesses:
        return True
    return row.kind not in {"instruction", "label"} and (
        bool(row.comment_text) or row.structured_data is not None
    )


def _listing_row_is_label(row: ListingRow) -> bool:
    return bool(row.label) or _listing_row_code(row).endswith(":")


def _api_call_same_function(left: dict[str, object], right: dict[str, object]) -> bool:
    return left.get("library") == right.get("library") and left.get("function") == right.get("function")


def _api_call_has_near_lvo_reference(
    api_calls: dict[ApiCallRowKey, dict[str, object]],
    hunk_index: int,
    offset: int,
    api_call: dict[str, object],
) -> bool:
    for probe_offset in range(max(0, offset - 8), offset):
        candidate = api_calls.get((hunk_index, probe_offset))
        if (
            candidate is not None
            and candidate.get("note_kind") == 0
            and _api_call_same_function(candidate, api_call)
        ):
            return True
    return False


def _api_call_is_navigation_target(
    api_calls: dict[ApiCallRowKey, dict[str, object]],
    hunk_index: int,
    offset: int,
    api_call: dict[str, object],
) -> bool:
    if api_call.get("note_kind") == _API_CALL_NOTE_LOCAL_WRAPPER_SYMBOL:
        return False
    if (
        api_call.get("note_kind") == _API_CALL_NOTE_INDEXED_VECTOR
        and _api_call_has_near_lvo_reference(api_calls, hunk_index, offset, api_call)
    ):
        return False
    return True


def _signed_hex_offset(value: int) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):04X}"


def _unresolved_typed_access_summary(access: PlatformUnresolvedTypedAccess) -> str:
    root = access.root_struct_name or "typed base"
    displacement = _signed_hex_offset(access.displacement)
    joiner = "" if access.displacement < 0 else "+"
    if access.classification == "prefix_extension":
        if access.refinement_applied and access.refined_struct_name:
            return f"{root}{joiner}{displacement} refines to {access.refined_struct_name}"
        if access.container_struct_name and access.container_field_expr:
            return f"{root}{joiner}{displacement} prefix extension: {access.container_struct_name}.{access.container_field_expr}"
        if access.container_struct_name:
            return f"{root}{joiner}{displacement} prefix extension: {access.container_struct_name}"
        if access.container_candidate_count:
            return f"{root}{joiner}{displacement} prefix extension ({access.container_candidate_count} candidate types)"
        return f"{root}{joiner}{displacement} prefix extension"
    if access.classification == "custom_tail_or_mistyped_base":
        return f"{root}{joiner}{displacement} unknown extension"
    return f"{root}{joiner}{displacement} field metadata gap"


def _listing_navigation_summary(
    row: ListingRow,
    jump_class: str,
    api_call: dict[str, object] | None = None,
    annotations: list[str] | None = None,
) -> str:
    if jump_class == "api-calls" and api_call:
        library = api_call.get("library", "")
        function = api_call.get("function", "")
        if api_call.get("note_kind") == 1:
            return f"{function} dispatch ({library})".strip()
        return f"{function} ({library})".strip()
    if jump_class == "comments" and annotations:
        return "; ".join(annotations)
    if jump_class == "typed-data" and row.typed_accesses:
        access = row.typed_accesses[0]
        owner = access.owner_struct_name or access.root_struct_name or ""
        field = access.field_expr or access.field_name or ""
        if owner and field:
            return f"{owner}.{field}"
        if field:
            return field
        if owner:
            return owner
    if jump_class == "typed-gaps" and row.unresolved_typed_accesses:
        return _unresolved_typed_access_summary(row.unresolved_typed_accesses[0])
    if jump_class == "typed-data" and (row.comment_text or row.structured_data):
        structured = row.structured_data or {}
        for key in ("label", "field_name"):
            value = structured.get(key)
            if isinstance(value, str) and value:
                return row.comment_text or value
        return row.comment_text or row.kind
    if jump_class == "labels":
        return _listing_row_code(row)
    return _listing_row_code(row) or row.comment_text or row.kind


def _navigation_entry(
    row: ListingRow,
    row_index: int,
    jump_class: str,
    api_call: dict[str, object] | None = None,
    annotations: list[str] | None = None,
) -> dict[str, object]:
    assert row.addr is not None
    entry = {
        "addr": row.addr,
        "row_index": row_index,
        "summary": _listing_navigation_summary(row, jump_class, api_call, annotations),
        "match_text": _listing_row_code(row),
        "stable_key": row.stable_key,
    }
    if isinstance(row.source_context, BlockRowContext):
        entry["hunk_index"] = row.source_context.hunk_index
    if row.section_index is not None:
        entry["section_index"] = row.section_index
    return entry


def _ordered_app_slot_access_counts(access_counts: dict[str, int]) -> dict[str, int]:
    ordered = {access: access_counts[access] for access in _APP_SLOT_ACCESS_ORDER if access_counts.get(access)}
    for access, count in sorted(access_counts.items()):
        if access not in ordered and count:
            ordered[access] = count
    return ordered


def _app_slot_navigation_ref_entry(row: ListingRow, row_index: int, ref: AppSlotRef) -> dict[str, object]:
    entry = _navigation_entry(row, row_index, "app-slots")
    entry.update(
        {
            "symbol": ref.symbol,
            "displacement": ref.displacement,
            "base_register": ref.base_register,
            "operand_index": ref.operand_index,
            "access": ref.access,
            "summary": _listing_row_code(row) or ref.symbol,
        }
    )
    return entry


def _typed_gap_navigation_entry(
    row: ListingRow,
    row_index: int,
    access: PlatformUnresolvedTypedAccess,
) -> dict[str, object]:
    entry = _navigation_entry(row, row_index, "typed-gaps")
    entry.update(
        {
            "root_struct_name": access.root_struct_name,
            "base_register": access.base_register,
            "operand_index": access.operand_index,
            "displacement": access.displacement,
            "struct_size": access.struct_size,
            "classification": access.classification,
            "container_candidate_count": access.container_candidate_count,
            "container_struct_name": access.container_struct_name,
            "container_field_expr": access.container_field_expr,
            "refinement_applied": access.refinement_applied,
            "refined_struct_name": access.refined_struct_name,
            "type_provenance_kind": access.type_provenance_kind,
            "type_provenance_section": access.type_provenance_section,
            "type_provenance_offset": access.type_provenance_offset,
            "summary": _unresolved_typed_access_summary(access),
        }
    )
    return entry


def _app_slot_region_navigation_entry(region: dict[str, object]) -> dict[str, object]:
    offset = cast(int, region.get("offset", 0))
    end = cast(int, region.get("end", offset))
    struct_name = cast(str, region.get("struct_name") or "")
    symbol = cast(str, region.get("symbol") or "")
    evidence = cast(list[dict[str, object]], region.get("evidence", []))
    first_evidence = evidence[0] if evidence else {}
    summary_type = f": {struct_name}" if struct_name else ""
    entry: dict[str, object] = {
        "summary": f"{symbol}{summary_type} ${offset:04X}-${end:04X}",
        "match_text": symbol,
        "symbol": symbol,
        "offset": offset,
        "end": end,
        "size": region.get("size"),
        "source": region.get("source"),
        "confidence": region.get("confidence"),
        "struct_name": struct_name,
        "field_ref_count": len(cast(list[dict[str, object]], region.get("field_refs", []))),
        "field_paths": [
            ".".join([struct_name, *path])
            for path in (
                field_ref.get("field_path")
                for field_ref in cast(list[dict[str, object]], region.get("field_refs", []))
                if isinstance(field_ref, dict)
            )
            if isinstance(path, list) and all(isinstance(part, str) for part in path)
        ],
    }
    if isinstance(first_evidence.get("row_index"), int):
        entry["row_index"] = first_evidence["row_index"]
    if isinstance(first_evidence.get("addr"), int):
        entry["addr"] = first_evidence["addr"]
    if isinstance(first_evidence.get("hunk_index"), int):
        entry["hunk_index"] = first_evidence["hunk_index"]
    if isinstance(first_evidence.get("stable_key"), str):
        entry["stable_key"] = first_evidence["stable_key"]
    return entry


def _app_slot_field_gap_navigation_entry(gap: dict[str, object]) -> dict[str, object]:
    start = cast(int, gap.get("start", 0))
    end = cast(int, gap.get("end", start))
    size = max(0, end - start)
    struct_name = cast(str, gap.get("struct_name") or "")
    field_path = gap.get("field_path")
    field_label = ""
    if isinstance(field_path, list) and all(isinstance(part, str) for part in field_path):
        field_label = ".".join([struct_name, *field_path])
    coverage = cast(str, gap.get("coverage") or "unknown")
    suffix = f" {field_label}" if field_label else f" {coverage}"
    return {
        "summary": f"Field gap ${start:04X}-${end:04X} ({size} bytes){suffix}",
        "match_text": field_label,
        "navigable": False,
        "start": start,
        "end": end,
        "size": size,
        "coverage": coverage,
        "field_path": field_path,
        "region_id": gap.get("region_id"),
        "symbol": gap.get("symbol"),
        "struct_name": struct_name,
    }


def _app_slot_gap_navigation_entry(gap: dict[str, object]) -> dict[str, object]:
    start = cast(int, gap.get("start", 0))
    end = cast(int, gap.get("end", start))
    size = max(0, end - start)
    return {
        "summary": f"Gap ${start:04X}-${end:04X} ({size} bytes)",
        "match_text": "",
        "navigable": False,
        "start": start,
        "end": end,
        "size": size,
        "after": gap.get("after"),
        "before": gap.get("before"),
        "coverage": gap.get("coverage"),
    }


def _app_slot_suggestion_navigation_entry(suggestion: dict[str, object]) -> dict[str, object]:
    metadata = suggestion.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    evidence = cast(list[dict[str, object]], suggestion.get("evidence", []))
    first_evidence = evidence[0] if evidence else {}
    offset = cast(int, metadata.get("offset", 0))
    size = cast(int, metadata.get("size", 0))
    struct_name = cast(str, metadata.get("struct_name") or "")
    symbol = cast(str, metadata.get("symbol") or "")
    summary_type = f": {struct_name}" if struct_name else ""
    entry: dict[str, object] = {
        "summary": cast(str, suggestion.get("summary") or f"Suggest {symbol}{summary_type} ${offset:04X}"),
        "match_text": symbol,
        "symbol": symbol,
        "offset": offset,
        "size": size,
        "struct_name": struct_name,
        "action": suggestion.get("action"),
        "confidence": suggestion.get("confidence"),
        "metadata": metadata,
    }
    for source_key, target_key in (("row_index", "row_index"), ("addr", "addr"), ("hunk_index", "hunk_index")):
        if source_key in first_evidence:
            entry[target_key] = first_evidence[source_key]
    if isinstance(first_evidence.get("stable_key"), str):
        entry["stable_key"] = first_evidence["stable_key"]
    return entry


def _app_slot_untyped_api_arg_navigation_entry(arg: dict[str, object]) -> dict[str, object]:
    offset = cast(int, arg.get("displacement", 0))
    symbol = cast(str, arg.get("symbol") or "")
    function_name = cast(str, arg.get("function") or "")
    input_name = cast(str, arg.get("input_name") or "")
    register = cast(str, arg.get("register") or "")
    reason = cast(str, arg.get("reason") or "untyped")
    summary_input = f" {input_name}" if input_name else ""
    entry: dict[str, object] = {
        "summary": f"{symbol} -> {function_name}{summary_input} {register} ({reason})",
        "match_text": symbol,
        "symbol": symbol,
        "offset": offset,
        "displacement": offset,
        "function": function_name,
        "input_name": input_name,
        "register": register,
        "reason": reason,
        "type_name": arg.get("type_name"),
    }
    for key in ("row_index", "addr", "hunk_index", "source_row_index", "source_flow_row_index"):
        if isinstance(arg.get(key), int):
            entry[key] = arg[key]
    for key in ("stable_key", "source_stable_key"):
        if isinstance(arg.get(key), str):
            entry[key] = arg[key]
    return entry


def _listing_label_symbol(row: ListingRow) -> str | None:
    if row.label:
        symbol = row.label.rstrip(":").strip()
        return symbol or None
    text = _listing_row_code(row).strip()
    if not text.endswith(":"):
        return None
    symbol = text[:-1].strip()
    return symbol or None


def _listing_row_symbol_operands(row: ListingRow) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    for operand in row.operand_parts:
        symbol = None
        if isinstance(operand.metadata, SymbolOperandMetadata):
            symbol = operand.metadata.symbol
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols


def _label_navigation_ref_entry(row: ListingRow, row_index: int, symbol: str, access: str) -> dict[str, object]:
    entry = _navigation_entry(row, row_index, "labels")
    entry.update(
        {
            "symbol": symbol,
            "access": access,
            "summary": f"{symbol}:" if access == "definition" else (_listing_row_code(row) or symbol),
        }
    )
    return entry


def _listing_navigation_payload(project_name: str, rows: list[ListingRow]) -> dict[str, object]:
    groups: dict[str, list[dict[str, object]]] = {
        "repro-issues": [],
        "typed-data": [],
        "typed-gaps": [],
        "relocations": [],
        "api-calls": [],
        "app-slots": [],
        "app-slot-regions": [],
        "app-slot-gaps": [],
        "app-slot-field-gaps": [],
        "app-slot-suggestions": [],
        "app-slot-api-args": [],
        "labels": [],
        "comments": [],
    }
    repro_report = _active_reproduction_report(project_name)
    if repro_report is not None:
        groups["repro-issues"] = reproduction_navigation_entries(repro_report)
    api_calls = _PROJECT_API_CALL_CACHE.get(project_name, {})
    try:
        entities_by_addr = get_entities_by_int_addr(project_name, project_root=PROJECT_ROOT)
    except (FileNotFoundError, ValueError, AssertionError):
        entities_by_addr = {}
    app_slots: dict[str, dict[str, object]] = {}
    labels: dict[str, dict[str, object]] = {}
    for row_index, row in enumerate(rows):
        if row.addr is None or not _listing_row_is_label(row):
            continue
        symbol = _listing_label_symbol(row)
        if symbol is None:
            continue
        label_entry = _navigation_entry(row, row_index, "labels")
        label_entry.update(
            {
                "symbol": symbol,
                "summary": f"{symbol}:",
                "ref_count": 1,
                "access_counts": {"definition": 1},
                "refs": [_label_navigation_ref_entry(row, row_index, symbol, "definition")],
            }
        )
        labels[symbol] = label_entry
    for row_index, row in enumerate(rows):
        if row.addr is None:
            continue
        entity = entities_by_addr.get(row.entity_addr) if isinstance(row.entity_addr, int) else None
        annotations = _entity_annotation_values(cast(dict[str, object] | None, entity))
        api_call = None
        if isinstance(row.source_context, BlockRowContext):
            api_call = api_calls.get((row.source_context.hunk_index, row.addr))
        if _listing_row_has_typed_data(row):
            groups["typed-data"].append(_navigation_entry(row, row_index, "typed-data"))
        for access in row.unresolved_typed_accesses:
            groups["typed-gaps"].append(_typed_gap_navigation_entry(row, row_index, access))
        if _listing_row_has_segment_reference(row):
            groups["relocations"].append(_navigation_entry(row, row_index, "relocations"))
        if (
            row.kind == "instruction"
            and api_call is not None
            and isinstance(row.source_context, BlockRowContext)
            and _api_call_is_navigation_target(api_calls, row.source_context.hunk_index, row.addr, api_call)
        ):
            groups["api-calls"].append(_navigation_entry(row, row_index, "api-calls", api_call))
        for ref in row.app_slot_refs:
            slot_entry = app_slots.setdefault(
                ref.symbol,
                {
                    "symbol": ref.symbol,
                    "summary": ref.symbol,
                    "match_text": ref.symbol,
                    "displacement": ref.displacement,
                    "ref_count": 0,
                    "access_counts": {},
                    "refs": [],
                },
            )
            refs = cast(list[dict[str, object]], slot_entry["refs"])
            access_counts = cast(dict[str, int], slot_entry["access_counts"])
            refs.append(_app_slot_navigation_ref_entry(row, row_index, ref))
            access_counts[ref.access] = access_counts.get(ref.access, 0) + 1
        for symbol in _listing_row_symbol_operands(row):
            label_entry = labels.get(symbol)
            if label_entry is None:
                continue
            refs = cast(list[dict[str, object]], label_entry["refs"])
            access_counts = cast(dict[str, int], label_entry["access_counts"])
            refs.append(_label_navigation_ref_entry(row, row_index, symbol, "reference"))
            label_entry["ref_count"] = cast(int, label_entry["ref_count"]) + 1
            access_counts["reference"] = access_counts.get("reference", 0) + 1
        if row.comment_text or annotations:
            groups["comments"].append(_navigation_entry(row, row_index, "comments", annotations=annotations))
    for slot_entry in app_slots.values():
        refs = cast(list[dict[str, object]], slot_entry["refs"])
        refs.sort(key=lambda entry: cast(int, entry.get("row_index", -1)))
        slot_entry["ref_count"] = len(refs)
        slot_entry["access_counts"] = _ordered_app_slot_access_counts(cast(dict[str, int], slot_entry["access_counts"]))
    app_slot_analysis = _PROJECT_APP_SLOT_ANALYSIS_CACHE.get(
        project_name,
        {
            "slot_count": 0,
            "ref_count": 0,
            "typed_region_count": 0,
            "gap_count": 0,
            "field_gap_count": 0,
            "suggestion_count": 0,
            "untyped_api_arg_count": 0,
            "slots": [],
            "regions": [],
            "gaps": [],
            "field_gaps": [],
            "suggestions": [],
            "untyped_api_args": [],
        },
    )
    app_slot_summaries = {
        cast(str, slot["symbol"]): slot
        for slot in cast(list[dict[str, object]], app_slot_analysis.get("slots", []))
        if isinstance(slot.get("symbol"), str)
    }
    for slot_entry in app_slots.values():
        slot_summary = app_slot_summaries.get(cast(str, slot_entry.get("symbol", "")))
        if slot_summary is None:
            continue
        for key in (
            "base_registers",
            "width_counts",
            "observed_size",
            "observed_end",
            "first_row_index",
            "last_row_index",
            "first_addr",
            "last_addr",
            "containing_regions",
        ):
            if key in slot_summary:
                slot_entry[key] = slot_summary[key]
    groups["app-slot-regions"] = [
        _app_slot_region_navigation_entry(region)
        for region in cast(list[dict[str, object]], app_slot_analysis.get("regions", []))
        if region.get("source") == "platform_api_arg"
    ]
    groups["app-slot-gaps"] = [
        _app_slot_gap_navigation_entry(gap)
        for gap in cast(list[dict[str, object]], app_slot_analysis.get("gaps", []))
    ]
    groups["app-slot-field-gaps"] = [
        _app_slot_field_gap_navigation_entry(gap)
        for gap in cast(list[dict[str, object]], app_slot_analysis.get("field_gaps", []))
    ]
    groups["app-slot-suggestions"] = [
        _app_slot_suggestion_navigation_entry(suggestion)
        for suggestion in cast(list[dict[str, object]], app_slot_analysis.get("suggestions", []))
    ]
    groups["app-slot-api-args"] = [
        _app_slot_untyped_api_arg_navigation_entry(arg)
        for arg in cast(list[dict[str, object]], app_slot_analysis.get("untyped_api_args", []))
    ]
    groups["app-slots"] = sorted(
        app_slots.values(),
        key=lambda entry: (cast(int, entry.get("displacement", 0)), cast(str, entry.get("symbol", ""))),
    )
    for label_entry in labels.values():
        refs = cast(list[dict[str, object]], label_entry["refs"])
        refs.sort(key=lambda entry: cast(int, entry.get("row_index", -1)))
    groups["labels"] = sorted(labels.values(), key=lambda entry: cast(int, entry.get("row_index", -1)))
    return {
        "analysis_generation": _PROJECT_ROW_GENERATION_CACHE.get(project_name),
        "total_rows": len(rows),
        "groups": groups,
        "app_slot_analysis": app_slot_analysis,
        "type_flow_analysis": _PROJECT_TYPE_FLOW_ANALYSIS_CACHE.get(project_name, {}),
    }


def _overlay_listing_navigation_payload(
    project_name: str,
    payload: dict[str, object],
    rows: list[ListingRow] | None = None,
) -> dict[str, object]:
    groups = cast(dict[str, list[dict[str, object]]], payload.setdefault("groups", {}))
    for group_name in (
        "repro-issues",
        "typed-data",
        "typed-gaps",
        "relocations",
        "api-calls",
        "app-slots",
        "app-slot-regions",
        "app-slot-gaps",
        "app-slot-field-gaps",
        "app-slot-suggestions",
        "app-slot-api-args",
        "labels",
        "comments",
    ):
        groups.setdefault(group_name, [])
    repro_report = _active_reproduction_report(project_name)
    if repro_report is not None:
        groups["repro-issues"] = reproduction_navigation_entries(repro_report)
    if rows is not None:
        try:
            entities_by_addr = get_entities_by_int_addr(project_name, project_root=PROJECT_ROOT)
        except (FileNotFoundError, ValueError, AssertionError):
            entities_by_addr = {}
        for row_index, row in enumerate(rows):
            if row.addr is None:
                continue
            entity = entities_by_addr.get(row.entity_addr) if isinstance(row.entity_addr, int) else None
            annotations = _entity_annotation_values(cast(dict[str, object] | None, entity))
            if annotations:
                groups["comments"].append(_navigation_entry(row, row_index, "comments", annotations=annotations))
    app_slot_analysis = cast(dict[str, object], payload.get("app_slot_analysis") or {})
    if not groups["app-slot-regions"]:
        groups["app-slot-regions"] = [
            _app_slot_region_navigation_entry(region)
            for region in cast(list[dict[str, object]], app_slot_analysis.get("regions", []))
            if region.get("source") == "platform_api_arg"
        ]
    if not groups["app-slot-gaps"]:
        groups["app-slot-gaps"] = [
            _app_slot_gap_navigation_entry(gap)
            for gap in cast(list[dict[str, object]], app_slot_analysis.get("gaps", []))
        ]
    if not groups["app-slot-field-gaps"]:
        groups["app-slot-field-gaps"] = [
            _app_slot_field_gap_navigation_entry(gap)
            for gap in cast(list[dict[str, object]], app_slot_analysis.get("field_gaps", []))
        ]
    if not groups["app-slot-suggestions"]:
        groups["app-slot-suggestions"] = [
            _app_slot_suggestion_navigation_entry(suggestion)
            for suggestion in cast(list[dict[str, object]], app_slot_analysis.get("suggestions", []))
        ]
    if not groups["app-slot-api-args"]:
        groups["app-slot-api-args"] = [
            _app_slot_untyped_api_arg_navigation_entry(arg)
            for arg in cast(list[dict[str, object]], app_slot_analysis.get("untyped_api_args", []))
        ]
    if "analysis_generation" not in payload or payload.get("analysis_generation") is None:
        payload["analysis_generation"] = _PROJECT_ROW_GENERATION_CACHE.get(project_name)
    if "type_flow_analysis" not in payload or not isinstance(payload.get("type_flow_analysis"), dict):
        payload["type_flow_analysis"] = _PROJECT_TYPE_FLOW_ANALYSIS_CACHE.get(project_name, {})
    payload["groups"] = groups
    return payload


def _clear_project_listing_cache(project_name: str) -> None:
    _PROJECT_ROW_CACHE.pop(project_name, None)
    artifact = _PROJECT_C_LISTING_ARTIFACT_CACHE.pop(project_name, None)
    if artifact is not None:
        artifact.close()
    _PROJECT_ROW_GENERATION_CACHE.pop(project_name, None)
    _PROJECT_LISTING_TOTAL_ROWS_CACHE.pop(project_name, None)
    _PROJECT_ROW_CACHE_KEY.pop(project_name, None)
    _PROJECT_APP_SLOT_ANALYSIS_CACHE.pop(project_name, None)
    _PROJECT_TYPE_FLOW_ANALYSIS_CACHE.pop(project_name, None)
    _PROJECT_API_CALL_CACHE.pop(project_name, None)


def _cached_project_rows(project_name: str) -> list[ListingRow] | None:
    rows = _PROJECT_ROW_CACHE.get(project_name)
    if (
        rows is not None
        and project_name in _PROJECT_ROW_CACHE_KEY
        and _PROJECT_ROW_CACHE_KEY.get(project_name) != _project_listing_cache_key(project_name)
    ):
        _clear_project_listing_cache(project_name)
        return None
    return rows


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _log_event(message: str, **fields: object) -> None:
    suffix = " ".join(f"{key}={value}" for key, value in fields.items())
    LOGGER.info("%s%s", message, f" {suffix}" if suffix else "")


def _parse_int_arg(
    values: dict[str, list[str]], key: str, default: int | None = None
) -> int | None:
    raw_values = values.get(key)
    raw = raw_values[0] if raw_values else None
    if raw in (None, ""):
        return default
    assert raw is not None
    return int(raw, 0)


def _first_query_value(values: dict[str, list[str]], key: str) -> str | None:
    raw_values = values.get(key)
    raw = raw_values[0] if raw_values else None
    if raw in (None, ""):
        return None
    return raw


def _empty_listing_payload(addr: int | None) -> EmptyListingPayload:
    return {
        "anchor_addr": addr,
        "start": 0,
        "end": 0,
        "has_more_before": False,
        "has_more_after": False,
        "total_rows": 0,
        "rows": [],
    }


def _phase_progress(phase_index: int, phase_count: int) -> tuple[int, int, int]:
    if phase_count <= 0:
        raise ValueError(f"phase_count must be positive, got {phase_count}")
    if phase_index < 0 or phase_index > phase_count:
        raise ValueError(f"phase_index {phase_index} outside 0..{phase_count}")
    completed = 0 if phase_index == 0 else phase_index - 1
    return completed, phase_count, int((completed / phase_count) * 100)


def _job_payload(job_id: str) -> AsyncJobPayload:
    with _JOB_LOCK:
        job = dict(_ASYNC_JOBS[job_id])
        project_id = job.get("project_id")
        if isinstance(project_id, str) and job.get("job_kind") == "full_listing":
            job["visible_generation"] = _PROJECT_ROW_GENERATION_CACHE.get(project_id) or (
                "full" if project_id in _PROJECT_C_LISTING_ARTIFACT_CACHE else None
            )
            total_rows = _PROJECT_LISTING_TOTAL_ROWS_CACHE.get(project_id)
            if total_rows is not None:
                job["total_rows"] = total_rows
    return cast(AsyncJobPayload, job)


def _job_payload_or_none(job_id: str) -> AsyncJobPayload | None:
    with _JOB_LOCK:
        if job_id not in _ASYNC_JOBS:
            return None
    return _job_payload(job_id)


def _publish_job_event_payload(job_id: str, payload: dict[str, object]) -> None:
    with _JOB_LOCK:
        subscribers = list(_JOB_EVENT_SUBSCRIBERS.get(job_id, []))
    for subscriber in subscribers:
        try:
            subscriber.put_nowait(payload)
        except queue.Full:  # pragma: no cover - queues are unbounded
            pass


def _publish_job_event(job_id: str) -> None:
    payload = _job_payload_or_none(job_id)
    if payload is not None:
        _publish_job_event_payload(job_id, payload)


def _listing_changed_ranges(rows: list[ListingRow]) -> list[dict[str, int]]:
    ranges_by_section: dict[int, list[int]] = {}
    for row in rows:
        section_index = row.section_index
        start_offset = row.start_offset
        end_offset = row.end_offset
        if section_index is None and isinstance(row.source_context, BlockRowContext):
            section_index = row.source_context.hunk_index
        if start_offset is None:
            start_offset = row.addr
        if end_offset is None:
            end_offset = start_offset
        if section_index is None or start_offset is None or end_offset is None:
            continue
        current = ranges_by_section.setdefault(section_index, [start_offset, end_offset])
        current[0] = min(current[0], start_offset)
        current[1] = max(current[1], end_offset)
    return [
        {"section_index": section_index, "start_offset": values[0], "end_offset": values[1]}
        for section_index, values in sorted(ranges_by_section.items())
    ]


def _publish_listing_generation_ready_event(
    job_id: str, project_name: str, generation: str, total_rows: int, rows: list[ListingRow]
) -> None:
    _publish_job_event_payload(
        job_id,
        {
            "_event_type": "listing_generation_ready",
            "project_id": project_name,
            "generation": generation,
            "total_rows": total_rows,
            "changed_ranges": _listing_changed_ranges(rows),
        },
    )


def _cancel_listing_jobs(project_name: str | None = None) -> None:
    canceled: list[tuple[str, AsyncJobPayload]] = []
    with _JOB_LOCK:
        stale_job_ids = [
            job_id
            for job_id, job in _ASYNC_JOBS.items()
            if job["job_kind"] == "full_listing"
            and (project_name is None or job["project_id"] == project_name)
        ]
        for job_id in stale_job_ids:
            job = dict(_ASYNC_JOBS[job_id])
            job["status"] = "failed"
            job["phase_id"] = "error"
            job["error"] = "job canceled"
            job["finished_at"] = time.time()
            canceled.append((job_id, cast(AsyncJobPayload, job)))
            del _ASYNC_JOBS[job_id]
    for job_id, payload in canceled:
        _publish_job_event_payload(job_id, payload)


def _set_job_state(
    job_id: str,
    *,
    status: str | object = _MISSING,
    phase_id: str | object = _MISSING,
    phase_index: int | object = _MISSING,
    phase_count: int | object = _MISSING,
    progress_mode: str | object = _MISSING,
    progress_current: int | object = _MISSING,
    progress_total: int | object = _MISSING,
    progress_percent: int | object = _MISSING,
    project_id: str | None | object = _MISSING,
    result_project_id: str | None | object = _MISSING,
    total_rows: int | None | object = _MISSING,
    error: str | None | object = _MISSING,
    finished_at: float | None | object = _MISSING,
    visible_generation: str | None | object = _MISSING,
    target_generation: str | None | object = _MISSING,
    reproduction_status: str | None | object = _MISSING,
) -> bool:
    updated = False
    with _JOB_LOCK:
        job = _ASYNC_JOBS.get(job_id)
        if job is None:
            return False
        if status is not _MISSING:
            assert isinstance(status, str)
            job["status"] = status
        if phase_id is not _MISSING:
            assert isinstance(phase_id, str)
            job["phase_id"] = phase_id
        if phase_index is not _MISSING:
            assert isinstance(phase_index, int)
            job["phase_index"] = phase_index
        if phase_count is not _MISSING:
            assert isinstance(phase_count, int)
            job["phase_count"] = phase_count
        if progress_mode is not _MISSING:
            assert isinstance(progress_mode, str)
            job["progress_mode"] = progress_mode
        if progress_current is not _MISSING:
            assert isinstance(progress_current, int)
            job["progress_current"] = progress_current
        if progress_total is not _MISSING:
            assert isinstance(progress_total, int)
            job["progress_total"] = progress_total
        if progress_percent is not _MISSING:
            assert isinstance(progress_percent, int)
            job["progress_percent"] = progress_percent
        if project_id is not _MISSING:
            assert project_id is None or isinstance(project_id, str)
            job["project_id"] = project_id
        if result_project_id is not _MISSING:
            assert result_project_id is None or isinstance(result_project_id, str)
            job["result_project_id"] = result_project_id
        if total_rows is not _MISSING:
            assert total_rows is None or isinstance(total_rows, int)
            job["total_rows"] = total_rows
        if error is not _MISSING:
            assert error is None or isinstance(error, str)
            job["error"] = error
        if finished_at is not _MISSING:
            assert finished_at is None or isinstance(finished_at, float)
            job["finished_at"] = finished_at
        if visible_generation is not _MISSING:
            assert visible_generation is None or isinstance(visible_generation, str)
            job["visible_generation"] = visible_generation
        if target_generation is not _MISSING:
            assert target_generation is None or isinstance(target_generation, str)
            job["target_generation"] = target_generation
        if reproduction_status is not _MISSING:
            assert reproduction_status is None or isinstance(reproduction_status, str)
            job["reproduction_status"] = reproduction_status
        updated = True
    if updated:
        _publish_job_event(job_id)
    return True


def _set_job_phase(
    job_id: str, *, phase_id: str, phase_index: int, phase_count: int
) -> bool:
    progress_current, progress_total, progress_percent = _phase_progress(
        phase_index, phase_count
    )
    return _set_job_state(
        job_id,
        phase_id=phase_id,
        phase_index=phase_index,
        phase_count=phase_count,
        progress_mode="determinate",
        progress_current=progress_current,
        progress_total=progress_total,
        progress_percent=progress_percent,
    )


def _project_create_phase_count(filename: str) -> int:
    return (
        _PROJECT_CREATE_DISK_PHASE_COUNT
        if Path(filename).suffix.lower() == ".adf"
        else _PROJECT_CREATE_EXECUTABLE_PHASE_COUNT
    )


def _file_cache_stamp(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError:
        return f"{path}:missing"
    return f"{path}:{stat.st_size}:{stat.st_mtime_ns}"


def _project_listing_cache_key(project_name: str) -> str:
    try:
        paths = resolve_project_paths(project_name, project_root=PROJECT_ROOT, require_entities=False)
    except (FileNotFoundError, ValueError):
        return f"{project_name}|unresolved"
    source = paths.binary_source
    parts = [project_name, source.kind, source.display_path]
    source_path = getattr(source, "path", None)
    if isinstance(source_path, Path):
        parts.append(_file_cache_stamp(source_path))
    adf_path = getattr(source, "adf_path", None)
    if isinstance(adf_path, Path):
        parts.append(_file_cache_stamp(adf_path))
        parts.append(str(getattr(source, "entry_path", "")))
    for attr in ("address_model", "load_address", "entrypoint", "code_start_offset"):
        if hasattr(source, attr):
            parts.append(f"{attr}={getattr(source, attr)}")
    parts.append(_file_cache_stamp(paths.target_dir / "source_binary.json"))
    parts.append(
        "source_renderer_tool_stamps="
        + json.dumps(source_renderer_tool_stamps(PROJECT_ROOT), sort_keys=True)
    )
    try:
        parts.append(f"effective_metadata={effective_metadata_hash(paths.target_dir)}")
    except ValueError as exc:
        parts.append(f"effective_metadata_error={exc}")
    return "|".join(parts)


def _cache_satisfies_full_generation(project_name: str, cache_key: str) -> bool:
    if project_name not in _PROJECT_ROW_CACHE_KEY:
        return (
            project_name in _PROJECT_C_LISTING_ARTIFACT_CACHE
            and _PROJECT_ROW_GENERATION_CACHE.get(project_name) == "full"
        )
    if _PROJECT_ROW_CACHE_KEY.get(project_name) != cache_key:
        return False
    cached_generation = _PROJECT_ROW_GENERATION_CACHE.get(project_name)
    return cached_generation == "full" and project_name in _PROJECT_C_LISTING_ARTIFACT_CACHE


def _build_rows_job(job_id: str, project_name: str) -> None:
    phase_count = _LISTING_PHASE_COUNT
    rows: list[ListingRow] = []
    total_rows = 0
    listing_artifact: CListingArtifact | None = None
    try:
        cache_key = _project_listing_cache_key(project_name)
        _log_event("listing_job start", job_id=job_id, project=project_name, generation="full")
        if not _set_job_state(job_id, status="building"):
            return
        if not _set_job_phase(job_id, phase_id="build_c_rows", phase_index=1, phase_count=phase_count):
            return
        _log_event(
            "listing_job phase",
            job_id=job_id,
            project=project_name,
            generation="full",
            phase="build_c_rows",
        )
        total_rows, api_calls, profile, listing_artifact = build_project_listing_artifact_generation_profile(
            project_name,
            generation="full",
        )
        app_slot_analysis = profile.get("app_slot_analysis")
        type_flow_analysis = profile.get("type_flow_analysis")
        if not _set_job_phase(job_id, phase_id="emit_rows", phase_index=2, phase_count=phase_count):
            if listing_artifact is not None:
                listing_artifact.close()
            return
        if _project_listing_cache_key(project_name) != cache_key:
            if listing_artifact is not None:
                listing_artifact.close()
            _set_job_state(
                job_id,
                status="failed",
                phase_id="stale",
                error="project changed while listing job was building",
                finished_at=time.time(),
            )
            return
        with _JOB_LOCK:
            if job_id not in _ASYNC_JOBS:
                return
            job_cache_key = _ASYNC_JOBS[job_id].get("cache_key")
            if job_cache_key is not None and job_cache_key != cache_key:
                if listing_artifact is not None:
                    listing_artifact.close()
                return
            _PROJECT_ROW_GENERATION_CACHE[project_name] = "full"
            _PROJECT_LISTING_TOTAL_ROWS_CACHE[project_name] = total_rows
            _PROJECT_ROW_CACHE_KEY[project_name] = cache_key
            old_artifact = _PROJECT_C_LISTING_ARTIFACT_CACHE.get(project_name)
            if listing_artifact is not None:
                _PROJECT_C_LISTING_ARTIFACT_CACHE[project_name] = listing_artifact
                listing_artifact = None
            if old_artifact is not None and old_artifact is not _PROJECT_C_LISTING_ARTIFACT_CACHE.get(project_name):
                old_artifact.close()
            _PROJECT_ROW_CACHE.pop(project_name, None)
            _PROJECT_API_CALL_CACHE[project_name] = api_calls
            if isinstance(app_slot_analysis, dict):
                _PROJECT_APP_SLOT_ANALYSIS_CACHE[project_name] = app_slot_analysis
            else:
                _PROJECT_APP_SLOT_ANALYSIS_CACHE.pop(project_name, None)
            if isinstance(type_flow_analysis, dict):
                _PROJECT_TYPE_FLOW_ANALYSIS_CACHE[project_name] = type_flow_analysis
            else:
                _PROJECT_TYPE_FLOW_ANALYSIS_CACHE.pop(project_name, None)
        _log_event(
            "listing_job generation_ready",
            job_id=job_id,
            project=project_name,
            generation="full",
            total_rows=total_rows,
        )
        _publish_listing_generation_ready_event(job_id, project_name, "full", total_rows, rows)
        if not _set_job_state(
            job_id,
            total_rows=total_rows,
            visible_generation="full",
            target_generation="full",
        ):
            if listing_artifact is not None:
                listing_artifact.close()
            return
        _log_event(
            "listing_job done",
            job_id=job_id,
            project=project_name,
            generation="full",
            total_rows=total_rows,
        )
        _set_job_state(
            job_id,
            status="ready",
            phase_id="done",
            phase_index=phase_count,
            phase_count=phase_count,
            progress_mode="determinate",
            progress_current=phase_count,
            progress_total=phase_count,
            progress_percent=100,
            total_rows=total_rows,
            visible_generation=_PROJECT_ROW_GENERATION_CACHE.get(project_name),
            target_generation="full",
            finished_at=time.time(),
        )
        _start_reproduction_job_if_needed(project_name)
    except Exception as exc:  # pragma: no cover
        if listing_artifact is not None:
            listing_artifact.close()
        _log_event(
            "listing_job failed", job_id=job_id, project=project_name, error=str(exc)
        )
        _set_job_state(
            job_id,
            status="failed",
            phase_id="error",
            error=str(exc),
            finished_at=time.time(),
        )


def _start_listing_job(project_name: str) -> AsyncJobPayload:
    cache_key = _project_listing_cache_key(project_name)
    if _cache_satisfies_full_generation(project_name, cache_key):
        total_rows = _PROJECT_LISTING_TOTAL_ROWS_CACHE.get(project_name)
        job_id = f"cached-full-{project_name}"
        payload: AsyncJobPayload = {
            "job_id": job_id,
            "job_kind": "full_listing",
            "project_id": project_name,
            "result_project_id": project_name,
            "status": "ready",
            "phase_id": "done",
            "phase_index": _LISTING_PHASE_COUNT,
            "phase_count": _LISTING_PHASE_COUNT,
            "progress_mode": "determinate",
            "progress_current": _LISTING_PHASE_COUNT,
            "progress_total": _LISTING_PHASE_COUNT,
            "progress_percent": 100,
            "total_rows": total_rows,
            "error": None,
            "created_at": time.time(),
            "finished_at": time.time(),
            "visible_generation": _PROJECT_ROW_GENERATION_CACHE.get(project_name) or "full",
            "target_generation": "full",
            "cache_key": cache_key,
        }
        with _JOB_LOCK:
            _ASYNC_JOBS[job_id] = payload
        _start_reproduction_job_if_needed(project_name)
        return payload

    with _JOB_LOCK:
        for _existing_id, job in _ASYNC_JOBS.items():
            if (
                job["job_kind"] == "full_listing"
                and job["project_id"] == project_name
                and job.get("cache_key") == cache_key
                and job["status"] in {"queued", "building"}
            ):
                return cast(AsyncJobPayload, dict(job))
        job_id = str(uuid.uuid4())
        _ASYNC_JOBS[job_id] = {
            "job_id": job_id,
            "job_kind": "full_listing",
            "project_id": project_name,
            "result_project_id": project_name,
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": _LISTING_PHASE_COUNT,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": _LISTING_PHASE_COUNT,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": time.time(),
            "finished_at": None,
            "visible_generation": _PROJECT_ROW_GENERATION_CACHE.get(project_name),
            "target_generation": "full",
            "cache_key": cache_key,
        }

    worker = threading.Thread(
        target=_build_rows_job,
        args=(job_id, project_name),
        daemon=True,
    )
    worker.start()
    return _job_payload(job_id)


def _reproduction_cache_key(project_name: str) -> str:
    try:
        stamp = reproduction_input_stamp(project_name, project_root=PROJECT_ROOT)
    except Exception as exc:
        return f"{project_name}|reproduction-unresolved|{exc}"
    return json.dumps(stamp, sort_keys=True)


def _build_reproduction_job(job_id: str, project_name: str) -> None:
    phase_count = _REPRODUCTION_PHASE_COUNT
    try:
        cache_key = _reproduction_cache_key(project_name)
        _log_event("reproduction_job start", job_id=job_id, project=project_name)
        if not _set_job_state(job_id, status="building"):
            return
        if not _set_job_phase(job_id, phase_id="prepare", phase_index=1, phase_count=phase_count):
            return
        rows = _cached_project_rows(project_name)
        if _PROJECT_ROW_GENERATION_CACHE.get(project_name) != "full":
            rows = None
        if not _set_job_phase(job_id, phase_id="assemble", phase_index=2, phase_count=phase_count):
            return
        report = run_reproduction(project_name, rows=rows, project_root=PROJECT_ROOT)
        if not _set_job_phase(job_id, phase_id="diff", phase_index=3, phase_count=phase_count):
            return
        if _reproduction_cache_key(project_name) != cache_key:
            _set_job_state(
                job_id,
                status="failed",
                phase_id="stale",
                error="project changed while reproduction job was running",
                finished_at=time.time(),
            )
            return
        _set_job_state(
            job_id,
            status="ready",
            phase_id="done",
            phase_index=phase_count,
            phase_count=phase_count,
            progress_mode="determinate",
            progress_current=phase_count,
            progress_total=phase_count,
            progress_percent=100,
            finished_at=time.time(),
            reproduction_status=str(report.get("status") or ""),
        )
        _log_event(
            "reproduction_job done",
            job_id=job_id,
            project=project_name,
            status=report.get("status"),
        )
    except Exception as exc:  # pragma: no cover
        _log_event("reproduction_job failed", job_id=job_id, project=project_name, error=str(exc))
        _set_job_state(
            job_id,
            status="failed",
            phase_id="error",
            error=str(exc),
            finished_at=time.time(),
        )


def _start_reproduction_job(project_name: str, *, force: bool = True) -> AsyncJobPayload:
    cache_key = _reproduction_cache_key(project_name)
    if not force:
        try:
            report = load_reproduction_report(project_name, project_root=PROJECT_ROOT)
        except Exception:
            report = {"status": "not_ready", "stale": True}
        if report.get("status") != "not_ready" and report.get("stale") is False:
            job_id = f"cached-reproduction-{project_name}"
            payload: AsyncJobPayload = {
                "job_id": job_id,
                "job_kind": "reproduction",
                "project_id": project_name,
                "result_project_id": project_name,
                "status": "ready",
                "phase_id": "done",
                "phase_index": _REPRODUCTION_PHASE_COUNT,
                "phase_count": _REPRODUCTION_PHASE_COUNT,
                "progress_mode": "determinate",
                "progress_current": _REPRODUCTION_PHASE_COUNT,
                "progress_total": _REPRODUCTION_PHASE_COUNT,
                "progress_percent": 100,
                "total_rows": None,
                "error": None,
                "created_at": time.time(),
                "finished_at": time.time(),
                "cache_key": cache_key,
                "reproduction_status": str(report.get("status") or ""),
            }
            with _JOB_LOCK:
                _ASYNC_JOBS[job_id] = payload
            return payload
    with _JOB_LOCK:
        for _existing_id, job in _ASYNC_JOBS.items():
            if (
                job["job_kind"] == "reproduction"
                and job["project_id"] == project_name
                and job.get("cache_key") == cache_key
                and job["status"] in {"queued", "building"}
            ):
                return cast(AsyncJobPayload, dict(job))
        job_id = str(uuid.uuid4())
        _ASYNC_JOBS[job_id] = {
            "job_id": job_id,
            "job_kind": "reproduction",
            "project_id": project_name,
            "result_project_id": project_name,
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": _REPRODUCTION_PHASE_COUNT,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": _REPRODUCTION_PHASE_COUNT,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": time.time(),
            "finished_at": None,
            "cache_key": cache_key,
            "reproduction_status": None,
        }
    worker = threading.Thread(
        target=_build_reproduction_job,
        args=(job_id, project_name),
        daemon=True,
    )
    worker.start()
    return _job_payload(job_id)


def _start_reproduction_job_if_needed(project_name: str) -> AsyncJobPayload | None:
    try:
        project = get_project(project_name)
    except FileNotFoundError:
        return None
    if project.kind != "binary" or not project.ready:
        return None
    if "reproduction-unresolved" in _reproduction_cache_key(project_name):
        return None
    return _start_reproduction_job(project_name, force=False)


def _cancel_reproduction_jobs(project_name: str | None = None) -> None:
    canceled: list[tuple[str, AsyncJobPayload]] = []
    with _JOB_LOCK:
        stale_job_ids = [
            job_id
            for job_id, job in _ASYNC_JOBS.items()
            if job["job_kind"] == "reproduction"
            and (project_name is None or job["project_id"] == project_name)
        ]
        for job_id in stale_job_ids:
            job = dict(_ASYNC_JOBS[job_id])
            job["status"] = "failed"
            job["phase_id"] = "error"
            job["error"] = "job canceled"
            job["finished_at"] = time.time()
            canceled.append((job_id, cast(AsyncJobPayload, job)))
            del _ASYNC_JOBS[job_id]
    for job_id, payload in canceled:
        _publish_job_event_payload(job_id, payload)


def _build_project_create_job(job_id: str, body: dict[str, object]) -> None:
    try:
        project = _create_project_from_media(body, job_id=job_id)
        phase_count = _job_payload(job_id)["phase_count"]
        _set_job_state(
            job_id,
            status="ready",
            result_project_id=project.id,
            phase_id="done",
            phase_index=phase_count,
            phase_count=phase_count,
            progress_mode="determinate",
            progress_current=phase_count,
            progress_total=phase_count,
            progress_percent=100,
            finished_at=time.time(),
        )
    except Exception as exc:  # pragma: no cover
        _log_event("project_create failed", job_id=job_id, error=str(exc))
        _set_job_state(
            job_id,
            status="failed",
            phase_id="error",
            error=str(exc),
            finished_at=time.time(),
        )


def _start_project_create_job(body: dict[str, object]) -> AsyncJobPayload:
    filename = body.get("filename")
    if not isinstance(filename, str):
        raise ValueError("Uploaded media filename is missing")
    phase_count = _project_create_phase_count(filename)
    job_id = str(uuid.uuid4())
    with _JOB_LOCK:
        _ASYNC_JOBS[job_id] = {
            "job_id": job_id,
            "job_kind": "project_create",
            "project_id": None,
            "result_project_id": None,
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": phase_count,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": phase_count,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": time.time(),
            "finished_at": None,
        }
    worker = threading.Thread(
        target=_build_project_create_job,
        args=(job_id, dict(body)),
        daemon=True,
    )
    worker.start()
    return _job_payload(job_id)


def _failed_project_create_job(error: str) -> AsyncJobPayload:
    job_id = str(uuid.uuid4())
    now = time.time()
    with _JOB_LOCK:
        _ASYNC_JOBS[job_id] = {
            "job_id": job_id,
            "job_kind": "project_create",
            "project_id": None,
            "result_project_id": None,
            "status": "failed",
            "phase_id": "error",
            "phase_index": 0,
            "phase_count": _PROJECT_CREATE_EXECUTABLE_PHASE_COUNT,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": _PROJECT_CREATE_EXECUTABLE_PHASE_COUNT,
            "progress_percent": 0,
            "total_rows": None,
            "error": error,
            "created_at": now,
            "finished_at": now,
        }
    return _job_payload(job_id)


def _project_payload(project_name: str) -> ProjectPayload:
    project = get_project(project_name)
    payload: ProjectPayload = {"project": project.to_dict()}
    if project.kind == "disk":
        manifest_path = project.manifest_path
        if manifest_path is None:
            raise ValueError(f"Disk project {project_name} is missing manifest_path")
        manifest = DiskManifest.load(Path(manifest_path))
        payload["disk_manifest"] = manifest.to_dict()
    elif project.kind == "binary" and project.ready:
        payload["reproduction"] = _current_reproduction_payload(project_name)
    return payload


def _project_disk_browser_payload(project_name: str, path: str = "") -> dict[str, object]:
    project = get_project(project_name)
    if project.kind != "disk":
        raise ValueError(f"Project {project_name} is not a disk project")
    manifest_path = project.manifest_path
    if manifest_path is None:
        raise ValueError(f"Disk project {project_name} is missing manifest_path")
    manifest = DiskManifest.load(Path(manifest_path))
    manifest_dict = manifest.to_dict()
    return disk_browser.payload_from_project_manifest(
        manifest_dict,
        path,
        content_for_entry=lambda entry: _project_disk_entry_content_payload(manifest_dict, entry),
    )


def _project_disk_entry_content_payload(
    manifest: dict[str, object],
    entry: dict[str, object],
) -> dict[str, object]:
    extracted_path = entry.get("extracted_path")
    try:
        if isinstance(extracted_path, str) and extracted_path:
            path = Path(extracted_path)
            data = path.read_bytes()
        else:
            source_path = manifest.get("source_path")
            entry_path = entry.get("full_path") or entry.get("path")
            if not isinstance(source_path, str) or not isinstance(entry_path, str):
                raise RuntimeError("Disk file entry is missing source path metadata")
            data = extract_disk_entry_with_c_backend(
                Path(source_path),
                entry_path,
                project_root=PROJECT_ROOT,
            )
    except Exception as exc:
        return disk_browser.content_error_payload(str(exc), disk_browser.entry_size(cast(dict[str, object], entry)))
    return disk_browser.content_payload_from_bytes(data)


def resolve_static_response(path: str) -> StaticResponse:
    relative = "index.html" if path in ("", "/") else path.lstrip("/")
    direct_file_path = (WEB_ROOT / relative).resolve()
    if (
        "/" not in relative
        and direct_file_path != WEB_ROOT.resolve()
        and not direct_file_path.exists()
    ):
        relative = "index.html"
    file_path = (WEB_ROOT / relative).resolve()
    if WEB_ROOT.resolve() not in file_path.parents and file_path != WEB_ROOT.resolve():
        raise FileNotFoundError(f"Unknown route: {path}")
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Unknown route: {path}")

    content_type = "text/plain; charset=utf-8"
    if file_path.suffix == ".html":
        content_type = "text/html; charset=utf-8"
    elif file_path.suffix == ".js":
        content_type = "application/javascript; charset=utf-8"
    elif file_path.suffix == ".css":
        content_type = "text/css; charset=utf-8"
    headers = {"Cache-Control": "no-store"}
    return {
        "content_type": content_type,
        "body": file_path.read_bytes(),
        "headers": headers,
    }


class DisasmApiHandler(BaseHTTPRequestHandler):
    server_version = "DisasmApi/0.1"

    def _handle_request(
        self,
        method: str,
        handler: Callable[[], tuple[bytes, str, int, dict[str, str] | None]],
    ) -> None:
        started = time.time()
        status = 200
        content_type = "application/json; charset=utf-8"
        extra_headers: dict[str, str] | None = None
        try:
            body, content_type, status, extra_headers = handler()
        except FileNotFoundError as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            status = 404
        except (FileExistsError, ValueError) as exc:
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            status = 400
        except Exception as exc:  # pragma: no cover
            body = _json_bytes({"ok": False, "error": str(exc)})
            content_type = "application/json; charset=utf-8"
            status = 500
        elapsed_ms = int((time.time() - started) * 1000)
        _log_event(
            "request",
            method=method,
            path=self.path,
            status=status,
            elapsed_ms=elapsed_ms,
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if extra_headers is not None:
            for name, value in extra_headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _write_sse_event(self, event_name: str, payload: dict[str, object]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.wfile.write(f"event: {event_name}\n".encode("ascii"))
        self.wfile.write(b"data: " + data + b"\n\n")
        self.wfile.flush()

    def _write_sse_job_event(self, payload: AsyncJobPayload) -> None:
        self._write_sse_event("job", cast(dict[str, object], payload))

    def _handle_job_events(self, query: dict[str, list[str]]) -> None:
        job_values = query.get("job_id")
        job_id = job_values[0] if job_values else None
        if not job_id:
            raise ValueError("Missing job_id")
        initial_payload = _job_payload_or_none(job_id)
        if initial_payload is None:
            raise FileNotFoundError(f"Unknown job: {job_id}")

        subscriber: queue.Queue[dict[str, object]] = queue.Queue()
        with _JOB_LOCK:
            _JOB_EVENT_SUBSCRIBERS.setdefault(job_id, []).append(subscriber)

        started = time.time()
        status = 200
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self._write_sse_job_event(initial_payload)
            if initial_payload["status"] not in {"queued", "building"}:
                return
            while True:
                try:
                    payload = subscriber.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    continue
                event_name = cast(str, payload.get("_event_type", "job"))
                payload = dict(payload)
                payload.pop("_event_type", None)
                self._write_sse_event(event_name, payload)
                if event_name == "job" and payload["status"] not in {"queued", "building"}:
                    return
        except (BrokenPipeError, ConnectionResetError, OSError):
            status = 499
        finally:
            with _JOB_LOCK:
                subscribers = _JOB_EVENT_SUBSCRIBERS.get(job_id)
                if subscribers is not None:
                    try:
                        subscribers.remove(subscriber)
                    except ValueError:
                        pass
                    if not subscribers:
                        del _JOB_EVENT_SUBSCRIBERS[job_id]
            elapsed_ms = int((time.time() - started) * 1000)
            _log_event(
                "request",
                method="GET",
                path=self.path,
                status=status,
                elapsed_ms=elapsed_ms,
            )

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/jobs/events":
            try:
                self._handle_job_events(parse_qs(parsed.query))
            except FileNotFoundError as exc:
                self.send_error(404, str(exc))
            except ValueError as exc:
                self.send_error(400, str(exc))
            return

        def handler() -> tuple[bytes, str, int, dict[str, str] | None]:
            if parsed.path == "/" or not parsed.path.startswith("/api/"):
                response = resolve_static_response(parsed.path)
                return (
                    response["body"],
                    response["content_type"],
                    200,
                    response["headers"],
                )
            payload = route_request("GET", parsed.path, parse_qs(parsed.query))
            return _json_bytes(payload), "application/json; charset=utf-8", 200, None

        self._handle_request("GET", handler)

    def do_PATCH(self) -> None:
        def handler() -> tuple[bytes, str, int, dict[str, str] | None]:
            parsed = urlparse(self.path)
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            assert isinstance(payload, dict), "PATCH body must be a JSON object"
            body = _json_bytes(
                route_request(
                    "PATCH",
                    parsed.path,
                    parse_qs(parsed.query),
                    cast(dict[str, object], payload),
                )
            )
            return body, "application/json; charset=utf-8", 200, None

        self._handle_request("PATCH", handler)

    def do_POST(self) -> None:
        def handler() -> tuple[bytes, str, int, dict[str, str] | None]:
            parsed = urlparse(self.path)
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            assert isinstance(payload, dict), "POST body must be a JSON object"
            body = _json_bytes(
                route_request(
                    "POST",
                    parsed.path,
                    parse_qs(parsed.query),
                    cast(dict[str, object], payload),
                )
            )
            return body, "application/json; charset=utf-8", 200, None

        self._handle_request("POST", handler)

    def log_message(self, format: str, *args: object) -> None:
        _log_event("http", detail=format % args)


def route_request(
    method: str,
    path: str,
    query: dict[str, list[str]],
    body: dict[str, object] | None = None,
) -> ApiResponse:
    if method == "GET" and path == "/api/projects":
        return {"ok": True, "data": [project.to_dict() for project in list_projects()]}
    if method == "POST" and path == "/api/projects":
        if "media_base64" in (body or {}):
            job = _start_project_create_job(cast(dict[str, object], body or {}))
            return {"ok": True, "data": job}
        project_id = (body or {}).get("id", "")
        if not isinstance(project_id, str):
            raise ValueError("Project id must be a string")
        return {"ok": True, "data": create_project(project_id).to_dict()}
    if method == "GET" and path == "/api/projects/create/status":
        job_values = query.get("job_id")
        job_id = job_values[0] if job_values else None
        if not job_id:
            raise ValueError("Missing job_id")
        return {"ok": True, "data": _job_payload(job_id)}

    parts = [part for part in path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "api" and parts[1] == "corpus":
        if method == "GET" and len(parts) == 3 and parts[2] == "features":
            return {"ok": True, "data": corpus_usage.feature_list()}
        if method == "GET" and len(parts) == 3 and parts[2] == "query":
            feature = _first_query_value(query, "feature")
            group = _first_query_value(query, "group")
            platform = _first_query_value(query, "platform")
            q = _first_query_value(query, "q")
            source_only = _first_query_value(query, "source_only") == "1"
            limit = _parse_int_arg(query, "limit")
            offset = _parse_int_arg(query, "offset", 0) or 0
            return {
                "ok": True,
                "data": corpus_usage.query_targets(
                    feature=feature,
                    group=group,
                    platform=platform,
                    q=q,
                    source_only=source_only,
                    limit=limit,
                    offset=offset,
                    projects=[project.to_dict() for project in list_projects()],
                ),
            }
        if method == "GET" and len(parts) == 3 and parts[2] == "variants":
            target_id = _first_query_value(query, "target_id")
            if not target_id:
                raise ValueError("Missing target_id")
            return {"ok": True, "data": corpus_usage.variants_payload(target_id)}
        if method == "GET" and len(parts) == 3 and parts[2] == "disk":
            target_id = _first_query_value(query, "target_id")
            if not target_id:
                raise ValueError("Missing target_id")
            return {
                "ok": True,
                "data": corpus_usage.disk_browser_payload(
                    target_id,
                    _first_query_value(query, "path") or "",
                    projects=[project.to_dict() for project in list_projects()],
                ),
            }
        if method == "GET" and len(parts) == 3 and parts[2] == "diff":
            left_target_id = _first_query_value(query, "left_target_id")
            right_target_id = _first_query_value(query, "right_target_id")
            if not left_target_id or not right_target_id:
                raise ValueError("Missing left_target_id/right_target_id")
            return {"ok": True, "data": corpus_usage.diff_payload(left_target_id, right_target_id)}
        if method == "GET" and len(parts) == 3 and parts[2] == "xrefs":
            target_id = _first_query_value(query, "target_id")
            feature = _first_query_value(query, "feature")
            group = _first_query_value(query, "group")
            source_only = _first_query_value(query, "source_only") == "1"
            limit = _parse_int_arg(query, "limit")
            offset = _parse_int_arg(query, "offset", 0) or 0
            return {
                "ok": True,
                "data": corpus_usage.query_xrefs(
                    target_id=target_id,
                    feature=feature,
                    group=group,
                    source_only=source_only,
                    limit=limit,
                    offset=offset,
                ),
            }
        if method == "GET" and len(parts) == 3 and parts[2] == "snippet":
            xref_id = _first_query_value(query, "xref_id")
            if not xref_id:
                raise ValueError("Missing xref_id")
            before = _parse_int_arg(query, "before", 20)
            after = _parse_int_arg(query, "after", 20)
            return {
                "ok": True,
                "data": corpus_usage.snippet_payload(
                    xref_id,
                    before=20 if before is None else before,
                    after=20 if after is None else after,
                ),
            }
        if method == "POST" and len(parts) == 3 and parts[2] == "import":
            target_id = (body or {}).get("target_id")
            if not isinstance(target_id, str) or not target_id:
                raise ValueError("target_id is required")
            mode = (body or {}).get("mode", "target")
            if not isinstance(mode, str):
                raise ValueError("mode must be a string")
            try:
                job = _start_project_create_job(
                    corpus_usage.corpus_import_media_body(target_id, mode=mode)
                )
            except Exception as exc:
                job = _failed_project_create_job(str(exc))
            return {"ok": True, "data": job}
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "projects":
        project_name = parts[2]
        if method == "GET" and len(parts) == 3:
            return {"ok": True, "data": _project_payload(project_name)}
        if method == "GET" and len(parts) == 4 and parts[3] == "disk-browser":
            return {"ok": True, "data": _project_disk_browser_payload(project_name, _first_query_value(query, "path") or "")}
        if method == "POST" and len(parts) == 4 and parts[3] == "delete":
            _cancel_listing_jobs(project_name)
            _cancel_reproduction_jobs(project_name)
            _clear_project_listing_cache(project_name)
            delete_project(project_name)
            return {"ok": True, "data": None}
        if method == "POST" and len(parts) == 4 and parts[3] == "open":
            return {"ok": True, "data": mark_project_opened(project_name).to_dict()}
        if method == "GET" and len(parts) == 4 and parts[3] == "session":
            return {"ok": True, "data": None}
        if (
            method == "GET"
            and len(parts) == 5
            and parts[3] == "api"
            and parts[4] == "type-catalog"
        ):
            return {"ok": True, "data": _type_catalog_payload(project_name)}
        if method == "GET" and len(parts) == 4 and parts[3] == "reproduction":
            project = get_project(project_name)
            if project.kind != "binary":
                raise ValueError(
                    f"Project {project_name} does not expose target reproduction"
                )
            if not project.ready:
                return {
                    "ok": True,
                    "data": _not_ready_reproduction_payload(project_name),
                }
            return {
                "ok": True,
                "data": _current_reproduction_payload(
                    project_name,
                    auto_start=_PROJECT_ROW_GENERATION_CACHE.get(project_name) == "full",
                ),
            }
        if (
            method == "POST"
            and len(parts) == 5
            and parts[3] == "reproduction"
            and parts[4] == "run"
        ):
            project = get_project(project_name)
            if project.kind != "binary" or not project.ready:
                raise ValueError(
                    f"Project {project_name} is not ready for target reproduction"
                )
            return {"ok": True, "data": _start_reproduction_job(project_name, force=True)}
        if (
            method == "GET"
            and len(parts) == 5
            and parts[3] == "reproduction"
            and parts[4] == "status"
        ):
            job_values = query.get("job_id")
            job_id = job_values[0] if job_values else None
            if not job_id:
                raise ValueError("Missing job_id")
            return {"ok": True, "data": _job_payload(job_id)}
        if method == "POST" and len(parts) == 4 and parts[3] == "target-edits":
            project = get_project(project_name)
            if project.kind != "binary" or not project.ready:
                raise ValueError(
                    f"Project {project_name} is not ready for target metadata edits"
                )
            paths = resolve_project_paths(project_name, project_root=PROJECT_ROOT, require_entities=False)
            edit = append_target_ui_edit(paths.target_dir, cast(dict[str, object], body or {}))
            _cancel_listing_jobs(project_name)
            _cancel_reproduction_jobs(project_name)
            _clear_project_listing_cache(project_name)
            mark_project_updated(paths.target_dir)
            return {"ok": True, "data": {"edit": edit}}
        if method == "GET" and len(parts) == 4 and parts[3] == "listing":
            project = get_project(project_name)
            if project.kind != "binary":
                raise ValueError(
                    f"Project {project_name} does not expose a disassembly listing"
                )
            if not project.ready:
                return {"ok": True, "data": _empty_listing_payload(None)}
            listing_artifact = _valid_c_listing_artifact(project_name)
            rows = _cached_project_rows(project_name)
            if rows is None and listing_artifact is None:
                raise ValueError(
                    f"Canonical rows not loaded for project: {project_name}"
                )
            start = _parse_int_arg(query, "start")
            count = _parse_int_arg(query, "count")
            anchor_code_values = query.get("anchor_code")
            anchor_code = anchor_code_values[0].strip() if anchor_code_values else ""
            if anchor_code:
                if listing_artifact is not None:
                    payload, _ = listing_artifact.anchor_window_payload(
                        anchor_code=anchor_code,
                        count=count or 240,
                    )
                elif rows is None:
                    raise ValueError(
                        f"Canonical rows not loaded for project: {project_name}"
                    )
                else:
                    payload = listing_index_window_payload(
                        rows,
                        _listing_anchor_code_start(rows, anchor_code),
                        count or 240,
                    )
            elif start is not None or count is not None:
                if listing_artifact is not None:
                    payload, _ = listing_artifact.window_payload(start=start or 0, count=count or 240)
                else:
                    assert rows is not None
                    payload = listing_index_window_payload(rows, start or 0, count or 240)
            else:
                addr = _parse_int_arg(query, "addr")
                before = _parse_int_arg(query, "before", 80) or 80
                after = _parse_int_arg(query, "after", 200) or 200
                if listing_artifact is not None:
                    payload, _ = listing_artifact.addr_window_payload(addr=addr, before=before, after=after)
                else:
                    assert rows is not None
                    payload = listing_window_payload(rows, addr, before, after)
            payload = cast(
                ListingWindowPayload,
                {
                    **payload,
                    "analysis_generation": _PROJECT_ROW_GENERATION_CACHE.get(project_name),
                },
            )
            return {
                "ok": True,
                "data": _annotate_listing_payload(project_name, payload),
            }
        if (
            method == "GET"
            and len(parts) == 5
            and parts[3] == "listing"
            and parts[4] == "navigation"
        ):
            project = get_project(project_name)
            if project.kind != "binary":
                raise ValueError(
                    f"Project {project_name} does not expose a disassembly listing"
                )
            listing_artifact = _valid_c_listing_artifact(project_name)
            rows = _cached_project_rows(project_name)
            if rows is None and listing_artifact is None:
                raise ValueError(
                    f"Canonical rows not loaded for project: {project_name}"
                )
            if listing_artifact is not None:
                navigation_payload, _ = listing_artifact.navigation_payload()
                return {
                    "ok": True,
                    "data": _overlay_listing_navigation_payload(project_name, navigation_payload, rows),
                }
            assert rows is not None
            return {"ok": True, "data": _listing_navigation_payload(project_name, rows)}
        if (
            method == "POST"
            and len(parts) == 5
            and parts[3] == "listing"
            and parts[4] == "open"
        ):
            project = get_project(project_name)
            if project.kind != "binary":
                raise ValueError(
                    f"Project {project_name} does not expose a disassembly listing"
                )
            if not project.ready:
                return {
                    "ok": True,
                    "data": cast(
                        AsyncJobPayload,
                        {
                            "job_id": f"cached-empty-{project_name}",
                            "job_kind": "full_listing",
                            "project_id": project_name,
                            "result_project_id": project_name,
                            "status": "ready",
                            "phase_id": "done",
                            "phase_index": _LISTING_PHASE_COUNT,
                            "phase_count": _LISTING_PHASE_COUNT,
                            "progress_mode": "determinate",
                            "progress_current": _LISTING_PHASE_COUNT,
                            "progress_total": _LISTING_PHASE_COUNT,
                            "progress_percent": 100,
                            "total_rows": 0,
                            "error": None,
                            "created_at": time.time(),
                            "finished_at": time.time(),
                        },
                    ),
                }
            return {"ok": True, "data": _start_listing_job(project_name)}
        if (
            method == "GET"
            and len(parts) == 5
            and parts[3] == "listing"
            and parts[4] == "status"
        ):
            job_values = query.get("job_id")
            job_id = job_values[0] if job_values else None
            if not job_id:
                raise ValueError("Missing job_id")
            return {"ok": True, "data": _job_payload(job_id)}
        if method == "GET" and len(parts) == 5 and parts[3] == "entities":
            return {"ok": True, "data": get_entity(project_name, parts[4], project_root=PROJECT_ROOT)}
        if method == "PATCH" and len(parts) == 5 and parts[3] == "entities":
            return {
                "ok": True,
                "data": patch_entity(
                    project_name,
                    parts[4],
                    cast(AnnotationPatchInput, body or {}),
                    project_root=PROJECT_ROOT,
                ),
            }
        if (
            method == "PATCH"
            and len(parts) == 10
            and parts[3] == "api"
            and parts[4] == "functions"
            and parts[7] == "inputs"
            and parts[9] == "struct"
        ):
            library = parts[5]
            function = parts[6]
            input_name = parts[8]
            struct_name = (body or {}).get("struct_name")
            if not isinstance(struct_name, str) or not struct_name:
                raise ValueError("struct_name must be a non-empty string")
            validation = _validate_api_input_struct(
                project_name, library, function, input_name, struct_name
            )
            _write_api_input_type_override(
                library=library,
                function=function,
                input_name=input_name,
                struct_name=struct_name,
            )
            return {"ok": True, "data": validation}
    raise FileNotFoundError(f"Unknown route: {path}")


def _dedupe_upload_path(uploads_dir: Path, filename: str) -> Path:
    candidate = uploads_dir / Path(filename).name
    stem = candidate.stem
    suffix = candidate.suffix
    index = 2
    while candidate.exists():
        candidate = uploads_dir / f"{stem}-{index}{suffix}"
        index += 1
    return candidate


def _create_project_from_media(
    body: dict[str, object], *, job_id: str | None = None
) -> ProjectRecord:
    def report(phase_id: str, phase_index: int, phase_count: int) -> None:
        if job_id is None:
            return
        _set_job_state(job_id, status="building")
        _set_job_phase(
            job_id, phase_id=phase_id, phase_index=phase_index, phase_count=phase_count
        )

    filename = body.get("filename")
    media_base64 = body.get("media_base64")
    if not isinstance(filename, str):
        raise ValueError("Uploaded media filename is missing")
    if not isinstance(media_base64, str):
        raise ValueError("Uploaded media payload is missing")
    uploaded_bytes = base64.b64decode(media_base64, validate=True)
    origin_payload = body.get("project_origin")
    if origin_payload is not None and not isinstance(origin_payload, dict):
        raise ValueError("project_origin must be an object")
    media_platform = "amiga-disk" if Path(filename).suffix.lower() == ".adf" else "amiga-hunk"
    project_origin = (
        {"kind": "user_upload", "filename": filename}
        if origin_payload is None
        else dict(cast(dict[str, object], origin_payload))
    )
    project_origin.setdefault("filename", filename)
    project_origin.setdefault("platform", media_platform)
    project_origin.setdefault("sha256", hashlib.sha256(uploaded_bytes).hexdigest())
    project_origin.setdefault("size", len(uploaded_bytes))
    uploads_dir = PROJECT_ROOT / "bin" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    report("write_media", 1, 4)
    media_path = _dedupe_upload_path(uploads_dir, filename)
    media_path.write_bytes(uploaded_bytes)
    if media_path.suffix.lower() == ".adf":
        base_name = dedupe_project_name(
            disk_project_id(derive_disk_id_from_stem(Path(filename).stem)),
            project_root=PROJECT_ROOT,
        )
        disk_id = base_name.removeprefix("amiga_disk_")
    else:
        base_name = dedupe_project_name(
            derive_project_name(filename), project_root=PROJECT_ROOT
        )
        disk_id = None
    _log_event(
        "media_upload saved",
        filename=filename,
        path=media_path.as_posix(),
        project_id=base_name,
    )
    if media_path.suffix.lower() == ".adf":
        if job_id is not None:
            _set_job_state(job_id, project_id=base_name)
        manifest = create_disk_project(
            media_path,
            disk_id=disk_id,
            project_root=PROJECT_ROOT,
            origin=project_origin,
            progress_fn=(
                None
                if job_id is None
                else lambda phase_id, phase_index, phase_count: report(
                    phase_id, phase_index + 1, phase_count + 1
                )
            ),
        )
        _log_event("media_upload imported", project_id=base_name, kind="disk")
        return get_project(disk_project_id(manifest.disk_id), project_root=PROJECT_ROOT)
    report("inspect_executable", 2, 4)
    try:
        validate_amiga_hunk_executable_with_c_backend(media_path, project_root=PROJECT_ROOT)
    except ValueError:
        media_path.unlink(missing_ok=True)
        raise
    report("create_target", 3, 4)
    project = create_project(base_name, project_root=PROJECT_ROOT, origin=project_origin)
    if job_id is not None:
        _set_job_state(job_id, project_id=project.id)
    write_source_descriptor(
        Path(project.target_dir),
        {
            "kind": "hunk_file",
            "path": media_path.relative_to(PROJECT_ROOT).as_posix(),
        },
    )
    mark_project_updated(Path(project.target_dir))
    report("finalize", 4, 4)
    _log_event("media_upload imported", project_id=project.id, kind="executable")
    return get_project(project.id, project_root=PROJECT_ROOT)


def serve(host: str = "127.0.0.1", port: int = 8123) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    httpd = ThreadingHTTPServer((host, port), DisasmApiHandler)
    _log_event("server_start", host=host, port=port)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve canonical disassembly API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8123)
    args = parser.parse_args()
    serve(host=args.host, port=args.port)
