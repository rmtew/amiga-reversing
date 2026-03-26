from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from disasm.amiga_metadata import ResidentAutoinitMetadata
from m68k_kb import runtime_os

TARGET_METADATA_FILE_NAME = "target_metadata.json"


def _json_object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _json_list(value: object) -> list[object]:
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

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        assert isinstance(result, dict)
        return result


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

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        assert isinstance(result, dict)
        return result


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

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        assert isinstance(result, dict)
        return result


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

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        assert isinstance(result, dict)
        return result


@dataclass(frozen=True, slots=True)
class TargetMetadata:
    target_type: str
    entry_register_seeds: tuple[EntryRegisterSeedMetadata, ...]
    bootblock: BootBlockTargetMetadata | None = None
    resident: ResidentTargetMetadata | None = None
    library: LibraryTargetMetadata | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> TargetMetadata:
        target_type = payload["target_type"]
        entry_register_seeds = payload["entry_register_seeds"]
        bootblock = payload["bootblock"]
        resident = payload["resident"]
        library = payload["library"]
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
        )

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        assert isinstance(result, dict)
        return result


@dataclass(frozen=True, slots=True)
class StructuredFieldSpec:
    offset: int
    label: str
    size: int | None = None
    is_string: bool = False
    pointer: bool = False


@dataclass(frozen=True, slots=True)
class StructuredRegionSpec:
    start: int
    end: int
    subtype: str
    struct_name: str | None = None
    fields: tuple[StructuredFieldSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class TargetStructureSpec:
    analysis_start_offset: int | None
    entrypoints: tuple[StructuredEntrypointSpec, ...]
    regions: tuple[StructuredRegionSpec, ...]


@dataclass(frozen=True, slots=True)
class StructuredEntrypointSpec:
    offset: int
    label: str


def _symbol_label(symbol: str) -> str:
    token = symbol
    token = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", token)
    token = re.sub(r"([A-Za-z])([0-9])", r"\1_\2", token)
    token = re.sub(r"[^A-Za-z0-9]+", "_", token)
    return token.strip("_").lower()


def _resident_vector_entrypoints(metadata: TargetMetadata, resident: ResidentTargetMetadata) -> tuple[StructuredEntrypointSpec, ...]:
    autoinit = resident.autoinit
    if autoinit is None:
        raise ValueError("Auto-init resident is missing autoinit payload metadata")
    resident_name = resident.name
    if resident_name is None:
        raise ValueError("Resident target is missing resident name for vector mapping")
    prefixes = runtime_os.META.resident_vector_prefixes.get(metadata.target_type)
    if prefixes is None:
        raise ValueError(f"Missing KB resident vector prefix metadata for target type {metadata.target_type}")
    entrypoints: list[StructuredEntrypointSpec] = []
    if autoinit.init_func_offset is not None:
        entrypoints.append(
            StructuredEntrypointSpec(
                offset=autoinit.init_func_offset,
                label=f"{metadata.target_type}_init",
            )
        )
    kb_library = runtime_os.LIBRARIES.get(resident_name)
    for index, offset in enumerate(autoinit.vector_offsets):
        if index < len(prefixes):
            symbol = prefixes[index]
        else:
            if kb_library is None:
                raise ValueError(
                    f"Missing KB library entrypoint mapping for {resident_name} slot {index}"
                )
            lvo = -(index + 1) * runtime_os.META.lvo_slot_size
            function_name = kb_library.lvo_index.get(str(lvo))
            if function_name is None:
                raise ValueError(f"Missing KB LVO mapping for {resident_name}:{lvo}")
            symbol = function_name
        entrypoints.append(StructuredEntrypointSpec(offset=offset, label=_symbol_label(symbol)))
    return tuple(entrypoints)


def target_structure_spec(metadata: TargetMetadata | None) -> TargetStructureSpec | None:
    if metadata is None:
        return None
    if metadata.bootblock is not None:
        bootblock = metadata.bootblock
        return TargetStructureSpec(
            analysis_start_offset=bootblock.bootcode_offset,
            entrypoints=(StructuredEntrypointSpec(offset=bootblock.bootcode_offset, label="boot_entry"),),
            regions=(
                StructuredRegionSpec(
                    start=0,
                    end=bootblock.bootcode_offset,
                    subtype="struct_instance",
                    fields=(
                        StructuredFieldSpec(offset=0, label="boot_magic", is_string=True),
                        StructuredFieldSpec(offset=4, label="boot_checksum", size=4),
                        StructuredFieldSpec(offset=8, label="boot_root_block", size=4),
                    ),
                ),
            ),
        )
    if metadata.resident is not None:
        resident = metadata.resident
        resident_struct = runtime_os.STRUCTS["RT"]
        field_labels = {
            "RT_MATCHWORD": ("resident_matchword", False),
            "RT_MATCHTAG": ("resident_matchtag", True),
            "RT_ENDSKIP": ("resident_endskip", True),
            "RT_FLAGS": ("resident_flags", False),
            "RT_VERSION": ("resident_version", False),
            "RT_TYPE": ("resident_type", False),
            "RT_PRI": ("resident_priority", False),
            "RT_NAME": ("resident_name_ptr", True),
            "RT_IDSTRING": ("resident_idstring_ptr", True),
            "RT_INIT": ("resident_init_ptr", True),
        }
        regions = [
            StructuredRegionSpec(
                start=resident.offset,
                end=resident.offset + resident_struct.size,
                subtype="struct_instance",
                struct_name="RT",
                fields=tuple(
                    StructuredFieldSpec(
                        offset=resident.offset + field.offset,
                        label=field_labels[field.name][0],
                        size=(field.size if field.size > 0 else None),
                        pointer=field_labels[field.name][1],
                    )
                    for field in resident_struct.fields
                    if field.name in field_labels
                ),
            )
        ]
        if resident.auto_init:
            if resident.autoinit is None:
                raise ValueError("Resident auto-init metadata is missing payload details")
            autoinit = resident.autoinit
            entrypoints = _resident_vector_entrypoints(metadata, resident)
            regions.append(
                StructuredRegionSpec(
                    start=autoinit.payload_offset,
                    end=autoinit.payload_offset + 16,
                    subtype="struct_instance",
                    fields=(
                        StructuredFieldSpec(offset=autoinit.payload_offset, label="resident_base_size", size=4),
                        StructuredFieldSpec(offset=autoinit.payload_offset + 4, label="resident_vectors_ptr", size=4, pointer=True),
                        StructuredFieldSpec(offset=autoinit.payload_offset + 8, label="resident_initstruct_ptr", size=4, pointer=True),
                        StructuredFieldSpec(offset=autoinit.payload_offset + 12, label="resident_initfunc_ptr", size=4, pointer=True),
                    ),
                )
            )
            return TargetStructureSpec(
                analysis_start_offset=entrypoints[0].offset,
                entrypoints=entrypoints,
                regions=tuple(regions),
            )
        entrypoints = (
            StructuredEntrypointSpec(
                offset=resident.offset + resident.init_offset,
                label="resident_init",
            ),
        )
        return TargetStructureSpec(
            analysis_start_offset=entrypoints[0].offset,
            entrypoints=entrypoints,
            regions=tuple(regions),
        )
    return None


def target_metadata_path(target_dir: Path) -> Path:
    return target_dir / TARGET_METADATA_FILE_NAME


def write_target_metadata(target_dir: Path, metadata: TargetMetadata) -> None:
    target_metadata_path(target_dir).write_text(
        json.dumps(metadata.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_target_metadata(target_dir: Path) -> TargetMetadata | None:
    metadata_path = target_metadata_path(target_dir)
    if not metadata_path.exists():
        return None
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return TargetMetadata.from_dict(_json_object(payload))


def target_metadata_seed_key(metadata: TargetMetadata | None) -> str:
    if metadata is None or not metadata.entry_register_seeds:
        return "default"
    payload = json.dumps(
        [seed.to_dict() for seed in metadata.entry_register_seeds],
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
