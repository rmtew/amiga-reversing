from __future__ import annotations

import json
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from amiga_disk.models import DiskManifest
from disasm.analysis_layout import (
    resolved_analysis_start_offset,
    resolved_entry_points,
    resolved_raw_analysis_base_addr,
)
from disasm.analysis_loader import analysis_cache_root, hunk_analysis_cache_path
from disasm.emitter import emit_session_rows
from disasm.entry_seeds import build_entry_seed_config
from disasm.os_include_kb import load_os_include_kb
from disasm.phase_timing import PhaseTimer
from disasm.project_ids import target_output_stem
from disasm.project_paths import resolve_project_paths
from disasm.session import build_disassembly_session
from disasm.target_metadata import load_target_metadata
from disasm.text import render_rows
from disasm.types import AppStructFieldOperandMetadata, StructFieldOperandMetadata
from m68k.analysis import HunkAnalysis
from m68k.hunk_parser import parse
from m68k_kb import runtime_os
from scripts.build_entities import build_entities_from_source

TARGETS_DIR = ROOT / "targets"
_OS_INCLUDE_KB = load_os_include_kb()


@dataclass(frozen=True, slots=True)
class AnalysisBenchmark:
    code_bytes: int
    core_block_count: int
    core_instruction_count: int
    core_covered_bytes: int
    core_coverage_ratio: float
    hint_block_count: int
    hint_instruction_count: int
    hint_covered_bytes: int
    hint_coverage_ratio: float
    xref_count: int
    jump_table_count: int
    indirect_site_count: int
    call_target_count: int
    branch_target_count: int
    library_call_count: int
    resolved_library_call_count: int
    library_count: int


@dataclass(frozen=True, slots=True)
class EntityBenchmark:
    entity_count: int
    code_entity_count: int
    data_entity_count: int
    bss_entity_count: int
    unknown_entity_count: int
    named_entity_count: int
    documented_entity_count: int


@dataclass(frozen=True, slots=True)
class AnalysisTimingBenchmark:
    init_seconds: float
    core_seconds: float
    per_caller_seconds: float
    store_pass_seconds: float
    hint_scan_seconds: float
    os_call_seconds: float


@dataclass(frozen=True, slots=True)
class EntitiesTimingBenchmark:
    parse_source_seconds: float
    analysis: AnalysisTimingBenchmark
    naming_seconds: float
    write_seconds: float


@dataclass(frozen=True, slots=True)
class SessionTimingBenchmark:
    load_analysis_seconds: float
    metadata_seconds: float
    substitutions_seconds: float
    build_seconds: float


@dataclass(frozen=True, slots=True)
class TimingBenchmark:
    entities: EntitiesTimingBenchmark
    session: SessionTimingBenchmark
    emit_seconds: float
    render_seconds: float


@dataclass(frozen=True, slots=True)
class LibraryLvoBenchmark:
    included: int
    inserted: int


@dataclass(frozen=True, slots=True)
class LvoBenchmark:
    included_count: int
    inserted_count: int
    by_library: dict[str, LibraryLvoBenchmark]


@dataclass(frozen=True, slots=True)
class SymbolUsageBenchmark:
    immediate_constant_count: int
    struct_field_count: int
    app_struct_field_count: int


@dataclass(frozen=True, slots=True)
class DisasmBenchmark:
    lvo: LvoBenchmark
    symbols: SymbolUsageBenchmark


@dataclass(frozen=True, slots=True)
class TargetBenchmark:
    target: str
    binary: str
    command: str
    measured_at: str
    status: str
    elapsed_seconds: float
    analysis_bytes: int | None
    entities_bytes: int | None
    disasm_bytes: int | None
    timing: TimingBenchmark | None
    analysis: AnalysisBenchmark | None
    entities: EntityBenchmark | None
    disasm: DisasmBenchmark | None
    error: str | None = None
    targets: dict[str, TargetBenchmark] | None = None


def _covered_bytes(blocks: Mapping[int, Any]) -> int:
    return sum(block.end - block.start for block in blocks.values())


def _analysis_cache_paths(target_dir: Path, binary_source: Any) -> list[Path]:
    target_metadata = load_target_metadata(target_dir)
    seed_config = build_entry_seed_config(target_metadata)
    if binary_source.kind == "raw_binary":
        entry_points = resolved_entry_points(binary_source, target_metadata, ())
        cache_root = analysis_cache_root(
            binary_source.analysis_cache_path,
            seed_key=seed_config.seed_key,
            base_addr=resolved_raw_analysis_base_addr(binary_source, target_metadata),
            code_start=resolved_analysis_start_offset(binary_source, target_metadata),
            entry_points=entry_points,
        )
        return [hunk_analysis_cache_path(cache_root, 0)]
    hunk_file = parse(binary_source.read_bytes())
    custom_entry_points = resolved_entry_points(binary_source, target_metadata, ())
    first_code_hunk_seen = False
    analysis_paths: list[Path] = []
    code_start = 0
    base_addr = 0
    for hunk in hunk_file.hunks:
        if hunk.type_name != "CODE":
            continue
        entry_points = custom_entry_points if not first_code_hunk_seen else ()
        cache_root = analysis_cache_root(
            binary_source.analysis_cache_path,
            seed_key=seed_config.seed_key,
            base_addr=base_addr,
            code_start=code_start,
            entry_points=entry_points,
        )
        analysis_paths.append(hunk_analysis_cache_path(cache_root, hunk.index))
        first_code_hunk_seen = True
    return list(analysis_paths)


def _analysis_benchmark(analysis_paths: Sequence[Path]) -> AnalysisBenchmark | None:
    existing_paths = [path for path in analysis_paths if path.exists()]
    if not existing_paths:
        return None
    analyses = [HunkAnalysis.load(path, runtime_os) for path in existing_paths]
    code_bytes = sum(len(ha.code) for ha in analyses)
    core_covered_bytes = sum(_covered_bytes(ha.blocks) for ha in analyses)
    hint_covered_bytes = sum(_covered_bytes(ha.hint_blocks) for ha in analyses)
    resolved_calls = tuple(
        call
        for ha in analyses
        for call in ha.lib_calls
        if call.library != "unknown"
    )
    libraries = {call.library for call in resolved_calls}
    return AnalysisBenchmark(
        code_bytes=code_bytes,
        core_block_count=sum(len(ha.blocks) for ha in analyses),
        core_instruction_count=sum(len(block.instructions) for ha in analyses for block in ha.blocks.values()),
        core_covered_bytes=core_covered_bytes,
        core_coverage_ratio=round(core_covered_bytes / code_bytes, 4) if code_bytes else 0.0,
        hint_block_count=sum(len(ha.hint_blocks) for ha in analyses),
        hint_instruction_count=sum(len(block.instructions) for ha in analyses for block in ha.hint_blocks.values()),
        hint_covered_bytes=hint_covered_bytes,
        hint_coverage_ratio=round(hint_covered_bytes / code_bytes, 4) if code_bytes else 0.0,
        xref_count=sum(len(ha.xrefs) for ha in analyses),
        jump_table_count=sum(len(ha.jump_tables) for ha in analyses),
        indirect_site_count=sum(len(ha.indirect_sites) for ha in analyses),
        call_target_count=sum(len(ha.call_targets) for ha in analyses),
        branch_target_count=sum(len(ha.branch_targets) for ha in analyses),
        library_call_count=sum(len(ha.lib_calls) for ha in analyses),
        resolved_library_call_count=len(resolved_calls),
        library_count=len(libraries),
    )


def _entities_benchmark(entities_path: Path) -> EntityBenchmark | None:
    if not entities_path.exists():
        return None
    rows = [
        json.loads(line)
        for line in entities_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return EntityBenchmark(
        entity_count=len(rows),
        code_entity_count=sum(1 for row in rows if row.get("type") == "code"),
        data_entity_count=sum(1 for row in rows if row.get("type") == "data"),
        bss_entity_count=sum(1 for row in rows if row.get("type") == "bss"),
        unknown_entity_count=sum(1 for row in rows if row.get("type") == "unknown"),
        named_entity_count=sum(1 for row in rows if row.get("status") == "named" or "name" in row),
        documented_entity_count=sum(1 for row in rows if row.get("status") == "documented"),
    )


def _disasm_benchmark(session: Any, rows: Sequence[Any]) -> DisasmBenchmark:
    lvo_by_library: dict[str, LibraryLvoBenchmark] = {}
    lvo_included_count = 0
    lvo_inserted_count = 0
    for hunk_session in session.hunk_sessions:
        for library_name, library_equs in hunk_session.lvo_equs.items():
            owner = _OS_INCLUDE_KB.library_lvo_owners.get(library_name)
            if owner is None:
                raise ValueError(f"Missing KB library include owner for benchmark LVOs: {library_name}")
            count = len(library_equs)
            existing = lvo_by_library.get(library_name, LibraryLvoBenchmark(included=0, inserted=0))
            if owner.kind == "native_include":
                lvo_included_count += count
                lvo_by_library[library_name] = LibraryLvoBenchmark(
                    included=existing.included + count,
                    inserted=existing.inserted,
                )
            elif owner.kind == "fd_only":
                lvo_inserted_count += count
                lvo_by_library[library_name] = LibraryLvoBenchmark(
                    included=existing.included,
                    inserted=existing.inserted + count,
                )
            else:
                raise ValueError(f"Unknown OS include owner kind for benchmark LVOs: {library_name}: {owner.kind}")
    struct_field_count = 0
    app_struct_field_count = 0
    for row in rows:
        for operand in row.operand_parts:
            metadata = operand.metadata
            if isinstance(metadata, StructFieldOperandMetadata):
                struct_field_count += 1
            elif isinstance(metadata, AppStructFieldOperandMetadata):
                if metadata.field_symbol is None:
                    continue
                app_struct_field_count += 1
    immediate_constant_count = sum(len(hunk_session.arg_substitutions) for hunk_session in session.hunk_sessions)
    return DisasmBenchmark(
        lvo=LvoBenchmark(
            included_count=lvo_included_count,
            inserted_count=lvo_inserted_count,
            by_library=dict(sorted(lvo_by_library.items())),
        ),
        symbols=SymbolUsageBenchmark(
            immediate_constant_count=immediate_constant_count,
            struct_field_count=struct_field_count,
            app_struct_field_count=app_struct_field_count,
        ),
    )


def _analysis_timing(timer: PhaseTimer) -> AnalysisTimingBenchmark:
    return AnalysisTimingBenchmark(
        init_seconds=round(timer.value("analysis.init"), 4),
        core_seconds=round(timer.value("analysis.core"), 4),
        per_caller_seconds=round(timer.value("analysis.per_caller"), 4),
        store_pass_seconds=round(timer.value("analysis.store_pass"), 4),
        hint_scan_seconds=round(timer.value("analysis.hint_scan"), 4),
        os_call_seconds=round(timer.value("analysis.os_calls"), 4),
    )


def _timing_benchmark(timer: PhaseTimer, emit_seconds: float, render_seconds: float) -> TimingBenchmark:
    return TimingBenchmark(
        entities=EntitiesTimingBenchmark(
            parse_source_seconds=round(timer.value("entities.parse_source"), 4),
            analysis=_analysis_timing(timer),
            naming_seconds=round(timer.value("entities.naming"), 4),
            write_seconds=round(timer.value("entities.write"), 4),
        ),
        session=SessionTimingBenchmark(
            load_analysis_seconds=round(timer.value("session.load_analysis"), 4),
            metadata_seconds=round(timer.value("session.metadata"), 4),
            substitutions_seconds=round(timer.value("session.substitutions"), 4),
            build_seconds=round(timer.value("session.build"), 4),
        ),
        emit_seconds=round(emit_seconds, 4),
        render_seconds=round(render_seconds, 4),
    )


def _sum_analysis_timing(records: Sequence[TargetBenchmark]) -> AnalysisTimingBenchmark:
    return AnalysisTimingBenchmark(
        init_seconds=round(sum((record.timing.entities.analysis.init_seconds if record.timing else 0.0) for record in records), 4),
        core_seconds=round(sum((record.timing.entities.analysis.core_seconds if record.timing else 0.0) for record in records), 4),
        per_caller_seconds=round(sum((record.timing.entities.analysis.per_caller_seconds if record.timing else 0.0) for record in records), 4),
        store_pass_seconds=round(sum((record.timing.entities.analysis.store_pass_seconds if record.timing else 0.0) for record in records), 4),
        hint_scan_seconds=round(sum((record.timing.entities.analysis.hint_scan_seconds if record.timing else 0.0) for record in records), 4),
        os_call_seconds=round(sum((record.timing.entities.analysis.os_call_seconds if record.timing else 0.0) for record in records), 4),
    )


def _sum_timing(records: Sequence[TargetBenchmark]) -> TimingBenchmark:
    return TimingBenchmark(
        entities=EntitiesTimingBenchmark(
            parse_source_seconds=round(sum((record.timing.entities.parse_source_seconds if record.timing else 0.0) for record in records), 4),
            analysis=_sum_analysis_timing(records),
            naming_seconds=round(sum((record.timing.entities.naming_seconds if record.timing else 0.0) for record in records), 4),
            write_seconds=round(sum((record.timing.entities.write_seconds if record.timing else 0.0) for record in records), 4),
        ),
        session=SessionTimingBenchmark(
            load_analysis_seconds=round(sum((record.timing.session.load_analysis_seconds if record.timing else 0.0) for record in records), 4),
            metadata_seconds=round(sum((record.timing.session.metadata_seconds if record.timing else 0.0) for record in records), 4),
            substitutions_seconds=round(sum((record.timing.session.substitutions_seconds if record.timing else 0.0) for record in records), 4),
            build_seconds=round(sum((record.timing.session.build_seconds if record.timing else 0.0) for record in records), 4),
        ),
        emit_seconds=round(sum((record.timing.emit_seconds if record.timing else 0.0) for record in records), 4),
        render_seconds=round(sum((record.timing.render_seconds if record.timing else 0.0) for record in records), 4),
    )


def _benchmark_record(
    target: str,
    binary_display_path: str,
    status: str,
    elapsed_seconds: float,
    analysis_paths: Sequence[Path],
    entities_path: Path,
    disasm_path: Path,
    error: str | None = None,
    *,
    timing: TimingBenchmark | None = None,
    disasm: DisasmBenchmark | None = None,
    targets: dict[str, TargetBenchmark] | None = None,
) -> TargetBenchmark:
    command = f"uv run scripts/benchmark_target.py {target}"
    return TargetBenchmark(
        target=target,
        binary=binary_display_path,
        command=command,
        measured_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        status=status,
        elapsed_seconds=round(elapsed_seconds, 2),
        analysis_bytes=sum(path.stat().st_size for path in analysis_paths if path.exists()) or None,
        entities_bytes=entities_path.stat().st_size if entities_path.exists() else None,
        disasm_bytes=disasm_path.stat().st_size if disasm_path.exists() else None,
        timing=timing,
        analysis=_analysis_benchmark(analysis_paths),
        entities=_entities_benchmark(entities_path),
        disasm=disasm,
        error=error,
        targets=targets,
    )


def _default_disasm_path(target_dir: Path, target: str) -> Path:
    return target_dir / f"{target_output_stem(target_dir.name)}.s"


def _benchmark_binary_target(target: str, *, write_output: bool) -> TargetBenchmark:
    paths = resolve_project_paths(target, project_root=ROOT, require_entities=False)
    target_dir = paths.target_dir
    analysis_paths = _analysis_cache_paths(target_dir, paths.binary_source)
    entities_path = paths.entities_path
    disasm_path = paths.output_path or _default_disasm_path(target_dir, target)

    for analysis_path in analysis_paths:
        analysis_path.unlink(missing_ok=True)
    entities_path.unlink(missing_ok=True)
    disasm_path.unlink(missing_ok=True)

    start = time.perf_counter()
    phase_timer = PhaseTimer()
    try:
        build_entities_from_source(paths.binary_source, str(entities_path), phase_timer=phase_timer)
        session = build_disassembly_session(
            paths.binary_source,
            str(entities_path),
            str(disasm_path),
            phase_timer=phase_timer,
        )
        emit_started = time.perf_counter()
        rows = emit_session_rows(session)
        emit_elapsed = time.perf_counter() - emit_started
        render_started = time.perf_counter()
        disasm_path.write_text(render_rows(rows), encoding="utf-8")
        render_elapsed = time.perf_counter() - render_started
        elapsed = time.perf_counter() - start
        missing_analysis_paths = [path for path in analysis_paths if not path.exists()]
        if missing_analysis_paths:
            raise FileNotFoundError(
                "missing benchmark output " + ", ".join(str(path) for path in missing_analysis_paths)
            )
        if not entities_path.exists():
            raise FileNotFoundError(f"missing benchmark output {entities_path}")
        if not disasm_path.exists():
            raise FileNotFoundError(f"missing benchmark output {disasm_path}")
        record = _benchmark_record(
            target,
            paths.binary_source.display_path,
            "ok",
            elapsed,
            analysis_paths,
            entities_path,
            disasm_path,
            timing=_timing_benchmark(phase_timer, emit_elapsed, render_elapsed),
            disasm=_disasm_benchmark(session, rows),
        )
    except Exception as exc:
        elapsed = time.perf_counter() - start
        record = _benchmark_record(
            target,
            paths.binary_source.display_path,
            "failed",
            elapsed,
            analysis_paths,
            entities_path,
            disasm_path,
            error=str(exc),
        )
    if write_output:
        (target_dir / "benchmark.json").write_text(
            json.dumps(asdict(record), indent=2) + "\n",
            encoding="ascii",
        )
    return record


def _disk_project_benchmark(target: str) -> TargetBenchmark:
    target_dir = TARGETS_DIR / target
    manifest = DiskManifest.load(target_dir / "manifest.json")
    child_targets: list[str] = []
    if manifest.bootblock_target_name:
        child_targets.append(manifest.bootblock_target_name)
    child_targets.extend(
        imported.target_name
        for imported in sorted(manifest.imported_targets, key=lambda imported: imported.entry_path)
    )

    started = time.perf_counter()
    child_records: dict[str, TargetBenchmark] = {}
    for child_target in child_targets:
        child_records[child_target] = _benchmark_binary_target(child_target, write_output=False)
    elapsed = time.perf_counter() - started
    failures = [record for record in child_records.values() if record.status != "ok"]
    record = TargetBenchmark(
        target=target,
        binary=manifest.source_path,
        command=f"uv run scripts/benchmark_target.py {target}",
        measured_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        status="failed" if failures else "ok",
        elapsed_seconds=round(elapsed, 2),
        analysis_bytes=sum(record.analysis_bytes or 0 for record in child_records.values()) or None,
        entities_bytes=sum(record.entities_bytes or 0 for record in child_records.values()) or None,
        disasm_bytes=sum(record.disasm_bytes or 0 for record in child_records.values()) or None,
        timing=_sum_timing(list(child_records.values())),
        analysis=None,
        entities=None,
        disasm=DisasmBenchmark(
            lvo=LvoBenchmark(
                included_count=sum((record.disasm.lvo.included_count if record.disasm else 0) for record in child_records.values()),
                inserted_count=sum((record.disasm.lvo.inserted_count if record.disasm else 0) for record in child_records.values()),
                by_library={
                    library_name: LibraryLvoBenchmark(
                        included=sum(
                            child.disasm.lvo.by_library.get(library_name, LibraryLvoBenchmark(0, 0)).included
                            for child in child_records.values()
                            if child.disasm is not None
                        ),
                        inserted=sum(
                            child.disasm.lvo.by_library.get(library_name, LibraryLvoBenchmark(0, 0)).inserted
                            for child in child_records.values()
                            if child.disasm is not None
                        ),
                    )
                    for library_name in sorted({
                        library_name
                        for child in child_records.values()
                        if child.disasm is not None
                        for library_name in child.disasm.lvo.by_library
                    })
                },
            ),
            symbols=SymbolUsageBenchmark(
                immediate_constant_count=sum((record.disasm.symbols.immediate_constant_count if record.disasm else 0) for record in child_records.values()),
                struct_field_count=sum((record.disasm.symbols.struct_field_count if record.disasm else 0) for record in child_records.values()),
                app_struct_field_count=sum((record.disasm.symbols.app_struct_field_count if record.disasm else 0) for record in child_records.values()),
            ),
        ),
        error=None if not failures else "; ".join(
            f"{record.target}: {record.error or record.status}" for record in failures
        ),
        targets=child_records,
    )
    (target_dir / "benchmark.json").write_text(
        json.dumps(asdict(record), indent=2) + "\n",
        encoding="ascii",
    )
    return record


def benchmark_target(target: str) -> TargetBenchmark:
    target_dir = TARGETS_DIR / target
    if (target_dir / "manifest.json").exists():
        return _disk_project_benchmark(target)
    return _benchmark_binary_target(target, write_output=True)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit("usage: uv run scripts/benchmark_target.py <target> [<target> ...]")
    had_failures = False
    for target in argv[1:]:
        record = benchmark_target(target)
        if record.status == "ok":
            print(f"{record.target}: {record.elapsed_seconds:.2f}s")
        else:
            had_failures = True
            print(f"{record.target}: failed after {record.elapsed_seconds:.2f}s")
    return 1 if had_failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
