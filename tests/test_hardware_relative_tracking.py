"""Closed hardware families retain SDK meaning without a fixed-address claim."""

import json
from collections import Counter
from pathlib import Path

import pytest
from test_hardware_render_quality import exact, fixture

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_actions,
    manual_action_log_path,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT


def test_pandora_audio_group_preserves_corrected_source_quality():
    baseline = json.loads((Path(__file__).parent / "fixtures/pandora-audio-hardware-quality.json").read_text())
    source = (PROJECT_ROOT / "targets/amiga_disk_pandora-1988-firebird/targets"
              / "amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/pandora_3e1ee0f1_bk_00_000000e8.s")
    if not source.exists():
        pytest.skip("Pandora generated source is not installed")
    expected = Counter(site["expected_line"] for site in baseline["sites"])
    actual = Counter(source.read_text().splitlines())
    assert not (expected - actual)
    assert actual["    ; INPUT contract: A6=_custom+16*D7.w; D7.w in {0,1,2,3}"] == 11


def analyze(source):
    return [u for s in c_backend.analyze_project_source_with_c_backend(source)["sections"]
            for u in s["platform_address_uses"] if u["use_shape_name"] == "hardware_register_family"]


@pytest.mark.parametrize("last_channel", [0, 1, 2, 3])
@pytest.mark.parametrize("scaling", ["lsl.w #4,d0", "mulu.w #16,d0"])
def test_dbf_channel_family_is_closed_and_renders_without_manual_bindings(tmp_path, last_channel, scaling):
    source, original = fixture(tmp_path, f""" moveq #{last_channel},d7
loop:
 lea.l $DFF000.l,a6
 move.w d7,d0
 {scaling}
 adda.w d0,a6
 move.l a2,$A0(a6)
 move.w #$20,$A4(a6)
 move.w d1,$A6(a6)
 move.w d2,$A8(a6)
 dbf d7,loop
 rts
""")
    uses = analyze(source)
    assert len(uses) == 4, uses
    for use in uses:
        assert use["relative_base_offsets"] == list(range(0, 16 * (last_channel + 1), 16))
        assert use["address"] is None and use["effective_address"] is None
        assert use["requires_indexed_input_contract"] is False
    rendered = c_backend.render_project_source_with_c_backend(source)
    for symbol in ("aud0+ac_ptr", "aud0+ac_len", "aud0+ac_per", "aud0+ac_vol"):
        assert symbol + "(a6)" in rendered, rendered
    for note in ("sound_sample pointer", "sound sample length 64 bytes", "audio period"):
        assert rendered.count(note) == 1, rendered
    exact(source, rendered, original)


def test_conflicting_indexed_entry_contract_refuses_without_appending(tmp_path):
    source, _ = fixture(tmp_path, " move.w d1,$A6(a6)\n rts\n")
    params = {"hunk": 0, "addr": 0, "register": "A6", "note": "Original dispatch only",
              "hardware_indexed": {"base_symbol": "_custom", "index_register": "D7", "stride": 16,
                                   "index_values": [0, 1, 2, 3]}}
    kind, payload = target_catalog_manual_payload("target.code.hardware_indexed_input.add", params)
    append_manual_actions(tmp_path, binary_source=source, actions=[(ManualActionKind(kind), payload)])
    history = manual_action_log_path(tmp_path)
    before = history.read_bytes()
    params["hardware_indexed"] = {**params["hardware_indexed"], "index_values": [0, 1]}
    kind, payload = target_catalog_manual_payload("target.code.hardware_indexed_input.add", params)
    with pytest.raises((RuntimeError, ValueError)):
        append_manual_actions(tmp_path, binary_source=source, actions=[(ManualActionKind(kind), payload)])
    assert history.read_bytes() == before


@pytest.mark.parametrize("change", [
    "jsr (a0)", "movea.l (a0),a6", "move.w d1,a6", "move.l (a6)+,d1",
    "move.l -(a6),d1", "movem.l (a0),a6", "adda.w d1,a6",
])
def test_unknown_writes_and_calls_discard_relative_family(tmp_path, change):
    source, _ = fixture(tmp_path, f""" moveq #2,d0
 lea.l $DFF000.l,a6
 lsl.w #4,d0
 adda.w d0,a6
 {change}
 move.w d2,$A6(a6)
 rts
""")
    assert not analyze(source)


@pytest.mark.parametrize("last_channel", [4, 8, 127])
def test_outside_sdk_family_or_domain_capacity_is_not_claimed(tmp_path, last_channel):
    source, _ = fixture(tmp_path, f""" moveq #{last_channel},d7
loop:
 lea.l $DFF000.l,a6
 move.w d7,d0
 lsl.w #4,d0
 adda.w d0,a6
 move.w d1,$A6(a6)
 dbf d7,loop
 rts
""")
    assert not analyze(source)


def test_unknown_loop_counter_does_not_invent_channel_bounds(tmp_path):
    source, _ = fixture(tmp_path, """loop:
 lea.l $DFF000.l,a6
 move.w d7,d0
 lsl.w #4,d0
 adda.w d0,a6
 move.w d1,$A6(a6)
 dbf d7,loop
 rts
""")
    assert not analyze(source)


def test_incomplete_fixed_point_does_not_publish_partial_channel_set(tmp_path, monkeypatch):
    monkeypatch.setenv("AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS", "6")
    source, _ = fixture(tmp_path, """ moveq #3,d7
loop:
 lea.l $DFF000.l,a6
 move.w d7,d0
 lsl.w #4,d0
 adda.w d0,a6
 move.w d1,$A6(a6)
 dbf d7,loop
 rts
""")
    assert not analyze(source)


@pytest.mark.parametrize(("alternative", "expected"), [("moveq #3,d0", [0, 48]),
                                                        ("moveq #4,d0", None),
                                                        ("move.w (a0),d0", None)])
def test_cfg_join_unions_known_channels_and_rejects_unknown_or_invalid_members(tmp_path, alternative, expected):
    source, _ = fixture(tmp_path, f""" tst.w d1
 beq other
 moveq #0,d0
 bra joined
other:
 {alternative}
joined:
 lea.l $DFF000.l,a6
 lsl.w #4,d0
 adda.w d0,a6
 move.w d1,$A6(a6)
 rts
""")
    uses = analyze(source)
    if expected:
        assert [u["relative_base_offsets"] for u in uses] == [expected]
    else:
        assert not uses


@pytest.mark.parametrize("write", ["move.b #3,d0", "move.w (a0),d0", "swap d0"])
def test_partial_and_unmodelled_scalar_writes_do_not_supply_a_channel(tmp_path, write):
    source, _ = fixture(tmp_path, f""" moveq #0,d0
 {write}
 lea.l $DFF000.l,a6
 lsl.w #4,d0
 adda.w d0,a6
 move.w d1,$A6(a6)
 rts
""")
    assert not analyze(source)


@pytest.mark.parametrize("base", ["_custom", "unknown_hardware_profile"])
def test_indexed_input_contract_uses_catalog_native_admission_and_explicit_source_note(tmp_path, base):
    source, original = fixture(tmp_path, """ move.l a2,$A0(a6)
 move.w #$20,$A4(a6)
 move.w d1,$A6(a6)
 move.w d2,$A8(a6)
 rts
""")
    assert not analyze(source)
    kind, payload = target_catalog_manual_payload("target.code.hardware_indexed_input.add", {
        "hunk": 0, "addr": 0, "register": "A6", "note": "Original dispatch entry only",
        "hardware_indexed": {"base_symbol": base, "index_register": "D7", "stride": 16,
                             "index_values": [0, 1, 2, 3]},
    })
    history = manual_action_log_path(tmp_path)
    before = history.read_bytes() if history.exists() else None
    if base != "_custom":
        with pytest.raises((ValueError, RuntimeError)):
            append_manual_actions(tmp_path, binary_source=source, actions=[(ManualActionKind(kind), payload)])
        assert (history.read_bytes() if history.exists() else None) == before
        return
    append_manual_actions(tmp_path, binary_source=source, actions=[(ManualActionKind(kind), payload)])
    with effective_metadata_file(tmp_path) as metadata:
        analysis = c_backend.analyze_project_source_with_c_backend(source, metadata_path=metadata)
        rendered = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
        policy = c_backend.effective_policy_project_source_with_c_backend(source, metadata_path=metadata)
    uses = [u for s in analysis["sections"] for u in s["platform_address_uses"]]
    assert len(uses) == 4
    assert all(u["use_shape_name"] == "hardware_register_family" for u in uses)
    assert all(u["relative_base_offsets"] == [0, 16, 32, 48] and u["address"] is None for u in uses)
    assert all(u["requires_indexed_input_contract"] is True for u in uses)
    assert policy["analysis_policy"]["register_seeds"][0]["hardware_indexed"] == payload["register_seed"]["hardware_indexed"]
    assert "INPUT contract: A6=_custom+16*D7.w; D7.w in {0,1,2,3}" in rendered
    assert "aud0+ac_per(a6)\t; audio period" in rendered
    exact(source, rendered, original)
