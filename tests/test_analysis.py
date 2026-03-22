"""Test the shared analysis pipeline (m68k.analysis)."""

import struct
import tempfile
from pathlib import Path

import pytest

from m68k.analysis import (analyze_hunk, HunkAnalysis, AnalysisCacheError,
                           detect_relocated_segments, _postinc_copy_regs,
                           RelocatedSegment)
from m68k.decode_errors import DecodeError
from m68k.hunk_parser import HunkType
from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import disassemble
from m68k.m68k_executor import analyze
from m68k.os_calls import LibraryCall
from m68k_kb import runtime_os
from m68k.ea_extension import parse_full_extension


def _site_view(site):
    return {
        "addr": site.addr,
        "mnemonic": site.mnemonic,
        "flow_type": site.flow_type,
        "shape": site.shape,
        "region": site.region,
        "status": site.status,
        "target": site.target,
        **({"detail": site.detail} if site.detail is not None else {}),
        **({"target_count": site.target_count} if site.target_count is not None else {}),
    }


def _make_simple_hunk():
    """Build a minimal code buffer with known structure for testing."""
    code = b''
    # Entry at $00: lea $10(pc),a0; moveq #0,d0; rts
    code += struct.pack('>HH', 0x41FA, 0x000E)   # [0x00] lea $10(pc),a0
    code += struct.pack('>H', 0x7000)              # [0x04] moveq #0,d0
    code += struct.pack('>H', 0x4E75)              # [0x06] rts
    # Padding
    code += b'\x4e\x71' * 5                        # [0x08..$11] nop
    # Data at $12
    code += struct.pack('>HH', 0x0000, 0x0000)     # [0x12] data
    return code


class _FakeReloc:
    """Minimal reloc object for testing."""
    def __init__(self, reloc_type, offsets):
        self.reloc_type = reloc_type
        self.offsets = offsets


def test_analyze_hunk_returns_dataclass():
    """analyze_hunk returns a HunkAnalysis with expected fields."""
    code = _make_simple_hunk()
    result = analyze_hunk(code, relocs=[], hunk_index=0,
                          print_fn=lambda *a: None)
    assert isinstance(result, HunkAnalysis)
    assert result.code is code
    assert result.hunk_index == 0
    assert isinstance(result.blocks, dict)
    assert isinstance(result.exit_states, dict)
    assert isinstance(result.hint_blocks, dict)
    assert isinstance(result.lib_calls, list)
    assert result.os_kb.STRUCTS
    assert 0 in result.blocks  # entry point block exists


def test_analyze_hunk_finds_blocks():
    """analyze_hunk discovers basic blocks from entry point 0."""
    code = _make_simple_hunk()
    result = analyze_hunk(code, relocs=[], hunk_index=0,
                          print_fn=lambda *a: None)
    # Should have at least the entry block
    assert len(result.blocks) >= 1
    entry_block = result.blocks[0]
    assert len(entry_block.instructions) >= 1


def test_analyze_hunk_propagates_state():
    """analyze_hunk produces exit states with propagated register values."""
    code = _make_simple_hunk()
    result = analyze_hunk(code, relocs=[], hunk_index=0,
                          print_fn=lambda *a: None)
    assert len(result.exit_states) > 0
    # Entry block exit state should have D0=0 (from moveq #0,d0)
    cpu, _ = result.exit_states[0]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 0


def test_analyze_hunk_identifies_os_calls():
    """analyze_hunk's os_kb is populated from the OS knowledge base."""
    code = _make_simple_hunk()
    result = analyze_hunk(code, relocs=[], hunk_index=0,
                          print_fn=lambda *a: None)
    assert result.os_kb.STRUCTS
    assert result.os_kb.META.calling_convention.base_reg == "A6"


def test_analyze_hunk_defers_per_caller_until_cheap_resolution_stabilizes(monkeypatch):
    code = _make_simple_hunk()
    real_runtime = []
    real_per_caller = []

    def fake_runtime(*args, **kwargs):
        real_runtime.append(1)
        if len(real_runtime) == 1:
            from m68k.indirect_analysis import IndirectResolution
            from m68k.indirect_core import IndirectSiteStatus
            return [IndirectResolution(target=4, source_addr=0,
                                       kind=IndirectSiteStatus.RUNTIME)]
        return []

    def fake_per_caller(*args, **kwargs):
        real_per_caller.append(1)
        return []

    monkeypatch.setattr("m68k.analysis.detect_jump_tables", lambda *a, **k: [])
    monkeypatch.setattr("m68k.analysis._prune_inline_dispatch_blocks", lambda *a, **k: None)
    monkeypatch.setattr("m68k.analysis.resolve_indirect_targets", fake_runtime)
    monkeypatch.setattr("m68k.analysis.resolve_backward_slice", lambda *a, **k: [])
    monkeypatch.setattr("m68k.analysis.resolve_per_caller", fake_per_caller)

    analyze_hunk(code, relocs=[], hunk_index=0, print_fn=lambda *a: None)

    assert len(real_runtime) >= 2
    assert len(real_per_caller) == 1


def test_analyze_hunk_skips_preclassified_external_sites_in_per_caller(monkeypatch):
    code = _make_simple_hunk()
    seen_skip_sets = []

    def fake_per_caller(*args, **kwargs):
        seen_skip_sets.append(kwargs["skip_site_addrs"])
        return []

    monkeypatch.setattr("m68k.analysis.detect_jump_tables", lambda *a, **k: [])
    monkeypatch.setattr("m68k.analysis._prune_inline_dispatch_blocks", lambda *a, **k: None)
    monkeypatch.setattr("m68k.analysis.resolve_indirect_targets", lambda *a, **k: [])
    monkeypatch.setattr("m68k.analysis.resolve_backward_slice", lambda *a, **k: [])
    monkeypatch.setattr("m68k.analysis.identify_library_calls", lambda *a, **k: [
        LibraryCall(addr=4, block=0, library="exec.library",
                    function="FindTask", lvo=-294)
    ])
    monkeypatch.setattr("m68k.analysis.refine_opened_base_calls", lambda *a, **k: a[1])
    monkeypatch.setattr("m68k.analysis.resolve_per_caller", fake_per_caller)

    analyze_hunk(code, relocs=[], hunk_index=0, print_fn=lambda *a: None)

    assert seen_skip_sets == [frozenset({4})]


def test_save_load_roundtrip():
    """HunkAnalysis can be saved and loaded with identical data."""
    code = _make_simple_hunk()
    ha = analyze_hunk(code, relocs=[], hunk_index=0,
                      print_fn=lambda *a: None)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.analysis"
        ha.save(path)
        assert path.exists()
        assert path.stat().st_size > 0

        ha2 = HunkAnalysis.load(path, ha.os_kb)
        assert len(ha2.blocks) == len(ha.blocks)
        assert len(ha2.exit_states) == len(ha.exit_states)
        assert ha2.hunk_index == ha.hunk_index
        assert ha2.code == ha.code
        assert ha2.call_targets == ha.call_targets
        assert ha2.os_kb is ha.os_kb  # re-attached, same object


def test_load_rejects_wrong_version():
    """Loading a cache with mismatched version raises AnalysisCacheError."""
    import pickle
    code = _make_simple_hunk()
    ha = analyze_hunk(code, relocs=[], hunk_index=0,
                      print_fn=lambda *a: None)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.analysis"
        # Save normally first, then tamper with version
        ha.save(path)
        with open(path, "rb") as f:
            _, saved_ha = pickle.load(f)
        with open(path, "wb") as f:
            pickle.dump((999, saved_ha), f)
        import pytest
        with pytest.raises(AnalysisCacheError, match="version mismatch"):
            HunkAnalysis.load(path, {})


def test_base_addr_resolves_absolute_targets():
    """Analysis with non-zero base_addr resolves absolute branch targets.

    Models Bloodwych: code runs at $0400, uses absolute addresses.
    BSR $0410 should discover the subroutine at file offset $10
    (which maps to runtime address $0410 with base_addr=$0400).
    """
    code = b''
    # $0400: bsr.w $0410
    # BSR.W: PC=$0402, disp=$000E, target=$0402+$000E=$0410
    code += struct.pack('>HH', 0x6100, 0x000E)
    # $0404: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $0406: rts
    code += struct.pack('>H', 0x4E75)
    # padding
    code += struct.pack('>HHHH', 0x4E71, 0x4E71, 0x4E71, 0x4E71)
    # $0410: sub at file offset $10
    code += struct.pack('>H', 0x7000)  # moveq #0,d0
    code += struct.pack('>H', 0x4E75)  # rts

    base = 0x0400
    ha = analyze_hunk(code, [], base_addr=base)

    # Subroutine at $0410 should be discovered
    assert 0x0410 in ha.call_targets, (
        f"Expected call target $0410, got {sorted(hex(t) for t in ha.call_targets)}")
    # Block at $0410 should have exit state
    assert 0x0410 in ha.blocks, (
        f"Expected block at $0410, got {sorted(hex(a) for a in ha.blocks)[:10]}")


def test_base_addr_with_code_start():
    """Analysis with code_start skips bootstrap prefix.

    Models Bloodwych: first $5C bytes are bootstrap (copy loop),
    real code starts at file offset $5C running at address $0400.
    """
    bootstrap = b'\x4e\x71' * 10  # 20 bytes of NOP (fake bootstrap)
    real_code = b''
    # $0400 (file offset $14): moveq #1,d0
    real_code += struct.pack('>H', 0x7001)
    # $0402: rts
    real_code += struct.pack('>H', 0x4E75)

    full_data = bootstrap + real_code
    base = 0x0400
    code_start = len(bootstrap)

    ha = analyze_hunk(full_data, [], base_addr=base,
                      code_start=code_start)

    # Entry block should be at $0400 (not $0000)
    assert base in ha.blocks, (
        f"Expected block at ${base:04X}, got {sorted(hex(a) for a in ha.blocks)[:10]}")
    # Should have exit state with D0=1
    assert base in ha.exit_states
    cpu, _ = ha.exit_states[base]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 1


def test_analyze_skips_invalid_full_extension_words():
    result = analyze(bytes.fromhex("20312100"), propagate=False, entry_points=[0])

    assert result["blocks"] == {}


def test_analyze_hunk_promotes_code_pointer_args_into_core_entries(monkeypatch):
    code = b""
    code += struct.pack(">HH", 0x4BFA, 0x0008)  # lea $0c(pc),a5
    code += struct.pack(">HH", 0x6100, 0x0008)  # bsr.w $0e
    code += struct.pack(">H", 0x4E75)           # rts
    code += struct.pack(">HH", 0x7000, 0x4E73)  # moveq #0,d0 ; rte
    code += struct.pack(">H", 0x4E75)           # dispatcher rts

    lib_call = LibraryCall(
        addr=0x04,
        block=0x00,
        library="exec.library",
        function="Supervisor",
        lvo=-30,
        inputs=(
            runtime_os.OsInput(
                name="userFunction",
                reg="A5",
                type="void *",
                semantic_kind="code_ptr",
            ),
        ),
    )

    monkeypatch.setattr("m68k.analysis.identify_library_calls", lambda *a, **k: [lib_call])
    monkeypatch.setattr("m68k.analysis.refine_opened_base_calls", lambda *a, **k: a[1])

    ha = analyze_hunk(code, relocs=[], hunk_index=0, print_fn=lambda *a: None)

    assert 0x0A in ha.blocks


def test_parse_full_extension_raises_decode_error_for_reserved_shape():
    with pytest.raises(DecodeError, match="Reserved full extension BD SIZE value"):
        parse_full_extension(
            0x2100,
            b"",
            0,
            base_register="a0",
            pc_offset=None,
        )


def test_analyze_hunk_prunes_inline_dispatch_speculative_blocks():
    code = b''
    code += struct.pack('>H', 0x7000)          # [0x00] moveq #0,d0
    code += struct.pack('>HH', 0x4EFB, 0x0000)  # [0x02] jmp 0(pc,d0.w)
    code += struct.pack('>H', 0x6006)          # [0x06] bra.s $0e
    code += struct.pack('>H', 0x6008)          # [0x08] bra.s $12
    code += struct.pack('>H', 0x600A)          # [0x0a] bra.s $16
    code += struct.pack('>H', 0x4E71)          # [0x0c] nop
    code += struct.pack('>HH', 0x4E71, 0x4E75)  # [0x0e] handler 0
    code += struct.pack('>HH', 0x4E71, 0x4E75)  # [0x12] handler 1
    code += struct.pack('>HH', 0x4E71, 0x4E75)  # [0x16] handler 2

    result = analyze_hunk(code, relocs=[], hunk_index=0, print_fn=lambda *a: None)

    assert any(t.pattern == "pc_inline_dispatch" for t in result.jump_tables)
    assert 0x04 not in result.blocks
    assert 0x0E in result.blocks
    assert 0x12 in result.blocks
    assert 0x16 in result.blocks


def test_analyze_hunk_reports_unresolved_indirect_sites():
    code = b""
    code += struct.pack(">H", 0x4E90)  # jsr (a0)
    code += struct.pack(">H", 0x4E75)  # rts
    lines = []

    result = analyze_hunk(
        code,
        relocs=[],
        hunk_index=0,
        print_fn=lambda line: lines.append(line),
    )

    assert [_site_view(site) for site in result.indirect_sites] == [{
        "addr": 0,
        "mnemonic": "JSR",
        "flow_type": "call",
        "shape": "ind",
        "region": "core",
        "status": "unresolved",
        "target": None,
    }]
    assert any("Indirects: 1 sites (1 core_unresolved)" in line for line in lines)
    assert any("unresolved_indirect_core $0000: JSR ind" in line for line in lines)


def test_analyze_hunk_reports_terminal_indirect_site_offset_not_block_start(monkeypatch):
    code = b""
    pc = 0
    for text in (
            "movea.l d0,a6",
            "jsr -2(a6)",
            "rts"):
        raw = assemble_instruction(text, pc=pc)
        code += raw
        pc += len(raw)

    monkeypatch.setattr(
        "m68k.analysis.identify_library_calls",
        lambda *args, **kwargs: [],
    )

    result = analyze_hunk(
        code,
        relocs=[],
        hunk_index=0,
        print_fn=lambda *_: None,
    )

    assert [_site_view(site) for site in result.indirect_sites] == [{
        "addr": 0x2,
        "mnemonic": "JSR",
        "flow_type": "call",
        "shape": "disp",
        "region": "core",
        "status": "unresolved",
        "target": None,
    }]


def test_analyze_hunk_marks_identified_library_call_as_external(monkeypatch):
    code = b""
    pc = 0
    for text in (
            "movea.l d0,a6",
            "jsr -2(a6)",
            "rts"):
        raw = assemble_instruction(text, pc=pc)
        code += raw
        pc += len(raw)

    monkeypatch.setattr(
        "m68k.analysis.identify_library_calls",
        lambda *args, **kwargs: [LibraryCall(
            addr=0x2,
            block=0x0,
            library="exec.library",
            function="AllocMem",
            lvo=-2,
        )],
    )

    result = analyze_hunk(
        code,
        relocs=[],
        hunk_index=0,
        print_fn=lambda *_: None,
    )

    assert [_site_view(site) for site in result.indirect_sites] == [{
        "addr": 0x2,
        "mnemonic": "JSR",
        "flow_type": "call",
        "shape": "disp",
        "region": "core",
        "status": "external",
        "detail": "exec.library::AllocMem",
        "target": None,
    }]


def test_analyze_hunk_core_per_caller_does_not_promote_hint_only_target(monkeypatch):
    monkeypatch.setattr("m68k.analysis.scan_and_score", lambda *args, **kwargs: [])

    code = b""
    code += struct.pack(">HH", 0x45FA, 0x000C)          # [0x00] lea $0c(pc),a2 -> $0e
    code += struct.pack(">HH", 0x6100, 0x0004)          # [0x04] bsr.w $0a
    code += struct.pack(">H", 0x4E75)                   # [0x08] rts
    code += struct.pack(">H", 0x4E92)                   # [0x0a] jsr (a2)
    code += struct.pack(">H", 0x4E75)                   # [0x0c] rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)         # [0x0e] core handler
    code += struct.pack(">HH", 0x45FA, 0x0008)         # [0x12] lea $08(pc),a2 -> $1c
    code += struct.pack(">HH", 0x6100, 0xFFF2)         # [0x16] bsr.w $0a
    code += struct.pack(">H", 0x4E75)                   # [0x1a] rts
    code += struct.pack(">HH", 0x4E71, 0x4E75)         # [0x1c] hint-only handler
    code += struct.pack(">I", 0x00000012)               # [0x20] reloc target -> hint caller

    relocs = [_FakeReloc(HunkType.HUNK_RELOC32, [0x20])]
    result = analyze_hunk(code, relocs=relocs, hunk_index=0,
                          print_fn=lambda *a: None)

    assert 0x0A in result.blocks
    assert 0x0E in result.blocks
    assert 0x12 in result.hint_blocks
    assert 0x1C not in result.blocks
    assert {
        "addr": 0x0A,
        "mnemonic": "JSR",
        "flow_type": "call",
        "shape": "ind",
        "region": "core",
        "status": "runtime",
        "target": 0x0E,
    } in [_site_view(site) for site in result.indirect_sites]


# -- Auto-detect relocated segments -----------------------------------

def test_detect_copy_and_jump():
    """Detect copy loop followed by JMP to destination.

    Bootstrap:
        $00: lea     $1C(pc),a6     ; source = $1E
        $04: lea     $0400,a0       ; dest = $0400
        $0A: moveq   #9,d0          ; 10 bytes
    loop:
        $0C: move.b  (a6)+,(a0)+    ; copy
        $0E: dbf     d0,loop
        $12: jmp     $0400           ; enter payload
    payload ($1E in file, runs at $0400):
        $1E: moveq   #42,d0
        $20: rts
    """
    code = b''
    # $00: lea $1C(pc),a6 -> a6 = $02 + $1C = $1E
    code += struct.pack('>HH', 0x4DFA, 0x001C)
    # $04: lea $0400,a0
    code += struct.pack('>HHH', 0x41F9, 0x0000, 0x0400)
    # $0A: moveq #9,d0
    code += struct.pack('>H', 0x7009)
    # $0C: move.b (a6)+,(a0)+
    code += struct.pack('>H', 0x10DE)
    # $0E: dbf d0,$0C (disp = $0C - $10 = -4)
    code += struct.pack('>HH', 0x51C8, 0xFFFC)
    # $12: jmp $0400
    code += struct.pack('>HHH', 0x4EF9, 0x0000, 0x0400)
    # padding to $1E
    code += struct.pack('>HH', 0x4E71, 0x4E71)
    # $1E: payload
    code += struct.pack('>H', 0x702A)  # moveq #42,d0
    code += struct.pack('>H', 0x4E75)  # rts

    segments = detect_relocated_segments(code)
    assert len(segments) >= 1, (
        f"Expected at least 1 relocated segment, got {segments}")
    seg = segments[0]
    assert seg.file_offset == 0x1E, (
        f"Expected file_offset=$1E, got ${seg.file_offset:X}")
    assert seg.base_addr == 0x400, (
        f"Expected base_addr=$400, got ${seg.base_addr:X}")


def test_detect_no_copy_returns_empty():
    """Normal hunk (no copy pattern) returns no relocated segments."""
    code = b''
    code += struct.pack('>H', 0x7000)  # moveq #0,d0
    code += struct.pack('>H', 0x4E75)  # rts

    segments = detect_relocated_segments(code)
    assert segments == []


def test_detect_relocated_segments_skips_analysis_without_bootstrap_signature(monkeypatch):
    code = struct.pack(">HH", 0x7000, 0x4E75)

    def _unexpected_analyze(*args, **kwargs):
        raise AssertionError("plain code should not trigger relocation analysis")

    monkeypatch.setattr("m68k.analysis.analyze", _unexpected_analyze)

    assert detect_relocated_segments(code) == []


def test_postinc_copy_detection_uses_decoded_operands_not_text():
    inst = disassemble(assemble_instruction("move.b (a6)+,(a0)+"))[0]
    inst.text = "corrupted"

    assert _postinc_copy_regs(inst) == (6, 0)


def _make_relocated_hunk():
    """Build a minimal relocated binary: bootstrap + payload.

    File layout:
        $00-$17: bootstrap (LEA source, LEA dest, copy loop, JMP $0400)
        $18-$1B: padding (NOP)
        $1C-$1F: payload source (moveq #42,d0; rts)

    Runtime layout (after bootstrap copies payload):
        $0400: moveq #42,d0  (copied from file $1C)
        $0402: rts
    """
    code = b''
    # $00: lea $1A(pc),a6 -> a6 = $02 + $1A = $1C (payload source)
    code += struct.pack('>HH', 0x4DFA, 0x001A)
    # $04: lea $0400,a0  (dest)
    code += struct.pack('>HHH', 0x41F9, 0x0000, 0x0400)
    # $0A: moveq #3,d0  (4 bytes: DBF loops 4 times)
    code += struct.pack('>H', 0x7003)
    # $0C: move.b (a6)+,(a0)+
    code += struct.pack('>H', 0x10DE)
    # $0E: dbf d0,$0C
    code += struct.pack('>HH', 0x51C8, 0xFFFC)
    # $12: jmp $0400
    code += struct.pack('>HHH', 0x4EF9, 0x0000, 0x0400)
    # padding to $1C
    code += struct.pack('>HH', 0x4E71, 0x4E71)
    # $1C: payload bytes (copied to $0400 at runtime)
    code += struct.pack('>H', 0x702A)  # moveq #42,d0
    code += struct.pack('>H', 0x4E75)  # rts
    return code


def test_payload_at_runtime_address():
    """Payload blocks are at runtime addresses, not file offsets.

    The bootstrap copies the payload from file offset $1C to runtime
    address $0400.  The analysis must use base_addr=$0400 for the
    payload so that absolute address references in the code naturally
    match block/label addresses.
    """
    code = _make_relocated_hunk()
    ha = analyze_hunk(code, [])

    # Bootstrap at $00 should be analyzed (at file offsets)
    assert 0 in ha.blocks, (
        f"Bootstrap block at $0000 missing, "
        f"got {sorted(hex(a) for a in ha.blocks)[:10]}")
    # Payload should be at runtime address $0400 (not file offset $1C)
    assert 0x0400 in ha.blocks, (
        f"Payload block at $0400 missing, "
        f"got {sorted(hex(a) for a in ha.blocks)[:10]}")
    assert 0x1C not in ha.blocks, (
        f"Payload should NOT be at file offset $001C")
    # The payload block should contain moveq #42
    if 0x0400 in ha.exit_states:
        cpu, _ = ha.exit_states[0x0400]
        assert cpu.d[0].is_known and cpu.d[0].concrete == 42, (
            f"D0 at $0400 should be 42 (payload), got {cpu.d[0]}")


def _make_two_stage_relocated_hunk():
    """Build a two-stage relocated binary (models Bloodwych's bootstrap).

    Stage 1 (bootstrap $00-$1F):
        Copy trap handler stub from $20 to $90, set A6 to payload
        source ($34), TRAP #0 (flow-terminating).

    Stage 2 (trap handler, file offset $20, runs at $90):
        Copy payload from A6 ($34) to $0400, JMP $0400.

    Payload (file offset $34):
        moveq #42,d0; rts

    Key: the payload at $34 is only reachable via the TWO-STAGE
    copy (bootstrap sets A6, handler uses A6).  Unlike the simple
    case where the copy source IS the secondary entry, here $34
    is the file_offset but NOT a secondary entry - $20 is.
    """
    code = b''
    # $00: lea $1E(pc),a0 -> a0 = $02 + $1E = $20 (handler source)
    code += struct.pack('>HH', 0x41FA, 0x001E)
    # $04: lea $90,a1 -> a1 = $90 (handler dest)
    code += struct.pack('>HHH', 0x43F9, 0x0000, 0x0090)
    # $0A: moveq #19,d0 -> copy 20 bytes
    code += struct.pack('>H', 0x7013)
    # $0C: move.b (a0)+,(a1)+
    code += struct.pack('>H', 0x12D8)
    # $0E: dbf d0,$0C (disp = $0C - $10 = -4)
    code += struct.pack('>HH', 0x51C8, 0xFFFC)
    # $12: lea $20(pc),a6 -> a6 = $14 + $20 = $34 (payload source)
    code += struct.pack('>HH', 0x4DFA, 0x0020)
    # $16: nop padding (8 bytes, replaces trap vector setup)
    code += struct.pack('>HHHH', 0x4E71, 0x4E71, 0x4E71, 0x4E71)
    # $1E: trap #0
    code += struct.pack('>H', 0x4E40)
    # -- handler source ($20, 20 bytes, runs at $90) --
    # $20: lea $0400,a0
    code += struct.pack('>HHH', 0x41F9, 0x0000, 0x0400)
    # $26: moveq #3,d0 (4 bytes)
    code += struct.pack('>H', 0x7003)
    # $28: move.b (a6)+,(a0)+
    code += struct.pack('>H', 0x10DE)
    # $2A: dbf d0,$28 (disp = $28 - $2C = -4)
    code += struct.pack('>HH', 0x51C8, 0xFFFC)
    # $2E: jmp $0400
    code += struct.pack('>HHH', 0x4EF9, 0x0000, 0x0400)
    # -- payload source ($34) --
    # $34: moveq #42,d0
    code += struct.pack('>H', 0x702A)
    # $36: rts
    code += struct.pack('>H', 0x4E75)
    return code  # 56 bytes ($38)


def test_payload_at_runtime_two_stage():
    """Two-stage relocation: payload at runtime address.

    In the Bloodwych pattern (bootstrap -> TRAP -> handler copies
    payload), the payload starts at runtime address $0400.  The
    handler at $20 (secondary entry) stays at file offsets.
    """
    code = _make_two_stage_relocated_hunk()
    ha = analyze_hunk(code, [])

    segs = detect_relocated_segments(code)
    assert len(segs) >= 1
    assert segs[0].file_offset == 0x34
    assert segs[0].base_addr == 0x400

    # Payload at runtime address $0400
    assert 0x0400 in ha.blocks, (
        f"Payload block at $0400 missing, "
        f"got core={sorted(hex(a) for a in ha.blocks)}")
    assert 0x34 not in ha.blocks, (
        f"Payload should NOT be at file offset $0034")


def test_secondary_entries_are_core():
    """Secondary entries (handler stubs) stay at file offsets.

    The handler at $20 is in the bootstrap region (before the
    payload file_offset).  It should be analyzed as core at its
    file offset, not at a runtime address.
    """
    code = _make_two_stage_relocated_hunk()
    ha = analyze_hunk(code, [])

    # Handler at $20 should be core (file offset, in bootstrap region)
    assert 0x20 in ha.blocks, (
        f"Handler at $0020 should be a core block, "
        f"got core={sorted(hex(a) for a in ha.blocks)}")

    # Handler's JMP $0400 should connect to the payload block
    assert 0x0400 in ha.blocks, (
        f"Payload at $0400 (handler's JMP target) should be core")


def _assert_no_hint_core_overlap(ha):
    """Assert no hint block overlaps any core block byte range."""
    core_addrs = set()
    for blk in ha.blocks.values():
        for a in range(blk.start, blk.end):
            core_addrs.add(a)
    for addr, hb in ha.hint_blocks.items():
        for a in range(hb.start, hb.end):
            assert a not in core_addrs, (
                f"Hint block ${addr:04X} ({hb.start:X}-{hb.end:X}) "
                f"overlaps with core at ${a:04X}")


def test_hint_blocks_no_core_overlap():
    """Hint blocks must not overlap with core blocks.

    The overlap filter in analyze_hunk removes hints that span into
    core block ranges.  Verify for both single-stage and two-stage
    relocated binaries (two-stage has more gap regions where the
    hint scanner may produce overlapping blocks).
    """
    _assert_no_hint_core_overlap(analyze_hunk(_make_relocated_hunk(), []))
    _assert_no_hint_core_overlap(
        analyze_hunk(_make_two_stage_relocated_hunk(), []))


def test_relocated_segments_stored():
    """HunkAnalysis stores relocated segment info for gen_disasm."""
    code = _make_relocated_hunk()
    ha = analyze_hunk(code, [])

    assert hasattr(ha, 'relocated_segments'), (
        "HunkAnalysis must have relocated_segments field")
    assert len(ha.relocated_segments) == 1
    seg = ha.relocated_segments[0]
    assert seg.file_offset == 0x1C
    assert seg.base_addr == 0x0400


def test_non_relocated_has_empty_segments():
    """Non-relocated hunk has empty relocated_segments."""
    code = _make_simple_hunk()
    ha = analyze_hunk(code, [])

    assert hasattr(ha, 'relocated_segments')
    assert ha.relocated_segments == []
