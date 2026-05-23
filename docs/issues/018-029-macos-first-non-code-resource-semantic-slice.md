# 018-029: Mac OS First Non-CODE Resource Semantic Slice

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS non-CODE resource semantics
- Blocked by: `018-014`, `018-023`, `018-025`
- Work order: research first. Only implement parser/payload/web behavior for a
  single resource type if the semantic evidence is sufficient and the issue
  records exact scope.
- Current proposal state: non-CODE resource types are browser-visible as
  candidate inventory with unsupported payload-decode status. No non-CODE
  resource type has accepted semantic decoding.
- Desired proposal state after this issue: one useful non-CODE resource type is
  selected and either implemented as a narrow semantic slice with citations, or
  explicitly deferred with a documented evidence blocker.

## Knowledge Delta

- Adds: first resource-type-specific semantic decision for Mac non-CODE
  resources.
- Changes: non-CODE work moves from inventory-only toward one cited semantic
  slice, or records why it cannot yet do so.
- Replaces: generic "later resource-specific semantics" note.
- Deletes: no inventory rows.
- Leaves out of scope: broad resource manager implementation, CODE parsing,
  relocation/fixups, roundtrip, and multiple resource types.

## Default Behavior

- Select exactly one initial resource type unless documenting why none qualify.
- Prefer a type that appears in MPW `Asm` and has old/compatible documentation.
- Keep semantics candidate/deferred unless evidence supports accepted/parser-
  asserted output.
- Do not decode payload bytes if layout evidence is insufficient.
- CODE UI and CODE parser behavior must remain unchanged.

## Evidence Standard

- Accepted semantics require cited resource layout or parser assertion with
  reason, standard interpretation, and scope.
- Project-observed payload bytes alone may support candidate inventory only.
- Tests must prove unsupported/candidate labels remain where semantics are not
  accepted.

## Implementation Slice

- Review 018-014 inventory and current non-CODE UI.
- Search local Inside Macintosh/MPW docs for resource types present in MPW
  `Asm`, such as `vers`, `CURS`, `acur`, or `cmdo`.
- Pick one resource type and decide:
  - narrow semantic implementation; or
  - documented blocker/deferred packet.
- If implementing, add payload/web/artifact tests and CDP verification.
- Update docs/proposals with the selected type and status.

## Research Completion Standard

Record trace blocks for:

- candidate resource types considered;
- sources searched;
- selected type and reason;
- semantic facts accepted/candidate/deferred;
- implementation or blocker decision.

## Research Coverage

- [ ] 018-014 inventory reviewed.
- [ ] Current non-CODE UI reviewed.
- [ ] Local docs searched for present resource types.
- [ ] One resource type selected or blocker recorded.
- [ ] Implementation/defer decision selected.
- [ ] CODE regression risk checked.

## Research Review

- [ ] Second pass checked non-CODE semantics are not over-accepted.
- [ ] Source policy recorded.
- [ ] CODE parser/UI behavior remains unchanged.
- [ ] Candidate/deferred labels preserved for unsupported types.
- [ ] Proposal/docs updated.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] One non-CODE resource type selected or blocker recorded.
- [ ] Semantic evidence classified.
- [ ] Parser/payload/web behavior changed only if evidence supports it.
- [ ] CODE behavior remains unchanged.
- [ ] Relevant tests/CDP pass if behavior changes.
- [ ] `amiga_reversing.tools.platform_executable_formats validate` passes if KB
  changes.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
