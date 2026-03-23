from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from disasm.project_paths import PROJECT_ROOT
from disasm.types import EntityRecord

EDITABLE_FIELDS = {"name", "comment", "type", "subtype", "confidence"}
TYPE_VALUES = {"code", "data", "bss", "unknown"}
SUBTYPE_VALUES = {
    "string",
    "pointer_table",
    "struct_instance",
    "lookup_table",
    "sprite",
    "bitmap",
    "palette",
    "copper_list",
    "tilemap",
    "sound_sample",
    "level_data",
}
CONFIDENCE_VALUES = {"tool-inferred", "llm-guessed", "verified"}


@dataclass(slots=True)
class AnnotationPatch:
    name: str | None = None
    comment: str | None = None
    type: str | None = None
    subtype: str | None = None
    confidence: str | None = None

    @classmethod
    def from_raw(cls, raw: dict[object, object]) -> AnnotationPatch:
        patch = cls()
        for field_name in EDITABLE_FIELDS:
            value = raw.get(field_name)
            if value is not None:
                assert isinstance(value, str), f"override {field_name} must be a string"
                setattr(patch, field_name, value)
        return patch

    def to_raw(self) -> dict[str, str]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(slots=True)
class OverridesPayload:
    entities: dict[str, AnnotationPatch]


class AnnotationPatchInput(dict[str, str | None]):
    pass


def _annotation_patch_from_input(patch: AnnotationPatch | AnnotationPatchInput) -> AnnotationPatch:
    if isinstance(patch, AnnotationPatch):
        return patch
    invalid = set(patch) - EDITABLE_FIELDS
    if invalid:
        raise ValueError(f"Unsupported annotation fields: {sorted(invalid)}")
    return AnnotationPatch(**patch)


def _overrides_path(target_dir: Path) -> Path:
    return target_dir / "overrides.json"


def _require_str_field(raw: dict[object, object], field_name: str, *, what: str) -> str:
    value = raw.get(field_name)
    assert isinstance(value, str), f"{what} {field_name} must be a string"
    return value


def _optional_field[T](raw: dict[object, object], field_name: str,
                       expected_type: type[T], *, what: str) -> T | None:
    value = raw.get(field_name)
    if value is None:
        return None
    assert isinstance(value, expected_type), (
        f"{what} {field_name} must be a {expected_type.__name__}")
    return value


def _entity_from_raw(raw: dict[object, object]) -> EntityRecord:
    entity: EntityRecord = {
        "addr": _require_str_field(raw, "addr", what="entity"),
        "type": _require_str_field(raw, "type", what="entity"),
    }
    end = _optional_field(raw, "end", str, what="entity")
    hunk = _optional_field(raw, "hunk", int, what="entity")
    name = _optional_field(raw, "name", str, what="entity")
    comment = _optional_field(raw, "comment", str, what="entity")
    subtype = _optional_field(raw, "subtype", str, what="entity")
    confidence = _optional_field(raw, "confidence", str, what="entity")
    if end is not None:
        entity["end"] = end
    if hunk is not None:
        entity["hunk"] = hunk
    if name is not None:
        entity["name"] = name
    if comment is not None:
        entity["comment"] = comment
    if subtype is not None:
        entity["subtype"] = subtype
    if confidence is not None:
        entity["confidence"] = confidence
    return entity


def _copy_entity(entity: EntityRecord) -> EntityRecord:
    copied: EntityRecord = {"addr": entity["addr"], "type": entity["type"]}
    if "end" in entity:
        copied["end"] = entity["end"]
    if "hunk" in entity:
        copied["hunk"] = entity["hunk"]
    if "name" in entity:
        copied["name"] = entity["name"]
    if "comment" in entity:
        copied["comment"] = entity["comment"]
    if "subtype" in entity:
        copied["subtype"] = entity["subtype"]
    if "confidence" in entity:
        copied["confidence"] = entity["confidence"]
    return copied


def _apply_patch(entity: EntityRecord, patch: AnnotationPatch) -> None:
    if patch.name is not None:
        entity["name"] = patch.name
    if patch.comment is not None:
        entity["comment"] = patch.comment
    if patch.type is not None:
        entity["type"] = patch.type
    if patch.subtype is not None:
        entity["subtype"] = patch.subtype
    if patch.confidence is not None:
        entity["confidence"] = patch.confidence


def _apply_patch_update(target: AnnotationPatch, patch: AnnotationPatch) -> None:
    if patch.name is not None:
        target.name = patch.name
    if patch.comment is not None:
        target.comment = patch.comment
    if patch.type is not None:
        target.type = patch.type
    if patch.subtype is not None:
        target.subtype = patch.subtype
    if patch.confidence is not None:
        target.confidence = patch.confidence


def load_overrides(target_dir: Path) -> OverridesPayload:
    path = _overrides_path(target_dir)
    if not path.exists():
        return OverridesPayload(entities={})
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    raw_entities = raw.get("entities", {})
    assert isinstance(raw_entities, dict), "overrides entities must be an object"
    entities: dict[str, AnnotationPatch] = {}
    for addr, patch in raw_entities.items():
        assert isinstance(addr, str), "override entity key must be a string"
        assert isinstance(patch, dict), "override entity patch must be an object"
        entities[addr] = AnnotationPatch.from_raw(patch)
    return OverridesPayload(entities=entities)


def save_overrides(target_dir: Path, payload: OverridesPayload) -> None:
    path = _overrides_path(target_dir)
    tmp_path = path.with_suffix(".json.tmp")
    raw = {
        "entities": {
            addr: patch.to_raw()
            for addr, patch in payload.entities.items()
        }
    }
    tmp_path.write_text(json.dumps(raw, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _load_entities_by_addr(entities_path: Path) -> dict[str, EntityRecord]:
    entities: dict[str, EntityRecord] = {}
    with open(entities_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entity = json.loads(line)
            assert isinstance(entity, dict), "entity line must decode to an object"
            typed_entity = _entity_from_raw(entity)
            entities[typed_entity["addr"]] = typed_entity
    return entities


def _resolve_annotation_paths(project_name: str, project_root: Path) -> tuple[Path, Path]:
    target_dir = project_root / "targets" / project_name
    if not target_dir.exists():
        raise FileNotFoundError(f"Unknown target: {project_name}")
    entities_path = target_dir / "entities.jsonl"
    if not entities_path.exists():
        raise FileNotFoundError(f"Missing entities.jsonl for target: {project_name}")
    return target_dir, entities_path


def get_entity(project_name: str, addr: str, project_root: Path = PROJECT_ROOT) -> EntityRecord:
    target_dir, entities_path = _resolve_annotation_paths(project_name, project_root)
    entities = _load_entities_by_addr(entities_path)
    entity = entities.get(addr.lower()) or entities.get(addr.upper()) or entities.get(addr)
    if entity is None:
        raise FileNotFoundError(f"Unknown entity {addr} in target {project_name}")

    overrides = load_overrides(target_dir)
    merged = _copy_entity(entity)
    patch = overrides.entities.get(entity["addr"])
    if patch is not None:
        _apply_patch(merged, patch)
    return merged


def patch_entity(project_name: str, addr: str, patch: AnnotationPatch | AnnotationPatchInput,
                 project_root: Path = PROJECT_ROOT) -> EntityRecord:
    patch = _annotation_patch_from_input(patch)
    if patch.type is not None and patch.type not in TYPE_VALUES:
        raise ValueError(f"Unsupported type: {patch.type}")
    if patch.subtype is not None and patch.subtype not in SUBTYPE_VALUES and patch.subtype != "":
        raise ValueError(f"Unsupported subtype: {patch.subtype}")
    if patch.confidence is not None and patch.confidence not in CONFIDENCE_VALUES:
        raise ValueError(f"Unsupported confidence: {patch.confidence}")

    target_dir, _entities_path = _resolve_annotation_paths(project_name, project_root)
    entity = get_entity(project_name, addr, project_root=project_root)
    overrides = load_overrides(target_dir)
    entity_patch = overrides.entities.setdefault(entity["addr"], AnnotationPatch())
    _apply_patch_update(entity_patch, patch)
    save_overrides(target_dir, overrides)
    return get_entity(project_name, addr, project_root=project_root)
