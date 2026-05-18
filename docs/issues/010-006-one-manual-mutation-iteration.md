Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Teach the reversing loop harness to execute one safe manual mutation iteration
through the existing command/manual-action path. The first supported action
should be narrow, such as applying a comment or similarly low-risk command to a
locator-backed work item.

## Out of scope

- Broad autonomous iteration.
- Output-affecting classification changes.
- Support-code refactoring recommendations.
- Browser/CDP operation.

## Files likely touched

- `amiga_reversing/reversing_loop.py` or equivalent
- Existing command/manual-action service or server helper if a direct service
  seam is needed
- `tests/test_reversing_loop.py`
- `tests/test_disasm_server.py` if command execution behavior is touched

## Acceptance criteria

- [ ] Dry-run mode selects an intended command without mutating state.
- [ ] Dry-run and run mode are available through stable CLI commands.
- [ ] Run mode checks command availability before execution.
- [ ] Run mode uses `ListingRowLocator` or durable domain identity, not row text/index.
- [ ] Mutation executes through the existing command/manual-action path.
- [ ] Result includes authoritative mutation result.
- [ ] Result includes `workflow_profile`.
- [ ] Iteration report records selected work item, evidence, command, durable result, and profile.

## Required tests

- [ ] Focused dry-run test proves no mutation.
- [ ] Focused mutation test proves command path execution.
- [ ] Focused test asserts workflow profile spans are included.
- [ ] Existing command route tests if touched.

## Blocked by

- `010-005-run-identity-and-report-storage.md`

## Cleanup / deletion

- Do not introduce an agent-only mutation API.
- Do not write retired target UI state.

## Notes for agents

This is the tracer bullet for "agent can act." Keep the action safe and prove
that it follows the same path as the UI.
