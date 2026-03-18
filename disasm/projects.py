from __future__ import annotations

from pathlib import Path

from disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from disasm.session import build_disassembly_session


def list_projects(project_root: Path = PROJECT_ROOT) -> list[dict]:
    targets_dir = project_root / "targets"
    projects: list[dict] = []
    for target_dir in sorted(path for path in targets_dir.iterdir() if path.is_dir()):
        entities_path = target_dir / "entities.jsonl"
        if not entities_path.exists():
            continue
        resolved = resolve_project_paths(target_dir.name, project_root=project_root)
        projects.append({
            "name": target_dir.name,
            "target_dir": str(target_dir),
            "entities_path": str(entities_path),
            "binary_path": str(resolved.binary_path),
            "output_path": str(resolved.output_path) if resolved.output_path else None,
            "provenance": resolved.provenance,
        })
    return projects
def build_project_session(target_name: str, project_root: Path = PROJECT_ROOT,
                          profile_stages: bool = False):
    paths = resolve_project_paths(target_name, project_root=project_root)
    return build_disassembly_session(
        str(paths.binary_path),
        str(paths.entities_path),
        str(paths.output_path) if paths.output_path else None,
        profile_stages=profile_stages,
    )
