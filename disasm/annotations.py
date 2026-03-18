from __future__ import annotations

import json
from pathlib import Path

from disasm.project_paths import PROJECT_ROOT

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


def _overrides_path(target_dir: Path) -> Path:
    return target_dir / "overrides.json"


def load_overrides(target_dir: Path) -> dict:
    path = _overrides_path(target_dir)
    if not path.exists():
        return {"entities": {}}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_overrides(target_dir: Path, payload: dict) -> None:
    path = _overrides_path(target_dir)
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _load_entities_by_addr(entities_path: Path) -> dict[str, dict]:
    entities: dict[str, dict] = {}
    with open(entities_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entity = json.loads(line)
            entities[entity["addr"]] = entity
    return entities


def _resolve_annotation_paths(project_name: str, project_root: Path) -> tuple[Path, Path]:
    target_dir = project_root / "targets" / project_name
    if not target_dir.exists():
        raise FileNotFoundError(f"Unknown target: {project_name}")
    entities_path = target_dir / "entities.jsonl"
    if not entities_path.exists():
        raise FileNotFoundError(f"Missing entities.jsonl for target: {project_name}")
    return target_dir, entities_path


def get_entity(project_name: str, addr: str, project_root: Path = PROJECT_ROOT) -> dict:
    target_dir, entities_path = _resolve_annotation_paths(project_name, project_root)
    entities = _load_entities_by_addr(entities_path)
    entity = entities.get(addr.lower()) or entities.get(addr.upper()) or entities.get(addr)
    if entity is None:
        raise FileNotFoundError(f"Unknown entity {addr} in target {project_name}")

    overrides = load_overrides(target_dir)
    merged = dict(entity)
    merged.update(overrides.get("entities", {}).get(entity["addr"], {}))
    return merged


def patch_entity(project_name: str, addr: str, patch: dict,
                 project_root: Path = PROJECT_ROOT) -> dict:
    invalid = set(patch) - EDITABLE_FIELDS
    if invalid:
        raise ValueError(f"Unsupported annotation fields: {sorted(invalid)}")
    if "type" in patch and patch["type"] not in TYPE_VALUES:
        raise ValueError(f"Unsupported type: {patch['type']}")
    if "subtype" in patch and patch["subtype"] not in SUBTYPE_VALUES and patch["subtype"] != "":
        raise ValueError(f"Unsupported subtype: {patch['subtype']}")
    if "confidence" in patch and patch["confidence"] not in CONFIDENCE_VALUES:
        raise ValueError(f"Unsupported confidence: {patch['confidence']}")

    target_dir, _entities_path = _resolve_annotation_paths(project_name, project_root)
    entity = get_entity(project_name, addr, project_root=project_root)
    overrides = load_overrides(target_dir)
    entities = overrides.setdefault("entities", {})
    entity_patch = entities.setdefault(entity["addr"], {})
    entity_patch.update({key: value for key, value in patch.items() if value is not None})
    save_overrides(target_dir, overrides)
    return get_entity(project_name, addr, project_root=project_root)
