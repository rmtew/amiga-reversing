#!/usr/bin/env py.exe
"""Import an AmigaDOS ADF into extracted files plus binary-backed targets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from amiga_disk import DiskAnalysisError, import_adf


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import an ADF into bin/imported and targets/"
    )
    parser.add_argument("adf_file", help="Path to ADF file")
    parser.add_argument(
        "--disk-id",
        help="Stable disk id (default: derived from filename)",
    )
    parser.add_argument(
        "--output",
        choices=["summary", "json"],
        default="summary",
        help="Output format (default: summary)",
    )
    args = parser.parse_args()

    try:
        manifest = import_adf(args.adf_file, disk_id=args.disk_id)
    except DiskAnalysisError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output == "json":
        print(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False))
        return 0

    disk_id = manifest.disk_id
    targets = manifest.imported_targets
    source_path = manifest.source_path
    print(f"Imported {source_path} as {disk_id}")
    print(f"  Targets created: {len(targets)}")
    for target in targets:
        print(f"    {target.target_name}: {target.entry_path}")
    if not targets:
        print("  No Amiga hunk executables found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
