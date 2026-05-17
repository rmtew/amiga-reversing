from __future__ import annotations

import argparse
import json
from typing import cast

from amiga_reversing.disasm import server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect and configure runtime-aware oracle tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("registry", help="Show configured tool registry.")

    subparsers.add_parser("runtimes", help="List runtime tools.")
    subparsers.add_parser("tools", help="List functional tools.")

    capability = subparsers.add_parser("capability", help="Resolve a tool capability.")
    capability.add_argument("capability_id")

    project_availability = subparsers.add_parser("project-availability", help="List availability for a project oracle context.")
    project_availability.add_argument("project")
    project_availability.add_argument("--profile-id")
    project_availability.add_argument("--oracle-modes")

    set_path = subparsers.add_parser("set-path", help="Set or clear a configured tool path.")
    set_path.add_argument("kind", choices=("runtime", "functional"))
    set_path.add_argument("tool_id")
    set_path.add_argument("path", nargs="?")

    args = parser.parse_args(argv)
    if args.command == "registry":
        payload = server.route_request("GET", "/api/tool-registry", {})
        _print_json(payload["data"])
        return 0
    if args.command == "runtimes":
        payload = server.route_request("GET", "/api/tools/runtimes", {})
        _print_json(payload["data"])
        return 0
    if args.command == "tools":
        payload = server.route_request("GET", "/api/tools/functional", {})
        _print_json(payload["data"])
        return 0
    if args.command == "capability":
        payload = server.route_request("GET", f"/api/tools/capabilities/{args.capability_id}", {})
        _print_json(payload["data"])
        return 0
    if args.command == "project-availability":
        query = _query(profile_id=args.profile_id, oracle_modes=args.oracle_modes)
        payload = server.route_request("GET", f"/api/projects/{args.project}/tool-availability", query)
        _print_json(payload["data"])
        return 0
    if args.command == "set-path":
        payload = server.route_request(
            "POST",
            "/api/tools/path",
            {},
            {"kind": args.kind, "tool_id": args.tool_id, "path": args.path},
        )
        _print_json(payload["data"])
        return 0
    raise SystemExit(f"Unsupported command: {cast(str, args.command)}")


def _query(**values: str | None) -> dict[str, list[str]]:
    return {key: [value] for key, value in values.items() if value}


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
