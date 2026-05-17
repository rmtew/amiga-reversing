from __future__ import annotations

import argparse
import json
from typing import cast

from amiga_reversing.disasm import server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect and configure runtime-aware oracle tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("runtimes", help="List runtime tools.")
    subparsers.add_parser("tools", help="List functional tools.")

    capability = subparsers.add_parser("capability", help="Resolve a tool capability.")
    capability.add_argument("capability_id")

    project_capabilities = subparsers.add_parser("project-capabilities", help="List tool capabilities for a project oracle context.")
    project_capabilities.add_argument("project")
    project_capabilities.add_argument("--profile-id")
    project_capabilities.add_argument("--oracle-modes")

    configure_path = subparsers.add_parser("configure-path", help="Set or clear a configured tool path.")
    configure_path.add_argument("kind", choices=("runtime", "functional"))
    configure_path.add_argument("tool_id")
    configure_path.add_argument("path", nargs="?")

    args = parser.parse_args(argv)
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
    if args.command == "project-capabilities":
        query = _query(profile_id=args.profile_id, oracle_modes=args.oracle_modes)
        payload = server.route_request("GET", f"/api/projects/{args.project}/tool-capabilities", query)
        _print_json(payload["data"])
        return 0
    if args.command == "configure-path":
        payload = server.route_request(
            "POST",
            "/api/tools/configuration/path",
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
