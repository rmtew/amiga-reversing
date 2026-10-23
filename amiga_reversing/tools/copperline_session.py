"""Run bounded, declarative headless Copperline observations and scenarios.

This is deliberately a read-only bridge between the project-owned headless
runner and the canonical listing.  It does not expose arbitrary control commands or
write target facts.  Scenario input is strictly declarative and is delivered
only through the native control protocol's allow-listed joystick interface.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.tools.runtime_analysis import build_project_listing_artifact_profile, analysis_scope
from amiga_reversing.tools.copperline_bus_trace import validate_bus_trace
from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.tools.copperline_runtime import (
    MAX_SCENARIO_PHASES, MAX_SCENARIO_INPUT_EVENTS, validate_phase_occurrences, observe, validate_memory_expectation, validate_custom_registers,
    validate_memory_access_watch, validate_phase_frame_budget, validate_memory_goal,
)
from amiga_reversing.tools.direct_payload_adapter import build_for_target, load_contract
from amiga_reversing.tools.runtime_symbols import generate_runtime_symbol_artifact

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class HeadlessCopperlineSession:
    """The bounded, non-interactive Copperline invocation used by this project."""

    rom_path: Path
    target_payload_path: Path
    binary_path: Path
    floppy0: Path | None = None
    host_directory: Path | None = None
    state_directory: Path | None = None
    loadseg_watch_seconds: int | None = None
    continue_seconds: int = 60
    breakpoint_wait_seconds: int = 60
    observation_memory_address: int | None = None
    observation_memory_equals: bytes | None = None
    observation_memory_write_watch: bool = False
    direct_payload_contract: str | None = None
    breakpoint_expected_source_offset: int | None = None
    breakpoint_source_offset: int | None = None
    breakpoint_runtime_address: int | None = None
    derived_artifact_manifest: Path | None = None
    scenario_path: Path | None = None
    checkpoint_save: Path | None = None
    checkpoint_load: Path | None = None

    def plan(self) -> dict[str, object]:
        return {
            "emulator": "copperline 1.0.0",
            "binary": str(self.binary_path),
            "rom": str(self.rom_path),
            "profile": "A500OCS PAL 68000 512K chip + 512K slow",
            "floppy0": str(self.floppy0) if self.floppy0 else None,
            "host_directory": str(self.host_directory) if self.host_directory else None,
            "continue_seconds": self.continue_seconds,
            "breakpoint_wait_seconds": self.breakpoint_wait_seconds,
            "derived_artifact_manifest": str(self.derived_artifact_manifest)
            if self.derived_artifact_manifest
            else None,
            "direct_payload_contract": self.direct_payload_contract,
            "checkpoint_save": str(self.checkpoint_save) if self.checkpoint_save else None,
            "checkpoint_load": str(self.checkpoint_load) if self.checkpoint_load else None,
        }


def _as_int(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def _resolve_breakpoint_stable_key_from_artifact(
    artifact: object, stable_key: str
) -> dict[str, object]:
    """Resolve one canonical listing row using an already-open listing artifact."""
    match = re.fullmatch(r"s(?P<section>\d+):(?P<offset>[0-9A-Fa-f]{8}):.+", stable_key)
    if match is None:
        raise ValueError(
            "Breakpoint stable key must use the canonical s<section>:<offset>:... form."
        )
    section_index = int(match.group("section"))
    source_offset = int(match.group("offset"), 16)
    row = artifact.row_for_source_offset(
        section_index=section_index, offset=source_offset
    )
    observation_views = getattr(artifact, "_runtime_observation_views", ())
    if row is None or row.get("stable_key") != stable_key:
        raise ValueError(
            f"Breakpoint stable key is not a current canonical row: {stable_key}"
        )
    matches = []
    for view in observation_views:
        base_addr = view.get("base_addr") if isinstance(view, dict) else None
        source_start = view.get("source_start") if isinstance(view, dict) else None
        source_end = view.get("source_end") if isinstance(view, dict) else None
        if not all(
            isinstance(value, int) for value in (base_addr, source_start, source_end)
        ):
            continue
        if (
            view.get("section_index", 0) == section_index
            and source_start <= source_offset < source_end
        ):
            matches.append((view, base_addr + source_offset - source_start))
    if len(matches) > 1:
        raise ValueError("Ambiguous runtime observation mappings for stable key")
    if matches:
        row = dict(
            row,
            runtime_observation_view=dict(matches[0][0]),
            runtime_breakpoint_address=matches[0][1],
        )
    return row


def resolve_breakpoint_stable_key(target_id: str, stable_key: str) -> dict[str, object]:
    """Resolve and validate one canonical listing row for a runtime breakpoint."""

    _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        return _resolve_breakpoint_stable_key_from_artifact(artifact, stable_key)
    finally:
        artifact.close()


def resolve_breakpoint_hit(
    row: dict[str, object], runner_report: dict[str, object]
) -> dict[str, object]:
    """Bind one temporary runtime breakpoint result back to its canonical row."""

    observation = runner_report.get("observation")
    breakpoint = (
        observation.get("breakpoint") if isinstance(observation, dict) else None
    )
    breakpoint_record = breakpoint if isinstance(breakpoint, dict) else {}
    active_execution = (
        observation.get("active_execution") if isinstance(observation, dict) else None
    )
    payload = (
        active_execution.get("payload") if isinstance(active_execution, dict) else None
    )
    runtime_base = (
        _as_int(payload.get("runtime_base")) if isinstance(payload, dict) else None
    )
    source_offset = row.get("start_offset")
    expected_address = row.get("runtime_breakpoint_address")
    if not isinstance(expected_address, int):
        expected_address = (
            runtime_base + source_offset
            if isinstance(runtime_base, int) and isinstance(source_offset, int)
            else None
        )
    hit_pc = _as_int(breakpoint_record.get("pc"))
    return {
        "status": "hit"
        if expected_address is not None
        and hit_pc == expected_address
        and breakpoint_record.get("status") == "hit"
        and breakpoint_record.get("stop_reason") == "breakpoint-hit"
        else "not_hit",
        "requested_row": {
            "stable_key": row["stable_key"],
            "section_index": row["section_index"],
            "source_offset": source_offset,
            "kind": row["kind"],
            "text": row["text"].strip(),
        },
        "expected_runtime_address": f"0x{expected_address:08x}"
        if expected_address is not None
        else None,
        "observation": breakpoint_record or None,
    }


def compile_scenario(
    target_id: str,
    scenario_path: Path,
    output_path: Path,
    *,
    symbol_directory: Path | None = None,
    derived_manifest: Path | None = None,
) -> dict[str, object]:
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
    if not isinstance(phases, list) or not 2 <= len(phases) <= MAX_SCENARIO_PHASES:
        raise ValueError(
            f"Scenario requires boot handoff plus canonical source-row phases (2..{MAX_SCENARIO_PHASES} total)."
        )
    if not isinstance(input_events, list) or len(input_events) > MAX_SCENARIO_INPUT_EVENTS:
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
            if "memory_access_watch" in phase:
                raise ValueError("Memory access watch requires a canonical source-row phase.")
            if 'chip_bus_trace' in phase:
                raise ValueError('Chip-bus trace requires a canonical source-row phase.')
            if "occurrences" in phase or "capture_first" in phase:
                raise ValueError(
                    "Occurrence capture requires a canonical source-row phase."
                )
            if phase.get("observable") not in {"direct_payload_handoff", "verified_checkpoint"}:
                raise ValueError(
                    "The first scenario phase must be direct_payload_handoff or verified_checkpoint."
                )
            continue
        stable_key = phase.get("breakpoint_stable_key")
        wait_seconds = phase.get("wait_seconds")
        transition = phase.get("transition", "continue")
        capture = phase.get("capture", {})
        occurrences = phase.get("occurrences", 1)
        capture_first = phase.get("capture_first", False)
        validate_phase_occurrences(phase)
        if type(capture_first) is not bool:
            raise ValueError("Scenario capture_first must be boolean.")
        if (
            not isinstance(stable_key, str)
            or not isinstance(wait_seconds, int)
            or not 1 <= wait_seconds <= 120
        ):
            raise ValueError(
                "Source-row scenario phases require breakpoint_stable_key and wait_seconds (1..120)."
            )
        validate_capture(capture)
        if "max_frames" in phase:
            if index == 1:
                raise ValueError("Phase frame budget needs a preceding source-row anchor")
            validate_phase_frame_budget(phase["max_frames"])
        if "until_memory" in phase:
            validate_memory_goal(phase["until_memory"])
            if "max_frames" not in phase or "occurrences" not in phase:
                raise ValueError("Memory goal requires explicit frame and visit budgets")
        if "memory_access_watch" in phase:
            validate_memory_access_watch(phase["memory_access_watch"])
        if 'chip_bus_trace' in phase:
            validate_bus_trace(phase['chip_bus_trace'])
            if 'memory_access_watch' in phase:
                raise ValueError('Chip-bus trace requires its own canonical source-row phase')
        if transition not in {"continue", "enter_function"}:
            raise ValueError(
                "Scenario phase transition must be continue or enter_function."
            )
        compiled_phases.append(
            {
                "name": name,
                "stable_key": stable_key,
                "wait_seconds": wait_seconds,
                "transition": transition,
                "capture": capture,
                **({"max_frames": phase["max_frames"]} if "max_frames" in phase else {}),
                **({"until_memory": dict(phase["until_memory"])} if "until_memory" in phase else {}),
                **({"memory_access_watch": dict(phase["memory_access_watch"])}
                   if "memory_access_watch" in phase else {}),
                **({'chip_bus_trace': dict(phase['chip_bus_trace'])}
                   if 'chip_bus_trace' in phase else {}),
                **({"occurrences": occurrences} if "occurrences" in phase else {}),
                **(
                    {"capture_first": capture_first} if "capture_first" in phase else {}
                ),
            }
        )
    phase_indexes = {
        str(phase["name"]): index for index, phase in enumerate(compiled_phases)
    }
    compiled_events: list[dict[str, object]] = []
    for event in input_events:
        if not isinstance(event, dict):
            raise ValueError("Scenario input event must be an object.")
        after_phase = event.get("after_phase")
        release_after_phase = event.get("release_after_phase")
        control = event.get("control")
        if after_phase not in phase_indexes:
            raise ValueError(
                "Scenario input must be scheduled after a named source-row phase."
            )
        if (
            release_after_phase not in phase_indexes
            or phase_indexes[release_after_phase] <= phase_indexes[after_phase]
        ):
            raise ValueError(
                "Scenario input release_after_phase must be a later named source-row phase."
            )
        if set(event) - {"after_phase", "release_after_phase", "control"}:
            raise ValueError(
                "Scenario input has unsupported fields; use phase-bounded press/release."
            )
        if control not in {
            f"port{port} {direction}"
            for port in range(2)
            for direction in ("fire", "left", "right", "up", "down")
        } and (
            not isinstance(control, str)
            or not re.fullmatch(r"key (?:[0-9]|[1-9][0-9]|1[01][0-9]|12[0-7])", control)
        ):
            raise ValueError(
                "Scenario input requires a joystick control or key 0..127."
            )
        compiled_events.append(
            {
                "after_phase": after_phase,
                "release_after_phase": release_after_phase,
                "control": control,
            }
        )
    _, _, artifact = build_project_listing_artifact_profile(target_id)
    excluded_ranges = ()
    try:
        needs_regions = derived_manifest is not None or any(
            "region_id" in r
            for p in compiled_phases
            for r in p["capture"].get("memory_reads", [])
        )
        placements = (
            {
                r["region_id"]: (r["runtime_address"], r["size"])
                for r in artifact.memory_regions_payload()["items"]
            }
            if needs_regions
            else {}
        )
        if derived_manifest is not None:
            from amiga_reversing.disasm.derived_artifact import (
                validate_manifest,
                verify_native_binding,
            )

            manifest, _ = validate_manifest(derived_manifest, target_id)
            verify_native_binding(manifest, artifact)
            if manifest.get('kind') == 'fixed_size_optional_patch':
                from amiga_reversing.tools.optional_patch import anchor_offset
                excluded_ranges = tuple((anchor_offset(p['start']), anchor_offset(p['end']))
                                        for p in manifest['patches'])
            else:
                placements[manifest["region"]["region_id"]] = (
                    manifest["placement"]["runtime_address"],
                    manifest["region"]["size"],
                )
        for phase in compiled_phases:
            for read in phase["capture"].get("memory_reads", []):
                if "region_id" in read:
                    placement = placements.get(read["region_id"])
                    if (
                        placement is None
                        or read.get("offset", 0) + read["size"] > placement[1]
                    ):
                        raise ValueError(
                            "Capture region is unknown or read exceeds its extent"
                        )
                    read["address"] = placement[0] + read.get("offset", 0)
                    del read["region_id"]
                    read.pop("offset", None)
            row = _resolve_breakpoint_stable_key_from_artifact(
                artifact, str(phase["stable_key"])
            )
            if any(start <= row['start_offset'] < end for start, end in excluded_ranges):
                raise ValueError('Scenario anchor lies inside an optional patch; original instruction mapping is invalid')
            address = row.get("runtime_breakpoint_address")
            if not isinstance(address, int):
                raise ValueError(
                    f"Scenario phase {phase['name']} has no reviewed runtime observation mapping: {phase['stable_key']}"
                )
            phase["breakpoint_address"] = address
            phase["source_offset"] = row["start_offset"]
            phase["runtime_view"] = row["runtime_observation_view"]
        symbols = (
            generate_runtime_symbol_artifact(
                target_id, symbol_directory, artifact=artifact,
                **({'excluded_ranges': excluded_ranges} if excluded_ranges else {}),
            )
            if symbol_directory is not None
            else None
        )
    finally:
        artifact.close()
    compiled = {
        "schema_version": 1,
        "identifier": identifier,
        "target_id": target_id,
        "direct_payload_contract": scenario.get("direct_payload_contract"),
        "start_observable": phases[0]["observable"],
        "phases": compiled_phases,
        "input_events": compiled_events,
    }
    if symbols is not None:
        compiled["symbols"] = symbols
    for phase in compiled_phases:
        if phase["transition"] == "enter_function":
            eligible = symbols.get("functions", []) if symbols else []
            if not any(
                f["runtime_start"] == phase["breakpoint_address"]
                and f["source_start"] == phase["source_offset"]
                for f in eligible
            ):
                raise ValueError(
                    f"Phase {phase['name']} requires an accepted exact function entry."
                )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
    return compiled


def resolve_paused_pc(
    target_id: str, runner_report: dict[str, object], *, derived_manifest: Path | None = None
) -> dict[str, object]:
    """Resolve a runner JSON observation to a canonical listing row.

    A payload identity match is required before a PC can be treated as target
    evidence.  Mapping is read-only; an analyst must still choose whether to
    preserve a runtime observation view or alter analysis facts.
    """

    observation = runner_report.get("observation")
    if not isinstance(observation, dict):
        return {
            "status": "not_observed",
            "reason": "runner report has no persistent-session observation",
        }
    active_execution = observation.get("active_execution")
    payload = (
        active_execution.get("payload") if isinstance(active_execution, dict) else None
    )
    if not isinstance(payload, dict) or payload.get("status") not in {
        "pc_matched",
        "ambiguous",
    }:
        return {
            "status": "not_target_payload",
            "pc": observation.get("pc"),
            "payload": payload,
        }
    pc = _as_int(observation.get("pc"))
    if pc is None:
        return {
            "status": "invalid_observation",
            "reason": "persistent-session PC is missing or invalid",
        }

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
    if derived_manifest is not None:
        from amiga_reversing.disasm.derived_artifact import validate_manifest
        from amiga_reversing.disasm.optional_artifact import overlaps
        manifest, _ = validate_manifest(derived_manifest, target_id)
        if manifest.get('kind') == 'fixed_size_optional_patch' and overlaps(
                manifest, row['start_offset'], row['start_offset'] + 1):
            return {'status': 'modified_instruction_range', 'pc': f'0x{pc:08x}',
                    'payload': payload, 'reason': 'Original instruction mapping is invalid inside an optional patch'}
    payload_status = payload["status"]
    if payload_status == "pc_matched":
        matched_offset = _as_int(payload.get("payload_offset"))
        matched_base = _as_int(payload.get("runtime_base"))
        if (
            matched_offset != row.get("start_offset")
            or matched_base is None
            or matched_base + matched_offset != pc
        ):
            return {
                "status": "not_target_payload",
                "pc": f"0x{pc:08x}",
                "payload": payload,
                "reason": "unique payload match conflicts with the canonical runtime row",
            }
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
        "status": "mapped"
        if payload_status == "pc_matched"
        else "mapped_with_runtime_view",
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


def run_session(session: HeadlessCopperlineSession) -> dict[str, object]:
    """Run the headless runner and return its JSON report without mutation."""

    return observe(session)


def resolve_binary(explicit: Path | None) -> Path:
    from amiga_reversing.disasm.tool_graph import runtime_tool_record

    candidate = explicit or os.environ.get("COPPERLINE_BINARY")
    if not candidate:
        candidate = runtime_tool_record("copperline").get(
            "resolved_path"
        ) or shutil.which("copperline")
    if not candidate or not Path(candidate).is_file():
        raise ValueError(
            "Provide Copperline 1.0.0 with --copperline, COPPERLINE_BINARY or tool registry."
        )
    return Path(candidate).resolve()


def validate_capture(capture: object) -> None:
    if not isinstance(capture, dict) or set(capture) - {"registers", "memory_reads", "custom_registers"}:
        raise ValueError("Scenario capture supports only registers, memory_reads and custom_registers.")
    custom = capture.get("custom_registers", [])
    validate_custom_registers(custom)
    registers, reads = capture.get("registers", []), capture.get("memory_reads", [])
    allowed = {f"{kind}{i}" for kind in ("a", "d") for i in range(8)} | {"sr"}
    if (
        not isinstance(registers, list)
        or len(registers) > 17
        or any(not isinstance(r, str) or r not in allowed for r in registers)
    ):
        raise ValueError("Capture registers must be d0..d7, a0..a7 or sr (maximum 17).")
    if not isinstance(reads, list) or len(reads) > 16:
        raise ValueError("Capture supports at most 16 memory reads.")
    for read in reads:
        if not isinstance(read, dict) or set(read) - {
            "address",
            "base_register",
            "region_id",
            "offset",
            "size",
            "expect_hex",
            "expect_mask_hex",
        }:
            raise ValueError("Invalid capture memory read.")
        size = read.get("size")
        if type(size) is not int or not 1 <= size <= 64:
            raise ValueError("Capture memory size must be 1..64.")
        validate_memory_expectation(read)
        if "region_id" in read:
            if (
                not isinstance(read["region_id"], str)
                or not read["region_id"]
                or "address" in read
                or "base_register" in read
                or type(read.get("offset", 0)) is not int
                or read.get("offset", 0) < 0
            ):
                raise ValueError(
                    "Capture requires a stable region identifier and nonnegative offset"
                )
        elif "address" in read:
            address = read["address"]
            if (
                "base_register" in read
                or "offset" in read
                or type(address) is not int
                or not 0 <= address <= 0x1000000 - size
            ):
                raise ValueError(
                    "Capture absolute address is outside 24-bit memory or conflicts with register addressing."
                )
        elif (
            read.get("base_register") not in {f"a{i}" for i in range(8)}
            or type(read.get("offset", 0)) is not int
            or not -0x1000000 < read.get("offset", 0) < 0x1000000
        ):
            raise ValueError(
                "Capture requires an absolute address or bounded a0..a7 relative address."
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--derived-artifact",
        type=Path,
        help="Validated fixed-width relocation manifest or explicit optional-patch receipt",
    )
    parser.add_argument("--target", required=True)
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument("--floppy0", type=Path)
    parser.add_argument(
        "--host-directory", type=Path, help="read-only host directory mounted as DH0:"
    )
    parser.add_argument(
        "--direct-payload-contract",
        help="validated contract used to build and boot a direct payload ADF",
    )
    parser.add_argument(
        "--scenario",
        type=Path,
        help="declarative runtime scenario executed after direct-payload handoff",
    )
    parser.add_argument("--loadseg-watch-seconds", type=int, choices=range(1, 121))
    parser.add_argument(
        "--continue-seconds", type=int, default=60, choices=range(1, 121)
    )
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
    parser.add_argument("--checkpoint-save", type=Path, help="Save a local verified checkpoint receipt after a completed scenario")
    parser.add_argument("--checkpoint-load", type=Path, help="Resume a content-bound local checkpoint at its canonical PC")
    parser.add_argument(
        "--observation-memory-address",
        type=lambda value: int(value, 0),
        help="read one diagnostic longword from emulated memory after the bounded pause",
    )
    parser.add_argument(
        "--copperline",
        type=Path,
        help="Copperline 1.0.0 executable (or COPPERLINE_BINARY / configured runtime / PATH)",
    )
    parser.add_argument("--breakpoint-stable-key")
    parser.add_argument(
        "--run",
        action="store_true",
        help="run the bounded session; otherwise print the launch plan",
    )
    return parser


def _main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    observation_memory_equals = (
        bytes.fromhex(args.observation_memory_equals)
        if args.observation_memory_equals
        else None
    )
    if observation_memory_equals is not None and len(observation_memory_equals) != 4:
        raise ValueError(
            "--observation-memory-equals must contain exactly four bytes of hexadecimal data."
        )
    if (
        observation_memory_equals is not None
        and args.observation_memory_address is None
    ):
        raise ValueError(
            "--observation-memory-equals requires --observation-memory-address."
        )
    if args.observation_memory_write_watch and args.observation_memory_address is None:
        raise ValueError(
            "--observation-memory-write-watch requires --observation-memory-address."
        )
    if args.direct_payload_contract and (args.floppy0 or args.host_directory):
        raise ValueError(
            "--direct-payload-contract cannot be combined with --floppy0 or --host-directory."
        )
    if args.direct_payload_contract and args.state_directory is None:
        raise ValueError(
            "--direct-payload-contract requires --state-directory for its generated ADF."
        )
    if (
        args.observation_memory_address is not None
        and not 0 <= args.observation_memory_address <= 0xFFFFFC
    ):
        raise ValueError("Observation address must fit the 24-bit memory space.")
    if args.loadseg_watch_seconds and (args.scenario or args.breakpoint_stable_key):
        raise ValueError("LoadSeg watching requires a standalone observation.")
    if args.scenario and args.breakpoint_stable_key:
        raise ValueError("Choose a scenario or a single breakpoint, not both.")
    if args.scenario and not args.direct_payload_contract:
        raise ValueError(
            "--scenario requires --direct-payload-contract so input cannot run before a verified handoff."
        )
    if (args.checkpoint_save or args.checkpoint_load) and (
        not args.scenario or not args.direct_payload_contract or args.loadseg_watch_seconds
    ):
        raise ValueError("Checkpoints require a direct-payload scenario without LoadSeg watching")
    if args.derived_artifact and not args.direct_payload_contract:
        raise ValueError(
            "--derived-artifact requires a verified direct-payload contract"
        )
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
        direct_payload = build_for_target(
            contract.identifier,
            args.target,
            output,
            derived_manifest=args.derived_artifact,
        )
        floppy0 = output
        observation_memory_address = contract.handoff_marker_address
        observation_memory_equals = contract.handoff_marker_value.to_bytes(4, "big")
        observation_memory_write_watch = True
        direct_payload_contract = contract.identifier
        if direct_payload.get('optional_patches') and not args.scenario:
            raise ValueError('Optional patched runtime artifacts require a canonical scenario')
    compiled_scenario = None
    scenario_output = None
    if args.scenario:
        scenario_output = args.state_directory / "runtime-scenario.json"
        compiled_scenario = compile_scenario(
            args.target,
            args.scenario,
            scenario_output,
            symbol_directory=args.state_directory,
            derived_manifest=args.derived_artifact,
        )
    if (
        compiled_scenario
        and compiled_scenario.get("direct_payload_contract") != direct_payload_contract
    ):
        raise ValueError(
            "Scenario direct_payload_contract does not match selected contract."
        )
    if (args.checkpoint_save and compiled_scenario
            and any(k in compiled_scenario['phases'][-1]
                    for k in ['memory_access_watch', 'chip_bus_trace'])):
        raise ValueError(
            "Checkpoint save requires a final canonical source anchor after any access watch."
        )
    breakpoint_row = (
        resolve_breakpoint_stable_key(args.target, args.breakpoint_stable_key)
        if args.breakpoint_stable_key
        else None
    )
    session = HeadlessCopperlineSession(
        rom_path=args.rom,
        floppy0=floppy0,
        host_directory=args.host_directory,
        target_payload_path=Path(direct_payload["payload"])
        if direct_payload
        else paths.binary_source.path,
        derived_artifact_manifest=args.derived_artifact,
        binary_path=resolve_binary(args.copperline),
        state_directory=args.state_directory,
        continue_seconds=args.continue_seconds,
        loadseg_watch_seconds=args.loadseg_watch_seconds,
        breakpoint_wait_seconds=args.breakpoint_wait_seconds,
        observation_memory_address=observation_memory_address,
        observation_memory_equals=observation_memory_equals,
        observation_memory_write_watch=observation_memory_write_watch,
        direct_payload_contract=direct_payload_contract,
        breakpoint_expected_source_offset=breakpoint_row["start_offset"]
        if breakpoint_row
        else None,
        breakpoint_source_offset=breakpoint_row["start_offset"]
        if breakpoint_row is not None
        and "runtime_breakpoint_address" not in breakpoint_row
        else None,
        breakpoint_runtime_address=breakpoint_row.get("runtime_breakpoint_address")
        if breakpoint_row is not None
        else None,
        scenario_path=scenario_output,
        checkpoint_save=args.checkpoint_save,
        checkpoint_load=args.checkpoint_load,
    )
    if not args.run:
        print(
            json.dumps(
                {
                    "status": "planned",
                    "target_id": args.target,
                    "direct_payload": direct_payload,
                    "scenario": compiled_scenario,
                    "breakpoint_stable_key": args.breakpoint_stable_key,
                    "launch": session.plan(),
                },
                indent=2,
            )
        )
        return 0
    report = run_session(session)
    scenario_summary = None
    if isinstance(compiled_scenario, dict):
        symbols = compiled_scenario.get("symbols")
        scenario_summary = {
            "identifier": compiled_scenario.get("identifier"),
            "symbol_artifact": symbols.get("metadata_path")
            if isinstance(symbols, dict)
            else None,
        }
    result = {
        "runner": report,
        "direct_payload": direct_payload,
        "scenario": scenario_summary,
        "pc_resolution": resolve_paused_pc(args.target, report,
            **({'derived_manifest': args.derived_artifact} if args.derived_artifact else {})),
    }
    if breakpoint_row is not None:
        result["breakpoint"] = resolve_breakpoint_hit(breakpoint_row, report)
    print(json.dumps(result, indent=2))
    return 0 if report.get("status") == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    with analysis_scope():
        return _main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
