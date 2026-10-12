"""Generate disposable runtime function metadata from canonical analysis facts.

The artifact is deliberately a host-side description only: it contains no
target bytes and is generated into a session state directory.  A function is
eligible only when an accepted manual name is exactly the start of one accepted
contiguous code run.  This makes its extent an analysis fact, rather than an
inference from rendered assembly or the next label.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.disasm.c_backend import build_project_listing_artifact_profile
from amiga_reversing.disasm.function_facts import canonical_function_facts


@dataclass(frozen=True, slots=True)
class FunctionSymbol:
    name: str
    source_start: int
    source_end: int


def _single_runtime_view(artifact: object) -> dict[str, int]:
    views = getattr(artifact, "_runtime_observation_views", ())
    valid = [
        view for view in views
        if isinstance(view, dict)
        and all(type(view.get(key)) is int for key in ("base_addr", "source_start", "source_end"))
    ]
    if len(valid) != 1:
        raise ValueError("runtime symbols require exactly one confirmed runtime observation view.")
    view = {key: int(valid[0][key]) for key in ("base_addr", "source_start", "source_end")}
    if not 0 <= view["source_start"] < view["source_end"]:
        raise ValueError("Runtime observation view has an invalid source range.")
    if not 0 <= view["base_addr"] < view["base_addr"] + view["source_end"] - view["source_start"] <= 0x1000000:
        raise ValueError("Runtime observation view exceeds the 24-bit address space.")
    return view


def _eligible_functions(target_id: str, artifact: object) -> tuple[dict[str, int], tuple[FunctionSymbol, ...]]:
    analysis, _ = artifact.analysis_payload()
    sections = analysis.get("sections")
    if not isinstance(sections, list) or not sections or not isinstance(sections[0], dict):
        raise ValueError("Canonical analysis has no primary section for runtime symbols.")
    view = _single_runtime_view(artifact)
    facts = canonical_function_facts(target_id, analysis, view).get("functions")
    if not isinstance(facts, list):
        raise ValueError("Canonical analysis has no function facts for runtime symbols.")
    functions, _ = _runtime_eligible_facts(facts)
    for function in functions:
        if not view["source_start"] <= function.source_start < function.source_end <= view["source_end"]:
            raise ValueError("Accepted function range lies outside the runtime observation view.")
    if len({item.name for item in functions}) != len(functions):
        raise ValueError("Accepted runtime function names are ambiguous.")
    functions.sort(key=lambda item: (item.source_start, item.name))
    return view, tuple(functions)


def _runtime_eligible_facts(facts: list[object]) -> tuple[list[FunctionSymbol], list[dict[str, object]]]:
    """Select accepted, named contiguous function ranges for runtime entrypoints."""

    functions: list[FunctionSymbol] = []
    omitted: list[dict[str, object]] = []
    for item in facts:
        if not isinstance(item, dict):
            raise ValueError("Canonical function facts contain a malformed entry.")
        name = item.get("name")
        entry = item.get("entry_offset")
        if not isinstance(name, str) or not isinstance(entry, int):
            raise ValueError("Canonical function fact has no named entry offset.")
        if item.get("status") != "accepted":
            omitted.append({"name": name, "entry_offset": entry, "reason": item.get("reason")})
            continue
        ranges = item.get("ranges")
        if not isinstance(ranges, list) or len(ranges) != 1:
            omitted.append({"name": name, "entry_offset": entry, "reason": "noncontiguous_function_ranges"})
            continue
        only_range = ranges[0]
        if not isinstance(only_range, dict) or not isinstance(only_range.get("start_offset"), int) or not isinstance(only_range.get("end_offset"), int):
            raise ValueError("Accepted function fact has an invalid range.")
        start, end = int(only_range["start_offset"]), int(only_range["end_offset"])
        if start != entry:
            omitted.append({"name": name, "entry_offset": entry, "reason": "range_does_not_begin_at_entry"})
            continue
        if end <= start:
            raise ValueError("Accepted function fact has an empty range.")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            omitted.append({"name": name, "entry_offset": entry, "reason": "invalid_symbol_name"})
            continue
        functions.append(FunctionSymbol(name, start, end))
    return functions, omitted


def generate_runtime_symbol_artifact(
    target_id: str, output_directory: Path, *, artifact: object | None = None
) -> dict[str, object]:
    """Write canonical function metadata, containing no executable or target bytes.

    Addresses are planned from the reviewed view; the session must confirm the
    payload identity and runtime mapping before using them as breakpoints.
    ``base_addr`` locates ``source_start``; ``runtime_base`` locates payload
    offset zero. Empty accepted function sets support source-row scenarios.
    """

    owns_artifact = artifact is None
    if artifact is None:
        _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        view, functions = _eligible_functions(target_id, artifact)
    finally:
        if owns_artifact:
            artifact.close()
    payload: dict[str, object] = {
        "schema_version": 1,
        "target_id": target_id,
        "runtime_view": {**view, "runtime_base": view["base_addr"] - view["source_start"]},
        "functions": [
            {
                "name": item.name,
                "source_start": item.source_start,
                "source_end": item.source_end,
                "runtime_start": view["base_addr"] + item.source_start - view["source_start"],
                "runtime_end": view["base_addr"] + item.source_end - view["source_start"],
            }
            for item in functions
        ],
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    metadata_path = output_directory / "canonical-runtime-symbols.json"
    payload["metadata_path"] = str(metadata_path)
    metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def symbol_coverage_report(target_id: str) -> dict[str, object]:
    """Report canonical symbol eligibility without creating an artifact."""

    _, _, artifact = build_project_listing_artifact_profile(target_id)
    try:
        analysis, _ = artifact.analysis_payload()
        view = _single_runtime_view(artifact)
        facts = canonical_function_facts(target_id, analysis, view)["functions"]
    finally:
        artifact.close()
    emitted_functions, omitted = _runtime_eligible_facts(facts)
    emitted = [
        {
            "name": item.name,
            "source_start": item.source_start,
            "source_end": item.source_end,
            "range_count": 1,
        }
        for item in emitted_functions
    ]
    return {
        "target_id": target_id,
        "runtime_view": view,
        "counts": {"emitted": len(emitted), "omitted": len(omitted)},
        "emitted": emitted,
        "omitted": omitted,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(symbol_coverage_report(args.target), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
