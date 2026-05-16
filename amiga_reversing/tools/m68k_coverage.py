from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Protocol, cast

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "src" / "scripts"

DIAGNOSTIC_DELETION_CRITERIA = (
    "Temporary bootstrap inventory. Delete or fold into canonical-model coverage "
    "after PRD 024/025 own canonical form identity and sample coverage."
)


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
) -> dict[str, Any]:
    if assembler_forms is None or disassembler_forms is None:
        loaded_assembler_forms, loaded_disassembler_forms = _load_current_forms()
        assembler_forms = loaded_assembler_forms if assembler_forms is None else assembler_forms
        disassembler_forms = loaded_disassembler_forms if disassembler_forms is None else disassembler_forms

    asm_by_key = {_form_key(form): _form_identity(form) for form in assembler_forms}
    disasm_by_key = {_form_key(form): _form_identity(form) for form in disassembler_forms}
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
        })

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
        unclassified = [
            entry for entry in inventory["entries"]
            if entry["status"] not in {"matched", "asm_only", "disasm_only"}
        ]
        if unclassified:
            print(f"diagnostic coverage check failed: {len(unclassified)} unclassified forms")
            return 1
        if args.format == "json":
            print(json.dumps(inventory, indent=2, sort_keys=True))
        else:
            _print_diagnostic_report(inventory)
        return 0
    raise SystemExit(f"Unsupported command: {args.command}")


def _load_current_forms() -> tuple[list[FormLike], list[FormLike]]:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    assembler_subset = __import__("generate_c99_assembler_subset")
    disassembler_subset = __import__("generate_c99_disassembler_subset")
    return (
        cast(list[FormLike], list(assembler_subset._load_forms(assembler_subset.KB_PATH))),
        cast(list[FormLike], list(disassembler_subset._load_forms())),
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


def _print_diagnostic_report(inventory: dict[str, Any]) -> None:
    counts = inventory["counts"]
    print("M68K diagnostic coverage")
    print(f"assembler forms: {counts['assembler_forms']}")
    print(f"disassembler forms: {counts['disassembler_forms']}")
    print(f"matched forms: {counts['matched_forms']}")
    print(f"asm-only forms: {counts['asm_only_forms']}")
    print(f"disasm-only forms: {counts['disasm_only_forms']}")
    print(f"deletion: {inventory['deletion_criteria']}")
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
