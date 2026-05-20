"""Classic Mac OS HFS fork role classification."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

INVENTORY_EVIDENCE = "ext/macos_includes/mpw_gm/inventory.json"
AEXAMPLES_EVIDENCE = "docs/macos-initial-analysis-research.md:276-290"
ASM_EVIDENCE = "docs/macos-initial-analysis-research.md:294-309"
OBJECT_EVIDENCE = "docs/macos-initial-analysis-research.md:311-321"
ASM_CODE_RESOURCE_EVIDENCE = "ext/macos_tools/mpw_gm/asm_code_resources.json"


def resource_type_counts(resource_fork_summary: Mapping[str, object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for resource_type in _typed_list(resource_fork_summary.get("types"), "types"):
        type_name = _typed_str(resource_type.get("type"), "type")
        count = _typed_int(resource_type.get("count"), "count")
        counts[type_name] = count
    return counts


def classify_inventory_items(
    items: Iterable[Mapping[str, object]],
    *,
    selected_paths: Iterable[str] | None = None,
    resource_type_counts_by_path: Mapping[str, Mapping[str, int]] | None = None,
) -> list[dict[str, object]]:
    selected = set(selected_paths) if selected_paths is not None else None
    resource_counts = resource_type_counts_by_path or {}
    out: list[dict[str, object]] = []
    for item in items:
        path = _typed_str(item.get("path"), "path")
        if selected is not None and path not in selected:
            continue
        out.append(
            classify_inventory_item(
                item,
                resource_type_counts=resource_counts.get(path),
            )
        )
    return out


def classify_inventory_item(
    item: Mapping[str, object],
    *,
    resource_type_counts: Mapping[str, int] | None = None,
) -> dict[str, object]:
    path = _typed_str(item.get("path"), "path")
    file_type = _typed_str(item.get("type"), "type")
    creator = _typed_str(item.get("creator"), "creator")
    data_size = _typed_int(item.get("data_size"), "data_size")
    resource_size = _typed_int(item.get("resource_size"), "resource_size")
    counts = resource_type_counts or {}

    return {
        "path": path,
        "cnid": _typed_int(item.get("cnid"), "cnid"),
        "type": file_type,
        "creator": creator,
        "data_size": data_size,
        "resource_size": resource_size,
        "fork_roles": {
            "data": _classify_data_fork(path, file_type, creator, data_size),
            "resource": _classify_resource_fork(path, file_type, creator, resource_size, counts),
        },
    }


def _classify_data_fork(path: str, file_type: str, creator: str, size: int) -> dict[str, object]:
    if size == 0:
        return _role("absent", INVENTORY_EVIDENCE)
    if _is_aexamples_source(path, file_type, creator):
        return _role("source_text", INVENTORY_EVIDENCE, AEXAMPLES_EVIDENCE)
    if _is_mpw_asm(path, file_type, creator):
        return _role("data_string_payload", INVENTORY_EVIDENCE, ASM_EVIDENCE)
    if file_type == "OBJ ":
        return _role("object_payload", INVENTORY_EVIDENCE, OBJECT_EVIDENCE)
    return _role("unknown", INVENTORY_EVIDENCE)


def _classify_resource_fork(
    path: str,
    file_type: str,
    creator: str,
    size: int,
    resource_type_counts: Mapping[str, int],
) -> dict[str, object]:
    if size == 0:
        return _role("absent", INVENTORY_EVIDENCE)
    if _is_aexamples_source(path, file_type, creator) and size == 430:
        return _role("editor_metadata", INVENTORY_EVIDENCE, AEXAMPLES_EVIDENCE, resource_types={"MPSR": 2})
    if _is_mpw_asm(path, file_type, creator):
        code_count = resource_type_counts.get("CODE")
        if code_count is not None:
            return _role(
                "executable_resource_fork",
                INVENTORY_EVIDENCE,
                ASM_EVIDENCE,
                ASM_CODE_RESOURCE_EVIDENCE,
                resource_types={"CODE": code_count},
            )
        return _role("executable_resource_fork", INVENTORY_EVIDENCE, ASM_EVIDENCE)
    return _role("unknown", INVENTORY_EVIDENCE)


def _is_aexamples_source(path: str, file_type: str, creator: str) -> bool:
    return file_type == "TEXT" and creator == "MPS " and "/MPW/Examples/AExamples/" in f"/{path}/"


def _is_mpw_asm(path: str, file_type: str, creator: str) -> bool:
    return file_type == "MPST" and creator == "MPS " and path.endswith("/MPW/Tools/Asm")


def _role(role: str, *evidence: str, resource_types: Mapping[str, int] | None = None) -> dict[str, object]:
    value: dict[str, object] = {"role": role, "evidence": list(evidence)}
    if resource_types is not None:
        value["resource_types"] = dict(resource_types)
    return value


def _typed_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _typed_int(value: object, field: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _typed_list(value: object, field: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    out: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field} entries must be objects")
        out.append(item)
    return out
