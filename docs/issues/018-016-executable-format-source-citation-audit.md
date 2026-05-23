# 018-016: Executable Format Source Citation Audit

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: source policy, citation quality, and accepted-fact audit
- Blocked by: `018-001`
- Independent of: `018-010`
- Current proposal state: executable-format KB records contain mixed old
  manual, project-observed, and parser-asserted evidence. The validator checks
  structure, but not citation quality or whether accepted facts have strong
  enough source wording.
- Desired proposal state after this issue: accepted facts across 018 have an
  explicit citation-quality audit and weak claims are downgraded or marked for
  follow-up.

## Knowledge Delta

- Adds: citation-quality audit notes for accepted/parser-asserted facts.
- Changes: weak or ambiguous accepted facts become explicit debt instead of
  hidden trust.
- Replaces: relying on structural validation as proof that citations are good.
- Deletes: no facts unless they are clearly wrong; prefer downgrade/defer with
  reason.
- Leaves out of scope: parser/rendering changes, new platform support,
  exhaustive source acquisition.

## Default Behavior

- No parser behavior changes.
- No renderer behavior changes.
- No accepted fact may remain accepted solely because tests pass if its citation
  wording does not support the claim.

## Evidence Standard

- Audit each accepted/parser-asserted fact for:
  source type, license status, cited path/page, claim wording, affected model
  layer, source strength, and ambiguity.
- Source strength should be recorded as direct, indirect, project-observed,
  parser-asserted, conflict, or insufficient.
- Insufficient accepted facts must be downgraded to candidate/deferred or
  marked as parser assertions with proper assertion fields.
- Large copied source text remains disallowed.

## Implementation Slice

- Review accepted/parser-asserted facts in
  `knowledge/platform_executable_formats.json`.
- Update `docs/platform-executable-formats.md` with audit summary and any
  downgrade/deferred rationale.
- Add tests if KB states change.
- Do not change parser/rendering code.

## Research Completion Standard

Record trace blocks for:

- every accepted/parser-asserted fact id reviewed;
- source path/page and claim wording summary;
- audit result and reason;
- downgrade/defer/parser-assertion changes;
- remaining source gaps.

## Research Coverage

- [ ] Mac accepted facts audited.
- [ ] Amiga accepted/parser-asserted facts audited if present.
- [ ] Atari accepted/parser-asserted facts audited if present.
- [ ] Parser assertions checked for required fields.
- [ ] Insufficient citations downgraded or marked for follow-up.
- [ ] Source policy violations checked.

## Research Review

- [ ] Second pass checked audit results against source citations.
- [ ] Accepted facts have direct citations or valid parser assertions.
- [ ] Project-observed-only general claims are not validated.
- [ ] No parser/rendering behavior changed.
- [ ] Validator/tests updated if fact states changed.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Accepted/parser-asserted facts audited.
- [ ] Weak accepted facts downgraded, deferred, or converted to parser
  assertions with required fields.
- [ ] Audit summary documented.
- [ ] No parser/rendering behavior changed.
- [ ] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
