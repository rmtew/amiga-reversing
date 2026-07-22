"""Bounded persistent GDB/MI session for the local headless WinUAE runner."""

from __future__ import annotations

import argparse
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
                raise MiError("Timed out waiting for GDB/MI response: " + " | ".join(transcript[-8:]))
            try:
                line = self._lines.get(timeout=remaining)
            except queue.Empty as exc:
                raise MiError("Timed out waiting for GDB/MI response.") from exc
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


def inspect_current_task(gdb: MiProcess, ndk: dict[str, object]) -> dict[str, object]:
    # ExecBase's absolute pointer is the Amiga Exec ABI's longword at address 4.
    exec_base = int.from_bytes(read_memory(gdb, 4, 4), "big")
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
    report: dict[str, object] = {
        "exec_base": f"0x{exec_base:08x}",
        "current_task": current,
    }
    for report_name, field_name in (("ready_tasks", "TaskReady"), ("waiting_tasks", "TaskWait")):
        list_address = exec_base + ndk_field_offset(ndk, "ExecBase", field_name)
        node_address = int.from_bytes(read_memory(gdb, list_address + list_head_offset, 4), "big")
        tail_sentinel = list_address + 4
        nodes: list[dict[str, object]] = []
        while node_address and node_address != tail_sentinel and len(nodes) < 32:
            node, node_address = inspect_node(gdb, node_address, node_type_offset, node_name_offset, known_types)
            nodes.append(node)
        report[report_name] = nodes
        report[f"{report_name}_truncated"] = bool(node_address and node_address != tail_sentinel)
    return report


def run_session(gdb_path: Path, ndk_path: Path, continue_seconds: int) -> dict[str, object]:
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
        current_task = inspect_current_task(gdb, ndk)
        gdb.command('-interpreter-exec console "kill"')
        return {
            "status": "ok",
            "continue_seconds": continue_seconds,
            "stop_reason": mi_stop_reason(stop),
            "pc": mi_value(pc),
            "sp": mi_value(sp),
            "memory_0xfc0000": mi_memory_bytes(memory),
            "current_task": current_task,
        }
    finally:
        gdb.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gdb", required=True, type=Path)
    parser.add_argument("--ndk", required=True, type=Path)
    parser.add_argument("--continue-seconds", required=True, type=int)
    args = parser.parse_args()
    if args.continue_seconds < 1 or args.continue_seconds > 120:
        parser.error("--continue-seconds must be between 1 and 120")
    try:
        result = run_session(args.gdb.resolve(), args.ndk.resolve(), args.continue_seconds)
    except MiError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
