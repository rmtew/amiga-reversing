# 017-032: Read-Only RSSET Evidence Packet Query

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: read-only v2 evidence packet/query slice
- Current proposal state: `017-031` completed the architecture inventory and
  recommended RSSET `rsset-raw-a6:022E` at `s0:000006E4` as the first v2
  packet/gate slice.
- Desired proposal state after this issue: 017 has a validated first packet
  shape for selected identity, evidence lanes, blockers/conflicts, render
  intent, and blocked command-gate summary, with any model corrections recorded.

## Protocol Delta

- Adds: internal read-only v2 evidence packet/query shape for one RSSET
  selected use.
- Changes: current RSSET report evidence can be projected into a common
  protocol packet shape for the selected candidate.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: Decision Journal writes, accepted app-base evidence
  recording, source mutation, default report replacement, Manual Action Log
  cutover, broad Pandora mutation runs.

## Default Behavior

- Unchanged, v2 internal only: packet/query is read-only and must not change
  existing report, planner, command, render, or verifier behavior.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: none unless a new explicitly internal/dev report or
  test fixture is added.

## Pandora Proof

- Target candidate: `rsset-raw-a6:022E` at selected use `s0:000006E4`.
- Evidence packet expected: stable selected-use identity, candidate id,
  candidate family, evidence lanes, blockers, conflict state, render intent,
  and command-gate summary.
- Decision behavior: no accept/defer/reject write in this issue; packet may
  describe available future decisions only as read-only metadata.
- Command gate behavior: gate remains blocked because accepted app-base
  evidence, selected A6 base identity, selected-use path/lifetime scope, and
  explicit empty conflicts are missing.
- Render effect: none; render intent may be represented, but no source output
  changes.
- Verifier/round-trip: no output-affecting verification required; existing
  Pandora report/dry-run proof must show no mutation became available.

## Implementation Slice

- C fact graph/query work: add only the minimum internal query/identity support
  needed for the selected RSSET packet, or explicitly document why the first
  slice is a Python adapter over current C listing facts.
- Python/API/report work: expose or test the read-only packet shape without
  changing default reports/planner behavior.
- Journal/replay work: none, except schema placeholders for decision result
  references if needed by the packet model.
- Renderer/verifier work: none beyond proving no render/mutation path is
  exposed.
- Tests: focused tests for packet shape, selected identity stability, blocker
  mapping, conflict-state representation, and blocked command-gate summary.

## Research Completion Standard

If implementation discovers additional architecture facts, record them as trace
blocks with:

- files and functions inspected;
- call/data flow summary;
- current ownership boundary;
- protocol/v2 implication;
- reuse/replace classification where relevant;
- commands or searches used to check for missed hooks;
- open questions, or `none`.

Pandora report or verifier claims require reproducible evidence:

```text
Command:
Commit:
Target:
Key output:
Validation artifact path, or inline result block:
```

## Research Coverage

- [ ] Current RSSET report payload fields mapped to packet fields, or marked
  out of scope with reason.
- [ ] Selected identity source traced from listing/report data, or marked out
  of scope with reason.
- [ ] Blocker/conflict mapping traced, or marked out of scope with reason.
- [ ] Command-gate source traced, or marked out of scope with reason.
- [ ] C/Python ownership boundary for this first packet documented, or marked
  out of scope with reason.

If research discovers another relevant subsystem, add it to this checklist
before continuing. The issue is not complete until the expanded checklist is
signed off or explicitly marked out of scope with reason.

## Research Review

- [ ] Second pass checked every completed trace block against the named
  files/functions.
- [ ] Cross-references searched for missed hooks, with search terms or commands
  recorded.
- [ ] Findings were checked against Pandora current RSSET output with command
  output or validation artifact references.
- [ ] Proposal updated with concrete model corrections if the packet model
  changed.
- [ ] Next issue scope follows from the implemented packet slice.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Every checked research item has a trace block satisfying the Research
  Completion Standard.
- [ ] Pandora report/verifier claims include reproducible command evidence.
- [ ] Evidence packet shape tested.
- [ ] Decision/replay behavior tested where applicable, or explicitly deferred
  because this issue is read-only.
- [ ] Command gate refuses unsafe mutation.
- [ ] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
