from __future__ import annotations

import time
from pathlib import Path


class FactsV2SourceRefused(RuntimeError):
    def __init__(self, listing_profile: dict[str, object]) -> None:
        self.listing_profile = listing_profile
        super().__init__(facts_v2_source_refusal_message(listing_profile))


def facts_v2_source_refused(listing_profile: dict[str, object]) -> bool:
    facts_v2 = listing_profile.get("facts_v2")
    return isinstance(facts_v2, dict) and facts_v2.get("asm_source_refused") is True


def facts_v2_source_refusal_message(listing_profile: dict[str, object]) -> str:
    facts_v2 = listing_profile.get("facts_v2")
    if not isinstance(facts_v2, dict):
        return "facts_v2 asm source refused"
    unassemblable_data_relocations = int(facts_v2.get("unassemblable_hunk_data_relocations") or 0)
    unassemblable_base_register_relocations = int(
        facts_v2.get("unassemblable_hunk_base_register_relocations") or 0
    )
    relocation_anchors = int(facts_v2.get("relocation_anchors") or 0)
    if unassemblable_base_register_relocations:
        return _relocation_anchor_message(
            facts_v2,
            "unassemblable_hunk_base_register_relocation",
        )
    if unassemblable_data_relocations:
        return _relocation_anchor_message(
            facts_v2,
            "unassemblable_hunk_data_relocation",
        )
    if relocation_anchors:
        return _relocation_anchor_message(facts_v2, "relocation_anchor")
    relocation_failures = int(facts_v2.get("relocation_failures") or 0)
    if relocation_failures:
        return (
            "facts_v2 asm source refused"
            f" relocation_reason={facts_v2.get('first_relocation_failure_reason')}"
            f" section={facts_v2.get('first_relocation_failure_section')}"
            f" offset={facts_v2.get('first_relocation_failure_offset')}"
            f" target_section={facts_v2.get('first_relocation_failure_target_section')}"
            f" raw_value={facts_v2.get('first_relocation_failure_raw_value')}"
            f" computed_target={facts_v2.get('first_relocation_failure_computed_target')}"
        )
    required_instruction_failures = int(facts_v2.get("required_instruction_failures") or 0)
    if required_instruction_failures:
        return (
            "facts_v2 asm source refused"
            f" required_instruction_failure section={facts_v2.get('first_required_instruction_failure_section')}"
            f" offset={facts_v2.get('first_required_instruction_failure_offset')}"
            f" code_start_reason={facts_v2.get('first_required_instruction_failure_reason')}"
            f" source_section={facts_v2.get('first_required_instruction_failure_source_section')}"
            f" source_offset={facts_v2.get('first_required_instruction_failure_source_offset')}"
        )
    return (
        "facts_v2 asm source refused"
        f" kind={facts_v2.get('asm_source_first_failure_kind')}"
        f" section={facts_v2.get('asm_source_first_failure_section')}"
        f" offset={facts_v2.get('asm_source_first_failure_offset')}"
        f" aux_offset={facts_v2.get('asm_source_first_failure_aux_offset')}"
    )


def facts_v2_source_refused_report(
    target_name: str,
    *,
    input_stamp: dict[str, object],
    listing_profile: dict[str, object],
    source_path: str | Path,
    rebuilt_path: str | Path,
    started_at: float,
) -> dict[str, object]:
    message = facts_v2_source_refusal_message(listing_profile)
    return {
        "target": target_name,
        "status": "render_error",
        "exact": False,
        "started_at": started_at,
        "finished_at": time.time(),
        "input_stamp": input_stamp,
        "analysis_backend": input_stamp.get("analysis_backend"),
        "backend": input_stamp.get("backend"),
        "assembler": input_stamp.get("assembler"),
        "assembler_cpu": input_stamp.get("assembler_cpu"),
        "source_path": str(source_path),
        "rebuilt_path": str(rebuilt_path),
        "original_size": input_stamp.get("original_size"),
        "tool_error": message,
        "issues": [{"kind": "renderer", "message": message, "row": None}],
        "assembler_stdout": "",
        "assembler_stderr": "",
        "listing_profile": listing_profile,
    }


def _relocation_anchor_message(facts_v2: dict[str, object], field_name: str) -> str:
    return (
        "facts_v2 asm source refused"
        f" {field_name}={facts_v2.get('first_relocation_anchor_kind')}"
        f" context={facts_v2.get('first_relocation_anchor_context')}"
        f" section={facts_v2.get('first_relocation_anchor_section')}"
        f" offset={facts_v2.get('first_relocation_anchor_offset')}"
        f" instruction_offset={facts_v2.get('first_relocation_anchor_instruction_offset')}"
        f" target_section={facts_v2.get('first_relocation_anchor_target_section')}"
        f" record_kind={facts_v2.get('first_relocation_anchor_platform_record_kind')}"
        f" raw_value={facts_v2.get('first_relocation_anchor_raw_value')}"
        f" addend={facts_v2.get('first_relocation_anchor_addend')}"
    )
