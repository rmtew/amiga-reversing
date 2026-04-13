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


def write_header(rows: list[tuple[str, str, int, str, dict]], includes_payload: dict) -> None:
    io_device_offset = struct_field_offset(includes_payload, "IO", "IO_DEVICE")
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
        "  const char *input_a1_struct_name;",
        "} AmigaOsLibraryVectorInfo;",
        "",
        "const char *amiga_os_find_library_base_name(const char *library_name);",
        "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector(const char *base_name, int16_t lvo);",
        "const AmigaOsLibraryVectorInfo *amiga_os_find_library_vector_by_symbol_name(const char *lvo_symbol_name);",
        "",
        f"#define AMIGA_OS_LIBRARY_VECTOR_COUNT {len(rows)}u",
    ]
    if io_device_offset is not None:
        lines.append(f"#define AMIGA_OS_STRUCT_IO_FIELD_IO_DEVICE_OFFSET {io_device_offset}u")
    lines.extend(["", "#endif", ""])
    HEADER_PATH.write_text("\n".join(lines), encoding="ascii")


def write_source(rows: list[tuple[str, str, int, str, dict]]) -> None:
    lines = [
        "/* Generated Amiga OS runtime metadata. Do not edit directly. */",
        '#include "generated/amiga_os_runtime.h"',
        "",
        "#include <string.h>",
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
        output_struct_name = reg_name(output, "i_struct")
        input_a1_struct_name = input_struct_for_reg(other_info, "A1")
        lines.append(
            '  { "%s", "%s", %d, "%s", "%s", %s, %s, %s, %s, %s },'
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
                "NULL" if input_a1_struct_name is None else f'"{c_string(input_a1_struct_name)}"',
            )
        )
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
            "",
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
        ]
    )
    SOURCE_PATH.write_text("\n".join(lines), encoding="ascii")


def main() -> None:
    includes_payload = json.loads(INCLUDES_PATH.read_text(encoding="utf-8"))
    other_payload = json.loads(OTHER_PATH.read_text(encoding="utf-8"))
    rows = library_rows(includes_payload, other_payload)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_header(rows, includes_payload)
    write_source(rows)


if __name__ == "__main__":
    main()
