from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "knowledge"
DEFAULT_OUTPUT_DIR = ROOT / "src" / "generated"


def _load_json(name: str) -> dict[str, Any]:
    with open(KNOWLEDGE_DIR / name, encoding="utf-8") as handle:
        return json.load(handle)


def _define_name(*parts: str) -> str:
    tokens: list[str] = []
    for part in parts:
        token = re.sub(r"[^A-Za-z0-9]+", "_", part).strip("_").upper()
        if token:
            tokens.append(token)
    return "_".join(tokens)


def _type_name(*parts: str) -> str:
    words: list[str] = []
    for part in parts:
        for token in re.split(r"[^A-Za-z0-9]+", part):
            if token:
                words.append(token[:1].upper() + token[1:])
    return "".join(words)


def _enum_value_or_zero(payload: dict[str, Any], key: str) -> int:
    for enum_payload in payload.get("enums", {}).values():
        if key in enum_payload:
            return int(enum_payload[key])
    return 0


def _wire_id_for_record(payload: dict[str, Any], record: dict[str, Any]) -> int:
    id_name = record.get("id_name")
    if not id_name:
        return 0
    return _enum_value_or_zero(payload, str(id_name))


def _write_constants(lines: list[str], prefix: str, payload: dict[str, Any]) -> None:
    for enum_name, enum_payload in payload.get("enums", {}).items():
        lines.append(f"/* {enum_name} */")
        for key, value in enum_payload.items():
            lines.append(f"#define {_define_name(prefix, enum_name, key)} {int(value)}u")
        lines.append("")
    for constraint_name, constraint_value in payload.get("constraints", {}).items():
        if isinstance(constraint_value, bool):
            lines.append(
                f"#define {_define_name(prefix, 'constraints', constraint_name)} {'1u' if constraint_value else '0u'}"
            )
        elif isinstance(constraint_value, int):
            lines.append(f"#define {_define_name(prefix, 'constraints', constraint_name)} {constraint_value}u")
    if payload.get("constraints"):
        lines.append("")
    for bitfield_name, bitfield_payload in payload.get("bitfields", {}).items():
        lines.append(f"/* {bitfield_name} */")
        value_mask = bitfield_payload.get("value_mask")
        if isinstance(value_mask, int):
            lines.append(f"#define {_define_name(prefix, bitfield_name, 'value_mask')} {value_mask}u")
        for field_name, field_payload in bitfield_payload.get("fields", {}).items():
            bit = field_payload.get("bit")
            bits = field_payload.get("bits")
            if isinstance(bit, int):
                lines.append(f"#define {_define_name(prefix, bitfield_name, field_name, 'bit')} {bit}u")
            elif isinstance(bits, list) and len(bits) == 2:
                lines.append(f"#define {_define_name(prefix, bitfield_name, field_name, 'bit_lo')} {int(bits[0])}u")
                lines.append(f"#define {_define_name(prefix, bitfield_name, field_name, 'bit_hi')} {int(bits[1])}u")
        lines.append("")


def _fixed_field_size(payload: dict[str, Any], field: dict[str, Any]) -> int | None:
    primitive_name = field.get("primitive")
    if isinstance(primitive_name, str):
        primitive = payload.get("primitives", {}).get(primitive_name, {})
        bytes_value = primitive.get("bytes")
        if isinstance(bytes_value, int):
            return int(bytes_value)
        return None
    if field.get("type") == "byte_blob":
        length_expr = field.get("length_expr")
        if isinstance(length_expr, str) and length_expr.isdigit():
            return int(length_expr)
    return None


def _write_field_offset_constants(lines: list[str], prefix: str, payload: dict[str, Any]) -> None:
    for record_name, record_payload in payload.get("record_types", {}).items():
        fields = record_payload.get("fields")
        if not isinstance(fields, list):
            continue
        offset = 0
        record_lines: list[str] = []
        for field in fields:
            if not isinstance(field, dict):
                break
            field_name = field.get("name")
            if not isinstance(field_name, str):
                break
            field_size = _fixed_field_size(payload, field)
            if field_size is None:
                break
            record_lines.append(
                f"#define {_define_name(prefix, record_name, 'field', field_name, 'offset')} {offset}u"
            )
            record_lines.append(
                f"#define {_define_name(prefix, record_name, 'field', field_name, 'size')} {field_size}u"
            )
            offset += field_size
        if record_lines:
            lines.append(f"/* {record_name} fixed fields */")
            lines.extend(record_lines)
            lines.append("")


def _emit_enum(lines: list[str], type_name: str, prefix: str, names: list[str]) -> None:
    lines.append(f"typedef enum {type_name} {{")
    for index, name in enumerate(names):
        lines.append(f"    {_define_name(prefix, name)} = {index},")
    lines.append(f"}} {type_name};")
    lines.append("")


def _names_from_values(values: list[str], empty: str) -> list[str]:
    return [empty] + sorted({_define_name(value) for value in values if value})


def _record_kind_names(payload: dict[str, Any]) -> list[str]:
    return ["NONE"] + list(payload.get("record_types", {}).keys())


def _record_kind_lookup(payload: dict[str, Any], prefix: str) -> dict[str, str]:
    return {
        name: _define_name(prefix, "META", "RECORD_KIND", name)
        for name in payload.get("record_types", {})
    }


def _role_names(payload: dict[str, Any]) -> list[str]:
    return _names_from_values([record.get("role", "") for record in payload.get("record_types", {}).values()], "UNKNOWN")


def _section_kind_names(payload: dict[str, Any]) -> list[str]:
    return _names_from_values([record.get("section_kind", "") for record in payload.get("record_types", {}).values()], "NONE")


def _relocation_mode_names(payload: dict[str, Any]) -> list[str]:
    return _names_from_values([data.get("mode", "") for data in payload.get("relocation_kinds", {}).values()], "NONE")


def _container_names(payload: dict[str, Any]) -> list[str]:
    return ["UNKNOWN"] + sorted(_define_name(name) for name in payload.get("containers", {}))


def _group_names(payload: dict[str, Any]) -> list[str]:
    return ["NONE"] + sorted(_define_name(name) for name in payload.get("groups", {}))


def _ext_variant_names(payload: dict[str, Any]) -> list[str]:
    variants = payload.get("record_types", {}).get("HUNK_EXT", {}).get("variant_selector", {}).get("variants", {})
    return _names_from_values(list(variants.values()), "NONE")


def _container_item_kind_names() -> list[str]:
    return ["NONE", "RECORD", "GROUP"]


def _record_rows(payload: dict[str, Any], prefix: str) -> list[str]:
    rows: list[str] = []
    kind_lookup = _record_kind_lookup(payload, prefix)
    for name, record in payload.get("record_types", {}).items():
        role_name = _define_name(record.get("role", "UNKNOWN")) if record.get("role") else "UNKNOWN"
        section_name = _define_name(record.get("section_kind", "NONE")) if record.get("section_kind") else "NONE"
        rows.append(
            "    { %s, %su, %s, %s },"
            % (
                kind_lookup[name],
                _wire_id_for_record(payload, record),
                _define_name(prefix, "META", "RECORD_ROLE", role_name),
                _define_name(prefix, "META", "SECTION_KIND", section_name),
            )
        )
    return rows


def _interpretation_rows(payload: dict[str, Any], prefix: str) -> list[str]:
    rows: list[str] = []
    kind_lookup = _record_kind_lookup(payload, prefix)
    for rule in payload.get("interpretation_rules", []):
        when = rule.get("when", {})
        record_type = when.get("record_type")
        interpret_as = rule.get("interpret_as")
        if not record_type or not interpret_as:
            continue
        rows.append(
            "    { %s, %s, %s },"
            % (
                _define_name(prefix, "META", "CONTAINER_KIND", _define_name(when.get("container", "UNKNOWN"))),
                kind_lookup[record_type],
                kind_lookup[interpret_as],
            )
        )
    return rows


def _relocation_rows(payload: dict[str, Any], prefix: str) -> list[str]:
    rows: list[str] = []
    kind_lookup = _record_kind_lookup(payload, prefix)
    for record_type, info in payload.get("relocation_kinds", {}).items():
        mode_name = _define_name(info.get("mode", "NONE")) if info.get("mode") else "NONE"
        target_record_type = str(info.get("record_type", record_type))
        rows.append(
            "    { %s, %su, %s },"
            % (
                kind_lookup.get(target_record_type, _define_name(prefix, "META", "RECORD_KIND", "NONE")),
                int(info.get("width_bytes", 0)),
                _define_name(prefix, "META", "RELOCATION_MODE", mode_name),
            )
        )
    return rows


def _container_rows(payload: dict[str, Any], prefix: str) -> list[str]:
    rows: list[str] = []
    kind_lookup = _record_kind_lookup(payload, prefix)
    for container_name, container in payload.get("containers", {}).items():
        container_id = _define_name(prefix, "META", "CONTAINER_KIND", _define_name(container_name))
        for item in container.get("top_level_sequence", []):
            if isinstance(item, str):
                item_name = item
                optional = 0
            else:
                item_name = item.get("type", "")
                optional = 1 if item.get("optional") else 0
            if item_name in payload.get("record_types", {}):
                item_kind = _define_name(prefix, "META", "CONTAINER_ITEM_KIND", "RECORD")
                item_id = kind_lookup[item_name]
            else:
                item_kind = _define_name(prefix, "META", "CONTAINER_ITEM_KIND", "GROUP")
                item_id = _define_name(prefix, "META", "GROUP_KIND", _define_name(item_name))
            rows.append("    { %s, %s, %s, %su }," % (container_id, item_kind, item_id, optional))
    return rows


def _ext_variant_rows(payload: dict[str, Any], prefix: str) -> list[str]:
    rows: list[str] = []
    variants = payload.get("record_types", {}).get("HUNK_EXT", {}).get("variant_selector", {}).get("variants", {})
    for ext_type_name, variant_name in variants.items():
        rows.append(
            "    { %su, %s },"
            % (
                _enum_value_or_zero(payload, ext_type_name),
                _define_name(prefix, "META", "EXT_VARIANT", _define_name(variant_name)),
            )
        )
    return rows


def _ext_reference_rows(payload: dict[str, Any], prefix: str) -> list[str]:
    rows: list[str] = []
    for ext_type_name, info in payload.get("ext_reference_kinds", {}).items():
        mode_name = _define_name(info.get("mode", "NONE")) if info.get("mode") else "NONE"
        rows.append(
            "    { %su, %su, %s },"
            % (
                _enum_value_or_zero(payload, ext_type_name),
                int(info.get("width_bytes", 0)),
                _define_name(prefix, "META", "RELOCATION_MODE", mode_name),
            )
        )
    return rows


def _write_table(lines: list[str], decl: str, rows: list[str], count_name: str, array_name: str) -> None:
    lines.append(f"const {decl}[] = {{")
    if rows:
        lines.extend(rows)
    else:
        lines.append("    { 0 },")
    lines.append("};")
    if rows:
        lines.append(f"const size_t {count_name} = sizeof({array_name}) / sizeof({array_name}[0]);")
    else:
        lines.append(f"const size_t {count_name} = 0u;")
    lines.append("")


def _container_magic_wire_ids(payload: dict[str, Any]) -> list[int]:
    values: list[int] = []
    for container in payload.get("containers", {}).values():
        magic_type = container.get("magic_type")
        if isinstance(magic_type, str):
            wire_id = _enum_value_or_zero(payload, magic_type)
            if wire_id != 0:
                values.append(wire_id)
    return sorted(set(values))


def _write_lookup_decls(lines_h: list[str], prefix: str, record_info_type: str, interpretation_type: str,
    relocation_type: str, ext_variant_info_type: str, ext_reference_type: str, record_kind_type: str,
    container_type: str, section_type: str, relocation_mode_type: str) -> None:
    lines_h.extend(
        [
            f"const {record_info_type} *{_define_name(prefix, 'record_info_by_wire_id').lower()}(unsigned wire_id);",
            f"const {record_info_type} *{_define_name(prefix, 'record_info_by_record_kind').lower()}({record_kind_type} record_kind);",
            f"const {record_info_type} *{_define_name(prefix, 'record_info_for_section_kind').lower()}({section_type} section_kind);",
            f"const {interpretation_type} *{_define_name(prefix, 'interpretation_rule_lookup').lower()}({container_type} container_kind, {record_kind_type} record_kind);",
            f"const {relocation_type} *{_define_name(prefix, 'relocation_kind_lookup').lower()}({record_kind_type} record_kind);",
            f"const {ext_variant_info_type} *{_define_name(prefix, 'ext_variant_lookup').lower()}(unsigned ext_type);",
            f"const {ext_reference_type} *{_define_name(prefix, 'ext_reference_kind_lookup').lower()}(unsigned ext_type);",
            f"const {ext_reference_type} *{_define_name(prefix, 'ext_reference_kind_lookup_by_mode_width').lower()}({relocation_mode_type} mode, unsigned width_bytes);",
            "",
        ]
    )


def _write_lookup_defs(lines_c: list[str], prefix: str, payload: dict[str, Any], record_info_type: str,
    interpretation_type: str, relocation_type: str, ext_variant_info_type: str, ext_reference_type: str,
    record_kind_type: str, container_type: str, section_type: str, relocation_mode_type: str) -> None:
    record_infos = list(payload.get("record_types", {}).items())
    record_lookup_name = _define_name(prefix, "record_info_by_wire_id").lower()
    lines_c.append(f"const {record_info_type} *{record_lookup_name}(unsigned wire_id) {{")
    lines_c.append("    (void)wire_id;")
    lines_c.append("    switch (wire_id) {")
    for index, (_name, record) in enumerate(record_infos):
        wire_id = _wire_id_for_record(payload, record)
        if wire_id != 0:
            lines_c.append(f"    case {wire_id}u: return &{_define_name(prefix, 'RECORD_INFOS')}[{index}];")
    lines_c.append("    default: return NULL;")
    lines_c.append("    }")
    lines_c.append("}")
    lines_c.append("")

    section_lookup_name = _define_name(prefix, "record_info_for_section_kind").lower()
    lines_c.append(f"const {record_info_type} *{section_lookup_name}({section_type} section_kind) {{")
    lines_c.append("    (void)section_kind;")
    lines_c.append("    switch (section_kind) {")
    for index, (_name, record) in enumerate(record_infos):
        role = str(record.get("role", ""))
        section_kind = str(record.get("section_kind", ""))
        if role == "section_start" and section_kind:
            lines_c.append(
                f"    case {_define_name(prefix, 'META', 'SECTION_KIND', _define_name(section_kind))}: return &{_define_name(prefix, 'RECORD_INFOS')}[{index}];"
            )
    lines_c.append("    default: return NULL;")
    lines_c.append("    }")
    lines_c.append("}")
    lines_c.append("")

    record_kind_lookup_name = _define_name(prefix, "record_info_by_record_kind").lower()
    lines_c.append(f"const {record_info_type} *{record_kind_lookup_name}({record_kind_type} record_kind) {{")
    lines_c.append("    (void)record_kind;")
    lines_c.append("    switch (record_kind) {")
    for index, (name, _record) in enumerate(record_infos):
        lines_c.append(
            f"    case {_define_name(prefix, 'META', 'RECORD_KIND', name)}: return &{_define_name(prefix, 'RECORD_INFOS')}[{index}];"
        )
    lines_c.append("    default: return NULL;")
    lines_c.append("    }")
    lines_c.append("}")
    lines_c.append("")

    interp_name = _define_name(prefix, "interpretation_rule_lookup").lower()
    lines_c.append(
        f"const {interpretation_type} *{interp_name}({container_type} container_kind, {record_kind_type} record_kind) {{"
    )
    lines_c.append("    (void)container_kind;")
    lines_c.append("    (void)record_kind;")
    lines_c.append("    switch (container_kind) {")
    rules = payload.get("interpretation_rules", [])
    by_container: dict[str, list[dict[str, Any]]] = {}
    for rule in rules:
        when = rule.get("when", {})
        container_name = str(when.get("container", "UNKNOWN"))
        by_container.setdefault(container_name, []).append(rule)
    for container_name, container_rules in by_container.items():
        lines_c.append(f"    case {_define_name(prefix, 'META', 'CONTAINER_KIND', _define_name(container_name))}:")
        lines_c.append("        switch (record_kind) {")
        for index, rule in enumerate(rules):
            if rule not in container_rules:
                continue
            record_type = rule.get("when", {}).get("record_type")
            if isinstance(record_type, str):
                lines_c.append(
                    f"        case {_define_name(prefix, 'META', 'RECORD_KIND', record_type)}: return &{_define_name(prefix, 'INTERPRETATION_RULES')}[{index}];"
                )
        lines_c.append("        default: return NULL;")
        lines_c.append("        }")
    lines_c.append("    default: return NULL;")
    lines_c.append("    }")
    lines_c.append("}")
    lines_c.append("")

    reloc_name = _define_name(prefix, "relocation_kind_lookup").lower()
    reloc_items = list(payload.get("relocation_kinds", {}).items())
    lines_c.append(f"const {relocation_type} *{reloc_name}({record_kind_type} record_kind) {{")
    lines_c.append("    (void)record_kind;")
    lines_c.append("    switch (record_kind) {")
    for index, (_record_type, info) in enumerate(reloc_items):
        target_record_type = str(info.get("record_type", _record_type))
        lines_c.append(
            f"    case {_define_name(prefix, 'META', 'RECORD_KIND', target_record_type)}: return &{_define_name(prefix, 'RELOCATION_KINDS')}[{index}];"
        )
    lines_c.append("    default: return NULL;")
    lines_c.append("    }")
    lines_c.append("}")
    lines_c.append("")

    ext_variant_name = _define_name(prefix, "ext_variant_lookup").lower()
    variant_items = list(payload.get("record_types", {}).get("HUNK_EXT", {}).get("variant_selector", {}).get("variants", {}).items())
    lines_c.append(f"const {ext_variant_info_type} *{ext_variant_name}(unsigned ext_type) {{")
    lines_c.append("    (void)ext_type;")
    lines_c.append("    switch (ext_type) {")
    for index, (ext_type_name, _variant_name) in enumerate(variant_items):
        ext_value = _enum_value_or_zero(payload, ext_type_name)
        lines_c.append(f"    case {ext_value}u: return &{_define_name(prefix, 'EXT_VARIANTS')}[{index}];")
    lines_c.append("    default: return NULL;")
    lines_c.append("    }")
    lines_c.append("}")
    lines_c.append("")

    ext_ref_name = _define_name(prefix, "ext_reference_kind_lookup").lower()
    ext_ref_items = list(payload.get("ext_reference_kinds", {}).items())
    lines_c.append(f"const {ext_reference_type} *{ext_ref_name}(unsigned ext_type) {{")
    lines_c.append("    (void)ext_type;")
    lines_c.append("    switch (ext_type) {")
    for index, (ext_type_name, _info) in enumerate(ext_ref_items):
        ext_value = _enum_value_or_zero(payload, ext_type_name)
        lines_c.append(f"    case {ext_value}u: return &{_define_name(prefix, 'EXT_REFERENCE_KINDS')}[{index}];")
    lines_c.append("    default: return NULL;")
    lines_c.append("    }")
    lines_c.append("}")
    lines_c.append("")

    ext_ref_mode_width_name = _define_name(prefix, "ext_reference_kind_lookup_by_mode_width").lower()
    lines_c.append(f"const {ext_reference_type} *{ext_ref_mode_width_name}({relocation_mode_type} mode, unsigned width_bytes) {{")
    lines_c.append("    (void)mode;")
    lines_c.append("    (void)width_bytes;")
    lines_c.append("    switch (mode) {")
    modes: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, (_ext_type_name, info) in enumerate(ext_ref_items):
        mode_name = str(info.get("mode", "NONE"))
        modes.setdefault(mode_name, []).append((index, info))
    for mode_name, items in modes.items():
        lines_c.append(f"    case {_define_name(prefix, 'META', 'RELOCATION_MODE', _define_name(mode_name))}:")
        lines_c.append("        switch (width_bytes) {")
        for index, info in items:
            lines_c.append(f"        case {int(info.get('width_bytes', 0))}u: return &{_define_name(prefix, 'EXT_REFERENCE_KINDS')}[{index}];")
        lines_c.append("        default: return NULL;")
        lines_c.append("        }")
    lines_c.append("    default: return NULL;")
    lines_c.append("    }")
    lines_c.append("}")
    lines_c.append("")


def _style_runtime_lines(lines: list[str], line_length: int = 140) -> list[str]:
    def pack_items(prefix: str, items: list[str], suffix: str, continuation: str) -> list[str]:
        packed: list[str] = []
        current = prefix
        for index, item in enumerate(items):
            token = item + (", " if index != len(items) - 1 else "")
            if len(current) + len(token) > line_length and current != prefix:
                packed.append(current.rstrip())
                current = continuation + token
            else:
                current += token
        if len(current) + len(suffix) > line_length and current.strip():
            packed.append(current.rstrip())
            current = continuation + suffix.lstrip()
        else:
            current += suffix
        packed.append(current.rstrip())
        return packed

    styled: list[str] = []
    for line in lines:
        if len(line) <= line_length:
            styled.append(line.rstrip())
            continue
        if line.startswith("const size_t ") and " = sizeof(" in line:
            head, tail = line.split(" = ", 1)
            styled.append((head + " =").rstrip())
            if len("    " + tail.rstrip()) > line_length and " / " in tail:
                left, right = tail.split(" / ", 1)
                styled.append("    " + left + " /")
                styled.append("        " + right.rstrip())
            else:
                styled.append("    " + tail.rstrip())
            continue
        if line.startswith("const ") and "(" in line and (line.endswith(";") or line.endswith(" {")):
            head, tail = line.split("(", 1)
            suffix = ");" if line.endswith(";") else ") {"
            params = tail[: -len(suffix)]
            styled.extend(pack_items(head + "(", params.split(", "), suffix, "    "))
            continue
        if line.startswith("    { ") and line.endswith(" },"):
            body = line[6:-3]
            items = body.split(", ")
            if len(items) > 1:
                styled.extend(pack_items("    { ", items, " },", "        "))
                continue
        styled.append(line.rstrip())
    return styled


def _write_runtime_files(path_h: Path, path_c: Path, payload: dict[str, Any], *, header_comment: str, source_comment: str) -> None:
    meta = payload["_meta"]
    prefix = _define_name(meta["name"])
    type_prefix = _type_name(meta["name"])
    guard = _define_name(meta["name"], "runtime_h")

    role_type = f"{type_prefix}RecordRole"
    record_kind_type = f"{type_prefix}RecordKind"
    section_type = f"{type_prefix}SectionKind"
    relocation_mode_type = f"{type_prefix}RelocationMode"
    container_type = f"{type_prefix}ContainerKind"
    group_type = f"{type_prefix}GroupKind"
    container_item_kind_type = f"{type_prefix}ContainerItemKind"
    ext_variant_type = f"{type_prefix}ExtVariant"
    ext_reference_type = f"{type_prefix}ExtReferenceKind"
    record_info_type = f"{type_prefix}RecordInfo"
    interpretation_type = f"{type_prefix}InterpretationRule"
    relocation_type = f"{type_prefix}RelocationKind"
    container_item_type = f"{type_prefix}ContainerItem"
    ext_variant_info_type = f"{type_prefix}ExtVariantInfo"
    rk = lambda name: _define_name(prefix, "META", "RECORD_KIND", name)
    rr = lambda name: _define_name(prefix, "META", "RECORD_ROLE", name)
    sk = lambda name: _define_name(prefix, "META", "SECTION_KIND", name)
    rm = lambda name: _define_name(prefix, "META", "RELOCATION_MODE", name)
    ck = lambda name: _define_name(prefix, "META", "CONTAINER_KIND", name)
    gk = lambda name: _define_name(prefix, "META", "GROUP_KIND", name)
    cik = lambda name: _define_name(prefix, "META", "CONTAINER_ITEM_KIND", name)
    ev = lambda name: _define_name(prefix, "META", "EXT_VARIANT", name)

    lines_h = [
        f"/* {header_comment} */",
        f"#ifndef {guard}",
        f"#define {guard}",
        "",
        "#include <stddef.h>",
        "",
    ]
    _write_constants(lines_h, prefix, payload)
    _write_field_offset_constants(lines_h, prefix, payload)
    _emit_enum(lines_h, record_kind_type, _define_name(prefix, "META", "RECORD_KIND"), _record_kind_names(payload))
    _emit_enum(lines_h, role_type, _define_name(prefix, "META", "RECORD_ROLE"), _role_names(payload))
    _emit_enum(lines_h, section_type, _define_name(prefix, "META", "SECTION_KIND"), _section_kind_names(payload))
    _emit_enum(lines_h, relocation_mode_type, _define_name(prefix, "META", "RELOCATION_MODE"), _relocation_mode_names(payload))
    _emit_enum(lines_h, container_type, _define_name(prefix, "META", "CONTAINER_KIND"), _container_names(payload))
    _emit_enum(lines_h, group_type, _define_name(prefix, "META", "GROUP_KIND"), _group_names(payload))
    _emit_enum(lines_h, container_item_kind_type, _define_name(prefix, "META", "CONTAINER_ITEM_KIND"), _container_item_kind_names())
    _emit_enum(lines_h, ext_variant_type, _define_name(prefix, "META", "EXT_VARIANT"), _ext_variant_names(payload))
    lines_h.extend(
        [
            f"typedef struct {record_info_type} {{",
            f"    {record_kind_type} record_kind;",
            "    unsigned wire_id;",
            f"    {role_type} role;",
            f"    {section_type} section_kind;",
            f"}} {record_info_type};",
            "",
            f"typedef struct {interpretation_type} {{",
            f"    {container_type} container_kind;",
            f"    {record_kind_type} record_kind;",
            f"    {record_kind_type} interpreted_kind;",
            f"}} {interpretation_type};",
            "",
            f"typedef struct {relocation_type} {{",
            f"    {record_kind_type} record_kind;",
            "    unsigned width_bytes;",
            f"    {relocation_mode_type} mode;",
            f"}} {relocation_type};",
            "",
            f"typedef struct {container_item_type} {{",
            f"    {container_type} container_kind;",
            f"    {container_item_kind_type} item_kind;",
            "    unsigned item_id;",
            "    unsigned optional;",
            f"}} {container_item_type};",
            "",
            f"typedef struct {ext_variant_info_type} {{",
            "    unsigned ext_type;",
            f"    {ext_variant_type} variant;",
            f"}} {ext_variant_info_type};",
            "",
            f"typedef struct {ext_reference_type} {{",
            "    unsigned ext_type;",
            "    unsigned width_bytes;",
            f"    {relocation_mode_type} mode;",
            f"}} {ext_reference_type};",
            "",
            f"extern const {record_info_type} {_define_name(prefix, 'RECORD_INFOS')}[];",
            f"extern const size_t {_define_name(prefix, 'RECORD_INFO_COUNT')};",
            "",
            f"extern const {interpretation_type} {_define_name(prefix, 'INTERPRETATION_RULES')}[];",
            f"extern const size_t {_define_name(prefix, 'INTERPRETATION_RULE_COUNT')};",
            "",
            f"extern const {relocation_type} {_define_name(prefix, 'RELOCATION_KINDS')}[];",
            f"extern const size_t {_define_name(prefix, 'RELOCATION_KIND_COUNT')};",
            "",
            f"extern const {container_item_type} {_define_name(prefix, 'CONTAINER_ITEMS')}[];",
            f"extern const size_t {_define_name(prefix, 'CONTAINER_ITEM_COUNT')};",
            "",
            f"extern const {ext_variant_info_type} {_define_name(prefix, 'EXT_VARIANTS')}[];",
            f"extern const size_t {_define_name(prefix, 'EXT_VARIANT_COUNT')};",
            "",
            f"extern const {ext_reference_type} {_define_name(prefix, 'EXT_REFERENCE_KINDS')}[];",
            f"extern const size_t {_define_name(prefix, 'EXT_REFERENCE_KIND_COUNT')};",
            "",
        ]
    )
    _write_lookup_decls(
        lines_h,
        prefix,
        record_info_type,
        interpretation_type,
        relocation_type,
        ext_variant_info_type,
        ext_reference_type,
        record_kind_type,
        container_type,
        section_type,
        relocation_mode_type,
    )
    lines_h.extend(
        [
            f"#endif /* {guard} */",
            "",
        ]
    )
    path_h.write_text("\n".join(_style_runtime_lines(lines_h)), encoding="utf-8")

    lines_c = [
        f"/* {source_comment} */",
        f'#include "{path_h.name}"',
        "",
    ]
    _write_table(
        lines_c,
        f"{record_info_type} {_define_name(prefix, 'RECORD_INFOS')}",
        _record_rows(payload, prefix),
        _define_name(prefix, "RECORD_INFO_COUNT"),
        _define_name(prefix, "RECORD_INFOS"),
    )
    _write_table(
        lines_c,
        f"{interpretation_type} {_define_name(prefix, 'INTERPRETATION_RULES')}",
        _interpretation_rows(payload, prefix),
        _define_name(prefix, "INTERPRETATION_RULE_COUNT"),
        _define_name(prefix, "INTERPRETATION_RULES"),
    )
    _write_table(
        lines_c,
        f"{relocation_type} {_define_name(prefix, 'RELOCATION_KINDS')}",
        _relocation_rows(payload, prefix),
        _define_name(prefix, "RELOCATION_KIND_COUNT"),
        _define_name(prefix, "RELOCATION_KINDS"),
    )
    _write_table(
        lines_c,
        f"{container_item_type} {_define_name(prefix, 'CONTAINER_ITEMS')}",
        _container_rows(payload, prefix),
        _define_name(prefix, "CONTAINER_ITEM_COUNT"),
        _define_name(prefix, "CONTAINER_ITEMS"),
    )
    _write_table(
        lines_c,
        f"{ext_variant_info_type} {_define_name(prefix, 'EXT_VARIANTS')}",
        _ext_variant_rows(payload, prefix),
        _define_name(prefix, "EXT_VARIANT_COUNT"),
        _define_name(prefix, "EXT_VARIANTS"),
    )
    _write_table(
        lines_c,
        f"{ext_reference_type} {_define_name(prefix, 'EXT_REFERENCE_KINDS')}",
        _ext_reference_rows(payload, prefix),
        _define_name(prefix, "EXT_REFERENCE_KIND_COUNT"),
        _define_name(prefix, "EXT_REFERENCE_KINDS"),
    )
    _write_lookup_defs(
        lines_c,
        prefix,
        payload,
        record_info_type,
        interpretation_type,
        relocation_type,
        ext_variant_info_type,
        ext_reference_type,
        record_kind_type,
        container_type,
        section_type,
        relocation_mode_type,
    )
    path_c.write_text("\n".join(_style_runtime_lines(lines_c)), encoding="utf-8")


def _write_runtime_json(path_json: Path, payload: dict[str, Any]) -> None:
    output = {
        "meta": payload.get("_meta", {}),
        "container_magic_wire_ids": _container_magic_wire_ids(payload),
        "unsupported_record_types": payload.get("unsupported_record_types", {}),
    }
    path_json.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


PLATFORM_FACT_SECTIONS = (
    "identification",
    "containers",
    "regions",
    "relocations",
    "symbols",
    "bss",
    "loader_model",
    "runtime_model",
    "analysis_model",
    "renderer_expectations",
    "entrypoints",
    "facts",
    "unknowns",
    "conflicts",
    "deferred",
    "unsupported",
)


def _json_string(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=True)


def _platform_parser_use(item: dict[str, Any]) -> str:
    parser_use = item.get("parser_use")
    if isinstance(parser_use, str) and parser_use:
        return parser_use
    return {
        "candidate": "candidate_only",
        "deferred": "deferred_only",
        "unsupported": "unsupported_only",
    }.get(str(item.get("status", "")), "")


def _platform_fact_rows(payload: dict[str, Any]) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for record in payload.get("records", []):
        record_id = str(record.get("id", ""))
        if not record_id:
            continue
        rows.append((record_id, record_id, "record", str(record.get("fact_state", "")), ""))
        for section in PLATFORM_FACT_SECTIONS:
            for item in record.get(section, []):
                item_id = str(item.get("id", ""))
                if not item_id:
                    continue
                rows.append((record_id, item_id, section, str(item.get("status", "")), _platform_parser_use(item)))
    return rows


def _write_platform_executable_format_files(path_h: Path, path_c: Path, payload: dict[str, Any]) -> None:
    guard = "PLATFORM_EXECUTABLE_FORMATS_H"
    rows = _platform_fact_rows(payload)
    record_ids = sorted({record_id for record_id, _item_id, section, _status, _parser_use in rows if section == "record"})
    fact_ids = sorted({item_id for _record_id, item_id, section, _status, _parser_use in rows if section != "record"})

    lines_h = [
        "/* Generated platform executable-format fact metadata. Do not edit directly. */",
        f"#ifndef {guard}",
        f"#define {guard}",
        "",
        "#include <stddef.h>",
        "",
        "typedef struct PlatformExecutableFormatFact {",
        "    const char *record_id;",
        "    const char *fact_id;",
        "    const char *section;",
        "    const char *status;",
        "    const char *parser_use;",
        "} PlatformExecutableFormatFact;",
        "",
    ]
    for record_id in record_ids:
        lines_h.append(f"#define {_define_name('PLATFORM_EXECUTABLE_FORMAT_RECORD', record_id)} {_json_string(record_id)}")
    if record_ids:
        lines_h.append("")
    for fact_id in fact_ids:
        lines_h.append(f"#define {_define_name('PLATFORM_EXECUTABLE_FORMAT_FACT', fact_id)} {_json_string(fact_id)}")
    if fact_ids:
        lines_h.append("")
    lines_h.extend(
        [
            "extern const PlatformExecutableFormatFact PLATFORM_EXECUTABLE_FORMAT_FACTS[];",
            "extern const size_t PLATFORM_EXECUTABLE_FORMAT_FACT_COUNT;",
            "",
            "const PlatformExecutableFormatFact *platform_executable_format_fact_lookup(",
            "    const char *record_id,",
            "    const char *fact_id",
            ");",
            "",
            f"#endif /* {guard} */",
            "",
        ]
    )
    path_h.write_text("\n".join(_style_runtime_lines(lines_h)).rstrip() + "\n", encoding="utf-8")

    lines_c = [
        "/* Generated platform executable-format fact metadata table. Do not edit directly. */",
        f'#include "{path_h.name}"',
        "",
        "#include <string.h>",
        "",
        "const PlatformExecutableFormatFact PLATFORM_EXECUTABLE_FORMAT_FACTS[] = {",
    ]
    if rows:
        for record_id, item_id, section, status, parser_use in rows:
            lines_c.append(
                f"    {{ {_json_string(record_id)}, {_json_string(item_id)}, {_json_string(section)}, "
                f"{_json_string(status)}, {_json_string(parser_use)} }},"
            )
    else:
        lines_c.append("    { NULL, NULL, NULL, NULL, NULL },")
    lines_c.extend(
        [
            "};",
            "const size_t PLATFORM_EXECUTABLE_FORMAT_FACT_COUNT = sizeof(PLATFORM_EXECUTABLE_FORMAT_FACTS) /",
            "    sizeof(PLATFORM_EXECUTABLE_FORMAT_FACTS[0]);",
            "",
            "const PlatformExecutableFormatFact *platform_executable_format_fact_lookup(",
            "    const char *record_id,",
            "    const char *fact_id",
            ") {",
            "    if (record_id == NULL || fact_id == NULL) {",
            "        return NULL;",
            "    }",
            "    for (size_t index = 0; index < PLATFORM_EXECUTABLE_FORMAT_FACT_COUNT; ++index) {",
            "        const PlatformExecutableFormatFact *fact = &PLATFORM_EXECUTABLE_FORMAT_FACTS[index];",
            "        if (strcmp(fact->record_id, record_id) == 0 && strcmp(fact->fact_id, fact_id) == 0) {",
            "            return fact;",
            "        }",
            "    }",
            "    return NULL;",
            "}",
            "",
        ]
    )
    path_c.write_text("\n".join(_style_runtime_lines(lines_c)).rstrip() + "\n", encoding="utf-8")


def generate(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for name, stem, title in (
        ("amiga_hunk_file.json", "amiga_hunk_file_runtime", "Amiga hunk file"),
        ("atari_st_prg_file.json", "atari_st_prg_file_runtime", "Atari ST PRG file"),
        ("atari_st_disk_file.json", "atari_st_disk_file_runtime", "Atari ST disk file"),
        ("amiga_disk_file.json", "amiga_disk_file_runtime", "Amiga disk file"),
    ):
        payload = _load_json(name)
        path_h = output_dir / f"{stem}.h"
        path_c = output_dir / f"{stem}.c"
        path_json = output_dir / f"{stem}.json"
        _write_runtime_files(
            path_h,
            path_c,
            payload,
            header_comment=f"Generated {title} runtime metadata. Do not edit directly.",
            source_comment=f"Generated {title} runtime metadata tables. Do not edit directly.",
        )
        _write_runtime_json(path_json, payload)
        outputs.extend([path_h, path_c, path_json])
    platform_payload = _load_json("platform_executable_formats.json")
    path_h = output_dir / "platform_executable_formats.h"
    path_c = output_dir / "platform_executable_formats.c"
    _write_platform_executable_format_files(path_h, path_c, platform_payload)
    outputs.extend([path_h, path_c])
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate compact C runtime metadata from platform format JSON files.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    for output in generate(args.output_dir):
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
