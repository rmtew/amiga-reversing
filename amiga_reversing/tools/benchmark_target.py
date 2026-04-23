from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from amiga_reversing.amiga_disk.models import DiskManifest
from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.c_backend import (
    benchmark_project_source_with_text_from_c_backend,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_ids import target_output_stem
from amiga_reversing.disasm.project_paths import resolve_project_paths

TARGETS_DIR = ROOT / "targets"


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
class TargetBenchmark:
    target: str
    binary: str
    command: str
    measured_at: str
    status: str
    elapsed_seconds: float
    benchmark_bytes: int | None
    entities_bytes: int | None
    disasm_bytes: int | None
    benchmark_version: int | None
    platform: str | None
    timing: dict[str, object] | None
    file: dict[str, object] | None
    analysis: dict[str, object] | None
    render: dict[str, object] | None
    sections: list[dict[str, object]] | None
    entities: EntityBenchmark | None
    error: str | None = None
    targets: dict[str, TargetBenchmark] | None = None
    facts_v2: dict[str, object] | None = None


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


def _sum_c_timing(records: Sequence[TargetBenchmark]) -> dict[str, object] | None:
    totals = {
        "analysis_seconds": 0.0,
        "ir_build_seconds": 0.0,
        "render_seconds": 0.0,
        "total_seconds": 0.0,
    }
    any_timing = False
    for record in records:
        timing = record.timing
        if not isinstance(timing, dict):
            continue
        any_timing = True
        for key in totals:
            value = timing.get(key)
            if isinstance(value, int | float):
                totals[key] += float(value)
    if not any_timing:
        return None
    return {key: round(value, 6) for key, value in totals.items()}


def _benchmark_command(target: str) -> str:
    return f"uv run amiga-benchmark-target {target}"


def _benchmark_record(
    target: str,
    binary_display_path: str,
    status: str,
    elapsed_seconds: float,
    c_benchmark: dict[str, object] | None,
    entities_path: Path,
    disasm_path: Path,
    error: str | None = None,
    targets: dict[str, TargetBenchmark] | None = None,
) -> TargetBenchmark:
    benchmark_version = c_benchmark.get("benchmark_version") if c_benchmark is not None else None
    platform = c_benchmark.get("platform") if c_benchmark is not None else None
    timing = c_benchmark.get("timing") if c_benchmark is not None else None
    file = c_benchmark.get("file") if c_benchmark is not None else None
    analysis = c_benchmark.get("analysis") if c_benchmark is not None else None
    render = c_benchmark.get("render") if c_benchmark is not None else None
    sections = c_benchmark.get("sections") if c_benchmark is not None else None
    facts_v2 = c_benchmark.get("facts_v2") if c_benchmark is not None else None
    return TargetBenchmark(
        target=target,
        binary=binary_display_path,
        command=_benchmark_command(target),
        measured_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        status=status,
        elapsed_seconds=round(elapsed_seconds, 2),
        benchmark_bytes=len(json.dumps(c_benchmark, sort_keys=True).encode("utf-8")) if c_benchmark is not None else None,
        entities_bytes=entities_path.stat().st_size if entities_path.exists() else None,
        disasm_bytes=disasm_path.stat().st_size if disasm_path.exists() else None,
        benchmark_version=benchmark_version if isinstance(benchmark_version, int) else None,
        platform=platform if isinstance(platform, str) else None,
        timing=timing if isinstance(timing, dict) else None,
        file=file if isinstance(file, dict) else None,
        analysis=analysis if isinstance(analysis, dict) else None,
        render=render if isinstance(render, dict) else None,
        sections=sections if isinstance(sections, list) else None,
        entities=_entities_benchmark(entities_path),
        error=error,
        targets=targets,
        facts_v2=facts_v2 if isinstance(facts_v2, dict) else None,
    )


def _default_disasm_path(target_dir: Path, target: str) -> Path:
    return target_dir / f"{target_output_stem(target_dir.name)}.s"


def _assembler_profile_for_target(target_dir: Path) -> str:
    if target_dir.name == "amiga_hunk_genam":
        return "devpac"
    return "vasm"


def _c_syntax_for_assembler_profile(assembler_profile_name: str) -> str:
    if assembler_profile_name == "devpac":
        return "genam"
    return assembler_profile_name


def _benchmark_binary_target(
    target: str,
    *,
    write_output: bool,
) -> TargetBenchmark:
    paths = resolve_project_paths(target, project_root=ROOT, require_entities=False)
    target_dir = paths.target_dir
    entities_path = paths.entities_path
    disasm_path = paths.output_path or _default_disasm_path(target_dir, target)

    disasm_path.unlink(missing_ok=True)

    start = time.perf_counter()
    assembler_profile_name = _assembler_profile_for_target(target_dir)
    c_benchmark: dict[str, object] | None = None
    try:
        c_syntax = _c_syntax_for_assembler_profile(assembler_profile_name)
        with effective_metadata_file(target_dir) as metadata_path:
            c_benchmark, rendered_text = benchmark_project_source_with_text_from_c_backend(
                paths.binary_source,
                syntax=c_syntax,
                metadata_path=metadata_path,
                project_root=ROOT,
            )
        c_benchmark["path"] = paths.binary_source.display_path
        assembler_profile = load_assembler_profile(assembler_profile_name)
        newline = "\n" if assembler_profile.render.line_ending == "lf" else "\r\n"
        disasm_path.write_text(rendered_text, encoding="utf-8", newline=newline)
        elapsed = time.perf_counter() - start
        if not disasm_path.exists():
            raise FileNotFoundError(f"missing benchmark output {disasm_path}")
        record = _benchmark_record(
            target,
            paths.binary_source.display_path,
            "ok",
            elapsed,
            c_benchmark,
            entities_path,
            disasm_path,
        )
    except Exception as exc:
        elapsed = time.perf_counter() - start
        record = _benchmark_record(
            target,
            paths.binary_source.display_path,
            "failed",
            elapsed,
            c_benchmark,
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
    if manifest.bootblock_target_name is not None:
        child_targets.append(manifest.bootblock_target_name)
    child_targets.extend(
        imported.target_name
        for imported in sorted(manifest.imported_targets, key=lambda imported: imported.entry_path)
    )

    started = time.perf_counter()
    child_records: dict[str, TargetBenchmark] = {}
    for child_target in child_targets:
        child_records[child_target] = _benchmark_binary_target(
            child_target,
            write_output=True,
        )
    elapsed = time.perf_counter() - started
    failures = [record for record in child_records.values() if record.status != "ok"]
    c_timing = _sum_c_timing(list(child_records.values()))
    record = TargetBenchmark(
        target=target,
        binary=manifest.source_path,
        command=_benchmark_command(target),
        measured_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        status="failed" if failures else "ok",
        elapsed_seconds=round(elapsed, 2),
        benchmark_bytes=sum(record.benchmark_bytes or 0 for record in child_records.values()) or None,
        entities_bytes=sum(record.entities_bytes or 0 for record in child_records.values()) or None,
        disasm_bytes=sum(record.disasm_bytes or 0 for record in child_records.values()) or None,
        benchmark_version=1,
        platform="disk-project",
        timing=c_timing,
        file=None,
        analysis=None,
        render=None,
        sections=None,
        entities=None,
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
    return _benchmark_binary_target(
        target,
        write_output=True,
    )


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser()
    parser.add_argument("targets", nargs="+")
    args = parser.parse_args(argv[1:])
    had_failures = False
    for target in args.targets:
        record = benchmark_target(target)
        if record.status == "ok":
            print(f"{record.target}: {record.elapsed_seconds:.2f}s")
        else:
            had_failures = True
            print(f"{record.target}: failed after {record.elapsed_seconds:.2f}s")
    return 1 if had_failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
