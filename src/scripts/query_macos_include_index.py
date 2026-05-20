#!/usr/bin/env python3
"""Query the Classic Mac OS include symbol index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_items(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data["items"])


def entry_text(item: dict[str, object]) -> str:
    bits = [f"  {item['kind']} {item['source']}:{item['line']}"]
    if item.get("value"):
        bits.append(f"= {item['value']}")
    if item.get("declaration"):
        bits.append(str(item["declaration"]))
    return "\n    ".join(bits)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("--index", type=Path, default=Path("ext/macos_includes/mpw_gm/index.json"))
    parser.add_argument("--kind", action="append", default=[])
    parser.add_argument("--contains", action="store_true", help="substring match instead of exact symbol match")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    symbol = args.symbol.lower()
    kinds = set(args.kind)
    matches: list[dict[str, object]] = []
    for item in load_items(args.index):
        name = str(item["name"])
        if kinds and item["kind"] not in kinds:
            continue
        if args.contains:
            if symbol not in name.lower():
                continue
        elif symbol != name.lower():
            continue
        matches.append(item)

    if not matches:
        print(f"{args.symbol}: no matches")
        return 1

    print(f"{args.symbol}: {len(matches)} match(es)")
    for item in matches[: args.limit]:
        print(entry_text(item))
    if len(matches) > args.limit:
        print(f"  ... {len(matches) - args.limit} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
