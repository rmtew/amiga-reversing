# 017-034: Decision Journal JSONL IO

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: Decision Journal durable storage boundary
- Current proposal state: `017-033` added an inactive
  `evidence-decision/v1` schema and validator. No per-target journal file is
  read or written.
- Desired proposal state after this issue: 017 has append-only
  `decision_journal.jsonl` read/write helpers that validate every record and
  whole-journal chain without replaying decisions into analysis facts.

## Protocol Delta

- Adds: read, append, and whole-chain validation for per-target
  `decision_journal.jsonl`.
- Changes: Decision Journal records can become durable target-local state.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: replay into C facts, replacing Manual Action Log,
  enabling RSSET mutation, rendering, command-gate activation, UI, broad
  migration.

## Default Behavior

- Unchanged by default: no existing report, planner, command, render, verifier,
  or Manual Action Log path may start consuming Decision Journal files.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: only explicit internal/dev helpers or tests may read
  or append the journal.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence packet expected: use the `017-032` packet shape as the referenced
  evidence for sample accept/defer/reject journal records.
- Decision behavior: a valid record can be appended, read back, and validated
  as part of an append-only chain, but must not affect analysis or command
  gates.
- Command gate behavior: Pandora RSSET remains blocked after journal IO.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required; prove no
  source/render path changed.

## Implementation Slice

- C fact graph/query work: none.
- Python/API/report work: add focused file IO helpers for journal read, append,
  malformed JSONL diagnostics, and chain validation.
- Journal/replay work: append-only storage only. Do not apply accepted facts.
- Renderer/verifier work: none.
- Tests: append valid record, read back records, reject invalid append, report
  malformed JSONL, detect bad `prev`, detect duplicate IDs, preserve
  supersession validation, and prove no `manual_actions.jsonl` or command gate
  mutation occurs.

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

- [ ] Existing target-local state file handling checked.
- [ ] Current Manual Action Log append/read behavior checked for reusable IO
  patterns and replacement boundaries.
- [ ] Decision Journal schema/hash-chain behavior checked against `017-033`.
- [ ] Error/diagnostic shape for malformed JSONL and invalid records defined.
- [ ] Side-effect boundary checked so journal IO cannot mutate analysis,
  reports, commands, render output, or Manual Action Log.

If research discovers another relevant subsystem, add it to this checklist
before continuing. The issue is not complete until the expanded checklist is
signed off or explicitly marked out of scope with reason.

## Research Review

- [ ] Second pass checked every completed trace block against the named
  files/functions.
- [ ] Cross-references searched for missed hooks, with search terms or commands
  recorded.
- [ ] Findings were checked against the current RSSET packet and Decision
  Journal schema.
- [ ] Proposal updated with concrete model corrections if journal IO changes
  the protocol.
- [ ] Next issue scope follows from the implemented IO boundary.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Every checked research item has a trace block satisfying the Research
  Completion Standard.
- [ ] Pandora report/verifier claims include reproducible command evidence, or
  explicitly not applicable because no Pandora command claim is made.
- [ ] Journal IO tested for valid append/read and invalid input.
- [ ] Decision/replay behavior tested where applicable, or explicitly deferred
  because this issue stores records only.
- [ ] Command gate refuses unsafe mutation.
- [ ] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
