"""KB-driven helpers for Amiga OS struct composition and field lookup."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


class OsStructFieldLike(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def type(self) -> str: ...

    @property
    def offset(self) -> int: ...

    @property
    def size(self) -> int: ...

    @property
    def struct(self) -> str | None: ...

    @property
    def pointer_struct(self) -> str | None: ...


class OsStructLike(Protocol):
    @property
    def source(self) -> str: ...

    @property
    def base_offset(self) -> int: ...

    @property
    def size(self) -> int: ...

    @property
    def fields(self) -> tuple[OsStructFieldLike, ...]: ...

    @property
    def base_struct(self) -> str | None: ...


@dataclass(frozen=True, slots=True)
class ResolvedStructField:
    owner_struct: str
    field: OsStructFieldLike


def resolve_struct_field(structs: Mapping[str, OsStructLike], struct_name: str, offset: int,
                         active: frozenset[str] = frozenset()
                         ) -> ResolvedStructField | None:
    if struct_name in active:
        raise ValueError(f"Cyclic struct embedding detected for {struct_name}")
    struct_def = structs[struct_name]
    if offset < 0 or offset >= struct_def.size:
        return None

    next_active = active | {struct_name}

    for field in struct_def.fields:
        if field.type != "STRUCT" and field.type != "LABEL" and field.offset == offset:
            return ResolvedStructField(owner_struct=struct_name, field=field)

    if struct_def.base_struct is not None and offset < struct_def.base_offset:
        return resolve_struct_field(structs, struct_def.base_struct, offset, next_active)

    for field in struct_def.fields:
        if (
            field.type == "STRUCT"
            and field.struct is not None
            and field.offset <= offset < field.offset + field.size
        ):
            return resolve_struct_field(
                structs, field.struct, offset - field.offset, next_active)

    return None
