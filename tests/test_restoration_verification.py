"""Receipt integrity, bounded probes and native include portability."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import restoration_verification as rv
from amiga_reversing.disasm.c_backend import (
    assemble_platform_source_text_with_c_backend,
)


def receipt(tmp_path, monkeypatch, subject="rev"):
    monkeypatch.setattr(rv, "PROJECT_ROOT", tmp_path)
    directory = rv._directory("target")
    payload = directory / "rebuilt.bin"
    payload.write_bytes(b"actual rebuilt bytes")
    return rv._persist(
        "target",
        {
            "kind": "verification",
            "target_id": "target",
            "subject_revision": subject,
            "exact": True,
            "rebuilt_path": str(payload),
            "output_sha256": rv._hash(payload.read_bytes()),
        },
    )


def test_stale_verification_refused(tmp_path, monkeypatch):
    record = receipt(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="stale"):
        rv._verified_receipt("target", "new revision", record)


def test_payload_tampering_refused(tmp_path, monkeypatch):
    record = receipt(tmp_path, monkeypatch)
    Path(record["rebuilt_path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        rv._verified_receipt("target", "rev", record)


def test_caller_cannot_forge_exact_receipt(tmp_path, monkeypatch):
    record = receipt(tmp_path, monkeypatch)
    record["subject_revision"] = "forged"
    with pytest.raises(ValueError, match="stale"):
        rv._verified_receipt("target", "forged", record)


def test_probe_path_escape_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(rv, "PROJECT_ROOT", tmp_path)
    with pytest.raises(ValueError, match="under runtime/scenarios"):
        rv.run_probe("target", "rev", "question?", "../../evil.json", {})


def scenario(tmp_path, waits=2):
    path = tmp_path / "runtime/scenarios/test.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "direct_payload_contract": "test",
                "phases": [
                    {"observable": "direct_payload_handoff"},
                    {
                        "name": "entry",
                        "wait_seconds": waits,
                        "breakpoint_stable_key": "s0:00000000:instruction",
                    },
                ],
            }
        )
    )
    return path


def test_aggregate_wait_limit_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(rv, "PROJECT_ROOT", tmp_path)
    scenario(tmp_path, 120)
    with pytest.raises(ValueError, match="total observation budget"):
        rv.run_probe("target", "rev", "question?", "test.json", {})


@pytest.mark.parametrize(
    ("phase_status", "runner_status", "expected"),
    [
        ("hit", "ok", "observed"),
        ("timeout", "incomplete", "not_observed"),
        ("not_hit", "incomplete", "failed"),
        ("exception", "failed", "failed"),
        ("exception", "timeout", "not_observed"),
    ],
)
def test_probe_uses_rebuilt_and_preserves_negative_limits(
    tmp_path,
    monkeypatch,
    phase_status,
    runner_status,
    expected,
):
    record = receipt(tmp_path, monkeypatch)
    scenario(tmp_path)
    rom = tmp_path / "rom"
    rom.write_bytes(b"fixture")
    monkeypatch.setenv("COPPERLINE_ROM", str(rom))
    monkeypatch.setattr(rv, "resolve_binary", lambda _: Path("copperline"))
    monkeypatch.setattr(
        rv,
        "load_contract",
        lambda _: SimpleNamespace(target_id="target", identifier="test"),
    )
    monkeypatch.setattr(
        rv,
        "compile_scenario",
        lambda *a, **k: {"phases": [{"stable_key": "s0:00000000:instruction"}]},
    )
    builds = []
    monkeypatch.setattr(
        rv, "build_boot_adf", lambda contract, payload, output: builds.append(payload)
    )
    sessions = []

    def run(session):
        sessions.append(session)
        if phase_status == "exception":
            if runner_status == "timeout":
                raise rv.CopperlineTimeout("bounded deadline")
            raise rv.CopperlineError("cannot establish verified handoff")
        return {
            "status": runner_status,
            "observation": {"scenario": {"phases": [{"status": phase_status}]}},
        }

    monkeypatch.setattr(rv, "run_session", run)
    result = rv.run_probe("target", "rev", "Does entry execute?", "test.json", record)
    assert result["status"] == expected
    assert builds == [Path(record["rebuilt_path"])]
    assert sessions[0].target_payload_path == builds[0]
    assert result["unknowns"] and result["source_phases"][0]["stable_key"]


def test_native_include_joins_root_and_nested_paths(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "constants.i").write_text("ANSWER equ 42\n")
    (tmp_path / "root.i").write_text('include "nested/constants.i"\n')
    rebuilt, _ = assemble_platform_source_text_with_c_backend(
        "amiga-raw",
        'include "root.i"\n section code,code\n dc.w ANSWER\n',
        include_dir=tmp_path,
    )
    assert rebuilt == bytes.fromhex("002a")


def test_verify_binds_one_source_to_both_gates(tmp_path, monkeypatch):
    monkeypatch.setattr(rv, "PROJECT_ROOT", tmp_path)
    source_path = tmp_path / "restored.s"
    rebuilt = tmp_path / "rebuilt.bin"
    rebuilt.write_bytes(b"\x4e\x75")
    paths = SimpleNamespace(output_path=source_path, binary_source=object())
    monkeypatch.setattr(rv, "resolve_project_paths", lambda _: paths)
    monkeypatch.setattr(rv, "read_binary_source_bytes", lambda _: b"\x4e\x75")
    calls = []

    def reproduce(target, **kwargs):
        calls.append(kwargs["pre_rendered_source_text"])
        return {
            "comparison": {"full_file_exact": True},
            "rebuilt_path": str(rebuilt),
            "status": "exact",
        }

    def oracle(target, **kwargs):
        calls.append(kwargs["pre_rendered_source_text"])
        return {"comparison_level": "oracle.full_file_match"}

    monkeypatch.setattr(rv, "run_reproduction", reproduce)
    monkeypatch.setattr(rv, "run_vasm_oracle", oracle)
    artifact = SimpleNamespace(source_text_with_profile=lambda: (" rts\n", {}))
    result = rv.verify("target", "revision", artifact=artifact)
    assert calls == [" rts\n", " rts\n"]
    assert source_path.read_text() == " rts\n"
    assert result["exact"] and result["subject_revision"] == "revision"
    assert Path(result["rebuilt_path"]).read_bytes() == b"\x4e\x75"


def test_failed_reproduction_cannot_reuse_surviving_binary(tmp_path, monkeypatch):
    monkeypatch.setattr(rv, "PROJECT_ROOT", tmp_path)
    paths = SimpleNamespace(output_path=None, binary_source=object())
    monkeypatch.setattr(rv, "resolve_project_paths", lambda _: paths)
    monkeypatch.setattr(rv, "read_binary_source_bytes", lambda _: b"original")
    monkeypatch.setattr(
        rv,
        "run_reproduction",
        lambda *a, **k: {
            "status": "assembler_error",
            "rebuilt_path": str(tmp_path / "old.bin"),
        },
    )
    monkeypatch.setattr(rv, "run_vasm_oracle", lambda *a, **k: {})
    artifact = SimpleNamespace(source_text_with_profile=lambda: ("invalid\n", {}))
    result = rv.verify("target", "revision", artifact=artifact)
    assert result["status"] == "failed"
    assert result["rebuilt_path"] is None and result["output_sha256"] is None


def test_receipt_read_rejects_path_and_tampered_content(tmp_path, monkeypatch):
    record = receipt(tmp_path, monkeypatch)
    assert rv.load_receipt("target", record["receipt_id"]) == record
    with pytest.raises(ValueError, match="identity"):
        rv.load_receipt("target", "../receipt")
    path = rv._directory("target") / (record["receipt_id"] + ".json")
    path.write_text("{}")
    with pytest.raises(ValueError, match="integrity"):
        rv.load_receipt("target", record["receipt_id"])


def test_oracle_mismatch_blocks_exact_acceptance(tmp_path, monkeypatch):
    monkeypatch.setattr(rv, "PROJECT_ROOT", tmp_path)
    rebuilt = tmp_path / "output.bin"
    rebuilt.write_bytes(b"exact native")
    monkeypatch.setattr(
        rv,
        "resolve_project_paths",
        lambda _: SimpleNamespace(output_path=None, binary_source=None),
    )
    monkeypatch.setattr(rv, "read_binary_source_bytes", lambda _: b"exact native")
    monkeypatch.setattr(
        rv,
        "run_reproduction",
        lambda *a, **k: {
            "comparison": {"full_file_exact": True},
            "rebuilt_path": str(rebuilt),
        },
    )
    monkeypatch.setattr(
        rv, "run_vasm_oracle", lambda *a, **k: {"comparison_level": "oracle.mismatch"}
    )
    result = rv.verify(
        "target",
        "revision",
        artifact=SimpleNamespace(source_text_with_profile=lambda: ("source", {})),
    )
    assert result["framework_exact"] is True
    assert result["exact"] is False
    with pytest.raises(ValueError, match="exact rebuilt"):
        rv._verified_receipt("target", "revision", result)
