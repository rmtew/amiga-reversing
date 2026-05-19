from __future__ import annotations

import json
import os
import queue
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from amiga_reversing.disasm import server as disasm_server
from amiga_reversing.disasm.api import ListingWindowPayload
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import UnsupportedCBackendProject
from amiga_reversing.disasm.manual_actions import (
    ReviewItemKind,
    ReviewItemState,
    ReviewState,
)
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord
from tests.listing_row_fixtures import serialize_row
from tests.listing_types_fixtures import (
    AppSlotRef,
    BlockRowContext,
    ListingRow,
    PlatformTypedAccess,
    PlatformUnresolvedTypedAccess,
    RuntimeAddressRef,
    SemanticOperand,
    SymbolOperandMetadata,
)

_FULL_DATA_ROLE_IDS = {
    "string",
    "length_prefixed_string",
    "string_control_stream",
    "scalar_table",
    "lookup_table",
    "pointer_table",
    "copper_list",
    "palette",
    "bitmap",
    "sound_sample",
    "audio_table",
    "sprite",
}


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _kill_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            return
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
            return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        process.kill()
        process.wait(timeout=5)


def _read_http_bytes(url: str) -> tuple[bytes, str]:
    with urllib.request.urlopen(url, timeout=2) as response:
        return response.read(), response.headers.get("Content-Type", "")


def _read_http_bytes_with_headers(url: str, headers: dict[str, str]) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=2) as response:
        return response.read(), response.headers.get("Content-Type", "")


def _binary_project(project_name: str, *, ready: bool) -> ProjectRecord:
    return ProjectRecord(
        id=project_name,
        name=project_name,
        kind=ProjectKind.BINARY,
        target_dir=f"targets/{project_name}",
        output_path=None,
        binary_path="bin/BLOODWYCH" if ready else None,
        ready=ready,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=None,
        disk_type=None,
        parent_project_id=None,
        target_type="program",
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )


def test_ui_preferences_route_persists_project_local_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = _binary_project("amiga_raw_demo", ready=True)
    target_dir = tmp_path / "targets" / project.id
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "bin" / "demo.bin"
    binary_path.parent.mkdir()
    binary_path.write_bytes(b"\0" * 16)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary_path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,
        load_address=0x6000,
        entrypoint=0x6004,
        code_start_offset=0,
        display_path="bin/demo.bin",
        analysis_cache_path=target_dir / "binary.analysis",
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=target_dir, binary_source=source),
    )

    initial = disasm_server.route_request("GET", f"/api/projects/{project.id}/ui-preferences", {})
    assert initial["data"]["preferences"]["listing_location"] is None
    assert initial["data"]["source_entrypoint"] == {
        "addr": 0x6004,
        "source_offset": 4,
        "runtime_address": 0x6004,
    }

    saved = disasm_server.route_request(
        "PUT",
        f"/api/projects/{project.id}/ui-preferences",
        {},
        {
            "listing_location": {
                "locator": {
                    "target_id": project.id,
                    "projection_hash": "hash-1",
                    "row_key": "entry",
                    "kind": "instruction",
                    "section_index": 0,
                    "start_offset": 4,
                    "storage_address": 4,
                    "runtime_address": 0x6004,
                },
                "viewport_anchor": {"scroll_top": 66, "window_start": 0},
                "row_index": 3,
                "stable_key": "legacy-entry",
            },
            "source_export_assembler": "vasm",
            "manual_action": "must-not-persist",
        },
    )

    assert saved["data"]["preferences"]["listing_location"] == {
        "locator": {
            "target_id": project.id,
            "projection_hash": "hash-1",
            "row_key": "entry",
            "kind": "instruction",
            "section_index": 0,
            "start_offset": 4,
            "storage_address": 4,
            "runtime_address": 0x6004,
        },
        "viewport_anchor": {"scroll_top": 66, "window_start": 0},
    }
    assert saved["data"]["preferences"]["source_export_assembler"] == "vasm"
    assert "manual_action" not in saved["data"]["preferences"]
    assert not (target_dir / "manual_actions.jsonl").exists()


class _FakeCListingArtifact:
    def __init__(self) -> None:
        self.closed = False
        self.navigation_calls = 0

    def close(self) -> None:
        self.closed = True

    def source_text_with_profile(self) -> tuple[str, dict[str, object]]:
        return "    SECTION section,code\n    rts\n", {"generation": "fake-source"}

    def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        return {"total_rows": 1}, {"generation": "fake"}

    def navigation_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        self.navigation_calls += 1
        return (
            {
                "analysis_generation": "full",
                "total_rows": 1,
                "groups": {
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
                    "labels": [
                        {
                            "addr": 0,
                            "row_index": 0,
                            "summary": "from_c:",
                            "match_text": "from_c",
                            "stable_key": "c-label",
                            "symbol": "from_c",
                            "ref_count": 1,
                            "access_counts": {"definition": 1},
                            "refs": [],
                        }
                    ],
                    "comments": [],
                },
                "app_slot_analysis": {},
                "type_flow_analysis": {},
            },
            {"generation": "fake"},
        )

    def analysis_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        return (
            {
                "sections": [
                    {
                        "section_index": 0,
                        "section_size": 4,
                        "blocks": [{"start_offset": 0, "end_offset": 2}],
                    }
                ]
            },
            {"generation": "fake-analysis"},
        )


class _RowsCListingArtifact:
    def __init__(
        self,
        rows: list[ListingRow],
        *,
        project_name: str = "bloodwych",
        api_calls_by_row_id: dict[str, dict[str, object]] | None = None,
        app_slot_analysis: dict[str, object] | None = None,
        type_flow_analysis: dict[str, object] | None = None,
    ) -> None:
        self.rows = rows
        self.project_name = project_name
        self.api_calls_by_row_id = api_calls_by_row_id or {}
        self.app_slot_analysis = app_slot_analysis or {}
        self.type_flow_analysis = type_flow_analysis or {}
        self.closed = False
        self.analysis_calls = 0

    def close(self) -> None:
        self.closed = True

    def window_payload(self, *, start: int, count: int):
        return _test_listing_index_window_payload(self.rows, start, count, self.api_calls_by_row_id), {}

    def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        return {"total_rows": len(self.rows)}, {"generation": "fake"}

    def addr_window_payload(self, *, addr: int | None, before: int, after: int):
        return _test_listing_addr_window_payload(self.rows, addr, before=before, after=after, api_calls_by_row_id=self.api_calls_by_row_id), {}

    def row_for_source_offset(self, *, section_index: int | None, offset: int):
        if section_index is None:
            return None
        for index, row in enumerate(self.rows):
            if row.section_index != section_index:
                continue
            start = row.start_offset if row.start_offset is not None else row.addr
            if start is None:
                continue
            end = row.end_offset if row.end_offset is not None else start + 1
            if start <= offset < end or start == offset:
                serialized = dict(serialize_row(row))
                serialized["row_index"] = index
                return serialized
        return None

    def anchor_window_payload(self, *, anchor_code: str, count: int):
        start = _test_listing_anchor_code_start(self.rows, anchor_code)
        return _test_listing_index_window_payload(self.rows, start, count, self.api_calls_by_row_id), {}

    def navigation_payload(self):
        return _test_listing_navigation_payload(
            self.project_name,
            self.rows,
            self.api_calls_by_row_id,
            app_slot_analysis=self.app_slot_analysis,
            type_flow_analysis=self.type_flow_analysis,
        ), {}

    def analysis_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        self.analysis_calls += 1
        return {"sections": []}, {}


def _seed_c_listing_artifact(
    monkeypatch: pytest.MonkeyPatch,
    project_name: str,
    artifact: object,
    *,
    cache_key: str = "cache",
) -> None:
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._COMMAND_AVAILABILITY_CACHE.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        project_name,
        artifact,
        cache_key=cache_key,
    )
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda requested: cache_key)


def _row_locator(
    row: ListingRow | Mapping[str, object],
    *,
    target_id: str = "bloodwych",
    projection_hash: str = "cache",
) -> dict[str, object]:
    if isinstance(row, ListingRow):
        row_key = row.stable_key or row.row_id
        section_index = row.section_index
        start_offset = row.start_offset
        end_offset = row.end_offset
        kind = row.kind
        storage_address = row.addr
        runtime_address = None
    else:
        row_key = str(row.get("row_key") or row.get("stable_key") or row.get("row_id") or "")
        section_index = row.get("section_index")
        start_offset = row.get("start_offset")
        end_offset = row.get("end_offset")
        kind = str(row.get("kind") or "")
        storage_address = row.get("storage_address", row.get("addr"))
        runtime_address = row.get("runtime_address")
    return {
        "target_id": target_id,
        "projection_hash": projection_hash,
        "row_key": row_key,
        "section_index": section_index,
        "start_offset": start_offset,
        "end_offset": end_offset,
        "kind": kind,
        "storage_address": storage_address,
        "runtime_address": runtime_address,
    }


def _row_command_context(row: ListingRow | Mapping[str, object]) -> dict[str, object]:
    return {"kind": "row", "locator": _row_locator(row)}


def _element_command_context(row: ListingRow | Mapping[str, object], element_id: str) -> dict[str, object]:
    return {"kind": "element", "locator": _row_locator(row), "element_id": element_id}


def _range_command_context(rows: Sequence[ListingRow | Mapping[str, object]]) -> dict[str, object]:
    return {"kind": "range", "locators": [_row_locator(row) for row in rows]}


def _row_command_query(row: ListingRow | Mapping[str, object]) -> dict[str, list[str]]:
    return {"context": ["row"], "locator": [json.dumps(_row_locator(row))]}


def _element_command_query(row: ListingRow | Mapping[str, object], element_id: str) -> dict[str, list[str]]:
    return {"context": ["element"], "locator": [json.dumps(_row_locator(row))], "element_id": [element_id]}


def _range_command_query(rows: Sequence[ListingRow | Mapping[str, object]]) -> dict[str, list[str]]:
    return {"context": ["range"], "locators": [json.dumps([_row_locator(row) for row in rows])]}


def _test_listing_row_code(row: ListingRow) -> str:
    if row.label:
        return row.label
    if row.opcode_or_directive:
        return " ".join(part for part in (row.opcode_or_directive, row.operand_text) if part).strip()
    return row.text.strip()


def _test_empty_navigation_groups() -> dict[str, list[dict[str, object]]]:
    return {
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


def _test_app_slot_region_navigation_entry(region: dict[str, object]) -> dict[str, object]:
    offset = cast(int, region.get("offset", 0))
    end = cast(int, region.get("end", offset))
    struct_name = cast(str, region.get("struct_name") or "")
    symbol = cast(str, region.get("symbol") or "")
    evidence = cast(list[dict[str, object]], region.get("evidence", []))
    first_evidence = evidence[0] if evidence else {}
    entry: dict[str, object] = {
        "summary": f"{symbol}: {struct_name} ${offset:04X}-${end:04X}",
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
    for key in ("row_index", "addr", "hunk_index", "stable_key"):
        if key in first_evidence:
            entry[key] = first_evidence[key]
    return entry


def _test_app_slot_gap_navigation_entry(gap: dict[str, object]) -> dict[str, object]:
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


def _test_app_slot_field_gap_navigation_entry(gap: dict[str, object]) -> dict[str, object]:
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


def _test_app_slot_suggestion_navigation_entry(suggestion: dict[str, object]) -> dict[str, object]:
    metadata = suggestion.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    evidence = cast(list[dict[str, object]], suggestion.get("evidence", []))
    first_evidence = evidence[0] if evidence else {}
    offset = cast(int, metadata.get("offset", 0))
    size = cast(int, metadata.get("size", 0))
    struct_name = cast(str, metadata.get("struct_name") or "")
    symbol = cast(str, metadata.get("symbol") or "")
    entry: dict[str, object] = {
        "summary": cast(str, suggestion.get("summary") or f"Suggest {symbol}: {struct_name} ${offset:04X}"),
        "match_text": symbol,
        "symbol": symbol,
        "offset": offset,
        "size": size,
        "struct_name": struct_name,
        "action": suggestion.get("action"),
        "confidence": suggestion.get("confidence"),
        "metadata": metadata,
    }
    for key in ("row_index", "addr", "hunk_index", "stable_key"):
        if key in first_evidence:
            entry[key] = first_evidence[key]
    return entry


def _test_app_slot_api_arg_navigation_entry(arg: dict[str, object]) -> dict[str, object]:
    offset = cast(int, arg.get("displacement", 0))
    symbol = cast(str, arg.get("symbol") or "")
    function_name = cast(str, arg.get("function") or "")
    input_name = cast(str, arg.get("input_name") or "")
    register = cast(str, arg.get("register") or "")
    reason = cast(str, arg.get("reason") or "untyped")
    return {
        "summary": f"{symbol} -> {function_name} {input_name} {register} ({reason})",
        "match_text": symbol,
        "symbol": symbol,
        "offset": offset,
        "displacement": offset,
        "function": function_name,
        "input_name": input_name,
        "register": register,
        "reason": reason,
        "type_name": arg.get("type_name"),
        **{key: arg[key] for key in ("row_index", "addr", "hunk_index", "source_row_index", "source_flow_row_index", "stable_key", "source_stable_key") if key in arg},
    }


def _test_navigation_entry(row: ListingRow, row_index: int, summary: str | None = None) -> dict[str, object]:
    assert row.addr is not None
    entry: dict[str, object] = {
        "addr": row.addr,
        "row_index": row_index,
        "summary": summary or _test_listing_row_code(row),
        "match_text": _test_listing_row_code(row),
        "stable_key": row.stable_key,
    }
    if row.section_index is not None:
        entry["section_index"] = row.section_index
    if isinstance(row.source_context, BlockRowContext):
        entry["hunk_index"] = row.source_context.hunk_index
    return entry


def _test_signed_hex_offset(value: int) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):04X}"


def _test_unresolved_typed_access_summary(access: PlatformUnresolvedTypedAccess) -> str:
    root = access.root_struct_name or "typed base"
    displacement = _test_signed_hex_offset(access.displacement)
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


def _test_api_call_is_navigation_target(
    api_calls: dict[tuple[int, int], dict[str, object]],
    hunk_index: int,
    offset: int,
    api_call: dict[str, object],
) -> bool:
    if api_call.get("note_kind") == 3:
        return False
    if api_call.get("note_kind") == 1:
        for probe_offset in range(max(0, offset - 8), offset):
            candidate = api_calls.get((hunk_index, probe_offset))
            if (
                candidate is not None
                and candidate.get("note_kind") == 0
                and candidate.get("library") == api_call.get("library")
                and candidate.get("function") == api_call.get("function")
            ):
                return False
    return True


def _test_listing_navigation_payload(
    project_name: str,
    rows: list[ListingRow],
    api_calls_by_row_id: dict[str, dict[str, object]] | None = None,
    *,
    app_slot_analysis: dict[str, object] | None = None,
    type_flow_analysis: dict[str, object] | None = None,
) -> dict[str, object]:
    groups = _test_empty_navigation_groups()
    label_entries: dict[str, dict[str, object]] = {}
    api_calls_by_row_id = api_calls_by_row_id or {}
    api_calls: dict[tuple[int, int], dict[str, object]] = {}
    for row in rows:
        api_call = api_calls_by_row_id.get(row.row_id)
        if api_call is None or not isinstance(row.source_context, BlockRowContext) or row.addr is None:
            continue
        api_calls[(row.source_context.hunk_index, row.addr)] = api_call
    repro_report = disasm_server._active_reproduction_report(project_name)
    if repro_report is not None:
        groups["repro-issues"] = disasm_server.reproduction_navigation_entries(repro_report)
    if app_slot_analysis is None:
        app_slot_analysis = {
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
        }
    for row_index, row in enumerate(rows):
        if row.addr is None:
            continue
        code = _test_listing_row_code(row)
        if row.label or code.endswith(":"):
            symbol = (row.label or code).rstrip(":")
            entry = _test_navigation_entry(row, row_index, f"{symbol}:")
            entry.update({"symbol": symbol, "ref_count": 1, "access_counts": {"definition": 1}, "refs": []})
            cast(list[dict[str, object]], entry["refs"]).append(
                {**_test_navigation_entry(row, row_index, f"{symbol}:"), "symbol": symbol, "access": "definition"}
            )
            label_entries[symbol] = entry
        if row.typed_accesses or (row.kind not in {"instruction", "label"} and (row.comment_text or row.structured_data)):
            summary = row.comment_text or row.kind
            if row.typed_accesses:
                access = row.typed_accesses[0]
                summary = ".".join(part for part in (access.owner_struct_name or access.root_struct_name, access.field_expr or access.field_name) if part)
            groups["typed-data"].append(_test_navigation_entry(row, row_index, summary))
        for access in row.unresolved_typed_accesses:
            entry = _test_navigation_entry(row, row_index, _test_unresolved_typed_access_summary(access))
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
                }
            )
            groups["typed-gaps"].append(entry)
        if any(operand.segment_addr is not None for operand in row.operand_parts):
            groups["relocations"].append(_test_navigation_entry(row, row_index))
        if isinstance(row.source_context, BlockRowContext):
            api_call = api_calls.get((row.source_context.hunk_index, row.addr))
            if (
                api_call is not None
                and row.kind == "instruction"
                and _test_api_call_is_navigation_target(api_calls, row.source_context.hunk_index, row.addr, api_call)
            ):
                summary = f"{api_call.get('function', '')} ({api_call.get('library', '')})".strip()
                groups["api-calls"].append(_test_navigation_entry(row, row_index, summary))
        for ref in row.app_slot_refs:
            slot = next((entry for entry in groups["app-slots"] if entry.get("symbol") == ref.symbol), None)
            if slot is None:
                slot = {
                    "symbol": ref.symbol,
                    "summary": ref.symbol,
                    "match_text": ref.symbol,
                    "displacement": ref.displacement,
                    "ref_count": 0,
                    "access_counts": {},
                    "refs": [],
                }
                groups["app-slots"].append(slot)
            refs = cast(list[dict[str, object]], slot["refs"])
            refs.append({**_test_navigation_entry(row, row_index), "symbol": ref.symbol, "access": ref.access})
            slot["ref_count"] = cast(int, slot["ref_count"]) + 1
            access_counts = cast(dict[str, int], slot["access_counts"])
            access_counts[ref.access] = access_counts.get(ref.access, 0) + 1
        if row.comment_text:
            groups["comments"].append(_test_navigation_entry(row, row_index, row.comment_text))
    for row_index, row in enumerate(rows):
        if row.addr is None:
            continue
        for operand in row.operand_parts:
            symbol = operand.metadata.symbol if isinstance(operand.metadata, SymbolOperandMetadata) else None
            if not symbol or symbol not in label_entries:
                continue
            label_entry = label_entries[symbol]
            refs = cast(list[dict[str, object]], label_entry["refs"])
            refs.append({**_test_navigation_entry(row, row_index), "symbol": symbol, "access": "reference"})
            label_entry["ref_count"] = cast(int, label_entry["ref_count"]) + 1
            access_counts = cast(dict[str, int], label_entry["access_counts"])
            access_counts["reference"] = access_counts.get("reference", 0) + 1
    for label_entry in label_entries.values():
        cast(list[dict[str, object]], label_entry["refs"]).sort(
            key=lambda entry: cast(int, entry.get("row_index", -1))
        )
    app_slot_summaries = {
        cast(str, slot["symbol"]): slot
        for slot in cast(list[dict[str, object]], app_slot_analysis.get("slots", []))
        if isinstance(slot.get("symbol"), str)
    }
    for slot_entry in groups["app-slots"]:
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
    groups["labels"] = sorted(label_entries.values(), key=lambda entry: cast(int, entry.get("row_index", -1)))
    groups["app-slot-regions"] = [
        _test_app_slot_region_navigation_entry(region)
        for region in cast(list[dict[str, object]], app_slot_analysis.get("regions", []))
        if region.get("source") == "platform_api_arg"
    ]
    groups["app-slot-gaps"] = [
        _test_app_slot_gap_navigation_entry(gap)
        for gap in cast(list[dict[str, object]], app_slot_analysis.get("gaps", []))
    ]
    groups["app-slot-field-gaps"] = [
        _test_app_slot_field_gap_navigation_entry(gap)
        for gap in cast(list[dict[str, object]], app_slot_analysis.get("field_gaps", []))
    ]
    groups["app-slot-suggestions"] = [
        _test_app_slot_suggestion_navigation_entry(suggestion)
        for suggestion in cast(list[dict[str, object]], app_slot_analysis.get("suggestions", []))
    ]
    groups["app-slot-api-args"] = [
        _test_app_slot_api_arg_navigation_entry(arg)
        for arg in cast(list[dict[str, object]], app_slot_analysis.get("untyped_api_args", []))
    ]
    return {
        "analysis_generation": "full",
        "total_rows": len(rows),
        "groups": groups,
        "app_slot_analysis": app_slot_analysis,
        "type_flow_analysis": type_flow_analysis or {},
    }


def _test_listing_anchor_code_start(rows: list[ListingRow], anchor_code: str) -> int:
    wanted = anchor_code.strip()
    if not wanted:
        return 0
    for index, row in enumerate(rows):
        if _test_listing_row_code(row).strip() == wanted:
            return index
    return 0


def _test_listing_addr_window_payload(
    rows: list[ListingRow],
    addr: int | None,
    *,
    before: int = 80,
    after: int = 160,
    api_calls_by_row_id: dict[str, dict[str, object]] | None = None,
) -> ListingWindowPayload:
    anchor_index = 0
    if addr is not None:
        anchor_index = max(0, len(rows) - 1)
        for index, row in enumerate(rows):
            if row.addr is not None and row.addr >= addr:
                anchor_index = index
                break
    start = max(0, anchor_index - before)
    end = min(len(rows), anchor_index + after + 1)
    return {
        "anchor_addr": addr,
        "start": start,
        "end": end,
        "has_more_before": start > 0,
        "has_more_after": end < len(rows),
        "total_rows": len(rows),
        "rows": _test_serialize_rows(rows[start:end], api_calls_by_row_id),
    }


def _test_listing_index_window_payload(
    rows: list[ListingRow],
    start: int,
    count: int,
    api_calls_by_row_id: dict[str, dict[str, object]] | None = None,
) -> ListingWindowPayload:
    safe_count = max(0, count)
    if safe_count == 0 or not rows:
        safe_start = 0
    else:
        max_start = max(0, len(rows) - safe_count)
        safe_start = max(0, min(start, max_start))
    end = min(len(rows), safe_start + safe_count)
    return {
        "anchor_addr": rows[safe_start].addr if safe_start < len(rows) else None,
        "start": safe_start,
        "end": end,
        "has_more_before": safe_start > 0,
        "has_more_after": end < len(rows),
        "total_rows": len(rows),
        "rows": _test_serialize_rows(rows[safe_start:end], api_calls_by_row_id),
    }


def _test_serialize_rows(
    rows: list[ListingRow],
    api_calls_by_row_id: dict[str, dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    api_calls_by_row_id = api_calls_by_row_id or {}
    serialized_rows: list[dict[str, object]] = []
    for row in rows:
        serialized = dict(serialize_row(row))
        api_call = api_calls_by_row_id.get(row.row_id)
        if api_call is not None:
            serialized["api_call"] = api_call
        serialized_rows.append(serialized)
    return serialized_rows


def test_listing_anchor_code_start_matches_non_address_row() -> None:
    rows = [
        ListingRow(row_id="include", kind="directive", text='INCLUDE "exec/io.i"\n'),
        ListingRow(row_id="section", kind="directive", text="    SECTION section,code\n"),
        ListingRow(
            row_id="code",
            kind="instruction",
            text="bra.b h0_0036\n",
            addr=0,
            opcode_or_directive="bra.b",
            operand_text="h0_0036",
        ),
    ]

    assert _test_listing_anchor_code_start(rows, "SECTION section,code") == 1


def test_route_listing_anchor_code_returns_window_at_non_address_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(row_id="include", kind="directive", text='INCLUDE "exec/io.i"\n'),
        ListingRow(row_id="section", kind="directive", text="    SECTION section,code\n"),
        ListingRow(
            row_id="code",
            kind="instruction",
            text="bra.b h0_0036\n",
            addr=0,
            opcode_or_directive="bra.b",
            operand_text="h0_0036",
        ),
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"anchor_code": ["SECTION section,code"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    window_rows = cast(list[dict[str, object]], data["rows"])

    assert data["start"] == 1
    assert window_rows[0]["text"].strip() == "SECTION section,code"


def test_route_listing_reuses_cached_analysis_review_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [ListingRow(row_id="r0", kind="instruction", text="rts\n", addr=0)]
    artifact = _RowsCListingArtifact(rows)
    _seed_c_listing_artifact(monkeypatch, "bloodwych", artifact)
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    for _ in range(2):
        disasm_server.route_request(
            "GET",
            "/api/projects/bloodwych/listing",
            {"start": ["0"], "count": ["1"]},
        )

    assert artifact.analysis_calls == 1


def test_route_listing_section_offset_uses_hunk_local_row(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id="h0", kind="instruction", text="rts\n", addr=0, section_index=0, start_offset=0, end_offset=2),
        ListingRow(
            row_id="h1",
            kind="instruction",
            text="moveq.l #0,d0\n",
            addr=0x14C,
            section_index=1,
            start_offset=0x14C,
            end_offset=0x14E,
        ),
        ListingRow(row_id="gap", kind="directive", text="    SECTION section_2,code\n"),
        ListingRow(
            row_id="h2-before",
            kind="instruction",
            text="nop\n",
            addr=0x148,
            section_index=2,
            start_offset=0x148,
            end_offset=0x14A,
        ),
        ListingRow(
            row_id="h2-target",
            kind="instruction",
            text="jmp $0040(a2)\n",
            addr=0x14C,
            section_index=2,
            start_offset=0x14C,
            end_offset=0x150,
        ),
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"section_index": ["2"], "source_offset": [str(0x14C)], "before": ["1"], "after": ["1"]},
    )
    data = cast(dict[str, object], payload["data"])
    returned_rows = cast(list[dict[str, object]], data["rows"])

    assert "h1" not in [row["row_key"] for row in returned_rows]
    assert returned_rows[-1]["row_key"] == "h2-target"
    assert returned_rows[-1]["section_index"] == 2


def test_route_listing_rows_use_locator_contract_without_old_identity_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            stable_key="s0:00000004:instruction:1",
            kind="instruction",
            text="rts\n",
            addr=4,
            section_index=0,
            start_offset=4,
            end_offset=6,
        )
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"start": ["0"], "count": ["1"]},
    )
    data = cast(dict[str, object], payload["data"])
    row = cast(list[dict[str, object]], data["rows"])[0]

    assert data["target_id"] == "bloodwych"
    assert isinstance(data["projection_hash"], str)
    assert row["target_id"] == "bloodwych"
    assert row["projection_hash"] == data["projection_hash"]
    assert row["row_key"] == "s0:00000004:instruction:1"
    assert row["locator"] == {
        "target_id": "bloodwych",
        "projection_hash": data["projection_hash"],
        "row_key": "s0:00000004:instruction:1",
        "section_index": 0,
        "start_offset": 4,
        "end_offset": 6,
        "kind": "instruction",
        "storage_address": 4,
        "runtime_address": None,
    }
    assert "row_id" not in row
    assert "stable_key" not in row


def _disk_manifest_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "disk_id": "demo_disk",
        "source_path": "bin/demo.adf",
        "source_sha256": "deadbeef",
        "bootblock_target_name": "amiga_disk_demo_disk__amiga_raw_bootblock",
        "bootblock_target_path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock",
        "analysis": {
            "disk_info": {
                "path": "demo.adf",
                "size": 901120,
                "variant": "DD",
                "total_sectors": 1760,
                "sectors_per_track": 11,
                "is_dos": True,
            },
            "boot_block": {
                "magic_ascii": "DOS",
                "is_dos": True,
                "flags_byte": 1,
                "fs_type": "FFS",
                "fs_description": "DOS\\1 - Fast File System",
                "checksum": "0x00000000",
                "checksum_valid": True,
                "rootblock_ptr": 880,
                "bootcode_size": 1012,
                "bootcode_has_code": False,
                "bootcode_entropy": 0.0,
            },
        },
        "imported_targets": [
            {
                "target_name": "amiga_disk_demo_disk__amiga_hunk_run_12345678",
                "target_path": "targets/amiga_disk_demo_disk/targets/amiga_hunk_run_12345678",
                "entry_path": "c/Run",
                "binary_path": "bin/demo.adf::c/Run",
                "target_type": "program",
            }
        ],
    }


def test_route_projects_returns_project_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [_binary_project("bloodwych", ready=True)])

    payload = disasm_server.route_request("GET", "/api/projects", {})

    assert payload["ok"] is True
    assert payload["data"] == [_binary_project("bloodwych", ready=True).to_dict()]


def test_route_app_contract_returns_web_version() -> None:
    payload = disasm_server.route_request("GET", "/api/app-contract", {})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["web_app_contract_version"] == disasm_server.WEB_APP_CONTRACT_VERSION


def test_installed_disasm_server_serves_web_static_assets() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    port = _free_tcp_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "amiga_reversing.tools.disasm_server",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0,
        start_new_session=os.name != "nt",
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 8
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=1)
                raise AssertionError(f"server exited early\nstdout:\n{stdout}\nstderr:\n{stderr}")
            try:
                body, content_type = _read_http_bytes(f"{base_url}/")
                break
            except Exception as exc:
                last_error = exc
                time.sleep(0.1)
        else:
            raise AssertionError(f"server did not serve /: {last_error}")

        assert b"<html" in body.lower()
        assert content_type.startswith("text/html")

        app_js, app_content_type = _read_http_bytes(f"{base_url}/app.js")
        styles_css, styles_content_type = _read_http_bytes(f"{base_url}/styles.css")

        assert b"function" in app_js
        assert app_content_type.startswith("application/javascript")
        assert b"body {" in styles_css
        assert styles_content_type.startswith("text/css")

        contract_body, contract_content_type = _read_http_bytes_with_headers(
            f"{base_url}/api/app-contract",
            {"Origin": f"http://localhost:{port}"},
        )
        assert b'"web_app_contract_version"' in contract_body
        assert contract_content_type.startswith("application/json")

        api_body, api_content_type = _read_http_bytes_with_headers(
            f"{base_url}/api/projects",
            {
                "Origin": f"http://localhost:{port}",
                "X-Amiga-Web-App-Contract": str(disasm_server.WEB_APP_CONTRACT_VERSION),
            },
        )
        assert b'"ok":true' in api_body.replace(b" ", b"")
        assert b'"web_app_contract_version"' in api_body
        assert api_content_type.startswith("application/json")

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _read_http_bytes_with_headers(
                f"{base_url}/api/projects",
                {"Origin": f"http://localhost:{port}"},
            )
        assert exc_info.value.code == 409

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            _read_http_bytes_with_headers(
                f"{base_url}/api/projects",
                {"Origin": "https://example.invalid"},
            )
        assert exc_info.value.code == 403
    finally:
        _kill_process_tree(process)


def test_route_create_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "create_project",
        lambda project_id: _binary_project(project_id, ready=False),
    )

    payload = disasm_server.route_request("POST", "/api/projects", {}, {"id": "demo"})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["id"] == "demo"


def test_route_project_returns_project_and_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych", {})
    data = cast(dict[str, object], payload["data"])
    project = cast(dict[str, object], data["project"])

    assert payload["ok"] is True
    assert project["name"] == "bloodwych"
    assert "session" not in data
    assert "disk_manifest" not in data


def test_route_project_overlays_cached_analysis_review_state(monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _FakeCListingArtifact()
    _seed_c_listing_artifact(monkeypatch, "bloodwych", artifact)
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "_current_reproduction_payload",
        lambda project_name: {"status": "not_ready"},
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych", {})
    data = cast(dict[str, object], payload["data"])
    project = cast(dict[str, object], data["project"])
    review_items = cast(list[dict[str, object]], project["review_items"])

    assert project["review_state"] == "needs_review"
    assert review_items[0]["kind"] == "unreconciled_data_range"
    action_ids = [action["action_id"] for action in cast(list[dict[str, object]], review_items[0]["catalog_actions"])]
    assert {action_id.removeprefix("review.seed.data.") for action_id in action_ids if action_id.startswith("review.seed.data.")} >= (
        _FULL_DATA_ROLE_IDS | {"raw"}
    )
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_returns_review_item_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    project = replace(
        _binary_project("bloodwych", ready=True),
        review_state=ReviewState.NEEDS_REVIEW,
        review_items=(
            {
                "kind": ReviewItemKind.UNRECONCILED_DATA_RANGE,
                "item_id": "unreconciled:h0:00000004-00000008",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "hunk": 0,
                "start": 4,
                "end": 8,
                "message": "Known data gap",
            },
        ),
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        {"context": ["review-item"], "item_id": ["unreconciled:h0:00000004-00000008"]},
    )
    data = cast(dict[str, object], payload["data"])
    actions = cast(list[dict[str, object]], data["commands"])

    assert data["context"] == {
        "kind": "review_item",
        "item_id": "unreconciled:h0:00000004-00000008",
    }
    assert actions[0]["action_id"] == "review.navigate"
    seed_action = next(action for action in actions if action["command_id"] == "review.seed.data.string")
    named_seed_action = next(action for action in actions if action["command_id"] == "review.seed.data.named")
    assert {
        str(action["action_id"]).removeprefix("review.seed.data.")
        for action in actions
        if str(action["action_id"]).removeprefix("review.seed.data.") in _FULL_DATA_ROLE_IDS
    } == _FULL_DATA_ROLE_IDS
    assert named_seed_action["parameters"] == {"seed_kind": "data", "data_role": "raw", "unit": "byte"}
    assert named_seed_action["parameter_schema"]["required"] == ["name"]
    assert named_seed_action["interaction_schema"]["type"] == "text"
    assert named_seed_action["interaction_schema"]["primary_field"] == "name"
    assert seed_action["effect"] == "manual_mutation"
    assert seed_action["target_context"] == {
        "kind": "review_item",
        "item_id": "unreconciled:h0:00000004-00000008",
    }
    assert seed_action["parameters"] == {"seed_kind": "data", "data_role": "string", "unit": "byte", "encoding": "ascii"}
    assert seed_action["typed_error"]["codes"] == [
        "missing_locator",
        "stale_locator",
        "ambiguous_locator",
        "non_mutable_command",
        "invalid_command_context",
    ]


def test_route_manual_action_catalog_returns_manual_seed_conflict_remove_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = replace(
        _binary_project("bloodwych", ready=True),
        review_state=ReviewState.BLOCKED,
        review_items=(
            {
                "kind": ReviewItemKind.MANUAL_SEED_CONFLICT,
                "item_id": "manual_seed_conflict:data-as-code:entry",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "seed_ids": ["data-as-code"],
                "hunk": 0,
                "start": 0,
                "end": 2,
                "message": "Required manual seed data-as-code conflicts",
            },
        ),
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        {"context": ["review-item"], "item_id": ["manual_seed_conflict:data-as-code:entry"]},
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])
    remove_action = next(action for action in actions if action["action_id"] == "review.seed.remove")

    assert remove_action["parameters"] == {"seed_id": "data-as-code"}
    assert remove_action["parameter_schema"]["properties"]["seed_id"]["enum"] == ["data-as-code"]
    assert remove_action["interaction_schema"]["type"] == "form"


def test_route_manual_action_catalog_returns_target_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        {"context": ["target"]},
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])

    palette_action = next(action for action in actions if action["command_id"] == "target.open_command_palette")
    assert palette_action["effect"] == "navigation"
    assert palette_action["target_context"] == {"kind": "target"}
    assert palette_action["parameter_schema"] == {"type": "object", "properties": {}, "required": []}
    assert palette_action["default_key_binding"] == "p"
    profile_action = next(action for action in actions if action["action_id"] == "target.reproduction_profile")
    assert profile_action["category"] == "target_tooling"
    assert profile_action["appends_to_manual_action_log"] is False
    assert profile_action["action"] == "set_reproduction_profile"
    assert profile_action["interaction_schema"]["type"] == "choice_grid"
    assert profile_action["parameter_schema"]["properties"]["profile_id"]["enum"] == [
        "exact-framework",
        "source-vasm",
        "source-devpac",
        "content-semantic",
    ]
    export_action = next(action for action in actions if action["action_id"] == "target.source_export")
    assert export_action["category"] == "target_tooling"
    assert export_action["appends_to_manual_action_log"] is False
    assert export_action["action"] == "export_source"
    assert export_action["parameter_schema"]["properties"]["assembler_profile"]["enum"] == ["vasm", "devpac"]
    equate_action = next(action for action in actions if action["action_id"] == "target.equate.add")
    assert equate_action["category"] == "target_metadata"
    assert equate_action["appends_to_manual_action_log"] is True
    assert equate_action["action"] == "create_manual_target_equate"
    assert equate_action["parameter_schema"]["required"] == ["name", "value"]
    equate_repr_action = next(action for action in actions if action["action_id"] == "target.equate.represent")
    assert equate_repr_action["action"] == "create_manual_target_equate"
    assert equate_repr_action["parameter_schema"]["properties"]["value_representation"]["enum"] == [
        "hex",
        "decimal",
        "binary",
        "character",
        "symbol",
    ]
    equate_rename_action = next(action for action in actions if action["action_id"] == "target.equate.rename")
    assert equate_rename_action["action"] == "rename_manual_target_equate"
    assert equate_rename_action["parameter_schema"]["required"] == ["previous_name", "name"]
    equate_remove_action = next(action for action in actions if action["action_id"] == "target.equate.remove")
    assert equate_remove_action["action"] == "remove_manual_target_equate"
    assert equate_remove_action["parameter_schema"]["required"] == ["name"]
    execution_view_action = next(action for action in actions if action["action_id"] == "target.execution_view.add")
    assert execution_view_action["category"] == "target_metadata"
    assert execution_view_action["appends_to_manual_action_log"] is True
    assert execution_view_action["action"] == "create_manual_execution_view"
    assert execution_view_action["parameter_schema"]["required"] == [
        "source_start",
        "source_end",
        "base_addr",
        "name",
    ]
    assert execution_view_action["interaction_schema"]["type"] == "form"
    execution_view_edit_action = next(action for action in actions if action["action_id"] == "target.execution_view.edit")
    assert execution_view_edit_action["category"] == "target_metadata"
    assert execution_view_edit_action["appends_to_manual_action_log"] is True
    assert execution_view_edit_action["action"] == "create_manual_execution_view"
    assert execution_view_edit_action["parameter_schema"]["required"] == [
        "source_start",
        "source_end",
        "base_addr",
        "name",
    ]
    execution_view_remove_action = next(
        action for action in actions if action["action_id"] == "target.execution_view.remove"
    )
    assert execution_view_remove_action["category"] == "target_metadata"
    assert execution_view_remove_action["appends_to_manual_action_log"] is True
    assert execution_view_remove_action["action"] == "remove_manual_execution_view"
    assert execution_view_remove_action["parameter_schema"]["required"] == [
        "source_start",
        "source_end",
        "base_addr",
    ]
    rsset_region_action = next(action for action in actions if action["action_id"] == "target.rsset_region.add")
    assert rsset_region_action["category"] == "target_metadata"
    assert rsset_region_action["appends_to_manual_action_log"] is True
    assert rsset_region_action["action"] == "create_manual_rsset_layout_region"
    assert rsset_region_action["parameter_schema"]["required"] == ["offset", "symbol"]
    rsset_region_edit_action = next(action for action in actions if action["action_id"] == "target.rsset_region.edit")
    assert rsset_region_edit_action["action"] == "create_manual_rsset_layout_region"
    assert rsset_region_edit_action["parameter_schema"]["required"] == ["offset", "symbol"]
    rsset_region_rename_action = next(action for action in actions if action["action_id"] == "target.rsset_region.rename")
    assert rsset_region_rename_action["action"] == "create_manual_rsset_layout_region"
    assert rsset_region_rename_action["parameter_schema"]["required"] == ["offset", "symbol"]
    rsset_region_remove_action = next(action for action in actions if action["action_id"] == "target.rsset_region.remove")
    assert rsset_region_remove_action["category"] == "target_metadata"
    assert rsset_region_remove_action["appends_to_manual_action_log"] is True
    assert rsset_region_remove_action["action"] == "remove_manual_rsset_layout_region"
    assert rsset_region_remove_action["parameter_schema"]["required"] == ["offset"]
    assert any(action["action_id"] == "navigation.history_back" for action in actions)


def test_route_source_export_returns_selected_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    calls: list[tuple[str, str]] = []

    def fake_source_export_payload(project_name: str, *, assembler_profile: str, project_root=None) -> dict[str, object]:
        calls.append((project_name, assembler_profile))
        return {"status": "ok", "filename": "bloodwych-devpac.s", "source_text": "; source\n"}

    monkeypatch.setattr(disasm_server, "source_export_payload", fake_source_export_payload)

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/source-export",
        {"assembler_profile": ["devpac"]},
    )

    assert payload["ok"] is True
    assert cast(dict[str, object], payload["data"])["filename"] == "bloodwych-devpac.s"
    assert calls == [("bloodwych", "devpac")]


def test_route_source_export_returns_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "source_export_payload",
        lambda project_name, *, assembler_profile, project_root=None: {
            "status": "refused",
            "message": "facts_v2 asm source refused",
            "listing_profile": {"facts_v2": {"asm_source_refused": True}},
        },
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/source-export", {})

    data = cast(dict[str, object], payload["data"])
    assert data["status"] == "refused"
    assert data["message"] == "facts_v2 asm source refused"


def test_route_manual_action_catalog_returns_label_fix_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    project = replace(
        _binary_project("bloodwych", ready=True),
        review_state=ReviewState.BLOCKED,
        review_items=(
            {
                "kind": ReviewItemKind.LABEL_SCOPE_CONFLICT,
                "item_id": "label_scope_conflict:l1:missing-owner",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "label_ids": ["l1"],
                "hunk": 0,
                "start": 4,
                "end": 5,
                "message": "Local manual label l1 has no explicit owner id",
            },
        ),
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        {"context": ["review-item"], "item_id": ["label_scope_conflict:l1:missing-owner"]},
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])

    assert any(action["action_id"] == "review.label.rename" for action in actions)
    change_scope = next(action for action in actions if action["action_id"] == "review.label.change_scope")
    assert change_scope["action"] == "change_label_scope"
    assert change_scope["parameters"] == {"label_id": "l1"}
    assert change_scope["parameter_schema"] == {
        "type": "object",
        "properties": {
            "label_id": {"type": "string"},
            "scope": {"type": "string", "enum": ["global", "local"]},
            "owner_id": {"type": "string"},
        },
        "required": ["scope"],
    }
    assert any(action["action_id"] == "review.label.remove" for action in actions)


def test_route_manual_action_catalog_returns_review_note_item_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    project = replace(
        _binary_project("bloodwych", ready=True),
        review_state=ReviewState.NEEDS_REVIEW,
        review_items=(
            {
                "kind": ReviewItemKind.REVIEW_NOTE,
                "item_id": "review_note:h0:$00000004-$00000006",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "note_id": "note-1",
                "hunk": 0,
                "start": 4,
                "end": 6,
                "message": "Check branch",
            },
        ),
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        {"context": ["review-item"], "item_id": ["review_note:h0:$00000004-$00000006"]},
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])

    assert [action["action_id"] for action in actions] == [
        "review.navigate",
        "review_note.edit",
        "review_note.clear",
    ]
    assert actions[1]["parameters"] == {"note_id": "note-1"}


def test_route_manual_action_catalog_execute_edits_and_clears_review_note(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = replace(
        _binary_project("bloodwych", ready=True),
        review_state=ReviewState.NEEDS_REVIEW,
        review_items=(
            {
                "kind": ReviewItemKind.REVIEW_NOTE,
                "item_id": "review_note:h0:$00000004-$00000006",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "note_id": "note-1",
                "hunk": 0,
                "start": 4,
                "end": 6,
                "message": "Check branch",
            },
        ),
    )
    appended_actions: list[dict[str, object]] = []
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="copy_loop:\n",
            addr=0x1001E,
            runtime_address=0x1001E,
            section_index=0,
            start_offset=0x1E,
            end_offset=0x1E,
            label="copy_loop",
            stable_key="s0:0000001E:label:245",
        )
    ]

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    edit_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "review_note.edit",
            "context": {"kind": "review_item", "item_id": "review_note:h0:$00000004-$00000006"},
            "parameters": {"title": "Updated", "tracking": "note_only"},
        },
    )
    clear_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "review_note.clear",
            "context": {"kind": "review_item", "item_id": "review_note:h0:$00000004-$00000006"},
        },
    )

    assert appended_actions == [
        {"kind": "edit_review_note", "payload": {"note_id": "note-1", "title": "Updated", "tracking": "note_only"}},
        {"kind": "clear_review_note", "payload": {"note_id": "note-1"}},
    ]
    edit_effect = cast(list[dict[str, object]], cast(dict[str, object], edit_payload["data"])["application"]["local_effects"])[0]
    clear_effect = cast(list[dict[str, object]], cast(dict[str, object], clear_payload["data"])["application"]["local_effects"])[0]
    assert edit_effect["kind"] == "review_note_edit"
    assert clear_effect["kind"] == "review_note_clear"


def test_route_manual_action_catalog_returns_row_and_element_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [ListingRow(row_id="r0", kind="data", text="dc.b $41\n", addr=0, stable_key="row-0", bytes=b"A")]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    row_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _row_command_query(rows[0]),
    )
    row_actions = cast(list[dict[str, object]], cast(dict[str, object], row_payload["data"])["commands"])
    element_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:data_literal:0"),
    )
    element_actions = cast(list[dict[str, object]], cast(dict[str, object], element_payload["data"])["commands"])

    assert any(action["action_id"] == "row.seed.data.string" for action in row_actions)
    assert any(action["action_id"] == "row.seed.data.named" for action in row_actions)
    assert any(action["action_id"] == "row.seed.data.word" for action in row_actions)
    assert any(action["action_id"] == "row.seed.data.pointer_table" for action in row_actions)
    assert any(action["action_id"] == "row.data_block.layout.create" for action in row_actions)
    assert any(action["action_id"] == "row.data_block.element.set" for action in row_actions)
    assert any(action["action_id"] == "row.data_block.element.remove" for action in row_actions)
    assert any(action["action_id"] == "row.data_block.element.represent" for action in row_actions)
    assert any(action["action_id"] == "row.data_block.element.interpret_ref" for action in row_actions)
    assert any(action["action_id"] == "row.data_block.element.clear_ref" for action in row_actions)
    assert {
        str(action["action_id"]).removeprefix("row.seed.data.")
        for action in row_actions
        if str(action["action_id"]).removeprefix("row.seed.data.") in _FULL_DATA_ROLE_IDS
    } == _FULL_DATA_ROLE_IDS
    palette_action = next(action for action in row_actions if action["action_id"] == "row.seed.data.palette")
    assert palette_action["parameters"] == {"seed_kind": "data", "data_role": "palette", "unit": "word"}
    named_action = next(action for action in row_actions if action["action_id"] == "row.seed.data.named")
    assert named_action["parameters"] == {"seed_kind": "data", "data_role": "raw", "unit": "byte"}
    assert named_action["parameter_schema"]["required"] == ["name"]
    assert named_action["default_key_binding"] == "F2"
    assert named_action["interaction_schema"]["type"] == "text"
    assert named_action["interaction_schema"]["primary_field"] == "name"
    comment_action = next(action for action in row_actions if action["action_id"] == "comment.edit")
    assert comment_action["default_key_binding"] == ";"
    assert comment_action["interaction_schema"]["type"] == "text"
    assert comment_action["interaction_schema"]["hosts"] == ["palette", "inline"]
    assert comment_action["interaction_schema"]["primary_rank"] == 10
    review_note = next(action for action in row_actions if action["action_id"] == "review_note.add")
    assert review_note["action"] == "add_review_note"
    assert review_note["parameter_schema"]["properties"]["tracking"]["enum"] == ["note_only", "needs_review"]
    representation_choice = next(action for action in element_actions if action["action_id"] == "representation.choose")
    assert representation_choice["default_key_binding"] == "r"
    assert representation_choice["interaction_schema"]["type"] == "choice_grid"
    assert representation_choice["interaction_schema"]["primary_rank"] == 20
    assert representation_choice["interaction_schema"]["options"][0]["value"] == "hex"
    assert any(action["action_id"] == "representation.hex" for action in element_actions)
    element_named = next(action for action in element_actions if action["action_id"] == "element.seed.data.named")
    assert element_named["parameters"] == {"seed_kind": "data", "data_role": "raw", "unit": "byte"}
    assert element_named["parameter_schema"]["required"] == ["name"]
    assert element_named["default_key_binding"] == "F2"
    assert element_named["interaction_schema"]["type"] == "text"
    assert element_named["interaction_schema"]["primary_field"] == "name"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_command_catalog_reports_malformed_locator_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [ListingRow(row_id="r0", kind="instruction", text="rts\n", addr=0, stable_key="row-0")]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    locator = _row_locator(rows[0])
    del locator["row_key"]
    with pytest.raises(disasm_server.CommandContractError) as exc:
        disasm_server.route_request(
            "GET",
            "/api/projects/bloodwych/commands",
            {"context": ["row"], "locator": [json.dumps(locator)]},
        )

    assert exc.value.code == "missing_locator"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_appends_review_note_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="rts\n",
            addr=4,
            section_index=0,
            start_offset=4,
            end_offset=6,
            stable_key="row-0",
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "review_note.add",
            "context": _row_command_context(rows[0]),
            "parameters": {"title": "Check RTS", "body": "Verify return path", "tracking": "needs_review"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    note = cast(dict[str, object], cast(dict[str, object], action["payload"])["note"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "add_review_note"
    assert note["title"] == "Check RTS"
    assert note["body"] == "Verify return path"
    assert note["tracking"] == "needs_review"
    assert note["addr"] == 4
    assert note["end"] == 6
    assert note["row_indexes"] == [0]
    assert application["status"] == "applied"
    assert local_effect["kind"] == "review_note_add"
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


@pytest.mark.parametrize("command_id", ["target.equate.add", "target.equate.edit", "target.equate.represent"])
def test_route_manual_action_catalog_execute_appends_target_equate_action(
    command_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": command_id,
            "context": {"kind": "target"},
            "parameters": {"name": "PLAYER_START_LIVES", "value": 3},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    target_equate = cast(dict[str, object], cast(dict[str, object], action["payload"])["target_equate"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "create_manual_target_equate"
    assert target_equate == {
        "target_equate_id": "catalog-target-equate-PLAYER_START_LIVES",
        "name": "PLAYER_START_LIVES",
        "value": 3,
    }
    assert application["status"] == "applied"
    assert local_effect == {"kind": "target_equate", "target_equate": target_equate}
    assert appended_actions == [action]


@pytest.mark.parametrize(
    ("command_id", "parameters", "action_kind", "local_effect_kind", "expected_equate"),
    [
        (
            "target.equate.rename",
            {"previous_name": "PLAYER_START_LIVES", "name": "PLAYER_INITIAL_LIVES"},
            "rename_manual_target_equate",
            "target_equate",
            {
                "target_equate_id": "catalog-target-equate-PLAYER_START_LIVES",
                "previous_name": "PLAYER_START_LIVES",
                "name": "PLAYER_INITIAL_LIVES",
            },
        ),
        (
            "target.equate.remove",
            {"name": "PLAYER_START_LIVES"},
            "remove_manual_target_equate",
            "target_equate_remove",
            {
                "target_equate_id": "catalog-target-equate-PLAYER_START_LIVES",
                "name": "PLAYER_START_LIVES",
            },
        ),
    ],
)
def test_route_manual_action_catalog_execute_returns_target_equate_local_effect(
    command_id: str,
    parameters: dict[str, object],
    action_kind: str,
    local_effect_kind: str,
    expected_equate: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {"command_id": command_id, "context": {"kind": "target"}, "parameters": parameters},
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    target_equate = cast(dict[str, object], cast(dict[str, object], action["payload"])["target_equate"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == action_kind
    assert target_equate == expected_equate
    assert application["status"] == "applied"
    assert local_effect == {"kind": local_effect_kind, "target_equate": target_equate}
    assert appended_actions == [action]


@pytest.mark.parametrize(
    ("command_id", "parameters", "action_kind", "payload_key", "local_effect_kind", "expected_payload"),
    [
        (
            "target.custom_struct.add",
            {"name": "InputEvent", "size": 22},
            "create_manual_custom_struct",
            "custom_struct",
            "custom_struct",
            {"name": "InputEvent", "size": 22, "fields": []},
        ),
        (
            "target.custom_struct.edit",
            {"name": "InputEvent", "size": 24},
            "create_manual_custom_struct",
            "custom_struct",
            "custom_struct",
            {"name": "InputEvent", "size": 24, "fields": []},
        ),
        (
            "target.custom_struct.remove",
            {"name": "InputEvent"},
            "remove_manual_custom_struct",
            "custom_struct",
            "custom_struct_remove",
            {"name": "InputEvent"},
        ),
        (
            "target.custom_struct.rename",
            {"previous_name": "InputEvent", "name": "GameInput"},
            "rename_manual_custom_struct",
            "custom_struct",
            "custom_struct",
            {"previous_name": "InputEvent", "name": "GameInput"},
        ),
        (
            "target.custom_struct_field.add",
            {"struct_name": "InputEvent", "name": "ie_Class", "type": "UBYTE", "offset": 4, "size": 1},
            "create_manual_custom_struct_field",
            "custom_struct_field",
            "custom_struct_field",
            {"struct_name": "InputEvent", "name": "ie_Class", "type": "UBYTE", "offset": 4, "size": 1},
        ),
        (
            "target.custom_struct_field.edit",
            {"struct_name": "InputEvent", "name": "ie_Class", "type": "UWORD", "offset": 4, "size": 2},
            "create_manual_custom_struct_field",
            "custom_struct_field",
            "custom_struct_field",
            {"struct_name": "InputEvent", "name": "ie_Class", "type": "UWORD", "offset": 4, "size": 2},
        ),
        (
            "target.custom_struct_field.remove",
            {"struct_name": "InputEvent", "offset": 4, "name": "ie_Class"},
            "remove_manual_custom_struct_field",
            "custom_struct_field",
            "custom_struct_field_remove",
            {"struct_name": "InputEvent", "offset": 4, "name": "ie_Class"},
        ),
        (
            "target.custom_struct_field.rename",
            {"struct_name": "InputEvent", "offset": 4, "name": "ie_Code"},
            "rename_manual_custom_struct_field",
            "custom_struct_field",
            "custom_struct_field",
            {"struct_name": "InputEvent", "offset": 4, "name": "ie_Code"},
        ),
    ],
)
def test_route_manual_action_catalog_execute_returns_custom_struct_local_effect(
    command_id: str,
    parameters: dict[str, object],
    action_kind: str,
    payload_key: str,
    local_effect_kind: str,
    expected_payload: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {"command_id": command_id, "context": {"kind": "target"}, "parameters": parameters},
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    projected = cast(dict[str, object], cast(dict[str, object], action["payload"])[payload_key])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == action_kind
    assert projected == expected_payload
    assert application["status"] == "applied"
    assert local_effect == {"kind": local_effect_kind, payload_key: projected}
    assert appended_actions == [action]


@pytest.mark.parametrize(
    ("row", "element_id", "command_id", "parameters", "action_kind", "expected_field"),
    [
        (
            ListingRow(
                row_id="r0",
                kind="instruction",
                text="move.w 36(a0),d0\n",
                addr=0x20,
                section_index=0,
                start_offset=0x20,
                end_offset=0x24,
                stable_key="gap-row",
                opcode_or_directive="move.w",
                operand_text="36(a0),d0",
                source_context=BlockRowContext(kind="core-block", hunk_index=0),
                unresolved_typed_accesses=(
                    PlatformUnresolvedTypedAccess(
                        operand_index=0,
                        base_register="A0",
                        displacement=36,
                        struct_size=40,
                        root_struct_name="InputEvent",
                        classification="prefix_extension",
                        refined_struct_name="DerivedEvent",
                    ),
                ),
            ),
            "gap-row:typed_gap:0:prefix_extension",
            "typed_gap.field.add",
            {"name": "de_Code", "type": "UWORD", "size": 2},
            "create_manual_custom_struct_field",
            {"struct_name": "DerivedEvent", "offset": 36, "name": "de_Code", "type": "UWORD", "size": 2},
        ),
        (
            ListingRow(
                row_id="r1",
                kind="instruction",
                text="move.w LIB_VERSION(a0),d0\n",
                addr=0x30,
                section_index=0,
                start_offset=0x30,
                end_offset=0x34,
                stable_key="typed-row",
                opcode_or_directive="move.w",
                operand_text="LIB_VERSION(a0),d0",
                source_context=BlockRowContext(kind="core-block", hunk_index=0),
                typed_accesses=(
                    PlatformTypedAccess(
                        operand_index=0,
                        base_register="A0",
                        displacement=20,
                        field_offset=20,
                        root_struct_name="Library",
                        owner_struct_name="Library",
                        field_name="LIB_VERSION",
                        field_expr="LIB_VERSION",
                    ),
                ),
            ),
            "typed-row:typed_access:0:LIB_VERSION",
            "typed_access.field.rename",
            {"name": "LIB_REVISION"},
            "rename_manual_custom_struct_field",
            {"struct_name": "Library", "offset": 20, "name": "LIB_REVISION"},
        ),
    ],
)
def test_route_manual_action_catalog_execute_returns_typed_field_local_effect(
    row: ListingRow,
    element_id: str,
    command_id: str,
    parameters: dict[str, object],
    action_kind: str,
    expected_field: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact([row]))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {"command_id": command_id, "context": _element_command_context(row, element_id), "parameters": parameters},
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    field = cast(dict[str, object], cast(dict[str, object], action["payload"])["custom_struct_field"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == action_kind
    for key, value in expected_field.items():
        assert field[key] == value
    assert field["source_family"] == "struct_pointer"
    assert field["source_evidence_status"] == "analysis_proven"
    assert field["confidence"] == "high"
    assert field["conflicts"] == []
    assert field["parent_evidence_ids"] == []
    assert isinstance(field["source_evidence_id"], str)
    assert field["source_evidence_id"].startswith("prov-bloodwych-struct_pointer-analysis_proven")
    path_scope = cast(dict[str, object], field["path_lifetime_scope"])
    assert path_scope["kind"] == "selected_use"
    assert path_scope["addr"] == row.addr
    assert application["status"] == "applied"
    assert local_effect == {"kind": "custom_struct_field", "custom_struct_field": field}
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_typed_field_preserves_context_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    row = ListingRow(
        row_id="r0",
        kind="instruction",
        text="move.w 36(a0),d0\n",
        addr=0x20,
        section_index=0,
        start_offset=0x20,
        end_offset=0x24,
        stable_key="gap-row",
        opcode_or_directive="move.w",
        operand_text="36(a0),d0",
        source_context=BlockRowContext(kind="core-block", hunk_index=0),
        unresolved_typed_accesses=(
            PlatformUnresolvedTypedAccess(
                operand_index=0,
                base_register="A0",
                displacement=36,
                struct_size=40,
                root_struct_name="InputEvent",
                classification="prefix_extension",
                refined_struct_name="DerivedEvent",
            ),
        ),
    )
    context = _element_command_context(row, "gap-row:typed_gap:0:prefix_extension") | {
        "source_evidence_id": "prov-selected-struct-pointer",
        "source_family": "struct_pointer",
        "source_evidence_status": "manual_classified",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x20},
        "confidence": "medium",
        "conflicts": [],
        "parent_evidence_ids": ["prov-parent-a0"],
    }
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact([row]))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "typed_gap.field.add",
            "context": context,
            "parameters": {"name": "de_Code", "type": "UWORD", "size": 2},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    field = cast(dict[str, object], cast(dict[str, object], action["payload"])["custom_struct_field"])

    assert field["source_evidence_id"] == "prov-selected-struct-pointer"
    assert field["source_evidence_status"] == "manual_classified"
    assert field["path_lifetime_scope"] == {"kind": "selected_use", "hunk": 0, "addr": 0x20}
    assert field["parent_evidence_ids"] == ["prov-parent-a0"]
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_data_block_type_preserves_context_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    row = {
        "row_id": "r0",
        "row_key": "data-row",
        "stable_key": "data-row",
        "kind": "data",
        "text": "dc.l $00000000\n",
        "addr": 0x20,
        "section_index": 0,
        "start_offset": 0x20,
        "end_offset": 0x24,
        "bytes": "00000000",
        "active_data_block_layout": {
            "layout_id": "event_table",
            "hunk": 0,
            "source_start": 0x20,
            "source_end": 0x24,
        },
    }
    context = _row_command_context(row) | {
        "source_evidence_id": "prov-selected-data-block",
        "source_family": "data_block_pointer",
        "source_evidence_status": "manual_classified",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0x20},
        "confidence": "medium",
        "conflicts": [],
        "parent_evidence_ids": ["prov-table-base"],
    }
    appended_actions: list[dict[str, object]] = []

    class DataBlockListingArtifact:
        rows = [row]

        def navigation_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return {"groups": {}, "app_slot_analysis": {}}, {}

        def close(self) -> None:
            return None

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", DataBlockListingArtifact())
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    catalog_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _row_command_query(row)
        | {
            "source_evidence_id": ["prov-selected-data-block"],
            "source_family": ["data_block_pointer"],
            "source_evidence_status": ["manual_classified"],
            "path_lifetime_scope": [json.dumps({"kind": "selected_use", "hunk": 0, "addr": 0x20})],
            "confidence": ["medium"],
            "conflicts": [json.dumps([])],
            "parent_evidence_ids": [json.dumps(["prov-table-base"])],
        },
    )
    commands = cast(list[dict[str, object]], cast(dict[str, object], catalog_payload["data"])["commands"])
    bind_command = next(command for command in commands if command["command_id"] == "row.data_block.element.bind_type")
    bind_parameters = cast(dict[str, object], bind_command["parameters"])
    assert bind_parameters["path_lifetime_scope"] == {"kind": "selected_use", "hunk": 0, "addr": 0x20}
    assert bind_parameters["parent_evidence_ids"] == ["prov-table-base"]

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "row.data_block.element.bind_type",
            "context": context,
            "parameters": {
                "layout_id": "event_table",
                "offset": 0,
                "width": 4,
                "binding_kind": "platform_struct",
                "type_id": "InputEvent",
                "requires_source_evidence": True,
            },
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    element = cast(dict[str, object], cast(dict[str, object], action["payload"])["data_block_element"])
    binding = cast(dict[str, object], element["type_binding"])

    assert binding["source_evidence_id"] == "prov-selected-data-block"
    assert binding["source_evidence_status"] == "manual_classified"
    assert binding["path_lifetime_scope"] == {"kind": "selected_use", "hunk": 0, "addr": 0x20}
    assert binding["confidence"] == "medium"
    assert binding["parent_evidence_ids"] == ["prov-table-base"]
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_manual_action_pending_range_preserves_subject_row_index_zero() -> None:
    pending = disasm_server._manual_action_pending_range(
        {"seed": {"row_index": 0, "hunk": 0, "addr": 4, "end": 6}},
        {"row_index": 9},
    )

    assert pending is not None
    assert pending["row_indexes"] == [0]


@pytest.mark.parametrize("command_id", ["target.execution_view.add", "target.execution_view.edit"])
def test_route_manual_action_catalog_execute_appends_execution_view_action(
    command_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": command_id,
            "context": {"kind": "target"},
            "parameters": {
                "source_start": 0x20,
                "source_end": 0x80,
                "base_addr": 0x4000,
                "name": "stage_code",
            },
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    execution_view = cast(dict[str, object], cast(dict[str, object], action["payload"])["execution_view"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "create_manual_execution_view"
    assert execution_view == {
        "execution_view_id": "catalog-execution-view-00000020-00000080-00004000",
        "source_start": 0x20,
        "source_end": 0x80,
        "base_addr": 0x4000,
        "name": "stage_code",
    }
    assert application["status"] == "applied"
    assert local_effect == {"kind": "execution_view", "execution_view": execution_view}
    assert appended_actions == [action]


def test_route_manual_action_catalog_execute_removes_execution_view_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "target.execution_view.remove",
            "context": {"kind": "target"},
            "parameters": {
                "source_start": 0x20,
                "source_end": 0x80,
                "base_addr": 0x4000,
            },
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    execution_view = cast(dict[str, object], cast(dict[str, object], action["payload"])["execution_view"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "remove_manual_execution_view"
    assert execution_view == {"source_start": 0x20, "source_end": 0x80, "base_addr": 0x4000}
    assert local_effect == {"kind": "execution_view_remove", "execution_view": execution_view}
    assert appended_actions == [action]


@pytest.mark.parametrize("command_id", ["target.rsset_region.add", "target.rsset_region.edit"])
def test_route_manual_action_catalog_execute_adds_rsset_layout_region_action(
    command_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": command_id,
            "context": {"kind": "target"},
            "parameters": {
                "offset": 4,
                "size": 2,
                "layout_name": "work",
                "base_symbol": "__game_work_base__",
                "sizeof_symbol": "work_SIZEOF",
                "symbol": "work_counter",
                "storage_kind": "scalar",
            },
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    region = cast(dict[str, object], cast(dict[str, object], action["payload"])["rsset_layout_region"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "create_manual_rsset_layout_region"
    assert region["rsset_layout_region_id"] == "catalog-rsset-region-work-0004"
    assert region["symbol"] == "work_counter"
    assert local_effect == {"kind": "rsset_layout_region", "rsset_layout_region": region}
    assert appended_actions == [action]


def test_route_manual_action_catalog_execute_renames_app_slot_with_rsset_region(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="move.l d0,app_0234(a6)\n",
            addr=0x20,
            section_index=0,
            start_offset=0x20,
            end_offset=0x24,
            stable_key="app-write",
            opcode_or_directive="move.l",
            operand_text="d0,app_0234(a6)",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_0234", 0x0234, "A6", 1, "write"),),
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "app_slot.rename",
            "context": _element_command_context(rows[0], "app-write:app_slot:1:app_0234:write"),
            "parameters": {"symbol": "app_player_state", "size": 4, "storage_kind": "pointer"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    region = cast(dict[str, object], cast(dict[str, object], action["payload"])["rsset_layout_region"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "create_manual_rsset_layout_region"
    assert region == {
        "rsset_layout_region_id": "catalog-rsset-region-app-0234",
        "offset": 0x0234,
        "size": 4,
        "symbol": "app_player_state",
        "storage_kind": "pointer",
    }
    assert local_effect == {"kind": "rsset_layout_region", "rsset_layout_region": region}
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_removes_app_slot_rsset_region(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="move.l d0,app_0234(a6)\n",
            addr=0x20,
            section_index=0,
            start_offset=0x20,
            end_offset=0x24,
            stable_key="app-write",
            opcode_or_directive="move.l",
            operand_text="d0,app_0234(a6)",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_0234", 0x0234, "A6", 1, "write"),),
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "app_slot.remove",
            "context": _element_command_context(rows[0], "app-write:app_slot:1:app_0234:write"),
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    region = cast(dict[str, object], cast(dict[str, object], action["payload"])["rsset_layout_region"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "remove_manual_rsset_layout_region"
    assert region == {"offset": 0x0234}
    assert local_effect == {"kind": "rsset_layout_region_remove", "rsset_layout_region": region}
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_removes_rsset_layout_region_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "target.rsset_region.remove",
            "context": {"kind": "target"},
            "parameters": {"offset": 4, "layout_name": "work", "base_symbol": "__game_work_base__"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    region = cast(dict[str, object], cast(dict[str, object], action["payload"])["rsset_layout_region"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "remove_manual_rsset_layout_region"
    assert region == {"offset": 4, "layout_name": "work", "base_symbol": "__game_work_base__"}
    assert local_effect == {"kind": "rsset_layout_region_remove", "rsset_layout_region": region}
    assert appended_actions == [action]


def test_route_manual_action_catalog_execute_appends_comment_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="rts\n",
            addr=4,
            section_index=0,
            start_offset=4,
            end_offset=6,
            stable_key="row-0",
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "comment.edit",
            "context": _row_command_context(rows[0]),
            "parameters": {"text": "manual return"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    comment = cast(dict[str, object], cast(dict[str, object], action["payload"])["comment"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]
    mutation = cast(dict[str, object], cast(dict[str, object], payload["data"])["mutation"])
    workflow_profile = cast(dict[str, object], cast(dict[str, object], payload["data"])["workflow_profile"])
    workflow_spans = cast(list[dict[str, object]], workflow_profile["spans"])

    assert action["kind"] == "create_manual_comment"
    assert comment["text"] == "manual return"
    assert comment["addr"] == 4
    assert comment["row_index"] == 0
    assert application["status"] == "applied"
    assert local_effect["kind"] == "comment"
    assert application["refresh"] == {"mode": "project"}
    assert mutation["durable_action_id"] == ""
    assert mutation["manual_action_log_count"] == 0
    assert mutation["projection_hash"] == "cache"
    assert cast(list[dict[str, object]], mutation["affected_locators"])[0]["row_key"] == "row-0"
    assert workflow_profile["workflow_id"] == "manual_command_execution"
    assert workflow_profile["target_id"] == "bloodwych"
    assert "locator_resolution" in [span["name"] for span in workflow_spans]
    assert "manual_action_append" in [span["name"] for span in workflow_spans]
    assert "listing_cache_invalidation" in [span["name"] for span in workflow_spans]
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_command_resolves_row_without_all_rows_materialization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="rts\n",
            addr=4,
            section_index=0,
            start_offset=4,
            end_offset=6,
            stable_key="row-0",
        )
    ]

    class NoAllRowsArtifact(_RowsCListingArtifact):
        def window_payload(self, *, start: int, count: int):
            if start == 0 and count == len(self.rows):
                raise AssertionError("normal row command should not materialize all rows")
            return super().window_payload(start=start, count=count)

    _seed_c_listing_artifact(monkeypatch, "bloodwych", NoAllRowsArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(
        disasm_server,
        "append_manual_action",
        lambda target_dir, *, kind, payload, binary_source: {"action_id": "a1", "kind": kind, "payload": payload},
    )
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "comment.edit",
            "context": _row_command_context(rows[0]),
            "parameters": {"text": "manual return"},
        },
    )

    assert payload["ok"] is True
    assert cast(dict[str, object], cast(dict[str, object], payload["data"])["mutation"])["projection_hash"] == "cache"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_command_resolves_element_without_all_rows_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="entry",
            kind="label",
            text="ENTRYPOINT:\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=0,
            label="ENTRYPOINT",
            stable_key="entry-key",
        )
    ]

    class NoAllRowsArtifact(_RowsCListingArtifact):
        def window_payload(self, *, start: int, count: int):
            if start == 0 and count == len(self.rows):
                raise AssertionError("normal element command should not materialize all rows")
            return super().window_payload(start=start, count=count)

    _seed_c_listing_artifact(monkeypatch, "bloodwych", NoAllRowsArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "entry-key:label:ENTRYPOINT"),
    )

    assert payload["ok"] is True
    assert cast(dict[str, object], payload["data"])["context"]["kind"] == "element"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_comment_id_distinguishes_same_address_rows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="entry-a",
            kind="label",
            text="ENTRYPOINT0001:\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=0,
            label="ENTRYPOINT0001",
            stable_key="entry-a-key",
        ),
        ListingRow(
            row_id="entry-b",
            kind="label",
            text="ENTRYPOINT0002:\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=0,
            label="ENTRYPOINT0002",
            stable_key="entry-b-key",
        ),
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    for row_index in (0, 1):
        disasm_server.route_request(
            "POST",
            "/api/projects/bloodwych/commands/execute",
            {},
            {
                "command_id": "comment.edit",
                "context": _row_command_context(rows[row_index]),
                "parameters": {"text": f"comment {row_index}"},
            },
        )

    comments = [
        cast(dict[str, object], cast(dict[str, object], action["payload"])["comment"])
        for action in appended_actions
    ]
    assert comments[0]["comment_id"] != comments[1]["comment_id"]
    assert comments[0]["stable_key"] == "entry-a-key"
    assert comments[1]["stable_key"] == "entry-b-key"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_label_id_distinguishes_same_address_rows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="entry-a",
            kind="label",
            text="ENTRYPOINT0001:\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=0,
            label="ENTRYPOINT0001",
            stable_key="entry-a-key",
        ),
        ListingRow(
            row_id="entry-b",
            kind="label",
            text="ENTRYPOINT0002:\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=0,
            label="ENTRYPOINT0002",
            stable_key="entry-b-key",
        ),
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    for row_index in (0, 1):
        disasm_server.route_request(
            "POST",
            "/api/projects/bloodwych/commands/execute",
            {},
            {
                "command_id": "label.rename",
                "context": _element_command_context(rows[row_index], f"entry-{chr(97 + row_index)}-key:label:ENTRYPOINT000{row_index + 1}"),
                "parameters": {"name": f"entry_{row_index}"},
            },
        )

    labels = [
        cast(dict[str, object], cast(dict[str, object], action["payload"])["label"])
        for action in appended_actions
    ]
    assert labels[0]["label_id"] != labels[1]["label_id"]
    assert labels[0]["stable_key"] == "entry-a-key"
    assert labels[1]["stable_key"] == "entry-b-key"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_manual_projection_uses_precise_comment_locator_without_address_fallback() -> None:
    rows = [
        {
            "kind": "label",
            "label": "ENTRYPOINT0001",
            "text": "ENTRYPOINT0001:\n",
            "section_index": 0,
            "start_offset": 0,
            "addr": 0,
            "stable_key": "entry-a-key",
        },
        {
            "kind": "directive",
            "text": "ORG $10000\n",
            "section_index": 0,
            "start_offset": 0,
            "addr": 0,
            "stable_key": "org-key",
        },
    ]
    comments = [
        {
            "comment_id": "comment-entry-a",
            "text": "entry only",
            "hunk": 0,
            "addr": 0,
            "stable_key": "entry-a-key",
        }
    ]

    first = disasm_server._apply_manual_listing_projection(rows[0], [], comments, 20)
    second = disasm_server._apply_manual_listing_projection(rows[1], [], comments, 21)

    assert first["comment_text"] == "entry only"
    assert "comment_text" not in second


def test_manual_projection_uses_precise_label_locator_without_address_fallback() -> None:
    rows = [
        {
            "kind": "label",
            "label": "ENTRYPOINT0001",
            "text": "ENTRYPOINT0001:\n",
            "section_index": 0,
            "start_offset": 0,
            "addr": 0,
            "stable_key": "entry-a-key",
        },
        {
            "kind": "label",
            "label": "ENTRYPOINT0002",
            "text": "ENTRYPOINT0002:\n",
            "section_index": 0,
            "start_offset": 0,
            "addr": 0,
            "stable_key": "entry-b-key",
        },
    ]
    labels = [
        {
            "label_id": "label-entry-a",
            "name": "renamed_entry",
            "scope": "global",
            "address_domain": "source",
            "hunk": 0,
            "addr": 0,
            "stable_key": "entry-a-key",
        }
    ]

    first = disasm_server._apply_manual_listing_projection(rows[0], labels, [], 20)
    second = disasm_server._apply_manual_listing_projection(rows[1], labels, [], 21)

    assert first["label"] == "renamed_entry"
    assert second["label"] == "ENTRYPOINT0002"


def test_manual_projection_strips_trailing_comment_text_from_source_comment_rows() -> None:
    row = {
        "kind": "comment",
        "text": "    ; Test\n",
        "comment_text": "Test",
        "section_index": 0,
        "stable_key": "source-comment-row",
    }
    comments = [
        {
            "comment_id": "source-comment",
            "text": "Test",
            "hunk": 0,
            "addr": 0,
            "stable_key": "source-comment-row",
        }
    ]

    projected = disasm_server._apply_manual_listing_projection(row, [], comments, 10)

    assert projected["text"] == "    ; Test\n"
    assert "comment_text" not in projected


def test_route_manual_action_catalog_returns_range_actions_with_mixed_eligibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="moveq #0,d0\n", addr=0, start_offset=0, end_offset=2),
        ListingRow(row_id="r1", kind="data", text="dc.b $41\n", addr=2, start_offset=2, end_offset=3, bytes=b"A"),
        ListingRow(row_id="r2", kind="data", text="dc.b $42\n", addr=3, start_offset=3, end_offset=4, bytes=b"B"),
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _range_command_query(rows),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])

    raw_block = next(action for action in actions if action["action_id"] == "range.seed.data.raw")
    named_block = next(action for action in actions if action["action_id"] == "range.seed.data.named")
    palette = next(action for action in actions if action["action_id"] == "range.seed.data.palette")
    data_block_layout = next(action for action in actions if action["action_id"] == "range.data_block.layout.create")
    code_seed = next(action for action in actions if action["action_id"] == "range.seed.code")
    semantic_helpers = next(action for action in actions if action["action_id"] == "range.semantic.helpers")

    assert raw_block["range_availability"] == "partial"
    assert raw_block["applicable_subranges"] == [{"row_indexes": [1, 2], "row_ids": ["r1", "r2"], "start_offset": 2, "end_offset": 4}]
    assert {
        str(action["action_id"]).removeprefix("range.seed.data.")
        for action in actions
        if str(action["action_id"]).removeprefix("range.seed.data.") in _FULL_DATA_ROLE_IDS
    } == _FULL_DATA_ROLE_IDS
    assert named_block["range_availability"] == "partial"
    assert named_block["parameters"] == {"seed_kind": "data", "data_role": "raw", "unit": "byte"}
    assert named_block["parameter_schema"]["required"] == ["name"]
    assert named_block["interaction_schema"]["type"] == "text"
    assert named_block["interaction_schema"]["primary_field"] == "name"
    assert palette["range_availability"] == "partial"
    assert palette["parameters"] == {"seed_kind": "data", "data_role": "palette", "unit": "word"}
    assert data_block_layout["range_availability"] == "partial"
    assert data_block_layout["parameters"] == {"default_unit": "byte"}
    assert data_block_layout["applicable_subranges"] == [
        {"row_indexes": [1, 2], "row_ids": ["r1", "r2"], "start_offset": 2, "end_offset": 4}
    ]
    assert "2 of 3" in str(raw_block["availability_reason"])
    assert code_seed["range_availability"] == "partial"
    assert semantic_helpers["range_availability"] == "unavailable"
    assert semantic_helpers["enabled"] is False
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_range_uses_visible_metadata_without_hidden_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(row_id="hidden-code", kind="instruction", text="rts\n", addr=0, start_offset=0, end_offset=2),
        ListingRow(row_id="visible-data-1", kind="data", text="dc.b $41\n", addr=2, start_offset=2, end_offset=3),
        ListingRow(row_id="hidden-code-2", kind="instruction", text="rts\n", addr=3, start_offset=3, end_offset=5),
        ListingRow(row_id="visible-data-2", kind="data", text="dc.b $42\n", addr=5, start_offset=5, end_offset=6),
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _range_command_query([rows[1], rows[3]]),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])
    raw_block = next(action for action in actions if action["action_id"] == "range.seed.data.raw")

    assert raw_block["range_availability"] == "applicable"
    assert raw_block["applicable_subranges"] == [
        {"row_indexes": [1], "row_ids": ["visible-data-1"], "start_offset": 2, "end_offset": 3},
        {"row_indexes": [3], "row_ids": ["visible-data-2"], "start_offset": 5, "end_offset": 6},
    ]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_range_uses_explicit_applicable_subranges(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="moveq #0,d0\n", addr=0, section_index=0, start_offset=0, end_offset=2),
        ListingRow(row_id="r1", kind="data", text="dc.b $41\n", addr=2, section_index=0, start_offset=2, end_offset=3, bytes=b"A"),
        ListingRow(row_id="r2", kind="data", text="dc.b $42\n", addr=3, section_index=0, start_offset=3, end_offset=4, bytes=b"B"),
    ]
    appended_actions: list[dict[str, object]] = []
    target_dir = tmp_path / "targets" / "bloodwych"
    target_dir.mkdir(parents=True)
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=target_dir),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "range.seed.data.raw",
            "context": _range_command_context(rows),
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    seed = cast(dict[str, object], cast(dict[str, object], action["payload"])["seed"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    pending_ranges = cast(list[dict[str, object]], application["pending_ranges"])

    assert seed["kind"] == "data"
    assert seed["addr"] == 2
    assert seed["end"] == 4
    assert seed["row_indexes"] == [1, 2]
    assert application["status"] == "pending"
    assert cast(dict[str, object], application["refresh"])["mode"] == "analysis"
    assert pending_ranges[0]["row_indexes"] == [1, 2]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    named_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "range.seed.data.named",
            "context": _range_command_context(rows),
            "parameters": {"name": "manual_range"},
        },
    )
    named_action = cast(dict[str, object], cast(dict[str, object], named_payload["data"])["action"])
    named_seed = cast(dict[str, object], cast(dict[str, object], named_action["payload"])["seed"])

    assert named_seed["kind"] == "data"
    assert named_seed["name"] == "manual_range"
    assert named_seed["data_role"] == "raw"
    assert named_seed["unit"] == "byte"
    assert named_seed["addr"] == 2
    assert named_seed["end"] == 4
    assert named_seed["row_indexes"] == [1, 2]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    layout_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "range.data_block.layout.create",
            "context": _range_command_context(rows),
            "parameters": {"name": "ascii_hex_digit_value", "role": "lookup_table", "default_unit": "byte"},
        },
    )
    layout_action = cast(dict[str, object], cast(dict[str, object], layout_payload["data"])["action"])
    layout = cast(dict[str, object], cast(dict[str, object], layout_action["payload"])["data_block_layout"])
    layout_application = cast(dict[str, object], cast(dict[str, object], layout_payload["data"])["application"])

    assert layout_action["kind"] == "create_manual_data_block_layout"
    assert layout["hunk"] == 0
    assert layout["source_start"] == 2
    assert layout["source_end"] == 4
    assert layout["row_indexes"] == [1, 2]
    assert layout["name"] == "ascii_hex_digit_value"
    assert layout["role"] == "lookup_table"
    assert layout["default_unit"] == "byte"
    assert layout_application["status"] == "applied"
    assert cast(dict[str, object], layout_application["refresh"])["mode"] == "project"
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    element_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "range.data_block.element.set",
            "context": _range_command_context(rows),
            "parameters": {
                "layout_id": "ascii-hex",
                "offset": 0x30,
                "kind": "array",
                "name": "digits",
                "representation": "character",
                "array_count": 2,
                "array_stride": 1,
            },
        },
    )
    element_action = cast(dict[str, object], cast(dict[str, object], element_payload["data"])["action"])
    element = cast(dict[str, object], cast(dict[str, object], element_action["payload"])["data_block_element"])
    element_application = cast(dict[str, object], cast(dict[str, object], element_payload["data"])["application"])

    assert element_action["kind"] == "set_manual_data_block_element"
    assert element == {
        "data_block_element_id": "ascii-hex:30",
        "layout_id": "ascii-hex",
        "offset": 0x30,
        "width": 2,
        "kind": "array",
        "name": "digits",
        "representation": "character",
        "array_count": 2,
        "array_stride": 1,
    }
    assert element_application["status"] == "applied"
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    represent_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "range.data_block.element.represent",
            "context": _range_command_context(rows),
            "parameters": {"layout_id": "ascii-hex", "offset": 0x30, "representation": "hex"},
        },
    )
    represent_action = cast(dict[str, object], cast(dict[str, object], represent_payload["data"])["action"])

    assert represent_action["kind"] == "represent_manual_data_block_element"
    assert cast(dict[str, object], represent_action["payload"])["data_block_element"] == {
        "layout_id": "ascii-hex",
        "offset": 0x30,
        "representation": "hex",
    }
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    remove_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "range.data_block.element.remove",
            "context": _range_command_context(rows),
            "parameters": {"layout_id": "ascii-hex", "offset": 0x30, "removal_state": "raw"},
        },
    )
    remove_action = cast(dict[str, object], cast(dict[str, object], remove_payload["data"])["action"])

    assert remove_action["kind"] == "remove_manual_data_block_element"
    assert cast(dict[str, object], remove_action["payload"])["data_block_element"] == {
        "layout_id": "ascii-hex",
        "offset": 0x30,
        "width": 2,
        "removal_state": "raw",
    }
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    interpret_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "row.data_block.element.interpret_ref",
            "context": _row_command_context(rows[1]),
            "parameters": {
                "layout_id": "ascii-hex",
                "offset": 0x30,
                "width": 1,
                "reference_kind": "absolute",
                "target_hunk": 0,
                "target_offset": 0x41,
            },
        },
    )
    interpret_action = cast(dict[str, object], cast(dict[str, object], interpret_payload["data"])["action"])
    interpreted_ref = cast(dict[str, object], cast(dict[str, object], interpret_action["payload"])["data_block_interpreted_ref"])
    interpret_application = cast(dict[str, object], cast(dict[str, object], interpret_payload["data"])["application"])
    interpret_effect = cast(list[dict[str, object]], interpret_application["local_effects"])[0]

    assert interpret_action["kind"] == "interpret_manual_data_block_element_ref"
    assert interpreted_ref == {
        "data_block_ref_id": "ascii-hex:30:absolute:h0:00000041",
        "layout_id": "ascii-hex",
        "offset": 0x30,
        "width": 1,
        "reference_kind": "absolute",
        "target_hunk": 0,
        "target_offset": 0x41,
        "target_locator": {"hunk": 0, "offset": 0x41},
        "source_value": 0x41,
        "confidence": "manual",
        "xref_generation_mode": "bidirectional",
    }
    assert interpret_effect["kind"] == "data_block_interpreted_ref"
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    clear_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "row.data_block.element.clear_ref",
            "context": _row_command_context(rows[1]),
            "parameters": {
                "layout_id": "ascii-hex",
                "offset": 0x30,
                "data_block_ref_id": "ascii-hex:30:absolute:h0:00000041",
            },
        },
    )
    clear_action = cast(dict[str, object], cast(dict[str, object], clear_payload["data"])["action"])
    cleared_ref = cast(dict[str, object], cast(dict[str, object], clear_action["payload"])["data_block_interpreted_ref"])
    clear_application = cast(dict[str, object], cast(dict[str, object], clear_payload["data"])["application"])
    clear_effect = cast(list[dict[str, object]], clear_application["local_effects"])[0]

    assert clear_action["kind"] == "remove_manual_data_block_element_ref"
    assert cleared_ref == {
        "data_block_ref_id": "ascii-hex:30:absolute:h0:00000041",
        "layout_id": "ascii-hex",
        "offset": 0x30,
    }
    assert clear_effect["kind"] == "data_block_interpreted_ref_remove"
    assert appended_actions == [
        action,
        named_action,
        layout_action,
        element_action,
        represent_action,
        remove_action,
        interpret_action,
        clear_action,
    ]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_ignores_numeric_label_text_for_semantic_hints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r28",
            kind="label",
            text="abs_0_00010488:\n",
            addr=0x10488,
            label="abs_0_00010488",
            stable_key="label-10488",
        )
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "label-10488:label:abs_0_00010488"),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])

    label_action = next(action for action in actions if action["action_id"] == "label.rename")
    assert [action["action_id"] for action in actions] == ["navigation.follow_reference", "label.rename"]
    assert label_action["default_key_binding"] == "F2"
    assert label_action["interaction_schema"]["type"] == "text"
    assert label_action["interaction_schema"]["primary_rank"] == 0
    assert label_action["interaction_schema"]["validation"]["active_profile"] == "vasm"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_appends_label_rename_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="loc_0_00000000:\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=0,
            label="loc_0_00000000",
            stable_key="label-0",
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "label.rename",
            "context": _element_command_context(rows[0], "label-0:label:loc_0_00000000"),
            "parameters": {"name": "start"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    label = cast(dict[str, object], cast(dict[str, object], action["payload"])["label"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "create_manual_label"
    assert label["label_id"] == "catalog-label-source-h0-00000000-sk-label-0"
    assert label["name"] == "start"
    assert label["previous_name"] == "loc_0_00000000"
    assert label["hunk"] == 0
    assert label["addr"] == 0
    assert application["status"] == "applied"
    assert cast(dict[str, object], application["refresh"])["mode"] == "project"
    assert local_effect["kind"] == "label_rename"
    assert local_effect["row_index"] == 0
    assert local_effect["name"] == "start"
    assert local_effect["label_id"] == "catalog-label-source-h0-00000000-sk-label-0"
    assert appended_actions == [action]
    assert disasm_server._LISTING_PROJECTION_SERVICE.is_presentation_dirty("bloodwych")
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_renames_projected_manual_label_by_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = replace(
        _binary_project("bloodwych", ready=True),
        manual_state={
            "labels": [
                {
                    "label_id": "catalog-label-runtime-h0-0001001E",
                    "name": "copy_loop",
                    "address_domain": "runtime",
                    "hunk": 0,
                    "addr": 0x1001E,
                    "row_index": 245,
                    "stable_key": "s0:0000001E:label:245",
                }
            ]
        },
    )
    appended_actions: list[dict[str, object]] = []
    rows = [
        {
            "row_index": 245,
            "row_id": "r0",
            "kind": "label",
            "text": "copy_loop:\n",
            "addr": 0x1001E,
            "runtime_address": 0x1001E,
            "section_index": 0,
            "start_offset": 0x1E,
            "end_offset": 0x1E,
            "label": "copy_loop",
            "stable_key": "s0:0000001E:label:245",
            "manual_label_id": "catalog-label-runtime-h0-0001001E",
            "manual_label_address_domain": "runtime",
        }
    ]

    class DictRowsArtifact:
        def close(self) -> None:
            return None

        def summary_payload(self):
            return {"total_rows": len(rows)}, {}

        def window_payload(self, *, start: int, count: int):
            return {"rows": rows[start : start + count]}, {}

        def navigation_payload(self):
            return {"groups": {}, "app_slot_analysis": {}}, {}

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", DictRowsArtifact())
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "label.rename",
            "context": _element_command_context(rows[0], "s0:0000001E:label:245:label:copy_loop"),
            "parameters": {"name": "copy_loop_again"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "rename_manual_label"
    assert action["payload"] == {
        "label_id": "catalog-label-runtime-h0-0001001E",
        "name": "copy_loop_again",
    }
    assert local_effect["label_id"] == "catalog-label-runtime-h0-0001001E"
    assert local_effect["address_domain"] == "runtime"
    assert local_effect["name"] == "copy_loop_again"
    assert appended_actions == [action]


def test_route_command_execute_rejects_locator_without_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {
        "row_index": 0,
        "row_id": "r0",
        "kind": "label",
        "text": "loc_0_00000000:\n",
        "addr": 0,
        "section_index": 0,
        "start_offset": 0,
        "end_offset": 0,
        "label": "loc_0_00000000",
        "stable_key": "label-0",
    }

    disasm_server._clear_project_listing_cache("bloodwych")
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    with pytest.raises(disasm_server.CommandContractError) as exc:
        disasm_server.route_request(
            "POST",
            "/api/projects/bloodwych/commands/execute",
            {},
            {
                "command_id": "label.rename",
                "context": _element_command_context(row, "label-0:label:loc_0_00000000"),
                "parameters": {"name": "start"},
            },
        )
    assert exc.value.code == "missing_locator"


def test_route_manual_action_catalog_execute_preserves_absolute_label_domain(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="abs_0_00010000:\n",
            addr=0,
            section_index=0,
            start_offset=0,
            label="abs_0_00010000",
            stable_key="label-0",
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "label.rename",
            "context": _element_command_context(rows[0], "label-0:label:abs_0_00010000"),
            "parameters": {"name": "ENTRYPOINT0000"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    label = cast(dict[str, object], cast(dict[str, object], action["payload"])["label"])

    assert label["label_id"] == "catalog-label-runtime-h0-00010000-sk-label-0"
    assert label["address_domain"] == "runtime"
    assert label["addr"] == 0x10000
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_appends_row_data_type_helper_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="data",
            text="dc.b $00,$00,$00,$00\n",
            addr=4,
            section_index=1,
            start_offset=4,
            end_offset=8,
            stable_key="row-0",
            bytes=b"\0\0\0\0",
            opcode_or_directive="dc.b",
            operand_text="$00,$00,$00,$00",
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "row.seed.data.palette",
            "context": _row_command_context(rows[0]),
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    seed = cast(dict[str, object], cast(dict[str, object], action["payload"])["seed"])

    assert action["kind"] == "create_manual_seed"
    assert seed["kind"] == "data"
    assert seed["data_role"] == "palette"
    assert seed["unit"] == "word"
    assert seed["hunk"] == 1
    assert seed["addr"] == 4
    assert seed["end"] == 8
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_appends_named_data_seed_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="data",
            text="dc.b $41,$42\n",
            addr=4,
            section_index=1,
            start_offset=4,
            end_offset=6,
            stable_key="row-0",
            bytes=b"AB",
            opcode_or_directive="dc.b",
            operand_text="$41,$42",
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "row.seed.data.named",
            "context": _row_command_context(rows[0]),
            "parameters": {"name": "manual_data"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    seed = cast(dict[str, object], cast(dict[str, object], action["payload"])["seed"])

    assert action["kind"] == "create_manual_seed"
    assert seed["kind"] == "data"
    assert seed["name"] == "manual_data"
    assert seed["data_role"] == "raw"
    assert seed["unit"] == "byte"
    assert seed["hunk"] == 1
    assert seed["addr"] == 4
    assert seed["end"] == 6
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_appends_valid_log_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = replace(
        _binary_project("bloodwych", ready=True),
        review_state=ReviewState.NEEDS_REVIEW,
        review_items=(
            {
                "kind": ReviewItemKind.UNRECONCILED_DATA_RANGE,
                "item_id": "unreconciled:h0:00000004-00000008",
                "evidence_fingerprint": "fingerprint",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "hunk": 0,
                "start": 4,
                "end": 8,
                "message": "Known data gap",
            },
        ),
    )
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "review.seed.data.copper_list",
            "context": {"kind": "review_item", "item_id": "unreconciled:h0:00000004-00000008"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    seed = cast(dict[str, object], cast(dict[str, object], action["payload"])["seed"])

    assert action["kind"] == "create_manual_seed"
    assert seed["kind"] == "data"
    assert seed["data_role"] == "copper_list"
    assert seed["unit"] == "word"
    assert seed["addr"] == 4
    assert seed["end"] == 8
    named_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "review.seed.data.named",
            "context": {"kind": "review_item", "item_id": "unreconciled:h0:00000004-00000008"},
            "parameters": {"name": "manual_gap"},
        },
    )
    named_action = cast(dict[str, object], cast(dict[str, object], named_payload["data"])["action"])
    named_seed = cast(dict[str, object], cast(dict[str, object], named_action["payload"])["seed"])

    assert named_seed["kind"] == "data"
    assert named_seed["name"] == "manual_gap"
    assert named_seed["data_role"] == "raw"
    assert named_seed["unit"] == "byte"
    assert named_seed["addr"] == 4
    assert named_seed["end"] == 8
    assert appended_actions == [action, named_action]


def test_route_manual_action_catalog_execute_removes_manual_seed_from_conflict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = replace(
        _binary_project("bloodwych", ready=True),
        review_state=ReviewState.BLOCKED,
        review_items=(
            {
                "kind": ReviewItemKind.MANUAL_SEED_CONFLICT,
                "item_id": "manual_seed_conflict:data-as-code:entry",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "seed_ids": ["data-as-code"],
                "hunk": 0,
                "start": 0,
                "end": 2,
                "message": "Required manual seed data-as-code conflicts",
            },
        ),
    )
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "review.seed.remove",
            "context": {"kind": "review_item", "item_id": "manual_seed_conflict:data-as-code:entry"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])

    assert action["kind"] == "remove_manual_seed"
    assert action["payload"] == {"seed_id": "data-as-code"}
    assert application["status"] == "applied"
    assert application["refresh"] == {"mode": "project"}
    assert appended_actions == [action]


def test_route_manual_action_catalog_execute_appends_label_rename_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = replace(
        _binary_project("bloodwych", ready=True),
        review_state=ReviewState.BLOCKED,
        review_items=(
            {
                "kind": ReviewItemKind.LABEL_SCOPE_CONFLICT,
                "item_id": "label_scope_conflict:l1:missing-owner",
                "scope": "range",
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "label_ids": ["l1"],
                "hunk": 0,
                "start": 4,
                "end": 5,
                "message": "Local manual label l1 has no explicit owner id",
            },
        ),
    )
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "review.label.rename",
            "context": {"kind": "review_item", "item_id": "label_scope_conflict:l1:missing-owner"},
            "parameters": {"name": "renamed_label"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])

    assert action["kind"] == "rename_manual_label"
    assert action["payload"] == {"label_id": "l1", "name": "renamed_label"}
    assert cast(dict[str, object], application["refresh"])["mode"] == "project"
    assert appended_actions == [action]


def test_route_manual_action_catalog_execute_appends_representation_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="data",
            text="dc.b $41\n",
            addr=4,
            section_index=0,
            start_offset=4,
            end_offset=5,
            stable_key="row-0",
            bytes=b"A",
            opcode_or_directive="dc.b",
            operand_text="$41",
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "representation.character",
            "context": _element_command_context(rows[0], "row-0:data_literal:4"),
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    representation = cast(dict[str, object], cast(dict[str, object], action["payload"])["representation"])

    assert action["kind"] == "create_manual_representation"
    assert representation["style"] == "character"
    assert representation["element_kind"] == "data_literal"
    assert representation["hunk"] == 0
    assert representation["addr"] == 4
    assert representation["end"] == 5
    assert representation["stable_key"] == "row-0"
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    named_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "element.seed.data.named",
            "context": _element_command_context(rows[0], "row-0:data_literal:4"),
            "parameters": {"name": "manual_byte"},
        },
    )
    named_action = cast(dict[str, object], cast(dict[str, object], named_payload["data"])["action"])
    named_seed = cast(dict[str, object], cast(dict[str, object], named_action["payload"])["seed"])

    assert named_seed["kind"] == "data"
    assert named_seed["name"] == "manual_byte"
    assert named_seed["data_role"] == "raw"
    assert named_seed["unit"] == "byte"
    assert named_seed["addr"] == 4
    assert named_seed["end"] == 5
    assert appended_actions == [action, named_action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_appends_library_base_semantic_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="jsr _LVOOpenLibrary(a6)\n",
            addr=0x120,
            section_index=0,
            start_offset=0x120,
            end_offset=0x124,
            stable_key="row-0",
            opcode_or_directive="jsr",
            operand_text="_LVOOpenLibrary(a6)",
            operand_parts=(
                SemanticOperand(
                    kind="symbol",
                    text="_LVOOpenLibrary",
                    base_register="A6",
                    metadata=SymbolOperandMetadata("_LVOOpenLibrary"),
                ),
            ),
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    catalog_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:symbol:0:_LVOOpenLibrary"),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], catalog_payload["data"])["commands"])
    assert any(action["action_id"] == "semantic.library_base.exec.library" for action in actions)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "semantic.library_base.exec.library",
            "context": _element_command_context(rows[0], "row-0:symbol:0:_LVOOpenLibrary"),
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    register_seed = cast(dict[str, object], cast(dict[str, object], action["payload"])["register_seed"])

    assert action["kind"] == "create_manual_register_seed"
    assert register_seed["entry_offset"] == 0x120
    assert register_seed["register"] == "A6"
    assert register_seed["kind"] == "library_base"
    assert register_seed["library_name"] == "exec.library"
    assert register_seed["struct_name"] == "LIB"
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_reports_and_executes_rsset_use_site_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rsset_binding_evidence = {
        "layout_name": "app",
        "base_symbol": "__amiga_app_base__",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "source_evidence_id": "prov-manual-rsset-a6",
        "source_family": "rsset_app_base",
        "source_evidence_status": "manual_override",
        "path_lifetime_scope": {"kind": "selected_use", "hunk": 0, "addr": 0xE2, "operand_index": 0},
        "confidence": "high",
        "conflicts": [{"source_evidence_id": "prov-stale-base"}],
        "parent_evidence_ids": ["prov-parent-a6"],
        "contradicted_evidence_id": "prov-stale-base",
        "reason": "selected use overrides stale base proof",
        "cleanup_scope": {"kind": "owned_descendants", "source_evidence_id": "prov-stale-base"},
    }
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="sf.b $0102(a6)\n",
            addr=0xE2,
            section_index=0,
            start_offset=0xE2,
            end_offset=0xE6,
            stable_key="row-0",
            opcode_or_directive="sf.b",
            operand_text="$0102(a6)",
            operand_parts=(SemanticOperand(kind="displacement", text="$0102(a6)", base_register="A6", displacement=0x0102),),
            operand_accesses=("write",),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="tst.b $0102(a6)\n",
            addr=0xF0,
            section_index=0,
            start_offset=0xF0,
            end_offset=0xF4,
            stable_key="row-1",
            opcode_or_directive="tst.b",
            operand_text="$0102(a6)",
            operand_parts=(SemanticOperand(kind="displacement", text="$0102(a6)", base_register="A6", displacement=0x0102),),
            operand_accesses=("read",),
        ),
    ]
    app_slot_analysis = {
        "regions": [
            {"offset": 0x0101, "end": 0x0102, "size": 1, "symbol": "app_0101", "source": "manual"},
            {"offset": 0x0103, "end": 0x0104, "size": 1, "symbol": "app_0103", "source": "manual"},
        ],
        "gaps": [{"start": 0x0102, "end": 0x0103, "after": "app_0101", "before": "app_0103"}],
    }
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(
        monkeypatch,
        "bloodwych",
        _RowsCListingArtifact(rows, app_slot_analysis=app_slot_analysis),
        cache_key="rsset-binding-report",
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    catalog_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:displacement:0:operand"),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], catalog_payload["data"])["commands"])
    report_action = next(action for action in actions if action["action_id"] == "rsset.binding.report")
    assert not any(action["action_id"] == "rsset.binding.bind" for action in actions)

    assert report_action["report"]["candidate"]["displacement"] == 0x0102
    assert report_action["report"]["candidate"]["base_evidence_id"] is None
    assert report_action["report"]["source_locator"]["row_text"] == "sf.b $0102(a6)"
    assert report_action["report"]["operand_facts"]["width_bytes"] == 1
    assert report_action["report"]["base_evidence"]["blockers"] == ["missing_base_evidence"]
    raw_base_ref = report_action["report"]["base_evidence_refs"][0]
    assert raw_base_ref["source_family"] == "unknown"
    assert raw_base_ref["status"] == "unresolved"
    assert raw_base_ref["accepted"] is False
    assert raw_base_ref.get("base_evidence_id") is None
    assert report_action["report"]["candidate_layouts"][0]["gap_covering_displacement"] == {
        "start": 0x0102,
        "end": 0x0103,
        "size": 1,
        "after": "app_0101",
        "before": "app_0103",
    }
    assert report_action["report"]["type_compatibility"]["width_fits_gap"] is True
    assert report_action["report"]["existing_xrefs"]["same_displacement_use_count"] == 2
    assert [use["row_text"] for use in report_action["report"]["existing_xrefs"]["same_displacement_uses"]] == [
        "sf.b $0102(a6)",
        "tst.b $0102(a6)",
    ]
    assert report_action["report"]["render"]["state"] == "linked_gap_or_raw"

    evidenced_query = _element_command_query(rows[0], "row-0:displacement:0:operand") | {
        key: [json.dumps(value) if isinstance(value, dict | list) else value]
        for key, value in rsset_binding_evidence.items()
    }
    catalog_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        evidenced_query,
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], catalog_payload["data"])["commands"])
    report_action = next(action for action in actions if action["action_id"] == "rsset.binding.report")
    bind_action = next(action for action in actions if action["action_id"] == "rsset.binding.bind")
    unbind_action = next(action for action in actions if action["action_id"] == "rsset.binding.unbind")

    assert report_action["report"]["candidate"]["displacement"] == 0x0102
    assert report_action["report"]["candidate"]["base_evidence_id"] == "selected-base:A6:__amiga_app_base__"
    assert report_action["report"]["base_evidence"]["has_explicit_evidence"] is True
    accepted_base_ref = report_action["report"]["base_evidence_refs"][0]
    assert accepted_base_ref["base_evidence_id"] == "selected-base:A6:__amiga_app_base__"
    assert accepted_base_ref["source_family"] == "rsset_app_base"
    assert accepted_base_ref["status"] == "manual_override"
    assert accepted_base_ref["source_evidence_id"] == "prov-manual-rsset-a6"
    assert accepted_base_ref["accepted"] is True
    assert accepted_base_ref["parent_evidence_ids"] == ["prov-parent-a6"]
    assert accepted_base_ref["conflicts"] == [{"source_evidence_id": "prov-stale-base"}]
    assert accepted_base_ref["contradicted_evidence_id"] == "prov-stale-base"
    assert accepted_base_ref["reason"] == "selected use overrides stale base proof"
    assert accepted_base_ref["cleanup_scope"] == {
        "kind": "owned_descendants",
        "source_evidence_id": "prov-stale-base",
    }
    assert accepted_base_ref["path_lifetime_scope"]["kind"] == "selected_use"
    assert report_action["report"]["verifier_readiness"]["replay"] == "ready"
    assert report_action["report"]["render"]["state"] == "linked_gap_or_raw"
    assert bind_action["parameters"] == {
        "layout_name": "app",
        "base_symbol": "__amiga_app_base__",
        "base_register": "A6",
        "base_evidence_id": "selected-base:A6:__amiga_app_base__",
        "displacement": 0x0102,
        "operand_index": 0,
    }
    assert unbind_action["parameters"] == bind_action["parameters"]

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "rsset.binding.bind",
            "context": _element_command_context(rows[0], "row-0:displacement:0:operand") | rsset_binding_evidence,
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    binding = cast(dict[str, object], cast(dict[str, object], action["payload"])["rsset_use_site_binding"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "create_manual_rsset_use_site_binding"
    assert (
        binding["rsset_use_site_binding_id"]
        == "rsset-binding-h0-000000E2-op0-A6-0102-app-__amiga_app_base__-selected-base_A6___amiga_app_base__"
    )
    assert binding["access"] == "write"
    assert binding["render_state"] == "linked_gap_or_raw"
    assert binding["source_evidence_id"] == accepted_base_ref["source_evidence_id"]
    assert binding["source_family"] == "rsset_app_base"
    assert binding["source_evidence_status"] == "manual_override"
    assert binding["path_lifetime_scope"] == accepted_base_ref["path_lifetime_scope"]
    assert binding["parent_evidence_ids"] == ["prov-parent-a6"]
    assert binding["conflicts"] == [{"source_evidence_id": "prov-stale-base"}]
    assert binding["contradicted_evidence_id"] == "prov-stale-base"
    assert binding["reason"] == "selected use overrides stale base proof"
    assert binding["cleanup_scope"] == accepted_base_ref["cleanup_scope"]
    assert binding["base_evidence_refs"] == [accepted_base_ref]
    assert local_effect["kind"] == "rsset_use_site_binding"

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "rsset.binding.unbind",
            "context": _element_command_context(rows[0], "row-0:displacement:0:operand") | rsset_binding_evidence,
        },
    )
    remove_action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    removed_binding = cast(dict[str, object], cast(dict[str, object], remove_action["payload"])["rsset_use_site_binding"])

    assert remove_action["kind"] == "remove_manual_rsset_use_site_binding"
    assert removed_binding["rsset_use_site_binding_id"] == binding["rsset_use_site_binding_id"]
    assert removed_binding["parent_evidence_ids"] == ["prov-parent-a6"]
    assert removed_binding["cleanup_scope"] == accepted_base_ref["cleanup_scope"]
    assert removed_binding["base_evidence_refs"] == [accepted_base_ref]
    assert appended_actions == [action, remove_action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_reports_lvo_register_provenance_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="jsr _LVOOpenLibrary(a6)\n",
            addr=0x120,
            section_index=0,
            start_offset=0x120,
            end_offset=0x124,
            stable_key="row-0",
            opcode_or_directive="jsr",
            operand_text="_LVOOpenLibrary(a6)",
            operand_parts=(
                SemanticOperand(
                    kind="symbol",
                    text="_LVOOpenLibrary",
                    base_register="A6",
                    metadata=SymbolOperandMetadata("_LVOOpenLibrary"),
                ),
            ),
        )
    ]
    _seed_c_listing_artifact(
        monkeypatch,
        "bloodwych",
        _RowsCListingArtifact(
            rows,
            api_calls_by_row_id={"r0": {"library": "exec.library", "function": "OpenLibrary", "inputs": []}},
        ),
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:symbol:0:_LVOOpenLibrary"),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])
    definition = next(action for action in actions if action["action_id"] == "provenance.definition.report")
    source_family = next(action for action in actions if action["action_id"] == "provenance.source_family.report")
    library_seed = next(action for action in actions if action["action_id"] == "semantic.library_base.exec.library")
    report = cast(dict[str, object], definition["report"])

    assert definition["appends_to_manual_action_log"] is False
    assert definition["effect"] == "inspection"
    assert report["source_family"] == "library_base"
    assert report["status"] == "analysis_proven"
    assert report["confidence"] == "high"
    assert cast(dict[str, object], report["subject"])["target"] == "bloodwych"
    assert cast(dict[str, object], report["subject"])["base_register"] == "A6"
    assert str(report["source_evidence_id"]).startswith(
        "prov-bloodwych-library_base-analysis_proven-h0-00000120-op0-A6-dn-lvo_api_operand-pn-entry"
    )
    assert cast(list[dict[str, object]], report["definitions"])[0]["library_name"] == "exec.library"
    assert source_family["parameters"] == {"source_evidence_id": report["source_evidence_id"], "focus": "source_family"}
    assert library_seed["parameters"]["source_evidence_id"] == report["source_evidence_id"]
    assert library_seed["parameters"]["source_family"] == "library_base"
    assert library_seed["parameters"]["source_evidence_status"] == "analysis_proven"

    with pytest.raises(disasm_server.CommandContractError) as exc:
        disasm_server.route_request(
            "POST",
            "/api/projects/bloodwych/commands/execute",
            {},
            {
                "command_id": "provenance.definition.report",
                "context": _element_command_context(rows[0], "row-0:symbol:0:_LVOOpenLibrary"),
            },
        )
    assert exc.value.code == "non_mutable_command"


def test_route_manual_action_catalog_reports_base_relative_provenance_uses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="sf.b $0102(a6)\n",
            addr=0xE2,
            section_index=0,
            start_offset=0xE2,
            end_offset=0xE6,
            stable_key="row-0",
            opcode_or_directive="sf.b",
            operand_text="$0102(a6)",
            operand_parts=(SemanticOperand(kind="displacement", text="$0102(a6)", base_register="A6", displacement=0x0102),),
            operand_accesses=("write",),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="tst.b $0102(a6)\n",
            addr=0xF0,
            section_index=0,
            start_offset=0xF0,
            end_offset=0xF4,
            stable_key="row-1",
            opcode_or_directive="tst.b",
            operand_text="$0102(a6)",
            operand_parts=(SemanticOperand(kind="displacement", text="$0102(a6)", base_register="A6", displacement=0x0102),),
            operand_accesses=("read",),
        ),
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:displacement:0:operand"),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])
    uses_action = next(action for action in actions if action["action_id"] == "provenance.uses.report")
    references_action = next(action for action in actions if action["action_id"] == "provenance.references.report")
    report = cast(dict[str, object], uses_action["report"])
    uses = cast(list[dict[str, object]], report["uses"])
    references = cast(list[dict[str, object]], cast(dict[str, object], references_action["report"])["references"])

    assert report["source_family"] == "unknown"
    assert report["status"] == "unresolved"
    assert cast(dict[str, object], report["subject"])["address_mode"] == "address_register_displacement"
    assert cast(dict[str, object], report["subject"])["displacement"] == 0x0102
    assert cast(dict[str, object], report["subject"])["width_bytes"] == 1
    assert [use["row_text"] for use in uses] == ["sf.b $0102(a6)", "tst.b $0102(a6)"]
    assert references_action["effect"] == "inspection"
    assert references_action["appends_to_manual_action_log"] is False
    assert references_action["parameters"] == {"source_evidence_id": report["source_evidence_id"], "focus": "references"}
    assert [ref["kind"] for ref in references] == ["register_base_use", "register_base_use"]
    assert [ref["row_text"] for ref in references] == ["sf.b $0102(a6)", "tst.b $0102(a6)"]
    assert all(ref["base_register"] == "A6" and ref["displacement"] == 0x0102 for ref in references)
    assert all(ref["consumers"] == ["rsset.binding", "semantic.register_seed"] for ref in references)
    assert {"command_id": "rsset.binding.report", "state": "report_only"} in report["possible_actions"]
    assert {"command_id": "provenance.classify_source", "state": "planned_write_boundary"} in report["possible_actions"]

    evidenced_query = _element_command_query(rows[0], "row-0:displacement:0:operand") | {
        "base_evidence_id": ["selected-base:A6:__amiga_app_base__"],
        "layout_name": ["app"],
        "base_symbol": ["__amiga_app_base__"],
    }
    evidenced_payload = disasm_server.route_request("GET", "/api/projects/bloodwych/commands", evidenced_query)
    evidenced_actions = cast(list[dict[str, object]], cast(dict[str, object], evidenced_payload["data"])["commands"])
    evidenced_report = cast(
        dict[str, object],
        next(action for action in evidenced_actions if action["action_id"] == "provenance.definition.report")["report"],
    )

    assert evidenced_report["source_family"] == "rsset_app_base"
    assert evidenced_report["status"] == "path_specific"
    assert "selected-base_A6___amiga_app_base__" in str(evidenced_report["source_evidence_id"])
    assert {"command_id": "rsset.binding.bind", "state": "available"} in evidenced_report["possible_actions"]


def test_route_manual_action_catalog_keeps_unrelated_displacements_report_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="move.w 36(a0),d0\n",
            addr=0x120,
            section_index=0,
            start_offset=0x120,
            end_offset=0x124,
            stable_key="row-0",
            opcode_or_directive="move.w",
            operand_text="36(a0),d0",
            operand_parts=(SemanticOperand(kind="displacement", text="36(a0)", base_register="A0", displacement=36),),
            operand_accesses=("read",),
            typed_accesses=(
                PlatformTypedAccess(
                    operand_index=0,
                    base_register="A0",
                    displacement=36,
                    field_offset=36,
                    root_struct_name="InputEvent",
                    owner_struct_name="InputEvent",
                    field_name="ie_Qualifier",
                    field_expr="ie_Qualifier",
                ),
            ),
        )
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    catalog_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:displacement:0:operand"),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], catalog_payload["data"])["commands"])

    assert any(action["action_id"] == "rsset.binding.report" for action in actions)
    assert not any(action["action_id"] in {"rsset.binding.bind", "rsset.binding.unbind"} for action in actions)
    report_action = next(action for action in actions if action["action_id"] == "rsset.binding.report")
    assert report_action["report"]["candidate"]["layout_name"] is None
    assert report_action["report"]["candidate"]["base_symbol"] is None
    assert report_action["report"]["base_evidence"]["blockers"] == ["missing_base_evidence"]


def test_route_manual_action_catalog_executes_api_specific_library_base_semantic_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            addr=0x140,
            section_index=0,
            start_offset=0x140,
            end_offset=0x144,
            stable_key="row-0",
            opcode_or_directive="jsr",
            operand_text="_LVOSetPointer(a6)",
            operand_parts=(
                SemanticOperand(
                    kind="symbol",
                    text="_LVOSetPointer",
                    base_register="A6",
                    metadata=SymbolOperandMetadata("_LVOSetPointer"),
                ),
            ),
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(
        monkeypatch,
        "bloodwych",
        _RowsCListingArtifact(
            rows,
            api_calls_by_row_id={"r0": {"library": "intuition.library", "function": "SetPointer", "inputs": []}},
        ),
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    catalog_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:symbol:0:_LVOSetPointer"),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], catalog_payload["data"])["commands"])
    assert any(action["action_id"] == "semantic.library_base.intuition.library" for action in actions)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "semantic.library_base.intuition.library",
            "context": _element_command_context(rows[0], "row-0:symbol:0:_LVOSetPointer"),
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    register_seed = cast(dict[str, object], cast(dict[str, object], action["payload"])["register_seed"])

    assert action["kind"] == "create_manual_register_seed"
    assert register_seed["entry_offset"] == 0x140
    assert register_seed["register"] == "A6"
    assert register_seed["kind"] == "library_base"
    assert register_seed["library_name"] == "intuition.library"
    assert register_seed["struct_name"] == "IntuitionBase"
    assert register_seed["context_name"] == "intuition.library"
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_rejects_library_base_semantic_action_without_lvo_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="moveq #1,d0\n",
            addr=0x120,
            section_index=0,
            start_offset=0x120,
            end_offset=0x122,
            stable_key="row-0",
            opcode_or_directive="moveq",
            operand_text="#1,d0",
            operand_parts=(SemanticOperand(kind="immediate", text="#1", value=1),),
        )
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:immediate:0:1"),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], payload["data"])["commands"])

    assert not any(str(action["action_id"]).startswith("semantic.library_base.") for action in actions)
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_execute_appends_struct_pointer_register_seed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="move.l (a1),d0\n",
            addr=0x160,
            section_index=0,
            start_offset=0x160,
            end_offset=0x162,
            stable_key="row-0",
            opcode_or_directive="move.l",
            operand_text="(a1),d0",
            operand_parts=(SemanticOperand(kind="register", text="a1", register="A1"),),
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    catalog_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:register:0:operand"),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], catalog_payload["data"])["commands"])
    struct_ptr_action = next(action for action in actions if action["action_id"] == "semantic.register.struct_ptr")

    assert struct_ptr_action["parameter_schema"]["required"] == ["struct_name"]
    assert struct_ptr_action["interaction_schema"]["type"] == "form"

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "semantic.register.struct_ptr",
            "context": _element_command_context(rows[0], "row-0:register:0:operand"),
            "parameters": {"struct_name": "IOStdReq", "context_name": "trackdisk.device"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    register_seed = cast(dict[str, object], cast(dict[str, object], action["payload"])["register_seed"])

    assert action["kind"] == "create_manual_register_seed"
    assert register_seed["entry_offset"] == 0x160
    assert register_seed["register"] == "A1"
    assert register_seed["kind"] == "struct_ptr"
    assert register_seed["library_name"] is None
    assert register_seed["struct_name"] == "IOStdReq"
    assert register_seed["context_name"] == "trackdisk.device"
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_manual_action_catalog_matches_equate_lvo_and_struct_offset_helpers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="move.l #65536,d0\n",
            addr=0x100,
            section_index=0,
            start_offset=0x100,
            end_offset=0x106,
            stable_key="row-0",
            opcode_or_directive="move.l",
            operand_text="#65536,d0",
            operand_parts=(SemanticOperand(kind="immediate", text="#65536", value=65536),),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="move.w #-552,d0\n",
            addr=0x106,
            section_index=0,
            start_offset=0x106,
            end_offset=0x10A,
            stable_key="row-1",
            opcode_or_directive="move.w",
            operand_text="#-552,d0",
            operand_parts=(SemanticOperand(kind="immediate", text="#-552", value=-552),),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="move.w #20,d0\n",
            addr=0x10A,
            section_index=0,
            start_offset=0x10A,
            end_offset=0x10E,
            stable_key="row-2",
            opcode_or_directive="move.w",
            operand_text="#20,d0",
            operand_parts=(SemanticOperand(kind="immediate", text="#20", value=20),),
        ),
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    equate_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], "row-0:immediate:0:65536"),
    )
    lvo_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[1], "row-1:immediate:0:-552"),
    )
    struct_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[2], "row-2:immediate:0:20"),
    )
    equate_actions = cast(list[dict[str, object]], cast(dict[str, object], equate_payload["data"])["commands"])
    lvo_actions = cast(list[dict[str, object]], cast(dict[str, object], lvo_payload["data"])["commands"])
    struct_actions = cast(list[dict[str, object]], cast(dict[str, object], struct_payload["data"])["commands"])

    equate_action = next(action for action in equate_actions if str(action["action_id"]).startswith("semantic.equate."))
    assert any(action["action_id"] == "semantic.lvo.exec.library_OpenLibrary" for action in lvo_actions)
    assert any(str(action["action_id"]).startswith("semantic.struct_offset.") for action in struct_actions)
    assert equate_action["default_key_binding"] == "s"
    assert equate_action["interaction_schema"]["type"] == "filtered_chooser"
    assert equate_action["interaction_schema"]["primary_rank"] == 30
    assert equate_action["interaction_schema"]["options"][0]["parameters"]["domain"] == "equate"

    execute_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {"command_id": equate_action["command_id"], "context": _element_command_context(rows[0], "row-0:immediate:0:65536")},
    )
    action = cast(dict[str, object], cast(dict[str, object], execute_payload["data"])["action"])
    hint = cast(dict[str, object], cast(dict[str, object], action["payload"])["semantic_hint"])

    assert action["kind"] == "create_manual_semantic_hint"
    assert hint["domain"] == "equate"
    assert hint["symbol"]
    assert hint["value"] == 65536
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_project_overlays_cached_analysis_review_blocker(monkeypatch: pytest.MonkeyPatch) -> None:
    class DecompressionBlockerArtifact(_FakeCListingArtifact):
        def analysis_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return (
                {
                    "sections": [],
                    "decompression_events": [
                        {
                            "event_id": "damocles-tetragon-child-2",
                            "status_id": 6,
                            "status": "needs_review_blocker",
                            "reason": "invalid_decompressed_entrypoint",
                            "source_section": 2,
                            "source_section_offset": 0x2A,
                        }
                    ],
                },
                {"generation": "fake-analysis"},
            )

    _seed_c_listing_artifact(monkeypatch, "bloodwych", DecompressionBlockerArtifact())
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "_current_reproduction_payload",
        lambda project_name: {"status": "not_ready"},
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych", {})
    data = cast(dict[str, object], payload["data"])
    project = cast(dict[str, object], data["project"])
    review_items = cast(list[dict[str, object]], project["review_items"])

    assert project["review_state"] == "blocked"
    assert review_items[0]["kind"] == "decompression_blocker"
    assert review_items[0]["review_blocker"] is True
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_project_reproduction_and_listing_include_review_warnings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [ListingRow(row_id="r0", kind="instruction", text="rts\n", addr=0)]
    project = replace(
        _binary_project("bloodwych", ready=True),
        review_state=ReviewState.BLOCKED,
        review_items=(
            {
                "kind": ReviewItemKind.MANUAL_ACTION_LOG_TARGET_MISMATCH,
                "item_id": "manual_action_log_target_mismatch:target",
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "message": "Manual Action Log target identity does not match current target",
            },
        ),
    )
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(
        disasm_server,
        "load_reproduction_report",
        lambda project_name, project_root=None: {"target": project_name, "status": "exact", "stale": False},
    )

    project_payload = disasm_server.route_request("GET", "/api/projects/bloodwych", {})
    project_data = cast(dict[str, object], project_payload["data"])
    repro_payload = disasm_server.route_request("GET", "/api/projects/bloodwych/reproduction", {})
    listing_payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})

    for data in (
        project_data,
        cast(dict[str, object], repro_payload["data"]),
        cast(dict[str, object], listing_payload["data"]),
    ):
        warnings = cast(list[dict[str, object]], data["review_warnings"])
        assert warnings[0]["review_state"] == "blocked"
        assert warnings[0]["blocker_count"] == 1
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_reproduction_read_run_and_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "load_reproduction_report",
        lambda project_name, project_root=None: {"target": project_name, "status": "exact"},
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_reproduction_job",
        lambda project_name, force=True: cast(
            disasm_server.AsyncJobPayload,
            {
                "job_id": "repro-1",
                "job_kind": "reproduction",
                "project_id": project_name,
                "result_project_id": project_name,
                "status": "queued",
                "phase_id": "queued",
                "phase_index": 0,
                "phase_count": 4,
                "progress_mode": "determinate",
                "progress_current": 0,
                "progress_total": 4,
                "progress_percent": 0,
                "total_rows": None,
                "error": None,
                "created_at": 1.0,
                "finished_at": None,
            },
        ),
    )
    disasm_server._ASYNC_JOBS["repro-1"] = cast(
        disasm_server.AsyncJobPayload,
        {
            "job_id": "repro-1",
            "job_kind": "reproduction",
            "project_id": "bloodwych",
            "result_project_id": "bloodwych",
            "status": "ready",
            "phase_id": "done",
            "phase_index": 4,
            "phase_count": 4,
            "progress_mode": "determinate",
            "progress_current": 4,
            "progress_total": 4,
            "progress_percent": 100,
            "total_rows": None,
            "error": None,
            "created_at": 1.0,
            "finished_at": 2.0,
        },
    )

    read_payload = disasm_server.route_request("GET", "/api/projects/bloodwych/reproduction", {})
    run_payload = disasm_server.route_request("POST", "/api/projects/bloodwych/reproduction/run", {})
    status_payload = disasm_server.route_request(
        "GET", "/api/projects/bloodwych/reproduction/status", {"job_id": ["repro-1"]}
    )

    assert cast(dict[str, object], read_payload["data"])["status"] == "exact"
    assert cast(dict[str, object], run_payload["data"])["job_kind"] == "reproduction"
    assert cast(dict[str, object], status_payload["data"])["status"] == "ready"
    disasm_server._ASYNC_JOBS.clear()


def test_route_reproduction_profile_list_show_set_without_manual_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "bloodwych"
    target_dir.mkdir(parents=True)
    updated: list[Path] = []
    disasm_server._ASYNC_JOBS["old-repro"] = cast(
        disasm_server.AsyncJobPayload,
        {
            "job_id": "old-repro",
            "job_kind": "reproduction",
            "project_id": "bloodwych",
            "result_project_id": "bloodwych",
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": 4,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": 4,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": 1.0,
            "finished_at": None,
        },
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=target_dir),
    )
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda path: updated.append(path))
    monkeypatch.setattr(
        disasm_server,
        "load_reproduction_report",
        lambda project_name, project_root=None: {"target": project_name, "status": "exact", "stale": True},
    )

    profiles_payload = disasm_server.route_request("GET", "/api/projects/bloodwych/reproduction/profiles", {})
    set_payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/reproduction/profile",
        {},
        {"profile_id": "source-vasm"},
    )
    show_payload = disasm_server.route_request("GET", "/api/projects/bloodwych/reproduction/profile", {})

    profiles = cast(list[dict[str, object]], cast(dict[str, object], profiles_payload["data"])["profiles"])
    set_data = cast(dict[str, object], set_payload["data"])
    show_data = cast(dict[str, object], show_payload["data"])
    options = cast(dict[str, object], set_data["options"])
    mutation = cast(dict[str, object], set_data["mutation"])
    reproduction_payload = cast(dict[str, object], set_data["reproduction"])
    policy_summary = cast(dict[str, object], reproduction_payload["policy_summary"])

    assert [profile["profile_id"] for profile in profiles] == [
        "exact-framework",
        "source-vasm",
        "source-devpac",
        "content-semantic",
    ]
    assert options["profile_id"] == "source-vasm"
    assert options["assembler"] == "our"
    assert options["oracle_modes"] == ["vasm"]
    assert mutation["durable_action_id"] == "target_metadata.reproduction"
    assert mutation["manual_action_log_count"] == 0
    assert policy_summary["profile_id"] == "source-vasm"
    assert show_data["profile_id"] == "source-vasm"
    assert updated == [target_dir]
    assert "old-repro" not in disasm_server._ASYNC_JOBS
    assert json.loads((target_dir / "target_metadata.json").read_text(encoding="utf-8"))["reproduction"]["profile_id"] == "source-vasm"
    assert not (target_dir / "target_ui_edits.json").exists()
    assert not (target_dir / "manual_actions.jsonl").exists()
    disasm_server._ASYNC_JOBS.clear()


def test_route_reproduction_policy_rejects_invalid_options(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "bloodwych"
    target_dir.mkdir(parents=True)
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=target_dir),
    )

    with pytest.raises(ValueError, match="invalid reproduction option 'assembler'"):
        disasm_server.route_request(
            "POST",
            "/api/projects/bloodwych/reproduction/policy",
            {},
            {"options": {"assembler": "vasm"}},
        )


def test_route_tool_capability_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    configured: list[dict[str, object]] = []
    monkeypatch.setattr(disasm_server, "runtime_tool_records", lambda project_root=None: [{"runtime_tool_id": "host", "status": "available"}])
    monkeypatch.setattr(disasm_server, "functional_tool_records", lambda project_root=None: [{"functional_tool_id": "vasm", "status": "missing"}])
    monkeypatch.setattr(
        disasm_server,
        "resolve_capability",
        lambda capability_id, project_root=None: {"capability_id": capability_id, "status": "missing"},
    )
    monkeypatch.setattr(
        disasm_server,
        "set_tool_artifact_path",
        lambda kind, tool_id, path, project_root=None: configured.append({"kind": kind, "tool_id": tool_id, "path": path})
        or {"version": 2, "runtime_tools": {}, "functional_tools": {tool_id: {"path": path}}},
    )

    runtimes_payload = disasm_server.route_request("GET", "/api/tools/runtimes", {})
    tools_payload = disasm_server.route_request("GET", "/api/tools/functional", {})
    capability_payload = disasm_server.route_request("GET", "/api/tools/capabilities/assemble_vasm_source", {})
    configure_payload = disasm_server.route_request(
        "POST",
        "/api/tools/configuration/path",
        {},
        {"kind": "functional", "tool_id": "vasm", "path": "tools/vasm"},
    )

    assert cast(list[dict[str, object]], cast(dict[str, object], runtimes_payload["data"])["runtimes"])[0]["runtime_tool_id"] == "host"
    assert cast(list[dict[str, object]], cast(dict[str, object], tools_payload["data"])["tools"])[0]["functional_tool_id"] == "vasm"
    assert cast(dict[str, object], capability_payload["data"])["capability_id"] == "assemble_vasm_source"
    assert cast(dict[str, object], cast(dict[str, object], configure_payload["data"])["functional_tools"])["vasm"] == {"path": "tools/vasm"}
    assert configured == [{"kind": "functional", "tool_id": "vasm", "path": "tools/vasm"}]


def test_route_project_tool_capabilities_for_profile_context(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))

    def availability(oracle_modes, *, project_root=None):
        calls.append(oracle_modes)
        return [{"capability_id": "assemble_devpac_source", "tool_id": "genam", "status": "missing", "missing_runtime_ids": ["vamos"]}]

    monkeypatch.setattr(disasm_server, "capability_availability_for_modes", availability)

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/tool-capabilities",
        {"profile_id": ["source-devpac"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert data["profile_id"] == "source-devpac"
    assert data["oracle_modes"] == ["devpac"]
    assert data["capability_ids"] == ["assemble_devpac_source"]
    assert cast(list[dict[str, object]], data["capabilities"])[0]["missing_runtime_ids"] == ["vamos"]
    assert calls == [["devpac"]]


def test_route_reproduction_stale_listing_artifact_exposes_background_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started: list[tuple[str, bool]] = []
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        "bloodwych",
        _FakeCListingArtifact(),
        cache_key="cache",
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(disasm_server, "_reproduction_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(
        disasm_server,
        "load_reproduction_report",
        lambda project_name, project_root=None: {
            "target": project_name,
            "status": "exact",
            "stale": True,
            "issues": [],
        },
    )

    def start_reproduction(project_name: str, force: bool = True) -> disasm_server.AsyncJobPayload:
        started.append((project_name, force))
        return cast(
            disasm_server.AsyncJobPayload,
            {
                "job_id": "repro-bg",
                "job_kind": "reproduction",
                "project_id": project_name,
                "result_project_id": project_name,
                "status": "queued",
                "phase_id": "queued",
                "phase_index": 0,
                "phase_count": 4,
                "progress_mode": "determinate",
                "progress_current": 0,
                "progress_total": 4,
                "progress_percent": 0,
                "total_rows": None,
                "error": None,
                "created_at": 1.0,
                "finished_at": None,
                "cache_key": "cache",
            },
        )

    monkeypatch.setattr(disasm_server, "_start_reproduction_job", start_reproduction)

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/reproduction", {})
    data = cast(dict[str, object], payload["data"])
    active_job = cast(dict[str, object], data["active_job"])

    assert started == [("bloodwych", False)]
    assert data["stale"] is True
    assert data["refreshing"] is True
    assert active_job["job_id"] == "repro-bg"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_project_returns_disk_manifest_for_disk_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_disk_manifest_payload()))

    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: ProjectRecord(
            id=project_name,
            name="demo_disk",
            kind=ProjectKind.DISK,
            target_dir=str(tmp_path),
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path=str(manifest_path),
            target_count=0,
            source_path="bin/demo.adf",
            disk_type="DOS",
            parent_project_id=None,
            target_type=None,
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T01:00:00+00:00",
        ),
    )

    payload = disasm_server.route_request("GET", "/api/projects/amiga_disk_demo_disk", {})

    data = cast(dict[str, object], payload["data"])
    project = cast(dict[str, object], data["project"])
    disk_manifest = cast(dict[str, object], data["disk_manifest"])

    assert payload["ok"] is True
    assert project["kind"] == "disk"
    assert disk_manifest["disk_id"] == "demo_disk"


def test_route_project_disk_browser_uses_common_disk_introspection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    extracted = tmp_path / "extracted" / "s" / "startup-sequence"
    extracted.parent.mkdir(parents=True)
    extracted.write_bytes(b"Echo")
    payload = _disk_manifest_payload()
    analysis = cast(dict[str, object], payload["analysis"])
    analysis["directories"] = [
        {
            "block_num": 42,
            "name": "s",
            "full_path": "s",
            "protection": "----rwed",
            "comment": None,
            "date": "2026-01-01T00:00:00",
            "hash_chain": 0,
            "parent": 880,
            "checksum_valid": True,
        }
    ]
    analysis["files"] = [
        {
            "block_num": 43,
            "name": "startup-sequence",
            "full_path": "s/startup-sequence",
            "size": 4,
            "protection": "----rwed",
            "comment": None,
            "date": "2026-01-01T00:00:00",
            "hash_chain": 0,
            "parent": 42,
            "extension_blocks": [],
            "data_blocks": [44],
            "data_block_count": 1,
            "checksum_valid": True,
            "extracted_path": str(extracted),
            "content": {"kind": "text", "size": 4, "sha256": "text-sha"},
        }
    ]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(payload))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: ProjectRecord(
            id=project_name,
            name="demo_disk",
            kind=ProjectKind.DISK,
            target_dir=str(tmp_path),
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path=str(manifest_path),
            target_count=0,
            source_path="bin/demo.adf",
            disk_type="DOS",
            parent_project_id=None,
            target_type=None,
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T01:00:00+00:00",
        ),
    )

    root = disasm_server.route_request("GET", "/api/projects/amiga_disk_demo_disk/disk-browser", {})
    child = disasm_server.route_request(
        "GET",
        "/api/projects/amiga_disk_demo_disk/disk-browser",
        {"path": ["s"]},
    )
    file_payload = disasm_server.route_request(
        "GET",
        "/api/projects/amiga_disk_demo_disk/disk-browser",
        {"path": ["s/startup-sequence"]},
    )

    root_entries = cast(list[dict[str, object]], cast(dict[str, object], root["data"])["entries"])
    child_data = cast(dict[str, object], child["data"])
    child_entries = cast(list[dict[str, object]], child_data["entries"])
    assert [entry["name"] for entry in root_entries] == ["s"]
    assert root_entries[0]["type"] == "directory"
    assert child_data["parent_path"] == ""
    assert child_entries[0]["name"] == "startup-sequence"
    assert child_entries[0]["size"] == 4
    assert child_entries[0]["type"] == "text"
    selected = cast(dict[str, object], cast(dict[str, object], file_payload["data"])["selected_entry"])
    content = cast(dict[str, object], selected["content"])
    assert content["text"] == "Echo"
    assert content["bytes"] == "45 63 68 6F"


def test_route_listing_rejects_disk_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_disk_manifest_payload()))
    disk_project = ProjectRecord(
        id="amiga_disk_demo_disk",
        name="demo_disk",
        kind=ProjectKind.DISK,
        target_dir=str(tmp_path),
        output_path=None,
        binary_path=None,
        ready=False,
        last_opened=None,
        manifest_path=str(manifest_path),
        target_count=0,
        source_path="bin/demo.adf",
        disk_type="DOS",
        parent_project_id=None,
        target_type=None,
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: disk_project)

    with pytest.raises(ValueError, match="does not expose a disassembly listing"):
        disasm_server.route_request("GET", "/api/projects/amiga_disk_demo_disk/listing", {})


def test_route_listing_open_rejects_disk_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_disk_manifest_payload()))
    disk_project = ProjectRecord(
        id="amiga_disk_demo_disk",
        name="demo_disk",
        kind=ProjectKind.DISK,
        target_dir=str(tmp_path),
        output_path=None,
        binary_path=None,
        ready=False,
        last_opened=None,
        manifest_path=str(manifest_path),
        target_count=0,
        source_path="bin/demo.adf",
        disk_type="DOS",
        parent_project_id=None,
        target_type=None,
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: disk_project)

    with pytest.raises(ValueError, match="does not expose a disassembly listing"):
        disasm_server.route_request("POST", "/api/projects/amiga_disk_demo_disk/listing/open", {}, {})


def test_route_create_project_from_adf_media(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_start_project_create_job",
        lambda body: {"job_id": "job-adf", "job_kind": "project_create", "status": "queued"},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects",
        {},
        {"filename": "demo.adf", "media_base64": "ZGVtbw=="},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-adf"
    assert data["job_kind"] == "project_create"


def test_route_create_project_from_executable_media(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_start_project_create_job",
        lambda body: {"job_id": "job-exe", "job_kind": "project_create", "status": "queued"},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects",
        {},
        {"filename": "bloodwych", "media_base64": "ZGVtbw=="},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-exe"
    assert data["job_kind"] == "project_create"


def test_route_corpus_features_query_xrefs_and_snippet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "list_projects", list)
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "feature_list",
        lambda: [{"feature": "hardware:custom", "target_count": 1, "occurrence_count": 2, "source_example_count": 1}],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "query_targets",
        lambda *, feature=None, group=None, platform=None, q=None, source_only=False, limit=None, offset=0, projects=None: [
            {
                "id": "platform_file_manifest:amiga-hunk/demo",
                "platform": platform,
                "count": 2,
                "source_example_count": 1,
                "feature": feature,
                "group": group,
                "q": q,
                "source_only": source_only,
                "limit": limit,
                "offset": offset,
            }
        ],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "query_xrefs",
        lambda *, target_id=None, feature=None, group=None, source_only=False, limit=None, offset=0: [
            {"id": "xref-1", "target_id": target_id, "feature": feature, "group": group, "row_index": 4, "limit": limit, "offset": offset}
        ],
    )
    snippet_args: list[tuple[str, int, int]] = []

    def fake_snippet_payload(xref_id: str, before: int = 20, after: int = 20) -> dict[str, object]:
        snippet_args.append((xref_id, before, after))
        return {
            "xref": {"id": xref_id},
            "start": 3,
            "end": 6,
            "highlighted_row_index": 4,
            "rows": [{"row_index": 4, "row_id": "r4", "text": "move.w _custom+intena,d0\n"}],
        }

    monkeypatch.setattr(disasm_server.corpus_usage, "snippet_payload", fake_snippet_payload)

    features = disasm_server.route_request("GET", "/api/corpus/features", {})
    query = disasm_server.route_request(
        "GET",
        "/api/corpus/query",
        {"feature": ["hardware:custom"], "group": ["hardware"], "platform": ["amiga-hunk"], "q": ["intena"], "source_only": ["1"], "limit": ["41"], "offset": ["40"]},
    )
    xrefs = disasm_server.route_request(
        "GET",
        "/api/corpus/xrefs",
        {"target_id": ["platform_file_manifest:amiga-hunk/demo"], "feature": ["hardware:custom"], "group": ["hardware"], "source_only": ["1"], "limit": ["121"], "offset": ["120"]},
    )
    snippet = disasm_server.route_request(
        "GET",
        "/api/corpus/snippet",
        {"xref_id": ["xref-1"], "before": ["0"], "after": ["0"]},
    )

    assert cast(list[dict[str, object]], features["data"])[0]["feature"] == "hardware:custom"
    assert cast(list[dict[str, object]], features["data"])[0]["source_example_count"] == 1
    assert cast(list[dict[str, object]], query["data"])[0]["platform"] == "amiga-hunk"
    assert cast(list[dict[str, object]], query["data"])[0]["source_example_count"] == 1
    assert cast(list[dict[str, object]], query["data"])[0]["group"] == "hardware"
    assert cast(list[dict[str, object]], query["data"])[0]["source_only"] is True
    assert cast(list[dict[str, object]], query["data"])[0]["limit"] == 41
    assert cast(list[dict[str, object]], query["data"])[0]["offset"] == 40
    assert cast(list[dict[str, object]], xrefs["data"])[0]["row_index"] == 4
    assert cast(list[dict[str, object]], xrefs["data"])[0]["limit"] == 121
    assert cast(list[dict[str, object]], xrefs["data"])[0]["offset"] == 120
    assert cast(dict[str, object], snippet["data"])["highlighted_row_index"] == 4
    assert snippet_args == [("xref-1", 0, 0)]
    assert cast(list[dict[str, object]], cast(dict[str, object], snippet["data"])["rows"])[0]["row_index"] == 4


def test_corpus_snippet_payload_preserves_explicit_row_indexes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_xrefs",
        lambda: [{"id": "xref-1", "target_id": "target-1", "row_index": 10}],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_manifest",
        lambda: [{"id": "target-1", "platform": "amiga-hunk", "origin": {"display_name": "demo"}}],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_snippet_rows",
        lambda: (_ for _ in ()).throw(AssertionError("snippet payload should load one target block")),
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_snippet_rows_for_target",
        lambda target_id: [
            {"target_id": "target-1", "row_index": 9, "row": {"text": "before"}},
            {"target_id": "target-1", "row_index": 10, "row": {"text": "hit"}},
            {"target_id": "target-1", "row_index": 12, "row": {"text": "sparse"}},
        ],
    )

    payload = disasm_server.corpus_usage.snippet_payload("xref-1", before=1, after=2)

    rows = cast(list[dict[str, object]], payload["rows"])
    assert [row["row_index"] for row in rows] == [9, 10, 12]
    assert payload["highlighted_row_index"] == 10


def test_route_corpus_variants_and_diff(monkeypatch: pytest.MonkeyPatch) -> None:
    left = {
        "id": "left-target",
        "platform": "amiga-hunk",
        "source_id": "left-source",
        "sha256": "left-sha",
        "size": 4,
        "origin": {"display_name": "Bloodwych [b2].zip", "in_image_path": "C/BLOODWYCH"},
        "feature_counts": {"hardware:custom": 1, "data:copper_list": 1},
    }
    right = {
        "id": "right-target",
        "platform": "amiga-hunk",
        "source_id": "right-source",
        "sha256": "right-sha",
        "size": 4,
        "origin": {"display_name": "Bloodwych [cr].zip", "in_image_path": "C/BLOODWYCH"},
        "feature_counts": {"hardware:custom": 2, "runtime:copied_code": 1},
    }
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: [left, right])
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_variants",
        lambda: [
            {
                "id": "variant-1",
                "platform": "amiga-hunk",
                "title_family": "bloodwych",
                "display_path": "C/BLOODWYCH",
                "target_count": 2,
                "unique_hash_count": 2,
                "targets": [
                    {"target_id": "left-target", "sha256": "left-sha", "origin": left["origin"]},
                    {"target_id": "right-target", "sha256": "right-sha", "origin": right["origin"]},
                ],
            }
        ],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "_target_media_bytes",
        lambda target: b"abcX" if target["id"] == "left-target" else b"abcY",
    )
    snippet_rows = [
        {"target_id": "left-target", "row_index": 0, "row": {"section_index": 0, "start_offset": 0, "text": "same_label:"}},
        {"target_id": "left-target", "row_index": 1, "row": {"section_index": 0, "start_offset": 3, "end_offset": 4, "text": "moveq #1,d0"}},
        {"target_id": "right-target", "row_index": 0, "row": {"section_index": 0, "start_offset": 0, "text": "same_label:"}},
        {"target_id": "right-target", "row_index": 1, "row": {"section_index": 0, "start_offset": 3, "end_offset": 4, "text": "moveq #2,d0"}},
    ]
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_snippet_rows_for_target",
        lambda target_id: [row for row in snippet_rows if row["target_id"] == target_id],
    )

    variants = disasm_server.route_request("GET", "/api/corpus/variants", {"target_id": ["left-target"]})
    diff = disasm_server.route_request(
        "GET",
        "/api/corpus/diff",
        {"left_target_id": ["left-target"], "right_target_id": ["right-target"]},
    )

    variant_data = cast(dict[str, object], variants["data"])
    diff_data = cast(dict[str, object], diff["data"])
    byte_diff = cast(dict[str, object], diff_data["byte_diff"])
    assert cast(dict[str, object], variant_data["group"])["id"] == "variant-1"
    assert cast(dict[str, object], diff_data["variant_group"])["id"] == "variant-1"
    assert [item["selected"] for item in cast(list[dict[str, object]], variant_data["variants"])] == [True, False]
    assert byte_diff["first_diff"] == 3
    assert byte_diff["region_count"] == 1
    regions = cast(list[dict[str, object]], byte_diff["regions"])
    assert regions[0]["left_start"] == 3
    assert regions[0]["right_start"] == 3
    assert regions[0]["skipped_left"] == 3
    assert regions[0]["skipped_right"] == 3
    assert "moveq #1,d0" in [row["text"] for row in cast(list[dict[str, object]], regions[0]["left_context"])]
    assert "moveq #2,d0" in [row["text"] for row in cast(list[dict[str, object]], regions[0]["right_context"])]


def test_corpus_diff_uses_listing_byte_space_not_raw_file_offsets(monkeypatch: pytest.MonkeyPatch) -> None:
    left = {"id": "left-target", "platform": "amiga-hunk", "origin": {"display_name": "left"}, "feature_counts": {}}
    right = {"id": "right-target", "platform": "amiga-hunk", "origin": {"display_name": "right"}, "feature_counts": {}}
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: [left, right])
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_variants",
        lambda: [
            {
                "id": "variant-1",
                "platform": "amiga-hunk",
                "title_family": "demo",
                "display_path": "C/DEMO",
                "targets": [{"target_id": "left-target"}, {"target_id": "right-target"}],
            }
        ],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "_target_media_bytes",
        lambda target: (b"raw-left-header" if target["id"] == "left-target" else b"different-raw-header") + b"\xaa\xef\xbb",
    )
    snippet_rows = [
        {
            "target_id": "left-target",
            "row_index": 0,
            "row": {
                "section_index": 0,
                "start_offset": 0,
                "end_offset": 3,
                "bytes": "aaefbb",
                "text": "\tdc.b $AA,$EF,$BB\n",
            },
        },
        {
            "target_id": "right-target",
            "row_index": 0,
            "row": {
                "section_index": 0,
                "start_offset": 0,
                "end_offset": 3,
                "bytes": "aaeebb",
                "text": "\tdc.b $AA,$EE,$BB\n",
            },
        },
    ]
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_snippet_rows_for_target",
        lambda target_id: [row for row in snippet_rows if row["target_id"] == target_id],
    )

    diff = disasm_server.corpus_usage.diff_payload("left-target", "right-target")

    byte_diff = cast(dict[str, object], diff["byte_diff"])
    regions = cast(list[dict[str, object]], byte_diff["regions"])
    assert byte_diff["left_space"] == "listing"
    assert byte_diff["right_space"] == "listing"
    assert byte_diff["left_size"] == 3
    assert byte_diff["right_size"] == 3
    assert byte_diff["first_diff"] == 1
    assert regions[0]["left_start"] == 1
    assert regions[0]["right_start"] == 1
    left_context = cast(list[dict[str, object]], regions[0]["left_context"])[0]
    assert left_context["diff_start_offset"] == 0
    assert left_context["diff_end_offset"] == 3


def test_corpus_listing_diff_space_expands_dcb_directives() -> None:
    rows = [
        {
            "section_index": 0,
            "row_index": 0,
            "start_offset": 0,
            "end_offset": 4,
            "bytes": "efef",
            "opcode_or_directive": "dcb.b",
            "operand_text": "4,$EF",
            "text": "\tdcb.b 4,$EF\n",
        }
    ]

    space = disasm_server.corpus_usage._listing_diff_space(rows)

    assert space is not None
    assert space["bytes"] == b"\xef\xef\xef\xef"
    mapped_rows = cast(list[dict[str, object]], space["rows"])
    assert mapped_rows[0]["diff_start_offset"] == 0
    assert mapped_rows[0]["diff_end_offset"] == 4


def test_corpus_diff_context_includes_preceding_rows_for_nearby_semantics() -> None:
    rows = [
        {"row_index": 0, "section_index": 0, "start_offset": 0, "end_offset": 4, "bytes": "11111111", "text": "\tmoveq #1,d0\n"},
        {"row_index": 1, "section_index": 0, "start_offset": 4, "end_offset": 8, "bytes": "22222222", "text": "\tmoveq #2,d0\n"},
        {"row_index": 2, "section_index": 0, "start_offset": 8, "end_offset": 12, "bytes": "33333333", "text": "\tmoveq #3,d0\n"},
        {"row_index": 3, "section_index": 0, "start_offset": 12, "end_offset": 16, "bytes": "44444444", "text": "\tmoveq #4,d0\n"},
    ]

    context = disasm_server.corpus_usage._source_rows_for_range(rows, 14, 15, limit=4, before=2)

    assert [row["row_index"] for row in context] == [1, 2, 3]


def test_corpus_byte_diff_merges_small_equal_runs_and_reports_skips() -> None:
    left = b"A" * 80 + b"abcd" + b"=" * 8 + b"wxyz" + b"B" * 80
    right = b"A" * 80 + b"ABCD" + b"=" * 8 + b"WXYZ" + b"B" * 80

    diff = disasm_server.corpus_usage._byte_diff_summary(left, right, merge_equal_gap=16)

    regions = cast(list[dict[str, object]], diff["regions"])
    assert diff["region_count"] == 1
    assert regions[0]["left_start"] == 80
    assert regions[0]["right_start"] == 80
    assert regions[0]["left_length"] == 16
    assert regions[0]["right_length"] == 16
    assert regions[0]["skipped_left"] == 80
    assert regions[0]["skipped_right"] == 80
    assert diff["trailing_skipped_left"] == 80
    assert diff["trailing_skipped_right"] == 80


def test_corpus_context_pairs_align_same_code_at_different_offsets() -> None:
    pairs = disasm_server.corpus_usage._paired_context_rows(
        [
            {"start_offset": 0x280, "end_offset": 0x284, "text": "\tmove.b ciaicr(a0),d0\n"},
            {"start_offset": 0x284, "end_offset": 0x286, "text": "\tandi.b #$7f,d0\n"},
        ],
        [
            {"start_offset": 0x25C, "end_offset": 0x260, "text": "\tmove.b ciaicr(a0),d0\n"},
            {"start_offset": 0x260, "end_offset": 0x266, "text": "\tandi.b #$7f,d0\n"},
        ],
    )

    assert len(pairs) == 2
    assert pairs[0]["same_text"] is True
    assert pairs[0]["same_offset"] is False
    assert cast(dict[str, object], pairs[0]["left"])["start_offset"] == 0x280
    assert cast(dict[str, object], pairs[0]["right"])["start_offset"] == 0x25C


def test_corpus_context_pairs_deemphasise_consistent_address_shift() -> None:
    pairs = disasm_server.corpus_usage._paired_context_rows(
        [
            {"start_offset": 0x1146, "end_offset": 0x114A, "opcode_or_directive": "bsr.w", "operand_text": "loc_0_00008576", "text": "\tbsr.w loc_0_00008576\n"},
            {"start_offset": 0x114A, "end_offset": 0x114E, "opcode_or_directive": "bsr.w", "operand_text": "loc_0_00008538", "text": "\tbsr.w loc_0_00008538\n"},
        ],
        [
            {"start_offset": 0x110A, "end_offset": 0x110E, "opcode_or_directive": "bsr.w", "operand_text": "loc_0_000084DA", "text": "\tbsr.w loc_0_000084DA\n"},
            {"start_offset": 0x110E, "end_offset": 0x1112, "opcode_or_directive": "bsr.w", "operand_text": "loc_0_0000849C", "text": "\tbsr.w loc_0_0000849C\n"},
        ],
    )

    assert [pair["diff_class"] for pair in pairs] == ["shifted_address", "shifted_address"]
    assert pairs[0]["dominant_delta"] == 0x9C
    assert "shifted address" in cast(str, pairs[0]["diff_label"])


def test_corpus_context_pairs_classify_immediate_and_addressing_mode_changes() -> None:
    pairs = disasm_server.corpus_usage._paired_context_rows(
        [
            {"start_offset": 0xACF, "end_offset": 0xAD4, "opcode_or_directive": "subi.l", "operand_text": "#60368,d0", "text": "\tsubi.l #60368,d0\n"},
            {"start_offset": 0x1A8, "end_offset": 0x1AE, "opcode_or_directive": "lea.l", "operand_text": "$00000060.l,a0", "text": "\tlea.l $00000060.l,a0\n"},
        ],
        [
            {"start_offset": 0xA92, "end_offset": 0xA98, "opcode_or_directive": "subi.l", "operand_text": "#60202,d0", "text": "\tsubi.l #60202,d0\n"},
            {"start_offset": 0x18E, "end_offset": 0x192, "opcode_or_directive": "lea.l", "operand_text": "$0060.w,a0", "text": "\tlea.l $0060.w,a0\n"},
        ],
    )

    assert pairs[0]["diff_class"] == "immediate_semantic"
    assert pairs[1]["diff_class"] == "addressing_mode"


def test_route_corpus_diff_rejects_unrelated_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_manifest",
        lambda: [
            {"id": "left-target", "platform": "amiga-hunk", "origin": {"display_name": "left"}},
            {"id": "right-target", "platform": "amiga-hunk", "origin": {"display_name": "right"}},
        ],
    )
    monkeypatch.setattr(disasm_server.corpus_usage, "read_variants", list)

    with pytest.raises(ValueError, match="not variants"):
        disasm_server.route_request(
            "GET",
            "/api/corpus/diff",
            {"left_target_id": ["left-target"], "right_target_id": ["right-target"]},
        )


def test_corpus_query_marks_existing_file_and_disk_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_rows = [
        {
            "id": "file-target",
            "platform": "amiga-hunk",
            "source_id": "file-row",
            "sha256": "file-sha",
            "size": 12,
            "feature_counts": {"hardware:custom": 1},
            "tags": ["hardware:custom"],
            "origin": {"in_image_path": "C/Run"},
        },
        {
            "id": "disk-target",
            "platform": "amiga-disk",
            "source_id": "disk-row",
            "sha256": "disk-sha",
            "size": 901120,
            "feature_counts": {"format:disk_image": 1},
            "tags": ["format:disk_image"],
            "origin": {"member_name": "Demo.adf"},
        },
    ]
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: manifest_rows)
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "read_xrefs",
        lambda: [{"id": "xref", "target_id": "file-target", "feature": "hardware:custom", "row_index": 3}],
    )

    def fake_read_jsonl(path: Path) -> list[dict[str, object]]:
        if path == disasm_server.corpus_usage.FILE_MANIFEST_PATH:
            return [{"id": "file-row", "disk_sha256": "disk-sha"}]
        return []

    monkeypatch.setattr(disasm_server.corpus_usage, "_read_jsonl_cached", fake_read_jsonl)

    rows = disasm_server.corpus_usage.query_targets(
        feature="hardware:custom",
        projects=[
            {"id": "project-file", "origin": {"kind": "user_upload", "platform": "amiga-hunk", "sha256": "file-sha", "size": 12}},
            {"id": "project-disk", "origin": {"kind": "user_upload", "platform": "amiga-disk", "sha256": "disk-sha", "size": 901120}},
        ],
    )

    assert len(rows) == 1
    coverage = cast(dict[str, object], rows[0]["project_coverage"])
    assert coverage["target_project_id"] == "project-file"
    assert coverage["disk_project_id"] == "project-disk"
    assert coverage["parent_disk_target_id"] == "disk-target"
    assert rows[0]["source_context"] == {
        "target_name": "C/Run",
        "disk_name": "Demo.adf",
        "disk_target_id": "disk-target",
    }


def test_corpus_disk_browser_lists_directories_first_and_file_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    disk_target = {
        "id": "disk-target",
        "platform": "amiga-disk",
        "source_id": "disk-row",
        "sha256": "disk-sha",
        "size": 901120,
        "origin": {"member_name": "Demo.adf"},
    }
    file_target = {
        "id": "file-run-target",
        "platform": "amiga-hunk",
        "source_id": "file-run-row",
        "sha256": "run-sha",
        "size": 12148,
        "origin": {"in_image_path": "run"},
    }
    disk_row = {
        "id": "disk-row",
        "platform": "amiga-disk",
        "origin": {"source_relpath": "resources/demo.adf"},
        "expect": {
            "inspect": {
                "entries": [
                    {"path": "Demo", "name": "Demo", "kind_name": "volume", "kind": 3},
                    {"path": "run", "name": "run", "kind_name": "file", "kind": 1, "byte_size": 12148, "content": {"kind": "amiga_hunk_executable", "target_type": "program", "size": 12148}},
                    {"path": "s", "name": "s", "kind_name": "directory", "kind": 2},
                    {"path": "s/startup-sequence", "name": "startup-sequence", "kind_name": "file", "kind": 1, "byte_size": 4, "extents": [{"image_offset": 0, "byte_size": 4}], "content": {"kind": "text", "size": 4}},
                ]
            }
        },
    }
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: [disk_target, file_target])
    monkeypatch.setattr(disasm_server.corpus_usage, "load_disk_image_bytes", lambda origin: b"Echo")
    monkeypatch.setattr(disasm_server, "list_projects", list)

    def fake_read_jsonl(path: Path) -> list[dict[str, object]]:
        if path == disasm_server.corpus_usage.DISK_MANIFEST_PATH:
            return [disk_row]
        if path == disasm_server.corpus_usage.FILE_MANIFEST_PATH:
            return [{"id": "file-run-row", "disk_sha256": "disk-sha", "origin": {"in_image_path": "run"}}]
        return []

    monkeypatch.setattr(disasm_server.corpus_usage, "_read_jsonl_cached", fake_read_jsonl)

    root = disasm_server.route_request("GET", "/api/corpus/disk", {"target_id": ["disk-target"]})
    root_data = cast(dict[str, object], root["data"])
    root_entries = cast(list[dict[str, object]], root_data["entries"])
    child = disasm_server.route_request("GET", "/api/corpus/disk", {"target_id": ["file-run-target"], "path": ["s"]})
    child_data = cast(dict[str, object], child["data"])
    child_entries = cast(list[dict[str, object]], child_data["entries"])
    selected = disasm_server.corpus_usage.disk_browser_payload("disk-target", "s/startup-sequence")

    assert root_data["path"] == ""
    disk = cast(dict[str, object], root_data["disk"])
    coverage = cast(dict[str, object], disk["project_coverage"])
    modes = cast(list[dict[str, object]], coverage["import_modes"])
    assert modes == [
        {
            "mode": "disk",
            "label": "Promote disk",
            "available": True,
            "covered_project_id": None,
            "corpus_target_id": "disk-target",
        }
    ]
    assert [entry["name"] for entry in root_entries] == ["s", "run"]
    assert root_entries[0]["is_directory"] is True
    assert root_entries[1]["size"] == 12148
    assert root_entries[1]["type"] == "Amiga HUNK program"
    assert root_entries[1]["target_id"] == "file-run-target"
    assert child_data["parent_path"] == ""
    assert [entry["name"] for entry in child_entries] == ["startup-sequence"]
    assert cast(dict[str, object], selected["selected_entry"])["name"] == "startup-sequence"
    assert selected["entries"] == []
    content = cast(dict[str, object], cast(dict[str, object], selected["selected_entry"])["content"])
    assert content["text"] == "Echo"
    assert content["bytes"] == "45 63 68 6F"


def test_corpus_import_disk_mode_for_file_imports_parent_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    file_target = {
        "id": "file-target",
        "platform": "amiga-hunk",
        "source_id": "file-row",
        "origin": {"in_image_path": "C/Run"},
    }
    disk_target = {
        "id": "disk-target",
        "platform": "amiga-disk",
        "source_id": "disk-row",
        "source_manifest": "platform_disk_manifest",
        "sha256": "disk-sha",
        "size": 901120,
        "origin": {"member_name": "Demo.adf", "source_relpath": "resources/Demo.zip"},
    }
    monkeypatch.setattr(disasm_server.corpus_usage, "read_manifest", lambda: [file_target, disk_target])

    def fake_read_jsonl(path: Path) -> list[dict[str, object]]:
        if path == disasm_server.corpus_usage.FILE_MANIFEST_PATH:
            return [{"id": "file-row", "disk_sha256": "disk-sha"}]
        if path == disasm_server.corpus_usage.DISK_MANIFEST_PATH:
            return [{"id": "disk-row", "origin": {"member_name": "Demo.adf"}}]
        return []

    monkeypatch.setattr(disasm_server.corpus_usage, "_read_jsonl_cached", fake_read_jsonl)
    monkeypatch.setattr(disasm_server.corpus_usage, "load_disk_image_bytes", lambda origin: b"disk-bytes")

    body = disasm_server.corpus_usage.corpus_import_media_body("file-target", mode="disk")

    assert body["filename"] == "Demo.adf"
    assert body["media_base64"] == "ZGlzay1ieXRlcw=="
    origin = cast(dict[str, object], body["project_origin"])
    assert origin["kind"] == "corpus_disk"
    assert origin["corpus_target_id"] == "disk-target"
    assert origin["requested_corpus_target_id"] == "file-target"


def test_route_corpus_import_uses_project_create_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "corpus_import_media_body",
        lambda target_id, mode="target": {"filename": f"{target_id}-{mode}.hunk", "media_base64": "ZGVtbw=="},
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_project_create_job",
        lambda body: {"job_id": "job-corpus", "job_kind": "project_create", "status": "queued", "filename": body["filename"]},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/corpus/import",
        {},
        {"target_id": "demo", "mode": "disk"},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-corpus"
    assert data["filename"] == "demo-disk.hunk"


def test_route_corpus_import_failure_returns_failed_project_job(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "corpus_import_media_body",
        lambda target_id, mode="target": (_ for _ in ()).throw(ValueError("cannot reconstruct")),
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/corpus/import",
        {},
        {"target_id": "missing"},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_kind"] == "project_create"
    assert data["status"] == "failed"
    assert data["error"] == "cannot reconstruct"
    disasm_server._ASYNC_JOBS.clear()


def test_route_project_create_status_returns_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_job_payload",
        lambda job_id: {"job_id": job_id, "status": "building", "phase_id": "analyze_disk"},
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/create/status",
        {"job_id": ["job-1"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["phase_id"] == "analyze_disk"


def test_route_delete_project(monkeypatch: pytest.MonkeyPatch) -> None:
    removed_projects: list[str] = []
    monkeypatch.setattr(disasm_server, "delete_project", lambda project_id: removed_projects.append(project_id))

    payload = disasm_server.route_request("POST", "/api/projects/demo/delete", {})

    assert payload["ok"] is True
    assert removed_projects == ["demo"]


def test_create_project_from_media_creates_executable_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "amiga_hunk_bloodwych"

    def fake_create_project(
        project_id: str,
        project_root: Path,
        *,
        origin: dict[str, object] | None = None,
    ) -> ProjectRecord:
        assert project_root == tmp_path
        assert origin is not None
        assert origin["kind"] == "user_upload"
        assert origin["filename"] == "Bloodwych"
        assert origin["platform"] == "amiga-hunk"
        assert origin["size"] == 4
        assert isinstance(origin["sha256"], str)
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / ".project.json").write_text(json.dumps({
            "schema_version": 2,
            "created_at": "2026-03-25T00:00:00+00:00",
            "updated_at": "2026-03-25T00:00:00+00:00",
            "origin": origin,
        }))
        return ProjectRecord(
            id=project_id,
            name=project_id,
            kind=ProjectKind.BINARY,
            target_dir=str(target_dir),
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path=None,
            target_count=None,
            source_path=None,
            disk_type=None,
            parent_project_id=None,
            target_type="program",
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T00:00:00+00:00",
        )

    monkeypatch.setattr(disasm_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        disasm_server,
        "validate_amiga_hunk_executable_with_c_backend",
        lambda path, project_root: None,
    )
    monkeypatch.setattr(disasm_server, "create_project", fake_create_project)
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name, project_root: _binary_project(project_name, ready=True),
    )

    project = disasm_server._create_project_from_media({
        "filename": "Bloodwych",
        "media_base64": "ZGVtbw==",
    })

    assert project.id == "amiga_hunk_bloodwych"
    assert (tmp_path / "bin" / "uploads" / "Bloodwych").read_bytes() == b"demo"
    payload = json.loads((target_dir / "source_binary.json").read_text())
    assert payload == {
        "kind": "hunk_file",
        "path": "bin/uploads/Bloodwych",
    }


def test_create_project_from_media_rejects_invalid_executable_with_c_backend(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(disasm_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        disasm_server,
        "validate_amiga_hunk_executable_with_c_backend",
        lambda path, project_root: (_ for _ in ()).throw(
            ValueError("Uploaded media is not an Amiga executable")
        ),
    )

    with pytest.raises(ValueError, match="Uploaded media is not an Amiga executable"):
        disasm_server._create_project_from_media({
            "filename": "Bloodwych",
            "media_base64": "ZGVtbw==",
        })

    assert not (tmp_path / "bin" / "uploads" / "Bloodwych").exists()


def test_create_project_from_media_creates_disk_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(disasm_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        disasm_server,
        "create_disk_project",
        lambda media_path, *, disk_id, project_root, progress_fn=None, origin=None: type("Manifest", (), {"disk_id": disk_id})(),
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name, project_root: ProjectRecord(
            id=project_name,
            name="bloodwych",
            kind=ProjectKind.DISK,
            target_dir="targets/amiga_disk_bloodwych",
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path="targets/amiga_disk_bloodwych/manifest.json",
            target_count=0,
            source_path="bin/uploads/Bloodwych.adf",
            disk_type="DOS",
            parent_project_id=None,
            target_type=None,
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T01:00:00+00:00",
        ),
    )

    project = disasm_server._create_project_from_media({
        "filename": "Bloodwych.adf",
        "media_base64": "ZGVtbw==",
    })

    assert project.id == "amiga_disk_bloodwych"
    assert (tmp_path / "bin" / "uploads" / "Bloodwych.adf").read_bytes() == b"demo"


def test_route_listing_returns_empty_payload_for_unready_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=False),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/demo/listing",
        {"addr": ["0x10"], "before": ["5"], "after": ["7"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["rows"] == []


def test_route_listing_raises_if_c_artifact_not_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    with pytest.raises(ValueError, match="C listing artifact not loaded"):
        disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})


def test_route_listing_returns_cached_window(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="moveq #0,d0\n",
            addr=0x10,
            structured_data={
                "struct_name": "RT",
                "field_name": "RT_MATCHWORD",
                "c_type": "UWORD",
                "value_domain": "exec.resident.matchword",
                "constant_name": "RTC_MATCHWORD",
            },
        )
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"addr": ["0x10"], "before": ["5"], "after": ["7"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert data["anchor_addr"] == 0x10
    assert rows_data[0]["row_key"] == "r0"
    assert "view_annotations" not in rows_data[0]
    assert rows_data[0]["structured_data"] == {
        "struct_name": "RT",
        "field_name": "RT_MATCHWORD",
        "c_type": "UWORD",
        "value_domain": "exec.resident.matchword",
        "constant_name": "RTC_MATCHWORD",
    }


def test_route_listing_marks_target_seeded_rows_suppressible(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="data",
            text="dc.b $00\n",
            section_index=0,
            start_offset=0x100,
            end_offset=0x101,
            addr=0x100,
        )
    ]
    target_dir = tmp_path / "bloodwych"
    target_dir.mkdir()
    (target_dir / "target_seeded_metadata.json").write_text(
        json.dumps(
            {
                "target_type": "program",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [],
                "seeded_entities": [
                    {
                        "addr": 0x100,
                        "end": 0x104,
                        "hunk": 0,
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "generated",
                        "source_id": "generated:entity",
                        "source_path": "targets/bloodwych/source.json",
                        "source_locator": "$.seeded_entities[0]",
                        "name": "seeded_data",
                    }
                ],
                "seeded_code_labels": [],
                "seeded_code_entrypoints": [],
                "absolute_code_labels": [],
                "entry_comments": [],
                "manual_representations": [],
                "execution_views": [],
                "suppressed_seeded_items": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=target_dir),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"start": ["0"], "count": ["1"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert rows_data[0]["suppressible_seeded_items"] == [
        {
            "kind": "seeded_entity",
            "hunk": 0,
            "addr": 0x100,
            "end": 0x104,
            "name": "seeded_data",
            "source_id": "generated:entity",
            "source_path": "targets/bloodwych/source.json",
            "source_locator": "$.seeded_entities[0]",
        }
    ]
    disasm_server._COMMAND_AVAILABILITY_CACHE.clear()
    command_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _row_command_query(rows[0]),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], command_payload["data"])["commands"])
    suppress_action = next(
        action for action in actions if action["action_id"] == "correction.suppress_seeded_item.seeded_entity"
    )
    assert suppress_action["parameters"] == {"kind": "seeded_entity", "hunk": 0, "addr": 0x100, "end": 0x104}
    rename_action = next(action for action in actions if action["action_id"] == "data_symbol.rename")
    assert rename_action["parameters"] == {
        "hunk": 0,
        "addr": 0x100,
        "end": 0x104,
        "previous_name": "seeded_data",
        "source_locator": "$.seeded_entities[0]",
    }
    assert rename_action["parameter_schema"]["required"] == ["name"]
    rename_existing_action = next(action for action in actions if action["action_id"] == "data_symbol.rename_existing")
    assert rename_existing_action["action"] == "rename_existing_data_symbol"
    assert rename_existing_action["parameters"] == rename_action["parameters"]
    edit_action = next(action for action in actions if action["action_id"] == "data_symbol.edit")
    assert edit_action["action"] == "rename_existing_data_symbol"
    assert edit_action["parameters"] == rename_action["parameters"]
    remove_action = next(action for action in actions if action["action_id"] == "data_symbol.remove")
    assert remove_action["parameters"] == {"kind": "seeded_entity", "hunk": 0, "addr": 0x100, "end": 0x104}


@pytest.mark.parametrize("command_id", ["data_symbol.rename", "data_symbol.rename_existing", "data_symbol.edit"])
def test_route_manual_action_catalog_execute_renames_seeded_data_symbol(
    command_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="data",
            text="dc.b $00\n",
            section_index=0,
            start_offset=0x100,
            end_offset=0x101,
            addr=0x100,
            stable_key="row-0",
        )
    ]
    target_dir = tmp_path / "bloodwych"
    target_dir.mkdir()
    (target_dir / "target_seeded_metadata.json").write_text(
        json.dumps(
            {
                "target_type": "program",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [],
                "seeded_entities": [
                    {
                        "addr": 0x100,
                        "end": 0x108,
                        "hunk": 0,
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "generated",
                        "source_id": "generated:entity-long",
                        "source_path": "targets/bloodwych/source.json",
                        "source_locator": "$.seeded_entities[0]",
                        "name": "seeded_data_long",
                    },
                    {
                        "addr": 0x100,
                        "end": 0x104,
                        "hunk": 0,
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "generated",
                        "source_id": "generated:entity",
                        "source_path": "targets/bloodwych/source.json",
                        "source_locator": "$.seeded_entities[1]",
                        "name": "seeded_data",
                    },
                ],
                "seeded_code_labels": [],
                "seeded_code_entrypoints": [],
                "absolute_code_labels": [],
                "entry_comments": [],
                "manual_representations": [],
                "execution_views": [],
                "suppressed_seeded_items": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=target_dir),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": command_id,
            "context": _row_command_context(rows[0]),
            "parameters": {"end": 0x104, "name": "player_table"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    data_symbol = cast(dict[str, object], cast(dict[str, object], action["payload"])["data_symbol"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "rename_data_symbol"
    assert data_symbol == {
        "data_symbol_id": "data-symbol:h0:00000100:00000104",
        "hunk": 0,
        "addr": 0x100,
        "end": 0x104,
        "previous_name": "seeded_data",
        "source_locator": "$.seeded_entities[1]",
        "name": "player_table",
    }
    assert local_effect == {"kind": "data_symbol_rename", "data_symbol": data_symbol}
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._COMMAND_AVAILABILITY_CACHE.clear()


def test_route_manual_action_catalog_execute_renames_referenced_data_symbol(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="lea $120(pc),a0\n",
            section_index=0,
            start_offset=0x20,
            end_offset=0x24,
            addr=0x20,
            stable_key="code-row",
            runtime_address_refs=(
                RuntimeAddressRef(
                    offset=0x20,
                    operand_index=0,
                    target_section_index=1,
                    target_offset=0x120,
                    runtime_address=0x40120,
                    confidence=2,
                    data_class="bitmap",
                    size=0x20,
                ),
            ),
        )
    ]
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    element_id = "code-row:data_ref:0:1:00000120"
    catalog_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _element_command_query(rows[0], element_id),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], catalog_payload["data"])["commands"])
    rename_action = next(action for action in actions if action["action_id"] == "data_symbol.rename")
    assert rename_action["parameters"] == {
        "source": "data_ref",
        "hunk": 1,
        "addr": 0x120,
        "end": 0x140,
        "data_class": "bitmap",
    }

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {
            "command_id": "data_symbol.rename",
            "context": _element_command_context(rows[0], element_id),
            "parameters": {"name": "player_bitmap"},
        },
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    data_symbol = cast(dict[str, object], cast(dict[str, object], action["payload"])["data_symbol"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "rename_data_symbol"
    assert data_symbol == {
        "data_symbol_id": "data-symbol:h1:00000120:00000140",
        "hunk": 1,
        "addr": 0x120,
        "end": 0x140,
        "data_class": "bitmap",
        "name": "player_bitmap",
    }
    assert local_effect == {"kind": "data_symbol_rename", "data_symbol": data_symbol}
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._COMMAND_AVAILABILITY_CACHE.clear()


def test_route_manual_action_catalog_execute_removes_seeded_data_symbol(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="data",
            text="dc.b $00\n",
            section_index=0,
            start_offset=0x100,
            end_offset=0x101,
            addr=0x100,
            stable_key="row-0",
        )
    ]
    target_dir = tmp_path / "bloodwych"
    target_dir.mkdir()
    (target_dir / "target_seeded_metadata.json").write_text(
        json.dumps(
            {
                "target_type": "program",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [],
                "seeded_entities": [
                    {
                        "addr": 0x100,
                        "end": 0x104,
                        "hunk": 0,
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "generated",
                        "source_id": "generated:entity",
                        "source_path": "targets/bloodwych/source.json",
                        "source_locator": "$.seeded_entities[0]",
                        "name": "seeded_data",
                    }
                ],
                "seeded_code_labels": [],
                "seeded_code_entrypoints": [],
                "absolute_code_labels": [],
                "entry_comments": [],
                "manual_representations": [],
                "execution_views": [],
                "suppressed_seeded_items": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=target_dir),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {"command_id": "data_symbol.remove", "context": _row_command_context(rows[0])},
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    suppressed = cast(dict[str, object], cast(dict[str, object], action["payload"])["suppressed_seeded_item"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])
    local_effect = cast(list[dict[str, object]], application["local_effects"])[0]

    assert action["kind"] == "suppress_seeded_item"
    assert suppressed == {"kind": "seeded_entity", "hunk": 0, "addr": 0x100, "end": 0x104}
    assert local_effect == {"kind": "seeded_item_suppression", "suppressed_seeded_item": suppressed}
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._COMMAND_AVAILABILITY_CACHE.clear()


def test_route_manual_action_catalog_execute_removes_manual_data_symbol_seed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="data",
            text="manual_data:\n    dc.b $00\n",
            section_index=0,
            start_offset=0x100,
            end_offset=0x101,
            addr=0x100,
            stable_key="row-0",
        )
    ]
    target_dir = tmp_path / "bloodwych"
    target_dir.mkdir()
    (target_dir / "target_seeded_metadata.json").write_text(
        json.dumps(
            {
                "target_type": "program",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "rsset_layout_regions": [],
                "seeded_entities": [
                    {
                        "addr": 0x100,
                        "end": 0x101,
                        "hunk": 0,
                        "seed_origin": "manual_analysis",
                        "review_status": "seeded",
                        "citation": "manual",
                        "source_id": "manual_action_log",
                        "source_path": "targets/bloodwych/manual_actions.jsonl",
                        "source_locator": "ManualSeed:manual-data-symbol-1",
                        "name": "manual_data",
                    }
                ],
                "seeded_code_labels": [],
                "seeded_code_entrypoints": [],
                "absolute_code_labels": [],
                "entry_comments": [],
                "manual_representations": [],
                "execution_views": [],
                "suppressed_seeded_items": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    appended_actions: list[dict[str, object]] = []

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"target_dir": str(target_dir), "kind": kind, "payload": payload}
        appended_actions.append(action)
        return action

    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: _binary_project(project_name, ready=True))
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=target_dir),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    command_payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/commands",
        _row_command_query(rows[0]),
    )
    actions = cast(list[dict[str, object]], cast(dict[str, object], command_payload["data"])["commands"])
    remove_action = next(action for action in actions if action["action_id"] == "data_symbol.remove")
    assert remove_action["action"] == "remove_manual_seed"
    assert remove_action["parameters"] == {"seed_id": "manual-data-symbol-1"}

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/commands/execute",
        {},
        {"command_id": "data_symbol.remove", "context": _row_command_context(rows[0])},
    )
    action = cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])
    application = cast(dict[str, object], cast(dict[str, object], payload["data"])["application"])

    assert action["kind"] == "remove_manual_seed"
    assert action["payload"] == {"seed_id": "manual-data-symbol-1"}
    assert application["status"] == "applied"
    assert appended_actions == [action]
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._COMMAND_AVAILABILITY_CACHE.clear()


def test_route_listing_returns_index_window(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id=f"r{index}", kind="instruction", text=f"moveq #{index},d0\n", addr=index * 2)
        for index in range(5)
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"start": ["2"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert data["start"] == 2
    assert data["end"] == 4
    assert data["total_rows"] == 5
    assert data["has_more_before"] is True
    assert data["has_more_after"] is True
    assert [row["row_key"] for row in rows_data] == ["r2", "r3"]


def test_route_listing_index_window_uses_c_artifact_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, int]] = []

    class FakeArtifact:
        def window_payload(self, *, start: int, count: int):
            calls.append((start, count))
            return (
                {
                    "anchor_addr": None,
                    "start": start,
                    "end": start + count,
                    "has_more_before": start > 0,
                    "has_more_after": True,
                    "total_rows": 5,
                    "analysis_generation": "full",
                    "rows": [
                        {
                            "row_id": "from-c",
                            "kind": "instruction",
                            "text": "\trts\n",
                            "addr": 4,
                            "source_context": {"kind": "core-block", "hunk_index": 0},
                        }
                    ],
                },
                {},
            )

    _seed_c_listing_artifact(monkeypatch, "bloodwych", FakeArtifact())
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"start": ["2"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert calls == [(2, 2)]
    assert rows_data[0]["row_key"] == "from-c"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_listing_anchor_code_uses_c_artifact_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, int]] = []

    class FakeArtifact:
        def anchor_window_payload(self, *, anchor_code: str, count: int):
            calls.append((anchor_code, count))
            return (
                {
                    "anchor_addr": None,
                    "start": 3,
                    "end": 5,
                    "has_more_before": True,
                    "has_more_after": True,
                    "total_rows": 8,
                    "analysis_generation": "full",
                    "rows": [
                        {
                            "row_id": "from-c-anchor",
                            "kind": "directive",
                            "text": "    SECTION section,code\n",
                            "addr": None,
                            "source_context": {},
                        }
                    ],
                },
                {},
            )

    _seed_c_listing_artifact(monkeypatch, "bloodwych", FakeArtifact())
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"anchor_code": ["SECTION section,code"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert calls == [("SECTION section,code", 2)]
    assert rows_data[0]["row_key"] == "from-c-anchor"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_listing_addr_window_uses_c_artifact_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int | None, int, int]] = []

    class FakeArtifact:
        def addr_window_payload(self, *, addr: int | None, before: int, after: int):
            calls.append((addr, before, after))
            return (
                {
                    "anchor_addr": addr,
                    "start": 1,
                    "end": 3,
                    "has_more_before": True,
                    "has_more_after": True,
                    "total_rows": 5,
                    "analysis_generation": "full",
                    "rows": [
                        {
                            "row_id": "from-c-addr",
                            "kind": "instruction",
                            "text": "\trts\n",
                            "addr": 4,
                            "source_context": {"kind": "core-block", "hunk_index": 0},
                        }
                    ],
                },
                {},
            )

    _seed_c_listing_artifact(monkeypatch, "bloodwych", FakeArtifact())
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"addr": ["4"], "before": ["1"], "after": ["1"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert calls == [(4, 1, 1)]
    assert rows_data[0]["row_key"] == "from-c-addr"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_route_listing_window_clamps_past_end(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id=f"r{index}", kind="instruction", text=f"moveq #{index},d0\n", addr=index * 2)
        for index in range(5)
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"start": ["999"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert data["start"] == 3
    assert data["end"] == 5
    assert data["total_rows"] == 5
    assert [row["row_key"] for row in rows_data] == ["r3", "r4"]


def test_listing_navigation_payload_uses_all_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0, label="start:"),
        ListingRow(row_id="r1", kind="instruction", text="rts\n", addr=2),
        ListingRow(row_id="r2", kind="label", text="far_target:\n", addr=2000, label="far_target:"),
    ]
    data = _test_listing_navigation_payload("bloodwych", rows)
    groups = cast(dict[str, list[dict[str, object]]], data["groups"])

    assert data["analysis_generation"] == "full"
    assert data["total_rows"] == 3
    assert [entry["summary"] for entry in groups["labels"]] == ["start:", "far_target:"]
    assert groups["labels"][1]["addr"] == 2000


def test_route_listing_navigation_uses_c_artifact_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _FakeCListingArtifact()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        "bloodwych",
        artifact,
        cache_key="cache",
    )
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing/navigation",
        {},
    )
    groups = cast(dict[str, list[dict[str, object]]], cast(dict[str, object], payload["data"])["groups"])

    assert payload["ok"] is True
    assert artifact.navigation_calls == 1
    assert [entry["summary"] for entry in groups["labels"]] == ["from_c:"]
    assert groups["manual-review"][0]["kind"] == "unreconciled_data_range"
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_listing_navigation_indexes_instruction_typed_accesses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="cmpi.w #36,LIB_VERSION(a0)\n",
            stable_key="typed-row",
            addr=0x30,
            typed_accesses=(
                PlatformTypedAccess(
                    operand_index=1,
                    base_register="A0",
                    displacement=20,
                    field_offset=20,
                    root_struct_name="Library",
                    owner_struct_name="Library",
                    field_name="LIB_VERSION",
                    field_expr="LIB_VERSION",
                ),
            ),
        )
    ]

    payload = _test_listing_navigation_payload("bloodwych", rows)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

    assert groups["typed-data"] == [
        {
            "addr": 0x30,
            "row_index": 0,
            "summary": "Library.LIB_VERSION",
            "match_text": "cmpi.w #36,LIB_VERSION(a0)",
            "stable_key": "typed-row",
        }
    ]


def test_listing_navigation_indexes_unresolved_typed_accesses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="cmpi.w #36,$0024(a0)\n",
            stable_key="gap-row",
            addr=0x34,
            unresolved_typed_accesses=(
                PlatformUnresolvedTypedAccess(
                    operand_index=1,
                    base_register="A0",
                    displacement=36,
                    struct_size=34,
                    root_struct_name="InputEvent",
                    classification="prefix_extension",
                    container_candidate_count=1,
                    container_struct_name="DerivedEvent",
                    container_field_expr="de_Field",
                    refinement_applied=True,
                    refined_struct_name="DerivedEvent",
                    type_provenance_kind="prefix_refinement",
                    type_provenance_section=0,
                    type_provenance_offset=0x34,
                ),
            ),
        )
    ]

    payload = _test_listing_navigation_payload("bloodwych", rows)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

    assert groups["typed-gaps"] == [
        {
            "addr": 0x34,
            "row_index": 0,
            "summary": "InputEvent+$0024 refines to DerivedEvent",
            "match_text": "cmpi.w #36,$0024(a0)",
            "stable_key": "gap-row",
            "root_struct_name": "InputEvent",
            "base_register": "A0",
            "operand_index": 1,
            "displacement": 36,
            "struct_size": 34,
            "classification": "prefix_extension",
            "container_candidate_count": 1,
            "container_struct_name": "DerivedEvent",
            "container_field_expr": "de_Field",
            "refinement_applied": True,
            "refined_struct_name": "DerivedEvent",
            "type_provenance_kind": "prefix_refinement",
            "type_provenance_section": 0,
            "type_provenance_offset": 0x34,
        }
    ]


def test_route_listing_navigation_indexes_label_definition_and_refs(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0, label="start"),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="bra.w target\n",
            addr=2,
            opcode_or_directive="bra.w",
            operand_text="target",
            operand_parts=(SemanticOperand(kind="symbol", text="target", metadata=SymbolOperandMetadata("target")),),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="move.l #target,d0\n",
            addr=6,
            opcode_or_directive="move.l",
            operand_text="#target,d0",
        ),
        ListingRow(
            row_id="r3",
            kind="instruction",
            text="move.l #target,d1\n",
            addr=8,
            opcode_or_directive="move.l",
            operand_text="#target,d1",
            operand_parts=(SemanticOperand(kind="symbol", text="target"),),
        ),
        ListingRow(row_id="r4", kind="label", text="target:\n", addr=10, label="target"),
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing/navigation",
        {},
    )
    data = cast(dict[str, object], payload["data"])
    groups = cast(dict[str, list[dict[str, object]]], data["groups"])
    target = groups["labels"][1]
    refs = cast(list[dict[str, object]], target["refs"])

    assert target["symbol"] == "target"
    assert target["ref_count"] == 2
    assert target["access_counts"] == {"definition": 1, "reference": 1}
    assert [(ref["access"], ref["row_index"]) for ref in refs] == [("reference", 1), ("definition", 4)]


def test_listing_navigation_api_calls_use_instruction_row_and_hunk_context() -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="moveq #0,d0\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
        ListingRow(
            row_id="r1",
            kind="label",
            text="loc_0010:\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="jsr loc_0100(pc)\t; KNOWN: local helper uses IntuitionBase _LVOSetPointer\n",
            addr=0x10,
            opcode_or_directive="jsr",
            operand_text="loc_0100(pc)",
            comment_text="KNOWN: local helper uses IntuitionBase _LVOSetPointer",
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r3",
            kind="instruction",
            text="moveq.l #_LVOSetPointer,d0\n",
            addr=0x12,
            opcode_or_directive="moveq.l",
            operand_text="#_LVOSetPointer,d0",
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r4",
            kind="instruction",
            text="bsr.w loc_dispatch\n",
            addr=0x14,
            opcode_or_directive="bsr.w",
            operand_text="loc_dispatch",
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
    ]
    api_calls_by_row_id = {
        "r2": {
            "library": "intuition.library",
            "function": "SetPointer",
            "note_kind": 3,
            "call_kind": 1,
            "inputs": [],
        },
        "r3": {
            "library": "intuition.library",
            "function": "SetPointer",
            "note_kind": 0,
            "call_kind": 1,
            "inputs": [],
        },
        "r4": {
            "library": "intuition.library",
            "function": "SetPointer",
            "note_kind": 1,
            "call_kind": 2,
            "inputs": [],
        },
    }

    payload = _test_listing_navigation_payload("bloodwych", rows, api_calls_by_row_id)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

    assert groups["api-calls"] == [
        {
            "addr": 0x12,
            "row_index": 3,
            "summary": "SetPointer (intuition.library)",
            "match_text": "moveq.l #_LVOSetPointer,d0",
            "stable_key": None,
            "hunk_index": 1,
        }
    ]


def test_listing_navigation_groups_app_slot_refs_by_symbol(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="move.l app_DOSBase(a6),d0\n",
            stable_key="app-read",
            addr=0x20,
            opcode_or_directive="move.l",
            operand_text="app_DOSBase(a6),d0",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_DOSBase", 0x26, "A6", 0, "read"),),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="move.l d0,app_0234(a6)\n",
            stable_key="app-write",
            addr=0x30,
            opcode_or_directive="move.l",
            operand_text="d0,app_0234(a6)",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_0234", 0x0234, "A6", 1, "write"),),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="lea.l app_0234(a6),a0\n",
            stable_key="app-address",
            addr=0x40,
            opcode_or_directive="lea.l",
            operand_text="app_0234(a6),a0",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_0234", 0x0234, "A6", 0, "address"),),
        ),
    ]

    app_slot_analysis = {
        "gap_count": 1,
        "slots": [
            {
                "symbol": "app_DOSBase",
                "base_registers": ["A6"],
                "width_counts": {"long": 1},
                "observed_size": 4,
                "observed_end": 0x2A,
                "first_row_index": 0,
                "last_row_index": 0,
                "first_addr": 0x20,
                "last_addr": 0x20,
            },
            {
                "symbol": "app_0234",
                "base_registers": ["A6"],
                "width_counts": {"long": 1},
                "observed_size": 4,
                "observed_end": 0x238,
                "first_row_index": 1,
                "last_row_index": 2,
                "first_addr": 0x30,
                "last_addr": 0x40,
            },
        ],
        "regions": [],
        "gaps": [],
        "field_gaps": [],
        "suggestions": [],
    }
    payload = _test_listing_navigation_payload("bloodwych", rows, app_slot_analysis=app_slot_analysis)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])
    app_slots = groups["app-slots"]
    app_slot_analysis_payload = cast(dict[str, object], payload["app_slot_analysis"])

    assert [entry["symbol"] for entry in app_slots] == ["app_DOSBase", "app_0234"]
    assert app_slots[0]["ref_count"] == 1
    assert app_slots[0]["access_counts"] == {"read": 1}
    assert app_slots[0]["width_counts"] == {"long": 1}
    assert app_slots[0]["observed_end"] == 0x2A
    assert app_slots[1]["ref_count"] == 2
    assert app_slots[1]["access_counts"] == {"write": 1, "address": 1}
    assert app_slots[1]["width_counts"] == {"long": 1}
    assert app_slots[1]["first_row_index"] == 1
    assert app_slots[1]["last_row_index"] == 2
    assert app_slot_analysis_payload["gap_count"] == 1
    refs = cast(list[dict[str, object]], app_slots[1]["refs"])
    assert [(ref["row_index"], ref["access"], ref["stable_key"]) for ref in refs] == [
        (1, "write", "app-write"),
        (2, "address", "app-address"),
    ]
    assert refs[0]["summary"] == "move.l d0,app_0234(a6)"


def test_listing_navigation_exposes_type_flow_analysis_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    type_flow_analysis = {
        "schema_version": 1,
        "target_id": "project_target:bloodwych",
        "pointer_chain_root_counts": {"app_slot": 2},
        "chains": [{"kind": "register_to_app_slot_reload", "count": 2}],
    }
    payload = _test_listing_navigation_payload("bloodwych", [], type_flow_analysis=type_flow_analysis)

    assert payload["type_flow_analysis"] == {
        "schema_version": 1,
        "target_id": "project_target:bloodwych",
        "pointer_chain_root_counts": {"app_slot": 2},
        "chains": [{"kind": "register_to_app_slot_reload", "count": 2}],
    }


def test_listing_navigation_exposes_rsset_layout_regions_and_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "_active_reproduction_report", lambda project_name: None)
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="lea.l app_input_event(a6),a1\n",
            stable_key="input-event-address",
            addr=0x10,
            opcode_or_directive="lea.l",
            operand_text="app_input_event(a6),a1",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_input_event", 0x100, "A6", 0, "address"),),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr _LVORawKeyConvert(a6)\n",
            stable_key="rawkeyconvert",
            addr=0x14,
            opcode_or_directive="jsr",
            operand_text="_LVORawKeyConvert(a6)",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="move.b app_after_event(a6),d0\n",
            stable_key="after-event",
            addr=0x18,
            opcode_or_directive="move.b",
            operand_text="app_after_event(a6),d0",
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_after_event", 0x120, "A6", 0, "read"),),
        ),
    ]
    app_slot_analysis = {
        "regions": [
            {
                "source": "platform_api_arg",
                "symbol": "app_input_event",
                "offset": 0x100,
                "end": 0x116,
                "size": 22,
                "confidence": "tool-inferred",
                "struct_name": "InputEvent",
                "field_refs": [{"field_path": ["ie_Code"]}],
                "evidence": [{"row_index": 1, "addr": 0x14, "hunk_index": 0}],
            }
        ],
        "gaps": [
            {
                "start": 0x116,
                "end": 0x120,
                "size": 10,
                "after": "app_slot_region_0100_InputEvent",
                "before": "app_slot_observed_app_after_event",
                "coverage": "unknown_app_slot_space",
            }
        ],
        "field_gaps": [
            {
                "start": 0x108,
                "end": 0x10A,
                "size": 2,
                "coverage": "known_struct_field",
                "field_path": ["ie_Qualifier"],
                "region_id": "app_slot_region_0100_InputEvent",
                "symbol": "app_input_event",
                "struct_name": "InputEvent",
            }
        ],
        "suggestions": [
            {
                "summary": "app_input_event at app+0x100 matches InputEvent from platform API usage",
                "action": "add_target_metadata",
                "confidence": "tool-inferred",
                "metadata": {
                    "symbol": "app_input_event",
                    "offset": 0x100,
                    "size": 22,
                    "struct_name": "InputEvent",
                    "storage_kind": "struct_instance",
                },
                "evidence": [{"row_index": 1, "addr": 0x14, "hunk_index": 0}],
            }
        ],
        "untyped_api_args": [
            {
                "symbol": "app_key_buffer",
                "displacement": 0x140,
                "function": "RawKeyConvert",
                "input_name": "buffer",
                "register": "A1",
                "type_name": "STRPTR",
                "reason": "missing_struct_metadata",
                "row_index": 1,
                "addr": 0x14,
                "hunk_index": 0,
                "stable_key": "call-row",
                "source_stable_key": "lea-row",
            }
        ],
    }

    payload = _test_listing_navigation_payload("input-demo", rows, app_slot_analysis=app_slot_analysis)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

    assert groups["app-slot-regions"] == [
        {
            "summary": "app_input_event: InputEvent $0100-$0116",
            "match_text": "app_input_event",
            "symbol": "app_input_event",
            "offset": 0x100,
            "end": 0x116,
            "size": 22,
            "source": "platform_api_arg",
            "confidence": "tool-inferred",
            "struct_name": "InputEvent",
            "field_ref_count": 1,
            "field_paths": ["InputEvent.ie_Code"],
            "row_index": 1,
            "addr": 0x14,
            "hunk_index": 0,
        }
    ]
    assert groups["app-slot-gaps"] == [
        {
            "summary": "Gap $0116-$0120 (10 bytes)",
            "match_text": "",
            "navigable": False,
            "start": 0x116,
            "end": 0x120,
            "size": 10,
            "after": "app_slot_region_0100_InputEvent",
            "before": "app_slot_observed_app_after_event",
            "coverage": "unknown_app_slot_space",
        }
    ]
    assert groups["app-slot-field-gaps"] == [
        {
            "summary": "Field gap $0108-$010A (2 bytes) InputEvent.ie_Qualifier",
            "match_text": "InputEvent.ie_Qualifier",
            "navigable": False,
            "start": 0x108,
            "end": 0x10A,
            "size": 2,
            "coverage": "known_struct_field",
            "field_path": ["ie_Qualifier"],
            "region_id": "app_slot_region_0100_InputEvent",
            "symbol": "app_input_event",
            "struct_name": "InputEvent",
        }
    ]
    suggestions = groups["app-slot-suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["action"] == "add_target_metadata"
    assert suggestions[0]["symbol"] == "app_input_event"
    assert suggestions[0]["offset"] == 0x100
    assert suggestions[0]["struct_name"] == "InputEvent"
    assert suggestions[0]["row_index"] == 1
    assert cast(dict[str, object], suggestions[0]["metadata"])["storage_kind"] == "struct_instance"
    api_args = groups["app-slot-api-args"]
    assert len(api_args) == 1
    assert api_args[0]["summary"] == "app_key_buffer -> RawKeyConvert buffer A1 (missing_struct_metadata)"
    assert api_args[0]["symbol"] == "app_key_buffer"
    assert api_args[0]["register"] == "A1"
    assert api_args[0]["type_name"] == "STRPTR"
    assert api_args[0]["row_index"] == 1
    assert api_args[0]["stable_key"] == "call-row"
    assert api_args[0]["source_stable_key"] == "lea-row"


def test_route_listing_navigation_rejects_stale_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        "bloodwych",
        _RowsCListingArtifact(
            [ListingRow(row_id="r0", kind="label", text="stale:\n", addr=0, label="stale:")]
        ),
        cache_key="old-cache",
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "_project_listing_cache_key",
        lambda project_name: "new-cache",
    )

    with pytest.raises(ValueError, match="C listing artifact not loaded"):
        disasm_server.route_request(
            "GET",
            "/api/projects/bloodwych/listing/navigation",
            {},
        )

    assert disasm_server._LISTING_PROJECTION_SERVICE.artifact_for_test("bloodwych") is None
    assert disasm_server._LISTING_PROJECTION_SERVICE.cache_key_for_test("bloodwych") is None


def test_route_listing_allows_projection_dirty_window_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="abs_0_0001001E:\n",
            addr=0x1001E,
            runtime_address=0x1001E,
            section_index=0,
            start_offset=0x1E,
            end_offset=0x1E,
            label="abs_0_0001001E",
            stable_key="label-row",
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="move.b (a0)+,(a2)+\n",
            addr=0x1001E,
            runtime_address=0x1001E,
            section_index=0,
            start_offset=0x1E,
            end_offset=0x20,
        ),
    ]
    project = replace(
        _binary_project("bloodwych", ready=True),
        manual_state={
            "labels": [
                {
                    "label_id": "catalog-label-source-h0-0000001E",
                    "name": "wrong_source_label",
                    "address_domain": "source",
                    "hunk": 0,
                    "addr": 0x1E,
                    "row_index": 0,
                    "stable_key": "label-row",
                },
                {
                    "label_id": "catalog-label-runtime-h0-0001001E",
                    "name": "renamed_label",
                    "address_domain": "runtime",
                    "hunk": 0,
                    "addr": 0x1001E,
                    "stable_key": "label-row",
                }
            ],
            "comments": [
                {
                    "comment_id": "c1",
                    "text": "confirmed copy loop",
                    "hunk": 0,
                    "addr": 0x1E,
                }
            ],
        },
    )
    artifact = _RowsCListingArtifact(rows)
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        "bloodwych",
        artifact,
        cache_key="old-cache",
    )
    disasm_server._LISTING_PROJECTION_SERVICE.mark_presentation_dirty("bloodwych")
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "new-cache")
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"start": ["0"], "count": ["2"]},
    )
    data = cast(dict[str, object], payload["data"])
    returned_rows = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert returned_rows[0]["label"] == "renamed_label"
    assert returned_rows[0]["text"] == "renamed_label:\n"
    assert returned_rows[0]["manual_label_id"] == "catalog-label-runtime-h0-0001001E"
    assert returned_rows[0]["manual_label_address_domain"] == "runtime"
    assert returned_rows[0]["comment_text"] == "confirmed copy loop"
    assert disasm_server._LISTING_PROJECTION_SERVICE.artifact_for_test("bloodwych") is artifact
    assert disasm_server._LISTING_PROJECTION_SERVICE.is_presentation_dirty("bloodwych")


def test_project_listing_cache_key_includes_renderer_tool_stamps(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_path = tmp_path / "demo.bin"
    binary_path.write_bytes(b"\x4e\x75")
    source = SimpleNamespace(
        kind=BinarySourceKind.HUNK_FILE,
        display_path="demo.bin",
        path=binary_path,
    )
    stamp = {"value": "a"}
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root: SimpleNamespace(
            target_dir=target_dir,
            binary_source=source,
        ),
    )
    monkeypatch.setattr(disasm_server, "effective_metadata_hash", lambda target_dir: "metadata")
    monkeypatch.setattr(disasm_server, "source_renderer_tool_stamps", lambda project_root: {"renderer": stamp["value"]})

    first = disasm_server._project_listing_cache_key("demo")
    stamp["value"] = "b"
    second = disasm_server._project_listing_cache_key("demo")

    assert first != second


def test_route_listing_adds_api_call_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            addr=0x814E,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        )
    ]
    _seed_c_listing_artifact(
        monkeypatch,
        "bloodwych",
        _RowsCListingArtifact(
            rows,
            api_calls_by_row_id={
                "r0": {
                    "library": "intuition.library",
                    "function": "SetPointer",
                    "inputs": [
                        {
                            "name": "pointer",
                            "regs": ["A1"],
                            "type": "UWORD *",
                            "i_struct": None,
                            "source": "parsed NDK",
                        }
                    ],
                }
            },
        ),
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert rows_data[0]["api_call"] == {
        "library": "intuition.library",
        "function": "SetPointer",
        "inputs": [
            {
                "name": "pointer",
                "regs": ["A1"],
                "type": "UWORD *",
                "i_struct": None,
                "source": "parsed NDK",
            }
        ],
    }


def test_route_listing_does_not_attach_api_call_metadata_to_label_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="loc_0010:\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
    ]
    _seed_c_listing_artifact(
        monkeypatch,
        "bloodwych",
        _RowsCListingArtifact(
            rows,
            api_calls_by_row_id={
                "r1": {
                    "library": "intuition.library",
                    "function": "SetPointer",
                    "inputs": [],
                }
            },
        ),
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert "api_call" not in rows_data[0]
    assert rows_data[1]["api_call"] == {
        "library": "intuition.library",
        "function": "SetPointer",
        "inputs": [],
    }


def test_route_listing_does_not_cross_apply_api_call_metadata_between_hunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="moveq #1,d0\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr _LVOOpenLibrary(a6)\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=3),
        ),
    ]
    _seed_c_listing_artifact(
        monkeypatch,
        "bloodwych",
        _RowsCListingArtifact(
            rows,
            api_calls_by_row_id={
                "r1": {
                    "library": "exec.library",
                    "function": "OpenLibrary",
                    "inputs": [],
                }
            },
        ),
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert "api_call" not in rows_data[0]
    assert rows_data[1]["api_call"] == {
        "library": "exec.library",
        "function": "OpenLibrary",
        "inputs": [],
    }


def test_route_type_catalog_returns_known_structs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "type_catalog_from_c_backend",
        lambda project_name: [
            {"name": "SimpleSprite", "source": "graphics/sprite.i", "size": 12},
            {"name": "Window", "source": "intuition/intuition.i", "size": 34},
        ],
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/api/type-catalog", {})
    data = cast(list[dict[str, object]], payload["data"])

    assert payload["ok"] is True
    assert data[0]["name"] == "SimpleSprite"
    assert data[0]["source"] == "graphics/sprite.i"


def test_route_patch_api_input_struct_writes_global_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    corrections_path = tmp_path / "amiga_ndk_corrections.json"
    corrections_path.write_text(json.dumps({
        "_meta": {
            "absolute_symbols": [],
            "api_input_semantic_assertions": [],
            "api_input_type_overrides": [],
            "api_input_value_bindings": [],
            "struct_field_value_bindings": [],
            "value_domains": {},
        },
        "libraries": {},
        "structs": {},
        "constants": {},
    }))
    monkeypatch.setattr(disasm_server, "_OS_CORRECTIONS_PATH", corrections_path)
    monkeypatch.setattr(
        disasm_server,
        "validate_api_input_struct_with_c_backend",
        lambda project_name, library, function, input_name, struct_name: {
            "library": library,
            "function": function,
            "input": input_name,
            "type": f"struct {struct_name} *",
            "i_struct": struct_name,
            "source": "global correction",
            "struct_source": "graphics/sprite.i",
        },
    )

    payload = disasm_server.route_request(
        "PATCH",
        "/api/projects/bloodwych/api/functions/intuition.library/SetPointer/inputs/pointer/struct",
        {},
        {"struct_name": "SimpleSprite"},
    )
    data = cast(dict[str, object], payload["data"])
    persisted = json.loads(corrections_path.read_text())

    assert payload["ok"] is True
    assert data["type"] == "struct SimpleSprite *"
    assert data["struct_source"] == "graphics/sprite.i"
    overrides = persisted["_meta"]["api_input_type_overrides"]
    assert overrides == [{
        "citation": "User-edited via disasm UI",
        "function": "SetPointer",
        "i_struct": "SimpleSprite",
        "input": "pointer",
        "library": "intuition.library",
        "review_status": "validated",
        "seed_origin": "manual",
        "type": "struct SimpleSprite *",
    }]


def test_route_listing_open_starts_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_listing_job",
        lambda project_name: {
            "job_id": "job-full",
            "project_id": project_name,
            "status": "queued",
        },
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/listing/open",
        {},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-full"


def test_start_listing_job_ignores_stale_ready_job_without_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeThread:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def start(self) -> None:
            pass

    monkeypatch.setattr(disasm_server.threading, "Thread", FakeThread)
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["stale-job"] = {
        "job_id": "stale-job",
        "job_kind": "listing_artifact",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "ready",
        "phase_id": "done",
        "phase_index": 2,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 2,
        "progress_total": 2,
        "progress_percent": 100,
        "total_rows": 10,
        "error": None,
        "created_at": 1.0,
        "finished_at": 1.0,
    }

    payload = disasm_server._start_listing_job("bloodwych")

    assert payload["job_id"] != "stale-job"
    assert payload["status"] in {"queued", "building"}


def test_build_rows_job_can_use_c_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    build_calls: list[tuple[str, str]] = []
    artifact = _FakeCListingArtifact()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["job-1"] = {
        "job_id": "job-1",
        "job_kind": "listing_artifact",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }
    monkeypatch.setattr(
        disasm_server,
        "build_project_listing_artifact_profile",
        lambda project_name: build_calls.append(project_name) or (1, {}, artifact),
    )

    disasm_server._build_rows_job("job-1", "bloodwych")

    assert disasm_server._LISTING_PROJECTION_SERVICE.artifact_for_test("bloodwych") is artifact
    assert artifact.closed is False
    assert build_calls == ["bloodwych"]
    assert disasm_server._ASYNC_JOBS["job-1"]["status"] == "ready"


def test_build_rows_job_reports_unsupported_c_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["job-1"] = {
        "job_id": "job-1",
        "job_kind": "listing_artifact",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }

    def fail(project_name: str) -> tuple[int, dict[str, object], _FakeCListingArtifact]:
        raise UnsupportedCBackendProject("unsupported project")

    monkeypatch.setattr(disasm_server, "build_project_listing_artifact_profile", fail)

    disasm_server._build_rows_job("job-1", "bloodwych")

    assert disasm_server._ASYNC_JOBS["job-1"]["status"] == "failed"
    assert disasm_server._ASYNC_JOBS["job-1"]["error"] == "unsupported project"


def test_build_rows_job_stops_if_job_was_cleared() -> None:
    disasm_server._ASYNC_JOBS.clear()

    assert disasm_server._set_job_state("missing", status="building") is False
    disasm_server._build_rows_job("missing", "bloodwych")


def test_build_rows_job_does_not_cache_after_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["job-full"] = {
        "job_id": "job-full",
        "job_kind": "listing_artifact",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }

    def canceled_build(project_name: str) -> tuple[int, dict[str, object], _FakeCListingArtifact]:
        del disasm_server._ASYNC_JOBS["job-full"]
        return 1, {}, _FakeCListingArtifact()

    monkeypatch.setattr(disasm_server, "build_project_listing_artifact_profile", canceled_build)

    disasm_server._build_rows_job("job-full", "bloodwych")

    assert disasm_server._LISTING_PROJECTION_SERVICE.artifact_for_test("bloodwych") is None


def test_listing_artifact_job_keeps_c_artifact_without_full_python_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    subscriber: queue.Queue[dict[str, object]] = queue.Queue()
    disasm_server._JOB_EVENT_SUBSCRIBERS["job-full"] = [subscriber]
    artifact = _FakeCListingArtifact()

    monkeypatch.setattr(
        disasm_server,
        "build_project_listing_artifact_profile",
        lambda project_name: (1, {}, artifact),
    )
    disasm_server._ASYNC_JOBS["job-full"] = {
        "job_id": "job-full",
        "job_kind": "listing_artifact",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }
    disasm_server._build_rows_job("job-full", "bloodwych")

    assert disasm_server._LISTING_PROJECTION_SERVICE.artifact_for_test("bloodwych") is artifact
    events: list[dict[str, object]] = []
    while not subscriber.empty():
        events.append(subscriber.get_nowait())
    artifact_events = [event for event in events if event.get("_event_type") == "listing_artifact_ready"]
    assert artifact_events == [
        {
            "_event_type": "listing_artifact_ready",
            "project_id": "bloodwych",
            "total_rows": 1,
            "changed_ranges": [],
        }
    ]


def test_route_listing_status_returns_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_job_payload",
        lambda job_id: {"job_id": job_id, "status": "building", "phase_id": "cache_artifact"},
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing/status",
        {"job_id": ["job-1"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["status"] == "building"
    assert data["phase_id"] == "cache_artifact"


def test_job_state_update_publishes_event() -> None:
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    subscriber: queue.Queue[disasm_server.AsyncJobPayload] = queue.Queue()
    disasm_server._ASYNC_JOBS["job-1"] = {
        "job_id": "job-1",
        "job_kind": "listing_artifact",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "queued",
        "phase_id": "queued",
        "phase_index": 0,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }
    disasm_server._JOB_EVENT_SUBSCRIBERS["job-1"] = [subscriber]

    assert disasm_server._set_job_state(
        "job-1",
        status="ready",
        phase_id="done",
        finished_at=2.0,
    )

    payload = subscriber.get_nowait()
    assert payload["job_id"] == "job-1"
    assert payload["status"] == "ready"
    assert payload["phase_id"] == "done"
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    disasm_server._ASYNC_JOBS.clear()


def test_cancel_listing_job_publishes_failed_event() -> None:
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    subscriber: queue.Queue[disasm_server.AsyncJobPayload] = queue.Queue()
    disasm_server._ASYNC_JOBS["job-1"] = {
        "job_id": "job-1",
        "job_kind": "listing_artifact",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "building",
        "phase_id": "build_c_artifact",
        "phase_index": 1,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 0,
        "progress_total": 2,
        "progress_percent": 0,
        "total_rows": None,
        "error": None,
        "created_at": 1.0,
        "finished_at": None,
    }
    disasm_server._JOB_EVENT_SUBSCRIBERS["job-1"] = [subscriber]

    disasm_server._cancel_listing_jobs("bloodwych")

    payload = subscriber.get_nowait()
    assert payload["job_id"] == "job-1"
    assert payload["status"] == "failed"
    assert payload["error"] == "job canceled"
    assert "job-1" not in disasm_server._ASYNC_JOBS
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()


def test_json_bytes_returns_valid_json() -> None:
    body = disasm_server._json_bytes({"ok": True, "data": {"x": 1}})

    assert json.loads(body.decode("utf-8")) == {
        "ok": True,
        "data": {"x": 1},
        "web_app_contract_version": disasm_server.WEB_APP_CONTRACT_VERSION,
    }


def test_resolve_static_response_serves_index() -> None:
    response = disasm_server.resolve_static_response("/")

    assert response["content_type"] == "text/html; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"Disassembly Projects" in response["body"]


def test_resolve_static_response_serves_project_route() -> None:
    response = disasm_server.resolve_static_response("/bloodwych")

    assert response["content_type"] == "text/html; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"Disassembly Projects" in response["body"]


def test_resolve_static_response_serves_dotted_project_route() -> None:
    response = disasm_server.resolve_static_response("/amiga_disk_search-for-the-king")

    assert response["content_type"] == "text/html; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"Disassembly Projects" in response["body"]


def test_resolve_static_response_serves_app_js_with_no_store() -> None:
    response = disasm_server.resolve_static_response("/app.js")

    assert response["content_type"] == "application/javascript; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"function renderDiskTargets(manifest" in response["body"]


def test_resolve_static_response_rejects_missing_file() -> None:
    with pytest.raises(FileNotFoundError, match="Unknown route"):
        disasm_server.resolve_static_response("/assets/missing.txt")


def test_listing_artifact_job_queues_reproduction(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[str] = []
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    artifact = _FakeCListingArtifact()
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(
        disasm_server,
        "build_project_listing_artifact_profile",
        lambda project_name: (
            1,
            {},
            artifact,
        ),
    )
    monkeypatch.setattr(disasm_server, "_start_reproduction_job_if_needed", lambda project_name: queued.append(project_name))
    disasm_server._ASYNC_JOBS["job-1"] = cast(
        disasm_server.AsyncJobPayload,
        {
            "job_id": "job-1",
            "job_kind": "listing_artifact",
            "project_id": "bloodwych",
            "result_project_id": "bloodwych",
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": 2,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": 2,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": 1.0,
            "finished_at": None,
            "cache_key": "cache",
        },
    )

    disasm_server._build_rows_job("job-1", "bloodwych")

    assert queued == ["bloodwych"]
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_cached_listing_artifact_job_queues_reproduction(monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[str] = []
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        "bloodwych",
        _FakeCListingArtifact(),
        cache_key="cache",
    )
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "cache")
    monkeypatch.setattr(
        disasm_server,
        "_start_reproduction_job_if_needed",
        lambda project_name: queued.append(project_name),
    )

    payload = disasm_server._start_listing_job("bloodwych")

    assert payload["status"] == "ready"
    assert payload["total_rows"] == 1
    assert queued == ["bloodwych"]
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_listing_cache_requires_c_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_cache_key_for_test("bloodwych", cache_key="cache")
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "cache")

    assert not disasm_server._cache_satisfies_listing("bloodwych", "cache")

    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_reproduction_job_does_not_use_stale_cached_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_cache_key_for_test("bloodwych", cache_key="old-cache")
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "fresh-cache")
    monkeypatch.setattr(disasm_server, "_reproduction_cache_key", lambda project_name: "repro-cache")
    monkeypatch.setattr(
        disasm_server,
        "run_reproduction",
        lambda *args, **kwargs: calls.append({"args": args, "kwargs": kwargs}) or {"status": "exact"},
    )
    disasm_server._ASYNC_JOBS["repro-job"] = cast(
        disasm_server.AsyncJobPayload,
        {
            "job_id": "repro-job",
            "job_kind": "reproduction",
            "project_id": "bloodwych",
            "result_project_id": "bloodwych",
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": 4,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": 4,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": 1.0,
            "finished_at": None,
            "cache_key": "repro-cache",
        },
    )

    disasm_server._build_reproduction_job("repro-job", "bloodwych")

    assert len(calls) == 1
    assert "rows" not in calls[0]["kwargs"]
    assert disasm_server._ASYNC_JOBS["repro-job"]["status"] == "ready"
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_reproduction_job_reuses_artifact_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_source: list[str | None] = []
    captured_profile: list[object] = []
    artifact = _FakeCListingArtifact()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        "carrier-raw",
        artifact,
        cache_key="listing-cache",
    )
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "listing-cache")
    monkeypatch.setattr(disasm_server, "_reproduction_cache_key", lambda project_name: "repro-cache")

    def fake_run_reproduction(
        project_name,
        project_root,
        pre_rendered_source_text=None,
        pre_rendered_source_profile=None,
    ):
        captured_source.append(pre_rendered_source_text)
        captured_profile.append(pre_rendered_source_profile)
        return {"status": "exact"}

    monkeypatch.setattr(disasm_server, "run_reproduction", fake_run_reproduction)
    disasm_server._ASYNC_JOBS["repro-job"] = cast(
        disasm_server.AsyncJobPayload,
        {
            "job_id": "repro-job",
            "job_kind": "reproduction",
            "project_id": "carrier-raw",
            "result_project_id": "carrier-raw",
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": 4,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": 4,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": 1.0,
            "finished_at": None,
            "cache_key": "repro-cache",
        },
    )

    disasm_server._build_reproduction_job("repro-job", "carrier-raw")

    assert captured_source == ["    SECTION section,code\n    rts\n"]
    assert captured_profile == [{"generation": "fake-source"}]
    assert disasm_server._ASYNC_JOBS["repro-job"]["status"] == "ready"
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_reproduction_job_fails_closed_when_artifact_source_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenSourceArtifact(_FakeCListingArtifact):
        def source_text_with_profile(self) -> tuple[str, dict[str, object]]:
            raise RuntimeError("source export failed")

    calls: list[object] = []
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        "carrier-raw",
        BrokenSourceArtifact(),
        cache_key="listing-cache",
    )
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "listing-cache")
    monkeypatch.setattr(disasm_server, "_reproduction_cache_key", lambda project_name: "repro-cache")
    monkeypatch.setattr(disasm_server, "run_reproduction", lambda *args, **kwargs: calls.append((args, kwargs)))
    disasm_server._ASYNC_JOBS["repro-job"] = cast(
        disasm_server.AsyncJobPayload,
        {
            "job_id": "repro-job",
            "job_kind": "reproduction",
            "project_id": "carrier-raw",
            "result_project_id": "carrier-raw",
            "status": "queued",
            "phase_id": "queued",
            "phase_index": 0,
            "phase_count": 4,
            "progress_mode": "determinate",
            "progress_current": 0,
            "progress_total": 4,
            "progress_percent": 0,
            "total_rows": None,
            "error": None,
            "created_at": 1.0,
            "finished_at": None,
            "cache_key": "repro-cache",
        },
    )

    disasm_server._build_reproduction_job("repro-job", "carrier-raw")

    job = disasm_server._ASYNC_JOBS["repro-job"]
    assert calls == []
    assert job["status"] == "failed"
    assert job["phase_id"] == "error"
    assert job["error"] == "artifact source unavailable: source export failed"
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_target_edits_route_is_removed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        "bloodwych",
        _RowsCListingArtifact([]),
        cache_key="cache",
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root: SimpleNamespace(target_dir=target_dir),
    )

    with pytest.raises(FileNotFoundError, match="Unknown route"):
        disasm_server.route_request(
            "POST",
            "/api/projects/bloodwych/target-edits",
            {},
            {"kind": "entrypoint", "addr": 0x20},
        )
    assert disasm_server._LISTING_PROJECTION_SERVICE.artifact_for_test("bloodwych") is not None


def test_manual_action_route_appends_action_and_invalidates_analysis(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    canceled: list[str] = []
    appended: list[dict[str, object]] = []
    binary_source = object()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        "bloodwych",
        _RowsCListingArtifact([]),
        cache_key="cache",
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root: SimpleNamespace(target_dir=target_dir),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: binary_source)
    monkeypatch.setattr(
        disasm_server,
        "append_manual_action",
        lambda target_dir, kind, payload, binary_source: appended.append(
            {"kind": kind, "payload": payload, "binary_source": binary_source}
        )
        or {"kind": kind, **payload},
    )
    monkeypatch.setattr(disasm_server, "_cancel_listing_jobs", lambda project_name: canceled.append(f"listing:{project_name}"))
    monkeypatch.setattr(disasm_server, "_cancel_reproduction_jobs", lambda project_name: canceled.append(f"repro:{project_name}"))
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/manual-actions",
        {},
        {"kind": "create_manual_seed", "seed": {"seed_id": "s1", "kind": "data", "addr": 0x20}},
    )

    assert cast(dict[str, object], cast(dict[str, object], payload["data"])["action"])["kind"] == "create_manual_seed"
    assert appended == [
        {
            "kind": "create_manual_seed",
            "payload": {"seed": {"seed_id": "s1", "kind": "data", "addr": 0x20}},
            "binary_source": binary_source,
        }
    ]
    assert disasm_server._LISTING_PROJECTION_SERVICE.artifact_for_test("bloodwych") is None
    assert canceled == ["listing:bloodwych", "repro:bloodwych"]


def test_manual_action_route_rejects_reserved_payload_fields(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    appended: list[dict[str, object]] = []
    binary_source = object()
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root: SimpleNamespace(target_dir=target_dir),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: binary_source)
    monkeypatch.setattr(
        disasm_server,
        "append_manual_action",
        lambda target_dir, kind, payload, binary_source: appended.append(payload) or payload,
    )

    with pytest.raises(ValueError, match="reserved field"):
        disasm_server.route_request(
            "POST",
            "/api/projects/bloodwych/manual-actions",
            {},
            {
                "kind": "create_manual_seed",
                "action_id": "manual-forged",
                "seed": {"seed_id": "s1", "kind": "data", "addr": 0x20},
            },
        )

    assert appended == []


def test_listing_navigation_includes_repro_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [ListingRow(row_id="r0", kind="instruction", text="rts\n", addr=0x20)]
    monkeypatch.setattr(
        disasm_server,
        "_active_reproduction_report",
        lambda project_name: {
            "issues": [
                {
                    "kind": "diff",
                    "summary": "Diff at file offset 0x20",
                    "row_index": 0,
                    "addr": 0x20,
                    "match_text": "rts",
                }
            ]
        },
    )
    payload = _test_listing_navigation_payload("bloodwych", rows)
    groups = cast(dict[str, list[dict[str, object]]], payload["groups"])

    assert groups["repro-issues"][0]["summary"] == "Diff at file offset 0x20"
