from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kb.os_reference import (
    load_split_os_reference_payloads,
    merge_os_reference_payloads,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class OsIncludeOwner:
    kind: str
    canonical_include_path: str | None
    assembler_include_path: str | None
    source_file: str


@dataclass(frozen=True, slots=True)
class OsIncludeKb:
    library_lvo_owners: dict[str, OsIncludeOwner]
    constant_owners: dict[str, OsIncludeOwner]


def load_os_include_kb(project_root: Path = PROJECT_ROOT) -> OsIncludeKb:
    if project_root != PROJECT_ROOT:
        raise ValueError("load_os_include_kb only supports the canonical project root")
    includes, other, corrections = load_split_os_reference_payloads()
    owners_payload = merge_os_reference_payloads(
        includes=includes,
        other=other,
        corrections=corrections,
    )
    library_lvo_owners: dict[str, OsIncludeOwner] = {}
    for library_name, library in owners_payload["libraries"].items():
        owner_payload = library["owner"]
        kind = owner_payload["kind"]
        canonical_include_path = owner_payload["canonical_include_path"]
        assembler_include_path = owner_payload.get("assembler_include_path")
        source_file = owner_payload["source_file"]
        library_lvo_owners[library_name] = OsIncludeOwner(
            kind=kind,
            canonical_include_path=canonical_include_path,
            assembler_include_path=assembler_include_path,
            source_file=source_file,
        )
    constant_owners: dict[str, OsIncludeOwner] = {}
    for constant_name, constant in owners_payload["constants"].items():
        owner_payload = constant["owner"]
        kind = owner_payload["kind"]
        canonical_include_path = owner_payload["canonical_include_path"]
        assembler_include_path = owner_payload.get("assembler_include_path")
        source_file = owner_payload["source_file"]
        constant_owners[constant_name] = OsIncludeOwner(
            kind=kind,
            canonical_include_path=canonical_include_path,
            assembler_include_path=assembler_include_path,
            source_file=source_file,
        )
    return OsIncludeKb(
        library_lvo_owners=library_lvo_owners,
        constant_owners=constant_owners,
    )
