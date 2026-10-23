"""Compact Pandora counts from canonical metadata, native queries and inventories.

This is an evidence index, not a semantic analyzer or a completion score. It
never classifies bytes from assembly text or treats a named object as proved.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from amiga_reversing.disasm.restoration_client import RestorationClient

TARGET = "amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8"


def stocktake(server: str = "http://127.0.0.1:8123") -> dict:
    client = RestorationClient(server)
    state = client.call(TARGET, "state")
    if not state["ready"]:
        raise ValueError(
            "Native listing is not ready; inspect the state job before retrying."
        )
    revision = state["revision"]
    paths = resolve_project_paths(TARGET)
    metadata = effective_target_metadata(paths.target_dir)
    if metadata is None:
        raise ValueError("Canonical target metadata is missing.")
    native = {}
    for kind in (
        "instructions",
        "symbols",
        "references",
        "functions",
        "fields",
        "edges",
        "gaps",
    ):
        page = client.call(
            TARGET,
            "query",
            kind=kind,
            limit=100 if kind == "fields" else 1,
            expected_revision=revision,
        )
        native[kind] = {"count": page["total"], "scope": page["scope"]}
        if kind == "fields":
            records = Counter()
            while True:
                for item in page["items"]:
                    # Native query records expose resolved field names or an
                    # explicit unresolved status; aggregate that existing DTO.
                    records[
                        "resolved"
                        if "field_name" in item
                        else item.get("status", "unknown")
                    ] += 1
                if not page.get("next_cursor"):
                    break
                page = client.call(
                    TARGET,
                    "query",
                    kind=kind,
                    limit=100,
                    cursor=page["next_cursor"],
                    expected_revision=revision,
                )
            native[kind]["native_record_status_counts"] = dict(records)
    declarations = {
        key: len(getattr(metadata, key))
        for key in (
            "custom_structs",
            "data_block_layouts",
            "function_summaries",
            "entry_register_seeds",
            "rsset_layout_regions",
            "seeded_code_labels",
            "target_equates",
            "manual_data_references",
            "manual_representations",
        )
    }
    inventory = PROJECT_ROOT / "docs/targets/pandora-coverage-current.tsv"
    with inventory.open() as stream:
        intervals = list(csv.DictReader(stream, delimiter="\t"))
    end = 0
    counts, sizes = Counter(), Counter()
    for interval in intervals:
        start, stop, size = (
            int(interval[k]) for k in ("start_offset", "end_offset", "size")
        )
        if (
            int(interval["section_index"]) != 0
            or start != end
            or stop - start != size
            or size <= 0
        ):
            raise ValueError(
                "Existing coverage inventory is not a complete disjoint partition."
            )
        counts[interval["classification"]] += 1
        sizes[interval["classification"]] += size
        end = stop
    original = paths.binary_source.path.read_bytes()
    if end != len(original):
        raise ValueError("Coverage inventory and payload size disagree.")
    manifest = json.loads(
        (paths.target_dir / "source-package-manifest.json").read_text()
    )["manifest"]
    assets = []
    for item in manifest["files"]:
        if item["kind"] != "asset":
            continue
        payload = (paths.target_dir / item["path"]).read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if len(payload) != item["size"] or digest != item["sha256"]:
            raise ValueError(f"Asset does not match its manifest: {item['path']}")
        assets.append(
            {key: item[key] for key in ("asset_id", "name", "path", "size", "sha256")}
        )
    if client.call(TARGET, "state")["revision"] != revision:
        raise ValueError("Canonical history changed during the stocktake; reinspect.")
    return {
        "target_id": TARGET,
        "revision": revision,
        "subject_revision": state["subject_revision"],
        "payload": {
            "size": len(original),
            "sha256": hashlib.sha256(original).hexdigest(),
        },
        "canonical_declarations": declarations,
        "native_query_totals": native,
        "history": state["history_summary"],
        "existing_coverage_inventory": {
            "path": str(inventory.relative_to(PROJECT_ROOT)),
            "sha256": hashlib.sha256(inventory.read_bytes()).hexdigest(),
            "intervals": len(intervals),
            "interval_counts": dict(counts),
            "union_bytes": dict(sizes),
            "partition_bytes": end,
            "scope": "Existing inventory partition; not rederived at this revision and not a semantic completion claim.",
        },
        "assets": {
            "count": len(assets),
            "identity_sha256": hashlib.sha256(
                json.dumps(assets, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "all_payloads_match_manifest": True,
        },
        "limits": [
            "Exact original-layout reproduction is a separate verification receipt.",
            "Declarations and candidate/query counts do not establish semantic truth or complete ownership.",
            "Raw preservation and the existing coverage partition do not establish resource purpose.",
            "Alternate-layout readiness requires closed references, placement/lifetime constraints and changed-layout execution evidence.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default="http://127.0.0.1:8123")
    args = parser.parse_args()
    print(json.dumps(stocktake(args.server), indent=2))


if __name__ == "__main__":
    main()
