from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMUTOS_INCLUDE = ROOT / "resources" / "clone_atari_st" / "emutos" / "include"
EMUTOS_DOC = ROOT / "resources" / "clone_atari_st" / "emutos" / "doc"
OUTPUT_DIR = ROOT / "src" / "generated"
HEADER_PATH = OUTPUT_DIR / "atari_st_os_runtime.h"
SOURCE_PATH = OUTPUT_DIR / "atari_st_os_runtime.c"
ATARI_ST_INCLUDE_DIR = ROOT / "ext" / "atarist_includes" / "devpac_3_10" / "include"
ATARI_ST_INCLUDE_SOURCE_DIR = ATARI_ST_INCLUDE_DIR

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
NAME_DOMAIN_FAMILY = 11
NAME_DOMAIN_HEADER = 12

SOURCES = [
    (
        "GEMDOS",
        1,
        "bdosbind.h",
        re.compile(r"^#define\s+([A-Za-z_]\w*)\(([^)]*)\)\s+trap1\(\s*(0x[0-9A-Fa-f]+|\d+)(?:\s*,\s*(.*))?\)\s*$"),
    ),
    (
        "BIOS",
        13,
        "biosbind.h",
        re.compile(r"^#define\s+([A-Za-z_]\w*)\([^)]*\)\s+(bios_[A-Za-z0-9_]+)\(\s*(0x[0-9A-Fa-f]+|\d+)"),
    ),
    (
        "XBIOS",
        14,
        "xbiosbind.h",
        re.compile(r"^#define\s+([A-Za-z_]\w*)\([^)]*\)\s+(xbios_[A-Za-z0-9_]+)\(\s*(0x[0-9A-Fa-f]+|\d+)"),
    ),
]

RETURN_KIND_VOID = "ATARI_ST_OS_RETURN_VOID"
RETURN_KIND_WORD = "ATARI_ST_OS_RETURN_WORD"
RETURN_KIND_LONG = "ATARI_ST_OS_RETURN_LONG"

STATUS_GEMDOS_SECTION = re.compile(r"^\s*GEMDOS Functions\s*$")
STATUS_SECTION_HEADER = re.compile(r"^\S")
STATUS_GEMDOS_ROW = re.compile(r"^\s*[TtX>]\s+0x([0-9A-Fa-f]+)\s+([A-Za-z_][A-Za-z0-9_]*)\s*$")


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
            "id_map": {value: index for index, value in enumerate(values, start=1)},
        })
    return items


def name_id_literal(name_domain_meta: list[dict], label: str, value: str | None) -> str:
    if value is None:
        return "0u"
    for item in name_domain_meta:
        if item["label"] == label:
            return item["enum_values"][value]
    raise KeyError(label)


def family_include_path(family_name: str) -> str:
    if family_name == "GEMDOS":
        return "GEMDOS.I"
    if family_name == "BIOS":
        return "BIOS.I"
    if family_name == "XBIOS":
        return "XBIOS.I"
    raise ValueError(f"unsupported Atari ST include family: {family_name}")


def original_include_filename(family_name: str) -> str:
    if family_name == "GEMDOS":
        return "GEMDOS.I"
    if family_name == "BIOS":
        return "BIOS.I"
    if family_name == "XBIOS":
        return "XBIOS.I"
    raise ValueError(f"unsupported Atari ST original include family: {family_name}")


def parse_original_include_entries(family_name: str) -> list[tuple[str, int]]:
    pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+equ\s+(\$[0-9A-Fa-f]+|0x[0-9A-Fa-f]+|\d+)\s*$", re.IGNORECASE)
    entries: list[tuple[str, int]] = []
    path = ATARI_ST_INCLUDE_SOURCE_DIR / original_include_filename(family_name)
    for raw_line in path.read_text(encoding="latin-1").splitlines():
        match = pattern.match(raw_line)
        if not match:
            continue
        opcode = int(match.group(2).replace("$", "0x"), 0)
        entries.append((match.group(1), opcode))
    return entries


def split_csv(text: str | None) -> list[str]:
    if text is None:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def parse_helper_signature(helper_name: str) -> tuple[str, int]:
    prefix, return_code, arg_codes = helper_name.split("_", 2)
    if prefix not in {"bios", "xbios"}:
        raise ValueError(f"unexpected helper prefix: {helper_name}")
    if return_code == "v":
        return_kind = RETURN_KIND_VOID
    elif return_code == "w":
        return_kind = RETURN_KIND_WORD
    elif return_code == "l":
        return_kind = RETURN_KIND_LONG
    else:
        raise ValueError(f"unexpected return code in helper: {helper_name}")
    cleanup_bytes = 2
    for code in arg_codes:
        if code == "v":
            continue
        if code == "w":
            cleanup_bytes += 2
        elif code == "l":
            cleanup_bytes += 4
        else:
            raise ValueError(f"unexpected arg code in helper: {helper_name}")
    return return_kind, cleanup_bytes


def parse_status_gemdos_rows() -> list[tuple[str, int, int, str, str, str, int, int, int]]:
    rows: list[tuple[str, int, int, str, str, str, int, int, int]] = []
    in_section = False
    path = EMUTOS_DOC / "status.txt"
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.rstrip()
        if not in_section:
            if STATUS_GEMDOS_SECTION.match(line):
                in_section = True
            continue
        if STATUS_SECTION_HEADER.match(line) and "GEMDOS" not in line and not line.startswith(" ") and not line.startswith("\t"):
            break
        match = STATUS_GEMDOS_ROW.match(line)
        if not match:
            continue
        opcode = int(match.group(1), 16)
        function_name = match.group(2)
        rows.append(("GEMDOS", 1, opcode, function_name, "status.txt", RETURN_KIND_LONG, 0, 0, 0))
    return rows


def parse_rows() -> list[tuple[str, int, int, str, str, str, int, int, int]]:
    rows: list[tuple[str, int, int, str, str, str, int, int, int]] = []
    seen_keys: set[tuple[int, int, str]] = set()
    seen_opcodes: set[tuple[int, int]] = set()
    for family_name, trap_vector, filename, pattern in SOURCES:
        path = EMUTOS_INCLUDE / filename
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = pattern.match(line.strip())
            if not match:
                continue
            function_name = match.group(1)
            if family_name == "GEMDOS":
                opcode = int(match.group(3), 0)
                arg_count = len(split_csv(match.group(4)))
                return_kind = RETURN_KIND_LONG
                cleanup_known = 1 if arg_count == 0 else 0
                cleanup_bytes = 2 if arg_count == 0 else 0
            else:
                helper_name = match.group(2)
                opcode = int(match.group(3), 0)
                return_kind, cleanup_bytes = parse_helper_signature(helper_name)
                arg_count = 0
                cleanup_known = 1
            key = (trap_vector, opcode, function_name)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            seen_opcodes.add((trap_vector, opcode))
            rows.append((family_name, trap_vector, opcode, function_name, filename, return_kind, cleanup_known,
                         cleanup_bytes, arg_count))
    for family_name, trap_vector, opcode, function_name, source_name, return_kind, cleanup_known, cleanup_bytes, arg_count in parse_status_gemdos_rows():
        if (trap_vector, opcode) in seen_opcodes:
            continue
        key = (trap_vector, opcode, function_name)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        seen_opcodes.add((trap_vector, opcode))
        rows.append((family_name, trap_vector, opcode, function_name, source_name, return_kind, cleanup_known,
                     cleanup_bytes, arg_count))
    rows.sort(key=lambda row: (row[1], row[2], row[0], row[3]))
    return rows


def build_name_domains(rows: list[tuple[str, int, int, str, str, str, int, int, int]]) -> list[tuple[int, str, list[str]]]:
    original_symbol_maps = {
        "GEMDOS": dict((opcode, symbol_name) for symbol_name, opcode in parse_original_include_entries("GEMDOS")),
        "BIOS": dict((opcode, symbol_name) for symbol_name, opcode in parse_original_include_entries("BIOS")),
        "XBIOS": dict((opcode, symbol_name) for symbol_name, opcode in parse_original_include_entries("XBIOS")),
    }
    family_names: set[str] = set()
    function_names: set[str] = set()
    symbol_names: set[str] = set()
    include_paths: set[str] = set()
    header_names: set[str] = set()
    for family_name, _, opcode, function_name, source_header, _, _, _, _ in rows:
        original_symbol = original_symbol_maps.get(family_name, {}).get(opcode)
        family_names.add(family_name)
        function_names.add(function_name)
        symbol_names.add(original_symbol if original_symbol is not None else f"{family_name}_{function_name}")
        header_names.add(source_header)
        if original_symbol is not None:
            include_paths.add(family_include_path(family_name))
    return [
        (NAME_DOMAIN_FAMILY, "family", sorted(family_names)),
        (NAME_DOMAIN_FUNCTION, "function", sorted(function_names)),
        (NAME_DOMAIN_SYMBOL, "symbol", sorted(symbol_names)),
        (NAME_DOMAIN_INCLUDE, "include", sorted(include_paths)),
        (NAME_DOMAIN_HEADER, "header", sorted(header_names)),
    ]


def write_header(rows: list[tuple[str, int, int, str, str, str, int, int, int]]) -> None:
    name_domains = build_name_domains(rows)
    name_domain_meta = build_name_domain_meta(name_domains, "ATARI_ST_OS")
    lines = [
        "/* Generated Atari ST OS runtime metadata from EmuTOS headers.",
        " * Sources:",
        " *  - resources/clone_atari_st/emutos/include/bdosbind.h",
        " *  - resources/clone_atari_st/emutos/include/biosbind.h",
        " *  - resources/clone_atari_st/emutos/include/xbiosbind.h",
        " *  - resources/clone_atari_st/emutos/doc/status.txt",
        " * Do not edit directly.",
        " */",
        "#ifndef ATARI_ST_OS_RUNTIME_H",
        "#define ATARI_ST_OS_RUNTIME_H",
        "",
        "#include <stddef.h>",
        "#include <stdint.h>",
        "",
        "typedef enum AtariStOsReturnKind {",
        "  ATARI_ST_OS_RETURN_VOID = 0,",
        "  ATARI_ST_OS_RETURN_WORD = 1,",
        "  ATARI_ST_OS_RETURN_LONG = 2",
        "} AtariStOsReturnKind;",
        "",
    ]
    for item in name_domain_meta:
        lines.extend([
            f"typedef enum {item['enum_type']} {{",
            f"  {item['enum_prefix']}_NONE = 0,",
        ])
        for value in item["values"]:
            lines.append(f"  {item['enum_values'][value]} = {item['id_map'][value]},")
        lines.extend([f"}} {item['enum_type']};", ""])
    lines.extend([
        "typedef struct AtariStOsCallInfo {",
        "  uint16_t family_id;",
        "  uint8_t trap_vector;",
        "  uint16_t opcode;",
        "  uint16_t function_id;",
        "  uint16_t symbol_id;",
        "  uint16_t source_header_id;",
        "  uint16_t include_id;",
        "  uint8_t stack_cleanup_known;",
        "  uint16_t stack_cleanup_bytes;",
        "  uint8_t arg_count;",
        "  uint8_t return_kind;",
        "} AtariStOsCallInfo;",
        "",
        f"#define ATARI_ST_OS_CALL_COUNT {len(rows)}u",
        "",
        "uint16_t atari_st_os_name_id(uint8_t domain_kind, const char *name);",
        "const char *atari_st_os_name(uint8_t domain_kind, uint16_t id);",
        "const AtariStOsCallInfo *atari_st_os_find_call_by_symbol_id(uint16_t symbol_id);",
        "const AtariStOsCallInfo *atari_st_os_find_call(uint8_t trap_vector, uint16_t opcode);",
        "const AtariStOsCallInfo *atari_st_os_find_call_by_symbol_name(const char *symbol_name);",
        "uint16_t atari_st_os_find_symbol_include_id(uint16_t symbol_id);",
        "const char *atari_st_os_find_symbol_include(const char *symbol_name);",
        "",
        "#endif",
        "",
    ])
    HEADER_PATH.write_text("\n".join(lines), encoding="ascii")


def write_source(rows: list[tuple[str, int, int, str, str, str, int, int, int]]) -> None:
    original_symbol_maps = {
        "GEMDOS": dict((opcode, symbol_name) for symbol_name, opcode in parse_original_include_entries("GEMDOS")),
        "BIOS": dict((opcode, symbol_name) for symbol_name, opcode in parse_original_include_entries("BIOS")),
        "XBIOS": dict((opcode, symbol_name) for symbol_name, opcode in parse_original_include_entries("XBIOS")),
    }
    name_domains = build_name_domains(rows)
    name_domain_meta = build_name_domain_meta(name_domains, "ATARI_ST_OS")
    lines = [
        "/* Generated Atari ST OS runtime metadata from EmuTOS headers. Do not edit directly. */",
        '#include "generated/atari_st_os_runtime.h"',
        "",
        "#include <string.h>",
        "",
    ]
    for _, label, values in name_domains:
        lines.extend([
            f"static const char *const g_atari_st_os_{label}_names[] = {{",
            "  NULL,",
        ])
        for value in values:
            lines.append(f'  "{c_string(value)}",')
        lines.extend(["};", ""])
    lines.extend([
        "static uint16_t atari_st_os_name_id_from_table(const char *const *names, size_t count, const char *name) {",
        "  size_t index;",
        "  if (names == NULL || name == NULL || name[0] == '\\0') return 0U;",
        "  for (index = 1U; index < count; ++index) {",
        "    if (strcmp(names[index], name) == 0) return (uint16_t)index;",
        "  }",
        "  return 0U;",
        "}",
        "",
        "static const char *atari_st_os_name_from_table(const char *const *names, size_t count, uint16_t id) {",
        "  if (names == NULL || id == 0U || (size_t)id >= count) return NULL;",
        "  return names[id];",
        "}",
        "",
        "uint16_t atari_st_os_name_id(uint8_t domain_kind, const char *name) {",
        "  switch (domain_kind) {",
    ])
    for domain_kind, label, _ in name_domains:
        lines.append(
            f"  case {domain_kind}u: return atari_st_os_name_id_from_table(g_atari_st_os_{label}_names, "
            f"sizeof(g_atari_st_os_{label}_names) / sizeof(g_atari_st_os_{label}_names[0]), name);")
    lines.extend([
        "  default: return 0U;",
        "  }",
        "}",
        "",
        "const char *atari_st_os_name(uint8_t domain_kind, uint16_t id) {",
        "  switch (domain_kind) {",
    ])
    for domain_kind, label, _ in name_domains:
        lines.append(
            f"  case {domain_kind}u: return atari_st_os_name_from_table(g_atari_st_os_{label}_names, "
            f"sizeof(g_atari_st_os_{label}_names) / sizeof(g_atari_st_os_{label}_names[0]), id);")
    lines.extend([
        "  default: return NULL;",
        "  }",
        "}",
        "",
        "static const AtariStOsCallInfo g_atari_st_os_calls[] = {",
    ])
    for family_name, trap_vector, opcode, function_name, source_header, return_kind, cleanup_known, cleanup_bytes, arg_count in rows:
        original_symbol = original_symbol_maps.get(family_name, {}).get(opcode)
        symbol_name = original_symbol if original_symbol is not None else f"{family_name}_{function_name}"
        include_path = family_include_path(family_name) if original_symbol is not None else None
        lines.append(
            "  { %s, %du, %du, %s, %s, %s, %s, %du, %du, %du, %s },"
            % (
                name_id_literal(name_domain_meta, "family", family_name),
                trap_vector,
                opcode,
                name_id_literal(name_domain_meta, "function", function_name),
                name_id_literal(name_domain_meta, "symbol", symbol_name),
                name_id_literal(name_domain_meta, "header", source_header),
                name_id_literal(name_domain_meta, "include", include_path),
                cleanup_known,
                cleanup_bytes,
                arg_count,
                return_kind,
            )
        )
    lines.extend(
        [
            "};",
            "",
            "const AtariStOsCallInfo *atari_st_os_find_call(uint8_t trap_vector, uint16_t opcode) {",
            "  size_t low = 0U;",
            "  size_t high = ATARI_ST_OS_CALL_COUNT;",
            "  while (low < high) {",
            "    size_t mid = low + ((high - low) / 2U);",
            "    const AtariStOsCallInfo *entry = &g_atari_st_os_calls[mid];",
            "    if (trap_vector == entry->trap_vector) {",
            "      if (opcode == entry->opcode) return entry;",
            "      if (opcode < entry->opcode) high = mid;",
            "      else low = mid + 1U;",
            "      continue;",
            "    }",
            "    if (trap_vector < entry->trap_vector) high = mid;",
            "    else low = mid + 1U;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const AtariStOsCallInfo *atari_st_os_find_call_by_symbol_id(uint16_t symbol_id) {",
            "  size_t index;",
            "  if (symbol_id == 0U) return NULL;",
            "  for (index = 0U; index < ATARI_ST_OS_CALL_COUNT; ++index) {",
            "    const AtariStOsCallInfo *entry = &g_atari_st_os_calls[index];",
            "    if (entry->symbol_id == symbol_id) return entry;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const AtariStOsCallInfo *atari_st_os_find_call_by_symbol_name(const char *symbol_name) {",
            f"  return atari_st_os_find_call_by_symbol_id(atari_st_os_name_id({NAME_DOMAIN_SYMBOL}u, symbol_name));",
            "}",
            "",
            "uint16_t atari_st_os_find_symbol_include_id(uint16_t symbol_id) {",
            "  const AtariStOsCallInfo *entry = atari_st_os_find_call_by_symbol_id(symbol_id);",
            "  return entry != NULL ? entry->include_id : 0U;",
            "}",
            "",
            "const char *atari_st_os_find_symbol_include(const char *symbol_name) {",
            f"  uint16_t include_id = atari_st_os_find_symbol_include_id(atari_st_os_name_id({NAME_DOMAIN_SYMBOL}u, symbol_name));",
            f"  return atari_st_os_name({NAME_DOMAIN_INCLUDE}u, include_id);",
            "}",
            "",
        ]
    )
    SOURCE_PATH.write_text("\n".join(lines), encoding="ascii")


def main() -> None:
    rows = parse_rows()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_header(rows)
    write_source(rows)


if __name__ == "__main__":
    main()
