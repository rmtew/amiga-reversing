#!/usr/bin/env python3
"""Inspect a classic Mac OS resource fork."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from amiga_reversing.disasm.macos_resource_fork import parse_resource_fork


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("resource_fork", type=Path)
    parser.add_argument("--type", dest="resource_type")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    summary = parse_resource_fork(args.resource_fork.read_bytes(), args.resource_fork.as_posix())
    if args.resource_type:
        summary["resources"] = [
            item for item in summary["resources"] if item["type"] == args.resource_type
        ]
        summary["types"] = [
            item for item in summary["types"] if item["type"] == args.resource_type
        ]

    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
