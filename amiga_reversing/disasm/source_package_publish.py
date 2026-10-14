"""Publish validated package companions beside a canonical target source.

The ownership manifest permits regeneration in a populated target directory.
Only files whose previous bytes still match that manifest may be replaced or
removed. Asset selection and rendering remain in the existing package producer.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

from .source_package import _hash, _json, validate_source_package
from .target_local_state import OBSOLETE_TARGET_LOCAL_STATE_FILES, SOURCE_IMPORT_FACT_FILES

PUBLISH_MANIFEST = "source-package-manifest.json"
_PROTECTED_TARGET_PATHS = SOURCE_IMPORT_FACT_FILES | frozenset(OBSOLETE_TARGET_LOCAL_STATE_FILES) | {
    PUBLISH_MANIFEST, "manifest.json", "target_state.json", "decision_journal.jsonl",
    "decision_verifier_artifacts.json",
}


def _destination(directory: Path, relative: str) -> Path:
    """Check every existing component, including portable case collisions."""
    current = directory
    for part in relative.split("/"):
        if current.is_symlink():
            raise ValueError("Refusing a symlink package destination")
        if current.exists():
            if not current.is_dir():
                raise ValueError("Package file/directory path collision")
            matches = [p.name for p in current.iterdir() if p.name.lower() == part.lower()]
            if matches and matches != [part]:
                raise ValueError("Package destination case collision")
        current = current / part
    if current.is_symlink():
        raise ValueError("Refusing a symlink package destination")
    return current


def _previous(directory: Path) -> tuple[dict[str, Any] | None, dict[str, bytes]]:
    manifest_path = _destination(directory, PUBLISH_MANIFEST)
    if not manifest_path.exists():
        return None, {}
    try:
        envelope = json.loads(manifest_path.read_bytes())
        manifest = envelope["manifest"]
        files = []
        for record in manifest["files"]:
            # Validate the inventory/path syntax before touching target files.
            files.append({"path": record["path"], "data_base64": ""})
        # Use the common validator for path/inventory checks, with placeholder
        # bytes bound to a temporary manifest. Then validate actual owned bytes.
        probe = {**manifest, "files": [
            {**record, "size": 0, "sha256": _hash(b"")}
            for record in manifest["files"]
        ]}
        validate_source_package({"manifest": probe, "sha256": _hash(_json(probe)), "files": files})
        _check_reserved(manifest)
        for item in files:
            path = _destination(directory, item["path"])
            if not path.is_file():
                raise ValueError("Owned package file missing or not regular")
            item["data_base64"] = base64.b64encode(path.read_bytes()).decode("ascii")
        owned = validate_source_package({**envelope, "files": files})
        return manifest, owned
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise ValueError("Existing source package was modified or is invalid") from exc


def _check_reserved(manifest: dict[str, Any]) -> None:
    for record in manifest["files"]:
        if record["path"].split("/")[0].lower() in _PROTECTED_TARGET_PATHS:
            raise ValueError("Reserved publisher or target state path collision")


def load_published_source_package(directory: Path) -> dict[str, Any]:
    """Load and validate the checked-in projection without regenerating it."""
    directory = Path(directory)
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("Package target directory must exist and not be a symlink")
    for parent in directory.absolute().parents:
        if parent.is_symlink():
            raise ValueError("Refusing a symlink target ancestor")
    manifest, files = _previous(directory)
    if manifest is None:
        raise ValueError("Published source package manifest is missing")
    return {"manifest": manifest, "sha256": _hash(_json(manifest)), "files": [
        {"path": path, "data_base64": base64.b64encode(data).decode("ascii")}
        for path, data in sorted(files.items())
    ]}


def publish_source_package(
    package: dict[str, Any], directory: Path, *,
    expected_source_text: str | None = None,
    expected_source_sha256: str | None = None,
) -> Path:
    """Publish per file with rollback, returning the canonical source file path.

    Initial takeover of an existing canonical source requires its current text
    or SHA-256. Subsequent writes require the entire old ownership inventory to
    remain intact, including companions that are becoming obsolete.
    """
    directory = Path(directory)
    files = validate_source_package(package)
    manifest = package["manifest"]
    _check_reserved(manifest)
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("Package target directory must exist and not be a symlink")
    for parent in directory.absolute().parents:
        if parent.is_symlink():
            raise ValueError("Refusing a symlink target ancestor")
    previous, owned = _previous(directory)
    source = manifest["source"]
    if previous is not None and previous["source"] != source:
        raise ValueError("Existing package owns a different canonical source")
    destinations = {p: _destination(directory, p) for p in files}
    for relative, path in destinations.items():
        if path.exists() and relative not in owned:
            if relative != source or not path.is_file():
                raise ValueError("Package destination collision with an unowned file")
            data = path.read_bytes()
            if expected_source_text is None and expected_source_sha256 is None:
                raise ValueError("Existing canonical source requires expected source validation")
            if ((expected_source_text is not None and data != expected_source_text.encode("utf-8"))
                    or (expected_source_sha256 is not None and _hash(data) != expected_source_sha256)):
                raise ValueError("Existing canonical source differs from expected source")
    manifest_path = directory / PUBLISH_MANIFEST
    manifest_bytes = _json({"manifest": manifest, "sha256": package["sha256"]})
    if files == owned and manifest_path.read_bytes() == manifest_bytes:
        return directory / source

    originals = {p: (directory / p) for p in owned}
    originals.update({p: path for p, path in destinations.items() if path.exists()})
    if manifest_path.exists():
        originals[PUBLISH_MANIFEST] = manifest_path
    created_directories: list[Path] = []
    changed: list[str] = []
    with tempfile.TemporaryDirectory(prefix=".source-package-", dir=directory) as temporary:
        staging = Path(temporary)
        # Stage all replacement bytes and recovery copies before any owned write.
        for index, (_relative, data) in enumerate([*files.items(), (PUBLISH_MANIFEST, manifest_bytes)]):
            staged = staging / f"new-{index}"
            with staged.open("wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        backups = {}
        for index, (relative, path) in enumerate(originals.items()):
            backup = staging / f"old-{index}"
            shutil.copy2(path, backup)
            backups[relative] = backup
        try:
            for index, relative in enumerate(files):
                path = destinations[relative]
                missing = []
                parent = path.parent
                while not parent.exists():
                    missing.append(parent)
                    parent = parent.parent
                for parent in reversed(missing):
                    parent.mkdir()
                    created_directories.append(parent)
                os.replace(staging / f"new-{index}", path)
                changed.append(relative)
            for relative in sorted(owned.keys() - files.keys()):
                (directory / relative).unlink()
                changed.append(relative)
            # The new inventory becomes authoritative only after every write.
            os.replace(staging / f"new-{len(files)}", manifest_path)
            changed.append(PUBLISH_MANIFEST)
        except BaseException:
            for relative in reversed(changed):
                path = directory / relative
                if relative in backups:
                    os.replace(backups[relative], path)
                else:
                    path.unlink(missing_ok=True)
            for parent in reversed(created_directories):
                parent.rmdir()
            raise
    # Only ancestors of proven obsolete owned files are eligible for cleanup.
    obsolete_parents = {parent for p in owned.keys() - files.keys()
                        for parent in (directory / p).parents if parent.is_relative_to(directory)
                        and parent != directory}
    for parent in sorted(obsolete_parents, key=lambda p: len(p.parts), reverse=True):
        with suppress(OSError):
            parent.rmdir()
    return directory / source
