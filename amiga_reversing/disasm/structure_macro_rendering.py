"""Optional structure presentation derived from canonical schemas/native rows.

Typing and boundaries never come from source spellings. Rendered expressions are
copied only after schema/native-coordinate checks; unsupported instances stay flat.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_DATA = re.compile(r"\s*dc\.([bwl])\s+([^;\r\n]+?)(?:\s*;([^\r\n]*))?\s*\Z", re.IGNORECASE)
_WIDTH = {"b": 1, "w": 2, "l": 4}
# Wire values of M68kRenderPlanRowKind (src/m68k_render_plan.h), checked by the
# native integration fixture rather than interpreted from source text.
_NATIVE_ROW_ORG = 7
_NATIVE_ROW_LABEL = 8
_NATIVE_ROW_DATA = 10


def _physical_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use native subline coordinate masks, never derive byte ranges from text."""
    result = []
    for row in plan_rows:
        if "line_ranges" not in row:
            result.append(row)
            continue
        cursor = row["start_byte"]
        lines = row["text"].splitlines(keepends=True)
        for index, text in enumerate(lines):
            ranges = row["line_ranges"][index] if index < len(row["line_ranges"]) else [0, 0, 0]
            source = index < 32 and row["source_line_mask"] & (1 << index)
            label = index < 32 and row["label_line_mask"] & (1 << index)
            directive = index < 32 and row["directive_line_mask"] & (1 << index)
            single = len(lines) == 1 and row["has_source_range"]
            size = len(text.encode("utf-8"))
            result.append({**row, "start_byte": cursor, "byte_count": size, "text": text,
                           "kind": _NATIVE_ROW_ORG if directive else _NATIVE_ROW_LABEL if label else row["kind"],
                           "has_source_range": bool(source or label or single),
                           "source_offset": ranges[0] if source else ranges[2] if label else row["source_offset"],
                           "source_size": ranges[1] if source else 0 if label else row["source_size"] if single else 0})
            cursor += size
    return result


def render_structure_macros(source_text: str, *, canonical_source_text: str,
                            metadata: dict[str, Any], source_plan: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Project only exact contiguous scalar records, preserving canonical labels.

    Up to nine positional arguments: nine values without labels, eight with a
    label prefix, seven with an array prefix/index. Arrays require exact stride.
    Native field labels matching canonical schema names are emitted inside the
    macro at their original offsets; unrelated interior labels force fallback.
    """
    schemas = {s["name"]: s for s in metadata.get("custom_structs", [])}
    rows = _physical_rows(source_plan.get("rows", []))
    labels = source_plan.get("labels", [])
    canonical = canonical_source_text.encode("utf-8")
    replacements: list[tuple[int, int, str]] = []
    definitions: dict[str, str] = {}
    fallbacks: list[dict[str, Any]] = []
    reasons: Counter[str] = Counter()
    fallback_records = 0
    unknown_count_groups = 0
    instances = 0

    def fallback(layout: dict[str, Any], section: int, offset: int, reason: str, records: int = 1) -> None:
        nonlocal fallback_records, unknown_count_groups
        reasons[reason] += 1
        fallback_records += records
        unknown_count_groups += not records
        if len(fallbacks) < 100:
            fallbacks.append({"layout_id": layout["layout_id"], "source_section_index": section,
                              "source_offset": offset, "reason": reason, "records": records})

    for layout in metadata.get("data_block_layouts", []):
        section = layout["hunk"]
        for element in layout.get("elements", []):
            binding = element.get("type_binding") or {}
            if binding.get("binding_kind") != "custom_struct":
                continue
            start = layout["source_start"] + element["offset"]
            count = binding.get("array_count") or element.get("array_count") or 1
            record_count = count if type(count) is int and count > 0 else 0
            schema = schemas.get(binding.get("bound_type_id"))
            if schema is None:
                fallback(layout, section, start, "missing_canonical_schema", record_count)
                continue
            fields = sorted(schema.get("fields", []), key=lambda field: field["offset"])
            cursor = 0
            schema_reason = None
            if schema.get("base_struct"):
                schema_reason = "inherited_or_nested_schema"
            for field in fields:
                if (field["offset"] != cursor or field["size"] not in {1, 2, 4}
                        or field.get("struct") or not _IDENTIFIER.fullmatch(field["name"])):
                    schema_reason = "schema_gap_overlap_or_unsupported_field"
                    break
                cursor += field["size"]
            if not fields or cursor != schema["size"]:
                schema_reason = schema_reason or "schema_gap_overlap_or_unsupported_field"
            stride = element.get("array_stride") or schema["size"]
            if (type(count) is not int or count < 1 or stride != schema["size"]
                    or element["width"] != count * stride or start + element["width"] > layout["source_end"]):
                schema_reason = "unsupported_array_extent_or_stride"
            if schema_reason:
                fallback(layout, section, start, schema_reason, record_count)
                continue
            base = layout.get("name") if element["offset"] == 0 and layout.get("name") else element.get("name")
            if base is not None and not _IDENTIFIER.fullmatch(base):
                fallback(layout, section, start, "unsupported_label_prefix", record_count)
                continue
            prefix_args = ([base, "0"] if count > 1 else [base]) if base else []
            if len(fields) + len(prefix_args) > 9:
                fallback(layout, section, start, "positional_argument_limit_9", record_count)
                continue
            for instance in range(count):
                pos = start + instance * stride
                end = pos + stride
                overlaps = [row for row in rows if row.get("has_source_range")
                            and row["source_section_index"] == section and row["source_size"]
                            and row["source_offset"] < end and row["source_offset"] + row["source_size"] > pos]
                if (len(overlaps) != len(fields) or any(row["kind"] != _NATIVE_ROW_DATA for row in overlaps)
                        or any(row["source_offset"] != pos + field["offset"] or row["source_size"] != field["size"]
                               for row, field in zip(overlaps, fields, strict=True))):
                    fallback(layout, section, pos, "native_range_overlap_or_field_boundary")
                    continue
                native_labels = [label for label in labels if label["source_section_index"] == section
                                 and pos <= label["source_offset"] < end]
                expected = {}
                for index, field in enumerate(fields):
                    if base:
                        public = instance == 0 and index == 0
                        expected[pos + field["offset"]] = (base if public else
                            f"{base}_{field['name']}" + (f"_{instance}" if count > 1 else ""))
                if any(label["name"] != expected.get(label["source_offset"]) for label in native_labels):
                    fallback(layout, section, pos, "noncanonical_interior_label")
                    continue
                label_map = {label["source_offset"]: label["name"] for label in native_labels}
                if len(label_map) != len(native_labels):
                    fallback(layout, section, pos, "ambiguous_native_label")
                    continue
                associated = [row for row in rows if row.get("has_source_range") and row["source_section_index"] == section
                          and pos <= row["source_offset"] < end]
                if not associated:
                    fallback(layout, section, pos, "native_rows_missing")
                    continue
                chosen = rows[rows.index(associated[0]):rows.index(associated[-1]) + 1]
                first, last = chosen[0], chosen[-1]
                block_start, block_end = first["start_byte"], last["start_byte"] + last["byte_count"]
                block = canonical[block_start:block_end].decode("utf-8")
                if block != "".join(row["text"] for row in chosen):
                    fallback(layout, section, pos, "noncontiguous_native_rows")
                    continue
                args = ([base, str(instance)] if count > 1 else [base]) if base else []
                body = []
                annotations = []
                preserve_start = ""
                failed = None
                for index, (row, field) in enumerate(zip(overlaps, fields, strict=True)):
                    match = _DATA.fullmatch(row["text"].rstrip("\r\n"))
                    if (not match or _WIDTH[match[1].lower()] != field["size"] or "," in match[2]
                            or "'" in row["text"].split(";")[0] or '"' in row["text"].split(";")[0]):
                        failed = "unsupported_native_field_expression"
                        break
                    # Parameters are literal expressions, never reinterpreted bytes.
                    value = match[2].strip()
                    if "\\" in value or "\n" in value:
                        failed = "unsupported_native_field_expression"
                        break
                    args.append(value)
                    if pos + field["offset"] in label_map:
                        if instance == 0 and index == 0:
                            preserve_start = f"{base}:\n"
                        else:
                            body.append(f"\\1_{field['name']}" + ("_\\2" if count > 1 else "") + ":\n")
                    body.append(f"\tdc.{match[1].lower()} \\{len(prefix_args) + index + 1}\t; {field['name']}\n")
                    if match[3] is not None and match[3].strip() != field["name"]:
                        annotations.append(f"; {field['name']}: {match[3].strip()}\n")
                # Only canonical labels and scalar field directives may disappear.
                for row in chosen:
                    if row in overlaps:
                        continue
                    if row["text"].strip().startswith(";") or not row["text"].strip():
                        annotations.append(row["text"])
                        continue
                    if row["kind"] != _NATIVE_ROW_LABEL or row["text"].strip() != label_map.get(row["source_offset"], "") + ":":
                        failed = "interior_directive_comment_or_alias"
                if failed:
                    fallback(layout, section, pos, failed)
                    continue
                macro_key = json.dumps([schema["name"], body], separators=(",", ":"))
                name = "STRUCT_" + re.sub(r"[^A-Za-z0-9_]", "_", schema["name"])[:48] + "_" + hashlib.sha256(macro_key.encode()).hexdigest()[:8]
                if re.search(rf"(?im)^\s*{re.escape(name)}\b", canonical_source_text):
                    fallback(layout, section, pos, "macro_symbol_collision")
                    continue
                if len(definitions) >= 128 and name not in definitions:
                    fallback(layout, section, pos, "macro_definition_limit_128")
                    continue
                if source_text == canonical_source_text:
                    output_start, output_end = block_start, block_end
                elif source_text.count(block) == 1:
                    output_start = len(source_text[:source_text.index(block)].encode("utf-8"))
                    output_end = output_start + len(block.encode("utf-8"))
                else:
                    fallback(layout, section, pos, "package_projection_span_not_unique")
                    continue
                if any(output_start < other_end and other_start < output_end for other_start, other_end, _ in replacements):
                    fallback(layout, section, pos, "overlapping_schema_instances")
                    continue
                field_order = ", ".join(f"{field['name']}@{field['offset']}:{field['size']}" for field in fields)
                prefix_doc = "prefix, index, " if base and count > 1 else "prefix, " if base else ""
                definitions[name] = (f"; {schema['name']} size={schema['size']}; arguments: {prefix_doc}{field_order}\n"
                    f"{name} MACRO\n" + "".join(body) + "\tENDM\n")
                replacements.append((output_start, output_end, preserve_start + "".join(annotations)
                                     + f"\t{name} " + ",".join(args) + "\n"))
                instances += 1
    output = source_text.encode("utf-8")
    for start, end, replacement in sorted(replacements, reverse=True):
        output = output[:start] + replacement.encode("utf-8") + output[end:]
    text = "".join(definitions[name] + "\n" for name in sorted(definitions)) + output.decode("utf-8")
    return text, {"selection": "custom_struct_bindings", "candidate_record_count": instances + fallback_records,
                  "definitions": len(definitions), "instances": instances, "fallback_count": fallback_records,
                  "fallback_record_count": fallback_records, "fallback_group_count": sum(reasons.values()),
                  "fallback_unknown_count_groups": unknown_count_groups,
                  "fallback_reason_counts": dict(sorted(reasons.items())), "fallbacks": fallbacks}
