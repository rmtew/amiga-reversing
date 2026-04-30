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
                                    "base_name": "DOSBase",
                                    "semantic_kind": "library_base",
                                    "value_domain_name": "dos.mode",
                                    "type_name": "struct FileHandle *",
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
                            "kind": "data",
                            "text": "\tdc.w bplpt+$02,$0000\n",
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
                        },
                        {
                            "kind": "directive",
                            "text": "\tFPU     3\n",
                            "section_index": 0,
                            "start_offset": 0x80,
                            "opcode_or_directive": "FPU",
                        },
                    ]
                },
            },
            bag,
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
        self.assertEqual(counts["value_domain:dos.mode"], 1)
        self.assertEqual(counts["struct:MemHeader"], 1)
        self.assertEqual(counts["platform_base:DOSBase"], 1)
        self.assertEqual(counts["semantic:library_base"], 1)
        self.assertEqual(counts["type:struct_FileHandle_*"], 1)
        self.assertEqual(counts["app_slot:any"], 2)
        self.assertEqual(counts["app_slot:read-write"], 1)
        self.assertEqual(counts["app_slot:write"], 1)
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
        self.assertEqual(counts["hardware_register:bplpt"], 1)
        self.assertEqual(counts["hardware_register:aud0"], 1)
        self.assertEqual(counts["hardware_register:aud0+ac_len"], 1)
        self.assertNotIn("coprocessor:fpu", counts)
        self.assertNotIn("coprocessor:fpu_id:3", counts)
        self.assertIn("os:exec.library/AllocMem", tags)
        self.assertEqual(examples["os:exec.library/AllocMem"][0]["offset"], 0x20)

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
                        "text": "\tdc.w bplpt,$0007\n",
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
        self.assertIn(("os:exec.library/AllocMem", "os_call", 1, "local_wrapper"), by_feature_resolution)
        self.assertIn(("os_library:exec.library", "os_library", None, None), by_feature_resolution)
        self.assertIn(("app_slot:write", "app_slot_ref", 0x30, 2), by_feature)
        self.assertIn(("runtime:copied_code", "runtime_view", 0x40, 3), by_feature)
        self.assertIn(("data:copper_list", "data_class", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom", "hardware_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom/copper", "hardware_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom/display", "hardware_ref", 0x50, 4), by_feature)
        self.assertIn(("hardware:custom/audio", "hardware_ref", 0x60, 5), by_feature)
        self.assertIn(("hardware_register:aud0+ac_len", "hardware_ref", 0x60, 5), by_feature)
        ids = [xref["id"] for xref in xrefs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([row["row_index"] for row in snippets], [0, 1, 2, 3, 4, 5])
        self.assertEqual(snippets[1]["row"]["stable_key"], "row-os")
        self.assertEqual(snippets[5]["row"]["stable_key"], "row-hw")

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
                "feature_counts": {"hardware:custom/display": 2, "os_call:any": 1},
                "feature_examples": {"hardware:custom/display": [{"offset": 4}]},
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
            {"target_id": "b", "feature": "runtime:copied_code", "row_index": 7, "platform": "amiga-hunk"},
        ]

        query = usage.query_usage_manifest(rows, "", group="hardware")
        xref_query = usage.query_usage_xrefs(xrefs, group="hardware")

        self.assertEqual([item["id"] for item in query], ["a"])
        self.assertEqual(query[0]["count"], 2)
        self.assertEqual(query[0]["examples"], [{"offset": 4}])
        self.assertEqual([item["target_id"] for item in xref_query], ["a"])

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
