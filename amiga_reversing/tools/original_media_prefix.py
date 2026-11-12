"""Reviewed normal-media recipes feeding the canonical scenario runner.

The recipe registry is intentionally closed. A scenario cannot supply Python,
arbitrary control requests, memory writes, or an unverified bootstrap address.
New games need their own reviewed loader/input recipe, not guessed handoffs.
"""
from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path


def validate_prefix_target(prefix, target_id):
    if prefix != "starglider2" or target_id != "amiga_raw_starglider2_game":
        raise ValueError("Original-media prefix is not registered for this target")


def prefix_source_view(prefix, target_id):
    """Expected loader coordinates; the live recipe must still verify the copy."""
    validate_prefix_target(prefix, target_id)
    from .starglider2_extract import SPANS
    _, _, size, load, _ = next(s for s in SPANS if s[0] == "game_copy")
    return dict(section_index=0, source_start=0, source_end=size, base_addr=load,
                mapping_source="reviewed_original_media_recipe", requires_loaded_byte_identity=True)


def run_original_media_session(session):
    if (session.floppy0 is None or session.state_directory is None or session.scenario_path is None or
            session.direct_payload_contract is not None or session.host_directory is not None or
            session.derived_artifact_manifest is not None or session.checkpoint_load is not None or
            session.checkpoint_save is not None or session.loadseg_watch_seconds is not None or
            session.breakpoint_runtime_address is not None or session.breakpoint_source_offset is not None or
            session.observation_memory_address is not None or session.observation_memory_equals is not None or
            session.observation_memory_write_watch):
        raise ValueError("Original-media prefix needs an isolated normal-media scenario")
    scenario = json.loads(session.scenario_path.read_text())
    validate_prefix_target(session.original_media_prefix, scenario.get("target_id"))
    if (scenario.get("start_observable") != "original_media_handoff" or
            scenario.get("original_media_prefix") != session.original_media_prefix or
            scenario.get("direct_payload_contract") is not None):
        raise ValueError("Compiled scenario does not select this original-media prefix")
    phases = scenario.get('phases')
    if not isinstance(phases, list) or not phases or any(not isinstance(p, dict) for p in phases):
        raise ValueError('Original-media handoff needs compiled canonical source phases')
    if any(p.get('transition', 'continue') != 'continue' for p in phases):
        raise ValueError('Original-media scenarios do not inject function calls')
    from .starglider2_extract import extract
    from .starglider2_flight_probe import main as run_flight

    disk = session.floppy0.resolve()
    payloads, _ = extract(disk.read_bytes())  # exact disk identity, not an address scan
    if session.target_payload_path.read_bytes() != payloads["game_copy"]:
        raise ValueError("Canonical target differs from the original extracted payload")
    inputs = Path(session.state_directory) / "original-media-inputs"
    output = Path(session.state_directory) / "original-media-run"
    if inputs.exists() or output.exists():
        raise ValueError("Original-media run paths must be fresh")
    inputs.mkdir(parents=True)
    (inputs / "original.adf").symlink_to(disk)
    (inputs / "first-read.bin").write_bytes(payloads["intro_read"])
    (inputs / "main-copy.bin").write_bytes(payloads["game_copy"])
    # Reuse the previously qualified normal protection-input workflow. All
    # transport ownership remains in that driver; canonical phases share its
    # live client after loaded-byte checks and the natural flight entry.
    with contextlib.redirect_stdout(sys.stderr):
        report = run_flight([
            "--inputs", str(inputs), "--rom", str(session.rom_path),
            "--copperline", str(session.binary_path), "--output", str(output),
            "--answer-selected-protection-request",
        ], canonical_scenario=scenario)
    if not isinstance(report, dict) or "canonical_observation" not in report:
        raise ValueError("Normal-media prefix did not reach the canonical scenario")
    return report["canonical_observation"]
