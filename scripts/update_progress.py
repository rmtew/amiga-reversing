#!/usr/bin/env python3
"""
Update progress.md from entities.jsonl.

Reads all entities, computes statistics, and rewrites the progress file
with current counts.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
ENTITIES_FILE = PROJECT_ROOT / "entities.jsonl"
PROGRESS_FILE = PROJECT_ROOT / "progress.md"
BIN_DIR = PROJECT_ROOT / "bin"


def parse_addr(addr):
    if isinstance(addr, int):
        return addr
    if isinstance(addr, str):
        return int(addr, 0)
    return 0


def load_entities():
    entities = []
    if not ENTITIES_FILE.exists():
        return entities
    with open(ENTITIES_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                entities.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entities


def get_binary_size():
    bin_files = [f for f in BIN_DIR.glob("*")
                 if f.is_file() and f.name != ".gitkeep" and not f.name.startswith(".")]
    if len(bin_files) == 1:
        return bin_files[0].stat().st_size
    return None


def main():
    entities = load_entities()
    binary_size = get_binary_size()

    total = len(entities)
    code_ents = [e for e in entities if e.get("type") == "code"]
    data_ents = [e for e in entities if e.get("type") == "data"]

    bytes_classified = 0
    for e in entities:
        if e.get("type") not in (None, "unknown"):
            start = parse_addr(e.get("addr", 0))
            end = parse_addr(e.get("end", 0))
            bytes_classified += end - start

    coverage = f"{(bytes_classified / binary_size * 100):.1f}%" if binary_size else "—"
    binary_size_str = str(binary_size) if binary_size else "—"

    named = sum(1 for e in entities if e.get("name"))
    documented = sum(1 for e in entities if e.get("status") == "documented")
    verified = sum(1 for e in entities if e.get("confidence") == "verified")
    typed = sum(1 for e in entities if e.get("type") not in (None, "unknown"))

    # Count xrefs
    xref_fields = ["calls", "called_by", "reads", "read_by", "writes", "written_by"]
    total_xrefs = sum(len(e.get(f, [])) for e in entities for f in xref_fields) // 2  # bidirectional

    def count_by_status(ents):
        counts = defaultdict(int)
        for e in ents:
            counts[e.get("status", "unmapped")] += 1
        return counts

    code_status = count_by_status(code_ents)
    data_status = count_by_status(data_ents)

    progress = f"""# Disassembly Progress

## Summary
| Metric | Value |
|--------|-------|
| Binary size | {binary_size_str} |
| Bytes classified | {bytes_classified} |
| Coverage | {coverage} |
| Total entities | {total} |
| Entities typed | {typed} |
| Entities named | {named} |
| Entities documented | {documented} |
| Entities verified | {verified} |
| Cross-refs resolved | {total_xrefs} |

## Milestones
- [ ] Binary loaded and initial mechanical disassembly
- [ ] Entry point identified
- [ ] Main loop identified
- [ ] OS takeover/restore code documented
- [ ] Interrupt handlers identified
- [ ] Copper list(s) analyzed
- [ ] Sprite data located
- [ ] Bitplane/graphics data located
- [ ] Sound/music driver identified
- [ ] Input handling identified
- [ ] Game state structures identified
- [ ] Level data format understood
- [ ] Full round-trip reassembly passes

## Entity Status Breakdown

### Code Entities ({len(code_ents)} total)
| Status | Count |
|--------|-------|
| unmapped | {code_status['unmapped']} |
| typed | {code_status['typed']} |
| named | {code_status['named']} |
| documented | {code_status['documented']} |

### Data Entities ({len(data_ents)} total)
| Status | Count |
|--------|-------|
| unmapped | {data_status['unmapped']} |
| typed | {data_status['typed']} |
| named | {data_status['named']} |
| documented | {data_status['documented']} |

## Data Subtype Breakdown
"""
    subtype_counts = defaultdict(int)
    for e in data_ents:
        if e.get("subtype"):
            subtype_counts[e["subtype"]] += 1

    if subtype_counts:
        progress += "| Subtype | Count |\n|---------|-------|\n"
        for st, count in sorted(subtype_counts.items()):
            progress += f"| {st} | {count} |\n"
    else:
        progress += "(No data subtypes identified yet)\n"

    progress += "\n## Recent Activity\n(Updated as work progresses)\n"

    with open(PROGRESS_FILE, "w") as f:
        f.write(progress)

    print(f"Progress updated: {total} entities, {coverage} coverage")


if __name__ == "__main__":
    main()
