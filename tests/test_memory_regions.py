"""Region identity/history and native reference facts; no inferred free storage."""

import json

import pytest

from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    build_flat_m68k_bytes_listing_artifact_profile,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_text
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
    load_manual_projection,
)
from amiga_reversing.disasm.memory_regions import validate_region
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def region(**changes):
    return {
        "region_id": "key_state",
        "name": "key_state",
        "runtime_address": 0x397C,
        "size": 128,
        "alignment": 2,
        "source_domain": "runtime_only",
        "memory_class": "cpu_ram",
        "lifetime": "persistent",
        "dma_access": "none",
    } | changes


@pytest.mark.parametrize(
    "changes",
    [
        {"size": 0},
        {"alignment": 3},
        {"runtime_address": 0x397D},
        {"size": 0x1000000},
        {"runtime_address": True},
        {"source_domain": "mapped_source"},
        {"lifetime": "overlay"},
        {"region_id": "bad\u0000id"},
        {"closed": True},
    ],
)
def test_invalid_or_unproved_contract_refused(changes):
    with pytest.raises(ValueError, match="memory_region"):
        validate_region(region(**changes))


def test_identity_history_projection_and_native_interior_reference(tmp_path):
    code = bytes.fromhex("41f90000397c4a39000039bc43f9000039cc4e75")
    binary = tmp_path / "fixture.bin"
    binary.write_bytes(code)
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
    kind, payload = target_catalog_manual_payload(
        "target.memory_region.add", parameters=region()
    )
    actions = append_manual_actions(
        tmp_path, binary_source=source, actions=[(ManualActionKind(kind), payload)]
    )
    before = (tmp_path / "manual_actions.jsonl").read_bytes()
    projection = load_manual_projection(tmp_path)
    assert projection.memory_regions == (region(),)
    with pytest.raises(ValueError, match="already exists"):
        append_manual_actions(
            tmp_path, binary_source=source, actions=[(ManualActionKind(kind), payload)]
        )
    assert (tmp_path / "manual_actions.jsonl").read_bytes() == before
    path = tmp_path / "effective.json"
    path.write_text(effective_metadata_text(tmp_path, binary_source=source))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        code, display_path=str(binary), metadata_path=path
    )
    try:
        facts = artifact.memory_regions_payload()["items"][0]
        assert facts["source_placement"] is None
        assert [r["region_offset"] for r in facts["references"]] == [0, 64, 80]
        assert [r["obligation"] for r in facts["references"]] == [
            "derived_pointer_accesses",
            "direct_access_bounds",
            "derived_pointer_accesses",
        ]
        assert facts["proof_status"] == "obligations_open"
    finally:
        artifact.close()
    append_manual_actions(
        tmp_path,
        binary_source=source,
        actions=[
            (
                ManualActionKind.UNDO_ACTION,
                {"undoes_action_id": actions[0]["action_id"]},
            )
        ],
    )
    assert load_manual_projection(tmp_path).memory_regions == ()
    assert (tmp_path / "manual_actions.jsonl").read_bytes().startswith(before)


@pytest.mark.parametrize(
    ("code", "changes", "destination", "memory_class", "refusal"),
    [
        ("4a390000397c4e75", {}, 0xC7F000, "slow", None),
        (
            "41f90000397c4e75",
            {},
            0xC7F000,
            "slow",
            "unresolved_reference_or_access_closure",
        ),
        ("4a390000397c4e75", {}, 0xC7F001, "slow", "reservation_alignment"),
        (
            "4a390000397c4e75",
            {"dma_access": "chip"},
            0xC7F000,
            "slow",
            "chip_dma_required",
        ),
        ("4a390000397c4e75", {}, 0x200000, "fast", "outside_supported_a500_memory"),
        ("4a38397c4e75", {}, 0xC7F000, "slow", "absolute_word_encoding_overflow"),
        (
            "4a390000397c4a3900c7f0104e75",
            {},
            0xC7F000,
            "slow",
            "existing_destination_reference",
        ),
    ],
)
def test_native_plan_rejects_open_or_incompatible_moves(
    tmp_path, code, changes, destination, memory_class, refusal
):
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region(**changes)]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        bytes.fromhex(code), display_path="fixture", metadata_path=path
    )
    try:
        plan = artifact.memory_region_plan("key_state", destination, memory_class)
        assert plan["refusal"] == refusal
        assert plan["status"] == ("refused" if refusal else "ready")
        if refusal is None:
            assert plan["rewrite_ledger"] == [
                {
                    "section_index": 0,
                    "source_offset": 0,
                    "operand_index": 0,
                    "region_offset": 0,
                    "before": "4a390000397c",
                    "after": "4a3900c7f000",
                }
            ]
    finally:
        artifact.close()


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("4a28000b41f9000040004e75", None),
        ("4a28008041f9000040004e75", "pointer_access_outside_region"),
        ("7e1f429851cffffc41f9000040004e75", None),
        ("22484e75", "pointer_value_escape_or_comparison"),
        ("2f0841f900004000205f4a28000b41f9000040004e75", None),
        (
            "2f0841f900004000205f4a28008041f9000040004e75",
            "pointer_access_outside_region",
        ),
        ("48e7008041f9000040004cdf01004a28000b41f9000040004e75", None),
        ("48e7008041f9000040004cdf01004e75", "unresolved_pointer_return_context"),
    ],
)
def test_native_derived_access_proof_checks_bounds_and_escapes(
    tmp_path, body, expected
):
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        bytes.fromhex("41f90000397c" + body), display_path="fixture", metadata_path=path
    )
    try:
        proof = artifact.memory_regions_payload()["items"][0]["references"][0][
            "root_access_proof"
        ]
        assert proof["reason"] == expected
        if expected is None:
            assert proof["access_count"] > 0
            assert proof["maximum_end"] == (128 if body.startswith("7e1f") else 12)
            assert (
                artifact.memory_region_plan("key_state", 0xC7F000, "slow")["status"]
                == "ready"
            )
    finally:
        artifact.close()


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ("d1fc000000804a1041f9000040004e75", "unsupported_pointer_arithmetic"),
        ("50884a1041f9000040004e75", "unsupported_pointer_arithmetic"),
        ("41e800804a1041f9000040004e75", "pointer_access_outside_region"),
        ("48d000ff41f9000040004e75", None),
        ("41e8007c48d000ff41f9000040004e75", "pointer_access_outside_region"),
        ("2f08224f41f9000040004e75", "saved_pointer_frame_address_escape"),
        ("2f084e56000041f9000040004e75", "saved_pointer_frame_address_escape"),
        ("4e4041f9000040004e75", "unmodeled_pointer_exception"),
        ("4e73", "unmodeled_pointer_return"),
        ("4e77", "unmodeled_pointer_return"),
        # A callee changes the actual return slot; remembered CFG return is invalid.
        ("6100000a41f9000040004e75588f4e75", "unsupported_pointer_stack_replacement"),
        ("6100000a41f9000040004e752e804e75", "pointer_return_slot_access"),
    ],
)
def test_native_proof_refuses_implicit_and_stack_escapes(tmp_path, body, reason):
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        bytes.fromhex("41f90000397c" + body), display_path="fixture", metadata_path=path
    )
    try:
        proof = artifact.memory_regions_payload()["items"][0]["references"][0][
            "root_access_proof"
        ]
        assert proof["reason"] == reason
        assert artifact.memory_region_plan("key_state", 0xC7F000, "slow")["status"] == (
            "ready" if reason is None else "refused"
        )
    finally:
        artifact.close()


@pytest.mark.parametrize("prefix", ["588f", "2280"])
def test_root_prefix_cannot_hide_return_frame_mutation(tmp_path, prefix):
    # JSR enters F; F mutates SP or writes through an unknown base before
    # producing a region pointer. Its apparent RTS cannot borrow the caller.
    body = bytes.fromhex("6100000a41f9000040004e75" + prefix + "41f90000397c4e75")
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        body, display_path="fixture", metadata_path=path
    )
    try:
        assert (
            artifact.memory_region_plan("key_state", 0xC7F000, "slow")["status"]
            == "refused"
        )
        proof = artifact.memory_regions_payload()["items"][0]["references"][0][
            "root_access_proof"
        ]
        assert proof["reason"] == "unmodeled_pointer_prefix_frame"
    finally:
        artifact.close()


def test_mutable_pc_relative_value_cannot_supply_index_bound(tmp_path):
    # Original byte zero is mutable memory, not a proved constant index.
    # MOVEQ clears high bits, MOVE.B loads a byte, then TST uses the long index.
    code = bytes.fromhex("41f90000397c7000103a000e4a30080041f9000040004e750000")
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        code, display_path="fixture", metadata_path=path
    )
    try:
        proof = artifact.memory_regions_payload()["items"][0]["references"][0][
            "root_access_proof"
        ]
        assert proof["reason"] == "pointer_access_outside_region"
        assert (
            artifact.memory_region_plan("key_state", 0xC7F000, "slow")["status"]
            == "refused"
        )
    finally:
        artifact.close()


def test_explicit_key_bit_clear_restores_byte_index_bound(tmp_path):
    code = bytes.fromhex("41f90000397c7000103a0012088000074a30080041f9000040004e750000")
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        code, display_path="fixture", metadata_path=path
    )
    try:
        proof = artifact.memory_regions_payload()["items"][0]["references"][0][
            "root_access_proof"
        ]
        assert proof["reason"] is None
        assert proof["maximum_end"] == 128
        assert (
            artifact.memory_region_plan("key_state", 0xC7F000, "slow")["status"]
            == "ready"
        )
    finally:
        artifact.close()


def test_synthetic_stack_address_cannot_replace_real_stack(tmp_path):
    code = bytes.fromhex("41f90000397c2e7c009000004e75")
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        code, display_path="fixture", metadata_path=path
    )
    try:
        proof = artifact.memory_regions_payload()["items"][0]["references"][0][
            "root_access_proof"
        ]
        assert proof["reason"] == "unsupported_pointer_stack_replacement"
    finally:
        artifact.close()


@pytest.mark.parametrize(
    ("prefix", "reason", "delta", "minimum"),
    [
        ("2f072e1f", None, 0, -4),
        ("48e703004cdf00c0", None, 0, -8),
        ("2e80", "frame_prefix_return_slot_write", 0, 0),
        ("2280", "unresolved_frame_prefix_memory_alias", 0, 0),
        ("2e7c00900000", "frame_prefix_stack_replacement", 0, 0),
        ("66022f07", "ambiguous_frame_prefix_delta", None, -4),
        ("2f1f", "unsupported_frame_prefix_multiple_stack_operands", 0, 0),
    ],
)
def test_native_frame_prefix_models_effects_without_absolute_sp(
    tmp_path, prefix, reason, delta, minimum
):
    # F is reached by a canonical direct call; fixture root has a real owner.
    root = "41f90000397c4a28000b41f9000040004e75"
    code = bytes.fromhex("6100000a41f9000040004e75" + prefix + root)
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        code, display_path="fixture", metadata_path=path
    )
    try:
        context = artifact.memory_regions_payload()["items"][0]["references"][0][
            "frame_prefix"
        ]
        assert context["entry_offset"] == 12
        assert context["reason"] == reason
        assert context["absolute_sp"] is None
        if delta is not None:
            assert context["stack_delta"] == delta
        assert context["minimum_delta"] == minimum
        assert context["status"] == ("refused" if reason else "modeled_relative_only")
    finally:
        artifact.close()


def test_balanced_native_prefix_can_borrow_a_return_context(tmp_path):
    # Entry -> F; F saves/restores D7 before producing the region pointer;
    # caller independently overwrites A0 after F's normal return.
    code = bytes.fromhex("6100000a41f9000040004e752f072e1f41f90000397c4a28000b4e75")
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        code, display_path="fixture", metadata_path=path
    )
    try:
        reference = artifact.memory_regions_payload()["items"][0]["references"][0]
        assert reference["frame_prefix"]["stack_delta"] == 0
        assert reference["frame_prefix"]["minimum_delta"] == -4
        assert reference["root_access_proof"]["reason"] is None
        assert (
            artifact.memory_region_plan("key_state", 0xC7F000, "slow")["status"]
            == "ready"
        )
    finally:
        artifact.close()


@pytest.mark.parametrize(
    ("prefix", "suffix", "reason"),
    [
        ("bne.b root\naddq.l #4,a7\nrts", "", "frame_prefix_entry_stack_imbalance"),
        (
            "bsr.w g",
            "g:\naddq.l #4,a7\nbsr.w h\nsubq.l #4,a7\nrts\nh:\nrts",
            "frame_prefix_call_slot_overlap",
        ),
        ("adda.w #-4,a7", "", None),
        (
            "adda.w #-4,a7\nsuba.l #65532,a7",
            "",
            None,
        ),
        ("pea.l $4000.l", "", "unmodeled_frame_prefix_exception_or_link"),
        ("move #$2000,sr", "", "unmodeled_frame_prefix_exception_or_link"),
        ("move.l usp,a0", "", "frame_prefix_address_escape"),
        ("lea.l $0(a1,a7.l),a2", "", "frame_prefix_address_escape"),
    ],
)
def test_native_prefix_rejects_control_frame_corruption_with_oracle(
    tmp_path, prefix, suffix, reason
):
    import subprocess

    from amiga_reversing.tools.direct_payload_adapter import VASM

    if not VASM.exists():
        pytest.skip("Installed vasm required for independent fixture encoding")
    source = tmp_path / "fixture.s"
    binary = tmp_path / "fixture.bin"
    source.write_text(
        "    org 0\n    bsr.w f\n    lea.l $4000.l,a0\n    rts\nf:\n"
        + prefix
        + "\nroot:\n    lea.l $397c.l,a0\n    tst.b $b(a0)\n    lea.l $4000.l,a0\n    rts\n"
        + suffix
        + "\n"
    )
    source.write_text(
        "\n".join(
            line if line.endswith(":") else "    " + line
            for line in source.read_text().splitlines()
        )
        + "\n"
    )
    result = subprocess.run(
        [str(VASM), "-Fbin", "-m68000", "-no-opt", "-o", str(binary), str(source)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    path = tmp_path / "meta.json"
    path.write_text(json.dumps({"memory_regions": [region()]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(
        binary.read_bytes(), display_path="fixture", metadata_path=path
    )
    try:
        context = artifact.memory_regions_payload()["items"][0]["references"][0][
            "frame_prefix"
        ]
        assert context["reason"] == reason
        if prefix.startswith("adda.w"):
            assert context["stack_delta"] == (-65536 if "65532" in prefix else -4)
    finally:
        artifact.close()
