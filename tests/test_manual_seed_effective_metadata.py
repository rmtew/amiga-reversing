from __future__ import annotations

import json
from pathlib import Path

from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.effective_metadata import effective_metadata_text
from amiga_reversing.disasm.manual_actions import (
    MANUAL_ACTION_LOG_FILE_NAME,
    build_target_identity,
)
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def _append_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _action(action_id: str, sequence: int, kind: str, **fields: object) -> dict[str, object]:
    return {
        "record": "manual_action",
        "action_id": action_id,
        "sequence": sequence,
        "created_at": f"2026-05-13T00:00:0{sequence}+00:00",
        "kind": kind,
        **fields,
    }


def test_effective_metadata_includes_required_manual_code_and_data_seeds(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={
                    "seed_id": "code-start",
                    "kind": "code",
                    "mode": "required",
                    "range": "h0:$00000200..$00000208",
                    "name": "manual_start",
                    "role": "extra entrypoint",
                },
            ),
            _action(
                "a2",
                2,
                "create_manual_seed",
                seed={
                    "seed_id": "text-table",
                    "kind": "data",
                    "mode": "required",
                    "hunk": 1,
                    "addr": 0x300,
                    "end": 0x320,
                    "data_role": "string",
                    "unit": "byte",
                    "encoding": "ascii",
                    "name": "manual_text",
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_entrypoints"] == [
        {
            "addr": 0x200,
            "citation": "manual_action_log:code-start",
            "comment": "mode=required",
            "hunk": 0,
            "name": "manual_start",
            "review_status": "seeded",
            "role": "extra entrypoint",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualSeed:code-start",
            "source_path": None,
        }
    ]
    assert payload["seeded_entities"] == [
        {
            "addr": 0x300,
            "citation": "manual_action_log:text-table",
            "comment": "mode=required, data_role=string, unit=byte, encoding=ascii",
            "end": 0x320,
            "hunk": 1,
            "name": "manual_text",
            "review_status": "seeded",
            "seed_origin": "manual_analysis",
            "source_id": "manual_action_log",
            "source_locator": "ManualSeed:text-table",
            "source_path": None,
            "subtype": "string",
            "type": "data",
            "unit": "byte",
            "encoding": "ascii",
        }
    ]


def test_effective_metadata_ignores_suggested_manual_seeds_until_accepted(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": {}},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={
                    "seed_id": "maybe-code",
                    "kind": "code",
                    "mode": "suggested",
                    "addr": 0x200,
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_entrypoints"] == []
    assert payload["seeded_entities"] == []


def test_effective_metadata_ignores_manual_seeds_when_log_target_identity_mismatches(tmp_path: Path) -> None:
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": str(binary_path),
                "load_address": 0x70000,
                "entrypoint": 0x70000,
                "code_start_offset": 0,
            }
        ),
        encoding="utf-8",
    )
    binary_source = resolve_target_binary_source(target_dir, project_root=tmp_path)
    assert binary_source is not None
    stale_identity = {**build_target_identity(binary_source), "original_sha256": "0" * 64}
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    _append_jsonl(
        target_dir / MANUAL_ACTION_LOG_FILE_NAME,
        [
            {"record": "manual_action_log_header", "version": 1, "target_identity": stale_identity},
            _action(
                "a1",
                1,
                "create_manual_seed",
                seed={
                    "seed_id": "stale-code",
                    "kind": "code",
                    "mode": "required",
                    "addr": 0x200,
                },
            ),
        ],
    )

    payload = json.loads(effective_metadata_text(target_dir))

    assert payload["seeded_code_entrypoints"] == []
