from __future__ import annotations

import json
from pathlib import Path

from disasm.annotations import AnnotationPatchInput, get_entity, patch_entity


def test_get_entity_merges_overrides(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    (target_dir / "entities.jsonl").write_text(
        json.dumps({"addr": "0x0000", "type": "code", "name": "entry_point"}) + "\n",
        encoding="utf-8",
    )
    (target_dir / "Demo.s").write_text("; output\n", encoding="utf-8")
    (bin_dir / "Demo").write_bytes(b"\x4e\x75")
    (target_dir / "overrides.json").write_text(
        json.dumps({"entities": {"0x0000": {"comment": "hello"}}}),
        encoding="utf-8",
    )

    entity = get_entity("demo", "0x0000", project_root=project_root)

    assert entity["name"] == "entry_point"
    assert entity["comment"] == "hello"


def test_patch_entity_persists_name_comment_and_metadata(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    (target_dir / "entities.jsonl").write_text(
        json.dumps({"addr": "0x0000", "type": "code"}) + "\n",
        encoding="utf-8",
    )
    (target_dir / "Demo.s").write_text("; output\n", encoding="utf-8")
    (bin_dir / "Demo").write_bytes(b"\x4e\x75")

    patch = AnnotationPatchInput({
        "name": "main",
        "comment": "top entry",
        "type": "data",
        "subtype": "string",
        "confidence": "verified",
    })

    updated = patch_entity(
        "demo", "0x0000",
        patch,
        project_root=project_root)

    assert updated["name"] == "main"
    assert updated["comment"] == "top entry"
    assert updated["type"] == "data"
    assert updated["subtype"] == "string"
    assert updated["confidence"] == "verified"
    saved = json.loads((target_dir / "overrides.json").read_text(encoding="utf-8"))
    assert saved["entities"]["0x0000"]["name"] == "main"
    assert saved["entities"]["0x0000"]["type"] == "data"


def test_patch_entity_rejects_unknown_fields(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    (target_dir / "entities.jsonl").write_text(
        json.dumps({"addr": "0x0000", "type": "code"}) + "\n",
        encoding="utf-8",
    )
    (target_dir / "Demo.s").write_text("; output\n", encoding="utf-8")
    (bin_dir / "Demo").write_bytes(b"\x4e\x75")

    try:
        patch = AnnotationPatchInput({"unsupported": "value"})
        patch_entity("demo", "0x0000", patch, project_root=project_root)
    except ValueError as exc:
        assert "Unsupported annotation fields" in str(exc)
    else:
        raise AssertionError("expected unsupported field error")


def test_patch_entity_rejects_invalid_subtype_value(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    (target_dir / "entities.jsonl").write_text(
        json.dumps({"addr": "0x0000", "type": "data"}) + "\n",
        encoding="utf-8",
    )
    (target_dir / "Demo.s").write_text("; output\n", encoding="utf-8")
    (bin_dir / "Demo").write_bytes(b"\x4e\x75")

    try:
        patch = AnnotationPatchInput({"subtype": "bad-subtype"})
        patch_entity("demo", "0x0000", patch, project_root=project_root)
    except ValueError as exc:
        assert "Unsupported subtype" in str(exc)
    else:
        raise AssertionError("expected invalid subtype error")
