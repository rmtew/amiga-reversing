from __future__ import annotations

import argparse
import concurrent.futures
import functools
import hashlib
import json
import os
import re
import tempfile
import threading
import zlib
from pathlib import Path
from typing import Any, cast

from amiga_reversing.disasm.binary_source import (
    DiskEntryBinarySource,
    HunkFileBinarySource,
    RawBinarySource,
    resolve_target_binary_source,
)
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from src.scripts import amiga_hardware_usage
from src.scripts.platform_manifest_io import (
    ROOT,
    load_disk_image_bytes,
    read_jsonl_manifest,
    reconstruct_file_bytes,
    sha256,
    write_jsonl_manifest,
)

DEFAULT_DISK_MANIFEST = ROOT / "corpus" / "platform_disk_manifest.jsonl"
DEFAULT_FILE_MANIFEST = ROOT / "corpus" / "platform_file_manifest.jsonl"
DEFAULT_OUTPUT = ROOT / "corpus" / "target_usage_manifest.jsonl"
DEFAULT_XREF_OUTPUT = ROOT / "corpus" / "target_usage_xrefs.jsonl"
DEFAULT_SNIPPET_ROWS_OUTPUT = ROOT / "corpus" / "target_usage_snippet_rows"
DEFAULT_VARIANT_OUTPUT = ROOT / "corpus" / "target_variant_index.jsonl"
DEFAULT_TYPE_FLOW_REPORT_OUTPUT = ROOT / "corpus" / "target_type_flow_report.jsonl"
DEFAULT_UNRESOLVED_TYPED_FIELD_REPORT_OUTPUT = ROOT / "corpus" / "target_unresolved_typed_fields.jsonl"
DEFAULT_TYPE_FLOW_SNAPSHOT_DIR = ROOT / "corpus" / "type_flow_snapshots"
DEFAULT_TYPE_FLOW_BASELINE = ROOT / "src" / "tests" / "fixtures" / "type_flow_baseline.json"
TARGET_USAGE_WORKERS_ENV = "AMIGA_TARGET_USAGE_WORKERS"
MAX_EXAMPLES = 5
CPU_NAMES = {
    0: "68000",
    1: "68010",
    2: "68020",
    3: "68030",
    4: "68040",
    5: "68060",
}
PLATFORM_EFFECT_NAMES = {
    1: "set_base_reg",
    2: "write_base_slot",
    3: "set_code_ptr_reg",
    4: "set_typed_reg",
    5: "write_typed_slot",
    6: "write_global_base_slot",
    7: "write_typed_global_slot",
}
PLATFORM_EFFECT_WRITE_BASE_SLOT = 2
PLATFORM_EFFECT_SET_TYPED_REG = 4
PLATFORM_EFFECT_WRITE_TYPED_SLOT = 5
PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT = 6
PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT = 7
PLATFORM_STORAGE_EFFECT_MEMORY_KIND_NAMES = {
    PLATFORM_EFFECT_WRITE_BASE_SLOT: "base_slot",
    PLATFORM_EFFECT_WRITE_TYPED_SLOT: "typed_slot",
    PLATFORM_EFFECT_WRITE_GLOBAL_BASE_SLOT: "global_base_slot",
    PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT: "typed_global_slot",
}
DATA_ROLE_COPPER_LIST = 1 << 0
DATA_ROLE_PALETTE = 1 << 1
DATA_ROLE_POINTER_TABLE = 1 << 2
DATA_ROLE_LOOKUP_TABLE = 1 << 3
DATA_ROLE_LENGTH_PREFIXED_STRING = 1 << 4
DATA_ROLE_BITMAP = 1 << 5
DATA_ROLE_SOUND_SAMPLE = 1 << 6
DATA_ROLE_STRING = 1 << 7
DATA_ROLE_AUDIO_TABLE = 1 << 8
DATA_ROLE_BLITTER_DESTINATION = 1 << 9
DATA_ROLE_BLITTER_SOURCE = 1 << 10
DATA_ROLE_DISK_BUFFER = 1 << 11
DATA_ROLE_SPRITE = 1 << 12
DATA_ROLE_STRING_CONTROL_STREAM = 1 << 13
DATA_ROLE_NAMES = (
    (DATA_ROLE_STRING | DATA_ROLE_LENGTH_PREFIXED_STRING, "length_prefixed_string"),
    (DATA_ROLE_COPPER_LIST, "copper_list"),
    (DATA_ROLE_PALETTE, "palette"),
    (DATA_ROLE_POINTER_TABLE, "pointer_table"),
    (DATA_ROLE_LOOKUP_TABLE, "lookup_table"),
    (DATA_ROLE_BITMAP, "bitmap"),
    (DATA_ROLE_SOUND_SAMPLE, "sound_sample"),
    (DATA_ROLE_STRING, "string"),
    (DATA_ROLE_AUDIO_TABLE, "audio_table"),
    (DATA_ROLE_BLITTER_DESTINATION, "blitter_destination"),
    (DATA_ROLE_BLITTER_SOURCE, "blitter_source"),
    (DATA_ROLE_DISK_BUFFER, "disk_buffer"),
    (DATA_ROLE_SPRITE, "sprite"),
    (DATA_ROLE_STRING_CONTROL_STREAM, "string_control_stream"),
)
LISTING_ROW_KIND_UNKNOWN = 0
LISTING_ROW_KIND_DIRECTIVE = 1
LISTING_ROW_KIND_LABEL = 2
LISTING_ROW_KIND_INSTRUCTION = 3
LISTING_ROW_KIND_DATA = 4
LISTING_ROW_KIND_BLANK = 5
LISTING_ROW_KIND_COMMENT = 6
CODE_START_REASON_CONTROL_TARGET = 4
CODE_START_REASON_PLATFORM_LOADSEG_ENTRY = 9
CONFLICT_STATE_CLEAN = 0
CONFLICT_STATE_CODE_OVERLAP = 1
CONFLICT_STATE_UNRESOLVED = 2
CONFLICT_STATE_CONFLICTED = 3
CONFLICT_STATE_NAMES = {
    CONFLICT_STATE_CLEAN: "clean",
    CONFLICT_STATE_CODE_OVERLAP: "code_overlap",
    CONFLICT_STATE_UNRESOLVED: "unresolved",
    CONFLICT_STATE_CONFLICTED: "conflicted",
}
ABSOLUTE_MEMORY_OWNER_NAMES = {
    0: "unknown",
    1: "execbase_literal",
    2: "cpu_vector",
    3: "hardware_register",
    4: "hardware_register_range",
    5: "runtime_range",
    6: "section_storage",
    7: "absolute_memory",
}
MEMORY_LAYOUT_RECORD_KIND_NAMES = {
    1: "base_layout",
    2: "base_layout_field",
    3: "platform_storage_effect",
    4: "platform_typed_access",
    5: "platform_unresolved_typed_access",
    6: "runtime_view",
    7: "runtime_address_ref",
    8: "absolute_memory_ref",
}
BASE_LAYOUT_KIND_NAMES = {
    1: "app",
    2: "named",
}
UNRESOLVED_TYPED_ACCESS_FIELD_GAP = 0
UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION = 1
UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE = 2
UNRESOLVED_TYPED_ACCESS_CLASSIFICATION_NAMES = {
    UNRESOLVED_TYPED_ACCESS_FIELD_GAP: "field_gap",
    UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION: "prefix_extension",
    UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE: "custom_tail_or_mistyped_base",
}
TYPE_PROVENANCE_NONE = 0
TYPE_PROVENANCE_API_OUTPUT = 1
TYPE_PROVENANCE_REGISTER_COPY = 2
TYPE_PROVENANCE_STACK_SLOT = 3
TYPE_PROVENANCE_BASE_SLOT = 4
TYPE_PROVENANCE_LOOKUP_STORAGE = 5
TYPE_PROVENANCE_APP_SLOT = 6
TYPE_PROVENANCE_FIELD_POINTER = 7
TYPE_PROVENANCE_PREFIX_REFINEMENT = 8
TYPE_PROVENANCE_FIELD_ADDRESS = 9
TYPE_PROVENANCE_NAMES = {
    TYPE_PROVENANCE_NONE: "unknown",
    TYPE_PROVENANCE_API_OUTPUT: "api_output",
    TYPE_PROVENANCE_REGISTER_COPY: "register_copy",
    TYPE_PROVENANCE_STACK_SLOT: "stack_slot",
    TYPE_PROVENANCE_BASE_SLOT: "base_slot",
    TYPE_PROVENANCE_LOOKUP_STORAGE: "lookup_storage",
    TYPE_PROVENANCE_APP_SLOT: "app_slot",
    TYPE_PROVENANCE_FIELD_POINTER: "field_pointer",
    TYPE_PROVENANCE_PREFIX_REFINEMENT: "prefix_refinement",
    TYPE_PROVENANCE_FIELD_ADDRESS: "field_address",
}
XREF_KIND_PLATFORM_TYPED_ACCESS = 1
XREF_KIND_TYPED_STORAGE = 2
XREF_KIND_PLATFORM_UNRESOLVED_TYPED_ACCESS = 3
XREF_KIND_PLATFORM_TYPE_REFINEMENT = 4
XREF_KIND_APP_SLOT_API_ARG = 5
XREF_KIND_APP_SLOT_GAP = 6
XREF_KIND_APP_SLOT_FIELD_GAP = 7
XREF_KIND_APP_SLOT_SUGGESTION = 8
XREF_KIND_OS_CALL = 9
XREF_KIND_STRUCT = 10
XREF_KIND_TYPE = 11
XREF_KIND_OS_CALL_OUTPUT = 12
XREF_KIND_OS_CALL_OUTPUT_STRUCT = 13
XREF_KIND_IDS = {
    "platform_typed_access": XREF_KIND_PLATFORM_TYPED_ACCESS,
    "typed_storage": XREF_KIND_TYPED_STORAGE,
    "platform_unresolved_typed_access": XREF_KIND_PLATFORM_UNRESOLVED_TYPED_ACCESS,
    "platform_type_refinement": XREF_KIND_PLATFORM_TYPE_REFINEMENT,
    "app_slot_api_arg": XREF_KIND_APP_SLOT_API_ARG,
    "app_slot_gap": XREF_KIND_APP_SLOT_GAP,
    "app_slot_field_gap": XREF_KIND_APP_SLOT_FIELD_GAP,
    "app_slot_suggestion": XREF_KIND_APP_SLOT_SUGGESTION,
    "os_call": XREF_KIND_OS_CALL,
    "struct": XREF_KIND_STRUCT,
    "type": XREF_KIND_TYPE,
    "os_call_output": XREF_KIND_OS_CALL_OUTPUT,
    "os_call_output_struct": XREF_KIND_OS_CALL_OUTPUT_STRUCT,
}
XREF_FEATURE_PLATFORM_TYPED_ACCESS_ANY = 1
XREF_FEATURE_TYPED_STORAGE_ANY = 2
XREF_FEATURE_TYPED_BASE_UNRESOLVED_FIELD = 3
XREF_FEATURE_PLATFORM_TYPE_REFINEMENT_APPLIED = 4
XREF_FEATURE_APP_SLOT_UNTYPED_API_ARG = 5
XREF_FEATURE_APP_SLOT_GAP = 6
XREF_FEATURE_APP_SLOT_FIELD_GAP = 7
XREF_FEATURE_APP_SLOT_SUGGESTED_REGION = 8
XREF_FEATURE_IDS = {
    "platform_typed_access:any": XREF_FEATURE_PLATFORM_TYPED_ACCESS_ANY,
    "typed_storage:any": XREF_FEATURE_TYPED_STORAGE_ANY,
    "typed_base_unresolved_field": XREF_FEATURE_TYPED_BASE_UNRESOLVED_FIELD,
    "platform_type_refinement:applied": XREF_FEATURE_PLATFORM_TYPE_REFINEMENT_APPLIED,
    "app_slot:untyped_api_arg": XREF_FEATURE_APP_SLOT_UNTYPED_API_ARG,
    "app_slot:gap": XREF_FEATURE_APP_SLOT_GAP,
    "app_slot:field_gap": XREF_FEATURE_APP_SLOT_FIELD_GAP,
    "app_slot:suggested_region": XREF_FEATURE_APP_SLOT_SUGGESTED_REGION,
}
XREF_FEATURE_CLASS_STRUCT = 1
XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_STRUCT = 2
XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_OWNER = 3
XREF_FEATURE_CLASS_PLATFORM_UNRESOLVED_TYPED_ACCESS_STRUCT = 4
XREF_FEATURE_CLASS_PLATFORM_STRUCT_FIELD = 5
XREF_FEATURE_CLASS_APP_SLOT_API_ARG = 6
XREF_FEATURE_CLASS_APP_SLOT_API_ARG_REASON = 7
XREF_FEATURE_CLASS_OS_CALL = 8
XREF_FEATURE_CLASS_DYNAMIC_PREFIXES = (
    ("struct:", XREF_FEATURE_CLASS_STRUCT),
    ("platform_typed_access_struct:", XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_STRUCT),
    ("platform_typed_access_owner:", XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_OWNER),
    ("platform_unresolved_typed_access_struct:", XREF_FEATURE_CLASS_PLATFORM_UNRESOLVED_TYPED_ACCESS_STRUCT),
    ("platform_struct_field:", XREF_FEATURE_CLASS_PLATFORM_STRUCT_FIELD),
    ("app_slot_api_arg:", XREF_FEATURE_CLASS_APP_SLOT_API_ARG),
    ("app_slot_api_arg_reason:", XREF_FEATURE_CLASS_APP_SLOT_API_ARG_REASON),
    ("os:", XREF_FEATURE_CLASS_OS_CALL),
)
UNRESOLVED_TYPED_FIELD_REPORT_CONTROL_TRANSFER = 1
UNRESOLVED_TYPED_FIELD_REPORT_PREFIX_EXTENSION = 2
UNRESOLVED_TYPED_FIELD_REPORT_CUSTOM_TAIL_OR_MISTYPED_BASE = 3
UNRESOLVED_TYPED_FIELD_REPORT_FIELD_GAP = 4
UNRESOLVED_TYPED_FIELD_REPORT_OUT_OF_STRUCT_BOUNDS = 5
UNRESOLVED_TYPED_FIELD_REPORT_NEARBY_API_UNKNOWN_FIELD = 6
UNRESOLVED_TYPED_FIELD_REPORT_UNKNOWN_STRUCT_FIELD = 7
UNRESOLVED_TYPED_FIELD_REPORT_NAMES = {
    UNRESOLVED_TYPED_FIELD_REPORT_CONTROL_TRANSFER: "control_transfer_operand",
    UNRESOLVED_TYPED_FIELD_REPORT_PREFIX_EXTENSION: "prefix_extension",
    UNRESOLVED_TYPED_FIELD_REPORT_CUSTOM_TAIL_OR_MISTYPED_BASE: "custom_tail_or_mistyped_base",
    UNRESOLVED_TYPED_FIELD_REPORT_FIELD_GAP: "field_gap",
    UNRESOLVED_TYPED_FIELD_REPORT_OUT_OF_STRUCT_BOUNDS: "out_of_struct_bounds",
    UNRESOLVED_TYPED_FIELD_REPORT_NEARBY_API_UNKNOWN_FIELD: "nearby_api_unknown_field",
    UNRESOLVED_TYPED_FIELD_REPORT_UNKNOWN_STRUCT_FIELD: "unknown_struct_field",
}
RUNTIME_VIEW_MATERIALIZATION_REASONS = {
    1: "full_source_policy_load_view",
    2: "policy_entry_point",
    3: "runtime_ref_target",
    4: "discovered_copy_entry",
    101: "conflicting_discovered_copy",
    102: "crossed_by_storage_xref",
    103: "exit_to_larger_runtime_range",
    104: "redundant_contained_view",
    105: "storage_continuation",
    106: "no_materializing_evidence",
    107: "overlaid_by_runtime_copy",
}
RUNTIME_VIEW_SUPPRESSED_EXIT_TO_LARGER_RUNTIME_RANGE = 103
RUNTIME_VIEW_RELATIONSHIP_NONE = 0
RUNTIME_VIEW_RELATIONSHIP_EXITS_TO_LARGER_RUNTIME_RANGE = 1
RUNTIME_VIEW_RELATIONSHIP_CONTAINED_BY_RUNTIME_RANGE = 2
RUNTIME_VIEW_RELATIONSHIP_OVERLAID_BY_RUNTIME_COPY = 3
RUNTIME_VIEW_RELATIONSHIP_NAMES = {
    RUNTIME_VIEW_RELATIONSHIP_EXITS_TO_LARGER_RUNTIME_RANGE: "exits_to_larger_runtime_range",
    RUNTIME_VIEW_RELATIONSHIP_CONTAINED_BY_RUNTIME_RANGE: "contained_by_runtime_range",
    RUNTIME_VIEW_RELATIONSHIP_OVERLAID_BY_RUNTIME_COPY: "overlaid_by_runtime_copy",
}
RUNTIME_VIEW_RELATIONSHIP_ROLE_FEATURES = {
    RUNTIME_VIEW_RELATIONSHIP_EXITS_TO_LARGER_RUNTIME_RANGE: (
        "runtime:view_role:entry_wrapper",
        "runtime:view_role:final_image_related",
    ),
    RUNTIME_VIEW_RELATIONSHIP_CONTAINED_BY_RUNTIME_RANGE: (
        "runtime:view_role:contained_helper",
        "runtime:view_role:final_image_related",
    ),
    RUNTIME_VIEW_RELATIONSHIP_OVERLAID_BY_RUNTIME_COPY: (
        "runtime:view_role:overlaid_helper",
        "runtime:view_role:final_image_related",
    ),
}
SIM_FLOW_NAMES = {
    0: "none",
    1: "sequential",
    2: "branch",
    3: "jump",
    4: "call",
    5: "return",
    6: "trap",
}
ORPHAN_CODE_SIGNAL_REASON_NAMES = {
    1: "terminal_decode",
}
ORPHAN_CODE_SIGNAL_STATUS_NAMES = {
    1: "unresolved",
    2: "rejected",
    3: "suppressed",
    4: "linked",
    5: "promoted",
}
ORPHAN_CODE_SIGNAL_STATUS_UNRESOLVED = 1
ORPHAN_CODE_SIGNAL_CONTEXT_NAMES = {
    1: "accepted_code_boundary",
    2: "renderable_label",
    3: "runtime_view",
}
ORPHAN_CODE_SIGNAL_INBOUND_NAMES = {
    1: "unknown",
    2: "jump_table",
    3: "callback",
    4: "vector",
    5: "runtime_copy",
    6: "api",
    7: "metadata",
    8: "policy_seed",
}
ORPHAN_CODE_SIGNAL_NEARBY_DATA_RELATION_NAMES = {
    1: "overlap",
    2: "after",
    3: "before",
}
RECOVERED_INDIRECT_FLOW_NAMES = {
    1: "call",
    2: "jump",
}
RECOVERED_INDIRECT_SHAPE_NAMES = {
    1: "ind",
    2: "disp",
    3: "index.brief",
    4: "pcindex.brief",
    5: "index.full",
    6: "pcindex.full",
    7: "index.memind",
    8: "pcindex.memind",
}
RECOVERED_INDIRECT_STATUS_NAMES = {
    1: "unresolved",
    2: "resolved_runtime",
    3: "runtime",
    4: "per_caller",
    5: "backward_slice",
    6: "jump_table",
    7: "external",
}
RECOVERED_INDIRECT_TABLE_BOUNDS_STATUS_NAMES = {
    0: "none",
    1: "rejected_insufficient_entries",
    2: "rejected_code_overlap",
    3: "rejected_undecoded_entry",
    4: "rejected_unsupported_entry_shape",
}
RECOVERED_INDIRECT_SOURCE_PATTERN_NAMES = {
    1: "indirect",
    2: "indexed_indirect",
    3: "pc_indexed_indirect",
}
STRUCTURED_DATA_SOURCE_PATTERN_NAMES = {
    1: "relocation_pointer_table",
    2: "indexed_word_dispatch",
    3: "indexed_local_pointer_read",
    4: "indexed_local_scalar_read",
    5: "postincrement_read_sequence",
    6: "pc_relative_indexed_read",
    7: "keyed_long_relative_dispatch",
}
TABLE_KIND_NAMES = {
    1: "scalar",
    2: "pointer",
    3: "relative_code_dispatch",
    4: "absolute_code_dispatch",
}
TABLE_BASE_EXPRESSION_NAMES = {
    1: "table_label",
    2: "target_label",
}
DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD = 1
DERIVED_TARGET_SUGGESTION_KIND_NAMES = {
    DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD: "decompressed_payload",
}
PROJECT_ORIGIN_KIND_DERIVED_DECOMPRESSED_PAYLOAD = 1
PROJECT_ORIGIN_KIND_NAMES = {
    PROJECT_ORIGIN_KIND_DERIVED_DECOMPRESSED_PAYLOAD: "derived_decompressed_payload",
}
PROJECT_TARGET_ROLE_DECOMPRESSED_PAYLOAD = 1
PROJECT_TARGET_ROLE_NAMES = {
    PROJECT_TARGET_ROLE_DECOMPRESSED_PAYLOAD: "decompressed_payload",
}
DECOMPRESSION_EVENT_KIND_DECOMPRESSION = 1
DECOMPRESSION_EVENT_KIND_NAMES = {
    DECOMPRESSION_EVENT_KIND_DECOMPRESSION: "decompression",
}
DECOMPRESSION_SOURCE_SECTION_RANGE = 1
DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER = 2
DECOMPRESSION_SOURCE_SELF_DECRUNCHER = 3
DECOMPRESSION_SOURCE_KIND_NAMES = {
    DECOMPRESSION_SOURCE_SECTION_RANGE: "section_range",
    DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER: "recognized_unpacker",
    DECOMPRESSION_SOURCE_SELF_DECRUNCHER: "self_decruncher",
}
DECOMPRESSION_STATUS_IDENTIFIED = 1
DECOMPRESSION_STATUS_MATERIALIZABLE = 2
DECOMPRESSION_STATUS_NEEDS_RUNTIME_METADATA = 3
DECOMPRESSION_STATUS_NEEDS_SIMULATED_DECRUNCH = 4
DECOMPRESSION_STATUS_SIMULATED_OUTPUT_OBSERVED = 5
DECOMPRESSION_STATUS_NAMES = {
    DECOMPRESSION_STATUS_IDENTIFIED: "identified",
    DECOMPRESSION_STATUS_MATERIALIZABLE: "materializable",
    DECOMPRESSION_STATUS_NEEDS_RUNTIME_METADATA: "needs_runtime_metadata",
    DECOMPRESSION_STATUS_NEEDS_SIMULATED_DECRUNCH: "needs_simulated_decrunch",
    DECOMPRESSION_STATUS_SIMULATED_OUTPUT_OBSERVED: "simulated_output_observed",
}
DECOMPRESSION_REASON_NAMES = {
    1: "invalid_record",
    2: "initial_control_target_validated_provider_wrapper",
    3: "initial_control_target_validated_runtime_copy",
    4: "missing_runtime_copy_evidence",
    5: "runtime_copy_conflicting",
    6: "runtime_copy_short",
    7: "runtime_copy_oversize",
    8: "missing_decompressed_load_entry",
    9: "native_tetragon_unpack_validated",
    10: "recognized_unpacker_signature",
    11: "unidentified_self_decruncher",
    12: "simulated_pc_range_stop",
    13: "simulated_pc_out_of_range",
    14: "simulated_instruction_limit",
    15: "simulated_decode_error",
    16: "simulated_error",
    17: "simulated_bad_argument",
    18: "simulated_no_output_range",
    19: "simulated_unknown_stop",
}
DECOMPRESSION_PAYLOAD_ROLE_NAMES = {
    1: "unknown_runtime_payload",
    2: "primary_program",
}
DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NAMES = {
    1: "tool_inferred",
    2: "native_unpack_entry_validated",
    3: "signature_only",
    4: "observed_output_only",
}
DECOMPRESSION_PARENT_REMAINS_ACTIVE_NAMES = {
    0: "unknown",
    1: "false",
    2: "true",
}
DECOMPRESSION_CODEC_SUPPORT_NAMES = {
    1: "external_provider",
    2: "native_decompressor",
    3: "simulator_required",
}
TYPED_STORAGE_EFFECT_TARGETS = {
    PLATFORM_EFFECT_SET_TYPED_REG: "register",
    PLATFORM_EFFECT_WRITE_TYPED_SLOT: "app_slot",
    PLATFORM_EFFECT_WRITE_TYPED_GLOBAL_SLOT: "global_slot",
}
NUMERIC_ADDRESS_REG_ACCESS_RE = re.compile(r"\$[0-9A-Fa-f]{2,8}(?:\.[wlWL])?\([aA][0-7]\)")
SUSPICIOUS_FIRST_STRUCT_NAMES = ("AmigaGuideMsg",)
SUSPICIOUS_FIRST_STRUCT_PREFIXES = ("agm_",)
FEATURE_GROUPS: dict[str, tuple[str, ...]] = {
    "os": ("os_call", "os:"),
    "hardware": ("hardware:", "hardware_register:", "value_domain:amiga.custom", "value_domain:amiga.cia"),
    "devices": ("device:", "device_call"),
    "copper": ("data:copper_list", "hardware:custom/copper", "value_domain:amiga.custom.copper", "copper_register:"),
    "display": ("display:", "hardware:custom/display", "value_domain:amiga.custom.display_config"),
    "runtime": ("runtime:",),
    "memory": ("memory:", "memory-layout:", "memory-layout-view:"),
    "analysis": ("analysis:", "orphan-code:"),
    "tables": ("table:",),
    "app_slots": (
        "app_slot:",
        "app_slot_region:",
        "app_slot_region_source:",
        "app_slot_field_path:",
        "app_slot_field_gap:",
        "app_slot_field_gap_path:",
        "app_slot_base:",
        "app_slot_api_arg:",
        "app_slot_api_arg_reason:",
    ),
    "platform_types": (
        "platform_typed_access:",
        "platform_typed_access_struct:",
        "platform_typed_access_owner:",
        "platform_unresolved_typed_access:",
        "platform_unresolved_typed_access_struct:",
        "platform_field:",
        "platform_struct_field:",
        "platform_field_expr:",
        "typed_base_unresolved_field",
        "typed_storage:",
        "typed_storage_kind:",
        "typed_storage_type:",
        "typed_storage_target:",
    ),
    "symbols": ("label:", "xref:label", "xref:segment"),
    "data": ("data:", "xref:data"),
    "compression": (
        "compressed-payload",
        "compressed:",
        "decompression:",
        "derived_target:",
        "derived_target_suggestion:",
        "derived-decompressed-target",
        "unsupported-compressor",
    ),
    "diagnostics": ("diagnostic:",),
    "patterns": ("target-pattern:",),
}

TARGET_PATTERN_FEATURE_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("table:kind:relative_code_dispatch",), "target-pattern:relative_lookup_dispatch"),
    (("runtime:copied_code",), "target-pattern:runtime_copied_code"),
    (("low-vector-trampoline",), "target-pattern:weak_low_trampoline"),
    (
        (
            "decompression:runtime_copy",
            "decompression:runtime_copy_conflicting",
            "decompression:pattern:runtime_copy_to_absolute",
        ),
        "target-pattern:packed_runtime_copy",
    ),
    (("decompression:runtime_copy_conflicting",), "target-pattern:packed_runtime_copy_conflict"),
    (("orphan-code:signal",), "target-pattern:orphan_code_signal"),
    (("orphan-code:missing_inbound:jump_table",), "target-pattern:orphan_missing_jump_table"),
    (("orphan-code:missing_inbound:callback",), "target-pattern:orphan_missing_callback"),
    (("orphan-code:missing_inbound:vector",), "target-pattern:orphan_missing_vector"),
    (("orphan-code:missing_inbound:runtime_copy",), "target-pattern:orphan_missing_runtime_copy"),
    (("orphan-code:missing_inbound:api",), "target-pattern:orphan_missing_api"),
    (("orphan-code:missing_inbound:metadata",), "target-pattern:orphan_missing_metadata"),
    (("runtime:view_role:entry_wrapper",), "target-pattern:runtime_entry_wrapper"),
    (("runtime:view_role:contained_helper",), "target-pattern:runtime_contained_helper"),
    (("runtime:view_role:overlaid_helper",), "target-pattern:runtime_overlaid_helper"),
)


class FeatureBag:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.examples: dict[str, list[dict[str, object]]] = {}

    def add(self, key: str, count: int = 1, example: dict[str, object] | None = None) -> None:
        if not key or count <= 0:
            return
        self.counts[key] = self.counts.get(key, 0) + count
        if example is not None:
            items = self.examples.setdefault(key, [])
            if len(items) < MAX_EXAMPLES:
                items.append(_compact_example(example))

    def row_features(self) -> tuple[dict[str, int], dict[str, list[dict[str, object]]], list[str]]:
        counts = dict(self.counts)
        examples = {key: list(self.examples[key]) for key in self.examples if key in counts}
        _add_target_pattern_features(counts, examples)
        counts = dict(sorted(counts.items()))
        examples = {key: examples[key] for key in sorted(examples) if key in counts}
        tags = sorted(counts)
        return counts, examples, tags


def _add_target_pattern_features(
    counts: dict[str, int], examples: dict[str, list[dict[str, object]]]
) -> None:
    for evidence_features, pattern_feature in TARGET_PATTERN_FEATURE_RULES:
        if pattern_feature in counts:
            continue
        evidence_feature = next((feature for feature in evidence_features if counts.get(feature, 0) > 0), None)
        if evidence_feature is None:
            continue
        counts[pattern_feature] = 1
        evidence_examples = examples.get(evidence_feature, [])
        if evidence_examples:
            examples[pattern_feature] = [
                {"evidence_feature": evidence_feature, **_compact_example(evidence_examples[0])}
            ]
        else:
            examples[pattern_feature] = [{"evidence_feature": evidence_feature}]


class DiskFileResolver:
    def __init__(self, disk_entries: list[dict[str, Any]], *, root: Path = ROOT) -> None:
        self.root = root
        self.by_id = {str(entry.get("id")): entry for entry in disk_entries if isinstance(entry.get("id"), str)}
        self.image_cache: dict[str, bytes] = {}
        self._lock = threading.Lock()

    def file_bytes(self, file_entry: dict[str, Any]) -> bytes:
        file_ref = file_entry.get("file_ref")
        origin = file_entry.get("origin")
        if not isinstance(file_ref, dict) or not isinstance(origin, dict):
            raise RuntimeError("File manifest row has no file_ref/origin")
        disk_id = file_ref.get("disk_id")
        image_path = origin.get("in_image_path")
        if not isinstance(disk_id, str) or not isinstance(image_path, str):
            raise RuntimeError("File manifest row has no disk_id/in_image_path")
        disk_entry = self.by_id.get(disk_id)
        if disk_entry is None:
            raise RuntimeError(f"Missing disk manifest row for {disk_id}")
        disk_platform = str(disk_entry.get("platform"))
        with self._lock:
            image_bytes = self.image_cache.get(disk_id)
            if image_bytes is None:
                disk_origin = disk_entry.get("origin")
                if not isinstance(disk_origin, dict):
                    raise RuntimeError("Disk manifest row has no origin")
                image_bytes = load_disk_image_bytes(disk_origin, root=self.root)
                self.image_cache[disk_id] = image_bytes
        candidate = _find_disk_file_entry(disk_entry, image_path)
        return reconstruct_file_bytes(disk_platform, candidate, image_bytes)


def _safe_part(value: object) -> str:
    text = str(value).strip() if value is not None else "unknown"
    text = re.sub(r"\s+", "_", text)
    return text.replace("\\", "/")


def _status(entry: dict[str, Any]) -> str:
    expect = entry.get("expect")
    if isinstance(expect, dict) and isinstance(expect.get("status"), str):
        return str(expect["status"])
    if isinstance(entry.get("status"), str):
        return str(entry["status"])
    return "unknown"


def _origin_summary(entry: dict[str, Any]) -> dict[str, object]:
    origin = entry.get("origin")
    if not isinstance(origin, dict):
        return {}
    keys = ("display_name", "source_relpath", "container_relpath", "member_name", "in_image_path")
    return {
        key: origin[key]
        for key in keys
        if key in origin and (isinstance(origin.get(key), (str, int, float, bool)) or origin.get(key) is None)
    }


def _base_row(source_manifest: str, entry: dict[str, Any], bag: FeatureBag) -> dict[str, object]:
    source_id = str(entry.get("id", "unknown"))
    platform = str(entry.get("platform", "unknown"))
    status = _status(entry)
    bag.add(f"platform:{platform}")
    bag.add(f"status:{status}")
    row = {
        "schema_version": 1,
        "id": f"{source_manifest}:{source_id}",
        "source_manifest": source_manifest,
        "source_id": source_id,
        "platform": platform,
        "sha256": entry.get("sha256") if isinstance(entry.get("sha256"), str) else None,
        "size": entry.get("size") if isinstance(entry.get("size"), int) else None,
        "status": status,
        "origin": _origin_summary(entry),
    }
    _finalize_row_features(row, bag)
    return row


def _finalize_row_features(row: dict[str, object], bag: FeatureBag) -> None:
    counts, examples, tags = bag.row_features()
    row["feature_counts"] = counts
    row["feature_examples"] = examples
    row["tags"] = tags


def build_usage_manifest(
    disk_manifest_path: Path = DEFAULT_DISK_MANIFEST,
    file_manifest_path: Path = DEFAULT_FILE_MANIFEST,
    *,
    root: Path = ROOT,
) -> list[dict[str, object]]:
    rows, _xrefs = build_usage_catalog(disk_manifest_path, file_manifest_path, root=root)
    return rows


def build_usage_catalog(
    disk_manifest_path: Path = DEFAULT_DISK_MANIFEST,
    file_manifest_path: Path = DEFAULT_FILE_MANIFEST,
    *,
    root: Path = ROOT,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows, xrefs, _snippet_rows = build_usage_outputs(disk_manifest_path, file_manifest_path, root=root)
    return rows, xrefs


def build_usage_outputs(
    disk_manifest_path: Path = DEFAULT_DISK_MANIFEST,
    file_manifest_path: Path = DEFAULT_FILE_MANIFEST,
    *,
    root: Path = ROOT,
    max_workers: int | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    disk_entries = read_jsonl_manifest(disk_manifest_path)
    file_entries = read_jsonl_manifest(file_manifest_path)
    resolver = DiskFileResolver(disk_entries, root=root)
    rows: list[dict[str, object]] = []
    xrefs: list[dict[str, object]] = []
    snippet_rows: list[dict[str, object]] = []
    for entry in disk_entries:
        row = _collect_disk_usage_row(entry)
        rows.append(row)
        xrefs.extend(_disk_usage_xrefs(row, entry))
    build_dir = root / "src" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    worker_count = _target_usage_worker_count(max_workers)
    with tempfile.TemporaryDirectory(dir=build_dir) as tmp:
        tmp_dir = Path(tmp)
        file_tasks = list(enumerate(file_entries))

        def collect_file_task(task: tuple[int, dict[str, Any]]) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
            index, entry = task
            task_tmp_dir = tmp_dir / f"file_{index:06d}"
            task_tmp_dir.mkdir()
            return collect_file_usage_catalog_entry(entry, resolver, task_tmp_dir, root=root)

        for row, row_xrefs, row_snippets in _run_usage_tasks(file_tasks, collect_file_task, worker_count):
            rows.append(row)
            xrefs.extend(row_xrefs)
            snippet_rows.extend(row_snippets)
        project_tasks = list(enumerate(_project_target_dirs(root)))

        def collect_project_task(task: tuple[int, Path]) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
            index, target_dir = task
            task_tmp_dir = tmp_dir / f"project_{index:06d}"
            task_tmp_dir.mkdir()
            return collect_project_usage_catalog_entry(target_dir, task_tmp_dir, root=root)

        for row, row_xrefs, row_snippets in _run_usage_tasks(project_tasks, collect_project_task, worker_count):
            rows.append(row)
            xrefs.extend(row_xrefs)
            snippet_rows.extend(row_snippets)
    rows = sorted(rows, key=lambda row: str(row["id"]))
    xrefs = sorted(
        xrefs,
        key=lambda row: (
            str(row.get("target_id")),
            str(row.get("feature")),
            _sort_int(row.get("section")),
            _sort_int(row.get("offset")),
            _sort_int(row.get("row_index")),
            str(row.get("id")),
        ),
    )
    snippet_rows = sorted(
        snippet_rows,
        key=lambda row: (
            str(row.get("target_id")),
            _sort_int(row.get("row_index")),
            str(row.get("id")),
        ),
    )
    return rows, xrefs, snippet_rows


def _target_usage_worker_count(max_workers: int | None) -> int:
    if max_workers is None:
        env_value = os.environ.get(TARGET_USAGE_WORKERS_ENV)
        if env_value:
            try:
                max_workers = int(env_value)
            except ValueError:
                max_workers = 1
        else:
            max_workers = min(8, os.cpu_count() or 1)
    return max(1, max_workers)


def _run_usage_tasks(
    tasks: list[Any],
    collect: Any,
    max_workers: int,
) -> list[tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]]:
    if max_workers <= 1 or len(tasks) <= 1:
        return [collect(task) for task in tasks]
    results: list[tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]] | None] = [None] * len(tasks)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(collect, task): index for index, task in enumerate(tasks)}
        for future in concurrent.futures.as_completed(futures):
            results[futures[future]] = future.result()
    return [cast(tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]], result) for result in results]


def build_variant_index(
    file_manifest_path: Path = DEFAULT_FILE_MANIFEST,
) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], dict[str, tuple[dict[str, Any], dict[str, Any]]]] = {}
    for entry in read_jsonl_manifest(file_manifest_path):
        platform = _string_value(entry.get("platform"))
        source_id = _string_value(entry.get("id"))
        if not platform or not source_id:
            continue
        for origin in _variant_origins(entry):
            in_image_path = _string_value(origin.get("in_image_path"))
            if not in_image_path:
                continue
            key = (
                platform,
                _disk_title_family(origin),
                _normalise_variant_path(in_image_path),
            )
            groups.setdefault(key, {}).setdefault(source_id, (entry, origin))

    rows: list[dict[str, object]] = []
    for (platform, title_family, file_path_key), members_by_id in sorted(groups.items()):
        members = list(members_by_id.values())
        entries = [entry for entry, _origin in members]
        hashes = sorted({str(entry.get("sha256")) for entry in entries if isinstance(entry.get("sha256"), str)})
        if len(hashes) <= 1:
            continue
        targets = [
            _variant_target(entry, origin)
            for entry, origin in sorted(members, key=_variant_member_sort_key)
        ]
        raw_id = json.dumps(
            {"platform": platform, "title_family": title_family, "file_path_key": file_path_key},
            sort_keys=True,
            separators=(",", ":"),
        )
        rows.append(
            {
                "schema_version": 1,
                "id": f"variant/{hashlib.sha256(raw_id.encode('utf-8')).hexdigest()[:20]}",
                "platform": platform,
                "title_family": title_family,
                "file_path_key": file_path_key,
                "display_path": _display_variant_path(members[0][1]),
                "target_count": len(targets),
                "unique_hash_count": len(hashes),
                "targets": targets,
            }
        )
    return rows


def _variant_origins(entry: dict[str, Any]) -> list[dict[str, Any]]:
    origin = entry.get("origin")
    if not isinstance(origin, dict):
        return []
    origins = [origin]
    alternate_origins = origin.get("alternate_origins")
    if isinstance(alternate_origins, list):
        origins.extend(item for item in alternate_origins if isinstance(item, dict))
    return origins


def _variant_target(entry: dict[str, Any], origin: dict[str, Any]) -> dict[str, object]:
    primary_origin = entry.get("origin") if isinstance(entry.get("origin"), dict) else {}
    file_ref = entry.get("file_ref") if isinstance(entry.get("file_ref"), dict) else {}
    alternate_origins = primary_origin.get("alternate_origins")
    return {
        "target_id": f"platform_file_manifest:{entry.get('id')}",
        "source_id": entry.get("id"),
        "platform": entry.get("platform"),
        "sha256": entry.get("sha256"),
        "size": entry.get("size"),
        "status": _status(entry),
        "origin": _origin_summary_from_origin(origin),
        "disk_id": file_ref.get("disk_id"),
        "disk_sha256": entry.get("disk_sha256"),
        "origin_count": 1 + (len(alternate_origins) if isinstance(alternate_origins, list) else 0),
    }


def _origin_summary_from_origin(origin: dict[str, Any]) -> dict[str, object]:
    keys = ("display_name", "source_relpath", "container_relpath", "member_name", "in_image_path")
    return {
        key: origin[key]
        for key in keys
        if key in origin and (isinstance(origin.get(key), (str, int, float, bool)) or origin.get(key) is None)
    }


def _variant_member_sort_key(member: tuple[dict[str, Any], dict[str, Any]]) -> tuple[str, str, str]:
    entry, origin = member
    return (
        str(origin.get("display_name", "")),
        str(origin.get("in_image_path", "")),
        str(entry.get("sha256", "")),
    )


def _display_variant_path(origin: dict[str, Any]) -> str:
    path = origin.get("in_image_path")
    return str(path) if isinstance(path, str) else ""


def _normalise_variant_path(path: str) -> str:
    return re.sub(r"/+", "/", path.replace("\\", "/").casefold().strip())


def _disk_title_family(origin: dict[str, Any]) -> str:
    name = (
        _string_value(origin.get("member_name"))
        or _string_value(origin.get("display_name"))
        or _string_value(origin.get("source_relpath"))
        or "unknown"
    )
    stem = Path(name.replace("\\", "/")).name
    for suffix in (".zip", ".adf", ".adz", ".st"):
        if stem.casefold().endswith(suffix):
            stem = stem[: -len(suffix)]
    stem = re.sub(r"\[[^\]]*\]", " ", stem)
    stem = re.sub(r"\([^)]*\)", " ", stem)
    stem = re.sub(r"\bdisk\s+\d+\s+of\s+\d+\b", " ", stem, flags=re.IGNORECASE)
    stem = re.sub(r"[^a-zA-Z0-9]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip().casefold()
    return stem or "unknown"


def collect_disk_usage_rows(disk_entries: list[dict[str, Any]]) -> list[dict[str, object]]:
    return [_collect_disk_usage_row(entry) for entry in disk_entries]


def _stable_analysis_error_message(message: str) -> str:
    return re.sub(r"access violation reading 0x[0-9A-Fa-f]+", "access violation reading <address>", message)


def collect_file_usage_row(
    entry: dict[str, Any],
    resolver: DiskFileResolver | None,
    tmp_dir: Path,
    *,
    root: Path = ROOT,
) -> dict[str, object]:
    row, _xrefs, _snippet_rows = collect_file_usage_catalog_entry(entry, resolver, tmp_dir, root=root)
    return row


def collect_file_usage_catalog_entry(
    entry: dict[str, Any],
    resolver: DiskFileResolver | None,
    tmp_dir: Path,
    *,
    root: Path = ROOT,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    bag = FeatureBag()
    _add_file_manifest_features(entry, bag)
    platform = str(entry.get("platform", "unknown"))
    combined: dict[str, Any] | None = None
    analysis_error: str | None = None
    if _status(entry) == "ok" and platform in {"amiga-hunk", "atari-st"}:
        try:
            if resolver is None:
                raise RuntimeError("No disk resolver supplied")
            file_bytes = resolver.file_bytes(entry)
            combined = analyze_executable_file(platform, file_bytes, tmp_dir, root=root)
            _add_executable_analysis_features(combined, bag, platform=platform, root=root, include_listing=False)
        except Exception as exc:
            analysis_error = _stable_analysis_error_message(str(exc))
            bag.add("diagnostic:analysis_error", example={"message": analysis_error})
    row = _base_row("platform_file_manifest", entry, bag)
    xrefs = _file_usage_xrefs(row, entry, combined, analysis_error, listing_feature_bag=bag)
    _finalize_row_features(row, bag)
    return row, xrefs, _snippet_rows_for_xrefs(row, combined, xrefs)


def _project_target_dirs(root: Path = ROOT) -> list[Path]:
    targets_dir = root / "targets"
    if not targets_dir.exists():
        return []
    return sorted(
        {source_binary.parent for source_binary in targets_dir.rglob("source_binary.json")},
        key=lambda item: item.relative_to(targets_dir).as_posix(),
    )


def _project_target_source_id(target_dir: Path, *, root: Path = ROOT) -> str:
    targets_dir = root / "targets"
    try:
        relpath = target_dir.relative_to(targets_dir).as_posix()
    except ValueError:
        return target_dir.name
    return target_dir.name if "/" not in relpath else relpath


def collect_project_usage_catalog_entry(
    target_dir: Path,
    tmp_dir: Path,
    *,
    root: Path = ROOT,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    bag = FeatureBag()
    bag.add("project_target:any", example={"target": target_dir.name})
    entry, source = _project_target_manifest_entry(target_dir, root=root)
    platform = str(entry.get("platform", "unknown"))
    if source is not None:
        bag.add(f"format:{_safe_part(source.kind)}")
    _add_project_target_metadata_features(entry, bag)
    if _status(entry) != "ok":
        expect = entry.get("expect") if isinstance(entry.get("expect"), dict) else {}
        bag.add("diagnostic:manifest_error", example={"message": expect.get("error") if isinstance(expect, dict) else None})
    combined: dict[str, Any] | None = None
    analysis_error: str | None = None
    if _status(entry) == "ok" and isinstance(source, HunkFileBinarySource) and platform == "amiga-hunk":
        try:
            combined = analyze_project_hunk_file(platform, source.path, target_dir, root=root)
            _add_executable_analysis_features(combined, bag, platform=platform, root=root, include_listing=False)
        except Exception as exc:
            analysis_error = _stable_analysis_error_message(str(exc))
            bag.add("diagnostic:analysis_error", example={"message": analysis_error})
    elif _status(entry) == "ok" and isinstance(source, DiskEntryBinarySource) and platform == "amiga-hunk":
        try:
            combined = analyze_executable_file(platform, source.read_bytes(), tmp_dir, root=root)
            _add_executable_analysis_features(combined, bag, platform=platform, root=root, include_listing=False)
        except Exception as exc:
            analysis_error = _stable_analysis_error_message(str(exc))
            bag.add("diagnostic:analysis_error", example={"message": analysis_error})
    reproduction = entry.get("reproduction")
    if isinstance(reproduction, dict) and combined is not None:
        analysis = combined.get("analysis")
        if isinstance(analysis, dict) and _analysis_has_decompression_relationship(analysis):
            status = _string_value(reproduction.get("status"))
            if status:
                bag.add(f"decompression:parent_reproduction_status:{_safe_part(status)}", example=reproduction)
            if reproduction.get("exact") is True:
                bag.add("decompression:parent_reproduction_exact", example=reproduction)
    row = _base_row("project_target", entry, bag)
    xrefs = _project_target_xrefs(row, entry, combined, analysis_error, listing_feature_bag=bag)
    _finalize_row_features(row, bag)
    return row, xrefs, _snippet_rows_for_xrefs(row, combined, xrefs)


def _project_target_manifest_entry(target_dir: Path, *, root: Path = ROOT) -> tuple[dict[str, Any], object | None]:
    project = _read_json_object(target_dir / ".project.json")
    project_origin = project.get("origin") if isinstance(project.get("origin"), dict) else {}
    source_error: str | None = None
    try:
        source = resolve_target_binary_source(target_dir, project_root=root)
    except Exception as exc:
        source = None
        source_error = str(exc)
    platform = _string_value(project_origin.get("platform"))
    if platform is None:
        if isinstance(source, (HunkFileBinarySource, DiskEntryBinarySource)):
            platform = "amiga-hunk"
        elif isinstance(source, RawBinarySource):
            platform = "raw-binary"
    status = "ok" if source is not None and platform is not None else ("error" if source_error else "unsupported")
    origin = {
        "display_name": target_dir.name,
        "source_relpath": getattr(source, "display_path", None),
    }
    filename = _string_value(project_origin.get("filename"))
    if filename:
        origin["member_name"] = filename
    source_id = _project_target_source_id(target_dir, root=root)
    entry: dict[str, Any] = {
        "id": source_id,
        "platform": platform or "unknown",
        "status": status,
        "origin": origin,
    }
    for source_key, entry_key in (
        ("kind", "project_origin_kind"),
        ("target_role", "target_role"),
        ("payload_role", "payload_role"),
        ("payload_role_confidence", "payload_role_confidence"),
        ("parent_remains_active", "parent_remains_active"),
        ("target_type", "target_type"),
        ("compressor", "compressor"),
        ("parent_target", "parent_target"),
    ):
        value = project_origin.get(source_key)
        if isinstance(value, (str, int, bool)):
            entry[entry_key] = value
    for source_key, entry_key in (
        ("project_origin_kind_id", "project_origin_kind_id"),
        ("target_role_id", "target_role_id"),
        ("payload_role_id", "payload_role_id"),
        ("payload_role_confidence_id", "payload_role_confidence_id"),
        ("parent_remains_active_id", "parent_remains_active_id"),
    ):
        value = project_origin.get(source_key)
        if isinstance(value, int):
            entry[entry_key] = value
    decompression = _read_json_object(target_dir / "decompression.json")
    if decompression:
        entry["decompression"] = decompression
    reproduction = _project_reproduction_summary(_read_json_object(target_dir / "reproduction.json"))
    if reproduction:
        entry["reproduction"] = reproduction
    if source_error:
        entry["expect"] = {"status": "error", "error": source_error}
    sha_value = _string_value(project_origin.get("sha256"))
    size_value = _int_value(project_origin.get("size"))
    if sha_value:
        entry["sha256"] = sha_value
    if size_value is not None:
        entry["size"] = size_value
    if source is not None and hasattr(source, "path") and ("sha256" not in entry or "size" not in entry):
        path = getattr(source, "path")
        if isinstance(path, Path):
            try:
                data = path.read_bytes()
                if "sha256" not in entry:
                    entry["sha256"] = sha256(data)
                if "size" not in entry:
                    entry["size"] = len(data)
            except OSError:
                pass
    return entry, source


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _project_reproduction_summary(report: dict[str, Any]) -> dict[str, object]:
    if not report:
        return {}
    comparison = report.get("comparison")
    status = _string_value(report.get("status"))
    if isinstance(comparison, dict):
        status = _string_value(comparison.get("status")) or status
    exact = report.get("exact")
    if not isinstance(exact, bool) and isinstance(comparison, dict):
        exact = comparison.get("selected_exact")
    summary: dict[str, object] = {}
    if status:
        summary["status"] = status
    if isinstance(exact, bool):
        summary["exact"] = exact
    return summary


def _analysis_has_decompression_relationship(analysis: dict[str, Any]) -> bool:
    for key in ("decompression_events", "derived_target_suggestions", "packed_payloads"):
        items = analysis.get(key)
        if isinstance(items, list) and items:
            return True
    return False


def analyze_project_hunk_file(platform: str, path: Path, target_dir: Path, *, root: Path = ROOT) -> dict[str, Any]:
    include_dir = _include_dir_for_platform(platform, root)
    with effective_metadata_file(target_dir) as metadata_path:
        return _analyze_file_with_listing_artifact(
            platform,
            path,
            str(metadata_path) if metadata_path is not None else "",
            str(include_dir),
            root=root,
        )


def analyze_executable_file(platform: str, file_bytes: bytes, tmp_dir: Path, *, root: Path = ROOT) -> dict[str, Any]:
    suffix = ".prg" if platform == "atari-st" else ".hunk"
    path = tmp_dir / f"usage_{platform.replace('-', '_')}_{sha256(file_bytes)[:12]}{suffix}"
    path.write_bytes(file_bytes)
    include_dir = _include_dir_for_platform(platform, root)
    return _analyze_file_with_listing_artifact(
        platform,
        path,
        "",
        str(include_dir),
        root=root,
    )


def _analyze_file_with_listing_artifact(
    platform: str,
    path: Path,
    metadata_text: str,
    include_dir: str,
    *,
    root: Path,
) -> dict[str, Any]:
    artifact = c_backend.CListingArtifact.create(
        c_backend._CBackendSourceFile(path, platform),
        metadata_text=metadata_text,
        include_dir=include_dir,
        project_root=root,
    )
    try:
        summary, summary_profile = artifact.summary_payload()
        analysis, analysis_profile = artifact.analysis_payload()
        navigation, navigation_profile = artifact.navigation_payload()
        total_rows = summary.get("total_rows", 0)
        listing, listing_profile = artifact.window_payload(start=0, count=total_rows if isinstance(total_rows, int) else 0)
    finally:
        artifact.close()
    profile = {**summary_profile, **analysis_profile, **navigation_profile, **listing_profile}
    result: dict[str, Any] = {
        "analysis": analysis,
        "listing": {"rows": list(listing["rows"])},
        "profile": profile,
    }
    app_slot_analysis = navigation.get("app_slot_analysis")
    if isinstance(app_slot_analysis, dict):
        result["listing"]["app_slot_analysis"] = app_slot_analysis
    type_flow_analysis = navigation.get("type_flow_analysis")
    if isinstance(type_flow_analysis, dict):
        result["listing"]["type_flow_analysis"] = type_flow_analysis
    return result


def _include_dir_for_platform(platform: str, root: Path) -> Path | str:
    if platform.startswith("amiga"):
        return root / "ext" / "amiga_includes" / "ndk_2.0" / "include"
    return ""


def _project_decompression_codec(entry: dict[str, Any]) -> str | None:
    decompression = entry.get("decompression")
    if isinstance(decompression, dict):
        compressor = decompression.get("compressor")
        if isinstance(compressor, dict):
            codec = _string_value(compressor.get("id")) or _string_value(compressor.get("name"))
            if codec:
                return codec
        relationship = decompression.get("relationship")
        if isinstance(relationship, dict):
            codec = _string_value(relationship.get("compressor"))
            if codec:
                return codec
    return _string_value(entry.get("compressor"))


def _project_decompression_example(entry: dict[str, Any]) -> dict[str, object]:
    decompression = entry.get("decompression")
    if not isinstance(decompression, dict):
        return {}
    packed = decompression.get("packed")
    decompressed = decompression.get("decompressed")
    example: dict[str, object] = {}
    if isinstance(packed, dict):
        section_offset = _int_value(packed.get("section_offset"))
        file_offset = _int_value(packed.get("file_offset"))
        packed_size = _int_value(packed.get("size"))
        if section_offset is not None:
            example["offset"] = section_offset
        if file_offset is not None:
            example["file_offset"] = file_offset
        if packed_size is not None:
            example["packed_size"] = packed_size
            if section_offset is not None:
                example["source_section_end_offset"] = section_offset + packed_size
    if isinstance(decompressed, dict):
        decompressed_size = _int_value(decompressed.get("size"))
        load_address = _int_value(decompressed.get("load_address"))
        entrypoint = _int_value(decompressed.get("entrypoint"))
        if decompressed_size is not None:
            example["decompressed_size"] = decompressed_size
        if load_address is not None:
            example["load_address"] = load_address
        if entrypoint is not None:
            example["entrypoint"] = entrypoint
    codec = _project_decompression_codec(entry)
    if codec:
        example["text"] = codec
    for id_key, text_key, names in (
        ("payload_role_id", "payload_role", DECOMPRESSION_PAYLOAD_ROLE_NAMES),
        ("payload_role_confidence_id", "payload_role_confidence", DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NAMES),
        ("parent_remains_active_id", "parent_remains_active", DECOMPRESSION_PARENT_REMAINS_ACTIVE_NAMES),
    ):
        value_id = _int_value(decompression.get(id_key))
        if value_id is None:
            value_id = _int_value(entry.get(id_key))
        if value_id is not None:
            example[id_key] = value_id
            value = names.get(value_id)
            if value:
                example[text_key] = value
    return example


def _add_project_target_metadata_features(entry: dict[str, Any], bag: FeatureBag) -> None:
    origin_kind_id = _int_value(entry.get("project_origin_kind_id"))
    origin_kind = PROJECT_ORIGIN_KIND_NAMES.get(origin_kind_id) if origin_kind_id is not None else None
    target_role_id = _int_value(entry.get("target_role_id"))
    target_role = PROJECT_TARGET_ROLE_NAMES.get(target_role_id) if target_role_id is not None else None
    payload_role_id = _int_value(entry.get("payload_role_id"))
    payload_role = DECOMPRESSION_PAYLOAD_ROLE_NAMES.get(payload_role_id) if payload_role_id is not None else None
    payload_role_confidence_id = _int_value(entry.get("payload_role_confidence_id"))
    payload_role_confidence = (
        DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NAMES.get(payload_role_confidence_id)
        if payload_role_confidence_id is not None else None
    )
    parent_remains_active_id = _int_value(entry.get("parent_remains_active_id"))
    parent_remains_active = (
        DECOMPRESSION_PARENT_REMAINS_ACTIVE_NAMES.get(parent_remains_active_id)
        if parent_remains_active_id is not None else None
    )
    target_type = _string_value(entry.get("target_type"))
    reproduction = entry.get("reproduction")
    reproduction_status = _string_value(reproduction.get("status")) if isinstance(reproduction, dict) else None
    if origin_kind:
        bag.add(f"project_origin:{_safe_part(origin_kind)}")
    if target_role:
        bag.add(f"project_target_role:{_safe_part(target_role)}")
    if payload_role:
        bag.add(f"decompression:payload_role:{_safe_part(payload_role)}")
    if payload_role_confidence:
        bag.add(f"decompression:payload_role_confidence:{_safe_part(payload_role_confidence)}")
    if parent_remains_active:
        bag.add(f"decompression:parent_remains_active:{_safe_part(parent_remains_active)}")
    if target_type:
        bag.add(f"project_target_type:{_safe_part(target_type)}")
    if reproduction_status:
        bag.add(f"reproduction:status:{_safe_part(reproduction_status)}")
    if isinstance(reproduction, dict) and reproduction.get("exact") is True:
        bag.add("reproduction:exact")
    if origin_kind_id == PROJECT_ORIGIN_KIND_DERIVED_DECOMPRESSED_PAYLOAD or target_role_id == PROJECT_TARGET_ROLE_DECOMPRESSED_PAYLOAD:
        example = _project_decompression_example(entry)
        if reproduction_status:
            example["reproduction_status"] = reproduction_status
        if isinstance(reproduction, dict) and reproduction.get("exact") is True:
            example["reproduction_exact"] = True
        bag.add("derived-decompressed-target", example=example)
        bag.add("derived_target:decompressed_payload", example=example)
        bag.add("decompression:child", example=example)
        if reproduction_status:
            bag.add(f"decompression:child_reproduction_status:{_safe_part(reproduction_status)}", example=example)
        if isinstance(reproduction, dict) and reproduction.get("exact") is True:
            bag.add("decompression:child_reproduction_exact", example=example)
        codec = _project_decompression_codec(entry)
        if codec:
            bag.add(f"decompression:codec:{_safe_part(codec)}", example=example)
        section_offset = _int_value(example.get("offset"))
        packed_size = _int_value(example.get("packed_size"))
        if section_offset is not None:
            bag.add("decompression:source_offset", example=example)
            bag.add(f"decompression:source_offset:0:{section_offset:08X}", example=example)
        if section_offset is not None and packed_size is not None:
            bag.add("decompression:source_range", example=example)
            bag.add(
                f"decompression:source_range:0:{section_offset:08X}-{section_offset + packed_size:08X}",
                example=example,
            )
            bag.add("decompression:packed_size", example=example)
        if _int_value(example.get("load_address")) is not None:
            bag.add("absolute-depack-dest", example=example)
        if _int_value(example.get("entrypoint")) is not None:
            bag.add("decompressed-entrypoint", example=example)
        source_load_entry = {
            "source_section": 0,
            "source_section_offset": section_offset,
            "source_section_end_offset": _int_value(example.get("source_section_end_offset")),
            "load_address": _int_value(example.get("load_address")),
            "entrypoint": _int_value(example.get("entrypoint")),
        }
        for feature in _decompression_source_load_entry_features(source_load_entry):
            bag.add(feature, example=example)


def _collect_disk_usage_row(entry: dict[str, Any]) -> dict[str, object]:
    bag = FeatureBag()
    platform = str(entry.get("platform", "unknown"))
    bag.add("format:disk_image")
    bag.add(f"disk_platform:{platform}")
    expect = entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    if isinstance(inspect, dict):
        entries = inspect.get("entries")
        if isinstance(entries, list):
            bag.add("disk:entry", len(entries))
            for item in entries:
                if not isinstance(item, dict):
                    continue
                if item.get("is_executable_candidate") == 1:
                    bag.add("disk:executable_candidate", example={"path": item.get("path")})
                kind = item.get("kind")
                if isinstance(kind, int):
                    bag.add(f"disk:entry_kind:{kind}")
        trackloader = inspect.get("trackloader_analysis")
        if isinstance(trackloader, dict):
            bag.add("disk:trackloader")
            tracks = trackloader.get("candidate_code_tracks")
            if isinstance(tracks, list):
                bag.add("disk:candidate_code_track", len(tracks))
        if inspect.get("bootblock") or inspect.get("bootblock_analysis") or inspect.get("boot_ascii_strings"):
            bag.add("disk:bootblock")
    if _status(entry) != "ok":
        bag.add("diagnostic:manifest_error")
    return _base_row("platform_disk_manifest", entry, bag)


def _add_file_manifest_features(entry: dict[str, Any], bag: FeatureBag) -> None:
    platform = str(entry.get("platform", "unknown"))
    bag.add(f"file_platform:{platform}")
    expect = entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    if _status(entry) != "ok":
        bag.add("diagnostic:manifest_error", example={"message": expect.get("error") if isinstance(expect, dict) else None})
        return
    if not isinstance(inspect, dict):
        return
    file_kind = inspect.get("file_kind")
    if isinstance(file_kind, str) and file_kind:
        bag.add(f"format:{_safe_part(file_kind)}")
    inspected_platform = inspect.get("platform")
    if isinstance(inspected_platform, str) and inspected_platform:
        bag.add(f"inspect_platform:{_safe_part(inspected_platform)}")
    form_type = inspect.get("form_type")
    if isinstance(form_type, str) and form_type:
        bag.add(f"format:iff:{_safe_part(form_type)}")
    for name, feature in (
        ("section_count", "section"),
        ("fixup_count", "relocation:fixup"),
        ("global_symbol_count", "symbol:global"),
        ("local_symbol_count", "symbol:local"),
        ("external_symbol_count", "symbol:external"),
    ):
        value = inspect.get(name)
        if isinstance(value, int) and value > 0:
            bag.add(feature, value)
    resident = inspect.get("resident")
    if isinstance(resident, dict):
        bag.add("amiga:resident")
        auto_init = resident.get("auto_init")
        if auto_init is True:
            bag.add("amiga:resident:autoinit")
        elif auto_init is False:
            bag.add("amiga:resident:non_autoinit")
        node_type_name = _string_value(resident.get("node_type_name"))
        if node_type_name:
            bag.add(f"amiga:resident_node:{_safe_part(node_type_name)}")
    elif resident is not None:
        bag.add("amiga:resident")
    if inspect.get("library") is not None:
        bag.add("amiga:library")


def _add_executable_analysis_features(
    combined: dict[str, Any],
    bag: FeatureBag,
    *,
    platform: str,
    root: Path,
    include_listing: bool = True,
) -> None:
    analysis = combined.get("analysis")
    listing = combined.get("listing")
    profile = combined.get("profile")
    if isinstance(profile, dict):
        generation = profile.get("generation")
        if isinstance(generation, str) and generation:
            bag.add(f"analysis_generation:{_safe_part(generation)}")
    if isinstance(analysis, dict):
        bag.add("analysis:facts_v2")
        _add_analysis_features(analysis, bag)
    if include_listing and isinstance(listing, dict):
        _add_listing_features(listing, bag)
    app_slot_analysis = _app_slot_layout_analysis(combined, platform=platform, root=root)
    if app_slot_analysis is not None:
        combined["app_slot_analysis"] = app_slot_analysis
        _add_app_slot_layout_features(app_slot_analysis, bag)


def _app_slot_layout_analysis(combined: dict[str, Any], *, platform: str, root: Path) -> dict[str, object] | None:
    listing = combined.get("listing")
    if not isinstance(listing, dict):
        return None
    app_slot_analysis = listing.get("app_slot_analysis")
    return app_slot_analysis if isinstance(app_slot_analysis, dict) else None


def _add_app_slot_layout_features(app_slot_analysis: dict[str, object], bag: FeatureBag) -> None:
    for region in _dict_items(app_slot_analysis.get("regions")):
        source = _string_value(region.get("source")) or "unknown"
        if not _is_generated_app_slot_region_source(source):
            continue
        struct_name = _string_value(region.get("struct_name")) or "unknown"
        example = {
            "symbol": region.get("symbol"),
            "offset": region.get("offset"),
            "end": region.get("end"),
            "struct_name": struct_name,
            "source": source,
        }
        bag.add("app_slot:typed_region", example=example)
        bag.add(f"app_slot_region:{_safe_part(struct_name)}", example=example)
        bag.add(f"app_slot_region_source:{_safe_part(source)}", example=example)
        field_refs = _dict_items(region.get("field_refs"))
        typed_field_refs = [field_ref for field_ref in field_refs if _string_value(field_ref.get("field_name"))]
        if typed_field_refs:
            bag.add("app_slot:typed_field_ref", len(typed_field_refs), example=example)
        for field_ref in typed_field_refs:
            field_example = {
                **example,
                "field_offset": field_ref.get("field_offset"),
                "field_name": field_ref.get("field_name"),
                "field_path": _field_path_text(struct_name, field_ref),
            }
            if field_ref.get("field_inherited") is True:
                bag.add("app_slot:inherited_field_ref", example=field_example)
            if field_ref.get("field_nested") is True:
                bag.add("app_slot:nested_field_ref", example=field_example)
            field_path = _field_path_text(struct_name, field_ref)
            if field_path:
                bag.add(f"app_slot_field_path:{_safe_part(field_path)}", example=field_example)
    for gap in _dict_items(app_slot_analysis.get("field_gaps")):
        coverage = _string_value(gap.get("coverage")) or "unknown"
        field_path = _field_path_text(_string_value(gap.get("struct_name")) or "unknown", gap)
        example = {
            "region_id": gap.get("region_id"),
            "start": gap.get("start"),
            "end": gap.get("end"),
            "size": gap.get("size"),
            "coverage": coverage,
            "field_path": field_path,
        }
        bag.add("app_slot:field_gap", example=example)
        bag.add(f"app_slot_field_gap:{_safe_part(coverage)}", example=example)
        if field_path:
            bag.add(f"app_slot_field_gap_path:{_safe_part(field_path)}", example=example)
    for gap in _dict_items(app_slot_analysis.get("gaps")):
        bag.add(
            "app_slot:gap",
            example={
                "start": gap.get("start"),
                "end": gap.get("end"),
                "size": gap.get("size"),
                "after": gap.get("after"),
                "before": gap.get("before"),
            },
        )
    for suggestion in _dict_items(app_slot_analysis.get("suggestions")):
        if suggestion.get("kind") != "app_slot_region":
            continue
        metadata = suggestion.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        struct_name = _string_value(metadata.get("struct_name")) or "unknown"
        bag.add(
            "app_slot:suggested_region",
            example={
                "symbol": metadata.get("symbol"),
                "offset": metadata.get("offset"),
                "size": metadata.get("size"),
                "struct_name": struct_name,
                "action": suggestion.get("action"),
            },
        )
    for arg in _dict_items(app_slot_analysis.get("untyped_api_args")):
        function_name = _string_value(arg.get("function")) or "unknown"
        reason = _string_value(arg.get("reason")) or "unknown"
        example = {
            "symbol": arg.get("symbol"),
            "offset": arg.get("displacement"),
            "function": function_name,
            "input_name": arg.get("input_name"),
            "register": arg.get("register"),
            "type_name": arg.get("type_name"),
            "reason": reason,
        }
        bag.add("app_slot:untyped_api_arg", example=example)
        bag.add(f"app_slot_api_arg:{_safe_part(function_name)}", example=example)
        bag.add(f"app_slot_api_arg_reason:{_safe_part(reason)}", example=example)


def _is_generated_app_slot_region_source(source: str) -> bool:
    return source == "platform_api_arg"


def _platform_typed_access_parts(access: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None]:
    root_struct = _string_value(access.get("root_struct_name"))
    owner_struct = _string_value(access.get("owner_struct_name"))
    field_name = _string_value(access.get("field_name"))
    field_expr = _string_value(access.get("field_expr"))
    return root_struct, owner_struct, field_name, field_expr


def _typed_access_provenance_id(access: dict[str, Any]) -> int | None:
    return _int_value(access.get("type_provenance_kind_id"))


def _typed_access_provenance_name(kind_id: int | None) -> str | None:
    if kind_id is None:
        return None
    return TYPE_PROVENANCE_NAMES.get(kind_id, "unknown")


def _typed_access_provenance(access: dict[str, Any]) -> tuple[int | None, str | None, int | None, int | None]:
    kind_id = _typed_access_provenance_id(access)
    return (
        kind_id,
        _typed_access_provenance_name(kind_id),
        _int_value(access.get("type_provenance_section")),
        _int_value(access.get("type_provenance_offset")),
    )


def _unresolved_typed_access_classification_id(access: dict[str, Any]) -> int | None:
    return _int_value(access.get("classification_id"))


def _unresolved_typed_access_classification_name(access: dict[str, Any]) -> str | None:
    classification_id = _unresolved_typed_access_classification_id(access)
    if classification_id is None:
        return None
    return UNRESOLVED_TYPED_ACCESS_CLASSIFICATION_NAMES.get(classification_id, "unknown")


def _add_platform_typed_access_features(
    bag: FeatureBag,
    access: dict[str, Any],
    *,
    example: dict[str, object],
) -> None:
    root_struct, owner_struct, field_name, field_expr = _platform_typed_access_parts(access)
    owner_for_feature = owner_struct or root_struct
    type_provenance_kind_id, type_provenance_kind, _type_provenance_section, _type_provenance_offset = (
        _typed_access_provenance(access)
    )
    bag.add("platform_typed_access:any", example=example)
    if type_provenance_kind_id is not None:
        bag.add(f"platform_typed_access_provenance:{_safe_part(type_provenance_kind)}", example=example)
    if root_struct:
        bag.add(f"platform_typed_access_struct:{_safe_part(root_struct)}", example=example)
        bag.add(f"struct:{_safe_part(root_struct)}", example=example)
    if owner_struct:
        bag.add(f"platform_typed_access_owner:{_safe_part(owner_struct)}", example=example)
    if field_name:
        bag.add(f"platform_field:{_safe_part(field_name)}", example=example)
        if owner_for_feature:
            bag.add(f"platform_struct_field:{_safe_part(owner_for_feature)}.{_safe_part(field_name)}", example=example)
    if field_expr and owner_for_feature:
        bag.add(f"platform_field_expr:{_safe_part(owner_for_feature)}.{_safe_part(field_expr)}", example=example)
    if access.get("inherited") is True or access.get("inherited") == 1:
        bag.add("platform_typed_access:inherited", example=example)
    if access.get("nested") is True or access.get("nested") == 1:
        bag.add("platform_typed_access:nested", example=example)


def _add_platform_unresolved_typed_access_features(
    bag: FeatureBag,
    access: dict[str, Any],
    *,
    example: dict[str, object],
) -> None:
    root_struct = _string_value(access.get("root_struct_name"))
    classification_id = _unresolved_typed_access_classification_id(access)
    classification = _unresolved_typed_access_classification_name(access)
    container_struct = _string_value(access.get("container_struct_name"))
    refined_struct = _string_value(access.get("refined_struct_name"))
    refinement_applied = access.get("refinement_applied") is True or access.get("refinement_applied") == 1
    bag.add("typed_base_unresolved_field", example=example)
    bag.add("platform_unresolved_typed_access:any", example=example)
    if classification:
        bag.add(f"platform_unresolved_typed_access:{_safe_part(classification)}", example=example)
    if root_struct:
        bag.add(f"platform_unresolved_typed_access_struct:{_safe_part(root_struct)}", example=example)
        bag.add(f"struct:{_safe_part(root_struct)}", example=example)
        if classification_id == UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION:
            bag.add(f"platform_prefix_extension_struct:{_safe_part(root_struct)}", example=example)
    if classification_id == UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION and container_struct:
        bag.add(f"platform_prefix_extension_candidate:{_safe_part(container_struct)}", example=example)
    if classification_id == UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE and root_struct:
        bag.add(f"platform_custom_tail_struct:{_safe_part(root_struct)}", example=example)
    if refinement_applied:
        bag.add("platform_type_refinement:applied", example=example)
        if root_struct:
            bag.add(f"platform_type_refinement_from:{_safe_part(root_struct)}", example=example)
        if refined_struct:
            bag.add(f"platform_type_refinement_to:{_safe_part(refined_struct)}", example=example)


def _orphan_code_signal_example(section_index: int, signal: dict[str, Any]) -> dict[str, object]:
    offset = _int_value(signal.get("offset"))
    reason = _orphan_code_signal_reason_name(signal)
    status = _orphan_code_signal_status_name(signal)
    example = _offset_example(section_index, offset, f"{reason}:{status}")
    for key in ("size", "terminal_offset", "confidence", "required_cpu", "instruction_count", "decode_conflict_count"):
        value = _int_value(signal.get(key))
        if value is not None:
            example[key] = value
    terminal_flow = _orphan_code_signal_terminal_flow_name(signal)
    if terminal_flow:
        example["terminal_flow"] = terminal_flow
    context = _orphan_code_signal_context_name(signal)
    if context:
        example["context"] = context
    missing_inbound = _orphan_code_signal_inbound_name(signal)
    if missing_inbound:
        example["missing_inbound"] = missing_inbound
    nearby_data_class = _orphan_code_signal_nearby_data_name(signal)
    if nearby_data_class:
        example["nearby_data_class"] = nearby_data_class
    nearby_data_relation = _orphan_code_signal_nearby_data_relation_name(signal)
    if nearby_data_relation:
        example["nearby_data_relation"] = nearby_data_relation
    for key in ("nearby_data_offset", "nearby_data_distance"):
        value = _int_value(signal.get(key))
        if value is not None:
            example[key] = value
    detail = _string_value(signal.get("detail"))
    if detail:
        example["detail"] = detail
    return example


def _add_orphan_code_signal_features(bag: FeatureBag, section_index: int, signal: dict[str, Any]) -> None:
    reason = _orphan_code_signal_reason_name(signal)
    status = _orphan_code_signal_status_name(signal)
    status_id = _int_value(signal.get("status_id"), 0) or 0
    terminal_flow = _orphan_code_signal_terminal_flow_name(signal)
    required_cpu = _int_value(signal.get("required_cpu"))
    instruction_count = _int_value(signal.get("instruction_count"))
    decode_conflict_count = _int_value(signal.get("decode_conflict_count"))
    context = _orphan_code_signal_context_name(signal)
    missing_inbound = _orphan_code_signal_inbound_name(signal)
    nearby_data_class = _orphan_code_signal_nearby_data_name(signal)
    nearby_data_relation = _orphan_code_signal_nearby_data_relation_name(signal)
    nearby_data_offset = _int_value(signal.get("nearby_data_offset"))
    nearby_data_distance = _int_value(signal.get("nearby_data_distance"))
    example = _orphan_code_signal_example(section_index, signal)
    bag.add("orphan-code:signal", example=example)
    bag.add(f"orphan-code:reason:{_safe_part(reason)}", example=example)
    bag.add(f"orphan-code:status:{_safe_part(status)}", example=example)
    bag.add(f"orphan-code:{_safe_part(reason)}:{_safe_part(status)}", example=example)
    if terminal_flow:
        bag.add(f"orphan-code:terminal_flow:{_safe_part(terminal_flow)}", example=example)
    if required_cpu is not None:
        bag.add(f"orphan-code:required_cpu:{required_cpu}", example=example)
    if instruction_count is not None:
        bag.add("orphan-code:has_instruction_count", example=example)
        bag.add(f"orphan-code:instruction_count:{instruction_count}", example=example)
    if decode_conflict_count is not None and decode_conflict_count > 0:
        bag.add("orphan-code:decode_conflict", example=example)
    if context:
        bag.add(f"orphan-code:context:{_safe_part(context)}", example=example)
    if missing_inbound and _orphan_code_signal_has_actionable_missing_inbound(status_id):
        bag.add(f"orphan-code:missing_inbound:{_safe_part(missing_inbound)}", example=example)
    if nearby_data_class:
        bag.add(f"orphan-code:nearby_data:{_safe_part(nearby_data_class)}", example=example)
        if nearby_data_offset is not None:
            bag.add("orphan-code:nearby_data:located", example=example)
        if nearby_data_distance is not None:
            bag.add(f"orphan-code:nearby_data_distance:{nearby_data_distance}", example=example)
        if nearby_data_relation:
            bag.add(
                f"orphan-code:nearby_data:{_safe_part(nearby_data_relation)}:{_safe_part(nearby_data_class)}",
                example=example,
            )


def _add_orphan_code_signal_summary_features(analysis: dict[str, Any], bag: FeatureBag) -> None:
    summary = analysis.get("orphan_code_signal_summary")
    if not isinstance(summary, dict):
        return
    total = _int_value(analysis.get("orphan_code_signal_count"), 0) or 0
    if total <= 0:
        return
    example: dict[str, Any] = {"signal_count": total}
    bag.add("orphan-code:summary", total, example=example)
    for group_name, feature_prefix in (("status", "orphan-code:summary:status"),):
        group = summary.get(group_name)
        if not isinstance(group, dict):
            continue
        for name, value in sorted(group.items()):
            count = _int_value(value, 0) or 0
            if count <= 0:
                continue
            group_example = dict(example)
            group_example[group_name] = name
            group_example["count"] = count
            bag.add(f"{feature_prefix}:{_safe_part(str(name))}", count, example=group_example)


def _orphan_code_signal_reason_name(signal: dict[str, Any]) -> str:
    return ORPHAN_CODE_SIGNAL_REASON_NAMES.get(_int_value(signal.get("reason_id"), 0) or 0, "unknown")


def _orphan_code_signal_status_name(signal: dict[str, Any]) -> str:
    return ORPHAN_CODE_SIGNAL_STATUS_NAMES.get(_int_value(signal.get("status_id"), 0) or 0, "unknown")


def _orphan_code_signal_has_actionable_missing_inbound(status_id: int) -> bool:
    return status_id == ORPHAN_CODE_SIGNAL_STATUS_UNRESOLVED


def _orphan_code_signal_terminal_flow_name(signal: dict[str, Any]) -> str | None:
    return SIM_FLOW_NAMES.get(_int_value(signal.get("terminal_flow_kind"), 0) or 0)


def _orphan_code_signal_context_name(signal: dict[str, Any]) -> str | None:
    return ORPHAN_CODE_SIGNAL_CONTEXT_NAMES.get(_int_value(signal.get("context_id"), 0) or 0)


def _orphan_code_signal_inbound_name(signal: dict[str, Any]) -> str | None:
    return ORPHAN_CODE_SIGNAL_INBOUND_NAMES.get(_int_value(signal.get("missing_inbound_id"), 0) or 0)


def _orphan_code_signal_nearby_data_name(signal: dict[str, Any]) -> str | None:
    return _data_role_name(_int_value(signal.get("nearby_data_flags"), 0) or 0)


def _orphan_code_signal_nearby_data_relation_name(signal: dict[str, Any]) -> str | None:
    return ORPHAN_CODE_SIGNAL_NEARBY_DATA_RELATION_NAMES.get(
        _int_value(signal.get("nearby_data_relation_id"), 0) or 0
    )


def _indirect_site_example(section_index: int, site: dict[str, Any]) -> dict[str, object]:
    offset = _int_value(site.get("offset"))
    status = _recovered_indirect_status_name(site)
    shape = _recovered_indirect_shape_name(site)
    flow = _recovered_indirect_flow_name(site)
    example = _offset_example(section_index, offset, f"{flow} {shape} {status}")
    example["status"] = status
    example["shape"] = shape
    example["flow"] = flow
    for key in ("source_offset", "source_size", "operand_index"):
        value = _int_value(site.get(key))
        if value is not None:
            example[key] = value
    target = _int_value(site.get("target"))
    if target is not None:
        example["target"] = target
    target_count = _int_value(site.get("target_count"))
    if target_count is not None:
        example["target_count"] = target_count
    detail = _string_value(site.get("detail"))
    if detail:
        example["detail"] = detail
    return example


def _indirect_site_source_pattern(record: dict[str, Any]) -> str:
    source_pattern_id = _int_value(record.get("source_pattern_id"), 0) or 0
    return RECOVERED_INDIRECT_SOURCE_PATTERN_NAMES.get(source_pattern_id, "unknown")


def _structured_table_source_pattern(record: dict[str, Any]) -> str | None:
    source_pattern_id = _int_value(record.get("source_pattern_id"), 0) or 0
    if source_pattern_id != 0:
        return STRUCTURED_DATA_SOURCE_PATTERN_NAMES.get(source_pattern_id, "unknown")
    return None


def _table_kind_name(record: dict[str, Any]) -> str:
    return TABLE_KIND_NAMES.get(_int_value(record.get("table_kind_id"), 0) or 0, "unknown")


def _table_base_expression_name(record: dict[str, Any]) -> str | None:
    base_expression_id = _int_value(record.get("base_expression_id"), 0) or 0
    if base_expression_id != 0:
        return TABLE_BASE_EXPRESSION_NAMES.get(base_expression_id, "unknown")
    return None


def _table_role_name(record: dict[str, Any]) -> str:
    role_flags = _int_value(record.get("role_flags"), 0) or 0
    return _data_role_name(role_flags) or "unknown"


def _add_indirect_site_features(bag: FeatureBag, section_index: int, site: dict[str, Any]) -> None:
    status = _recovered_indirect_status_name(site)
    shape = _recovered_indirect_shape_name(site)
    flow = _recovered_indirect_flow_name(site)
    source_pattern = _indirect_site_source_pattern(site)
    example = _indirect_site_example(section_index, site)
    example["source_pattern"] = source_pattern
    bag.add("analysis:indirect_site", example=example)
    bag.add(f"analysis:indirect_site:status:{_safe_part(status)}", example=example)
    bag.add(f"analysis:indirect_site:shape:{_safe_part(shape)}", example=example)
    bag.add(f"analysis:indirect_site:flow:{_safe_part(flow)}", example=example)
    bag.add(f"analysis:indirect_site:source_pattern:{_safe_part(source_pattern)}", example=example)


def _add_table_candidate_record_features(bag: FeatureBag, record: dict[str, Any]) -> None:
    section_index = _int_value(record.get("section_index"), 0)
    offset = _int_value(record.get("offset"))
    status = _recovered_indirect_status_name(record)
    shape = _recovered_indirect_shape_name(record)
    flow = _recovered_indirect_flow_name(record)
    source_pattern = _indirect_site_source_pattern(record)
    conflict_state = _conflict_state_name(record)
    example = _offset_example(section_index, offset, f"{flow} {shape} {status}")
    example["status"] = status
    example["shape"] = shape
    example["flow"] = flow
    example["source_pattern"] = source_pattern
    if conflict_state:
        example["conflict_state"] = conflict_state
    for key in ("source_offset", "source_size", "operand_index"):
        value = _int_value(record.get(key))
        if value is not None:
            example[key] = value
    table_bounds_status = _recovered_indirect_table_bounds_status_name(record)
    for key in ("expression_base_offset", "table_offset", "table_size", "table_entry_size", "table_entry_count"):
        value = _int_value(record.get(key))
        if value is not None:
            example[key] = value
    example["table_bounds_status"] = table_bounds_status
    target = _int_value(record.get("target"))
    if target is not None:
        example["target"] = target
    target_count = _int_value(record.get("target_count"))
    if target_count is not None:
        example["target_count"] = target_count
    detail = _string_value(record.get("detail"))
    if detail:
        example["detail"] = detail
    bag.add("table:candidate_unresolved", example=example)
    bag.add(f"table:candidate_unresolved:source_pattern:{_safe_part(source_pattern)}", example=example)
    bag.add(f"table:candidate_unresolved:status:{_safe_part(status)}", example=example)
    bag.add(f"table:candidate_unresolved:shape:{_safe_part(shape)}", example=example)
    bag.add(f"table:candidate_unresolved:flow:{_safe_part(flow)}", example=example)
    if conflict_state:
        bag.add(f"table:candidate_unresolved:conflict_state:{_safe_part(conflict_state)}", example=example)
    if _int_value(record.get("source_size")) is not None:
        bag.add("table:candidate_unresolved:source_range", example=example)
    if _int_value(record.get("expression_base_offset")) is not None:
        bag.add("table:candidate_unresolved:expression_base", example=example)
    if _int_value(record.get("table_offset")) is not None:
        bag.add("table:candidate_unresolved:table_base", example=example)
    table_bounds_status_id = _int_value(record.get("table_bounds_status_id"), 0) or 0
    if _int_value(record.get("table_size")) is not None:
        bag.add("table:candidate_unresolved:table_bounds", example=example)
    if table_bounds_status_id != 0:
        bag.add(f"table:candidate_unresolved:table_bounds_status:{_safe_part(table_bounds_status)}",
            example=example)
    table_entry_size = _int_value(record.get("table_entry_size"))
    if table_entry_size is not None:
        bag.add(f"table:candidate_unresolved:entry_size:{table_entry_size}", example=example)


def _recovered_indirect_flow_name(record: dict[str, Any]) -> str:
    return RECOVERED_INDIRECT_FLOW_NAMES.get(_int_value(record.get("flow_kind"), 0) or 0, "unknown")


def _recovered_indirect_shape_name(record: dict[str, Any]) -> str:
    return RECOVERED_INDIRECT_SHAPE_NAMES.get(_int_value(record.get("shape_id"), 0) or 0, "unknown")


def _recovered_indirect_status_name(record: dict[str, Any]) -> str:
    return RECOVERED_INDIRECT_STATUS_NAMES.get(_int_value(record.get("status_id"), 0) or 0, "unknown")


def _recovered_indirect_table_bounds_status_name(record: dict[str, Any]) -> str:
    status_id = _int_value(record.get("table_bounds_status_id"), 0)
    return RECOVERED_INDIRECT_TABLE_BOUNDS_STATUS_NAMES.get(status_id or 0, "unknown")


def _add_analysis_features(analysis: dict[str, Any], bag: FeatureBag) -> None:
    findings = analysis.get("findings")
    if isinstance(findings, dict):
        required_cpu = findings.get("required_cpu")
        if isinstance(required_cpu, int) and required_cpu in CPU_NAMES:
            bag.add(f"cpu:{CPU_NAMES[required_cpu]}")
        violation_count = findings.get("cpu_violation_count")
        if isinstance(violation_count, int) and violation_count > 0:
            bag.add("diagnostic:cpu_violation", violation_count)
    _add_decompression_analysis_features(analysis, bag)
    _add_orphan_code_signal_summary_features(analysis, bag)
    for table in _dict_items(analysis.get("table_records")):
        role = _table_role_name(table)
        table_kind = _table_kind_name(table)
        section_index = _int_value(table.get("section_index"), 0)
        offset = _int_value(table.get("offset"))
        example = _offset_example(section_index, offset, table_kind)
        for key in ("size", "entry_size", "entry_count"):
            value = _int_value(table.get(key))
            if value is not None:
                example[key] = value
        source_pattern = _structured_table_source_pattern(table)
        if source_pattern:
            example["source_pattern"] = source_pattern
        base_expression = _table_base_expression_name(table)
        if base_expression:
            example["base_expression"] = base_expression
        conflict_state = _conflict_state_name(table)
        conflicted = _bool_value(table.get("conflicted"))
        if conflict_state:
            example["conflict_state"] = conflict_state
        example["conflicted"] = conflicted
        consumer_section = _int_value(table.get("consumer_section"))
        consumer_offset = _int_value(table.get("consumer_offset"))
        if consumer_section is not None and consumer_offset is not None:
            example["consumer_section"] = consumer_section
            example["consumer_offset"] = consumer_offset
        bag.add("table:any", example=example)
        bag.add(f"table:role:{_safe_part(role)}", example=example)
        bag.add(f"table:kind:{_safe_part(table_kind)}", example=example)
        if source_pattern:
            bag.add(f"table:source_pattern:{_safe_part(source_pattern)}", example=example)
        if conflicted:
            bag.add("table:conflict", example=example)
            if conflict_state:
                bag.add(f"table:conflict_state:{_safe_part(conflict_state)}", example=example)
        if base_expression:
            bag.add(f"table:base:{_safe_part(base_expression)}", example=example)
        if consumer_section is not None and consumer_offset is not None:
            bag.add("table:consumer", example=example)
        entry_size = _int_value(table.get("entry_size"))
        if entry_size is not None:
            bag.add(f"table:entry_size:{entry_size}", example=example)
    for record in _dict_items(analysis.get("table_candidate_records")):
        _add_table_candidate_record_features(bag, record)
    memory_layout_records = list(_dict_items(analysis.get("memory_layout_records")))
    for record in memory_layout_records:
        record_kind = _memory_layout_record_kind_name(record)
        memory_kind = _memory_layout_memory_kind_name(record)
        section_index = _int_value(record.get("section_index"), 0)
        source_offset = _int_value(record.get("source_offset"))
        example = _offset_example(section_index, source_offset, memory_kind)
        for key in (
            "record_kind_id", "source_size", "runtime_address", "runtime_size", "target_offset", "sink_address",
            "field_offset", "field_size", "address", "access_width", "owner_offset",
            "owner_range_start", "owner_range_size", "owner_range_end",
            "range_space_kind", "range_start", "range_size", "range_end", "effect_kind",
            "target_section_index", "displacement", "field_disp", "field_count", "layout_kind",
            "type_provenance_kind_id",
        ):
            value = _int_value(record.get(key))
            if value is not None:
                example[key] = value
        for key in (
            "layout_name", "base_symbol", "symbol", "root_struct_name", "owner_struct_name",
            "field_name", "field_expr", "classification", "type_provenance_kind",
            "access", "owner_kind", "owner_symbol", "owner_base_symbol",
            "effect_kind_name", "base_name", "symbol_name", "type_name", "sizeof_symbol",
        ):
            value = _string_value(record.get(key))
            if value:
                example[key] = value
        bag.add("memory-layout:any", example=example)
        bag.add(f"memory-layout:record:{_safe_part(record_kind)}", example=example)
        bag.add(f"memory-layout:kind:{_safe_part(memory_kind)}", example=example)
        layout_kind = _int_value(record.get("layout_kind"))
        layout_kind_name = BASE_LAYOUT_KIND_NAMES.get(layout_kind) if layout_kind is not None else None
        if layout_kind_name:
            bag.add(f"memory-layout:layout_kind:{_safe_part(layout_kind_name)}", example=example)
        root_struct = _string_value(record.get("root_struct_name")) or _string_value(record.get("owner_struct_name"))
        field_expr = _string_value(record.get("field_expr")) or _string_value(record.get("field_name"))
        if root_struct:
            bag.add(f"memory-layout:platform_struct:{_safe_part(root_struct)}", example=example)
        if field_expr:
            bag.add(f"memory-layout:platform_field:{_safe_part(field_expr)}", example=example)
        effect_kind = _int_value(record.get("effect_kind"))
        effect_kind_name = PLATFORM_EFFECT_NAMES.get(effect_kind) if effect_kind is not None else None
        if effect_kind_name:
            bag.add("memory-layout:storage_effect", example=example)
            bag.add(f"memory-layout:storage_effect:{_safe_part(effect_kind_name)}", example=example)
        if _int_value(record.get("sink_address")) is not None:
            bag.add("memory-layout:sink_address", example=example)
        range_space_kind = _int_value(record.get("range_space_kind"))
        if range_space_kind is not None:
            bag.add("memory-layout:range", example=example)
            bag.add(f"memory-layout:range_space:{range_space_kind}", example=example)
        range_size = _int_value(record.get("range_size"))
        if range_size is not None:
            bag.add(f"memory-layout:range_size:{range_size}", example=example)
        conflict_state = _conflict_state_name(record)
        conflict_state_id = _conflict_state_id(record)
        if conflict_state:
            example["conflict_state"] = conflict_state
        if conflict_state_id is not None and conflict_state_id != CONFLICT_STATE_CLEAN:
            bag.add(f"memory-layout:conflict_state:{_safe_part(conflict_state)}", example=example)
        if _bool_value(record.get("conflicted")):
            bag.add("memory-layout:conflict", example=example)
    _add_memory_layout_view_features(bag, memory_layout_records)
    for section in _dict_items(analysis.get("sections")):
        section_index = _int_value(section.get("section_index"), 0)
        for call in _dict_items(section.get("recovered_platform_calls")):
            library = _string_value(call.get("library_name")) or _string_value(call.get("note_base_name")) or "unknown"
            function = (
                _string_value(call.get("function_name"))
                or _string_value(call.get("symbol_name"))
                or _string_value(call.get("note_symbol_name"))
                or "unknown"
            ).removeprefix("_LVO")
            example = _offset_example(section_index, call.get("offset"), f"{library}/{function}")
            bag.add("os_call:any", example=example)
            bag.add(f"os_call_library:{_safe_part(library)}", example=example)
            bag.add(f"os:{_safe_part(library)}/{_safe_part(function)}", example=example)
            bag.add(f"os_library:{_safe_part(library)}", example=example)
            for feature in _device_call_features(function, call):
                bag.add(feature, example=example)
            available_since = _string_value(call.get("available_since"))
            if available_since:
                bag.add(f"os_version:min:{_safe_part(available_since)}")
            for item in _dict_items(call.get("inputs")):
                value_domain = _string_value(item.get("value_domain"))
                if value_domain:
                    bag.add(f"value_domain:{_safe_part(value_domain)}", example=example)
                i_struct = _string_value(item.get("i_struct"))
                if i_struct:
                    bag.add(f"struct:{_safe_part(i_struct)}", example=example)
            for item in _dict_items(call.get("outputs")):
                for reg in _list_strings(item.get("regs")):
                    bag.add(f"os_call_output_reg:{_safe_part(reg)}", example=example)
                value_domain = _string_value(item.get("value_domain"))
                if value_domain:
                    bag.add(f"value_domain:{_safe_part(value_domain)}", example=example)
                o_struct = _string_value(item.get("o_struct"))
                if o_struct:
                    bag.add(f"struct:{_safe_part(o_struct)}", example=example)
        for effect in _dict_items(section.get("recovered_platform_effects")):
            effect_kind = _int_value(effect.get("kind"))
            effect_kind_name = PLATFORM_EFFECT_NAMES.get(effect_kind) if effect_kind is not None else None
            base_name = _string_value(effect.get("base_name"))
            effect_example = _offset_example(section_index, effect.get("offset"), base_name or effect_kind_name)
            if effect_kind_name:
                bag.add(f"platform_effect:{effect_kind_name}", example=effect_example)
            if base_name:
                bag.add(f"platform_base:{_safe_part(base_name)}", example=effect_example)
                if effect_kind == PLATFORM_EFFECT_WRITE_BASE_SLOT:
                    bag.add("app_slot:base_slot", example=effect_example)
                    bag.add(f"app_slot_base:{_safe_part(base_name)}", example=effect_example)
            semantic_kind = _string_value(effect.get("semantic_kind"))
            if semantic_kind:
                bag.add(f"semantic:{_safe_part(semantic_kind)}")
            value_domain = _string_value(effect.get("value_domain_name"))
            if value_domain:
                bag.add(f"value_domain:{_safe_part(value_domain)}")
            type_name = _string_value(effect.get("type_name"))
            if type_name:
                bag.add(f"type:{_safe_part(type_name)}")
                storage_target = TYPED_STORAGE_EFFECT_TARGETS.get(effect_kind)
                if storage_target:
                    bag.add("typed_storage:any", example=effect_example)
                    bag.add(f"typed_storage_kind:{_safe_part(effect_kind_name or 'unknown')}", example=effect_example)
                    bag.add(f"typed_storage_type:{_safe_part(type_name)}", example=effect_example)
                    bag.add(f"typed_storage_target:{_safe_part(storage_target)}", example=effect_example)
        for ref in _dict_items(section.get("app_slot_refs")):
            access = _string_value(ref.get("access")) or "unknown"
            example = _offset_example(section_index, ref.get("offset"), _string_value(ref.get("displacement")))
            bag.add("app_slot:any", example=example)
            bag.add(f"app_slot:{_safe_part(access)}", example=example)
        for access in _dict_items(section.get("recovered_platform_typed_accesses")):
            _root_struct, _owner_struct, field_name, field_expr = _platform_typed_access_parts(access)
            example = _offset_example(section_index, access.get("offset"), field_expr or field_name)
            _add_platform_typed_access_features(bag, access, example=example)
        for access in _dict_items(section.get("recovered_platform_unresolved_typed_accesses")):
            root_struct = _string_value(access.get("root_struct_name"))
            displacement = _int_value(access.get("displacement"))
            example = _offset_example(section_index, access.get("offset"), root_struct)
            if displacement is not None:
                example["displacement"] = displacement
            example["struct_size"] = _int_value(access.get("struct_size"))
            _add_platform_unresolved_typed_access_features(bag, access, example=example)
        for runtime_view in _dict_items(section.get("runtime_views")):
            storage = _int_value(runtime_view.get("storage_address"))
            runtime = _int_value(runtime_view.get("runtime_address"))
            kind = _int_value(runtime_view.get("kind"))
            view_example = _offset_example(section_index, runtime_view.get("storage_offset"), None)
            size = _int_value(runtime_view.get("size"))
            if runtime is not None:
                view_example["runtime_address"] = runtime
            if size is not None:
                view_example["size"] = size
            if storage is not None or runtime is not None:
                view_example["text"] = f"storage=${_hex_int(storage)} runtime=${_hex_int(runtime)}"
            bag.add("runtime:view", example=view_example)
            if kind is not None:
                bag.add(f"runtime:view_kind:{kind}")
            materialized = runtime_view.get("materialized")
            reason = _int_value(runtime_view.get("materialization_reason"))
            reason_name = RUNTIME_VIEW_MATERIALIZATION_REASONS.get(reason or 0)
            if materialized is True:
                bag.add("runtime:view_materialized", example=view_example)
                if reason_name:
                    bag.add(f"runtime:view_materialized_reason:{_safe_part(reason_name)}", example=view_example)
            elif materialized is False:
                bag.add("runtime:suppressed_org_range", example=view_example)
                if reason_name:
                    bag.add(f"runtime:suppressed_org_reason:{_safe_part(reason_name)}", example=view_example)
                    if reason == RUNTIME_VIEW_SUPPRESSED_EXIT_TO_LARGER_RUNTIME_RANGE:
                        bag.add("suppressed-weak-org-range", example=view_example)
                        if runtime is not None and runtime < 0x100:
                            bag.add("low-vector-trampoline", example=view_example)
            relationship_kind = _int_value(runtime_view.get("relationship_kind"))
            relationship_name = RUNTIME_VIEW_RELATIONSHIP_NAMES.get(relationship_kind or RUNTIME_VIEW_RELATIONSHIP_NONE)
            if relationship_kind is not None and relationship_kind != RUNTIME_VIEW_RELATIONSHIP_NONE and relationship_name:
                related_runtime = _int_value(runtime_view.get("related_runtime_address"))
                relationship_example = view_example
                if related_runtime is not None:
                    relationship_example = dict(view_example)
                    relationship_example["related_runtime_address"] = related_runtime
                bag.add(f"runtime:view_relationship:{_safe_part(relationship_name)}", example=relationship_example)
                if related_runtime is not None:
                    bag.add("runtime:view_related_range", example=relationship_example)
                for role_feature in RUNTIME_VIEW_RELATIONSHIP_ROLE_FEATURES.get(relationship_kind, ()):
                    bag.add(role_feature, example=relationship_example)
            if storage is not None and runtime is not None and storage != runtime:
                bag.add("runtime:copied_code")
                if storage < 0x200 and runtime < 0x1000:
                    bag.add("runtime:copied_entry_stub")
        for signal in _dict_items(section.get("orphan_code_signals")):
            _add_orphan_code_signal_features(bag, section_index, signal)
        violation_count = _int_value(section.get("violation_count"), 0)
        if violation_count > 0:
            bag.add("diagnostic:analysis_violation", violation_count)
        indirect_sites = list(_dict_items(section.get("recovered_indirect_sites")))
        if indirect_sites:
            for site in indirect_sites:
                _add_indirect_site_features(bag, section_index, site)
        else:
            indirect_count = _int_value(section.get("recovered_indirect_site_count"), 0)
            if indirect_count > 0:
                bag.add("analysis:indirect_site", indirect_count)
        string_ref_count = _int_value(section.get("recovered_string_ref_count"), 0)
        if string_ref_count > 0:
            bag.add("data:string_ref", string_ref_count)


def _decompression_example(record: dict[str, Any]) -> dict[str, object]:
    section_index = _int_value(record.get("source_section"))
    if section_index is None:
        section_index = _int_value(record.get("source_section_index"))
    offset = _int_value(record.get("source_section_offset"))
    if offset is None:
        offset = _int_value(record.get("source_offset"))
    text = (
        _string_value(record.get("event_id"))
        or _string_value(record.get("event_kind"))
        or _string_value(record.get("codec_id"))
        or _string_value(record.get("codec_name"))
        or _string_value(record.get("kind"))
        or _string_value(record.get("status"))
        or "packed payload"
    )
    example = _offset_example(section_index, offset, text)
    packed_size = _int_value(record.get("packed_size"))
    if packed_size is not None:
        example["packed_size"] = packed_size
        if offset is not None:
            example["source_section_end_offset"] = offset + packed_size
    compressed_source_end = _int_value(record.get("compressed_source_section_end_offset"))
    if compressed_source_end is not None:
        example["compressed_source_section_end_offset"] = compressed_source_end
        if "source_section_end_offset" not in example:
            example["source_section_end_offset"] = compressed_source_end
    compressed_source_start = _int_value(record.get("compressed_source_section_offset"))
    if compressed_source_start is not None:
        example["compressed_source_section_offset"] = compressed_source_start
    decompressed_size = _int_value(record.get("decompressed_size"))
    if decompressed_size is not None:
        example["decompressed_size"] = decompressed_size
    runtime_copy_address = _int_value(record.get("runtime_copy_address"))
    if runtime_copy_address is not None:
        example["runtime_copy_address"] = runtime_copy_address
    runtime_copy_size = _int_value(record.get("runtime_copy_size"))
    if runtime_copy_size is not None:
        example["runtime_copy_size"] = runtime_copy_size
    runtime_copy_kind = _int_value(record.get("runtime_copy_kind"))
    if runtime_copy_kind is not None:
        example["runtime_copy_kind"] = runtime_copy_kind
    if isinstance(record.get("runtime_copy_conflicting"), bool):
        example["runtime_copy_conflicting"] = bool(record["runtime_copy_conflicting"])
    load_address = _int_value(record.get("load_address"))
    if load_address is not None:
        example["load_address"] = load_address
    target_start_address = _int_value(record.get("target_start_address"))
    if target_start_address is not None:
        example["target_start_address"] = target_start_address
        if load_address is None:
            example["load_address"] = target_start_address
    target_end_address = _int_value(record.get("target_end_address"))
    if target_end_address is not None:
        example["target_end_address"] = target_end_address
    entrypoint = _int_value(record.get("entrypoint"))
    if entrypoint is not None:
        example["entrypoint"] = entrypoint
    initial_control_target = _int_value(record.get("initial_control_target"))
    if initial_control_target is not None:
        example["initial_control_target"] = initial_control_target
    event_id = _string_value(record.get("event_id"))
    if event_id:
        example["event_id"] = event_id
    event_kind_id = _int_value(record.get("event_kind_id"), 0) or 0
    event_kind = DECOMPRESSION_EVENT_KIND_NAMES.get(event_kind_id)
    if event_kind:
        example["event_kind_id"] = event_kind_id
        example["event_kind"] = event_kind
    payload_role_id = _int_value(record.get("payload_role_id"), 0) or 0
    payload_role = DECOMPRESSION_PAYLOAD_ROLE_NAMES.get(payload_role_id)
    if payload_role:
        example["payload_role_id"] = payload_role_id
        example["payload_role"] = payload_role
    parent_remains_active_id = _int_value(record.get("parent_remains_active_id"), 0)
    parent_remains_active = DECOMPRESSION_PARENT_REMAINS_ACTIVE_NAMES.get(parent_remains_active_id or 0)
    if parent_remains_active:
        example["parent_remains_active_id"] = parent_remains_active_id or 0
        example["parent_remains_active"] = parent_remains_active
    source_kind_id = _int_value(record.get("source_kind_id"), 0) or 0
    source_kind = DECOMPRESSION_SOURCE_KIND_NAMES.get(source_kind_id)
    if source_kind:
        example["source_kind"] = source_kind
    provider_id = _string_value(record.get("provider_id"))
    if provider_id:
        example["provider_id"] = provider_id
    decompressor_section = _int_value(record.get("decompressor_code_section"))
    if decompressor_section is not None:
        example["decompressor_code_section"] = decompressor_section
    decompressor_entry = _int_value(record.get("decompressor_entry_offset"))
    if decompressor_entry is not None:
        example["decompressor_entry_offset"] = decompressor_entry
    unpacker_marker = _int_value(record.get("unpacker_marker_offset"))
    if unpacker_marker is not None:
        example["unpacker_marker_offset"] = unpacker_marker
    copied_stub_storage = _int_value(record.get("copied_stub_storage_offset"))
    if copied_stub_storage is not None:
        example["copied_stub_storage_offset"] = copied_stub_storage
    copied_stub_runtime = _int_value(record.get("copied_stub_runtime_address"))
    if copied_stub_runtime is not None:
        example["copied_stub_runtime_address"] = copied_stub_runtime
    copied_stub_transfer = _int_value(record.get("copied_stub_transfer_offset"))
    if copied_stub_transfer is not None:
        example["copied_stub_transfer_offset"] = copied_stub_transfer
    return example


def _decompression_decompressor_features(record: dict[str, Any]) -> list[str]:
    features: list[str] = []
    source_section = _int_value(record.get("source_section"))
    if source_section is None:
        source_section = _int_value(record.get("source_section_index"))
    decompressor_section = _int_value(record.get("decompressor_code_section"))
    decompressor_entry = _int_value(record.get("decompressor_entry_offset"))
    if decompressor_section is not None and decompressor_entry is not None:
        features.append("decompression:decompressor_code")
        features.append(f"decompression:decompressor_entry:{decompressor_section}:{decompressor_entry:08X}")
    unpacker_marker = _int_value(record.get("unpacker_marker_offset"))
    if source_section is not None and unpacker_marker is not None:
        features.append("decompression:unpacker_marker")
        features.append(f"decompression:unpacker_marker:{source_section}:{unpacker_marker:08X}")
    copied_stub_storage = _int_value(record.get("copied_stub_storage_offset"))
    if source_section is not None and copied_stub_storage is not None:
        features.append("decompression:copied_stub")
        features.append(f"decompression:copied_stub_storage:{source_section}:{copied_stub_storage:08X}")
    copied_stub_runtime = _int_value(record.get("copied_stub_runtime_address"))
    if copied_stub_runtime is not None:
        features.append("decompression:copied_stub_runtime")
        features.append(f"decompression:copied_stub_runtime:{copied_stub_runtime:08X}")
    copied_stub_transfer = _int_value(record.get("copied_stub_transfer_offset"))
    if copied_stub_transfer is not None:
        features.append("decompression:copied_stub_transfer")
        features.append(f"decompression:copied_stub_transfer:{copied_stub_transfer:08X}")
    return features


def _decompression_source_range_features(record: dict[str, Any]) -> list[str]:
    features: list[str] = []
    section_index = _int_value(record.get("source_section"))
    if section_index is None:
        section_index = _int_value(record.get("source_section_index"))
    offset = _int_value(record.get("source_section_offset"))
    if offset is None:
        offset = _int_value(record.get("source_offset"))
    end_offset = _int_value(record.get("source_section_end_offset"))
    compressed_source_offset = _int_value(record.get("compressed_source_section_offset"))
    compressed_source_end = _int_value(record.get("compressed_source_section_end_offset"))
    if offset is None:
        offset = compressed_source_offset
    if end_offset is None:
        end_offset = compressed_source_end
    packed_size = _int_value(record.get("packed_size"))
    if end_offset is None and offset is not None and packed_size is not None:
        end_offset = offset + packed_size
    if section_index is not None:
        features.append("decompression:source_section")
        features.append(f"decompression:source_section:{section_index}")
    if section_index is not None and offset is not None:
        features.append("decompression:source_offset")
        features.append(f"decompression:source_offset:{section_index}:{offset:08X}")
    if section_index is not None and offset is not None and end_offset is not None and end_offset >= offset:
        features.append("decompression:source_range")
        features.append(f"decompression:source_range:{section_index}:{offset:08X}-{end_offset:08X}")
    if section_index is not None and compressed_source_offset is not None and compressed_source_end is not None:
        features.append("decompression:compressed_source_range")
        features.append(
            f"decompression:compressed_source_range:{section_index}:{compressed_source_offset:08X}-{compressed_source_end:08X}"
        )
    if packed_size is not None:
        features.append("decompression:packed_size")
    return features


def _decompression_output_address_features(record: dict[str, Any]) -> list[str]:
    features: list[str] = []
    load_address = _int_value(record.get("load_address"))
    if load_address is None:
        load_address = _int_value(record.get("target_start_address"))
    if load_address is not None:
        features.append("decompression:output_load_address")
        features.append(f"decompression:output_load_address:{load_address:08X}")
        features.append("absolute-depack-dest")
    entrypoint = _int_value(record.get("entrypoint"))
    if entrypoint is not None:
        features.append("decompression:entrypoint")
        features.append(f"decompression:entrypoint:{entrypoint:08X}")
        features.append("decompressed-entrypoint")
    return features


def _decompression_source_load_entry_features(record: dict[str, Any]) -> list[str]:
    section_index = _int_value(record.get("source_section"))
    if section_index is None:
        section_index = _int_value(record.get("source_section_index"))
    offset = _int_value(record.get("source_section_offset"))
    if offset is None:
        offset = _int_value(record.get("source_offset"))
    end_offset = _int_value(record.get("source_section_end_offset"))
    compressed_source_offset = _int_value(record.get("compressed_source_section_offset"))
    compressed_source_end = _int_value(record.get("compressed_source_section_end_offset"))
    if offset is None:
        offset = compressed_source_offset
    if end_offset is None:
        end_offset = compressed_source_end
    packed_size = _int_value(record.get("packed_size"))
    if end_offset is None and offset is not None and packed_size is not None:
        end_offset = offset + packed_size
    load_address = _int_value(record.get("load_address"))
    if load_address is None:
        load_address = _int_value(record.get("target_start_address"))
    entrypoint = _int_value(record.get("entrypoint"))
    if section_index is None or offset is None or end_offset is None or load_address is None or entrypoint is None:
        return []
    return [
        "decompression:source_load_entry",
        (
            f"decompression:source_load_entry:{section_index}:{offset:08X}-{end_offset:08X}:"
            f"{load_address:08X}:{entrypoint:08X}"
        ),
    ]


def _decompression_pattern_features(record: dict[str, Any]) -> list[str]:
    features: list[str] = []
    source_kind_id = _int_value(record.get("source_kind_id"), 0) or 0
    codec_id = _string_value(record.get("codec_id"))
    if source_kind_id == DECOMPRESSION_SOURCE_SELF_DECRUNCHER:
        features.append("decompression:pattern:absolute_self_decrunch_transfer")
        if _int_value(record.get("simulated_output_size")) is not None:
            features.append("decompression:pattern:simulated_self_decrunch_output")
    if source_kind_id == DECOMPRESSION_SOURCE_RECOGNIZED_UNPACKER:
        features.append("decompression:pattern:recognized_unpacker")
        if codec_id:
            features.append(f"decompression:pattern:recognized_unpacker:{_safe_part(codec_id)}")
    if _int_value(record.get("runtime_copy_address")) is not None:
        features.append("decompression:pattern:runtime_copy_to_absolute")
    return features


def _decompression_unmaterialized_features(status_id: int | None, reason_id: int | None) -> list[str]:
    if status_id in (None, 0, DECOMPRESSION_STATUS_MATERIALIZABLE, DECOMPRESSION_STATUS_SIMULATED_OUTPUT_OBSERVED):
        return []
    features = ["decompression:unmaterialized_work_item"]
    reason = DECOMPRESSION_REASON_NAMES.get(reason_id or 0)
    if reason:
        features.append(f"decompression:work_item_reason:{_safe_part(reason)}")
    return features


def _add_decompression_analysis_features(analysis: dict[str, Any], bag: FeatureBag) -> None:
    for payload in _dict_items(analysis.get("packed_payloads")):
        example = _decompression_example(payload)
        found = payload.get("found")
        if found is False or found == 0:
            bag.add("unsupported-compressor", example=example)
            continue
        bag.add("compressed-payload", example=example)
        codec_id = _string_value(payload.get("codec_id"))
        if codec_id:
            bag.add(f"compressed:{_safe_part(codec_id)}", example=example)
        provider_id = _string_value(payload.get("provider_id"))
        if provider_id:
            bag.add(f"decompression:provider:{_safe_part(provider_id)}", example=example)
        codec_support = DECOMPRESSION_CODEC_SUPPORT_NAMES.get(_int_value(payload.get("codec_support_id"), 0) or 0)
        if codec_support:
            bag.add(f"decompression:codec_support:{_safe_part(codec_support)}", example=example)
        if _int_value(payload.get("decompressed_size")) is not None:
            bag.add("decompression:has_output_size", example=example)
        if _string_value(payload.get("decompressed_sha256")):
            bag.add("decompression:has_output_hash", example=example)
        if _string_value(payload.get("diagnostic")):
            bag.add("decompression:diagnostic", example=example)
        for feature in _decompression_source_range_features(payload):
            bag.add(feature, example=example)
        for feature in _decompression_output_address_features(payload):
            bag.add(feature, example=example)
        for feature in _decompression_source_load_entry_features(payload):
            bag.add(feature, example=example)
    for suggestion in _dict_items(analysis.get("derived_target_suggestions")):
        example = _decompression_example(suggestion)
        kind_id = _int_value(suggestion.get("kind_id"), 0) or 0
        kind = DERIVED_TARGET_SUGGESTION_KIND_NAMES.get(kind_id, "unknown")
        bag.add(f"derived_target_suggestion:{_safe_part(kind)}", example=example)
        if kind_id == DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD:
            bag.add("derived-decompressed-target", example=example)
        status_id = _int_value(suggestion.get("status_id"), 0) or 0
        status = DECOMPRESSION_STATUS_NAMES.get(status_id)
        if status:
            bag.add(f"derived_target_suggestion_status:{_safe_part(status)}", example=example)
        reason_id = _int_value(suggestion.get("reason_id"), 0) or 0
        reason = DECOMPRESSION_REASON_NAMES.get(reason_id)
        if reason:
            bag.add(f"derived_target_suggestion_reason:{_safe_part(reason)}", example=example)
        for feature in _decompression_unmaterialized_features(status_id, reason_id):
            bag.add(feature, example=example)
        for feature in _decompression_source_range_features(suggestion):
            bag.add(feature, example=example)
        for feature in _decompression_output_address_features(suggestion):
            bag.add(feature, example=example)
        for feature in _decompression_source_load_entry_features(suggestion):
            bag.add(feature, example=example)
        runtime_copy_address = _int_value(suggestion.get("runtime_copy_address"))
        if runtime_copy_address is not None:
            bag.add("decompression:runtime_copy", example=example)
            runtime_copy_kind = _int_value(suggestion.get("runtime_copy_kind"))
            if runtime_copy_kind is not None:
                bag.add(f"decompression:runtime_copy_kind:{runtime_copy_kind}", example=example)
            if suggestion.get("runtime_copy_conflicting") is True:
                bag.add("decompression:runtime_copy_conflicting", example=example)
            else:
                bag.add("decompression:runtime_copy_non_conflicting", example=example)
            runtime_copy_size = _int_value(suggestion.get("runtime_copy_size"))
            packed_size = _int_value(suggestion.get("packed_size"))
            if runtime_copy_size is not None and packed_size is not None:
                if runtime_copy_size == packed_size:
                    bag.add("decompression:runtime_copy_exact_size", example=example)
                elif runtime_copy_size < packed_size:
                    bag.add("decompression:runtime_copy_short", example=example)
                else:
                    bag.add("decompression:runtime_copy_oversize", example=example)
        for feature in _decompression_pattern_features(suggestion):
            bag.add(feature, example=example)
    for event in _dict_items(analysis.get("decompression_events")):
        example = _decompression_example(event)
        event_kind_id = _int_value(event.get("event_kind_id"), 0) or 0
        event_kind = DECOMPRESSION_EVENT_KIND_NAMES.get(event_kind_id, "unknown")
        bag.add(f"decompression:event:{_safe_part(event_kind)}", example=example)
        if _string_value(event.get("event_id")):
            bag.add("decompression:has_event_id", example=example)
        status_id = _int_value(event.get("status_id"), 0) or 0
        status = DECOMPRESSION_STATUS_NAMES.get(status_id)
        if status:
            bag.add(f"decompression:event_status:{_safe_part(status)}", example=example)
        reason_id = _int_value(event.get("reason_id"), 0) or 0
        reason = DECOMPRESSION_REASON_NAMES.get(reason_id)
        if reason:
            bag.add(f"decompression:event_reason:{_safe_part(reason)}", example=example)
        for feature in _decompression_unmaterialized_features(status_id, reason_id):
            bag.add(feature, example=example)
        payload_role = DECOMPRESSION_PAYLOAD_ROLE_NAMES.get(_int_value(event.get("payload_role_id"), 0) or 0)
        if payload_role:
            bag.add(f"decompression:payload_role:{_safe_part(payload_role)}", example=example)
        source_kind = DECOMPRESSION_SOURCE_KIND_NAMES.get(_int_value(event.get("source_kind_id"), 0) or 0)
        if source_kind:
            bag.add(f"decompression:source_kind:{_safe_part(source_kind)}", example=example)
        provider_id = _string_value(event.get("provider_id"))
        if provider_id:
            bag.add(f"decompression:provider:{_safe_part(provider_id)}", example=example)
        codec_id = _string_value(event.get("codec_id"))
        if codec_id:
            bag.add(f"decompression:codec:{_safe_part(codec_id)}", example=example)
        parent_remains_active = DECOMPRESSION_PARENT_REMAINS_ACTIVE_NAMES.get(
            _int_value(event.get("parent_remains_active_id"), 0) or 0
        )
        if parent_remains_active:
            bag.add(f"decompression:parent_remains_active:{_safe_part(parent_remains_active)}", example=example)
        codec_support = DECOMPRESSION_CODEC_SUPPORT_NAMES.get(_int_value(event.get("codec_support_id"), 0) or 0)
        if codec_support:
            bag.add(f"decompression:codec_support:{_safe_part(codec_support)}", example=example)
        if _int_value(event.get("simulated_output_size")) is not None:
            bag.add("decompression:simulated_output", example=example)
        if _string_value(event.get("simulated_output_sha256")):
            bag.add("decompression:simulated_output_hash", example=example)
        for feature in _decompression_decompressor_features(event):
            bag.add(feature, example=example)
        for feature in _decompression_source_range_features(event):
            bag.add(feature, example=example)
        for feature in _decompression_output_address_features(event):
            bag.add(feature, example=example)
        for feature in _decompression_source_load_entry_features(event):
            bag.add(feature, example=example)
        for feature in _decompression_pattern_features(event):
            bag.add(feature, example=example)


def _add_listing_features(listing: dict[str, Any], bag: FeatureBag) -> None:
    direct_control_stub_rows = _listing_direct_control_stub_table_row_features(listing)
    for row_index, row in enumerate(_dict_items(listing.get("rows"))):
        text = _string_value(row.get("text")) or ""
        opcode_or_directive = (_string_value(row.get("opcode_or_directive")) or "").upper()
        is_equate = bool(re.search(r"(^|\s)EQU(\s|$)", text))
        section_index = _int_value(row.get("section_index"), -1)
        offset = row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr")
        example = _offset_example(section_index, offset, text.strip()[:160])
        example["row_index"] = row_index
        if _listing_row_is_kind(row, LISTING_ROW_KIND_DIRECTIVE) and opcode_or_directive == "ORG":
            org_address = _org_directive_address(row, text)
            org_example = dict(example)
            if org_address is not None:
                org_example["runtime_address"] = org_address
            bag.add("materialized-org-range", example=org_example)
            bag.add("runtime:materialized_org_range", example=org_example)
            if org_address is not None:
                bag.add(f"runtime:materialized_org_address:{org_address:08X}", example=org_example)
        stack_top_symbols = sorted(set(re.findall(r"\bstack_top_[0-9A-Fa-f]{8}\b", text)))
        for symbol in stack_top_symbols:
            stack_example = dict(example)
            stack_example["symbol"] = symbol
            bag.add("memory:absolute_stack_top", example=stack_example)
            bag.add(f"memory:absolute_stack_top:{_safe_part(symbol)}", example=stack_example)
        _add_runtime_table_base_addend_features(bag, text, example)
        for feature in sorted(direct_control_stub_rows.get(row_index, ())):
            bag.add(feature, example=example)
        for feature in _listing_code_start_reason_features(row):
            bag.add(feature, example=example)
        if _listing_row_label_symbol(row):
            bag.add("label:any", example=example)
            bag.add("label:definition", example=example)
        data_class_flags = _listing_row_data_class_flags(row)
        data_class = _data_role_name(data_class_flags)
        copper_row = _data_role_has(data_class_flags, DATA_ROLE_COPPER_LIST)
        hardware_symbol_refs: list[tuple[str, str]] = []
        row_hardware_group_features: set[str] = set()
        if data_class:
            bag.add(f"data:{_safe_part(data_class)}", example=example)
            for feature in _listing_table_shape_features(text, data_class_flags):
                bag.add(feature, example=example)
            if _data_role_has(data_class_flags, DATA_ROLE_COPPER_LIST):
                bag.add("hardware:custom", example=example)
                row_hardware_group_features.update(amiga_hardware_usage.group_features("_custom", "copper", copper_row=True))
        if not is_equate:
            for base in amiga_hardware_usage.HARDWARE_BASES:
                if base in text:
                    bag.add(f"hardware:{base.removeprefix('_')}", example=example)
            hardware_symbol_refs = amiga_hardware_usage.symbol_refs_from_listing_text(text, copper_row=copper_row)
            for base, symbol in hardware_symbol_refs:
                bag.add(f"hardware_register:{_safe_part(symbol)}", example=example)
                row_hardware_group_features.update(amiga_hardware_usage.group_features(base, symbol, copper_row=copper_row))
        for feature in sorted(row_hardware_group_features):
            bag.add(feature, example=example)
        for feature in amiga_hardware_usage.display_features_from_symbol_refs(text, hardware_symbol_refs, copper_row=copper_row):
            bag.add(feature, example=example)
        comment_text = _string_value(row.get("comment_text")) or ""
        if "bitmap memory plane" in comment_text:
            bag.add("display:bitmap_memory_use", example=example)
        for operand in _dict_items(row.get("operand_parts")):
            segment_addr = _int_value(operand.get("segment_addr"))
            if segment_addr is not None:
                bag.add("xref:segment_ref", example=example)
                ref_feature = "xref:data_ref" if _listing_row_is_kind(row, LISTING_ROW_KIND_DATA) else "xref:code_ref"
                bag.add(ref_feature, example=example)
            symbol = _operand_symbol(operand)
            if symbol:
                bag.add("label:reference", example=example)
            metadata = operand.get("metadata")
            if isinstance(metadata, dict):
                value_domain = _string_value(metadata.get("value_domain"))
                if value_domain:
                    bag.add(f"value_domain:{_safe_part(value_domain)}", example=example)
                semantic_kind = _string_value(metadata.get("semantic_kind"))
                if semantic_kind:
                    bag.add(f"semantic:{_safe_part(semantic_kind)}", example=example)
                type_name = _string_value(metadata.get("type_name"))
                if type_name:
                    bag.add(f"type:{_safe_part(type_name)}", example=example)
        for app_ref in _dict_items(row.get("app_slot_refs")):
            access = _string_value(app_ref.get("access")) or "unknown"
            bag.add("app_slot:any", example=example)
            bag.add(f"app_slot:{_safe_part(access)}", example=example)
        for runtime_ref in _dict_items(row.get("runtime_address_refs")):
            runtime_class_flags = _int_value(runtime_ref.get("data_class_flags"), 0) or 0
            runtime_class = _data_role_name(runtime_class_flags)
            runtime_address = _int_value(runtime_ref.get("runtime_address"))
            sink_address = _int_value(runtime_ref.get("sink_address"))
            runtime_example = dict(example)
            if runtime_address is not None:
                runtime_example["runtime_address"] = runtime_address
            if sink_address is not None:
                runtime_example["sink_address"] = sink_address
            if runtime_class:
                bag.add(f"data:{_safe_part(runtime_class)}", example=runtime_example)
                bag.add("runtime:external_data_ref", example=runtime_example)
                if _data_role_has(runtime_class_flags, DATA_ROLE_BITMAP):
                    bag.add("display:bitmap_memory", example=runtime_example)
        for access in _dict_items(row.get("typed_accesses")):
            _add_platform_typed_access_features(bag, access, example=example)
        for access in _dict_items(row.get("unresolved_typed_accesses")):
            _add_platform_unresolved_typed_access_features(bag, access, example=example)


def _runtime_table_base_addend_matches(text: str) -> list[tuple[str, int]]:
    matches = set(re.findall(r"\blea\.l\s+(abs_[0-9]+_[0-9A-Fa-f]{8})-([0-9]+)\.l,a[0-7]\b", text))
    return sorted((symbol, -int(addend)) for symbol, addend in matches)


def _add_runtime_table_base_addend_features(bag: FeatureBag, text: str, example: dict[str, object]) -> None:
    for symbol, addend in _runtime_table_base_addend_matches(text):
        table_example = dict(example)
        table_example["symbol"] = symbol
        table_example["addend"] = addend
        bag.add("analysis:runtime_table_base_addend", example=table_example)
        bag.add(f"analysis:runtime_table_base_addend:{_safe_part(symbol)}", example=table_example)


def _org_directive_address(row: dict[str, Any], text: str) -> int | None:
    operand = _string_value(row.get("operand_text"))
    if operand is None:
        match = re.search(r"\bORG\s+(\$[0-9A-Fa-f]+|0x[0-9A-Fa-f]+|[0-9]+)\b", text)
        operand = match.group(1) if match else None
    if operand is None:
        return None
    operand = operand.strip()
    try:
        if operand.startswith("$"):
            return int(operand[1:], 16)
        if operand.lower().startswith("0x"):
            return int(operand, 16)
        return int(operand, 10)
    except ValueError:
        return None


_TABLE_LABEL_RE = re.compile(r"\b(?:abs|loc)_[0-9]+_[0-9A-Fa-f]{8}\b")
_TABLE_REL_LABEL_RE = re.compile(
    r"\b(?:abs|loc)_[0-9]+_[0-9A-Fa-f]{8}-(?:abs|loc)_[0-9]+_[0-9A-Fa-f]{8}\b"
)


def _listing_row_data_class(row: dict[str, object]) -> str | None:
    if not _listing_row_is_kind(row, LISTING_ROW_KIND_DATA):
        return None
    return _data_role_name(_listing_row_data_class_flags(row))


def _listing_row_data_class_flags(row: dict[str, object]) -> int:
    if not _listing_row_is_kind(row, LISTING_ROW_KIND_DATA):
        return 0
    return _int_value(row.get("data_class_flags"), 0) or 0


def _listing_row_kind_id(row: dict[str, object]) -> int:
    return _int_value(row.get("kind_id"), LISTING_ROW_KIND_UNKNOWN) or LISTING_ROW_KIND_UNKNOWN


def _listing_row_is_kind(row: dict[str, object], kind_id: int) -> bool:
    return _listing_row_kind_id(row) == kind_id


def _data_role_name(flags: int) -> str | None:
    for role_flags, name in DATA_ROLE_NAMES:
        if flags & role_flags == role_flags:
            return name
    return None


def _data_role_has(flags: int, role_flag: int) -> bool:
    return (flags & role_flag) != 0


def _conflict_state_id(record: dict[str, Any]) -> int | None:
    return _int_value(record.get("conflict_state_id"))


def _conflict_state_name(record: dict[str, Any]) -> str | None:
    state_id = _conflict_state_id(record)
    if state_id is None:
        return None
    return CONFLICT_STATE_NAMES.get(state_id, "unknown")


def _absolute_memory_owner_kind_id(record: dict[str, Any]) -> int | None:
    return _int_value(record.get("owner_kind_id"))


def _absolute_memory_owner_kind_name(owner_id: int) -> str:
    return ABSOLUTE_MEMORY_OWNER_NAMES.get(owner_id, "unknown")


def _memory_layout_record_kind_id(record: dict[str, Any]) -> int | None:
    return _int_value(record.get("record_kind_id"))


def _memory_layout_record_kind_name(record: dict[str, Any]) -> str:
    record_kind_id = _memory_layout_record_kind_id(record)
    if record_kind_id is None:
        return "unknown"
    return MEMORY_LAYOUT_RECORD_KIND_NAMES.get(record_kind_id, "unknown")


def _memory_layout_memory_kind_name(record: dict[str, Any]) -> str:
    record_kind_id = _memory_layout_record_kind_id(record)
    if record_kind_id == 1:
        return "base_layout"
    if record_kind_id == 2:
        return "base_layout_alias" if _bool_value(record.get("alias")) else "base_layout_field"
    if record_kind_id == 3:
        effect_kind = _int_value(record.get("effect_kind"))
        return PLATFORM_STORAGE_EFFECT_MEMORY_KIND_NAMES.get(effect_kind, "unknown")
    if record_kind_id == 4:
        return "platform_struct_field"
    if record_kind_id == 5:
        return "platform_struct_unresolved"
    if record_kind_id == 6:
        return "runtime_code" if _bool_value(record.get("materialized")) else "runtime_view_candidate"
    if record_kind_id == 7:
        data_class = _data_role_name(_int_value(record.get("data_class_flags"), 0) or 0)
        return data_class or "runtime_address"
    if record_kind_id == 8:
        owner_kind_id = _absolute_memory_owner_kind_id(record)
        return _absolute_memory_owner_kind_name(owner_kind_id) if owner_kind_id is not None else "unknown"
    return "unknown"


def _add_memory_layout_view_features(bag: FeatureBag, records: list[dict[str, Any]]) -> None:
    if not records:
        return
    range_space_counts: dict[int, int] = {}
    conflict_state_counts: dict[int, int] = {}
    absolute_owner_counts: dict[int, int] = {}
    for record in records:
        range_space_kind = _int_value(record.get("range_space_kind"))
        if range_space_kind is not None:
            range_space_counts[range_space_kind] = range_space_counts.get(range_space_kind, 0) + 1
        conflict_state_id = _conflict_state_id(record)
        if conflict_state_id is not None and conflict_state_id != CONFLICT_STATE_CLEAN:
            conflict_state_counts[conflict_state_id] = conflict_state_counts.get(conflict_state_id, 0) + 1
        owner_kind_id = _absolute_memory_owner_kind_id(record)
        if owner_kind_id is not None:
            absolute_owner_counts[owner_kind_id] = absolute_owner_counts.get(owner_kind_id, 0) + 1
    summary: dict[str, object] = {"record_count": len(records)}
    if range_space_counts:
        summary["range_spaces"] = {str(key): range_space_counts[key] for key in sorted(range_space_counts)}
    if conflict_state_counts:
        summary["conflict_count"] = sum(conflict_state_counts.values())
    if absolute_owner_counts:
        summary["absolute_ref_count"] = sum(absolute_owner_counts.values())
    bag.add("memory-layout-view:any", example=summary)
    for range_space_kind, count in sorted(range_space_counts.items()):
        bag.add(
            f"memory-layout-view:range_space:{range_space_kind}",
            example={"range_space_kind": range_space_kind, "record_count": count},
        )
    if conflict_state_counts:
        bag.add("memory-layout-view:has_conflict", example=summary)
        for conflict_state_id, count in sorted(conflict_state_counts.items()):
            state_name = CONFLICT_STATE_NAMES.get(conflict_state_id, "unknown")
            bag.add(
                f"memory-layout-view:conflict_state:{_safe_part(state_name)}",
                example={"conflict_state_id": conflict_state_id, "conflict_count": count},
            )
    if absolute_owner_counts:
        bag.add("memory-layout-view:absolute_refs", example=summary)
        for owner_kind_id, count in sorted(absolute_owner_counts.items()):
            owner_name = _absolute_memory_owner_kind_name(owner_kind_id)
            bag.add(
                f"memory-layout-view:absolute_owner:{_safe_part(owner_name)}",
                example={"owner_kind_id": owner_kind_id, "absolute_ref_count": count},
            )


def _listing_table_shape_features(text: str, data_class_flags: int) -> list[str]:
    lookup_table = _data_role_has(data_class_flags, DATA_ROLE_LOOKUP_TABLE)
    pointer_table = _data_role_has(data_class_flags, DATA_ROLE_POINTER_TABLE)
    if not lookup_table and not pointer_table:
        return []
    stripped = text.strip().lower()
    features: list[str] = []
    if lookup_table and stripped.startswith("dc.w") and _TABLE_REL_LABEL_RE.search(text):
        features.append("analysis:lookup_table:word_relative_labels")
    if lookup_table and stripped.startswith("dc.l") and _TABLE_LABEL_RE.search(text):
        features.append("analysis:lookup_table:long_label_entries")
    if pointer_table and stripped.startswith("dc.l") and _TABLE_LABEL_RE.search(text):
        features.append("analysis:pointer_table:long_label_entries")
    return features


def _listing_row_is_direct_control_stub(row: dict[str, object]) -> bool:
    return bool(_listing_row_direct_control_stub_features(row))


def _listing_row_direct_control_stub_features(row: dict[str, object]) -> tuple[str, ...]:
    if not _listing_row_is_kind(row, LISTING_ROW_KIND_INSTRUCTION):
        return ()
    opcode = (_string_value(row.get("opcode_or_directive")) or "").strip().lower()
    mnemonic = opcode.split(".", 1)[0]
    accesses = row.get("operand_accesses")
    if not isinstance(accesses, list) or "branch_target" not in accesses:
        return ()
    symbols = [_operand_symbol(operand) for operand in _dict_items(row.get("operand_parts"))]
    symbols = [symbol for symbol in symbols if symbol]
    if not symbols:
        return ()
    refs = row.get("code_start_refs")
    if not isinstance(refs, list):
        return ()
    if not any(isinstance(ref, dict) and ref.get("reason") == CODE_START_REASON_CONTROL_TARGET for ref in refs):
        return ()
    if mnemonic == "bra":
        return ("analysis:direct_control_stub_table",)
    if mnemonic == "jmp":
        section = _int_value(row.get("section_index"))
        for symbol in symbols:
            match = re.match(r"^loc_(\d+)_", symbol)
            if match is not None and section is not None and int(match.group(1)) != section:
                return ("analysis:direct_control_stub_table", "analysis:relocated_absolute_jmp_stub_table")
    return ()


def _listing_code_start_reason_features(row: dict[str, object]) -> tuple[str, ...]:
    refs = row.get("code_start_refs")
    features: list[str] = []
    if not isinstance(refs, list):
        return ()
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        reason = _int_value(ref.get("reason"), 0) or 0
        if reason == CODE_START_REASON_PLATFORM_LOADSEG_ENTRY:
            features.append("analysis:platform_loadseg_entry")
            features.append("target-pattern:platform_loadseg_entry")
    return tuple(dict.fromkeys(features))


def _listing_direct_control_stub_table_row_features(listing: dict[str, Any]) -> dict[int, set[str]]:
    rows = _dict_items(listing.get("rows"))
    result: dict[int, set[str]] = {}
    run: list[tuple[int, tuple[str, ...]]] = []
    previous_section: int | None = None
    previous_end: int | None = None
    previous_width: int | None = None
    for row_index, row in enumerate(rows):
        section = _int_value(row.get("section_index"))
        start = _int_value(row.get("start_offset"))
        end = _int_value(row.get("end_offset"))
        width = end - start if start is not None and end is not None and end >= start else None
        is_zero_width_label = _listing_row_is_kind(row, LISTING_ROW_KIND_LABEL) and width == 0
        features = _listing_row_direct_control_stub_features(row)
        if not features and is_zero_width_label:
            continue
        if (features and section is not None and start is not None and end is not None and
            width is not None and width > 0 and previous_section == section and previous_end == start and
            previous_width == width and run and run[-1][1] == features):
            run.append((row_index, features))
        else:
            if len(run) >= 2:
                for run_index, run_features in run:
                    result.setdefault(run_index, set()).update(run_features)
            run = [(row_index, features)] if features and width is not None and width > 0 else []
        previous_section = section
        previous_end = end
        previous_width = width
    if len(run) >= 2:
        for run_index, run_features in run:
            result.setdefault(run_index, set()).update(run_features)
    return result


def _listing_direct_control_stub_table_row_indices(listing: dict[str, Any]) -> set[int]:
    return set(_listing_direct_control_stub_table_row_features(listing))


def _disk_usage_xrefs(row: dict[str, object], entry: dict[str, Any]) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    xrefs.append(_xref(row, "format:disk_image", "format", text="disk image"))
    xrefs.append(_xref(row, f"disk_platform:{_safe_part(entry.get('platform'))}", "format", text=str(entry.get("platform"))))
    expect = entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    if isinstance(inspect, dict):
        entries = inspect.get("entries")
        if isinstance(entries, list):
            for item in entries:
                if not isinstance(item, dict):
                    continue
                path = _string_value(item.get("path")) or ""
                xrefs.append(_xref(row, "disk:entry", "disk_entry", text=path, symbol=path))
                if item.get("is_executable_candidate") == 1:
                    xrefs.append(_xref(row, "disk:executable_candidate", "disk_entry", text=path, symbol=path))
                kind = item.get("kind")
                if isinstance(kind, int):
                    xrefs.append(_xref(row, f"disk:entry_kind:{kind}", "disk_entry", text=path, value=kind))
        trackloader = inspect.get("trackloader_analysis")
        if isinstance(trackloader, dict):
            xrefs.append(_xref(row, "disk:trackloader", "disk_trackloader", text="trackloader analysis"))
            tracks = trackloader.get("candidate_code_tracks")
            if isinstance(tracks, list):
                for track in tracks:
                    if isinstance(track, int):
                        xrefs.append(_xref(row, "disk:candidate_code_track", "disk_trackloader", value=track, text=f"track {track}"))
        if inspect.get("bootblock") or inspect.get("bootblock_analysis") or inspect.get("boot_ascii_strings"):
            xrefs.append(_xref(row, "disk:bootblock", "disk_bootblock", text="bootblock"))
    if _status(entry) != "ok":
        xrefs.append(_xref(row, "diagnostic:manifest_error", "diagnostic", text="manifest error"))
    return _dedupe_xrefs(xrefs)


def _file_usage_xrefs(
    row: dict[str, object],
    entry: dict[str, Any],
    combined: dict[str, Any] | None,
    analysis_error: str | None,
    *,
    listing_feature_bag: FeatureBag | None = None,
) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    xrefs.extend(_file_manifest_xrefs(row, entry))
    if analysis_error is not None:
        xrefs.append(_xref(row, "diagnostic:analysis_error", "diagnostic", text=analysis_error))
    if combined is not None:
        analysis = combined.get("analysis")
        listing = combined.get("listing")
        profile = combined.get("profile")
        if isinstance(profile, dict):
            generation = _string_value(profile.get("generation"))
            if generation:
                xrefs.append(_xref(row, f"analysis_generation:{_safe_part(generation)}", "analysis_profile", text=generation))
        row_locations = _listing_row_locations(listing if isinstance(listing, dict) else None)
        if isinstance(analysis, dict):
            xrefs.append(_xref(row, "analysis:facts_v2", "analysis_profile", text="facts_v2"))
            xrefs.extend(_analysis_xrefs(row, analysis, row_locations))
        if isinstance(listing, dict):
            xrefs.extend(_listing_xrefs(row, listing, feature_bag=listing_feature_bag))
        app_slot_analysis = combined.get("app_slot_analysis")
        if isinstance(app_slot_analysis, dict):
            xrefs.extend(_app_slot_layout_xrefs(row, app_slot_analysis))
    return _dedupe_xrefs(xrefs)


def _project_target_metadata_xrefs(row: dict[str, object], entry: dict[str, Any]) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    origin_kind_id = _int_value(entry.get("project_origin_kind_id"))
    origin_kind = PROJECT_ORIGIN_KIND_NAMES.get(origin_kind_id) if origin_kind_id is not None else None
    target_role_id = _int_value(entry.get("target_role_id"))
    target_role = PROJECT_TARGET_ROLE_NAMES.get(target_role_id) if target_role_id is not None else None
    payload_role_id = _int_value(entry.get("payload_role_id"))
    payload_role = DECOMPRESSION_PAYLOAD_ROLE_NAMES.get(payload_role_id) if payload_role_id is not None else None
    payload_role_confidence_id = _int_value(entry.get("payload_role_confidence_id"))
    payload_role_confidence = (
        DECOMPRESSION_PAYLOAD_ROLE_CONFIDENCE_NAMES.get(payload_role_confidence_id)
        if payload_role_confidence_id is not None else None
    )
    parent_remains_active_id = _int_value(entry.get("parent_remains_active_id"))
    parent_remains_active = (
        DECOMPRESSION_PARENT_REMAINS_ACTIVE_NAMES.get(parent_remains_active_id)
        if parent_remains_active_id is not None else None
    )
    target_type = _string_value(entry.get("target_type"))
    reproduction = entry.get("reproduction")
    reproduction_status = _string_value(reproduction.get("status")) if isinstance(reproduction, dict) else None
    for value, prefix, kind in (
        (origin_kind, "project_origin", "project_target_metadata"),
        (target_role, "project_target_role", "project_target_metadata"),
        (target_type, "project_target_type", "project_target_metadata"),
    ):
        if value:
            xrefs.append(_xref(row, f"{prefix}:{_safe_part(value)}", kind, symbol=value, text=value))
    if reproduction_status:
        xrefs.append(
            _xref(
                row,
                f"reproduction:status:{_safe_part(reproduction_status)}",
                "project_reproduction",
                symbol=reproduction_status,
                text=reproduction_status,
            )
        )
    if isinstance(reproduction, dict) and reproduction.get("exact") is True:
        xrefs.append(_xref(row, "reproduction:exact", "project_reproduction", text=reproduction_status or "exact"))
    if origin_kind_id == PROJECT_ORIGIN_KIND_DERIVED_DECOMPRESSED_PAYLOAD or target_role_id == PROJECT_TARGET_ROLE_DECOMPRESSED_PAYLOAD:
        codec = _project_decompression_codec(entry)
        example = _project_decompression_example(entry)
        offset = _int_value(example.get("offset"))
        text = _string_value(example.get("text")) or "decompressed payload"
        for feature in ("derived-decompressed-target", "derived_target:decompressed_payload", "decompression:child"):
            xrefs.append(_xref(row, feature, "derived_target", offset=offset, symbol=codec, text=text))
        if reproduction_status:
            xrefs.append(
                _xref(
                    row,
                    f"decompression:child_reproduction_status:{_safe_part(reproduction_status)}",
                    "derived_target",
                    offset=offset,
                    symbol=reproduction_status,
                    text=text,
                )
            )
        if isinstance(reproduction, dict) and reproduction.get("exact") is True:
            xrefs.append(_xref(row, "decompression:child_reproduction_exact", "derived_target", offset=offset, symbol=codec, text=text))
        if _int_value(example.get("load_address")) is not None:
            xrefs.append(_xref(row, "absolute-depack-dest", "derived_target", offset=offset, symbol=codec, text=text))
        if _int_value(example.get("entrypoint")) is not None:
            xrefs.append(_xref(row, "decompressed-entrypoint", "derived_target", offset=offset, symbol=codec, text=text))
        if codec:
            xrefs.append(
                _xref(
                    row,
                    f"decompression:codec:{_safe_part(codec)}",
                    "derived_target",
                    offset=offset,
                    symbol=codec,
                    text=text,
                )
            )
        packed_size = _int_value(example.get("packed_size"))
        if offset is not None:
            xrefs.append(_xref(row, "decompression:source_offset", "derived_target", offset=offset, symbol=codec, text=text))
            xrefs.append(
                _xref(
                    row,
                    f"decompression:source_offset:0:{offset:08X}",
                    "derived_target",
                    offset=offset,
                    symbol=codec,
                    text=text,
                )
            )
        if offset is not None and packed_size is not None:
            end_offset = offset + packed_size
            for feature in (
                "decompression:source_range",
                f"decompression:source_range:0:{offset:08X}-{end_offset:08X}",
                "decompression:packed_size",
            ):
                xrefs.append(_xref(row, feature, "derived_target", offset=offset, symbol=codec, value=packed_size, text=text))
        source_load_entry = {
            "source_section": 0,
            "source_section_offset": offset,
            "source_section_end_offset": _int_value(example.get("source_section_end_offset")),
            "load_address": _int_value(example.get("load_address")),
            "entrypoint": _int_value(example.get("entrypoint")),
        }
        for feature in _decompression_source_load_entry_features(source_load_entry):
            xrefs.append(_xref(row, feature, "derived_target", offset=offset, symbol=codec, text=text))
        for value, feature_prefix in (
            (payload_role, "decompression:payload_role"),
            (payload_role_confidence, "decompression:payload_role_confidence"),
            (parent_remains_active, "decompression:parent_remains_active"),
        ):
            if value:
                xrefs.append(
                    _xref(
                        row,
                        f"{feature_prefix}:{_safe_part(value)}",
                        "derived_target",
                        offset=offset,
                        symbol=value,
                        text=text,
                    )
                )
    return xrefs


def _project_target_xrefs(
    row: dict[str, object],
    entry: dict[str, Any],
    combined: dict[str, Any] | None,
    analysis_error: str | None,
    *,
    listing_feature_bag: FeatureBag | None = None,
) -> list[dict[str, object]]:
    xrefs = [
        _xref(row, "project_target:any", "project_target", text=str(row.get("source_id") or "")),
        *_project_target_metadata_xrefs(row, entry),
        *_file_usage_xrefs(row, entry, combined, analysis_error, listing_feature_bag=listing_feature_bag),
    ]
    reproduction = entry.get("reproduction")
    analysis = combined.get("analysis") if isinstance(combined, dict) else None
    if isinstance(reproduction, dict) and isinstance(analysis, dict) and _analysis_has_decompression_relationship(analysis):
        status = _string_value(reproduction.get("status"))
        if status:
            xrefs.append(
                _xref(
                    row,
                    f"decompression:parent_reproduction_status:{_safe_part(status)}",
                    "decompression_parent_reproduction",
                    symbol=status,
                    text=status,
                )
            )
        if reproduction.get("exact") is True:
            xrefs.append(
                _xref(
                    row,
                    "decompression:parent_reproduction_exact",
                    "decompression_parent_reproduction",
                    symbol=status,
                    text=status or "exact",
                )
            )
    return _dedupe_xrefs(xrefs)


def _snippet_rows_for_xrefs(
    target_row: dict[str, object],
    combined: dict[str, Any] | None,
    xrefs: list[dict[str, object]],
    *,
    before: int = 20,
    after: int = 20,
) -> list[dict[str, object]]:
    if combined is None:
        return []
    listing = combined.get("listing")
    rows = listing.get("rows") if isinstance(listing, dict) else None
    if not isinstance(rows, list):
        return []
    wanted: set[int] = set()
    for xref in xrefs:
        row_index = xref.get("row_index")
        if not isinstance(row_index, int):
            continue
        for index in range(max(0, row_index - before), min(len(rows), row_index + after + 1)):
            wanted.add(index)
    result: list[dict[str, object]] = []
    target_id = str(target_row.get("id"))
    for row_index in sorted(wanted):
        row = rows[row_index]
        if not isinstance(row, dict):
            continue
        result.append(
            {
                "schema_version": 1,
                "id": _stable_snippet_row_id(target_id, row_index, row),
                "target_id": target_id,
                "row_index": row_index,
                "row": _compact_listing_row(row),
            }
        )
    return result


def _compact_listing_row(row: dict[str, Any]) -> dict[str, object]:
    keys = (
        "row_id",
        "kind_id",
        "kind",
        "text",
        "stable_key",
        "section_index",
        "start_offset",
        "end_offset",
        "storage_address",
        "runtime_address",
        "runtime_view_id",
        "addr",
        "bytes",
        "label",
        "opcode_or_directive",
        "operand_parts",
        "operand_text",
        "comment_text",
        "data_class",
        "structured_data",
        "app_slot_refs",
        "typed_accesses",
        "unresolved_typed_accesses",
    )
    return {key: row[key] for key in keys if key in row}


def _stable_snippet_row_id(target_id: str, row_index: int, row: dict[str, Any]) -> str:
    raw = json.dumps(
        {
            "target_id": target_id,
            "row_index": row_index,
            "stable_key": row.get("stable_key"),
            "text": row.get("text"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _file_manifest_xrefs(row: dict[str, object], entry: dict[str, Any]) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    platform = str(entry.get("platform", "unknown"))
    xrefs.append(_xref(row, f"file_platform:{_safe_part(platform)}", "format", text=platform))
    expect = entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    if _status(entry) != "ok":
        message = expect.get("error") if isinstance(expect, dict) else None
        xrefs.append(_xref(row, "diagnostic:manifest_error", "diagnostic", text=str(message or "manifest error")))
        return xrefs
    if not isinstance(inspect, dict):
        return xrefs
    for key, prefix in (
        ("file_kind", "format"),
        ("platform", "inspect_platform"),
    ):
        value = _string_value(inspect.get(key))
        if value:
            xrefs.append(_xref(row, f"{prefix}:{_safe_part(value)}", "format", text=value))
    form_type = _string_value(inspect.get("form_type"))
    if form_type:
        xrefs.append(_xref(row, f"format:iff:{_safe_part(form_type)}", "format", text=form_type))
    for name, feature in (
        ("section_count", "section"),
        ("fixup_count", "relocation:fixup"),
        ("global_symbol_count", "symbol:global"),
        ("local_symbol_count", "symbol:local"),
        ("external_symbol_count", "symbol:external"),
    ):
        value = inspect.get(name)
        if isinstance(value, int) and value > 0:
            xrefs.append(_xref(row, feature, "format_count", value=value, text=name))
    resident = inspect.get("resident")
    if isinstance(resident, dict):
        xrefs.append(_xref(row, "amiga:resident", "format", text="resident"))
        auto_init = resident.get("auto_init")
        if auto_init is True:
            xrefs.append(_xref(row, "amiga:resident:autoinit", "format", text="resident.autoinit"))
        elif auto_init is False:
            xrefs.append(_xref(row, "amiga:resident:non_autoinit", "format", text="resident.non_autoinit"))
        node_type_name = _string_value(resident.get("node_type_name"))
        if node_type_name:
            xrefs.append(_xref(row, f"amiga:resident_node:{_safe_part(node_type_name)}", "format", text=node_type_name))
    elif resident is not None:
        xrefs.append(_xref(row, "amiga:resident", "format", text="resident"))
    if inspect.get("library") is not None:
        xrefs.append(_xref(row, "amiga:library", "format", text="library"))
    return xrefs


def _listing_row_locations(listing: dict[str, Any] | None) -> dict[tuple[int, int], tuple[int, str | None, str | None]]:
    if listing is None:
        return {}
    rows = listing.get("rows")
    if not isinstance(rows, list):
        return {}
    ranked: dict[tuple[int, int], tuple[int, int, str | None, str | None]] = {}
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        section_index = _int_value(row.get("section_index"))
        if section_index is None:
            continue
        rank = _listing_row_location_rank(row)
        stable_key = _string_value(row.get("stable_key"))
        text = (_string_value(row.get("text")) or "").strip()
        for key in ("start_offset", "addr", "storage_address"):
            offset = _int_value(row.get(key))
            if offset is None:
                continue
            location_key = (section_index, offset)
            existing = ranked.get(location_key)
            if existing is None or rank < existing[0]:
                ranked[location_key] = (rank, row_index, stable_key, text or None)
    return {key: (value[1], value[2], value[3]) for key, value in ranked.items()}


def _listing_row_location_rank(row: dict[str, Any]) -> int:
    kind = _listing_row_kind_id(row)
    if kind == LISTING_ROW_KIND_INSTRUCTION:
        return 0
    if kind == LISTING_ROW_KIND_DATA:
        return 1
    if kind == LISTING_ROW_KIND_DIRECTIVE:
        return 2
    if kind == LISTING_ROW_KIND_LABEL:
        return 3
    return 4


def _row_location(
    row_locations: dict[tuple[int, int], tuple[int, str | None, str | None]],
    section_index: int | None,
    offset: int | None,
) -> tuple[int | None, str | None, str | None]:
    if section_index is None or offset is None:
        return None, None, None
    return row_locations.get((section_index, offset), (None, None, None))


def _platform_typed_access_xrefs(
    target_row: dict[str, object],
    access: dict[str, Any],
    *,
    section_index: int | None,
    offset: int | None,
    row_index: int | None,
    stable_key: str | None,
    row_text: str | None,
) -> list[dict[str, object]]:
    root_struct, owner_struct, field_name, field_expr = _platform_typed_access_parts(access)
    owner_for_feature = owner_struct or root_struct
    text = row_text or field_expr or field_name or owner_for_feature or "typed platform access"
    field_offset = _int_value(access.get("field_offset"))
    type_provenance_kind_id, type_provenance_kind, type_provenance_section, type_provenance_offset = (
        _typed_access_provenance(access)
    )
    xrefs = [
        _xref(
            target_row,
            "platform_typed_access:any",
            "platform_typed_access",
            section=section_index,
            offset=offset,
            row_index=row_index,
            stable_key=stable_key,
            symbol=field_name,
            value=field_offset,
            text=text,
        )
    ]
    if root_struct:
        xrefs.append(
            _xref(
                target_row,
                f"platform_typed_access_struct:{_safe_part(root_struct)}",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=root_struct,
                value=field_offset,
                text=text,
            )
        )
        xrefs.append(
            _xref(
                target_row,
                f"struct:{_safe_part(root_struct)}",
                "struct",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=root_struct,
                value=field_offset,
                text=text,
            )
        )
    if owner_struct:
        xrefs.append(
            _xref(
                target_row,
                f"platform_typed_access_owner:{_safe_part(owner_struct)}",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=owner_struct,
                value=field_offset,
                text=text,
            )
        )
    if field_name:
        xrefs.append(
            _xref(
                target_row,
                f"platform_field:{_safe_part(field_name)}",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=field_name,
                value=field_offset,
                text=text,
            )
        )
        if owner_for_feature:
            xrefs.append(
                _xref(
                    target_row,
                    f"platform_struct_field:{_safe_part(owner_for_feature)}.{_safe_part(field_name)}",
                    "platform_typed_access",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=field_name,
                    value=field_offset,
                    text=text,
                )
            )
    if field_expr and owner_for_feature:
        xrefs.append(
            _xref(
                target_row,
                f"platform_field_expr:{_safe_part(owner_for_feature)}.{_safe_part(field_expr)}",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=field_name,
                value=field_offset,
                text=text,
            )
        )
    if access.get("inherited") is True or access.get("inherited") == 1:
        xrefs.append(
            _xref(
                target_row,
                "platform_typed_access:inherited",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=field_name,
                value=field_offset,
                text=text,
            )
        )
    if access.get("nested") is True or access.get("nested") == 1:
        xrefs.append(
            _xref(
                target_row,
                "platform_typed_access:nested",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=field_name,
                value=field_offset,
                text=text,
            )
        )
    if type_provenance_kind_id is not None:
        xrefs.append(
            _xref(
                target_row,
                f"platform_typed_access_provenance:{_safe_part(type_provenance_kind)}",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=field_name,
                value=field_offset,
                text=text,
                type_provenance_kind_id=type_provenance_kind_id,
                type_provenance_kind=type_provenance_kind,
                type_provenance_section=type_provenance_section,
                type_provenance_offset=type_provenance_offset,
            )
        )
    if type_provenance_kind_id is not None:
        for xref in xrefs:
            xref["type_provenance_kind_id"] = type_provenance_kind_id
            xref["type_provenance_kind"] = type_provenance_kind
            if type_provenance_section is not None:
                xref["type_provenance_section"] = type_provenance_section
            if type_provenance_offset is not None:
                xref["type_provenance_offset"] = type_provenance_offset
    return xrefs


def _platform_unresolved_typed_access_xrefs(
    target_row: dict[str, object],
    access: dict[str, Any],
    *,
    section_index: int | None,
    offset: int | None,
    row_index: int | None,
    stable_key: str | None,
    row_text: str | None,
) -> list[dict[str, object]]:
    root_struct = _string_value(access.get("root_struct_name"))
    displacement = _int_value(access.get("displacement"))
    struct_size = _int_value(access.get("struct_size"))
    classification_id = _unresolved_typed_access_classification_id(access)
    classification = _unresolved_typed_access_classification_name(access)
    container_candidate_count = _int_value(access.get("container_candidate_count"))
    container_struct_name = _string_value(access.get("container_struct_name"))
    container_field_expr = _string_value(access.get("container_field_expr"))
    refinement_applied = access.get("refinement_applied") is True or access.get("refinement_applied") == 1
    refined_struct_name = _string_value(access.get("refined_struct_name"))
    type_provenance_kind_id = _typed_access_provenance_id(access)
    type_provenance_kind = _typed_access_provenance_name(type_provenance_kind_id)
    type_provenance_section = _int_value(access.get("type_provenance_section"))
    type_provenance_offset = _int_value(access.get("type_provenance_offset"))
    text = row_text or root_struct or "unresolved typed platform access"
    xrefs = [
        _xref(
            target_row,
            "typed_base_unresolved_field",
            "platform_unresolved_typed_access",
            section=section_index,
            offset=offset,
            row_index=row_index,
            stable_key=stable_key,
            symbol=root_struct,
            value=displacement,
            text=text,
            struct_size=struct_size,
            classification_id=classification_id,
            classification=classification,
            container_candidate_count=container_candidate_count,
            container_struct_name=container_struct_name,
            container_field_expr=container_field_expr,
            refinement_applied=refinement_applied,
            refined_struct_name=refined_struct_name,
            type_provenance_kind_id=type_provenance_kind_id,
            type_provenance_kind=type_provenance_kind,
            type_provenance_section=type_provenance_section,
            type_provenance_offset=type_provenance_offset,
        ),
        _xref(
            target_row,
            "platform_unresolved_typed_access:any",
            "platform_unresolved_typed_access",
            section=section_index,
            offset=offset,
            row_index=row_index,
            stable_key=stable_key,
            symbol=root_struct,
            value=displacement,
            text=text,
            struct_size=struct_size,
            classification_id=classification_id,
            classification=classification,
            container_candidate_count=container_candidate_count,
            container_struct_name=container_struct_name,
            container_field_expr=container_field_expr,
            refinement_applied=refinement_applied,
            refined_struct_name=refined_struct_name,
            type_provenance_kind_id=type_provenance_kind_id,
            type_provenance_kind=type_provenance_kind,
            type_provenance_section=type_provenance_section,
            type_provenance_offset=type_provenance_offset,
        ),
    ]
    if refinement_applied:
        xrefs.append(
            _xref(
                target_row,
                "platform_type_refinement:applied",
                "platform_type_refinement",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=refined_struct_name or container_struct_name or root_struct,
                value=displacement,
                text=text,
                struct_size=struct_size,
                classification_id=classification_id,
                classification=classification,
                container_candidate_count=container_candidate_count,
                container_struct_name=container_struct_name,
                container_field_expr=container_field_expr,
                refinement_applied=True,
                refined_struct_name=refined_struct_name,
                type_provenance_kind_id=type_provenance_kind_id,
                type_provenance_kind=type_provenance_kind,
                type_provenance_section=type_provenance_section,
                type_provenance_offset=type_provenance_offset,
            )
        )
        if root_struct:
            xrefs.append(
                _xref(
                    target_row,
                    f"platform_type_refinement_from:{_safe_part(root_struct)}",
                    "platform_type_refinement",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=root_struct,
                    value=displacement,
                    text=text,
                    refinement_applied=True,
                    refined_struct_name=refined_struct_name,
                    type_provenance_kind_id=type_provenance_kind_id,
                    type_provenance_kind=type_provenance_kind,
                    type_provenance_section=type_provenance_section,
                    type_provenance_offset=type_provenance_offset,
                )
            )
        if refined_struct_name:
            xrefs.append(
                _xref(
                    target_row,
                    f"platform_type_refinement_to:{_safe_part(refined_struct_name)}",
                    "platform_type_refinement",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=refined_struct_name,
                    value=displacement,
                    text=text,
                    refinement_applied=True,
                    refined_struct_name=refined_struct_name,
                    type_provenance_kind_id=type_provenance_kind_id,
                    type_provenance_kind=type_provenance_kind,
                    type_provenance_section=type_provenance_section,
                    type_provenance_offset=type_provenance_offset,
                )
            )
    if classification:
        xrefs.append(
            _xref(
                target_row,
                f"platform_unresolved_typed_access:{_safe_part(classification)}",
                "platform_unresolved_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=root_struct,
                value=displacement,
                text=text,
                struct_size=struct_size,
                classification_id=classification_id,
                classification=classification,
                container_candidate_count=container_candidate_count,
                container_struct_name=container_struct_name,
                container_field_expr=container_field_expr,
                type_provenance_kind_id=type_provenance_kind_id,
                type_provenance_kind=type_provenance_kind,
                type_provenance_section=type_provenance_section,
                type_provenance_offset=type_provenance_offset,
            )
        )
    if root_struct:
        xrefs.append(
            _xref(
                target_row,
                f"platform_unresolved_typed_access_struct:{_safe_part(root_struct)}",
                "platform_unresolved_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=root_struct,
                value=displacement,
                text=text,
                struct_size=struct_size,
                classification_id=classification_id,
                classification=classification,
                container_candidate_count=container_candidate_count,
                container_struct_name=container_struct_name,
                container_field_expr=container_field_expr,
                type_provenance_kind_id=type_provenance_kind_id,
                type_provenance_kind=type_provenance_kind,
                type_provenance_section=type_provenance_section,
                type_provenance_offset=type_provenance_offset,
            )
        )
        xrefs.append(
            _xref(
                target_row,
                f"struct:{_safe_part(root_struct)}",
                "struct",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=root_struct,
                value=displacement,
                text=text,
                struct_size=struct_size,
                classification_id=classification_id,
                classification=classification,
                container_candidate_count=container_candidate_count,
                container_struct_name=container_struct_name,
                container_field_expr=container_field_expr,
                type_provenance_kind_id=type_provenance_kind_id,
                type_provenance_kind=type_provenance_kind,
                type_provenance_section=type_provenance_section,
                type_provenance_offset=type_provenance_offset,
            )
        )
        if classification_id == UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION:
            xrefs.append(
                _xref(
                    target_row,
                    f"platform_prefix_extension_struct:{_safe_part(root_struct)}",
                    "platform_unresolved_typed_access",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=root_struct,
                    value=displacement,
                    text=text,
                    struct_size=struct_size,
                    classification_id=classification_id,
                    classification=classification,
                    container_candidate_count=container_candidate_count,
                    container_struct_name=container_struct_name,
                    container_field_expr=container_field_expr,
                )
            )
    if classification_id == UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION and container_struct_name:
        xrefs.append(
            _xref(
                target_row,
                f"platform_prefix_extension_candidate:{_safe_part(container_struct_name)}",
                "platform_unresolved_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=container_struct_name,
                value=displacement,
                text=text,
                struct_size=struct_size,
                classification_id=classification_id,
                classification=classification,
                container_candidate_count=container_candidate_count,
                container_struct_name=container_struct_name,
                container_field_expr=container_field_expr,
            )
        )
    return xrefs


def _decompression_analysis_xrefs(
    row: dict[str, object],
    analysis: dict[str, Any],
    row_locations: dict[tuple[int, int], tuple[int, str | None, str | None]],
) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    for payload in _dict_items(analysis.get("packed_payloads")):
        section_index = _int_value(payload.get("source_section"))
        if section_index is None:
            section_index = _int_value(payload.get("source_section_index"))
        offset = _int_value(payload.get("source_section_offset"))
        if offset is None:
            offset = _int_value(payload.get("source_offset"))
        row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
        codec_id = _string_value(payload.get("codec_id"))
        provider_id = _string_value(payload.get("provider_id"))
        packed_size = _int_value(payload.get("packed_size"))
        decompressed_size = _int_value(payload.get("decompressed_size"))
        text = row_text or codec_id or _string_value(payload.get("codec_name")) or "packed payload"
        features = ["compressed-payload"]
        if codec_id:
            features.append(f"compressed:{_safe_part(codec_id)}")
        if provider_id:
            features.append(f"decompression:provider:{_safe_part(provider_id)}")
        if decompressed_size is not None:
            features.append("decompression:has_output_size")
        if _string_value(payload.get("decompressed_sha256")):
            features.append("decompression:has_output_hash")
        if _string_value(payload.get("diagnostic")):
            features.append("decompression:diagnostic")
        features.extend(_decompression_source_range_features(payload))
        features.extend(_decompression_output_address_features(payload))
        features.extend(_decompression_source_load_entry_features(payload))
        if payload.get("found") is False or payload.get("found") == 0:
            features = ["unsupported-compressor"]
        for feature in features:
            xrefs.append(
                _xref(
                    row,
                    feature,
                    "packed_payload",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=codec_id,
                    access=provider_id,
                    value=decompressed_size if decompressed_size is not None else packed_size,
                    text=text,
                )
            )
    for suggestion in _dict_items(analysis.get("derived_target_suggestions")):
        section_index = _int_value(suggestion.get("source_section"))
        if section_index is None:
            section_index = _int_value(suggestion.get("source_section_index"))
        offset = _int_value(suggestion.get("source_section_offset"))
        if offset is None:
            offset = _int_value(suggestion.get("source_offset"))
        row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
        kind_id = _int_value(suggestion.get("kind_id"), 0) or 0
        kind = DERIVED_TARGET_SUGGESTION_KIND_NAMES.get(kind_id, "unknown")
        status_id = _int_value(suggestion.get("status_id"), 0) or 0
        status = DECOMPRESSION_STATUS_NAMES.get(status_id)
        text = row_text or kind
        features = [f"derived_target_suggestion:{_safe_part(kind)}"]
        if kind_id == DERIVED_TARGET_SUGGESTION_DECOMPRESSED_PAYLOAD:
            features.append("derived-decompressed-target")
        if status:
            features.append(f"derived_target_suggestion_status:{_safe_part(status)}")
        reason_id = _int_value(suggestion.get("reason_id"), 0) or 0
        reason = DECOMPRESSION_REASON_NAMES.get(reason_id)
        if reason:
            features.append(f"derived_target_suggestion_reason:{_safe_part(reason)}")
        features.extend(_decompression_unmaterialized_features(status_id, reason_id))
        features.extend(_decompression_source_range_features(suggestion))
        features.extend(_decompression_output_address_features(suggestion))
        features.extend(_decompression_source_load_entry_features(suggestion))
        runtime_copy_address = _int_value(suggestion.get("runtime_copy_address"))
        runtime_copy_size = _int_value(suggestion.get("runtime_copy_size"))
        packed_size = _int_value(suggestion.get("packed_size"))
        runtime_copy_kind = _int_value(suggestion.get("runtime_copy_kind"))
        if runtime_copy_address is not None:
            features.append("decompression:runtime_copy")
            if runtime_copy_kind is not None:
                features.append(f"decompression:runtime_copy_kind:{runtime_copy_kind}")
            if suggestion.get("runtime_copy_conflicting") is True:
                features.append("decompression:runtime_copy_conflicting")
            else:
                features.append("decompression:runtime_copy_non_conflicting")
            if runtime_copy_size is not None and packed_size is not None:
                if runtime_copy_size == packed_size:
                    features.append("decompression:runtime_copy_exact_size")
                elif runtime_copy_size < packed_size:
                    features.append("decompression:runtime_copy_short")
                else:
                    features.append("decompression:runtime_copy_oversize")
        features.extend(_decompression_pattern_features(suggestion))
        for feature in features:
            xrefs.append(
                _xref(
                    row,
                    feature,
                    "derived_target_suggestion",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=kind,
                    value=runtime_copy_address if feature.startswith("decompression:runtime_copy") else status_id,
                    text=text,
                )
            )
    for event in _dict_items(analysis.get("decompression_events")):
        section_index = _int_value(event.get("source_section"))
        offset = _int_value(event.get("source_section_offset"))
        if section_index is None:
            section_index = _int_value(event.get("decompressor_code_section"))
        if offset is None:
            offset = _int_value(event.get("decompressor_entry_offset"))
        row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
        event_kind_id = _int_value(event.get("event_kind_id"), 0) or 0
        event_kind = DECOMPRESSION_EVENT_KIND_NAMES.get(event_kind_id, "unknown")
        status_id = _int_value(event.get("status_id"), 0) or 0
        status = DECOMPRESSION_STATUS_NAMES.get(status_id)
        text = row_text or _string_value(event.get("event_id")) or event_kind
        features = [f"decompression:event:{_safe_part(event_kind)}"]
        if _string_value(event.get("event_id")):
            features.append("decompression:has_event_id")
        if status:
            features.append(f"decompression:event_status:{_safe_part(status)}")
        reason_id = _int_value(event.get("reason_id"), 0) or 0
        reason = DECOMPRESSION_REASON_NAMES.get(reason_id)
        if reason:
            features.append(f"decompression:event_reason:{_safe_part(reason)}")
        features.extend(_decompression_unmaterialized_features(status_id, reason_id))
        payload_role = DECOMPRESSION_PAYLOAD_ROLE_NAMES.get(_int_value(event.get("payload_role_id"), 0) or 0)
        if payload_role:
            features.append(f"decompression:payload_role:{_safe_part(payload_role)}")
        source_kind = DECOMPRESSION_SOURCE_KIND_NAMES.get(_int_value(event.get("source_kind_id"), 0) or 0)
        if source_kind:
            features.append(f"decompression:source_kind:{_safe_part(source_kind)}")
        provider_id = _string_value(event.get("provider_id"))
        if provider_id:
            features.append(f"decompression:provider:{_safe_part(provider_id)}")
        codec_id = _string_value(event.get("codec_id"))
        if codec_id:
            features.append(f"decompression:codec:{_safe_part(codec_id)}")
        codec_support = DECOMPRESSION_CODEC_SUPPORT_NAMES.get(_int_value(event.get("codec_support_id"), 0) or 0)
        if codec_support:
            features.append(f"decompression:codec_support:{_safe_part(codec_support)}")
        if _int_value(event.get("simulated_output_size")) is not None:
            features.append("decompression:simulated_output")
        if _string_value(event.get("simulated_output_sha256")):
            features.append("decompression:simulated_output_hash")
        features.extend(_decompression_decompressor_features(event))
        features.extend(_decompression_source_range_features(event))
        features.extend(_decompression_output_address_features(event))
        features.extend(_decompression_source_load_entry_features(event))
        features.extend(_decompression_pattern_features(event))
        for feature in features:
            xrefs.append(
                _xref(
                    row,
                    feature,
                    "decompression_event",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=event_kind,
                    value=status_id,
                    text=text,
                )
            )
    return xrefs


def _analysis_xrefs(
    row: dict[str, object],
    analysis: dict[str, Any],
    row_locations: dict[tuple[int, int], tuple[int, str | None, str | None]],
) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    findings = analysis.get("findings")
    if isinstance(findings, dict):
        required_cpu = findings.get("required_cpu")
        if isinstance(required_cpu, int) and required_cpu in CPU_NAMES:
            xrefs.append(_xref(row, f"cpu:{CPU_NAMES[required_cpu]}", "cpu_requirement", value=required_cpu, text=CPU_NAMES[required_cpu]))
        violation_count = findings.get("cpu_violation_count")
        if isinstance(violation_count, int) and violation_count > 0:
            for index in range(violation_count):
                xrefs.append(_xref(row, "diagnostic:cpu_violation", "diagnostic", value=index, text="CPU violation"))
    xrefs.extend(_decompression_analysis_xrefs(row, analysis, row_locations))
    for table in _dict_items(analysis.get("table_records")):
        role = _table_role_name(table)
        table_kind = _table_kind_name(table)
        section_index = _int_value(table.get("section_index"), 0)
        offset = _int_value(table.get("offset"))
        row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
        base_expression = _table_base_expression_name(table)
        conflict_state = _conflict_state_name(table)
        conflicted = _bool_value(table.get("conflicted"))
        source_pattern = _structured_table_source_pattern(table)
        entry_count = _int_value(table.get("entry_count"))
        consumer_section = _int_value(table.get("consumer_section"))
        consumer_offset = _int_value(table.get("consumer_offset"))
        features = [
            "table:any",
            f"table:role:{_safe_part(role)}",
            f"table:kind:{_safe_part(table_kind)}",
        ]
        if conflicted:
            features.append("table:conflict")
            if conflict_state:
                features.append(f"table:conflict_state:{_safe_part(conflict_state)}")
        if source_pattern:
            features.append(f"table:source_pattern:{_safe_part(source_pattern)}")
        if base_expression:
            features.append(f"table:base:{_safe_part(base_expression)}")
        if consumer_section is not None and consumer_offset is not None:
            features.append("table:consumer")
        entry_size = _int_value(table.get("entry_size"))
        if entry_size is not None:
            features.append(f"table:entry_size:{entry_size}")
        for feature in features:
            xrefs.append(_xref(row, feature, "table_record", section=section_index, offset=offset,
                row_index=row_index, stable_key=stable_key, symbol=role, value=entry_count,
                text=row_text or table_kind))
        if consumer_section is not None and consumer_offset is not None:
            consumer_row_index, consumer_stable_key, consumer_row_text = _row_location(
                row_locations, consumer_section, consumer_offset
            )
            xrefs.append(_xref(row, "table:consumer", "table_consumer", section=consumer_section,
                offset=consumer_offset, row_index=consumer_row_index, stable_key=consumer_stable_key,
                symbol=role, value=entry_count, text=consumer_row_text or table_kind))
    for record in _dict_items(analysis.get("table_candidate_records")):
        section_index = _int_value(record.get("section_index"), 0)
        offset = _int_value(record.get("offset"))
        row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
        status = _recovered_indirect_status_name(record)
        shape = _recovered_indirect_shape_name(record)
        flow = _recovered_indirect_flow_name(record)
        source_pattern = _indirect_site_source_pattern(record)
        conflict_state = _conflict_state_name(record)
        target_count = _int_value(record.get("target_count"))
        source_size = _int_value(record.get("source_size"))
        expression_base_offset = _int_value(record.get("expression_base_offset"))
        table_offset = _int_value(record.get("table_offset"))
        table_size = _int_value(record.get("table_size"))
        table_bounds_status_id = _int_value(record.get("table_bounds_status_id"), 0) or 0
        table_bounds_status = _recovered_indirect_table_bounds_status_name(record)
        table_entry_size = _int_value(record.get("table_entry_size"))
        text = row_text or _string_value(record.get("detail")) or f"{flow} {shape} {status}"
        features = [
            "table:candidate_unresolved",
            f"table:candidate_unresolved:source_pattern:{_safe_part(source_pattern)}",
            f"table:candidate_unresolved:status:{_safe_part(status)}",
            f"table:candidate_unresolved:shape:{_safe_part(shape)}",
            f"table:candidate_unresolved:flow:{_safe_part(flow)}",
        ]
        if conflict_state:
            features.append(f"table:candidate_unresolved:conflict_state:{_safe_part(conflict_state)}")
        if source_size is not None:
            features.append("table:candidate_unresolved:source_range")
        if expression_base_offset is not None:
            features.append("table:candidate_unresolved:expression_base")
        if table_offset is not None:
            features.append("table:candidate_unresolved:table_base")
        if table_size is not None:
            features.append("table:candidate_unresolved:table_bounds")
        if table_bounds_status_id != 0:
            features.append(f"table:candidate_unresolved:table_bounds_status:{_safe_part(table_bounds_status)}")
        if table_entry_size is not None:
            features.append(f"table:candidate_unresolved:entry_size:{table_entry_size}")
        for feature in features:
            xrefs.append(
                _xref(
                    row,
                    feature,
                    "table_candidate",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    value=target_count,
                    text=text,
                )
            )
    for record in _dict_items(analysis.get("memory_layout_records")):
        record_kind = _memory_layout_record_kind_name(record)
        memory_kind = _memory_layout_memory_kind_name(record)
        section_index = _int_value(record.get("section_index"), 0)
        source_offset = _int_value(record.get("source_offset"))
        row_index, stable_key, row_text = _row_location(row_locations, section_index, source_offset)
        runtime_address = _int_value(record.get("runtime_address"))
        record_address = _int_value(record.get("address"))
        record_value = runtime_address if runtime_address is not None else record_address
        sink_address = _int_value(record.get("sink_address"))
        range_space_kind = _int_value(record.get("range_space_kind"))
        range_size = _int_value(record.get("range_size"))
        owner_range_start = _int_value(record.get("owner_range_start"))
        owner_range_size = _int_value(record.get("owner_range_size"))
        owner_range_end = _int_value(record.get("owner_range_end"))
        owner_range_xref = (
            {
                "owner_range_start": owner_range_start,
                "owner_range_size": owner_range_size,
                "owner_range_end": owner_range_end,
            }
            if owner_range_start is not None and owner_range_size is not None and owner_range_end is not None
            else {}
        )
        layout_kind = _int_value(record.get("layout_kind"))
        layout_kind_name = BASE_LAYOUT_KIND_NAMES.get(layout_kind) if layout_kind is not None else None
        root_struct = _string_value(record.get("root_struct_name")) or _string_value(record.get("owner_struct_name"))
        field_expr = _string_value(record.get("field_expr")) or _string_value(record.get("field_name"))
        for feature in (
            "memory-layout:any",
            f"memory-layout:record:{_safe_part(record_kind)}",
            f"memory-layout:kind:{_safe_part(memory_kind)}",
        ):
            xrefs.append(_xref(row, feature, "memory_layout", section=section_index, offset=source_offset,
                row_index=row_index, stable_key=stable_key, symbol=memory_kind, value=record_value,
                text=row_text or memory_kind, **owner_range_xref))
        if sink_address is not None:
            xrefs.append(_xref(row, "memory-layout:sink_address", "memory_layout", section=section_index,
                offset=source_offset, row_index=row_index, stable_key=stable_key, symbol=memory_kind,
                value=sink_address, text=row_text or memory_kind, **owner_range_xref))
        if range_space_kind is not None:
            xrefs.append(_xref(row, "memory-layout:range", "memory_layout", section=section_index,
                offset=source_offset, row_index=row_index, stable_key=stable_key, symbol=memory_kind,
                value=record_value, text=row_text or memory_kind, **owner_range_xref))
            xrefs.append(_xref(row, f"memory-layout:range_space:{range_space_kind}", "memory_layout",
                section=section_index, offset=source_offset, row_index=row_index, stable_key=stable_key,
                symbol=memory_kind, value=record_value, text=row_text or memory_kind, **owner_range_xref))
        if range_size is not None:
            xrefs.append(_xref(row, f"memory-layout:range_size:{range_size}", "memory_layout",
                section=section_index, offset=source_offset, row_index=row_index, stable_key=stable_key,
                symbol=memory_kind, value=range_size, text=row_text or memory_kind, **owner_range_xref))
        if layout_kind_name:
            xrefs.append(_xref(row, f"memory-layout:layout_kind:{_safe_part(layout_kind_name)}",
                "memory_layout", section=section_index, offset=source_offset, row_index=row_index,
                stable_key=stable_key, symbol=layout_kind_name, value=record_value, text=row_text or memory_kind,
                **owner_range_xref))
        if root_struct:
            xrefs.append(_xref(row, f"memory-layout:platform_struct:{_safe_part(root_struct)}",
                "memory_layout", section=section_index, offset=source_offset, row_index=row_index,
                stable_key=stable_key, symbol=root_struct, value=record_value, text=row_text or memory_kind,
                **owner_range_xref))
        if field_expr:
            xrefs.append(_xref(row, f"memory-layout:platform_field:{_safe_part(field_expr)}",
                "memory_layout", section=section_index, offset=source_offset, row_index=row_index,
                stable_key=stable_key, symbol=field_expr, value=record_value, text=row_text or memory_kind,
                **owner_range_xref))
        effect_kind = _int_value(record.get("effect_kind"))
        effect_kind_name = PLATFORM_EFFECT_NAMES.get(effect_kind) if effect_kind is not None else None
        if effect_kind_name:
            xrefs.append(_xref(row, "memory-layout:storage_effect",
                "memory_layout", section=section_index, offset=source_offset, row_index=row_index,
                stable_key=stable_key, symbol=effect_kind_name, value=record_value, text=row_text or memory_kind,
                **owner_range_xref))
            xrefs.append(_xref(row, f"memory-layout:storage_effect:{_safe_part(effect_kind_name)}",
                "memory_layout", section=section_index, offset=source_offset, row_index=row_index,
                stable_key=stable_key, symbol=effect_kind_name, value=record_value, text=row_text or memory_kind,
                **owner_range_xref))
        conflict_state = _conflict_state_name(record)
        conflict_state_id = _conflict_state_id(record)
        if conflict_state_id is not None and conflict_state_id != CONFLICT_STATE_CLEAN:
            xrefs.append(_xref(row, f"memory-layout:conflict_state:{_safe_part(conflict_state)}",
                "memory_layout", section=section_index, offset=source_offset, row_index=row_index,
                stable_key=stable_key, symbol=memory_kind, value=record_value, text=row_text or conflict_state,
                **owner_range_xref))
        if _bool_value(record.get("conflicted")):
            xrefs.append(_xref(row, "memory-layout:conflict", "memory_layout", section=section_index,
                offset=source_offset, row_index=row_index, stable_key=stable_key, symbol=memory_kind,
                value=record_value, text=row_text or conflict_state, **owner_range_xref))
    for section in _dict_items(analysis.get("sections")):
        section_index = _int_value(section.get("section_index"), 0)
        for call in _dict_items(section.get("recovered_platform_calls")):
            library = _string_value(call.get("library_name")) or _string_value(call.get("note_base_name")) or "unknown"
            function = (
                _string_value(call.get("function_name"))
                or _string_value(call.get("symbol_name"))
                or _string_value(call.get("note_symbol_name"))
                or "unknown"
            ).removeprefix("_LVO")
            offset = _int_value(call.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            text = row_text or f"{library}/{function}"
            resolution = _platform_call_resolution(call)
            xrefs.append(_xref(row, "os_call:any", "os_call", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=library, text=text, resolution=resolution))
            xrefs.append(_xref(row, f"os_call_library:{_safe_part(library)}", "os_call", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=library, text=text, resolution=resolution))
            xrefs.append(_xref(row, f"os:{_safe_part(library)}/{_safe_part(function)}", "os_call", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=library, text=text, resolution=resolution))
            for feature in _device_call_features(function, call):
                xrefs.append(_xref(row, feature, "device_call", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=library, text=text, resolution=resolution))
            xrefs.append(_xref(row, f"os_library:{_safe_part(library)}", "os_library", symbol=library, text=library))
            available_since = _string_value(call.get("available_since"))
            if available_since:
                xrefs.append(_xref(row, f"os_version:min:{_safe_part(available_since)}", "os_version", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=available_since, text=text, resolution=resolution))
            for item in _dict_items(call.get("inputs")):
                value_domain = _string_value(item.get("value_domain"))
                if value_domain:
                    xrefs.append(_xref(row, f"value_domain:{_safe_part(value_domain)}", "value_domain", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=value_domain, text=text, resolution=resolution))
                i_struct = _string_value(item.get("i_struct"))
                if i_struct:
                    xrefs.append(_xref(row, f"struct:{_safe_part(i_struct)}", "struct", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=i_struct, text=text, resolution=resolution))
            for item in _dict_items(call.get("outputs")):
                output_struct = _string_value(item.get("o_struct"))
                for reg in _list_strings(item.get("regs")):
                    xrefs.append(_xref(row, f"os_call_output_reg:{_safe_part(reg)}", "os_call_output", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=reg, text=text, resolution=resolution))
                    if output_struct:
                        xrefs.append(_xref(row, f"os_call_output_struct:{_safe_part(output_struct)}", "os_call_output_struct", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, access=reg, value=output_struct, text=text, resolution=resolution))
                value_domain = _string_value(item.get("value_domain"))
                if value_domain:
                    xrefs.append(_xref(row, f"value_domain:{_safe_part(value_domain)}", "value_domain", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=value_domain, text=text, resolution=resolution))
                if output_struct:
                    xrefs.append(_xref(row, f"struct:{_safe_part(output_struct)}", "struct", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=output_struct, text=text, resolution=resolution))
        for effect in _dict_items(section.get("recovered_platform_effects")):
            offset = _int_value(effect.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            effect_kind = _int_value(effect.get("kind"))
            effect_kind_name = PLATFORM_EFFECT_NAMES.get(effect_kind) if effect_kind is not None else None
            base_name = _string_value(effect.get("base_name"))
            if effect_kind_name:
                xrefs.append(_xref(row, f"platform_effect:{effect_kind_name}", "platform_effect", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=effect_kind_name, text=row_text or effect_kind_name))
            if base_name:
                xrefs.append(_xref(row, f"platform_base:{_safe_part(base_name)}", "platform_effect", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=base_name, text=row_text or base_name))
                if effect_kind == PLATFORM_EFFECT_WRITE_BASE_SLOT:
                    xrefs.append(_xref(row, "app_slot:base_slot", "app_slot_base_slot", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=base_name, value=_int_value(effect.get("displacement")), text=row_text or base_name))
                    xrefs.append(_xref(row, f"app_slot_base:{_safe_part(base_name)}", "app_slot_base_slot", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=base_name, value=_int_value(effect.get("displacement")), text=row_text or base_name))
            semantic_kind = _string_value(effect.get("semantic_kind"))
            if semantic_kind:
                xrefs.append(_xref(row, f"semantic:{_safe_part(semantic_kind)}", "platform_effect", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=semantic_kind, text=row_text or base_name or semantic_kind))
            value_domain = _string_value(effect.get("value_domain_name"))
            if value_domain:
                xrefs.append(_xref(row, f"value_domain:{_safe_part(value_domain)}", "value_domain", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=value_domain, text=row_text or base_name or value_domain))
            type_name = _string_value(effect.get("type_name"))
            if type_name:
                xrefs.append(_xref(row, f"type:{_safe_part(type_name)}", "type", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=type_name, text=row_text or base_name or type_name))
                storage_target = TYPED_STORAGE_EFFECT_TARGETS.get(effect_kind)
                if storage_target:
                    storage_text = row_text or base_name or type_name
                    storage_value = _int_value(effect.get("target_offset"))
                    if storage_value is None:
                        storage_value = _int_value(effect.get("displacement"))
                    for feature in (
                        "typed_storage:any",
                        f"typed_storage_kind:{_safe_part(effect_kind_name or 'unknown')}",
                        f"typed_storage_type:{_safe_part(type_name)}",
                        f"typed_storage_target:{_safe_part(storage_target)}",
                    ):
                        xrefs.append(
                            _xref(
                                row,
                                feature,
                                "typed_storage",
                                section=section_index,
                                offset=offset,
                                row_index=row_index,
                                stable_key=stable_key,
                                symbol=type_name,
                                access=storage_target,
                                value=storage_value,
                                text=storage_text,
                            )
                        )
        for ref in _dict_items(section.get("app_slot_refs")):
            access = _string_value(ref.get("access")) or "unknown"
            offset = _int_value(ref.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            symbol = _string_value(ref.get("symbol")) or _app_slot_symbol(ref.get("displacement"))
            displacement = _int_value(ref.get("displacement"))
            xrefs.append(_xref(row, "app_slot:any", "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=row_text or symbol or "app slot"))
            xrefs.append(_xref(row, f"app_slot:{_safe_part(access)}", "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=row_text or symbol or "app slot"))
        for access in _dict_items(section.get("recovered_platform_typed_accesses")):
            offset = _int_value(access.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            xrefs.extend(
                _platform_typed_access_xrefs(
                    row,
                    access,
                    section_index=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    row_text=row_text,
                )
            )
        for access in _dict_items(section.get("recovered_platform_unresolved_typed_accesses")):
            offset = _int_value(access.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            xrefs.extend(
                _platform_unresolved_typed_access_xrefs(
                    row,
                    access,
                    section_index=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    row_text=row_text,
                )
            )
        for runtime_view in _dict_items(section.get("runtime_views")):
            storage = _int_value(runtime_view.get("storage_address"))
            runtime = _int_value(runtime_view.get("runtime_address"))
            kind = _int_value(runtime_view.get("kind"))
            storage_offset = _int_value(runtime_view.get("storage_offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, storage_offset)
            xrefs.append(_xref(row, "runtime:view", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or f"storage=${_hex_int(storage)} runtime=${_hex_int(runtime)}"))
            if kind is not None:
                xrefs.append(_xref(row, f"runtime:view_kind:{kind}", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=kind, text=row_text or f"runtime view kind {kind}"))
            materialized = runtime_view.get("materialized")
            reason = _int_value(runtime_view.get("materialization_reason"))
            reason_name = RUNTIME_VIEW_MATERIALIZATION_REASONS.get(reason or 0)
            if materialized is True:
                xrefs.append(_xref(row, "runtime:view_materialized", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or "materialized runtime view"))
                if reason_name:
                    xrefs.append(_xref(row, f"runtime:view_materialized_reason:{_safe_part(reason_name)}", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or reason_name))
            elif materialized is False:
                xrefs.append(_xref(row, "runtime:suppressed_org_range", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or "suppressed ORG range"))
                if reason_name:
                    xrefs.append(_xref(row, f"runtime:suppressed_org_reason:{_safe_part(reason_name)}", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or reason_name))
                    if reason == RUNTIME_VIEW_SUPPRESSED_EXIT_TO_LARGER_RUNTIME_RANGE:
                        xrefs.append(_xref(row, "suppressed-weak-org-range", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or reason_name))
                        if runtime is not None and runtime < 0x100:
                            xrefs.append(_xref(row, "low-vector-trampoline", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or reason_name))
            relationship_kind = _int_value(runtime_view.get("relationship_kind"))
            relationship_name = RUNTIME_VIEW_RELATIONSHIP_NAMES.get(relationship_kind or RUNTIME_VIEW_RELATIONSHIP_NONE)
            if relationship_kind is not None and relationship_kind != RUNTIME_VIEW_RELATIONSHIP_NONE and relationship_name:
                related_runtime = _int_value(runtime_view.get("related_runtime_address"))
                xrefs.append(_xref(row, f"runtime:view_relationship:{_safe_part(relationship_name)}", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=related_runtime, text=row_text or relationship_name))
                xrefs.append(_xref(row, "runtime:view_related_range", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=related_runtime, text=row_text or relationship_name))
                for role_feature in RUNTIME_VIEW_RELATIONSHIP_ROLE_FEATURES.get(relationship_kind, ()):
                    xrefs.append(_xref(row, role_feature, "runtime_view", section=section_index,
                        offset=storage_offset, row_index=row_index, stable_key=stable_key, value=related_runtime,
                        text=row_text or relationship_name))
            if storage is not None and runtime is not None and storage != runtime:
                xrefs.append(_xref(row, "runtime:copied_code", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or f"copied code ${runtime:04X}"))
                if storage < 0x200 and runtime < 0x1000:
                    xrefs.append(_xref(row, "runtime:copied_entry_stub", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or f"copied entry stub ${runtime:04X}"))
        for signal in _dict_items(section.get("orphan_code_signals")):
            offset = _int_value(signal.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            reason = _orphan_code_signal_reason_name(signal)
            status = _orphan_code_signal_status_name(signal)
            terminal_flow = _orphan_code_signal_terminal_flow_name(signal)
            required_cpu = _int_value(signal.get("required_cpu"))
            instruction_count = _int_value(signal.get("instruction_count"))
            decode_conflict_count = _int_value(signal.get("decode_conflict_count"))
            context = _orphan_code_signal_context_name(signal)
            missing_inbound = _orphan_code_signal_inbound_name(signal)
            nearby_data_class = _orphan_code_signal_nearby_data_name(signal)
            nearby_data_relation = _orphan_code_signal_nearby_data_relation_name(signal)
            nearby_data_offset = _int_value(signal.get("nearby_data_offset"))
            nearby_data_distance = _int_value(signal.get("nearby_data_distance"))
            size = _int_value(signal.get("size"))
            text = row_text or _string_value(signal.get("detail")) or f"orphan code {reason}:{status}"
            features = [
                "orphan-code:signal",
                f"orphan-code:reason:{_safe_part(reason)}",
                f"orphan-code:status:{_safe_part(status)}",
                f"orphan-code:{_safe_part(reason)}:{_safe_part(status)}",
            ]
            if terminal_flow:
                features.append(f"orphan-code:terminal_flow:{_safe_part(terminal_flow)}")
            if required_cpu is not None:
                features.append(f"orphan-code:required_cpu:{required_cpu}")
            if instruction_count is not None:
                features.append("orphan-code:has_instruction_count")
                features.append(f"orphan-code:instruction_count:{instruction_count}")
            if decode_conflict_count is not None and decode_conflict_count > 0:
                features.append("orphan-code:decode_conflict")
            if context:
                features.append(f"orphan-code:context:{_safe_part(context)}")
            if missing_inbound and _orphan_code_signal_has_actionable_missing_inbound(status):
                features.append(f"orphan-code:missing_inbound:{_safe_part(missing_inbound)}")
            if nearby_data_class:
                features.append(f"orphan-code:nearby_data:{_safe_part(nearby_data_class)}")
                if nearby_data_offset is not None:
                    features.append("orphan-code:nearby_data:located")
                if nearby_data_distance is not None:
                    features.append(f"orphan-code:nearby_data_distance:{nearby_data_distance}")
                if nearby_data_relation:
                    features.append(
                        f"orphan-code:nearby_data:{_safe_part(nearby_data_relation)}:"
                        f"{_safe_part(nearby_data_class)}"
                    )
            for feature in features:
                xrefs.append(
                    _xref(
                        row,
                        feature,
                        "orphan_code_signal",
                        section=section_index,
                        offset=offset,
                        row_index=row_index,
                        stable_key=stable_key,
                        value=size,
                        text=text,
                    )
                )
        recovered_indirect_sites = list(_dict_items(section.get("recovered_indirect_sites")))
        for site in recovered_indirect_sites:
            offset = _int_value(site.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            status = _recovered_indirect_status_name(site)
            shape = _recovered_indirect_shape_name(site)
            flow = _recovered_indirect_flow_name(site)
            source_pattern = _indirect_site_source_pattern(site)
            target_count = _int_value(site.get("target_count"))
            text = row_text or _string_value(site.get("detail")) or f"{flow} {shape} {status}"
            features = [
                "analysis:indirect_site",
                f"analysis:indirect_site:status:{_safe_part(status)}",
                f"analysis:indirect_site:shape:{_safe_part(shape)}",
                f"analysis:indirect_site:flow:{_safe_part(flow)}",
                f"analysis:indirect_site:source_pattern:{_safe_part(source_pattern)}",
            ]
            for feature in features:
                xrefs.append(
                    _xref(
                        row,
                        feature,
                        "indirect_site",
                        section=section_index,
                        offset=offset,
                        row_index=row_index,
                        stable_key=stable_key,
                        value=target_count,
                        text=text,
                    )
                )
        violations = _dict_items(section.get("violations"))
        if violations:
            for index, violation in enumerate(violations):
                offset = _int_value(violation.get("offset"))
                row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
                message = _string_value(violation.get("message")) or "analysis violation"
                kind = _int_value(violation.get("kind"))
                xrefs.append(_xref(row, "diagnostic:analysis_violation", "diagnostic", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=kind if kind is not None else index, text=row_text or message))
        else:
            violation_count = _int_value(section.get("violation_count"), 0) or 0
            for index in range(violation_count):
                xrefs.append(_xref(row, "diagnostic:analysis_violation", "diagnostic", section=section_index, value=index, text="analysis violation"))
        for name, feature in (("recovered_string_ref_count", "data:string_ref"),):
            count = _int_value(section.get(name), 0) or 0
            for index in range(count):
                xrefs.append(_xref(row, feature, "analysis_count", section=section_index, value=index, text=name))
        if not recovered_indirect_sites:
            count = _int_value(section.get("recovered_indirect_site_count"), 0) or 0
            for index in range(count):
                xrefs.append(
                    _xref(row, "analysis:indirect_site", "analysis_count", section=section_index, value=index,
                        text="recovered_indirect_site_count")
                )
    return xrefs


def _listing_xrefs(
    row: dict[str, object],
    listing: dict[str, Any],
    *,
    feature_bag: FeatureBag | None = None,
) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    direct_control_stub_rows = _listing_direct_control_stub_table_row_features(listing)
    for row_index, listing_row in enumerate(_dict_items(listing.get("rows"))):
        text = _string_value(listing_row.get("text")) or ""
        stripped_text = text.strip()
        opcode_or_directive = (_string_value(listing_row.get("opcode_or_directive")) or "").upper()
        is_equate = bool(re.search(r"(^|\s)EQU(\s|$)", text))
        section_index = _int_value(listing_row.get("section_index"), -1)
        offset = listing_row.get("start_offset") if isinstance(listing_row.get("start_offset"), int) else listing_row.get("addr")
        stable_key = _string_value(listing_row.get("stable_key"))
        data_class_flags = _listing_row_data_class_flags(listing_row)
        data_class = _data_role_name(data_class_flags)
        copper_row = _data_role_has(data_class_flags, DATA_ROLE_COPPER_LIST)
        hardware_symbol_refs: list[tuple[str, str]] = []
        seen_group_features: set[str] = set()
        example = _offset_example(section_index, offset, stripped_text[:160])
        example["row_index"] = row_index
        label_symbol = _listing_row_label_symbol(listing_row)
        if label_symbol:
            if feature_bag is not None:
                feature_bag.add("label:any", example=example)
                feature_bag.add("label:definition", example=example)
        direct_control_features = sorted(direct_control_stub_rows.get(row_index, ()))
        code_start_reason_features = _listing_code_start_reason_features(listing_row)
        if direct_control_features:
            if feature_bag is not None:
                for feature in direct_control_features:
                    feature_bag.add(feature, example=example)
            for feature in direct_control_features:
                xrefs.append(
                    _xref(
                        row,
                        feature,
                        "analysis_ref",
                        section=section_index,
                        offset=offset,
                        row_index=row_index,
                        stable_key=stable_key,
                        text=stripped_text,
                    )
                )
        for feature in code_start_reason_features:
            if feature_bag is not None:
                feature_bag.add(feature, example=example)
            xrefs.append(
                _xref(
                    row,
                    feature,
                    "analysis_ref",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    text=stripped_text,
                )
            )
        if _listing_row_is_kind(listing_row, LISTING_ROW_KIND_DIRECTIVE) and opcode_or_directive == "ORG":
            org_address = _org_directive_address(listing_row, text)
            org_example = dict(example)
            if org_address is not None:
                org_example["runtime_address"] = org_address
            for feature in ("materialized-org-range", "runtime:materialized_org_range"):
                if feature_bag is not None:
                    feature_bag.add(feature, example=org_example)
                xrefs.append(_xref(row, feature, "runtime_org", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=org_address, text=stripped_text))
            if org_address is not None:
                feature = f"runtime:materialized_org_address:{org_address:08X}"
                if feature_bag is not None:
                    feature_bag.add(feature, example=org_example)
                xrefs.append(_xref(row, feature, "runtime_org", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=org_address, text=stripped_text))
        for symbol, addend in _runtime_table_base_addend_matches(text):
            table_example = dict(example)
            table_example["symbol"] = symbol
            table_example["addend"] = addend
            if feature_bag is not None:
                feature_bag.add("analysis:runtime_table_base_addend", example=table_example)
                feature_bag.add(f"analysis:runtime_table_base_addend:{_safe_part(symbol)}", example=table_example)
            xrefs.append(
                _xref(
                    row,
                    "analysis:runtime_table_base_addend",
                    "analysis_ref",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=symbol,
                    value=addend,
                    text=stripped_text,
                )
            )
            xrefs.append(
                _xref(
                    row,
                    f"analysis:runtime_table_base_addend:{_safe_part(symbol)}",
                    "analysis_ref",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=symbol,
                    value=addend,
                    text=stripped_text,
                )
            )
        if data_class:
            data_feature = f"data:{_safe_part(data_class)}"
            if feature_bag is not None:
                feature_bag.add(data_feature, example=example)
            xrefs.append(_xref(row, data_feature, "data_class", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=data_class, text=stripped_text))
            for feature in _listing_table_shape_features(text, data_class_flags):
                if feature_bag is not None:
                    feature_bag.add(feature, example=example)
                xrefs.append(_xref(row, feature, "table_shape", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=data_class, text=stripped_text))
            if _data_role_has(data_class_flags, DATA_ROLE_COPPER_LIST):
                if feature_bag is not None:
                    feature_bag.add("hardware:custom", example=example)
                xrefs.append(_xref(row, "hardware:custom", "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol="_custom", text=stripped_text))
                for feature in amiga_hardware_usage.group_features("_custom", "copper", copper_row=True):
                    if feature not in seen_group_features:
                        seen_group_features.add(feature)
                        if feature_bag is not None:
                            feature_bag.add(feature, example=example)
                        xrefs.append(_xref(row, feature, "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol="copper", text=stripped_text))
        if not is_equate:
            for base in amiga_hardware_usage.HARDWARE_BASES:
                if base in text:
                    feature = f"hardware:{base.removeprefix('_')}"
                    if feature_bag is not None:
                        feature_bag.add(feature, example=example)
                    xrefs.append(_xref(row, feature, "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=base, text=stripped_text))
            hardware_symbol_refs = amiga_hardware_usage.symbol_refs_from_listing_text(text, copper_row=copper_row)
            for base, symbol in hardware_symbol_refs:
                feature = f"hardware_register:{_safe_part(symbol)}"
                if feature_bag is not None:
                    feature_bag.add(feature, example=example)
                xrefs.append(_xref(row, feature, "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, text=stripped_text))
                if _data_role_has(data_class_flags, DATA_ROLE_COPPER_LIST):
                    feature = f"copper_register:{_safe_part(symbol)}"
                    xrefs.append(_xref(row, feature, "copper_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, text=stripped_text))
                for feature in amiga_hardware_usage.group_features(base, symbol, copper_row=copper_row):
                    if feature not in seen_group_features:
                        seen_group_features.add(feature)
                        if feature_bag is not None:
                            feature_bag.add(feature, example=example)
                        xrefs.append(_xref(row, feature, "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, text=stripped_text))
        for feature in amiga_hardware_usage.display_features_from_symbol_refs(text, hardware_symbol_refs, copper_row=copper_row):
            if feature_bag is not None:
                feature_bag.add(feature, example=example)
            xrefs.append(_xref(row, feature, "display_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, text=stripped_text))
        comment_text = _string_value(listing_row.get("comment_text")) or ""
        if "bitmap memory plane" in comment_text:
            if feature_bag is not None:
                feature_bag.add("display:bitmap_memory_use", example=example)
            xrefs.append(_xref(row, "display:bitmap_memory_use", "display_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, text=stripped_text))
        for operand in _dict_items(listing_row.get("operand_parts")):
            operand_text = _string_value(operand.get("text")) or stripped_text
            segment_addr = _int_value(operand.get("segment_addr"))
            symbol = _operand_symbol(operand)
            if symbol:
                if feature_bag is not None:
                    feature_bag.add("label:reference", example=example)
            if segment_addr is not None:
                ref_feature = (
                    "xref:data_ref" if _listing_row_is_kind(listing_row, LISTING_ROW_KIND_DATA) else "xref:code_ref"
                )
                if feature_bag is not None:
                    feature_bag.add("xref:segment_ref", example=example)
                    feature_bag.add(ref_feature, example=example)
                xrefs.append(_xref(row, "xref:segment_ref", "segment_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, value=segment_addr, text=operand_text))
                xrefs.append(_xref(row, ref_feature, "segment_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, value=segment_addr, text=operand_text))
            metadata = operand.get("metadata")
            if isinstance(metadata, dict):
                for key, prefix, kind in (
                    ("value_domain", "value_domain", "value_domain"),
                    ("semantic_kind", "semantic", "semantic"),
                    ("type_name", "type", "type"),
                ):
                    value = _string_value(metadata.get(key))
                    if value:
                        feature = f"{prefix}:{_safe_part(value)}"
                        if feature_bag is not None:
                            feature_bag.add(feature, example=example)
                        xrefs.append(_xref(row, feature, kind, section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, value=value, text=stripped_text))
        for app_ref in _dict_items(listing_row.get("app_slot_refs")):
            access = _string_value(app_ref.get("access")) or "unknown"
            symbol = _string_value(app_ref.get("symbol")) or _app_slot_symbol(app_ref.get("displacement"))
            displacement = _int_value(app_ref.get("displacement"))
            access_feature = f"app_slot:{_safe_part(access)}"
            if feature_bag is not None:
                feature_bag.add("app_slot:any", example=example)
                feature_bag.add(access_feature, example=example)
            xrefs.append(_xref(row, "app_slot:any", "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=stripped_text))
            xrefs.append(_xref(row, access_feature, "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=stripped_text))
        for runtime_ref in _dict_items(listing_row.get("runtime_address_refs")):
            runtime_class_flags = _int_value(runtime_ref.get("data_class_flags"), 0) or 0
            runtime_class = _data_role_name(runtime_class_flags)
            runtime_address = _int_value(runtime_ref.get("runtime_address"))
            sink_address = _int_value(runtime_ref.get("sink_address"))
            runtime_example = dict(example)
            if runtime_address is not None:
                runtime_example["runtime_address"] = runtime_address
            if sink_address is not None:
                runtime_example["sink_address"] = sink_address
            if runtime_class:
                data_feature = f"data:{_safe_part(runtime_class)}"
                if feature_bag is not None:
                    feature_bag.add(data_feature, example=runtime_example)
                    feature_bag.add("runtime:external_data_ref", example=runtime_example)
                xrefs.append(_xref(row, data_feature, "runtime_data_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=runtime_class, value=runtime_address, text=stripped_text))
                xrefs.append(_xref(row, "runtime:external_data_ref", "runtime_data_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=runtime_class, value=runtime_address, text=stripped_text))
                if _data_role_has(runtime_class_flags, DATA_ROLE_BITMAP):
                    if feature_bag is not None:
                        feature_bag.add("display:bitmap_memory", example=runtime_example)
                    xrefs.append(_xref(row, "display:bitmap_memory", "display_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=runtime_class, value=runtime_address, text=stripped_text))
        for access in _dict_items(listing_row.get("typed_accesses")):
            if feature_bag is not None:
                _add_platform_typed_access_features(feature_bag, access, example=example)
            xrefs.extend(
                _platform_typed_access_xrefs(
                    row,
                    access,
                    section_index=section_index,
                    offset=_int_value(offset),
                    row_index=row_index,
                    stable_key=stable_key,
                    row_text=stripped_text,
                )
            )
        for access in _dict_items(listing_row.get("unresolved_typed_accesses")):
            if feature_bag is not None:
                _add_platform_unresolved_typed_access_features(feature_bag, access, example=example)
            xrefs.extend(
                _platform_unresolved_typed_access_xrefs(
                    row,
                    access,
                    section_index=section_index,
                    offset=_int_value(offset),
                    row_index=row_index,
                    stable_key=stable_key,
                    row_text=stripped_text,
                )
            )
    return xrefs


def _app_slot_layout_xrefs(row: dict[str, object], app_slot_analysis: dict[str, Any]) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    for region in _dict_items(app_slot_analysis.get("regions")):
        source = _string_value(region.get("source")) or "unknown"
        if not _is_generated_app_slot_region_source(source):
            continue
        struct_name = _string_value(region.get("struct_name")) or "unknown"
        symbol = _string_value(region.get("symbol"))
        offset = _int_value(region.get("offset"))
        evidence = _dict_items(region.get("evidence"))
        first_evidence = evidence[0] if evidence else {}
        row_index = _int_value(first_evidence.get("row_index"))
        section = _int_value(first_evidence.get("hunk_index"))
        text = f"{symbol or 'app slot'}: {struct_name}"
        xrefs.append(
            _xref(
                row,
                "app_slot:typed_region",
                "app_slot_region",
                section=section,
                offset=offset,
                row_index=row_index,
                symbol=symbol,
                value=struct_name,
                text=text,
            )
        )
        xrefs.append(
            _xref(
                row,
                f"app_slot_region:{_safe_part(struct_name)}",
                "app_slot_region",
                section=section,
                offset=offset,
                row_index=row_index,
                symbol=symbol,
                value=struct_name,
                text=text,
            )
        )
        xrefs.append(
            _xref(
                row,
                f"app_slot_region_source:{_safe_part(source)}",
                "app_slot_region",
                section=section,
                offset=offset,
                row_index=row_index,
                symbol=symbol,
                value=source,
                text=text,
            )
        )
        for field_ref in _dict_items(region.get("field_refs")):
            field_symbol = _string_value(field_ref.get("symbol")) or symbol
            field_offset = _int_value(field_ref.get("field_offset"))
            field_name = _string_value(field_ref.get("field_name"))
            if not field_name:
                continue
            field_path = _field_path_text(struct_name, field_ref) or field_name
            refs = _dict_items(field_ref.get("refs"))
            first_ref = refs[0] if refs else {}
            field_xref = dict(
                section=section,
                offset=offset,
                row_index=_int_value(first_ref.get("row_index"), row_index),
                stable_key=_string_value(first_ref.get("stable_key")),
                symbol=field_symbol,
                value=field_offset,
                text=f"{field_path} in {struct_name}",
            )
            xrefs.append(_xref(row, "app_slot:typed_field_ref", "app_slot_field_ref", **field_xref))
            if field_ref.get("field_inherited") is True:
                xrefs.append(_xref(row, "app_slot:inherited_field_ref", "app_slot_field_ref", **field_xref))
            if field_ref.get("field_nested") is True:
                xrefs.append(_xref(row, "app_slot:nested_field_ref", "app_slot_field_ref", **field_xref))
            xrefs.append(
                _xref(row, f"app_slot_field_path:{_safe_part(field_path)}", "app_slot_field_ref", **field_xref)
            )
    for gap in _dict_items(app_slot_analysis.get("field_gaps")):
        start = _int_value(gap.get("start"))
        end = _int_value(gap.get("end"))
        size = _int_value(gap.get("size"))
        coverage = _string_value(gap.get("coverage")) or "unknown"
        field_path = _field_path_text(_string_value(gap.get("struct_name")) or "unknown", gap)
        text = (
            f"app slot field gap ${start:04X}-${end:04X} {coverage}"
            if start is not None and end is not None
            else "app slot field gap"
        )
        field_gap_xref = dict(offset=start, value=size, text=field_path or text)
        xrefs.append(_xref(row, "app_slot:field_gap", "app_slot_field_gap", **field_gap_xref))
        xrefs.append(_xref(row, f"app_slot_field_gap:{_safe_part(coverage)}", "app_slot_field_gap", **field_gap_xref))
        if field_path:
            xrefs.append(
                _xref(row, f"app_slot_field_gap_path:{_safe_part(field_path)}", "app_slot_field_gap", **field_gap_xref)
            )
    for gap in _dict_items(app_slot_analysis.get("gaps")):
        start = _int_value(gap.get("start"))
        end = _int_value(gap.get("end"))
        size = _int_value(gap.get("size"))
        text = f"app slot gap ${start:04X}-${end:04X}" if start is not None and end is not None else "app slot gap"
        xrefs.append(
            _xref(
                row,
                "app_slot:gap",
                "app_slot_gap",
                offset=start,
                value=size,
                text=text,
            )
        )
    for suggestion in _dict_items(app_slot_analysis.get("suggestions")):
        if suggestion.get("kind") != "app_slot_region":
            continue
        metadata = suggestion.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        symbol = _string_value(metadata.get("symbol"))
        offset = _int_value(metadata.get("offset"))
        struct_name = _string_value(metadata.get("struct_name")) or "unknown"
        evidence = _dict_items(suggestion.get("evidence"))
        first_evidence = evidence[0] if evidence else {}
        xrefs.append(
            _xref(
                row,
                "app_slot:suggested_region",
                "app_slot_suggestion",
                section=_int_value(first_evidence.get("hunk_index")),
                offset=offset,
                row_index=_int_value(first_evidence.get("row_index")),
                symbol=symbol,
                value=struct_name,
                text=_string_value(suggestion.get("summary")) or f"{symbol or 'app slot'}: {struct_name}",
            )
        )
    for arg in _dict_items(app_slot_analysis.get("untyped_api_args")):
        function_name = _string_value(arg.get("function")) or "unknown"
        reason = _string_value(arg.get("reason")) or "unknown"
        arg_xref = dict(
            section=_int_value(arg.get("hunk_index")),
            offset=_int_value(arg.get("addr")),
            row_index=_int_value(arg.get("row_index")),
            stable_key=_string_value(arg.get("stable_key")),
            source_stable_key=_string_value(arg.get("source_stable_key")),
            symbol=_string_value(arg.get("symbol")),
            value=_int_value(arg.get("displacement")),
            text=f"{arg.get('symbol') or 'app slot'} -> {function_name} {arg.get('register') or ''}".strip(),
        )
        xrefs.append(_xref(row, "app_slot:untyped_api_arg", "app_slot_api_arg", **arg_xref))
        xrefs.append(_xref(row, f"app_slot_api_arg:{_safe_part(function_name)}", "app_slot_api_arg", **arg_xref))
        xrefs.append(_xref(row, f"app_slot_api_arg_reason:{_safe_part(reason)}", "app_slot_api_arg", **arg_xref))
    return xrefs


def _xref(
    target_row: dict[str, object],
    feature: str,
    kind: str,
    *,
    section: object = None,
    offset: object = None,
    row_index: object = None,
    stable_key: str | None = None,
    symbol: str | None = None,
    access: str | None = None,
    value: object = None,
    text: str | None = None,
    resolution: str | None = None,
    source_stable_key: str | None = None,
    struct_size: object = None,
    classification_id: object = None,
    classification: str | None = None,
    container_candidate_count: object = None,
    container_struct_name: str | None = None,
    container_field_expr: str | None = None,
    refinement_applied: object = None,
    refined_struct_name: str | None = None,
    type_provenance_kind_id: object = None,
    type_provenance_kind: str | None = None,
    type_provenance_section: object = None,
    type_provenance_offset: object = None,
    owner_range_start: object = None,
    owner_range_size: object = None,
    owner_range_end: object = None,
) -> dict[str, object]:
    target_id = str(target_row.get("id"))
    kind_id = XREF_KIND_IDS.get(kind)
    feature_id = XREF_FEATURE_IDS.get(feature)
    feature_class_id, feature_value = _xref_feature_class(feature)
    payload: dict[str, object] = {
        "schema_version": 1,
        "target_id": target_id,
        "feature": feature,
        "kind": kind,
        "platform": target_row.get("platform"),
        "source_id": target_row.get("source_id"),
        "origin": target_row.get("origin"),
        "section": section if isinstance(section, (int, str)) else None,
        "offset": offset if isinstance(offset, int) else None,
        "row_index": row_index if isinstance(row_index, int) else None,
        "stable_key": stable_key,
        "symbol": symbol,
        "access": access,
        "resolution": resolution,
        "value": value if isinstance(value, (str, int, float, bool)) or value is None else str(value),
        "text": text or "",
    }
    if kind_id is not None:
        payload["kind_id"] = kind_id
    if feature_id is not None:
        payload["feature_id"] = feature_id
    if feature_class_id is not None:
        payload["feature_class_id"] = feature_class_id
        payload["feature_value"] = feature_value
    if isinstance(struct_size, int):
        payload["struct_size"] = struct_size
    if isinstance(classification_id, int):
        payload["classification_id"] = classification_id
    if classification is not None:
        payload["classification"] = classification
    if isinstance(container_candidate_count, int):
        payload["container_candidate_count"] = container_candidate_count
    if container_struct_name is not None:
        payload["container_struct_name"] = container_struct_name
    if container_field_expr is not None:
        payload["container_field_expr"] = container_field_expr
    if isinstance(refinement_applied, bool):
        payload["refinement_applied"] = refinement_applied
    if refined_struct_name is not None:
        payload["refined_struct_name"] = refined_struct_name
    if isinstance(type_provenance_kind_id, int):
        payload["type_provenance_kind_id"] = type_provenance_kind_id
    if type_provenance_kind is not None:
        payload["type_provenance_kind"] = type_provenance_kind
    if isinstance(type_provenance_section, int):
        payload["type_provenance_section"] = type_provenance_section
    if isinstance(type_provenance_offset, int):
        payload["type_provenance_offset"] = type_provenance_offset
    if isinstance(owner_range_start, int):
        payload["owner_range_start"] = owner_range_start
    if isinstance(owner_range_size, int):
        payload["owner_range_size"] = owner_range_size
    if isinstance(owner_range_end, int):
        payload["owner_range_end"] = owner_range_end
    if source_stable_key is not None:
        payload["source_stable_key"] = source_stable_key
    payload["id"] = _stable_xref_id(payload)
    return payload


def _xref_feature_class(feature: str) -> tuple[int | None, str | None]:
    for prefix, class_id in XREF_FEATURE_CLASS_DYNAMIC_PREFIXES:
        if feature.startswith(prefix):
            return class_id, feature.removeprefix(prefix)
    return None, None


def _stable_xref_id(payload: dict[str, object]) -> str:
    keys = (
        "target_id",
        "feature",
        "kind",
        "section",
        "offset",
        "row_index",
        "stable_key",
        "symbol",
        "access",
        "resolution",
        "value",
        "text",
    )
    if payload.get("source_stable_key") is not None:
        keys = (*keys[:7], "source_stable_key", *keys[7:])
    if payload.get("struct_size") is not None:
        keys = (*keys, "struct_size")
    if payload.get("classification_id") is not None:
        keys = (*keys, "classification_id")
    if payload.get("type_provenance_kind_id") is not None:
        keys = (*keys, "type_provenance_kind_id", "type_provenance_section", "type_provenance_offset")
    if payload.get("owner_range_start") is not None:
        keys = (*keys, "owner_range_start", "owner_range_size", "owner_range_end")
    raw = json.dumps({key: payload.get(key) for key in keys}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _dedupe_xrefs(xrefs: list[dict[str, object]]) -> list[dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for xref in xrefs:
        result[str(xref["id"])] = xref
    return list(result.values())


def _platform_call_resolution(call: dict[str, Any]) -> str:
    note_kind = _int_value(call.get("note_kind"), 0) or 0
    if note_kind == 1:
        return "indexed_vector"
    if note_kind == 2:
        return "callback_field"
    if note_kind == 3:
        return "local_wrapper"
    if note_kind == 4:
        return "direct_os_call"
    if note_kind == 5:
        return "stack_cleanup"
    return "direct"


def _device_call_features(function: str, call: dict[str, Any] | None = None) -> list[str]:
    if function in {
        "AbortIO",
        "BeginIO",
        "CheckIO",
        "CloseDevice",
        "DoIO",
        "OpenDevice",
        "SendIO",
        "WaitIO",
    }:
        features = ["device_call:any", f"device_call_function:{_safe_part(function)}"]
        for device_name in _device_names_from_call(call):
            safe_device = _safe_part(device_name)
            features.append(f"device:{safe_device}")
            features.append(f"device_call:{safe_device}/{_safe_part(function)}")
        return features
    return []


def _device_names_from_call(call: dict[str, Any] | None) -> list[str]:
    if not isinstance(call, dict):
        return []
    candidates: list[str] = []
    for key in ("device_name", "device", "target_device", "resolved_device"):
        value = _string_value(call.get(key))
        if value:
            candidates.append(value)
    for item in _dict_items(call.get("inputs")):
        input_name = (_string_value(item.get("name")) or "").casefold()
        if "device" not in input_name and input_name not in {"name", "devname"}:
            continue
        for key in ("device_name", "string_value", "value_text", "constant_name", "symbol", "value"):
            value = _string_value(item.get(key))
            if value:
                candidates.append(value)
    result: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        value = candidate.strip().strip('"')
        if not value.endswith(".device"):
            continue
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _app_slot_symbol(displacement: object) -> str | None:
    if isinstance(displacement, int):
        return f"app_{displacement & 0xFFFF:04X}"
    return None


def _field_path_text(struct_name: str, item: dict[str, object]) -> str | None:
    parts = _string_list(item.get("field_path"))
    if parts:
        return ".".join([struct_name, *parts])
    field_name = _string_value(item.get("field_name"))
    if field_name:
        return f"{struct_name}.{field_name}"
    return None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _listing_row_label_symbol(row: dict[str, Any]) -> str | None:
    label = _string_value(row.get("label"))
    if label:
        return label.rstrip(":").strip() or None
    text = (_string_value(row.get("text")) or "").strip()
    if text.endswith(":") and " " not in text and "\t" not in text:
        return text[:-1].strip() or None
    return None


def _operand_symbol(operand: dict[str, Any]) -> str | None:
    metadata = operand.get("metadata")
    if isinstance(metadata, dict):
        for key in ("symbol", "symbol_name", "label", "name"):
            value = _string_value(metadata.get(key))
            if value:
                return value.rstrip(":")
    text = _string_value(operand.get("text"))
    if not text:
        return None
    candidate = text.strip().split("+", 1)[0].split("(", 1)[0].split(",", 1)[0].strip()
    if not candidate or candidate.startswith("#") or candidate.startswith("$"):
        return None
    if re.match(r"^[A-Za-z_][A-Za-z0-9_$.]*$", candidate):
        return candidate.rstrip(":")
    return None


def _hex_int(value: int | None) -> str:
    return "?" if value is None else f"{value:04X}"


def _find_disk_file_entry(disk_entry: dict[str, Any], image_path: str) -> dict[str, Any]:
    expect = disk_entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    entries = inspect.get("entries") if isinstance(inspect, dict) else None
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and entry.get("path") == image_path:
                return entry
    raise RuntimeError(f"Missing disk file entry {image_path}")


def _dict_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _list_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _string_value(value: object) -> str | None:
    if isinstance(value, str) and value != "":
        return value
    if isinstance(value, int):
        return str(value)
    return None


def _int_value(value: object, default: int | None = None) -> int | None:
    return value if isinstance(value, int) else default


def _xref_kind_id(xref: dict[str, Any]) -> int:
    return _int_value(xref.get("kind_id"), 0) or 0


def _xref_feature_id(xref: dict[str, Any]) -> int:
    return _int_value(xref.get("feature_id"), 0) or 0


def _xref_feature_class_id(xref: dict[str, Any]) -> int:
    return _int_value(xref.get("feature_class_id"), 0) or 0


def _xref_feature_value(xref: dict[str, Any]) -> str | None:
    return _string_value(xref.get("feature_value"))


def _bool_value(value: object) -> bool:
    return value if isinstance(value, bool) else False


def _sort_int(value: object) -> int:
    return value if isinstance(value, int) else -1


def _offset_example(section_index: int | None, offset: object, text: object) -> dict[str, object]:
    example: dict[str, object] = {}
    if isinstance(section_index, int) and section_index >= 0:
        example["section"] = section_index
    if isinstance(offset, int):
        example["offset"] = offset
    if text is not None:
        example["text"] = str(text)
    return example


def _compact_value(value: object, depth: int = 0) -> object | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value[:200]
    if isinstance(value, (int, float, bool)):
        return value
    if depth >= 2:
        return None
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                continue
            compacted = _compact_value(value[key], depth + 1)
            if compacted is not None:
                result[key] = compacted
        return result if result else None
    if isinstance(value, list):
        result = []
        for item in value[:5]:
            compacted = _compact_value(item, depth + 1)
            if compacted is not None:
                result.append(compacted)
        return result if result else None
    return None


def _compact_example(example: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key in sorted(example):
        compacted = _compact_value(example[key])
        if compacted is not None:
            result[key] = compacted
    return result


def write_usage_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_usage_xrefs(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_usage_snippet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    index_path = snippet_rows_index_path(path)
    blob_path = snippet_rows_blob_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows_by_target: dict[str, list[dict[str, object]]] = {}
    index_rows: list[dict[str, object]] = []
    compressed_offset = 0
    for row in rows:
        target_id = str(row.get("target_id"))
        rows_by_target.setdefault(target_id, []).append(row)
    with blob_path.open("wb") as blob:
        for target_id in sorted(rows_by_target):
            target_rows = sorted(rows_by_target[target_id], key=lambda item: _sort_int(item.get("row_index")))
            raw_text = "".join(
                json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                for row in target_rows
            )
            raw_bytes = raw_text.encode("utf-8")
            compressed = zlib.compress(raw_bytes, level=6)
            blob.write(compressed)
            index_rows.append(
                {
                    "schema_version": 1,
                    "target_id": target_id,
                    "row_count": len(target_rows),
                    "raw_size": len(raw_bytes),
                    "compressed_offset": compressed_offset,
                    "compressed_size": len(compressed),
                    "compression": "zlib",
                }
            )
            compressed_offset += len(compressed)
    write_jsonl_manifest(index_path, index_rows)
    if path.exists():
        path.unlink()


def write_variant_index(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_type_flow_report(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_unresolved_typed_field_report(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def type_flow_snapshot_path(output_dir: Path, name: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    if not safe:
        safe = "snapshot"
    return output_dir / f"{safe}.jsonl"


def write_type_flow_snapshot(
    report_path: Path = DEFAULT_TYPE_FLOW_REPORT_OUTPUT,
    output_dir: Path = DEFAULT_TYPE_FLOW_SNAPSHOT_DIR,
    *,
    name: str,
) -> Path:
    rows = read_type_flow_report(report_path)
    snapshot_path = type_flow_snapshot_path(output_dir, name)
    write_type_flow_report(snapshot_path, rows)
    return snapshot_path


def write_type_flow_delta(path: Path, delta: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(delta, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_type_flow_baseline(path: Path, baseline: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_usage_manifest(path: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_usage_xrefs(path: Path = DEFAULT_XREF_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def snippet_rows_index_path(path: Path = DEFAULT_SNIPPET_ROWS_OUTPUT) -> Path:
    return path.with_name(f"{path.stem}.index.jsonl")


def snippet_rows_blob_path(path: Path = DEFAULT_SNIPPET_ROWS_OUTPUT) -> Path:
    return path.with_name(f"{path.stem}.blob")


def _read_compressed_snippet_block(blob_path: Path, entry: dict[str, Any]) -> list[dict[str, Any]]:
    offset = _int_value(entry.get("compressed_offset"))
    size = _int_value(entry.get("compressed_size"))
    if offset is None or size is None or offset < 0 or size < 0:
        return []
    with blob_path.open("rb") as blob:
        blob.seek(offset)
        compressed = blob.read(size)
    raw_text = zlib.decompress(compressed).decode("utf-8")
    rows: list[dict[str, Any]] = []
    for line in raw_text.splitlines():
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def read_usage_snippet_rows(path: Path = DEFAULT_SNIPPET_ROWS_OUTPUT) -> list[dict[str, Any]]:
    index_path = snippet_rows_index_path(path)
    blob_path = snippet_rows_blob_path(path)
    rows: list[dict[str, Any]] = []
    for entry in read_jsonl_manifest(index_path):
        rows.extend(_read_compressed_snippet_block(blob_path, entry))
    return rows


def read_usage_snippet_rows_for_target(
    target_id: str,
    path: Path = DEFAULT_SNIPPET_ROWS_OUTPUT,
) -> list[dict[str, Any]]:
    index_path = snippet_rows_index_path(path)
    blob_path = snippet_rows_blob_path(path)
    for entry in read_jsonl_manifest(index_path):
        if _string_value(entry.get("target_id")) == target_id:
            return _read_compressed_snippet_block(blob_path, entry)
    return []


def read_variant_index(path: Path = DEFAULT_VARIANT_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_type_flow_report(path: Path = DEFAULT_TYPE_FLOW_REPORT_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_unresolved_typed_field_report(
    path: Path = DEFAULT_UNRESOLVED_TYPED_FIELD_REPORT_OUTPUT,
) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_type_flow_delta(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_type_flow_baseline(path: Path = DEFAULT_TYPE_FLOW_BASELINE) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


_TYPE_FLOW_NUMERIC_ADDRESS_BASE_RE = re.compile(r"\$[0-9A-Fa-f]{2,8}(?:\.[wlWL])?\([aA]([0-7])\)")
_TYPE_FLOW_NUMERIC_ADDRESS_DISPLACEMENT_RE = re.compile(r"(-?)\$([0-9A-Fa-f]{2,8})(?:\.[wlWL])?\([aA][0-7]\)")
_TYPE_FLOW_ASSIGNMENT_RE = re.compile(r"^\s*(?:movea?|lea)\.[bwlBWL]\s+(.+?),\s*([dDaA][0-7])\b", re.IGNORECASE)
_TYPE_FLOW_STORE_RE = re.compile(r"^\s*move\.([bwlBWL])\s+([dDaA][0-7]),\s*(.+?)(?:\s*;.*)?$")
_TYPE_FLOW_REGISTER_RE = re.compile(r"([dDaA][0-7])")
_TYPE_FLOW_ADDRESS_BASE_RE = re.compile(r"\([aA]([0-7])\)")
_TYPE_FLOW_CALL_LIKE_RE = re.compile(r"^\s*(?:jsr|bsr|jmp|trap)\b", re.IGNORECASE)
_TYPE_FLOW_ADDRESS_EXPR_RE = re.compile(r"\([aA][0-7]\)")
_TYPE_FLOW_GLOBAL_OR_BASE_RE = re.compile(r"\$[0-9a-f]{4,8}(?:\.[wl])?$")

TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN = 1
TYPE_FLOW_CAUSE_API_OUTPUT_NEARBY = 2
TYPE_FLOW_CAUSE_API_OUTPUT_NEARBY_UNKNOWN_OUTPUT = 3
TYPE_FLOW_CAUSE_POST_CALL_REGISTER_COPY = 4
TYPE_FLOW_CAUSE_APP_SLOT_LOAD = 5
TYPE_FLOW_CAUSE_STACK_SLOT_LOAD = 6
TYPE_FLOW_CAUSE_GLOBAL_OR_BASE_SLOT_LOAD = 7
TYPE_FLOW_CAUSE_POST_CALL_EXISTING_BASE = 8

TYPE_FLOW_CAUSE_NAMES = {
    TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN: "unknown_pointer_chain",
    TYPE_FLOW_CAUSE_API_OUTPUT_NEARBY: "api_output_nearby",
    TYPE_FLOW_CAUSE_API_OUTPUT_NEARBY_UNKNOWN_OUTPUT: "api_output_nearby_unknown_output",
    TYPE_FLOW_CAUSE_POST_CALL_REGISTER_COPY: "post_call_register_copy",
    TYPE_FLOW_CAUSE_APP_SLOT_LOAD: "app_slot_load",
    TYPE_FLOW_CAUSE_STACK_SLOT_LOAD: "stack_slot_load",
    TYPE_FLOW_CAUSE_GLOBAL_OR_BASE_SLOT_LOAD: "global_or_base_slot_load",
    TYPE_FLOW_CAUSE_POST_CALL_EXISTING_BASE: "post_call_existing_base",
}

TYPE_FLOW_CAUSE_STOP_REASONS = {
    TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN: "assignment_source_is_address_register_memory_chain",
    TYPE_FLOW_CAUSE_API_OUTPUT_NEARBY: "assignment_source_is_register_after_nearby_os_call",
    TYPE_FLOW_CAUSE_API_OUTPUT_NEARBY_UNKNOWN_OUTPUT: "assignment_source_is_register_after_call_without_output_metadata",
    TYPE_FLOW_CAUSE_POST_CALL_REGISTER_COPY: "assignment_source_is_not_nearest_call_output_register",
    TYPE_FLOW_CAUSE_APP_SLOT_LOAD: "assignment_source_is_app_slot",
    TYPE_FLOW_CAUSE_STACK_SLOT_LOAD: "assignment_source_is_stack_slot",
    TYPE_FLOW_CAUSE_GLOBAL_OR_BASE_SLOT_LOAD: "assignment_source_is_global_or_base_slot",
}

TYPE_FLOW_PROPAGATION_CHAIN_API_OUTPUT = 1
TYPE_FLOW_PROPAGATION_CHAIN_API_UNSTRUCTURED_OUTPUT = 2
TYPE_FLOW_PROPAGATION_CHAIN_API_OUTPUT_COPY = 3
TYPE_FLOW_PROPAGATION_CHAIN_API_UNSTRUCTURED_OUTPUT_COPY = 4
TYPE_FLOW_PROPAGATION_CHAIN_API_CALL_UNKNOWN_OUTPUT = 5
TYPE_FLOW_PROPAGATION_CHAIN_REGISTER = 6

TYPE_FLOW_PROPAGATION_CHAIN_API_OUTPUT_IDS = {
    TYPE_FLOW_PROPAGATION_CHAIN_API_OUTPUT,
    TYPE_FLOW_PROPAGATION_CHAIN_API_OUTPUT_COPY,
}


def _type_flow_numeric_address_base_reg(text: str) -> int | None:
    match = _TYPE_FLOW_NUMERIC_ADDRESS_BASE_RE.search(text)
    if match is None:
        return None
    return int(match.group(1))


def _type_flow_numeric_address_displacement(text: str) -> int | None:
    match = _TYPE_FLOW_NUMERIC_ADDRESS_DISPLACEMENT_RE.search(text)
    if match is None:
        return None
    value = int(match.group(2), 16)
    return -value if match.group(1) == "-" else value


def _type_flow_app_slot_subaccess(trace: dict[str, object]) -> dict[str, object] | None:
    assignment = trace.get("assignment")
    if not isinstance(assignment, dict):
        return None
    app_refs = assignment.get("app_slot_refs")
    text = _string_value(trace.get("text"))
    if text is None:
        return None
    refs = _dict_items(app_refs)
    if not refs:
        return None
    slot_symbol = _string_value(refs[0].get("symbol")) or _app_slot_symbol(refs[0].get("displacement"))
    if slot_symbol is None:
        return None
    displacement = _type_flow_numeric_address_displacement(text)
    if displacement is None:
        return None
    return {
        "slot": slot_symbol,
        "slot_access_displacement": displacement,
        "slot_access_displacement_hex": _signed_hex_string(displacement),
    }


def _type_flow_assignment_source_for_reg(text: str, base_reg: int) -> str | None:
    match = _TYPE_FLOW_ASSIGNMENT_RE.search(text)
    if match is None or match.group(2).upper() != f"A{base_reg}":
        return None
    return match.group(1).strip()


def _type_flow_assignment_source_for_named_reg(text: str, reg_name: str) -> str | None:
    match = _TYPE_FLOW_ASSIGNMENT_RE.search(text)
    if match is None or match.group(2).upper() != reg_name.upper():
        return None
    return match.group(1).strip()


def _type_flow_store_to_memory(text: str) -> tuple[str, str] | None:
    match = _TYPE_FLOW_STORE_RE.search(text)
    if match is None:
        return None
    if match.group(1).lower() != "l":
        return None
    dest_expr = match.group(3).strip()
    if _type_flow_operand_is_register(dest_expr):
        return None
    return match.group(2).upper(), dest_expr


def _type_flow_normalized_operand_expr(text: str) -> str:
    lowered = re.sub(r"\s+", "", text.lower())
    return re.sub(r"\.(?:[bwl])(?=$|\))", "", lowered)


def _type_flow_operand_is_register(text: str) -> bool:
    return _TYPE_FLOW_REGISTER_RE.fullmatch(text.strip()) is not None


def _type_flow_register_name(text: str) -> str | None:
    match = _TYPE_FLOW_REGISTER_RE.fullmatch(text.strip())
    if match is None:
        return None
    return match.group(1).upper()


def _type_flow_address_base_register_name(text: str) -> str | None:
    match = _TYPE_FLOW_ADDRESS_BASE_RE.search(text)
    if match is None:
        return None
    return f"A{match.group(1)}"


def _type_flow_row_is_call_like(row: dict[str, Any]) -> bool:
    text = _string_value(row.get("text")) if isinstance(row, dict) else None
    return text is not None and _TYPE_FLOW_CALL_LIKE_RE.search(text) is not None


def _type_flow_storage_kind(assignment_source: str, assignment_row: dict[str, Any] | None) -> str:
    source_lower = assignment_source.lower()
    app_refs = assignment_row.get("app_slot_refs") if isinstance(assignment_row, dict) else None
    if _dict_items(app_refs):
        return "app_slot"
    if "(a7)" in source_lower or "(sp)" in source_lower:
        return "stack_slot"
    return "global_or_base_slot"


def _type_flow_struct_is_specific(struct_name: object) -> bool:
    struct_text = _string_value(struct_name)
    if struct_text is None:
        return False
    normalized = struct_text.strip().lower()
    return normalized not in {"", "void", "void *", "aptr"}


def _type_flow_register_copy_from_call_output(
    target_id: str,
    source_reg: str,
    store_row_index: int,
    rows_by_index: dict[int, dict[str, Any]],
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
) -> dict[str, object] | None:
    source_reg = source_reg.upper()
    for row_index in range(store_row_index - 1, max(0, store_row_index - 8) - 1, -1):
        row = rows_by_index.get(row_index)
        if not isinstance(row, dict) or not _listing_row_is_kind(row, LISTING_ROW_KIND_INSTRUCTION):
            continue
        row_text = _string_value(row.get("text")) or ""
        if re.search(r"^\s*(?:movea?|lea)\.l\b", row_text, re.IGNORECASE) is None:
            continue
        assigned = _type_flow_assignment_source_for_named_reg(row_text, source_reg)
        if assigned is None:
            continue
        assigned_reg = assigned.upper()
        if not _TYPE_FLOW_REGISTER_RE.fullmatch(assigned_reg):
            return None
        os_call = _type_flow_nearby_os_call(target_id, row_index - 8, row_index, xrefs_by_row, rows_by_index)
        output_regs = os_call.get("output_regs") if os_call is not None else None
        if isinstance(output_regs, list) and assigned_reg in output_regs:
            output_structs = os_call.get("output_structs_by_reg")
            output_struct = output_structs.get(assigned_reg) if isinstance(output_structs, dict) else None
            return {
                "copy_row_index": row_index,
                "copy_stable_key": row.get("stable_key"),
                "copy_text": (_string_value(row.get("text")) or "").strip(),
                "api_output_reg": assigned_reg,
                "api_output_struct": output_struct,
                "os_call": os_call,
            }
        return None
    return None


def _type_flow_storage_reload_chain(
    target_id: str,
    assignment_source: str,
    assignment_row: dict[str, Any] | None,
    assignment_row_index: int,
    rows: list[dict[str, Any]],
    rows_by_index: dict[int, dict[str, Any]],
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
) -> dict[str, object] | None:
    if _type_flow_operand_is_register(assignment_source):
        return None
    storage_key = _type_flow_normalized_operand_expr(assignment_source)
    storage_kind = _type_flow_storage_kind(assignment_source, assignment_row)
    del rows
    for candidate_index in range(assignment_row_index - 1, max(0, assignment_row_index - 48) - 1, -1):
        candidate_row = rows_by_index.get(candidate_index)
        if not isinstance(candidate_row, dict) or not _listing_row_is_kind(candidate_row, LISTING_ROW_KIND_INSTRUCTION):
            continue
        store = _type_flow_store_to_memory(_string_value(candidate_row.get("text")) or "")
        if store is None:
            continue
        source_reg, dest_expr = store
        if _type_flow_normalized_operand_expr(dest_expr) != storage_key:
            continue
        os_call = _type_flow_nearby_os_call(target_id, candidate_index - 8, candidate_index, xrefs_by_row, rows_by_index)
        output_regs = os_call.get("output_regs") if os_call is not None else None
        if isinstance(output_regs, list) and source_reg in output_regs:
            output_structs = os_call.get("output_structs_by_reg")
            output_struct = output_structs.get(source_reg) if isinstance(output_structs, dict) else None
            chain_prefix = "api_output" if _type_flow_struct_is_specific(output_struct) else "api_unstructured_output"
            chain = f"{chain_prefix}_to_{storage_kind}_reload"
            return {
                "kind": chain,
                "kind_id": (
                    TYPE_FLOW_PROPAGATION_CHAIN_API_OUTPUT
                    if chain_prefix == "api_output"
                    else TYPE_FLOW_PROPAGATION_CHAIN_API_UNSTRUCTURED_OUTPUT
                ),
                "storage_kind": storage_kind,
                "storage": assignment_source,
                "store_row_index": candidate_index,
                "store_stable_key": candidate_row.get("stable_key"),
                "store_text": (_string_value(candidate_row.get("text")) or "").strip(),
                "store_source_reg": source_reg,
                "api_output_reg": source_reg,
                "api_output_struct": output_struct,
                "os_call": os_call,
            }
        copied = _type_flow_register_copy_from_call_output(
            target_id, source_reg, candidate_index, rows_by_index, xrefs_by_row
        )
        if copied is not None:
            chain_prefix = (
                "api_output_copy"
                if _type_flow_struct_is_specific(copied.get("api_output_struct"))
                else "api_unstructured_output_copy"
            )
            chain = f"{chain_prefix}_to_{storage_kind}_reload"
            return {
                "kind": chain,
                "kind_id": (
                    TYPE_FLOW_PROPAGATION_CHAIN_API_OUTPUT_COPY
                    if chain_prefix == "api_output_copy"
                    else TYPE_FLOW_PROPAGATION_CHAIN_API_UNSTRUCTURED_OUTPUT_COPY
                ),
                "storage_kind": storage_kind,
                "storage": assignment_source,
                "store_row_index": candidate_index,
                "store_stable_key": candidate_row.get("stable_key"),
                "store_text": (_string_value(candidate_row.get("text")) or "").strip(),
                "store_source_reg": source_reg,
                **copied,
            }
        if os_call is not None:
            chain = f"api_call_to_{storage_kind}_reload_unknown_output"
            return {
                "kind": chain,
                "kind_id": TYPE_FLOW_PROPAGATION_CHAIN_API_CALL_UNKNOWN_OUTPUT,
                "storage_kind": storage_kind,
                "storage": assignment_source,
                "store_row_index": candidate_index,
                "store_stable_key": candidate_row.get("stable_key"),
                "store_text": (_string_value(candidate_row.get("text")) or "").strip(),
                "store_source_reg": source_reg,
                "os_call": os_call,
            }
        return {
            "kind": f"register_to_{storage_kind}_reload",
            "kind_id": TYPE_FLOW_PROPAGATION_CHAIN_REGISTER,
            "storage_kind": storage_kind,
            "storage": assignment_source,
            "store_row_index": candidate_index,
            "store_stable_key": candidate_row.get("stable_key"),
            "store_text": (_string_value(candidate_row.get("text")) or "").strip(),
            "store_source_reg": source_reg,
        }
    return None


def _type_flow_find_assignment_to_reg(
    rows: list[dict[str, Any]],
    *,
    row_index: int,
    reg_name: str,
    rows_by_index: dict[int, dict[str, Any]] | None = None,
    assignment_cache: dict[tuple[int, str, int], tuple[int, dict[str, Any], str] | None] | None = None,
    window: int = 64,
) -> tuple[int, dict[str, Any], str] | None:
    reg_name = reg_name.upper()
    if rows_by_index is not None:
        cache_key = (row_index, reg_name, window)
        if assignment_cache is not None and cache_key in assignment_cache:
            return assignment_cache[cache_key]
        for candidate_index in range(row_index - 1, max(0, row_index - window) - 1, -1):
            candidate_row = rows_by_index.get(candidate_index)
            if (
                not isinstance(candidate_row, dict)
                or not _listing_row_is_kind(candidate_row, LISTING_ROW_KIND_INSTRUCTION)
            ):
                continue
            source = _type_flow_assignment_source_for_named_reg(_string_value(candidate_row.get("text")) or "", reg_name)
            if source is not None:
                result = (candidate_index, candidate_row, source)
                if assignment_cache is not None:
                    assignment_cache[cache_key] = result
                return result
        if assignment_cache is not None:
            assignment_cache[cache_key] = None
        return None
    for candidate in reversed(rows):
        candidate_index = candidate.get("row_index")
        if (
            not isinstance(candidate_index, int)
            or candidate_index >= row_index
            or candidate_index < row_index - window
        ):
            continue
        candidate_row = candidate.get("row")
        if (
            not isinstance(candidate_row, dict)
            or not _listing_row_is_kind(candidate_row, LISTING_ROW_KIND_INSTRUCTION)
        ):
            continue
        source = _type_flow_assignment_source_for_named_reg(_string_value(candidate_row.get("text")) or "", reg_name)
        if source is None:
            continue
        return candidate_index, candidate_row, source
    return None


def _type_flow_pointer_chain_source_kind(
    assignment_source: str,
    assignment_row: dict[str, Any] | None,
    target_id: str,
    assignment_row_index: int,
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    rows_by_index: dict[int, dict[str, Any]],
) -> str:
    source_lower = assignment_source.lower()
    source_reg = _type_flow_register_name(assignment_source)
    app_refs = assignment_row.get("app_slot_refs") if isinstance(assignment_row, dict) else None
    if _dict_items(app_refs):
        return "app_slot"
    if "(a7)" in source_lower or "(sp)" in source_lower:
        return "stack_slot"
    if source_reg is not None:
        os_call = _type_flow_nearby_os_call(
            target_id, assignment_row_index - 8, assignment_row_index, xrefs_by_row, rows_by_index
        )
        output_regs = os_call.get("output_regs") if os_call is not None else None
        if isinstance(output_regs, list) and source_reg in output_regs:
            return "api_output_register"
        return "register"
    if _TYPE_FLOW_ADDRESS_EXPR_RE.search(assignment_source):
        return "memory_indirect"
    if source_lower.startswith("#"):
        return "immediate"
    if source_lower.startswith("$") or _TYPE_FLOW_GLOBAL_OR_BASE_RE.search(source_lower):
        return "global_or_base_slot"
    return "unknown"


def _type_flow_pointer_chain_trace(
    target_id: str,
    base_reg: int,
    row_index: int,
    rows: list[dict[str, Any]],
    rows_by_index: dict[int, dict[str, Any]],
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    *,
    assignment_cache: dict[tuple[int, str, int], tuple[int, dict[str, Any], str] | None] | None = None,
    max_hops: int = 6,
) -> dict[str, object]:
    cursor_reg = f"A{base_reg}"
    cursor_row_index = row_index
    hops: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    root_kind = "unknown"
    stop_reason = "max_depth"
    for _depth in range(max_hops):
        key = (cursor_reg, cursor_row_index)
        if key in seen:
            stop_reason = "cycle"
            break
        seen.add(key)
        assignment = _type_flow_find_assignment_to_reg(
            rows,
            row_index=cursor_row_index,
            reg_name=cursor_reg,
            rows_by_index=rows_by_index,
            assignment_cache=assignment_cache,
        )
        if assignment is None:
            root_kind = "unknown"
            stop_reason = "no_assignment_to_chain_base"
            break
        assignment_row_index, assignment_row, assignment_source = assignment
        source_kind = _type_flow_pointer_chain_source_kind(
            assignment_source,
            assignment_row,
            target_id,
            assignment_row_index,
            xrefs_by_row,
            rows_by_index,
        )
        hop: dict[str, object] = {
            "row_index": assignment_row_index,
            "stable_key": assignment_row.get("stable_key"),
            "dest": cursor_reg,
            "source": assignment_source,
            "source_kind": source_kind,
            "text": (_string_value(assignment_row.get("text")) or "").strip(),
        }
        storage_chain = _type_flow_storage_reload_chain(
            target_id, assignment_source, assignment_row, assignment_row_index, rows, rows_by_index, xrefs_by_row
        )
        if storage_chain is not None:
            hop["propagation_chain"] = storage_chain
        os_call = _type_flow_nearby_os_call(target_id, assignment_row_index - 8, assignment_row_index,
            xrefs_by_row, rows_by_index)
        if os_call is not None:
            hop["nearest_os_call"] = os_call
        hops.append(hop)
        if source_kind == "register":
            source_reg = _type_flow_register_name(assignment_source)
            if source_reg is not None and source_reg.startswith("A"):
                cursor_reg = source_reg
                cursor_row_index = assignment_row_index
                continue
            root_kind = source_kind
            stop_reason = "register_source"
            break
        if source_kind == "memory_indirect":
            next_reg = _type_flow_address_base_register_name(assignment_source)
            if next_reg is not None and next_reg != "A7":
                cursor_reg = next_reg
                cursor_row_index = assignment_row_index
                continue
            root_kind = source_kind
            stop_reason = "memory_indirect_without_address_base"
            break
        root_kind = source_kind
        stop_reason = f"source_is_{source_kind}"
        break
    return {
        "base_register": f"A{base_reg}",
        "depth": len(hops),
        "hops": hops,
        "root_kind": root_kind,
        "stop_reason": stop_reason,
    }


def _type_flow_rows_for_target(snippet_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows_by_target: dict[str, list[dict[str, Any]]] = {}
    for snippet in snippet_rows:
        target_id = _string_value(snippet.get("target_id"))
        if target_id is None:
            continue
        rows_by_target.setdefault(target_id, []).append(snippet)
    for rows in rows_by_target.values():
        rows.sort(key=lambda item: int(item.get("row_index", -1)) if isinstance(item.get("row_index"), int) else -1)
    return rows_by_target


def _type_flow_xrefs_by_target_row(xrefs: list[dict[str, Any]]) -> dict[tuple[str, int], list[dict[str, Any]]]:
    by_row: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for xref in xrefs:
        target_id = _string_value(xref.get("target_id"))
        row_index = xref.get("row_index")
        if target_id is None or not isinstance(row_index, int):
            continue
        by_row.setdefault((target_id, row_index), []).append(xref)
    return by_row


def _type_flow_rows_by_index(rows_by_target: dict[str, list[dict[str, Any]]], target_id: str) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for snippet in rows_by_target.get(target_id, []):
        row_index = snippet.get("row_index")
        row = snippet.get("row")
        if isinstance(row_index, int) and isinstance(row, dict):
            result[row_index] = row
    return result


def _type_flow_nearby_os_call(
    target_id: str,
    start_row: int,
    end_row: int,
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    rows_by_index: dict[int, dict[str, Any]],
) -> dict[str, object] | None:
    for row_index in range(end_row, max(0, start_row) - 1, -1):
        row_xrefs = xrefs_by_row.get((target_id, row_index), [])
        for xref in row_xrefs:
            if _xref_kind_id(xref) == XREF_KIND_OS_CALL:
                row = rows_by_index.get(row_index, {})
                output_regs = sorted(
                    {
                        str(output.get("value")).upper()
                        for output in row_xrefs
                        if _xref_kind_id(output) == XREF_KIND_OS_CALL_OUTPUT
                        and _string_value(output.get("value"))
                    }
                )
                output_structs_by_reg = {
                    str(output.get("access")).upper(): str(output.get("value"))
                    for output in row_xrefs
                    if _xref_kind_id(output) == XREF_KIND_OS_CALL_OUTPUT_STRUCT
                    and _string_value(output.get("access"))
                    and _string_value(output.get("value"))
                }
                return {
                    "row_index": row_index,
                    "feature": xref.get("feature"),
                    "stable_key": xref.get("stable_key") or row.get("stable_key"),
                    "resolution": xref.get("resolution"),
                    "text": _string_value(xref.get("text")) or (_string_value(row.get("text")) or "").strip(),
                    "output_regs": output_regs,
                    "output_structs_by_reg": output_structs_by_reg,
                    "structured_output_regs": sorted(
                        reg for reg, struct in output_structs_by_reg.items() if _type_flow_struct_is_specific(struct)
                    ),
                }
        row = rows_by_index.get(row_index)
        if isinstance(row, dict) and _type_flow_row_is_call_like(row):
            return None
    return None


def _type_flow_nearby_has_os_call(
    target_id: str,
    start_row: int,
    end_row: int,
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    rows_by_index: dict[int, dict[str, Any]] | None = None,
) -> bool:
    return _type_flow_nearby_os_call(target_id, start_row, end_row, xrefs_by_row, rows_by_index or {}) is not None


def _type_flow_numeric_access_cause(
    target_id: str,
    snippet: dict[str, Any],
    rows_by_target: dict[str, list[dict[str, Any]]],
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
) -> str:
    return str(
        _type_flow_numeric_access_trace(target_id, snippet, rows_by_target, xrefs_by_row).get(
            "cause", "unknown_pointer_chain"
        )
    )


def _type_flow_numeric_source_kind(
    assignment_source: str,
    assignment_row: dict[str, Any] | None,
    target_id: str,
    assignment_row_index: int,
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    rows_by_index: dict[int, dict[str, Any]],
) -> str:
    return TYPE_FLOW_CAUSE_NAMES[
        _type_flow_numeric_source_kind_id(
            assignment_source, assignment_row, target_id, assignment_row_index, xrefs_by_row, rows_by_index
        )
    ]


def _type_flow_numeric_source_kind_id(
    assignment_source: str,
    assignment_row: dict[str, Any] | None,
    target_id: str,
    assignment_row_index: int,
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    rows_by_index: dict[int, dict[str, Any]],
) -> int:
    source_lower = assignment_source.lower()
    app_refs = assignment_row.get("app_slot_refs") if isinstance(assignment_row, dict) else None
    if _dict_items(app_refs):
        return TYPE_FLOW_CAUSE_APP_SLOT_LOAD
    if "(a7)" in source_lower or "(sp)" in source_lower:
        return TYPE_FLOW_CAUSE_STACK_SLOT_LOAD
    if _TYPE_FLOW_REGISTER_RE.fullmatch(source_lower):
        os_call = _type_flow_nearby_os_call(
            target_id, assignment_row_index - 8, assignment_row_index, xrefs_by_row, rows_by_index
        )
        if os_call is not None:
            output_regs = os_call.get("output_regs")
            if isinstance(output_regs, list) and source_lower.upper() in output_regs:
                return TYPE_FLOW_CAUSE_API_OUTPUT_NEARBY
            if isinstance(output_regs, list) and output_regs:
                return TYPE_FLOW_CAUSE_POST_CALL_REGISTER_COPY
            return TYPE_FLOW_CAUSE_API_OUTPUT_NEARBY_UNKNOWN_OUTPUT
    if _TYPE_FLOW_ADDRESS_EXPR_RE.search(assignment_source):
        return TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN
    if source_lower.startswith("$") or _TYPE_FLOW_GLOBAL_OR_BASE_RE.search(source_lower):
        return TYPE_FLOW_CAUSE_GLOBAL_OR_BASE_SLOT_LOAD
    return TYPE_FLOW_CAUSE_GLOBAL_OR_BASE_SLOT_LOAD


def _type_flow_numeric_access_trace(
    target_id: str,
    snippet: dict[str, Any],
    rows_by_target: dict[str, list[dict[str, Any]]],
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    rows_by_index_by_target: dict[str, dict[int, dict[str, Any]]] | None = None,
    assignment_cache_by_target: dict[
        str,
        dict[tuple[int, str, int], tuple[int, dict[str, Any], str] | None],
    ] | None = None,
) -> dict[str, object]:
    row = snippet.get("row")
    text = _string_value(row.get("text")) if isinstance(row, dict) else None
    row_index = snippet.get("row_index")
    trace: dict[str, object] = {}
    if text is None or not isinstance(row_index, int):
        trace["cause_id"] = TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN
        trace["cause"] = TYPE_FLOW_CAUSE_NAMES[TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN]
        trace["stop_reason"] = "missing_instruction_text"
        return trace
    base_reg = _type_flow_numeric_address_base_reg(text)
    trace["row_index"] = row_index
    trace["text"] = text.strip()
    if base_reg is None:
        trace["cause_id"] = TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN
        trace["cause"] = TYPE_FLOW_CAUSE_NAMES[TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN]
        trace["stop_reason"] = "no_numeric_address_base"
        return trace
    trace["base_register"] = f"A{base_reg}"
    if base_reg == 7:
        trace["cause_id"] = TYPE_FLOW_CAUSE_STACK_SLOT_LOAD
        trace["cause"] = TYPE_FLOW_CAUSE_NAMES[TYPE_FLOW_CAUSE_STACK_SLOT_LOAD]
        trace["stop_reason"] = "stack_pointer_base"
        return trace
    rows = rows_by_target.get(target_id, [])
    rows_by_index = (
        rows_by_index_by_target.get(target_id, {})
        if rows_by_index_by_target is not None
        else _type_flow_rows_by_index(rows_by_target, target_id)
    )
    assignment_cache = (
        assignment_cache_by_target.setdefault(target_id, {})
        if assignment_cache_by_target is not None
        else None
    )
    pointer_chain = _type_flow_pointer_chain_trace(
        target_id,
        base_reg,
        row_index,
        rows,
        rows_by_index,
        xrefs_by_row,
        assignment_cache=assignment_cache,
    )
    trace["pointer_chain"] = pointer_chain
    assignment_source: str | None = None
    assignment_row_index = row_index
    assignment_row: dict[str, Any] | None = None
    assignment = _type_flow_find_assignment_to_reg(
        rows,
        row_index=row_index,
        reg_name=f"A{base_reg}",
        rows_by_index=rows_by_index,
        assignment_cache=assignment_cache,
        window=16,
    )
    if assignment is not None:
        assignment_row_index, assignment_row, assignment_source = assignment
    if assignment_source is None:
        os_call = _type_flow_nearby_os_call(target_id, row_index - 8, row_index, xrefs_by_row, rows_by_index)
        if os_call is not None:
            trace["cause_id"] = TYPE_FLOW_CAUSE_POST_CALL_EXISTING_BASE
            trace["cause"] = TYPE_FLOW_CAUSE_NAMES[TYPE_FLOW_CAUSE_POST_CALL_EXISTING_BASE]
            trace["nearest_os_call"] = os_call
            trace["stop_reason"] = "existing_base_access_after_nearby_os_call"
            trace["pointer_chain"] = pointer_chain
            return trace
        trace["cause_id"] = TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN
        trace["cause"] = TYPE_FLOW_CAUSE_NAMES[TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN]
        trace["stop_reason"] = "no_assignment_to_base_register"
        trace["pointer_chain"] = pointer_chain
        return trace
    cause_id = _type_flow_numeric_source_kind_id(
        assignment_source, assignment_row, target_id, assignment_row_index, xrefs_by_row, rows_by_index
    )
    cause = TYPE_FLOW_CAUSE_NAMES[cause_id]
    storage_chain = _type_flow_storage_reload_chain(
        target_id, assignment_source, assignment_row, assignment_row_index, rows, rows_by_index, xrefs_by_row
    )
    trace["cause_id"] = cause_id
    trace["cause"] = cause
    trace["assignment"] = {
        "row_index": assignment_row_index,
        "stable_key": assignment_row.get("stable_key") if isinstance(assignment_row, dict) else None,
        "source": assignment_source,
        "text": (_string_value(assignment_row.get("text")) or "").strip() if isinstance(assignment_row, dict) else None,
        "app_slot_refs": assignment_row.get("app_slot_refs") if isinstance(assignment_row, dict) else None,
    }
    if storage_chain is not None:
        trace["propagation_chain"] = storage_chain
    os_call = _type_flow_nearby_os_call(target_id, assignment_row_index - 8, assignment_row_index, xrefs_by_row, rows_by_index)
    if os_call is not None:
        trace["nearest_os_call"] = os_call
    trace["stop_reason"] = TYPE_FLOW_CAUSE_STOP_REASONS.get(
        cause_id, "assignment_source_is_global_or_base_slot"
    )
    return trace


def _signed_hex_string(value: int) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):04X}"


@functools.lru_cache(maxsize=1)
def _ndk_structs() -> dict[str, Any]:
    path = ROOT / "knowledge" / "amiga_ndk_includes_parsed.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return {}
    structs = payload.get("structs")
    return structs if isinstance(structs, dict) else {}


def _struct_chain_contains(structs: dict[str, Any], struct_name: str, base_name: str) -> bool:
    current = struct_name
    seen: set[str] = set()
    while current and current not in seen:
        seen.add(current)
        info = structs.get(current)
        if not isinstance(info, dict):
            return False
        parent = _string_value(info.get("base_struct"))
        if parent == base_name:
            return True
        if parent is None:
            return False
        current = parent
    return False


def _struct_field_match_at(structs: dict[str, Any], struct_name: str, displacement: int) -> dict[str, object] | None:
    info = structs.get(struct_name)
    if not isinstance(info, dict):
        return None
    for field in _dict_items(info.get("fields")):
        if field.get("type") == "LABEL":
            continue
        field_name = _string_value(field.get("name"))
        offset = _int_value(field.get("offset"))
        size = _int_value(field.get("size"), 0) or 0
        if field_name is None or offset is None:
            continue
        end = offset + max(size, 1)
        if not offset <= displacement < end:
            continue
        nested_struct = _string_value(field.get("struct"))
        if nested_struct and displacement != offset:
            nested = _struct_field_match_at(structs, nested_struct, displacement - offset)
            if nested:
                nested_offset = _int_value(nested.get("field_offset"), 0) or 0
                result = dict(nested)
                result["field_expr"] = f"{field_name}+{nested.get('field_expr')}"
                result["field_offset"] = offset + nested_offset
                result["field_start_delta"] = displacement - (offset + nested_offset)
                result["nested"] = True
                return result
        delta = displacement - offset
        expr = field_name if delta == 0 else f"{field_name}+{delta}"
        return {
            "field_expr": expr,
            "field_offset": offset,
            "field_size": size,
            "field_start_delta": delta,
            "exact_field_start": delta == 0,
        }
    base_name = _string_value(info.get("base_struct"))
    base_size = _int_value(info.get("base_offset"))
    if base_name is not None and base_size is not None and displacement < base_size:
        return _struct_field_match_at(structs, base_name, displacement)
    return None


def _struct_field_expr_at(structs: dict[str, Any], struct_name: str, displacement: int) -> str | None:
    match = _struct_field_match_at(structs, struct_name, displacement)
    if match is None:
        return None
    return _string_value(match.get("field_expr"))


def _instruction_access_size_from_text(text: object) -> int | None:
    value = _string_value(text)
    if value is None:
        return None
    match = re.search(r"^\s*[a-z][a-z0-9]*\.(?P<size>[bwl])\b", value, flags=re.IGNORECASE)
    if match is None:
        return None
    return {"b": 1, "w": 2, "l": 4}.get(match.group("size").casefold())


def _access_size_counts_from_group(group: dict[str, Any]) -> dict[int, int]:
    raw = group.get("access_size_counts")
    if not isinstance(raw, dict):
        return {}
    result: dict[int, int] = {}
    for key, value in raw.items():
        size = key if isinstance(key, int) else None
        if size is None and isinstance(key, str):
            try:
                size = int(key, 10)
            except ValueError:
                size = None
        if isinstance(size, int) and isinstance(value, int) and size > 0 and value > 0:
            result[size] = result.get(size, 0) + value
    return result


def _rank_prefix_extension_candidate(candidate: dict[str, object], access_size_counts: dict[int, int]) -> None:
    score = int(candidate.get("target_context_score", 0)) * 3
    reasons: list[str] = []
    field_start_delta = _int_value(candidate.get("field_start_delta"))
    field_size = _int_value(candidate.get("field_size"))
    exact_count = 0
    partial_count = 0
    if int(candidate.get("target_context_score", 0)) > 0:
        reasons.append("struct appears elsewhere in target context")
    for access_size, count in sorted(access_size_counts.items()):
        if field_start_delta != 0:
            continue
        if field_size == access_size:
            exact_count += count
            score += 20 * count
        elif field_size is not None and field_size > access_size:
            partial_count += count
            score += 2 * count
    if exact_count:
        reasons.append("field starts at displacement and matches access size")
    elif partial_count:
        reasons.append("field starts at displacement and contains access size")
    candidate["access_size_score"] = (exact_count * 20) + (partial_count * 2)
    candidate["exact_access_size_match_count"] = exact_count
    candidate["candidate_rank_score"] = score
    if reasons:
        candidate["ranking_reasons"] = reasons


def _dominant_prefix_candidate(candidates: list[dict[str, object]]) -> dict[str, object] | None:
    if not candidates:
        return None
    top_score = int(candidates[0].get("candidate_rank_score", 0))
    if top_score <= 0:
        return None
    second_score = int(candidates[1].get("candidate_rank_score", 0)) if len(candidates) > 1 else -1
    if top_score <= second_score:
        return None
    top_exact_matches = int(candidates[0].get("exact_access_size_match_count", 0))
    if len(candidates) > 1 and top_exact_matches <= 0:
        return None
    if len(candidates) > 1:
        second_exact_matches = max(
            int(candidate.get("exact_access_size_match_count", 0)) for candidate in candidates[1:]
        )
        if top_exact_matches <= second_exact_matches:
            return None
    return candidates[0]


def _serialise_access_size_counts(access_size_counts: dict[int, int]) -> dict[str, int]:
    return {str(size): access_size_counts[size] for size in sorted(access_size_counts)}


def _attach_custom_tail_cluster_summaries(rows: list[dict[str, object]]) -> None:
    clusters: dict[str, dict[str, Any]] = {}
    for row in rows:
        if _int_value(row.get("classification_id")) != UNRESOLVED_TYPED_FIELD_REPORT_CUSTOM_TAIL_OR_MISTYPED_BASE:
            continue
        root_struct = _string_value(row.get("root_struct_name")) or "unknown"
        displacement = _int_value(row.get("displacement"))
        tail_offset = _int_value(row.get("tail_offset_from_struct_end"))
        count = _int_value(row.get("count"), 0) or 0
        cluster = clusters.setdefault(
            root_struct,
            {
                "root_struct_name": root_struct,
                "group_count": 0,
                "xref_count": 0,
                "target_ids": set(),
                "displacements": {},
                "displacement_values": [],
                "tail_offsets": {},
                "tail_offset_values": [],
                "nearby_api_features": {},
            },
        )
        cluster["group_count"] = int(cluster["group_count"]) + 1
        cluster["xref_count"] = int(cluster["xref_count"]) + count
        target_ids = cluster.get("target_ids")
        if isinstance(target_ids, set):
            for target_id in row.get("target_ids", []):
                target_ids.add(str(target_id))
        if displacement is not None:
            values = cluster.get("displacement_values")
            if isinstance(values, list):
                values.append(displacement)
            hist = cluster["displacements"]
            if isinstance(hist, dict):
                key = _signed_hex_string(displacement)
                hist[key] = int(hist.get(key, 0)) + count
        if tail_offset is not None:
            values = cluster.get("tail_offset_values")
            if isinstance(values, list):
                values.append(tail_offset)
            hist = cluster["tail_offsets"]
            if isinstance(hist, dict):
                key = _signed_hex_string(tail_offset)
                hist[key] = int(hist.get(key, 0)) + count
        nearby_api_feature = _string_value(row.get("nearby_api_feature")) or "none"
        nearby = cluster["nearby_api_features"]
        if isinstance(nearby, dict):
            nearby[nearby_api_feature] = int(nearby.get(nearby_api_feature, 0)) + count
    summaries: dict[str, dict[str, object]] = {}
    for root_struct, cluster in clusters.items():
        target_ids = cluster.get("target_ids")
        sorted_targets = sorted(target_ids) if isinstance(target_ids, set) else []
        displacement_values = [
            value for value in cluster.get("displacement_values", []) if isinstance(value, int)
        ]
        tail_offset_values = [
            value for value in cluster.get("tail_offset_values", []) if isinstance(value, int)
        ]
        summary = {
            "root_struct_name": root_struct,
            "group_count": int(cluster.get("group_count", 0)),
            "xref_count": int(cluster.get("xref_count", 0)),
            "target_count": len(sorted_targets),
            "target_ids": sorted_targets[:MAX_EXAMPLES],
            "displacement_histogram": dict(sorted(cluster.get("displacements", {}).items())),
            "tail_offset_histogram": dict(sorted(cluster.get("tail_offsets", {}).items())),
            "nearby_api_feature_counts": dict(sorted(cluster.get("nearby_api_features", {}).items())),
        }
        if displacement_values:
            summary["displacement_min"] = min(displacement_values)
            summary["displacement_max"] = max(displacement_values)
            summary["displacement_min_hex"] = _signed_hex_string(min(displacement_values))
            summary["displacement_max_hex"] = _signed_hex_string(max(displacement_values))
        if tail_offset_values:
            summary["tail_offset_min"] = min(tail_offset_values)
            summary["tail_offset_max"] = max(tail_offset_values)
            summary["tail_offset_min_hex"] = _signed_hex_string(min(tail_offset_values))
            summary["tail_offset_max_hex"] = _signed_hex_string(max(tail_offset_values))
        summaries[root_struct] = summary
    for row in rows:
        if _int_value(row.get("classification_id")) != UNRESOLVED_TYPED_FIELD_REPORT_CUSTOM_TAIL_OR_MISTYPED_BASE:
            continue
        root_struct = _string_value(row.get("root_struct_name")) or "unknown"
        if root_struct in summaries:
            row["tail_cluster_summary"] = summaries[root_struct]


def _prefix_extension_candidates(root_struct: str, displacement: int) -> list[dict[str, object]]:
    structs = _ndk_structs()
    candidates: list[dict[str, object]] = []
    for struct_name, info in structs.items():
        if not isinstance(struct_name, str) or not isinstance(info, dict) or struct_name == root_struct:
            continue
        size = _int_value(info.get("size"))
        if size is None or displacement >= size:
            continue
        if not _struct_chain_contains(structs, struct_name, root_struct):
            continue
        candidate: dict[str, object] = {"struct_name": struct_name, "size": size}
        field_match = _struct_field_match_at(structs, struct_name, displacement)
        if field_match:
            candidate.update(field_match)
        candidates.append(candidate)
    return sorted(candidates, key=lambda item: (str(item.get("struct_name")), str(item.get("field_expr"))))


def _unresolved_typed_field_text_is_control_transfer(text: object) -> bool:
    value = _string_value(text)
    if value is None:
        return False
    stripped = value.strip().lower()
    return stripped.startswith("jsr ") or stripped.startswith("jmp ")


def _unresolved_typed_field_report_classification_name(classification_id: int) -> str:
    return UNRESOLVED_TYPED_FIELD_REPORT_NAMES.get(classification_id, "unknown_struct_field")


def _classify_unresolved_typed_field_group(group: dict[str, Any]) -> tuple[int, str, str]:
    examples = group.get("examples")
    displacement = _int_value(group.get("displacement"))
    struct_size = _int_value(group.get("struct_size"))
    source_classification_id = _int_value(group.get("source_classification_id"))
    if isinstance(examples, list) and any(
        isinstance(example, dict) and _unresolved_typed_field_text_is_control_transfer(example.get("text"))
        for example in examples
    ):
        return (
            UNRESOLVED_TYPED_FIELD_REPORT_CONTROL_TRANSFER,
            _unresolved_typed_field_report_classification_name(
                UNRESOLVED_TYPED_FIELD_REPORT_CONTROL_TRANSFER
            ),
            "example operand is a control-transfer target, not a data field access",
        )
    if source_classification_id == UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION:
        return (
            UNRESOLVED_TYPED_FIELD_REPORT_PREFIX_EXTENSION,
            _unresolved_typed_field_report_classification_name(UNRESOLVED_TYPED_FIELD_REPORT_PREFIX_EXTENSION),
            "displacement is outside the prefix type and inside one or more generated container types",
        )
    if source_classification_id == UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE:
        return (
            UNRESOLVED_TYPED_FIELD_REPORT_CUSTOM_TAIL_OR_MISTYPED_BASE,
            _unresolved_typed_field_report_classification_name(
                UNRESOLVED_TYPED_FIELD_REPORT_CUSTOM_TAIL_OR_MISTYPED_BASE
            ),
            "displacement is outside the known structure and no generated container type matched",
        )
    if source_classification_id == UNRESOLVED_TYPED_ACCESS_FIELD_GAP:
        return (
            UNRESOLVED_TYPED_FIELD_REPORT_FIELD_GAP,
            _unresolved_typed_field_report_classification_name(UNRESOLVED_TYPED_FIELD_REPORT_FIELD_GAP),
            "field metadata did not resolve inside the known structure bounds",
        )
    if displacement is not None and struct_size is not None and not 0 <= displacement < struct_size:
        return (
            UNRESOLVED_TYPED_FIELD_REPORT_OUT_OF_STRUCT_BOUNDS,
            _unresolved_typed_field_report_classification_name(UNRESOLVED_TYPED_FIELD_REPORT_OUT_OF_STRUCT_BOUNDS),
            "displacement is outside the known structure size",
        )
    if group.get("nearby_api_feature") is not None:
        return (
            UNRESOLVED_TYPED_FIELD_REPORT_NEARBY_API_UNKNOWN_FIELD,
            _unresolved_typed_field_report_classification_name(
                UNRESOLVED_TYPED_FIELD_REPORT_NEARBY_API_UNKNOWN_FIELD
            ),
            "field access is near a platform API call but the field metadata did not resolve",
        )
    return (
        UNRESOLVED_TYPED_FIELD_REPORT_UNKNOWN_STRUCT_FIELD,
        _unresolved_typed_field_report_classification_name(UNRESOLVED_TYPED_FIELD_REPORT_UNKNOWN_STRUCT_FIELD),
        "field metadata did not resolve for this typed base access",
    )


def build_unresolved_typed_field_report(
    manifest_rows: list[dict[str, Any]],
    xrefs: list[dict[str, Any]],
    snippet_rows: list[dict[str, Any]],
) -> list[dict[str, object]]:
    manifest_by_id = {
        str(row.get("id")): row
        for row in manifest_rows
        if isinstance(row.get("id"), str)
    }
    rows_by_target = _type_flow_rows_for_target(snippet_rows)
    xrefs_by_row = _type_flow_xrefs_by_target_row(xrefs)
    struct_features_by_target: dict[str, set[str]] = {}
    for xref in xrefs:
        target_id = _string_value(xref.get("target_id"))
        feature_class_id = _xref_feature_class_id(xref)
        feature_value = _xref_feature_value(xref)
        if target_id is None or feature_value is None:
            continue
        if feature_class_id in {XREF_FEATURE_CLASS_STRUCT, XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_STRUCT}:
            struct_features_by_target.setdefault(target_id, set()).add(feature_value)
    rows_by_index_cache: dict[str, dict[int, dict[str, Any]]] = {}
    groups: dict[tuple[str, int, str], dict[str, Any]] = {}

    for xref in xrefs:
        if (
            _xref_kind_id(xref) != XREF_KIND_PLATFORM_UNRESOLVED_TYPED_ACCESS
            or _xref_feature_id(xref) != XREF_FEATURE_TYPED_BASE_UNRESOLVED_FIELD
        ):
            continue
        target_id = _string_value(xref.get("target_id"))
        displacement = _int_value(xref.get("value"))
        if target_id is None or displacement is None:
            continue
        root_struct = _string_value(xref.get("symbol")) or "unknown"
        struct_size = _int_value(xref.get("struct_size"))
        source_classification_id = _int_value(xref.get("classification_id"))
        source_classification = _string_value(xref.get("classification"))
        container_candidate_count = _int_value(xref.get("container_candidate_count"))
        container_struct_name = _string_value(xref.get("container_struct_name"))
        container_field_expr = _string_value(xref.get("container_field_expr"))
        refinement_applied = xref.get("refinement_applied") is True or xref.get("refinement_applied") == 1
        refined_struct_name = _string_value(xref.get("refined_struct_name"))
        row_index = _int_value(xref.get("row_index"))
        rows_by_index = rows_by_index_cache.setdefault(
            target_id,
            _type_flow_rows_by_index(rows_by_target, target_id),
        )
        row = rows_by_index.get(row_index, {}) if row_index is not None else {}
        row_text = (_string_value(xref.get("text")) or _string_value(row.get("text")) or "").strip()
        access_size = _instruction_access_size_from_text(row_text)
        nearby_api = (
            _type_flow_nearby_os_call(target_id, row_index - 8, row_index, xrefs_by_row, rows_by_index)
            if row_index is not None
            else None
        )
        nearby_feature = _string_value(nearby_api.get("feature")) if isinstance(nearby_api, dict) else None
        nearby_key = nearby_feature or "none"
        key = (root_struct, displacement, nearby_key)
        group = groups.get(key)
        if group is None:
            group = {
                "schema_version": 1,
                "root_struct_name": root_struct,
                "displacement": displacement,
                "displacement_hex": _signed_hex_string(displacement),
                "struct_size": struct_size,
                "in_struct_bounds": None if struct_size is None else 0 <= displacement < struct_size,
                "nearby_api_feature": nearby_feature,
                "source_classification_id": source_classification_id,
                "source_classification": source_classification,
                "container_candidate_count": container_candidate_count,
                "container_struct_name": container_struct_name,
                "container_field_expr": container_field_expr,
                "refinement_applied_count": 0,
                "refined_struct_name": refined_struct_name,
                "access_size_counts": {},
                "count": 0,
                "target_ids": set(),
                "examples": [],
            }
            groups[key] = group
        if group.get("struct_size") is None and struct_size is not None:
            group["struct_size"] = struct_size
            group["in_struct_bounds"] = 0 <= displacement < struct_size
        if source_classification_id is not None:
            existing_classification_id = _int_value(group.get("source_classification_id"))
            if existing_classification_id is None:
                group["source_classification_id"] = source_classification_id
                group["source_classification"] = source_classification
            elif existing_classification_id != source_classification_id:
                group["source_classification_id"] = None
                group["source_classification"] = "mixed"
        if container_candidate_count is not None:
            existing_count = _int_value(group.get("container_candidate_count"))
            if existing_count is None or container_candidate_count > existing_count:
                group["container_candidate_count"] = container_candidate_count
        if container_struct_name:
            existing_container = _string_value(group.get("container_struct_name"))
            if existing_container is None:
                group["container_struct_name"] = container_struct_name
            elif existing_container != container_struct_name:
                group["container_struct_name"] = None
        if container_field_expr:
            existing_expr = _string_value(group.get("container_field_expr"))
            if existing_expr is None:
                group["container_field_expr"] = container_field_expr
            elif existing_expr != container_field_expr:
                group["container_field_expr"] = None
        if refinement_applied:
            group["refinement_applied_count"] = int(group.get("refinement_applied_count", 0)) + 1
        if refined_struct_name:
            existing_refined = _string_value(group.get("refined_struct_name"))
            if existing_refined is None:
                group["refined_struct_name"] = refined_struct_name
            elif existing_refined != refined_struct_name:
                group["refined_struct_name"] = None
        group["count"] = int(group.get("count", 0)) + 1
        if access_size is not None:
            access_size_counts = group.get("access_size_counts")
            if isinstance(access_size_counts, dict):
                access_size_counts[access_size] = int(access_size_counts.get(access_size, 0)) + 1
        cast_target_ids = group["target_ids"]
        if isinstance(cast_target_ids, set):
            cast_target_ids.add(target_id)
        examples = group["examples"]
        if isinstance(examples, list) and len(examples) < MAX_EXAMPLES:
            manifest = manifest_by_id.get(target_id, {})
            example: dict[str, object] = {
                "target_id": target_id,
                "source_id": xref.get("source_id") or manifest.get("source_id"),
                "platform": xref.get("platform") or manifest.get("platform"),
                "section": xref.get("section"),
                "offset": xref.get("offset"),
                "row_index": row_index,
                "stable_key": xref.get("stable_key") or row.get("stable_key"),
                "text": row_text,
            }
            if isinstance(nearby_api, dict):
                example["nearby_api"] = nearby_api
            if source_classification:
                example["classification_id"] = source_classification_id
                example["classification"] = source_classification
            if container_candidate_count is not None:
                example["container_candidate_count"] = container_candidate_count
            if container_struct_name:
                example["container_struct_name"] = container_struct_name
            if container_field_expr:
                example["container_field_expr"] = container_field_expr
            if refinement_applied:
                example["refinement_applied"] = True
            if refined_struct_name:
                example["refined_struct_name"] = refined_struct_name
            type_provenance_kind_id = _int_value(xref.get("type_provenance_kind_id"))
            type_provenance_kind = _typed_access_provenance_name(type_provenance_kind_id)
            if type_provenance_kind_id is not None:
                example["type_provenance_kind_id"] = type_provenance_kind_id
                example["type_provenance_kind"] = type_provenance_kind
                type_provenance_offset = _int_value(xref.get("type_provenance_offset"))
                if type_provenance_offset is not None:
                    example["type_provenance_offset"] = type_provenance_offset
            examples.append(_compact_example(example))

    result: list[dict[str, object]] = []
    for group in groups.values():
        target_ids = group.get("target_ids")
        sorted_targets = sorted(str(target_id) for target_id in target_ids) if isinstance(target_ids, set) else []
        classification_id, classification, classification_reason = _classify_unresolved_typed_field_group(group)
        group["classification_id"] = classification_id
        group["classification"] = classification
        group["classification_reason"] = classification_reason
        access_size_counts = _access_size_counts_from_group(group)
        if access_size_counts:
            group["access_size_counts"] = _serialise_access_size_counts(access_size_counts)
        if classification_id == UNRESOLVED_TYPED_FIELD_REPORT_CUSTOM_TAIL_OR_MISTYPED_BASE:
            displacement = _int_value(group.get("displacement"))
            struct_size = _int_value(group.get("struct_size"))
            if displacement is not None and struct_size is not None:
                tail_offset = displacement - struct_size
                group["tail_offset_from_struct_end"] = tail_offset
                group["tail_offset_from_struct_end_hex"] = _signed_hex_string(tail_offset)
        if classification_id == UNRESOLVED_TYPED_FIELD_REPORT_PREFIX_EXTENSION:
            root_struct = _string_value(group.get("root_struct_name"))
            displacement = _int_value(group.get("displacement"))
            if root_struct is not None and displacement is not None:
                candidates = _prefix_extension_candidates(root_struct, displacement)
                for candidate in candidates:
                    candidate_struct = _string_value(candidate.get("struct_name"))
                    score = 0
                    if candidate_struct is not None:
                        for target_id in sorted_targets:
                            if candidate_struct in struct_features_by_target.get(target_id, set()):
                                score += 1
                    candidate["target_context_score"] = score
                    _rank_prefix_extension_candidate(candidate, access_size_counts)
                candidates.sort(
                    key=lambda item: (
                        -int(item.get("candidate_rank_score", 0)),
                        -int(item.get("exact_access_size_match_count", 0)),
                        -int(item.get("target_context_score", 0)),
                        abs(int(item.get("field_start_delta", 999999))),
                        str(item.get("struct_name")),
                        str(item.get("field_expr")),
                    )
                )
                if candidates:
                    group["candidate_rankings"] = candidates[:10]
                    dominant = _dominant_prefix_candidate(candidates)
                    if dominant is not None:
                        group["dominant_candidate"] = {
                            key: dominant[key]
                            for key in (
                                "struct_name",
                                "field_expr",
                                "field_offset",
                                "field_size",
                                "exact_access_size_match_count",
                                "exact_field_start",
                                "field_start_delta",
                                "access_size_score",
                                "target_context_score",
                                "candidate_rank_score",
                                "ranking_reasons",
                            )
                            if key in dominant
                        }
        group["target_count"] = len(sorted_targets)
        group["target_ids"] = sorted_targets
        result.append(group)
    _attach_custom_tail_cluster_summaries(result)
    return sorted(
        result,
        key=lambda row: (
            -int(row.get("count", 0)),
            -int(row.get("target_count", 0)),
            str(row.get("root_struct_name")),
            int(row.get("displacement", 0)) if isinstance(row.get("displacement"), int) else 0,
            str(row.get("nearby_api_feature")),
        ),
    )


def build_type_flow_report(
    manifest_rows: list[dict[str, Any]],
    xrefs: list[dict[str, Any]],
    snippet_rows: list[dict[str, Any]],
) -> list[dict[str, object]]:
    manifest_by_id = {
        str(row.get("id")): row
        for row in manifest_rows
        if isinstance(row.get("id"), str)
    }
    reports: dict[str, dict[str, Any]] = {}

    def report_for(target_id: str) -> dict[str, Any]:
        report = reports.get(target_id)
        if report is not None:
            return report
        manifest = manifest_by_id.get(target_id, {})
        report = {
            "schema_version": 1,
            "target_id": target_id,
            "source_id": manifest.get("source_id"),
            "platform": manifest.get("platform"),
            "origin": manifest.get("origin") if isinstance(manifest.get("origin"), dict) else {},
            "counts": {},
            "struct_counts": {},
            "field_counts": {},
            "typed_access_provenance_counts": {},
            "typed_storage_provenance_counts": {},
            "numeric_cause_counts": {},
            "propagation_chain_counts": {},
            "pointer_chain_root_counts": {},
            "pointer_chain_stop_counts": {},
            "_app_slot_substructure_clusters": {},
            "examples": {},
        }
        reports[target_id] = report
        return report

    def bump(report: dict[str, Any], key: str, count: int = 1) -> None:
        counts = report["counts"]
        counts[key] = int(counts.get(key, 0)) + count

    def bump_map(report: dict[str, Any], map_key: str, key: str) -> None:
        values = report[map_key]
        values[key] = int(values.get(key, 0)) + 1

    def add_example(report: dict[str, Any], key: str, example: dict[str, object]) -> None:
        examples = report["examples"].setdefault(key, [])
        if len(examples) < MAX_EXAMPLES:
            examples.append(_compact_example(example))

    for xref in xrefs:
        target_id = _string_value(xref.get("target_id"))
        feature = _string_value(xref.get("feature")) or ""
        kind = _string_value(xref.get("kind")) or ""
        kind_id = _xref_kind_id(xref)
        feature_id = _xref_feature_id(xref)
        if target_id is None:
            continue
        report = report_for(target_id)
        example = {
            "feature": feature,
            "kind": kind,
            "section": xref.get("section"),
            "offset": xref.get("offset"),
            "row_index": xref.get("row_index"),
            "stable_key": xref.get("stable_key"),
            "symbol": xref.get("symbol"),
            "value": xref.get("value"),
            "text": xref.get("text"),
        }
        if _string_value(xref.get("access")):
            example["access"] = xref.get("access")
        classification_id = _int_value(xref.get("classification_id"))
        classification = UNRESOLVED_TYPED_ACCESS_CLASSIFICATION_NAMES.get(classification_id) \
            if classification_id is not None else None
        candidate_count = _int_value(xref.get("container_candidate_count"))
        if classification:
            example["classification_id"] = classification_id
            example["classification"] = classification
        if candidate_count is not None:
            example["container_candidate_count"] = candidate_count
        if _string_value(xref.get("container_struct_name")):
            example["container_struct_name"] = xref.get("container_struct_name")
        if xref.get("refinement_applied") is True or xref.get("refinement_applied") == 1:
            example["refinement_applied"] = True
        if _string_value(xref.get("refined_struct_name")):
            example["refined_struct_name"] = xref.get("refined_struct_name")
        type_provenance_kind_id = _int_value(xref.get("type_provenance_kind_id"))
        type_provenance_kind = _typed_access_provenance_name(type_provenance_kind_id)
        if type_provenance_kind_id is not None:
            example["type_provenance_kind_id"] = type_provenance_kind_id
            example["type_provenance_kind"] = type_provenance_kind
            if _int_value(xref.get("type_provenance_offset")) is not None:
                example["type_provenance_offset"] = xref.get("type_provenance_offset")
        if kind_id == XREF_KIND_PLATFORM_TYPED_ACCESS and feature_id == XREF_FEATURE_PLATFORM_TYPED_ACCESS_ANY:
            bump(report, "resolved_typed_access")
            if type_provenance_kind_id is not None:
                bump_map(report, "typed_access_provenance_counts", type_provenance_kind)
                bump(report, f"typed_access_provenance:{_safe_part(type_provenance_kind)}")
            add_example(report, "resolved_typed_access", example)
        elif kind_id == XREF_KIND_TYPED_STORAGE and feature_id == XREF_FEATURE_TYPED_STORAGE_ANY:
            storage_target = _string_value(xref.get("access")) or "unknown"
            bump(report, "typed_storage")
            bump_map(report, "typed_storage_provenance_counts", storage_target)
            bump(report, f"typed_storage_provenance:{_safe_part(storage_target)}")
            add_example(report, "typed_storage", example)
        elif (
            kind_id == XREF_KIND_PLATFORM_UNRESOLVED_TYPED_ACCESS
            and feature_id == XREF_FEATURE_TYPED_BASE_UNRESOLVED_FIELD
        ):
            bump(report, "typed_base_unresolved_field")
            if type_provenance_kind_id is not None:
                bump(report, f"type_provenance:{_safe_part(type_provenance_kind)}")
            if classification_id == UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION:
                bump(report, "prefix_extension_evidence")
                if candidate_count == 1:
                    bump(report, "prefix_extension_unique")
                elif candidate_count is not None and candidate_count > 1:
                    bump(report, "prefix_extension_ambiguous")
            elif classification_id == UNRESOLVED_TYPED_ACCESS_CUSTOM_TAIL_OR_MISTYPED_BASE:
                bump(report, "custom_tail_or_mistyped_base")
                if _string_value(xref.get("symbol")):
                    bump(report, f"custom_tail_struct:{_safe_part(str(xref.get('symbol')))}")
            add_example(report, "typed_base_unresolved_field", example)
        elif (
            kind_id == XREF_KIND_PLATFORM_TYPE_REFINEMENT
            and feature_id == XREF_FEATURE_PLATFORM_TYPE_REFINEMENT_APPLIED
        ):
            bump(report, "type_refinement_applied")
            if type_provenance_kind_id is not None:
                bump(report, f"type_refinement_provenance:{_safe_part(type_provenance_kind)}")
            add_example(report, "type_refinement_applied", example)
        elif kind_id == XREF_KIND_APP_SLOT_API_ARG and feature_id == XREF_FEATURE_APP_SLOT_UNTYPED_API_ARG:
            bump(report, "untyped_app_slot_api_arg")
            add_example(report, "untyped_app_slot_api_arg", example)
        elif kind_id == XREF_KIND_APP_SLOT_GAP and feature_id == XREF_FEATURE_APP_SLOT_GAP:
            bump(report, "app_slot_gap")
            add_example(report, "app_slot_gap", example)
        elif kind_id == XREF_KIND_APP_SLOT_FIELD_GAP and feature_id == XREF_FEATURE_APP_SLOT_FIELD_GAP:
            bump(report, "app_slot_field_gap")
            add_example(report, "app_slot_field_gap", example)
        elif (
            kind_id == XREF_KIND_APP_SLOT_SUGGESTION
            and feature_id == XREF_FEATURE_APP_SLOT_SUGGESTED_REGION
        ):
            bump(report, "app_slot_suggested_region")
            add_example(report, "app_slot_suggested_region", example)
        feature_class_id = _xref_feature_class_id(xref)
        feature_value = _xref_feature_value(xref)
        if feature_class_id == XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_STRUCT and feature_value is not None:
            bump_map(report, "struct_counts", feature_value)
        elif feature_class_id == XREF_FEATURE_CLASS_PLATFORM_UNRESOLVED_TYPED_ACCESS_STRUCT and feature_value is not None:
            bump_map(report, "struct_counts", feature_value)
        elif feature_class_id == XREF_FEATURE_CLASS_PLATFORM_STRUCT_FIELD and feature_value is not None:
            bump_map(report, "field_counts", feature_value)
        elif feature_class_id == XREF_FEATURE_CLASS_APP_SLOT_API_ARG_REASON and feature_value is not None:
            bump(report, f"untyped_reason:{feature_value}")

    refinements_by_target: dict[str, list[dict[str, object]]] = {}
    typed_structs_by_target: dict[str, list[dict[str, object]]] = {}
    for xref in xrefs:
        target_id = _string_value(xref.get("target_id"))
        row_index = _int_value(xref.get("row_index"))
        if target_id is None or row_index is None:
            continue
        if (
            _xref_kind_id(xref) == XREF_KIND_PLATFORM_TYPE_REFINEMENT
            and _xref_feature_id(xref) == XREF_FEATURE_PLATFORM_TYPE_REFINEMENT_APPLIED
        ):
            refinements_by_target.setdefault(target_id, []).append(xref)
        elif _xref_feature_class_id(xref) == XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_STRUCT:
            typed_structs_by_target.setdefault(target_id, []).append(xref)
    for target_id, refinements in refinements_by_target.items():
        typed_structs = typed_structs_by_target.get(target_id, [])
        if not typed_structs:
            continue
        report = report_for(target_id)
        for refinement in refinements:
            refined_struct = _string_value(refinement.get("refined_struct_name")) or _string_value(refinement.get("symbol"))
            refinement_row = _int_value(refinement.get("row_index"))
            if refined_struct is None or refinement_row is None:
                continue
            for access in typed_structs:
                access_row = _int_value(access.get("row_index"))
                if access_row is None or access_row <= refinement_row or _string_value(access.get("symbol")) != refined_struct:
                    continue
                bump(report, "resolved_after_type_refinement")
                add_example(
                    report,
                    "resolved_after_type_refinement",
                    {
                        "refinement_row_index": refinement_row,
                        "row_index": access_row,
                        "refined_struct_name": refined_struct,
                        "refinement_text": refinement.get("text"),
                        "text": access.get("text"),
                        "stable_key": access.get("stable_key"),
                    },
                )
                break

    rows_by_target = _type_flow_rows_for_target(snippet_rows)
    rows_by_index_by_target = {
        target_id: _type_flow_rows_by_index(rows_by_target, target_id)
        for target_id in rows_by_target
    }
    assignment_cache_by_target: dict[str, dict[tuple[int, str, int], tuple[int, dict[str, Any], str] | None]] = {}
    xrefs_by_row = _type_flow_xrefs_by_target_row(xrefs)
    for snippet in snippet_rows:
        target_id = _string_value(snippet.get("target_id"))
        row = snippet.get("row")
        if target_id is None or not isinstance(row, dict):
            continue
        if not _listing_row_is_kind(row, LISTING_ROW_KIND_INSTRUCTION):
            continue
        if _dict_items(row.get("typed_accesses")) or _dict_items(row.get("unresolved_typed_accesses")):
            continue
        text = _string_value(row.get("text")) or ""
        if NUMERIC_ADDRESS_REG_ACCESS_RE.search(text) is None:
            continue
        report = report_for(target_id)
        trace = _type_flow_numeric_access_trace(
            target_id,
            snippet,
            rows_by_target,
            xrefs_by_row,
            rows_by_index_by_target,
            assignment_cache_by_target,
        )
        cause_id = _int_value(trace.get("cause_id")) or TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN
        cause = TYPE_FLOW_CAUSE_NAMES.get(cause_id, TYPE_FLOW_CAUSE_NAMES[TYPE_FLOW_CAUSE_UNKNOWN_POINTER_CHAIN])
        propagation_chain = trace.get("propagation_chain")
        pointer_chain = trace.get("pointer_chain")
        propagation_chain_kind = (
            str(propagation_chain.get("kind"))
            if isinstance(propagation_chain, dict) and isinstance(propagation_chain.get("kind"), str)
            else None
        )
        propagation_chain_kind_id = (
            _int_value(propagation_chain.get("kind_id")) if isinstance(propagation_chain, dict) else None
        )
        bump(report, "numeric_address_reg_access_without_type")
        bump(report, f"numeric_cause:{cause}")
        bump_map(report, "numeric_cause_counts", cause)
        if isinstance(pointer_chain, dict):
            pointer_root = _string_value(pointer_chain.get("root_kind")) or "unknown"
            pointer_stop = _string_value(pointer_chain.get("stop_reason")) or "unknown"
            bump(report, f"pointer_chain_root:{_safe_part(pointer_root)}")
            bump(report, f"pointer_chain_stop:{_safe_part(pointer_stop)}")
            bump_map(report, "pointer_chain_root_counts", pointer_root)
            bump_map(report, "pointer_chain_stop_counts", pointer_stop)
        pointer_chain_example: dict[str, object] | None = None
        if isinstance(pointer_chain, dict):
            pointer_chain_example = {
                "root_kind": _string_value(pointer_chain.get("root_kind")) or "unknown",
                "stop_reason": _string_value(pointer_chain.get("stop_reason")) or "unknown",
                "depth": int(pointer_chain.get("depth", 0)) if isinstance(pointer_chain.get("depth"), int) else 0,
            }
            hops = pointer_chain.get("hops")
            if isinstance(hops, list) and hops and isinstance(hops[0], dict):
                pointer_chain_example["first_source"] = hops[0].get("source")
                pointer_chain_example["first_source_kind"] = hops[0].get("source_kind")
            if isinstance(hops, list) and len(hops) > 1 and isinstance(hops[1], dict):
                pointer_chain_example["root_source"] = hops[-1].get("source") if isinstance(hops[-1], dict) else None
        app_slot_subaccess = (
            _type_flow_app_slot_subaccess(trace) if cause_id == TYPE_FLOW_CAUSE_APP_SLOT_LOAD else None
        )
        if app_slot_subaccess is not None:
            slot_name = str(app_slot_subaccess["slot"])
            slot_disp = str(app_slot_subaccess["slot_access_displacement_hex"])
            slot_displacement = int(app_slot_subaccess["slot_access_displacement"])
            clusters = report["_app_slot_substructure_clusters"]
            cluster = clusters.setdefault(
                slot_name,
                {
                    "slot": slot_name,
                    "access_count": 0,
                    "min_field_displacement": slot_displacement,
                    "max_field_displacement": slot_displacement,
                    "fields": {},
                },
            )
            cluster["access_count"] = int(cluster.get("access_count", 0)) + 1
            cluster["min_field_displacement"] = min(int(cluster["min_field_displacement"]), slot_displacement)
            cluster["max_field_displacement"] = max(int(cluster["max_field_displacement"]), slot_displacement)
            fields = cluster["fields"]
            field = fields.setdefault(
                slot_disp,
                {
                    "displacement": slot_displacement,
                    "displacement_hex": slot_disp,
                    "access_count": 0,
                    "examples": [],
                },
            )
            field["access_count"] = int(field.get("access_count", 0)) + 1
            if len(field["examples"]) < MAX_EXAMPLES:
                field["examples"].append(
                    {
                        "row_index": snippet.get("row_index"),
                        "stable_key": row.get("stable_key"),
                        "text": text.strip(),
                    }
                )
            bump(report, "app_slot_substructure_access")
            bump(report, f"app_slot_substructure_slot:{_safe_part(slot_name)}")
            bump(report, f"app_slot_substructure_field:{_safe_part(slot_name)}:{_safe_part(slot_disp)}")
        if propagation_chain_kind:
            bump(report, f"propagation_chain:{propagation_chain_kind}")
            bump_map(report, "propagation_chain_counts", propagation_chain_kind)
            if propagation_chain_kind_id in TYPE_FLOW_PROPAGATION_CHAIN_API_OUTPUT_IDS:
                bump(report, "propagation_gap:api_output_storage_reload_untyped_access")
                bump(report, f"propagation_gap:{propagation_chain_kind}")
                if _string_value(propagation_chain.get("api_output_struct")) == "LIB" and _type_flow_row_is_call_like(row):
                    bump(report, "propagation_gap:library_base_reload_lvo_gap")
                os_call = propagation_chain.get("os_call")
                if isinstance(os_call, dict) and _string_value(os_call.get("resolution")) == "local_helper":
                    bump(report, "propagation_gap:local_helper_output_storage_gap")
        add_example(
            report,
            "numeric_address_reg_access_without_type",
            {
                "row_index": snippet.get("row_index"),
                "stable_key": row.get("stable_key"),
                "section": row.get("section_index"),
                "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                "text": text.strip(),
                "cause": cause,
                "pointer_chain": pointer_chain_example,
                "trace": trace,
            },
        )
        add_example(
            report,
            f"numeric_address_reg_access_without_type:{cause}",
            {
                "row_index": snippet.get("row_index"),
                "stable_key": row.get("stable_key"),
                "section": row.get("section_index"),
                "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                "text": text.strip(),
                "pointer_chain": pointer_chain_example,
                "trace": trace,
            },
        )
        if app_slot_subaccess is not None:
            add_example(
                report,
                "app_slot_substructure_access",
                {
                    "row_index": snippet.get("row_index"),
                    "stable_key": row.get("stable_key"),
                    "section": row.get("section_index"),
                    "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                    "text": text.strip(),
                    "app_slot_subaccess": app_slot_subaccess,
                    "pointer_chain": pointer_chain_example,
                    "trace": trace,
                },
            )
        if propagation_chain_kind:
            add_example(
                report,
                f"propagation_chain:{propagation_chain_kind}",
                {
                    "row_index": snippet.get("row_index"),
                    "stable_key": row.get("stable_key"),
                    "section": row.get("section_index"),
                    "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                    "text": text.strip(),
                    "trace": trace,
                },
            )
            if propagation_chain_kind_id in TYPE_FLOW_PROPAGATION_CHAIN_API_OUTPUT_IDS:
                if (
                    isinstance(propagation_chain, dict)
                    and _string_value(propagation_chain.get("api_output_struct")) == "LIB"
                    and _type_flow_row_is_call_like(row)
                ):
                    add_example(
                        report,
                        "propagation_gap:library_base_reload_lvo_gap",
                        {
                            "row_index": snippet.get("row_index"),
                            "stable_key": row.get("stable_key"),
                            "section": row.get("section_index"),
                            "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                            "text": text.strip(),
                            "trace": trace,
                        },
                    )
                os_call = propagation_chain.get("os_call") if isinstance(propagation_chain, dict) else None
                if isinstance(os_call, dict) and _string_value(os_call.get("resolution")) == "local_helper":
                    add_example(
                        report,
                        "propagation_gap:local_helper_output_storage_gap",
                        {
                            "row_index": snippet.get("row_index"),
                            "stable_key": row.get("stable_key"),
                            "section": row.get("section_index"),
                            "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                            "text": text.strip(),
                            "trace": trace,
                        },
                    )

    result: list[dict[str, object]] = []
    for report in reports.values():
        counts = report["counts"]
        if not counts:
            continue
        substructure_suggestions: list[dict[str, object]] = []
        for cluster in report.pop("_app_slot_substructure_clusters", {}).values():
            fields = [
                dict(field)
                for field in sorted(
                    cluster.get("fields", {}).values(),
                    key=lambda item: int(item.get("displacement", 0)),
                )
            ]
            if not fields:
                continue
            substructure_suggestions.append(
                {
                    "kind": "app_slot_substructure_region",
                    "inference_kind": "app_slot_pointer_substructure_access",
                    "confidence": "evidence",
                    "source": "numeric_app_slot_substructure_access",
                    "slot": cluster["slot"],
                    "access_count": int(cluster.get("access_count", 0)),
                    "field_count": len(fields),
                    "min_field_displacement": int(cluster["min_field_displacement"]),
                    "min_field_displacement_hex": _signed_hex_string(int(cluster["min_field_displacement"])),
                    "max_field_displacement": int(cluster["max_field_displacement"]),
                    "max_field_displacement_hex": _signed_hex_string(int(cluster["max_field_displacement"])),
                    "fields": fields,
                }
            )
        substructure_suggestions.sort(
            key=lambda item: (-int(item.get("access_count", 0)), str(item.get("slot", "")))
        )
        if substructure_suggestions:
            counts["app_slot_substructure_suggested_region"] = len(substructure_suggestions)
            report["app_slot_substructure_suggestions"] = substructure_suggestions
        opportunity_count = sum(
            int(counts.get(key, 0))
            for key in (
                "untyped_app_slot_api_arg",
                "app_slot_gap",
                "app_slot_field_gap",
                "app_slot_suggested_region",
                "app_slot_substructure_suggested_region",
                "typed_base_unresolved_field",
                "numeric_address_reg_access_without_type",
            )
        )
        report["opportunity_count"] = opportunity_count
        report["resolved_typed_access_count"] = int(counts.get("resolved_typed_access", 0))
        report["counts"] = dict(sorted(counts.items()))
        report["struct_counts"] = dict(sorted(report["struct_counts"].items()))
        report["field_counts"] = dict(sorted(report["field_counts"].items()))
        report["typed_access_provenance_counts"] = dict(sorted(report["typed_access_provenance_counts"].items()))
        report["typed_storage_provenance_counts"] = dict(sorted(report["typed_storage_provenance_counts"].items()))
        report["numeric_cause_counts"] = dict(sorted(report["numeric_cause_counts"].items()))
        report["propagation_chain_counts"] = dict(sorted(report["propagation_chain_counts"].items()))
        report["pointer_chain_root_counts"] = dict(sorted(report["pointer_chain_root_counts"].items()))
        report["pointer_chain_stop_counts"] = dict(sorted(report["pointer_chain_stop_counts"].items()))
        report["examples"] = {
            key: report["examples"][key]
            for key in sorted(report["examples"])
        }
        result.append(report)
    return sorted(
        result,
        key=lambda row: (
            -int(row.get("opportunity_count", 0)),
            -int(row.get("resolved_typed_access_count", 0)),
            str(row.get("platform")),
            str(row.get("target_id")),
        ),
    )


def _type_flow_int(row: dict[str, Any], key: str) -> int:
    value = row.get(key)
    return value if isinstance(value, int) else 0


def _type_flow_count_map(row: dict[str, Any] | None, key: str) -> dict[str, int]:
    if row is None:
        return {}
    values = row.get(key)
    if not isinstance(values, dict):
        return {}
    return {
        str(name): int(value)
        for name, value in values.items()
        if isinstance(name, str) and isinstance(value, int)
    }


def _type_flow_total_map(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in rows:
        for name, value in _type_flow_count_map(row, key).items():
            totals[name] = totals.get(name, 0) + value
    return dict(sorted(totals.items()))


def _type_flow_delta_map(before: dict[str, int], after: dict[str, int]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for key in sorted(set(before) | set(after)):
        before_value = before.get(key, 0)
        after_value = after.get(key, 0)
        delta = after_value - before_value
        if before_value != 0 or after_value != 0 or delta != 0:
            result[key] = {"before": before_value, "after": after_value, "delta": delta}
    return result


TYPE_FLOW_EFFECTIVENESS_KEYS = (
    "numeric_address_reg_access_without_type",
    "typed_base_unresolved_field",
    "resolved_typed_access",
    "typed_storage",
    "prefix_extension_evidence",
    "prefix_extension_unique",
    "prefix_extension_ambiguous",
    "custom_tail_or_mistyped_base",
    "type_refinement_applied",
    "resolved_after_type_refinement",
    "untyped_app_slot_api_arg",
    "app_slot_gap",
    "app_slot_field_gap",
    "app_slot_suggested_region",
    "app_slot_substructure_access",
    "app_slot_substructure_suggested_region",
)


def _type_flow_effectiveness_totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = _type_flow_total_map(rows, "counts")
    result = {key: int(counts.get(key, 0)) for key in TYPE_FLOW_EFFECTIVENESS_KEYS}
    result["custom_tail_struct_count"] = sum(
        1 for key, value in counts.items() if key.startswith("custom_tail_struct:") and value > 0
    )
    return result


TYPE_FLOW_OPEN_OPPORTUNITY_KEYS = (
    "numeric_address_reg_access_without_type",
    "typed_base_unresolved_field",
    "untyped_app_slot_api_arg",
    "app_slot_gap",
    "app_slot_field_gap",
    "app_slot_suggested_region",
    "app_slot_substructure_access",
    "app_slot_substructure_suggested_region",
)


def _type_flow_open_score(row: dict[str, Any]) -> int:
    counts = _type_flow_count_map(row, "counts")
    return sum(int(counts.get(key, 0)) for key in TYPE_FLOW_OPEN_OPPORTUNITY_KEYS)


def _type_flow_nested_bump(
    mapping: dict[str, dict[str, int]],
    outer: object,
    inner: object,
    amount: int,
) -> None:
    outer_key = str(outer) if isinstance(outer, str) and outer else "unknown"
    inner_key = str(inner) if isinstance(inner, str) and inner else "unknown"
    bucket = mapping.setdefault(outer_key, {})
    bucket[inner_key] = int(bucket.get(inner_key, 0)) + int(amount)


def _type_flow_storage_kind_from_chain(chain_kind: str) -> str | None:
    match = re.search(r"_to_(.+)_reload(?:_|$)", chain_kind)
    if match:
        return match.group(1)
    match = re.search(r"^register_to_(.+)_reload$", chain_kind)
    if match:
        return match.group(1)
    return None


def _type_flow_api_feature_from_example(example: dict[str, Any]) -> str | None:
    trace = example.get("trace")
    if not isinstance(trace, dict):
        return None
    for key in ("nearest_os_call", "os_call"):
        os_call = trace.get(key)
        if isinstance(os_call, dict):
            feature = os_call.get("feature")
            if isinstance(feature, str) and feature:
                return feature
    chain = trace.get("propagation_chain")
    if isinstance(chain, dict):
        for key in ("os_call", "nearest_os_call"):
            os_call = chain.get(key)
            if isinstance(os_call, dict):
                feature = os_call.get("feature")
                if isinstance(feature, str) and feature:
                    return feature
        feature = chain.get("api_feature")
        if isinstance(feature, str) and feature:
            return feature
    return None


def _type_flow_example_trace(example: dict[str, Any]) -> dict[str, Any]:
    trace = example.get("trace")
    return trace if isinstance(trace, dict) else {}


def _type_flow_example_propagation_chain(example: dict[str, Any]) -> dict[str, Any]:
    trace = _type_flow_example_trace(example)
    chain = trace.get("propagation_chain")
    return chain if isinstance(chain, dict) else {}


def _type_flow_example_pointer_chain(example: dict[str, Any]) -> dict[str, Any]:
    trace = _type_flow_example_trace(example)
    chain = trace.get("pointer_chain")
    return chain if isinstance(chain, dict) else {}


def _type_flow_example_value(mapping: dict[str, Any], key: str, fallback: str = "unknown") -> str:
    value = mapping.get(key)
    return value if isinstance(value, str) and value else fallback


def _type_flow_example_items(row: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    result: list[tuple[str, dict[str, Any]]] = []
    examples = row.get("examples")
    if not isinstance(examples, dict):
        return result
    for example_kind, values in examples.items():
        if not isinstance(values, list):
            continue
        for example in values:
            if isinstance(example, dict):
                result.append((str(example_kind), example))
    return result


def build_type_flow_api_audit_report(
    type_flow_rows: list[dict[str, Any]],
    *,
    api_feature: str | None = None,
    max_targets: int = 25,
) -> dict[str, object]:
    features: dict[str, dict[str, Any]] = {}
    target_sets: dict[str, set[str]] = {}
    for row in type_flow_rows:
        target_id = row.get("target_id") if isinstance(row.get("target_id"), str) else "unknown"
        platform = row.get("platform") if isinstance(row.get("platform"), str) else "unknown"
        for example_kind, example in _type_flow_example_items(row):
            feature = _type_flow_api_feature_from_example(example)
            if feature is None or (api_feature is not None and feature != api_feature):
                continue
            trace = _type_flow_example_trace(example)
            pointer_chain = _type_flow_example_pointer_chain(example)
            propagation_chain = _type_flow_example_propagation_chain(example)
            chain_kind = _type_flow_example_value(propagation_chain, "kind", "none")
            storage_kind = _type_flow_example_value(
                propagation_chain,
                "storage_kind",
                _type_flow_storage_kind_from_chain(chain_kind) or "none",
            )
            bucket = features.setdefault(
                feature,
                {
                    "feature": feature,
                    "example_count": 0,
                    "platform_counts": {},
                    "cause_counts": {},
                    "example_kind_counts": {},
                    "propagation_chain_counts": {},
                    "pointer_chain_root_counts": {},
                    "pointer_chain_stop_counts": {},
                    "storage_kind_counts": {},
                    "targets": [],
                },
            )
            bucket["example_count"] = int(bucket["example_count"]) + 1
            _type_flow_nested_bump({"root": bucket["platform_counts"]}, "root", platform, 1)
            _type_flow_nested_bump({"root": bucket["cause_counts"]}, "root", trace.get("cause"), 1)
            _type_flow_nested_bump({"root": bucket["example_kind_counts"]}, "root", example_kind, 1)
            _type_flow_nested_bump({"root": bucket["propagation_chain_counts"]}, "root", chain_kind, 1)
            _type_flow_nested_bump(
                {"root": bucket["pointer_chain_root_counts"]},
                "root",
                pointer_chain.get("root_kind"),
                1,
            )
            _type_flow_nested_bump(
                {"root": bucket["pointer_chain_stop_counts"]},
                "root",
                pointer_chain.get("stop_reason"),
                1,
            )
            _type_flow_nested_bump({"root": bucket["storage_kind_counts"]}, "root", storage_kind, 1)
            target_sets.setdefault(feature, set()).add(target_id)
            targets = cast(list[dict[str, object]], bucket["targets"])
            if len(targets) < max_targets:
                targets.append(
                    {
                        "target_id": target_id,
                        "source_id": row.get("source_id"),
                        "platform": platform,
                        "example_kind": example_kind,
                        "cause": trace.get("cause"),
                        "propagation_chain": propagation_chain,
                        "pointer_chain": pointer_chain,
                        "example": example,
                    }
                )
    ordered_features = sorted(
        features.values(),
        key=lambda item: (-int(item.get("example_count", 0)), str(item.get("feature", ""))),
    )
    for item in ordered_features:
        feature_name = str(item.get("feature", ""))
        item["target_count"] = len(target_sets.get(feature_name, set()))
        for key in (
            "platform_counts",
            "cause_counts",
            "example_kind_counts",
            "propagation_chain_counts",
            "pointer_chain_root_counts",
            "pointer_chain_stop_counts",
            "storage_kind_counts",
        ):
            value = item.get(key)
            if isinstance(value, dict):
                item[key] = dict(sorted((str(k), int(v)) for k, v in value.items()))
    return {
        "schema_version": 1,
        "api_feature": api_feature,
        "feature_count": len(ordered_features),
        "features": ordered_features,
    }


def build_type_flow_chain_slice_report(
    type_flow_rows: list[dict[str, Any]],
    *,
    max_slices: int = 25,
    platform: str | None = None,
) -> dict[str, object]:
    buckets: dict[tuple[str, str, str, str, str, str, str], dict[str, Any]] = {}
    target_sets: dict[tuple[str, str, str, str, str, str, str], set[str]] = {}
    for row in type_flow_rows:
        row_platform = row.get("platform") if isinstance(row.get("platform"), str) else "unknown"
        if platform is not None and row_platform != platform:
            continue
        target_id = row.get("target_id") if isinstance(row.get("target_id"), str) else "unknown"
        for example_kind, example in _type_flow_example_items(row):
            trace = _type_flow_example_trace(example)
            if not trace:
                continue
            pointer_chain = _type_flow_example_pointer_chain(example)
            propagation_chain = _type_flow_example_propagation_chain(example)
            chain_kind = _type_flow_example_value(propagation_chain, "kind", "none")
            storage_kind = _type_flow_example_value(
                propagation_chain,
                "storage_kind",
                _type_flow_storage_kind_from_chain(chain_kind) or "none",
            )
            feature = _type_flow_api_feature_from_example(example) or "none"
            key = (
                row_platform,
                _type_flow_example_value(trace, "cause"),
                _type_flow_example_value(pointer_chain, "root_kind"),
                _type_flow_example_value(pointer_chain, "stop_reason"),
                chain_kind,
                storage_kind,
                feature,
            )
            bucket = buckets.setdefault(
                key,
                {
                    "platform": key[0],
                    "cause": key[1],
                    "pointer_root": key[2],
                    "pointer_stop": key[3],
                    "propagation_chain": key[4],
                    "storage_kind": key[5],
                    "api_feature": key[6],
                    "example_count": 0,
                    "example_kind_counts": {},
                    "targets": [],
                },
            )
            bucket["example_count"] = int(bucket["example_count"]) + 1
            _type_flow_nested_bump({"root": bucket["example_kind_counts"]}, "root", example_kind, 1)
            target_sets.setdefault(key, set()).add(target_id)
            targets = cast(list[dict[str, object]], bucket["targets"])
            if len(targets) < 5:
                targets.append(
                    {
                        "target_id": target_id,
                        "source_id": row.get("source_id"),
                        "example_kind": example_kind,
                        "example": example,
                    }
                )
    slices = sorted(
        buckets.values(),
        key=lambda item: (
            -int(item.get("example_count", 0)),
            str(item.get("platform", "")),
            str(item.get("cause", "")),
            str(item.get("pointer_root", "")),
            str(item.get("propagation_chain", "")),
            str(item.get("api_feature", "")),
        ),
    )
    for key, item in buckets.items():
        item["target_count"] = len(target_sets.get(key, set()))
    for item in slices:
        counts = item.get("example_kind_counts")
        if isinstance(counts, dict):
            item["example_kind_counts"] = dict(sorted((str(k), int(v)) for k, v in counts.items()))
    return {
        "schema_version": 1,
        "platform": platform,
        "slice_count": len(slices),
        "slices": slices[:max_slices],
    }


def _type_flow_storage_type_aliases(type_name: str | None) -> set[str]:
    if not type_name:
        return set()
    aliases = {type_name}
    cleaned = re.sub(r"\b(?:const|volatile|struct)\b", " ", type_name)
    cleaned = cleaned.replace("*", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned:
        aliases.add(cleaned)
        parts = cleaned.split()
        if parts:
            aliases.add(parts[-1])
    return {alias for alias in aliases if alias and alias not in {"void"}}


def _type_flow_row_context(row: dict[str, Any]) -> dict[str, object]:
    return _compact_example(
        {
            "row_index": row.get("row_index"),
            "section": row.get("section"),
            "offset": row.get("offset"),
            "stable_key": row.get("stable_key"),
            "symbol": row.get("symbol"),
            "access": row.get("access"),
            "value": row.get("value"),
            "text": row.get("text"),
        }
    )


def _type_flow_access_structs_by_target_row(xrefs: list[dict[str, Any]]) -> dict[tuple[str, int], set[str]]:
    structs_by_row: dict[tuple[str, int], set[str]] = {}
    for xref in xrefs:
        if _xref_kind_id(xref) != XREF_KIND_PLATFORM_TYPED_ACCESS:
            continue
        target_id = _string_value(xref.get("target_id"))
        row_index = _int_value(xref.get("row_index"))
        if target_id is None or row_index is None:
            continue
        if _xref_feature_class_id(xref) not in {
            XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_STRUCT,
            XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_OWNER,
        }:
            continue
        symbol = _string_value(xref.get("symbol"))
        if symbol:
            structs_by_row.setdefault((target_id, row_index), set()).add(symbol)
    return structs_by_row


def _type_flow_storage_nearby_api_call(
    target_id: str,
    row_index: int,
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    *,
    lookbehind: int = 8,
) -> dict[str, object] | None:
    for candidate_row in range(row_index, max(0, row_index - lookbehind) - 1, -1):
        row_xrefs = xrefs_by_row.get((target_id, candidate_row), [])
        row_has_output = any(
            _xref_kind_id(item) in {XREF_KIND_OS_CALL_OUTPUT, XREF_KIND_OS_CALL_OUTPUT_STRUCT}
            for item in row_xrefs
        )
        if candidate_row != row_index and not row_has_output:
            continue
        for xref in row_xrefs:
            feature = _string_value(xref.get("feature")) or ""
            if (
                _xref_kind_id(xref) != XREF_KIND_OS_CALL
                or _xref_feature_class_id(xref) != XREF_FEATURE_CLASS_OS_CALL
            ):
                continue
            return _compact_example(
                {
                    "row_index": xref.get("row_index"),
                    "section": xref.get("section"),
                    "offset": xref.get("offset"),
                    "stable_key": xref.get("stable_key"),
                    "feature": feature,
                    "symbol": xref.get("symbol"),
                    "value": xref.get("value"),
                    "resolution": xref.get("resolution"),
                    "text": xref.get("text"),
                }
            )
    return None


def _type_flow_access_matches_storage(storage: dict[str, Any], access: dict[str, Any]) -> bool:
    storage_section = _int_value(storage.get("section"))
    storage_offset = _int_value(storage.get("offset"))
    provenance_section = _int_value(access.get("type_provenance_section"))
    provenance_offset = _int_value(access.get("type_provenance_offset"))
    if provenance_offset is not None and storage_offset is not None:
        if provenance_offset == storage_offset and (
            provenance_section is None or storage_section is None or provenance_section == storage_section
        ):
            return True
    storage_aliases = _type_flow_storage_type_aliases(_string_value(storage.get("symbol")))
    access_structs = access.get("structs")
    if storage_aliases and isinstance(access_structs, set) and storage_aliases.intersection(access_structs):
        return True
    return False


def _type_flow_first_later_xref(
    xrefs: list[dict[str, Any]],
    storage: dict[str, Any],
    *,
    max_window: int,
    match_kind: str | None = None,
) -> dict[str, object] | None:
    storage_row = _int_value(storage.get("row_index"))
    storage_section = _int_value(storage.get("section"))
    if storage_row is None:
        return None
    best: dict[str, Any] | None = None
    for xref in xrefs:
        row_index = _int_value(xref.get("row_index"))
        if row_index is None or row_index <= storage_row or row_index - storage_row > max_window:
            continue
        if storage_section is not None and _int_value(xref.get("section")) not in (None, storage_section):
            continue
        if match_kind is not None and _string_value(xref.get("kind")) != match_kind:
            continue
        if best is None or row_index < int(best.get("row_index", 1 << 30)):
            best = xref
    return _type_flow_row_context(best) if best is not None else None


def _type_flow_first_later_numeric_access(
    snippet_rows: list[dict[str, Any]],
    storage: dict[str, Any],
    *,
    max_window: int,
) -> dict[str, object] | None:
    storage_row = _int_value(storage.get("row_index"))
    storage_section = _int_value(storage.get("section"))
    if storage_row is None:
        return None
    for snippet in snippet_rows:
        row_index = _int_value(snippet.get("row_index"))
        row = snippet.get("row")
        if row_index is None or not isinstance(row, dict):
            continue
        if row_index <= storage_row or row_index - storage_row > max_window:
            continue
        if storage_section is not None and _int_value(row.get("section_index")) not in (None, storage_section):
            continue
        if not _listing_row_is_kind(row, LISTING_ROW_KIND_INSTRUCTION):
            continue
        if _dict_items(row.get("typed_accesses")) or _dict_items(row.get("unresolved_typed_accesses")):
            continue
        text = _string_value(row.get("text")) or ""
        if NUMERIC_ADDRESS_REG_ACCESS_RE.search(text) is None:
            continue
        return _compact_example(
            {
                "row_index": row_index,
                "section": row.get("section_index"),
                "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                "stable_key": row.get("stable_key"),
                "text": text.strip(),
            }
        )
    return None


def build_type_flow_storage_access_gap_report(
    type_flow_rows: list[dict[str, Any]],
    xrefs: list[dict[str, Any]],
    snippet_rows: list[dict[str, Any]],
    *,
    platform: str | None = None,
    api_feature: str | None = None,
    storage_target: str | None = None,
    max_targets: int = 25,
    max_examples: int = 5,
    window: int = 500,
) -> dict[str, object]:
    manifest_by_target = {
        str(row.get("target_id")): row
        for row in type_flow_rows
        if isinstance(row.get("target_id"), str)
    }
    rows_by_target = _type_flow_rows_for_target(snippet_rows)
    xrefs_by_row = _type_flow_xrefs_by_target_row(xrefs)
    structs_by_row = _type_flow_access_structs_by_target_row(xrefs)
    access_xrefs_by_target: dict[str, list[dict[str, Any]]] = {}
    unresolved_xrefs_by_target: dict[str, list[dict[str, Any]]] = {}
    storage_xrefs: list[dict[str, Any]] = []
    for xref in xrefs:
        target_id = _string_value(xref.get("target_id"))
        kind_id = _xref_kind_id(xref)
        feature_id = _xref_feature_id(xref)
        if target_id is None:
            continue
        if kind_id == XREF_KIND_TYPED_STORAGE and feature_id == XREF_FEATURE_TYPED_STORAGE_ANY:
            storage_xrefs.append(xref)
        elif kind_id == XREF_KIND_PLATFORM_TYPED_ACCESS and feature_id == XREF_FEATURE_PLATFORM_TYPED_ACCESS_ANY:
            entry = dict(xref)
            row_index = _int_value(xref.get("row_index"))
            entry["structs"] = set(structs_by_row.get((target_id, row_index if row_index is not None else -1), set()))
            access_xrefs_by_target.setdefault(target_id, []).append(entry)
        elif (
            kind_id == XREF_KIND_PLATFORM_UNRESOLVED_TYPED_ACCESS
            and feature_id == XREF_FEATURE_TYPED_BASE_UNRESOLVED_FIELD
        ):
            unresolved_xrefs_by_target.setdefault(target_id, []).append(xref)
    for values in access_xrefs_by_target.values():
        values.sort(key=lambda item: _sort_int(item.get("row_index")))
    for values in unresolved_xrefs_by_target.values():
        values.sort(key=lambda item: _sort_int(item.get("row_index")))

    targets: dict[str, dict[str, Any]] = {}
    platform_counts: dict[str, int] = {}
    api_feature_counts: dict[str, int] = {}
    storage_target_counts: dict[str, int] = {}
    storage_type_counts: dict[str, int] = {}
    total_storage_count = 0
    covered_storage_count = 0
    total_gap_count = 0

    def bump(mapping: dict[str, int], key: str | None, amount: int = 1) -> None:
        safe_key = key if key else "none"
        mapping[safe_key] = int(mapping.get(safe_key, 0)) + amount

    for storage in sorted(storage_xrefs, key=lambda item: (str(item.get("target_id")), _sort_int(item.get("row_index")))):
        target_id = _string_value(storage.get("target_id"))
        if target_id is None:
            continue
        target_row = manifest_by_target.get(target_id, {})
        target_platform = _string_value(storage.get("platform")) or _string_value(target_row.get("platform")) or "unknown"
        if platform is not None and target_platform != platform:
            continue
        observed_storage_target = _string_value(storage.get("access")) or "unknown"
        if storage_target is not None and observed_storage_target != storage_target:
            continue
        row_index = _int_value(storage.get("row_index"))
        if row_index is None:
            continue
        api_call = _type_flow_storage_nearby_api_call(target_id, row_index, xrefs_by_row)
        observed_api_feature = _string_value(api_call.get("feature")) if isinstance(api_call, dict) else None
        if api_feature is not None and observed_api_feature != api_feature:
            continue
        total_storage_count += 1
        access_candidates = access_xrefs_by_target.get(target_id, [])
        matching_access = None
        for access in access_candidates:
            access_row = _int_value(access.get("row_index"))
            if access_row is None or access_row <= row_index or access_row - row_index > window:
                continue
            if _type_flow_access_matches_storage(storage, access):
                matching_access = access
                break
        if matching_access is not None:
            covered_storage_count += 1
            continue

        total_gap_count += 1
        bump(platform_counts, target_platform)
        bump(storage_target_counts, observed_storage_target)
        storage_type = _string_value(storage.get("symbol")) or "unknown"
        bump(storage_type_counts, storage_type)
        bump(api_feature_counts, observed_api_feature)
        target = targets.setdefault(
            target_id,
            {
                "target_id": target_id,
                "source_id": storage.get("source_id") or target_row.get("source_id"),
                "platform": target_platform,
                "origin": storage.get("origin") if isinstance(storage.get("origin"), dict) else target_row.get("origin", {}),
                "gap_count": 0,
                "storage_target_counts": {},
                "storage_type_counts": {},
                "api_feature_counts": {},
                "gaps": [],
            },
        )
        target["gap_count"] = int(target["gap_count"]) + 1
        bump(cast(dict[str, int], target["storage_target_counts"]), observed_storage_target)
        bump(cast(dict[str, int], target["storage_type_counts"]), storage_type)
        bump(cast(dict[str, int], target["api_feature_counts"]), observed_api_feature)
        gaps = cast(list[dict[str, object]], target["gaps"])
        if len(gaps) < max_examples:
            target_snippets = rows_by_target.get(target_id, [])
            gaps.append(
                _compact_example(
                    {
                        "storage": _type_flow_row_context(storage),
                        "api_call": api_call,
                        "first_later_typed_access": _type_flow_first_later_xref(
                            access_candidates,
                            storage,
                            max_window=window,
                            match_kind="platform_typed_access",
                        ),
                        "first_later_unresolved_access": _type_flow_first_later_xref(
                            unresolved_xrefs_by_target.get(target_id, []),
                            storage,
                            max_window=window,
                            match_kind="platform_unresolved_typed_access",
                        ),
                        "first_later_numeric_access": _type_flow_first_later_numeric_access(
                            target_snippets,
                            storage,
                            max_window=window,
                        ),
                    }
                )
            )

    target_rows = sorted(
        targets.values(),
        key=lambda item: (
            -int(item.get("gap_count", 0)),
            str(item.get("platform", "")),
            str(item.get("target_id", "")),
        ),
    )
    for item in target_rows:
        item["storage_target_counts"] = dict(sorted(cast(dict[str, int], item["storage_target_counts"]).items()))
        item["storage_type_counts"] = dict(sorted(cast(dict[str, int], item["storage_type_counts"]).items()))
        item["api_feature_counts"] = dict(sorted(cast(dict[str, int], item["api_feature_counts"]).items()))
    return {
        "schema_version": 1,
        "platform": platform,
        "api_feature": api_feature,
        "storage_target": storage_target,
        "window": window,
        "total_storage_count": total_storage_count,
        "covered_storage_count": covered_storage_count,
        "total_gap_count": total_gap_count,
        "target_count": len(target_rows),
        "platform_counts": dict(sorted(platform_counts.items())),
        "api_feature_counts": dict(sorted(api_feature_counts.items())),
        "storage_target_counts": dict(sorted(storage_target_counts.items())),
        "storage_type_counts": dict(sorted(storage_type_counts.items())),
        "targets": target_rows[:max_targets],
    }


def build_type_flow_opportunity_report(
    type_flow_rows: list[dict[str, Any]],
    *,
    max_targets: int = 25,
    platform: str | None = None,
) -> dict[str, object]:
    rows = [
        row
        for row in type_flow_rows
        if platform is None or row.get("platform") == platform
    ]
    targets: list[dict[str, object]] = []
    platform_open_counts: dict[str, dict[str, int]] = {}
    numeric_cause_by_platform: dict[str, dict[str, int]] = {}
    propagation_chain_by_platform: dict[str, dict[str, int]] = {}
    pointer_chain_root_by_platform: dict[str, dict[str, int]] = {}
    pointer_chain_stop_by_platform: dict[str, dict[str, int]] = {}
    storage_kind_counts: dict[str, int] = {}
    api_feature_counts: dict[str, int] = {}
    for row in rows:
        score = _type_flow_open_score(row)
        platform_name = str(row.get("platform")) if isinstance(row.get("platform"), str) else "unknown"
        counts = _type_flow_count_map(row, "counts")
        for key in TYPE_FLOW_OPEN_OPPORTUNITY_KEYS:
            value = int(counts.get(key, 0))
            if value:
                _type_flow_nested_bump(platform_open_counts, platform_name, key, value)
        for cause, value in _type_flow_count_map(row, "numeric_cause_counts").items():
            _type_flow_nested_bump(numeric_cause_by_platform, platform_name, cause, value)
        for chain, value in _type_flow_count_map(row, "propagation_chain_counts").items():
            storage_kind = _type_flow_storage_kind_from_chain(chain)
            _type_flow_nested_bump(propagation_chain_by_platform, platform_name, chain, value)
            if storage_kind is not None:
                storage_kind_counts[storage_kind] = int(storage_kind_counts.get(storage_kind, 0)) + int(value)
        for root_kind, value in _type_flow_count_map(row, "pointer_chain_root_counts").items():
            _type_flow_nested_bump(pointer_chain_root_by_platform, platform_name, root_kind, value)
        for stop_reason, value in _type_flow_count_map(row, "pointer_chain_stop_counts").items():
            _type_flow_nested_bump(pointer_chain_stop_by_platform, platform_name, stop_reason, value)
        examples = row.get("examples")
        if isinstance(examples, dict):
            for values in examples.values():
                if not isinstance(values, list):
                    continue
                for example in values:
                    if not isinstance(example, dict):
                        continue
                    feature = _type_flow_api_feature_from_example(example)
                    if feature is not None:
                        api_feature_counts[feature] = int(api_feature_counts.get(feature, 0)) + 1
        if score <= 0:
            continue
        targets.append(
            {
                "target_id": row.get("target_id"),
                "source_id": row.get("source_id"),
                "platform": row.get("platform"),
                "origin": row.get("origin") if isinstance(row.get("origin"), dict) else {},
                "open_score": score,
                "resolved_typed_access_count": _type_flow_int(row, "resolved_typed_access_count"),
                "open_counts": {
                    key: int(counts.get(key, 0))
                    for key in TYPE_FLOW_OPEN_OPPORTUNITY_KEYS
                    if int(counts.get(key, 0)) != 0
                },
                "numeric_cause_counts": _type_flow_count_map(row, "numeric_cause_counts"),
                "propagation_chain_counts": _type_flow_count_map(row, "propagation_chain_counts"),
                "pointer_chain_root_counts": _type_flow_count_map(row, "pointer_chain_root_counts"),
                "pointer_chain_stop_counts": _type_flow_count_map(row, "pointer_chain_stop_counts"),
                "typed_access_provenance_counts": _type_flow_count_map(row, "typed_access_provenance_counts"),
                "typed_storage_provenance_counts": _type_flow_count_map(row, "typed_storage_provenance_counts"),
                "app_slot_substructure_suggestions": row.get("app_slot_substructure_suggestions", []),
                "examples": row.get("examples") if isinstance(row.get("examples"), dict) else {},
            }
        )
    targets.sort(
        key=lambda row: (
            -int(row.get("open_score", 0)),
            -int(row.get("resolved_typed_access_count", 0)),
            str(row.get("platform")),
            str(row.get("target_id")),
        )
    )
    return {
        "schema_version": 1,
        "target_count": len(targets),
        "totals": _type_flow_effectiveness_totals(rows),
        "numeric_cause_counts": _type_flow_total_map(rows, "numeric_cause_counts"),
        "propagation_chain_counts": _type_flow_total_map(rows, "propagation_chain_counts"),
        "pointer_chain_root_counts": _type_flow_total_map(rows, "pointer_chain_root_counts"),
        "pointer_chain_stop_counts": _type_flow_total_map(rows, "pointer_chain_stop_counts"),
        "platform_open_counts": {key: dict(sorted(value.items())) for key, value in sorted(platform_open_counts.items())},
        "numeric_cause_by_platform": {
            key: dict(sorted(value.items())) for key, value in sorted(numeric_cause_by_platform.items())
        },
        "propagation_chain_by_platform": {
            key: dict(sorted(value.items())) for key, value in sorted(propagation_chain_by_platform.items())
        },
        "pointer_chain_root_by_platform": {
            key: dict(sorted(value.items())) for key, value in sorted(pointer_chain_root_by_platform.items())
        },
        "pointer_chain_stop_by_platform": {
            key: dict(sorted(value.items())) for key, value in sorted(pointer_chain_stop_by_platform.items())
        },
        "api_feature_counts": dict(sorted(api_feature_counts.items())),
        "storage_kind_counts": dict(sorted(storage_kind_counts.items())),
        "typed_access_provenance_counts": _type_flow_total_map(rows, "typed_access_provenance_counts"),
        "typed_storage_provenance_counts": _type_flow_total_map(rows, "typed_storage_provenance_counts"),
        "targets": targets[:max_targets],
    }


TYPE_FLOW_BASELINE_MIN_TOTALS = (
    "resolved_typed_access",
    "typed_storage",
    "type_refinement_applied",
    "resolved_after_type_refinement",
)
TYPE_FLOW_BASELINE_MAX_TOTALS = (
    "numeric_address_reg_access_without_type",
)
TYPE_FLOW_BASELINE_MAX_NUMERIC_CAUSES = (
    "unknown_pointer_chain",
    "stack_slot_load",
    "global_or_base_slot_load",
)


def build_type_flow_baseline_report(type_flow_rows: list[dict[str, Any]]) -> dict[str, object]:
    opportunity = build_type_flow_opportunity_report(type_flow_rows, max_targets=0)
    return {
        "schema_version": 1,
        "target_count": len(type_flow_rows),
        "totals": opportunity["totals"],
        "numeric_cause_counts": opportunity["numeric_cause_counts"],
        "propagation_chain_counts": opportunity["propagation_chain_counts"],
        "pointer_chain_root_counts": opportunity["pointer_chain_root_counts"],
        "pointer_chain_stop_counts": opportunity["pointer_chain_stop_counts"],
        "platform_open_counts": opportunity["platform_open_counts"],
        "numeric_cause_by_platform": opportunity["numeric_cause_by_platform"],
        "propagation_chain_by_platform": opportunity["propagation_chain_by_platform"],
        "pointer_chain_root_by_platform": opportunity["pointer_chain_root_by_platform"],
        "pointer_chain_stop_by_platform": opportunity["pointer_chain_stop_by_platform"],
        "api_feature_counts": opportunity["api_feature_counts"],
        "storage_kind_counts": opportunity["storage_kind_counts"],
        "typed_access_provenance_counts": opportunity["typed_access_provenance_counts"],
        "typed_storage_provenance_counts": opportunity["typed_storage_provenance_counts"],
    }


def _type_flow_compact_target_baseline_row(row: dict[str, Any]) -> dict[str, object]:
    return {
        "target_id": row.get("target_id"),
        "source_id": row.get("source_id"),
        "platform": row.get("platform"),
        "origin": row.get("origin") if isinstance(row.get("origin"), dict) else {},
        "opportunity_count": _type_flow_int(row, "opportunity_count"),
        "resolved_typed_access_count": _type_flow_int(row, "resolved_typed_access_count"),
        "counts": _type_flow_count_map(row, "counts"),
        "numeric_cause_counts": _type_flow_count_map(row, "numeric_cause_counts"),
        "propagation_chain_counts": _type_flow_count_map(row, "propagation_chain_counts"),
        "pointer_chain_root_counts": _type_flow_count_map(row, "pointer_chain_root_counts"),
        "pointer_chain_stop_counts": _type_flow_count_map(row, "pointer_chain_stop_counts"),
        "typed_access_provenance_counts": _type_flow_count_map(row, "typed_access_provenance_counts"),
        "typed_storage_provenance_counts": _type_flow_count_map(row, "typed_storage_provenance_counts"),
        "struct_counts": _type_flow_count_map(row, "struct_counts"),
        "field_counts": _type_flow_count_map(row, "field_counts"),
    }


def build_type_flow_target_baseline_report(type_flow_rows: list[dict[str, Any]]) -> dict[str, object]:
    targets = [
        _type_flow_compact_target_baseline_row(row)
        for row in type_flow_rows
        if isinstance(row.get("target_id"), str)
    ]
    targets.sort(key=lambda row: (str(row.get("platform")), str(row.get("target_id"))))
    return {
        "schema_version": 1,
        "target_count": len(targets),
        "targets": targets,
    }


def _type_flow_target_baseline_rows(payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    targets = payload.get("targets") if isinstance(payload, dict) else None
    if not isinstance(targets, list):
        return []
    return [cast(dict[str, Any], row) for row in targets if isinstance(row, dict)]


def build_type_flow_target_baseline_delta_report(
    type_flow_rows: list[dict[str, Any]],
    baseline: dict[str, Any] | list[dict[str, Any]],
    *,
    max_targets: int = 25,
) -> dict[str, object]:
    current = cast(list[dict[str, Any]], build_type_flow_target_baseline_report(type_flow_rows)["targets"])
    before = _type_flow_target_baseline_rows(baseline)
    delta = build_type_flow_report_delta(before, current, max_targets=max_targets)
    return {
        "schema_version": 1,
        "baseline_target_count": len(before),
        "current_target_count": len(current),
        "delta": delta,
    }


def build_type_flow_baseline_gate_report(
    type_flow_rows: list[dict[str, Any]],
    unresolved_typed_field_rows: list[dict[str, Any]],
    xrefs: list[dict[str, Any]],
    baseline: dict[str, Any],
) -> dict[str, object]:
    correctness = build_type_flow_correctness_report(type_flow_rows, unresolved_typed_field_rows, xrefs)
    current = build_type_flow_baseline_report(type_flow_rows)
    current_totals = current.get("totals") if isinstance(current.get("totals"), dict) else {}
    baseline_totals = baseline.get("totals") if isinstance(baseline.get("totals"), dict) else {}
    current_causes = current.get("numeric_cause_counts") if isinstance(current.get("numeric_cause_counts"), dict) else {}
    baseline_causes = baseline.get("numeric_cause_counts") if isinstance(baseline.get("numeric_cause_counts"), dict) else {}
    metric_regressions: list[dict[str, object]] = []
    for key in TYPE_FLOW_BASELINE_MIN_TOTALS:
        current_value = int(current_totals.get(key, 0))
        baseline_value = int(baseline_totals.get(key, 0))
        if current_value < baseline_value:
            metric_regressions.append({
                "kind": "below_baseline_minimum",
                "key": key,
                "current": current_value,
                "baseline": baseline_value,
            })
    for key in TYPE_FLOW_BASELINE_MAX_TOTALS:
        current_value = int(current_totals.get(key, 0))
        baseline_value = int(baseline_totals.get(key, 0))
        if baseline_value != 0 and current_value > baseline_value:
            metric_regressions.append({
                "kind": "above_baseline_maximum",
                "key": key,
                "current": current_value,
                "baseline": baseline_value,
            })
    for key in TYPE_FLOW_BASELINE_MAX_NUMERIC_CAUSES:
        current_value = int(current_causes.get(key, 0))
        baseline_value = int(baseline_causes.get(key, 0))
        if baseline_value != 0 and current_value > baseline_value:
            metric_regressions.append({
                "kind": "numeric_cause_above_baseline_maximum",
                "key": key,
                "current": current_value,
                "baseline": baseline_value,
            })
    return {
        "schema_version": 1,
        "ok": bool(correctness.get("ok")) and not metric_regressions,
        "correctness": correctness,
        "metric_regressions": metric_regressions,
        "current": current,
        "baseline": baseline,
    }


def build_type_flow_report_delta(
    before_rows: list[dict[str, Any]],
    after_rows: list[dict[str, Any]],
    *,
    max_targets: int = 25,
) -> dict[str, object]:
    before_by_target = {
        str(row.get("target_id")): row
        for row in before_rows
        if isinstance(row.get("target_id"), str)
    }
    after_by_target = {
        str(row.get("target_id")): row
        for row in after_rows
        if isinstance(row.get("target_id"), str)
    }
    before_opportunities = sum(_type_flow_int(row, "opportunity_count") for row in before_by_target.values())
    after_opportunities = sum(_type_flow_int(row, "opportunity_count") for row in after_by_target.values())
    before_resolved = sum(_type_flow_int(row, "resolved_typed_access_count") for row in before_by_target.values())
    after_resolved = sum(_type_flow_int(row, "resolved_typed_access_count") for row in after_by_target.values())
    target_deltas: list[dict[str, object]] = []

    for target_id in sorted(set(before_by_target) | set(after_by_target)):
        before_row = before_by_target.get(target_id)
        after_row = after_by_target.get(target_id)
        before_opportunity = _type_flow_int(before_row or {}, "opportunity_count")
        after_opportunity = _type_flow_int(after_row or {}, "opportunity_count")
        before_resolved_count = _type_flow_int(before_row or {}, "resolved_typed_access_count")
        after_resolved_count = _type_flow_int(after_row or {}, "resolved_typed_access_count")
        opportunity_delta = after_opportunity - before_opportunity
        resolved_delta = after_resolved_count - before_resolved_count
        numeric_delta = _type_flow_delta_map(
            _type_flow_count_map(before_row, "numeric_cause_counts"),
            _type_flow_count_map(after_row, "numeric_cause_counts"),
        )
        propagation_delta = _type_flow_delta_map(
            _type_flow_count_map(before_row, "propagation_chain_counts"),
            _type_flow_count_map(after_row, "propagation_chain_counts"),
        )
        pointer_root_delta = _type_flow_delta_map(
            _type_flow_count_map(before_row, "pointer_chain_root_counts"),
            _type_flow_count_map(after_row, "pointer_chain_root_counts"),
        )
        pointer_stop_delta = _type_flow_delta_map(
            _type_flow_count_map(before_row, "pointer_chain_stop_counts"),
            _type_flow_count_map(after_row, "pointer_chain_stop_counts"),
        )
        typed_access_provenance_delta = _type_flow_delta_map(
            _type_flow_count_map(before_row, "typed_access_provenance_counts"),
            _type_flow_count_map(after_row, "typed_access_provenance_counts"),
        )
        typed_storage_provenance_delta = _type_flow_delta_map(
            _type_flow_count_map(before_row, "typed_storage_provenance_counts"),
            _type_flow_count_map(after_row, "typed_storage_provenance_counts"),
        )
        count_delta = _type_flow_delta_map(
            _type_flow_count_map(before_row, "counts"),
            _type_flow_count_map(after_row, "counts"),
        )
        if (
            opportunity_delta == 0
            and resolved_delta == 0
            and not any(item["delta"] != 0 for item in count_delta.values())
            and not any(item["delta"] != 0 for item in numeric_delta.values())
            and not any(item["delta"] != 0 for item in propagation_delta.values())
            and not any(item["delta"] != 0 for item in pointer_root_delta.values())
            and not any(item["delta"] != 0 for item in pointer_stop_delta.values())
            and not any(item["delta"] != 0 for item in typed_access_provenance_delta.values())
            and not any(item["delta"] != 0 for item in typed_storage_provenance_delta.values())
        ):
            continue
        display_row = after_row or before_row or {}
        target_deltas.append(
            {
                "target_id": target_id,
                "source_id": display_row.get("source_id"),
                "platform": display_row.get("platform"),
                "origin": display_row.get("origin") if isinstance(display_row.get("origin"), dict) else {},
                "before_opportunity_count": before_opportunity,
                "after_opportunity_count": after_opportunity,
                "opportunity_delta": opportunity_delta,
                "before_resolved_typed_access_count": before_resolved_count,
                "after_resolved_typed_access_count": after_resolved_count,
                "resolved_typed_access_delta": resolved_delta,
                "count_deltas": count_delta,
                "numeric_cause_deltas": numeric_delta,
                "propagation_chain_deltas": propagation_delta,
                "pointer_chain_root_deltas": pointer_root_delta,
                "pointer_chain_stop_deltas": pointer_stop_delta,
                "typed_access_provenance_deltas": typed_access_provenance_delta,
                "typed_storage_provenance_deltas": typed_storage_provenance_delta,
            }
        )

    target_deltas.sort(
        key=lambda row: (
            -abs(int(row.get("resolved_typed_access_delta", 0))),
            -abs(int(row.get("opportunity_delta", 0))),
            str(row.get("platform")),
            str(row.get("target_id")),
        )
    )
    return {
        "schema_version": 1,
        "before_target_count": len(before_by_target),
        "after_target_count": len(after_by_target),
        "totals": {
            "opportunity_count": {
                "before": before_opportunities,
                "after": after_opportunities,
                "delta": after_opportunities - before_opportunities,
            },
            "resolved_typed_access_count": {
                "before": before_resolved,
                "after": after_resolved,
                "delta": after_resolved - before_resolved,
            },
        },
        "count_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "counts"),
            _type_flow_total_map(after_rows, "counts"),
        ),
        "effectiveness_deltas": _type_flow_delta_map(
            _type_flow_effectiveness_totals(before_rows),
            _type_flow_effectiveness_totals(after_rows),
        ),
        "numeric_cause_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "numeric_cause_counts"),
            _type_flow_total_map(after_rows, "numeric_cause_counts"),
        ),
        "propagation_chain_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "propagation_chain_counts"),
            _type_flow_total_map(after_rows, "propagation_chain_counts"),
        ),
        "pointer_chain_root_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "pointer_chain_root_counts"),
            _type_flow_total_map(after_rows, "pointer_chain_root_counts"),
        ),
        "pointer_chain_stop_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "pointer_chain_stop_counts"),
            _type_flow_total_map(after_rows, "pointer_chain_stop_counts"),
        ),
        "typed_access_provenance_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "typed_access_provenance_counts"),
            _type_flow_total_map(after_rows, "typed_access_provenance_counts"),
        ),
        "typed_storage_provenance_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "typed_storage_provenance_counts"),
            _type_flow_total_map(after_rows, "typed_storage_provenance_counts"),
        ),
        "struct_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "struct_counts"),
            _type_flow_total_map(after_rows, "struct_counts"),
        ),
        "field_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "field_counts"),
            _type_flow_total_map(after_rows, "field_counts"),
        ),
        "target_deltas": target_deltas[:max_targets],
    }


def _suspicious_first_struct_match(text: str) -> str | None:
    lowered = text.lower()
    for name in SUSPICIOUS_FIRST_STRUCT_NAMES:
        if name.lower() in lowered:
            return name
    for prefix in SUSPICIOUS_FIRST_STRUCT_PREFIXES:
        if prefix.lower() in lowered:
            return prefix
    return None


def build_type_flow_suspicious_first_struct_report(
    manifest_rows: list[dict[str, Any]],
    xrefs: list[dict[str, Any]],
    snippet_rows: list[dict[str, Any]],
) -> dict[str, object]:
    manifest_by_id = {
        str(row.get("id")): row
        for row in manifest_rows
        if isinstance(row.get("id"), str)
    }
    examples: list[dict[str, object]] = []
    target_counts: dict[str, int] = {}

    def add_example(target_id: str, match: str, example: dict[str, object]) -> None:
        target_counts[target_id] = target_counts.get(target_id, 0) + 1
        if len(examples) >= MAX_EXAMPLES:
            return
        manifest = manifest_by_id.get(target_id, {})
        payload = {
            "target_id": target_id,
            "source_id": manifest.get("source_id"),
            "platform": manifest.get("platform"),
            "match": match,
        }
        payload.update(example)
        examples.append(_compact_example(payload))

    interesting_kind_ids = {
        XREF_KIND_PLATFORM_TYPED_ACCESS,
        XREF_KIND_PLATFORM_UNRESOLVED_TYPED_ACCESS,
        XREF_KIND_PLATFORM_TYPE_REFINEMENT,
        XREF_KIND_TYPED_STORAGE,
        XREF_KIND_STRUCT,
        XREF_KIND_TYPE,
    }
    for xref in xrefs:
        target_id = _string_value(xref.get("target_id"))
        if target_id is None:
            continue
        kind = _string_value(xref.get("kind")) or ""
        feature = _string_value(xref.get("feature")) or ""
        if (
            _xref_kind_id(xref) not in interesting_kind_ids
            and _xref_feature_class_id(xref) not in {
                XREF_FEATURE_CLASS_STRUCT,
                XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_STRUCT,
                XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_OWNER,
            }
        ):
            continue
        haystack = " ".join(
            str(value)
            for value in (
                xref.get("feature"),
                xref.get("kind"),
                xref.get("symbol"),
                xref.get("value"),
                xref.get("text"),
            )
            if value is not None
        )
        match = _suspicious_first_struct_match(haystack)
        if match is None:
            continue
        add_example(
            target_id,
            match,
            {
                "source": "xref",
                "feature": feature,
                "kind": kind,
                "section": xref.get("section"),
                "offset": xref.get("offset"),
                "row_index": xref.get("row_index"),
                "stable_key": xref.get("stable_key"),
                "text": xref.get("text"),
            },
        )

    for snippet in snippet_rows:
        target_id = _string_value(snippet.get("target_id"))
        row = snippet.get("row")
        if target_id is None or not isinstance(row, dict):
            continue
        text = _string_value(row.get("text")) or ""
        match = _suspicious_first_struct_match(text)
        if match is None:
            continue
        add_example(
            target_id,
            match,
            {
                "source": "listing",
                "section": row.get("section_index"),
                "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                "row_index": snippet.get("row_index"),
                "stable_key": row.get("stable_key"),
                "text": text.strip(),
            },
        )

    return {
        "schema_version": 1,
        "total": sum(target_counts.values()),
        "target_count": len(target_counts),
        "target_counts": dict(sorted(target_counts.items())),
        "examples": examples,
    }


def build_type_flow_correctness_report(
    type_flow_rows: list[dict[str, Any]],
    unresolved_typed_field_rows: list[dict[str, Any]],
    xrefs: list[dict[str, Any]],
) -> dict[str, object]:
    violations: list[dict[str, object]] = []
    suspicious_kind_ids = {
        XREF_KIND_PLATFORM_TYPED_ACCESS,
        XREF_KIND_PLATFORM_UNRESOLVED_TYPED_ACCESS,
        XREF_KIND_PLATFORM_TYPE_REFINEMENT,
        XREF_KIND_TYPED_STORAGE,
        XREF_KIND_STRUCT,
        XREF_KIND_TYPE,
    }
    for row in unresolved_typed_field_rows:
        dominant = row.get("dominant_candidate")
        rankings = row.get("candidate_rankings")
        if not isinstance(dominant, dict) or not isinstance(rankings, list) or len(rankings) <= 1:
            continue
        dominant_exact = _int_value(dominant.get("exact_access_size_match_count"), 0) or 0
        other_exact = max(
            (_int_value(candidate.get("exact_access_size_match_count"), 0) or 0)
            for candidate in rankings[1:]
            if isinstance(candidate, dict)
        )
        if dominant_exact <= other_exact:
            violations.append(
                {
                    "kind": "dominant_candidate_exact_size_tie",
                    "root_struct_name": row.get("root_struct_name"),
                    "displacement_hex": row.get("displacement_hex"),
                    "dominant_struct_name": dominant.get("struct_name"),
                    "dominant_exact_access_size_match_count": dominant_exact,
                    "next_exact_access_size_match_count": other_exact,
                }
            )
    for xref in xrefs:
        kind_id = _xref_kind_id(xref)
        feature_id = _xref_feature_id(xref)
        if (
            kind_id == XREF_KIND_PLATFORM_TYPE_REFINEMENT
            and feature_id == XREF_FEATURE_PLATFORM_TYPE_REFINEMENT_APPLIED
        ):
            if _int_value(xref.get("classification_id")) != UNRESOLVED_TYPED_ACCESS_PREFIX_EXTENSION:
                violations.append(
                    {
                        "kind": "refinement_without_prefix_extension_classification",
                        "target_id": xref.get("target_id"),
                        "row_index": xref.get("row_index"),
                        "text": xref.get("text"),
                    }
                )
            if not _string_value(xref.get("refined_struct_name")):
                violations.append(
                    {
                        "kind": "refinement_without_refined_struct",
                        "target_id": xref.get("target_id"),
                        "row_index": xref.get("row_index"),
                        "text": xref.get("text"),
                    }
                )
            if not _string_value(xref.get("container_field_expr")):
                violations.append(
                    {
                        "kind": "refinement_without_generated_field_expression",
                        "target_id": xref.get("target_id"),
                        "row_index": xref.get("row_index"),
                        "refined_struct_name": xref.get("refined_struct_name"),
                        "text": xref.get("text"),
                    }
                )
        if (
            kind_id in suspicious_kind_ids
            or _xref_feature_class_id(xref) in {
                XREF_FEATURE_CLASS_STRUCT,
                XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_STRUCT,
                XREF_FEATURE_CLASS_PLATFORM_TYPED_ACCESS_OWNER,
            }
        ):
            haystack = " ".join(
                str(value)
                for value in (
                    xref.get("feature"),
                    xref.get("kind"),
                    xref.get("symbol"),
                    xref.get("value"),
                    xref.get("text"),
                )
                if value is not None
            )
            suspicious_match = _suspicious_first_struct_match(haystack)
            if suspicious_match is not None:
                violations.append(
                        {
                            "kind": "suspicious_first_struct_type_flow",
                            "target_id": xref.get("target_id"),
                            "match": suspicious_match,
                            "feature": xref.get("feature"),
                            "xref_kind": xref.get("kind"),
                            "row_index": xref.get("row_index"),
                            "text": xref.get("text"),
                        }
                )
    for row in type_flow_rows:
        counts = row.get("counts") if isinstance(row.get("counts"), dict) else {}
        resolved_after = _int_value(counts.get("resolved_after_type_refinement"), 0) or 0
        resolved = _int_value(counts.get("resolved_typed_access"), 0) or 0
        if resolved_after > resolved:
            violations.append(
                {
                    "kind": "resolved_after_refinement_exceeds_resolved_typed_access",
                    "target_id": row.get("target_id"),
                    "resolved_after_type_refinement": resolved_after,
                    "resolved_typed_access": resolved,
                }
            )
    return {
        "schema_version": 1,
        "ok": not violations,
        "violation_count": len(violations),
        "violations": violations,
        "applied_refinement_count": sum(
            1
            for xref in xrefs
            if _xref_kind_id(xref) == XREF_KIND_PLATFORM_TYPE_REFINEMENT
            and _xref_feature_id(xref) == XREF_FEATURE_PLATFORM_TYPE_REFINEMENT_APPLIED
        ),
        "dominant_candidate_count": sum(
            1 for row in unresolved_typed_field_rows if isinstance(row.get("dominant_candidate"), dict)
        ),
    }


def build_type_flow_gate_report(
    type_flow_rows: list[dict[str, Any]],
    unresolved_typed_field_rows: list[dict[str, Any]],
    xrefs: list[dict[str, Any]],
    *,
    before_rows: list[dict[str, Any]] | None = None,
    fail_on_metric_regression: bool = False,
    max_targets: int = 25,
) -> dict[str, object]:
    correctness = build_type_flow_correctness_report(type_flow_rows, unresolved_typed_field_rows, xrefs)
    delta = (
        build_type_flow_report_delta(before_rows, type_flow_rows, max_targets=max_targets)
        if before_rows is not None
        else None
    )
    metric_regressions: list[dict[str, object]] = []
    if fail_on_metric_regression and isinstance(delta, dict):
        for key in ("resolved_typed_access", "type_refinement_applied", "resolved_after_type_refinement"):
            change = delta.get("effectiveness_deltas", {}).get(key) if isinstance(delta.get("effectiveness_deltas"), dict) else None
            if isinstance(change, dict) and int(change.get("delta", 0)) < 0:
                metric_regressions.append({"key": key, "change": change})
    return {
        "schema_version": 1,
        "ok": bool(correctness.get("ok")) and not metric_regressions,
        "correctness": correctness,
        "delta": delta,
        "metric_regressions": metric_regressions,
    }


def build_type_flow_snapshot_gate_report(
    type_flow_rows: list[dict[str, Any]],
    unresolved_typed_field_rows: list[dict[str, Any]],
    xrefs: list[dict[str, Any]],
    *,
    snapshot_path: Path,
    before_rows: list[dict[str, Any]] | None = None,
    fail_on_metric_regression: bool = False,
    max_targets: int = 25,
) -> dict[str, object]:
    write_type_flow_report(snapshot_path, type_flow_rows)
    gate = build_type_flow_gate_report(
        type_flow_rows,
        unresolved_typed_field_rows,
        xrefs,
        before_rows=before_rows,
        fail_on_metric_regression=fail_on_metric_regression,
        max_targets=max_targets,
    )
    gate["snapshot_path"] = str(snapshot_path)
    return gate


def feature_summary(rows: list[dict[str, Any]]) -> list[dict[str, object]]:
    target_counts: dict[str, int] = {}
    occurrence_counts: dict[str, int] = {}
    for row in rows:
        counts = row.get("feature_counts")
        if not isinstance(counts, dict):
            continue
        for key, value in counts.items():
            if not isinstance(key, str) or not isinstance(value, int):
                continue
            target_counts[key] = target_counts.get(key, 0) + 1
            occurrence_counts[key] = occurrence_counts.get(key, 0) + value
    return [
        {"feature": key, "target_count": target_counts[key], "occurrence_count": occurrence_counts[key]}
        for key in sorted(target_counts)
    ]


def query_usage_manifest(
    rows: list[dict[str, Any]],
    feature: str,
    *,
    group: str | None = None,
    platform: str | None = None,
    q: str | None = None,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    needle = q.casefold().strip() if q else ""
    for row in rows:
        if platform is not None and row.get("platform") != platform:
            continue
        counts = row.get("feature_counts")
        if not isinstance(counts, dict):
            continue
        if feature and feature not in counts:
            continue
        matching_features = _matching_features(counts, feature=feature, group=group)
        if group and not matching_features:
            continue
        haystack = json.dumps(
            {
                "id": row.get("id"),
                "source_id": row.get("source_id"),
                "platform": row.get("platform"),
                "origin": row.get("origin"),
                "tags": row.get("tags"),
            },
            sort_keys=True,
        ).casefold()
        if needle and needle not in haystack:
            continue
        examples = row.get("feature_examples")
        selected_examples: list[object] = []
        if isinstance(examples, dict):
            if feature:
                selected_examples = examples.get(feature, [])
            elif group:
                for key in matching_features:
                    for example in examples.get(key, []):
                        if len(selected_examples) >= MAX_EXAMPLES:
                            break
                        selected_examples.append(example)
        result.append(
            {
                "id": row.get("id"),
                "source_id": row.get("source_id"),
                "platform": row.get("platform"),
                "count": counts.get(feature) if feature else sum(
                    value
                    for key, value in counts.items()
                    if isinstance(key, str)
                    and isinstance(value, int)
                    and (not group or feature_matches_group(key, group))
                ),
                "feature_counts": counts,
                "tags": row.get("tags"),
                "origin": row.get("origin"),
                "examples": selected_examples,
            }
        )
    return sorted(result, key=lambda item: (str(item.get("platform")), str(item.get("id"))))


def query_usage_xrefs(
    xrefs: list[dict[str, Any]],
    *,
    target_id: str | None = None,
    feature: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    q: str | None = None,
) -> list[dict[str, object]]:
    needle = q.casefold().strip() if q else ""
    result: list[dict[str, object]] = []
    for xref in xrefs:
        if target_id is not None and xref.get("target_id") != target_id:
            continue
        if feature is not None and xref.get("feature") != feature:
            continue
        if group is not None and not feature_matches_group(_string_value(xref.get("feature")) or "", group):
            continue
        if platform is not None and xref.get("platform") != platform:
            continue
        if needle and needle not in json.dumps(xref, sort_keys=True).casefold():
            continue
        result.append(cast_xref(xref))
    return sorted(
        result,
        key=lambda row: (
            str(row.get("target_id")),
            str(row.get("feature")),
            _sort_int(row.get("section")),
            _sort_int(row.get("offset")),
            _sort_int(row.get("row_index")),
            str(row.get("id")),
        ),
    )


def feature_matches_group(feature: str, group: str | None) -> bool:
    if not group:
        return True
    prefixes = FEATURE_GROUPS.get(group)
    if prefixes is None:
        return False
    return any(feature.startswith(prefix) for prefix in prefixes)


def _matching_features(counts: dict[object, object], *, feature: str, group: str | None) -> list[str]:
    if feature:
        return [feature] if feature in counts and feature_matches_group(feature, group) else []
    return sorted(
        key
        for key in counts
        if isinstance(key, str) and feature_matches_group(key, group)
    )


def cast_xref(row: dict[str, Any]) -> dict[str, object]:
    return {key: row.get(key) for key in (
        "schema_version",
        "id",
        "target_id",
        "feature",
        "kind",
        "platform",
        "source_id",
        "origin",
        "section",
        "offset",
        "row_index",
        "stable_key",
        "source_stable_key",
        "symbol",
        "access",
        "resolution",
        "value",
        "text",
    )}


def _print_feature_summary(rows: list[dict[str, Any]], *, json_output: bool) -> None:
    summary = feature_summary(rows)
    if json_output:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    for item in summary:
        print(f"{item['target_count']:5d} {item['occurrence_count']:7d} {item['feature']}")


def _print_query(rows: list[dict[str, Any]], feature: str, *, group: str | None, platform: str | None, json_output: bool) -> None:
    matches = query_usage_manifest(rows, feature, group=group, platform=platform)
    if json_output:
        print(json.dumps(matches, indent=2, sort_keys=True))
        return
    for item in matches:
        print(f"{item['platform']} {item['source_id']} count={item['count']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and query corpus-wide target usage features.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--disk-manifest", type=Path, default=DEFAULT_DISK_MANIFEST)
    build.add_argument("--file-manifest", type=Path, default=DEFAULT_FILE_MANIFEST)
    build.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    build.add_argument("--xrefs-output", type=Path, default=DEFAULT_XREF_OUTPUT)
    build.add_argument("--snippet-rows-output", type=Path, default=DEFAULT_SNIPPET_ROWS_OUTPUT)
    build.add_argument("--variants-output", type=Path, default=DEFAULT_VARIANT_OUTPUT)
    build.add_argument("--type-flow-report-output", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    build.add_argument("--unresolved-typed-field-report-output", type=Path,
        default=DEFAULT_UNRESOLVED_TYPED_FIELD_REPORT_OUTPUT)
    build.add_argument("--workers", type=int, default=None,
        help=f"Target analysis workers; default uses {TARGET_USAGE_WORKERS_ENV} or up to 8")

    list_features = subparsers.add_parser("list-features")
    list_features.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    list_features.add_argument("--json", action="store_true")

    query = subparsers.add_parser("query")
    query.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    query.add_argument("--feature", default="")
    query.add_argument("--group")
    query.add_argument("--platform")
    query.add_argument("--json", action="store_true")

    type_flow_report = subparsers.add_parser("type-flow-report")
    type_flow_report.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    type_flow_report.add_argument("--xrefs", type=Path, default=DEFAULT_XREF_OUTPUT)
    type_flow_report.add_argument("--snippet-rows", type=Path, default=DEFAULT_SNIPPET_ROWS_OUTPUT)
    type_flow_report.add_argument("--output", type=Path)
    type_flow_report.add_argument("--json", action="store_true")

    unresolved_typed_fields = subparsers.add_parser("unresolved-typed-fields")
    unresolved_typed_fields.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    unresolved_typed_fields.add_argument("--xrefs", type=Path, default=DEFAULT_XREF_OUTPUT)
    unresolved_typed_fields.add_argument("--snippet-rows", type=Path, default=DEFAULT_SNIPPET_ROWS_OUTPUT)
    unresolved_typed_fields.add_argument("--output", type=Path)
    unresolved_typed_fields.add_argument("--json", action="store_true")

    type_flow_delta = subparsers.add_parser("type-flow-delta")
    type_flow_delta.add_argument("--before", type=Path, required=True)
    type_flow_delta.add_argument("--after", type=Path, required=True)
    type_flow_delta.add_argument("--output", type=Path)
    type_flow_delta.add_argument("--max-targets", type=int, default=25)
    type_flow_delta.add_argument("--json", action="store_true")

    type_flow_opportunities = subparsers.add_parser("type-flow-opportunities")
    type_flow_opportunities.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_opportunities.add_argument("--output", type=Path)
    type_flow_opportunities.add_argument("--max-targets", type=int, default=25)
    type_flow_opportunities.add_argument("--platform")
    type_flow_opportunities.add_argument("--json", action="store_true")

    type_flow_api_audit = subparsers.add_parser("type-flow-api-audit")
    type_flow_api_audit.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_api_audit.add_argument("--api-feature")
    type_flow_api_audit.add_argument("--output", type=Path)
    type_flow_api_audit.add_argument("--max-targets", type=int, default=25)
    type_flow_api_audit.add_argument("--json", action="store_true")

    type_flow_chain_slices = subparsers.add_parser("type-flow-chain-slices")
    type_flow_chain_slices.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_chain_slices.add_argument("--output", type=Path)
    type_flow_chain_slices.add_argument("--max-slices", type=int, default=25)
    type_flow_chain_slices.add_argument("--platform")
    type_flow_chain_slices.add_argument("--json", action="store_true")

    type_flow_storage_access_gaps = subparsers.add_parser("type-flow-storage-access-gaps")
    type_flow_storage_access_gaps.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_storage_access_gaps.add_argument("--xrefs", type=Path, default=DEFAULT_XREF_OUTPUT)
    type_flow_storage_access_gaps.add_argument("--snippet-rows", type=Path, default=DEFAULT_SNIPPET_ROWS_OUTPUT)
    type_flow_storage_access_gaps.add_argument("--output", type=Path)
    type_flow_storage_access_gaps.add_argument("--platform")
    type_flow_storage_access_gaps.add_argument("--api-feature")
    type_flow_storage_access_gaps.add_argument("--storage-target")
    type_flow_storage_access_gaps.add_argument("--window", type=int, default=500)
    type_flow_storage_access_gaps.add_argument("--max-targets", type=int, default=25)
    type_flow_storage_access_gaps.add_argument("--max-examples", type=int, default=5)
    type_flow_storage_access_gaps.add_argument("--json", action="store_true")

    type_flow_baseline = subparsers.add_parser("type-flow-baseline")
    type_flow_baseline.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_baseline.add_argument("--output", type=Path, default=DEFAULT_TYPE_FLOW_BASELINE)
    type_flow_baseline.add_argument("--json", action="store_true")

    type_flow_target_baseline = subparsers.add_parser("type-flow-target-baseline")
    type_flow_target_baseline.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_target_baseline.add_argument("--output", type=Path, required=True)
    type_flow_target_baseline.add_argument("--json", action="store_true")

    type_flow_target_baseline_delta = subparsers.add_parser("type-flow-target-baseline-delta")
    type_flow_target_baseline_delta.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_target_baseline_delta.add_argument("--baseline", type=Path, required=True)
    type_flow_target_baseline_delta.add_argument("--output", type=Path)
    type_flow_target_baseline_delta.add_argument("--max-targets", type=int, default=25)
    type_flow_target_baseline_delta.add_argument("--json", action="store_true")

    type_flow_baseline_check = subparsers.add_parser("type-flow-baseline-check")
    type_flow_baseline_check.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_baseline_check.add_argument("--unresolved-typed-fields", type=Path,
        default=DEFAULT_UNRESOLVED_TYPED_FIELD_REPORT_OUTPUT)
    type_flow_baseline_check.add_argument("--xrefs", type=Path, default=DEFAULT_XREF_OUTPUT)
    type_flow_baseline_check.add_argument("--baseline", type=Path, default=DEFAULT_TYPE_FLOW_BASELINE)
    type_flow_baseline_check.add_argument("--output", type=Path)
    type_flow_baseline_check.add_argument("--json", action="store_true")

    type_flow_check = subparsers.add_parser("type-flow-check")
    type_flow_check.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_check.add_argument("--unresolved-typed-fields", type=Path,
        default=DEFAULT_UNRESOLVED_TYPED_FIELD_REPORT_OUTPUT)
    type_flow_check.add_argument("--xrefs", type=Path, default=DEFAULT_XREF_OUTPUT)
    type_flow_check.add_argument("--before", type=Path)
    type_flow_check.add_argument("--output", type=Path)
    type_flow_check.add_argument("--max-targets", type=int, default=25)
    type_flow_check.add_argument("--fail-on-metric-regression", action="store_true")
    type_flow_check.add_argument("--json", action="store_true")

    suspicious_first_struct = subparsers.add_parser("type-flow-suspicious-first-struct")
    suspicious_first_struct.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    suspicious_first_struct.add_argument("--xrefs", type=Path, default=DEFAULT_XREF_OUTPUT)
    suspicious_first_struct.add_argument("--snippet-rows", type=Path, default=DEFAULT_SNIPPET_ROWS_OUTPUT)
    suspicious_first_struct.add_argument("--output", type=Path)
    suspicious_first_struct.add_argument("--json", action="store_true")

    type_flow_snapshot = subparsers.add_parser("type-flow-snapshot")
    type_flow_snapshot.add_argument("--report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_snapshot.add_argument("--output-dir", type=Path, default=DEFAULT_TYPE_FLOW_SNAPSHOT_DIR)
    type_flow_snapshot.add_argument("--name", required=True)
    type_flow_snapshot.add_argument("--json", action="store_true")

    type_flow_snapshot_check = subparsers.add_parser("type-flow-snapshot-check")
    type_flow_snapshot_check.add_argument("--type-flow-report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_snapshot_check.add_argument("--unresolved-typed-fields", type=Path,
        default=DEFAULT_UNRESOLVED_TYPED_FIELD_REPORT_OUTPUT)
    type_flow_snapshot_check.add_argument("--xrefs", type=Path, default=DEFAULT_XREF_OUTPUT)
    type_flow_snapshot_check.add_argument("--before", type=Path)
    type_flow_snapshot_check.add_argument("--output-dir", type=Path, default=DEFAULT_TYPE_FLOW_SNAPSHOT_DIR)
    type_flow_snapshot_check.add_argument("--name", required=True)
    type_flow_snapshot_check.add_argument("--output", type=Path)
    type_flow_snapshot_check.add_argument("--max-targets", type=int, default=25)
    type_flow_snapshot_check.add_argument("--fail-on-metric-regression", action="store_true")
    type_flow_snapshot_check.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "build":
        rows, xrefs, snippet_rows = build_usage_outputs(args.disk_manifest, args.file_manifest, max_workers=args.workers)
        variant_rows = build_variant_index(args.file_manifest)
        type_flow_rows = build_type_flow_report(rows, xrefs, snippet_rows)
        unresolved_typed_field_rows = build_unresolved_typed_field_report(rows, xrefs, snippet_rows)
        write_usage_manifest(args.output, rows)
        write_usage_xrefs(args.xrefs_output, xrefs)
        write_usage_snippet_rows(args.snippet_rows_output, snippet_rows)
        write_variant_index(args.variants_output, variant_rows)
        write_type_flow_report(args.type_flow_report_output, type_flow_rows)
        write_unresolved_typed_field_report(args.unresolved_typed_field_report_output, unresolved_typed_field_rows)
        print(f"Wrote {args.output}")
        print(f"Wrote {args.xrefs_output}")
        print(f"Wrote {snippet_rows_index_path(args.snippet_rows_output)}")
        print(f"Wrote {snippet_rows_blob_path(args.snippet_rows_output)}")
        print(f"Wrote {args.variants_output}")
        print(f"Wrote {args.type_flow_report_output}")
        print(f"Wrote {args.unresolved_typed_field_report_output}")
        print(f"Entries: {len(rows)}")
        print(f"Xrefs: {len(xrefs)}")
        print(f"Snippet rows: {len(snippet_rows)}")
        print(f"Variants: {len(variant_rows)}")
        print(f"Type-flow report rows: {len(type_flow_rows)}")
        print(f"Unresolved typed field report rows: {len(unresolved_typed_field_rows)}")
        return 0
    if args.command == "list-features":
        rows = read_usage_manifest(args.manifest)
        _print_feature_summary(rows, json_output=bool(args.json))
        return 0
    if args.command == "query":
        rows = read_usage_manifest(args.manifest)
        _print_query(rows, args.feature, group=args.group, platform=args.platform, json_output=bool(args.json))
        return 0
    if args.command == "type-flow-report":
        rows = read_usage_manifest(args.manifest)
        type_flow_rows = build_type_flow_report(rows, read_usage_xrefs(args.xrefs), read_usage_snippet_rows(args.snippet_rows))
        if args.output is not None:
            write_type_flow_report(args.output, type_flow_rows)
        if args.json or args.output is None:
            print(json.dumps(type_flow_rows, indent=2, sort_keys=True))
        return 0
    if args.command == "unresolved-typed-fields":
        rows = read_usage_manifest(args.manifest)
        report_rows = build_unresolved_typed_field_report(
            rows,
            read_usage_xrefs(args.xrefs),
            read_usage_snippet_rows(args.snippet_rows),
        )
        if args.output is not None:
            write_unresolved_typed_field_report(args.output, report_rows)
        if args.json or args.output is None:
            print(json.dumps(report_rows, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-delta":
        delta = build_type_flow_report_delta(
            read_type_flow_report(args.before),
            read_type_flow_report(args.after),
            max_targets=max(0, int(args.max_targets)),
        )
        if args.output is not None:
            write_type_flow_delta(args.output, delta)
        if args.json or args.output is None:
            print(json.dumps(delta, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-opportunities":
        report = build_type_flow_opportunity_report(
            read_type_flow_report(args.type_flow_report),
            max_targets=max(0, int(args.max_targets)),
            platform=args.platform if isinstance(args.platform, str) else None,
        )
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.json or args.output is None:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-api-audit":
        report = build_type_flow_api_audit_report(
            read_type_flow_report(args.type_flow_report),
            api_feature=args.api_feature if isinstance(args.api_feature, str) else None,
            max_targets=max(0, int(args.max_targets)),
        )
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.json or args.output is None:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-chain-slices":
        report = build_type_flow_chain_slice_report(
            read_type_flow_report(args.type_flow_report),
            max_slices=max(0, int(args.max_slices)),
            platform=args.platform if isinstance(args.platform, str) else None,
        )
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.json or args.output is None:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-storage-access-gaps":
        report = build_type_flow_storage_access_gap_report(
            read_type_flow_report(args.type_flow_report),
            read_usage_xrefs(args.xrefs),
            read_usage_snippet_rows(args.snippet_rows),
            platform=args.platform if isinstance(args.platform, str) else None,
            api_feature=args.api_feature if isinstance(args.api_feature, str) else None,
            storage_target=args.storage_target if isinstance(args.storage_target, str) else None,
            max_targets=max(0, int(args.max_targets)),
            max_examples=max(0, int(args.max_examples)),
            window=max(0, int(args.window)),
        )
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.json or args.output is None:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-baseline":
        report = build_type_flow_baseline_report(read_type_flow_report(args.type_flow_report))
        write_type_flow_baseline(args.output, report)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"Wrote {args.output}")
        return 0
    if args.command == "type-flow-target-baseline":
        report = build_type_flow_target_baseline_report(read_type_flow_report(args.type_flow_report))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"Wrote {args.output}")
        return 0
    if args.command == "type-flow-target-baseline-delta":
        report = build_type_flow_target_baseline_delta_report(
            read_type_flow_report(args.type_flow_report),
            read_type_flow_baseline(args.baseline),
            max_targets=max(0, int(args.max_targets)),
        )
        if args.output is not None:
            write_type_flow_delta(args.output, report)
        if args.json or args.output is None:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-baseline-check":
        gate = build_type_flow_baseline_gate_report(
            read_type_flow_report(args.type_flow_report),
            read_unresolved_typed_field_report(args.unresolved_typed_fields),
            read_usage_xrefs(args.xrefs),
            read_type_flow_baseline(args.baseline),
        )
        if args.output is not None:
            write_type_flow_delta(args.output, gate)
        if args.json or args.output is None:
            print(json.dumps(gate, indent=2, sort_keys=True))
        return 0 if gate.get("ok") is True else 1
    if args.command == "type-flow-check":
        gate = build_type_flow_gate_report(
            read_type_flow_report(args.type_flow_report),
            read_unresolved_typed_field_report(args.unresolved_typed_fields),
            read_usage_xrefs(args.xrefs),
            before_rows=read_type_flow_report(args.before) if args.before is not None else None,
            fail_on_metric_regression=bool(args.fail_on_metric_regression),
            max_targets=max(0, int(args.max_targets)),
        )
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.json or args.output is None:
            print(json.dumps(gate, indent=2, sort_keys=True))
        return 0 if gate.get("ok") is True else 1
    if args.command == "type-flow-suspicious-first-struct":
        report = build_type_flow_suspicious_first_struct_report(
            read_usage_manifest(args.manifest),
            read_usage_xrefs(args.xrefs),
            read_usage_snippet_rows(args.snippet_rows),
        )
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.json or args.output is None:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-snapshot":
        snapshot_path = write_type_flow_snapshot(args.report, args.output_dir, name=str(args.name))
        if args.json:
            print(json.dumps({"path": str(snapshot_path)}, indent=2, sort_keys=True))
        else:
            print(f"Wrote {snapshot_path}")
        return 0
    if args.command == "type-flow-snapshot-check":
        snapshot_path = type_flow_snapshot_path(args.output_dir, str(args.name))
        gate = build_type_flow_snapshot_gate_report(
            read_type_flow_report(args.type_flow_report),
            read_unresolved_typed_field_report(args.unresolved_typed_fields),
            read_usage_xrefs(args.xrefs),
            snapshot_path=snapshot_path,
            before_rows=read_type_flow_report(args.before) if args.before is not None else None,
            fail_on_metric_regression=bool(args.fail_on_metric_regression),
            max_targets=max(0, int(args.max_targets)),
        )
        if args.output is not None:
            write_type_flow_delta(args.output, gate)
        if args.json or args.output is None:
            print(json.dumps(gate, indent=2, sort_keys=True))
        return 0 if gate.get("ok") is True else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
