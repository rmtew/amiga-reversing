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


def write_header(rows: list[tuple[str, int, int, str, str, str, int, int, int]]) -> None:
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
        "typedef struct AtariStOsCallInfo {",
        "  const char *family_name;",
        "  uint8_t trap_vector;",
        "  uint16_t opcode;",
        "  const char *function_name;",
        "  const char *symbol_name;",
        "  const char *source_header;",
        "  const char *include_path;",
        "  uint8_t stack_cleanup_known;",
        "  uint16_t stack_cleanup_bytes;",
        "  uint8_t arg_count;",
        "  uint8_t return_kind;",
        "} AtariStOsCallInfo;",
        "",
        f"#define ATARI_ST_OS_CALL_COUNT {len(rows)}u",
        "",
        "const AtariStOsCallInfo *atari_st_os_find_call(uint8_t trap_vector, uint16_t opcode);",
        "const AtariStOsCallInfo *atari_st_os_find_call_by_symbol_name(const char *symbol_name);",
        "const char *atari_st_os_find_symbol_include(const char *symbol_name);",
        "",
        "#endif",
        "",
    ]
    HEADER_PATH.write_text("\n".join(lines), encoding="ascii")


def write_source(rows: list[tuple[str, int, int, str, str, str, int, int, int]]) -> None:
    original_symbol_maps = {
        "GEMDOS": dict((opcode, symbol_name) for symbol_name, opcode in parse_original_include_entries("GEMDOS")),
        "BIOS": dict((opcode, symbol_name) for symbol_name, opcode in parse_original_include_entries("BIOS")),
        "XBIOS": dict((opcode, symbol_name) for symbol_name, opcode in parse_original_include_entries("XBIOS")),
    }
    lines = [
        "/* Generated Atari ST OS runtime metadata from EmuTOS headers. Do not edit directly. */",
        '#include "generated/atari_st_os_runtime.h"',
        "",
        "#include <string.h>",
        "",
        "static const AtariStOsCallInfo g_atari_st_os_calls[] = {",
    ]
    for family_name, trap_vector, opcode, function_name, source_header, return_kind, cleanup_known, cleanup_bytes, arg_count in rows:
        original_symbol = original_symbol_maps.get(family_name, {}).get(opcode)
        symbol_name = original_symbol if original_symbol is not None else f"{family_name}_{function_name}"
        include_path = family_include_path(family_name) if original_symbol is not None else None
        lines.append(
            '  { "%s", %du, %du, "%s", "%s", "%s", %s, %du, %du, %du, %s },'
            % (
                c_string(family_name),
                trap_vector,
                opcode,
                c_string(function_name),
                c_string(symbol_name),
                c_string(source_header),
                "NULL" if include_path is None else f'"{c_string(include_path)}"',
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
            "const AtariStOsCallInfo *atari_st_os_find_call_by_symbol_name(const char *symbol_name) {",
            "  size_t index;",
            "  if (symbol_name == NULL || symbol_name[0] == '\\0') return NULL;",
            "  for (index = 0U; index < ATARI_ST_OS_CALL_COUNT; ++index) {",
            "    const AtariStOsCallInfo *entry = &g_atari_st_os_calls[index];",
            "    if (strcmp(symbol_name, entry->symbol_name) == 0) return entry;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const char *atari_st_os_find_symbol_include(const char *symbol_name) {",
            "  const AtariStOsCallInfo *entry = atari_st_os_find_call_by_symbol_name(symbol_name);",
            "  return (entry != NULL && entry->include_path != NULL && entry->include_path[0] != '\\0') ? entry->include_path : NULL;",
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
