# 012-025: Post-018 Closeout Blocker Map

Status: active

## Proposal Context

- Source proposal: `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Proposal 018 is complete as the executable-format KB authority.
- This issue replaces the still-active `012-023` planning role. Complete this
  issue by promoting any durable conclusion into Proposal 012, then delete or
  supersede `012-023` if it is redundant.

## Scope

Build the current Proposal 012 closeout map:

- starter-complete areas;
- full-closeout blockers caused by formal 018 deferrals/unsupported states;
- future out-of-scope work;
- safe next 012 issues, if any.

## Out of Scope

- Do not reopen Proposal 018.
- Do not promote Mac byte-entry, relocation/fixup, source-to-CODE, or non-CODE
  payload facts beyond their current KB states.
- Do not regenerate broad Mac target artifacts unless the audit proves a stale
  drift check requires it.

## Files Likely Touched

- `docs/proposals/012-classic-mac-os-m68k-platform.md`
- `docs/issues/012-025-post-018-closeout-blocker-map.md`
- Possibly `docs/issues/012-023-mac-platform-closeout-blocker-map.md` if it is
  deleted or marked superseded.

## Acceptance Criteria

- [ ] Proposal 012 closeout matrix is checked against current 018 KB state.
- [ ] Each remaining item is classified as starter-complete, blocked,
  deferred/future, or safe next 012 work.
- [ ] `012-023` is either deleted as redundant or explicitly superseded.
- [ ] No code/parser/rendering behavior changes are included.
- [ ] Proposal 012 records the current map durably.

## Required Tests

Docs/audit issue. Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend
git diff --check
```

Add targeted tests only if non-doc files change.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 012 records the map.

## Notes for Agents

This is a coordination issue, not a license to close 012 by assertion. It should
make the later `012-026` starter closeout decision mechanical.

