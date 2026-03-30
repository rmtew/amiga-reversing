from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from disasm.types import (
    BlockRowContext,
    DisassemblySession,
    ListingRow,
    StructFieldOperandMetadata,
)
from m68k.os_calls import OsKb


@dataclass(frozen=True, slots=True)
class CompatibilityDependency:
    kind: str
    symbol: str
    required_since: str
    usages: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CompatibilityReport:
    floor: str
    dependencies: tuple[CompatibilityDependency, ...]


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
    return str(max(candidates, key=lambda item: _version_key(item[0]))[1])


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


def _include_path_from_row(row: ListingRow) -> str | None:
    if row.opcode_or_directive != "INCLUDE":
        return None
    match = re.match(r'\s*INCLUDE\s+"([^"]+)"\s*$', row.text.strip())
    if match is None:
        raise ValueError(f"Malformed INCLUDE row: {row.text!r}")
    return match.group(1)


def _usage_label(hunk_index: int, addr: int) -> str:
    return f"hunk {hunk_index} @ ${addr:04X}"


def _row_usage(row: ListingRow) -> str | None:
    if row.addr is None:
        return None
    source_context = row.source_context
    if not isinstance(source_context, BlockRowContext):
        return None
    return _usage_label(source_context.hunk_index, row.addr)


def _collect_used_struct_field_usages(rows: Sequence[ListingRow]) -> dict[tuple[str, str], set[str]]:
    usages: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        row_usage = _row_usage(row)
        for operand in row.operand_parts:
            metadata = operand.metadata
            if not isinstance(metadata, StructFieldOperandMetadata):
                continue
            if metadata.field_symbol is None:
                continue
            key = (metadata.owner_struct, metadata.field_symbol)
            if row_usage is None:
                usages.setdefault(key, set())
                continue
            usages.setdefault(key, set()).add(row_usage)
    return usages


def _collect_include_paths(rows: Sequence[ListingRow]) -> tuple[str, ...]:
    includes: set[str] = set()
    for row in rows:
        include_path = _include_path_from_row(row)
        if include_path is not None:
            includes.add(include_path)
    return tuple(sorted(includes))


def _canonical_include_path(os_kb: OsKb, include_path: str) -> str:
    normalized = include_path.lower()
    meta = os_kb.META
    include_min_versions = meta.include_min_versions
    if normalized in include_min_versions:
        return normalized
    for owner in meta.library_lvo_owners.values():
        assembler_include_path = owner.assembler_include_path
        canonical_include_path = owner.canonical_include_path
        if (
            isinstance(assembler_include_path, str)
            and isinstance(canonical_include_path, str)
            and normalized == assembler_include_path.lower()
        ):
            return canonical_include_path.lower()
    return normalized


def _target_library_name(session: DisassemblySession) -> str | None:
    metadata = getattr(session, "target_metadata", None)
    if metadata is None:
        return None
    if metadata.library is not None:
        return str(metadata.library.library_name)
    if metadata.resident is not None:
        return str(metadata.resident.name)
    return None


def build_emit_compatibility_report(
    session: DisassemblySession,
    *,
    rows: Sequence[ListingRow],
    include_paths: Iterable[str] | None = None,
    struct_fields: Iterable[tuple[str, str]] | None = None,
) -> CompatibilityReport:
    if not session.hunk_sessions:
        raise ValueError("Disassembly session is missing hunk sessions")
    os_kb: OsKb = session.hunk_sessions[0].os_kb
    supported = tuple(os_kb.META.compatibility_versions)
    if not supported:
        raise ValueError("OS KB is missing compatibility_versions")

    resolved_include_paths = tuple(sorted(include_paths if include_paths is not None else _collect_include_paths(rows)))
    resolved_struct_field_usages = _collect_used_struct_field_usages(rows)
    if struct_fields is not None:
        allowed_fields = set(struct_fields)
        resolved_struct_field_usages = {
            key: usages
            for key, usages in resolved_struct_field_usages.items()
            if key in allowed_fields
        }

    dependency_map: dict[tuple[str, str], tuple[str, set[str]]] = {}
    target_library_name = _target_library_name(session)

    def add_dependency(kind: str, symbol: str, required_since: str, usages: Iterable[str] = ()) -> None:
        key = (kind, symbol)
        usage_set = set(usages)
        existing = dependency_map.get(key)
        if existing is None:
            dependency_map[key] = (required_since, usage_set)
            return
        existing_version, existing_usages = existing
        if existing_version != required_since:
            raise ValueError(
                f"Conflicting compatibility versions for {kind} {symbol}: "
                f"{existing_version} vs {required_since}"
            )
        existing_usages.update(usage_set)

    include_min_versions: Mapping[str, str] = os_kb.META.include_min_versions
    for include_path in resolved_include_paths:
        canonical_include_path = _canonical_include_path(os_kb, include_path)
        version = include_min_versions.get(canonical_include_path)
        if version is None:
            raise ValueError(f"Missing KB include compatibility for {include_path}")
        add_dependency("include", include_path, version)

    for struct_name, field_name in sorted(resolved_struct_field_usages):
        struct_def = os_kb.STRUCTS.get(struct_name)
        if struct_def is None:
            raise ValueError(f"Missing KB struct for compatibility inference: {struct_name}")
        if getattr(struct_def, "source", None) == "target_metadata":
            continue
        field_def = next((field for field in struct_def.fields if field.name == field_name), None)
        if field_def is None:
            raise ValueError(f"Missing KB struct field for compatibility inference: {struct_name}.{field_name}")
        usages = resolved_struct_field_usages[(struct_name, field_name)]
        add_dependency("struct", struct_name, struct_def.available_since, usages)
        add_dependency("struct_field", f"{struct_name}.{field_name}", field_def.available_since, usages)

    for hunk_session in session.hunk_sessions:
        for call in hunk_session.lib_calls:
            if not call.library or not call.function or call.library == "unknown":
                continue
            if target_library_name is not None and call.library == target_library_name:
                continue
            library = os_kb.LIBRARIES.get(call.library)
            if library is None:
                raise ValueError(f"Missing KB library for compatibility inference: {call.library}")
            function = library.functions.get(call.function)
            if function is None:
                raise ValueError(
                    f"Missing KB function for compatibility inference: {call.library}/{call.function}"
                )
            if function.os_since is None:
                continue
            add_dependency(
                "library_call",
                f"{call.library}/{call.function}",
                normalize_compatibility_version(function.os_since, supported),
                (_usage_label(hunk_session.hunk_index, call.addr),),
            )

    required_versions = [supported[0]]
    dependencies = tuple(
        CompatibilityDependency(
            kind=kind,
            symbol=symbol,
            required_since=required_since,
            usages=tuple(sorted(usages)),
        )
        for (kind, symbol), (required_since, usages) in sorted(dependency_map.items())
    )
    required_versions.extend(dependency.required_since for dependency in dependencies)
    return CompatibilityReport(
        floor=max_compatibility_version(required_versions),
        dependencies=dependencies,
    )


def infer_emit_compatibility_floor(
    session: DisassemblySession,
    *,
    include_paths: Iterable[str],
    struct_fields: Iterable[tuple[str, str]],
) -> str:
    return build_emit_compatibility_report(
        session,
        rows=(),
        include_paths=include_paths,
        struct_fields=struct_fields,
    ).floor
