# 012-024: Post-018 Status Wording Sync

Status: active

## Proposal Context

- Source proposal: `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Related proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Reopens a closeout finding from 018 review.
- Problem: Proposal 012's top status still says it is blocked on Proposal 018's
  cited knowledge layer and specifically on 018-002 supplying facts. Proposal
  018 is now closed as the executable-format KB authority; 012 remains open
  because 018 formally records Mac byte-entry, relocation/fixup,
  source-to-CODE fixture product, and non-CODE payload limits as deferred or
  unsupported.

## Scope

Update Proposal 012 wording so the top status matches the current closeout
matrix:

- 018 is complete as KB authority;
- 012 remains open/blocked for full Mac executable/CODE correctness because the
  relevant KB states are formal deferrals/unsupported boundaries;
- current Mac candidate views remain useful starter visibility, not accepted
  byte-entry or relocation correctness;
- no 018 issue files need to exist for this to be true.

## Out of Scope

- Do not change Mac parser/listing/web behavior.
- Do not promote byte-entry, relocation/fixup, source-to-CODE, or non-CODE
  payload facts.
- Do not reopen 012-022 review findings.

## Files Likely Touched

- `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Possibly this issue file only.

## Acceptance Criteria

- [ ] The top Proposal 012 status no longer says 012 is waiting for 018-002 or
  for Proposal 018 to supply facts in the future.
- [ ] The top status says 018 is complete as the KB authority but records formal
  deferrals/unsupported states that still block full 012 closeout.
- [ ] The closeout matrix and top status agree.
- [ ] No parser, target, generated, or web behavior changes are included.

## Required Tests

Docs-only issue. Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
git diff --check
```

If any tests or code are touched, run the targeted tests for those files.

## Cleanup / Deletion

Delete this issue after completion only after the corrected wording is durable
in Proposal 012.

## Notes for Agents

This is not a license to close Proposal 012. It is a wording sync so future
workers do not chase already-closed 018 issue numbers or assume 018 is still the
active blocker rather than the authority recording the blockers.

