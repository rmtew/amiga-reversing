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

PACKAGE_MACRO_CALLS = {
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
    c_prototypes = parse_c_onewordinline_prototypes()
    calls = parse_opword_calls(c_prototypes)
    calls.extend(parse_trap_constants())
    for asm_name, (family, asm_file, c_file, c_name) in PACKAGE_MACRO_CALLS.items():
        asm_path = AINCLUDES / asm_file
        c_path = CINCLUDES / c_file
        asm_lines = read_mac(asm_path)
        c_lines = read_mac(c_path)
        call = parse_call_asm(asm_lines, asm_name, family, rel(asm_path))
        prototype = parse_c_prototype_metadata(c_lines, c_name)
        call["prototype"] = prototype["prototype"] if prototype is not None else None
        call["prototype_source"] = rel(c_path)
        call["prototype_line"] = find_c_name_line(c_lines, c_name)
        call["c_name"] = prototype.get("c_name") if prototype is not None else None
        call["return_type"] = prototype.get("return_type") if prototype is not None else None
        call["parameters"] = prototype.get("parameters") if prototype is not None else []
        calls.append(call)
    return sorted(calls, key=lambda call: (str(call["kind"]), str(call["source"]), int(call["line"]), str(call["name"])))


def parse_trap_constants() -> list[dict[str, object]]:
    path = CINCLUDES / "Traps.h"
    lines = read_mac(path)
    calls: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^\s*(_[A-Za-z][A-Za-z0-9_]*)\s*=\s*0x([0-9A-Fa-f]{4})\b", line)
        if not match:
            continue
        calls.append(
            {
                "name": match.group(1),
                "family": "Traps",
                "kind": "trap_constant",
                "opword": int(match.group(2), 16),
                "package_word": 0,
                "source": rel(path),
                "line": index + 1,
                "parameter_register": None,
                "result_register": None,
                "prototype": None,
                "prototype_source": "",
                "prototype_line": 0,
                "c_name": None,
                "return_type": None,
                "parameters": [],
            }
        )
    return calls


def parse_opword_calls(c_prototypes: dict[int, dict[str, object]]) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    for asm_path in sorted(AINCLUDES.glob("*.a")):
        asm_lines = read_mac(asm_path)
        family = asm_path.stem
        for index, line in enumerate(asm_lines):
            match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*):\s*OPWORD\s+\$([0-9A-Fa-f]{4})\b", line)
            if not match:
                continue
            asm_name = match.group(1)
            opword = int(match.group(2), 16)
            key = (asm_name, opword)
            if key in seen:
                continue
            seen.add(key)
            window = asm_lines[max(0, index - 8) : index + 1]
            prototype = c_prototypes.get(opword)
            calls.append(
                {
                    "name": asm_name,
                    "family": family,
                    "kind": "opword",
                    "opword": opword,
                    "package_word": 0,
                    "source": rel(asm_path),
                    "line": index + 1,
                    "parameter_register": _parameter_register(window),
                    "result_register": _result_register(window),
                    "prototype": prototype["prototype"] if prototype is not None else None,
                    "prototype_source": prototype["source"] if prototype is not None else "",
                    "prototype_line": prototype["line"] if prototype is not None else 0,
                    "c_name": prototype.get("c_name") if prototype is not None else None,
                    "return_type": prototype.get("return_type") if prototype is not None else None,
                    "parameters": prototype.get("parameters") if prototype is not None else [],
                }
            )
    return calls


def parse_c_onewordinline_prototypes() -> dict[int, dict[str, object]]:
    prototypes: dict[int, dict[str, object]] = {}
    for c_path in sorted(CINCLUDES.glob("*.h")):
        lines = read_mac(c_path)
        for start, end in iter_c_prototype_blocks(lines):
            block = " ".join(line.strip() for line in lines[start : end + 1])
            inline_match = re.search(r"\bONEWORDINLINE\s*\(\s*0x([0-9A-Fa-f]{4})\s*\)", block)
            if not inline_match:
                continue
            opword = int(inline_match.group(1), 16)
            prototypes.setdefault(
                opword,
                {
                    "prototype": re.sub(r"\s+", " ", block).strip(),
                    "source": rel(c_path),
                    "line": start + 1,
                    **parse_c_prototype_signature(block),
                },
            )
    return prototypes


def parse_c_prototype_signature(block: str) -> dict[str, object]:
    normalized = re.sub(r"\s+", " ", block).strip()
    match = re.search(
        r"\bEXTERN_API\s*\(\s*(?P<return_type>.*?)\s*\)\s+"
        r"(?P<c_name>[A-Za-z_][A-Za-z0-9_]*)\s*\((?P<params>.*?)\)\s+ONEWORDINLINE\b",
        normalized,
    )
    if not match:
        return {"c_name": None, "return_type": None, "parameters": []}
    return {
        "c_name": match.group("c_name"),
        "return_type": match.group("return_type").strip(),
        "parameters": parse_c_parameters(match.group("params")),
    }


def parse_c_parameters(params: str) -> list[dict[str, object]]:
    text = params.strip()
    if not text or text == "void":
        return []
    parsed: list[dict[str, object]] = []
    for index, raw_param in enumerate(part.strip() for part in text.split(",")):
        param = parse_c_parameter(raw_param)
        param["index"] = index
        parsed.append(param)
    return parsed


def parse_c_parameter(raw_param: str) -> dict[str, object]:
    param = re.sub(r"\s+", " ", raw_param.replace("*", " * ")).strip()
    name_match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)(?:\s*\[[^\]]*\])?$", param)
    if not name_match:
        return {
            "name": "",
            "type": param,
            "pointer_depth": param.count("*"),
            "direction": "unknown",
        }
    name = name_match.group(1)
    type_text = param[: name_match.start()].strip()
    pointer_depth = type_text.count("*")
    return {
        "name": name,
        "type": re.sub(r"\s+", " ", type_text).strip(),
        "pointer_depth": pointer_depth,
        "direction": c_parameter_direction(type_text, pointer_depth),
    }


def c_parameter_direction(type_text: str, pointer_depth: int) -> str:
    if pointer_depth == 0:
        return "input_value"
    if re.search(r"\bconst\b", type_text):
        return "input_pointer"
    return "output_or_inout_pointer"


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
    metadata = parse_c_prototype_metadata(lines, c_name)
    return metadata["prototype"] if metadata is not None else None


def parse_c_prototype_metadata(lines: list[str], c_name: str) -> dict[str, object] | None:
    for start, end in iter_c_prototype_blocks(lines):
        block = " ".join(line.strip() for line in lines[start : end + 1])
        if re.search(rf"\b{re.escape(c_name)}\b", block):
            normalized = re.sub(r"\s+", " ", block).strip()
            return {
                "prototype": normalized,
                "source": "",
                "line": start + 1,
                **parse_c_prototype_signature(block),
            }
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
        "  MAC_OS_CALL_KIND_PACKAGE_MACRO = 2,",
        "  MAC_OS_CALL_KIND_TRAP_CONSTANT = 3",
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
        "typedef struct MacOsCallParameterInfo {",
        "  const char *call_name;",
        "  uint16_t index;",
        "  const char *name;",
        "  const char *type_name;",
        "  uint16_t pointer_depth;",
        "  const char *direction;",
        "} MacOsCallParameterInfo;",
        "",
        "typedef struct MacOsCallInfo {",
        "  const char *name;",
        "  const char *c_name;",
        "  const char *family;",
        "  uint16_t kind;",
        "  uint16_t opword;",
        "  uint16_t package_word;",
        "  const char *source_path;",
        "  uint32_t line;",
        "  const char *prototype;",
        "  const char *prototype_source_path;",
        "  uint32_t prototype_line;",
        "  const char *return_type;",
        "  uint16_t first_parameter;",
        "  uint16_t parameter_count;",
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
        "const MacOsCallParameterInfo *mac_os_call_parameter(const MacOsCallInfo *call, uint16_t parameter_index);",
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
    call_parameters: list[dict[str, object]] = []
    for call in calls:
        parameters = call.get("parameters")
        if isinstance(parameters, list):
            for parameter in parameters:
                if isinstance(parameter, dict):
                    call_parameters.append({"call_name": call["name"], **parameter})
    call_rows: list[str] = []
    first_parameter = 0
    for call in calls:
        parameters = call.get("parameters")
        parameter_count = len(parameters) if isinstance(parameters, list) else 0
        call_rows.append(
            f"  {{ {c_string(str(call['name']))}, "
            f"{c_string(call.get('c_name') if isinstance(call.get('c_name'), str) else None)}, "
            f"{c_string(str(call['family']))}, "
            f"{mac_os_call_kind_c_name(str(call['kind']))}, "
            f"{int(call['opword'])}u, {int(call['package_word'])}u, {c_string(str(call['source']))}, "
            f"{int(call['line'])}u, "
            f"{c_string(call.get('prototype') if isinstance(call.get('prototype'), str) else None)}, "
            f"{c_string(str(call['prototype_source']))}, {int(call['prototype_line'])}u, "
            f"{c_string(call.get('return_type') if isinstance(call.get('return_type'), str) else None)}, "
            f"{first_parameter}u, {parameter_count}u, "
            f"{c_string(call.get('parameter_register') if isinstance(call.get('parameter_register'), str) else None)}, "
            f"{c_string(call.get('result_register') if isinstance(call.get('result_register'), str) else None)} }},"
        )
        first_parameter += parameter_count
    call_parameter_rows = [
        f"  {{ {c_string(str(parameter['call_name']))}, {int(parameter['index'])}u, "
        f"{c_string(str(parameter['name']))}, {c_string(str(parameter['type']))}, "
        f"{int(parameter['pointer_depth'])}u, {c_string(str(parameter['direction']))} }},"
        for parameter in call_parameters
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
        "static const MacOsCallParameterInfo g_mac_os_call_parameters[] = {",
        *call_parameter_rows,
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
        "    if ((g_mac_os_calls[index].kind == MAC_OS_CALL_KIND_OPWORD ||",
        "         g_mac_os_calls[index].kind == MAC_OS_CALL_KIND_TRAP_CONSTANT) &&",
        "        g_mac_os_calls[index].opword == opword) return &g_mac_os_calls[index];",
        "  }",
        "  return NULL;",
        "}",
        "",
        "const MacOsCallParameterInfo *mac_os_call_parameter(const MacOsCallInfo *call, uint16_t parameter_index) {",
        "  if (call == NULL || parameter_index >= call->parameter_count) return NULL;",
        "  return &g_mac_os_call_parameters[call->first_parameter + parameter_index];",
        "}",
        "",
    ]
    return "\n".join(lines)


def mac_os_call_kind_c_name(kind: str) -> str:
    if kind == "package_macro":
        return "MAC_OS_CALL_KIND_PACKAGE_MACRO"
    if kind == "trap_constant":
        return "MAC_OS_CALL_KIND_TRAP_CONSTANT"
    return "MAC_OS_CALL_KIND_OPWORD"


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
