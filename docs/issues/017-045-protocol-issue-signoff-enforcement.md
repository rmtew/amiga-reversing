# 017-045: Protocol Issue Sign-Off Enforcement

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: issue protocol hygiene and review enforcement
- Blocked by: none after `017-040`
- Current proposal state: the issue protocol requires research coverage,
  research review, required sign-off, proposal updates, and post-commit review.
  Recent review found a completed issue with unchecked research boxes, so the
  protocol needs a lightweight enforcement path.
- Desired proposal state after this issue: a local check can flag active or
  completed `017-*` issues whose required protocol sections or checkboxes are
  incomplete before commit/review.

## Protocol Delta

- Adds: issue protocol validation for `017-*` markdown issues.
- Changes: completed issues become mechanically reviewable for required
  sections, checkbox completion, proposal reference, and completion evidence.
- Replaces: purely manual detection of missing issue sign-off.
- Deletes: none.
- Leaves out of scope: changing historical issue wording except where needed to
  make validation rules precise, CI integration unless already trivial, and UI.

## Default Behavior

- The validator must not rewrite issue files.
- It must not block work on active issues with unchecked boxes.
- It must fail or warn for issues marked implemented/completed/complete if
  required research/sign-off boxes remain unchecked or required sections are
  missing.

## Evidence Standard

The check must verify, at minimum:

- `Status:` exists and is one of the known local statuses;
- proposal context references `docs/proposals/017-evidence-driven-analysis-protocol.md`;
- required protocol sections exist for active/completed future issues;
- completed statuses have no unchecked boxes in research coverage, research
  review, or required sign-off sections;
- completion evidence exists for completed statuses;
- superseded issues identify the replacement or reason.

Any exception for historical issues must be explicit and narrow.

## Pandora Proof

- Use `017-039` and `017-040` as passing examples.
- Include a fixture or temporary sample issue with unchecked completed research
  boxes to prove the validator catches the failure.
- Do not mutate Pandora target state.

## Implementation Slice

- C fact graph/query work: none.
- Python/API/report work: add a small local validator or test helper consistent
  with existing repo tooling.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests/proof: passing examples, missing section failure, unchecked completed
  checkbox failure, superseded replacement/reason check, and no file rewrite.

## Research Completion Standard

Record trace blocks for issue status conventions, existing proposal issue
protocol, current `017-*` issue variations, test/tool location, and any
historical exception kept out of scope.

## Research Coverage

- [x] Current `017-*` status vocabulary checked.
- [x] Required issue sections checked against proposal protocol.
- [x] Historical variations and superseded issue handling checked.
- [x] Existing docs/test/tooling patterns checked.
- [x] Passing and failing examples planned.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for existing markdown validation helpers.
- [x] Historical exception list reviewed for pure churn risk.
- [x] Proposal updated with validation rules or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Validator behavior tested.
- [x] No file rewrite behavior tested.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Added `amiga_reversing.tools.validate_017_issues`, a read-only local
  validator for `017-*` issue Markdown. It checks status vocabulary, proposal
  reference, required protocol sections for protocol-era issues, completed
  checklist closure, completion evidence, and superseded replacement/reason.
- Historical exception is narrow: `017-001` through `017-038` predate this
  validator's enforced completion-evidence shape, while `017-039+` are
  validated against it.
- Required passing examples verified:
  `uv run python -m amiga_reversing.tools.validate_017_issues docs\issues\017-039-rsset-journal-backed-safe-mutation.md docs\issues\017-040-pandora-rsset-journal-accept-evidence.md`
  exited 0 with no file rewrite.
- Fixture tests cover passing completed issue, active unchecked issue,
  completed unchecked failure, missing section failure, superseded
  replacement/reason failure, and no-rewrite CLI behavior.
- Verification: focused 369-test pytest run and changed-file `ruff check` both
  passed.
