# 017-033: Decision Journal Skeleton

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: Decision Journal durable decision model
- Current proposal state: `017-032` added a read-only RSSET evidence packet
  projection with selected identity, blockers/conflicts, render intent, and a
  blocked command gate. No accepted/deferred/rejected decisions are stored yet.
- Desired proposal state after this issue: 017 has a validated first Decision
  Journal schema and append/supersession model that can reference the RSSET
  packet shape without becoming active replay or mutation authority.

## Protocol Delta

- Adds: per-target Decision Journal record schema for `accept_fact`,
  `defer_fact`, `reject_fact`, and `supersede_decision`.
- Changes: evidence packets can be referenced by durable decision records, but
  remain read-only unless later replay work consumes those decisions.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: applying decisions to the C fact graph, replacing Manual
  Action Log, enabling RSSET mutation, rendering, command-gate activation,
  default behavior changes, legacy migration.

## Default Behavior

- Unchanged, v2 internal only: journal schema/tests must not affect current
  reports, planner, commands, render/export, Manual Action Log, or verifier
  behavior.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: none unless an explicitly internal/dev validation
  helper is added.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence packet expected: existing `017-032` packet shape is referenced by
  decision records through selected identity, candidate id, and evidence refs.
- Decision behavior: records validate structurally for accept/defer/reject and
  supersession, but are not applied to analysis or command gates yet.
- Command gate behavior: remains blocked; journal records must not expose
  `rsset.binding.bind`.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required; tests must
  prove journal validation is side-effect free.

## Implementation Slice

- C fact graph/query work: none, unless a tiny type placeholder is needed and
  documented as inactive.
- Python/API/report work: schema/validator helpers and focused tests only.
- Journal/replay work: define record shape, required fields, actor metadata,
  selected identity reference, evidence refs, conflict state, supersession
  reference shape, and validation diagnostics. Do not add active replay.
- Renderer/verifier work: none.
- Tests: schema validation for valid/invalid accept/defer/reject/supersede
  records; proof that no command gate or mutation behavior changes.

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

- [ ] Current Manual Action Log append/validation boundaries checked, or marked
  out of scope with reason.
- [ ] Decision Journal record fields mapped to `017-032` RSSET packet fields,
  or marked out of scope with reason.
- [ ] Supersession and invalid-record diagnostics shape defined, or marked out
  of scope with reason.
- [ ] Side-effect boundary checked so journal validation cannot mutate reports,
  commands, or target state, or marked out of scope with reason.

If research discovers another relevant subsystem, add it to this checklist
before continuing. The issue is not complete until the expanded checklist is
signed off or explicitly marked out of scope with reason.

## Research Review

- [ ] Second pass checked every completed trace block against the named
  files/functions.
- [ ] Cross-references searched for missed hooks, with search terms or commands
  recorded.
- [ ] Findings were checked against the current RSSET packet shape.
- [ ] Proposal updated with concrete model corrections if the journal model
  changed.
- [ ] Next issue scope follows from the journal skeleton.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Every checked research item has a trace block satisfying the Research
  Completion Standard.
- [ ] Pandora report/verifier claims include reproducible command evidence, or
  explicitly not applicable because no Pandora command claim is made.
- [ ] Decision record schema tested.
- [ ] Decision/replay behavior tested where applicable, or explicitly deferred
  because this issue defines schema only.
- [ ] Command gate refuses unsafe mutation.
- [ ] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
