"""Operation contracts with real action/decision histories and a bounded fact provider."""

from __future__ import annotations

import base64
import json
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import restoration
from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.decision_journal import (
    project_decision_journal,
    read_decision_journal,
)
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_action,
    load_manual_projection,
)


@pytest.fixture
def target(tmp_path, monkeypatch):
    directory = tmp_path / "target"
    directory.mkdir()
    binary = directory / "binary.bin"
    binary.write_bytes(bytes.fromhex("4e714e75"))
    (directory / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": str(binary),
                "load_address": 0,
                "entrypoint": 0,
                "code_start_offset": 0,
            }
        )
    )
    source = resolve_target_binary_source(directory, project_root=tmp_path)
    paths = SimpleNamespace(target_dir=directory, binary_source=source)
    calls = []
    native_symbols = [
        {"name": name, "section_index": 0, "source_offset": i * 2}
        for i, name in enumerate(("start", "return"))
    ]

    class Artifact:
        def query_payload(self, **query):
            calls.append(query)
            values = native_symbols
            offset, limit = query["offset"], query["limit"]
            return {
                "items": values[offset : offset + limit],
                "offset": offset,
                "limit": limit,
                "total": len(values),
                "has_more": offset + limit < len(values),
                "provenance": "native_test_facts",
                "unknowns": [],
            }

        def row_for_source_offset(self, *, section_index, offset):
            return (
                {"stable_key": "s0:00000000:instruction"}
                if (section_index, offset) == (0, 0)
                else None
            )

    artifact = Artifact()
    backend = SimpleNamespace(
        PROJECT_ROOT=tmp_path,
        resolve_project_paths=lambda *a, **k: paths,
        _project_listing_cache_key=lambda _: "native-revision-1",
        _LISTING_PROJECTION_SERVICE=SimpleNamespace(valid_artifact=lambda *a: artifact),
        _clear_project_listing_cache=lambda *a, **k: None,
    )
    monkeypatch.setattr(restoration, "_server", lambda: backend)

    def add(*, interpretation=False, name="start", subject=...):
        payload = {
            "label": {
                "label_id": name,
                "name": name,
                "hunk": 0,
                "addr": 0,
                "scope": "global",
            }
        }
        if interpretation:
            payload["interpretation"] = {
                "source_evidence_status": "hypothesis",
                "reason": "Native entry fact",
                "evidence_refs": ["s0:00000000:instruction"],
            }
            if subject is not ...:
                payload["interpretation"]["subject"] = subject
        return append_manual_action(
            directory,
            kind=ManualActionKind.CREATE_MANUAL_LABEL,
            payload=payload,
            binary_source=source,
        )

    return SimpleNamespace(
        directory=directory,
        source=source,
        backend=backend,
        add=add,
        calls=calls,
        native_symbols=native_symbols,
    )


def invoke(operation, **body):
    return restoration.execute("test", {"operation": operation, **body})


def current():
    return invoke("state")["revision"]


def test_gap_source_filter_overlaps_native_ranges_before_paging(target):
    items = [dict(item_id='before', hunk=0, start=0, end=4),
             dict(item_id='left', hunk=0, start=4, end=8),
             dict(item_id='right', hunk=0, start=8, end=12),
             dict(item_id='after', hunk=0, start=12, end=16),
             dict(item_id='other-section', hunk=1, start=4, end=12),
             dict(item_id='unlocated'), dict(item_id='empty', hunk=0, start=6, end=6)]
    target.backend._cached_analysis_review_items = lambda *args: tuple(items)
    first = invoke('query', kind='gaps', section_index=0, source_offset=6, end_offset=10, limit=1)
    assert first['total'] == 2 and first['items'][0]['item_id'] == 'left'
    second = invoke('query', kind='gaps', section_index=0, source_offset=6, end_offset=10,
                    limit=1, cursor=first['next_cursor'])
    assert second['items'][0]['item_id'] == 'right' and second['next_cursor'] is None
    point = invoke('query', kind='gaps', section_index=0, source_offset=8)
    assert [item['item_id'] for item in point['items']] == ['right']
    assert invoke('query', kind='gaps', section_index=0, source_offset=16)['total'] == 0
    assert invoke('query', kind='gaps', section_index=1)['items'][0]['item_id'] == 'other-section'
    assert invoke('query', kind='gaps')['total'] == len(items)
    assert target.calls == []  # The cached native review projection is reused.
    with pytest.raises(ValueError, match='stale_cursor'):
        invoke('query', kind='gaps', section_index=0, source_offset=7, end_offset=10,
               cursor=first['next_cursor'])


@pytest.mark.parametrize('extra', [dict(end_offset=4), dict(source_offset=4, end_offset=4),
                                  dict(source_offset=8, end_offset=4), dict(symbol='pointer'),
                                  dict(field_offset=4), dict(struct_name='Record'),
                                  dict(direction='incoming'), dict(relation='callers')])
def test_gap_query_refuses_unsupported_filters_and_invalid_ranges(target, extra):
    with pytest.raises(ValueError, match='gaps supports only|gap end_offset requires'):
        invoke('query', kind='gaps', **extra)
    assert target.calls == []


def test_field_gap_query_forwards_native_filters_and_revision_cursor(target):
    first = invoke('query', kind='field_gaps', struct_name='Record', field_offset=8, limit=1)
    assert target.calls[-1]['kind'] == 'field_gaps'
    assert target.calls[-1]['struct_name'] == 'Record' and target.calls[-1]['field_offset'] == 8
    second = invoke('query', kind='field_gaps', struct_name='Record', field_offset=8,
                    limit=1, cursor=first['next_cursor'])
    assert len(second['items']) == 1 and second['next_cursor'] is None
    with pytest.raises(ValueError, match='stale_cursor'):
        invoke('query', kind='field_gaps', struct_name='Other', field_offset=8,
               cursor=first['next_cursor'])
    with pytest.raises(ValueError, match='query text is unsupported'):
        invoke('query', kind='field_gaps', query='zero')
    for extra in ({'symbol': 'Record'}, {'direction': 'incoming'}):
        with pytest.raises(ValueError, match='field_gaps supports source coordinates'):
            invoke('query', kind='field_gaps', **extra)


def test_memory_layout_query_preserves_non_export_verdict(target, monkeypatch):
    artifact = target.backend._LISTING_PROJECTION_SERVICE.valid_artifact()
    item = {"layout_id": "diagnostic", "status": "placement_valid", "export_ready": False}
    monkeypatch.setattr(artifact, "memory_layouts_payload", lambda: {
        "items": [item], "total": 1, "scope": "canonical_fixed_layout_placement_only"}, raising=False)
    page = invoke("query", kind="memory_layouts")
    assert page["items"] == [item]
    with pytest.raises(ValueError, match="only pagination"):
        invoke("query", kind="memory_layouts", query="ignored")


def test_typed_pointer_query_uses_revision_bound_cursor_and_rejects_ignored_filters(target, monkeypatch):
    from amiga_reversing.disasm import effective_metadata
    from amiga_reversing.disasm.target_metadata import (
        SeededEntityMetadata,
        TargetMetadata,
        TargetMetadataReviewStatus,
        TargetMetadataSeedOrigin,
    )
    fields = tuple(SeededEntityMetadata(
        addr=addr, end=addr + 4, struct_name="Record", field_name="pointer",
        value_kind="target_pointer", seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED, citation="test",
    ) for addr in (0, 4))
    metadata = TargetMetadata(target_type="raw", entry_register_seeds=(), seeded_entities=fields)
    original_effective = effective_metadata.effective_target_metadata
    monkeypatch.setattr(effective_metadata, "effective_target_metadata", lambda _: metadata)
    first = invoke("query", kind="typed_pointers", struct_name="Record", limit=1)
    assert first["total"] == 2 and first["items"][0]["source_offset"] == 0
    second = invoke("query", kind="typed_pointers", struct_name="Record", limit=1,
                    cursor=first["next_cursor"])
    assert second["items"][0]["source_offset"] == 4 and not second["has_more"]
    ranged = invoke("query", kind="typed_pointers", struct_name="Record", section_index=0,
                    source_offset=4, end_offset=8, limit=1)
    assert ranged['total'] == ranged['population_total'] == 1
    assert ranged['items'][0]['source_offset'] == 4
    with pytest.raises(ValueError, match='stale_cursor'):
        invoke("query", kind="typed_pointers", struct_name="Record", section_index=0,
               source_offset=4, end_offset=8, limit=1, cursor=first['next_cursor'])
    monkeypatch.setattr(effective_metadata, "effective_target_metadata", original_effective)
    target.add()
    with pytest.raises(ValueError, match="stale_cursor"):
        invoke("query", kind="typed_pointers", struct_name="Record", limit=1,
               cursor=first["next_cursor"])
    with pytest.raises(ValueError, match="requires section_index"):
        invoke("query", kind="typed_pointers", source_offset=0)
    with pytest.raises(ValueError, match="supports only"):
        invoke("query", kind="typed_pointers", query='ignored')


def test_reads_preserve_legacy_annotations_and_unknown_fields(target):
    target.add()
    path = target.directory / "manual_actions.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    records[1]["future_annotation"] = {"user": "keep exactly"}
    raw = ("\n".join(json.dumps(r, indent=None) for r in records) + "\n").encode()
    path.write_bytes(raw)
    state = invoke("state")
    page = invoke("query", kind="symbols", expected_revision=state["revision"], limit=1)
    history = invoke("history")
    assert page["items"][0]["name"] == "start"
    assert history["items"][0]["status"] == "unassessed"
    assert path.read_bytes() == raw
    assert state["history_summary"]["unassessed"] == 1


def test_stale_revision_blocks_reads_and_writes_without_changes(target):
    old = current()
    target.add()
    raw = (target.directory / "manual_actions.jsonl").read_bytes()
    for operation in ("query", "interpret", "rollback", "review"):
        with pytest.raises(ValueError, match="stale_revision"):
            invoke(operation, expected_revision=old, kind="symbols")
    assert (target.directory / "manual_actions.jsonl").read_bytes() == raw


@pytest.mark.parametrize("operation", ["query", "history"])
@pytest.mark.parametrize("offset", [0, 1, 2650])
def test_pagination_rejects_ignored_offset_without_reading_native_facts(target, operation, offset):
    body = {"kind": "fields"} if operation == "query" else {}
    with pytest.raises(ValueError, match="offset is not supported; use the returned next_cursor"):
        invoke(operation, offset=offset, **body)
    assert not target.calls


def test_cursor_pages_are_bound_to_filters_and_revision(target):
    first = invoke("query", kind="symbols", limit=1)
    second = invoke("query", kind="symbols", limit=1, cursor=first["next_cursor"])
    assert second["items"][0]["name"] == "return"
    assert second["next_cursor"] is None
    with pytest.raises(ValueError, match="stale_cursor"):
        invoke("query", kind="references", limit=1, cursor=first["next_cursor"])
    target.add()
    with pytest.raises(ValueError, match="stale_cursor"):
        invoke("query", kind="symbols", limit=1, cursor=first["next_cursor"])
    assert len(target.calls) == 2


@pytest.mark.parametrize("limit", [0, -1, 101, True, "5", 1.5])
def test_limits_reject_before_native_query(target, limit):
    with pytest.raises(ValueError, match="limit"):
        invoke("query", kind="symbols", limit=limit)
    assert target.calls == []


@pytest.mark.parametrize(
    "cursor",
    [
        "!",
        "not-base64",
        base64.urlsafe_b64encode(b"[]").decode(),
        base64.urlsafe_b64encode(b"null").decode(),
        123,
    ],
)
def test_malformed_cursor_is_a_domain_error(target, cursor):
    with pytest.raises(ValueError, match="cursor"):
        invoke("query", kind="symbols", cursor=cursor)
    assert target.calls == []


def test_review_requires_current_exact_verification_receipt(target, monkeypatch):
    from amiga_reversing.disasm import restoration_verification

    action = target.add(interpretation=True)
    subject = invoke("state")["subject_revision"]
    for receipt in (
        {"kind": "verification", "subject_revision": "old", "exact": True},
        {"kind": "verification", "subject_revision": subject, "exact": False},
        {"kind": "probe", "subject_revision": subject, "exact": True},
    ):
        monkeypatch.setattr(
            restoration_verification, "load_receipt", lambda *_, r=receipt: r
        )
        with pytest.raises(ValueError, match="verification|rebuild"):
            invoke(
                "review",
                expected_revision=current(),
                action_id=action["action_id"],
                decision="accept",
                reason="Encoding verified",
                verification_id="receipt",
            )
    assert not (target.directory / "decision_journal.jsonl").exists()


def test_review_supersession_and_undo_redo_preserve_canonical_history(
    target, monkeypatch
):
    from amiga_reversing.disasm import restoration_verification

    action = target.add(interpretation=True)
    subject = invoke("state")["subject_revision"]
    monkeypatch.setattr(
        restoration_verification,
        "load_receipt",
        lambda *_: {"kind": "verification", "subject_revision": subject, "exact": True},
    )
    invoke(
        "review",
        expected_revision=current(),
        action_id=action["action_id"],
        decision="accept",
        reason="Entry supported and exact",
        verification_id="receipt",
    )
    assert invoke("history")["items"][0]["status"] == "accepted"
    invoke(
        "review",
        expected_revision=current(),
        action_id=action["action_id"],
        decision="defer",
        reason="More evidence needed",
    )
    assert invoke("history")["items"][0]["status"] == "deferred"
    journal = read_decision_journal(target.directory)
    canonical = project_decision_journal(journal["records"])
    assert journal["valid"] is True
    assert canonical["accepted_facts"] == []
    assert len(canonical["deferred_facts"]) == 1
    assert any(r["action"] == "supersede_decision" for r in journal["records"])

    invoke("rollback", expected_revision=current(), action_id=action["action_id"])
    assert (
        load_manual_projection(target.directory, binary_source=target.source).labels
        == ()
    )
    original = next(
        i for i in invoke("history")["items"] if i["action_id"] == action["action_id"]
    )
    assert original["active"] is False
    invoke(
        "rollback",
        expected_revision=current(),
        action_id=action["action_id"],
        redo=True,
    )
    assert (
        load_manual_projection(target.directory, binary_source=target.source).labels[0][
            "name"
        ]
        == "start"
    )
    original = next(
        i for i in invoke("history")["items"] if i["action_id"] == action["action_id"]
    )
    assert original["active"] is True
    assert original["status"] == "deferred"
    assert original["verification_current"] is False


def test_interpretation_uses_catalog_payload_and_retains_evidence(target):
    from amiga_reversing.disasm.manual_action_catalog import (
        listing_catalog_manual_payload,
    )

    def execute_command(_target, body):
        # Exercise the real command-to-action conversion and durable action path;
        # the test provider substitutes only HTTP/listing context resolution.
        row = {
            "kind": "label",
            "row_index": 0,
            "section_index": 0,
            "start_offset": 0,
            "end_offset": 0,
            "addr": 0,
            "label": "loc_0_00000000",
            "stable_key": "s0:00000000:label",
        }
        kind, payload = listing_catalog_manual_payload(
            row,
            "label.rename",
            element_context={
                "kind": "element",
                "element_kind": "label",
                "symbol": "loc_0_00000000",
            },
            parameters=body["parameters"],
        )
        action = append_manual_action(
            target.directory,
            kind=ManualActionKind(kind),
            payload={**payload, "interpretation": body["interpretation"]},
            binary_source=target.source,
        )
        return {"action": action}

    target.backend._execute_command_unchecked = execute_command
    result = invoke(
        "interpret",
        expected_revision=current(),
        command_id="label.rename",
        parameters={"name": "entry"},
        evidence={
            "reason": "Section entry supported by native analysis",
            "confidence": "high",
            "evidence_refs": ["s0:00000000:instruction"],
        },
    )
    assert result["action"]["label"]["name"] == "entry"
    history = invoke("history")["items"][0]
    assert history["status"] == "hypothesis"
    assert history["interpretation"]["confidence"] == "high"
    assert (
        load_manual_projection(target.directory, binary_source=target.source).labels[0][
            "name"
        ]
        == "entry"
    )


@pytest.mark.parametrize(
    "evidence",
    [
        {"reason": "Guess", "evidence_refs": []},
        {"reason": "Guess", "evidence_refs": ["s0:00000004:instruction"]},
        {"reason": "Guess", "evidence_refs": ["s0:00000000:label"]},
    ],
)
def test_interpretation_rejects_missing_or_noncanonical_evidence(target, evidence):
    with pytest.raises(ValueError, match="evidence"):
        invoke("interpret", expected_revision=current(), evidence=evidence)
    assert not (target.directory / "manual_actions.jsonl").exists()


def test_single_oversized_history_record_has_explicit_bounded_preview(target):
    target.add(interpretation=True)
    path = target.directory / "manual_actions.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    records[1]["interpretation"]["future_evidence"] = {
        f"key_{index}": "x" * 1024 for index in range(100)
    }
    raw = ("\n".join(json.dumps(record) for record in records) + "\n").encode()
    path.write_bytes(raw)
    result = invoke("history", limit=1)
    assert len(json.dumps(result).encode()) <= result["response_byte_budget"]
    assert result["items"][0]["preview_truncated"] is True
    assert result["items"][0]["action_id"] == records[1]["action_id"]
    assert result["truncated_fields"]
    assert result["has_more"] is False
    assert result["next_cursor"] is None
    assert path.read_bytes() == raw


def test_negative_structure_field_offset_reaches_native_query(target):
    result = invoke("query", kind="fields", field_offset=-4, limit=1)
    assert target.calls[-1]["field_offset"] == -4
    assert result["items"]
    with pytest.raises(ValueError, match="signed 32-bit"):
        invoke("query", kind="fields", field_offset=-(2**31) - 1)


def test_truncation_diagnostics_fit_page_budget():
    value = {f"{index}" + "x" * 128: "v" * 2000 for index in range(32)}
    for _ in range(6):
        value = {"k" * 128: value}
    result = restoration._envelope(
        restoration._page([value] * 5, 0, 30),
        {"revision": "r", "subject_revision": "s"},
        {},
    )
    assert result["truncated_fields"]
    assert len(json.dumps(result).encode()) <= result["response_byte_budget"]


@pytest.mark.parametrize(
    ("symbol_coordinates", "subject"),
    [
        ({}, ...),
        ({"section_index": None, "source_offset": None}, ...),
        ({"section_index": None, "source_offset": None}, None),
        ({}, {}),
        (
            {"section_index": None, "source_offset": None},
            {"section_index": None, "source_offset": None},
        ),
        ({"section_index": 0}, {"section_index": 0}),
        ({"source_offset": 0}, {"source_offset": 0}),
        ({"section_index": 0}, {"section_index": 0, "source_offset": None}),
        ({"source_offset": 0}, {"section_index": None, "source_offset": 0}),
        ({"section_index": 0, "source_offset": 0}, {}),
        ({}, {"section_index": 0, "source_offset": 0}),
        (
            {"section_index": False, "source_offset": 0},
            {"section_index": 0, "source_offset": 0},
        ),
        (
            {"section_index": 0, "source_offset": 0},
            {"section_index": 0, "source_offset": False},
        ),
        (
            {"section_index": "0", "source_offset": 0},
            {"section_index": "0", "source_offset": 0},
        ),
        (
            {"section_index": 0, "source_offset": -1},
            {"section_index": 0, "source_offset": -1},
        ),
        (
            {"section_index": 0, "source_offset": 2**32},
            {"section_index": 0, "source_offset": 2**32},
        ),
        (
            {"section_index": 0, "source_offset": 0},
            {"section_index": 1, "source_offset": 0},
        ),
        (
            {"section_index": 0, "source_offset": 0},
            {"section_index": 0, "source_offset": 2},
        ),
    ],
)
def test_symbol_evidence_does_not_match_absent_partial_or_invalid_identity(
    target, symbol_coordinates, subject
):
    target.native_symbols[:] = [{"name": "constant", **symbol_coordinates}]
    target.add(interpretation=subject is not ..., subject=subject)
    before = (target.directory / "manual_actions.jsonl").read_bytes()

    item = invoke("query", kind="symbols")["items"][0]

    assert item["interpretations"] == []
    assert item["interpretation_status"] == "unassessed"
    assert (target.directory / "manual_actions.jsonl").read_bytes() == before


@pytest.mark.parametrize("coordinates", [(0, 0), (0, 2), (1, 0)])
def test_symbol_evidence_matches_concrete_source_identity_including_zero(
    target, coordinates
):
    section, offset = coordinates
    subject = {"section_index": section, "source_offset": offset}
    target.native_symbols[:] = [{"name": "entry", **subject}]
    target.add(name="legacy")
    target.add(
        interpretation=True,
        name="unrelated",
        subject={"section_index": section, "source_offset": offset + 2},
    )
    matching = target.add(interpretation=True, name="matching", subject=subject)

    item = invoke("query", kind="symbols")["items"][0]

    assert [entry["action_id"] for entry in item["interpretations"]] == [
        matching["action_id"]
    ]
    assert item["interpretations"][0]["evidence"]["subject"] == subject
    assert "interpretation_status" not in item


@pytest.mark.parametrize("kind", ["references", "fields", "edges", "gaps"])
def test_unsupported_text_query_refused_before_native_reads(target, kind):
    with pytest.raises(ValueError, match=f"query text is unsupported for {kind}"):
        invoke("query", kind=kind, query="65370")
    assert target.calls == []


def test_instruction_text_query_passed_to_native_provider(target):
    invoke("query", kind="instructions", query="rts", limit=1)
    assert target.calls[-1]["query"] == "rts"
    assert target.calls[-1]["kind"] == "instructions"


@pytest.mark.parametrize("kind", ["references", "fields", "edges"])
def test_empty_text_query_keeps_native_query_compatibility(target, kind):
    invoke("query", kind=kind, query="", limit=1)
    assert target.calls[-1]["query"] == ""


def test_runtime_allocation_plan_requires_current_revision_and_keeps_refusal(target,monkeypatch):
    artifact=target.backend._LISTING_PROJECTION_SERVICE.valid_artifact()
    calls=[]
    def plan(region_id,layout_id,actual):
        calls.append((region_id,layout_id,actual))
        return dict(status='refused',reason='allocator_result_overlaps_protected_runtime_extent')
    monkeypatch.setattr(artifact,'runtime_allocation_plan',plan,raising=False)
    with pytest.raises(ValueError,match='revision'):
        invoke('allocation_plan',region_id='body',layout_id='layout',actual_base=0x59e8)
    assert calls==[]
    revision=current()
    for _ in range(2):
        result=invoke('allocation_plan',expected_revision=revision,
            region_id='body',layout_id='layout',actual_base=0x59e8)
        assert result['plan']['status']=='refused'
    assert calls==[('body','layout',0x59e8)]*2
    with pytest.raises(ValueError,match='revision'):
        invoke('allocation_plan',expected_revision='old',region_id='body',layout_id='layout')


def test_expression_query_preserves_native_field_and_shared_source_identity(target,monkeypatch):
    artifact=target.backend._LISTING_PROJECTION_SERVICE.valid_artifact()
    def query(**options):
        assert options['kind']=='expressions'
        return dict(items=[dict(source_section_index=0,source_offset=0,kind=1,
            instruction_field=dict(extension_offset=2,extension_bytes=4))],offset=0,limit=25,total=1,has_more=False,unknowns=[])
    monkeypatch.setattr(artifact,'query_payload',query)
    result=invoke('query',kind='expressions')
    assert result['items'][0]['section_index']==0
    assert result['items'][0]['source_section_index']==0
    assert result['items'][0]['instruction_field']['extension_bytes']==4
