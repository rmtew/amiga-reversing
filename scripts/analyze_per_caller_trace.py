from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load_events(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _site_key(event: dict[str, Any]) -> int | None:
    source_addr = event.get("source_addr")
    return source_addr if isinstance(source_addr, int) else None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: uv run scripts/analyze_per_caller_trace.py <trace.jsonl>")
    events = _load_events(Path(argv[1]))
    site_times: Counter[int] = Counter()
    site_resolutions: Counter[int] = Counter()
    site_targets: dict[int, set[int]] = defaultdict(set)
    collect_counts: Counter[int] = Counter()
    collect_state_sigs: Counter[int] = Counter()
    ctx_counts: Counter[int] = Counter()
    ctx_state_sigs: Counter[int] = Counter()
    site_needed_regs: dict[int, tuple[str, ...]] = {}
    site_reg_projections: dict[int, Counter[str]] = defaultdict(Counter)
    site_target_by_projection: dict[int, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))

    for event in events:
        kind = event.get("kind")
        site = _site_key(event)
        if kind == "site_start" and site is not None:
            needed_regs = event.get("needed_regs")
            if isinstance(needed_regs, list) and all(isinstance(item, str) for item in needed_regs):
                site_needed_regs[site] = tuple(needed_regs)
        elif kind == "site_done" and site is not None:
            site_times[site] += float(event.get("elapsed_seconds", 0.0))
            site_resolutions[site] += int(event.get("resolution_count", 0))
        elif kind == "site_resolution" and site is not None:
            target = event.get("target")
            if isinstance(target, int):
                site_targets[site].add(target)
            needed_regs = event.get("needed_regs")
            if isinstance(needed_regs, dict):
                projection = json.dumps(needed_regs, sort_keys=True, separators=(",", ":"))
                site_reg_projections[site][projection] += 1
                if isinstance(target, int):
                    site_target_by_projection[site][projection].add(target)
        elif kind == "collect_call_entry_states" and site is not None:
            collect_counts[site] += 1
            collect_state_sigs[site] += int(event.get("unique_state_signatures", 0))
        elif kind == "build_caller_ctx":
            entry = event.get("entry")
            if isinstance(entry, int):
                ctx_counts[entry] += 1
                ctx_state_sigs[entry] += 1

    print("Top per-caller sites by elapsed time:")
    for site, elapsed in site_times.most_common(12):
        print(
            f"  ${site:04X}: {elapsed:.4f}s, "
            f"resolutions={site_resolutions[site]}, "
            f"unique_targets={len(site_targets[site])}, "
            f"collect_calls={collect_counts[site]}, "
            f"collect_unique_state_sig_total={collect_state_sigs[site]}, "
            f"needed_regs={list(site_needed_regs.get(site, ()))}, "
            f"reg_projections={len(site_reg_projections[site])}"
        )
        projection_targets = [
            len(targets)
            for targets in site_target_by_projection[site].values()
        ]
        if projection_targets:
            print(
                f"    projection_target_span=min={min(projection_targets)} "
                f"max={max(projection_targets)}"
            )

    if ctx_counts:
        print("\nTop subroutine entries by caller-context rebuild count:")
        for entry, count in ctx_counts.most_common(12):
            print(f"  ${entry:04X}: caller_ctx_builds={count}, ctx_signatures={ctx_state_sigs[entry]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
