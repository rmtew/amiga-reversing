from __future__ import annotations
"""Hunk preparation helpers for disassembly session assembly."""

from collections.abc import Mapping
from pathlib import Path

from m68k.analysis import RelocatedSegment
from m68k.indirect_core import IndirectSite
from m68k.os_calls import CallArgumentAnnotation, OsKb, PlatformState, TypedMemoryRegion

from disasm.types import (
    DisasmBlockLike,
    DisassemblySession,
    EntityRecord,
    HunkDisassemblySession,
    JumpTableRegion,
)


def prepare_hunk_code(code: bytes, relocated_segments: list[RelocatedSegment]
                      ) -> tuple[bytes, int, list[RelocatedSegment], int, int]:
    code_size = len(code)
    reloc_file_offset = 0
    reloc_base_addr = 0
    if relocated_segments:
        seg = relocated_segments[0]
        reloc_file_offset = seg.file_offset
        reloc_base_addr = seg.base_addr
        payload_size = code_size - reloc_file_offset
        runtime_size = reloc_base_addr + payload_size
        runtime_code = bytearray(runtime_size)
        runtime_code[:reloc_file_offset] = code[:reloc_file_offset]
        runtime_code[reloc_base_addr:] = code[reloc_file_offset:]
        code = bytes(runtime_code)
        code_size = runtime_size
    return code, code_size, relocated_segments, reloc_file_offset, reloc_base_addr


def build_session_object(*, target_name: str | None, binary_path: str | Path,
                         entities_path: str | Path, output_path: str | Path | None,
                         entities: list[EntityRecord],
                         hunk_sessions: list[HunkDisassemblySession],
                         profile_stages: bool) -> DisassemblySession:
    binary_path = Path(binary_path)
    return DisassemblySession(
        target_name=target_name,
        binary_path=binary_path,
        entities_path=Path(entities_path),
        analysis_cache_path=binary_path.with_suffix(".analysis"),
        output_path=Path(output_path) if output_path else None,
        entities=entities,
        hunk_sessions=hunk_sessions,
        profile_stages=profile_stages,
    )


def build_hunk_session(*,
                       hunk_index: int,
                       code: bytes,
                       code_size: int,
                       entities: list[EntityRecord],
                       blocks: Mapping[int, DisasmBlockLike],
                       hint_blocks: Mapping[int, DisasmBlockLike],
                       code_addrs: set[int],
                       hint_addrs: set[int],
                       reloc_map: dict[int, int],
                       reloc_target_set: set[int],
                       pc_targets: dict[int, str],
                       string_addrs: set[int],
                       labels: dict[int, str],
                       jump_table_regions: dict[int, JumpTableRegion],
                       jump_table_target_sources: dict[int, tuple[str, ...]],
                       region_map: dict[int, dict[str, TypedMemoryRegion]],
                       lvo_equs: dict[str, dict[int, str]],
                       lvo_substitutions: dict[int, tuple[str, str]],
                       arg_equs: dict[str, int],
                       arg_substitutions: dict[int, tuple[str, str]],
                       app_offsets: dict[int, str],
                       arg_annotations: dict[int, CallArgumentAnnotation],
                       data_access_sizes: dict[int, int],
                       platform: PlatformState,
                       os_kb: OsKb,
                       base_addr: int,
                       code_start: int,
                       relocated_segments: list[RelocatedSegment],
                       reloc_file_offset: int,
                       reloc_base_addr: int,
                       string_ranges: dict[int, int] | None = None,
                       absolute_labels: dict[int, str] | None = None,
                       reserved_absolute_addrs: set[int] | None = None,
                       app_struct_regions: dict[int, TypedMemoryRegion] | None = None,
                       hardware_base_regs: dict[int, dict[str, int]] | None = None,
                       unresolved_indirects: dict[int, IndirectSite] | None = None) -> HunkDisassemblySession:
    return HunkDisassemblySession(
        hunk_index=hunk_index,
        code=code,
        code_size=code_size,
        entities=entities,
        blocks=dict(blocks),
        hint_blocks=dict(hint_blocks),
        code_addrs=code_addrs,
        hint_addrs=hint_addrs,
        reloc_map=reloc_map,
        reloc_target_set=reloc_target_set,
        pc_targets=pc_targets,
        string_addrs=string_addrs,
        labels=labels,
        jump_table_regions=jump_table_regions,
        jump_table_target_sources=jump_table_target_sources,
        region_map=region_map,
        lvo_equs=lvo_equs,
        lvo_substitutions=lvo_substitutions,
        arg_equs=arg_equs,
        arg_substitutions=arg_substitutions,
        app_offsets=app_offsets,
        arg_annotations=arg_annotations,
        data_access_sizes=data_access_sizes,
        platform=platform,
        os_kb=os_kb,
        base_addr=base_addr,
        code_start=code_start,
        relocated_segments=relocated_segments,
        reloc_file_offset=reloc_file_offset,
        reloc_base_addr=reloc_base_addr,
        string_ranges={} if string_ranges is None else string_ranges,
        absolute_labels={} if absolute_labels is None else absolute_labels,
        reserved_absolute_addrs=set() if reserved_absolute_addrs is None else reserved_absolute_addrs,
        app_struct_regions={} if app_struct_regions is None else app_struct_regions,
        hardware_base_regs={} if hardware_base_regs is None else hardware_base_regs,
        unresolved_indirects={} if unresolved_indirects is None else unresolved_indirects,
    )
