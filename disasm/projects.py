from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from amiga_disk.models import DiskManifest
from disasm.binary_source import is_internal_target, resolve_target_binary_source
from disasm.project_ids import (
    disk_project_id,
    ensure_safe_project_id,
    hunk_target_id,
    is_disk_project_id,
    normalize_filename_stem,
)
from disasm.project_paths import (
    PROJECT_ROOT,
    resolve_project_dir,
    resolve_project_paths,
)
from disasm.session import build_disassembly_session
from disasm.target_metadata import load_target_metadata

if TYPE_CHECKING:
    from disasm.session import DisassemblySession

STATE_FILE_NAME = ".browser_state.json"
PROJECT_METADATA_FILE_NAME = ".project.json"


@dataclass(frozen=True, slots=True)
class BrowserState:
    recent_projects: dict[str, str]


@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    schema_version: int
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ProjectRecord:
    id: str
    name: str
    kind: Literal["binary", "disk"]
    target_dir: str
    entities_path: str | None
    output_path: str | None
    binary_path: str | None
    ready: bool
    last_opened: str | None
    manifest_path: str | None
    target_count: int | None
    source_path: str | None
    disk_type: str | None
    parent_project_id: str | None
    target_type: str | None
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        assert isinstance(result, dict)
        return result


def _targets_dir(project_root: Path) -> Path:
    return project_root / "targets"


def _is_internal_target(target_dir: Path, project_root: Path) -> bool:
    return bool(is_internal_target(target_dir, project_root=project_root))


def _state_path(project_root: Path) -> Path:
    return _targets_dir(project_root) / STATE_FILE_NAME


def _metadata_path(project_dir: Path) -> Path:
    return project_dir / PROJECT_METADATA_FILE_NAME


def _iso_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, UTC).isoformat()


def _load_project_metadata(project_dir: Path) -> ProjectMetadata:
    metadata_path = _metadata_path(project_dir)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing {PROJECT_METADATA_FILE_NAME} for project: {project_dir.name}")
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    schema_version = payload["schema_version"]
    created_at = payload["created_at"]
    updated_at = payload["updated_at"]
    assert isinstance(schema_version, int)
    assert isinstance(created_at, str)
    assert isinstance(updated_at, str)
    return ProjectMetadata(
        schema_version=schema_version,
        created_at=created_at,
        updated_at=updated_at,
    )


def _save_project_metadata(project_dir: Path, metadata: ProjectMetadata) -> None:
    _metadata_path(project_dir).write_text(
        json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def initialize_project_metadata(project_dir: Path, *, timestamp: datetime | None = None) -> None:
    now = (timestamp or datetime.now(UTC)).isoformat()
    _save_project_metadata(
        project_dir,
        ProjectMetadata(schema_version=1, created_at=now, updated_at=now),
    )


def mark_project_updated(project_dir: Path, *, timestamp: datetime | None = None) -> None:
    metadata = _load_project_metadata(project_dir)
    _save_project_metadata(
        project_dir,
        ProjectMetadata(
            schema_version=metadata.schema_version,
            created_at=metadata.created_at,
            updated_at=(timestamp or datetime.now(UTC)).isoformat(),
        ),
    )


def _load_state(project_root: Path) -> BrowserState:
    state_path = _state_path(project_root)
    if not state_path.exists():
        return BrowserState(recent_projects={})
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    recent_projects = payload["recent_projects"]
    assert isinstance(recent_projects, dict)
    result: dict[str, str] = {}
    for key, value in recent_projects.items():
        assert isinstance(key, str)
        assert isinstance(value, str)
        result[key] = value
    return BrowserState(recent_projects=result)


def _save_state(project_root: Path, state: BrowserState) -> None:
    state_path = _state_path(project_root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(asdict(state), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _binary_project_record(project_id: str, target_dir: Path, state: BrowserState, project_root: Path) -> ProjectRecord:
    metadata = _load_project_metadata(target_dir)
    target_metadata = load_target_metadata(target_dir)
    entities_path = target_dir / "entities.jsonl"
    if not entities_path.exists():
        raise FileNotFoundError(f"Missing entities.jsonl for target: {target_dir.name}")
    output_candidates = sorted(target_dir.glob("*.s"))
    binary_source = resolve_target_binary_source(target_dir, project_root=project_root)
    return ProjectRecord(
        id=project_id,
        name=target_dir.name,
        kind="binary",
        target_dir=str(target_dir),
        entities_path=str(entities_path),
        output_path=str(output_candidates[0]) if len(output_candidates) == 1 else None,
        binary_path=None if binary_source is None else binary_source.display_path,
        ready=binary_source is not None,
        last_opened=state.recent_projects.get(project_id),
        manifest_path=None,
        target_count=None,
        source_path=None,
        disk_type=None,
        parent_project_id=(
            None if binary_source is None or binary_source.parent_disk_id is None
            else disk_project_id(binary_source.parent_disk_id)
        ),
        target_type=None if target_metadata is None else target_metadata.target_type,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
    )


def derive_project_name(filename: str) -> str:
    return cast(str, hunk_target_id(normalize_filename_stem(Path(filename).stem)))


def dedupe_project_name(base_name: str, project_root: Path = PROJECT_ROOT) -> str:
    base_name = ensure_safe_project_id(base_name)
    targets_dir = _targets_dir(project_root)
    candidate = base_name
    suffix = 2
    while (targets_dir / candidate).exists():
        candidate = f"{base_name}-{suffix}"
        suffix += 1
    return candidate


def _disk_project_record(disk_dir: Path, state: BrowserState) -> ProjectRecord:
    metadata = _load_project_metadata(disk_dir)
    manifest_path = disk_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest.json for disk project: {disk_dir.name}")
    manifest = DiskManifest.load(manifest_path)
    project_id = disk_dir.name
    disk_type = "DOS" if manifest.analysis.filesystem is not None else "non-DOS"
    return ProjectRecord(
        id=project_id,
        name=manifest.disk_id,
        kind="disk",
        target_dir=str(disk_dir),
        entities_path=None,
        output_path=None,
        binary_path=None,
        ready=False,
        last_opened=state.recent_projects.get(project_id),
        manifest_path=str(manifest_path),
        target_count=len(manifest.imported_targets) + (1 if manifest.bootblock_target_name is not None else 0),
        source_path=manifest.source_path,
        disk_type=disk_type,
        parent_project_id=None,
        target_type=None,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
    )


def _load_project_record(project_name: str, state: BrowserState, project_root: Path) -> ProjectRecord:
    target_dir = resolve_project_dir(project_name, project_root=project_root)
    if is_disk_project_id(project_name):
        return _disk_project_record(target_dir, state)
    return _binary_project_record(project_name, target_dir, state, project_root)


def get_project(project_name: str, project_root: Path = PROJECT_ROOT) -> ProjectRecord:
    return _load_project_record(project_name, _load_state(project_root), project_root)


def list_projects(project_root: Path = PROJECT_ROOT) -> list[ProjectRecord]:
    targets_dir = _targets_dir(project_root)
    if not targets_dir.exists():
        return []
    state = _load_state(project_root)
    projects: list[ProjectRecord] = []
    for target_dir in targets_dir.iterdir():
        if not target_dir.is_dir() or target_dir.name.startswith("."):
            continue
        if is_disk_project_id(target_dir.name):
            projects.append(_disk_project_record(target_dir, state))
            continue
        if _is_internal_target(target_dir, project_root):
            continue
        projects.append(_binary_project_record(target_dir.name, target_dir, state, project_root))
    projects.sort(key=lambda project: project.id)
    projects.sort(key=lambda project: project.last_opened or "", reverse=True)
    return projects


def create_project(project_name: str, project_root: Path = PROJECT_ROOT) -> ProjectRecord:
    project_name = ensure_safe_project_id(project_name)
    target_dir = _targets_dir(project_root) / project_name
    if target_dir.exists():
        raise FileExistsError(f"Project already exists: {project_name}")
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("", encoding="utf-8")
    initialize_project_metadata(target_dir)
    return get_project(project_name, project_root=project_root)


def create_project_at_path(target_relpath: str, project_root: Path = PROJECT_ROOT) -> Path:
    target_dir = project_root / Path(target_relpath)
    if target_dir.exists():
        raise FileExistsError(f"Project already exists: {target_relpath}")
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("", encoding="utf-8")
    initialize_project_metadata(target_dir)
    return target_dir


def mark_project_opened(project_name: str, project_root: Path = PROJECT_ROOT) -> ProjectRecord:
    get_project(project_name, project_root=project_root)
    state = _load_state(project_root)
    state.recent_projects[project_name] = datetime.now(UTC).isoformat()
    _save_state(project_root, state)
    return get_project(project_name, project_root=project_root)


def delete_project(project_name: str, project_root: Path = PROJECT_ROOT) -> None:
    project = get_project(project_name, project_root=project_root)
    state = _load_state(project_root)
    state.recent_projects.pop(project_name, None)
    if project.kind == "disk":
        assert project.manifest_path is not None
        manifest = DiskManifest.load(Path(project.manifest_path))
        if manifest.bootblock_target_name is not None:
            target_dir = project_root / manifest.bootblock_target_path
            if target_dir.exists():
                shutil.rmtree(target_dir)
            state.recent_projects.pop(manifest.bootblock_target_name, None)
        for imported_target in manifest.imported_targets:
            target_dir = project_root / imported_target.target_path
            if target_dir.exists():
                shutil.rmtree(target_dir)
            state.recent_projects.pop(imported_target.target_name, None)
        source_path = project_root / Path(manifest.source_path)
        if source_path.exists() and source_path.is_file():
            source_path.resolve().relative_to(project_root.resolve())
            source_path.unlink()
        target_dir = Path(project.target_dir)
        if target_dir.exists():
            shutil.rmtree(target_dir)
    else:
        target_dir = Path(project.target_dir)
        if target_dir.exists():
            shutil.rmtree(target_dir)
    _save_state(project_root, state)


def build_project_session(
    target_name: str,
    project_root: Path = PROJECT_ROOT,
    profile_stages: bool = False,
) -> DisassemblySession:
    project = get_project(target_name, project_root=project_root)
    if project.kind != "binary":
        raise ValueError(f"Project {target_name} does not have a binary disassembly session")
    paths = resolve_project_paths(target_name, project_root=project_root)
    return build_disassembly_session(
        paths.binary_source,
        str(paths.entities_path),
        str(paths.output_path) if paths.output_path else None,
        profile_stages=profile_stages,
    )
