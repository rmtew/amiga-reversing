from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.amiga_disk.models import (
    AdfAnalysis,
    BitmapInfo,
    BlockUsageInfo,
    BootBlockInfo,
    BootloaderAnalysis,
    DiskDirectoryEntry,
    DiskFileEntry,
    DiskInfo,
    FileContentInfo,
    FilesystemInfo,
    NonDosInfo,
    RootBlockInfo,
    TrackAnalysis,
    TrackloaderAnalysis,
)
from amiga_reversing.disasm.c_backend import (
    extract_disk_entry_with_c_backend,
    inspect_disk_with_c_backend,
)
from amiga_reversing.disasm.project_ids import (
    derive_disk_id_from_stem,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT


class DiskAnalysisError(ValueError):
    """Raised when disk analysis or import cannot proceed."""


@dataclass(frozen=True, slots=True)
class DosFilesystem:
    boot: BootBlockInfo
    root: RootBlockInfo
    directories: list[DiskDirectoryEntry]
    files: list[DiskFileEntry]
    bitmap: BitmapInfo
    block_usage: BlockUsageInfo


def _bool_from_c_json(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    raise DiskAnalysisError(f"Expected C disk boolean, got {value!r}")


def _boot_block_from_c_disk_inspect(payload: dict[str, object]) -> BootBlockInfo:
    boot_payload = payload.get("boot_block")
    if not isinstance(boot_payload, dict):
        raise DiskAnalysisError("C disk inspect output is missing boot_block")
    boot = dict(boot_payload)
    magic_bytes = boot.get("magic_bytes")
    if isinstance(magic_bytes, list) and len(magic_bytes) >= 3 and all(isinstance(item, int) for item in magic_bytes[:3]):
        boot["magic_ascii"] = bytes(magic_bytes[:3]).decode("latin-1", errors="replace")
    boot["is_dos"] = _bool_from_c_json(boot.get("is_dos"))
    boot["checksum_valid"] = _bool_from_c_json(boot.get("checksum_valid"))
    boot["bootcode_has_code"] = _bool_from_c_json(boot.get("bootcode_has_code"))
    return BootBlockInfo.from_dict(boot)


def _non_dos_analysis(
    boot: BootBlockInfo,
    filesystem_parse_error: str | None = None,
) -> NonDosInfo:
    return NonDosInfo(
        description="Custom format disk (non-AmigaDOS)",
        bootcode_present=boot.bootcode_has_code,
        dos_magic_without_filesystem=boot.is_dos,
        filesystem_parse_error=filesystem_parse_error,
    )


def _extract_file(adf_path: Path, entry: DiskFileEntry, output_dir: Path, *, project_root: Path) -> Path:
    destination = output_dir / entry.full_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = extract_disk_entry_with_c_backend(adf_path, entry.full_path, project_root=project_root)
    except Exception as exc:
        raise DiskAnalysisError(f"ADF entry not found: {entry.full_path}") from exc
    destination.write_bytes(payload)
    assert isinstance(destination, Path)
    return destination


def _c_object(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise DiskAnalysisError(f"C disk inspect output is missing {key}")
    return value


def _c_list(payload: dict[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise DiskAnalysisError(f"C disk inspect output is missing {key}")
    return value


def _c_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise DiskAnalysisError(f"C disk inspect field {key} is not an integer")
    return value


def _c_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise DiskAnalysisError(f"C disk inspect field {key} is not a string")
    return value


def _c_optional_str(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None or isinstance(value, str):
        return value
    raise DiskAnalysisError(f"C disk inspect field {key} is not a string")


def _c_optional_object(payload: dict[str, object], key: str) -> dict[str, object] | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    raise DiskAnalysisError(f"C disk inspect field {key} is not an object")


def _c_int_list(payload: dict[str, object], key: str) -> list[int]:
    values = _c_list(payload, key)
    if not all(isinstance(item, int) for item in values):
        raise DiskAnalysisError(f"C disk inspect field {key} is not an integer list")
    return [item for item in values if isinstance(item, int)]


def _root_from_c_disk_inspect(payload: dict[str, object]) -> RootBlockInfo:
    root = _c_object(payload, "root")
    return RootBlockInfo(
        block_num=_c_int(root, "block_num"),
        hash_table=_c_int_list(root, "hash_table"),
        checksum_valid=_bool_from_c_json(root.get("checksum_valid")),
        bm_flag=_c_int(root, "bm_flag"),
        bm_pages=_c_int_list(root, "bm_pages"),
        volume_name=_c_str(root, "volume_name"),
        root_date=_c_str(root, "root_date"),
        volume_date=_c_str(root, "volume_date"),
        creation_date=_c_str(root, "creation_date"),
    )


def _bitmap_from_c_disk_inspect(payload: dict[str, object]) -> BitmapInfo:
    bitmap = _c_object(payload, "bitmap")
    percent_used = bitmap.get("percent_used")
    if not isinstance(percent_used, int | float):
        raise DiskAnalysisError("C disk inspect bitmap percent_used is invalid")
    return BitmapInfo(
        checksum_valid=_bool_from_c_json(bitmap.get("checksum_valid")),
        free_blocks=_c_int(bitmap, "free_blocks"),
        allocated_blocks=_c_int(bitmap, "allocated_blocks"),
        total_blocks=_c_int(bitmap, "total_blocks"),
        percent_used=float(percent_used),
    )


def _block_usage_from_c_disk_inspect(payload: dict[str, object]) -> BlockUsageInfo:
    block_usage = _c_object(payload, "block_usage")
    summary = _c_object(block_usage, "summary")
    if not all(isinstance(key, str) and isinstance(value, int) for key, value in summary.items()):
        raise DiskAnalysisError("C disk inspect block usage summary is invalid")
    return BlockUsageInfo(
        summary={key: value for key, value in summary.items() if isinstance(value, int)},
        orphan_blocks=_c_int_list(block_usage, "orphan_blocks"),
    )


def _track_analysis_from_c_disk_inspect(payload: dict[str, object]) -> TrackAnalysis | None:
    track_payload = payload.get("track_analysis")
    if track_payload is None:
        return None
    if not isinstance(track_payload, dict):
        raise DiskAnalysisError("C disk inspect track_analysis is not an object")
    return TrackAnalysis.from_dict(track_payload)


def _trackloader_analysis_from_c_disk_inspect(payload: dict[str, object]) -> TrackloaderAnalysis | None:
    trackloader_payload = payload.get("trackloader_analysis")
    if trackloader_payload is None:
        return None
    if not isinstance(trackloader_payload, dict):
        raise DiskAnalysisError("C disk inspect trackloader_analysis is not an object")
    return TrackloaderAnalysis.from_dict(trackloader_payload)


def _bootloader_analysis_from_c_disk_inspect(payload: dict[str, object]) -> BootloaderAnalysis:
    bootloader_payload = payload.get("bootloader_analysis")
    if bootloader_payload is None:
        return BootloaderAnalysis(stages=[], memory_regions=[], transfers=[])
    if not isinstance(bootloader_payload, dict):
        raise DiskAnalysisError("C disk inspect bootloader_analysis is not an object")
    return BootloaderAnalysis.from_dict(bootloader_payload)


def _dos_entries_from_c_disk_inspect(payload: dict[str, object]) -> tuple[list[DiskDirectoryEntry], list[DiskFileEntry]]:
    directories: list[DiskDirectoryEntry] = []
    files: list[DiskFileEntry] = []
    for raw_entry in _c_list(payload, "entries"):
        if not isinstance(raw_entry, dict):
            raise DiskAnalysisError("C disk inspect entry is not an object")
        entry = dict(raw_entry)
        kind_name = _c_str(entry, "kind_name")
        if kind_name == "volume":
            continue
        date = _c_str(entry, "date")
        block_num = _c_int(entry, "header_block")
        name = _c_str(entry, "name")
        full_path = _c_str(entry, "path")
        protection = _c_str(entry, "protection")
        comment = _c_optional_str(entry, "comment")
        hash_chain = _c_int(entry, "hash_chain")
        parent = _c_int(entry, "parent")
        checksum_valid = _bool_from_c_json(entry.get("checksum_valid"))
        if kind_name == "directory":
            directories.append(
                DiskDirectoryEntry(
                    block_num=block_num,
                    name=name,
                    full_path=full_path,
                    protection=protection,
                    comment=comment,
                    date=date,
                    hash_chain=hash_chain,
                    parent=parent,
                    checksum_valid=checksum_valid,
                )
            )
        elif kind_name == "file":
            data_blocks = _c_int_list(entry, "data_blocks")
            content = _c_optional_object(entry, "content")
            files.append(
                DiskFileEntry(
                    block_num=block_num,
                    name=name,
                    full_path=full_path,
                    size=_c_int(entry, "byte_size"),
                    protection=protection,
                    comment=comment,
                    date=date,
                    hash_chain=hash_chain,
                    parent=parent,
                    extension_blocks=_c_int_list(entry, "extension_blocks"),
                    data_blocks=data_blocks,
                    data_block_count=len(data_blocks),
                    checksum_valid=checksum_valid,
                    content=None if content is None else FileContentInfo.from_dict(content),
                )
            )
    return directories, files


def _load_dos_filesystem(inspect_payload: dict[str, object], boot: BootBlockInfo) -> DosFilesystem:
    assert boot.is_dos
    root = _root_from_c_disk_inspect(inspect_payload)
    directories, files = _dos_entries_from_c_disk_inspect(inspect_payload)
    return DosFilesystem(
        boot=boot,
        root=root,
        directories=directories,
        files=files,
        bitmap=_bitmap_from_c_disk_inspect(inspect_payload),
        block_usage=_block_usage_from_c_disk_inspect(inspect_payload),
    )


def analyze_adf(
    adf_path: str | Path,
    *,
    extract_dir: str | Path | None = None,
    include_tracks: bool = False,
    kb_root: Path = PROJECT_ROOT,
) -> AdfAnalysis:
    adf_file = Path(adf_path)
    data = adf_file.read_bytes()
    c_disk_inspect = inspect_disk_with_c_backend(adf_file, project_root=kb_root)
    disk_info_payload = _c_object(c_disk_inspect, "disk_info")
    if _c_int(disk_info_payload, "size") != len(data):
        raise DiskAnalysisError("C disk inspect size does not match input")
    boot = _boot_block_from_c_disk_inspect(c_disk_inspect)
    disk_info = DiskInfo(
        path=adf_file.name,
        size=len(data),
        variant=_c_str(disk_info_payload, "variant"),
        total_sectors=_c_int(disk_info_payload, "total_sectors"),
        sectors_per_track=_c_int(disk_info_payload, "sectors_per_track"),
        is_dos=boot.is_dos,
    )

    if not boot.is_dos:
        track_analysis = _track_analysis_from_c_disk_inspect(c_disk_inspect) if include_tracks else None
        trackloader_analysis = _trackloader_analysis_from_c_disk_inspect(c_disk_inspect) if include_tracks else None
        return AdfAnalysis(
            disk_info=disk_info,
            boot_block=boot,
            non_dos=_non_dos_analysis(boot),
            track_analysis=track_analysis,
            trackloader_analysis=trackloader_analysis,
            bootloader_analysis=_bootloader_analysis_from_c_disk_inspect(c_disk_inspect),
        )

    try:
        filesystem = _load_dos_filesystem(c_disk_inspect, boot)
    except DiskAnalysisError as exc:
        track_analysis = _track_analysis_from_c_disk_inspect(c_disk_inspect) if include_tracks else None
        trackloader_analysis = _trackloader_analysis_from_c_disk_inspect(c_disk_inspect) if include_tracks else None
        return AdfAnalysis(
            disk_info=disk_info,
            boot_block=boot,
            non_dos=_non_dos_analysis(boot, filesystem_parse_error=str(exc)),
            track_analysis=track_analysis,
            trackloader_analysis=trackloader_analysis,
            bootloader_analysis=_bootloader_analysis_from_c_disk_inspect(c_disk_inspect),
        )
    root = filesystem.root
    directories = filesystem.directories
    files = filesystem.files
    bitmap = filesystem.bitmap

    extracted_files: list[DiskFileEntry] = files
    if extract_dir is not None:
        output_dir = Path(extract_dir)
        if output_dir.exists():
            raise DiskAnalysisError(f"Extraction directory already exists: {output_dir}")
        output_dir.mkdir(parents=True)
        extracted_entries: list[DiskFileEntry] = []
        for entry in extracted_files:
            extracted_path = _extract_file(adf_file, entry, output_dir, project_root=kb_root)
            extracted_entries.append(
                DiskFileEntry(
                    block_num=entry.block_num,
                    name=entry.name,
                    full_path=entry.full_path,
                    size=entry.size,
                    protection=entry.protection,
                    comment=entry.comment,
                    date=entry.date,
                    hash_chain=entry.hash_chain,
                    parent=entry.parent,
                    extension_blocks=entry.extension_blocks,
                    data_blocks=entry.data_blocks,
                    data_block_count=entry.data_block_count,
                    checksum_valid=entry.checksum_valid,
                    extracted_path=str(extracted_path),
                    content=entry.content,
                )
            )
        extracted_files = extracted_entries

    track_analysis = _track_analysis_from_c_disk_inspect(c_disk_inspect) if include_tracks else None
    trackloader_analysis = _trackloader_analysis_from_c_disk_inspect(c_disk_inspect) if include_tracks else None
    bootloader_analysis = _bootloader_analysis_from_c_disk_inspect(c_disk_inspect)

    return AdfAnalysis(
        disk_info=disk_info,
        boot_block=boot,
        root_block=root,
        filesystem=FilesystemInfo(
            type=boot.fs_type,
            volume_name=root.volume_name,
            directories=len(directories),
            files=len(files),
            total_file_size=sum(entry.size for entry in files),
        ),
        files=extracted_files,
        directories=directories,
        bitmap=bitmap,
        block_usage=filesystem.block_usage,
        track_analysis=track_analysis,
        trackloader_analysis=trackloader_analysis,
        bootloader_analysis=bootloader_analysis,
    )


def derive_disk_id(adf_path: str | Path) -> str:
    try:
        disk_id: str = derive_disk_id_from_stem(Path(adf_path).stem.strip())
        return disk_id
    except ValueError as exc:
        raise DiskAnalysisError(str(exc)) from exc
