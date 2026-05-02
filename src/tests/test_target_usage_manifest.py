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
    def test_extracts_structured_analysis_and_listing_features(self) -> None:
        bag = usage.FeatureBag()
        usage._add_executable_analysis_features(
            {
                "profile": {"generation": "facts_v2_full_listing"},
                "analysis": {
                    "findings": {"required_cpu": 2, "cpu_violation_count": 1},
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
                                }
                            ],
                            "violation_count": 2,
                            "recovered_indirect_site_count": 3,
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
                            "kind": "data",
                            "text": "\tdc.w bplcon0,BPU2|BPU1|COLORON\n",
                            "section_index": 0,
                            "start_offset": 0x60,
                            "data_class": "copper_list",
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
        self.assertEqual(counts["platform_typed_access:any"], 2)
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
        self.assertEqual(counts["analysis:indirect_site"], 3)
        self.assertEqual(counts["data:string_ref"], 4)
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
        self.assertEqual(examples["os:exec.library/AllocMem"][0]["offset"], 0x20)

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
                            {"offset": 0x30, "kind": 2, "displacement": 0x234, "base_name": "DOSBase"}
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
                            {"storage_offset": 0x40, "storage_address": 0x40, "runtime_address": 0x400, "kind": 2}
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
                            }
                        ],
                    },
                    {
                        "kind": "directive",
                        "text": "\tORG $400\n",
                        "section_index": 0,
                        "start_offset": 0x40,
                        "stable_key": "row-runtime",
                    },
                    {
                        "kind": "data",
                        "text": "\tdc.w bplcon0,BPU2|BPU1|BPU0|COLORON\n",
                        "section_index": 0,
                        "start_offset": 0x50,
                        "stable_key": "row-copper",
                        "data_class": "copper_list",
                    },
                    {
                        "kind": "instruction",
                        "text": "\tmove.w #$1234,_custom+aud0+ac_len.l\n",
                        "section_index": 0,
                        "start_offset": 0x60,
                        "stable_key": "row-hw",
                    },
                ],
            },
        }

        xrefs = usage._file_usage_xrefs(target_row, {}, combined, None)
        by_feature = {(xref["feature"], xref["kind"], xref["offset"], xref["row_index"]) for xref in xrefs}
        by_feature_resolution = {
            (xref["feature"], xref["kind"], xref["row_index"], xref.get("resolution")) for xref in xrefs
        }
        snippets = usage._snippet_rows_for_xrefs(target_row, combined, xrefs, before=1, after=0)

        self.assertIn(("os:exec.library/AllocMem", "os_call", 0x20, 1), by_feature)
        self.assertIn(("os_call:any", "os_call", 0x20, 1), by_feature)
        self.assertIn(("os_call_library:exec.library", "os_call", 0x20, 1), by_feature)
        self.assertIn(("os_call_output_reg:D0", "os_call_output", 0x20, 1), by_feature)
        self.assertIn(("value_domain:exec.allocmem.result", "value_domain", 0x20, 1), by_feature)
        self.assertIn(("struct:MemHeader", "struct", 0x20, 1), by_feature)
        self.assertIn(("os:exec.library/AllocMem", "os_call", 1, "local_wrapper"), by_feature_resolution)
        self.assertIn(("os_library:exec.library", "os_library", None, None), by_feature_resolution)
        self.assertIn(("label:any", "label_definition", 0x20, 0), by_feature)
        self.assertIn(("label:definition", "label_definition", 0x20, 0), by_feature)
        self.assertIn(("label:reference", "label_ref", 0x20, 1), by_feature)
        self.assertIn(("xref:segment_ref", "segment_ref", 0x20, 1), by_feature)
        self.assertIn(("xref:code_ref", "segment_ref", 0x20, 1), by_feature)
        self.assertIn(("platform_effect:write_base_slot", "platform_effect", 0x30, 2), by_feature)
        self.assertIn(("app_slot:base_slot", "app_slot_base_slot", 0x30, 2), by_feature)
        self.assertIn(("app_slot_base:DOSBase", "app_slot_base_slot", 0x30, 2), by_feature)
        self.assertIn(("app_slot:write", "app_slot_ref", 0x30, 2), by_feature)
        self.assertIn(("platform_typed_access:any", "platform_typed_access", 0x30, 2), by_feature)
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
        self.assertIn(("data:copper_list", "data_class", 0x50, 4), by_feature)
        self.assertIn(("copper_register:bplcon0", "copper_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom", "hardware_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom/copper", "hardware_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom/display", "hardware_ref", 0x50, 4), by_feature)
        self.assertIn(("display:bitplanes:7", "display_ref", 0x50, 4), by_feature)
        self.assertIn(("display:color", "display_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom/audio", "hardware_ref", 0x60, 5), by_feature)
        self.assertIn(("hardware_register:aud0+ac_len", "hardware_ref", 0x60, 5), by_feature)
        ids = [xref["id"] for xref in xrefs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([row["row_index"] for row in snippets], [0, 1, 2, 3, 4, 5])
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
        self.assertEqual(report[0]["counts"]["numeric_address_reg_access_without_type"], 1)
        self.assertEqual(report[0]["counts"]["numeric_cause:unknown_pointer_chain"], 1)
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
                "app_slot_load": 1,
                "global_or_base_slot_load": 4,
                "post_call_existing_base": 1,
                "post_call_register_copy": 2,
                "stack_slot_load": 2,
                "unknown_pointer_chain": 2,
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

    def test_type_flow_delta_summarizes_totals_and_target_changes(self) -> None:
        before = [
            {
                "target_id": "a",
                "source_id": "old-a",
                "platform": "amiga-hunk",
                "opportunity_count": 4,
                "resolved_typed_access_count": 1,
                "counts": {"numeric_address_reg_access_without_type": 4, "resolved_typed_access": 1},
                "numeric_cause_counts": {"api_output_nearby": 3, "unknown_pointer_chain": 1},
                "propagation_chain_counts": {"api_output_to_global_or_base_slot_reload": 2},
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
                "counts": {"numeric_address_reg_access_without_type": 2, "resolved_typed_access": 3},
                "numeric_cause_counts": {"api_output_nearby": 1, "unknown_pointer_chain": 1},
                "propagation_chain_counts": {"api_output_to_global_or_base_slot_reload": 1},
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
            delta["propagation_chain_deltas"]["api_output_to_global_or_base_slot_reload"],
            {"before": 2, "after": 1, "delta": -1},
        )
        self.assertEqual(delta["struct_deltas"]["Library"], {"before": 1, "after": 3, "delta": 2})
        self.assertEqual([item["target_id"] for item in delta["target_deltas"]], ["a"])
        self.assertEqual(delta["target_deltas"][0]["origin"], {"display_name": "A"})

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

            with mock.patch.object(usage, "analyze_executable_file", side_effect=RuntimeError("analysis failed")):
                rows = usage.build_usage_manifest(disk_manifest, file_manifest, root=tmpdir)

            ids = [row["id"] for row in rows]
            self.assertEqual(ids, ["platform_disk_manifest:amiga-disk/test", "platform_file_manifest:amiga-hunk/test"])
            file_row = rows[1]
            counts = file_row["feature_counts"]
            self.assertEqual(counts["format:executable"], 1)
            self.assertEqual(counts["relocation:fixup"], 2)
            self.assertEqual(counts["diagnostic:analysis_error"], 1)

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
                    "os_call:any": 1,
                    "platform_field:IO_COMMAND": 1,
                },
                "feature_examples": {
                    "hardware:custom/display": [{"offset": 4}],
                    "display:bitplanes:5": [{"offset": 6}],
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
            {"target_id": "b", "feature": "runtime:copied_code", "row_index": 7, "platform": "amiga-hunk"},
        ]

        query = usage.query_usage_manifest(rows, "", group="hardware")
        display_query = usage.query_usage_manifest(rows, "", group="display")
        typed_query = usage.query_usage_manifest(rows, "", group="platform_types")
        xref_query = usage.query_usage_xrefs(xrefs, group="hardware")
        typed_xref_query = usage.query_usage_xrefs(xrefs, group="platform_types")

        self.assertEqual([item["id"] for item in query], ["a"])
        self.assertEqual(query[0]["count"], 2)
        self.assertEqual(query[0]["examples"], [{"offset": 4}])
        self.assertEqual([item["id"] for item in display_query], ["a"])
        self.assertEqual(display_query[0]["count"], 3)
        self.assertEqual([item["id"] for item in typed_query], ["a"])
        self.assertEqual(typed_query[0]["count"], 1)
        self.assertEqual([item["target_id"] for item in xref_query], ["a"])
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
