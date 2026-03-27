#!/usr/bin/env py.exe
"""Validate and optionally normalize the authored Amiga NDK corrections KB."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb.os_reference import (
    load_os_reference_payload,
    load_split_os_reference_payloads,
    merge_os_reference_payloads,
    normalize_os_reference_corrections,
)
from kb.paths import AMIGA_OS_REFERENCE_CORRECTIONS_JSON


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corrections",
        default=str(AMIGA_OS_REFERENCE_CORRECTIONS_JSON),
        help="Path to authored corrections JSON",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite the corrections file in normalized canonical form",
    )
    args = parser.parse_args()

    includes, other, _ = load_split_os_reference_payloads()
    correction_path = Path(args.corrections)
    corrections = load_os_reference_payload(correction_path)
    normalized = normalize_os_reference_corrections(corrections)
    merge_os_reference_payloads(
        includes=includes,
        other=other,
        corrections=normalized,
    )

    if args.write:
        with open(correction_path, "w", encoding="utf-8") as handle:
            json.dump(normalized, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        print(f"normalized {correction_path}")
    else:
        print(f"validated {correction_path}")


if __name__ == "__main__":
    main()
