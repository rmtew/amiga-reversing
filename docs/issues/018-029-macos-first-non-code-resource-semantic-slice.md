# 018-029: Mac OS First Non-CODE Resource Semantic Slice

Status: completed

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

## Resolution

Decision: implement one narrow type-level semantic slice for `CURS`; do not
decode non-CODE payload bytes.

Trace blocks:

- Candidate resource types considered: `CURS`, `acur`, `cmdo`, and `vers` from
  the current Mac non-CODE resource type inventory.
- Sources searched: Inside Macintosh / QuickDraw cursor records and MPW
  resource type lists for `CURS` plus local docs for the named non-CODE types.
- Selected type and reason: `CURS`, because local sources define a narrow
  classic 16-by-16 cursor layout and the current Mac fixture exposes the type.
- Accepted semantic fact: `macos.resource_fork.curs.layout.accepted` is
  type-level only: 32 bytes image data, 32 bytes mask data, and 4 bytes hot
  spot Point.
- Candidate/deferred facts: `acur`, `cmdo`, and `vers` remain candidate
  inventory with `payload_decode_status: unsupported`; individual `CURS`
  payload bitmap/hotspot decoding is still unsupported.
- Implementation scope: payload/web rows label only `CURS` type-level semantics
  as validated accepted parser output. CODE parser/listing behavior is
  unchanged.

## Research Coverage

- [x] 018-014 inventory reviewed.
- [x] Current non-CODE UI reviewed.
- [x] Local docs searched for present resource types.
- [x] One resource type selected or blocker recorded.
- [x] Implementation/defer decision selected.
- [x] CODE regression risk checked.

## Research Review

- [x] Second pass checked non-CODE semantics are not over-accepted.
- [x] Source policy recorded.
- [x] CODE parser/UI behavior remains unchanged.
- [x] Candidate/deferred labels preserved for unsupported types.
- [x] Proposal/docs updated.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] One non-CODE resource type selected or blocker recorded.
- [x] Semantic evidence classified.
- [x] Parser/payload/web behavior changed only if evidence supports it.
- [x] CODE behavior remains unchanged.
- [x] Relevant tests/CDP pass if behavior changes.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes if KB
  changes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m pytest tests\test_macos_project_payload.py tests\test_web_app_source.py -q
22 passed
uv run python -m pytest tests\test_web_e2e_cdp.py::test_brave_cdp_macos_code_details_show_candidate_previews -q
1 passed
uv run python -m pytest tests\test_macos_asm_container.py tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py -q
19 passed
uv run python -m amiga_reversing.tools.validate_018_issues
```
