"""Classic Mac OS HFS container browser payloads."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from amiga_reversing.disasm.binary_source import write_source_descriptor
from amiga_reversing.disasm.macos_hfs import HFSFileRecord, HFSVolume
from amiga_reversing.disasm.macos_image import read_macos_hfs_image_bytes
from amiga_reversing.disasm.macos_project_origin import (
    MACOS_CODE_FILE_ORIGIN_KIND,
    MACOS_CODE_FILE_TARGET_TYPE,
    MACOS_CONTAINER_ORIGIN_KIND,
)
from amiga_reversing.disasm.macos_resource_fork import parse_resource_fork
from amiga_reversing.disasm.project_ids import ensure_safe_project_id
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import (
    initialize_project_metadata,
    mark_project_updated,
)


def build_macos_container_payload(project: object, *, project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    origin = _mapping(getattr(project, "origin", {}))
    if origin.get("kind") != MACOS_CONTAINER_ORIGIN_KIND:
        raise ValueError("Mac OS container payload requires macos_mpw_fixture origin")
    source_image = _required_string(origin, "source_image")
    image_bytes = read_macos_hfs_image_bytes(project_root / source_image)
    volume = HFSVolume(image_bytes)
    parent_project_id = str(getattr(project, "id", ""))
    target_dir = Path(str(getattr(project, "target_dir", project_root / "targets" / parent_project_id)))
    imported_targets = _imported_targets(parent_project_id, target_dir)
    imported_by_path = {
        str(item["hfs_path"]): str(item["target_id"])
        for item in imported_targets
        if isinstance(item.get("hfs_path"), str) and isinstance(item.get("target_id"), str)
    }
    files = [
        _file_payload(volume, file_record, imported_by_path=imported_by_path)
        for file_record in sorted(volume.files, key=lambda item: item.path)
    ]
    return {
        "schema_version": 1,
        "kind": "macos_hfs_container",
        "platform": "macos",
        "image_path": source_image,
        "volume_name": volume.volume_name,
        "files": files,
        "imported_targets": imported_targets,
    }


def macos_local_target_id_for_hfs_path(hfs_path: str) -> str:
    parts = [part for part in hfs_path.replace("\\", "/").split("/") if part]
    if len(parts) > 1:
        parts = parts[1:]
    stem = "_".join(_safe_component(part) for part in parts) or "file"
    safe_id: str = ensure_safe_project_id(f"macos_file_{stem}")
    return safe_id


def import_macos_resource_code_file(
    project: object,
    *,
    hfs_path: str,
    selected_code_resource_id: int = 1,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    origin = _mapping(getattr(project, "origin", {}))
    if origin.get("kind") != MACOS_CONTAINER_ORIGIN_KIND:
        raise ValueError("Mac CODE import requires a Mac HFS container project")
    source_image = _required_string(origin, "source_image")
    parent_project_id = str(getattr(project, "id", ""))
    parent_dir = Path(str(getattr(project, "target_dir", project_root / "targets" / parent_project_id)))
    image_bytes = read_macos_hfs_image_bytes(project_root / source_image)
    volume = HFSVolume(image_bytes)
    file_record = volume.find_file(hfs_path)
    if file_record.resource_size <= 0:
        raise ValueError(f"HFS file has no resource fork: {hfs_path}")
    resource_inventory = parse_resource_fork(volume.resource_fork(file_record), hfs_path)
    code_resources = [
        resource for resource in resource_inventory.get("resources", []) if resource.get("type") == "CODE"
    ]
    if not code_resources:
        raise ValueError(f"HFS file has no CODE resources: {hfs_path}")
    selected_resource = _selected_code_resource(code_resources, selected_code_resource_id)
    local_target_id = macos_local_target_id_for_hfs_path(hfs_path)
    target_id = f"{parent_project_id}__{local_target_id}"
    child_dir = parent_dir / "targets" / local_target_id
    status = "existing" if child_dir.exists() else "imported"
    child_dir.mkdir(parents=True, exist_ok=True)
    child_origin = {
        "kind": MACOS_CODE_FILE_ORIGIN_KIND,
        "parent_project_id": parent_project_id,
        "source_image": source_image,
        "hfs_path": hfs_path,
        "resource_type": "CODE",
        "selected_code_resource_id": selected_code_resource_id,
        "selected_code_resource_name": selected_resource.get("name"),
        "finder_type": file_record.file_type,
        "creator": file_record.creator,
        "renderer": "amiga_reversing.disasm.macos_target_artifact",
        "artifact": "asm.s",
    }
    if not (child_dir / ".project.json").exists():
        initialize_project_metadata(child_dir, origin=child_origin)
    write_source_descriptor(
        child_dir,
        {
            "kind": "macos_code_resource",
            "source_image": source_image,
            "hfs_path": hfs_path,
            "resource_type": "CODE",
            "resource_id": selected_code_resource_id,
            "resource_name": selected_resource.get("name"),
            "address_model": "macos_code_resource_offset",
            "parent_project_id": parent_project_id,
        },
    )
    (child_dir / "macos_resource_inventory.json").write_text(
        json.dumps(resource_inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    mark_project_updated(parent_dir)
    return {
        "status": status,
        "target_id": target_id,
        "target_path": str(child_dir),
        "hfs_path": hfs_path,
        "selected_code_resource_id": selected_code_resource_id,
    }


def _file_payload(
    volume: HFSVolume,
    file_record: HFSFileRecord,
    *,
    imported_by_path: Mapping[str, str],
) -> dict[str, object]:
    resource_fork = _resource_fork_payload(volume, file_record)
    supported_imports: list[str] = []
    resources = resource_fork.get("resources")
    resource_rows = resources if isinstance(resources, list) else []
    if any(_mapping(item).get("type") == "CODE" for item in resource_rows):
        supported_imports.append(MACOS_CODE_FILE_TARGET_TYPE)
    payload = {
        "path": file_record.path,
        "name": file_record.name,
        "cnid": file_record.cnid,
        "finder_type": file_record.file_type,
        "creator": file_record.creator,
        "data_fork_size": file_record.data_size,
        "resource_fork_size": file_record.resource_size,
        "supported_imports": supported_imports,
        "resource_fork": resource_fork,
    }
    target_id = imported_by_path.get(file_record.path)
    if target_id is not None:
        payload["imported_target_id"] = target_id
    return payload


def _resource_fork_payload(volume: HFSVolume, file_record: HFSFileRecord) -> dict[str, object]:
    if file_record.resource_size <= 0:
        return {"status": "absent", "types": [], "resources": []}
    try:
        resource_bytes = volume.resource_fork(file_record)
        inventory = parse_resource_fork(resource_bytes, file_record.path)
    except (KeyError, ValueError) as exc:
        return {"status": "unparseable", "error": str(exc), "types": [], "resources": []}
    return {
        "status": "parseable",
        "types": inventory.get("types", []),
        "resources": inventory.get("resources", []),
    }


def _selected_code_resource(
    code_resources: list[object],
    selected_code_resource_id: int,
) -> Mapping[str, object]:
    for resource in code_resources:
        item = _mapping(resource)
        if item.get("id") == selected_code_resource_id:
            return item
    raise ValueError(f"CODE resource {selected_code_resource_id} is not present")


def _imported_targets(parent_project_id: str, target_dir: Path) -> list[dict[str, object]]:
    targets_dir = target_dir / "targets"
    if not targets_dir.exists():
        return []
    imported: list[dict[str, object]] = []
    for child_dir in sorted(targets_dir.iterdir(), key=lambda item: item.name):
        if not child_dir.is_dir() or child_dir.name.startswith("."):
            continue
        metadata_path = child_dir / ".project.json"
        try:
            with open(metadata_path, encoding="utf-8") as handle:
                metadata = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        origin = _mapping(_mapping(metadata).get("origin"))
        if origin.get("kind") != MACOS_CODE_FILE_ORIGIN_KIND:
            continue
        imported.append(
            {
                "target_id": f"{parent_project_id}__{child_dir.name}",
                "local_target_id": child_dir.name,
                "target_path": str(child_dir),
                "hfs_path": origin.get("hfs_path"),
                "target_type": MACOS_CODE_FILE_TARGET_TYPE,
                "resource_type": origin.get("resource_type", "CODE"),
                "selected_code_resource_id": origin.get("selected_code_resource_id"),
                "selected_code_resource_name": origin.get("selected_code_resource_name"),
            }
        )
    return imported


def _safe_component(component: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in component).strip("_") or "item"


def _required_string(origin: Mapping[str, object], key: str) -> str:
    value = origin.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Mac container origin missing {key}")
    return value


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
