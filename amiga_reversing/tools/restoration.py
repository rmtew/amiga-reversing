"""Operate the shared restoration service from a shell."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from amiga_reversing.disasm.restoration_client import (
    RestorationClient,
    RestorationClientError,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", default="http://127.0.0.1:8123")
    parser.add_argument("--target", required=True)
    parser.add_argument(
        "operation",
        choices=(
            "state",
            "export",
            "query",
            "inspect",
            "interpret",
            "interpret_batch",
            "verify",
            "probe",
            "review",
            "review_batch",
            "history",
            "rollback",
        ),
    )
    parser.add_argument(
        "--request", type=Path, help="JSON operation parameters (use - for stdin)"
    )
    parser.add_argument("--assembler-profile", choices=("vasm", "devpac"))
    parser.add_argument("--binary-assets", action="store_true", default=None)
    parser.add_argument("--structure-macros", action="store_true", default=None)
    parser.add_argument("--minimum-asset-size", type=int)
    parser.add_argument("--expected-revision")
    parser.add_argument(
        "--kind",
        choices=(
            "symbols",
            "references",
            "fields",
            "instructions",
            "edges",
            "functions",
            "gaps",
            "typed_pointers",
        ),
    )
    parser.add_argument("--query")
    parser.add_argument(
        "--relation",
        choices=(
            "callers",
            "callees",
            "ranges",
            "owned_blocks",
            "unresolved_transfers",
            "entry_evidence",
            "name_evidence",
        ),
    )
    parser.add_argument("--symbol")
    parser.add_argument("--section-index", type=int)
    parser.add_argument("--row-kind", choices=("instruction", "label", "data"))
    parser.add_argument("--source-offset", type=lambda x: int(x, 0))
    parser.add_argument("--end-offset", type=lambda x: int(x, 0))
    parser.add_argument("--struct-name")
    parser.add_argument("--exceptions-only", action="store_true", default=None)
    parser.add_argument("--field-offset", type=lambda x: int(x, 0))
    parser.add_argument("--direction", choices=("incoming", "outgoing", "both"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--cursor")
    args = parser.parse_args(argv)
    try:
        parameters = {}
        if args.request:
            parameters = json.loads(
                sys.stdin.read()
                if str(args.request) == "-"
                else args.request.read_text(encoding="utf-8")
            )
            if not isinstance(parameters, dict) or "operation" in parameters:
                raise ValueError(
                    "Request must be an object of parameters without operation"
                )
        for name in (
            "assembler_profile",
            "binary_assets",
            "structure_macros",
            "minimum_asset_size",
            "expected_revision",
            "kind",
            "relation",
            "query",
            "symbol",
            "section_index",
            "source_offset",
            "row_kind",
            "end_offset",
            "struct_name",
            "exceptions_only",
            "field_offset",
            "direction",
            "limit",
            "cursor",
        ):
            value = getattr(args, name)
            if value is not None:
                parameters[name] = value
        result = RestorationClient(args.server).call(
            args.target, args.operation, **parameters
        )
    except RestorationClientError as exc:
        print(json.dumps(exc.payload, ensure_ascii=False), file=sys.stderr)
        return 1
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
