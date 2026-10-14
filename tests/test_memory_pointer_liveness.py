"""Future-use evidence must never silently discharge relocation obligations."""

import json
import subprocess

import pytest
from test_memory_regions import region

from amiga_reversing.disasm.c_backend import (
    build_flat_m68k_bytes_listing_artifact_profile,
)
from amiga_reversing.tools.direct_payload_adapter import VASM


def build_fixture(tmp_path, code):
    if not VASM.exists():
        pytest.skip("Installed vasm required for independent fixture encoding")
    source = tmp_path / "fixture.s"
    binary = tmp_path / "fixture.bin"
    source.write_text(
        "\n".join(
            line if line.endswith(":") else "    " + line
            for line in ("org 0\n" + code).splitlines()
        )
        + "\n"
    )
    result = subprocess.run(
        [str(VASM), "-Fbin", "-m68000", "-no-opt", "-o", str(binary), str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    metadata = tmp_path / "meta.json"
    metadata.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        binary.read_bytes(), display_path="fixture", metadata_path=metadata
    )
    return artifact


@pytest.mark.parametrize(
    ("body", "events"),
    [
        ("lea.l $4000.l,a0\nmove.l a0,$5000.l\nrts", {"independent_overwrite"}),
        ("tst.b (a0)\nrts", {"later_pointer_memory_access"}),
        (
            "move.l a0,a1\nlea.l $4000.l,a0\ntst.b (a1)\nrts",
            {"later_pointer_memory_access"},
        ),
        (
            "move.l a0,d0\nlea.l $4000.l,a0\ntst.b $0(a1,d0.l)\nrts",
            {"later_pointer_memory_access"},
        ),
        (
            "lea.l $4(a0),a1\nlea.l $4000.l,a0\ntst.b (a1)\nrts",
            {"later_pointer_memory_access"},
        ),
        ("move.l a0,$5000.l\nrts", {"pointer_value_escape"}),
        ("move.l a0,-(sp)\nrts", {"pointer_value_escape"}),
        ("movem.l a0-a1,-(sp)\nrts", {"saved_or_restored_pointer_observer"}),
        (
            "move #$2700,sr\nlea.l $4000.l,a0\nrts",
            {"exception_or_implicit_frame_observer"},
        ),
        ("trap #0\nlea.l $4000.l,a0\nrts", {"exception_or_implicit_frame_observer"}),
        ("chk.w #2,d0\nlea.l $4000.l,a0\nrts", {"exception_or_implicit_frame_observer"}),
        (
            "move.l a0,d0\nlea.l $4000.l,a0\nmove.w #0,d0\nrts",
            {"partial_alias_overwrite"},
        ),
        ("move.l a0,a7\nrts", {"pointer_stack_escape"}),
        (
            "bne.b use\nlea.l $4000.l,a0\nrts\nuse:\ntst.b (a0)\nrts",
            {"independent_overwrite", "later_pointer_memory_access"},
        ),
        (
            "bsr.w helper\nmove.l a0,$5000.l\nrts\nhelper:\nlea.l $4000.l,a0\nrts",
            {"independent_overwrite"},
        ),
        (
            "bsr.w helper\ntst.b (a0)\nrts\nhelper:\nmoveq #1,d0\nrts",
            {"later_pointer_memory_access"},
        ),
        ("jmp (a0)", {"pointer_control_escape"}),
    ],
)
def test_native_after_leaf_use_audit_is_bounded_and_not_closure(tmp_path, body, events):
    artifact = build_fixture(tmp_path, "lea.l $397c.l,a0\ntst.b $56(a0)\n" + body)
    try:
        reference = artifact.memory_regions_payload()["items"][0]["references"][0]
        audit = reference["after_leaf_liveness"]
        assert audit["leaf_offset"] == 6
        assert audit["start_offset"] == 10
        assert audit["relocation_closure"] is False
        assert audit["interrupt_observers"] == "unmodeled"
        assert audit["frame_integrity"] == "unproved"
        assert not audit["truncated"]
        assert {event["kind"] for event in audit["events"]} == events
        assert 0 < audit["states"] < 100
        if "exception_or_implicit_frame_observer" in events:
            assert reference["root_access_proof"]["status"] == "refused"
            assert (
                artifact.memory_region_plan("key_state", 0xC7F000, "slow")["status"]
                == "refused"
            )
    finally:
        artifact.close()


def test_native_liveness_does_not_omit_tail_entry_context(tmp_path):
    artifact = build_fixture(
        tmp_path,
        "bsr.w f\nlea.l $4000.l,a0\nbsr.w g\nlea.l $4000.l,a0\nrts\n"
        "g:\nbra.w f\nf:\nlea.l $397c.l,a0\ntst.b $56(a0)\nrts",
    )
    try:
        reference = artifact.memory_regions_payload()["items"][0]["references"][0]
        audit = reference["after_leaf_liveness"]
        assert {event["kind"] for event in audit["events"]} == {
            "unmodeled_tail_return_context",
            "independent_overwrite",
        }
        assert audit["relocation_closure"] is False
        assert reference["root_access_proof"]["status"] == "refused"
    finally:
        artifact.close()


@pytest.mark.parametrize("leaf", ["movem.l (a0),a0", "chk.w (a0),d0"])
def test_leaf_overwrite_or_exception_is_not_a_preserved_pointer(tmp_path, leaf):
    artifact = build_fixture(
        tmp_path,
        f"lea.l $397c.l,a0\n{leaf}\ntst.b (a0)\nlea.l $4000.l,a0\nrts",
    )
    try:
        reference = artifact.memory_regions_payload()["items"][0]["references"][0]
        assert "after_leaf_liveness" not in reference
    finally:
        artifact.close()
