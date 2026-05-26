"""Web payload shape for the Classic Mac OS starter view."""

from __future__ import annotations

from collections.abc import Mapping


def build_macos_starter_web_payload(
    *,
    source_project: Mapping[str, object],
    source_render: Mapping[str, object],
    asm_container: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "macos_starter_view",
        "platform": "macos",
        "source_view": _source_view(source_project, source_render),
        "binary_container_view": _binary_container_view(asm_container),
        "source_binary_boundary": {
            "source_project_kind": source_project.get("kind"),
            "binary_container_kind": asm_container.get("container_kind"),
            "source_segments_map_to_observed_code_resources": False,
            "observed_code_fixture": _mapping(asm_container.get("file")).get("path"),
        },
        "unsupported": sorted(
            {
                *[str(item) for item in _sequence(source_project.get("unsupported"))],
                *[str(item) for item in _sequence(asm_container.get("unsupported"))],
            }
        ),
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


def _binary_container_view(asm_container: Mapping[str, object]) -> dict[str, object]:
    file_info = _mapping(asm_container.get("file"))
    data_fork = _mapping(asm_container.get("data_fork"))
    resource_fork = _mapping(asm_container.get("resource_fork"))
    native_source = _native_source_identity(asm_container)
    resource_placeholders = _executable_resource_placeholders(
        _sequence(resource_fork.get("types")),
        source_image=str(asm_container.get("source_image") or ""),
        hfs_path=str(file_info.get("path") or ""),
    )
    selected = _mapping(asm_container.get("selected_code_segment"))
    selected_with_source = dict(selected)
    if selected_with_source:
        selected_with_source["native_source"] = dict(native_source)
        if _mapping(selected_with_source.get("restored_source")).get("authority") != "c_owned":
            selected_with_source["restored_source"] = {
                "model": "restored_source_missing",
                "status": "blocked",
                "authority": "missing_c_owned_model",
                "reason": "selected CODE restored-source evidence is missing from the C-owned model",
            }
    return {
        "kind": asm_container.get("container_kind"),
        "native_source": native_source,
        "file": file_info,
        "forks": [
            {
                "name": "data",
                "role": data_fork.get("role"),
                "size": data_fork.get("size"),
                "sha256": data_fork.get("sha256"),
            },
            {
                "name": "resource",
                "role": resource_fork.get("role"),
                "size": resource_fork.get("size"),
                "sha256": resource_fork.get("sha256"),
                "types": resource_fork.get("types"),
            },
        ],
        "code0": asm_container.get("code0"),
        "code_resources": _sequence(asm_container.get("code_resources")),
        "selected_code_segment": selected_with_source or asm_container.get("selected_code_segment"),
        "executable_resource_placeholders": resource_placeholders,
        "unsupported": _sequence(asm_container.get("unsupported")),
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


def _executable_resource_placeholders(
    resource_types: list[object],
    *,
    source_image: str,
    hfs_path: str,
) -> list[dict[str, object]]:
    placeholders: list[dict[str, object]] = []
    for value in resource_types:
        item = _mapping(value)
        resource_type = item.get("type")
        if resource_type == "CODE":
            continue
        stable_identity = f"macos-resource:{source_image}:{hfs_path}:{resource_type}:*"
        placeholders.append(
            {
                "kind": "executable_resource_placeholder",
                "resource_type": resource_type,
                "resource_id": None,
                "resource_name": None,
                "resource_count": item.get("count"),
                "byte_size": None,
                "sha256": None,
                "stable_identity": stable_identity,
                "status": "candidate",
                "reason": "non-CODE resource metadata is inventory-only and not executable CODE",
                "provenance": "platform_file_lib.macos_hfs_code_summary resource_fork.types",
                "source_visible": True,
                "source_context": {
                    "status": "unlinked",
                    "stable_identity": stable_identity,
                    "link_kind": "resource_type_inventory",
                    "reason": "No direct CODE routing, fixup, or restored-source reference targets this resource type yet.",
                },
                "reference_sites": [
                    {
                        "kind": "resource_type_inventory",
                        "resource_type": resource_type,
                        "resource_id": None,
                        "stable_identity": stable_identity,
                        "link_status": "unlinked",
                        "source_offset": None,
                        "reason": "No direct CODE routing, fixup, or restored-source reference targets this resource type yet.",
                    }
                ],
            }
        )
    return placeholders


def _native_source_identity(asm_container: Mapping[str, object]) -> dict[str, object]:
    selected = _mapping(asm_container.get("selected_code_segment"))
    resource_id = selected.get("id", 1)
    source_image = str(asm_container.get("source_image") or "")
    hfs_path = str(_mapping(asm_container.get("file")).get("path") or "")
    return {
        "kind": "macos_code_resource",
        "backend": "macos-code",
        "source_kind": "macos_code_resource",
        "source_image": source_image,
        "hfs_path": hfs_path,
        "resource_type": "CODE",
        "resource_id": resource_id,
        "resource_name": selected.get("name"),
        "address_model": "macos_code_resource_offset",
        "cache_identity": f"macos-code-resource:{source_image}:{hfs_path}:CODE:{resource_id}",
        "wrapped_backend": None,
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
