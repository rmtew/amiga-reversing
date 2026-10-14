"""Source-bound verification and bounded observations for restoration operations.

Callers serialize target operations and check the subject revision before and after
these operations. Receipts are disposable evidence, never target facts or decisions.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from amiga_reversing.disasm.binary_source import read_binary_source_bytes
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.oracle_compatibility import run_vasm_oracle
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from amiga_reversing.disasm.reproduction import run_reproduction
from amiga_reversing.disasm.source_rendering import (
    publish_rendered_source,
    render_source_from_binary_source_or_raise,
)
from amiga_reversing.tools.copperline_control import CopperlineError, CopperlineTimeout
from amiga_reversing.tools.copperline_session import (
    HeadlessCopperlineSession,
    compile_scenario,
    resolve_binary,
    run_session,
)
from amiga_reversing.tools.direct_payload_adapter import build_boot_adf, load_contract


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _directory(target_id: str) -> Path:
    # Hash untrusted identifiers rather than permitting path components.
    path = PROJECT_ROOT / ".runtime-state" / "restoration" / _hash(target_id.encode())
    path.mkdir(parents=True, exist_ok=True)
    return path


def _persist(target_id: str, receipt: dict) -> dict:
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    identity = _hash(encoded)
    (_directory(target_id) / f"{identity}.json").write_bytes(encoded)
    return {**receipt, "receipt_id": identity}


def verify(target_id: str, subject_revision: str, *, artifact=None) -> dict:
    """Regenerate canonical source and run the existing C/external oracle gates."""
    paths = resolve_project_paths(target_id)
    with effective_metadata_file(paths.target_dir) as metadata_path:
        rendering = render_source_from_binary_source_or_raise(
                target_id=target_id,
                binary_source=paths.binary_source,
                target_dir=paths.target_dir,
                metadata_path=metadata_path,
                project_root=PROJECT_ROOT,
                workflow_id="restoration_verify",
                artifact=artifact,
            )
    source, profile = rendering.source_text, rendering.listing_profile
    source_bytes = source.encode("utf-8")
    directory = _directory(target_id)
    source_path = directory / f"{_hash(source_bytes)}.s"
    if rendering.source_package is None:
        source_path.write_bytes(source_bytes)
    if paths.output_path is not None:
        publish_rendered_source(rendering, paths.output_path, target_id=target_id, project_root=PROJECT_ROOT)
    report = run_reproduction(
        target_id,
        assembler="our",
        persist_report=False,
        pre_rendered_source_text=source,
        pre_rendered_source_profile=profile,
        pre_rendered_source_package=rendering.source_package,
    )
    if rendering.source_package is not None:
        source_path = Path(report["source_path"])
    original = read_binary_source_bytes(paths.binary_source)
    comparison = report.get("comparison") or {}
    exact = comparison.get("full_file_exact") is True
    rebuilt_path = None
    output_hash = None
    if exact:
        # Never trust a previously surviving rebuilt.bin when the current run failed.
        rebuilt = Path(report["rebuilt_path"]).read_bytes()
        exact = rebuilt == original
        if exact:
            output_hash = _hash(rebuilt)
            rebuilt_path = directory / f"{output_hash}.bin"
            rebuilt_path.write_bytes(rebuilt)
    oracle = run_vasm_oracle(
        target_id,
        pre_rendered_source_text=source,
        pre_rendered_source_profile=profile,
        pre_rendered_source_package=rendering.source_package,
    )
    framework_exact = exact
    exact = exact and oracle.get("comparison_level") == "oracle.full_file_match"
    return _persist(
        target_id,
        {
            "kind": "verification",
            "framework_exact": framework_exact,
            "target_id": target_id,
            "subject_revision": subject_revision,
            "status": "exact" if exact else "failed",
            "exact": exact,
            "source_sha256": _hash(source_bytes),
            "source_path": str(source_path),
            "source_package_sha256": rendering.source_package["sha256"] if rendering.source_package else None,
            "original_sha256": _hash(original),
            "original_size": len(original),
            "output_sha256": output_hash,
            "rebuilt_path": str(rebuilt_path) if rebuilt_path else None,
            "framework_status": report.get("status"),
            "failure_kinds": comparison.get("failure_kinds", []),
            "message": str(
                report.get("message")
                or report.get("tool_error")
                or report.get("assembler_stderr")
                or ""
            )[:1000],
            "oracle": {
                key: oracle.get(key)
                for key in (
                    "oracle_id",
                    "output_sha256",
                    "comparison_level",
                    "assembler_status",
                    "message",
                )
            },
        },
    )


def load_receipt(target_id: str, receipt_id: str) -> dict:
    """Read content-addressed evidence; never accept a caller-supplied path."""
    if (
        not isinstance(receipt_id, str)
        or len(receipt_id) != 64
        or any(c not in "0123456789abcdef" for c in receipt_id)
    ):
        raise ValueError("A persisted receipt identity is required.")
    encoded = (_directory(target_id) / f"{receipt_id}.json").read_bytes()
    if _hash(encoded) != receipt_id:
        raise ValueError("Receipt integrity mismatch.")
    saved = json.loads(encoded)
    if saved.get("target_id") != target_id:
        raise ValueError("Receipt belongs to another target.")
    return {**saved, "receipt_id": receipt_id}


def _verified_receipt(
    target_id: str, subject_revision: str, verification: dict
) -> dict:
    saved = load_receipt(target_id, verification.get("receipt_id", ""))
    if (
        saved.get("target_id") != target_id
        or saved.get("subject_revision") != subject_revision
    ):
        raise ValueError("Verification subject is stale or belongs to another target.")
    if saved.get("kind") != "verification" or saved.get("exact") is not True:
        raise ValueError("An exact rebuilt payload is required.")
    payload = Path(saved["rebuilt_path"]).resolve()
    if not payload.is_relative_to(_directory(target_id).resolve()):
        raise ValueError("Rebuilt payload is outside the receipt directory.")
    if _hash(payload.read_bytes()) != saved["output_sha256"]:
        raise ValueError("Verified rebuilt payload changed.")
    return saved


def run_probe(
    target_id: str,
    subject_revision: str,
    question: str,
    scenario: str,
    verification: dict,
    *,
    duration_seconds: int = 120,
) -> dict:
    """Observe an explicit question using a repository scenario and rebuilt bytes.

    duration_seconds bounds the sum of emulator observation waits, including the
    handoff. Process startup and canonical scenario compilation are additional.
    """
    if not isinstance(question, str) or not question.strip() or len(question) > 2000:
        raise ValueError("An explicit question of 1..2000 characters is required.")
    if type(duration_seconds) is not int or not 1 <= duration_seconds <= 120:
        raise ValueError("Observation budget must be 1..120 seconds.")
    scenario_root = (PROJECT_ROOT / "runtime" / "scenarios").resolve()
    scenario_name = scenario if Path(scenario).suffix else scenario + ".json"
    scenario_path = (scenario_root / scenario_name).resolve()
    if (
        not scenario_path.is_relative_to(scenario_root)
        or scenario_path.suffix != ".json"
    ):
        raise ValueError("Choose a JSON scenario under runtime/scenarios.")
    if scenario_path.stat().st_size > 65536:
        raise ValueError("Scenario exceeds the 64 KiB definition limit.")
    definition = json.loads(scenario_path.read_text())
    phases = definition.get("phases", [])
    waits = [phase.get("wait_seconds") for phase in phases[1:]]
    if any(type(wait) is not int or wait < 1 for wait in waits):
        raise ValueError("Each source phase requires a positive integer wait.")
    handoff_seconds = min(15, duration_seconds - sum(waits))
    if handoff_seconds < 1:
        raise ValueError("Scenario waits exceed the total observation budget.")
    saved = _verified_receipt(target_id, subject_revision, verification)
    contract = load_contract(definition["direct_payload_contract"])
    if contract.target_id != target_id:
        raise ValueError("Scenario contract belongs to another target.")
    rom = os.environ.get("COPPERLINE_ROM")
    if not rom or not Path(rom).is_file():
        raise ValueError("Set COPPERLINE_ROM to a legal local Kickstart ROM.")
    binary = resolve_binary(None)
    directory = _directory(target_id) / _hash(
        (subject_revision + question + scenario).encode()
    )
    directory.mkdir(parents=True, exist_ok=True)
    compiled_path = directory / "scenario.json"
    compiled = compile_scenario(
        target_id, scenario_path, compiled_path, symbol_directory=directory
    )
    payload = Path(saved["rebuilt_path"])
    floppy = directory / "rebuilt.adf"
    build_boot_adf(contract, payload, floppy)
    error = None
    try:
        result = run_session(
            HeadlessCopperlineSession(
                rom_path=Path(rom),
                binary_path=binary,
                target_payload_path=payload,
                floppy0=floppy,
                state_directory=directory,
                continue_seconds=handoff_seconds,
                direct_payload_contract=contract.identifier,
                scenario_path=compiled_path,
            )
        )
    except CopperlineError as exc:
        error = f"{type(exc).__name__}: {exc}"[:1000]
        result = {
            "status": "timeout" if isinstance(exc, CopperlineTimeout) else "failed"
        }
    observed = ((result.get("observation") or {}).get("scenario") or {}).get(
        "phases", []
    )
    status = (
        "observed"
        if result.get("status") == "ok"
        else (
            "not_observed"
            if result.get("status") == "timeout"
            or any(p.get("status") == "timeout" for p in observed)
            else "failed"
        )
    )
    return _persist(
        target_id,
        {
            "kind": "probe",
            "target_id": target_id,
            "subject_revision": subject_revision,
            "question": question,
            "error": error,
            "status": status,
            "scenario": scenario_path.name,
            "scenario_sha256": _hash(scenario_path.read_bytes()),
            "verification_receipt_id": verification["receipt_id"],
            "output_sha256": saved["output_sha256"],
            "conditions": {
                "profile": "A500OCS PAL 68000 512K chip + 512K slow",
                "observation_budget_seconds": duration_seconds,
                "handoff_seconds": handoff_seconds,
                "contract": contract.identifier,
                "rom_sha256": _hash(Path(rom).read_bytes()),
                "input_events": definition.get("input_events", []),
            },
            "source_phases": compiled.get("phases", []),
            "outcomes": observed,
            "unknowns": [
                "Not observed means only not observed under these conditions; it is not proof of unreachability."
            ],
        },
    )
