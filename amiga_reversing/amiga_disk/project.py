from __future__ import annotations

import contextlib
import datetime
import hashlib
import json
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from amiga_reversing.amiga_disk.adf import (
    DiskAnalysisError,
    analyze_adf,
    derive_disk_id,
)
from amiga_reversing.amiga_disk.models import (
    AdfAnalysis,
    BootloaderDiskCommand,
    BootloaderStage,
    BootloaderTransferSourceKind,
    DiskManifest,
    FileImportTargetInfo,
    ImportedTarget,
)
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    HunkFileBinarySource,
    resolve_target_binary_source,
    write_source_descriptor,
)
from amiga_reversing.disasm.c_backend import (
    analyze_project_source_with_c_backend,
    decompress_packed_section_range_with_c_backend,
    extract_disk_entry_with_c_backend,
    materialize_recognized_unpacker_event_with_c_backend,
    materialize_self_decrunch_event_with_c_backend,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_ids import (
    AMIGA_DISK_PREFIX,
    disk_child_project_id,
    disk_child_target_relpath,
    disk_project_root,
    disk_project_targets_dir,
    raw_target_id,
    target_output_stem,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_local_state import clean_obsolete_target_local_state
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


@dataclass(frozen=True, slots=True)
class MaterializedPayloadChildren:
    parent_derived: list[dict[str, object]]
    child_targets: list[ImportedTarget]
    created_dirs: list[Path]
    analysis_completed: bool


PROJECT_ORIGIN_KIND_DERIVED_DECOMPRESSED_PAYLOAD = 1
TARGET_ROLE_DECOMPRESSED_PAYLOAD = 1
DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD = 1
DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER = 2
DECOMPRESSION_SOURCE_SELF_DECRUNCHER = 3
DECOMPRESSION_STATUS_MATERIALIZABLE = 2
DECOMPRESSION_STATUS_SIMULATED_OUTPUT_OBSERVED = 5
DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM = 2
DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE = 1
DECOMPRESSION_PAYLOAD_ROLE_NAMES = {
    1: "unknown_runtime_payload",
    2: "primary_program",
    3: "asset_data",
}
DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NAMES = {
    1: "tool_inferred",
    2: "native_unpack_entry_validated",
    3: "signature_only",
    4: "observed_output_only",
}
DECOMPRESSION_PARENT_REMAINS_ACTIVE_NAMES = {
    0: "unknown",
    1: "false",
    2: "true",
}
TARGET_STATE_SCHEMA_VERSION = 1
TARGET_STATE_IMPORT_MODE = "amiga_dos_startup_sequence"
TARGET_STATE_STARTUP_PARSE_STATUS_DISABLED = "disabled"
TARGET_STATE_STARTUP_PARSE_STATUS_MISSING = "missing"
TARGET_STATE_STARTUP_PARSE_STATUS_PARSE_ERROR = "parse_error"
TARGET_STATE_STARTUP_PARSE_STATUS_EMPTY = "empty"
TARGET_STATE_STARTUP_PARSE_STATUS_OK = "ok"
TARGET_STATE_STARTUP_PARSE_SOURCE_PATH = "s/startup-sequence"
TARGET_STATE_STARTUP_PARSE_DEFAULT_REASON = "startup-sequence auto-import is not currently available"
TARGET_STATE_REJECT_REASON_PARSE_ERROR = "parse_error"
TARGET_STATE_REJECT_REASON_MISSING_STARTUP = "missing_startup"
TARGET_STATE_REJECT_REASON_PATH_NOT_FOUND = "path_not_found"
TARGET_STATE_REJECT_REASON_UNSUPPORTED_FORMAT = "unsupported_format"
TARGET_STATE_REJECT_REASON_DUPLICATE = "filtered_duplicate"
TARGET_STATE_REJECT_REASON_FILTERED_DIR = "filtered_dir"


class TargetStateSubtargetState(StrEnum):
    ADDED = "added"


class TargetStateSubtargetOrigin(StrEnum):
    AUTO = "auto"
    MANUAL = "manual"


TARGET_STATE_SUBTARGET_STATES = {TargetStateSubtargetState.ADDED}
_STARTUP_PARSE_PREFIX_ALIASES = {"s"}
_STARTUP_PARSE_PREFIX_FILTERED = {"c", "l", "lib", "libs", "devs", "fonts", "system"}
_STARTUP_PARSE_SHELL_KEYWORDS = {
    "loadwb",
    "alias",
    "assign",
    "cd",
    "cat",
    "copy",
    "delete",
    "else",
    "esac",
    "echo",
    "fi",
    "for",
    "if",
    "in",
    "set",
    "setenv",
    "skip",
    "then",
    "while",
    "wait",
}
_STARTUP_PARSE_PATH_KEYWORDS = {
    "s/startup-sequence",
    "s:startup-sequence",
    "startup-sequence",
}
_STARTUP_PARSE_BARE_PATH_TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")


def _normalize_disk_id_arg(disk_id: str | None) -> str | None:
    if disk_id is None:
        return None
    normalized = disk_id.strip()
    if not normalized:
        return None
    if normalized.startswith(AMIGA_DISK_PREFIX):
        raise DiskAnalysisError(
            f"disk_id argument must be bare disk id; do not prefix with '{AMIGA_DISK_PREFIX}'"
        )
    return normalized


def _normalize_disk_project_id(project_name: str) -> str:
    normalized = project_name.strip()
    if not normalized.startswith(AMIGA_DISK_PREFIX):
        raise DiskAnalysisError(f"Project {project_name} is not a disk project")
    suffix = normalized[len(AMIGA_DISK_PREFIX):]
    if "__" in suffix:
        raise DiskAnalysisError(f"Project {project_name} is not a parent disk project")
    disk_id = _normalize_disk_id_arg(suffix)
    if disk_id is None:
        raise DiskAnalysisError(f"Invalid disk project id in {project_name}")
    return disk_id


def _is_legacy_startup_prefix(entry_path: str | None) -> bool:
    if not isinstance(entry_path, str):
        return False
    normalized = entry_path.strip().strip("/")
    if not normalized:
        return False
    first = normalized.split("/", 1)[0].lower()
    return first in _STARTUP_PARSE_PREFIX_FILTERED


def _coerce_disk_entry_import_path(raw_path: str | None) -> str | None:
    if not isinstance(raw_path, str):
        return None
    value = raw_path.replace("\\", "/").strip()
    if not value:
        return None
    return value.strip("/")


def _is_decompressed_payload_relationship(relationship: dict[str, object]) -> bool:
    return _int_field(relationship, "kind_id") == DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD


def _target_state_subtarget_state_from_json(value: object) -> TargetStateSubtargetState | None:
    if not isinstance(value, str):
        return None
    try:
        return TargetStateSubtargetState(value)
    except ValueError:
        return None


def _target_state_subtarget_origin_from_json(value: object) -> TargetStateSubtargetOrigin | None:
    if not isinstance(value, str):
        return None
    try:
        return TargetStateSubtargetOrigin(value)
    except ValueError:
        return None


def _startup_disk_entry_paths(analysis: AdfAnalysis) -> set[str]:
    if analysis.files is None:
        return set()
    paths: set[str] = set()
    for entry in analysis.files:
        full_path = getattr(entry, "full_path", None)
        if not isinstance(full_path, str):
            continue
        normalized = full_path.strip().strip("/").lower()
        if normalized:
            paths.add(normalized)
    return paths


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


def _bootblock_read_stage_metadata() -> dict[str, object]:
    return {
        "target_type": "bootloader_stage",
        "entry_register_seeds": [
            {
                "entry_offset": None,
                "register": "A6",
                "kind": "library_base",
                "library_name": "exec.library",
                "struct_name": "LIB",
                "context_name": None,
                "note": "ExecBase",
            },
            {
                "entry_offset": None,
                "register": "A1",
                "kind": "struct_ptr",
                "library_name": None,
                "struct_name": "IO",
                "context_name": "trackdisk.device",
                "note": "IOStdReq (open trackdisk.device)",
            },
        ],
        "bootblock": None,
        "resident": None,
        "library": None,
        "custom_structs": [],
        "rsset_layout_regions": [],
        "seeded_entities": [],
        "seeded_code_labels": [],
        "seeded_code_entrypoints": [],
        "absolute_code_labels": [],
        "execution_views": [],
        "suppressed_seeded_items": [],
    }


def _bootloader_stage_runtime_copy_execution_views(
    stage: BootloaderStage,
    analysis: AdfAnalysis,
) -> list[dict[str, object]]:
    if analysis.bootloader_analysis is None:
        return []
    views: list[dict[str, object]] = []
    for copy_stage in analysis.bootloader_analysis.stages:
        for copy in copy_stage.memory_copies:
            if copy.byte_length <= 0 or copy.source_addr < stage.base_addr:
                continue
            source_start = copy.source_addr - stage.base_addr
            source_end = source_start + copy.byte_length
            dest_end = copy.destination_addr + copy.byte_length
            handoff_target = copy_stage.handoff_target
            if (
                source_start < 0
                or source_end > stage.size
                or handoff_target is None
                or handoff_target < copy.destination_addr
                or handoff_target >= dest_end
            ):
                continue
            views.append(
                {
                    "source_start": source_start,
                    "source_end": source_end,
                    "base_addr": copy.destination_addr,
                    "name": "bootstrapped_code",
                    "seed_origin": "autodoc",
                    "review_status": "seeded",
                    "citation": f"bootloader:{copy_stage.name}:runtime_copy:{copy.instruction_addr:08x}",
                    "comment": (
                        f"Bootloader copies ${copy.source_addr:08X}-${copy.source_addr + copy.byte_length - 1:08X} "
                        f"to ${copy.destination_addr:08X} and hands off at ${handoff_target:08X}"
                    ),
                }
            )
    return views


def _bootloader_stage_target_metadata(stage: BootloaderStage, analysis: AdfAnalysis) -> dict[str, object]:
    assert stage.import_target is not None
    metadata = dict(stage.import_target.target_metadata)
    existing_views = metadata.get("execution_views")
    views: list[object] = list(existing_views) if isinstance(existing_views, list) else []
    existing_keys: set[tuple[int, int, int]] = set()
    for view in views:
        if not isinstance(view, dict):
            continue
        source_start = _int_field(view, "source_start")
        source_end = _int_field(view, "source_end")
        base_addr = _int_field(view, "base_addr")
        if source_start is not None and source_end is not None and base_addr is not None:
            existing_keys.add((source_start, source_end, base_addr))
    for view in _bootloader_stage_runtime_copy_execution_views(stage, analysis):
        source_start = _int_field(view, "source_start")
        source_end = _int_field(view, "source_end")
        base_addr = _int_field(view, "base_addr")
        if source_start is None or source_end is None or base_addr is None:
            continue
        key = (source_start, source_end, base_addr)
        if key in existing_keys:
            continue
        views.append(view)
        existing_keys.add(key)
    metadata["execution_views"] = views
    return metadata


def _bootblock_disk_read_stage_targets(
    source_analysis: dict[str, object] | None,
    disk_bytes: bytes,
) -> list[tuple[FileImportTargetInfo, bytes]]:
    if source_analysis is None:
        return []
    sections = source_analysis.get("sections")
    if not isinstance(sections, list):
        return []
    stage_targets: list[tuple[FileImportTargetInfo, bytes]] = []
    runtime_copies: list[dict[str, int | str]] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        copies = section.get("recovered_platform_runtime_copies")
        if not isinstance(copies, list):
            continue
        for copy in copies:
            if not isinstance(copy, dict):
                continue
            source_kind = _str_field(copy, "source_kind")
            source_addr = _int_field(copy, "source_addr")
            destination_addr = _int_field(copy, "destination_addr")
            byte_length = _int_field(copy, "byte_length")
            handoff_addr = _int_field(copy, "handoff_addr")
            instruction_offset = _int_field(copy, "offset")
            transfer_source_kind = None if source_kind is None else BootloaderTransferSourceKind(source_kind)
            if (
                transfer_source_kind is not BootloaderTransferSourceKind.POST_READ_RUNTIME_COPY
                or source_addr is None
                or destination_addr is None
                or byte_length is None
                or handoff_addr is None
                or instruction_offset is None
                or source_kind is None
                or byte_length <= 0
            ):
                continue
            runtime_copies.append(
                {
                    "source_addr": source_addr,
                    "destination_addr": destination_addr,
                    "byte_length": byte_length,
                    "handoff_addr": handoff_addr,
                    "instruction_offset": instruction_offset,
                    "source_kind": source_kind,
                }
            )
    for section in sections:
        if not isinstance(section, dict):
            continue
        reads = section.get("recovered_platform_disk_reads")
        if not isinstance(reads, list):
            continue
        for read in reads:
            if not isinstance(read, dict):
                continue
            command_name = _str_field(read, "command_name")
            source_kind = _str_field(read, "source_kind")
            disk_offset = _int_field(read, "disk_offset")
            byte_length = _int_field(read, "byte_length")
            destination_addr = _int_field(read, "destination_addr")
            instruction_offset = _int_field(read, "offset")
            disk_command = None if command_name is None else BootloaderDiskCommand(command_name)
            transfer_source_kind = None if source_kind is None else BootloaderTransferSourceKind(source_kind)
            if (
                disk_command is not BootloaderDiskCommand.CMD_READ
                or transfer_source_kind is not BootloaderTransferSourceKind.LOGICAL_DISK_OFFSET
                or disk_offset is None
                or byte_length is None
                or destination_addr is None
                or instruction_offset is None
                or disk_offset < 0
                or byte_length <= 0
            ):
                continue
            end = disk_offset + byte_length
            if end > len(disk_bytes):
                continue
            metadata = _bootblock_read_stage_metadata()
            execution_views: list[dict[str, object]] = []
            read_end_addr = destination_addr + byte_length
            for copy in runtime_copies:
                copy_source_addr = int(copy["source_addr"])
                copy_destination_addr = int(copy["destination_addr"])
                copy_byte_length = int(copy["byte_length"])
                copy_handoff_addr = int(copy["handoff_addr"])
                copy_instruction_offset = int(copy["instruction_offset"])
                copy_source_end = copy_source_addr + copy_byte_length
                copy_destination_end = copy_destination_addr + copy_byte_length
                if (
                    copy_source_addr < destination_addr
                    or copy_source_end > read_end_addr
                    or copy_handoff_addr < copy_destination_addr
                    or copy_handoff_addr >= copy_destination_end
                ):
                    continue
                source_start = copy_source_addr - destination_addr
                execution_views.append(
                    {
                        "source_start": source_start,
                        "source_end": source_start + copy_byte_length,
                        "base_addr": copy_destination_addr,
                        "name": "bootstrapped_code",
                        "seed_origin": "autodoc",
                        "review_status": "seeded",
                        "citation": f"bootblock:runtime_copy:{copy_instruction_offset:08x}",
                        "comment": (
                            f"Bootblock copies ${copy_source_addr:08X}-${copy_source_end - 1:08X} "
                            f"to ${copy_destination_addr:08X} and hands off at ${copy_handoff_addr:08X}"
                        ),
                    }
                )
            metadata["execution_views"] = execution_views
            stage_index = len(stage_targets) + 1
            stage_targets.append(
                (
                    FileImportTargetInfo(
                        target_type="bootloader_stage",
                        entry_path=f"bootloader/stage_{stage_index}",
                        local_target_id=f"amiga_raw_bootloader_stage_{stage_index}",
                        source={
                            "kind": "raw_binary",
                            "address_model": "runtime_absolute",
                            "byte_offset": disk_offset,
                            "byte_size": byte_length,
                            "disk_byte_offset": disk_offset,
                            "disk_byte_size": byte_length,
                            "load_address": destination_addr,
                            "entrypoint": destination_addr,
                            "code_start_offset": 0,
                            "source_kind": source_kind,
                            "bootblock_read_instruction_offset": instruction_offset,
                        },
                        target_metadata=metadata,
                    ),
                    disk_bytes[disk_offset:end],
                )
            )
    return stage_targets


def _analyze_bootblock_source_for_disk_reads(
    bootblock_target_dir: Path,
    *,
    project_root: Path,
) -> dict[str, object] | None:
    backend_project_root = project_root
    if not (backend_project_root / "src" / "build" / "platform_file_lib.dll").exists():
        backend_project_root = PROJECT_ROOT
    if not (backend_project_root / "src" / "build" / "platform_file_lib.dll").exists():
        return None
    try:
        source = resolve_target_binary_source(bootblock_target_dir, project_root=project_root)
    except (OSError, ValueError):
        return None
    if source is None:
        return None
    try:
        return analyze_project_source_with_c_backend(
            source,
            metadata_path=bootblock_target_dir / "target_metadata.json",
            project_root=backend_project_root,
        )
    except (OSError, ValueError):
        return None


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


def _disk_target_state_path(disk_target_root: Path) -> Path:
    return disk_target_root / "target_state.json"


def _disk_target_state_payload(
    *,
    schema_version: int,
    import_mode: str,
    imported_targets: list[ImportedTarget],
    state_subtargets: list[dict[str, object]] | None = None,
    source_path: str,
    startup_sequence_parse: dict[str, object],
    candidate_rejects: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    now = datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat()
    subtargets: list[dict[str, object]] = []
    payload_nodes: list[dict[str, object]] = []
    if state_subtargets is None:
        for imported_target in imported_targets:
            subtargets.append(
                {
                    "id": imported_target.target_name,
                    "path": imported_target.target_path,
                    "state": TargetStateSubtargetState.ADDED,
                    "origin": TargetStateSubtargetOrigin.AUTO,
                    "reason_code": None,
                    "reason_detail": None,
                    "added_by_import": True,
                    "imported_at": now,
                }
            )
    else:
        for state_entry_payload in state_subtargets:
            state_entry = dict(state_entry_payload)
            if not isinstance(state_entry.get("id"), str) or not state_entry.get("id"):
                continue
            path_value = state_entry.get("path")
            if not isinstance(path_value, str):
                state_entry["path"] = ""
            state_entry.setdefault("state", TargetStateSubtargetState.ADDED)
            state_entry.setdefault("origin", TargetStateSubtargetOrigin.MANUAL)
            state_entry.setdefault("added_by_import", False)
            state_entry["imported_at"] = now
            subtargets.append(state_entry)
    for item in imported_targets:
        if not isinstance(item.derived_from, dict):
            continue
        relationship = item.derived_from
        if not _is_decompressed_payload_relationship(relationship):
            continue
        payload_nodes.append(
            {
                "id": item.target_name,
                "path": item.target_path,
                "parent_file_id": relationship.get("parent_target"),
                "origin": TargetStateSubtargetOrigin.AUTO,
                "codec": _str_field(relationship, "codec_id") or _str_field(relationship, "codec_name") or "unknown",
                "decode_status": "ok",
                "media_hint": "raw",
                "decoded_size": _int_field(relationship, "decompressed_size"),
                "source_offset": _int_field(relationship, "packed_section_offset")
                or _int_field(relationship, "source_section"),
                "source_file_offset": _int_field(relationship, "packed_file_offset"),
                "source_hunk_offset": (
                    _int_field(relationship, "source_hunk_offset")
                    or _int_field(relationship, "packed_section_offset")
                ),
                "source_size": _int_field(relationship, "packed_size"),
                "source_path": source_path,
                "crc32": None,
                "state": TargetStateSubtargetState.ADDED,
                "reason_code": None,
                "reason_detail": None,
            }
        )
    return {
        "schema_version": schema_version,
        "import_mode": import_mode,
        "imported_at": now,
        "startup_sequence_parse": startup_sequence_parse,
        "subtargets": subtargets,
        "payload_nodes": payload_nodes,
        "candidate_rejects": candidate_rejects or [],
    }


def _write_disk_target_state(path: Path, state: dict[str, object]) -> None:
    _write_text(path, json.dumps(state, indent=2, sort_keys=True) + "\n")


def _load_disk_target_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _startup_parse_status_payload(
    status: str,
    *,
    reason: str,
    line: int | None = None,
    command: str | None = None,
    error: str | None = None,
    source_path: str = TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": status,
        "source_path": source_path,
        "reason": reason,
        "line": line,
        "command": command,
        "error": error,
    }
    if isinstance(extra, dict):
        payload.update(extra)
    return payload


def _coerce_startup_parse_status(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return _startup_parse_status_payload(
            TARGET_STATE_STARTUP_PARSE_STATUS_DISABLED,
            reason=TARGET_STATE_STARTUP_PARSE_DEFAULT_REASON,
            source_path=TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
        )
    status = payload.get("status")
    if not isinstance(status, str):
        status = TARGET_STATE_STARTUP_PARSE_STATUS_DISABLED
    parsed_status: dict[str, object] = {
        "status": status,
        "source_path": payload.get("source_path") or TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
        "reason": payload.get("reason") or "startup-sequence parse status unknown",
        "line": _int_field(payload, "line"),
        "command": payload.get("command") if isinstance(payload.get("command"), str) else None,
        "error": payload.get("error") if isinstance(payload.get("error"), str) else None,
    }
    startup_sequence_lines = payload.get("startup_sequence_lines")
    if isinstance(startup_sequence_lines, list):
        parsed_status["startup_sequence_lines"] = [
            item for item in startup_sequence_lines if isinstance(item, str)
        ]
    startup_sequence_entries = payload.get("startup_sequence_entries")
    if isinstance(startup_sequence_entries, list):
        parsed_entries: list[dict[str, object]] = []
        for entry in startup_sequence_entries:
            if not isinstance(entry, dict):
                continue
            coerced_entry: dict[str, object] = {}
            line = _int_field(entry, "line")
            if line is not None:
                coerced_entry["line"] = line
            for name in ("path", "command", "status", "reason_code", "reason_detail", "target_name"):
                value = entry.get(name)
                if isinstance(value, str):
                    coerced_entry[name] = value
            parsed_entries.append(coerced_entry)
        parsed_status["startup_sequence_entries"] = parsed_entries
    return parsed_status


def _coerce_candidate_rejects(payload: object) -> list[dict[str, object]]:
    if not isinstance(payload, list):
        return []
    rejects: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        reason_code = item.get("reason_code")
        if not isinstance(path, str) or not isinstance(reason_code, str):
            continue
        reason_detail = item.get("reason_detail")
        if reason_detail is not None and not isinstance(reason_detail, str):
            reason_detail = None
        reject_entry: dict[str, object] = {
            "path": path,
            "reason_code": reason_code,
            "reason_detail": reason_detail,
        }
        line = _int_field(item, "line")
        if line is not None:
            reject_entry["line"] = line
        command = item.get("command")
        if isinstance(command, str):
            reject_entry["command"] = command
        rejects.append(reject_entry)
    return rejects


def _coerce_state_subtargets(payload: object) -> dict[str, dict[str, object]]:
    if not isinstance(payload, list):
        return {}
    entries: dict[str, dict[str, object]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        item = dict(item)
        target_id = item.get("id")
        if not isinstance(target_id, str) or not target_id:
            continue
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            continue
        state = _target_state_subtarget_state_from_json(item.get("state"))
        if state not in TARGET_STATE_SUBTARGET_STATES:
            continue
        origin = _target_state_subtarget_origin_from_json(item.get("origin"))
        if origin is None:
            continue
        item["state"] = state
        item["origin"] = origin
        entries[target_id] = item
    return entries


def _coerce_payload_target_ids(payload: object, *, parent_ids: set[str]) -> set[str]:
    if not isinstance(payload, list):
        return set()
    result: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        node_id = _str_field(item, "id")
        if not node_id:
            continue
        if _target_state_subtarget_state_from_json(item.get("state")) is not TargetStateSubtargetState.ADDED:
            continue
        parent_target = _str_field(item, "parent_file_id")
        if not parent_target:
            continue
        if parent_target not in parent_ids:
            continue
        result.add(node_id)
    return result


def _state_entry_payload(
    *,
    target_id: str,
    target_path: str,
    origin: TargetStateSubtargetOrigin,
) -> dict[str, object]:
    return {
        "id": target_id,
        "path": target_path,
        "state": TargetStateSubtargetState.ADDED,
        "origin": origin,
        "reason_code": None,
        "reason_detail": None,
        "added_by_import": origin is TargetStateSubtargetOrigin.AUTO,
    }


def import_disk_entry_target(
    project_name: str,
    *,
    entry_path: str,
    project_root: Path = PROJECT_ROOT,
) -> ImportedTarget:
    from amiga_reversing.disasm.projects import mark_project_updated

    normalized_disk_id = _normalize_disk_project_id(project_name)
    disk_target_root = disk_project_root(project_root, normalized_disk_id)
    manifest_path = disk_target_root / "manifest.json"
    if not manifest_path.exists():
        raise DiskAnalysisError(f"Disk manifest does not exist: {manifest_path}")
    manifest = DiskManifest.load(manifest_path)
    normalized_entry_path = _coerce_disk_entry_import_path(entry_path)
    if normalized_entry_path is None:
        raise DiskAnalysisError("entry_path must be a non-empty string")
    if manifest.analysis.files is None:
        raise DiskAnalysisError("Disk analysis has no indexed files to resolve manual entry import")
    entry = _find_dos_entry_by_path(manifest.analysis, normalized_entry_path)
    if entry is None:
        raise DiskAnalysisError(f"Disk entry was not found: {normalized_entry_path}")
    entry_content = getattr(entry, "content", None)
    if entry_content is None or getattr(entry_content, "import_target", None) is None:
        raise DiskAnalysisError(f"Disk entry is not importable: {normalized_entry_path}")
    import_target = entry_content.import_target
    if import_target is None:
        raise DiskAnalysisError(f"Disk entry is missing import metadata: {normalized_entry_path}")
    adf_file = Path(manifest.source_path)
    if not adf_file.is_absolute():
        adf_file = project_root / adf_file
    if not adf_file.exists():
        raise DiskAnalysisError(f"Disk source file does not exist: {manifest.source_path}")
    created_target_dirs: list[Path] = []
    disk_children_root = disk_project_targets_dir(project_root, normalized_disk_id)
    state_payload = _load_disk_target_state(_disk_target_state_path(disk_target_root))
    state_subtargets = _coerce_state_subtargets(state_payload.get("subtargets"))
    startup_parse = _coerce_startup_parse_status(state_payload.get("startup_sequence_parse"))
    candidate_rejects = _coerce_candidate_rejects(state_payload.get("candidate_rejects"))
    imported_targets = {target.target_name: target for target in manifest.imported_targets}
    try:
        imported_target, child_targets = _import_disk_file_entry(
            adf_file=adf_file,
            disk_id=normalized_disk_id,
            disk_children_root=disk_children_root,
            import_target=import_target,
            created_target_dirs=created_target_dirs,
            project_root=project_root,
        )
        imported_targets[imported_target.target_name] = imported_target
        for child_target in child_targets:
            imported_targets[child_target.target_name] = child_target
        state_subtargets[imported_target.target_name] = _state_entry_payload(
            target_id=imported_target.target_name,
            target_path=imported_target.target_path,
            origin=TargetStateSubtargetOrigin.MANUAL,
        )
        for child_target in child_targets:
            if child_target.target_name in state_subtargets:
                continue
            state_subtargets[child_target.target_name] = _state_entry_payload(
                target_id=child_target.target_name,
                target_path=child_target.target_path,
                origin=TargetStateSubtargetOrigin.AUTO,
            )
        for target_id, state_entry in list(state_subtargets.items()):
            existing_target = imported_targets.get(target_id)
            if existing_target is None:
                state_subtargets.pop(target_id, None)
                continue
            state_entry["path"] = existing_target.target_path
            state_entry["id"] = target_id
            state_entry.setdefault("reason_code", None)
            state_entry.setdefault("reason_detail", None)
            state_entry.setdefault(
                "origin",
                (
                    TargetStateSubtargetOrigin.MANUAL
                    if target_id == imported_target.target_name
                    else TargetStateSubtargetOrigin.AUTO
                ),
            )
            if target_id == imported_target.target_name:
                state_entry["origin"] = TargetStateSubtargetOrigin.MANUAL
                state_entry["added_by_import"] = False
            elif state_entry.get("origin") is TargetStateSubtargetOrigin.MANUAL:
                pass
            else:
                state_entry["origin"] = TargetStateSubtargetOrigin.AUTO
                state_entry["added_by_import"] = True
        manifest_path.write_text(
            json.dumps(
                DiskManifest(
                    schema_version=manifest.schema_version,
                    disk_id=manifest.disk_id,
                    source_path=manifest.source_path,
                    source_sha256=manifest.source_sha256,
                    analysis=manifest.analysis,
                    imported_targets=sorted(imported_targets.values(), key=lambda target: target.entry_path),
                    bootblock_target_name=manifest.bootblock_target_name,
                    bootblock_target_path=manifest.bootblock_target_path,
                ).to_dict(),
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )
        _write_disk_target_state(
            _disk_target_state_path(disk_target_root),
            _disk_target_state_payload(
                schema_version=TARGET_STATE_SCHEMA_VERSION,
                import_mode=TARGET_STATE_IMPORT_MODE,
                imported_targets=sorted(imported_targets.values(), key=lambda target: target.entry_path),
                source_path=manifest.source_path,
                startup_sequence_parse=startup_parse,
                candidate_rejects=candidate_rejects,
                state_subtargets=list(state_subtargets.values()),
            ),
        )
        mark_project_updated(disk_target_root)
        return imported_target
    except Exception:
        for target_dir in reversed(created_target_dirs):
            shutil.rmtree(target_dir, ignore_errors=True)
        raise


def _import_disk_file_entry(
    *,
    adf_file: Path,
    disk_id: str,
    disk_children_root: Path,
    import_target: Any,
    created_target_dirs: list[Path],
    project_root: Path,
) -> tuple[ImportedTarget, list[ImportedTarget]]:
    from amiga_reversing.disasm.projects import (
        create_project_at_path,
        mark_project_updated,
    )

    target_type = _obj_str_field(import_target, "target_type")
    if target_type is None:
        raise DiskAnalysisError("C disk import target is missing target_type")
    local_target_name = _import_target_required_text(
        _obj_str_field(import_target, "local_target_id"),
        "local_target_id",
        target_type,
    )
    entry_path = _import_target_required_text(
        _import_target_required_text(
            _obj_str_field(import_target, "entry_path"),
            "entry_path",
            target_type,
        ),
        "entry_path",
        target_type,
    )
    target_name = disk_child_project_id(disk_id, local_target_name)
    target_dir = disk_children_root / local_target_name
    if target_dir.exists():
        if not target_dir.is_dir():
            raise DiskAnalysisError(f"Target already exists but is not a directory: {target_name}")
    else:
        create_project_at_path(
            disk_child_target_relpath(disk_id, local_target_name).as_posix(),
            project_root=project_root,
            origin={
                "kind": "disk_child",
                "parent_disk_id": disk_id,
                "target_role": "disk_entry",
                "entry_path": entry_path,
                "target_type": target_type,
                "source_path": adf_file.as_posix(),
            },
        )
        created_target_dirs.append(target_dir)
    clean_obsolete_target_local_state(target_dir)
    write_source_descriptor(
        target_dir,
        {
            "kind": "disk_entry",
            "disk_id": disk_id,
            "disk_path": adf_file.as_posix(),
            "entry_path": entry_path,
            "parent_disk_id": disk_id,
        },
    )
    target_metadata = import_target.target_metadata if hasattr(import_target, "target_metadata") else None
    if not isinstance(target_metadata, dict):
        raise DiskAnalysisError("C disk import target is missing target metadata")
    write_target_metadata(target_dir, TargetMetadata.from_dict(target_metadata))
    mark_project_updated(target_dir)
    parent_derived: list[dict[str, object]] = []
    child_targets: list[ImportedTarget] = []
    if _target_type_may_contain_packed_payload(target_type):
        materialized = _materialize_decompressed_payload_children(
            adf_file=adf_file,
            disk_id=disk_id,
            disk_children_root=disk_children_root,
            parent_local_target_id=local_target_name,
            parent_target_name=target_name,
            parent_entry_path=entry_path,
            project_root=project_root,
        )
        parent_derived = materialized.parent_derived
        child_targets = materialized.child_targets
        created_target_dirs.extend(materialized.created_dirs)
    return (
        ImportedTarget(
            target_name=target_name,
            target_path=disk_child_target_relpath(disk_id, local_target_name).as_posix(),
            entry_path=entry_path,
            binary_path=f"{adf_file.as_posix()}::{entry_path}",
            target_type=target_type,
            derived_targets=parent_derived or None,
        ),
        child_targets,
    )


def _append_startup_candidate_reject(
    rejects: list[dict[str, object]],
    *,
    path: str,
    reason_code: str,
    reason_detail: str,
    line: int | None = None,
    command: str | None = None,
) -> None:
    entry: dict[str, object] = {
        "path": path,
        "reason_code": reason_code,
        "reason_detail": reason_detail,
    }
    if line is not None:
        entry["line"] = line
    if command is not None:
        entry["command"] = command
    rejects.append(entry)


def _coerce_startup_warning_reason(item: dict[str, object]) -> tuple[str, str]:
    reason_code = item.get("reason_code")
    if not isinstance(reason_code, str) or not reason_code:
        reason_code = TARGET_STATE_REJECT_REASON_PARSE_ERROR
    reason_detail = item.get("reason")
    if not isinstance(reason_detail, str) or not reason_detail:
        detail = item.get("reason_detail")
        reason_detail = detail if isinstance(detail, str) and detail else "startup parse warning"
    return reason_code, reason_detail


def _find_dos_entry_by_path(analysis: AdfAnalysis, path: str) -> object | None:
    normalized = path.strip().strip("/").lower()
    if not normalized:
        return None
    if analysis.files is None:
        return None
    for entry in analysis.files:
        candidate_path = getattr(entry, "full_path", None)
        if not isinstance(candidate_path, str):
            continue
        if candidate_path.strip().strip("/").lower() == normalized:
            entry_object: object = entry
            return entry_object
    return None


def _normalize_startup_token(
    token: str,
    *,
    token_args: list[str] | None = None,
    available_entry_paths: set[str] | None = None,
) -> tuple[str | None, str | None]:
    value = token.strip().strip().strip('"').strip("'").strip()
    if not value:
        return None, None
    normalized_value = value.lower().strip()
    if normalized_value in _STARTUP_PARSE_PATH_KEYWORDS:
        return None, None
    if value.startswith((";", "#", ">", "<")):
        return None, None
    if ":" in value:
        prefix, _, rest = value.partition(":")
        prefix_lower = prefix.lower()
        if not rest:
            return None, TARGET_STATE_REJECT_REASON_UNSUPPORTED_FORMAT
        if prefix_lower in _STARTUP_PARSE_PREFIX_FILTERED:
            return None, TARGET_STATE_REJECT_REASON_FILTERED_DIR
        if prefix_lower not in _STARTUP_PARSE_PREFIX_ALIASES and not prefix_lower.startswith("df"):
            return None, TARGET_STATE_REJECT_REASON_UNSUPPORTED_FORMAT
        suffix = rest.lstrip("/").strip()
        if not suffix:
            return None, TARGET_STATE_REJECT_REASON_UNSUPPORTED_FORMAT
        if prefix_lower in _STARTUP_PARSE_PREFIX_ALIASES:
            return f"{prefix_lower}/{suffix}", None
        return suffix, None
    command_args = token_args or []
    if normalized_value == "run" and command_args:
        return None, TARGET_STATE_REJECT_REASON_UNSUPPORTED_FORMAT
    if "/" not in value and ":" not in value:
        if normalized_value in _STARTUP_PARSE_SHELL_KEYWORDS:
            return None, None
        normalized_candidate = value.lstrip("/")
        lower_candidate = normalized_candidate.lower()
        if available_entry_paths is not None:
            if lower_candidate in available_entry_paths:
                return normalized_candidate, None
            filtered_candidate = f"c/{lower_candidate}"
            if filtered_candidate in available_entry_paths:
                return None, TARGET_STATE_REJECT_REASON_FILTERED_DIR
        if not _STARTUP_PARSE_BARE_PATH_TOKEN.fullmatch(value):
            return None, None
        return value.lstrip("/"), None
    return value.lstrip("/"), None


def _extract_startup_candidates(
    raw_lines: list[str],
    *,
    available_entry_paths: set[str] | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    candidates: list[dict[str, object]] = []
    seen: set[str] = set()
    parse_failures: list[dict[str, object]] = []
    for index, raw_line in enumerate(raw_lines, start=1):
        line = raw_line.split(";", 1)[0].strip()
        if not line:
            continue
        try:
            tokens = re.findall(r'"[^"]*"|\'[^\']*\'|\S+', line)
        except Exception:
            parse_failures.append(
                {
                    "line": index,
                    "reason": f"Failed to tokenize startup line {index}",
                    "command": line,
                }
            )
            continue
        if not tokens:
            continue
        command = tokens[0]
        path, reject_reason = _normalize_startup_token(
            command,
            token_args=tokens[1:],
            available_entry_paths=available_entry_paths,
        )
        if path is None:
            if reject_reason is not None:
                parse_failures.append(
                    {
                        "line": index,
                        "reason": "Startup token was not importable for startup-sequence auto import",
                        "reason_detail": reject_reason,
                        "path": command,
                        "command": command,
                        "reason_code": reject_reason,
                    }
                )
            continue
        path_key = path.lower()
        if path_key in seen:
            parse_failures.append(
                {
                    "line": index,
                    "reason": "Filtered duplicate startup reference",
                    "path": path,
                    "command": command,
                    "reason_code": TARGET_STATE_REJECT_REASON_DUPLICATE,
                }
            )
            continue
        seen.add(path_key)
        candidates.append({
            "path": path,
            "line": index,
            "command": command,
        })
    return candidates, parse_failures


def _discover_startup_sequence_targets(
    analysis: AdfAnalysis,
    *,
    available_entry_paths: set[str] | None = None,
    adf_path: Path,
    project_root: Path,
) -> tuple[list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    try:
        startup_entry = None
        startup_path: str | None = None
        if analysis.files is None:
            return (
                [],
                _startup_parse_status_payload(
                    TARGET_STATE_STARTUP_PARSE_STATUS_MISSING,
                    reason="Missing DOS file inventory for startup-sequence parse",
                    source_path=TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
                    extra={"startup_sequence_lines": []},
                ),
                [],
            )
        for entry in analysis.files:
            if entry.full_path.lower().strip() == TARGET_STATE_STARTUP_PARSE_SOURCE_PATH.lower():
                startup_entry = entry
                startup_path = entry.full_path
                break
        if startup_entry is None:
            return (
                [],
                _startup_parse_status_payload(
                    TARGET_STATE_STARTUP_PARSE_STATUS_MISSING,
                    reason="startup-sequence file was not indexed in the filesystem analysis",
                    source_path=TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
                    extra={"startup_sequence_lines": []},
                ),
                [],
            )
        try:
            startup_text_bytes = extract_disk_entry_with_c_backend(
                adf_path,
                startup_path or TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
                project_root=project_root,
            )
        except Exception as exc:
            return (
                [],
                _startup_parse_status_payload(
                    TARGET_STATE_STARTUP_PARSE_STATUS_PARSE_ERROR,
                    reason=f"Could not extract {TARGET_STATE_STARTUP_PARSE_SOURCE_PATH}",
                    error=str(exc),
                    source_path=TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
                    extra={"startup_sequence_lines": []},
                ),
                [],
            )
        try:
            startup_text = startup_text_bytes.decode("utf-8")
        except UnicodeDecodeError:
            startup_text = startup_text_bytes.decode("latin1")
        raw_lines = startup_text.splitlines()
        candidates, parse_warnings = _extract_startup_candidates(
            raw_lines,
            available_entry_paths=available_entry_paths,
        )
        if not candidates:
            return (
                [],
                _startup_parse_status_payload(
                    TARGET_STATE_STARTUP_PARSE_STATUS_EMPTY,
                    reason="No valid startup command candidates were discovered",
                    source_path=TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
                    extra={"startup_sequence_lines": raw_lines},
                ),
                parse_warnings,
            )
        return (
            candidates,
            _startup_parse_status_payload(
                TARGET_STATE_STARTUP_PARSE_STATUS_OK,
                reason="startup-sequence parsed",
                source_path=TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
                extra={"startup_sequence_lines": raw_lines},
            ),
            parse_warnings,
        )
    except Exception as exc:
        return (
            [],
            _startup_parse_status_payload(
                TARGET_STATE_STARTUP_PARSE_STATUS_PARSE_ERROR,
                reason="Failed parsing startup-sequence",
                error=str(exc),
                source_path=TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
                extra={"startup_sequence_lines": []},
            ),
            [{"path": TARGET_STATE_STARTUP_PARSE_SOURCE_PATH, "reason_code": TARGET_STATE_REJECT_REASON_PARSE_ERROR, "reason_detail": str(exc)}],
        )


def _int_field(payload: dict[str, object], key: str) -> int | None:
    value = payload.get(key)
    return value if isinstance(value, int) else None


def _str_field(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value else None


def _obj_str_field(payload: Any, key: str) -> str | None:
    if isinstance(payload, dict):
        return _str_field(payload, key)
    if not hasattr(payload, key):
        return None
    value = getattr(payload, key)
    return value if isinstance(value, str) and value else None


def _decompression_role_fields(payload: dict[str, object]) -> dict[str, object]:
    fields: dict[str, object] = {}
    payload_role_id = _int_field(payload, "payload_role_id")
    payload_role_confidence_id = _int_field(payload, "payload_role_confidence_id")
    parent_remains_active_id = _int_field(payload, "parent_remains_active_id")
    if payload_role_id is not None:
        fields["payload_role_id"] = payload_role_id
        payload_role = DECOMPRESSION_PAYLOAD_ROLE_NAMES.get(payload_role_id)
        if payload_role is not None:
            fields["payload_role"] = payload_role
    if payload_role_confidence_id is not None:
        fields["payload_role_confidence_id"] = payload_role_confidence_id
        payload_role_confidence = DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NAMES.get(payload_role_confidence_id)
        if payload_role_confidence is not None:
            fields["payload_role_confidence"] = payload_role_confidence
    if parent_remains_active_id is not None:
        fields["parent_remains_active_id"] = parent_remains_active_id
        parent_remains_active = DECOMPRESSION_PARENT_REMAINS_ACTIVE_NAMES.get(parent_remains_active_id)
        if parent_remains_active is not None:
            fields["parent_remains_active"] = parent_remains_active
    return fields


def _safe_id_part(value: str, fallback: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)
    return safe.strip("._-").replace("-", "_") or fallback


def _native_unpacker_provider_id(event: dict[str, object]) -> str:
    codec = _safe_id_part(_str_field(event, "codec_id") or "unpacker", "unpacker")
    return f"c-{codec}-native"


def _decompressed_payload_child_local_id(
    parent_local_target_id: str,
    suggestion: dict[str, object],
) -> str:
    codec_raw = _str_field(suggestion, "codec_id") or "packed"
    codec = _safe_id_part(codec_raw, "packed")
    section = _int_field(suggestion, "source_section") or 0
    offset = _int_field(suggestion, "source_section_offset") or 0
    stem = target_output_stem(parent_local_target_id)
    candidate = f"{stem}_{codec}_{section:02x}_{offset:08x}"
    if len(candidate) > 71:
        candidate = candidate[:71].rstrip("._-")
    result = raw_target_id(candidate)
    assert isinstance(result, str)
    return result


def _self_decrunch_payload_child_local_id(parent_local_target_id: str, event: dict[str, object]) -> str:
    section = _int_field(event, "decompressor_code_section") or 0
    entry = _int_field(event, "decompressor_entry_offset") or 0
    load_address = _int_field(event, "load_address") or 0
    stem = target_output_stem(parent_local_target_id)
    candidate = f"{stem}_simdecrunch_{section:02x}_{entry:08x}_{load_address:08x}"
    if len(candidate) > 71:
        candidate = candidate[:71].rstrip("._-")
    result = raw_target_id(candidate)
    assert isinstance(result, str)
    return result


def _recognized_unpacker_payload_child_local_id(parent_local_target_id: str, event: dict[str, object]) -> str:
    section = _int_field(event, "source_section") or 0
    offset = _int_field(event, "unpacker_marker_offset") or 0
    codec_raw = _str_field(event, "codec_id") or "native"
    codec = _safe_id_part(codec_raw, "native")
    stem = target_output_stem(parent_local_target_id)
    candidate = f"{stem}_native_{codec}_{section:02x}_{offset:08x}"
    if len(candidate) > 71:
        candidate = candidate[:71].rstrip("._-")
    result = raw_target_id(candidate)
    assert isinstance(result, str)
    return result


def _materializable_decompression_suggestions(analysis: dict[str, object]) -> list[dict[str, object]]:
    suggestions = analysis.get("derived_target_suggestions")
    if not isinstance(suggestions, list):
        return []
    materializable: list[dict[str, object]] = []
    for item in suggestions:
        if not isinstance(item, dict):
            continue
        if _int_field(item, "kind_id") != DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD:
            continue
        if _int_field(item, "status_id") != DECOMPRESSION_STATUS_MATERIALIZABLE:
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


def _materializable_recognized_unpacker_events(analysis: dict[str, object]) -> list[dict[str, object]]:
    events = analysis.get("decompression_events")
    if not isinstance(events, list):
        return []
    materializable: list[dict[str, object]] = []
    for item in events:
        if not isinstance(item, dict):
            continue
        if _int_field(item, "source_kind_id") != DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER:
            continue
        if _int_field(item, "status_id") != DECOMPRESSION_STATUS_MATERIALIZABLE:
            continue
        if _int_field(item, "payload_role_id") != DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM:
            continue
        if _int_field(item, "parent_remains_active_id") != DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE:
            continue
        if _str_field(item, "event_id") is None:
            continue
        if _int_field(item, "decompressed_size") is None:
            continue
        if _str_field(item, "decompressed_sha256") is None:
            continue
        if _int_field(item, "target_start_address") is None:
            continue
        if _int_field(item, "entrypoint") is None:
            continue
        materializable.append(dict(item))
    return materializable


def _materializable_self_decrunch_events(analysis: dict[str, object]) -> list[dict[str, object]]:
    events = analysis.get("decompression_events")
    if not isinstance(events, list):
        return []
    materializable: list[dict[str, object]] = []
    for item in events:
        if not isinstance(item, dict):
            continue
        if _int_field(item, "source_kind_id") != DECOMPRESSION_SOURCE_SELF_DECRUNCHER:
            continue
        if item.get("provider_id") != "m68k-sim-decrunch":
            continue
        if _int_field(item, "status_id") != DECOMPRESSION_STATUS_SIMULATED_OUTPUT_OBSERVED:
            continue
        if _int_field(item, "payload_role_id") != DECOMPRESSION_PAYLOAD_ROLE_PRIMARY_PROGRAM:
            continue
        if _int_field(item, "parent_remains_active_id") != DECOMPRESSION_PARENT_REMAINS_ACTIVE_FALSE:
            continue
        if _str_field(item, "event_id") is None:
            continue
        if _int_field(item, "simulated_output_size") is None:
            continue
        if _str_field(item, "simulated_output_sha256") is None:
            continue
        if _int_field(item, "load_address") is None:
            continue
        if _int_field(item, "entrypoint") is None:
            continue
        materializable.append(dict(item))
    return materializable


def _target_type_may_contain_packed_payload(target_type: str) -> bool:
    return target_type in {"program", "library"}


def _hunk_file_section_payload_starts(hunk_data: bytes) -> dict[int, int]:
    try:
        from amiga_reversing.disasm import reproduction
    except Exception:
        return {}
    try:
        layout_builder = reproduction.__dict__.get("_amiga_hunk_file_layout")
        if not callable(layout_builder):
            return {}
        layout = layout_builder(hunk_data)
    except Exception:
        return {}
    payload_starts: dict[int, int] = {}
    for item in layout:
        if not isinstance(item, dict) or item.get("kind") != "section_payload":
            continue
        section_index = _int_field(item, "section_index")
        file_start = _int_field(item, "file_start")
        if section_index is None or file_start is None:
            continue
        section_offset_start = _int_field(item, "section_offset_start") or 0
        payload_start = file_start - section_offset_start
        if payload_start < 0:
            continue
        payload_starts.setdefault(section_index, payload_start)
    return payload_starts


def _materialize_decompressed_payload_children(
    *,
    adf_file: Path,
    disk_id: str,
    disk_children_root: Path,
    parent_local_target_id: str,
    parent_target_name: str,
    parent_entry_path: str,
    project_root: Path,
) -> MaterializedPayloadChildren:
    from amiga_reversing.disasm.projects import (
        create_project_at_path,
        mark_project_updated,
        set_project_origin,
    )

    try:
        parent_bytes = extract_disk_entry_with_c_backend(adf_file, parent_entry_path, project_root=project_root)
    except Exception:
        return MaterializedPayloadChildren([], [], [], False)
    parent_temp_path = disk_children_root / f".{parent_local_target_id}.decompression-parent.bin"
    parent_target_dir = disk_children_root / parent_local_target_id
    created_dirs: list[Path] = []
    parent_derived: list[dict[str, object]] = []
    child_targets: list[ImportedTarget] = []
    _write_bytes(parent_temp_path, parent_bytes)
    try:
        try:
            parent_source = HunkFileBinarySource(
                kind=BinarySourceKind.HUNK_FILE,
                path=parent_temp_path,
                display_path=parent_temp_path.as_posix(),
                analysis_cache_path=parent_temp_path.with_suffix(parent_temp_path.suffix + ".analysis"),
                parent_disk_id=disk_id,
            )
            with effective_metadata_file(parent_target_dir) as metadata_path:
                analysis = analyze_project_source_with_c_backend(
                    parent_source,
                    metadata_path=metadata_path,
                    project_root=project_root,
                )
        except Exception:
            return MaterializedPayloadChildren([], [], [], False)
        section_payload_starts = _hunk_file_section_payload_starts(parent_temp_path.read_bytes())
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
            section_payload_start = section_payload_starts.get(source_section)
            packed_file_offset = (
                source_section_offset + section_payload_start
                if section_payload_start is not None
                else None
            )
            role_fields = _decompression_role_fields(suggestion)
            local_target_id = _decompressed_payload_child_local_id(parent_local_target_id, suggestion)
            target_name = disk_child_project_id(disk_id, local_target_id)
            target_dir = disk_children_root / local_target_id
            child_entry_path = (
                f"{parent_entry_path}::{_str_field(suggestion, 'codec_id') or 'decompressed'}_"
                f"{source_section_offset:08x}"
            )
            origin = {
                "project_origin_kind_id": PROJECT_ORIGIN_KIND_DERIVED_DECOMPRESSED_PAYLOAD,
                "kind": "derived_decompressed_payload",
                "parent_disk_id": disk_id,
                "parent_target": parent_target_name,
                "parent_entry_path": parent_entry_path,
                "child_entry_path": child_entry_path,
                "target_role_id": TARGET_ROLE_DECOMPRESSED_PAYLOAD,
                "target_role": "decompressed_payload",
                "target_type": "raw_binary",
                **role_fields,
                "codec_id": _str_field(suggestion, "codec_id"),
                "codec_name": _str_field(suggestion, "codec_name"),
                "packed_file_offset": packed_file_offset,
                "packed_section_offset": source_section_offset,
                "packed_size": packed_size,
                "decompressed_size": decompressed_size,
                "load_address": load_address,
                "entrypoint": entrypoint,
            }
            if target_dir.exists() and not target_dir.is_dir():
                continue
            if not target_dir.exists():
                create_project_at_path(
                    disk_child_target_relpath(disk_id, local_target_id).as_posix(),
                    project_root=project_root,
                    origin=origin,
                )
                created_dirs.append(target_dir)
            clean_obsolete_target_local_state(target_dir)
            output_path = target_dir / "binary.bin"
            temp_output_path = target_dir / ".decompression-output.tmp"
            try:
                result = decompress_packed_section_range_with_c_backend(
                    "amiga-hunk",
                    parent_temp_path,
                    source_section,
                    source_section_offset,
                    packed_size,
                    temp_output_path,
                    project_root=project_root,
                )
                packed_payloads = result.get("packed_payloads")
                packed_payload = packed_payloads[0] if isinstance(packed_payloads, list) and packed_payloads else {}
                if not isinstance(packed_payload, dict) or packed_payload.get("found") is not True:
                    raise DiskAnalysisError(f"C decompression did not materialise {child_entry_path}")
                temp_output_path.replace(output_path)
            finally:
                with contextlib.suppress(FileNotFoundError):
                    temp_output_path.unlink()
            set_project_origin(target_dir, origin=origin)
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
                "kind_id": DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD,
                "kind": "decompressed_payload",
                "parent_target": parent_target_name,
                "parent_entry_path": parent_entry_path,
                "child_target": target_name,
                "child_entry_path": child_entry_path,
                "packed_section_offset": source_section_offset,
                "packed_size": packed_size,
                "source_section": source_section,
                "decompressed_size": decompressed_size,
                "load_address": load_address,
                "entrypoint": entrypoint,
                "codec_id": _str_field(suggestion, "codec_id"),
                "codec_name": _str_field(suggestion, "codec_name"),
                "packed_file_offset": packed_file_offset,
                **role_fields,
            }
            decompression_record = {
                "schema_version": 1,
                "parent_target_id": parent_target_name,
                "child_target_id": target_name,
                "parent_entry_path": parent_entry_path,
                "child_entry_path": child_entry_path,
                **role_fields,
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
                    "kind_id": DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD,
                    "kind": "decompressed_payload",
                    "target_name": target_name,
                    "packed_section_offset": source_section_offset,
                    "packed_size": packed_size,
                    "codec_id": _str_field(suggestion, "codec_id"),
                    **role_fields,
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
        for event in _materializable_recognized_unpacker_events(analysis):
            event_id = _str_field(event, "event_id")
            output_size = _int_field(event, "decompressed_size")
            output_sha256 = _str_field(event, "decompressed_sha256")
            load_address = _int_field(event, "target_start_address")
            entrypoint = _int_field(event, "entrypoint")
            source_section = _int_field(event, "source_section") or 0
            marker_offset = _int_field(event, "unpacker_marker_offset") or 0
            compressed_source_section_offset = _int_field(event, "compressed_source_section_offset")
            source_section_payload_start = section_payload_starts.get(source_section)
            packed_file_offset = (
                compressed_source_section_offset + source_section_payload_start
                if (
                    compressed_source_section_offset is not None
                    and source_section_payload_start is not None
                )
                else None
            )
            native_provider_id = _native_unpacker_provider_id(event)
            assert event_id is not None
            assert output_size is not None
            assert output_sha256 is not None
            assert load_address is not None
            assert entrypoint is not None
            role_fields = _decompression_role_fields(event)
            local_target_id = _recognized_unpacker_payload_child_local_id(parent_local_target_id, event)
            target_name = disk_child_project_id(disk_id, local_target_id)
            target_dir = disk_children_root / local_target_id
            child_entry_path = (
                f"{parent_entry_path}::{_str_field(event, 'codec_id') or 'native'}_"
                f"{source_section:02x}_{marker_offset:08x}"
            )
            origin = {
                "project_origin_kind_id": PROJECT_ORIGIN_KIND_DERIVED_DECOMPRESSED_PAYLOAD,
                "kind": "derived_decompressed_payload",
                "parent_disk_id": disk_id,
                "parent_target": parent_target_name,
                "parent_entry_path": parent_entry_path,
                "child_entry_path": child_entry_path,
                "target_role_id": TARGET_ROLE_DECOMPRESSED_PAYLOAD,
                "target_role": "decompressed_payload",
                "source_section": source_section,
                "target_type": "raw_binary",
                **role_fields,
                "packed_file_offset": packed_file_offset,
                "packed_section_offset": compressed_source_section_offset,
                "codec_id": _str_field(event, "codec_id"),
                "codec_name": _str_field(event, "codec_name"),
                "provider_id": native_provider_id,
                "event_id": event_id,
                "decompressed_size": output_size,
                "decompressed_sha256": output_sha256,
                "load_address": load_address,
                "entrypoint": entrypoint,
            }
            if target_dir.exists() and not target_dir.is_dir():
                continue
            if not target_dir.exists():
                create_project_at_path(
                    disk_child_target_relpath(disk_id, local_target_id).as_posix(),
                    project_root=project_root,
                    origin=origin,
                )
                created_dirs.append(target_dir)
            clean_obsolete_target_local_state(target_dir)
            output_path = target_dir / "binary.bin"
            temp_output_path = target_dir / ".recognized-unpacker-output.tmp"
            try:
                result = materialize_recognized_unpacker_event_with_c_backend(
                    "amiga-hunk",
                    parent_temp_path,
                    event_id,
                    temp_output_path,
                    project_root=project_root,
                )
                materialized = result.get("decompressed")
                if not isinstance(materialized, dict) or result.get("status") != "ok":
                    raise DiskAnalysisError(f"C recognized unpacker did not materialise {child_entry_path}")
                actual_bytes = temp_output_path.read_bytes()
                actual_hash = hashlib.sha256(actual_bytes).hexdigest()
                if len(actual_bytes) != output_size or actual_hash != output_sha256:
                    raise DiskAnalysisError(f"C recognized unpacker output mismatch for {child_entry_path}")
                temp_output_path.replace(output_path)
            finally:
                with contextlib.suppress(FileNotFoundError):
                    temp_output_path.unlink()
            set_project_origin(target_dir, origin=origin)
            code_start_offset = entrypoint - load_address if entrypoint >= load_address else 0
            if code_start_offset >= output_size:
                code_start_offset = 0
            write_source_descriptor(
                target_dir,
                {
                    "kind": "raw_binary",
                    "address_model": "runtime_absolute",
                    "path": output_path.relative_to(project_root).as_posix(),
                    "load_address": load_address,
                    "entrypoint": entrypoint,
                    "code_start_offset": code_start_offset,
                    "parent_disk_id": disk_id,
                },
            )
            write_target_metadata(target_dir, TargetMetadata(target_type="raw_binary", entry_register_seeds=()))
            relationship = {
                "kind_id": DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD,
                "kind": "decompressed_payload",
                "parent_target": parent_target_name,
                "parent_entry_path": parent_entry_path,
                "child_target": target_name,
                "child_entry_path": child_entry_path,
                "decompressed_size": output_size,
                "load_address": load_address,
                "entrypoint": entrypoint,
                "packed_file_offset": packed_file_offset,
                "packed_section_offset": compressed_source_section_offset,
                "codec_id": _str_field(event, "codec_id"),
                "codec_name": _str_field(event, "codec_name"),
                "provider_id": native_provider_id,
                "event_id": event_id,
                "source_kind_id": DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER,
                "source_kind": "recognized_unpacker",
                "source_section": source_section,
                "unpacker_marker_offset": marker_offset,
                **role_fields,
            }
            decompression_record = {
                "schema_version": 1,
                "parent_target_id": parent_target_name,
                "child_target_id": target_name,
                "parent_entry_path": parent_entry_path,
                "child_entry_path": child_entry_path,
                **role_fields,
                "compressor": {
                    "id": _str_field(event, "codec_id"),
                    "name": _str_field(event, "codec_name"),
                    "confidence": _str_field(event, "payload_role_confidence") or "tool_inferred",
                },
                "source": {
                    "kind_id": DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER,
                    "kind": "recognized_unpacker",
                    "provider_id": _str_field(event, "provider_id"),
                    "event_id": event_id,
                "source_section": source_section,
                "unpacker_marker_offset": marker_offset,
                "packed_section_offset": _int_field(event, "compressed_source_section_offset"),
                "compressed_source_section_offset": _int_field(event, "compressed_source_section_offset"),
                "compressed_source_section_end_offset": _int_field(
                    event, "compressed_source_section_end_offset"
                ),
                    "compressed_source_consumed_section_offset": _int_field(
                        event, "compressed_source_consumed_section_offset"
                    ),
                    "postpass_source_start_address": _int_field(event, "postpass_source_start_address"),
                    "postpass_source_end_address": _int_field(event, "postpass_source_end_address"),
                    "postpass_source_consumed_address": _int_field(event, "postpass_source_consumed_address"),
                    "postpass_escape_byte": _int_field(event, "postpass_escape_byte"),
                },
                "decompressed": {
                    "size": output_size,
                    "sha256": output_sha256,
                    "load_address": load_address,
                    "entrypoint": entrypoint,
                },
                "extraction": {"method": native_provider_id},
                "relationship": relationship,
            }
            _write_text(
                target_dir / "decompression.json",
                json.dumps(decompression_record, indent=2, sort_keys=True) + "\n",
            )
            mark_project_updated(target_dir)
            parent_derived.append(
                {
                    "kind_id": DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD,
                    "kind": "decompressed_payload",
                    "target_name": target_name,
                    "provider_id": native_provider_id,
                    "event_id": event_id,
                    "codec_id": _str_field(event, "codec_id"),
                    **role_fields,
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
        for event in _materializable_self_decrunch_events(analysis):
            event_id = _str_field(event, "event_id")
            output_size = _int_field(event, "simulated_output_size")
            output_sha256 = _str_field(event, "simulated_output_sha256")
            load_address = _int_field(event, "load_address")
            entrypoint = _int_field(event, "entrypoint")
            code_section = _int_field(event, "decompressor_code_section") or 0
            code_entry = _int_field(event, "decompressor_entry_offset") or 0
            transfer_offset = _int_field(event, "transfer_offset")
            assert event_id is not None
            assert output_size is not None
            assert output_sha256 is not None
            assert load_address is not None
            assert entrypoint is not None
            role_fields = _decompression_role_fields(event)
            local_target_id = _self_decrunch_payload_child_local_id(parent_local_target_id, event)
            target_name = disk_child_project_id(disk_id, local_target_id)
            target_dir = disk_children_root / local_target_id
            child_entry_path = f"{parent_entry_path}::simdecrunch_{code_section:02x}_{code_entry:08x}"
            origin = {
                "project_origin_kind_id": PROJECT_ORIGIN_KIND_DERIVED_DECOMPRESSED_PAYLOAD,
                "kind": "derived_decompressed_payload",
                "parent_disk_id": disk_id,
                "parent_target": parent_target_name,
                "parent_entry_path": parent_entry_path,
                "child_entry_path": child_entry_path,
                "target_role_id": TARGET_ROLE_DECOMPRESSED_PAYLOAD,
                "target_role": "decompressed_payload",
                "target_type": "raw_binary",
                "packed_section_offset": transfer_offset,
                **role_fields,
                "codec_id": _str_field(event, "codec_id"),
                "codec_name": _str_field(event, "codec_name"),
                "provider_id": "m68k-sim-decrunch",
                "event_id": event_id,
                "decompressed_size": output_size,
                "decompressed_sha256": output_sha256,
                "load_address": load_address,
                "entrypoint": entrypoint,
                "source_section": code_section,
            }
            if target_dir.exists() and not target_dir.is_dir():
                continue
            if not target_dir.exists():
                create_project_at_path(
                    disk_child_target_relpath(disk_id, local_target_id).as_posix(),
                    project_root=project_root,
                    origin=origin,
                )
                created_dirs.append(target_dir)
            clean_obsolete_target_local_state(target_dir)
            output_path = target_dir / "binary.bin"
            temp_output_path = target_dir / ".self-decrunch-output.tmp"
            try:
                result = materialize_self_decrunch_event_with_c_backend(
                    "amiga-hunk",
                    parent_temp_path,
                    event_id,
                    temp_output_path,
                    project_root=project_root,
                )
                materialized = result.get("decompressed")
                if not isinstance(materialized, dict) or result.get("status") != "ok":
                    raise DiskAnalysisError(f"C self-decrunch did not materialise {child_entry_path}")
                actual_bytes = temp_output_path.read_bytes()
                actual_hash = hashlib.sha256(actual_bytes).hexdigest()
                if len(actual_bytes) != output_size or actual_hash != output_sha256:
                    raise DiskAnalysisError(f"C self-decrunch output mismatch for {child_entry_path}")
                temp_output_path.replace(output_path)
            finally:
                with contextlib.suppress(FileNotFoundError):
                    temp_output_path.unlink()
            set_project_origin(target_dir, origin=origin)
            code_start_offset = entrypoint - load_address if entrypoint >= load_address else 0
            if code_start_offset >= output_size:
                code_start_offset = 0
            write_source_descriptor(
                target_dir,
                {
                    "kind": "raw_binary",
                    "address_model": "runtime_absolute",
                    "path": output_path.relative_to(project_root).as_posix(),
                    "load_address": load_address,
                    "entrypoint": entrypoint,
                    "code_start_offset": code_start_offset,
                    "parent_disk_id": disk_id,
                },
            )
            write_target_metadata(target_dir, TargetMetadata(target_type="raw_binary", entry_register_seeds=()))
            relationship = {
                "kind_id": DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD,
                "kind": "decompressed_payload",
                "parent_target": parent_target_name,
                "parent_entry_path": parent_entry_path,
                "child_target": target_name,
                "child_entry_path": child_entry_path,
                "decompressed_size": output_size,
                "load_address": load_address,
                "entrypoint": entrypoint,
                "codec_id": _str_field(event, "codec_id"),
                "codec_name": _str_field(event, "codec_name"),
                "provider_id": "m68k-sim-decrunch",
                "event_id": event_id,
                "source_kind_id": DECOMPRESSION_SOURCE_SELF_DECRUNCHER,
                "source_kind": "self_decruncher",
                "decompressor_code_section": code_section,
                "decompressor_entry_offset": code_entry,
                **role_fields,
            }
            if transfer_offset is not None:
                relationship["transfer_offset"] = transfer_offset
            decompression_record = {
                "schema_version": 1,
                "parent_target_id": parent_target_name,
                "child_target_id": target_name,
                "parent_entry_path": parent_entry_path,
                "child_entry_path": child_entry_path,
                **role_fields,
                "compressor": {
                    "id": _str_field(event, "codec_id"),
                    "name": _str_field(event, "codec_name"),
                    "confidence": _str_field(event, "payload_role_confidence") or "tool_inferred",
                },
                "source": {
                    "kind_id": DECOMPRESSION_SOURCE_SELF_DECRUNCHER,
                    "kind": "self_decruncher",
                    "provider_id": "m68k-sim-decrunch",
                    "event_id": event_id,
                    "decompressor_code_section": code_section,
                    "decompressor_entry_offset": code_entry,
                    "transfer_offset": transfer_offset,
                },
                "decompressed": {
                    "size": output_size,
                    "sha256": output_sha256,
                    "load_address": load_address,
                    "entrypoint": entrypoint,
                },
                "extraction": {
                    "method": "m68k-sim-decrunch",
                    "simulated_stop_reason": _str_field(event, "simulated_stop_reason_name"),
                    "simulated_step_count": _int_field(event, "simulated_step_count"),
                    "simulated_write_count": _int_field(event, "simulated_write_count"),
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
                    "kind_id": DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD,
                    "kind": "decompressed_payload",
                    "target_name": target_name,
                    "provider_id": "m68k-sim-decrunch",
                    "event_id": event_id,
                    "codec_id": _str_field(event, "codec_id"),
                    **role_fields,
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
        with contextlib.suppress(FileNotFoundError):
            parent_temp_path.unlink()
    return MaterializedPayloadChildren(parent_derived, child_targets, created_dirs, True)


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
    resolved_disk_id = _normalize_disk_id_arg(disk_id) or derive_disk_id(adf_file)
    disk_target_root = disk_project_root(project_root, resolved_disk_id)
    disk_children_root = disk_project_targets_dir(project_root, resolved_disk_id)
    manifest_path = disk_target_root / "manifest.json"
    disk_root_exists = disk_target_root.exists()
    existing_state = _load_disk_target_state(_disk_target_state_path(disk_target_root))
    existing_state_subtargets = _coerce_state_subtargets(existing_state.get("subtargets"))
    existing_payload_target_ids = _coerce_payload_target_ids(
        existing_state.get("payload_nodes"),
        parent_ids=set(existing_state_subtargets.keys()),
    )
    existing_imported_targets: dict[str, ImportedTarget] = {}
    if disk_root_exists:
        if manifest_path.exists():
            existing_imported_targets = {
                target.target_name: target
                for target in DiskManifest.load(manifest_path).imported_targets
                if target.target_name in existing_state_subtargets
                or target.target_name in existing_payload_target_ids
            }
    else:
        disk_target_root.mkdir(parents=True)
        initialize_project_metadata(
            disk_target_root,
            origin={
                "kind": "user_upload",
                "filename": adf_file.name,
                "platform": "amiga-disk",
                "source_path": adf_file.as_posix(),
                "sha256": hashlib.sha256(adf_file.read_bytes()).hexdigest(),
                "size": adf_file.stat().st_size,
            },
        )
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
        if not disk_root_exists:
            initialize_project_metadata(disk_target_root, origin=disk_origin)
        if progress_fn is not None:
            progress_fn("analyze_disk", 1, 4)
        analysis = analyze_adf(adf_file, include_tracks=True)

        imported_targets_by_name: dict[str, ImportedTarget] = dict(existing_imported_targets)
        auto_discovered_target_names: set[str] = set()

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
        auto_discovered_target_names.add(bootblock_target_name)
        if bootblock_target_dir.exists():
            if not bootblock_target_dir.is_dir():
                raise DiskAnalysisError(f"Target already exists but is not a directory: {bootblock_target_name}")
        else:
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
        clean_obsolete_target_local_state(bootblock_target_dir)
        bootblock_binary_path = bootblock_target_dir / "binary.bin"
        _write_bytes(bootblock_binary_path, disk_bytes[bootblock_byte_offset:bootblock_byte_offset + bootblock_byte_size])
        bootblock_source["path"] = bootblock_binary_path.relative_to(project_root).as_posix()
        bootblock_source["parent_disk_id"] = resolved_disk_id
        write_source_descriptor(bootblock_target_dir, bootblock_source)
        write_target_metadata(bootblock_target_dir, TargetMetadata.from_dict(bootblock_import.target_metadata))
        mark_project_updated(bootblock_target_dir)

        imported_targets_by_name[bootblock_target_name] = ImportedTarget(
            target_name=bootblock_target_name,
            target_path=disk_child_target_relpath(resolved_disk_id, bootblock_local_name).as_posix(),
            entry_path="bootblock",
            binary_path=f"{adf_file.as_posix()}::bootblock",
            target_type="bootblock",
        )
        bootblock_source_analysis = _analyze_bootblock_source_for_disk_reads(
            bootblock_target_dir,
            project_root=project_root,
        )
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
            auto_discovered_target_names.add(target_name)
            if target_dir.exists():
                if not target_dir.is_dir():
                    raise DiskAnalysisError(f"Target already exists: {target_name}")
            else:
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
            clean_obsolete_target_local_state(target_dir)
            binary_path = target_dir / "binary.bin"
            _write_bytes(binary_path, stage_bytes)
            source_descriptor = dict(stage.import_target.source)
            source_descriptor.pop("byte_offset", None)
            source_descriptor.pop("byte_size", None)
            source_descriptor["path"] = binary_path.relative_to(project_root).as_posix()
            source_descriptor["parent_disk_id"] = resolved_disk_id
            write_source_descriptor(target_dir, source_descriptor)
            write_target_metadata(target_dir, TargetMetadata.from_dict(_bootloader_stage_target_metadata(stage, analysis)))
            mark_project_updated(target_dir)
            imported_targets_by_name[target_name] = ImportedTarget(
                target_name=target_name,
                target_path=disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                entry_path=stage_entry_path,
                binary_path=f"{adf_file.as_posix()}::{stage_entry_path}",
                target_type=stage.import_target.target_type,
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
            auto_discovered_target_names.add(target_name)
            if target_dir.exists():
                if not target_dir.is_dir():
                    raise DiskAnalysisError(f"Target already exists: {target_name}")
            else:
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
            clean_obsolete_target_local_state(target_dir)
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
            imported_targets_by_name[target_name] = ImportedTarget(
                target_name=target_name,
                target_path=disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                entry_path=span_entry_path,
                binary_path=f"{adf_file.as_posix()}::{span_entry_path}",
                target_type=import_target.target_type,
            )
        for import_target, stage_bytes in _bootblock_disk_read_stage_targets(bootblock_source_analysis, disk_bytes):
            assert import_target.source is not None
            stage_entry_path = _import_target_required_text(
                import_target.entry_path, "entry_path", import_target.target_type
            )
            local_target_name = _import_target_required_text(
                import_target.local_target_id, "local_target_id", import_target.target_type
            )
            target_name = disk_child_project_id(resolved_disk_id, local_target_name)
            if target_name in imported_targets_by_name:
                stage_index = 1
                while True:
                    stage_entry_path = f"bootloader/stage_{stage_index}"
                    local_target_name = f"amiga_raw_bootloader_stage_{stage_index}"
                    target_name = disk_child_project_id(resolved_disk_id, local_target_name)
                    if target_name not in imported_targets_by_name:
                        break
                    stage_index += 1
            target_dir = disk_children_root / local_target_name
            auto_discovered_target_names.add(target_name)
            if target_dir.exists():
                if not target_dir.is_dir():
                    raise DiskAnalysisError(f"Target already exists: {target_name}")
            else:
                create_project_at_path(
                    disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                    project_root=project_root,
                    origin={
                        "kind": "disk_child",
                        "parent_disk_id": resolved_disk_id,
                        "target_role": "bootloader_stage",
                        "entry_path": stage_entry_path,
                        "target_type": import_target.target_type,
                        "source_path": adf_file.as_posix(),
                    },
                )
                created_target_dirs.append(target_dir)
            clean_obsolete_target_local_state(target_dir)
            binary_path = target_dir / "binary.bin"
            _write_bytes(binary_path, stage_bytes)
            source_descriptor = dict(import_target.source)
            source_descriptor.pop("byte_offset", None)
            source_descriptor.pop("byte_size", None)
            source_descriptor["path"] = binary_path.relative_to(project_root).as_posix()
            source_descriptor["parent_disk_id"] = resolved_disk_id
            write_source_descriptor(target_dir, source_descriptor)
            write_target_metadata(target_dir, TargetMetadata.from_dict(import_target.target_metadata))
            mark_project_updated(target_dir)
            imported_targets_by_name[target_name] = ImportedTarget(
                target_name=target_name,
                target_path=disk_child_target_relpath(resolved_disk_id, local_target_name).as_posix(),
                entry_path=stage_entry_path,
                binary_path=f"{adf_file.as_posix()}::{stage_entry_path}",
                target_type=import_target.target_type,
            )
        startup_parse_status = _startup_parse_status_payload(
            TARGET_STATE_STARTUP_PARSE_STATUS_MISSING,
            reason="No DOS filesystem available for startup-sequence import discovery",
            source_path=TARGET_STATE_STARTUP_PARSE_SOURCE_PATH,
        )
        candidate_rejects: list[dict[str, object]] = []
        startup_sequence_entries: list[dict[str, object]] = []
        if _has_dos_filesystem(analysis):
            _require_complete_dos_analysis(analysis)
            if progress_fn is not None:
                progress_fn("import_targets", 3, 4)
            startup_candidates: list[dict[str, object]] = []
            startup_parse_warnings: list[dict[str, object]] = []
            if analysis.files is not None:
                startup_candidates, startup_parse_status, startup_parse_warnings = _discover_startup_sequence_targets(
                    analysis,
                    available_entry_paths=_startup_disk_entry_paths(analysis),
                    adf_path=adf_file,
                    project_root=project_root,
                )
            for warning in startup_parse_warnings:
                if not isinstance(warning, dict):
                    continue
                warn_path = warning.get("path")
                if not isinstance(warn_path, str):
                    warn_path = TARGET_STATE_STARTUP_PARSE_SOURCE_PATH
                reason_code, reason_detail = _coerce_startup_warning_reason(warning)
                startup_command = _str_field(warning, "command")
                startup_sequence_entries.append(
                    {
                        "line": _int_field(warning, "line"),
                        "command": startup_command,
                        "path": warn_path,
                        "status": "rejected",
                        "reason_code": reason_code,
                        "reason_detail": reason_detail,
                    }
                )
                _append_startup_candidate_reject(
                    candidate_rejects,
                    path=warn_path,
                    reason_code=reason_code,
                    reason_detail=reason_detail,
                    line=_int_field(warning, "line"),
                    command=startup_command,
                )
            startup_imported_paths: set[str] = set()
            for startup_entry in startup_candidates:
                candidate_path = _str_field(startup_entry, "path")
                if candidate_path is None:
                    continue
                path_key = candidate_path.strip().strip("/").lower()
                startup_line = _int_field(startup_entry, "line")
                startup_command = _str_field(startup_entry, "command")
                if path_key in startup_imported_paths:
                    reason_code = TARGET_STATE_REJECT_REASON_DUPLICATE
                    reason_detail = "Filtered duplicate startup reference"
                    startup_sequence_entries.append(
                        {
                            "line": startup_line,
                            "command": startup_command,
                            "path": candidate_path,
                            "status": "rejected",
                            "reason_code": reason_code,
                            "reason_detail": reason_detail,
                        }
                    )
                    _append_startup_candidate_reject(
                        candidate_rejects,
                        path=candidate_path,
                        reason_code=reason_code,
                        reason_detail=reason_detail,
                        line=startup_line,
                        command=startup_command,
                    )
                    continue
                startup_imported_paths.add(path_key)
                entry = _find_dos_entry_by_path(analysis, candidate_path)
                if entry is None:
                    reason_code = TARGET_STATE_REJECT_REASON_PATH_NOT_FOUND
                    reason_detail = "startup-sequence candidate was not found in disk index"
                    startup_sequence_entries.append(
                        {
                            "line": startup_line,
                            "command": startup_command,
                            "path": candidate_path,
                            "status": "missing",
                            "reason_code": reason_code,
                            "reason_detail": reason_detail,
                        }
                    )
                    _append_startup_candidate_reject(
                        candidate_rejects,
                        path=candidate_path,
                        reason_code=reason_code,
                        reason_detail=reason_detail,
                        line=startup_line,
                        command=startup_command,
                    )
                    continue
                entry_content = getattr(entry, "content", None)
                if entry_content is None:
                    reason_code = TARGET_STATE_REJECT_REASON_UNSUPPORTED_FORMAT
                    reason_detail = "Disk entry does not have import metadata"
                    startup_sequence_entries.append(
                        {
                            "line": startup_line,
                            "command": startup_command,
                            "path": candidate_path,
                            "status": "rejected",
                            "reason_code": reason_code,
                            "reason_detail": reason_detail,
                        }
                    )
                    _append_startup_candidate_reject(
                        candidate_rejects,
                        path=candidate_path,
                        reason_code=reason_code,
                        reason_detail=reason_detail,
                        line=startup_line,
                        command=startup_command,
                    )
                    continue
                import_target = cast(Any, getattr(entry_content, "import_target", None))
                if import_target is None:
                    reason_code = TARGET_STATE_REJECT_REASON_UNSUPPORTED_FORMAT
                    reason_detail = "Disk entry type is unsupported for direct import"
                    startup_sequence_entries.append(
                        {
                            "line": startup_line,
                            "command": startup_command,
                            "path": candidate_path,
                            "status": "rejected",
                            "reason_code": reason_code,
                            "reason_detail": reason_detail,
                        }
                    )
                    _append_startup_candidate_reject(
                        candidate_rejects,
                        path=candidate_path,
                        reason_code=reason_code,
                        reason_detail=reason_detail,
                        line=startup_line,
                        command=startup_command,
                    )
                    continue
                startup_sequence_entries.append(
                    {
                        "line": startup_line,
                        "command": startup_command,
                        "path": candidate_path,
                        "status": "pending",
                    }
                )
                imported_target, child_targets = _import_disk_file_entry(
                    adf_file=adf_file,
                    disk_id=resolved_disk_id,
                    disk_children_root=disk_children_root,
                    import_target=import_target,
                    created_target_dirs=created_target_dirs,
                    project_root=project_root,
                )
                target_name = imported_target.target_name
                imported_targets_by_name[target_name] = imported_target
                auto_discovered_target_names.add(target_name)
                for child_target in child_targets:
                    imported_targets_by_name[child_target.target_name] = child_target
                    auto_discovered_target_names.add(child_target.target_name)
                startup_sequence_entries[-1]["status"] = "imported"
                startup_sequence_entries[-1]["target_name"] = target_name

        startup_parse_status["startup_sequence_entries"] = startup_sequence_entries
        state_subtargets_by_id: dict[str, dict[str, object]] = {
            target_id: dict(item) for target_id, item in existing_state_subtargets.items()
        }
        decompressed_related_target_names: set[str] = set()
        for existing_import in imported_targets_by_name.values():
            if isinstance(existing_import.derived_from, dict):
                decompressed_related_target_names.add(existing_import.target_name)
                parent_target = _str_field(existing_import.derived_from, "parent_target")
                if isinstance(parent_target, str):
                    decompressed_related_target_names.add(parent_target)
        for target_id, imported_target in imported_targets_by_name.items():
            if target_id in auto_discovered_target_names:
                state_subtargets_by_id[target_id] = {
                    "id": target_id,
                    "path": imported_target.target_path,
                    "state": TargetStateSubtargetState.ADDED,
                    "origin": TargetStateSubtargetOrigin.AUTO,
                    "reason_code": None,
                    "reason_detail": None,
                    "added_by_import": True,
                }
                continue
            if (
                _is_legacy_startup_prefix(imported_target.entry_path)
                and target_id not in decompressed_related_target_names
            ):
                continue

            state_entry = state_subtargets_by_id.get(target_id)
            if state_entry is None:
                continue
            if state_entry.get("origin") is TargetStateSubtargetOrigin.MANUAL:
                state_entry = dict(state_entry)
                state_entry["id"] = target_id
                state_entry["path"] = imported_target.target_path
                state_entry["state"] = TargetStateSubtargetState.ADDED
                state_entry["added_by_import"] = False
                state_subtargets_by_id[target_id] = state_entry

        for target_id, state_entry in list(state_subtargets_by_id.items()):
            if state_entry.get("origin") is not TargetStateSubtargetOrigin.MANUAL and target_id in auto_discovered_target_names:
                continue
            state_subtargets_by_id.pop(target_id, None)
            imported_targets_by_name.pop(target_id, None)
            subtarget_path = Path(_str_field(state_entry, "path") or target_id)
            if not subtarget_path.is_absolute():
                subtarget_path = PROJECT_ROOT / subtarget_path
            if subtarget_path.exists() and subtarget_path.is_dir():
                shutil.rmtree(subtarget_path, ignore_errors=True)
        state_subtargets = [
            dict(item) for _, item in sorted(state_subtargets_by_id.items(), key=lambda item: item[0])
        ]

        if progress_fn is not None:
            progress_fn("write_manifest", 4, 4)
        imported_targets = sorted(imported_targets_by_name.values(), key=lambda target: target.entry_path)
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
        _write_disk_target_state(
            _disk_target_state_path(disk_target_root),
            _disk_target_state_payload(
                schema_version=TARGET_STATE_SCHEMA_VERSION,
                import_mode=TARGET_STATE_IMPORT_MODE,
                imported_targets=imported_targets,
                state_subtargets=state_subtargets,
                source_path=adf_file.as_posix(),
                startup_sequence_parse=startup_parse_status,
                candidate_rejects=candidate_rejects,
            ),
        )
        mark_project_updated(disk_target_root)
        return manifest
    except Exception:
        for target_dir in reversed(created_target_dirs):
            shutil.rmtree(target_dir, ignore_errors=True)
        if not disk_root_exists:
            shutil.rmtree(disk_target_root, ignore_errors=True)
        raise


def refresh_decompressed_payload_children(
    disk_id: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> DiskManifest:
    from amiga_reversing.disasm.projects import mark_project_updated

    normalized_disk_id = _normalize_disk_id_arg(disk_id)
    if normalized_disk_id is None:
        raise DiskAnalysisError("disk_id is required for decompression refresh")
    disk_target_root = disk_project_root(project_root, normalized_disk_id)
    manifest_path = disk_target_root / "manifest.json"
    if not manifest_path.exists():
        raise DiskAnalysisError(f"Disk manifest does not exist: {manifest_path}")
    manifest = DiskManifest.load(manifest_path)
    adf_file = Path(manifest.source_path)
    if not adf_file.is_absolute():
        adf_file = project_root / adf_file
    if not adf_file.exists():
        raise DiskAnalysisError(f"Disk source does not exist: {adf_file}")
    existing_state = _load_disk_target_state(_disk_target_state_path(disk_target_root))
    startup_sequence_parse = _coerce_startup_parse_status(
        existing_state.get("startup_sequence_parse")
    )
    candidate_rejects = _coerce_candidate_rejects(existing_state.get("candidate_rejects"))
    imported_by_name = {target.target_name: target for target in manifest.imported_targets}
    disk_children_root = disk_project_targets_dir(project_root, normalized_disk_id)
    refreshed_by_parent: dict[str, list[dict[str, object]]] = {}
    refreshed_children: dict[str, ImportedTarget] = {}
    refreshed_parent_names: set[str] = set()
    for target in manifest.imported_targets:
        if target.derived_from is not None or not _target_type_may_contain_packed_payload(target.target_type):
            continue
        local_target_id = Path(target.target_path).name
        materialized = _materialize_decompressed_payload_children(
            adf_file=adf_file,
            disk_id=normalized_disk_id,
            disk_children_root=disk_children_root,
            parent_local_target_id=local_target_id,
            parent_target_name=target.target_name,
            parent_entry_path=target.entry_path,
            project_root=project_root,
        )
        if not materialized.analysis_completed:
            continue
        refreshed_parent_names.add(target.target_name)
        refreshed_by_parent[target.target_name] = materialized.parent_derived
        for child in materialized.child_targets:
            refreshed_children[child.target_name] = child
    for child in refreshed_children.values():
        imported_by_name[child.target_name] = child
    for target in list(imported_by_name.values()):
        relationship = target.derived_from
        if not isinstance(relationship, dict) or not _is_decompressed_payload_relationship(relationship):
            continue
        parent_name = relationship.get("parent_target")
        if not isinstance(parent_name, str) or parent_name not in refreshed_parent_names:
            continue
        if target.target_name in refreshed_children:
            continue
        imported_by_name.pop(target.target_name, None)
        target_dir = (project_root / target.target_path).resolve()
        children_root = disk_children_root.resolve()
        if target_dir.parent == children_root and target_dir.exists():
            shutil.rmtree(target_dir)
    refreshed_targets: list[ImportedTarget] = []
    for target in imported_by_name.values():
        parent_derived = refreshed_by_parent.get(target.target_name)
        if parent_derived is not None:
            refreshed_targets.append(
                ImportedTarget(
                    target_name=target.target_name,
                    target_path=target.target_path,
                    entry_path=target.entry_path,
                    binary_path=target.binary_path,
                    target_type=target.target_type,
                    derived_from=target.derived_from,
                    derived_targets=parent_derived or None,
                )
            )
        else:
            refreshed_targets.append(target)
    refreshed_targets.sort(key=lambda target: target.entry_path)
    refreshed_manifest = DiskManifest(
        schema_version=manifest.schema_version,
        disk_id=manifest.disk_id,
        source_path=manifest.source_path,
        source_sha256=manifest.source_sha256,
        analysis=manifest.analysis,
        imported_targets=refreshed_targets,
        bootblock_target_name=manifest.bootblock_target_name,
        bootblock_target_path=manifest.bootblock_target_path,
    )
    _write_text(manifest_path, json.dumps(refreshed_manifest.to_dict(), indent=2, sort_keys=True) + "\n")
    _write_disk_target_state(
        _disk_target_state_path(disk_target_root),
        _disk_target_state_payload(
            schema_version=TARGET_STATE_SCHEMA_VERSION,
            import_mode=TARGET_STATE_IMPORT_MODE,
            imported_targets=refreshed_targets,
            source_path=str(adf_file),
            startup_sequence_parse=startup_sequence_parse,
            candidate_rejects=candidate_rejects,
        ),
    )
    mark_project_updated(disk_target_root)
    return refreshed_manifest


def import_adf(
    adf_path: str | Path,
    *,
    disk_id: str | None = None,
    project_root: Path = PROJECT_ROOT,
    progress_fn: Callable[[str, int, int], None] | None = None,
) -> DiskManifest:
    return create_disk_project(adf_path, disk_id=disk_id, project_root=project_root, progress_fn=progress_fn)
