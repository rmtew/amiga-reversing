from __future__ import annotations

import json
import re
import uuid
from collections.abc import Callable, Mapping, Sequence
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
        _target_equate_represent_action(),
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
    if _row_allows_data_seed(row):
        actions.append(
            _context_log_action(
                "row.data_block.layout.create",
                "Create data-block layout",
                "create_manual_data_block_layout",
                context,
                {"default_unit": "byte"},
                _data_block_layout_parameter_schema(),
            )
        )
        actions.extend(_row_data_block_element_actions(context, row))
    return actions


def listing_element_action_catalog(
    row: Mapping[str, object],
    element_selector: Mapping[str, object],
) -> list[dict[str, object]]:
    context = selected_listing_element_context(row, element_selector)
    target = element_selector.get("target")
    if isinstance(target, str) and target.strip():
        context["target"] = target.strip()
    for key in (
        "layout_name",
        "base_symbol",
        "base_evidence_id",
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "confidence",
        "contradicted_evidence_id",
        "reason",
    ):
        value = element_selector.get(key)
        if isinstance(value, str) and value.strip():
            context[key] = value.strip()
    for key in ("path_lifetime_scope", "conflicts", "parent_evidence_ids", "cleanup_scope"):
        value = element_selector.get(key)
        if isinstance(value, dict | list):
            context[key] = value
    same_displacement_uses = element_selector.get("same_displacement_uses")
    if isinstance(same_displacement_uses, list):
        context["same_displacement_uses"] = same_displacement_uses
    same_displacement_use_count = _optional_int(element_selector.get("same_displacement_use_count"))
    if same_displacement_use_count is not None:
        context["same_displacement_use_count"] = same_displacement_use_count
    element_kind = str(context.get("element_kind") or "")
    actions = [
        _context_transient("navigation.follow_reference", "Follow Reference", "follow_reference", context, "Right"),
    ]
    actions.extend(_provenance_report_actions(context, row))
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
            if "previous_name" in identity:
                actions.append(
                    _context_log_action(
                        "data_symbol.rename_existing",
                        "Rename existing referenced data symbol",
                        "rename_existing_data_symbol",
                        context,
                        identity,
                        _data_name_parameter_schema(),
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
    actions.extend(_rsset_binding_actions(context, row))
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
                    _typed_field_action_parameters(context, row),
                    _typed_field_parameter_schema(),
                ),
                _context_log_action(
                    "typed_gap.field.edit",
                    "Edit struct field",
                    "create_manual_custom_struct_field",
                    context,
                    _typed_field_action_parameters(context, row),
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
                    _typed_field_action_parameters(context, row),
                    _typed_field_parameter_schema(),
                ),
                _context_log_action(
                    "typed_access.field.rename",
                    "Rename struct field",
                    "rename_manual_custom_struct_field",
                    context,
                    _typed_field_action_parameters(context, row),
                    _typed_field_rename_parameter_schema(),
                    "F2",
                ),
                _context_log_action(
                    "typed_access.field.remove",
                    "Remove struct field",
                    "remove_manual_custom_struct_field",
                    context,
                    _typed_field_action_parameters(context, row),
                ),
            )
        )
    if element_kind == "register":
        actions.extend(_struct_pointer_actions(context))
    actions.extend(_library_base_actions(context))
    if element_kind in {"immediate", "data_literal"}:
        actions.extend(_semantic_hint_actions(context))
    return actions


def _provenance_report_actions(context: Mapping[str, object], row: Mapping[str, object]) -> list[dict[str, object]]:
    report = _provenance_report(context, row)
    if report is None:
        return []
    actions: list[dict[str, object]] = []
    for action_id, label, focus in (
        ("provenance.definition.report", "Provenance definition report", "definitions"),
        ("provenance.uses.report", "Provenance uses report", "uses"),
        ("provenance.references.report", "Provenance reference report", "references"),
        ("provenance.source_family.report", "Provenance source-family report", "source_family"),
    ):
        action = _context_transient(action_id, label, "provenance_report", context, None)
        focused_report = dict(report)
        focused_report["focus"] = focus
        action["report"] = focused_report
        action["parameters"] = {"source_evidence_id": report["source_evidence_id"], "focus": focus}
        actions.append(action)
    return actions


def _provenance_report(context: Mapping[str, object], row: Mapping[str, object]) -> dict[str, object] | None:
    subject = _provenance_subject(context, row)
    if subject is None:
        return None
    classification = _provenance_classification(context, subject)
    source_evidence_id = _provenance_source_evidence_id(context, subject, classification)
    definitions = _provenance_definitions(context, row, subject, classification, source_evidence_id)
    uses = _provenance_uses(context, subject)
    references = _provenance_references(context, subject, uses)
    possible_actions = _provenance_possible_actions(context, classification)
    return {
        "kind": "provenance_report",
        "subject": subject,
        "definitions": definitions,
        "uses": uses,
        "references": references,
        "source_family": classification["source_family"],
        "status": classification["status"],
        "path_lifetime_scope": classification["path_lifetime_scope"],
        "source_evidence_id": source_evidence_id,
        "confidence": classification["confidence"],
        "conflicts": classification["conflicts"],
        "parent_evidence_ids": classification.get("parent_evidence_ids", []),
        "possible_actions": possible_actions,
        "consumers": _provenance_consumers(context),
    }


def _provenance_subject(context: Mapping[str, object], row: Mapping[str, object]) -> dict[str, object] | None:
    register = _provenance_register(context)
    if register is None:
        return None
    subject = {
        "target": context.get("target"),
        "hunk": context.get("hunk"),
        "addr": context.get("addr") or context.get("start_offset"),
        "stable_key": context.get("stable_key") or row.get("row_key") or row.get("stable_key"),
        "row_text": str(row.get("text") or "").strip(),
        "element_id": context.get("element_id"),
        "element_kind": context.get("element_kind"),
        "operand_index": context.get("operand_index"),
        "register": register,
    }
    base_register = context.get("base_register")
    if isinstance(base_register, str) and base_register:
        subject["base_register"] = base_register.upper()
    displacement = _optional_int(context.get("displacement"))
    if displacement is not None:
        subject["displacement"] = displacement
        subject["address_mode"] = "address_register_displacement"
    width_bytes = _optional_int(context.get("width_bytes"))
    if width_bytes is None:
        width_bytes = _rsset_binding_width_bytes(context, row)
    if width_bytes is not None:
        subject["width_bytes"] = width_bytes
    value = _optional_int(context.get("value"))
    if value is not None:
        subject["value"] = value
    return {key: value for key, value in subject.items() if value is not None}


def _provenance_register(context: Mapping[str, object]) -> str | None:
    for key in ("base_register", "register"):
        value = context.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().upper()
    return None


def _provenance_classification(
    context: Mapping[str, object],
    subject: Mapping[str, object],
) -> dict[str, object]:
    base_evidence_id = context.get("base_evidence_id")
    if isinstance(base_evidence_id, str) and base_evidence_id.strip():
        return {
            "source_family": "rsset_app_base",
            "status": "path_specific",
            "path_lifetime_scope": _provenance_scope(context, "selected_use"),
            "confidence": "medium",
            "origin_kind": "explicit_base_evidence",
            "conflicts": [],
            "parent_evidence_ids": [base_evidence_id.strip()],
        }
    if context.get("element_kind") == "app_slot":
        return {
            "source_family": "rsset_app_base",
            "status": "analysis_proven",
            "path_lifetime_scope": _provenance_scope(context, "selected_use"),
            "confidence": "high",
            "origin_kind": "app_slot_analysis",
            "conflicts": [],
            "parent_evidence_ids": [],
        }
    if _is_structured_a6_lvo_context(context):
        return {
            "source_family": "library_base",
            "status": "analysis_proven",
            "path_lifetime_scope": _provenance_scope(context, "entry"),
            "confidence": "high",
            "origin_kind": "lvo_api_operand",
            "conflicts": [],
            "parent_evidence_ids": [],
        }
    if context.get("element_kind") in {"typed_access", "typed_gap"} and (
        context.get("root_struct_name") or context.get("owner_struct_name")
    ):
        return {
            "source_family": "struct_pointer",
            "status": "analysis_proven",
            "path_lifetime_scope": _provenance_scope(context, "selected_use"),
            "confidence": "high",
            "origin_kind": "typed_access_analysis",
            "conflicts": [],
            "parent_evidence_ids": [],
        }
    if "displacement" in subject:
        return {
            "source_family": "unknown",
            "status": "unresolved",
            "path_lifetime_scope": _provenance_scope(context, "selected_use"),
            "confidence": "low",
            "origin_kind": "base_relative_operand",
            "conflicts": [],
            "parent_evidence_ids": [],
        }
    return {
        "source_family": "unknown",
        "status": "unknown",
        "path_lifetime_scope": _provenance_scope(context, "selected_use"),
        "confidence": "low",
        "origin_kind": "register_operand",
        "conflicts": [],
        "parent_evidence_ids": [],
    }


def _provenance_scope(context: Mapping[str, object], kind: str) -> dict[str, object]:
    scope: dict[str, object] = {"kind": kind}
    for key in ("hunk", "addr", "start_offset", "end_offset", "operand_index"):
        value = context.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            scope[key] = value
    return scope


def _provenance_source_evidence_id(
    context: Mapping[str, object],
    subject: Mapping[str, object],
    classification: Mapping[str, object],
) -> str:
    target = _id_token(str(subject.get("target") or "target"))
    family = _id_token(str(classification.get("source_family") or "unknown"))
    status = _id_token(str(classification.get("status") or "unknown"))
    register = _id_token(str(subject.get("register") or "reg"))
    hunk = _optional_int(subject.get("hunk")) or 0
    addr = _optional_int(subject.get("addr")) or _optional_int(subject.get("start_offset")) or 0
    operand_index = _optional_int(subject.get("operand_index"))
    operand_token = f"op{operand_index}" if operand_index is not None else "opnone"
    displacement = _optional_int(subject.get("displacement"))
    displacement_token = f"d{displacement:04X}" if displacement is not None else "dn"
    origin = _id_token(str(classification.get("origin_kind") or "origin"))
    parent_token = _provenance_parent_token(classification)
    scope = classification.get("path_lifetime_scope")
    scope_kind = _id_token(str(scope.get("kind") if isinstance(scope, Mapping) else "scope"))
    return (
        f"prov-{target}-{family}-{status}-h{hunk}-{addr:08X}-{operand_token}-"
        f"{register}-{displacement_token}-{origin}-{parent_token}-{scope_kind}"
    )


def _provenance_parent_token(classification: Mapping[str, object]) -> str:
    parent_ids = classification.get("parent_evidence_ids")
    if not isinstance(parent_ids, Sequence) or isinstance(parent_ids, (str, bytes, bytearray)):
        return "pn"
    parent_tokens = [_id_token(item) for item in parent_ids if isinstance(item, str) and item]
    if not parent_tokens:
        return "pn"
    if len(parent_tokens) == 1:
        return parent_tokens[0]
    return "__".join(parent_tokens)


def _provenance_definitions(
    context: Mapping[str, object],
    row: Mapping[str, object],
    subject: Mapping[str, object],
    classification: Mapping[str, object],
    source_evidence_id: str,
) -> list[dict[str, object]]:
    definition = {
        "source_evidence_id": source_evidence_id,
        "origin_kind": classification["origin_kind"],
        "origin_hunk": subject.get("hunk"),
        "origin_addr": subject.get("addr") or subject.get("start_offset"),
        "defining_instruction": str(row.get("text") or "").strip(),
        "register": subject.get("register"),
        "source_family": classification["source_family"],
        "status": classification["status"],
        "path_lifetime_scope": classification["path_lifetime_scope"],
        "parent_evidence_ids": classification.get("parent_evidence_ids", []),
    }
    if context.get("api_library"):
        definition["library_name"] = context.get("api_library")
    if context.get("api_function"):
        definition["function_name"] = context.get("api_function")
    if classification.get("source_family") == "library_base" and "library_name" not in definition:
        candidates = _library_base_candidates(context)
        if candidates:
            definition["library_name"] = candidates[0][0]
            definition["struct_name"] = candidates[0][1]
            function_name = _lvo_function_name(context)
            if function_name:
                definition["function_name"] = function_name
    for key in ("root_struct_name", "owner_struct_name", "field_name", "field_expr"):
        value = context.get(key)
        if isinstance(value, str) and value:
            definition[key] = value
    return [{key: value for key, value in definition.items() if value is not None}]


def _provenance_uses(context: Mapping[str, object], subject: Mapping[str, object]) -> list[dict[str, object]]:
    uses = _mapping_sequence(context.get("same_displacement_uses"))
    if uses:
        return [dict(use) for use in uses]
    use = {
        "hunk": subject.get("hunk"),
        "addr": subject.get("addr"),
        "stable_key": subject.get("stable_key"),
        "row_text": subject.get("row_text"),
        "operand_index": subject.get("operand_index"),
        "access": context.get("access") or "reference",
        "width_bytes": subject.get("width_bytes"),
    }
    return [{key: value for key, value in use.items() if value is not None}]


def _provenance_references(
    context: Mapping[str, object],
    subject: Mapping[str, object],
    uses: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    consumers = _provenance_consumers(context)
    references: list[dict[str, object]] = []
    for use in uses:
        ref = {
            "kind": "register_base_use",
            "hunk": use.get("hunk"),
            "addr": use.get("addr"),
            "stable_key": use.get("stable_key"),
            "row_text": use.get("row_text"),
            "operand_index": use.get("operand_index"),
            "access": use.get("access"),
            "width_bytes": use.get("width_bytes"),
            "register": subject.get("register"),
            "base_register": subject.get("base_register"),
            "displacement": subject.get("displacement"),
            "consumers": consumers,
        }
        references.append({key: value for key, value in ref.items() if value not in (None, [])})
    return references


def _provenance_possible_actions(
    context: Mapping[str, object],
    classification: Mapping[str, object],
) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    if classification.get("source_family") == "library_base":
        for library_name, _struct_name in _library_base_candidates(context):
            actions.append({"command_id": f"semantic.library_base.{_action_id_token(library_name)}", "state": "available"})
    if _provenance_register(context):
        actions.append({"command_id": "semantic.register.struct_ptr", "state": "available_with_parameters"})
    if context.get("displacement") is not None and context.get("base_register"):
        actions.append({"command_id": "rsset.binding.report", "state": "report_only"})
        if context.get("base_evidence_id"):
            actions.append({"command_id": "rsset.binding.bind", "state": "available"})
        else:
            actions.append({"command_id": "provenance.classify_source", "state": "planned_write_boundary"})
    return actions


def _provenance_consumers(context: Mapping[str, object]) -> list[str]:
    consumers: list[str] = []
    if context.get("displacement") is not None and context.get("base_register"):
        consumers.append("rsset.binding")
    if context.get("element_kind") in {"typed_access", "typed_gap"}:
        consumers.append("typed_field")
    if _provenance_register(context):
        consumers.append("semantic.register_seed")
    return consumers


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
    actions.append(_range_data_block_layout_action(context, rows))
    actions.extend(_range_data_block_element_actions(context, rows))
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
    user_params = dict(parameters or {})
    if parameters:
        params.update(parameters)
    if action.get("action") == "add_review_note":
        return [("add_review_note", {"note": _range_review_note_payload(rows, params)})]
    if action.get("action") == "create_manual_data_block_layout":
        return [
            ("create_manual_data_block_layout", {"data_block_layout": _data_block_layout_payload(subrange_rows, params)})
            for subrange_rows in _range_action_subrange_rows(action, rows)
        ]
    if action.get("action") == "set_manual_data_block_element":
        return [
            (
                "set_manual_data_block_element",
                {
                    "data_block_element": _data_block_element_payload(
                        subrange_rows,
                        _data_block_range_subrange_params(params, user_params, {"layout_id", "offset", "width"}),
                    )
                },
            )
            for subrange_rows in _range_action_subrange_rows(action, rows)
        ]
    if action.get("action") == "remove_manual_data_block_element":
        return [
            (
                "remove_manual_data_block_element",
                {
                    "data_block_element": _data_block_element_remove_payload(
                        subrange_rows,
                        _data_block_range_subrange_params(params, user_params, {"layout_id", "offset", "width"}),
                    )
                },
            )
            for subrange_rows in _range_action_subrange_rows(action, rows)
        ]
    if action.get("action") == "represent_manual_data_block_element":
        return [
            (
                "represent_manual_data_block_element",
                {
                    "data_block_element": _data_block_element_representation_payload(
                        subrange_rows,
                        _data_block_range_subrange_params(params, user_params, {"layout_id", "offset"}),
                    )
                },
            )
            for subrange_rows in _range_action_subrange_rows(action, rows)
        ]
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


def _data_block_range_subrange_params(
    params: Mapping[str, object],
    user_params: Mapping[str, object],
    inferred_keys: set[str],
) -> dict[str, object]:
    return {key: value for key, value in params.items() if key not in inferred_keys or key in user_params}


def _range_action_subrange_rows(
    action: Mapping[str, object],
    rows: list[Mapping[str, object]],
) -> list[list[Mapping[str, object]]]:
    subranges = action.get("applicable_subranges")
    if not isinstance(subranges, list) or not subranges:
        raise ValueError("Range action has no explicit applicable subranges")
    rows_by_index = {_optional_int(row.get("row_index")): row for row in rows}
    result: list[list[Mapping[str, object]]] = []
    for raw_subrange in subranges:
        if not isinstance(raw_subrange, Mapping):
            continue
        row_indexes = [
            value for value in raw_subrange.get("row_indexes", []) if isinstance(value, int) and not isinstance(value, bool)
        ]
        subrange_rows = [rows_by_index[index] for index in row_indexes if index in rows_by_index]
        if subrange_rows:
            result.append(subrange_rows)
    if not result:
        raise ValueError("Range action has no available selected rows")
    return result


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


def _data_block_layout_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "role": {"type": "string"},
            "default_unit": {"type": "string", "enum": ["byte", "word", "long"]},
        },
    }


def _data_block_element_parameter_schema(defaults: Mapping[str, object] | None = None) -> dict[str, object]:
    return _data_block_element_schema_with_inferred_identity(
        {
            "type": "object",
            "properties": {
                "layout_id": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0},
                "width": {"type": "integer", "minimum": 1},
                "kind": {
                    "type": "string",
                    "enum": ["scalar", "array", "struct", "platform_struct", "padding", "gap", "raw"],
                },
                "name": {"type": "string"},
                "array_count": {"type": "integer", "minimum": 1},
                "array_stride": {"type": "integer", "minimum": 1},
                "representation": {"type": "string", "enum": ["hex", "binary", "character"]},
            },
            "required": ["layout_id", "offset"],
        },
        defaults,
    )


def _data_block_element_identity_parameter_schema(defaults: Mapping[str, object] | None = None) -> dict[str, object]:
    return _data_block_element_schema_with_inferred_identity(
        {
            "type": "object",
            "properties": {
                "layout_id": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0},
                "width": {"type": "integer", "minimum": 1},
                "removal_state": {"type": "string", "enum": ["raw", "gap"]},
            },
            "required": ["layout_id", "offset"],
        },
        defaults,
    )


def _data_block_element_representation_parameter_schema(defaults: Mapping[str, object] | None = None) -> dict[str, object]:
    return _data_block_element_schema_with_inferred_identity(
        {
            "type": "object",
            "properties": {
                "layout_id": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0},
                "representation": {"type": "string", "enum": ["hex", "binary", "character"]},
            },
            "required": ["layout_id", "offset", "representation"],
        },
        defaults,
    )


def _data_block_element_ref_parameter_schema(defaults: Mapping[str, object] | None = None) -> dict[str, object]:
    return _data_block_element_schema_with_inferred_identity(
        {
            "type": "object",
            "properties": {
                "layout_id": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0},
                "width": {"type": "integer", "minimum": 1},
                "reference_kind": {"type": "string", "enum": ["absolute"]},
                "target_hunk": {"type": "integer", "minimum": 0},
                "target_offset": {"type": "integer", "minimum": 0},
                "source_value": {"type": "integer", "minimum": 0},
                "signed": {"type": "boolean"},
                "scale": {"type": "integer", "minimum": 1},
                "base_evidence_id": {"type": "string"},
                "source_evidence_id": {"type": "string"},
                "confidence": {"type": "string", "enum": ["manual", "high", "medium", "low"]},
                "xref_generation_mode": {"type": "string", "enum": ["bidirectional", "source_only", "none"]},
                "data_block_ref_id": {"type": "string"},
            },
            "required": ["layout_id", "offset", "width", "reference_kind", "target_hunk", "target_offset"],
        },
        defaults,
    )


def _data_block_element_type_binding_parameter_schema(defaults: Mapping[str, object] | None = None) -> dict[str, object]:
    return _data_block_element_schema_with_inferred_identity(
        {
            "type": "object",
            "properties": {
                "layout_id": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0},
                "width": {"type": "integer", "minimum": 1},
                "kind": {"type": "string", "enum": ["struct", "platform_struct", "scalar", "array"]},
                "binding_kind": {
                    "type": "string",
                    "enum": ["custom_struct", "platform_struct", "enum_domain", "equate_domain"],
                },
                "type_binding_id": {"type": "string"},
                "type_id": {"type": "string"},
                "domain_id": {"type": "string"},
                "name": {"type": "string"},
                "array_count": {"type": "integer", "minimum": 1},
                "array_stride": {"type": "integer", "minimum": 1},
                "representation": {"type": "string", "enum": ["hex", "binary", "character"]},
                "source_evidence_id": {"type": "string"},
                "source_family": {
                    "type": "string",
                    "enum": ["data_block_pointer", "struct_pointer", "constant_or_equ", "rsset_app_base"],
                },
                "source_evidence_status": {
                    "type": "string",
                    "enum": ["analysis_proven", "path_specific", "manual_classified", "manual_override"],
                },
                "parent_evidence_ids": {"type": "array", "items": {"type": "string"}},
                "requires_source_evidence": {"type": "boolean"},
            },
            "required": ["layout_id", "offset", "width", "binding_kind"],
        },
        defaults,
    )


def _data_block_element_type_clear_parameter_schema(defaults: Mapping[str, object] | None = None) -> dict[str, object]:
    return _data_block_element_schema_with_inferred_identity(
        {
            "type": "object",
            "properties": {
                "layout_id": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0},
                "width": {"type": "integer", "minimum": 1},
                "kind": {
                    "type": "string",
                    "enum": ["scalar", "array", "struct", "platform_struct", "padding", "gap", "raw"],
                },
                "name": {"type": "string"},
                "array_count": {"type": "integer", "minimum": 1},
                "array_stride": {"type": "integer", "minimum": 1},
                "representation": {"type": "string", "enum": ["hex", "binary", "character"]},
            },
            "required": ["layout_id", "offset", "width", "kind"],
        },
        defaults,
    )


def _data_block_element_ref_remove_parameter_schema(defaults: Mapping[str, object] | None = None) -> dict[str, object]:
    schema = _data_block_element_schema_with_inferred_identity(
        {
            "type": "object",
            "properties": {
                "layout_id": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0},
                "data_block_ref_id": {"type": "string"},
                "reference_kind": {"type": "string", "enum": ["absolute"]},
                "target_hunk": {"type": "integer", "minimum": 0},
                "target_offset": {"type": "integer", "minimum": 0},
            },
            "required": ["layout_id", "offset", "data_block_ref_id"],
        },
        defaults,
    )
    required = schema.get("required")
    if isinstance(required, list) and defaults and "data_block_ref_id" in defaults:
        schema["required"] = [key for key in required if key != "data_block_ref_id"]
    return schema


def _data_block_element_schema_with_inferred_identity(
    schema: dict[str, object],
    defaults: Mapping[str, object] | None,
) -> dict[str, object]:
    if not defaults:
        return schema
    required = schema.get("required")
    if not isinstance(required, list):
        return schema
    inferred = {key for key in ("layout_id", "offset", "width", "kind") if key in defaults}
    schema["required"] = [key for key in required if key not in inferred]
    return schema


def _row_data_block_element_actions(context: Mapping[str, object], row: Mapping[str, object]) -> list[dict[str, object]]:
    defaults = _data_block_element_context([row])
    ref_defaults = _data_block_element_ref_context(row)
    return [
        _context_log_action(
            "row.data_block.element.set",
            "Set data-block element",
            "set_manual_data_block_element",
            context,
            defaults,
            _data_block_element_parameter_schema(defaults),
        ),
        _context_log_action(
            "row.data_block.element.remove",
            "Remove data-block element",
            "remove_manual_data_block_element",
            context,
            defaults,
            _data_block_element_identity_parameter_schema(defaults),
        ),
        _context_log_action(
            "row.data_block.element.represent",
            "Represent data-block element",
            "represent_manual_data_block_element",
            context,
            {key: value for key, value in defaults.items() if key in {"layout_id", "offset"}},
            _data_block_element_representation_parameter_schema(defaults),
        ),
        _context_log_action(
            "row.data_block.element.interpret_ref",
            "Interpret data-block element reference",
            "interpret_manual_data_block_element_ref",
            context,
            {**defaults, "reference_kind": "absolute", "confidence": "manual", "xref_generation_mode": "bidirectional"},
            _data_block_element_ref_parameter_schema(defaults),
        ),
        _context_log_action(
            "row.data_block.element.clear_ref",
            "Clear data-block element reference",
            "remove_manual_data_block_element_ref",
            context,
            {
                key: value
                for key, value in ref_defaults.items()
                if key in {"layout_id", "offset", "data_block_ref_id", "reference_kind", "target_hunk", "target_offset"}
            },
            _data_block_element_ref_remove_parameter_schema(ref_defaults),
        ),
        _context_log_action(
            "row.data_block.element.bind_type",
            "Bind data-block element type",
            "set_manual_data_block_element",
            context,
            {
                key: value
                for key, value in defaults.items()
                if key in {"layout_id", "offset", "width", "kind", "name", "array_count", "array_stride", "representation"}
            },
            _data_block_element_type_binding_parameter_schema(defaults),
        ),
        _context_log_action(
            "row.data_block.element.clear_type",
            "Clear data-block element type",
            "set_manual_data_block_element",
            context,
            {
                key: value
                for key, value in defaults.items()
                if key in {"layout_id", "offset", "width", "kind", "name", "array_count", "array_stride", "representation"}
            },
            _data_block_element_type_clear_parameter_schema(defaults),
        ),
    ]


def _range_data_block_element_actions(
    context: Mapping[str, object],
    rows: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    defaults = _data_block_element_context(rows)
    return [
        _range_data_block_element_action(
            "range.data_block.element.set",
            "Set data-block element",
            "set_manual_data_block_element",
            context,
            rows,
            defaults,
            _data_block_element_parameter_schema(defaults),
        ),
        _range_data_block_element_action(
            "range.data_block.element.remove",
            "Remove data-block element",
            "remove_manual_data_block_element",
            context,
            rows,
            defaults,
            _data_block_element_identity_parameter_schema(defaults),
        ),
        _range_data_block_element_action(
            "range.data_block.element.represent",
            "Represent data-block element",
            "represent_manual_data_block_element",
            context,
            rows,
            {key: value for key, value in defaults.items() if key in {"layout_id", "offset"}},
            _data_block_element_representation_parameter_schema(defaults),
        ),
    ]


def _range_data_block_element_action(
    action_id: str,
    label: str,
    ui_action: str,
    context: Mapping[str, object],
    rows: list[Mapping[str, object]],
    defaults: Mapping[str, object],
    parameter_schema: Mapping[str, object],
) -> dict[str, object]:
    eligible = [row for row in rows if _row_allows_data_seed(row)]
    action = _context_log_action(action_id, label, ui_action, context, defaults, parameter_schema)
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


def _range_data_block_layout_action(context: Mapping[str, object], rows: list[Mapping[str, object]]) -> dict[str, object]:
    eligible = [row for row in rows if _row_allows_data_seed(row)]
    action = _context_log_action(
        "range.data_block.layout.create",
        "Create data-block layout",
        "create_manual_data_block_layout",
        context,
        {"default_unit": "byte"},
        _data_block_layout_parameter_schema(),
    )
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
    if ui_action == "rename_existing_data_symbol":
        payload = _data_symbol_payload(row, params)
        if "previous_name" not in payload:
            raise ValueError("rename_existing_data_symbol requires previous_name")
        return "rename_data_symbol", {"data_symbol": payload}
    if ui_action == "remove_manual_seed":
        seed_id = params.get("seed_id")
        if not isinstance(seed_id, str) or not seed_id:
            raise ValueError("remove_manual_seed requires seed_id")
        return "remove_manual_seed", {"seed_id": seed_id}
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
    if ui_action == "create_manual_rsset_use_site_binding":
        if not element_context:
            raise ValueError("create_manual_rsset_use_site_binding requires an element context")
        return "create_manual_rsset_use_site_binding", {
            "rsset_use_site_binding": _rsset_use_site_binding_payload(row, element_context, params)
        }
    if ui_action == "create_manual_data_block_layout":
        return "create_manual_data_block_layout", {"data_block_layout": _data_block_layout_payload([row], params)}
    if action_id == "row.data_block.element.bind_type":
        return "set_manual_data_block_element", {
            "data_block_element": _data_block_element_type_binding_payload([row], params)
        }
    if action_id == "row.data_block.element.clear_type":
        return "set_manual_data_block_element", {
            "data_block_element": _data_block_element_clear_type_payload([row], params)
        }
    if ui_action == "set_manual_data_block_element":
        return "set_manual_data_block_element", {"data_block_element": _data_block_element_payload([row], params)}
    if ui_action == "remove_manual_data_block_element":
        return "remove_manual_data_block_element", {
            "data_block_element": _data_block_element_remove_payload([row], params)
        }
    if ui_action == "represent_manual_data_block_element":
        return "represent_manual_data_block_element", {
            "data_block_element": _data_block_element_representation_payload([row], params)
        }
    if ui_action == "interpret_manual_data_block_element_ref":
        return "interpret_manual_data_block_element_ref", {
            "data_block_interpreted_ref": _data_block_element_ref_payload([row], params)
        }
    if ui_action == "remove_manual_data_block_element_ref":
        return "remove_manual_data_block_element_ref", {
            "data_block_interpreted_ref": _data_block_element_ref_remove_payload([row], params)
        }
    if ui_action == "remove_manual_rsset_use_site_binding":
        if not element_context:
            raise ValueError("remove_manual_rsset_use_site_binding requires an element context")
        return "remove_manual_rsset_use_site_binding", {
            "rsset_use_site_binding": _rsset_use_site_binding_identity_payload(row, element_context, params)
        }
    if ui_action == "create_manual_custom_struct_field":
        if not element_context or element_context.get("element_kind") not in {"typed_access", "typed_gap"}:
            raise ValueError("create_manual_custom_struct_field requires a typed element context")
        field = _custom_struct_field_target_payload(params)
        _attach_custom_struct_field_evidence(field, params, element_context, row)
        return "create_manual_custom_struct_field", {"custom_struct_field": field}
    if ui_action == "rename_manual_custom_struct_field":
        if not element_context or element_context.get("element_kind") != "typed_access":
            raise ValueError("rename_manual_custom_struct_field requires a typed-access element context")
        field = _custom_struct_field_rename_payload(params)
        _attach_custom_struct_field_evidence(field, params, element_context, row)
        return "rename_manual_custom_struct_field", {"custom_struct_field": field}
    if ui_action == "remove_manual_custom_struct_field":
        if not element_context or element_context.get("element_kind") != "typed_access":
            raise ValueError("remove_manual_custom_struct_field requires a typed-access element context")
        field = _custom_struct_field_identity_payload(params)
        _attach_custom_struct_field_evidence(field, params, element_context, row)
        return "remove_manual_custom_struct_field", {"custom_struct_field": field}
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
        if "name" in item:
            actions.append(
                _context_log_action(
                    "data_symbol.rename_existing",
                    "Rename existing data symbol",
                    "rename_existing_data_symbol",
                    context,
                    {
                        "hunk": item["hunk"],
                        "addr": item["addr"],
                        **({"end": item["end"]} if "end" in item else {}),
                        "previous_name": item["name"],
                        **({"source_locator": item["source_locator"]} if "source_locator" in item else {}),
                    },
                    _data_name_parameter_schema(),
                )
            )
        manual_seed_id = _manual_seed_id_from_source_locator(item.get("source_locator"))
        if manual_seed_id is not None:
            actions.append(
                _context_log_action(
                    "data_symbol.remove",
                    "Remove data symbol",
                    "remove_manual_seed",
                    context,
                    {"seed_id": manual_seed_id},
                )
            )
        else:
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
            if "previous_name" in identity:
                actions.append(
                    _context_log_action(
                        "data_symbol.rename_existing",
                        "Rename existing data symbol",
                        "rename_existing_data_symbol",
                        context,
                        identity,
                        _data_name_parameter_schema(),
                    )
                )
    return actions


def _manual_seed_id_from_source_locator(value: object) -> str | None:
    prefix = "ManualSeed:"
    if not isinstance(value, str) or not value.startswith(prefix):
        return None
    seed_id = value.removeprefix(prefix)
    return seed_id if seed_id else None


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
    symbol = context.get("symbol")
    if isinstance(symbol, str) and symbol:
        identity["previous_name"] = symbol
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
    value_representation = params.get("value_representation")
    if isinstance(value_representation, str) and value_representation.strip():
        representation = value_representation.strip()
        if representation not in {"hex", "decimal", "binary", "character", "symbol"}:
            raise ValueError("target_equate value_representation must be hex, decimal, binary, character, or symbol")
        equate["value_representation"] = representation
    value_expression = params.get("value_expression")
    if isinstance(value_expression, str) and value_expression.strip():
        equate["value_expression"] = value_expression.strip()
    if equate.get("value_representation") == "symbol" and "value_expression" not in equate:
        raise ValueError("target_equate symbol value_representation requires value_expression")
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


def _rsset_binding_actions(context: Mapping[str, object], row: Mapping[str, object]) -> list[dict[str, object]]:
    report_params = _rsset_use_site_binding_parameters(context, require_evidence=False)
    if report_params is None:
        return []
    report = _context_transient("rsset.binding.report", "RSSET binding report", "rsset_binding_report", context, None)
    report["parameters"] = dict(report_params)
    report["report"] = _rsset_binding_report(context, row, report_params)
    actions = [report]
    mutation_params = _rsset_use_site_binding_parameters(context, require_evidence=True)
    if mutation_params is None:
        return actions
    actions.extend(
        [
            _context_log_action(
                "rsset.binding.bind",
                "Bind RSSET use site",
                "create_manual_rsset_use_site_binding",
                context,
                mutation_params,
                _rsset_use_site_binding_parameter_schema(),
            ),
            _context_log_action(
                "rsset.binding.unbind",
                "Remove RSSET use-site binding",
                "remove_manual_rsset_use_site_binding",
                context,
                mutation_params,
            ),
        ]
    )
    return actions


def _rsset_use_site_binding_parameters(
    context: Mapping[str, object],
    *,
    require_evidence: bool,
) -> dict[str, object] | None:
    displacement = _optional_int(context.get("displacement"))
    operand_index = _optional_int(context.get("operand_index"))
    base_register = context.get("base_register")
    if displacement is None or displacement < 0 or displacement > 0x7FFF:
        return None
    if operand_index is None:
        return None
    if not isinstance(base_register, str) or not base_register.strip():
        return None
    symbol = context.get("symbol")
    if isinstance(symbol, str) and symbol.startswith("_LVO"):
        return None
    base_register_text = base_register.strip().upper()
    evidence = _rsset_binding_evidence_parameters(context, base_register_text)
    if require_evidence and evidence is None:
        return None
    if evidence is not None:
        layout_name: object = evidence.get("layout_name")
        base_symbol: object = evidence.get("base_symbol")
    elif base_register_text == "A6":
        layout_name = "app"
        base_symbol = "__amiga_app_base__"
    else:
        layout_name = None
        base_symbol = None
    return {
        "layout_name": layout_name,
        "base_symbol": base_symbol,
        "base_register": base_register_text,
        "base_evidence_id": evidence.get("base_evidence_id") if evidence is not None else None,
        "displacement": displacement,
        "operand_index": operand_index,
    }


def _rsset_binding_evidence_parameters(context: Mapping[str, object], base_register: str) -> dict[str, str] | None:
    layout_name = str(context.get("layout_name") or "app").strip() or "app"
    base_symbol = str(context.get("base_symbol") or "__amiga_app_base__").strip() or "__amiga_app_base__"
    base_evidence_id = context.get("base_evidence_id")
    if isinstance(base_evidence_id, str) and base_evidence_id.strip():
        return {
            "layout_name": layout_name,
            "base_symbol": base_symbol,
            "base_evidence_id": base_evidence_id.strip(),
        }
    if context.get("element_kind") == "app_slot":
        return {
            "layout_name": layout_name,
            "base_symbol": base_symbol,
            "base_evidence_id": f"selected-app-slot:{base_register}:{base_symbol}",
        }
    return None


def _rsset_use_site_binding_parameter_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "layout_name": {"type": "string", "default": "app"},
            "base_symbol": {"type": "string", "default": "__amiga_app_base__"},
            "base_evidence_id": {"type": "string"},
        },
        "required": ["base_evidence_id"],
    }


def _rsset_binding_width_bytes(context: Mapping[str, object], row: Mapping[str, object]) -> int | None:
    width_bytes = _optional_int(context.get("width_bytes"))
    if width_bytes is not None:
        return width_bytes
    opcode = str(row.get("opcode_or_directive") or row.get("opcode") or "")
    if opcode.endswith(".b"):
        return 1
    if opcode.endswith(".w"):
        return 2
    if opcode.endswith(".l"):
        return 4
    return None


def _signed_16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def _rsset_report_base_evidence_source(context: Mapping[str, object], has_base_evidence: bool) -> str:
    if context.get("element_kind") == "app_slot":
        return "selected_app_slot"
    if has_base_evidence:
        return "explicit_context"
    return "report_only_raw_displacement"


def _rsset_report_current_field(row: Mapping[str, object], displacement: int) -> dict[str, object] | None:
    for region in _rsset_report_regions(row):
        offset = _optional_int(region.get("offset"))
        end = _optional_int(region.get("end"))
        size = _optional_int(region.get("size"))
        if offset is None:
            continue
        if end is None and size is not None:
            end = offset + size
        if end is None:
            end = offset + 1
        if offset <= displacement < end:
            return _rsset_report_region_summary(region, offset, end)
    return None


def _rsset_report_current_gap(row: Mapping[str, object], displacement: int) -> dict[str, object] | None:
    for gap in _mapping_sequence(row.get("app_slot_gaps")):
        start = _optional_int(gap.get("start"))
        end = _optional_int(gap.get("end"))
        if start is None or end is None or not (start <= displacement < end):
            continue
        return {
            "start": start,
            "end": end,
            "size": max(0, end - start),
            **_optional_text_fields(gap, ("after", "before", "coverage")),
        }
    analysis = row.get("app_slot_analysis")
    if isinstance(analysis, Mapping):
        for gap in _mapping_sequence(analysis.get("gaps")):
            start = _optional_int(gap.get("start"))
            end = _optional_int(gap.get("end"))
            if start is None or end is None or not (start <= displacement < end):
                continue
            return {
                "start": start,
                "end": end,
                "size": max(0, end - start),
                **_optional_text_fields(gap, ("after", "before", "coverage")),
            }
    return None


def _rsset_report_nearby_fields(row: Mapping[str, object], displacement: int) -> list[dict[str, object]]:
    nearby: list[dict[str, object]] = []
    for region in _rsset_report_regions(row):
        offset = _optional_int(region.get("offset"))
        end = _optional_int(region.get("end"))
        size = _optional_int(region.get("size"))
        if offset is None:
            continue
        if end is None and size is not None:
            end = offset + size
        if end is None:
            end = offset + 1
        if abs(offset - displacement) <= 8 or abs(end - displacement) <= 8:
            nearby.append(_rsset_report_region_summary(region, offset, end))
    nearby.sort(key=lambda item: int(item.get("offset", 0)))
    return nearby[:6]


def _rsset_report_regions(row: Mapping[str, object]) -> list[Mapping[str, object]]:
    regions = _mapping_sequence(row.get("app_slot_regions"))
    analysis = row.get("app_slot_analysis")
    if isinstance(analysis, Mapping):
        regions.extend(_mapping_sequence(analysis.get("regions")))
    for raw_ref in _mapping_sequence(row.get("app_slot_refs") or row.get("appSlotRefs")):
        displacement = _optional_int(raw_ref.get("displacement"))
        if displacement is None:
            continue
        regions.append(raw_ref)
    return regions


def _rsset_report_region_summary(region: Mapping[str, object], offset: int, end: int) -> dict[str, object]:
    summary: dict[str, object] = {"offset": offset, "end": end, "size": max(0, end - offset)}
    for key in (
        "symbol",
        "source",
        "confidence",
        "struct_name",
        "storage_kind",
        "semantic_type",
        "parser_role",
    ):
        value = region.get(key)
        if isinstance(value, str) and value:
            summary[key] = value
    return summary


def _optional_text_fields(source: Mapping[str, object], keys: tuple[str, ...]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key in keys:
        value = source.get(key)
        if isinstance(value, str) and value:
            result[key] = value
    return result


def _rsset_report_type_compatibility(
    width_bytes: int | None,
    current_field: Mapping[str, object] | None,
    current_gap: Mapping[str, object] | None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "observed_width_bytes": width_bytes,
        "field_state": "field" if current_field else "gap" if current_gap else "unknown",
    }
    if current_field:
        field_size = _optional_int(current_field.get("size"))
        result["field_size"] = field_size
        result["width_matches_field"] = width_bytes is not None and field_size == width_bytes
    elif current_gap:
        gap_size = _optional_int(current_gap.get("size"))
        result["gap_size"] = gap_size
        result["width_fits_gap"] = width_bytes is not None and gap_size is not None and width_bytes <= gap_size
    else:
        result["blockers"] = ["no_field_or_gap_context"]
    return result


def _rsset_report_existing_xrefs(context: Mapping[str, object], row: Mapping[str, object], displacement: int) -> dict[str, object]:
    same_uses = _mapping_sequence(context.get("same_displacement_uses"))
    same_count = _optional_int(context.get("same_displacement_use_count"))
    slots = [
        slot
        for slot in _rsset_report_slots(row)
        if _optional_int(slot.get("displacement")) == displacement
    ]
    return {
        "same_displacement_use_count": same_count if same_count is not None else len(same_uses),
        "same_displacement_uses": same_uses,
        "app_slot_slots": [_rsset_report_slot_summary(slot) for slot in slots],
    }


def _rsset_report_slots(row: Mapping[str, object]) -> list[Mapping[str, object]]:
    slots = _mapping_sequence(row.get("app_slot_slots"))
    analysis = row.get("app_slot_analysis")
    if isinstance(analysis, Mapping):
        slots.extend(_mapping_sequence(analysis.get("slots")))
    return slots


def _rsset_report_slot_summary(slot: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key in (
        "symbol",
        "displacement",
        "ref_count",
        "observed_size",
        "observed_end",
        "first_addr",
        "last_addr",
        "first_row_index",
        "last_row_index",
    ):
        value = slot.get(key)
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            result[key] = value
    for key in ("access_counts", "width_counts"):
        value = slot.get(key)
        if isinstance(value, Mapping):
            result[key] = dict(value)
    return result


def _rsset_binding_report(
    context: Mapping[str, object],
    row: Mapping[str, object],
    params: Mapping[str, object],
) -> dict[str, object]:
    displacement = _optional_int(params.get("displacement")) or 0
    width_bytes = _rsset_binding_width_bytes(context, row)
    current_field = _rsset_report_current_field(row, displacement)
    current_gap = _rsset_report_current_gap(row, displacement)
    base_evidence_id = params.get("base_evidence_id")
    has_base_evidence = isinstance(base_evidence_id, str) and bool(base_evidence_id.strip())
    base_evidence_refs = _rsset_base_evidence_refs(context, row, params)
    compatibility = _rsset_report_type_compatibility(width_bytes, current_field, current_gap)
    missing_verifiers = ["bind_refine_selected_use_render", "owned_cascade_cleanup", "type_flow"]
    if not has_base_evidence:
        missing_verifiers.insert(0, "base_evidence")
    return {
        "kind": "rsset_binding_report",
        "candidate": {
            "layout_name": params.get("layout_name"),
            "base_symbol": params.get("base_symbol"),
            "base_register": params.get("base_register"),
            "base_evidence_id": base_evidence_id,
            "displacement": displacement,
        },
        "source_locator": {
            "hunk": context.get("hunk"),
            "addr": context.get("addr") or context.get("start_offset"),
            "stable_key": context.get("stable_key") or row.get("row_key") or row.get("stable_key"),
            "row_text": str(row.get("text") or "").strip(),
            "operand_index": params.get("operand_index"),
            "current_rendered_text": row.get("operand_text") or row.get("text"),
        },
        "operand_facts": {
            "base_register": params.get("base_register"),
            "displacement": displacement,
            "signed_displacement": _signed_16(displacement),
            "operand_index": params.get("operand_index"),
            "access": context.get("access") or "reference",
            "width_bytes": width_bytes,
            "address_mode": "address_register_displacement",
        },
        "base_evidence": {
            "base_register": params.get("base_register"),
            "base_evidence_id": base_evidence_id,
            "has_explicit_evidence": has_base_evidence,
            "source": _rsset_report_base_evidence_source(context, has_base_evidence),
            "blockers": [] if has_base_evidence else ["missing_base_evidence"],
            "base_evidence_refs": base_evidence_refs,
        },
        "base_evidence_refs": base_evidence_refs,
        "candidate_layouts": [
            {
                "layout_name": params.get("layout_name"),
                "base_symbol": params.get("base_symbol"),
                "field_at_displacement": current_field,
                "gap_covering_displacement": current_gap,
                "nearby_fields": _rsset_report_nearby_fields(row, displacement),
            }
        ],
        "type_compatibility": compatibility,
        "existing_xrefs": _rsset_report_existing_xrefs(context, row, displacement),
        "expected_cascade": {
            "selected_use_render": "field_symbol" if current_field else "raw_or_linked_gap",
            "same_displacement_candidates": "deferred_until_selected_use_verified",
            "generated_xrefs": "deferred_until_symbolic_selected_use_or_refinement",
            "cleanup_owner": "manual_action_id_after_bind",
            "review_items": "missing_field" if current_gap and not current_field else None,
        },
        "selected_use": {
            "hunk": context.get("hunk"),
            "addr": context.get("addr") or context.get("start_offset"),
            "operand_index": params.get("operand_index"),
            "access": context.get("access") or "reference",
            "width_bytes": width_bytes,
        },
        "render": {
            "state": "field_available" if current_field else "linked_gap_or_raw",
            "reason": (
                "An existing field may render after bind verification."
                if current_field
                else "No field is created by bind-only; source rendering changes after a field/refinement action."
            ),
        },
        "verifier_readiness": {
            "replay": "ready",
            "exact_round_trip": "ready",
            "selected_use_render": "ready_if_existing_field" if current_field else "blocked_until_field_refinement",
            "xref": "blocked_until_symbolic_selected_use",
            "type_flow": "blocked_until_type_refinement_verifier",
            "cleanup": "binding_state_ready_descendant_cleanup_planned",
            "missing_verifier_blockers": missing_verifiers,
        },
    }


def _rsset_base_evidence_refs(
    context: Mapping[str, object],
    row: Mapping[str, object],
    params: Mapping[str, object],
) -> list[dict[str, object]]:
    report = _provenance_report(context, row)
    if report is None:
        return []
    subject = report.get("subject")
    definitions = report.get("definitions")
    definition = definitions[0] if isinstance(definitions, list) and definitions and isinstance(definitions[0], dict) else {}
    parent_ids = definition.get("parent_evidence_ids") if isinstance(definition, dict) else None
    parent_evidence_ids: list[str] = []
    if isinstance(parent_ids, list):
        parent_evidence_ids = [item for item in parent_ids if isinstance(item, str) and item]
    source_family = report.get("source_family")
    status = report.get("status")
    source_evidence_id = report.get("source_evidence_id")
    base_evidence_id = params.get("base_evidence_id")
    accepted = (
        isinstance(source_evidence_id, str)
        and isinstance(source_family, str)
        and source_family not in {"", "unknown", "conflicting"}
        and status in {"analysis_proven", "path_specific", "manual_classified", "manual_override"}
        and isinstance(base_evidence_id, str)
        and bool(base_evidence_id.strip())
    )
    ref = {
        "operand_index": params.get("operand_index"),
        "base_register": params.get("base_register"),
        "displacement": params.get("displacement"),
        "source_family": source_family,
        "status": status,
        "source_evidence_id": source_evidence_id,
        "base_evidence_id": base_evidence_id,
        "path_lifetime_scope": report.get("path_lifetime_scope"),
        "confidence": report.get("confidence"),
        "origin_kind": definition.get("origin_kind") if isinstance(definition, dict) else None,
        "origin_hunk": definition.get("origin_hunk") if isinstance(definition, dict) else None,
        "origin_offset": definition.get("origin_addr") if isinstance(definition, dict) else None,
        "origin_register": definition.get("register") if isinstance(definition, dict) else None,
        "layout_name": params.get("layout_name"),
        "base_symbol": params.get("base_symbol"),
        "conflicts": report.get("conflicts"),
        "accepted": accepted,
    }
    for key in ("contradicted_evidence_id", "reason"):
        value = context.get(key)
        if isinstance(value, str) and value.strip():
            ref[key] = value.strip()
    if parent_evidence_ids:
        ref["parent_evidence_ids"] = parent_evidence_ids
    if isinstance(subject, Mapping):
        ref["subject"] = {
            key: subject.get(key)
            for key in ("target", "hunk", "addr", "stable_key", "row_text", "element_id", "element_kind")
            if subject.get(key) is not None
        }
    return [{key: value for key, value in ref.items() if value is not None}]


def _rsset_use_site_binding_payload(
    row: Mapping[str, object],
    context: Mapping[str, object],
    params: Mapping[str, object],
) -> dict[str, object]:
    hunk = _int_field(row, "section_index", default=0)
    addr = _int_field(row, "start_offset", fallback="addr")
    displacement = _optional_int(params.get("displacement"))
    operand_index = _optional_int(params.get("operand_index"))
    base_register = params.get("base_register")
    if displacement is None or operand_index is None or not isinstance(base_register, str) or not base_register:
        raise ValueError("create_manual_rsset_use_site_binding requires base_register, displacement, and operand_index")
    layout_name = str(params.get("layout_name") or "app").strip() or "app"
    base_symbol = str(params.get("base_symbol") or "__amiga_app_base__").strip() or "__amiga_app_base__"
    base_evidence_id = str(params.get("base_evidence_id") or "").strip()
    if not base_evidence_id:
        raise ValueError("create_manual_rsset_use_site_binding requires base_evidence_id")
    binding: dict[str, object] = {
        "rsset_use_site_binding_id": _rsset_use_site_binding_id(
            hunk=hunk,
            addr=addr,
            operand_index=operand_index,
            base_register=base_register,
            displacement=displacement,
            layout_name=layout_name,
            base_symbol=base_symbol,
            base_evidence_id=base_evidence_id,
        ),
        "hunk": hunk,
        "addr": addr,
        "operand_index": operand_index,
        "base_register": base_register.upper(),
        "displacement": displacement,
        "layout_name": layout_name,
        "base_symbol": base_symbol,
        "base_evidence_id": base_evidence_id,
        "access": context.get("access") or "reference",
        "render_state": "linked_gap_or_raw",
    }
    evidence_refs = _rsset_base_evidence_refs(context, row, params)
    accepted_ref = next((ref for ref in evidence_refs if ref.get("accepted") is True), None)
    if evidence_refs:
        binding["base_evidence_refs"] = evidence_refs
    if accepted_ref is not None:
        binding["source_evidence_id"] = accepted_ref.get("source_evidence_id")
        binding["source_family"] = accepted_ref.get("source_family")
        binding["source_evidence_status"] = accepted_ref.get("status")
        binding["path_lifetime_scope"] = accepted_ref.get("path_lifetime_scope")
        binding["confidence"] = accepted_ref.get("confidence")
        binding["conflicts"] = accepted_ref.get("conflicts", [])
        for key in ("contradicted_evidence_id", "reason"):
            if key in accepted_ref:
                binding[key] = accepted_ref[key]
    width_bytes = _optional_int(context.get("width_bytes"))
    if width_bytes is not None:
        binding["width_bytes"] = width_bytes
    row_index = _optional_int(row.get("row_index"))
    if row_index is not None:
        binding["row_index"] = row_index
    for field_name in ("stable_key", "row_id", "text"):
        value = row.get(field_name)
        if isinstance(value, str) and value:
            binding[field_name if field_name != "text" else "source_text"] = value.strip()
    element_id = context.get("element_id")
    if isinstance(element_id, str) and element_id:
        binding["element_id"] = element_id
    return binding


def _rsset_use_site_binding_identity_payload(
    row: Mapping[str, object],
    context: Mapping[str, object],
    params: Mapping[str, object],
) -> dict[str, object]:
    payload = _rsset_use_site_binding_payload(row, context, params)
    return {
        key: payload[key]
        for key in (
            "rsset_use_site_binding_id",
            "hunk",
            "addr",
            "operand_index",
            "base_register",
            "base_evidence_id",
            "displacement",
            "layout_name",
            "base_symbol",
            "source_evidence_id",
            "source_family",
            "source_evidence_status",
            "path_lifetime_scope",
            "confidence",
            "conflicts",
            "contradicted_evidence_id",
            "reason",
            "base_evidence_refs",
        )
        if key in payload
    }


def _rsset_use_site_binding_id(
    *,
    hunk: int,
    addr: int,
    operand_index: int,
    base_register: str,
    displacement: int,
    layout_name: str,
    base_symbol: str,
    base_evidence_id: str,
) -> str:
    return (
        f"rsset-binding-h{hunk}-{addr:08X}-op{operand_index}-"
        f"{base_register.upper()}-{displacement:04X}-{_id_token(layout_name)}-"
        f"{_id_token(base_symbol)}-{_id_token(base_evidence_id)}"
    )


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


def _typed_field_action_parameters(context: Mapping[str, object], row: Mapping[str, object]) -> dict[str, object]:
    params = _typed_field_identity_parameters(context)
    _attach_custom_struct_field_evidence(params, params, context, row)
    return params


def _attach_custom_struct_field_evidence(
    field: dict[str, object],
    params: Mapping[str, object],
    context: Mapping[str, object],
    row: Mapping[str, object],
) -> None:
    report = _provenance_report(context, row)
    evidence_source: Mapping[str, object] = params
    if not isinstance(params.get("source_evidence_id"), str) and isinstance(context.get("source_evidence_id"), str):
        evidence_source = context
    elif not isinstance(params.get("source_evidence_id"), str) and report is not None:
        evidence_source = {
            "source_evidence_id": report.get("source_evidence_id"),
            "source_family": report.get("source_family"),
            "source_evidence_status": report.get("status"),
            "path_lifetime_scope": report.get("path_lifetime_scope"),
            "confidence": report.get("confidence"),
            "conflicts": report.get("conflicts"),
            "parent_evidence_ids": report.get("parent_evidence_ids"),
        }
    for key in (
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "path_lifetime_scope",
        "confidence",
        "conflicts",
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
    ):
        value = evidence_source.get(key)
        if value is not None:
            field[key] = value


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
            "parent_evidence_ids": {"type": "array", "items": {"type": "string"}},
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
            "value_representation": {
                "type": "string",
                "enum": ["hex", "decimal", "binary", "character", "symbol"],
            },
            "value_expression": {"type": "string"},
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
            "parent_evidence_ids": {"type": "array", "items": {"type": "string"}},
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


def _data_block_layout_payload(rows: list[Mapping[str, object]], params: Mapping[str, object]) -> dict[str, object]:
    first = rows[0]
    last = rows[-1]
    source_start = _int_field(first, "start_offset", fallback="addr")
    source_end = _optional_int(last.get("end_offset"))
    if source_end is None:
        source_end = _optional_int(last.get("start_offset"))
    if source_end is None:
        source_end = _optional_int(last.get("addr"))
    if source_end is None or source_end <= source_start:
        raise ValueError("create_manual_data_block_layout requires a non-empty source range")
    hunk = _int_field(first, "section_index", default=0)
    layout: dict[str, object] = {
        "layout_id": f"catalog-{uuid.uuid4().hex}",
        "hunk": hunk,
        "source_start": source_start,
        "source_end": source_end,
        "row_indexes": [
            index for row in rows if (index := _optional_int(row.get("row_index"))) is not None
        ],
    }
    name = params.get("name")
    if isinstance(name, str) and name.strip():
        layout["name"] = name.strip()
    role = params.get("role")
    if isinstance(role, str) and role.strip():
        layout["role"] = role.strip()
    default_unit = params.get("default_unit")
    if isinstance(default_unit, str) and default_unit in {"byte", "word", "long"}:
        layout["default_unit"] = default_unit
    return layout


def _data_block_element_context(rows: list[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    first = rows[0]
    last = rows[-1]
    layout = _active_data_block_layout(first)
    if layout is None:
        return {}
    layout_id = str(layout.get("layout_id") or "").strip()
    layout_hunk = _optional_int(layout.get("hunk"))
    layout_start = _optional_int(layout.get("source_start"))
    layout_end = _optional_int(layout.get("source_end"))
    if not layout_id or layout_hunk is None or layout_start is None or layout_end is None:
        return {}
    hunk = _int_field(first, "section_index", default=0)
    source_start = _int_field(first, "start_offset", fallback="addr")
    source_end = _optional_int(last.get("end_offset"))
    if source_end is None:
        source_end = _optional_int(last.get("start_offset"))
    if source_end is None:
        source_end = _optional_int(last.get("addr"))
    if hunk != layout_hunk or source_end is None or source_start < layout_start or source_end > layout_end:
        return {}
    context: dict[str, object] = {"layout_id": layout_id, "offset": source_start - layout_start, "width": source_end - source_start}
    active_element = _active_data_block_element(first, context)
    if active_element is not None:
        for key in (
            "width",
            "kind",
            "name",
            "array_count",
            "array_stride",
            "representation",
            "type_binding",
            "provenance",
        ):
            value = active_element.get(key)
            if value is not None:
                context[key] = value
    return context


def _active_data_block_layout(row: Mapping[str, object]) -> Mapping[str, object] | None:
    for key in ("active_data_block_layout", "data_block_layout"):
        layout = row.get(key)
        if isinstance(layout, Mapping):
            return layout
    layouts = row.get("data_block_layouts")
    if not isinstance(layouts, list | tuple):
        return None
    hunk = _optional_int(row.get("section_index"))
    start = _optional_int(row.get("start_offset"))
    end = _optional_int(row.get("end_offset"))
    if hunk is None or start is None:
        return None
    end = end if end is not None else start
    matches: list[Mapping[str, object]] = []
    for layout in layouts:
        if not isinstance(layout, Mapping):
            continue
        layout_hunk = _optional_int(layout.get("hunk"))
        layout_start = _optional_int(layout.get("source_start"))
        layout_end = _optional_int(layout.get("source_end"))
        if (
            layout_hunk == hunk
            and layout_start is not None
            and layout_end is not None
            and layout_start <= start
            and end <= layout_end
        ):
            matches.append(layout)
    return matches[0] if len(matches) == 1 else None


def _active_data_block_element(
    row: Mapping[str, object],
    context: Mapping[str, object],
) -> Mapping[str, object] | None:
    for key in ("active_data_block_element", "data_block_element"):
        element = row.get(key)
        if isinstance(element, Mapping):
            return element
    elements = row.get("data_block_elements")
    if not isinstance(elements, list | tuple):
        return None
    layout_id = context.get("layout_id")
    offset = context.get("offset")
    matches: list[Mapping[str, object]] = []
    for element in elements:
        if not isinstance(element, Mapping):
            continue
        if layout_id is not None and element.get("layout_id") != layout_id:
            continue
        if offset is not None and _optional_int(element.get("offset")) != offset:
            continue
        matches.append(element)
    return matches[0] if len(matches) == 1 else None


def _data_block_element_ref_context(row: Mapping[str, object]) -> dict[str, object]:
    context = _data_block_element_context([row])
    ref = _active_data_block_interpreted_ref(row, context)
    if ref is None:
        return context
    merged = dict(context)
    for key in ("data_block_ref_id", "reference_kind", "target_hunk", "target_offset"):
        value = ref.get(key)
        if value is not None:
            merged[key] = value
    return merged


def _active_data_block_interpreted_ref(
    row: Mapping[str, object],
    context: Mapping[str, object],
) -> Mapping[str, object] | None:
    for key in ("active_data_block_interpreted_ref", "data_block_interpreted_ref"):
        ref = row.get(key)
        if isinstance(ref, Mapping):
            return ref
    refs = row.get("data_block_interpreted_refs")
    if not isinstance(refs, list | tuple):
        return None
    layout_id = context.get("layout_id")
    offset = context.get("offset")
    matches: list[Mapping[str, object]] = []
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        if layout_id is not None and ref.get("layout_id") != layout_id:
            continue
        if offset is not None and _optional_int(ref.get("offset")) != offset:
            continue
        matches.append(ref)
    return matches[0] if len(matches) == 1 else None


def _data_block_element_payload(rows: list[Mapping[str, object]], params: Mapping[str, object]) -> dict[str, object]:
    context = _data_block_element_context(rows)
    layout_id = str(params.get("layout_id") or context.get("layout_id") or "").strip()
    offset = _optional_int(params.get("offset"))
    if offset is None:
        offset = _optional_int(context.get("offset"))
    if not layout_id:
        raise ValueError("set_manual_data_block_element requires layout_id")
    if offset is None or offset < 0:
        raise ValueError("set_manual_data_block_element requires non-negative offset")
    width = _optional_int(params.get("width"))
    if width is None:
        width = _optional_int(context.get("width"))
    if width is None:
        source_start = _int_field(rows[0], "start_offset", fallback="addr")
        source_end = _optional_int(rows[-1].get("end_offset"))
        if source_end is not None and source_end > source_start:
            width = source_end - source_start
    if width is None or width <= 0:
        raise ValueError("set_manual_data_block_element requires positive width")
    kind = str(params.get("kind") or "raw").strip() or "raw"
    if kind not in {"scalar", "array", "padding", "gap", "raw"}:
        raise ValueError("set_manual_data_block_element kind is unsupported")
    element: dict[str, object] = {
        "data_block_element_id": f"{layout_id}:{offset:X}",
        "layout_id": layout_id,
        "offset": offset,
        "width": width,
        "kind": kind,
    }
    for field_name in ("name", "representation"):
        value = params.get(field_name)
        if isinstance(value, str) and value.strip():
            element[field_name] = value.strip()
    for field_name in ("array_count", "array_stride"):
        value = _optional_int(params.get(field_name))
        if value is not None:
            element[field_name] = value
    return element


def _data_block_element_type_binding_payload(
    rows: list[Mapping[str, object]],
    params: Mapping[str, object],
) -> dict[str, object]:
    element = _data_block_element_payload(rows, params)
    binding_kind = str(params.get("binding_kind") or "").strip()
    if binding_kind not in {"custom_struct", "platform_struct", "enum_domain", "equate_domain"}:
        raise ValueError("bind data-block element type requires binding_kind")
    type_id = str(params.get("type_id") or "").strip()
    domain_id = str(params.get("domain_id") or "").strip()
    bound_id_key = "bound_domain_id" if binding_kind.endswith("_domain") else "bound_type_id"
    bound_id = domain_id if binding_kind.endswith("_domain") else type_id
    if not bound_id:
        raise ValueError("bind data-block element type requires type_id or domain_id")
    width = cast(int, element["width"])
    offset = cast(int, element["offset"])
    layout_id = cast(str, element["layout_id"])
    binding: dict[str, object] = {
        "type_binding_id": str(
            params.get("type_binding_id") or f"{layout_id}:{offset:X}:{width}:{binding_kind}:{bound_id}"
        ),
        "layout_id": layout_id,
        "element_offset": offset,
        "element_width": width,
        "binding_kind": binding_kind,
        bound_id_key: bound_id,
    }
    array_count = _optional_int(params.get("array_count") or element.get("array_count"))
    if array_count is not None:
        binding["array_count"] = array_count
    for key in (
        "source_evidence_id",
        "source_family",
        "source_evidence_status",
        "requires_source_evidence",
        "parent_evidence_ids",
        "contradicted_evidence_id",
        "reason",
        "cleanup_scope",
    ):
        value = params.get(key)
        if value is not None:
            binding[key] = value
    for key in ("path_lifetime_scope", "conflicts"):
        value = params.get(key)
        if isinstance(value, dict | list):
            binding[key] = value
    if binding_kind == "custom_struct":
        element["kind"] = "struct"
    elif binding_kind == "platform_struct":
        element["kind"] = "platform_struct"
    elif element.get("kind") == "raw":
        element["kind"] = "scalar"
    element["type_binding"] = binding
    return element


def _data_block_element_clear_type_payload(
    rows: list[Mapping[str, object]],
    params: Mapping[str, object],
) -> dict[str, object]:
    context = _data_block_element_context(rows)
    element = _data_block_element_payload(rows, params)
    previous = context.get("type_binding")
    if isinstance(previous, Mapping):
        element["previous_type_binding"] = dict(previous)
    element.pop("type_binding", None)
    return element


def _data_block_element_remove_payload(
    rows: list[Mapping[str, object]],
    params: Mapping[str, object],
) -> dict[str, object]:
    context = _data_block_element_context(rows)
    layout_id = str(params.get("layout_id") or context.get("layout_id") or "").strip()
    offset = _optional_int(params.get("offset"))
    if offset is None:
        offset = _optional_int(context.get("offset"))
    if not layout_id:
        raise ValueError("remove_manual_data_block_element requires layout_id")
    if offset is None or offset < 0:
        raise ValueError("remove_manual_data_block_element requires non-negative offset")
    element: dict[str, object] = {"layout_id": layout_id, "offset": offset}
    width = _optional_int(params.get("width"))
    if width is None:
        width = _optional_int(context.get("width"))
    if width is None and rows:
        source_start = _int_field(rows[0], "start_offset", fallback="addr")
        source_end = _optional_int(rows[-1].get("end_offset"))
        if source_end is not None and source_end > source_start:
            width = source_end - source_start
    if width is not None:
        element["width"] = width
    removal_state = params.get("removal_state")
    if isinstance(removal_state, str) and removal_state in {"raw", "gap"}:
        element["removal_state"] = removal_state
    return element


def _data_block_element_representation_payload(
    rows: list[Mapping[str, object]],
    params: Mapping[str, object],
) -> dict[str, object]:
    context = _data_block_element_context(rows)
    layout_id = str(params.get("layout_id") or context.get("layout_id") or "").strip()
    offset = _optional_int(params.get("offset"))
    if offset is None:
        offset = _optional_int(context.get("offset"))
    representation = params.get("representation")
    if not layout_id:
        raise ValueError("represent_manual_data_block_element requires layout_id")
    if offset is None or offset < 0:
        raise ValueError("represent_manual_data_block_element requires non-negative offset")
    if representation not in {"hex", "binary", "character"}:
        raise ValueError("represent_manual_data_block_element requires representation")
    return {"layout_id": layout_id, "offset": offset, "representation": representation}


def _data_block_element_ref_payload(
    rows: list[Mapping[str, object]],
    params: Mapping[str, object],
) -> dict[str, object]:
    context = _data_block_element_context(rows)
    layout_id = str(params.get("layout_id") or context.get("layout_id") or "").strip()
    offset = _optional_int(params.get("offset"))
    if offset is None:
        offset = _optional_int(context.get("offset"))
    width = _optional_int(params.get("width"))
    if width is None:
        width = _optional_int(context.get("width"))
    reference_kind = str(params.get("reference_kind") or "").strip()
    target_hunk = _optional_int(params.get("target_hunk"))
    target_offset = _optional_int(params.get("target_offset"))
    if not layout_id:
        raise ValueError("interpret_manual_data_block_element_ref requires layout_id")
    if offset is None or offset < 0:
        raise ValueError("interpret_manual_data_block_element_ref requires non-negative offset")
    if width is None or width <= 0:
        raise ValueError("interpret_manual_data_block_element_ref requires positive width")
    if width not in {1, 2, 4}:
        raise ValueError("interpret_manual_data_block_element_ref supports only byte, word, and long widths")
    if reference_kind != "absolute":
        raise ValueError("interpret_manual_data_block_element_ref supports only absolute references")
    if target_hunk is None or target_hunk < 0:
        raise ValueError("interpret_manual_data_block_element_ref requires non-negative target_hunk")
    if target_offset is None or target_offset < 0:
        raise ValueError("interpret_manual_data_block_element_ref requires non-negative target_offset")
    source_value = _data_block_ref_source_value(rows, width)
    if source_value != target_offset:
        raise ValueError("interpret_manual_data_block_element_ref target_offset must match selected source bytes")
    ref_id = str(params.get("data_block_ref_id") or "").strip()
    if not ref_id:
        ref_id = f"{layout_id}:{offset:X}:{reference_kind}:h{target_hunk}:{target_offset:08X}"
    confidence = str(params.get("confidence") or "manual").strip() or "manual"
    if confidence not in {"manual", "high", "medium", "low"}:
        raise ValueError("interpret_manual_data_block_element_ref confidence is unsupported")
    xref_generation_mode = str(params.get("xref_generation_mode") or "bidirectional").strip() or "bidirectional"
    if xref_generation_mode not in {"bidirectional", "source_only", "none"}:
        raise ValueError("interpret_manual_data_block_element_ref xref_generation_mode is unsupported")
    ref: dict[str, object] = {
        "data_block_ref_id": ref_id,
        "layout_id": layout_id,
        "offset": offset,
        "width": width,
        "reference_kind": reference_kind,
        "target_hunk": target_hunk,
        "target_offset": target_offset,
        "target_locator": {"hunk": target_hunk, "offset": target_offset},
        "source_value": source_value,
        "confidence": confidence,
        "xref_generation_mode": xref_generation_mode,
    }
    signed = params.get("signed")
    if isinstance(signed, bool):
        ref["signed"] = signed
    scale = _optional_int(params.get("scale"))
    if scale is not None:
        if scale <= 0:
            raise ValueError("interpret_manual_data_block_element_ref scale must be positive")
        ref["scale"] = scale
    for field_name in ("base_evidence_id", "source_evidence_id"):
        value = params.get(field_name)
        if isinstance(value, str) and value.strip():
            ref[field_name] = value.strip()
    return ref


def _data_block_ref_source_value(rows: list[Mapping[str, object]], width: int) -> int:
    if not rows:
        raise ValueError("interpret_manual_data_block_element_ref requires selected source bytes")
    raw_bytes = rows[0].get("bytes")
    if not isinstance(raw_bytes, str) or not raw_bytes:
        raise ValueError("interpret_manual_data_block_element_ref requires selected source bytes")
    try:
        data = bytes.fromhex(raw_bytes)
    except ValueError as exc:
        raise ValueError("interpret_manual_data_block_element_ref requires valid selected source bytes") from exc
    if len(data) < width:
        raise ValueError("interpret_manual_data_block_element_ref selected source bytes are shorter than width")
    return int.from_bytes(data[:width], "big")


def _data_block_element_ref_remove_payload(
    rows: list[Mapping[str, object]],
    params: Mapping[str, object],
) -> dict[str, object]:
    context = _data_block_element_ref_context(rows[0]) if rows else {}
    layout_id = str(params.get("layout_id") or context.get("layout_id") or "").strip()
    offset = _optional_int(params.get("offset"))
    if offset is None:
        offset = _optional_int(context.get("offset"))
    if not layout_id:
        raise ValueError("remove_manual_data_block_element_ref requires layout_id")
    if offset is None or offset < 0:
        raise ValueError("remove_manual_data_block_element_ref requires non-negative offset")
    ref_id = str(params.get("data_block_ref_id") or context.get("data_block_ref_id") or "").strip()
    if not ref_id:
        reference_kind = str(params.get("reference_kind") or context.get("reference_kind") or "").strip()
        target_hunk = _optional_int(params.get("target_hunk"))
        if target_hunk is None:
            target_hunk = _optional_int(context.get("target_hunk"))
        target_offset = _optional_int(params.get("target_offset"))
        if target_offset is None:
            target_offset = _optional_int(context.get("target_offset"))
        if reference_kind and target_hunk is not None and target_offset is not None:
            ref_id = f"{layout_id}:{offset:X}:{reference_kind}:h{target_hunk}:{target_offset:08X}"
    if not ref_id:
        raise ValueError("remove_manual_data_block_element_ref requires data_block_ref_id")
    ref: dict[str, object] = {"data_block_ref_id": ref_id, "layout_id": layout_id, "offset": offset}
    for field_name in ("reference_kind", "target_hunk", "target_offset"):
        value = params.get(field_name) if field_name in params else context.get(field_name)
        if value is not None:
            ref[field_name] = value
    return ref


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


def _target_equate_represent_action() -> dict[str, object]:
    return _target_log_action(
        "target.equate.represent",
        "Represent equate value",
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


def _mapping_sequence(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _object(value: object, description: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{description} is missing")
    return value
