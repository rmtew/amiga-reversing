Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Add the write-capable `clean-run` cleanup mode for target-local state. It should
consume the hygiene classification from `010-002`, delete only files classified
as generated, obsolete UI/manual state, or local manual state, preserve
source/import facts, preserve agent audit history, and stop on unknown files.

## Out of scope

- Reimporting targets.
- Executing reversing actions.
- Deleting unknown files.
- Deleting source/import facts.

## Files likely touched

- `amiga_reversing/reversing_workspace.py` or equivalent
- `tests/test_reversing_workspace.py`
- CLI entrypoint from `010-002`

## Acceptance criteria

- [ ] `clean-run` mode is available through the stable CLI.
- [ ] Cleanup writes a before/after cleanup report.
- [ ] Cleanup preserves source/import facts.
- [ ] Cleanup preserves agent audit history unless explicit scratch pruning is added later.
- [ ] Cleanup deletes only classified generated/obsolete/local manual state.
- [ ] Cleanup stops without deletion when unknown possible durable files exist.
- [ ] Cleanup result is JSON-serializable and suitable for iteration reports.

## Required tests

- [ ] Focused clean-run preserves source/import facts test.
- [ ] Focused clean-run deletes obsolete UI/manual state test.
- [ ] Focused clean-run deletes generated state test.
- [ ] Focused clean-run stops on unknown file test.
- [ ] Focused cleanup report before/after shape test.

## Blocked by

- `010-002-target-workspace-hygiene-report.md`

## Cleanup / deletion

- Do not implement broad recursive deletion without classification.
- Do not delete unknown files.
- Do not delete Manual Action Log history except in explicit clean-run local
  state reset.

## Notes for agents

This is the first destructive slice. Keep deletion narrow, classified, and
reported.
