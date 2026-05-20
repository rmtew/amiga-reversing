"""Source-level Classic Mac OS Rez/resource metadata parser."""

from __future__ import annotations

import ast
import operator
import re
from collections.abc import Mapping

_INT_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.floordiv,
}

_INITIAL_RESOURCE_TYPES = frozenset({"MBAR", "MENU", "ALRT", "DITL", "WIND", "RECT", "SIZE", "cmdo"})


def parse_resource_constants(c_header_text: str, asm_include_text: str) -> dict[str, object]:
    constants: list[dict[str, object]] = []
    by_name: dict[str, dict[str, object]] = {}
    for constant in _c_defines(c_header_text):
        constants.append(constant)
        by_name[str(constant["name"])] = constant
    for constant in _asm_equates(asm_include_text):
        name = str(constant["name"])
        if name in by_name:
            by_name[name]["asm_value"] = constant.get("value")
            by_name[name]["asm_expression"] = constant.get("expression")
            by_name[name]["asm_line"] = constant.get("line")
            continue
        constants.append(constant)
        by_name[name] = constant
    return {"constants": constants, "by_name": by_name}


def parse_rez_source(
    text: str,
    *,
    path: str,
    constants: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    constants_by_name = constants or {}
    resources: list[dict[str, object]] = []
    type_declarations: list[dict[str, object]] = []
    block_comment = False
    active_resource: dict[str, object] | None = None
    brace_depth = 0

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        code, block_comment = _strip_c_comment(raw_line, block_comment)
        if active_resource is not None:
            brace_depth += code.count("{") - code.count("}")
            if brace_depth <= 0:
                active_resource["line_end"] = line_number
                active_resource = None
            continue

        type_match = re.match(r"\s*type\s+'([^']+)'\s*\{", code)
        if type_match:
            type_declarations.append({"type": type_match.group(1), "line": line_number})
            continue

        resource_match = re.match(r"\s*resource\s+'([^']+)'\s*\(([^)]*)\)\s*\{", code)
        if resource_match:
            resource_type = resource_match.group(1)
            args = [part.strip() for part in resource_match.group(2).split(",") if part.strip()]
            id_expression = args[0] if args else ""
            resource = {
                "type": resource_type,
                "symbolic_id": id_expression if not _int_literal(id_expression) else None,
                "id_expression": id_expression,
                "numeric_id": _resolve_constant_or_int(id_expression, constants_by_name),
                "attributes": args[1:],
                "line": line_number,
                "line_end": line_number,
                "source": path,
                "initial_type": resource_type in _INITIAL_RESOURCE_TYPES,
            }
            resources.append(resource)
            active_resource = resource
            brace_depth = code.count("{") - code.count("}")
            if brace_depth <= 0:
                active_resource = None
            continue

    return {
        "path": path,
        "type_declarations": type_declarations,
        "resources": resources,
    }


def build_resource_xrefs(
    source_files: Mapping[str, str],
    resources: list[Mapping[str, object]],
    constants: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    resources_by_symbol: dict[str, list[Mapping[str, object]]] = {}
    for resource in resources:
        symbolic_id = resource.get("symbolic_id")
        if isinstance(symbolic_id, str):
            resources_by_symbol.setdefault(symbolic_id, []).append(resource)
    resources_by_type_and_id: dict[tuple[str, int], list[Mapping[str, object]]] = {}
    for resource in resources:
        resource_type = resource.get("type")
        numeric_id = resource.get("numeric_id")
        if isinstance(resource_type, str) and isinstance(numeric_id, int):
            resources_by_type_and_id.setdefault((resource_type, numeric_id), []).append(resource)

    xrefs: list[dict[str, object]] = []
    for path, text in source_files.items():
        pending_symbols: list[dict[str, object]] = []
        pending_resource_types: list[dict[str, object]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            code = _strip_asm_comment(line)
            for symbol in re.findall(r"#([A-Za-z_][A-Za-z0-9_]*)", code):
                pending_symbols.append({"symbol": symbol, "line": line_number})
            for resource_type in re.findall(r"#'([A-Za-z0-9 ]{4})'", code):
                pending_resource_types.append({"type": resource_type, "line": line_number})

            call_name = _source_call_name(code)
            if call_name is None:
                _trim_pending(pending_symbols, line_number)
                _trim_pending(pending_resource_types, line_number)
                continue
            if call_name == "_GetResource":
                resource_type = _nearest_pending(pending_resource_types, line_number)
                xrefs.append(
                    {
                        "source": path,
                        "line": line_number,
                        "call": call_name,
                        "resource_type": None if resource_type is None else resource_type["type"],
                        "id_source": "caller_supplied_parameter",
                        "resource": None,
                    }
                )
            else:
                pending = _nearest_pending(pending_symbols, line_number)
                if pending is not None:
                    symbol = str(pending["symbol"])
                    selected_resource = _resource_for_call(call_name, resources_by_symbol.get(symbol, []))
                    xrefs.append(
                        {
                            "source": path,
                            "line": line_number,
                            "call": call_name,
                            "symbolic_id": symbol,
                            "numeric_id": _resolve_constant_or_int(symbol, constants),
                            "resource": _resource_ref(selected_resource),
                        }
                    )
            _trim_pending(pending_symbols, line_number)
            _trim_pending(pending_resource_types, line_number)
    return xrefs


def _c_defines(text: str) -> list[dict[str, object]]:
    constants: list[dict[str, object]] = []
    block_comment = False
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line, block_comment = _strip_c_comment(raw_line, block_comment)
        match = re.match(r"\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$", line)
        if not match:
            continue
        expression = match.group(2).strip()
        constants.append(
            {
                "name": match.group(1),
                "expression": expression,
                "value": _safe_int_expression(expression),
                "source": "c_header",
                "line": line_number,
            }
        )
    return constants


def _asm_equates(text: str) -> list[dict[str, object]]:
    constants: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_asm_comment(raw_line)
        match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s+EQU\s+(.+?)\s*$", line, re.IGNORECASE)
        if not match:
            continue
        expression = match.group(2).strip()
        constants.append(
            {
                "name": match.group(1),
                "expression": expression,
                "value": _safe_int_expression(expression),
                "source": "asm_include",
                "line": line_number,
            }
        )
    return constants


def _strip_c_comment(line: str, in_block: bool) -> tuple[str, bool]:
    out = ""
    index = 0
    while index < len(line):
        if in_block:
            end = line.find("*/", index)
            if end < 0:
                return out, True
            index = end + 2
            in_block = False
            continue
        if line.startswith("/*", index):
            in_block = True
            index += 2
            continue
        if line.startswith("//", index):
            break
        out += line[index]
        index += 1
    return out, in_block


def _strip_asm_comment(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith("*"):
        return ""
    quote: str | None = None
    for index, char in enumerate(line):
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
        elif char == ";" and quote is None:
            return line[:index]
    return line


def _safe_int_expression(expression: str, names: Mapping[str, int] | None = None) -> int | None:
    cleaned = re.sub(r"\$([0-9A-Fa-f]+)", r"0x\1", expression.strip())
    try:
        node = ast.parse(cleaned, mode="eval").body
    except SyntaxError:
        return None
    return _eval_int_node(node, names or {})


def _eval_int_node(node: ast.AST, names: Mapping[str, int]) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.Name):
        return names.get(node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _eval_int_node(node.operand, names)
        return None if value is None else -value
    if isinstance(node, ast.BinOp):
        left = _eval_int_node(node.left, names)
        right = _eval_int_node(node.right, names)
        operation = _INT_OPERATORS.get(type(node.op))
        if left is None or right is None or operation is None:
            return None
        return int(operation(left, right))
    return None


def _int_literal(expression: str) -> bool:
    return _safe_int_expression(expression) is not None


def _resolve_constant_or_int(
    expression: str,
    constants: Mapping[str, Mapping[str, object]],
) -> int | None:
    if expression in constants:
        value = constants[expression].get("value")
        return value if isinstance(value, int) else None
    resolved_names: dict[str, int] = {}
    for name, constant in constants.items():
        value = constant.get("value")
        if isinstance(value, int):
            resolved_names[name] = value
    return _safe_int_expression(expression, resolved_names)


def _source_call_name(code: str) -> str | None:
    for call_name in ("_GetNewWindow", "_GetNewMBar", "_GetResource", "_Alert", "GoGetRect"):
        if re.search(rf"\b{re.escape(call_name)}\b", code):
            return call_name
    return None


def _resource_for_call(call_name: str, resources: list[Mapping[str, object]]) -> Mapping[str, object] | None:
    preferred_type = {
        "_GetNewWindow": "WIND",
        "_GetNewMBar": "MBAR",
        "_Alert": "ALRT",
        "GoGetRect": "RECT",
    }.get(call_name)
    if preferred_type is not None:
        for resource in resources:
            if resource.get("type") == preferred_type:
                return resource
    return resources[0] if resources else None


def _trim_pending(pending: list[dict[str, object]], line_number: int) -> None:
    kept: list[dict[str, object]] = []
    for entry in pending:
        entry_line = entry.get("line")
        if isinstance(entry_line, int) and line_number - entry_line <= 6:
            kept.append(entry)
    pending[:] = kept


def _nearest_pending(pending: list[dict[str, object]], line_number: int) -> dict[str, object] | None:
    recent: list[dict[str, object]] = []
    for entry in pending:
        entry_line = entry.get("line")
        if isinstance(entry_line, int) and entry_line <= line_number:
            recent.append(entry)
    return recent[-1] if recent else None


def _resource_ref(resource: Mapping[str, object] | None) -> dict[str, object] | None:
    if resource is None:
        return None
    return {
        "type": resource.get("type"),
        "symbolic_id": resource.get("symbolic_id"),
        "numeric_id": resource.get("numeric_id"),
        "source": resource.get("source"),
        "line": resource.get("line"),
    }
