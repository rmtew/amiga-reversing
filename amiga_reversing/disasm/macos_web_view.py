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
        "kind": "classic_macos_starter_view",
        "platform": "classic_macos",
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
    return {
        "kind": asm_container.get("container_kind"),
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
        "selected_code_segment": asm_container.get("selected_code_segment"),
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


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
