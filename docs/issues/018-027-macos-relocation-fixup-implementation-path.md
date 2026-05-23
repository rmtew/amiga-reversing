# 018-027: Mac OS Relocation/Fixup Implementation Path

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS Segment Loader relocation/fixup implementation path
- Blocked by: `018-021`
- Work order: research/planning first. Do not implement parser relocation
  behavior unless this issue finds sufficient accepted/parser-asserted evidence
  and explicitly records the migration scope.
- Current proposal state: 018-021 found candidate Segment Loader memory
  relocation context, but no accepted on-disk CODE fixup byte-layout rule.
  Parser/artifact/web output correctly remains deferred-only for fixups.
- Desired proposal state after this issue: the project has a concrete
  relocation/fixup implementation path, or a documented blocker showing exactly
  what evidence/source is missing before implementation can start.

## Knowledge Delta

- Adds: implementation-readiness assessment for Mac relocation/fixup handling.
- Changes: relocation/fixup work becomes actionable or explicitly blocked.
- Replaces: generic "recover on-disk fixup format" closeout row.
- Deletes: no deferred state unless replaced by accepted/parser-asserted facts.
- Leaves out of scope: byte-entry promotion, source-to-CODE mapping, non-CODE
  semantics, and roundtrip.

## Default Behavior

- Existing parser output remains deferred unless this issue records sufficient
  accepted/parser-asserted evidence.
- If implementation is not justified, close with a blocker packet and do not
  touch parser/payload/web behavior.
- If implementation is justified, scope only a narrow parser-visible slice and
  keep unknown fixups deferred.
- Do not infer relocation formats from decoded instruction bytes alone.

## Evidence Standard

- Implementation requires source-backed or parser-asserted byte layout:
  where fixup records live, how they are encoded, what payload offsets they
  affect, and how Segment Loader applies them.
- Runtime memory relocation context is not enough by itself.
- Tests must distinguish accepted fixup facts from deferred/unknown fixups.

## Implementation Slice

- Search local docs and extracted MPW/tool materials for fixup layout evidence.
- Inspect available binary/container data only as project-observed candidate
  evidence.
- Produce one of:
  - implementation plan with exact fact ids and first parser slice; or
  - blocker packet with missing evidence list.
- Update Proposal 012/018 and `docs/platform-executable-formats.md`.
- Avoid parser behavior changes unless the plan includes accepted/parser-
  asserted facts and tests.

## Research Completion Standard

Record trace blocks for:

- sources searched;
- binary structures inspected, if any;
- fixup layout facts found or missing;
- implementation/defer decision;
- tests or future tests required.

## Research Coverage

- [ ] Local Mac/MPW docs searched for fixup layout.
- [ ] Existing relocation packets reviewed.
- [ ] Project-observed binary evidence classified.
- [ ] Implementation/defer decision selected.
- [ ] Proposal 012 closeout matrix impact checked.

## Research Review

- [ ] Second pass checked runtime relocation context is not overused.
- [ ] Deferred state remains if byte layout is missing.
- [ ] Parser behavior remains unchanged unless evidence supports it.
- [ ] Proposal/docs updated with exact blocker or plan.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Relocation/fixup implementation path or blocker packet added.
- [ ] Evidence strength classified.
- [ ] Parser behavior unchanged unless justified.
- [ ] Candidate/deferred facts are not promoted without support.
- [ ] `amiga_reversing.tools.platform_executable_formats validate` passes if KB
  changes.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
