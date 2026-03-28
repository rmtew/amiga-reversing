#!/usr/bin/env py.exe
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from disasm.target_metadata import (
    TargetMetadata,
    target_seeded_metadata_path,
    validate_target_seeded_metadata,
    write_target_seeded_metadata,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and normalize optional target_seeded_metadata.json")
    parser.add_argument("target_dir")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    target_dir = Path(args.target_dir)
    seeded_path = target_seeded_metadata_path(target_dir)
    if not seeded_path.exists():
        raise FileNotFoundError(f"Missing target_seeded_metadata.json: {target_dir}")
    try:
        seeded_only = validate_target_seeded_metadata(
            TargetMetadata.from_dict(json.loads(seeded_path.read_text(encoding="utf-8")))
        )
    except Exception as exc:
        raise ValueError("Bad target_seeded_metadata.json") from exc
    if args.write:
        write_target_seeded_metadata(target_dir, seeded_only)
    print("target_seeded_metadata: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
