"""Structured smoke renderer for Classic Mac OS source projects."""

from __future__ import annotations

from collections.abc import Mapping


def render_macos_source_views(project: Mapping[str, object]) -> dict[str, object]:
    entities = _mapping(project.get("entities"))
    annotations = _annotations_by_entity(project.get("mac_os_annotations"))
    resource_xrefs = _mapping_list(project.get("resource_xrefs"))
    routine_views = [
        _routine_view(routine, entities, annotations, resource_xrefs, project)
        for routine in _mapping_list(entities.get("routines"))
    ]
    return {
        "schema_version": 1,
        "kind": "classic_macos_source_render_smoke",
        "project_id": project.get("project_id"),
        "routine_views": routine_views,
        "product_views": _product_views(entities),
        "unsupported": _sequence(project.get("unsupported")),
    }


def _routine_view(
    routine: Mapping[str, object],
    entities: Mapping[str, object],
    annotations: Mapping[str, list[Mapping[str, object]]],
    resource_xrefs: list[Mapping[str, object]],
    project: Mapping[str, object],
) -> dict[str, object]:
    path = str(routine.get("source") or _entity_path(routine.get("id")))
    line = _int_or_none(routine.get("line"))
    line_end = _int_or_none(routine.get("line_end"))
    imports = _routine_entities(entities.get("imports"), path, routine.get("name"))
    records = _routine_entities(entities.get("records"), path, routine.get("name"))
    exports = _routine_entities(entities.get("exports"), path, routine.get("name"))
    api_calls = [_annotation_summary(annotation) for entity in imports for annotation in annotations.get(str(entity.get("id")), [])]
    record_facts = [
        _annotation_summary(annotation)
        for entity in records
        for annotation in annotations.get(str(entity.get("id")), [])
    ]
    xrefs = [
        dict(xref)
        for xref in resource_xrefs
        if (
            xref.get("source") == path
            and _line_in_range(_int_or_none(xref.get("line")), line, line_end)
        )
        or xref.get("call") == routine.get("name")
    ]
    return {
        "id": routine.get("id"),
        "name": routine.get("name"),
        "file": path,
        "segment": routine.get("segment"),
        "kind": routine.get("kind"),
        "line": line,
        "line_end": line_end,
        "imports": [_symbol(entity) for entity in imports],
        "exports": [_symbol(entity) for entity in exports],
        "records": [_symbol(entity, key="name") for entity in records],
        "api_calls": api_calls,
        "record_facts": record_facts,
        "resource_xrefs": xrefs,
        "intent_hints": _intent_hints(api_calls, record_facts),
        "unknown_imports": _unknown_imports(imports, annotations),
        "source_project_only": _mapping(project.get("project_model")).get("imports_executable_code_resources") is False,
    }


def _product_views(entities: Mapping[str, object]) -> list[dict[str, object]]:
    resources = _mapping_list(entities.get("resource_declarations"))
    products: list[dict[str, object]] = []
    for product in _mapping_list(entities.get("build_products")):
        link: Mapping[str, object] = _mapping(product.get("link"))
        setfile: Mapping[str, object] = _mapping(product.get("setfile"))
        rez_inputs = [
            resource
            for rez in _mapping_list(product.get("rez"))
            for resource in _sequence(rez.get("resource_inputs"))
        ]
        products.append(
            {
                "target": product.get("target"),
                "program_kind": link.get("program_kind"),
                "file_type": setfile.get("file_type") or link.get("output_type"),
                "creator": setfile.get("creator") or link.get("output_creator"),
                "object_inputs": _sequence(link.get("object_inputs")),
                "library_inputs": _sequence(link.get("library_inputs")),
                "resource_inputs": rez_inputs,
                "resource_types": sorted({str(resource.get("type")) for resource in resources if resource.get("type")}),
                "byte_for_byte_roundtrip": product.get("byte_for_byte_roundtrip"),
            }
        )
    return products


def _annotation_summary(annotation: Mapping[str, object]) -> dict[str, object]:
    fact = _mapping(annotation.get("fact"))
    summary: dict[str, object] = {"kind": annotation.get("kind"), "name": annotation.get("name")}
    for key in ("opword", "package_word", "family", "parameter_register", "result_register", "size", "source", "line"):
        if key in fact:
            summary[key] = fact[key]
    return summary


def _intent_hints(api_calls: list[dict[str, object]], record_facts: list[dict[str, object]]) -> list[str]:
    call_names = {str(call.get("name")) for call in api_calls}
    record_names = {str(record.get("name")) for record in record_facts}
    hints: list[str] = []
    if "_GetResource" in call_names:
        hints.append("resource_lookup")
    if "_PBHGetVInfoSync" in call_names and "HVolumeParam" in record_names:
        hints.append("volume_free_space_query")
    return hints


def _routine_entities(values: object, path: str, routine_name: object) -> list[Mapping[str, object]]:
    out: list[Mapping[str, object]] = []
    for entity in _mapping_list(values):
        entity_path = _entity_path(entity.get("id"))
        if entity_path != path:
            continue
        routine = entity.get("routine")
        if routine is None or routine == routine_name:
            out.append(entity)
    return out


def _unknown_imports(
    imports: list[Mapping[str, object]],
    annotations: Mapping[str, list[Mapping[str, object]]],
) -> list[str]:
    return [str(entity.get("symbol")) for entity in imports if not annotations.get(str(entity.get("id")))]


def _annotations_by_entity(value: object) -> dict[str, list[Mapping[str, object]]]:
    out: dict[str, list[Mapping[str, object]]] = {}
    for annotation in _mapping_list(value):
        entity_id = annotation.get("entity_id")
        if isinstance(entity_id, str):
            out.setdefault(entity_id, []).append(annotation)
    return out


def _entity_path(entity_id: object) -> str:
    if not isinstance(entity_id, str):
        return ""
    parts = entity_id.split(":", 2)
    return parts[1] if len(parts) >= 3 else ""


def _symbol(entity: Mapping[str, object], *, key: str = "symbol") -> str:
    value = entity.get(key)
    return str(value) if value is not None else ""


def _line_in_range(line: int | None, start: int | None, end: int | None) -> bool:
    if line is None or start is None or end is None:
        return False
    return start <= line <= end


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None
