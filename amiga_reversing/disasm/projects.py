from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from amiga_reversing.amiga_disk.models import DiskManifest
from amiga_reversing.disasm.binary_source import (
    is_internal_target,
    resolve_target_binary_source,
)
from amiga_reversing.disasm.manual_actions import (
    ReviewItemKind,
    ReviewItemScope,
    ReviewItemState,
    ReviewState,
    finalize_review_items,
    load_manual_projection,
    manual_action_log_path,
    review_item_is_open,
)
from amiga_reversing.disasm.project_ids import (
    disk_project_id,
    ensure_safe_project_id,
    hunk_target_id,
    is_disk_project_id,
    normalize_filename_stem,
)
from amiga_reversing.disasm.project_paths import (
    PROJECT_ROOT,
    resolve_project_dir,
)
from amiga_reversing.disasm.reproduction import reproduction_report_path
from amiga_reversing.disasm.target_metadata import load_target_metadata

STATE_FILE_NAME = ".browser_state.json"
PROJECT_METADATA_FILE_NAME = ".project.json"
PROJECT_METADATA_SCHEMA_VERSION = 2
DECOMPRESSION_STATUS_NEEDS_REVIEW_BLOCKER = 6


class ProjectKind(StrEnum):
    BINARY = "binary"
    DISK = "disk"


@dataclass(frozen=True, slots=True)
class BrowserState:
    recent_projects: dict[str, str]


@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    schema_version: int
    created_at: str
    updated_at: str
    origin: dict[str, object]


@dataclass(frozen=True, slots=True)
class ProjectRecord:
    id: str
    name: str
    kind: ProjectKind
    target_dir: str
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
    manual_action_log_path: str | None = None
    review_state: ReviewState | None = None
    review_items: tuple[dict[str, object], ...] = ()
    manual_state: dict[str, object] | None = None
    origin: dict[str, object] = field(default_factory=lambda: {"kind": "project_record"})

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProjectKind):
            raise TypeError("ProjectRecord.kind must be a ProjectKind")

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


def _load_project_metadata(project_dir: Path) -> ProjectMetadata:
    metadata_path = _metadata_path(project_dir)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing {PROJECT_METADATA_FILE_NAME} for project: {project_dir.name}")
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    schema_version = payload["schema_version"]
    assert isinstance(schema_version, int)
    if schema_version != PROJECT_METADATA_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported {PROJECT_METADATA_FILE_NAME} schema for project {project_dir.name}: "
            f"{schema_version}"
        )
    created_at = payload["created_at"]
    updated_at = payload["updated_at"]
    origin = payload["origin"]
    assert isinstance(created_at, str)
    assert isinstance(updated_at, str)
    assert isinstance(origin, dict)
    return ProjectMetadata(
        schema_version=schema_version,
        created_at=created_at,
        updated_at=updated_at,
        origin=dict(origin),
    )


def _save_project_metadata(project_dir: Path, metadata: ProjectMetadata) -> None:
    _metadata_path(project_dir).write_text(
        json.dumps(asdict(metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def initialize_project_metadata(
    project_dir: Path,
    *,
    timestamp: datetime | None = None,
    origin: dict[str, object],
) -> None:
    now = (timestamp or datetime.now(UTC)).isoformat()
    _save_project_metadata(
        project_dir,
        ProjectMetadata(
            schema_version=PROJECT_METADATA_SCHEMA_VERSION,
            created_at=now,
            updated_at=now,
            origin=dict(origin),
        ),
    )


def mark_project_updated(project_dir: Path, *, timestamp: datetime | None = None) -> None:
    metadata = _load_project_metadata(project_dir)
    _save_project_metadata(
        project_dir,
        ProjectMetadata(
            schema_version=metadata.schema_version,
            created_at=metadata.created_at,
            updated_at=(timestamp or datetime.now(UTC)).isoformat(),
            origin=metadata.origin,
        ),
    )


def set_project_origin(project_dir: Path, *, origin: dict[str, object], timestamp: datetime | None = None) -> None:
    metadata = _load_project_metadata(project_dir)
    _save_project_metadata(
        project_dir,
        ProjectMetadata(
            schema_version=metadata.schema_version,
            created_at=metadata.created_at,
            updated_at=(timestamp or datetime.now(UTC)).isoformat(),
            origin=dict(origin),
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
    output_candidates = sorted(target_dir.glob("*.s"))
    binary_source = resolve_target_binary_source(target_dir, project_root=project_root)
    manual_projection = load_manual_projection(
        target_dir,
        binary_source=binary_source,
        stronger_metadata=target_metadata,
    )
    reproduction_review_items = _reproduction_review_items(target_dir)
    decompression_review_items = _decompression_review_items(binary_source.analysis_cache_path if binary_source else None)
    review_items = (*manual_projection.review_items, *reproduction_review_items, *decompression_review_items)
    review_state = _combined_review_state(manual_projection.review_state, review_items)
    return ProjectRecord(
        id=project_id,
        name=target_dir.name,
        kind=ProjectKind.BINARY,
        target_dir=str(target_dir),
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
        manual_action_log_path=str(manual_action_log_path(target_dir)),
        review_state=review_state,
        review_items=review_items,
        manual_state=manual_projection.to_dict(),
        origin=metadata.origin,
    )


def _combined_review_state(
    manual_state: ReviewState,
    review_items: tuple[dict[str, object], ...],
) -> ReviewState:
    if manual_state is ReviewState.BLOCKED:
        return ReviewState.BLOCKED
    open_items = tuple(item for item in review_items if review_item_is_open(item))
    if any(item.get("review_blocker") is True for item in open_items):
        return ReviewState.BLOCKED
    if manual_state is ReviewState.NEEDS_REVIEW or open_items:
        return ReviewState.NEEDS_REVIEW
    return ReviewState.CLEAR


def _reproduction_review_items(target_dir: Path) -> tuple[dict[str, object], ...]:
    report_path = reproduction_report_path(target_dir)
    if not report_path.exists():
        return ()
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return finalize_review_items((
            {
                "kind": ReviewItemKind.REPRODUCTION_MISMATCH,
                "scope": ReviewItemScope.TARGET,
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "message": f"Reproduction report cannot be checked: {exc}",
                "source": "reproduction",
            },
        ))
    if not isinstance(report, dict):
        return finalize_review_items((
            {
                "kind": ReviewItemKind.REPRODUCTION_MISMATCH,
                "scope": ReviewItemScope.TARGET,
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "message": "Reproduction report cannot be checked",
                "source": "reproduction",
            },
        ))
    return finalize_review_items(tuple(_raw_reproduction_review_items(report)))


def _decompression_review_items(analysis_cache_path: Path | None) -> tuple[dict[str, object], ...]:
    if analysis_cache_path is None or not analysis_cache_path.exists():
        return ()
    try:
        payload = json.loads(analysis_cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, dict):
        return ()
    analysis = payload.get("analysis")
    if isinstance(analysis, dict):
        payload = analysis
    events = payload.get("decompression_events")
    if not isinstance(events, list):
        return ()
    items: list[dict[str, object]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("status_id") != DECOMPRESSION_STATUS_NEEDS_REVIEW_BLOCKER:
            continue
        event_id = event.get("event_id")
        source_section = event.get("source_section")
        source_offset = event.get("source_section_offset")
        reason = event.get("reason") if isinstance(event.get("reason"), str) else "needs_review_blocker"
        if not isinstance(event_id, str) or not event_id:
            event_id = f"decompression:{source_section}:{source_offset}:{reason}"
        items.append(
            {
                "kind": ReviewItemKind.DECOMPRESSION_BLOCKER,
                "item_id": f"decompression_blocker:{event_id}",
                "scope": (
                    ReviewItemScope.RANGE
                    if isinstance(source_section, int) and isinstance(source_offset, int)
                    else ReviewItemScope.TARGET
                ),
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "source": "decompression",
                "event_id": event_id,
                "reason": reason,
                "hunk": source_section if isinstance(source_section, int) else 0,
                "start": source_offset if isinstance(source_offset, int) else 0,
                "end": source_offset + 1 if isinstance(source_offset, int) else 1,
                "message": f"Decompressed payload requires review: {reason}",
            }
        )
    return finalize_review_items(tuple(items))


def _raw_reproduction_review_items(report: dict[str, object]) -> list[dict[str, object]]:
    comparison = report.get("comparison")
    status = report.get("status")
    if not isinstance(comparison, dict):
        if status in {None, "not_ready", "exact"} and report.get("exact") is True:
            return []
        return [
            {
                "kind": ReviewItemKind.REPRODUCTION_MISMATCH,
                "scope": ReviewItemScope.TARGET,
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "status": status,
                "message": f"Reproduction content exactness cannot be checked: {status}",
                "source": "reproduction",
            }
        ]

    file_structure_issue_kinds = _string_list(comparison.get("file_structure_issue_kinds"))
    content_exact = comparison.get("content_exact")
    full_file_exact = comparison.get("full_file_exact")
    if content_exact is not True:
        return [
            {
                "kind": ReviewItemKind.REPRODUCTION_MISMATCH,
                "scope": ReviewItemScope.TARGET,
                "state": ReviewItemState.OPEN,
                "review_blocker": True,
                "status": status,
                "comparison_status": comparison.get("status"),
                "failure_kinds": _string_list(comparison.get("failure_kinds")),
                "message": "Reproduction content exactness failed or could not be checked",
                "source": "reproduction",
            }
        ]
    if full_file_exact is True and not file_structure_issue_kinds:
        return []

    kind = (
        ReviewItemKind.UNSUPPORTED_CONTAINER_SHAPE
        if ReviewItemKind.UNSUPPORTED_CONTAINER_SHAPE in file_structure_issue_kinds
        else ReviewItemKind.REPRODUCTION_MISMATCH
    )
    return [
        {
            "kind": kind,
            "scope": ReviewItemScope.TARGET,
            "state": ReviewItemState.OPEN,
            "review_blocker": False,
            "status": status,
            "comparison_status": comparison.get("status"),
            "file_structure_issue_kinds": file_structure_issue_kinds,
            "message": "Reproduction content is exact but container shape differs",
            "source": "reproduction",
        }
    ]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, str)]


def derive_project_name(filename: str) -> str:
    result = hunk_target_id(normalize_filename_stem(Path(filename).stem))
    assert isinstance(result, str)
    return result


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
        kind=ProjectKind.DISK,
        target_dir=str(disk_dir),
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
        origin=metadata.origin,
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


def create_project(
    project_name: str,
    project_root: Path = PROJECT_ROOT,
    *,
    origin: dict[str, object] | None = None,
) -> ProjectRecord:
    project_name = ensure_safe_project_id(project_name)
    target_dir = _targets_dir(project_root) / project_name
    if target_dir.exists():
        raise FileExistsError(f"Project already exists: {project_name}")
    target_dir.mkdir(parents=True)
    initialize_project_metadata(
        target_dir,
        origin=origin or {"kind": "manual_project", "project_id": project_name},
    )
    return get_project(project_name, project_root=project_root)


def create_project_at_path(
    target_relpath: str,
    project_root: Path = PROJECT_ROOT,
    *,
    origin: dict[str, object] | None = None,
) -> Path:
    target_dir = project_root / Path(target_relpath)
    if target_dir.exists():
        raise FileExistsError(f"Project already exists: {target_relpath}")
    target_dir.mkdir(parents=True)
    initialize_project_metadata(
        target_dir,
        origin=origin or {"kind": "materialized_target", "target_relpath": target_relpath},
    )
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
    if project.kind is ProjectKind.DISK:
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
