"""KB-driven canonical operand coverage using the vasm case generator."""

import tempfile
from collections import defaultdict

from m68k.m68k_disasm import disassemble
from m68k.kb_util import KB
from disasm.operands import build_instruction_semantic_operands
from disasm.types import HunkDisassemblySession
from tests.test_m68k_roundtrip import ALL_CASES, _batch_assemble


def _coverage_session() -> HunkDisassemblySession:
    return HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        core_absolute_targets=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        struct_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform={},
        os_kb={"structs": {}},
        kb=KB(),
        fixed_abs_addrs=set(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )


def test_kb_find_resolves_bare_mnemonic_via_asm_syntax_index():
    assert KB().find("PFLUSHA")["mnemonic"] == "PFLUSH PFLUSHA"


def test_kb_generated_cases_build_canonical_semantic_operands():
    session = _coverage_session()
    batches: dict[str, list] = defaultdict(list)
    for case in ALL_CASES:
        batches[case.cpu_flag].append(case)

    failures = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for cpu_flag, cases in batches.items():
            raws = _batch_assemble(cases, cpu_flag, tmpdir)
            for case, raw in zip(cases, raws):
                try:
                    insts = disassemble(raw, max_cpu=case.max_cpu)
                    if not insts:
                        raise ValueError(f"Disassembly produced no instructions for {case.asm!r}")
                    build_instruction_semantic_operands(insts[0], session)
                except Exception as exc:
                    failures.append(f"{case.asm} => {type(exc).__name__}: {exc}")
                    if len(failures) >= 20:
                        break
            if failures:
                break

    assert not failures, "Canonical operand coverage failures:\n" + "\n".join(failures)
