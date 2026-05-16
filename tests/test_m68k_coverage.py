from __future__ import annotations

from dataclasses import dataclass

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


def test_diagnostic_report_command_prints_counts(capsys) -> None:
    assert m68k_coverage.main(["report", "--phase", "diagnostic"]) == 0

    output = capsys.readouterr().out
    assert "assembler forms:" in output
    assert "disassembler forms:" in output
    assert "matched forms:" in output
    assert "asm-only forms:" in output
    assert "disasm-only forms:" in output
