from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _json_object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


@dataclass(frozen=True, slots=True)
class OsIncludeOwner:
    kind: str
    include_path: str | None
    comment_include_path: str | None
    source_file: str


@dataclass(frozen=True, slots=True)
class OsIncludeKb:
    library_lvo_owners: dict[str, OsIncludeOwner]


def load_os_include_kb(project_root: Path = PROJECT_ROOT) -> OsIncludeKb:
    payload = json.loads((project_root / "knowledge" / "amiga_os_reference.json").read_text(encoding="utf-8"))
    root = _json_object(payload)
    meta_payload = _json_object(root["_meta"])
    owners_payload = _json_object(meta_payload["library_lvo_owners"])
    library_lvo_owners: dict[str, OsIncludeOwner] = {}
    for library_name, owner_value in owners_payload.items():
        assert isinstance(library_name, str)
        owner_payload = _json_object(owner_value)
        kind = owner_payload["kind"]
        include_path = owner_payload["include_path"]
        comment_include_path = owner_payload["comment_include_path"]
        source_file = owner_payload["source_file"]
        assert isinstance(kind, str)
        assert include_path is None or isinstance(include_path, str)
        assert comment_include_path is None or isinstance(comment_include_path, str)
        assert isinstance(source_file, str)
        library_lvo_owners[library_name] = OsIncludeOwner(
            kind=kind,
            include_path=include_path,
            comment_include_path=comment_include_path,
            source_file=source_file,
        )
    return OsIncludeKb(library_lvo_owners=library_lvo_owners)
