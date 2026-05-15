from __future__ import annotations

import argparse
import json
from pathlib import Path

from amiga_reversing.disasm.target_metadata import (
    TargetMetadata,
    target_seeded_metadata_path,
    validate_target_seeded_metadata,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate optional target_seeded_metadata.json")
    parser.add_argument("target_dir")
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
    print("target_seeded_metadata: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
