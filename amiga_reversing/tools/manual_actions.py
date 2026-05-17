from __future__ import annotations

import argparse
import json
from typing import cast

from amiga_reversing.disasm import server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List and invoke Command Catalog entries.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List catalog actions.")
    _add_context_args(list_parser)

    show_parser = subparsers.add_parser("show", help="Show one catalog action.")
    _add_context_args(show_parser)
    show_parser.add_argument("action_id")

    invoke_parser = subparsers.add_parser("invoke", help="Invoke a command catalog entry.")
    _add_context_args(invoke_parser)
    invoke_parser.add_argument("action_id")
    invoke_parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=JSON",
        help="Action parameter. Values are parsed as JSON when possible.",
    )

    args = parser.parse_args(argv)
    if args.command == "list":
        _print_json(_catalog(args))
        return 0
    if args.command == "show":
        commands = cast(list[dict[str, object]], _catalog(args)["commands"])
        for command in commands:
            if command.get("action_id") == args.action_id:
                _print_json(command)
                return 0
        raise SystemExit(f"Catalog command not found: {args.action_id}")
    if args.command == "invoke":
        body = {
            "command_id": args.action_id,
            "context": _context_body(args),
            "parameters": _parse_params(args.param),
        }
        payload = server.route_request(
            "POST",
            f"/api/projects/{args.project}/commands/execute",
            {},
            body,
        )
        _print_json(payload["data"])
        return 0
    raise SystemExit(f"Unsupported command: {args.command}")


def _add_context_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("project")
    parser.add_argument("--context", choices=("target", "review-item", "row", "element", "range"), default="target")
    parser.add_argument("--review-index", type=int)
    parser.add_argument("--locator", help="ListingRowLocator JSON for row or element context.")
    parser.add_argument("--locators", help="JSON list of ListingRowLocator objects for range context.")
    parser.add_argument("--item-id")
    parser.add_argument("--element-id")
    parser.add_argument("--element-kind")
    parser.add_argument("--operand-index", type=int)
    parser.add_argument("--symbol")
    parser.add_argument("--access")
    parser.add_argument("--value", type=int)


def _catalog(args: argparse.Namespace) -> dict[str, object]:
    query: dict[str, list[str]] = {"context": [args.context]}
    if args.review_index is not None:
        query["review_index"] = [str(args.review_index)]
    if args.item_id:
        query["item_id"] = [args.item_id]
    if args.locator:
        query["locator"] = [args.locator]
    if args.locators:
        query["locators"] = [args.locators]
    if args.element_kind:
        query["element_kind"] = [args.element_kind]
    if args.element_id:
        query["element_id"] = [args.element_id]
    if args.operand_index is not None:
        query["operand_index"] = [str(args.operand_index)]
    if args.symbol:
        query["symbol"] = [args.symbol]
    if args.access:
        query["access"] = [args.access]
    if args.value is not None:
        query["value"] = [str(args.value)]
    payload = server.route_request(
        "GET",
        f"/api/projects/{args.project}/commands",
        query,
    )
    return cast(dict[str, object], payload["data"])


def _context_body(args: argparse.Namespace) -> dict[str, object]:
    context: dict[str, object] = {"kind": args.context.replace("-", "_")}
    if args.review_index is not None:
        context["review_index"] = args.review_index
    if args.item_id:
        context["item_id"] = args.item_id
    if args.locator:
        context["locator"] = _parse_json_arg(args.locator, "--locator")
    if args.locators:
        context["locators"] = _parse_json_arg(args.locators, "--locators")
    if args.element_kind:
        context["element_kind"] = args.element_kind
    if args.element_id:
        context["element_id"] = args.element_id
    if args.operand_index is not None:
        context["operand_index"] = args.operand_index
    if args.symbol:
        context["symbol"] = args.symbol
    if args.access:
        context["access"] = args.access
    if args.value is not None:
        context["value"] = args.value
    return context


def _parse_params(values: list[str]) -> dict[str, object]:
    params: dict[str, object] = {}
    for value in values:
        name, separator, raw = value.partition("=")
        if not separator or not name:
            raise SystemExit(f"Invalid --param value: {value}")
        try:
            params[name] = json.loads(raw)
        except json.JSONDecodeError:
            params[name] = raw
    return params


def _parse_json_arg(value: str, name: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid {name} JSON: {value}") from exc


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
