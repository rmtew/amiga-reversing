from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.tools import copperline_session


def test_native_session_plan_is_explicit_and_bounded():
    session = copperline_session.HeadlessCopperlineSession(
        rom_path=Path("kick.rom"),
        target_payload_path=Path("binary.bin"),
        binary_path=Path("copperline"),
        continue_seconds=12,
    )
    assert session.plan()["emulator"] == "copperline 1.0.0"
    assert session.plan()["continue_seconds"] == 12


@pytest.mark.parametrize("phase", [
    {"name": "boot", "observable": "direct_payload_handoff",
     "memory_access_watch": {"address": 0, "access": "read", "engine": "cpu", "wait_seconds": 1}},
    {"name": "packet", "breakpoint_stable_key": "s0:00006B0A:instruction",
     "wait_seconds": 1, "memory_access_watch": {"address": 0, "access": "read",
     "engine": "blitter", "wait_seconds": 1, "class": "cpu"}},
])
def test_compile_rejects_unanchored_or_extra_watch_fields_before_listing(tmp_path, phase):
    first = {"name": "boot", "observable": "direct_payload_handoff"}
    phases = [phase, {"name": "next"}] if phase["name"] == "boot" else [first, phase]
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps({"schema_version": 1, "target_id": "fixture",
                               "identifier": "invalid", "phases": phases}))
    with pytest.raises(ValueError, match="Memory access watch requires"):
        copperline_session.compile_scenario("fixture", path, tmp_path / "compiled.json")


@pytest.mark.parametrize("observable", ["direct_payload_handoff", "verified_checkpoint"])
def test_compile_scenario_resolves_only_canonical_rows_once(
    monkeypatch, tmp_path: Path, observable
) -> None:
    scenario = tmp_path / "scenario.json"
    output = tmp_path / "compiled.json"
    scenario.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "identifier": "test",
                "target_id": "pandora",
                "phases": [
                    {"name": "boot", "observable": observable},
                    {
                        "name": "title",
                        "breakpoint_stable_key": "s0:00000BA8:instruction:760",
                        "wait_seconds": 10,
                        "memory_access_watch": {
                            "address": 0x49DC8, "access": "read",
                            "engine": "blitter", "wait_seconds": 2,
                        },
                    },
                    {
                        "name": "inventory",
                        "breakpoint_stable_key": "s0:00002904:instruction:2473",
                        "wait_seconds": 10,
                        "capture": {"registers": ["a4", "a5"], "memory_reads": []},
                        "occurrences": 64,
                        "capture_first": True,
                    },
                ],
                "input_events": [
                    {
                        "after_phase": "title",
                        "control": "port1 fire",
                        "release_after_phase": "inventory",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    artifact = _FakeArtifact(
        {
            "stable_key": "unused",
            "runtime_observation_view": {
                "base_addr": 0x10000,
                "source_start": 0,
                "source_end": 0x40000,
            },
        }
    )
    artifact._runtime_observation_views = (
        {"base_addr": 0x10000, "source_start": 0, "source_end": 0x40000},
    )
    rows = {
        0xBA8: {"stable_key": "s0:00000BA8:instruction:760", "start_offset": 0xBA8},
        0x2904: {"stable_key": "s0:00002904:instruction:2473", "start_offset": 0x2904},
    }
    artifact.row_for_source_offset = lambda *, section_index, offset: rows[offset]  # type: ignore[method-assign]
    monkeypatch.setattr(
        copperline_session,
        "build_project_listing_artifact_profile",
        lambda _: (0, {}, artifact),
    )

    compiled = copperline_session.compile_scenario("pandora", scenario, output)

    assert [phase["breakpoint_address"] for phase in compiled["phases"]] == [
        0x10BA8,
        0x12904,
    ]
    assert compiled["input_events"] == [
        {
            "after_phase": "title",
            "release_after_phase": "inventory",
            "control": "port1 fire",
        }
    ]
    assert "occurrences" not in compiled["phases"][0]
    assert "capture_first" not in compiled["phases"][0]
    assert compiled["phases"][1]["occurrences"] == 64
    assert compiled["phases"][1]["capture_first"] is True
    assert compiled["start_observable"] == observable
    assert compiled["phases"][0]["memory_access_watch"] == {
        "address": 0x49DC8, "access": "read", "engine": "blitter", "wait_seconds": 2,
    }
    assert json.loads(output.read_text(encoding="utf-8"))["identifier"] == "test"


def test_compile_scenario_plans_generated_symbols_in_the_public_session(
    monkeypatch, tmp_path: Path
) -> None:
    scenario = tmp_path / "scenario.json"
    output = tmp_path / "compiled.json"
    scenario.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "identifier": "test",
                "target_id": "pandora",
                "phases": [
                    {"name": "boot", "observable": "direct_payload_handoff"},
                    {
                        "name": "title",
                        "breakpoint_stable_key": "s0:00000BA8:instruction:760",
                        "wait_seconds": 10,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    artifact = _FakeArtifact(
        {
            "stable_key": "s0:00000BA8:instruction:760",
            "start_offset": 0xBA8,
            "runtime_observation_view": {
                "base_addr": 0x12000,
                "source_start": 0,
                "source_end": 0x40000,
            },
        }
    )
    artifact._runtime_observation_views = (
        {"base_addr": 0x12000, "source_start": 0, "source_end": 0x40000},
    )
    monkeypatch.setattr(
        copperline_session,
        "build_project_listing_artifact_profile",
        lambda _: (0, {}, artifact),
    )
    symbol_calls: list[dict[str, object]] = []

    def generate_symbols(*_: object, **kwargs: object) -> object:
        symbol_calls.append(kwargs)
        return {
            "metadata_path": "symbols.json",
            "runtime_view": {"base_addr": 0x12000},
            "functions": [],
        }

    monkeypatch.setattr(
        copperline_session, "generate_runtime_symbol_artifact", generate_symbols
    )

    compiled = copperline_session.compile_scenario(
        "pandora", scenario, output, symbol_directory=tmp_path
    )

    assert compiled["phases"][0]["breakpoint_address"] == 0x12BA8
    assert compiled["symbols"]["runtime_view"]["base_addr"] == 0x12000
    assert symbol_calls == [{"artifact": artifact}]


def test_resolve_breakpoint_stable_key_requires_current_canonical_row(
    monkeypatch,
) -> None:
    row = {"stable_key": "s0:00000BA8:instruction:760", "start_offset": 0xBA8}
    artifact = _FakeArtifact(row)
    monkeypatch.setattr(
        copperline_session,
        "build_project_listing_artifact_profile",
        lambda _: (0, {}, artifact),
    )

    assert (
        copperline_session.resolve_breakpoint_stable_key("pandora", row["stable_key"])
        == row
    )
    assert artifact.source_offset_call == (0, 0xBA8)


def test_resolve_breakpoint_hit_requires_the_expected_runtime_pc() -> None:
    row = {
        "stable_key": "s0:00000BA8:instruction:760",
        "section_index": 0,
        "start_offset": 0xBA8,
        "kind": "instruction",
        "text": "rts",
    }
    report = {
        "observation": {
            "active_execution": {"payload": {"runtime_base": "0x10000"}},
            "breakpoint": {
                "status": "hit",
                "stop_reason": "breakpoint-hit",
                "pc": "0x10ba8",
            },
        }
    }

    resolved = copperline_session.resolve_breakpoint_hit(row, report)

    assert resolved["status"] == "hit"
    assert resolved["expected_runtime_address"] == "0x00010ba8"


def test_resolve_paused_pc_rejects_ambiguous_payload_without_runtime_view(
    monkeypatch,
) -> None:
    report = {
        "observation": {
            "pc": "0x00010bc6",
            "active_execution": {"payload": {"status": "ambiguous"}},
        }
    }
    monkeypatch.setattr(
        copperline_session,
        "build_project_listing_artifact_profile",
        lambda _: (0, {}, _FakeArtifact({"runtime_observation_view": None})),
    )

    assert copperline_session.resolve_paused_pc("unused", report) == {
        "status": "not_target_payload",
        "pc": "0x00010bc6",
        "payload": {"status": "ambiguous"},
        "reason": "ambiguous payload sample has no confirmed runtime observation view",
    }


def test_resolve_paused_pc_uses_confirmed_runtime_view_for_ambiguous_sample(
    monkeypatch,
) -> None:
    row = {
        "stable_key": "s0:00000BB8:instruction:761",
        "section_index": 0,
        "start_offset": 0xBB8,
        "kind": "instruction",
        "text": "\tmove.w d0,$0004(a2)\n",
        "runtime_observation_view": {"source_start": 0, "base_addr": 0x10000},
    }
    report = {
        "observation": {
            "pc": "0x00010bb8",
            "active_execution": {
                "payload": {
                    "status": "ambiguous",
                    "matching_offsets": ["0xbb8", "0xc44"],
                }
            },
        }
    }
    monkeypatch.setattr(
        copperline_session,
        "build_project_listing_artifact_profile",
        lambda _: (0, {}, _FakeArtifact(row)),
    )

    resolved = copperline_session.resolve_paused_pc("pandora", report)

    assert resolved["status"] == "mapped_with_runtime_view"
    assert resolved["canonical_row"]["stable_key"] == "s0:00000BB8:instruction:761"


class _FakeArtifact:
    def __init__(self, row):
        self._row = row

    def row_for_runtime_address(self, *, address: int):
        return self._row

    def row_for_source_offset(self, *, section_index: int, offset: int):
        self.source_offset_call = (section_index, offset)
        return self._row

    def close(self) -> None:
        pass


def test_capture_validation_rejects_unbounded_or_conflicting_reads():
    import pytest

    for capture in (
        {"registers": ["pc"]},
        {"memory_reads": [{"address": 0, "size": 65}]},
        {"memory_reads": [{"address": 0, "base_register": "a0", "size": 1}]},
        {"memory_reads": [{"address": 0xFFFFFF, "size": 2}]},
        {"memory_reads": [{"base_register": "d0", "size": 1}]},
        {"commands": ["arbitrary"]},
    ):
        with pytest.raises(ValueError, match="[Cc]apture"):
            copperline_session.validate_capture(capture)


def test_capture_validation_accepts_status_register_with_bounded_general_registers():
    import pytest

    registers = [f"{kind}{index}" for kind in ("d", "a") for index in range(8)] + ["sr"]
    copperline_session.validate_capture({"registers": registers})
    with pytest.raises(ValueError, match="Capture registers"):
        copperline_session.validate_capture({"registers": registers + ["sr"]})


def test_stable_key_rejects_ambiguous_runtime_views():
    import pytest

    artifact = _FakeArtifact(
        {"stable_key": "s0:00000BA8:instruction", "start_offset": 0xBA8}
    )
    artifact._runtime_observation_views = [
        {"base_addr": 0x10000, "source_start": 0, "source_end": 0x4000},
        {"base_addr": 0x20000, "source_start": 0, "source_end": 0x4000},
    ]
    with pytest.raises(ValueError, match="Ambiguous"):
        copperline_session._resolve_breakpoint_stable_key_from_artifact(
            artifact, "s0:00000BA8:instruction"
        )


def test_unique_match_rejects_stale_reviewed_mapping(monkeypatch):
    row = {"start_offset": 0xBB8}
    monkeypatch.setattr(
        copperline_session,
        "build_project_listing_artifact_profile",
        lambda _: (0, {}, _FakeArtifact(row)),
    )
    report = {
        "observation": {
            "pc": "0x10bb8",
            "active_execution": {
                "payload": {
                    "status": "pc_matched",
                    "payload_offset": "0xcb8",
                    "runtime_base": "0xff00",
                }
            },
        }
    }
    assert (
        copperline_session.resolve_paused_pc("test", report)["status"]
        == "not_target_payload"
    )


def test_cli_incomplete_observation_exits_nonzero(monkeypatch, tmp_path, capsys):
    from types import SimpleNamespace

    binary = tmp_path / "copperline"
    binary.touch()
    monkeypatch.setattr(
        copperline_session,
        "resolve_project_paths",
        lambda _: SimpleNamespace(
            binary_source=SimpleNamespace(path=tmp_path / "payload")
        ),
    )
    monkeypatch.setattr(
        copperline_session,
        "run_session",
        lambda _: {"status": "incomplete", "observation": {}},
    )
    assert (
        copperline_session.main(
            ["--target", "fake", "--rom", "rom", "--copperline", str(binary), "--run"]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["runner"]["status"] == "incomplete"


def test_cli_loadseg_watch_cannot_move_after_source_breakpoint():
    import pytest

    with pytest.raises(ValueError, match="standalone observation"):
        copperline_session.main(
            [
                "--target",
                "fake",
                "--rom",
                "rom",
                "--loadseg-watch-seconds",
                "1",
                "--breakpoint-stable-key",
                "s0:00000000:instruction",
            ]
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("occurrences", 0),
        ("occurrences", 65),
        ("occurrences", True),
        ("occurrences", "2"),
        ("occurrences", 1.5),
        ("capture_first", 1),
    ],
)
def test_compile_occurrences_rejects_invalid_fields_before_analysis(
    tmp_path, monkeypatch, field, value
):
    phases = [
        {"name": "boot", "observable": "direct_payload_handoff"},
        {
            "name": "counted",
            "breakpoint_stable_key": "s0:00009844:instruction",
            "wait_seconds": 20,
            field: value,
        },
    ]
    path = tmp_path / "scenario.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "identifier": "test",
                "target_id": "pandora",
                "phases": phases,
            }
        )
    )

    def no_analysis(*args):
        raise AssertionError("Invalid occurrence request reached native analysis")

    monkeypatch.setattr(
        copperline_session, "build_project_listing_artifact_profile", no_analysis
    )
    with pytest.raises(ValueError, match=field):
        copperline_session.compile_scenario("pandora", path, tmp_path / "out.json")


def test_compile_occurrences_are_not_a_boot_handoff_counter(tmp_path):
    path = tmp_path / "scenario.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "identifier": "test",
                "target_id": "pandora",
                "phases": [
                    {
                        "name": "boot",
                        "observable": "direct_payload_handoff",
                        "occurrences": 2,
                    },
                    {
                        "name": "counted",
                        "breakpoint_stable_key": "s0:00009844:instruction",
                        "wait_seconds": 20,
                    },
                ],
            }
        )
    )
    with pytest.raises(ValueError, match="source-row"):
        copperline_session.compile_scenario("pandora", path, tmp_path / "out.json")


@pytest.mark.parametrize(
    ("offset", "expected"), [(0, 0x397C), (127, 0x39FB), (128, None)]
)
def test_region_capture_resolves_native_identity_and_bounds(
    monkeypatch, tmp_path, offset, expected
):
    from types import SimpleNamespace

    artifact = SimpleNamespace(
        memory_regions_payload=lambda: {
            "items": [{"region_id": "keys", "runtime_address": 0x397C, "size": 128}]
        },
        close=lambda: None,
    )
    monkeypatch.setattr(
        copperline_session,
        "build_project_listing_artifact_profile",
        lambda _: (None, None, artifact),
    )
    monkeypatch.setattr(
        copperline_session,
        "_resolve_breakpoint_stable_key_from_artifact",
        lambda *args: {
            "runtime_breakpoint_address": 0x10000,
            "start_offset": 0,
            "runtime_observation_view": {},
        },
    )
    scenario = {
        "schema_version": 1,
        "target_id": "fixture",
        "identifier": "region-capture",
        "phases": [
            {"name": "handoff", "observable": "direct_payload_handoff"},
            {
                "name": "read",
                "breakpoint_stable_key": "s0:00000000:instruction",
                "wait_seconds": 1,
                "capture": {
                    "memory_reads": [{"region_id": "keys", "offset": offset, "size": 1}]
                },
            },
        ],
    }
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(scenario))
    output = tmp_path / "compiled.json"
    if expected is None:
        with pytest.raises(ValueError, match="exceeds its extent"):
            copperline_session.compile_scenario("fixture", path, output)
        assert not output.exists()
    else:
        result = copperline_session.compile_scenario("fixture", path, output)
        assert result["phases"][0]["capture"]["memory_reads"] == [
            {"address": expected, "size": 1}
        ]


def test_custom_register_capture_is_bounded_by_names_or_even_offsets():
    copperline_session.validate_capture({'custom_registers': ['AUD0VOL', 'DMACON']})
    copperline_session.validate_capture({'custom_registers': [0, 2, 0x1C, 0x1E, 0x1FE]})
    for names in [['AUD0VOL']*17, ['mem.write'], [True], [-2], [1], [0x200]]:
        with pytest.raises(ValueError, match='custom registers'):
            copperline_session.validate_capture({'custom_registers': names})


def test_compiler_and_runner_share_bounded_phase_capacity(monkeypatch, tmp_path):
    path = tmp_path/'many-phases.json'
    phases = [{'name': 'boot', 'observable': 'direct_payload_handoff'}] + [
        {'name': f'visit_{i}', 'breakpoint_stable_key': 's0:00000004:instruction', 'wait_seconds': 1}
        for i in range(63)]
    scenario = {'schema_version': 1, 'identifier': 'many', 'target_id': 'fixture', 'phases': phases}
    row = {'stable_key': 's0:00000004:instruction', 'start_offset': 4}
    artifact = _FakeArtifact(row)
    artifact._runtime_observation_views = ({'base_addr': 0x10000, 'source_start': 0, 'source_end': 16},)
    monkeypatch.setattr(copperline_session, 'build_project_listing_artifact_profile', lambda _: (0, {}, artifact))
    path.write_text(json.dumps(scenario))
    compiled = copperline_session.compile_scenario('fixture', path, tmp_path/'compiled.json')
    assert len(compiled['phases']) == 63
    scenario['phases'].append(dict(phases[-1], name='excess'))
    path.write_text(json.dumps(scenario))
    with pytest.raises(ValueError, match='2..64'):
        copperline_session.compile_scenario('fixture', path, tmp_path/'excess.json')


@pytest.mark.parametrize('expectation', [
    {'expect_hex': None}, {'expect_hex': ''}, {'expect_hex': '0'},
    {'expect_hex': 'gg'}, {'expect_hex': '0000'},
    {'expect_mask_hex': 'ff'}, {'expect_hex': '00', 'expect_mask_hex': None},
    {'expect_hex': '00', 'expect_mask_hex': 'f'},
])
def test_capture_expectations_reject_malformed_or_size_mismatched_values(expectation):
    with pytest.raises(ValueError, match='expectation'):
        copperline_session.validate_capture({'memory_reads': [dict(address=0x2000, size=1, **expectation)]})


def test_capture_expectation_preserves_register_and_region_addressing():
    for address in ({'base_register': 'a6', 'offset': 558}, {'region_id': 'test'}):
        copperline_session.validate_capture({'memory_reads': [dict(size=1, expect_hex='00', expect_mask_hex='06', **address)]})


def test_state_goal_and_frame_budget_compile_through_shared_service(monkeypatch,tmp_path):
    row={'stable_key':'s0:00000004:instruction','start_offset':4}
    artifact=_FakeArtifact(row)
    artifact._runtime_observation_views=({'base_addr':0x10000,'source_start':0,'source_end':16},)
    monkeypatch.setattr(copperline_session,'build_project_listing_artifact_profile',lambda _:(0,{},artifact))
    p={'name':'goal','breakpoint_stable_key':row['stable_key'],'wait_seconds':1,
       'occurrences':8,'max_frames':12,'until_memory':{'address':0x6000,'size':1,'expect_hex':'03'}}
    s={'schema_version':1,'identifier':'goal','target_id':'fixture','phases':[
        {'name':'boot','observable':'direct_payload_handoff'},
        {'name':'anchor','breakpoint_stable_key':row['stable_key'],'wait_seconds':1},p]}
    path=tmp_path/'goal.json';path.write_text(json.dumps(s))
    r=copperline_session.compile_scenario('fixture',path,tmp_path/'compiled.json')
    assert r['phases'][-1]['until_memory']==p['until_memory']
    assert r['phases'][-1]['max_frames']==12
    del p['max_frames'];path.write_text(json.dumps(s))
    with pytest.raises(ValueError,match='frame and visit budgets'):
        copperline_session.compile_scenario('fixture',path,tmp_path/'rejected.json')


def test_compiler_accepts_runner_64_input_events_and_rejects65(monkeypatch,tmp_path):
    row={'stable_key':'s0:00000004:instruction','start_offset':4}
    artifact=_FakeArtifact(row)
    artifact._runtime_observation_views=({'base_addr':0x10000,'source_start':0,'source_end':16},)
    monkeypatch.setattr(copperline_session,'build_project_listing_artifact_profile',lambda _:(0,{},artifact))
    s={'schema_version':1,'identifier':'events','target_id':'fixture','phases':[
       {'name':'boot','observable':'direct_payload_handoff'},
       {'name':'start','breakpoint_stable_key':row['stable_key'],'wait_seconds':1},
       {'name':'end','breakpoint_stable_key':row['stable_key'],'wait_seconds':1}],
       'input_events':[{'after_phase':'start','control':'port1 fire','release_after_phase':'end'}]*64}
    path=tmp_path/'events.json';path.write_text(json.dumps(s))
    assert len(copperline_session.compile_scenario('fixture',path,tmp_path/'out.json')['input_events'])==64
    s['input_events'].append(dict(s['input_events'][0]));path.write_text(json.dumps(s))
    with pytest.raises(ValueError):copperline_session.compile_scenario('fixture',path,tmp_path/'reject.json')
