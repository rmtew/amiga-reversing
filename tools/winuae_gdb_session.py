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


def run_session(gdb_path: Path, continue_seconds: int) -> dict[str, object]:
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
        gdb.command('-interpreter-exec console "kill"')
        return {
            "status": "ok",
            "continue_seconds": continue_seconds,
            "stop_reason": mi_stop_reason(stop),
            "pc": mi_value(pc),
            "sp": mi_value(sp),
            "memory_0xfc0000": mi_memory_bytes(memory),
        }
    finally:
        gdb.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gdb", required=True, type=Path)
    parser.add_argument("--continue-seconds", required=True, type=int)
    args = parser.parse_args()
    if args.continue_seconds < 1 or args.continue_seconds > 120:
        parser.error("--continue-seconds must be between 1 and 120")
    try:
        result = run_session(args.gdb.resolve(), args.continue_seconds)
    except MiError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
