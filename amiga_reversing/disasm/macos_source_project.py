"""Source-first Classic Mac OS project model assembly."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from amiga_reversing.disasm.macos_build_provenance import parse_mpw_build_text
from amiga_reversing.disasm.macos_resource_model import (
    build_resource_xrefs,
    parse_resource_constants,
    parse_rez_source,
)
from amiga_reversing.disasm.macos_runtime_metadata import (
    load_generated_mac_os_runtime_metadata,
)
from amiga_reversing.disasm.macos_source_structure import parse_mpw_source_text


def build_macos_source_project(
    *,
    project_id: str,
    source_files: Mapping[str, str],
    resource_files: Mapping[str, str],
    build_files: Mapping[str, str],
    c_header_text: str = "",
    asm_include_text: str = "",
    mac_os_metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build a navigable source-only project model for MPW example sources."""
    constants = parse_resource_constants(c_header_text, asm_include_text)
    constants_by_name = _mapping(constants.get("by_name"))
    parsed_sources = [
        parse_mpw_source_text(text, path=path)
        for path, text in sorted(source_files.items())
        if Path(path).suffix.lower() == ".a"
    ]
    parsed_resources = [
        parse_rez_source(text, path=path, constants=constants_by_name)
        for path, text in sorted(resource_files.items())
    ]
    resources = [
        resource
        for parsed in parsed_resources
        for resource in _mapping_list(parsed.get("resources"))
    ]
    parsed_builds = [parse_mpw_build_text(text, path=path) for path, text in sorted(build_files.items())]
    source_entities = _source_entities(parsed_sources)
    resource_entities = _resource_entities(parsed_resources)
    build_entities = _build_entities(parsed_builds)
    runtime_metadata = mac_os_metadata if mac_os_metadata is not None else load_generated_mac_os_runtime_metadata()
    annotations = _mac_os_annotations(source_entities, runtime_metadata)

    return {
        "schema_version": 1,
        "kind": "macos_source_project",
        "project_id": project_id,
        "platform": "macos",
        "project_model": {
            "kind": "source_first",
            "requires_built_binary": False,
            "requires_rom": False,
            "requires_emulator": False,
            "imports_executable_code_resources": False,
            "maps_source_segments_to_observed_code_resources": False,
        },
        "source_files": parsed_sources,
        "resources": parsed_resources,
        "build_provenance": parsed_builds,
        "resource_xrefs": build_resource_xrefs(source_files, resources, constants_by_name),
        "entities": {
            **source_entities,
            **resource_entities,
            **build_entities,
        },
        "mac_os_annotations": annotations,
        "mac_os_metadata_source": _metadata_source(runtime_metadata),
        "unsupported": [
            "executable CODE resource import",
            "CODE 0 Segment Loader metadata",
            "byte-for-byte MPW Link/Rez roundtrip",
        ],
    }


def _source_entities(parsed_sources: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    files: list[dict[str, object]] = []
    segments: list[dict[str, object]] = []
    routines: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    imports: list[dict[str, object]] = []
    exports: list[dict[str, object]] = []
    for parsed in parsed_sources:
        path = str(parsed.get("path") or "")
        file_id = f"source-file:{path}"
        files.append({"id": file_id, "path": path, "file_name": parsed.get("file_name")})
        segments.extend(_with_entity_ids(path, "segment", parsed.get("segments"), "name"))
        routines.extend(_with_entity_ids(path, "routine", parsed.get("routines"), "name"))
        records.extend(_with_entity_ids(path, "record", parsed.get("records"), "name"))
        imports.extend(_with_entity_ids(path, "import", parsed.get("imports"), "symbol"))
        exports.extend(_with_entity_ids(path, "export", parsed.get("exports"), "symbol"))
    return {
        "source_files": files,
        "segments": segments,
        "routines": routines,
        "records": records,
        "imports": imports,
        "exports": exports,
    }


def _resource_entities(parsed_resources: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    resources: list[dict[str, object]] = []
    for parsed in parsed_resources:
        path = str(parsed.get("path") or "")
        for index, resource in enumerate(_mapping_list(parsed.get("resources"))):
            resource_type = str(resource.get("type") or "")
            id_expr = str(resource.get("id_expression") or resource.get("symbolic_id") or index)
            resources.append({"id": f"resource:{path}:{resource_type}:{id_expr}", **dict(resource)})
    return {"resource_declarations": resources}


def _build_entities(parsed_builds: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    products: list[dict[str, object]] = []
    object_recipes: list[dict[str, object]] = []
    for parsed in parsed_builds:
        path = str(parsed.get("path") or "")
        for product in _mapping_list(parsed.get("products")):
            products.append({"id": f"build-product:{path}:{product.get('target')}", **dict(product)})
        for recipe in _mapping_list(parsed.get("object_recipes")):
            object_recipes.append({"id": f"object-recipe:{path}:{recipe.get('object')}", **dict(recipe)})
    return {"build_products": products, "object_recipes": object_recipes}


def _mac_os_annotations(
    source_entities: dict[str, list[dict[str, object]]],
    mac_os_metadata: Mapping[str, object],
) -> list[dict[str, object]]:
    calls = {str(call.get("name")): call for call in _mapping_list(mac_os_metadata.get("calls"))}
    records = {str(record.get("name")): record for record in _mapping_list(mac_os_metadata.get("records"))}
    annotations: list[dict[str, object]] = []
    for imported in source_entities["imports"]:
        symbol = imported.get("symbol")
        if isinstance(symbol, str) and symbol in calls:
            annotations.append({"kind": "mac_os_call", "entity_id": imported["id"], "name": symbol, "fact": calls[symbol]})
    for record in source_entities["records"]:
        name = record.get("name")
        if isinstance(name, str) and name in records:
            annotations.append({"kind": "mac_os_record", "entity_id": record["id"], "name": name, "fact": records[name]})
    return annotations


def _metadata_source(metadata: Mapping[str, object]) -> dict[str, object]:
    return {
        "kind": metadata.get("kind"),
        "schema_version": metadata.get("schema_version"),
        "generated_path": "src/generated/mac_os_runtime.json",
    }


def _with_entity_ids(
    path: str,
    kind: str,
    values: object,
    name_key: str,
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for index, value in enumerate(_mapping_list(values)):
        name = value.get(name_key, index)
        out.append({"id": f"{kind}:{path}:{name}", **dict(value)})
    return out


def _mapping(value: object) -> Mapping[str, Mapping[str, object]]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items() if isinstance(item, Mapping)}
    return {}


def _mapping_list(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]
