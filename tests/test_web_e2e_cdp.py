from __future__ import annotations

import json
import shutil
import socket
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from amiga_reversing.amiga_disk.project import import_disk_entry_target
from amiga_reversing.disasm import projects as project_store
from amiga_reversing.disasm import server as disasm_server
from amiga_reversing.disasm.api import ListingWindowPayload
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord
from tests.cdp_brave import brave_cdp_requested, brave_cdp_skip_reason, brave_page
from tests.listing_row_fixtures import serialize_row
from tests.listing_types_fixtures import (
    AppSlotRef,
    BlockRowContext,
    ListingRow,
    SemanticOperand,
    SymbolOperandMetadata,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(not brave_cdp_requested(), reason=brave_cdp_skip_reason())


def _binary_project(project_name: str) -> ProjectRecord:
    return ProjectRecord(
        id=project_name,
        name=project_name,
        kind=ProjectKind.BINARY,
        target_dir=f"targets/{project_name}",
        output_path=f"targets/{project_name}/{project_name}.s",
        binary_path="bin/demo",
        ready=True,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path="bin/demo",
        disk_type=None,
        parent_project_id=None,
        target_type="program",
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )


def _cache_full_project_rows(
    project_id: str,
    rows: list[ListingRow],
    *,
    api_calls_by_row_id: dict[str, dict[str, object]] | None = None,
    app_slot_analysis: dict[str, object] | None = None,
    type_flow_analysis: dict[str, object] | None = None,
) -> None:
    disasm_server._PROJECT_C_LISTING_ARTIFACT_CACHE[project_id] = _FakeCListingArtifact(
        rows,
        project_name=project_id,
        api_calls_by_row_id=api_calls_by_row_id,
        app_slot_analysis=app_slot_analysis,
        type_flow_analysis=type_flow_analysis,
    )
    disasm_server._PROJECT_LISTING_CACHE_KEY[project_id] = "test-cache"


def _test_row_code(row: ListingRow) -> str:
    if row.label:
        return row.label
    if row.opcode_or_directive:
        return " ".join(part for part in (row.opcode_or_directive, row.operand_text) if part).strip()
    return row.text.strip()


def _test_navigation_payload(
    project_name: str,
    rows: list[ListingRow],
    api_calls_by_row_id: dict[str, dict[str, object]] | None = None,
    *,
    app_slot_analysis: dict[str, object] | None = None,
    type_flow_analysis: dict[str, object] | None = None,
) -> dict[str, object]:
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
        "equates": [],
        "comments": [],
    }
    app_slots: dict[str, dict[str, object]] = {}
    labels: dict[str, dict[str, object]] = {}
    equates: dict[str, dict[str, object]] = {}
    api_calls_by_row_id = api_calls_by_row_id or {}
    for row_index, row in enumerate(rows):
        code = _test_row_code(row)
        parts = code.split(None, 2)
        if len(parts) >= 2 and parts[1].upper() == "EQU":
            symbol = parts[0]
            operand = parts[2] if len(parts) > 2 else ""
            equates[symbol] = {
                "addr": row.addr,
                "row_index": row_index,
                "summary": f"{symbol} EQU{f' {operand}' if operand else ''}",
                "match_text": code,
                "stable_key": row.stable_key,
                "symbol": symbol,
                "operand": operand,
                "ref_count": 1,
                "access_counts": {"definition": 1},
                "refs": [
                    {
                        "addr": row.addr,
                        "row_index": row_index,
                        "summary": code,
                        "match_text": code,
                        "stable_key": row.stable_key,
                        "symbol": symbol,
                        "access": "definition",
                    }
                ],
            }
        if row.addr is None:
            continue
        base_entry: dict[str, object] = {
            "addr": row.addr,
            "row_index": row_index,
            "summary": code,
            "match_text": code,
            "stable_key": row.stable_key,
        }
        if isinstance(row.source_context, BlockRowContext):
            base_entry["hunk_index"] = row.source_context.hunk_index
        if row.label or code.endswith(":"):
            symbol = (row.label or code).rstrip(":")
            label_entry = {
                **base_entry,
                "summary": f"{symbol}:",
                "symbol": symbol,
                "ref_count": 1,
                "access_counts": {"definition": 1},
                "refs": [{**base_entry, "summary": f"{symbol}:", "symbol": symbol, "access": "definition"}],
            }
            labels[symbol] = label_entry
        api_call = api_calls_by_row_id.get(row.row_id)
        if isinstance(api_call, dict) and row.kind == "instruction":
            groups["api-calls"].append(
                {
                    **base_entry,
                    "summary": f"{api_call.get('function', '')} ({api_call.get('library', '')})".strip(),
                }
            )
        if row.typed_accesses or (row.kind not in {"instruction", "label"} and (row.comment_text or row.structured_data)):
            summary = row.comment_text or row.kind
            if row.typed_accesses:
                access = row.typed_accesses[0]
                summary = ".".join(
                    part
                    for part in (
                        access.owner_struct_name or access.root_struct_name,
                        access.field_expr or access.field_name,
                    )
                    if part
                )
            groups["typed-data"].append({**base_entry, "summary": summary})
        for ref in row.app_slot_refs:
            slot = app_slots.setdefault(
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
            cast(list[dict[str, object]], slot["refs"]).append({**base_entry, "symbol": ref.symbol, "access": ref.access})
            slot["ref_count"] = cast(int, slot["ref_count"]) + 1
            access_counts = cast(dict[str, int], slot["access_counts"])
            access_counts[ref.access] = access_counts.get(ref.access, 0) + 1
    for row_index, row in enumerate(rows):
        if row.addr is None:
            continue
        code = _test_row_code(row)
        base_entry: dict[str, object] = {
            "addr": row.addr,
            "row_index": row_index,
            "summary": code,
            "match_text": code,
            "stable_key": row.stable_key,
        }
        if isinstance(row.source_context, BlockRowContext):
            base_entry["hunk_index"] = row.source_context.hunk_index
        for operand in row.operand_parts:
            symbol = operand.metadata.symbol if isinstance(operand.metadata, SymbolOperandMetadata) else None
            if not symbol:
                continue
            if symbol in labels:
                label_entry = labels[symbol]
                cast(list[dict[str, object]], label_entry["refs"]).append(
                    {**base_entry, "symbol": symbol, "access": "reference"}
                )
                label_entry["ref_count"] = cast(int, label_entry["ref_count"]) + 1
                access_counts = cast(dict[str, int], label_entry["access_counts"])
                access_counts["reference"] = access_counts.get("reference", 0) + 1
            if symbol in equates:
                equate_entry = equates[symbol]
                cast(list[dict[str, object]], equate_entry["refs"]).append(
                    {**base_entry, "symbol": symbol, "access": "reference"}
                )
                equate_entry["ref_count"] = cast(int, equate_entry["ref_count"]) + 1
                access_counts = cast(dict[str, int], equate_entry["access_counts"])
                access_counts["reference"] = access_counts.get("reference", 0) + 1
    for label_entry in labels.values():
        cast(list[dict[str, object]], label_entry["refs"]).sort(
            key=lambda entry: cast(int, entry.get("row_index", -1))
        )
    groups["app-slots"] = list(app_slots.values())
    groups["labels"] = sorted(labels.values(), key=lambda entry: cast(int, entry.get("row_index", -1)))
    groups["equates"] = sorted(equates.values(), key=lambda entry: cast(int, entry.get("row_index", -1)))
    return {
        "analysis_generation": "full" if project_name in disasm_server._PROJECT_C_LISTING_ARTIFACT_CACHE else None,
        "total_rows": len(rows),
        "groups": groups,
        "app_slot_analysis": app_slot_analysis or {},
        "type_flow_analysis": type_flow_analysis or {},
    }


class _FakeCListingArtifact:
    def __init__(
        self,
        rows: list[ListingRow],
        *,
        project_name: str = "test_project",
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

    def close(self) -> None:
        self.closed = True

    def window_payload(self, *, start: int, count: int) -> tuple[dict[str, object], dict[str, object]]:
        payload = dict(_test_listing_index_window_payload(self.rows, start, count, self.api_calls_by_row_id))
        payload["analysis_generation"] = "full"
        return payload, {}

    def addr_window_payload(
        self, *, addr: int | None, before: int, after: int
    ) -> tuple[dict[str, object], dict[str, object]]:
        payload = dict(
            _test_listing_addr_window_payload(
                self.rows,
                addr,
                before=before,
                after=after,
                api_calls_by_row_id=self.api_calls_by_row_id,
            )
        )
        payload["analysis_generation"] = "full"
        return payload, {}

    def row_for_source_offset(self, *, section_index: int | None, offset: int) -> dict[str, object] | None:
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

    def row_for_runtime_address(self, *, address: int) -> dict[str, object] | None:
        for index, row in enumerate(self.rows):
            start = row.runtime_address
            if start is None:
                continue
            source_start = row.start_offset if row.start_offset is not None else row.addr
            source_end = row.end_offset if row.end_offset is not None else None
            end = start + max(1, source_end - source_start) if source_start is not None and source_end is not None else start + 1
            if start <= address < end or start == address:
                serialized = dict(serialize_row(row))
                serialized["row_index"] = index
                return serialized
        return None

    def anchor_window_payload(self, *, anchor_code: str, count: int) -> tuple[dict[str, object], dict[str, object]]:
        start = 0
        needle = anchor_code.strip()
        for index, row in enumerate(self.rows):
            if row.text.strip() == needle:
                start = index
                break
        payload = dict(_test_listing_index_window_payload(self.rows, start, count, self.api_calls_by_row_id))
        payload["analysis_generation"] = "full"
        return payload, {}

    def navigation_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        return _test_navigation_payload(
            self.project_name,
            self.rows,
            self.api_calls_by_row_id,
            app_slot_analysis=self.app_slot_analysis,
            type_flow_analysis=self.type_flow_analysis,
        ), {}


def _temp_project_accessors(monkeypatch: pytest.MonkeyPatch, project_root: Path) -> None:
    monkeypatch.setattr(disasm_server, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(
        disasm_server,
        "list_projects",
        lambda: project_store.list_projects(project_root=project_root),
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name, project_root=project_root: project_store.get_project(
            project_name, project_root=project_root
        ),
    )
    monkeypatch.setattr(
        disasm_server,
        "mark_project_opened",
        lambda project_name, project_root=project_root: project_store.get_project(
            project_name, project_root=project_root
        ),
    )


def _append_carrier_decompressed_fixture(project_root: Path, disk_project_id: str) -> None:
    disk_root = project_root / "targets" / disk_project_id
    manifest_path = disk_root / "manifest.json"
    local_target_id = "amiga_raw_carrier_91b0ba24_rnc1_old_00_00004c40"
    decompression_path = (
        disk_root
        / "targets"
        / local_target_id
        / "decompression.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if decompression_path.exists():
        decompression = json.loads(decompression_path.read_text(encoding="utf-8"))
    else:
        child_target_id = f"{disk_project_id}__{local_target_id}"
        decompression = {
            "child_entry_path": "Carrier::RNC1-old_00004c40",
            "child_target_id": child_target_id,
            "relationship": {
                "kind": "derived_decompressed_payload",
                "compressor": {"id": "RNC1-old", "name": "RNC1-old"},
                "parent_target_id": f"{disk_project_id}__amiga_hunk_carrier_91b0ba24",
                "packed_file_offset": 0x4C40,
                "load_address": 0x4000,
                "entrypoint": 0x4000,
                "decompressed_size": 0x1000,
            },
        }
    relationship = decompression["relationship"]
    child_target_id = decompression["child_target_id"]
    targets = manifest["imported_targets"]
    parent_target_id = relationship.get("parent_target") or relationship.get("parent_target_id")
    for target in targets:
        if target.get("target_name") != parent_target_id:
            continue
        target["derived_targets"] = [
            {
                "kind": "decompressed_payload",
                "target_name": child_target_id,
                "provider_id": "fixture",
                "codec_id": "RNC1-old",
                "payload_role": "primary_program",
                "parent_remains_active": "false",
            }
        ]
        break
    if not any(target["target_name"] == child_target_id for target in targets):
        targets.append(
            {
                "binary_path": (
                    f"targets/{disk_project_id}/targets/"
                    f"{local_target_id}/binary.bin"
                ),
                "derived_from": relationship,
                "derived_targets": None,
                "entry_path": decompression["child_entry_path"],
                "target_name": child_target_id,
                "target_path": (
                    f"targets/{disk_project_id}/targets/"
                    f"{local_target_id}"
                ),
                "target_type": "raw_binary",
            }
        )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def _skip_without_c_backend() -> None:
    missing = [
        PROJECT_ROOT / "src" / "build" / "platform_file_lib.dll",
        PROJECT_ROOT / "src" / "build" / "platform_disk_lib.dll",
    ]
    missing = [path for path in missing if not path.exists()]
    if missing:
        pytest.skip(f"missing C backend DLL; run cmd /c src\\build.bat: {missing[0]}")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class _QuietThreadingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: object, client_address: object) -> None:
        _, exc, _ = sys.exc_info()
        if isinstance(exc, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


@pytest.fixture(autouse=True)
def _clear_disasm_server_listing_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    original_cache_key = disasm_server._project_listing_cache_key

    def project_listing_cache_key(project_name: str) -> str:
        cached = disasm_server._PROJECT_LISTING_CACHE_KEY.get(project_name)
        if cached is not None:
            return cached
        return original_cache_key(project_name)

    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", project_listing_cache_key)
    disasm_server._PROJECT_C_LISTING_ARTIFACT_CACHE.clear()
    disasm_server._PROJECT_LISTING_CACHE_KEY.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    yield
    disasm_server._PROJECT_C_LISTING_ARTIFACT_CACHE.clear()
    disasm_server._PROJECT_LISTING_CACHE_KEY.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()


@contextmanager
def _live_server() -> Iterator[str]:
    port = _free_port()
    httpd = _QuietThreadingHTTPServer(("127.0.0.1", port), disasm_server.DisasmApiHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()


@pytest.mark.web_e2e
def test_brave_cdp_can_open_project_and_render_listing(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_demo")
    rows = [
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0),
        ListingRow(row_id="r1", kind="instruction", text="moveq #0,d0\n", addr=0),
        ListingRow(row_id="r2", kind="instruction", text="rts\n", addr=2),
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": base_url})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.project-open-button').length === 1")

        page.click(".project-open-button")

        page.wait_for_expression("document.querySelectorAll('.listing-row').length === 3")
        assert page.evaluate("document.querySelector('#project-title')?.textContent") == project.id
        assert page.evaluate("document.querySelector('.listing-code')?.textContent") == "start:"
        assert page.evaluate("location.pathname") == f"/{project.id}"
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_manual_review_panel_filters_and_navigates(monkeypatch: pytest.MonkeyPatch) -> None:
    base_project = _binary_project("amiga_hunk_review")
    project = replace(
        base_project,
        review_state="blocked",
        review_items=(
            {
                "kind": "label_scope_conflict",
                "item_id": "label_scope_conflict:demo",
                "scope": "range",
                "state": "open",
                "review_blocker": True,
                "review_confidence": "high",
                "hunk": 0,
                "start": 2,
                "end": 4,
                "message": "Duplicate label",
                "suggested_actions": [{"action": "rename_manual_label"}],
            },
            {
                "kind": "unreconciled_data_range",
                "item_id": "unreconciled:h0:00000004-00000008",
                "scope": "range",
                "state": "resolved",
                "review_confidence": "medium",
                "source": "analysis",
                "hunk": 0,
                "start": 4,
                "end": 8,
                "message": "Known data gap",
                "suggested_actions": [{"action": "navigate"}],
            },
        ),
    )
    rows = [
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0, section_index=0, start_offset=0, end_offset=0),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="moveq #0,d0\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=2,
        ),
        ListingRow(row_id="r2", kind="instruction", text="rts\n", addr=2, section_index=0, start_offset=2, end_offset=4),
        ListingRow(row_id="r3", kind="data", text="dc.b $00,$01,$02,$03\n", addr=4, section_index=0, start_offset=4, end_offset=8),
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": base_url})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.project-open-button').length === 1")
        assert "Blocked" in page.text_content(".project-open-button")
        page.click(".project-open-button")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length === 4")
        assert "Blocked" in page.text_content("#project-details")
        page.click("#open-review")
        page.wait_for_selector("#review-overlay .review-item")
        assert "1 of 2 items" in page.text_content("#review-overlay")
        assert "label scope conflict" in page.text_content("#review-overlay")
        page.select_value("[data-review-filter='state']", "")
        page.wait_for_expression("document.querySelector('#review-overlay .review-summary')?.textContent.includes('2 of 2')")
        page.select_value("[data-review-filter='kind']", "unreconciled_data_range")
        page.wait_for_expression("document.querySelector('#review-overlay .review-summary')?.textContent.includes('1 of 2')")
        assert "Known data gap" in page.text_content("#review-overlay")
        page.click("#review-overlay .review-item-title")
        page.wait_for_selector(".listing-row-focus")
        assert page.evaluate("document.querySelector('.listing-row-focus')?.dataset.rowAddr") == "4"
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_listing_ready_refreshes_analysis_review_badge(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_analysis_review")
    rows = [
        *[
            ListingRow(
                row_id=f"h0-{index}",
                kind="instruction",
                text="nop\n",
                addr=index * 2,
                section_index=0,
                start_offset=index * 2,
                end_offset=index * 2 + 2,
            )
            for index in range(320)
        ],
        ListingRow(row_id="section-2", kind="directive", text="    SECTION section_2,code\n"),
        ListingRow(
            row_id="h2-target",
            kind="instruction",
            text="jmp $0040(a2)\n",
            addr=0x14C,
            section_index=2,
            start_offset=0x14C,
            end_offset=0x150,
        ),
        ListingRow(
            row_id="h2-after",
            kind="instruction",
            text="rts\n",
            addr=0x150,
            section_index=2,
            start_offset=0x150,
            end_offset=0x152,
        ),
    ]

    class AnalysisBlockerArtifact(_FakeCListingArtifact):
        def analysis_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return (
                {
                    "sections": [],
                    "decompression_events": [
                        {
                            "event_id": "child-2",
                            "status_id": 6,
                            "status": "needs_review_blocker",
                            "reason": "invalid_decompressed_entrypoint",
                            "source_section": 2,
                            "source_section_offset": 0x14C,
                        }
                    ],
                },
                {},
            )

    def build_listing_artifact(project_name: str) -> tuple[int, dict[str, object], _FakeCListingArtifact]:
        artifact = AnalysisBlockerArtifact(rows, project_name=project_name)
        return len(rows), {}, artifact

    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "build_project_listing_artifact_profile", build_listing_artifact)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length > 0")
        page.wait_for_expression(
            "document.querySelector('#project-details')?.textContent.includes('Blocked')",
            timeout=10.0,
        )
        page.click("#open-review")
        page.wait_for_expression(
            "document.querySelector('#review-overlay')?.textContent.includes('decompression blocker')",
            timeout=10.0,
        )
        page.click("#review-overlay [data-review-action='navigate']")
        page.wait_for_expression(
            "document.querySelector('.listing-row-focus')?.dataset.startOffset === '332'",
            timeout=10.0,
        )
        assert page.evaluate("document.querySelector('.listing-row-focus')?.dataset.sectionIndex") == "2"
        assert page.evaluate(
            """
            (() => {
              const viewport = document.querySelector('#listing-viewport');
              const row = document.querySelector('.listing-row-focus');
              if (!viewport || !row) return false;
              const viewportRect = viewport.getBoundingClientRect();
              const rowRect = row.getBoundingClientRect();
              return rowRect.top >= viewportRect.top && rowRect.bottom <= viewportRect.bottom;
            })()
            """
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_review_navigation_back_refills_listing_window(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_review_history_refill")
    h1_rows = [
        ListingRow(
            row_id=f"h1-{index}",
            kind="instruction",
            text="nop\n",
            addr=index * 2,
            section_index=1,
            start_offset=index * 2,
            end_offset=index * 2 + 2,
            stable_key=f"h1-{index}",
        )
        for index in range(260)
    ]
    h2_rows = [
        ListingRow(
            row_id=f"h2-{index}",
            kind="instruction",
            text="nop\n",
            addr=0x100 + index * 2,
            section_index=2,
            start_offset=0x100 + index * 2,
            end_offset=0x100 + index * 2 + 2,
            stable_key=f"h2-{index}",
        )
        for index in range(80)
    ]
    rows = [*h1_rows, *h2_rows]

    project = replace(
        project,
        review_state="blocked",
        review_items=(
            {
                "kind": "unreconciled_data_range",
                "item_id": "unreconciled_data_range:h1:$000000c4:$000000ce",
                "scope": "range",
                "state": "open",
                "review_confidence": "low",
                "hunk": 1,
                "start": 0xC4,
                "end": 0xCE,
                "message": "Range has no accepted code, data, metadata, policy, or manual seed evidence",
            },
            {
                "kind": "decompression_blocker",
                "item_id": "decompression_blocker:h2:$0000014c",
                "scope": "range",
                "state": "open",
                "review_blocker": True,
                "review_confidence": "high",
                "hunk": 2,
                "start": 0x14C,
                "end": 0x14D,
                "message": "Decompressed payload requires manual review before parent can be clear",
            },
        ),
    )

    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length > 0")
        page.click("#open-review")
        page.wait_for_expression(
            "document.querySelector('#review-overlay')?.textContent.includes('decompression blocker')",
            timeout=10.0,
        )
        page.click("#review-overlay .review-item:nth-child(2) [data-review-action='navigate']")
        page.wait_for_expression(
            "document.querySelector('.listing-row-focus')?.dataset.sectionIndex === '1'",
            timeout=10.0,
        )
        page.evaluate(
            """
            (() => {
              const item = Array.from(document.querySelectorAll('#review-overlay .review-item'))
                .find((node) => node.textContent.includes('decompression blocker'));
              const button = item?.querySelector('[data-review-action="navigate"]');
              if (!button) throw new Error('missing decompression blocker navigate');
              button.click();
              return true;
            })()
            """
        )
        page.wait_for_expression(
            "document.querySelector('.listing-row-focus')?.dataset.sectionIndex === '2'",
            timeout=10.0,
        )
        page.click("#navigation-back")
        page.wait_for_expression(
            "document.querySelector('.listing-row-focus')?.dataset.sectionIndex === '1'",
            timeout=10.0,
        )
        time.sleep(0.2)
        metrics = page.evaluate(
            """
            (() => {
              const viewport = document.querySelector('#listing-viewport');
              const rows = Array.from(document.querySelectorAll('#listing-viewport .listing-row'));
              const viewportRect = viewport?.getBoundingClientRect();
              const visibleRows = rows.filter((row) => {
                const rect = row.getBoundingClientRect();
                return viewportRect && rect.bottom > viewportRect.top && rect.top < viewportRect.bottom;
              });
              const maxVisibleBottom = Math.max(...visibleRows.map((row) => row.getBoundingClientRect().bottom));
              return {
                rowCount: rows.length,
                visibleCount: visibleRows.length,
                firstIndex: rows[0]?.dataset.rowIndex || null,
                lastIndex: rows[rows.length - 1]?.dataset.rowIndex || null,
                focusIndex: document.querySelector('.listing-row-focus')?.dataset.rowIndex || null,
                focusSection: document.querySelector('.listing-row-focus')?.dataset.sectionIndex || null,
                scrollTop: viewport?.scrollTop ?? null,
                clientHeight: viewport?.clientHeight ?? null,
                scrollHeight: viewport?.scrollHeight ?? null,
                firstTop: rows[0]?.getBoundingClientRect().top ?? null,
                lastBottom: rows[rows.length - 1]?.getBoundingClientRect().bottom ?? null,
                viewportBottom: viewportRect?.bottom ?? null,
                maxVisibleBottom,
              };
            })()
            """
        )
        assert metrics["rowCount"] >= 40 and metrics["maxVisibleBottom"] >= metrics["viewportBottom"] - 30, metrics
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_manual_seed_waits_for_analysis_before_review_refresh(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project = _binary_project("amiga_hunk_manual_seed_refresh")
    rows = [
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0, section_index=0, start_offset=0, end_offset=0),
        ListingRow(row_id="r1", kind="data", text="dc.b $00,$01,$02,$03\n", addr=0, section_index=0, start_offset=0, end_offset=4),
    ]
    build_calls = 0
    second_build_entered = threading.Event()
    release_second_build = threading.Event()
    appended_actions: list[dict[str, object]] = []

    class AnalysisArtifact(_FakeCListingArtifact):
        def analysis_payload(self) -> tuple[dict[str, object], dict[str, object]]:
            return (
                {
                    "sections": [{"section_index": 0, "section_size": 8, "blocks": []}],
                    "decompression_events": [
                        {
                            "event_id": "still-blocked",
                            "status_id": 6,
                            "status": "needs_review_blocker",
                            "reason": "invalid_decompressed_entrypoint",
                            "source_section": 0,
                            "source_section_offset": 4,
                        }
                    ],
                },
                {},
            )

    def build_listing_artifact(project_name: str) -> tuple[int, dict[str, object], _FakeCListingArtifact]:
        nonlocal build_calls
        build_calls += 1
        if build_calls == 2:
            second_build_entered.set()
            assert release_second_build.wait(timeout=10.0)
        artifact = AnalysisArtifact(rows, project_name=project_name)
        return len(rows), {}, artifact

    def append_action(target_dir: Path, *, kind: str, payload: dict[str, object], binary_source: object) -> dict[str, object]:
        action = {"kind": kind, **payload}
        appended_actions.append(action)
        return action

    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_updated", lambda target_dir: None)
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "stable-cache")
    monkeypatch.setattr(disasm_server, "build_project_listing_artifact_profile", build_listing_artifact)
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda project_name, project_root=None: SimpleNamespace(target_dir=tmp_path / project_name),
    )
    monkeypatch.setattr(disasm_server, "resolve_target_binary_source", lambda target_dir: object())
    monkeypatch.setattr(disasm_server, "append_manual_action", append_action)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression(
            "document.querySelector('#project-details')?.textContent.includes('Blocked')",
            timeout=10.0,
        )
        page.click("#open-review")
        page.wait_for_expression(
            "document.querySelector('#review-overlay')?.textContent.includes('unreconciled data range')",
            timeout=10.0,
        )
        page.select_value("[data-review-filter='kind']", "unreconciled_data_range")
        page.wait_for_expression("document.querySelector('#review-overlay .review-summary')?.textContent.includes('1 of 2')")
        page.click("#review-overlay [data-review-action='create_manual_seed'][data-data-role='string']")
        if not second_build_entered.wait(timeout=10.0):
            page.assert_no_errors()
            raise AssertionError("manual seed did not trigger listing rebuild")
        assert appended_actions and appended_actions[0]["kind"] == "create_manual_seed"
        assert "Review clear" not in page.text_content("#project-details")
        assert "0 of 0" not in page.text_content("#review-overlay")
        release_second_build.set()
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and project.id not in disasm_server._PROJECT_C_LISTING_ARTIFACT_CACHE:
            time.sleep(0.05)
        assert project.id in disasm_server._PROJECT_C_LISTING_ARTIFACT_CACHE
        page.wait_for_expression(
            "document.querySelector('#project-details')?.textContent.includes('Blocked')",
            timeout=10.0,
        )
        page.wait_for_expression(
            "document.querySelector('#review-overlay .review-summary')?.textContent.includes('1 of 2')",
            timeout=10.0,
        )
        assert "Review clear" not in page.text_content("#project-details")
        assert "0 of 0" not in page.text_content("#review-overlay")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_corpus_filter_snippet_and_import(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_corpus_demo")
    _cache_full_project_rows(project.id, [
        ListingRow(row_id="r0", kind="label", text="imported_start:\n", addr=0),
        ListingRow(row_id="r1", kind="instruction", text="rts\n", addr=0),
    ])
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "feature_list",
        lambda: [
            {
                "feature": "hardware:custom",
                "target_count": 1,
                "occurrence_count": 1,
                "source_example_count": 1,
                "source_target_count": 1,
            },
            {
                "feature": "analysis:facts_v2",
                "target_count": 1,
                "occurrence_count": 1,
                "source_example_count": 0,
                "source_target_count": 0,
            },
        ],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "query_targets",
        lambda *, feature=None, group=None, platform=None, q=None, source_only=False, limit=None, offset=0, projects=None: [
            {
                "id": "platform_file_manifest:amiga-hunk/demo",
                "platform": "amiga-hunk",
                "size": 12148,
                "count": 1,
                "source_example_count": 1,
                "origin": {"in_image_path": "c/Demo"},
                "source_context": {
                    "target_name": "c/Demo",
                    "disk_name": "DemoDisk.adf",
                    "disk_target_id": "platform_disk_manifest:amiga-disk/demo",
                },
                "project_coverage": {
                    "target_project_id": None,
                    "disk_project_id": "amiga_disk_demo_project",
                    "parent_disk_target_id": "platform_disk_manifest:amiga-disk/demo",
                    "import_modes": [
                        {"mode": "target", "label": "Promote file", "available": True},
                        {"mode": "disk", "label": "Promote containing disk", "available": True, "corpus_target_id": "platform_disk_manifest:amiga-disk/demo"},
                    ],
                },
                "tags": ["hardware:custom"],
            }
        ],
    )
    def fake_query_xrefs(*, target_id=None, feature=None, group=None, source_only=False, limit=None, offset=0):
        rows = [
            {
                "id": "xref-target",
                "target_id": target_id,
                "feature": "analysis:facts_v2",
                "kind": "analysis_profile",
                "row_index": None,
                "text": "facts_v2",
            },
            {
                "id": "xref-1",
                "target_id": target_id,
                "feature": "hardware:custom",
                "kind": "hardware_ref",
                "row_index": 0,
                "text": "move.w #$7fff,_custom+intena.l",
            }
        ]
        if feature:
            rows = [row for row in rows if row["feature"] == feature]
        if source_only:
            rows = [row for row in rows if isinstance(row.get("row_index"), int)]
        if limit is not None:
            rows = rows[offset:offset + limit]
        return rows

    monkeypatch.setattr(disasm_server.corpus_usage, "query_xrefs", fake_query_xrefs)
    snippet_release = threading.Event()

    def fake_snippet_payload(xref_id, before=20, after=20):
        snippet_release.wait(timeout=5.0)
        return {
            "xref": {"id": xref_id},
            "start": 0,
            "end": 1,
            "highlighted_row_index": 0,
            "rows": [
                {
                    "row_id": "s0",
                    "row_index": 0,
                    "kind": "instruction",
                    "text": "\tmove.w #$7fff,_custom+intena.l\n",
                    "start_offset": 0,
                    "bytes": "33fc7fff00dff09a",
                }
            ],
        }

    monkeypatch.setattr(disasm_server.corpus_usage, "snippet_payload", fake_snippet_payload)

    def fake_disk_browser_payload(target_id, path="", **_kwargs):
        disk = {
            "id": "platform_disk_manifest:amiga-disk/demo",
            "corpus_target_id": "platform_disk_manifest:amiga-disk/demo",
            "platform": "amiga-disk",
            "display_name": "DemoDisk.adf",
            "disk_name": "DemoDisk.adf",
            "size": 901120,
            "project_coverage": {
                "import_modes": [
                    {"mode": "disk", "label": "Promote disk", "available": True, "corpus_target_id": "platform_disk_manifest:amiga-disk/demo"},
                ],
            },
        }
        if path == "s":
            return {
                "disk": disk,
                "path": "s",
                "parent_path": "",
                "volume": None,
                "selected_entry": {"name": "s", "path": "s", "type": "directory", "is_directory": True, "size": None},
                "entries": [
                    {
                        "name": "startup-sequence",
                        "path": "s/startup-sequence",
                        "type": "text",
                        "size": 42,
                        "is_directory": False,
                    }
                ],
            }
        if path == "s/startup-sequence":
            return {
                "disk": disk,
                "path": "s/startup-sequence",
                "parent_path": "s",
                "volume": None,
                "selected_entry": {
                    "name": "startup-sequence",
                    "path": "s/startup-sequence",
                    "type": "text",
                    "size": 4,
                    "is_directory": False,
                    "content": {
                        "size": 4,
                        "truncated": False,
                        "text_available": True,
                        "text": "Echo",
                        "bytes": "45 63 68 6F",
                        "hexdump": [{"offset": 0, "hex": "45 63 68 6F", "ascii": "Echo"}],
                    },
                },
                "entries": [],
            }
        return {
            "disk": disk,
            "path": "",
            "parent_path": None,
            "volume": None,
            "selected_entry": None,
            "entries": [
                {"name": "s", "path": "s", "type": "directory", "size": None, "is_directory": True},
                {
                    "name": "run",
                    "path": "run",
                    "type": "Amiga HUNK program",
                    "size": 12148,
                    "is_directory": False,
                    "target_id": "platform_file_manifest:amiga-hunk/demo",
                },
            ],
        }

    monkeypatch.setattr(disasm_server.corpus_usage, "disk_browser_payload", fake_disk_browser_payload)
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "corpus_import_media_body",
        lambda target_id, mode="target": {"filename": "Demo", "media_base64": "ZGVtbw=="},
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_project_create_job",
        lambda body: {
            "job_id": "cached-corpus-import",
            "job_kind": "project_create",
            "project_id": None,
            "result_project_id": project.id,
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
            "finished_at": 1.0,
        },
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_listing_job",
        lambda project_name: {
            "job_id": "cached-listing",
            "job_kind": "listing_artifact",
            "project_id": project_name,
            "result_project_id": project_name,
            "status": "ready",
            "phase_id": "done",
            "phase_index": 2,
            "phase_count": 2,
            "progress_mode": "determinate",
            "progress_current": 2,
            "progress_total": 2,
            "progress_percent": 100,
            "total_rows": 2,
            "error": None,
            "created_at": 1.0,
            "finished_at": 1.0,
        },
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": base_url})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector("[data-home-view='corpus']")
        page.click("[data-home-view='corpus']")
        page.wait_for_selector("#corpus-feature")
        page.wait_for_expression("document.querySelector('#corpus-feature')?.textContent.includes('1 source')")
        assert "analysis:facts_v2" not in page.text_content("#corpus-feature")
        page.click("[data-corpus-group='hardware']")
        page.wait_for_expression("document.querySelector('.corpus-quick-filter.active')?.textContent.includes('Hardware')")
        page.select_value("#corpus-feature", "hardware:custom")
        page.wait_for_selector(".corpus-card")
        assert "1 source examples" in page.text_content(".corpus-card-meta")
        assert "12 KB" in page.text_content(".corpus-card-meta")
        assert "Disk: DemoDisk.adf" in page.text_content(".corpus-card")
        assert page.evaluate("document.querySelector('.corpus-card-main .corpus-card-source-button') !== null")
        assert page.evaluate("document.querySelector('.corpus-disk-browse-button')?.dataset.corpusDiskBrowse === 'platform_disk_manifest:amiga-disk/demo'")
        assert "Disk in projects" in page.text_content(".corpus-card")
        assert page.evaluate("document.querySelector('.corpus-card-source-button')?.dataset.corpusRelatedTarget === 'platform_disk_manifest:amiga-disk/demo'")
        assert page.text_content(".corpus-add-button") == "\U0001f516"
        assert page.evaluate("document.querySelector('.corpus-add-button')?.title === 'Promote to be a real project'")
        assert page.evaluate("getComputedStyle(document.querySelector('.corpus-quick-filters')).flexWrap === 'wrap'")
        page.click(".corpus-disk-browse-button")
        page.wait_for_selector("#corpus-disk-browser-overlay .corpus-disk-entry")
        assert "Amiga HUNK program" in page.text_content("#corpus-disk-browser-overlay")
        assert "12 KB" in page.text_content("#corpus-disk-browser-overlay")
        assert "Promote disk" in page.text_content("#corpus-disk-browser-overlay")
        assert page.evaluate("document.querySelector('#corpus-disk-browser-overlay [data-corpus-import-mode=\"disk\"]')?.dataset.corpusImport === 'platform_disk_manifest:amiga-disk/demo'")
        disk_entries = page.evaluate("[...document.querySelectorAll('.corpus-disk-entry-name')].map((el) => el.textContent)")
        assert "s" in disk_entries[0]
        assert "run" in disk_entries[1]
        page.click("#corpus-disk-browser-overlay .corpus-disk-entry.directory")
        page.wait_for_expression("document.querySelector('#corpus-disk-browser-overlay')?.textContent.includes('startup-sequence')")
        page.click("#corpus-disk-browser-overlay .corpus-disk-entry.file")
        page.wait_for_expression("document.querySelector('#corpus-disk-browser-overlay')?.textContent.includes('Echo')")
        page.click("[data-disk-browser-view='hexdump']")
        page.wait_for_expression("document.querySelector('#corpus-disk-browser-overlay')?.textContent.includes('45 63 68 6F')")
        page.press_key("Escape")
        page.wait_for_expression("document.querySelector('#corpus-disk-browser-overlay') === null")
        page.click(".corpus-card-main")
        page.wait_for_selector(".corpus-xref")
        assert "Source Examples" in page.text_content(".corpus-detail")
        assert "Target Facts" not in page.text_content(".corpus-detail")
        page.click("#corpus-show-facts")
        page.wait_for_expression("document.querySelector('.corpus-detail')?.textContent.includes('Target Facts')")
        assert "No target facts for this filter." in page.text_content(".corpus-detail")
        assert page.evaluate("getComputedStyle(document.querySelector('.corpus-results')).overflowY === 'auto'")
        assert page.evaluate("getComputedStyle(document.querySelector('.corpus-detail')).overflowY === 'auto'")
        page.click("button.corpus-xref[data-corpus-xref='xref-1']")
        page.wait_for_selector("#corpus-snippet-overlay .corpus-snippet-loading")
        assert "Loading source context" in page.text_content("#corpus-snippet-overlay")
        snippet_release.set()
        page.wait_for_selector("#corpus-snippet-overlay .corpus-listing-row.active")
        assert "_custom+intena" in page.text_content("#corpus-snippet-overlay .corpus-listing-row.active")
        page.press_key("Escape")
        page.wait_for_expression("document.querySelector('#corpus-snippet-overlay') === null")
        page.click(".corpus-add-button")
        page.wait_for_selector(".corpus-import-menu")
        assert "Promote file" in page.text_content(".corpus-import-menu")
        assert "Promote containing disk" in page.text_content(".corpus-import-menu")
        page.click("[data-corpus-import-mode='target']")
        page.wait_for_expression(f"location.pathname === '/{project.id}'", timeout=10.0)
        page.wait_for_expression("document.querySelectorAll('.listing-row').length === 2")
        page.wait_for_expression("document.querySelector('.listing-row-focus')?.dataset.rowIndex === '0'")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_app_slot_navigation_drills_to_refs(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_app_slots")
    rows = [
        ListingRow(
            row_id="rs0",
            kind="directive",
            text="app_0234 RS.L 1\n",
            stable_key="app-rs",
        ),
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="move.l app_DOSBase(a6),d0\n",
            stable_key="app-read",
            addr=0x20,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_DOSBase", 0x26, "A6", 0, "read"),),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="move.l d0,app_0234(a6)\n",
            stable_key="app-write",
            addr=0x30,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_0234", 0x0234, "A6", 1, "write"),),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="lea.l app_0234(a6),a0\n",
            stable_key="app-address",
            addr=0x40,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
            app_slot_refs=(AppSlotRef("app_0234", 0x0234, "A6", 0, "address"),),
        ),
    ]
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length >= 3")
        page.click("#open-navigation")
        page.wait_for_selector("#navigation-overlay")
        page.select_value("[data-navigation-class='1']", "app-slots")
        page.wait_for_expression("document.body.textContent.includes('app_0234')")
        assert page.evaluate("document.querySelector('.navigation-summary')?.textContent") == "2 entries"

        page.evaluate(
            """
            Array.from(document.querySelectorAll('.navigation-item'))
              .find((item) => item.textContent.includes('app_0234') && item.textContent.includes('2 refs'))
              .click()
            """
        )
        page.wait_for_expression("document.querySelector('.navigation-summary')?.textContent === 'app_0234: 2 refs'")
        assert page.evaluate(
            "Array.from(document.querySelectorAll('.navigation-access-badge')).map((badge) => badge.textContent).join('|')"
        ) == "W|A"
        page.evaluate(
            """
            Array.from(document.querySelectorAll('.navigation-item'))
              .find((item) => item.textContent.includes('move.l d0,app_0234(a6)'))
              .click()
            """
        )
        page.wait_for_expression(
            "document.querySelector('.listing-row-focus')?.dataset.rowStableKey === 'app-write'",
            timeout=10.0,
        )
        page.evaluate(
            """
            Array.from(document.querySelectorAll('.listing-app-slot-reference'))
              .find((item) => item.textContent === 'app_DOSBase')
              .click()
            """
        )
        page.wait_for_expression("document.querySelector('.navigation-summary')?.textContent === 'app_DOSBase: 1 ref'")
        assert page.evaluate("document.querySelector('.navigation-item.active')?.textContent.includes('move.l app_DOSBase(a6),d0')")
        page.evaluate(
            """
            Array.from(document.querySelectorAll('.listing-app-slot-reference'))
              .find((item) => item.textContent === 'app_0234' && item.closest('.listing-row')?.dataset.rowStableKey === 'app-address')
              .click()
            """
        )
        page.wait_for_expression("document.querySelector('.navigation-summary')?.textContent === 'app_0234: 2 refs'")
        assert page.evaluate("document.querySelector('.navigation-item.active')?.textContent.includes('lea.l app_0234(a6),a0')")
        page.evaluate("loadListingWindow(state.project, null, 0, 20, {start: 0, count: 20})")
        page.wait_for_selector(".listing-app-slot-definition[data-app-slot-symbol='app_0234']")
        page.click(".listing-app-slot-definition[data-app-slot-symbol='app_0234']")
        page.wait_for_expression("document.querySelector('.navigation-summary')?.textContent === 'app_0234: 2 refs'")
        assert page.evaluate("document.querySelector('.navigation-item.active')?.textContent.includes('move.l d0,app_0234(a6)')")
        page.click("[data-navigation-app-slots-root='1']")
        assert page.evaluate("document.querySelector('.navigation-item.active')?.textContent.includes('app_0234')")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_virtual_listing_scrolls_and_navigation_uses_global_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_large")
    rows: list[ListingRow] = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="start:\n",
            addr=0,
            label="start:",
            analysis_generation="full",
        )
    ]
    for index in range(1, 899):
        rows.append(
            ListingRow(
                row_id=f"r{index}",
                kind="instruction",
                text="rts\n",
                addr=index * 2,
                opcode_or_directive="rts",
                analysis_generation="full",
            )
        )
    rows.append(
        ListingRow(
            row_id="r899",
            kind="label",
            text="far_target:\n",
            addr=1798,
            label="far_target:",
            analysis_generation="full",
        )
    )
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_app_event(
            "amiga:project-rendered",
            f"detail.projectId === {json.dumps(project.id)}",
            timeout=10.0,
        )
        page.wait_for_expression("document.querySelectorAll('.listing-row').length > 0")
        assert page.evaluate("document.querySelectorAll('.listing-row').length < 600")
        assert page.evaluate("document.querySelector('.listing-scroll-spacer').offsetHeight > 10000")
        assert not page.evaluate("document.body.textContent.includes('far_target:')")

        page.wait_for_app_event_after_js(
            "amiga:listing-window-rendered",
            """
            (() => {
              scrollListingViewport(state.project, "end");
              return true;
            })()
            """,
            "detail.start > 0 && detail.end === detail.totalRows",
            timeout=10.0,
        )
        assert page.evaluate("document.body.textContent.includes('far_target:')")
        assert page.evaluate("document.querySelectorAll('.listing-row').length < 600")

        page.wait_for_app_event_after_js(
            "amiga:listing-window-rendered",
            """
            (() => {
              scrollListingViewport(state.project, "home");
              return true;
            })()
            """,
            "detail.start === 0",
            timeout=10.0,
        )
        page.click("#open-navigation")
        page.wait_for_selector("#navigation-overlay")
        page.select_value("[data-navigation-class='1']", "labels")
        page.wait_for_expression(
            "Array.from(document.querySelectorAll('.navigation-item')).some((item) => item.textContent.includes('far_target'))"
        )
        page.wait_for_app_event_after_js(
            "amiga:listing-row-focused",
            """
            Array.from(document.querySelectorAll('.navigation-item'))
              .find((item) => item.textContent.includes('far_target'))
              .click()
            """,
            "detail.addr === 1798",
            timeout=10.0,
        )
        page.press_key("Escape")
        page.wait_for_expression("document.querySelector('#navigation-overlay') === null")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_virtual_listing_pagedown_fetches_low_latency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_pagedown")
    rows = [
        ListingRow(
            row_id=f"r{index}",
            kind="instruction",
            text="rts\n",
            addr=index * 2,
            opcode_or_directive="rts",
            analysis_generation="full",
        )
        for index in range(1000)
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length > 0")
        assert page.evaluate("getComputedStyle(document.querySelector('.listing-row')).alignItems") == "center"
        assert page.evaluate("getComputedStyle(document.querySelector('.listing-row')).lineHeight") == "20px"
        page.evaluate("document.querySelector('#listing-viewport').focus()")
        started = time.perf_counter()
        page.evaluate(
            """
            (() => {
              scrollListingViewport(state.project, "end");
              return true;
            })()
            """
        )
        page.wait_for_expression(
            "Number(document.querySelector('.listing-row')?.dataset.rowAddr || 0) > 0",
            timeout=2.0,
        )
        assert time.perf_counter() - started < 1.0
        assert page.evaluate("document.querySelectorAll('.listing-row').length < 600")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_corpus_tab_renders_before_corpus_fetches_finish(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "list_projects", list)
    feature_entered = threading.Event()
    feature_release = threading.Event()

    def fake_feature_list():
        feature_entered.set()
        feature_release.wait(timeout=5.0)
        return [
            {
                "feature": "hardware:custom",
                "target_count": 1,
                "occurrence_count": 1,
                "source_example_count": 1,
                "source_target_count": 1,
            }
        ]

    monkeypatch.setattr(disasm_server.corpus_usage, "feature_list", fake_feature_list)
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "query_targets",
        lambda *, feature=None, group=None, platform=None, q=None, source_only=False, limit=None, offset=0, projects=None: [],
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": base_url})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector("[data-home-view='corpus']")
        page.click("[data-home-view='corpus']")
        assert feature_entered.wait(timeout=5.0)
        page.wait_for_selector(".page-corpus")
        assert "Loading features" in page.text_content("#corpus-feature")
        feature_release.set()
        page.wait_for_expression("document.querySelector('#corpus-feature')?.textContent.includes('1 source')")
        assert page.evaluate("compareInlineSourceText('dc.b $EF', 'dc.b $EE').left.includes('corpus-inline-diff')")
        assert page.evaluate("compareInlineSourceText('dc.b $EF', 'dc.b $EE').right.includes('corpus-inline-diff')")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_corpus_target_selection_ignores_stale_xrefs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "list_projects", list)
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "feature_list",
        lambda: [
            {
                "feature": "hardware:custom",
                "target_count": 2,
                "occurrence_count": 2,
                "source_example_count": 2,
                "source_target_count": 2,
            }
        ],
    )
    monkeypatch.setattr(
        disasm_server.corpus_usage,
        "query_targets",
        lambda *, feature=None, group=None, platform=None, q=None, source_only=False, limit=None, offset=0, projects=None: [
            {
                "id": "slow-target",
                "platform": "amiga-hunk",
                "count": 1,
                "source_example_count": 1,
                "origin": {"in_image_path": "slow"},
                "source_context": {"target_name": "slow"},
                "project_coverage": {"import_modes": []},
                "tags": ["hardware:custom"],
            },
            {
                "id": "fast-target",
                "platform": "amiga-hunk",
                "count": 1,
                "source_example_count": 1,
                "origin": {"in_image_path": "fast"},
                "source_context": {"target_name": "fast"},
                "project_coverage": {"import_modes": []},
                "tags": ["hardware:custom"],
            },
        ],
    )
    slow_entered = threading.Event()
    slow_release = threading.Event()

    def fake_query_xrefs(*, target_id=None, feature=None, group=None, source_only=False, limit=None, offset=0):
        if target_id == "slow-target":
            slow_entered.set()
            slow_release.wait(timeout=5.0)
        text = "slow-ref" if target_id == "slow-target" else "fast-ref"
        rows = [
            {
                "id": f"{target_id}-xref",
                "target_id": target_id,
                "feature": "hardware:custom",
                "kind": "hardware_ref",
                "row_index": 0,
                "text": text,
            }
        ]
        if limit is not None:
            rows = rows[offset:offset + limit]
        return rows

    monkeypatch.setattr(disasm_server.corpus_usage, "query_xrefs", fake_query_xrefs)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": base_url})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector("[data-home-view='corpus']")
        page.click("[data-home-view='corpus']")
        page.wait_for_selector(".corpus-card-main")
        page.evaluate("document.querySelectorAll('.corpus-card-main')[0].click()")
        assert slow_entered.wait(timeout=5.0)
        page.evaluate("document.querySelectorAll('.corpus-card-main')[1].click()")
        page.wait_for_expression("document.querySelector('.corpus-detail')?.textContent.includes('fast-ref')")
        slow_release.set()
        time.sleep(0.2)
        assert "fast-ref" in page.text_content(".corpus-detail")
        assert "slow-ref" not in page.text_content(".corpus-detail")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_stats_overlay_shows_fetch_latency(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_stats")
    rows = [
        ListingRow(
            row_id=f"r{index}",
            kind="instruction",
            text="rts\n",
            addr=index * 2,
            opcode_or_directive="rts",
            analysis_generation="full",
        )
        for index in range(400)
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_app_event(
            "amiga:project-rendered",
            f"detail.projectId === {json.dumps(project.id)}",
            timeout=10.0,
        )
        page.wait_for_expression("document.querySelectorAll('.listing-row').length > 0")
        page.wait_for_app_event_after_js(
            "amiga:listing-window-rendered",
            """
            (async () => {
              await loadListingWindow(state.project, null, 0, 80, {
                start: 120,
                count: 80,
                preserveScroll: true,
              });
              return true;
            })()
            """,
            "detail.start === 120",
            timeout=10.0,
        )
        page.click("#open-stats")
        page.wait_for_selector("#stats-overlay")
        assert page.evaluate("document.querySelectorAll('.stats-tab').length === 2")
        assert page.evaluate("document.querySelector('.stats-latency-graph polyline') !== null")
        assert page.evaluate("document.querySelector('.stats-grid')?.textContent.includes('Median')")
        assert page.evaluate("document.querySelector('.stats-grid')?.textContent.includes('Mean')")
        assert page.evaluate("document.querySelector('.stats-latest')?.textContent.includes('Latest:')")
        assert page.evaluate("document.querySelector('.stats-latest')?.textContent.includes('queue')")
        assert page.evaluate("document.querySelector('.stats-latest')?.textContent.includes('fetch')")
        assert page.evaluate("document.querySelector('.stats-latest')?.textContent.includes('render')")
        assert page.evaluate("state.stats.fetchSamples.at(-1).queueMs !== undefined")
        assert page.evaluate("state.stats.fetchSamples.at(-1).fetchMs !== undefined")
        assert page.evaluate("state.stats.fetchSamples.at(-1).renderMs !== undefined")
        page.click("[data-stats-tab='jobs']")
        page.wait_for_expression("document.querySelector('.stats-tab.active')?.textContent === 'Jobs'")
        page.press_key("Escape")
        page.wait_for_expression("document.querySelector('#stats-overlay') === null")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_full_enrichment_preserves_virtual_scroll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_progressive")

    def make_rows(generation: str, final_label: str) -> list[ListingRow]:
        rows: list[ListingRow] = []
        for index in range(899):
            rows.append(
                ListingRow(
                    row_id=f"{generation}-{index}",
                    kind="instruction",
                    text="rts\n",
                    addr=index * 2,
                    opcode_or_directive="rts",
                    analysis_generation=generation,
                )
            )
        rows.append(
            ListingRow(
                row_id=f"{generation}-899",
                kind="label",
                text=f"{final_label}:\n",
                addr=1798,
                label=f"{final_label}:",
                analysis_generation=generation,
            )
        )
        return rows

    full_rows = [
        ListingRow(row_id="full-comment", kind="comment", text="; full header\n", analysis_generation="full"),
        ListingRow(row_id="full-equ", kind="directive", text="app_SIZEOF EQU __RS\n", analysis_generation="full"),
        ListingRow(row_id="full-include", kind="directive", text='INCLUDE "exec/exec_lib.i"\n', analysis_generation="full"),
        ListingRow(row_id="full-section", kind="directive", text="    SECTION section,code\n", analysis_generation="full"),
        *make_rows("full", "far_full"),
    ]
    full_started = threading.Event()
    release_full = threading.Event()

    def build_artifact(project_name: str) -> tuple[int, dict[str, object], _FakeCListingArtifact]:
        full_started.set()
        assert release_full.wait(timeout=15.0)
        return len(full_rows), {}, _FakeCListingArtifact(full_rows, project_name=project_name)

    disasm_server._PROJECT_LISTING_CACHE_KEY.clear()
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "stable-cache")
    monkeypatch.setattr(disasm_server, "build_project_listing_artifact_profile", build_artifact)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        assert full_started.wait(timeout=10.0)
        release_full.set()
        page.wait_for_expression(
            "document.querySelector('.listing-row')?.dataset.analysisGeneration === 'full'",
            timeout=15.0,
        )
        before_scroll = page.evaluate("document.querySelector('#listing-viewport').scrollTop")
        page.wait_for_app_event_after_js(
            "amiga:listing-window-rendered",
            """
            (() => {
              scrollListingViewport(state.project, "end");
              return true;
            })()
            """,
            "detail.start > 0 && detail.generation === 'full'",
            timeout=10.0,
        )
        assert page.evaluate("document.body.textContent.includes('far_full:')")
        assert page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row')).every((row) => row.dataset.analysisGeneration === 'full')"
        )
        after_scroll = page.evaluate("document.querySelector('#listing-viewport').scrollTop")
        assert after_scroll >= before_scroll - 44
        assert page.evaluate("document.querySelectorAll('.listing-row').length < 600")
        page.wait_for_app_event_after_js(
            "amiga:listing-window-rendered",
            """
            (() => {
              scrollListingViewport(state.project, "home");
              return true;
            })()
            """,
            "detail.start === 0 && detail.generation === 'full'",
            timeout=10.0,
        )
        page.wait_for_expression(
            "document.querySelector('.listing-row')?.dataset.rowCode.trim() === '; full header'",
            timeout=10.0,
        )
        assert page.evaluate("document.body.textContent.includes('INCLUDE \"exec/exec_lib.i\"')")
        assert page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row')).some((row) => row.dataset.rowCode.trim() === 'app_SIZEOF EQU __RS')"
        )
        assert page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row')).some((row) => row.dataset.rowCode.trim() === 'SECTION section,code')"
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_full_enrichment_keeps_section_anchor_when_prefix_rows_appear(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_section_anchor")
    full_rows = [
        ListingRow(row_id="include", kind="directive", text='INCLUDE "exec/io.i"\n', analysis_generation="full"),
        ListingRow(row_id="rsset", kind="directive", text="RSSET 0\n", analysis_generation="full"),
        ListingRow(row_id="rs", kind="directive", text="app_ULONG RS.L 1\n", analysis_generation="full"),
        ListingRow(row_id="equ", kind="directive", text="app_SIZEOF EQU __RS\n", analysis_generation="full"),
        ListingRow(
            row_id="full-section",
            kind="directive",
            text="    SECTION section,code\n",
            analysis_generation="full",
        ),
        ListingRow(
            row_id="full-code",
            kind="instruction",
            text="bra.b h0_0036\n",
            addr=0,
            opcode_or_directive="bra.b",
            operand_text="h0_0036",
            analysis_generation="full",
        ),
    ]
    full_started = threading.Event()
    release_full = threading.Event()

    def build_artifact(project_name: str) -> tuple[int, dict[str, object], _FakeCListingArtifact]:
        full_started.set()
        assert release_full.wait(timeout=15.0)
        return len(full_rows), {}, _FakeCListingArtifact(full_rows, project_name=project_name)

    disasm_server._PROJECT_LISTING_CACHE_KEY.clear()
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "stable-cache")
    monkeypatch.setattr(disasm_server, "build_project_listing_artifact_profile", build_artifact)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        assert full_started.wait(timeout=10.0)
        release_full.set()
        page.wait_for_expression(
            "document.querySelector('.listing-row')?.dataset.analysisGeneration === 'full'",
            timeout=10.0,
        )
        page.wait_for_app_event_after_js(
            "amiga:listing-window-rendered",
            """
            (() => {
              scrollListingViewport(state.project, "home");
              return true;
            })()
            """,
            "detail.start === 0 && detail.generation === 'full'",
            timeout=10.0,
        )
        page.wait_for_expression(
            "document.querySelector('.listing-row')?.dataset.rowCode.includes('INCLUDE')",
            timeout=10.0,
        )
        assert page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row')).some((row) => row.dataset.rowCode.trim() === 'app_ULONG RS.L 1')"
        )
        assert page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row')).some((row) => row.dataset.rowCode.trim() === 'app_SIZEOF EQU __RS')"
        )
        assert page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row')).some((row) => row.dataset.rowCode.trim() === 'SECTION section,code')"
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_navigation_overlay_opens_on_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_demo")
    rows = [
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0),
        ListingRow(row_id="r1", kind="instruction", text="jsr sub_0008\n", addr=0),
        ListingRow(row_id="r2", kind="label", text="sub_0008:\n", addr=8),
        ListingRow(row_id="r3", kind="instruction", text="rts\n", addr=8),
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length === 4")

        page.click("#open-navigation")

        page.wait_for_expression("document.querySelector('#navigation-overlay') !== null")
        page.evaluate(
            """
            (() => {
              const select = document.querySelector("[data-navigation-class='1']");
              select.value = "labels";
              select.dispatchEvent(new Event("change", {bubbles: true}));
              return true;
            })()
            """
        )
        page.wait_for_expression("document.querySelectorAll('.navigation-item').length >= 2")
        assert page.evaluate("document.querySelectorAll('.navigation-item').length") >= 2
        assert page.evaluate("document.querySelector('.navigation-item')?.textContent.includes('start')")
        page.evaluate(
            """
            (() => {
              document.querySelector(".navigation-item")?.click();
              closeNavigationOverlay();
              return true;
            })()
            """
        )
        page.wait_for_expression("document.querySelector('#navigation-overlay') === null")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_navigation_overlay_list_scrolls_with_many_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_many_nav_entries")
    rows = [
        ListingRow(
            row_id=f"r{index}",
            kind="label",
            text=f"label_{index:02d}:\n",
            addr=index * 4,
            label=f"label_{index:02d}:",
        )
        for index in range(40)
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length === 40")

        page.click("#open-navigation")
        page.wait_for_selector("#navigation-overlay")
        page.select_value("[data-navigation-class='1']", "labels")
        page.wait_for_expression("document.querySelectorAll('.navigation-item').length === 40")

        metrics = page.evaluate(
            """
            (() => {
              const list = document.querySelector("[data-navigation-list='1']");
              return {
                clientHeight: list.clientHeight,
                scrollHeight: list.scrollHeight,
                count: document.querySelectorAll(".navigation-item").length,
              };
            })()
            """
        )
        assert metrics["count"] == 40
        assert metrics["scrollHeight"] > metrics["clientHeight"]

        page.evaluate(
            """
            (() => {
              const list = document.querySelector("[data-navigation-list='1']");
              list.scrollTop = list.scrollHeight;
              list.dispatchEvent(new Event("scroll"));
              return true;
            })()
            """
        )
        page.wait_for_expression(
            "document.querySelector('[data-navigation-list=\"1\"]').scrollTop > 0"
        )
        assert page.evaluate(
            "document.querySelectorAll('.navigation-item')[39]?.textContent.includes('label_39')"
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_page_level_listing_keys_route_to_listing_viewport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_page_level_listing_keys")
    rows = [
        ListingRow(
            row_id=f"r{index}",
            kind="label",
            text=f"label_{index:03d}:\n",
            addr=index * 4,
            label=f"label_{index:03d}:",
        )
        for index in range(120)
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelector('#listing-viewport')?.scrollHeight > document.querySelector('#listing-viewport')?.clientHeight")
        page.evaluate(
            """
            (() => {
              const viewport = document.querySelector("#listing-viewport");
              viewport.scrollTop = 0;
              viewport.blur();
              document.body.tabIndex = -1;
              document.body.focus();
              return document.activeElement === document.body;
            })()
            """
        )

        page.press_key("PageDown")
        page.wait_for_expression("document.querySelector('#listing-viewport').scrollTop > 0")
        page.press_key("PageDown", modifiers=2)
        page.wait_for_expression(
            """
            (() => {
              const viewport = document.querySelector("#listing-viewport");
              return viewport.scrollTop >= viewport.scrollHeight - viewport.clientHeight - 4;
            })()
            """
        )
        page.press_key("PageUp", modifiers=2)
        page.wait_for_expression("document.querySelector('#listing-viewport').scrollTop === 0")

        page.click("#open-navigation")
        page.wait_for_selector("#navigation-overlay")
        page.select_value("[data-navigation-class='1']", "labels")
        page.wait_for_expression("document.querySelectorAll('.navigation-item').length === 120")
        page.press_key("PageDown")
        page.wait_for_expression("document.querySelector('.navigation-item.active')?.textContent.includes('label_010')")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_navigation_click_preserves_list_scroll_after_jump(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_many_typed_nav_entries")
    rows = [
        ListingRow(
            row_id=f"r{index}",
            kind="data",
            text=f"dc.b ${index:02X}\n",
            addr=index * 4,
            comment_text="string",
            stable_key=f"data-{index:02d}",
        )
        for index in range(60)
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length >= 1")

        page.click("#open-navigation")
        page.wait_for_selector("#navigation-overlay")
        page.select_value("[data-navigation-class='1']", "typed-data")
        page.wait_for_expression("document.querySelectorAll('.navigation-item').length === 60")
        page.evaluate(
            """
            (() => {
              const list = document.querySelector("[data-navigation-list='1']");
              const item = document.querySelectorAll(".navigation-item")[35];
              list.scrollTop = Math.max(0, item.offsetTop - list.clientHeight + item.offsetHeight + 12);
              return true;
            })()
            """
        )
        page.wait_for_expression("document.querySelector('[data-navigation-list=\"1\"]').scrollTop > 0")
        page.wait_for_app_event_after_js(
            "amiga:listing-row-focused",
            """
            document.querySelectorAll(".navigation-item")[35].click();
            """,
            "detail.rowIndex === 35",
            timeout=10.0,
        )
        page.wait_for_expression(
            """
            (() => {
              const list = document.querySelector("[data-navigation-list='1']");
              const active = document.querySelector(".navigation-item.active");
              if (!list || !active || !active.textContent.includes("string")) return false;
              const listRect = list.getBoundingClientRect();
              const activeRect = active.getBoundingClientRect();
              return list.scrollTop > 0 && activeRect.top >= listRect.top && activeRect.bottom <= listRect.bottom;
            })()
            """
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_api_navigation_uses_row_index_for_duplicate_offsets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_duplicate_api_offsets")
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="jsr loc_shared(pc)\n",
            stable_key="h0-call",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
        ListingRow(
            row_id="r1",
            kind="label",
            text="loc_0010:\n",
            stable_key="h1-label",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            stable_key="h1-call",
            addr=0x10,
            opcode_or_directive="jsr",
            operand_text="_LVOSetPointer(a6)",
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(
        project.id,
        rows,
        api_calls_by_row_id={
            "r2": {
                "library": "intuition.library",
                "function": "SetPointer",
                "note_kind": 0,
                "call_kind": 1,
                "inputs": [],
            }
        },
    )
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length === 3")

        page.click("#open-navigation")
        page.wait_for_selector("#navigation-overlay")
        page.select_value("[data-navigation-class='1']", "api-calls")
        page.wait_for_expression("document.querySelectorAll('.navigation-item').length === 1")

        assert page.evaluate("document.querySelector('.navigation-item-addr')?.textContent") == "h1:0010"
        assert page.evaluate(
            "document.querySelector('.navigation-item-text')?.textContent"
        ) == "SetPointer (intuition.library)"
        page.evaluate("document.querySelector('.navigation-item')?.click()")
        page.wait_for_expression(
            "document.querySelector('.listing-row-focus')?.dataset.rowStableKey === 'h1-call'"
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_listing_symbol_links_are_focusable_and_jump(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_symbol_links")
    rows: list[ListingRow] = [
        ListingRow(row_id="global-rs", kind="directive", text="app_ULONG RS.L 1\n"),
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0, label="start"),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr target.l\n",
            addr=2,
            opcode_or_directive="jsr",
            operand_text="target.l",
            operand_parts=(
                SemanticOperand(kind="symbol", text="target", metadata=SymbolOperandMetadata(symbol="target")),
            ),
        ),
        ListingRow(
            row_id="r2",
            kind="instruction",
            text="move.l d0,a6\n",
            addr=4,
            opcode_or_directive="move.l",
            operand_text="d0,a6",
        ),
        ListingRow(
            row_id="r3",
            kind="instruction",
            text="jsr _LVOSetSignal(a6)\n",
            addr=6,
            opcode_or_directive="jsr",
            operand_text="_LVOSetSignal(a6)",
        ),
        ListingRow(
            row_id="r4",
            kind="instruction",
            text="move.l #target,$006C.w\n",
            addr=8,
            opcode_or_directive="move.l",
            operand_text="#target,$006C.w",
            operand_parts=(
                SemanticOperand(kind="symbol", text="target", metadata=SymbolOperandMetadata(symbol="target")),
            ),
        ),
        ListingRow(
            row_id="r5",
            kind="instruction",
            text="dbf.w d1,target\n",
            addr=10,
            opcode_or_directive="dbf.w",
            operand_text="d1,target",
            operand_parts=(
                SemanticOperand(kind="symbol", text="target", metadata=SymbolOperandMetadata(symbol="target")),
            ),
        ),
        ListingRow(
            row_id="r6",
            kind="instruction",
            text="move.l #target,d0\n",
            addr=12,
            opcode_or_directive="move.l",
            operand_text="#target,d0",
        ),
        ListingRow(
            row_id="r7",
            kind="instruction",
            text="move.l #target,d1\n",
            addr=14,
            opcode_or_directive="move.l",
            operand_text="#target,d1",
            operand_parts=(SemanticOperand(kind="symbol", text="target"),),
        ),
        ListingRow(
            row_id="r8",
            kind="data",
            text="dc.l target\n",
            addr=16,
            opcode_or_directive="dc.l",
            operand_text="target",
            operand_parts=(
                SemanticOperand(kind="symbol", text="target", metadata=SymbolOperandMetadata(symbol="target")),
            ),
        ),
        ListingRow(
            row_id="r9",
            kind="data",
            text="dc.w target-base\n",
            addr=18,
            opcode_or_directive="dc.w",
            operand_text="target-base",
            operand_parts=(
                SemanticOperand(kind="symbol", text="target", metadata=SymbolOperandMetadata(symbol="target")),
            ),
        ),
    ]
    for index in range(10, 180):
        rows.append(
            ListingRow(
                row_id=f"r{index}",
                kind="instruction",
                text="rts\n",
                addr=index * 2,
                opcode_or_directive="rts",
            )
        )
    rows.append(ListingRow(row_id="target", kind="label", text="target:\n", addr=400, label="target"))

    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_app_event(
            "amiga:project-rendered",
            f"detail.projectId === {json.dumps(project.id)}",
            timeout=10.0,
        )
        page.wait_for_selector(".listing-symbol-reference[data-symbol-name='target']")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"app_ULONG\"]')")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"RS\"]')")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"d0\"]')")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"a6\"]')")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"_LVOSetSignal\"]')")
        assert page.evaluate(
            "document.querySelectorAll('.listing-symbol-reference[data-symbol-name=\"target\"]').length === 5"
        )
        page.evaluate(
            """
            state.navigation.entries = null;
            renderVirtualListingWindow(state.project, {
              rows: state.listingRows,
              start: state.virtualListing.start,
              end: state.virtualListing.end,
              total_rows: state.virtualListing.totalRows,
              analysis_generation: state.virtualListing.generation,
            }, true);
            """
        )
        assert page.evaluate(
            "document.querySelectorAll('.listing-symbol-reference[data-symbol-name=\"target\"]').length === 5"
        )
        assert page.evaluate("document.querySelector('.listing-symbol-reference[data-symbol-name=\"target\"]')?.tabIndex === 0")
        page.evaluate("document.querySelector('.listing-symbol-reference[data-symbol-name=\"target\"]').focus()")
        assert page.evaluate("document.activeElement?.dataset.symbolName === 'target'")
        focus_wait = page.begin_app_event_wait(
            "amiga:listing-row-focused",
            "detail.addr === 400",
            timeout=10.0,
        )
        page.press_key("Enter")
        page.finish_app_event_wait(focus_wait, timeout=10.0)
        assert page.evaluate("document.querySelector('#listing-viewport')?.textContent.includes('target:')")

        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_app_event(
            "amiga:project-rendered",
            f"detail.projectId === {json.dumps(project.id)}",
            timeout=10.0,
        )
        page.wait_for_selector(".listing-symbol-reference[data-symbol-name='target']")
        page.wait_for_app_event_after_js(
            "amiga:listing-row-focused",
            "document.querySelector('.listing-symbol-reference[data-symbol-name=\"target\"]').click()",
            "detail.addr === 400",
            timeout=10.0,
        )
        page.click(".listing-symbol-definition[data-symbol-name='target']")
        page.wait_for_expression("document.querySelector('.navigation-summary')?.textContent === 'target: 6 refs'")
        assert page.evaluate("document.querySelector('[data-navigation-class=\"1\"]')?.value") == "labels"
        assert page.evaluate(
            "document.querySelector('.navigation-item.active')?.textContent.includes('target:')"
        )
        assert page.evaluate(
            "document.querySelector('.navigation-item.active .navigation-access-badge')?.textContent"
        ) == "D"
        page.click("[data-navigation-labels-root='1']")
        assert page.evaluate("document.querySelector('.navigation-item.active')?.textContent.includes('target')")
        page.click("[data-navigation-close='1']")
        page.wait_for_expression("document.querySelector('#navigation-overlay') === null")

        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_app_event(
            "amiga:project-rendered",
            f"detail.projectId === {json.dumps(project.id)}",
            timeout=10.0,
        )
        page.wait_for_selector(".listing-symbol-reference[data-symbol-name='target']")
        page.evaluate(
            """
            document.querySelector('.listing-symbol-reference[data-symbol-name="target"]')
              .dispatchEvent(new MouseEvent('click', {bubbles: true, ctrlKey: true}))
            """
        )
        page.wait_for_expression("document.querySelector('.navigation-summary')?.textContent === 'target: 6 refs'")
        assert page.evaluate(
            "document.querySelector('.navigation-item.active')?.textContent.includes('jsr target.l')"
        )
        assert page.evaluate(
            "document.querySelector('.navigation-item.active .navigation-access-badge')?.textContent"
        ) == "R"
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_equate_navigation_lists_refs_and_source_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_equate_navigation")
    symbol = "disk_buffer_00067D00"
    rows = [
        ListingRow(
            row_id="equ",
            kind="directive",
            text=f"{symbol} EQU $67D00\n",
            stable_key="equate-def",
        ),
        ListingRow(
            row_id="ref",
            kind="instruction",
            text=f"lea.l {symbol},a0\n",
            stable_key="equate-ref",
            addr=0x20,
            opcode_or_directive="lea.l",
            operand_text=f"{symbol},a0",
            operand_parts=(
                SemanticOperand(
                    kind="absolute",
                    text=symbol,
                    metadata=SymbolOperandMetadata(symbol),
                ),
                SemanticOperand(kind="register", text="a0", register="a0"),
            ),
        ),
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_app_event(
            "amiga:project-rendered",
            f"detail.projectId === {json.dumps(project.id)}",
            timeout=10.0,
        )
        page.wait_for_selector(f".listing-equate-definition[data-equate-symbol='{symbol}']")
        page.wait_for_selector(f".listing-equate-reference[data-equate-symbol='{symbol}']")
        page.evaluate(
            """
            state.navigation.entries = null;
            renderVirtualListingWindow(state.project, {
              rows: state.listingRows,
              start: state.virtualListing.start,
              end: state.virtualListing.end,
              total_rows: state.virtualListing.totalRows,
              analysis_generation: state.virtualListing.generation,
            }, true);
            """
        )
        page.wait_for_selector(f".listing-equate-reference[data-equate-symbol='{symbol}']")

        page.click("#open-navigation")
        page.wait_for_selector("#navigation-overlay")
        page.select_value("[data-navigation-class='1']", "equates")
        page.wait_for_expression(
            f"document.querySelector('.navigation-item')?.textContent.includes({json.dumps(symbol + ' EQU $67D00')})"
        )
        assert page.evaluate("document.querySelector('.navigation-summary')?.textContent") == "1 entries"

        page.click(f".listing-equate-definition[data-equate-symbol='{symbol}']")
        page.wait_for_expression(
            f"document.querySelector('.navigation-summary')?.textContent === {json.dumps(symbol + ': 2 refs')}"
        )
        assert page.evaluate("document.querySelector('[data-navigation-class=\"1\"]')?.value") == "equates"
        assert page.evaluate(
            "document.querySelector('.navigation-item.active .navigation-access-badge')?.textContent"
        ) == "D"
        page.click("[data-navigation-equates-root='1']")
        assert page.evaluate("document.querySelector('.navigation-item.active')?.textContent.includes('EQU $67D00')")

        page.click(f".listing-equate-reference[data-equate-symbol='{symbol}']")
        page.wait_for_expression(
            f"document.querySelector('.navigation-summary')?.textContent === {json.dumps(symbol + ': 2 refs')}"
        )
        assert page.evaluate("document.querySelector('.navigation-item.active')?.textContent.includes('lea.l')")
        assert page.evaluate(
            "document.querySelector('.navigation-item.active .navigation-access-badge')?.textContent"
        ) == "R"
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_listing_layout_aligns_globals_and_shows_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_layout")
    rows = [
        ListingRow(row_id="include", kind="directive", text='INCLUDE "exec/io.i"\n'),
        ListingRow(row_id="rsset", kind="directive", text="    RSSET LIB_SIZE\n"),
        ListingRow(row_id="rsgap", kind="directive", text="    RS.B 24\n"),
        ListingRow(row_id="long-rs", kind="directive", text="app_timer_device_iorequest RS.L 1\n"),
        ListingRow(row_id="equ", kind="directive", text="app_SIZEOF EQU __RS\n"),
        ListingRow(row_id="section", kind="directive", text="    SECTION section,code\n"),
        ListingRow(
            row_id="data",
            kind="data",
            text="DC.B $12,$34\n",
            addr=0,
            bytes=b"\x12\x34",
            opcode_or_directive="DC.B",
            operand_text="$12,$34",
        ),
        ListingRow(
            row_id="code",
            kind="instruction",
            text="rts\n",
            addr=2,
            start_offset=2,
            end_offset=4,
            runtime_address=0x6102,
            bytes=b"\x4e\x75",
            opcode_or_directive="rts",
        ),
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector(".listing-row-instruction")
        global_left = page.evaluate(
            "document.querySelector('.listing-row-global .listing-code').getBoundingClientRect().left"
        )
        label_left = page.evaluate(
            "document.querySelector('.listing-row-instruction .listing-code').getBoundingClientRect().left"
        )
        section_left = page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row-directive'))"
            ".find((row) => row.dataset.rowCode.includes('SECTION'))"
            ".querySelector('.listing-code').getBoundingClientRect().left"
        )
        rs_text = page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row-directive'))"
            ".find((row) => row.dataset.rowCode.includes('RSSET'))"
            ".querySelector('.listing-code').textContent"
        )
        rsgap_text = page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row-directive'))"
            ".find((row) => row.dataset.rowCode.includes('RS.B'))"
            ".querySelector('.listing-code').textContent"
        )
        rsset_directive_left = page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row-directive'))"
            ".find((row) => row.dataset.rowCode.includes('RSSET'))"
            ".querySelector('.listing-global-directive').getBoundingClientRect().left"
        )
        rsgap_directive_left = page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row-directive'))"
            ".find((row) => row.dataset.rowCode.includes('RS.B'))"
            ".querySelector('.listing-global-directive').getBoundingClientRect().left"
        )
        equ_directive_left = page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row-directive'))"
            ".find((row) => row.dataset.rowCode.includes('EQU'))"
            ".querySelector('.listing-global-directive').getBoundingClientRect().left"
        )
        long_label_exists = page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row-directive'))"
            ".find((row) => row.dataset.rowCode.includes('app_timer_device_iorequest'))"
            ".querySelector('.listing-global-label') !== null"
        )
        long_label_title = page.evaluate(
            "Array.from(document.querySelectorAll('.listing-row-directive'))"
            ".find((row) => row.dataset.rowCode.includes('app_timer_device_iorequest'))"
            ".querySelector('.listing-global-label').getAttribute('title')"
        )
        long_label_clipped = page.evaluate(
            "(() => {"
            "const label = Array.from(document.querySelectorAll('.listing-row-directive')).find((row) => row.dataset.rowCode.includes('app_timer_device_iorequest')).querySelector('.listing-global-label');"
            "return label.scrollWidth > label.clientWidth;"
            "})()"
        )
        rs_visible_delta = page.evaluate(
            "(() => {"
            "const row = Array.from(document.querySelectorAll('.listing-row-directive')).find((item) => item.dataset.rowCode.includes('RSSET'));"
            "const directive = row.querySelector('.listing-global-directive');"
            "return Math.abs(directive.getBoundingClientRect().top - row.getBoundingClientRect().top);"
            "})()"
        )
        assert abs(global_left - label_left) < 1
        assert abs(section_left - label_left) < 1
        assert "RSSETLIB_SIZE" in "".join(rs_text.split())
        assert "RS.B24" in "".join(rsgap_text.split())
        assert abs(rsset_directive_left - rsgap_directive_left) < 1
        assert abs(rsset_directive_left - equ_directive_left) < 1
        assert long_label_exists
        assert long_label_title == "app_timer_device_iorequest"
        assert long_label_clipped
        assert rs_visible_delta < 4
        assert page.evaluate("document.querySelector('.listing-row-global .listing-offset')?.offsetParent !== null")
        assert page.evaluate("document.querySelector('.listing-row-instruction .listing-runtime')?.textContent === '6102'")
        assert page.evaluate("document.querySelector('.listing-row-instruction .listing-bytes')?.textContent === '4e75'")
        assert page.evaluate("document.querySelector('.listing-row-data .listing-bytes')?.textContent === '1234'")
        assert page.evaluate("document.querySelectorAll('.listing-column-resizer').length >= 4")
        assert page.evaluate(
            "getComputedStyle(document.querySelector('.listing-row-instruction .listing-bytes')).borderRightStyle === 'solid'"
        )
        original_bytes_width = page.evaluate(
            "parseFloat(getComputedStyle(document.querySelector('.listing-row-layer')).getPropertyValue('--listing-bytes-width'))"
        )
        handle = page.evaluate(
            "(() => {"
            "const rect = document.querySelector('.listing-row-instruction .listing-column-resizer-bytes').getBoundingClientRect();"
            "return {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};"
            "})()"
        )
        page.call(
            "Input.dispatchMouseEvent",
            {"type": "mousePressed", "x": handle["x"], "y": handle["y"], "button": "left", "buttons": 1},
        )
        page.call(
            "Input.dispatchMouseEvent",
            {"type": "mouseMoved", "x": handle["x"] + 40, "y": handle["y"], "button": "left", "buttons": 1},
        )
        page.call(
            "Input.dispatchMouseEvent",
            {"type": "mouseReleased", "x": handle["x"] + 40, "y": handle["y"], "button": "left", "buttons": 0},
        )
        assert page.evaluate(
            "parseFloat(getComputedStyle(document.querySelector('.listing-row-layer')).getPropertyValue('--listing-bytes-width'))"
        ) >= original_bytes_width + 20
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_navigation_buttons_move_history(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_demo")
    rows = [
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0),
        ListingRow(row_id="r1", kind="instruction", text="jsr sub_0008\n", addr=0),
        ListingRow(row_id="r2", kind="label", text="sub_0008:\n", addr=8),
        ListingRow(row_id="r3", kind="instruction", text="rts\n", addr=8),
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length === 4")
        page.click("#open-navigation")
        page.wait_for_selector("#navigation-overlay")
        page.select_value("[data-navigation-class='1']", "labels")
        page.wait_for_expression("document.querySelectorAll('.navigation-item').length === 2")
        page.evaluate("document.querySelectorAll('.navigation-item')[1].click()")
        page.wait_for_expression(
            "document.querySelector('[data-row-addr=\"8\"]')?.classList.contains('listing-row-focus')"
        )
        page.click("[data-navigation-close='1']")
        page.wait_for_expression("document.querySelector('#navigation-overlay') === null")

        page.click("#navigation-back")
        page.wait_for_expression(
            "Array.from(document.querySelectorAll('[data-row-addr=\"0\"]')).some((row) => row.classList.contains('listing-row-focus'))"
        )
        page.click("#navigation-forward")
        page.wait_for_expression(
            "Array.from(document.querySelectorAll('[data-row-addr=\"8\"]')).some((row) => row.classList.contains('listing-row-focus'))"
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_navigation_jumps_to_runtime_address(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_runtime_nav")
    rows = [
        ListingRow(
            row_id=f"r{index}",
            kind="instruction",
            text="nop\n",
            addr=index * 2,
            section_index=0,
            start_offset=index * 2,
            end_offset=index * 2 + 2,
            runtime_address=0x4000 + index * 2,
        )
        for index in range(320)
    ]
    target_index = 260
    rows[target_index] = ListingRow(
        row_id="runtime-target",
        kind="instruction",
        text="rts\n",
        addr=target_index * 2,
        section_index=0,
        start_offset=target_index * 2,
        end_offset=target_index * 2 + 2,
        runtime_address=0x6102,
        stable_key="runtime-target",
    )
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(project.id, rows)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector(".listing-row-instruction")
        assert not page.evaluate("document.querySelector('[data-row-stable-key=\"runtime-target\"]')")
        page.click("#open-navigation")
        page.wait_for_selector("[data-navigation-address-input='1']")
        page.fill("[data-navigation-address-input='1']", "$6102")
        page.click(".navigation-address-submit")
        page.wait_for_expression(
            "document.querySelector('[data-row-stable-key=\"runtime-target\"]')?.classList.contains('listing-row-focus')"
        )
        assert page.evaluate(
            "document.querySelector('[data-row-stable-key=\"runtime-target\"] .listing-runtime')?.textContent"
        ) == "6102"
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_project_delete_confirms_and_removes_project(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_demo")
    projects = [project]
    removed_projects: list[str] = []
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(disasm_server, "list_projects", lambda: list(projects))
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)

    def delete(project_id: str) -> None:
        removed_projects.append(project_id)
        projects.clear()

    monkeypatch.setattr(disasm_server, "delete_project", delete)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": base_url})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector(".project-delete-button")
        page.evaluate(
            """
            (() => {
              setTimeout(() => document.querySelector(".project-delete-button").click(), 0);
              return true;
            })()
            """
        )
        page.wait_for_event("Page.javascriptDialogOpening")
        page.handle_dialog(accept=True)
        page.wait_for_expression("document.querySelectorAll('.project-open-button').length === 0")

        assert removed_projects == [project.id]
        assert "No projects." in page.text_content("#app")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_real_c_backend_listing_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    _skip_without_c_backend()
    project_id = "amiga_hunk_genam"
    for artifact in disasm_server._PROJECT_C_LISTING_ARTIFACT_CACHE.values():
        artifact.close()
    disasm_server._PROJECT_C_LISTING_ARTIFACT_CACHE.clear()
    disasm_server._PROJECT_LISTING_CACHE_KEY.clear()
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(
        disasm_server,
        "mark_project_opened",
        lambda project_name: project_store.get_project(project_name),
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project_id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression(
            "document.querySelector('.listing-row')?.dataset.analysisGeneration === 'full'",
            timeout=45.0,
        )
        assert page.text_content("#project-title") == project_id
        assert page.evaluate("document.querySelectorAll('.listing-row').length > 0")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_upload_import_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project_root"
    (project_root / "targets").mkdir(parents=True)
    _temp_project_accessors(monkeypatch, project_root)
    upload_path = tmp_path / "DemoHunk"
    upload_path.write_bytes((PROJECT_ROOT / "bin" / "GenAm").read_bytes())
    expected_project_id = "amiga_hunk_demohunk"
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(expected_project_id, [
        ListingRow(row_id="r0", kind="label", text="uploaded_start:\n", addr=0),
        ListingRow(row_id="r1", kind="instruction", text="rts\n", addr=0),
    ])
    monkeypatch.setattr(
        disasm_server,
        "validate_amiga_hunk_executable_with_c_backend",
        lambda path, project_root: None,
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": base_url})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector("#new-project-media")
        page.set_file_input_files("#new-project-media", [upload_path])

        page.wait_for_expression(f"location.pathname === '/{expected_project_id}'", timeout=15.0)
        page.wait_for_expression("document.querySelectorAll('.listing-row').length === 2")
        assert page.text_content("#project-title") == expected_project_id
        assert (project_root / "bin" / "uploads" / "DemoHunk").exists()
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_upload_import_failure_shows_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project_root"
    (project_root / "targets").mkdir(parents=True)
    _temp_project_accessors(monkeypatch, project_root)
    upload_path = tmp_path / "NotAHunk"
    upload_path.write_bytes(b"not an amiga executable")
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(
        disasm_server,
        "validate_amiga_hunk_executable_with_c_backend",
        lambda path, project_root: (_ for _ in ()).throw(
            ValueError("Uploaded media is not an Amiga executable")
        ),
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": base_url})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector("#new-project-media")
        page.set_file_input_files("#new-project-media", [upload_path])

        page.wait_for_expression(
            "document.querySelector('#home-error')?.textContent.includes('Uploaded media is not')",
            timeout=15.0,
            fail_on_ui_error=False,
        )
        assert not (project_root / "targets" / "amiga_hunk_notahunk").exists()
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_disk_project_browsing_and_target_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _skip_without_c_backend()
    disk_project_id = "amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5"
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(
        disasm_server,
        "mark_project_opened",
        lambda project_name: project_store.get_project(project_name),
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{disk_project_id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.disk-target-button').length > 1")
        assert page.evaluate("document.querySelector('[data-tab=\"targets\"]')?.classList.contains('active')")
        page.click("[data-tab='contents']")
        page.wait_for_expression("document.querySelector(\"[data-tab-panel='contents']\").hidden === false")
        page.evaluate("document.querySelectorAll('.disk-target-button')[1].click()")
        page.wait_for_expression(
            "document.querySelectorAll('.listing-row-instruction').length > 0",
            timeout=45.0,
        )
        assert page.evaluate("location.pathname.includes('amiga_hunk_')")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_disk_project_shows_decompressed_child_target(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _skip_without_c_backend()
    disk_project_id = "amiga_disk_carrier-command-1994-kixx-budget"
    project_root = tmp_path / "project_root"
    shutil.copytree(
        PROJECT_ROOT / "targets" / disk_project_id,
        project_root / "targets" / disk_project_id,
    )
    (project_root / "bin").mkdir()
    shutil.copy2(
        PROJECT_ROOT / "bin" / "Carrier Command (1994)(Kixx)[h][budget].adf",
        project_root / "bin" / "Carrier Command (1994)(Kixx)[h][budget].adf",
    )
    _temp_project_accessors(monkeypatch, project_root)
    import_disk_entry_target(
        disk_project_id,
        entry_path="Carrier",
        project_root=project_root,
    )
    _append_carrier_decompressed_fixture(project_root, disk_project_id)
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(
        disasm_server,
        "mark_project_opened",
        lambda project_name: project_store.get_project(
            project_name,
            project_root=project_root,
        ),
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{disk_project_id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression(
            """
            Array.from(document.querySelectorAll('.disk-target-button'))
              .some((button) => button.textContent.toLowerCase().includes('carrier::rnc1-old_00004c40')
                && button.textContent.includes('decompressed')
                && button.textContent.toLowerCase().includes('rnc1')
                && button.textContent.includes('$4C40')
                && button.textContent.includes('$4000'))
            """,
            timeout=15.0,
        )
        page.wait_for_expression(
            """
            Array.from(document.querySelectorAll('.disk-target-button'))
              .some((button) => button.textContent.includes('Carrier')
                && !button.textContent.toLowerCase().includes('carrier::rnc1-old_00004c40')
                && button.textContent.includes('stub'))
            """,
            timeout=15.0,
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_disk_project_does_not_stub_badge_multi_payload_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    disk_project_id = "amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h"
    parent_target_id = f"{disk_project_id}__amiga_hunk_damocles_53b24620"
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(
        disasm_server,
        "mark_project_opened",
        lambda project_name: project_store.get_project(project_name),
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{disk_project_id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression(
            f"document.querySelector('[data-project-id=\"{parent_target_id}\"]') !== null",
            timeout=15.0,
        )
        assert not page.evaluate(
            f"document.querySelector('[data-project-id=\"{parent_target_id}\"]')?.textContent.includes('stub')"
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_dos_disk_icon_library_target(monkeypatch: pytest.MonkeyPatch) -> None:
    _skip_without_c_backend()
    disk_project_id = "amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5"
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(
        disasm_server,
        "mark_project_opened",
        lambda project_name: project_store.get_project(project_name),
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{disk_project_id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelector('.disk-state-summary') !== null")
        page.wait_for_expression(
            "Array.from(document.querySelectorAll('.disk-target-button')).every((button) => "
            "!button.textContent.includes('libs/icon.library'))"
        )
        assert "Startup import state" in page.text_content(".disk-section")
        page.assert_no_errors()
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_non_dos_disk_bootblock_and_bootloader_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _skip_without_c_backend()
    disk_project_id = "amiga_disk_ice-1991-06-28-the-silents"
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(
        disasm_server,
        "mark_project_opened",
        lambda project_name: project_store.get_project(project_name),
    )

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{disk_project_id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector(".disk-view", timeout=10.0)
        page.wait_for_expression("document.body.textContent.includes('Boot Block')")
        page.wait_for_expression("document.body.textContent.includes('bootloader/stage_1')")
        page.evaluate(
            """
            Array.from(document.querySelectorAll('.disk-target-button'))
              .find((button) => button.textContent.includes('Boot Block'))
              .click()
            """
        )
        page.wait_for_expression(
            "location.pathname.includes('amiga_raw_bootblock')",
            timeout=10.0,
        )
        page.wait_for_expression(
            "document.querySelectorAll('.listing-row-instruction').length > 0",
            timeout=45.0,
        )
        page.call("Page.navigate", {"url": f"{base_url}/{disk_project_id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression(
            "Array.from(document.querySelectorAll('.disk-target-button')).some((button) => button.textContent.includes('bootloader/stage_1'))"
        )
        page.evaluate(
            """
            Array.from(document.querySelectorAll('.disk-target-button'))
              .find((button) => button.textContent.includes('bootloader/stage_1'))
              .click()
            """
        )
        page.wait_for_expression(
            "location.pathname.includes('amiga_raw_bootloader_stage_1')",
            timeout=10.0,
        )
        page.wait_for_expression(
            "document.querySelectorAll('.listing-row-instruction').length > 0",
            timeout=45.0,
        )
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_api_edit_modal_applies_struct_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project = _binary_project("amiga_hunk_demo")
    initial_rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
    ]
    updated_rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
    ]
    disasm_server._ASYNC_JOBS.clear()
    _cache_full_project_rows(
        project.id,
        initial_rows,
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
    )
    corrections_path = tmp_path / "amiga_ndk_corrections.json"
    corrections_path.write_text(
        json.dumps(
            {
                "_meta": {"api_input_type_overrides": []},
                "libraries": {},
                "structs": {},
                "constants": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(disasm_server, "_OS_CORRECTIONS_PATH", corrections_path)
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    monkeypatch.setattr(
        disasm_server,
        "type_catalog_from_c_backend",
        lambda project_name: [{"name": "SimpleSprite", "source": "graphics/sprite.i", "size": 12}],
    )
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
        },
    )

    def build_updated_artifact(project_name: str) -> tuple[int, dict[str, object], _FakeCListingArtifact]:
        artifact = _FakeCListingArtifact(
            updated_rows,
            project_name=project_name,
            api_calls_by_row_id={
                "r0": {
                    "library": "intuition.library",
                    "function": "SetPointer",
                    "inputs": [
                        {
                            "name": "pointer",
                            "regs": ["A1"],
                            "type": "struct SimpleSprite *",
                            "i_struct": "SimpleSprite",
                            "source": "global correction",
                        }
                    ],
                }
            },
        )
        return len(updated_rows), {}, artifact

    monkeypatch.setattr(disasm_server, "build_project_listing_artifact_profile", build_updated_artifact)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_app_event(
            "amiga:project-rendered",
            f"detail.projectId === {json.dumps(project.id)}",
            timeout=10.0,
        )
        page.wait_for_selector("[data-api-edit='1']")
        page.wait_for_app_event_after_js(
            "amiga:api-edit-dialog-opened",
            "document.querySelector('[data-api-edit=\"1\"]').click()",
            "detail.function === 'SetPointer'",
            timeout=10.0,
        )
        page.wait_for_selector(".api-edit-input", timeout=20.0)
        page.fill(".api-edit-input", "SimpleSprite")
        page.click(".api-edit-apply")

        page.wait_for_expression(
            "document.querySelector('.project-badge-source-global-correction') !== null",
            timeout=15.0,
        )
        persisted = cast(dict[str, object], json.loads(corrections_path.read_text(encoding="utf-8")))
        overrides = cast(dict[str, object], persisted["_meta"])["api_input_type_overrides"]
        assert cast(list[dict[str, object]], overrides)[0]["i_struct"] == "SimpleSprite"
        page.assert_no_errors()


