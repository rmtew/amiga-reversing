from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INTERFACES = ROOT / "ext" / "macos_includes" / "mpw_gm" / "Interfaces"
AINCLUDES = INTERFACES / "AIncludes"
CINCLUDES = INTERFACES / "CIncludes"
OUTPUT_DIR = ROOT / "src" / "generated"
HEADER_PATH = OUTPUT_DIR / "mac_os_runtime.h"
SOURCE_PATH = OUTPUT_DIR / "mac_os_runtime.c"
JSON_PATH = OUTPUT_DIR / "mac_os_runtime.json"

BASELINE_RECORDS = {
    "Point": "MacTypes.a",
    "Rect": "MacTypes.a",
    "EventRecord": "Events.a",
    "HVolumeParam": "Files.a",
    "QDGlobals": "Quickdraw.a",
    "WindowRecord": "MacWindows.a",
    "DCtlEntry": "Devices.a",
    "SysEnvRec": "OSUtils.a",
}

BASELINE_CALLS = {
    "_GetResource": ("Resources", "Resources.a", "Resources.h", "GetResource"),
    "_WaitNextEvent": ("Events", "Events.a", "Events.h", "WaitNextEvent"),
    "_UnloadSeg": ("SegmentLoader", "SegLoad.a", "SegLoad.h", "UnloadSeg"),
    "_PBHGetVInfoSync": ("FileManager", "Files.a", "Files.h", "PBHGetVInfoSync"),
    "_NumToString": ("NumberFormatting", "NumberFormatting.a", "NumberFormatting.h", "NumToString"),
}


def c_string(text: str | None) -> str:
    if text is None:
        return "NULL"
    ascii_text = "".join(char if 32 <= ord(char) < 127 else "?" for char in text)
    return '"' + ascii_text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def enum_token(text: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").upper()
    if not token:
        token = "VALUE"
    if token[0].isdigit():
        token = "_" + token
    return token


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_mac(path: Path) -> list[str]:
    return path.read_text(encoding="mac_roman", errors="replace").splitlines()


def as_int(value: object) -> int:
    assert isinstance(value, int)
    return value


def parse_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    record_sizes: dict[str, int] = {}
    for record_name, filename in BASELINE_RECORDS.items():
        path = AINCLUDES / filename
        lines = read_mac(path)
        record = parse_record(lines, record_name, rel(path), record_sizes)
        records.append(record)
        record_sizes[record_name] = as_int(record["size"])
    return records


def parse_record(
    lines: list[str],
    record_name: str,
    source_path: str,
    record_sizes: dict[str, int] | None = None,
) -> dict[str, object]:
    start_index = None
    for index, line in enumerate(lines):
        if re.match(rf"^\s*{re.escape(record_name)}\s+RECORD\b", line, re.IGNORECASE):
            start_index = index
            break
    if start_index is None:
        raise ValueError(f"record {record_name} not found")

    raw_fields: list[dict[str, object]] = []
    record_size = None
    end_line = None
    for index in range(start_index + 1, len(lines)):
        line = lines[index]
        if re.search(r"\bENDR\b", line, re.IGNORECASE):
            end_line = index + 1
            break
        size_match = re.search(r"\bsizeof\s+EQU\s+\*\s+;\s*size:\s+\$[0-9A-Fa-f]+\s+\((\d+)\)", line)
        if size_match:
            record_size = int(size_match.group(1))
            continue
        field_match = re.match(
            r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+ds(?:\.([bwl]))?\s+([A-Za-z_][A-Za-z0-9_]*|\d+)"
            r".*?offset:\s+\$[0-9A-Fa-f]+\s+\((\d+)\)",
            line,
            re.IGNORECASE,
        )
        if field_match:
            raw_fields.append(
                {
                    "name": field_match.group(1),
                    "record_name": record_name,
                    "storage": "ds" + (("." + field_match.group(2).lower()) if field_match.group(2) else ""),
                    "type": field_match.group(3),
                    "offset": int(field_match.group(4)),
                    "line": index + 1,
                    "count_or_type": field_match.group(3),
                }
            )
    if record_size is None or end_line is None:
        raise ValueError(f"record {record_name} missing size/end")

    fields: list[dict[str, object]] = []
    offsets = sorted({as_int(field["offset"]) for field in raw_fields})
    for field in raw_fields:
        offset = as_int(field["offset"])
        next_offsets = [candidate for candidate in offsets if candidate > offset]
        fallback_size = (next_offsets[0] if next_offsets else record_size) - offset
        field_size = field_declared_size(field, record_sizes or {}, fallback_size)
        fields.append({**field, "size": field_size, "source": source_path})

    return {
        "name": record_name,
        "size": record_size,
        "source": source_path,
        "line": start_index + 1,
        "line_end": end_line,
        "fields": fields,
    }


def field_declared_size(field: dict[str, object], record_sizes: dict[str, int], fallback_size: int) -> int:
    storage = str(field["storage"]).lower()
    count_or_type = str(field["count_or_type"])
    if storage in {"ds.b", "ds.w", "ds.l"} and count_or_type.isdigit():
        scale = {"ds.b": 1, "ds.w": 2, "ds.l": 4}[storage]
        return scale * int(count_or_type)
    if storage == "ds" and count_or_type in record_sizes:
        return record_sizes[count_or_type]
    return fallback_size


def parse_calls() -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []
    for asm_name, (family, asm_file, c_file, c_name) in BASELINE_CALLS.items():
        asm_path = AINCLUDES / asm_file
        c_path = CINCLUDES / c_file
        asm_lines = read_mac(asm_path)
        c_lines = read_mac(c_path)
        call = parse_call_asm(asm_lines, asm_name, family, rel(asm_path))
        call["prototype"] = parse_c_prototype(c_lines, c_name)
        call["prototype_source"] = rel(c_path)
        call["prototype_line"] = find_c_name_line(c_lines, c_name)
        calls.append(call)
    return calls


def parse_call_asm(lines: list[str], asm_name: str, family: str, source_path: str) -> dict[str, object]:
    for index, line in enumerate(lines):
        opword_match = re.search(rf"\b{re.escape(asm_name)}:\s*OPWORD\s+\$([0-9A-Fa-f]+)", line)
        if opword_match:
            window = lines[max(0, index - 8) : index + 1]
            return {
                "name": asm_name,
                "family": family,
                "kind": "opword",
                "opword": int(opword_match.group(1), 16),
                "package_word": 0,
                "source": source_path,
                "line": index + 1,
                "parameter_register": _parameter_register(window),
                "result_register": _result_register(window),
            }
    for index, line in enumerate(lines):
        if re.search(rf"\b{re.escape(asm_name)}\b", line):
            for probe in range(index + 1, min(index + 8, len(lines))):
                package_match = re.search(r"\bdc\.w\s+\$([0-9A-Fa-f]+)", lines[probe], re.IGNORECASE)
                if package_match:
                    return {
                        "name": asm_name,
                        "family": family,
                        "kind": "package_macro",
                        "opword": 0,
                        "package_word": int(package_match.group(1), 16),
                        "source": source_path,
                        "line": index + 1,
                        "parameter_register": None,
                        "result_register": None,
                    }
    raise ValueError(f"call {asm_name} not found")


def _parameter_register(lines: list[str]) -> str | None:
    text = "\n".join(lines)
    match = re.search(r";\s*\w+\s*=>\s*([AD][0-7])", text)
    return match.group(1) if match else None


def _result_register(lines: list[str]) -> str | None:
    text = "\n".join(lines)
    match = re.search(r";\s*\w+\s*<=\s*([AD][0-7])", text)
    return match.group(1) if match else None


def parse_c_prototype(lines: list[str], c_name: str) -> str | None:
    for start, end in iter_c_prototype_blocks(lines):
        block = " ".join(line.strip() for line in lines[start : end + 1])
        if re.search(rf"\b{re.escape(c_name)}\b", block):
            return re.sub(r"\s+", " ", block).strip()
    return None


def find_c_name_line(lines: list[str], c_name: str) -> int:
    for start, end in iter_c_prototype_blocks(lines):
        for index in range(start, end + 1):
            if re.search(rf"\b{re.escape(c_name)}\b", lines[index]):
                return index + 1
    return 0


def iter_c_prototype_blocks(lines: list[str]) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    index = 0
    while index < len(lines):
        if "EXTERN_API" not in lines[index]:
            index += 1
            continue
        start = index
        while index < len(lines) and ";" not in lines[index]:
            index += 1
        if index < len(lines):
            blocks.append((start, index))
        index += 1
    return blocks


def extract_baseline_metadata() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "mac_os_baseline_runtime",
        "records": parse_records(),
        "calls": parse_calls(),
    }


def render_header(metadata: dict[str, object]) -> str:
    records = metadata["records"]
    calls = metadata["calls"]
    assert isinstance(records, list)
    assert isinstance(calls, list)
    lines = [
        "/* Generated Classic Mac OS runtime metadata from MPW includes. Do not edit directly. */",
        "#ifndef MAC_OS_RUNTIME_H",
        "#define MAC_OS_RUNTIME_H",
        "",
        "#include <stddef.h>",
        "#include <stdint.h>",
        "",
        "typedef enum MacOsCallKind {",
        "  MAC_OS_CALL_KIND_OPWORD = 1,",
        "  MAC_OS_CALL_KIND_PACKAGE_MACRO = 2",
        "} MacOsCallKind;",
        "",
        "typedef struct MacOsRecordInfo {",
        "  const char *name;",
        "  uint16_t size;",
        "  const char *source_path;",
        "  uint32_t line;",
        "  uint32_t line_end;",
        "  uint16_t first_field;",
        "  uint16_t field_count;",
        "} MacOsRecordInfo;",
        "",
        "typedef struct MacOsRecordFieldInfo {",
        "  const char *record_name;",
        "  const char *name;",
        "  const char *type_name;",
        "  const char *storage;",
        "  uint16_t offset;",
        "  uint16_t size;",
        "  const char *source_path;",
        "  uint32_t line;",
        "} MacOsRecordFieldInfo;",
        "",
        "typedef struct MacOsCallInfo {",
        "  const char *name;",
        "  const char *family;",
        "  uint16_t kind;",
        "  uint16_t opword;",
        "  uint16_t package_word;",
        "  const char *source_path;",
        "  uint32_t line;",
        "  const char *prototype;",
        "  const char *prototype_source_path;",
        "  uint32_t prototype_line;",
        "  const char *parameter_register;",
        "  const char *result_register;",
        "} MacOsCallInfo;",
        "",
        f"#define MAC_OS_RECORD_COUNT {len(records)}u",
        f"#define MAC_OS_CALL_COUNT {len(calls)}u",
        "",
        "const MacOsRecordInfo *mac_os_find_record(const char *name);",
        "const MacOsRecordFieldInfo *mac_os_find_record_field(const char *record_name, const char *field_name);",
        "const MacOsCallInfo *mac_os_find_call_by_name(const char *name);",
        "const MacOsCallInfo *mac_os_find_call_by_opword(uint16_t opword);",
        "",
        "#endif",
        "",
    ]
    return "\n".join(lines)


def write_header(metadata: dict[str, object]) -> str:
    text = render_header(metadata)
    HEADER_PATH.write_text(text, encoding="ascii")
    return text


def render_source(metadata: dict[str, object]) -> str:
    records = metadata["records"]
    calls = metadata["calls"]
    assert isinstance(records, list)
    assert isinstance(calls, list)
    fields: list[dict[str, object]] = []
    for record in records:
        record_fields = record["fields"]
        assert isinstance(record_fields, list)
        fields.extend(record_fields)
    first_field = 0
    record_rows: list[str] = []
    for record in records:
        record_fields = record["fields"]
        assert isinstance(record_fields, list)
        record_rows.append(
            f"  {{ {c_string(str(record['name']))}, {int(record['size'])}u, "
            f"{c_string(str(record['source']))}, {int(record['line'])}u, "
            f"{int(record['line_end'])}u, {first_field}u, {len(record_fields)}u }},"
        )
        first_field += len(record_fields)

    field_rows = [
        f"  {{ {c_string(str(field['record_name']))}, {c_string(str(field['name']))}, "
        f"{c_string(str(field['type']))}, {c_string(str(field['storage']))}, "
        f"{as_int(field['offset'])}u, {as_int(field['size'])}u, {c_string(str(field['source']))}, "
        f"{as_int(field['line'])}u }},"
        for field in fields
    ]
    call_rows = [
        f"  {{ {c_string(str(call['name']))}, {c_string(str(call['family']))}, "
        f"{'MAC_OS_CALL_KIND_PACKAGE_MACRO' if call['kind'] == 'package_macro' else 'MAC_OS_CALL_KIND_OPWORD'}, "
        f"{int(call['opword'])}u, {int(call['package_word'])}u, {c_string(str(call['source']))}, "
        f"{int(call['line'])}u, "
        f"{c_string(call.get('prototype') if isinstance(call.get('prototype'), str) else None)}, "
        f"{c_string(str(call['prototype_source']))}, {int(call['prototype_line'])}u, "
        f"{c_string(call.get('parameter_register') if isinstance(call.get('parameter_register'), str) else None)}, "
        f"{c_string(call.get('result_register') if isinstance(call.get('result_register'), str) else None)} }},"
        for call in calls
    ]
    lines = [
        "/* Generated Classic Mac OS runtime metadata from MPW includes. Do not edit directly. */",
        '#include "generated/mac_os_runtime.h"',
        "",
        "#include <string.h>",
        "",
        "static const MacOsRecordInfo g_mac_os_records[] = {",
        *record_rows,
        "};",
        "",
        "static const MacOsRecordFieldInfo g_mac_os_record_fields[] = {",
        *field_rows,
        "};",
        "",
        "static const MacOsCallInfo g_mac_os_calls[] = {",
        *call_rows,
        "};",
        "",
        "const MacOsRecordInfo *mac_os_find_record(const char *name) {",
        "  size_t index;",
        "  if (name == NULL) return NULL;",
        "  for (index = 0U; index < MAC_OS_RECORD_COUNT; ++index) {",
        "    if (strcmp(g_mac_os_records[index].name, name) == 0) return &g_mac_os_records[index];",
        "  }",
        "  return NULL;",
        "}",
        "",
        "const MacOsRecordFieldInfo *mac_os_find_record_field(const char *record_name, const char *field_name) {",
        "  size_t index;",
        "  if (record_name == NULL || field_name == NULL) return NULL;",
        "  for (index = 0U; index < sizeof(g_mac_os_record_fields) / sizeof(g_mac_os_record_fields[0]); ++index) {",
        "    const MacOsRecordFieldInfo *field = &g_mac_os_record_fields[index];",
        "    if (strcmp(field->record_name, record_name) == 0 && strcmp(field->name, field_name) == 0) return field;",
        "  }",
        "  return NULL;",
        "}",
        "",
        "const MacOsCallInfo *mac_os_find_call_by_name(const char *name) {",
        "  size_t index;",
        "  if (name == NULL) return NULL;",
        "  for (index = 0U; index < MAC_OS_CALL_COUNT; ++index) {",
        "    if (strcmp(g_mac_os_calls[index].name, name) == 0) return &g_mac_os_calls[index];",
        "  }",
        "  return NULL;",
        "}",
        "",
        "const MacOsCallInfo *mac_os_find_call_by_opword(uint16_t opword) {",
        "  size_t index;",
        "  for (index = 0U; index < MAC_OS_CALL_COUNT; ++index) {",
        "    if (g_mac_os_calls[index].kind == MAC_OS_CALL_KIND_OPWORD && g_mac_os_calls[index].opword == opword) return &g_mac_os_calls[index];",
        "  }",
        "  return NULL;",
        "}",
        "",
    ]
    return "\n".join(lines)


def write_source(metadata: dict[str, object]) -> str:
    text = render_source(metadata)
    SOURCE_PATH.write_text(text, encoding="ascii")
    return text


def render_json(metadata: dict[str, object]) -> str:
    return json.dumps(metadata, indent=2, sort_keys=True) + "\n"


def write_json(metadata: dict[str, object]) -> str:
    text = render_json(metadata)
    JSON_PATH.write_text(text, encoding="ascii")
    return text


def generate() -> dict[str, str]:
    metadata = extract_baseline_metadata()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "header": write_header(metadata),
        "source": write_source(metadata),
        "json": write_json(metadata),
    }


def main() -> None:
    generate()


if __name__ == "__main__":
    main()
