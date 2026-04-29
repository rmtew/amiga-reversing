from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KB_PATH = ROOT / "knowledge" / "m68k_instructions.json"
OUTPUT_PATH = ROOT / "src" / "generated" / "m68k_cpu_runtime.h"


KIND_IDS = {
    "unknown": 0,
    "reset": 1,
    "exception": 2,
    "interrupt": 3,
    "trap": 4,
}


def c_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def vector_symbol_name(name: str) -> str:
    chars: list[str] = []
    last_was_sep = False
    for ch in name.lower():
        if ch.isalnum():
            chars.append(ch)
            last_was_sep = False
        elif not last_was_sep:
            chars.append("_")
            last_was_sep = True
    text = "".join(chars).strip("_")
    return f"m68k_vector_{text}" if text else "m68k_vector_unknown"


def exception_vector_rows(payload: dict) -> list[tuple[int, int, str, str, str]]:
    rows: list[tuple[int, int, str, str, str]] = []
    for item in payload.get("_meta", {}).get("exception_vectors", []):
        if not isinstance(item, dict):
            continue
        vector = item.get("vector")
        address = item.get("address")
        name = item.get("name")
        kind = item.get("kind")
        if not isinstance(vector, int) or not isinstance(address, int):
            continue
        if not isinstance(name, str) or not name:
            continue
        if not isinstance(kind, str) or kind not in KIND_IDS:
            kind = "unknown"
        rows.append((vector, address, kind, name, vector_symbol_name(name)))
    return sorted(rows, key=lambda row: row[1])


def write_header(rows: list[tuple[int, int, str, str, str]]) -> None:
    lines = [
        "/* Generated M68K CPU runtime metadata. Do not edit directly. */",
        "#ifndef M68K_CPU_RUNTIME_H",
        "#define M68K_CPU_RUNTIME_H",
        "",
        "#include <stddef.h>",
        "#include <stdint.h>",
        "",
        "typedef enum M68kCpuVectorKind {",
        "  M68K_CPU_VECTOR_KIND_UNKNOWN = 0,",
        "  M68K_CPU_VECTOR_KIND_RESET = 1,",
        "  M68K_CPU_VECTOR_KIND_EXCEPTION = 2,",
        "  M68K_CPU_VECTOR_KIND_INTERRUPT = 3,",
        "  M68K_CPU_VECTOR_KIND_TRAP = 4",
        "} M68kCpuVectorKind;",
        "",
        "typedef struct M68kCpuExceptionVectorInfo {",
        "  uint16_t vector;",
        "  uint16_t address;",
        "  uint8_t kind;",
        "  const char *name;",
        "  const char *symbol_name;",
        "} M68kCpuExceptionVectorInfo;",
        "",
        f"#define M68K_CPU_EXCEPTION_VECTOR_COUNT {len(rows)}u",
        "",
        "static const M68kCpuExceptionVectorInfo g_m68k_cpu_exception_vectors[] = {",
    ]
    for vector, address, kind, name, symbol_name in rows:
        lines.append(
            '  { %du, 0x%04Xu, M68K_CPU_VECTOR_KIND_%s, "%s", "%s" },'
            % (vector, address, kind.upper(), c_string(name), c_string(symbol_name))
        )
    lines.extend(
        [
            "};",
            "",
            "static inline const M68kCpuExceptionVectorInfo *m68k_cpu_exception_vector_at(size_t index) {",
            "  if (index >= M68K_CPU_EXCEPTION_VECTOR_COUNT) return NULL;",
            "  return &g_m68k_cpu_exception_vectors[index];",
            "}",
            "",
            "static inline const M68kCpuExceptionVectorInfo *m68k_cpu_find_exception_vector_by_address(uint32_t address) {",
            "  size_t index;",
            "  for (index = 0U; index < M68K_CPU_EXCEPTION_VECTOR_COUNT; ++index) {",
            "    const M68kCpuExceptionVectorInfo *entry = &g_m68k_cpu_exception_vectors[index];",
            "    if (entry->address == address) return entry;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "static inline const M68kCpuExceptionVectorInfo *m68k_cpu_find_exception_vector_by_symbol_name(const char *symbol_name) {",
            "  size_t index;",
            "  if (symbol_name == NULL || symbol_name[0] == '\\0') return NULL;",
            "  for (index = 0U; index < M68K_CPU_EXCEPTION_VECTOR_COUNT; ++index) {",
            "    const M68kCpuExceptionVectorInfo *entry = &g_m68k_cpu_exception_vectors[index];",
            "    const char *left = entry->symbol_name;",
            "    const char *right = symbol_name;",
            "    if (left == NULL) continue;",
            "    while (*left != '\\0' && *right != '\\0' && *left == *right) { ++left; ++right; }",
            "    if (*left == '\\0' && *right == '\\0') return entry;",
            "  }",
            "  return NULL;",
            "}",
            "",
            "static inline int m68k_cpu_exception_vector_address_has_kind(uint32_t address, uint8_t kind) {",
            "  const M68kCpuExceptionVectorInfo *entry = m68k_cpu_find_exception_vector_by_address(address);",
            "  return entry != NULL && entry->kind == kind;",
            "}",
            "",
            "#endif",
            "",
        ]
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="ascii")


def main() -> None:
    payload = json.loads(KB_PATH.read_text(encoding="utf-8"))
    write_header(exception_vector_rows(payload))


if __name__ == "__main__":
    main()
