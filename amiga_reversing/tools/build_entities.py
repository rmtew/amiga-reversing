"""Legacy CLI wrapper for C-backed entity generation."""

import argparse
import sys
from pathlib import Path

from amiga_reversing.disasm.entity_builder import build_entities


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Legacy entities.jsonl generator; current workflows use C analysis facts and Manual Review")
    parser.add_argument("binary", help="Path to Amiga hunk executable")
    parser.add_argument("--output", "-o",
                        help="Output path (default: <target-dir>/entities.jsonl)")
    parser.add_argument("--target-dir", "-t",
                        help="Target output directory (e.g. targets/amiga_hunk_genam)")
    parser.add_argument("--base-addr", type=lambda x: int(x, 0),
                        default=0,
                        help="Runtime base address (e.g. 0x400)")
    parser.add_argument("--code-start", type=lambda x: int(x, 0),
                        default=0,
                        help="Byte offset where code begins (skips bootstrap)")
    args = parser.parse_args()

    output = args.output
    if output is None and args.target_dir:
        output = str(Path(args.target_dir) / "entities.jsonl")

    return int(build_entities(args.binary, output,
                              base_addr=args.base_addr,
                              code_start=args.code_start))


if __name__ == "__main__":
    sys.exit(main())
