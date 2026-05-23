# 018-007: Executable KB Issue Sign-Off Enforcement

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: 018 issue protocol hygiene and completion enforcement
- Blocked by: at least one completed 018 issue using the protocol structure
- Current proposal state: 018 issues now define research coverage, research
  review, and required sign-off, but completion is still manually reviewed.
- Desired proposal state after this issue: a local check can flag completed
  `018-*` issues whose required sections or checkboxes are incomplete before
  commit/review.

## Knowledge Delta

- Adds: local issue protocol validation for `018-*`.
- Changes: completed 018 issues become mechanically reviewable.
- Replaces: purely manual detection of missing sign-off.
- Deletes: none.
- Leaves out of scope: changing 017 validation, UI, and broad CI integration
  unless already trivial.

## Default Behavior

- The validator must not rewrite issue files.
- It must not block active/open issues with unchecked boxes.
- It must fail or warn for issues marked implemented/completed/complete if
  required sections or sign-off boxes are incomplete.

## Evidence Standard

The check must verify:

- `Status:` exists and is known locally;
- proposal context references Proposal 018;
- required protocol sections exist;
- completed statuses have no unchecked boxes in research coverage, research
  review, or required sign-off;
- completion evidence exists for completed statuses;
- superseded/deleted issues identify replacement or reason where applicable.

## Implementation Slice

- Python/tooling: add a small local validator consistent with existing repo
  tooling.
- Tests: passing issue fixture, missing section failure, unchecked completed
  checkbox failure, superseded reason check, and no file rewrite.
- Proposal: update 018 with validation rules if needed.

## Research Completion Standard

Record trace blocks for existing 017 validator pattern, issue status vocabulary,
test/tool location, and any historical exception kept out of scope.

## Completion Evidence

- Added `amiga_reversing.tools.validate_018_issues`.
- Added `tests/test_validate_018_issues.py`.
- Updated Proposal 018 implementation notes with the validation rules.
- The validator checks status vocabulary, Proposal 018 references, required
  protocol sections, completion evidence, completed checkbox sign-off, and
  superseded/deleted reasons. It does not rewrite files.

Verification:

```text
uv run python -m pytest tests\test_validate_018_issues.py -q
uv run python -m amiga_reversing.tools.validate_018_issues
```

## Research Coverage

- [x] Existing 017 issue validator pattern checked.
- [x] Current `018-*` status vocabulary checked.
- [x] Required 018 issue sections checked.
- [x] Passing and failing examples planned.
- [x] Historical exception policy reviewed.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for markdown validation helpers.
- [x] Exception list reviewed for pure churn risk.
- [x] Proposal updated with validation rules or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Validator behavior tested.
- [x] Completed unchecked checkbox failure tested.
- [x] No file rewrite behavior tested.
- [x] Active/open issue behavior tested.
- [x] Post-commit review found no unresolved worthwhile findings.

## Post-Completion Review Gap

The 018 issue validator checks structure and checkbox completion only. It does
not prove that completion evidence is technically true, that parser-output fact
ids resolve to the KB, or that implementation tests cover the intended runtime
paths.

Workers must not use a passing `validate_018_issues` result as evidence that
018 implementation goals are complete. For the concrete gaps found after commit
`b5e38e84`, see
`docs/issues/018-008-parser-output-fact-validation-and-macos-rendering-cleanup.md`.
