from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Callable
from pathlib import Path

from amiga_reversing.amiga_disk.adf import (
    DiskAnalysisError,
    analyze_adf,
    derive_disk_id,
)
from amiga_reversing.amiga_disk.models import (
    AdfAnalysis,
    BootloaderStage,
    DiskManifest,
    ImportedTarget,
)
from amiga_reversing.disasm.binary_source import write_source_descriptor
from amiga_reversing.disasm.c_backend import (
    analyze_binary_source_with_c_backend,
    decompress_packed_section_range_with_c_backend,
    extract_disk_entry_with_c_backend,
)
from amiga_reversing.disasm.project_ids import (
    disk_child_project_id,
    disk_child_target_relpath,
    disk_project_root,
    disk_project_targets_dir,
    raw_target_id,
    target_output_stem,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def _materialized_bootloader_disk_stage_targets(
    analysis: AdfAnalysis,
    disk_bytes: bytes,
) -> list[tuple[BootloaderStage, bytes]]:
    if analysis.bootloader_analysis is None:
        return []
    stage_targets: list[tuple[BootloaderStage, bytes]] = []
    for stage in analysis.bootloader_analysis.stages:
        import_target = stage.import_target
        if import_target is None or import_target.source is None:
            continue
        source = import_target.source
        start = source.get("byte_offset")
        size = source.get("byte_size")
        if not isinstance(start, int) or not isinstance(size, int):
            raise DiskAnalysisError(f"Bootloader stage import target has invalid source span: {stage.name}")
        end = start + size
        if start < 0 or end > len(disk_bytes):
            continue
        stage_targets.append((stage, disk_bytes[start:end]))
    return stage_targets


def _unique_bootloader_raw_span_targets(
    analysis: AdfAnalysis,
    disk_bytes: bytes,
) -> list[tuple[BootloaderStage, int, bytes]]:
    if analysis.bootloader_analysis is None:
        return []
    span_targets: list[tuple[BootloaderStage, int, bytes]] = []
    for stage in analysis.bootloader_analysis.stages:
        for span_index, region in enumerate(stage.decode_regions):
            import_target = region.import_target
            if import_target is None or import_target.source is None:
                continue
            source = import_target.source
            start = source.get("byte_offset")
            size = source.get("byte_size")
            if not isinstance(start, int) or not isinstance(size, int):
                raise DiskAnalysisError(f"Bootloader raw span import target has invalid source span: {stage.name}")
            end = start + size
            if start < 0 or end > len(disk_bytes):
                continue
            span_targets.append((stage, span_index, disk_bytes[start:end]))
    return span_targets


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _int_field(payload: dict[str, object], key: str) -> int | None:
    value = payload.get(key)
    return value if isinstance(value, int) else None


def _str_field(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value else None


def _decompressed_payload_child_local_id(
    parent_local_target_id: str,
    suggestion: dict[str, object],
) -> str:
    codec_raw = _str_field(suggestion, "codec_id") or "packed"
    codec = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in codec_raw)
    codec = codec.strip("._-").replace("-", "_") or "packed"
    section = _int_field(suggestion, "source_section") or 0
    offset = _int_field(suggestion, "source_section_offset") or 0
    stem = target_output_stem(parent_local_target_id)
    candidate = f"{stem}_{codec}_{section:02x}_{offset:08x}"
    if len(candidate) > 71:
        candidate = candidate[:71].rstrip("._-")
    return raw_target_id(candidate)


def _materializable_decompression_suggestions(analysis: dict[str, object]) -> list[dict[str, object]]:
    suggestions = analysis.get("derived_target_suggestions")
    if not isinstance(suggestions, list):
        return []
    materializable: list[dict[str, object]] = []
    for item in suggestions:
        if not isinstance(item, dict):
            continue
        if item.get("kind") != "decompressed_payload":
            continue
        if item.get("status") == "needs_runtime_metadata":
            continue
        if _int_field(item, "source_section") is None:
            continue
        if _int_field(item, "source_section_offset") is None:
            continue
        if _int_field(item, "packed_size") is None:
            continue
        if _int_field(item, "decompressed_size") is None:
            continue
        if _int_field(item, "load_address") is None:
            continue
        if _int_field(item, "entrypoint") is None:
            continue
        materializable.append(dict(item))
    return materializable


def _target_type_may_contain_packed_payload(target_type: str) -> bool:
    return target_type in {"program", "library"}


def _materialize_decompressed_payload_children(
    *,
    adf_file: Path,
    disk_id: str,
    disk_children_root: Path,
    parent_local_target_id: str,
    parent_target_name: str,
    parent_entry_path: str,
    project_root: Path,
) -> tuple[list[dict[str, object]], list[ImportedTarget], list[Path]]:
    from amiga_reversing.disasm.projects import create_project_at_path, mark_project_updated

    try:
        parent_bytes = extract_disk_entry_with_c_backend(adf_file, parent_entry_path, project_root=project_root)
    except Exception:
        return [], [], []
    parent_temp_path = disk_children_root / f".{parent_local_target_id}.decompression-parent.bin"
    created_dirs: list[Path] = []
    parent_derived: list[dict[str, object]] = []
    child_targets: list[ImportedTarget] = []
    _write_bytes(parent_temp_path, parent_bytes)
    try:
        try:
            analysis = analyze_binary_source_with_c_backend(parent_temp_path, project_root=project_root)
        except Exception:
            return [], [], []
        for suggestion in _materializable_decompression_suggestions(analysis):
            source_section = _int_field(suggestion, "source_section")
            source_section_offset = _int_field(suggestion, "source_section_offset")
            packed_size = _int_field(suggestion, "packed_size")
            decompressed_size = _int_field(suggestion, "decompressed_size")
            load_address = _int_field(suggestion, "load_address")
            entrypoint = _int_field(suggestion, "entrypoint")
            assert source_section is not None
            assert source_section_offset is not None
            assert packed_size is not None
            assert decompressed_size is not None
            assert load_address is not None
            assert entrypoint is not None
            local_target_id = _decompressed_payload_child_local_id(parent_local_target_id, suggestion)
            target_name = disk_child_project_id(disk_id, local_target_id)
            target_dir = disk_children_root / local_target_id
            if target_dir.exists():
                continue
            child_entry_path = (
                f"{parent_entry_path}::{_str_field(suggestion, 'codec_id') or 'decompressed'}_"
                f"{source_section_offset:08x}"
            )
            create_project_at_path(
                disk_child_target_relpath(disk_id, local_target_id).as_posix(),
                project_root=project_root,
                origin={
                    "kind": "derived_decompressed_payload",
                    "parent_disk_id": disk_id,
                    "parent_target": parent_target_name,
                    "parent_entry_path": parent_entry_path,
                    "child_entry_path": child_entry_path,
                    "target_role": "decompressed_payload",
                    "target_type": "raw_binary",
                    "codec_id": _str_field(suggestion, "codec_id"),
                    "codec_name": _str_field(suggestion, "codec_name"),
                    "packed_section_offset": source_section_offset,
                    "packed_size": packed_size,
                    "decompressed_size": decompressed_size,
                    "load_address": load_address,
                    "entrypoint": entrypoint,
                },
            )
            created_dirs.append(target_dir)
            output_path = target_dir / "binary.bin"
            result = decompress_packed_section_range_with_c_backend(
                "amiga-hunk",
                parent_temp_path,
                source_section,
                source_section_offset,
                packed_size,
                output_path,
                project_root=project_root,
            )
            packed_payloads = result.get("packed_payloads")
            packed_payload = packed_payloads[0] if isinstance(packed_payloads, list) and packed_payloads else {}
            if not isinstance(packed_payload, dict) or packed_payload.get("found") is not True:
                raise DiskAnalysisError(f"C decompression did not materialise {child_entry_path}")
            source_sha256 = _str_field(packed_payload, "source_sha256") or _str_field(suggestion, "source_sha256")
            decompressed_sha256 = (
                _str_field(packed_payload, "decompressed_sha256")
                or _str_field(suggestion, "decompressed_sha256")
            )
            write_source_descriptor(
                target_dir,
                {
                    "kind": "raw_binary",
                    "address_model": "runtime_absolute",
                    "path": output_path.relative_to(project_root).as_posix(),
                    "load_address": load_address,
                    "entrypoint": entrypoint,
                    "code_start_offset": _int_field(suggestion, "code_start_offset") or 0,
                    "parent_disk_id": disk_id,
                },
            )
            write_target_metadata(target_dir, TargetMetadata(target_type="raw_binary", entry_register_seeds=()))
            relationship = {
                "kind": "decompressed_payload",
                "parent_target": parent_target_name,
                "parent_entry_path": parent_entry_path,
                "child_target": target_name,
                "child_entry_path": child_entry_path,
                "packed_section_offset": source_section_offset,
                "packed_size": packed_size,
                "decompressed_size": decompressed_size,
                "load_address": load_address,
                "entrypoint": entrypoint,
                "codec_id": _str_field(suggestion, "codec_id"),
                "codec_name": _str_field(suggestion, "codec_name"),
            }
            decompression_record = {
                "schema_version": 1,
                "parent_target_id": parent_target_name,
                "child_target_id": target_name,
                "parent_entry_path": parent_entry_path,
                "child_entry_path": child_entry_path,
                "compressor": {
                    "id": _str_field(suggestion, "codec_id"),
                    "name": _str_field(suggestion, "codec_name"),
                    "confidence": _str_field(packed_payload, "confidence") or "provider-identified",
                },
                "packed": {
                    "section_offset": source_section_offset,
                    "size": packed_size,
                    "sha256": source_sha256,
                },
                "decompressed": {
                    "size": decompressed_size,
                    "sha256": decompressed_sha256,
                    "load_address": load_address,
                    "entrypoint": entrypoint,
                },
                "extraction": {
                    "method": _str_field(packed_payload, "provider_id") or "ancient-cli",
                    "tool": _str_field(packed_payload, "provider_path"),
                },
                "relationship": relationship,
            }
            _write_text(
                target_dir / "decompression.json",
                json.dumps(decompression_record, indent=2, sort_keys=True) + "\n",
            )
            mark_project_updated(target_dir)
            parent_derived.append(
                {
                    "kind": "decompressed_payload",
                    "target_name": target_name,
                    "packed_section_offset": source_section_offset,
                    "packed_size": packed_size,
                    "codec_id": _str_field(suggestion, "codec_id"),
                }
            )
            child_targets.append(
                ImportedTarget(
                    target_name=target_name,
                    target_path=disk_child_target_relpath(disk_id, local_target_id).as_posix(),
                    entry_path=child_entry_path,
                    binary_path=output_path.relative_to(project_root).as_posix(),
                    target_type="raw_binary",
                    derived_from=relationship,
                )
            )
    except Exception:
        for target_dir in reversed(created_dirs):
            shutil.rmtree(target_dir, ignore_errors=True)
        raise
    finally:
        try:
            parent_temp_path.unlink()
        except FileNotFoundError:
            pass
    return parent_derived, child_targets, created_dirs


def _has_dos_filesystem(analysis: AdfAnalysis) -> bool:
    return analysis.filesystem is not None


def _require_complete_dos_analysis(analysis: AdfAnalysis) -> None:
    if analysis.root_block is None:
        raise DiskAnalysisError("DOS analysis is missing root block")
    if analysis.files is None:
        raise DiskAnalysisError("DOS analysis is missing file inventory")
    if analysis.directories is None:
        raise DiskAnalysisError("DOS analysis is missing directory inventory")
    if analysis.bitmap is None:
        raise DiskAnalysisError("DOS analysis is missing bitmap summary")
    if analysis.block_usage is None:
        raise DiskAnalysisError("DOS analysis is missing block usage summary")


def _import_target_required_text(value: str | None, field_name: str, target_type: str) -> str:
    if value is None or value == "":
        raise DiskAnalysisError(f"C disk inspect {target_type} import target is missing {field_name}")
    return value


def create_disk_project(
    adf_path: str | Path,
    *,
    disk_id: str | None = None,
    project_root: Path = PROJECT_ROOT,
    progress_fn: Callable[[str, int, int], None] | None = None,
    origin: dict[str, object] | None = None,
) -> DiskManifest:
    from amiga_reversing.disasm.projects import (
        create_project_at_path,
        initialize_project_metadata,
        mark_project_updated,
    )

    adf_file = Path(adf_path)
    resolved_disk_id = disk_id or derive_disk_id(adf_file)
    disk_target_root = disk_project_root(project_root, resolved_disk_id)
    disk_children_root = disk_project_targets_dir(project_root, resolved_disk_id)
    manifest_path = disk_target_root / "manifest.json"
    if disk_target_root.exists():
        raise DiskAnalysisError(f"Disk target root already exists: {disk_target_root}")
    disk_target_root.mkdir(parents=True)
    created_target_dirs: list[Path] = []
    try:
        disk_bytes = adf_file.read_bytes()
        disk_sha256 = hashlib.sha256(disk_bytes).hexdigest()
        disk_origin = origin or {
            "kind": "user_upload",
            "filename": adf_file.name,
            "platform": "amiga-disk",
            "source_path": adf_file.as_posix(),
            "sha256": disk_sha256,
            "size": len(disk_bytes),
        }
        initialize_project_metadata(disk_target_root, origin=disk_origin)
        if progress_fn is not None:
            progress_fn("analyze_disk", 1, 4)
        analysis = analyze_adf(adf_file, include_tracks=True)

        if progress_fn is not None:
            progress_fn("create_bootblock_target", 2, 4)
        bootblock_import = analysis.boot_block.import_target
        if bootblock_import is None or bootblock_import.source is None:
            raise DiskAnalysisError("C disk inspect output is missing bootblock import target")
        bootblock_source = dict(bootblock_import.source)
        bootblock_byte_offset = bootblock_source.pop("byte_offset")
        bootblock_byte_size = bootblock_source.pop("byte_size")
        if not isinstance(bootblock_byte_offset, int) or not isinstance(bootblock_byte_size, int):
            raise DiskAnalysisError("C disk inspect bootblock source byte span is invalid")
        bootblock_local_name = _import_target_required_text(
            bootblock_import.local_target_id, "local_target_id", "bootblock"
        )
        bootblock_target_name = disk_child_project_id(resolved_disk_id, bootblock_local_name)
        bootblock_target_dir = disk_children_root / bootblock_local_name
        if bootblock_target_dir.exists():
            raise DiskAnalysisError(f"Target already exists: {bootblock_target_name}")
        create_project_at_path(
            disk_child_target_relpath(resolved_disk_id, bootblock_local_name).as_posix(),
            project_root=project_root,
            origin={
                "kind": "disk_child",
                "parent_disk_id": resolved_disk_id,
                "target_role": "bootblock",
                "target_type": "bootblock",
                "source_path": adf_file.as_posix(),
            },
        )
        created_target_dirs.append(bootblock_target_dir)
        bootblock_binary_path = bootblock_target_dir / "binary.bin"
        _write_bytes(bootblock_binary_path, disk_bytes[bootblock_byte_offset:bootblock_byte_offset + bootblock_byte_size])
        bootblock_source["path"] = bootblock_binary_path.relative_to(project_root).as_posix()
        bootblock_source["parent_disk_id"] = resolved_disk_id
        write_source_descriptor(bootblock_target_dir, bootblock_source)
        write_target_metadata(bootblock_target_dir, TargetMetadata.from_dict(bootblock_import.target_metadata))
        mark_project_updated(bootblock_target_dir)

        imported_targets: list[ImportedTarget] = []
        for stage, stage_bytes in _materialized_bootloader_disk_stage_targets(analysis, disk_bytes):
            assert stage.import_target is not None
            assert stage.import_target.source is not None
            stage_entry_path = _import_target_required_text(
                stage.import_target.entry_path, "entry_path", stage.import_target.target_type
            )
            local_target_name = _import_target_required_text(
                stage.import_target.local_target_id, "local_target_id", stage.import_target.target_type
            )
            target_name = disk_child_project_id(resolved_disk_id, local_target_name)
            target_dir = disk_children_root / local_target_name
            if target_dir.exists():
                raise DiskAnalysisError(f"Target already exists: {target_name}")
            create_project_at_path(
                disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                project_root=project_root,
                origin={
                    "kind": "disk_child",
                    "parent_disk_id": resolved_disk_id,
                    "target_role": "bootloader_stage",
                    "entry_path": stage_entry_path,
                    "target_type": stage.import_target.target_type,
                    "source_path": adf_file.as_posix(),
                },
            )
            created_target_dirs.append(target_dir)
            binary_path = target_dir / "binary.bin"
            _write_bytes(binary_path, stage_bytes)
            source_descriptor = dict(stage.import_target.source)
            source_descriptor.pop("byte_offset", None)
            source_descriptor.pop("byte_size", None)
            source_descriptor["path"] = binary_path.relative_to(project_root).as_posix()
            source_descriptor["parent_disk_id"] = resolved_disk_id
            write_source_descriptor(target_dir, source_descriptor)
            write_target_metadata(target_dir, TargetMetadata.from_dict(stage.import_target.target_metadata))
            mark_project_updated(target_dir)
            imported_targets.append(
                ImportedTarget(
                    target_name=target_name,
                    target_path=disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                    entry_path=stage_entry_path,
                    binary_path=f"{adf_file.as_posix()}::{stage_entry_path}",
                    target_type=stage.import_target.target_type,
                )
            )
        for stage, span_index, span_bytes in _unique_bootloader_raw_span_targets(analysis, disk_bytes):
            import_target = stage.decode_regions[span_index].import_target
            assert import_target is not None
            assert import_target.source is not None
            span_entry_path = _import_target_required_text(import_target.entry_path, "entry_path", import_target.target_type)
            local_target_name = _import_target_required_text(
                import_target.local_target_id, "local_target_id", import_target.target_type
            )
            target_name = disk_child_project_id(resolved_disk_id, local_target_name)
            target_dir = disk_children_root / local_target_name
            if target_dir.exists():
                raise DiskAnalysisError(f"Target already exists: {target_name}")
            create_project_at_path(
                disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                project_root=project_root,
                origin={
                    "kind": "disk_child",
                    "parent_disk_id": resolved_disk_id,
                    "target_role": "bootloader_raw_span",
                    "entry_path": span_entry_path,
                    "target_type": import_target.target_type,
                    "source_path": adf_file.as_posix(),
                },
            )
            created_target_dirs.append(target_dir)
            binary_path = target_dir / "binary.bin"
            _write_bytes(binary_path, span_bytes)
            source_descriptor = dict(import_target.source)
            source_descriptor.pop("byte_offset", None)
            source_descriptor.pop("byte_size", None)
            source_descriptor["path"] = binary_path.relative_to(project_root).as_posix()
            source_descriptor["parent_disk_id"] = resolved_disk_id
            write_source_descriptor(target_dir, source_descriptor)
            write_target_metadata(target_dir, TargetMetadata.from_dict(import_target.target_metadata))
            mark_project_updated(target_dir)
            imported_targets.append(
                ImportedTarget(
                    target_name=target_name,
                    target_path=disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                    entry_path=span_entry_path,
                    binary_path=f"{adf_file.as_posix()}::{span_entry_path}",
                    target_type=import_target.target_type,
                )
            )
        if _has_dos_filesystem(analysis):
            _require_complete_dos_analysis(analysis)
            if progress_fn is not None:
                progress_fn("import_targets", 3, 4)
            assert analysis.files is not None
            for entry in analysis.files:
                if entry.content is None:
                    raise DiskAnalysisError(f"Extracted file is missing content classification: {entry.full_path}")
                import_target = entry.content.import_target
                if import_target is None:
                    continue
                local_target_name = _import_target_required_text(
                    import_target.local_target_id, "local_target_id", import_target.target_type
                )
                entry_path = _import_target_required_text(import_target.entry_path, "entry_path", import_target.target_type)
                target_name = disk_child_project_id(resolved_disk_id, local_target_name)
                target_dir = disk_children_root / local_target_name
                if target_dir.exists():
                    raise DiskAnalysisError(f"Target already exists: {target_name}")
                create_project_at_path(
                    disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                    project_root=project_root,
                    origin={
                        "kind": "disk_child",
                        "parent_disk_id": resolved_disk_id,
                        "target_role": "disk_entry",
                        "entry_path": entry_path,
                        "target_type": import_target.target_type,
                        "source_path": adf_file.as_posix(),
                    },
                )
                created_target_dirs.append(target_dir)
                write_source_descriptor(
                    target_dir,
                    {
                        "kind": "disk_entry",
                        "disk_id": resolved_disk_id,
                        "disk_path": adf_file.as_posix(),
                        "entry_path": entry_path,
                        "parent_disk_id": resolved_disk_id,
                    },
                )
                write_target_metadata(target_dir, TargetMetadata.from_dict(import_target.target_metadata))
                mark_project_updated(target_dir)
                parent_derived: list[dict[str, object]] = []
                child_targets: list[ImportedTarget] = []
                child_dirs: list[Path] = []
                if _target_type_may_contain_packed_payload(import_target.target_type):
                    parent_derived, child_targets, child_dirs = _materialize_decompressed_payload_children(
                        adf_file=adf_file,
                        disk_id=resolved_disk_id,
                        disk_children_root=disk_children_root,
                        parent_local_target_id=local_target_name,
                        parent_target_name=target_name,
                        parent_entry_path=entry_path,
                        project_root=project_root,
                    )
                created_target_dirs.extend(child_dirs)
                imported_targets.append(
                    ImportedTarget(
                        target_name=target_name,
                        target_path=disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                        entry_path=entry_path,
                        binary_path=f"{adf_file.as_posix()}::{entry_path}",
                        target_type=import_target.target_type,
                        derived_targets=parent_derived or None,
                    )
                )
                imported_targets.extend(child_targets)

        if progress_fn is not None:
            progress_fn("write_manifest", 4, 4)
        imported_targets.sort(key=lambda target: target.entry_path)
        manifest = DiskManifest(
            schema_version=1,
            disk_id=resolved_disk_id,
            source_path=adf_file.as_posix(),
            source_sha256=disk_sha256,
            analysis=analysis,
            imported_targets=imported_targets,
            bootblock_target_name=bootblock_target_name,
            bootblock_target_path=disk_child_target_relpath(resolved_disk_id, bootblock_local_name).as_posix(),
        )
        _write_text(manifest_path, json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n")
        mark_project_updated(disk_target_root)
        return manifest
    except Exception:
        for target_dir in reversed(created_target_dirs):
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.rmtree(disk_target_root, ignore_errors=True)
        raise


def import_adf(
    adf_path: str | Path,
    *,
    disk_id: str | None = None,
    project_root: Path = PROJECT_ROOT,
    progress_fn: Callable[[str, int, int], None] | None = None,
) -> DiskManifest:
    return create_disk_project(adf_path, disk_id=disk_id, project_root=project_root, progress_fn=progress_fn)
