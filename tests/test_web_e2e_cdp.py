from __future__ import annotations

import json
import shutil
import socket
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
from amiga_reversing.disasm.listing_types import BlockRowContext, ListingRow
from amiga_reversing.disasm.projects import ProjectRecord
from tests.cdp_brave import brave_page

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


@contextmanager
def _live_server() -> Iterator[str]:
    port = _free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), disasm_server.DisasmApiHandler)
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
        page.wait_for_expression("document.querySelectorAll('.listing-row').length > 0")
        assert page.evaluate("document.querySelectorAll('.listing-row').length < 600")
        assert page.evaluate("document.querySelector('.listing-scroll-spacer').offsetHeight > 10000")
        assert not page.evaluate("document.body.textContent.includes('far_target:')")

        page.evaluate(
            """
            (() => {
              const viewport = document.querySelector("#listing-viewport");
              viewport.scrollTop = viewport.scrollHeight;
              viewport.dispatchEvent(new Event("scroll"));
              return true;
            })()
            """
        )
        page.wait_for_expression("document.body.textContent.includes('far_target:')", timeout=10.0)
        assert page.evaluate("document.querySelectorAll('.listing-row').length < 600")

        page.evaluate("document.querySelector('#listing-viewport').scrollTop = 0")
        page.click("#open-navigation")
        page.wait_for_selector("#navigation-overlay")
        page.select_value("[data-navigation-class='1']", "labels")
        page.wait_for_expression(
            "Array.from(document.querySelectorAll('.navigation-item')).some((item) => item.textContent.includes('far_target'))"
        )
        page.evaluate(
            """
            Array.from(document.querySelectorAll('.navigation-item'))
              .find((item) => item.textContent.includes('far_target'))
              .click()
            """
        )
        page.wait_for_expression(
            "document.querySelector('[data-row-addr=\"1798\"]')?.classList.contains('listing-row-focus')",
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
        for _index in range(4):
            page.press_key("PageDown")
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
        page.wait_for_expression("document.querySelectorAll('.listing-row').length > 0")
        page.evaluate(
            """
            (() => {
              const viewport = document.querySelector("#listing-viewport");
              viewport.scrollTop = 1800;
              viewport.dispatchEvent(new Event("scroll"));
              return true;
            })()
            """
        )
        page.wait_for_expression(
            "Number(document.querySelector('.listing-row')?.dataset.rowAddr || 0) > 0",
            timeout=2.0,
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
    full_rows = make_rows("full", "far_full")
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
        page.evaluate(
            """
            (() => {
              const viewport = document.querySelector("#listing-viewport");
              viewport.scrollTop = viewport.scrollHeight;
              viewport.dispatchEvent(new Event("scroll"));
              return true;
            })()
            """
        )
        page.wait_for_expression("document.body.textContent.includes('far_basic:')", timeout=10.0)
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
        page.press_key("Enter")
        page.wait_for_expression("document.querySelector('#navigation-overlay') === null")
        page.assert_no_errors()


@pytest.mark.web_e2e
def test_brave_cdp_listing_symbol_links_are_focusable_and_jump(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _binary_project("amiga_hunk_symbol_links")
    rows: list[ListingRow] = [
        ListingRow(row_id="global-rs", kind="directive", text="app_ULONG RS.L 1\n"),
        ListingRow(row_id="r0", kind="label", text="start:\n", addr=0, label="start:"),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr target.l\n",
            addr=2,
            opcode_or_directive="jsr",
            operand_text="target.l",
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
    ]
    for index in range(4, 180):
        rows.append(
            ListingRow(
                row_id=f"r{index}",
                kind="instruction",
                text="rts\n",
                addr=index * 2,
                opcode_or_directive="rts",
            )
        )
    rows.append(ListingRow(row_id="target", kind="label", text="target:\n", addr=400, label="target:"))

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
        page.wait_for_selector(".listing-symbol-reference[data-symbol-name='target']")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"app_ULONG\"]')")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"RS\"]')")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"d0\"]')")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"a6\"]')")
        assert not page.evaluate("document.querySelector('[data-symbol-name=\"_LVOSetSignal\"]')")
        assert page.evaluate("document.querySelector('.listing-symbol-reference[data-symbol-name=\"target\"]')?.tabIndex === 0")
        page.evaluate("document.querySelector('.listing-symbol-reference[data-symbol-name=\"target\"]').focus()")
        assert page.evaluate("document.activeElement?.dataset.symbolName === 'target'")
        page.press_key("Enter")
        page.wait_for_expression(
            "document.querySelector('[data-row-addr=\"400\"]')?.classList.contains('listing-row-focus')",
            timeout=10.0,
        )
        assert page.evaluate("document.querySelector('#listing-viewport')?.textContent.includes('target:')")

        page.call("Page.navigate", {"url": f"{base_url}/{project.id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector(".listing-symbol-reference[data-symbol-name='target']")
        page.click(".listing-symbol-reference[data-symbol-name='target']")
        page.wait_for_expression(
            "document.querySelector('[data-row-addr=\"400\"]')?.classList.contains('listing-row-focus')",
            timeout=10.0,
        )
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
            row_id="code",
            kind="instruction",
            text="rts\n",
            addr=0,
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
        page.press_key("Escape")
        page.wait_for_expression("document.querySelector('#navigation-overlay') === null")

        page.click("#navigation-back")
        page.wait_for_expression(
            "document.querySelector('[data-row-addr=\"0\"]')?.classList.contains('listing-row-focus')"
        )
        page.click("#navigation-forward")
        page.wait_for_expression(
            "document.querySelector('[data-row-addr=\"8\"]')?.classList.contains('listing-row-focus')"
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
        page.wait_for_selector("[data-api-edit='1']")
        page.click("[data-api-edit='1']")
        page.wait_for_selector(".api-edit-dialog")
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
        page.wait_for_selector("[data-annotation-edit='1']")
        page.evaluate("new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve(true))))")
        page.click("[data-annotation-edit='1']")
        page.wait_for_selector(".annotation-edit-dialog")
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
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._PROJECT_ROW_CACHE[project_id] = rows
    disasm_server._PROJECT_API_CALL_CACHE[project_id] = api_calls

    with _live_server() as base_url, brave_page() as page:
        page.call("Page.navigate", {"url": f"{base_url}/{project_id}"})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_selector("[data-annotation-edit='1']", timeout=45.0)
        page.evaluate(
            """
            document.querySelector('[data-row-addr="0"] [data-annotation-edit="1"]')?.click()
            """
        )
        page.wait_for_selector(".annotation-edit-dialog")
        page.fill(".annotation-edit-name", "cdp_entry")
        page.fill(".annotation-edit-comment", "real c-backed annotation")
        page.select_value(".annotation-edit-confidence", "verified")
        page.click(".annotation-edit-apply")
        page.wait_for_expression(
            "Array.from(document.querySelectorAll('.project-badge')).some((badge) => badge.textContent === 'cdp_entry')",
            timeout=15.0,
        )
        page.assert_no_errors()

    overrides = json.loads((project_root / "targets" / project_id / "overrides.json").read_text(encoding="utf-8"))
    assert overrides["entities"]["0x0000"]["name"] == "cdp_entry"
    assert overrides["entities"]["0x0000"]["comment"] == "real c-backed annotation"
    assert overrides["entities"]["0x0000"]["confidence"] == "verified"
