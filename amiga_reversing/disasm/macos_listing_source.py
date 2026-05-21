"""Listing source adapter for selected Classic Mac OS CODE resources."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    CListingArtifact,
    build_listing_artifact_profile_from_binary_source,
    extract_macos_hfs_code_resource_bytes_with_c_backend,
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import (
    MPW_ASM_PATH,
    read_macos_hfs_image_bytes,
)
from amiga_reversing.disasm.macos_project_origin import is_macos_project_origin
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import ProjectRecord


def build_macos_project_listing_artifact_profile(
    project: ProjectRecord,
    *,
    project_root: Path = PROJECT_ROOT,
) -> tuple[int, dict[str, object], CListingArtifact]:
    listing_source = build_macos_code_listing_source(project, project_root=project_root)
    with _temporary_code_binary_source(listing_source, project_root=project_root) as binary_source:
        return build_listing_artifact_profile_from_binary_source(binary_source, project_root=project_root)


def build_macos_code_listing_source(
    project: ProjectRecord,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    origin = _macos_origin(project)
    image_relpath = _required_string(origin, "source_image")
    hfs_path = str(origin.get("hfs_path") or MPW_ASM_PATH)
    resource_id = _selected_resource_id(origin)
    hfs_bytes = read_macos_hfs_image_bytes(project_root / image_relpath)
    summary = inspect_macos_hfs_code_summary_with_c_backend(hfs_bytes, hfs_path)
    code_bytes = extract_macos_hfs_code_resource_bytes_with_c_backend(hfs_bytes, hfs_path, resource_id)
    if not code_bytes:
        raise ValueError(f"Mac OS project {project.id} selected CODE {resource_id} has no code bytes")
    selected_code = _mapping(summary.get("selected_code"))
    resource = _code_resource_by_id(_sequence(_mapping(summary.get("resource_fork")).get("code_resources")), resource_id)
    file_info = _mapping(summary.get("file"))
    return {
        "project_id": project.id,
        "platform": "macos",
        "source_image": image_relpath,
        "hfs_path": hfs_path,
        "fork": "resource",
        "resource_type": "CODE",
        "resource_id": resource_id,
        "resource_name": resource.get("name") or selected_code.get("name"),
        "resource": resource,
        "selected_code": selected_code,
        "code_bytes": code_bytes,
        "display_path": f"{hfs_path} CODE {resource_id} {resource.get('name') or selected_code.get('name') or ''}".strip(),
        "container": {
            "kind": summary.get("container_kind"),
            "file_type": file_info.get("type"),
            "creator": file_info.get("creator"),
            "cnid": file_info.get("cnid"),
        },
        "unsupported": _sequence(summary.get("unsupported")),
    }


def macos_listing_cache_key(project: ProjectRecord, *, project_root: Path = PROJECT_ROOT) -> str:
    origin = _macos_origin(project)
    image_relpath = _required_string(origin, "source_image")
    hfs_path = str(origin.get("hfs_path") or MPW_ASM_PATH)
    resource_id = _selected_resource_id(origin)
    target_dir = project_root / project.target_dir
    return "|".join(
        [
            project.id,
            "macos-code-resource",
            image_relpath,
            _file_cache_stamp(project_root / image_relpath),
            hfs_path,
            f"CODE:{resource_id}",
            _file_cache_stamp(target_dir / ".project.json"),
        ]
    )


@contextmanager
def _temporary_code_binary_source(
    listing_source: Mapping[str, object],
    *,
    project_root: Path,
) -> Iterator[RawBinarySource]:
    code_bytes = listing_source.get("code_bytes")
    if not isinstance(code_bytes, bytes):
        raise TypeError("Mac CODE listing source requires code_bytes")
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".macos-code.bin") as temp_file:
            temp_file.write(code_bytes)
            temp_path = Path(temp_file.name)
        yield RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=temp_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(listing_source.get("display_path") or "Mac OS CODE resource"),
            analysis_cache_path=project_root / "targets" / ".macos-code.analysis",
        )
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _macos_origin(project: ProjectRecord) -> Mapping[str, object]:
    origin = project.origin
    if not is_macos_project_origin(origin):
        raise ValueError("Mac OS listing requires macos_mpw_fixture origin")
    return origin


def _selected_resource_id(origin: Mapping[str, object]) -> int:
    value = origin.get("selected_code_resource_id", 1)
    return value if isinstance(value, int) and value > 0 else 1


def _required_string(origin: Mapping[str, object], key: str) -> str:
    value = origin.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Mac OS project origin missing {key}")
    return value


def _code_resource_by_id(resources: list[object], resource_id: int) -> Mapping[str, object]:
    for resource in resources:
        mapping = _mapping(resource)
        if mapping.get("id") == resource_id:
            return mapping
    return {}


def _file_cache_stamp(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError:
        return f"{path}:missing"
    return f"{path}:{stat.st_size}:{stat.st_mtime_ns}"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
