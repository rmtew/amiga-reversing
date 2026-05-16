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
    canonical_form_id: int | None = None
    canonical_form_id_source: str = "fixture"


def test_diagnostic_inventory_loads_current_generated_form_tables() -> None:
    inventory = m68k_coverage.build_diagnostic_inventory()

    assert inventory["phase"] == "diagnostic"
    assert inventory["temporary_bootstrap"] is True
    assert inventory["counts"]["assembler_forms"] > 0
    assert inventory["counts"]["disassembler_forms"] > 0
    assert inventory["counts"]["matched_forms"] > 0
    assert inventory["sample_status_counts"]["sampled"] > 0
    assert len(inventory["entries"]) >= inventory["counts"]["matched_forms"]
    assert len(inventory["ea_sample_plans"]) > 0
    assert inventory["ea_sample_plans"][0]["required_families"]
    assert "missing_families" in inventory["ea_sample_plans"][0]
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
    assert "unsupported statuses:" in output
    assert "ea sample families:" in output


def test_canonical_report_command_prints_summaries(capsys) -> None:
    assert m68k_coverage.main(["report", "--phase", "canonical"]) == 0

    output = capsys.readouterr().out
    assert "M68K diagnostic coverage" in output
    assert "canonical summaries:" in output
    assert "ea families required=" in output
    assert "executor semantics:" in output
    assert "unsupported families:" in output


def test_canonical_inventory_summarizes_current_generated_data() -> None:
    inventory = m68k_coverage.build_canonical_inventory()

    assert inventory["phase"] == "canonical"
    assert inventory["temporary_bootstrap"] is False
    assert inventory["summaries"]["cpu"]
    assert inventory["summaries"]["mnemonic"]
    assert inventory["summaries"]["ea_family"]["required"]
    assert "executor_semantic" in inventory["summaries"]
    assert inventory["summaries"]["executor_semantic"]["available"] > 0
    assert inventory["summaries"]["executor_semantic"]["generated_semantics_missing"] > 0
    assert inventory["summaries"]["executor_semantic"]["intentionally_unsupported"] > 0
    assert inventory["summaries"]["unsupported"]["families"]
    unsupported_keys = {
        (
            form["kb_mnemonic"],
            form["local_form_index"],
            form["syntax"],
            form["mnemonic"],
        )
        for unsupported in inventory["unsupported_inventory"]
        for form in unsupported["forms"]
    }
    matched_entries = [entry for entry in inventory["entries"] if entry["status"] == "matched"]
    required_matched_entries = [
        entry
        for entry in matched_entries
        if (
            entry["key"]["kb_mnemonic"],
            entry["key"]["local_form_index"],
            entry["key"]["syntax"],
            entry["key"]["mnemonic"],
        )
        not in unsupported_keys
    ]
    assert required_matched_entries
    assert all(isinstance(entry["assembler"]["canonical_form_id"], int) for entry in required_matched_entries)
    assert all(isinstance(entry["disassembler"]["canonical_form_id"], int) for entry in required_matched_entries)
    assert all(
        entry["assembler"]["canonical_form_id"] == entry["disassembler"]["canonical_form_id"]
        for entry in required_matched_entries
    )


def test_diagnostic_check_command_succeeds_with_current_classified_data(capsys) -> None:
    assert m68k_coverage.main(["check", "--phase", "diagnostic"]) == 0

    assert "M68K diagnostic coverage" in capsys.readouterr().out


def test_canonical_check_command_prints_canonical_summaries(capsys) -> None:
    assert m68k_coverage.main(["check", "--phase", "canonical"]) == 0

    output = capsys.readouterr().out
    assert "canonical summaries:" in output
    assert "executor semantics:" in output


def test_diagnostic_check_fails_synthetic_unclassified_form() -> None:
    form = FakeForm("MOVE", "MOVE", 0, 0, "MOVE <ea>,Dn")
    inventory = m68k_coverage.build_diagnostic_inventory(
        assembler_forms=[form],
        disassembler_forms=[form],
        assembler_sample_entries=[],
    )
    inventory["entries"][0]["status"] = "unknown"

    failures = m68k_coverage.diagnostic_check_failures(inventory)

    assert failures == [
        {
            "kind": "unclassified_form",
            "message": "MOVE#0 MOVE MOVE <ea>,Dn has unknown form status unknown",
        }
    ]


def test_diagnostic_check_fails_synthetic_missing_sample_strategy() -> None:
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
            }
        ],
    )

    failures = m68k_coverage.diagnostic_check_failures(inventory)

    assert failures == [
        {
            "kind": "missing_sample_strategy",
            "message": "MOVE#0 MOVE MOVE <ea>,Dn has no sample strategy for size w",
        }
    ]


def test_bootstrap_unsupported_inventory_classifies_current_families() -> None:
    inventory = m68k_coverage.build_diagnostic_inventory()

    unsupported_by_id = {entry["family_id"]: entry for entry in inventory["unsupported_inventory"]}
    assert {"move16", "fsave_frestore", "pmmu", "generic_coprocessor"} <= set(unsupported_by_id)
    assert unsupported_by_id["move16"]["status"] == "implemented_unsupported"
    assert unsupported_by_id["move16"]["reason_category"] == "generated_semantics_missing"
    assert "generated_semantics" in unsupported_by_id["move16"]["blocking_artifacts"]
    assert unsupported_by_id["move16"]["semantic_status_counts"]["generated_semantics_missing"] > 0
    assert unsupported_by_id["generic_coprocessor"]["semantic_status_counts"]["intentionally_unsupported"] > 0
    assert unsupported_by_id["generic_coprocessor"]["status"] == "intentionally_unsupported"
    assert unsupported_by_id["generic_coprocessor"]["reason_category"] == "missing_schema"
    assert all(entry["form_count"] > 0 for entry in unsupported_by_id.values())
    assert all(entry["stale_conditions"] for entry in unsupported_by_id.values())
    assert all(
        condition["stale"] is False
        for entry in unsupported_by_id.values()
        for condition in entry["stale_conditions"]
    )
    assert inventory["unsupported_counts"] == {
        "implemented_unsupported": 3,
        "intentionally_unsupported": 1,
    }


def test_diagnostic_check_fails_stale_unsupported_reason() -> None:
    inventory = {
        "entries": [],
        "unsupported_inventory": [
            {
                "family_id": "synthetic",
                "status": "intentionally_unsupported",
                "stale": True,
            }
        ],
    }

    failures = m68k_coverage.diagnostic_check_failures(inventory)

    assert failures == [
        {
            "kind": "stale_unsupported_reason",
            "message": "synthetic unsupported entry matched no current generated forms",
        }
    ]


def test_strict_coverage_fails_asm_decode_parity_mismatch() -> None:
    asm_only = FakeForm("ADD", "ADD", 1, 1, "ADD Dn,<ea>")
    disasm_only = FakeForm("SUB", "SUB", 2, 20, "SUB <ea>,Dn")
    inventory = m68k_coverage.build_diagnostic_inventory(
        assembler_forms=[asm_only],
        disassembler_forms=[disasm_only],
    )

    failures = m68k_coverage.strict_coverage_failures(inventory)

    assert inventory["unsupported_inventory"] == []
    assert {failure["kind"] for failure in failures} == {"asm_decode_parity_mismatch"}


def test_strict_coverage_allows_canonical_unsupported_parity_mismatch() -> None:
    disasm_only = FakeForm("CPBCC", "cpBcc", 0, 20, "cpBcc <label>")
    inventory = m68k_coverage.build_canonical_inventory(
        assembler_forms=[],
        disassembler_forms=[disasm_only],
    )

    failures = m68k_coverage.strict_coverage_failures(inventory)

    assert inventory["unsupported_inventory"][0]["family_id"] == "generic_coprocessor"
    assert failures == []


def test_strict_coverage_fails_canonical_identity_mismatch() -> None:
    asm_form = FakeForm("MOVE", "MOVE", 0, 0, "MOVE <ea>,Dn", canonical_form_id=10)
    disasm_form = FakeForm("MOVE", "MOVE", 0, 10, "MOVE <ea>,Dn", canonical_form_id=11)
    inventory = m68k_coverage.build_canonical_inventory(
        assembler_forms=[asm_form],
        disassembler_forms=[disasm_form],
    )

    failures = m68k_coverage.strict_coverage_failures(inventory)

    assert failures == [
        {
            "kind": "canonical_form_identity_mismatch",
            "message": "MOVE#0 MOVE MOVE <ea>,Dn has assembler canonical id 10 and decoder canonical id 11",
        }
    ]


def test_strict_coverage_includes_unclassified_missing_and_stale_failures() -> None:
    form = FakeForm("MOVE", "MOVE", 0, 0, "MOVE <ea>,Dn")
    inventory = m68k_coverage.build_canonical_inventory(
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
            }
        ],
    )
    inventory["entries"][0]["status"] = "unknown"
    inventory["unsupported_inventory"].append({
        "family_id": "synthetic",
        "status": "intentionally_unsupported",
        "stale": True,
    })

    failures = m68k_coverage.strict_coverage_failures(inventory)

    assert {failure["kind"] for failure in failures} == {
        "unclassified_form",
        "missing_sample_strategy",
        "stale_unsupported_reason",
    }


def test_explicit_unsupported_sample_status_is_classified() -> None:
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
                "status": "intentionally_unsupported",
                "reason": "synthetic unsupported fixture",
                "missing_operand_kinds": [],
            }
        ],
    )

    assert m68k_coverage.diagnostic_check_failures(inventory) == []


def _load_corpus_script():
    scripts_dir = Path(__file__).resolve().parents[1] / "src" / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    return __import__("generate_c99_assembler_corpus")
