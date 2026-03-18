from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from disasm.session import build_disassembly_session

SAFE_PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
STATE_FILE_NAME = ".browser_state.json"


def _targets_dir(project_root: Path) -> Path:
    return project_root / "targets"


def _state_path(project_root: Path) -> Path:
    return _targets_dir(project_root) / STATE_FILE_NAME


def _load_state(project_root: Path) -> dict:
    state_path = _state_path(project_root)
    if not state_path.exists():
        return {"recent_projects": {}}
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    recent_projects = payload.get("recent_projects", {})
    if not isinstance(recent_projects, dict):
        raise ValueError("Invalid browser state: recent_projects must be an object")
    return {"recent_projects": recent_projects}


def _save_state(project_root: Path, state: dict) -> None:
    state_path = _state_path(project_root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _recorded_binary_path(target_dir: Path, project_root: Path) -> tuple[str | None, bool]:
    binary_path_file = target_dir / "binary_path.txt"
    if not binary_path_file.exists():
        return None, False
    recorded = binary_path_file.read_text(encoding="utf-8").strip()
    if not recorded:
        raise ValueError(f"Empty binary_path.txt for target: {target_dir.name}")
    candidate = Path(recorded)
    if not candidate.exists():
        candidate = (project_root / recorded).resolve()
    return recorded, candidate.exists()


def _project_record(target_dir: Path, state: dict, project_root: Path) -> dict:
    entities_path = target_dir / "entities.jsonl"
    if not entities_path.exists():
        raise FileNotFoundError(f"Missing entities.jsonl for target: {target_dir.name}")
    output_candidates = sorted(target_dir.glob("*.s"))
    recorded_binary_path, ready = _recorded_binary_path(target_dir, project_root)
    return {
        "id": target_dir.name,
        "name": target_dir.name,
        "target_dir": str(target_dir),
        "entities_path": str(entities_path),
        "output_path": str(output_candidates[0]) if len(output_candidates) == 1 else None,
        "binary_path": recorded_binary_path,
        "ready": ready,
        "last_opened": state["recent_projects"].get(target_dir.name),
    }


def get_project(project_name: str, project_root: Path = PROJECT_ROOT) -> dict:
    target_dir = _targets_dir(project_root) / project_name
    if not target_dir.exists():
        raise FileNotFoundError(f"Unknown target: {project_name}")
    return _project_record(target_dir, _load_state(project_root), project_root)


def list_projects(project_root: Path = PROJECT_ROOT) -> list[dict]:
    targets_dir = _targets_dir(project_root)
    if not targets_dir.exists():
        return []
    state = _load_state(project_root)
    projects = [
        _project_record(target_dir, state, project_root)
        for target_dir in targets_dir.iterdir()
        if target_dir.is_dir() and not target_dir.name.startswith(".")
    ]
    projects.sort(key=lambda project: project["id"])
    projects.sort(key=lambda project: project["last_opened"] or "", reverse=True)
    return projects


def create_project(project_name: str, project_root: Path = PROJECT_ROOT) -> dict:
    project_name = project_name.strip()
    if not SAFE_PROJECT_RE.fullmatch(project_name):
        raise ValueError("Project id must match [A-Za-z0-9][A-Za-z0-9._-]*")
    target_dir = _targets_dir(project_root) / project_name
    if target_dir.exists():
        raise FileExistsError(f"Project already exists: {project_name}")
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("", encoding="utf-8")
    return get_project(project_name, project_root=project_root)


def mark_project_opened(project_name: str, project_root: Path = PROJECT_ROOT) -> dict:
    get_project(project_name, project_root=project_root)
    state = _load_state(project_root)
    state["recent_projects"][project_name] = datetime.now(timezone.utc).isoformat()
    _save_state(project_root, state)
    return get_project(project_name, project_root=project_root)


def build_project_session(target_name: str, project_root: Path = PROJECT_ROOT,
                          profile_stages: bool = False):
    paths = resolve_project_paths(target_name, project_root=project_root)
    return build_disassembly_session(
        str(paths.binary_path),
        str(paths.entities_path),
        str(paths.output_path) if paths.output_path else None,
        profile_stages=profile_stages,
    )
