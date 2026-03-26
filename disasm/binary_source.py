from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DESCRIPTOR_FILE_NAME = "source_binary.json"


# TODO(X)
def _json_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object, got {type(value).__name__}")
    return cast(dict[str, object], value)


@dataclass(frozen=True, slots=True)
class HunkFileBinarySource:
    kind: Literal["hunk_file"]
    path: Path
    display_path: str
    analysis_cache_path: Path
    parent_disk_id: str | None = None

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()


@dataclass(frozen=True, slots=True)
class DiskEntryBinarySource:
    kind: Literal["disk_entry"]
    disk_id: str
    adf_path: Path
    entry_path: str
    display_path: str
    analysis_cache_path: Path
    parent_disk_id: str | None = None

    def read_bytes(self) -> bytes:
        from amiga_disk.adf import read_adf_entry
        return read_adf_entry(self.adf_path, self.entry_path)


@dataclass(frozen=True, slots=True)
class RawBinarySource:
    kind: Literal["raw_binary"]
    path: Path
    address_model: Literal["local_offset", "runtime_absolute"]
    load_address: int
    entrypoint: int
    code_start_offset: int
    display_path: str
    analysis_cache_path: Path
    parent_disk_id: str | None = None

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()

    @property
    def code_start_address(self) -> int:
        return self.load_address + self.code_start_offset

    @property
    def analysis_base_addr(self) -> int:
        if self.address_model == "local_offset":
            return 0
        return self.load_address

    @property
    def analysis_entrypoint(self) -> int:
        if self.address_model == "local_offset":
            return self.local_entrypoint
        return self.entrypoint

    @property
    def local_entrypoint(self) -> int:
        return self.entrypoint - self.load_address


type BinarySource = HunkFileBinarySource | DiskEntryBinarySource | RawBinarySource


def source_descriptor_path(target_dir: Path) -> Path:
    return target_dir / SOURCE_DESCRIPTOR_FILE_NAME


def write_source_descriptor(target_dir: Path, payload: dict[str, object]) -> None:
    source_descriptor_path(target_dir).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _resolve_recorded_path(recorded_path: str, project_root: Path) -> Path:
    candidate = Path(recorded_path)
    if not candidate.exists():
        candidate = (project_root / recorded_path).resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"Recorded source path does not exist: {recorded_path}")
    return candidate


def _load_hunk_file_source(
    payload: dict[str, object],
    target_dir: Path,
    project_root: Path,
) -> HunkFileBinarySource:
    path = payload["path"]
    parent_disk_id = payload.get("parent_disk_id")
    assert isinstance(path, str)
    assert parent_disk_id is None or isinstance(parent_disk_id, str)
    resolved_path = _resolve_recorded_path(path, project_root)
    return HunkFileBinarySource(
        kind="hunk_file",
        path=resolved_path,
        display_path=path,
        analysis_cache_path=target_dir / "binary.analysis",
        parent_disk_id=parent_disk_id,
    )


def _load_disk_entry_source(
    payload: dict[str, object],
    target_dir: Path,
    project_root: Path,
) -> DiskEntryBinarySource:
    disk_id = payload["disk_id"]
    disk_path = payload["disk_path"]
    entry_path = payload["entry_path"]
    parent_disk_id = payload.get("parent_disk_id")
    assert isinstance(disk_id, str)
    assert isinstance(disk_path, str)
    assert isinstance(entry_path, str)
    assert parent_disk_id is None or isinstance(parent_disk_id, str)
    adf_path = _resolve_recorded_path(disk_path, project_root)
    return DiskEntryBinarySource(
        kind="disk_entry",
        disk_id=disk_id,
        adf_path=adf_path,
        entry_path=entry_path,
        display_path=f"{adf_path.as_posix()}::{entry_path}",
        analysis_cache_path=target_dir / "binary.analysis",
        parent_disk_id=parent_disk_id,
    )


def _load_raw_binary_source(
    payload: dict[str, object],
    target_dir: Path,
    project_root: Path,
) -> RawBinarySource:
    path = payload["path"]
    address_model = payload["address_model"]
    load_address = payload["load_address"]
    entrypoint = payload["entrypoint"]
    code_start_offset = payload["code_start_offset"]
    parent_disk_id = payload.get("parent_disk_id")
    assert isinstance(path, str)
    assert isinstance(address_model, str)
    assert isinstance(load_address, int)
    assert isinstance(entrypoint, int)
    assert isinstance(code_start_offset, int)
    assert isinstance(parent_disk_id, str) or parent_disk_id is None
    if address_model not in ("local_offset", "runtime_absolute"):
        raise ValueError(f"Unsupported raw binary address_model for target {target_dir.name}: {address_model}")
    if code_start_offset < 0:
        raise ValueError(f"Raw binary code_start_offset must be non-negative: {code_start_offset}")
    code_start_addr = load_address + code_start_offset
    resolved_path = _resolve_recorded_path(path, project_root)
    file_size = resolved_path.stat().st_size
    if code_start_offset >= file_size:
        raise ValueError(
            f"Raw binary code_start_offset 0x{code_start_offset:X} lies outside file of {file_size} bytes"
        )
    if entrypoint < code_start_addr:
        raise ValueError(
            f"Raw binary entrypoint 0x{entrypoint:X} precedes code start address 0x{code_start_addr:X}"
        )
    code_end_addr = code_start_addr + (file_size - code_start_offset)
    if entrypoint >= code_end_addr:
        raise ValueError(
            f"Raw binary entrypoint 0x{entrypoint:X} lies outside code range "
            f"0x{code_start_addr:X}..0x{code_end_addr - 1:X}"
        )
    return RawBinarySource(
        kind="raw_binary",
        path=resolved_path,
        address_model=cast(Literal["local_offset", "runtime_absolute"], address_model),
        load_address=load_address,
        entrypoint=entrypoint,
        code_start_offset=code_start_offset,
        display_path=path,
        analysis_cache_path=target_dir / "binary.analysis",
        parent_disk_id=parent_disk_id,
    )


def resolve_target_binary_source(target_dir: Path, project_root: Path = PROJECT_ROOT) -> BinarySource | None:
    descriptor_path = source_descriptor_path(target_dir)
    if not descriptor_path.exists():
        return None
    payload = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor = _json_object(payload)
    kind = descriptor["kind"]
    assert isinstance(kind, str)
    if kind == "hunk_file":
        return _load_hunk_file_source(descriptor, target_dir, project_root)
    if kind == "disk_entry":
        return _load_disk_entry_source(descriptor, target_dir, project_root)
    if kind == "raw_binary":
        return _load_raw_binary_source(descriptor, target_dir, project_root)
    raise ValueError(f"Unsupported source_binary kind for target {target_dir.name}: {kind}")


def is_internal_target(target_dir: Path, project_root: Path = PROJECT_ROOT) -> bool:
    descriptor_path = source_descriptor_path(target_dir)
    if not descriptor_path.exists():
        return False
    payload = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor = _json_object(payload)
    parent_disk_id = descriptor.get("parent_disk_id")
    assert parent_disk_id is None or isinstance(parent_disk_id, str)
    return parent_disk_id is not None
