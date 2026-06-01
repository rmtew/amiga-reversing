from __future__ import annotations

import json
import os
import tempfile
from contextlib import suppress
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
    path = ui_preferences_path(target_dir)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=path.parent,
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(json.dumps(preferences, indent=2, sort_keys=True) + "\n")
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            with suppress(FileNotFoundError):
                temp_path.unlink()
    return preferences


def _sanitize_ui_preferences(payload: dict[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    listing_location = payload.get("listing_location")
    if isinstance(listing_location, dict):
        sanitized_listing_location = _sanitize_listing_location(cast(dict[str, object], listing_location))
        if sanitized_listing_location:
            clean["listing_location"] = sanitized_listing_location
    for key in ("reproduction_profile_view", "source_export_assembler"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            clean[key] = value
        elif value is None:
            clean[key] = None
    return clean


def _sanitize_listing_location(payload: dict[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    locator = _sanitize_listing_locator(payload.get("locator"))
    if locator is not None:
        clean["locator"] = locator
    selection_locator = _sanitize_listing_locator(payload.get("selection_locator"))
    if selection_locator is not None:
        clean["selection_locator"] = selection_locator
    focus_locator = _sanitize_listing_locator(payload.get("focus_locator"))
    if focus_locator is not None:
        clean["focus_locator"] = focus_locator
    viewport_anchor = _sanitize_viewport_anchor(payload.get("viewport_anchor"))
    if viewport_anchor is not None:
        clean["viewport_anchor"] = viewport_anchor
    return clean


def _sanitize_listing_locator(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    payload = cast(dict[str, object], value)
    clean: dict[str, object] = {}
    for key in ("target_id", "projection_hash", "row_key", "kind"):
        text = payload.get(key)
        if not isinstance(text, str) or not text:
            return None
        clean[key] = text
    for key in (
        "section_index",
        "start_offset",
        "end_offset",
        "storage_address",
        "runtime_address",
    ):
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            clean[key] = value
        elif isinstance(value, float) and value.is_integer():
            clean[key] = int(value)
    return clean


def _sanitize_viewport_anchor(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    payload = cast(dict[str, object], value)
    clean: dict[str, object] = {}
    for key in ("scroll_top", "window_start"):
        raw = payload.get(key)
        if isinstance(raw, int) and not isinstance(raw, bool):
            clean[key] = raw
        elif isinstance(raw, float) and raw.is_integer():
            clean[key] = int(raw)
    return clean or None
