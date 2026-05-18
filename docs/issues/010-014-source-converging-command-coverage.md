Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

Scope:
Create and close a command-coverage gap list for source-converging manual edits
that a human reverser can perform and an agent must be able to perform through
the same supported command/manual-action path.

Problem:
The loop initially supported comments, then label rename was added only after an
agent fell back to a temporary script. That is the wrong failure mode. Agents
should discover missing normal-path commands before target work requires
workarounds.

Out of scope:
Do not implement every missing command in this slice. Do not add private agent
APIs or direct file mutation paths.

Files likely touched:
- `docs/agents/reversing-loop.md`
- `docs/proposals/010-agentic-reversing-loop.md`
- command catalog tests and fixtures as needed

Acceptance criteria:
- Document a command coverage matrix for source-converging work:
  labels/functions, app/global slots, code/data seeds, representations,
  immediate value representations, equate add/edit/rename, string/table
  classification, review item resolution, API/semantic notes, and comments.
- For each row, record current support status, durable target identity,
  Manual Action Log action, verifier, and known blockers.
- Create follow-up issue files for concrete unsupported but required commands.
- Update agent instructions so temporary scripts/direct metadata writes are
  explicitly invalid when a command is missing; the correct result is a command
  capability issue or implementation.

Required tests:
Docs-only if this remains a coverage/instruction slice. If helper validation is
added, run focused doc/command-catalog tests.

Cleanup / deletion:
Delete this issue after the matrix and follow-up issues are committed, and any
durable observations are promoted to the proposal.

Notes for agents:
This slice is a forcing function. It should make missing capabilities visible
before another GenAm loop falls into unsupported manual edits.
