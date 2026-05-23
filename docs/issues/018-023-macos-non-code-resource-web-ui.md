# 018-023: Mac OS Non-CODE Resource Web UI

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS non-CODE resource metadata visibility
- Blocked by: `018-014`
- Work order: may run after `018-018`; avoid concurrent edits with `018-024`
  because both touch Mac web container UI.
- Current proposal state: non-CODE resource metadata inventory exists as
  candidate/deferred knowledge, and the artifact has placeholders, but the web
  UI does not present a useful non-CODE resource detail view.
- Desired proposal state after this issue: Mac web UI exposes non-CODE resource
  metadata inventory with candidate/deferred labels and CDP verification.

## Knowledge Delta

- Adds: browser-visible non-CODE resource metadata obligations.
- Changes: non-CODE resources become visible as structured metadata, not only
  count/placeholders.
- Replaces: raw resource type list as the only web-visible non-CODE surface.
- Deletes: no candidate/deferred state.
- Leaves out of scope: decoding resource payload semantics, accepting unknown
  resource formats, and CODE preview/listing changes.

## Default Behavior

- Non-CODE resource semantics remain candidate/deferred unless already accepted.
- UI must distinguish known metadata, candidate metadata, deferred, unsupported,
  and unknown.
- Do not imply non-CODE payload decoding is complete.
- CODE resource UI behavior must remain unchanged.

## Evidence Standard

- Browser-visible rows must show resource type/count/status and evidence reason
  or inventory source.
- CDP must verify at least one non-CODE metadata row and one candidate/deferred
  label.
- Tests must ensure CODE preview UI is not regressed.

## Implementation Slice

- Trace 018-014 inventory output and current Mac project payload fields.
- Add/extend payload only if needed to expose structured non-CODE metadata.
- Render non-CODE metadata in the Mac web container view.
- Add focused web/source tests and CDP verification.
- Update docs with current candidate/deferred non-CODE UI state.

## Research Completion Standard

Record trace blocks for:

- inventory source consumed;
- payload fields added or reused;
- UI shape selected;
- CDP assertions;
- non-goals for payload decoding.

## Research Coverage

- [ ] 018-014 inventory reviewed.
- [ ] Current payload non-CODE fields traced.
- [ ] UI shape selected.
- [ ] CDP assertions selected.
- [ ] CODE UI regression risk checked.
- [ ] 012/018 wording checked.

## Research Review

- [ ] Second pass checked non-CODE semantics are not over-accepted.
- [ ] CODE preview/listing UI still works.
- [ ] Candidate/deferred labels are visible.
- [ ] CDP verifies browser-rendered non-CODE rows.
- [ ] Proposal/docs updated.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Non-CODE metadata inventory visible in Mac web UI.
- [ ] Candidate/deferred/unsupported labels preserved.
- [ ] CODE resource UI behavior remains unchanged.
- [ ] CDP browser verification passes.
- [ ] Relevant web tests pass.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
