"""Bounded persistent GDB/MI session for the local headless WinUAE runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import queue
import re
import subprocess
import sys
import threading
import time
from contextlib import suppress
from pathlib import Path


class MiError(RuntimeError):
    """A GDB/MI request did not complete successfully."""


class MiTimeout(MiError):
    """A GDB/MI request did not complete before its bounded deadline."""


class MiProcess:
    def __init__(self, gdb_path: Path) -> None:
        self._process = subprocess.Popen(
            [str(gdb_path), "--interpreter=mi2", "--nx", "--quiet"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._token = 1
        threading.Thread(target=self._read_lines, daemon=True).start()

    def _read_lines(self) -> None:
        assert self._process.stdout is not None
        for line in self._process.stdout:
            self._lines.put(line.rstrip("\r\n"))
        self._lines.put(None)

    def command(self, command: str, timeout_seconds: int = 15) -> str:
        if self._process.poll() is not None:
            raise MiError(f"GDB exited with code {self._process.returncode}.")
        token = self._token
        self._token += 1
        assert self._process.stdin is not None
        self._process.stdin.write(f"{token}{command}\n")
        self._process.stdin.flush()
        return self._wait_for(lambda line: line.startswith(f"{token}^"), timeout_seconds)

    def wait_for_stop(self, timeout_seconds: int = 15) -> str:
        return self._wait_for(lambda line: line.startswith("*stopped"), timeout_seconds)

    def _wait_for(self, predicate: object, timeout_seconds: int) -> str:
        deadline = time.monotonic() + timeout_seconds
        transcript: list[str] = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MiTimeout("Timed out waiting for GDB/MI response: " + " | ".join(transcript[-8:]))
            try:
                line = self._lines.get(timeout=remaining)
            except queue.Empty as exc:
                raise MiTimeout("Timed out waiting for GDB/MI response.") from exc
            if line is None:
                raise MiError(f"GDB exited with code {self._process.returncode}: " + " | ".join(transcript[-8:]))
            transcript.append(line)
            if callable(predicate) and predicate(line):
                if "^error," in line:
                    raise MiError(line)
                return line

    def close(self) -> None:
        if self._process.poll() is None:
            try:
                assert self._process.stdin is not None
                self._process.stdin.write("-gdb-exit\n")
                self._process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process.wait(timeout=5)


def mi_value(record: str) -> str | None:
    match = re.search(r'value="([^"]*)"', record)
    return match.group(1) if match else None


def mi_memory_bytes(record: str) -> str | None:
    match = re.search(r'contents="([0-9a-fA-F]*)"', record)
    return match.group(1).lower() if match else None


def mi_stop_reason(record: str) -> str | None:
    match = re.search(r'reason="([^"]*)"', record)
    return match.group(1) if match else None


def mi_address(value: str | None) -> int | None:
    """Parse GDB's address value, which may carry a resolved symbol suffix."""

    if value is None:
        return None
    token = value.split(maxsplit=1)[0]
    try:
        return int(token, 0)
    except ValueError:
        return None


def ndk_field_offset(ndk: dict[str, object], struct_name: str, field_name: str) -> int:
    structs = ndk["structs"]
    fields = structs[struct_name]["fields"]
    for field in fields:
        if field["name"] == field_name:
            return int(field["offset"])
    raise MiError(f"NDK has no {struct_name}.{field_name} field.")


def read_memory(gdb: MiProcess, address: int, count: int) -> bytes:
    record = gdb.command(f"-data-read-memory-bytes 0x{address:x} {count}")
    contents = mi_memory_bytes(record)
    if contents is None or len(contents) != count * 2:
        raise MiError(f"Could not read {count} bytes at 0x{address:08x}: {record}")
    return bytes.fromhex(contents)


def inspect_node(gdb: MiProcess, address: int, node_type_offset: int, node_name_offset: int, known_types: dict[str, int]) -> tuple[dict[str, object], int]:
    node = read_memory(gdb, address, node_name_offset + 4)
    successor = int.from_bytes(node[:4], "big")
    name_address = int.from_bytes(node[node_name_offset : node_name_offset + 4], "big")
    name_bytes = read_memory(gdb, name_address, 64) if name_address else b""
    name = name_bytes.split(b"\0", 1)[0].decode("latin-1", errors="replace") or None
    node_type = node[node_type_offset]
    type_name = next((name for name, value in known_types.items() if value == node_type), None)
    return {
        "address": f"0x{address:08x}",
        "node_type": node_type,
        "node_type_name": type_name,
        "name": name,
    }, successor


def read_c_string(gdb: MiProcess, address: int) -> str | None:
    if not address:
        return None
    return read_memory(gdb, address, 64).split(b"\0", 1)[0].decode("latin-1", errors="replace") or None


def exec_base_address(gdb: MiProcess) -> int:
    # ExecBase's absolute pointer is the Amiga Exec ABI's longword at address 4.
    return int.from_bytes(read_memory(gdb, 4, 4), "big")


def locate_library(gdb: MiProcess, ndk: dict[str, object], library_name: str) -> int:
    exec_base = exec_base_address(gdb)
    list_address = exec_base + ndk_field_offset(ndk, "ExecBase", "LibList")
    head_offset = ndk_field_offset(ndk, "LH", "LH_HEAD")
    name_offset = ndk_field_offset(ndk, "LN", "LN_NAME")
    node_address = int.from_bytes(read_memory(gdb, list_address + head_offset, 4), "big")
    tail_sentinel = list_address + 4
    for _ in range(64):
        if not node_address or node_address == tail_sentinel:
            break
        node = read_memory(gdb, node_address, name_offset + 4)
        name_address = int.from_bytes(node[name_offset : name_offset + 4], "big")
        if read_c_string(gdb, name_address) == library_name:
            return node_address
        node_address = int.from_bytes(node[:4], "big")
    raise MiError(f"{library_name} is not present in ExecBase.LibList.")


def inspect_process_segment(gdb: MiProcess, ndk: dict[str, object], process_address: int) -> dict[str, object]:
    seg_list_offset = ndk_field_offset(ndk, "Process", "pr_SegList")
    seg_list_bptr = int.from_bytes(read_memory(gdb, process_address + seg_list_offset, 4), "big")
    segment_header = seg_list_bptr << 2
    code_address = segment_header + 4 if seg_list_bptr else 0
    code_prefix = read_memory(gdb, code_address, 16).hex() if code_address else None
    return {
        "segment_list_bptr": f"0x{seg_list_bptr:08x}",
        "segment_code_address": f"0x{code_address:08x}" if code_address else None,
        "segment_code_prefix": code_prefix,
    }


def watch_loadseg(gdb: MiProcess, ndk: dict[str, object], timeout_seconds: int) -> dict[str, object]:
    dos_base = locate_library(gdb, ndk, "dos.library")
    loadseg_lvo = int(ndk["libraries"]["dos.library"]["functions"]["LoadSeg"]["lvo"])
    loadseg_address = dos_base + loadseg_lvo
    gdb.command(f"-break-insert *0x{loadseg_address:x}")
    gdb.command("-exec-continue")
    try:
        stop = gdb.wait_for_stop(timeout_seconds)
    except MiTimeout:
        gdb.command("-exec-interrupt")
        stop = gdb.wait_for_stop()
        return {
            "status": "timeout",
            "dos_library_base": f"0x{dos_base:08x}",
            "loadseg_address": f"0x{loadseg_address:08x}",
            "stop_reason": mi_stop_reason(stop),
        }
    d1 = gdb.command("-data-evaluate-expression $d1")
    d1_value = mi_value(d1)
    d1_address = int(d1_value, 0) if d1_value is not None else 0
    return {
        "status": "hit" if mi_stop_reason(stop) == "breakpoint-hit" else "stopped_otherwise",
        "dos_library_base": f"0x{dos_base:08x}",
        "loadseg_address": f"0x{loadseg_address:08x}",
        "stop_reason": mi_stop_reason(stop),
        "loadseg_name": read_c_string(gdb, d1_address),
    }


def detect_payload_execution(payload_path: Path, pc_address: int, pc_memory: bytes) -> dict[str, object]:
    payload = payload_path.read_bytes()
    offsets: list[int] = []
    start = 0
    while len(offsets) < 16:
        offset = payload.find(pc_memory, start)
        if offset < 0:
            break
        offsets.append(offset)
        start = offset + 1
    result: dict[str, object] = {
        "payload_name": payload_path.name,
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "sample_size": len(pc_memory),
        "matching_offsets": [f"0x{offset:x}" for offset in offsets],
    }
    if len(offsets) == 1:
        result.update({
            "status": "pc_matched",
            "payload_offset": f"0x{offsets[0]:x}",
            "runtime_base": f"0x{pc_address - offsets[0]:08x}",
        })
    elif offsets:
        result["status"] = "ambiguous"
    else:
        result["status"] = "not_matched"
    return result


def inspect_current_task(gdb: MiProcess, ndk: dict[str, object]) -> dict[str, object]:
    exec_base = exec_base_address(gdb)
    this_task_offset = ndk_field_offset(ndk, "ExecBase", "ThisTask")
    node_type_offset = ndk_field_offset(ndk, "LN", "LN_TYPE")
    node_name_offset = ndk_field_offset(ndk, "LN", "LN_NAME")
    list_head_offset = ndk_field_offset(ndk, "LH", "LH_HEAD")
    task = int.from_bytes(read_memory(gdb, exec_base + this_task_offset, 4), "big")
    known_types = {
        name: int(record["value"])
        for name, record in ndk["constants"].items()
        if name in {"NT_PROCESS", "NT_TASK"}
    }
    current, _ = inspect_node(gdb, task, node_type_offset, node_name_offset, known_types)
    if current["node_type_name"] == "NT_PROCESS":
        current["process_segment"] = inspect_process_segment(gdb, ndk, task)
    report: dict[str, object] = {
        "exec_base": f"0x{exec_base:08x}",
        "active_task": current,
    }
    for report_name, field_name in (("ready_tasks", "TaskReady"), ("waiting_tasks", "TaskWait")):
        list_address = exec_base + ndk_field_offset(ndk, "ExecBase", field_name)
        node_address = int.from_bytes(read_memory(gdb, list_address + list_head_offset, 4), "big")
        tail_sentinel = list_address + 4
        nodes: list[dict[str, object]] = []
        while node_address and node_address != tail_sentinel and len(nodes) < 32:
            node, node_address = inspect_node(gdb, node_address, node_type_offset, node_name_offset, known_types)
            if node["node_type_name"] == "NT_PROCESS":
                node["process_segment"] = inspect_process_segment(gdb, ndk, int(node["address"], 0))
            nodes.append(node)
        report[report_name] = nodes
        report[f"{report_name}_truncated"] = bool(node_address and node_address != tail_sentinel)
    return report


def pause_at_observation_memory(gdb: MiProcess, *, address: int | None, expected: bytes | None, write_watch: bool, timeout_seconds: int) -> tuple[str, dict[str, object] | None]:
    """Pause at a bounded diagnostic marker, or after the supplied time budget."""

    started = time.monotonic()
    matched = False
    observation = None
    if write_watch:
        if address is None:
            raise MiError("A diagnostic write watch requires a memory address.")
        gdb.command(f'-break-watch -- "*((unsigned char *)0x{address:x})"')
        gdb.command("-exec-continue")
        try:
            stop = gdb.wait_for_stop(timeout_seconds)
        except MiTimeout:
            gdb.command("-exec-interrupt")
            stop = gdb.wait_for_stop()
        value = read_memory(gdb, address, 4)
        return stop, {
            "address": f"0x{address:08x}",
            "bytes": value.hex(),
            "matched": expected is None or value == expected,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "watchpoint": True,
        }
    gdb.command("-exec-continue")
    if address is None:
        time.sleep(timeout_seconds)
        gdb.command("-exec-interrupt")
        return gdb.wait_for_stop(), None
    while True:
        remaining = timeout_seconds - (time.monotonic() - started)
        if remaining <= 0:
            gdb.command("-exec-interrupt")
            stop = gdb.wait_for_stop()
            break
        time.sleep(min(0.25, remaining))
        gdb.command("-exec-interrupt")
        stop = gdb.wait_for_stop()
        if address is not None:
            value = read_memory(gdb, address, 4)
            observation = {"address": f"0x{address:08x}", "bytes": value.hex()}
            matched = expected is not None and value == expected
            if matched:
                break
        gdb.command("-exec-continue")
    if observation is not None:
        observation["matched"] = matched
        observation["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return stop, observation


def run_monitor_input(gdb: MiProcess, control: str, state: str) -> None:
    """Send one allow-listed emulator input event through the scenario bridge."""

    if control not in {f"port{port} {direction}" for port in range(2) for direction in ("fire", "left", "right", "up", "down")}:
        raise MiError(f"Scenario requests unsupported input control: {control}")
    if state not in {"press", "release"}:
        raise MiError(f"Scenario requests unsupported input state: {state}")
    gdb.command(f'-interpreter-exec console "monitor input {control} {state}"')


def capture_scenario_state(gdb: MiProcess, capture: dict[str, object]) -> dict[str, object]:
    """Read only the bounded registers and memory explicitly declared by a scenario."""

    registers = capture.get("registers", [])
    memory_reads = capture.get("memory_reads", [])
    if not isinstance(registers, list) or not all(isinstance(register, str) for register in registers):
        raise MiError("Scenario capture.registers must be a list of register names.")
    if not isinstance(memory_reads, list):
        raise MiError("Scenario capture.memory_reads must be a list.")
    register_values: dict[str, str | None] = {}
    for register in registers:
        if not re.fullmatch(r"[ad][0-7]", register):
            raise MiError(f"Scenario capture has an invalid 68000 register: {register}")
        register_values[register] = mi_value(gdb.command(f"-data-evaluate-expression ${register}"))
    captured_memory: list[dict[str, object]] = []
    for memory_read in memory_reads:
        if not isinstance(memory_read, dict):
            raise MiError("Scenario capture memory read must be an object.")
        address = memory_read.get("address")
        base_register = memory_read.get("base_register")
        offset = memory_read.get("offset", 0)
        size = memory_read.get("size")
        if address is not None and base_register is not None:
            raise MiError("Scenario capture memory read cannot specify both address and base_register.")
        if base_register is not None:
            if not isinstance(base_register, str) or not re.fullmatch(r"a[0-7]", base_register) or not isinstance(offset, int):
                raise MiError("Scenario capture register-relative memory read requires an address register and integer offset.")
            base_value = register_values.get(base_register)
            if base_value is None:
                base_value = mi_value(gdb.command(f"-data-evaluate-expression ${base_register}"))
            if base_value is None:
                raise MiError(f"Scenario capture could not read ${base_register}.")
            address = int(base_value, 0) + offset
        if not isinstance(address, int) or not 0 <= address <= 0xFFFFFF:
            raise MiError("Scenario capture memory address must resolve to a 24-bit integer.")
        if not isinstance(size, int) or not 1 <= size <= 64:
            raise MiError("Scenario capture memory size must be between 1 and 64 bytes.")
        captured_memory.append({"address": f"0x{address:08x}", "bytes": read_memory(gdb, address, size).hex(), "base_register": base_register, "offset": offset if base_register is not None else None})
    return {"registers": register_values, "memory_reads": captured_memory}


def wait_for_phase_breakpoint(gdb: MiProcess, address: int, timeout_seconds: int) -> tuple[bool, str, str | None, list[dict[str, str | None]]]:
    """Wait for one phase's breakpoint while preserving non-phase stops as evidence."""

    deadline = time.monotonic() + timeout_seconds
    intervening_stops: list[dict[str, str | None]] = []
    gdb.command("-exec-continue")
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            gdb.command("-exec-interrupt")
            stop = gdb.wait_for_stop()
            pc = mi_value(gdb.command("-data-evaluate-expression $pc"))
            return False, stop, pc, intervening_stops
        try:
            stop = gdb.wait_for_stop(remaining)
        except MiTimeout:
            gdb.command("-exec-interrupt")
            stop = gdb.wait_for_stop()
            pc = mi_value(gdb.command("-data-evaluate-expression $pc"))
            return False, stop, pc, intervening_stops
        pc = mi_value(gdb.command("-data-evaluate-expression $pc"))
        if mi_stop_reason(stop) == "breakpoint-hit" and mi_address(pc) == address:
            return True, stop, pc, intervening_stops
        intervening_stops.append({"stop_reason": mi_stop_reason(stop), "pc": pc})
        gdb.command("-exec-continue")


def load_scenario_symbols(gdb: MiProcess, symbols: object, target_payload_path: Path) -> dict[str, object]:
    """Load generated symbols only after a uniquely confirmed payload PC."""

    if not isinstance(symbols, dict):
        raise MiError("Scenario is missing generated symbol metadata.")
    elf_path = symbols.get("elf_path")
    view = symbols.get("runtime_view")
    if not isinstance(elf_path, str) or not Path(elf_path).is_file() or not isinstance(view, dict):
        raise MiError("Scenario generated symbol artifact is invalid.")
    expected_base = view.get("base_addr")
    if not isinstance(expected_base, int):
        raise MiError("Scenario generated symbol artifact has no runtime base view.")
    pc_value = mi_value(gdb.command("-data-evaluate-expression $pc"))
    if pc_value is None:
        raise MiError("Could not read PC while confirming the symbol runtime base.")
    pc = int(pc_value, 0)
    detection = detect_payload_execution(target_payload_path, pc, read_memory(gdb, pc, 16))
    if detection.get("status") != "pc_matched" or detection.get("runtime_base") != f"0x{expected_base:08x}":
        raise MiError("Scenario symbol artifact runtime base was not confirmed from the target payload.")
    debugger_path = Path(elf_path).as_posix()
    gdb.command(f'-interpreter-exec console "add-symbol-file {debugger_path} 0x{expected_base:x}"')
    return {"runtime_base": f"0x{expected_base:08x}", "artifact": elf_path, "function_count": len(symbols.get("functions", []))}


def resolved_function(symbols: object, address: int) -> dict[str, object] | None:
    if not isinstance(symbols, dict) or not isinstance(symbols.get("runtime_view"), dict):
        return None
    base = symbols["runtime_view"].get("base_addr")
    source_start = symbols["runtime_view"].get("source_start")
    functions = symbols.get("functions")
    if not isinstance(base, int) or not isinstance(source_start, int) or not isinstance(functions, list):
        return None
    source_offset = source_start + address - base
    for item in functions:
        if isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("source_start"), int) and isinstance(item.get("source_end"), int) and item["source_start"] <= source_offset < item["source_end"]:
            return {"name": item["name"], "source_start": f"0x{item['source_start']:x}", "source_end": f"0x{item['source_end']:x}"}
    return None


def run_scenario(gdb: MiProcess, scenario: dict[str, object], target_payload_path: Path) -> dict[str, object]:
    """Execute a validated phase sequence after the public handoff checkpoint."""

    phases = scenario.get("phases")
    input_events = scenario.get("input_events", [])
    if not isinstance(phases, list) or not phases:
        raise MiError("Scenario must contain at least one executable phase.")
    if not isinstance(input_events, list):
        raise MiError("Scenario input_events must be a list.")
    events_by_phase: dict[str, list[dict[str, object]]] = {}
    for event in input_events:
        if not isinstance(event, dict):
            raise MiError("Scenario input event must be an object.")
        phase_name = event.get("after_phase")
        control = event.get("control")
        delay_seconds = event.get("delay_seconds", 0)
        duration_seconds = event.get("duration_seconds")
        if not isinstance(phase_name, str) or not isinstance(control, str) or not isinstance(delay_seconds, (int, float)) or not isinstance(duration_seconds, (int, float)):
            raise MiError("Scenario input event requires after_phase, control, delay_seconds, and duration_seconds.")
        if not 0 <= delay_seconds <= 30:
            raise MiError("Scenario input delay_seconds must be between 0 and 30.")
        if not 0 < duration_seconds <= 30:
            raise MiError("Scenario input duration_seconds must be between 0 and 30.")
        events_by_phase.setdefault(phase_name, []).append(event)
    result_phases: list[dict[str, object]] = []
    symbols = scenario.get("symbols")
    symbols_loaded = None
    for phase_index, phase in enumerate(phases):
        if not isinstance(phase, dict):
            raise MiError("Scenario phase must be an object.")
        name = phase.get("name")
        address = phase.get("breakpoint_address")
        wait_seconds = phase.get("wait_seconds")
        transition = phase.get("transition", "continue")
        capture = phase.get("capture", {})
        if not isinstance(name, str) or not isinstance(address, int) or not 0 <= address <= 0xFFFFFF:
            raise MiError("Scenario phase requires a name and 24-bit breakpoint_address.")
        if not isinstance(wait_seconds, int) or not 1 <= wait_seconds <= 120:
            raise MiError("Scenario phase wait_seconds must be between 1 and 120.")
        if transition not in {"continue", "enter_function"}:
            raise MiError("Scenario phase transition must be continue or enter_function.")
        if not isinstance(capture, dict):
            raise MiError("Scenario phase capture must be an object.")
        breakpoint_number = None
        if transition == "enter_function":
            if symbols_loaded is None:
                raise MiError("Function entry requires generated symbols loaded after the first confirmed phase.")
            function = resolved_function(symbols, address)
            if function is None:
                raise MiError("Function entry phase must resolve to an accepted named function range.")
            breakpoint_record = gdb.command(f"-break-insert {function['name']}")
            breakpoint_number = re.search(r'number=\\?"(\d+)\\?"', breakpoint_record)
            if breakpoint_number is None:
                raise MiError(f"Could not identify symbolic breakpoint for scenario phase {name}: {breakpoint_record}")
            hit, stop, pc_value, intervening_stops = wait_for_phase_breakpoint(gdb, address, wait_seconds)
        else:
            breakpoint_record = gdb.command(f"-break-insert *0x{address:x}")
            breakpoint_number = re.search(r'number=\\?"(\d+)\\?"', breakpoint_record)
            if breakpoint_number is None:
                raise MiError(f"Could not identify breakpoint for scenario phase {name}: {breakpoint_record}")
            hit, stop, pc_value, intervening_stops = wait_for_phase_breakpoint(gdb, address, wait_seconds)
        capture_result = capture_scenario_state(gdb, capture) if hit else None
        if breakpoint_number is not None:
            gdb.command(f"-break-delete {breakpoint_number.group(1)}")
        result_phases.append({
            "name": name,
            "address": f"0x{address:08x}",
            "status": "hit" if hit else "not_hit",
            "stop_reason": mi_stop_reason(stop),
            "pc": pc_value,
            "intervening_stops": intervening_stops,
            "capture": capture_result,
            "resolved_function": resolved_function(symbols, address) if hit else None,
        })
        if not hit:
            break
        if phase_index == 0:
            symbols_loaded = load_scenario_symbols(gdb, symbols, target_payload_path)
        for event in events_by_phase.get(name, []):
            control = event["control"]
            delay_seconds = float(event["delay_seconds"])
            duration_seconds = float(event["duration_seconds"])
            if delay_seconds:
                gdb.command("-exec-continue")
                time.sleep(delay_seconds)
                gdb.command("-exec-interrupt")
                gdb.wait_for_stop(15)
            run_monitor_input(gdb, control, "press")
            gdb.command("-exec-continue")
            time.sleep(duration_seconds)
            gdb.command("-exec-interrupt")
            gdb.wait_for_stop(15)
            run_monitor_input(gdb, control, "release")
    return {"identifier": scenario.get("identifier"), "symbols": symbols_loaded, "phases": result_phases}


def run_session(gdb_path: Path, ndk_path: Path, continue_seconds: int, loadseg_watch_seconds: int | None, target_payload_path: Path | None, breakpoint_address: int | None, breakpoint_source_offset: int | None, breakpoint_wait_seconds: int, observation_memory_address: int | None, observation_memory_equals: bytes | None, observation_memory_write_watch: bool, scenario_path: Path | None) -> dict[str, object]:
    ndk = json.loads(ndk_path.read_text(encoding="utf-8"))
    gdb = MiProcess(gdb_path)
    try:
        gdb.command("-gdb-set pagination off")
        gdb.command("-gdb-set confirm off")
        gdb.command("-gdb-set mi-async on")
        gdb.command("-target-select remote 127.0.0.1:2345")
        stop, observation_memory = pause_at_observation_memory(
            gdb,
            address=observation_memory_address,
            expected=observation_memory_equals,
            write_watch=observation_memory_write_watch,
            timeout_seconds=continue_seconds,
        )
        pc = gdb.command("-data-evaluate-expression $pc")
        sp = gdb.command("-data-evaluate-expression $sp")
        memory = gdb.command("-data-read-memory-bytes 0xfc0000 8")
        pc_value = mi_value(pc)
        pc_address = int(pc_value, 0) if pc_value is not None else 0
        pc_memory_bytes = read_memory(gdb, pc_address, 16) if pc_address else b""
        pc_memory = pc_memory_bytes.hex() if pc_memory_bytes else None
        observation_memory = observation_memory or (
            {
                "address": f"0x{observation_memory_address:08x}",
                "bytes": read_memory(gdb, observation_memory_address, 4).hex(),
            }
            if observation_memory_address is not None
            else None
        )
        exec_state = inspect_current_task(gdb, ndk)
        loader_watch = watch_loadseg(gdb, ndk, loadseg_watch_seconds) if loadseg_watch_seconds else None
        target_detection = detect_payload_execution(target_payload_path, pc_address, pc_memory_bytes) if target_payload_path and pc_memory_bytes else None
        active_task = exec_state["active_task"]
        active_process = active_task if active_task["node_type_name"] == "NT_PROCESS" else None
        active_execution = {
            "status": "target_payload_executing" if target_detection and target_detection["status"] == "pc_matched" else "unclassified",
            "process": active_process,
            "payload": target_detection,
        }
        scenario = json.loads(scenario_path.read_text(encoding="utf-8")) if scenario_path is not None else None
        if isinstance(scenario, dict) and target_payload_path is None:
            raise MiError("Scenario symbols require a target payload for runtime-base confirmation.")
        scenario_result = run_scenario(gdb, scenario, target_payload_path) if isinstance(scenario, dict) and target_payload_path is not None else None
        breakpoint = None
        if breakpoint_address is not None and breakpoint_source_offset is not None:
            raise MiError("Specify either a breakpoint address or a source offset, not both.")
        if breakpoint_source_offset is not None:
            if not target_detection or target_detection.get("status") != "pc_matched":
                raise MiError("A source-offset breakpoint requires a uniquely matched target payload checkpoint.")
            runtime_base = target_detection.get("runtime_base")
            if not isinstance(runtime_base, str):
                raise MiError("Target payload checkpoint has no runtime base.")
            breakpoint_address = int(runtime_base, 0) + breakpoint_source_offset
        if breakpoint_address is not None:
            gdb.command(f"-break-insert *0x{breakpoint_address:x}")
            gdb.command("-exec-continue")
            breakpoint_status = "hit"
            try:
                breakpoint_stop = gdb.wait_for_stop(breakpoint_wait_seconds)
            except MiTimeout:
                gdb.command("-exec-interrupt")
                breakpoint_stop = gdb.wait_for_stop()
                breakpoint_status = "timeout"
            breakpoint_pc = gdb.command("-data-evaluate-expression $pc")
            breakpoint_sp = gdb.command("-data-evaluate-expression $sp")
            breakpoint_sp_value = mi_value(breakpoint_sp)
            breakpoint_sp_address = int(breakpoint_sp_value, 0) if breakpoint_sp_value is not None else 0
            breakpoint_return_address = None
            if breakpoint_sp_address:
                with suppress(MiError):
                    breakpoint_return_address = f"0x{int.from_bytes(read_memory(gdb, breakpoint_sp_address, 4), 'big'):08x}"
            breakpoint = {
                "address": f"0x{breakpoint_address:08x}",
                "status": breakpoint_status,
                "stop_reason": mi_stop_reason(breakpoint_stop),
                "pc": mi_value(breakpoint_pc),
                "sp": breakpoint_sp_value,
                "stack_return_address": breakpoint_return_address,
            }
        gdb.command('-interpreter-exec console "kill"')
        return {
            "status": "ok",
            "continue_seconds": continue_seconds,
            "stop_reason": mi_stop_reason(stop),
            "pc": pc_value,
            "sp": mi_value(sp),
            "memory_pc": pc_memory,
            "memory_0xfc0000": mi_memory_bytes(memory),
            "observation_memory": observation_memory,
            "exec_state": exec_state,
            "active_execution": active_execution,
            "loadseg_watch": loader_watch,
            "scenario": scenario_result,
            "breakpoint": breakpoint,
        }
    finally:
        gdb.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gdb", required=True, type=Path)
    parser.add_argument("--ndk", required=True, type=Path)
    parser.add_argument("--continue-seconds", required=True, type=int)
    parser.add_argument("--loadseg-watch-seconds", type=int)
    parser.add_argument("--target-payload", type=Path)
    parser.add_argument("--breakpoint-address", type=lambda value: int(value, 0))
    parser.add_argument("--breakpoint-source-offset", type=lambda value: int(value, 0))
    parser.add_argument("--breakpoint-wait-seconds", type=int, default=60)
    parser.add_argument("--observation-memory-address", type=lambda value: int(value, 0))
    parser.add_argument("--observation-memory-equals", type=bytes.fromhex)
    parser.add_argument("--observation-memory-write-watch", action="store_true")
    parser.add_argument("--scenario", type=Path)
    args = parser.parse_args()
    if args.continue_seconds < 1 or args.continue_seconds > 120:
        parser.error("--continue-seconds must be between 1 and 120")
    if args.loadseg_watch_seconds is not None and not 1 <= args.loadseg_watch_seconds <= 120:
        parser.error("--loadseg-watch-seconds must be between 1 and 120")
    if not 1 <= args.breakpoint_wait_seconds <= 120:
        parser.error("--breakpoint-wait-seconds must be between 1 and 120")
    if args.observation_memory_address is not None and not 0 <= args.observation_memory_address <= 0xFFFFFF:
        parser.error("--observation-memory-address must be a 24-bit Amiga address")
    if args.observation_memory_equals is not None and len(args.observation_memory_equals) != 4:
        parser.error("--observation-memory-equals must contain exactly four bytes of hexadecimal data")
    if args.observation_memory_equals is not None and args.observation_memory_address is None:
        parser.error("--observation-memory-equals requires --observation-memory-address")
    try:
        result = run_session(args.gdb.resolve(), args.ndk.resolve(), args.continue_seconds, args.loadseg_watch_seconds, args.target_payload.resolve() if args.target_payload else None, args.breakpoint_address, args.breakpoint_source_offset, args.breakpoint_wait_seconds, args.observation_memory_address, args.observation_memory_equals, args.observation_memory_write_watch, args.scenario.resolve() if args.scenario else None)
    except MiError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
