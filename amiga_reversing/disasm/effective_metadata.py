from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, replace
from pathlib import Path

from amiga_reversing.disasm.binary_source import (
    RawAddressModel,
    RawBinarySource,
    resolve_target_binary_source,
)
from amiga_reversing.disasm.manual_actions import (
    ManualLabelScope,
    ManualSeedKind,
    ManualSeedMode,
    ReviewItemKind,
    load_manual_projection,
)
from amiga_reversing.disasm.target_metadata import (
    AbsoluteCodeLabelMetadata,
    EntryCommentMetadata,
    EntryRegisterSeedKind,
    EntryRegisterSeedMetadata,
    ExecutionViewMetadata,
    ManualRepresentationMetadata,
    ManualRepresentationStyle,
    SeededCodeEntrypointMetadata,
    SeededCodeLabelMetadata,
    SeededEntityMetadata,
    SuppressedSeededItemMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
    apply_suppressed_seeded_items,
    load_target_metadata,
)


def effective_target_metadata(target_dir: Path) -> TargetMetadata | None:
    metadata = load_target_metadata(target_dir)
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


def _manual_label_source_locator(label: dict[str, object]) -> str:
    label_id = _manual_seed_text(label, "label_id") or "unnamed"
    return f"ManualLabel:{label_id}"


def _manual_comment_source_locator(comment: dict[str, object]) -> str:
    comment_id = _manual_seed_text(comment, "comment_id") or "unnamed"
    return f"ManualComment:{comment_id}"


def _manual_representation_source_locator(representation: dict[str, object]) -> str:
    representation_id = _manual_seed_text(representation, "representation_id") or "unnamed"
    return f"ManualRepresentation:{representation_id}"


def _manual_semantic_hint_source_locator(hint: dict[str, object]) -> str:
    hint_id = _manual_seed_text(hint, "semantic_hint_id") or "unnamed"
    return f"ManualSemanticHint:{hint_id}"


def _manual_action_citation(action_object: dict[str, object], id_field: str) -> str:
    action_id = _manual_seed_text(action_object, id_field) or "unnamed"
    return f"manual_action_log:{action_id}"


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
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
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
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_seed_citation(seed),
        source_id="manual_action_log",
        source_locator=_manual_seed_source_locator(seed),
    )


def _manual_label_to_code_label(label: dict[str, object]) -> SeededCodeLabelMetadata | None:
    if _manual_seed_text(label, "address_domain") == "runtime":
        return None
    if label.get("scope") is ManualLabelScope.LOCAL:
        return None
    parsed_range = _parse_manual_seed_range(label)
    if parsed_range is None:
        return None
    hunk, addr, _end = parsed_range
    name = _manual_seed_text(label, "name")
    if name is None:
        return None
    return SeededCodeLabelMetadata(
        addr=addr,
        hunk=hunk,
        name=name,
        comment=_manual_seed_text(label, "comment"),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(label, "label_id"),
        source_id="manual_action_log",
        source_locator=_manual_label_source_locator(label),
    )


def _manual_label_to_absolute_code_label(label: dict[str, object]) -> AbsoluteCodeLabelMetadata | None:
    if _manual_seed_text(label, "address_domain") != "runtime":
        return None
    addr = _manual_seed_int(label, "addr")
    name = _manual_seed_text(label, "name")
    if addr is None or name is None:
        return None
    return AbsoluteCodeLabelMetadata(
        addr=addr,
        name=name,
        comment=_manual_seed_text(label, "comment"),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(label, "label_id"),
    )


def _manual_comment_to_entry_comment(comment: dict[str, object]) -> EntryCommentMetadata | None:
    parsed_range = _parse_manual_seed_range(comment)
    if parsed_range is None:
        return None
    hunk, addr, _end = parsed_range
    text = _manual_seed_text(comment, "text") or _manual_seed_text(comment, "comment")
    if text is None:
        return None
    return EntryCommentMetadata(
        addr=addr,
        hunk=hunk,
        comment=text,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(comment, "comment_id"),
        source_id="manual_action_log",
        source_locator=_manual_comment_source_locator(comment),
    )


def _manual_representation_to_metadata(representation: dict[str, object]) -> ManualRepresentationMetadata | None:
    parsed_range = _parse_manual_seed_range(representation)
    if parsed_range is None:
        return None
    style_text = _manual_seed_text(representation, "style")
    if style_text is None:
        return None
    hunk, addr, end = parsed_range
    try:
        style = ManualRepresentationStyle(style_text)
    except ValueError:
        return None
    return ManualRepresentationMetadata(
        addr=addr,
        end=end,
        hunk=hunk,
        style=style,
        element_kind=_manual_seed_text(representation, "element_kind"),
        operand_index=_manual_seed_int(representation, "operand_index"),
        symbol=_manual_seed_text(representation, "symbol"),
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(representation, "representation_id"),
        source_id="manual_action_log",
        source_locator=_manual_representation_source_locator(representation),
    )


def _manual_semantic_hint_symbol(hint: dict[str, object]) -> str | None:
    domain = _manual_seed_text(hint, "domain")
    symbol = _manual_seed_text(hint, "symbol")
    if symbol is None:
        return None
    if domain == "equate":
        return symbol
    if domain == "lvo":
        function = _manual_seed_text(hint, "function")
        if function is None and "/" in symbol:
            function = symbol.rsplit("/", 1)[-1]
        if function is None:
            return None
        return function if function.startswith("_LVO") else f"_LVO{function}"
    if domain == "struct_offset":
        field = _manual_seed_text(hint, "field")
        if field is None and "." in symbol:
            field = symbol.rsplit(".", 1)[-1]
        if field is None:
            return None
        return field.upper()
    return None


def _manual_semantic_hint_to_representation(hint: dict[str, object]) -> ManualRepresentationMetadata | None:
    symbol = _manual_semantic_hint_symbol(hint)
    if symbol is None:
        return None
    parsed_range = _parse_manual_seed_range(hint)
    if parsed_range is None:
        return None
    hunk, addr, end = parsed_range
    return ManualRepresentationMetadata(
        addr=addr,
        end=end,
        hunk=hunk,
        style=ManualRepresentationStyle.SYMBOL,
        element_kind=_manual_seed_text(hint, "element_kind"),
        operand_index=_manual_seed_int(hint, "operand_index"),
        symbol=symbol,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(hint, "semantic_hint_id"),
        source_id="manual_action_log",
        source_locator=_manual_semantic_hint_source_locator(hint),
    )


def _manual_register_seed_to_metadata(register_seed: dict[str, object]) -> EntryRegisterSeedMetadata | None:
    register = _manual_seed_text(register_seed, "register")
    kind_text = _manual_seed_text(register_seed, "kind")
    if register is None or kind_text is None:
        return None
    try:
        kind = EntryRegisterSeedKind(kind_text)
    except ValueError:
        return None
    entry_offset = _manual_seed_int(register_seed, "entry_offset")
    return EntryRegisterSeedMetadata(
        entry_offset=entry_offset,
        register=register,
        kind=kind,
        note=_manual_seed_text(register_seed, "note") or _manual_action_citation(register_seed, "register_seed_id"),
        library_name=_manual_seed_text(register_seed, "library_name"),
        struct_name=_manual_seed_text(register_seed, "struct_name"),
        context_name=_manual_seed_text(register_seed, "context_name"),
    )


def _manual_suppressed_seeded_item_to_metadata(item: dict[str, object]) -> SuppressedSeededItemMetadata | None:
    kind = _manual_seed_text(item, "kind")
    hunk = _manual_seed_int(item, "hunk")
    addr = _manual_seed_int(item, "addr")
    if kind is None or hunk is None or addr is None:
        return None
    try:
        return SuppressedSeededItemMetadata.from_dict({"kind": kind, "hunk": hunk, "addr": addr})
    except AssertionError:
        return None


def _merge_seeded_entity_projection(
    existing: SeededEntityMetadata,
    override: SeededEntityMetadata,
) -> SeededEntityMetadata:
    return SeededEntityMetadata(
        addr=override.addr,
        hunk=override.hunk,
        end=override.end if override.end is not None else existing.end,
        name=override.name if override.name is not None else existing.name,
        comment=override.comment if override.comment is not None else existing.comment,
        type=override.type if override.type is not None else existing.type,
        subtype=override.subtype if override.subtype is not None else existing.subtype,
        unit=override.unit if override.unit is not None else existing.unit,
        encoding=override.encoding if override.encoding is not None else existing.encoding,
        seed_origin=override.seed_origin,
        review_status=override.review_status,
        citation=override.citation,
        source_id=override.source_id if override.source_id is not None else existing.source_id,
        source_path=override.source_path if override.source_path is not None else existing.source_path,
        source_locator=override.source_locator if override.source_locator is not None else existing.source_locator,
    )


def _merge_projected_seeded_entities(
    entities: list[SeededEntityMetadata],
) -> tuple[SeededEntityMetadata, ...]:
    merged: dict[tuple[int, int], SeededEntityMetadata] = {}
    for entity in entities:
        key = (entity.hunk, entity.addr)
        existing = merged.get(key)
        merged[key] = entity if existing is None else _merge_seeded_entity_projection(existing, entity)
    return tuple(merged[key] for key in sorted(merged))


def _manual_execution_view_to_metadata(view: dict[str, object]) -> ExecutionViewMetadata | None:
    source_start = _manual_seed_int(view, "source_start")
    source_end = _manual_seed_int(view, "source_end")
    base_addr = _manual_seed_int(view, "base_addr")
    name = _manual_seed_text(view, "name")
    if source_start is None or source_end is None or base_addr is None or name is None:
        return None
    if source_start < 0 or source_end <= source_start or base_addr < 0:
        return None
    return ExecutionViewMetadata(
        source_start=source_start,
        source_end=source_end,
        base_addr=base_addr,
        name=name,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED,
        citation=_manual_action_citation(view, "execution_view_id"),
        comment=_manual_seed_text(view, "comment"),
    )


def _manual_execution_view_key(view: dict[str, object]) -> tuple[int, int, int] | None:
    source_start = _manual_seed_int(view, "source_start")
    source_end = _manual_seed_int(view, "source_end")
    base_addr = _manual_seed_int(view, "base_addr")
    if source_start is None or source_end is None or base_addr is None:
        return None
    if source_start < 0 or source_end <= source_start or base_addr < 0:
        return None
    return source_start, source_end, base_addr


def _apply_manual_seed_projection(target_dir: Path, metadata: TargetMetadata | None) -> TargetMetadata | None:
    projection = load_manual_projection(
        target_dir,
        binary_source=resolve_target_binary_source(target_dir),
        stronger_metadata=metadata,
    )
    conflicted_seed_ids: set[str] = set()
    conflicted_label_ids: set[str] = set()
    for item in projection.review_items:
        kind = item.get("kind")
        if not isinstance(kind, ReviewItemKind):
            raise TypeError("review item kind must be a ReviewItemKind")
        if kind is ReviewItemKind.MANUAL_SEED_CONFLICT:
            seed_ids = item.get("seed_ids")
            if isinstance(seed_ids, list | tuple):
                conflicted_seed_ids.update(seed_id for seed_id in seed_ids if isinstance(seed_id, str))
        elif kind is ReviewItemKind.LABEL_SCOPE_CONFLICT:
            label_ids = item.get("label_ids")
            if isinstance(label_ids, list | tuple):
                conflicted_label_ids.update(label_id for label_id in label_ids if isinstance(label_id, str))
    required_seeds = tuple(
        seed for seed in projection.seeds
        if seed.get("mode") is ManualSeedMode.REQUIRED or seed.get("mode") is None
        if seed.get("seed_id") not in conflicted_seed_ids
    )
    labels = tuple(
        label for label in projection.labels
        if label.get("label_id") not in conflicted_label_ids
    )
    comments = projection.comments
    representations = projection.representations
    semantic_hints = projection.semantic_hints
    register_seed_projections = projection.register_seeds
    suppressed_seeded_item_projections = projection.suppressed_seeded_items
    execution_view_projections = projection.execution_views
    removed_execution_view_projections = projection.removed_execution_views
    if (
        not required_seeds
        and not labels
        and not comments
        and not representations
        and not semantic_hints
        and not register_seed_projections
        and not suppressed_seeded_item_projections
        and not execution_view_projections
        and not removed_execution_view_projections
    ):
        return metadata
    if metadata is None:
        metadata = TargetMetadata(target_type="program", entry_register_seeds=())
    seeded_entities = list(metadata.seeded_entities)
    seeded_code_labels = list(metadata.seeded_code_labels)
    seeded_code_entrypoints = list(metadata.seeded_code_entrypoints)
    absolute_code_labels = list(metadata.absolute_code_labels)
    entry_comments = list(metadata.entry_comments)
    entry_register_seeds = list(metadata.entry_register_seeds)
    manual_representations = list(metadata.manual_representations)
    execution_views = list(metadata.execution_views)
    suppressed_seeded_items = list(metadata.suppressed_seeded_items)
    removed_execution_view_keys = {
        key
        for view in removed_execution_view_projections
        if (key := _manual_execution_view_key(view)) is not None
    }
    if removed_execution_view_keys:
        execution_views = [
            view
            for view in execution_views
            if (view.source_start, view.source_end, view.base_addr) not in removed_execution_view_keys
        ]
    for seed in required_seeds:
        seed_kind = seed.get("kind")
        if seed_kind is ManualSeedKind.CODE:
            entrypoint = _manual_seed_to_code_entrypoint(seed)
            if entrypoint is not None:
                seeded_code_entrypoints.append(entrypoint)
        elif seed_kind is ManualSeedKind.DATA:
            entity = _manual_seed_to_data_entity(seed)
            if entity is not None:
                seeded_entities.append(entity)
    for label in labels:
        code_label = _manual_label_to_code_label(label)
        if code_label is not None:
            seeded_code_labels.append(code_label)
        absolute_label = _manual_label_to_absolute_code_label(label)
        if absolute_label is not None:
            absolute_code_labels.append(absolute_label)
    for comment in comments:
        entry_comment = _manual_comment_to_entry_comment(comment)
        if entry_comment is not None:
            entry_comments.append(entry_comment)
    for representation in representations:
        manual_representation = _manual_representation_to_metadata(representation)
        if manual_representation is not None:
            manual_representations.append(manual_representation)
    for hint in semantic_hints:
        manual_representation = _manual_semantic_hint_to_representation(hint)
        if manual_representation is not None:
            manual_representations.append(manual_representation)
    for register_seed in register_seed_projections:
        entry_register_seed = _manual_register_seed_to_metadata(register_seed)
        if entry_register_seed is not None:
            entry_register_seeds.append(entry_register_seed)
    for item in suppressed_seeded_item_projections:
        suppressed_seeded_item = _manual_suppressed_seeded_item_to_metadata(item)
        if suppressed_seeded_item is not None:
            suppressed_seeded_items.append(suppressed_seeded_item)
    for view in execution_view_projections:
        execution_view = _manual_execution_view_to_metadata(view)
        if execution_view is not None:
            execution_views.append(execution_view)
    merged_execution_views = {
        (view.source_start, view.source_end, view.base_addr): view for view in execution_views
    }
    result = replace(
        metadata,
        entry_register_seeds=tuple(entry_register_seeds),
        seeded_entities=_merge_projected_seeded_entities(seeded_entities),
        seeded_code_labels=tuple(seeded_code_labels),
        absolute_code_labels=tuple(absolute_code_labels),
        seeded_code_entrypoints=tuple(seeded_code_entrypoints),
        entry_comments=tuple(entry_comments),
        manual_representations=tuple(manual_representations),
        execution_views=tuple(merged_execution_views.values()),
        suppressed_seeded_items=tuple(suppressed_seeded_items),
    )
    if suppressed_seeded_items:
        result = apply_suppressed_seeded_items(result, tuple(suppressed_seeded_items))
        result = replace(result, suppressed_seeded_items=tuple(suppressed_seeded_items))
    return result


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
    if binary_source.address_model is not RawAddressModel.RUNTIME_ABSOLUTE:
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
