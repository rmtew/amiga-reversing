from __future__ import annotations

import json
from pathlib import Path
from typing import cast

UI_PREFERENCES_FILE_NAME = "ui_preferences.json"


def ui_preferences_path(target_dir: Path) -> Path:
    return target_dir / UI_PREFERENCES_FILE_NAME


def default_ui_preferences(target_id: str, *, stale: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": 1,
        "target_id": target_id,
        "listing_location": None,
        "reproduction_profile_view": None,
        "source_export_assembler": None,
    }
    if stale:
        payload["stale"] = True
    return payload


def load_ui_preferences(target_dir: Path, target_id: str) -> dict[str, object]:
    path = ui_preferences_path(target_dir)
    if not path.exists():
        return default_ui_preferences(target_id)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_ui_preferences(target_id, stale=True)
    if not isinstance(raw, dict):
        return default_ui_preferences(target_id, stale=True)
    payload = cast(dict[str, object], raw)
    if payload.get("target_id") != target_id:
        return default_ui_preferences(target_id, stale=True)
    return {
        **default_ui_preferences(target_id),
        **_sanitize_ui_preferences(payload),
    }


def save_ui_preferences(target_dir: Path, target_id: str, payload: dict[str, object]) -> dict[str, object]:
    preferences = {
        **default_ui_preferences(target_id),
        **_sanitize_ui_preferences(payload),
        "version": 1,
        "target_id": target_id,
    }
    ui_preferences_path(target_dir).write_text(
        json.dumps(preferences, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return preferences


def _sanitize_ui_preferences(payload: dict[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    listing_location = payload.get("listing_location")
    if isinstance(listing_location, dict):
        clean["listing_location"] = _sanitize_listing_location(cast(dict[str, object], listing_location))
    for key in ("reproduction_profile_view", "source_export_assembler"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            clean[key] = value
        elif value is None:
            clean[key] = None
    return clean


def _sanitize_listing_location(payload: dict[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    for key in ("row_index", "addr", "section_index", "start_offset", "scroll_top", "window_start"):
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            clean[key] = value
        elif isinstance(value, float) and value.is_integer():
            clean[key] = int(value)
    for key in ("stable_key", "row_code"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            clean[key] = value
    return clean
