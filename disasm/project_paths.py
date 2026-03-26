from __future__ import annotations

"""Project path and provenance resolution."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from amiga_disk.models import DiskManifest
from disasm.binary_source import BinarySource, resolve_target_binary_source

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ProjectPaths:
    name: str
    kind: Literal["binary"]
    target_dir: Path
    entities_path: Path
    output_path: Path | None
    binary_source: BinarySource


def resolve_project_dir(name: str, project_root: Path = PROJECT_ROOT) -> Path:
    target_dir = project_root / "targets" / name
    if target_dir.exists():
        return target_dir
    targets_dir = project_root / "targets"
    if not targets_dir.exists():
        raise FileNotFoundError(f"Unknown target: {name}")
    for disk_dir in targets_dir.iterdir():
        if not disk_dir.is_dir():
            continue
        manifest_path = disk_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = DiskManifest.load(manifest_path)
        if manifest.bootblock_target_name == name:
            return project_root / Path(manifest.bootblock_target_path)
        for imported_target in manifest.imported_targets:
            if imported_target.target_name == name:
                return project_root / Path(imported_target.target_path)
    raise FileNotFoundError(f"Unknown target: {name}")


def resolve_project_paths(
    name: str,
    project_root: Path = PROJECT_ROOT,
    *,
    require_entities: bool = True,
) -> ProjectPaths:
    target_dir = resolve_project_dir(name, project_root=project_root)
    if (target_dir / "manifest.json").exists():
        raise ValueError(f"Disk project {name} does not resolve to binary project paths")

    entities_path = target_dir / "entities.jsonl"
    if require_entities and not entities_path.exists():
        raise FileNotFoundError(f"Missing entities.jsonl for target: {name}")

    output_candidates = sorted(target_dir.glob("*.s"))
    output_path = output_candidates[0] if len(output_candidates) == 1 else None

    binary_source = resolve_target_binary_source(target_dir, project_root=project_root)
    if binary_source is None:
        raise FileNotFoundError(
            f"Unable to resolve binary source for target {name}; add source_binary.json"
        )

    return ProjectPaths(
        name=name,
        kind="binary",
        target_dir=target_dir,
        entities_path=entities_path,
        output_path=output_path,
        binary_source=binary_source,
    )
