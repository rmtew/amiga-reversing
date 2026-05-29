from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DESCRIPTOR_FILE_NAME = "source_binary.json"
_DISK_ENTRY_BYTES_CACHE: dict[tuple[str, str, str, int, int], bytes] = {}


class BinarySourceKind(StrEnum):
    HUNK_FILE = "hunk_file"
    DISK_ENTRY = "disk_entry"
    RAW_BINARY = "raw_binary"
    MACOS_CODE_RESOURCE = "macos_code_resource"


class RawAddressModel(StrEnum):
    LOCAL_OFFSET = "local_offset"
    RUNTIME_ABSOLUTE = "runtime_absolute"


class MacosCodeAddressModel(StrEnum):
    RESOURCE_OFFSET = "macos_code_resource_offset"


def _json_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object, got {type(value).__name__}")
    return cast(dict[str, object], value)


@dataclass(frozen=True, slots=True)
class HunkFileBinarySource:
    kind: BinarySourceKind
    path: Path
    display_path: str
    analysis_cache_path: Path
    parent_disk_id: str | None = None

    def __post_init__(self) -> None:
        if self.kind is not BinarySourceKind.HUNK_FILE:
            raise TypeError("HunkFileBinarySource.kind must be BinarySourceKind.HUNK_FILE")

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()


@dataclass(frozen=True, slots=True)
class DiskEntryBinarySource:
    kind: BinarySourceKind
    disk_id: str
    adf_path: Path
    entry_path: str
    display_path: str
    analysis_cache_path: Path
    parent_disk_id: str | None = None
    project_root: Path = PROJECT_ROOT

    def __post_init__(self) -> None:
        if self.kind is not BinarySourceKind.DISK_ENTRY:
            raise TypeError("DiskEntryBinarySource.kind must be BinarySourceKind.DISK_ENTRY")

    def read_bytes(self) -> bytes:
        from amiga_reversing.disasm.c_backend import extract_disk_entry_with_c_backend

        try:
            stat = self.adf_path.stat()
        except OSError:
            stat = None
        key = None
        if stat is not None:
            key = (
                str(self.project_root.resolve()),
                str(self.adf_path.resolve()),
                self.entry_path,
                stat.st_size,
                stat.st_mtime_ns,
            )
            cached = _DISK_ENTRY_BYTES_CACHE.get(key)
            if cached is not None:
                return cached
        data = extract_disk_entry_with_c_backend(
            self.adf_path,
            self.entry_path,
            project_root=self.project_root,
        )
        if not isinstance(data, bytes):
            raise TypeError("C backend disk entry extraction did not return bytes")
        if key is not None:
            _DISK_ENTRY_BYTES_CACHE[key] = data
        return data


@dataclass(frozen=True, slots=True)
class RawBinarySource:
    kind: BinarySourceKind
    path: Path
    address_model: RawAddressModel
    load_address: int
    entrypoint: int
    code_start_offset: int
    display_path: str
    analysis_cache_path: Path
    parent_disk_id: str | None = None

    def __post_init__(self) -> None:
        if self.kind is not BinarySourceKind.RAW_BINARY:
            raise TypeError("RawBinarySource.kind must be BinarySourceKind.RAW_BINARY")
        if not isinstance(self.address_model, RawAddressModel):
            raise TypeError("RawBinarySource.address_model must be a RawAddressModel")

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()

    @property
    def code_start_address(self) -> int:
        return self.load_address + self.code_start_offset

    @property
    def analysis_base_addr(self) -> int:
        if self.address_model is RawAddressModel.LOCAL_OFFSET:
            return 0
        return self.load_address

    @property
    def analysis_entrypoint(self) -> int:
        if self.address_model is RawAddressModel.LOCAL_OFFSET:
            return self.local_entrypoint
        return self.entrypoint

    @property
    def local_entrypoint(self) -> int:
        return self.entrypoint - self.load_address


@dataclass(frozen=True, slots=True)
class MacosCodeResourceSource:
    kind: BinarySourceKind
    source_image: Path
    hfs_path: str
    resource_type: str
    resource_id: int
    address_model: MacosCodeAddressModel
    display_path: str
    analysis_cache_path: Path
    resource_name: str | None = None
    cache_identity: str | None = None
    parent_project_id: str | None = None
    project_root: Path = PROJECT_ROOT

    def __post_init__(self) -> None:
        if self.kind is not BinarySourceKind.MACOS_CODE_RESOURCE:
            raise TypeError("MacosCodeResourceSource.kind must be BinarySourceKind.MACOS_CODE_RESOURCE")
        if self.resource_type != "CODE":
            raise ValueError(f"MacosCodeResourceSource.resource_type must be CODE: {self.resource_type}")
        if self.resource_id < 0:
            raise ValueError(f"MacosCodeResourceSource.resource_id must be non-negative: {self.resource_id}")
        if not isinstance(self.address_model, MacosCodeAddressModel):
            raise TypeError("MacosCodeResourceSource.address_model must be a MacosCodeAddressModel")

    @property
    def stable_cache_identity(self) -> str:
        if self.cache_identity:
            return self.cache_identity
        return macos_code_resource_cache_identity(
            self.source_image.as_posix(),
            self.hfs_path,
            self.resource_type,
            self.resource_id,
        )


type BinarySource = HunkFileBinarySource | DiskEntryBinarySource | RawBinarySource | MacosCodeResourceSource


def read_binary_source_bytes(binary_source: BinarySource) -> bytes:
    if isinstance(binary_source, MacosCodeResourceSource):
        from amiga_reversing.disasm.c_backend import (
            extract_macos_hfs_code_resource_bytes_with_c_backend,
        )
        from amiga_reversing.disasm.macos_image import read_macos_hfs_image_bytes

        hfs_bytes = read_macos_hfs_image_bytes(binary_source.source_image)
        return extract_macos_hfs_code_resource_bytes_with_c_backend(
            hfs_bytes,
            binary_source.hfs_path,
            binary_source.resource_id,
            project_root=binary_source.project_root,
        )
    return binary_source.read_bytes()


def macos_code_resource_cache_identity(
    source_image: str,
    hfs_path: str,
    resource_type: str,
    resource_id: int,
) -> str:
    return f"macos-code-resource:{source_image}:{hfs_path}:{resource_type}:{resource_id}"


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
        kind=BinarySourceKind.HUNK_FILE,
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
        kind=BinarySourceKind.DISK_ENTRY,
        disk_id=disk_id,
        adf_path=adf_path,
        entry_path=entry_path,
        display_path=f"{adf_path.as_posix()}::{entry_path}",
        analysis_cache_path=target_dir / "binary.analysis",
        parent_disk_id=parent_disk_id,
        project_root=project_root,
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
    try:
        address_model_id = RawAddressModel(address_model)
    except ValueError:
        raise ValueError(f"Unsupported raw binary address_model for target {target_dir.name}: {address_model}") from None
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
        kind=BinarySourceKind.RAW_BINARY,
        path=resolved_path,
        address_model=address_model_id,
        load_address=load_address,
        entrypoint=entrypoint,
        code_start_offset=code_start_offset,
        display_path=path,
        analysis_cache_path=target_dir / "binary.analysis",
        parent_disk_id=parent_disk_id,
    )


def _load_macos_code_resource_source(
    payload: dict[str, object],
    target_dir: Path,
    project_root: Path,
) -> MacosCodeResourceSource:
    source_image = payload["source_image"]
    hfs_path = payload["hfs_path"]
    resource_type = payload.get("resource_type", "CODE")
    resource_id = payload["resource_id"]
    address_model = payload["address_model"]
    resource_name = payload.get("resource_name")
    cache_identity = payload.get("cache_identity")
    parent_project_id = payload.get("parent_project_id")
    assert isinstance(source_image, str)
    assert isinstance(hfs_path, str)
    assert isinstance(resource_type, str)
    assert isinstance(resource_id, int)
    assert isinstance(address_model, str)
    assert isinstance(resource_name, str) or resource_name is None
    assert isinstance(cache_identity, str) or cache_identity is None
    assert isinstance(parent_project_id, str) or parent_project_id is None
    try:
        address_model_id = MacosCodeAddressModel(address_model)
    except ValueError:
        raise ValueError(
            f"Unsupported Mac CODE address_model for target {target_dir.name}: {address_model}"
        ) from None
    resolved_image = _resolve_recorded_path(source_image, project_root)
    return MacosCodeResourceSource(
        kind=BinarySourceKind.MACOS_CODE_RESOURCE,
        source_image=resolved_image,
        hfs_path=hfs_path,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        address_model=address_model_id,
        display_path=f"{source_image}::{hfs_path}::{resource_type} {resource_id}",
        analysis_cache_path=target_dir / "binary.analysis",
        cache_identity=cache_identity
        or macos_code_resource_cache_identity(source_image, hfs_path, resource_type, resource_id),
        parent_project_id=parent_project_id,
        project_root=project_root,
    )


def resolve_target_binary_source(target_dir: Path, project_root: Path = PROJECT_ROOT) -> BinarySource | None:
    descriptor_path = source_descriptor_path(target_dir)
    if not descriptor_path.exists():
        return None
    payload = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor = _json_object(payload)
    kind = descriptor["kind"]
    assert isinstance(kind, str)
    try:
        kind_id = BinarySourceKind(kind)
    except ValueError:
        raise ValueError(f"Unsupported source_binary kind for target {target_dir.name}: {kind}") from None
    if kind_id is BinarySourceKind.HUNK_FILE:
        return _load_hunk_file_source(descriptor, target_dir, project_root)
    if kind_id is BinarySourceKind.DISK_ENTRY:
        return _load_disk_entry_source(descriptor, target_dir, project_root)
    if kind_id is BinarySourceKind.RAW_BINARY:
        return _load_raw_binary_source(descriptor, target_dir, project_root)
    if kind_id is BinarySourceKind.MACOS_CODE_RESOURCE:
        return _load_macos_code_resource_source(descriptor, target_dir, project_root)
    raise AssertionError(f"Unhandled source_binary kind: {kind_id}")


def is_internal_target(target_dir: Path, project_root: Path = PROJECT_ROOT) -> bool:
    descriptor_path = source_descriptor_path(target_dir)
    if not descriptor_path.exists():
        return False
    payload = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor = _json_object(payload)
    parent_disk_id = descriptor.get("parent_disk_id")
    assert parent_disk_id is None or isinstance(parent_disk_id, str)
    return parent_disk_id is not None
