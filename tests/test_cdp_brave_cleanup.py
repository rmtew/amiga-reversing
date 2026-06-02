from __future__ import annotations

import subprocess

from tests import cdp_brave


class _FakeProcess:
    pid = 12345

    def __init__(self) -> None:
        self.terminated = False
        self.killed = False
        self.wait_calls = 0

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls += 1
        return 0


def test_windows_brave_cleanup_falls_back_when_taskkill_cannot_start(monkeypatch) -> None:
    process = _FakeProcess()

    def fail_taskkill(*_args, **_kwargs):
        raise OSError("invalid handle")

    monkeypatch.setattr(cdp_brave.sys, "platform", "win32")
    monkeypatch.setattr(cdp_brave.subprocess, "run", fail_taskkill)

    cdp_brave._terminate_brave_process(process)  # type: ignore[arg-type]

    assert process.terminated is True
    assert process.killed is False
    assert process.wait_calls == 1


def test_brave_cleanup_kills_process_after_timeout(monkeypatch) -> None:
    class SlowProcess(_FakeProcess):
        def wait(self, timeout: float | None = None) -> int:
            self.wait_calls += 1
            if self.wait_calls == 1:
                raise subprocess.TimeoutExpired("brave", timeout)
            return 0

    process = SlowProcess()
    monkeypatch.setattr(cdp_brave.sys, "platform", "linux")

    cdp_brave._terminate_brave_process(process)  # type: ignore[arg-type]

    assert process.terminated is True
    assert process.killed is True
    assert process.wait_calls == 2


def test_brave_cdp_file_or_module_selected_accepts_direct_file_and_nodeid() -> None:
    assert cdp_brave.brave_cdp_file_or_module_selected(["tests/test_web_e2e_cdp.py"])
    assert cdp_brave.brave_cdp_file_or_module_selected(
        ["tests\\test_web_e2e_cdp.py::test_brave_cdp_can_open_project_and_render_listing"]
    )
    assert cdp_brave.brave_cdp_file_or_module_selected(["tests.test_web_e2e_cdp"])
    assert not cdp_brave.brave_cdp_file_or_module_selected(["tests"])


def test_brave_cdp_marker_selected_detects_web_e2e_marker_expression() -> None:
    assert cdp_brave.brave_cdp_marker_selected(["-m", "web_e2e"])
    assert cdp_brave.brave_cdp_marker_selected(["--markexpr=web_e2e and not slow"])
    assert not cdp_brave.brave_cdp_marker_selected(["-m", "not integration"])
