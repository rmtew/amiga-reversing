from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_validate_target_seeded_metadata_script_normalizes_seeded_file(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / "target_seeded_metadata.json").write_text(
        json.dumps(
            {
                "target_type": "program",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "app_slot_regions": [],
                "seeded_entities": [
                    {
                        "addr": 256,
                        "end": 512,
                        "hunk": 0,
                        "name": "map_data_keep",
                        "type": "data",
                        "subtype": "level_data",
                        "seed_origin": "primary_doc",
                        "review_status": "seeded",
                        "citation": "asm",
                        "source_id": "seeded_source",
                        "source_path": "resources/demo/source.asm",
                        "source_locator": "MapDataKeep",
                    }
                ],
                "seeded_code_entrypoints": [
                    {
                        "addr": 1494,
                        "hunk": 0,
                        "name": "check_keyboard",
                        "seed_origin": "primary_doc",
                        "review_status": "seeded",
                        "citation": "asm",
                        "source_id": "seeded_source",
                        "source_path": "resources/demo/source.asm",
                        "source_locator": "CheckKeyboard",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parent.parent / "scripts" / "validate_target_seeded_metadata.py"

    result = subprocess.run(
        [sys.executable, str(script), str(target_dir), "--write"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "target_seeded_metadata: ok"
    payload = json.loads((target_dir / "target_seeded_metadata.json").read_text(encoding="utf-8"))
    assert payload["seeded_entities"][0]["name"] == "map_data_keep"
    assert payload["seeded_entities"][0]["source_locator"] == "MapDataKeep"
    assert payload["seeded_code_entrypoints"][0]["name"] == "check_keyboard"


def test_validate_target_seeded_metadata_script_rejects_bootblock_payload(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / "target_seeded_metadata.json").write_text(
        json.dumps(
            {
                "target_type": "bootblock",
                "entry_register_seeds": [],
                "bootblock": {
                    "magic_ascii": "DOS",
                    "flags_byte": 0,
                    "fs_description": "DOS\\0 - OFS",
                    "checksum": "0x00000000",
                    "checksum_valid": True,
                    "rootblock_ptr": 880,
                    "bootcode_offset": 12,
                    "bootcode_size": 1012,
                    "load_address": 458752,
                    "entrypoint": 458764,
                },
                "resident": None,
                "library": None,
                "custom_structs": [],
                "app_slot_regions": [],
                "seeded_entities": [],
                "seeded_code_entrypoints": [],
            }
        ),
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parent.parent / "scripts" / "validate_target_seeded_metadata.py"

    result = subprocess.run(
        [sys.executable, str(script), str(target_dir)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "must not contain bootblock metadata" in result.stderr


def test_validate_target_seeded_metadata_script_rejects_missing_source_locator(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / "target_seeded_metadata.json").write_text(
        json.dumps(
            {
                "target_type": "program",
                "entry_register_seeds": [],
                "bootblock": None,
                "resident": None,
                "library": None,
                "custom_structs": [],
                "app_slot_regions": [],
                "seeded_entities": [
                    {
                        "addr": 256,
                        "end": 512,
                        "hunk": 0,
                        "name": "map_data_keep",
                        "type": "data",
                        "subtype": "level_data",
                        "seed_origin": "primary_doc",
                        "review_status": "seeded",
                        "citation": "asm",
                        "source_id": "seeded_source",
                        "source_path": "resources/demo/source.asm",
                    }
                ],
                "seeded_code_entrypoints": [],
            }
        ),
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parent.parent / "scripts" / "validate_target_seeded_metadata.py"

    result = subprocess.run(
        [sys.executable, str(script), str(target_dir)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "missing source_locator" in result.stderr


def test_validate_target_seeded_metadata_script_rejects_non_object_root(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / "target_seeded_metadata.json").write_text(
        "[]",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parent.parent / "scripts" / "validate_target_seeded_metadata.py"

    result = subprocess.run(
        [sys.executable, str(script), str(target_dir)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Bad target_seeded_metadata.json" in result.stderr
