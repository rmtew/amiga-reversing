"""Inspect explicit typed pointer fields using the canonical native render plan."""

from __future__ import annotations

import argparse
import json

from amiga_reversing.disasm.c_backend import build_project_listing_artifact_profile
from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.disasm.target_history import target_lock
from amiga_reversing.disasm.typed_pointer_report import typed_pointer_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--struct-name")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--exceptions-only", action="store_true")
    args = parser.parse_args(argv)
    paths = resolve_project_paths(args.target)
    with target_lock(paths.target_dir):
        metadata = effective_target_metadata(paths.target_dir)
        if metadata is None:
            parser.error("Target metadata is required")
        _, _, artifact = build_project_listing_artifact_profile(args.target)
        try:
            report = typed_pointer_report(
                metadata, artifact.row_for_source_offset,
                offset=args.offset, limit=args.limit,
                struct_name=args.struct_name, summary_only=args.summary,
                exceptions_only=args.exceptions_only,
            )
        finally:
            artifact.close()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
