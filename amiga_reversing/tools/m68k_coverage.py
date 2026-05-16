from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Protocol, cast

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "src" / "scripts"

DIAGNOSTIC_DELETION_CRITERIA = (
    "Temporary bootstrap inventory. Delete or fold into canonical-model coverage "
    "after PRD 024/025 own canonical form identity and sample coverage."
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


def build_diagnostic_inventory(
    assembler_forms: list[FormLike] | None = None,
    disassembler_forms: list[FormLike] | None = None,
    assembler_sample_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if assembler_forms is None or disassembler_forms is None:
        loaded_assembler_forms, loaded_disassembler_forms, loaded_sample_entries = _load_current_forms()
        assembler_forms = loaded_assembler_forms if assembler_forms is None else assembler_forms
        disassembler_forms = loaded_disassembler_forms if disassembler_forms is None else disassembler_forms
        assembler_sample_entries = loaded_sample_entries if assembler_sample_entries is None else assembler_sample_entries
    if assembler_sample_entries is None:
        assembler_sample_entries = []

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
    unsupported_counts = {
        status: count
        for status, count in sorted(sample_status_counts.items())
        if status in DIAGNOSTIC_UNSUPPORTED_SAMPLE_STATUSES
    }

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
        "unsupported_counts": unsupported_counts,
        "entries": entries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report generated M68K coverage state.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command_name in ("report", "check"):
        command = subparsers.add_parser(command_name)
        command.add_argument("--phase", choices=("diagnostic",), required=True)
        command.add_argument("--format", choices=("text", "json"), default="text")

    args = parser.parse_args(argv)
    inventory = build_diagnostic_inventory()
    if args.command == "report":
        if args.format == "json":
            print(json.dumps(inventory, indent=2, sort_keys=True))
        else:
            _print_diagnostic_report(inventory)
        return 0
    if args.command == "check":
        failures = diagnostic_check_failures(inventory)
        if failures:
            if args.format == "json":
                print(json.dumps({"ok": False, "failures": failures}, indent=2, sort_keys=True))
            else:
                print(f"diagnostic coverage check failed: {len(failures)} failures")
                for failure in failures:
                    print(f"  {failure['kind']}: {failure['message']}")
            return 1
        if args.format == "json":
            print(json.dumps(inventory, indent=2, sort_keys=True))
        else:
            _print_diagnostic_report(inventory)
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
    return failures


def _load_current_forms() -> tuple[list[FormLike], list[FormLike], list[dict[str, Any]]]:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    assembler_subset = __import__("generate_c99_assembler_subset")
    disassembler_subset = __import__("generate_c99_disassembler_subset")
    assembler_corpus = __import__("generate_c99_assembler_corpus")
    return (
        cast(list[FormLike], list(assembler_subset._load_forms(assembler_subset.KB_PATH))),
        cast(list[FormLike], list(disassembler_subset._load_forms())),
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
    )


def _form_key(form: FormLike) -> tuple[str, int, str, str]:
    return (
        str(form.kb_mnemonic),
        int(form.local_form_index),
        str(form.syntax),
        str(form.mnemonic),
    )


def _form_identity(form: FormLike) -> dict[str, Any]:
    return {
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


if __name__ == "__main__":
    raise SystemExit(main())
