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
        self.watch = None

    def registers(self):
        return self.regs.copy()

    def read_memory(self, addr, length):
        return bytes(self.memory[addr : addr + length])

    def add_breakpoint(self, address):
        self.calls.append(("add", address))
        return 1

    def remove_breakpoint(self, ident):
        self.calls.append(("remove", ident))
        self.watch = None

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
        if method == "break.add":
            self.watch = dict(params, id=1)
        if method == "break.list":
            return {"breaks": [self.watch] if self.watch else []}
        if method == "mem.write":
            data = bytes.fromhex(params["data"])
            self.memory[params["addr"] : params["addr"] + len(data)] = data
        return {"id": 1}


def payload(tmp_path):
    p = tmp_path / "payload.bin"
    p.write_bytes(bytes(range(256)) * 2 + b"final unique payload bytes")
    return p


def access_watch(**changes):
    return dict(address=0x49DC8, access="read", engine="blitter", wait_seconds=1,
                **changes)


@pytest.mark.parametrize("changes", [
    {"address": True}, {"address": -1}, {"address": 0x1000000},
    {"address": "0x49dc8"}, {"access": "execute"}, {"access": []},
    {"engine": "dma"}, {"engine": []}, {"wait_seconds": True},
    {"wait_seconds": 0}, {"wait_seconds": 121}, {"length": 2},
    {"address": {"base_register": "d0", "offset": 0}},
    {"address": {"base_register": "a0", "offset": True}},
    {"address": {"base_register": "a0", "offset": 0, "expression": "pc"}},
])
def test_access_watch_schema_rejects_unsupported_shapes_before_rpc(changes):
    c = Client()
    watch = access_watch()
    watch.update(changes)
    with pytest.raises(ValueError, match="Memory access watch requires"):
        runtime.wait_for_memory_access(c, watch)
    assert c.calls == []


@pytest.mark.parametrize(("stop", "status"), [
    ({"reason": "watchpoint", "detail": "blitter read", "pc": 0x16B0E}, "hit"),
    ({"reason": "breakpoint"}, "not_hit"),
    (CopperlineTimeout("expired"), "timeout"),
])
def test_access_watch_filters_engine_retains_event_and_cleans_up(stop, status):
    c = Client()
    c.stop = stop
    result = runtime.wait_for_memory_access(c, access_watch())
    assert result["status"] == status
    assert result["stop_event"] == (None if isinstance(stop, Exception) else stop)
    assert result["armed_watch"] == {
        "kind": "watch", "addr": 0x49DC8, "access": "read", "class": "blitter",
    }
    assert c.calls[0] == ("break.add", result["armed_watch"])
    assert c.calls[-1] == ("remove", result["watch_id"])
    assert result["filter_confirmed"] is True


@pytest.mark.parametrize("change", [
    {"access": "write"}, {"class": "cpu"}, {"addr": 0x49DCA}, {"id": 2},
])
def test_access_watch_requires_backend_filter_readback_before_resume(change):
    c = Client()
    original = c.request
    def request(method, params=None):
        if method == "break.list":
            return {"breaks": [dict(c.watch, **change)]}
        return original(method, params)
    c.request = request
    result = runtime.wait_for_memory_access(c, access_watch())
    assert result["filter_confirmed"] is False
    assert result["termination"] == "watch_filter_readback_mismatch"
    assert not any(call[0] == "run" for call in c.calls)
    assert c.calls[-1] == ("remove", 1)


def test_access_watch_cleanup_on_error_and_cleanup_failure_is_not_success():
    c = Client()
    c.stop = CopperlineError("transport failure")
    with pytest.raises(CopperlineError, match="transport failure"):
        runtime.wait_for_memory_access(c, access_watch())
    assert c.calls[-1] == ("remove", 1)
    c.stop = {"reason": "watchpoint"}
    def fail_remove(ident):
        raise CopperlineError("cannot remove owned watch")
    c.remove_breakpoint = fail_remove
    with pytest.raises(CopperlineError, match="cannot remove"):
        runtime.wait_for_memory_access(c, access_watch())


def test_access_watch_retains_deadline_recovery_and_queued_stop_evidence():
    c = Client()
    stop = {"reason": "watchpoint", "pc": 0x16B0E}
    paused = {"reason": "pause"}
    c.stop = CopperlineTimeout("expired", stop_event=stop, pause_event=paused)
    c.events = [{"method": "event.stopped", "params": stop}]
    result = runtime.wait_for_memory_access(c, access_watch())
    assert result["status"] == "timeout"
    assert result["stop_event"] == stop
    assert result["deadline_recovery"] == {"resume_stop": stop, "pause_stop": paused}
    assert result["queued_stop_notifications"] == c.events
    assert c.calls[-1] == ("remove", 1)


def test_access_watch_resolves_paused_register_binding_without_wrapping():
    c = Client()
    c.stop = {"reason": "watchpoint"}
    watch = access_watch()
    watch["address"] = {"base_register": "a0", "offset": -2}
    c.regs["a0"] = 0x49DCA
    result = runtime.wait_for_memory_access(c, watch)
    assert result["armed_watch"]["addr"] == 0x49DC8
    assert result["requested_watch"]["address"] == watch["address"]
    for value in (1, 0x1000002):
        c.calls.clear()
        c.regs["a0"] = value
        with pytest.raises(ValueError, match="Resolved memory access watch address"):
            runtime.wait_for_memory_access(c, watch)
        assert c.calls == []


@pytest.mark.parametrize("identity_ok", [False, True])
def test_access_watch_only_arms_after_verified_canonical_anchor(tmp_path, identity_ok):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    phase = dict(name="packet", stable_key="s0:00000200:instruction",
                 breakpoint_address=0x1200, source_offset=0x200,
                 wait_seconds=1, memory_access_watch=access_watch())
    if not identity_ok:
        phase["source_offset"] = 0x201
    original_run = c.run_until
    def run(params, timeout):
        if "pc" in params:
            return original_run(params, timeout)
        return {"reason": "watchpoint", "detail": "blitter read"}
    c.run_until = run
    result = runtime._run_scenario_phase(c, phase, p, {}, None)
    armed = [call for call in c.calls if call[0] == "break.add"]
    assert bool(armed) is identity_ok
    assert result["status"] == ("hit" if identity_ok else "not_hit")
    if identity_ok:
        assert result["payload"]["status"] == "pc_matched"
        assert result["memory_access_watch"]["status"] == "hit"


def test_dma_stop_outside_payload_retains_hit_without_claiming_source_identity(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    original_run = c.run_until
    def run(params, timeout):
        if "pc" in params:
            return original_run(params, timeout)
        c.regs["pc"] = 0xFC0000
        return {"reason": "watchpoint", "pc": 0xFC0000}
    c.run_until = run
    phase = dict(name="packet", stable_key="s0:00000200:instruction",
                 breakpoint_address=0x1200, source_offset=0x200, wait_seconds=1,
                 runtime_view={"base_addr": 0x1000, "source_start": 0,
                               "source_end": p.stat().st_size},
                 memory_access_watch=access_watch())
    result = runtime._run_scenario_phase(c, phase, p, {}, None)
    assert result["status"] == "hit"
    assert result["payload"]["status"] == "pc_matched"
    assert result["memory_access_watch"]["payload_at_stop"]["status"] == "not_matched"


def test_access_timeout_stops_scenario_and_releases_held_input(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    s = scenario()
    s["phases"][1].update(stable_key="s0:00000201:instruction",
                            memory_access_watch=access_watch())
    original_run = c.run_until
    def run(params, timeout):
        if "pc" in params:
            return original_run(params, timeout)
        raise CopperlineTimeout("expired")
    c.run_until = run
    result = runtime.run_scenario(c, s, p)
    assert result["phases"][-1]["status"] == "timeout"
    assert result["phases"][-1]["memory_access_watch"]["stop_event"] is None
    assert ("joy", {"port": 2, "red": True}) in c.calls
    assert c.calls[-1] == ("joy", {"port": 2})


def test_custom_capture_error_identifies_the_rejected_selector():
    c = Client()
    def request(method, params):
        raise CopperlineError("Copperline RPC error (code -32007)")
    c.request = request
    with pytest.raises(CopperlineError, match="capture 0x040 failed.*-32007"):
        runtime.capture_scenario_state(c, {"custom_registers": [0x40]})


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


def test_capture_status_register_observes_carry_without_accepting_other_controls():
    c = Client()
    c.regs["sr"] = 0x2001
    assert runtime.capture_scenario_state(c, {"registers": ["a5", "sr"]})[
        "registers"
    ] == {
        "a5": "0x00002000",
        "sr": "0x00002001",
    }
    for name in ("pc", "ccr", "control"):
        with pytest.raises(ValueError, match="Capture"):
            runtime.capture_scenario_state(c, {"registers": [name]})


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


class OccurrenceClient(Client):
    def __init__(self, payload, clock=None):
        super().__init__(payload)
        self.visits = 0
        self.steps = 0
        self.clock = clock
        self.timeouts = []

    def request(self, method, params=None, *, timeout=None):
        if method == "step":
            self.calls.append((method, params))
            self.steps += 1
            self.regs["pc"] += 2
            if self.clock is not None:
                self.clock[0] += 0.1
            return {"reason": "step"}
        return super().request(method, params)

    def run_until(self, params, timeout):
        self.timeouts.append(timeout)
        # A run at the already-matching PC makes no progress, matching the real
        # isolated Copperline transport probe. Only departed visits are counted.
        if self.regs["pc"] != params["pc"]:
            self.visits += 1
            self.regs["d0"] = self.visits
        if self.clock is not None:
            self.clock[0] += 0.41
        return super().run_until(params, timeout)


def counted_scenario(count=3):
    s = scenario()
    s["phases"] = [s["phases"][0]]
    s["input_events"] = []
    s["phases"][0].update(
        stable_key="s0:00000200:instruction",
        occurrences=count,
        capture_first=True,
        capture={"registers": ["d0"]},
    )
    return s


def test_occurrences_depart_and_validate_each_visit_with_first_and_last_capture(
    tmp_path, monkeypatch
):
    p = payload(tmp_path)
    c = OccurrenceClient(p.read_bytes())
    identities = []
    original = runtime.payload_at_pc

    def identify(*args, **kwargs):
        identities.append(c.visits)
        return original(*args, **kwargs)

    monkeypatch.setattr(runtime, "payload_at_pc", identify)
    phase = runtime.run_scenario(c, counted_scenario(), p)["phases"][0]
    assert phase["status"] == "hit"
    assert phase["occurrences_observed"] == phase["occurrences_requested"] == 3
    assert identities == [1, 2, 3] and c.steps == 2
    assert phase["first_capture"]["registers"]["d0"] == "0x00000001"
    assert phase["capture"]["registers"]["d0"] == "0x00000003"
    assert "visits" not in phase  # No unbounded per-visit capture list.


def test_consecutive_matching_phases_depart_before_first_counted_visit(tmp_path):
    p = payload(tmp_path)
    c = OccurrenceClient(p.read_bytes())
    s = counted_scenario(1)
    second = dict(s["phases"][0], name="next", occurrences=2)
    s["phases"].append(second)
    result = runtime.run_scenario(c, s, p)["phases"]
    assert [x["occurrences_observed"] for x in result] == [1, 2]
    assert c.visits == 3 and c.steps == 2


def test_occurrence_budget_is_shared_and_partial_last_capture_survives(
    tmp_path, monkeypatch
):
    p = payload(tmp_path)
    clock = [0.0]
    monkeypatch.setattr(runtime.time, "monotonic", lambda: clock[0])
    c = OccurrenceClient(p.read_bytes(), clock)
    phase = runtime.run_scenario(c, counted_scenario(), p)["phases"][0]
    assert phase["status"] == "timeout" and phase["termination"] == "phase_deadline"
    assert phase["occurrences_observed"] == 2 and len(c.timeouts) == 2
    assert c.timeouts[1] < c.timeouts[0]
    assert phase["capture"]["registers"]["d0"] == "0x00000002"
    assert c.calls[-2:] == [("joy", {"port": 1}), ("joy", {"port": 2})]


def test_occurrence_identity_failure_does_not_count_or_capture_wrong_visit(
    tmp_path, monkeypatch
):
    p = payload(tmp_path)
    c = OccurrenceClient(p.read_bytes())
    original = runtime.payload_at_pc

    def identify(*args, **kwargs):
        result = original(*args, **kwargs)
        if c.visits == 2:
            result["payload_offset"] = "0x202"
        return result

    monkeypatch.setattr(runtime, "payload_at_pc", identify)
    phase = runtime.run_scenario(c, counted_scenario(), p)["phases"][0]
    assert phase["termination"] == "payload_identity_mismatch"
    assert phase["occurrences_observed"] == 1 and c.visits == 2
    assert phase["capture"]["registers"]["d0"] == "0x00000001"


def test_occurrence_unchanged_pc_fails_after_one_departure_attempt(tmp_path):
    p = payload(tmp_path)

    class Parked(OccurrenceClient):
        def request(self, method, params=None, *, timeout=None):
            if method == "step":
                self.steps += 1
                return {"reason": "step"}
            return super().request(method, params, timeout=timeout)

    c = Parked(p.read_bytes())
    c.regs["pc"] = 0x1200
    phase = runtime.run_scenario(c, counted_scenario(), p)["phases"][0]
    assert phase["termination"] == "pc_departure_failed"
    assert c.steps == 1 and c.visits == phase["occurrences_observed"] == 0


@pytest.mark.parametrize("value", [0, 65, True, "2", 1.5])
def test_occurrences_reject_invalid_bounds_at_runtime(tmp_path, value):
    p = payload(tmp_path)
    with pytest.raises(ValueError, match="occurrences"):
        runtime.run_scenario(
            OccurrenceClient(p.read_bytes()), counted_scenario(value), p
        )


def test_overlapping_keyboard_holds_release_once_and_cleanup_after_failure(tmp_path):
    p=payload(tmp_path); c=Client(p.read_bytes())
    def key(rawkey,*,pressed): c.calls.append(('key',(rawkey,pressed)))
    c.key=key
    s=scenario();s['input_events'][0]['control']='key 11'
    s['input_events'].append(dict(s['input_events'][0]))
    result=runtime.run_scenario(c,s,p)
    assert all(phase['status']=='hit' for phase in result['phases'])
    assert [v for k,v in c.calls if k=='key']==[(11,True),(11,False)]
    c.calls=[]
    def failing_key(rawkey,*,pressed):
        key(rawkey,pressed=pressed)
        if pressed: raise CopperlineError('lost press response')
    c.key=failing_key
    with pytest.raises(CopperlineError,match='lost press'):
        runtime.run_scenario(c,s,p)
    assert [v for k,v in c.calls if k=='key']==[(11,True),(11,False)]


def materialization_contract(p):
    from amiga_reversing.tools.direct_payload_adapter import DirectPayloadContract
    return DirectPayloadContract('test', 'target', hashlib.sha256(p.read_bytes()).hexdigest(),
        0x1000, 0x1000, {}, 0x5000, 0x48414E44,
        materialization={'source_offset': 0, 'size': len(p.read_bytes()),
            'runtime_address': 0x11000, 'entry_source_offset': 0,
            'source_consumed_at_entry': True}, initialization=(0x18000, b'\x00\x40'))


def test_materialization_verifies_whole_copy_then_exact_init_and_anchor(tmp_path):
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    c.memory[0x11000:0x11000+len(p.read_bytes())] = p.read_bytes()
    report = runtime.prepare_materialization(c, materialization_contract(p), p, 2)
    assert report['materialization']['size'] == len(p.read_bytes())
    assert report['materialization']['initialization']['bytes'] == '0040'
    assert c.read_memory(0x18000, 4) == b'\x00\x40\x00\x00'
    assert c.calls[-1][0] == 'reverse_anchor'
    assert len([x for x in c.calls if x[0] == 'run']) == 1


@pytest.mark.parametrize('failure', ['stop', 'wrong_pc', 'copy', 'readback'])
def test_materialization_refuses_before_resume_on_failed_phase(tmp_path, failure):
    p = payload(tmp_path)
    class FaultClient(Client):
        def run_until(self, params, timeout):
            result = super().run_until(params, timeout)
            if failure == 'wrong_pc':
                self.regs['pc'] += 2
            return result
        def request(self, method, params=None):
            result = super().request(method, params)
            if failure == 'readback' and method == 'mem.write' and params['addr'] == 0x18000:
                self.memory[0x18000] ^= 1
            return result
    c = FaultClient(p.read_bytes())
    c.memory[0x11000:0x11000+len(p.read_bytes())] = p.read_bytes()
    if failure == 'stop':
        c.stop = {'reason': 'double_fault'}
    if failure == 'copy':
        c.memory[0x11100] ^= 1
    with pytest.raises(CopperlineError):
        runtime.prepare_materialization(c, materialization_contract(p), p, 2)
    writes = [x for x in c.calls if x[0] == 'mem.write' and x[1]['addr'] == 0x18000]
    assert len(writes) == (1 if failure == 'readback' else 0)
    assert len([x for x in c.calls if x[0] == 'run']) == 1
    assert c.calls[-1][0] != 'reverse_anchor'


@pytest.mark.parametrize('mode', ['free', 'breakpoint', 'scenario'])
def test_observe_materializes_and_initializes_once_before_every_observation_path(tmp_path, monkeypatch, mode):
    import json
    p = payload(tmp_path)
    c = Client(p.read_bytes())
    c.memory[0x11000:0x11000+len(p.read_bytes())] = p.read_bytes()
    c.memory[0x5000:0x5004] = b'HAND'
    fake_process(monkeypatch, c)
    monkeypatch.setattr(runtime, 'load_contract', lambda _: materialization_contract(p))
    options = {'direct_payload_contract': 'test'}
    if mode == 'breakpoint':
        options['breakpoint_runtime_address'] = 0x11000
    elif mode == 'scenario':
        s = tmp_path/'scenario.json'
        s.write_text(json.dumps(scenario()))
        options['scenario_path'] = s
    report = runtime.observe(fake_session(tmp_path, p, **options))
    writes = [(i, v) for i, (k, v) in enumerate(c.calls) if k == 'mem.write']
    assert [v['addr'] for _, v in writes] == [0x5000, 0x18000]
    after_init = c.calls[writes[-1][0]+1:]
    assert after_init[0][0] == 'reverse_anchor'
    assert any(k == 'run' for k, _ in after_init)
    assert report['observation']['reverse_boundary']['materialization']['initialization']['readback_verified']


def test_named_custom_register_capture_uses_read_only_chipset_inspection():
    c = Client()
    result = runtime.capture_scenario_state(c, {'custom_registers': ['AUD0VOL', 'DMACON']})
    assert list(result['custom_registers']) == ['AUD0VOL', 'DMACON']
    assert c.calls == [('custom.read', {'reg': 'AUD0VOL'}), ('custom.read', {'reg': 'DMACON'})]
    for custom in [['AUD0VOL']*17, ['mem.write'], [True], [-2], [1], [0x200]]:
        with pytest.raises(ValueError, match='custom registers'):
            runtime.capture_scenario_state(c, {'custom_registers': custom})


def test_custom_status_offsets_use_chipset_read_instead_of_debugger_memory():
    c = Client()
    result = runtime.capture_scenario_state(c, {'custom_registers': [2, 0x1C, 0x1E, 0x1FE]})
    assert list(result['custom_registers']) == ['0x002', '0x01c', '0x01e', '0x1fe']
    assert c.calls == [('custom.read', {'reg': n}) for n in [2, 0x1C, 0x1E, 0x1FE]]


def test_pc_identity_window_stays_inside_copy_view_at_final_instruction(tmp_path):
    p = tmp_path/'copy.bin'
    data = bytes(range(64)) + b'\x4e\x75' + bytes(range(64, 128))
    p.write_bytes(data)
    c = Client(data[:66])
    # The input beyond the copied view is not materialized here.
    c.memory[0x1042:0x1052] = b'\xff'*16
    view = {'source_start': 0, 'source_end': 66, 'base_addr': 0x1000}
    assert runtime.payload_at_pc(c, p, 0x1040)['status'] == 'not_matched'
    result = runtime.payload_at_pc(c, p, 0x1040, runtime_view=view)
    assert result['status'] == 'pc_matched'
    assert result['payload_offset'] == '0x40'
    assert result['runtime_base'] == '0x00001000'
    assert result['sample_size'] == 16
    assert result['sample_address'] == '0x00001032'
    c.memory[0x103F] ^= 1
    assert runtime.payload_at_pc(c, p, 0x1040, runtime_view=view)['status'] == 'not_matched'


@pytest.mark.parametrize('view', [
    {'source_start': 0, 'source_end': 15, 'base_addr': 0x1000},
    {'source_start': 0, 'source_end': 9999, 'base_addr': 0x1000},
    {'source_start': 0, 'source_end': 66, 'base_addr': 0x2000},
])
def test_pc_identity_refuses_invalid_or_noncontaining_copy_view(tmp_path, view):
    p = payload(tmp_path)
    with pytest.raises(CopperlineError, match='containing canonical view'):
        runtime.payload_at_pc(Client(), p, 0x1040, runtime_view=view)


def test_pc_identity_boundary_with_nonzero_source_start(tmp_path):
    p = tmp_path/'offset-view.bin'
    data = bytes(range(128));p.write_bytes(data)
    c = Client(data[32:96]);c.memory[0x1040:0x1050] = b'\xff'*16
    result = runtime.payload_at_pc(c, p, 0x103E,
        runtime_view={'source_start': 32, 'source_end': 96, 'base_addr': 0x1000})
    assert result['status'] == 'pc_matched'
    assert result['payload_offset'] == '0x5e'
    assert result['runtime_base'] == '0x00000fe0'
    assert result['sample_size'] == 16


def test_memory_expectation_failure_stops_counted_route_and_releases_input(tmp_path):
    p = payload(tmp_path)
    c = OccurrenceClient(p.read_bytes())
    s = counted_scenario(3)
    first = dict(s['phases'][0], name='press', occurrences=1, capture={})
    check = dict(s['phases'][0], name='guard', capture={'memory_reads': [
        {'address': 0x2000, 'size': 1, 'expect_hex': '00', 'expect_mask_hex': '06'}]})
    s['phases'] = [first, check, dict(first, name='never')]
    s['input_events'] = [{'after_phase': 'press', 'release_after_phase': 'never', 'control': 'port1 right'}]
    c.memory[0x2000] = 2
    result = runtime.run_scenario(c, s, p)
    assert len(result['phases']) == 2
    failure = result['phases'][-1]
    assert failure['termination'] == 'capture_expectation_mismatch'
    assert failure['status'] == 'not_hit'
    assert failure['occurrences_observed'] == 1
    assert not failure['capture']['memory_reads'][0]['expectation']['matched']
    assert [v for k,v in c.calls if k == 'joy'][-2:] == [{'port': 1}, {'port': 2}]


def test_memory_expectations_exact_and_masked_are_read_only():
    c = Client(); c.memory[0x2000] = 0x80
    for read in ({'expect_hex': '80'}, {'expect_hex': '00', 'expect_mask_hex': '06'}):
        result = runtime.capture_scenario_state(c, {'memory_reads': [dict(address=0x2000, size=1, **read)]})
        assert result['memory_reads'][0]['expectation']['matched']
    assert c.memory[0x2000] == 0x80
    assert not c.calls


def test_checkpoint_cleanup_requires_acknowledged_full_input_release():
    class CleanupClient:
        def __init__(self):self.calls=[]
        def joystick(self,**kw):self.calls.append(('joy',kw))
        def key(self,key,**kw):self.calls.append(('key',key,kw))
    c=CleanupClient()
    runtime.confirm_checkpoint_input_release(c,{'input_events':[{'control':'key 64'},{'control':'key 64'},{'control':'port1 right'}]})
    assert c.calls==[('joy',{'port':1}),('joy',{'port':2}),('key',64,{'pressed':False})]


def test_checkpoint_cleanup_failure_is_not_suppressed():
    class BrokenCleanup:
        def joystick(self,**kw):raise CopperlineError('release not acknowledged')
    with pytest.raises(CopperlineError,match='not acknowledged'):
        runtime.confirm_checkpoint_input_release(BrokenCleanup(),{})
