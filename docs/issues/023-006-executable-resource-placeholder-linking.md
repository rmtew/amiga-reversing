# 023-006: Executable Resource Placeholder Linking

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- 022 exposed executable-relevant resource placeholders.
- 023 requires those placeholders to be linked back to source context where
  evidence exists, rather than remaining a detached inventory.

## What To Build

Connect non-CODE executable-resource placeholders to CODE routing, fixup, or
source reference context when current evidence supports the link. Keep broad
resource payload parsing out of scope unless it is needed for source
comprehension.

## Acceptance Criteria

- [ ] Placeholder identity is stable by resource type/id/name where known.
- [ ] Linked placeholders include source reference sites when evidence exists.
- [ ] Unlinked placeholders state why no source site is known.
- [ ] Artifact/web/API output allows a reverser to move between source context
      and placeholder identity.
- [ ] Unsupported resource payloads remain placeholders, not partial decoders.

## Blocked By

- docs/issues/023-003-code0-routing-and-source-references.md
- docs/issues/023-004-segment-loader-fixup-source-records.md

## Required Sign-Off

- [ ] Baseline proof updated for linked placeholder visibility.
- [ ] Focused Mac tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `git diff --check` passes.
