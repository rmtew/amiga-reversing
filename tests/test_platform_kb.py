from __future__ import annotations

import json
from pathlib import Path

from amiga_reversing.tools import platform_kb


def test_platform_kb_report_aggregates_fixture_artifacts(tmp_path: Path) -> None:
    _write_fixture_tree(tmp_path)

    report = platform_kb.build_report(tmp_path)

    ndk = report["ndk"]
    assert ndk["include_paths"] == 2
    assert ndk["libraries"] == 1
    assert ndk["functions"] == 2
    assert ndk["raw_available_since_counts"] == {"1.2": 1, "3.0": 1}
    assert ndk["normalized_available_since_counts"] == {"1.3": 1, "3.1": 1}
    assert ndk["raw_os_version_rank_coverage"]["1.2"] is True
    assert ndk["fd_version_counts"] == {"34": 1, "39": 1}
    assert report["hardware"]["joined_cpu_address_rows"] == 1
    assert report["corrections"]["review_status_counts"] == {"seeded": 1, "validated": 1}
    assert report["hunk"]["half_represented_record_types"] == ["HUNK_OVERLAY"]
    assert report["target_platform_summary"]["os_compatibility_state_counts"] == {
        "observed": 1,
        "no_os_calls": 1,
        "unknown": 1,
    }


def test_platform_kb_check_reports_enforced_debt(tmp_path: Path) -> None:
    _write_fixture_tree(tmp_path)
    corrections = tmp_path / "knowledge" / "amiga_ndk_corrections.json"
    corrections.write_text(
        json.dumps({"items": [{"review_status": "mystery"}, {"review_status": "seeded"}]}),
        encoding="utf-8",
    )

    violations = platform_kb.check_report(platform_kb.build_report(tmp_path))

    assert any("unknown review_status" in violation for violation in violations)
    assert any("missing citations" in violation for violation in violations)
    assert any("HUNK records are half-represented: HUNK_OVERLAY" in violation for violation in violations)
    assert any("raw OS availability precision" in violation for violation in violations)


def test_platform_kb_report_text_is_stable(tmp_path: Path) -> None:
    _write_fixture_tree(tmp_path)

    text = platform_kb.format_report(platform_kb.build_report(tmp_path))

    assert "Platform KB coverage report" in text
    assert "raw available_since counts: 1.2=1, 3.0=1" in text
    assert "half-represented record types: HUNK_OVERLAY" in text


def _write_fixture_tree(root: Path) -> None:
    knowledge = root / "knowledge"
    generated = root / "src" / "generated"
    targets = root / "targets"
    knowledge.mkdir(parents=True)
    generated.mkdir(parents=True)
    targets.mkdir()
    (knowledge / "adcd21_inventory.md").write_text(
        "| Path | Description | Status |\n"
        "|------|-------------|--------|\n"
        "| `NDK/NDK_3.1/` | includes | **Parsed** |\n"
        "| `EXTRAS/TOOLS/` | tools | Not explored |\n",
        encoding="utf-8",
    )
    _write_json(
        knowledge / "amiga_ndk_includes_parsed.json",
        {
            "_meta": {
                "parsed_include_paths": ["exec/exec.i", "dos/dos.i"],
                "include_min_versions": {"exec/exec.i": "1.3"},
                "value_domains": {"open_modes": {}},
            },
            "libraries": {
                "exec.library": {
                    "functions": {
                        "OldOpenLibrary": {"fd_version": "34"},
                        "NewGetID": {"fd_version": "39"},
                    }
                }
            },
            "structs": {"Node": {}},
            "constants": {"MEMF_CHIP": {}},
        },
    )
    _write_json(
        knowledge / "amiga_ndk_other_parsed.json",
        {
            "_meta": {},
            "functions": {
                "exec.library": {
                    "OldOpenLibrary": {"available_since": "1.2"},
                    "NewGetID": {"available_since": "3.0"},
                }
            },
        },
    )
    _write_json(
        knowledge / "amiga_hw_registers.json",
        {"registers": [{"address_68k": "0xDFF002", "bits": [{"bit": 0}]}, {"address_68k": "0xDFF004"}]},
    )
    _write_json(
        knowledge / "amiga_hw_symbols.json",
        {"registers": [{"cpu_address": "0xDFF002"}, {"cpu_address": "0xBFE001"}]},
    )
    _write_json(
        knowledge / "amiga_ndk_corrections.json",
        {"items": [{"review_status": "seeded", "citation": "doc"}, {"review_status": "validated", "citation": "review"}]},
    )
    _write_json(
        knowledge / "amiga_hunk_file.json",
        {
            "enums": {"hunk_type": {"HUNK_HEADER": 1011, "HUNK_CODE": 1001, "HUNK_END": 1010, "HUNK_OVERLAY": 1013}},
            "record_types": {"HUNK_HEADER": {}, "HUNK_CODE": {}, "HUNK_END": {}},
            "groups": {
                "section_block": {
                    "section_start_types": ["HUNK_CODE"],
                    "aux_types": [],
                    "terminator_types": ["HUNK_END"],
                }
            },
        },
    )
    (generated / "amiga_os_runtime.h").write_text('"1.3"\n"3.1"\n', encoding="utf-8")
    for name, status in (("a", "observed"), ("b", "no_os_calls"), ("c", "unknown")):
        path = targets / name
        path.mkdir()
        _write_json(path / "platform_summary.json", {"os_compatibility": {"status": status}})


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
