"""Committed Classic Mac OS example target artifact rendering."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path

from amiga_reversing.disasm.c_backend import (
    extract_macos_hfs_code_resource_payload_bytes_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import read_macos_hfs_image_bytes
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

_RAW_LOCAL_LABEL_RE = re.compile(r"\bloc_0_([0-9A-Fa-f]{8})\b")

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
    hfs_bytes = read_macos_hfs_image_bytes(project_root / MACOS_EXAMPLE_SOURCE_IMAGE)
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
    selected_listing = _mapping(selected.get("listing"))
    code_resources = [_mapping(item) for item in _sequence(container.get("code_resources"))]
    code_resource_details = [_mapping(item) for item in _sequence(container.get("code_resource_details"))]
    source_body_sections = [_mapping(item) for item in _sequence(container.get("source_body_sections"))]
    source_quality_gate = _mapping(container.get("source_quality_gate"))
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
        source_body_sections,
        selected_id=selected.get("id"),
        selected=selected,
        selected_listing=selected_listing,
        selected_code_source=selected_code_source,
        selected_listing_rows=total_rows,
        hfs_bytes=hfs_bytes,
        project_root=project_root,
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
    lines = [*header_lines, *source_sections, *_source_quality_gate_lines(source_quality_gate)]
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
    sections: Sequence[Mapping[str, object]],
    *,
    selected_id: object,
    selected: Mapping[str, object],
    selected_listing: Mapping[str, object],
    selected_code_source: str,
    selected_listing_rows: int,
    hfs_bytes: bytes,
    project_root: Path,
) -> list[str]:
    lines = ["; CODE source body sections"]
    for section in sections:
        resource_id = section.get("id")
        payload_bytes = _code_resource_payload_bytes(section, hfs_bytes=hfs_bytes, project_root=project_root)
        restored_source = _mapping(section.get("restored_source"))
        presentation = _mapping(section.get("presentation"))
        listing = _mapping(section.get("listing"))
        lines.extend(
            [
                "",
                f"; CODE {_text(resource_id)} {_text(section.get('name'))} source section",
                f"{_text(section.get('label'))}:",
                f";   source_section_id: {_text(section.get('source_section_id'))}",
                f";   source_kind: {_text(section.get('source_kind'))}",
                f";   backend: {_text(section.get('backend'))}",
                f";   status: {_text(section.get('status'))}",
                f";   resource_type: {_text(section.get('resource_type'))}",
                f";   id: {_text(resource_id)}",
                f";   name: {_text(section.get('name'))}",
                f";   role: {_text(section.get('role'))}",
                f";   code_kind: {_text(section.get('code_kind'))}",
                f";   payload_size: {_text(section.get('payload_size'))}",
                f";   payload_sha256: {_text(section.get('payload_sha256'))}",
                f";   presentation: kind={_text(presentation.get('kind'))} "
                f"status={_text(presentation.get('status'))} "
                f"visible={_text(presentation.get('source_visible'))} "
                f"identity={_text(presentation.get('stable_identity'))}",
                f";   listing: kind={_text(listing.get('kind'))} available={_text(listing.get('available'))} "
                f"reason={_text(listing.get('reason'))}",
                ";   restored_source_model:",
                *_restored_source_model_lines(restored_source),
                ";   source_body_ranges:",
                *_code_source_body_range_lines(section),
                *_incoming_code0_xref_lines(section),
            ]
        )
        if resource_id == 0:
            lines.extend(_code0_structured_source_lines(section))
        if resource_id == selected_id:
            selected_context = _mapping(section.get("selected_listing_context"))
            lines.extend(
                [
                    f";   selected_code_entry_offset: {_text(selected_context.get('code_entry_offset'))}",
                    f";   selected_code_bytes_size: {_text(selected_context.get('code_bytes_size'))}",
                    f";   code_bytes_sha256: {_text(selected_context.get('code_bytes_sha256'))}",
                    f";   listing_rows: {selected_listing_rows}",
                    *_code1_entry_stub_context_lines(section),
                    "",
                    f"; CODE {_text(resource_id)} {_text(section.get('name'))} byte-real source follows.",
                ]
            )
            lines.extend(_code_source_byte_real_lines(section, payload_bytes=payload_bytes))
        else:
            lines.extend(_code_source_byte_real_lines(section, payload_bytes=payload_bytes))
    lines.append("")
    return lines


def _code_resource_payload_bytes(section: Mapping[str, object], *, hfs_bytes: bytes, project_root: Path) -> bytes:
    resource_id = _int_value(section.get("id"))
    if resource_id is None:
        return b""
    return extract_macos_hfs_code_resource_payload_bytes_with_c_backend(
        hfs_bytes,
        MACOS_EXAMPLE_HFS_PATH,
        resource_id,
        project_root=project_root,
    )


def _code_source_body_range_lines(section: Mapping[str, object]) -> list[str]:
    ranges = [_mapping(item) for item in _sequence(section.get("source_body_ranges"))]
    if not ranges:
        payload_size = section.get("payload_size")
        return [
            f";     placeholder payload[0..{_text(payload_size)}): status=deferred "
            "reason=no C-owned CODE layout range available"
        ]
    lines: list[str] = []
    for item in ranges:
        lines.append(
            f";     {_text(item.get('kind'))} payload[{_text(item.get('start'))}..{_text(item.get('end'))}) "
            f"size={_text(item.get('size'))} entrypoint={_text(item.get('entrypoint'))}"
        )
    return lines


def _code_source_byte_real_lines(section: Mapping[str, object], *, payload_bytes: bytes) -> list[str]:
    placeholder = _mapping(section.get("byte_preserving_placeholder"))
    semantic_source = _mapping(section.get("semantic_source"))
    semantic_rows = [_mapping(item) for item in _sequence(semantic_source.get("rows"))]
    lines = [
        (
            f";   byte_preserving_placeholder: CODE {_text(section.get('id'))} "
            f"payload[{_text(placeholder.get('start'))}..{_text(placeholder.get('end'))}) "
            f"sha256={_text(placeholder.get('payload_sha256'))}"
        ),
        f";   placeholder_reason: {_text(placeholder.get('reason'))}",
        ";   byte_real_source:",
    ]
    if section.get("id") == 0:
        lines.extend(_code0_byte_real_source_lines(section, payload_bytes=payload_bytes))
        return lines
    ranges = [_mapping(item) for item in _sequence(section.get("source_body_ranges"))]
    if not ranges:
        lines.extend(_dc_b_lines(payload_bytes, label=f"{_text(section.get('label'))}_payload"))
        return lines
    for item in ranges:
        start = _int_value(item.get("start")) or 0
        end = _int_value(item.get("end")) or start
        kind = _text(item.get("kind"))
        label = f"{_text(section.get('label'))}_{kind}_{start:08x}"
        lines.append(f";     {kind} payload[{start}..{end})")
        if kind in {"candidate_code", "candidate_unresolved_prefix", "confirmed_code", "code"} and semantic_rows:
            lines.extend(_semantic_source_lines(section, semantic_source, payload_bytes=payload_bytes, start=start, end=end))
            continue
        lines.extend(_dc_b_lines(payload_bytes[start:end], label=label, base_offset=start))
    return lines


def _code0_byte_real_source_lines(section: Mapping[str, object], *, payload_bytes: bytes) -> list[str]:
    context = _mapping(section.get("code0_structured_context"))
    jump_table = _mapping(context.get("jump_table"))
    label = f"{_text(section.get('label'))}_metadata_00000000"
    if len(payload_bytes) < 16:
        return _dc_b_lines(payload_bytes, label=label)
    above_a5 = int.from_bytes(payload_bytes[0:4], "big")
    below_a5 = int.from_bytes(payload_bytes[4:8], "big")
    jump_table_length = int.from_bytes(payload_bytes[8:12], "big")
    jump_table_offset = int.from_bytes(payload_bytes[12:16], "big")
    lines = [
        f"{label}:",
        "CODE_0_above_a5_size:",
        f"\tdc.l ${above_a5:08X}",
        "CODE_0_below_a5_size:",
        f"\tdc.l ${below_a5:08X}",
        "CODE_0_jump_table_length:",
        f"\tdc.l ${jump_table_length:08X}",
        "CODE_0_jump_table_offset_from_a5:",
        f"\tdc.l ${jump_table_offset:08X}",
        "CODE_0_jump_table:",
    ]
    jump_start = _int_value(jump_table.get("start")) or 16
    jump_end = _int_value(jump_table.get("end")) or len(payload_bytes)
    entry_size = _int_value(jump_table.get("entry_size")) or 8
    rows_by_offset = {
        _int_value(row.get("code0_payload_offset")): row
        for row in (_mapping(item) for item in _sequence(context.get("jump_table_rows")))
    }
    cursor = min(jump_start, len(payload_bytes))
    entry_index = 0
    while entry_size == 8 and cursor + entry_size <= min(jump_end, len(payload_bytes)):
        chunk = payload_bytes[cursor : cursor + entry_size]
        row = rows_by_offset.get(cursor)
        if row:
            lines.extend(_code0_jump_table_entry_lines(row, chunk=chunk, fallback_index=entry_index))
        else:
            lines.extend(_code0_raw_jump_table_entry_lines(chunk, entry_index=entry_index))
        cursor += entry_size
        entry_index += 1
    if cursor < len(payload_bytes):
        lines.extend(_dc_b_lines(payload_bytes[cursor:], label=f"CODE_0_trailing_metadata_{cursor:08x}", base_offset=cursor))
    return lines


def _code0_jump_table_entry_lines(row: Mapping[str, object], *, chunk: bytes, fallback_index: int) -> list[str]:
    entry_index = _int_value(row.get("entry_index"))
    if entry_index is None:
        entry_index = fallback_index
    label = f"CODE_0_jump_table_entry_{entry_index}"
    target_resource_id = _int_value(row.get("target_resource_id"))
    routine_offset = _int_value(row.get("routine_offset_from_segment"))
    if target_resource_id is None or routine_offset is None:
        return _code0_raw_jump_table_entry_lines(chunk, entry_index=entry_index)
    if int.from_bytes(chunk[2:4], "big") == 0x3F3C and int.from_bytes(chunk[6:8], "big") == 0xA9F0:
        return [
            f"{label}:",
            f"\tdc.w ${routine_offset:04X}",
            f"\tmove.w #{target_resource_id},-(a7)",
            "\tdc.w $A9F0",
        ]
    trap_word = int.from_bytes(chunk[2:4], "big")
    if trap_word == 0xA9F0:
        return [
            f"{label}:",
            f"\tdc.w ${target_resource_id & 0xFFFF:04X}",
            "\tdc.w $A9F0",
            f"\tdc.l ${routine_offset:08X}",
        ]
    return _code0_raw_jump_table_entry_lines(chunk, entry_index=entry_index)


def _code0_raw_jump_table_entry_lines(chunk: bytes, *, entry_index: int) -> list[str]:
    return [
        f"CODE_0_jump_table_entry_{entry_index}:",
        f"\tdc.w ${int.from_bytes(chunk[0:2], 'big'):04X}",
        f"\tdc.w ${int.from_bytes(chunk[2:4], 'big'):04X}",
        f"\tdc.l ${int.from_bytes(chunk[4:8], 'big'):08X}",
    ]


def _semantic_source_lines(
    section: Mapping[str, object],
    semantic_source: Mapping[str, object],
    *,
    payload_bytes: bytes,
    start: int,
    end: int,
) -> list[str]:
    rows = [
        row
        for row in (_mapping(value) for value in _sequence(semantic_source.get("rows")))
        if _semantic_row_in_range(row, start=start, end=end)
    ]
    gap_kinds = {
        (_int_value(item.get("start")), _int_value(item.get("end"))): _text(item.get("kind"))
        for item in (_mapping(value) for value in _sequence(semantic_source.get("semantic_gap_residuals")))
    }
    lines = [
        (
            f";     semantic_source: kind={_text(semantic_source.get('kind'))} "
            f"status={_text(semantic_source.get('status'))} "
            f"instructions={_text(semantic_source.get('instruction_row_count'))} "
            f"labels={_text(semantic_source.get('generated_label_count'))} "
            f"xrefs={_text(semantic_source.get('generated_xref_count'))}"
        )
    ]
    resource_id = section.get("id")
    cursor = start
    for row in rows:
        kind = row.get("kind")
        payload_offset = _int_value(row.get("payload_offset"))
        payload_end = _int_value(row.get("payload_end")) or payload_offset
        if payload_offset is not None and payload_offset > cursor:
            lines.extend(
                _semantic_gap_lines(
                    payload_bytes[cursor:payload_offset],
                    label=f"{_text(section.get('label'))}_{_semantic_gap_kind(gap_kinds, cursor, payload_offset)}_{cursor:08x}",
                    kind=_semantic_gap_kind(gap_kinds, cursor, payload_offset),
                    base_offset=cursor,
                )
            )
            cursor = payload_offset
        if kind == "label":
            label_offset = payload_offset if payload_offset is not None else start
            lines.append(f"CODE_{_text(resource_id)}_loc_{label_offset:08x}:")
            continue
        text = _macos_semantic_text(str(row.get("text") or "").rstrip(), resource_id=resource_id)
        if not text:
            continue
        if row.get("kind") == "instruction":
            lines.append(text)
        else:
            lines.append(text)
        if payload_end is not None:
            cursor = max(cursor, payload_end)
    if cursor < end:
        lines.extend(
            _semantic_gap_lines(
                payload_bytes[cursor:end],
                label=f"{_text(section.get('label'))}_{_semantic_gap_kind(gap_kinds, cursor, end)}_{cursor:08x}",
                kind=_semantic_gap_kind(gap_kinds, cursor, end),
                base_offset=cursor,
            )
        )
    return lines


def _semantic_gap_kind(gap_kinds: Mapping[tuple[int | None, int | None], str], start: int, end: int) -> str:
    exact = gap_kinds.get((start, end))
    if exact:
        return exact
    for (gap_start, gap_end), kind in gap_kinds.items():
        if gap_start is not None and gap_end is not None and gap_start <= start and end <= gap_end:
            return kind
    return "semantic_decode_gap"


def _semantic_gap_lines(data: bytes, *, label: str, kind: str, base_offset: int) -> list[str]:
    if kind == "semantic_alignment_padding_gap" and data and all(byte == 0 for byte in data):
        return [f"{label}:", f"\tds.b {len(data)}"]
    return _dc_b_lines(data, label=label, base_offset=base_offset)


def _macos_semantic_text(text: str, *, resource_id: object) -> str:
    def replace(match: re.Match[str]) -> str:
        return f"CODE_{_text(resource_id)}_loc_{int(match.group(1), 16):08x}"

    return _RAW_LOCAL_LABEL_RE.sub(replace, text)


def _incoming_code0_xref_lines(section: Mapping[str, object]) -> list[str]:
    xrefs = [_mapping(item) for item in _sequence(section.get("incoming_code0_xrefs"))]
    if not xrefs:
        return []
    lines = [";   incoming_CODE0_xrefs:"]
    for xref in xrefs:
        candidate = _mapping(xref.get("candidate_target"))
        lines.append(
            f";     from={_text(xref.get('source_label'))} "
            f"target={_text(xref.get('target_label'))} "
            f"source_payload={_text(xref.get('source_payload_offset'))} "
            f"target_payload={_text(xref.get('target_payload_offset'))} "
            f"status={_text(candidate.get('fact_status'))} "
            f"parser_use={_text(candidate.get('parser_use'))} "
            f"fact={_text(candidate.get('fact_id'))}"
        )
    return lines


def _semantic_row_in_range(row: Mapping[str, object], *, start: int, end: int) -> bool:
    payload_offset = _int_value(row.get("payload_offset"))
    payload_end = _int_value(row.get("payload_end"))
    if payload_offset is None:
        return False
    if payload_end is None or payload_end == payload_offset:
        return start <= payload_offset < end
    return start <= payload_offset and payload_end <= end


def _source_quality_gate_lines(gate: Mapping[str, object]) -> list[str]:
    if not gate:
        return [
            "",
            "; Source quality gate",
            ";   status: blocked",
            ";   reason: missing source_quality_gate model",
            "",
        ]
    checklist = _mapping(gate.get("checklist"))
    lines = [
        "",
        "; Source quality gate",
        f";   kind: {_text(gate.get('kind'))}",
        f";   status: {_text(gate.get('status'))}",
        f";   semantic_closeout_status: {_text(gate.get('semantic_closeout_status'))}",
        f";   baseline_status: {_text(gate.get('baseline_status'))}",
        f";   baseline_status_meaning: {_text(gate.get('baseline_status_meaning'))}",
        f";   scope: {_text(gate.get('scope'))}",
        ";   semantic_components:",
    ]
    components = _mapping(gate.get("semantic_components"))
    for key in sorted(components):
        lines.append(f";     {key}: {_text(components.get(key))}")
    lines.extend(
        [
        ";   checklist:",
        ]
    )
    for key in sorted(checklist):
        lines.append(f";     {key}: {_text(checklist.get(key))}")
    claims = _sequence(gate.get("does_not_claim"))
    if claims:
        lines.append(";   does_not_claim:")
        lines.extend(f";     {claim}" for claim in claims)
    non_blocking = _sequence(gate.get("non_blocking_for_semantic_disassembly"))
    if non_blocking:
        lines.append(";   non_blocking_for_semantic_disassembly:")
        lines.extend(f";     {item}" for item in non_blocking)
    lines.append(";   resource_review:")
    for item in [_mapping(value) for value in _sequence(gate.get("resources"))]:
        lines.extend(
            [
                (
                    f";     CODE {_text(item.get('resource_id'))}: "
                    f"section={_text(item.get('section_id'))} "
                    f"ownership={','.join(_text(value) for value in _sequence(item.get('ownership_kinds')))} "
                    f"coverage={_text(item.get('ownership_complete'))} "
                    f"labels={len(_sequence(item.get('labels')))} "
                    f"xrefs={_text(item.get('generated_xref_count'))} "
                    f"instructions={_text(item.get('semantic_instruction_row_count'))} "
                    f"body_spans={_text(item.get('executable_body_span_count'))} "
                    f"byte_real_only_body={_text(item.get('byte_real_only_executable_body'))} "
                    f"reachable_evidence={len(_sequence(item.get('reachable_code_evidence')))} "
                    f"residuals={len(_sequence(item.get('residuals')))}"
                ),
                f";       next: {_text(item.get('next_required_implementation'))}",
            ]
        )
        residual_lines, candidate_offsets = _human_residual_lines(item)
        lines.extend(residual_lines)
        if candidate_offsets:
            lines.append(
                f";       residual candidate_unvisited_entry_pattern count={len(candidate_offsets)} "
                f"payload_offsets={','.join(candidate_offsets[:12])}"
                f"{',...' if len(candidate_offsets) > 12 else ''} "
                "status=candidate parser_use=candidate_only reason=unvisited executable-looking bytes remain "
                "structured residuals, not promoted to source rows"
            )
    lines.append("")
    return lines


def _human_residual_lines(item: Mapping[str, object]) -> tuple[list[str], list[str]]:
    lines: list[str] = []
    candidate_offsets: list[str] = []
    for residual in [_mapping(value) for value in _sequence(item.get("residuals"))]:
        if residual.get("kind") == "candidate_unvisited_entry_pattern":
            start = _int_value(residual.get("start"))
            if start is not None:
                candidate_offsets.append(f"{start}")
            continue
        lines.append(
            f";       residual { _text(residual.get('kind')) } "
            f"payload[{_text(residual.get('start'))}..{_text(residual.get('end'))}) "
            f"status={_text(residual.get('status'))} parser_use={_text(residual.get('parser_use'))} "
            f"reason={_text(residual.get('reason'))}"
        )
    return lines, candidate_offsets


def _dc_b_lines(data: bytes, *, label: str, base_offset: int = 0) -> list[str]:
    lines = [f"{label}:"]
    if not data:
        lines.append(";     empty")
        return lines
    for offset in range(0, len(data), 16):
        chunk = data[offset : offset + 16]
        byte_text = ",".join(f"${value:02X}" for value in chunk)
        lines.append(f"\tdc.b {byte_text}")
    return lines


def _code0_structured_source_lines(section: Mapping[str, object]) -> list[str]:
    context = _mapping(section.get("code0_structured_context"))
    jump_table = _mapping(context.get("jump_table"))
    rows = [_mapping(item) for item in _sequence(context.get("jump_table_rows"))]
    xrefs = [_mapping(item) for item in _sequence(context.get("generated_routing_xrefs"))]
    lines = [
        ";   structured_CODE0_context:",
        ";     above/below A5 metadata and jump-table header are accepted CODE 0 metadata.",
        f";     jump_table payload[{_text(jump_table.get('start'))}..{_text(jump_table.get('end'))}) "
        f"entry_size={_text(jump_table.get('entry_size'))} entry_count={_text(jump_table.get('entry_count'))} "
        f"status={_text(jump_table.get('fact_status'))} parser_use={_text(jump_table.get('parser_use'))} "
        f"fact={_text(jump_table.get('fact_id'))}",
    ]
    if not rows:
        lines.append(
            ";     no parsed jump-table rows; raw CODE 0 payload remains covered by the exact metadata placeholder"
        )
        return lines
    for row in rows:
        accepted = _mapping(row.get("accepted_layout"))
        candidate = _mapping(row.get("candidate_target"))
        target_id = row.get("target_resource_id")
        entry_index = row.get("entry_index")
        label = f"CODE_0_jump_table_entry_{_text(entry_index)}"
        lines.extend(
            [
                f";     {label}: payload_offset={_text(row.get('code0_payload_offset'))} "
                f"size={_text(row.get('entry_size'))}",
                f";     accepted_layout status={_text(accepted.get('fact_status'))} "
                f"parser_use={_text(accepted.get('parser_use'))} fact={_text(accepted.get('fact_id'))}",
            ]
        )
        if candidate:
            lines.append(
                f";     candidate_target target_section=CODE_{_text(target_id)} "
                f"target_resource_id={_text(target_id)} "
                f"routine_offset={_text(row.get('routine_offset_from_segment'))} "
                f"status={_text(candidate.get('fact_status'))} parser_use={_text(candidate.get('parser_use'))} "
                f"fact={_text(candidate.get('fact_id'))}"
            )
        else:
            lines.append(";     no decoded routine target for this accepted jump-table entry")
        for xref in xrefs:
            if xref.get("entry_index") == entry_index:
                lines.append(
                    f";     generated_xref source={_text(xref.get('source_label'))} "
                    f"target={_text(xref.get('target_label'))} "
                    f"link_status={_text(xref.get('link_status'))}"
                )
    return lines


def _code1_entry_stub_context_lines(section: Mapping[str, object]) -> list[str]:
    if section.get("id") != 1:
        return []
    context = _mapping(section.get("code1_layout_context"))
    header = _mapping(context.get("far_model_header"))
    stub = _mapping(context.get("candidate_entry_stub"))
    residual = _mapping(context.get("candidate_body_after_stub"))
    return [
        ";   CODE_1_layout_context:",
        f"{_text(header.get('label'))}:",
        (
            f";     payload[{_text(header.get('start'))}..{_text(header.get('end'))}) "
            f"status={_text(header.get('status'))} parser_use={_text(header.get('parser_use'))} "
            f"reason={_text(header.get('reason'))}"
        ),
        f"{_text(stub.get('label'))}:",
        (
            f";     payload[{_text(stub.get('start'))}..{_text(stub.get('end'))}) "
            f"selected_code_bytes[{_text(stub.get('selected_code_bytes_start'))}.."
            f"{_text(stub.get('selected_code_bytes_end'))}) "
            f"status={_text(stub.get('status'))} parser_use={_text(stub.get('parser_use'))} "
            f"reason={_text(stub.get('reason'))}"
        ),
        f"{_text(residual.get('label'))}:",
        (
            f";     payload[{_text(residual.get('start'))}..{_text(residual.get('end'))}) "
            f"status={_text(residual.get('status'))} parser_use={_text(residual.get('parser_use'))} "
            f"reason={_text(residual.get('reason'))}"
        ),
    ]


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
        listing = _mapping(detail.get("listing"))
        lines.append(_listing_descriptor_line(listing))
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


def _int_value(value: object) -> int | None:
    return value if isinstance(value, int) else None


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
