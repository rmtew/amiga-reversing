from m68k.assembler_coverage_audit import (
    audit_local_assembler_support,
    find_gap,
)
from m68k.m68k_asm import assemble_instruction


def test_audit_flags_current_local_assembler_gaps():
    gaps = audit_local_assembler_support()

    assert not find_gap(gaps, "full-ext-preindexed")
    assert not find_gap(gaps, "full-ext-pc-preindexed")


def test_audit_confirms_supported_neighbor_cases():
    gaps = audit_local_assembler_support()

    assert not find_gap(gaps, "pack-dn")
    assert not find_gap(gaps, "pack-predec")
    assert not find_gap(gaps, "unpk-dn")
    assert not find_gap(gaps, "link-w")
    assert not find_gap(gaps, "link-l")
    assert not find_gap(gaps, "full-ext-preindexed")
    assert not find_gap(gaps, "full-ext-postindexed")
    assert not find_gap(gaps, "full-ext-pc-preindexed")
    assert not find_gap(gaps, "full-ext-pc-postindexed")


def test_preindexed_full_extension_alias_assembles_to_existing_encoding():
    assert assemble_instruction("move.l (4,[8,a0,d0.w]),d1") == assemble_instruction(
        "move.l ([8,a0,d0.w],4),d1"
    )


def test_pc_preindexed_full_extension_alias_assembles_to_existing_encoding():
    assert assemble_instruction("move.l (4,[8,pc,d0.w]),d1") == assemble_instruction(
        "move.l ([8,pc,d0.w],4),d1"
    )
