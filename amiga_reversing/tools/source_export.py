from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from amiga_reversing.disasm.source_export import (
    SOURCE_EXPORT_ASSEMBLER_PROFILES,
    source_export_payload,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export rendered assembler source without verification.")
    parser.add_argument("target")
    parser.add_argument("--assembler-profile", choices=SOURCE_EXPORT_ASSEMBLER_PROFILES, default="vasm")
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--binary-assets", action="store_true", help="Export a deterministic vasm ZIP package with evidenced opaque assets.")
    parser.add_argument("--structure-macros", action="store_true", help="Generate eligible structure macros from the canonical type definitions; expanded fallbacks remain explicit.")
    parser.add_argument("--minimum-asset-size", type=int, default=256)
    parser.add_argument("--verify-package", action="store_true", help="Check the package with the C assembler and vasm, comparing complete originals.")
    parser.add_argument("--json", action="store_true", help="Print export metadata as JSON.")
    args = parser.parse_args(argv)

    if args.verify_package and not args.binary_assets:
        parser.error("--verify-package requires --binary-assets")
    options = {}
    if args.binary_assets:
        options = {"binary_assets": True, "minimum_asset_size": args.minimum_asset_size}
    if args.structure_macros:
        options["structure_macros"] = True
    try:
        payload = source_export_payload(args.target, assembler_profile=args.assembler_profile, **options)
    except ValueError as exc:
        parser.error(str(exc))
    if payload.get("status") == "refused":
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"source export refused: {payload.get('message')}", file=sys.stderr)
        return 2
    source_text = str(payload["source_text"])
    output = args.output or Path(str(payload["filename"]))
    if args.binary_assets:
        from amiga_reversing.disasm.source_package import write_source_package
        output = args.output or output.with_suffix(".zip")
        write_source_package(cast(dict[str, Any], payload["package"]), output)
    else:
        output.write_text(source_text, encoding="utf-8", newline="")
    exact = True
    if args.verify_package:
        from amiga_reversing.disasm.source_export import verify_source_export_package
        verification = verify_source_export_package(args.target, payload)
        payload["verification"] = verification
        exact = verification["exact"] is True
    if args.json:
        metadata = {key: value for key, value in payload.items() if key not in {"source_text", "package"}}
        metadata["output"] = str(output)
        print(json.dumps(metadata, indent=2, sort_keys=True))
    else:
        print(f"exported {output}" + (f" (package exact: {exact})" if args.verify_package else " (not verification)"))
    return 0 if exact else 3


if __name__ == "__main__":
    raise SystemExit(main())
