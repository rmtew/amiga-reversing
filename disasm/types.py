from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SemanticOperand:
    kind: str
    text: str
    value: int | None = None
    register: str | None = None
    base_register: str | None = None
    displacement: int | None = None
    target_addr: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ListingRow:
    row_id: str
    kind: str
    text: str
    addr: int | None = None
    entity_addr: int | None = None
    verified_state: str | None = None
    bytes: bytes | None = None
    label: str | None = None
    opcode_or_directive: str | None = None
    operand_parts: tuple[SemanticOperand, ...] = ()
    operand_text: str = ""
    comment_parts: tuple[str, ...] = ()
    comment_text: str = ""
    source_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class HunkDisassemblySession:
    hunk_index: int
    code: bytes
    code_size: int
    entities: list[dict]
    blocks: dict
    hint_blocks: dict
    code_addrs: set[int]
    hint_addrs: set[int]
    reloc_map: dict[int, int]
    reloc_target_set: set[int]
    pc_targets: dict[int, str]
    string_addrs: set[int]
    core_absolute_targets: set[int]
    labels: dict[int, str]
    jump_table_regions: dict[int, dict]
    jump_table_target_sources: dict[int, list[str]]
    struct_map: dict[int, dict]
    lvo_equs: dict[str, dict[int, str]]
    lvo_substitutions: dict[int, tuple[str, str]]
    arg_equs: dict[str, int]
    arg_substitutions: dict[int, tuple[str, str]]
    app_offsets: dict[int, str]
    arg_annotations: dict[int, dict]
    data_access_sizes: dict[int, int]
    platform: dict
    os_kb: dict
    kb: Any
    fixed_abs_addrs: set[int]
    base_addr: int
    code_start: int
    relocated_segments: list[dict]
    reloc_file_offset: int
    reloc_base_addr: int


@dataclass
class DisassemblySession:
    target_name: str | None
    binary_path: Path
    entities_path: Path
    analysis_cache_path: Path
    output_path: Path | None
    entities: list[dict]
    hunk_sessions: list[HunkDisassemblySession]
    profile_stages: bool = False

