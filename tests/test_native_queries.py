"""Compact native projections share typed facts, never navigation JSON."""

from __future__ import annotations

import json
import tempfile
from contextlib import closing, contextmanager
from ctypes import byref, c_void_p
from pathlib import Path

import pytest

from amiga_reversing.disasm.c_backend import CListingArtifact, _CBackendSourceFile

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def artifact(code: str, metadata_path: str = ""):
    if not (ROOT / "src/build/platform_file_lib.dll").exists():
        pytest.skip("native backend must be built")
    with tempfile.TemporaryDirectory() as directory:
        binary = Path(directory) / "query.bin"
        binary.write_bytes(bytes.fromhex(code))
        with closing(
            CListingArtifact.create(
                _CBackendSourceFile(binary, "amiga-raw", entry_offset=0),
                metadata_text=metadata_path,
                include_dir=str(ROOT / "ext/amiga_includes/ndk_2.0/include"),
                project_root=ROOT,
            )
        ) as instance:
            yield instance


def test_native_queries_pagination_references_and_encoding():
    with artifact("61024e754e75") as a:
        # Prevent accidentally implementing this as navigation/analysis trimming.
        a.navigation_payload = lambda: pytest.fail("navigation queried")
        a.analysis_payload = lambda: pytest.fail("whole analysis queried")
        first = a.query_payload("instructions", limit=1)
        second = a.query_payload("instructions", offset=1, limit=1)
        assert first["total"] == second["total"] == 3
        assert first["has_more"] is True
        assert first["items"][0]["bytes"] == "6102"
        assert second["items"][0]["source_offset"] == 2
        assert a.query_payload("instructions", offset=3)["items"] == []
        assert a.query_payload("instructions", section_index=99)["total"] == 0
        assert (
            a.query_payload("instructions", source_offset=2, end_offset=6)["total"] == 2
        )
        refs = a.query_payload(
            "references", section_index=0, source_offset=4, direction="incoming"
        )
        assert [(x["source_offset"], x["target_offset"]) for x in refs["items"]] == [
            (0, 4)
        ]
        name = refs["items"][0]["symbol"]
        assert a.query_payload("references", symbol=name)["items"] == refs["items"]
        assert a.query_payload("symbols", query=name)["items"][0]["source_offset"] == 4
        edges = a.query_payload("edges", source_offset=0, direction="outgoing")["items"]
        assert {x["kind"] for x in edges} == {"call", "fallthrough"}
        assert len(json.dumps(first)) < 1500
        assert first["unknowns"]


@pytest.mark.parametrize(("code", "kind"), [("4e904e75", "call"), ("4ed0", "jump")])
def test_native_query_unresolved_indirect_transfer(code, kind):
    with artifact(code) as a:
        calls = [x for x in a.query_payload("edges")["items"] if x["kind"] == kind]
        assert len(calls) == 1
        assert calls[0]["status"] == "unresolved"
        assert calls[0]["target_offset"] is None
        assert calls[0]["target_section_index"] is None


def test_native_query_typed_comment_only_field(tmp_path):
    metadata = tmp_path / "metadata.json"
    metadata.write_text(
        json.dumps(
            {
                "target_type": "raw_binary",
                "entry_register_seeds": [
                    {
                        "entry_offset": None,
                        "hunk": 0,
                        "register": "A0",
                        "kind": "struct_ptr",
                        "note": "Record",
                        "struct_name": "Record",
                        "context_name": None,
                    }
                ],
                "custom_structs": [
                    {
                        "name": "Record",
                        "size": 8,
                        "fields": [
                            {
                                "name": "first",
                                "type": "long",
                                "offset": 0,
                                "size": 4,
                                "struct": None,
                                "pointer_struct": None,
                                "named_base": None,
                            },
                        ],
                    }
                ],
            }
        )
    )
    with artifact("4a904e75", str(metadata)) as a:
        uses = a.query_payload("fields", struct_name="Record", field_offset=0)
        assert uses["total"] == 1
        assert uses["items"][0]["field_name"] == "first"
        assert uses["items"][0]["provenance"]["kind"] != 0
        refs = a.query_payload("references", symbol="Record_first")["items"]
        assert refs[0]["comment_only"] is True
        instruction = a.query_payload("instructions", source_offset=0)["items"][0]
        assert instruction["text"] == "tst.l (a0)"
        assert "Record_first" in instruction["annotation"]
        assert instruction["bytes"] == "4a90"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"source_offset": 2**32},
        {"end_offset": 4},
        {"source_offset": 4, "end_offset": 4},
        {"direction": "invalid"},
        {"symbol": "bad\0name"},
    ],
)
def test_native_query_validation(kwargs):
    with artifact("4e75") as a, pytest.raises(ValueError, match="must|requires"):
        a.query_payload("instructions", **kwargs)


def test_native_limit_enforced_below_python():
    with artifact("4e75") as a:
        out = c_void_p()
        result = a._dll.platform_file_facts_v2_listing_artifact_query_json_alloc(
            a._handle,
            b"instructions",
            b"",
            0,
            0,
            0,
            0,
            0,
            0,
            b"",
            b"",
            0,
            0,
            b"both",
            0,
            101,
            byref(out),
        )
        assert result != 0
        assert out.value is None


def test_navigation_keeps_summaries_without_competing_reference_arrays():
    with artifact("61024e754e75") as a:
        navigation, _ = a.navigation_payload()
        labels = navigation["groups"]["labels"]
        target = next(label for label in labels if label["addr"] == 4)
        assert "refs" not in target
        assert target["ref_count"] == 2
        assert target["access_counts"] == {"definition": 1, "reference": 1}
        assert a.query_payload("references", symbol=target["symbol"])["total"] == 1
