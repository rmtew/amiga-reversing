"""Transport contracts: CLI and real MCP stdio share the HTTP operation client."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from amiga_reversing.disasm.restoration_client import (
    RestorationClient,
    RestorationClientError,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def operation_server():
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.reply({"web_app_contract_version": 2})

        def do_POST(self):
            assert self.headers["X-Amiga-Web-App-Contract"] == "2"
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            if body.get("expected_revision") == "old":
                self.reply({"error": "stale_revision"}, 409)
            else:
                self.reply({"revision": "current", "request": body, "items": []})

        def reply(self, data, status=200):
            payload = (
                {"ok": status == 200, "data": data}
                if status == 200
                else {"ok": False, **data}
            )
            raw = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_cli_http_equivalence_and_stale_refusal(operation_server):
    url, requests = operation_server
    expected = RestorationClient(url).call(
        "demo",
        "query",
        kind="references",
        symbol="label",
        expected_revision="current",
        limit=2,
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "amiga_reversing.tools.restoration",
            "--server",
            url,
            "--target",
            "demo",
            "query",
            "--kind",
            "references",
            "--symbol",
            "label",
            "--expected-revision",
            "current",
            "--limit",
            "2",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == expected
    with pytest.raises(RestorationClientError, match="stale_revision"):
        RestorationClient(url).call("demo", "interpret", expected_revision="old")
    assert requests[-1]["expected_revision"] == "old"


def test_cli_batch_forwards_one_revision_and_entries(operation_server):
    url, requests = operation_server
    parameters = {"expected_revision": "current", "entries": [{
        "command_id": "comment.edit", "context": {"kind": "row"},
        "parameters": {"text": "Supported caller evidence."},
        "evidence": {"reason": "Native caller", "evidence_refs": ["s0:00000000:instruction"]},
    }]}
    result = subprocess.run([
        sys.executable, "-m", "amiga_reversing.tools.restoration", "--server", url,
        "--target", "demo", "interpret_batch", "--request", "-",
    ], input=json.dumps(parameters), cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert requests[-1] == {"operation": "interpret_batch", **parameters}


def test_cli_review_batch_forwards_ids_and_shared_proof(operation_server):
    url, requests = operation_server
    parameters = {"expected_revision": "current", "action_ids": ["action-1", "action-2"],
                  "decision": "accept", "reason": "Inspected consumers and exact source", "verification_id": "proof"}
    result = subprocess.run([
        sys.executable, "-m", "amiga_reversing.tools.restoration", "--server", url,
        "--target", "demo", "review_batch", "--request", "-",
    ], input=json.dumps(parameters), cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert requests[-1] == {"operation": "review_batch", **parameters}


def test_mcp_stdio_initialize_list_and_operation_parity(operation_server):
    pytest.importorskip("mcp")
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    url, requests = operation_server

    async def exercise():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "amiga_reversing.tools.restoration_mcp", "--server", url],
            cwd=str(ROOT),
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            initialized = await session.initialize()
            assert initialized.server_info.name == "Amiga source restoration"
            tools = (await session.list_tools()).tools
            assert len(tools) == 12
            by_name = {tool.name: tool for tool in tools}
            assert by_name["restoration_query"].annotations.read_only_hint
            assert not by_name["restoration_interpret"].annotations.read_only_hint
            assert (
                "expected_revision"
                in by_name["restoration_interpret"].input_schema["required"]
            )
            result = await session.call_tool(
                "restoration_query",
                {
                    "project": "demo",
                    "kind": "references",
                    "expected_revision": "current",
                    "symbol": "label",
                    "limit": 2,
                },
            )
            expected = RestorationClient(url).call(
                "demo",
                "query",
                kind="references",
                expected_revision="current",
                symbol="label",
                limit=2,
            )
            assert not result.is_error
            assert result.structured_content == expected
            result = await session.call_tool(
                "restoration_interpret",
                {
                    "project": "demo",
                    "expected_revision": "current",
                    "command_id": "rename",
                    "context": {"kind": "row"},
                    "parameters": {"name": "label"},
                    "question": "What is this entry?",
                    "reason": "Native caller",
                    "source_evidence_status": "hypothesis",
                    "source_evidence_refs": ["row-key"],
                },
            )
            assert not result.is_error
            assert requests[-1]["operation"] == "interpret"
            assert requests[-1]["evidence"]["source_evidence_status"] == "hypothesis"
            entries = [{"command_id": "comment.edit", "context": {"kind": "row"},
                        "parameters": {"text": "Caller evidence."},
                        "evidence": {"reason": "Native caller", "evidence_refs": ["row-key"]}}]
            batch = await session.call_tool("restoration_interpret_batch", {
                "project": "demo", "expected_revision": "current", "entries": entries})
            assert not batch.is_error
            assert requests[-1] == {"operation": "interpret_batch", "expected_revision": "current", "entries": entries}
            assert not by_name["restoration_interpret_batch"].annotations.read_only_hint
            reviewed = await session.call_tool("restoration_review_batch", {
                "project": "demo", "expected_revision": "current", "action_ids": ["action-1", "action-2"],
                "decision": "accept", "reason": "Exact source and inspected consumers", "verification_id": "proof"})
            assert not reviewed.is_error
            assert requests[-1]["operation"] == "review_batch"
            assert requests[-1]["action_ids"] == ["action-1", "action-2"]
            assert not by_name["restoration_review_batch"].annotations.read_only_hint
            rejected = await session.call_tool(
                "restoration_verify", {"project": "demo", "expected_revision": "old"}
            )
            assert rejected.is_error
            assert "stale_revision" in rejected.content[0].text

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://example.com",
        "http://127.0.0.1/path",
        "http://user:pass@localhost",
    ],
)
def test_adapter_rejects_nonlocal_or_ambiguous_origin(url):
    with pytest.raises(ValueError, match="local|origin"):
        RestorationClient(url)
