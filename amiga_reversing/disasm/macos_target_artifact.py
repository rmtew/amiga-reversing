"""Committed Classic Mac OS example target artifact rendering."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path

from amiga_reversing.disasm.macos_listing_source import (
    build_macos_project_listing_artifact_profile,
)
from amiga_reversing.disasm.macos_project_origin import MACOS_PROJECT_ORIGIN_KIND
from amiga_reversing.disasm.macos_project_payload import build_macos_project_payload
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import (
    PROJECT_METADATA_SCHEMA_VERSION,
    ProjectKind,
    ProjectMetadata,
    ProjectRecord,
)

MACOS_EXAMPLE_PROJECT_ID = "macos_hfs_mpw_gm"
MACOS_EXAMPLE_SUBTARGET_ID = "macos_file_mpw_tools_asm"
MACOS_EXAMPLE_HFS_PATH = "MPW-GM/MPW/Tools/Asm"
MACOS_EXAMPLE_SOURCE_IMAGE = "resources/platform_macos/MPW-GM.img.bin"
MACOS_EXAMPLE_TIMESTAMP = "2026-05-21T00:00:00+00:00"
MACOS_EXAMPLE_TARGET_RELPATH = Path("targets") / MACOS_EXAMPLE_PROJECT_ID
MACOS_EXAMPLE_SUBTARGET_RELPATH = MACOS_EXAMPLE_TARGET_RELPATH / "targets" / MACOS_EXAMPLE_SUBTARGET_ID
MACOS_EXAMPLE_ASM_RELPATH = MACOS_EXAMPLE_SUBTARGET_RELPATH / "asm.s"
MACOS_EXAMPLE_SOURCE_FILES = ("ext/macos_includes/mpw_gm/Interfaces/AStructMacs/Sample.a",)
MACOS_EXAMPLE_RESOURCE_FILES = ("ext/macos_includes/mpw_gm/Interfaces/AStructMacs/Sample.r",)
MACOS_EXAMPLE_BUILD_FILES = ("ext/macos_includes/mpw_gm/Interfaces/AStructMacs/Sample.make",)


def macos_example_origin() -> dict[str, object]:
    return {
        "kind": MACOS_PROJECT_ORIGIN_KIND,
        "source_image": MACOS_EXAMPLE_SOURCE_IMAGE,
        "source_project": "MPW-GM/MPW/Examples/AExamples/Sample",
        "hfs_path": MACOS_EXAMPLE_HFS_PATH,
        "selected_code_resource_id": 1,
        "source_files": list(MACOS_EXAMPLE_SOURCE_FILES),
        "resource_files": list(MACOS_EXAMPLE_RESOURCE_FILES),
        "build_files": list(MACOS_EXAMPLE_BUILD_FILES),
    }


def macos_example_subtarget_origin() -> dict[str, object]:
    return {
        "kind": "macos_hfs_resource_code_file",
        "parent_project_id": MACOS_EXAMPLE_PROJECT_ID,
        "source_image": MACOS_EXAMPLE_SOURCE_IMAGE,
        "hfs_path": MACOS_EXAMPLE_HFS_PATH,
        "resource_type": "CODE",
        "selected_code_resource_id": 1,
        "selected_code_resource_name": "Main",
        "artifact": "asm.s",
        "renderer": "amiga_reversing.disasm.macos_target_artifact",
    }


def macos_example_project_record(*, project_root: Path = PROJECT_ROOT) -> ProjectRecord:
    target_dir = project_root / MACOS_EXAMPLE_TARGET_RELPATH
    return ProjectRecord(
        id=MACOS_EXAMPLE_PROJECT_ID,
        name=MACOS_EXAMPLE_PROJECT_ID,
        kind=ProjectKind.MACOS,
        target_dir=str(target_dir),
        output_path=None,
        binary_path=MACOS_EXAMPLE_SOURCE_IMAGE,
        ready=True,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=MACOS_EXAMPLE_SOURCE_IMAGE,
        disk_type="HFS",
        parent_project_id=None,
        target_type="macos_hfs_resource_code_file",
        created_at=MACOS_EXAMPLE_TIMESTAMP,
        updated_at=MACOS_EXAMPLE_TIMESTAMP,
        origin=macos_example_origin(),
    )


def render_macos_example_asm(*, project_root: Path = PROJECT_ROOT) -> str:
    project = macos_example_project_record(project_root=project_root)
    payload = build_macos_project_payload(project, project_root=project_root)
    total_rows, _summary_profile, artifact = build_macos_project_listing_artifact_profile(
        project,
        project_root=project_root,
    )
    try:
        selected_code_source, _source_profile = artifact.source_text_with_profile()
    finally:
        artifact.close()

    container = _mapping(payload.get("binary_container_view"))
    finder = _mapping(container.get("finder"))
    forks = _sequence(container.get("forks"))
    resource_fork = _mapping(container.get("resource_fork"))
    code0 = _mapping(container.get("code0"))
    code0_resource = _mapping(code0.get("resource"))
    code0_metadata = _mapping(code0.get("metadata"))
    selected = _mapping(container.get("selected_code_segment"))
    native_source = _mapping(selected.get("native_source")) or _mapping(container.get("native_source"))
    selected_listing = _mapping(selected.get("listing"))
    selected_restored_source = _mapping(selected.get("restored_source"))
    code_resources = [_mapping(item) for item in _sequence(container.get("code_resources"))]
    code_resource_details = [_mapping(item) for item in _sequence(container.get("code_resource_details"))]
    code_segment_map = [_mapping(item) for item in _sequence(container.get("code_segment_map"))]
    executable_placeholders = [_mapping(item) for item in _sequence(container.get("executable_resource_placeholders"))]
    resource_types = [_mapping(item) for item in _sequence(resource_fork.get("types"))]
    non_code_types = [item for item in resource_types if item.get("type") != "CODE"]
    unsupported = sorted(
        {
            *[str(item) for item in _sequence(container.get("unsupported"))],
            "complete Segment Loader behavior",
            "source-to-CODE segment mapping",
            "byte-for-byte MPW Link/Rez roundtrip",
        }
    )
    header_lines: list[str] = [
        "; Classic Mac OS target artifact: MPW Tools Asm",
        "; Renderer: amiga_reversing.disasm.macos_target_artifact",
        "; Source image: resources/platform_macos/MPW-GM.img.bin",
        f"; HFS path: {MACOS_EXAMPLE_HFS_PATH}",
        f"; Finder type: {_text(finder.get('type'))}",
        f"; Finder creator: {_text(finder.get('creator'))}",
        f"; CNID: {_text(finder.get('cnid'))}",
        ";",
        "; This is an illustrative source artifact, not an MPW round-trip contract.",
        "; Durable input comes from the C-backed HFS/resource/CODE summary and shared m68k listing renderer.",
        "",
    ]
    source_sections = _code_source_body_section_lines(
        code_resource_details,
        selected_id=selected.get("id"),
        selected=selected,
        selected_listing=selected_listing,
        selected_restored_source=selected_restored_source,
        native_source=native_source,
        selected_code_source=selected_code_source,
        selected_listing_rows=total_rows,
    )
    report_lines: list[str] = [
        "",
        "; Supporting evidence follows after the source body.",
        "",
        "; File forks",
        *_fork_lines(forks),
        "",
        "; Resource fork",
        f";   resource_count: {_text(resource_fork.get('resource_count'))}",
        f";   type_count: {_text(resource_fork.get('type_count'))}",
        *_resource_type_lines(resource_types),
        "",
        "; CODE 0 jump-table/application metadata",
        _resource_line(code0_resource),
        f";   above_a5_size: {_text(code0_metadata.get('above_a5_size'))}",
        f";   below_a5_size: {_text(code0_metadata.get('below_a5_size'))}",
        f";   jump_table_length: {_text(code0_metadata.get('jump_table_length'))}",
        f";   jump_table_offset_from_a5: {_text(code0_metadata.get('jump_table_offset_from_a5'))}",
        "",
        "; CODE resources",
        *_code_resource_lines(code_resources, selected_id=selected.get("id")),
        "",
        "; CODE resource coverage",
        f";   total_code_resources: {len(code_resources)}",
        *_code_resource_coverage_lines(code_resources, selected_id=selected.get("id")),
        "",
        "; CODE segment/routine map",
        *_code_segment_map_lines(code_segment_map),
        "",
        "; CODE resource detail subviews",
        *_code_resource_detail_lines(code_resource_details),
        "",
        "; Non-CODE resource placeholders",
        *(
            _resource_type_placeholder_lines(non_code_types)
            if non_code_types
            else [";   none reported by the C-backed resource summary"]
        ),
        "; Executable resource placeholders",
        *_executable_resource_placeholder_lines(executable_placeholders),
        "",
        "; Unsupported Mac Segment Loader/runtime areas",
        *[f";   {item}" for item in unsupported],
    ]
    lines = [*header_lines, *source_sections]
    lines.extend(report_lines)
    lines.append("")
    return "\n".join(lines)


def write_macos_example_target(*, project_root: Path = PROJECT_ROOT) -> None:
    container_dir = project_root / MACOS_EXAMPLE_TARGET_RELPATH
    subtarget_dir = project_root / MACOS_EXAMPLE_SUBTARGET_RELPATH
    subtarget_dir.mkdir(parents=True, exist_ok=True)
    _write_metadata(container_dir / ".project.json", macos_example_origin())
    _write_metadata(subtarget_dir / ".project.json", macos_example_subtarget_origin())
    (project_root / MACOS_EXAMPLE_ASM_RELPATH).write_text(
        render_macos_example_asm(project_root=project_root),
        encoding="utf-8",
    )


def _write_metadata(path: Path, origin: Mapping[str, object]) -> None:
    payload = ProjectMetadata(
        schema_version=PROJECT_METADATA_SCHEMA_VERSION,
        created_at=MACOS_EXAMPLE_TIMESTAMP,
        updated_at=MACOS_EXAMPLE_TIMESTAMP,
        origin=dict(origin),
    )
    path.write_text(json.dumps(asdict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fork_lines(forks: Sequence[object]) -> list[str]:
    lines: list[str] = []
    for item in forks:
        fork = _mapping(item)
        lines.append(
            f";   {_text(fork.get('name'))}: role={_text(fork.get('role'))} "
            f"size={_text(fork.get('size'))} sha256={_text(fork.get('sha256'))}"
        )
    return lines


def _resource_type_lines(types: Sequence[Mapping[str, object]]) -> list[str]:
    return [f";   type {_text(item.get('type'))}: count={_text(item.get('count'))}" for item in types]


def _resource_type_placeholder_lines(types: Sequence[Mapping[str, object]]) -> list[str]:
    return [
        f";   type {_text(item.get('type'))}: { _text(item.get('count')) } resource(s), structured placeholder"
        for item in types
    ]


def _code_source_body_section_lines(
    details: Sequence[Mapping[str, object]],
    *,
    selected_id: object,
    selected: Mapping[str, object],
    selected_listing: Mapping[str, object],
    selected_restored_source: Mapping[str, object],
    native_source: Mapping[str, object],
    selected_code_source: str,
    selected_listing_rows: int,
) -> list[str]:
    lines = ["; CODE source body sections"]
    for detail in details:
        resource_id = detail.get("id")
        restored_source = selected_restored_source if resource_id == selected_id else _mapping(detail.get("restored_source"))
        presentation = _mapping(detail.get("source_presentation_status"))
        listing = _mapping(detail.get("listing"))
        section_status = _code_source_section_status(detail, selected_id=selected_id)
        lines.extend(
            [
                "",
                f"; CODE {_text(resource_id)} {_text(detail.get('name'))} source section",
                f";   source_section_id: macos-code-CODE-{_text(resource_id)}",
                f";   source_kind: {_text(native_source.get('source_kind') or 'macos_code_resource')}",
                f";   backend: {_text(native_source.get('backend') or 'macos-code')}",
                f";   status: {section_status}",
                f";   resource_type: {_text(detail.get('resource_type'))}",
                f";   id: {_text(resource_id)}",
                f";   name: {_text(detail.get('name'))}",
                f";   role: {_text(detail.get('role'))}",
                f";   code_kind: {_text(detail.get('code_kind'))}",
                f";   payload_size: {_text(detail.get('payload_size'))}",
                f";   payload_sha256: {_text(detail.get('payload_sha256'))}",
                f";   presentation: kind={_text(presentation.get('kind'))} "
                f"status={_text(presentation.get('status'))} "
                f"visible={_text(presentation.get('source_visible'))} "
                f"identity={_text(presentation.get('stable_identity'))}",
                f";   listing: kind={_text(listing.get('kind'))} available={_text(listing.get('available'))} "
                f"reason={_text(listing.get('reason'))}",
                ";   restored_source_model:",
                *_restored_source_model_lines(restored_source),
                ";   source_body_ranges:",
                *_code_source_body_range_lines(detail),
            ]
        )
        if resource_id == selected_id:
            lines.extend(
                [
                    f";   selected_code_entry_offset: {_text(selected.get('code_entry_offset'))}",
                    f";   selected_code_bytes_size: {_text(selected.get('code_bytes_size'))}",
                    f";   code_bytes_sha256: {_text(selected.get('code_bytes_sha256'))}",
                    f";   listing_rows: {selected_listing_rows}",
                    "",
                    f"; CODE {_text(resource_id)} {_text(detail.get('name'))} full selected listing follows.",
                ]
            )
            lines.extend(selected_code_source.rstrip().splitlines())
        else:
            lines.extend(_code_source_preview_or_placeholder_lines(detail))
    lines.append("")
    return lines


def _code_source_section_status(detail: Mapping[str, object], *, selected_id: object) -> str:
    if detail.get("id") == selected_id:
        return "selected_full_listing"
    presentation = _mapping(detail.get("source_presentation_status"))
    listing = _mapping(detail.get("listing"))
    if presentation.get("status") == "covered" and listing.get("available") is True:
        return "partial_preview_with_exact_placeholders"
    if presentation.get("status") == "covered":
        return "covered_placeholder"
    return _text(presentation.get("status") or "deferred_placeholder")


def _code_source_body_range_lines(detail: Mapping[str, object]) -> list[str]:
    ranges = [_mapping(item) for item in _sequence(detail.get("code_layout"))]
    if not ranges:
        payload_size = detail.get("payload_size")
        return [
            f";     placeholder payload[0..{_text(payload_size)}): status=deferred "
            "reason=no C-owned CODE layout range available"
        ]
    lines: list[str] = []
    for item in ranges:
        lines.append(
            f";     {_text(item.get('kind'))} payload[{_text(item.get('start'))}..{_text(item.get('end'))}) "
            f"size={_text(item.get('size'))} entrypoint={_text(item.get('entrypoint'))} "
            f"status={_text(item.get('fact_status'))} parser_use={_text(item.get('parser_use'))} "
            f"evidence={_text(item.get('evidence'))} fact={_text(item.get('fact_id'))}"
        )
    return lines


def _code_source_preview_or_placeholder_lines(detail: Mapping[str, object]) -> list[str]:
    lines = [
        (
            f";   byte_preserving_placeholder: CODE {_text(detail.get('id'))} "
            f"payload[0..{_text(detail.get('payload_size'))}) "
            f"sha256={_text(detail.get('payload_sha256'))}"
        ),
        (
            ";   placeholder_reason: full CODE source listing remains deferred; "
            "current source body preserves exact C-owned ranges and evidence status without promoting byte-entry, "
            "A5, or Segment Loader semantics."
        ),
    ]
    previews = [_mapping(item) for item in _sequence(detail.get("preview_windows"))]
    if not previews:
        lines.append(";   preview_rows: none")
        return lines
    lines.append(";   bounded_preview_rows:")
    for preview in previews:
        lines.append(
            f";     preview payload[{_text(preview.get('start'))}..{_text(preview.get('end'))}) "
            f"range={_text(preview.get('range_kind'))} truncated={_text(preview.get('truncated'))} "
            f"status={_text(preview.get('fact_status'))} parser_use={_text(preview.get('parser_use'))} "
            f"reason={_text(preview.get('reason'))}"
        )
        for row in [_mapping(item) for item in _sequence(preview.get("rows"))]:
            lines.append(
                f";       { _text(row.get('offset')) }: bytes={_text(row.get('bytes'))} "
                f"kind={_text(row.get('row_kind'))} decode={_text(row.get('decode_status'))} "
                f"text={_text(row.get('text'))}"
            )
        for reason in [_mapping(item) for item in _sequence(preview.get("deferred_reasons"))]:
            lines.append(
                f";       deferred scope={_text(reason.get('scope'))} "
                f"status={_text(reason.get('fact_status'))} parser_use={_text(reason.get('parser_use'))} "
                f"reason={_text(reason.get('reason'))}"
            )
    return lines


def _code_resource_lines(resources: Sequence[Mapping[str, object]], *, selected_id: object) -> list[str]:
    lines: list[str] = []
    for resource in resources:
        marker = " selected" if resource.get("id") == selected_id else ""
        lines.append(f";   {_resource_line(resource)}{marker}")
    return lines


def _executable_resource_placeholder_lines(placeholders: Sequence[Mapping[str, object]]) -> list[str]:
    if not placeholders:
        return [";   none"]
    lines: list[str] = []
    for item in placeholders:
        source_context = _mapping(item.get("source_context"))
        lines.append(
            f";   {_text(item.get('kind'))}: type={_text(item.get('resource_type'))} "
            f"id={_text(item.get('resource_id'))} name={_text(item.get('resource_name'))} "
            f"count={_text(item.get('resource_count'))} size={_text(item.get('byte_size'))} "
            f"sha256={_text(item.get('sha256'))} identity={_text(item.get('stable_identity'))} "
            f"status={_text(item.get('fact_status') or item.get('status'))} "
            f"source_context={_text(source_context.get('status'))} "
            f"reason={_text(item.get('reason'))}"
        )
        for site in [_mapping(value) for value in _sequence(item.get("reference_sites"))]:
            lines.append(
                f";     reference_site={_text(site.get('kind'))} "
                f"type={_text(site.get('resource_type'))} id={_text(site.get('resource_id'))} "
                f"identity={_text(site.get('stable_identity'))} "
                f"link_status={_text(site.get('link_status'))} "
                f"source_offset={_text(site.get('source_offset'))} reason={_text(site.get('reason'))}"
            )
    return lines


def _code_resource_coverage_lines(resources: Sequence[Mapping[str, object]], *, selected_id: object) -> list[str]:
    return [_code_resource_coverage_line(resource, selected_id=selected_id) for resource in resources]


def _code_resource_coverage_line(resource: Mapping[str, object], *, selected_id: object) -> str:
    resource_id = resource.get("id")
    code = _mapping(resource.get("code"))
    ranges = [_mapping(item) for item in _sequence(code.get("layout_ranges"))]
    kinds = ",".join(_text(item.get("kind")) for item in ranges) or "none"
    candidate = next((item for item in ranges if item.get("kind") in {"confirmed_code", "candidate_code"}), None)
    deferred = next((item for item in ranges if item.get("kind") == "deferred"), None)
    if resource_id == 0:
        status = "metadata-only"
        reason = "CODE 0 jump-table/application metadata"
    elif resource_id == selected_id:
        status = "rendered"
        reason = "expanded below through macos-code listing backend"
    elif candidate is not None:
        status = "partial"
        reason = (
            f"{_text(candidate.get('kind'))} entry payload[{_text(candidate.get('start'))}.."
            f"{_text(candidate.get('end'))}); "
            "full per-resource listing deferred until relocation/source-boundary context is represented"
        )
    elif deferred is not None:
        status = "deferred"
        reason = f"classifier deferred range: {_text(deferred.get('evidence'))}"
    else:
        status = "unsupported"
        reason = "no classified CODE layout range available"
    return (
        f";   CODE {_text(resource_id)} {_text(resource.get('name'))}: "
        f"status={status} layout={kinds} reason={reason}"
    )


def _code_segment_map_lines(entries: Sequence[Mapping[str, object]]) -> list[str]:
    if not entries:
        return [";   none"]
    lines: list[str] = []
    for entry in entries:
        lines.append(
            f";   CODE {_text(entry.get('resource_id'))}: "
            f"jt_first={_text(entry.get('first_jump_table_entry_offset'))} "
            f"jt_count={_text(entry.get('jump_table_entry_count'))} "
            f"jt_span_size={_text(entry.get('jump_table_span_size'))} "
            f"fact={_text(entry.get('fact_id'))} status={_text(entry.get('fact_status'))}"
        )
        routine_candidates = [_mapping(item) for item in _sequence(entry.get("routine_entry_candidates"))]
        for candidate in routine_candidates:
            lines.append(
                f";     routine_candidate index={_text(candidate.get('index'))} "
                f"jt_offset={_text(candidate.get('jump_table_offset'))} "
                f"code0_offset={_text(candidate.get('code0_payload_offset'))} "
                f"routine_offset={_text(candidate.get('routine_offset_from_segment'))} "
                f"fact={_text(candidate.get('fact_id'))} status={_text(candidate.get('fact_status'))}"
            )
    return lines


def _code_resource_detail_lines(details: Sequence[Mapping[str, object]]) -> list[str]:
    if not details:
        return [";   none"]
    lines: list[str] = []
    for detail in details:
        resource_id = detail.get("id")
        lines.append(
            f";   CODE {_text(resource_id)} {_text(detail.get('name'))}: "
            f"role={_text(detail.get('role'))} kind={_text(detail.get('code_kind'))} "
            f"payload_size={_text(detail.get('payload_size'))} sha256={_text(detail.get('payload_sha256'))} "
            f"fact={_text(detail.get('fact_id'))} status={_text(detail.get('fact_status'))}"
        )
        jump_table = _mapping(detail.get("jump_table"))
        if jump_table:
            lines.append(
                f";     jump_table: start={_text(jump_table.get('start'))} "
                f"size={_text(jump_table.get('size'))} entries={_text(jump_table.get('entry_count'))} "
                f"fact={_text(jump_table.get('fact_id'))} status={_text(jump_table.get('fact_status'))}"
            )
        lines.extend(_jump_table_row_lines([_mapping(item) for item in _sequence(detail.get("jump_table_rows"))]))
        segment = _mapping(detail.get("segment_map"))
        if segment:
            lines.append(
                f";     segment: jt_first={_text(segment.get('first_jump_table_entry_offset'))} "
                f"jt_count={_text(segment.get('jump_table_entry_count'))} "
                f"fact={_text(segment.get('fact_id'))} status={_text(segment.get('fact_status'))}"
            )
        presentation = _mapping(detail.get("source_presentation_status"))
        if presentation:
            lines.append(
                f";     source_presentation: kind={_text(presentation.get('kind'))} "
                f"status={_text(presentation.get('status'))} "
                f"stable_identity={_text(presentation.get('stable_identity'))} "
                f"visible={_text(presentation.get('source_visible'))}"
            )
        anchors = [_mapping(item) for item in _sequence(detail.get("navigation_anchors"))]
        lines.extend(_navigation_anchor_lines(anchors))
        lines.append(";     restored_source_model:")
        lines.extend(_restored_source_model_lines(_mapping(detail.get("restored_source"))))
        lines.append(_listing_descriptor_line(_mapping(detail.get("listing"))))
        lines.extend(_preview_window_lines([_mapping(item) for item in _sequence(detail.get("preview_windows"))]))
    return lines


def _jump_table_row_lines(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return []
    lines = [";     jump_table_rows:"]
    for row in rows:
        accepted = _mapping(row.get("accepted_layout"))
        candidate = _mapping(row.get("candidate_target"))
        lines.append(
            f";       entry={_text(row.get('entry_index'))} "
            f"code0_offset={_text(row.get('code0_payload_offset'))} "
            f"entry_size={_text(row.get('entry_size'))} "
            f"target_CODE={_text(row.get('target_resource_id'))} "
            f"routine_offset={_text(row.get('routine_offset_from_segment'))} "
            f"layout_fact={_text(accepted.get('fact_id'))} layout_status={_text(accepted.get('fact_status'))} "
            f"target_fact={_text(candidate.get('fact_id'))} target_status={_text(candidate.get('fact_status'))} "
            f"target_parser_use={_text(candidate.get('parser_use'))}"
        )
    return lines


def _navigation_anchor_lines(anchors: Sequence[Mapping[str, object]]) -> list[str]:
    if not anchors:
        return [";     anchors: none"]
    lines = [";     anchors:"]
    for anchor in anchors:
        lines.append(
            f";       {_text(anchor.get('kind'))}: label={_text(anchor.get('label'))} "
            f"offset={_text(anchor.get('offset'))} fact={_text(anchor.get('fact_id'))} "
            f"status={_text(anchor.get('fact_status'))} parser_use={_text(anchor.get('parser_use'))}"
        )
    return lines


def _listing_descriptor_line(listing: Mapping[str, object]) -> str:
    if not listing:
        return ";     listing: none"
    return (
        f";     listing: kind={_text(listing.get('kind'))} available={_text(listing.get('available'))} "
        f"route={_text(listing.get('route'))} reason={_text(listing.get('reason'))}"
    )


def _preview_window_lines(previews: Sequence[Mapping[str, object]]) -> list[str]:
    if not previews:
        return [";     previews: none"]
    lines = [";     previews:"]
    for preview in previews:
        lines.append(
            f";       {_text(preview.get('kind'))}: start={_text(preview.get('start'))} "
            f"end={_text(preview.get('end'))} size={_text(preview.get('size'))} "
            f"range={_text(preview.get('range_kind'))} fact={_text(preview.get('fact_id'))} "
            f"status={_text(preview.get('fact_status'))} parser_use={_text(preview.get('parser_use'))} "
            f"bounded={_text(preview.get('bounded'))} truncated={_text(preview.get('truncated'))} "
            f"reason={_text(preview.get('reason'))}"
        )
        for reason in [_mapping(item) for item in _sequence(preview.get("deferred_reasons"))]:
            lines.append(
                f";         deferred: scope={_text(reason.get('scope'))} "
                f"fact={_text(reason.get('fact_id'))} status={_text(reason.get('fact_status'))} "
                f"parser_use={_text(reason.get('parser_use'))} reason={_text(reason.get('reason'))}"
            )
        for row in [_mapping(item) for item in _sequence(preview.get("rows"))]:
            fallback = row.get("fallback_reason")
            fallback_text = f" fallback={_text(fallback)}" if fallback else ""
            lines.append(
                f";         row: offset={_text(row.get('offset'))} end={_text(row.get('end'))} "
                f"bytes={_text(row.get('bytes'))} text={_text(row.get('text'))} "
                f"decode={_text(row.get('decode_status'))} row_kind={_text(row.get('row_kind'))}"
                f"{fallback_text} "
                f"range={_text(row.get('range_kind'))} fact={_text(row.get('fact_id'))} "
                f"status={_text(row.get('fact_status'))} parser_use={_text(row.get('parser_use'))}"
            )
    return lines


def _restored_source_model_lines(restored_source: Mapping[str, object]) -> list[str]:
    if not restored_source:
        return [";     none"]
    verifier = _mapping(restored_source.get("source_coverage_verifier"))
    ranges = [_mapping(item) for item in _sequence(restored_source.get("source_ownership_ranges"))]
    references = [_mapping(item) for item in _sequence(restored_source.get("source_reference_records"))]
    extensions = _mapping(restored_source.get("platform_extensions"))
    code_resource = _mapping(extensions.get("code_resource"))
    a5_world = _mapping(extensions.get("a5_world"))
    lines = [
        (
            f";     model={_text(restored_source.get('model'))} "
            f"round_trip_required={str(restored_source.get('round_trip_required')).lower()}"
        ),
        (
            f";     coverage ok={str(verifier.get('ok')).lower()} gaps={_text(verifier.get('gap_count'))} "
            f"overlaps={_text(verifier.get('overlap_count'))} "
            f"unknown_detail={_text(verifier.get('explicit_unknown_missing_detail_count'))}"
        ),
        (
            f";     code_resource={_text(code_resource.get('resource_type'))} {_text(code_resource.get('resource_id'))} "
            f"name={_text(code_resource.get('resource_name'))}"
        ),
        f";     a5_world status={_text(a5_world.get('status'))} parser_use={_text(a5_world.get('parser_use'))}",
        ";     ownership_ranges:",
    ]
    lines.extend(_restored_source_ownership_lines(ranges))
    lines.append(";     source_reference_records:")
    lines.extend(_restored_source_reference_lines(references))
    return lines


def _restored_source_ownership_lines(ranges: Sequence[Mapping[str, object]]) -> list[str]:
    if not ranges:
        return [";       none"]
    return [
        (
            f";       {index}: role={_text(item.get('role'))} "
            f"span={_text(item.get('start'))}..{_text(item.get('end'))} "
            f"status={_text(item.get('fact_status') or item.get('status'))} "
            f"parser_use={_text(item.get('parser_use'))} reason={_text(item.get('reason'))}"
        )
        for index, item in enumerate(ranges)
    ]


def _restored_source_reference_lines(references: Sequence[Mapping[str, object]]) -> list[str]:
    if not references:
        return [";       none"]
    return [
        (
            f";       {index}: kind={_text(item.get('kind'))} "
            f"ownership={_text(item.get('ownership_range_index'))} "
            f"status={_text(item.get('fact_status') or item.get('status'))} "
            f"parser_use={_text(item.get('parser_use'))} target={_text(item.get('target'))}"
        )
        for index, item in enumerate(references)
    ]


def _resource_line(resource: Mapping[str, object]) -> str:
    return (
        f"CODE {_text(resource.get('id'))} {_text(resource.get('name'))}: "
        f"payload_size={_text(resource.get('payload_size'))} sha256={_text(resource.get('sha256'))}"
    )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _text(value: object) -> str:
    return "unknown" if value is None else str(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the committed Mac OS example target files")
    args = parser.parse_args(argv)
    if args.write:
        write_macos_example_target()
    else:
        print(render_macos_example_asm(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
