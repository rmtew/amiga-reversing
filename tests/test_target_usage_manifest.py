from src.scripts.target_usage_manifest import FeatureBag, _add_analysis_features, _analysis_xrefs


def test_runtime_copied_entry_stub_feature_and_xref() -> None:
    analysis = {
        "sections": [
            {
                "section_index": 0,
                "runtime_views": [
                    {
                        "storage_address": 0x52,
                        "storage_offset": 0x52,
                        "runtime_address": 0x100,
                        "kind": 2,
                    },
                    {
                        "storage_address": 0x5C,
                        "storage_offset": 0x5C,
                        "runtime_address": 0x5BFF0,
                        "kind": 2,
                    },
                ],
            }
        ]
    }
    bag = FeatureBag()
    _add_analysis_features(analysis, bag)
    counts, _examples, tags = bag.row_features()

    assert counts["runtime:copied_code"] == 2
    assert counts["runtime:copied_entry_stub"] == 1
    assert "runtime:copied_entry_stub" in tags

    row = {"id": "fixture", "platform": "amiga-hunk", "source_id": "fixture", "origin": {}}
    row_locations = {(0, 0x52): (7, "s0:00000052:instruction:7", "subq.l #1,d7")}
    xrefs = _analysis_xrefs(row, analysis, row_locations)

    copied_entry_xrefs = [xref for xref in xrefs if xref["feature"] == "runtime:copied_entry_stub"]
    assert len(copied_entry_xrefs) == 1
    assert copied_entry_xrefs[0]["offset"] == 0x52
    assert copied_entry_xrefs[0]["value"] == 0x100
