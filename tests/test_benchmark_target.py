from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from scripts.benchmark_target import (
    _benchmark_record,
    AnalysisBenchmark,
    EntityBenchmark,
)


def test_benchmark_record_uses_relative_paths_and_sizes(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    root = Path.cwd()
    binary = root / "bin" / "Example"
    analysis = tmp_path / "Example.analysis"
    entities = tmp_path / "entities.jsonl"
    disasm = tmp_path / "Example.s"
    analysis.write_bytes(b"a" * 10)
    entities.write_bytes(b"b" * 20)
    disasm.write_bytes(b"c" * 30)

    monkeypatch.setattr(
        "scripts.benchmark_target._analysis_benchmark",
        lambda path: AnalysisBenchmark(
            code_bytes=100,
            core_block_count=2,
            core_instruction_count=5,
            core_covered_bytes=20,
            core_coverage_ratio=0.2,
            hint_block_count=1,
            hint_instruction_count=2,
            hint_covered_bytes=8,
            hint_coverage_ratio=0.08,
            xref_count=3,
            jump_table_count=0,
            indirect_site_count=1,
            call_target_count=4,
            branch_target_count=5,
            library_call_count=6,
            resolved_library_call_count=4,
            library_count=2,
        ),
    )
    monkeypatch.setattr(
        "scripts.benchmark_target._entities_benchmark",
        lambda path: EntityBenchmark(
            entity_count=7,
            code_entity_count=3,
            data_entity_count=2,
            bss_entity_count=1,
            unknown_entity_count=1,
            named_entity_count=4,
            documented_entity_count=1,
        ),
    )

    record = _benchmark_record(
        "example",
        binary,
        "ok",
        12.345,
        analysis,
        entities,
        disasm,
    )

    assert record.target == "example"
    assert record.binary == "bin/Example"
    assert record.command == "uv run scripts/gen_disasm.py bin/Example -t targets/example"
    assert record.status == "ok"
    assert record.elapsed_seconds == 12.35
    assert record.analysis_bytes == 10
    assert record.entities_bytes == 20
    assert record.disasm_bytes == 30
    assert record.analysis is not None
    assert record.analysis.core_block_count == 2
    assert record.analysis.library_call_count == 6
    assert record.entities is not None
    assert record.entities.entity_count == 7
    assert record.entities.named_entity_count == 4
    assert record.error is None
