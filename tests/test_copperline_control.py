"""Transport contracts; real emulator probes opt in with COPPERLINE_BINARY."""

import json
import os
import socket
import threading
from pathlib import Path

import pytest

from amiga_reversing.tools.copperline_control import (
    CopperlineClient,
    CopperlineError,
    CopperlineProcess,
    CopperlineTimeout,
)


def fake_server(handler):
    client_socket, server_socket = socket.socketpair()
    errors = []

    def serve():
        try:
            with server_socket, server_socket.makefile("rwb") as stream:
                handler(stream)
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return CopperlineClient(client_socket, request_timeout=0.1), thread, errors


def read(stream):
    return json.loads(stream.readline())


def reply(stream, request, result):
    stream.write(
        (
            json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result}) + "\n"
        ).encode()
    )
    stream.flush()


@pytest.mark.parametrize(
    "wire",
    [
        b"garbage\n",
        b"[]\n",
        b'{"jsonrpc":"2.0","id":999,"result":{}}\n',
        b'{"jsonrpc":"2.0","id":1,"result":{},"error":{}}\n',
        b"",
    ],
)
def test_bad_response_closes_connection(wire):
    def serve(stream):
        read(stream)
        stream.write(wire)
        stream.flush()

    client, thread, errors = fake_server(serve)
    with pytest.raises(CopperlineError):
        client.request("status")
    assert client.closed
    thread.join(1)
    assert not errors


@pytest.mark.parametrize("pause_first", [True, False])
def test_timeout_pauses_same_stream_drains_both_and_can_reuse(pause_first):
    def serve(stream):
        run = read(stream)
        pause = read(stream)
        assert run["method"] == "run_until" and pause["method"] == "pause"
        for request in [pause, run] if pause_first else [run, pause]:
            reply(stream, request, {"reason": "pause"})
        reply(stream, read(stream), {"paused": True})

    client, thread, errors = fake_server(serve)
    with pytest.raises(CopperlineTimeout, match="emulator paused"):
        client.run_until({"pc": 0x1000}, timeout=0.01)
    assert client.request("status") == {"paused": True}
    client.close()
    thread.join(1)
    assert not errors


def test_pause_unresponsive_disconnects():
    release = threading.Event()

    def serve(stream):
        read(stream)
        read(stream)
        release.wait(1)

    client, thread, errors = fake_server(serve)
    try:
        with pytest.raises(CopperlineTimeout, match="connection closed"):
            client.run_until({"pc": 0x1000}, timeout=0.01)
        assert client.closed
    finally:
        release.set()
        thread.join(1)
    assert not errors


def test_auth_error_never_echoes_server_token():
    def serve(stream):
        request = read(stream)
        stream.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "error": {"code": -32000, "message": "secret-token"},
                }
            ).encode()
            + b"\n"
        )
        stream.flush()

    client, thread, _ = fake_server(serve)
    with pytest.raises(CopperlineError) as error:
        client.request("hello", {"token": "secret-token"})
    assert "secret-token" not in str(error.value)
    thread.join(1)


def test_line_and_notification_limits():
    def serve(stream):
        read(stream)
        stream.write(b"x" * 101)
        stream.flush()

    client, thread, _ = fake_server(serve)
    client.MAX_LINE = 100
    with pytest.raises(CopperlineError, match="line limit"):
        client.request("status")
    thread.join(1)


def test_joystick_sends_complete_state():
    def serve(stream):
        request = read(stream)
        assert request["params"]["port"] == 2
        assert request["params"]["red"] is True
        assert request["params"]["up"] is False
        assert len(request["params"]) == 12
        reply(stream, request, {})

    client, thread, errors = fake_server(serve)
    client.joystick(red=True)
    with pytest.raises(ValueError, match="Invalid joystick"):
        client.joystick(fire=True)
    client.close()
    thread.join(1)
    assert not errors


def test_failed_launch_cleans_temporary_directory(tmp_path):
    process = CopperlineProcess(tmp_path / "missing")
    with pytest.raises(FileNotFoundError):
        process.start()
    assert process._temporary is None
    process.close()


@pytest.mark.skipif(
    not os.environ.get("COPPERLINE_BINARY"),
    reason="Set COPPERLINE_BINARY for real emulator verification",
)
@pytest.mark.parametrize("iteration", range(2))
def test_real_execution_breakpoint_state_and_repeated_cleanup(tmp_path, iteration):
    process = CopperlineProcess(
        os.environ["COPPERLINE_BINARY"], rom=os.environ.get("COPPERLINE_ROM")
    )
    with process:
        client = process.client
        # Synthetic instructions in slow RAM; no original-target parity claim.
        write = client.request(
            "mem.write", {"addr": 0xC10000, "data": "702a528060fc", "encoding": "hex"}
        )
        assert write["replay_unsafe"] is True
        assert client.read_memory(0xC10000, 6) == bytes.fromhex("702a528060fc")
        client.request("regs.set", {"reg": "pc", "value": 0xC10000})
        client.request("step", {"n": 1})
        assert client.registers()["d0"] == 42
        breakpoint = client.add_breakpoint(0xC10004)
        stop = client.run_until({"pc": 0xC10004}, timeout=2)
        assert stop["reason"] in ("target", "breakpoint")
        assert stop["pc"] == 0xC10004
        assert client.registers()["d0"] == 43
        client.remove_breakpoint(breakpoint)
        # Removed breakpoint slots must remain reusable over repeated hits.
        for _ in range(3):
            client.request("regs.set", {"reg": "pc", "value": 0xC10000})
            breakpoint = client.add_breakpoint(0xC10004)
            hit = client.run_until({"pc": 0xC11000}, timeout=2)
            assert hit["reason"] == "breakpoint"
            assert hit["pc"] == 0xC10004
            client.remove_breakpoint(breakpoint)
        snapshot = str(tmp_path / "test.clstate")
        client.request("state.save", {"path": snapshot})
        client.request("step", {"n": 2})
        assert client.registers()["d0"] == 44
        client.request("state.load", {"path": snapshot})
        assert client.registers()["d0"] == 43
        client.joystick(red=True)
        client.joystick()
        with pytest.raises(CopperlineTimeout, match="emulator paused"):
            client.run_until({"pc": 0xC11000}, timeout=0.01)
        assert isinstance(client.registers()["pc"], int)
        client.request("machine.reset", {"kind": "cold"})
        assert client.registers()["pc"] != 0xC10004
        assert client.run_until({"frame": 1}, timeout=2)["reason"] == "target"
        temporary = Path(process._temporary.name)
    assert process.process.poll() is not None
    assert not temporary.exists()
    process.close()


def test_notification_queue_is_bounded():
    def serve(stream):
        request = read(stream)
        for n in range(200):
            stream.write(
                (
                    json.dumps(
                        {"jsonrpc": "2.0", "method": "event.frame", "params": {"n": n}}
                    )
                    + "\n"
                ).encode()
            )
        reply(stream, request, {})

    client, thread, errors = fake_server(serve)
    client.request("status")
    assert len(client.events) == 128
    assert client.events[0]["params"]["n"] == 72
    client.close()
    thread.join(1)
    assert not errors


def test_owned_process_escalates_cleanup(monkeypatch):
    import subprocess

    calls = []

    class Process:
        stdout = None

        def wait(self, timeout):
            calls.append(("wait", timeout))
            if len(calls) < 5:
                raise subprocess.TimeoutExpired("fake", timeout)
            return 0

        def terminate(self):
            calls.append("terminate")

        def kill(self):
            calls.append("kill")

    owner = CopperlineProcess("fake")
    owner.process = Process()
    owner.close()
    assert calls == [("wait", 1), "terminate", ("wait", 1), "kill", ("wait", 2)]
    owner.close()
    assert calls[-1] == ("wait", 1)


def test_raw_key_transition_validates_and_uses_native_protocol():
    def serve(stream):
        for pressed in (True, False):
            req=read(stream)
            assert req['method']=='input.key'
            assert req['params']=={'rawkey':11,'action':'press' if pressed else 'release'}
            reply(stream,req,{})
    client,thread,errors=fake_server(serve)
    client.key(11,pressed=True); client.key(11,pressed=False)
    for key in (-1,128,True):
        with pytest.raises(ValueError): client.key(key,pressed=True)
    client.close();thread.join(1);assert not errors
