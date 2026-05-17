from __future__ import annotations

from pathlib import Path

from amiga_reversing.disasm.manual_actions import MANUAL_ACTION_LOG_FILE_NAME
from amiga_reversing.disasm.ui_preferences import UI_PREFERENCES_FILE_NAME

TARGET_UI_EDITS_FILE_NAME = "target_ui_edits.json"

OBSOLETE_TARGET_LOCAL_STATE_FILES = (
    TARGET_UI_EDITS_FILE_NAME,
    UI_PREFERENCES_FILE_NAME,
    MANUAL_ACTION_LOG_FILE_NAME,
)

SOURCE_IMPORT_FACT_FILES = frozenset(
    {
        "source_binary.json",
        "target_metadata.json",
        "target_seeded_metadata.json",
        "target_corrections.json",
        "binary.bin",
        "decompression.json",
        ".project.json",
    }
)
PROFILE_SET_TARGET_METADATA_FILES = (
    "target_metadata.json",
    "target_seeded_metadata.json",
    "target_corrections.json",
)


def clean_obsolete_target_local_state(target_dir: Path) -> None:
    for file_name in OBSOLETE_TARGET_LOCAL_STATE_FILES:
        path = target_dir / file_name
        if path.exists() and path.is_file():
            path.unlink()
