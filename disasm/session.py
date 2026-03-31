"""Build canonical post-analysis disassembly sessions."""

from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from disasm.absolute_resolver import resolve_absolute_labels
from disasm.analysis_layout import (
    resolved_analysis_start_offset,
    resolved_entry_points,
    resolved_raw_analysis_base_addr,
    target_primary_entrypoint_offset,
    target_seeded_entrypoint_offsets,
)
from disasm.analysis_loader import load_hunk_analysis
from disasm.binary_source import BinarySource, HunkFileBinarySource
from disasm.data_access import collect_data_access_sizes
from disasm.decode import DecodedInstructionForEmit
from disasm.discovery import (
    apply_generic_data_label_promotions,
    apply_generic_data_size_promotions,
    discover_pc_relative_targets,
)
from disasm.entities import infer_target_name, load_entities
from disasm.entry_seeds import (
    apply_entry_seed_config,
    build_entry_seed_config,
    scoped_entry_initial_states,
)
from disasm.hardware_symbols import collect_hardware_base_regs
from disasm.metadata import HunkAnalysisLike, build_hunk_metadata
from disasm.phase_timing import PhaseTimer
from disasm.substitutions import build_arg_substitutions, build_lvo_substitutions
from disasm.target_metadata import (
    ExecutionViewMetadata,
    StructuredRegionSpec,
    TargetMetadata,
    load_required_target_metadata,
    target_structure_spec,
)
from disasm.typed_data_streams import decode_stream_by_name
from disasm.types import (
    DisasmBlockLike,
    DisassemblySession,
    EntityRecord,
    HunkDisassemblySession,
    JumpTableEntryRef,
    JumpTableRegion,
    TypedDataFieldInfo,
)
from m68k.analysis import (
    HunkAnalysis,
    RelocatedSegment,
    analyze_hunk,
    detect_relocated_segments,
    resolve_reloc_target,
)
from m68k.hunk_parser import Hunk, HunkType, MemType, parse
from m68k.indirect_core import IndirectSiteStatus
from m68k.instruction_decode import decode_inst_operands
from m68k.instruction_kb import instruction_kb
from m68k.instruction_primitives import Operand
from m68k.jump_tables import JumpTableEntry
from m68k.m68k_disasm import DecodedOperandNode, Instruction, disassemble
from m68k.m68k_executor import BasicBlock, XRef
from m68k.memory_provenance import MemoryRegionDerivationKind, provenance_named_base
from m68k.os_calls import (
    LibraryCall,
    OsKb,
    PlatformState,
    TypedMemoryRegion,
    analyze_call_setups,
    build_app_slot_symbols,
    build_app_struct_regions,
    build_target_local_os_kb,
    get_platform_config,
    infer_named_base_extension_structs,
    propagate_typed_memory_regions,
    refine_library_calls,
)
from m68k.os_structs import resolve_struct_field
from m68k_kb import runtime_hunk, runtime_m68k_analysis, runtime_os

_FLOW_BRANCH = runtime_m68k_analysis.FlowType.BRANCH
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
_OPERAND_SIZE_BYTES = {"b": 1, "w": 2, "l": 4}

__all__ = [
    "DisassemblySession",
    "EntityRecord",
    "HunkDisassemblySession",
    "build_disassembly_session",
]

def _execution_views_for_session(
    *,
    code: bytes,
    blocks: Mapping[int, DisasmBlockLike],
    target_metadata: TargetMetadata | None,
    relocated_segments: list[RelocatedSegment],
    physical_stored_size: int,
) -> tuple[ExecutionViewMetadata, ...]:
    views: list[ExecutionViewMetadata] = []
    seen: set[tuple[int, int, int]] = set()

    def add_view(view: ExecutionViewMetadata) -> None:
        key = (view.source_start, view.source_end, view.base_addr)
        if key in seen:
            return
        seen.add(key)
        views.append(view)

    for index, seg in enumerate(relocated_segments):
        if seg.file_offset >= physical_stored_size:
            continue
        add_view(
            ExecutionViewMetadata(
                source_start=seg.file_offset,
                source_end=physical_stored_size,
                base_addr=seg.base_addr,
                name=f"relocated_code_{index + 1}",
                seed_origin="autodoc",
                review_status="seeded",
                citation="container:relocated_segment",
                comment=f"Relocated code executes from ${seg.base_addr:08X}",
            )
        )
    physical_code = code[:physical_stored_size]
    for index, seg in enumerate(detect_relocated_segments(physical_code)):
        if seg.file_offset >= physical_stored_size:
            continue
        add_view(
            ExecutionViewMetadata(
                source_start=seg.file_offset,
                source_end=physical_stored_size,
                base_addr=seg.base_addr,
                name=f"detected_relocated_code_{index + 1}",
                seed_origin="autodoc",
                review_status="seeded",
                citation="analysis:relocated_segment",
                comment=f"Relocated code executes from ${seg.base_addr:08X}",
            )
        )
    for index, view in enumerate(
        _trap_bootstrap_execution_views(
            code=physical_code,
            blocks=blocks,
            physical_stored_size=physical_stored_size,
        ),
        start=1,
    ):
        add_view(
            replace(
                view,
                name=f"trap_bootstrap_{index}" if not view.name else view.name,
            )
        )
    if target_metadata is None:
        target_views: tuple[ExecutionViewMetadata, ...] = ()
    else:
        target_views = target_metadata.execution_views
        for view in target_views:
            add_view(view)

    queue = list(views)
    while queue:
        parent = queue.pop(0)
        if parent.source_end > len(code):
            continue
        nested_code = code[parent.source_start:parent.source_end]
        for segment in detect_relocated_segments(nested_code):
            nested_view = ExecutionViewMetadata(
                source_start=parent.source_start + segment.file_offset,
                source_end=parent.source_end,
                base_addr=segment.base_addr,
                name=f"{parent.name}_nested_{len(views) + 1}",
                seed_origin="autodoc",
                review_status="seeded",
                citation=f"{parent.citation}:nested",
                comment=f"Embedded relocated code executes from ${segment.base_addr:08X}",
            )
            key = (nested_view.source_start, nested_view.source_end, nested_view.base_addr)
            if key not in seen:
                add_view(nested_view)
                queue.append(nested_view)
    return tuple(views)


def _copy_loop_info(inst: Instruction) -> tuple[int, int, int] | None:
    mnemonic = instruction_kb(inst)
    if runtime_m68k_analysis.OPERATION_TYPES.get(mnemonic) != runtime_m68k_analysis.OperationType.MOVE:
        return None
    decoded = decode_inst_operands(inst, mnemonic)
    src = decoded.ea_op
    dst = decoded.dst_op
    if src is None or dst is None or src.mode != "postinc" or dst.mode != "postinc":
        return None
    if src.reg is None or dst.reg is None or inst.operand_size not in _OPERAND_SIZE_BYTES:
        return None
    return src.reg, dst.reg, _OPERAND_SIZE_BYTES[inst.operand_size]


def _trap_number(inst: Instruction) -> int | None:
    if instruction_kb(inst) != "TRAP" or len(inst.raw) < 2:
        return None
    return int.from_bytes(inst.raw[:2], "big") & 0xF


def _immediate_to_absolute_write(inst: Instruction) -> tuple[int, int] | None:
    mnemonic = instruction_kb(inst)
    if mnemonic not in {"MOVE", "MOVEA"}:
        return None
    decoded = decode_inst_operands(inst, mnemonic)
    source = decoded.ea_op
    dest = decoded.dst_op
    if source is None or dest is None or source.mode != "imm":
        return None
    if dest.mode not in {"absw", "absl"} or source.value is None or dest.value is None:
        return None
    return int(source.value), int(dest.value & 0xFFFF if dest.mode == "absw" else dest.value)


def _simple_register_value_before(
    *,
    blocks: Mapping[int, DisasmBlockLike],
    before_addr: int,
    register_kind: str,
    register_num: int,
) -> int | None:
    for block_addr in sorted((addr for addr in blocks if addr < before_addr), reverse=True):
        block = blocks[block_addr]
        for inst in reversed(block.instructions):
            mnemonic = instruction_kb(inst)
            decoded = decode_inst_operands(inst, mnemonic)
            if register_kind == "an":
                opcode = int.from_bytes(inst.raw[:2], "big") if len(inst.raw) >= 2 else 0
                if mnemonic == "LEA" and ((opcode >> 9) & 0x7) == register_num:
                    source = decoded.ea_op
                    if source is not None and source.value is not None:
                        return int(source.value)
                dst = decoded.dst_op
                if mnemonic == "MOVEA" and dst is not None and dst.mode == "an" and dst.reg == register_num:
                    source = decoded.ea_op
                    if source is not None and source.mode == "imm" and source.value is not None:
                        return int(source.value)
            elif register_kind == "dn":
                dst = decoded.dst_op
                if dst is not None and dst.mode in {"dn", "dreg"} and dst.reg == register_num:
                    source = decoded.ea_op
                    if source is not None and source.mode == "imm" and source.value is not None:
                        return int(source.value)
                if mnemonic == "MOVEQ" and inst.raw:
                    opcode = int.from_bytes(inst.raw[:2], "big")
                    if ((opcode >> 9) & 0x7) == register_num:
                        immediate = opcode & 0xFF
                        if immediate & 0x80:
                            immediate -= 0x100
                        return immediate
    return None


def _trap_bootstrap_execution_views(
    *,
    code: bytes,
    blocks: Mapping[int, DisasmBlockLike],
    physical_stored_size: int,
) -> tuple[ExecutionViewMetadata, ...]:
    views: list[ExecutionViewMetadata] = []
    for trap_addr in sorted(blocks):
        block = blocks[trap_addr]
        vector_target: int | None = None
        trap_number: int | None = None
        for inst in block.instructions:
            maybe_trap = _trap_number(inst)
            if maybe_trap is not None:
                trap_number = maybe_trap
                break
        if trap_number is None:
            continue
        vector_slot = 0x80 + (trap_number * 4)
        for inst in block.instructions:
            write = _immediate_to_absolute_write(inst)
            if write is None:
                continue
            immediate, absolute_dest = write
            if absolute_dest == vector_slot:
                vector_target = immediate
        if vector_target is None:
            continue
        for copy_addr in sorted(blocks):
            if copy_addr >= trap_addr:
                break
            copy_block = blocks[copy_addr]
            loop_info = None
            for inst in copy_block.instructions:
                loop_info = _copy_loop_info(inst)
                if loop_info is not None:
                    break
            if loop_info is None:
                continue
            src_reg, dst_reg, unit_size = loop_info
            source_start = _simple_register_value_before(
                blocks=blocks,
                before_addr=copy_addr,
                register_kind="an",
                register_num=src_reg,
            )
            dest_start = _simple_register_value_before(
                blocks=blocks,
                before_addr=copy_addr,
                register_kind="an",
                register_num=dst_reg,
            )
            count = _simple_register_value_before(
                blocks=blocks,
                before_addr=copy_addr,
                register_kind="dn",
                register_num=0,
            )
            if (
                source_start is None
                or dest_start is None
                or count is None
                or dest_start != vector_target
                or not (0 <= source_start < physical_stored_size)
            ):
                continue
            copy_size = (count + 1) * unit_size
            source_end = min(physical_stored_size, source_start + copy_size)
            if source_end <= source_start:
                continue
            views.append(
                ExecutionViewMetadata(
                    source_start=source_start,
                    source_end=source_end,
                    base_addr=vector_target,
                    name=f"trap_{trap_number}_stub",
                    seed_origin="autodoc",
                    review_status="seeded",
                    citation="analysis:trap_bootstrap",
                    comment=f"Copied trap {trap_number} stub executes from ${vector_target:08X}",
                )
            )
            break
    return tuple(views)


def _maybe_rebase_substitution_map(
    substitutions: dict[int, tuple[str, str]],
    *,
    instruction_addrs: set[int],
    base_addr: int,
    code_size: int,
) -> dict[int, tuple[str, str]]:
    if not substitutions or base_addr <= 0:
        return substitutions
    if all(addr in instruction_addrs for addr in substitutions):
        return substitutions
    rebased: dict[int, tuple[str, str]] = {}
    for addr, value in substitutions.items():
        if base_addr <= addr < base_addr + code_size:
            rebased[_rebase_local_addr(addr, base_addr)] = value
        else:
            rebased[addr] = value
    if all(addr in instruction_addrs for addr in rebased):
        return rebased
    return substitutions


def _rebase_local_addr(addr: int, base_addr: int) -> int:
    rebased = addr - base_addr
    assert rebased >= 0
    return rebased


def _maybe_rebase_addr(addr: int, base_addr: int, code_size: int) -> int:
    if base_addr <= addr < base_addr + code_size:
        return _rebase_local_addr(addr, base_addr)
    return addr


def _source_addr_for_runtime(
    addr: int,
    *,
    file_offset: int,
    base_addr: int,
    physical_size: int,
) -> int:
    payload_size = physical_size - file_offset
    if base_addr <= addr < base_addr + payload_size:
        return file_offset + (addr - base_addr)
    return addr


def _remap_operand_value_to_source(
    operand: Operand | None,
    *,
    file_offset: int,
    base_addr: int,
    physical_size: int,
) -> Operand | None:
    if operand is None or operand.value is None:
        return operand
    if operand.mode not in ("pcdisp", "pcindex", "absw", "absl"):
        return operand
    return replace(
        operand,
        value=_source_addr_for_runtime(
            operand.value,
            file_offset=file_offset,
            base_addr=base_addr,
            physical_size=physical_size,
        ),
    )


def _remap_decoded_operand_node_to_source(
    node: DecodedOperandNode,
    *,
    file_offset: int,
    base_addr: int,
    physical_size: int,
) -> DecodedOperandNode:
    target = node.target
    if target is not None and node.kind in (
        "branch_target",
        "pc_relative_target",
        "pc_relative_indexed",
        "absolute_target",
    ):
        target = _source_addr_for_runtime(
            target,
            file_offset=file_offset,
            base_addr=base_addr,
            physical_size=physical_size,
        )
    value = node.value
    if value is not None and node.kind in (
        "branch_target",
        "pc_relative_target",
        "pc_relative_indexed",
        "absolute_target",
    ):
        value = _source_addr_for_runtime(
            value,
            file_offset=file_offset,
            base_addr=base_addr,
            physical_size=physical_size,
        )
    return replace(node, target=target, value=value)


def _remap_decoded_for_emit_to_source(
    decoded_for_emit: DecodedInstructionForEmit,
    *,
    file_offset: int,
    base_addr: int,
    physical_size: int,
) -> DecodedInstructionForEmit:
    decoded = decoded_for_emit.decoded
    return replace(
        decoded_for_emit,
        decoded=replace(
            decoded,
            ea_op=_remap_operand_value_to_source(
                decoded.ea_op,
                file_offset=file_offset,
                base_addr=base_addr,
                physical_size=physical_size,
            ),
            dst_op=_remap_operand_value_to_source(
                decoded.dst_op,
                file_offset=file_offset,
                base_addr=base_addr,
                physical_size=physical_size,
            ),
        ),
    )


def _decoded_for_emit_from_instruction(instruction: Instruction) -> DecodedInstructionForEmit:
    if instruction.kb_mnemonic is None:
        raise ValueError(f"Instruction at ${instruction.offset:06X} is missing kb_mnemonic")
    if instruction.operand_size is None:
        raise ValueError(f"Instruction at ${instruction.offset:06X} is missing operand_size")
    return DecodedInstructionForEmit(
        mnemonic=instruction_kb(instruction),
        size=instruction.operand_size,
        decoded=decode_inst_operands(instruction, instruction_kb(instruction)),
    )


def _remap_analysis_to_source(
    ha: HunkAnalysis,
    *,
    physical_size: int,
) -> HunkAnalysis:
    if not ha.relocated_segments:
        return ha
    seg = ha.relocated_segments[0]
    file_offset = seg.file_offset
    base_addr = seg.base_addr

    def map_addr(addr: int) -> int:
        return _source_addr_for_runtime(
            addr,
            file_offset=file_offset,
            base_addr=base_addr,
            physical_size=physical_size,
        )

    def map_block(block: DisasmBlockLike) -> BasicBlock:
        return BasicBlock(
            start=map_addr(block.start),
            end=map_addr(block.end),
            instructions=[
                replace(
                    instruction,
                    offset=map_addr(instruction.offset),
                    decoded_operands=_remap_decoded_for_emit_to_source(
                        (
                            instruction.decoded_operands
                            if instruction.decoded_operands is not None
                            else _decoded_for_emit_from_instruction(instruction)
                        ),
                        file_offset=file_offset,
                        base_addr=base_addr,
                        physical_size=physical_size,
                    ),
                    operand_nodes=(
                        None
                        if instruction.operand_nodes is None
                        else tuple(
                            _remap_decoded_operand_node_to_source(
                                node,
                                file_offset=file_offset,
                                base_addr=base_addr,
                                physical_size=physical_size,
                            )
                            for node in instruction.operand_nodes
                        )
                    ),
                )
                for instruction in block.instructions
            ],
            successors=[map_addr(successor) for successor in block.successors],
            predecessors=[map_addr(predecessor) for predecessor in block.predecessors],
            xrefs=[
                XRef(src=map_addr(xref.src), dst=map_addr(xref.dst), type=xref.type, conditional=xref.conditional)
                for xref in block.xrefs
            ],
            is_entry=block.is_entry,
            is_return=block.is_return,
        )

    mapped_blocks = {map_addr(start): map_block(block) for start, block in ha.blocks.items()}
    mapped_hints = {map_addr(start): map_block(block) for start, block in ha.hint_blocks.items()}
    mapped_jump_tables = [
        replace(
            table,
            addr=map_addr(table.addr),
            targets=tuple(map_addr(target) for target in table.targets),
            dispatch_sites=tuple(map_addr(site) for site in table.dispatch_sites),
            dispatch_block=map_addr(table.dispatch_block),
            table_end=map_addr(table.table_end),
            base_addr=None if table.base_addr is None else map_addr(table.base_addr),
            entries=tuple(
                JumpTableEntry(offset_addr=map_addr(entry.offset_addr), target=map_addr(entry.target))
                for entry in table.entries
            ),
        )
        for table in ha.jump_tables
    ]
    mapped_lib_calls = [
        replace(
            call,
            addr=map_addr(call.addr),
            block=map_addr(call.block),
            owner_sub=(call.owner_sub if call.owner_sub < 0 else map_addr(call.owner_sub)),
        )
        for call in ha.lib_calls
    ]
    return replace(
        ha,
        blocks=mapped_blocks,
        hint_blocks=mapped_hints,
        jump_tables=mapped_jump_tables,
        call_targets={map_addr(addr) for addr in ha.call_targets},
        branch_targets={map_addr(addr) for addr in ha.branch_targets},
        lib_calls=mapped_lib_calls,
        exit_states={map_addr(addr): state for addr, state in ha.exit_states.items()},
        xrefs=[XRef(src=map_addr(xref.src), dst=map_addr(xref.dst), type=xref.type, conditional=xref.conditional) for xref in ha.xrefs],
    )


def _remap_data_access_sizes_to_source(
    data_access_sizes: Mapping[int, int],
    *,
    file_offset: int,
    base_addr: int,
    physical_size: int,
) -> dict[int, int]:
    remapped: dict[int, int] = {}
    for addr, size in data_access_sizes.items():
        mapped = _source_addr_for_runtime(
            addr,
            file_offset=file_offset,
            base_addr=base_addr,
            physical_size=physical_size,
        )
        current = remapped.get(mapped)
        if current is None or size > current:
            remapped[mapped] = size
    return remapped


def _with_refined_named_base_structs(
    region: TypedMemoryRegion,
    os_kb: OsKb,
) -> TypedMemoryRegion:
    derivation = region.provenance.derivation
    if derivation is None or derivation.kind is not MemoryRegionDerivationKind.NAMED_BASE:
        return region
    named_base = derivation.named_base
    if named_base is None:
        return region
    struct_name = os_kb.META.named_base_structs.get(named_base)
    if struct_name is None or struct_name == region.struct:
        return region
    struct_def = os_kb.STRUCTS.get(struct_name)
    if struct_def is None:
        return region
    return TypedMemoryRegion(
        struct=struct_name,
        size=struct_def.size,
        provenance=region.provenance,
        struct_offset=region.struct_offset,
        context_name=region.context_name,
    )


def _apply_named_base_struct_overrides(platform: PlatformState, os_kb: OsKb) -> None:
    if platform.initial_register_regions:
        platform.initial_register_regions = {
            reg: _with_refined_named_base_structs(region, os_kb)
            for reg, region in platform.initial_register_regions.items()
        }
    if platform.entry_register_regions:
        platform.entry_register_regions = {
            entry: {
                reg: _with_refined_named_base_structs(region, os_kb)
                for reg, region in regions.items()
            }
            for entry, regions in platform.entry_register_regions.items()
        }


def _session_os_kb_score(os_kb: OsKb) -> tuple[int, int]:
    return (len(os_kb.STRUCTS), len(os_kb.META.named_base_structs))


def _normalize_session_os_kb(hunk_sessions: list[HunkDisassemblySession]) -> None:
    if not hunk_sessions:
        return
    session_os_kb = max(
        (hunk_session.os_kb for hunk_session in hunk_sessions),
        key=_session_os_kb_score,
    )
    session_structs = session_os_kb.STRUCTS
    session_named_bases = session_os_kb.META.named_base_structs
    for hunk_session in hunk_sessions:
        assert set(hunk_session.os_kb.STRUCTS).issubset(session_structs), (
            f"hunk {hunk_session.hunk_index} has non-session structs"
        )
        for named_base, struct_name in hunk_session.os_kb.META.named_base_structs.items():
            assert session_named_bases.get(named_base) == struct_name, (
                f"hunk {hunk_session.hunk_index} named-base mismatch for {named_base}"
            )
        if hunk_session.os_kb is session_os_kb:
            continue
        hunk_session.os_kb = session_os_kb
        _apply_named_base_struct_overrides(hunk_session.platform, session_os_kb)


def _cross_hunk_control_entrypoints(hunks: list[Hunk]) -> dict[int, tuple[int, ...]]:
    targets_by_hunk: dict[int, set[int]] = {}
    for hunk in hunks:
        if hunk.hunk_type != HunkType.HUNK_CODE:
            continue
        for reloc in hunk.relocs:
            target_hunk = reloc.target_hunk
            if target_hunk == hunk.index:
                continue
            reloc_name = HunkType(reloc.reloc_type).name
            reloc_info = runtime_hunk.RELOCATION_SEMANTICS.get(reloc_name)
            if reloc_info is None or reloc_info[1] is not runtime_hunk.RelocMode.ABSOLUTE:
                continue
            reloc_size = reloc_info[0]
            for offset in reloc.offsets:
                target = resolve_reloc_target(reloc, offset, hunk.data)
                if target is None:
                    continue
                inst_start = offset - runtime_m68k_analysis.OPWORD_BYTES
                inst_end = offset + reloc_size
                if inst_start < 0 or inst_end > len(hunk.data):
                    continue
                try:
                    instructions = disassemble(
                        hunk.data[inst_start:inst_end],
                        base_offset=inst_start,
                    )
                except Exception:
                    continue
                if len(instructions) != 1:
                    continue
                inst = instructions[0]
                if inst.offset != inst_start or inst.kb_mnemonic is None:
                    continue
                flow = runtime_m68k_analysis.FLOW_TYPES[instruction_kb(inst)]
                if flow not in (_FLOW_BRANCH, _FLOW_CALL, _FLOW_JUMP):
                    continue
                targets_by_hunk.setdefault(target_hunk, set()).add(target)
    return {
        hunk_index: tuple(sorted(targets))
        for hunk_index, targets in targets_by_hunk.items()
    }


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
                        else _rebase_decoded_for_emit(
                            instruction.decoded_operands, base_addr, code_size
                        )
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
            successors=[
                _maybe_rebase_addr(successor, base_addr, code_size)
                for successor in block.successors
            ],
            predecessors=[
                _maybe_rebase_addr(predecessor, base_addr, code_size)
                for predecessor in block.predecessors
            ],
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
    return replace(
        operand, value=_maybe_rebase_addr(operand.value, base_addr, code_size)
    )


def _rebase_decoded_operand_node(
    node: DecodedOperandNode, base_addr: int, code_size: int
) -> DecodedOperandNode:
    target = node.target
    if target is not None:
        target = _maybe_rebase_addr(target, base_addr, code_size)
    value = node.value
    if value is not None and node.kind in (
        "branch_target",
        "pc_relative_target",
        "absolute_target",
    ):
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
            targets=tuple(
                _maybe_rebase_addr(target, base_addr, code_size)
                for target in region.targets
            ),
            base_addr=None
            if region.base_addr is None
            else _maybe_rebase_addr(region.base_addr, base_addr, code_size),
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
    keep = {addr for addr, block in blocks.items() if block.end > entry_point}
    filtered: dict[int, BasicBlock] = {}
    for _addr, block in blocks.items():
        if block.end <= entry_point:
            continue
        kept_instructions = [
            inst for inst in block.instructions if inst.offset >= entry_point
        ]
        if not kept_instructions:
            continue
        new_start = entry_point if block.start < entry_point else block.start
        filtered[new_start] = replace(
            block,
            start=new_start,
            instructions=kept_instructions,
            is_entry=(block.is_entry or new_start == entry_point),
            successors=[succ for succ in block.successors if succ in keep],
            predecessors=[
                pred
                for pred in block.predecessors
                if pred in keep and pred >= entry_point
            ],
            xrefs=[
                xref
                for xref in block.xrefs
                if xref.src >= entry_point and xref.dst >= entry_point
            ],
        )
    return filtered


def _analysis_entry_floor(entry_points: tuple[int, ...]) -> int | None:
    if not entry_points:
        return None
    return min(entry_points)


def _inferred_execution_view_entrypoints(
    *,
    analysis_floor: int,
    entry_points: tuple[int, ...],
    extra_entry_points: tuple[int, ...],
    execution_views: tuple[ExecutionViewMetadata, ...],
) -> tuple[int, ...]:
    existing = set(entry_points)
    existing.update(extra_entry_points)
    inferred = {
        view.source_start
        for view in execution_views
        if view.source_start >= analysis_floor
        if view.source_start not in existing
    }
    return tuple(sorted(inferred))


def _load_or_analyze_hunk_session(
    *,
    source: BinarySource,
    hunk: Hunk,
    base_addr: int,
    code_start: int,
    entry_points: tuple[int, ...],
    extra_entry_points: tuple[int, ...],
    seed_config: object,
    entry_initial_states: object,
    target_metadata: TargetMetadata | None,
    phase_timer: PhaseTimer | None,
) -> tuple[HunkAnalysis, tuple[int, ...]]:
    def run_analysis(extra_points: tuple[int, ...]) -> HunkAnalysis:
        if source.kind == "raw_binary":
            return analyze_hunk(
                hunk.data,
                [],
                hunk.index,
                base_addr=base_addr,
                code_start=code_start,
                entry_points=entry_points,
                extra_entry_points=extra_points,
                initial_state=cast(Any, seed_config).initial_state,
                entry_initial_states=cast(Any, entry_initial_states),
                phase_timer=phase_timer,
            )
        return load_hunk_analysis(
            analysis_cache_path=source.analysis_cache_path,
            code=hunk.data,
            relocs=hunk.relocs,
            hunk_index=hunk.index,
            base_addr=base_addr,
            code_start=code_start,
            entry_points=entry_points,
            extra_entry_points=extra_points,
            seed_key=cast(Any, seed_config).seed_key,
            initial_state=cast(Any, seed_config).initial_state,
            entry_initial_states=cast(Any, entry_initial_states),
        )

    ha = run_analysis(extra_entry_points)
    execution_views = _execution_views_for_session(
        code=hunk.data,
        blocks=ha.blocks,
        target_metadata=target_metadata,
        relocated_segments=ha.relocated_segments,
        physical_stored_size=hunk.stored_size,
    )
    analysis_floor = code_start
    if ha.relocated_segments:
        analysis_floor = max(analysis_floor, ha.relocated_segments[0].file_offset)
    inferred_extra = _inferred_execution_view_entrypoints(
        analysis_floor=analysis_floor,
        entry_points=entry_points,
        extra_entry_points=extra_entry_points,
        execution_views=execution_views,
    )
    if not inferred_extra:
        return ha, extra_entry_points
    merged_extra = tuple(sorted(set(extra_entry_points).union(inferred_extra)))
    return run_analysis(merged_extra), merged_extra


def _filter_hint_blocks_against_seeded_entities(
    hint_blocks: Mapping[int, DisasmBlockLike],
    target_metadata: TargetMetadata | None,
    *,
    hunk_index: int,
) -> dict[int, DisasmBlockLike]:
    if target_metadata is None or not target_metadata.seeded_entities:
        return dict(hint_blocks)
    seeded_ranges = [
        (entity.addr, entity.end)
        for entity in target_metadata.seeded_entities
        if entity.hunk == hunk_index
        and entity.end is not None
        and entity.type != "code"
    ]
    if not seeded_ranges:
        return dict(hint_blocks)
    filtered: dict[int, DisasmBlockLike] = {}
    for addr, block in hint_blocks.items():
        if any(block.start < end and block.end > start for start, end in seeded_ranges):
            continue
        filtered[addr] = block
    return filtered


def _seeded_code_note(*, comment: str | None, role: str | None = None) -> str | None:
    if comment is not None and role is not None:
        return f"{role}: {comment}"
    return comment if comment is not None else role


def _apply_seeded_code_annotations(
    *,
    target_metadata: TargetMetadata | None,
    hunk_index: int,
    code_size: int,
    labels: dict[int, str],
    addr_comments: dict[int, str],
) -> None:
    if target_metadata is None:
        return
    for seeded_entrypoint in target_metadata.seeded_code_entrypoints:
        if seeded_entrypoint.hunk != hunk_index:
            continue
        if not (0 <= seeded_entrypoint.addr < code_size):
            raise ValueError(
                f"Seeded code entrypoint 0x{seeded_entrypoint.addr:X} lies outside code size 0x{code_size:X}"
            )
        labels[seeded_entrypoint.addr] = seeded_entrypoint.name
        note = _seeded_code_note(
            comment=seeded_entrypoint.comment, role=seeded_entrypoint.role
        )
        if note is not None:
            addr_comments[seeded_entrypoint.addr] = note
    for seeded_label in target_metadata.seeded_code_labels:
        if seeded_label.hunk != hunk_index:
            continue
        if not (0 <= seeded_label.addr < code_size):
            raise ValueError(
                f"Seeded code label 0x{seeded_label.addr:X} lies outside code size 0x{code_size:X}"
            )
        labels[seeded_label.addr] = seeded_label.name
        note = _seeded_code_note(comment=seeded_label.comment)
        if note is not None:
            addr_comments[seeded_label.addr] = note


def _merge_missing_pc_targets(
    existing: dict[int, str],
    discovered: dict[int, str],
) -> dict[int, str]:
    merged = dict(existing)
    for addr, label in discovered.items():
        merged.setdefault(addr, label)
    return merged


def _derived_segment_struct_comments(call_setup_analysis: object) -> dict[int, str]:
    comments: dict[int, str] = {}
    segment_struct_regions = cast(
        dict[int, str], getattr(call_setup_analysis, "segment_struct_regions", {})
    )
    typed_data_comments = cast(
        dict[int, str], getattr(call_setup_analysis, "typed_data_comments", {})
    )
    typed_data_sizes = cast(
        dict[int, int], getattr(call_setup_analysis, "typed_data_sizes", {})
    )
    for start, struct_name in sorted(segment_struct_regions.items()):
        if start in typed_data_comments or start in typed_data_sizes:
            continue
        comments[start] = f"Derived data interpretation: {struct_name}"
    return comments


def _refresh_library_call_signatures(
    lib_calls: list[LibraryCall],
    os_kb: OsKb,
) -> list[LibraryCall]:
    refreshed: list[LibraryCall] = []
    for call in lib_calls:
        library = os_kb.LIBRARIES.get(call.library)
        if library is None:
            refreshed.append(call)
            continue
        function = library.functions.get(call.function)
        if function is None:
            refreshed.append(call)
            continue
        refreshed.append(
            replace(
                call,
                inputs=function.inputs,
                output=function.output,
                no_return=function.no_return,
                available_since=function.available_since,
                fd_version=function.fd_version,
            )
        )
    return refreshed


def _dynamic_structured_regions(
    *,
    target_metadata: TargetMetadata | None,
    hunk_index: int,
    reloc_map: dict[int, int],
    labels: dict[int, str],
    code: bytes,
) -> tuple[StructuredRegionSpec, ...]:
    if (
        target_metadata is None
        or hunk_index != 0
        or target_metadata.resident is None
        or not target_metadata.resident.auto_init
        or target_metadata.resident.autoinit is None
    ):
        return ()
    autoinit = target_metadata.resident.autoinit
    library_name = (
        target_metadata.library.library_name
        if target_metadata.library is not None
        else target_metadata.resident.name
    )
    struct_name = (
        runtime_os.META.named_base_structs.get(library_name, "LIB")
        if library_name is not None
        else "LIB"
    )
    stream_regions: list[StructuredRegionSpec] = []
    for index, word_name in enumerate(runtime_os.META.resident_autoinit_words):
        stream_format = runtime_os.META.resident_autoinit_word_stream_formats.get(word_name)
        if stream_format is None:
            continue
        ptr_addr = autoinit.payload_offset + (index * 4)
        stream_addr = reloc_map.get(ptr_addr)
        if stream_addr is None or stream_addr == 0:
            continue
        stream = decode_stream_by_name(code, stream_addr, runtime_os, stream_format)
        if stream is None:
            continue
        labels.setdefault(stream.start, f"resident_{word_name}")
        stream_regions.append(
            StructuredRegionSpec(
                start=stream.start,
                end=stream.end,
                subtype="typed_data_stream",
                struct_name=struct_name,
                stream_format=stream_format,
            )
        )
    return tuple(stream_regions)


def _apply_cross_hunk_reloc_labels(
    hunk_sessions: list[HunkDisassemblySession],
) -> None:
    sessions_by_index = {session.hunk_index: session for session in hunk_sessions}
    for hunk_session in hunk_sessions:
        reloc_labels: dict[int, str] = {}
        for offset, target in hunk_session.reloc_map.items():
            target_hunk = hunk_session.reloc_target_hunks.get(offset)
            if target_hunk is None or target_hunk == hunk_session.hunk_index:
                continue
            target_session = sessions_by_index.get(target_hunk)
            if target_session is None:
                continue
            label = target_session.labels.get(target)
            if label is None:
                continue
            reloc_labels[offset] = label
        hunk_session.reloc_labels = reloc_labels


def _default_cross_hunk_target_label(
    hunk_session: HunkDisassemblySession,
    addr: int,
    *,
    prefer_code: bool = False,
) -> str:
    for entity in hunk_session.entities:
        raw_addr = entity.get("addr")
        if not isinstance(raw_addr, str) or int(raw_addr, 16) != addr:
            continue
        raw_name = entity.get("name")
        if raw_name:
            return raw_name
        if entity.get("type") == "code":
            return f"sub_{addr:04x}"
        break
    if prefer_code:
        return f"sub_{addr:04x}" if addr not in hunk_session.blocks else f"loc_{addr:04x}"
    if addr in hunk_session.blocks:
        return f"loc_{addr:04x}"
    if addr in hunk_session.hint_blocks:
        return f"hint_{addr:04x}"
    if addr in hunk_session.jump_table_regions:
        return f"jt_{addr:04x}"
    if addr in hunk_session.string_addrs:
        return f"str_{addr:04x}"
    if addr in hunk_session.code_addrs:
        return f"loc_{addr:04x}"
    return f"dat_{addr:04x}"


def _reloc_target_prefers_code_label(
    hunk_session: HunkDisassemblySession,
    reloc_offset: int,
) -> bool:
    for block_set in (hunk_session.blocks, hunk_session.hint_blocks):
        for block in block_set.values():
            for inst in block.instructions:
                ext_start = inst.offset + runtime_m68k_analysis.OPWORD_BYTES
                if not (ext_start <= reloc_offset < inst.offset + inst.size):
                    continue
                if inst.kb_mnemonic is None:
                    return False
                flow = runtime_m68k_analysis.FLOW_TYPES[instruction_kb(inst)]
                return flow in (_FLOW_BRANCH, _FLOW_CALL, _FLOW_JUMP)
    return False


def _ensure_cross_hunk_target_labels(
    hunk_sessions: list[HunkDisassemblySession],
) -> None:
    sessions_by_index = {session.hunk_index: session for session in hunk_sessions}
    for hunk_session in hunk_sessions:
        for offset, target in hunk_session.reloc_map.items():
            target_hunk = hunk_session.reloc_target_hunks.get(offset)
            if target_hunk is None or target_hunk == hunk_session.hunk_index:
                continue
            target_session = sessions_by_index.get(target_hunk)
            if target_session is None or target in target_session.labels:
                continue
            target_session.labels[target] = _default_cross_hunk_target_label(
                target_session,
                target,
                prefer_code=_reloc_target_prefers_code_label(hunk_session, offset),
            )


def _apply_session_unique_labels(
    hunk_sessions: list[HunkDisassemblySession],
) -> None:
    name_counts: dict[str, int] = {}
    for hunk_session in hunk_sessions:
        for label in hunk_session.labels.values():
            name_counts[label] = name_counts.get(label, 0) + 1
    used: set[str] = set()
    for hunk_session in sorted(hunk_sessions, key=lambda session: session.hunk_index):
        rewritten: dict[int, str] = {}
        for addr, label in sorted(hunk_session.labels.items()):
            candidate = label
            if name_counts.get(label, 0) > 1:
                candidate = f"hunk_{hunk_session.hunk_index}_{label}"
            suffix = 2
            while candidate in used:
                candidate = f"hunk_{hunk_session.hunk_index}_{suffix}_{label}"
                suffix += 1
            rewritten[addr] = candidate
            used.add(candidate)
        hunk_session.labels = rewritten


def _decoded_source_register(inst: Instruction) -> str | None:
    ikb = instruction_kb(inst)
    decoded = decode_inst_operands(inst, ikb)
    source = decoded.ea_op
    if source is None or source.mode not in {"dn", "an"} or source.reg is None:
        return None
    prefix = "a" if source.mode == "an" else "d"
    return f"{prefix}{source.reg}"


@dataclass(frozen=True, slots=True)
class _SessionMemoryCellFact:
    typed_size: int | None = None
    typed_field: TypedDataFieldInfo | None = None
    addr_comment: str | None = None
    pointer_region: TypedMemoryRegion | None = None


def _merge_session_memory_cell_fact(
    existing: _SessionMemoryCellFact | None,
    candidate: _SessionMemoryCellFact,
) -> _SessionMemoryCellFact | None:
    if existing is None or existing == candidate:
        return candidate
    typed_size = (
        existing.typed_size
        if existing.typed_size == candidate.typed_size
        else (
            existing.typed_size
            if candidate.typed_size is None
            else candidate.typed_size if existing.typed_size is None else None
        )
    )
    typed_field = (
        existing.typed_field
        if existing.typed_field == candidate.typed_field
        else (
            existing.typed_field
            if candidate.typed_field is None
            else candidate.typed_field if existing.typed_field is None else None
        )
    )
    addr_comment = (
        existing.addr_comment
        if existing.addr_comment == candidate.addr_comment
        else (
            existing.addr_comment
            if candidate.addr_comment is None
            else candidate.addr_comment if existing.addr_comment is None else None
        )
    )
    if existing.pointer_region is None or existing.pointer_region == candidate.pointer_region:
        pointer_region = candidate.pointer_region
    elif candidate.pointer_region is None:
        pointer_region = existing.pointer_region
    else:
        pointer_region = None
    if (
        typed_size is None
        and typed_field is None
        and addr_comment is None
        and pointer_region is None
    ):
        return None
    return _SessionMemoryCellFact(
        typed_size=typed_size,
        typed_field=typed_field,
        addr_comment=addr_comment,
        pointer_region=pointer_region,
    )


def _absolute_operand_target(
    hunk_session: HunkDisassemblySession,
    inst: Instruction,
    operand: Operand | None,
) -> tuple[int, int] | None:
    if operand is None or operand.mode not in {"absw", "absl"} or operand.value is None:
        return None
    target_addr = (operand.value & 0xFFFF) if operand.mode == "absw" else operand.value
    target_hunk = hunk_session.hunk_index
    for ext_off in range(
        inst.offset + runtime_m68k_analysis.OPWORD_BYTES,
        inst.offset + inst.size,
    ):
        reloc_target = hunk_session.reloc_map.get(ext_off)
        if reloc_target != target_addr:
            continue
        target_hunk = hunk_session.reloc_target_hunks.get(ext_off, target_hunk)
        break
    return target_hunk, target_addr


def _source_memory_cell_fact(
    hunk_session: HunkDisassemblySession,
    inst: Instruction,
    current: dict[int, dict[int, _SessionMemoryCellFact]],
) -> _SessionMemoryCellFact | None:
    source_register = _decoded_source_register(inst)
    if source_register is not None:
        region = hunk_session.region_map.get(inst.offset, {}).get(source_register)
        if region is None:
            return None
        return _SessionMemoryCellFact(pointer_region=region)
    ikb = instruction_kb(inst)
    decoded = decode_inst_operands(inst, ikb)
    source = decoded.ea_op
    if source is None:
        return None
    source_target = _absolute_operand_target(hunk_session, inst, source)
    if source_target is not None:
        source_hunk, source_addr = source_target
        return current.get(source_hunk, {}).get(source_addr)
    if source.mode == "ind":
        if source.reg is None:
            return None
        base_register = f"a{source.reg}"
        displacement = 0
    elif source.mode == "disp":
        if source.reg is None or source.value is None:
            return None
        base_register = f"a{source.reg}"
        displacement = source.value
    else:
        return None
    base_region = hunk_session.region_map.get(inst.offset, {}).get(base_register)
    if base_region is None:
        return None
    resolved = resolve_struct_field(
        hunk_session.os_kb.STRUCTS,
        base_region.struct,
        base_region.struct_offset + displacement,
    )
    if resolved is None:
        return None
    pointer_region = None
    if resolved.field.pointer_struct is not None:
        struct_name = resolved.field.pointer_struct
        named_base = resolved.field.named_base
        if named_base is not None:
            struct_name = hunk_session.os_kb.META.named_base_structs.get(
                named_base,
                struct_name,
            )
        struct_def = hunk_session.os_kb.STRUCTS.get(struct_name)
        if struct_def is not None:
            provenance = (
                provenance_named_base(named_base)
                if named_base is not None
                else base_region.provenance
            )
            pointer_region = TypedMemoryRegion(
                struct=struct_name,
                size=struct_def.size,
                provenance=provenance,
            )
    operand_size = inst.operand_size
    typed_size = None if operand_size is None else _OPERAND_SIZE_BYTES.get(operand_size)
    return _SessionMemoryCellFact(
        typed_size=typed_size,
        typed_field=TypedDataFieldInfo(
            owner_struct=resolved.owner_struct,
            field_symbol=resolved.field.name,
            context_name=base_region.context_name,
        ),
        addr_comment=f"{resolved.owner_struct}.{resolved.field.name}",
        pointer_region=pointer_region,
    )


def _store_target_for_instruction(
    hunk_session: HunkDisassemblySession,
    inst: Instruction,
) -> tuple[int, int] | None:
    ikb = instruction_kb(inst)
    if ikb == "MOVEA":
        return None
    decoded = decode_inst_operands(inst, ikb)
    return _absolute_operand_target(hunk_session, inst, decoded.dst_op)


def _session_pointer_cell_symbol(region: TypedMemoryRegion, addr: int) -> str:
    derivation = region.provenance.derivation
    if derivation is not None and derivation.kind is MemoryRegionDerivationKind.NAMED_BASE:
        named_base = derivation.named_base
        if named_base is not None:
            return f"{named_base.replace('.', '_').lower()}_base"
    stem = "".join(
        ch.lower() if ch.isalnum() else "_"
        for ch in region.struct
    ).strip("_")
    if stem:
        suffix = "base" if stem.endswith(("library", "device", "resource")) else "ptr"
        return f"{stem}_{suffix}"
    return f"dat_{addr:04x}"


def _is_default_generated_label(label: str) -> bool:
    return label.startswith(("sub_", "loc_", "dat_", "hint_", "jt_"))


def _reserved_generated_label_names(
    *,
    labels: Mapping[int, str],
    app_offsets: Mapping[int, str],
    os_kb: OsKb,
    addr: int,
) -> set[str]:
    reserved = set(app_offsets.values())
    reserved.update(
        field.name
        for struct in os_kb.STRUCTS.values()
        if str(struct.source).lower() not in os_kb.META.include_min_versions
        for field in struct.fields
        if field.size > 0 and field.offset >= struct.base_offset
    )
    reserved.update(
        label
        for label_addr, label in labels.items()
        if label_addr != addr
    )
    return reserved


def _disambiguate_generated_label(
    *,
    labels: Mapping[int, str],
    app_offsets: Mapping[int, str],
    os_kb: OsKb,
    addr: int,
    symbol: str,
) -> str:
    reserved = _reserved_generated_label_names(
        labels=labels,
        app_offsets=app_offsets,
        os_kb=os_kb,
        addr=addr,
    )
    candidate = symbol
    if candidate in reserved:
        candidate = f"{symbol}_ptr"
    suffix = 2
    while candidate in reserved:
        candidate = f"{symbol}_ptr_{suffix}"
        suffix += 1
    return candidate


def _rename_reserved_generated_labels(
    *,
    labels: dict[int, str],
    entities: list[EntityRecord],
    app_offsets: Mapping[int, str],
    os_kb: OsKb,
) -> None:
    explicit_names = {
        raw_name
        for entity in entities
        if (raw_name := entity.get("name"))
    }
    for addr, label in list(labels.items()):
        if label in explicit_names:
            continue
        renamed = _disambiguate_generated_label(
            labels=labels,
            app_offsets=app_offsets,
            os_kb=os_kb,
            addr=addr,
            symbol=label,
        )
        if renamed != label:
            labels[addr] = renamed


def _apply_execution_view_source_labels(
    *,
    labels: dict[int, str],
    execution_views: tuple[ExecutionViewMetadata, ...],
) -> None:
    for view in execution_views:
        existing = labels.get(view.source_start)
        if existing is not None and not existing.startswith(("pcref_", "dat_")):
            continue
        labels[view.source_start] = f"loc_{view.source_start:04x}"


def _seeded_session_memory_cells(
    hunk_sessions: list[HunkDisassemblySession],
) -> dict[int, dict[int, _SessionMemoryCellFact]]:
    result: dict[int, dict[int, _SessionMemoryCellFact]] = {}
    for hunk_session in hunk_sessions:
        seeded = result.setdefault(hunk_session.hunk_index, {})
        all_addrs = (
            set(hunk_session.typed_data_sizes)
            | set(hunk_session.typed_data_fields)
            | set(hunk_session.addr_comments)
        )
        for addr in all_addrs:
            seeded[addr] = _SessionMemoryCellFact(
                typed_size=hunk_session.typed_data_sizes.get(addr),
                typed_field=hunk_session.typed_data_fields.get(addr),
                addr_comment=hunk_session.addr_comments.get(addr),
            )
    return result


def _collect_session_memory_cells(
    hunk_sessions: list[HunkDisassemblySession],
    current: dict[int, dict[int, _SessionMemoryCellFact]],
) -> dict[int, dict[int, _SessionMemoryCellFact]]:
    result = {
        hunk_index: dict(cells)
        for hunk_index, cells in current.items()
    }
    changed = True
    while changed:
        changed = False
        for hunk_session in hunk_sessions:
            for block in hunk_session.blocks.values():
                for inst in block.instructions:
                    operand_size = inst.operand_size
                    typed_size = (
                        None if operand_size is None else _OPERAND_SIZE_BYTES.get(operand_size)
                    )
                    if typed_size is None:
                        continue
                    source_fact = _source_memory_cell_fact(hunk_session, inst, result)
                    if source_fact is None:
                        continue
                    if source_fact.typed_size is None:
                        source_fact = replace(source_fact, typed_size=typed_size)
                    target = _store_target_for_instruction(hunk_session, inst)
                    if target is None:
                        continue
                    target_hunk, target_addr = target
                    existing = result.setdefault(target_hunk, {}).get(target_addr)
                    merged = _merge_session_memory_cell_fact(existing, source_fact)
                    if merged is None or merged == existing:
                        continue
                    result[target_hunk][target_addr] = merged
                    changed = True
    return result


def _refresh_session_memory_cells(
    hunk_sessions: list[HunkDisassemblySession],
) -> None:
    _normalize_session_os_kb(hunk_sessions)
    current = _seeded_session_memory_cells(hunk_sessions)
    memory_cells = _collect_session_memory_cells(hunk_sessions, current)
    if not memory_cells:
        return
    for hunk_session in hunk_sessions:
        cell_facts = memory_cells.get(hunk_session.hunk_index)
        blocks = {
            addr: cast(BasicBlock, block)
            for addr, block in hunk_session.blocks.items()
        }
        absolute_pointer_regions = {
            (cell_hunk, addr): fact.pointer_region
            for cell_hunk, cells in memory_cells.items()
            for addr, fact in cells.items()
            if fact.pointer_region is not None
        }
        if cell_facts:
            for addr, fact in cell_facts.items():
                if fact.pointer_region is not None:
                    existing_label = hunk_session.labels.get(addr)
                    symbol = _session_pointer_cell_symbol(fact.pointer_region, addr)
                    if existing_label is None or _is_default_generated_label(existing_label):
                        hunk_session.labels[addr] = _disambiguate_generated_label(
                            labels=hunk_session.labels,
                            app_offsets=hunk_session.app_offsets,
                            os_kb=hunk_session.os_kb,
                            addr=addr,
                            symbol=symbol,
                        )
                if fact.typed_size is not None:
                    hunk_session.typed_data_sizes[addr] = fact.typed_size
                if fact.typed_field is not None:
                    hunk_session.typed_data_fields[addr] = fact.typed_field
                if fact.addr_comment is not None:
                    hunk_session.addr_comments[addr] = fact.addr_comment
        hunk_session.region_map = propagate_typed_memory_regions(
            blocks,
            list(hunk_session.lib_calls),
            hunk_session.code,
            hunk_session.os_kb,
            hunk_session.platform,
            absolute_pointer_regions=absolute_pointer_regions,
            hunk_index=hunk_session.hunk_index,
            reloc_target_hunks=hunk_session.reloc_target_hunks,
        )
        hunk_session.lib_calls = tuple(refine_library_calls(
            blocks,
            list(hunk_session.lib_calls),
            hunk_session.code,
            hunk_session.os_kb,
            hunk_session.platform,
            region_map=hunk_session.region_map,
        ))
        hunk_session.lvo_equs, hunk_session.lvo_substitutions = build_lvo_substitutions(
            blocks=dict(hunk_session.blocks),
            lib_calls=list(hunk_session.lib_calls),
            hunk_entities=hunk_session.entities,
        )
        hunk_session.lvo_substitutions = _maybe_rebase_substitution_map(
            hunk_session.lvo_substitutions,
            instruction_addrs={
                inst.offset
                for block in hunk_session.blocks.values()
                for inst in block.instructions
            },
            base_addr=hunk_session.base_addr,
            code_size=hunk_session.code_size,
        )
        hunk_session.arg_constants, hunk_session.arg_substitutions = build_arg_substitutions(
            blocks=dict(hunk_session.blocks),
            lib_calls=list(hunk_session.lib_calls),
            hunk_entities=hunk_session.entities,
            os_kb=hunk_session.os_kb,
        )


def build_disassembly_session(
    binary_source: str | BinarySource,
    entities_path: str,
    output_path: str | None = None,
    base_addr: int = 0,
    code_start: int = 0,
    assembler_profile_name: str = "vasm",
    profile_stages: bool = False,
    phase_timer: PhaseTimer | None = None,
) -> DisassemblySession:
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
    target_dir = (
        Path(entities_path).parent if Path(entities_path).parent.exists() else None
    )
    target_name = infer_target_name(target_dir, entities_path)
    target_metadata = load_required_target_metadata(
        target_dir=target_dir,
        source_kind=source.kind,
        parent_disk_id=source.parent_disk_id,
    )
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
            extra_entry_points=target_seeded_entrypoint_offsets(
                target_metadata, hunk_index=0
            ),
            assembler_profile_name=assembler_profile_name,
            profile_stages=profile_stages,
            phase_timer=phase_timer,
        )

    hf = parse(source.read_bytes())
    custom_entry_points = resolved_entry_points(source, target_metadata, ())
    cross_hunk_entry_points = _cross_hunk_control_entrypoints(hf.hunks)
    first_code_hunk_seen = False

    for hunk in hf.hunks:
        if hunk.hunk_type == HunkType.HUNK_CODE:
            extra_entry_points = set(target_seeded_entrypoint_offsets(
                target_metadata, hunk_index=hunk.index
            ))
            extra_entry_points.update(cross_hunk_entry_points.get(hunk.index, ()))
            hunk_sessions.append(
                _build_hunk_session_data(
                    source=source,
                    entities=entities,
                    hunk=hunk,
                    hf_hunks=hf.hunks,
                    base_addr=base_addr,
                    code_start=code_start,
                    entry_points=(custom_entry_points if not first_code_hunk_seen else ()),
                    extra_entry_points=tuple(sorted(extra_entry_points)),
                    target_metadata=target_metadata,
                    apply_target_structure=not first_code_hunk_seen,
                    assembler_profile_name=assembler_profile_name,
                    phase_timer=phase_timer,
                )
            )
            first_code_hunk_seen = True
            continue
        if hunk.hunk_type not in (HunkType.HUNK_DATA, HunkType.HUNK_BSS):
            continue
        hunk_sessions.append(
            _build_noncode_hunk_session(
                entities=entities,
                hunk=hunk,
                hf_hunks=hf.hunks,
                assembler_profile_name=assembler_profile_name,
            )
        )

    _refresh_session_memory_cells(hunk_sessions)
    _ensure_cross_hunk_target_labels(hunk_sessions)
    _apply_session_unique_labels(hunk_sessions)
    _apply_cross_hunk_reloc_labels(hunk_sessions)

    return DisassemblySession(
        target_name=target_name,
        binary_path=Path(source.display_path),
        analysis_cache_path=source.analysis_cache_path,
        entities_path=Path(entities_path),
        output_path=Path(output_path) if output_path else None,
        entities=entities,
        hunk_sessions=hunk_sessions,
        target_metadata=target_metadata,
        source_kind=source.kind,
        raw_address_model=(
            None if source.kind != "raw_binary" else source.address_model
        ),
        profile_stages=profile_stages,
        assembler_profile_name=assembler_profile_name,
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
    extra_entry_points: tuple[int, ...],
    assembler_profile_name: str,
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
        extra_entry_points=extra_entry_points,
        target_metadata=target_metadata,
        apply_target_structure=True,
        assembler_profile_name=assembler_profile_name,
        phase_timer=phase_timer,
    )
    _refresh_session_memory_cells([hunk_session])
    _ensure_cross_hunk_target_labels([hunk_session])
    _apply_session_unique_labels([hunk_session])
    _apply_cross_hunk_reloc_labels([hunk_session])
    return DisassemblySession(
        target_name=target_name,
        binary_path=Path(source.display_path),
        analysis_cache_path=source.analysis_cache_path,
        entities_path=Path(entities_path),
        output_path=Path(output_path) if output_path else None,
        entities=entities,
        hunk_sessions=[hunk_session],
        target_metadata=target_metadata,
        source_kind=source.kind,
        raw_address_model=(
            None if source.kind != "raw_binary" else source.address_model
        ),
        profile_stages=profile_stages,
        assembler_profile_name=assembler_profile_name,
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
    extra_entry_points: tuple[int, ...],
    target_metadata: TargetMetadata | None,
    apply_target_structure: bool,
    assembler_profile_name: str,
    phase_timer: PhaseTimer | None,
) -> HunkDisassemblySession:
    seed_config = build_entry_seed_config(target_metadata)
    entry_initial_states = scoped_entry_initial_states(seed_config, entry_points)
    code = hunk.data
    code_size = len(code)
    physical_stored_size = hunk.stored_size
    hunk_entities = [e for e in entities if e.get("hunk") == hunk.index]
    hunk_entities.sort(key=lambda e: int(e["addr"], 16))

    with (
        phase_timer.phase("session.load_analysis")
        if phase_timer is not None
        else nullcontext()
    ):
        ha, extra_entry_points = _load_or_analyze_hunk_session(
            source=source,
            hunk=hunk,
            base_addr=base_addr,
            code_start=code_start,
            entry_points=entry_points,
            extra_entry_points=extra_entry_points,
            seed_config=seed_config,
            entry_initial_states=entry_initial_states,
            target_metadata=target_metadata,
            phase_timer=phase_timer,
        )
    if source.kind != "raw_binary" and ha.relocated_segments:
        ha = _remap_analysis_to_source(ha, physical_size=physical_stored_size)
    entry_point = _analysis_entry_floor(entry_points)
    blocks = _filter_pre_entry_blocks(ha.blocks, entry_point)
    hint_blocks: Mapping[int, DisasmBlockLike] = _filter_pre_entry_blocks(
        ha.hint_blocks, entry_point
    )
    hint_blocks = _filter_hint_blocks_against_seeded_entities(
        hint_blocks,
        target_metadata,
        hunk_index=hunk.index,
    )
    lib_calls = [
        call for call in ha.lib_calls if entry_point is None or call.addr >= entry_point
    ]
    os_kb = ha.os_kb
    if os_kb is None:
        raise ValueError(f"Analysis for hunk {hunk.index} did not provide an OS KB")
    os_kb = build_target_local_os_kb(os_kb, target_metadata)
    lib_calls = _refresh_library_call_signatures(lib_calls, os_kb)
    platform = ha.platform
    apply_entry_seed_config(platform, seed_config)
    exit_states = {
        addr: state
        for addr, state in ha.exit_states.items()
        if entry_point is None or addr >= entry_point
    }
    execution_views = _execution_views_for_session(
        code=code,
        blocks=blocks,
        target_metadata=target_metadata,
        relocated_segments=ha.relocated_segments,
        physical_stored_size=physical_stored_size,
    )
    relocated_segments = ha.relocated_segments
    stored_size = hunk.stored_size
    alloc_size = hunk.alloc_size
    with (
        phase_timer.phase("session.metadata")
        if phase_timer is not None
        else nullcontext()
    ):
        absolute_resolution = resolve_absolute_labels(
            platform=platform,
            target_metadata=target_metadata,
        )
        region_map = propagate_typed_memory_regions(
            blocks,
            lib_calls,
            code,
            os_kb,
            platform,
            target_metadata,
            hunk_index=hunk.index,
            reloc_target_hunks=ha.reloc_target_hunks if hasattr(ha, "reloc_target_hunks") else None,
        )
        inferred_structs, inferred_named_base_overrides = infer_named_base_extension_structs(
            blocks,
            region_map,
            os_kb,
        )
        if inferred_structs or inferred_named_base_overrides:
            os_kb = build_target_local_os_kb(
                os_kb,
                target_metadata,
                extra_custom_structs=inferred_structs,
                named_base_struct_overrides=inferred_named_base_overrides,
            )
            lib_calls = _refresh_library_call_signatures(lib_calls, os_kb)
            _apply_named_base_struct_overrides(platform, os_kb)
            region_map = propagate_typed_memory_regions(
                blocks,
                lib_calls,
                code,
                os_kb,
                platform,
                target_metadata,
                hunk_index=hunk.index,
                reloc_target_hunks=ha.reloc_target_hunks if hasattr(ha, "reloc_target_hunks") else None,
            )
        lib_calls = refine_library_calls(
            blocks,
            lib_calls,
            code,
            os_kb,
            platform,
            target_metadata,
            region_map=region_map,
        )
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
                        addr
                        for addr in ha.call_targets
                        if entry_point is None or addr >= entry_point
                    },
                    branch_targets={
                        addr
                        for addr in ha.branch_targets
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
        app_struct_regions = build_app_struct_regions(
            blocks, lib_calls, os_kb, platform, target_metadata
        )
        hardware_base_regs = collect_hardware_base_regs(blocks, code, platform)
    with (
        phase_timer.phase("session.substitutions")
        if phase_timer is not None
        else nullcontext()
    ):
        lvo_equs, lvo_substitutions = build_lvo_substitutions(
            blocks=blocks,
            lib_calls=lib_calls,
            hunk_entities=hunk_entities,
        )
        arg_constants, arg_substitutions = build_arg_substitutions(
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
            target_metadata=target_metadata,
        )
    labels = metadata.labels
    apply_generic_data_label_promotions(
        labels,
        metadata.pc_targets,
        metadata.generic_data_label_addrs,
        call_setup_analysis.segment_data_symbols,
    )
    for addr, symbol in call_setup_analysis.segment_data_symbols.items():
        if addr not in labels:
            labels[addr] = symbol
    for addr, symbol in call_setup_analysis.segment_code_symbols.items():
        labels[addr] = symbol
    _rename_reserved_generated_labels(
        labels=labels,
        entities=hunk_entities,
        app_offsets=app_offsets,
        os_kb=os_kb,
    )
    _apply_execution_view_source_labels(
        labels=labels,
        execution_views=execution_views,
    )
    data_access_sizes = collect_data_access_sizes(blocks, exit_states)
    if source.kind != "raw_binary" and relocated_segments:
        seg = relocated_segments[0]
        data_access_sizes = _remap_data_access_sizes_to_source(
            data_access_sizes,
            file_offset=seg.file_offset,
            base_addr=seg.base_addr,
            physical_size=physical_stored_size,
        )
    apply_generic_data_size_promotions(
        labels,
        metadata.generic_data_label_addrs,
        data_access_sizes,
    )
    unresolved_indirects = {
        site.addr: site
        for site in ha.indirect_sites
        if site.status == IndirectSiteStatus.UNRESOLVED
        and (entry_point is None or site.addr >= entry_point)
    }
    hint_blocks = metadata.hint_blocks
    dynamic_structured_regions = _dynamic_structured_regions(
        target_metadata=target_metadata,
        hunk_index=hunk.index,
        reloc_map=metadata.reloc_map,
        labels=labels,
        code=code,
    )
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
            _maybe_rebase_addr(addr, base_addr, code_size): size
            for addr, size in data_access_sizes.items()
        }
        unresolved_indirects = {
            _rebase_local_addr(addr, base_addr): site
            for addr, site in unresolved_indirects.items()
        }
        dynamic_structured_regions = tuple(
            replace(
                region,
                start=_rebase_local_addr(region.start, base_addr),
                end=_rebase_local_addr(region.end, base_addr),
            )
            for region in dynamic_structured_regions
        )
        labels = {
            _maybe_rebase_addr(addr, base_addr, code_size): label
            for addr, label in labels.items()
        }
        metadata = replace(
            metadata,
            code_addrs={
                _rebase_local_addr(addr, base_addr) for addr in metadata.code_addrs
            },
            hint_addrs={
                _rebase_local_addr(addr, base_addr) for addr in metadata.hint_addrs
            },
            hint_blocks=hint_blocks,
            pc_targets={
                _maybe_rebase_addr(addr, base_addr, code_size): label
                for addr, label in metadata.pc_targets.items()
            },
            string_addrs={
                _rebase_local_addr(addr, base_addr) for addr in metadata.string_addrs
            },
            generic_data_label_addrs={
                _maybe_rebase_addr(addr, base_addr, code_size)
                for addr in metadata.generic_data_label_addrs
            },
            jump_table_regions=_rebase_jump_table_regions(
                metadata.jump_table_regions, base_addr, code_size
            ),
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
        merged_pc_targets = _merge_missing_pc_targets(
            metadata.pc_targets,
            discover_pc_relative_targets(blocks, code),
        )
        merged_string_addrs = set(metadata.string_addrs)
        merged_string_addrs.update(
            addr for addr, name in merged_pc_targets.items() if name.startswith("str_")
        )
        merged_generic_data_label_addrs = set(metadata.generic_data_label_addrs)
        merged_generic_data_label_addrs.update(merged_pc_targets)
        for addr, label in merged_pc_targets.items():
            labels.setdefault(addr, label)
        metadata = replace(
            metadata,
            pc_targets=merged_pc_targets,
            string_addrs=merged_string_addrs,
            generic_data_label_addrs=merged_generic_data_label_addrs,
            labels=labels,
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
    addr_comments: dict[int, str] = {}
    _apply_seeded_code_annotations(
        target_metadata=target_metadata,
        hunk_index=hunk.index,
        code_size=code_size,
        labels=labels,
        addr_comments=addr_comments,
    )
    typed_data_comments = dict(call_setup_analysis.typed_data_comments)
    typed_data_fields = {
        addr: TypedDataFieldInfo(
            owner_struct=owner, field_symbol=field, context_name=context_name
        )
        for addr, (
            owner,
            field,
            context_name,
        ) in call_setup_analysis.typed_data_fields.items()
    }
    derived_struct_comments = _derived_segment_struct_comments(call_setup_analysis)
    typed_data_sizes = dict(call_setup_analysis.typed_data_sizes)
    if source.kind == "raw_binary" and source.address_model == "runtime_absolute":
        typed_data_comments = {
            _rebase_local_addr(addr, base_addr): comment
            for addr, comment in typed_data_comments.items()
        }
        typed_data_fields = {
            _rebase_local_addr(addr, base_addr): info
            for addr, info in typed_data_fields.items()
        }
        derived_struct_comments = {
            _rebase_local_addr(addr, base_addr): comment
            for addr, comment in derived_struct_comments.items()
        }
    for addr, comment in typed_data_comments.items():
        addr_comments[addr] = comment
    if source.kind == "raw_binary" and source.address_model == "runtime_absolute":
        typed_data_sizes = {
            _rebase_local_addr(addr, base_addr): size
            for addr, size in typed_data_sizes.items()
        }
    for addr, comment in derived_struct_comments.items():
        addr_comments.setdefault(addr, comment)
    with (
        phase_timer.phase("session.build") if phase_timer is not None else nullcontext()
    ):
        return HunkDisassemblySession(
            hunk_index=hunk.index,
            hunk_type=hunk.hunk_type,
            mem_type=hunk.mem_type,
            mem_attrs=hunk.mem_attrs,
            section_name=hunk.name,
            code=code,
            code_size=code_size,
            alloc_size=alloc_size,
            stored_size=stored_size,
            entities=hunk_entities,
            blocks=dict(blocks),
            hint_blocks=dict(hint_blocks),
            code_addrs=metadata.code_addrs,
            hint_addrs=metadata.hint_addrs,
            reloc_map=metadata.reloc_map,
            reloc_target_set=metadata.reloc_target_set,
            reloc_target_hunks=metadata.reloc_target_hunks,
            pc_targets=metadata.pc_targets,
            string_addrs=metadata.string_addrs,
            labels=labels,
            addr_comments=addr_comments,
            absolute_labels=metadata.absolute_labels,
            reserved_absolute_addrs=metadata.reserved_absolute_addrs,
            jump_table_regions=metadata.jump_table_regions,
            jump_table_target_sources=metadata.jump_table_target_sources,
            lib_calls=tuple(lib_calls),
            region_map=region_map,
            dynamic_structured_regions=dynamic_structured_regions,
            app_struct_regions=app_struct_regions,
            hardware_base_regs=hardware_base_regs,
            lvo_equs=lvo_equs,
            lvo_substitutions=lvo_substitutions,
            arg_substitutions=arg_substitutions,
            app_offsets=app_offsets,
            arg_annotations=arg_annotations,
            data_access_sizes=data_access_sizes,
            typed_data_sizes=typed_data_sizes,
            typed_data_fields=typed_data_fields,
            generic_data_label_addrs=metadata.generic_data_label_addrs,
            platform=platform,
            os_kb=os_kb,
            base_addr=base_addr,
            code_start=code_start,
            relocated_segments=relocated_segments,
            execution_views=execution_views,
            arg_constants=arg_constants,
            string_ranges=metadata.string_ranges,
            unresolved_indirects=unresolved_indirects,
            assembler_profile_name=assembler_profile_name,
        )


def _build_noncode_hunk_session(
    *,
    entities: list[EntityRecord],
    hunk: Hunk,
    hf_hunks: list[Hunk],
    assembler_profile_name: str,
) -> HunkDisassemblySession:
    hunk_entities = [e for e in entities if e.get("hunk") == hunk.index]
    hunk_entities.sort(key=lambda e: int(e["addr"], 16))
    metadata = build_hunk_metadata(
        code=hunk.data,
        code_size=len(hunk.data),
        hunk_index=hunk.index,
        hunk_entities=hunk_entities,
        ha=cast(
            HunkAnalysisLike,
            HunkAnalysis(
                code=hunk.data,
                hunk_index=hunk.index,
                blocks={},
                exit_states={},
                xrefs=[],
                call_targets=set(),
                branch_targets=set(),
                jump_tables=[],
                hint_blocks={},
                hint_reasons={},
                lib_calls=[],
                platform=get_platform_config(),
                reloc_targets=set(),
                reloc_refs=(),
                relocated_segments=[],
                os_kb=runtime_os,
            ),
        ),
        hf_hunks=hf_hunks,
    )
    labels = metadata.labels
    return HunkDisassemblySession(
        hunk_index=hunk.index,
        hunk_type=hunk.hunk_type,
        mem_type=hunk.mem_type,
        mem_attrs=hunk.mem_attrs,
        section_name=hunk.name,
        code=hunk.data,
        code_size=len(hunk.data),
        alloc_size=hunk.alloc_size,
        stored_size=hunk.stored_size,
        entities=hunk_entities,
        blocks={},
        hint_blocks={},
        code_addrs=metadata.code_addrs,
        hint_addrs=metadata.hint_addrs,
        reloc_map=metadata.reloc_map,
        reloc_target_set=metadata.reloc_target_set,
        pc_targets=metadata.pc_targets,
        string_addrs=metadata.string_addrs,
        labels=labels,
        jump_table_regions=metadata.jump_table_regions,
        jump_table_target_sources=metadata.jump_table_target_sources,
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=get_platform_config(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        execution_views=(),
        arg_constants=set(),
        absolute_labels=metadata.absolute_labels,
        reserved_absolute_addrs=metadata.reserved_absolute_addrs,
        reloc_target_hunks=metadata.reloc_target_hunks,
        assembler_profile_name=assembler_profile_name,
    )
