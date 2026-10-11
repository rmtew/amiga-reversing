import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.tools import copperline_runtime as runtime
from amiga_reversing.tools.copperline_control import CopperlineError, CopperlineTimeout


class Client:
    def __init__(self, payload=b""):
        self.memory = bytearray(0x20000)
        self.memory[0x1000 : 0x1000 + len(payload)] = payload
        self.regs = dict(
            pc=0x1000, sp=0x5000, a4=0x1000, a5=0x2000, **{f"d{i}": i for i in range(8)}
        )
        self.calls = []
        self.stop = None

    def registers(self):
        return self.regs.copy()

    def read_memory(self, addr, length):
        return bytes(self.memory[addr : addr + length])

    def add_breakpoint(self, address):
        self.calls.append(("add", address))
        return 1

    def remove_breakpoint(self, ident):
        self.calls.append(("remove", ident))

    def run_until(self, params, timeout):
        self.calls.append(("run", params))
        if isinstance(self.stop, Exception):
            raise self.stop
        self.regs["pc"] = params.get("pc", 0x1000)
        return self.stop or {"reason": "target"}

    def joystick(self, **kwargs):
        self.calls.append(("joy", kwargs))

    def request(self, method, params=None):
        self.calls.append((method, params))
        if method == "mem.write":
            data = bytes.fromhex(params["data"])
            self.memory[params["addr"] : params["addr"] + len(data)] = data
        return {"id": 1}


def payload(tmp_path):
    p = tmp_path / "payload.bin"
    p.write_bytes(bytes(range(256)) * 2 + b"final unique payload bytes")
    return p


def test_payload_identity_is_not_empty_or_ambiguous(tmp_path):
    p = payload(tmp_path)
    assert runtime.detect_payload_execution(p, 0x1000, b"")["status"] == "not_matched"
    assert (
        runtime.detect_payload_execution(p, 0x1000, bytes(range(16)))["status"]
        == "ambiguous"
    )
    assert (
        runtime.detect_payload_execution(p, 0x1200, b"final unique payload bytes")[
            "runtime_base"
        ]
        == "0x00001000"
    )


@pytest.mark.parametrize(
    ("stop", "status"),
    [
        (None, "hit"),
        ({"reason": "double_fault"}, "not_hit"),
        (CopperlineTimeout("expired"), "timeout"),
    ],
)
def test_wait_reason_deadline_and_break_cleanup(stop, status):
    c = Client()
    c.stop = stop
    result = runtime.wait_for_pc(c, 0x1000, 1)
    assert result["status"] == status
    assert c.calls[-1] == ("remove", 1)


def test_entire_handoff_hash_and_reverse_boundary(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    contract = SimpleNamespace(
        payload_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        load_address=0x1000,
        handoff_marker_address=0x5000,
    )
    assert runtime.verify_handoff(c, contract, p)["status"] == "verified"
    c.memory[0x1100] ^= 1
    with pytest.raises(CopperlineError, match="entire"):
        runtime.verify_handoff(c, contract, p)
    boundary = runtime.release_handoff(c, contract)
    assert boundary["replay_across_write"] is False
    assert c.calls[-1][0] == "reverse_anchor"


def test_capture_register_relative_and_bounds():
    c = Client(b"0123456789abcdef")
    result = runtime.capture_scenario_state(
        c,
        {
            "registers": ["a4"],
            "memory_reads": [{"base_register": "a4", "offset": 2, "size": 3}],
        },
    )
    assert result["memory_reads"][0]["bytes"] == b"234".hex()
    for read in (
        {"address": 0xFFFFFF, "size": 2},
        {"address": 0, "size": True},
        {"base_register": "d0", "size": 1},
    ):
        with pytest.raises(ValueError, match="Memory read requires"):
            runtime.capture_scenario_state(c, {"memory_reads": [read]})


def scenario():
    return {
        "identifier": "test",
        "phases": [
            {
                "name": "first",
                "breakpoint_address": 0x1200,
                "source_offset": 0x200,
                "wait_seconds": 1,
            },
            {
                "name": "second",
                "breakpoint_address": 0x1201,
                "source_offset": 0x201,
                "wait_seconds": 1,
            },
        ],
        "input_events": [
            {
                "after_phase": "first",
                "release_after_phase": "second",
                "control": "port1 fire",
            }
        ],
    }


def test_phase_input_and_cleanup(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    result = runtime.run_scenario(c, scenario(), p)
    assert all(p["status"] == "hit" for p in result["phases"])
    joys = [v for k, v in c.calls if k == "joy"]
    assert {"port": 2, "red": True} in joys
    assert joys[-2:] == [{"port": 1}, {"port": 2}]


def test_function_entry_requires_exact_accepted_entry(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    s = scenario()
    s["phases"][1]["transition"] = "enter_function"
    s["symbols"] = {
        "functions": [
            {"name": "function", "runtime_start": 0x1200, "runtime_end": 0x1250}
        ]
    }
    with pytest.raises(CopperlineError, match="exact function entry"):
        runtime.run_scenario(c, s, p)
    assert c.calls[-1] == ("joy", {"port": 2})


def test_wrong_payload_fails_conservatively_and_releases(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    s = scenario()
    s["phases"][0]["source_offset"] = 0
    result = runtime.run_scenario(c, s, p)
    assert result["phases"][0]["termination"] == "payload_identity_mismatch"
    assert len(result["phases"]) == 1
    assert c.calls[-1] == ("joy", {"port": 2})


def test_schema_drift_and_malformed_input_rejected_before_execution(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    s = scenario()
    del s["input_events"][0]["release_after_phase"]
    s["input_events"][0]["duration_seconds"] = 1
    with pytest.raises(ValueError, match="release phases"):
        runtime.run_scenario(c, s, p)
    assert c.calls == []


def test_ndk_task_inspection_uses_declared_offsets_and_bounds():
    c = Client()
    ndk = {
        "structs": {
            name: {
                "fields": [
                    {"name": field, "offset": offset}
                    for field, offset in fields.items()
                ]
            }
            for name, fields in {
                "ExecBase": {"ThisTask": 8, "TaskReady": 16, "TaskWait": 32},
                "LN": {"LN_TYPE": 8, "LN_NAME": 10},
                "LH": {"LH_HEAD": 0},
                "Process": {"pr_SegList": 20},
            }.items()
        },
        "constants": {"NT_TASK": {"value": 1}, "NT_PROCESS": {"value": 13}},
    }

    def put(addr, value):
        c.memory[addr : addr + 4] = value.to_bytes(4, "big")

    put(4, 0x100)
    put(0x108, 0x200)
    c.memory[0x208] = 1
    put(0x20A, 0x300)
    c.memory[0x300:0x305] = b"task\0"
    put(0x110, 0x114)
    put(0x120, 0x124)
    result = runtime.inspect_current_task(c, ndk)
    assert result["active_task"]["name"] == "task"
    assert result["active_task"]["node_type_name"] == "NT_TASK"
    assert result["ready_tasks"] == []
    put(0x108, 0xFFFFFFF0)
    with pytest.raises(CopperlineError, match="24-bit"):
        runtime.inspect_current_task(c, ndk)


def test_loadseg_watch_reads_filename_only_at_verified_hit():
    c = Client()
    c.regs["d1"] = 0x2000
    c.memory[0x2000:0x2006] = b"game\0\0"
    original = runtime.locate_library
    try:
        runtime.locate_library = lambda *a: 0x3000
        result = runtime.watch_loadseg(
            c,
            {"libraries": {"dos.library": {"functions": {"LoadSeg": {"lvo": -150}}}}},
            1,
        )
        assert result["loadseg_name"] == "game"
        c.stop = {"reason": "double_fault"}
        result = runtime.watch_loadseg(
            c,
            {"libraries": {"dos.library": {"functions": {"LoadSeg": {"lvo": -150}}}}},
            1,
        )
        assert "loadseg_name" not in result
    finally:
        runtime.locate_library = original


def test_nonzero_view_source_start_overrides_legacy_runtime_base_alias(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    s = scenario()
    s["symbols"] = {
        "runtime_view": {
            "base_addr": 0x1100,
            "source_start": 0x100,
            "runtime_base": 0x1100,
        }
    }
    assert all(x["status"] == "hit" for x in runtime.run_scenario(c, s, p)["phases"])


def test_overlapping_input_holds_keep_button_pressed(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    s = scenario()
    s["phases"].append(
        {
            "name": "third",
            "breakpoint_address": 0x1202,
            "source_offset": 0x202,
            "wait_seconds": 1,
        }
    )
    s["input_events"].append(
        {
            "after_phase": "first",
            "release_after_phase": "third",
            "control": "port1 fire",
        }
    )
    runtime.run_scenario(c, s, p)
    joys = [v for k, v in c.calls if k == "joy"]
    assert joys == [{"port": 2, "red": True}, {"port": 2}, {"port": 1}, {"port": 2}]


def fake_session(tmp_path, p, **changes):
    attrs = {
        "binary_path": Path("/fake"),
        "rom_path": None,
        "floppy0": None,
        "host_directory": None,
        "target_payload_path": p,
        "continue_seconds": 1,
        "breakpoint_wait_seconds": 1,
        "observation_memory_address": None,
        "observation_memory_equals": None,
        "observation_memory_write_watch": False,
        "direct_payload_contract": None,
        "breakpoint_runtime_address": None,
        "breakpoint_source_offset": None,
        "scenario_path": None,
    }
    attrs.update(changes)
    return SimpleNamespace(**attrs)


def fake_process(monkeypatch, client):
    class Process:
        def __init__(self, *a, **kw):
            self.client = client

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            client.calls.append(("closed", None))

    monkeypatch.setattr(runtime, "CopperlineProcess", Process)
    monkeypatch.setattr(runtime, "inspect_current_task", lambda *a: {})


def test_ordinary_explicit_breakpoint_refuses_unidentified_payload_before_arming(
    tmp_path, monkeypatch
):
    p = payload(tmp_path)
    c = Client()
    fake_process(monkeypatch, c)
    with pytest.raises(CopperlineError, match="before arming"):
        runtime.observe(fake_session(tmp_path, p, breakpoint_runtime_address=0x1200))
    assert not any(k == "add" for k, _ in c.calls)
    assert c.calls[-1] == ("closed", None)


def test_standalone_direct_contract_releases_and_records_reverse_boundary(
    tmp_path, monkeypatch
):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    fake_process(monkeypatch, c)
    contract = SimpleNamespace(
        payload_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        load_address=0x1000,
        handoff_marker_address=0x5000,
        handoff_marker_value=0x48414E44,
    )
    c.memory[0x5000:0x5004] = b"HAND"
    monkeypatch.setattr(runtime, "load_contract", lambda _: contract)
    report = runtime.observe(fake_session(tmp_path, p, direct_payload_contract="test"))
    assert report["observation"]["reverse_boundary"]["replay_across_write"] is False
    assert c.memory[0x5000:0x5004] == b"GO!!"
    assert any(k == "run" for k, _ in c.calls)
    assert c.calls[-1] == ("closed", None)


def test_observe_incomplete_scenario_uses_last_stop_reason(tmp_path, monkeypatch):
    import json

    p = payload(tmp_path)
    c = Client(p.read_bytes())
    fake_process(monkeypatch, c)
    contract = SimpleNamespace(
        payload_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        load_address=0x1000,
        handoff_marker_address=0x5000,
        handoff_marker_value=0x48414E44,
    )
    c.memory[0x5000:0x5004] = b"HAND"
    c.stop = {"reason": "double_fault"}
    monkeypatch.setattr(runtime, "load_contract", lambda _: contract)
    s = tmp_path / "scenario.json"
    s.write_text(json.dumps(scenario()))
    report = runtime.observe(
        fake_session(tmp_path, p, direct_payload_contract="test", scenario_path=s)
    )
    assert report["status"] == report["observation"]["status"] == "incomplete"
    assert report["observation"]["stop_reason"] == "double_fault"


def test_marker_write_only_stops_on_first_write_and_polling_avoids_watch():
    c = Client()
    c.stop = {"reason": "watchpoint"}
    result = runtime.wait_for_marker(c, 0x5000, None, 1)
    assert result["matched"] is True
    c = Client()
    c.memory[0x5000:0x5004] = b"HAND"
    assert runtime.wait_for_marker(c, 0x5000, b"HAND", 1, write_watch=False)["matched"]
    assert not any(k == "break.add" for k, _ in c.calls)
