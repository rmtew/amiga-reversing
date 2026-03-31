from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from kb.os_reference import (
    load_split_os_reference_payloads,
    merge_os_reference_payloads,
)
from kb.schemas import (
    OsAbsoluteSymbol,
    OsCallingConvention,
    OsConstant,
    OsExecBaseAddress,
    OsFunction,
    OsInput,
    OsLibrary,
    OsOutput,
    OsReferencePayload,
    OsReturnsBase,
    OsReturnsMemory,
    OsStructDef,
    OsStructField,
    OsTypedDataStreamFormat,
    OsValueDomain,
)
from m68k import analysis as m68k_analysis
from m68k import os_calls as m68k_os_calls
from m68k_kb import runtime_os


def _calling_convention(payload: OsCallingConvention) -> runtime_os.CallingConvention:
    return runtime_os.CallingConvention(
        scratch_regs=tuple(payload["scratch_regs"]),
        preserved_regs=tuple(payload["preserved_regs"]),
        base_reg=str(payload["base_reg"]),
        return_reg=str(payload["return_reg"]),
        note=str(payload["note"]),
        seed_origin=str(payload["seed_origin"]),
        review_status=str(payload["review_status"]),
        citation=str(payload["citation"]),
    )


def _exec_base(payload: OsExecBaseAddress) -> runtime_os.ExecBaseAddress:
    return runtime_os.ExecBaseAddress(
        address=payload["address"],
        library=str(payload["library"]),
        note=str(payload["note"]),
        seed_origin=str(payload["seed_origin"]),
        review_status=str(payload["review_status"]),
        citation=str(payload["citation"]),
    )


def _absolute_symbol(payload: OsAbsoluteSymbol) -> runtime_os.AbsoluteSymbol:
    return runtime_os.AbsoluteSymbol(
        address=payload["address"],
        name=str(payload["name"]),
        note=str(payload["note"]),
        seed_origin=str(payload["seed_origin"]),
        review_status=str(payload["review_status"]),
        citation=str(payload["citation"]),
    )


def _struct_field(payload: OsStructField) -> runtime_os.OsStructField:
    return runtime_os.OsStructField(
        name=payload["name"],
        type=payload["type"],
        offset=payload["offset"],
        size=payload["size"],
        available_since=payload.get("available_since", "1.0"),
        names_by_version=dict(payload.get("names_by_version", {})),
        size_symbol=payload.get("size_symbol"),
        struct=payload.get("struct"),
        c_type=payload.get("c_type"),
        pointer_struct=payload.get("pointer_struct"),
    )


def _struct_def(payload: OsStructDef) -> runtime_os.OsStruct:
    return runtime_os.OsStruct(
        source=payload["source"],
        base_offset=payload["base_offset"],
        base_offset_symbol=payload.get("base_offset_symbol"),
        size=payload["size"],
        fields=tuple(_struct_field(field) for field in payload["fields"]),
        available_since=payload.get("available_since", "1.0"),
        base_struct=payload.get("base_struct"),
    )


def _constant(payload: OsConstant) -> runtime_os.OsConstant:
    return runtime_os.OsConstant(
        raw=payload["raw"],
        value=payload["value"],
        available_since=payload.get("available_since", "1.0"),
        owner=runtime_os.OsIncludeOwner(**payload["owner"]),
    )


def _value_domain(name: str, payload: OsValueDomain) -> runtime_os.OsValueDomain:
    return runtime_os.OsValueDomain(
        kind=str(payload["kind"]),
        members=tuple(payload["members"]),
        zero_name=payload.get("zero_name"),
        exact_match_policy=str(payload["exact_match_policy"]),
        composition=payload.get("composition"),
        remainder_policy=payload.get("remainder_policy"),
    )


def _input(payload: OsInput) -> runtime_os.OsInput:
    return runtime_os.OsInput(
        name=payload["name"],
        regs=tuple(payload["regs"]),
        type=payload.get("type"),
        i_struct=payload.get("i_struct"),
        semantic_kind=payload.get("semantic_kind"),
        semantic_note=payload.get("semantic_note"),
    )


def _output(payload: OsOutput) -> runtime_os.OsOutput:
    return runtime_os.OsOutput(
        name=payload["name"],
        reg=payload.get("reg"),
        type=payload.get("type"),
        i_struct=payload.get("i_struct"),
    )


def _returns_base(payload: OsReturnsBase) -> runtime_os.OsReturnsBase:
    return runtime_os.OsReturnsBase(
        name_reg=payload["name_reg"],
        base_reg=payload["base_reg"],
    )


def _returns_memory(payload: OsReturnsMemory) -> runtime_os.OsReturnsMemory:
    return runtime_os.OsReturnsMemory(
        result_reg=payload["result_reg"],
        size_reg=payload.get("size_reg"),
    )


def _function(payload: OsFunction) -> runtime_os.OsFunction:
    return runtime_os.OsFunction(
        lvo=payload.get("lvo"),
        inputs=tuple(_input(item) for item in payload.get("inputs", [])),
        output=(_output(payload["output"]) if "output" in payload else None),
        returns_base=(
            _returns_base(payload["returns_base"])
            if "returns_base" in payload
            else None
        ),
        returns_memory=(
            _returns_memory(payload["returns_memory"])
            if "returns_memory" in payload
            else None
        ),
        no_return=payload.get("no_return", False),
        available_since=payload.get("available_since"),
        fd_version=payload.get("fd_version"),
        private=payload.get("private", False),
    )


def _library(payload: OsLibrary) -> runtime_os.OsLibrary:
    functions = payload["functions"]
    lvo_index = dict(payload.get("lvo_index", {}))
    if not lvo_index:
        for func_name, func in functions.items():
            lvo = func.get("lvo")
            if lvo is None:
                continue
            key = str(lvo)
            existing = lvo_index.get(key)
            if existing is not None and existing != func_name:
                raise ValueError(f"Duplicate library LVO {key}: {existing} vs {func_name}")
            lvo_index[key] = func_name
    return runtime_os.OsLibrary(
        owner=runtime_os.OsIncludeOwner(**payload["owner"]),
        lvo_index=lvo_index,
        functions={name: _function(func) for name, func in functions.items()},
    )


def build_runtime_os_kb_from_payload(payload: OsReferencePayload) -> object:
    meta = payload["_meta"]
    api_input_value_domains: dict[str, dict[str, dict[str, str]]] = {}
    for api_binding in meta["api_input_value_bindings"]:
        api_input_value_domains.setdefault(api_binding["library"], {}).setdefault(
            api_binding["function"], {}
        )[api_binding["input"]] = api_binding["domain"]
    struct_field_value_domains: dict[str, dict[str | None, str]] = {}
    for field_binding in meta["struct_field_value_bindings"]:
        field_key = f"{field_binding['struct']}.{field_binding['field']}"
        struct_field_value_domains.setdefault(field_key, {})[
            field_binding.get("context_name")
        ] = field_binding["domain"]
    return SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=_calling_convention(meta["calling_convention"]),
            exec_base_addr=_exec_base(meta["exec_base_addr"]),
            absolute_symbols=tuple(
                _absolute_symbol(item) for item in meta["absolute_symbols"]
            ),
            lvo_slot_size=meta["lvo_slot_size"],
            compatibility_versions=tuple(meta["compatibility_versions"]),
            include_min_versions=dict(meta["include_min_versions"]),
            resident_autoinit_words=tuple(meta["resident_autoinit_words"]),
            resident_autoinit_word_stream_formats=dict(meta["resident_autoinit_word_stream_formats"]),
            resident_autoinit_supports_short_vectors=meta[
                "resident_autoinit_supports_short_vectors"
            ],
            resident_vector_prefixes={
                key: tuple(values)
                for key, values in meta["resident_vector_prefixes"].items()
            },
            resident_entry_register_seeds={
                target_type: {
                    role: tuple(dict(spec) for spec in specs)
                    for role, specs in role_map.items()
                }
                for target_type, role_map in meta["resident_entry_register_seeds"].items()
            },
            named_base_structs=dict(meta["named_base_structs"]),
            typed_data_stream_formats=cast(
                dict[str, OsTypedDataStreamFormat],
                dict(meta.get("typed_data_stream_formats", {})),
            ),
        ),
        VALUE_DOMAINS={
            name: _value_domain(name, domain)
            for name, domain in payload["_meta"]["value_domains"].items()
        },
        API_INPUT_VALUE_DOMAINS=api_input_value_domains,
        STRUCT_FIELD_VALUE_DOMAINS=struct_field_value_domains,
        STRUCTS={
            name: _struct_def(struct_def)
            for name, struct_def in payload["structs"].items()
        },
        CONSTANTS={
            name: _constant(constant) for name, constant in payload["constants"].items()
        },
        LIBRARIES={
            name: _library(library) for name, library in payload["libraries"].items()
        },
    )


def load_live_os_reference_payload() -> OsReferencePayload:
    includes, other, corrections = load_split_os_reference_payloads()
    return cast(
        OsReferencePayload,
        merge_os_reference_payloads(
            includes=includes,
            other=other,
            corrections=corrections,
        ),
    )


def install_live_runtime_os_kb() -> object:
    payload = load_live_os_reference_payload()
    runtime_kb = build_runtime_os_kb_from_payload(payload)
    m68k_os_calls.RUNTIME_OS_KB = runtime_kb
    m68k_analysis.RUNTIME_OS_KB = runtime_kb
    return runtime_kb
