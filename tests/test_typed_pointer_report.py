from dataclasses import replace

import pytest

from amiga_reversing.disasm.target_metadata import (
    SeededEntityMetadata,
    TargetMetadata,
    TargetMetadataReviewStatus,
    TargetMetadataSeedOrigin,
)
from amiga_reversing.disasm.typed_pointer_report import typed_pointer_report


def _field(addr, *, kind="target_pointer", name="pointer"):
    return SeededEntityMetadata(
        addr=addr, end=addr + 4, struct_name="Record", field_name=name,
        name=name, value_kind=kind,
        seed_origin=TargetMetadataSeedOrigin.MANUAL_ANALYSIS,
        review_status=TargetMetadataReviewStatus.SEEDED, citation="test",
    )


def test_report_counts_native_outcomes_but_never_promotes_pointer_named_scalar():
    fields = (_field(0), _field(4), _field(8),
              _field(12, kind="scalar", name="looks_like_ptr"))
    metadata = TargetMetadata(target_type="raw", entry_register_seeds=(), seeded_entities=fields)
    calls = []

    def row_lookup(*, section_index, offset):
        calls.append((section_index, offset))
        if offset == 0:
            return {"start_offset": 0, "end_offset": 4,
                    "pointer_resolution": {"outcome": "symbolic", "reason": "resolved_source",
                                           "symbol": "image", "addend": 4}}
        if offset == 4:
            return {"start_offset": 4, "end_offset": 8,
                    "pointer_resolution": {"outcome": "null", "reason": "null_pointer"}}
        # Text cannot rescue a missing native expression or interrupted field.
        return {"text": "dc.l plausible_symbol", "end_offset": 10}

    result = typed_pointer_report(metadata, row_lookup, offset=1, limit=1)
    assert result["total"] == 3
    assert result["outcomes"] == {"null": 1, "symbolic": 1, "unresolved": 1}
    assert result["items"][0]["source_offset"] == 4
    assert result["next_offset"] == 2
    assert calls == [(0, 0), (0, 4), (0, 8)]
    summary = typed_pointer_report(metadata, row_lookup, summary_only=True)
    assert summary["items"] == [] and summary["total"] == 3
    exceptions = typed_pointer_report(metadata, row_lookup, exceptions_only=True)
    assert exceptions["population_total"] == 3 and exceptions["total"] == 1
    assert exceptions["items"][0]["source_offset"] == 8
    assert exceptions["outcomes"] == result["outcomes"]


def test_covering_row_cannot_supply_another_fields_resolution():
    metadata = TargetMetadata(target_type="raw", entry_register_seeds=(), seeded_entities=(_field(4),))
    report = typed_pointer_report(metadata, lambda **_: {
        "start_offset": 0, "end_offset": 8,
        "pointer_resolution": {"outcome": "symbolic", "reason": "resolved_source"},
    })
    assert report["reasons"] == {"field_boundary": 1}
    report = typed_pointer_report(metadata, lambda **_: {"start_offset": 4, "end_offset": 8})
    assert report["reasons"] == {"missing_native_resolution": 1}


def test_conflicting_canonical_pointer_fields_are_not_silently_deduplicated():
    field = _field(0)
    metadata = TargetMetadata(target_type="raw", entry_register_seeds=(),
                              seeded_entities=(field, replace(field, name="conflicting")))
    with pytest.raises(ValueError, match="Conflicting canonical"):
        typed_pointer_report(metadata, lambda **_: None)


@pytest.mark.parametrize("limit", [0, 101, True])
def test_report_page_bounds(limit):
    with pytest.raises(ValueError, match="1..100"):
        typed_pointer_report(TargetMetadata(target_type="raw", entry_register_seeds=()),
                             lambda **_: None, limit=limit)


def test_exception_filter_requires_boolean():
    with pytest.raises(ValueError, match="exceptions_only must be boolean"):
        typed_pointer_report(TargetMetadata(target_type="raw", entry_register_seeds=()),
                             lambda **_: None, exceptions_only=1)


def test_source_interval_filters_before_native_lookup_and_scopes_counts():
    fields = (_field(0), _field(4), _field(8), _field(12), replace(_field(4), hunk=1))
    metadata = TargetMetadata(target_type="raw", entry_register_seeds=(), seeded_entities=fields)
    calls = []
    def lookup(*, section_index, offset):
        calls.append((section_index, offset))
        return {"start_offset": offset, "end_offset": offset+4, "pointer_resolution": {
            "outcome": "symbolic" if offset == 4 else "unresolved", "reason": "native_fixture",
        }}
    filters = dict(section_index=0, source_offset=4, end_offset=12)
    result = typed_pointer_report(metadata, lookup, **filters, limit=1)
    assert calls == [(0, 4), (0, 8)]
    assert result["total"] == result["population_total"] == 2
    assert result["outcomes"] == {"symbolic": 1, "unresolved": 1}
    assert result["items"][0]["source_offset"] == 4 and result["has_more"]
    exceptions = typed_pointer_report(metadata, lookup, **filters, exceptions_only=True)
    assert exceptions["population_total"] == 2 and exceptions["total"] == 1
    assert exceptions["items"][0]["source_offset"] == 8
    # Bounds select starts, not a truncated native field or a storage extent.
    narrow = typed_pointer_report(metadata, lookup, section_index=0, source_offset=4, end_offset=5)
    assert narrow["total"] == 1 and narrow["items"][0]["end_offset"] == 8
    other = typed_pointer_report(metadata, lookup, section_index=1)
    assert other["total"] == 1 and other["items"][0]["section_index"] == 1


@pytest.mark.parametrize('filters', [
    {'source_offset': 0}, {'end_offset': 8}, {'section_index': True},
    {'section_index': -1}, {'section_index': 0, 'source_offset': True},
    {'section_index': 0, 'source_offset': 8, 'end_offset': 4},
    {'section_index': 0, 'source_offset': 8, 'end_offset': 8},
])
def test_invalid_source_selection_refuses_without_lookup(filters):
    def lookup(**_):
        pytest.fail('invalid selection must not read native rows')
    with pytest.raises(ValueError):
        typed_pointer_report(TargetMetadata(target_type='raw', entry_register_seeds=()), lookup, **filters)
