from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import TypeGuard, cast

from .amiga_metadata import ResidentAutoinitMetadata
from .binary_source import BinarySourceKind

TARGET_METADATA_FILE_NAME = "target_metadata.json"
TARGET_SEEDED_METADATA_FILE_NAME = "target_seeded_metadata.json"
TARGET_CORRECTIONS_FILE_NAME = "target_corrections.json"


@dataclass(frozen=True, slots=True)
class SourceOutputPolicyMetadata:
    """Presentation only; native data classifications determine eligibility."""

    mode: str = "inline"
    minimum_asset_size: int = 256

    def __post_init__(self) -> None:
        if not isinstance(self.mode, str) or self.mode not in {"inline", "binary_assets"}:
            raise ValueError("source output mode must be inline or binary_assets")
        if type(self.minimum_asset_size) is not int or not 1 <= self.minimum_asset_size <= 0xFFFFFFFF:
            raise ValueError("minimum_asset_size must be 1..4294967295")

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SourceOutputPolicyMetadata:
        if set(payload) - {"mode", "minimum_asset_size"}:
            raise ValueError("unsupported source output policy field")
        return cls(mode=cast(str, payload.get("mode", "inline")),
                   minimum_asset_size=cast(int, payload.get("minimum_asset_size", 256)))


class TargetMetadataSeedOrigin(StrEnum):
    MANUAL_ANALYSIS = "manual_analysis"
    PRIMARY_DOC = "primary_doc"
    INCLUDE = "include"
    AUTODOC = "autodoc"


class TargetMetadataReviewStatus(StrEnum):
    SEEDED = "seeded"
    VALIDATED = "validated"


class SuppressedSeededItemKind(StrEnum):
    SEEDED_ENTITY = "seeded_entity"
    SEEDED_CODE_LABEL = "seeded_code_label"
    SEEDED_CODE_ENTRYPOINT = "seeded_code_entrypoint"


class RssetLayoutStorageKind(StrEnum):
    STRUCT_INSTANCE = "struct_instance"
    STRUCT_POINTER = "struct_pointer"
    POINTER = "pointer"
    POINTER_TABLE = "pointer_table"
    SCALAR = "scalar"
    BYTE_ARRAY = "byte_array"


class EntryRegisterSeedKind(StrEnum):
    LIBRARY_BASE = "library_base"
    STRUCT_PTR = "struct_ptr"


class ManualRepresentationStyle(StrEnum):
    HEX = "hex"
    DECIMAL = "decimal"
    BINARY = "binary"
    CHARACTER = "character"
    STRING = "string"
    SYMBOL = "symbol"


class DataBlockElementKind(StrEnum):
    SCALAR = "scalar"
    ARRAY = "array"
    STRUCT = "struct"
    PLATFORM_STRUCT = "platform_struct"
    POINTER_REFERENCE = "pointer_reference"
    PADDING = "padding"
    GAP = "gap"
    RAW = "raw"


def _json_object(value: object, *, what: str = "JSON value") -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _json_list(value: object, *, what: str = "JSON value") -> list[object]:
    assert isinstance(value, list)
    return value


def _target_metadata_seed_origin(value: object) -> TargetMetadataSeedOrigin:
    assert isinstance(value, str)
    try:
        return TargetMetadataSeedOrigin(value)
    except ValueError:
        raise AssertionError(f"Unsupported target metadata seed_origin: {value}") from None


def _target_metadata_review_status(value: object) -> TargetMetadataReviewStatus:
    assert isinstance(value, str)
    try:
        return TargetMetadataReviewStatus(value)
    except ValueError:
        raise AssertionError(f"Unsupported target metadata review_status: {value}") from None


def _suppressed_seeded_item_kind(value: object) -> SuppressedSeededItemKind:
    assert isinstance(value, str)
    try:
        return SuppressedSeededItemKind(value)
    except ValueError:
        raise AssertionError(f"Unsupported suppressed seeded item kind: {value}") from None


def _rsset_layout_storage_kind(value: object) -> RssetLayoutStorageKind:
    assert isinstance(value, str)
    try:
        return RssetLayoutStorageKind(value)
    except ValueError:
        raise AssertionError(f"Unsupported RSSET layout storage_kind: {value}") from None


def _entry_register_seed_kind(value: object) -> EntryRegisterSeedKind:
    assert isinstance(value, str)
    try:
        return EntryRegisterSeedKind(value)
    except ValueError:
        raise AssertionError(f"Unsupported entry register seed kind: {value}") from None


def _manual_representation_style(value: object) -> ManualRepresentationStyle:
    assert isinstance(value, str)
    try:
        return ManualRepresentationStyle(value)
    except ValueError:
        raise AssertionError(f"Unsupported manual representation style: {value}") from None


def _data_block_element_kind(value: object) -> DataBlockElementKind:
    assert isinstance(value, str)
    try:
        return DataBlockElementKind(value)
    except ValueError:
        raise AssertionError(f"Unsupported data block element kind: {value}") from None


def _assert_target_metadata_review_fields(
    seed_origin: object,
    review_status: object,
) -> None:
    assert isinstance(seed_origin, TargetMetadataSeedOrigin)
    assert isinstance(review_status, TargetMetadataReviewStatus)


@dataclass(frozen=True, slots=True)
class BootBlockTargetMetadata:
    magic_ascii: str
    flags_byte: int
    fs_description: str
    checksum: str
    checksum_valid: bool
    rootblock_ptr: int
    bootcode_offset: int
    bootcode_size: int
    load_address: int
    entrypoint: int
    bootcode_has_code: bool | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> BootBlockTargetMetadata:
        magic_ascii = payload["magic_ascii"]
        flags_byte = payload["flags_byte"]
        fs_description = payload["fs_description"]
        checksum = payload["checksum"]
        checksum_valid = payload["checksum_valid"]
        rootblock_ptr = payload["rootblock_ptr"]
        bootcode_offset = payload["bootcode_offset"]
        bootcode_size = payload["bootcode_size"]
        bootcode_has_code = payload.get("bootcode_has_code")
        load_address = payload["load_address"]
        entrypoint = payload["entrypoint"]
        assert isinstance(magic_ascii, str)
        assert isinstance(flags_byte, int)
        assert isinstance(fs_description, str)
        assert isinstance(checksum, str)
        assert isinstance(checksum_valid, bool)
        assert isinstance(rootblock_ptr, int)
        assert isinstance(bootcode_offset, int)
        assert isinstance(bootcode_size, int)
        assert bootcode_has_code is None or isinstance(bootcode_has_code, bool)
        assert isinstance(load_address, int)
        assert isinstance(entrypoint, int)
        return cls(
            magic_ascii=magic_ascii,
            flags_byte=flags_byte,
            fs_description=fs_description,
            checksum=checksum,
            checksum_valid=checksum_valid,
            rootblock_ptr=rootblock_ptr,
            bootcode_offset=bootcode_offset,
            bootcode_size=bootcode_size,
            bootcode_has_code=bootcode_has_code,
            load_address=load_address,
            entrypoint=entrypoint,
        )

@dataclass(frozen=True, slots=True)
class EntryRegisterSeedMetadata:
    entry_offset: int | None
    register: str
    kind: EntryRegisterSeedKind
    note: str
    library_name: str | None = None
    struct_name: str | None = None
    context_name: str | None = None
    source_evidence_id: str | None = None
    source_family: str | None = None
    source_evidence_status: str | None = None
    path_lifetime_scope: dict[str, object] | None = None
    confidence: str | None = None
    conflicts: tuple[dict[str, object], ...] = ()
    parent_evidence_ids: tuple[str, ...] = ()
    contradicted_evidence_id: str | None = None
    reason: str | None = None
    cleanup_scope: dict[str, object] | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> EntryRegisterSeedMetadata:
        entry_offset = payload["entry_offset"]
        register = payload["register"]
        kind = payload["kind"]
        note = payload["note"]
        library_name = payload["library_name"]
        struct_name = payload["struct_name"]
        context_name = payload["context_name"]
        source_evidence_id = payload.get("source_evidence_id")
        source_family = payload.get("source_family")
        source_evidence_status = payload.get("source_evidence_status")
        path_lifetime_scope = payload.get("path_lifetime_scope")
        confidence = payload.get("confidence")
        conflicts = payload.get("conflicts", [])
        parent_evidence_ids = payload.get("parent_evidence_ids", [])
        contradicted_evidence_id = payload.get("contradicted_evidence_id")
        reason = payload.get("reason")
        cleanup_scope = payload.get("cleanup_scope")
        assert entry_offset is None or isinstance(entry_offset, int)
        assert isinstance(register, str)
        assert isinstance(kind, str)
        assert isinstance(note, str)
        assert library_name is None or isinstance(library_name, str)
        assert struct_name is None or isinstance(struct_name, str)
        assert context_name is None or isinstance(context_name, str)
        assert source_evidence_id is None or isinstance(source_evidence_id, str)
        assert source_family is None or isinstance(source_family, str)
        assert source_evidence_status is None or isinstance(source_evidence_status, str)
        assert path_lifetime_scope is None or isinstance(path_lifetime_scope, dict)
        assert confidence is None or isinstance(confidence, str)
        assert isinstance(conflicts, list | tuple)
        assert all(isinstance(item, dict) for item in conflicts)
        assert isinstance(parent_evidence_ids, list | tuple)
        assert all(isinstance(item, str) for item in parent_evidence_ids)
        assert contradicted_evidence_id is None or isinstance(contradicted_evidence_id, str)
        assert reason is None or isinstance(reason, str)
        assert cleanup_scope is None or isinstance(cleanup_scope, dict)
        return cls(
            entry_offset=entry_offset,
            register=register,
            kind=_entry_register_seed_kind(kind),
            note=note,
            library_name=library_name,
            struct_name=struct_name,
            context_name=context_name,
            source_evidence_id=source_evidence_id,
            source_family=source_family,
            source_evidence_status=source_evidence_status,
            path_lifetime_scope=path_lifetime_scope,
            confidence=confidence,
            conflicts=tuple(cast(dict[str, object], item) for item in conflicts),
            parent_evidence_ids=tuple(parent_evidence_ids),
            contradicted_evidence_id=contradicted_evidence_id,
            reason=reason,
            cleanup_scope=cleanup_scope,
        )

    def __post_init__(self) -> None:
        assert isinstance(self.kind, EntryRegisterSeedKind)


@dataclass(frozen=True, slots=True)
class FunctionSummaryAbiLocationMetadata:
    kind: str
    width: int
    register: str | None = None
    offset: int | None = None
    convention: str | None = None
    registers: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> FunctionSummaryAbiLocationMetadata:
        kind = payload["kind"]
        width = payload["width"]
        assert kind in {"register", "stack", "register_tuple"}
        assert isinstance(width, int) and width > 0
        if kind == "register":
            register = payload["register"]
            assert isinstance(register, str) and len(register) == 2
            assert register[0].upper() in {"D", "A"} and register[1] in "01234567"
            assert set(payload) == {"kind", "register", "width"}
            return cls(kind=kind, register=register.upper(), width=width)
        if kind == "stack":
            offset = payload["offset"]
            convention = payload["convention"]
            assert isinstance(offset, int)
            assert convention in {"caller_argument", "caller_result", "caller_cleanup"}
            assert set(payload) == {"kind", "offset", "width", "convention"}
            return cls(kind=kind, width=width, offset=offset, convention=convention)
        registers = payload["registers"]
        assert isinstance(registers, list) and 2 <= len(registers) <= 4
        assert all(isinstance(register, str) and len(register) == 2 and register[0].upper() in {"D", "A"}
                   and register[1] in "01234567" for register in registers)
        canonical = tuple(register.upper() for register in registers)
        assert canonical == tuple(sorted(canonical, key=lambda value: (0 if value[0] == "D" else 1, value[1])))
        assert len(set(canonical)) == len(canonical)
        assert width == len(canonical) * 4
        assert set(payload) == {"kind", "registers", "width"}
        return cls(kind=kind, width=width, registers=canonical)


@dataclass(frozen=True, slots=True)
class FunctionSummaryInputMetadata:
    location: FunctionSummaryAbiLocationMetadata
    value_kind: str
    struct_name: str | None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> FunctionSummaryInputMetadata:
        location = FunctionSummaryAbiLocationMetadata.from_dict(_json_object(payload["location"]))
        value_kind = payload["value_kind"]
        assert isinstance(value_kind, str) and value_kind in {"struct_ptr", "abi_pointer"}
        if value_kind == "struct_ptr":
            struct_name = payload["struct_name"]
            assert isinstance(struct_name, str) and struct_name
            assert set(payload) == {"location", "value_kind", "struct_name"}
            return cls(location, value_kind, struct_name)
        assert set(payload) == {"location", "value_kind"}
        return cls(location, value_kind, None)


@dataclass(frozen=True, slots=True)
class FunctionSummaryResultMetadata:
    """A reviewer-declared lossless callable result.

    Target metadata may express only an identity transform from an existing
    input. Generated platform/base/typed results are source-analysis facts,
    never copied target-facing names.
    """

    kind: str
    location: FunctionSummaryAbiLocationMetadata
    input_index: int

    @classmethod
    def from_dict(cls, payload: dict[str, object], inputs: tuple[FunctionSummaryInputMetadata, ...]) -> FunctionSummaryResultMetadata:
        kind = payload["kind"]
        location = FunctionSummaryAbiLocationMetadata.from_dict(_json_object(payload["location"]))
        input_index = payload["input_index"]
        assert kind == "identity_input"
        assert isinstance(input_index, int) and 0 <= input_index < len(inputs)
        input_location = inputs[input_index].location
        assert location.width == input_location.width
        assert len(location.registers) == len(input_location.registers)
        assert (location.kind == "stack") == (input_location.kind == "stack")
        assert set(payload) == {"kind", "location", "input_index"}
        return cls(kind=kind, location=location, input_index=input_index)


@dataclass(frozen=True, slots=True)
class FunctionSummaryEffectsMetadata:
    """The persisted callable-effect boundary.

    B3 currently permits only an explicitly tagged unknown partition.  The
    tag is intentional: later explicit register, memory, and escape members
    extend this one object, rather than reviving independent string fields.
    """

    schema_version: int
    registers_state: str
    memory_state: str
    escapes_state: str
    register_locations: tuple[tuple[FunctionSummaryAbiLocationMetadata, str], ...] = ()
    memory_effects: tuple[tuple[str, tuple[object, ...]], ...] = ()
    escapes: tuple[tuple[str, FunctionSummaryAbiLocationMetadata, tuple[object, ...]], ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, object], inputs: tuple[FunctionSummaryInputMetadata, ...],
                  results: tuple[FunctionSummaryResultMetadata, ...]) -> FunctionSummaryEffectsMetadata:
        schema_version = payload["schema_version"]
        registers = _json_object(payload["registers"])
        memory = _json_object(payload["memory"])
        escapes = _json_object(payload["escapes"])
        registers_state = registers["state"]
        memory_state = memory["state"]
        escapes_state = escapes["state"]
        assert schema_version == 1
        assert set(payload) == {"schema_version", "registers", "memory", "escapes"}
        assert registers_state in {"unknown", "explicit", "invalid", "overflow"}
        assert memory_state in {"unknown", "explicit", "invalid", "overflow"}
        assert escapes_state in {"unknown", "explicit", "invalid", "overflow"}
        register_locations: list[tuple[FunctionSummaryAbiLocationMetadata, str]] = []
        if registers_state == "explicit":
            locations = registers["locations"]
            assert isinstance(locations, list)
            assert set(registers) == {"state", "locations"}
            for item in locations:
                item_object = _json_object(item)
                location = FunctionSummaryAbiLocationMetadata.from_dict(_json_object(item_object["location"]))
                effect = item_object["effect"]
                assert effect in {"preserved", "clobbered"}
                # The partition describes individual caller-visible registers
                # and stack ABI slots.  A register tuple remains a value ABI
                # identity and cannot be a duplicate partition spelling.
                assert location.kind in {"register", "stack"}
                assert set(item_object) == {"location", "effect"}
                register_locations.append((location, effect))
            identities = [item[0] for item in register_locations]
            assert len(set(identities)) == len(identities)
            required = {("register", register, 4) for register in (*[f"D{i}" for i in range(8)], *[f"A{i}" for i in range(8)])}
            observed = {(location.kind, location.register, location.width) for location, _ in register_locations
                        if location.kind == "register"}
            assert required <= observed
            for input_item in inputs:
                if input_item.location.kind == "stack":
                    assert any(location == input_item.location for location, _ in register_locations)
        else:
            assert set(registers) == {"state"}
        def subject(value: object) -> tuple[object, ...]:
            item = _json_object(value)
            kind = item["kind"]
            if kind == "input":
                index = item["input_index"]
                assert isinstance(index, int) and 0 <= index < len(inputs) and set(item) == {"kind", "input_index"}
                return (kind, index)
            if kind == "static_storage":
                section = item["section_index"]; offset = item["offset"]
                assert isinstance(section, int) and section >= 0 and isinstance(offset, int) and offset >= 0
                assert set(item) == {"kind", "section_index", "offset"}
                return (kind, section, offset)
            if kind == "stack":
                offset = item["offset"]; convention = item["convention"]
                assert isinstance(offset, int) and offset >= 0
                assert convention in {"caller_argument", "caller_result", "caller_cleanup"}
                assert set(item) == {"kind", "offset", "convention"}
                return (kind, offset, convention)
            region = item["region_id"]
            assert kind == "abstract_region" and isinstance(region, str) and region and set(item) == {"kind", "region_id"}
            return (kind, region)
        memory_effects: list[tuple[str, tuple[object, ...]]] = []
        if memory_state == "explicit":
            effects = memory["effects"]
            assert isinstance(effects, list) and set(memory) == {"state", "effects"}
            for item in effects:
                item_object = _json_object(item); kind = item_object["kind"]
                assert kind in {"read", "write", "nonaliasing_read", "nonaliasing_write"} and set(item_object) == {"kind", "subject"}
                memory_effects.append((kind, subject(item_object["subject"])))
            assert len(set(memory_effects)) == len(memory_effects)
        else:
            assert set(memory) == {"state"}
        escape_records: list[tuple[str, FunctionSummaryAbiLocationMetadata, tuple[object, ...]]] = []
        if escapes_state == "explicit":
            items = escapes["escapes"]
            assert isinstance(items, list) and set(escapes) == {"state", "escapes"}
            allowed_inputs = {item.location for item in inputs}
            allowed_results = {item.location for item in results}
            for item in items:
                item_object = _json_object(item); location = FunctionSummaryAbiLocationMetadata.from_dict(_json_object(item_object["source_location"]))
                source_kind = item_object["source_kind"]
                assert source_kind in {"input", "result"}
                assert location in (allowed_inputs if source_kind == "input" else allowed_results)
                assert set(item_object) == {"source_kind", "source_location", "sink_subject"}
                escape_records.append((source_kind, location, subject(item_object["sink_subject"])))
            assert len(set(escape_records)) == len(escape_records)
        else:
            assert set(escapes) == {"state"}
        return cls(
            schema_version=schema_version,
            registers_state=registers_state,
            memory_state=memory_state,
            escapes_state=escapes_state,
            register_locations=tuple(register_locations),
            memory_effects=tuple(memory_effects),
            escapes=tuple(escape_records),
        )


@dataclass(frozen=True, slots=True)
class FunctionSummaryMetadata:
    function_summary_id: str
    hunk: int
    callable_kind: str
    inputs: tuple[FunctionSummaryInputMetadata, ...]
    results: tuple[FunctionSummaryResultMetadata, ...]
    effects: FunctionSummaryEffectsMetadata
    note: str
    context_name: str | None = None
    entry_offset: int | None = None
    table_offset: int | None = None
    entry_count: int | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> FunctionSummaryMetadata:
        function_summary_id = payload["function_summary_id"]
        hunk = payload["hunk"]
        callable_kind = payload["callable_kind"]
        inputs = payload["inputs"]
        results = payload["results"]
        note = payload["note"]
        context_name = payload.get("context_name")
        entry_offset = payload.get("entry_offset")
        table_offset = payload.get("table_offset")
        entry_count = payload.get("entry_count")
        assert isinstance(function_summary_id, str) and function_summary_id
        assert isinstance(hunk, int) and hunk >= 0
        assert callable_kind in {"direct", "callback_table"}
        assert isinstance(note, str)
        assert context_name is None or isinstance(context_name, str)
        allowed_keys = {"function_summary_id", "hunk", "callable_kind", "inputs", "results", "effects", "note",
                        "context_name", "entry_offset", "table_offset", "entry_count"}
        assert set(payload) <= allowed_keys
        parsed_inputs = tuple(
            FunctionSummaryInputMetadata.from_dict(_json_object(item))
            for item in _json_list(inputs)
        )
        assert parsed_inputs
        assert len({item.location for item in parsed_inputs}) == len(parsed_inputs)
        parsed_results = tuple(
            FunctionSummaryResultMetadata.from_dict(_json_object(item), parsed_inputs)
            for item in _json_list(results)
        )
        assert len({item.location for item in parsed_results}) == len(parsed_results)
        effects = FunctionSummaryEffectsMetadata.from_dict(_json_object(payload["effects"]), parsed_inputs, parsed_results)
        if callable_kind == "direct":
            assert isinstance(entry_offset, int) and entry_offset >= 0
            assert table_offset is None and entry_count is None
        else:
            assert entry_offset is None
            assert isinstance(table_offset, int) and table_offset >= 0
            assert isinstance(entry_count, int) and entry_count > 0
        return cls(
            function_summary_id=function_summary_id,
            hunk=hunk,
            callable_kind=callable_kind,
            inputs=parsed_inputs,
            results=parsed_results,
            effects=effects,
            note=note,
            context_name=context_name,
            entry_offset=entry_offset,
            table_offset=table_offset,
            entry_count=entry_count,
        )


@dataclass(frozen=True, slots=True)
class AbstractRegionMetadata:
    """A named, non-overlapping source range usable by callable effects."""

    region_id: str
    section_index: int
    start_offset: int
    size: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> AbstractRegionMetadata:
        region_id = payload["region_id"]
        section_index = payload["section_index"]
        start_offset = payload["start_offset"]
        size = payload["size"]
        assert isinstance(region_id, str) and region_id
        assert isinstance(section_index, int) and section_index >= 0
        assert isinstance(start_offset, int) and start_offset >= 0
        assert isinstance(size, int) and size > 0
        assert start_offset + size <= 0x1_0000_0000
        assert set(payload) == {"region_id", "section_index", "start_offset", "size"}
        return cls(region_id, section_index, start_offset, size)

@dataclass(frozen=True, slots=True)
class ResidentTargetMetadata:
    offset: int
    matchword: int
    flags: int
    version: int
    node_type_name: str
    priority: int
    name: str | None
    id_string: str | None
    init_offset: int
    auto_init: bool
    autoinit: ResidentAutoinitMetadata | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ResidentTargetMetadata:
        offset = payload["offset"]
        matchword = payload["matchword"]
        flags = payload["flags"]
        version = payload["version"]
        node_type_name = payload["node_type_name"]
        priority = payload["priority"]
        name = payload["name"]
        id_string = payload["id_string"]
        init_offset = payload["init_offset"]
        auto_init = payload["auto_init"]
        autoinit = payload["autoinit"]
        assert isinstance(offset, int)
        assert isinstance(matchword, int)
        assert isinstance(flags, int)
        assert isinstance(version, int)
        assert isinstance(node_type_name, str)
        assert isinstance(priority, int)
        assert name is None or isinstance(name, str)
        assert id_string is None or isinstance(id_string, str)
        assert isinstance(init_offset, int)
        assert isinstance(auto_init, bool)
        return cls(
            offset=offset,
            matchword=matchword,
            flags=flags,
            version=version,
            node_type_name=node_type_name,
            priority=priority,
            name=name,
            id_string=id_string,
            init_offset=init_offset,
            auto_init=auto_init,
            autoinit=None if autoinit is None else ResidentAutoinitMetadata.from_dict(_json_object(autoinit)),
        )

@dataclass(frozen=True, slots=True)
class LibraryTargetMetadata:
    library_name: str
    id_string: str | None
    version: int
    public_function_count: int | None
    total_lvo_count: int | None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> LibraryTargetMetadata:
        library_name = payload["library_name"]
        id_string = payload["id_string"]
        version = payload["version"]
        public_function_count = payload["public_function_count"]
        total_lvo_count = payload["total_lvo_count"]
        assert isinstance(library_name, str)
        assert id_string is None or isinstance(id_string, str)
        assert isinstance(version, int)
        assert public_function_count is None or isinstance(public_function_count, int)
        assert total_lvo_count is None or isinstance(total_lvo_count, int)
        return cls(
            library_name=library_name,
            id_string=id_string,
            version=version,
            public_function_count=public_function_count,
            total_lvo_count=total_lvo_count,
        )

@dataclass(frozen=True, slots=True)
class CustomStructFieldMetadata:
    name: str
    type: str
    offset: int
    size: int
    available_since: str = "1.0"
    struct: str | None = None
    pointer_struct: str | None = None
    named_base: str | None = None
    value_kind: str = "scalar"

    def __post_init__(self) -> None:
        if self.value_kind not in {"scalar", "target_pointer", "struct_pointer"}:
            raise ValueError(f"unsupported custom struct field value_kind: {self.value_kind}")
        if self.pointer_struct is not None:
            if self.value_kind != "struct_pointer":
                raise ValueError("pointer_struct requires value_kind struct_pointer")
        elif self.value_kind == "struct_pointer":
            raise ValueError("struct_pointer fields require pointer_struct")

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> CustomStructFieldMetadata:
        name = payload["name"]
        field_type = payload["type"]
        offset = payload["offset"]
        size = payload["size"]
        available_since = payload["available_since"]
        struct_name = payload["struct"]
        pointer_struct = payload["pointer_struct"]
        named_base = payload.get("named_base")
        value_kind = payload.get("value_kind")
        assert isinstance(name, str)
        assert isinstance(field_type, str)
        assert isinstance(offset, int)
        assert isinstance(size, int)
        assert isinstance(available_since, str)
        assert struct_name is None or isinstance(struct_name, str)
        assert pointer_struct is None or isinstance(pointer_struct, str)
        assert named_base is None or isinstance(named_base, str)
        assert value_kind is None or isinstance(value_kind, str)
        if pointer_struct is not None:
            if value_kind not in (None, "struct_pointer"):
                raise ValueError("pointer_struct requires value_kind struct_pointer")
            value_kind = "struct_pointer"
        elif value_kind is None:
            value_kind = "scalar"
        if value_kind not in {"scalar", "target_pointer", "struct_pointer"}:
            raise ValueError(f"unsupported custom struct field value_kind: {value_kind}")
        if value_kind == "struct_pointer":
            raise ValueError("struct_pointer fields require pointer_struct")
        return cls(
            name=name,
            type=field_type,
            offset=offset,
            size=size,
            available_since=available_since,
            struct=struct_name,
            pointer_struct=pointer_struct,
            named_base=named_base,
            value_kind=value_kind,
        )

@dataclass(frozen=True, slots=True, kw_only=True)
class CustomStructMetadata:
    name: str
    size: int
    fields: tuple[CustomStructFieldMetadata, ...]
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    source: str = "target_metadata"
    base_offset: int = 0
    base_struct: str | None = None
    available_since: str = "1.0"

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> CustomStructMetadata:
        name = payload["name"]
        size = payload["size"]
        fields = payload["fields"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        source = payload["source"]
        base_offset = payload["base_offset"]
        base_struct = payload["base_struct"]
        available_since = payload["available_since"]
        assert isinstance(name, str)
        assert isinstance(size, int)
        seed_origin = _target_metadata_seed_origin(seed_origin)
        review_status = _target_metadata_review_status(review_status)
        assert isinstance(citation, str)
        assert isinstance(source, str)
        assert isinstance(base_offset, int)
        assert base_struct is None or isinstance(base_struct, str)
        assert isinstance(available_since, str)
        return cls(
            name=name,
            size=size,
            fields=tuple(
                CustomStructFieldMetadata.from_dict(_json_object(field))
                for field in _json_list(fields)
            ),
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            source=source,
            base_offset=base_offset,
            base_struct=base_struct,
            available_since=available_since,
        )

@dataclass(frozen=True, slots=True, kw_only=True)
class RssetLayoutRegionMetadata:
    offset: int
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    size: int | None = None
    layout_name: str | None = None
    base_symbol: str | None = None
    sizeof_symbol: str | None = None
    symbol: str | None = None
    struct_name: str | None = None
    pointer_struct: str | None = None
    storage_kind: RssetLayoutStorageKind | None = None
    semantic_type: str | None = None
    parser_role: str | None = None
    parser_routine: str | None = None
    parse_order: int | None = None

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)
        assert self.storage_kind is None or isinstance(self.storage_kind, RssetLayoutStorageKind)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> RssetLayoutRegionMetadata:
        offset = payload["offset"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        size = payload.get("size")
        layout_name = payload.get("layout_name")
        base_symbol = payload.get("base_symbol")
        sizeof_symbol = payload.get("sizeof_symbol")
        symbol = payload["symbol"]
        struct_name = payload["struct_name"]
        pointer_struct = payload["pointer_struct"]
        storage_kind = payload.get("storage_kind")
        semantic_type = payload.get("semantic_type")
        parser_role = payload.get("parser_role")
        parser_routine = payload.get("parser_routine")
        parse_order = payload.get("parse_order")
        assert isinstance(offset, int)
        seed_origin = _target_metadata_seed_origin(seed_origin)
        review_status = _target_metadata_review_status(review_status)
        assert isinstance(citation, str)
        assert size is None or (isinstance(size, int) and 0 < size <= 255)
        assert layout_name is None or isinstance(layout_name, str)
        assert base_symbol is None or isinstance(base_symbol, str)
        assert sizeof_symbol is None or isinstance(sizeof_symbol, str)
        assert symbol is None or isinstance(symbol, str)
        assert struct_name is None or isinstance(struct_name, str)
        assert pointer_struct is None or isinstance(pointer_struct, str)
        assert storage_kind is None or isinstance(storage_kind, str)
        assert semantic_type is None or isinstance(semantic_type, str)
        assert parser_role is None or isinstance(parser_role, str)
        assert parser_routine is None or isinstance(parser_routine, str)
        assert parse_order is None or isinstance(parse_order, int)
        return cls(
            offset=offset,
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            size=size,
            layout_name=layout_name,
            base_symbol=base_symbol,
            sizeof_symbol=sizeof_symbol,
            symbol=symbol,
            struct_name=struct_name,
            pointer_struct=pointer_struct,
            storage_kind=None if storage_kind is None else _rsset_layout_storage_kind(storage_kind),
            semantic_type=semantic_type,
            parser_role=parser_role,
            parser_routine=parser_routine,
            parse_order=parse_order,
        )

@dataclass(frozen=True, slots=True)
class RssetUseSiteBindingMetadata:
    hunk: int
    addr: int
    operand_index: int
    base_register: str
    displacement: int
    layout_name: str
    base_symbol: str
    base_evidence_id: str
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    binding_id: str | None = None
    access: str | None = None
    width_bytes: int | None = None
    owner_action_id: str | None = None
    source_evidence_id: str | None = None
    source_family: str | None = None
    source_evidence_status: str | None = None
    path_lifetime_scope: dict[str, object] | None = None
    confidence: str | None = None
    base_evidence_refs: tuple[dict[str, object], ...] = ()

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> RssetUseSiteBindingMetadata:
        hunk = payload["hunk"]
        addr = payload["addr"]
        operand_index = payload["operand_index"]
        base_register = payload["base_register"]
        displacement = payload["displacement"]
        layout_name = payload["layout_name"]
        base_symbol = payload["base_symbol"]
        base_evidence_id = payload["base_evidence_id"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        binding_id = payload.get("binding_id")
        access = payload.get("access")
        width_bytes = payload.get("width_bytes")
        owner_action_id = payload.get("owner_action_id")
        source_evidence_id = payload.get("source_evidence_id")
        source_family = payload.get("source_family")
        source_evidence_status = payload.get("source_evidence_status")
        path_lifetime_scope = payload.get("path_lifetime_scope")
        confidence = payload.get("confidence")
        base_evidence_refs = payload.get("base_evidence_refs", [])
        assert isinstance(hunk, int)
        assert isinstance(addr, int)
        assert isinstance(operand_index, int)
        assert isinstance(base_register, str)
        assert isinstance(displacement, int)
        assert isinstance(layout_name, str)
        assert isinstance(base_symbol, str)
        assert isinstance(base_evidence_id, str)
        seed_origin = _target_metadata_seed_origin(seed_origin)
        review_status = _target_metadata_review_status(review_status)
        assert isinstance(citation, str)
        assert binding_id is None or isinstance(binding_id, str)
        assert access is None or isinstance(access, str)
        assert width_bytes is None or isinstance(width_bytes, int)
        assert owner_action_id is None or isinstance(owner_action_id, str)
        assert source_evidence_id is None or isinstance(source_evidence_id, str)
        assert source_family is None or isinstance(source_family, str)
        assert source_evidence_status is None or isinstance(source_evidence_status, str)
        assert path_lifetime_scope is None or isinstance(path_lifetime_scope, dict)
        assert confidence is None or isinstance(confidence, str)
        assert isinstance(base_evidence_refs, list | tuple)
        return cls(
            hunk=hunk,
            addr=addr,
            operand_index=operand_index,
            base_register=base_register,
            displacement=displacement,
            layout_name=layout_name,
            base_symbol=base_symbol,
            base_evidence_id=base_evidence_id,
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            binding_id=binding_id,
            access=access,
            width_bytes=width_bytes,
            owner_action_id=owner_action_id,
            source_evidence_id=source_evidence_id,
            source_family=source_family,
            source_evidence_status=source_evidence_status,
            path_lifetime_scope=path_lifetime_scope,
            confidence=confidence,
            base_evidence_refs=tuple(cast(dict[str, object], ref) for ref in base_evidence_refs if isinstance(ref, dict)),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class AbsoluteStorageSlotMetadata:
    address: int
    symbol: str
    storage_kind: RssetLayoutStorageKind
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    size: int = 4
    pointer_struct: str | None = None
    semantic_type: str | None = None

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)
        assert 0 <= self.address <= 0xFFFFFFFF
        assert self.symbol
        assert 0 < self.size <= 255
        assert self.storage_kind in {
            RssetLayoutStorageKind.POINTER,
            RssetLayoutStorageKind.STRUCT_POINTER,
            RssetLayoutStorageKind.POINTER_TABLE,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> AbsoluteStorageSlotMetadata:
        address = payload["address"]
        symbol = payload["symbol"]
        storage_kind = payload["storage_kind"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        size = payload.get("size", 4)
        pointer_struct = payload.get("pointer_struct")
        semantic_type = payload.get("semantic_type")
        assert isinstance(address, int)
        assert isinstance(symbol, str)
        assert isinstance(storage_kind, str)
        assert isinstance(seed_origin, str)
        assert isinstance(review_status, str)
        assert isinstance(citation, str)
        assert isinstance(size, int)
        assert pointer_struct is None or isinstance(pointer_struct, str)
        assert semantic_type is None or isinstance(semantic_type, str)
        return cls(
            address=address,
            symbol=symbol,
            storage_kind=_rsset_layout_storage_kind(storage_kind),
            seed_origin=_target_metadata_seed_origin(seed_origin),
            review_status=_target_metadata_review_status(review_status),
            citation=citation,
            size=size,
            pointer_struct=pointer_struct,
            semantic_type=semantic_type,
        )

@dataclass(frozen=True, slots=True)
class SeededEntityMetadata:
    addr: int
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    source_id: str | None = None
    source_path: str | None = None
    source_locator: str | None = None
    end: int | None = None
    hunk: int = 0
    name: str | None = None
    comment: str | None = None
    type: str | None = None
    subtype: str | None = None
    unit: str | None = None
    encoding: str | None = None
    struct_name: str | None = None
    field_name: str | None = None
    field_type: str | None = None
    c_type: str | None = None
    pointer_struct: str | None = None
    value_kind: str | None = None
    value_domain: str | None = None
    owner_action_id: str | None = None
    source_evidence_id: str | None = None
    parent_evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SeededEntityMetadata:
        addr = payload["addr"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        source_id = payload.get("source_id")
        source_path = payload.get("source_path")
        source_locator = payload.get("source_locator")
        end = payload.get("end")
        hunk = payload.get("hunk", 0)
        name = payload.get("name")
        comment = payload.get("comment")
        entity_type = payload.get("type")
        subtype = payload.get("subtype")
        unit = payload.get("unit")
        encoding = payload.get("encoding")
        struct_name = payload.get("struct_name")
        field_name = payload.get("field_name")
        field_type = payload.get("field_type")
        c_type = payload.get("c_type")
        pointer_struct = payload.get("pointer_struct")
        value_kind = payload.get("value_kind")
        value_domain = payload.get("value_domain")
        owner_action_id = payload.get("owner_action_id")
        source_evidence_id = payload.get("source_evidence_id")
        parent_evidence_ids = payload.get("parent_evidence_ids", [])
        assert isinstance(addr, int)
        seed_origin = _target_metadata_seed_origin(seed_origin)
        review_status = _target_metadata_review_status(review_status)
        assert isinstance(citation, str)
        assert source_id is None or isinstance(source_id, str)
        assert source_path is None or isinstance(source_path, str)
        assert source_locator is None or isinstance(source_locator, str)
        assert end is None or isinstance(end, int)
        assert isinstance(hunk, int)
        assert name is None or isinstance(name, str)
        assert comment is None or isinstance(comment, str)
        assert entity_type is None or isinstance(entity_type, str)
        assert subtype is None or isinstance(subtype, str)
        assert unit is None or isinstance(unit, str)
        assert encoding is None or isinstance(encoding, str)
        assert struct_name is None or isinstance(struct_name, str)
        assert field_name is None or isinstance(field_name, str)
        assert field_type is None or isinstance(field_type, str)
        assert c_type is None or isinstance(c_type, str)
        assert pointer_struct is None or isinstance(pointer_struct, str)
        assert value_kind is None or value_kind in {"scalar", "target_pointer", "struct_pointer"}
        assert value_domain is None or isinstance(value_domain, str)
        assert owner_action_id is None or isinstance(owner_action_id, str)
        assert source_evidence_id is None or isinstance(source_evidence_id, str)
        assert isinstance(parent_evidence_ids, list | tuple)
        assert all(isinstance(item, str) for item in parent_evidence_ids)
        return cls(
            addr=addr,
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            source_id=source_id,
            source_path=source_path,
            source_locator=source_locator,
            end=end,
            hunk=hunk,
            name=name,
            comment=comment,
            type=entity_type,
            subtype=subtype,
            unit=unit,
            encoding=encoding,
            struct_name=struct_name,
            field_name=field_name,
            field_type=field_type,
            c_type=c_type,
            pointer_struct=pointer_struct,
            value_kind=value_kind,
            value_domain=value_domain,
            owner_action_id=owner_action_id,
            source_evidence_id=source_evidence_id,
            parent_evidence_ids=tuple(parent_evidence_ids),
        )

@dataclass(frozen=True, slots=True)
class SeededCodeLabelMetadata:
    addr: int
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    name: str
    source_id: str | None = None
    source_path: str | None = None
    source_locator: str | None = None
    hunk: int = 0
    comment: str | None = None

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SeededCodeLabelMetadata:
        addr = payload["addr"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        name = payload["name"]
        source_id = payload.get("source_id")
        source_path = payload.get("source_path")
        source_locator = payload.get("source_locator")
        hunk = payload.get("hunk", 0)
        comment = payload.get("comment")
        assert isinstance(addr, int)
        seed_origin = _target_metadata_seed_origin(seed_origin)
        review_status = _target_metadata_review_status(review_status)
        assert isinstance(citation, str)
        assert isinstance(name, str)
        assert source_id is None or isinstance(source_id, str)
        assert source_path is None or isinstance(source_path, str)
        assert source_locator is None or isinstance(source_locator, str)
        assert isinstance(hunk, int)
        assert comment is None or isinstance(comment, str)
        return cls(
            addr=addr,
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            name=name,
            source_id=source_id,
            source_path=source_path,
            source_locator=source_locator,
            hunk=hunk,
            comment=comment,
        )

@dataclass(frozen=True, slots=True)
class SeededCodeEntrypointMetadata:
    addr: int
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    name: str
    source_id: str | None = None
    source_path: str | None = None
    source_locator: str | None = None
    hunk: int = 0
    comment: str | None = None
    role: str | None = None

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SeededCodeEntrypointMetadata:
        addr = payload["addr"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        name = payload["name"]
        source_id = payload.get("source_id")
        source_path = payload.get("source_path")
        source_locator = payload.get("source_locator")
        hunk = payload.get("hunk", 0)
        comment = payload.get("comment")
        role = payload.get("role")
        assert isinstance(addr, int)
        seed_origin = _target_metadata_seed_origin(seed_origin)
        review_status = _target_metadata_review_status(review_status)
        assert isinstance(citation, str)
        assert isinstance(name, str)
        assert source_id is None or isinstance(source_id, str)
        assert source_path is None or isinstance(source_path, str)
        assert source_locator is None or isinstance(source_locator, str)
        assert isinstance(hunk, int)
        assert comment is None or isinstance(comment, str)
        assert role is None or isinstance(role, str)
        return cls(
            addr=addr,
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            name=name,
            source_id=source_id,
            source_path=source_path,
            source_locator=source_locator,
            hunk=hunk,
            comment=comment,
            role=role,
        )

@dataclass(frozen=True, slots=True)
class AbsoluteCodeLabelMetadata:
    addr: int
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    name: str
    comment: str | None = None

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> AbsoluteCodeLabelMetadata:
        addr = payload["addr"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        name = payload["name"]
        comment = payload.get("comment")
        assert isinstance(addr, int)
        seed_origin = _target_metadata_seed_origin(seed_origin)
        review_status = _target_metadata_review_status(review_status)
        assert isinstance(citation, str)
        assert isinstance(name, str)
        assert comment is None or isinstance(comment, str)
        return cls(
            addr=addr,
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            name=name,
            comment=comment,
        )


@dataclass(frozen=True, slots=True)
class EntryCommentMetadata:
    addr: int
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    comment: str
    source_id: str | None = None
    source_path: str | None = None
    source_locator: str | None = None
    hunk: int = 0

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> EntryCommentMetadata:
        addr = payload["addr"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        comment = payload["comment"]
        source_id = payload.get("source_id")
        source_path = payload.get("source_path")
        source_locator = payload.get("source_locator")
        hunk = payload.get("hunk", 0)
        assert isinstance(addr, int)
        seed_origin = _target_metadata_seed_origin(seed_origin)
        review_status = _target_metadata_review_status(review_status)
        assert isinstance(citation, str)
        assert isinstance(comment, str)
        assert source_id is None or isinstance(source_id, str)
        assert source_path is None or isinstance(source_path, str)
        assert source_locator is None or isinstance(source_locator, str)
        assert isinstance(hunk, int)
        return cls(
            addr=addr,
            hunk=hunk,
            comment=comment,
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            source_id=source_id,
            source_path=source_path,
            source_locator=source_locator,
        )


@dataclass(frozen=True, slots=True)
class ManualRepresentationMetadata:
    addr: int
    style: ManualRepresentationStyle
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    end: int | None = None
    hunk: int = 0
    element_kind: str | None = None
    operand_index: int | None = None
    symbol: str | None = None
    source_id: str | None = None
    source_path: str | None = None
    source_locator: str | None = None

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)
        assert isinstance(self.style, ManualRepresentationStyle)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ManualRepresentationMetadata:
        addr = payload["addr"]
        style = payload["style"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        end = payload.get("end")
        hunk = payload.get("hunk", 0)
        element_kind = payload.get("element_kind")
        operand_index = payload.get("operand_index")
        symbol = payload.get("symbol")
        source_id = payload.get("source_id")
        source_path = payload.get("source_path")
        source_locator = payload.get("source_locator")
        assert isinstance(addr, int)
        assert end is None or isinstance(end, int)
        assert isinstance(hunk, int)
        assert isinstance(citation, str)
        assert element_kind is None or isinstance(element_kind, str)
        assert operand_index is None or isinstance(operand_index, int)
        assert symbol is None or isinstance(symbol, str)
        assert source_id is None or isinstance(source_id, str)
        assert source_path is None or isinstance(source_path, str)
        assert source_locator is None or isinstance(source_locator, str)
        return cls(
            addr=addr,
            end=end,
            hunk=hunk,
            style=_manual_representation_style(style),
            element_kind=element_kind,
            operand_index=operand_index,
            symbol=symbol,
            seed_origin=_target_metadata_seed_origin(seed_origin),
            review_status=_target_metadata_review_status(review_status),
            citation=citation,
            source_id=source_id,
            source_path=source_path,
            source_locator=source_locator,
        )


@dataclass(frozen=True, slots=True)
class TargetEquateMetadata:
    name: str
    value: int
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    comment: str | None = None
    value_representation: ManualRepresentationStyle | None = None
    value_expression: str | None = None

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)
        if self.value_representation is not None:
            assert isinstance(self.value_representation, ManualRepresentationStyle)
        if self.value_expression is not None:
            assert isinstance(self.value_expression, str)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> TargetEquateMetadata:
        name = payload["name"]
        value = payload["value"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        comment = payload.get("comment")
        value_representation = payload.get("value_representation")
        value_expression = payload.get("value_expression")
        assert isinstance(name, str)
        assert isinstance(value, int)
        assert isinstance(citation, str)
        assert comment is None or isinstance(comment, str)
        assert value_representation is None or isinstance(value_representation, str)
        assert value_expression is None or isinstance(value_expression, str)
        return cls(
            name=name,
            value=value,
            seed_origin=_target_metadata_seed_origin(seed_origin),
            review_status=_target_metadata_review_status(review_status),
            citation=citation,
            comment=comment,
            value_representation=None
            if value_representation is None
            else _manual_representation_style(value_representation),
            value_expression=value_expression,
        )


def validate_base_displacement_reference(ref: Mapping[str, object], *, source_hunk: int | None = None, source_addr: int | None = None) -> None:
    """Validate the bounded signed-word, unscaled, same-section reference form."""
    def integer(value: object) -> TypeGuard[int]:
        return isinstance(value, int) and not isinstance(value, bool)

    width = ref.get("width", ref.get("size"))
    source_value = ref.get("source_value")
    base = ref.get("base_locator")
    if not isinstance(base, Mapping):
        raise ValueError("base_displacement requires explicit base_locator")
    base_hunk, base_offset = base.get("hunk"), base.get("offset")
    target_hunk, target_offset = ref.get("target_hunk"), ref.get("target_offset")
    scale = ref.get("scale", 1)
    if not integer(width) or width != 2 or ref.get("signed") is not True or not integer(scale) or scale != 1:
        raise ValueError("base_displacement supports only signed 16-bit width 2 and scale 1")
    if not integer(source_value) or not 0 <= source_value <= 0xFFFF:
        raise ValueError("base_displacement source_value must be unsigned encoded 16-bit bits")
    if any(not integer(value) or not 0 <= value <= 0xFFFFFFFF for value in (base_hunk, base_offset, target_hunk, target_offset)):
        raise ValueError("base_displacement requires unsigned 32-bit base and target locators")
    if source_hunk is not None and (not integer(source_hunk) or not 0 <= source_hunk <= 0xFFFFFFFF):
        raise ValueError("base_displacement source section must be unsigned 32-bit")
    if base_hunk != target_hunk or (source_hunk is not None and base_hunk != source_hunk):
        raise ValueError("base_displacement requires source, base and target in the same section")
    if source_addr is not None and (not integer(source_addr) or not 0 <= source_addr <= 0xFFFFFFFD):
        raise ValueError("base_displacement source word must fit a 32-bit section span")
    target_locator = ref.get("target_locator")
    if target_locator is not None and (not isinstance(target_locator, Mapping) or not integer(target_locator.get("hunk")) or not integer(target_locator.get("offset")) or target_locator.get("hunk") != target_hunk or target_locator.get("offset") != target_offset):
        raise ValueError("base_displacement target_locator must match target_hunk/target_offset")
    displacement = source_value if source_value < 0x8000 else source_value - 0x10000
    if cast(int, base_offset) + displacement != target_offset:
        raise ValueError("base_displacement target_offset must equal base offset plus signed source_value")
    if "runtime_address" in ref:
        raise ValueError("base_displacement does not accept runtime_address")


def validate_base_displacement_owner(ref: Mapping[str, object], element: Mapping[str, object]) -> None:
    """Accept only encoded word scalars or aligned entries in a word array."""
    offset, owner_offset, width = ref.get("offset"), element.get("offset"), element.get("width")
    if any(not isinstance(value, int) or isinstance(value, bool) for value in (offset, owner_offset, width)):
        raise ValueError("base_displacement requires integer owner/source spans")
    offset, owner_offset, width = cast(int, offset), cast(int, owner_offset), cast(int, width)
    scalar_word = element.get("kind") == "scalar" and width == 2 and offset == owner_offset
    array_word = (element.get("kind") == "array" and element.get("array_stride") == 2
                  and (offset - owner_offset) % 2 == 0 and width % 2 == 0)
    if not (scalar_word or array_word) or offset < owner_offset or offset + 2 > owner_offset + width:
        raise ValueError("base_displacement requires a scalar word or aligned word-array entry")


@dataclass(frozen=True, slots=True)
class ManualDataReferenceMetadata:
    addr: int
    hunk: int
    size: int
    source_value: int
    reference_kind: str
    signed: bool
    base_hunk: int
    base_offset: int
    target_hunk: int
    target_offset: int
    owner_kind: str
    owner_id: str
    owner_layout_id: str
    owner_element_offset: int
    xref_generation_mode: str
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)
        if self.reference_kind != "base_displacement":
            raise ValueError("manual_data_references supports only base_displacement")
        validate_base_displacement_reference(
            {**asdict(self), "base_locator": {"hunk": self.base_hunk, "offset": self.base_offset}},
            source_hunk=self.hunk, source_addr=self.addr,
        )
        assert isinstance(self.owner_element_offset, int) and not isinstance(self.owner_element_offset, bool)
        assert 0 <= self.owner_element_offset <= 0xFFFFFFFF
        assert self.owner_kind == "data_block_interpreted_ref"
        assert isinstance(self.owner_id, str) and self.owner_id
        assert isinstance(self.owner_layout_id, str) and self.owner_layout_id
        assert isinstance(self.citation, str)
        assert self.xref_generation_mode in {"bidirectional", "source_only", "none"}

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ManualDataReferenceMetadata:
        return cls(
            addr=cast(int, payload["addr"]), hunk=cast(int, payload["hunk"]),
            size=cast(int, payload["size"]), source_value=cast(int, payload["source_value"]),
            reference_kind=cast(str, payload["reference_kind"]), signed=cast(bool, payload["signed"]),
            base_hunk=cast(int, payload["base_hunk"]), base_offset=cast(int, payload["base_offset"]),
            target_hunk=cast(int, payload["target_hunk"]), target_offset=cast(int, payload["target_offset"]),
            owner_kind=cast(str, payload["owner_kind"]), owner_id=cast(str, payload["owner_id"]),
            owner_layout_id=cast(str, payload["owner_layout_id"]),
            owner_element_offset=cast(int, payload["owner_element_offset"]),
            xref_generation_mode=cast(str, payload["xref_generation_mode"]),
            seed_origin=_target_metadata_seed_origin(payload["seed_origin"]),
            review_status=_target_metadata_review_status(payload["review_status"]),
            citation=cast(str, payload["citation"]),
        )


@dataclass(frozen=True, slots=True)
class ManualRuntimeAddressRefMetadata:
    addr: int
    size: int
    target_hunk: int
    target_offset: int
    runtime_address: int
    confidence: int
    owner_kind: str
    owner_id: str
    owner_layout_id: str
    owner_element_offset: int
    xref_generation_mode: str
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    hunk: int = 0

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ManualRuntimeAddressRefMetadata:
        addr = payload["addr"]
        size = payload["size"]
        target_hunk = payload["target_hunk"]
        target_offset = payload["target_offset"]
        runtime_address = payload["runtime_address"]
        confidence = payload["confidence"]
        owner_kind = payload["owner_kind"]
        owner_id = payload["owner_id"]
        owner_layout_id = payload["owner_layout_id"]
        owner_element_offset = payload["owner_element_offset"]
        xref_generation_mode = payload["xref_generation_mode"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        hunk = payload.get("hunk", 0)
        assert isinstance(addr, int)
        assert isinstance(size, int)
        assert isinstance(target_hunk, int)
        assert isinstance(target_offset, int)
        assert isinstance(runtime_address, int)
        assert isinstance(confidence, int)
        assert isinstance(owner_kind, str)
        assert isinstance(owner_id, str)
        assert isinstance(owner_layout_id, str)
        assert isinstance(owner_element_offset, int)
        assert isinstance(xref_generation_mode, str)
        assert isinstance(citation, str)
        assert isinstance(hunk, int)
        return cls(
            addr=addr,
            size=size,
            target_hunk=target_hunk,
            target_offset=target_offset,
            runtime_address=runtime_address,
            confidence=confidence,
            owner_kind=owner_kind,
            owner_id=owner_id,
            owner_layout_id=owner_layout_id,
            owner_element_offset=owner_element_offset,
            xref_generation_mode=xref_generation_mode,
            seed_origin=_target_metadata_seed_origin(seed_origin),
            review_status=_target_metadata_review_status(review_status),
            citation=citation,
            hunk=hunk,
        )


@dataclass(frozen=True, slots=True)
class ExecutionViewMetadata:
    source_start: int
    source_end: int
    base_addr: int
    name: str
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    comment: str | None = None

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ExecutionViewMetadata:
        source_start = payload["source_start"]
        source_end = payload["source_end"]
        base_addr = payload["base_addr"]
        name = payload["name"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        comment = payload.get("comment")
        assert isinstance(source_start, int)
        assert isinstance(source_end, int)
        assert isinstance(base_addr, int)
        assert isinstance(name, str)
        seed_origin = _target_metadata_seed_origin(seed_origin)
        review_status = _target_metadata_review_status(review_status)
        assert isinstance(citation, str)
        assert comment is None or isinstance(comment, str)
        return cls(
            source_start=source_start,
            source_end=source_end,
            base_addr=base_addr,
            name=name,
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            comment=comment,
        )


@dataclass(frozen=True, slots=True)
class SuppressedSeededItemMetadata:
    kind: SuppressedSeededItemKind
    hunk: int
    addr: int
    end: int | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SuppressedSeededItemMetadata:
        kind = payload["kind"]
        hunk = payload["hunk"]
        addr = payload["addr"]
        end = payload.get("end")
        assert isinstance(kind, str)
        assert isinstance(hunk, int)
        assert isinstance(addr, int)
        assert end is None or isinstance(end, int)
        return cls(kind=_suppressed_seeded_item_kind(kind), hunk=hunk, addr=addr, end=end)

    def __post_init__(self) -> None:
        assert isinstance(self.kind, SuppressedSeededItemKind)


@dataclass(frozen=True, slots=True)
class DataBlockElementMetadata:
    layout_id: str
    offset: int
    width: int
    kind: DataBlockElementKind
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    name: str | None = None
    array_count: int | None = None
    array_stride: int | None = None
    representation: ManualRepresentationStyle | None = None
    type_binding: dict[str, object] | None = None
    reference_interpretation: dict[str, object] | None = None
    provenance: dict[str, object] | None = None

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)
        assert isinstance(self.kind, DataBlockElementKind)
        assert self.offset >= 0
        assert self.width > 0
        if self.array_count is not None:
            assert self.array_count > 0
        if self.array_stride is not None:
            assert self.array_stride > 0
        if self.representation is not None:
            assert isinstance(self.representation, ManualRepresentationStyle)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> DataBlockElementMetadata:
        layout_id = payload["layout_id"]
        offset = payload["offset"]
        width = payload["width"]
        kind = payload["kind"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        name = payload.get("name")
        array_count = payload.get("array_count")
        array_stride = payload.get("array_stride")
        representation = payload.get("representation")
        type_binding = payload.get("type_binding")
        reference_interpretation = payload.get("reference_interpretation")
        provenance = payload.get("provenance")
        assert isinstance(layout_id, str)
        assert isinstance(offset, int)
        assert isinstance(width, int)
        assert isinstance(kind, str)
        assert isinstance(citation, str)
        assert name is None or isinstance(name, str)
        assert array_count is None or isinstance(array_count, int)
        assert array_stride is None or isinstance(array_stride, int)
        assert representation is None or isinstance(representation, str)
        assert type_binding is None or isinstance(type_binding, dict)
        assert reference_interpretation is None or isinstance(reference_interpretation, dict)
        assert provenance is None or isinstance(provenance, dict)
        return cls(
            layout_id=layout_id,
            offset=offset,
            width=width,
            kind=_data_block_element_kind(kind),
            name=name,
            array_count=array_count,
            array_stride=array_stride,
            representation=None if representation is None else _manual_representation_style(representation),
            type_binding=cast(dict[str, object], type_binding),
            reference_interpretation=cast(dict[str, object], reference_interpretation),
            provenance=cast(dict[str, object], provenance),
            seed_origin=_target_metadata_seed_origin(seed_origin),
            review_status=_target_metadata_review_status(review_status),
            citation=citation,
        )


@dataclass(frozen=True, slots=True)
class DataBlockLayoutMetadata:
    layout_id: str
    hunk: int
    source_start: int
    source_end: int
    seed_origin: TargetMetadataSeedOrigin
    review_status: TargetMetadataReviewStatus
    citation: str
    runtime_execution_view_id: str | None = None
    runtime_start: int | None = None
    runtime_end: int | None = None
    role: str | None = None
    name: str | None = None
    default_unit: str | None = None
    version: int = 1
    provenance: dict[str, object] | None = None
    elements: tuple[DataBlockElementMetadata, ...] = ()

    def __post_init__(self) -> None:
        _assert_target_metadata_review_fields(self.seed_origin, self.review_status)
        assert self.layout_id
        assert self.hunk >= 0
        assert self.source_start >= 0
        assert self.source_end > self.source_start
        assert self.version > 0
        if self.runtime_start is not None:
            assert self.runtime_start >= 0
        if self.runtime_end is not None:
            assert self.runtime_start is not None
            assert self.runtime_end > self.runtime_start
        for element in self.elements:
            assert element.layout_id == self.layout_id
            assert element.offset + element.width <= self.source_end - self.source_start

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> DataBlockLayoutMetadata:
        layout_id = payload["layout_id"]
        hunk = payload["hunk"]
        source_start = payload["source_start"]
        source_end = payload["source_end"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        runtime_execution_view_id = payload.get("runtime_execution_view_id")
        runtime_start = payload.get("runtime_start")
        runtime_end = payload.get("runtime_end")
        role = payload.get("role")
        name = payload.get("name")
        default_unit = payload.get("default_unit")
        version = payload.get("version", 1)
        provenance = payload.get("provenance")
        elements = payload.get("elements", [])
        assert isinstance(layout_id, str)
        assert isinstance(hunk, int)
        assert isinstance(source_start, int)
        assert isinstance(source_end, int)
        assert isinstance(citation, str)
        assert runtime_execution_view_id is None or isinstance(runtime_execution_view_id, str)
        assert runtime_start is None or isinstance(runtime_start, int)
        assert runtime_end is None or isinstance(runtime_end, int)
        assert role is None or isinstance(role, str)
        assert name is None or isinstance(name, str)
        assert default_unit is None or isinstance(default_unit, str)
        assert isinstance(version, int)
        assert provenance is None or isinstance(provenance, dict)
        return cls(
            layout_id=layout_id,
            hunk=hunk,
            source_start=source_start,
            source_end=source_end,
            runtime_execution_view_id=runtime_execution_view_id,
            runtime_start=runtime_start,
            runtime_end=runtime_end,
            role=role,
            name=name,
            default_unit=default_unit,
            version=version,
            provenance=cast(dict[str, object], provenance),
            elements=tuple(
                DataBlockElementMetadata.from_dict(_json_object(element_payload))
                for element_payload in _json_list(elements)
            ),
            seed_origin=_target_metadata_seed_origin(seed_origin),
            review_status=_target_metadata_review_status(review_status),
            citation=citation,
        )

@dataclass(frozen=True, slots=True)
class TargetMetadata:
    target_type: str
    entry_register_seeds: tuple[EntryRegisterSeedMetadata, ...]
    function_summaries: tuple[FunctionSummaryMetadata, ...] = ()
    abstract_regions: tuple[AbstractRegionMetadata, ...] = ()
    bootblock: BootBlockTargetMetadata | None = None
    resident: ResidentTargetMetadata | None = None
    library: LibraryTargetMetadata | None = None
    custom_structs: tuple[CustomStructMetadata, ...] = ()
    rsset_layout_regions: tuple[RssetLayoutRegionMetadata, ...] = ()
    absolute_storage_slots: tuple[AbsoluteStorageSlotMetadata, ...] = ()
    rsset_use_site_bindings: tuple[RssetUseSiteBindingMetadata, ...] = ()
    seeded_entities: tuple[SeededEntityMetadata, ...] = ()
    seeded_code_labels: tuple[SeededCodeLabelMetadata, ...] = ()
    seeded_code_entrypoints: tuple[SeededCodeEntrypointMetadata, ...] = ()
    absolute_code_labels: tuple[AbsoluteCodeLabelMetadata, ...] = ()
    entry_comments: tuple[EntryCommentMetadata, ...] = ()
    manual_representations: tuple[ManualRepresentationMetadata, ...] = ()
    target_equates: tuple[TargetEquateMetadata, ...] = ()
    manual_runtime_address_refs: tuple[ManualRuntimeAddressRefMetadata, ...] = ()
    manual_data_references: tuple[ManualDataReferenceMetadata, ...] = ()
    data_block_layouts: tuple[DataBlockLayoutMetadata, ...] = ()
    execution_views: tuple[ExecutionViewMetadata, ...] = ()
    suppressed_seeded_items: tuple[SuppressedSeededItemMetadata, ...] = ()
    source_output_policy: SourceOutputPolicyMetadata = SourceOutputPolicyMetadata()

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> TargetMetadata:
        target_type = payload["target_type"]
        entry_register_seeds = payload["entry_register_seeds"]
        function_summaries = payload.get("function_summaries", [])
        abstract_regions = payload.get("abstract_regions", [])
        bootblock = payload["bootblock"]
        resident = payload["resident"]
        library = payload["library"]
        custom_structs = payload["custom_structs"]
        rsset_layout_regions = payload["rsset_layout_regions"]
        absolute_storage_slots = payload.get("absolute_storage_slots", [])
        rsset_use_site_bindings = payload.get("rsset_use_site_bindings", [])
        seeded_entities = payload.get("seeded_entities", [])
        seeded_code_labels = payload.get("seeded_code_labels", [])
        seeded_code_entrypoints = payload.get("seeded_code_entrypoints", [])
        absolute_code_labels = payload.get("absolute_code_labels", [])
        entry_comments = payload.get("entry_comments", [])
        manual_representations = payload.get("manual_representations", [])
        target_equates = payload.get("target_equates", [])
        manual_runtime_address_refs = payload.get("manual_runtime_address_refs", [])
        data_block_layouts = payload.get("data_block_layouts", [])
        execution_views = payload.get("execution_views", [])
        suppressed_seeded_items = payload.get("suppressed_seeded_items", [])
        assert isinstance(target_type, str)
        seeds = _json_list(entry_register_seeds)
        parsed_abstract_regions = tuple(
            AbstractRegionMetadata.from_dict(_json_object(region))
            for region in _json_list(abstract_regions)
        )
        assert len(parsed_abstract_regions) <= 128
        assert len({region.region_id for region in parsed_abstract_regions}) == len(parsed_abstract_regions)
        for index, region in enumerate(parsed_abstract_regions):
            for other in parsed_abstract_regions[:index]:
                assert region.section_index != other.section_index or (
                    region.start_offset >= other.start_offset + other.size or
                    other.start_offset >= region.start_offset + region.size
                )
        return cls(
            target_type=target_type,
            source_output_policy=SourceOutputPolicyMetadata.from_dict(
                _json_object(payload.get("source_output_policy", {}))),
            entry_register_seeds=tuple(
                EntryRegisterSeedMetadata.from_dict(_json_object(seed))
                for seed in seeds
            ),
            function_summaries=tuple(
                FunctionSummaryMetadata.from_dict(_json_object(summary))
                for summary in _json_list(function_summaries)
            ),
            abstract_regions=parsed_abstract_regions,
            bootblock=None if bootblock is None else BootBlockTargetMetadata.from_dict(_json_object(bootblock)),
            resident=None if resident is None else ResidentTargetMetadata.from_dict(_json_object(resident)),
            library=None if library is None else LibraryTargetMetadata.from_dict(_json_object(library)),
            custom_structs=tuple(
                CustomStructMetadata.from_dict(_json_object(struct_payload))
                for struct_payload in _json_list(custom_structs)
            ),
            rsset_layout_regions=tuple(
                RssetLayoutRegionMetadata.from_dict(_json_object(slot_payload))
                for slot_payload in _json_list(rsset_layout_regions)
            ),
            absolute_storage_slots=tuple(
                AbsoluteStorageSlotMetadata.from_dict(_json_object(slot_payload))
                for slot_payload in _json_list(absolute_storage_slots)
            ),
            rsset_use_site_bindings=tuple(
                RssetUseSiteBindingMetadata.from_dict(_json_object(binding_payload))
                for binding_payload in _json_list(rsset_use_site_bindings)
            ),
            seeded_entities=tuple(
                SeededEntityMetadata.from_dict(_json_object(entity_payload))
                for entity_payload in _json_list(seeded_entities)
            ),
            seeded_code_labels=tuple(
                SeededCodeLabelMetadata.from_dict(_json_object(label_payload))
                for label_payload in _json_list(seeded_code_labels)
            ),
            seeded_code_entrypoints=tuple(
                SeededCodeEntrypointMetadata.from_dict(_json_object(entrypoint_payload))
                for entrypoint_payload in _json_list(seeded_code_entrypoints)
            ),
            absolute_code_labels=tuple(
                AbsoluteCodeLabelMetadata.from_dict(_json_object(label_payload))
                for label_payload in _json_list(absolute_code_labels)
            ),
            entry_comments=tuple(
                EntryCommentMetadata.from_dict(_json_object(comment_payload))
                for comment_payload in _json_list(entry_comments)
            ),
            manual_representations=tuple(
                ManualRepresentationMetadata.from_dict(_json_object(representation_payload))
                for representation_payload in _json_list(manual_representations)
            ),
            target_equates=tuple(
                TargetEquateMetadata.from_dict(_json_object(equate_payload))
                for equate_payload in _json_list(target_equates)
            ),
            manual_runtime_address_refs=tuple(
                ManualRuntimeAddressRefMetadata.from_dict(_json_object(ref_payload))
                for ref_payload in _json_list(manual_runtime_address_refs)
            ),
            manual_data_references=tuple(
                ManualDataReferenceMetadata.from_dict(_json_object(ref_payload))
                for ref_payload in _json_list(payload.get("manual_data_references", []))
            ),
            data_block_layouts=tuple(
                DataBlockLayoutMetadata.from_dict(_json_object(layout_payload))
                for layout_payload in _json_list(data_block_layouts)
            ),
            execution_views=tuple(
                ExecutionViewMetadata.from_dict(_json_object(view_payload))
                for view_payload in _json_list(execution_views)
            ),
            suppressed_seeded_items=tuple(
                SuppressedSeededItemMetadata.from_dict(_json_object(item_payload))
                for item_payload in _json_list(suppressed_seeded_items)
            ),
        )

def target_metadata_path(target_dir: Path) -> Path:
    return target_dir / TARGET_METADATA_FILE_NAME


def target_seeded_metadata_path(target_dir: Path) -> Path:
    return target_dir / TARGET_SEEDED_METADATA_FILE_NAME


def target_corrections_path(target_dir: Path) -> Path:
    return target_dir / TARGET_CORRECTIONS_FILE_NAME


def require_target_metadata(
    metadata: TargetMetadata | None,
    *,
    target_dir: Path | None,
    source_kind: BinarySourceKind,
    parent_disk_id: str | None,
) -> TargetMetadata | None:
    if source_kind is BinarySourceKind.RAW_BINARY and metadata is None:
        raise ValueError(f"Missing target_metadata.json for raw binary target: {target_dir}")
    if parent_disk_id is not None and metadata is None:
        raise ValueError(f"Missing target_metadata.json for internal target: {target_dir}")
    return metadata


def load_required_target_metadata(
    *,
    target_dir: Path | None,
    source_kind: BinarySourceKind,
    parent_disk_id: str | None,
) -> TargetMetadata | None:
    return require_target_metadata(
        None if target_dir is None else load_target_metadata(target_dir),
        target_dir=target_dir,
        source_kind=source_kind,
        parent_disk_id=parent_disk_id,
    )


def write_target_metadata(target_dir: Path, metadata: TargetMetadata) -> None:
    target_metadata_path(target_dir).write_text(
        json.dumps(target_metadata_json_payload(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_target_seeded_metadata(target_dir: Path, metadata: TargetMetadata) -> None:
    target_seeded_metadata_path(target_dir).write_text(
        json.dumps(target_metadata_json_payload(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_target_seeded_metadata(target_dir: Path) -> TargetMetadata | None:
    seeded_path = target_seeded_metadata_path(target_dir)
    if not seeded_path.exists():
        return None
    return _load_target_metadata_file(seeded_path, validate=validate_target_seeded_metadata)


def write_target_corrections_metadata(target_dir: Path, metadata: TargetMetadata) -> None:
    target_corrections_path(target_dir).write_text(
        json.dumps(target_metadata_json_payload(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _function_summary_effect_subject_payload(subject: object) -> dict[str, object]:
    """Rebuild the closed persisted subject object after dataclass export."""
    assert isinstance(subject, list | tuple) and subject
    kind = subject[0]
    if kind == "input":
        assert len(subject) == 2 and isinstance(subject[1], int)
        return {"kind": kind, "input_index": subject[1]}
    if kind == "static_storage":
        assert len(subject) == 3 and isinstance(subject[1], int) and isinstance(subject[2], int)
        return {"kind": kind, "section_index": subject[1], "offset": subject[2]}
    if kind == "stack":
        assert len(subject) == 3 and isinstance(subject[1], int) and isinstance(subject[2], str)
        return {"kind": kind, "offset": subject[1], "convention": subject[2]}
    assert kind == "abstract_region" and len(subject) == 2 and isinstance(subject[1], str)
    return {"kind": kind, "region_id": subject[1]}


def _function_summary_location_payload(location: object) -> dict[str, object]:
    assert isinstance(location, dict)
    kind = location.get("kind")
    if kind == "register":
        register = location.get("register"); width = location.get("width")
        assert isinstance(register, str) and isinstance(width, int)
        return {"kind": kind, "register": register, "width": width}
    if kind == "stack":
        offset = location.get("offset"); width = location.get("width"); convention = location.get("convention")
        assert isinstance(offset, int) and isinstance(width, int) and isinstance(convention, str)
        return {"kind": kind, "offset": offset, "width": width, "convention": convention}
    registers = location.get("registers"); width = location.get("width")
    assert kind == "register_tuple" and isinstance(registers, list) and isinstance(width, int)
    return {"kind": kind, "registers": registers, "width": width}


def target_metadata_json_payload(metadata: TargetMetadata) -> dict[str, object]:
    payload = asdict(metadata)
    if metadata.source_output_policy == SourceOutputPolicyMetadata():
        payload.pop("source_output_policy", None)
    function_summaries = payload.get("function_summaries")
    if isinstance(function_summaries, list | tuple):
        for summary in function_summaries:
            if not isinstance(summary, dict):
                continue
            for key in ("entry_offset", "table_offset", "entry_count", "context_name"):
                if summary.get(key) is None:
                    summary.pop(key, None)
            result_records = summary.get("results")
            if isinstance(result_records, list | tuple):
                for result_record in result_records:
                    if not isinstance(result_record, dict):
                        continue
                    if isinstance(result_record.get("location"), dict):
                        result_record["location"] = _function_summary_location_payload(result_record["location"])
                summary["results"] = list(result_records)
            effects = summary.get("effects")
            if isinstance(effects, dict):
                input_records = summary.get("inputs")
                if isinstance(input_records, list | tuple):
                    for input_record in input_records:
                        if not isinstance(input_record, dict):
                            continue
                        if input_record.get("struct_name") is None:
                            input_record.pop("struct_name", None)
                        if isinstance(input_record.get("location"), dict):
                            input_record["location"] = _function_summary_location_payload(input_record["location"])
                    summary["inputs"] = list(input_records)
                registers_state = effects.pop("registers_state", None)
                memory_state = effects.pop("memory_state", None)
                escapes_state = effects.pop("escapes_state", None)
                register_locations = effects.pop("register_locations", [])
                memory_effects = effects.pop("memory_effects", [])
                escape_records = effects.pop("escapes", [])
                if isinstance(registers_state, str) and isinstance(memory_state, str) and isinstance(escapes_state, str):
                    registers: dict[str, object] = {"state": registers_state}
                    if registers_state == "explicit" and isinstance(register_locations, list | tuple):
                        registers["locations"] = [
                            {"location": _function_summary_location_payload(location), "effect": effect}
                            for location, effect in register_locations
                        ]
                    memory: dict[str, object] = {"state": memory_state}
                    if memory_state == "explicit" and isinstance(memory_effects, list | tuple):
                        memory["effects"] = [
                            {"kind": kind, "subject": _function_summary_effect_subject_payload(subject)}
                            for kind, subject in memory_effects
                        ]
                    escapes: dict[str, object] = {"state": escapes_state}
                    if escapes_state == "explicit" and isinstance(escape_records, list | tuple):
                        escapes["escapes"] = [
                            {"source_kind": source_kind,
                             "source_location": _function_summary_location_payload(location),
                             "sink_subject": _function_summary_effect_subject_payload(subject)}
                            for source_kind, location, subject in escape_records
                        ]
                    effects["registers"] = registers
                    effects["memory"] = memory
                    effects["escapes"] = escapes
    bootblock = payload.get("bootblock")
    if isinstance(bootblock, dict) and bootblock.get("bootcode_has_code") is None:
        bootblock.pop("bootcode_has_code", None)
    seeded_entities = payload.get("seeded_entities")
    if isinstance(seeded_entities, list | tuple):
        for entity in seeded_entities:
            if not isinstance(entity, dict):
                continue
            if entity.get("owner_action_id") is None:
                entity.pop("owner_action_id", None)
            if entity.get("source_evidence_id") is None:
                entity.pop("source_evidence_id", None)
            if not entity.get("parent_evidence_ids"):
                entity.pop("parent_evidence_ids", None)
    entry_register_seeds = payload.get("entry_register_seeds")
    if isinstance(entry_register_seeds, list | tuple):
        for seed in entry_register_seeds:
            if not isinstance(seed, dict):
                continue
            for key in (
                "source_evidence_id",
                "source_family",
                "source_evidence_status",
                "path_lifetime_scope",
                "confidence",
                "contradicted_evidence_id",
                "reason",
                "cleanup_scope",
            ):
                if seed.get(key) is None:
                    seed.pop(key, None)
            if not seed.get("conflicts"):
                seed.pop("conflicts", None)
            if not seed.get("parent_evidence_ids"):
                seed.pop("parent_evidence_ids", None)
    return cast(dict[str, object], payload)


def _load_target_metadata_file(
    path: Path,
    *,
    validate: Callable[[TargetMetadata], TargetMetadata] | None = None,
) -> TargetMetadata:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metadata = TargetMetadata.from_dict(_json_object(payload))
        return metadata if validate is None else validate(metadata)
    except Exception as exc:
        raise ValueError(f"Bad {path.name}") from exc


def validate_target_seeded_metadata(metadata: TargetMetadata) -> TargetMetadata:
    if metadata.bootblock is not None:
        raise ValueError("target_seeded_metadata.json must not contain bootblock metadata")
    if metadata.resident is not None:
        raise ValueError("target_seeded_metadata.json must not contain resident metadata")
    if metadata.library is not None:
        raise ValueError("target_seeded_metadata.json must not contain library metadata")
    if metadata.entry_register_seeds:
        raise ValueError("target_seeded_metadata.json must not contain entry_register_seeds")
    if metadata.function_summaries:
        raise ValueError("target_seeded_metadata.json must not contain function_summaries")
    if metadata.suppressed_seeded_items:
        raise ValueError("target_seeded_metadata.json must not contain suppressed_seeded_items")
    if metadata.target_equates:
        raise ValueError("target_seeded_metadata.json must not contain target_equates")
    for entity in metadata.seeded_entities:
        if entity.source_id is None:
            raise ValueError(f"target_seeded_metadata.json entity at {entity.addr:#x} is missing source_id")
        if entity.source_path is None:
            raise ValueError(f"target_seeded_metadata.json entity at {entity.addr:#x} is missing source_path")
        if entity.source_locator is None:
            raise ValueError(f"target_seeded_metadata.json entity at {entity.addr:#x} is missing source_locator")
    for label in metadata.seeded_code_labels:
        if label.source_id is None:
            raise ValueError(f"target_seeded_metadata.json code label at {label.addr:#x} is missing source_id")
        if label.source_path is None:
            raise ValueError(f"target_seeded_metadata.json code label at {label.addr:#x} is missing source_path")
        if label.source_locator is None:
            raise ValueError(f"target_seeded_metadata.json code label at {label.addr:#x} is missing source_locator")
    for entrypoint in metadata.seeded_code_entrypoints:
        if entrypoint.source_id is None:
            raise ValueError(
                f"target_seeded_metadata.json code entrypoint at {entrypoint.addr:#x} is missing source_id"
            )
        if entrypoint.source_path is None:
            raise ValueError(
                f"target_seeded_metadata.json code entrypoint at {entrypoint.addr:#x} is missing source_path"
            )
        if entrypoint.source_locator is None:
            raise ValueError(
                f"target_seeded_metadata.json code entrypoint at {entrypoint.addr:#x} is missing source_locator"
            )
    for absolute_label in metadata.absolute_code_labels:
        if absolute_label.addr < 0:
            raise ValueError(
                f"target_seeded_metadata.json absolute code label at {absolute_label.addr:#x} is invalid"
            )
    for comment in metadata.entry_comments:
        if comment.source_id is None:
            raise ValueError(f"target_seeded_metadata.json entry comment at {comment.addr:#x} is missing source_id")
        if comment.source_path is None:
            raise ValueError(f"target_seeded_metadata.json entry comment at {comment.addr:#x} is missing source_path")
        if comment.source_locator is None:
            raise ValueError(
                f"target_seeded_metadata.json entry comment at {comment.addr:#x} is missing source_locator"
            )
    for view in metadata.execution_views:
        if view.source_start < 0 or view.source_end <= view.source_start:
            raise ValueError("target_seeded_metadata.json execution view source range is invalid")
        if view.base_addr < 0:
            raise ValueError("target_seeded_metadata.json execution view base_addr is invalid")
    return metadata


def validate_target_corrections_metadata(metadata: TargetMetadata) -> TargetMetadata:
    if metadata.bootblock is not None:
        raise ValueError("target_corrections.json must not contain bootblock metadata")
    if metadata.resident is not None:
        raise ValueError("target_corrections.json must not contain resident metadata")
    if metadata.library is not None:
        raise ValueError("target_corrections.json must not contain library metadata")
    if metadata.entry_register_seeds:
        raise ValueError("target_corrections.json must not contain entry_register_seeds")
    if metadata.function_summaries:
        raise ValueError("target_corrections.json must not contain function_summaries")
    if metadata.custom_structs:
        raise ValueError("target_corrections.json must not contain custom_structs")
    if metadata.rsset_layout_regions:
        raise ValueError("target_corrections.json must not contain rsset_layout_regions")
    if metadata.target_equates:
        raise ValueError("target_corrections.json must not contain target_equates")
    return metadata


def apply_suppressed_seeded_items(
    seeded: TargetMetadata,
    suppressed_seeded_items: tuple[SuppressedSeededItemMetadata, ...],
) -> TargetMetadata:
    if not suppressed_seeded_items:
        return seeded
    suppressed = set(suppressed_seeded_items)
    return TargetMetadata(
        target_type=seeded.target_type,
        source_output_policy=seeded.source_output_policy,
        entry_register_seeds=seeded.entry_register_seeds,
        function_summaries=seeded.function_summaries,
        bootblock=seeded.bootblock,
        resident=seeded.resident,
        library=seeded.library,
        custom_structs=seeded.custom_structs,
        rsset_layout_regions=seeded.rsset_layout_regions,
        absolute_storage_slots=seeded.absolute_storage_slots,
        seeded_entities=tuple(
            entity
            for entity in seeded.seeded_entities
            if not _seeded_entity_is_suppressed(entity, suppressed)
        ),
        seeded_code_labels=tuple(
            label
            for label in seeded.seeded_code_labels
            if not _seeded_item_is_suppressed(SuppressedSeededItemKind.SEEDED_CODE_LABEL, label.hunk, label.addr, suppressed)
        ),
        seeded_code_entrypoints=tuple(
            entrypoint
            for entrypoint in seeded.seeded_code_entrypoints
            if not _seeded_item_is_suppressed(
                SuppressedSeededItemKind.SEEDED_CODE_ENTRYPOINT,
                entrypoint.hunk,
                entrypoint.addr,
                suppressed,
            )
        ),
        entry_comments=seeded.entry_comments,
        manual_representations=seeded.manual_representations,
        target_equates=seeded.target_equates,
        manual_runtime_address_refs=seeded.manual_runtime_address_refs,
        manual_data_references=seeded.manual_data_references,
        data_block_layouts=seeded.data_block_layouts,
        execution_views=seeded.execution_views,
        suppressed_seeded_items=(),
    )


def _seeded_entity_is_suppressed(
    entity: SeededEntityMetadata,
    suppressed: set[SuppressedSeededItemMetadata],
) -> bool:
    exact = SuppressedSeededItemMetadata(SuppressedSeededItemKind.SEEDED_ENTITY, entity.hunk, entity.addr, entity.end)
    broad = SuppressedSeededItemMetadata(SuppressedSeededItemKind.SEEDED_ENTITY, entity.hunk, entity.addr)
    return exact in suppressed or broad in suppressed


def _seeded_item_is_suppressed(
    kind: SuppressedSeededItemKind,
    hunk: int,
    addr: int,
    suppressed: set[SuppressedSeededItemMetadata],
) -> bool:
    return SuppressedSeededItemMetadata(kind, hunk, addr) in suppressed


def _merge_optional_field[T](manual: T | None, seeded: T | None, *, what: str) -> T | None:
    if manual is None:
        return seeded
    if seeded is None:
        return manual
    if manual != seeded:
        raise ValueError(f"Conflicting {what} between target metadata and seeded target metadata")
    return manual


def _merge_unique_by_key[T](
    manual: tuple[T, ...],
    seeded: tuple[T, ...],
    *,
    key: Callable[[T], object],
    what: str,
) -> tuple[T, ...]:
    merged: list[T] = []
    seen: set[object] = set()
    for item in (*manual, *seeded):
        item_key = key(item)
        if item_key in seen:
            raise ValueError(f"Duplicate {what} in merged target metadata: {item_key!r}")
        seen.add(item_key)
        merged.append(item)
    return tuple(merged)


def _merge_seeded_entity(manual: SeededEntityMetadata, seeded: SeededEntityMetadata) -> SeededEntityMetadata:
    if manual.end is not None and seeded.end is not None and manual.end != seeded.end:
        raise ValueError(f"Conflicting seeded entity end for {(manual.hunk, manual.addr)!r}")
    if manual.type is not None and seeded.type is not None and manual.type != seeded.type:
        raise ValueError(f"Conflicting seeded entity type for {(manual.hunk, manual.addr)!r}")
    if manual.subtype is not None and seeded.subtype is not None and manual.subtype != seeded.subtype:
        raise ValueError(f"Conflicting seeded entity subtype for {(manual.hunk, manual.addr)!r}")
    if manual.unit is not None and seeded.unit is not None and manual.unit != seeded.unit:
        raise ValueError(f"Conflicting seeded entity unit for {(manual.hunk, manual.addr)!r}")
    if manual.encoding is not None and seeded.encoding is not None and manual.encoding != seeded.encoding:
        raise ValueError(f"Conflicting seeded entity encoding for {(manual.hunk, manual.addr)!r}")
    return SeededEntityMetadata(
        addr=manual.addr,
        hunk=manual.hunk,
        end=manual.end if manual.end is not None else seeded.end,
        name=manual.name if manual.name is not None else seeded.name,
        comment=manual.comment if manual.comment is not None else seeded.comment,
        type=manual.type if manual.type is not None else seeded.type,
        subtype=manual.subtype if manual.subtype is not None else seeded.subtype,
        unit=manual.unit if manual.unit is not None else seeded.unit,
        encoding=manual.encoding if manual.encoding is not None else seeded.encoding,
        seed_origin=manual.seed_origin,
        review_status=manual.review_status,
        citation=manual.citation,
        source_id=manual.source_id if manual.source_id is not None else seeded.source_id,
        source_path=manual.source_path if manual.source_path is not None else seeded.source_path,
        source_locator=manual.source_locator if manual.source_locator is not None else seeded.source_locator,
        struct_name=manual.struct_name if manual.struct_name is not None else seeded.struct_name,
        field_name=manual.field_name if manual.field_name is not None else seeded.field_name,
        field_type=manual.field_type if manual.field_type is not None else seeded.field_type,
        c_type=manual.c_type if manual.c_type is not None else seeded.c_type,
        pointer_struct=manual.pointer_struct if manual.pointer_struct is not None else seeded.pointer_struct,
        value_kind=manual.value_kind if manual.value_kind is not None else seeded.value_kind,
        value_domain=manual.value_domain if manual.value_domain is not None else seeded.value_domain,
        owner_action_id=manual.owner_action_id if manual.owner_action_id is not None else seeded.owner_action_id,
        source_evidence_id=manual.source_evidence_id
        if manual.source_evidence_id is not None
        else seeded.source_evidence_id,
        parent_evidence_ids=manual.parent_evidence_ids or seeded.parent_evidence_ids,
    )


def _seeded_entity_merge_key(entity: SeededEntityMetadata) -> tuple[int, int, int | None, str | None]:
    return (entity.hunk, entity.addr, entity.end, entity.type)


def _seeded_entity_merge_sort_key(key: tuple[int, int, int | None, str | None]) -> tuple[int, int, int, str]:
    hunk, addr, end, entity_type = key
    return (hunk, addr, -1 if end is None else end, entity_type or "")


def _merge_seeded_entities(
    manual: tuple[SeededEntityMetadata, ...],
    seeded: tuple[SeededEntityMetadata, ...],
) -> tuple[SeededEntityMetadata, ...]:
    merged: dict[tuple[int, int, int | None, str | None], SeededEntityMetadata] = {
        _seeded_entity_merge_key(entity): entity for entity in seeded
    }
    for entity in manual:
        key = _seeded_entity_merge_key(entity)
        if key in merged:
            merged[key] = _merge_seeded_entity(entity, merged[key])
        else:
            merged[key] = entity
    return tuple(merged[key] for key in sorted(merged, key=_seeded_entity_merge_sort_key))


def _merge_seeded_code_labels(
    manual: tuple[SeededCodeLabelMetadata, ...],
    seeded: tuple[SeededCodeLabelMetadata, ...],
) -> tuple[SeededCodeLabelMetadata, ...]:
    merged: dict[tuple[int, int], SeededCodeLabelMetadata] = {
        (label.hunk, label.addr): label for label in seeded
    }
    for label in manual:
        key = (label.hunk, label.addr)
        if key not in merged:
            merged[key] = label
            continue
        seeded_label = merged[key]
        merged[key] = SeededCodeLabelMetadata(
            addr=label.addr,
            hunk=label.hunk,
            name=label.name,
            comment=label.comment if label.comment is not None else seeded_label.comment,
            seed_origin=label.seed_origin,
            review_status=label.review_status,
            citation=label.citation,
            source_id=label.source_id if label.source_id is not None else seeded_label.source_id,
            source_path=label.source_path if label.source_path is not None else seeded_label.source_path,
            source_locator=label.source_locator if label.source_locator is not None else seeded_label.source_locator,
        )
    return tuple(merged[key] for key in sorted(merged))


def _merge_seeded_code_entrypoints(
    manual: tuple[SeededCodeEntrypointMetadata, ...],
    seeded: tuple[SeededCodeEntrypointMetadata, ...],
) -> tuple[SeededCodeEntrypointMetadata, ...]:
    merged: dict[tuple[int, int], SeededCodeEntrypointMetadata] = {
        (entrypoint.hunk, entrypoint.addr): entrypoint for entrypoint in seeded
    }
    for entrypoint in manual:
        key = (entrypoint.hunk, entrypoint.addr)
        if key not in merged:
            merged[key] = entrypoint
            continue
        seeded_entrypoint = merged[key]
        merged[key] = SeededCodeEntrypointMetadata(
            addr=entrypoint.addr,
            hunk=entrypoint.hunk,
            name=entrypoint.name,
            comment=entrypoint.comment if entrypoint.comment is not None else seeded_entrypoint.comment,
            role=entrypoint.role if entrypoint.role is not None else seeded_entrypoint.role,
            seed_origin=entrypoint.seed_origin,
            review_status=entrypoint.review_status,
            citation=entrypoint.citation,
            source_id=entrypoint.source_id if entrypoint.source_id is not None else seeded_entrypoint.source_id,
            source_path=entrypoint.source_path if entrypoint.source_path is not None else seeded_entrypoint.source_path,
            source_locator=(
                entrypoint.source_locator if entrypoint.source_locator is not None else seeded_entrypoint.source_locator
            ),
        )
    return tuple(merged[key] for key in sorted(merged))


def _merge_absolute_code_labels(
    manual: tuple[AbsoluteCodeLabelMetadata, ...],
    seeded: tuple[AbsoluteCodeLabelMetadata, ...],
) -> tuple[AbsoluteCodeLabelMetadata, ...]:
    merged: dict[int, AbsoluteCodeLabelMetadata] = {label.addr: label for label in seeded}
    for label in manual:
        existing = merged.get(label.addr)
        if existing is None:
            merged[label.addr] = label
            continue
        merged[label.addr] = AbsoluteCodeLabelMetadata(
            addr=label.addr,
            name=label.name,
            comment=label.comment if label.comment is not None else existing.comment,
            seed_origin=label.seed_origin,
            review_status=label.review_status,
            citation=label.citation,
        )
    return tuple(merged[key] for key in sorted(merged))


def _merge_entry_comments(
    manual: tuple[EntryCommentMetadata, ...],
    seeded: tuple[EntryCommentMetadata, ...],
) -> tuple[EntryCommentMetadata, ...]:
    merged: dict[tuple[int, int, str], EntryCommentMetadata] = {
        (comment.hunk, comment.addr, comment.comment): comment for comment in seeded
    }
    for comment in manual:
        merged[(comment.hunk, comment.addr, comment.comment)] = comment
    return tuple(merged[key] for key in sorted(merged))


def _merge_manual_representations(
    manual: tuple[ManualRepresentationMetadata, ...],
    seeded: tuple[ManualRepresentationMetadata, ...],
) -> tuple[ManualRepresentationMetadata, ...]:
    merged: dict[tuple[int, int, int | None, str | None, int | None], ManualRepresentationMetadata] = {
        (
            representation.hunk,
            representation.addr,
            representation.end,
            representation.element_kind,
            representation.operand_index,
        ): representation
        for representation in seeded
    }
    for representation in manual:
        key = (
            representation.hunk,
            representation.addr,
            representation.end,
            representation.element_kind,
            representation.operand_index,
        )
        existing = merged.get(key)
        if existing is not None and existing.style != representation.style:
            raise ValueError(f"Conflicting manual representation style for {(representation.hunk, representation.addr)!r}")
        merged[key] = representation
    return tuple(merged[key] for key in sorted(merged))


def _merge_target_equates(
    manual: tuple[TargetEquateMetadata, ...],
    seeded: tuple[TargetEquateMetadata, ...],
) -> tuple[TargetEquateMetadata, ...]:
    merged: dict[str, TargetEquateMetadata] = {equate.name: equate for equate in seeded}
    for equate in manual:
        merged[equate.name] = equate
    return tuple(merged[key] for key in sorted(merged))


def _merge_execution_views(
    manual: tuple[ExecutionViewMetadata, ...],
    seeded: tuple[ExecutionViewMetadata, ...],
) -> tuple[ExecutionViewMetadata, ...]:
    merged: dict[tuple[int, int, int], ExecutionViewMetadata] = {
        (view.source_start, view.source_end, view.base_addr): view for view in seeded
    }
    for view in manual:
        merged[(view.source_start, view.source_end, view.base_addr)] = view
    return tuple(merged[key] for key in sorted(merged))


def _merge_data_block_layouts(
    manual: tuple[DataBlockLayoutMetadata, ...],
    seeded: tuple[DataBlockLayoutMetadata, ...],
) -> tuple[DataBlockLayoutMetadata, ...]:
    merged: dict[str, DataBlockLayoutMetadata] = {layout.layout_id: layout for layout in seeded}
    for layout in manual:
        merged[layout.layout_id] = layout
    return tuple(merged[key] for key in sorted(merged))


def merge_target_metadata(manual: TargetMetadata, seeded: TargetMetadata) -> TargetMetadata:
    if manual.target_type != seeded.target_type:
        raise ValueError("Conflicting target_type between target metadata and seeded target metadata")
    if seeded.entry_register_seeds:
        raise ValueError("Conflicting entry_register_seeds between target metadata and seeded target metadata")
    if seeded.function_summaries:
        raise ValueError("Conflicting function_summaries between target metadata and seeded target metadata")
    seeded = apply_suppressed_seeded_items(seeded, manual.suppressed_seeded_items)
    return TargetMetadata(
        target_type=manual.target_type,
        source_output_policy=manual.source_output_policy,
        entry_register_seeds=manual.entry_register_seeds,
        function_summaries=manual.function_summaries,
        bootblock=_merge_optional_field(manual.bootblock, seeded.bootblock, what="bootblock metadata"),
        resident=_merge_optional_field(manual.resident, seeded.resident, what="resident metadata"),
        library=_merge_optional_field(manual.library, seeded.library, what="library metadata"),
        custom_structs=_merge_unique_by_key(
            manual.custom_structs,
            seeded.custom_structs,
            key=lambda struct: struct.name,
            what="custom struct",
        ),
        rsset_layout_regions=_merge_unique_by_key(
            manual.rsset_layout_regions,
            seeded.rsset_layout_regions,
            key=lambda region: (region.layout_name or "app", region.base_symbol or "__amiga_app_base__", region.offset),
            what="RSSET layout region",
        ),
        absolute_storage_slots=_merge_unique_by_key(
            manual.absolute_storage_slots,
            seeded.absolute_storage_slots,
            key=lambda slot: slot.address,
            what="absolute storage slot",
        ),
        seeded_entities=_merge_seeded_entities(manual.seeded_entities, seeded.seeded_entities),
        seeded_code_labels=_merge_seeded_code_labels(manual.seeded_code_labels, seeded.seeded_code_labels),
        seeded_code_entrypoints=_merge_seeded_code_entrypoints(
            manual.seeded_code_entrypoints,
            seeded.seeded_code_entrypoints,
        ),
        absolute_code_labels=_merge_absolute_code_labels(
            manual.absolute_code_labels,
            seeded.absolute_code_labels,
        ),
        entry_comments=_merge_entry_comments(manual.entry_comments, seeded.entry_comments),
        manual_representations=_merge_manual_representations(
            manual.manual_representations,
            seeded.manual_representations,
        ),
        target_equates=_merge_target_equates(manual.target_equates, seeded.target_equates),
        manual_runtime_address_refs=_merge_unique_by_key(
            manual.manual_runtime_address_refs, seeded.manual_runtime_address_refs,
            key=lambda ref: (ref.owner_kind, ref.owner_id, ref.hunk, ref.addr),
            what="manual runtime address reference",
        ),
        manual_data_references=_merge_unique_by_key(
            manual.manual_data_references, seeded.manual_data_references,
            key=lambda ref: (ref.owner_kind, ref.owner_id, ref.hunk, ref.addr),
            what="manual data reference",
        ),
        data_block_layouts=_merge_data_block_layouts(
            manual.data_block_layouts,
            seeded.data_block_layouts,
        ),
        execution_views=_merge_execution_views(
            manual.execution_views,
            seeded.execution_views,
        ),
        suppressed_seeded_items=manual.suppressed_seeded_items,
    )


def load_target_metadata(target_dir: Path) -> TargetMetadata | None:
    manual_path = target_metadata_path(target_dir)
    seeded_path = target_seeded_metadata_path(target_dir)
    corrections_path = target_corrections_path(target_dir)
    manual = None
    seeded = None
    corrections = None
    if manual_path.exists():
        manual = _load_target_metadata_file(manual_path)
    if seeded_path.exists():
        seeded = _load_target_metadata_file(seeded_path, validate=validate_target_seeded_metadata)
    if corrections_path.exists():
        corrections = _load_target_metadata_file(corrections_path, validate=validate_target_corrections_metadata)
    merged = manual
    if merged is None:
        merged = seeded
    elif seeded is not None:
        merged = merge_target_metadata(merged, seeded)
    if merged is None:
        return corrections
    if corrections is None:
        return merged
    return merge_target_metadata(corrections, merged)
