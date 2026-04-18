from __future__ import annotations

import hashlib
import re
from pathlib import Path

AMIGA_DISK_PREFIX = "amiga_disk_"
AMIGA_HUNK_PREFIX = "amiga_hunk_"
AMIGA_RAW_PREFIX = "amiga_raw_"

SAFE_PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
UNSAFE_PROJECT_CHARS_RE = re.compile(r"[^A-Za-z0-9._-]+")
SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


def ensure_safe_project_id(project_id: str) -> str:
    project_id = project_id.strip()
    if not SAFE_PROJECT_RE.fullmatch(project_id):
        raise ValueError("Project id must match [A-Za-z0-9][A-Za-z0-9._-]*")
    return project_id


def normalize_filename_stem(filename: str) -> str:
    stem = filename.strip()
    cleaned = UNSAFE_PROJECT_CHARS_RE.sub("-", stem).strip("._-")
    if not cleaned:
        raise ValueError("Unable to derive project name from filename")
    if not cleaned[0].isalnum():
        cleaned = f"project-{cleaned}"
    lowered = cleaned.lower()
    return ensure_safe_project_id(lowered)


def derive_disk_id_from_stem(stem: str) -> str:
    cleaned = normalize_filename_stem(stem)
    if not cleaned[0].isalnum():
        cleaned = f"disk-{cleaned}"
    return ensure_safe_project_id(cleaned)


def disk_project_id(disk_id: str) -> str:
    return ensure_safe_project_id(f"{AMIGA_DISK_PREFIX}{disk_id}")


def hunk_target_id(base_name: str) -> str:
    return ensure_safe_project_id(f"{AMIGA_HUNK_PREFIX}{base_name}")


def raw_target_id(base_name: str) -> str:
    return ensure_safe_project_id(f"{AMIGA_RAW_PREFIX}{base_name}")


def bootblock_local_target_id() -> str:
    return raw_target_id("bootblock")


def _disk_entry_base_name(full_path: str) -> str:
    base = SAFE_ID_RE.sub("_", full_path.replace("/", "__")).strip("._-").lower()
    digest = hashlib.sha1(full_path.encode("utf-8")).hexdigest()[:8]
    candidate = f"{base}_{digest}"
    if len(candidate) > 71:
        candidate = candidate[:71].rstrip("._-")
    return ensure_safe_project_id(candidate)


def disk_entry_local_target_id(full_path: str) -> str:
    candidate = hunk_target_id(_disk_entry_base_name(full_path))
    if len(candidate) > 80:
        candidate = candidate[:80].rstrip("._-")
    return ensure_safe_project_id(candidate)


def disk_child_project_id(disk_id: str, local_target_id: str) -> str:
    return ensure_safe_project_id(f"{disk_project_id(disk_id)}__{local_target_id}")


def target_output_stem(target_dir_name: str) -> str:
    for prefix in (AMIGA_HUNK_PREFIX, AMIGA_RAW_PREFIX, AMIGA_DISK_PREFIX):
        if target_dir_name.startswith(prefix):
            stem = target_dir_name.removeprefix(prefix)
            return ensure_safe_project_id(stem)
    return ensure_safe_project_id(target_dir_name)


def is_disk_project_id(project_id: str) -> bool:
    return project_id.startswith(AMIGA_DISK_PREFIX) and "__" not in project_id[len(AMIGA_DISK_PREFIX):]


def disk_project_root(project_root: Path, disk_id: str) -> Path:
    return project_root / "targets" / disk_project_id(disk_id)


def disk_project_targets_dir(project_root: Path, disk_id: str) -> Path:
    return disk_project_root(project_root, disk_id) / "targets"


def disk_child_target_relpath(disk_id: str, local_target_id: str) -> Path:
    return Path("targets") / disk_project_id(disk_id) / "targets" / local_target_id
