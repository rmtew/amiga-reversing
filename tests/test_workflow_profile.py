from __future__ import annotations

from amiga_reversing.disasm.workflow_profile import WorkflowProfile, WorkflowSpan


def test_workflow_profile_serializes_stable_span_records() -> None:
    profile = WorkflowProfile(
        "round_trip_verification",
        target_id="demo",
        input_stamp={"backend": "amiga-hunk"},
        counters={"rows": 2},
    )
    profile.spans.append(
        WorkflowSpan(
            name="direct_rebuild",
            seconds=0.1234567,
            module="c_backend",
            detail={"profile": {"direct_rebuild_exact": True}},
        )
    )

    assert profile.to_payload() == {
        "workflow_id": "round_trip_verification",
        "spans": [
            {
                "name": "direct_rebuild",
                "seconds": 0.123457,
                "module": "c_backend",
                "detail": {"profile": {"direct_rebuild_exact": True}},
            }
        ],
        "target_id": "demo",
        "input_stamp": {"backend": "amiga-hunk"},
        "counters": {"rows": 2},
    }
