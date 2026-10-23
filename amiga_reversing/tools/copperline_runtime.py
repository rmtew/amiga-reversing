"""Bounded Copperline observations; runtime evidence never mutates target facts."""

from __future__ import annotations

import hashlib
import json
import re
import time
from contextlib import suppress
from pathlib import Path

from .copperline_control import CopperlineError, CopperlineProcess, CopperlineTimeout
from .direct_payload_adapter import HANDOFF_RELEASE_VALUE, load_contract

# The measured Pandora ending uses577 authored stages/375 input events. Keep a finite
# plan budget while permitting that single continuous route. Per-phase frame,
# visit, wait and input-release limits remain unchanged.
MAX_SCENARIO_PHASES = 768
MAX_SCENARIO_INPUT_EVENTS = 512
MEMORY_ACCESS_ENGINES = frozenset(
    ["cpu", "blitter", "disk", "copper"]
    + [f"bpl{i}" for i in range(1, 9)]
    + [f"spr{i}" for i in range(8)]
    + [f"aud{i}" for i in range(4)]
)


def validate_memory_access_watch(watch):
    """One address/event or bounded CPU range, independent of snapshot reads."""
    address = watch.get("address") if isinstance(watch, dict) else None
    absolute = type(address) is int and 0 <= address <= 0xFFFFFF
    relative = (
        isinstance(address, dict)
        and set(address) == {"base_register", "offset"}
        and isinstance(address.get("base_register"), str)
        and re.fullmatch(r"a[0-7]", address["base_register"]) is not None
        and type(address.get("offset")) is int
        and -0x1000000 < address["offset"] < 0x1000000
    )
    if (
        not isinstance(watch, dict)
        or set(watch) not in (
            {"address", "access", "engine", "wait_seconds"},
            {"address", "access", "engine", "wait_seconds", "length"},
            {"address", "access", "engine", "wait_seconds", "length", "frames"},
        )
        or not (absolute or relative)
        or watch.get("access") not in ("read", "write", "access")
        or not isinstance(watch.get("engine"), str)
        or watch["engine"] not in MEMORY_ACCESS_ENGINES
        or type(watch.get("wait_seconds")) is not int
        or not 1 <= watch["wait_seconds"] <= 120
        or ("frames" in watch and (
            type(watch["frames"]) is not int or not 1 <= watch["frames"] <= 600
        ))
        or ("length" in watch and (
            watch["engine"] != "cpu" or type(watch["length"]) is not int
            or not 1 <= watch["length"] <= 4096
            or (absolute and address + watch["length"] > 0x1000000)
        ))
    ):
        raise ValueError(
            "Memory access watch requires a 24-bit integer address or a0..a7/offset binding, access "
            "read/write/access, supported engine and wait_seconds (1..120); "
            "optional CPU-only length (1..4096) and frames (1..600), with no address wrapping; no other fields"
        )


def wait_for_memory_access(client, watch, *, start_event=None):
    """Wait for one engine-filtered access; retain backend evidence verbatim.

    Only called after a canonical scenario anchor has passed identity checks.
    The owned session has no other armed watches during this bounded operation.
    CPU ranges use the backend's documented mmio data-access trap. No access
    width is inferred when the backend event does not provide one.
    """
    validate_memory_access_watch(watch)
    frame_window = None
    if "frames" in watch:
        frame = start_event.get("frame") if isinstance(start_event, dict) else None
        if type(frame) is not int or frame < 0:
            raise ValueError("Frame-bounded watch requires the canonical anchor frame")
        frame_window = {"start_frame": frame, "target_frame": frame + watch["frames"]}
    address = watch["address"]
    if isinstance(address, dict):
        address = client.registers()[address["base_register"]] + address["offset"]
        if not 0 <= address <= 0xFFFFFF:
            raise ValueError("Resolved memory access watch address exceeds 24-bit memory")
    if "length" in watch:
        if address + watch["length"] > 0x1000000:
            raise ValueError("Resolved memory access watch address range exceeds 24-bit memory")
        armed = {"kind": "mmio", "addr": address,
                 "len": watch["length"], "access": watch["access"]}
    else:
        armed = {"kind": "watch", "addr": address,
                 "access": watch["access"], "class": watch["engine"]}
    expected_reason = "mmio" if armed["kind"] == "mmio" else "watchpoint"
    registration = client.request("break.add", armed)
    ident = registration["id"]
    started = time.monotonic()
    result = {"requested_watch": dict(watch), "armed_watch": dict(armed),
              "registration": registration, "watch_id": ident,
              "wait_seconds": watch["wait_seconds"], "stop_event": None}
    if frame_window is not None:
        result["frame_window"] = frame_window
    try:
        result["backend_watch_state"] = client.request("break.list")
        state = result["backend_watch_state"]
        breaks = state.get("breaks", []) if isinstance(state, dict) else []
        result["filter_confirmed"] = isinstance(breaks, list) and any(
            isinstance(b, dict) and b.get("id") == ident
            and all(b.get(k) == v for k, v in armed.items()) for b in breaks
        )
        if not result["filter_confirmed"]:
            result.update(status="not_hit", termination="watch_filter_readback_mismatch")
        else:
            try:
                stop = client.run_until(
                    {"frame": frame_window["target_frame"]} if frame_window is not None
                    else {"seconds": 1_000_000_000}, timeout=watch["wait_seconds"]
                )
                result.update(
                    status="hit" if stop.get("reason") == expected_reason else "not_hit",
                    termination="access_observed" if stop.get("reason") == expected_reason
                    else "unexpected_stop",
                    stop_event=stop,
                )
                if frame_window is not None:
                    position = (stop.get("access") or {}).get("position") or {}
                    access_frame = position.get("frame", stop.get("frame"))
                    if result["status"] == "hit" and not (
                        type(access_frame) is int
                        and frame_window["start_frame"] <= access_frame < frame_window["target_frame"]
                    ):
                        result.update(status="not_hit", termination="access_outside_frame_window")
                    elif (stop.get("reason") == "target"
                          and type(stop.get("frame")) is int
                          and stop.get("frame") == frame_window["target_frame"]):
                        result.update(status="not_hit", termination="frame_budget_completed_no_access")
            except CopperlineTimeout as exc:
                result.update(
                    status="timeout", termination="deadline_interrupt",
                    stop_event=exc.stop_event,
                    deadline_recovery={"resume_stop": exc.stop_event,
                                       "pause_stop": exc.pause_event},
                )
        result["queued_stop_notifications"] = [
            event for event in getattr(client, "events", ())
            if event.get("method") == "event.stopped"
        ]
        result["registers"] = client.registers()
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
        return result
    finally:
        # A failure to remove the watch must fail the scenario, not leave an
        # untracked watch that could make a later access appear successful.
        client.remove_breakpoint(ident)


def detect_payload_execution(
    payload_path: Path, pc_address: int, pc_memory: bytes
) -> dict:
    payload = payload_path.read_bytes()
    offsets, start = [], 0
    if pc_memory:
        while len(offsets) < 16:
            offset = payload.find(pc_memory, start)
            if offset < 0:
                break
            offsets.append(offset)
            start = offset + 1
    result = {
        "payload_name": payload_path.name,
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "sample_size": len(pc_memory),
        "matching_offsets": [hex(offset) for offset in offsets],
        "status": "pc_matched"
        if len(offsets) == 1
        else "ambiguous"
        if offsets
        else "not_matched",
    }
    if len(offsets) == 1:
        result.update(
            payload_offset=hex(offsets[0]),
            runtime_base=f"0x{pc_address - offsets[0]:08x}",
        )
    return result


def payload_at_pc(client, path, pc, *, runtime_view=None):
    # A canonical copied view may end immediately after this instruction. Keep
    # the identity window inside that view by including preceding bytes; reading
    # past its end would compare unrelated runtime storage with unloaded input.
    bounds = None
    if runtime_view is not None:
        start, end, base = (runtime_view.get(k) for k in ("source_start", "source_end", "base_addr"))
        if (any(type(v) is not int for v in (start, end, base))
                or not 0 <= start < end <= path.stat().st_size
                or end - start < 16 or not 0 <= base <= 0x1000000 - (end-start)
                or not base <= pc < base + end-start):
            raise CopperlineError("PC identity requires a valid containing canonical view")
        bounds = (base, base + end-start)
    for size in (16, 32, 64, 128, 256):
        address, count = pc, min(size, 0x1000000 - pc)
        if bounds is not None:
            count = min(size, bounds[1]-bounds[0])
            address = max(bounds[0], min(pc, bounds[1]-count))
        sample = client.read_memory(address, count)
        detected = detect_payload_execution(path, address, sample)
        if address != pc:
            bias = pc-address
            detected["matching_offsets"] = [hex(int(v, 0)+bias) for v in detected["matching_offsets"]]
            detected["sample_address"] = f"0x{address:08x}"
            if detected["status"] == "pc_matched":
                detected["payload_offset"] = hex(int(detected["payload_offset"], 0)+bias)
        if detected["status"] != "ambiguous":
            return detected
    return detected


def validate_memory_expectation(read):
    """Validate an optional exact/masked assertion on a bounded memory capture."""
    expected = read.get("expect_hex")
    if "expect_hex" not in read:
        if "expect_mask_hex" in read:
            raise ValueError("Capture expectation mask requires expect_hex")
        return
    size = read.get("size")
    for value in (expected, read.get("expect_mask_hex", expected)):
        if (type(size) is not int or not 1 <= size <= 64
                or not isinstance(value, str) or len(value) != size*2
                or not re.fullmatch(r"[0-9a-fA-F]+", value)):
            raise ValueError("Capture expectation must be size-matched hexadecimal bytes")


def validate_custom_registers(custom):
    # Copperline accepts named registers or even offsets in the custom block.
    if (not isinstance(custom, list) or len(custom) > 16
            or any(not ((isinstance(n, str) and re.fullmatch(r"[A-Z][A-Z0-9]{1,31}", n))
                        or (type(n) is int and 0 <= n < 0x200 and n % 2 == 0)) for n in custom)):
        raise ValueError("Capture requires at most 16 custom registers by name or even offset below 0x200")


def capture_scenario_state(client, capture):
    if not isinstance(capture, dict):
        raise ValueError("Scenario capture must be an object")
    names, reads = capture.get("registers", []), capture.get("memory_reads", [])
    if (
        not isinstance(names, list)
        or len(names) > 17
        or any(
            not isinstance(n, str) or not re.fullmatch("(?:[ad][0-7]|sr)", n)
            for n in names
        )
    ):
        raise ValueError(
            "Capture requires at most 17 valid 68000 registers, including sr"
        )
    if not isinstance(reads, list) or len(reads) > 64:
        raise ValueError("Capture requires at most 64 memory reads")
    regs = client.registers()
    output = []
    for read in reads:
        if not isinstance(read, dict):
            raise ValueError("Memory read must be an object")
        validate_memory_expectation(read)
        addr, base, offset, size = (
            read.get("address"),
            read.get("base_register"),
            read.get("offset", 0),
            read.get("size"),
        )
        if base is not None:
            if (
                addr is not None
                or not isinstance(base, str)
                or not re.fullmatch("a[0-7]", base)
                or type(offset) is not int
            ):
                raise ValueError(
                    "Memory read requires one address or address register plus integer offset"
                )
            addr = regs[base] + offset
        if (
            type(size) is not int
            or not 1 <= size <= 64
            or type(addr) is not int
            or not 0 <= addr <= 0x1000000 - size
        ):
            raise ValueError(
                "Memory read requires 1..64 bytes in the 24-bit address space"
            )
        output.append(
            {
                "address": f"0x{addr:08x}",
                "bytes": client.read_memory(addr, size).hex(),
                "base_register": base,
                "offset": offset if base is not None else None,
            }
        )
        if "expect_hex" in read:
            actual = bytes.fromhex(output[-1]["bytes"])
            expected = bytes.fromhex(read["expect_hex"])
            mask = bytes.fromhex(read.get("expect_mask_hex", "ff"*size))
            output[-1]["expectation"] = {
                "expected_hex": expected.hex(), "mask_hex": mask.hex(),
                "matched": len(actual) == size and all(
                    a & m == e & m for a, e, m in zip(actual, expected, mask))}
    result = {"registers": {n: f"0x{regs[n]:08x}" for n in names}, "memory_reads": output}
    custom = capture.get("custom_registers", [])
    validate_custom_registers(custom)
    if custom:
        result["custom_registers"] = {}
        for name in custom:
            key = name if isinstance(name, str) else f"0x{name:03x}"
            try:
                result["custom_registers"][key] = client.request("custom.read", {"reg": name})
            except CopperlineError as exc:
                raise CopperlineError(f"Custom register capture {key} failed: {exc}") from None
    return result


def wait_for_pc(client, address, seconds, *, frame_limit=None):
    if (
        type(address) is not int
        or not 0 <= address <= 0xFFFFFF
        or isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or not 0 < seconds <= 120
    ):
        raise ValueError(
            "Breakpoint requires a 24-bit address and wait of 0..120 seconds"
        )
    ident = client.add_breakpoint(address)
    try:
        try:
            stop = client.run_until(
                {"frame": frame_limit} if frame_limit is not None else {"pc": address},
                timeout=seconds,
            )
            regs = client.registers()
            hit = (
                stop.get("reason") in ("target", "breakpoint") and regs["pc"] == address
            )
            if frame_limit is not None and type(stop.get("frame")) is int and stop["frame"] >= frame_limit:
                hit = False
            status, termination = (
                ("hit", "breakpoint_hit") if hit else ("not_hit", "unexpected_stop")
            )
            if (not hit and frame_limit is not None and stop.get("reason") == "target"
                    and stop.get("frame") == frame_limit):
                termination = "frame_budget_exhausted"
        except CopperlineTimeout:
            regs = client.registers()
            stop, status, termination = (
                {"reason": "pause"},
                "timeout",
                "deadline_interrupt",
            )
        result = {
            "address": f"0x{address:08x}",
            "status": status,
            "termination": termination,
            "stop_reason": "breakpoint-hit" if status == "hit" else stop.get("reason"),
            "stop_event": stop if status != "timeout" else None,
            "pc": f"0x{regs['pc']:08x}",
            "sp": f"0x{regs['sp']:08x}",
            "stack_return_address": None,
        }
        if 0 <= regs["sp"] <= 0xFFFFFC:
            with suppress(CopperlineError):
                result["stack_return_address"] = (
                    f"0x{int.from_bytes(client.read_memory(regs['sp'], 4), 'big'):08x}"
                )
        return result
    finally:
        with suppress(CopperlineError):
            client.remove_breakpoint(ident)


def wait_for_marker(client, address, expected, seconds, *, write_watch=True):
    if not 0 <= address <= 0xFFFFFC or (
        expected is not None and (not isinstance(expected, bytes) or len(expected) != 4)
    ):
        raise ValueError("Observation marker must be four bytes at a 24-bit address")
    started = time.monotonic()
    ident = (
        client.request(
            "break.add", {"kind": "watch", "addr": address, "access": "write"}
        )["id"]
        if write_watch
        else None
    )
    frame = 0
    reason = "observation_present"
    try:
        for _ in range(4096):
            value = client.read_memory(address, 4)
            if value == expected or (expected is None and reason == "watchpoint"):
                return {
                    "address": f"0x{address:08x}",
                    "bytes": value.hex(),
                    "matched": True,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                    "stop_reason": reason,
                }
            remaining = seconds - (time.monotonic() - started)
            if remaining <= 0:
                break
            try:
                stop = client.run_until(
                    {"seconds": 1_000_000_000} if write_watch else {"frame": frame + 1},
                    timeout=remaining,
                )
            except CopperlineTimeout:
                reason = "deadline_interrupt"
                break
            reason = stop.get("reason")
            frame = stop.get("frame", frame + 1)
            if reason != ("watchpoint" if write_watch else "target"):
                break
        value = client.read_memory(address, 4)
        return {
            "address": f"0x{address:08x}",
            "bytes": value.hex(),
            "matched": value == expected
            or (expected is None and reason == "watchpoint"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "stop_reason": reason,
        }
    finally:
        if ident is not None:
            with suppress(CopperlineError):
                client.remove_breakpoint(ident)


def verify_handoff(client, contract, payload_path):
    payload = payload_path.read_bytes()
    expected = contract.payload_sha256
    if hashlib.sha256(payload).hexdigest() != expected:
        raise CopperlineError("Local payload does not match direct contract")
    digest = hashlib.sha256()
    for offset in range(0, len(payload), 65536):
        digest.update(
            client.read_memory(
                contract.load_address + offset, min(65536, len(payload) - offset)
            )
        )
    if digest.hexdigest() != expected:
        raise CopperlineError(
            "Handoff memory does not match the entire contracted payload"
        )
    seeds=[]
    if getattr(contract,'seed_copies',()):
        from .direct_payload_adapter import normalize_seed_copies
        for source,address,size in normalize_seed_copies(contract.seed_copies,
                payload_size=len(payload),load_address=contract.load_address):
            data=client.read_memory(address,size)
            if data!=payload[source:source+size]:
                raise CopperlineError('Guest loader seed does not match declared staged input bytes')
            seeds.append(dict(source_offset=source,runtime_address=address,size=size,
                sha256=hashlib.sha256(data).hexdigest(),phase='guest_shim_before_handoff',readback_verified=True))
    report = {
        "payload_sha256": expected,
        "size": len(payload),
        "load_address": contract.load_address,
        "status": "verified",
    }
    if seeds:report['loader_seeds']=seeds
    return report


def release_handoff(client, contract):
    expected = HANDOFF_RELEASE_VALUE.to_bytes(4, "big")
    client.request(
        "mem.write",
        {
            "addr": contract.handoff_marker_address,
            "data": expected.hex(),
            "encoding": "hex",
        },
    )
    if client.read_memory(contract.handoff_marker_address, 4) != expected:
        raise CopperlineError("Handoff release did not persist")
    client.request("reverse_anchor")
    return {
        "memory_write": "handoff_release",
        "reverse_anchor": "after_write",
        "replay_across_write": False,
    }


def prepare_materialization(client, contract, payload_path, seconds):
    """Consume input only at the declared native copy handoff, before game code.

    The versioned, payload-hash-bound contract asserts that its input copy is no
    longer read after this boundary. Verify the *entire* copied view before any
    initialization; ownership of input backing is retained for the process life.
    """
    from .direct_payload_adapter import validate_materialization

    payload = payload_path.read_bytes()
    validate_materialization(contract, len(payload))
    m = contract.materialization
    entry = m["runtime_address"] + m["entry_source_offset"] - m["source_offset"]
    ident = client.add_breakpoint(entry)
    try:
        boundary = release_handoff(client, contract)
        stop = client.run_until({"pc": entry}, timeout=seconds)
        if stop.get("reason") not in {"target", "breakpoint"} or client.registers()["pc"] != entry:
            raise CopperlineError("Materialization entry was not reached; refusing initialization")
    finally:
        client.remove_breakpoint(ident)
    expected = payload[m["source_offset"]:m["source_offset"]+m["size"]]
    digest = hashlib.sha256()
    for offset in range(0, len(expected), 65536):
        digest.update(client.read_memory(m["runtime_address"]+offset, min(65536, len(expected)-offset)))
    if digest.digest() != hashlib.sha256(expected).digest():
        raise CopperlineError("Materialized memory does not match the entire copied payload")
    report = {"status": "verified", "entrypoint": entry, "size": len(expected),
        "copied_sha256": digest.hexdigest(), "source_consumed_at_entry": True,
        "input_backing_retained": True, "initialization": None}
    if contract.initialization is not None:
        address, data = contract.initialization
        client.request("mem.write", {"addr": address, "data": data.hex(), "encoding": "hex"})
        if client.read_memory(address, len(data)) != data:
            raise CopperlineError("Relocated initialization did not persist")
        client.request("reverse_anchor")
        report["initialization"] = {"address": address, "bytes": data.hex(),
            "readback_verified": True, "reverse_anchor": "after_write", "replay_across_write": False}
    return boundary | {"materialization": report}


def validate_phase_occurrences(phase):
    """Slow semantic goals may poll longer, within an explicit frame bound."""
    value = phase.get("occurrences", 1)
    limit = 1024 if phase.get("until_memory") is not None and "max_frames" in phase else 64
    if type(value) is not int or not 1 <= value <= limit:
        raise ValueError(f"Scenario occurrences must be an integer from 1 to {limit}")
    return value


def _run_scenario_phase(
    client, phase, payload_path, symbols, function, *, depart_current=False, trace_directory=None,
    start_event=None,
):
    address, seconds = phase.get("breakpoint_address"), phase.get("wait_seconds")
    occurrences = phase.get("occurrences", 1)
    capture_first = phase.get("capture_first", False)
    goal = phase.get("until_memory")
    if goal is not None:
        validate_memory_goal(goal)
        if "max_frames" not in phase or "occurrences" not in phase:
            raise ValueError("Memory goal requires explicit frame and visit budgets")
    if "memory_access_watch" in phase:
        validate_memory_access_watch(phase["memory_access_watch"])
        if not isinstance(phase.get("stable_key"), str):
            raise ValueError("Memory access watch requires a canonical source-row phase")
    if "chip_bus_trace" in phase:
        from .copperline_bus_trace import validate_bus_trace
        validate_bus_trace(phase['chip_bus_trace'])
        if not isinstance(phase.get('stable_key'), str) or 'memory_access_watch' in phase:
            raise ValueError('Chip-bus trace requires its own canonical source-row phase')
    validate_phase_occurrences(phase)
    if type(capture_first) is not bool:
        raise ValueError("Scenario capture_first must be boolean")
    counted = "occurrences" in phase or capture_first or depart_current
    if counted and not isinstance(phase.get("stable_key"), str):
        raise ValueError("Occurrence capture requires a canonical source-row phase")
    if type(seconds) not in (int, float) or not 0 < seconds <= 120:
        raise ValueError("Scenario phase wait must be from 0 to 120 seconds")
    deadline = time.monotonic() + seconds
    frame_limit = None
    if "max_frames" in phase:
        validate_phase_frame_budget(phase["max_frames"])
        if (not isinstance(start_event, dict) or type(start_event.get("frame")) is not int
                or start_event["frame"] < 0):
            raise ValueError("Phase frame budget requires a preceding stopped-frame anchor")
        frame_limit = start_event["frame"] + phase["max_frames"]
    item = {
        "name": phase["name"],
        "stable_key": phase.get("stable_key"),
        "capture": None,
        "resolved_function": None,
        "occurrences_requested": occurrences,
        "occurrences_observed": 0,
        "first_visit": None,
        "last_visit": None,
    }
    if capture_first:
        item["first_capture"] = None
    for visit in range(occurrences):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            item.update(status="timeout", termination="phase_deadline")
            break
        if (occurrences > 1 or depart_current or visit > 0) and client.registers()[
            "pc"
        ] == address:
            try:
                stop = client.request("step", {"n": 1}, timeout=remaining)
            except CopperlineTimeout:
                item.update(status="timeout", termination="phase_deadline")
                break
            regs = client.registers()
            if stop.get("reason") != "step" or regs["pc"] == address:
                item.update(
                    status="not_hit",
                    termination="pc_departure_failed",
                    pc=f"0x{regs['pc']:08x}",
                )
                break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            item.update(status="timeout", termination="phase_deadline")
            break
        kwargs = {"frame_limit": frame_limit} if frame_limit is not None else {}
        item.update(wait_for_pc(client, address, remaining if counted else seconds, **kwargs))
        if item["status"] != "hit":
            if frame_limit is not None:
                item["diagnostic_capture"] = capture_scenario_state(client, phase.get("capture", {}))
                item["diagnostic_payload"] = payload_at_pc(client, payload_path, client.registers()["pc"])
                item["frame_limit"] = frame_limit
            break
        detection = payload_at_pc(client, payload_path, address, runtime_view=phase.get("runtime_view"))
        item["payload"] = detection
        offset = phase.get("source_offset")
        if detection["status"] != "pc_matched" or (
            offset is not None and int(detection["payload_offset"], 0) != offset
        ):
            item.update(status="not_hit", termination="payload_identity_mismatch")
            break
        view = symbols.get("runtime_view", {})
        expected_base = view.get("runtime_base")
        if type(view.get("base_addr")) is int and type(view.get("source_start")) is int:
            expected_base = view["base_addr"] - view["source_start"]
        if (
            expected_base is not None
            and int(detection["runtime_base"], 0) != expected_base
        ):
            item.update(status="not_hit", termination="runtime_mapping_mismatch")
            break
        item["occurrences_observed"] += 1
        summary = {
            "pc": item["pc"],
            "payload_offset": detection["payload_offset"],
            "runtime_base": detection["runtime_base"],
        }
        if item["first_visit"] is None:
            item["first_visit"] = summary
        item["last_visit"] = summary
        item["capture"] = capture_scenario_state(client, phase.get("capture", {}))
        if any(not r.get("expectation", {}).get("matched", True)
               for r in item["capture"]["memory_reads"]):
            item.update(status="not_hit", termination="capture_expectation_mismatch")
            break
        if capture_first and item["occurrences_observed"] == 1:
            item["first_capture"] = item["capture"]
        if counted and time.monotonic() > deadline:
            item.update(status="timeout", termination="phase_deadline")
            break
        if goal is not None:
            goal_capture = capture_scenario_state(client, {"memory_reads": [goal]})
            item["goal_capture"] = goal_capture
            if time.monotonic() > deadline:
                item.update(status="timeout", termination="phase_deadline")
                break
            if goal_capture["memory_reads"][0]["expectation"]["matched"]:
                break
            item.update(status="not_hit", termination="goal_not_reached")
        item["resolved_function"] = function
        if counted and time.monotonic() > deadline:
            item.update(status="timeout", termination="phase_deadline")
            break
    if item.get("status") == "hit" and "memory_access_watch" in phase:
        watch = wait_for_memory_access(
            client, phase["memory_access_watch"], start_event=item.get("stop_event")
        )
        item["memory_access_watch"] = watch
        watch["payload_at_stop"] = payload_at_pc(
            client, payload_path, watch["registers"]["pc"],
        )
        access = (watch.get("stop_event") or {}).get("access")
        if (watch["status"] == "hit" and phase["memory_access_watch"]["engine"] == "cpu"
                and isinstance(access, dict) and type(access.get("pc")) is int
                and 0 <= access["pc"] <= 0xFFFFFF):
            # The paused PC can follow the accessing instruction. Verify the
            # event's instruction address independently rather than conflating them.
            watch["payload_at_access"] = payload_at_pc(client, payload_path, access["pc"])
        watch["capture"] = capture_scenario_state(client, phase.get("capture", {}))
        if watch["status"] != "hit":
            item.update(status=watch["status"], termination=watch["termination"])
        elif any(not r.get("expectation", {}).get("matched", True)
                 for r in watch["capture"]["memory_reads"]):
            item.update(status="not_hit", termination="watch_capture_expectation_mismatch")
        item["stop_reason"] = (
            watch["stop_event"].get("reason") if watch["stop_event"] else watch["termination"]
        )
    if item.get('status') == 'hit' and 'chip_bus_trace' in phase:
        from .copperline_bus_trace import capture_bus_trace
        trace = capture_bus_trace(client, phase['chip_bus_trace'], item.get('stop_event'), trace_directory)
        item['chip_bus_trace'] = trace
        trace['registers'] = client.registers()
        trace['payload_at_stop'] = payload_at_pc(client, payload_path, trace['registers']['pc'])
        trace['capture'] = capture_scenario_state(client, phase.get('capture', {}))
        if trace['status'] != 'captured':
            item.update(status='not_hit', termination='chip_bus_trace_'+trace['status'])
        elif any(not r.get('expectation', {}).get('matched', True)
                 for r in trace['capture']['memory_reads']):
            item.update(status='not_hit', termination='trace_capture_expectation_mismatch')
        item['stop_reason'] = (trace.get('stop_event') or {}).get('reason', trace['status'])
    if not counted:
        for key in (
            "occurrences_requested",
            "occurrences_observed",
            "first_visit",
            "last_visit",
        ):
            item.pop(key)
    return item


def validate_phase_frame_budget(value):
    if type(value) is not int or not 1 <= value <= 3600:
        raise ValueError("Phase max_frames must be an integer from 1 to 3600")


def validate_memory_goal(value):
    if not isinstance(value, dict) or "expect_hex" not in value or "address" not in value:
        raise ValueError("Memory goal requires an absolute capture read and expectation")
    # Reuse exactly the capture read schema and expectation semantics.
    from .copperline_session import validate_capture
    validate_capture({"memory_reads": [value]})


def phase_stop_event(item):
    """Use the actual paused endpoint after an optional observer hook."""
    if item is None:
        return None
    for name in ("chip_bus_trace", "memory_access_watch"):
        if name in item:
            return item[name].get("stop_event")
    return item.get("stop_event")


def run_scenario(client, scenario, payload_path, release=None, *, trace_directory=None):
    phases, events = scenario.get("phases"), scenario.get("input_events", [])
    if (
        not isinstance(phases, list)
        or not phases
        or len(phases) > MAX_SCENARIO_PHASES
        or not isinstance(events, list)
        or len(events) > MAX_SCENARIO_INPUT_EVENTS
    ):
        raise ValueError(
            f"Scenario requires 1..{MAX_SCENARIO_PHASES} compiled phases and at most {MAX_SCENARIO_INPUT_EVENTS} input events"
        )
    names = [p.get("name") for p in phases if isinstance(p, dict)]
    if (
        len(names) != len(phases)
        or any(not isinstance(n, str) or not n for n in names)
        or len(set(names)) != len(names)
    ):
        raise ValueError("Scenario phase names must be unique strings")
    for event in events:
        if (
            not isinstance(event, dict)
            or event.get("after_phase") not in names
            or event.get("release_after_phase") not in names
        ):
            raise ValueError("Input events require named press and release phases")
        if names.index(event["release_after_phase"]) <= names.index(
            event["after_phase"]
        ):
            raise ValueError("Input release must follow press")
        if not isinstance(event.get("control"), str) or not re.fullmatch(
            r"(?:port[01] (?:fire|left|right|up|down)|key (?:[0-9]|[1-9][0-9]|1[01][0-9]|12[0-7]))", event["control"]
        ):
            raise ValueError("Unsupported input control")
    symbols = scenario.get("symbols") or {}
    functions = symbols.get("functions", [])
    held, result, confirmed = {1: {}, 2: {}}, [], False
    held_keys = set()
    reverse_boundary = None
    input_trace = []
    input_anchor = None
    def send_input(method, arguments, *, cleanup=False):
        row = {"method": method, "arguments": arguments, "anchor": input_anchor,
               "cleanup": cleanup, "outcome": "uncertain"}
        input_trace.append(row)
        response = (client.key(arguments["rawkey"], pressed=arguments["pressed"])
                    if method == "key" else client.joystick(**arguments))
        row["outcome"] = "acknowledged"
        return response
    try:
        for index, phase in enumerate(phases):
            address, transition = (
                phase.get("breakpoint_address"),
                phase.get("transition", "continue"),
            )
            function = next(
                (f for f in functions if f.get("runtime_start") == address), None
            )
            if transition not in ("continue", "enter_function"):
                raise ValueError("Unsupported scenario transition")
            if transition == "enter_function" and (not confirmed or function is None):
                raise CopperlineError(
                    "Function entry needs confirmed runtime identity and accepted exact function entry"
                )
            if index == 0 and release is not None:
                reverse_boundary = release()
            previous = result[-1] if result else None
            depart_current = (
                previous is not None and previous.get("address") == f"0x{address:08x}"
            )
            item = _run_scenario_phase(
                client,
                phase,
                payload_path,
                symbols,
                function,
                depart_current=depart_current,
                trace_directory=trace_directory,
                start_event=phase_stop_event(previous),
            )
            result.append(item)
            input_anchor = {"phase": phase["name"], "stop": phase_stop_event(item)}
            if item["status"] != "hit":
                break
            confirmed = True
            next_held = {1: {}, 2: {}}
            next_keys = set()
            for event in events:
                if (
                    names.index(event["after_phase"])
                    <= index
                    < names.index(event["release_after_phase"])
                ):
                    port, key = event["control"].split()
                    if port == "key":
                        next_keys.add(int(key))
                        continue
                    port = int(port[-1]) + 1
                    next_held[port]["red" if key == "fire" else key] = True
            for port, state in next_held.items():
                if state != held[port]:
                    send_input("joystick", {"port": port, **state})
            held = next_held
            for key in sorted(held_keys - next_keys):
                send_input("key", {"rawkey": key, "pressed": False})
                held_keys.remove(key)
            for key in sorted(next_keys - held_keys):
                # Track before sending: a lost response can still have pressed it.
                held_keys.add(key)
                send_input("key", {"rawkey": key, "pressed": True})
        return {
            "identifier": scenario.get("identifier"),
            "symbols": symbols,
            "phases": result,
            "reverse_boundary": reverse_boundary,
            "input_trace": input_trace,
        }
    finally:
        for key in sorted(held_keys):
            with suppress(CopperlineError):
                send_input("key", {"rawkey": key, "pressed": False}, cleanup=True)
        for port in held:
            with suppress(CopperlineError):
                send_input("joystick", {"port": port}, cleanup=True)


def ndk_field_offset(ndk: dict[str, object], struct_name: str, field_name: str) -> int:
    structs = ndk["structs"]
    fields = structs[struct_name]["fields"]
    for field in fields:
        if field["name"] == field_name:
            return int(field["offset"])
    raise CopperlineError(f"NDK has no {struct_name}.{field_name} field.")


def inspect_node(
    client: object,
    address: int,
    node_type_offset: int,
    node_name_offset: int,
    known_types: dict[str, int],
) -> tuple[dict[str, object], int]:
    node = read_memory(client, address, node_name_offset + 4)
    successor = int.from_bytes(node[:4], "big")
    name_address = int.from_bytes(node[node_name_offset : node_name_offset + 4], "big")
    name_bytes = read_memory(client, name_address, 64) if name_address else b""
    name = name_bytes.split(b"\0", 1)[0].decode("latin-1", errors="replace") or None
    node_type = node[node_type_offset]
    type_name = next(
        (name for name, value in known_types.items() if value == node_type), None
    )
    return {
        "address": f"0x{address:08x}",
        "node_type": node_type,
        "node_type_name": type_name,
        "name": name,
    }, successor


def read_c_string(client: object, address: int) -> str | None:
    if not address:
        return None
    return (
        read_memory(client, address, 64)
        .split(b"\0", 1)[0]
        .decode("latin-1", errors="replace")
        or None
    )


def exec_base_address(client: object) -> int:
    # ExecBase's absolute pointer is the Amiga Exec ABI's longword at address 4.
    return int.from_bytes(read_memory(client, 4, 4), "big")


def locate_library(client: object, ndk: dict[str, object], library_name: str) -> int:
    exec_base = exec_base_address(client)
    list_address = exec_base + ndk_field_offset(ndk, "ExecBase", "LibList")
    head_offset = ndk_field_offset(ndk, "LH", "LH_HEAD")
    name_offset = ndk_field_offset(ndk, "LN", "LN_NAME")
    node_address = int.from_bytes(
        read_memory(client, list_address + head_offset, 4), "big"
    )
    tail_sentinel = list_address + 4
    for _ in range(64):
        if not node_address or node_address == tail_sentinel:
            break
        node = read_memory(client, node_address, name_offset + 4)
        name_address = int.from_bytes(node[name_offset : name_offset + 4], "big")
        if read_c_string(client, name_address) == library_name:
            return node_address
        node_address = int.from_bytes(node[:4], "big")
    raise CopperlineError(f"{library_name} is not present in ExecBase.LibList.")


def inspect_process_segment(
    client: object, ndk: dict[str, object], process_address: int
) -> dict[str, object]:
    seg_list_offset = ndk_field_offset(ndk, "Process", "pr_SegList")
    seg_list_bptr = int.from_bytes(
        read_memory(client, process_address + seg_list_offset, 4), "big"
    )
    segment_header = seg_list_bptr << 2
    code_address = segment_header + 4 if seg_list_bptr else 0
    code_prefix = read_memory(client, code_address, 16).hex() if code_address else None
    return {
        "segment_list_bptr": f"0x{seg_list_bptr:08x}",
        "segment_code_address": f"0x{code_address:08x}" if code_address else None,
        "segment_code_prefix": code_prefix,
    }


def inspect_current_task(client: object, ndk: dict[str, object]) -> dict[str, object]:
    exec_base = exec_base_address(client)
    if not 0 < exec_base <= 0xFFFF00:
        raise CopperlineError("ExecBase is not initialized")
    this_task_offset = ndk_field_offset(ndk, "ExecBase", "ThisTask")
    node_type_offset = ndk_field_offset(ndk, "LN", "LN_TYPE")
    node_name_offset = ndk_field_offset(ndk, "LN", "LN_NAME")
    list_head_offset = ndk_field_offset(ndk, "LH", "LH_HEAD")
    task = int.from_bytes(read_memory(client, exec_base + this_task_offset, 4), "big")
    known_types = {
        name: int(record["value"])
        for name, record in ndk["constants"].items()
        if name in {"NT_PROCESS", "NT_TASK"}
    }
    current, _ = inspect_node(
        client, task, node_type_offset, node_name_offset, known_types
    )
    if current["node_type_name"] == "NT_PROCESS":
        current["process_segment"] = inspect_process_segment(client, ndk, task)
    report: dict[str, object] = {
        "exec_base": f"0x{exec_base:08x}",
        "active_task": current,
    }
    for report_name, field_name in (
        ("ready_tasks", "TaskReady"),
        ("waiting_tasks", "TaskWait"),
    ):
        list_address = exec_base + ndk_field_offset(ndk, "ExecBase", field_name)
        node_address = int.from_bytes(
            read_memory(client, list_address + list_head_offset, 4), "big"
        )
        tail_sentinel = list_address + 4
        nodes: list[dict[str, object]] = []
        while node_address and node_address != tail_sentinel and len(nodes) < 32:
            node, node_address = inspect_node(
                client, node_address, node_type_offset, node_name_offset, known_types
            )
            if node["node_type_name"] == "NT_PROCESS":
                node["process_segment"] = inspect_process_segment(
                    client, ndk, int(node["address"], 0)
                )
            nodes.append(node)
        report[report_name] = nodes
        report[f"{report_name}_truncated"] = bool(
            node_address and node_address != tail_sentinel
        )
    return report


def read_memory(client, address, count):
    if type(address) is not int or not 0 <= address <= 0x1000000 - count:
        raise CopperlineError("Observed pointer is outside 24-bit memory")
    return client.read_memory(address, count)


def watch_loadseg(client, ndk, seconds):
    dos_base = locate_library(client, ndk, "dos.library")
    address = dos_base + int(
        ndk["libraries"]["dos.library"]["functions"]["LoadSeg"]["lvo"]
    )
    result = wait_for_pc(client, address, seconds)
    result.update(
        dos_library_base=f"0x{dos_base:08x}", loadseg_address=f"0x{address:08x}"
    )
    if result["status"] == "hit":
        result["loadseg_name"] = read_c_string(client, client.registers()["d1"])
    return result


def confirm_checkpoint_input_release(client, scenario):
    """Checkpoint saves require acknowledged cleanup, beyond best-effort finally."""
    for port in (1, 2):
        client.joystick(port=port)
    keys = {int(e['control'].split()[1]) for e in scenario.get('input_events', [])
            if e['control'].startswith('key ')}
    for key in sorted(keys):
        client.key(key, pressed=False)


def observe(session):
    """Run one isolated owned process and return the public observation envelope."""
    if not 0 < session.continue_seconds <= 600:
        raise ValueError("Observation wait must be between 0 and 600 seconds")
    contract = (
        load_contract(session.direct_payload_contract)
        if session.direct_payload_contract
        else None
    )
    if getattr(session,"derived_artifact_manifest",None) is not None:
        if contract is None:
            raise CopperlineError("Derived artifacts require a direct contract")
        from .direct_payload_adapter import bind_derived_contract
        contract,payload_path,manifest=bind_derived_contract(contract,session.derived_artifact_manifest)
        if payload_path.resolve()!=session.target_payload_path.resolve():
            raise CopperlineError("Session payload does not match its derived artifact")
    scenario = (
        json.loads(session.scenario_path.read_text()) if session.scenario_path else None
    )
    from . import copperline_checkpoint as checkpoints
    load_path = getattr(session, 'checkpoint_load', None)
    save_path = getattr(session, 'checkpoint_save', None)
    checkpoint_record = checkpoint_context = None
    if load_path or save_path:
        if (contract is None or scenario is None or getattr(session,'loadseg_watch_seconds',None)
                or session.breakpoint_runtime_address is not None or session.breakpoint_source_offset is not None):
            raise CopperlineError('Checkpoints require a direct scenario without standalone observations')
        checkpoint_context = checkpoints.binding(session,contract,scenario)
        if save_path and (Path(save_path).exists() or checkpoints.snapshot_path(save_path).exists()):
            raise CopperlineError('Checkpoint destination already exists; choose a fresh name')
        if load_path:
            checkpoint_record = checkpoints.read_checkpoint(load_path,checkpoint_context)
    if scenario is not None and (scenario.get('start_observable','direct_payload_handoff') == 'verified_checkpoint') != bool(load_path):
        raise CopperlineError('Scenario start observable does not match checkpoint mode')
    with CopperlineProcess(
        session.binary_path,
        rom=session.rom_path,
        floppy=session.floppy0,
        host_directory=session.host_directory,
    ) as process:
        client = process.client
        marker, handoff, scenario_result, bp = None, None, None, None
        reverse_boundary = None
        checkpoint_result = None
        if checkpoint_record is not None:
            checkpoint_result = checkpoints.restore(client,load_path,checkpoint_record,
                scenario,session.target_payload_path,payload_at_pc)
            handoff = dict(checkpoint_record['root']['handoff'], verification_source='checkpoint_root')
            prepared = dict(checkpoint_record['root']['reverse_boundary'],
                memory_write=None, reverse_anchor='after_state_load', replay_across_load=False,
                verification_source='checkpoint_root', snapshot_sha256=checkpoint_record['snapshot_sha256'])
            stop_reason = 'checkpoint_restored'
        else:
            address = (
                contract.handoff_marker_address
                if contract
                else session.observation_memory_address
            )
            expected = (
                contract.handoff_marker_value.to_bytes(4, "big")
                if contract
                else session.observation_memory_equals
            )
            if address is not None and (
                expected is not None or session.observation_memory_write_watch
            ):
                marker = wait_for_marker(
                    client,
                    address,
                    expected,
                    session.continue_seconds,
                    write_watch=bool(contract) or session.observation_memory_write_watch,
                )
                stop_reason = marker["stop_reason"]
            else:
                try:
                    stop = client.run_until(
                        {"seconds": 1_000_000_000}, timeout=session.continue_seconds
                    )
                    stop_reason = stop.get("reason")
                except CopperlineTimeout:
                    stop_reason = "deadline_interrupt"
                if address is not None:
                    marker = {
                        "address": f"0x{address:08x}",
                        "bytes": client.read_memory(address, 4).hex(),
                        "matched": None,
                    }
            if contract:
                if not marker["matched"]:
                    raise CopperlineError(
                        "Direct payload marker was not observed; refusing release"
                    )
                handoff = verify_handoff(client, contract, session.target_payload_path)
            prepared = None
            if contract and getattr(contract, "materialization", None) is not None:
                prepared = prepare_materialization(client, contract, session.target_payload_path, session.continue_seconds)
        def release():
            return prepared if prepared is not None else release_handoff(client, contract)
        if scenario is not None:
            if contract is None:
                raise ValueError(
                    "Compiled scenarios require a direct-payload handoff contract"
                )
            scenario_result = run_scenario(
                client,
                scenario,
                session.target_payload_path,
                release,
                trace_directory=getattr(session, 'state_directory', None),
            )
            reverse_boundary = scenario_result["reverse_boundary"]
            if scenario_result["phases"]:
                stop_reason = scenario_result["phases"][-1]["stop_reason"]
        elif (
            session.breakpoint_runtime_address is not None
            or session.breakpoint_source_offset is not None
        ):
            address = session.breakpoint_runtime_address
            if contract is None:
                initial = payload_at_pc(
                    client, session.target_payload_path, client.registers()["pc"]
                )
                if initial["status"] != "pc_matched":
                    raise CopperlineError(
                        "Breakpoint requires uniquely matched payload before arming"
                    )
            if address is None:
                regs = client.registers()
                detection = payload_at_pc(
                    client, session.target_payload_path, regs["pc"]
                )
                if detection["status"] != "pc_matched":
                    raise CopperlineError(
                        "Source offset requires uniquely matched payload PC"
                    )
                address = (
                    int(detection["runtime_base"], 0) + session.breakpoint_source_offset
                )
            if contract:
                reverse_boundary = release()
            bp = wait_for_pc(client, address, session.breakpoint_wait_seconds)
            stop_reason = bp["stop_reason"]
            if bp["status"] == "hit":
                found = payload_at_pc(client, session.target_payload_path, address)
                expected_offset = getattr(
                    session, "breakpoint_expected_source_offset", None
                )
                bp["payload"] = found
                if found["status"] != "pc_matched" or (
                    expected_offset is not None
                    and int(found["payload_offset"], 0) != expected_offset
                ):
                    bp.update(status="not_hit", termination="payload_identity_mismatch")
        elif contract:
            reverse_boundary = release()
            try:
                stop = client.run_until(
                    {"seconds": 1_000_000_000}, timeout=session.continue_seconds
                )
                stop_reason = stop.get("reason")
            except CopperlineTimeout:
                stop_reason = "deadline_interrupt"
        ndk = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "knowledge/amiga_ndk_includes_parsed.json"
            ).read_text()
        )
        try:
            exec_state = inspect_current_task(client, ndk)
            exec_state["status"] = "observed"
        except CopperlineError, KeyError, ValueError, IndexError:
            exec_state = {
                "status": "unavailable",
                "reason": "Guest Exec structures unavailable or invalid",
            }
        loader_watch = None
        if getattr(session, "loadseg_watch_seconds", None):
            loader_watch = watch_loadseg(client, ndk, session.loadseg_watch_seconds)
        if loader_watch is not None:
            stop_reason = loader_watch["stop_reason"]
        regs = client.registers()
        detection = payload_at_pc(client, session.target_payload_path, regs["pc"])
        status = "ok"
        if (
            scenario_result
            and (
                len(scenario_result["phases"]) != len(scenario["phases"])
                or any(p["status"] != "hit" for p in scenario_result["phases"])
            )
            or bp
            and bp["status"] != "hit"
        ):
            status = "incomplete"
        if save_path:
            if status == 'ok':
                confirm_checkpoint_input_release(client, scenario)
                checkpoint_result = {'load':checkpoint_result, 'save':checkpoints.save(
                    client,save_path,checkpoint_context,scenario,scenario_result,handoff,
                    reverse_boundary,parent=checkpoint_record,identify=payload_at_pc,
                    payload_path=session.target_payload_path)}
            else:
                checkpoint_result = {'load':checkpoint_result,'save':{'status':'not_saved','reason':'scenario_incomplete'}}
        observation = {
            "status": status,
            "continue_seconds": session.continue_seconds,
            "stop_reason": stop_reason,
            "pc": f"0x{regs['pc']:08x}",
            "sp": f"0x{regs['sp']:08x}",
            "memory_pc": client.read_memory(regs["pc"], 16).hex(),
            "observation_memory": marker,
            "active_execution": {
                "status": "target_payload_executing"
                if detection["status"] == "pc_matched"
                else "unclassified",
                "process": exec_state.get("active_task")
                if exec_state.get("active_task", {}).get("node_type_name")
                == "NT_PROCESS"
                else None,
                "payload": detection,
            },
            "direct_payload_handoff": handoff,
            "reverse_boundary": reverse_boundary,
            "scenario": scenario_result,
            "breakpoint": bp,
            "exec_state": exec_state,
            "loadseg_watch": loader_watch,
            "checkpoint": checkpoint_result,
        }
        return {"status": status, "backend": "copperline", "observation": observation}
