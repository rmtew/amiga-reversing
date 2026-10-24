"""Deterministic source packages; classification belongs to the native render plan.

The transport contains base64 files and a content-hashed manifest. Materialization
uses fresh directories; normal target publication validates and updates an owned
inventory through source_package_publish. ZIP exports use the same package.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from amiga_reversing.disasm.behaviour_validation import LoadedSource

LOADED_SOURCE = LoadedSource(__file__)

SCHEMA = "amiga-reversing-source-package-v1"
MANIFEST = "manifest.json"


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def _path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Invalid package relative path")
    parts = value.split("/")
    if any(not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", p) for p in parts):
        raise ValueError("Unsafe package relative path")
    if any(p.endswith(".") or p.split(".")[0].upper() in {
        "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    } for p in parts):
        raise ValueError("Nonportable package relative path")
    return value


def collect_package_includes(source_text: str, include_root: Path, *, provided: dict[str, bytes] | None = None) -> list[dict[str, Any]]:
    """Collect literal SDK INCLUDE dependencies using the configured include root.

    This does not interpret data or change the rendered source. Conditional
    includes are intentionally over-collected; dynamic include names are refused.
    """
    provided=dict(provided or {})
    for name,data in provided.items():
        _path(name)
        if not isinstance(data,bytes):raise ValueError('Provided INCLUDE must be bytes')
        if (include_root/name).exists():raise ValueError('Provided INCLUDE may not shadow the configured SDK')
    pending = [source_text]
    found: dict[str, dict[str, Any]] = {}
    root = include_root.resolve()
    while pending:
        text = pending.pop()
        for line in text.splitlines():
            directive = re.match(r"^\s*include\s+(.+)$", line, re.IGNORECASE)
            if directive is None:
                continue
            match = re.fullmatch(r'''(["'])([^"'\r\n]+)\1\s*(?:;.*)?''', directive[1])
            if match is None:
                raise ValueError("Package requires literal quoted INCLUDE paths")
            path = _path(match[2])
            if path in found:
                continue
            resolved = (root / path).resolve()
            if not resolved.is_relative_to(root):
                raise ValueError("INCLUDE dependency escapes configured SDK root")
            data = provided[path] if path in provided else resolved.read_bytes()
            provenance = 'provided-application-source' if path in provided else 'configured-platform-sdk'
            found[path] = {"path": path, "data_hex": data.hex(), "kind": "include",
                           "size": len(data), "provenance": provenance}
            pending.append(data.decode("latin-1"))
    return [found[path] for path in sorted(found)]


def build_source_package(payload: dict[str, Any], assets: list[dict[str, Any]], minimum_asset_size: int,
                         *, includes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Bind final profile-encoded source, native-selected bytes and provenance."""
    source = _path(payload["filename"])
    if "/" in source:
        raise ValueError("Package source must be at its root")
    records = []
    files = []
    contents = [(source, payload["source_text"].encode("utf-8"), {"kind": "source"})]
    for asset in [*assets, *(includes or [])]:
        provenance = {k: v for k, v in asset.items() if k not in {"path", "data_hex"}}
        data = bytes.fromhex(asset["data_hex"])
        if asset["size"] != len(data):
            raise ValueError("Native asset size does not match its bytes")
        contents.append((_path(asset["path"]), data,
                         {"kind": "asset", **provenance}))
    for path, data, provenance in sorted(contents):
        records.append({**provenance, "path": path, "size": len(data), "sha256": _hash(data)})
        files.append({"path": path, "data_base64": base64.b64encode(data).decode("ascii")})
    manifest = {
        "schema": SCHEMA, "source": source,
        "target": payload["target"], "assembler_profile": payload["assembler_profile"],
        "metadata_hash": payload["metadata_hash"],
        "target_identity_sha256": payload["target_identity_sha256"],
        "policy": {"id": "native-evidenced-opaque-v1", "minimum_asset_size": minimum_asset_size},
        "files": records,
    }
    package = {"manifest": manifest, "sha256": _hash(_json(manifest)), "files": files}
    validate_source_package(package)
    return package


def extend_source_package(package: dict[str, Any], records: list[dict[str, Any]], *, application: dict[str, Any]) -> dict[str, Any]:
    """Add owned application sources to the existing deterministic package."""
    import copy
    existing=validate_source_package(package);result=copy.deepcopy(package)
    for record in records:
        path=_path(record['path']);data=bytes.fromhex(record['data_hex'])
        if len(data)!=record['size']:raise ValueError('Application file extent differs')
        if path in existing:
            old=next(r for r in result['manifest']['files'] if r['path']==path)
            if data!=existing[path] or record.get('kind')!='include' or old.get('kind')!='include':
                raise ValueError('Application file collides with existing package')
            continue
        existing[path]=data
        attributes={k:v for k,v in record.items() if k!='data_hex'}
        result['manifest']['files'].append(dict(attributes,sha256=_hash(data)))
        result['files'].append(dict(path=path,data_base64=base64.b64encode(data).decode('ascii')))
    result['manifest']['application']=copy.deepcopy(application)
    result['manifest']['files'].sort(key=lambda r:r['path']);result['files'].sort(key=lambda r:r['path'])
    result['sha256']=_hash(_json(result['manifest']));validate_source_package(result)
    return result


def validate_source_package(package: dict[str, Any]) -> dict[str, bytes]:
    """Validate all bytes before writing or invoking either assembler."""
    manifest = package["manifest"]
    if manifest.get("schema") != SCHEMA or package["sha256"] != _hash(_json(manifest)):
        raise ValueError("Source package manifest integrity mismatch")
    files = {}
    folded = set()
    for item in package["files"]:
        path = _path(item["path"])
        if path.lower() in folded or path.lower() == MANIFEST:
            raise ValueError("Duplicate or reserved package path")
        folded.add(path.lower())
        files[path] = base64.b64decode(item["data_base64"], validate=True)
    # Directory entries are implicit, including the generated manifest. Check
    # the complete inventory before writing; ordering must not affect safety.
    occupied = folded | {MANIFEST}
    for path in folded:
        components = path.split("/")
        if any("/".join(components[:index]) in occupied for index in range(1, len(components))):
            raise ValueError("Package file/directory path collision")
    records = manifest["files"]
    if len(records) != len(files) or {r["path"] for r in records} != set(files):
        raise ValueError("Source package file inventory mismatch")
    for record in records:
        data = files[_path(record["path"])]
        if len(data) != record["size"] or _hash(data) != record["sha256"]:
            raise ValueError("Source package file integrity mismatch")
    if "/" in _path(manifest["source"]):
        raise ValueError("Package source must be at its root")
    if manifest["source"] not in files:
        raise ValueError("Source package entry point missing")
    return files


def materialize_source_package(package: dict[str, Any], directory: Path) -> Path:
    files = validate_source_package(package)
    # Staging must be private and empty. Never follow a caller's output symlinks.
    if directory.is_symlink() or (directory.exists() and any(directory.iterdir())):
        raise ValueError("Package staging directory must be empty")
    directory.mkdir(parents=True, exist_ok=True)
    for path, data in files.items():
        destination = directory / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    (directory / MANIFEST).write_bytes(_json(package["manifest"]))
    return directory / str(package["manifest"]["source"])


def source_package_zip(package: dict[str, Any]) -> bytes:
    files = validate_source_package(package)
    files[MANIFEST] = _json(package["manifest"])
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.comment = package["sha256"].encode("ascii")
        for path, data in sorted(files.items()):
            info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output.getvalue()


def _validate_previous_archive(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read(MANIFEST))
            names = archive.namelist()
            expected = [MANIFEST, *(r["path"] for r in manifest["files"])]
            if sorted(names) != sorted(expected):
                raise ValueError("Archive contains unowned files")
            validate_source_package({
                "manifest": manifest, "sha256": archive.comment.decode("ascii"),
                "files": [{"path": p, "data_base64": base64.b64encode(archive.read(p)).decode()}
                          for p in names if p != MANIFEST],
            })
    except (KeyError, TypeError, ValueError, zipfile.BadZipFile) as exc:
        raise ValueError("Existing export was modified or is not a source package; use a new output path") from exc


def write_source_package(package: dict[str, Any], output: Path) -> None:
    """Replace only intact generated ZIPs; reject edited or unrelated artifacts."""
    data = source_package_zip(package)
    if output.is_symlink():
        raise ValueError("Refusing a symlink output")
    if output.exists():
        _validate_previous_archive(output)
        if output.read_bytes() == data:
            return
    with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".source-package-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
