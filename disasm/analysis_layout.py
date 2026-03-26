from __future__ import annotations

from disasm.binary_source import BinarySource
from disasm.target_metadata import TargetMetadata, target_structure_spec


def target_structure_entrypoint_offsets(target_metadata: TargetMetadata | None) -> tuple[int, ...]:
    structure = target_structure_spec(target_metadata)
    if structure is None:
        return ()
    return tuple(entry.offset for entry in structure.entrypoints)


def target_primary_entrypoint_offset(target_metadata: TargetMetadata | None) -> int | None:
    entrypoints = target_structure_entrypoint_offsets(target_metadata)
    if not entrypoints:
        return None
    return entrypoints[0]


def target_structure_analysis_start_offset(target_metadata: TargetMetadata | None) -> int | None:
    structure = target_structure_spec(target_metadata)
    if structure is None:
        return None
    return structure.analysis_start_offset


def resolved_raw_analysis_start_offset(source: BinarySource, target_metadata: TargetMetadata | None) -> int:
    assert source.kind == "raw_binary"
    structure_start = target_structure_analysis_start_offset(target_metadata)
    if structure_start is not None and structure_start != source.code_start_offset:
        raise ValueError(
            f"Raw target structure analysis start 0x{structure_start:X} does not match "
            f"source code_start_offset 0x{source.code_start_offset:X}"
        )
    return source.code_start_offset


def resolved_raw_analysis_base_addr(source: BinarySource, target_metadata: TargetMetadata | None) -> int:
    assert source.kind == "raw_binary"
    resolved_raw_analysis_start_offset(source, target_metadata)
    if source.address_model == "runtime_absolute":
        return source.code_start_address
    return source.code_start_offset


def resolved_analysis_start_offset(source: BinarySource, target_metadata: TargetMetadata | None) -> int:
    if source.kind == "raw_binary":
        return resolved_raw_analysis_start_offset(source, target_metadata)
    structure_start = target_structure_analysis_start_offset(target_metadata)
    if structure_start is None:
        return 0
    return int(structure_start)


def resolved_entry_points(
    source: BinarySource,
    target_metadata: TargetMetadata | None,
    explicit_entry_points: tuple[int, ...],
) -> tuple[int, ...]:
    if source.kind == "raw_binary":
        structure_entries = target_structure_entrypoint_offsets(target_metadata)
        local_entry_offsets = structure_entries or (source.local_entrypoint,)
        if local_entry_offsets[0] != source.local_entrypoint:
            raise ValueError(
                f"Raw target structure entrypoint 0x{local_entry_offsets[0]:X} does not match "
                f"source entrypoint 0x{source.local_entrypoint:X}"
            )
        base_addr = resolved_raw_analysis_base_addr(source, target_metadata)
        code_start_offset = resolved_raw_analysis_start_offset(source, target_metadata)
        return tuple(base_addr + (offset - code_start_offset) for offset in local_entry_offsets)
    if explicit_entry_points:
        return explicit_entry_points
    return target_structure_entrypoint_offsets(target_metadata)
