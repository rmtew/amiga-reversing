"""Bounded, owned headless Copperline 1.0.0 control transport.

This internal layer deliberately knows nothing about target/source identities.
Memory writes invalidate reverse-history assumptions; callers must record that
boundary rather than treating replay across an injected write as evidence.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
import threading
import time
from collections import deque
from pathlib import Path


class CopperlineError(RuntimeError):
    """Protocol, process or emulator failure (never includes authentication data)."""


class CopperlineTimeout(CopperlineError):
    """The wall deadline expired; the machine was paused or disconnected."""


class CopperlineClient:
    MAX_LINE = 4 * 1024 * 1024

    def __init__(self, sock: socket.socket, *, request_timeout: float = 5):
        self.sock = sock
        self.request_timeout = request_timeout
        self._buffer = bytearray()
        self._counter = 0
        self.events = deque(maxlen=128)
        self.closed = False

    def close(self):
        if not self.closed:
            self.closed = True
            self.sock.close()

    def _send(self, method, params, deadline):
        if self.closed:
            raise CopperlineError("Control connection is closed")
        self._counter += 1
        data = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": self._counter,
                    "method": method,
                    "params": params or {},
                }
            ).encode()
            + b"\n"
        )
        if len(data) > self.MAX_LINE:
            raise CopperlineError("Control request exceeds line limit")
        self.sock.settimeout(max(0.001, deadline - time.monotonic()))
        self.sock.sendall(data)
        return self._counter

    def _receive(self, deadline):
        while b"\n" not in self._buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            self.sock.settimeout(remaining)
            chunk = self.sock.recv(65536)
            if not chunk:
                raise CopperlineError("Control connection disconnected")
            self._buffer.extend(chunk)
            if len(self._buffer.split(b"\n", 1)[0]) > self.MAX_LINE:
                raise CopperlineError("Control response exceeds line limit")
        line, _, rest = self._buffer.partition(b"\n")
        self._buffer = bytearray(rest)
        if len(line) > self.MAX_LINE:
            raise CopperlineError("Control response exceeds line limit")
        try:
            message = json.loads(line)
        except ValueError, UnicodeError:
            raise CopperlineError("Malformed control JSON") from None
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            raise CopperlineError("Malformed control response")
        return message

    def _responses(self, ids, deadline):
        results = {}
        notifications = 0
        while ids - results.keys():
            if time.monotonic() >= deadline:
                raise TimeoutError
            message = self._receive(deadline)
            if "id" not in message:
                if not isinstance(message.get("method"), str) or not message[
                    "method"
                ].startswith("event."):
                    raise CopperlineError("Malformed control notification")
                self.events.append(message)
                notifications += 1
                if notifications > 4096:
                    raise CopperlineError("Control notification budget exceeded")
                continue
            ident = message["id"]
            if type(ident) is not int or ident not in ids or ident in results:
                raise CopperlineError("Unexpected control response id")
            if ("result" in message) == ("error" in message):
                raise CopperlineError("Malformed control result")
            results[ident] = message
        return results

    @staticmethod
    def _result(message):
        if "error" in message:
            error = message["error"]
            code = error.get("code") if isinstance(error, dict) else None
            code = code if type(code) is int else None
            # Server strings can echo request parameters, including a token.
            raise CopperlineError(f"Copperline RPC error (code {code!r})")
        return message["result"]

    def request(self, method, params=None, *, timeout=None):
        deadline = time.monotonic() + (
            self.request_timeout if timeout is None else timeout
        )
        try:
            ident = self._send(method, params, deadline)
            return self._result(self._responses({ident}, deadline)[ident])
        except TimeoutError:
            self.close()
            raise CopperlineTimeout(
                "Control request timed out; connection closed"
            ) from None
        except (OSError, CopperlineError) as exc:
            self.close()
            if isinstance(exc, CopperlineError):
                raise
            raise CopperlineError("Control socket failed") from None

    def run_until(self, params, *, timeout):
        deadline = time.monotonic() + timeout
        try:
            ident = self._send("run_until", params, deadline)
            try:
                return self._result(self._responses({ident}, deadline)[ident])
            except TimeoutError:
                # A second connection cannot control a headless owned session.
                # Pause on the SAME stream and drain both replies before reuse.
                pause_deadline = time.monotonic() + self.request_timeout
                pause_id = self._send("pause", {}, pause_deadline)
                replies = self._responses({ident, pause_id}, pause_deadline)
                self._result(replies[ident])
                self._result(replies[pause_id])
                raise CopperlineTimeout(
                    "Run deadline expired; emulator paused"
                ) from None
        except CopperlineTimeout:
            raise
        except (OSError, CopperlineError) as exc:
            self.close()
            if isinstance(exc, TimeoutError):
                raise CopperlineTimeout(
                    "Pause deadline expired; connection closed"
                ) from None
            if isinstance(exc, CopperlineError):
                raise
            raise CopperlineError("Control socket failed") from None

    def read_memory(self, addr, length):
        if not 0 <= length <= 1024 * 1024:
            raise ValueError("Memory read must be at most 1 MiB")
        result = self.request(
            "mem.read", {"addr": addr, "len": length, "encoding": "hex"}
        )
        try:
            data = bytes.fromhex(result["data"])
            if len(data) != length:
                raise ValueError
            return data
        except KeyError, TypeError, ValueError:
            raise CopperlineError("Malformed memory result") from None

    def registers(self):
        raw = self.request("regs.get")
        try:
            result = {
                f"{kind}{i}": int(raw[kind][i]) for kind in ("d", "a") for i in range(8)
            }
            result.update(pc=int(raw["pc"]), sr=int(raw["sr"]))
            result["sp"] = result["a7"]
            return result
        except KeyError, TypeError, ValueError, IndexError:
            raise CopperlineError("Malformed registers result") from None

    def add_breakpoint(self, addr):
        return self.request("break.add", {"kind": "pc", "addr": addr})["id"]

    def remove_breakpoint(self, ident):
        return self.request("break.remove", {"id": ident})

    def joystick(self, *, port=2, **state):
        controls = {
            "up",
            "down",
            "left",
            "right",
            "red",
            "blue",
            "green",
            "yellow",
            "play",
            "rwd",
            "ffw",
        }
        if (
            port not in (1, 2, 3, 4)
            or state.keys() - controls
            or any(type(v) is not bool for v in state.values())
        ):
            raise ValueError("Invalid joystick full state")
        return self.request(
            "input.joy",
            {"port": port, **{key: state.get(key, False) for key in sorted(controls)}},
        )


class CopperlineProcess:
    """One owned process and isolated endpoint/config; close is repeatable."""

    def __init__(
        self,
        binary,
        *,
        rom=None,
        floppy=None,
        host_directory=None,
        startup_timeout=15,
        request_timeout=5,
    ):
        self.binary = str(Path(binary).resolve())
        self.rom, self.floppy, self.host_directory = rom, floppy, host_directory
        self.startup_timeout, self.request_timeout = startup_timeout, request_timeout
        self.process = self.client = self._temporary = self._reader = None
        self.log_tail = deque(maxlen=64)

    def __enter__(self):
        return self.start()

    def start(self):
        if self.process is not None:
            raise CopperlineError("Process already started")
        self._temporary = tempfile.TemporaryDirectory(prefix="amiga-copperline-")
        root = Path(self._temporary.name)
        config = "[paths]\nbase = " + json.dumps(str(root)) + "\n"
        if self.floppy:
            config += (
                "[floppy.df0]\npath = "
                + json.dumps(str(Path(self.floppy).resolve()))
                + "\nwrite_protected = true\n"
            )
        if self.host_directory:
            config += (
                "[[filesys]]\npath = "
                + json.dumps(str(Path(self.host_directory).resolve()))
                + '\nvolume = "DH0"\nbootpri = 6\nreadonly = true\n'
            )
        (root / "machine.toml").write_text(config)
        command = [
            self.binary,
            "--factory",
            "--config",
            str(root / "machine.toml"),
            "--model",
            "A500OCS",
            "--cpu",
            "68000",
            "--chipset",
            "OCS",
            "--video",
            "PAL",
            "--chip",
            "512K",
            "--slow",
            "512K",
            "--fast",
            "0",
            "--noaudio",
            "--floppy-speed",
            "0",
            "--control",
            "127.0.0.1:0",
            "--control-info",
            str(root / "endpoint.json"),
        ]
        if self.rom:
            command.append(str(Path(self.rom).resolve()))
        try:
            self.process = subprocess.Popen(
                command,
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env={**os.environ, "COPPERLINE_DBG_RR_BUDGET_MB": "32"},
            )
            self._reader = threading.Thread(target=self._drain_log, daemon=True)
            self._reader.start()
            deadline = time.monotonic() + self.startup_timeout
            while True:
                if self.process.poll() is not None:
                    raise CopperlineError(
                        f"Copperline exited during startup ({self.process.returncode})"
                    )
                try:
                    info = json.loads((root / "endpoint.json").read_text())
                    break
                except FileNotFoundError, ValueError:
                    if time.monotonic() >= deadline:
                        raise CopperlineTimeout(
                            "Copperline endpoint startup timed out"
                        ) from None
                    time.sleep(0.02)
            if info.get("proto") != 1 or not isinstance(info.get("token"), str):
                raise CopperlineError("Invalid control endpoint metadata")
            host, port_text = info["listen"].rsplit(":", 1)
            port = int(port_text)
            if host != "127.0.0.1" or not 1 <= port <= 65535:
                raise CopperlineError("Control endpoint must be loopback")
            sock = socket.create_connection(
                (host, port), timeout=max(0.001, deadline - time.monotonic())
            )
            self.client = CopperlineClient(sock, request_timeout=self.request_timeout)
            hello = self.client.request(
                "hello",
                {"token": info["token"]},
                timeout=max(0.001, deadline - time.monotonic()),
            )
            if (
                hello.get("proto") != 1
                or hello.get("emulator") != "copperline 1.0.0"
                or hello.get("authed") is not True
            ):
                raise CopperlineError(
                    "Expected authenticated Copperline 1.0.0 protocol 1"
                )
            self.endpoint = (host, port)
            return self
        except Exception:
            self.close()
            raise

    def _drain_log(self):
        # Fixed chunks avoid unbounded lines. Never retain the startup token or
        # arbitrary emulator output: counts suffice for lifecycle diagnostics.
        while True:
            chunk = self.process.stdout.read(4096)
            if not chunk:
                break
            self.log_tail.append(f"Copperline output: {len(chunk)} bytes")

    def close(self):
        if self.client is not None:
            try:
                if not self.client.closed:
                    self.client.request(
                        "shutdown", timeout=min(1, self.request_timeout)
                    )
            except CopperlineError:
                pass
            finally:
                self.client.close()
        if self.process is not None:
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
            if self._reader:
                self._reader.join(timeout=1)
            if self.process.stdout:
                self.process.stdout.close()
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None

    def __exit__(self, *exc):
        self.close()
