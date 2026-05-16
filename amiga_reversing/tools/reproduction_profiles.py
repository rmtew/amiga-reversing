from __future__ import annotations

import argparse
import json
from typing import cast

from amiga_reversing.disasm import server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List and set target reproduction profiles.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List built-in profiles for a project.")
    list_parser.add_argument("project")

    show_parser = subparsers.add_parser("show", help="Show the active reproduction policy.")
    show_parser.add_argument("project")

    set_parser = subparsers.add_parser("set", help="Set the active reproduction profile.")
    set_parser.add_argument("project")
    set_parser.add_argument("profile_id")

    args = parser.parse_args(argv)
    if args.command == "list":
        payload = server.route_request("GET", f"/api/projects/{args.project}/reproduction/profiles", {})
        _print_json(payload["data"])
        return 0
    if args.command == "show":
        payload = server.route_request("GET", f"/api/projects/{args.project}/reproduction/profile", {})
        _print_json(payload["data"])
        return 0
    if args.command == "set":
        payload = server.route_request(
            "POST",
            f"/api/projects/{args.project}/reproduction/profile",
            {},
            {"profile_id": args.profile_id},
        )
        _print_json(payload["data"])
        return 0
    raise SystemExit(f"Unsupported command: {cast(str, args.command)}")


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
