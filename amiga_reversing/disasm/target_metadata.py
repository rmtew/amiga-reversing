from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from .amiga_metadata import ResidentAutoinitMetadata

TARGET_METADATA_FILE_NAME = "target_metadata.json"
TARGET_SEEDED_METADATA_FILE_NAME = "target_seeded_metadata.json"
TARGET_CORRECTIONS_FILE_NAME = "target_corrections.json"
TARGET_METADATA_SEED_ORIGIN_VALUES = frozenset({
    "manual_analysis",
    "primary_doc",
    "include",
    "autodoc",
})
TARGET_METADATA_REVIEW_STATUS_VALUES = frozenset({
    "seeded",
    "validated",
})
APP_SLOT_STORAGE_KIND_VALUES = frozenset({
    "struct_instance",
    "struct_pointer",
    "pointer",
    "scalar",
})


def _json_object(value: object, *, what: str = "JSON value") -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _json_list(value: object, *, what: str = "JSON value") -> list[object]:
    assert isinstance(value, list)
    return value


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
            load_address=load_address,
            entrypoint=entrypoint,
        )

@dataclass(frozen=True, slots=True)
class EntryRegisterSeedMetadata:
    entry_offset: int | None
    register: str
    kind: str
    note: str
    library_name: str | None = None
    struct_name: str | None = None
    context_name: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> EntryRegisterSeedMetadata:
        entry_offset = payload["entry_offset"]
        register = payload["register"]
        kind = payload["kind"]
        note = payload["note"]
        library_name = payload["library_name"]
        struct_name = payload["struct_name"]
        context_name = payload["context_name"]
        assert entry_offset is None or isinstance(entry_offset, int)
        assert isinstance(register, str)
        assert isinstance(kind, str)
        assert isinstance(note, str)
        assert library_name is None or isinstance(library_name, str)
        assert struct_name is None or isinstance(struct_name, str)
        assert context_name is None or isinstance(context_name, str)
        return cls(
            entry_offset=entry_offset,
            register=register,
            kind=kind,
            note=note,
            library_name=library_name,
            struct_name=struct_name,
            context_name=context_name,
        )

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
        assert isinstance(name, str)
        assert isinstance(field_type, str)
        assert isinstance(offset, int)
        assert isinstance(size, int)
        assert isinstance(available_since, str)
        assert struct_name is None or isinstance(struct_name, str)
        assert pointer_struct is None or isinstance(pointer_struct, str)
        assert named_base is None or isinstance(named_base, str)
        return cls(
            name=name,
            type=field_type,
            offset=offset,
            size=size,
            available_since=available_since,
            struct=struct_name,
            pointer_struct=pointer_struct,
            named_base=named_base,
        )

@dataclass(frozen=True, slots=True, kw_only=True)
class CustomStructMetadata:
    name: str
    size: int
    fields: tuple[CustomStructFieldMetadata, ...]
    seed_origin: str
    review_status: str
    citation: str
    source: str = "target_metadata"
    base_offset: int = 0
    base_struct: str | None = None
    available_since: str = "1.0"

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
        assert isinstance(seed_origin, str)
        assert seed_origin in TARGET_METADATA_SEED_ORIGIN_VALUES
        assert isinstance(review_status, str)
        assert review_status in TARGET_METADATA_REVIEW_STATUS_VALUES
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
class AppSlotRegionMetadata:
    offset: int
    seed_origin: str
    review_status: str
    citation: str
    layout_name: str | None = None
    base_symbol: str | None = None
    sizeof_symbol: str | None = None
    symbol: str | None = None
    struct_name: str | None = None
    pointer_struct: str | None = None
    storage_kind: str | None = None
    semantic_type: str | None = None
    parser_role: str | None = None
    parser_routine: str | None = None
    parse_order: int | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> AppSlotRegionMetadata:
        offset = payload["offset"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
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
        assert isinstance(seed_origin, str)
        assert seed_origin in TARGET_METADATA_SEED_ORIGIN_VALUES
        assert isinstance(review_status, str)
        assert review_status in TARGET_METADATA_REVIEW_STATUS_VALUES
        assert isinstance(citation, str)
        assert layout_name is None or isinstance(layout_name, str)
        assert base_symbol is None or isinstance(base_symbol, str)
        assert sizeof_symbol is None or isinstance(sizeof_symbol, str)
        assert symbol is None or isinstance(symbol, str)
        assert struct_name is None or isinstance(struct_name, str)
        assert pointer_struct is None or isinstance(pointer_struct, str)
        assert storage_kind is None or (
            isinstance(storage_kind, str) and storage_kind in APP_SLOT_STORAGE_KIND_VALUES
        )
        assert semantic_type is None or isinstance(semantic_type, str)
        assert parser_role is None or isinstance(parser_role, str)
        assert parser_routine is None or isinstance(parser_routine, str)
        assert parse_order is None or isinstance(parse_order, int)
        return cls(
            offset=offset,
            seed_origin=seed_origin,
            review_status=review_status,
            citation=citation,
            layout_name=layout_name,
            base_symbol=base_symbol,
            sizeof_symbol=sizeof_symbol,
            symbol=symbol,
            struct_name=struct_name,
            pointer_struct=pointer_struct,
            storage_kind=storage_kind,
            semantic_type=semantic_type,
            parser_role=parser_role,
            parser_routine=parser_routine,
            parse_order=parse_order,
        )

@dataclass(frozen=True, slots=True)
class SeededEntityMetadata:
    addr: int
    seed_origin: str
    review_status: str
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
        assert isinstance(addr, int)
        assert isinstance(seed_origin, str)
        assert seed_origin in TARGET_METADATA_SEED_ORIGIN_VALUES
        assert isinstance(review_status, str)
        assert review_status in TARGET_METADATA_REVIEW_STATUS_VALUES
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
        )

@dataclass(frozen=True, slots=True)
class SeededCodeLabelMetadata:
    addr: int
    seed_origin: str
    review_status: str
    citation: str
    name: str
    source_id: str | None = None
    source_path: str | None = None
    source_locator: str | None = None
    hunk: int = 0
    comment: str | None = None

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
        assert isinstance(seed_origin, str)
        assert seed_origin in TARGET_METADATA_SEED_ORIGIN_VALUES
        assert isinstance(review_status, str)
        assert review_status in TARGET_METADATA_REVIEW_STATUS_VALUES
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
    seed_origin: str
    review_status: str
    citation: str
    name: str
    source_id: str | None = None
    source_path: str | None = None
    source_locator: str | None = None
    hunk: int = 0
    comment: str | None = None
    role: str | None = None

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
        assert isinstance(seed_origin, str)
        assert seed_origin in TARGET_METADATA_SEED_ORIGIN_VALUES
        assert isinstance(review_status, str)
        assert review_status in TARGET_METADATA_REVIEW_STATUS_VALUES
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
    seed_origin: str
    review_status: str
    citation: str
    name: str
    comment: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> AbsoluteCodeLabelMetadata:
        addr = payload["addr"]
        seed_origin = payload["seed_origin"]
        review_status = payload["review_status"]
        citation = payload["citation"]
        name = payload["name"]
        comment = payload.get("comment")
        assert isinstance(addr, int)
        assert isinstance(seed_origin, str)
        assert seed_origin in TARGET_METADATA_SEED_ORIGIN_VALUES
        assert isinstance(review_status, str)
        assert review_status in TARGET_METADATA_REVIEW_STATUS_VALUES
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
class ExecutionViewMetadata:
    source_start: int
    source_end: int
    base_addr: int
    name: str
    seed_origin: str
    review_status: str
    citation: str
    comment: str | None = None

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
        assert isinstance(seed_origin, str)
        assert seed_origin in TARGET_METADATA_SEED_ORIGIN_VALUES
        assert isinstance(review_status, str)
        assert review_status in TARGET_METADATA_REVIEW_STATUS_VALUES
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
    kind: str
    hunk: int
    addr: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SuppressedSeededItemMetadata:
        kind = payload["kind"]
        hunk = payload["hunk"]
        addr = payload["addr"]
        assert isinstance(kind, str)
        assert kind in {"seeded_entity", "seeded_code_label", "seeded_code_entrypoint"}
        assert isinstance(hunk, int)
        assert isinstance(addr, int)
        return cls(kind=kind, hunk=hunk, addr=addr)

@dataclass(frozen=True, slots=True)
class TargetMetadata:
    target_type: str
    entry_register_seeds: tuple[EntryRegisterSeedMetadata, ...]
    bootblock: BootBlockTargetMetadata | None = None
    resident: ResidentTargetMetadata | None = None
    library: LibraryTargetMetadata | None = None
    custom_structs: tuple[CustomStructMetadata, ...] = ()
    app_slot_regions: tuple[AppSlotRegionMetadata, ...] = ()
    seeded_entities: tuple[SeededEntityMetadata, ...] = ()
    seeded_code_labels: tuple[SeededCodeLabelMetadata, ...] = ()
    seeded_code_entrypoints: tuple[SeededCodeEntrypointMetadata, ...] = ()
    absolute_code_labels: tuple[AbsoluteCodeLabelMetadata, ...] = ()
    execution_views: tuple[ExecutionViewMetadata, ...] = ()
    suppressed_seeded_items: tuple[SuppressedSeededItemMetadata, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> TargetMetadata:
        target_type = payload["target_type"]
        entry_register_seeds = payload["entry_register_seeds"]
        bootblock = payload["bootblock"]
        resident = payload["resident"]
        library = payload["library"]
        custom_structs = payload["custom_structs"]
        app_slot_regions = payload["app_slot_regions"]
        seeded_entities = payload.get("seeded_entities", [])
        seeded_code_labels = payload.get("seeded_code_labels", [])
        seeded_code_entrypoints = payload.get("seeded_code_entrypoints", [])
        absolute_code_labels = payload.get("absolute_code_labels", [])
        execution_views = payload.get("execution_views", [])
        suppressed_seeded_items = payload.get("suppressed_seeded_items", [])
        assert isinstance(target_type, str)
        seeds = _json_list(entry_register_seeds)
        return cls(
            target_type=target_type,
            entry_register_seeds=tuple(
                EntryRegisterSeedMetadata.from_dict(_json_object(seed))
                for seed in seeds
            ),
            bootblock=None if bootblock is None else BootBlockTargetMetadata.from_dict(_json_object(bootblock)),
            resident=None if resident is None else ResidentTargetMetadata.from_dict(_json_object(resident)),
            library=None if library is None else LibraryTargetMetadata.from_dict(_json_object(library)),
            custom_structs=tuple(
                CustomStructMetadata.from_dict(_json_object(struct_payload))
                for struct_payload in _json_list(custom_structs)
            ),
            app_slot_regions=tuple(
                AppSlotRegionMetadata.from_dict(_json_object(slot_payload))
                for slot_payload in _json_list(app_slot_regions)
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
    source_kind: str,
    parent_disk_id: str | None,
) -> TargetMetadata | None:
    if source_kind == "raw_binary" and metadata is None:
        raise ValueError(f"Missing target_metadata.json for raw binary target: {target_dir}")
    if parent_disk_id is not None and metadata is None:
        raise ValueError(f"Missing target_metadata.json for internal target: {target_dir}")
    return metadata


def load_required_target_metadata(
    *,
    target_dir: Path | None,
    source_kind: str,
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
        json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_target_seeded_metadata(target_dir: Path, metadata: TargetMetadata) -> None:
    target_seeded_metadata_path(target_dir).write_text(
        json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_target_corrections_metadata(target_dir: Path, metadata: TargetMetadata) -> None:
    target_corrections_path(target_dir).write_text(
        json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    if metadata.suppressed_seeded_items:
        raise ValueError("target_seeded_metadata.json must not contain suppressed_seeded_items")
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
    if metadata.custom_structs:
        raise ValueError("target_corrections.json must not contain custom_structs")
    if metadata.app_slot_regions:
        raise ValueError("target_corrections.json must not contain app_slot_regions")
    return metadata


def _apply_suppressed_seeded_items(
    seeded: TargetMetadata,
    suppressed_seeded_items: tuple[SuppressedSeededItemMetadata, ...],
) -> TargetMetadata:
    if not suppressed_seeded_items:
        return seeded
    suppressed = {(item.kind, item.hunk, item.addr) for item in suppressed_seeded_items}
    return TargetMetadata(
        target_type=seeded.target_type,
        entry_register_seeds=seeded.entry_register_seeds,
        bootblock=seeded.bootblock,
        resident=seeded.resident,
        library=seeded.library,
        custom_structs=seeded.custom_structs,
        app_slot_regions=seeded.app_slot_regions,
        seeded_entities=tuple(
            entity
            for entity in seeded.seeded_entities
            if ("seeded_entity", entity.hunk, entity.addr) not in suppressed
        ),
        seeded_code_labels=tuple(
            label
            for label in seeded.seeded_code_labels
            if ("seeded_code_label", label.hunk, label.addr) not in suppressed
        ),
        seeded_code_entrypoints=tuple(
            entrypoint
            for entrypoint in seeded.seeded_code_entrypoints
            if ("seeded_code_entrypoint", entrypoint.hunk, entrypoint.addr) not in suppressed
        ),
        suppressed_seeded_items=(),
    )


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
    return SeededEntityMetadata(
        addr=manual.addr,
        hunk=manual.hunk,
        end=manual.end if manual.end is not None else seeded.end,
        name=manual.name if manual.name is not None else seeded.name,
        comment=manual.comment if manual.comment is not None else seeded.comment,
        type=manual.type if manual.type is not None else seeded.type,
        subtype=manual.subtype if manual.subtype is not None else seeded.subtype,
        seed_origin=manual.seed_origin,
        review_status=manual.review_status,
        citation=manual.citation,
        source_id=manual.source_id if manual.source_id is not None else seeded.source_id,
        source_path=manual.source_path if manual.source_path is not None else seeded.source_path,
        source_locator=manual.source_locator if manual.source_locator is not None else seeded.source_locator,
    )


def _merge_seeded_entities(
    manual: tuple[SeededEntityMetadata, ...],
    seeded: tuple[SeededEntityMetadata, ...],
) -> tuple[SeededEntityMetadata, ...]:
    merged: dict[tuple[int, int], SeededEntityMetadata] = {
        (entity.hunk, entity.addr): entity for entity in seeded
    }
    for entity in manual:
        key = (entity.hunk, entity.addr)
        if key in merged:
            merged[key] = _merge_seeded_entity(entity, merged[key])
        else:
            merged[key] = entity
    return tuple(merged[key] for key in sorted(merged))


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


def merge_target_metadata(manual: TargetMetadata, seeded: TargetMetadata) -> TargetMetadata:
    if manual.target_type != seeded.target_type:
        raise ValueError("Conflicting target_type between target metadata and seeded target metadata")
    if seeded.entry_register_seeds:
        raise ValueError("Conflicting entry_register_seeds between target metadata and seeded target metadata")
    seeded = _apply_suppressed_seeded_items(seeded, manual.suppressed_seeded_items)
    return TargetMetadata(
        target_type=manual.target_type,
        entry_register_seeds=manual.entry_register_seeds,
        bootblock=_merge_optional_field(manual.bootblock, seeded.bootblock, what="bootblock metadata"),
        resident=_merge_optional_field(manual.resident, seeded.resident, what="resident metadata"),
        library=_merge_optional_field(manual.library, seeded.library, what="library metadata"),
        custom_structs=_merge_unique_by_key(
            manual.custom_structs,
            seeded.custom_structs,
            key=lambda struct: struct.name,
            what="custom struct",
        ),
        app_slot_regions=_merge_unique_by_key(
            manual.app_slot_regions,
            seeded.app_slot_regions,
            key=lambda region: (region.layout_name or "app", region.base_symbol or "__amiga_app_base__", region.offset),
            what="app slot region",
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
