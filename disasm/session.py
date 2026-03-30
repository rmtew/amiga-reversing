"""Build canonical post-analysis disassembly sessions."""

from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

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
from disasm.discovery import apply_generic_data_label_promotions
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
    resolve_reloc_target,
)
from m68k.hunk_parser import Hunk, HunkType, MemType, parse
from m68k.indirect_core import IndirectSiteStatus
from m68k.instruction_decode import decode_inst_operands
from m68k.instruction_kb import instruction_kb
from m68k.instruction_primitives import Operand
from m68k.m68k_disasm import DecodedOperandNode, Instruction, disassemble
from m68k.m68k_executor import BasicBlock
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


def _prepare_hunk_code(
    code: bytes,
    relocated_segments: list[RelocatedSegment],
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


def _prepare_hunk_sizes(
    *,
    stored_size: int,
    alloc_size: int,
    reloc_file_offset: int,
    reloc_base_addr: int,
) -> tuple[int, int]:
    if reloc_file_offset == 0 and reloc_base_addr == 0:
        return stored_size, alloc_size
    runtime_stored_size = max(0, reloc_base_addr + (stored_size - reloc_file_offset))
    runtime_alloc_size = max(0, reloc_base_addr + (alloc_size - reloc_file_offset))
    assert runtime_alloc_size >= runtime_stored_size, (
        f"Runtime alloc size {runtime_alloc_size} < runtime stored size {runtime_stored_size}"
    )
    return runtime_stored_size, runtime_alloc_size


def _rebase_local_addr(addr: int, base_addr: int) -> int:
    rebased = addr - base_addr
    assert rebased >= 0
    return rebased


def _maybe_rebase_addr(addr: int, base_addr: int, code_size: int) -> int:
    if base_addr <= addr < base_addr + code_size:
        return _rebase_local_addr(addr, base_addr)
    return addr


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
                os_since=function.os_since,
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
        hunk_session.arg_equs, hunk_session.arg_substitutions = build_arg_substitutions(
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
    hunk_entities = [e for e in entities if e.get("hunk") == hunk.index]
    hunk_entities.sort(key=lambda e: int(e["addr"], 16))

    with (
        phase_timer.phase("session.load_analysis")
        if phase_timer is not None
        else nullcontext()
    ):
        if source.kind == "raw_binary":
            ha = analyze_hunk(
                code,
                [],
                hunk.index,
                base_addr=base_addr,
                code_start=code_start,
                entry_points=entry_points,
                extra_entry_points=extra_entry_points,
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
                extra_entry_points=extra_entry_points,
                seed_key=seed_config.seed_key,
                initial_state=seed_config.initial_state,
                entry_initial_states=entry_initial_states,
            )
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
    relocated_segments = ha.relocated_segments
    code, code_size, relocated_segments, reloc_file_offset, reloc_base_addr = (
        _prepare_hunk_code(code, relocated_segments)
    )
    stored_size, alloc_size = _prepare_hunk_sizes(
        stored_size=hunk.stored_size,
        alloc_size=hunk.alloc_size,
        reloc_file_offset=reloc_file_offset,
        reloc_base_addr=reloc_base_addr,
    )
    with (
        phase_timer.phase("session.metadata")
        if phase_timer is not None
        else nullcontext()
    ):
        absolute_resolution = resolve_absolute_labels(platform=platform)
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
    data_access_sizes = collect_data_access_sizes(blocks, exit_states)
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
            _rebase_local_addr(addr, base_addr): size
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
            arg_equs=arg_equs,
            arg_substitutions=arg_substitutions,
            app_offsets=app_offsets,
            arg_annotations=arg_annotations,
            data_access_sizes=data_access_sizes,
            typed_data_sizes=typed_data_sizes,
            typed_data_fields=typed_data_fields,
            platform=platform,
            os_kb=os_kb,
            base_addr=base_addr,
            code_start=code_start,
            relocated_segments=relocated_segments,
            reloc_file_offset=reloc_file_offset,
            reloc_base_addr=reloc_base_addr,
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
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=get_platform_config(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        absolute_labels=metadata.absolute_labels,
        reserved_absolute_addrs=metadata.reserved_absolute_addrs,
        reloc_target_hunks=metadata.reloc_target_hunks,
        assembler_profile_name=assembler_profile_name,
    )
