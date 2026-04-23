from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INCLUDES_PATH = ROOT / "knowledge" / "amiga_ndk_includes_parsed.json"
OTHER_PATH = ROOT / "knowledge" / "amiga_ndk_other_parsed.json"
CORRECTIONS_PATH = ROOT / "knowledge" / "amiga_ndk_corrections.json"
NAMING_RULES_PATH = ROOT / "knowledge" / "naming_rules.json"
OUTPUT_DIR = ROOT / "src" / "generated"
HEADER_PATH = OUTPUT_DIR / "amiga_os_runtime.h"
SOURCE_PATH = OUTPUT_DIR / "amiga_os_runtime.c"
VENDORED_AMIGA_INCLUDE_ROOT = ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"

NAME_DOMAIN_LIBRARY = 1
NAME_DOMAIN_BASE = 2
NAME_DOMAIN_FUNCTION = 3
NAME_DOMAIN_SYMBOL = 4
NAME_DOMAIN_INCLUDE = 5
NAME_DOMAIN_TYPE = 6
NAME_DOMAIN_STRUCT = 7
NAME_DOMAIN_FIELD = 8
NAME_DOMAIN_SEMANTIC_KIND = 9
NAME_DOMAIN_VALUE_DOMAIN = 10

AMIGA_REGISTER_KIND_NONE = 0
AMIGA_REGISTER_KIND_DATA = 1
AMIGA_REGISTER_KIND_ADDRESS = 2

AMIGA_VALUE_DOMAIN_KIND_NONE = 0
AMIGA_VALUE_DOMAIN_KIND_ENUM = 1
AMIGA_VALUE_DOMAIN_KIND_FLAGS = 2

AMIGA_VALUE_DOMAIN_EXACT_MATCH_NONE = 0
AMIGA_VALUE_DOMAIN_EXACT_MATCH_ERROR = 1

AMIGA_VALUE_DOMAIN_COMPOSITION_NONE = 0
AMIGA_VALUE_DOMAIN_COMPOSITION_OR = 1
AMIGA_VALUE_DOMAIN_COMPOSITION_BIT_OR = 2

AMIGA_VALUE_DOMAIN_REMAINDER_NONE = 0
AMIGA_VALUE_DOMAIN_REMAINDER_ERROR = 1

def c_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def pascal_case(text: str) -> str:
    return "".join(part.capitalize() for part in text.split("_"))


def enum_token(text: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").upper()
    if not token:
        token = "VALUE"
    if token[0].isdigit():
        token = f"_{token}"
    return token


def build_name_domain_meta(name_domains: list[tuple[int, str, list[str]]], prefix: str) -> list[dict]:
    items: list[dict] = []
    for domain_kind, label, values in name_domains:
        enum_prefix = f"{prefix}_{label.upper()}_ID"
        enum_values: dict[str, str] = {}
        used: set[str] = set()
        for value in values:
            base_name = f"{enum_prefix}_{enum_token(value)}"
            name = base_name
            suffix = 2
            while name in used:
                name = f"{base_name}_{suffix}"
                suffix += 1
            used.add(name)
            enum_values[value] = name
        items.append({
            "kind": domain_kind,
            "label": label,
            "values": values,
            "enum_type": f"{prefix.title().replace('_', '')}{pascal_case(label)}Id",
            "enum_prefix": enum_prefix,
            "enum_values": enum_values,
            "id_map": {value: index for index, value in enumerate(values)},
            "none_id": len(values),
        })
    return items


def find_name_domain_meta(name_domain_meta: list[dict], label: str) -> dict:
    for item in name_domain_meta:
        if item["label"] == label:
            return item
    raise KeyError(label)


def name_id_literal(name_domain_meta: list[dict], label: str, value: str | None) -> str:
    meta = find_name_domain_meta(name_domain_meta, label)
    if value is None:
        return f"{meta['enum_prefix']}_NONE"
    return meta["enum_values"][value]


def naming_patterns(naming_rules_payload: dict) -> list[dict]:
    patterns = naming_rules_payload.get("patterns", [])
    return [pattern for pattern in patterns if isinstance(pattern, dict)]


def naming_trivial_functions(naming_rules_payload: dict) -> list[str]:
    functions = naming_rules_payload.get("trivial_functions", [])
    return [function for function in functions if isinstance(function, str) and function]


def resident_vector_prefix_rows(includes_payload: dict) -> list[tuple[str, int, str]]:
    prefixes = includes_payload.get("_meta", {}).get("resident_vector_prefixes", {})
    rows: list[tuple[str, int, str]] = []
    if not isinstance(prefixes, dict):
        return rows
    for target_type, values in sorted(prefixes.items()):
        if not isinstance(target_type, str) or not isinstance(values, list):
            continue
        for slot_index, symbol_name in enumerate(values):
            if isinstance(symbol_name, str) and symbol_name:
                rows.append((target_type, slot_index, symbol_name))
    return rows


def resident_entry_seed_rows(includes_payload: dict) -> list[dict[str, str | None]]:
    seed_map = includes_payload.get("_meta", {}).get("resident_entry_register_seeds", {})
    rows: list[dict[str, str | None]] = []
    if not isinstance(seed_map, dict):
        return rows
    for target_type, role_map in sorted(seed_map.items()):
        if not isinstance(target_type, str) or not isinstance(role_map, dict):
            continue
        for role, specs in sorted(role_map.items()):
            if not isinstance(role, str) or not isinstance(specs, list):
                continue
            for spec in specs:
                if not isinstance(spec, dict):
                    continue
                register = spec.get("register")
                kind = spec.get("kind")
                if not isinstance(register, str) or not isinstance(kind, str):
                    continue
                rows.append({
                    "target_type": target_type,
                    "role": role,
                    "register": register,
                    "kind": kind,
                    "struct_name": spec.get("struct_name") if isinstance(spec.get("struct_name"), str) else None,
                    "context_name": spec.get("context_name") if isinstance(spec.get("context_name"), str) else None,
                    "named_base_source": spec.get("named_base_source") if isinstance(spec.get("named_base_source"), str) else None,
                    "named_base_name": spec.get("named_base_name") if isinstance(spec.get("named_base_name"), str) else None,
                })
    return rows


def parse_register_name(name: str | None) -> tuple[int, int]:
    if not isinstance(name, str) or len(name) != 2:
        return AMIGA_REGISTER_KIND_NONE, 0
    if name[0] in {"D", "d"} and "0" <= name[1] <= "7":
        return AMIGA_REGISTER_KIND_DATA, int(name[1])
    if name[0] in {"A", "a"} and "0" <= name[1] <= "7":
        return AMIGA_REGISTER_KIND_ADDRESS, int(name[1])
    return AMIGA_REGISTER_KIND_NONE, 0


def value_domain_kind_literal(kind: str | None) -> str:
    if kind == "enum":
        return "AMIGA_OS_VALUE_DOMAIN_KIND_ENUM"
    if kind == "flags":
        return "AMIGA_OS_VALUE_DOMAIN_KIND_FLAGS"
    return "AMIGA_OS_VALUE_DOMAIN_KIND_NONE"


def value_domain_exact_match_literal(policy: str | None) -> str:
    if policy == "error":
        return "AMIGA_OS_VALUE_DOMAIN_EXACT_MATCH_ERROR"
    return "AMIGA_OS_VALUE_DOMAIN_EXACT_MATCH_NONE"


def value_domain_composition_literal(policy: str | None) -> str:
    if policy == "or":
        return "AMIGA_OS_VALUE_DOMAIN_COMPOSITION_OR"
    if policy == "bit_or":
        return "AMIGA_OS_VALUE_DOMAIN_COMPOSITION_BIT_OR"
    return "AMIGA_OS_VALUE_DOMAIN_COMPOSITION_NONE"


def value_domain_remainder_literal(policy: str | None) -> str:
    if policy == "error":
        return "AMIGA_OS_VALUE_DOMAIN_REMAINDER_ERROR"
    return "AMIGA_OS_VALUE_DOMAIN_REMAINDER_NONE"


def normalize_include_path(path: str | None) -> str | None:
    if not isinstance(path, str) or not path:
        return None
    normalized = path.replace("\\", "/").strip()
    if ":" in normalized:
        return None
    return normalized.lower()


def load_assembler_include_symbols(include_root: Path = VENDORED_AMIGA_INCLUDE_ROOT) -> dict[str, set[str]]:
    import sys

    symbols_by_path: dict[str, set[str]] = {}
    if not include_root.is_dir():
        return symbols_by_path
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.scripts.kb.ndk_parser import collect_raw_constants_from_include_dir, scan_type_macros

    include_root_str = str(include_root)
    constant_source_file_sets: dict[str, set[str]] = {}
    raw_constants, _constant_source_files, parsed_include_paths = collect_raw_constants_from_include_dir(
        include_root_str,
        scan_type_macros(include_root_str),
        constant_source_file_sets,
    )
    for include_path in parsed_include_paths:
        relative_path = Path(include_path).relative_to(include_root).as_posix().lower()
        symbols_by_path[relative_path] = set()
    for symbol_name in raw_constants:
        for source_file in constant_source_file_sets.get(symbol_name, set()):
            relative_path = Path(source_file).relative_to(include_root).as_posix().lower()
            symbols_by_path.setdefault(relative_path, set()).add(symbol_name)
    return symbols_by_path


def include_defines_assembler_symbol(
        symbols_by_path: dict[str, set[str]],
        include_path: str,
        symbol_name: str) -> bool:
    symbols = symbols_by_path.get(include_path)
    return symbols is None or symbol_name in symbols


def struct_field_offset(payload: dict, struct_name: str, field_name: str) -> int | None:
    for field in payload.get("structs", {}).get(struct_name, {}).get("fields", []):
        if not isinstance(field, dict):
            continue
        if field.get("name") == field_name and isinstance(field.get("offset"), int):
            return int(field["offset"])
    return None


def reg_name(payload: dict | None, key: str) -> str | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def infer_struct_name_from_type(type_name: str | None, includes_payload: dict, other_payload: dict) -> str | None:
    match = re.match(r"^struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\*$", type_name or "")
    if match is None:
        return None
    raw_name = match.group(1)
    struct_name_map = other_payload.get("_meta", {}).get("struct_name_map", {})
    canonical_name = struct_name_map.get(raw_name, raw_name) if isinstance(struct_name_map, dict) else raw_name
    structs = includes_payload.get("structs", {})
    if isinstance(structs, dict) and canonical_name in structs:
        return canonical_name
    return None


def build_api_input_value_domain_map(includes_payload: dict, corrections_payload: dict) -> dict[tuple[str, str, str], str]:
    rows: dict[tuple[str, str, str], str] = {}
    for payload in (includes_payload, corrections_payload):
        bindings = payload.get("_meta", {}).get("api_input_value_bindings", [])
        if not isinstance(bindings, list):
            continue
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            library_name = binding.get("library")
            function_name = binding.get("function")
            input_name = binding.get("input")
            domain_name = binding.get("domain")
            if not isinstance(library_name, str) or not library_name:
                continue
            if not isinstance(function_name, str) or not function_name:
                continue
            if not isinstance(input_name, str) or not input_name:
                continue
            if not isinstance(domain_name, str) or not domain_name:
                continue
            rows[(library_name, function_name, input_name)] = domain_name
    if _has_alert_number_domain(includes_payload):
        rows.setdefault(("exec.library", "Alert", "alertNum"), "exec.alert.number")
    return rows


def build_api_input_semantic_kind_map(includes_payload: dict, corrections_payload: dict) -> dict[tuple[str, str, str], str]:
    rows: dict[tuple[str, str, str], str] = {}
    for payload in (includes_payload, corrections_payload):
        bindings = payload.get("_meta", {}).get("api_input_semantic_assertions", [])
        if not isinstance(bindings, list):
            continue
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            library_name = binding.get("library")
            function_name = binding.get("function")
            input_name = binding.get("input")
            semantic_kind = binding.get("semantic_kind")
            if not isinstance(library_name, str) or not library_name:
                continue
            if not isinstance(function_name, str) or not function_name:
                continue
            if not isinstance(input_name, str) or not input_name:
                continue
            if not isinstance(semantic_kind, str) or not semantic_kind:
                continue
            rows[(library_name, function_name, input_name)] = semantic_kind
    return rows


def build_api_input_type_override_map(corrections_payload: dict) -> dict[tuple[str, str, str], tuple[str, str | None]]:
    rows: dict[tuple[str, str, str], tuple[str, str | None]] = {}
    bindings = corrections_payload.get("_meta", {}).get("api_input_type_overrides", [])
    if not isinstance(bindings, list):
        return rows
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        library_name = binding.get("library")
        function_name = binding.get("function")
        input_name = binding.get("input")
        type_name = binding.get("type")
        struct_name = binding.get("i_struct")
        if not isinstance(library_name, str) or not library_name:
            continue
        if not isinstance(function_name, str) or not function_name:
            continue
        if not isinstance(input_name, str) or not input_name:
            continue
        if not isinstance(type_name, str) or not type_name:
            continue
        rows[(library_name, function_name, input_name)] = (
            type_name,
            struct_name if isinstance(struct_name, str) and struct_name else None,
        )
    return rows


def build_struct_field_value_domain_rows(includes_payload: dict,
                                         corrections_payload: dict) -> list[tuple[str, str, str | None, str]]:
    rows: dict[tuple[str, str, str | None], str] = {}
    for payload in (includes_payload, corrections_payload):
        bindings = payload.get("_meta", {}).get("struct_field_value_bindings", [])
        if not isinstance(bindings, list):
            continue
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            struct_name = binding.get("struct")
            field_name = binding.get("field")
            context_name = binding.get("context_name")
            domain_name = binding.get("domain")
            if not isinstance(struct_name, str) or not struct_name:
                continue
            if not isinstance(field_name, str) or not field_name:
                continue
            if context_name is not None and (not isinstance(context_name, str) or not context_name):
                context_name = None
            if not isinstance(domain_name, str) or not domain_name:
                continue
            rows[(struct_name, field_name, context_name)] = domain_name
    return sorted(((struct_name, field_name, context_name, domain_name)
                   for (struct_name, field_name, context_name), domain_name in rows.items()),
                  key=lambda row: (row[0], row[1], "" if row[2] is None else row[2], row[3]))


def build_merged_value_domains(includes_payload: dict, corrections_payload: dict) -> dict[str, dict]:
    merged: dict[str, dict] = {}
    for payload in (includes_payload, corrections_payload):
        domains = payload.get("_meta", {}).get("value_domains", {})
        if not isinstance(domains, dict):
            continue
        for domain_name, domain_info in domains.items():
            if isinstance(domain_name, str) and domain_name and isinstance(domain_info, dict):
                merged[domain_name] = domain_info
    constants = includes_payload.get("constants", {})
    if isinstance(constants, dict):
        def add_domain(name: str, kind: str, members: list[str], *, exact: bool = False) -> None:
            present = [
                member for member in members
                if isinstance(constants.get(member), dict)
                and isinstance(constants[member].get("value"), int)
            ]
            if present and name not in merged:
                merged[name] = {
                    "kind": kind,
                    "members": present,
                    **({"exact_match_policy": "error"} if exact else {}),
                    **({"composition": "bit_or"} if kind == "flags" else {}),
                }

        add_domain("exec.resident.matchword", "enum", ["RTC_MATCHWORD"], exact=True)
        add_domain("exec.resident.flags", "flags", [
            "RTF_COLDSTART",
            "RTF_SINGLETASK",
            "RTF_AFTERDOS",
            "RTF_AUTOINIT",
        ])
        add_domain("exec.node.type", "enum", [
            "NT_UNKNOWN",
            "NT_TASK",
            "NT_INTERRUPT",
            "NT_DEVICE",
            "NT_MSGPORT",
            "NT_MESSAGE",
            "NT_FREEMSG",
            "NT_REPLYMSG",
            "NT_RESOURCE",
            "NT_LIBRARY",
            "NT_MEMORY",
            "NT_SOFTINT",
            "NT_FONT",
            "NT_PROCESS",
            "NT_SEMAPHORE",
            "NT_SIGNALSEM",
            "NT_BOOTNODE",
            "NT_KICKMEM",
            "NT_GRAPHICS",
            "NT_DEATHMESSAGE",
        ], exact=True)
        add_domain("exec.library.flags", "flags", [
            "LIBF_SUMMING",
            "LIBF_CHANGED",
            "LIBF_SUMUSED",
            "LIBF_DELEXP",
            "LIBF_EXP0CNT",
        ])
        alert_members = _alert_number_domain_members(includes_payload)
        if alert_members and "exec.alert.number" not in merged:
            merged["exec.alert.number"] = {
                "kind": "flags",
                "members": alert_members,
                "composition": "bit_or",
                "remainder_policy": "error",
            }
    return merged


def _constant_include_path(constant_info: dict) -> str | None:
    owner = constant_info.get("owner")
    if isinstance(owner, dict):
        include_path = owner.get("assembler_include_path") or owner.get("canonical_include_path")
        if isinstance(include_path, str) and include_path:
            return include_path.replace("\\", "/").lower()
    return None


def _alert_number_domain_members(includes_payload: dict) -> list[str]:
    constants = includes_payload.get("constants", {})
    if not isinstance(constants, dict):
        return []
    rows: list[str] = []
    for symbol_name, constant_info in constants.items():
        if not isinstance(symbol_name, str) or not symbol_name.startswith(("AT_", "AG_", "AO_", "AN_")):
            continue
        if not isinstance(constant_info, dict) or not isinstance(constant_info.get("value"), int):
            continue
        if _constant_include_path(constant_info) != "exec/alerts.i":
            continue
        rows.append(symbol_name)
    return sorted(rows)


def _has_alert_number_domain(includes_payload: dict) -> bool:
    return bool(_alert_number_domain_members(includes_payload))


def build_constant_rows(includes_payload: dict) -> list[tuple[str, int, str | None]]:
    constants = includes_payload.get("constants", {})
    rows: list[tuple[str, int, str | None]] = []
    if not isinstance(constants, dict):
        return rows
    for symbol_name, info in sorted(constants.items()):
        if not isinstance(symbol_name, str) or not symbol_name:
            continue
        if not isinstance(info, dict):
            continue
        value = info.get("value")
        owner = info.get("owner")
        if not isinstance(value, int):
            continue
        include_path = normalize_include_path(owner.get("assembler_include_path") if isinstance(owner, dict) else None)
        rows.append((symbol_name, int(value), include_path))
    existing = {symbol_name for symbol_name, _, _ in rows}
    missing = sorted({
        symbol_name
        for target_type, _slot_index, symbol_name in resident_vector_prefix_rows(includes_payload)
        if target_type == "library" and symbol_name not in existing
    })
    if missing:
        raise ValueError(
            "missing parsed LIBDEF constants from exec/libraries.i: " + ", ".join(missing)
        )
    rows.sort(key=lambda row: row[0])
    return rows


def ensure_core_struct_field_value_domain_rows(rows: list[tuple[str, str, str | None, str]],
                                               merged_domains: dict[str, dict]) -> list[tuple[str, str, str | None, str]]:
    row_map = {(struct_name, field_name, context_name): domain_name
               for struct_name, field_name, context_name, domain_name in rows}
    for struct_name, field_name, domain_name in (
        ("RT", "RT_MATCHWORD", "exec.resident.matchword"),
        ("RT", "RT_FLAGS", "exec.resident.flags"),
        ("RT", "RT_TYPE", "exec.node.type"),
        ("LIB", "LIB_FLAGS", "exec.library.flags"),
    ):
        if domain_name in merged_domains:
            row_map.setdefault((struct_name, field_name, None), domain_name)
    return sorted(((struct_name, field_name, context_name, domain_name)
                   for (struct_name, field_name, context_name), domain_name in row_map.items()),
                  key=lambda row: (row[0], row[1], "" if row[2] is None else row[2], row[3]))


def build_domain_member_rows(merged_domains: dict[str, dict], constant_rows: list[tuple[str, int, str | None]]
                             ) -> tuple[list[tuple[str, str, int | None, str | None]],
                                        list[tuple[str, int, str | None]]]:
    constant_values: dict[str, int] = {}
    constant_includes: dict[str, str | None] = {}
    used_constants: dict[str, tuple[int, str | None]] = {}
    rows: list[tuple[str, str, int | None, str | None]] = []
    for symbol_name, value, include_path in constant_rows:
        constant_values[symbol_name] = value
        constant_includes[symbol_name] = include_path
    for domain_name in sorted(merged_domains.keys()):
        domain_info = merged_domains[domain_name]
        members = domain_info.get("members", [])
        if not isinstance(members, list):
            continue
        for member_name in members:
            if not isinstance(member_name, str) or not member_name:
                continue
            member_value = constant_values.get(member_name)
            include_path = constant_includes.get(member_name)
            rows.append((domain_name, member_name, member_value, include_path))
            if member_value is not None:
                used_constants[member_name] = (member_value, include_path)
    used_constant_rows = sorted(((symbol_name, value, include_path)
                                 for symbol_name, (value, include_path) in used_constants.items()),
                                key=lambda row: row[0])
    return rows, used_constant_rows


def include_resident_vector_constant_rows(includes_payload: dict, constant_rows: list[tuple[str, int, str | None]],
                                          used_constant_rows: list[tuple[str, int, str | None]]
                                          ) -> list[tuple[str, int, str | None]]:
    by_name = {symbol_name: (symbol_name, value, include_path)
               for symbol_name, value, include_path in used_constant_rows}
    constant_by_name = {symbol_name: (symbol_name, value, include_path)
                        for symbol_name, value, include_path in constant_rows}
    for _target_type, _slot_index, symbol_name in resident_vector_prefix_rows(includes_payload):
        row = constant_by_name.get(symbol_name)
        if row is not None:
            by_name.setdefault(symbol_name, row)
    return sorted(by_name.values(), key=lambda row: row[0])


def value_domain_rows(merged_domains: dict[str, dict]) -> list[tuple[str, str | None, str | None, str | None, str | None, str | None]]:
    rows: list[tuple[str, str | None, str | None, str | None, str | None, str | None]] = []
    for domain_name in sorted(merged_domains.keys()):
        domain_info = merged_domains[domain_name]
        if not isinstance(domain_info, dict):
            continue
        rows.append((
            domain_name,
            domain_info.get("kind") if isinstance(domain_info.get("kind"), str) and domain_info.get("kind") else None,
            domain_info.get("zero_name")
            if isinstance(domain_info.get("zero_name"), str) and domain_info.get("zero_name") else None,
            domain_info.get("exact_match_policy")
            if isinstance(domain_info.get("exact_match_policy"), str) and domain_info.get("exact_match_policy") else None,
            domain_info.get("composition")
            if isinstance(domain_info.get("composition"), str) and domain_info.get("composition") else None,
            domain_info.get("remainder_policy")
            if isinstance(domain_info.get("remainder_policy"), str) and domain_info.get("remainder_policy") else None,
        ))
    return rows


def input_rows(library_name: str, function_name: str, other_info: dict, includes_payload: dict, other_payload: dict,
               api_input_value_domains: dict[tuple[str, str, str], str],
               api_input_semantic_kinds: dict[tuple[str, str, str], str],
               api_input_type_overrides: dict[tuple[str, str, str], tuple[str, str | None]]
               ) -> list[tuple[str, str | None, str | None, str | None, str | None, str | None]]:
    rows: list[tuple[str, str | None, str | None, str | None, str | None, str | None]] = []
    for item in other_info.get("inputs", []):
        if not isinstance(item, dict):
            continue
        regs = item.get("regs")
        if not isinstance(regs, list):
            continue
        input_name = item.get("name") if isinstance(item.get("name"), str) and item.get("name") else None
        type_name = item.get("type") if isinstance(item.get("type"), str) and item.get("type") else None
        struct_name = item.get("i_struct") if isinstance(item.get("i_struct"), str) and item.get("i_struct") else None
        if input_name is not None and (library_name, function_name, input_name) in api_input_type_overrides:
            type_name, struct_name = api_input_type_overrides[(library_name, function_name, input_name)]
        if struct_name is None:
            struct_name = infer_struct_name_from_type(type_name, includes_payload, other_payload)
        semantic_kind = item.get("semantic_kind") if isinstance(item.get("semantic_kind"), str) and item.get("semantic_kind") else None
        if input_name is not None:
            semantic_kind = api_input_semantic_kinds.get((library_name, function_name, input_name), semantic_kind)
        value_domain_name = (
            item.get("value_domain_name")
            if isinstance(item.get("value_domain_name"), str) and item.get("value_domain_name")
            else None
        )
        if input_name is not None:
            value_domain_name = api_input_value_domains.get((library_name, function_name, input_name), value_domain_name)
        for reg_name_text in regs:
            if isinstance(reg_name_text, str) and reg_name_text:
                rows.append((reg_name_text, input_name, type_name, struct_name, semantic_kind, value_domain_name))
    return rows


def output_struct_for_function(function_name: str, other_info: dict, includes_payload: dict, other_payload: dict) -> str | None:
    output = other_info.get("output")
    value = reg_name(output, "i_struct")
    if value:
        return value
    if not isinstance(output, dict):
        return None
    inferred = infer_struct_name_from_type(output.get("type") if isinstance(output.get("type"), str) else None,
                                           includes_payload, other_payload)
    if inferred:
        return inferred
    output_type = output.get("type")
    output_name = output.get("name")
    if output_type != "BPTR" or not isinstance(output_name, str):
        return None
    lowered_name = output_name.lower()
    if lowered_name in {"file", "fh"}:
        return "FileHandle"
    if lowered_name == "lock":
        return "FileLock"
    if function_name == "Output":
        return "FileHandle"
    if function_name == "Open":
        return "FileHandle"
    if function_name == "OpenFromLock":
        return "FileHandle"
    if function_name == "Lock":
        return "FileLock"
    return None


def output_row(function_name: str, other_info: dict, includes_payload: dict,
               other_payload: dict) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None]:
    output = other_info.get("output")
    if not isinstance(output, dict):
      return None, None, None, None, None, None
    return (
        reg_name(output, "reg"),
        output.get("name") if isinstance(output.get("name"), str) and output.get("name") else None,
        output.get("type") if isinstance(output.get("type"), str) and output.get("type") else None,
        output_struct_for_function(function_name, other_info, includes_payload, other_payload),
        output.get("semantic_kind") if isinstance(output.get("semantic_kind"), str) and output.get("semantic_kind") else None,
        output.get("value_domain_name")
        if isinstance(output.get("value_domain_name"), str) and output.get("value_domain_name") else None,
    )


def library_rows(includes_payload: dict, other_payload: dict) -> list[tuple[str, str, int, str, dict]]:
    rows: list[tuple[str, str, int, str, dict]] = []
    libraries = includes_payload.get("libraries", {})
    other_functions = other_payload.get("functions", {})
    for library_name, library in sorted(libraries.items()):
        base_name = library.get("base")
        if not isinstance(base_name, str) or not base_name:
            continue
        functions = library.get("functions", {})
        for function_name, function in sorted(functions.items()):
            if not isinstance(function, dict):
                continue
            lvo = function.get("lvo")
            if not isinstance(lvo, int):
                continue
            merged_info = dict(function)
            other_info = other_functions.get(library_name, {}).get(function_name, {})
            if isinstance(other_info, dict):
                merged_info.update(other_info)
            rows.append((library_name, base_name, lvo, function_name, merged_info))
    rows.sort(key=lambda row: (row[1], row[2], row[0], row[3]))
    return rows


def compatibility_versions(includes_payload: dict) -> list[str]:
    versions = includes_payload.get("_meta", {}).get("compatibility_versions", [])
    if not isinstance(versions, list):
        return []
    filtered = [version for version in versions if isinstance(version, str) and version]
    return sorted(
        filtered,
        key=lambda version: (
            compatibility_version_rank(version) if compatibility_version_rank(version) is not None else 1 << 30,
            version,
        ),
    )


def include_min_version_rows(includes_payload: dict) -> list[tuple[str, str]]:
    rows: dict[str, str] = {}
    include_versions = includes_payload.get("_meta", {}).get("include_min_versions", {})
    if not isinstance(include_versions, dict):
        return []
    for include_path, version in include_versions.items():
        normalized_path = normalize_include_path(include_path if isinstance(include_path, str) else None)
        if normalized_path is None:
            continue
        if not isinstance(version, str) or not version:
            continue
        rows[normalized_path] = version
    return sorted(rows.items(), key=lambda row: row[0])


def compatibility_version_rank(version: str | None) -> int | None:
    if not isinstance(version, str) or not version:
        return None
    parts = version.split(".")
    rank = 0
    part_count = 0
    for part in parts:
        if not part.isdigit():
            return None
        rank = (rank * 100) + int(part)
        part_count += 1
    if part_count == 1:
        rank *= 100
    return rank


def compatibility_enum_name(version: str) -> str:
    return f"AMIGA_OS_COMPAT_VERSION_{version.replace('.', '_')}"


def normalized_compatibility_enum_literal(version: str | None, supported_versions: list[str]) -> str:
    raw_rank = compatibility_version_rank(version)
    if raw_rank is None:
        return "AMIGA_OS_COMPAT_VERSION_NONE"
    for candidate in supported_versions:
        candidate_rank = compatibility_version_rank(candidate)
        if candidate_rank is not None and candidate_rank >= raw_rank:
            return compatibility_enum_name(candidate)
    return "AMIGA_OS_COMPAT_VERSION_NONE"


def referenced_struct_names(rows: list[tuple[str, str, int, str, dict]], includes_payload: dict, other_payload: dict,
                            api_input_value_domains: dict[tuple[str, str, str], str],
                            api_input_semantic_kinds: dict[tuple[str, str, str], str],
                            api_input_type_overrides: dict[tuple[str, str, str], tuple[str, str | None]]) -> list[str]:
    names: set[str] = set()
    for library_name, _, _, function_name, other_info in rows:
        if not isinstance(other_info, dict):
            continue
        output = other_info.get("output")
        if isinstance(output, dict):
            value = output_struct_for_function("", {"output": output}, includes_payload, other_payload)
            if isinstance(value, str) and value:
                names.add(value)
        for _, _, _, input_struct_name, _, _ in input_rows(library_name, function_name, other_info, includes_payload,
                                                           other_payload, api_input_value_domains,
                                                           api_input_semantic_kinds, api_input_type_overrides):
            if input_struct_name:
                names.add(input_struct_name)
    return sorted(names)


def struct_field_rows(includes_payload: dict, struct_names: list[str]) -> list[tuple[str, int, str, str | None, int, str | None, str | None, str | None]]:
    rows: list[tuple[str, int, str, str | None, int, str | None, str | None, str | None]] = []
    structs = includes_payload.get("structs", {})
    for struct_name in struct_names:
        struct_info = structs.get(struct_name, {})
        if not isinstance(struct_info, dict):
            continue
        for field in struct_info.get("fields", []):
            if not isinstance(field, dict):
                continue
            field_name = field.get("name")
            offset = field.get("offset")
            nested_type_name = None
            if not isinstance(field_name, str) or not field_name:
                continue
            if not isinstance(offset, int):
                continue
            if isinstance(field.get("struct"), str) and field["struct"]:
                nested_type_name = field["struct"]
            elif isinstance(field.get("pointer_struct"), str) and field["pointer_struct"]:
                nested_type_name = field["pointer_struct"]
            size = field.get("size")
            field_type = field.get("type") if isinstance(field.get("type"), str) and field.get("type") else None
            c_type = field.get("c_type") if isinstance(field.get("c_type"), str) and field.get("c_type") else None
            pointer_struct = (
                field.get("pointer_struct")
                if isinstance(field.get("pointer_struct"), str) and field.get("pointer_struct")
                else None
            )
            rows.append((
                struct_name,
                int(offset),
                field_name,
                nested_type_name,
                int(size) if isinstance(size, int) else 0,
                field_type,
                c_type,
                pointer_struct,
            ))
    rows.sort(key=lambda row: (row[0], row[1], row[2]))
    return rows


def symbol_include_rows(includes_payload: dict,
                        rows: list[tuple[str, str, int, str, dict]],
                        field_rows: list[tuple[str, int, str, str | None, int, str | None, str | None, str | None]],
                        domain_constant_rows: list[tuple[str, int, str | None]],
                        assembler_include_symbols_by_path: dict[str, set[str]] | None = None) -> list[tuple[str, str]]:
    entries: dict[str, str] = {}
    libraries = includes_payload.get("libraries", {})
    structs = includes_payload.get("structs", {})
    if assembler_include_symbols_by_path is None:
        assembler_include_symbols_by_path = load_assembler_include_symbols()

    for library_name, _, _, function_name, _ in rows:
        library = libraries.get(library_name, {})
        if not isinstance(library, dict):
            continue
        owner = library.get("owner", {})
        include_path = normalize_include_path(owner.get("assembler_include_path") if isinstance(owner, dict) else None)
        if include_path is None:
            continue
        symbol_name = f"_LVO{function_name}"
        if include_defines_assembler_symbol(assembler_include_symbols_by_path, include_path, symbol_name):
            entries.setdefault(symbol_name, include_path)

    for struct_name in sorted(structs.keys()):
        struct_info = structs.get(struct_name, {})
        if not isinstance(struct_info, dict):
            continue
        include_path = normalize_include_path(struct_info.get("source"))
        if include_path is None:
            continue
        base_offset_symbol = struct_info.get("base_offset_symbol")
        if isinstance(base_offset_symbol, str) and base_offset_symbol:
            entries.setdefault(base_offset_symbol, include_path)
        for field in struct_info.get("fields", []):
            if not isinstance(field, dict):
                continue
            field_name = field.get("name")
            if isinstance(field_name, str) and field_name:
                entries.setdefault(field_name, include_path)

    for symbol_name, _, include_path in domain_constant_rows:
        if include_path is not None:
            entries.setdefault(symbol_name, include_path)

    return sorted(entries.items(), key=lambda row: (row[1], row[0]))


def build_name_domains(rows: list[tuple[str, str, int, str, dict]],
                       field_rows: list[tuple[str, int, str, str | None, int, str | None, str | None, str | None]],
                       value_domain_rows_data: list[tuple[str, str | None, str | None, str | None, str | None, str | None]],
                       domain_member_rows: list[tuple[str, str, int | None, str | None]],
                       api_input_binding_rows: list[tuple[str, str, str, str]],
                       struct_field_binding_rows: list[tuple[str, str, str | None, str]],
                       domain_constant_rows: list[tuple[str, int, str | None]],
                       include_min_versions_data: list[tuple[str, str]],
                       symbol_include_rows_data: list[tuple[str, str]],
                       includes_payload: dict, other_payload: dict,
                       api_input_value_domains: dict[tuple[str, str, str], str],
                       api_input_semantic_kinds: dict[tuple[str, str, str], str],
                       api_input_type_overrides: dict[tuple[str, str, str], tuple[str, str | None]]) -> list[tuple[int, str, list[str]]]:
    library_names: set[str] = set()
    base_names: set[str] = set()
    function_names: set[str] = set()
    symbol_names: set[str] = set()
    include_paths: set[str] = set()
    type_names: set[str] = {"LIB"}
    struct_names: set[str] = set()
    field_names: set[str] = set()
    semantic_kinds: set[str] = set()
    value_domain_names: set[str] = set()

    for library_name, base_name, _, function_name, other_info in rows:
        library_names.add(library_name)
        base_names.add(base_name)
        function_names.add(function_name)
        symbol_names.add(f"_LVO{function_name}")
        for _, input_name, type_name, struct_name, semantic_kind, value_domain_name in input_rows(
                library_name, function_name, other_info, includes_payload, other_payload, api_input_value_domains,
                api_input_semantic_kinds, api_input_type_overrides):
            if input_name is not None:
                symbol_names.add(input_name)
            if type_name is not None:
                type_names.add(type_name)
            if struct_name is not None:
                struct_names.add(struct_name)
                type_names.add(struct_name)
            if semantic_kind is not None:
                semantic_kinds.add(semantic_kind)
            if value_domain_name is not None:
                value_domain_names.add(value_domain_name)
        _, output_name, output_type_name, output_struct_name, output_semantic_kind, output_value_domain_name = output_row(
            function_name, other_info, includes_payload, other_payload)
        if output_name is not None:
            symbol_names.add(output_name)
        if output_type_name is not None:
            type_names.add(output_type_name)
        if output_struct_name is not None:
            struct_names.add(output_struct_name)
            type_names.add(output_struct_name)
        if output_semantic_kind is not None:
            semantic_kinds.add(output_semantic_kind)
        if output_value_domain_name is not None:
            value_domain_names.add(output_value_domain_name)

    for struct_name, _, field_name, nested_type_name, _, field_type, c_type, pointer_struct in field_rows:
        struct_names.add(struct_name)
        type_names.add(struct_name)
        field_names.add(field_name)
        symbol_names.add(field_name)
        for type_name in (nested_type_name, field_type, c_type, pointer_struct):
            if type_name is not None:
                type_names.add(type_name)
        for maybe_struct_name in (nested_type_name, pointer_struct):
            if maybe_struct_name is not None:
                struct_names.add(maybe_struct_name)

    for domain_name, _, zero_name, _, _, _ in value_domain_rows_data:
        value_domain_names.add(domain_name)
        if zero_name is not None:
            symbol_names.add(zero_name)

    for _, member_name, _, include_path in domain_member_rows:
        symbol_names.add(member_name)
        if include_path is not None:
            include_paths.add(include_path)

    for library_name, function_name, input_name, domain_name in api_input_binding_rows:
        library_names.add(library_name)
        function_names.add(function_name)
        symbol_names.add(input_name)
        value_domain_names.add(domain_name)

    for struct_name, field_name, context_name, domain_name in struct_field_binding_rows:
        struct_names.add(struct_name)
        type_names.add(struct_name)
        field_names.add(field_name)
        symbol_names.add(field_name)
        if context_name is not None:
            symbol_names.add(context_name)
        value_domain_names.add(domain_name)

    for symbol_name, _, include_path in domain_constant_rows:
        symbol_names.add(symbol_name)
        if include_path is not None:
            include_paths.add(include_path)

    for include_path, _ in include_min_versions_data:
        include_paths.add(include_path)
    for symbol_name, include_path in symbol_include_rows_data:
        symbol_names.add(symbol_name)
        include_paths.add(include_path)
    for library_name, struct_name in includes_payload.get("_meta", {}).get("named_base_structs", {}).items():
        library_names.add(library_name)
        struct_names.add(struct_name)
        type_names.add(struct_name)
    for _, _, symbol_name in resident_vector_prefix_rows(includes_payload):
        symbol_names.add(symbol_name)
    for seed in resident_entry_seed_rows(includes_payload):
        named_base_name = seed["named_base_name"]
        struct_name = seed["struct_name"]
        context_name = seed["context_name"]
        if named_base_name is not None:
            library_names.add(named_base_name)
        if struct_name is not None:
            struct_names.add(struct_name)
            type_names.add(struct_name)
        if context_name is not None:
            symbol_names.add(context_name)

    return [
        (NAME_DOMAIN_LIBRARY, "library", sorted(library_names)),
        (NAME_DOMAIN_BASE, "base", sorted(base_names)),
        (NAME_DOMAIN_FUNCTION, "function", sorted(function_names)),
        (NAME_DOMAIN_SYMBOL, "symbol", sorted(symbol_names)),
        (NAME_DOMAIN_INCLUDE, "include", sorted(include_paths)),
        (NAME_DOMAIN_TYPE, "type", sorted(type_names)),
        (NAME_DOMAIN_STRUCT, "struct", sorted(struct_names)),
        (NAME_DOMAIN_FIELD, "field", sorted(field_names)),
        (NAME_DOMAIN_SEMANTIC_KIND, "semantic_kind", sorted(semantic_kinds)),
        (NAME_DOMAIN_VALUE_DOMAIN, "value_domain", sorted(value_domain_names)),
    ]


def write_header(rows: list[tuple[str, str, int, str, dict]],
                 field_rows: list[tuple[str, int, str, str | None, int, str | None, str | None, str | None]],
                 value_domain_rows_data: list[tuple[str, str | None, str | None, str | None, str | None, str | None]],
                 domain_member_rows: list[tuple[str, str, int | None, str | None]],
                 api_input_binding_rows: list[tuple[str, str, str, str]],
                 struct_field_binding_rows: list[tuple[str, str, str | None, str]],
                 domain_constant_rows: list[tuple[str, int, str | None]],
                 compatibility_versions_data: list[str], include_min_versions_data: list[tuple[str, str]],
                 includes_payload: dict, other_payload: dict,
                 api_input_value_domains: dict[tuple[str, str, str], str],
                 api_input_semantic_kinds: dict[tuple[str, str, str], str],
                 api_input_type_overrides: dict[tuple[str, str, str], tuple[str, str | None]],
                 naming_rules_payload: dict) -> None:
    io_device_offset = struct_field_offset(includes_payload, "IO", "IO_DEVICE")
    symbol_include_rows_data = symbol_include_rows(includes_payload, rows, field_rows, domain_constant_rows)
    named_base_struct_rows = sorted(includes_payload.get("_meta", {}).get("named_base_structs", {}).items())
    naming_pattern_rows = naming_patterns(naming_rules_payload)
    resident_prefix_rows = resident_vector_prefix_rows(includes_payload)
    resident_seed_rows = resident_entry_seed_rows(includes_payload)
    naming_function_limit = max(
        (len(pattern.get("functions", [])) for pattern in naming_pattern_rows if isinstance(pattern.get("functions"), list)),
        default=0,
    )
    name_domains = build_name_domains(rows, field_rows, value_domain_rows_data, domain_member_rows,
                                      api_input_binding_rows, struct_field_binding_rows, domain_constant_rows,
                                      include_min_versions_data, symbol_include_rows_data, includes_payload,
                                      other_payload, api_input_value_domains, api_input_semantic_kinds,
                                      api_input_type_overrides)
    name_domain_meta = build_name_domain_meta(name_domains, "AMIGA_OS")
    input_row_count = sum(len(input_rows(library_name, function_name, other_info, includes_payload, other_payload,
                                         api_input_value_domains, api_input_semantic_kinds, api_input_type_overrides))
                          for library_name, _, _, function_name, other_info in rows)
    lines = [
        "/* Generated Amiga OS runtime metadata. Do not edit directly. */",
        "#ifndef AMIGA_OS_RUNTIME_H",
        "#define AMIGA_OS_RUNTIME_H",
        "",
        "#include <stddef.h>",
        "#include <stdint.h>",
        "",
        "typedef enum AmigaOsCompatVersion {",
        "  AMIGA_OS_COMPAT_VERSION_NONE = 0,",
    ]
    for index, version in enumerate(compatibility_versions_data, start=1):
        lines.append(f"  {compatibility_enum_name(version)} = {index},")
    lines.extend([
        "} AmigaOsCompatVersion;",
        "",
        "typedef enum AmigaOsRegisterKind {",
        "  AMIGA_OS_REGISTER_NONE = 0,",
        "  AMIGA_OS_REGISTER_DATA = 1,",
        "  AMIGA_OS_REGISTER_ADDRESS = 2",
        "} AmigaOsRegisterKind;",
        "",
        "typedef enum AmigaOsValueDomainKind {",
        "  AMIGA_OS_VALUE_DOMAIN_KIND_NONE = 0,",
        "  AMIGA_OS_VALUE_DOMAIN_KIND_ENUM = 1,",
        "  AMIGA_OS_VALUE_DOMAIN_KIND_FLAGS = 2",
        "} AmigaOsValueDomainKind;",
        "",
        "typedef enum AmigaOsValueDomainExactMatchPolicy {",
        "  AMIGA_OS_VALUE_DOMAIN_EXACT_MATCH_NONE = 0,",
        "  AMIGA_OS_VALUE_DOMAIN_EXACT_MATCH_ERROR = 1",
        "} AmigaOsValueDomainExactMatchPolicy;",
        "",
        "typedef enum AmigaOsValueDomainComposition {",
        "  AMIGA_OS_VALUE_DOMAIN_COMPOSITION_NONE = 0,",
        "  AMIGA_OS_VALUE_DOMAIN_COMPOSITION_OR = 1,",
        "  AMIGA_OS_VALUE_DOMAIN_COMPOSITION_BIT_OR = 2",
        "} AmigaOsValueDomainComposition;",
        "",
        "typedef enum AmigaOsValueDomainRemainderPolicy {",
        "  AMIGA_OS_VALUE_DOMAIN_REMAINDER_NONE = 0,",
        "  AMIGA_OS_VALUE_DOMAIN_REMAINDER_ERROR = 1",
        "} AmigaOsValueDomainRemainderPolicy;",
        "",
    ])
    for item in name_domain_meta:
        lines.extend([
            f"typedef enum {item['enum_type']} {{",
        ])
        for value in item["values"]:
            lines.append(f"  {item['enum_values'][value]} = {item['id_map'][value]},")
        lines.append(f"  {item['enum_prefix']}_NONE = {item['none_id']},")
        lines.extend([f"}} {item['enum_type']};", ""])
    lines.extend([
        f"#define AMIGA_OS_NAMING_PATTERN_FUNCTION_LIMIT {naming_function_limit}u",
        "",
    ])
    lines.extend([
        "typedef struct AmigaOsCallInputInfo {",
        "  uint8_t reg_kind;",
        "  uint8_t reg_index;",
        "  uint16_t input_id;",
        "  uint16_t type_id;",
        "  uint16_t struct_id;",
        "  uint16_t semantic_kind_id;",
        "  uint16_t value_domain_id;",
        "  uint8_t source_kind;",
        "} AmigaOsCallInputInfo;",
        "",
        "typedef struct AmigaOsCallOutputInfo {",
        "  uint8_t reg_kind;",
        "  uint8_t reg_index;",
        "  uint16_t output_id;",
        "  uint16_t type_id;",
        "  uint16_t struct_id;",
        "  uint16_t semantic_kind_id;",
        "  uint16_t value_domain_id;",
        "} AmigaOsCallOutputInfo;",
        "",
        "typedef struct AmigaOsLibraryVectorInfo {",
        "  uint16_t library_id;",
        "  uint16_t base_id;",
        "  int16_t lvo;",
        "  uint16_t function_id;",
        "  uint16_t lvo_symbol_id;",
        "  uint8_t returns_base_reg_kind;",
        "  uint8_t returns_base_reg_index;",
        "  uint8_t returns_base_name_reg_kind;",
        "  uint8_t returns_base_name_reg_index;",
        "  uint16_t available_since_version;",
        "  const char *fd_version;",
        "  uint16_t input_start;",
        "  uint16_t input_count;",
        "  AmigaOsCallOutputInfo output;",
        "} AmigaOsLibraryVectorInfo;",
        "",
        "typedef struct AmigaOsStructFieldInfo {",
        "  uint16_t struct_id;",
        "  int16_t offset;",
        "  uint16_t field_id;",
        "  uint16_t nested_type_id;",
        "  uint16_t size;",
        "  uint16_t field_type_id;",
        "  uint16_t c_type_id;",
        "  uint16_t pointer_struct_id;",
        "} AmigaOsStructFieldInfo;",
        "",
        "typedef struct AmigaOsValueDomainMemberInfo {",
        "  uint16_t name_id;",
        "  int32_t value;",
        "  uint8_t value_known;",
        "} AmigaOsValueDomainMemberInfo;",
        "",
        "typedef struct AmigaOsValueDomainInfo {",
        "  uint16_t name_id;",
        "  uint16_t zero_name_id;",
        "  uint8_t kind;",
        "  uint8_t exact_match_policy;",
        "  uint8_t composition;",
        "  uint8_t remainder_policy;",
        "  uint16_t member_start;",
        "  uint16_t member_count;",
        "} AmigaOsValueDomainInfo;",
        "",
        "typedef struct AmigaOsApiInputValueDomainInfo {",
        "  uint16_t library_id;",
        "  uint16_t function_id;",
        "  uint16_t input_id;",
        "  uint16_t domain_id;",
        "} AmigaOsApiInputValueDomainInfo;",
        "",
        "typedef struct AmigaOsStructFieldValueDomainInfo {",
        "  uint16_t struct_id;",
        "  uint16_t field_id;",
        "  uint16_t context_id;",
        "  uint16_t domain_id;",
        "} AmigaOsStructFieldValueDomainInfo;",
        "",
        "typedef struct AmigaOsNamedBaseStructInfo {",
        "  uint16_t library_id;",
        "  uint16_t struct_id;",
        "} AmigaOsNamedBaseStructInfo;",
        "",
        "typedef struct AmigaOsNamingPatternInfo {",
        "  const char *name;",
        "  uint16_t function_ids[AMIGA_OS_NAMING_PATTERN_FUNCTION_LIMIT];",
        "  uint8_t function_count;",
        "  uint8_t partial;",
        "} AmigaOsNamingPatternInfo;",
        "",
        "typedef struct AmigaOsResidentVectorPrefixInfo {",
        "  const char *target_type;",
        "  uint8_t slot_index;",
        "  uint16_t symbol_id;",
        "} AmigaOsResidentVectorPrefixInfo;",
        "",
        "typedef struct AmigaOsResidentEntrySeedInfo {",
        "  const char *target_type;",
        "  const char *role;",
        "  const char *register_name;",
        "  const char *kind;",
        "  const char *named_base_source;",
        "  uint16_t named_base_library_id;",
        "  uint16_t struct_id;",
        "  uint16_t context_id;",
        "} AmigaOsResidentEntrySeedInfo;",
        "",
        "uint16_t amiga_os_name_id(uint8_t domain_kind, const char *name);",
        "const char *amiga_os_name(uint8_t domain_kind, uint16_t id);",
            "const char *amiga_os_register_name(uint8_t reg_kind, uint8_t reg_index);",
            "const char *amiga_os_find_library_base_name_by_id(uint16_t library_id);",
        "const char *amiga_os_find_library_base_name(const char *library_name);",
        "uint16_t amiga_os_find_library_base_struct_id(uint16_t library_id);",
        "const char *amiga_os_find_library_base_struct_name(const char *library_name);",
        "const AmigaOsNamedBaseStructInfo *amiga_os_named_base_struct_at(size_t index);",
        "const char *amiga_os_find_library_name_by_base_id(uint16_t base_id);",
            "const char *amiga_os_find_library_name_by_base_name(const char *base_name);",
            "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_base_id(uint16_t base_id, int16_t lvo);",
        "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector(const char *base_name, int16_t lvo);",
        "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_symbol_id(uint16_t lvo_symbol_id);",
        "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_symbol_name(const char *lvo_symbol_name);",
        "const AmigaOsLibraryVectorInfo *amiga_os_library_vector_at(size_t index);",
        "const AmigaOsCallInputInfo *amiga_os_library_vector_inputs(const AmigaOsLibraryVectorInfo *entry, size_t *out_count);",
        "const AmigaOsStructFieldInfo *amiga_os_find_struct_field_by_struct_id(uint16_t struct_id, int16_t offset);",
        "const AmigaOsStructFieldInfo *amiga_os_find_struct_field(const char *struct_name, int16_t offset);",
        "const AmigaOsStructFieldInfo *amiga_os_find_struct_field_by_field_id(uint16_t field_id);",
        "const AmigaOsStructFieldInfo *amiga_os_find_struct_field_by_symbol_name(const char *field_name);",
        "const AmigaOsStructFieldInfo *amiga_os_struct_field_at(size_t index);",
        "const AmigaOsValueDomainInfo *amiga_os_find_value_domain_by_id(uint16_t domain_id);",
        "const AmigaOsValueDomainInfo *amiga_os_find_value_domain(const char *domain_name);",
        "const AmigaOsValueDomainMemberInfo *amiga_os_value_domain_members(const AmigaOsValueDomainInfo *domain, size_t *out_count);",
        "uint16_t amiga_os_find_api_input_value_domain_id(uint16_t library_id, uint16_t function_id, uint16_t input_id);",
        "const char *amiga_os_find_api_input_value_domain(const char *library_name, const char *function_name, const char *input_name);",
        "uint16_t amiga_os_find_struct_field_value_domain_id(uint16_t struct_id, uint16_t field_id, uint16_t context_id);",
        "const char *amiga_os_find_struct_field_value_domain(const char *struct_name, const char *field_name, const char *context_name);",
        "int amiga_os_find_constant_value_by_id(uint16_t symbol_id, int32_t *out_value);",
        "int amiga_os_find_constant_value(const char *symbol_name, int32_t *out_value);",
        "const char *amiga_os_compatibility_version_name(AmigaOsCompatVersion version);",
        "AmigaOsCompatVersion amiga_os_parse_compatibility_version(const char *version);",
        "AmigaOsCompatVersion amiga_os_normalize_compatibility_version_enum(const char *version);",
        "AmigaOsCompatVersion amiga_os_find_include_min_compat_version_by_id(uint16_t include_id);",
        "const char *amiga_os_find_include_min_version(const char *include_path);",
        "AmigaOsCompatVersion amiga_os_find_include_min_compat_version(const char *include_path);",
        "int amiga_os_is_supported_compatibility_version(const char *version);",
        "const char *amiga_os_normalize_compatibility_version(const char *version);",
        "uint16_t amiga_os_find_symbol_include_id(uint16_t symbol_id);",
        "const char *amiga_os_find_symbol_include(const char *symbol_name);",
        "const AmigaOsNamingPatternInfo *amiga_os_naming_pattern_at(size_t index);",
        "int amiga_os_is_trivial_naming_function_id(uint16_t function_id);",
        "const char *amiga_os_generic_naming_prefix(void);",
        "const AmigaOsResidentVectorPrefixInfo *amiga_os_resident_vector_prefix_at(size_t index);",
        "const AmigaOsResidentEntrySeedInfo *amiga_os_resident_entry_seed_at(size_t index);",
        "const char *amiga_os_exec_base_library_name(void);",
        "uint8_t amiga_os_lvo_slot_size(void);",
        "",
        f"#define AMIGA_OS_LIBRARY_VECTOR_COUNT {len(rows)}u",
        f"#define AMIGA_OS_CALL_INPUT_COUNT {input_row_count}u",
        f"#define AMIGA_OS_STRUCT_FIELD_COUNT {len(field_rows)}u",
        f"#define AMIGA_OS_VALUE_DOMAIN_COUNT {len(value_domain_rows_data)}u",
        f"#define AMIGA_OS_VALUE_DOMAIN_MEMBER_COUNT {len(domain_member_rows)}u",
        f"#define AMIGA_OS_API_INPUT_VALUE_DOMAIN_COUNT {len(api_input_binding_rows)}u",
        f"#define AMIGA_OS_STRUCT_FIELD_VALUE_DOMAIN_COUNT {len(struct_field_binding_rows)}u",
        f"#define AMIGA_OS_NAMED_BASE_STRUCT_COUNT {len(named_base_struct_rows)}u",
        f"#define AMIGA_OS_COMPATIBILITY_VERSION_COUNT {len(compatibility_versions_data)}u",
        f"#define AMIGA_OS_INCLUDE_MIN_VERSION_COUNT {len(include_min_versions_data)}u",
        f"#define AMIGA_OS_SYMBOL_INCLUDE_COUNT {len(symbol_include_rows_data)}u",
        f"#define AMIGA_OS_NAMING_PATTERN_COUNT {len(naming_pattern_rows)}u",
        f"#define AMIGA_OS_TRIVIAL_NAMING_FUNCTION_COUNT {len(naming_trivial_functions(naming_rules_payload))}u",
        f"#define AMIGA_OS_RESIDENT_VECTOR_PREFIX_COUNT {len(resident_prefix_rows)}u",
        f"#define AMIGA_OS_RESIDENT_ENTRY_SEED_COUNT {len(resident_seed_rows)}u",
    ])
    if io_device_offset is not None:
        lines.append(f"#define AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET {io_device_offset}u")
    lines.extend(["", "#endif", ""])
    HEADER_PATH.write_text("\n".join(lines), encoding="ascii")


def write_source(rows: list[tuple[str, str, int, str, dict]],
                 field_rows: list[tuple[str, int, str, str | None, int, str | None, str | None, str | None]],
                 value_domain_rows_data: list[tuple[str, str | None, str | None, str | None, str | None, str | None]],
                 domain_member_rows: list[tuple[str, str, int | None, str | None]],
                 api_input_binding_rows: list[tuple[str, str, str, str]],
                 struct_field_binding_rows: list[tuple[str, str, str | None, str]],
                 domain_constant_rows: list[tuple[str, int, str | None]],
                 compatibility_versions_data: list[str], include_min_versions_data: list[tuple[str, str]],
                 includes_payload: dict, other_payload: dict,
                 api_input_value_domains: dict[tuple[str, str, str], str],
                 api_input_semantic_kinds: dict[tuple[str, str, str], str],
                 api_input_type_overrides: dict[tuple[str, str, str], tuple[str, str | None]],
                 naming_rules_payload: dict) -> None:
    symbol_include_rows_data = symbol_include_rows(includes_payload, rows, field_rows, domain_constant_rows)
    name_domains = build_name_domains(rows, field_rows, value_domain_rows_data, domain_member_rows,
                                      api_input_binding_rows, struct_field_binding_rows, domain_constant_rows,
                                      include_min_versions_data, symbol_include_rows_data, includes_payload,
                                      other_payload, api_input_value_domains, api_input_semantic_kinds,
                                      api_input_type_overrides)
    name_domain_meta = build_name_domain_meta(name_domains, "AMIGA_OS")
    named_base_struct_rows = sorted(includes_payload.get("_meta", {}).get("named_base_structs", {}).items())
    naming_pattern_rows = naming_patterns(naming_rules_payload)
    trivial_naming_functions = naming_trivial_functions(naming_rules_payload)
    resident_prefix_rows = resident_vector_prefix_rows(includes_payload)
    resident_seed_rows = resident_entry_seed_rows(includes_payload)
    flat_input_rows: list[tuple[str, str | None, str | None, str | None, str | None, str | None, int]] = []
    lines = [
        "/* Generated Amiga OS runtime metadata. Do not edit directly. */",
        '#include "generated/amiga_os_runtime.h"',
        '#include "platform_name_table.h"',
        "",
        "#include <string.h>",
        "",
        "typedef struct AmigaOsSymbolIncludeInfo {",
        "  uint16_t symbol_id;",
        "  uint16_t include_id;",
        "} AmigaOsSymbolIncludeInfo;",
        "",
        "typedef struct AmigaOsConstantInfo {",
        "  uint16_t symbol_id;",
        "  int32_t value;",
        "} AmigaOsConstantInfo;",
        "",
        "typedef struct AmigaOsIncludeMinVersionInfo {",
        "  uint16_t include_id;",
        "  uint16_t min_version;",
        "} AmigaOsIncludeMinVersionInfo;",
        "",
    ]
    for _, label, values in name_domains:
        lines.extend([
            f"static const char *const g_amiga_os_{label}_names[] = {{",
        ])
        for value in values:
            lines.append(f'  "{c_string(value)}",')
        lines.append("  NULL,")
        lines.extend(["};", ""])
    lines.extend([
        "uint16_t amiga_os_name_id(uint8_t domain_kind, const char *name) {",
        "  switch (domain_kind) {",
    ])
    for domain_kind, label, _ in name_domains:
        count_expr = f"(sizeof(g_amiga_os_{label}_names) / sizeof(g_amiga_os_{label}_names[0]))"
        lines.append(
            f"  case {domain_kind}u: return platform_name_id_from_table(g_amiga_os_{label}_names, "
            f"{count_expr}, name);")
    lines.extend([
        "  default: return 0U;",
        "  }",
        "}",
        "",
        "const char *amiga_os_name(uint8_t domain_kind, uint16_t id) {",
        "  switch (domain_kind) {",
    ])
    for domain_kind, label, _ in name_domains:
        count_expr = f"(sizeof(g_amiga_os_{label}_names) / sizeof(g_amiga_os_{label}_names[0]))"
        lines.append(
            f"  case {domain_kind}u: return g_amiga_os_{label}_names[(size_t)id < {count_expr} ? (size_t)id : {count_expr} - 1U];")
    lines.extend([
        "  default: return NULL;",
        "  }",
        "}",
        "",
        "const char *amiga_os_register_name(uint8_t reg_kind, uint8_t reg_index) {",
        "  static const char *const data_regs[] = { \"D0\", \"D1\", \"D2\", \"D3\", \"D4\", \"D5\", \"D6\", \"D7\" };",
        "  static const char *const addr_regs[] = { \"A0\", \"A1\", \"A2\", \"A3\", \"A4\", \"A5\", \"A6\", \"A7\" };",
        "  if (reg_index >= 8U) return NULL;",
        "  if (reg_kind == AMIGA_OS_REGISTER_DATA) return data_regs[reg_index];",
        "  if (reg_kind == AMIGA_OS_REGISTER_ADDRESS) return addr_regs[reg_index];",
        "  return NULL;",
        "}",
        "",
        "static const AmigaOsCallInputInfo g_amiga_os_call_inputs[] = {",
    ])
    for library_name, _, _, function_name, other_info in rows:
        for reg_name_text, input_name, type_name, struct_name, semantic_kind, value_domain_name in input_rows(
                library_name, function_name, other_info, includes_payload, other_payload, api_input_value_domains,
                api_input_semantic_kinds, api_input_type_overrides):
            reg_kind, reg_index = parse_register_name(reg_name_text)
            source_kind = 1 if input_name is not None and (
                library_name, function_name, input_name) in api_input_type_overrides else 0
            flat_input_rows.append((reg_name_text, input_name, type_name, struct_name, semantic_kind,
                                    value_domain_name, source_kind))
            lines.append(
                "  { %du, %du, %s, %s, %s, %s, %s, %du },"
                % (
                    reg_kind,
                    reg_index,
                    name_id_literal(name_domain_meta, "symbol", input_name),
                    name_id_literal(name_domain_meta, "type", type_name),
                    name_id_literal(name_domain_meta, "struct", struct_name),
                    name_id_literal(name_domain_meta, "semantic_kind", semantic_kind),
                    name_id_literal(name_domain_meta, "value_domain", value_domain_name),
                    source_kind,
                )
            )
    lines.extend([
        "};",
        "",
        "static const AmigaOsLibraryVectorInfo g_amiga_os_library_vectors[] = {",
    ])
    input_start = 0
    for library_name, base_name, lvo, function_name, other_info in rows:
        returns_base = other_info.get("returns_base") if isinstance(other_info, dict) else None
        available_since = other_info.get("available_since") if isinstance(other_info.get("available_since"), str) and other_info.get("available_since") else None
        available_since_version = normalized_compatibility_enum_literal(available_since, compatibility_versions_data)
        fd_version = other_info.get("fd_version") if isinstance(other_info.get("fd_version"), str) and other_info.get("fd_version") else None
        lvo_name = f"_LVO{function_name}"
        returns_base_reg_name = reg_name(returns_base, "base_reg")
        returns_base_name_reg_name = reg_name(returns_base, "name_reg")
        returns_base_reg_kind, returns_base_reg_index = parse_register_name(returns_base_reg_name)
        returns_base_name_reg_kind, returns_base_name_reg_index = parse_register_name(returns_base_name_reg_name)
        output_reg_name, output_name, output_type_name, output_struct_name, output_semantic_kind, output_value_domain_name = output_row(
            function_name, other_info, includes_payload, other_payload)
        output_reg_kind, output_reg_index = parse_register_name(output_reg_name)
        vector_input_rows = input_rows(library_name, function_name, other_info, includes_payload, other_payload,
                                       api_input_value_domains, api_input_semantic_kinds, api_input_type_overrides)
        input_count = len(vector_input_rows)
        lines.append(
            "  { %s, %s, %d, %s, %s, %du, %du, %du, %du, %s, %s, %du, %du, { %du, %du, %s, %s, %s, %s, %s } },"
            % (
                name_id_literal(name_domain_meta, "library", library_name),
                name_id_literal(name_domain_meta, "base", base_name),
                lvo,
                name_id_literal(name_domain_meta, "function", function_name),
                name_id_literal(name_domain_meta, "symbol", lvo_name),
                returns_base_reg_kind,
                returns_base_reg_index,
                returns_base_name_reg_kind,
                returns_base_name_reg_index,
                available_since_version,
                "NULL" if fd_version is None else f'"{c_string(fd_version)}"',
                input_start,
                input_count,
                output_reg_kind,
                output_reg_index,
                name_id_literal(name_domain_meta, "symbol", output_name),
                name_id_literal(name_domain_meta, "type", output_type_name),
                name_id_literal(name_domain_meta, "struct", output_struct_name),
                name_id_literal(name_domain_meta, "semantic_kind", output_semantic_kind),
                name_id_literal(name_domain_meta, "value_domain", output_value_domain_name),
            )
        )
        input_start += input_count
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsStructFieldInfo g_amiga_os_struct_fields[] = {",
        ]
    )
    for struct_name, offset, field_name, nested_type_name, size, field_type, c_type, pointer_struct in field_rows:
        lines.append(
            "  { %s, %d, %s, %s, %du, %s, %s, %s },"
            % (
                name_id_literal(name_domain_meta, "struct", struct_name),
                offset,
                name_id_literal(name_domain_meta, "field", field_name),
                name_id_literal(name_domain_meta, "type", nested_type_name),
                size,
                name_id_literal(name_domain_meta, "type", field_type),
                name_id_literal(name_domain_meta, "type", c_type),
                name_id_literal(name_domain_meta, "struct", pointer_struct),
            )
        )
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsValueDomainMemberInfo g_amiga_os_value_domain_members[] = {",
        ]
    )
    for _, member_name, member_value, _ in domain_member_rows:
        lines.append(
            "  { %s, %d, %du },"
            % (
                name_id_literal(name_domain_meta, "symbol", member_name),
                0 if member_value is None else int(member_value),
                0 if member_value is None else 1,
            )
        )
    domain_member_starts: dict[str, tuple[int, int]] = {}
    member_start = 0
    for domain_name, _, _, _, _, _ in value_domain_rows_data:
        member_count = sum(1 for row in domain_member_rows if row[0] == domain_name)
        domain_member_starts[domain_name] = (member_start, member_count)
        member_start += member_count
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsValueDomainInfo g_amiga_os_value_domains[] = {",
        ]
    )
    for domain_name, kind, zero_name, exact_match_policy, composition, remainder_policy in value_domain_rows_data:
        input_start, input_count = domain_member_starts.get(domain_name, (0, 0))
        lines.append(
            "  { %s, %s, %s, %s, %s, %s, %du, %du },"
            % (
                name_id_literal(name_domain_meta, "value_domain", domain_name),
                name_id_literal(name_domain_meta, "symbol", zero_name),
                value_domain_kind_literal(kind),
                value_domain_exact_match_literal(exact_match_policy),
                value_domain_composition_literal(composition),
                value_domain_remainder_literal(remainder_policy),
                input_start,
                input_count,
            )
        )
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsApiInputValueDomainInfo g_amiga_os_api_input_value_domains[] = {",
        ]
    )
    for library_name, function_name, input_name, domain_name in api_input_binding_rows:
        lines.append(
            "  { %s, %s, %s, %s },"
            % (
                name_id_literal(name_domain_meta, "library", library_name),
                name_id_literal(name_domain_meta, "function", function_name),
                name_id_literal(name_domain_meta, "symbol", input_name),
                name_id_literal(name_domain_meta, "value_domain", domain_name),
            )
        )
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsStructFieldValueDomainInfo g_amiga_os_struct_field_value_domains[] = {",
        ]
    )
    for struct_name, field_name, context_name, domain_name in struct_field_binding_rows:
        lines.append(
            "  { %s, %s, %s, %s },"
            % (
                name_id_literal(name_domain_meta, "struct", struct_name),
                name_id_literal(name_domain_meta, "field", field_name),
                name_id_literal(name_domain_meta, "symbol", context_name),
                name_id_literal(name_domain_meta, "value_domain", domain_name),
            )
        )
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsNamedBaseStructInfo g_amiga_os_named_base_structs[] = {",
        ]
    )
    for library_name, struct_name in named_base_struct_rows:
        lines.append("  { %s, %s }," % (
            name_id_literal(name_domain_meta, "library", library_name),
            name_id_literal(name_domain_meta, "struct", struct_name)))
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsNamingPatternInfo g_amiga_os_naming_patterns[] = {",
        ]
    )
    for pattern in naming_pattern_rows:
        raw_functions = pattern.get("functions", [])
        functions = [function for function in raw_functions if isinstance(function, str)] if isinstance(raw_functions, list) else []
        function_ids = [name_id_literal(name_domain_meta, "function", function) for function in functions]
        initializer_values = ", ".join(function_ids)
        if initializer_values:
            initializer_values = "{ " + initializer_values + " }"
        else:
            initializer_values = "{ 0u }"
        lines.append("  { \"%s\", %s, %du, %du }," % (
            c_string(str(pattern.get("name", ""))),
            initializer_values,
            len(functions),
            1 if pattern.get("partial") else 0))
    lines.extend(
        [
            "};",
            "",
            "static const uint16_t g_amiga_os_trivial_naming_functions[] = {",
        ]
    )
    for function_name in trivial_naming_functions:
        lines.append("  %s," % name_id_literal(name_domain_meta, "function", function_name))
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsResidentVectorPrefixInfo g_amiga_os_resident_vector_prefixes[] = {",
        ]
    )
    for target_type, slot_index, symbol_name in resident_prefix_rows:
        lines.append("  { \"%s\", %du, %s }," % (
            c_string(target_type),
            slot_index,
            name_id_literal(name_domain_meta, "symbol", symbol_name)))
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsResidentEntrySeedInfo g_amiga_os_resident_entry_seeds[] = {",
        ]
    )
    for seed in resident_seed_rows:
        lines.append("  { \"%s\", \"%s\", \"%s\", \"%s\", %s, %s, %s, %s }," % (
            c_string(str(seed["target_type"])),
            c_string(str(seed["role"])),
            c_string(str(seed["register"])),
            c_string(str(seed["kind"])),
            "NULL" if seed["named_base_source"] is None else "\"%s\"" % c_string(str(seed["named_base_source"])),
            name_id_literal(name_domain_meta, "library", seed["named_base_name"]),
            name_id_literal(name_domain_meta, "struct", seed["struct_name"]),
            name_id_literal(name_domain_meta, "symbol", seed["context_name"])))
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsConstantInfo g_amiga_os_constants[] = {",
        ]
    )
    for symbol_name, value, _ in domain_constant_rows:
        lines.append("  { %s, %d }," % (name_id_literal(name_domain_meta, "symbol", symbol_name), value))
    lines.extend(
        [
            "};",
            "",
            "static const char *g_amiga_os_compatibility_version_names[] = {",
            "  NULL,",
        ]
    )
    for version in compatibility_versions_data:
        lines.append('  "%s",' % c_string(version))
    lines.extend(
        [
            "};",
            "",
            "static const uint16_t g_amiga_os_compatibility_version_ranks[] = {",
            "  0u,",
        ]
    )
    for version in compatibility_versions_data:
        rank = compatibility_version_rank(version)
        lines.append("  %du," % (0 if rank is None else rank))
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsIncludeMinVersionInfo g_amiga_os_include_min_versions[] = {",
        ]
    )
    for include_path, version in include_min_versions_data:
        lines.append("  { %s, %s }," % (
            name_id_literal(name_domain_meta, "include", include_path),
            normalized_compatibility_enum_literal(version, compatibility_versions_data)))
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsSymbolIncludeInfo g_amiga_os_symbol_includes[] = {",
        ]
    )
    for symbol_name, include_path in symbol_include_rows_data:
        lines.append("  { %s, %s }," % (
            name_id_literal(name_domain_meta, "symbol", symbol_name),
            name_id_literal(name_domain_meta, "include", include_path)))
    lines.extend(
        [
            "};",
            "",
            "const char *amiga_os_find_library_base_name_by_id(uint16_t library_id) {",
            "  size_t index;",
            "  if (amiga_os_name(%du, library_id) == NULL) return NULL;" % NAME_DOMAIN_LIBRARY,
            "  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {",
            "    const AmigaOsLibraryVectorInfo *entry = &g_amiga_os_library_vectors[index];",
            "    if (entry->library_id == library_id) return amiga_os_name(%du, entry->base_id);" % NAME_DOMAIN_BASE,
            "  }",
            "  return NULL;",
            "}",
            "",
            "const char *amiga_os_find_library_base_name(const char *library_name) {",
            "  return amiga_os_find_library_base_name_by_id(amiga_os_name_id(%du, library_name));" % NAME_DOMAIN_LIBRARY,
            "}",
            "",
            "uint16_t amiga_os_find_library_base_struct_id(uint16_t library_id) {",
            "  size_t index;",
            "  if (amiga_os_name(%du, library_id) == NULL) return AMIGA_OS_STRUCT_ID_NONE;" % NAME_DOMAIN_LIBRARY,
            "  for (index = 0U; index < AMIGA_OS_NAMED_BASE_STRUCT_COUNT; ++index) {",
            "    const AmigaOsNamedBaseStructInfo *entry = &g_amiga_os_named_base_structs[index];",
            "    if (entry->library_id == library_id) return entry->struct_id;",
            "  }",
            "  return AMIGA_OS_STRUCT_ID_NONE;",
            "}",
            "",
            "const char *amiga_os_find_library_base_struct_name(const char *library_name) {",
            "  return amiga_os_name(%du, amiga_os_find_library_base_struct_id(amiga_os_name_id(%du, library_name)));" % (
                NAME_DOMAIN_STRUCT, NAME_DOMAIN_LIBRARY),
            "}",
            "",
            "const AmigaOsNamedBaseStructInfo *amiga_os_named_base_struct_at(size_t index) {",
            "  if (index >= AMIGA_OS_NAMED_BASE_STRUCT_COUNT) return NULL;",
            "  return &g_amiga_os_named_base_structs[index];",
            "}",
            "",
            "const AmigaOsNamingPatternInfo *amiga_os_naming_pattern_at(size_t index) {",
            "  if (index >= AMIGA_OS_NAMING_PATTERN_COUNT) return NULL;",
            "  return &g_amiga_os_naming_patterns[index];",
            "}",
            "",
            "int amiga_os_is_trivial_naming_function_id(uint16_t function_id) {",
            "  size_t index;",
            "  if (amiga_os_name(%du, function_id) == NULL) return 0;" % NAME_DOMAIN_FUNCTION,
            "  for (index = 0U; index < AMIGA_OS_TRIVIAL_NAMING_FUNCTION_COUNT; ++index) {",
            "    if (g_amiga_os_trivial_naming_functions[index] == function_id) return 1;",
            "  }",
            "  return 0;",
            "}",
            "",
            "const char *amiga_os_generic_naming_prefix(void) {",
            "  return \"%s\";" % c_string(str(naming_rules_payload.get("generic_prefix", ""))),
            "}",
            "",
            "const AmigaOsResidentVectorPrefixInfo *amiga_os_resident_vector_prefix_at(size_t index) {",
            "  if (index >= AMIGA_OS_RESIDENT_VECTOR_PREFIX_COUNT) return NULL;",
            "  return &g_amiga_os_resident_vector_prefixes[index];",
            "}",
            "",
            "const AmigaOsResidentEntrySeedInfo *amiga_os_resident_entry_seed_at(size_t index) {",
            "  if (index >= AMIGA_OS_RESIDENT_ENTRY_SEED_COUNT) return NULL;",
            "  return &g_amiga_os_resident_entry_seeds[index];",
            "}",
            "",
            "const char *amiga_os_exec_base_library_name(void) {",
            "  return \"%s\";" % c_string(str(includes_payload.get("_meta", {}).get("exec_base_addr", {}).get("library", "exec.library"))),
            "}",
            "",
            "uint8_t amiga_os_lvo_slot_size(void) {",
            "  return %du;" % int(includes_payload.get("_meta", {}).get("lvo_slot_size", 6)),
            "}",
            "",
            "const char *amiga_os_find_library_name_by_base_id(uint16_t base_id) {",
            "  size_t index;",
            "  if (amiga_os_name(%du, base_id) == NULL) return NULL;" % NAME_DOMAIN_BASE,
            "  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {",
            "    const AmigaOsLibraryVectorInfo *entry = &g_amiga_os_library_vectors[index];",
            "    if (entry->base_id == base_id) return amiga_os_name(%du, entry->library_id);" % NAME_DOMAIN_LIBRARY,
            "  }",
            "  return NULL;",
            "}",
            "",
            "const char *amiga_os_find_library_name_by_base_name(const char *base_name) {",
            "  return amiga_os_find_library_name_by_base_id(amiga_os_name_id(%du, base_name));" % NAME_DOMAIN_BASE,
            "}",
            "",
            "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_base_id(uint16_t base_id, int16_t lvo) {",
            "  size_t low = 0U;",
            "  size_t high = AMIGA_OS_LIBRARY_VECTOR_COUNT;",
            "  if (amiga_os_name(%du, base_id) == NULL) return NULL;" % NAME_DOMAIN_BASE,
            "  while (low < high) {",
            "    size_t mid = low + ((high - low) / 2U);",
            "    const AmigaOsLibraryVectorInfo *entry = &g_amiga_os_library_vectors[mid];",
            "    if (base_id == entry->base_id) {",
            "      if (lvo == entry->lvo) return entry;",
            "      if (lvo < entry->lvo) high = mid;",
            "      else low = mid + 1U;",
            "      continue;",
            "    }",
            "    if (base_id < entry->base_id) high = mid;",
            "    else low = mid + 1U;",
            "  }",
            "  return NULL;",
            "}",
            "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector(const char *base_name, int16_t lvo) {",
            "  return amiga_os_find_library_vector_by_base_id(amiga_os_name_id(%du, base_name), lvo);" % NAME_DOMAIN_BASE,
            "}",
            "",
            "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_symbol_id(uint16_t lvo_symbol_id) {",
            "  size_t index;",
            "  if (amiga_os_name(%du, lvo_symbol_id) == NULL) return NULL;" % NAME_DOMAIN_SYMBOL,
            "  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {",
            "    const AmigaOsLibraryVectorInfo *entry = &g_amiga_os_library_vectors[index];",
            "    if (entry->lvo_symbol_id == lvo_symbol_id) return entry;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_symbol_name(const char *lvo_symbol_name) {",
            "  return amiga_os_find_library_vector_by_symbol_id(amiga_os_name_id(%du, lvo_symbol_name));" % NAME_DOMAIN_SYMBOL,
            "}",
            "",
            "const AmigaOsLibraryVectorInfo *amiga_os_library_vector_at(size_t index) {",
            "  if (index >= AMIGA_OS_LIBRARY_VECTOR_COUNT) return NULL;",
            "  return &g_amiga_os_library_vectors[index];",
            "}",
            "",
            "const AmigaOsCallInputInfo *amiga_os_library_vector_inputs(const AmigaOsLibraryVectorInfo *entry, size_t *out_count) {",
            "  if (out_count != NULL) *out_count = 0U;",
            "  if (entry == NULL || entry->input_count == 0U) return NULL;",
            "  if (out_count != NULL) *out_count = (size_t)entry->input_count;",
            "  return &g_amiga_os_call_inputs[entry->input_start];",
            "}",
            "",
            "const AmigaOsStructFieldInfo *amiga_os_find_struct_field_by_struct_id(uint16_t struct_id, int16_t offset) {",
            "  size_t low = 0U;",
            "  size_t high = AMIGA_OS_STRUCT_FIELD_COUNT;",
            "  if (amiga_os_name(%du, struct_id) == NULL) return NULL;" % NAME_DOMAIN_STRUCT,
            "  while (low < high) {",
            "    size_t mid = low + ((high - low) / 2U);",
            "    const AmigaOsStructFieldInfo *entry = &g_amiga_os_struct_fields[mid];",
            "    if (struct_id == entry->struct_id) {",
            "      if (offset == entry->offset) return entry;",
            "      if (offset < entry->offset) high = mid;",
            "      else low = mid + 1U;",
            "      continue;",
            "    }",
            "    if (struct_id < entry->struct_id) high = mid;",
            "    else low = mid + 1U;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const AmigaOsStructFieldInfo *amiga_os_find_struct_field(const char *struct_name, int16_t offset) {",
            "  return amiga_os_find_struct_field_by_struct_id(amiga_os_name_id(%du, struct_name), offset);" % NAME_DOMAIN_STRUCT,
            "}",
            "",
            "const AmigaOsStructFieldInfo *amiga_os_find_struct_field_by_field_id(uint16_t field_id) {",
            "  size_t index;",
            "  if (amiga_os_name(%du, field_id) == NULL) return NULL;" % NAME_DOMAIN_FIELD,
            "  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {",
            "    const AmigaOsStructFieldInfo *entry = &g_amiga_os_struct_fields[index];",
            "    if (entry->field_id == field_id) return entry;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const AmigaOsStructFieldInfo *amiga_os_find_struct_field_by_symbol_name(const char *field_name) {",
            "  return amiga_os_find_struct_field_by_field_id(amiga_os_name_id(%du, field_name));" % NAME_DOMAIN_FIELD,
            "}",
            "",
            "const AmigaOsStructFieldInfo *amiga_os_struct_field_at(size_t index) {",
            "  if (index >= AMIGA_OS_STRUCT_FIELD_COUNT) return NULL;",
            "  return &g_amiga_os_struct_fields[index];",
            "}",
            "",
            "const AmigaOsValueDomainInfo *amiga_os_find_value_domain_by_id(uint16_t domain_id) {",
            "  size_t index;",
            "  if (domain_id == 0U) return NULL;",
            "  for (index = 0U; index < AMIGA_OS_VALUE_DOMAIN_COUNT; ++index) {",
            "    const AmigaOsValueDomainInfo *entry = &g_amiga_os_value_domains[index];",
            "    if (entry->name_id == domain_id) return entry;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const AmigaOsValueDomainInfo *amiga_os_find_value_domain(const char *domain_name) {",
            "  return amiga_os_find_value_domain_by_id(amiga_os_name_id(%du, domain_name));" % NAME_DOMAIN_VALUE_DOMAIN,
            "}",
            "",
            "const AmigaOsValueDomainMemberInfo *amiga_os_value_domain_members(const AmigaOsValueDomainInfo *domain, size_t *out_count) {",
            "  if (out_count != NULL) *out_count = 0U;",
            "  if (domain == NULL || domain->member_count == 0U) return NULL;",
            "  if (out_count != NULL) *out_count = (size_t)domain->member_count;",
            "  return &g_amiga_os_value_domain_members[domain->member_start];",
            "}",
            "",
            "uint16_t amiga_os_find_api_input_value_domain_id(uint16_t library_id, uint16_t function_id, uint16_t input_id) {",
            "  size_t index;",
            "  if (amiga_os_name(%du, library_id) == NULL || amiga_os_name(%du, function_id) == NULL || amiga_os_name(%du, input_id) == NULL) return AMIGA_OS_VALUE_DOMAIN_ID_NONE;" % (NAME_DOMAIN_LIBRARY, NAME_DOMAIN_FUNCTION, NAME_DOMAIN_SYMBOL),
            "  for (index = 0U; index < AMIGA_OS_API_INPUT_VALUE_DOMAIN_COUNT; ++index) {",
            "    const AmigaOsApiInputValueDomainInfo *entry = &g_amiga_os_api_input_value_domains[index];",
            "    if (entry->library_id != library_id) continue;",
            "    if (entry->function_id != function_id) continue;",
            "    if (entry->input_id != input_id) continue;",
            "    return entry->domain_id;",
            "  }",
            "  return AMIGA_OS_VALUE_DOMAIN_ID_NONE;",
            "}",
            "",
            "const char *amiga_os_find_api_input_value_domain(const char *library_name, const char *function_name, const char *input_name) {",
            "  uint16_t domain_id = amiga_os_find_api_input_value_domain_id(",
            "    amiga_os_name_id(%du, library_name)," % NAME_DOMAIN_LIBRARY,
            "    amiga_os_name_id(%du, function_name)," % NAME_DOMAIN_FUNCTION,
            "    amiga_os_name_id(%du, input_name));" % NAME_DOMAIN_SYMBOL,
            "  return amiga_os_name(%du, domain_id);" % NAME_DOMAIN_VALUE_DOMAIN,
            "}",
            "",
            "uint16_t amiga_os_find_struct_field_value_domain_id(uint16_t struct_id, uint16_t field_id, uint16_t context_id) {",
            "  size_t index;",
            "  uint16_t fallback = AMIGA_OS_VALUE_DOMAIN_ID_NONE;",
            "  if (amiga_os_name(%du, struct_id) == NULL || amiga_os_name(%du, field_id) == NULL) return AMIGA_OS_VALUE_DOMAIN_ID_NONE;" % (NAME_DOMAIN_STRUCT, NAME_DOMAIN_FIELD),
            "  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_VALUE_DOMAIN_COUNT; ++index) {",
            "    const AmigaOsStructFieldValueDomainInfo *entry = &g_amiga_os_struct_field_value_domains[index];",
            "    if (entry->struct_id != struct_id) continue;",
            "    if (entry->field_id != field_id) continue;",
            "    if (amiga_os_name(%du, entry->context_id) == NULL) {" % NAME_DOMAIN_SYMBOL,
            "      fallback = entry->domain_id;",
            "      continue;",
            "    }",
            "    if (amiga_os_name(%du, context_id) != NULL && entry->context_id == context_id) return entry->domain_id;" % NAME_DOMAIN_SYMBOL,
            "  }",
            "  return fallback;",
            "}",
            "",
            "const char *amiga_os_find_struct_field_value_domain(const char *struct_name, const char *field_name, const char *context_name) {",
            "  uint16_t domain_id = amiga_os_find_struct_field_value_domain_id(",
            "    amiga_os_name_id(%du, struct_name)," % NAME_DOMAIN_STRUCT,
            "    amiga_os_name_id(%du, field_name)," % NAME_DOMAIN_FIELD,
            "    amiga_os_name_id(%du, context_name));" % NAME_DOMAIN_SYMBOL,
            "  return amiga_os_name(%du, domain_id);" % NAME_DOMAIN_VALUE_DOMAIN,
            "}",
            "",
            "int amiga_os_find_constant_value_by_id(uint16_t symbol_id, int32_t *out_value) {",
            "  size_t index;",
            "  if (amiga_os_name(%du, symbol_id) == NULL || out_value == NULL) return 0;" % NAME_DOMAIN_SYMBOL,
            "  for (index = 0U; index < sizeof(g_amiga_os_constants) / sizeof(g_amiga_os_constants[0]); ++index) {",
            "    const AmigaOsConstantInfo *entry = &g_amiga_os_constants[index];",
            "    if (entry->symbol_id == symbol_id) {",
            "      *out_value = entry->value;",
            "      return 1;",
            "    }",
            "  }",
            "  return 0;",
            "}",
            "",
            "int amiga_os_find_constant_value(const char *symbol_name, int32_t *out_value) {",
            "  return amiga_os_find_constant_value_by_id(amiga_os_name_id(%du, symbol_name), out_value);" % NAME_DOMAIN_SYMBOL,
            "}",
            "",
            "static void amiga_os_normalize_include_path_copy(char *dest, size_t dest_size, const char *source) {",
            "  size_t index = 0U;",
            "  if (dest == NULL || dest_size == 0U) return;",
            "  if (source == NULL) {",
            "    dest[0] = '\\0';",
            "    return;",
            "  }",
            "  while (source[index] != '\\0' && index + 1U < dest_size) {",
            "    char ch = source[index];",
            "    if (ch == '\\\\') ch = '/';",
            "    if (ch >= 'A' && ch <= 'Z') ch = (char)(ch - 'A' + 'a');",
            "    dest[index] = ch;",
            "    ++index;",
            "  }",
            "  dest[index] = '\\0';",
            "}",
            "",
            "static int amiga_os_parse_compatibility_version_rank(const char *version, unsigned long *out_rank) {",
            "  const char *cursor = version;",
            "  unsigned long rank = 0UL;",
            "  unsigned long component_count = 0UL;",
            "  if (out_rank != NULL) *out_rank = 0UL;",
            "  if (version == NULL || version[0] == '\\0' || out_rank == NULL) return 0;",
            "  while (*cursor != '\\0') {",
            "    unsigned long component = 0UL;",
            "    int has_digits = 0;",
            "    while (*cursor >= '0' && *cursor <= '9') {",
            "      has_digits = 1;",
            "      component = (component * 10UL) + (unsigned long)(*cursor - '0');",
            "      ++cursor;",
            "    }",
            "    if (!has_digits) return 0;",
            "    rank = (rank * 100UL) + component;",
            "    ++component_count;",
            "    if (*cursor == '\\0') break;",
            "    if (*cursor != '.') return 0;",
            "    ++cursor;",
            "    if (*cursor == '\\0') return 0;",
            "  }",
            "  if (component_count == 1UL) rank *= 100UL;",
            "  *out_rank = rank;",
            "  return 1;",
            "}",
            "",
            "const char *amiga_os_compatibility_version_name(AmigaOsCompatVersion version) {",
            "  size_t index = (size_t)version;",
            "  if (index >= sizeof(g_amiga_os_compatibility_version_names) / sizeof(g_amiga_os_compatibility_version_names[0]))",
            "    return NULL;",
            "  return g_amiga_os_compatibility_version_names[index];",
            "}",
            "",
            "AmigaOsCompatVersion amiga_os_parse_compatibility_version(const char *version) {",
            "  size_t index;",
            "  if (version == NULL || version[0] == '\\0') return AMIGA_OS_COMPAT_VERSION_NONE;",
            "  for (index = 1U; index < sizeof(g_amiga_os_compatibility_version_names) / sizeof(g_amiga_os_compatibility_version_names[0]); ++index) {",
            "    const char *candidate = g_amiga_os_compatibility_version_names[index];",
            "    if (candidate != NULL && strcmp(version, candidate) == 0) return (AmigaOsCompatVersion)index;",
            "  }",
            "  return AMIGA_OS_COMPAT_VERSION_NONE;",
            "}",
            "",
            "AmigaOsCompatVersion amiga_os_normalize_compatibility_version_enum(const char *version) {",
            "  size_t index;",
            "  unsigned long rank = 0UL;",
            "  AmigaOsCompatVersion parsed = amiga_os_parse_compatibility_version(version);",
            "  if (parsed != AMIGA_OS_COMPAT_VERSION_NONE) return parsed;",
            "  if (!amiga_os_parse_compatibility_version_rank(version, &rank)) return AMIGA_OS_COMPAT_VERSION_NONE;",
            "  for (index = 1U; index < sizeof(g_amiga_os_compatibility_version_ranks) / sizeof(g_amiga_os_compatibility_version_ranks[0]); ++index) {",
            "    if ((unsigned long)g_amiga_os_compatibility_version_ranks[index] >= rank)",
            "      return (AmigaOsCompatVersion)index;",
            "  }",
            "  return AMIGA_OS_COMPAT_VERSION_NONE;",
            "}",
            "",
            "AmigaOsCompatVersion amiga_os_find_include_min_compat_version_by_id(uint16_t include_id) {",
            "  size_t index;",
            "  if (include_id == 0U) return AMIGA_OS_COMPAT_VERSION_NONE;",
            "  for (index = 0U; index < AMIGA_OS_INCLUDE_MIN_VERSION_COUNT; ++index) {",
            "    const AmigaOsIncludeMinVersionInfo *entry = &g_amiga_os_include_min_versions[index];",
            "    if (entry->include_id == include_id) return (AmigaOsCompatVersion)entry->min_version;",
            "  }",
            "  return AMIGA_OS_COMPAT_VERSION_NONE;",
            "}",
            "",
            "const char *amiga_os_find_include_min_version(const char *include_path) {",
            "  return amiga_os_compatibility_version_name(amiga_os_find_include_min_compat_version(include_path));",
            "}",
            "",
            "AmigaOsCompatVersion amiga_os_find_include_min_compat_version(const char *include_path) {",
            "  char normalized[128];",
            "  if (include_path == NULL || include_path[0] == '\\0') return AMIGA_OS_COMPAT_VERSION_NONE;",
            "  amiga_os_normalize_include_path_copy(normalized, sizeof(normalized), include_path);",
            "  return amiga_os_find_include_min_compat_version_by_id(amiga_os_name_id(%du, normalized));" % NAME_DOMAIN_INCLUDE,
            "}",
            "",
            "int amiga_os_is_supported_compatibility_version(const char *version) {",
            "  return amiga_os_parse_compatibility_version(version) != AMIGA_OS_COMPAT_VERSION_NONE;",
            "}",
            "",
            "const char *amiga_os_normalize_compatibility_version(const char *version) {",
            "  return amiga_os_compatibility_version_name(amiga_os_normalize_compatibility_version_enum(version));",
            "}",
            "",
            "uint16_t amiga_os_find_symbol_include_id(uint16_t symbol_id) {",
            "  size_t index;",
            "  if (amiga_os_name(%du, symbol_id) == NULL) return AMIGA_OS_INCLUDE_ID_NONE;" % NAME_DOMAIN_SYMBOL,
            "  for (index = 0U; index < AMIGA_OS_SYMBOL_INCLUDE_COUNT; ++index) {",
            "    const AmigaOsSymbolIncludeInfo *entry = &g_amiga_os_symbol_includes[index];",
            "    if (entry->symbol_id == symbol_id) return entry->include_id;",
            "  }",
            "  return AMIGA_OS_INCLUDE_ID_NONE;",
            "}",
            "",
            "const char *amiga_os_find_symbol_include(const char *symbol_name) {",
            "  uint16_t include_id = amiga_os_find_symbol_include_id(amiga_os_name_id(%du, symbol_name));" % NAME_DOMAIN_SYMBOL,
            "  return amiga_os_name(%du, include_id);" % NAME_DOMAIN_INCLUDE,
            "}",
            "",
        ]
    )
    SOURCE_PATH.write_text("\n".join(lines), encoding="ascii")


def main() -> None:
    includes_payload = json.loads(INCLUDES_PATH.read_text(encoding="utf-8"))
    other_payload = json.loads(OTHER_PATH.read_text(encoding="utf-8"))
    corrections_payload = json.loads(CORRECTIONS_PATH.read_text(encoding="utf-8"))
    naming_rules_payload = json.loads(NAMING_RULES_PATH.read_text(encoding="utf-8"))
    api_input_value_domains = build_api_input_value_domain_map(includes_payload, corrections_payload)
    api_input_semantic_kinds = build_api_input_semantic_kind_map(includes_payload, corrections_payload)
    api_input_type_overrides = build_api_input_type_override_map(corrections_payload)
    merged_domains = build_merged_value_domains(includes_payload, corrections_payload)
    constant_rows = build_constant_rows(includes_payload)
    value_domain_rows_data = value_domain_rows(merged_domains)
    domain_member_rows, domain_constant_rows = build_domain_member_rows(merged_domains, constant_rows)
    domain_constant_rows = include_resident_vector_constant_rows(includes_payload, constant_rows, domain_constant_rows)
    constant_row_by_name = {symbol_name: (symbol_name, value, include_path) for symbol_name, value, include_path in constant_rows}
    constant_row_by_name.update({symbol_name: (symbol_name, value, include_path) for symbol_name, value, include_path in domain_constant_rows})
    domain_constant_rows = sorted(constant_row_by_name.values(), key=lambda row: row[0])
    api_input_binding_rows = sorted((library_name, function_name, input_name, domain_name)
                                    for (library_name, function_name, input_name), domain_name
                                    in api_input_value_domains.items())
    struct_field_binding_rows = ensure_core_struct_field_value_domain_rows(
        build_struct_field_value_domain_rows(includes_payload, corrections_payload),
        merged_domains,
    )
    compatibility_versions_data = compatibility_versions(includes_payload)
    include_min_versions_data = include_min_version_rows(includes_payload)
    rows = library_rows(includes_payload, other_payload)
    field_rows = struct_field_rows(includes_payload,
                                   referenced_struct_names(rows, includes_payload, other_payload,
                                                           api_input_value_domains, api_input_semantic_kinds,
                                                           api_input_type_overrides))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_header(rows, field_rows, value_domain_rows_data, domain_member_rows, api_input_binding_rows,
                 struct_field_binding_rows, domain_constant_rows, compatibility_versions_data,
                 include_min_versions_data, includes_payload, other_payload,
                 api_input_value_domains, api_input_semantic_kinds, api_input_type_overrides,
                 naming_rules_payload)
    write_source(rows, field_rows, value_domain_rows_data, domain_member_rows, api_input_binding_rows,
                 struct_field_binding_rows, domain_constant_rows, compatibility_versions_data,
                 include_min_versions_data, includes_payload, other_payload,
                 api_input_value_domains, api_input_semantic_kinds, api_input_type_overrides,
                 naming_rules_payload)


if __name__ == "__main__":
    main()
