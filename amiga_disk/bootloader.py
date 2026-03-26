from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from amiga_disk.kb import PROJECT_ROOT, DiskKb, load_disk_kb
from amiga_disk.models import (
    BootloaderAnalysis,
    BootloaderDecodeOutput,
    BootloaderDecodeRegion,
    BootloaderDerivedRegion,
    BootloaderDiskRead,
    BootloaderHandoff,
    BootloaderLoad,
    BootloaderMemoryAccess,
    BootloaderMemoryCopy,
    BootloaderMemoryRegion,
    BootloaderReadSetup,
    BootloaderStage,
    BootloaderTransfer,
    RawTrackSource,
    RawTrackSourceSpan,
)
from m68k.abstract_values import _concrete
from m68k.m68k_disasm import (
    DecodedBaseDisplacementNodeMetadata,
    DecodedBaseRegisterNodeMetadata,
    DecodedOperandNode,
    Instruction,
)
from m68k.m68k_executor import (
    AbstractMemory,
    CPUState,
    collect_instruction_traces,
    discover_blocks,
)
from m68k.typing_protocols import MemoryLike


@dataclass(slots=True)
class _InstructionTrace:
    incoming_source: int
    inst: Instruction
    pre_cpu: CPUState
    pre_mem: MemoryLike
    post_cpu: CPUState
    post_mem: MemoryLike


@dataclass(slots=True)
class _FloppyControlState:
    port_value: int | None
    drive: int | None
    cylinder: int
    head: int
    motor_on: bool | None
    direction_inward: bool | None


def _size_bits(inst: Instruction) -> int:
    return {"b": 8, "w": 16, "l": 32}.get(inst.operand_size or "", 0)


def _branch_target(inst: Instruction) -> int | None:
    for node in inst.operand_nodes or ():
        if node.kind == "branch_target":
            target = node.target
            assert target is None or isinstance(target, int)
            return target
    return None


def _jump_target(inst: Instruction) -> int | None:
    for node in inst.operand_nodes or ():
        if node.kind == "absolute_target":
            target = node.target
            assert target is None or isinstance(target, int)
            return target
    return None


def _register_value(cpu: CPUState, register: str) -> int | None:
    normalized = register.lower()
    if normalized == "sp":
        return cpu.sp.concrete if cpu.sp.is_known else None
    if len(normalized) != 2 or not normalized[1].isdigit():
        return None
    reg_num = int(normalized[1])
    if normalized[0] == "d":
        value = cpu.get_reg("dn", reg_num)
        return value.concrete if value.is_known else None
    if normalized[0] == "a":
        value = cpu.get_reg("an", reg_num)
        return value.concrete if value.is_known else None
    return None


def _resolve_source_value(src_node: DecodedOperandNode, cpu: CPUState) -> int | None:
    if src_node.kind == "immediate":
        return src_node.value if isinstance(src_node.value, int) else None
    if src_node.kind == "absolute_target":
        return src_node.target if isinstance(src_node.target, int) else None
    if src_node.kind == "register" and src_node.register is not None:
        return _register_value(cpu, src_node.register)
    return None


def _read_mem_int(mem: MemoryLike, addr: int, size: str) -> int | None:
    value = mem.read(addr, size)
    return value.concrete if value.is_known else None


def _record_memory_access(
    kb: DiskKb,
    inst: Instruction,
    pre_cpu: CPUState,
    hardware_accesses: list[BootloaderMemoryAccess],
) -> None:
    nodes = list(inst.operand_nodes or ())
    if len(nodes) != 2:
        return
    src_node = nodes[0]
    dst_node = nodes[1]
    resolved_value = _resolve_source_value(src_node, pre_cpu)
    address: int | None = None
    if dst_node.kind == "absolute_target":
        address = dst_node.target
    elif dst_node.kind == "base_displacement":
        metadata = dst_node.metadata
        assert isinstance(metadata, DecodedBaseDisplacementNodeMetadata)
        base_value = _register_value(pre_cpu, metadata.base_register)
        if base_value is None:
            return
        address = base_value + metadata.displacement
    if address is None:
        return
    symbol = kb.boot_loader.tracked_hardware_registers.get(address)
    if symbol is None:
        return
    hardware_accesses.append(
        BootloaderMemoryAccess(
            instruction_addr=inst.offset,
            access="write",
            width_bits=_size_bits(inst),
            address=address,
            symbol=symbol,
            value=resolved_value,
        )
    )


def _maybe_record_load(
    kb: DiskKb,
    inst: Instruction,
    pre_mem: MemoryLike,
    loads: list[BootloaderLoad],
) -> None:
    if inst.opcode_text != "jsr":
        return
    nodes = list(inst.operand_nodes or ())
    if len(nodes) != 1:
        return
    target_node = nodes[0]
    if target_node.kind != "base_displacement":
        return
    metadata = target_node.metadata
    assert isinstance(metadata, DecodedBaseDisplacementNodeMetadata)
    if metadata.base_register != "a6":
        return
    vector_name = kb.boot_loader.exec_vectors_by_lvo.get(metadata.displacement)
    if vector_name != "DoIO":
        return
    offsets = kb.boot_loader.iostdreq_offsets
    io_command = _read_mem_int(pre_mem, offsets["io_Command"], "w")
    io_length = _read_mem_int(pre_mem, offsets["io_Length"], "l")
    io_data = _read_mem_int(pre_mem, offsets["io_Data"], "l")
    io_offset = _read_mem_int(pre_mem, offsets["io_Offset"], "l")
    if io_command is None or io_length is None or io_data is None or io_offset is None:
        return
    command_name = kb.boot_loader.trackdisk_commands.get(io_command)
    if command_name is None:
        return
    loads.append(
        BootloaderLoad(
            instruction_addr=inst.offset,
            command_name=command_name,
            disk_offset=io_offset,
            byte_length=io_length,
            destination_addr=io_data,
        )
    )


def _boot_initial_state() -> tuple[CPUState, AbstractMemory]:
    cpu = CPUState()
    mem = AbstractMemory()
    cpu.set_reg("an", 1, _concrete(0))
    return cpu, mem


def _empty_initial_state() -> tuple[CPUState, AbstractMemory]:
    return CPUState(), AbstractMemory()


def _instruction_traces(
    stage: bytes,
    *,
    base_addr: int,
    entry_addr: int,
    initial_cpu: CPUState,
    initial_mem: AbstractMemory,
    watch_ranges: list[tuple[int, int]] | None = None,
) -> list[_InstructionTrace]:
    blocks = discover_blocks(stage, base_addr, [entry_addr])
    if not blocks:
        return []
    return [
        _InstructionTrace(
            incoming_source=trace.incoming_source,
            inst=trace.instruction,
            pre_cpu=trace.pre_cpu,
            pre_mem=trace.pre_mem,
            post_cpu=trace.post_cpu,
            post_mem=trace.post_mem,
        )
        for trace in collect_instruction_traces(
            blocks,
            stage,
            base_addr=base_addr,
            initial_state=initial_cpu.copy(),
            initial_mem=initial_mem.copy(),
            watch_ranges=watch_ranges,
        )
    ]


def _scan_stage(
    kb: DiskKb,
    stage: bytes,
    *,
    name: str,
    base_addr: int,
    entry_addr: int,
    initial_cpu: CPUState,
    initial_mem: AbstractMemory,
    raw_track_sources: list[RawTrackSource],
    disk_bytes: bytes | None,
) -> BootloaderStage:
    watch_ranges = _trace_watch_ranges(kb, [])
    raw_traces = _instruction_traces(
        stage,
        base_addr=base_addr,
        entry_addr=entry_addr,
        initial_cpu=initial_cpu,
        initial_mem=initial_mem,
        watch_ranges=watch_ranges,
    )
    stage_result = _analyze_stage_result(kb, raw_traces, raw_track_sources, disk_bytes)
    seeded_mem = _seed_decode_input_memory(initial_mem, stage_result.decode_regions, disk_bytes)
    expanded_watch_ranges = _trace_watch_ranges(kb, stage_result.decode_regions)
    if seeded_mem is not None:
        raw_traces = _instruction_traces(
            stage,
            base_addr=base_addr,
            entry_addr=entry_addr,
            initial_cpu=initial_cpu,
            initial_mem=seeded_mem,
            watch_ranges=expanded_watch_ranges,
        )
        stage_result = _analyze_stage_result(kb, raw_traces, raw_track_sources, disk_bytes)
    elif expanded_watch_ranges != watch_ranges:
        raw_traces = _instruction_traces(
            stage,
            base_addr=base_addr,
            entry_addr=entry_addr,
            initial_cpu=initial_cpu,
            initial_mem=initial_mem,
            watch_ranges=expanded_watch_ranges,
        )
        stage_result = _analyze_stage_result(kb, raw_traces, raw_track_sources, disk_bytes)
    if seeded_mem is None:
        replayed_result = _replay_best_candidate_stage_result(
            kb,
            stage,
            base_addr=base_addr,
            entry_addr=entry_addr,
            initial_cpu=initial_cpu,
            initial_mem=initial_mem,
            stage_result=stage_result,
            raw_track_sources=raw_track_sources,
            disk_bytes=disk_bytes,
        )
        if replayed_result is not None:
            stage_result = replayed_result
    if stage_result.handoff_target is not None:
        memory_copies = [
            copy for copy in stage_result.memory_copies
            if copy.destination_addr == stage_result.handoff_target
        ] or stage_result.memory_copies
    else:
        memory_copies = stage_result.memory_copies
    return BootloaderStage(
        name=name,
        base_addr=base_addr,
        entry_addr=entry_addr,
        size=len(stage),
        materialized=True,
        reachable_instruction_count=len({trace.inst.offset for trace in stage_result.traces}),
        hardware_accesses=stage_result.hardware_accesses,
        loads=stage_result.loads,
        disk_reads=stage_result.disk_reads,
        memory_copies=memory_copies,
        read_setups=stage_result.read_setups,
        decode_outputs=stage_result.decode_outputs,
        decode_regions=stage_result.decode_regions,
        derived_regions=stage_result.derived_regions,
        handoffs=stage_result.handoffs,
        handoff_target=stage_result.handoff_target,
    )


@dataclass(slots=True)
class _StageAnalysisResult:
    traces: list[_InstructionTrace]
    hardware_accesses: list[BootloaderMemoryAccess]
    loads: list[BootloaderLoad]
    disk_reads: list[BootloaderDiskRead]
    memory_copies: list[BootloaderMemoryCopy]
    read_setups: list[BootloaderReadSetup]
    decode_outputs: list[BootloaderDecodeOutput]
    decode_regions: list[BootloaderDecodeRegion]
    derived_regions: list[BootloaderDerivedRegion]
    handoffs: list[BootloaderHandoff]
    handoff_target: int | None


def _analyze_stage_result(
    kb: DiskKb,
    raw_traces: list[_InstructionTrace],
    raw_track_sources: list[RawTrackSource],
    disk_bytes: bytes | None,
) -> _StageAnalysisResult:
    traces = _select_best_traces(raw_traces)
    hardware_accesses: list[BootloaderMemoryAccess] = []
    loads: list[BootloaderLoad] = []
    for trace in traces:
        _record_memory_access(kb, trace.inst, trace.pre_cpu, hardware_accesses)
        _maybe_record_load(kb, trace.inst, trace.pre_mem, loads)
    memory_copies = _infer_memory_copies(traces)
    handoff_target = _infer_handoff_target(traces)
    read_setups = _infer_read_setups(kb, traces, hardware_accesses)
    decode_outputs = _infer_decode_outputs(kb, traces)
    disk_reads = _build_disk_reads(loads)
    decode_regions = _build_decode_regions(
        kb,
        traces,
        disk_reads,
        read_setups,
        decode_outputs,
        raw_track_sources,
        disk_bytes,
    )
    derived_regions = _build_derived_regions(raw_traces, decode_regions)
    handoffs = _build_handoffs(traces, handoff_target, decode_regions)
    return _StageAnalysisResult(
        traces=traces,
        hardware_accesses=hardware_accesses,
        loads=loads,
        disk_reads=disk_reads,
        memory_copies=memory_copies,
        read_setups=read_setups,
        decode_outputs=decode_outputs,
        decode_regions=decode_regions,
        derived_regions=derived_regions,
        handoffs=handoffs,
        handoff_target=handoff_target,
    )


def _seed_decode_input_memory(
    initial_mem: AbstractMemory,
    decode_regions: list[BootloaderDecodeRegion],
    disk_bytes: bytes | None,
) -> AbstractMemory | None:
    if disk_bytes is None:
        return None
    seeded_mem: AbstractMemory | None = None
    for region in decode_regions:
        if region.input_buffer_addr is None or region.input_required_byte_length is None:
            continue
        if len(region.input_source_candidate_spans) != 1:
            continue
        if seeded_mem is None:
            seeded_mem = initial_mem.copy()
        if not _seed_region_from_span(seeded_mem, region, region.input_source_candidate_spans[0], disk_bytes):
            continue
    return seeded_mem


def _seed_region_from_span(
    mem: AbstractMemory,
    region: BootloaderDecodeRegion,
    span: RawTrackSourceSpan,
    disk_bytes: bytes,
) -> bool:
    if region.input_buffer_addr is None or region.input_required_byte_length is None:
        return False
    start = span.start_byte_offset
    end = start + region.input_required_byte_length
    if end > len(disk_bytes):
        return False
    payload = disk_bytes[start:end]
    if len(payload) != region.input_required_byte_length:
        return False
    for offset, value in enumerate(payload):
        mem.write(region.input_buffer_addr + offset, _concrete(value), "b")
    return True


def _trace_watch_ranges(
    kb: DiskKb,
    decode_regions: list[BootloaderDecodeRegion],
) -> list[tuple[int, int]]:
    offsets = kb.boot_loader.iostdreq_offsets
    ranges: list[tuple[int, int]] = [
        (0, max(offsets.values()) + 4),
    ]
    for region in decode_regions:
        if region.input_buffer_addr is not None:
            if region.byte_length is not None:
                ranges.append((region.input_buffer_addr, region.input_buffer_addr + region.byte_length))
            else:
                prefix_length = kb.boot_loader.trace_watch_input_prefix_bytes_when_output_unknown
                if region.input_required_byte_length is not None:
                    prefix_length = min(prefix_length, region.input_required_byte_length)
                ranges.append((region.input_buffer_addr, region.input_buffer_addr + prefix_length))
        if region.output_base_addr is not None and region.byte_length is not None:
            ranges.append((region.output_base_addr, region.output_base_addr + region.byte_length))
        elif region.output_addr is not None and region.byte_length is not None:
            ranges.append((region.output_addr, region.output_addr + region.byte_length))
    return ranges


def _replay_best_candidate_stage_result(
    kb: DiskKb,
    stage: bytes,
    *,
    base_addr: int,
    entry_addr: int,
    initial_cpu: CPUState,
    initial_mem: AbstractMemory,
    stage_result: _StageAnalysisResult,
    raw_track_sources: list[RawTrackSource],
    disk_bytes: bytes | None,
) -> _StageAnalysisResult | None:
    if disk_bytes is None:
        return None
    if len(stage) > kb.boot_loader.max_candidate_replay_stage_bytes:
        return None
    unresolved_regions = [
        region
        for region in stage_result.decode_regions
        if region.input_buffer_addr is not None
        and region.input_required_byte_length is not None
        and not region.input_complete
        and len(region.input_source_candidate_spans) > 1
    ]
    if len(unresolved_regions) != 1:
        return None
    region = unresolved_regions[0]
    if len(region.input_source_candidate_spans) > kb.boot_loader.max_candidate_replay_spans:
        return None
    base_score = _stage_result_score(stage_result)
    scored_results: list[tuple[tuple[int, ...], _StageAnalysisResult]] = []
    for span in region.input_source_candidate_spans:
        seeded_mem = initial_mem.copy()
        if not _seed_region_from_span(seeded_mem, region, span, disk_bytes):
            continue
        watch_ranges = _trace_watch_ranges(kb, stage_result.decode_regions)
        raw_traces = _instruction_traces(
            stage,
            base_addr=base_addr,
            entry_addr=entry_addr,
            initial_cpu=initial_cpu,
            initial_mem=seeded_mem,
            watch_ranges=watch_ranges,
        )
        replayed = _analyze_stage_result(kb, raw_traces, raw_track_sources, disk_bytes)
        replayed_score = _stage_result_score(replayed)
        if replayed_score > base_score:
            scored_results.append((replayed_score, replayed))
    if not scored_results:
        return None
    best_score = max(score for score, _ in scored_results)
    best_results = [result for score, result in scored_results if score == best_score]
    if len(best_results) != 1:
        return None
    return best_results[0]


def _stage_result_score(stage_result: _StageAnalysisResult) -> tuple[int, ...]:
    return (
        1 if stage_result.handoff_target is not None else 0,
        sum(1 for region in stage_result.derived_regions if region.complete),
        sum(region.concrete_byte_count for region in stage_result.derived_regions),
        sum(1 for region in stage_result.decode_regions if region.input_complete),
        sum(region.input_concrete_byte_count for region in stage_result.decode_regions),
        len({trace.inst.offset for trace in stage_result.traces}),
    )


def _trace_score(trace: _InstructionTrace) -> tuple[int, int]:
    known_regs = 0
    for index in range(8):
        if trace.pre_cpu.get_reg("dn", index).is_known:
            known_regs += 1
        if trace.pre_cpu.get_reg("an", index).is_known:
            known_regs += 1
    return known_regs, -trace.incoming_source


def _select_best_traces(traces: list[_InstructionTrace]) -> list[_InstructionTrace]:
    best_by_addr: dict[int, _InstructionTrace] = {}
    for trace in traces:
        current = best_by_addr.get(trace.inst.offset)
        if current is None or _trace_score(trace) > _trace_score(current):
            best_by_addr[trace.inst.offset] = trace
    return [best_by_addr[offset] for offset in sorted(best_by_addr)]


def _infer_handoff_target(traces: list[_InstructionTrace]) -> int | None:
    jumps = [trace for trace in traces if trace.inst.opcode_text == "jmp"]
    if not jumps:
        return None
    return _jump_target(jumps[-1].inst)


def _build_disk_reads(loads: list[BootloaderLoad]) -> list[BootloaderDiskRead]:
    return [
        BootloaderDiskRead(
            instruction_addr=load.instruction_addr,
            command_name=load.command_name,
            source_kind="logical_disk_offset",
            disk_offset=load.disk_offset,
            byte_length=load.byte_length,
            destination_addr=load.destination_addr,
        )
        for load in loads
    ]


def _operand_byte_size(inst: Instruction) -> int:
    return max(1, _size_bits(inst) // 8)


def _operand_memory_addr(
    node: DecodedOperandNode,
    cpu: CPUState,
    *,
    opcode: str,
) -> int | None:
    if node.kind == "absolute_target":
        if opcode in {"jmp", "jsr", "lea", "pea"}:
            return None
        target = node.target
        return target if isinstance(target, int) else None
    if node.kind in {"indirect", "postincrement", "predecrement"}:
        metadata = node.metadata
        assert isinstance(metadata, DecodedBaseRegisterNodeMetadata)
        return _register_value(cpu, metadata.base_register)
    if node.kind == "base_displacement":
        metadata = node.metadata
        assert isinstance(metadata, DecodedBaseDisplacementNodeMetadata)
        base_value = _register_value(cpu, metadata.base_register)
        if base_value is None:
            return None
        displacement = metadata.displacement
        assert isinstance(displacement, int)
        return base_value + displacement
    return None


def _memory_read_ranges(trace: _InstructionTrace) -> list[tuple[int, int]]:
    nodes = list(trace.inst.operand_nodes or ())
    if not nodes:
        return []
    opcode = trace.inst.opcode_text
    byte_size = _operand_byte_size(trace.inst)
    ranges: list[tuple[int, int]] = []
    for index, node in enumerate(nodes):
        addr = _operand_memory_addr(node, trace.pre_cpu, opcode=opcode)
        if addr is None:
            continue
        is_destination = len(nodes) > 1 and index == len(nodes) - 1
        if is_destination and opcode.startswith(("move", "clr")):
            continue
        ranges.append((addr, byte_size))
    return ranges


def _infer_input_consumed_range(
    traces: list[_InstructionTrace],
    *,
    input_buffer_addr: int,
    input_required_byte_length: int | None,
    output_byte_length: int | None,
    scan_start_addr: int | None,
    scan_end_addr: int,
) -> tuple[int | None, int | None]:
    buffer_end = None if input_required_byte_length is None else input_buffer_addr + input_required_byte_length
    consumed_start: int | None = None
    consumed_end: int | None = None
    for trace in traces:
        if scan_start_addr is not None and trace.inst.offset < scan_start_addr:
            continue
        if trace.inst.offset > scan_end_addr:
            continue
        for addr, byte_length in _memory_read_ranges(trace):
            if addr + byte_length <= input_buffer_addr:
                continue
            if buffer_end is not None and addr >= buffer_end:
                continue
            clamped_start = max(addr, input_buffer_addr)
            clamped_end = addr + byte_length if buffer_end is None else min(addr + byte_length, buffer_end)
            if clamped_end <= clamped_start:
                continue
            consumed_start = clamped_start if consumed_start is None else min(consumed_start, clamped_start)
            consumed_end = clamped_end if consumed_end is None else max(consumed_end, clamped_end)
    if consumed_start is None or consumed_end is None:
        return None, None
    consumed_offset = consumed_start - input_buffer_addr
    consumed_length = consumed_end - consumed_start
    if output_byte_length is not None:
        consumed_length = min(consumed_length, output_byte_length)
    return consumed_offset, consumed_length


def _infer_write_loop_input_offset(
    traces: list[_InstructionTrace],
    *,
    input_buffer_addr: int,
    input_required_byte_length: int | None,
    write_loop_addr: int,
) -> int | None:
    buffer_end = None if input_required_byte_length is None else input_buffer_addr + input_required_byte_length
    for trace in traces:
        if trace.inst.offset != write_loop_addr:
            continue
        read_ranges = _memory_read_ranges(trace)
        if not read_ranges:
            continue
        addr, _ = read_ranges[0]
        if addr < input_buffer_addr:
            continue
        if buffer_end is not None and addr >= buffer_end:
            continue
        return addr - input_buffer_addr
    return None


def _infer_backscan_input_consumed_range(
    kb: DiskKb,
    traces: list[_InstructionTrace],
    *,
    input_buffer_addr: int,
    input_required_byte_length: int | None,
    output_byte_length: int | None,
    write_loop_addr: int,
) -> tuple[int | None, int | None]:
    write_index = next((index for index, trace in enumerate(traces) if trace.inst.offset == write_loop_addr), None)
    if write_index is None:
        return None, None
    start_index = max(0, write_index - kb.boot_loader.decode_output_backscan_instructions)
    return _infer_input_consumed_range(
        traces[start_index:write_index],
        input_buffer_addr=input_buffer_addr,
        input_required_byte_length=input_required_byte_length,
        output_byte_length=output_byte_length,
        scan_start_addr=None,
        scan_end_addr=write_loop_addr,
    )


def _infer_sync_skip_bytes(
    traces: list[_InstructionTrace],
    *,
    input_buffer_addr: int,
    sync_word: int | None,
    buffer_scan_addr: int | None,
    write_loop_addr: int,
) -> int:
    if sync_word is None or buffer_scan_addr is None:
        return 0
    for trace in traces:
        if trace.inst.offset < buffer_scan_addr or trace.inst.offset > write_loop_addr:
            continue
        if trace.inst.opcode_text != "cmpi.w":
            continue
        nodes = list(trace.inst.operand_nodes or ())
        if len(nodes) != 2:
            continue
        immediate_node, input_node = nodes
        if immediate_node.kind != "immediate" or immediate_node.value != sync_word:
            continue
        addr = _operand_memory_addr(input_node, trace.pre_cpu, opcode=trace.inst.opcode_text)
        if addr != input_buffer_addr:
            continue
        return _operand_byte_size(trace.inst)
    return 0


def _infer_checksum_gate(
    kb: DiskKb,
    traces: list[_InstructionTrace],
    *,
    write_loop_addr: int,
) -> tuple[int | None, str | None]:
    write_index = next((index for index, trace in enumerate(traces) if trace.inst.offset == write_loop_addr), None)
    if write_index is None:
        return None, None
    start_index = max(0, write_index - kb.boot_loader.decode_output_backscan_instructions)
    for index in range(start_index, write_index - 1):
        trace = traces[index]
        next_trace = traces[index + 1]
        next_opcode = next_trace.inst.opcode_text or ""
        if not next_opcode.startswith(("beq", "bne")):
            continue
        nodes = list(trace.inst.operand_nodes or ())
        if trace.inst.opcode_text == "tst.w" and len(nodes) == 1 and nodes[0].kind == "register":
            return trace.inst.offset, f"tst.w+{next_opcode}"
        if trace.inst.opcode_text == "cmpi.w" and len(nodes) == 2:
            immediate_node = nodes[0]
            if immediate_node.kind == "immediate" and immediate_node.value == 0:
                return trace.inst.offset, f"cmpi.w_zero+{next_opcode}"
    return None, None


def _build_decode_regions(
    kb: DiskKb,
    traces: list[_InstructionTrace],
    disk_reads: list[BootloaderDiskRead],
    read_setups: list[BootloaderReadSetup],
    decode_outputs: list[BootloaderDecodeOutput],
    raw_track_sources: list[RawTrackSource],
    disk_bytes: bytes | None,
) -> list[BootloaderDecodeRegion]:
    regions: list[BootloaderDecodeRegion] = []
    for output in decode_outputs:
        byte_length = None if output.longword_count is None else output.longword_count * 4
        matching_setup = next(
            (
                setup
                for setup in read_setups
                if setup.buffer_scan_addr is not None and setup.buffer_scan_addr <= output.instruction_addr
            ),
            None,
        )
        input_buffer_addr = None if matching_setup is None else matching_setup.buffer_addr
        input_source_kind = "none"
        input_required_source_kind = "none"
        input_source_candidates: list[RawTrackSource] = []
        input_source_candidate_spans: list[RawTrackSourceSpan] = []
        input_required_byte_length = None if matching_setup is None else matching_setup.dma_byte_length
        input_consumed_byte_offset: int | None = None
        input_consumed_byte_length: int | None = None
        checksum_gate_addr: int | None = None
        checksum_gate_kind: str | None = None
        input_concrete_byte_count = 0
        input_complete = False
        input_materializable = False
        input_missing_reason: str | None = None
        if input_buffer_addr is not None and byte_length is not None:
            loop_input_offset = _infer_write_loop_input_offset(
                traces,
                input_buffer_addr=input_buffer_addr,
                input_required_byte_length=input_required_byte_length,
                write_loop_addr=output.write_loop_addr,
            )
            input_consumed_byte_offset, input_consumed_byte_length = _infer_input_consumed_range(
                traces,
                input_buffer_addr=input_buffer_addr,
                input_required_byte_length=input_required_byte_length,
                output_byte_length=byte_length,
                scan_start_addr=output.write_loop_addr,
                scan_end_addr=max(output.instruction_addr, output.write_loop_addr),
            )
            if loop_input_offset is not None:
                input_consumed_byte_offset = loop_input_offset
                input_consumed_byte_length = byte_length
            elif input_consumed_byte_offset is None or input_consumed_byte_length is None:
                input_consumed_byte_offset, input_consumed_byte_length = _infer_backscan_input_consumed_range(
                    kb,
                    traces,
                    input_buffer_addr=input_buffer_addr,
                    input_required_byte_length=input_required_byte_length,
                    output_byte_length=byte_length,
                    write_loop_addr=output.write_loop_addr,
                )
            sync_skip_bytes = _infer_sync_skip_bytes(
                traces,
                input_buffer_addr=input_buffer_addr,
                sync_word=None if matching_setup is None else matching_setup.sync_word,
                buffer_scan_addr=None if matching_setup is None else matching_setup.buffer_scan_addr,
                write_loop_addr=output.write_loop_addr,
            )
            if (
                loop_input_offset is None
                and (
                sync_skip_bytes > 0
                and input_consumed_byte_offset is not None
                and input_consumed_byte_offset < sync_skip_bytes
                )
            ):
                input_consumed_byte_offset = sync_skip_bytes
            checksum_gate_addr, checksum_gate_kind = _infer_checksum_gate(
                kb,
                traces,
                write_loop_addr=output.write_loop_addr,
            )
            matching_disk_read = next(
                (
                    disk_read
                    for disk_read in disk_reads
                    if disk_read.destination_addr <= input_buffer_addr
                    and input_buffer_addr + byte_length <= disk_read.destination_addr + disk_read.byte_length
                ),
                None,
            )
            input_source_kind = "logical_buffer" if matching_disk_read is not None else "custom_track_dma_buffer"
            input_required_source_kind = "logical_disk_bytes" if matching_disk_read is not None else "raw_custom_track_bytes"
            if matching_disk_read is None:
                input_source_candidates = _candidate_track_sources(raw_track_sources, matching_setup)
                if input_required_byte_length is not None:
                    input_source_candidate_spans = _candidate_track_sync_spans(
                        input_source_candidates,
                        input_required_byte_length,
                        None if matching_setup is None else matching_setup.track,
                        None if matching_setup is None else matching_setup.sync_word,
                        disk_bytes,
                    )
            concrete_offsets: set[int] = set()
            for trace in traces:
                for offset in range(byte_length):
                    value = trace.pre_mem.read(input_buffer_addr + offset, "b")
                    if value.is_known:
                        concrete_offsets.add(offset)
            input_concrete_byte_count = len(concrete_offsets)
            input_complete = input_concrete_byte_count == byte_length
            input_materializable = input_complete
            if not input_complete:
                input_missing_reason = (
                        "logical_buffer_bytes_unavailable"
                        if matching_disk_read is not None
                        else (
                            "custom_track_decode_mapping_unresolved"
                            if input_source_candidate_spans
                            else (
                            "custom_track_sync_window_unavailable"
                            if input_source_candidates
                            else "custom_track_source_unavailable"
                        )
                    )
                )
        elif input_buffer_addr is not None:
            input_source_kind = "custom_track_dma_buffer"
            input_required_source_kind = "raw_custom_track_bytes"
            input_source_candidates = _candidate_track_sources(raw_track_sources, matching_setup)
            if input_required_byte_length is not None:
                input_source_candidate_spans = _candidate_track_sync_spans(
                    input_source_candidates,
                    input_required_byte_length,
                    None if matching_setup is None else matching_setup.track,
                    None if matching_setup is None else matching_setup.sync_word,
                    disk_bytes,
                )
            input_missing_reason = "decode_output_length_unknown"
        else:
            input_materializable = True
        regions.append(
            BootloaderDecodeRegion(
                instruction_addr=output.instruction_addr,
                input_buffer_addr=input_buffer_addr,
                input_consumed_byte_offset=input_consumed_byte_offset,
                input_consumed_byte_length=input_consumed_byte_length,
                checksum_gate_addr=checksum_gate_addr,
                checksum_gate_kind=checksum_gate_kind,
                input_source_kind=input_source_kind,
                input_required_source_kind=input_required_source_kind,
                input_source_candidates=input_source_candidates,
                input_source_candidate_spans=input_source_candidate_spans,
                input_required_byte_length=input_required_byte_length,
                input_concrete_byte_count=input_concrete_byte_count,
                input_complete=input_complete,
                input_materializable=input_materializable,
                input_missing_reason=input_missing_reason,
                output_base_addr=output.output_base_addr,
                output_addr=output.output_addr,
                byte_length=byte_length,
                write_loop_addr=output.write_loop_addr,
            )
        )
    return regions


def _build_handoffs(
    traces: list[_InstructionTrace],
    handoff_target: int | None,
    decode_regions: list[BootloaderDecodeRegion],
) -> list[BootloaderHandoff]:
    if handoff_target is None:
        return []
    jumps = [trace for trace in traces if trace.inst.opcode_text == "jmp"]
    if not jumps:
        return []
    source_kind = "direct_jump"
    for region in decode_regions:
        if region.output_base_addr is None:
            continue
        if region.byte_length is None:
            source_kind = "decode_region"
            break
        if region.output_base_addr <= handoff_target < region.output_base_addr + region.byte_length:
            source_kind = "decode_region"
            break
    return [
        BootloaderHandoff(
            instruction_addr=jumps[-1].inst.offset,
            target_addr=handoff_target,
            source_kind=source_kind,
        )
    ]


def _build_derived_regions(
    traces: list[_InstructionTrace],
    decode_regions: list[BootloaderDecodeRegion],
) -> list[BootloaderDerivedRegion]:
    regions: list[BootloaderDerivedRegion] = []
    for region in decode_regions:
        if region.byte_length is None:
            continue
        region_base = region.output_base_addr if region.output_base_addr is not None else region.output_addr
        if region_base is None:
            continue
        concrete_bytes: dict[int, int] = {}
        for trace in traces:
            for offset in range(region.byte_length):
                addr = region_base + offset
                pre_value = trace.pre_mem.read(addr, "b")
                post_value = trace.post_mem.read(addr, "b")
                if post_value.is_known and (
                    not pre_value.is_known or pre_value.concrete != post_value.concrete
                ):
                    concrete_bytes[offset] = post_value.concrete
        complete = len(concrete_bytes) == region.byte_length
        data_hex = None
        if complete:
            data_hex = bytes(concrete_bytes[offset] for offset in range(region.byte_length)).hex()
        if concrete_bytes:
            regions.append(
                BootloaderDerivedRegion(
                    base_addr=region_base,
                    byte_length=region.byte_length,
                    concrete_byte_count=len(concrete_bytes),
                    complete=complete,
                    data_hex=data_hex,
                )
            )
    return regions


def _infer_memory_copies(traces: list[_InstructionTrace]) -> list[BootloaderMemoryCopy]:
    copies: list[BootloaderMemoryCopy] = []
    for index, trace in enumerate(traces):
        inst = trace.inst
        if inst.opcode_text != "move.l":
            continue
        nodes = list(inst.operand_nodes or ())
        if len(nodes) != 2:
            continue
        src_node = nodes[0]
        dst_node = nodes[1]
        if src_node.kind != "postincrement" or dst_node.kind != "postincrement":
            continue
        src_meta = src_node.metadata
        dst_meta = dst_node.metadata
        if not isinstance(src_meta, DecodedBaseRegisterNodeMetadata):
            continue
        if not isinstance(dst_meta, DecodedBaseRegisterNodeMetadata):
            continue
        src_base = _register_value(trace.pre_cpu, src_meta.base_register)
        dst_base = _register_value(trace.pre_cpu, dst_meta.base_register)
        if src_base is None or dst_base is None:
            continue
        count_reg: str | None = None
        if index + 1 < len(traces):
            next_inst = traces[index + 1].inst
            next_nodes = list(next_inst.operand_nodes or ())
            if next_inst.opcode_text == "dbf" and len(next_nodes) == 2 and next_nodes[0].register is not None:
                count_reg = next_nodes[0].register
        if count_reg is None:
            continue
        count_value = _register_value(trace.pre_cpu, count_reg)
        if count_value is None:
            continue
        copies.append(
            BootloaderMemoryCopy(
                instruction_addr=inst.offset,
                source_addr=src_base,
                destination_addr=dst_base,
                byte_length=(count_value + 1) * 4,
            )
        )
    return copies


def _infer_read_setups(
    kb: DiskKb,
    traces: list[_InstructionTrace],
    hardware_accesses: list[BootloaderMemoryAccess],
) -> list[BootloaderReadSetup]:
    relevant_symbols = {"dskpt", "dsklen", "dsksync", "adkcon", "dmacon", kb.boot_loader.cia_port_b_symbol}
    instruction_map = {trace.inst.offset: trace.inst for trace in traces}
    setups: list[BootloaderReadSetup] = []
    current: list[BootloaderMemoryAccess] = []
    floppy_state = _initial_floppy_state(kb)
    for access in sorted(hardware_accesses, key=lambda item: item.instruction_addr):
        if access.symbol == kb.boot_loader.cia_port_b_symbol and access.value is not None:
            floppy_state = _apply_floppy_control_write(kb, floppy_state, access.value)
        if access.symbol not in relevant_symbols:
            if current:
                setup = _finalize_read_setup(kb, current, instruction_map, floppy_state)
                if setup is not None:
                    setups.append(setup)
                current = []
            continue
        if current and access.instruction_addr - current[-1].instruction_addr > kb.boot_loader.hardware_access_group_gap_bytes:
            setup = _finalize_read_setup(kb, current, instruction_map, floppy_state)
            if setup is not None:
                setups.append(setup)
            current = []
        current.append(access)
    if current:
        setup = _finalize_read_setup(kb, current, instruction_map, floppy_state)
        if setup is not None:
            setups.append(setup)
    return setups


def _finalize_read_setup(
    kb: DiskKb,
    accesses: list[BootloaderMemoryAccess],
    instruction_map: dict[int, Instruction],
    floppy_state: _FloppyControlState,
) -> BootloaderReadSetup | None:
    symbols = {access.symbol for access in accesses}
    if "dskpt" not in symbols or "dsklen" not in symbols:
        return None
    buffer_addr = next((access.value for access in accesses if access.symbol == "dskpt"), None)
    sync_word = next((access.value for access in accesses if access.symbol == "dsksync"), None)
    dsklen_value = next((access.value for access in reversed(accesses) if access.symbol == "dsklen"), None)
    dma_byte_length = _decode_dsklen_byte_length(kb, dsklen_value)
    adkcon_values = [access.value for access in accesses if access.symbol == "adkcon" and access.value is not None]
    dmacon_values = [access.value for access in accesses if access.symbol == "dmacon" and access.value is not None]
    last_addr = accesses[-1].instruction_addr
    wait_loop_addr = _infer_wait_loop_addr(kb, last_addr, instruction_map)
    buffer_scan_addr = _infer_buffer_scan_addr(kb, last_addr, instruction_map, sync_word)
    return BootloaderReadSetup(
        instruction_addr=accesses[0].instruction_addr,
        buffer_addr=buffer_addr,
        sync_word=sync_word,
        dsklen_value=dsklen_value,
        dma_byte_length=dma_byte_length,
        drive=floppy_state.drive,
        cylinder=floppy_state.cylinder,
        head=floppy_state.head,
        track=None if floppy_state.drive is None else floppy_state.cylinder * 2 + floppy_state.head,
        adkcon_values=adkcon_values,
        dmacon_values=dmacon_values,
        wait_loop_addr=wait_loop_addr,
        buffer_scan_addr=buffer_scan_addr,
    )


def _decode_dsklen_byte_length(kb: DiskKb, dsklen_value: int | None) -> int | None:
    if dsklen_value is None:
        return None
    length_mask = kb.boot_loader.dsklen_length_mask
    length_unit_bytes = kb.boot_loader.dsklen_length_unit_bytes
    assert isinstance(length_mask, int)
    assert isinstance(length_unit_bytes, int)
    return (dsklen_value & length_mask) * length_unit_bytes


def _candidate_track_sync_spans(
    raw_track_sources: list[RawTrackSource],
    required_byte_length: int,
    required_start_track: int | None,
    sync_word: int | None,
    disk_bytes: bytes | None,
) -> list[RawTrackSourceSpan]:
    if not raw_track_sources or sync_word is None or disk_bytes is None:
        return []
    ordered_sources = sorted(raw_track_sources, key=lambda source: source.track)
    sync_bytes = sync_word.to_bytes(2, byteorder="big")
    spans: list[RawTrackSourceSpan] = []
    for start_index, start_source in enumerate(ordered_sources):
        if required_start_track is not None and start_source.track != required_start_track:
            continue
        track_start = start_source.byte_offset
        track_end = track_start + start_source.byte_length
        track_bytes = disk_bytes[track_start:track_end]
        if len(track_bytes) != start_source.byte_length:
            continue
        sync_offsets = [
            offset
            for offset in range(len(track_bytes) - 1)
            if track_bytes[offset:offset + 2] == sync_bytes
        ]
        for sync_offset in sync_offsets:
            total_bytes = start_source.byte_length - sync_offset
            end_source = start_source
            if total_bytes >= required_byte_length:
                spans.append(
                    RawTrackSourceSpan(
                        start_track=start_source.track,
                        end_track=end_source.track,
                        start_byte_offset=start_source.byte_offset + sync_offset,
                        byte_length=total_bytes,
                    )
                )
                continue
            for next_source in ordered_sources[start_index + 1:]:
                if next_source.track != end_source.track + 1:
                    break
                total_bytes += next_source.byte_length
                end_source = next_source
                if total_bytes >= required_byte_length:
                    spans.append(
                        RawTrackSourceSpan(
                            start_track=start_source.track,
                            end_track=end_source.track,
                            start_byte_offset=start_source.byte_offset + sync_offset,
                            byte_length=total_bytes,
                        )
                    )
                    break
    return spans


def _candidate_track_sources(
    raw_track_sources: list[RawTrackSource],
    read_setup: BootloaderReadSetup | None,
) -> list[RawTrackSource]:
    if read_setup is None or read_setup.track is None:
        return raw_track_sources
    return [source for source in raw_track_sources if source.track >= read_setup.track]


def _initial_floppy_state(kb: DiskKb) -> _FloppyControlState:
    return _FloppyControlState(
        port_value=None,
        drive=None,
        cylinder=kb.boot_loader.initial_cylinder,
        head=kb.boot_loader.initial_head,
        motor_on=None,
        direction_inward=None,
    )


def _apply_floppy_control_write(
    kb: DiskKb,
    state: _FloppyControlState,
    value: int,
) -> _FloppyControlState:
    drive = _selected_drive(kb, value)
    head = (
        kb.boot_loader.side_zero_head
        if value & kb.boot_loader.side_bit_mask == 0
        else kb.boot_loader.side_one_head
    )
    motor_on = _active_low_enabled(value, kb.boot_loader.motor_bit_mask, kb.boot_loader.motor_active_low)
    direction_name = (
        kb.boot_loader.direction_zero_means
        if value & kb.boot_loader.direction_bit_mask == 0
        else kb.boot_loader.direction_one_means
    )
    direction_inward = direction_name == "inward"
    cylinder = state.cylinder
    if _is_step_pulse(kb, state.port_value, value):
        cylinder = max(0, cylinder + (1 if direction_inward else -1))
    return _FloppyControlState(
        port_value=value,
        drive=drive,
        cylinder=cylinder,
        head=head,
        motor_on=motor_on,
        direction_inward=direction_inward,
    )


def _selected_drive(kb: DiskKb, value: int) -> int | None:
    selected_drives = [
        drive
        for drive, mask in sorted(kb.boot_loader.drive_select_masks.items())
        if _active_low_enabled(value, mask, kb.boot_loader.drive_select_active_low)
    ]
    return selected_drives[0] if len(selected_drives) == 1 else None


def _active_low_enabled(value: int, mask: int, active_low: bool) -> bool:
    bit_set = bool(value & mask)
    return not bit_set if active_low else bit_set


def _is_step_pulse(kb: DiskKb, previous_value: int | None, current_value: int) -> bool:
    if previous_value is None:
        return False
    previous_set = bool(previous_value & kb.boot_loader.step_bit_mask)
    current_set = bool(current_value & kb.boot_loader.step_bit_mask)
    if not kb.boot_loader.step_active_low:
        return kb.boot_loader.step_pulse_edge == "rising" and (not previous_set and current_set)
    return kb.boot_loader.step_pulse_edge == "falling" and previous_set and not current_set


def _infer_decode_outputs(kb: DiskKb, traces: list[_InstructionTrace]) -> list[BootloaderDecodeOutput]:
    outputs: list[BootloaderDecodeOutput] = []
    for index, trace in enumerate(traces):
        inst = trace.inst
        if inst.opcode_text != "move.l":
            continue
        nodes = list(inst.operand_nodes or ())
        if len(nodes) != 2:
            continue
        dst_node = nodes[1]
        if dst_node.kind != "postincrement":
            continue
        dst_meta = dst_node.metadata
        if not isinstance(dst_meta, DecodedBaseRegisterNodeMetadata):
            continue
        if dst_meta.base_register != "a1":
            continue
        count_reg: str | None = None
        if index + 1 < len(traces):
            next_inst = traces[index + 1].inst
            next_nodes = list(next_inst.operand_nodes or ())
            if next_inst.opcode_text == "dbf" and len(next_nodes) == 2 and next_nodes[0].register is not None:
                count_reg = next_nodes[0].register
        longword_count = None
        if count_reg is not None:
            count_value = _register_value(trace.pre_cpu, count_reg)
            if count_value is not None:
                longword_count = count_value + 1
        output_addr = None
        output_base_addr = None
        for back_index in range(max(0, index - kb.boot_loader.decode_output_backscan_instructions), index):
            prev_trace = traces[back_index]
            prev_inst = prev_trace.inst
            prev_nodes = list(prev_inst.operand_nodes or ())
            if len(prev_nodes) != 2:
                continue
            prev_src = prev_nodes[0]
            prev_dst = prev_nodes[1]
            if prev_dst.kind != "register" or prev_dst.register != "a1":
                continue
            if prev_inst.opcode_text == "lea" and prev_src.kind == "absolute_target" and prev_src.target is not None:
                output_addr = prev_src.target
                output_base_addr = prev_src.target
                break
            if prev_inst.opcode_text == "movea.l" and prev_src.kind == "register" and prev_src.register is not None:
                reg = prev_src.register
                if reg.startswith("a"):
                    base = _register_value(prev_trace.pre_cpu, reg)
                    if base is not None:
                        output_addr = base
                        output_base_addr = base
                        break
                if reg.startswith("d"):
                    data_value = _register_value(prev_trace.pre_cpu, reg)
                    if data_value is not None:
                        output_addr = data_value
                    for earlier_index in range(
                        max(0, back_index - kb.boot_loader.decode_output_add_base_backscan_instructions),
                        back_index,
                    ):
                        earlier_trace = traces[earlier_index]
                        earlier_inst = earlier_trace.inst
                        if earlier_inst.opcode_text != "add.l":
                            continue
                        earlier_nodes = list(earlier_inst.operand_nodes or ())
                        if len(earlier_nodes) != 2:
                            continue
                        add_src = earlier_nodes[0]
                        add_dst = earlier_nodes[1]
                        if add_dst.kind != "register" or add_dst.register != reg:
                            continue
                        if add_src.kind == "register" and add_src.register is not None and add_src.register.startswith("a"):
                            base = _register_value(earlier_trace.pre_cpu, add_src.register)
                            if base is not None:
                                output_base_addr = base
                                break
                    break
        outputs.append(
            BootloaderDecodeOutput(
                instruction_addr=inst.offset,
                write_loop_addr=inst.offset,
                output_addr=output_addr,
                output_base_addr=output_base_addr,
                longword_count=longword_count,
            )
        )
    return outputs


def _infer_wait_loop_addr(
    kb: DiskKb,
    last_access_addr: int,
    instruction_map: dict[int, Instruction],
) -> int | None:
    for offset in range(last_access_addr + 2, last_access_addr + kb.boot_loader.wait_loop_search_bytes, 2):
        inst = instruction_map.get(offset)
        if inst is None or inst.opcode_text != "tst.w":
            continue
        next_inst = instruction_map.get(offset + inst.size)
        if next_inst is None or next_inst.opcode_text is None or not next_inst.opcode_text.startswith("beq"):
            continue
        target = _branch_target(next_inst)
        if target == offset:
            return offset
    return None


def _infer_buffer_scan_addr(
    kb: DiskKb,
    last_access_addr: int,
    instruction_map: dict[int, Instruction],
    sync_word: int | None,
) -> int | None:
    if sync_word is None:
        return None
    for offset in range(last_access_addr + 2, last_access_addr + kb.boot_loader.buffer_scan_search_bytes, 2):
        inst = instruction_map.get(offset)
        if inst is None or inst.opcode_text != "cmpi.w":
            continue
        nodes = list(inst.operand_nodes or ())
        if len(nodes) != 2:
            continue
        src_node = nodes[0]
        dst_node = nodes[1]
        if src_node.kind != "immediate" or src_node.value != sync_word:
            continue
        if dst_node.kind not in {"postincrement", "indirect"}:
            continue
        return offset
    return None


def analyze_bootloader(
    boot_code: bytes,
    *,
    disk_bytes: bytes | None = None,
    raw_track_sources: list[RawTrackSource] | None = None,
    kb: DiskKb | None = None,
    kb_root: Path = PROJECT_ROOT,
    entry_addr: int | None = None,
) -> BootloaderAnalysis:
    resolved_kb = kb
    if resolved_kb is None:
        resolved_kb = load_disk_kb(kb_root)
    resolved_raw_track_sources = [] if raw_track_sources is None else raw_track_sources
    boot_entry = resolved_kb.boot_loader.entry_offset if entry_addr is None else entry_addr
    boot_cpu, boot_mem = _boot_initial_state()
    stages = [
        _scan_stage(
            resolved_kb,
            boot_code,
            name="boot",
            base_addr=boot_entry,
            entry_addr=boot_entry,
            initial_cpu=boot_cpu,
            initial_mem=boot_mem,
            raw_track_sources=resolved_raw_track_sources,
            disk_bytes=disk_bytes,
        )
    ]
    stage_payloads: list[bytes] = [boot_code]
    inferred_stage_keys = {(stages[0].base_addr, stages[0].entry_addr, stages[0].size)}
    index = 0
    while index < len(stages):
        stage = stages[index]
        stage_payload = stage_payloads[index]
        if disk_bytes is not None and stage.handoff_target is not None:
            matching_load = next(
                (
                    load
                    for load in stage.loads
                    if load.destination_addr == stage.handoff_target
                    and load.disk_offset + load.byte_length <= len(disk_bytes)
                ),
                None,
            )
            if matching_load is not None:
                stage_bytes = disk_bytes[matching_load.disk_offset : matching_load.disk_offset + matching_load.byte_length]
                stage_cpu, stage_mem = _empty_initial_state()
                stages.append(
                    _scan_stage(
                        resolved_kb,
                        stage_bytes,
                        name=f"stage_{len(stages)}",
                        base_addr=matching_load.destination_addr,
                        entry_addr=matching_load.destination_addr,
                        initial_cpu=stage_cpu,
                        initial_mem=stage_mem,
                        raw_track_sources=resolved_raw_track_sources,
                        disk_bytes=disk_bytes,
                    )
                )
                stage_payloads.append(stage_bytes)
                inferred_stage_keys.add((matching_load.destination_addr, matching_load.destination_addr, len(stage_bytes)))
                index += 1
                continue
        matching_copy = next(
            (
                copy
                for copy in stage.memory_copies
                if stage.handoff_target is not None and copy.destination_addr == stage.handoff_target
            ),
            None,
        )
        if matching_copy is not None:
            source_stage_base = stage.base_addr
            source_offset = matching_copy.source_addr - source_stage_base
            if source_offset >= 0 and source_offset < len(stage_payload):
                available_length = len(stage_payload) - source_offset
                copied_bytes = stage_payload[
                    source_offset : source_offset + min(matching_copy.byte_length, available_length)
                ]
                stage_cpu, stage_mem = _empty_initial_state()
                stages.append(
                    _scan_stage(
                        resolved_kb,
                        copied_bytes,
                        name=f"stage_{len(stages)}",
                        base_addr=matching_copy.destination_addr,
                        entry_addr=matching_copy.destination_addr,
                        initial_cpu=stage_cpu,
                        initial_mem=stage_mem,
                        raw_track_sources=resolved_raw_track_sources,
                        disk_bytes=disk_bytes,
                    )
                )
                stage_payloads.append(copied_bytes)
                inferred_stage_keys.add((matching_copy.destination_addr, matching_copy.destination_addr, len(copied_bytes)))
                index += 1
                continue
        index += 1
    return BootloaderAnalysis(
        stages=stages,
        memory_regions=_build_memory_regions(stages),
        transfers=_build_transfers(stages),
    )


def _build_memory_regions(stages: list[BootloaderStage]) -> list[BootloaderMemoryRegion]:
    regions: list[BootloaderMemoryRegion] = []
    for stage in stages:
        regions.append(
            BootloaderMemoryRegion(
                stage_name=stage.name,
                region_kind="stage",
                base_addr=stage.base_addr,
                byte_length=stage.size,
                materialized=stage.materialized,
            )
        )
        for setup in stage.read_setups:
            if setup.buffer_addr is None or setup.dma_byte_length is None:
                continue
            regions.append(
                BootloaderMemoryRegion(
                    stage_name=stage.name,
                    region_kind="dma_buffer",
                    base_addr=setup.buffer_addr,
                    byte_length=setup.dma_byte_length,
                    materialized=False,
                )
            )
        for region in stage.decode_regions:
            decode_base = region.output_base_addr if region.output_base_addr is not None else region.output_addr
            if decode_base is None or region.byte_length is None:
                continue
            regions.append(
                BootloaderMemoryRegion(
                    stage_name=stage.name,
                    region_kind="decode_output",
                    base_addr=decode_base,
                    byte_length=region.byte_length,
                    materialized=region.input_materializable,
                )
            )
        for derived in stage.derived_regions:
            regions.append(
                BootloaderMemoryRegion(
                    stage_name=stage.name,
                    region_kind="derived_output",
                    base_addr=derived.base_addr,
                    byte_length=derived.byte_length,
                    materialized=derived.complete,
                )
            )
    return regions


def _build_transfers(stages: list[BootloaderStage]) -> list[BootloaderTransfer]:
    transfers: list[BootloaderTransfer] = []
    for stage in stages:
        for disk_read in stage.disk_reads:
            transfers.append(
                BootloaderTransfer(
                    stage_name=stage.name,
                    transfer_kind="disk_read",
                    source_kind=disk_read.source_kind,
                    destination_addr=disk_read.destination_addr,
                    byte_length=disk_read.byte_length,
                    disk_offset=disk_read.disk_offset,
                )
            )
        for copy in stage.memory_copies:
            transfers.append(
                BootloaderTransfer(
                    stage_name=stage.name,
                    transfer_kind="memory_copy",
                    source_kind="memory_region",
                    destination_addr=copy.destination_addr,
                    byte_length=copy.byte_length,
                    source_addr=copy.source_addr,
                )
            )
        for region in stage.decode_regions:
            decode_base = region.output_base_addr if region.output_base_addr is not None else region.output_addr
            start_span = region.input_source_candidate_spans[0] if len(region.input_source_candidate_spans) == 1 else None
            transfers.append(
                BootloaderTransfer(
                    stage_name=stage.name,
                    transfer_kind="decode",
                    source_kind=region.input_source_kind,
                    destination_addr=decode_base,
                    byte_length=region.byte_length,
                    input_buffer_addr=region.input_buffer_addr,
                    output_addr=region.output_addr,
                    start_track=None if start_span is None else start_span.start_track,
                    end_track=None if start_span is None else start_span.end_track,
                    start_byte_offset=None if start_span is None else start_span.start_byte_offset,
                    checksum_gate_addr=region.checksum_gate_addr,
                    checksum_gate_kind=region.checksum_gate_kind,
                )
            )
        for handoff in stage.handoffs:
            transfers.append(
                BootloaderTransfer(
                    stage_name=stage.name,
                    transfer_kind="handoff",
                    source_kind=handoff.source_kind,
                    destination_addr=None,
                    byte_length=None,
                    target_addr=handoff.target_addr,
                )
            )
    return transfers
