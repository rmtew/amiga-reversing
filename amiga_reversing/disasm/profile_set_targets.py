from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from amiga_reversing.amiga_disk.models import DiskManifest
from amiga_reversing.amiga_disk.project import create_disk_project
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    write_source_descriptor,
)
from amiga_reversing.disasm.c_backend import inspect_disk_with_c_backend
from amiga_reversing.disasm.project_ids import (
    ensure_safe_project_id,
    normalize_filename_stem,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import create_project_at_path
from amiga_reversing.disasm.target_local_state import PROFILE_SET_TARGET_METADATA_FILES
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata

RESOURCE_DIRS = (
    PROJECT_ROOT / "resources" / "platform_amiga",
    PROJECT_ROOT / "resources" / "platform_atari_st",
)
PROFILE_RESOURCE_DISK_PATTERNS = (
    "3d construction kit",
    "argasm",
    "bloodwych",
    "devpac",
    "search for the king",
    "workbench",
)
PROFILE_TARGET_CATEGORIES = (
    ("king", ("king",)),
    ("bloodwych", ("bloodwych",)),
    ("icon.library", ("icon.library",)),
    ("mathtrans.library", ("mathtrans.library",)),
    ("3dedit", ("3dedit",)),
    ("fastfilesystem", ("fastfilesystem",)),
    ("atari_3d", ("resource-atari", "3d-construction-kit")),
    ("devpac_amon030", ("amon030",)),
)
ProfileTargetCategories = Sequence[tuple[str, Sequence[str]]]
BUILD_RUNTIME_FILES = (
    "platform_file_lib.dll",
    "platform_disk_lib.dll",
    "m68k_disassembler_lib.dll",
    "m68k_assembler_lib.dll",
    "m68k_assembler_app.exe",
)
INCLUDE_DIRS = (
    Path("ext") / "amiga_includes" / "ndk_2.0" / "include",
    Path("ext") / "atarist_includes" / "devpac_3_10" / "include",
)
PROFILE_SET_STAMP_FILE = ".profile_set_targets.json"


@dataclass(frozen=True, slots=True)
class ProfileSetProject:
    project_root: Path
    target_names: list[str]
    selected_targets: list[str]
    import_failures: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "project_root": str(self.project_root),
            "target_names": self.target_names,
            "selected_targets": self.selected_targets,
            "import_failures": self.import_failures,
        }


def ensure_profile_set_project(
    project_root: Path,
    *,
    extraction_root: Path,
    refresh: bool = False,
    repo_root: Path = PROJECT_ROOT,
) -> ProfileSetProject:
    project_root = project_root.resolve()
    stamp_path = project_root / PROFILE_SET_STAMP_FILE
    if not refresh and stamp_path.exists():
        loaded = _read_profile_set_stamp(stamp_path)
        if loaded is not None:
            _copy_build_runtime_files(loaded.project_root, repo_root=repo_root)
            return loaded
    if project_root.exists():
        _remove_generated_project_root(project_root, repo_root=repo_root)
    return build_profile_set_project(project_root, extraction_root=extraction_root, repo_root=repo_root)


def build_profile_set_project(
    project_root: Path,
    *,
    extraction_root: Path,
    repo_root: Path = PROJECT_ROOT,
) -> ProfileSetProject:
    import_failures: list[str] = []
    project_root = project_root.resolve()
    prepare_reproduction_project_root(project_root, repo_root=repo_root)
    target_names = _copy_existing_binary_targets(project_root, repo_root=repo_root, limit=None)
    target_names.extend(
        _import_resource_disk_targets(
            project_root,
            extraction_root,
            import_failures=import_failures,
            profile_set=True,
            repo_root=repo_root,
        )
    )
    selected_targets = select_profile_targets(target_names)
    result = ProfileSetProject(
        project_root=project_root,
        target_names=target_names,
        selected_targets=selected_targets,
        import_failures=import_failures,
    )
    _write_profile_set_stamp(result)
    return result


def prepare_reproduction_project_root(project_root: Path, *, repo_root: Path = PROJECT_ROOT) -> None:
    _copy_build_runtime_files(project_root, repo_root=repo_root)
    for include_dir in INCLUDE_DIRS:
        source_dir = repo_root / include_dir
        if source_dir.exists():
            shutil.copytree(source_dir, project_root / include_dir, dirs_exist_ok=True)
    (project_root / "targets").mkdir(exist_ok=True)


def _copy_build_runtime_files(project_root: Path, *, repo_root: Path = PROJECT_ROOT) -> None:
    build_dir = project_root / "src" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    for file_name in BUILD_RUNTIME_FILES:
        source = repo_root / "src" / "build" / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing build runtime file: {source}")
        shutil.copy2(source, build_dir / file_name)


def select_profile_targets(
    target_names: Sequence[str],
    *,
    categories: ProfileTargetCategories = PROFILE_TARGET_CATEGORIES,
) -> list[str]:
    selected: list[str] = []
    seen_categories: set[str] = set()
    for target_name in target_names:
        category = profile_target_category(target_name, categories=categories)
        if category is None or category in seen_categories:
            continue
        selected.append(target_name)
        seen_categories.add(category)
    return selected


def profile_target_category(
    target_name: str,
    *,
    categories: ProfileTargetCategories = PROFILE_TARGET_CATEGORIES,
) -> str | None:
    normalized = target_name.lower().replace("_", "-")
    for category, required_tokens in categories:
        if all(token in normalized for token in required_tokens):
            return category
    return None


def _read_profile_set_stamp(stamp_path: Path) -> ProfileSetProject | None:
    try:
        payload = json.loads(stamp_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    project_root = payload.get("project_root")
    target_names = payload.get("target_names")
    selected_targets = payload.get("selected_targets")
    import_failures = payload.get("import_failures")
    if not isinstance(project_root, str):
        return None
    if not isinstance(target_names, list) or not all(isinstance(item, str) for item in target_names):
        return None
    if not isinstance(selected_targets, list) or not all(isinstance(item, str) for item in selected_targets):
        return None
    if not isinstance(import_failures, list) or not all(isinstance(item, str) for item in import_failures):
        return None
    return ProfileSetProject(
        project_root=Path(project_root),
        target_names=list(cast(list[str], target_names)),
        selected_targets=list(cast(list[str], selected_targets)),
        import_failures=list(cast(list[str], import_failures)),
    )


def _write_profile_set_stamp(profile_set: ProfileSetProject) -> None:
    stamp_path = profile_set.project_root / PROFILE_SET_STAMP_FILE
    stamp_path.write_text(json.dumps(profile_set.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _remove_generated_project_root(project_root: Path, *, repo_root: Path) -> None:
    safe_root = (repo_root / "bin" / "rebuilt").resolve()
    resolved = project_root.resolve()
    resolved.relative_to(safe_root)
    shutil.rmtree(resolved)


def _copy_existing_binary_targets(project_root: Path, *, repo_root: Path, limit: int | None) -> list[str]:
    target_names: list[str] = []
    source_paths = sorted((repo_root / "targets").rglob("source_binary.json"))
    for index, source_path in enumerate(source_paths):
        if limit is not None and len(target_names) >= limit:
            break
        source_payload = cast(dict[str, object], json.loads(source_path.read_text(encoding="utf-8")))
        if _source_payload_kind(source_payload) is BinarySourceKind.RAW_BINARY:
            continue
        source_payload = _absolute_source_payload(source_payload, repo_root=repo_root)
        target_name = _integration_target_name("existing", f"{index}-{source_path.parent}")
        target_dir = project_root / "targets" / target_name
        create_project_at_path(f"targets/{target_name}", project_root=project_root)
        write_source_descriptor(target_dir, source_payload)
        for metadata_name in PROFILE_SET_TARGET_METADATA_FILES:
            metadata_path = source_path.parent / metadata_name
            if metadata_path.exists():
                shutil.copy2(metadata_path, target_dir / metadata_name)
        target_names.append(target_name)
    return target_names


def _absolute_source_payload(payload: dict[str, object], *, repo_root: Path) -> dict[str, object]:
    result = dict(payload)
    for key in ("path", "disk_path"):
        value = result.get(key)
        if isinstance(value, str):
            result[key] = str(_resolve_repo_path(value, repo_root=repo_root))
    result.pop("parent_disk_id", None)
    return result


def _resolve_repo_path(value: str, *, repo_root: Path) -> Path:
    path = Path(value)
    if path.exists():
        return path.resolve()
    return (repo_root / value).resolve()


def _import_resource_disk_targets(
    project_root: Path,
    extraction_root: Path,
    *,
    import_failures: list[str],
    profile_set: bool,
    repo_root: Path,
) -> list[str]:
    target_names: list[str] = []
    for disk_path in _resource_disk_images(extraction_root, profile_set=profile_set, repo_root=repo_root):
        imported_targets, failures = _import_resource_disk_path_targets(project_root, disk_path)
        target_names.extend(imported_targets)
        import_failures.extend(failures)
    return target_names


def _resource_disk_images(extraction_root: Path, *, profile_set: bool, repo_root: Path) -> Iterator[Path]:
    extraction_dir = extraction_root / "resource_disks"
    for path in _resource_input_files(profile_set=profile_set, repo_root=repo_root):
        suffix = path.suffix.lower()
        if suffix in {".adf", ".st", ".msa"}:
            yield path
            continue
        yield from _extract_zipped_disk_images(path, extraction_dir)


def _resource_input_files(*, profile_set: bool, repo_root: Path) -> Iterator[Path]:
    resource_dirs = (
        repo_root / "resources" / "platform_amiga",
        repo_root / "resources" / "platform_atari_st",
    )
    for resource_dir in resource_dirs:
        if not resource_dir.exists():
            continue
        for path in sorted(resource_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".adf", ".st", ".msa", ".zip"}:
                continue
            if profile_set and not _is_profile_resource_path(path):
                continue
            yield path


def _is_profile_resource_path(path: Path) -> bool:
    normalized = path.name.lower().replace("_", " ").replace("-", " ")
    return any(pattern in normalized for pattern in PROFILE_RESOURCE_DISK_PATTERNS)


def _extract_zipped_disk_images(zip_path: Path, extraction_dir: Path) -> Iterator[Path]:
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                member_suffix = Path(member.filename).suffix.lower()
                if member_suffix not in {".adf", ".st", ".msa"}:
                    continue
                digest = hashlib.sha1(f"{zip_path}|{member.filename}".encode()).hexdigest()[:12]
                out_path = extraction_dir / f"{digest}_{Path(member.filename).name}"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, out_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
                yield out_path
    except zipfile.BadZipFile:
        return


def _import_resource_disk_path_targets(project_root: Path, disk_path: Path) -> tuple[list[str], list[str]]:
    import_failures: list[str] = []
    suffix = disk_path.suffix.lower()
    if suffix == ".adf":
        return _import_amiga_disk_targets(project_root, disk_path, import_failures), import_failures
    if suffix in {".st", ".msa"}:
        return _import_atari_disk_targets(project_root, disk_path, import_failures), import_failures
    return [], import_failures


def _import_amiga_disk_targets(
    project_root: Path,
    disk_path: Path,
    import_failures: list[str],
) -> list[str]:
    disk_id = _integration_target_name("resource_amiga_disk", str(disk_path))
    try:
        manifest = create_disk_project(disk_path, disk_id=disk_id, project_root=project_root)
    except Exception as exc:
        import_failures.append(f"{disk_path}: Amiga disk import failed: {type(exc).__name__}: {exc}")
        return []
    target_names: list[str] = []
    if manifest.bootblock_target_name:
        target_names.append(manifest.bootblock_target_name)
    target_names.extend(target.target_name for target in manifest.imported_targets)
    return [
        target_name
        for target_name in target_names
        if _target_source_kind(project_root, target_name) is not BinarySourceKind.RAW_BINARY
    ]


def _import_atari_disk_targets(
    project_root: Path,
    disk_path: Path,
    import_failures: list[str],
) -> list[str]:
    try:
        inspection = inspect_disk_with_c_backend(disk_path, project_root=project_root)
    except Exception as exc:
        import_failures.append(f"{disk_path}: Atari disk import failed: {type(exc).__name__}: {exc}")
        return []

    target_names: list[str] = []
    disk_id = _integration_target_name("resource_atari_disk", str(disk_path))
    entries = inspection.get("entries")
    if not isinstance(entries, list):
        return target_names
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if not entry.get("is_executable_candidate"):
            continue
        entry_path = entry.get("path")
        if not isinstance(entry_path, str):
            continue
        if Path(entry_path).suffix.lower() not in {".prg", ".tos", ".ttp"}:
            continue
        target_name = _integration_target_name("resource_atari", f"{disk_path}::{entry_path}")
        target_dir = project_root / "targets" / target_name
        create_project_at_path(f"targets/{target_name}", project_root=project_root)
        write_source_descriptor(
            target_dir,
            {
                "kind": "disk_entry",
                "disk_id": disk_id,
                "disk_path": str(disk_path.resolve()),
                "entry_path": entry_path,
            },
        )
        write_target_metadata(target_dir, _empty_metadata())
        target_names.append(target_name)
    return target_names


def _source_payload_kind(payload: dict[str, object]) -> BinarySourceKind | None:
    kind = payload.get("kind")
    if not isinstance(kind, str):
        return None
    try:
        return BinarySourceKind(kind)
    except ValueError:
        return None


def _target_source_kind(project_root: Path, target_name: str) -> BinarySourceKind | None:
    source_path = project_root / "targets" / target_name / "source_binary.json"
    if not source_path.exists():
        for manifest_path in (project_root / "targets").glob("*/manifest.json"):
            manifest = DiskManifest.load(manifest_path)
            if manifest.bootblock_target_name == target_name:
                source_path = project_root / manifest.bootblock_target_path / "source_binary.json"
                break
            for imported_target in manifest.imported_targets:
                if imported_target.target_name == target_name:
                    source_path = project_root / imported_target.target_path / "source_binary.json"
                    break
    if not source_path.exists():
        return None
    payload = cast(dict[str, object], json.loads(source_path.read_text(encoding="utf-8")))
    return _source_payload_kind(payload)


def _integration_target_name(prefix: str, label: str) -> str:
    stem = normalize_filename_stem(Path(label).stem)[:36]
    digest = hashlib.sha1(label.encode("utf-8")).hexdigest()[:10]
    return str(ensure_safe_project_id(f"{prefix}_{stem}_{digest}"))


def _empty_metadata() -> TargetMetadata:
    return TargetMetadata.from_dict(
        {
            "target_type": "program",
            "entry_register_seeds": [],
            "bootblock": None,
            "resident": None,
            "library": None,
            "custom_structs": [],
            "rsset_layout_regions": [],
            "seeded_entities": [],
            "seeded_code_labels": [],
            "seeded_code_entrypoints": [],
            "absolute_code_labels": [],
            "execution_views": [],
            "suppressed_seeded_items": [],
        }
    )
