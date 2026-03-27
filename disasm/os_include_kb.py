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
    include_path: str | None
    comment_include_path: str | None
    source_file: str
    available_since: str | None


@dataclass(frozen=True, slots=True)
class OsIncludeKb:
    library_lvo_owners: dict[str, OsIncludeOwner]


def load_os_include_kb(project_root: Path = PROJECT_ROOT) -> OsIncludeKb:
    if project_root != PROJECT_ROOT:
        raise ValueError("load_os_include_kb only supports the canonical project root")
    includes, other, corrections = load_split_os_reference_payloads()
    owners_payload = merge_os_reference_payloads(
        includes=includes,
        other=other,
        corrections=corrections,
    )["_meta"]["library_lvo_owners"]
    library_lvo_owners: dict[str, OsIncludeOwner] = {}
    for library_name, owner_value in owners_payload.items():
        owner_payload = owner_value
        kind = owner_payload["kind"]
        include_path = owner_payload["include_path"]
        comment_include_path = owner_payload["comment_include_path"]
        source_file = owner_payload["source_file"]
        available_since = owner_payload["available_since"]
        library_lvo_owners[library_name] = OsIncludeOwner(
            kind=kind,
            include_path=include_path,
            comment_include_path=comment_include_path,
            source_file=source_file,
            available_since=available_since,
        )
    return OsIncludeKb(library_lvo_owners=library_lvo_owners)
