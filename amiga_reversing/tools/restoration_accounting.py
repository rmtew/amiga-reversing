"""Report independent restoration evidence dimensions without changing target state."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from amiga_reversing.disasm.binary_source import read_binary_source_bytes
from amiga_reversing.disasm.c_backend import (
    build_listing_artifact_profile_from_binary_source,
)
from amiga_reversing.disasm.completeness import build_accounting, format_accounting
from amiga_reversing.disasm.decision_journal import (
    project_decision_journal,
    read_decision_journal,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_target_metadata,
)
from amiga_reversing.disasm.function_facts import analysis_function_facts
from amiga_reversing.disasm.manual_actions import (
    load_manual_projection,
    manual_action_interpretation,
)
from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.disasm.purpose_assessments import reviewed_assessments


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def verification_evidence(receipt, *, target_id, original, source, package_sha256):
    """Reuse an exact source-bound receipt, never reinterpret it as semantic proof."""
    if receipt is None:
        return {"status": "not_supplied"}
    bound = (
        receipt.get("target_id") == target_id
        and receipt.get("original_sha256") == _hash(original)
        and receipt.get("original_size") == len(original)
        and source is not None
        and receipt.get("source_sha256") == _hash(source)
        and receipt.get("source_package_sha256") == package_sha256
    )
    exact = (
        bound
        and receipt.get("exact") is True
        and receipt.get("framework_exact") is True
        and receipt.get("output_sha256") == _hash(original)
        and (receipt.get("oracle") or {}).get("comparison_level")
        == "oracle.full_file_match"
        and receipt["oracle"].get("output_sha256") == _hash(original)
    )
    return {
        "status": "exact_original_layout" if exact else "stale_or_failed_receipt",
        "source_bound": bound,
        "original_sha256": _hash(original),
        "receipt_id": receipt.get("receipt_id"),
        "semantic_proof": False,
    }


def _snapshot(paths):
    meta = effective_target_metadata(paths.target_dir)
    if meta is None:
        raise ValueError("Canonical target metadata is missing")
    hashes = {
        f: _hash((paths.target_dir / f).read_bytes())
        if (paths.target_dir / f).exists()
        else None
        for f in (
            "manual_actions.jsonl",
            "decision_journal.jsonl",
            "source_binary.json",
            "source-package-manifest.json",
        )
    }
    if paths.output_path is not None:
        hashes["rendered_source"] = (
            _hash(paths.output_path.read_bytes())
            if paths.output_path.exists()
            else None
        )
    return {
        "original_sha256": _hash(read_binary_source_bytes(paths.binary_source)),
        "effective_metadata_sha256": _hash(
            json.dumps(asdict(meta), sort_keys=True).encode()
        ),
        "input_sha256": hashes,
    }


def account_target(target_id, *, receipt=None):
    paths = resolve_project_paths(target_id)
    before = _snapshot(paths)
    metadata = effective_target_metadata(paths.target_dir)
    projection = load_manual_projection(
        paths.target_dir, binary_source=paths.binary_source
    )
    journal = read_decision_journal(paths.target_dir)
    if not journal["valid"]:
        raise ValueError("Invalid canonical Decision Journal")
    decisions = project_decision_journal(journal["records"])
    active = set(projection.active_action_ids)
    statuses = Counter()
    log = paths.target_dir / "manual_actions.jsonl"
    records = (
        [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        if log.exists()
        else []
    )
    for record in records:
        if record.get("action_id") in active:
            statuses[
                manual_action_interpretation(record)["source_evidence_status"]
            ] += 1
    history = {
        "active_actions": len(active),
        "inactive_actions": len(projection.inactive_action_ids),
        "declared_source_evidence_status": dict(sorted(statuses.items())),
        "journal_decision_counts": {
            k: len(decisions[k])
            for k in ("accepted_facts", "deferred_facts", "rejected_facts")
        },
        "purpose_inferred": False,
    }
    with effective_metadata_file(paths.target_dir) as metadata_path:
        artifact = build_listing_artifact_profile_from_binary_source(
            paths.binary_source, metadata_path=metadata_path
        )[2]
    try:
        analysis, _ = artifact.analysis_payload()
        functions = analysis_function_facts(target_id, analysis)
        plan = artifact.source_plan_payload()
        regions = artifact.memory_regions_payload()
    finally:
        artifact.close()
    package_file = paths.target_dir / "source-package-manifest.json"
    package = (
        json.loads(package_file.read_text())
        if package_file.exists()
        else {"manifest": {"files": []}}
    )
    # Check the canonical package's asset byte identities rather than counting
    # arbitrary files or treating every INCBIN as a recovered semantic resource.
    for item in package["manifest"]["files"]:
        if item.get("kind") == "asset":
            path = (paths.target_dir / item["path"]).resolve()
            if not path.is_relative_to(paths.target_dir.resolve()):
                raise ValueError("Asset escapes target")
            blob = path.read_bytes()
            if len(blob) != item["size"] or _hash(blob) != item["sha256"]:
                raise ValueError(f"Stale asset: {item['asset_id']}")
    original = read_binary_source_bytes(paths.binary_source)
    source = (
        paths.output_path.read_bytes()
        if paths.output_path is not None and paths.output_path.exists()
        else None
    )
    verification = verification_evidence(
        receipt,
        target_id=target_id,
        original=original,
        source=source,
        package_sha256=package.get("sha256"),
    )
    report = build_accounting(
        target_id=target_id,
        analysis=analysis,
        metadata=metadata,
        functions=functions,
        source_plan=plan,
        manifest=package["manifest"],
        memory_regions=regions,
        verification=verification,
        provenance={**before, "original_size": len(original)},
        history=history,
        purpose_assessments=reviewed_assessments(
            projection.purpose_assessments, decisions
        ),
    )
    if _snapshot(paths) != before:
        raise ValueError("Canonical inputs changed during accounting; reinspect")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--verification-receipt", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--text-output", type=Path)
    args = parser.parse_args()
    target_dir = resolve_project_paths(args.target).target_dir.resolve()
    outputs = [
        p.resolve() for p in (args.json_output, args.text_output) if p is not None
    ]
    if len(outputs) != len(set(outputs)):
        raise ValueError("Machine and text reports require different output paths")
    if any(p.is_relative_to(target_dir) for p in outputs):
        raise ValueError(
            "Read-only report outputs must be outside the canonical target directory"
        )
    receipt = (
        json.loads(args.verification_receipt.read_text())
        if args.verification_receipt
        else None
    )
    report = account_target(args.target, receipt=receipt)
    machine = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    human = format_accounting(report)
    if args.json_output:
        args.json_output.write_text(machine)
    if args.text_output:
        args.text_output.write_text(human)
    print(human, end="")


if __name__ == "__main__":
    main()
