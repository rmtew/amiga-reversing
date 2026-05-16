from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from amiga_reversing.disasm.source_export import (
    SOURCE_EXPORT_ASSEMBLER_PROFILES,
    source_export_payload,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export rendered assembler source without verification.")
    parser.add_argument("target")
    parser.add_argument("--assembler-profile", choices=SOURCE_EXPORT_ASSEMBLER_PROFILES, default="vasm")
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--json", action="store_true", help="Print export metadata as JSON.")
    args = parser.parse_args(argv)

    payload = source_export_payload(args.target, assembler_profile=args.assembler_profile)
    if payload.get("status") == "refused":
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"source export refused: {payload.get('message')}", file=sys.stderr)
        return 2
    source_text = str(payload["source_text"])
    output = args.output or Path(str(payload["filename"]))
    output.write_text(source_text, encoding="utf-8", newline="")
    if args.json:
        metadata = {key: value for key, value in payload.items() if key != "source_text"}
        metadata["output"] = str(output)
        print(json.dumps(metadata, indent=2, sort_keys=True))
    else:
        print(f"exported {output} (not verification)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
