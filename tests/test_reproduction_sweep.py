from __future__ import annotations

from pathlib import Path

from amiga_reversing.disasm.reproduction_sweep import (
    ReproductionSweepStatus,
    crash_record,
    format_reproduction_sweep_score,
    import_failure_record,
    record_from_reproduction_report,
    reproduction_sweep_summary,
    timeout_record,
)


def test_reproduction_sweep_summary_scores_and_groups_failures(tmp_path: Path) -> None:
    exact = record_from_reproduction_report(
        "ok",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "input_stamp": {},
            "diff_ranges": [],
            "issues": [],
        },
    )
    mismatch = record_from_reproduction_report(
        "bad",
        {
            "status": "binary_mismatch",
            "exact": False,
            "backend": "amiga-hunk",
            "first_diff": {"offset": 36, "original": 1, "rebuilt": 2},
            "diff_ranges": [{"start": 36, "end": 40}],
            "file_layout": [
                {
                    "kind": "section_payload",
                    "file_start": 32,
                    "file_end": 64,
                    "section_index": 0,
                }
            ],
            "issues": [{"kind": "diff"}],
        },
    )
    summary = reproduction_sweep_summary(
        [
            exact,
            mismatch,
            import_failure_record("disk import failed"),
            crash_record("boom", RuntimeError("renderer crashed")),
        ],
        limit=4,
        project_root=tmp_path,
    )

    assert summary["status_counts"] == {
        "binary_mismatch": 1,
        "crashed": 1,
        "exact": 1,
        "import_failed": 1,
    }
    assert summary["score"] == {
        "exact": 1,
        "non_exact_match": 0,
        "supported": 3,
        "total_targets": 3,
        "unsupported": 0,
        "import_failed": 1,
        "failed_supported": 2,
        "exact_supported_percent": 33.33,
        "exact_all_targets_percent": 33.33,
    }
    assert summary["failure_group_count"] == 3
    assert "1/3 supported exact" in format_reproduction_sweep_score(summary)


def test_reproduction_sweep_tracks_analysis_stamp(tmp_path: Path) -> None:
    record = record_from_reproduction_report(
        "ok",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "diff_ranges": [],
            "issues": [],
        },
    )

    summary = reproduction_sweep_summary([record], limit=1, project_root=tmp_path)

    assert record["analysis_backend"] == "facts_v2"
    assert summary["analysis_backend_counts"] == {"facts_v2": 1}


def test_reproduction_sweep_tracks_facts_v2_phase_timing(tmp_path: Path) -> None:
    fast = record_from_reproduction_report(
        "fast",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "duration_seconds": 1.0,
            "original_size": 100,
            "listing_profile": {
                "facts_v2": {
                    "decode_seconds": 0.01,
                    "seed_seconds": 0.02,
                    "fixed_point_seconds": 0.03,
                    "fixed_point_reachable_seconds": 0.011,
                    "fixed_point_reachable_decode_seconds": 0.001,
                    "fixed_point_reachable_validate_seconds": 0.002,
                    "fixed_point_reachable_accept_seconds": 0.003,
                    "fixed_point_reachable_target_seconds": 0.004,
                    "fixed_point_reachable_relocation_seconds": 0.005,
                    "fixed_point_reachable_fallthrough_seconds": 0.006,
                    "fixed_point_index_seconds": 0.002,
                    "fixed_point_required_label_conflict_seconds": 0.003,
                    "fixed_point_opcode_relocation_conflict_seconds": 0.004,
                    "fixed_point_rebuild_accepted_seconds": 0.005,
                    "fixed_point_relocation_anchor_seconds": 0.006,
                    "fixed_point_materialize_labels_seconds": 0.007,
                    "fixed_point_data_span_seconds": 0.008,
                    "fixed_point_invariant_seconds": 0.009,
                    "render_ir_seconds": 0.04,
                    "source_render_seconds": 0.05,
                    "decoded_candidates": 10,
                    "accepted_instructions": 9,
                    "queue_iterations": 11,
                    "render_ir_statements": 20,
                    "asm_source_bytes": 200,
                }
            },
        },
    )
    slow = record_from_reproduction_report(
        "slow",
        {
            "status": "exact",
            "exact": True,
            "backend": "atari-st",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "duration_seconds": 2.0,
            "original_size": 200,
            "listing_profile": {
                "facts_v2": {
                    "fixed_point_seconds": 0.5,
                    "fixed_point_reachable_seconds": 0.3,
                    "fixed_point_reachable_validate_seconds": 0.2,
                    "fixed_point_reachable_fallthrough_seconds": 0.05,
                    "fixed_point_index_seconds": 0.02,
                    "decoded_candidates": 30,
                    "accepted_instructions": 25,
                    "queue_iterations": 40,
                    "render_ir_statements": 50,
                    "asm_source_bytes": 500,
                }
            },
        },
    )

    summary = reproduction_sweep_summary([fast, slow], limit=2, project_root=tmp_path)
    facts_timing = summary["facts_v2_timing"]

    assert facts_timing["profiled_targets"] == 2
    assert facts_timing["phase_totals"]["fixed_point_seconds"] == 0.53
    assert facts_timing["phase_totals"]["fixed_point_reachable_seconds"] == 0.311
    assert facts_timing["phase_totals"]["fixed_point_reachable_validate_seconds"] == 0.202
    assert facts_timing["phase_totals"]["fixed_point_reachable_fallthrough_seconds"] == 0.056
    assert facts_timing["phase_totals"]["fixed_point_index_seconds"] == 0.022
    assert facts_timing["phase_totals"]["fixed_point_invariant_seconds"] == 0.009
    assert facts_timing["phase_totals"]["source_render_seconds"] == 0.05
    assert facts_timing["count_totals"]["decoded_candidates"] == 40
    assert facts_timing["count_totals"]["accepted_instructions"] == 34
    assert facts_timing["count_totals"]["queue_iterations"] == 51
    assert facts_timing["slowest_by_phase"]["fixed_point_seconds"][0]["target"] == "slow"
    assert facts_timing["slowest_by_phase"]["fixed_point_seconds"][0]["phase_seconds"] == 0.5


def test_reproduction_sweep_summarizes_facts_v2_direct_source_comparison(tmp_path: Path) -> None:
    matched = record_from_reproduction_report(
        "matched",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "comparison": {
                "canonical_full_file_exact": True,
                "content_exact": True,
                "payload_exact": True,
                "policy_adjusted_full_file_exact": True,
            },
            "profile": {
                "facts_v2_direct_rebuild_c_api": 1.0,
                "facts_v2_direct_source_compare": 1.0,
                "facts_v2_direct_source_match": 1.0,
                "facts_v2_direct_rebuilt_sha256": "same",
                "facts_v2_source_assembled_sha256": "same",
                "facts_v2_source_full_file_exact": 1.0,
                "facts_v2_source_content_exact": 1.0,
                "facts_v2_source_payload_exact": 1.0,
                "facts_v2_source_relocation_semantics_exact": 1.0,
                "facts_v2_source_relocation_encoding_exact": 1.0,
            },
        },
    )
    mismatched = record_from_reproduction_report(
        "mismatched",
        {
            "status": "exact",
            "exact": True,
            "backend": "atari-st",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "comparison": {
                "canonical_full_file_exact": True,
                "content_exact": True,
                "payload_exact": True,
                "policy_adjusted_full_file_exact": True,
            },
            "profile": {
                "facts_v2_direct_rebuild_c_api": 1.0,
                "facts_v2_direct_source_compare": 1.0,
                "facts_v2_direct_source_match": 0.0,
                "facts_v2_direct_source_mismatch": 1.0,
                "facts_v2_direct_rebuilt_sha256": "direct",
                "facts_v2_source_assembled_sha256": "source",
                "facts_v2_source_full_file_exact": 0.0,
                "facts_v2_source_content_exact": 1.0,
                "facts_v2_source_payload_exact": 1.0,
                "facts_v2_source_relocation_semantics_exact": 1.0,
                "facts_v2_source_relocation_encoding_exact": 0.0,
            },
        },
    )

    summary = reproduction_sweep_summary([matched, mismatched], limit=2, project_root=tmp_path)
    comparison = summary["facts_v2_direct_source_comparison"]

    assert comparison["compared_targets"] == 2
    assert comparison["matched_targets"] == 1
    assert comparison["mismatched_targets"] == 1
    assert comparison["overrode_direct_targets"] == 0
    assert comparison["fell_back_targets"] == 0
    assert comparison["source_full_file_exact_targets"] == 1
    assert comparison["source_content_compared_targets"] == 2
    assert comparison["source_content_exact_targets"] == 2
    assert comparison["source_payload_exact_targets"] == 2
    assert comparison["source_relocation_semantics_applicable_targets"] == 2
    assert comparison["source_relocation_semantics_exact_targets"] == 2
    assert comparison["source_relocation_encoding_applicable_targets"] == 2
    assert comparison["source_relocation_encoding_exact_targets"] == 1
    assert comparison["source_content_mismatch_targets"] == []
    assert comparison["first_mismatch"] == {
        "target": "mismatched",
        "status": "exact",
        "backend": "atari-st",
        "direct_sha256": "direct",
        "source_sha256": "source",
    }
    readiness = summary["facts_v2_readiness"]
    assert readiness["direct_rebuild_default_ready"] is True
    assert readiness["direct_rebuild_source_mismatched_targets"] == 1
    assert "direct_rebuild_source_mismatches" not in readiness["blockers"]
    assert "direct_rebuild_source_mismatches" not in readiness["direct_rebuild_blockers"]


def test_reproduction_sweep_facts_v2_readiness_tracks_reproduction_blockers(tmp_path: Path) -> None:
    accepted = record_from_reproduction_report(
        "accepted",
        {
            "status": "binary_mismatch",
            "exact": False,
            "backend": "amiga-hunk",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "comparison": {
                "status": "mismatch",
                "canonical_full_file_exact": False,
                "content_exact": False,
                "payload_exact": True,
                "policy_adjusted_full_file_exact": False,
                "relocation_semantics_exact": False,
                "relocation_encoding_exact": False,
                "semantic_diagnostics": [
                    {
                        "kind": "missing_relocation_group",
                        "original": {"record_id": 1004, "target_section": 1, "count": 1},
                    }
                ],
            },
            "listing_profile": {
                "facts_v2": {
                    "asm_source_enabled": True,
                    "asm_source_symbolic_instructions": 1,
                    "asm_source_lossy_numeric_hunk_relocations": 1,
                }
            },
            "profile": {
                "facts_v2_direct_rebuild_c_api": 1.0,
                "facts_v2_direct_source_compare": 1.0,
                "facts_v2_direct_source_match": 1.0,
                "facts_v2_source_full_file_exact": 1.0,
                "facts_v2_source_content_exact": 1.0,
                "facts_v2_source_payload_exact": 1.0,
            },
        },
    )

    summary = reproduction_sweep_summary([accepted], limit=1, project_root=tmp_path)
    readiness = summary["facts_v2_readiness"]

    assert readiness["analysis_path"] == "facts_v2"
    assert readiness["facts_v2_analysis_records"] == 1
    assert readiness["non_facts_v2_analysis_records"] == 0
    assert readiness["accepted_mismatch_count"] == 1
    assert readiness["accepted_mismatch_kinds"] == {"lossy_hunk_reloc32": 1}
    assert readiness["accepted_mismatch_policy_ready"] is True
    assert readiness["direct_rebuild_default_ready"] is True
    assert readiness["source_render_default_ready"] is True
    assert readiness["source_render_default_blocker"] is None
    assert readiness["source_render_default_blockers"] == []
    assert "accepted_mismatch_policy_required" not in readiness["blockers"]
    assert readiness["blockers"] == []


def test_reproduction_sweep_facts_v2_readiness_blocks_unknown_accepted_policy(
    tmp_path: Path,
) -> None:
    accepted = {
        "target": "unknown",
        "status": ReproductionSweepStatus.ACCEPTED_MISMATCH,
        "exact": False,
        "backend": "amiga-hunk",
        "analysis_backend": "facts_v2",
        "accepted_mismatch_kind": "new_policy_needed",
        "comparison": {
            "status": "mismatch",
            "canonical_full_file_exact": False,
            "content_exact": True,
            "payload_exact": True,
            "policy_adjusted_full_file_exact": True,
        },
        "profile": {
            "facts_v2_direct_source_compare": 1.0,
            "facts_v2_direct_source_match": 1.0,
        },
    }

    summary = reproduction_sweep_summary([accepted], limit=1, project_root=tmp_path)
    readiness = summary["facts_v2_readiness"]

    assert readiness["accepted_mismatch_policy_ready"] is False
    assert readiness["accepted_mismatch_policy"]["unexpected_kinds"] == ["new_policy_needed"]
    assert readiness["facts_v2_reproduction_default_ready"] is False
    assert readiness["blockers"] == ["unexpected_accepted_mismatch_policy"]


def test_reproduction_sweep_source_default_requires_all_profiles_source_enabled(tmp_path: Path) -> None:
    record = record_from_reproduction_report(
        "direct_only",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "listing_profile": {
                "facts_v2": {
                    "asm_source_enabled": False,
                    "asm_source_symbolic_instructions": 0,
                }
            },
        },
    )

    summary = reproduction_sweep_summary([record], limit=1, project_root=tmp_path)
    readiness = summary["facts_v2_readiness"]

    assert summary["facts_v2_invariant_failures"]["asm_source_enabled_targets"] == 0
    assert readiness["source_render_default_ready"] is False
    assert "asm_source_enabled_targets=0/1" in readiness["source_render_default_blockers"]


def test_reproduction_sweep_source_default_blocks_source_content_mismatch(tmp_path: Path) -> None:
    record = record_from_reproduction_report(
        "source_bad",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "listing_profile": {
                "facts_v2": {
                    "asm_source_enabled": True,
                    "asm_source_symbolic_instructions": 1,
                }
            },
            "profile": {
                "facts_v2_direct_source_compare": 1.0,
                "facts_v2_direct_source_match": 0.0,
                "facts_v2_source_content_exact": 0.0,
                "facts_v2_source_payload_exact": 0.0,
            },
        },
    )

    summary = reproduction_sweep_summary([record], limit=1, project_root=tmp_path)
    readiness = summary["facts_v2_readiness"]

    assert summary["facts_v2_direct_source_comparison"]["source_content_exact_targets"] == 0
    assert readiness["source_render_default_ready"] is False
    assert "source_content_exact_targets=0/1" in readiness["source_render_default_blockers"]


def test_reproduction_sweep_tracks_facts_v2_comparison_invariants(tmp_path: Path) -> None:
    record = record_from_reproduction_report(
        "ok",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "listing_profile": {
                "comparison": {
                    "rendered_source_sha256": "abc",
                    "facts_v2_render_ir_hash": "def",
                    "facts_v2_unresolved_labels": 2,
                    "facts_v2_interior_conflicts": 5,
                    "facts_v2_interior_conflicts_resolved_by_demote": 4,
                    "facts_v2_interior_conflicts_unresolved": 1,
                    "facts_v2_relocation_failures": 3,
                    "facts_v2_relocation_anchors": 4,
                    "facts_v2_first_relocation_anchor_kind": "negative",
                    "facts_v2_first_relocation_anchor_section": 0,
                    "facts_v2_first_relocation_anchor_offset": 46,
                    "facts_v2_first_relocation_anchor_target_section": 0,
                    "facts_v2_first_relocation_anchor_width": 4,
                    "facts_v2_first_relocation_anchor_platform_record_kind": "hunk_reloc32",
                    "facts_v2_first_relocation_anchor_raw_value": 0xFFFFFFFC,
                    "facts_v2_first_relocation_anchor_addend": -4,
                    "facts_v2_relocation_anchor_instruction_bytes": 1,
                    "facts_v2_relocation_anchor_data_payloads": 2,
                    "facts_v2_relocation_anchor_unknown_contexts": 1,
                    "facts_v2_unassemblable_hunk_data_relocations": 2,
                    "facts_v2_unassemblable_hunk_base_register_relocations": 4,
                    "facts_v2_first_relocation_anchor_context": "data_payload",
                    "facts_v2_first_relocation_anchor_instruction_offset": 0,
                    "facts_v2_first_relocation_failure_reason": "target_out_of_range",
                    "facts_v2_first_relocation_failure_section": 0,
                    "facts_v2_first_relocation_failure_offset": 46,
                    "facts_v2_first_relocation_failure_target_section": 0,
                    "facts_v2_first_relocation_failure_raw_value": 0xFFFFFFFC,
                    "facts_v2_first_relocation_failure_computed_target": 0xFFFFFFFC,
                    "facts_v2_required_instruction_failures": 6,
                    "facts_v2_unsupported_instruction_demotes": 11,
                    "facts_v2_opcode_relocation_conflicts_resolved_by_demote": 12,
                    "facts_v2_asm_source_symbolic_instructions": 10,
                    "facts_v2_asm_source_instruction_render_failures": 7,
                    "facts_v2_asm_source_instruction_byte_mismatches": 8,
                    "facts_v2_asm_source_instruction_relocation_failures": 9,
                    "facts_v2_asm_source_relocation_anchor_refusals": 3,
                    "facts_v2_asm_source_unassemblable_hunk_data_relocation_refusals": 2,
                    "facts_v2_asm_source_unassemblable_hunk_base_register_relocation_refusals": 4,
                    "facts_v2_asm_source_first_failure_kind": "unassemblable_hunk_data_relocation",
                    "facts_v2_asm_source_lossy_numeric_hunk_relocations": 6,
                    "facts_v2_asm_source_first_failure_section": 0,
                    "facts_v2_asm_source_first_failure_offset": 46,
                    "facts_v2_asm_source_first_failure_aux_offset": 0,
                    "structural_invariant_failures": [
                        "facts_v2_unresolved_labels",
                        "facts_v2_interior_conflicts_unresolved",
                        "facts_v2_relocation_failures",
                    ],
                    "source_invariant_failures": [
                        "facts_v2_asm_source_instruction_render_failures",
                        "facts_v2_asm_source_instruction_byte_mismatches",
                        "facts_v2_asm_source_instruction_relocation_failures",
                    ],
                }
            },
            "diff_ranges": [],
            "issues": [],
        },
    )

    summary = reproduction_sweep_summary([record], limit=1, project_root=tmp_path)

    assert record["analysis_comparison"]["rendered_source_sha256"] == "abc"
    assert summary["facts_v2_invariant_failures"]["profiled_targets"] == 1
    assert summary["facts_v2_invariant_failures"]["hard_failure_count"] == 14
    assert summary["facts_v2_invariant_failures"]["unaccepted_hard_failure_count"] == 14
    assert summary["facts_v2_invariant_failures"]["unresolved_labels"] == 2
    assert summary["facts_v2_invariant_failures"]["unaccepted_unresolved_labels"] == 2
    assert summary["facts_v2_invariant_failures"]["interior_conflicts"] == 5
    assert summary["facts_v2_invariant_failures"]["interior_conflicts_resolved_by_demote"] == 4
    assert summary["facts_v2_invariant_failures"]["interior_conflicts_unresolved"] == 1
    assert summary["facts_v2_invariant_failures"]["unaccepted_interior_conflicts_unresolved"] == 1
    assert summary["facts_v2_invariant_failures"]["relocation_failures"] == 3
    assert summary["facts_v2_invariant_failures"]["unaccepted_relocation_failures"] == 3
    assert summary["facts_v2_invariant_failures"]["relocation_anchors"] == 4
    assert summary["facts_v2_invariant_failures"]["relocation_anchor_instruction_bytes"] == 1
    assert (
        summary["facts_v2_invariant_failures"][
            "unaccepted_relocation_anchor_instruction_bytes"
        ]
        == 1
    )
    assert summary["facts_v2_invariant_failures"]["relocation_anchor_data_payloads"] == 2
    assert summary["facts_v2_invariant_failures"]["relocation_anchor_unknown_contexts"] == 1
    assert (
        summary["facts_v2_invariant_failures"]["unaccepted_relocation_anchor_unknown_contexts"]
        == 1
    )
    assert summary["facts_v2_invariant_failures"]["unassemblable_hunk_data_relocations"] == 2
    assert summary["facts_v2_invariant_failures"]["unassemblable_hunk_base_register_relocations"] == 4
    assert summary["facts_v2_invariant_failures"]["first_relocation_failures"] == [
        {
            "target": "ok",
            "reason": "target_out_of_range",
            "section": 0,
            "offset": 46,
            "target_section": 0,
            "raw_value": 0xFFFFFFFC,
            "computed_target": 0xFFFFFFFC,
        }
    ]
    assert summary["facts_v2_invariant_failures"]["first_relocation_anchors"] == [
        {
            "target": "ok",
            "kind": "negative",
            "section": 0,
            "offset": 46,
            "target_section": 0,
            "record_kind": "hunk_reloc32",
            "raw_value": 0xFFFFFFFC,
            "addend": -4,
            "context": "data_payload",
            "instruction_offset": 0,
        }
    ]
    assert summary["facts_v2_invariant_failures"]["required_instruction_failures"] == 6
    assert summary["facts_v2_invariant_failures"]["unaccepted_required_instruction_failures"] == 6
    assert summary["facts_v2_invariant_failures"]["unsupported_instruction_demotes"] == 11
    assert summary["facts_v2_invariant_failures"]["opcode_relocation_conflicts_resolved_by_demote"] == 12
    assert summary["facts_v2_invariant_failures"]["affected_targets"] == ["ok"]
    assert summary["facts_v2_invariant_failures"]["unaccepted_affected_targets"] == ["ok"]
    assert summary["facts_v2_invariant_failures"]["accepted_invariant_targets"] == []
    assert summary["facts_v2_invariant_failures"]["source_failure_count"] == 27
    assert summary["facts_v2_invariant_failures"]["unaccepted_source_failure_count"] == 27
    assert summary["facts_v2_invariant_failures"]["asm_source_symbolic_instructions"] == 10
    assert summary["facts_v2_invariant_failures"]["asm_source_lossy_numeric_hunk_relocations"] == 6
    assert summary["facts_v2_invariant_failures"]["asm_source_instruction_render_failures"] == 7
    assert (
        summary["facts_v2_invariant_failures"][
            "unaccepted_asm_source_instruction_render_failures"
        ]
        == 7
    )
    assert summary["facts_v2_invariant_failures"]["asm_source_instruction_byte_mismatches"] == 8
    assert (
        summary["facts_v2_invariant_failures"][
            "unaccepted_asm_source_instruction_byte_mismatches"
        ]
        == 8
    )
    assert summary["facts_v2_invariant_failures"]["asm_source_instruction_relocation_failures"] == 9
    assert (
        summary["facts_v2_invariant_failures"][
            "unaccepted_asm_source_instruction_relocation_failures"
        ]
        == 9
    )
    assert summary["facts_v2_invariant_failures"]["asm_source_relocation_anchor_refusals"] == 3
    assert (
        summary["facts_v2_invariant_failures"][
            "unaccepted_asm_source_relocation_anchor_refusals"
        ]
        == 3
    )
    assert (
        summary["facts_v2_invariant_failures"][
            "asm_source_unassemblable_hunk_data_relocation_refusals"
        ]
        == 2
    )
    assert (
        summary["facts_v2_invariant_failures"][
            "asm_source_unassemblable_hunk_base_register_relocation_refusals"
        ]
        == 4
    )
    assert summary["facts_v2_invariant_failures"]["source_affected_targets"] == ["ok"]
    assert summary["facts_v2_invariant_failures"]["unaccepted_source_affected_targets"] == ["ok"]
    assert summary["facts_v2_invariant_failures"]["first_source_failures"] == [
        {
            "target": "ok",
            "kind": "unassemblable_hunk_data_relocation",
            "section": 0,
            "offset": 46,
            "aux_offset": 0,
        }
    ]
    assert summary["facts_v2_invariant_failures"]["source_failure_signatures"] == [
        {
            "count": 27,
            "target_count": 1,
            "kind": "unassemblable_hunk_data_relocation",
            "anchor_kind": "negative",
            "anchor_context": "data_payload",
            "target_section": 0,
            "record_kind": "hunk_reloc32",
            "width": 4,
            "raw_value": 0xFFFFFFFC,
            "addend": -4,
            "first_target": "ok",
            "first_section": 0,
            "first_offset": 46,
            "first_aux_offset": 0,
        }
    ]


def test_reproduction_sweep_tracks_non_exact_content_matches(tmp_path: Path) -> None:
    content_match = record_from_reproduction_report(
        "content",
        {
            "status": "content_match",
            "exact": False,
            "backend": "amiga-hunk",
            "input_stamp": {},
            "comparison": {"status": "content_match", "failure_kinds": ["header_shape_mismatch"]},
            "diff_ranges": [],
            "issues": [],
        },
    )

    summary = reproduction_sweep_summary([content_match], limit=1, project_root=tmp_path)

    assert summary["score"]["exact"] == 0
    assert summary["score"]["non_exact_match"] == 1
    assert summary["failure_group_count"] == 0
    assert summary["accepted_mismatch_kinds"] == {}


def test_reproduction_sweep_accepts_lossy_hunk_reloc32_mismatch(tmp_path: Path) -> None:
    accepted = record_from_reproduction_report(
        "lossy",
        {
            "status": "binary_mismatch",
            "exact": False,
            "backend": "amiga-hunk",
            "comparison": {
                "status": "mismatch",
                "canonical_full_file_exact": False,
                "content_exact": False,
                "payload_exact": True,
                "policy_adjusted_full_file_exact": False,
                "relocation_semantics_exact": False,
                "relocation_encoding_exact": False,
                "failure_kinds": ["relocation_semantic_mismatch"],
                "semantic_diagnostics": [
                    {
                        "kind": "missing_relocation_group",
                        "section_index": 0,
                        "original": {
                            "record_id": 1004,
                            "target_section": 1,
                            "short_counts": False,
                            "count": 1,
                            "offsets": [514],
                        },
                    }
                ],
            },
            "listing_profile": {
                "facts_v2": {"asm_source_lossy_numeric_hunk_relocations": 1}
            },
            "diff_ranges": [],
            "issues": [],
        },
    )

    summary = reproduction_sweep_summary([accepted], limit=1, project_root=tmp_path)
    exactness = summary["reproduction_exactness"]

    assert accepted["status"] == "accepted_mismatch"
    assert accepted["accepted_mismatch_kind"] == "lossy_hunk_reloc32"
    assert summary["accepted_mismatch_kinds"] == {"lossy_hunk_reloc32": 1}
    assert summary["score"]["exact"] == 0
    assert summary["score"]["non_exact_match"] == 1
    assert summary["failure_group_count"] == 0
    assert exactness["accepted_mismatch"] == 1
    assert exactness["accepted_content_or_lossy"] == 1
    assert exactness["accepted_adjusted_or_lossy"] == 1
    assert exactness["content_mismatch_targets"] == []
    assert exactness["policy_adjusted_mismatch_targets"] == []


def test_reproduction_sweep_preserves_reported_accepted_mismatch_kind(tmp_path: Path) -> None:
    accepted = record_from_reproduction_report(
        "lossy-direct",
        {
            "status": "accepted_mismatch",
            "exact": False,
            "backend": "amiga-hunk",
            "accepted_mismatch_kind": "lossy_hunk_reloc32",
            "accepted_mismatch_reason": "facts_v2 direct rebuild refused: lossy_numeric_hunk_relocations",
            "listing_profile": {"facts_v2": {"unassemblable_hunk_data_relocations": 1}},
            "issues": [],
        },
    )

    summary = reproduction_sweep_summary([accepted], limit=1, project_root=tmp_path)

    assert accepted["accepted_mismatch_kind"] == "lossy_hunk_reloc32"
    assert summary["accepted_mismatch_kinds"] == {"lossy_hunk_reloc32": 1}
    assert summary["failure_group_count"] == 0


def test_reproduction_sweep_accepts_atari_target_out_of_range_source_refusal(
    tmp_path: Path,
) -> None:
    exact = record_from_reproduction_report(
        "ok",
        {
            "status": "exact",
            "exact": True,
            "backend": "atari-st",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "comparison": {
                "status": "exact_file",
                "canonical_full_file_exact": True,
                "content_exact": True,
                "payload_exact": True,
                "policy_adjusted_full_file_exact": True,
                "relocation_semantics_exact": True,
                "relocation_encoding_exact": True,
                "failure_kinds": [],
            },
        },
    )
    accepted = record_from_reproduction_report(
        "bad_atari",
        {
            "status": "render_error",
            "exact": False,
            "backend": "atari-st",
            "input_stamp": {"analysis_backend": "facts_v2"},
            "tool_error": (
                "facts_v2 asm source refused relocation_reason=target_out_of_range "
                "section=0 offset=6 target_section=0 raw_value=1411631616 "
                "computed_target=1411631616"
            ),
            "listing_profile": {
                "facts_v2": {
                    "asm_source_refused": True,
                    "first_relocation_failure_reason": "target_out_of_range",
                    "relocation_failures": 153,
                }
            },
            "diff_ranges": [],
            "issues": [],
        },
    )

    summary = reproduction_sweep_summary([exact, accepted], limit=2, project_root=tmp_path)
    exactness = summary["reproduction_exactness"]

    assert accepted["status"] == "accepted_mismatch"
    assert accepted["accepted_mismatch_kind"] == "atari_relocation_target_out_of_range"
    assert summary["status_counts"] == {"accepted_mismatch": 1, "exact": 1}
    assert summary["accepted_mismatch_kinds"] == {"atari_relocation_target_out_of_range": 1}
    assert summary["score"]["exact"] == 1
    assert summary["score"]["non_exact_match"] == 1
    assert summary["failure_group_count"] == 0
    assert exactness["comparison_targets"] == 1
    assert exactness["missing_comparison_targets"] == 0
    assert exactness["accepted_mismatch"] == 1
    assert exactness["accepted_no_comparison"] == 1
    assert exactness["accepted_content_or_lossy"] == 1
    assert exactness["accepted_adjusted_or_lossy"] == 1
    assert summary["facts_v2_invariant_failures"]["hard_failure_count"] == 153
    assert summary["facts_v2_invariant_failures"]["unaccepted_hard_failure_count"] == 0
    assert summary["facts_v2_invariant_failures"]["relocation_failures"] == 153
    assert summary["facts_v2_invariant_failures"]["unaccepted_relocation_failures"] == 0
    assert summary["facts_v2_invariant_failures"]["affected_targets"] == ["bad_atari"]
    assert summary["facts_v2_invariant_failures"]["unaccepted_affected_targets"] == []
    assert summary["facts_v2_invariant_failures"]["accepted_invariant_targets"] == [
        {
            "target": "bad_atari",
            "accepted_mismatch_kind": "atari_relocation_target_out_of_range",
            "hard_failure_count": 153,
            "source_failure_count": 0,
        }
    ]


def test_reproduction_sweep_splits_canonical_content_and_adjusted_exactness(tmp_path: Path) -> None:
    canonical = record_from_reproduction_report(
        "canonical",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "comparison": {
                "status": "exact_file",
                "canonical_full_file_exact": True,
                "content_exact": True,
                "payload_exact": True,
                "policy_adjusted_full_file_exact": True,
                "relocation_semantics_exact": True,
                "relocation_encoding_exact": True,
                "failure_kinds": [],
            },
        },
    )
    adjusted_only = record_from_reproduction_report(
        "adjusted",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "comparison": {
                "status": "container_shape_mismatch",
                "canonical_full_file_exact": False,
                "content_exact": True,
                "payload_exact": True,
                "policy_adjusted_full_file_exact": True,
                "relocation_semantics_exact": True,
                "relocation_encoding_exact": False,
                "failure_kinds": ["header_shape_mismatch"],
            },
        },
    )
    mismatch = record_from_reproduction_report(
        "mismatch",
        {
            "status": "binary_mismatch",
            "exact": False,
            "backend": "amiga-hunk",
            "comparison": {
                "status": "mismatch",
                "canonical_full_file_exact": False,
                "content_exact": False,
                "payload_exact": False,
                "policy_adjusted_full_file_exact": False,
                "relocation_semantics_exact": False,
                "relocation_encoding_exact": False,
                "failure_kinds": ["payload_mismatch"],
            },
        },
    )

    summary = reproduction_sweep_summary([canonical, adjusted_only, mismatch], limit=3, project_root=tmp_path)
    exactness = summary["reproduction_exactness"]

    assert exactness["comparison_targets"] == 3
    assert exactness["status_exact"] == 2
    assert exactness["canonical_full_file_exact"] == 1
    assert exactness["content_exact"] == 2
    assert exactness["payload_exact"] == 2
    assert exactness["policy_adjusted_full_file_exact"] == 2
    assert exactness["policy_adjusted_only_exact"] == 1
    assert exactness["content_only_exact"] == 1
    assert exactness["canonical_mismatch_targets"] == ["adjusted", "mismatch"]
    assert exactness["content_mismatch_targets"] == ["mismatch"]
    assert exactness["policy_adjusted_mismatch_targets"] == ["mismatch"]
    assert "Canonical/content/adjusted: 1/2/2 of 3" in format_reproduction_sweep_score(summary)


def test_reproduction_sweep_summary_includes_timing_and_timeout(tmp_path: Path) -> None:
    exact = record_from_reproduction_report(
        "ok",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
        },
    )
    exact["duration_seconds"] = 1.5
    exact["worker_timings"] = {"analysis_seconds": 0.5, "reproduction_seconds": 1.0}
    exact["row_count"] = 42
    timed_out = timeout_record("slow", 3)
    timed_out["duration_seconds"] = 3.1

    summary = reproduction_sweep_summary([exact, timed_out], limit=2, project_root=tmp_path)

    assert summary["status_counts"] == {"exact": 1, "timeout": 1}
    assert summary["failure_group_count"] == 1
    assert summary["timing"] == {
        "timed_targets": 2,
        "total_seconds": 4.6,
        "max_seconds": 3.1,
        "average_seconds": 2.3,
        "slowest_targets": [
            {
                "target": "slow",
                "status": "timeout",
                "duration_seconds": 3.1,
                "analysis_seconds": None,
                "reproduction_seconds": None,
                "timeout_phase": "unknown",
                "row_count": None,
            },
            {
                "target": "ok",
                "status": "exact",
                "duration_seconds": 1.5,
                "analysis_seconds": 0.5,
                "reproduction_seconds": 1.0,
                "timeout_phase": None,
                "row_count": 42,
            },
        ],
    }
    assert summary["timeout_by_phase"] == {"unknown": 1}
    assert summary["slowest_by_phase"]["unknown"][0]["target"] == "slow"


def test_reproduction_sweep_summarizes_assembler_profile(tmp_path: Path) -> None:
    first = record_from_reproduction_report(
        "first",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
            "duration_seconds": 1.0,
            "profile": {
                "assemble_seconds": 0.7,
                "assembler_total_seconds": 0.6,
                "assembler_parse_layout_seconds": 0.4,
                "assembler_emit_object_seconds": 0.1,
                "assembler_write_file_seconds": 0.05,
                "assembler_read_output_seconds": 0.05,
                "assembler_source_bytes": 1000,
                "assembler_rebuilt_bytes": 200,
            },
        },
    )
    second = record_from_reproduction_report(
        "second",
        {
            "status": "exact",
            "exact": True,
            "backend": "atari-st",
            "duration_seconds": 2.0,
            "profile": {
                "assemble_seconds": 1.2,
                "assembler_total_seconds": 1.1,
                "assembler_parse_layout_seconds": 0.8,
                "assembler_emit_object_seconds": 0.2,
                "assembler_source_bytes": 3000,
                "assembler_rebuilt_bytes": 400,
            },
        },
    )

    summary = reproduction_sweep_summary([first, second], limit=2, project_root=tmp_path)
    timing = summary["assembler_timing"]

    assert timing["profiled_targets"] == 2
    assert timing["phase_totals"]["assemble_seconds"] == 1.9
    assert timing["phase_totals"]["assembler_parse_layout_seconds"] == 1.2
    assert timing["count_totals"]["assembler_source_bytes"] == 4000
    assert timing["count_totals"]["assembler_rebuilt_bytes"] == 600
    assert timing["slowest_by_phase"]["assembler_total_seconds"][0]["target"] == "second"


def test_reproduction_sweep_timeout_record_uses_progress_phase(tmp_path: Path) -> None:
    timed_out = timeout_record(
        "slow",
        2,
        progress={"phase": "assemble", "backend": "amiga-hunk", "row_count": 10, "original_size": 4096},
        duration_seconds=2.1,
    )

    summary = reproduction_sweep_summary([timed_out], limit=1, project_root=tmp_path)

    assert timed_out["timeout_phase"] == "assemble"
    assert timed_out["backend"] == "amiga-hunk"
    assert timed_out["row_count"] == 10
    assert timed_out["original_size"] == 4096
    assert summary["timeout_by_phase"] == {"assemble": 1}
    assert summary["failure_groups"][0]["signature"] == "assemble"


def test_reproduction_sweep_summarizes_c_backend_profile(tmp_path: Path) -> None:
    profiled = record_from_reproduction_report(
        "profiled",
        {
            "status": "exact",
            "exact": True,
            "backend": "amiga-hunk",
        },
    )
    profiled["duration_seconds"] = 3.0
    profiled["row_count"] = 100
    profiled["original_size"] = 4096
    profiled["listing_profile"] = {
        "timing": {
            "policy_seconds": 0.1,
            "analysis_seconds": 1.5,
            "decode_seconds": 0.4,
            "fixed_point_seconds": 0.8,
            "render_ir_seconds": 0.2,
            "rows_json_seconds": 0.2,
        },
        "sections": [
            {
                "section_index": 0,
                "name": "code",
                "size": 2048,
                "render_ir_seconds": 1.1,
                "source_render_seconds": 0.3,
            },
            {
                "section_index": 1,
                "name": "data",
                "size": 1024,
                "timing": {
                    "fixed_point_data_span_seconds": 0.4,
                },
            },
        ],
    }

    summary = reproduction_sweep_summary([profiled], limit=1, project_root=tmp_path)
    c_timing = summary["c_backend_timing"]

    assert c_timing["profiled_targets"] == 1
    assert c_timing["top_level_totals"]["analysis_seconds"] == 1.5
    assert c_timing["top_level_totals"]["decode_seconds"] == 0.4
    assert c_timing["top_level_totals"]["fixed_point_seconds"] == 0.8
    assert c_timing["section_phase_totals"]["render_ir_seconds"] == 1.1
    assert c_timing["section_phase_totals"]["source_render_seconds"] == 0.3
    assert c_timing["slowest_top_level"]["analysis_seconds"][0]["target"] == "profiled"
    assert c_timing["slowest_sections"][0] == {
        "target": "profiled",
        "status": "exact",
        "backend": "amiga-hunk",
        "section_index": 0,
        "section_name": "code",
        "section_size": 2048,
        "phase": "render_ir_seconds",
        "phase_seconds": 1.1,
        "duration_seconds": 3.0,
        "row_count": 100,
    }


def test_reproduction_sweep_record_captures_assembler_signature() -> None:
    record = record_from_reproduction_report(
        "asm",
        {
            "status": "assembler_error",
            "exact": False,
            "backend": "atari-st",
            "assembler_diagnostics": [{"kind": "assembler", "message": "Unknown symbol _Foo"}],
            "issues": [{"kind": "assembler"}],
        },
    )

    assert record["assembler_error_signature"] == "Unknown symbol _Foo"
    assert record["issue_counts"] == {"assembler": 1}
