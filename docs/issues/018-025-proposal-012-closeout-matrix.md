# 018-025: Proposal 012 Closeout Matrix

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Proposal 012 remaining blocker clarity
- Blocked by: none
- Work order: batch-safe with research/docs issues; do not change code.
- Current proposal state: Proposal 012 has accumulated completed Mac source,
  container, artifact, preview, UI, and CDP work, but remaining closeout items
  are scattered through narrative text.
- Desired proposal state after this issue: Proposal 012 has a concise closeout
  matrix that names completed starter support, remaining blockers, owning
  proposal/issue area, evidence needed, and whether the item is required for
  starter closeout or deeper roundtrip work.

## Knowledge Delta

- Adds: closeout matrix for Proposal 012.
- Changes: remaining Mac platform work becomes auditable and assignable.
- Replaces: scattered narrative blocker list as the only closeout guide.
- Deletes: no historical notes unless duplicated and misleading.
- Leaves out of scope: parser/payload/web implementation, KB fact changes,
  source recovery, relocation implementation.

## Default Behavior

- Documentation-only issue.
- Do not mark Proposal 012 closed.
- Do not weaken the current blocked/open status.
- Matrix must preserve candidate/deferred status for byte-entry and relocation.

## Evidence Standard

- Matrix must include at least: byte-entry rules, relocation/fixups,
  source-to-CODE mapping, non-CODE semantics, overflow extents, roundtrip,
  CODE preview/UI state, and starter target usefulness.
- Each row must state completed/current state, remaining work, evidence needed,
  and likely owning issue/proposal.
- Completed 018-009 through 018-018 work must be represented without implying
  accepted byte-entry or relocation semantics.

## Implementation Slice

- Review Proposal 012 closeout/future-scope sections.
- Review Proposal 018 relationship-to-012 notes.
- Add a closeout matrix to Proposal 012.
- Add a brief pointer from Proposal 018 if useful.
- Run issue/doc validation.

## Research Completion Standard

Record trace blocks for:

- docs reviewed;
- matrix row set;
- items explicitly not required for starter closeout;
- items still blocking 012;
- follow-up issue references.

## Research Coverage

- [ ] Proposal 012 closeout text reviewed.
- [ ] Proposal 018 relationship text reviewed.
- [ ] Completed 018-009 through 018-018 state reviewed.
- [ ] Matrix rows selected.
- [ ] Starter vs deeper-roundtrip distinction checked.

## Research Review

- [ ] Second pass checked matrix does not close 012 prematurely.
- [ ] Candidate/deferred facts remain candidate/deferred.
- [ ] Completed work is accurately represented.
- [ ] Follow-up ownership is clear.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Proposal 012 closeout matrix added.
- [ ] Remaining blockers and non-blockers clearly separated.
- [ ] Completed 018 work accurately represented.
- [ ] No code files modified.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
