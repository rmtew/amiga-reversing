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
from amiga_reversing.disasm.reproduction import builtin_reproduction_profiles

_KNOWLEDGE_PATH = Path(__file__).resolve().parents[2] / "knowledge" / "amiga_ndk_includes_parsed.json"

_DATA_ROLE_COMMANDS: tuple[dict[str, str], ...] = (
    {"role": "string", "label": "String", "unit": "byte", "encoding": "ascii"},
    {"role": "length_prefixed_string", "label": "Length-prefixed string", "unit": "byte", "encoding": "ascii"},
    {"role": "string_control_stream", "label": "String control stream", "unit": "byte"},
    {"role": "scalar_table", "label": "Scalar table", "unit": "word"},
    {"role": "lookup_table", "label": "Lookup table", "unit": "word"},
    {"role": "pointer_table", "label": "Pointer table", "unit": "pointer"},
    {"role": "copper_list", "label": "Copper list", "unit": "word"},
    {"role": "palette", "label": "Palette", "unit": "word"},
    {"role": "bitmap", "label": "Bitmap", "unit": "byte"},
    {"role": "sound_sample", "label": "Sound sample", "unit": "byte"},
    {"role": "audio_table", "label": "Audio table", "unit": "pointer"},
    {"role": "sprite", "label": "Sprite", "unit": "byte"},
)


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
        actions.extend(_review_data_seed_actions(item))
        actions.append(_resolution("review.resolve.opaque_data", "Opaque data", item, "opaque_data"))
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
        if kind == "manual_seed_conflict":
            actions.append(_seed_remove_action(item))
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
        _target_reproduction_profile_action(),
        _target_source_export_action(),
        _target_equate_action(),
        _target_equate_edit_action(),
        _target_equate_rename_action(),
        _target_equate_remove_action(),
        _target_execution_view_action(),
        _target_execution_view_edit_action(),
        _target_execution_view_remove_action(),
        _target_custom_struct_action(),
        _target_custom_struct_edit_action(),
        _target_custom_struct_rename_action(),
        _target_custom_struct_remove_action(),
        _target_custom_struct_field_action(),
        _target_custom_struct_field_edit_action(),
        _target_custom_struct_field_rename_action(),
        _target_custom_struct_field_remove_action(),
        _target_rsset_layout_region_action(),
        _target_rsset_layout_region_edit_action(),
        _target_rsset_layout_region_rename_action(),
        _target_rsset_layout_region_remove_action(),
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


def target_catalog_manual_payload(
    action_id: str,
    parameters: Mapping[str, object] | None = None,
) -> tuple[str, dict[str, object]]:
    action = _catalog_action(target_action_catalog(), action_id)
    if action.get("appends_to_manual_action_log") is not True:
        raise ValueError(f"Catalog action does not append to Manual Action Log: {action_id}")
    params = dict(_object(action.get("parameters"), "catalog action parameters"))
    if parameters:
        params.update(parameters)
    if action.get("action") == "create_manual_execution_view":
        return "create_manual_execution_view", {"execution_view": _execution_view_payload(params)}
    if action.get("action") == "remove_manual_execution_view":
        return "remove_manual_execution_view", {"execution_view": _execution_view_identity_payload(params)}
    if action.get("action") == "create_manual_target_equate":
        return "create_manual_target_equate", {"target_equate": _target_equate_payload(params)}
    if action.get("action") == "rename_manual_target_equate":
        return "rename_manual_target_equate", {"target_equate": _target_equate_rename_payload(params)}
    if action.get("action") == "remove_manual_target_equate":
        return "remove_manual_target_equate", {"target_equate": _target_equate_identity_payload(params)}
    if action.get("action") == "create_manual_custom_struct":
        return "create_manual_custom_struct", {"custom_struct": _custom_struct_payload(params)}
    if action.get("action") == "rename_manual_custom_struct":
        return "rename_manual_custom_struct", {"custom_struct": _custom_struct_rename_payload(params)}
    if action.get("action") == "remove_manual_custom_struct":
        return "remove_manual_custom_struct", {"custom_struct": _custom_struct_identity_payload(params)}
    if action.get("action") == "create_manual_custom_struct_field":
        return "create_manual_custom_struct_field", {"custom_struct_field": _custom_struct_field_target_payload(params)}
    if action.get("action") == "rename_manual_custom_struct_field":
        return "rename_manual_custom_struct_field", {
            "custom_struct_field": _custom_struct_field_rename_payload(params)
        }
    if action.get("action") == "remove_manual_custom_struct_field":
        return "remove_manual_custom_struct_field", {
            "custom_struct_field": _custom_struct_field_identity_payload(params)
        }
    if action.get("action") == "create_manual_rsset_layout_region":
        return "create_manual_rsset_layout_region", {"rsset_layout_region": _rsset_layout_region_payload(params)}
    if action.get("action") == "remove_manual_rsset_layout_region":
        return "remove_manual_rsset_layout_region", {"rsset_layout_region": _rsset_layout_region_identity_payload(params)}
    raise ValueError(f"Catalog action has no Manual Action Log execution: {action_id}")


def listing_row_action_catalog(row: Mapping[str, object]) -> list[dict[str, object]]:
    context = listing_row_context(row)
    actions = [
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
            "comment.edit",
            "Edit comment",
            "create_manual_comment",
            context,
            {},
            _comment_parameter_schema(),
            ";",
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
            "row.seed.data.named",
            "Name data",
            "create_manual_seed",
            context,
            {"seed_kind": "data", "data_role": "raw", "unit": "byte"},
            _data_name_parameter_schema(),
            "F2",
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
    ]
    actions.extend(_data_symbol_actions(context, row))
    actions.extend(_suppress_seeded_item_actions(context, row))
    actions.extend(_row_data_role_actions(context))
    return actions


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
                    "representation.choose",
                    "Choose representation",
                    "set_representation",
                    context,
                    {},
                    _representation_parameter_schema(),
                    "r",
                ),
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
    if element_kind == "data_literal":
        actions.append(
            _context_log_action(
                "element.seed.data.named",
                "Name data",
                "create_manual_seed",
                context,
                {"seed_kind": "data", "data_role": "raw", "unit": "byte"},
                _data_name_parameter_schema(),
                "F2",
            )
        )
    if element_kind == "data_ref":
        identity = _data_ref_symbol_identity(context)
        if identity is not None:
            actions.append(
                _context_log_action(
                    "data_symbol.rename",
                    "Rename referenced data symbol",
                    "rename_data_symbol",
                    context,
                    identity,
                    _data_name_parameter_schema(),
                    "F2",
                )
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
                "F2",
            )
        )
    if element_kind == "app_slot":
        actions.extend(
            (
                _context_log_action(
                    "app_slot.rename",
                    "Rename app slot",
                    "create_manual_rsset_layout_region",
                    context,
                    _app_slot_region_identity_parameters(context),
                    _app_slot_rename_parameter_schema(),
                    "F2",
                ),
                _context_log_action(
                    "app_slot.edit",
                    "Edit app slot",
                    "create_manual_rsset_layout_region",
                    context,
                    _app_slot_region_identity_parameters(context),
                    _app_slot_rename_parameter_schema(),
                ),
                _context_log_action(
                    "app_slot.remove",
                    "Remove app slot",
                    "remove_manual_rsset_layout_region",
                    context,
                    _app_slot_region_identity_parameters(context),
                    _app_slot_remove_parameter_schema(),
                ),
            )
        )
    if element_kind == "typed_gap":
        actions.extend(
            (
                _context_log_action(
                    "typed_gap.field.add",
                    "Add struct field",
                    "create_manual_custom_struct_field",
                    context,
                    _typed_field_identity_parameters(context),
                    _typed_field_parameter_schema(),
                ),
                _context_log_action(
                    "typed_gap.field.edit",
                    "Edit struct field",
                    "create_manual_custom_struct_field",
                    context,
                    _typed_field_identity_parameters(context),
                    _typed_field_parameter_schema(),
                ),
            )
        )
    if element_kind == "typed_access":
        actions.extend(
            (
                _context_log_action(
                    "typed_access.field.edit",
                    "Edit struct field",
                    "create_manual_custom_struct_field",
                    context,
                    _typed_field_identity_parameters(context),
                    _typed_field_parameter_schema(),
                ),
                _context_log_action(
                    "typed_access.field.rename",
                    "Rename struct field",
                    "rename_manual_custom_struct_field",
                    context,
                    _typed_field_identity_parameters(context),
                    _typed_field_rename_parameter_schema(),
                    "F2",
                ),
                _context_log_action(
                    "typed_access.field.remove",
                    "Remove struct field",
                    "remove_manual_custom_struct_field",
                    context,
                    _typed_field_identity_parameters(context),
                ),
            )
        )
    if element_kind == "register":
        actions.extend(_struct_pointer_actions(context))
    actions.extend(_library_base_actions(context))
    if element_kind in {"immediate", "data_literal"}:
        actions.extend(_semantic_hint_actions(context))
    return actions


def listing_range_action_catalog(rows: list[Mapping[str, object]]) -> list[dict[str, object]]:
    context = listing_range_context(rows)
    actions = [
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
            "range.seed.data.named",
            "Name data",
            context,
            rows,
            {"seed_kind": "data", "data_role": "raw", "unit": "byte"},
            _row_allows_data_seed,
            _data_name_parameter_schema(),
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
            "range.seed.data.long",
            "Long data",
            context,
            rows,
            {"seed_kind": "data", "unit": "long"},
            _row_allows_data_seed,
        ),
    ]
    actions.extend(_range_data_role_actions(context, rows))
    actions.append(
        _range_unavailable_action(
            "range.semantic.helpers",
            "Semantic helpers",
            context,
            "Element-level semantic helpers require one selected operand.",
        )
    )
    return actions


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


def _data_role_parameters(spec: Mapping[str, str]) -> dict[str, object]:
    parameters: dict[str, object] = {
        "seed_kind": "data",
        "data_role": spec["role"],
        "unit": spec["unit"],
    }
    encoding = spec.get("encoding")
    if encoding:
        parameters["encoding"] = encoding
    return parameters


def _review_data_seed_actions(item: Mapping[str, object]) -> list[dict[str, object]]:
    actions = [
        _seed("review.seed.data.raw", "Raw bytes", item, seed_kind="data", data_role="raw", unit="byte"),
        _seed(
            "review.seed.data.named",
            "Name data",
            item,
            seed_kind="data",
            data_role="raw",
            unit="byte",
            parameter_schema=_data_name_parameter_schema(),
        ),
    ]
    actions.extend(
        _seed(
            f"review.seed.data.{spec['role']}",
            spec["label"],
            item,
            seed_kind="data",
            data_role=spec["role"],
            unit=spec["unit"],
            encoding=spec.get("encoding"),
        )
        for spec in _DATA_ROLE_COMMANDS
    )
    return actions


def _row_data_role_actions(context: Mapping[str, object]) -> list[dict[str, object]]:
    return [
        _context_log_action(
            f"row.seed.data.{spec['role']}",
            spec["label"],
            "create_manual_seed",
            context,
            _data_role_parameters(spec),
        )
        for spec in _DATA_ROLE_COMMANDS
    ]


def _range_data_role_actions(context: Mapping[str, object], rows: list[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        _range_seed_action(
            f"range.seed.data.{spec['role']}",
            spec["label"],
            context,
            rows,
            _data_role_parameters(spec),
            _row_allows_data_seed,
        )
        for spec in _DATA_ROLE_COMMANDS
    ]


def _suppress_seeded_item_actions(context: Mapping[str, object], row: Mapping[str, object]) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    for item in _row_suppressible_seeded_items(row):
        kind = item["kind"]
        label = {
            "seeded_entity": "Suppress seeded data",
            "seeded_code_label": "Suppress seeded label",
            "seeded_code_entrypoint": "Suppress seeded entrypoint",
        }.get(kind, "Suppress seeded item")
        actions.append(
            _context_log_action(
                f"correction.suppress_seeded_item.{kind}",
                label,
                "suppress_seeded_item",
                context,
                {"kind": kind, "hunk": item["hunk"], "addr": item["addr"]},
            )
        )
    return actions


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
    if ui_action == "remove_manual_seed":
        return "remove_manual_seed", {"seed_id": _manual_seed_id(item, params)}
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
    if ui_action == "rename_data_symbol":
        return "rename_data_symbol", {"data_symbol": _data_symbol_payload(row, params)}
    if ui_action == "create_manual_label":
        manual_label_id = row.get("manual_label_id")
        name = params.get("name")
        if isinstance(manual_label_id, str) and manual_label_id and isinstance(name, str) and name.strip():
            return "rename_manual_label", {"label_id": manual_label_id, "name": name.strip()}
        return "create_manual_label", {"label": _row_label_payload(row, element_context, params)}
    if ui_action == "create_manual_comment":
        return "create_manual_comment", {"comment": _row_comment_payload(row, params)}
    if ui_action == "create_manual_semantic_hint":
        return "create_manual_semantic_hint", {"semantic_hint": _semantic_hint_payload(row, element_context, params)}
    if ui_action == "create_manual_rsset_layout_region":
        if not element_context or element_context.get("element_kind") != "app_slot":
            raise ValueError("create_manual_rsset_layout_region requires an app-slot element context")
        return "create_manual_rsset_layout_region", {"rsset_layout_region": _app_slot_region_payload(element_context, params)}
    if ui_action == "remove_manual_rsset_layout_region":
        if not element_context or element_context.get("element_kind") != "app_slot":
            raise ValueError("remove_manual_rsset_layout_region requires an app-slot element context")
        return "remove_manual_rsset_layout_region", {"rsset_layout_region": _rsset_layout_region_identity_payload(params)}
    if ui_action == "create_manual_custom_struct_field":
        if not element_context or element_context.get("element_kind") not in {"typed_access", "typed_gap"}:
            raise ValueError("create_manual_custom_struct_field requires a typed element context")
        return "create_manual_custom_struct_field", {"custom_struct_field": _custom_struct_field_target_payload(params)}
    if ui_action == "rename_manual_custom_struct_field":
        if not element_context or element_context.get("element_kind") != "typed_access":
            raise ValueError("rename_manual_custom_struct_field requires a typed-access element context")
        return "rename_manual_custom_struct_field", {"custom_struct_field": _custom_struct_field_rename_payload(params)}
    if ui_action == "remove_manual_custom_struct_field":
        if not element_context or element_context.get("element_kind") != "typed_access":
            raise ValueError("remove_manual_custom_struct_field requires a typed-access element context")
        return "remove_manual_custom_struct_field", {"custom_struct_field": _custom_struct_field_identity_payload(params)}
    if ui_action == "set_representation":
        return "create_manual_representation", {"representation": _representation_payload(row, element_context, params)}
    if ui_action == "add_review_note":
        return "add_review_note", {"note": _row_review_note_payload(row, params)}
    if ui_action == "edit_review_note":
        note_id = _review_note_id(row, params)
        return "edit_review_note", _review_note_edit_payload(note_id, params)
    if ui_action == "clear_review_note":
        return "clear_review_note", {"note_id": _review_note_id(row, params)}
    if ui_action == "suppress_seeded_item":
        return "suppress_seeded_item", {"suppressed_seeded_item": _suppressed_seeded_item_payload(row, params)}
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
        name = _data_seed_name(params)
        if name is not None:
            seed["name"] = name
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
        name = _data_seed_name(params)
        if name is not None:
            seed["name"] = name
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


def _row_suppressible_seeded_items(row: Mapping[str, object]) -> list[dict[str, object]]:
    raw_items = row.get("suppressible_seeded_items")
    if not isinstance(raw_items, list | tuple):
        return []
    items: list[dict[str, object]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, Mapping):
            continue
        kind = raw_item.get("kind")
        hunk = _optional_int(raw_item.get("hunk"))
        addr = _optional_int(raw_item.get("addr"))
        if kind not in {"seeded_entity", "seeded_code_label", "seeded_code_entrypoint"}:
            continue
        if hunk is None or addr is None:
            continue
        item = {"kind": kind, "hunk": hunk, "addr": addr}
        end = _optional_int(raw_item.get("end"))
        if end is not None:
            item["end"] = end
        name = raw_item.get("name")
        if isinstance(name, str) and name:
            item["name"] = name
        source_locator = raw_item.get("source_locator")
        if isinstance(source_locator, str) and source_locator:
            item["source_locator"] = source_locator
        items.append(item)
    return items


def _data_symbol_actions(context: Mapping[str, object], row: Mapping[str, object]) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    has_seeded_entity = False
    for item in _row_suppressible_seeded_items(row):
        if item["kind"] != "seeded_entity":
            continue
        has_seeded_entity = True
        actions.append(
            _context_log_action(
                "data_symbol.rename",
                "Rename data symbol",
                "rename_data_symbol",
                context,
                {
                    "hunk": item["hunk"],
                    "addr": item["addr"],
                    **({"end": item["end"]} if "end" in item else {}),
                    **({"previous_name": item["name"]} if "name" in item else {}),
                    **({"source_locator": item["source_locator"]} if "source_locator" in item else {}),
                },
                _data_name_parameter_schema(),
                "F2",
            )
        )
        actions.append(
            _context_log_action(
                "data_symbol.remove",
                "Remove data symbol",
                "suppress_seeded_item",
                context,
                {"kind": item["kind"], "hunk": item["hunk"], "addr": item["addr"]},
            )
        )
    if not has_seeded_entity and row.get("kind") == "data":
        identity = _row_data_symbol_identity(row)
        if identity is not None:
            actions.append(
                _context_log_action(
                    "data_symbol.rename",
                    "Rename data symbol",
                    "rename_data_symbol",
                    context,
                    identity,
                    _data_name_parameter_schema(),
                    "F2",
                )
            )
    return actions


def _row_data_symbol_identity(row: Mapping[str, object]) -> dict[str, object] | None:
    hunk = _optional_int(row.get("section_index"))
    if hunk is None:
        hunk = _optional_int(row.get("hunk"))
    addr = _optional_int(row.get("start_offset"))
    if addr is None:
        addr = _optional_int(row.get("addr"))
    if hunk is None or addr is None:
        return None
    identity: dict[str, object] = {"hunk": hunk, "addr": addr}
    end = _optional_int(row.get("end_offset"))
    if end is None:
        end = _optional_int(row.get("end"))
    if end is not None and end > addr:
        identity["end"] = end
    label = row.get("label")
    if isinstance(label, str) and label:
        identity["previous_name"] = label
    return identity


def _data_ref_symbol_identity(context: Mapping[str, object]) -> dict[str, object] | None:
    hunk = _optional_int(context.get("target_hunk"))
    addr = _optional_int(context.get("target_addr"))
    if hunk is None or addr is None:
        return None
    identity: dict[str, object] = {"source": "data_ref", "hunk": hunk, "addr": addr}
    end = _optional_int(context.get("target_end"))
    if end is not None and end > addr:
        identity["end"] = end
    data_class = context.get("data_class")
    if isinstance(data_class, str) and data_class:
        identity["data_class"] = data_class
    return identity


def _data_symbol_payload(row: Mapping[str, object], params: Mapping[str, object]) -> dict[str, object]:
    hunk = _optional_int(params.get("hunk"))
    addr = _optional_int(params.get("addr"))
    if hunk is None or addr is None:
        raise ValueError("rename_data_symbol requires hunk and addr")
    for item in _row_suppressible_seeded_items(row):
        if item["kind"] == "seeded_entity" and item["hunk"] == hunk and item["addr"] == addr:
            name = _data_seed_name(params)
            if name is None:
                raise ValueError("rename_data_symbol requires parameter name")
            symbol: dict[str, object] = {
                "data_symbol_id": f"data-symbol:h{hunk}:{addr:08X}",
                "hunk": hunk,
                "addr": addr,
                "name": name,
            }
            if "end" in item:
                symbol["end"] = item["end"]
            if "name" in item:
                symbol["previous_name"] = item["name"]
            if "source_locator" in item:
                symbol["source_locator"] = item["source_locator"]
            return symbol
    if row.get("kind") == "data" or params.get("source") == "data_ref":
        name = _data_seed_name(params)
        if name is None:
            raise ValueError("rename_data_symbol requires parameter name")
        symbol = {
            "data_symbol_id": f"data-symbol:h{hunk}:{addr:08X}",
            "hunk": hunk,
            "addr": addr,
            "name": name,
        }
        end = _optional_int(params.get("end"))
        if end is not None and end > addr:
            symbol["end"] = end
        previous_name = params.get("previous_name")
        if isinstance(previous_name, str) and previous_name:
            symbol["previous_name"] = previous_name
        data_class = params.get("data_class")
        if isinstance(data_class, str) and data_class:
            symbol["data_class"] = data_class
        return symbol
    raise ValueError("rename_data_symbol requires a data row, data ref, or seeded data entity on the selected row")


def _suppressed_seeded_item_payload(row: Mapping[str, object], params: Mapping[str, object]) -> dict[str, object]:
    kind = params.get("kind")
    hunk = _optional_int(params.get("hunk"))
    addr = _optional_int(params.get("addr"))
    for item in _row_suppressible_seeded_items(row):
        if item["kind"] == kind and item["hunk"] == hunk and item["addr"] == addr:
            return {"kind": item["kind"], "hunk": item["hunk"], "addr": item["addr"]}
    raise ValueError("suppress_seeded_item requires a suppressible seeded item on the selected row")


def _execution_view_payload(params: Mapping[str, object]) -> dict[str, object]:
    source_start = _optional_int(params.get("source_start"))
    source_end = _optional_int(params.get("source_end"))
    base_addr = _optional_int(params.get("base_addr"))
    name = params.get("name")
    if source_start is None or source_end is None or base_addr is None:
        raise ValueError("create_manual_execution_view requires source_start, source_end, and base_addr")
    if source_start < 0 or source_end <= source_start or base_addr < 0:
        raise ValueError("create_manual_execution_view has invalid source/runtime range")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("create_manual_execution_view requires parameter name")
    view: dict[str, object] = {
        "execution_view_id": f"catalog-execution-view-{source_start:08X}-{source_end:08X}-{base_addr:08X}",
        "source_start": source_start,
        "source_end": source_end,
        "base_addr": base_addr,
        "name": name.strip(),
    }
    comment = params.get("comment")
    if isinstance(comment, str) and comment.strip():
        view["comment"] = comment.strip()
    return view


def _execution_view_identity_payload(params: Mapping[str, object]) -> dict[str, object]:
    source_start = _optional_int(params.get("source_start"))
    source_end = _optional_int(params.get("source_end"))
    base_addr = _optional_int(params.get("base_addr"))
    if source_start is None or source_end is None or base_addr is None:
        raise ValueError("remove_manual_execution_view requires source_start, source_end, and base_addr")
    if source_start < 0 or source_end <= source_start or base_addr < 0:
        raise ValueError("remove_manual_execution_view has invalid source/runtime range")
    return {
        "source_start": source_start,
        "source_end": source_end,
        "base_addr": base_addr,
    }


def _target_equate_payload(params: Mapping[str, object]) -> dict[str, object]:
    name = str(params.get("name") or "").strip()
    value = _optional_int(params.get("value"))
    if not name:
        raise ValueError("create_manual_target_equate requires parameter name")
    if value is None:
        raise ValueError("create_manual_target_equate requires value")
    equate: dict[str, object] = {
        "target_equate_id": f"catalog-target-equate-{_action_id_token(name)}",
        "name": name,
        "value": value,
    }
    comment = params.get("comment")
    if isinstance(comment, str) and comment.strip():
        equate["comment"] = comment.strip()
    return equate


def _target_equate_identity_payload(params: Mapping[str, object]) -> dict[str, object]:
    name = str(params.get("name") or "").strip()
    if not name:
        raise ValueError("remove_manual_target_equate requires parameter name")
    return {"target_equate_id": f"catalog-target-equate-{_action_id_token(name)}", "name": name}


def _target_equate_rename_payload(params: Mapping[str, object]) -> dict[str, object]:
    previous_name = str(params.get("previous_name") or "").strip()
    name = str(params.get("name") or "").strip()
    if not previous_name:
        raise ValueError("rename_manual_target_equate requires parameter previous_name")
    if not name:
        raise ValueError("rename_manual_target_equate requires parameter name")
    return {
        "target_equate_id": f"catalog-target-equate-{_action_id_token(previous_name)}",
        "previous_name": previous_name,
        "name": name,
    }


def _custom_struct_field_payload(field: Mapping[str, object]) -> dict[str, object]:
    name = field.get("name")
    field_type = field.get("type")
    offset = _optional_int(field.get("offset"))
    size = _optional_int(field.get("size"))
    if not isinstance(name, str) or not name.strip():
        raise ValueError("create_manual_custom_struct field requires name")
    if not isinstance(field_type, str) or not field_type.strip():
        raise ValueError("create_manual_custom_struct field requires type")
    if offset is None or offset < 0:
        raise ValueError("create_manual_custom_struct field requires offset")
    if size is None or size <= 0:
        raise ValueError("create_manual_custom_struct field requires size")
    payload: dict[str, object] = {
        "name": name.strip(),
        "type": field_type.strip(),
        "offset": offset,
        "size": size,
    }
    for field_name in ("available_since", "struct", "pointer_struct", "named_base"):
        value = field.get(field_name)
        if isinstance(value, str) and value.strip():
            payload[field_name] = value.strip()
    return payload


def _custom_struct_payload(params: Mapping[str, object]) -> dict[str, object]:
    name = params.get("name")
    size = _optional_int(params.get("size"))
    if not isinstance(name, str) or not name.strip():
        raise ValueError("create_manual_custom_struct requires parameter name")
    if size is None or size <= 0:
        raise ValueError("create_manual_custom_struct requires size")
    raw_fields = params.get("fields", ())
    if raw_fields is None:
        raw_fields = ()
    if not isinstance(raw_fields, list | tuple):
        raise ValueError("create_manual_custom_struct fields must be an array")
    fields = [
        _custom_struct_field_payload(field)
        for field in raw_fields
        if isinstance(field, Mapping)
    ]
    struct: dict[str, object] = {
        "name": name.strip(),
        "size": size,
        "fields": fields,
    }
    if len(fields) != len(raw_fields):
        raise ValueError("create_manual_custom_struct fields must be objects")
    base_offset = _optional_int(params.get("base_offset"))
    if base_offset is not None:
        struct["base_offset"] = base_offset
    for field_name in ("base_struct", "available_since"):
        value = params.get(field_name)
        if isinstance(value, str) and value.strip():
            struct[field_name] = value.strip()
    return struct


def _custom_struct_identity_payload(params: Mapping[str, object]) -> dict[str, object]:
    name = params.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("remove_manual_custom_struct requires parameter name")
    return {"name": name.strip()}


def _custom_struct_rename_payload(params: Mapping[str, object]) -> dict[str, object]:
    previous_name = params.get("previous_name")
    name = params.get("name")
    if not isinstance(previous_name, str) or not previous_name.strip():
        raise ValueError("rename_manual_custom_struct requires parameter previous_name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("rename_manual_custom_struct requires parameter name")
    return {"previous_name": previous_name.strip(), "name": name.strip()}


def _custom_struct_field_target_payload(params: Mapping[str, object]) -> dict[str, object]:
    struct_name = params.get("struct_name")
    if not isinstance(struct_name, str) or not struct_name.strip():
        raise ValueError("create_manual_custom_struct_field requires parameter struct_name")
    field = _custom_struct_field_payload(params)
    field["struct_name"] = struct_name.strip()
    return field


def _custom_struct_field_rename_payload(params: Mapping[str, object]) -> dict[str, object]:
    field = _custom_struct_field_identity_payload(params)
    name = params.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("rename_manual_custom_struct_field requires parameter name")
    field["name"] = name.strip()
    return field


def _custom_struct_field_identity_payload(params: Mapping[str, object]) -> dict[str, object]:
    struct_name = params.get("struct_name")
    offset = _optional_int(params.get("offset"))
    if not isinstance(struct_name, str) or not struct_name.strip():
        raise ValueError("remove_manual_custom_struct_field requires parameter struct_name")
    if offset is None or offset < 0:
        raise ValueError("remove_manual_custom_struct_field requires offset")
    field: dict[str, object] = {"struct_name": struct_name.strip(), "offset": offset}
    name = params.get("name")
    if isinstance(name, str) and name.strip():
        field["name"] = name.strip()
    return field


def _rsset_layout_region_payload(params: Mapping[str, object]) -> dict[str, object]:
    offset = _optional_int(params.get("offset"))
    size = _optional_int(params.get("size"))
    symbol = params.get("symbol")
    if offset is None or offset < 0 or offset > 0x7FFF:
        raise ValueError("create_manual_rsset_layout_region requires offset in range")
    if size is not None and (size <= 0 or size > 255):
        raise ValueError("create_manual_rsset_layout_region size must be 1..255")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("create_manual_rsset_layout_region requires parameter symbol")
    layout_name = str(params.get("layout_name") or "app").strip() or "app"
    region: dict[str, object] = {
        "rsset_layout_region_id": f"catalog-rsset-region-{layout_name}-{offset:04X}",
        "offset": offset,
        "symbol": symbol.strip(),
    }
    if size is not None:
        region["size"] = size
    for field_name in (
        "layout_name",
        "base_symbol",
        "sizeof_symbol",
        "struct_name",
        "pointer_struct",
        "storage_kind",
        "semantic_type",
        "parser_role",
        "parser_routine",
    ):
        value = params.get(field_name)
        if isinstance(value, str) and value.strip():
            region[field_name] = value.strip()
    parse_order = _optional_int(params.get("parse_order"))
    if parse_order is not None:
        region["parse_order"] = parse_order
    return region


def _rsset_layout_region_identity_payload(params: Mapping[str, object]) -> dict[str, object]:
    offset = _optional_int(params.get("offset"))
    if offset is None or offset < 0 or offset > 0x7FFF:
        raise ValueError("remove_manual_rsset_layout_region requires offset in range")
    region: dict[str, object] = {"offset": offset}
    for field_name in ("layout_name", "base_symbol"):
        value = params.get(field_name)
        if isinstance(value, str) and value.strip():
            region[field_name] = value.strip()
    return region


def _app_slot_region_identity_parameters(context: Mapping[str, object]) -> dict[str, object]:
    displacement = _optional_int(context.get("displacement"))
    params: dict[str, object] = {}
    if displacement is not None:
        params["offset"] = displacement
    symbol = context.get("symbol")
    if isinstance(symbol, str) and symbol:
        params["previous_symbol"] = symbol
    return params


def _app_slot_region_payload(context: Mapping[str, object], params: Mapping[str, object]) -> dict[str, object]:
    offset = _optional_int(params.get("offset"))
    size = _optional_int(params.get("size"))
    symbol = params.get("symbol") or params.get("name")
    if offset is None or offset < 0 or offset > 0x7FFF:
        raise ValueError("app_slot.rename requires app-slot displacement")
    if size is None or size <= 0 or size > 255:
        raise ValueError("app_slot.rename requires size 1..255")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("app_slot.rename requires parameter symbol")
    region: dict[str, object] = {
        "rsset_layout_region_id": f"catalog-rsset-region-app-{offset:04X}",
        "offset": offset,
        "size": size,
        "symbol": symbol.strip(),
    }
    for field_name in (
        "layout_name",
        "base_symbol",
        "sizeof_symbol",
        "storage_kind",
        "semantic_type",
        "parser_role",
        "parser_routine",
    ):
        value = params.get(field_name)
        if isinstance(value, str) and value.strip():
            region[field_name] = value.strip()
    parse_order = _optional_int(params.get("parse_order"))
    if parse_order is not None:
        region["parse_order"] = parse_order
    return region


def _typed_field_identity_parameters(context: Mapping[str, object]) -> dict[str, object]:
    struct_name = (
        context.get("owner_struct_name")
        or context.get("refined_struct_name")
        or context.get("container_struct_name")
        or context.get("root_struct_name")
    )
    offset = _optional_int(context.get("field_offset"))
    if offset is None:
        offset = _optional_int(context.get("displacement"))
    params: dict[str, object] = {}
    if isinstance(struct_name, str) and struct_name.strip():
        params["struct_name"] = struct_name.strip()
    if offset is not None:
        params["offset"] = offset
    field_name = context.get("field_name")
    if isinstance(field_name, str) and field_name.strip():
        params["name"] = field_name.strip()
    return params


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


def _comment_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
        },
        "required": ["text"],
    }


def _data_name_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }


def _app_slot_rename_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "size": {"type": "integer", "minimum": 1, "maximum": 255},
            "storage_kind": {
                "type": "string",
                "enum": ["scalar", "pointer", "struct_instance", "struct_pointer"],
            },
            "semantic_type": {"type": "string"},
            "parser_role": {"type": "string"},
            "parser_routine": {"type": "string"},
            "parse_order": {"type": "integer", "minimum": 0},
        },
        "required": ["symbol", "size"],
    }


def _app_slot_remove_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "layout_name": {"type": "string"},
            "base_symbol": {"type": "string"},
        },
        "required": [],
    }


def _typed_field_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string"},
            "size": {"type": "integer", "minimum": 1},
            "struct": {"type": "string"},
            "pointer_struct": {"type": "string"},
            "named_base": {"type": "string"},
        },
        "required": ["name", "type", "size"],
    }


def _typed_field_rename_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }


def _seed_id_parameter_schema(seed_ids: list[str]) -> dict[str, object]:
    property_schema: dict[str, object] = {"type": "string"}
    if seed_ids:
        property_schema["enum"] = seed_ids
    return {
        "type": "object",
        "properties": {"seed_id": property_schema},
        "required": ["seed_id"],
    }


def _representation_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "representation": {"type": "string", "enum": ["hex", "binary", "character"]},
        },
        "required": ["representation"],
    }


def _execution_view_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "source_start": {"type": "integer", "minimum": 0},
            "source_end": {"type": "integer", "minimum": 1},
            "base_addr": {"type": "integer", "minimum": 0},
            "name": {"type": "string"},
            "comment": {"type": "string"},
        },
        "required": ["source_start", "source_end", "base_addr", "name"],
    }


def _target_equate_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "integer"},
            "comment": {"type": "string"},
        },
        "required": ["name", "value"],
    }


def _target_equate_identity_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }


def _target_equate_rename_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "previous_name": {"type": "string"},
            "name": {"type": "string"},
        },
        "required": ["previous_name", "name"],
    }


def _execution_view_identity_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "source_start": {"type": "integer", "minimum": 0},
            "source_end": {"type": "integer", "minimum": 1},
            "base_addr": {"type": "integer", "minimum": 0},
        },
        "required": ["source_start", "source_end", "base_addr"],
    }


def _custom_struct_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "size": {"type": "integer", "minimum": 1},
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "offset": {"type": "integer", "minimum": 0},
                        "size": {"type": "integer", "minimum": 1},
                        "available_since": {"type": "string", "default": "1.0"},
                        "struct": {"type": "string"},
                        "pointer_struct": {"type": "string"},
                        "named_base": {"type": "string"},
                    },
                    "required": ["name", "type", "offset", "size"],
                },
            },
            "base_offset": {"type": "integer", "default": 0},
            "base_struct": {"type": "string"},
            "available_since": {"type": "string", "default": "1.0"},
        },
        "required": ["name", "size"],
    }


def _custom_struct_identity_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }


def _custom_struct_rename_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "previous_name": {"type": "string"},
            "name": {"type": "string"},
        },
        "required": ["previous_name", "name"],
    }


def _custom_struct_field_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "struct_name": {"type": "string"},
            "name": {"type": "string"},
            "type": {"type": "string"},
            "offset": {"type": "integer", "minimum": 0},
            "size": {"type": "integer", "minimum": 1},
            "available_since": {"type": "string", "default": "1.0"},
            "struct": {"type": "string"},
            "pointer_struct": {"type": "string"},
            "named_base": {"type": "string"},
        },
        "required": ["struct_name", "name", "type", "offset", "size"],
    }


def _custom_struct_field_identity_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "struct_name": {"type": "string"},
            "offset": {"type": "integer", "minimum": 0},
            "name": {"type": "string"},
        },
        "required": ["struct_name", "offset"],
    }


def _custom_struct_field_rename_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "struct_name": {"type": "string"},
            "offset": {"type": "integer", "minimum": 0},
            "name": {"type": "string"},
        },
        "required": ["struct_name", "offset", "name"],
    }


def _rsset_layout_region_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "offset": {"type": "integer", "minimum": 0},
            "size": {"type": "integer", "minimum": 1, "maximum": 255},
            "symbol": {"type": "string"},
            "layout_name": {"type": "string", "default": "app"},
            "base_symbol": {"type": "string"},
            "sizeof_symbol": {"type": "string"},
            "struct_name": {"type": "string"},
            "pointer_struct": {"type": "string"},
            "storage_kind": {
                "type": "string",
                "enum": ["scalar", "pointer", "struct_instance", "struct_pointer"],
            },
            "semantic_type": {"type": "string"},
            "parser_role": {"type": "string"},
            "parser_routine": {"type": "string"},
            "parse_order": {"type": "integer", "minimum": 0},
        },
        "required": ["offset", "symbol"],
    }


def _rsset_layout_region_identity_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "offset": {"type": "integer", "minimum": 0},
            "layout_name": {"type": "string", "default": "app"},
            "base_symbol": {"type": "string"},
        },
        "required": ["offset"],
    }


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


def _manual_seed_ids(item: Mapping[str, object]) -> list[str]:
    raw_seed_ids = item.get("seed_ids")
    if isinstance(raw_seed_ids, list | tuple):
        return [seed_id for seed_id in raw_seed_ids if isinstance(seed_id, str) and seed_id]
    seed_id = item.get("seed_id")
    if isinstance(seed_id, str) and seed_id:
        return [seed_id]
    return []


def _manual_seed_id(item: Mapping[str, object], params: Mapping[str, object]) -> str:
    seed_id = params.get("seed_id")
    if isinstance(seed_id, str) and seed_id:
        return seed_id
    seed_ids = _manual_seed_ids(item)
    if len(seed_ids) == 1:
        return seed_ids[0]
    raise ValueError("seed_id parameter is required")


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


def _row_comment_payload(row: Mapping[str, object], params: Mapping[str, object]) -> dict[str, object]:
    text = params.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("create_manual_comment requires parameter text")
    addr = _int_field(row, "start_offset", fallback="addr")
    hunk = _int_field(row, "section_index", default=0)
    comment: dict[str, object] = {
        "comment_id": f"catalog-comment-{_row_identity_token(row, hunk, addr)}",
        "text": text.strip(),
        "hunk": hunk,
        "addr": addr,
    }
    end = _optional_int(row.get("end_offset"))
    if end is not None and end > addr:
        comment["end"] = end
    row_index = _optional_int(row.get("row_index"))
    if row_index is not None:
        comment["row_index"] = row_index
    stable_key = row.get("stable_key")
    if isinstance(stable_key, str) and stable_key:
        comment["stable_key"] = stable_key
    return comment


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
        name = _data_seed_name(params)
        if name is not None:
            seed["name"] = name
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


def _data_seed_name(params: Mapping[str, object]) -> str | None:
    if "name" not in params:
        return None
    name = params.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("create_manual_seed requires parameter name")
    return name.strip()


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
    if parsed_symbol is not None:
        addr = parsed_symbol[1]
    else:
        addr = _int_field(row, "start_offset", fallback="addr")
    label: dict[str, object] = {
        "label_id": f"catalog-label-{address_domain}-{_row_identity_token(row, hunk, addr)}",
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


def _row_identity_token(row: Mapping[str, object], hunk: int, addr: int) -> str:
    stable_key = row.get("stable_key")
    if isinstance(stable_key, str) and stable_key:
        return f"h{hunk}-{addr:08X}-sk-{_id_token(stable_key)}"
    row_id = row.get("row_id")
    if isinstance(row_id, str) and row_id:
        return f"h{hunk}-{addr:08X}-row-{_id_token(row_id)}"
    row_index = _optional_int(row.get("row_index"))
    if row_index is not None:
        return f"h{hunk}-{addr:08X}-idx-{row_index}"
    return f"h{hunk}-{addr:08X}"


def _id_token(value: str) -> str:
    token = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value.strip())
    return token or "unnamed"


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
    kind = str(params.get("kind") or "library_base")
    library_name = params.get("library_name")
    struct_name = params.get("struct_name")
    context_name = params.get("context_name")
    library_name_value = library_name if isinstance(library_name, str) else None
    struct_name_value = struct_name if isinstance(struct_name, str) else None
    context_name_value = context_name if isinstance(context_name, str) else None
    if kind != "struct_ptr":
        library_name_value = library_name_value or "exec.library"
        struct_name_value = struct_name_value or "LIB"
        context_name_value = context_name_value or ""
    register_seed: dict[str, object] = {
        "register_seed_id": f"catalog-{uuid.uuid4().hex}",
        "entry_offset": addr,
        "register": str(params.get("register") or "A6"),
        "kind": kind,
        "library_name": library_name_value,
        "struct_name": struct_name_value or "",
        "context_name": context_name_value,
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
                    None,
                    "s",
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


def _struct_pointer_actions(context: Mapping[str, object]) -> list[dict[str, object]]:
    register = _register_name(context)
    if register is None:
        return []
    return [
        _context_log_action(
            "semantic.register.struct_ptr",
            f"Treat {register} as struct pointer",
            "create_manual_register_seed",
            context,
            {"register": register, "kind": "struct_ptr", "library_name": None},
            _struct_pointer_parameter_schema(),
        )
    ]


def _register_name(context: Mapping[str, object]) -> str | None:
    register = context.get("register")
    if not isinstance(register, str) or not register:
        return None
    return register.upper()


def _struct_pointer_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "struct_name": {"type": "string"},
            "context_name": {"type": "string"},
        },
        "required": ["struct_name"],
    }


def _library_base_actions(context: Mapping[str, object]) -> list[dict[str, object]]:
    if not _is_structured_a6_lvo_context(context):
        return []
    actions: list[dict[str, object]] = []
    for library_name, struct_name in _library_base_candidates(context):
        actions.append(
            _context_log_action(
                f"semantic.library_base.{_action_id_token(library_name)}",
                f"Treat A6 as {library_name} base",
                "create_manual_register_seed",
                context,
                {
                    "register": "A6",
                    "kind": "library_base",
                    "library_name": library_name,
                    "struct_name": struct_name,
                    "context_name": library_name,
                },
            )
        )
    return actions


def _library_base_candidates(context: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    payload = _amiga_ndk_payload()
    libraries = payload.get("libraries")
    if not isinstance(libraries, dict):
        return ()
    context_library = str(context.get("api_library") or context.get("library_name") or "")
    candidates: list[tuple[str, str]] = []
    if context_library:
        struct_name = _library_base_struct_name(payload, context_library)
        if struct_name is not None:
            candidates.append((context_library, struct_name))
    else:
        function_name = _lvo_function_name(context)
        if function_name:
            for library_name, library in libraries.items():
                if not isinstance(library_name, str) or not isinstance(library, dict):
                    continue
                functions = library.get("functions")
                if not isinstance(functions, dict) or function_name not in functions:
                    continue
                struct_name = _library_base_struct_name(payload, library_name)
                if struct_name is not None:
                    candidates.append((library_name, struct_name))
                if len(candidates) >= 4:
                    break
    return tuple(dict.fromkeys(candidates))


def _lvo_function_name(context: Mapping[str, object]) -> str:
    function = context.get("api_function")
    if isinstance(function, str) and function:
        return function
    symbol = str(context.get("symbol") or "")
    if symbol.startswith("_LVO") and len(symbol) > 4:
        return symbol[4:]
    function = context.get("function")
    return function if isinstance(function, str) else ""


def _library_base_struct_name(payload: Mapping[str, object], library_name: str) -> str | None:
    meta = payload.get("_meta")
    named_base_structs = meta.get("named_base_structs") if isinstance(meta, dict) else None
    if isinstance(named_base_structs, dict):
        struct_name = named_base_structs.get(library_name)
        if isinstance(struct_name, str) and struct_name:
            return struct_name
    libraries = payload.get("libraries")
    if isinstance(libraries, dict) and isinstance(libraries.get(library_name), dict):
        return "LIB"
    return None


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
    parameter_schema: Mapping[str, object] | None = None,
) -> dict[str, object]:
    parameters: dict[str, object] = {"seed_kind": seed_kind}
    if data_role is not None:
        parameters["data_role"] = data_role
    if unit is not None:
        parameters["unit"] = unit
    if encoding is not None:
        parameters["encoding"] = encoding
    return _log_action(action_id, label, "create_manual_seed", item, parameters, parameter_schema)


def _seed_remove_action(item: Mapping[str, object]) -> dict[str, object]:
    seed_ids = _manual_seed_ids(item)
    parameters: dict[str, object] = {}
    if len(seed_ids) == 1:
        parameters["seed_id"] = seed_ids[0]
    return _log_action(
        "review.seed.remove",
        "Remove manual seed",
        "remove_manual_seed",
        item,
        parameters,
        _seed_id_parameter_schema(seed_ids),
    )


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


def _target_log_action(
    action_id: str,
    label: str,
    ui_action: str,
    parameter_schema: Mapping[str, object],
) -> dict[str, object]:
    action = _target_transient(action_id, label, ui_action, None)
    action["appends_to_manual_action_log"] = True
    action["parameter_schema"] = dict(parameter_schema)
    action["category"] = "target_metadata"
    action["interaction_schema"] = {
        "type": "form",
        "hosts": ["palette"],
        "primary_rank": 88,
    }
    return action


def _target_reproduction_profile_action() -> dict[str, object]:
    profiles = builtin_reproduction_profiles()
    profile_ids = [str(profile["profile_id"]) for profile in profiles]
    action = _target_transient(
        "target.reproduction_profile",
        "Set reproduction profile",
        "set_reproduction_profile",
        None,
    )
    action["category"] = "target_tooling"
    action["parameter_schema"] = {
        "type": "object",
        "properties": {"profile_id": {"type": "string", "enum": profile_ids}},
        "required": ["profile_id"],
    }
    action["interaction_schema"] = {
        "type": "choice_grid",
        "hosts": ["palette"],
        "primary_rank": 80,
        "parameter": "profile_id",
        "default": "exact-framework",
        "options": [
            {
                "value": profile["profile_id"],
                "label": profile["name"],
                "preview": {"kind": "reproduction_profile", "text": profile["workflow"]},
            }
            for profile in profiles
        ],
        "preview": {"kind": "reproduction_profile"},
    }
    return action


def _target_source_export_action() -> dict[str, object]:
    profile_ids = ["vasm", "devpac"]
    action = _target_transient(
        "target.source_export",
        "Export Source",
        "export_source",
        None,
    )
    action["category"] = "target_tooling"
    action["parameter_schema"] = {
        "type": "object",
        "properties": {"assembler_profile": {"type": "string", "enum": profile_ids, "default": "vasm"}},
        "required": ["assembler_profile"],
    }
    action["interaction_schema"] = {
        "type": "choice_grid",
        "hosts": ["palette"],
        "primary_rank": 82,
        "parameter": "assembler_profile",
        "default": "vasm",
        "options": [
            {"value": profile_id, "label": profile_id, "preview": {"kind": "source_export", "text": "not verification"}}
            for profile_id in profile_ids
        ],
        "preview": {"kind": "source_export"},
    }
    return action


def _target_execution_view_action() -> dict[str, object]:
    return _target_log_action(
        "target.execution_view.add",
        "Add execution view",
        "create_manual_execution_view",
        _execution_view_parameter_schema(),
    )


def _target_equate_action() -> dict[str, object]:
    return _target_log_action(
        "target.equate.add",
        "Add equate",
        "create_manual_target_equate",
        _target_equate_parameter_schema(),
    )


def _target_equate_edit_action() -> dict[str, object]:
    return _target_log_action(
        "target.equate.edit",
        "Edit equate",
        "create_manual_target_equate",
        _target_equate_parameter_schema(),
    )


def _target_equate_rename_action() -> dict[str, object]:
    return _target_log_action(
        "target.equate.rename",
        "Rename equate",
        "rename_manual_target_equate",
        _target_equate_rename_parameter_schema(),
    )


def _target_equate_remove_action() -> dict[str, object]:
    return _target_log_action(
        "target.equate.remove",
        "Remove equate",
        "remove_manual_target_equate",
        _target_equate_identity_parameter_schema(),
    )


def _target_execution_view_edit_action() -> dict[str, object]:
    return _target_log_action(
        "target.execution_view.edit",
        "Edit execution view",
        "create_manual_execution_view",
        _execution_view_parameter_schema(),
    )


def _target_execution_view_remove_action() -> dict[str, object]:
    return _target_log_action(
        "target.execution_view.remove",
        "Remove execution view",
        "remove_manual_execution_view",
        _execution_view_identity_parameter_schema(),
    )


def _target_custom_struct_action() -> dict[str, object]:
    return _target_log_action(
        "target.custom_struct.add",
        "Add custom struct",
        "create_manual_custom_struct",
        _custom_struct_parameter_schema(),
    )


def _target_custom_struct_edit_action() -> dict[str, object]:
    return _target_log_action(
        "target.custom_struct.edit",
        "Edit custom struct",
        "create_manual_custom_struct",
        _custom_struct_parameter_schema(),
    )


def _target_custom_struct_rename_action() -> dict[str, object]:
    return _target_log_action(
        "target.custom_struct.rename",
        "Rename custom struct",
        "rename_manual_custom_struct",
        _custom_struct_rename_parameter_schema(),
    )


def _target_custom_struct_remove_action() -> dict[str, object]:
    return _target_log_action(
        "target.custom_struct.remove",
        "Remove custom struct",
        "remove_manual_custom_struct",
        _custom_struct_identity_parameter_schema(),
    )


def _target_custom_struct_field_action() -> dict[str, object]:
    return _target_log_action(
        "target.custom_struct_field.add",
        "Add custom struct field",
        "create_manual_custom_struct_field",
        _custom_struct_field_parameter_schema(),
    )


def _target_custom_struct_field_edit_action() -> dict[str, object]:
    return _target_log_action(
        "target.custom_struct_field.edit",
        "Edit custom struct field",
        "create_manual_custom_struct_field",
        _custom_struct_field_parameter_schema(),
    )


def _target_custom_struct_field_rename_action() -> dict[str, object]:
    return _target_log_action(
        "target.custom_struct_field.rename",
        "Rename custom struct field",
        "rename_manual_custom_struct_field",
        _custom_struct_field_rename_parameter_schema(),
    )


def _target_custom_struct_field_remove_action() -> dict[str, object]:
    return _target_log_action(
        "target.custom_struct_field.remove",
        "Remove custom struct field",
        "remove_manual_custom_struct_field",
        _custom_struct_field_identity_parameter_schema(),
    )


def _target_rsset_layout_region_action() -> dict[str, object]:
    return _target_log_action(
        "target.rsset_region.add",
        "Add RSSET region",
        "create_manual_rsset_layout_region",
        _rsset_layout_region_parameter_schema(),
    )


def _target_rsset_layout_region_edit_action() -> dict[str, object]:
    return _target_log_action(
        "target.rsset_region.edit",
        "Edit RSSET region",
        "create_manual_rsset_layout_region",
        _rsset_layout_region_parameter_schema(),
    )


def _target_rsset_layout_region_rename_action() -> dict[str, object]:
    return _target_log_action(
        "target.rsset_region.rename",
        "Rename RSSET region",
        "create_manual_rsset_layout_region",
        _rsset_layout_region_parameter_schema(),
    )


def _target_rsset_layout_region_remove_action() -> dict[str, object]:
    return _target_log_action(
        "target.rsset_region.remove",
        "Remove RSSET region",
        "remove_manual_rsset_layout_region",
        _rsset_layout_region_identity_parameter_schema(),
    )


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
    default_key_binding: str | None = None,
) -> dict[str, object]:
    return _context_entry(action_id, label, ui_action, context, True, parameters, default_key_binding, parameter_schema)


def _range_seed_action(
    action_id: str,
    label: str,
    context: Mapping[str, object],
    rows: list[Mapping[str, object]],
    parameters: Mapping[str, object],
    predicate: Callable[[Mapping[str, object]], bool],
    parameter_schema: Mapping[str, object] | None = None,
) -> dict[str, object]:
    eligible = [row for row in rows if predicate(row)]
    action = _context_log_action(action_id, label, "create_manual_seed", context, parameters, parameter_schema)
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
    entry = {
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
    interaction = _interaction_schema(action_id, label, ui_action, context, parameters, parameter_schema)
    if interaction:
        entry["interaction_schema"] = interaction
    return entry


def _entry(
    action_id: str,
    label: str,
    ui_action: str,
    item: Mapping[str, object],
    appends_to_log: bool,
    parameters: Mapping[str, object] | None,
    parameter_schema: Mapping[str, object] | None,
) -> dict[str, object]:
    context = {
        "kind": "review_item",
        "item_id": item.get("item_id"),
        "review_item_kind": str(item.get("kind") or ""),
    }
    entry = {
        "action_id": action_id,
        "label": label,
        "description": label,
        "enabled": True,
        "target_context": context,
        "parameter_schema": dict(parameter_schema or {"type": "object", "properties": {}, "required": []}),
        "default_key_binding": None,
        "appends_to_manual_action_log": appends_to_log,
        "action": ui_action,
        "parameters": dict(parameters or {}),
    }
    interaction = _interaction_schema(action_id, label, ui_action, context, parameters or {}, parameter_schema, item=item)
    if interaction:
        entry["interaction_schema"] = interaction
    return entry


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


def _interaction_schema(
    action_id: str,
    label: str,
    ui_action: str,
    context: Mapping[str, object],
    parameters: Mapping[str, object],
    parameter_schema: Mapping[str, object] | None,
    *,
    item: Mapping[str, object] | None = None,
) -> dict[str, object] | None:
    if ui_action in {"create_manual_label", "rename_manual_label"}:
        return {
            "type": "text",
            "hosts": ["palette", "inline"],
            "primary_rank": 0,
            "primary_field": "name",
            "submit_label": label,
            "preview": {"kind": "label", "symbol": context.get("symbol") or (item or {}).get("message")},
            "validation": _label_validation_metadata(context),
        }
    if ui_action == "create_manual_seed" and action_id.endswith(".seed.data.named"):
        return {
            "type": "text",
            "hosts": ["palette", "inline"],
            "primary_rank": 5,
            "primary_field": "name",
            "submit_label": label,
            "preview": {"kind": "data_label", "addr": context.get("addr") or (item or {}).get("start")},
            "validation": _label_validation_metadata(context),
        }
    if ui_action == "create_manual_comment":
        return {
            "type": "text",
            "hosts": ["palette", "inline"],
            "primary_rank": 10,
            "primary_field": "text",
            "submit_label": label,
            "preview": {"kind": "comment", "addr": context.get("addr")},
        }
    if ui_action in {"add_review_note", "edit_review_note"}:
        return {
            "type": "text",
            "hosts": ["palette", "inline"],
            "primary_rank": 40,
            "primary_field": "title",
            "submit_label": label,
            "preview": {"kind": "review_note", "addr": context.get("addr")},
        }
    if ui_action == "set_representation" and action_id == "representation.choose":
        return {
            "type": "choice_grid",
            "hosts": ["palette", "inline"],
            "primary_rank": 20,
            "parameter": "representation",
            "default": parameters.get("representation") or "hex",
            "options": _representation_options(context),
            "preview": {"kind": "representation", "value": context.get("value"), "width_bytes": context.get("width_bytes")},
        }
    if ui_action == "create_manual_semantic_hint":
        return {
            "type": "filtered_chooser",
            "hosts": ["palette", "inline"],
            "primary_rank": 30,
            "parameter": "semantic_option",
            "default": action_id,
            "options": [
                {
                    "value": action_id,
                    "label": label,
                    "parameters": dict(parameters),
                    "preview": {
                        "kind": "semantic_hint",
                        "domain": parameters.get("domain"),
                        "symbol": parameters.get("symbol"),
                        "value": parameters.get("value"),
                    },
                }
            ],
        }
    if parameter_schema is not None:
        return {
            "type": "form",
            "hosts": ["palette"],
            "submit_label": label,
        }
    return None


def _label_validation_metadata(context: Mapping[str, object]) -> dict[str, object]:
    symbol = str(context.get("symbol") or "")
    return {
        "active_profile": "vasm",
        "local_labels_supported": True,
        "allowed_scopes": ["global", "local"],
        "current_scope": "global",
        "current_name": symbol,
        "name_pattern": r"^[A-Za-z_.$][A-Za-z0-9_.$]*$",
        "messages": {
            "invalid_syntax": "Invalid label syntax",
            "local_disallowed": "Local labels are not allowed by the active profile",
            "conflict": "Name may conflict with an existing symbol",
            "stale": "Validation may be stale; server will recheck on save",
            "ready": "Ready",
        },
    }


def _representation_options(context: Mapping[str, object]) -> list[dict[str, object]]:
    value = _optional_int(context.get("value")) or 0
    return [
        {"value": "hex", "label": "Hex", "preview": {"kind": "literal", "text": f"${value:X}"}},
        {"value": "binary", "label": "Binary", "preview": {"kind": "literal", "text": f"%{value:b}"}},
        {"value": "character", "label": "Character", "preview": {"kind": "literal", "text": _character_preview(value)}},
    ]


def _character_preview(value: int) -> str:
    if 32 <= value <= 126:
        return repr(chr(value))
    return "not printable"


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _object(value: object, description: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{description} is missing")
    return value
