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


def run_session(gdb_path: Path, ndk_path: Path, continue_seconds: int, loadseg_watch_seconds: int | None, target_payload_path: Path | None) -> dict[str, object]:
    ndk = json.loads(ndk_path.read_text(encoding="utf-8"))
    gdb = MiProcess(gdb_path)
    try:
        gdb.command("-gdb-set pagination off")
        gdb.command("-gdb-set confirm off")
        gdb.command("-gdb-set mi-async on")
        gdb.command("-target-select remote 127.0.0.1:2345")
        gdb.command("-exec-continue")
        time.sleep(continue_seconds)
        gdb.command("-exec-interrupt")
        stop = gdb.wait_for_stop()
        pc = gdb.command("-data-evaluate-expression $pc")
        sp = gdb.command("-data-evaluate-expression $sp")
        memory = gdb.command("-data-read-memory-bytes 0xfc0000 8")
        pc_value = mi_value(pc)
        pc_address = int(pc_value, 0) if pc_value is not None else 0
        pc_memory_bytes = read_memory(gdb, pc_address, 16) if pc_address else b""
        pc_memory = pc_memory_bytes.hex() if pc_memory_bytes else None
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
        gdb.command('-interpreter-exec console "kill"')
        return {
            "status": "ok",
            "continue_seconds": continue_seconds,
            "stop_reason": mi_stop_reason(stop),
            "pc": pc_value,
            "sp": mi_value(sp),
            "memory_pc": pc_memory,
            "memory_0xfc0000": mi_memory_bytes(memory),
            "exec_state": exec_state,
            "active_execution": active_execution,
            "loadseg_watch": loader_watch,
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
    args = parser.parse_args()
    if args.continue_seconds < 1 or args.continue_seconds > 120:
        parser.error("--continue-seconds must be between 1 and 120")
    if args.loadseg_watch_seconds is not None and not 1 <= args.loadseg_watch_seconds <= 120:
        parser.error("--loadseg-watch-seconds must be between 1 and 120")
    try:
        result = run_session(args.gdb.resolve(), args.ndk.resolve(), args.continue_seconds, args.loadseg_watch_seconds, args.target_payload.resolve() if args.target_payload else None)
    except MiError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
