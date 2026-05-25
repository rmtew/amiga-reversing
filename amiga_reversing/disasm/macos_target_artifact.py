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
    selected_layout = [_mapping(item) for item in _sequence(selected.get("code_layout"))]
    selected_orphans = [_mapping(item) for item in _sequence(selected.get("orphan_ranges"))]
    selected_relocations = _mapping(selected.get("relocation_fixups"))
    code_resources = [_mapping(item) for item in _sequence(container.get("code_resources"))]
    code_resource_details = [_mapping(item) for item in _sequence(container.get("code_resource_details"))]
    code_segment_map = [_mapping(item) for item in _sequence(container.get("code_segment_map"))]
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
    lines: list[str] = [
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
        "",
        "; Unsupported Mac Segment Loader/runtime areas",
        *[f";   {item}" for item in unsupported],
        "",
        "; Selected CODE segment",
        f";   source_kind: {_text(native_source.get('source_kind'))}",
        f";   backend: {_text(native_source.get('backend'))}",
        f";   resource_type: {_text(selected.get('resource_type'))}",
        f";   id: {_text(selected.get('id'))}",
        f";   name: {_text(selected.get('name'))}",
        f";   fork: {_text(selected_listing.get('fork'))}",
        f";   payload_size: {_text(selected.get('payload_size'))}",
        f";   code_entry_offset: {_text(selected.get('code_entry_offset'))}",
        f";   code_bytes_size: {_text(selected.get('code_bytes_size'))}",
        f";   payload_sha256: {_text(selected.get('sha256'))}",
        f";   code_bytes_sha256: {_text(selected.get('code_bytes_sha256'))}",
        ";   classified_layout:",
        *_code_layout_lines(selected_layout),
        ";   orphan_ranges:",
        *_orphan_range_lines(selected_orphans),
        ";   relocation_fixups:",
        _relocation_fixup_line(selected_relocations),
        f";   listing_rows: {total_rows}",
        "",
        "; CODE 1 Main listing follows. Offsets are local to the selected CODE resource code bytes.",
    ]
    lines.extend(selected_code_source.rstrip().splitlines())
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


def _code_resource_lines(resources: Sequence[Mapping[str, object]], *, selected_id: object) -> list[str]:
    lines: list[str] = []
    for resource in resources:
        marker = " selected" if resource.get("id") == selected_id else ""
        lines.append(f";   {_resource_line(resource)}{marker}")
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
        anchors = [_mapping(item) for item in _sequence(detail.get("navigation_anchors"))]
        lines.extend(_navigation_anchor_lines(anchors))
        lines.append(";     layout:")
        lines.extend(_code_layout_lines([_mapping(item) for item in _sequence(detail.get("code_layout"))]))
        lines.append(";     orphan_ranges:")
        lines.extend(_orphan_range_lines([_mapping(item) for item in _sequence(detail.get("orphan_ranges"))]))
        lines.append(";     relocation_fixups:")
        lines.append(_relocation_fixup_line(_mapping(detail.get("relocation_fixups"))))
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


def _code_layout_lines(ranges: Sequence[Mapping[str, object]]) -> list[str]:
    if not ranges:
        return [";     none"]
    return [
        f";     {_text(item.get('kind'))}: start={_text(item.get('start'))} "
        f"end={_text(item.get('end'))} entrypoint={_text(item.get('entrypoint'))} "
        f"evidence={_text(item.get('evidence'))} fact={_text(item.get('fact_id'))} "
        f"status={_text(item.get('fact_status'))}"
        for item in ranges
    ]


def _orphan_range_lines(ranges: Sequence[Mapping[str, object]]) -> list[str]:
    if not ranges:
        return [";     none"]
    return [
        f";     {_text(item.get('classification'))}: start={_text(item.get('start'))} "
        f"end={_text(item.get('end'))} evidence={_text(item.get('evidence'))} "
        f"fact={_text(item.get('fact_id'))} status={_text(item.get('fact_status'))}"
        for item in ranges
    ]


def _relocation_fixup_line(relocation_fixups: Mapping[str, object]) -> str:
    if not relocation_fixups:
        return ";     none"
    return (
        f";     status={_text(relocation_fixups.get('status'))} "
        f"fact={_text(relocation_fixups.get('fact_id'))} "
        f"parser_use={_text(relocation_fixups.get('parser_use'))} "
        f"reason={_text(relocation_fixups.get('reason'))}"
    )


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
