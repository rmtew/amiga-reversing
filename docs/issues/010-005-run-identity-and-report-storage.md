Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Add explicit agent run identity and report storage for reversing loop work.
Reports should have append-only history plus an atomic latest report, keyed by
`run_id`, so `/goal` can resume or inspect progress without relying on chat
history.

## Out of scope

- Executing mutations.
- Adding new candidate types.
- Browser/CDP behavior.

## Files likely touched

- `amiga_reversing/reversing_loop.py` or equivalent
- `amiga_reversing/reversing_workspace.py` or equivalent
- `tests/test_reversing_loop.py`
- `tests/test_reversing_workspace.py`

## Acceptance criteria

- [ ] Run state includes `run_id`, `target_id`, mode, status, last iteration id, and report paths.
- [ ] Iteration history is append-only.
- [ ] Latest report writes are atomic.
- [ ] `continue` mode can resume a complete non-terminal run.
- [ ] Partial iteration state is reported and rejected or requires an explicit new run.
- [ ] `clean-run` and `reimport` start new run ids.
- [ ] Rollback policy is represented in docs/report semantics: corrective action or clean-run/reimport, not silent history deletion.

## Required tests

- [ ] Focused run id creation test.
- [ ] Focused append-only history test.
- [ ] Focused atomic latest write behavior test.
- [ ] Focused resume complete run test.
- [ ] Focused partial iteration rejection/report test.

## Blocked by

- `010-004-reversing-loop-read-only-report.md`

## Cleanup / deletion

- Avoid overwriting history.
- Avoid using chat/session memory as run state.

## Notes for agents

This slice makes long-running `/goal` work resumable and auditable.
