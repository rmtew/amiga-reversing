"""Bounded native callee proofs distinguish returned constants from preservation."""

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import (
    target_catalog_manual_payload,
)
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


@pytest.mark.parametrize(
    ("body", "known"),
    [
        ("lea.l $DFF000.l,a5", True),
        ("move.l #$DFF000,d4\n exg d4,a5", True),
        ("lea.l $DFF000.l,a5\n move.w #0,d4", True),
        ("lea.l $DFF000.l,a5\n addq.l #2,a5", False),
        ("lea.l $DFF000.l,a5\n movea.l (a0),a5", False),
        ("lea.l $DFF000.l,a5\n jsr (a0)", False),
        (
            "tst.l d0\n beq.b other\n lea.l $DFF000.l,a5\n rts\nother:\n lea.l $DFF000.l,a5",
            True,
        ),
        (
            "tst.l d0\n beq.b other\n lea.l $DFF000.l,a5\n rts\nother:\n suba.l a5,a5",
            False,
        ),
        ("move.l a5,-(a7)\n lea.l $DFF000.l,a5\n movea.l (a7)+,a5", False),
        ("bsr.b nested\n rts\nnested:\n lea.l $DFF000.l,a5", True),
    ],
)
@pytest.mark.parametrize("manual", [False, True])
def test_only_a_constant_on_every_normal_return_establishes_hardware(
    tmp_path, body, known, manual
):
    binary = tmp_path / "input.bin"
    original, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        f" SECTION code,code\n ORG 0\n suba.l a5,a5\n bsr helper\n move.w #$40,$9C(a5)\n rts\nhelper:\n {body}\n rts\n",
        output_path=binary,
    )
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY,
        path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0,
        entrypoint=0,
        code_start_offset=0,
        display_path=str(binary),
        analysis_cache_path=tmp_path / "analysis",
    )
    write_target_metadata(
        tmp_path, TargetMetadata(target_type="program", entry_register_seeds=())
    )
    analysis = c_backend.analyze_project_source_with_c_backend(source)
    results = [
        r
        for section in analysis["sections"]
        for summary in section["function_summaries"]
        for r in summary["results"]
        if r.get("kind") == "hardware_base"
    ]
    if known:
        assert any(r["location"].get("register") == "A5" for r in results), results
    if manual:
        equate = target_catalog_manual_payload(
            "target.equate.add",
            {"name": "MY_BLIT_REQUEST", "value": 64, "group": "test"},
        )
        # Replay an already accepted literal binding from before a new native
        # proof symbolized this operand. It must retain priority afterwards.
        binding = (
            "create_manual_representation",
            {
                "representation": {
                    "representation_id": "historical-blit-binding",
                    "hunk": 0,
                    "addr": 6,
                    "end": 12,
                    "operand_index": 0,
                    "element_kind": "immediate",
                    "element_id": "s0:00000006:instruction:immediate:0:64",
                    "stable_key": "s0:00000006:instruction",
                    "style": "symbol",
                    "symbol": "MY_BLIT_REQUEST",
                    "value": 64,
                    "signed_value": 64,
                }
            },
        )
        append_manual_actions(
            tmp_path,
            binary_source=source,
            actions=[
                (ManualActionKind(kind), payload) for kind, payload in (equate, binding)
            ],
        )
    with effective_metadata_file(tmp_path) as metadata:
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata
        )
    caller = rendered.split("bsr.w", 1)[-1].split("rts", 1)[0]
    assert ("intreq(a5)" in caller) == known, rendered
    assert ("INTF_BLIT" in caller) == (known and not manual), rendered
    assert ("#MY_BLIT_REQUEST" in caller) == manual, rendered
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        rendered,
        include_dir=PROJECT_ROOT / "ext/amiga_includes/ndk_2.0/include",
    )
    assert rebuilt == original
