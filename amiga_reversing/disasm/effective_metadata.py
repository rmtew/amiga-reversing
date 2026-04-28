from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from amiga_reversing.disasm.binary_source import RawBinarySource, resolve_target_binary_source
from amiga_reversing.disasm.target_metadata import TargetMetadata, load_target_metadata
from amiga_reversing.disasm.target_ui_edits import (
    apply_target_ui_edits,
    load_target_ui_edits,
    target_ui_edits_stamp_text,
)


def effective_target_metadata(target_dir: Path) -> TargetMetadata | None:
    return apply_target_ui_edits(load_target_metadata(target_dir), load_target_ui_edits(target_dir))


def effective_metadata_text(target_dir: Path) -> str:
    metadata = effective_target_metadata(target_dir)
    if metadata is None:
        return ""
    payload = asdict(metadata)
    _add_source_descriptor_execution_view(target_dir, payload)
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _add_source_descriptor_execution_view(target_dir: Path, payload: dict[str, object]) -> None:
    binary_source = resolve_target_binary_source(target_dir)
    if not isinstance(binary_source, RawBinarySource):
        return
    if binary_source.address_model != "runtime_absolute":
        return
    source_end = binary_source.path.stat().st_size
    if source_end <= 0:
        return
    existing_views = payload.get("execution_views")
    if existing_views is None:
        raw_views: list[object] = []
    elif isinstance(existing_views, tuple):
        raw_views = list(existing_views)
    elif isinstance(existing_views, list):
        raw_views = existing_views
    else:
        return
    payload["execution_views"] = raw_views
    for raw_view in raw_views:
        if not isinstance(raw_view, dict):
            continue
        if (
            raw_view.get("source_start") == 0
            and raw_view.get("source_end") == source_end
            and raw_view.get("base_addr") == binary_source.load_address
        ):
            return
    raw_views.append(
        {
            "base_addr": binary_source.load_address,
            "citation": "source_binary.json",
            "comment": "Runtime absolute raw source load view.",
            "name": "source_binary",
            "review_status": "validated",
            "seed_origin": "manual_analysis",
            "source_end": source_end,
            "source_start": 0,
        }
    )


def effective_metadata_hash(target_dir: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(effective_metadata_text(target_dir).encode("utf-8"))
    edits_text = target_ui_edits_stamp_text(target_dir)
    if edits_text:
        hasher.update(b"\n--target-ui-edits--\n")
        hasher.update(edits_text.encode("utf-8"))
    return hasher.hexdigest()


@contextmanager
def effective_metadata_file(target_dir: Path) -> Iterator[Path | None]:
    text = effective_metadata_text(target_dir)
    if not text:
        yield None
        return
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as temp_file:
            temp_file.write(text)
            temp_path = Path(temp_file.name)
        yield temp_path
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
