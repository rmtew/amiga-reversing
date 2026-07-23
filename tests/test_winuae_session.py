from __future__ import annotations

from pathlib import Path

from amiga_reversing.tools import winuae_session


def test_headless_session_command_is_non_interactive_and_payload_bound() -> None:
    session = winuae_session.HeadlessWinUaeSession(
        rom_path=Path(r"C:\roms\kick.rom"),
        floppy0=Path(r"C:\media\pandora.adf"),
        target_payload_path=Path(r"C:\target\binary.bin"),
        runner_path=Path(r"C:\repo\tools\run_winuae_headless.ps1"),
        state_directory=Path(r"C:\tmp\winuae"),
        continue_seconds=60,
    )

    assert session.command() == [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
        r"C:\repo\tools\run_winuae_headless.ps1", "-RomPath", r"C:\roms\kick.rom",
        "-TargetPayloadPath", r"C:\target\binary.bin", "-ContinueSeconds", "60",
        "-Floppy0", r"C:\media\pandora.adf", "-StateDirectory", r"C:\tmp\winuae",
    ]


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

    def close(self) -> None:
        pass
