"""Build canonical post-analysis disassembly sessions."""

from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from disasm.absolute_resolver import resolve_absolute_labels
from disasm.analysis_layout import (
    resolved_analysis_start_offset,
    resolved_entry_points,
    resolved_raw_analysis_base_addr,
    target_primary_entrypoint_offset,
)
from disasm.analysis_loader import load_hunk_analysis
from disasm.binary_source import BinarySource, HunkFileBinarySource
from disasm.data_access import collect_data_access_sizes
from disasm.decode import DecodedInstructionForEmit
from disasm.discovery import apply_generic_data_label_promotions
from disasm.entities import infer_target_name, load_entities
from disasm.entry_seeds import (
    apply_entry_seed_config,
    build_entry_seed_config,
    scoped_entry_initial_states,
)
from disasm.hardware_symbols import collect_hardware_base_regs
from disasm.hunks import build_hunk_session, build_session_object, prepare_hunk_code
from disasm.metadata import HunkAnalysisLike, build_hunk_metadata
from disasm.phase_timing import PhaseTimer
from disasm.substitutions import build_arg_substitutions, build_lvo_substitutions
from disasm.target_metadata import (
    TargetMetadata,
    load_target_metadata,
    target_structure_spec,
)
from disasm.types import (
    DisasmBlockLike,
    DisassemblySession,
    EntityRecord,
    HunkDisassemblySession,
    JumpTableEntryRef,
    JumpTableRegion,
)
from m68k.analysis import analyze_hunk
from m68k.hunk_parser import Hunk, HunkType, MemType, parse
from m68k.indirect_core import IndirectSiteStatus
from m68k.instruction_primitives import Operand
from m68k.m68k_disasm import DecodedOperandNode
from m68k.m68k_executor import BasicBlock
from m68k.os_calls import (
    analyze_call_setups,
    build_app_slot_symbols,
    build_app_struct_regions,
    propagate_typed_memory_regions,
)

__all__ = [
    "DisassemblySession",
    "EntityRecord",
    "HunkDisassemblySession",
    "build_disassembly_session",
]


def _rebase_local_addr(addr: int, base_addr: int) -> int:
    rebased = addr - base_addr
    assert rebased >= 0
    return rebased


def _maybe_rebase_addr(addr: int, base_addr: int, code_size: int) -> int:
    if base_addr <= addr < base_addr + code_size:
        return _rebase_local_addr(addr, base_addr)
    return addr


def _rebase_block_map(
    blocks: Mapping[int, DisasmBlockLike], base_addr: int, code_size: int
) -> dict[int, BasicBlock]:
    rebased: dict[int, BasicBlock] = {}
    for start, block in blocks.items():
        rebased_start = _rebase_local_addr(start, base_addr)
        rebased[rebased_start] = BasicBlock(
            start=rebased_start,
            end=_rebase_local_addr(block.end, base_addr),
            instructions=[
                replace(
                    instruction,
                    offset=_rebase_local_addr(instruction.offset, base_addr),
                    decoded_operands=(
                        None
                        if instruction.decoded_operands is None
                        else _rebase_decoded_for_emit(instruction.decoded_operands, base_addr, code_size)
                    ),
                    operand_nodes=(
                        None
                        if instruction.operand_nodes is None
                        else tuple(
                            _rebase_decoded_operand_node(node, base_addr, code_size)
                            for node in instruction.operand_nodes
                        )
                    ),
                )
                for instruction in block.instructions
            ],
            successors=[_maybe_rebase_addr(successor, base_addr, code_size) for successor in block.successors],
            predecessors=[_maybe_rebase_addr(predecessor, base_addr, code_size) for predecessor in block.predecessors],
            xrefs=list(block.xrefs),
            is_entry=block.is_entry,
            is_return=block.is_return,
        )
    return rebased


def _rebase_operand_value(
    operand: Operand | None, base_addr: int, code_size: int
) -> Operand | None:
    if operand is None or operand.value is None:
        return operand
    if operand.mode not in ("pcdisp", "pcindex", "absw", "absl"):
        return operand
    return replace(operand, value=_maybe_rebase_addr(operand.value, base_addr, code_size))


def _rebase_decoded_operand_node(
    node: DecodedOperandNode, base_addr: int, code_size: int
) -> DecodedOperandNode:
    target = node.target
    if target is not None:
        target = _maybe_rebase_addr(target, base_addr, code_size)
    value = node.value
    if value is not None and node.kind in ("branch_target", "pc_relative_target", "absolute_target"):
        value = _maybe_rebase_addr(value, base_addr, code_size)
    return replace(node, target=target, value=value)


def _rebase_decoded_for_emit(
    decoded_for_emit: DecodedInstructionForEmit, base_addr: int, code_size: int
) -> DecodedInstructionForEmit:
    decoded = decoded_for_emit.decoded
    return replace(
        decoded_for_emit,
        decoded=replace(
            decoded,
            ea_op=_rebase_operand_value(decoded.ea_op, base_addr, code_size),
            dst_op=_rebase_operand_value(decoded.dst_op, base_addr, code_size),
        ),
    )


def _rebase_jump_table_regions(
    regions: dict[int, JumpTableRegion], base_addr: int, code_size: int
) -> dict[int, JumpTableRegion]:
    rebased: dict[int, JumpTableRegion] = {}
    for table_addr, region in regions.items():
        rebased[_rebase_local_addr(table_addr, base_addr)] = JumpTableRegion(
            pattern=region.pattern,
            table_end=_rebase_local_addr(region.table_end, base_addr),
            entries=tuple(
                JumpTableEntryRef(
                    entry_addr=_rebase_local_addr(entry.entry_addr, base_addr),
                    target=_maybe_rebase_addr(entry.target, base_addr, code_size),
                )
                for entry in region.entries
            ),
            targets=tuple(_maybe_rebase_addr(target, base_addr, code_size) for target in region.targets),
            base_addr=None if region.base_addr is None else _maybe_rebase_addr(region.base_addr, base_addr, code_size),
            base_label=region.base_label,
        )
    return rebased


def _apply_target_structure_annotations(
    *,
    target_metadata: TargetMetadata | None,
    labels: dict[int, str],
    string_addrs: set[int],
    data_access_sizes: dict[int, int],
    code_size: int,
    apply_structure: bool,
) -> int:
    if not apply_structure:
        return 0
    structure = target_structure_spec(target_metadata)
    if structure is None:
        return 0
    for region in structure.regions:
        if region.start < 0 or region.end > code_size or region.start > region.end:
            raise ValueError(
                f"Structured region {region.start:#x}..{region.end:#x} lies outside code size {code_size:#x}"
            )
        for field in region.fields:
            if not (region.start <= field.offset <= code_size):
                raise ValueError(
                    f"Structured field {field.label} at 0x{field.offset:X} lies outside code size 0x{code_size:X}"
                )
            labels[field.offset] = field.label
            if field.is_string:
                string_addrs.add(field.offset)
            if field.size is not None:
                data_access_sizes.setdefault(field.offset, field.size)
    for entrypoint in structure.entrypoints:
        if not (0 <= entrypoint.offset <= code_size):
            raise ValueError(
                f"Structured entrypoint 0x{entrypoint.offset:X} lies outside code size 0x{code_size:X}"
            )
        labels[entrypoint.offset] = entrypoint.label
    primary_entrypoint = target_primary_entrypoint_offset(target_metadata)
    return 0 if primary_entrypoint is None else primary_entrypoint


def _filter_pre_entry_blocks(
    blocks: Mapping[int, BasicBlock],
    entry_point: int | None,
) -> dict[int, BasicBlock]:
    if entry_point is None or entry_point <= 0:
        return dict(blocks)
    keep = {
        addr
        for addr, block in blocks.items()
        if block.end > entry_point
    }
    filtered: dict[int, BasicBlock] = {}
    for _addr, block in blocks.items():
        if block.end <= entry_point:
            continue
        kept_instructions = [inst for inst in block.instructions if inst.offset >= entry_point]
        if not kept_instructions:
            continue
        new_start = entry_point if block.start < entry_point else block.start
        filtered[new_start] = replace(
            block,
            start=new_start,
            instructions=kept_instructions,
            is_entry=(block.is_entry or new_start == entry_point),
            successors=[succ for succ in block.successors if succ in keep],
            predecessors=[pred for pred in block.predecessors if pred in keep and pred >= entry_point],
            xrefs=[xref for xref in block.xrefs if xref.src >= entry_point and xref.dst >= entry_point],
        )
    return filtered

def build_disassembly_session(binary_source: str | BinarySource, entities_path: str,
                              output_path: str | None = None,
                              base_addr: int = 0, code_start: int = 0,
                              profile_stages: bool = False,
                              phase_timer: PhaseTimer | None = None) -> DisassemblySession:
    source = (
        HunkFileBinarySource(
            kind="hunk_file",
            path=Path(binary_source),
            display_path=str(binary_source),
            analysis_cache_path=Path(binary_source).with_suffix(".analysis"),
        )
        if isinstance(binary_source, str)
        else binary_source
    )
    entities: list[EntityRecord] = load_entities(entities_path)
    target_dir = Path(entities_path).parent if Path(entities_path).parent.exists() else None
    target_name = infer_target_name(target_dir, entities_path)
    target_metadata = None if target_dir is None else load_target_metadata(target_dir)
    if source.kind == "raw_binary" and target_metadata is None:
        raise ValueError(f"Missing target_metadata.json for raw binary target: {target_dir}")
    if source.parent_disk_id is not None and target_metadata is None:
        raise ValueError(f"Missing target_metadata.json for internal target: {target_dir}")
    hunk_sessions: list[HunkDisassemblySession] = []

    if source.kind == "raw_binary":
        source_bytes = source.read_bytes()
        raw_hunk = Hunk(
            index=0,
            hunk_type=int(HunkType.HUNK_CODE),
            mem_type=int(MemType.ANY),
            alloc_size=len(source_bytes),
            data=source_bytes,
        )
        return _build_code_session(
            source=source,
            entities=entities,
            target_name=target_name,
            target_metadata=target_metadata,
            entities_path=entities_path,
            output_path=output_path,
            hunk=raw_hunk,
            hf_hunks=[raw_hunk],
            base_addr=resolved_raw_analysis_base_addr(source, target_metadata),
            code_start=resolved_analysis_start_offset(source, target_metadata),
            entry_points=resolved_entry_points(source, target_metadata, ()),
            profile_stages=profile_stages,
            phase_timer=phase_timer,
        )

    hf = parse(source.read_bytes())
    custom_entry_points = resolved_entry_points(source, target_metadata, ())
    first_code_hunk_seen = False

    for hunk in hf.hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            continue
        hunk_sessions.append(_build_hunk_session_data(
            source=source,
            entities=entities,
            hunk=hunk,
            hf_hunks=hf.hunks,
            base_addr=base_addr,
            code_start=code_start,
            entry_points=(custom_entry_points if not first_code_hunk_seen else ()),
            target_metadata=target_metadata,
            apply_target_structure=not first_code_hunk_seen,
            phase_timer=phase_timer,
        ))
        first_code_hunk_seen = True

    return build_session_object(
        target_name=target_name,
        binary_path=Path(source.display_path),
        analysis_cache_path=source.analysis_cache_path,
        entities_path=Path(entities_path),
        output_path=Path(output_path) if output_path else None,
        entities=entities,
        hunk_sessions=hunk_sessions,
        target_metadata=target_metadata,
        source_kind=source.kind,
        raw_address_model=(None if source.kind != "raw_binary" else source.address_model),
        profile_stages=profile_stages,
    )


def _build_code_session(
    *,
    source: BinarySource,
    entities: list[EntityRecord],
    target_name: str | None,
    target_metadata: TargetMetadata | None,
    entities_path: str,
    output_path: str | None,
    hunk: Hunk,
    hf_hunks: list[Hunk],
    base_addr: int,
    code_start: int,
    entry_points: tuple[int, ...],
    profile_stages: bool,
    phase_timer: PhaseTimer | None,
) -> DisassemblySession:
    hunk_session = _build_hunk_session_data(
        source=source,
        entities=entities,
        hunk=hunk,
        hf_hunks=hf_hunks,
        base_addr=base_addr,
        code_start=code_start,
        entry_points=entry_points,
        target_metadata=target_metadata,
        apply_target_structure=True,
        phase_timer=phase_timer,
    )
    return build_session_object(
        target_name=target_name,
        binary_path=Path(source.display_path),
        analysis_cache_path=source.analysis_cache_path,
        entities_path=Path(entities_path),
        output_path=Path(output_path) if output_path else None,
        entities=entities,
        hunk_sessions=[hunk_session],
        target_metadata=target_metadata,
        source_kind=source.kind,
        raw_address_model=(None if source.kind != "raw_binary" else source.address_model),
        profile_stages=profile_stages,
    )


def _build_hunk_session_data(
    *,
    source: BinarySource,
    entities: list[EntityRecord],
    hunk: Hunk,
    hf_hunks: list[Hunk],
    base_addr: int,
    code_start: int,
    entry_points: tuple[int, ...],
    target_metadata: TargetMetadata | None,
    apply_target_structure: bool,
    phase_timer: PhaseTimer | None,
) -> HunkDisassemblySession:
    seed_config = build_entry_seed_config(target_metadata)
    entry_initial_states = scoped_entry_initial_states(seed_config, entry_points)
    code = hunk.data
    code_size = len(code)
    hunk_entities = [e for e in entities if e.get("hunk") == hunk.index]
    hunk_entities.sort(key=lambda e: int(e["addr"], 16))

    with phase_timer.phase("session.load_analysis") if phase_timer is not None else nullcontext():
        if source.kind == "raw_binary":
            ha = analyze_hunk(
                code,
                [],
                hunk.index,
                base_addr=base_addr,
                code_start=code_start,
                entry_points=entry_points,
                initial_state=seed_config.initial_state,
                entry_initial_states=entry_initial_states,
                phase_timer=phase_timer,
            )
        else:
            ha = load_hunk_analysis(
                analysis_cache_path=source.analysis_cache_path,
                code=code,
                relocs=hunk.relocs,
                hunk_index=hunk.index,
                base_addr=base_addr,
                code_start=code_start,
                entry_points=entry_points,
                seed_key=seed_config.seed_key,
                initial_state=seed_config.initial_state,
                entry_initial_states=entry_initial_states,
            )
    entry_point = entry_points[0] if entry_points else None
    blocks = _filter_pre_entry_blocks(ha.blocks, entry_point)
    hint_blocks: Mapping[int, DisasmBlockLike] = _filter_pre_entry_blocks(ha.hint_blocks, entry_point)
    lib_calls = [call for call in ha.lib_calls if entry_point is None or call.addr >= entry_point]
    os_kb = ha.os_kb
    assert os_kb is not None, f"Analysis for hunk {hunk.index} did not provide an OS KB"
    platform = ha.platform
    apply_entry_seed_config(platform, seed_config)
    exit_states = {
        addr: state
        for addr, state in ha.exit_states.items()
        if entry_point is None or addr >= entry_point
    }
    relocated_segments = ha.relocated_segments
    code, code_size, relocated_segments, reloc_file_offset, reloc_base_addr = (
        prepare_hunk_code(code, relocated_segments)
    )
    with phase_timer.phase("session.metadata") if phase_timer is not None else nullcontext():
        absolute_resolution = resolve_absolute_labels(platform=platform)
        call_setup_analysis = analyze_call_setups(
            blocks=blocks,
            lib_calls=lib_calls,
            os_kb=os_kb,
            code=code,
            platform=platform,
        )
        metadata = build_hunk_metadata(
            code=code,
            code_size=code_size,
            hunk_index=hunk.index,
            hunk_entities=hunk_entities,
            ha=cast(
                HunkAnalysisLike,
                SimpleNamespace(
                    blocks=blocks,
                    hint_blocks=hint_blocks,
                    jump_tables=ha.jump_tables,
                    call_targets={
                        addr for addr in ha.call_targets
                        if entry_point is None or addr >= entry_point
                    },
                    branch_targets={
                        addr for addr in ha.branch_targets
                        if entry_point is None or addr >= entry_point
                    },
                ),
            ),
            hf_hunks=hf_hunks,
            segment_start=base_addr,
            typed_string_ranges=call_setup_analysis.string_ranges,
            reserved_absolute_addrs=absolute_resolution.reserved_absolute_addrs,
            absolute_labels=absolute_resolution.absolute_labels,
        )
        region_map = propagate_typed_memory_regions(blocks, lib_calls, code, os_kb, platform)
        app_struct_regions = build_app_struct_regions(blocks, lib_calls, os_kb, platform)
        hardware_base_regs = collect_hardware_base_regs(blocks, code, platform)
    with phase_timer.phase("session.substitutions") if phase_timer is not None else nullcontext():
        lvo_equs, lvo_substitutions = build_lvo_substitutions(
            blocks=blocks,
            lib_calls=lib_calls,
            hunk_entities=hunk_entities,
        )
        arg_equs, arg_substitutions = build_arg_substitutions(
            blocks=blocks,
            lib_calls=lib_calls,
            hunk_entities=hunk_entities,
            os_kb=os_kb,
        )
        app_offsets = build_app_slot_symbols(
            blocks=blocks,
            lib_calls=lib_calls,
            code=code,
            os_kb=os_kb,
            platform=platform,
        )
    labels = metadata.labels
    apply_generic_data_label_promotions(
        labels,
        metadata.pc_targets,
        metadata.generic_data_label_addrs,
        call_setup_analysis.segment_data_symbols,
    )
    for addr, symbol in call_setup_analysis.segment_code_symbols.items():
        labels[addr] = symbol
    data_access_sizes = collect_data_access_sizes(blocks, exit_states)
    unresolved_indirects = {
        site.addr: site
        for site in ha.indirect_sites
        if site.status == IndirectSiteStatus.UNRESOLVED
        and (entry_point is None or site.addr >= entry_point)
    }
    hint_blocks = metadata.hint_blocks
    if source.kind == "raw_binary" and source.address_model == "runtime_absolute":
        blocks = _rebase_block_map(blocks, base_addr, code_size)
        hint_blocks = _rebase_block_map(metadata.hint_blocks, base_addr, code_size)
        region_map = {
            _rebase_local_addr(addr, base_addr): regions
            for addr, regions in region_map.items()
        }
        app_struct_regions = {
            _rebase_local_addr(addr, base_addr): region
            for addr, region in app_struct_regions.items()
        }
        hardware_base_regs = {
            _rebase_local_addr(addr, base_addr): regs
            for addr, regs in hardware_base_regs.items()
        }
        lvo_substitutions = {
            _rebase_local_addr(addr, base_addr): value
            for addr, value in lvo_substitutions.items()
        }
        arg_substitutions = {
            _rebase_local_addr(addr, base_addr): value
            for addr, value in arg_substitutions.items()
        }
        arg_annotations = {
            _rebase_local_addr(addr, base_addr): value
            for addr, value in call_setup_analysis.arg_annotations.items()
        }
        data_access_sizes = {
            _rebase_local_addr(addr, base_addr): size
            for addr, size in data_access_sizes.items()
        }
        unresolved_indirects = {
            _rebase_local_addr(addr, base_addr): site
            for addr, site in unresolved_indirects.items()
        }
        labels = {
            _maybe_rebase_addr(addr, base_addr, code_size): label
            for addr, label in labels.items()
        }
        metadata = replace(
            metadata,
            code_addrs={_rebase_local_addr(addr, base_addr) for addr in metadata.code_addrs},
            hint_addrs={_rebase_local_addr(addr, base_addr) for addr in metadata.hint_addrs},
            hint_blocks=hint_blocks,
            pc_targets={
                _maybe_rebase_addr(addr, base_addr, code_size): label
                for addr, label in metadata.pc_targets.items()
            },
            string_addrs={_rebase_local_addr(addr, base_addr) for addr in metadata.string_addrs},
            generic_data_label_addrs={
                _maybe_rebase_addr(addr, base_addr, code_size) for addr in metadata.generic_data_label_addrs
            },
            jump_table_regions=_rebase_jump_table_regions(metadata.jump_table_regions, base_addr, code_size),
            jump_table_target_sources={
                _maybe_rebase_addr(addr, base_addr, code_size): sources
                for addr, sources in metadata.jump_table_target_sources.items()
            },
            labels=labels,
            string_ranges={
                _rebase_local_addr(start, base_addr): _rebase_local_addr(end, base_addr)
                for start, end in metadata.string_ranges.items()
            },
        )
    else:
        hint_blocks = metadata.hint_blocks
        arg_annotations = call_setup_analysis.arg_annotations
    structured_code_start = target_primary_entrypoint_offset(target_metadata)
    if structured_code_start is not None:
        code_start = structured_code_start
    _apply_target_structure_annotations(
        target_metadata=target_metadata,
        labels=labels,
        string_addrs=metadata.string_addrs,
        data_access_sizes=data_access_sizes,
        code_size=code_size,
        apply_structure=apply_target_structure,
    )
    with phase_timer.phase("session.build") if phase_timer is not None else nullcontext():
        return build_hunk_session(
            hunk_index=hunk.index,
            code=code,
            code_size=code_size,
            entities=hunk_entities,
            blocks=blocks,
            hint_blocks=hint_blocks,
            code_addrs=metadata.code_addrs,
            hint_addrs=metadata.hint_addrs,
            reloc_map=metadata.reloc_map,
            reloc_target_set=metadata.reloc_target_set,
            reserved_absolute_addrs=metadata.reserved_absolute_addrs,
            pc_targets=metadata.pc_targets,
            string_addrs=metadata.string_addrs,
            string_ranges=metadata.string_ranges,
            labels=labels,
            absolute_labels=metadata.absolute_labels,
            jump_table_regions=metadata.jump_table_regions,
            jump_table_target_sources=metadata.jump_table_target_sources,
            lib_calls=lib_calls,
            region_map=region_map,
            app_struct_regions=app_struct_regions,
            hardware_base_regs=hardware_base_regs,
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
            unresolved_indirects=unresolved_indirects,
        )




