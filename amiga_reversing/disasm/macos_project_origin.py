"""Classic Mac OS project origin identifiers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    MacosCodeAddressModel,
    MacosCodeResourceSource,
    macos_code_resource_cache_identity,
)
from amiga_reversing.disasm.macos_asm_container import MPW_ASM_PATH
from amiga_reversing.disasm.project_paths import PROJECT_ROOT

MACOS_CONTAINER_ORIGIN_KIND = "macos_mpw_fixture"
MACOS_CODE_FILE_ORIGIN_KIND = "macos_hfs_resource_code_file"
MACOS_CONTAINER_TARGET_TYPE = "macos_hfs_container"
MACOS_CODE_FILE_TARGET_TYPE = "macos_hfs_resource_code_file"
MACOS_PROJECT_ORIGIN_KIND = MACOS_CONTAINER_ORIGIN_KIND


class MacosProjectLike(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def origin(self) -> dict[str, object]: ...

    @property
    def target_dir(self) -> str: ...


def is_macos_project_origin(origin: Mapping[str, object]) -> bool:
    return origin.get("kind") in {MACOS_CONTAINER_ORIGIN_KIND, MACOS_CODE_FILE_ORIGIN_KIND}


def is_macos_container_origin(origin: Mapping[str, object]) -> bool:
    return origin.get("kind") == MACOS_CONTAINER_ORIGIN_KIND


def is_macos_code_file_origin(origin: Mapping[str, object]) -> bool:
    return origin.get("kind") == MACOS_CODE_FILE_ORIGIN_KIND


def macos_code_source_descriptor_from_project(
    project: MacosProjectLike,
    *,
    project_root: Path = PROJECT_ROOT,
) -> MacosCodeResourceSource:
    origin = project.origin
    if not is_macos_project_origin(origin):
        raise ValueError(f"Project {project.id} is not a Classic Mac OS CODE project")
    source_image = _required_string(origin, "source_image")
    hfs_path = _optional_string(origin, "hfs_path") or MPW_ASM_PATH
    resource_id = _optional_int(origin, "selected_code_resource_id", default=1)
    resource_name = _optional_string(origin, "selected_code_resource_name")
    resolved_image = _resolve_project_path(source_image, project_root)
    return MacosCodeResourceSource(
        kind=BinarySourceKind.MACOS_CODE_RESOURCE,
        source_image=resolved_image,
        hfs_path=hfs_path,
        resource_type="CODE",
        resource_id=resource_id,
        resource_name=resource_name,
        address_model=MacosCodeAddressModel.RESOURCE_OFFSET,
        display_path=f"{source_image}::{hfs_path}::CODE {resource_id}",
        analysis_cache_path=Path(getattr(project, "target_dir", project_root / "targets" / project.id))
        / "binary.analysis",
        cache_identity=macos_code_resource_cache_identity(source_image, hfs_path, "CODE", resource_id),
        parent_project_id=_optional_string(origin, "parent_project_id") or project.id,
        project_root=project_root,
    )


def _required_string(origin: Mapping[str, object], key: str) -> str:
    value = origin.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Mac CODE project origin missing {key}")
    return value


def _optional_string(origin: Mapping[str, object], key: str) -> str | None:
    value = origin.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"Mac CODE project origin has invalid {key}")
    return value


def _optional_int(origin: Mapping[str, object], key: str, *, default: int) -> int:
    value = origin.get(key, default)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Mac CODE project origin has invalid {key}")
    return value


def _resolve_project_path(recorded_path: str, project_root: Path) -> Path:
    candidate = Path(recorded_path)
    if not candidate.exists():
        candidate = project_root / recorded_path
    if not candidate.exists():
        raise FileNotFoundError(f"Mac CODE source image does not exist: {recorded_path}")
    return candidate.resolve()
