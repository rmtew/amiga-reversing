"""Normal project/API payload assembly for Classic Mac OS projects."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from amiga_reversing.disasm.c_backend import (
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import (
    MPW_ASM_PATH,
    read_macos_hfs_image_bytes,
)
from amiga_reversing.disasm.macos_project_origin import is_macos_project_origin
from amiga_reversing.disasm.macos_source_project import build_macos_source_project
from amiga_reversing.disasm.macos_source_render import render_macos_source_views
from amiga_reversing.disasm.project_paths import PROJECT_ROOT


def build_macos_project_payload(project: object, *, project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    origin = _mapping(getattr(project, "origin", {}))
    if not is_macos_project_origin(origin):
        raise ValueError("Mac OS project payload requires macos_mpw_fixture origin")
    project_id = str(getattr(project, "id", ""))
    source_files = _read_text_files(project_root, origin.get("source_files"))
    resource_files = _read_text_files(project_root, origin.get("resource_files"))
    build_files = _read_text_files(project_root, origin.get("build_files"))
    source_project = build_macos_source_project(
        project_id=project_id,
        source_files=source_files,
        resource_files=resource_files,
        build_files=build_files,
        c_header_text=_join_text_files(project_root, origin.get("c_header_files")),
        asm_include_text=_join_text_files(project_root, origin.get("asm_include_files")),
    )
    source_render = render_macos_source_views(source_project)
    image_relpath = _required_string(origin, "source_image")
    hfs_path = str(origin.get("hfs_path") or MPW_ASM_PATH)
    hfs_bytes = read_macos_hfs_image_bytes(project_root / image_relpath)
    c_summary = inspect_macos_hfs_code_summary_with_c_backend(hfs_bytes, hfs_path)
    return {
        "schema_version": 1,
        "kind": "macos_project",
        "platform": "macos",
        "source_view": _source_view(source_project, source_render),
        "binary_container_view": _binary_container_view(c_summary),
        "source_binary_boundary": {
            "source_project_kind": source_project.get("kind"),
            "binary_container_kind": c_summary.get("container_kind"),
            "source_segments_map_to_observed_code_resources": False,
            "observed_code_fixture": _mapping(c_summary.get("file")).get("path"),
        },
        "unsupported": sorted(
            {
                *[str(item) for item in _sequence(source_project.get("unsupported"))],
                *[str(item) for item in _sequence(c_summary.get("unsupported"))],
            }
        ),
        "provenance": {
            "origin_kind": origin.get("kind"),
            "source_image": image_relpath,
            "hfs_path": hfs_path,
            "source_files": _string_list(origin.get("source_files")),
            "resource_files": _string_list(origin.get("resource_files")),
            "build_files": _string_list(origin.get("build_files")),
            "binary_container_source": "platform_file_lib.macos_hfs_code_summary",
        },
    }


def _source_view(source_project: Mapping[str, object], source_render: Mapping[str, object]) -> dict[str, object]:
    entities = _mapping(source_project.get("entities"))
    return {
        "kind": source_project.get("kind"),
        "project_model": source_project.get("project_model"),
        "pivots": {
            "source_files": _sequence(entities.get("source_files")),
            "segments": _sequence(entities.get("segments")),
            "routines": _sequence(entities.get("routines")),
            "resources": _sequence(entities.get("resource_declarations")),
            "build_products": _sequence(entities.get("build_products")),
            "api_facts": _sequence(source_project.get("mac_os_annotations")),
        },
        "routine_views": _sequence(source_render.get("routine_views")),
        "product_views": _sequence(source_render.get("product_views")),
        "unsupported": _sequence(source_project.get("unsupported")),
    }


def _binary_container_view(c_summary: Mapping[str, object]) -> dict[str, object]:
    file_info = _mapping(c_summary.get("file"))
    forks = _mapping(file_info.get("forks"))
    data_fork = _mapping(forks.get("data"))
    resource_fork = _mapping(forks.get("resource"))
    resource_summary = _mapping(c_summary.get("resource_fork"))
    code_resources = _sequence(resource_summary.get("code_resources"))
    code0 = _code_resource_by_id(code_resources, 0)
    selected = _mapping(c_summary.get("selected_code"))
    return {
        "kind": c_summary.get("container_kind"),
        "file": file_info,
        "forks": [
            {"name": "data", "role": "data_fork", "size": data_fork.get("size"), "sha256": data_fork.get("sha256")},
            {
                "name": "resource",
                "role": "executable_resource_fork",
                "size": resource_fork.get("size"),
                "sha256": resource_fork.get("sha256"),
                "types": resource_summary.get("types"),
            },
        ],
        "code0": {"resource": code0, "metadata": _mapping(code0.get("code"))},
        "code_resources": code_resources,
        "selected_code_segment": {
            "resource_type": "CODE",
            "id": selected.get("id", 1),
            "available": selected.get("available"),
            "payload_size": selected.get("payload_size"),
            "code_bytes_size": selected.get("code_bytes_size"),
            "sha256": selected.get("payload_sha256"),
            "code_bytes_sha256": selected.get("code_bytes_sha256"),
        },
        "unsupported": _sequence(c_summary.get("unsupported")),
        "source_mapping": {
            "maps_to_sample_source": False,
            "reason": "observed MPW/Tools/Asm CODE resources are not inferred from Sample source segments",
        },
        "finder": {
            "type": file_info.get("type"),
            "creator": file_info.get("creator"),
            "cnid": file_info.get("cnid"),
        },
    }


def _code_resource_by_id(resources: list[object], resource_id: int) -> Mapping[str, object]:
    for resource in resources:
        mapping = _mapping(resource)
        if mapping.get("id") == resource_id:
            return mapping
    return {}


def _read_text_files(project_root: Path, value: object) -> dict[str, str]:
    return {path: _read_text(project_root / path) for path in _string_list(value)}


def _join_text_files(project_root: Path, value: object) -> str:
    return "\n".join(_read_text(project_root / path) for path in _string_list(value))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="mac_roman")


def _required_string(origin: Mapping[str, object], key: str) -> str:
    value = origin.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Mac OS project origin missing {key}")
    return value


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, str)]
