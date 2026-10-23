"""Hardware readability is distinct from fixed base-address proof."""

import json
from collections import Counter
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_target_metadata,
)
from amiga_reversing.disasm.listing_context import listing_element_contexts
from amiga_reversing.disasm.manual_action_catalog import listing_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
    manual_action_log_path,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def test_pandora_retains_reviewed_hardware_rendering():
    baseline = json.loads(
        (Path(__file__).parent / "fixtures/pandora-render-quality-baseline.json").read_text()
    )
    source = (
        PROJECT_ROOT
        / "targets/amiga_disk_pandora-1988-firebird/targets"
        / "amiga_raw_pandora_3e1ee0f1_bk_00_000000e8"
        / "pandora_3e1ee0f1_bk_00_000000e8.s"
    )
    if not source.exists():
        pytest.skip("Pandora generated source is not installed")
    actual = Counter(source.read_text().splitlines())
    expected = Counter(baseline["lines"])
    metadata = effective_target_metadata(source.parent)
    equates = {e.name: e.value for e in metadata.target_equates}
    for name, value in baseline.get("equate_values", {}).items():
        assert equates[name] == value
    assert not (expected - actual), expected - actual


def fixture(tmp_path, text):
    binary = tmp_path / "input.bin"
    original, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw", " SECTION code,code\n ORG 0\n" + text, output_path=binary
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
    return source, original


def exact(source, rendered, original):
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        rendered,
        include_dir=PROJECT_ROOT / "ext/amiga_includes/ndk_2.0/include",
    )
    assert rebuilt == original


@pytest.mark.parametrize(
    ("body", "known"),
    [
        ("rts", True),
        ("lea.l $DFF000.l,a5\n rts", True),
        ("suba.l a5,a5\n rts", False),
        ("jsr (a0)\n rts", False),
    ],
)
def test_call_proofs_retain_display_explanations(tmp_path, body, known):
    source, original = fixture(
        tmp_path,
        f""" lea.l $DFF000.l,a5
 bsr helper
 move.w #$4200,$100(a5)
 move.w #$2C81,$8E(a5)
 move.w #$F4C1,$90(a5)
 move.w #$38,$92(a5)
 move.w #$D0,$94(a5)
 move.l a0,$80(a5)
 rts
helper:
 {body}
""",
    )
    rendered = c_backend.render_project_source_with_c_backend(source)
    caller = rendered.split("\trts", 1)[0]
    for note in (
        "display 4 bitplanes lores color",
        "display window start v=$2C h=$81",
        "display window stop v=$F4 h=$C1",
        "display fetch start $38",
        "display fetch stop $D0",
        "copper_list pointer",
    ):
        assert (note in caller) == known, rendered
        assert caller.count(note) <= 1, rendered
    exact(source, rendered, original)


@pytest.mark.parametrize(
    ("offset", "symbol", "note"),
    [
        (0xA0, "aud0+ac_ptr", "sound_sample pointer"),
        (0xA4, "aud0+ac_len", "sound sample length 64 bytes"),
        (0xA6, "aud0+ac_per", "audio period"),
        (0xA8, "aud0+ac_vol", "audio volume"),
        (0x80, "cop1lc", "copper_list pointer"),
        (0x96, "dmacon", None),
        (0x9C, "intreq", None),
    ],
)
def test_offset_domain_retains_names_without_claiming_a_constant_base(
    tmp_path, offset, symbol, note
):
    opcode = "move.l a0" if offset in (0xA0, 0x80) else "move.w #$20"
    source, original = fixture(
        tmp_path, f" jsr (a0)\n {opcode},${offset:X}(a6)\n rts\n"
    )
    before = c_backend.render_project_source_with_c_backend(source)
    assert symbol + "(a6)" not in before
    artifact = c_backend.build_listing_artifact_profile_from_binary_source(source)[2]
    try:
        row = next(
            r
            for r in artifact.addr_window_payload(addr=2, before=0, after=2)[0]["rows"]
            if r["kind"] == "instruction" and r["start_offset"] == 2
        )
        element = next(
            e
            for e in listing_element_contexts(row)
            if e["element_kind"] == "displacement"
        )
        kind, payload = listing_catalog_manual_payload(
            row,
            "representation.hardware_offset",
            element_context=element,
            parameters={"base_symbol": "_custom"},
        )
    finally:
        artifact.close()
    append_manual_actions(
        tmp_path, binary_source=source, actions=[(ManualActionKind(kind), payload)]
    )
    with effective_metadata_file(tmp_path) as metadata:
        rendered = c_backend.render_project_source_with_c_backend(
            source, metadata_path=metadata
        )
        analysis = c_backend.analyze_project_source_with_c_backend(
            source, metadata_path=metadata
        )
    assert symbol + "(a6)" in rendered, rendered
    if note:
        assert note in rendered, rendered
    # The accepted literal domain supplies neither a runtime address nor an
    # inferred identity for A6 after the opaque call.
    assert not [
        u
        for s in analysis["sections"]
        for u in s["platform_address_uses"]
        if u["offset"] == 2
    ]
    exact(source, rendered, original)


def test_unknown_hardware_profile_refuses_without_history_append(tmp_path):
    source, _ = fixture(tmp_path, " move.w #$20,$A4(a6)\n rts\n")
    artifact = c_backend.build_listing_artifact_profile_from_binary_source(source)[2]
    try:
        row = next(
            r
            for r in artifact.addr_window_payload(addr=0, before=0, after=2)[0]["rows"]
            if r["kind"] == "instruction"
        )
        element = next(
            e
            for e in listing_element_contexts(row)
            if e["element_kind"] == "displacement"
        )
        kind, payload = listing_catalog_manual_payload(
            row,
            "representation.hardware_offset",
            element_context=element,
            parameters={"base_symbol": "not_a_hardware_base"},
        )
    finally:
        artifact.close()
    path = manual_action_log_path(tmp_path)
    before = path.read_bytes() if path.exists() else None
    with pytest.raises((ValueError, RuntimeError)):
        append_manual_actions(
            tmp_path, binary_source=source, actions=[(ManualActionKind(kind), payload)]
        )
    assert (path.read_bytes() if path.exists() else None) == before


def test_offset_domain_native_replay_deduplicates_and_rejects_conflicts(tmp_path):
    source, _ = fixture(tmp_path, " move.w #$20,$A4(a6)\n rts\n")
    metadata = tmp_path / "offset-policy.json"
    entry = {
        "hunk": 0, "addr": 0, "end": 6, "operand_index": 1,
        "style": "hardware_offset", "element_kind": "displacement",
        "hardware_offset": {"base_symbol": "_custom", "offset": 0xA4},
    }
    metadata.write_text(json.dumps({"manual_representations": [entry, entry]}))
    policy = c_backend.effective_policy_project_source_with_c_backend(
        source, metadata_path=metadata
    )["analysis_policy"]
    assert policy["manual_representation_count"] == 1
    assert policy["manual_representations"][0]["hardware_offset"] == entry["hardware_offset"]
    conflict = {**entry, "hardware_offset": {"base_symbol": "_custom", "offset": 0xA6}}
    metadata.write_text(json.dumps({"manual_representations": [entry, conflict]}))
    with pytest.raises(RuntimeError, match="manual representation"):
        c_backend.effective_policy_project_source_with_c_backend(
            source, metadata_path=metadata
        )
    metadata.write_text(json.dumps({"manual_representations": [conflict]}))
    with pytest.raises(RuntimeError):
        c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)


@pytest.mark.parametrize(('offset', 'symbol'), [(0x96, 'dmacon'), (0x108, 'bpl1mod')])
def test_legacy_sdk_presentation_is_not_treated_as_a_canonical_equate(tmp_path, offset, symbol):
    source, original = fixture(tmp_path, f' lea.l $DFF000.l,a5\n move.w d0,${offset:X}(a5)\n rts\n')
    # Historical accepted hardware-domain facts project to this SDK-symbol
    # presentation, without a target_equate_index. Keep that path distinct.
    metadata = tmp_path / 'legacy.json'
    metadata.write_text(json.dumps({'manual_representations': [{
        'hunk': 0, 'addr': 6, 'end': 10, 'style': 'symbol',
        'element_kind': 'a5_hardware_ref', 'operand_index': 1, 'symbol': symbol}]}))
    rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
    assert f'move.w d0,{symbol}(a5)' in rendered
    exact(source, rendered, original)
