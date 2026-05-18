Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Add a read-only target workspace hygiene report. It should classify target-local
files before any agent loop mutates a target, so stale generated files,
obsolete UI/manual state, previous agent scratch, unknown files, and durable
source/import facts are not treated as equivalent.

## Out of scope

- Deleting files.
- Running target import/reimport.
- Executing reversing actions.

## Files likely touched

- `amiga_reversing/reversing_workspace.py` or equivalent
- `tests/test_reversing_workspace.py`
- Optional CLI entrypoint if a thin command surface is useful immediately.

## Acceptance criteria

- [ ] Hygiene report classifies known source/import facts as preserve.
- [ ] Hygiene report classifies generated outputs as regenerable/resettable.
- [ ] Hygiene report classifies obsolete UI/manual state as resettable.
- [ ] Hygiene report classifies agent scratch/audit files separately from durable state.
- [ ] Hygiene report names unknown files and marks the target unsafe for automated cleanup.
- [ ] Report recommends whether `continue`, `clean-run`, or `reimport` is safe.
- [ ] Report is JSON-serializable and suitable for later iteration reports.
- [ ] Report is available through a stable CLI command.
- [ ] A concrete initial allowlist inventory exists for known target-local files.

## Required tests

- [ ] Focused test for source/import fact preservation.
- [ ] Focused test for obsolete UI/manual state classification.
- [ ] Focused test for unknown file handling.
- [ ] Focused test for report JSON shape.
- [ ] Focused test for CLI report command.

## Blocked by

None - can start immediately.

## Cleanup / deletion

- Do not delete files in this slice.
- Do not classify unknown files as safe by default.

## Notes for agents

This slice is intentionally read-only. It establishes the trust boundary before
the loop can safely run on polluted `targets/<target>/` directories.
