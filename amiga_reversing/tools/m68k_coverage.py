from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "src" / "scripts"
ASM_TABLE_PATH = ROOT / "src" / "generated" / "m68k_asm_tables.c"
DISASM_TABLE_PATH = ROOT / "src" / "generated" / "m68k_disassembler_tables.h"
GENERATED_FORM_ROW_RE = re.compile(
    r'^\s*\{\s*"(?P<mnemonic>(?:\\.|[^"])*)",\s*"(?P<syntax>(?:\\.|[^"])*)",\s*'
    r"M68K_ASM_MNEMONIC_[A-Za-z0-9_]+,\s*(?P<form_index>\d+)u?,\s*(?P<canonical_form_id>\d+)u?,"
)
NUMBER_RE = re.compile(r"0x[0-9A-Fa-f]+|\d+")

DIAGNOSTIC_DELETION_CRITERIA = (
    "Temporary bootstrap inventory. Delete or fold into canonical-model coverage "
    "after PRD 024/025 own canonical form identity and sample coverage."
)
CANONICAL_DELETION_CRITERIA = (
    "Canonical strict surface is active for inspection now. Final gating is owned by PRD 026 "
    "after legacy fallback paths are deleted and final generated coverage verification passes."
)
DIAGNOSTIC_FORM_STATUSES = {"matched", "asm_only", "disasm_only"}
DIAGNOSTIC_SAMPLE_STATUSES = {
    "sampled",
    "missing_sample_strategy",
    "intentionally_unsupported",
    "implemented_unsupported",
    "not_target_cpu",
    "oracle_unavailable",
}
DIAGNOSTIC_UNSUPPORTED_SAMPLE_STATUSES = {"intentionally_unsupported", "implemented_unsupported"}
CANONICAL_UNSUPPORTED_FAMILIES = (
    {
        "family_id": "move16",
        "status": "implemented_unsupported",
        "mnemonics": ("MOVE16",),
        "reason_category": "generated_semantics_missing",
        "blocking_artifacts": ("canonical_sample_plan", "generated_semantics", "oracle_support"),
        "reason": (
            "MOVE16 decode/render forms exist, but generated sample plans and semantics do not yet model "
            "cache-line transfer behavior or oracle support."
        ),
    },
    {
        "family_id": "fsave_frestore",
        "status": "implemented_unsupported",
        "mnemonics": ("FSAVE", "FRESTORE"),
        "reason_category": "generated_semantics_missing",
        "blocking_artifacts": ("canonical_sample_plan", "generated_semantics", "oracle_support"),
        "reason": (
            "FPU state-frame save/restore forms are generated, but sample plans and semantics do not yet "
            "represent implementation-specific state frames or oracle support."
        ),
    },
    {
        "family_id": "pmmu",
        "status": "implemented_unsupported",
        "mnemonics": ("PBCC", "PDBCC", "PFLUSH", "PFLUSHA", "PFLUSHR", "PLOADR", "PLOADW", "PMOVE", "PSCC", "PTESTR", "PTESTW", "PTRAPCC", "PVALID"),
        "reason_category": "decode_render_metadata_missing",
        "blocking_artifacts": ("canonical_sample_plan", "decode_render_metadata", "generated_semantics", "oracle_support"),
        "reason": (
            "PMMU forms are present but lack complete generated operand metadata, semantics, and oracle "
            "coverage for strict canonical parity."
        ),
    },
    {
        "family_id": "generic_coprocessor",
        "status": "intentionally_unsupported",
        "mnemonics": ("CPBCC", "CPDBCC", "CPRESTORE", "CPSAVE", "CPSCC", "CPTRAPCC"),
        "reason_category": "missing_schema",
        "blocking_artifacts": ("canonical_schema", "decode_render_metadata", "oracle_support"),
        "reason": (
            "Generic coprocessor forms require coprocessor-ID schema and generated metadata before they can "
            "be treated as required canonical coverage."
        ),
    },
)
BOOTSTRAP_UNSUPPORTED_FAMILIES = CANONICAL_UNSUPPORTED_FAMILIES


class FormLike(Protocol):
    mnemonic: str
    kb_mnemonic: str
    local_form_index: int
    form_index: int
    syntax: str
    operand_kinds: tuple[str, ...]
    sampling_operand_kinds: tuple[str, ...]
    opword_base: int
    opword_mask: int
    cpu_mask: int


@dataclass(frozen=True, slots=True)
class CoverageForm:
    mnemonic: str
    kb_mnemonic: str
    local_form_index: int
    form_index: int
    syntax: str
    operand_kinds: tuple[str, ...]
    sampling_operand_kinds: tuple[str, ...]
    opword_base: int
    opword_mask: int
    cpu_mask: int
    canonical_form_id: int | None
    canonical_form_id_source: str


def build_diagnostic_inventory(
    assembler_forms: list[FormLike] | None = None,
    disassembler_forms: list[FormLike] | None = None,
    assembler_sample_entries: list[dict[str, Any]] | None = None,
    ea_sample_plan_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if assembler_forms is None or disassembler_forms is None:
        (
            loaded_assembler_forms,
            loaded_disassembler_forms,
            loaded_sample_entries,
            loaded_ea_plan_entries,
        ) = _load_current_forms()
        assembler_forms = loaded_assembler_forms if assembler_forms is None else assembler_forms
        disassembler_forms = loaded_disassembler_forms if disassembler_forms is None else disassembler_forms
        assembler_sample_entries = loaded_sample_entries if assembler_sample_entries is None else assembler_sample_entries
        ea_sample_plan_entries = loaded_ea_plan_entries if ea_sample_plan_entries is None else ea_sample_plan_entries
    if assembler_sample_entries is None:
        assembler_sample_entries = []
    if ea_sample_plan_entries is None:
        ea_sample_plan_entries = []

    asm_by_key = {_form_key(form): _form_identity(form) for form in assembler_forms}
    disasm_by_key = {_form_key(form): _form_identity(form) for form in disassembler_forms}
    samples_by_key = _sample_entries_by_key(assembler_sample_entries)
    keys = sorted(set(asm_by_key) | set(disasm_by_key))

    entries: list[dict[str, Any]] = []
    for key in keys:
        in_asm = key in asm_by_key
        in_disasm = key in disasm_by_key
        status = "matched" if in_asm and in_disasm else "asm_only" if in_asm else "disasm_only"
        entries.append({
            "status": status,
            "key": {
                "kb_mnemonic": key[0],
                "local_form_index": key[1],
                "syntax": key[2],
                "mnemonic": key[3],
            },
            "assembler": asm_by_key.get(key),
            "disassembler": disasm_by_key.get(key),
            "sample_statuses": samples_by_key.get(key, []),
        })
    sample_status_counts = Counter(
        str(sample["status"])
        for samples in samples_by_key.values()
        for sample in samples
    )
    unsupported_inventory = _bootstrap_unsupported_inventory(entries)
    unsupported_counts = Counter(str(entry["status"]) for entry in unsupported_inventory)

    return {
        "phase": "diagnostic",
        "temporary_bootstrap": True,
        "deletion_criteria": DIAGNOSTIC_DELETION_CRITERIA,
        "counts": {
            "assembler_forms": len(assembler_forms),
            "disassembler_forms": len(disassembler_forms),
            "matched_forms": sum(1 for entry in entries if entry["status"] == "matched"),
            "asm_only_forms": sum(1 for entry in entries if entry["status"] == "asm_only"),
            "disasm_only_forms": sum(1 for entry in entries if entry["status"] == "disasm_only"),
        },
        "sample_status_counts": dict(sorted(sample_status_counts.items())),
        "unsupported_counts": dict(sorted(unsupported_counts.items())),
        "unsupported_inventory": unsupported_inventory,
        "ea_sample_plans": ea_sample_plan_entries,
        "entries": entries,
    }


def build_canonical_inventory(
    assembler_forms: list[FormLike] | None = None,
    disassembler_forms: list[FormLike] | None = None,
    assembler_sample_entries: list[dict[str, Any]] | None = None,
    ea_sample_plan_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    inventory = build_diagnostic_inventory(
        assembler_forms=assembler_forms,
        disassembler_forms=disassembler_forms,
        assembler_sample_entries=assembler_sample_entries,
        ea_sample_plan_entries=ea_sample_plan_entries,
    )
    inventory["phase"] = "canonical"
    inventory["temporary_bootstrap"] = False
    inventory["deletion_criteria"] = CANONICAL_DELETION_CRITERIA
    inventory["summaries"] = _canonical_summaries(inventory)
    return inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report generated M68K coverage state.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command_name in ("report", "check"):
        command = subparsers.add_parser(command_name)
        command.add_argument("--phase", choices=("diagnostic", "canonical"), required=True)
        command.add_argument("--format", choices=("text", "json"), default="text")

    args = parser.parse_args(argv)
    inventory = build_canonical_inventory() if args.phase == "canonical" else build_diagnostic_inventory()
    if args.command == "report":
        if args.format == "json":
            print(json.dumps(inventory, indent=2, sort_keys=True))
        else:
            _print_canonical_report(inventory) if args.phase == "canonical" else _print_diagnostic_report(inventory)
        return 0
    if args.command == "check":
        failures = strict_coverage_failures(inventory) if args.phase == "canonical" else diagnostic_check_failures(inventory)
        if failures:
            if args.format == "json":
                print(json.dumps({"ok": False, "failures": failures}, indent=2, sort_keys=True))
            else:
                print(f"{args.phase} coverage check failed: {len(failures)} failures")
                for failure in failures:
                    print(f"  {failure['kind']}: {failure['message']}")
            return 1
        if args.format == "json":
            print(json.dumps(inventory, indent=2, sort_keys=True))
        else:
            _print_canonical_report(inventory) if args.phase == "canonical" else _print_diagnostic_report(inventory)
        return 0
    raise SystemExit(f"Unsupported command: {args.command}")


def diagnostic_check_failures(inventory: dict[str, Any]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for entry in inventory["entries"]:
        key = entry["key"]
        form_name = f"{key['kb_mnemonic']}#{key['local_form_index']} {key['mnemonic']} {key['syntax']}"
        status = str(entry["status"])
        if status not in DIAGNOSTIC_FORM_STATUSES:
            failures.append({
                "kind": "unclassified_form",
                "message": f"{form_name} has unknown form status {status}",
            })
        for sample in entry["sample_statuses"]:
            sample_status = str(sample["status"])
            if sample_status not in DIAGNOSTIC_SAMPLE_STATUSES:
                failures.append({
                    "kind": "unclassified_sample_status",
                    "message": f"{form_name} has unknown sample status {sample_status}",
                })
            if sample_status == "missing_sample_strategy":
                failures.append({
                    "kind": "missing_sample_strategy",
                    "message": f"{form_name} has no sample strategy for size {sample.get('size') or '-'}",
                })
    for unsupported in inventory.get("unsupported_inventory", []):
        if unsupported.get("stale") is True:
            failures.append({
                "kind": "stale_unsupported_reason",
                "message": f"{unsupported['family_id']} unsupported entry matched no current generated forms",
            })
    return failures


def strict_coverage_failures(inventory: dict[str, Any]) -> list[dict[str, str]]:
    failures = diagnostic_check_failures(inventory)
    unsupported_form_keys = _unsupported_form_keys(inventory)
    for entry in inventory["entries"]:
        status = str(entry["status"])
        key = entry["key"]
        if _entry_key(key) in unsupported_form_keys:
            continue
        if status not in {"asm_only", "disasm_only"}:
            assembler = entry.get("assembler")
            disassembler = entry.get("disassembler")
            if isinstance(assembler, dict) and isinstance(disassembler, dict):
                asm_canonical = assembler.get("canonical_form_id")
                disasm_canonical = disassembler.get("canonical_form_id")
                if (
                    ("canonical_form_id" in assembler or "canonical_form_id" in disassembler)
                    and (asm_canonical is None or disasm_canonical is None)
                ):
                    failures.append({
                        "kind": "missing_canonical_form_identity",
                        "message": (
                            f"{key['kb_mnemonic']}#{key['local_form_index']} "
                            f"{key['mnemonic']} {key['syntax']} is missing a generated canonical id"
                        ),
                    })
                if asm_canonical is not None and disasm_canonical is not None and asm_canonical != disasm_canonical:
                    failures.append({
                        "kind": "canonical_form_identity_mismatch",
                        "message": (
                            f"{key['kb_mnemonic']}#{key['local_form_index']} "
                            f"{key['mnemonic']} {key['syntax']} has assembler canonical id "
                            f"{asm_canonical} and decoder canonical id {disasm_canonical}"
                        ),
                    })
            continue
        if _entry_key(key) in unsupported_form_keys:
            continue
        failures.append({
            "kind": "asm_decode_parity_mismatch",
            "message": (
                f"{key['kb_mnemonic']}#{key['local_form_index']} "
                f"{key['mnemonic']} {key['syntax']} is {status}"
            ),
        })
    return failures


def _load_current_forms() -> tuple[list[FormLike], list[FormLike], list[dict[str, Any]], list[dict[str, Any]]]:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    assembler_subset = __import__("generate_c99_assembler_subset")
    disassembler_subset = __import__("generate_c99_disassembler_subset")
    assembler_corpus = __import__("generate_c99_assembler_corpus")
    raw_assembler_forms = list(assembler_subset._load_forms(assembler_subset.KB_PATH))
    raw_disassembler_forms = list(disassembler_subset._load_forms())
    assembler_form_ids = _generated_canonical_form_ids(ASM_TABLE_PATH)
    assembler_forms = _forms_with_generated_canonical_ids(
        raw_assembler_forms,
        assembler_form_ids,
        "src/generated/m68k_asm_tables.c",
        lambda form: int(form.form_index),
    )
    disassembler_forms = _forms_with_generated_canonical_ids(
        raw_disassembler_forms,
        _generated_disassembler_canonical_form_ids(DISASM_TABLE_PATH),
        "src/generated/m68k_disassembler_tables.h",
        _generated_match_key,
    )
    return (
        cast(list[FormLike], assembler_forms),
        cast(list[FormLike], disassembler_forms),
        [
            {
                "mnemonic": str(entry.mnemonic),
                "kb_mnemonic": str(entry.kb_mnemonic),
                "local_form_index": int(entry.local_form_index),
                "form_index": int(entry.form_index),
                "syntax": str(entry.syntax),
                "size": entry.size,
                "target_cpu": str(entry.target_cpu),
                "status": str(entry.status),
                "reason": str(entry.reason),
                "missing_operand_kinds": list(entry.missing_operand_kinds),
            }
            for entry in assembler_corpus.generate_sample_coverage()
        ],
        [
            {
                "mnemonic": str(entry.mnemonic),
                "kb_mnemonic": str(entry.kb_mnemonic),
                "local_form_index": int(entry.local_form_index),
                "form_index": int(entry.form_index),
                "syntax": str(entry.syntax),
                "size": entry.size,
                "target_cpu": str(entry.target_cpu),
                "operand_index": int(entry.operand_index),
                "operand_kind": str(entry.operand_kind),
                "operand_role": entry.operand_role,
                "required_families": list(entry.required_families),
                "covered_families": list(entry.covered_families),
                "missing_families": list(entry.missing_families),
                "sample_families": list(entry.sample_families),
            }
            for entry in assembler_corpus.generate_ea_sample_plans()
        ],
    )


def _form_key(form: FormLike) -> tuple[str, int, str, str]:
    return (
        str(form.kb_mnemonic),
        int(form.local_form_index),
        str(form.syntax),
        str(form.mnemonic),
    )


def _form_identity(form: FormLike) -> dict[str, Any]:
    identity = {
        "mnemonic": str(form.mnemonic),
        "kb_mnemonic": str(form.kb_mnemonic),
        "local_form_index": int(form.local_form_index),
        "form_index": int(form.form_index),
        "syntax": str(form.syntax),
        "operand_kinds": list(form.operand_kinds),
        "sampling_operand_kinds": list(form.sampling_operand_kinds),
        "opword_base": int(form.opword_base),
        "opword_mask": int(form.opword_mask),
        "cpu_mask": int(form.cpu_mask),
    }
    canonical_form_id = getattr(form, "canonical_form_id", None)
    if canonical_form_id is not None:
        identity["canonical_form_id"] = int(canonical_form_id)
        identity["canonical_form_id_source"] = str(getattr(form, "canonical_form_id_source", "provided"))
    return identity


def _generated_canonical_form_ids(table_path: Path) -> dict[int, int]:
    form_ids: dict[int, int] = {}
    for row in _generated_form_rows(table_path):
        first_line = row.splitlines()[0]
        match = GENERATED_FORM_ROW_RE.match(first_line)
        if match is None:
            continue
        form_index = _parse_generated_int(match.group("form_index"))
        canonical_form_id = _parse_generated_int(match.group("canonical_form_id"))
        if form_index in form_ids:
            raise ValueError(f"{table_path} contains duplicate generated form index {form_index}")
        form_ids[form_index] = canonical_form_id
    if not form_ids:
        raise ValueError(f"{table_path} contains no generated canonical form ids")
    return form_ids


def _generated_disassembler_canonical_form_ids(
    table_path: Path,
) -> dict[tuple[Any, ...], int | None]:
    form_ids: dict[tuple[Any, ...], int | None] = {}
    for row in _generated_form_rows(table_path):
        first_line = row.splitlines()[0]
        match = GENERATED_FORM_ROW_RE.match(first_line)
        if match is None:
            continue
        key = _generated_row_match_key(row, match)
        canonical_form_id = _parse_generated_int(match.group("canonical_form_id"))
        if key in form_ids and form_ids[key] != canonical_form_id:
            form_ids[key] = None
            continue
        form_ids[key] = canonical_form_id
    if not form_ids:
        raise ValueError(f"{table_path} contains no generated disassembler canonical form ids")
    return form_ids


def _forms_with_generated_canonical_ids(
    forms: Any,
    canonical_form_ids: dict[Any, int | None],
    source: str,
    key_fn: Any,
) -> list[CoverageForm]:
    loaded = list(forms)
    def canonical_id_for(form: Any) -> int | None:
        form_id = canonical_form_ids.get(key_fn(form))
        return int(form_id) if form_id is not None else None

    return [
        CoverageForm(
            mnemonic=str(form.mnemonic),
            kb_mnemonic=str(form.kb_mnemonic),
            local_form_index=int(form.local_form_index),
            form_index=int(form.form_index),
            syntax=str(form.syntax),
            operand_kinds=tuple(str(kind) for kind in form.operand_kinds),
            sampling_operand_kinds=tuple(str(kind) for kind in form.sampling_operand_kinds),
            opword_base=int(form.opword_base),
            opword_mask=int(form.opword_mask),
            cpu_mask=int(form.cpu_mask),
            canonical_form_id=canonical_id_for(form),
            canonical_form_id_source=source,
        )
        for form in loaded
    ]


def _generated_form_rows(table_path: Path) -> list[str]:
    rows: list[str] = []
    current: list[str] = []
    for line in table_path.read_text(encoding="utf-8").splitlines():
        if not current and not line.lstrip().startswith('{ "'):
            continue
        current.append(line)
        if line.rstrip().endswith("},"):
            rows.append("\n".join(current))
            current = []
    return rows


def _generated_row_match_key(row: str, match: re.Match[str]) -> tuple[Any, ...]:
    operand_token = row.find("M68K_ASM_OPERAND_")
    operand_start = row.rfind("{", 0, operand_token)
    operand_end = row.find("}", operand_token)
    if operand_token < 0 or operand_start < 0 or operand_end < 0:
        raise ValueError(f"Generated row has no operand array: {match.group('syntax')}")
    numeric_tail = row[operand_end + 1:]
    numbers = [_parse_generated_int(value.group(0)) for value in NUMBER_RE.finditer(numeric_tail)]
    if len(numbers) < 18:
        raise ValueError(f"Generated row has too few numeric fields: {match.group('syntax')}")
    return (
        match.group("mnemonic").lower(),
        match.group("syntax"),
        numbers[4],
        numbers[7],
        numbers[8],
        tuple(numbers[14:16]),
        tuple(numbers[16:18]),
    )


def _generated_match_key(form: Any) -> tuple[Any, ...]:
    return (
        str(form.mnemonic).lower(),
        str(form.syntax),
        int(form.cpu_mask),
        int(form.opword_base),
        int(form.opword_mask),
        tuple(int(value) for value in getattr(form, "bound_word_bases", (0, 0))),
        tuple(int(value) for value in getattr(form, "bound_word_masks", (0, 0))),
    )


def _parse_generated_int(value: str) -> int:
    return int(value.rstrip("uU"), 0)


def _sample_entries_by_key(entries: list[dict[str, Any]]) -> dict[tuple[str, int, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        key = (
            str(entry["kb_mnemonic"]),
            int(entry["local_form_index"]),
            str(entry["syntax"]),
            str(entry["mnemonic"]),
        )
        grouped[key].append(entry)
    return dict(grouped)


def _entry_key(key: dict[str, Any]) -> tuple[str, int, str, str]:
    return (
        str(key["kb_mnemonic"]),
        int(key["local_form_index"]),
        str(key["syntax"]),
        str(key["mnemonic"]),
    )


def _unsupported_form_keys(inventory: dict[str, Any]) -> set[tuple[str, int, str, str]]:
    keys: set[tuple[str, int, str, str]] = set()
    for unsupported in inventory.get("unsupported_inventory", []):
        if not isinstance(unsupported, dict):
            continue
        for form in unsupported.get("forms", []):
            if isinstance(form, dict):
                keys.add(_entry_key(form))
    return keys


def _canonical_summaries(inventory: dict[str, Any]) -> dict[str, Any]:
    sample_entries = [
        sample
        for entry in inventory["entries"]
        for sample in entry["sample_statuses"]
    ]
    cpu_counts = Counter(str(sample.get("target_cpu", "-")) for sample in sample_entries)
    mnemonic_counts = Counter(str(entry["key"]["mnemonic"]).upper() for entry in inventory["entries"])
    alias_entries = [
        entry["key"]
        for entry in inventory["entries"]
        if str(entry["key"]["mnemonic"]).upper() != str(entry["key"]["kb_mnemonic"]).upper()
    ]
    ea_family_required = Counter(
        family
        for plan in inventory.get("ea_sample_plans", [])
        for family in plan.get("required_families", [])
    )
    ea_family_covered = Counter(
        family
        for plan in inventory.get("ea_sample_plans", [])
        for family in plan.get("covered_families", [])
    )
    ea_family_missing = Counter(
        family
        for plan in inventory.get("ea_sample_plans", [])
        for family in plan.get("missing_families", [])
    )
    oracle_statuses = Counter(
        str(sample["status"])
        for sample in sample_entries
        if str(sample["status"]) == "oracle_unavailable"
    )
    return {
        "cpu": dict(sorted(cpu_counts.items())),
        "mnemonic": dict(sorted(mnemonic_counts.items())),
        "ea_family": {
            "required": dict(sorted(ea_family_required.items())),
            "covered": dict(sorted(ea_family_covered.items())),
            "missing": dict(sorted(ea_family_missing.items())),
        },
        "alias": {
            "count": len(alias_entries),
            "entries": alias_entries[:20],
        },
        "oracle": dict(sorted(oracle_statuses.items())),
        "executor_semantic": {
            "available": False,
            "reason": "executor semantic coverage is generated in a later PRD phase",
        },
        "unsupported": {
            "counts": inventory["unsupported_counts"],
            "families": [
                {
                    "family_id": entry["family_id"],
                    "status": entry["status"],
                    "reason_category": entry.get("reason_category"),
                    "form_count": entry["form_count"],
                }
                for entry in inventory.get("unsupported_inventory", [])
            ],
        },
    }


def _bootstrap_unsupported_inventory(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_mnemonic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        by_mnemonic[str(entry["key"]["mnemonic"]).upper()].append(entry["key"])
    inventory: list[dict[str, Any]] = []
    for family in BOOTSTRAP_UNSUPPORTED_FAMILIES:
        matched_forms = [
            form
            for mnemonic in family["mnemonics"]
            for form in by_mnemonic.get(str(mnemonic), [])
        ]
        if not matched_forms:
            continue
        stale_conditions = [
            {
                "condition_id": "current_generated_forms_present",
                "stale_when": "no_current_generated_form_matches_mnemonics",
                "stale": False,
                "message": "Unsupported family no longer matches any current generated form.",
            },
            {
                "condition_id": "blocking_artifacts_still_missing",
                "stale_when": "canonical strict coverage reports no missing blocking artifact for this family",
                "stale": False,
                "message": "Unsupported reason must be removed when all blocking artifacts are generated.",
            },
        ]
        inventory.append({
            "family_id": family["family_id"],
            "status": family["status"],
            "mnemonics": list(family["mnemonics"]),
            "reason_category": family["reason_category"],
            "blocking_artifacts": list(family["blocking_artifacts"]),
            "reason": family["reason"],
            "stale_condition": "stale_when_no_current_generated_form_matches_mnemonics",
            "stale_conditions": stale_conditions,
            "stale": any(condition["stale"] for condition in stale_conditions),
            "form_count": len(matched_forms),
            "forms": matched_forms,
        })
    return inventory


def _print_diagnostic_report(inventory: dict[str, Any]) -> None:
    counts = inventory["counts"]
    print("M68K diagnostic coverage")
    print(f"assembler forms: {counts['assembler_forms']}")
    print(f"disassembler forms: {counts['disassembler_forms']}")
    print(f"matched forms: {counts['matched_forms']}")
    print(f"asm-only forms: {counts['asm_only_forms']}")
    print(f"disasm-only forms: {counts['disasm_only_forms']}")
    print("sample statuses:")
    sample_status_counts = inventory["sample_status_counts"]
    if sample_status_counts:
        for status, count in sample_status_counts.items():
            print(f"  {status}: {count}")
    else:
        print("  none: 0")
    print("unsupported statuses:")
    unsupported_counts = inventory["unsupported_counts"]
    if unsupported_counts:
        for status, count in unsupported_counts.items():
            print(f"  {status}: {count}")
    else:
        print("  none: 0")
    unsupported_inventory = inventory.get("unsupported_inventory", [])
    if unsupported_inventory:
        print("unsupported entries:")
        for entry in unsupported_inventory:
            blockers = ",".join(entry.get("blocking_artifacts", []))
            print(
                f"  {entry['family_id']}: {entry['status']} "
                f"reason={entry.get('reason_category', '-')} forms={entry['form_count']} blockers={blockers}"
            )
    ea_sample_plans = inventory.get("ea_sample_plans", [])
    if ea_sample_plans:
        missing_ea_plans = [entry for entry in ea_sample_plans if entry.get("missing_families")]
        print("ea sample families:")
        print(f"  plan operands: {len(ea_sample_plans)}")
        print(f"  complete operands: {len(ea_sample_plans) - len(missing_ea_plans)}")
        print(f"  missing-family operands: {len(missing_ea_plans)}")
        if missing_ea_plans:
            print("missing ea family entries:")
            for entry in missing_ea_plans:
                size = entry.get("size") or "-"
                role = entry.get("operand_role") or "-"
                required = ",".join(entry.get("required_families", []))
                covered = ",".join(entry.get("covered_families", []))
                missing = ",".join(entry.get("missing_families", []))
                print(
                    "  "
                    f"{entry['kb_mnemonic']}#{entry['local_form_index']} "
                    f"{entry['mnemonic']} {entry['syntax']} size={size} "
                    f"operand={entry['operand_index']} role={role} "
                    f"required={required} covered={covered} missing={missing}"
                )
    print(f"deletion: {inventory['deletion_criteria']}")
    missing_sample_entries = [
        (entry["key"], sample)
        for entry in inventory["entries"]
        for sample in entry["sample_statuses"]
        if sample["status"] == "missing_sample_strategy"
    ]
    if missing_sample_entries:
        print("missing-sample-strategy entries:")
        for form, sample in missing_sample_entries:
            missing = ",".join(sample.get("missing_operand_kinds", []))
            size = sample.get("size") or "-"
            print(
                "  "
                f"{form['kb_mnemonic']}#{form['local_form_index']} "
                f"{form['mnemonic']} {form['syntax']} size={size} missing={missing}"
            )
    for status in ("asm_only", "disasm_only"):
        forms = [entry["key"] for entry in inventory["entries"] if entry["status"] == status]
        if not forms:
            continue
        print(f"{status.replace('_', '-')} entries:")
        for form in forms:
            print(
                "  "
                f"{form['kb_mnemonic']}#{form['local_form_index']} "
                f"{form['mnemonic']} {form['syntax']}"
            )


def _print_canonical_report(inventory: dict[str, Any]) -> None:
    _print_diagnostic_report(inventory)
    summaries = inventory.get("summaries", {})
    if not summaries:
        return
    print("canonical summaries:")
    for label in ("cpu", "mnemonic", "oracle"):
        summary = summaries.get(label, {})
        print(f"  {label}: {len(summary)} entries")
    ea_family = summaries.get("ea_family", {})
    if ea_family:
        required = ",".join(sorted(ea_family.get("required", {}).keys()))
        missing = ",".join(sorted(ea_family.get("missing", {}).keys()))
        print(f"  ea families required={required or '-'} missing={missing or '-'}")
    alias = summaries.get("alias", {})
    print(f"  aliases: {alias.get('count', 0)}")
    executor = summaries.get("executor_semantic", {})
    print(f"  executor semantics: {'available' if executor.get('available') else 'not-generated'}")
    unsupported = summaries.get("unsupported", {})
    print(f"  unsupported families: {len(unsupported.get('families', []))}")


if __name__ == "__main__":
    raise SystemExit(main())
