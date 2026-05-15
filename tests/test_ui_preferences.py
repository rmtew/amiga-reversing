from __future__ import annotations

from pathlib import Path

from amiga_reversing.disasm.ui_preferences import (
    load_ui_preferences,
    save_ui_preferences,
    ui_preferences_path,
)


def test_ui_preferences_load_save_and_missing_file(tmp_path: Path) -> None:
    assert load_ui_preferences(tmp_path, "demo") == {
        "version": 1,
        "target_id": "demo",
        "listing_location": None,
        "reproduction_profile_view": None,
        "source_export_assembler": None,
    }

    saved = save_ui_preferences(
        tmp_path,
        "demo",
        {
            "target_id": "wrong",
            "listing_location": {
                "row_index": 12,
                "stable_key": "row-12",
                "row_code": "start:",
                "addr": 4,
                "section_index": 0,
                "start_offset": 4,
                "scroll_top": 240,
                "window_start": 8,
                "ignored": "x",
            },
            "reproduction_profile_view": "summary",
            "source_export_assembler": "vasm",
            "domain_fact": "must-not-persist",
        },
    )

    assert saved["target_id"] == "demo"
    assert saved["listing_location"] == {
        "row_index": 12,
        "stable_key": "row-12",
        "row_code": "start:",
        "addr": 4,
        "section_index": 0,
        "start_offset": 4,
        "scroll_top": 240,
        "window_start": 8,
    }
    assert "domain_fact" not in saved
    assert load_ui_preferences(tmp_path, "demo") == saved
    assert not (tmp_path / "manual_actions.jsonl").exists()


def test_ui_preferences_stale_identity_falls_back(tmp_path: Path) -> None:
    save_ui_preferences(tmp_path, "old-target", {"listing_location": {"row_index": 5}})

    loaded = load_ui_preferences(tmp_path, "new-target")

    assert loaded["target_id"] == "new-target"
    assert loaded["listing_location"] is None
    assert loaded["stale"] is True
    assert ui_preferences_path(tmp_path).name == "ui_preferences.json"
