from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, replace
from pathlib import Path

from amiga_reversing.disasm.binary_source import (
    RawBinarySource,
    resolve_target_binary_source,
)
from amiga_reversing.disasm.manual_actions import load_manual_projection
from amiga_reversing.disasm.target_metadata import (
    SeededCodeEntrypointMetadata,
    SeededEntityMetadata,
    TargetMetadata,
    load_target_metadata,
)
from amiga_reversing.disasm.target_ui_edits import (
    apply_target_ui_edits,
    load_target_ui_edits,
    target_ui_edits_stamp_text,
)


def effective_target_metadata(target_dir: Path) -> TargetMetadata | None:
    metadata = apply_target_ui_edits(load_target_metadata(target_dir), load_target_ui_edits(target_dir))
    return _apply_manual_seed_projection(target_dir, metadata)


def _manual_seed_int(seed: dict[str, object], field_name: str) -> int | None:
    value = seed.get(field_name)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            return None
    return None


def _parse_manual_seed_range(seed: dict[str, object]) -> tuple[int, int, int | None] | None:
    hunk = _manual_seed_int(seed, "hunk") or 0
    addr = _manual_seed_int(seed, "addr")
    end = _manual_seed_int(seed, "end")
    if addr is not None:
        return hunk, addr, end
    raw_range = seed.get("range")
    if not isinstance(raw_range, str):
        return None
    range_text = raw_range.strip()
    if ":" in range_text:
        hunk_text, range_text = range_text.split(":", 1)
        if hunk_text.lower().startswith("h"):
            try:
                hunk = int(hunk_text[1:], 0)
            except ValueError:
                return None
    if ".." in range_text:
        start_text, end_text = range_text.split("..", 1)
        try:
            return hunk, int(start_text.replace("$", "0x"), 0), int(end_text.replace("$", "0x"), 0)
        except ValueError:
            return None
    try:
        return hunk, int(range_text.replace("$", "0x"), 0), None
    except ValueError:
        return None


def _manual_seed_text(seed: dict[str, object], field_name: str) -> str | None:
    value = seed.get(field_name)
    return value if isinstance(value, str) and value else None


def _manual_seed_name(seed: dict[str, object]) -> str:
    name = _manual_seed_text(seed, "name")
    if name is not None:
        return name
    seed_id = _manual_seed_text(seed, "seed_id") or "unnamed"
    safe = "".join(char if char.isalnum() or char == "_" else "_" for char in seed_id)
    return f"manual_seed_{safe}"


def _manual_seed_citation(seed: dict[str, object]) -> str:
    seed_id = _manual_seed_text(seed, "seed_id") or "unnamed"
    return f"manual_action_log:{seed_id}"


def _manual_seed_source_locator(seed: dict[str, object]) -> str:
    seed_id = _manual_seed_text(seed, "seed_id") or "unnamed"
    return f"ManualSeed:{seed_id}"


def _manual_seed_comment(seed: dict[str, object]) -> str | None:
    comment = _manual_seed_text(seed, "comment")
    if comment is not None:
        return comment
    details: list[str] = []
    for key in ("mode", "data_role", "unit", "encoding"):
        value = _manual_seed_text(seed, key)
        if value is not None:
            details.append(f"{key}={value}")
    return ", ".join(details) if details else None


def _manual_seed_to_code_entrypoint(seed: dict[str, object]) -> SeededCodeEntrypointMetadata | None:
    parsed_range = _parse_manual_seed_range(seed)
    if parsed_range is None:
        return None
    hunk, addr, _end = parsed_range
    return SeededCodeEntrypointMetadata(
        addr=addr,
        hunk=hunk,
        name=_manual_seed_name(seed),
        role=_manual_seed_text(seed, "role"),
        comment=_manual_seed_comment(seed),
        seed_origin="manual_analysis",
        review_status="seeded",
        citation=_manual_seed_citation(seed),
        source_id="manual_action_log",
        source_locator=_manual_seed_source_locator(seed),
    )


def _manual_seed_to_data_entity(seed: dict[str, object]) -> SeededEntityMetadata | None:
    parsed_range = _parse_manual_seed_range(seed)
    if parsed_range is None:
        return None
    hunk, addr, end = parsed_range
    return SeededEntityMetadata(
        addr=addr,
        end=end,
        hunk=hunk,
        name=_manual_seed_text(seed, "name"),
        comment=_manual_seed_comment(seed),
        type="data",
        subtype=_manual_seed_text(seed, "data_role"),
        unit=_manual_seed_text(seed, "unit"),
        encoding=_manual_seed_text(seed, "encoding"),
        seed_origin="manual_analysis",
        review_status="seeded",
        citation=_manual_seed_citation(seed),
        source_id="manual_action_log",
        source_locator=_manual_seed_source_locator(seed),
    )


def _apply_manual_seed_projection(target_dir: Path, metadata: TargetMetadata | None) -> TargetMetadata | None:
    projection = load_manual_projection(target_dir, binary_source=resolve_target_binary_source(target_dir))
    conflicted_seed_ids: set[str] = set()
    for item in projection.review_items:
        if item.get("kind") != "manual_seed_conflict":
            continue
        seed_ids = item.get("seed_ids")
        if isinstance(seed_ids, list | tuple):
            conflicted_seed_ids.update(seed_id for seed_id in seed_ids if isinstance(seed_id, str))
    required_seeds = tuple(
        seed for seed in projection.seeds
        if seed.get("mode") == "required" or seed.get("mode") is None
        if seed.get("seed_id") not in conflicted_seed_ids
    )
    if not required_seeds:
        return metadata
    if metadata is None:
        metadata = TargetMetadata(target_type="program", entry_register_seeds=())
    seeded_entities = list(metadata.seeded_entities)
    seeded_code_entrypoints = list(metadata.seeded_code_entrypoints)
    for seed in required_seeds:
        seed_kind = _manual_seed_text(seed, "kind")
        if seed_kind == "code":
            entrypoint = _manual_seed_to_code_entrypoint(seed)
            if entrypoint is not None:
                seeded_code_entrypoints.append(entrypoint)
        elif seed_kind == "data":
            entity = _manual_seed_to_data_entity(seed)
            if entity is not None:
                seeded_entities.append(entity)
    return replace(
        metadata,
        seeded_entities=tuple(seeded_entities),
        seeded_code_entrypoints=tuple(seeded_code_entrypoints),
    )


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
