from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.scripts import target_usage_manifest as usage
from src.scripts.platform_manifest_io import sha256


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


class TargetUsageManifestTests(unittest.TestCase):
    def test_feature_bag_derives_target_pattern_tags_from_evidence(self) -> None:
        bag = usage.FeatureBag()
        bag.add("table:kind:relative_code_dispatch", example={"offset": 0x20})
        bag.add("runtime:copied_code")
        bag.add("low-vector-trampoline", example={"runtime_address": 4})
        bag.add("decompression:runtime_copy_conflicting", example={"runtime_copy_address": 0x4000})
        bag.add("orphan-code:signal", example={"offset": 0x80})

        counts, examples, tags = bag.row_features()

        self.assertEqual(counts["target-pattern:relative_lookup_dispatch"], 1)
        self.assertEqual(counts["target-pattern:runtime_copied_code"], 1)
        self.assertEqual(counts["target-pattern:weak_low_trampoline"], 1)
        self.assertEqual(counts["target-pattern:packed_runtime_copy"], 1)
        self.assertEqual(counts["target-pattern:packed_runtime_copy_conflict"], 1)
        self.assertEqual(counts["target-pattern:orphan_code_signal"], 1)
        self.assertIn("target-pattern:relative_lookup_dispatch", tags)
        self.assertEqual(
            examples["target-pattern:relative_lookup_dispatch"][0]["evidence_feature"],
            "table:kind:relative_code_dispatch",
        )

    def test_orphan_signal_features_use_status_id_for_suppressed_signal(self) -> None:
        bag = usage.FeatureBag()
        usage._add_orphan_code_signal_features(
            bag,
            0,
            {
                "offset": 0x20,
                "size": 4,
                "terminal_offset": 0x22,
                "terminal_flow_kind": 5,
                "terminal_flow": "stale_display_name",
                "reason_id": 1,
                "reason": "stale_display_name",
                "status_id": 3,
                "status": "stale_display_name",
                "context_id": 1,
                "context": "stale_display_name",
                "missing_inbound_id": 2,
                "missing_inbound": "stale_display_name",
                "nearby_data_flags": 8,
                "nearby_data_class": "stale_display_name",
                "nearby_data_relation": "overlap",
            },
        )
        counts, examples, _tags = bag.row_features()
        self.assertEqual(counts["orphan-code:status:suppressed"], 1)
        self.assertEqual(counts["orphan-code:terminal_decode:suppressed"], 1)
        self.assertEqual(counts["orphan-code:terminal_flow:return"], 1)
        self.assertEqual(counts["orphan-code:nearby_data:lookup_table"], 1)
        self.assertEqual(counts["orphan-code:nearby_data:overlap:lookup_table"], 1)
        self.assertEqual(examples["orphan-code:signal"][0]["nearby_data_class"], "lookup_table")

    def test_extracts_structured_analysis_and_listing_features(self) -> None:
        bag = usage.FeatureBag()
        usage._add_executable_analysis_features(
            {
                "profile": {"generation": "facts_v2_full_listing"},
                "analysis": {
                    "findings": {"required_cpu": 2, "cpu_violation_count": 1},
                    "packed_payloads": [
                        {
                            "found": True,
                            "provider_id": "ancient-cli",
                            "codec_id": "rnc1-old",
                            "source_section": 0,
                            "source_section_offset": 0x4C40,
                            "packed_size": 168391,
                            "decompressed_size": 359600,
                            "decompressed_sha256": "d37ec7db83012eba179956026b0677cfd46763d585722154f761bd6f6d2b5748",
                        }
                    ],
                    "derived_target_suggestions": [
                        {
                            "kind": "decompressed_payload",
                            "status": "materializable",
                            "reason": "initial_control_target_validated_runtime_copy",
                            "source_section": 0,
                            "source_section_offset": 0x4C40,
                            "packed_size": 168391,
                            "load_address": 0x4000,
                            "entrypoint": 0x4000,
                            "initial_control_target": 0x9B3A,
                            "runtime_copy_address": 0x4000,
                            "runtime_copy_size": 168396,
                            "runtime_copy_kind": 3,
                            "runtime_copy_conflicting": True,
                        }
                    ],
                    "table_candidate_records": [
                        {
                            "section_index": 0,
                            "offset": 0x120,
                            "source_offset": 0x120,
                            "source_size": 4,
                            "operand_index": 0,
                            "flow_kind": 2,
                            "flow": "stale_display_name",
                            "shape_id": 4,
                            "shape": "stale_display_name",
                            "status_id": 1,
                            "status": "stale_display_name",
                            "source_pattern": "stale_display_name",
                            "conflict_state_id": 2,
                            "conflict_state": "unresolved",
                            "table_offset": 0x160,
                            "table_size": 2,
                            "table_entry_size": 2,
                            "table_entry_count": 1,
                            "table_bounds_status_id": 1,
                            "table_bounds_status": "stale_display_name",
                            "detail": "indexed dispatch candidate",
                            "target": None,
                            "target_count": None,
                        }
                    ],
                    "table_records": [
                        {
                            "section_index": 0,
                            "offset": 0x90,
                            "size": 4,
                            "entry_size": 2,
                            "entry_count": 2,
                            "role": "lookup_table",
                            "table_kind": "relative_code_dispatch",
                            "source_pattern": "indexed_word_dispatch",
                            "base_expression": "target_label",
                            "target_section": 0,
                            "target_offset": 0x94,
                            "consumer_section": 0,
                            "consumer_offset": 0x20,
                            "confidence": "tool_inferred",
                            "conflicted": False,
                            "conflict_state_id": 0,
                            "conflict_state": "clean",
                        }
                    ],
                    "memory_layout_records": [
                        {
                            "record_kind_id": 1,
                            "record_kind": "stale_display_name",
                            "memory_kind": "stale_display_name",
                            "layout_name": "app",
                            "base_symbol": "app",
                            "sizeof_symbol": "app_SIZEOF",
                            "field_count": 1,
                            "range_space_kind": 1,
                            "range_start": 0x234,
                            "range_size": 4,
                            "range_end": 0x238,
                        },
                        {
                            "record_kind_id": 2,
                            "record_kind": "base_layout_field",
                            "memory_kind": "stale_display_name",
                            "layout_name": "app",
                            "base_symbol": "app",
                            "symbol": "app_0234",
                            "owner_struct_name": "AppState",
                            "section_index": 0,
                            "source_offset": 0x30,
                            "field_offset": 0x234,
                            "field_size": 4,
                            "alias": False,
                            "range_space_kind": 1,
                            "range_start": 0x234,
                            "range_size": 4,
                            "range_end": 0x238,
                        },
                        {
                            "record_kind_id": 6,
                            "record_kind": "runtime_view",
                            "memory_kind": "runtime_view_candidate",
                            "section_index": 0,
                            "source_offset": 0x40,
                            "source_size": 0x20,
                            "runtime_address": 0x400,
                            "runtime_size": 0x20,
                            "range_space_kind": 2,
                            "range_start": 0x400,
                            "range_size": 0x20,
                            "range_end": 0x420,
                        },
                        {
                            "record_kind_id": 7,
                            "record_kind": "runtime_address_ref",
                            "memory_kind": "copper_list",
                            "section_index": 0,
                            "source_offset": 0x60,
                            "source_size": 12,
                            "runtime_address": 0x0E,
                            "runtime_size": 12,
                            "target_offset": 0x0E,
                            "sink_address": 0xDFF080,
                            "data_class_flags": 1,
                            "range_space_kind": 2,
                            "range_start": 0x0E,
                            "range_size": 12,
                            "range_end": 0x1A,
                        },
                        {
                            "record_kind_id": 8,
                            "record_kind": "absolute_memory_ref",
                            "memory_kind": "hardware_register",
                            "section_index": 0,
                            "source_offset": 0x60,
                            "source_size": 8,
                            "operand_index": 1,
                            "access": "memory_write",
                            "access_width": 2,
                            "address": 0xDFF09A,
                            "owner_kind_id": 3,
                            "owner_kind": "hardware_register",
                            "owner_symbol": "intena",
                            "owner_base_symbol": "_custom",
                            "owner_offset": 0x9A,
                            "range_space_kind": 3,
                            "range_start": 0xDFF09A,
                            "range_size": 2,
                            "range_end": 0xDFF09C,
                            "confidence": 2,
                            "conflicted": True,
                            "conflict_state_id": 1,
                            "conflict_state": "code_overlap",
                        },
                        {
                            "record_kind_id": 4,
                            "record_kind": "platform_typed_access",
                            "memory_kind": "platform_struct_field",
                            "section_index": 0,
                            "source_offset": 0x34,
                            "operand_index": 1,
                            "base_register": "A0",
                            "displacement": 20,
                            "field_offset": 20,
                            "root_struct_name": "Library",
                            "owner_struct_name": "Library",
                            "field_name": "LIB_VERSION",
                            "field_expr": "LIB_VERSION",
                            "type_provenance_kind": "api_output",
                            "range_space_kind": 1,
                            "range_start": 20,
                            "range_size": 2,
                            "range_end": 22,
                        },
                        {
                            "record_kind_id": 3,
                            "record_kind": "platform_storage_effect",
                            "memory_kind": "typed_global_slot",
                            "section_index": 0,
                            "source_offset": 0x34,
                            "effect_kind": 7,
                            "effect_kind_name": "write_typed_global_slot",
                            "displacement": -32768,
                            "field_disp": -32768,
                            "base_name": "exec.library",
                            "symbol_name": "MP_SIGBIT",
                            "type_name": "MP",
                            "target_section_index": 0,
                            "target_offset": 0x100,
                            "range_space_kind": 4,
                            "range_start": 0x100,
                            "range_size": 4,
                            "range_end": 0x104,
                        },
                        {
                            "record_kind_id": 5,
                            "record_kind": "platform_unresolved_typed_access",
                            "memory_kind": "platform_struct_unresolved",
                            "section_index": 0,
                            "source_offset": 0x38,
                            "operand_index": 0,
                            "base_register": "A1",
                            "displacement": 36,
                            "struct_size": 22,
                            "classification_id": 0,
                            "classification": "field_gap",
                            "root_struct_name": "InputEvent",
                            "type_provenance_kind": "unknown",
                            "range_space_kind": 1,
                            "range_start": 36,
                            "range_size": 22,
                            "range_end": 58,
                        },
                    ],
                    "sections": [
                        {
                            "section_index": 0,
                            "recovered_platform_calls": [
                                {
                                    "offset": 0x20,
                                    "library_name": "exec.library",
                                    "function_name": "AllocMem",
                                    "available_since": "1.3",
                                    "inputs": [
                                        {
                                            "name": "attributes",
                                            "value_domain": "exec.allocmem.attributes",
                                            "i_struct": "MemHeader",
                                        }
                                    ],
                                    "outputs": [
                                        {
                                            "name": "memory",
                                            "regs": ["D0"],
                                            "type": "APTR",
                                            "o_struct": "MemHeader",
                                            "value_domain": "exec.allocmem.result",
                                        }
                                    ],
                                },
                                {
                                    "offset": 0x24,
                                    "library_name": "exec.library",
                                    "function_name": "OpenDevice",
                                    "device_name": "input.device",
                                },
                            ],
                            "recovered_platform_effects": [
                                {
                                    "offset": 0x30,
                                    "kind": 2,
                                    "displacement": 0x120,
                                    "base_name": "DOSBase",
                                    "semantic_kind": "library_base",
                                    "value_domain_name": "dos.mode",
                                    "type_name": "struct FileHandle *",
                                },
                                {
                                    "offset": 0x32,
                                    "kind": 7,
                                    "target_section_index": 0,
                                    "target_offset": 0x200,
                                    "base_name": "TimerBase",
                                    "type_name": "Device",
                                }
                            ],
                            "recovered_platform_typed_accesses": [
                                {
                                    "offset": 0x34,
                                    "operand_index": 1,
                                    "base_register": "A0",
                                    "displacement": 20,
                                    "field_offset": 20,
                                    "root_struct_name": "Library",
                                    "owner_struct_name": "Library",
                                    "field_name": "LIB_VERSION",
                                    "field_expr": "LIB_VERSION",
                                    "inherited": False,
                                    "nested": False,
                                    "type_provenance_kind": "api_output",
                                    "type_provenance_section": 0,
                                    "type_provenance_offset": 0x20,
                                }
                            ],
                            "recovered_platform_unresolved_typed_accesses": [
                                {
                                    "offset": 0x38,
                                    "operand_index": 0,
                                    "base_register": "A1",
                                    "displacement": 36,
                                    "struct_size": 22,
                                    "root_struct_name": "InputEvent",
                                }
                            ],
                            "app_slot_refs": [
                                {"offset": 0x40, "displacement": 0x234, "access": "read-write"}
                            ],
                            "runtime_views": [
                                {
                                    "storage_offset": 0x50,
                                    "storage_address": 0x50,
                                    "runtime_address": 0x400,
                                    "kind": 2,
                                    "size": 0x20,
                                    "materialized": False,
                                    "materialization_reason": 103,
                                    "relationship_kind": 1,
                                    "relationship_kind_name": "exits_to_larger_runtime_range",
                                    "related_runtime_address": 0x800,
                                }
                            ],
                            "orphan_code_signals": [
                                {
                                    "offset": 0x84,
                                    "size": 4,
                                    "terminal_offset": 0x86,
                                    "terminal_flow_kind": 5,
                                    "terminal_flow": "stale_display_name",
                                    "required_cpu": 0,
                                    "instruction_count": 2,
                                    "decode_conflict_count": 0,
                                    "reason_id": 1,
                                    "reason": "stale_display_name",
                                    "status_id": 1,
                                    "status": "stale_display_name",
                                    "context_id": 1,
                                    "context": "stale_display_name",
                                    "missing_inbound_id": 2,
                                    "missing_inbound": "stale_display_name",
                                    "nearby_data_flags": 8,
                                    "nearby_data_class": "stale_display_name",
                                    "nearby_data_relation": "after",
                                    "confidence": 60,
                                    "detail": "terminal decode after data label",
                                }
                            ],
                            "violation_count": 2,
                            "recovered_indirect_site_count": 2,
                            "recovered_indirect_sites": [
                                {
                                    "offset": 0x120,
                                    "flow_kind": 2,
                                    "flow": "stale_display_name",
                                    "shape_id": 4,
                                    "shape": "stale_display_name",
                                    "status_id": 1,
                                    "status": "stale_display_name",
                                    "detail": "indexed dispatch candidate",
                                    "target": None,
                                    "target_count": None,
                                },
                                {
                                    "offset": 0x140,
                                    "flow_kind": 2,
                                    "flow": "stale_display_name",
                                    "shape_id": 3,
                                    "shape": "stale_display_name",
                                    "status_id": 6,
                                    "status": "stale_display_name",
                                    "target": 0x180,
                                    "target_count": 3,
                                },
                            ],
                            "recovered_string_ref_count": 4,
                        }
                    ],
                },
                "listing": {
                    "rows": [
                        {
                            "kind": "label",
                            "text": "loc_0_00000020:\n",
                            "section_index": 0,
                            "start_offset": 0x20,
                        },
                        {
                            "kind": "directive",
                            "text": "\tORG $400\n",
                            "section_index": 0,
                            "start_offset": 0x50,
                            "opcode_or_directive": "ORG",
                            "operand_text": "$400",
                        },
                        {
                            "kind": "data",
                            "text": "\tdc.w bplcon0,BPU2|BPU1|COLORON\n",
                            "section_index": 0,
                            "start_offset": 0x60,
                            "data_class": "copper_list",
                            "data_class_flags": 1,
                        },
                        {
                            "kind": "instruction",
                            "text": "\tmove.w #$1234,_custom+aud0+ac_len.l\n",
                            "section_index": 0,
                            "start_offset": 0x70,
                            "app_slot_refs": [
                                {"symbol": "app_0234", "displacement": 0x234, "access": "write"}
                            ],
                            "typed_accesses": [
                                {
                                    "operand_index": 1,
                                    "base_register": "A1",
                                    "displacement": 28,
                                    "field_offset": 28,
                                    "root_struct_name": "IO",
                                    "owner_struct_name": "IO",
                                    "field_name": "IO_COMMAND",
                                    "field_expr": "IO_COMMAND",
                                    "inherited": False,
                                    "nested": False,
                                    "type_provenance_kind": "lookup_storage",
                                    "type_provenance_section": 0,
                                    "type_provenance_offset": 0x30,
                                }
                            ],
                        },
                        {
                            "kind": "instruction",
                            "text": "\tbsr.w loc_0_00000090\n",
                            "section_index": 0,
                            "start_offset": 0x74,
                            "operand_parts": [
                                {
                                    "kind": "symbol",
                                    "text": "loc_0_00000090",
                                    "segment_addr": 0x90,
                                    "metadata": {"symbol": "loc_0_00000090"},
                                }
                            ],
                        },
                        {
                            "kind": "directive",
                            "text": "stack_top_00080000\tEQU\t$80000\n",
                            "section_index": 0,
                        },
                        {
                            "kind": "instruction",
                            "text": "\tlea.l stack_top_00080000.l,a7\n",
                            "section_index": 0,
                            "start_offset": 0x78,
                        },
                        {
                            "kind": "instruction",
                            "text": "\tlea.l abs_0_0000C266-4.l,a0\n",
                            "section_index": 0,
                            "start_offset": 0x7C,
                        },
                        {
                            "kind": "directive",
                            "text": "\tFPU     3\n",
                            "section_index": 0,
                            "start_offset": 0x80,
                            "opcode_or_directive": "FPU",
                        },
                    ],
                    "app_slot_analysis": {
                        "regions": [
                            {
                                "source": "platform_api_arg",
                                "symbol": "app_input_event",
                                "offset": 0x100,
                                "end": 0x116,
                                "struct_name": "InputEvent",
                                "field_refs": [
                                    {
                                        "symbol": "app_input_event_code",
                                        "field_offset": 6,
                                        "field_name": "ie_Code",
                                        "field_path": ["ie_Code"],
                                    }
                                ],
                            }
                        ],
                        "field_gaps": [
                            {
                                "region_id": "app_slot_region_0100_InputEvent",
                                "struct_name": "InputEvent",
                                "start": 0x108,
                                "end": 0x10A,
                                "size": 2,
                                "coverage": "known_struct_field",
                                "field_name": "ie_Qualifier",
                                "field_path": ["ie_Qualifier"],
                            }
                        ],
                        "gaps": [
                            {
                                "start": 0x116,
                                "end": 0x120,
                                "size": 10,
                                "coverage": "unknown_app_slot_space",
                            }
                        ],
                        "suggestions": [
                            {
                                "kind": "app_slot_region",
                                "action": "add_target_metadata",
                                "metadata": {
                                    "symbol": "app_input_event",
                                    "offset": 0x100,
                                    "size": 22,
                                    "struct_name": "InputEvent",
                                },
                            }
                        ],
                        "untyped_api_args": [
                            {
                                "symbol": "app_key_buffer",
                                "displacement": 0x140,
                                "function": "RawKeyConvert",
                                "input_name": "buffer",
                                "register": "A1",
                                "type_name": "STRPTR",
                                "reason": "missing_struct_metadata",
                            }
                        ],
                    },
                },
            },
            bag,
            platform="amiga-hunk",
            root=usage.ROOT,
        )

        counts, examples, tags = bag.row_features()

        self.assertEqual(counts["os:exec.library/AllocMem"], 1)
        self.assertEqual(counts["os_call:any"], 2)
        self.assertEqual(counts["os_call_library:exec.library"], 2)
        self.assertEqual(counts["os_library:exec.library"], 2)
        self.assertEqual(counts["device_call:any"], 1)
        self.assertEqual(counts["device_call_function:OpenDevice"], 1)
        self.assertEqual(counts["device:input.device"], 1)
        self.assertEqual(counts["device_call:input.device/OpenDevice"], 1)
        self.assertEqual(counts["cpu:68020"], 1)
        self.assertEqual(counts["diagnostic:cpu_violation"], 1)
        self.assertEqual(counts["diagnostic:analysis_violation"], 2)
        self.assertEqual(counts["value_domain:exec.allocmem.attributes"], 1)
        self.assertEqual(counts["value_domain:exec.allocmem.result"], 1)
        self.assertEqual(counts["value_domain:dos.mode"], 1)
        self.assertEqual(counts["struct:MemHeader"], 2)
        self.assertEqual(counts["os_call_output_reg:D0"], 1)
        self.assertEqual(counts["platform_effect:write_base_slot"], 1)
        self.assertEqual(counts["platform_base:DOSBase"], 1)
        self.assertEqual(counts["app_slot:base_slot"], 1)
        self.assertEqual(counts["app_slot_base:DOSBase"], 1)
        self.assertEqual(counts["semantic:library_base"], 1)
        self.assertEqual(counts["type:struct_FileHandle_*"], 1)
        self.assertEqual(counts["type:Device"], 1)
        self.assertEqual(counts["typed_storage:any"], 1)
        self.assertEqual(counts["typed_storage_kind:write_typed_global_slot"], 1)
        self.assertEqual(counts["typed_storage_type:Device"], 1)
        self.assertEqual(counts["typed_storage_target:global_slot"], 1)
        self.assertEqual(counts["platform_typed_access:any"], 2)
        self.assertEqual(counts["platform_typed_access_provenance:api_output"], 1)
        self.assertEqual(counts["platform_typed_access_provenance:lookup_storage"], 1)
        self.assertEqual(counts["platform_typed_access_struct:Library"], 1)
        self.assertEqual(counts["platform_typed_access_struct:IO"], 1)
        self.assertEqual(counts["platform_typed_access_owner:IO"], 1)
        self.assertEqual(counts["platform_field:LIB_VERSION"], 1)
        self.assertEqual(counts["platform_field:IO_COMMAND"], 1)
        self.assertEqual(counts["platform_struct_field:IO.IO_COMMAND"], 1)
        self.assertEqual(counts["platform_field_expr:IO.IO_COMMAND"], 1)
        self.assertEqual(counts["struct:IO"], 1)
        self.assertEqual(counts["typed_base_unresolved_field"], 1)
        self.assertEqual(counts["platform_unresolved_typed_access:any"], 1)
        self.assertEqual(counts["platform_unresolved_typed_access_struct:InputEvent"], 1)
        self.assertEqual(counts["struct:InputEvent"], 1)
        self.assertEqual(counts["app_slot:any"], 2)
        self.assertEqual(counts["app_slot:read-write"], 1)
        self.assertEqual(counts["app_slot:write"], 1)
        self.assertEqual(counts["app_slot:typed_region"], 1)
        self.assertEqual(counts["app_slot_region:InputEvent"], 1)
        self.assertEqual(counts["app_slot_region_source:platform_api_arg"], 1)
        self.assertEqual(counts["app_slot:typed_field_ref"], 1)
        self.assertEqual(counts["app_slot_field_path:InputEvent.ie_Code"], 1)
        self.assertEqual(counts["app_slot:field_gap"], 1)
        self.assertEqual(counts["app_slot_field_gap:known_struct_field"], 1)
        self.assertEqual(counts["app_slot_field_gap_path:InputEvent.ie_Qualifier"], 1)
        self.assertEqual(counts["app_slot:gap"], 1)
        self.assertEqual(counts["app_slot:suggested_region"], 1)
        self.assertEqual(counts["app_slot:untyped_api_arg"], 1)
        self.assertEqual(counts["app_slot_api_arg:RawKeyConvert"], 1)
        self.assertEqual(counts["app_slot_api_arg_reason:missing_struct_metadata"], 1)
        self.assertEqual(counts["runtime:view"], 1)
        self.assertEqual(counts["runtime:copied_code"], 1)
        self.assertEqual(counts["runtime:view_kind:2"], 1)
        self.assertEqual(counts["runtime:suppressed_org_range"], 1)
        self.assertEqual(counts["runtime:suppressed_org_reason:exit_to_larger_runtime_range"], 1)
        self.assertEqual(counts["runtime:view_relationship:exits_to_larger_runtime_range"], 1)
        self.assertEqual(counts["runtime:view_related_range"], 1)
        self.assertEqual(counts["suppressed-weak-org-range"], 1)
        self.assertEqual(counts["orphan-code:signal"], 1)
        self.assertEqual(counts["orphan-code:reason:terminal_decode"], 1)
        self.assertEqual(counts["orphan-code:status:unresolved"], 1)
        self.assertEqual(counts["orphan-code:terminal_decode:unresolved"], 1)
        self.assertEqual(counts["orphan-code:terminal_flow:return"], 1)
        self.assertEqual(counts["orphan-code:required_cpu:0"], 1)
        self.assertEqual(counts["orphan-code:has_instruction_count"], 1)
        self.assertEqual(counts["orphan-code:instruction_count:2"], 1)
        self.assertEqual(counts["orphan-code:context:accepted_code_boundary"], 1)
        self.assertEqual(counts["orphan-code:missing_inbound:jump_table"], 1)
        self.assertEqual(counts["orphan-code:nearby_data:lookup_table"], 1)
        self.assertEqual(counts["orphan-code:nearby_data:after:lookup_table"], 1)
        self.assertEqual(counts["materialized-org-range"], 1)
        self.assertEqual(counts["runtime:materialized_org_range"], 1)
        self.assertEqual(counts["runtime:materialized_org_address:00000400"], 1)
        self.assertEqual(counts["memory:absolute_stack_top"], 2)
        self.assertEqual(counts["memory:absolute_stack_top:stack_top_00080000"], 2)
        self.assertEqual(counts["analysis:runtime_table_base_addend"], 1)
        self.assertEqual(counts["analysis:runtime_table_base_addend:abs_0_0000C266"], 1)
        self.assertEqual(counts["analysis:indirect_site"], 2)
        self.assertEqual(counts["analysis:indirect_site:status:unresolved"], 1)
        self.assertEqual(counts["analysis:indirect_site:status:jump_table"], 1)
        self.assertEqual(counts["analysis:indirect_site:shape:pcindex.brief"], 1)
        self.assertEqual(counts["analysis:indirect_site:source_pattern:pc_indexed_indirect"], 1)
        self.assertEqual(counts["table:candidate_unresolved"], 1)
        self.assertEqual(counts["table:candidate_unresolved:source_pattern:pc_indexed_indirect"], 1)
        self.assertEqual(counts["table:candidate_unresolved:status:unresolved"], 1)
        self.assertEqual(counts["table:candidate_unresolved:source_range"], 1)
        self.assertEqual(counts["table:candidate_unresolved:table_bounds"], 1)
        self.assertEqual(
            counts["table:candidate_unresolved:table_bounds_status:rejected_insufficient_entries"], 1
        )
        self.assertEqual(counts["table:candidate_unresolved:entry_size:2"], 1)
        self.assertEqual(counts["data:string_ref"], 4)
        self.assertEqual(counts["compressed-payload"], 1)
        self.assertEqual(counts["compressed:rnc1-old"], 1)
        self.assertEqual(counts["decompression:provider:ancient-cli"], 1)
        self.assertEqual(counts["decompression:has_output_size"], 1)
        self.assertEqual(counts["decompression:has_output_hash"], 1)
        self.assertEqual(counts["derived_target_suggestion:decompressed_payload"], 1)
        self.assertEqual(counts["derived_target_suggestion_status:materializable"], 1)
        self.assertEqual(counts["derived_target_suggestion_reason:initial_control_target_validated_runtime_copy"], 1)
        self.assertEqual(counts["derived-decompressed-target"], 1)
        self.assertEqual(counts["absolute-depack-dest"], 1)
        self.assertEqual(counts["decompressed-entrypoint"], 1)
        self.assertEqual(counts["decompression:output_load_address"], 1)
        self.assertEqual(counts["decompression:output_load_address:00004000"], 1)
        self.assertEqual(counts["decompression:entrypoint"], 1)
        self.assertEqual(counts["decompression:entrypoint:00004000"], 1)
        self.assertEqual(counts["decompression:runtime_copy"], 1)
        self.assertEqual(counts["decompression:runtime_copy_kind:3"], 1)
        self.assertEqual(counts["decompression:runtime_copy_conflicting"], 1)
        self.assertEqual(counts["decompression:runtime_copy_oversize"], 1)
        self.assertEqual(counts["decompression:pattern:runtime_copy_to_absolute"], 1)
        self.assertEqual(counts["table:any"], 1)
        self.assertEqual(counts["table:role:lookup_table"], 1)
        self.assertEqual(counts["table:kind:relative_code_dispatch"], 1)
        self.assertEqual(counts["table:source_pattern:indexed_word_dispatch"], 1)
        self.assertEqual(counts["table:base:target_label"], 1)
        self.assertEqual(counts["table:consumer"], 1)
        self.assertEqual(counts["table:entry_size:2"], 1)
        self.assertNotIn("table:conflict_state:clean", counts)
        self.assertEqual(counts["memory-layout:any"], 8)
        self.assertEqual(counts["memory-layout:record:base_layout"], 1)
        self.assertEqual(counts["memory-layout:record:base_layout_field"], 1)
        self.assertEqual(counts["memory-layout:record:runtime_view"], 1)
        self.assertEqual(counts["memory-layout:record:runtime_address_ref"], 1)
        self.assertEqual(counts["memory-layout:record:absolute_memory_ref"], 1)
        self.assertEqual(counts["memory-layout:record:platform_typed_access"], 1)
        self.assertEqual(counts["memory-layout:record:platform_storage_effect"], 1)
        self.assertEqual(counts["memory-layout:record:platform_unresolved_typed_access"], 1)
        self.assertEqual(counts["memory-layout:kind:base_layout"], 1)
        self.assertEqual(counts["memory-layout:kind:base_layout_field"], 1)
        self.assertEqual(counts["memory-layout:kind:runtime_view_candidate"], 1)
        self.assertEqual(counts["memory-layout:kind:copper_list"], 1)
        self.assertEqual(counts["memory-layout:kind:hardware_register"], 1)
        self.assertEqual(counts["memory-layout:kind:platform_struct_field"], 1)
        self.assertEqual(counts["memory-layout:kind:typed_global_slot"], 1)
        self.assertEqual(counts["memory-layout:kind:platform_struct_unresolved"], 1)
        self.assertEqual(counts["memory-layout:platform_struct:Library"], 1)
        self.assertEqual(counts["memory-layout:platform_struct:AppState"], 1)
        self.assertEqual(counts["memory-layout:platform_struct:InputEvent"], 1)
        self.assertEqual(counts["memory-layout:platform_field:LIB_VERSION"], 1)
        self.assertEqual(counts["memory-layout:storage_effect"], 1)
        self.assertEqual(counts["memory-layout:storage_effect:write_typed_global_slot"], 1)
        self.assertEqual(counts["memory-layout:sink_address"], 1)
        self.assertEqual(counts["memory-layout:range"], 8)
        self.assertEqual(counts["memory-layout:range_space:1"], 4)
        self.assertEqual(counts["memory-layout:range_space:2"], 2)
        self.assertEqual(counts["memory-layout:range_space:3"], 1)
        self.assertEqual(counts["memory-layout:range_space:4"], 1)
        self.assertEqual(counts["memory-layout:range_size:4"], 3)
        self.assertEqual(counts["memory-layout:conflict"], 1)
        self.assertEqual(counts["memory-layout:conflict:code_overlap"], 1)
        self.assertEqual(counts["memory-layout-view:any"], 1)
        self.assertEqual(counts["memory-layout-view:range_space:1"], 1)
        self.assertEqual(counts["memory-layout-view:range_space:2"], 1)
        self.assertEqual(counts["memory-layout-view:range_space:3"], 1)
        self.assertEqual(counts["memory-layout-view:range_space:4"], 1)
        self.assertEqual(counts["memory-layout-view:has_conflict"], 1)
        self.assertEqual(counts["memory-layout-view:conflict_state:code_overlap"], 1)
        self.assertEqual(counts["memory-layout-view:absolute_refs"], 1)
        self.assertEqual(counts["memory-layout-view:absolute_owner:hardware_register"], 1)
        self.assertEqual(counts["data:copper_list"], 1)
        self.assertEqual(counts["hardware:custom"], 2)
        self.assertEqual(counts["hardware:custom/audio"], 1)
        self.assertEqual(counts["hardware:custom/copper"], 1)
        self.assertEqual(counts["hardware:custom/display"], 1)
        self.assertEqual(counts["value_domain:amiga.custom.copper"], 1)
        self.assertEqual(counts["value_domain:amiga.custom.display_config"], 1)
        self.assertEqual(counts["hardware_register:bplcon0"], 1)
        self.assertEqual(counts["display:bplcon0"], 1)
        self.assertEqual(counts["display:bitplanes:6"], 1)
        self.assertEqual(counts["display:color"], 1)
        self.assertEqual(counts["hardware_register:aud0"], 1)
        self.assertEqual(counts["hardware_register:aud0+ac_len"], 1)
        self.assertEqual(counts["label:any"], 1)
        self.assertEqual(counts["label:definition"], 1)
        self.assertEqual(counts["label:reference"], 1)
        self.assertEqual(counts["xref:segment_ref"], 1)
        self.assertEqual(counts["xref:code_ref"], 1)
        self.assertNotIn("coprocessor:fpu", counts)
        self.assertNotIn("coprocessor:fpu_id:3", counts)
        self.assertIn("os:exec.library/AllocMem", tags)
        self.assertIn("compressed:rnc1-old", tags)
        self.assertIn("materialized-org-range", tags)
        self.assertIn("orphan-code:terminal_decode:unresolved", tags)
        self.assertIn("table:kind:relative_code_dispatch", tags)
        self.assertIn("table:source_pattern:indexed_word_dispatch", tags)
        self.assertIn("table:candidate_unresolved", tags)
        self.assertIn("table:candidate_unresolved:source_pattern:pc_indexed_indirect", tags)
        self.assertEqual(examples["os:exec.library/AllocMem"][0]["offset"], 0x20)
        self.assertEqual(examples["compressed-payload"][0]["offset"], 0x4C40)
        self.assertEqual(examples["decompression:runtime_copy"][0]["runtime_copy_address"], 0x4000)
        self.assertTrue(examples["decompression:runtime_copy"][0]["runtime_copy_conflicting"])
        self.assertEqual(examples["absolute-depack-dest"][0]["load_address"], 0x4000)
        self.assertEqual(examples["decompressed-entrypoint"][0]["entrypoint"], 0x4000)
        self.assertEqual(examples["decompressed-entrypoint"][0]["initial_control_target"], 0x9B3A)
        self.assertEqual(examples["decompression:output_load_address:00004000"][0]["load_address"], 0x4000)
        self.assertEqual(examples["memory:absolute_stack_top"][0]["symbol"], "stack_top_00080000")
        self.assertEqual(examples["analysis:runtime_table_base_addend"][0]["addend"], -4)
        self.assertEqual(examples["table:any"][0]["entry_count"], 2)
        self.assertEqual(examples["table:any"][0]["consumer_offset"], 0x20)
        self.assertEqual(examples["table:any"][0]["conflict_state"], "clean")
        self.assertEqual(examples["table:any"][0]["source_pattern"], "indexed_word_dispatch")
        self.assertEqual(examples["memory-layout:record:base_layout"][0]["record_kind_id"], 1)
        self.assertEqual(examples["memory-layout:kind:base_layout"][0]["range_start"], 0x234)
        self.assertEqual(examples["memory-layout:kind:base_layout"][0]["field_count"], 1)
        self.assertEqual(examples["memory-layout:kind:base_layout"][0]["sizeof_symbol"], "app_SIZEOF")
        self.assertEqual(examples["memory-layout:kind:base_layout_field"][0]["symbol"], "app_0234")
        self.assertEqual(examples["memory-layout:kind:base_layout_field"][0]["range_start"], 0x234)
        self.assertEqual(examples["memory-layout:kind:base_layout_field"][0]["range_end"], 0x238)
        self.assertEqual(examples["memory-layout:kind:copper_list"][0]["runtime_address"], 0x0E)
        self.assertEqual(examples["memory-layout:kind:copper_list"][0]["sink_address"], 0xDFF080)
        self.assertEqual(examples["memory-layout:kind:hardware_register"][0]["owner_symbol"], "intena")
        self.assertEqual(examples["memory-layout:kind:typed_global_slot"][0]["target_offset"], 0x100)
        self.assertEqual(examples["memory-layout:storage_effect"][0]["effect_kind_name"], "write_typed_global_slot")
        self.assertEqual(examples["memory-layout:platform_struct:Library"][0]["field_expr"], "LIB_VERSION")
        self.assertEqual(examples["memory-layout-view:any"][0]["record_count"], 8)
        self.assertEqual(examples["memory-layout-view:any"][0]["absolute_ref_count"], 1)
        self.assertEqual(examples["memory-layout-view:any"][0]["conflict_count"], 1)
        self.assertEqual(examples["memory-layout-view:any"][0]["range_spaces"]["1"], 4)
        self.assertEqual(
            examples["memory-layout-view:absolute_owner:hardware_register"][0]["owner_kind_id"],
            3,
        )
        self.assertEqual(examples["orphan-code:signal"][0]["terminal_offset"], 0x86)
        self.assertEqual(examples["orphan-code:signal"][0]["terminal_flow"], "return")
        self.assertEqual(examples["orphan-code:signal"][0]["required_cpu"], 0)
        self.assertEqual(examples["orphan-code:signal"][0]["instruction_count"], 2)
        self.assertEqual(examples["orphan-code:signal"][0]["decode_conflict_count"], 0)
        self.assertEqual(examples["orphan-code:signal"][0]["context"], "accepted_code_boundary")
        self.assertEqual(examples["orphan-code:signal"][0]["missing_inbound"], "jump_table")
        self.assertEqual(examples["orphan-code:signal"][0]["nearby_data_class"], "lookup_table")
        self.assertEqual(examples["orphan-code:signal"][0]["nearby_data_relation"], "after")

    def test_self_decrunch_event_indexes_pattern_and_work_item(self) -> None:
        analysis = {
            "decompression_events": [
                {
                    "event_kind": "decompression",
                    "event_id": "decompression:self_decrunch:section:0:00000000:00020000",
                    "status": "needs_simulated_decrunch",
                    "reason": "simulated_instruction_limit",
                    "codec_id": "unknown-self-decrunch",
                    "codec_support": "simulator_required",
                    "payload_role": "unknown_runtime_payload",
                    "parent_remains_active": "false",
                    "source_kind": "self_decruncher",
                    "provider_id": "m68k-sim-decrunch",
                    "decompressor_code_section": 0,
                    "decompressor_entry_offset": 0,
                    "load_address": 0x20000,
                    "entrypoint": 0x20000,
                    "simulated_output_size": 44220,
                    "simulated_output_sha256": "21ea11a46f008c69cca2795347eca093967191bf535b33c5ff3777619161999d",
                }
            ]
        }
        bag = usage.FeatureBag()
        usage._add_analysis_features(analysis, bag)
        counts, examples, tags = bag.row_features()

        self.assertEqual(counts["decompression:pattern:absolute_self_decrunch_transfer"], 1)
        self.assertEqual(counts["decompression:pattern:simulated_self_decrunch_output"], 1)
        self.assertEqual(counts["decompression:output_load_address:00020000"], 1)
        self.assertEqual(counts["decompression:entrypoint:00020000"], 1)
        self.assertEqual(counts["decompression:decompressor_code"], 1)
        self.assertEqual(counts["decompression:decompressor_entry:0:00000000"], 1)
        self.assertEqual(counts["decompression:unmaterialized_work_item"], 1)
        self.assertEqual(counts["decompression:work_item_reason:simulated_instruction_limit"], 1)
        self.assertIn("decompression:pattern:absolute_self_decrunch_transfer", tags)
        self.assertEqual(examples["decompression:output_load_address:00020000"][0]["load_address"], 0x20000)
        self.assertEqual(examples["decompression:decompressor_code"][0]["decompressor_entry_offset"], 0)

        row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
        row_locations = {(0, 0): (2, "s0:00000000:instruction:2", "lea.l $20000,a0")}
        xrefs = usage._analysis_xrefs(row, analysis, row_locations)
        self.assertTrue(
            any(
                xref["feature"] == "decompression:pattern:absolute_self_decrunch_transfer"
                and xref["row_index"] == 2
                for xref in xrefs
            )
        )
        self.assertTrue(any(xref["feature"] == "decompression:output_load_address:00020000" for xref in xrefs))
        self.assertTrue(any(xref["feature"] == "decompression:decompressor_entry:0:00000000" for xref in xrefs))

    def test_device_features_use_resolved_device_names_for_all_io_calls(self) -> None:
        bag = usage.FeatureBag()
        usage._add_analysis_features(
            {
                "sections": [
                    {
                        "section_index": 0,
                        "recovered_platform_calls": [
                            {
                                "offset": 0x20,
                                "library_name": "exec.library",
                                "function_name": "DoIO",
                                "device_name": "trackdisk.device",
                            }
                        ],
                    }
                ],
            },
            bag,
        )

        counts, _examples, _tags = bag.row_features()

        self.assertEqual(counts["device_call:any"], 1)
        self.assertEqual(counts["device_call_function:DoIO"], 1)
        self.assertEqual(counts["device:trackdisk.device"], 1)
        self.assertEqual(counts["device_call:trackdisk.device/DoIO"], 1)

    def test_project_target_dirs_include_nested_disk_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            top = root / "targets" / "amiga_hunk_top"
            nested = root / "targets" / "amiga_disk_demo" / "targets" / "amiga_hunk_child"
            unrelated = root / "targets" / "amiga_disk_demo" / "targets" / "not_a_target"
            top.mkdir(parents=True)
            nested.mkdir(parents=True)
            unrelated.mkdir(parents=True)
            (top / "source_binary.json").write_text("{}", encoding="utf-8")
            (nested / "source_binary.json").write_text("{}", encoding="utf-8")

            target_dirs = usage._project_target_dirs(root=root)

        self.assertEqual([path.name for path in target_dirs], ["amiga_hunk_child", "amiga_hunk_top"])
        self.assertEqual(
            [usage._project_target_source_id(path, root=root) for path in target_dirs],
            ["amiga_disk_demo/targets/amiga_hunk_child", "amiga_hunk_top"],
        )

    def test_project_target_manifest_infers_disk_entry_hunk_platform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_dir = root / "targets" / "disk" / "targets" / "child"
            target_dir.mkdir(parents=True)
            source = usage.DiskEntryBinarySource(
                kind="disk_entry",
                disk_id="disk",
                adf_path=root / "disk.adf",
                entry_path="Carrier",
                display_path="disk.adf::Carrier",
                analysis_cache_path=target_dir / "binary.analysis",
                project_root=root,
            )
            with mock.patch.object(usage, "resolve_target_binary_source", return_value=source):
                entry, resolved_source = usage._project_target_manifest_entry(target_dir, root=root)

        self.assertIs(resolved_source, source)
        self.assertEqual(entry["id"], "disk/targets/child")
        self.assertEqual(entry["platform"], "amiga-hunk")
        self.assertEqual(entry["status"], "ok")

    def test_project_target_metadata_features_include_decompressed_child(self) -> None:
        entry = {
            "id": "child",
            "platform": "raw-binary",
            "status": "ok",
            "origin": {},
            "project_origin_kind": "derived_decompressed_payload",
            "target_role": "decompressed_payload",
            "payload_role": "primary_program",
            "payload_role_confidence": "tool_inferred",
            "parent_remains_active": "unknown",
            "target_type": "raw_binary",
            "reproduction": {"status": "exact_file", "exact": True},
            "decompression": {
                "compressor": {"id": "rnc1-old", "name": "RNC1"},
                "payload_role": "primary_program",
                "payload_role_confidence": "tool_inferred",
                "parent_remains_active": "unknown",
                "packed": {"section_offset": 0x4C40, "file_offset": 0x4C60, "size": 168391},
                "decompressed": {"size": 359600, "load_address": 0x4000, "entrypoint": 0x4000},
            },
        }
        bag = usage.FeatureBag()

        usage._add_project_target_metadata_features(entry, bag)
        counts, examples, _tags = bag.row_features()
        xrefs = usage._project_target_metadata_xrefs(
            {
                "id": "project_target:child",
                "source_id": "child",
                "platform": "raw-binary",
                "origin": {},
            },
            entry,
        )

        self.assertEqual(counts["project_origin:derived_decompressed_payload"], 1)
        self.assertEqual(counts["project_target_role:decompressed_payload"], 1)
        self.assertEqual(counts["decompression:payload_role:primary_program"], 1)
        self.assertEqual(counts["decompression:payload_role_confidence:tool_inferred"], 1)
        self.assertEqual(counts["decompression:parent_remains_active:unknown"], 1)
        self.assertEqual(counts["project_target_type:raw_binary"], 1)
        self.assertEqual(counts["reproduction:status:exact_file"], 1)
        self.assertEqual(counts["reproduction:exact"], 1)
        self.assertEqual(counts["derived-decompressed-target"], 1)
        self.assertEqual(counts["derived_target:decompressed_payload"], 1)
        self.assertEqual(counts["decompression:child"], 1)
        self.assertEqual(counts["decompression:child_reproduction_status:exact_file"], 1)
        self.assertEqual(counts["decompression:child_reproduction_exact"], 1)
        self.assertEqual(counts["decompression:codec:rnc1-old"], 1)
        self.assertEqual(counts["decompression:source_offset"], 1)
        self.assertEqual(counts["decompression:source_offset:0:00004C40"], 1)
        self.assertEqual(counts["decompression:source_range"], 1)
        self.assertEqual(counts["decompression:source_range:0:00004C40-0002DE07"], 1)
        self.assertEqual(counts["decompression:packed_size"], 1)
        self.assertEqual(examples["derived-decompressed-target"][0]["offset"], 0x4C40)
        self.assertEqual(examples["derived-decompressed-target"][0]["source_section_end_offset"], 0x2DE07)
        self.assertEqual(examples["derived-decompressed-target"][0]["load_address"], 0x4000)
        self.assertEqual(examples["derived-decompressed-target"][0]["payload_role"], "primary_program")
        self.assertEqual(examples["derived-decompressed-target"][0]["reproduction_status"], "exact_file")
        self.assertTrue(examples["derived-decompressed-target"][0]["reproduction_exact"])
        self.assertIn("decompression:codec:rnc1-old", {xref["feature"] for xref in xrefs})
        self.assertIn("decompression:source_range:0:00004C40-0002DE07", {xref["feature"] for xref in xrefs})
        self.assertIn("decompression:child_reproduction_exact", {xref["feature"] for xref in xrefs})
        self.assertIn("decompression:payload_role:primary_program", {xref["feature"] for xref in xrefs})

    def test_numeric_copper_register_rows_use_hardware_metadata(self) -> None:
        bag = usage.FeatureBag()
        usage._add_listing_features(
            {
                "rows": [
                    {
                        "kind": "data",
                        "text": "\tdc.w $0100,$4200\n",
                        "section_index": 0,
                        "start_offset": 0x10,
                        "data_class": "copper_list",
                        "data_class_flags": 1,
                    }
                ]
            },
            bag,
        )

        counts, _examples, _tags = bag.row_features()

        self.assertEqual(counts["hardware_register:bplcon0"], 1)
        self.assertEqual(counts["hardware:custom/display"], 1)
        self.assertEqual(counts["display:bplcon0"], 1)
        self.assertEqual(counts["display:bitplanes:4"], 1)

    def test_listing_data_class_does_not_parse_comments_as_analysis(self) -> None:
        bag = usage.FeatureBag()
        usage._add_listing_features(
            {
                "rows": [
                    {
                        "kind": "data",
                        "text": "\tdc.w loc_0_00000010-loc_0_00000008\t; lookup_table\n",
                        "section_index": 0,
                        "start_offset": 0x10,
                    }
                ]
            },
            bag,
        )

        counts, _examples, _tags = bag.row_features()

        self.assertNotIn("data:lookup_table", counts)
        self.assertNotIn("analysis:lookup_table:word_relative_labels", counts)

    def test_builds_xrefs_from_structured_analysis_and_listing_metadata(self) -> None:
        target_row = {
            "id": "platform_file_manifest:demo",
            "source_id": "demo",
            "platform": "amiga-hunk",
            "origin": {"display_name": "demo"},
        }
        combined = {
            "analysis": {
                "findings": {"required_cpu": 2, "cpu_violation_count": 1},
                "packed_payloads": [
                    {
                        "found": True,
                        "provider_id": "ancient-cli",
                        "codec_id": "rnc1-old",
                        "source_section": 0,
                        "source_section_offset": 0x4C40,
                        "packed_size": 168391,
                        "decompressed_size": 359600,
                        "decompressed_sha256": "d37ec7db83012eba179956026b0677cfd46763d585722154f761bd6f6d2b5748",
                    }
                ],
                "derived_target_suggestions": [
                    {
                        "kind": "decompressed_payload",
                        "status": "materializable",
                        "reason": "initial_control_target_validated_runtime_copy",
                        "source_section": 0,
                        "source_section_offset": 0x4C40,
                        "packed_size": 168391,
                        "load_address": 0x4000,
                        "entrypoint": 0x4000,
                        "initial_control_target": 0x9B3A,
                        "runtime_copy_address": 0x4000,
                        "runtime_copy_size": 168396,
                        "runtime_copy_kind": 3,
                        "runtime_copy_conflicting": True,
                    }
                ],
                "table_candidate_records": [
                    {
                        "section_index": 0,
                        "offset": 0x120,
                        "source_offset": 0x120,
                        "source_size": 4,
                        "operand_index": 0,
                        "flow_kind": 2,
                        "flow": "stale_display_name",
                        "shape_id": 4,
                        "shape": "stale_display_name",
                        "status_id": 1,
                        "status": "stale_display_name",
                        "source_pattern": "stale_display_name",
                        "conflict_state_id": 2,
                        "conflict_state": "unresolved",
                        "table_offset": 0x160,
                        "table_size": 2,
                        "table_entry_size": 2,
                        "table_entry_count": 1,
                        "table_bounds_status_id": 1,
                        "table_bounds_status": "stale_display_name",
                        "detail": "indexed dispatch candidate",
                        "target": None,
                        "target_count": None,
                    }
                ],
                "table_records": [
                    {
                        "section_index": 0,
                        "offset": 0x90,
                        "size": 4,
                        "entry_size": 2,
                        "entry_count": 2,
                        "role": "lookup_table",
                        "table_kind": "relative_code_dispatch",
                        "source_pattern": "indexed_word_dispatch",
                        "base_expression": "target_label",
                        "consumer_section": 0,
                        "consumer_offset": 0x20,
                        "conflicted": False,
                        "conflict_state_id": 0,
                        "conflict_state": "clean",
                    }
                ],
                "memory_layout_records": [
                    {
                        "record_kind_id": 1,
                        "record_kind": "base_layout",
                        "memory_kind": "base_layout",
                        "layout_name": "app",
                        "base_symbol": "app",
                        "sizeof_symbol": "app_SIZEOF",
                        "field_count": 1,
                        "range_space_kind": 1,
                        "range_start": 0x234,
                        "range_size": 4,
                        "range_end": 0x238,
                    },
                    {
                        "record_kind_id": 2,
                        "record_kind": "base_layout_field",
                        "memory_kind": "base_layout_field",
                        "layout_name": "app",
                        "base_symbol": "app",
                        "symbol": "app_0234",
                        "owner_struct_name": "AppState",
                        "section_index": 0,
                        "source_offset": 0x30,
                        "field_offset": 0x234,
                        "field_size": 4,
                        "alias": False,
                        "range_space_kind": 1,
                        "range_start": 0x234,
                        "range_size": 4,
                        "range_end": 0x238,
                    },
                    {
                        "record_kind_id": 6,
                        "record_kind": "runtime_view",
                        "memory_kind": "runtime_view_candidate",
                        "section_index": 0,
                        "source_offset": 0x40,
                        "source_size": 0x20,
                        "runtime_address": 0x400,
                        "runtime_size": 0x20,
                        "range_space_kind": 2,
                        "range_start": 0x400,
                        "range_size": 0x20,
                        "range_end": 0x420,
                    },
                        {
                            "record_kind_id": 7,
                            "record_kind": "runtime_address_ref",
                            "memory_kind": "copper_list",
                        "section_index": 0,
                        "source_offset": 0x60,
                        "source_size": 12,
                            "runtime_address": 0x0E,
                            "runtime_size": 12,
                            "target_offset": 0x0E,
                            "sink_address": 0xDFF080,
                            "data_class_flags": 1,
                            "range_space_kind": 2,
                            "range_start": 0x0E,
                            "range_size": 12,
                            "range_end": 0x1A,
                        },
                        {
                            "record_kind_id": 8,
                            "record_kind": "absolute_memory_ref",
                            "memory_kind": "hardware_register",
                            "section_index": 0,
                            "source_offset": 0x60,
                            "source_size": 8,
                            "operand_index": 1,
                            "access": "memory_write",
                            "access_width": 2,
                            "address": 0xDFF09A,
                            "owner_kind_id": 3,
                            "owner_kind": "hardware_register",
                            "owner_symbol": "intena",
                            "owner_base_symbol": "_custom",
                            "owner_offset": 0x9A,
                            "range_space_kind": 3,
                            "range_start": 0xDFF09A,
                            "range_size": 2,
                            "range_end": 0xDFF09C,
                            "confidence": 2,
                            "conflicted": True,
                            "conflict_state_id": 1,
                            "conflict_state": "code_overlap",
                        },
                        {
                            "record_kind_id": 4,
                            "record_kind": "platform_typed_access",
                            "memory_kind": "platform_struct_field",
                            "section_index": 0,
                            "source_offset": 0x30,
                            "operand_index": 1,
                            "base_register": "A0",
                            "displacement": 20,
                            "field_offset": 20,
                            "root_struct_name": "Library",
                            "owner_struct_name": "Library",
                            "field_name": "LIB_VERSION",
                            "field_expr": "LIB_VERSION",
                            "type_provenance_kind": "api_output",
                            "range_space_kind": 1,
                            "range_start": 20,
                            "range_size": 2,
                            "range_end": 22,
                        },
                        {
                            "record_kind_id": 3,
                            "record_kind": "platform_storage_effect",
                            "memory_kind": "typed_global_slot",
                            "section_index": 0,
                            "source_offset": 0x30,
                            "effect_kind": 7,
                            "effect_kind_name": "write_typed_global_slot",
                            "displacement": -32768,
                            "field_disp": -32768,
                            "base_name": "exec.library",
                            "symbol_name": "MP_SIGBIT",
                            "type_name": "MP",
                            "target_section_index": 0,
                            "target_offset": 0x100,
                            "range_space_kind": 4,
                            "range_start": 0x100,
                            "range_size": 4,
                            "range_end": 0x104,
                        },
                        {
                            "record_kind_id": 5,
                            "record_kind": "platform_unresolved_typed_access",
                            "memory_kind": "platform_struct_unresolved",
                            "section_index": 0,
                            "source_offset": 0x30,
                            "operand_index": 0,
                            "base_register": "A0",
                            "displacement": 64,
                            "struct_size": 34,
                            "classification_id": 0,
                            "classification": "field_gap",
                            "root_struct_name": "Library",
                            "type_provenance_kind": "unknown",
                            "range_space_kind": 1,
                            "range_start": 64,
                            "range_size": 34,
                            "range_end": 98,
                        },
                ],
                "sections": [
                    {
                        "section_index": 0,
                        "recovered_platform_calls": [
                            {
                                "offset": 0x20,
                                "library_name": "exec.library",
                                "function_name": "AllocMem",
                                "note_kind": 3,
                                "outputs": [
                                    {
                                        "name": "memory",
                                        "regs": ["D0"],
                                        "type": "APTR",
                                        "o_struct": "MemHeader",
                                        "value_domain": "exec.allocmem.result",
                                    }
                                ],
                            }
                        ],
                        "recovered_platform_effects": [
                            {"offset": 0x30, "kind": 2, "displacement": 0x234, "base_name": "DOSBase"},
                            {"offset": 0x30, "kind": 5, "displacement": 0x240, "type_name": "MP"},
                        ],
                        "recovered_platform_typed_accesses": [
                            {
                                "offset": 0x30,
                                "operand_index": 1,
                                "base_register": "A0",
                                "displacement": 20,
                                "field_offset": 20,
                                "root_struct_name": "Library",
                                "owner_struct_name": "Library",
                                "field_name": "LIB_VERSION",
                                "field_expr": "LIB_VERSION",
                                "inherited": False,
                                "nested": False,
                                "type_provenance_kind": "api_output",
                                "type_provenance_section": 0,
                                "type_provenance_offset": 0x20,
                            }
                        ],
                        "recovered_platform_unresolved_typed_accesses": [
                            {
                                "offset": 0x30,
                                "operand_index": 0,
                                "base_register": "A0",
                                "displacement": 64,
                                "struct_size": 34,
                                "root_struct_name": "Library",
                            }
                        ],
                        "app_slot_refs": [
                            {"offset": 0x30, "symbol": "app_0234", "displacement": 0x234, "access": "write"}
                        ],
                        "runtime_views": [
                            {
                                "storage_offset": 0x40,
                                "storage_address": 0x40,
                                "runtime_address": 0x400,
                                "kind": 2,
                                "size": 0x20,
                                "materialized": False,
                                "materialization_reason": 103,
                                "relationship_kind": 1,
                                "relationship_kind_name": "exits_to_larger_runtime_range",
                                "related_runtime_address": 0x800,
                            }
                        ],
                        "orphan_code_signals": [
                            {
                                "offset": 0x84,
                                "size": 4,
                                "terminal_offset": 0x86,
                                "terminal_flow_kind": 5,
                                "terminal_flow": "stale_display_name",
                                "required_cpu": 0,
                                "instruction_count": 2,
                                "decode_conflict_count": 0,
                                "reason_id": 1,
                                "reason": "stale_display_name",
                                "status_id": 1,
                                "status": "stale_display_name",
                                "context_id": 1,
                                "context": "stale_display_name",
                                "missing_inbound_id": 2,
                                "missing_inbound": "stale_display_name",
                                "nearby_data_flags": 8,
                                "nearby_data_class": "stale_display_name",
                                "nearby_data_relation": "after",
                                "confidence": 60,
                            }
                        ],
                        "recovered_indirect_site_count": 2,
                        "recovered_indirect_sites": [
                            {
                                "offset": 0x120,
                                "flow_kind": 2,
                                "flow": "stale_display_name",
                                "shape_id": 4,
                                "shape": "stale_display_name",
                                "status_id": 1,
                                "status": "stale_display_name",
                                "detail": "indexed dispatch candidate",
                                "target": None,
                                "target_count": None,
                            },
                            {
                                "offset": 0x140,
                                "flow_kind": 2,
                                "flow": "stale_display_name",
                                "shape_id": 3,
                                "shape": "stale_display_name",
                                "status_id": 6,
                                "status": "stale_display_name",
                                "target": 0x180,
                                "target_count": 3,
                            },
                        ],
                    }
                ],
            },
            "listing": {
                "rows": [
                    {
                        "kind": "label",
                        "text": "loc_0_00000020:\n",
                        "section_index": 0,
                        "start_offset": 0x20,
                        "stable_key": "row-label",
                    },
                    {
                        "kind": "instruction",
                        "text": "\tjsr loc_0_00000080.l\n",
                        "section_index": 0,
                        "start_offset": 0x20,
                        "stable_key": "row-os",
                        "operand_parts": [
                            {
                                "kind": "symbol",
                                "text": "loc_0_00000080",
                                "segment_addr": 0x80,
                                "metadata": {"symbol": "loc_0_00000080"},
                            }
                        ],
                    },
                    {
                        "kind": "instruction",
                        "text": "\tmove.l d0,app_0234(a6)\n",
                        "section_index": 0,
                        "start_offset": 0x30,
                        "stable_key": "row-app",
                        "app_slot_refs": [
                            {"symbol": "app_0234", "displacement": 0x234, "access": "write"}
                        ],
                        "typed_accesses": [
                            {
                                "operand_index": 1,
                                "base_register": "A0",
                                "displacement": 20,
                                "field_offset": 20,
                                "root_struct_name": "Library",
                                "owner_struct_name": "Library",
                                "field_name": "LIB_VERSION",
                                "field_expr": "LIB_VERSION",
                                "inherited": False,
                                "nested": False,
                                "type_provenance_kind": "api_output",
                                "type_provenance_section": 0,
                                "type_provenance_offset": 0x20,
                            }
                        ],
                    },
                    {
                        "kind": "directive",
                        "text": "\tORG $400\n",
                        "section_index": 0,
                        "start_offset": 0x40,
                        "stable_key": "row-runtime",
                        "opcode_or_directive": "ORG",
                    },
                    {
                        "kind": "data",
                        "text": "\tdc.w bplcon0,BPU2|BPU1|BPU0|COLORON\n",
                        "section_index": 0,
                        "start_offset": 0x50,
                        "stable_key": "row-copper",
                        "data_class": "copper_list",
                        "data_class_flags": 1,
                    },
                    {
                        "kind": "instruction",
                        "text": "\tmove.w #$1234,_custom+aud0+ac_len.l\n",
                        "section_index": 0,
                        "start_offset": 0x60,
                        "stable_key": "row-hw",
                    },
                    {
                        "kind": "data",
                        "text": "\tdc.b $52,$4E,$43,$01\n",
                        "section_index": 0,
                        "start_offset": 0x4C40,
                        "stable_key": "row-rnc",
                    },
                    {
                        "kind": "data",
                        "text": "\tdc.w loc_0_00000094-loc_0_00000094\n",
                        "section_index": 0,
                        "start_offset": 0x90,
                        "stable_key": "row-table",
                    },
                    {
                        "kind": "data",
                        "text": "\t4e75\n",
                        "section_index": 0,
                        "start_offset": 0x84,
                        "stable_key": "row-orphan",
                    },
                ],
            },
        }

        xrefs = usage._file_usage_xrefs(target_row, {}, combined, None)
        by_feature = {(xref["feature"], xref["kind"], xref["offset"], xref["row_index"]) for xref in xrefs}
        by_feature_resolution = {
            (xref["feature"], xref["kind"], xref["row_index"], xref.get("resolution")) for xref in xrefs
        }
        typed_any = [
            xref for xref in xrefs
            if xref["feature"] == "platform_typed_access:any" and xref["kind"] == "platform_typed_access"
        ]
        snippets = usage._snippet_rows_for_xrefs(target_row, combined, xrefs, before=1, after=0)

        self.assertIn(("os:exec.library/AllocMem", "os_call", 0x20, 1), by_feature)
        self.assertIn(("os_call:any", "os_call", 0x20, 1), by_feature)
        self.assertIn(("os_call_library:exec.library", "os_call", 0x20, 1), by_feature)
        self.assertIn(("os_call_output_reg:D0", "os_call_output", 0x20, 1), by_feature)
        self.assertIn(("value_domain:exec.allocmem.result", "value_domain", 0x20, 1), by_feature)
        self.assertIn(("struct:MemHeader", "struct", 0x20, 1), by_feature)
        self.assertIn(("os:exec.library/AllocMem", "os_call", 1, "local_wrapper"), by_feature_resolution)
        self.assertIn(("os_library:exec.library", "os_library", None, None), by_feature_resolution)
        self.assertIn(("xref:segment_ref", "segment_ref", 0x20, 1), by_feature)
        self.assertIn(("xref:code_ref", "segment_ref", 0x20, 1), by_feature)
        self.assertIn(("platform_effect:write_base_slot", "platform_effect", 0x30, 2), by_feature)
        self.assertIn(("app_slot:base_slot", "app_slot_base_slot", 0x30, 2), by_feature)
        self.assertIn(("app_slot_base:DOSBase", "app_slot_base_slot", 0x30, 2), by_feature)
        self.assertIn(("app_slot:write", "app_slot_ref", 0x30, 2), by_feature)
        self.assertIn(("typed_storage:any", "typed_storage", 0x30, 2), by_feature)
        self.assertIn(("typed_storage_kind:write_typed_slot", "typed_storage", 0x30, 2), by_feature)
        self.assertIn(("platform_typed_access:any", "platform_typed_access", 0x30, 2), by_feature)
        self.assertTrue(any(xref.get("type_provenance_kind") == "api_output" for xref in typed_any))
        self.assertIn(("platform_typed_access_provenance:api_output", "platform_typed_access", 0x30, 2), by_feature)
        self.assertIn(("platform_typed_access_struct:Library", "platform_typed_access", 0x30, 2), by_feature)
        self.assertIn(("platform_field:LIB_VERSION", "platform_typed_access", 0x30, 2), by_feature)
        self.assertIn(("platform_struct_field:Library.LIB_VERSION", "platform_typed_access", 0x30, 2), by_feature)
        self.assertIn(("typed_base_unresolved_field", "platform_unresolved_typed_access", 0x30, 2), by_feature)
        self.assertIn(("platform_unresolved_typed_access:any", "platform_unresolved_typed_access", 0x30, 2), by_feature)
        self.assertIn(
            ("platform_unresolved_typed_access_struct:Library", "platform_unresolved_typed_access", 0x30, 2),
            by_feature,
        )
        self.assertIn(("runtime:copied_code", "runtime_view", 0x40, 3), by_feature)
        self.assertIn(("runtime:suppressed_org_range", "runtime_view", 0x40, 3), by_feature)
        self.assertIn(
            ("runtime:suppressed_org_reason:exit_to_larger_runtime_range", "runtime_view", 0x40, 3),
            by_feature,
        )
        self.assertIn(
            ("runtime:view_relationship:exits_to_larger_runtime_range", "runtime_view", 0x40, 3),
            by_feature,
        )
        self.assertIn(("runtime:view_related_range", "runtime_view", 0x40, 3), by_feature)
        self.assertIn(("suppressed-weak-org-range", "runtime_view", 0x40, 3), by_feature)
        self.assertIn(("materialized-org-range", "runtime_org", 0x40, 3), by_feature)
        self.assertIn(("runtime:materialized_org_range", "runtime_org", 0x40, 3), by_feature)
        self.assertIn(("runtime:materialized_org_address:00000400", "runtime_org", 0x40, 3), by_feature)
        self.assertIn(("table:any", "table_record", 0x90, 7), by_feature)
        self.assertIn(("table:role:lookup_table", "table_record", 0x90, 7), by_feature)
        self.assertIn(("table:kind:relative_code_dispatch", "table_record", 0x90, 7), by_feature)
        self.assertIn(("table:source_pattern:indexed_word_dispatch", "table_record", 0x90, 7), by_feature)
        self.assertNotIn(("table:conflict_state:clean", "table_record", 0x90, 7), by_feature)
        self.assertIn(("table:consumer", "table_record", 0x90, 7), by_feature)
        self.assertIn(("table:consumer", "table_consumer", 0x20, 1), by_feature)
        self.assertIn(("memory-layout:record:base_layout", "memory_layout", None, None), by_feature)
        self.assertIn(("memory-layout:kind:base_layout", "memory_layout", None, None), by_feature)
        self.assertIn(("memory-layout:kind:base_layout_field", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:platform_struct:AppState", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:kind:platform_struct_field", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:platform_struct:Library", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:platform_field:LIB_VERSION", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:record:platform_storage_effect", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:kind:typed_global_slot", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:storage_effect", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:storage_effect:write_typed_global_slot", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:range_space:4", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:range_size:4", "memory_layout", 0x30, 2), by_feature)
        self.assertIn(("memory-layout:kind:runtime_view_candidate", "memory_layout", 0x40, 3), by_feature)
        self.assertIn(("memory-layout:kind:copper_list", "memory_layout", 0x60, 5), by_feature)
        self.assertIn(("memory-layout:record:absolute_memory_ref", "memory_layout", 0x60, 5), by_feature)
        self.assertIn(("memory-layout:kind:hardware_register", "memory_layout", 0x60, 5), by_feature)
        self.assertIn(("memory-layout:sink_address", "memory_layout", 0x60, 5), by_feature)
        self.assertIn(("memory-layout:range", "memory_layout", 0x60, 5), by_feature)
        self.assertIn(("memory-layout:range_space:3", "memory_layout", 0x60, 5), by_feature)
        self.assertIn(("memory-layout:range_size:2", "memory_layout", 0x60, 5), by_feature)
        self.assertIn(("memory-layout:conflict", "memory_layout", 0x60, 5), by_feature)
        self.assertIn(("memory-layout:conflict:code_overlap", "memory_layout", 0x60, 5), by_feature)
        self.assertIn(("orphan-code:signal", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:reason:terminal_decode", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:status:unresolved", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:terminal_decode:unresolved", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:terminal_flow:return", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:required_cpu:0", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:has_instruction_count", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:instruction_count:2", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:context:accepted_code_boundary", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:missing_inbound:jump_table", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:nearby_data:lookup_table", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("orphan-code:nearby_data:after:lookup_table", "orphan_code_signal", 0x84, 8), by_feature)
        self.assertIn(("analysis:indirect_site:status:unresolved", "indirect_site", 0x120, None), by_feature)
        self.assertIn(("analysis:indirect_site:shape:pcindex.brief", "indirect_site", 0x120, None), by_feature)
        self.assertIn(("table:candidate_unresolved", "table_candidate", 0x120, None), by_feature)
        self.assertIn(("table:candidate_unresolved:source_range", "table_candidate", 0x120, None), by_feature)
        self.assertIn(("table:candidate_unresolved:table_bounds", "table_candidate", 0x120, None), by_feature)
        self.assertIn(
            (
                "table:candidate_unresolved:table_bounds_status:rejected_insufficient_entries",
                "table_candidate",
                0x120,
                None,
            ),
            by_feature,
        )
        self.assertIn(("table:candidate_unresolved:entry_size:2", "table_candidate", 0x120, None), by_feature)
        self.assertIn(
            ("table:candidate_unresolved:source_pattern:pc_indexed_indirect", "table_candidate", 0x120, None),
            by_feature,
        )
        self.assertIn(("compressed-payload", "packed_payload", 0x4C40, 6), by_feature)
        self.assertIn(("compressed:rnc1-old", "packed_payload", 0x4C40, 6), by_feature)
        self.assertIn(
            ("derived_target_suggestion:decompressed_payload", "derived_target_suggestion", 0x4C40, 6),
            by_feature,
        )
        self.assertIn(("derived-decompressed-target", "derived_target_suggestion", 0x4C40, 6), by_feature)
        self.assertIn(
            (
                "derived_target_suggestion_reason:initial_control_target_validated_runtime_copy",
                "derived_target_suggestion",
                0x4C40,
                6,
            ),
            by_feature,
        )
        self.assertIn(("absolute-depack-dest", "derived_target_suggestion", 0x4C40, 6), by_feature)
        self.assertIn(("decompressed-entrypoint", "derived_target_suggestion", 0x4C40, 6), by_feature)
        self.assertIn(("decompression:runtime_copy", "derived_target_suggestion", 0x4C40, 6), by_feature)
        self.assertIn(("decompression:runtime_copy_kind:3", "derived_target_suggestion", 0x4C40, 6), by_feature)
        self.assertIn(("decompression:runtime_copy_conflicting", "derived_target_suggestion", 0x4C40, 6), by_feature)
        self.assertIn(("decompression:runtime_copy_oversize", "derived_target_suggestion", 0x4C40, 6), by_feature)
        self.assertIn(("data:copper_list", "data_class", 0x50, 4), by_feature)
        self.assertIn(("copper_register:bplcon0", "copper_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom", "hardware_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom/copper", "hardware_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom/display", "hardware_ref", 0x50, 4), by_feature)
        self.assertIn(("display:bitplanes:7", "display_ref", 0x50, 4), by_feature)
        self.assertIn(("display:color", "display_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom/audio", "hardware_ref", 0x60, 5), by_feature)
        self.assertIn(("hardware_register:aud0+ac_len", "hardware_ref", 0x60, 5), by_feature)
        payload_xref = next(item for item in xrefs if item["feature"] == "compressed:rnc1-old")
        self.assertEqual(payload_xref["stable_key"], "row-rnc")
        self.assertEqual(payload_xref["value"], 359600)
        copy_xref = next(item for item in xrefs if item["feature"] == "decompression:runtime_copy")
        self.assertEqual(copy_xref["value"], 0x4000)
        ids = [xref["id"] for xref in xrefs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([row["row_index"] for row in snippets], [0, 1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(snippets[1]["row"]["stable_key"], "row-os")
        self.assertEqual(snippets[2]["row"]["typed_accesses"][0]["field_name"], "LIB_VERSION")
        self.assertEqual(snippets[5]["row"]["stable_key"], "row-hw")

    def test_untyped_app_slot_api_arg_xref_uses_call_stable_key(self) -> None:
        target_row = {
            "id": "platform_file_manifest:demo",
            "source_id": "demo",
            "platform": "amiga-hunk",
            "origin": {"display_name": "demo"},
        }
        combined = {
            "listing": {
                "rows": [
                    {
                        "kind": "instruction",
                        "text": "\tlea.l app_key_buffer(a6),a1\n",
                        "section_index": 0,
                        "start_offset": 0,
                        "stable_key": "source-row",
                    },
                    {
                        "kind": "instruction",
                        "text": "\tjsr _LVORawKeyConvert(a6)\n",
                        "section_index": 0,
                        "start_offset": 4,
                        "stable_key": "call-row",
                    },
                ],
            },
            "app_slot_analysis": {
                "untyped_api_args": [
                    {
                        "symbol": "app_key_buffer",
                        "displacement": 0x200,
                        "function": "RawKeyConvert",
                        "register": "A1",
                        "reason": "missing_struct_metadata",
                        "hunk_index": 0,
                        "addr": 4,
                        "row_index": 1,
                        "stable_key": "call-row",
                        "source_stable_key": "source-row",
                    }
                ],
            },
        }

        xrefs = usage._file_usage_xrefs(target_row, {}, combined, None)
        api_xrefs = [xref for xref in xrefs if xref["kind"] == "app_slot_api_arg"]
        snippets = usage._snippet_rows_for_xrefs(target_row, combined, api_xrefs, before=0, after=0)

        self.assertEqual({xref["stable_key"] for xref in api_xrefs}, {"call-row"})
        self.assertEqual({xref["source_stable_key"] for xref in api_xrefs}, {"source-row"})
        self.assertEqual([snippet["row"]["stable_key"] for snippet in snippets], ["call-row"])

    def test_usage_snippet_rows_write_compressed_target_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snippets"
            rows = [
                {"target_id": "target-b", "row_index": 1, "row": {"text": "b1"}},
                {"target_id": "target-a", "row_index": 2, "row": {"text": "a2"}},
                {"target_id": "target-a", "row_index": 1, "row": {"text": "a1"}},
            ]

            usage.write_usage_snippet_rows(path, rows)

            self.assertFalse(path.exists())
            self.assertTrue(usage.snippet_rows_index_path(path).exists())
            self.assertTrue(usage.snippet_rows_blob_path(path).exists())
            self.assertEqual(
                [row["row_index"] for row in usage.read_usage_snippet_rows_for_target("target-a", path)],
                [1, 2],
            )
            self.assertEqual(
                [(row["target_id"], row["row_index"]) for row in usage.read_usage_snippet_rows(path)],
                [("target-a", 1), ("target-a", 2), ("target-b", 1)],
            )

    def test_type_flow_report_summarizes_resolved_and_open_opportunities(self) -> None:
        manifest_rows = [
            {
                "id": "platform_file_manifest:demo",
                "source_id": "demo",
                "platform": "amiga-hunk",
                "origin": {"display_name": "demo"},
            }
        ]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_typed_access:any",
                "kind": "platform_typed_access",
                "section": 0,
                "offset": 0x30,
                "row_index": 2,
                "stable_key": "typed-row",
                "symbol": "LIB_VERSION",
                "value": 20,
                "text": "cmpi.w #36,LIB_VERSION(a0)",
                "type_provenance_kind": "api_output",
                "type_provenance_section": 0,
                "type_provenance_offset": 0x20,
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_storage:any",
                "kind": "typed_storage",
                "section": 0,
                "offset": 0x28,
                "row_index": 1,
                "stable_key": "storage-row",
                "symbol": "MP",
                "access": "global_slot",
                "value": 0x100,
                "text": "move.l d0,$100.l",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_typed_access_struct:Library",
                "kind": "platform_typed_access",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_struct_field:Library.LIB_VERSION",
                "kind": "platform_typed_access",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "section": 0,
                "offset": 0x34,
                "row_index": 3,
                "stable_key": "unresolved-row",
                "symbol": "InputEvent",
                "value": 36,
                "text": "cmpi.w #36,$0024(a0)",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_unresolved_typed_access_struct:InputEvent",
                "kind": "platform_unresolved_typed_access",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "app_slot:untyped_api_arg",
                "kind": "app_slot_api_arg",
                "row_index": 4,
                "stable_key": "call-row",
                "text": "app_key_buffer -> RawKeyConvert A1",
            },
        ]
        snippets = [
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 8,
                "row": {
                    "kind": "instruction",
                    "text": "\tcmpi.w #36,$0014(a0)\n",
                    "stable_key": "numeric-row",
                    "section_index": 0,
                    "start_offset": 0x80,
                },
            }
        ]

        report = usage.build_type_flow_report(manifest_rows, xrefs, snippets)

        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["resolved_typed_access_count"], 1)
        self.assertEqual(report[0]["opportunity_count"], 3)
        self.assertEqual(report[0]["counts"]["untyped_app_slot_api_arg"], 1)
        self.assertEqual(report[0]["counts"]["typed_base_unresolved_field"], 1)
        self.assertEqual(report[0]["counts"]["typed_access_provenance:api_output"], 1)
        self.assertEqual(report[0]["counts"]["typed_storage"], 1)
        self.assertEqual(report[0]["counts"]["typed_storage_provenance:global_slot"], 1)
        self.assertEqual(report[0]["counts"]["numeric_address_reg_access_without_type"], 1)
        self.assertEqual(report[0]["counts"]["numeric_cause:unknown_pointer_chain"], 1)
        self.assertEqual(report[0]["typed_access_provenance_counts"], {"api_output": 1})
        self.assertEqual(report[0]["typed_storage_provenance_counts"], {"global_slot": 1})
        self.assertEqual(report[0]["numeric_cause_counts"], {"unknown_pointer_chain": 1})
        self.assertEqual(report[0]["struct_counts"], {"InputEvent": 1, "Library": 1})
        self.assertEqual(report[0]["field_counts"], {"Library.LIB_VERSION": 1})
        self.assertEqual(report[0]["examples"]["numeric_address_reg_access_without_type"][0]["stable_key"], "numeric-row")
        self.assertEqual(
            report[0]["examples"]["numeric_address_reg_access_without_type"][0]["trace"]["base_register"],
            "A0",
        )
        self.assertEqual(
            report[0]["examples"]["numeric_address_reg_access_without_type"][0]["trace"]["stop_reason"],
            "no_assignment_to_base_register",
        )

    def test_unresolved_typed_field_report_groups_by_struct_displacement_and_nearby_api(self) -> None:
        manifest_rows = [
            {"id": "platform_file_manifest:demo-a", "source_id": "demo-a", "platform": "amiga-hunk"},
            {"id": "platform_file_manifest:demo-b", "source_id": "demo-b", "platform": "amiga-hunk"},
        ]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo-a",
                "feature": "os:exec.library/FindTask",
                "kind": "os_call",
                "row_index": 10,
                "stable_key": "call-a",
                "text": "FindTask",
            },
            {
                "target_id": "platform_file_manifest:demo-a",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "section": 0,
                "offset": 0x34,
                "row_index": 12,
                "stable_key": "gap-a",
                "symbol": "Task",
                "value": 0xAC,
                "struct_size": 0x5C,
                "text": "move.l $00AC(a0),d0",
            },
            {
                "target_id": "platform_file_manifest:demo-b",
                "feature": "os:exec.library/FindTask",
                "kind": "os_call",
                "row_index": 20,
                "stable_key": "call-b",
                "text": "FindTask",
            },
            {
                "target_id": "platform_file_manifest:demo-b",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "section": 0,
                "offset": 0x48,
                "row_index": 22,
                "stable_key": "gap-b",
                "symbol": "Task",
                "value": 0xAC,
                "struct_size": 0x5C,
                "text": "cmpi.w #1,$00AC(a0)",
            },
        ]
        snippets = [
            {
                "target_id": "platform_file_manifest:demo-a",
                "row_index": 10,
                "row": {"kind": "instruction", "text": "\tjsr _LVOFindTask(a6)\n", "stable_key": "call-a"},
            },
            {
                "target_id": "platform_file_manifest:demo-a",
                "row_index": 12,
                "row": {"kind": "instruction", "text": "\tmove.l $00AC(a0),d0\n", "stable_key": "gap-a"},
            },
            {
                "target_id": "platform_file_manifest:demo-b",
                "row_index": 20,
                "row": {"kind": "instruction", "text": "\tjsr _LVOFindTask(a6)\n", "stable_key": "call-b"},
            },
            {
                "target_id": "platform_file_manifest:demo-b",
                "row_index": 22,
                "row": {"kind": "instruction", "text": "\tcmpi.w #1,$00AC(a0)\n", "stable_key": "gap-b"},
            },
        ]

        report = usage.build_unresolved_typed_field_report(manifest_rows, xrefs, snippets)

        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["root_struct_name"], "Task")
        self.assertEqual(report[0]["displacement"], 0xAC)
        self.assertEqual(report[0]["displacement_hex"], "$00AC")
        self.assertEqual(report[0]["struct_size"], 0x5C)
        self.assertFalse(report[0]["in_struct_bounds"])
        self.assertEqual(report[0]["classification"], "out_of_struct_bounds")
        self.assertEqual(report[0]["nearby_api_feature"], "os:exec.library/FindTask")
        self.assertEqual(report[0]["count"], 2)
        self.assertEqual(report[0]["target_count"], 2)
        self.assertEqual(report[0]["examples"][0]["nearby_api"]["stable_key"], "call-a")

    def test_unresolved_typed_field_report_classifies_control_transfer_operands(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "section": 0,
                "offset": 0x20,
                "row_index": 4,
                "stable_key": "lvo",
                "symbol": "Library",
                "value": -0x7E,
                "struct_size": 0x22,
                "text": "jsr -$007E(a6)",
            }
        ]
        snippets = [
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 4,
                "row": {"kind": "instruction", "text": "\tjsr -$007E(a6)\n", "stable_key": "lvo"},
            }
        ]

        report = usage.build_unresolved_typed_field_report(manifest_rows, xrefs, snippets)

        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["classification"], "control_transfer_operand")
        self.assertIn("control-transfer", report[0]["classification_reason"])

    def test_unresolved_typed_field_report_uses_prefix_extension_metadata(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "section": 0,
                "offset": 0x30,
                "row_index": 3,
                "stable_key": "prefix-row",
                "symbol": "MP",
                "value": 0x40,
                "struct_size": 34,
                "classification_id": 1,
                "classification": "prefix_extension",
                "container_candidate_count": 1,
                "container_struct_name": "ConUnit",
                "container_field_expr": "cu_YCCP",
                "refinement_applied": True,
                "refined_struct_name": "ConUnit",
                "text": "move.l $0040(a0),d0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_typed_access_struct:ConUnit",
                "kind": "platform_typed_access",
            },
        ]
        snippets = [
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 3,
                "row": {"kind": "instruction", "text": "\tmove.l $0040(a0),d0\n", "stable_key": "prefix-row"},
            }
        ]

        report = usage.build_unresolved_typed_field_report(manifest_rows, xrefs, snippets)

        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["classification"], "prefix_extension")
        self.assertEqual(report[0]["container_candidate_count"], 1)
        self.assertEqual(report[0]["container_struct_name"], "ConUnit")
        self.assertEqual(report[0]["container_field_expr"], "cu_YCCP")
        self.assertEqual(report[0]["refinement_applied_count"], 1)
        self.assertEqual(report[0]["refined_struct_name"], "ConUnit")
        self.assertEqual(report[0]["access_size_counts"], {"4": 1})
        self.assertEqual(report[0]["candidate_rankings"][0]["struct_name"], "ConUnit")
        self.assertEqual(report[0]["candidate_rankings"][0]["field_size"], 2)
        self.assertEqual(report[0]["candidate_rankings"][0]["target_context_score"], 1)
        self.assertEqual(report[0]["examples"][0]["container_struct_name"], "ConUnit")
        self.assertEqual(report[0]["examples"][0]["refinement_applied"], True)
        self.assertEqual(report[0]["examples"][0]["refined_struct_name"], "ConUnit")

    def test_unresolved_typed_field_report_ranks_exact_size_prefix_candidates(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "platform": "amiga-hunk",
                "section": 0,
                "offset": 0x20,
                "row_index": 4,
                "stable_key": "row",
                "symbol": "LIB",
                "value": 0xCE,
                "struct_size": 34,
                "classification_id": 1,
                "classification": "prefix_extension",
                "container_candidate_count": 3,
                "text": "move.w $00CE(a0),d0",
            }
        ]
        snippets = [
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 4,
                "row": {"text": "move.w $00CE(a0),d0", "stable_key": "row"},
            }
        ]

        report = usage.build_unresolved_typed_field_report(manifest_rows, xrefs, snippets)

        self.assertEqual(report[0]["access_size_counts"], {"2": 1})
        self.assertEqual(report[0]["candidate_rankings"][0]["struct_name"], "GfxBase")
        self.assertEqual(report[0]["candidate_rankings"][0]["field_expr"], "gb_DisplayFlags")
        self.assertEqual(report[0]["candidate_rankings"][0]["exact_access_size_match_count"], 1)
        self.assertEqual(report[0]["dominant_candidate"]["struct_name"], "GfxBase")
        self.assertEqual(report[0]["dominant_candidate"]["exact_access_size_match_count"], 1)

    def test_unresolved_typed_field_report_does_not_dominate_when_exact_size_ties(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "platform": "amiga-hunk",
                "row_index": 4,
                "stable_key": "row",
                "symbol": "MN",
                "value": 0x24,
                "struct_size": 20,
                "classification_id": 1,
                "classification": "prefix_extension",
                "container_candidate_count": 14,
                "text": "move.l $0024(a0),d0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_typed_access_struct:IO",
                "kind": "platform_typed_access",
                "row_index": 3,
                "symbol": "IO",
                "text": "move.l IO_LENGTH(a0),d0",
            },
        ]
        snippets = [
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 4,
                "row": {"text": "move.l $0024(a0),d0", "stable_key": "row"},
            }
        ]

        report = usage.build_unresolved_typed_field_report(manifest_rows, xrefs, snippets)

        self.assertEqual(report[0]["candidate_rankings"][0]["struct_name"], "IO")
        self.assertEqual(report[0]["candidate_rankings"][0]["exact_access_size_match_count"], 1)
        self.assertNotIn("dominant_candidate", report[0])

    def test_unresolved_typed_field_report_marks_custom_tail_distance(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "row_index": 3,
                "stable_key": "tail-row",
                "symbol": "AmigaGuideMsg",
                "value": 0x36,
                "struct_size": 0x34,
                "classification_id": 2,
                "classification": "custom_tail_or_mistyped_base",
                "container_candidate_count": 0,
                "text": "move.l $0036(a0),d0",
            }
        ]
        snippets = [
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 3,
                "row": {"kind": "instruction", "text": "\tmove.l $0036(a0),d0\n", "stable_key": "tail-row"},
            }
        ]

        report = usage.build_unresolved_typed_field_report(manifest_rows, xrefs, snippets)

        self.assertEqual(report[0]["classification"], "custom_tail_or_mistyped_base")
        self.assertEqual(report[0]["tail_offset_from_struct_end"], 2)
        self.assertEqual(report[0]["tail_offset_from_struct_end_hex"], "$0002")

    def test_unresolved_typed_field_report_clusters_custom_tail_groups(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "platform": "amiga-hunk",
                "section": 0,
                "offset": 0x10,
                "row_index": 1,
                "stable_key": "row-a",
                "symbol": "AmigaGuideMsg",
                "value": 0x36,
                "struct_size": 0x34,
                "classification_id": 2,
                "classification": "custom_tail_or_mistyped_base",
                "container_candidate_count": 0,
                "text": "move.l $0036(a0),d0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "platform": "amiga-hunk",
                "section": 0,
                "offset": 0x14,
                "row_index": 2,
                "stable_key": "row-b",
                "symbol": "AmigaGuideMsg",
                "value": 0x3A,
                "struct_size": 0x34,
                "classification_id": 2,
                "classification": "custom_tail_or_mistyped_base",
                "container_candidate_count": 0,
                "text": "move.l $003A(a0),d0",
            },
        ]

        report = usage.build_unresolved_typed_field_report(manifest_rows, xrefs, [])

        first = next(row for row in report if row["displacement"] == 0x36)
        cluster = first["tail_cluster_summary"]
        self.assertEqual(cluster["root_struct_name"], "AmigaGuideMsg")
        self.assertEqual(cluster["group_count"], 2)
        self.assertEqual(cluster["xref_count"], 2)
        self.assertEqual(cluster["displacement_min"], 0x36)
        self.assertEqual(cluster["displacement_max"], 0x3A)
        self.assertEqual(cluster["tail_offset_histogram"], {"$0002": 1, "$0006": 1})

    def test_unresolved_typed_fields_cli_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "manifest.jsonl"
            xrefs_path = tmp_path / "xrefs.jsonl"
            snippets_path = tmp_path / "snippets"
            output_path = tmp_path / "report.jsonl"
            _write_jsonl(manifest_path, [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}])
            _write_jsonl(
                xrefs_path,
                [
                    {
                        "target_id": "platform_file_manifest:demo",
                        "feature": "typed_base_unresolved_field",
                        "kind": "platform_unresolved_typed_access",
                        "row_index": 1,
                        "symbol": "InputEvent",
                        "value": 36,
                        "struct_size": 34,
                        "text": "cmpi.w #36,$0024(a0)",
                    }
                ],
            )
            usage.write_usage_snippet_rows(
                snippets_path,
                [
                    {
                        "target_id": "platform_file_manifest:demo",
                        "row_index": 1,
                        "row": {"kind": "instruction", "text": "\tcmpi.w #36,$0024(a0)\n"},
                    }
                ],
            )

            exit_code = usage.main(
                [
                    "unresolved-typed-fields",
                    "--manifest",
                    str(manifest_path),
                    "--xrefs",
                    str(xrefs_path),
                    "--snippet-rows",
                    str(snippets_path),
                    "--output",
                    str(output_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            rows = usage.read_unresolved_typed_field_report(output_path)
            self.assertEqual(rows[0]["root_struct_name"], "InputEvent")

    def test_type_flow_report_counts_prefix_refinement_resolution(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "row_index": 10,
                "stable_key": "prefix-row",
                "symbol": "MP",
                "value": 0x40,
                "classification_id": 1,
                "classification": "prefix_extension",
                "container_candidate_count": 1,
                "container_struct_name": "ConUnit",
                "container_field_expr": "cu_YCCP",
                "refinement_applied": True,
                "refined_struct_name": "ConUnit",
                "text": "move.l $0040(a0),d0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_type_refinement:applied",
                "kind": "platform_type_refinement",
                "row_index": 10,
                "stable_key": "prefix-row",
                "symbol": "ConUnit",
                "value": 0x40,
                "classification_id": 1,
                "classification": "prefix_extension",
                "container_candidate_count": 1,
                "container_struct_name": "ConUnit",
                "container_field_expr": "cu_YCCP",
                "refinement_applied": True,
                "refined_struct_name": "ConUnit",
                "text": "move.l $0040(a0),d0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_typed_access:any",
                "kind": "platform_typed_access",
                "row_index": 11,
                "stable_key": "typed-row",
                "symbol": "cu_YCCP",
                "text": "tst.w cu_YCCP(a0)",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_typed_access_struct:ConUnit",
                "kind": "platform_typed_access",
                "row_index": 11,
                "stable_key": "typed-row",
                "symbol": "ConUnit",
                "text": "tst.w cu_YCCP(a0)",
            },
        ]
        snippets: list[dict[str, object]] = []

        report = usage.build_type_flow_report(manifest_rows, xrefs, snippets)[0]

        self.assertEqual(report["counts"]["typed_base_unresolved_field"], 1)
        self.assertEqual(report["counts"]["prefix_extension_evidence"], 1)
        self.assertEqual(report["counts"]["prefix_extension_unique"], 1)
        self.assertEqual(report["counts"]["type_refinement_applied"], 1)
        self.assertEqual(report["counts"]["resolved_after_type_refinement"], 1)
        self.assertEqual(report["counts"]["resolved_typed_access"], 1)
        self.assertEqual(report["examples"]["type_refinement_applied"][0]["refined_struct_name"], "ConUnit")
        self.assertEqual(
            report["examples"]["resolved_after_type_refinement"][0]["refined_struct_name"],
            "ConUnit",
        )

    def test_type_flow_report_counts_custom_tail_structs(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "typed_base_unresolved_field",
                "kind": "platform_unresolved_typed_access",
                "row_index": 10,
                "stable_key": "tail-row",
                "symbol": "AmigaGuideMsg",
                "value": 0x36,
                "classification_id": 2,
                "classification": "custom_tail_or_mistyped_base",
                "container_candidate_count": 0,
                "text": "move.l $0036(a0),d0",
            }
        ]

        report = usage.build_type_flow_report(manifest_rows, xrefs, [])[0]

        self.assertEqual(report["counts"]["custom_tail_or_mistyped_base"], 1)
        self.assertEqual(report["counts"]["custom_tail_struct:AmigaGuideMsg"], 1)

    def test_suspicious_first_struct_report_finds_stale_struct_names(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "source_id": "demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "platform_typed_access_struct:AmigaGuideMsg",
                "kind": "platform_typed_access",
                "row_index": 3,
                "stable_key": "typed",
                "symbol": "AmigaGuideMsg",
                "text": "cmpi.w #36,agm_Type(a0)",
            }
        ]
        snippets = [
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 4,
                "row": {"kind": "instruction", "text": "\tmove.w agm_Msg(a0),d0\n", "stable_key": "agm-row"},
            }
        ]

        report = usage.build_type_flow_suspicious_first_struct_report(manifest_rows, xrefs, snippets)

        self.assertEqual(report["total"], 2)
        self.assertEqual(report["target_counts"], {"platform_file_manifest:demo": 2})
        self.assertEqual(report["examples"][0]["match"], "AmigaGuideMsg")

    def test_type_flow_report_classifies_numeric_access_causes(self) -> None:
        manifest_rows = [{"id": "platform_file_manifest:demo", "platform": "amiga-hunk"}]
        xrefs = [
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os:exec.library/WaitPort",
                "kind": "os_call",
                "row_index": 1,
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_reg:D0",
                "kind": "os_call_output",
                "row_index": 1,
                "value": "D0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os:exec.library/WaitPort",
                "kind": "os_call",
                "row_index": 28,
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_reg:D0",
                "kind": "os_call_output",
                "row_index": 28,
                "value": "D0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_struct:MP",
                "kind": "os_call_output_struct",
                "row_index": 28,
                "access": "D0",
                "value": "MP",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os:exec.library/CloseLibrary",
                "kind": "os_call",
                "row_index": 50,
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os:exec.library/OpenLibrary",
                "kind": "os_call",
                "row_index": 60,
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_reg:D0",
                "kind": "os_call_output",
                "row_index": 60,
                "value": "D0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os:exec.library/WaitPort",
                "kind": "os_call",
                "row_index": 70,
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_reg:D0",
                "kind": "os_call_output",
                "row_index": 70,
                "value": "D0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os:exec.library/WaitPort",
                "kind": "os_call",
                "row_index": 80,
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_reg:D0",
                "kind": "os_call_output",
                "row_index": 80,
                "value": "D0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_struct:MP",
                "kind": "os_call_output_struct",
                "row_index": 80,
                "access": "D0",
                "value": "MP",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os:exec.library/WaitPort",
                "kind": "os_call",
                "row_index": 90,
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_reg:D0",
                "kind": "os_call_output",
                "row_index": 90,
                "value": "D0",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_struct:MP",
                "kind": "os_call_output_struct",
                "row_index": 90,
                "access": "D0",
                "value": "MP",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os:exec.library/OpenLibrary",
                "kind": "os_call",
                "row_index": 100,
                "resolution": "local_helper",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_reg:D0",
                "kind": "os_call_output",
                "row_index": 100,
                "value": "D0",
                "resolution": "local_helper",
            },
            {
                "target_id": "platform_file_manifest:demo",
                "feature": "os_call_output_struct:LIB",
                "kind": "os_call_output_struct",
                "row_index": 100,
                "access": "D0",
                "value": "LIB",
                "resolution": "local_helper",
            },
        ]
        snippets = [
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 1,
                "row": {"kind": "instruction", "text": "\tjsr _LVOWaitPort(a6)\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 2,
                "row": {"kind": "instruction", "text": "\tmovea.l d0,a0\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 3,
                "row": {"kind": "instruction", "text": "\ttst.w $0014(a0)\n", "stable_key": "api"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 10,
                "row": {
                    "kind": "instruction",
                    "text": "\tmovea.l app_Window(a6),a1\n",
                    "app_slot_refs": [{"symbol": "app_Window"}],
                },
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 11,
                "row": {"kind": "instruction", "text": "\ttst.w $0004(a1)\n", "stable_key": "app"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 20,
                "row": {"kind": "instruction", "text": "\tmovea.l $0010(a7),a2\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 21,
                "row": {"kind": "instruction", "text": "\ttst.w $0004(a2)\n", "stable_key": "stack"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 24,
                "row": {
                    "kind": "instruction",
                    "text": "\tmovea.l app_Window(a6),a4\n",
                    "app_slot_refs": [{"symbol": "app_Window"}],
                    "stable_key": "chain-root",
                },
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 28,
                "row": {"kind": "instruction", "text": "\tjsr _LVOWaitPort(a6)\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 29,
                "row": {"kind": "instruction", "text": "\tmove.l d0,$000100.w\n", "stable_key": "global-store"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 30,
                "row": {"kind": "instruction", "text": "\tmovea.l $000100.w,a3\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 31,
                "row": {"kind": "instruction", "text": "\ttst.w $0004(a3)\n", "stable_key": "global"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 40,
                "row": {"kind": "instruction", "text": "\tmovea.l $0004(a4),a5\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 41,
                "row": {"kind": "instruction", "text": "\ttst.w $0004(a5)\n", "stable_key": "chain"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 50,
                "row": {"kind": "instruction", "text": "\tjsr _LVOCloseLibrary(a6)\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 51,
                "row": {"kind": "instruction", "text": "\ttst.w $0004(a4)\n", "stable_key": "post-call"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 60,
                "row": {"kind": "instruction", "text": "\tjsr _LVOOpenLibrary(a6)\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 61,
                "row": {"kind": "instruction", "text": "\tmovea.l a5,a0\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 62,
                "row": {"kind": "instruction", "text": "\ttst.w $0004(a0)\n", "stable_key": "post-copy"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 70,
                "row": {"kind": "instruction", "text": "\tjsr _LVOWaitPort(a6)\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 71,
                "row": {"kind": "instruction", "text": "\tmove.l d0,d4\n", "stable_key": "register-copy"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 72,
                "row": {"kind": "instruction", "text": "\tmovea.l d4,a2\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 73,
                "row": {"kind": "instruction", "text": "\ttst.w $0004(a2)\n", "stable_key": "register-copy-access"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 80,
                "row": {"kind": "instruction", "text": "\tjsr _LVOWaitPort(a6)\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 81,
                "row": {"kind": "instruction", "text": "\tmove.l d0,d2\n", "stable_key": "copy-source"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 82,
                "row": {"kind": "instruction", "text": "\tmove.l d2,$000200.w\n", "stable_key": "copy-store"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 83,
                "row": {"kind": "instruction", "text": "\tmovea.l $000200.w,a4\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 84,
                "row": {"kind": "instruction", "text": "\ttst.w $0004(a4)\n", "stable_key": "copy-global"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 90,
                "row": {"kind": "instruction", "text": "\tjsr _LVOWaitPort(a6)\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 91,
                "row": {"kind": "instruction", "text": "\tjsr loc_helper(pc)\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 92,
                "row": {"kind": "instruction", "text": "\tmove.l d0,$000300.w\n", "stable_key": "blocked-store"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 93,
                "row": {"kind": "instruction", "text": "\tmovea.l $000300.w,a6\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 94,
                "row": {"kind": "instruction", "text": "\ttst.w $0004(a6)\n", "stable_key": "blocked-global"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 100,
                "row": {"kind": "instruction", "text": "\tbsr.w loc_open_library\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 101,
                "row": {"kind": "instruction", "text": "\tmove.l d0,$000400.w\n", "stable_key": "lib-store"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 102,
                "row": {"kind": "instruction", "text": "\tmovea.l $000400.w,a6\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 103,
                "row": {"kind": "instruction", "text": "\tjsr $FEF2(a6)\n", "stable_key": "lib-lvo"},
            },
        ]

        report = usage.build_type_flow_report(manifest_rows, xrefs, snippets)[0]

        self.assertEqual(
            report["numeric_cause_counts"],
            {
                "api_output_nearby": 1,
                "app_slot_load": 2,
                "global_or_base_slot_load": 4,
                "post_call_existing_base": 1,
                "post_call_register_copy": 2,
                "stack_slot_load": 2,
                "unknown_pointer_chain": 1,
            },
        )
        self.assertEqual(report["counts"]["numeric_address_reg_access_without_type"], 13)
        self.assertEqual(report["counts"]["numeric_cause:api_output_nearby"], 1)
        self.assertEqual(
            report["propagation_chain_counts"],
            {
                "api_output_copy_to_global_or_base_slot_reload": 1,
                "api_output_to_global_or_base_slot_reload": 2,
                "register_to_global_or_base_slot_reload": 1,
            },
        )
        self.assertEqual(report["counts"]["propagation_gap:api_output_storage_reload_untyped_access"], 3)
        self.assertEqual(report["counts"]["propagation_gap:api_output_to_global_or_base_slot_reload"], 2)
        self.assertEqual(report["counts"]["propagation_gap:library_base_reload_lvo_gap"], 1)
        self.assertEqual(report["counts"]["propagation_gap:local_helper_output_storage_gap"], 1)
        self.assertEqual(report["counts"]["app_slot_substructure_access"], 2)
        self.assertEqual(report["counts"]["app_slot_substructure_slot:app_Window"], 2)
        self.assertEqual(report["counts"]["app_slot_substructure_field:app_Window:$0004"], 2)
        self.assertEqual(report["counts"]["app_slot_substructure_suggested_region"], 1)
        self.assertGreaterEqual(report["pointer_chain_root_counts"]["app_slot"], 1)
        self.assertGreaterEqual(report["pointer_chain_stop_counts"]["source_is_app_slot"], 1)
        self.assertEqual(report["app_slot_substructure_suggestions"][0]["slot"], "app_Window")
        self.assertEqual(
            report["app_slot_substructure_suggestions"][0]["inference_kind"],
            "app_slot_pointer_substructure_access",
        )
        self.assertEqual(report["app_slot_substructure_suggestions"][0]["field_count"], 1)
        self.assertEqual(report["app_slot_substructure_suggestions"][0]["fields"][0]["displacement_hex"], "$0004")
        self.assertEqual(
            report["examples"]["app_slot_substructure_access"][0]["app_slot_subaccess"]["slot_access_displacement_hex"],
            "$0004",
        )
        self.assertEqual(
            report["examples"]["numeric_address_reg_access_without_type:app_slot_load"][0]["stable_key"],
            "app",
        )
        self.assertEqual(
            report["examples"]["propagation_chain:api_output_to_global_or_base_slot_reload"][0]["trace"][
                "propagation_chain"
            ]["store_stable_key"],
            "global-store",
        )
        self.assertEqual(
            report["examples"]["propagation_chain:api_output_copy_to_global_or_base_slot_reload"][0]["trace"][
                "propagation_chain"
            ]["store_stable_key"],
            "copy-store",
        )
        self.assertEqual(
            report["examples"]["propagation_chain:register_to_global_or_base_slot_reload"][0]["trace"][
                "propagation_chain"
            ]["store_stable_key"],
            "blocked-store",
        )
        self.assertEqual(
            report["examples"]["propagation_gap:library_base_reload_lvo_gap"][0]["stable_key"],
            "lib-lvo",
        )
        self.assertEqual(
            report["examples"]["propagation_gap:local_helper_output_storage_gap"][0]["stable_key"],
            "lib-lvo",
        )
        self.assertEqual(
            report["examples"]["propagation_gap:local_helper_output_storage_gap"][0]["trace"]["propagation_chain"][
                "api_output_struct"
            ],
            "LIB",
        )
        self.assertEqual(
            report["examples"]["numeric_address_reg_access_without_type:api_output_nearby"][0]["trace"][
                "assignment"
            ]["source"],
            "d0",
        )
        self.assertEqual(
            report["examples"]["numeric_address_reg_access_without_type:api_output_nearby"][0]["trace"][
                "nearest_os_call"
            ]["feature"],
            "os:exec.library/WaitPort",
        )
        self.assertEqual(
            report["examples"]["numeric_address_reg_access_without_type:post_call_existing_base"][0]["trace"][
                "stop_reason"
            ],
            "existing_base_access_after_nearby_os_call",
        )
        self.assertEqual(
            report["examples"]["numeric_address_reg_access_without_type:post_call_existing_base"][0]["trace"][
                "nearest_os_call"
            ]["feature"],
            "os:exec.library/CloseLibrary",
        )
        self.assertEqual(
            report["examples"]["numeric_address_reg_access_without_type:post_call_register_copy"][0]["trace"][
                "stop_reason"
            ],
            "assignment_source_is_not_nearest_call_output_register",
        )
        self.assertNotIn(
            "propagation_chain",
            report["examples"]["numeric_address_reg_access_without_type:post_call_register_copy"][0]["trace"],
        )

    def test_type_flow_numeric_trace_follows_pointer_chain_to_app_slot_root(self) -> None:
        snippets = [
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 1,
                "row": {
                    "kind": "instruction",
                    "text": "\tmovea.l app_Window(a6),a4\n",
                    "app_slot_refs": [{"symbol": "app_Window"}],
                },
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 2,
                "row": {"kind": "instruction", "text": "\tmovea.l $0004(a4),a5\n"},
            },
            {
                "target_id": "platform_file_manifest:demo",
                "row_index": 3,
                "row": {"kind": "instruction", "text": "\ttst.w $0008(a5)\n"},
            },
        ]
        rows_by_target = usage._type_flow_rows_for_target(snippets)
        rows_by_index = {
            "platform_file_manifest:demo": usage._type_flow_rows_by_index(
                rows_by_target, "platform_file_manifest:demo"
            )
        }

        trace = usage._type_flow_numeric_access_trace(
            "platform_file_manifest:demo",
            snippets[2],
            rows_by_target,
            {},
            rows_by_index,
        )

        self.assertEqual(trace["cause"], "unknown_pointer_chain")
        self.assertEqual(trace["pointer_chain"]["root_kind"], "app_slot")
        self.assertEqual(trace["pointer_chain"]["hops"][0]["source"], "$0004(a4)")
        self.assertEqual(trace["pointer_chain"]["hops"][1]["source"], "app_Window(a6)")

    def test_type_flow_delta_summarizes_totals_and_target_changes(self) -> None:
        before = [
            {
                "target_id": "a",
                "source_id": "old-a",
                "platform": "amiga-hunk",
                "opportunity_count": 4,
                "resolved_typed_access_count": 1,
                "counts": {
                    "numeric_address_reg_access_without_type": 4,
                    "prefix_extension_ambiguous": 1,
                    "resolved_typed_access": 1,
                },
                "numeric_cause_counts": {"api_output_nearby": 3, "unknown_pointer_chain": 1},
                "propagation_chain_counts": {"api_output_to_global_or_base_slot_reload": 2},
                "typed_access_provenance_counts": {"api_output": 1},
                "typed_storage_provenance_counts": {"global_slot": 1},
                "struct_counts": {"Library": 1},
                "field_counts": {"Library.LIB_VERSION": 1},
            },
            {
                "target_id": "b",
                "source_id": "b",
                "platform": "amiga-hunk",
                "opportunity_count": 2,
                "resolved_typed_access_count": 0,
                "counts": {"numeric_address_reg_access_without_type": 2},
                "numeric_cause_counts": {"stack_slot_load": 2},
                "struct_counts": {},
                "field_counts": {},
            },
        ]
        after = [
            {
                "target_id": "a",
                "source_id": "new-a",
                "platform": "amiga-hunk",
                "origin": {"display_name": "A"},
                "opportunity_count": 2,
                "resolved_typed_access_count": 3,
                "counts": {
                    "numeric_address_reg_access_without_type": 2,
                    "resolved_typed_access": 3,
                    "resolved_after_type_refinement": 1,
                    "type_refinement_applied": 1,
                },
                "numeric_cause_counts": {"api_output_nearby": 1, "unknown_pointer_chain": 1},
                "propagation_chain_counts": {"api_output_to_global_or_base_slot_reload": 1},
                "typed_access_provenance_counts": {"api_output": 3},
                "typed_storage_provenance_counts": {"global_slot": 2},
                "struct_counts": {"Library": 3},
                "field_counts": {"Library.LIB_VERSION": 3},
            },
            {
                "target_id": "b",
                "source_id": "b",
                "platform": "amiga-hunk",
                "opportunity_count": 2,
                "resolved_typed_access_count": 0,
                "counts": {"numeric_address_reg_access_without_type": 2},
                "numeric_cause_counts": {"stack_slot_load": 2},
                "struct_counts": {},
                "field_counts": {},
            },
        ]

        delta = usage.build_type_flow_report_delta(before, after)

        self.assertEqual(delta["totals"]["opportunity_count"], {"before": 6, "after": 4, "delta": -2})
        self.assertEqual(delta["totals"]["resolved_typed_access_count"], {"before": 1, "after": 3, "delta": 2})
        self.assertEqual(delta["numeric_cause_deltas"]["api_output_nearby"], {"before": 3, "after": 1, "delta": -2})
        self.assertEqual(
            delta["effectiveness_deltas"]["type_refinement_applied"],
            {"before": 0, "after": 1, "delta": 1},
        )
        self.assertEqual(
            delta["propagation_chain_deltas"]["api_output_to_global_or_base_slot_reload"],
            {"before": 2, "after": 1, "delta": -1},
        )
        self.assertEqual(delta["typed_access_provenance_deltas"]["api_output"], {"before": 1, "after": 3, "delta": 2})
        self.assertEqual(delta["typed_storage_provenance_deltas"]["global_slot"], {"before": 1, "after": 2, "delta": 1})
        self.assertEqual(delta["struct_deltas"]["Library"], {"before": 1, "after": 3, "delta": 2})
        self.assertEqual([item["target_id"] for item in delta["target_deltas"]], ["a"])
        self.assertEqual(delta["target_deltas"][0]["origin"], {"display_name": "A"})
        self.assertEqual(
            delta["target_deltas"][0]["count_deltas"]["resolved_after_type_refinement"],
            {"before": 0, "after": 1, "delta": 1},
        )

    def test_type_flow_delta_cli_reads_and_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            before = tmpdir / "before.jsonl"
            after = tmpdir / "after.jsonl"
            output = tmpdir / "delta.json"
            _write_jsonl(before, [{"target_id": "a", "opportunity_count": 1, "resolved_typed_access_count": 0}])
            _write_jsonl(after, [{"target_id": "a", "opportunity_count": 0, "resolved_typed_access_count": 1}])

            result = usage.main(["type-flow-delta", "--before", str(before), "--after", str(after), "--output", str(output)])

            self.assertEqual(result, 0)
            payload = usage.read_type_flow_delta(output)
            self.assertEqual(payload["totals"]["opportunity_count"], {"before": 1, "after": 0, "delta": -1})
            self.assertEqual(payload["totals"]["resolved_typed_access_count"], {"before": 0, "after": 1, "delta": 1})

    def test_type_flow_opportunity_report_ranks_open_shapes(self) -> None:
        rows = [
            {
                "target_id": "a",
                "source_id": "a",
                "platform": "amiga-hunk",
                "origin": {"display_name": "A"},
                "resolved_typed_access_count": 3,
                "counts": {
                    "numeric_address_reg_access_without_type": 2,
                    "typed_base_unresolved_field": 1,
                    "app_slot_substructure_access": 1,
                },
                "numeric_cause_counts": {"app_slot_load": 2},
                "propagation_chain_counts": {"register_to_app_slot_reload": 1},
                "app_slot_substructure_suggestions": [{"slot": "app_input_event"}],
                "examples": {
                    "propagation_chain:register_to_app_slot_reload": [
                        {
                            "trace": {
                                "propagation_chain": {
                                    "kind": "register_to_app_slot_reload",
                                    "storage_kind": "app_slot",
                                },
                                "nearest_os_call": {"feature": "os:exec.library/WaitPort"},
                            }
                        }
                    ]
                },
            },
            {
                "target_id": "b",
                "source_id": "b",
                "platform": "atari-st",
                "counts": {"numeric_address_reg_access_without_type": 8},
                "numeric_cause_counts": {"unknown_pointer_chain": 8},
            },
        ]

        report = usage.build_type_flow_opportunity_report(rows, platform="amiga-hunk")

        self.assertEqual(report["target_count"], 1)
        self.assertEqual(report["totals"]["app_slot_substructure_access"], 1)
        self.assertEqual(report["numeric_cause_counts"], {"app_slot_load": 2})
        self.assertEqual(
            report["platform_open_counts"],
            {
                "amiga-hunk": {
                    "app_slot_substructure_access": 1,
                    "numeric_address_reg_access_without_type": 2,
                    "typed_base_unresolved_field": 1,
                }
            },
        )
        self.assertEqual(report["numeric_cause_by_platform"], {"amiga-hunk": {"app_slot_load": 2}})
        self.assertEqual(report["propagation_chain_by_platform"], {"amiga-hunk": {"register_to_app_slot_reload": 1}})
        self.assertEqual(report["storage_kind_counts"], {"app_slot": 1})
        self.assertEqual(report["api_feature_counts"], {"os:exec.library/WaitPort": 1})
        self.assertEqual(report["targets"][0]["target_id"], "a")
        self.assertEqual(report["targets"][0]["open_score"], 4)
        self.assertEqual(
            report["targets"][0]["app_slot_substructure_suggestions"],
            [{"slot": "app_input_event"}],
        )

    def test_type_flow_opportunities_cli_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            report_path = tmpdir / "type_flow.jsonl"
            output_path = tmpdir / "opportunities.json"
            _write_jsonl(
                report_path,
                [
                    {
                        "target_id": "a",
                        "platform": "amiga-hunk",
                        "counts": {"numeric_address_reg_access_without_type": 1},
                    }
                ],
            )

            result = usage.main(
                [
                    "type-flow-opportunities",
                    "--type-flow-report",
                    str(report_path),
                    "--output",
                    str(output_path),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))["target_count"], 1)

    def test_type_flow_api_audit_groups_api_output_fallout(self) -> None:
        rows = [
            {
                "target_id": "genam",
                "source_id": "genam",
                "platform": "amiga-hunk",
                "examples": {
                    "propagation_chain:api_output_to_global_or_base_slot_reload": [
                        {
                            "trace": {
                                "cause": "global_or_base_slot_load",
                                "pointer_chain": {
                                    "root_kind": "global_or_base_slot",
                                    "stop_reason": "source_is_global_or_base_slot",
                                },
                                "propagation_chain": {
                                    "kind": "api_output_to_global_or_base_slot_reload",
                                    "storage_kind": "global_or_base_slot",
                                    "os_call": {"feature": "os:exec.library/MakeLibrary"},
                                },
                            }
                        }
                    ]
                },
            }
        ]

        report = usage.build_type_flow_api_audit_report(rows, api_feature="os:exec.library/MakeLibrary")

        self.assertEqual(report["feature_count"], 1)
        feature = report["features"][0]
        self.assertEqual(feature["feature"], "os:exec.library/MakeLibrary")
        self.assertEqual(feature["example_count"], 1)
        self.assertEqual(feature["target_count"], 1)
        self.assertEqual(feature["propagation_chain_counts"], {"api_output_to_global_or_base_slot_reload": 1})
        self.assertEqual(feature["storage_kind_counts"], {"global_or_base_slot": 1})

    def test_type_flow_chain_slice_report_ranks_pointer_chain_shapes(self) -> None:
        rows = [
            {
                "target_id": "a",
                "platform": "amiga-hunk",
                "examples": {
                    "numeric_address_reg_access_without_type": [
                        {
                            "trace": {
                                "cause": "unknown_pointer_chain",
                                "pointer_chain": {"root_kind": "stack_slot", "stop_reason": "source_is_stack_slot"},
                                "propagation_chain": {
                                    "kind": "register_to_stack_slot_reload",
                                    "storage_kind": "stack_slot",
                                },
                            }
                        },
                        {
                            "trace": {
                                "cause": "unknown_pointer_chain",
                                "pointer_chain": {"root_kind": "stack_slot", "stop_reason": "source_is_stack_slot"},
                                "propagation_chain": {
                                    "kind": "register_to_stack_slot_reload",
                                    "storage_kind": "stack_slot",
                                },
                            }
                        },
                    ]
                },
            },
            {
                "target_id": "b",
                "platform": "atari-st",
                "examples": {
                    "numeric_address_reg_access_without_type": [
                        {
                            "trace": {
                                "cause": "unknown_pointer_chain",
                                "pointer_chain": {"root_kind": "unknown", "stop_reason": "no_assignment_to_chain_base"},
                            }
                        }
                    ]
                },
            },
        ]

        report = usage.build_type_flow_chain_slice_report(rows, platform="amiga-hunk")

        self.assertEqual(report["slice_count"], 1)
        self.assertEqual(report["slices"][0]["example_count"], 2)
        self.assertEqual(report["slices"][0]["pointer_root"], "stack_slot")
        self.assertEqual(report["slices"][0]["propagation_chain"], "register_to_stack_slot_reload")

    def test_type_flow_storage_access_gap_report_groups_uncovered_storage(self) -> None:
        rows = [{"target_id": "demo", "platform": "amiga-hunk", "source_id": "demo-source"}]
        xrefs = [
            {
                "target_id": "demo",
                "platform": "amiga-hunk",
                "feature": "os:exec.library/AllocMem",
                "kind": "os_call",
                "row_index": 10,
                "section": 0,
                "offset": 0x20,
                "stable_key": "call",
                "symbol": "AllocMem",
                "value": "exec.library",
                "text": "jsr _LVOAllocMem(a6)",
            },
            {
                "target_id": "demo",
                "platform": "amiga-hunk",
                "feature": "os_call_output_reg:D0",
                "kind": "os_call_output",
                "row_index": 10,
                "section": 0,
                "offset": 0x20,
                "stable_key": "call",
                "symbol": "AllocMem",
                "value": "D0",
                "text": "jsr _LVOAllocMem(a6)",
            },
            {
                "target_id": "demo",
                "platform": "amiga-hunk",
                "feature": "typed_storage:any",
                "kind": "typed_storage",
                "row_index": 11,
                "section": 0,
                "offset": 0x24,
                "stable_key": "store",
                "symbol": "void *",
                "access": "app_slot",
                "value": 0x100,
                "text": "move.l d0,app_buffer(a6)",
            },
            {
                "target_id": "demo",
                "platform": "amiga-hunk",
                "feature": "platform_typed_access:any",
                "kind": "platform_typed_access",
                "row_index": 18,
                "section": 0,
                "offset": 0x38,
                "stable_key": "later-typed",
                "symbol": "LIB_VERSION",
                "value": 0x14,
                "text": "cmpi.w #36,LIB_VERSION(a0)",
            },
            {
                "target_id": "demo",
                "platform": "amiga-hunk",
                "feature": "typed_storage:any",
                "kind": "typed_storage",
                "row_index": 30,
                "section": 0,
                "offset": 0x60,
                "stable_key": "lib-store",
                "symbol": "LIB",
                "access": "global_slot",
                "value": 0x200,
                "text": "move.l d0,TimerBase.l",
            },
            {
                "target_id": "demo",
                "platform": "amiga-hunk",
                "feature": "platform_typed_access:any",
                "kind": "platform_typed_access",
                "row_index": 35,
                "section": 0,
                "offset": 0x70,
                "stable_key": "lib-access",
                "symbol": "LIB_VERSION",
                "value": 0x14,
                "text": "cmpi.w #36,LIB_VERSION(a0)",
            },
            {
                "target_id": "demo",
                "platform": "amiga-hunk",
                "feature": "platform_typed_access_struct:LIB",
                "kind": "platform_typed_access",
                "row_index": 35,
                "section": 0,
                "offset": 0x70,
                "stable_key": "lib-access",
                "symbol": "LIB",
                "value": 0x14,
                "text": "cmpi.w #36,LIB_VERSION(a0)",
            },
        ]
        snippets = [
            {
                "target_id": "demo",
                "row_index": 12,
                "row": {
                    "kind": "instruction",
                    "section_index": 0,
                    "start_offset": 0x28,
                    "stable_key": "numeric",
                    "text": "move.l $0004(a0),d1",
                },
            }
        ]

        report = usage.build_type_flow_storage_access_gap_report(rows, xrefs, snippets)

        self.assertEqual(report["total_storage_count"], 2)
        self.assertEqual(report["covered_storage_count"], 1)
        self.assertEqual(report["total_gap_count"], 1)
        self.assertEqual(report["api_feature_counts"], {"os:exec.library/AllocMem": 1})
        self.assertEqual(report["storage_target_counts"], {"app_slot": 1})
        self.assertEqual(report["storage_type_counts"], {"void *": 1})
        gap = report["targets"][0]["gaps"][0]
        self.assertEqual(gap["api_call"]["feature"], "os:exec.library/AllocMem")
        self.assertEqual(gap["first_later_numeric_access"]["text"], "move.l $0004(a0),d1")
        self.assertEqual(gap["first_later_typed_access"]["stable_key"], "later-typed")

    def test_type_flow_storage_access_gaps_cli_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            type_flow = tmpdir / "type_flow.jsonl"
            xrefs = tmpdir / "xrefs.jsonl"
            snippets = tmpdir / "snippets"
            output = tmpdir / "storage_gaps.json"
            _write_jsonl(type_flow, [{"target_id": "demo", "platform": "amiga-hunk"}])
            _write_jsonl(
                xrefs,
                [
                    {
                        "target_id": "demo",
                        "platform": "amiga-hunk",
                        "feature": "os:exec.library/AllocMem",
                        "kind": "os_call",
                        "row_index": 1,
                        "section": 0,
                        "offset": 0x10,
                        "text": "jsr _LVOAllocMem(a6)",
                    },
                    {
                        "target_id": "demo",
                        "platform": "amiga-hunk",
                        "feature": "os_call_output_reg:D0",
                        "kind": "os_call_output",
                        "row_index": 1,
                        "section": 0,
                        "offset": 0x10,
                        "symbol": "AllocMem",
                        "value": "D0",
                        "text": "jsr _LVOAllocMem(a6)",
                    },
                    {
                        "target_id": "demo",
                        "platform": "amiga-hunk",
                        "feature": "typed_storage:any",
                        "kind": "typed_storage",
                        "row_index": 2,
                        "section": 0,
                        "offset": 0x14,
                        "symbol": "void *",
                        "access": "global_slot",
                        "value": 0x80,
                        "text": "move.l d0,buffer.l",
                    },
                ],
            )
            usage.write_usage_snippet_rows(snippets, [])

            result = usage.main(
                [
                    "type-flow-storage-access-gaps",
                    "--type-flow-report",
                    str(type_flow),
                    "--xrefs",
                    str(xrefs),
                    "--snippet-rows",
                    str(snippets),
                    "--api-feature",
                    "os:exec.library/AllocMem",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["total_gap_count"], 1)
            self.assertEqual(payload["api_feature"], "os:exec.library/AllocMem")

    def test_type_flow_target_baseline_delta_reports_per_target_changes(self) -> None:
        baseline = {
            "targets": [
                {
                    "target_id": "a",
                    "platform": "amiga-hunk",
                    "opportunity_count": 4,
                    "resolved_typed_access_count": 1,
                    "counts": {"numeric_address_reg_access_without_type": 4},
                    "numeric_cause_counts": {"unknown_pointer_chain": 4},
                }
            ]
        }
        current = [
            {
                "target_id": "a",
                "platform": "amiga-hunk",
                "opportunity_count": 2,
                "resolved_typed_access_count": 3,
                "counts": {"numeric_address_reg_access_without_type": 2, "resolved_typed_access": 3},
                "numeric_cause_counts": {"unknown_pointer_chain": 2},
            }
        ]

        report = usage.build_type_flow_target_baseline_delta_report(current, baseline)

        delta = report["delta"]
        self.assertEqual(delta["totals"]["opportunity_count"], {"before": 4, "after": 2, "delta": -2})
        self.assertEqual(delta["totals"]["resolved_typed_access_count"], {"before": 1, "after": 3, "delta": 2})
        self.assertEqual(delta["target_deltas"][0]["target_id"], "a")

    def test_type_flow_baseline_report_keeps_aggregate_metrics(self) -> None:
        rows = [
            {
                "target_id": "a",
                "counts": {
                    "numeric_address_reg_access_without_type": 3,
                    "resolved_typed_access": 2,
                    "typed_storage": 4,
                },
                "numeric_cause_counts": {"unknown_pointer_chain": 2, "stack_slot_load": 1},
                "propagation_chain_counts": {"register_to_stack_slot_reload": 1},
                "pointer_chain_root_counts": {"stack_slot": 1, "unknown": 2},
                "pointer_chain_stop_counts": {"source_is_stack_slot": 1, "no_assignment_to_chain_base": 2},
                "typed_access_provenance_counts": {"api_output": 2},
                "typed_storage_provenance_counts": {"stack_slot": 4},
            }
        ]

        baseline = usage.build_type_flow_baseline_report(rows)

        self.assertEqual(baseline["target_count"], 1)
        self.assertEqual(baseline["totals"]["resolved_typed_access"], 2)
        self.assertEqual(baseline["numeric_cause_counts"]["unknown_pointer_chain"], 2)
        self.assertEqual(baseline["pointer_chain_root_counts"]["stack_slot"], 1)

    def test_type_flow_baseline_check_rejects_metric_regressions(self) -> None:
        current = [
            {
                "target_id": "a",
                "counts": {
                    "numeric_address_reg_access_without_type": 3,
                    "resolved_typed_access": 1,
                    "typed_storage": 1,
                },
                "numeric_cause_counts": {"unknown_pointer_chain": 3},
            }
        ]
        baseline = {
            "totals": {
                "numeric_address_reg_access_without_type": 2,
                "resolved_typed_access": 2,
                "typed_storage": 2,
            },
            "numeric_cause_counts": {"unknown_pointer_chain": 2},
        }

        gate = usage.build_type_flow_baseline_gate_report(current, [], [], baseline)

        self.assertEqual(gate["ok"], False)
        self.assertEqual(
            {regression["kind"] for regression in gate["metric_regressions"]},
            {"above_baseline_maximum", "below_baseline_minimum", "numeric_cause_above_baseline_maximum"},
        )

    def test_type_flow_baseline_cli_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            report_path = tmpdir / "type_flow.jsonl"
            output_path = tmpdir / "baseline.json"
            _write_jsonl(
                report_path,
                [
                    {
                        "target_id": "a",
                        "counts": {"resolved_typed_access": 1},
                        "numeric_cause_counts": {"unknown_pointer_chain": 1},
                    }
                ],
            )

            result = usage.main(
                [
                    "type-flow-baseline",
                    "--type-flow-report",
                    str(report_path),
                    "--output",
                    str(output_path),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(usage.read_type_flow_baseline(output_path)["totals"]["resolved_typed_access"], 1)

    def test_type_flow_baseline_check_cli_fails_on_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            report_path = tmpdir / "type_flow.jsonl"
            unresolved = tmpdir / "unresolved.jsonl"
            xrefs = tmpdir / "xrefs.jsonl"
            baseline = tmpdir / "baseline.json"
            output = tmpdir / "gate.json"
            _write_jsonl(report_path, [{"target_id": "a", "counts": {"resolved_typed_access": 0}}])
            _write_jsonl(unresolved, [])
            _write_jsonl(xrefs, [])
            baseline.write_text(
                json.dumps({"totals": {"resolved_typed_access": 1}}) + "\n",
                encoding="utf-8",
            )

            result = usage.main(
                [
                    "type-flow-baseline-check",
                    "--type-flow-report",
                    str(report_path),
                    "--unresolved-typed-fields",
                    str(unresolved),
                    "--xrefs",
                    str(xrefs),
                    "--baseline",
                    str(baseline),
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 1)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["ok"], False)

    def test_type_flow_correctness_report_rejects_dominant_exact_ties(self) -> None:
        report = usage.build_type_flow_correctness_report(
            [],
            [
                {
                    "root_struct_name": "MN",
                    "displacement_hex": "$0024",
                    "dominant_candidate": {"struct_name": "IO", "exact_access_size_match_count": 1},
                    "candidate_rankings": [
                        {"struct_name": "IO", "exact_access_size_match_count": 1},
                        {"struct_name": "RexxMsg", "exact_access_size_match_count": 1},
                    ],
                }
            ],
            [],
        )

        self.assertEqual(report["ok"], False)
        self.assertEqual(report["violations"][0]["kind"], "dominant_candidate_exact_size_tie")

    def test_type_flow_gate_rejects_suspicious_first_struct_xrefs(self) -> None:
        gate = usage.build_type_flow_gate_report(
            [],
            [],
            [
                {
                    "target_id": "demo",
                    "feature": "platform_typed_access_struct:AmigaGuideMsg",
                    "kind": "platform_typed_access",
                    "row_index": 4,
                    "text": "move.l agm_Reserved(a0),d0",
                }
            ],
        )

        self.assertEqual(gate["ok"], False)
        self.assertEqual(
            gate["correctness"]["violations"][0]["kind"],
            "suspicious_first_struct_type_flow",
        )

    def test_type_flow_gate_accepts_audited_refinement_shapes(self) -> None:
        type_flow_rows = [
            {
                "target_id": "demo",
                "counts": {
                    "resolved_typed_access": 2,
                    "type_refinement_applied": 2,
                    "resolved_after_type_refinement": 1,
                },
            }
        ]
        unresolved_rows = [
            {
                "root_struct_name": "LIB",
                "displacement_hex": "$00CE",
                "dominant_candidate": {"struct_name": "GfxBase", "exact_access_size_match_count": 1},
                "candidate_rankings": [
                    {"struct_name": "GfxBase", "exact_access_size_match_count": 1},
                    {"struct_name": "ExecBase", "exact_access_size_match_count": 0},
                ],
            },
            {
                "root_struct_name": "MN",
                "displacement_hex": "$0018",
                "candidate_rankings": [
                    {"struct_name": "ColorTextFont", "exact_access_size_match_count": 1},
                    {"struct_name": "TextFont", "exact_access_size_match_count": 1},
                ],
            },
        ]
        xrefs = [
            {
                "target_id": "demo",
                "feature": "platform_type_refinement:applied",
                "kind": "platform_type_refinement",
                "classification_id": 1,
                "classification": "prefix_extension",
                "container_field_expr": "gb_DisplayFlags",
                "refined_struct_name": "GfxBase",
            },
            {
                "target_id": "demo",
                "feature": "platform_type_refinement:applied",
                "kind": "platform_type_refinement",
                "classification_id": 1,
                "classification": "prefix_extension",
                "container_field_expr": "tf_XSize",
                "refined_struct_name": "TextFont",
            },
        ]

        gate = usage.build_type_flow_gate_report(type_flow_rows, unresolved_rows, xrefs)

        self.assertEqual(gate["ok"], True)
        self.assertEqual(gate["correctness"]["applied_refinement_count"], 2)

    def test_type_flow_check_cli_fails_on_correctness_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            type_flow = tmpdir / "type_flow.jsonl"
            unresolved = tmpdir / "unresolved.jsonl"
            xrefs = tmpdir / "xrefs.jsonl"
            output = tmpdir / "gate.json"
            _write_jsonl(type_flow, [])
            _write_jsonl(
                unresolved,
                [
                    {
                        "dominant_candidate": {"struct_name": "IO", "exact_access_size_match_count": 1},
                        "candidate_rankings": [
                            {"struct_name": "IO", "exact_access_size_match_count": 1},
                            {"struct_name": "RexxMsg", "exact_access_size_match_count": 1},
                        ],
                    }
                ],
            )
            _write_jsonl(xrefs, [])

            result = usage.main(
                [
                    "type-flow-check",
                    "--type-flow-report",
                    str(type_flow),
                    "--unresolved-typed-fields",
                    str(unresolved),
                    "--xrefs",
                    str(xrefs),
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 1)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["ok"], False)

    def test_type_flow_snapshot_cli_writes_sanitized_report_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            report = tmpdir / "report.jsonl"
            out_dir = tmpdir / "snapshots"
            _write_jsonl(report, [{"target_id": "a", "opportunity_count": 1}])

            result = usage.main(
                [
                    "type-flow-snapshot",
                    "--report",
                    str(report),
                    "--output-dir",
                    str(out_dir),
                    "--name",
                    "../before api output",
                ]
            )

            self.assertEqual(result, 0)
            snapshot = out_dir / "before_api_output.jsonl"
            self.assertEqual(usage.read_type_flow_report(snapshot), [{"target_id": "a", "opportunity_count": 1}])

    def test_type_flow_snapshot_check_cli_writes_snapshot_and_gate_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            before = tmpdir / "before.jsonl"
            report = tmpdir / "report.jsonl"
            unresolved = tmpdir / "unresolved.jsonl"
            xrefs = tmpdir / "xrefs.jsonl"
            out_dir = tmpdir / "snapshots"
            output = tmpdir / "gate.json"
            _write_jsonl(before, [{"target_id": "a", "opportunity_count": 1, "resolved_typed_access_count": 0}])
            _write_jsonl(report, [{"target_id": "a", "opportunity_count": 0, "resolved_typed_access_count": 1}])
            _write_jsonl(unresolved, [])
            _write_jsonl(xrefs, [])

            result = usage.main(
                [
                    "type-flow-snapshot-check",
                    "--type-flow-report",
                    str(report),
                    "--unresolved-typed-fields",
                    str(unresolved),
                    "--xrefs",
                    str(xrefs),
                    "--before",
                    str(before),
                    "--output-dir",
                    str(out_dir),
                    "--name",
                    "after type propagation",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(result, 0)
            snapshot = out_dir / "after_type_propagation.jsonl"
            self.assertEqual(usage.read_type_flow_report(snapshot), [{"target_id": "a", "opportunity_count": 0, "resolved_typed_access_count": 1}])
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["snapshot_path"], str(snapshot))
            self.assertEqual(payload["delta"]["totals"]["resolved_typed_access_count"], {"before": 0, "after": 1, "delta": 1})

    def test_builds_stable_manifest_and_records_analysis_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            image_path = tmpdir / "disk.adf"
            file_bytes = b"\x00\x00\x03\xf3bad hunk"
            image_path.write_bytes(file_bytes)
            disk_entry = {
                "id": "amiga-disk/test",
                "platform": "amiga-disk",
                "sha256": sha256(file_bytes),
                "size": len(file_bytes),
                "origin": {
                    "display_name": "disk.adf",
                    "source_relpath": str(image_path),
                    "container_relpath": None,
                    "member_name": None,
                },
                "expect": {
                    "status": "ok",
                    "inspect": {
                        "entries": [
                            {
                                "path": "HELLO",
                                "kind": 1,
                                "byte_size": len(file_bytes),
                                "extents": [{"image_offset": 0, "byte_size": len(file_bytes)}],
                            }
                        ],
                    },
                },
            }
            file_entry = {
                "id": "amiga-hunk/test",
                "platform": "amiga-hunk",
                "sha256": sha256(file_bytes),
                "size": len(file_bytes),
                "disk_sha256": sha256(file_bytes),
                "origin": {
                    "display_name": "disk.adf",
                    "source_relpath": str(image_path),
                    "container_relpath": None,
                    "member_name": None,
                    "in_image_path": "HELLO",
                },
                "file_ref": {"disk_platform": "amiga-disk", "disk_id": "amiga-disk/test", "extents": []},
                "expect": {
                    "status": "ok",
                    "inspect": {"platform": "amiga-hunk", "file_kind": "executable", "fixup_count": 2},
                },
            }
            disk_manifest = tmpdir / "disk.jsonl"
            file_manifest = tmpdir / "file.jsonl"
            _write_jsonl(disk_manifest, [disk_entry])
            _write_jsonl(file_manifest, [file_entry])

            with mock.patch.object(
                usage,
                "analyze_executable_file",
                side_effect=RuntimeError("exception: access violation reading 0x00000230950BC3B0"),
            ):
                rows = usage.build_usage_manifest(disk_manifest, file_manifest, root=tmpdir)

            ids = [row["id"] for row in rows]
            self.assertEqual(ids, ["platform_disk_manifest:amiga-disk/test", "platform_file_manifest:amiga-hunk/test"])
            file_row = rows[1]
            counts = file_row["feature_counts"]
            self.assertEqual(counts["format:executable"], 1)
            self.assertEqual(counts["relocation:fixup"], 2)
            self.assertEqual(counts["diagnostic:analysis_error"], 1)
            self.assertEqual(
                file_row["feature_examples"]["diagnostic:analysis_error"],
                [{"message": "exception: access violation reading <address>"}],
            )

    def test_build_usage_outputs_includes_project_targets_with_effective_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            disk_manifest = tmpdir / "disk.jsonl"
            file_manifest = tmpdir / "file.jsonl"
            _write_jsonl(disk_manifest, [])
            _write_jsonl(file_manifest, [])
            binary_path = tmpdir / "demo.hunk"
            binary_path.write_bytes(b"\0\0\3\xf3")
            target_dir = tmpdir / "targets" / "demo_project"
            target_dir.mkdir(parents=True)
            (target_dir / "source_binary.json").write_text(
                json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
                encoding="utf-8",
            )
            (target_dir / ".project.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "origin": {
                            "filename": "Demo",
                            "platform": "amiga-hunk",
                            "sha256": sha256(binary_path.read_bytes()),
                            "size": binary_path.stat().st_size,
                        },
                    }
                ),
                encoding="utf-8",
            )
            metadata_path = tmpdir / "effective_metadata.json"
            metadata_path.write_text("{}", encoding="utf-8")
            calls: list[tuple[object, ...]] = []

            @contextlib.contextmanager
            def fake_effective_metadata_file(target: Path):
                self.assertEqual(target, target_dir)
                yield metadata_path

            def fake_analyze_project_hunk_file(
                platform: str, path: Path, target: Path, *, root: Path
            ) -> dict[str, object]:
                calls.append((platform, path, target, root))
                return {
                    "profile": {"generation": "facts_v2_listing_artifact_window"},
                    "analysis": {"sections": []},
                    "listing": {"rows": []},
                }

            with mock.patch.object(usage, "effective_metadata_file", fake_effective_metadata_file):
                with mock.patch.object(usage, "analyze_project_hunk_file", fake_analyze_project_hunk_file):
                    rows, xrefs, snippets = usage.build_usage_outputs(disk_manifest, file_manifest, root=tmpdir)

            self.assertEqual([row["id"] for row in rows], ["project_target:demo_project"])
            self.assertEqual(rows[0]["feature_counts"]["project_target:any"], 1)
            self.assertEqual(rows[0]["feature_counts"]["analysis:facts_v2"], 1)
            self.assertEqual(calls[0], ("amiga-hunk", binary_path, target_dir, tmpdir))
            self.assertIn("project_target:any", {xref["feature"] for xref in xrefs})
            self.assertEqual(snippets, [])

    def test_build_usage_outputs_parallel_matches_serial_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            disk_manifest = tmpdir / "disk.jsonl"
            file_manifest = tmpdir / "file.jsonl"
            _write_jsonl(disk_manifest, [])
            _write_jsonl(file_manifest, [])
            for name in ("alpha", "beta"):
                binary_path = tmpdir / f"{name}.hunk"
                binary_path.write_bytes(b"\0\0\3\xf3")
                target_dir = tmpdir / "targets" / name
                target_dir.mkdir(parents=True)
                (target_dir / "source_binary.json").write_text(
                    json.dumps({"kind": "hunk_file", "path": str(binary_path)}),
                    encoding="utf-8",
                )
                (target_dir / ".project.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 2,
                            "origin": {
                                "filename": name,
                                "platform": "amiga-hunk",
                                "sha256": sha256(binary_path.read_bytes()),
                                "size": binary_path.stat().st_size,
                            },
                        }
                    ),
                    encoding="utf-8",
                )

            @contextlib.contextmanager
            def fake_effective_metadata_file(_target: Path):
                yield None

            def fake_analyze_project_hunk_file(
                _platform: str, path: Path, _target: Path, *, root: Path
            ) -> dict[str, object]:
                return {
                    "profile": {"generation": "facts_v2_listing_artifact_window"},
                    "analysis": {"sections": []},
                    "listing": {
                        "rows": [
                            {
                                "kind": "instruction",
                                "text": f"\tjsr {path.stem}\n",
                                "row_index": 0,
                            }
                        ]
                    },
                }

            with mock.patch.object(usage, "effective_metadata_file", fake_effective_metadata_file):
                with mock.patch.object(usage, "analyze_project_hunk_file", fake_analyze_project_hunk_file):
                    serial = usage.build_usage_outputs(disk_manifest, file_manifest, root=tmpdir, max_workers=1)
                    parallel = usage.build_usage_outputs(disk_manifest, file_manifest, root=tmpdir, max_workers=2)

            self.assertEqual(parallel, serial)

    def test_non_executable_file_rows_use_format_tags_without_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            row = usage.collect_file_usage_row(
                {
                    "id": "amiga-text/test",
                    "platform": "amiga-text",
                    "sha256": "abc",
                    "size": 12,
                    "origin": {"display_name": "readme", "source_relpath": "readme"},
                    "expect": {
                        "status": "ok",
                        "inspect": {"platform": "amiga-text", "file_kind": "text", "line_count": 1},
                    },
                },
                None,
                Path(tmp),
            )

        counts = row["feature_counts"]
        self.assertEqual(counts["format:text"], 1)
        self.assertEqual(counts["inspect_platform:amiga-text"], 1)
        self.assertNotIn("analysis:facts_v2", counts)
        self.assertNotIn("diagnostic:analysis_error", counts)

    def test_query_filters_by_feature_and_platform(self) -> None:
        rows = [
            {
                "id": "a",
                "source_id": "source/a",
                "platform": "amiga-hunk",
                "origin": {"display_name": "a"},
                "feature_counts": {"data:copper_list": 2},
                "feature_examples": {"data:copper_list": [{"offset": 4}]},
            },
            {
                "id": "b",
                "source_id": "source/b",
                "platform": "atari-st",
                "origin": {"display_name": "b"},
                "feature_counts": {"data:copper_list": 1},
                "feature_examples": {},
            },
        ]

        summary = usage.feature_summary(rows)
        query = usage.query_usage_manifest(rows, "data:copper_list", platform="amiga-hunk")

        self.assertEqual(summary, [{"feature": "data:copper_list", "occurrence_count": 3, "target_count": 2}])
        self.assertEqual(len(query), 1)
        self.assertEqual(query[0]["id"], "a")
        self.assertEqual(query[0]["examples"], [{"offset": 4}])

    def test_query_filters_by_feature_group(self) -> None:
        rows = [
            {
                "id": "a",
                "source_id": "source/a",
                "platform": "amiga-hunk",
                "origin": {"display_name": "a"},
                "feature_counts": {
                    "hardware:custom/display": 2,
                    "display:bitplanes:5": 1,
                    "orphan-code:signal": 1,
                    "os_call:any": 1,
                    "table:kind:relative_code_dispatch": 1,
                    "table:consumer": 1,
                    "memory-layout:kind:bitmap": 1,
                    "platform_field:IO_COMMAND": 1,
                    "target-pattern:relative_lookup_dispatch": 1,
                },
                "feature_examples": {
                    "hardware:custom/display": [{"offset": 4}],
                    "display:bitplanes:5": [{"offset": 6}],
                    "orphan-code:signal": [{"offset": 10}],
                    "table:kind:relative_code_dispatch": [{"offset": 12}],
                    "table:consumer": [{"offset": 12, "consumer_offset": 4}],
                    "memory-layout:kind:bitmap": [{"offset": 14, "runtime_address": 0x10000}],
                    "platform_field:IO_COMMAND": [{"offset": 8}],
                },
            },
            {
                "id": "b",
                "source_id": "source/b",
                "platform": "amiga-hunk",
                "origin": {"display_name": "b"},
                "feature_counts": {"runtime:copied_code": 1},
                "feature_examples": {},
            },
        ]
        xrefs = [
            {"target_id": "a", "feature": "hardware:custom/display", "row_index": 3, "platform": "amiga-hunk"},
            {"target_id": "a", "feature": "platform_field:IO_COMMAND", "row_index": 4, "platform": "amiga-hunk"},
            {"target_id": "a", "feature": "orphan-code:signal", "row_index": 5, "platform": "amiga-hunk"},
            {"target_id": "a", "feature": "table:kind:relative_code_dispatch", "row_index": 6, "platform": "amiga-hunk"},
            {"target_id": "a", "feature": "memory-layout:kind:bitmap", "row_index": 7, "platform": "amiga-hunk"},
            {"target_id": "b", "feature": "runtime:copied_code", "row_index": 7, "platform": "amiga-hunk"},
        ]

        query = usage.query_usage_manifest(rows, "", group="hardware")
        display_query = usage.query_usage_manifest(rows, "", group="display")
        analysis_query = usage.query_usage_manifest(rows, "", group="analysis")
        table_query = usage.query_usage_manifest(rows, "", group="tables")
        memory_query = usage.query_usage_manifest(rows, "", group="memory")
        typed_query = usage.query_usage_manifest(rows, "", group="platform_types")
        pattern_query = usage.query_usage_manifest(rows, "", group="patterns")
        xref_query = usage.query_usage_xrefs(xrefs, group="hardware")
        analysis_xref_query = usage.query_usage_xrefs(xrefs, group="analysis")
        table_xref_query = usage.query_usage_xrefs(xrefs, group="tables")
        memory_xref_query = usage.query_usage_xrefs(xrefs, group="memory")
        typed_xref_query = usage.query_usage_xrefs(xrefs, group="platform_types")

        self.assertEqual([item["id"] for item in query], ["a"])
        self.assertEqual(query[0]["count"], 2)
        self.assertEqual(query[0]["examples"], [{"offset": 4}])
        self.assertEqual([item["id"] for item in display_query], ["a"])
        self.assertEqual(display_query[0]["count"], 3)
        self.assertEqual([item["id"] for item in analysis_query], ["a"])
        self.assertEqual(analysis_query[0]["count"], 1)
        self.assertEqual([item["id"] for item in table_query], ["a"])
        self.assertEqual(table_query[0]["count"], 2)
        self.assertEqual([item["id"] for item in memory_query], ["a"])
        self.assertEqual(memory_query[0]["count"], 1)
        self.assertEqual([item["id"] for item in typed_query], ["a"])
        self.assertEqual(typed_query[0]["count"], 1)
        self.assertEqual([item["id"] for item in pattern_query], ["a"])
        self.assertEqual(pattern_query[0]["count"], 1)
        self.assertEqual([item["target_id"] for item in xref_query], ["a"])
        self.assertEqual([item["target_id"] for item in analysis_xref_query], ["a"])
        self.assertEqual([item["target_id"] for item in table_xref_query], ["a"])
        self.assertEqual([item["target_id"] for item in memory_xref_query], ["a"])
        self.assertEqual([item["target_id"] for item in typed_xref_query], ["a"])

    def test_builds_variant_index_for_same_named_file_different_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "files.jsonl"
            rows = [
                {
                    "id": "amiga-hunk/aaa",
                    "platform": "amiga-hunk",
                    "sha256": "a" * 64,
                    "size": 4,
                    "disk_sha256": "d1",
                    "origin": {
                        "display_name": "Bloodwych (1989)(Image Works)[b2].zip",
                        "source_relpath": "resources/Bloodwych b2.zip",
                        "container_relpath": "resources/Bloodwych b2.zip",
                        "member_name": "Bloodwych (1989)(Image Works)[b2].adf",
                        "in_image_path": "C/BLOODWYCH",
                    },
                    "file_ref": {"disk_id": "disk/a"},
                    "expect": {"status": "ok"},
                },
                {
                    "id": "amiga-hunk/bbb",
                    "platform": "amiga-hunk",
                    "sha256": "b" * 64,
                    "size": 5,
                    "disk_sha256": "d2",
                    "origin": {
                        "display_name": "Bloodwych (1989)(Image Works)[cr QTX].zip",
                        "source_relpath": "resources/Bloodwych cr.zip",
                        "container_relpath": "resources/Bloodwych cr.zip",
                        "member_name": "Bloodwych (1989)(Image Works)[cr QTX].adf",
                        "in_image_path": "c/bloodwych",
                    },
                    "file_ref": {"disk_id": "disk/b"},
                    "expect": {"status": "ok"},
                },
                {
                    "id": "amiga-hunk/ccc",
                    "platform": "amiga-hunk",
                    "sha256": "c" * 64,
                    "size": 5,
                    "disk_sha256": "d3",
                    "origin": {
                        "display_name": "Bloodwych - The Extended Levels (1989)(Image Works).zip",
                        "source_relpath": "resources/Bloodwych ext.zip",
                        "container_relpath": "resources/Bloodwych ext.zip",
                        "member_name": "Bloodwych - The Extended Levels (1989)(Image Works).adf",
                        "in_image_path": "C/BLOODWYCH",
                    },
                    "file_ref": {"disk_id": "disk/c"},
                    "expect": {"status": "ok"},
                },
            ]
            _write_jsonl(manifest, rows)

            variants = usage.build_variant_index(manifest)

        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0]["platform"], "amiga-hunk")
        self.assertEqual(variants[0]["title_family"], "bloodwych")
        self.assertEqual(variants[0]["file_path_key"], "c/bloodwych")
        self.assertEqual(variants[0]["unique_hash_count"], 2)
        self.assertEqual(
            [target["target_id"] for target in variants[0]["targets"]],
            ["platform_file_manifest:amiga-hunk/aaa", "platform_file_manifest:amiga-hunk/bbb"],
        )

    def test_variant_index_uses_alternate_origins_without_duplicate_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "files.jsonl"
            rows = [
                {
                    "id": "atari-st/aaa",
                    "platform": "atari-st",
                    "sha256": "a" * 64,
                    "size": 4,
                    "origin": {
                        "display_name": "Magicland Dizzy (1991)(Codemasters)[cr Elite][t].st",
                        "source_relpath": "resources/magic.st",
                        "container_relpath": None,
                        "member_name": None,
                        "in_image_path": "AUTO/MAG_LAND.PRG",
                        "alternate_origins": [
                            {
                                "display_name": "Magicland Dizzy (1991)(Codemasters)[cr Elite][t].st",
                                "source_relpath": "resources/magic.st",
                                "container_relpath": None,
                                "member_name": None,
                                "in_image_path": "MAG_LAND.PRG",
                            }
                        ],
                    },
                    "expect": {"status": "ok"},
                },
                {
                    "id": "atari-st/bbb",
                    "platform": "atari-st",
                    "sha256": "b" * 64,
                    "size": 5,
                    "origin": {
                        "display_name": "Magicland Dizzy (1991)(Codemasters)[cr Other].st",
                        "source_relpath": "resources/magic-other.st",
                        "container_relpath": None,
                        "member_name": None,
                        "in_image_path": "MAG_LAND.PRG",
                    },
                    "expect": {"status": "ok"},
                },
            ]
            _write_jsonl(manifest, rows)

            variants = usage.build_variant_index(manifest)

        matching = [row for row in variants if row["file_path_key"] == "mag_land.prg"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["target_count"], 2)
        self.assertEqual(
            [target["target_id"] for target in matching[0]["targets"]],
            ["platform_file_manifest:atari-st/aaa", "platform_file_manifest:atari-st/bbb"],
        )
        self.assertEqual(matching[0]["targets"][0]["origin"]["in_image_path"], "MAG_LAND.PRG")

    def test_cli_query_json_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "usage.jsonl"
            usage.write_usage_manifest(
                manifest,
                [
                    {
                        "id": "z",
                        "source_id": "source/z",
                        "platform": "amiga-text",
                        "origin": {"display_name": "z"},
                        "feature_counts": {"format:text": 1},
                        "feature_examples": {"format:text": [{"text": "z"}]},
                    },
                    {
                        "id": "a",
                        "source_id": "source/a",
                        "platform": "amiga-text",
                        "origin": {"display_name": "a"},
                        "feature_counts": {"format:text": 1},
                        "feature_examples": {"format:text": [{"text": "a"}]},
                    },
                ],
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = usage.main(
                    ["query", "--manifest", str(manifest), "--feature", "format:text", "--platform", "amiga-text", "--json"]
                )

        self.assertEqual(result, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual([item["id"] for item in payload], ["a", "z"])


if __name__ == "__main__":
    unittest.main()
