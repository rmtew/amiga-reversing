from amiga_reversing.tools.migrate_function_summaries import migrate_canonical_location_records, migrate_records


def _unknown_effects() -> dict[str, object]:
    return {
        "schema_version": 1,
        "registers": {"state": "unknown"},
        "memory": {"state": "unknown"},
        "escapes": {"state": "unknown"},
    }


def _direct(action_id: str, sequence: int, entry_offset: int, register: str) -> dict[str, object]:
    return {
        "record": "manual_action",
        "action_id": action_id,
        "sequence": sequence,
        "kind": "create_manual_function_register_contract",
        "function_register_contract": {
            "function_register_contract_id": f"old-{action_id}",
            "hunk": 0,
            "entry_offset": entry_offset,
            "register": register,
            "struct_name": "world_object_shared_prefix",
            "note": "old direct input",
            "context_name": "test",
        },
    }


def test_migration_groups_inputs_by_direct_callable_and_preserves_history() -> None:
    header = {"record": "manual_action_log_header", "version": 1}
    converted, report = migrate_records([header, _direct("first", 2, 0x807C, "A1"), _direct("second", 3, 0x807C, "A2")])

    assert converted[0] == header
    summary = converted[1]["function_summary"]
    assert summary["function_summary_id"] == "function-summary-entry-h0-0000807C"
    assert summary["inputs"] == [
        {"location": {"kind": "register", "register": "A1", "width": 4}, "value_kind": "struct_ptr", "struct_name": "world_object_shared_prefix"},
        {"location": {"kind": "register", "register": "A2", "width": 4}, "value_kind": "struct_ptr", "struct_name": "world_object_shared_prefix"},
    ]
    assert summary["effects"] == _unknown_effects()
    assert report["active_summary_mappings"][0]["source_action_ids"] == ["first", "second"]


def test_migration_keeps_removed_fact_out_of_summary() -> None:
    created = _direct("first", 2, 0x807C, "A1")
    removed = {
        "record": "manual_action",
        "action_id": "remove",
        "sequence": 3,
        "kind": "remove_manual_function_register_contract",
        "function_register_contract_id": "old-first",
    }
    converted, report = migrate_records([created, removed])

    assert converted == []
    assert report["retired_action_history"][-1]["state"] == "removed"


def test_migration_converts_callback_table_and_retains_nonlegacy_records() -> None:
    retained = {"record": "manual_action", "action_id": "label", "sequence": 1, "kind": "create_manual_label"}
    callback = {
        "record": "manual_action",
        "action_id": "callback",
        "sequence": 2,
        "created_at": "2026-07-29T00:00:00+00:00",
        "kind": "create_manual_callback_table_signature",
        "callback_table_signature": {
            "callback_table_signature_id": "old-callback",
            "hunk": 0,
            "table_offset": 0x1432,
            "entry_count": 33,
            "register": "A5",
            "struct_name": "world_object_shared_prefix",
            "note": "old callback input",
            "context_name": "callback",
        },
    }
    converted, report = migrate_records([retained, callback])

    assert converted[0] == retained
    summary = converted[1]["function_summary"]
    assert summary["callable_kind"] == "callback_table"
    assert summary["table_offset"] == 0x1432
    assert summary["entry_count"] == 33
    assert summary["inputs"][0]["location"] == {"kind": "register", "register": "A5", "width": 4}
    assert summary["effects"] == _unknown_effects()
    assert report["active_summary_mappings"][0]["source_fact_ids"] == ["old-callback"]


def test_migration_rejects_duplicate_input_location() -> None:
    try:
        migrate_records([_direct("first", 2, 0x807C, "A1"), _direct("second", 3, 0x807C, "A1")])
    except ValueError as exc:
        assert "duplicate input location" in str(exc)
    else:
        raise AssertionError("expected duplicate input rejection")


def test_migration_rejects_undo_of_retired_action() -> None:
    try:
        migrate_records([
            _direct("first", 2, 0x807C, "A1"),
            {"record": "manual_action", "action_id": "undo", "sequence": 3, "kind": "undo_action", "undoes_action_id": "first"},
        ])
    except ValueError as exc:
        assert "undo/redo" in str(exc)
    else:
        raise AssertionError("expected undo rejection")


def test_migration_replaces_retired_effect_triple_in_existing_summary() -> None:
    legacy_summary = {
        "record": "manual_action",
        "action_id": "summary",
        "sequence": 2,
        "kind": "create_manual_function_summary",
        "function_summary": {
            "function_summary_id": "summary-id",
            "hunk": 0,
            "callable_kind": "direct",
            "entry_offset": 0x807C,
            "inputs": [{"location": "A1", "value_kind": "struct_ptr", "struct_name": "world_object"}],
            "return_contract": "unknown",
            "register_effects": "unknown",
            "memory_effects": "unknown",
            "note": "legacy",
            "context_name": "",
        },
    }
    converted, report = migrate_records([legacy_summary])

    assert converted[0]["action_id"] == "summary"
    assert converted[0]["function_summary"]["effects"] == _unknown_effects()
    assert "return_contract" not in converted[0]["function_summary"]
    assert report["summary_schema_migrations"] == [
        {"action_id": "summary", "sequence": 2, "function_summary_id": "summary-id"}
    ]


def test_migration_rejects_mixed_or_previously_migrated_summary_schema() -> None:
    record = {
        "record": "manual_action",
        "action_id": "summary",
        "sequence": 2,
        "kind": "create_manual_function_summary",
        "function_summary": {"function_summary_id": "summary-id", "effects": _unknown_effects()},
    }
    try:
        migrate_records([record])
    except ValueError as exc:
        assert "canonical effects schema" in str(exc)
    else:
        raise AssertionError("expected mixed-schema rejection")


def test_location_migration_replaces_only_canonical_register_strings() -> None:
    record = {
        "record": "manual_action",
        "action_id": "summary",
        "sequence": 2,
        "kind": "create_manual_function_summary",
        "function_summary": {
            "function_summary_id": "summary-id",
            "hunk": 0,
            "callable_kind": "direct",
            "entry_offset": 0x807C,
            "inputs": [{"location": "A1", "value_kind": "struct_ptr", "struct_name": "world_object"}],
            "effects": _unknown_effects(),
            "note": "canonical old location",
            "context_name": "",
        },
    }
    converted, report = migrate_canonical_location_records([record])

    assert converted[0]["function_summary"]["inputs"][0]["location"] == {
        "kind": "register", "register": "A1", "width": 4,
    }
    assert report["function_summary_location_migrations"] == [
        {"action_id": "summary", "sequence": 2, "function_summary_id": "summary-id"}
    ]
