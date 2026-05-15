from __future__ import annotations

import json
import re
import uuid
from collections.abc import Callable, Mapping
from functools import lru_cache
from pathlib import Path
from typing import cast

from amiga_reversing.disasm.listing_context import (
    element_numeric_values,
    listing_row_context,
    selected_listing_element_context,
)

_KNOWLEDGE_PATH = Path(__file__).resolve().parents[2] / "knowledge" / "amiga_ndk_includes_parsed.json"


def review_item_action_catalog(item: Mapping[str, object]) -> list[dict[str, object]]:
    kind = str(item.get("kind") or "")
    actions = [_transient("review.navigate", "Navigate", "navigate", item)]
    if kind == "review_note":
        actions.append(_review_note_action("review_note.edit", "Edit review note", "edit_review_note", item))
        actions.append(_review_note_action("review_note.clear", "Clear review note", "clear_review_note", item))
        return actions
    if kind == "orphan_code_candidate":
        actions.append(_seed("review.seed.code", "Seed code", item, seed_kind="code"))
        actions.append(
            _resolution(
                "review.resolve.data_or_padding",
                "Resolve data/padding",
                item,
                "data_or_padding",
            )
        )
    elif kind == "unreconciled_data_range":
        actions.extend(
            [
                _seed(
                    "review.seed.data.string",
                    "String",
                    item,
                    seed_kind="data",
                    data_role="string",
                    unit="byte",
                    encoding="ascii",
                ),
                _seed(
                    "review.seed.data.scalar_table",
                    "Scalar table",
                    item,
                    seed_kind="data",
                    data_role="scalar_table",
                    unit="word",
                ),
                _seed(
                    "review.seed.data.pointer_table",
                    "Pointer table",
                    item,
                    seed_kind="data",
                    data_role="pointer_table",
                    unit="long",
                ),
                _seed(
                    "review.seed.data.raw",
                    "Raw bytes",
                    item,
                    seed_kind="data",
                    data_role="raw",
                    unit="byte",
                ),
                _resolution("review.resolve.opaque_data", "Opaque data", item, "opaque_data"),
            ]
        )
    elif kind == "suspicious_instruction_decode":
        actions.append(
            _seed("review.seed.data.raw", "Seed data", item, seed_kind="data", data_role="raw", unit="byte")
        )
        actions.append(_resolution("review.resolve.acknowledged", "Acknowledge", item, "acknowledged"))
    elif kind in {"manual_label_unreconciled", "manual_comment_unreconciled"}:
        actions.append(
            _seed("review.seed.data.raw", "Seed data", item, seed_kind="data", data_role="raw", unit="byte")
        )
        if kind == "manual_label_unreconciled":
            actions.append(_label_action("review.label.rename", "Rename label", "rename_manual_label", item))
        actions.append(_log_action("review.remove_annotation", "Remove annotation", "remove_manual_annotation", item))
        actions.append(_resolution("review.resolve.acknowledged", "Acknowledge", item, "acknowledged"))
    elif kind in {"reproduction_mismatch", "unsupported_container_shape"}:
        actions.append(_transient("review.open_reproduction_report", "Open comparison", "open_reproduction_report", item))
        actions.append(
            _transient(
                "review.rerun_round_trip_verification",
                "Rerun round-trip",
                "rerun_round_trip_verification",
                item,
            )
        )
        actions.append(_resolution("review.resolve.acknowledged", "Acknowledge", item, "acknowledged"))
    elif kind in {"manual_seed_conflict", "label_scope_conflict"}:
        if kind == "label_scope_conflict":
            actions.extend(
                [
                    _label_action("review.label.rename", "Rename label", "rename_manual_label", item),
                    _label_action("review.label.change_scope", "Change label scope", "change_label_scope", item),
                    _label_action("review.label.remove", "Remove label", "remove_manual_label", item),
                ]
            )
        label = "Acknowledge blocker" if item.get("review_blocker") is True else "Acknowledge"
        actions.append(_resolution("review.resolve.acknowledged", label, item, "acknowledged"))
    elif not kind.startswith("manual_action_log_"):
        actions.append(_resolution("review.resolve.acknowledged", "Acknowledge", item, "acknowledged"))
    return actions


def target_action_catalog() -> list[dict[str, object]]:
    return [
        _target_transient("target.open_command_palette", "Open Command Palette", "open_command_palette", "p"),
        _target_transient("target.open_review", "Open Review", "open_review", "r"),
        _target_transient("target.open_navigation", "Open Navigate", "open_navigation", "n"),
        _target_transient("target.open_reproduction_report", "Open Reproduction", "open_reproduction_report", None),
        _target_transient("navigation.history_back", "History Back", "history_back", "Alt+Left"),
        _target_transient("navigation.history_forward", "History Forward", "history_forward", "Alt+Right"),
        _target_transient("navigation.follow_reference", "Follow Reference", "follow_reference", "Right"),
        _target_transient("navigation.previous_label", "Previous Label", "previous_label", "Ctrl+Up"),
        _target_transient("navigation.next_label", "Next Label", "next_label", "Ctrl+Down"),
        _target_transient("navigation.previous_hunk", "Previous Hunk", "previous_hunk", None),
        _target_transient("navigation.next_hunk", "Next Hunk", "next_hunk", None),
        _target_transient("listing.selection_up", "Select Previous Row", "selection_up", "Up"),
        _target_transient("listing.selection_down", "Select Next Row", "selection_down", "Down"),
        _target_transient("listing.viewport_page_up", "Page Up", "viewport_page_up", "PageUp"),
        _target_transient("listing.viewport_page_down", "Page Down", "viewport_page_down", "PageDown"),
    ]


def listing_row_action_catalog(row: Mapping[str, object]) -> list[dict[str, object]]:
    context = listing_row_context(row)
    return [
        _context_transient("navigation.follow_reference", "Follow Reference", "follow_reference", context, "Right"),
        _context_log_action(
            "review_note.add",
            "Add review note",
            "add_review_note",
            context,
            {},
            _review_note_parameter_schema(),
        ),
        _context_log_action(
            "review_note.edit",
            "Edit review note",
            "edit_review_note",
            context,
            {},
            _review_note_edit_parameter_schema(),
        ),
        _context_log_action(
            "review_note.clear",
            "Clear review note",
            "clear_review_note",
            context,
            {},
            _review_note_clear_parameter_schema(),
        ),
        _context_log_action(
            "row.seed.code",
            "Seed code",
            "create_manual_seed",
            context,
            {"seed_kind": "code"},
        ),
        _context_log_action(
            "row.seed.data.raw",
            "Raw block",
            "create_manual_seed",
            context,
            {"seed_kind": "data", "data_role": "raw", "unit": "byte"},
        ),
        _context_log_action(
            "row.seed.data.byte",
            "Byte data",
            "create_manual_seed",
            context,
            {"seed_kind": "data", "unit": "byte"},
        ),
        _context_log_action(
            "row.seed.data.word",
            "Word data",
            "create_manual_seed",
            context,
            {"seed_kind": "data", "unit": "word"},
        ),
        _context_log_action(
            "row.seed.data.long",
            "Long data",
            "create_manual_seed",
            context,
            {"seed_kind": "data", "unit": "long"},
        ),
        _context_log_action(
            "row.seed.data.string",
            "String",
            "create_manual_seed",
            context,
            {"seed_kind": "data", "data_role": "string", "unit": "byte", "encoding": "ascii"},
        ),
        _context_log_action(
            "row.seed.data.scalar_table",
            "Scalar table",
            "create_manual_seed",
            context,
            {"seed_kind": "data", "data_role": "scalar_table", "unit": "word"},
        ),
        _context_log_action(
            "row.seed.data.pointer_table",
            "Pointer table",
            "create_manual_seed",
            context,
            {"seed_kind": "data", "data_role": "pointer_table", "unit": "pointer"},
        ),
    ]


def listing_element_action_catalog(
    row: Mapping[str, object],
    element_selector: Mapping[str, object],
) -> list[dict[str, object]]:
    context = selected_listing_element_context(row, element_selector)
    element_kind = str(context.get("element_kind") or "")
    actions = [
        _context_transient("navigation.follow_reference", "Follow Reference", "follow_reference", context, "Right"),
    ]
    if element_kind in {"immediate", "data_literal"}:
        actions.extend(
            [
                _context_log_action(
                    "representation.hex",
                    "Hex",
                    "set_representation",
                    context,
                    {"representation": "hex"},
                ),
                _context_log_action(
                    "representation.binary",
                    "Binary",
                    "set_representation",
                    context,
                    {"representation": "binary"},
                ),
                _context_log_action(
                    "representation.character",
                    "Character",
                    "set_representation",
                    context,
                    {"representation": "character"},
                ),
            ]
        )
    if element_kind == "label":
        actions.append(
            _context_log_action(
                "label.rename",
                "Rename label",
                "create_manual_label",
                context,
                {},
                {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            )
        )
    if _is_structured_a6_lvo_context(context):
        actions.append(
            _context_log_action(
                "semantic.library_base.exec",
                "Treat A6 as exec.library base",
                "create_manual_register_seed",
                context,
                {
                    "register": "A6",
                    "kind": "library_base",
                    "library_name": "exec.library",
                    "struct_name": "LIB",
                    "context_name": "exec.library",
                },
            )
        )
    if element_kind in {"immediate", "data_literal"}:
        actions.extend(_semantic_hint_actions(context))
    return actions


def listing_range_action_catalog(rows: list[Mapping[str, object]]) -> list[dict[str, object]]:
    context = listing_range_context(rows)
    return [
        _context_log_action(
            "range.review_note.add",
            "Add range review note",
            "add_review_note",
            context,
            {},
            _review_note_parameter_schema(),
        ),
        _range_seed_action("range.seed.code", "Seed code", context, rows, {"seed_kind": "code"}, _row_allows_code_seed),
        _range_seed_action(
            "range.seed.data.raw",
            "Raw block",
            context,
            rows,
            {"seed_kind": "data", "data_role": "raw", "unit": "byte"},
            _row_allows_data_seed,
        ),
        _range_seed_action(
            "range.seed.data.byte",
            "Byte data",
            context,
            rows,
            {"seed_kind": "data", "unit": "byte"},
            _row_allows_data_seed,
        ),
        _range_seed_action(
            "range.seed.data.word",
            "Word data",
            context,
            rows,
            {"seed_kind": "data", "unit": "word"},
            _row_allows_data_seed,
        ),
        _range_seed_action(
            "range.seed.data.string",
            "String",
            context,
            rows,
            {"seed_kind": "data", "data_role": "string", "unit": "byte", "encoding": "ascii"},
            _row_allows_data_seed,
        ),
        _range_unavailable_action(
            "range.semantic.helpers",
            "Semantic helpers",
            context,
            "Element-level semantic helpers require one selected operand.",
        ),
    ]


def listing_range_context(rows: list[Mapping[str, object]]) -> dict[str, object]:
    row_contexts = [listing_row_context(row) for row in rows]
    row_indexes = [context["row_index"] for context in row_contexts if isinstance(context.get("row_index"), int)]
    row_ids = [str(row.get("row_id")) for row in rows if isinstance(row.get("row_id"), str) and row.get("row_id")]
    context: dict[str, object] = {
        "kind": "range",
        "row_indexes": row_indexes,
        "row_ids": row_ids,
        "rows": row_contexts,
    }
    if row_indexes:
        context["range_start_row_index"] = min(row_indexes)
        context["range_end_row_index"] = max(row_indexes)
    return context


def listing_range_catalog_manual_payload(
    rows: list[Mapping[str, object]],
    action_id: str,
    *,
    parameters: Mapping[str, object] | None = None,
) -> list[tuple[str, dict[str, object]]]:
    action = _catalog_action(listing_range_action_catalog(rows), action_id)
    if action.get("appends_to_manual_action_log") is not True:
        raise ValueError(f"Catalog action does not append to Manual Action Log: {action_id}")
    if action.get("range_availability") == "unavailable":
        raise ValueError(str(action.get("availability_reason") or "Range action is unavailable"))
    params = dict(_object(action.get("parameters"), "catalog action parameters"))
    if parameters:
        params.update(parameters)
    if action.get("action") == "add_review_note":
        return [("add_review_note", {"note": _range_review_note_payload(rows, params)})]
    subranges = action.get("applicable_subranges")
    if not isinstance(subranges, list) or not subranges:
        raise ValueError("Range action has no explicit applicable subranges")
    results: list[tuple[str, dict[str, object]]] = []
    rows_by_index = {_optional_int(row.get("row_index")): row for row in rows}
    for raw_subrange in subranges:
        if not isinstance(raw_subrange, Mapping):
            continue
        row_indexes = [
            value for value in raw_subrange.get("row_indexes", []) if isinstance(value, int) and not isinstance(value, bool)
        ]
        subrange_rows = [rows_by_index[index] for index in row_indexes if index in rows_by_index]
        if subrange_rows:
            results.append(("create_manual_seed", {"seed": _range_seed_payload(subrange_rows, params)}))
    if not results:
        raise ValueError("Range action has no available selected rows")
    return results


def catalog_entry_by_id(item: Mapping[str, object], action_id: str) -> dict[str, object]:
    for action in review_item_action_catalog(item):
        if action.get("action_id") == action_id:
            return action
    raise ValueError(f"Catalog action is not valid for review item: {action_id}")


def review_item_catalog_manual_payload(
    item: Mapping[str, object],
    action_id: str,
    parameters: Mapping[str, object] | None = None,
) -> tuple[str, dict[str, object]]:
    action = catalog_entry_by_id(item, action_id)
    if action.get("appends_to_manual_action_log") is not True:
        raise ValueError(f"Catalog action does not append to Manual Action Log: {action_id}")
    ui_action = str(action.get("action") or "")
    params = dict(_object(action.get("parameters"), "catalog action parameters"))
    if parameters:
        params.update(parameters)
    if ui_action == "create_manual_seed":
        return "create_manual_seed", {"seed": _seed_payload(item, params)}
    if ui_action == "resolve_review_item":
        disposition = str(params.get("disposition") or "acknowledged")
        return "resolve_review_item", {"resolution": _resolution_payload(item, disposition)}
    if ui_action == "remove_manual_annotation":
        label_id = item.get("label_id")
        comment_id = item.get("comment_id")
        if isinstance(label_id, str) and label_id:
            return "remove_manual_label", {"label_id": label_id}
        if isinstance(comment_id, str) and comment_id:
            return "remove_manual_comment", {"comment_id": comment_id}
        raise ValueError("Review item has no removable manual annotation id")
    if ui_action == "remove_manual_label":
        label_id = _manual_label_id(item, params)
        return "remove_manual_label", {"label_id": label_id}
    if ui_action == "rename_manual_label":
        label_id = _manual_label_id(item, params)
        name = params.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("rename_manual_label requires parameter name")
        return "rename_manual_label", {"label_id": label_id, "name": name.strip()}
    if ui_action == "change_label_scope":
        label_id = _manual_label_id(item, params)
        scope = params.get("scope")
        if scope not in {"global", "local"}:
            raise ValueError("change_label_scope requires scope global or local")
        payload = {"label_id": label_id, "scope": scope}
        owner_id = params.get("owner_id") or params.get("owner_label_id")
        if isinstance(owner_id, str) and owner_id:
            payload["owner_id"] = owner_id
        return "change_label_scope", payload
    if ui_action == "edit_review_note":
        note_id = _review_note_id(item, params)
        payload = _review_note_edit_payload(note_id, params)
        return "edit_review_note", payload
    if ui_action == "clear_review_note":
        note_id = _review_note_id(item, params)
        return "clear_review_note", {"note_id": note_id}
    raise ValueError(f"Catalog action has no Manual Action Log execution: {action_id}")


def listing_catalog_manual_payload(
    row: Mapping[str, object],
    action_id: str,
    *,
    element_context: Mapping[str, object] | None = None,
    parameters: Mapping[str, object] | None = None,
) -> tuple[str, dict[str, object]]:
    actions = (
        listing_element_action_catalog(row, element_context)
        if element_context
        else listing_row_action_catalog(row)
    )
    action = _catalog_action(actions, action_id)
    if action.get("appends_to_manual_action_log") is not True:
        raise ValueError(f"Catalog action does not append to Manual Action Log: {action_id}")
    ui_action = str(action.get("action") or "")
    params = dict(_object(action.get("parameters"), "catalog action parameters"))
    if parameters:
        params.update(parameters)
    if ui_action == "create_manual_seed":
        return "create_manual_seed", {"seed": _row_seed_payload(row, params)}
    if ui_action == "create_manual_register_seed":
        return "create_manual_register_seed", {"register_seed": _register_seed_payload(row, params)}
    if ui_action == "create_manual_label":
        return "create_manual_label", {"label": _row_label_payload(row, element_context, params)}
    if ui_action == "create_manual_semantic_hint":
        return "create_manual_semantic_hint", {"semantic_hint": _semantic_hint_payload(row, element_context, params)}
    if ui_action == "set_representation":
        return "create_manual_representation", {"representation": _representation_payload(row, element_context, params)}
    if ui_action == "add_review_note":
        return "add_review_note", {"note": _row_review_note_payload(row, params)}
    if ui_action == "edit_review_note":
        note_id = _review_note_id(row, params)
        return "edit_review_note", _review_note_edit_payload(note_id, params)
    if ui_action == "clear_review_note":
        return "clear_review_note", {"note_id": _review_note_id(row, params)}
    raise ValueError(f"Catalog action has no Manual Action Log execution: {action_id}")


def _seed_payload(item: Mapping[str, object], params: Mapping[str, object]) -> dict[str, object]:
    addr = _int_field(item, "start", fallback="addr")
    seed_kind = str(params.get("seed_kind") or "data")
    seed: dict[str, object] = {
        "seed_id": f"catalog-{uuid.uuid4().hex}",
        "kind": seed_kind,
        "mode": "required",
        "hunk": _int_field(item, "hunk", default=0),
        "addr": addr,
    }
    end = _optional_int(item.get("end"))
    if end is not None and end > addr:
        seed["end"] = end
    if seed_kind == "data":
        data_role = params.get("data_role")
        unit = params.get("unit")
        if isinstance(data_role, str) and data_role:
            seed["data_role"] = data_role
        if isinstance(unit, str) and unit:
            seed["unit"] = unit
        encoding = params.get("encoding")
        if isinstance(encoding, str) and encoding:
            seed["encoding"] = encoding
    return seed


def _resolution_payload(item: Mapping[str, object], disposition: str) -> dict[str, object]:
    return {
        "resolution_id": f"catalog-{uuid.uuid4().hex}",
        "item_id": str(item.get("item_id") or ""),
        "evidence_fingerprint": str(item.get("evidence_fingerprint") or ""),
        "disposition": disposition,
    }


def _row_seed_payload(row: Mapping[str, object], params: Mapping[str, object]) -> dict[str, object]:
    addr = _int_field(row, "start_offset", fallback="addr")
    seed_kind = str(params.get("seed_kind") or "data")
    seed: dict[str, object] = {
        "seed_id": f"catalog-{uuid.uuid4().hex}",
        "kind": seed_kind,
        "mode": "required",
        "hunk": _int_field(row, "section_index", default=0),
        "addr": addr,
    }
    end = _optional_int(row.get("end_offset"))
    if end is not None and end > addr:
        seed["end"] = end
    if seed_kind == "data":
        data_role = params.get("data_role")
        unit = params.get("unit")
        if isinstance(data_role, str) and data_role:
            seed["data_role"] = data_role
        if isinstance(unit, str) and unit:
            seed["unit"] = unit
        encoding = params.get("encoding")
        if isinstance(encoding, str) and encoding:
            seed["encoding"] = encoding
    return seed


def _review_note_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "body": {"type": "string"},
            "tracking": {"type": "string", "enum": ["note_only", "needs_review"]},
        },
        "required": [],
    }


def _review_note_edit_parameter_schema() -> dict[str, object]:
    schema = _review_note_parameter_schema()
    cast(dict[str, object], schema["properties"])["note_id"] = {"type": "string"}
    cast(list[str], schema["required"]).append("note_id")
    return schema


def _review_note_clear_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {"note_id": {"type": "string"}},
        "required": ["note_id"],
    }


def _review_note_id(item: Mapping[str, object], params: Mapping[str, object]) -> str:
    note_id = params.get("note_id") or item.get("note_id")
    if isinstance(note_id, str) and note_id:
        return note_id
    raise ValueError("note_id parameter is required")


def _review_note_edit_payload(note_id: str, params: Mapping[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {"note_id": note_id}
    if "title" in params:
        title = params.get("title")
        if not isinstance(title, str):
            raise ValueError("review note title must be a string")
        payload["title"] = title
    if "body" in params:
        body = params.get("body")
        if not isinstance(body, str):
            raise ValueError("review note body must be a string")
        payload["body"] = body
    if "tracking" in params:
        tracking = params.get("tracking")
        if tracking not in {"note_only", "needs_review"}:
            raise ValueError("review note tracking must be note_only or needs_review")
        payload["tracking"] = tracking
    if len(payload) == 1:
        raise ValueError("edit_review_note requires title, body, or tracking")
    return payload


def _review_note_text(params: Mapping[str, object], name: str) -> str:
    value = params.get(name)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"review note {name} must be a string")
    return value.strip()


def _review_note_tracking(params: Mapping[str, object]) -> str:
    tracking = params.get("tracking") or "note_only"
    if tracking not in {"note_only", "needs_review"}:
        raise ValueError("review note tracking must be note_only or needs_review")
    return str(tracking)


def _row_review_note_payload(row: Mapping[str, object], params: Mapping[str, object]) -> dict[str, object]:
    addr = _int_field(row, "start_offset", fallback="addr")
    note: dict[str, object] = {
        "note_id": f"catalog-{uuid.uuid4().hex}",
        "target_kind": "row",
        "title": _review_note_text(params, "title"),
        "body": _review_note_text(params, "body"),
        "tracking": _review_note_tracking(params),
        "hunk": _int_field(row, "section_index", default=0),
        "addr": addr,
    }
    end = _optional_int(row.get("end_offset"))
    if end is not None and end > addr:
        note["end"] = end
    row_index = _optional_int(row.get("row_index"))
    if row_index is not None:
        note["row_index"] = row_index
        note["row_indexes"] = [row_index]
    stable_key = row.get("stable_key")
    if isinstance(stable_key, str) and stable_key:
        note["stable_key"] = stable_key
    return note


def _range_review_note_payload(rows: list[Mapping[str, object]], params: Mapping[str, object]) -> dict[str, object]:
    if not rows:
        raise ValueError("range review note requires selected rows")
    first = rows[0]
    last = rows[-1]
    addr = _int_field(first, "start_offset", fallback="addr")
    note: dict[str, object] = {
        "note_id": f"catalog-{uuid.uuid4().hex}",
        "target_kind": "range",
        "title": _review_note_text(params, "title"),
        "body": _review_note_text(params, "body"),
        "tracking": _review_note_tracking(params),
        "hunk": _int_field(first, "section_index", default=0),
        "addr": addr,
        "row_indexes": [
            index for row in rows if (index := _optional_int(row.get("row_index"))) is not None
        ],
    }
    end = _optional_int(last.get("end_offset"))
    if end is None:
        end = _optional_int(last.get("start_offset"))
    if end is None:
        end = _optional_int(last.get("addr"))
    if end is not None and end > addr:
        note["end"] = end
    return note


def _range_seed_payload(rows: list[Mapping[str, object]], params: Mapping[str, object]) -> dict[str, object]:
    first = rows[0]
    last = rows[-1]
    addr = _int_field(first, "start_offset", fallback="addr")
    seed_kind = str(params.get("seed_kind") or "data")
    seed: dict[str, object] = {
        "seed_id": f"catalog-{uuid.uuid4().hex}",
        "kind": seed_kind,
        "mode": "required",
        "hunk": _int_field(first, "section_index", default=0),
        "addr": addr,
        "row_indexes": [
            index for row in rows if (index := _optional_int(row.get("row_index"))) is not None
        ],
    }
    end = _optional_int(last.get("end_offset"))
    if end is None:
        end = _optional_int(last.get("start_offset"))
    if end is None:
        end = _optional_int(last.get("addr"))
    if end is not None and end > addr:
        seed["end"] = end
    if seed_kind == "data":
        data_role = params.get("data_role")
        unit = params.get("unit")
        if isinstance(data_role, str) and data_role:
            seed["data_role"] = data_role
        if isinstance(unit, str) and unit:
            seed["unit"] = unit
        encoding = params.get("encoding")
        if isinstance(encoding, str) and encoding:
            seed["encoding"] = encoding
    return seed


def _row_label_payload(
    row: Mapping[str, object],
    element_context: Mapping[str, object] | None,
    params: Mapping[str, object],
) -> dict[str, object]:
    name = params.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("create_manual_label requires parameter name")
    symbol = element_context.get("symbol") if isinstance(element_context, Mapping) else None
    symbol_text = symbol if isinstance(symbol, str) else ""
    parsed_symbol = _parse_generated_label_symbol(symbol_text)
    address_domain = "runtime" if parsed_symbol is not None and symbol_text.startswith("abs_") else "source"
    hunk = parsed_symbol[0] if parsed_symbol is not None else _int_field(row, "section_index", default=0)
    addr = parsed_symbol[1] if parsed_symbol is not None else _int_field(row, "start_offset", fallback="addr")
    label: dict[str, object] = {
        "label_id": f"catalog-label-{address_domain}-h{hunk}-{addr:08X}",
        "name": name.strip(),
        "scope": "global",
        "address_domain": address_domain,
        "hunk": hunk,
        "addr": addr,
    }
    end = _optional_int(row.get("end_offset"))
    if end is not None and end > addr:
        label["end"] = end
    if isinstance(element_context, Mapping):
        if isinstance(symbol, str) and symbol:
            label["previous_name"] = symbol
        _copy_element_provenance(label, element_context)
    row_index = _optional_int(row.get("row_index"))
    if row_index is not None:
        label["row_index"] = row_index
    stable_key = row.get("stable_key")
    if isinstance(stable_key, str) and stable_key:
        label["stable_key"] = stable_key
    return label


def _parse_generated_label_symbol(symbol: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"(?:loc|abs)_([0-9]+)_([0-9A-Fa-f]{8})", symbol)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2), 16)


def _representation_payload(
    row: Mapping[str, object],
    element_context: Mapping[str, object] | None,
    params: Mapping[str, object],
) -> dict[str, object]:
    style = params.get("representation")
    if style not in {"hex", "binary", "character", "string"}:
        raise ValueError("representation must be hex, binary, character, or string")
    addr = _int_field(row, "start_offset", fallback="addr")
    element_kind = str((element_context or {}).get("element_kind") or "")
    representation: dict[str, object] = {
        "representation_id": f"catalog-{uuid.uuid4().hex}",
        "hunk": _int_field(row, "section_index", default=0),
        "addr": addr,
        "style": style,
        "element_kind": element_kind,
    }
    end = _optional_int(row.get("end_offset"))
    if end is not None and end > addr:
        representation["end"] = end
    row_index = _optional_int(row.get("row_index"))
    if row_index is not None:
        representation["row_index"] = row_index
    stable_key = row.get("stable_key")
    if isinstance(stable_key, str) and stable_key:
        representation["stable_key"] = stable_key
    _copy_element_provenance(representation, element_context)
    return representation


def _register_seed_payload(row: Mapping[str, object], params: Mapping[str, object]) -> dict[str, object]:
    addr = _int_field(row, "start_offset", fallback="addr")
    register_seed: dict[str, object] = {
        "register_seed_id": f"catalog-{uuid.uuid4().hex}",
        "entry_offset": addr,
        "register": str(params.get("register") or "A6"),
        "kind": str(params.get("kind") or "library_base"),
        "library_name": str(params.get("library_name") or "exec.library"),
        "struct_name": str(params.get("struct_name") or "LIB"),
        "context_name": str(params.get("context_name") or ""),
        "note": "Manual semantic helper",
    }
    row_index = _optional_int(row.get("row_index"))
    if row_index is not None:
        register_seed["row_index"] = row_index
    stable_key = row.get("stable_key")
    if isinstance(stable_key, str) and stable_key:
        register_seed["stable_key"] = stable_key
    return register_seed


@lru_cache(maxsize=1)
def _amiga_ndk_payload() -> dict[str, object]:
    return cast(dict[str, object], json.loads(_KNOWLEDGE_PATH.read_text(encoding="utf-8")))


def _semantic_hint_actions(context: Mapping[str, object]) -> list[dict[str, object]]:
    values = element_numeric_values(context)
    if not values:
        return []
    actions: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for value in values:
        for candidate in _semantic_hint_candidates(value):
            domain = str(candidate["domain"])
            symbol = str(candidate["symbol"])
            identity = (domain, symbol)
            if identity in seen:
                continue
            seen.add(identity)
            actions.append(
                _context_log_action(
                    f"semantic.{domain}.{_action_id_token(symbol)}",
                    str(candidate["label"]),
                    "create_manual_semantic_hint",
                    context,
                    {
                        **candidate,
                        "element_id": context.get("element_id"),
                        "element_kind": context.get("element_kind"),
                        "operand_index": context.get("operand_index"),
                    },
                )
            )
    return actions


def _semantic_hint_candidates(value: int) -> tuple[dict[str, object], ...]:
    payload = _amiga_ndk_payload()
    candidates: list[dict[str, object]] = []
    candidates.extend(_equate_candidates(payload, value))
    candidates.extend(_lvo_candidates(payload, value))
    candidates.extend(_struct_offset_candidates(payload, value))
    return tuple(candidates[:12])


def _equate_candidates(payload: Mapping[str, object], value: int) -> list[dict[str, object]]:
    constants = payload.get("constants")
    if not isinstance(constants, dict):
        return []
    candidates: list[dict[str, object]] = []
    for symbol, raw in constants.items():
        if not isinstance(symbol, str) or not isinstance(raw, dict) or raw.get("value") != value:
            continue
        owner = raw.get("owner")
        namespace = ""
        if isinstance(owner, dict):
            namespace = str(owner.get("canonical_include_path") or owner.get("assembler_include_path") or "")
        candidates.append(
            {
                "domain": "equate",
                "symbol": symbol,
                "value": value,
                "namespace": namespace,
                "label": f"Equate {symbol}",
            }
        )
        if len(candidates) >= 4:
            break
    return candidates


def _lvo_candidates(payload: Mapping[str, object], value: int) -> list[dict[str, object]]:
    libraries = payload.get("libraries")
    if not isinstance(libraries, dict):
        return []
    candidates: list[dict[str, object]] = []
    for library_name, library in libraries.items():
        if not isinstance(library_name, str) or not isinstance(library, dict):
            continue
        functions = library.get("functions")
        if not isinstance(functions, dict):
            continue
        for function_name, function in functions.items():
            if isinstance(function_name, str) and isinstance(function, dict) and function.get("lvo") == value:
                symbol = f"{library_name}/{function_name}"
                candidates.append(
                    {
                        "domain": "lvo",
                        "symbol": symbol,
                        "value": value,
                        "namespace": library_name,
                        "function": function_name,
                        "label": f"LVO {library_name} {function_name}",
                    }
                )
                if len(candidates) >= 4:
                    return candidates
    return candidates


def _struct_offset_candidates(payload: Mapping[str, object], value: int) -> list[dict[str, object]]:
    structs = payload.get("structs")
    if not isinstance(structs, dict):
        return []
    candidates: list[dict[str, object]] = []
    for struct_name, struct in structs.items():
        if not isinstance(struct_name, str) or not isinstance(struct, dict):
            continue
        fields = struct.get("fields")
        if not isinstance(fields, list):
            continue
        for field in fields:
            if not isinstance(field, dict) or field.get("offset") != value:
                continue
            field_name = field.get("name")
            if not isinstance(field_name, str):
                continue
            symbol = f"{struct_name}.{field_name}"
            candidates.append(
                {
                    "domain": "struct_offset",
                    "symbol": symbol,
                    "value": value,
                    "namespace": struct_name,
                    "field": field_name,
                    "label": f"Struct {symbol}",
                }
            )
            if len(candidates) >= 4:
                return candidates
    return candidates


def _semantic_hint_payload(
    row: Mapping[str, object],
    element_context: Mapping[str, object] | None,
    params: Mapping[str, object],
) -> dict[str, object]:
    hint = {
        "semantic_hint_id": f"catalog-{uuid.uuid4().hex}",
        "hunk": _int_field(row, "section_index", default=0),
        "addr": _int_field(row, "start_offset", fallback="addr"),
        "element_kind": str((element_context or {}).get("element_kind") or params.get("element_kind") or ""),
        "domain": str(params.get("domain") or ""),
        "symbol": str(params.get("symbol") or ""),
        "value": params.get("value") if isinstance(params.get("value"), int) else 0,
        "namespace": str(params.get("namespace") or ""),
    }
    _copy_element_provenance(hint, element_context)
    for key in ("function", "field"):
        value = params.get(key)
        if isinstance(value, str) and value:
            hint[key] = value
    return hint


def _copy_element_provenance(
    target: dict[str, object],
    element_context: Mapping[str, object] | None,
) -> None:
    if not element_context:
        return
    for key in ("element_id", "operand_index", "value", "signed_value", "width_bits", "width_bytes", "byte_count"):
        value = element_context.get(key)
        if isinstance(value, int) and not isinstance(value, bool) or key == "element_id" and isinstance(value, str) and value:
            target[key] = value


def _is_structured_a6_lvo_context(context: Mapping[str, object]) -> bool:
    base_register = str(context.get("base_register") or context.get("register") or "")
    if base_register.upper() != "A6":
        return False
    symbol = str(context.get("symbol") or "")
    return symbol.startswith("_LVO") or context.get("domain") == "lvo"


def _label_ids(item: Mapping[str, object]) -> tuple[str, ...]:
    raw_ids = item.get("label_ids")
    if isinstance(raw_ids, list):
        ids = tuple(label_id for label_id in raw_ids if isinstance(label_id, str) and label_id)
        if ids:
            return ids
    label_id = item.get("label_id")
    if isinstance(label_id, str) and label_id:
        return (label_id,)
    return ()


def _manual_label_id(item: Mapping[str, object], params: Mapping[str, object]) -> str:
    label_id = params.get("label_id")
    if isinstance(label_id, str) and label_id:
        return label_id
    ids = _label_ids(item)
    if len(ids) == 1:
        return ids[0]
    raise ValueError("label_id parameter is required")


def _label_action(
    action_id: str,
    label: str,
    ui_action: str,
    item: Mapping[str, object],
) -> dict[str, object]:
    parameters: dict[str, object] = {}
    ids = _label_ids(item)
    if len(ids) == 1:
        parameters["label_id"] = ids[0]
    schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "label_id": {"type": "string"},
        },
        "required": [] if len(ids) == 1 else ["label_id"],
    }
    if ui_action == "rename_manual_label":
        cast(dict[str, object], schema["properties"])["name"] = {"type": "string"}
        cast(list[str], schema["required"]).append("name")
    elif ui_action == "change_label_scope":
        properties = cast(dict[str, object], schema["properties"])
        properties["scope"] = {"type": "string", "enum": ["global", "local"]}
        properties["owner_id"] = {"type": "string"}
        cast(list[str], schema["required"]).append("scope")
    return _log_action(action_id, label, ui_action, item, parameters, schema)


def _review_note_action(
    action_id: str,
    label: str,
    ui_action: str,
    item: Mapping[str, object],
) -> dict[str, object]:
    note_id = item.get("note_id")
    parameters: dict[str, object] = {}
    if isinstance(note_id, str) and note_id:
        parameters["note_id"] = note_id
    schema = _review_note_edit_parameter_schema() if ui_action == "edit_review_note" else _review_note_clear_parameter_schema()
    if isinstance(note_id, str) and note_id:
        required = cast(list[str], schema["required"])
        schema["required"] = [field for field in required if field != "note_id"]
    return _log_action(action_id, label, ui_action, item, parameters, schema)


def _action_id_token(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")[:80] or "candidate"


def _catalog_action(actions: list[dict[str, object]], action_id: str) -> dict[str, object]:
    for action in actions:
        if action.get("action_id") == action_id:
            return action
    raise ValueError(f"Catalog action is not valid for context: {action_id}")


def _seed(
    action_id: str,
    label: str,
    item: Mapping[str, object],
    *,
    seed_kind: str,
    data_role: str | None = None,
    unit: str | None = None,
    encoding: str | None = None,
) -> dict[str, object]:
    parameters: dict[str, object] = {"seed_kind": seed_kind}
    if data_role is not None:
        parameters["data_role"] = data_role
    if unit is not None:
        parameters["unit"] = unit
    if encoding is not None:
        parameters["encoding"] = encoding
    return _log_action(action_id, label, "create_manual_seed", item, parameters)


def _resolution(action_id: str, label: str, item: Mapping[str, object], disposition: str) -> dict[str, object]:
    return _log_action(action_id, label, "resolve_review_item", item, {"disposition": disposition})


def _log_action(
    action_id: str,
    label: str,
    ui_action: str,
    item: Mapping[str, object],
    parameters: Mapping[str, object] | None = None,
    parameter_schema: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return _entry(action_id, label, ui_action, item, True, parameters, parameter_schema)


def _transient(action_id: str, label: str, ui_action: str, item: Mapping[str, object]) -> dict[str, object]:
    return _entry(action_id, label, ui_action, item, False, None, None)


def _target_transient(
    action_id: str,
    label: str,
    ui_action: str,
    default_key_binding: str | None,
) -> dict[str, object]:
    return {
        "action_id": action_id,
        "label": label,
        "description": label,
        "enabled": True,
        "target_context": {"kind": "target"},
        "parameter_schema": {"type": "object", "properties": {}, "required": []},
        "default_key_binding": default_key_binding,
        "appends_to_manual_action_log": False,
        "action": ui_action,
        "parameters": {},
    }


def _context_transient(
    action_id: str,
    label: str,
    ui_action: str,
    context: Mapping[str, object],
    default_key_binding: str | None,
) -> dict[str, object]:
    return _context_entry(action_id, label, ui_action, context, False, {}, default_key_binding)


def _context_log_action(
    action_id: str,
    label: str,
    ui_action: str,
    context: Mapping[str, object],
    parameters: Mapping[str, object],
    parameter_schema: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return _context_entry(action_id, label, ui_action, context, True, parameters, None, parameter_schema)


def _range_seed_action(
    action_id: str,
    label: str,
    context: Mapping[str, object],
    rows: list[Mapping[str, object]],
    parameters: Mapping[str, object],
    predicate: Callable[[Mapping[str, object]], bool],
) -> dict[str, object]:
    eligible = [row for row in rows if predicate(row)]
    action = _context_log_action(action_id, label, "create_manual_seed", context, parameters)
    subranges = _contiguous_subranges(eligible)
    if len(eligible) == len(rows):
        action["range_availability"] = "applicable"
        action["availability_reason"] = f"Applies to all {len(rows)} selected rows."
    elif eligible:
        action["range_availability"] = "partial"
        action["availability_reason"] = f"Applies to {len(eligible)} of {len(rows)} selected rows."
    else:
        action["range_availability"] = "unavailable"
        action["availability_reason"] = "No selected rows match this action."
        action["enabled"] = False
    action["applicable_subranges"] = subranges
    action["row_reasons"] = _row_eligibility_reasons(rows, eligible)
    return action


def _range_unavailable_action(
    action_id: str,
    label: str,
    context: Mapping[str, object],
    reason: str,
) -> dict[str, object]:
    action = _context_transient(action_id, label, "unavailable_range_action", context, None)
    action["enabled"] = False
    action["range_availability"] = "unavailable"
    action["availability_reason"] = reason
    action["applicable_subranges"] = []
    return action


def _row_allows_data_seed(row: Mapping[str, object]) -> bool:
    return str(row.get("kind") or "") == "data"


def _row_allows_code_seed(row: Mapping[str, object]) -> bool:
    return str(row.get("kind") or "") in {"instruction", "label"}


def _contiguous_subranges(rows: list[Mapping[str, object]]) -> list[dict[str, object]]:
    subranges: list[dict[str, object]] = []
    current: list[Mapping[str, object]] = []
    previous_index: int | None = None
    for row in rows:
        row_index = _optional_int(row.get("row_index"))
        if row_index is None:
            continue
        if previous_index is None or row_index == previous_index + 1:
            current.append(row)
        else:
            subranges.append(_subrange_payload(current))
            current = [row]
        previous_index = row_index
    if current:
        subranges.append(_subrange_payload(current))
    return subranges


def _subrange_payload(rows: list[Mapping[str, object]]) -> dict[str, object]:
    return {
        "row_indexes": [index for row in rows if (index := _optional_int(row.get("row_index"))) is not None],
        "row_ids": [str(row.get("row_id")) for row in rows if isinstance(row.get("row_id"), str) and row.get("row_id")],
        "start_offset": _optional_int(rows[0].get("start_offset")),
        "end_offset": _optional_int(rows[-1].get("end_offset")),
    }


def _row_eligibility_reasons(
    rows: list[Mapping[str, object]],
    eligible_rows: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    eligible_ids = {id(row) for row in eligible_rows}
    reasons: list[dict[str, object]] = []
    for row in rows:
        applicable = id(row) in eligible_ids
        row_index = _optional_int(row.get("row_index"))
        reasons.append(
            {
                "row_index": row_index,
                "row_id": row.get("row_id"),
                "applicable": applicable,
                "reason": "Selected row matches." if applicable else f"Row kind {row.get('kind') or 'unknown'} is not applicable.",
            }
        )
    return reasons


def _context_entry(
    action_id: str,
    label: str,
    ui_action: str,
    context: Mapping[str, object],
    appends_to_log: bool,
    parameters: Mapping[str, object],
    default_key_binding: str | None,
    parameter_schema: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return {
        "action_id": action_id,
        "label": label,
        "description": label,
        "enabled": True,
        "target_context": dict(context),
        "parameter_schema": dict(parameter_schema or {"type": "object", "properties": {}, "required": []}),
        "default_key_binding": default_key_binding,
        "appends_to_manual_action_log": appends_to_log,
        "action": ui_action,
        "parameters": dict(parameters),
    }


def _entry(
    action_id: str,
    label: str,
    ui_action: str,
    item: Mapping[str, object],
    appends_to_log: bool,
    parameters: Mapping[str, object] | None,
    parameter_schema: Mapping[str, object] | None,
) -> dict[str, object]:
    return {
        "action_id": action_id,
        "label": label,
        "description": label,
        "enabled": True,
        "target_context": {
            "kind": "review_item",
            "item_id": item.get("item_id"),
            "review_item_kind": str(item.get("kind") or ""),
        },
        "parameter_schema": dict(parameter_schema or {"type": "object", "properties": {}, "required": []}),
        "default_key_binding": None,
        "appends_to_manual_action_log": appends_to_log,
        "action": ui_action,
        "parameters": dict(parameters or {}),
    }


def _int_field(
    item: Mapping[str, object],
    name: str,
    *,
    fallback: str | None = None,
    default: int | None = None,
) -> int:
    value = _optional_int(item.get(name))
    if value is not None:
        return value
    if fallback is not None:
        fallback_value = _optional_int(item.get(fallback))
        if fallback_value is not None:
            return fallback_value
    if default is not None:
        return default
    raise ValueError(f"Review item has no integer {name}")


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _object(value: object, description: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{description} is missing")
    return value
