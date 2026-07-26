from __future__ import annotations

import json
from pathlib import Path

from amiga_reversing.tools import winuae_session


def test_headless_session_command_is_non_interactive_and_payload_bound() -> None:
    session = winuae_session.HeadlessWinUaeSession(
        rom_path=Path(r"C:\roms\kick.rom"),
        floppy0=Path(r"C:\media\pandora.adf"),
        host_directory=Path(r"C:\media\payload"),
        target_payload_path=Path(r"C:\target\binary.bin"),
        runner_path=Path(r"C:\repo\tools\run_winuae_headless.ps1"),
        state_directory=Path(r"C:\tmp\winuae"),
        continue_seconds=60,
    )

    assert session.command() == [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
        r"C:\repo\tools\run_winuae_headless.ps1", "-RomPath", r"C:\roms\kick.rom",
        "-TargetPayloadPath", r"C:\target\binary.bin", "-ContinueSeconds", "60",
        "-Floppy0", r"C:\media\pandora.adf", "-HostDirectory", r"C:\media\payload",
        "-StateDirectory", r"C:\tmp\winuae",
    ]


def test_headless_session_passes_only_a_source_offset_breakpoint() -> None:
    session = winuae_session.HeadlessWinUaeSession(
        rom_path=Path(r"C:\roms\kick.rom"),
        target_payload_path=Path(r"C:\target\binary.bin"),
        runner_path=Path(r"C:\repo\tools\run_winuae_headless.ps1"),
        breakpoint_source_offset=0xBA8,
        breakpoint_wait_seconds=12,
    )

    assert session.command()[-4:] == [
        "-BreakpointSourceOffset", "0xba8", "-BreakpointWaitSeconds", "12",
    ]


def test_headless_session_does_not_pass_breakpoint_wait_without_a_breakpoint() -> None:
    session = winuae_session.HeadlessWinUaeSession(
        rom_path=Path(r"C:\roms\kick.rom"),
        target_payload_path=Path(r"C:\target\binary.bin"),
        runner_path=Path(r"C:\repo\tools\run_winuae_headless.ps1"),
        breakpoint_wait_seconds=12,
    )

    assert "-BreakpointWaitSeconds" not in session.command()


def test_headless_session_passes_a_single_bounded_memory_observation() -> None:
    session = winuae_session.HeadlessWinUaeSession(
        rom_path=Path(r"C:\roms\kick.rom"),
        target_payload_path=Path(r"C:\target\binary.bin"),
        runner_path=Path(r"C:\repo\tools\run_winuae_headless.ps1"),
        observation_memory_address=0x400,
        observation_memory_equals=b"HAND",
        observation_memory_write_watch=True,
    )

    assert session.command()[-5:] == [
        "-ObservationMemoryAddress", "0x400", "-ObservationMemoryEquals", "48414e44",
        "-ObservationMemoryWriteWatch",
    ]


def test_direct_contract_requires_an_isolated_generated_adf_state_directory() -> None:
    parser = winuae_session.build_parser()
    args = parser.parse_args(["--target", "pandora", "--rom", "C:\\roms\\kick.rom", "--direct-payload-contract", "pandora"])

    assert args.direct_payload_contract == "pandora"


def test_compile_scenario_resolves_only_canonical_rows_once(monkeypatch, tmp_path: Path) -> None:
    scenario = tmp_path / "scenario.json"
    output = tmp_path / "compiled.json"
    scenario.write_text(json.dumps({
        "schema_version": 1,
        "identifier": "test",
        "target_id": "pandora",
        "phases": [
            {"name": "boot", "observable": "direct_payload_handoff"},
            {"name": "title", "breakpoint_stable_key": "s0:00000BA8:instruction:760", "wait_seconds": 10},
            {"name": "inventory", "breakpoint_stable_key": "s0:00002904:instruction:2473", "wait_seconds": 10,
             "capture": {"registers": ["a4", "a5"], "memory_reads": []}},
        ],
        "input_events": [{"after_phase": "title", "control": "port1 fire", "delay_seconds": 3, "duration_seconds": 1}],
    }), encoding="utf-8")
    artifact = _FakeArtifact({"stable_key": "unused", "runtime_observation_view": {"base_addr": 0x10000, "source_start": 0, "source_end": 0x40000}})
    artifact._runtime_observation_views = ({"base_addr": 0x10000, "source_start": 0, "source_end": 0x40000},)
    rows = {
        0xBA8: {"stable_key": "s0:00000BA8:instruction:760", "start_offset": 0xBA8},
        0x2904: {"stable_key": "s0:00002904:instruction:2473", "start_offset": 0x2904},
    }
    artifact.row_for_source_offset = lambda *, section_index, offset: rows[offset]  # type: ignore[method-assign]
    monkeypatch.setattr(winuae_session, "build_project_listing_artifact_profile", lambda _: (0, {}, artifact))

    compiled = winuae_session.compile_scenario("pandora", scenario, output)

    assert [phase["breakpoint_address"] for phase in compiled["phases"]] == [0x10BA8, 0x12904]
    assert json.loads(output.read_text(encoding="utf-8"))["identifier"] == "test"


def test_compile_scenario_plans_generated_symbols_in_the_public_session(monkeypatch, tmp_path: Path) -> None:
    scenario = tmp_path / "scenario.json"
    output = tmp_path / "compiled.json"
    scenario.write_text(json.dumps({"schema_version": 1, "identifier": "test", "target_id": "pandora", "phases": [{"name": "boot", "observable": "direct_payload_handoff"}, {"name": "title", "breakpoint_stable_key": "s0:00000BA8:instruction:760", "wait_seconds": 10}]}), encoding="utf-8")
    artifact = _FakeArtifact({"stable_key": "s0:00000BA8:instruction:760", "start_offset": 0xBA8, "runtime_observation_view": {"base_addr": 0x12000, "source_start": 0, "source_end": 0x40000}})
    artifact._runtime_observation_views = ({"base_addr": 0x12000, "source_start": 0, "source_end": 0x40000},)
    monkeypatch.setattr(winuae_session, "build_project_listing_artifact_profile", lambda _: (0, {}, artifact))
    monkeypatch.setattr(winuae_session, "generate_gdb_symbol_artifact", lambda *_: type("Symbols", (), {"scenario_payload": lambda _: {"elf_path": "generated.elf", "runtime_view": {"base_addr": 0x12000}, "functions": []}})())

    compiled = winuae_session.compile_scenario("pandora", scenario, output, symbol_directory=tmp_path)

    assert compiled["phases"][0]["breakpoint_address"] == 0x12BA8
    assert compiled["symbols"]["runtime_view"]["base_addr"] == 0x12000


def test_resolve_breakpoint_stable_key_requires_current_canonical_row(monkeypatch) -> None:
    row = {"stable_key": "s0:00000BA8:instruction:760", "start_offset": 0xBA8}
    artifact = _FakeArtifact(row)
    monkeypatch.setattr(winuae_session, "build_project_listing_artifact_profile", lambda _: (0, {}, artifact))

    assert winuae_session.resolve_breakpoint_stable_key("pandora", row["stable_key"]) == row
    assert artifact.source_offset_call == (0, 0xBA8)


def test_resolve_breakpoint_hit_requires_the_expected_runtime_pc() -> None:
    row = {"stable_key": "s0:00000BA8:instruction:760", "section_index": 0, "start_offset": 0xBA8, "kind": "instruction", "text": "rts"}
    report = {
        "observation": {
            "active_execution": {"payload": {"runtime_base": "0x10000"}},
            "breakpoint": {"status": "hit", "stop_reason": "breakpoint-hit", "pc": "0x10ba8"},
        }
    }

    resolved = winuae_session.resolve_breakpoint_hit(row, report)

    assert resolved["status"] == "hit"
    assert resolved["expected_runtime_address"] == "0x00010ba8"


def test_resolve_paused_pc_rejects_ambiguous_payload_without_runtime_view(monkeypatch) -> None:
    report = {"observation": {"pc": "0x00010bc6", "active_execution": {"payload": {"status": "ambiguous"}}}}
    monkeypatch.setattr(
        winuae_session,
        "build_project_listing_artifact_profile",
        lambda _: (0, {}, _FakeArtifact({"runtime_observation_view": None})),
    )

    assert winuae_session.resolve_paused_pc("unused", report) == {
        "status": "not_target_payload",
        "pc": "0x00010bc6",
        "payload": {"status": "ambiguous"},
        "reason": "ambiguous payload sample has no confirmed runtime observation view",
    }


def test_resolve_paused_pc_uses_confirmed_runtime_view_for_ambiguous_sample(monkeypatch) -> None:
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
            "active_execution": {"payload": {"status": "ambiguous", "matching_offsets": ["0xbb8", "0xc44"]}},
        }
    }
    monkeypatch.setattr(winuae_session, "build_project_listing_artifact_profile", lambda _: (0, {}, _FakeArtifact(row)))

    resolved = winuae_session.resolve_paused_pc("pandora", report)

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
