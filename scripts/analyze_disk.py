#!/usr/bin/env py.exe
"""Analyze Amiga ADF disk images."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from amiga_disk import DiskAnalysisError, analyze_adf, print_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Amiga ADF disk images")
    parser.add_argument("adf_file", help="Path to ADF file")
    parser.add_argument(
        "-o",
        "--output",
        choices=["json", "summary"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument("--outfile", help="Write JSON output to file")
    parser.add_argument(
        "--extract",
        metavar="DIR",
        help="Extract files to directory (AmigaDOS disks only)",
    )
    parser.add_argument(
        "--tracks",
        action="store_true",
        help="Include per-track analysis",
    )
    args = parser.parse_args()

    try:
        result = analyze_adf(
            args.adf_file,
            extract_dir=args.extract,
            include_tracks=args.tracks,
        )
    except DiskAnalysisError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output == "json" or args.outfile:
        json_text = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        if args.outfile:
            Path(args.outfile).write_text(json_text, encoding="utf-8")
        else:
            print(json_text)
        return 0

    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
