Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

Scope:
Teach the reversing loop to select and execute source-converging work through
the opened listing's command catalog instead of bespoke proof commands or
one-off CLI flags.

Problem:
Useful target work should start from analysis/listing evidence, ask what
commands are available for the relevant locator or durable item, and choose the
highest-value verified action. The current loop still has narrow bespoke paths
such as listing-backed comments and label rename helpers. Those are useful
building blocks, but not enough agency.

Out of scope:
Do not create a broad speculative AI planner. Do not execute output-affecting
actions without the action-specific verifier. Do not add private mutation
routes.

Files likely touched:
- `amiga_reversing/reversing_loop.py`
- `amiga_reversing/disasm/server.py` if command catalog shape needs metadata
- focused reversing-loop and workflow tests
- `docs/agents/reversing-loop.md`

Acceptance criteria:
- Loop opens listing in-process, gathers navigation/analysis facts, obtains
  command catalogs for candidate locators/items, and ranks source-converging
  actions by documented evidence.
- Selection is command-driven: the report records command id, durable target
  identity, evidence, expected rendered-source improvement, verifier, and why
  higher-ranked candidates were skipped.
- Already-satisfied candidates are skipped using projected semantic state.
- Missing command/verifier capability stops with a precise blocker instead of
  falling back to comments, scripts, or direct file writes.
- At least one non-comment, source-converging GenAm action is selected and
  verified through the loop in a focused smoke.

Required tests:
- unit test for ranking/skipping already-satisfied candidates;
- fake command-catalog test proving selection uses available commands;
- GenAm-style smoke for one non-comment action through `/commands/execute`;
- verifier failure test proving the loop stops without workaround mutation.

Cleanup / deletion:
Delete this issue after implementation, verification, proposal notes, and commit.

Notes for agents:
This is the bridge from a safe harness to an actual reversing worker. Keep it
small: use existing command/catalog contracts and add only the metadata needed
to choose real source-converging work.
