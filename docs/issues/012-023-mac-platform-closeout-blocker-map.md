# 012-023: Mac Platform Closeout Blocker Map

Status: active

## Proposal Context

- Source proposal: `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Depends on: `docs/issues/018-030-executable-kb-restart-and-state-sync.md`
- Purpose: map Proposal 012's current starter-complete areas, full-closeout
  blockers, and safe next 012 issues without touching 018-owned executable KB
  behavior.
- This issue is docs/test-audit first. Code changes are allowed only for a small
  stale test or documentation mismatch discovered during the audit.

## Scope

Produce an actionable 012 map:

- what is complete for starter Mac visibility;
- what is blocked by 018 byte-entry or relocation/fixup evidence;
- what is unblocked 012 platform work independent of 018;
- which future 012 issues can be assigned safely without conflicting with 018.

## Out of Scope

- Promoting Mac byte-entry evidence.
- Implementing classic 68K CODE relocation/fixups.
- Editing `knowledge/platform_executable_formats.json` except to report a
  blocker discovered in 018-owned work.
- Broad Mac target artifact regeneration.

## Files Likely Touched

- `docs/issues/012-023-mac-platform-closeout-blocker-map.md`
- `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Possibly small targeted tests if the audit finds stale assertions.

## Acceptance Criteria

- [ ] Proposal 012 closeout matrix is checked against current code/tests.
- [ ] Each remaining blocker is assigned to 012, 018, or future out-of-scope
  work.
- [ ] Any unblocked 012 follow-up issues are listed with safe file boundaries.
- [ ] The issue explicitly records if no useful 012 work is safe while 018 is
  active.
- [ ] No 018 behavior or KB state is changed.

## Required Tests

Run the narrow tests relevant to any files touched. For docs-only completion,
run at least:

```text
uv run python -m pytest tests\test_macos_resource_model.py tests\test_macos_source_structure.py tests\test_mac_fork_roles.py -q
uv run python -m amiga_reversing.tools.validate_018_issues
git diff --check
```

If the issue updates web/listing/artifact conclusions, add the relevant Mac
payload/artifact tests to the proof.

## Cleanup / Deletion

Delete this issue after completion only after durable conclusions are promoted
into Proposal 012.

## Notes for Agents

Do not use this issue to reopen already-verified 012-022 review findings. Do not
accept current Mac CODE byte-entry or relocation/fixup behavior as correct
unless Proposal 018 has supplied accepted evidence and the parser/listing path
consumes it.

