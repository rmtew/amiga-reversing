"""Run bounded, declarative headless WinUAE observations and scenarios.

This is deliberately a read-only bridge between the project-owned headless
runner and the canonical listing.  It does not expose arbitrary GDB commands,
write target facts.  Scenario input is strictly declarative and is delivered
only through the pinned emulator's allow-listed virtual joystick bridge.
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
from amiga_reversing.tools.direct_payload_adapter import build_for_target, load_contract
from amiga_reversing.tools.gdb_symbols import generate_gdb_symbol_artifact

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HEADLESS_RUNNER = ROOT / "tools" / "run_winuae_headless.ps1"


@dataclass(frozen=True, slots=True)
class HeadlessWinUaeSession:
    """The bounded, non-interactive WinUAE invocation used by this project."""

    rom_path: Path
    target_payload_path: Path
    runner_path: Path = DEFAULT_HEADLESS_RUNNER
    floppy0: Path | None = None
    host_directory: Path | None = None
    state_directory: Path | None = None
    continue_seconds: int = 60
    breakpoint_wait_seconds: int = 60
    observation_memory_address: int | None = None
    observation_memory_equals: bytes | None = None
    observation_memory_write_watch: bool = False
    direct_payload_contract: str | None = None
    breakpoint_source_offset: int | None = None
    breakpoint_runtime_address: int | None = None
    scenario_path: Path | None = None

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
        if self.host_directory is not None:
            command.extend(("-HostDirectory", str(self.host_directory)))
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
        if self.observation_memory_address is not None:
            command.extend(("-ObservationMemoryAddress", f"0x{self.observation_memory_address:x}"))
        if self.observation_memory_equals is not None:
            command.extend(("-ObservationMemoryEquals", self.observation_memory_equals.hex()))
        if self.observation_memory_write_watch:
            command.append("-ObservationMemoryWriteWatch")
        if self.direct_payload_contract is not None:
            command.extend(("-DirectPayloadContract", self.direct_payload_contract))
        if self.scenario_path is not None:
            command.extend(("-ScenarioPath", str(self.scenario_path)))
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


def _resolve_breakpoint_stable_key_from_artifact(artifact: object, stable_key: str) -> dict[str, object]:
    """Resolve one canonical listing row using an already-open listing artifact."""
    match = re.fullmatch(r"s(?P<section>\d+):(?P<offset>[0-9A-Fa-f]{8}):.+", stable_key)
    if match is None:
        raise ValueError("Breakpoint stable key must use the canonical s<section>:<offset>:... form.")
    section_index = int(match.group("section"))
    source_offset = int(match.group("offset"), 16)
    row = artifact.row_for_source_offset(section_index=section_index, offset=source_offset)
    observation_views = getattr(artifact, "_runtime_observation_views", ())
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


def resolve_breakpoint_stable_key(target_id: str, stable_key: str) -> dict[str, object]:
    """Resolve and validate one canonical listing row for a runtime breakpoint."""

    _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        return _resolve_breakpoint_stable_key_from_artifact(artifact, stable_key)
    finally:
        artifact.close()


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


def compile_scenario(target_id: str, scenario_path: Path, output_path: Path, *, symbol_directory: Path | None = None) -> dict[str, object]:
    """Validate a target scenario and resolve only canonical source rows to PCs."""

    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    if not isinstance(scenario, dict) or scenario.get("schema_version") != 1:
        raise ValueError("Scenario must be a schema_version 1 JSON object.")
    if scenario.get("target_id") != target_id:
        raise ValueError("Scenario target_id does not match --target.")
    identifier = scenario.get("identifier")
    phases = scenario.get("phases")
    input_events = scenario.get("input_events", [])
    if not isinstance(identifier, str) or not identifier:
        raise ValueError("Scenario requires a non-empty identifier.")
    if not isinstance(phases, list) or len(phases) < 2:
        raise ValueError("Scenario requires boot handoff plus at least one canonical source-row phase.")
    if not isinstance(input_events, list):
        raise ValueError("Scenario input_events must be a list.")
    compiled_phases: list[dict[str, object]] = []
    names: set[str] = set()
    for index, phase in enumerate(phases):
        if not isinstance(phase, dict):
            raise ValueError("Scenario phase must be an object.")
        name = phase.get("name")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("Scenario phase names must be unique non-empty strings.")
        names.add(name)
        if index == 0:
            if phase.get("observable") != "direct_payload_handoff":
                raise ValueError("The first scenario phase must be the direct_payload_handoff observable.")
            continue
        stable_key = phase.get("breakpoint_stable_key")
        wait_seconds = phase.get("wait_seconds")
        transition = phase.get("transition", "continue")
        capture = phase.get("capture", {})
        if not isinstance(stable_key, str) or not isinstance(wait_seconds, int) or not 1 <= wait_seconds <= 120:
            raise ValueError("Source-row scenario phases require breakpoint_stable_key and wait_seconds (1..120).")
        if not isinstance(capture, dict):
            raise ValueError("Scenario phase capture must be an object.")
        if transition not in {"continue", "enter_function"}:
            raise ValueError("Scenario phase transition must be continue or enter_function.")
        compiled_phases.append({"name": name, "stable_key": stable_key, "wait_seconds": wait_seconds, "transition": transition, "capture": capture})
    phase_indexes = {str(phase["name"]): index for index, phase in enumerate(compiled_phases)}
    compiled_events: list[dict[str, object]] = []
    for event in input_events:
        if not isinstance(event, dict):
            raise ValueError("Scenario input event must be an object.")
        after_phase = event.get("after_phase")
        release_after_phase = event.get("release_after_phase")
        control = event.get("control")
        if after_phase not in phase_indexes:
            raise ValueError("Scenario input must be scheduled after a named source-row phase.")
        if release_after_phase not in phase_indexes or phase_indexes[release_after_phase] <= phase_indexes[after_phase]:
            raise ValueError("Scenario input release_after_phase must be a later named source-row phase.")
        if control not in {f"port{port} {direction}" for port in range(2) for direction in ("fire", "left", "right", "up", "down")}:
            raise ValueError("Scenario input control is not supported by the virtual joystick bridge.")
        compiled_events.append({"after_phase": after_phase, "release_after_phase": release_after_phase, "control": control})
    _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        for phase in compiled_phases:
            row = _resolve_breakpoint_stable_key_from_artifact(artifact, str(phase["stable_key"]))
            address = row.get("runtime_breakpoint_address")
            if not isinstance(address, int):
                raise ValueError(f"Scenario phase {phase['name']} has no reviewed runtime observation mapping: {phase['stable_key']}")
            phase["breakpoint_address"] = address
        symbols = (
            generate_gdb_symbol_artifact(target_id, symbol_directory, artifact=artifact).scenario_payload()
            if symbol_directory is not None
            else None
        )
    finally:
        artifact.close()
    compiled = {"schema_version": 1, "identifier": identifier, "phases": compiled_phases, "input_events": compiled_events}
    if symbols is not None:
        compiled["symbols"] = symbols
    output_path.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
    return compiled
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
    parser.add_argument("--host-directory", type=Path, help="host directory mounted as PAYLOAD:")
    parser.add_argument("--direct-payload-contract", help="validated contract used to build and boot a direct payload ADF")
    parser.add_argument("--scenario", type=Path, help="declarative runtime scenario executed after direct-payload handoff")
    parser.add_argument("--continue-seconds", type=int, default=60, choices=range(1, 121))
    parser.add_argument(
        "--breakpoint-wait-seconds",
        type=int,
        default=60,
        choices=range(1, 121),
        help="bounded wait after the payload is confirmed and a breakpoint is armed",
    )
    parser.add_argument(
        "--observation-memory-write-watch",
        action="store_true",
        help="stop on the first write to the observed diagnostic longword",
    )
    parser.add_argument(
        "--observation-memory-equals",
        help="stop early when the observed diagnostic longword equals this eight-hex-digit value",
    )
    parser.add_argument("--state-directory", type=Path)
    parser.add_argument(
        "--observation-memory-address",
        type=lambda value: int(value, 0),
        help="read one diagnostic longword from emulated memory after the bounded pause",
    )
    parser.add_argument("--runner", type=Path, default=DEFAULT_HEADLESS_RUNNER)
    parser.add_argument("--breakpoint-stable-key")
    parser.add_argument("--run", action="store_true", help="run the bounded session; otherwise print the launch plan")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    observation_memory_equals = bytes.fromhex(args.observation_memory_equals) if args.observation_memory_equals else None
    if observation_memory_equals is not None and len(observation_memory_equals) != 4:
        raise ValueError("--observation-memory-equals must contain exactly four bytes of hexadecimal data.")
    if observation_memory_equals is not None and args.observation_memory_address is None:
        raise ValueError("--observation-memory-equals requires --observation-memory-address.")
    if args.observation_memory_write_watch and args.observation_memory_address is None:
        raise ValueError("--observation-memory-write-watch requires --observation-memory-address.")
    if args.direct_payload_contract and (args.floppy0 or args.host_directory):
        raise ValueError("--direct-payload-contract cannot be combined with --floppy0 or --host-directory.")
    if args.direct_payload_contract and args.state_directory is None:
        raise ValueError("--direct-payload-contract requires --state-directory for its generated ADF.")
    if args.scenario and not args.direct_payload_contract:
        raise ValueError("--scenario requires --direct-payload-contract so input cannot run before a verified handoff.")
    paths = resolve_project_paths(args.target)
    direct_payload = None
    floppy0 = args.floppy0
    observation_memory_address = args.observation_memory_address
    observation_memory_equals = observation_memory_equals
    observation_memory_write_watch = args.observation_memory_write_watch
    direct_payload_contract = None
    if args.direct_payload_contract:
        contract = load_contract(args.direct_payload_contract)
        output = args.state_directory / f"direct-payload-{contract.identifier}.adf"
        direct_payload = build_for_target(contract.identifier, args.target, output)
        floppy0 = output
        observation_memory_address = contract.handoff_marker_address
        observation_memory_equals = contract.handoff_marker_value.to_bytes(4, "big")
        observation_memory_write_watch = True
        direct_payload_contract = contract.identifier
    compiled_scenario = None
    scenario_output = None
    if args.scenario:
        scenario_output = args.state_directory / "runtime-scenario.json"
        compiled_scenario = compile_scenario(args.target, args.scenario, scenario_output, symbol_directory=args.state_directory)
    breakpoint_row = resolve_breakpoint_stable_key(args.target, args.breakpoint_stable_key) if args.breakpoint_stable_key else None
    session = HeadlessWinUaeSession(
        rom_path=args.rom,
        floppy0=floppy0,
        host_directory=args.host_directory,
        target_payload_path=paths.binary_source.path,
        runner_path=args.runner,
        state_directory=args.state_directory,
        continue_seconds=args.continue_seconds,
        breakpoint_wait_seconds=args.breakpoint_wait_seconds,
        observation_memory_address=observation_memory_address,
        observation_memory_equals=observation_memory_equals,
        observation_memory_write_watch=observation_memory_write_watch,
        direct_payload_contract=direct_payload_contract,
        breakpoint_source_offset=breakpoint_row["start_offset"] if breakpoint_row is not None and "runtime_breakpoint_address" not in breakpoint_row else None,
        breakpoint_runtime_address=breakpoint_row.get("runtime_breakpoint_address") if breakpoint_row is not None else None,
        scenario_path=scenario_output,
    )
    if not args.run:
        print(json.dumps({"status": "planned", "target_id": args.target, "direct_payload": direct_payload, "scenario": compiled_scenario, "breakpoint_stable_key": args.breakpoint_stable_key, "command": session.command()}, indent=2))
        return 0
    report = run_session(session)
    scenario_summary = None
    if isinstance(compiled_scenario, dict):
        symbols = compiled_scenario.get("symbols")
        scenario_summary = {
            "identifier": compiled_scenario.get("identifier"),
            "symbol_artifact": symbols.get("elf_path") if isinstance(symbols, dict) else None,
        }
    result = {"runner": report, "direct_payload": direct_payload, "scenario": scenario_summary, "pc_resolution": resolve_paused_pc(args.target, report)}
    if breakpoint_row is not None:
        result["breakpoint"] = resolve_breakpoint_hit(breakpoint_row, report)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
