"""MPW build recipe provenance parser for Classic Mac OS fixtures."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

_TARGET_SEPARATORS = "\u00c4\u00c5\u0192"
_LINK_ARG_OPTIONS = frozenset({"-o", "-t", "-c", "-rt", "-sg", "-sn"})
_SETFILE_ARG_OPTIONS = frozenset({"-t", "-c", "-a"})
_REZ_ARG_OPTIONS = frozenset({"-o"})


def parse_mpw_build_file(path: Path) -> dict[str, object]:
    text = path.read_bytes().decode("mac_roman")
    return parse_mpw_build_text(text, path=str(path))


def parse_mpw_build_text(text: str, *, path: str) -> dict[str, object]:
    variables: list[dict[str, object]] = []
    variables_by_name: dict[str, dict[str, object]] = {}
    targets: list[dict[str, object]] = []
    commands: list[dict[str, object]] = []
    object_recipes: list[dict[str, object]] = []
    products: dict[str, dict[str, object]] = {}
    current_target: str | None = None

    for logical in _logical_lines(text.splitlines()):
        raw_text = logical["text"]
        if not isinstance(raw_text, str):
            continue
        code = _strip_comment(raw_text).rstrip()
        if not code.strip():
            continue
        line = _int_value(logical.get("start_line"))
        line_end = _int_value(logical.get("end_line"))
        if line is None or line_end is None:
            continue

        variable = _parse_variable(code, line, line_end)
        if variable is not None:
            variables.append(variable)
            variables_by_name[str(variable["name"])] = variable
            continue

        target = _parse_target(code, variables_by_name, line, line_end)
        if target is not None:
            targets.append(target)
            current_target = str(target["target"])
            if current_target.endswith(".a.o"):
                object_recipes.append(_object_recipe(target))
            continue

        if current_target is None or not raw_text[:1].isspace():
            continue
        command = _parse_command(code, current_target, variables_by_name, line, line_end)
        if command is None:
            continue
        commands.append(command)
        _apply_command_to_product(products, command)

    return {
        "schema_version": 1,
        "kind": "mpw_build_provenance",
        "path": path,
        "provenance_scope": {
            "kind": "source_build_recipe",
            "source_view_provenance": True,
            "executable_import_provenance": False,
            "maps_to_observed_asm_code_resources": False,
            "byte_for_byte_roundtrip": False,
        },
        "variables": variables,
        "targets": targets,
        "object_recipes": object_recipes,
        "commands": commands,
        "products": list(products.values()),
    }


def _logical_lines(lines: list[str]) -> list[dict[str, object]]:
    logical: list[dict[str, object]] = []
    buffer = ""
    start_line = 1
    first_indent = ""
    for index, line in enumerate(lines, start=1):
        stripped_right = line.rstrip()
        if not buffer:
            start_line = index
            indent_match = re.match(r"\s*", line)
            first_indent = indent_match.group(0) if indent_match else ""
        continued = stripped_right.endswith(("\u00b6", "\u2202", "\\"))
        piece = stripped_right[:-1] if continued else stripped_right
        if buffer:
            buffer += " " + piece.strip()
        else:
            buffer = first_indent + piece.strip()
        if continued:
            continue
        logical.append({"start_line": start_line, "end_line": index, "text": buffer})
        buffer = ""
    if buffer:
        logical.append({"start_line": start_line, "end_line": len(lines), "text": buffer})
    return logical


def _parse_variable(text: str, line: int, line_end: int) -> dict[str, object] | None:
    match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", text)
    if not match:
        return None
    value = match.group(2).strip()
    return {
        "name": match.group(1),
        "value": value,
        "tokens": _tokens(value),
        "line": line,
        "line_end": line_end,
    }


def _parse_target(
    text: str,
    variables: dict[str, dict[str, object]],
    line: int,
    line_end: int,
) -> dict[str, object] | None:
    separator = f"[{_TARGET_SEPARATORS}]+"
    match = re.match(rf"\s*([^\s=]+)\s+{separator}\s*(.*?)\s*$", text)
    if not match:
        return None
    target_name = match.group(1)
    dependency_text = match.group(2).strip()
    return {
        "target": target_name,
        "dependencies": _expanded_tokens(dependency_text, variables, target_name),
        "line": line,
        "line_end": line_end,
    }


def _parse_command(
    text: str,
    target: str,
    variables: dict[str, dict[str, object]],
    line: int,
    line_end: int,
) -> dict[str, object] | None:
    expanded = _expand_variables(text, variables, target)
    tokens = _tokens(expanded)
    if not tokens:
        return None
    tool = tokens[0]
    lowered = tool.lower()
    if lowered == "asm":
        return _parse_asm_command(tokens, target, line, line_end)
    if lowered == "link":
        return _parse_link_command(tokens, target, line, line_end)
    if lowered == "setfile":
        return _parse_setfile_command(tokens, target, line, line_end)
    if lowered == "rez":
        return _parse_rez_command(tokens, target, line, line_end)
    return None


def _parse_asm_command(tokens: list[str], target: str, line: int, line_end: int) -> dict[str, object]:
    sources = [token for token in tokens[1:] if not token.startswith("-")]
    return {
        "tool": "Asm",
        "target": target,
        "line": line,
        "line_end": line_end,
        "source_inputs": sources,
        "object_outputs": [f"{source}.o" for source in sources if source.endswith(".a")],
        "options": [token for token in tokens[1:] if token.startswith("-")],
    }


def _parse_link_command(tokens: list[str], target: str, line: int, line_end: int) -> dict[str, object]:
    options, args = _option_arguments(tokens[1:], _LINK_ARG_OPTIONS)
    inputs = [token for token in args if token.endswith(".o")]
    library_inputs = [token for token in inputs if token.startswith("{Libraries}")]
    object_inputs = [token for token in inputs if token not in library_inputs]
    resource_type = options.get("-rt")
    return {
        "tool": "Link",
        "target": target,
        "line": line,
        "line_end": line_end,
        "object_inputs": object_inputs,
        "library_inputs": library_inputs,
        "output": options.get("-o"),
        "output_type": options.get("-t"),
        "output_creator": options.get("-c"),
        "resource_type": resource_type,
        "segment_names": _multi_options(tokens[1:], "-sn"),
        "segment_group": options.get("-sg"),
        "program_kind": _program_kind(options.get("-t"), resource_type),
        "options": [token for token in tokens[1:] if token.startswith("-")],
    }


def _parse_setfile_command(tokens: list[str], target: str, line: int, line_end: int) -> dict[str, object]:
    options, args = _option_arguments(tokens[1:], _SETFILE_ARG_OPTIONS)
    return {
        "tool": "SetFile",
        "target": target,
        "line": line,
        "line_end": line_end,
        "file": args[0] if args else None,
        "file_type": options.get("-t"),
        "creator": options.get("-c"),
        "attributes": options.get("-a"),
    }


def _parse_rez_command(tokens: list[str], target: str, line: int, line_end: int) -> dict[str, object]:
    options, args = _option_arguments(tokens[1:], _REZ_ARG_OPTIONS)
    return {
        "tool": "Rez",
        "target": target,
        "line": line,
        "line_end": line_end,
        "resource_inputs": [token for token in args if token.endswith(".r")],
        "output": options.get("-o"),
        "append": "-append" in tokens[1:],
        "options": [token for token in tokens[1:] if token.startswith("-")],
    }


def _object_recipe(target: dict[str, object]) -> dict[str, object]:
    dependencies = target.get("dependencies")
    deps = dependencies if isinstance(dependencies, list) else []
    object_name = target.get("target")
    primary_source = f"{object_name[:-2]}" if isinstance(object_name, str) and object_name.endswith(".o") else None
    source_inputs = [primary_source] if primary_source in deps else []
    return {
        "object": object_name,
        "source_inputs": source_inputs,
        "dependency_inputs": deps,
        "line": target.get("line"),
        "line_end": target.get("line_end"),
        "provenance_kind": "source_to_object_recipe",
        "binary_object_imported": False,
    }


def _new_product(target: str) -> dict[str, object]:
    return {
        "target": target,
        "source_view_provenance": True,
        "executable_import_provenance": False,
        "byte_for_byte_roundtrip": False,
        "link": None,
        "setfile": None,
        "rez": [],
    }


def _apply_command_to_product(products: dict[str, dict[str, object]], command: dict[str, object]) -> None:
    target = command.get("target")
    if not isinstance(target, str) or target.endswith(".a.o"):
        return
    product = products.setdefault(target, _new_product(target))
    tool = command.get("tool")
    if tool == "Link":
        product["link"] = command
    elif tool == "SetFile":
        product["setfile"] = command
    elif tool == "Rez":
        rez_entries = product.get("rez")
        if isinstance(rez_entries, list):
            rez_entries.append(command)


def _strip_comment(text: str) -> str:
    quote: str | None = None
    for index, char in enumerate(text):
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
        elif char == "#" and quote is None:
            return text[:index]
    return text


def _tokens(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _expanded_tokens(text: str, variables: dict[str, dict[str, object]], target: str) -> list[str]:
    return _tokens(_expand_variables(text, variables, target))


def _expand_variables(text: str, variables: dict[str, dict[str, object]], target: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name == "Targ":
            return target
        variable = variables.get(name)
        if variable is None:
            return match.group(0)
        value = variable.get("value")
        return str(value) if value is not None else ""

    previous = text
    while True:
        current = re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", replace, previous)
        if current == previous:
            return current
        previous = current


def _option_arguments(tokens: list[str], options_with_args: frozenset[str]) -> tuple[dict[str, str], list[str]]:
    options: dict[str, str] = {}
    args: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        lowered = token.lower()
        if lowered in options_with_args and index + 1 < len(tokens):
            options[lowered] = tokens[index + 1]
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        args.append(token)
        index += 1
    return options, args


def _multi_options(tokens: list[str], option_name: str) -> list[str]:
    values: list[str] = []
    index = 0
    while index < len(tokens) - 1:
        if tokens[index].lower() == option_name:
            values.append(tokens[index + 1])
            index += 2
            continue
        index += 1
    return values


def _program_kind(output_type: str | None, resource_type: str | None) -> str | None:
    if resource_type and resource_type.upper().startswith("DRVR="):
        return "driver"
    if output_type == "APPL":
        return "application"
    if output_type == "MPST":
        return "mpw_tool"
    return None


def _int_value(value: object) -> int | None:
    return value if isinstance(value, int) else None
