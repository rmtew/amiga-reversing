from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.tools import m68k_coverage


@dataclass(frozen=True, slots=True)
class FakeForm:
    mnemonic: str
    kb_mnemonic: str
    local_form_index: int
    form_index: int
    syntax: str
    operand_kinds: tuple[str, ...] = ()
    sampling_operand_kinds: tuple[str, ...] = ()
    opword_base: int = 0
    opword_mask: int = 0
    cpu_mask: int = 0


def test_diagnostic_inventory_loads_current_generated_form_tables() -> None:
    inventory = m68k_coverage.build_diagnostic_inventory()

    assert inventory["phase"] == "diagnostic"
    assert inventory["temporary_bootstrap"] is True
    assert inventory["counts"]["assembler_forms"] > 0
    assert inventory["counts"]["disassembler_forms"] > 0
    assert inventory["counts"]["matched_forms"] > 0
    assert inventory["sample_status_counts"]["sampled"] > 0
    assert len(inventory["entries"]) >= inventory["counts"]["matched_forms"]
    assert "canonical-model coverage" in inventory["deletion_criteria"]


def test_diagnostic_inventory_reports_unmatched_forms() -> None:
    matched_asm = FakeForm("MOVE", "MOVE", 0, 0, "MOVE <ea>,Dn")
    matched_disasm = FakeForm("MOVE", "MOVE", 0, 10, "MOVE <ea>,Dn")
    asm_only = FakeForm("ADD", "ADD", 1, 1, "ADD Dn,<ea>")
    disasm_only = FakeForm("SUB", "SUB", 2, 20, "SUB <ea>,Dn")

    inventory = m68k_coverage.build_diagnostic_inventory(
        assembler_forms=[matched_asm, asm_only],
        disassembler_forms=[matched_disasm, disasm_only],
    )

    assert inventory["counts"] == {
        "assembler_forms": 2,
        "disassembler_forms": 2,
        "matched_forms": 1,
        "asm_only_forms": 1,
        "disasm_only_forms": 1,
    }
    statuses = {entry["key"]["kb_mnemonic"]: entry["status"] for entry in inventory["entries"]}
    assert statuses == {"MOVE": "matched", "ADD": "asm_only", "SUB": "disasm_only"}
    asm_only_entry = next(entry for entry in inventory["entries"] if entry["status"] == "asm_only")
    assert asm_only_entry["assembler"]["syntax"] == "ADD Dn,<ea>"
    assert asm_only_entry["disassembler"] is None


def test_diagnostic_inventory_keeps_missing_sample_strategy_distinct() -> None:
    form = FakeForm("MOVE", "MOVE", 0, 0, "MOVE <ea>,Dn")

    inventory = m68k_coverage.build_diagnostic_inventory(
        assembler_forms=[form],
        disassembler_forms=[form],
        assembler_sample_entries=[
            {
                "mnemonic": "MOVE",
                "kb_mnemonic": "MOVE",
                "local_form_index": 0,
                "form_index": 0,
                "syntax": "MOVE <ea>,Dn",
                "size": "w",
                "target_cpu": "68000",
                "status": "missing_sample_strategy",
                "reason": "one or more operands produced no sample options",
                "missing_operand_kinds": ["ea"],
            },
            {
                "mnemonic": "MOVE",
                "kb_mnemonic": "MOVE",
                "local_form_index": 0,
                "form_index": 0,
                "syntax": "MOVE <ea>,Dn",
                "size": "l",
                "target_cpu": "68000",
                "status": "intentionally_unsupported",
                "reason": "synthetic unsupported fixture",
                "missing_operand_kinds": [],
            },
            {
                "mnemonic": "MOVE",
                "kb_mnemonic": "MOVE",
                "local_form_index": 0,
                "form_index": 0,
                "syntax": "MOVE <ea>,Dn",
                "size": "b",
                "target_cpu": "68000",
                "status": "implemented_unsupported",
                "reason": "synthetic unsupported fixture",
                "missing_operand_kinds": [],
            },
        ],
    )

    assert inventory["sample_status_counts"] == {
        "implemented_unsupported": 1,
        "intentionally_unsupported": 1,
        "missing_sample_strategy": 1,
    }
    entry = inventory["entries"][0]
    assert [sample["status"] for sample in entry["sample_statuses"]] == [
        "missing_sample_strategy",
        "intentionally_unsupported",
        "implemented_unsupported",
    ]


def test_empty_sample_options_produce_missing_strategy_status() -> None:
    corpus = _load_corpus_script()
    form = FakeForm("MOVE", "MOVE", 0, 0, "MOVE <unknown>", sampling_operand_kinds=("unknown",), operand_kinds=("unknown",))
    context = corpus.FormContext(
        form=form,
        size="w",
        syntax=form.syntax,
        operand_kinds=("unknown",),
        operand_roles=(None,),
    )

    entry = corpus._sample_status_for_options(context, ((),))

    assert entry.status == "missing_sample_strategy"
    assert entry.missing_operand_kinds == ("unknown",)


def test_diagnostic_report_command_prints_counts(capsys) -> None:
    assert m68k_coverage.main(["report", "--phase", "diagnostic"]) == 0

    output = capsys.readouterr().out
    assert "assembler forms:" in output
    assert "disassembler forms:" in output
    assert "matched forms:" in output
    assert "asm-only forms:" in output
    assert "disasm-only forms:" in output
    assert "sample statuses:" in output


def _load_corpus_script():
    scripts_dir = Path(__file__).resolve().parents[1] / "src" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    return __import__("generate_c99_assembler_corpus")
