from __future__ import annotations

from pathlib import Path

from disasm.emitter import emit_session_rows
from disasm.instruction_rows import render_instruction_text
from disasm.text import render_rows
from disasm.types import DisassemblySession, HunkDisassemblySession
from m68k.m68k_disasm import Instruction


def _instruction_at(hunk: HunkDisassemblySession, addr: int) -> Instruction:
    for block in hunk.blocks.values():
        for inst in block.instructions:
            if inst.offset == addr:
                return inst
    raise ValueError(f"Instruction not found at ${addr:04X}")


def _render_at(
    hunk: HunkDisassemblySession,
    addr: int,
) -> tuple[str, str, tuple[str, ...]]:
    inst = _instruction_at(hunk, addr)
    text, comment, comment_parts = render_instruction_text(
        inst, hunk, set(), include_arg_subs=True)
    return text, comment, comment_parts


def _render_session_for_hunk(hunk: HunkDisassemblySession) -> str:
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=Path("targets/test/entities.jsonl"),
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=None,
        entities=hunk.entities,
        hunk_sessions=[hunk],
    )
    return render_rows(emit_session_rows(session))


def test_bloodwych_startup_stays_relocatable_and_has_no_absolute_app_anchor(
    bloodwych_hunk_session: HunkDisassemblySession,
) -> None:
    hunk = bloodwych_hunk_session

    assert _render_at(hunk, 0x0400) == ("move.w #$7fff,_custom+intena", "", ())
    assert _render_at(hunk, 0x0408) == ("move.w #$7fff,_custom+intreq", "", ())
    assert _render_at(hunk, 0x041C) == ("bsr.w sub_0492", "", ())
    assert hunk.labels[0x0492] == "sub_0492"
    assert 0x00008000 not in hunk.absolute_labels
    assert "app_base_00008000" not in hunk.absolute_labels.values()


def test_bloodwych_emission_uses_custom_include_without_custom_equ_spam(
    bloodwych_hunk_session: HunkDisassemblySession,
) -> None:
    text = _render_session_for_hunk(bloodwych_hunk_session)

    assert '    INCLUDE "hardware/cia.i"\n' in text
    assert '    INCLUDE "hardware/custom.i"\n' in text
    assert "INTENA\tEQU\t$DFF09A" not in text
    assert "CIAA_PRA\tEQU\t$BFE001" not in text
    assert "move.w #$7fff,_custom+intena" in text
    assert "lea _ciaa+ciapra,a0" in text
