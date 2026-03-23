#!/usr/bin/env py.exe
"""
Update progress.md from entities.jsonl.

Reads all entities, computes statistics, and rewrites the progress file
with current counts.
"""

import json
from collections import defaultdict
from contextlib import suppress
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent
BIN_DIR = PROJECT_ROOT / "bin"
EntityRecord = dict[str, Any]


def parse_addr(addr: object) -> int:
    if isinstance(addr, int):
        return addr
    if isinstance(addr, str):
        return int(addr, 0)
    return 0


def load_entities(entities_file: Path) -> list[EntityRecord]:
    entities: list[EntityRecord] = []
    if not entities_file.exists():
        return entities
    with open(entities_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            with suppress(json.JSONDecodeError):
                entities.append(json.loads(line))
    return entities


def get_binary_size() -> int | None:
    bin_files = [f for f in BIN_DIR.glob("*")
                 if f.is_file() and f.name != ".gitkeep" and not f.name.startswith(".")]
    if len(bin_files) == 1:
        return bin_files[0].stat().st_size
    return None


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Update progress.md from entities.jsonl")
    parser.add_argument("--target-dir", "-t", default=".",
                        help="Target directory containing entities.jsonl")
    args = parser.parse_args()

    target_dir = Path(args.target_dir)
    entities_file = target_dir / "entities.jsonl"
    progress_file = target_dir / "progress.md"

    entities = load_entities(entities_file)
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

    coverage = f"{(bytes_classified / binary_size * 100):.1f}%" if binary_size else "-"
    binary_size_str = str(binary_size) if binary_size else "-"

    named = sum(1 for e in entities if e.get("name"))
    documented = sum(1 for e in entities if str(e.get("comment", "")).strip())
    verified = sum(1 for e in entities if e.get("confidence") == "verified")
    typed = sum(1 for e in entities if e.get("type") not in (None, "unknown"))

    # Count xrefs
    xref_fields = ["calls", "called_by", "reads", "read_by", "writes", "written_by"]
    total_xrefs = sum(len(e.get(f, [])) for e in entities for f in xref_fields) // 2  # bidirectional

    unknown_code = sum(1 for e in code_ents if not e.get("name"))
    documented_code = sum(1 for e in code_ents if str(e.get("comment", "")).strip())
    unknown_data = sum(1 for e in data_ents if not e.get("subtype"))
    documented_data = sum(1 for e in data_ents if str(e.get("comment", "")).strip())

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

## Entity Breakdown

### Code Entities ({len(code_ents)} total)
| Metric | Count |
|--------|-------|
| named | {len(code_ents) - unknown_code} |
| unnamed | {unknown_code} |
| documented | {documented_code} |

### Data Entities ({len(data_ents)} total)
| Metric | Count |
|--------|-------|
| typed subtype | {len(data_ents) - unknown_data} |
| untyped subtype | {unknown_data} |
| documented | {documented_data} |

## Data Subtype Breakdown
"""
    subtype_counts: defaultdict[str, int] = defaultdict(int)
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

    with open(progress_file, "w") as f:
        f.write(progress)

    print(f"Progress updated: {total} entities, {coverage} coverage")


if __name__ == "__main__":
    main()
