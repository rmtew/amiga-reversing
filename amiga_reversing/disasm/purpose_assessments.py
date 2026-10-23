"""Bounded semantic claims owned by the Manual Action Log, never source policy.

A whole-scope claim establishes a stated purpose for its interval, not complete
field knowledge, control-flow closure, reachability or relocation safety.
Acceptance belongs to the existing Decision Journal; confidence is never
inferred from that decision or from the spelling of an annotation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

CATEGORIES = ("graphics", "audio", "game_data", "text", "code", "platform", "workspace")
CONFIDENCES = ("low", "medium", "high")


@dataclass(frozen=True, slots=True)
class PurposeAssessment:
    assessment_id: str
    coordinate_space: str
    start: int
    end: int
    category: str
    purpose: str
    confidence: str
    coverage: str
    limits: str
    section_index: int | None = None
    layout_name: str | None = None
    base_symbol: str | None = None

    def __post_init__(self):
        for name, limit in (("assessment_id", 128), ("purpose", 512), ("limits", 512)):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(
                    f"purpose assessment {name} needs nonempty text, at most {limit} characters"
                )
        if self.category not in CATEGORIES or self.confidence not in CONFIDENCES:
            raise ValueError(
                "purpose assessment needs an explicit category and confidence"
            )
        if self.coverage not in {"whole_scope", "partial_scope"}:
            raise ValueError("purpose coverage must be whole_scope or partial_scope")
        if (
            type(self.start) is not int
            or type(self.end) is not int
            or not -(1 << 31) <= self.start < self.end <= 0x100000000
        ):
            raise ValueError("purpose assessment needs a bounded nonempty interval")
        if self.coordinate_space == "source":
            if (
                type(self.section_index) is not int
                or self.section_index < 0
                or self.start < 0
                or self.layout_name is not None
                or self.base_symbol is not None
            ):
                raise ValueError(
                    "source purpose scope requires section_index and nonnegative offsets only"
                )
        elif self.coordinate_space == "base_relative":
            if self.section_index is not None or any(
                not isinstance(x, str) or not x.strip()
                for x in (self.layout_name, self.base_symbol)
            ):
                raise ValueError(
                    "base-relative purpose scope requires exact layout and base identities"
                )
        elif self.coordinate_space == "absolute":
            if (
                self.start < 0
                or self.section_index is not None
                or self.layout_name is not None
                or self.base_symbol is not None
            ):
                raise ValueError(
                    "absolute purpose scope must not include section/base identities"
                )
        else:
            raise ValueError("unsupported purpose coordinate space")

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) - set(cls.__dataclass_fields__):
            raise ValueError("unsupported purpose assessment fields")
        try:
            return cls(**value)
        except TypeError as exc:
            raise ValueError("incomplete purpose assessment") from exc

    def to_dict(self):
        return asdict(self)


def reviewed_assessments(assessments, decisions):
    """Join active replayed claims to the existing journal, without promoting evidence."""
    reviewed = {}
    for bucket, status in (
        ("accepted_facts", "accepted"),
        ("deferred_facts", "deferred"),
        ("rejected_facts", "rejected"),
    ):
        for d in decisions.get(bucket, []):
            if d.get("fact_type") == "restoration_interpretation":
                action = (d.get("selected_identity") or {}).get("subject_id")
                reviewed.setdefault(action, []).append((status, d.get("decision_id")))
    result = []
    for claim in assessments:
        record = dict(claim)
        action = claim.get("action_id")
        reviews = reviewed.get(action, [])
        record["review_status"] = (
            reviews[0][0]
            if len(reviews) == 1
            else "conflicting_reviews"
            if reviews
            else "unassessed"
        )
        record["decision_ids"] = [d[1] for d in reviews]
        record["evidence_available"] = bool(
            (record.get("interpretation") or {}).get("evidence_refs")
        )
        result.append(record)
    return sorted(result, key=lambda a: a["assessment_id"])


def purpose_intervals(start, end, claims):
    """Partition one mapped coordinate domain; partial/provisional claims earn no whole-scope credit."""
    selected = [
        a
        for a in claims
        if a["start"] < end
        and a["end"] > start
        and a["review_status"] not in {"rejected", "deferred"}
    ]
    points = sorted(
        {
            start,
            end,
            *[max(start, a["start"]) for a in selected],
            *[min(end, a["end"]) for a in selected],
        }
    )
    result = []
    for lo, hi in zip(points, points[1:], strict=False):
        active = [a for a in selected if a["start"] <= lo and a["end"] >= hi]
        supported = [
            a
            for a in active
            if a["review_status"] == "accepted"
            and a["evidence_available"]
            and a["coverage"] == "whole_scope"
        ]
        partial = [
            a
            for a in active
            if a["review_status"] == "accepted"
            and a["evidence_available"]
            and a["coverage"] == "partial_scope"
        ]
        status = (
            "overlapping_assessments"
            if len(supported) > 1
            else "supported"
            if supported
            else "partial_claim"
            if partial
            else "provisional"
            if active
            else "unassessed"
        )
        result.append(
            {
                "start": lo,
                "end": hi,
                "status": status,
                "assessment_ids": sorted(a["assessment_id"] for a in active),
                "category": supported[0]["category"] if len(supported) == 1 else None,
                "confidence": supported[0]["confidence"]
                if len(supported) == 1
                else None,
            }
        )
    return result


def purpose_summary(cells):
    sizes = {}
    categories = {}
    for c in cells:
        size = c["end"] - c["start"]
        sizes[c["status"]] = sizes.get(c["status"], 0) + size
        if c["status"] == "supported":
            key = c["category"] + ":" + c["confidence"]
            categories[key] = categories.get(key, 0) + size
    return {
        "status": "supported_scope"
        if sizes.get("supported", 0) and len(sizes) == 1
        else "partially_assessed"
        if sizes.get("supported", 0)
        else "overlap_review_required"
        if sizes.get("overlapping_assessments", 0)
        else "partial_scope_claims"
        if sizes.get("partial_claim", 0)
        else "unreviewed_claims"
        if sizes.get("provisional", 0)
        else "not_assessed",
        "bytes_by_status": dict(sorted(sizes.items())),
        "supported_bytes_by_category_confidence": dict(sorted(categories.items())),
        "intervals": cells,
    }


def unit_purpose_summary(cells):
    """Units link to the common scoped claims rather than repeating interval ledgers."""
    ids = sorted({identity for cell in cells for identity in cell["assessment_ids"]})
    if not ids:
        return {"status": "not_assessed"}
    summary = purpose_summary(cells)
    summary.pop("intervals")
    return {**summary, "assessment_ids": ids}


def observed_absolute_purpose(observations, assessments):
    """Assess only native observed extents, never fill the address-space envelope."""
    ranges = []
    for observation in sorted(observations, key=lambda x: (x["start"], x["end"])):
        lo, hi = observation["start"], observation["end"]
        if hi <= lo:
            continue
        if ranges and lo <= ranges[-1][1]:
            ranges[-1][1] = max(hi, ranges[-1][1])
        else:
            ranges.append([lo, hi])
    selected = [a for a in assessments if a["coordinate_space"] == "absolute"]
    result = purpose_summary(
        [cell for lo, hi in ranges for cell in purpose_intervals(lo, hi, selected)]
    )
    return {
        **result,
        "extent_limit": "observed_ranges_only; full domain denominator unknown",
    }
