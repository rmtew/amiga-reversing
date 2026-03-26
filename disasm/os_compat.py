from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from disasm.types import DisassemblySession, ListingRow, StructFieldOperandMetadata


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def normalize_compatibility_version(required: str, supported: Sequence[str]) -> str:
    required_key = _version_key(required)
    for candidate in supported:
        if _version_key(candidate) >= required_key:
            return candidate
    raise ValueError(f"Missing KB compatibility version for required OS level {required}")


def max_compatibility_version(versions: Iterable[str]) -> str:
    materialized = tuple(versions)
    if not materialized:
        raise ValueError("Cannot compute compatibility floor from an empty version set")
    return max(materialized, key=_version_key)


def select_struct_field_name(field: object, compatibility_floor: str) -> str:
    names_by_version = getattr(field, "names_by_version", None)
    if not isinstance(names_by_version, Mapping) or not names_by_version:
        name = getattr(field, "name", None)
        if not isinstance(name, str):
            raise ValueError("Missing KB struct field name")
        return name
    candidates = [
        (version, name)
        for version, name in names_by_version.items()
        if _version_key(version) <= _version_key(compatibility_floor)
    ]
    if not candidates:
        raise ValueError(
            f"Missing KB struct field name at compatibility {compatibility_floor} for "
            f"{getattr(field, 'name', '<unknown>')}"
        )
    return max(candidates, key=lambda item: _version_key(item[0]))[1]


def collect_used_struct_fields(rows: Sequence[ListingRow]) -> set[tuple[str, str]]:
    used: set[tuple[str, str]] = set()
    for row in rows:
        for operand in row.operand_parts:
            metadata = operand.metadata
            if not isinstance(metadata, StructFieldOperandMetadata):
                continue
            if metadata.field_symbol is None:
                continue
            used.add((metadata.owner_struct, metadata.field_symbol))
    return used


def infer_emit_compatibility_floor(
    session: DisassemblySession,
    *,
    include_paths: Iterable[str],
    struct_fields: Iterable[tuple[str, str]],
) -> str:
    if not session.hunk_sessions:
        raise ValueError("Disassembly session is missing hunk sessions")
    os_kb = session.hunk_sessions[0].os_kb
    supported = tuple(os_kb.META.compatibility_versions)
    if not supported:
        raise ValueError("OS KB is missing compatibility_versions")

    required_versions: list[str] = [supported[0]]
    include_min_versions: Mapping[str, str] = os_kb.META.include_min_versions

    for include_path in include_paths:
        version = include_min_versions.get(include_path.lower())
        if version is None:
            raise ValueError(f"Missing KB include compatibility for {include_path}")
        required_versions.append(version)

    for struct_name, field_name in struct_fields:
        struct_def = os_kb.STRUCTS.get(struct_name)
        if struct_def is None:
            raise ValueError(f"Missing KB struct for compatibility inference: {struct_name}")
        required_versions.append(struct_def.available_since)
        for field in struct_def.fields:
            if field.name != field_name:
                continue
            required_versions.append(field.available_since)
            break
        else:
            raise ValueError(f"Missing KB struct field for compatibility inference: {struct_name}.{field_name}")

    for hunk_session in session.hunk_sessions:
        for call in hunk_session.lib_calls:
            if not call.library or not call.function or call.library == "unknown":
                continue
            library = os_kb.LIBRARIES.get(call.library)
            if library is None:
                raise ValueError(f"Missing KB library for compatibility inference: {call.library}")
            function = library.functions.get(call.function)
            if function is None:
                raise ValueError(
                    f"Missing KB function for compatibility inference: {call.library}/{call.function}"
                )
            if function.os_since is not None:
                required_versions.append(normalize_compatibility_version(function.os_since, supported))

    return max_compatibility_version(required_versions)
