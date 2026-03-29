from __future__ import annotations

"""Tests for the shared disassembly session/row pipeline."""

import io
import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from _pytest.monkeypatch import MonkeyPatch

from disasm import cli as gen_disasm_mod
from disasm import data_render as data_render_mod
from disasm import emitter as emitter_mod
from disasm import session as session_mod
from disasm.amiga_metadata import ResidentAutoinitMetadata
from disasm.analysis_loader import (
    analysis_cache_root,
    hunk_analysis_cache_path,
    load_hunk_analysis,
)
from disasm.api import listing_window_payload, serialize_row, session_metadata
from disasm.binary_source import RawBinarySource
from disasm.comments import build_instruction_comment_parts, render_comment_parts
from disasm.emitter import emit_session_rows, render_session_text
from disasm.entities import infer_target_name, load_entities
from disasm.entry_seeds import build_entry_seed_config
from disasm.hint_validation import (
    hint_block_has_supported_terminal_flow,
    is_valid_hint_block,
)
from disasm.instruction_rows import render_instruction_text
from disasm.jump_tables import emit_jump_table_rows
from disasm.metadata import build_hunk_metadata
from disasm.os_include_kb import load_os_include_kb
from disasm.session import (
    _apply_seeded_code_annotations,
    _prepare_hunk_code,
    _prepare_hunk_sizes,
    _refresh_library_call_signatures,
    build_disassembly_session,
)
from disasm.substitutions import build_arg_substitutions, build_lvo_substitutions
from disasm.target_metadata import (
    BootBlockTargetMetadata,
    CustomStructFieldMetadata,
    CustomStructMetadata,
    EntryRegisterSeedMetadata,
    LibraryTargetMetadata,
    ResidentTargetMetadata,
    SeededCodeEntrypointMetadata,
    SeededCodeLabelMetadata,
    StructuredRegionSpec,
    TargetMetadata,
    effective_entry_register_seeds,
    target_structure_spec,
)
from disasm.text import listing_window, render_rows
from disasm.typed_data_streams import (
    decode_stream_by_name,
    format_typed_data_stream_command,
)
from disasm.types import (
    AddressRowContext,
    DisasmBlockLike,
    DisassemblySession,
    HunkDisassemblySession,
    JumpTableEntryRef,
    JumpTableRegion,
    ListingRow,
    SemanticOperand,
    StructFieldOperandMetadata,
    TypedDataFieldInfo,
)
from disasm.validation import get_instruction_processor_min, has_valid_branch_target
from m68k.analysis import RelocatedSegment, RelocLike
from m68k.hunk_parser import Hunk, HunkType, MemType, Reloc
from m68k.indirect_core import IndirectSite, IndirectSiteRegion, IndirectSiteStatus
from m68k.jump_tables import JumpTable, JumpTableEntry, JumpTablePattern
from m68k.m68k_asm import assemble_instruction
from m68k.m68k_disasm import Instruction, disassemble
from m68k.m68k_executor import BasicBlock, XRef
from m68k.memory_provenance import (
    MemoryRegionAddressSpace,
    MemoryRegionProvenance,
    provenance_named_base,
)
from m68k.os_calls import (
    AppBaseInfo,
    AppBaseKind,
    CallArgumentAnnotation,
    LibraryBaseTag,
    LibraryCall,
    TypedMemoryRegion,
    analyze_call_setups,
    build_app_slot_symbols,
    build_target_local_os_kb,
)
from m68k_kb import runtime_m68k_analysis, runtime_os
from tests.os_kb_helpers import make_empty_os_kb
from tests.platform_helpers import make_platform
from tests.runtime_kb_helpers import load_canonical_os_kb

_OS_INCLUDE_KB = load_os_include_kb()


@dataclass
class _FakeBlock:
    start: int
    end: int
    successors: tuple[int, ...]
    instructions: list[Instruction]
    predecessors: tuple[int, ...] = ()
    xrefs: list[XRef] = field(default_factory=list)
    is_entry: bool = False
    is_return: bool = False


def test_os_include_kb_contains_device_include_mappings() -> None:
    assert _OS_INCLUDE_KB.library_lvo_owners["timer.device"].include_path == "devices/timer.i"
    assert _OS_INCLUDE_KB.library_lvo_owners["console.device"].include_path == "devices/console.i"


def test_os_include_kb_loads_from_main_os_reference() -> None:
    payload = load_canonical_os_kb()
    assert "library_lvo_owners" in payload["_meta"]
    assert "exec.library" in payload["_meta"]["library_lvo_owners"]


@dataclass
class _FakeReloc:
    reloc_type: HunkType
    offsets: tuple[int, ...]
    target_hunk: int = 0


def _block(start: int = 0, end: int = 1) -> DisasmBlockLike:
    return _FakeBlock(start=start, end=end, successors=(), instructions=[])


def _instruction(*, offset: int, raw: bytes, mnemonic: str, operand_size: str, operand_texts: tuple[str, ...]) -> Instruction:
    return Instruction(
        offset=offset,
        size=len(raw),
        opcode=int.from_bytes(raw[:2], byteorder="big"),
        text=mnemonic,
        raw=raw,
        opcode_text=mnemonic,
        kb_mnemonic=mnemonic,
        operand_size=operand_size,
        operand_texts=operand_texts,
    )


def test_load_entities_reads_jsonl(tmp_path: Path) -> None:
    entities_path = tmp_path / "entities.jsonl"
    entities_path.write_text(
        '{"addr":"0000","type":"code"}\n'
        '\n'
        '{"addr":"0010","type":"data"}\n',
        encoding="utf-8",
    )

    assert load_entities(entities_path) == [
        {"addr": "0000", "type": "code"},
        {"addr": "0010", "type": "data"},
    ]


def test_infer_target_name_prefers_target_dir(tmp_path: Path) -> None:
    target_dir = tmp_path / "demo"
    entities_path = target_dir / "entities.jsonl"

    assert infer_target_name(target_dir, entities_path) == "demo"


def test_infer_target_name_falls_back_to_entities_parent(tmp_path: Path) -> None:
    entities_path = tmp_path / "demo" / "entities.jsonl"

    assert infer_target_name(None, entities_path) == "demo"


def test_apply_seeded_code_annotations_adds_labels_and_notes() -> None:
    labels: dict[int, str] = {}
    comments: dict[int, str] = {}
    metadata = TargetMetadata(
        target_type="program",
        entry_register_seeds=(),
        seeded_code_labels=(
            SeededCodeLabelMetadata(
                addr=0x10,
                name="named_label",
                hunk=0,
                comment="seeded note",
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="demo",
            ),
        ),
        seeded_code_entrypoints=(
            SeededCodeEntrypointMetadata(
                addr=0x20,
                name="entry_name",
                hunk=0,
                role="input routine",
                comment="seeded comment",
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="demo",
            ),
        ),
    )

    _apply_seeded_code_annotations(
        target_metadata=metadata,
        hunk_index=0,
        code_size=0x40,
        labels=labels,
        addr_comments=comments,
    )

    assert labels == {0x10: "named_label", 0x20: "entry_name"}
    assert comments == {0x10: "seeded note", 0x20: "input routine: seeded comment"}


def test_apply_seeded_code_annotations_rejects_out_of_bounds_label() -> None:
    metadata = TargetMetadata(
        target_type="program",
        entry_register_seeds=(),
        seeded_code_labels=(
            SeededCodeLabelMetadata(
                addr=0x40,
                name="named_label",
                hunk=0,
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="demo",
            ),
        ),
    )

    with pytest.raises(ValueError, match="Seeded code label 0x40 lies outside code size 0x40"):
        _apply_seeded_code_annotations(
            target_metadata=metadata,
            hunk_index=0,
            code_size=0x40,
            labels={},
            addr_comments={},
        )


def test_build_lvo_substitutions_collects_direct_jsr_substitution() -> None:
    call = LibraryCall(
        addr=0x20,
        block=0x20,
        library="dos.library",
        function="OpenLibrary",
        lvo=-552,
    )

    lvo_equs, lvo_substitutions = build_lvo_substitutions(
        blocks={},
        lib_calls=[call],
        hunk_entities=[],
    )

    assert lvo_equs == {"dos.library": {-552: "_LVOOpenLibrary"}}
    assert lvo_substitutions == {0x20: ("-552(", "_LVOOpenLibrary(")}


def test_build_lvo_substitutions_collects_dispatch_call_lvo_from_call_site() -> None:
    setter = Instruction(
        offset=0x12,
        size=2,
        opcode=0x70E2,
        text="corrupted",
        raw=b"\x70\xe2",
        kb_mnemonic="moveq",
        operand_size="l",
        operand_texts=("#-30", "d0"),
    )
    call_inst = Instruction(
        offset=0x14,
        size=4,
        opcode=0x6100,
        text="corrupted",
        raw=b"\x61\x00\x00\x2a",
        kb_mnemonic="bsr",
        operand_size="w",
        operand_texts=("$0040",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()

    lvo_equs, lvo_substitutions = build_lvo_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x14,
            block=0x10,
            library="dos.library",
            function="Open",
            lvo=-30,
            dispatch=0x42,
        )],
        hunk_entities=[{"addr": "0040", "end": "0050", "type": "code"}],
    )

    assert lvo_equs == {"dos.library": {-30: "_LVOOpen"}}
    assert lvo_substitutions == {0x12: ("#-30", "#_LVOOpen")}


def test_build_arg_substitutions_collects_immediate_constant() -> None:
    setter = Instruction(
        offset=0x10,
        size=4,
        opcode=0x7001,
        text="corrupted",
        raw=b"\x70\x01",
        kb_mnemonic="moveq",
        operand_size="l",
        operand_texts=("#1", "d0"),
    )
    block = type("Block", (), {
        "instructions": [
            setter,
            Instruction(
                offset=0x20,
                size=2,
                opcode=0x4E75,
                text="jsr     _LVOOpenLibrary(a6)",
                raw=b"\x4E\x75",
                kb_mnemonic="jsr",
                operand_size="w",
                operand_texts=("_LVOOpenLibrary(a6)",),
            ),
        ]
    })()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},
            library_lvo_owners={},
        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"OpenLibrary": {"name": "test.openlibrary.name"}}},
        VALUE_DOMAINS={"test.openlibrary.name": runtime_os.OsValueDomain(kind="enum", members=("OL_TAG",), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={"OL_TAG": runtime_os.OsConstant(raw="1", value=1)},
        LIBRARIES={
            "dos.library": runtime_os.OsLibrary(
                lvo_index={},
                functions={
                    "OpenLibrary": runtime_os.OsFunction(
                        lvo=-552,
                        inputs=(runtime_os.OsInput(name="name", regs=("d0",)),),
                    )
                },
            )
        },
    )

    arg_equs, arg_substitutions = build_arg_substitutions(
        blocks={0x20: block},
        hunk_entities=[],
        lib_calls=[LibraryCall(
            addr=0x20,
            block=0x20,
            library="dos.library",
            function="OpenLibrary",
            lvo=-552,
        )],
        os_kb=os_kb,
    )

    assert arg_equs == {"OL_TAG": 1}
    assert arg_substitutions == {0x10: ("#1", "#OL_TAG")}


def test_build_arg_substitutions_collects_dispatch_call_constant() -> None:
    setter = Instruction(
        offset=0x12,
        size=2,
        opcode=0x76FF,
        text="corrupted",
        raw=b"\x76\xff",
        kb_mnemonic="moveq",
        operand_size="l",
        operand_texts=("#-1", "d3"),
    )
    branch = Instruction(
        offset=0x16,
        size=4,
        opcode=0x6100,
        text="bsr.w   $40",
        raw=b"\x61\x00\x00\x28",
        kb_mnemonic="bsr",
        operand_size="w",
        operand_texts=("$40",),
    )
    block = type("Block", (), {
        "instructions": [
            Instruction(
                offset=0x10,
                size=2,
                opcode=0x2F03,
                text="move.l  d3,-(sp)",
                raw=b"\x2f\x03",
                kb_mnemonic="move",
                operand_size="l",
                operand_texts=("d3", "-(sp)"),
            ),
            setter,
            Instruction(
                offset=0x14,
                size=2,
                opcode=0x70BE,
                text="moveq   #-66,d0",
                raw=b"\x70\xbe",
                kb_mnemonic="moveq",
                operand_size="l",
                operand_texts=("#-66", "d0"),
            ),
            branch,
        ]
    })()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},
            library_lvo_owners={},
        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"Seek": {"mode": "test.seek.mode"}}},
        VALUE_DOMAINS={"test.seek.mode": runtime_os.OsValueDomain(kind="enum", members=("OFFSET_BEGINNING", "OFFSET_CURRENT"), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={
            "OFFSET_BEGINNING": runtime_os.OsConstant(raw="-1", value=-1),
            "OFFSET_CURRENT": runtime_os.OsConstant(raw="0", value=0),
        },
        LIBRARIES={
            "dos.library": runtime_os.OsLibrary(
                lvo_index={},
                functions={
                    "Seek": runtime_os.OsFunction(
                        lvo=-66,
                        inputs=(
                            runtime_os.OsInput(name="arg1", regs=("d1",)),
                            runtime_os.OsInput(name="arg2", regs=("d2",)),
                            runtime_os.OsInput(name="mode", regs=("d3",)),
                        ),
                    )
                },
            )
        },
    )

    arg_equs, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x10,
            block=0x10,
            library="dos.library",
            function="Seek",
            lvo=-66,
            dispatch=0x42,
        )],
        hunk_entities=[{"addr": "0040", "end": "0050", "type": "code"}],
        os_kb=os_kb,
    )

    assert arg_equs == {"OFFSET_BEGINNING": -1}
    assert arg_substitutions == {0x12: ("#-1", "#OFFSET_BEGINNING")}


def test_build_arg_substitutions_collects_long_immediate_constant() -> None:
    setter = _instruction(
        offset=0x10,
        raw=b"\x22\x3c\x00\x00\x10\x00",
        mnemonic="move",
        operand_size="l",
        operand_texts=("#$1000", "d1"),
    )
    call_inst = _instruction(
        offset=0x16,
        raw=b"\x4e\x75",
        mnemonic="jsr",
        operand_size="w",
        operand_texts=("_LVOSetSignal(a6)",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},
            library_lvo_owners={},
        ),
        API_INPUT_VALUE_DOMAINS={"exec.library": {"SetSignal": {"signalMask": "test.exec.signal_mask"}}},
        VALUE_DOMAINS={"test.exec.signal_mask": runtime_os.OsValueDomain(kind="flags", members=("SIGBREAKF_CTRL_C",), zero_name=None, exact_match_policy="error", composition="bit_or", remainder_policy="error")},
        CONSTANTS={
            "SIGBREAKF_CTRL_C": runtime_os.OsConstant(raw="(1<<12)", value=0x1000),
        },
        LIBRARIES={
            "exec.library": runtime_os.OsLibrary(
                lvo_index={},
                functions={
                    "SetSignal": runtime_os.OsFunction(
                        lvo=-306,
                        inputs=(
                            runtime_os.OsInput(name="newSignals", regs=("d0",)),
                            runtime_os.OsInput(name="signalMask", regs=("d1",)),
                        ),
                    )
                },
            )
        },
    )

    arg_equs, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x16,
            block=0x10,
            library="exec.library",
            function="SetSignal",
            lvo=-306,
            dispatch=None,
        )],
        hunk_entities=[],
        os_kb=os_kb,
    )

    assert arg_equs == {"SIGBREAKF_CTRL_C": 0x1000}
    assert arg_substitutions == {0x10: ("#$1000", "#SIGBREAKF_CTRL_C")}


def test_build_arg_substitutions_collects_open_mode_constant() -> None:
    setter = _instruction(
        offset=0x10,
        raw=b"\x24\x3c\x00\x00\x03\xed",
        mnemonic="move",
        operand_size="l",
        operand_texts=("#$3ed", "d2"),
    )
    call_inst = _instruction(
        offset=0x12,
        raw=b"\x4e\x75",
        mnemonic="jsr",
        operand_size="w",
        operand_texts=("_LVOOpen(a6)",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},
            library_lvo_owners={},
        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"Open": {"accessMode": "test.open.access_mode"}}},
        VALUE_DOMAINS={"test.open.access_mode": runtime_os.OsValueDomain(kind="enum", members=("MODE_OLDFILE", "MODE_NEWFILE", "MODE_READWRITE"), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={
            "MODE_OLDFILE": runtime_os.OsConstant(raw="1005", value=0x3ED),
            "MODE_NEWFILE": runtime_os.OsConstant(raw="1006", value=0x3EE),
            "MODE_READWRITE": runtime_os.OsConstant(raw="1004", value=0x3EC),
        },
        LIBRARIES={
            "dos.library": runtime_os.OsLibrary(
                lvo_index={},
                functions={
                    "Open": runtime_os.OsFunction(
                        lvo=-30,
                        inputs=(
                            runtime_os.OsInput(name="name", regs=("d1",)),
                            runtime_os.OsInput(name="accessMode", regs=("d2",)),
                        ),
                    )
                },
            )
        },
    )

    arg_equs, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x12,
            block=0x10,
            library="dos.library",
            function="Open",
            lvo=-30,
            dispatch=None,
        )],
        hunk_entities=[],
        os_kb=os_kb,
    )

    assert arg_equs == {"MODE_OLDFILE": 0x3ED}
    assert arg_substitutions == {0x10: ("#$3ed", "#MODE_OLDFILE")}


def test_build_arg_substitutions_collects_composed_flag_constants() -> None:
    setter = _instruction(
        offset=0x10,
        raw=b"\x22\x3c\x00\x00\x00\x03",
        mnemonic="move",
        operand_size="l",
        operand_texts=("#3", "d1"),
    )
    call_inst = _instruction(
        offset=0x16,
        raw=b"\x4e\x75",
        mnemonic="jsr",
        operand_size="w",
        operand_texts=("_LVOAllocMem(a6)",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},
            library_lvo_owners={},
        ),
        API_INPUT_VALUE_DOMAINS={"exec.library": {"AllocMem": {"attributes": "test.alloc.attributes"}}},
        VALUE_DOMAINS={
            "test.alloc.attributes": runtime_os.OsValueDomain(
                kind="flags",
                members=("MEMF_PUBLIC", "MEMF_CHIP", "MEMF_FAST"),
                zero_name=None,
                exact_match_policy="error",
                composition="bit_or",
                remainder_policy="error",
            )
        },
        CONSTANTS={
            "MEMF_PUBLIC": runtime_os.OsConstant(raw="(1<<0)", value=0x1),
            "MEMF_CHIP": runtime_os.OsConstant(raw="(1<<1)", value=0x2),
            "MEMF_FAST": runtime_os.OsConstant(raw="(1<<2)", value=0x4),
        },
        LIBRARIES={
            "exec.library": runtime_os.OsLibrary(
                lvo_index={},
                functions={
                    "AllocMem": runtime_os.OsFunction(
                        lvo=-198,
                        inputs=(
                            runtime_os.OsInput(name="byteSize", regs=("d0",)),
                            runtime_os.OsInput(name="attributes", regs=("d1",)),
                        ),
                    )
                },
            )
        },
    )

    arg_equs, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x16,
            block=0x10,
            library="exec.library",
            function="AllocMem",
            lvo=-198,
            dispatch=None,
        )],
        hunk_entities=[],
        os_kb=os_kb,
    )

    assert arg_equs == {"MEMF_PUBLIC": 0x1, "MEMF_CHIP": 0x2}
    assert arg_substitutions == {0x10: ("#3", "#MEMF_PUBLIC|MEMF_CHIP")}


def test_build_arg_substitutions_collects_availmem_flag_constants() -> None:
    setter = _instruction(
        offset=0x10,
        raw=b"\x22\x3c\x00\x02\x00\x01",
        mnemonic="move",
        operand_size="l",
        operand_texts=("#$20001", "d1"),
    )
    call_inst = _instruction(
        offset=0x16,
        raw=b"\x4e\x75",
        mnemonic="jsr",
        operand_size="w",
        operand_texts=("_LVOAvailMem(a6)",),
    )
    block = type("Block", (), {"instructions": [setter, call_inst]})()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},
            library_lvo_owners={},
        ),
        API_INPUT_VALUE_DOMAINS={"exec.library": {"AvailMem": {"attributes": "test.alloc.attributes"}}},
        VALUE_DOMAINS={
            "test.alloc.attributes": runtime_os.OsValueDomain(
                kind="flags",
                members=("MEMF_PUBLIC", "MEMF_LARGEST"),
                zero_name=None,
                exact_match_policy="error",
                composition="bit_or",
                remainder_policy="error",
            )
        },
        CONSTANTS={
            "MEMF_PUBLIC": runtime_os.OsConstant(raw="(1<<0)", value=0x1),
            "MEMF_LARGEST": runtime_os.OsConstant(raw="(1<<17)", value=0x20000),
        },
        LIBRARIES={
            "exec.library": runtime_os.OsLibrary(
                lvo_index={},
                functions={
                    "AvailMem": runtime_os.OsFunction(
                        lvo=-216,
                        inputs=(runtime_os.OsInput(name="attributes", regs=("d1",)),),
                    )
                },
            )
        },
    )

    arg_equs, arg_substitutions = build_arg_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x16,
            block=0x10,
            library="exec.library",
            function="AvailMem",
            lvo=-216,
            dispatch=None,
        )],
        hunk_entities=[],
        os_kb=os_kb,
    )

    assert arg_equs == {"MEMF_PUBLIC": 0x1, "MEMF_LARGEST": 0x20000}
    assert arg_substitutions == {0x10: ("#$20001", "#MEMF_PUBLIC|MEMF_LARGEST")}


def test_build_arg_substitutions_requires_declared_constant() -> None:
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},
            library_lvo_owners={},
        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"OpenLibrary": {"name": "test.openlibrary.name"}}},
        VALUE_DOMAINS={"test.openlibrary.name": runtime_os.OsValueDomain(kind="enum", members=("OL_TAG",), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={},
        LIBRARIES={},
    )

    with pytest.raises(KeyError, match="Missing constant OL_TAG"):
        build_arg_substitutions(
            blocks={},
            hunk_entities=[],
            lib_calls=[],
            os_kb=os_kb,
        )


def test_build_arg_substitutions_requires_concrete_constant_value() -> None:
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},
            library_lvo_owners={},
        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"OpenLibrary": {"name": "test.openlibrary.name"}}},
        VALUE_DOMAINS={"test.openlibrary.name": runtime_os.OsValueDomain(kind="enum", members=("OL_TAG",), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={"OL_TAG": runtime_os.OsConstant(raw="TAG_USER+1", value=None)},
        LIBRARIES={},
    )

    with pytest.raises(ValueError, match="Non-concrete constant OL_TAG"):
        build_arg_substitutions(
            blocks={},
            hunk_entities=[],
            lib_calls=[],
            os_kb=os_kb,
        )


def test_build_arg_substitutions_rejects_ambiguous_matched_function_domain_value() -> None:
    setter = Instruction(
        offset=0x10,
        size=2,
        opcode=0x76FF,
        text="corrupted",
        raw=b"\x76\xff",
        kb_mnemonic="moveq",
        operand_size="l",
        operand_texts=("#-1", "d3"),
    )
    block = type("Block", (), {
        "instructions": [
            setter,
            Instruction(
                offset=0x20,
                size=2,
                opcode=0x4E75,
                text="jsr     _LVOSeek(a6)",
                raw=b"\x4E\x75",
                kb_mnemonic="jsr",
                operand_size="w",
                operand_texts=("_LVOSeek(a6)",),
            ),
        ]
    })()
    os_kb = SimpleNamespace(
        META=runtime_os.OsMeta(
            calling_convention=runtime_os.META.calling_convention,
            exec_base_addr=runtime_os.META.exec_base_addr,
            absolute_symbols=(),
            lvo_slot_size=runtime_os.META.lvo_slot_size,
            named_base_structs={},
            library_lvo_owners={},
        ),
        API_INPUT_VALUE_DOMAINS={"dos.library": {"Seek": {"mode": "test.seek.mode"}}},
        VALUE_DOMAINS={"test.seek.mode": runtime_os.OsValueDomain(kind="enum", members=("OFFSET_BEGINNING", "OFFSET_ALIAS"), zero_name=None, exact_match_policy="error", composition=None, remainder_policy=None)},
        CONSTANTS={
            "OFFSET_BEGINNING": runtime_os.OsConstant(raw="-1", value=-1),
            "OFFSET_ALIAS": runtime_os.OsConstant(raw="-1", value=-1),
        },
        LIBRARIES={
            "dos.library": runtime_os.OsLibrary(
                lvo_index={},
                functions={
                    "Seek": runtime_os.OsFunction(
                        lvo=-66,
                        inputs=(runtime_os.OsInput(name="mode", regs=("d3",)),),
                    )
                },
            )
        },
    )

    with pytest.raises(ValueError, match="Input domain resolution failed for Seek.mode"):
        build_arg_substitutions(
            blocks={0x20: block},
            hunk_entities=[],
            lib_calls=[LibraryCall(
                addr=0x20,
                block=0x20,
                library="dos.library",
                function="Seek",
                lvo=-66,
            )],
            os_kb=os_kb,
        )


def test_build_lvo_substitutions_collects_dispatch_call_lvo_constant() -> None:
    branch = Instruction(
        offset=0x16,
        size=4,
        opcode=0x6100,
        text="bsr.w   $40",
        raw=b"\x61\x00\x00\x28",
        kb_mnemonic="bsr",
        operand_size="w",
        operand_texts=("$40",),
    )
    block = type("Block", (), {
        "instructions": [
            Instruction(
                offset=0x12,
                size=2,
                opcode=0x70BE,
                text="moveq   #-66,d0",
                raw=b"\x70\xbe",
                kb_mnemonic="moveq",
                operand_size="l",
                operand_texts=("#-66", "d0"),
            ),
            branch,
        ]
    })()

    lvo_equs, lvo_substitutions = build_lvo_substitutions(
        blocks={0x10: block},
        lib_calls=[LibraryCall(
            addr=0x10,
            block=0x10,
            library="dos.library",
            function="Seek",
            lvo=-66,
            dispatch=0x42,
        )],
        hunk_entities=[{"addr": "0040", "end": "0050", "type": "code"}],
    )

    assert lvo_equs == {"dos.library": {-66: "_LVOSeek"}}
    assert lvo_substitutions == {0x12: ("#-66", "#_LVOSeek")}


def test_build_app_slot_symbols_prefers_initial_mem_and_typed_slots() -> None:
    class FakeInitMem:
        _tags = {
            (0x1020, 4): LibraryBaseTag(library_base="dos.library"),
        }

        def iter_tags(self) -> tuple[tuple[tuple[int, int], object], ...]:
            return tuple(self._tags.items())

    app_offsets = build_app_slot_symbols(
        blocks={},
        lib_calls=[],
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0x1000), initial_mem=FakeInitMem()),
    )

    assert app_offsets == {0x20: "app_dos_base"}


def test_build_app_slot_symbols_ignores_non_app_relative_library_tags_for_dynamic_base() -> None:
    class FakeInitMem:
        _tags = {
            (0x02C00CD8, 4): LibraryBaseTag(library_base="dos.library"),
            (0x03700CD8, 4): LibraryBaseTag(library_base="dos.library"),
            (0x04200CD8, 4): LibraryBaseTag(library_base="dos.library"),
            (0x80300CD8, 4): LibraryBaseTag(library_base="dos.library"),
        }

        def iter_tags(self) -> tuple[tuple[tuple[int, int], object], ...]:
            return tuple(self._tags.items())

    app_offsets = build_app_slot_symbols(
        blocks={},
        lib_calls=[],
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0x80300002), initial_mem=FakeInitMem()),
    )

    assert app_offsets == {0x0CD6: "app_dos_base"}


def test_build_app_slot_symbols_accepts_only_signed_word_slots_for_absolute_base() -> None:
    class FakeInitMem:
        _tags = {
            (0x00007FFC, 4): LibraryBaseTag(library_base="dos.library"),
            (0x00010000, 4): LibraryBaseTag(library_base="dos.library"),
        }

        def iter_tags(self) -> tuple[tuple[tuple[int, int], object], ...]:
            return tuple(self._tags.items())

    app_offsets = build_app_slot_symbols(
        blocks={},
        lib_calls=[],
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=AppBaseInfo(
            kind=AppBaseKind.ABSOLUTE,
            reg_num=6,
            concrete=0x00008000,
        ), initial_mem=FakeInitMem()),
    )

    assert app_offsets == {-4: "app_dos_base"}


def test_build_app_slot_symbols_disambiguates_duplicate_typed_slot_names() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="timer.device",
            function="GetSysTime",
            lvo=-66,
            inputs=(runtime_os.OsInput(name="dest", regs=("A0",), type="struct timeval *", i_struct="TIMEVAL"),),
        ),
        LibraryCall(
            addr=12,
            block=8,
            library="timer.device",
            function="GetSysTime",
            lvo=-66,
            inputs=(runtime_os.OsInput(name="dest", regs=("A0",), type="struct timeval *", i_struct="TIMEVAL"),),
        ),
        LibraryCall(
            addr=22,
            block=16,
            library="timer.device",
            function="SubTime",
            lvo=-48,
            inputs=(
                runtime_os.OsInput(name="dest", regs=("A0",), type="struct timeval *", i_struct="TIMEVAL"),
                runtime_os.OsInput(name="src", regs=("A1",), type="struct timeval *", i_struct="TIMEVAL"),
            ),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41EE, text="lea 4264(a6),a0", raw=b"\x41\xEE\x10\xA8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
        8: type("Block", (), {"instructions": [
            Instruction(offset=8, size=4, opcode=0x41EE, text="lea 4272(a6),a0", raw=b"\x41\xEE\x10\xB0",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=12, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
        16: type("Block", (), {"instructions": [
            Instruction(offset=16, size=4, opcode=0x41EE, text="lea 4272(a6),a0", raw=b"\x41\xEE\x10\xB0",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=20, size=4, opcode=0x43EE, text="lea 4264(a6),a1", raw=b"\x43\xEE\x10\xA8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=22, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0)),
    )

    assert app_offsets == {
        0x10A8: "app_subtime_src",
        0x10B0: "app_subtime_dest",
    }


def test_build_app_slot_symbols_prefers_backward_usage_name_for_single_slot() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="dos.library",
            function="Output",
            lvo=-60,
            output=runtime_os.OsOutput(name="file", reg="D0", type="BPTR"),
        ),
        LibraryCall(
            addr=12,
            block=8,
            library="dos.library",
            function="Write",
            lvo=-48,
            inputs=(runtime_os.OsInput(name="file", regs=("D1",), type="BPTR"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
            Instruction(offset=6, size=4, opcode=0x2D40, text="move.l d0,4264(a6)", raw=b"\x2D\x40\x10\xA8",
                        kb_mnemonic="MOVE", operand_size="l"),
        ]})(),
        8: type("Block", (), {"instructions": [
            Instruction(offset=8, size=4, opcode=0x222E, text="move.l 4264(a6),d1", raw=b"\x22\x2E\x10\xA8",
                        kb_mnemonic="MOVE", operand_size="l"),
            Instruction(offset=12, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }
    blocks[0].xrefs = []
    blocks[8].xrefs = []

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0)),
    )

    assert app_offsets == {
        0x10A8: "app_write_file",
    }


def test_build_app_slot_symbols_preserves_first_equal_priority_usage() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="exec.library",
            function="OpenDevice",
            lvo=-444,
            inputs=(runtime_os.OsInput(name="ioRequest", regs=("A1",), type="struct IORequest *", i_struct="IO"),),
        ),
        LibraryCall(
            addr=12,
            block=8,
            library="exec.library",
            function="CloseDevice",
            lvo=-450,
            inputs=(runtime_os.OsInput(name="ioRequest", regs=("A1",), type="struct IORequest *", i_struct="IO"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x43EE, text="lea 4280(a6),a1", raw=b"\x43\xEE\x10\xB8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
        8: type("Block", (), {"instructions": [
            Instruction(offset=8, size=4, opcode=0x43EE, text="lea 4280(a6),a1", raw=b"\x43\xEE\x10\xB8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=12, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0)),
    )

    assert app_offsets == {
        0x10B8: "app_opendevice_iorequest",
    }


def test_build_app_slot_symbols_prefers_named_base_identity_for_struct_slot() -> None:
    code = (
        b"\x41\xFA\x00\x08"
        + b"\x43\xEE\x10\xB8"
        + b"\x4E\x75"
        + b"timer.device\x00"
    )
    lib_calls = [
        LibraryCall(
            addr=8,
            block=0,
            library="exec.library",
            function="OpenDevice",
            lvo=-444,
            inputs=(
                runtime_os.OsInput(name="devName", regs=("A0",), type="STRPTR"),
                runtime_os.OsInput(name="ioRequest", regs=("A1",), type="struct IORequest *", i_struct="IO"),
            ),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41FA, text="lea 8(pc),a0", raw=b"\x41\xFA\x00\x08",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=4, opcode=0x43EE, text="lea 4280(a6),a1", raw=b"\x43\xEE\x10\xB8",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=8, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=code,
        os_kb=runtime_os,
        platform=make_platform(app_base=(6, 0)),
    )

    assert app_offsets == {
        0x10B8: "app_timer_device_iorequest",
    }


def test_build_app_slot_symbols_for_absolute_app_base_disambiguates_by_absolute_address() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="exec.library",
            function="OpenLibrary",
            lvo=-552,
            output=runtime_os.OsOutput(name="library", reg="D0", type="struct Library *", i_struct="LIBRARY"),
        ),
        LibraryCall(
            addr=12,
            block=8,
            library="exec.library",
            function="OpenLibrary",
            lvo=-552,
            output=runtime_os.OsOutput(name="library", reg="D0", type="struct Library *", i_struct="LIBRARY"),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
            Instruction(offset=6, size=4, opcode=0x2D40, text="move.l d0,-32768(a6)", raw=b"\x2D\x40\x80\x00",
                        kb_mnemonic="MOVE", operand_size="l"),
        ]})(),
        8: type("Block", (), {"instructions": [
            Instruction(offset=12, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
            Instruction(offset=14, size=4, opcode=0x2D40, text="move.l d0,-32764(a6)", raw=b"\x2D\x40\x80\x04",
                        kb_mnemonic="MOVE", operand_size="l"),
        ]})(),
    }
    blocks[0].xrefs = []
    blocks[8].xrefs = []

    app_offsets = build_app_slot_symbols(
        blocks=blocks,
        lib_calls=lib_calls,
        code=b"",
        os_kb=runtime_os,
        platform=make_platform(app_base=AppBaseInfo(
            kind=AppBaseKind.ABSOLUTE,
            reg_num=6,
            concrete=0x8000,
        )),
    )

    assert app_offsets == {
        -32768: "app_openlibrary_library_0000",
        -32764: "app_openlibrary_library_0004",
    }


def test_analyze_call_setups_names_pc_relative_struct_argument_targets() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="intuition.library",
            function="OpenScreen",
            lvo=-198,
            inputs=(runtime_os.OsInput(name="newScreen", regs=("A0",),
                                       type="struct NewScreen *", i_struct="NewScreen"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41FA, text="lea 8(pc),a0", raw=b"\x41\xFA\x00\x08",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    result = analyze_call_setups(
        blocks=blocks,
        lib_calls=lib_calls,
        os_kb=runtime_os,
        code=b"\x00" * 16,
        platform=make_platform(),
    )

    assert result.arg_annotations == {
        0: CallArgumentAnnotation("newScreen", "A0", "OpenScreen", "intuition.library")
    }
    assert result.segment_data_symbols == {0x000A: "openscreen_newscreen"}
    assert result.segment_struct_regions == {0x000A: "NewScreen"}
    assert result.segment_code_symbols == {}
    assert result.code_entry_points == ()
    assert result.string_ranges == {}
    assert result.typed_data_fields[0x000A] == ("NewScreen", "ns_LeftEdge", None)
    assert result.typed_data_sizes[0x000A] == 2
    assert result.typed_data_sizes[0x000C] == 2
    assert result.typed_data_sizes[0x001A] == 4
    assert result.typed_data_comments[0x000A] == "NewScreen.ns_LeftEdge"
    assert result.typed_data_comments[0x000C] == "NewScreen.ns_TopEdge"
    assert result.typed_data_comments[0x001A] == "NewScreen.ns_Font"


def test_refresh_library_call_signatures_uses_current_os_kb_inputs() -> None:
    call = LibraryCall(
        addr=0x12,
        block=0x10,
        library="intuition.library",
        function="SetPointer",
        lvo=-270,
        inputs=(runtime_os.OsInput(name="pointer", regs=("A1",), type="UWORD *", i_struct=None),),
    )
    updated_input = runtime_os.OsInput(
        name="pointer",
        regs=("A1",),
        type="struct SimpleSprite *",
        i_struct="SimpleSprite",
    )
    updated_function = replace(
        runtime_os.LIBRARIES["intuition.library"].functions["SetPointer"],
        inputs=(updated_input,),
    )
    updated_library = replace(
        runtime_os.LIBRARIES["intuition.library"],
        functions={
            **runtime_os.LIBRARIES["intuition.library"].functions,
            "SetPointer": updated_function,
        },
    )
    updated_os_kb = make_empty_os_kb()
    updated_os_kb = SimpleNamespace(
        META=updated_os_kb.META,
        VALUE_DOMAINS=updated_os_kb.VALUE_DOMAINS,
        API_INPUT_VALUE_DOMAINS=updated_os_kb.API_INPUT_VALUE_DOMAINS,
        STRUCT_FIELD_VALUE_DOMAINS=updated_os_kb.STRUCT_FIELD_VALUE_DOMAINS,
        STRUCTS=updated_os_kb.STRUCTS,
        CONSTANTS=updated_os_kb.CONSTANTS,
        LIBRARIES={
            **runtime_os.LIBRARIES,
            "intuition.library": updated_library,
        },
    )

    refreshed = _refresh_library_call_signatures([call], updated_os_kb)

    assert refreshed[0].inputs[0].type == "struct SimpleSprite *"
    assert refreshed[0].inputs[0].i_struct == "SimpleSprite"


def test_analyze_call_setups_extnewscreen_includes_inherited_fields() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="intuition.library",
            function="OpenScreen",
            lvo=-198,
            inputs=(runtime_os.OsInput(name="newScreen", regs=("A0",),
                                       type="struct ExtNewScreen *", i_struct="ExtNewScreen"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41FA, text="lea 8(pc),a0", raw=b"\x41\xFA\x00\x08",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    result = analyze_call_setups(
        blocks=blocks,
        lib_calls=lib_calls,
        os_kb=runtime_os,
        code=b"\x00" * 64,
        platform=make_platform(),
    )

    assert result.segment_struct_regions == {0x000A: "ExtNewScreen"}
    assert result.typed_data_sizes[0x000A] == 2
    assert result.typed_data_comments[0x000A] == "NewScreen.ns_LeftEdge"
    assert result.typed_data_comments[0x002A] == "ExtNewScreen.ens_Extension"


def test_analyze_call_setups_errors_on_conflicting_typed_names_for_same_segment_address() -> None:
    lib_calls = [
        LibraryCall(
            addr=4,
            block=0,
            library="intuition.library",
            function="OpenScreen",
            lvo=-198,
            inputs=(runtime_os.OsInput(name="newScreen", regs=("A0",),
                                       type="struct NewScreen *", i_struct="NewScreen"),),
        ),
        LibraryCall(
            addr=10,
            block=0,
            library="intuition.library",
            function="OpenWindow",
            lvo=-204,
            inputs=(runtime_os.OsInput(name="newWindow", regs=("A0",),
                                       type="struct NewWindow *", i_struct="NewWindow"),),
        ),
    ]
    blocks = {
        0: type("Block", (), {"instructions": [
            Instruction(offset=0, size=4, opcode=0x41FA, text="lea 8(pc),a0", raw=b"\x41\xFA\x00\x08",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=4, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
            Instruction(offset=6, size=4, opcode=0x41FA, text="lea 2(pc),a0", raw=b"\x41\xFA\x00\x02",
                        kb_mnemonic="LEA", operand_size="l"),
            Instruction(offset=10, size=2, opcode=0x4E75, text="rts", raw=b"\x4E\x75",
                        kb_mnemonic="RTS", operand_size="w"),
        ]})(),
    }

    with pytest.raises(ValueError, match="Conflicting typed segment names"):
        analyze_call_setups(
            blocks=blocks,
            lib_calls=lib_calls,
            os_kb=runtime_os,
            code=b"\x00" * 16,
            platform=make_platform(),
        )


def test_build_hunk_metadata_masks_hints_inside_typed_string_ranges() -> None:
    core_block = type("Block", (), {"start": 0x00, "end": 0x04, "successors": [], "instructions": []})()
    hint_block = type("Block", (), {"start": 0x20, "end": 0x24, "successors": [], "instructions": []})()
    ha = type("HA", (), {
        "blocks": {0x00: core_block},
        "hint_blocks": {0x20: hint_block},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [],
    })()
    metadata = build_hunk_metadata(
        code=b"\x00" * 0x40,
        code_size=0x40,
        hunk_index=0,
        hunk_entities=[],
        ha=ha,
        hf_hunks=[],
        typed_string_ranges={0x20: 0x24},
    )

    assert metadata.hint_addrs == set()
    assert metadata.string_addrs == {0x20}
    assert metadata.string_ranges == {0x20: 0x24}
    assert 0x20 not in metadata.labels


def test_prepare_hunk_code_relocates_payload_segment() -> None:
    code, code_size, relocated_segments, reloc_file_offset, reloc_base_addr = _prepare_hunk_code(
        b"\xAA\xBB\x11\x22",
        [RelocatedSegment(file_offset=2, base_addr=6)],
    )

    assert code == b"\xAA\xBB\x00\x00\x00\x00\x11\x22"
    assert code_size == 8
    assert relocated_segments == [RelocatedSegment(file_offset=2, base_addr=6)]
    assert reloc_file_offset == 2
    assert reloc_base_addr == 6


def test_prepare_hunk_sizes_rebases_relocated_runtime_window() -> None:
    stored_size, alloc_size = _prepare_hunk_sizes(
        stored_size=9968,
        alloc_size=9968,
        reloc_file_offset=490,
        reloc_base_addr=0,
    )

    assert stored_size == 9478
    assert alloc_size == 9478


def test_disassembly_session_uses_binary_analysis_suffix(tmp_path: Path) -> None:
    binary_path = tmp_path / "demo.bin"
    entities_path = tmp_path / "entities.jsonl"
    output_path = tmp_path / "demo.s"

    session = DisassemblySession(
        target_name="demo",
        binary_path=binary_path,
        analysis_cache_path=binary_path.with_suffix(".analysis"),
        entities_path=entities_path,
        output_path=output_path,
        entities=[],
        hunk_sessions=[],
        profile_stages=True,
    )

    assert session.target_name == "demo"
    assert session.analysis_cache_path == binary_path.with_suffix(".analysis")
    assert session.output_path == output_path
    assert session.profile_stages is True


def test_hunk_disassembly_session_preserves_metadata_and_analysis_fields() -> None:
    block = _block()
    hint_block = _block(2, 3)
    session = HunkDisassemblySession(
        hunk_index=1,
        code=b"\x00\x01",
        code_size=2,
        entities=[{"addr": "0000", "type": "code"}],
        blocks={0: block},
        hint_blocks={2: hint_block},
        code_addrs={0, 1},
        hint_addrs={2},
        reloc_map={0: 0x40},
        reloc_target_set={0x40},
        pc_targets={0x20: "pcref_0020"},
        string_addrs={0x20},
        labels={0x40: "loc_0040"},
        jump_table_regions={0x10: JumpTableRegion(pattern="word_table", table_end=0)},
        jump_table_target_sources={0x80: ("loc_0040",)},
        region_map={0x00: {"a0": TypedMemoryRegion(
            struct="Foo",
            size=4,
                provenance=MemoryRegionProvenance(
                    address_space=MemoryRegionAddressSpace.ABSOLUTE,
                    absolute_addr=0,
                ),
        )}},
        lvo_equs={"dos.library": {-552: "_LVOOpenLibrary"}},
        lvo_substitutions={0x10: ("-552(", "_LVOOpenLibrary(")},
        arg_equs={"OL_TAG": 1},
        arg_substitutions={0x12: ("#1", "#OL_TAG")},
        app_offsets={0x20: "app_dos_base"},
        arg_annotations={0x30: CallArgumentAnnotation("name", "D0", "OpenLibrary", "dos.library")},
        data_access_sizes={0x40: 2},
        typed_data_sizes={},
        typed_data_fields={},
        platform=make_platform(app_base=(6, 0x1000)),
        os_kb=make_empty_os_kb(),
        base_addr=0x400,
        code_start=2,
        relocated_segments=[RelocatedSegment(file_offset=0, base_addr=0)],
        reloc_file_offset=0,
        reloc_base_addr=0,
        string_ranges={},
        dynamic_structured_regions=(),
        absolute_labels={},
        reserved_absolute_addrs=set(),
        app_struct_regions={},
        hardware_base_regs={},
        unresolved_indirects={},
    )

    assert session.hunk_index == 1
    assert session.code == b"\x00\x01"
    assert session.jump_table_target_sources == {0x80: ("loc_0040",)}
    assert session.lvo_substitutions == {0x10: ("-552(", "_LVOOpenLibrary(")}
    assert session.app_offsets == {0x20: "app_dos_base"}


def test_build_hunk_metadata_collects_code_and_hint_addresses() -> None:
    block = type("Block", (), {"start": 0x10, "end": 0x14, "successors": [], "instructions": []})()
    hint_block = type("Block", (), {"start": 0x20, "end": 0x22, "successors": [], "instructions": []})()
    ha = type("Analysis", (), {
        "blocks": {0x10: block},
        "hint_blocks": {0x20: hint_block},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [],
    })()

    metadata = build_hunk_metadata(
        code=b"\x00" * 0x40,
        code_size=0x40,
        hunk_index=0,
        hunk_entities=[],
        ha=ha,
        hf_hunks=[],
        reserved_absolute_addrs=set(),
    )

    assert metadata.code_addrs == {0x10, 0x11, 0x12, 0x13}
    assert metadata.hint_addrs == {0x20, 0x21}


def test_build_hunk_metadata_builds_word_table_regions_and_sources() -> None:
    block = type("Block", (), {"start": 0x10, "end": 0x14, "successors": [], "instructions": []})()
    ha = type("Analysis", (), {
        "blocks": {0x10: block},
        "hint_blocks": {},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [JumpTable(
            addr=0x30,
            pattern=JumpTablePattern.WORD_OFFSET,
            targets=(0x80, 0x90),
            dispatch_sites=(0x10,),
            dispatch_block=0x10,
            base_addr=0x50,
            table_end=0x34,
        )],
    })()

    metadata = build_hunk_metadata(
        code=b"\x00" * 0x100,
        code_size=0x100,
        hunk_index=0,
        hunk_entities=[],
        ha=ha,
        hf_hunks=[],
        reserved_absolute_addrs=set(),
    )

    assert metadata.jump_table_regions[0x30].entries == (
        JumpTableEntryRef(0x30, 0x80), JumpTableEntryRef(0x32, 0x90))
    assert metadata.jump_table_regions[0x30].base_label == "loc_0050"
    assert metadata.jump_table_target_sources == {
        0x80: ("loc_0050",),
        0x90: ("loc_0050",),
    }


def test_build_hunk_metadata_preserves_string_dispatch_entry_offsets() -> None:
    block = type("Block", (), {"start": 0x10, "end": 0x14, "successors": [], "instructions": []})()
    ha = type("Analysis", (), {
        "blocks": {0x10: block},
        "hint_blocks": {},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [JumpTable(
            addr=0x30,
            pattern=JumpTablePattern.STRING_DISPATCH_SELF_RELATIVE,
            entries=(
                JumpTableEntry(offset_addr=0x32, target=0x80),
                JumpTableEntry(offset_addr=0x37, target=0x90),
            ),
            targets=(0x80, 0x90),
            dispatch_sites=(0x10,),
            dispatch_block=0x10,
            table_end=0x39,
        )],
    })()

    metadata = build_hunk_metadata(
        code=b"\x00" * 0x100,
        code_size=0x100,
        hunk_index=0,
        hunk_entities=[],
        ha=ha,
        hf_hunks=[],
        reserved_absolute_addrs=set(),
    )

    assert metadata.jump_table_regions[0x30].entries == (
        JumpTableEntryRef(0x32, 0x80), JumpTableEntryRef(0x37, 0x90))


def test_build_hunk_metadata_rejects_out_of_segment_jump_table_targets() -> None:
    block = type("Block", (), {"start": 0x10, "end": 0x14, "successors": [], "instructions": []})()
    ha = type("Analysis", (), {
        "blocks": {0x10: block},
        "hint_blocks": {},
        "call_targets": set(),
        "branch_targets": set(),
        "jump_tables": [JumpTable(
            addr=0x30,
            pattern=JumpTablePattern.WORD_OFFSET,
            targets=(0x80, 0x40000),
            dispatch_sites=(0x10,),
            dispatch_block=0x10,
            base_addr=0x50,
            table_end=0x34,
        )],
    })()

    with pytest.raises(ValueError, match="out-of-segment targets"):
        build_hunk_metadata(
            code=b"\x00" * 0x100,
            code_size=0x100,
            hunk_index=0,
            hunk_entities=[],
            ha=ha,
            hf_hunks=[],
            reserved_absolute_addrs=set(),
        )


def test_load_hunk_analysis_uses_cache_when_present(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    cache_path = hunk_analysis_cache_path(
        analysis_cache_root(
            tmp_path / "demo.analysis",
            seed_key="default",
            base_addr=0,
            code_start=0,
            entry_points=(),
        ),
        0,
    )
    cache_path.write_text("cache", encoding="utf-8")
    sentinel = object()
    seen: dict[str, object] = {}

    def fake_load(path: Path, os_kb: object) -> object:
        seen["path"] = path
        seen["os_kb"] = os_kb
        return sentinel

    monkeypatch.setattr("disasm.analysis_loader.HunkAnalysis.load", fake_load)
    fake_os_kb = make_empty_os_kb()
    monkeypatch.setattr("disasm.analysis_loader.m68k_analysis.RUNTIME_OS_KB", fake_os_kb)

    result = load_hunk_analysis(
        analysis_cache_path=tmp_path / "demo.analysis",
        code=b"\x00\x00",
        relocs=[],
        hunk_index=0,
        base_addr=0,
        code_start=0,
    )

    assert result is sentinel
    assert seen == {"path": cache_path, "os_kb": fake_os_kb}


def test_load_hunk_analysis_runs_analysis_without_cache(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    class FakeAnalysis:
        def save(self, path: Path) -> None:
            seen["saved_path"] = path

    sentinel = FakeAnalysis()
    relocs: list[RelocLike] = [_FakeReloc(reloc_type=HunkType.HUNK_RELOC32, offsets=(1,))]

    def fake_analyze_hunk(
        code: bytes,
        relocs: object,
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...] = (),
        extra_entry_points: tuple[int, ...] = (),
        entry_initial_states: object | None = None,
    ) -> FakeAnalysis:
        seen["args"] = (code, relocs, hunk_index, base_addr, code_start, entry_points)
        seen["extra_entry_points"] = extra_entry_points
        return sentinel

    monkeypatch.setattr("disasm.analysis_loader.analyze_hunk", fake_analyze_hunk)

    result = load_hunk_analysis(
        analysis_cache_path=tmp_path / "demo.analysis",
        code=b"\x01\x02",
        relocs=relocs,
        hunk_index=3,
        base_addr=0x400,
        code_start=2,
    )

    assert cast(object, result) is sentinel
    assert seen["args"] == (b"\x01\x02", relocs, 3, 0x400, 2, ())
    assert seen["extra_entry_points"] == ()
    assert seen["saved_path"] == hunk_analysis_cache_path(
        analysis_cache_root(
            tmp_path / "demo.analysis",
            seed_key="default",
            base_addr=0x400,
            code_start=2,
            entry_points=(),
            extra_entry_points=(),
        ),
        3,
    )


def test_load_hunk_analysis_rebuilds_stale_cache(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    cache_path = hunk_analysis_cache_path(
        analysis_cache_root(
            tmp_path / "demo.analysis",
            seed_key="default",
            base_addr=0x400,
            code_start=2,
            entry_points=(),
        ),
        3,
    )
    cache_path.write_text("stale", encoding="utf-8")
    seen: dict[str, object] = {}

    class FakeAnalysis:
        def save(self, path: Path) -> None:
            seen["saved_path"] = path

    sentinel = FakeAnalysis()
    relocs: list[RelocLike] = [_FakeReloc(reloc_type=HunkType.HUNK_RELOC32, offsets=(1,))]

    def fake_load(path: Path, os_kb: object) -> object:
        seen["load"] = (path, os_kb)
        from m68k.analysis import AnalysisCacheError
        raise AnalysisCacheError("Cache version mismatch")

    def fake_analyze_hunk(
        code: bytes,
        relocs: object,
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...] = (),
        extra_entry_points: tuple[int, ...] = (),
        entry_initial_states: object | None = None,
    ) -> FakeAnalysis:
        seen["analyze"] = (code, relocs, hunk_index, base_addr, code_start, entry_points)
        seen["extra_entry_points"] = extra_entry_points
        return sentinel

    monkeypatch.setattr("disasm.analysis_loader.HunkAnalysis.load", fake_load)
    monkeypatch.setattr("disasm.analysis_loader.analyze_hunk", fake_analyze_hunk)
    fake_os_kb = make_empty_os_kb()
    monkeypatch.setattr("disasm.analysis_loader.m68k_analysis.RUNTIME_OS_KB", fake_os_kb)

    result = load_hunk_analysis(
        analysis_cache_path=tmp_path / "demo.analysis",
        code=b"\x01\x02",
        relocs=relocs,
        hunk_index=3,
        base_addr=0x400,
        code_start=2,
    )

    assert cast(object, result) is sentinel
    assert seen["load"] == (cache_path, fake_os_kb)
    assert seen["analyze"] == (b"\x01\x02", relocs, 3, 0x400, 2, ())
    assert seen["extra_entry_points"] == ()
    assert seen["saved_path"] == cache_path


def test_load_hunk_analysis_does_not_hide_non_cache_value_errors(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    cache_path = hunk_analysis_cache_path(
        analysis_cache_root(
            tmp_path / "demo.analysis",
            seed_key="default",
            base_addr=0,
            code_start=0,
            entry_points=(),
            extra_entry_points=(),
        ),
        0,
    )
    cache_path.write_text("broken", encoding="utf-8")

    def fake_load(path: Path, os_kb: object) -> object:
        raise ValueError("unexpected parse bug")

    monkeypatch.setattr("disasm.analysis_loader.HunkAnalysis.load", fake_load)
    monkeypatch.setattr("disasm.analysis_loader.m68k_analysis.RUNTIME_OS_KB", make_empty_os_kb())

    with pytest.raises(ValueError, match="unexpected parse bug"):
        load_hunk_analysis(
            analysis_cache_path=tmp_path / "demo.analysis",
            code=b"\x01\x02",
            relocs=[],
            hunk_index=0,
            base_addr=0,
            code_start=0,
        )


def test_load_hunk_analysis_uses_distinct_cache_files_per_hunk(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    cache_root = tmp_path / "demo.analysis"
    seen_paths: list[Path] = []

    class FakeAnalysis:
        def save(self, path: Path) -> None:
            seen_paths.append(path)

    monkeypatch.setattr("disasm.analysis_loader.analyze_hunk", lambda *args, **kwargs: FakeAnalysis())

    load_hunk_analysis(
        analysis_cache_path=cache_root,
        code=b"\x00",
        relocs=[],
        hunk_index=0,
        base_addr=0,
        code_start=0,
    )
    load_hunk_analysis(
        analysis_cache_path=cache_root,
        code=b"\x00",
        relocs=[],
        hunk_index=1,
        base_addr=0,
        code_start=0,
    )

    assert seen_paths == [
        hunk_analysis_cache_path(
            analysis_cache_root(
                cache_root,
                seed_key="default",
                base_addr=0,
                code_start=0,
                entry_points=(),
            ),
            0,
        ),
        hunk_analysis_cache_path(
            analysis_cache_root(
                cache_root,
                seed_key="default",
                base_addr=0,
                code_start=0,
                entry_points=(),
            ),
            1,
        ),
    ]


def test_render_rows_concatenates_listing_text() -> None:
    rows = [
        ListingRow(row_id="a", kind="comment", text="; one\n"),
        ListingRow(row_id="b", kind="instruction", text="moveq #0,d0\n"),
    ]

    assert render_rows(rows) == "; one\nmoveq #0,d0\n"


def test_render_comment_parts_joins_non_empty_parts() -> None:
    assert render_comment_parts(("68020+", "", "note")) == "68020+; note"


def test_build_instruction_comment_parts_prefers_app_offset_before_ascii() -> None:
    inst = Instruction(
        offset=0x10,
        size=6,
        opcode=0x203C,
        text="corrupted",
        raw=b"\x20\x3C\x4C\x49\x4E\x45",
        kb_mnemonic="move",
        operand_size="l",
        operand_texts=("#$4C494E45", "568(a6)"),
    )
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={"exec.library": {-456: "_LVODoIO"}},
        lvo_substitutions={0: ("rts", "_LVODoIO(a6)")},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(app_base=(6, 0)),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    parts = build_instruction_comment_parts(
        inst,
        session,
        operand_parts=(
            SemanticOperand(kind="immediate", value=0x4C494E45,
                            base_register=None, displacement=None,
                            text="#$4C494E45"),
            SemanticOperand(kind="base_displacement", value=568,
                            base_register="a6", displacement=568,
                            text="568(a6)"),
        ))

    assert parts == ("app+$238",)


def test_build_instruction_comment_parts_uses_instruction_processor_min_not_text() -> None:
    inst = Instruction(
        offset=0x10,
        size=2,
        opcode=0x49C0,
        text="corrupted",
        raw=b"\x49\xC0",
        kb_mnemonic="extb",
        operand_size="l",
    )
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    parts = build_instruction_comment_parts(
        inst,
        session,
        operand_parts=(
            SemanticOperand(kind="register", value=None,
                            base_register=None, displacement=None,
                            text="d0"),
        ))
    assert parts == ("68020+",)


def test_render_instruction_text_requires_opcode_text() -> None:
    inst = Instruction(
        offset=0x10,
        size=2,
        opcode=0x49C0,
        text="corrupted",
        raw=b"\x49\xC0",
        kb_mnemonic="extb",
        operand_size="l",
        operand_texts=("d0",),
    )
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    from disasm.instruction_rows import render_instruction_text

    with pytest.raises(AssertionError, match="missing opcode_text"):
        render_instruction_text(inst, session, set())


def test_build_instruction_comment_parts_uses_decoded_immediate_not_rendered_text() -> None:
    inst = Instruction(
        offset=0x38,
        size=6,
        opcode=0x203C,
        text="corrupted",
        raw=b"\x20\x3C\x4C\x49\x4E\x45",
        kb_mnemonic="move",
        operand_size="l",
        operand_texts=("#$4C494E45", "d0"),
    )
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    parts = build_instruction_comment_parts(
        inst,
        session,
        operand_parts=(
            SemanticOperand(kind="immediate", value=0x4C494E45,
                            base_register=None, displacement=None,
                            text="#$4C494E45"),
            SemanticOperand(kind="register", value=None,
                            base_register=None, displacement=None,
                            text="d0"),
        ))

    assert parts == ("'LINE'",)


def test_build_instruction_comment_parts_appends_unresolved_indirect_marker() -> None:
    session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        unresolved_indirects={0x20: IndirectSite(
            addr=0x20,
            mnemonic="JSR",
            flow_type=runtime_m68k_analysis.FlowType.CALL,
            shape="pcindex.brief",
            status=IndirectSiteStatus.UNRESOLVED,
            target=None,
            region=IndirectSiteRegion.CORE,
        )},
    )
    inst = Instruction(
        offset=0x20,
        size=2,
        opcode=0x4E90,
        text="corrupted",
        raw=b"\x4E\x90",
        kb_mnemonic="jsr",
    )

    parts = build_instruction_comment_parts(inst, session, ())

    assert parts == ("unresolved_indirect_core:pcindex.brief",)


def test_build_instruction_comment_parts_suppresses_unresolved_marker_for_refined_lib_call() -> None:
    inst = Instruction(
        offset=0x20,
        size=4,
        opcode=0x4EAE,
        text="jsr -210(a6)",
        raw=b"\x4e\xae\xff\x2e",
        kb_mnemonic="jsr",
        operand_size="l",
        operand_texts=("-210(a6)",),
    )
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs={0x20},
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        unresolved_indirects={
            0x20: IndirectSite(
                addr=0x20,
                mnemonic="JSR",
                flow_type=runtime_m68k_analysis.FlowType.CALL,
                shape="disp",
                target=None,
                region=IndirectSiteRegion.CORE,
                status=IndirectSiteStatus.UNRESOLVED,
            )
        },
        lib_calls=(
            LibraryCall(
                addr=0x20,
                block=0x20,
                library="exec.library",
                function="FreeMem",
                lvo=-210,
            ),
        ),
    )

    parts = build_instruction_comment_parts(inst, hunk_session, operand_parts=())

    assert parts == ()


def test_get_instruction_processor_min_reports_base_68000_instruction() -> None:
    inst = Instruction(
        offset=0x10,
        size=2,
        opcode=0x7000,
        text="moveq   #0,d0",
        raw=b"\x70\x00",
        kb_mnemonic="moveq",
        operand_size="l",
    )
    assert get_instruction_processor_min(inst) == "68000"


def test_has_valid_branch_target_rejects_odd_branch_target() -> None:
    inst = Instruction(
        offset=0x40,
        size=2,
        opcode=0x6605,
        text="bne.s   $000047",
        raw=b"\x66\x05",
        kb_mnemonic="bcc",
    )

    assert has_valid_branch_target(inst) is False


def test_hint_block_has_supported_terminal_flow_for_return() -> None:
    block = type("Block", (), {
        "instructions": [
            Instruction(
                offset=0x10,
                size=2,
                opcode=0x4E75,
                text="rts",
                raw=b"\x4E\x75",
                kb_mnemonic="rts",
                operand_size="w",
            )
        ]
    })()

    assert hint_block_has_supported_terminal_flow(block) is True


def test_is_valid_hint_block_rejects_non_68000_instruction() -> None:
    block = type("Block", (), {
        "instructions": [
            Instruction(
                offset=0x10,
                size=2,
                opcode=0x49C0,
                text="corrupted",
                raw=b"\x49\xC0",
                kb_mnemonic="extb",
                operand_size="l",
            )
        ]
    })()

    assert is_valid_hint_block(block) is False


def test_emit_jump_table_rows_emits_data_entries() -> None:
    rows: list[ListingRow] = []
    labels_seen = []

    def emit_label(addr: int) -> None:
        labels_seen.append(addr)

    hunk_session = type("HunkSession", (), {
        "jump_table_regions": {
            0x20: JumpTableRegion(
                pattern="word_table",
                entries=(JumpTableEntryRef(0x20, 0x80), JumpTableEntryRef(0x22, 0x90)),
                base_label="ignored",
                table_end=0x24,
            )
        },
        "labels": {0x80: "loc_0080", 0x90: "loc_0090"},
    })()

    end = emit_jump_table_rows(
        rows, hunk_session, 0x20, 0x20, set(), emit_label)

    assert end == 0x24
    assert labels_seen == []
    assert len(rows) == 2
    assert rows[0].text == "    dc.w    loc_0080-*\n"


def test_emit_jump_table_rows_emits_inline_dispatch_rows() -> None:
    rows: list[ListingRow] = []
    labels_seen = []

    def emit_label(addr: int) -> None:
        labels_seen.append(addr)

    code = b"\x70\x00\x4E\x75"
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=code,
        code_size=len(code),
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x02: "loc_0002"},
        jump_table_regions={
            0x00: JumpTableRegion(pattern="pc_inline_dispatch", table_end=0x04)
        },
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    end = emit_jump_table_rows(
        rows, hunk_session, 0x00, 0x00, set(), emit_label)

    assert end == 0x04
    assert labels_seen == [0x02]
    assert len(rows) == 2


def test_emit_jump_table_rows_emits_string_dispatch_rows() -> None:
    rows: list[ListingRow] = []

    def emit_label(addr: int) -> None:
        raise AssertionError(f"Unexpected label emission at ${addr:04x}")

    code = bytes([1, 1, 0, 6, 1, 2, 0, 8, 0, 0x4E, 0x75, 0x4E, 0x75])
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=code,
        code_size=len(code),
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x08: "loc_0008", 0x0A: "loc_000a"},
        jump_table_regions={
            0x00: JumpTableRegion(
                pattern="string_dispatch_self_relative",
                entries=(JumpTableEntryRef(0x02, 0x08), JumpTableEntryRef(0x06, 0x0A)),
                table_end=0x08,
            )
        },
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    end = emit_jump_table_rows(
        rows, hunk_session, 0x00, 0x00, set(), emit_label)

    assert end == 0x08
    assert [row.text for row in rows] == [
        "    dc.b    $01,$01\n",
        "    dc.w    loc_0008-*\n",
        "    dc.b    $01,$02\n",
        "    dc.w    loc_000a-*\n",
    ]


def test_emit_jump_table_rows_preserves_sparse_word_gaps() -> None:
    rows: list[ListingRow] = []

    def emit_label(addr: int) -> None:
        raise AssertionError(f"Unexpected label emission at ${addr:04x}")

    code = bytes.fromhex("0000000400000008")
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=code,
        code_size=len(code),
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x20: "loc_0020", 0x24: "loc_0024"},
        jump_table_regions={
            0x00: JumpTableRegion(
                pattern="pc_sparse_word_offset",
                entries=(JumpTableEntryRef(0x02, 0x20), JumpTableEntryRef(0x06, 0x24)),
                base_addr=0x00,
                base_label="jt_0000",
                table_end=0x08,
            )
        },
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    end = emit_jump_table_rows(
        rows, hunk_session, 0x00, 0x00, set(), emit_label)

    assert end == 0x08
    assert [row.text for row in rows] == [
        "    dc.b    $00,$00\n",
        "    dc.w    loc_0020-jt_0000\n",
        "    dc.b    $00,$00\n",
        "    dc.w    loc_0024-jt_0000\n",
    ]


def test_listing_window_anchors_to_matching_addr() -> None:
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="", addr=0x10),
        ListingRow(row_id="r1", kind="instruction", text="", addr=0x20),
        ListingRow(row_id="r2", kind="instruction", text="", addr=0x30),
    ]

    window = listing_window(rows, 0x20, before=1, after=1)

    assert [row.row_id for row in window["rows"]] == ["r0", "r1", "r2"]
    assert window["start"] == 0
    assert window["end"] == 3


def test_listing_window_anchors_to_last_row_past_end() -> None:
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="", addr=0x10),
        ListingRow(row_id="r1", kind="instruction", text="", addr=0x20),
        ListingRow(row_id="r2", kind="instruction", text="", addr=0x30),
    ]

    window = listing_window(rows, 0x40, before=1, after=0)

    assert [row.row_id for row in window["rows"]] == ["r1", "r2"]
    assert window["has_more_before"] is True
    assert window["has_more_after"] is False


def test_gen_disasm_uses_shared_session_row_pipeline(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    calls: list[str] = []
    output_path = tmp_path / "out.s"
    entities_path = tmp_path / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=entities_path,
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=output_path,
        entities=[],
        hunk_sessions=[],
    )
    rows: list[ListingRow] = [ListingRow(row_id="row0", kind="instruction", text="moveq #0,d0\n")]

    def fake_build_session(
        binary_path: str,
        entities_path: str,
        session_output_path: str | None,
        base_addr: int = 0,
        code_start: int = 0,
        profile_stages: bool = False,
    ) -> DisassemblySession:
        calls.append("build_session")
        assert binary_path == "bin/test"
        assert entities_path == str(entities_path_obj)
        assert session_output_path == str(output_path)
        assert base_addr == 0x400
        assert code_start == 2
        assert profile_stages is True
        return session

    def fake_emit_rows(seen_session: DisassemblySession) -> list[ListingRow]:
        calls.append("emit_rows")
        assert seen_session is session
        return rows

    def fake_render_rows(seen_rows: list[ListingRow]) -> str:
        calls.append("render_rows")
        assert seen_rows == rows
        return "; rendered\n"

    def fake_refresh_needed(binary_path: str, seen_entities_path: str) -> bool:
        assert binary_path == "bin/test"
        assert seen_entities_path == str(entities_path_obj)
        return False

    entities_path_obj = entities_path
    monkeypatch.setattr(gen_disasm_mod, "build_disassembly_session",
                        fake_build_session)
    monkeypatch.setattr(gen_disasm_mod, "emit_session_rows", fake_emit_rows)
    monkeypatch.setattr(gen_disasm_mod, "render_rows", fake_render_rows)
    monkeypatch.setattr(gen_disasm_mod, "_entities_need_refresh", fake_refresh_needed)

    gen_disasm_mod.gen_disasm(
        "bin/test",
        str(entities_path),
        str(output_path),
        base_addr=0x400,
        code_start=2,
        profile_stages=True,
    )

    assert calls == ["build_session", "emit_rows", "render_rows"]
    assert output_path.read_text() == "; rendered\n"


def test_gen_disasm_refreshes_entities_when_needed(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[object, ...]] = []
    output_path = tmp_path / "out.s"
    entities_path = tmp_path / "entities.jsonl"
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=entities_path,
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=output_path,
        entities=[],
        hunk_sessions=[],
    )

    def fake_refresh_needed(binary_path: str, seen_entities_path: str) -> bool:
        calls.append(("refresh_check", binary_path, seen_entities_path))
        return True

    def fake_build_entities(
        binary_path: str,
        seen_entities_path: str,
        base_addr: int,
        code_start: int,
    ) -> int:
        calls.append(("build_entities", binary_path, seen_entities_path, base_addr, code_start))
        Path(seen_entities_path).write_text("", encoding="utf-8")
        return 0

    def fake_build_session(
        binary_path: str,
        seen_entities_path: str,
        session_output_path: str | None,
        base_addr: int = 0,
        code_start: int = 0,
        profile_stages: bool = False,
    ) -> DisassemblySession:
        calls.append(("build_session", binary_path, seen_entities_path))
        return session

    def fake_emit_session_rows(seen_session: DisassemblySession) -> list[ListingRow]:
        return []

    def fake_render_rows(seen_rows: list[ListingRow]) -> str:
        return ""

    monkeypatch.setattr(gen_disasm_mod, "_entities_need_refresh", fake_refresh_needed)
    monkeypatch.setattr(gen_disasm_mod, "build_entities", fake_build_entities)
    monkeypatch.setattr(gen_disasm_mod, "build_disassembly_session", fake_build_session)
    monkeypatch.setattr(gen_disasm_mod, "emit_session_rows", fake_emit_session_rows)
    monkeypatch.setattr(gen_disasm_mod, "render_rows", fake_render_rows)

    gen_disasm_mod.gen_disasm(
        "bin/test",
        str(entities_path),
        str(output_path),
        base_addr=0x400,
        code_start=2,
    )

    assert calls[:3] == [
        ("refresh_check", "bin/test", str(entities_path)),
        ("build_entities", "bin/test", str(entities_path), 0x400, 2),
        ("build_session", "bin/test", str(entities_path)),
    ]


def test_emit_session_rows_smoke_for_empty_hunk_session() -> None:
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[
            HunkDisassemblySession(
                hunk_index=0,
                code=b"",
                code_size=0,
                entities=[],
                blocks={},
                hint_blocks={},
                code_addrs=set(),
                hint_addrs=set(),
                reloc_map={},
                reloc_target_set=set(),
                pc_targets={},
                string_addrs=set(),
                labels={},
                jump_table_regions={},
                jump_table_target_sources={},
                region_map={},
                lvo_equs={},
                lvo_substitutions={},
                arg_equs={},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                data_access_sizes={},
                platform=make_platform(),
        os_kb=make_empty_os_kb(),
                base_addr=0,
                code_start=0,
                relocated_segments=[],
                reloc_file_offset=0,
                reloc_base_addr=0,
            )
        ],
    )

    rows = emit_session_rows(session)

    assert rows
    assert rows[0].kind == "comment"


def test_emit_session_rows_emits_file_header_once_for_multi_hunk_session() -> None:
    def empty_hunk(index: int, size: int) -> HunkDisassemblySession:
        return HunkDisassemblySession(
            hunk_index=index,
            code=b"\x00" * size,
            code_size=size,
            entities=[],
            blocks={},
            hint_blocks={},
            code_addrs=set(),
            hint_addrs=set(),
            reloc_map={},
            reloc_target_set=set(),
            pc_targets={},
            string_addrs=set(),
            labels={},
            jump_table_regions={},
            jump_table_target_sources={},
            region_map={},
            lvo_equs={},
            lvo_substitutions={},
            arg_equs={},
            arg_substitutions={},
            app_offsets={},
            arg_annotations={},
            data_access_sizes={},
            platform=make_platform(),
            os_kb=make_empty_os_kb(),
            base_addr=0,
            code_start=0,
            relocated_segments=[],
            reloc_file_offset=0,
            reloc_base_addr=0,
        )

    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[empty_hunk(0, 316), empty_hunk(1, 504)],
    )

    rows = emit_session_rows(session)
    comments = [row.text for row in rows if row.kind == "comment"]

    assert comments.count("; Generated disassembly -- vasm Motorola syntax\n") == 1
    assert comments.count("; Source: bin\\demo\n") == 1
    assert "; 820 bytes, 0 entities, 0 blocks\n" in comments
    assert "; Hunk 0: 316 bytes, 0 entities, 0 blocks\n" in comments
    assert "; Hunk 1: 504 bytes, 0 entities, 0 blocks\n" in comments


def test_emit_hunk_rows_uses_real_section_kind_and_bss_space() -> None:
    data_hunk = HunkDisassemblySession(
        hunk_index=0,
        hunk_type=int(HunkType.HUNK_DATA),
        mem_type=int(MemType.FAST),
        section_name="assets",
        code=b"\x11\x22\x33\x44",
        code_size=4,
        alloc_size=4,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    bss_hunk = replace(
        data_hunk,
        hunk_index=1,
        hunk_type=int(HunkType.HUNK_BSS),
        mem_type=int(MemType.CHIP),
        section_name="work",
        code=b"",
        code_size=0,
        alloc_size=12,
        stored_size=0,
        labels={0: "work_area"},
    )

    data_rows, _data_floor, _data_preamble = emitter_mod._emit_hunk_rows(
        data_hunk,
        include_header=False,
    )
    bss_rows, _bss_floor, _bss_preamble = emitter_mod._emit_hunk_rows(
        bss_hunk,
        include_header=False,
    )

    assert data_rows[0].text == "    section assets,data,fast\n"
    assert any(row.kind == "data" for row in data_rows)
    assert bss_rows[0].text == "    section work,bss,chip\n"
    assert any(row.text == "work_area:\n" for row in bss_rows)
    assert any(row.text == "    ds.b 12\n" for row in bss_rows)


def test_emit_hunk_rows_splits_bss_space_at_interior_labels() -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        hunk_type=int(HunkType.HUNK_BSS),
        mem_type=int(MemType.ANY),
        section_name="bss",
        code=b"",
        code_size=0,
        alloc_size=12,
        stored_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0: "bss_start", 4: "bss_mid", 8: "bss_end"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    rows, _compat_floor, _preamble = emitter_mod._emit_hunk_rows(
        hunk_session,
        include_header=False,
    )

    assert rows[0].text == "    section bss,bss\n"
    assert [row.text for row in rows if row.kind == "label"] == [
        "bss_start:\n",
        "bss_mid:\n",
        "bss_end:\n",
    ]
    assert [row.text for row in rows if row.kind == "directive"] == [
        "    ds.b 4\n",
        "    ds.b 4\n",
        "    ds.b 4\n",
    ]


def test_emit_hunk_rows_emits_databss_tail_for_shortened_data_hunk() -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        hunk_type=int(HunkType.HUNK_DATA),
        mem_type=int(MemType.ANY),
        section_name="data",
        code=b"\x11\x22\x33\x44",
        code_size=4,
        alloc_size=8,
        stored_size=4,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    rows, _floor, _preamble = emitter_mod._emit_hunk_rows(
        hunk_session,
        include_header=False,
    )

    assert [row.text for row in rows] == [
        "    section data,data\n",
        "\n",
        "    dc.b    $11,$22,$33,$44\n",
        "    ds.b 4\n",
    ]


def test_emit_hunk_rows_splits_databss_tail_at_interior_labels() -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        hunk_type=int(HunkType.HUNK_DATA),
        mem_type=int(MemType.ANY),
        section_name="data",
        code=b"\x11\x22\x33\x44",
        code_size=4,
        alloc_size=12,
        stored_size=4,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={8: "tail_mid"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    rows, _floor, _preamble = emitter_mod._emit_hunk_rows(
        hunk_session,
        include_header=False,
    )

    assert [row.text for row in rows] == [
        "    section data,data\n",
        "\n",
        "    dc.b    $11,$22,$33,$44\n",
        "    ds.b 4\n",
        "tail_mid:\n",
        "    ds.b 4\n",
    ]


def test_emit_session_rows_includes_bootblock_structure_section() -> None:
    session = DisassemblySession(
        target_name="demo_bootblock",
        binary_path=Path("targets/demo_bootblock/binary.bin"),
        entities_path=Path("targets/demo_bootblock/entities.jsonl"),
        analysis_cache_path=Path("targets/demo_bootblock/binary.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[
                HunkDisassemblySession(
                    hunk_index=0,
                    code=b"DOS\x00" + b"\x00\x00\x00\x00" + b"\x00\x00\x03\x70" + b"\x4e\x75",
                    code_size=14,
                    entities=[],
                    blocks={
                        0x0C: _FakeBlock(
                            start=0x0C,
                            end=0x0E,
                            successors=(),
                            instructions=[
                                _instruction(
                                    offset=0x0C,
                                    raw=b"\x4e\x75",
                                    mnemonic="rts",
                                    operand_size="w",
                                    operand_texts=(),
                                )
                            ],
                        )
                    },
                    hint_blocks={},
                    code_addrs={0x0C, 0x0D},
                    hint_addrs=set(),
                    reloc_map={},
                    reloc_target_set=set(),
                    pc_targets={},
                    string_addrs={0},
                    labels={
                        0: "boot_magic",
                        4: "boot_checksum",
                        8: "boot_root_block",
                        0x0C: "boot_entry",
                    },
                jump_table_regions={},
                jump_table_target_sources={},
                region_map={},
                lvo_equs={"exec.library": {-456: "_LVODoIO"}},
                lvo_substitutions={0: ("rts", "_LVODoIO(a6)")},
                arg_equs={},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                    data_access_sizes={4: 4, 8: 4},
                    platform=make_platform(),
                    os_kb=make_empty_os_kb(),
                    base_addr=0,
                    code_start=0x0C,
                relocated_segments=[],
                reloc_file_offset=0,
                reloc_base_addr=0,
            )
        ],
        target_metadata=TargetMetadata(
            target_type="bootblock",
            entry_register_seeds=(
                EntryRegisterSeedMetadata(
                    entry_offset=None,
                    register="A6",
                    kind="library_base",
                    note="ExecBase",
                    library_name="exec.library",
                    struct_name="LIB",
                    context_name=None,
                ),
                EntryRegisterSeedMetadata(
                    entry_offset=None,
                    register="A1",
                    kind="struct_ptr",
                    note="IOStdReq (open trackdisk.device)",
                    library_name=None,
                    struct_name="IO",
                    context_name="trackdisk.device",
                ),
            ),
            bootblock=BootBlockTargetMetadata(
                magic_ascii="DOS",
                flags_byte=0,
                fs_description="DOS\\0 - OFS",
                checksum="0x00000000",
                checksum_valid=True,
                rootblock_ptr=880,
                bootcode_offset=0x0C,
                bootcode_size=1012,
                load_address=0x70000,
                entrypoint=0x7000C,
            ),
        ),
    )

    rows = emit_session_rows(session)
    rendered = "".join(row.text for row in rows)

    assert "; Boot block structure\n" in rendered
    assert "; OS compatibility floor: 1.3\n" in rendered
    assert ";   boot code: offset 0xC, size 1012 bytes\n" in rendered
    assert ";   execution context:" not in rendered
    assert 'INCLUDE "exec/exec_lib.i"\n' in rendered
    assert "_LVODoIO\tEQU\t-456\n" not in rendered
    assert "boot_entry:\n" in rendered


def test_build_disassembly_session_for_local_offset_raw_bootblock_renders_local_labels(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "bootblock"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(
        (b"DOS\x00" + b"\x00\x00\x00\x00" + b"\x00\x00\x03\x70")
        + bytes.fromhex("43FA00184EAEFFA04A80670A20402068001670004E7570FF60FA")
        + b"dos.library\x00",
    )
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="bootblock",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        bootblock=BootBlockTargetMetadata(
            magic_ascii="DOS",
            flags_byte=0,
            fs_description="DOS\\0 - OFS",
            checksum="0x00000000",
            checksum_valid=True,
            rootblock_ptr=880,
            bootcode_offset=0x0C,
            bootcode_size=1012,
            load_address=0x70000,
            entrypoint=0x7000C,
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )

    rendered = render_session_text(build_disassembly_session(source, str(entities_path)))

    assert "boot_magic:\n" in rendered
    assert "; OS compatibility floor: 1.3\n" in rendered
    assert 'dc.b    "DOS",0\n' in rendered
    assert "boot_checksum:\n" in rendered
    assert "dc.l    $00000000\n" in rendered
    assert "boot_root_block:\n" in rendered
    assert "dc.l    $00000370\n" in rendered
    assert "boot_entry:\n" in rendered
    assert "dc.b    $43,$fa,$00,$18,$4e,$ae,$ff,$a0" not in rendered
    assert "jsr _LVOFindResident(a6)" in rendered
    assert "movea.l RT_INIT(a0),a0" in rendered
    assert "movea.l d0,a0" in rendered
    assert "moveq #0,d0" in rendered
    assert ";   boot code: offset 0xC, size 1012 bytes\n" in rendered
    assert ";   execution context:" not in rendered
    assert "$70022" not in rendered
    assert "$70020" not in rendered


def test_build_disassembly_session_leaves_out_of_segment_absolute_jump_unlabeled(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "bootblock_abs_jump"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(
        b"DOS\x00"
        + bytes.fromhex("A382070F")
        + bytes.fromhex("00000370")
        + bytes.fromhex(
            "48E7FFFE337C0002001C237C000400000028237C000054000024"
            "237C00000400002C4EAEFE384EF900040000"
        )
        + b"\x00" * (1024 - 12 - 38)
    )
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="bootblock",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A1",
                kind="struct_ptr",
                note="IOStdReq (open trackdisk.device)",
                library_name=None,
                struct_name="IO",
                context_name="trackdisk.device",
            ),
        ),
        bootblock=BootBlockTargetMetadata(
            magic_ascii="DOS",
            flags_byte=0,
            fs_description="DOS\\0 - OFS",
            checksum="0xA382070F",
            checksum_valid=True,
            rootblock_ptr=880,
            bootcode_offset=0x0C,
            bootcode_size=1012,
            load_address=0x70000,
            entrypoint=0x7000C,
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="local_offset",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )

    rendered = render_session_text(build_disassembly_session(source, str(entities_path)))

    assert "move.w #CMD_READ,IO_COMMAND(a1)" in rendered
    assert "move.l #$40000,IO_DATA(a1)" in rendered
    assert "move.l #$5400,IO_LENGTH(a1)" in rendered
    assert "move.l #$400,IO_OFFSET(a1)" in rendered
    assert "jsr _LVODoIO(a6)" in rendered
    assert "jmp $00040000" in rendered
    assert "loc_40000" not in rendered


def test_build_disassembly_session_for_runtime_absolute_raw_keeps_absolute_label_space(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "absolute_boot"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "binary.bin"
    binary_path.write_bytes(
        (b"DOS\x00" + b"\x00\x00\x00\x00" + b"\x00\x00\x03\x70")
        + bytes.fromhex("43FA00184EAEFFA04A80670A20402068001670004E7570FF60FA")
        + b"dos.library\x00",
    )
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="bootblock",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=None,
                register="A1",
                kind="struct_ptr",
                note="IOStdReq (open trackdisk.device)",
                library_name=None,
                struct_name="IO",
                context_name="trackdisk.device",
            ),
        ),
        bootblock=BootBlockTargetMetadata(
            magic_ascii="DOS",
            flags_byte=0,
            fs_description="DOS\\0 - OFS",
            checksum="0x00000000",
            checksum_valid=True,
            rootblock_ptr=880,
            bootcode_offset=0x0C,
            bootcode_size=1012,
            load_address=0x70000,
            entrypoint=0x7000C,
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source = RawBinarySource(
        kind="raw_binary",
        path=binary_path,
        address_model="runtime_absolute",
        load_address=0x70000,
        entrypoint=0x7000C,
        code_start_offset=0x0C,
        display_path=str(binary_path),
        analysis_cache_path=target_dir / "binary.analysis",
    )

    rendered = render_session_text(build_disassembly_session(source, str(entities_path)))

    assert "boot_magic:\n" in rendered
    assert "boot_entry:\n" in rendered
    assert "dc.b    $43,$fa,$00,$18,$4e,$ae,$ff,$a0" not in rendered
    assert "movea.l d0,a0" in rendered
    assert "moveq #0,d0" in rendered
    assert ";   boot code: offset 0xC, size 1012 bytes\n" in rendered
    assert ";   execution context: load 0x70000, entry 0x7000C\n" in rendered
    assert "$70022" not in rendered
    assert "$70020" not in rendered


def test_build_entry_seed_config_scopes_autoinit_library_a6_by_entrypoint() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x88,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=4,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x44,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x44,
                base_size=0x24,
                vectors_offset=0x54,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x88,
            ),
        ),
    )

    seed_config = build_entry_seed_config(metadata)

    assert seed_config.initial_state is None
    assert seed_config.initial_register_regions == {}
    assert seed_config.entry_initial_states.keys() == {0x88, 0x90}
    assert seed_config.entry_register_regions[0x88]["a6"].context_name is None
    assert seed_config.entry_register_regions[0x90]["a6"].provenance.derivation is not None
    assert seed_config.entry_register_regions[0x90]["a6"].provenance.derivation.named_base == "icon.library"
    assert seed_config.entry_initial_states[0x88].a[6].tag == LibraryBaseTag(
        library_base="exec.library",
        struct_name="LIB",
    )
    assert seed_config.entry_initial_states[0x90].a[6].tag == LibraryBaseTag(
        library_base="icon.library",
        struct_name="LIB",
    )


def test_build_entry_seed_config_synthesizes_autoinit_library_a6_by_entrypoint() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        resident=ResidentTargetMetadata(
            offset=4,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x44,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x44,
                base_size=0x24,
                vectors_offset=0x54,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x88,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 37.1",
            version=37,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    seed_config = build_entry_seed_config(metadata)

    assert seed_config.initial_state is None
    assert seed_config.initial_register_regions == {}
    assert seed_config.entry_initial_states.keys() == {0x88, 0x90}
    assert seed_config.entry_register_regions[0x88]["a6"].context_name is None
    assert seed_config.entry_register_regions[0x90]["a6"].provenance.derivation is not None
    assert seed_config.entry_register_regions[0x90]["a6"].provenance.derivation.named_base == "icon.library"
    assert seed_config.entry_initial_states[0x88].a[6].tag == LibraryBaseTag(
        library_base="exec.library",
        struct_name="LIB",
    )
    assert seed_config.entry_initial_states[0x90].a[6].tag == LibraryBaseTag(
        library_base="icon.library",
        struct_name="LIB",
    )


def test_decode_stream_by_name_decodes_autoinit_commands() -> None:
    code = bytes.fromhex(
        "e0 00 00 08 09 00"
        "c0 00 00 0a 00 00 00 18"
        "00"
    ) + b"dos.library\x00"

    spec = runtime_os.META.typed_data_stream_formats["exec.InitStruct"]
    stream = decode_stream_by_name(code, 0, runtime_os, "exec.InitStruct")

    assert stream is not None
    assert stream.end == 15
    assert len(stream.commands) == 2
    assert format_typed_data_stream_command(
        stream.commands[0],
        spec=spec,
        code=code,
        labels={0x18: "dos_name"},
        reloc_map={},
        reloc_labels={},
        structs=runtime_os.STRUCTS,
        struct_name="LIB",
    ) == "INITBYTE LN_TYPE,$09"
    assert format_typed_data_stream_command(
        stream.commands[1],
        spec=spec,
        code=code,
        labels={0x18: "dos_name"},
        reloc_map={10: 0x18},
        reloc_labels={10: "dos_name"},
        structs=runtime_os.STRUCTS,
        struct_name="LIB",
    ) == "INITLONG LN_NAME,dos_name"


def test_emit_target_structure_rows_filters_library_exports_by_library_version() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2",
            version=34,
            public_function_count=8,
            total_lvo_count=18,
        ),
    )
    session = DisassemblySession(
        target_name="icon34",
        binary_path=Path("icon.library"),
        entities_path=Path("entities.jsonl"),
        analysis_cache_path=Path("binary.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[],
        target_metadata=metadata,
        source_kind="hunk_file",
    )

    rendered = render_rows(emitter_mod._emit_target_structure_rows(session))

    assert (
        ";   exports: BumpRevision, MatchToolValue, FindToolType, FreeDiskObject, "
        "PutDiskObject, GetDiskObject, AddFreeList, FreeFreeList\n"
    ) in rendered
    assert "GetDiskObjectNew" not in rendered
    assert "DeleteDiskObject" not in rendered


def test_emit_target_structure_rows_dedupes_library_entry_register_notes() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x148,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x0DC,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x0EA,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    session = DisassemblySession(
        target_name="icon.library",
        binary_path=Path("bin/icon.library"),
        entities_path=Path("targets/icon/entities.jsonl"),
        analysis_cache_path=Path("targets/icon/binary.analysis"),
        output_path=None,
        hunk_sessions=[],
        entities=[],
        target_metadata=metadata,
    )

    rendered = "".join(row.text for row in emitter_mod._emit_target_structure_rows(session))

    assert ";   entry registers:" not in rendered
    assert "GetDefDiskObject" not in rendered
    assert "PutDefDiskObject" not in rendered


def test_emit_target_structure_rows_shows_synthesized_library_entry_register_notes() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=34,
            node_type_name="NT_LIBRARY",
            priority=70,
            name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            init_offset=0x48,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x48,
                base_size=0x24,
                vectors_offset=0x58,
                vector_format="offset32",
                vector_offsets=(0xDC, 0xEA, 0x100, 0x144),
                init_struct_offset=0,
                init_func_offset=0x148,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    session = DisassemblySession(
        target_name="icon.library",
        binary_path=Path("bin/icon.library"),
        entities_path=Path("targets/icon/entities.jsonl"),
        analysis_cache_path=Path("targets/icon/binary.analysis"),
        output_path=None,
        hunk_sessions=[],
        entities=[],
        target_metadata=metadata,
    )

    rendered = "".join(row.text for row in emitter_mod._emit_target_structure_rows(session))

    assert ";   entry registers:" not in rendered


def test_emit_session_rows_emits_entry_register_notes_at_entry_labels() -> None:
    inst = Instruction(
        offset=0x0,
        size=2,
        opcode=0x4E75,
        text="rts",
        raw=b"\x4e\x75",
        opcode_text="rts",
        kb_mnemonic="rts",
        operand_size="l",
        operand_texts=(),
    )
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x0,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x0,
                register="D0",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
    )
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={0x0: _FakeBlock(0x0, 0x2, (), [inst])},
        hint_blocks={},
        code_addrs={0x0, 0x1},
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={0x0: "library_init"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    session = DisassemblySession(
        target_name="icon.library",
        binary_path=Path("bin/icon.library"),
        entities_path=Path("targets/icon/entities.jsonl"),
        analysis_cache_path=Path("targets/icon/binary.analysis"),
        output_path=None,
        hunk_sessions=[hunk_session],
        entities=[],
        target_metadata=metadata,
    )

    rendered = emitter_mod.render_session_text(session)

    assert "; entry registers: A6=ExecBase, D0=icon.library base\nlibrary_init:\n" in rendered


def test_target_structure_spec_filters_resident_library_vector_names_by_library_version() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=34,
            node_type_name="NT_LIBRARY",
            priority=70,
            name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            init_offset=0x48,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x48,
                base_size=0x24,
                vectors_offset=0x58,
                vector_format="offset32",
                vector_offsets=tuple(0x100 + (index * 2) for index in range(23)),
                init_struct_offset=0,
                init_func_offset=0x148,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    structure = target_structure_spec(metadata)

    assert structure is not None
    labels = [entry.label for entry in structure.entrypoints]
    assert "put_disk_object" in labels
    assert "bump_revision" in labels
    assert "get_def_disk_object" not in labels
    assert "put_def_disk_object" not in labels
    assert "get_disk_object_new" not in labels
    assert "delete_disk_object" not in labels
    assert "icon_private_8" in labels
    assert "icon_private_9" in labels
    assert "icon_private_10" in labels
    assert "icon_private_11" in labels


def test_effective_entry_register_seeds_include_kb_typed_vector_inputs() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=34,
            node_type_name="NT_LIBRARY",
            priority=70,
            name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            init_offset=0x48,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x48,
                base_size=0x24,
                vectors_offset=0x58,
                vector_format="offset32",
                vector_offsets=(
                    0x74, 0x78, 0x7C, 0x80, 0x84, 0x88, 0x8C, 0x90, 0x94,
                    0x98, 0x9C, 0xA0, 0xA4, 0xA8, 0xAC, 0xB0, 0xB4, 0xB8, 0xBC,
                ),
                init_struct_offset=0,
                init_func_offset=0xDC,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    seeds = effective_entry_register_seeds(metadata)

    assert any(
        seed.entry_offset == 0xDC
        and seed.register == "D0"
        and seed.kind == "library_base"
        and seed.library_name == "icon.library"
        and seed.struct_name == "LIB"
        for seed in seeds
    )
    assert any(
        seed.entry_offset == 0xA8
        and seed.register == "A1"
        and seed.kind == "struct_ptr"
        and seed.struct_name == "DiskObject"
        for seed in seeds
    )
    assert not any(
        seed.entry_offset == 0x74
        and seed.register == "D0"
        and seed.kind == "struct_ptr"
        for seed in seeds
    )


def test_effective_entry_register_seeds_merges_explicit_and_synthesized_resident_inputs() -> None:
    metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0xDC,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x74,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=34,
            node_type_name="NT_LIBRARY",
            priority=70,
            name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            init_offset=0x48,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x48,
                base_size=0x24,
                vectors_offset=0x58,
                vector_format="offset32",
                vector_offsets=(0x74,),
                init_struct_offset=0,
                init_func_offset=0xDC,
            ),
        ),
        library=LibraryTargetMetadata(
            library_name="icon.library",
            id_string="icon 34.2 (22 Jun 1988)\r\n",
            version=34,
            public_function_count=12,
            total_lvo_count=19,
        ),
    )

    seeds = effective_entry_register_seeds(metadata)

    assert any(
        seed.entry_offset == 0xDC
        and seed.register == "A6"
        and seed.library_name == "exec.library"
        for seed in seeds
    )
    assert any(
        seed.entry_offset == 0x74
        and seed.register == "A6"
        and seed.library_name == "icon.library"
        for seed in seeds
    )
    assert any(
        seed.entry_offset == 0xDC
        and seed.register == "D0"
        and seed.kind == "library_base"
        and seed.library_name == "icon.library"
        and seed.struct_name == "LIB"
        for seed in seeds
    )


def test_apply_named_base_struct_overrides_rewrites_seeded_register_regions() -> None:
    platform = make_platform()
    icon_region = TypedMemoryRegion(
        struct="LIB",
        size=runtime_os.STRUCTS["LIB"].size,
        provenance=provenance_named_base("icon.library"),
    )
    platform.entry_register_regions = {
        0x148: {
            "d0": icon_region,
            "a2": TypedMemoryRegion(
                struct="LIB",
                size=runtime_os.STRUCTS["LIB"].size,
                provenance=MemoryRegionProvenance(
                    address_space=MemoryRegionAddressSpace.REGISTER,
                ),
            ),
        }
    }
    platform.initial_register_regions = {"d0": icon_region}
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(),
        custom_structs=(
            CustomStructMetadata(
                name="InferredIconLibraryBase",
                size=46,
                fields=(
                    CustomStructFieldMetadata(
                        name="exec_library_base",
                        type="APTR",
                        offset=34,
                        size=4,
                        pointer_struct="LIB",
                    ),
                ),
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="test",
                base_struct="LIB",
                base_offset=runtime_os.STRUCTS["LIB"].size,
            ),
        ),
    )
    os_kb = build_target_local_os_kb(
        runtime_os,
        target_metadata,
        named_base_struct_overrides={"icon.library": "InferredIconLibraryBase"},
    )
    session_mod._apply_named_base_struct_overrides(platform, os_kb)

    assert platform.initial_register_regions["d0"].struct == "InferredIconLibraryBase"
    assert platform.entry_register_regions[0x148]["d0"].struct == "InferredIconLibraryBase"
    assert platform.entry_register_regions[0x148]["a2"].struct == "LIB"


def test_emit_session_rows_emits_initstruct_macros() -> None:
    code = bytes.fromhex(
        "e0 00 00 08 09 00"
        "c0 00 00 0a 00 00 00 18"
        "00"
    ) + b"dos.library\x00"
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=code,
        code_size=len(code),
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={10: 0x18},
        reloc_target_set={0x18},
        pc_targets={},
        string_addrs={0x18},
        labels={0: "resident_initstruct", 0x18: "dos_name"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        typed_data_sizes={},
        typed_data_fields={},
        addr_comments={},
        string_ranges={0x18: 0x24},
        dynamic_structured_regions=(
            StructuredRegionSpec(
                start=0,
                end=15,
                subtype="typed_data_stream",
                struct_name="LIB",
                stream_format="exec.InitStruct",
            ),
        ),
        absolute_labels={},
        reserved_absolute_addrs=set(),
        app_struct_regions={},
        hardware_base_regs={},
        unresolved_indirects={},
        lib_calls=(),
    )
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("targets/demo/binary.analysis"),
        output_path=None,
        hunk_sessions=[hunk_session],
        entities=[],
        target_metadata=None,
    )

    rendered = render_rows(emit_session_rows(session))

    assert '    INCLUDE "exec/initializers.i"\n' in rendered
    assert "    INITBYTE LN_TYPE,$09\n" in rendered
    assert "    INITLONG LN_NAME,dos_name\n" in rendered
    assert "    dc.b    $00\n" in rendered
    assert "resident_initstruct:\n" in rendered


def test_emit_hunk_rows_rewrites_struct_field_names_for_compatibility_floor() -> None:
    custom_struct = SimpleNamespace(
        source="exec/libraries.i",
        base_offset=0,
        base_offset_symbol=None,
        size=34,
        fields=(
            SimpleNamespace(
                name="LIB_OPENCOUNT",
                type="UWORD",
                offset=32,
                size=2,
                available_since="1.3",
                names_by_version={"1.3": "LIB_OPENCNT", "3.1": "LIB_OPENCOUNT"},
            ),
        ),
        available_since="1.3",
    )
    row = ListingRow(
        row_id="instruction:000000",
        kind="instruction",
        text="    move.w LIB_OPENCOUNT(a6),d0\n",
        addr=0,
        opcode_or_directive="move.w",
        operand_parts=(
            SemanticOperand(
                kind="struct_field",
                text="LIB_OPENCOUNT(a6)",
                base_register="a6",
                displacement=32,
                metadata=StructFieldOperandMetadata(
                    symbol="LIB_OPENCOUNT",
                    owner_struct="LIB",
                    field_symbol="LIB_OPENCOUNT",
                ),
            ),
            SemanticOperand(kind="register", text="d0", register="d0"),
        ),
        operand_text="LIB_OPENCOUNT(a6),d0",
    )

    rewritten = emitter_mod._apply_compatibility_field_names(
        [row],
        cast(HunkDisassemblySession, SimpleNamespace(
            os_kb=SimpleNamespace(STRUCTS={"LIB": custom_struct}),
        )),
        "1.3",
    )

    assert rewritten[0].text == "    move.w LIB_OPENCNT(a6),d0\n"
    assert rewritten[0].operand_text == "LIB_OPENCNT(a6),d0"


def test_build_disassembly_session_for_resident_library_uses_resident_init_entry(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "library"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "library.bin"
    binary_path.write_bytes(b"fake")
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0xA0,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x40,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x40,
                base_size=0x24,
                vectors_offset=0x50,
                vector_format="offset32",
                vector_offsets=(0xA0,),
                init_struct_offset=None,
                init_func_offset=0x90,
            ),
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    code = bytearray(0xA2)
    code[0:2] = bytes.fromhex("4afc")
    code[2:6] = (0).to_bytes(4, byteorder="big")
    code[6:10] = (0x42).to_bytes(4, byteorder="big")
    code[10] = 0x80
    code[11] = 37
    code[12] = 9
    code[14:18] = (0x20).to_bytes(4, byteorder="big")
    code[18:22] = (0x30).to_bytes(4, byteorder="big")
    code[22:26] = (0x40).to_bytes(4, byteorder="big")
    code[0x20:0x2D] = b"icon.library\x00"
    code[0x30:0x3A] = b"icon 37.1\x00"
    code[0x40:0x44] = (0x24).to_bytes(4, byteorder="big")
    code[0x44:0x48] = (0x50).to_bytes(4, byteorder="big")
    code[0x48:0x4C] = (0).to_bytes(4, byteorder="big")
    code[0x4C:0x50] = (0x90).to_bytes(4, byteorder="big")
    code[0x50:0x54] = (0xA0).to_bytes(4, byteorder="big")
    code[0x54:0x58] = (0xFFFFFFFF).to_bytes(4, byteorder="big", signed=False)
    code[0x90:0x92] = b"\x4e\x75"
    code[0xA0:0xA2] = b"\x4e\x75"

    def fake_parse(_data: bytes) -> SimpleNamespace:
        return SimpleNamespace(
            hunks=[
                Hunk(
                    index=0,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=len(code),
                    data=bytes(code),
                )
            ]
        )

    def fake_load_hunk_analysis(
        *,
        analysis_cache_path: Path,
        code: bytes,
        relocs: list[RelocLike],
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...],
        extra_entry_points: tuple[int, ...],
        seed_key: str,
        initial_state: object,
        entry_initial_states: object | None = None,
    ) -> SimpleNamespace:
        assert entry_points == (0x90, 0xA0)
        assert extra_entry_points == ()
        assert isinstance(entry_initial_states, dict)
        assert set(entry_initial_states) == {0x90, 0xA0}
        inst = disassemble(b"\x4e\x75")[0]
        inst.offset = 0x90
        block = BasicBlock(
            start=0x90,
            end=0x92,
            instructions=[inst],
            is_entry=True,
        )
        return SimpleNamespace(
            blocks={0x90: block},
            hint_blocks={},
            jump_tables=[],
            call_targets=set(),
            branch_targets=set(),
            lib_calls=[],
            os_kb=runtime_os,
            platform=make_platform(),
            exit_states={},
            relocated_segments=[],
            indirect_sites=[],
            xrefs=[],
        )

    monkeypatch.setattr("disasm.session.parse", fake_parse)
    monkeypatch.setattr("disasm.session.load_hunk_analysis", fake_load_hunk_analysis)

    rendered = render_session_text(build_disassembly_session(str(binary_path), str(entities_path)))

    assert "resident_matchword:\n" in rendered
    assert "resident_init_ptr:\n" in rendered
    assert "library_init:\n" in rendered
    assert "lib_open:\n" in rendered


def test_build_disassembly_session_keeps_resident_vector_blocks_before_init_entry(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "library"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "library.bin"
    binary_path.write_bytes(b"fake")
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x120,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x40,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x40,
                base_size=0x24,
                vectors_offset=0x50,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x120,
            ),
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    code = bytearray(0x122)
    code[0:2] = bytes.fromhex("4afc")
    code[2:6] = (0).to_bytes(4, byteorder="big")
    code[6:10] = (0x42).to_bytes(4, byteorder="big")
    code[10] = 0x80
    code[11] = 37
    code[12] = 9
    code[14:18] = (0x20).to_bytes(4, byteorder="big")
    code[18:22] = (0x30).to_bytes(4, byteorder="big")
    code[22:26] = (0x40).to_bytes(4, byteorder="big")
    code[0x20:0x2D] = b"icon.library\x00"
    code[0x30:0x3A] = b"icon 37.1\x00"
    code[0x40:0x44] = (0x24).to_bytes(4, byteorder="big")
    code[0x44:0x48] = (0x50).to_bytes(4, byteorder="big")
    code[0x48:0x4C] = (0).to_bytes(4, byteorder="big")
    code[0x4C:0x50] = (0x120).to_bytes(4, byteorder="big")
    code[0x50:0x54] = (0x90).to_bytes(4, byteorder="big")
    code[0x54:0x58] = (0xFFFFFFFF).to_bytes(4, byteorder="big", signed=False)
    code[0x90:0x92] = b"\x4e\x75"
    code[0x120:0x122] = b"\x4e\x75"

    def fake_parse(_data: bytes) -> SimpleNamespace:
        return SimpleNamespace(
            hunks=[
                Hunk(
                    index=0,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=len(code),
                    data=bytes(code),
                )
            ]
        )

    def fake_load_hunk_analysis(
        *,
        analysis_cache_path: Path,
        code: bytes,
        relocs: list[RelocLike],
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...],
        extra_entry_points: tuple[int, ...],
        seed_key: str,
        initial_state: object,
        entry_initial_states: object | None = None,
    ) -> SimpleNamespace:
        assert entry_points == (0x120, 0x90)
        vector_inst = disassemble(b"\x4e\x75")[0]
        vector_inst.offset = 0x90
        init_inst = disassemble(b"\x4e\x75")[0]
        init_inst.offset = 0x120
        vector_block = BasicBlock(
            start=0x90,
            end=0x92,
            instructions=[vector_inst],
            is_entry=True,
        )
        init_block = BasicBlock(
            start=0x120,
            end=0x122,
            instructions=[init_inst],
            is_entry=True,
        )
        return SimpleNamespace(
            blocks={0x90: vector_block, 0x120: init_block},
            hint_blocks={},
            jump_tables=[],
            call_targets={0x90, 0x120},
            branch_targets=set(),
            lib_calls=[],
            os_kb=runtime_os,
            platform=make_platform(),
            exit_states={},
            relocated_segments=[],
            indirect_sites=[],
            xrefs=[],
        )

    monkeypatch.setattr("disasm.session.parse", fake_parse)
    monkeypatch.setattr("disasm.session.load_hunk_analysis", fake_load_hunk_analysis)

    session = build_disassembly_session(str(binary_path), str(entities_path))
    rendered = render_session_text(session)

    assert 0x90 in session.hunk_sessions[0].blocks
    assert 0x120 in session.hunk_sessions[0].blocks
    assert "lib_open:\n" in rendered
    assert "library_init:\n" in rendered


def test_target_structure_spec_for_resident_library_starts_at_earliest_vector_entry() -> None:
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x120,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=0,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x40,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x40,
                base_size=0x24,
                vectors_offset=0x50,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x120,
            ),
        ),
    )
    structure = target_structure_spec(target_metadata)

    assert structure is not None
    assert structure.analysis_start_offset == 0x90
    assert tuple(entry.offset for entry in structure.entrypoints) == (0x120, 0x90)


def test_build_disassembly_session_applies_resident_structure_only_to_first_code_hunk(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "targets" / "library"
    target_dir.mkdir(parents=True)
    binary_path = target_dir / "library.bin"
    binary_path.write_bytes(b"fake")
    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("", encoding="utf-8")
    target_metadata = TargetMetadata(
        target_type="library",
        entry_register_seeds=(
            EntryRegisterSeedMetadata(
                entry_offset=0x88,
                register="A6",
                kind="library_base",
                note="ExecBase",
                library_name="exec.library",
                struct_name="LIB",
                context_name=None,
            ),
            EntryRegisterSeedMetadata(
                entry_offset=0x90,
                register="A6",
                kind="library_base",
                note="icon.library base",
                library_name="icon.library",
                struct_name="LIB",
                context_name=None,
            ),
        ),
        resident=ResidentTargetMetadata(
            offset=4,
            matchword=0x4AFC,
            flags=0x80,
            version=37,
            node_type_name="NT_LIBRARY",
            priority=0,
            name="icon.library",
            id_string="icon 37.1",
            init_offset=0x44,
            auto_init=True,
            autoinit=ResidentAutoinitMetadata(
                payload_offset=0x44,
                base_size=0x24,
                vectors_offset=0x54,
                vector_format="offset32",
                vector_offsets=(0x90,),
                init_struct_offset=None,
                init_func_offset=0x88,
            ),
        ),
    )
    (target_dir / "target_metadata.json").write_text(
        json.dumps(asdict(target_metadata), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    first_code = bytearray(0x92)
    first_code[4:6] = bytes.fromhex("4afc")
    first_code[6:10] = (4).to_bytes(4, byteorder="big")
    first_code[10:14] = (0x4A).to_bytes(4, byteorder="big")
    first_code[14] = 0x80
    first_code[15] = 37
    first_code[16] = 9
    first_code[18:22] = (0x20).to_bytes(4, byteorder="big")
    first_code[22:26] = (0x30).to_bytes(4, byteorder="big")
    first_code[26:30] = (0x44).to_bytes(4, byteorder="big")
    first_code[0x20:0x2D] = b"icon.library\x00"
    first_code[0x30:0x3A] = b"icon 37.1\x00"
    first_code[0x44:0x48] = (0x24).to_bytes(4, byteorder="big")
    first_code[0x48:0x4C] = (0x54).to_bytes(4, byteorder="big")
    first_code[0x4C:0x50] = (0).to_bytes(4, byteorder="big")
    first_code[0x50:0x54] = (0x88).to_bytes(4, byteorder="big")
    first_code[0x54:0x58] = (0x90).to_bytes(4, byteorder="big")
    first_code[0x58:0x5C] = (0xFFFFFFFF).to_bytes(4, byteorder="big", signed=False)
    first_code[0x88:0x8A] = b"\x4e\x75"
    first_code[0x90:0x92] = b"\x4e\x75"
    second_code = b"\x4e\x75" * 10

    def fake_parse(_data: bytes) -> SimpleNamespace:
        return SimpleNamespace(
            hunks=[
                Hunk(
                    index=0,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=len(first_code),
                    data=bytes(first_code),
                ),
                Hunk(
                    index=1,
                    hunk_type=int(HunkType.HUNK_CODE),
                    mem_type=int(MemType.ANY),
                    alloc_size=len(second_code),
                    data=second_code,
                ),
            ]
        )

    def fake_load_hunk_analysis(
        *,
        analysis_cache_path: Path,
        code: bytes,
        relocs: list[RelocLike],
        hunk_index: int,
        base_addr: int,
        code_start: int,
        entry_points: tuple[int, ...],
        extra_entry_points: tuple[int, ...],
        seed_key: str,
        initial_state: object,
        entry_initial_states: object | None = None,
    ) -> SimpleNamespace:
        if hunk_index == 0:
                assert entry_points == (0x88, 0x90)
                assert extra_entry_points == ()
                assert isinstance(entry_initial_states, dict)
                assert set(entry_initial_states) == {0x88, 0x90}
                inst = disassemble(b"\x4e\x75")[0]
                inst.offset = 0x88
                block = BasicBlock(
                    start=0x88,
                    end=0x8A,
                    instructions=[inst],
                    is_entry=True,
                )
                return SimpleNamespace(
                    blocks={0x88: block},
                hint_blocks={},
                jump_tables=[],
                call_targets=set(),
                branch_targets=set(),
                lib_calls=[],
                os_kb=runtime_os,
                platform=make_platform(),
                exit_states={},
                relocated_segments=[],
                indirect_sites=[],
                xrefs=[],
            )
        assert hunk_index == 1
        assert entry_points == ()
        assert extra_entry_points == ()
        assert entry_initial_states == {}
        inst = disassemble(b"\x4e\x75")[0]
        inst.offset = 0
        block = BasicBlock(
            start=0,
            end=2,
            instructions=[inst],
            is_entry=True,
        )
        return SimpleNamespace(
            blocks={0: block},
            hint_blocks={},
            jump_tables=[],
            call_targets=set(),
            branch_targets=set(),
            lib_calls=[],
            os_kb=runtime_os,
            platform=make_platform(),
            exit_states={},
            relocated_segments=[],
            indirect_sites=[],
            xrefs=[],
        )

    monkeypatch.setattr("disasm.session.parse", fake_parse)
    monkeypatch.setattr("disasm.session.load_hunk_analysis", fake_load_hunk_analysis)

    session = build_disassembly_session(str(binary_path), str(entities_path))
    rendered = render_session_text(session)

    assert rendered.count("resident_matchword:\n") == 1
    assert "resident_matchword" not in session.hunk_sessions[1].labels.values()
    assert "resident_init" not in session.hunk_sessions[1].labels.values()


def test_emit_session_rows_emits_fd_only_lvo_equates() -> None:
    session = DisassemblySession(
        target_name="demo_graphics",
        binary_path=Path("targets/demo_graphics/binary.bin"),
        entities_path=Path("targets/demo_graphics/entities.jsonl"),
        analysis_cache_path=Path("targets/demo_graphics/binary.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[
            HunkDisassemblySession(
                hunk_index=0,
                code=b"\x4e\x75",
                code_size=2,
                entities=[],
                blocks={
                    0: _FakeBlock(
                        start=0,
                        end=2,
                        successors=(),
                        instructions=[
                            _instruction(
                                offset=0,
                                raw=b"\x4e\x75",
                                mnemonic="rts",
                                operand_size="w",
                                operand_texts=(),
                            )
                        ],
                    )
                },
                hint_blocks={},
                code_addrs={0, 1},
                hint_addrs=set(),
                reloc_map={},
                reloc_target_set=set(),
                pc_targets={},
                string_addrs=set(),
                labels={0: "loc_0000"},
                jump_table_regions={},
                jump_table_target_sources={},
                region_map={},
                lvo_equs={"graphics.library": {-30: "_LVOBltBitMap"}},
                lvo_substitutions={},
                arg_equs={},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                data_access_sizes={},
                platform=make_platform(),
                os_kb=make_empty_os_kb(),
                base_addr=0,
                code_start=0,
                relocated_segments=[],
                reloc_file_offset=0,
                reloc_base_addr=0,
            )
        ],
        target_metadata=None,
    )

    rendered = "".join(row.text for row in emit_session_rows(session))

    assert "; LVO offsets: graphics.library (FD-derived)\n" in rendered
    assert "_LVOBltBitMap\tEQU\t-30\n" in rendered


def test_render_instruction_text_substitutes_field_domain_constant_for_trackdisk_io_command() -> None:
    inst = Instruction(
        offset=0x22,
        size=6,
        opcode=0x337C,
        text="move.w",
        raw=b"\x33\x7c\x00\x02\x00\x1c",
        opcode_text="move.w",
        kb_mnemonic="move",
        operand_size="w",
        operand_texts=("#$2", "$1c(a1)"),
    )
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=inst.raw,
        code_size=len(inst.raw),
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs={inst.offset},
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={
            inst.offset: {
                "a1": TypedMemoryRegion(
                    struct="IO",
                    size=runtime_os.STRUCTS["IO"].size,
                    provenance=MemoryRegionProvenance(
                        address_space=MemoryRegionAddressSpace.REGISTER,
                    ),
                    context_name="trackdisk.device",
                )
            }
        },
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    text, _comment, _parts = render_instruction_text(inst, hunk_session, set())

    assert text == "move.w #CMD_READ,IO_COMMAND(a1)"


def test_absolute_symbol_rows_emit_only_used_external_equ_and_hardware_includes() -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        absolute_labels={
            0x00000004: "AbsExecBase",
        },
    )
    rows = [
        ListingRow(
            row_id="instruction:000000",
            kind="instruction",
            text="",
            operand_parts=(
                SemanticOperand(
                    kind="absolute_target",
                    text="_custom+intena",
                    segment_addr=0x00DFF09A,
                ),
                SemanticOperand(kind="absolute_target", text="AbsExecBase", segment_addr=0x00000004),
                SemanticOperand(kind="absolute_target", text="_ciaa+ciapra", segment_addr=0x00BFE001),
                SemanticOperand(kind="absolute_target", text="$1234", segment_addr=0x00001234),
            ),
        )
    ]

    used = emitter_mod._collect_used_absolute_addrs(rows, hunk_session)
    equ_defs, includes = emitter_mod._absolute_symbol_defs(used, hunk_session)

    assert used == {0x00000004, 0x00DFF09A, 0x00BFE001}
    assert includes == {"hardware/cia.i", "hardware/custom.i"}
    assert equ_defs == {"AbsExecBase": 0x00000004}


def test_emit_hunk_rows_emits_fd_derived_lvo_equates(monkeypatch: MonkeyPatch) -> None:
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={"graphics.library": {-36: "_LVOText", -30: "_LVOBltBitMap"}},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    monkeypatch.setattr(
        emitter_mod,
        "_OS_INCLUDE_KB",
        SimpleNamespace(
            library_lvo_owners={
                "graphics.library": SimpleNamespace(
                    kind="fd_only",
                    include_path=None,
                    comment_include_path="graphics/graphics_lib.i",
                    source_file="FD/GRAPHICS_LIB.FD",
                )
            }
        ),
    )

    rows, _compat_floor, preamble = emitter_mod._emit_hunk_rows(hunk_session, include_header=False)

    assert [row.text for row in rows[:2]] == [
        "    section code,code\n",
        "\n",
    ]
    assert preamble["fd_only_lvo_equs"] == {
        "graphics.library": {
            -36: "_LVOText",
            -30: "_LVOBltBitMap",
        }
    }


def test_emit_session_rows_dedupes_preamble_before_first_hunk() -> None:
    hunk0 = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        reloc_target_hunks={},
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=build_target_local_os_kb(
            runtime_os,
            extra_custom_structs=(
                CustomStructMetadata(
                    name="InferredIconLibraryBase",
                    size=46,
                    fields=(
                        CustomStructFieldMetadata(
                            name="exec_library_base",
                            type="APTR",
                            offset=34,
                            size=4,
                            pointer_struct="ExecBase",
                            named_base="exec.library",
                        ),
                    ),
                    seed_origin="manual_analysis",
                    review_status="seeded",
                    citation="test",
                    base_struct="LIB",
                    base_offset=runtime_os.STRUCTS["LIB"].size,
                ),
            ),
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        lvo_equs={"exec.library": {-198: "_LVOAllocMem"}},
        region_map={
            0x100: {
                "a2": TypedMemoryRegion(
                    struct="InferredIconLibraryBase",
                    size=46,
                    provenance=provenance_named_base("icon.library"),
                )
            }
        },
    )
    hunk1 = replace(
        hunk0,
        hunk_index=1,
    )
    rendered = emitter_mod.render_session_text(
        DisassemblySession(
            target_name="demo",
            binary_path=Path("demo.bin"),
            entities_path=Path("entities.jsonl"),
            analysis_cache_path=Path("analysis"),
            output_path=None,
            entities=[],
            hunk_sessions=[hunk0, hunk1],
        )
    )

    assert rendered.count('    INCLUDE "exec/exec_lib.i"\n') == 1
    assert rendered.count("exec_library_base\tEQU\t34\n") == 1
    first_section = rendered.index("    section code,code\n")
    assert rendered.index('    INCLUDE "exec/exec_lib.i"\n') < first_section
    assert rendered.index("exec_library_base\tEQU\t34\n") < first_section


def test_serialize_row_preserves_structured_fields() -> None:
    row = ListingRow(
        row_id="row0",
        kind="instruction",
        text="    moveq #0,d0\n",
        addr=0x20,
        entity_addr=0x20,
        verified_state="verified",
        bytes=b"\x70\x00",
        label="entry_point",
        opcode_or_directive="moveq",
        operand_parts=(
            SemanticOperand(kind="immediate", text="#0", value=0),
            SemanticOperand(kind="register", text="d0", register="d0"),
        ),
        operand_text="#0,d0",
        comment_parts=("note",),
        comment_text="note",
        source_context=AddressRowContext(block=0x20),
    )

    payload = serialize_row(row)

    assert payload["row_id"] == "row0"
    assert payload["bytes"] == "7000"
    assert payload["operand_parts"][0]["kind"] == "immediate"
    assert payload["source_context"] == {"block": 0x20}


def test_session_metadata_summarizes_hunks() -> None:
    block = _block(0, 2)
    session = DisassemblySession(
        target_name="test",
        binary_path=Path("bin/test"),
        entities_path=Path("targets/test/entities.jsonl"),
        analysis_cache_path=Path("bin/test.analysis"),
        output_path=Path("targets/test/out.s"),
        entities=[{"addr": "0000", "type": "code"}],
        hunk_sessions=[
            HunkDisassemblySession(
                hunk_index=0,
                code=b"\x4e\x75",
                code_size=2,
                entities=[{"addr": "0000", "type": "code"}],
                blocks={0: block},
                hint_blocks={},
                code_addrs={0, 1},
                hint_addrs=set(),
                reloc_map={},
                reloc_target_set=set(),
                pc_targets={},
                string_addrs=set(),
                labels={0: "entry_point"},
                jump_table_regions={},
                jump_table_target_sources={},
                region_map={},
                lvo_equs={},
                lvo_substitutions={},
                arg_equs={},
                arg_substitutions={},
                app_offsets={},
                arg_annotations={},
                data_access_sizes={},
                platform=make_platform(),
                os_kb=make_empty_os_kb(),
                base_addr=0,
                code_start=0,
                relocated_segments=[],
                reloc_file_offset=0,
                reloc_base_addr=0,
            )
        ],
    )

    payload = session_metadata(session)

    assert payload["target_name"] == "test"
    assert payload["entity_count"] == 1
    assert payload["hunk_count"] == 1
    assert payload["hunks"][0]["label_count"] == 1
    assert payload["hunks"][0]["relocated"] is False


def test_listing_window_payload_serializes_rows() -> None:
    rows = [
        ListingRow(row_id="r0", kind="instruction", text="a\n", addr=0x10),
        ListingRow(row_id="r1", kind="instruction", text="b\n", addr=0x20),
        ListingRow(row_id="r2", kind="instruction", text="c\n", addr=0x30),
    ]

    payload = listing_window_payload(rows, 0x20, before=0, after=1)

    assert payload["anchor_addr"] == 0x20
    assert [row["row_id"] for row in payload["rows"]] == ["r1", "r2"]
    assert payload["has_more_before"] is True
    assert payload["has_more_after"] is False


def test_build_listing_rows_delegates_to_session_builder(monkeypatch: MonkeyPatch) -> None:
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[],
    )
    rows: list[ListingRow] = [ListingRow(row_id="r0", kind="instruction", text="nop\n", addr=0)]
    calls: list[str] = []

    def fake_build(
        binary_path: str,
        entities_path: str,
        output_path: str | None,
        base_addr: int = 0,
        code_start: int = 0,
        profile_stages: bool = False,
    ) -> DisassemblySession:
        calls.append("build")
        assert binary_path == "bin/demo"
        assert entities_path == "targets/demo/entities.jsonl"
        assert output_path is None
        assert base_addr == 0x400
        assert code_start == 2
        return session

    def fake_emit(seen_session: DisassemblySession) -> list[ListingRow]:
        calls.append("emit")
        assert seen_session is session
        return rows

    monkeypatch.setattr(emitter_mod, "build_disassembly_session", fake_build)
    monkeypatch.setattr(emitter_mod, "emit_session_rows", fake_emit)

    result = emitter_mod.build_listing_rows("bin/demo", "targets/demo/entities.jsonl",
                                            base_addr=0x400, code_start=2)

    assert calls == ["build", "emit"]
    assert result == rows


def test_render_session_text_renders_emitted_rows(monkeypatch: MonkeyPatch) -> None:
    session = DisassemblySession(
        target_name="demo",
        binary_path=Path("bin/demo"),
        entities_path=Path("targets/demo/entities.jsonl"),
        analysis_cache_path=Path("bin/demo.analysis"),
        output_path=None,
        entities=[],
        hunk_sessions=[],
    )
    rows: list[ListingRow] = [ListingRow(row_id="r0", kind="instruction", text="moveq #0,d0\n", addr=0)]
    calls: list[str] = []

    def fake_emit(seen_session: DisassemblySession) -> list[ListingRow]:
        calls.append("emit")
        assert seen_session is session
        return rows

    def fake_render(seen_rows: list[ListingRow]) -> str:
        calls.append("render")
        assert seen_rows == rows
        return "; rendered\n"

    monkeypatch.setattr(emitter_mod, "emit_session_rows", fake_emit)
    monkeypatch.setattr(emitter_mod, "render_rows", fake_render)

    assert emitter_mod.render_session_text(session) == "; rendered\n"
    assert calls == ["emit", "render"]


def test_emit_data_region_renders_relocated_longword_label() -> None:
    output = io.StringIO()

    data_render_mod.emit_data_region(
        output,
        code=b"\x00\x00\x00\x20",
        start=0,
        end=4,
        labels={0x20: "target_label"},
        reloc_map={0: 0x20},
        string_addrs=set(),
    )

    assert output.getvalue() == "    dc.l    target_label\n"


def test_emit_data_region_renders_cross_hunk_relocated_longword_label() -> None:
    output = io.StringIO()

    data_render_mod.emit_data_region(
        output,
        code=b"\x00\x00\x00\x20",
        start=0,
        end=4,
        labels={},
        reloc_map={0: 0x20},
        string_addrs=set(),
        reloc_labels={0: "hunk_3_sub_0020"},
    )

    assert output.getvalue() == "    dc.l    hunk_3_sub_0020\n"


def test_build_hunk_metadata_excludes_cross_hunk_reloc_targets_from_local_labels() -> None:
    metadata = build_hunk_metadata(
        code=(0x03FE).to_bytes(4, "big"),
        code_size=4,
        hunk_index=0,
        hunk_entities=[],
        ha=SimpleNamespace(
            blocks={},
            hint_blocks={},
            jump_tables=[],
            call_targets=set(),
            branch_targets=set(),
        ),
        hf_hunks=[
            Hunk(
                index=0,
                hunk_type=int(HunkType.HUNK_CODE),
                mem_type=int(MemType.ANY),
                alloc_size=4,
                data=(0x03FE).to_bytes(4, "big"),
                relocs=[
                    Reloc(
                        reloc_type=HunkType.HUNK_RELOC32,
                        target_hunk=1,
                        offsets=(0,),
                    )
                ],
            )
        ],
    )

    assert metadata.reloc_target_hunks == {0: 1}
    assert metadata.reloc_target_set == set()
    assert 0x03FE not in metadata.labels


def test_session_cross_hunk_labels_are_synthesized_and_uniquified() -> None:
    source = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0x40,
        entities=[],
        blocks={0x0000: _block(0x0000, 0x0002)},
        hint_blocks={},
        code_addrs={0x0000, 0x0001},
        hint_addrs=set(),
        reloc_map={0x0014: 0x0000, 0x003E: 0x0018},
        reloc_target_set=set(),
        reloc_target_hunks={0x0014: 1, 0x003E: 1},
        pc_targets={},
        string_addrs=set(),
        labels={0x0000: "loc_0000"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    target = HunkDisassemblySession(
        hunk_index=1,
        code=b"",
        code_size=0x40,
        entities=[],
        blocks={0x0000: _block(0x0000, 0x0002), 0x0018: _block(0x0018, 0x001A)},
        hint_blocks={},
        code_addrs={0x0000, 0x0001, 0x0018, 0x0019},
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        reloc_target_hunks={},
        pc_targets={},
        string_addrs=set(),
        labels={0x0000: "loc_0000"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=make_empty_os_kb(),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    session_mod._ensure_cross_hunk_target_labels([source, target])
    session_mod._apply_session_unique_labels([source, target])
    session_mod._apply_cross_hunk_reloc_labels([source, target])

    assert source.labels[0x0000] == "hunk_0_loc_0000"
    assert target.labels[0x0000] == "hunk_1_loc_0000"
    assert target.labels[0x0018] == "loc_0018"
    assert source.reloc_labels == {
        0x0014: "hunk_1_loc_0000",
        0x003E: "loc_0018",
    }


def test_refresh_session_memory_cells_propagates_named_base_across_hunks() -> None:
    store_inst = disassemble(assemble_instruction("move.l a6,$00000192"))[0]
    load_inst = disassemble(b"\x2c\x79\x00\x00\x01\x92")[0]
    call_inst = disassemble(b"\x4e\xae\xff\x3a")[0]

    exec_region = TypedMemoryRegion(
        struct="ExecBase",
        size=runtime_os.STRUCTS["ExecBase"].size,
        provenance=provenance_named_base("exec.library"),
    )
    source_blocks: dict[int, DisasmBlockLike] = {0: _block(0, len(store_inst.raw))}
    source = HunkDisassemblySession(
        hunk_index=0,
        code=store_inst.raw,
        code_size=len(store_inst.raw),
        entities=[],
        blocks=source_blocks,
        hint_blocks={},
        code_addrs=set(range(len(store_inst.raw))),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        reloc_target_hunks={},
        pc_targets={},
        string_addrs=set(),
        labels={0: "store_exec_base"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={0: {"a6": exec_region}},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    source_blocks[0] = replace(cast(_FakeBlock, source_blocks[0]), instructions=[store_inst])

    target_block = _FakeBlock(
        start=0,
        end=len(load_inst.raw) + len(call_inst.raw),
        successors=(),
        instructions=[load_inst, replace(call_inst, offset=len(load_inst.raw))],
    )
    target = HunkDisassemblySession(
        hunk_index=1,
        code=load_inst.raw + call_inst.raw,
        code_size=len(load_inst.raw) + len(call_inst.raw),
        entities=[],
        blocks={0: target_block},
        hint_blocks={},
        code_addrs=set(range(len(load_inst.raw) + len(call_inst.raw))),
        hint_addrs=set(),
        reloc_map={2: 0x0192},
        reloc_target_set={0x0192},
        reloc_target_hunks={2: 0},
        pc_targets={},
        string_addrs=set(),
        labels={0: "target_entry", 0x0192: "sub_0192"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
        lib_calls=(LibraryCall(
            addr=len(load_inst.raw),
            block=0,
            library="unknown",
            function="LVO_-198",
            lvo=-198,
        ),),
    )

    session_mod._refresh_session_memory_cells([source, target])

    assert source.labels[0x0192] == "exec_library_base"
    derivation = target.region_map[len(load_inst.raw)]["a6"].provenance.derivation
    assert derivation is not None
    assert derivation.named_base == "exec.library"
    assert target.lib_calls[0].library == "exec.library"
    assert target.lib_calls[0].function == "AllocMem"


def test_refresh_session_memory_cells_propagates_typed_field_across_hunks() -> None:
    store_inst = disassemble(assemble_instruction("move.w 20(a2),$00000180"))[0]

    code = bytearray(0x182)
    code[0x180:0x182] = b"\x00\x22"
    target = HunkDisassemblySession(
        hunk_index=1,
        code=bytes(code),
        code_size=len(code),
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        reloc_target_hunks={},
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    source_blocks: dict[int, DisasmBlockLike] = {0: _block(0, len(store_inst.raw))}
    source = HunkDisassemblySession(
        hunk_index=0,
        code=store_inst.raw,
        code_size=len(store_inst.raw),
        entities=[],
        blocks=source_blocks,
        hint_blocks={},
        code_addrs=set(range(len(store_inst.raw))),
        hint_addrs=set(),
        reloc_map={4: 0x0180},
        reloc_target_set=set(),
        reloc_target_hunks={4: 1},
        pc_targets={},
        string_addrs=set(),
        labels={0: "store_version"},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={
            0: {
                    "a2": TypedMemoryRegion(
                        struct="LIB",
                        size=runtime_os.STRUCTS["LIB"].size,
                        provenance=provenance_named_base("icon.library"),
                        context_name="icon.library",
                    )
                }
            },
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    source_blocks[0] = replace(cast(_FakeBlock, source_blocks[0]), instructions=[store_inst])

    session_mod._refresh_session_memory_cells([source, target])

    assert target.typed_data_sizes[0x0180] == 2
    assert target.typed_data_fields[0x0180] == TypedDataFieldInfo(
        owner_struct="LIB",
        field_symbol="LIB_VERSION",
        context_name="icon.library",
    )
    assert target.addr_comments[0x0180] == "LIB.LIB_VERSION"


def test_refresh_session_memory_cells_normalizes_session_os_kb() -> None:
    source = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        reloc_target_hunks={},
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=build_target_local_os_kb(
            runtime_os,
            extra_custom_structs=(
                CustomStructMetadata(
                    name="InferredIconLibraryBase",
                    size=46,
                    fields=(
                        CustomStructFieldMetadata(
                            name="exec_library_base",
                            type="APTR",
                            offset=34,
                            size=4,
                            pointer_struct="ExecBase",
                            named_base="exec.library",
                        ),
                    ),
                    seed_origin="manual_analysis",
                    review_status="seeded",
                    citation="test",
                    base_struct="LIB",
                    base_offset=runtime_os.STRUCTS["LIB"].size,
                ),
            ),
            named_base_struct_overrides={"icon.library": "InferredIconLibraryBase"},
        ),
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )
    target = HunkDisassemblySession(
        hunk_index=1,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        reloc_target_hunks={},
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={},
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=runtime_os,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    session_mod._refresh_session_memory_cells([source, target])

    assert source.os_kb is target.os_kb
    assert "InferredIconLibraryBase" in target.os_kb.STRUCTS
    assert target.os_kb.META.named_base_structs["icon.library"] == "InferredIconLibraryBase"


def test_cross_hunk_control_entrypoints_collects_inbound_jsr_targets() -> None:
    source = Hunk(
        index=0,
        hunk_type=int(HunkType.HUNK_CODE),
        mem_type=int(MemType.ANY),
        alloc_size=6,
        data=b"\x4e\xb9\x00\x00\x00\x08",
        relocs=[
            Reloc(
                reloc_type=HunkType.HUNK_RELOC32,
                target_hunk=1,
                offsets=(2,),
            )
        ],
    )
    target = Hunk(
        index=1,
        hunk_type=int(HunkType.HUNK_CODE),
        mem_type=int(MemType.ANY),
        alloc_size=16,
        data=b"\x4e\x75" + b"\x00" * 14,
    )

    assert session_mod._cross_hunk_control_entrypoints([source, target]) == {1: (0x0008,)}


def test_disambiguate_generated_label_avoids_app_offset_collision() -> None:
    assert (
        session_mod._disambiguate_generated_label(
            labels={},
            app_offsets={0x22: "exec_library_base"},
            os_kb=runtime_os,
            addr=0x018E,
            symbol="exec_library_base",
        )
        == "exec_library_base_ptr"
    )


def test_rename_reserved_generated_labels_avoids_target_local_field_collision() -> None:
    os_kb = build_target_local_os_kb(
        runtime_os,
        extra_custom_structs=(
            CustomStructMetadata(
                name="InferredIconLibraryBase",
                size=46,
                fields=(
                    CustomStructFieldMetadata(
                        name="exec_library_base",
                        type="APTR",
                        offset=34,
                        size=4,
                        pointer_struct="ExecBase",
                        named_base="exec.library",
                    ),
                ),
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="test",
                base_struct="LIB",
                base_offset=runtime_os.STRUCTS["LIB"].size,
            ),
        ),
        named_base_struct_overrides={"icon.library": "InferredIconLibraryBase"},
    )
    labels = {0x0192: "exec_library_base"}

    session_mod._rename_reserved_generated_labels(
        labels=labels,
        entities=[],
        app_offsets={},
        os_kb=os_kb,
    )

    assert labels[0x0192] == "exec_library_base_ptr"


def test_target_local_struct_equ_rows_emit_custom_field_offsets() -> None:
    os_kb = build_target_local_os_kb(
        runtime_os,
        extra_custom_structs=(
            CustomStructMetadata(
                name="InferredIconLibraryBase",
                size=46,
                fields=(
                    CustomStructFieldMetadata(
                        name="exec_library_base",
                        type="APTR",
                        offset=34,
                        size=4,
                        pointer_struct="ExecBase",
                        named_base="exec.library",
                    ),
                ),
                seed_origin="manual_analysis",
                review_status="seeded",
                citation="test",
                base_struct="LIB",
                base_offset=runtime_os.STRUCTS["LIB"].size,
            ),
        ),
        named_base_struct_overrides={"icon.library": "InferredIconLibraryBase"},
    )
    hunk_session = HunkDisassemblySession(
        hunk_index=0,
        code=b"",
        code_size=0,
        entities=[],
        blocks={},
        hint_blocks={},
        code_addrs=set(),
        hint_addrs=set(),
        reloc_map={},
        reloc_target_set=set(),
        reloc_target_hunks={},
        pc_targets={},
        string_addrs=set(),
        labels={},
        jump_table_regions={},
        jump_table_target_sources={},
        region_map={
            0x100: {
                "a2": TypedMemoryRegion(
                    struct="InferredIconLibraryBase",
                    size=46,
                    provenance=provenance_named_base("icon.library"),
                )
            }
        },
        lvo_equs={},
        lvo_substitutions={},
        arg_equs={},
        arg_substitutions={},
        app_offsets={},
        arg_annotations={},
        data_access_sizes={},
        platform=make_platform(),
        os_kb=os_kb,
        base_addr=0,
        code_start=0,
        relocated_segments=[],
        reloc_file_offset=0,
        reloc_base_addr=0,
    )

    equs = emitter_mod._target_local_struct_equ_defs(hunk_session)

    assert equs == {"exec_library_base": 34}


def test_emit_data_region_renders_zero_fill_run() -> None:
    output = io.StringIO()

    data_render_mod.emit_data_region(
        output,
        code=b"\x00\x00\x00\x00\x00",
        start=0,
        end=5,
        labels={},
        reloc_map={},
        string_addrs=set(),
    )

    assert output.getvalue() == "    dcb.b   5,0\n"


def test_emit_data_region_renders_ascii_string() -> None:
    output = io.StringIO()

    data_render_mod.emit_data_region(
        output,
        code=b"TEST\x00",
        start=0,
        end=5,
        labels={},
        reloc_map={},
        string_addrs={0},
    )

    assert output.getvalue() == '    dc.b    "TEST",0\n'

