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


def payload_at_pc(client, path, pc):
    for size in (16, 32, 64, 128, 256):
        sample = client.read_memory(pc, min(size, 0x1000000 - pc))
        detected = detect_payload_execution(path, pc, sample)
        if detected["status"] != "ambiguous":
            return detected
    return detected


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
    return {"registers": {n: f"0x{regs[n]:08x}" for n in names}, "memory_reads": output}


def wait_for_pc(client, address, seconds):
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
            stop = client.run_until({"pc": address}, timeout=seconds)
            regs = client.registers()
            hit = (
                stop.get("reason") in ("target", "breakpoint") and regs["pc"] == address
            )
            status, termination = (
                ("hit", "breakpoint_hit") if hit else ("not_hit", "unexpected_stop")
            )
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
    return {
        "payload_sha256": expected,
        "size": len(payload),
        "load_address": contract.load_address,
        "status": "verified",
    }


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


def _run_scenario_phase(
    client, phase, payload_path, symbols, function, *, depart_current=False
):
    address, seconds = phase.get("breakpoint_address"), phase.get("wait_seconds")
    occurrences = phase.get("occurrences", 1)
    capture_first = phase.get("capture_first", False)
    if type(occurrences) is not int or not 1 <= occurrences <= 64:
        raise ValueError("Scenario occurrences must be an integer from 1 to 64")
    if type(capture_first) is not bool:
        raise ValueError("Scenario capture_first must be boolean")
    counted = "occurrences" in phase or capture_first or depart_current
    if counted and not isinstance(phase.get("stable_key"), str):
        raise ValueError("Occurrence capture requires a canonical source-row phase")
    if type(seconds) not in (int, float) or not 0 < seconds <= 120:
        raise ValueError("Scenario phase wait must be from 0 to 120 seconds")
    deadline = time.monotonic() + seconds
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
        item.update(wait_for_pc(client, address, remaining if counted else seconds))
        if item["status"] != "hit":
            break
        detection = payload_at_pc(client, payload_path, address)
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
        if capture_first and item["occurrences_observed"] == 1:
            item["first_capture"] = item["capture"]
        item["resolved_function"] = function
        if counted and time.monotonic() > deadline:
            item.update(status="timeout", termination="phase_deadline")
            break
    if not counted:
        for key in (
            "occurrences_requested",
            "occurrences_observed",
            "first_visit",
            "last_visit",
        ):
            item.pop(key)
    return item


def run_scenario(client, scenario, payload_path, release=None):
    phases, events = scenario.get("phases"), scenario.get("input_events", [])
    if (
        not isinstance(phases, list)
        or not phases
        or len(phases) > 64
        or not isinstance(events, list)
        or len(events) > 64
    ):
        raise ValueError(
            "Scenario requires 1..64 compiled phases and at most 64 input events"
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
            )
            result.append(item)
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
                    client.joystick(port=port, **state)
            held = next_held
            for key in sorted(held_keys - next_keys):
                client.key(key, pressed=False)
                held_keys.remove(key)
            for key in sorted(next_keys - held_keys):
                # Track before sending: a lost response can still have pressed it.
                held_keys.add(key)
                client.key(key, pressed=True)
        return {
            "identifier": scenario.get("identifier"),
            "symbols": symbols,
            "phases": result,
            "reverse_boundary": reverse_boundary,
        }
    finally:
        for key in sorted(held_keys):
            with suppress(CopperlineError):
                client.key(key, pressed=False)
        for port in held:
            with suppress(CopperlineError):
                client.joystick(port=port)


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
    with CopperlineProcess(
        session.binary_path,
        rom=session.rom_path,
        floppy=session.floppy0,
        host_directory=session.host_directory,
    ) as process:
        client = process.client
        marker, handoff, scenario_result, bp = None, None, None, None
        reverse_boundary = None
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
        if scenario is not None:
            if contract is None:
                raise ValueError(
                    "Compiled scenarios require a direct-payload handoff contract"
                )
            scenario_result = run_scenario(
                client,
                scenario,
                session.target_payload_path,
                lambda: release_handoff(client, contract),
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
                reverse_boundary = release_handoff(client, contract)
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
            reverse_boundary = release_handoff(client, contract)
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
        }
        return {"status": status, "backend": "copperline", "observation": observation}
