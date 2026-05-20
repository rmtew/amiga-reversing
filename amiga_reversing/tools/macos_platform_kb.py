from __future__ import annotations

import argparse
from pathlib import Path

from amiga_reversing.tools.docs_source_inventory import (
    build_docs_inventory_report,
    check_docs_inventory_report,
    format_docs_inventory_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report Classic Mac OS platform KB source inventory.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("report", help="Print Classic Mac OS source inventory report.")
    subparsers.add_parser("check", help="Fail on Classic Mac OS source inventory consistency issues.")
    args = parser.parse_args(argv)

    report = build_report(PROJECT_ROOT)
    if args.command == "report":
        print(format_report(report))
        return 0
    if args.command == "check":
        violations = check_report(report)
        if violations:
            print("Classic Mac OS platform KB check failed:")
            for violation in violations:
                print(f"  - {violation}")
            return 1
        print("Classic Mac OS platform KB check passed.")
        return 0
    raise SystemExit(f"Unsupported command: {args.command}")


def build_report(project_root: Path) -> dict[str, object]:
    return build_docs_inventory_report(project_root, project_root / "knowledge" / "macos_source_inventory.json")


def check_report(report: dict[str, object]) -> list[str]:
    return check_docs_inventory_report(report)


def format_report(report: dict[str, object]) -> str:
    return format_docs_inventory_report(report, title="Classic Mac OS Platform KB")


if __name__ == "__main__":
    raise SystemExit(main())
