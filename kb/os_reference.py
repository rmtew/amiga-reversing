from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from kb.paths import (
    AMIGA_OS_REFERENCE_CORRECTIONS_JSON,
    AMIGA_OS_REFERENCE_INCLUDES_PARSED_JSON,
    AMIGA_OS_REFERENCE_OTHER_PARSED_JSON,
)
from kb.schemas import OsReferencePayload

JsonObject = dict[str, object]
EXTENSION_META_KEYS = frozenset({
    "calling_convention",
    "exec_base_addr",
    "absolute_symbols",
    "value_domains",
    "api_input_value_bindings",
    "api_input_type_overrides",
    "api_input_semantic_assertions",
    "struct_field_value_bindings",
})
CORRECTION_SEED_ORIGIN_VALUES = frozenset({
    "primary_doc",
    "include",
    "autodoc",
    "manual",
})
CORRECTION_REVIEW_STATUS_VALUES = frozenset({
    "seeded",
    "validated",
})


def load_os_reference_payload(path: Path) -> OsReferencePayload:
    with open(path, encoding="utf-8") as handle:
        return cast(OsReferencePayload, json.load(handle))


def load_split_os_reference_payloads() -> tuple[OsReferencePayload, OsReferencePayload, OsReferencePayload]:
    return (
        load_os_reference_payload(AMIGA_OS_REFERENCE_INCLUDES_PARSED_JSON),
        load_os_reference_payload(AMIGA_OS_REFERENCE_OTHER_PARSED_JSON),
        load_os_reference_payload(AMIGA_OS_REFERENCE_CORRECTIONS_JSON),
    )


def normalize_os_reference_corrections(corrections: OsReferencePayload) -> OsReferencePayload:
    correction_meta = corrections["_meta"]
    return cast(
        OsReferencePayload,
        {
            "_meta": {
                "calling_convention": correction_meta.get("calling_convention"),
                "exec_base_addr": correction_meta.get("exec_base_addr"),
                "absolute_symbols": sorted(
                    correction_meta.get("absolute_symbols", []),
                    key=lambda symbol: (symbol["address"], symbol["name"]),
                ),
                "value_domains": dict(sorted(correction_meta.get("value_domains", {}).items())),
                "api_input_value_bindings": sorted(
                    correction_meta.get("api_input_value_bindings", []),
                    key=lambda binding: (
                        binding["library"],
                        binding["function"],
                        binding["input"],
                    ),
                ),
                "api_input_type_overrides": sorted(
                    correction_meta.get("api_input_type_overrides", []),
                    key=lambda override: (
                        override["library"],
                        override["function"],
                        override["input"],
                    ),
                ),
                "api_input_semantic_assertions": sorted(
                    correction_meta.get("api_input_semantic_assertions", []),
                    key=lambda assertion: (
                        assertion["library"],
                        assertion["function"],
                        assertion["input"],
                    ),
                ),
                "struct_field_value_bindings": sorted(
                    correction_meta.get("struct_field_value_bindings", []),
                    key=lambda binding: (
                        binding["struct"],
                        binding["field"],
                        binding.get("context_name", ""),
                    ),
                ),
            },
            "libraries": {},
            "structs": {},
            "constants": {},
        },
    )


def merge_parsed_os_reference_payloads(
    *,
    includes: OsReferencePayload,
    other: OsReferencePayload,
) -> OsReferencePayload:
    merged = cast(OsReferencePayload, json.loads(json.dumps(includes)))
    merged_meta = merged["_meta"]
    other_meta = other["_meta"]

    if other["structs"] or other["constants"]:
        raise ValueError("Other parsed OS reference payload must not define structs or constants")

    for meta_key in (
        "source",
        "ndk_path",
        "type_sizes",
        "struct_name_map",
        "version_map",
        "version_fields_note",
        "os_since_default_note",
    ):
        if meta_key in other_meta:
            merged_meta[meta_key] = other_meta[meta_key]

    for library_name, other_library in other["libraries"].items():
        if library_name not in merged["libraries"]:
            raise ValueError(f"Other parsed OS reference payload references missing library {library_name}")
        merged_library = merged["libraries"][library_name]
        for key in other_library:
            if key not in {"functions"}:
                raise ValueError(
                    f"Other parsed OS reference payload must not override library-level key "
                    f"{library_name}.{key}"
                )
        for function_name, function_overlay in other_library.get("functions", {}).items():
            merged_function = merged_library["functions"].get(function_name)
            if merged_function is None:
                merged_library["functions"][function_name] = function_overlay
                continue
            for field_name, field_value in function_overlay.items():
                merged_function[field_name] = field_value

    return merged


def merge_os_reference_payloads(
    *,
    includes: OsReferencePayload,
    other: OsReferencePayload,
    corrections: OsReferencePayload,
) -> OsReferencePayload:
    merged = merge_parsed_os_reference_payloads(includes=includes, other=other)
    merged_meta = merged["_meta"]
    parsed_meta = merged["_meta"]
    correction_meta = corrections["_meta"]

    if corrections["libraries"] or corrections["structs"] or corrections["constants"]:
        raise ValueError("OS reference corrections must not define libraries, structs, or constants")
    unexpected_extension_meta = set(correction_meta) - EXTENSION_META_KEYS
    if unexpected_extension_meta:
        raise ValueError(
            "OS reference corrections must not define non-correction meta keys: "
            f"{sorted(unexpected_extension_meta)}"
        )

    def _require_extension_fields(entry: JsonObject, fields: tuple[str, ...], kind: str) -> None:
        missing = [field for field in fields if field not in entry]
        if missing:
            raise ValueError(f"OS {kind} is missing required fields {missing}: {entry}")

    def _require_correction_status(entry: JsonObject, kind: str) -> None:
        _require_extension_fields(entry, ("seed_origin", "review_status", "citation"), kind)
        seed_origin = cast(str, entry["seed_origin"])
        review_status = cast(str, entry["review_status"])
        if seed_origin not in CORRECTION_SEED_ORIGIN_VALUES:
            raise ValueError(
                f"OS {kind} uses unknown seed_origin {seed_origin!r}; "
                f"expected one of {sorted(CORRECTION_SEED_ORIGIN_VALUES)}"
            )
        if review_status not in CORRECTION_REVIEW_STATUS_VALUES:
            raise ValueError(
                f"OS {kind} uses unknown review_status {review_status!r}; "
                f"expected one of {sorted(CORRECTION_REVIEW_STATUS_VALUES)}"
            )

    if "calling_convention" in correction_meta:
        _require_correction_status(
            cast(JsonObject, correction_meta["calling_convention"]),
            "calling_convention correction",
        )
        merged_meta["calling_convention"] = correction_meta["calling_convention"]
    if "exec_base_addr" in correction_meta:
        _require_correction_status(
            cast(JsonObject, correction_meta["exec_base_addr"]),
            "exec_base_addr correction",
        )
        merged_meta["exec_base_addr"] = correction_meta["exec_base_addr"]
    if "absolute_symbols" in correction_meta:
        for symbol in correction_meta["absolute_symbols"]:
            _require_correction_status(
                cast(JsonObject, symbol),
                "absolute_symbol correction",
            )
        merged_meta["absolute_symbols"] = correction_meta["absolute_symbols"]

    merged_value_domains = dict(parsed_meta["value_domains"])
    for domain_name, domain_data in correction_meta.get("value_domains", {}).items():
        existing = merged_value_domains.get(domain_name)
        if existing is not None and existing != domain_data:
            raise ValueError(
                f"Conflicting OS value domain {domain_name}: {existing} vs {domain_data}"
            )
        merged_value_domains[domain_name] = domain_data
    merged_meta["value_domains"] = merged_value_domains

    api_binding_keys: set[tuple[str, str, str]] = set()
    merged_api_bindings = list(parsed_meta["api_input_value_bindings"])
    extension_api_bindings = correction_meta.get("api_input_value_bindings", [])
    for binding in extension_api_bindings:
        _require_correction_status(
            cast(JsonObject, binding),
            "api_input_value_binding extension",
        )
    for binding in merged_api_bindings + extension_api_bindings:
        binding_key = (binding["library"], binding["function"], binding["input"])
        if binding_key in api_binding_keys:
            raise ValueError(f"Duplicate OS API input binding {binding_key}")
        api_binding_keys.add(binding_key)
    merged_api_bindings.extend(extension_api_bindings)
    merged_meta["api_input_value_bindings"] = merged_api_bindings

    type_override_keys: set[tuple[str, str, str]] = set()
    merged_type_overrides: list[JsonObject] = []
    extension_type_overrides = correction_meta.get("api_input_type_overrides", [])
    for override in extension_type_overrides:
        _require_correction_status(
            cast(JsonObject, override),
            "api_input_type_override extension",
        )
    for override in extension_type_overrides:
        override_key = (override["library"], override["function"], override["input"])
        if override_key in type_override_keys:
            raise ValueError(f"Duplicate OS API input type override {override_key}")
        type_override_keys.add(override_key)
        merged_type_overrides.append(cast(JsonObject, override))
    merged_meta["api_input_type_overrides"] = merged_type_overrides

    semantic_assertion_keys: set[tuple[str, str, str]] = set()
    merged_semantic_assertions = list(parsed_meta["api_input_semantic_assertions"])
    extension_semantic_assertions = correction_meta.get("api_input_semantic_assertions", [])
    for assertion in extension_semantic_assertions:
        _require_correction_status(
            cast(JsonObject, assertion),
            "api_input_semantic_assertion extension",
        )
    for assertion in merged_semantic_assertions + extension_semantic_assertions:
        assertion_key = (assertion["library"], assertion["function"], assertion["input"])
        if assertion_key in semantic_assertion_keys:
            raise ValueError(f"Duplicate OS API input semantic assertion {assertion_key}")
        semantic_assertion_keys.add(assertion_key)
    merged_semantic_assertions.extend(extension_semantic_assertions)
    merged_meta["api_input_semantic_assertions"] = merged_semantic_assertions

    field_binding_keys: set[tuple[str, str, str | None]] = set()
    merged_field_bindings = list(parsed_meta["struct_field_value_bindings"])
    extension_field_bindings = correction_meta.get("struct_field_value_bindings", [])
    for binding in extension_field_bindings:
        _require_correction_status(
            cast(JsonObject, binding),
            "struct_field_value_binding extension",
        )
    for binding in merged_field_bindings + extension_field_bindings:
        binding_key = (binding["struct"], binding["field"], binding.get("context_name"))
        if binding_key in field_binding_keys:
            raise ValueError(f"Duplicate OS struct field binding {binding_key}")
        field_binding_keys.add(binding_key)
    merged_field_bindings.extend(extension_field_bindings)
    merged_meta["struct_field_value_bindings"] = merged_field_bindings

    for binding in merged_meta["api_input_value_bindings"]:
        library = merged["libraries"].get(binding["library"])
        if library is None:
            raise ValueError(f"OS API input binding references missing library {binding['library']}")
        function = library["functions"].get(binding["function"])
        if function is None:
            raise ValueError(
                f"OS API input binding references missing function {binding['library']}/{binding['function']}"
            )
        inputs = {
            input_entry["name"]
            for input_entry in function.get("inputs", [])
            if "name" in input_entry
        }
        if binding["input"] not in inputs:
            raise ValueError(
                f"OS API input binding references missing input "
                f"{binding['library']}/{binding['function']}.{binding['input']}"
            )
        if binding["domain"] not in merged_meta["value_domains"]:
            raise ValueError(
                f"OS API input binding references missing value domain {binding['domain']}"
            )

    inputs_by_key: dict[tuple[str, str, str], JsonObject] = {}
    for library_name, library in merged["libraries"].items():
        for function_name, function in library["functions"].items():
            for input_entry in function.get("inputs", []):
                if "name" not in input_entry:
                    continue
                inputs_by_key[(library_name, function_name, input_entry["name"])] = input_entry

    for override in merged_meta["api_input_type_overrides"]:
        override_key = (override["library"], override["function"], override["input"])
        input_entry = inputs_by_key.get(override_key)
        if input_entry is None:
            raise ValueError(
                "OS API input type override references missing input "
                f"{override['library']}/{override['function']}.{override['input']}"
            )
        if "type" not in override:
            raise ValueError(f"OS API input type override missing type {override_key}")
        input_entry["type"] = override["type"]
        if "i_struct" in override:
            if override["i_struct"] not in merged["structs"]:
                raise ValueError(
                    "OS API input type override references missing struct "
                    f"{override['i_struct']}"
                )
            input_entry["i_struct"] = override["i_struct"]
        else:
            input_entry.pop("i_struct", None)

    for assertion in merged_meta["api_input_semantic_assertions"]:
        assertion_key = (assertion["library"], assertion["function"], assertion["input"])
        input_entry = inputs_by_key.get(assertion_key)
        if input_entry is None:
            raise ValueError(
                "OS API input semantic assertion references missing input "
                f"{assertion['library']}/{assertion['function']}.{assertion['input']}"
            )
        existing_kind = input_entry.get("semantic_kind")
        if existing_kind is not None and existing_kind != assertion["semantic_kind"]:
            raise ValueError(
                "OS API input semantic assertion conflicts with parsed semantic kind "
                f"{assertion_key}: {existing_kind} vs {assertion['semantic_kind']}"
            )
        existing_note = input_entry.get("semantic_note")
        if existing_note is not None and existing_note != assertion["semantic_note"]:
            raise ValueError(
                "OS API input semantic assertion conflicts with parsed semantic note "
                f"{assertion_key}"
            )
        input_entry["semantic_kind"] = assertion["semantic_kind"]
        input_entry["semantic_note"] = assertion["semantic_note"]

    for binding in merged_meta["struct_field_value_bindings"]:
        struct_def = merged["structs"].get(binding["struct"])
        if struct_def is None:
            raise ValueError(f"OS struct field binding references missing struct {binding['struct']}")
        if not any(field["name"] == binding["field"] for field in struct_def["fields"]):
            raise ValueError(
                f"OS struct field binding references missing field {binding['struct']}.{binding['field']}"
            )
        if binding["domain"] not in merged_meta["value_domains"]:
            raise ValueError(
                f"OS struct field binding references missing value domain {binding['domain']}"
            )

    for domain_name, domain_data in merged_meta["value_domains"].items():
        domain_kind = domain_data.get("kind")
        if domain_kind not in {"enum", "flags"}:
            raise ValueError(
                f"OS value domain {domain_name} uses unsupported kind {domain_kind!r}"
            )
        domain_members = domain_data.get("members")
        if not isinstance(domain_members, list) or not domain_members:
            raise ValueError(
                f"OS value domain {domain_name} is missing non-empty members"
            )
        for constant_name in domain_members:
            if constant_name not in merged["constants"]:
                raise ValueError(
                    f"OS value domain {domain_name} references missing constant {constant_name}"
                )
        zero_name = domain_data.get("zero_name")
        if zero_name is not None and zero_name not in merged["constants"]:
            raise ValueError(
                f"OS value domain {domain_name} references missing zero_name constant {zero_name}"
            )
        if "exact_match_policy" not in domain_data:
            raise ValueError(
                f"OS value domain {domain_name} is missing exact_match_policy"
            )
        exact_match_policy = domain_data["exact_match_policy"]
        if exact_match_policy not in {"error", "canonical_by_member_order"}:
            raise ValueError(
                f"OS value domain {domain_name} uses unsupported exact_match_policy "
                f"{exact_match_policy!r}"
            )
        composition = domain_data.get("composition")
        if domain_kind == "enum":
            if composition is not None:
                raise ValueError(
                    f"Enum OS value domain {domain_name} must not define composition"
                )
            if "remainder_policy" in domain_data:
                raise ValueError(
                    f"Enum OS value domain {domain_name} must not define remainder_policy"
                )
        else:
            if composition != "bit_or":
                raise ValueError(
                    f"Flag OS value domain {domain_name} must define composition='bit_or'"
                )
            if "remainder_policy" not in domain_data:
                raise ValueError(
                    f"Flag OS value domain {domain_name} is missing remainder_policy"
                )
            remainder_policy = domain_data["remainder_policy"]
            if remainder_policy not in {"error", "append_hex"}:
                raise ValueError(
                    f"OS value domain {domain_name} uses unsupported remainder_policy "
                    f"{remainder_policy!r}"
                )

    return merged
