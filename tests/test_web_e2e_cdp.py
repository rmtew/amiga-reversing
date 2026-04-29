from __future__ import annotations

import json
import shutil
import socket
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import cast

import pytest

from amiga_reversing.disasm import projects as project_store
from amiga_reversing.disasm import server as disasm_server
from amiga_reversing.disasm.c_backend import build_project_rows_with_c_backend
from amiga_reversing.disasm.listing_types import (
    AppSlotRef,
    BlockRowContext,
    ListingRow,
    SemanticOperand,
    SymbolOperandMetadata,
)
from amiga_reversing.disasm.projects import ProjectRecord
from tests.cdp_brave import brave_cdp_requested, brave_cdp_skip_reason, brave_page

PROJECT_ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(not brave_cdp_requested(), reason=brave_cdp_skip_reason())


def _binary_project(project_name: str) -> ProjectRecord:
    return ProjectRecord(
        id=project_name,
        name=project_name,
        kind="binary",
        target_dir=f"targets/{project_name}",
        entities_path=f"targets/{project_name}/entities.jsonl",
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
def _clear_disasm_server_listing_state() -> Iterator[None]:
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._JOB_EVENT_SUBSCRIBERS.clear()
    yield
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
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
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
    disasm_server._PROJECT_ROW_GENERATION_CACHE[project.id] = "full"
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
            analysis_generation="basic",
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
                analysis_generation="basic",
            )
        )
    rows.append(
        ListingRow(
            row_id="r899",
            kind="label",
            text="far_target:\n",
            addr=1798,
            label="far_target:",
            analysis_generation="basic",
        )
    )
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
    disasm_server._PROJECT_ROW_GENERATION_CACHE[project.id] = "basic"
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
            analysis_generation="basic",
        )
        for index in range(1000)
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
    disasm_server._PROJECT_ROW_GENERATION_CACHE[project.id] = "basic"
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
              for (let index = 0; index < 4; index += 1) {
                scrollListingViewport(state.project, "down");
              }
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
def test_brave_cdp_stats_overlay_shows_fetch_latency(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_stats")
    rows = [
        ListingRow(
            row_id=f"r{index}",
            kind="instruction",
            text="rts\n",
            addr=index * 2,
            opcode_or_directive="rts",
            analysis_generation="basic",
        )
        for index in range(400)
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
    disasm_server._PROJECT_ROW_GENERATION_CACHE[project.id] = "basic"
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

    basic_rows = make_rows("basic", "far_basic")
    full_rows = [
        ListingRow(row_id="full-comment", kind="comment", text="; full header\n", analysis_generation="full"),
        ListingRow(row_id="full-equ", kind="directive", text="app_SIZEOF EQU __RS\n", analysis_generation="full"),
        ListingRow(row_id="full-include", kind="directive", text='INCLUDE "exec/exec_lib.i"\n', analysis_generation="full"),
        ListingRow(row_id="full-section", kind="directive", text="    SECTION section,code\n", analysis_generation="full"),
        *make_rows("full", "far_full"),
    ]
    full_started = threading.Event()
    release_full = threading.Event()

    def build_rows(
        project_name: str, generation: str
    ) -> tuple[list[ListingRow], dict[tuple[int, int], dict[str, object]]]:
        if generation == "full":
            full_started.set()
            assert release_full.wait(timeout=15.0)
            return full_rows, {}
        return basic_rows, {}

    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "stable-cache")
    monkeypatch.setattr(disasm_server, "build_project_rows_generation_with_c_backend", build_rows)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression(
            "document.querySelector('.listing-row')?.dataset.analysisGeneration === 'basic'",
            timeout=10.0,
        )
        page.wait_for_app_event_after_js(
            "amiga:listing-window-rendered",
            """
            (() => {
              scrollListingViewport(state.project, "end");
              return true;
            })()
            """,
            "detail.start > 0 && detail.generation === 'basic'",
            timeout=10.0,
        )
        assert page.evaluate("document.body.textContent.includes('far_basic:')")
        before_scroll = page.evaluate("document.querySelector('#listing-viewport').scrollTop")
        assert full_started.wait(timeout=10.0)
        release_full.set()
        page.wait_for_expression(
            "document.body.textContent.includes('far_full:') && document.querySelector('.listing-row')?.dataset.analysisGeneration === 'full'",
            timeout=15.0,
        )
        assert not page.evaluate("document.body.textContent.includes('far_basic:')")
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
    basic_rows = [
        ListingRow(
            row_id="basic-section",
            kind="directive",
            text="    SECTION section,code\n",
            analysis_generation="basic",
        ),
        ListingRow(
            row_id="basic-data",
            kind="data",
            text='DC.B $60,$34\n',
            addr=0,
            opcode_or_directive="DC.B",
            operand_text="$60,$34",
            analysis_generation="basic",
        ),
    ]
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

    def build_rows(
        project_name: str, generation: str
    ) -> tuple[list[ListingRow], dict[tuple[int, int], dict[str, object]]]:
        if generation == "full":
            full_started.set()
            assert release_full.wait(timeout=15.0)
            return full_rows, {}
        return basic_rows, {}

    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda project_name: "stable-cache")
    monkeypatch.setattr(disasm_server, "build_project_rows_generation_with_c_backend", build_rows)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression(
            "document.querySelector('.listing-row')?.dataset.rowCode.trim() === 'SECTION section,code'",
            timeout=10.0,
        )
        before_top_code = page.evaluate(
            "document.querySelector('.listing-row')?.dataset.rowCode.trim()"
        )
        assert before_top_code == "SECTION section,code"
        assert page.evaluate(
            "document.querySelector('.listing-row-data .listing-code')?.textContent === '    DC.B $60,$34'"
        )
        assert full_started.wait(timeout=10.0)
        release_full.set()
        page.wait_for_expression(
            "document.querySelector('.listing-row')?.dataset.analysisGeneration === 'full'",
            timeout=15.0,
        )
        assert page.evaluate(
            "document.querySelector('.listing-row')?.dataset.rowCode.trim()"
        ) == "SECTION section,code"
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
    disasm_server._PROJECT_API_CALL_CACHE[project.id] = {
        (1, 0x10): {
            "library": "intuition.library",
            "function": "SetPointer",
            "note_kind": 0,
            "call_kind": 1,
            "inputs": [],
        }
    }
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
    ]
    for index in range(8, 180):
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

    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
    disasm_server._PROJECT_ROW_GENERATION_CACHE[project.id] = "full"
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
            "document.querySelectorAll('.listing-symbol-reference[data-symbol-name=\"target\"]').length === 3"
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
            "document.querySelectorAll('.listing-symbol-reference[data-symbol-name=\"target\"]').length === 3"
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
        page.wait_for_expression("document.querySelector('.navigation-summary')?.textContent === 'target: 4 refs'")
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
        page.wait_for_expression("document.querySelector('.navigation-summary')?.textContent === 'target: 4 refs'")
        assert page.evaluate(
            "document.querySelector('.navigation-item.active')?.textContent.includes('jsr target.l')"
        )
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
            bytes=b"\x4e\x75",
            opcode_or_directive="rts",
        ),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
    disasm_server._PROJECT_ROW_GENERATION_CACHE[project.id] = "full"
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
        assert page.evaluate("document.querySelector('.listing-row-instruction .listing-bytes')?.textContent === '4e75'")
        assert page.evaluate("document.querySelector('.listing-row-data .listing-bytes')?.textContent === '1234'")
        assert page.evaluate("document.querySelectorAll('.listing-column-resizer').length >= 3")
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
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
def test_brave_cdp_project_delete_confirms_and_removes_project(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_demo")
    projects = [project]
    removed_projects: list[str] = []
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
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
            "document.querySelectorAll('.listing-row-instruction').length > 0",
            timeout=45.0,
        )
        assert page.text_content("#project-title") == project_id
        assert page.evaluate("document.querySelectorAll('.listing-row-label').length > 0")
        assert page.evaluate("document.querySelectorAll('.listing-row-instruction').length > 0")
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[expected_project_id] = [
        ListingRow(row_id="r0", kind="label", text="uploaded_start:\n", addr=0),
        ListingRow(row_id="r1", kind="instruction", text="rts\n", addr=0),
    ]
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
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
        assert "Targets" in page.text_content(".disk-section")
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
def test_brave_cdp_dos_disk_icon_library_target(monkeypatch: pytest.MonkeyPatch) -> None:
    _skip_without_c_backend()
    disk_project_id = "amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5"
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
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
            """
            Array.from(document.querySelectorAll('.disk-target-button'))
              .some((button) => button.textContent.includes('libs/icon.library')
                && button.textContent.includes('library')
                && button.textContent.includes('LVOs'))
            """
        )
        page.evaluate(
            """
            Array.from(document.querySelectorAll('.disk-target-button'))
              .find((button) => button.textContent.includes('libs/icon.library'))
              .click()
            """
        )
        page.wait_for_expression(
            "location.pathname.includes('amiga_hunk_libs__icon.library')",
            timeout=10.0,
        )
        page.wait_for_expression(
            "document.querySelectorAll('.listing-row-instruction').length > 0",
            timeout=45.0,
        )
        assert "amiga_hunk_libs__icon.library" in page.text_content("#project-title")
        assert "library" in page.text_content("#project-details")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_non_dos_disk_bootblock_and_bootloader_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _skip_without_c_backend()
    disk_project_id = "amiga_disk_ice-1991-06-28-the-silents"
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
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
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = initial_rows
    disasm_server._PROJECT_API_CALL_CACHE[project.id] = {
        (0, 0x10): {
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
    }
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

    def build_updated_rows(
        project_name: str, generation: str = "full"
    ) -> tuple[list[ListingRow], dict[tuple[int, int], dict[str, object]]]:
        if generation == "basic":
            return updated_rows, {}
        return updated_rows, {
            (0, 0x10): {
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
        }

    monkeypatch.setattr(disasm_server, "build_project_rows_generation_with_c_backend", build_updated_rows)

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


@pytest.mark.web_e2e
def test_brave_cdp_annotation_edit_modal_patches_entity(monkeypatch: pytest.MonkeyPatch) -> None:
    project = _binary_project("amiga_hunk_demo")
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="loc_0010:\n",
            addr=0x10,
            entity_addr=0x10,
        ),
        ListingRow(row_id="r1", kind="instruction", text="rts\n", addr=0x10),
    ]
    entity: dict[str, object] = {
        "addr": "0010",
        "type": "code",
        "name": "loc_0010",
        "comment": "",
        "confidence": "tool-inferred",
    }
    patches: list[dict[str, object]] = []
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project.id] = rows
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [project])
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "mark_project_opened", lambda project_name: project)
    monkeypatch.setattr(disasm_server, "get_entity", lambda project_name, addr, project_root=None: dict(entity))
    monkeypatch.setattr(
        disasm_server,
        "get_entities_by_int_addr",
        lambda project_name, project_root=None: {0x10: dict(entity)},
    )

    def patch_entity(
        project_name: str,
        addr: str,
        patch: dict[str, object],
        project_root: Path | None = None,
    ) -> dict[str, object]:
        patches.append(dict(patch))
        entity.update({key: value for key, value in patch.items() if value is not None})
        return dict(entity)

    monkeypatch.setattr(disasm_server, "patch_entity", patch_entity)

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_app_event(
            "amiga:project-rendered",
            f"detail.projectId === {json.dumps(project.id)}",
            timeout=10.0,
        )
        page.wait_for_selector("[data-annotation-edit='1']")
        page.wait_for_app_event_after_js(
            "amiga:annotation-edit-dialog-opened",
            "document.querySelector('[data-annotation-edit=\"1\"]').click()",
            "detail.addr === 16",
            timeout=10.0,
        )
        page.fill(".annotation-edit-name", "main_entry")
        page.fill(".annotation-edit-comment", "validated entry")
        page.select_value(".annotation-edit-confidence", "verified")
        page.click(".annotation-edit-apply")

        page.wait_for_expression(
            "Array.from(document.querySelectorAll('.project-badge')).some((badge) => badge.textContent === 'main_entry')",
            timeout=15.0,
        )
        assert patches[-1]["name"] == "main_entry"
        assert patches[-1]["comment"] == "validated entry"
        assert patches[-1]["confidence"] == "verified"
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_real_annotation_edit_round_trip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _skip_without_c_backend()
    project_root = tmp_path / "project_root"
    project_id = "amiga_hunk_genam"
    rows, api_calls = build_project_rows_with_c_backend(project_id, project_root=PROJECT_ROOT)
    shutil.copytree(PROJECT_ROOT / "targets" / project_id, project_root / "targets" / project_id)
    for stale in (project_root / "targets" / project_id).glob("overrides.json*"):
        stale.unlink()
    _temp_project_accessors(monkeypatch, project_root)
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_GENERATION_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE_KEY.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project_id] = rows
    disasm_server._PROJECT_ROW_GENERATION_CACHE[project_id] = "full"
    disasm_server._PROJECT_API_CALL_CACHE[project_id] = api_calls

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project_id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_app_event(
            "amiga:project-rendered",
            f"detail.projectId === {json.dumps(project_id)}",
            timeout=45.0,
        )
        page.wait_for_selector("[data-annotation-edit='1']", timeout=45.0)
        page.wait_for_app_event_after_js(
            "amiga:annotation-edit-dialog-opened",
            "document.querySelector('[data-row-addr=\"0\"] [data-annotation-edit=\"1\"]').click()",
            "detail.addr === 0",
            timeout=10.0,
        )
        page.evaluate(
            """
            (() => {
              document.querySelector(".annotation-edit-name").value = "cdp_entry";
              document.querySelector(".annotation-edit-comment").value = "real c-backed annotation";
              document.querySelector(".annotation-edit-confidence").value = "verified";
              document.querySelector(".annotation-edit-apply").click();
              return true;
            })()
            """
        )
        page.wait_for_expression(
            "Array.from(document.querySelectorAll('.project-badge')).some((badge) => badge.textContent === 'cdp_entry')",
            timeout=15.0,
        )
        page.assert_no_errors()

    overrides = json.loads((project_root / "targets" / project_id / "overrides.json").read_text(encoding="utf-8"))
    assert overrides["entities"]["0x0000"]["name"] == "cdp_entry"
    assert overrides["entities"]["0x0000"]["comment"] == "real c-backed annotation"
    assert overrides["entities"]["0x0000"]["confidence"] == "verified"
