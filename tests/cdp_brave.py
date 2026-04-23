from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import socket
import struct
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Self, cast
from urllib.request import Request, urlopen

import pytest

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_CDP_TEST_FILE = "test_web_e2e_cdp.py"
_CDP_TEST_MODULE = "tests.test_web_e2e_cdp"

type AllowedHttpFailure = tuple[str, int]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return cast(int, sock.getsockname()[1])


def _brave_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.environ.get("BRAVE_PATH")
    if env_path:
        candidates.append(Path(env_path))
    for base_name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(base_name)
        if base:
            candidates.append(
                Path(base)
                / "BraveSoftware"
                / "Brave-Browser"
                / "Application"
                / "brave.exe"
            )
    return candidates


def find_brave() -> Path:
    for candidate in _brave_candidates():
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Brave executable not found; set BRAVE_PATH")


def brave_cdp_skip_reason() -> str:
    return (
        "set M68K_RUN_BRAVE_CDP=1 to run Brave/CDP web E2E tests as part of a wider suite, "
        "or select tests/test_web_e2e_cdp.py directly"
    )


def brave_cdp_requested() -> bool:
    if os.environ.get("M68K_RUN_BRAVE_CDP") == "1":
        return True
    for arg in sys.argv[1:]:
        if arg.startswith("-"):
            continue
        normalized = arg.replace("\\", "/")
        if normalized.endswith(_CDP_TEST_FILE) or f"{_CDP_TEST_FILE}::" in normalized:
            return True
        if normalized == _CDP_TEST_MODULE or normalized.startswith(f"{_CDP_TEST_MODULE}::"):
            return True
    return False


def _http_failure_allowed(url: str, status: int, allowed: list[AllowedHttpFailure]) -> bool:
    return any(pattern in url and allowed_status == status for pattern, allowed_status in allowed)


def _virtual_key_code(key: str) -> int:
    codes = {
        "ArrowDown": 40,
        "ArrowLeft": 37,
        "ArrowRight": 39,
        "ArrowUp": 38,
        "End": 35,
        "Enter": 13,
        "Escape": 27,
        "Home": 36,
        "PageDown": 34,
        "PageUp": 33,
    }
    if len(key) == 1:
        return ord(key.upper())
    return codes.get(key, 0)


class CdpWebSocket:
    def __init__(self, url: str) -> None:
        self._sock = self._connect(url)
        self._next_id = 1
        self.events: list[dict[str, Any]] = []

    @classmethod
    def connect(cls, url: str) -> Self:
        return cls(url)

    def close(self) -> None:
        self._sock.close()

    def call(
        self, method: str, params: dict[str, Any] | None = None, *, timeout: float = 5.0
    ) -> dict[str, Any]:
        command_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {"id": command_id, "method": method}
        if params is not None:
            payload["params"] = params
        self._send_text(json.dumps(payload, separators=(",", ":")))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            message = self._recv_json(deadline - time.monotonic())
            if message.get("id") == command_id:
                if "error" in message:
                    raise AssertionError(f"CDP {method} failed: {message['error']}")
                return cast(dict[str, Any], message.get("result", {}))
            self.events.append(message)
        raise TimeoutError(f"Timed out waiting for CDP response: {method}")

    def wait_for_event(self, method: str, *, timeout: float = 5.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for index, event in enumerate(self.events):
                if event.get("method") == method:
                    return self.events.pop(index)
            self.events.append(self._recv_json(deadline - time.monotonic()))
        raise TimeoutError(f"Timed out waiting for CDP event: {method}")

    def drain_events(self, *, timeout: float = 0.15) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                self.events.append(self._recv_json(deadline - time.monotonic()))
            except TimeoutError:
                return

    def evaluate(self, expression: str, *, timeout: float = 5.0) -> Any:
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
            },
            timeout=timeout,
        )
        value = cast(dict[str, Any], result.get("result", {}))
        if "exceptionDetails" in result:
            raise AssertionError(f"JavaScript evaluation failed: {result['exceptionDetails']}")
        return value.get("value")

    def wait_for_selector(
        self,
        selector: str,
        *,
        timeout: float = 5.0,
        fail_on_ui_error: bool = True,
    ) -> None:
        quoted = json.dumps(selector)
        self.wait_for_expression(
            f"document.querySelector({quoted}) !== null",
            timeout=timeout,
            fail_on_ui_error=fail_on_ui_error,
        )

    def wait_for_expression(
        self,
        expression: str,
        *,
        timeout: float = 5.0,
        interval: float = 0.05,
        fail_on_ui_error: bool = True,
    ) -> Any:
        deadline = time.monotonic() + timeout
        last_value: Any = None
        while time.monotonic() < deadline:
            last_value = self.evaluate(expression, timeout=timeout)
            if last_value:
                return last_value
            if fail_on_ui_error:
                ui_error = self.ui_error_text()
                if ui_error:
                    artifacts = self.capture_failure_artifacts()
                    raise AssertionError(
                        f"UI error while waiting for expression: {ui_error}\n"
                        f"Expression: {expression}\n"
                        f"HTML: {artifacts['html']}\n"
                        f"Screenshot: {artifacts['screenshot']}"
                    )
            time.sleep(interval)
        raise TimeoutError(f"Timed out waiting for expression: {expression}; last={last_value!r}")

    def ui_error_text(self) -> str:
        value = self.evaluate(
            """
            (() => {
              const selectors = [
                ".progress-panel-error .error",
                ".page > .error",
                "#home-error"
              ];
              for (const selector of selectors) {
                const node = document.querySelector(selector);
                const text = node && node.textContent ? node.textContent.trim() : "";
                if (text) return text;
              }
              return "";
            })()
            """,
            timeout=2.0,
        )
        return value if isinstance(value, str) else ""

    def text_content(self, selector: str) -> str:
        quoted = json.dumps(selector)
        value = self.evaluate(
            f"""
            (() => {{
              const node = document.querySelector({quoted});
              if (!node) throw new Error(`Missing selector: ${{{quoted}}}`);
              return node.textContent || "";
            }})()
            """
        )
        assert isinstance(value, str)
        return value

    def click(self, selector: str) -> None:
        quoted = json.dumps(selector)
        self.evaluate(
            f"""
            (() => {{
              const node = document.querySelector({quoted});
              if (!node) throw new Error(`Missing selector: ${{{quoted}}}`);
              node.click();
              return true;
            }})()
            """
        )

    def click_until_selector(
        self,
        click_selector: str,
        target_selector: str,
        *,
        timeout: float = 5.0,
        interval: float = 0.1,
    ) -> None:
        quoted_click = json.dumps(click_selector)
        quoted_target = json.dumps(target_selector)
        self.wait_for_expression(
            f"""
            (() => {{
              if (document.querySelector({quoted_target})) return true;
              const node = document.querySelector({quoted_click});
              if (!node) return false;
              node.click();
              return document.querySelector({quoted_target}) !== null;
            }})()
            """,
            timeout=timeout,
            interval=interval,
        )

    def fill(self, selector: str, value: str) -> None:
        quoted_selector = json.dumps(selector)
        quoted_value = json.dumps(value)
        self.evaluate(
            f"""
            (() => {{
              const node = document.querySelector({quoted_selector});
              if (!node) throw new Error(`Missing selector: ${{{quoted_selector}}}`);
              node.value = {quoted_value};
              node.dispatchEvent(new Event("input", {{bubbles: true}}));
              node.dispatchEvent(new Event("change", {{bubbles: true}}));
              return true;
            }})()
            """
        )

    def select_value(self, selector: str, value: str) -> None:
        self.fill(selector, value)

    def set_file_input_files(self, selector: str, files: list[Path]) -> None:
        quoted_selector = json.dumps(selector)
        document = self.call("DOM.getDocument", {"depth": 1})
        root = cast(dict[str, Any], document["root"])
        query = self.call(
            "DOM.querySelector",
            {"nodeId": root["nodeId"], "selector": selector},
        )
        node_id = query.get("nodeId")
        if not isinstance(node_id, int) or node_id == 0:
            raise AssertionError(f"Missing selector: {quoted_selector}")
        self.call(
            "DOM.setFileInputFiles",
            {
                "nodeId": node_id,
                "files": [str(path.resolve()) for path in files],
            },
        )

    def press_key(self, key: str) -> None:
        key_code = _virtual_key_code(key)
        params = {
            "key": key,
            "code": key,
            "windowsVirtualKeyCode": key_code,
            "nativeVirtualKeyCode": key_code,
        }
        self.call("Input.dispatchKeyEvent", {"type": "keyDown", **params})
        self.call("Input.dispatchKeyEvent", {"type": "keyUp", **params})

    def handle_dialog(self, *, accept: bool) -> None:
        self.call("Page.handleJavaScriptDialog", {"accept": accept})

    def assert_no_errors(
        self,
        *,
        allowed_http_failures: list[AllowedHttpFailure] | None = None,
    ) -> None:
        self.drain_events()
        failures: list[str] = []
        allowed = allowed_http_failures or []
        for event in self.events:
            method = event.get("method")
            params = cast(dict[str, Any], event.get("params", {}))
            if method == "Runtime.exceptionThrown":
                failures.append(json.dumps(params.get("exceptionDetails", params), sort_keys=True))
            if method == "Log.entryAdded":
                entry = cast(dict[str, Any], params.get("entry", {}))
                if entry.get("level") in {"error", "warning"}:
                    failures.append(str(entry.get("text", entry)))
            if method == "Network.loadingFailed" and params.get("errorText") != "net::ERR_CACHE_MISS":
                if (
                    params.get("type") in {"EventSource", "Fetch"}
                    and params.get("errorText") == "net::ERR_ABORTED"
                    and params.get("canceled") is True
                ):
                    continue
                failures.append(json.dumps(params, sort_keys=True))
            if method == "Network.responseReceived":
                response = cast(dict[str, Any], params.get("response", {}))
                status = response.get("status")
                url = str(response.get("url", ""))
                if isinstance(status, int) and status >= 400 and not _http_failure_allowed(url, status, allowed):
                    failures.append(f"HTTP {status}: {url}")
        if failures:
            artifacts = self.capture_failure_artifacts()
            raise AssertionError(
                "Browser errors:\n"
                + "\n".join(failures)
                + f"\nHTML: {artifacts['html']}\nScreenshot: {artifacts['screenshot']}"
            )

    def capture_failure_artifacts(self) -> dict[str, Path]:
        artifact_dir = Path(tempfile.mkdtemp(prefix="amiga-reversing-cdp-failure-"))
        html_path = artifact_dir / "page.html"
        screenshot_path = artifact_dir / "page.png"
        html = self.evaluate("document.documentElement.outerHTML", timeout=2.0)
        html_path.write_text(str(html), encoding="utf-8")
        screenshot = self.call("Page.captureScreenshot", {"format": "png"}, timeout=5.0)
        data = screenshot.get("data")
        if isinstance(data, str):
            screenshot_path.write_bytes(base64.b64decode(data))
        else:
            screenshot_path.write_bytes(b"")
        return {"html": html_path, "screenshot": screenshot_path}

    @staticmethod
    def _connect(url: str) -> socket.socket:
        if not url.startswith("ws://"):
            raise ValueError(f"Unsupported WebSocket URL: {url}")
        host_path = url.removeprefix("ws://")
        host_port, path = host_path.split("/", 1)
        host, port_text = host_port.rsplit(":", 1)
        sock = socket.create_connection((host, int(port_text)), timeout=5.0)
        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        request = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        sock.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            response += sock.recv(4096)
        header_text = response.decode("iso-8859-1")
        accept = base64.b64encode(hashlib.sha1((key + _WS_GUID).encode("ascii")).digest()).decode(
            "ascii"
        )
        if " 101 " not in header_text or f"Sec-WebSocket-Accept: {accept}" not in header_text:
            raise ConnectionError(f"WebSocket handshake failed: {header_text}")
        return sock

    def _send_text(self, text: str) -> None:
        payload = text.encode("utf-8")
        header = bytearray([0x81])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length <= 0xFFFF:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        mask = secrets.token_bytes(4)
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self._sock.sendall(bytes(header) + masked)

    def _recv_json(self, timeout: float) -> dict[str, Any]:
        self._sock.settimeout(max(timeout, 0.001))
        while True:
            opcode, payload = self._recv_frame()
            if opcode == 0x1:
                return cast(dict[str, Any], json.loads(payload.decode("utf-8")))
            if opcode == 0x8:
                raise ConnectionError("WebSocket closed")
            if opcode == 0x9:
                self._send_pong(payload)

    def _recv_frame(self) -> tuple[int, bytes]:
        first = self._recv_exact(2)
        opcode = first[0] & 0x0F
        length = first[1] & 0x7F
        masked = bool(first[1] & 0x80)
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if masked else b""
        payload = self._recv_exact(length)
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return opcode, payload

    def _recv_exact(self, length: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self._sock.recv(length - len(chunks))
            if not chunk:
                raise ConnectionError("WebSocket connection closed")
            chunks.extend(chunk)
        return bytes(chunks)

    def _send_pong(self, payload: bytes) -> None:
        header = bytearray([0x8A, 0x80 | len(payload)])
        mask = secrets.token_bytes(4)
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self._sock.sendall(bytes(header) + masked)


@contextmanager
def brave_page() -> Iterator[CdpWebSocket]:
    if not brave_cdp_requested():
        pytest.skip(brave_cdp_skip_reason())
    brave = find_brave()
    port = _free_port()
    with tempfile.TemporaryDirectory(prefix="amiga-reversing-brave-", ignore_cleanup_errors=True) as profile_dir:
        process = subprocess.Popen(
            [
                str(brave),
                f"--remote-debugging-port={port}",
                f"--user-data-dir={profile_dir}",
                "--no-first-run",
                "--disable-default-apps",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-extensions",
                "about:blank",
            ]
        )
        try:
            target = _new_target(port)
            ws = CdpWebSocket.connect(str(target["webSocketDebuggerUrl"]))
            try:
                ws.call("Runtime.enable")
                ws.call("Page.enable")
                ws.call("Log.enable")
                ws.call("Network.enable")
                ws.call("DOM.enable")
                yield ws
            finally:
                ws.close()
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _new_target(port: int) -> dict[str, Any]:
    deadline = time.monotonic() + 10.0
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            request = Request(f"http://127.0.0.1:{port}/json/new?about:blank", method="PUT")
            with urlopen(request, timeout=1.0) as response:
                return cast(dict[str, Any], json.load(response))
        except Exception as exc:  # pragma: no cover - depends on browser startup timing
            last_error = exc
            time.sleep(0.05)
    raise TimeoutError(f"Timed out waiting for Brave CDP endpoint: {last_error}")
