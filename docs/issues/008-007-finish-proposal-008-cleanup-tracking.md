# 008-007 Finish Proposal 008 Cleanup Tracking

Status: Done
Source proposal: `docs/proposals/008-tool-runtime-capability-graph.md`
Created: 2026-05-17

## Problem

Proposal 008 and issue tracking still contain stale mixed state after the tool
graph implementation. Slice 1 is implemented but remains unchecked in the
proposal index, and cleanup/deletion items from `008-001` are not fully
resolved.

## Scope

- Update Proposal 008 checkpoint and slice status to match current state.
- Promote durable reasoning from completed issue files into the proposal.
- Delete or archive completed issue files once their reasoning is in the
  proposal.
- Keep deferred compiler fingerprinting clearly separate from current cleanup.
- Remove stale references to flat registry concepts where they are no longer
  useful historical context.

## Acceptance Criteria

- Proposal 008 clearly distinguishes completed graph/runtime-chain work from
  deferred fingerprinting work.
- Completed issue files are not left as active work unless the project keeps an
  explicit archive convention.
- No stale TODO/checklist item implies the old flat registry still needs to be
  implemented or preserved.
- Verification commands in the proposal match current tests and CLI names.

## Verification

```text
docs-only review
search docs for stale flat-registry route/CLI wording
search docs/issues for completed active 008 issues
```

## Implementation Notes

- Proposal 008 now describes the implemented tool/runtime capability graph
  instead of saying the production model is still flat.
- Checkpoint and slice status now mark the graph/runtime/probe work complete
  while leaving compiler fingerprint fixtures explicitly deferred.
- Verification commands use the current CLI vocabulary:
  `project-capabilities` and `configure-path`.
- Completed `008-*` issue files remain in `docs/issues/` as the project issue
  archive; their statuses are `Done` or `Implemented`.

## Verified

```text
Select-String docs/proposals/008-tool-runtime-capability-graph.md for stale
route/CLI vocabulary.
Select-String docs/issues/008-*.md for active statuses.
```
