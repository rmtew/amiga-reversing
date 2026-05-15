# 017-007: Label Policy Validation Metadata

## Parent

[PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)
- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)
- [PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Return label policy validation metadata in the label edit interaction schema so the UI can validate name and scope locally under the active source rendering assembler profile.

## Acceptance criteria

- [ ] Interaction schema includes active assembler/profile context where it affects label editing.
- [ ] Metadata includes local label support, allowed scopes, current scope, owner/anchor context where available, name grammar, reserved names/prefixes, and validation messages.
- [ ] UI distinguishes invalid syntax, policy-disallowed local names, reserved/conflicting names, unknown/stale validation, and commit-ready names.
- [ ] Local-label scope controls appear only when supported by the active source rendering profile.
- [ ] Server remains authoritative on commit for final uniqueness, owner validity, stale state, and render safety.
- [ ] Tests cover `.local` under allowed and disallowed profiles, invalid characters, reserved names, and stale server rejection.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [017-003: Inline Text Editors For Labels And Comments](017-003-inline-text-editors-for-labels-and-comments.md)
- [007-004: Listing Element Selection](007-004-listing-element-selection.md)
