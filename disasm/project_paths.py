from __future__ import annotations
"""Project path and provenance resolution."""

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ProjectPaths:
    name: str
    target_dir: Path
    entities_path: Path
    output_path: Path | None
    binary_path: Path
    analysis_cache_path: Path
    provenance: str


def _resolve_recorded_binary_path(target_dir: Path, project_root: Path) -> Path | None:
    binary_path_file = target_dir / "binary_path.txt"
    if not binary_path_file.exists():
        return None
    recorded = Path(binary_path_file.read_text().strip())
    if recorded.exists():
        return recorded
    candidate = (project_root / recorded).resolve()
    if candidate.exists():
        return candidate
    return None


def resolve_project_paths(name: str, project_root: Path = PROJECT_ROOT) -> ProjectPaths:
    target_dir = project_root / "targets" / name
    if not target_dir.exists():
        raise FileNotFoundError(f"Unknown target: {name}")

    entities_path = target_dir / "entities.jsonl"
    if not entities_path.exists():
        raise FileNotFoundError(f"Missing entities.jsonl for target: {name}")

    output_candidates = sorted(target_dir.glob("*.s"))
    output_path = output_candidates[0] if len(output_candidates) == 1 else None

    binary_path = _resolve_recorded_binary_path(target_dir, project_root)
    if binary_path is None:
        raise FileNotFoundError(
            f"Unable to resolve binary for target {name}; add binary_path.txt")

    return ProjectPaths(
        name=name,
        target_dir=target_dir,
        entities_path=entities_path,
        output_path=output_path,
        binary_path=binary_path,
        analysis_cache_path=binary_path.with_suffix(".analysis"),
        provenance="recorded",
    )
