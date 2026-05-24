# 012-028: Mac Future Work Extraction

Status: active

## Proposal Context

- Source proposal: `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Parallel-safe after `012-025` starts.
- Purpose: separate future Mac platform work from 012 starter closeout so the
  proposal does not stay open for research that is formally deferred or outside
  starter scope.

## Scope

Extract and organize future work in Proposal 012:

- nonzero CODE byte-entry evidence;
- classic 68K CODE relocation/fixup implementation;
- source-to-CODE fixture product capture/reproduction;
- non-CODE resource payload decoders;
- MPW Asm/Link/Rez byte-for-byte roundtrip;
- overflow extents for broader fixtures, if still future-only.

Each item should say why it is not starter closeout and what evidence would
make it actionable later.

## Out of Scope

- Do not create a new proposal unless the user asks.
- Do not implement the future work.
- Do not promote candidate/deferred facts.
- Do not delete useful future context; move it into a clearer future/deferred
  section.

## Files Likely Touched

- `docs/proposals/012-classic-mac-os-m68k-platform.md`
- `docs/issues/012-028-mac-future-work-extraction.md`

## Acceptance Criteria

- [ ] Proposal 012 clearly distinguishes starter closeout from future/deferred
  Mac work.
- [ ] Each future item has an evidence requirement or activation condition.
- [ ] The proposal no longer reads as if 012 must solve all future work before
  starter closeout.
- [ ] No parser, target, generated, or web behavior changes are included.

## Required Tests

Docs-only issue. Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
git diff --check
```

If any non-doc file changes, run targeted tests for it.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 012 records the future
work split.

## Notes for Agents

This is a proposal-shaping issue. Keep it concrete and avoid proposal churn:
future work should be precise enough to become later issues, but this issue does
not create those issues unless the user asks.

