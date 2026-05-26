# 024-009: Documented CODE Segment Layout Parser

Status: complete
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- 024-001 added `segment_loader_fixup_inventory_v1`, but it only proved that
  the current parser lacks fixup encoding byte provenance.
- That is not a final platform blocker. Classic Mac OS CODE segment and Segment
  Loader behavior is documented old technology.
- The next required work is to research the documented layout and implement the
  parser boundary that finds A5 relocation and segment relocation information in
  CODE resources where present.

## What To Build

Perform a primary-source documentation pass and implement the corresponding C
parser boundary for current Mac CODE resources.

Use Apple/MPW documentation where available. Useful starting points include
Inside Macintosh Runtime Architectures, Segment Manager documentation, and MPW
Segment Loader notes. Cite the exact document/source and summarize the relevant
layout fields in Proposal 024.

Then update the C Mac resource parser so `segment_loader_fixup_inventory_v1`
classifies records from documented CODE layout evidence, not from broad CODE
payload candidate spans.

## Acceptance Criteria

- [x] Proposal 024 cites the primary documentation used and records the specific
      CODE segment fields/offsets relevant to code bytes, A5 relocation
      information, and segment relocation information.
- [x] The C parser maps documented fields onto current CODE resource bytes where
      the fixture supports them.
- [x] Inventory records distinguish actual fixup encoding byte spans from
      executable bytes that may be affected by fixups.
- [x] Nonzero CODE resources are no longer all `custom_unknown` merely because
      the old parser lacked a layout model.
- [x] Unsupported/custom/malformed cases stay deferred with exact documented
      mismatch or blocker reason.
- [x] No decoded fixup effect is emitted until a supported encoding span and
      format are proven.
- [x] 024-002 through 024-008 are updated to the correct state after this issue:
      active if a parser boundary exists, or specifically blocked if the fixture
      uses a documented custom/unsupported variant.

## Completed Result

- Proposal 024 records the primary-source far-model and near-model CODE segment
  layout.
- C parses the documented 40-byte far-model segment header and records A5 and
  segment relocation information offsets.
- Current MPW `Asm` far-model resources have zero A5/segment relocation offsets;
  near-model resources have no relocation-info fields. The fixture therefore has
  documented absence of fixup encoding spans, not a generic parser gap.
- 024-002 through 024-008 remain blocked for this fixture until a nonzero
  documented relocation-info span or equivalent primary-source evidence exists.

## Blocked By

- docs/issues/024-001-current-fixup-byte-inventory-and-parser-boundary.md

## Required Sign-Off

- [ ] Documentation sources and exact layout findings are recorded in Proposal
      024.
- [ ] Native C unit tests cover the documented parser boundary.
- [ ] Focused Mac C/backend/project/artifact tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
