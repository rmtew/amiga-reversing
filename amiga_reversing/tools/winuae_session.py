"""Run a bounded headless WinUAE observation and resolve its paused PC.

This is deliberately a read-only bridge between the project-owned headless
runner and the canonical listing.  It does not expose arbitrary GDB commands,
write target facts, or alter emulator input.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.disasm.c_backend import build_project_listing_artifact_profile
from amiga_reversing.disasm.project_paths import resolve_project_paths

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HEADLESS_RUNNER = ROOT / "tools" / "run_winuae_headless.ps1"


@dataclass(frozen=True, slots=True)
class HeadlessWinUaeSession:
    """The bounded, non-interactive WinUAE invocation used by this project."""

    rom_path: Path
    target_payload_path: Path
    runner_path: Path = DEFAULT_HEADLESS_RUNNER
    floppy0: Path | None = None
    state_directory: Path | None = None
    continue_seconds: int = 60
    breakpoint_wait_seconds: int = 60
    breakpoint_source_offset: int | None = None
    breakpoint_runtime_address: int | None = None

    def command(self) -> list[str]:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.runner_path),
            "-RomPath",
            str(self.rom_path),
            "-TargetPayloadPath",
            str(self.target_payload_path),
            "-ContinueSeconds",
            str(self.continue_seconds),
        ]
        if self.floppy0 is not None:
            command.extend(("-Floppy0", str(self.floppy0)))
        if self.state_directory is not None:
            command.extend(("-StateDirectory", str(self.state_directory)))
        if self.breakpoint_runtime_address is not None:
            command.extend((
                "-BreakpointAddress", f"0x{self.breakpoint_runtime_address:x}",
                "-BreakpointWaitSeconds", str(self.breakpoint_wait_seconds),
            ))
        elif self.breakpoint_source_offset is not None:
            command.extend((
                "-BreakpointSourceOffset", f"0x{self.breakpoint_source_offset:x}",
                "-BreakpointWaitSeconds", str(self.breakpoint_wait_seconds),
            ))
        return command


def command_line(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def _as_int(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def resolve_breakpoint_stable_key(target_id: str, stable_key: str) -> dict[str, object]:
    """Resolve and validate one canonical listing row for a runtime breakpoint."""

    match = re.fullmatch(r"s(?P<section>\d+):(?P<offset>[0-9A-Fa-f]{8}):.+", stable_key)
    if match is None:
        raise ValueError("Breakpoint stable key must use the canonical s<section>:<offset>:... form.")
    section_index = int(match.group("section"))
    source_offset = int(match.group("offset"), 16)
    _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        row = artifact.row_for_source_offset(section_index=section_index, offset=source_offset)
        observation_views = getattr(artifact, "_runtime_observation_views", ())
    finally:
        artifact.close()
    if row is None or row.get("stable_key") != stable_key:
        raise ValueError(f"Breakpoint stable key is not a current canonical row: {stable_key}")
    for view in observation_views:
        base_addr = view.get("base_addr") if isinstance(view, dict) else None
        source_start = view.get("source_start") if isinstance(view, dict) else None
        source_end = view.get("source_end") if isinstance(view, dict) else None
        if not all(isinstance(value, int) for value in (base_addr, source_start, source_end)):
            continue
        if source_start <= source_offset < source_end:
            row["runtime_observation_view"] = dict(view)
            row["runtime_breakpoint_address"] = base_addr + source_offset - source_start
            break
    return row


def resolve_breakpoint_hit(row: dict[str, object], runner_report: dict[str, object]) -> dict[str, object]:
    """Bind one temporary runtime breakpoint result back to its canonical row."""

    observation = runner_report.get("observation")
    breakpoint = observation.get("breakpoint") if isinstance(observation, dict) else None
    breakpoint_record = breakpoint if isinstance(breakpoint, dict) else {}
    active_execution = observation.get("active_execution") if isinstance(observation, dict) else None
    payload = active_execution.get("payload") if isinstance(active_execution, dict) else None
    runtime_base = _as_int(payload.get("runtime_base")) if isinstance(payload, dict) else None
    source_offset = row.get("start_offset")
    expected_address = row.get("runtime_breakpoint_address")
    if not isinstance(expected_address, int):
        expected_address = runtime_base + source_offset if isinstance(runtime_base, int) and isinstance(source_offset, int) else None
    hit_pc = _as_int(breakpoint_record.get("pc"))
    return {
        "status": "hit" if expected_address is not None and hit_pc == expected_address and breakpoint_record.get("status") == "hit" and breakpoint_record.get("stop_reason") == "breakpoint-hit" else "not_hit",
        "requested_row": {
            "stable_key": row["stable_key"],
            "section_index": row["section_index"],
            "source_offset": source_offset,
            "kind": row["kind"],
            "text": row["text"].strip(),
        },
        "expected_runtime_address": f"0x{expected_address:08x}" if expected_address is not None else None,
        "observation": breakpoint_record or None,
    }
def resolve_paused_pc(target_id: str, runner_report: dict[str, object]) -> dict[str, object]:
    """Resolve a runner JSON observation to a canonical listing row.

    A payload identity match is required before a PC can be treated as target
    evidence.  Mapping is read-only; an analyst must still choose whether to
    preserve a runtime observation view or alter analysis facts.
    """

    observation = runner_report.get("observation")
    if not isinstance(observation, dict):
        return {"status": "not_observed", "reason": "runner report has no persistent-session observation"}
    active_execution = observation.get("active_execution")
    payload = active_execution.get("payload") if isinstance(active_execution, dict) else None
    if not isinstance(payload, dict) or payload.get("status") not in {"pc_matched", "ambiguous"}:
        return {
            "status": "not_target_payload",
            "pc": observation.get("pc"),
            "payload": payload,
        }
    pc = _as_int(observation.get("pc"))
    if pc is None:
        return {"status": "invalid_observation", "reason": "persistent-session PC is missing or invalid"}

    _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        row = artifact.row_for_runtime_address(address=pc)
    finally:
        artifact.close()
    if row is None:
        return {
            "status": "unmapped_runtime_address",
            "target_id": target_id,
            "pc": f"0x{pc:08x}",
            "payload": payload,
        }
    payload_status = payload["status"]
    if payload_status == "ambiguous":
        view = row.get("runtime_observation_view")
        matching_offsets = payload.get("matching_offsets")
        if not isinstance(view, dict) or not isinstance(matching_offsets, list):
            return {
                "status": "not_target_payload",
                "pc": f"0x{pc:08x}",
                "payload": payload,
                "reason": "ambiguous payload sample has no confirmed runtime observation view",
            }
        base_addr = view.get("base_addr")
        source_start = view.get("source_start")
        if not isinstance(base_addr, int) or not isinstance(source_start, int):
            return {
                "status": "not_target_payload",
                "pc": f"0x{pc:08x}",
                "payload": payload,
                "reason": "runtime observation view has no usable address mapping",
            }
        expected_offset = pc - base_addr + source_start
        parsed_offsets = {_as_int(value) for value in matching_offsets}
        if expected_offset not in parsed_offsets:
            return {
                "status": "not_target_payload",
                "pc": f"0x{pc:08x}",
                "payload": payload,
                "reason": "ambiguous payload sample conflicts with the runtime observation view",
            }
    return {
        "status": "mapped" if payload_status == "pc_matched" else "mapped_with_runtime_view",
        "target_id": target_id,
        "pc": f"0x{pc:08x}",
        "payload": payload,
        "canonical_row": {
            "stable_key": row["stable_key"],
            "section_index": row["section_index"],
            "source_offset": row["start_offset"],
            "kind": row["kind"],
            "text": row["text"].strip(),
        },
        "runtime_observation_view": row.get("runtime_observation_view"),
    }


def run_session(session: HeadlessWinUaeSession) -> dict[str, object]:
    """Run the headless runner and return its JSON report without mutation."""

    completed = subprocess.run(session.command(), capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "headless WinUAE runner failed")
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("headless WinUAE runner did not return JSON") from exc
    if not isinstance(report, dict):
        raise RuntimeError("headless WinUAE runner returned a non-object JSON value")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument("--floppy0", type=Path)
    parser.add_argument("--continue-seconds", type=int, default=60, choices=range(1, 121))
    parser.add_argument(
        "--breakpoint-wait-seconds",
        type=int,
        default=60,
        choices=range(1, 121),
        help="bounded wait after the payload is confirmed and a breakpoint is armed",
    )
    parser.add_argument("--state-directory", type=Path)
    parser.add_argument("--runner", type=Path, default=DEFAULT_HEADLESS_RUNNER)
    parser.add_argument("--breakpoint-stable-key")
    parser.add_argument("--run", action="store_true", help="run the bounded session; otherwise print the launch plan")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = resolve_project_paths(args.target)
    breakpoint_row = resolve_breakpoint_stable_key(args.target, args.breakpoint_stable_key) if args.breakpoint_stable_key else None
    session = HeadlessWinUaeSession(
        rom_path=args.rom,
        floppy0=args.floppy0,
        target_payload_path=paths.binary_source.path,
        runner_path=args.runner,
        state_directory=args.state_directory,
        continue_seconds=args.continue_seconds,
        breakpoint_wait_seconds=args.breakpoint_wait_seconds,
        breakpoint_source_offset=breakpoint_row["start_offset"] if breakpoint_row is not None and "runtime_breakpoint_address" not in breakpoint_row else None,
        breakpoint_runtime_address=breakpoint_row.get("runtime_breakpoint_address") if breakpoint_row is not None else None,
    )
    if not args.run:
        print(json.dumps({"status": "planned", "target_id": args.target, "breakpoint_stable_key": args.breakpoint_stable_key, "command": session.command()}, indent=2))
        return 0
    report = run_session(session)
    result = {"runner": report, "pc_resolution": resolve_paused_pc(args.target, report)}
    if breakpoint_row is not None:
        result["breakpoint"] = resolve_breakpoint_hit(breakpoint_row, report)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
