from __future__ import annotations

import json
from pathlib import Path

from amiga_reversing.tools import atari_platform_kb, macos_platform_kb


def test_atari_platform_kb_report_validates_committed_markdown_sources(tmp_path: Path) -> None:
    _write_fixture_tree(tmp_path)

    report = atari_platform_kb.build_report(tmp_path)

    assert report["source_count"] == 1
    assert report["availability_counts"] == {"committed": 1}
    assert atari_platform_kb.check_report(report) == []
    text = atari_platform_kb.format_report(report)
    assert "Atari ST Platform KB" in text
    assert "markers=2/2" in text


def test_macos_platform_kb_report_uses_matching_inventory_shape(tmp_path: Path) -> None:
    _write_fixture_tree(tmp_path, inventory_name="macos_source_inventory.json")

    report = macos_platform_kb.build_report(tmp_path)

    assert report["source_count"] == 1
    assert macos_platform_kb.check_report(report) == []
    assert "Classic Mac OS Platform KB" in macos_platform_kb.format_report(report)


def test_atari_platform_kb_check_reports_bad_inventory_and_metadata(tmp_path: Path) -> None:
    _write_fixture_tree(tmp_path)
    payload = json.loads((tmp_path / "knowledge" / "atari_st_source_inventory.json").read_text(encoding="utf-8"))
    payload["sources"].append(
        {
            "id": "fixture-md",
            "path": "ext/docs_atari_st/missing.md",
            "metadata_path": "ext/docs_atari_st/fixture.source.json",
            "availability": "mystery",
            "extraction_status": "candidate",
            "review_status": "seeded",
            "decision": "cite_manually",
            "citation_quality": "line",
        }
    )
    _write_json(tmp_path / "knowledge" / "atari_st_source_inventory.json", payload)

    violations = atari_platform_kb.check_report(atari_platform_kb.build_report(tmp_path))

    assert any("duplicate ids" in violation for violation in violations)
    assert any("unknown availability" in violation for violation in violations)
    assert any("citation_quality must be page" in violation for violation in violations)
    assert any("source path missing" in violation for violation in violations)
    assert any("metadata final_md does not match inventory path" in violation for violation in violations)


def _write_fixture_tree(root: Path, *, inventory_name: str = "atari_st_source_inventory.json") -> None:
    docs = root / "ext" / "docs_atari_st"
    knowledge = root / "knowledge"
    docs.mkdir(parents=True)
    knowledge.mkdir()
    (docs / "fixture.md").write_text(
        "<!-- source-page: 1 -->\n## Page 1\n\nA\n\n<!-- source-page: 3 -->\n## Page 3\n\nB\n",
        encoding="utf-8",
    )
    _write_json(
        docs / "fixture.source.json",
        {
            "schema_version": 1,
            "source_id": "fixture-md",
            "paths": {"final_md": "ext/docs_atari_st/fixture.md"},
            "probe": {"text_pages": 2},
        },
    )
    _write_json(
        knowledge / inventory_name,
        {
            "schema_version": 1,
            "sources": [
                {
                    "id": "fixture-md",
                    "path": "ext/docs_atari_st/fixture.md",
                    "metadata_path": "ext/docs_atari_st/fixture.source.json",
                    "availability": "committed",
                    "extraction_status": "candidate",
                    "review_status": "seeded",
                    "decision": "cite_manually",
                    "citation_quality": "page",
                }
            ],
        },
    )


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
