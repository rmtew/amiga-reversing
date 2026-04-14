from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INCLUDES_PATH = ROOT / "knowledge" / "amiga_ndk_includes_parsed.json"
OTHER_PATH = ROOT / "knowledge" / "amiga_ndk_other_parsed.json"
OUTPUT_DIR = ROOT / "src" / "generated"
HEADER_PATH = OUTPUT_DIR / "amiga_os_runtime.h"
SOURCE_PATH = OUTPUT_DIR / "amiga_os_runtime.c"


def c_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def normalize_include_path(path: str | None) -> str | None:
    if not isinstance(path, str) or not path:
        return None
    normalized = path.replace("\\", "/").strip()
    if ":" in normalized:
        return None
    return normalized.lower()


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


def input_struct_for_reg(other_info: dict, reg_name_text: str) -> str | None:
    for item in other_info.get("inputs", []):
        if not isinstance(item, dict):
            continue
        regs = item.get("regs")
        if not isinstance(regs, list) or reg_name_text not in regs:
            continue
        value = item.get("i_struct")
        if isinstance(value, str) and value:
            return value
    return None


def first_input_struct(other_info: dict) -> tuple[str | None, str | None]:
    for item in other_info.get("inputs", []):
        if not isinstance(item, dict):
            continue
        struct_name = item.get("i_struct")
        regs = item.get("regs")
        if not isinstance(struct_name, str) or not struct_name:
            continue
        if not isinstance(regs, list) or not regs:
            continue
        reg_name_text = regs[0]
        if isinstance(reg_name_text, str) and reg_name_text:
            return reg_name_text, struct_name
    return None, None


def output_struct_for_function(function_name: str, other_info: dict) -> str | None:
    output = other_info.get("output")
    value = reg_name(output, "i_struct")
    if value:
        return value
    if not isinstance(output, dict):
        return None
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
            other_info = other_functions.get(library_name, {}).get(function_name, {})
            if not isinstance(other_info, dict):
                other_info = {}
            rows.append((library_name, base_name, lvo, function_name, other_info))
    rows.sort(key=lambda row: (row[1], row[2], row[0], row[3]))
    return rows


def referenced_struct_names(rows: list[tuple[str, str, int, str, dict]]) -> list[str]:
    names: set[str] = set()
    for _, _, _, _, other_info in rows:
        if not isinstance(other_info, dict):
            continue
        output = other_info.get("output")
        if isinstance(output, dict):
            value = output.get("i_struct")
            if isinstance(value, str) and value:
                names.add(value)
        input_struct_reg_name, input_struct_name = first_input_struct(other_info)
        if input_struct_reg_name and input_struct_name:
            names.add(input_struct_name)
    return sorted(names)


def struct_field_rows(includes_payload: dict, struct_names: list[str]) -> list[tuple[str, int, str, str | None]]:
    rows: list[tuple[str, int, str, str | None]] = []
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
            rows.append((struct_name, int(offset), field_name, nested_type_name))
    rows.sort(key=lambda row: (row[0], row[1], row[2]))
    return rows


def symbol_include_rows(includes_payload: dict,
                        rows: list[tuple[str, str, int, str, dict]],
                        field_rows: list[tuple[str, int, str, str | None]]) -> list[tuple[str, str]]:
    entries: dict[str, str] = {}
    libraries = includes_payload.get("libraries", {})
    structs = includes_payload.get("structs", {})

    for library_name, _, _, function_name, _ in rows:
        library = libraries.get(library_name, {})
        if not isinstance(library, dict):
            continue
        owner = library.get("owner", {})
        include_path = normalize_include_path(owner.get("assembler_include_path") if isinstance(owner, dict) else None)
        if include_path is None:
            continue
        entries.setdefault(f"_LVO{function_name}", include_path)

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

    return sorted(entries.items(), key=lambda row: (row[1], row[0]))


def write_header(rows: list[tuple[str, str, int, str, dict]], field_rows: list[tuple[str, int, str, str | None]],
                 includes_payload: dict) -> None:
    io_device_offset = struct_field_offset(includes_payload, "IO", "IO_DEVICE")
    symbol_include_rows_data = symbol_include_rows(includes_payload, rows, field_rows)
    lines = [
        "/* Generated Amiga OS runtime metadata. Do not edit directly. */",
        "#ifndef AMIGA_OS_RUNTIME_H",
        "#define AMIGA_OS_RUNTIME_H",
        "",
        "#include <stddef.h>",
        "#include <stdint.h>",
        "",
        "typedef struct AmigaOsLibraryVectorInfo {",
        "  const char *library_name;",
        "  const char *base_name;",
        "  int16_t lvo;",
        "  const char *function_name;",
        "  const char *lvo_symbol_name;",
        "  const char *returns_base_reg_name;",
        "  const char *returns_base_name_reg_name;",
        "  const char *output_reg_name;",
        "  const char *output_struct_name;",
        "  const char *input_struct_reg_name;",
        "  const char *input_struct_name;",
        "} AmigaOsLibraryVectorInfo;",
        "",
        "typedef struct AmigaOsStructFieldInfo {",
        "  const char *struct_name;",
        "  int16_t offset;",
        "  const char *field_name;",
        "  const char *nested_type_name;",
        "} AmigaOsStructFieldInfo;",
        "",
        "const char *amiga_os_find_library_base_name(const char *library_name);",
        "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector(const char *base_name, int16_t lvo);",
        "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_symbol_name(const char *lvo_symbol_name);",
        "const AmigaOsStructFieldInfo *amiga_os_find_struct_field(const char *struct_name, int16_t offset);",
        "const AmigaOsStructFieldInfo *amiga_os_find_struct_field_by_symbol_name(const char *field_name);",
        "const char *amiga_os_find_symbol_include(const char *symbol_name);",
        "",
        f"#define AMIGA_OS_LIBRARY_VECTOR_COUNT {len(rows)}u",
        f"#define AMIGA_OS_STRUCT_FIELD_COUNT {len(field_rows)}u",
        f"#define AMIGA_OS_SYMBOL_INCLUDE_COUNT {len(symbol_include_rows_data)}u",
    ]
    if io_device_offset is not None:
        lines.append(f"#define AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET {io_device_offset}u")
    lines.extend(["", "#endif", ""])
    HEADER_PATH.write_text("\n".join(lines), encoding="ascii")


def write_source(rows: list[tuple[str, str, int, str, dict]], field_rows: list[tuple[str, int, str, str | None]],
                 includes_payload: dict) -> None:
    symbol_include_rows_data = symbol_include_rows(includes_payload, rows, field_rows)
    lines = [
        "/* Generated Amiga OS runtime metadata. Do not edit directly. */",
        '#include "generated/amiga_os_runtime.h"',
        "",
        "#include <string.h>",
        "",
        "typedef struct AmigaOsSymbolIncludeInfo {",
        "  const char *symbol_name;",
        "  const char *include_path;",
        "} AmigaOsSymbolIncludeInfo;",
        "",
        "static const AmigaOsLibraryVectorInfo g_amiga_os_library_vectors[] = {",
    ]
    for library_name, base_name, lvo, function_name, other_info in rows:
        returns_base = other_info.get("returns_base") if isinstance(other_info, dict) else None
        output = other_info.get("output") if isinstance(other_info, dict) else None
        lvo_name = f"_LVO{function_name}"
        returns_base_reg_name = reg_name(returns_base, "base_reg")
        returns_base_name_reg_name = reg_name(returns_base, "name_reg")
        output_reg_name = reg_name(output, "reg")
        output_struct_name = output_struct_for_function(function_name, other_info)
        input_struct_reg_name, input_struct_name = first_input_struct(other_info)
        lines.append(
            '  { "%s", "%s", %d, "%s", "%s", %s, %s, %s, %s, %s, %s },'
            % (
                c_string(library_name),
                c_string(base_name),
                lvo,
                c_string(function_name),
                c_string(lvo_name),
                "NULL" if returns_base_reg_name is None else f'"{c_string(returns_base_reg_name)}"',
                "NULL" if returns_base_name_reg_name is None else f'"{c_string(returns_base_name_reg_name)}"',
                "NULL" if output_reg_name is None else f'"{c_string(output_reg_name)}"',
                "NULL" if output_struct_name is None else f'"{c_string(output_struct_name)}"',
                "NULL" if input_struct_reg_name is None else f'"{c_string(input_struct_reg_name)}"',
                "NULL" if input_struct_name is None else f'"{c_string(input_struct_name)}"',
            )
        )
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsStructFieldInfo g_amiga_os_struct_fields[] = {",
        ]
    )
    for struct_name, offset, field_name, nested_type_name in field_rows:
        lines.append(
            '  { "%s", %d, "%s", %s },'
            % (
                c_string(struct_name),
                offset,
                c_string(field_name),
                "NULL" if nested_type_name is None else f'"{c_string(nested_type_name)}"',
            )
        )
    lines.extend(
        [
            "};",
            "",
            "static const AmigaOsSymbolIncludeInfo g_amiga_os_symbol_includes[] = {",
        ]
    )
    for symbol_name, include_path in symbol_include_rows_data:
        lines.append('  { "%s", "%s" },' % (c_string(symbol_name), c_string(include_path)))
    lines.extend(
        [
            "};",
            "",
            "const char *amiga_os_find_library_base_name(const char *library_name) {",
            "  size_t index;",
            "  if (library_name == NULL || library_name[0] == '\\0') return NULL;",
            "  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {",
            "    const AmigaOsLibraryVectorInfo *entry = &g_amiga_os_library_vectors[index];",
            "    if (strcmp(library_name, entry->library_name) == 0) return entry->base_name;",
            "  }",
            "  return NULL;",
            "}",
            "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector(const char *base_name, int16_t lvo) {",
            "  size_t low = 0U;",
            "  size_t high = AMIGA_OS_LIBRARY_VECTOR_COUNT;",
            "  if (base_name == NULL || base_name[0] == '\\0') return NULL;",
            "  while (low < high) {",
            "    size_t mid = low + ((high - low) / 2U);",
            "    const AmigaOsLibraryVectorInfo *entry = &g_amiga_os_library_vectors[mid];",
            "    int base_cmp = strcmp(base_name, entry->base_name);",
            "    if (base_cmp == 0) {",
            "      if (lvo == entry->lvo) return entry;",
            "      if (lvo < entry->lvo) high = mid;",
            "      else low = mid + 1U;",
            "      continue;",
            "    }",
            "    if (base_cmp < 0) high = mid;",
            "    else low = mid + 1U;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_symbol_name(const char *lvo_symbol_name) {",
            "  size_t index;",
            "  if (lvo_symbol_name == NULL || lvo_symbol_name[0] == '\\0') return NULL;",
            "  for (index = 0U; index < AMIGA_OS_LIBRARY_VECTOR_COUNT; ++index) {",
            "    const AmigaOsLibraryVectorInfo *entry = &g_amiga_os_library_vectors[index];",
            "    if (strcmp(lvo_symbol_name, entry->lvo_symbol_name) == 0) return entry;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const AmigaOsStructFieldInfo *amiga_os_find_struct_field(const char *struct_name, int16_t offset) {",
            "  size_t low = 0U;",
            "  size_t high = AMIGA_OS_STRUCT_FIELD_COUNT;",
            "  if (struct_name == NULL || struct_name[0] == '\\0') return NULL;",
            "  while (low < high) {",
            "    size_t mid = low + ((high - low) / 2U);",
            "    const AmigaOsStructFieldInfo *entry = &g_amiga_os_struct_fields[mid];",
            "    int struct_cmp = strcmp(struct_name, entry->struct_name);",
            "    if (struct_cmp == 0) {",
            "      if (offset == entry->offset) return entry;",
            "      if (offset < entry->offset) high = mid;",
            "      else low = mid + 1U;",
            "      continue;",
            "    }",
            "    if (struct_cmp < 0) high = mid;",
            "    else low = mid + 1U;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const AmigaOsStructFieldInfo *amiga_os_find_struct_field_by_symbol_name(const char *field_name) {",
            "  size_t index;",
            "  if (field_name == NULL || field_name[0] == '\\0') return NULL;",
            "  for (index = 0U; index < AMIGA_OS_STRUCT_FIELD_COUNT; ++index) {",
            "    const AmigaOsStructFieldInfo *entry = &g_amiga_os_struct_fields[index];",
            "    if (strcmp(field_name, entry->field_name) == 0) return entry;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "const char *amiga_os_find_symbol_include(const char *symbol_name) {",
            "  size_t index;",
            "  if (symbol_name == NULL || symbol_name[0] == '\\0') return NULL;",
            "  for (index = 0U; index < AMIGA_OS_SYMBOL_INCLUDE_COUNT; ++index) {",
            "    const AmigaOsSymbolIncludeInfo *entry = &g_amiga_os_symbol_includes[index];",
            "    if (strcmp(symbol_name, entry->symbol_name) == 0) return entry->include_path;",
            "  }",
            "  return NULL;",
            "}",
            "",
        ]
    )
    SOURCE_PATH.write_text("\n".join(lines), encoding="ascii")


def main() -> None:
    includes_payload = json.loads(INCLUDES_PATH.read_text(encoding="utf-8"))
    other_payload = json.loads(OTHER_PATH.read_text(encoding="utf-8"))
    rows = library_rows(includes_payload, other_payload)
    field_rows = struct_field_rows(includes_payload, referenced_struct_names(rows))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_header(rows, field_rows, includes_payload)
    write_source(rows, field_rows, includes_payload)


if __name__ == "__main__":
    main()
