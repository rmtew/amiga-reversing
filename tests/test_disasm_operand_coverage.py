"""KB-driven canonical operand coverage using the vasm case generator."""

from __future__ import annotations

import tempfile
from collections import defaultdict

from disasm.operands import build_instruction_semantic_operands
from disasm.types import HunkDisassemblySession
from m68k.instruction_kb import find_kb_entry
from m68k.m68k_disasm import Instruction, disassemble
from tests.os_kb_helpers import make_empty_os_kb
from tests.platform_helpers import make_platform
from tests.test_m68k_roundtrip import ALL_CASES, Case, _batch_assemble


def _coverage_session() -> HunkDisassemblySession:
    return HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )


def _seed_absolute_labels(session: HunkDisassemblySession, inst: Instruction) -> None:
    for node in inst.operand_nodes or ():
        target = getattr(node, "target", None)
        if isinstance(target, int):
            session.absolute_labels.setdefault(target, f"abs_{target:08x}")


def test_kb_find_resolves_bare_mnemonic_via_asm_syntax_index() -> None:
    assert find_kb_entry("PFLUSHA") == "PFLUSH PFLUSHA"


def test_kb_generated_cases_build_canonical_semantic_operands() -> None:
    session = _coverage_session()
    batches: dict[str, list[Case]] = defaultdict(list)
    for case in ALL_CASES:
        batches[case.cpu_flag].append(case)

    failures = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for cpu_flag, cases in batches.items():
            raws = _batch_assemble(cases, cpu_flag, tmpdir)
            for case, raw in zip(cases, raws, strict=True):
                try:
                    insts = disassemble(raw, max_cpu=case.max_cpu)
                    if not insts:
                        raise ValueError(f"Disassembly produced no instructions for {case.asm!r}")
                    _seed_absolute_labels(session, insts[0])
                    build_instruction_semantic_operands(insts[0], session)
                except Exception as exc:
                    failures.append(f"{case.asm} => {type(exc).__name__}: {exc}")
                    if len(failures) >= 20:
                        break
            if failures:
                break

    assert not failures, "Canonical operand coverage failures:\n" + "\n".join(failures)

