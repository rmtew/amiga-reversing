from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from m68k.analysis import HunkAnalysis
from m68k_kb import runtime_os

TARGETS_DIR = ROOT / "targets"


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
    analysis: AnalysisBenchmark | None
    entities: EntityBenchmark | None
    error: str | None = None


def _binary_path(target_dir: Path) -> Path:
    binary_path_file = target_dir / "binary_path.txt"
    if not binary_path_file.exists():
        raise FileNotFoundError(f"missing {binary_path_file}")
    relative = binary_path_file.read_text(encoding="ascii").strip()
    if not relative:
        raise ValueError(f"empty {binary_path_file}")
    return ROOT / relative


def _covered_bytes(blocks) -> int:
    return sum(block.end - block.start for block in blocks.values())


def _analysis_benchmark(analysis_path: Path) -> AnalysisBenchmark | None:
    if not analysis_path.exists():
        return None
    ha = HunkAnalysis.load(analysis_path, runtime_os)
    code_bytes = len(ha.code)
    core_covered_bytes = _covered_bytes(ha.blocks)
    hint_covered_bytes = _covered_bytes(ha.hint_blocks)
    resolved_calls = tuple(call for call in ha.lib_calls if call.library != "unknown")
    libraries = {call.library for call in resolved_calls}
    return AnalysisBenchmark(
        code_bytes=code_bytes,
        core_block_count=len(ha.blocks),
        core_instruction_count=sum(len(block.instructions) for block in ha.blocks.values()),
        core_covered_bytes=core_covered_bytes,
        core_coverage_ratio=round(core_covered_bytes / code_bytes, 4) if code_bytes else 0.0,
        hint_block_count=len(ha.hint_blocks),
        hint_instruction_count=sum(len(block.instructions) for block in ha.hint_blocks.values()),
        hint_covered_bytes=hint_covered_bytes,
        hint_coverage_ratio=round(hint_covered_bytes / code_bytes, 4) if code_bytes else 0.0,
        xref_count=len(ha.xrefs),
        jump_table_count=len(ha.jump_tables),
        indirect_site_count=len(ha.indirect_sites),
        call_target_count=len(ha.call_targets),
        branch_target_count=len(ha.branch_targets),
        library_call_count=len(ha.lib_calls),
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


def _benchmark_record(target: str,
                      binary_path: Path,
                      status: str,
                      elapsed_seconds: float,
                      analysis_path: Path,
                      entities_path: Path,
                      disasm_path: Path,
                      error: str | None = None) -> TargetBenchmark:
    binary_rel = str(binary_path.relative_to(ROOT)).replace("\\", "/")
    command = f"uv run scripts/gen_disasm.py {binary_rel} -t targets/{target}"
    return TargetBenchmark(
        target=target,
        binary=binary_rel,
        command=command,
        measured_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        status=status,
        elapsed_seconds=round(elapsed_seconds, 2),
        analysis_bytes=analysis_path.stat().st_size if analysis_path.exists() else None,
        entities_bytes=entities_path.stat().st_size if entities_path.exists() else None,
        disasm_bytes=disasm_path.stat().st_size if disasm_path.exists() else None,
        analysis=_analysis_benchmark(analysis_path),
        entities=_entities_benchmark(entities_path),
        error=error,
    )


def benchmark_target(target: str) -> TargetBenchmark:
    target_dir = TARGETS_DIR / target
    if not target_dir.is_dir():
        raise FileNotFoundError(f"missing target dir {target_dir}")

    binary_path = _binary_path(target_dir)
    analysis_path = ROOT / "bin" / f"{binary_path.name}.analysis"
    entities_path = target_dir / "entities.jsonl"
    disasm_path = target_dir / f"{binary_path.name}.s"

    analysis_path.unlink(missing_ok=True)
    entities_path.unlink(missing_ok=True)

    start = time.perf_counter()
    proc = subprocess.run(
        ["uv", "run", "scripts/gen_disasm.py",
         str(binary_path.relative_to(ROOT)),
         "-t", f"targets/{target}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - start
    if proc.returncode == 0:
        if not analysis_path.exists():
            raise FileNotFoundError(f"missing benchmark output {analysis_path}")
        if not entities_path.exists():
            raise FileNotFoundError(f"missing benchmark output {entities_path}")
        if not disasm_path.exists():
            raise FileNotFoundError(f"missing benchmark output {disasm_path}")
        record = _benchmark_record(
            target,
            binary_path,
            "ok",
            elapsed,
            analysis_path,
            entities_path,
            disasm_path,
        )
    else:
        error = (proc.stderr or proc.stdout).strip().splitlines()[-1]
        record = _benchmark_record(
            target,
            binary_path,
            "failed",
            elapsed,
            analysis_path,
            entities_path,
            disasm_path,
            error=error,
        )
    (target_dir / "benchmark.json").write_text(
        json.dumps(asdict(record), indent=2) + "\n",
        encoding="ascii",
    )
    return record


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit("usage: uv run scripts/benchmark_target.py <target> [<target> ...]")
    for target in argv[1:]:
        record = benchmark_target(target)
        if record.status == "ok":
            print(f"{record.target}: {record.elapsed_seconds:.2f}s")
        else:
            print(f"{record.target}: failed after {record.elapsed_seconds:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
