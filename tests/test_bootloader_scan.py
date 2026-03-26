from __future__ import annotations

from amiga_disk.bootloader import (
    _infer_backscan_input_consumed_range,
    _infer_checksum_gate,
    _infer_input_consumed_range,
    _infer_sync_skip_bytes,
    _infer_write_loop_input_offset,
    _InstructionTrace,
    analyze_bootloader,
)
from amiga_disk.kb import load_disk_kb
from amiga_disk.models import RawTrackSource
from m68k.abstract_values import _concrete
from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble
from m68k.m68k_executor import AbstractMemory, CPUState


def _trace(
    offset: int,
    instruction: str,
    *,
    a1: int | None = None,
    a2: int | None = None,
    d0: int | None = None,
    d1: int | None = None,
) -> _InstructionTrace:
    inst = disassemble(assemble_instruction(instruction, pc=offset), base_offset=offset)[0]
    cpu = CPUState()
    if a1 is not None:
        cpu.set_reg("an", 1, _concrete(a1))
    if a2 is not None:
        cpu.set_reg("an", 2, _concrete(a2))
    if d0 is not None:
        cpu.set_reg("dn", 0, _concrete(d0))
    if d1 is not None:
        cpu.set_reg("dn", 1, _concrete(d1))
    mem = AbstractMemory()
    return _InstructionTrace(
        incoming_source=-1,
        inst=inst,
        pre_cpu=cpu,
        pre_mem=mem,
        post_cpu=cpu.copy(),
        post_mem=mem.copy(),
    )


def _ice_style_boot_code() -> bytes:
    return bytes.fromhex(
        "48E7FFFE"
        "337C0002001C"
        "237C000400000028"
        "237C000054000024"
        "237C00000400002C"
        "4EAEFE38"
        "4EF900040000"
        "4CDF7FFF"
        "4E75"
    )


def _hardware_loader_stage() -> bytes:
    return bytes.fromhex(
        "4DF900DFF000"
        "33FC448900DFF07E"
        "41F900123456"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C9B060024"
        "3D7C9B060024"
        "3D7C82100096"
        "4E75"
    )


def _relocator_stage() -> bytes:
    copied_stage = bytes.fromhex(
        "33FC448900DFF07E"
        "33FC801000DFF024"
        "4E75"
        "4E71"
    )
    relocator = bytes.fromhex(
        "41FA0018"
        "43F900006000"
        "303C0004"
        "22D8"
        "51C8FFFC"
        "4EF900006000"
    )
    return relocator + copied_stage


def _branch_over_data_stage() -> bytes:
    return (
        bytes.fromhex("6008")
        + b"ICEBOOT!"
        + bytes.fromhex("33FC448900DFF07E4E75")
    )


def test_bootloader_scanner_inferrs_stage0_read_and_chases_loaded_stage() -> None:
    kb = load_disk_kb()
    disk = bytearray(0x6000)
    stage1 = _hardware_loader_stage()
    disk[0x400:0x400 + len(stage1)] = stage1

    analysis = analyze_bootloader(
        _ice_style_boot_code(),
        disk_bytes=bytes(disk),
        kb=kb,
    )

    assert len(analysis.stages) == 2
    assert analysis.stages[0].name == "boot"
    assert analysis.stages[0].entry_addr == kb.boot_loader.entry_offset
    assert analysis.stages[0].loads[0].command_name == "CMD_READ"
    assert analysis.stages[0].disk_reads[0].source_kind == "logical_disk_offset"
    assert analysis.stages[0].loads[0].disk_offset == 0x400
    assert analysis.stages[0].loads[0].byte_length == 0x5400
    assert analysis.stages[0].loads[0].destination_addr == 0x40000
    assert analysis.stages[0].handoff_target == 0x40000

    stage1_scan = analysis.stages[1]
    assert stage1_scan.base_addr == 0x40000
    assert [access.symbol for access in stage1_scan.hardware_accesses] == [
        "dsksync",
        "dskpt",
        "adkcon",
        "adkcon",
        "dsklen",
        "dsklen",
        "dmacon",
    ]
    assert stage1_scan.hardware_accesses[1].value == 0x123456
    assert len(stage1_scan.read_setups) == 1
    assert stage1_scan.read_setups[0].buffer_addr == 0x123456
    assert stage1_scan.read_setups[0].sync_word == 0x4489
    assert stage1_scan.read_setups[0].dsklen_value == 0x9B06
    assert stage1_scan.read_setups[0].dma_byte_length == 0x360C
    assert stage1_scan.read_setups[0].adkcon_values == [0x6800, 0x9500]
    assert stage1_scan.read_setups[0].wait_loop_addr is None
    assert stage1_scan.read_setups[0].buffer_scan_addr is None
    assert analysis.transfers[0].transfer_kind == "disk_read"
    assert analysis.transfers[0].disk_offset == 0x400
    assert analysis.transfers[0].destination_addr == 0x40000
    assert any(region.region_kind == "stage" and region.base_addr == 0x40000 for region in analysis.memory_regions)


def test_bootloader_scanner_handles_branch_over_inline_data() -> None:
    kb = load_disk_kb()

    analysis = analyze_bootloader(
        _branch_over_data_stage(),
        kb=kb,
        entry_addr=0,
    )

    assert len(analysis.stages) == 1
    assert analysis.stages[0].reachable_instruction_count == 3
    assert [access.symbol for access in analysis.stages[0].hardware_accesses] == ["dsksync"]


def test_bootloader_scanner_chases_relocator_copy_stage() -> None:
    kb = load_disk_kb()
    disk = bytearray(0x1000)
    relocator = _relocator_stage()
    disk[0x200:0x200 + len(relocator)] = relocator

    boot = bytes.fromhex(
        "48E7FFFE"
        "337C0002001C"
        "237C000400000028"
        "237C0000002E0024"
        "237C00000200002C"
        "4EAEFE38"
        "4EF900040000"
        "4CDF7FFF"
        "4E75"
    )

    analysis = analyze_bootloader(boot, disk_bytes=bytes(disk), kb=kb)

    assert len(analysis.stages) == 3
    assert analysis.stages[1].handoff_target == 0x6000
    assert analysis.stages[1].memory_copies[0].source_addr == 0x4001A
    assert analysis.stages[1].memory_copies[0].destination_addr == 0x6000
    assert analysis.stages[2].base_addr == 0x6000
    assert [access.symbol for access in analysis.stages[2].hardware_accesses] == [
        "dsksync",
        "dsklen",
    ]


def test_bootloader_scanner_inferrs_wait_loop_and_buffer_scan_for_read_setup() -> None:
    kb = load_disk_kb()
    stage = bytes.fromhex(
        "4DF900DFF000"
        "43FA001E"
        "4251"
        "3D7C40000024"
        "41F900002000"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C4489007E"
        "3D7C9B060024"
        "3D7C9B060024"
        "4A51"
        "67FC"
        "4251"
        "45F900002000"
        "700A"
        "0C5A4489"
        "66FA"
        "4E75"
        "0000"
    )

    analysis = analyze_bootloader(stage, kb=kb, entry_addr=0x6000)

    setup = analysis.stages[0].read_setups[0]
    assert setup.buffer_addr == 0x2000
    assert setup.sync_word == 0x4489
    assert setup.dsklen_value == 0x9B06
    assert setup.dma_byte_length == 0x360C
    assert setup.wait_loop_addr == 0x603A
    assert setup.buffer_scan_addr == 0x6048


def test_bootloader_scanner_inferrs_decode_output_region() -> None:
    kb = load_disk_kb()
    stage = bytes.fromhex(
        "4BF900002000"
        "7204"
        "D28D"
        "2241"
        "7003"
        "7401"
        "22C2"
        "51C8FFFC"
        "4EF900002000"
    )

    analysis = analyze_bootloader(stage, kb=kb, entry_addr=0x7000)

    output = analysis.stages[0].decode_outputs[0]
    region = analysis.stages[0].decode_regions[0]
    assert output.output_addr == 0x2004
    assert output.output_base_addr == 0x2000
    assert output.write_loop_addr == 0x7010
    assert output.longword_count == 4
    assert region.input_buffer_addr is None
    assert region.input_source_kind == "none"
    assert region.input_required_source_kind == "none"
    assert region.input_concrete_byte_count == 0
    assert region.input_complete is False
    assert region.input_materializable is True
    assert region.input_missing_reason is None
    assert region.output_base_addr == 0x2000
    assert region.byte_length == 16
    derived = analysis.stages[0].derived_regions[0]
    assert derived.base_addr == 0x2000
    assert derived.byte_length == 16
    assert derived.concrete_byte_count == 12
    assert derived.complete is False
    assert derived.data_hex is None


def test_bootloader_scanner_leaves_decode_handoff_without_synthesizing_stage() -> None:
    kb = load_disk_kb()
    stage = bytes.fromhex(
        "4BF900002000"
        "7204"
        "D28D"
        "2241"
        "7003"
        "7401"
        "22C2"
        "51C8FFFC"
        "4EF900002800"
    )

    analysis = analyze_bootloader(stage, kb=kb, entry_addr=0x7000)

    assert len(analysis.stages) == 1
    assert analysis.stages[0].handoff_target == 0x2800


def test_bootloader_scanner_records_handoff_provenance() -> None:
    kb = load_disk_kb()
    stage = bytes.fromhex(
        "4DF900DFF000"
        "43FA001E"
        "4251"
        "3D7C40000024"
        "41F900002000"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C4489007E"
        "3D7C9B060024"
        "3D7C9B060024"
        "4A51"
        "67FC"
        "4251"
        "45F900002000"
        "700A"
        "0C5A4489"
        "66FA"
        "4EF900002008"
    )

    analysis = analyze_bootloader(stage, kb=kb, entry_addr=0x6000)

    handoff = analysis.stages[0].handoffs[0]
    assert handoff.target_addr == 0x2008
    assert handoff.source_kind == "direct_jump"


def test_bootloader_decode_region_reports_missing_input_concreteness() -> None:
    kb = load_disk_kb()
    read_setup = bytes.fromhex(
        "4DF900DFF000"
        "43FA001E"
        "4251"
        "3D7C40000024"
        "41F900002000"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C4489007E"
        "3D7C9B060024"
        "3D7C9B060024"
        "4A51"
        "67FC"
        "4251"
        "45F900002000"
        "700A"
        "0C5A4489"
        "66FA"
    )
    decode_loop = bytes.fromhex(
        "4BF900003000"
        "7204"
        "D28D"
        "2241"
        "7003"
        "7401"
        "22C2"
        "51C8FFFC"
        "4EF900003000"
    )
    stage = read_setup + decode_loop

    analysis = analyze_bootloader(stage, kb=kb, entry_addr=0x6000)

    region = analysis.stages[0].decode_regions[0]
    assert region.input_buffer_addr == 0x2000
    assert region.input_source_kind == "custom_track_dma_buffer"
    assert region.input_required_source_kind == "raw_custom_track_bytes"
    assert region.input_source_candidates == []
    assert region.input_source_candidate_spans == []
    assert region.input_required_byte_length == 0x360C
    assert region.input_concrete_byte_count == 0
    assert region.input_complete is False
    assert region.input_materializable is False
    assert region.input_missing_reason == "custom_track_source_unavailable"


def test_bootloader_decode_region_links_available_raw_track_sources() -> None:
    kb = load_disk_kb()
    read_setup = bytes.fromhex(
        "4DF900DFF000"
        "43FA001E"
        "4251"
        "3D7C40000024"
        "41F900002000"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C4489007E"
        "3D7C9B060024"
        "3D7C9B060024"
        "4A51"
        "67FC"
        "4251"
        "45F900002000"
        "700A"
        "0C5A4489"
        "66FA"
    )
    decode_loop = bytes.fromhex(
        "4BF900003000"
        "7204"
        "D28D"
        "2241"
        "7003"
        "7401"
        "22C2"
        "51C8FFFC"
        "4EF900003000"
    )
    stage = read_setup + decode_loop

    analysis = analyze_bootloader(
        stage,
        kb=kb,
        entry_addr=0x6000,
        raw_track_sources=[
            RawTrackSource(track=0, cylinder=0, head=0, byte_offset=0, byte_length=5632),
            RawTrackSource(track=1, cylinder=0, head=1, byte_offset=5632, byte_length=5632),
        ],
    )

    region = analysis.stages[0].decode_regions[0]
    assert [source.track for source in region.input_source_candidates] == [0, 1]
    assert region.input_source_candidate_spans == []
    assert region.input_required_byte_length == 0x360C
    assert region.input_missing_reason == "custom_track_sync_window_unavailable"


def test_bootloader_decode_region_builds_candidate_track_spans_when_capacity_exists() -> None:
    kb = load_disk_kb()
    read_setup = bytes.fromhex(
        "4DF900DFF000"
        "43FA001E"
        "4251"
        "3D7C40000024"
        "41F900002000"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C4489007E"
        "3D7C9B060024"
        "3D7C9B060024"
        "4A51"
        "67FC"
        "4251"
        "45F900002000"
        "700A"
        "0C5A4489"
        "66FA"
    )
    decode_loop = bytes.fromhex(
        "4BF900003000"
        "7204"
        "D28D"
        "2241"
        "7003"
        "7401"
        "22C2"
        "51C8FFFC"
        "4EF900003000"
    )

    analysis = analyze_bootloader(
        read_setup + decode_loop,
        kb=kb,
        entry_addr=0x6000,
        disk_bytes=(
            (b"\x00" * 20) + b"\x44\x89" + (b"\x00" * 7978)
            + (b"\x00" * 40) + b"\x44\x89" + (b"\x00" * 7958)
            + (b"\x00" * 8000)
        ),
        raw_track_sources=[
            RawTrackSource(track=10, cylinder=5, head=0, byte_offset=0, byte_length=8000),
            RawTrackSource(track=11, cylinder=5, head=1, byte_offset=8000, byte_length=8000),
            RawTrackSource(track=12, cylinder=6, head=0, byte_offset=16000, byte_length=8000),
        ],
    )

    region = analysis.stages[0].decode_regions[0]
    assert [
        (span.start_track, span.end_track, span.start_byte_offset, span.byte_length)
        for span in region.input_source_candidate_spans
    ] == [
        (10, 11, 20, 15980),
        (11, 12, 8040, 15960),
    ]
    assert region.input_missing_reason == "custom_track_decode_mapping_unresolved"


def test_bootloader_decode_region_uses_sync_offset_when_track_bytes_exist() -> None:
    kb = load_disk_kb()
    read_setup = bytes.fromhex(
        "4DF900DFF000"
        "43FA001E"
        "4251"
        "3D7C40000024"
        "41F900002000"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C4489007E"
        "3D7C9B060024"
        "3D7C9B060024"
        "4A51"
        "67FC"
        "4251"
        "45F900002000"
        "700A"
        "0C5A4489"
        "66FA"
    )
    decode_loop = bytes.fromhex(
        "4BF900003000"
        "7204"
        "D28D"
        "2241"
        "7003"
        "7401"
        "22C2"
        "51C8FFFC"
        "4EF900003000"
    )
    track0 = bytearray(b"\x00" * 8000)
    track1 = bytearray(b"\x00" * 8000)
    track0[100:102] = b"\x44\x89"
    disk_bytes = bytes(track0 + track1)

    analysis = analyze_bootloader(
        read_setup + decode_loop,
        kb=kb,
        entry_addr=0x6000,
        disk_bytes=disk_bytes,
        raw_track_sources=[
            RawTrackSource(track=0, cylinder=0, head=0, byte_offset=0, byte_length=8000),
            RawTrackSource(track=1, cylinder=0, head=1, byte_offset=8000, byte_length=8000),
        ],
    )

    region = analysis.stages[0].decode_regions[0]
    assert [(span.start_track, span.end_track, span.start_byte_offset, span.byte_length) for span in region.input_source_candidate_spans] == [
        (0, 1, 100, 15900)
    ]


def test_write_loop_input_offset_uses_direct_source_pointer() -> None:
    offset = _infer_write_loop_input_offset(
        [_trace(0x605C, "move.l (a2)+,(a1)+", a1=0x3000, a2=0x2000)],
        input_buffer_addr=0x2000,
        input_required_byte_length=0x360C,
        write_loop_addr=0x605C,
    )

    assert offset == 0


def test_sync_skip_bytes_detects_buffer_sync_scan() -> None:
    skip = _infer_sync_skip_bytes(
        [
            _trace(0x6048, "cmpi.w #$4489,(a2)+", a2=0x2000),
            _trace(0x605C, "move.l d1,(a1)+", a1=0x3000, d1=0x01020304),
        ],
        input_buffer_addr=0x2000,
        sync_word=0x4489,
        buffer_scan_addr=0x6048,
        write_loop_addr=0x605C,
    )

    assert skip == 2


def test_backscan_input_consumed_range_tracks_odd_even_deinterleave_reads() -> None:
    kb = load_disk_kb()
    offset, length = _infer_backscan_input_consumed_range(
        kb,
        [
            _trace(0x6056, "move.w (a2)+,d1", a2=0x2002),
            _trace(0x6058, "swap d1", d1=0x01020000),
            _trace(0x605A, "move.w (a2)+,d1", a2=0x2004, d1=0x01020000),
            _trace(0x6062, "move.l d1,(a1)+", a1=0x3000, d1=0x01020304),
        ],
        input_buffer_addr=0x2000,
        input_required_byte_length=0x360C,
        output_byte_length=4,
        write_loop_addr=0x6062,
    )

    assert offset == 2
    assert length == 4


def test_input_consumed_range_tracks_copy_loop_reads() -> None:
    offset, length = _infer_input_consumed_range(
        [
            _trace(0x605C, "move.l (a2)+,(a1)+", a1=0x3000, a2=0x2000),
            _trace(0x605C, "move.l (a2)+,(a1)+", a1=0x3004, a2=0x2004),
            _trace(0x605C, "move.l (a2)+,(a1)+", a1=0x3008, a2=0x2008),
            _trace(0x605C, "move.l (a2)+,(a1)+", a1=0x300C, a2=0x200C),
        ],
        input_buffer_addr=0x2000,
        input_required_byte_length=0x360C,
        output_byte_length=16,
        scan_start_addr=0x605C,
        scan_end_addr=0x605C,
    )

    assert offset == 0
    assert length == 16


def test_checksum_gate_detects_tst_guard_before_write_loop() -> None:
    kb = load_disk_kb()
    gate_addr, gate_kind = _infer_checksum_gate(
        kb,
        [
            _trace(0x6058, "tst.w d2"),
            _trace(0x605A, "beq.s $6062"),
            _trace(0x605C, "move.l d1,(a1)+", a1=0x3000, d1=0x01020304),
        ],
        write_loop_addr=0x605C,
    )

    assert gate_addr == 0x6058
    assert gate_kind == "tst.w+beq.s"


def test_checksum_gate_detects_zero_compare_guard_before_write_loop() -> None:
    kb = load_disk_kb()
    gate_addr, gate_kind = _infer_checksum_gate(
        kb,
        [
            _trace(0x6056, "cmpi.w #0,d2"),
            _trace(0x605A, "bne.s $6062"),
            _trace(0x605C, "move.l d1,(a1)+", a1=0x3000, d1=0x01020304),
        ],
        write_loop_addr=0x605C,
    )

    assert gate_addr == 0x6056
    assert gate_kind == "cmpi.w_zero+bne.s"


def test_bootloader_leaves_ambiguous_multiple_candidate_sync_windows_unmaterialized() -> None:
    kb = load_disk_kb()
    read_setup = bytes.fromhex(
        "4DF900DFF000"
        "43FA001E"
        "4251"
        "3D7C40000024"
        "41F900002000"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C4489007E"
        "3D7C9B060024"
        "3D7C9B060024"
        "4A51"
        "67FC"
    )
    decode_loop = bytes.fromhex(
        "45F900002000"
        "0C5A4489"
        "6612"
        "7000"
        "301A"
        "41F900002004"
        "43F900003000"
        "22D8"
        "51C8FFFC"
        "4EF900003000"
        "4E75"
    )
    # Keep this above the replay budget so the test stays a cheap ambiguity check.
    stage = read_setup + decode_loop + (b"\x4E\x71" * 600)
    track0 = bytearray(b"\x00" * 8000)
    track1 = bytearray(b"\x00" * 8000)
    good_source = bytes.fromhex("448900030102030405060708090A0B0C0D0E0F10")
    bad_source = bytes.fromhex("448900000102030405060708090A0B0C0D0E0F10")
    track0[100:100 + len(good_source)] = good_source
    track0[400:400 + len(bad_source)] = bad_source
    disk_bytes = bytes(track0 + track1)

    analysis = analyze_bootloader(
        stage,
        kb=kb,
        entry_addr=0x6000,
        disk_bytes=disk_bytes,
        raw_track_sources=[
            RawTrackSource(track=0, cylinder=0, head=0, byte_offset=0, byte_length=8000),
            RawTrackSource(track=1, cylinder=0, head=1, byte_offset=8000, byte_length=8000),
        ],
    )

    region = analysis.stages[0].decode_regions[0]
    assert len(region.input_source_candidate_spans) == 2
    assert region.byte_length is None
    assert region.input_complete is False
    assert region.input_concrete_byte_count == 0
    assert region.input_missing_reason == "decode_output_length_unknown"
    assert analysis.stages[0].derived_regions == []
    assert analysis.stages[0].handoff_target == 0x3000


def test_bootloader_read_setup_tracks_floppy_head_and_steps() -> None:
    kb = load_disk_kb()
    stage = bytes.fromhex(
        "13FC00F100BFD100"
        "13FC00F000BFD100"
        "13FC00F100BFD100"
        "4DF900DFF000"
        "43FA001E"
        "4251"
        "3D7C40000024"
        "41F900002000"
        "2D480020"
        "3D7C6800009E"
        "3D7C9500009E"
        "3D7C4489007E"
        "3D7C9B060024"
        "3D7C9B060024"
        "4A51"
        "67FC"
        "4251"
        "45F900002000"
        "700A"
        "0C5A4489"
        "66FA"
        "4BF900003000"
        "7204"
        "D28D"
        "2241"
        "7003"
        "7401"
        "22C2"
        "51C8FFFC"
        "4EF900003000"
    )

    analysis = analyze_bootloader(
        stage,
        kb=kb,
        entry_addr=0x6000,
        disk_bytes=(
            (b"\x00" * 8000)
            + (b"\x00" * 8000)
            + (b"\x00" * 60) + b"\x44\x89" + (b"\x00" * 7938)
            + (b"\x00" * 8000)
        ),
        raw_track_sources=[
            RawTrackSource(track=0, cylinder=0, head=0, byte_offset=0, byte_length=8000),
            RawTrackSource(track=1, cylinder=0, head=1, byte_offset=8000, byte_length=8000),
            RawTrackSource(track=2, cylinder=1, head=0, byte_offset=16000, byte_length=8000),
            RawTrackSource(track=3, cylinder=1, head=1, byte_offset=24000, byte_length=8000),
        ],
    )

    setup = analysis.stages[0].read_setups[0]
    region = analysis.stages[0].decode_regions[0]
    assert setup.drive == 0
    assert setup.cylinder == 1
    assert setup.head == 0
    assert setup.track == 2
    assert [source.track for source in region.input_source_candidates] == [2, 3]
    assert [
        (span.start_track, span.end_track, span.start_byte_offset, span.byte_length)
        for span in region.input_source_candidate_spans
    ] == [
        (2, 3, 16060, 15940)
    ]


def test_bootloader_scanner_records_unresolved_jump_targets_without_crashing() -> None:
    kb = load_disk_kb()

    analysis = analyze_bootloader(
        bytes.fromhex("4EF900123456"),
        kb=kb,
        entry_addr=0,
    )

    assert analysis.stages[0].handoff_target == 0x123456
    assert analysis.stages[0].loads == []
