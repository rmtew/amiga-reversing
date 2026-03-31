# ruff: noqa: F401
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
from disasm.assembler_profiles import load_assembler_profile
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
    _refresh_library_call_signatures,
    build_disassembly_session,
)
from disasm.substitutions import build_arg_substitutions, build_lvo_substitutions
from disasm.target_metadata import (
    BootBlockTargetMetadata,
    CustomStructFieldMetadata,
    CustomStructMetadata,
    EntryRegisterSeedMetadata,
    ExecutionViewMetadata,
    LibraryTargetMetadata,
    ResidentTargetMetadata,
    SeededCodeEntrypointMetadata,
    SeededCodeLabelMetadata,
    StructuredFieldSpec,
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


def _test_include_owner() -> runtime_os.OsIncludeOwner:
    return runtime_os.OsIncludeOwner(
        kind="native_include",
        canonical_include_path="test/test.i",
        assembler_include_path="test/test.i",
        source_file="test/test.i",
    )


def _test_constant(raw: str, value: int | None) -> runtime_os.OsConstant:
    return runtime_os.OsConstant(raw=raw, value=value, owner=_test_include_owner())


def _test_library(functions: dict[str, runtime_os.OsFunction]) -> runtime_os.OsLibrary:
    return runtime_os.OsLibrary(
        owner=_test_include_owner(),
        lvo_index={},
        functions=functions,
    )

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


__all__ = [name for name in globals() if not name.startswith("__")]
