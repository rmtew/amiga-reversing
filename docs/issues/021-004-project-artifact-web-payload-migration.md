# 021-004: Project Artifact Web Payload Migration

Status: active
Type: AFK
Source proposal: docs/proposals/021-native-macos-code-source-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`
- Blocked by: 021-003.
- Current state: Mac project/artifact/web views still contain compatibility
  assumptions from the raw-wrapper era.
- Desired state after this issue: existing user-visible Mac views consume native
  Mac CODE source identity and shared ranges.

## Start-Of-Issue Refresh

Review 021-003 completion evidence and list every public payload field that
still depends on raw-wrapper assumptions. Update Proposal 021 before deleting or
renaming public fields.

## What To Build

Migrate Mac project payloads, target artifact rendering, and web/API listing
surfaces to native Mac CODE source identity.

Required behavior:

- Existing CODE 0 metadata, CODE coverage, candidate previews, orphan ranges,
  non-CODE placeholders, and deferred relocation/fixup explanations remain
  visible.
- Payloads expose native source identity where they previously exposed or implied
  wrapped raw source identity.
- Shared executable ranges are the source of range authority in user-facing
  payloads where range authority is needed.
- Public compatibility fields may remain only if tests prove current consumers
  still need them and Proposal 021 records the retained blocker.

## Acceptance Criteria

- [ ] Mac project payload reports native Mac CODE source identity.
- [ ] Mac target artifact rendering reports native Mac CODE source identity.
- [ ] Mac web/API listing payloads report native Mac CODE source identity.
- [ ] Candidate/deferred/non-CODE visibility does not regress.
- [ ] Tests fail if raw-wrapper identity is reintroduced in migrated payloads.
- [ ] Proposal 021 records retained public compatibility fields and blockers.

## Blocked By

- 021-003

## Required Sign-Off

- [ ] No UI/API visibility regression.
- [ ] No fact promotion.
- [ ] Mac project/artifact/web tests pass.
- [ ] Cross-platform 020 coverage still passes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record payload fields migrated, retained compatibility fields, and proof tests.
