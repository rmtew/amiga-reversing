# 018-004: Generated Checks And Heuristic Guardrails

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: generated validation and candidate/accepted parser boundaries
- Blocked by: `018-001`, at least one accepted platform record from `018-003`
- Current proposal state: facts can be represented, but tooling does not yet
  prevent candidate facts from being treated as accepted parser behavior.
- Desired proposal state after this issue: local tests/checks fail when a parser
  or renderer promotes heuristic-only executable facts.

## Knowledge Delta

- Adds: schema/data validation checks, accepted-vs-candidate guardrails, and
  reportable KB-backed parser coverage.
- Changes: 018-backed issues become mechanically harder to close prematurely.
- Replaces: purely manual review of heuristic promotion.
- Deletes: none.
- Leaves out of scope: migrating Mac parser/listing code, full precommit
  integration for legacy platforms, and rewriting historical parser behavior.

## Default Behavior

- Existing Amiga/Atari parser behavior remains unchanged.
- Existing Mac parser behavior remains unchanged until 018-005.
- Checks are blocking for new/adopted KB-backed parser slices and optional
  reports for legacy areas until they declare `kb_backed: true`.

## Evidence Standard

The guardrail must distinguish:

- validated/parser_asserted facts allowed for accepted parser output;
- candidate facts allowed only for reports/candidate ranges;
- deferred/unsupported facts that must emit placeholder, fail closed, or block
  closeout according to the KB.

## Implementation Slice

- Python tests/tooling: validate KB files and fact-state use.
- Generated checks: create the first check path from KB to parser expectation.
- Mac proof: show the current CODE entry heuristic cannot be labelled accepted
  without 018-003 validation.
- Proposal/issues: update if enforcement discovers missing issue protocol.

## Research Completion Standard

Record trace blocks for existing test/tool locations, schema validation method,
generated metadata patterns, and any check deliberately left report-only.

## Research Coverage

- [ ] Existing KB/schema test patterns checked.
- [ ] Existing generated metadata/check patterns checked.
- [ ] Candidate-vs-accepted failure cases planned.
- [ ] Mac heuristic guardrail planned.
- [ ] Legacy report-only behavior scoped.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Guardrails fail for candidate promotion.
- [ ] Guardrails do not block untouched legacy parser behavior.
- [ ] Proposal updated with enforcement rules or deferred follow-ups.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] KB validation checks added.
- [ ] Candidate promotion failure tested.
- [ ] Mac heuristic guardrail tested.
- [ ] Legacy parser behavior unchanged unless explicitly adopted.
- [ ] Post-commit review found no unresolved worthwhile findings.
