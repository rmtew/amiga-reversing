# 018-037: MacOS Blocker Resolution or Final Deferral

Status: active

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-036-macos-executable-kb-closeout-research.md`
- Purpose: convert the 018-036 research packets into durable executable-format
  KB state, either by accepting/parser-asserting facts or by formally deferring
  unsupported facts with downstream blocker semantics.

## Knowledge Delta

For each Mac blocker from 018-036:

- add accepted or parser-asserted KB facts only when the research packet meets
  the evidence standard;
- otherwise add or update candidate/deferred/unsupported records that explain
  the missing evidence and required downstream behavior;
- ensure byte-entry and relocation/fixup states cannot be mistaken for accepted
  parser authority if they remain unresolved.

The expected useful outcome may be a formal deferral, not an implementation.

## Default Behavior

Default parser/listing/web behavior changes only when backed by accepted or
parser-asserted KB state. If facts remain deferred, current candidate visibility
may remain but accepted parser behavior must not broaden.

## Evidence Standard

All KB state changes must trace directly to 018-036 evidence packets. No
standalone promotion is allowed in this issue.

## Implementation Slice

AFK implementation/docs slice:

- update `knowledge/platform_executable_formats.json` with the resolved Mac
  fact states;
- update validation tests so accepted/candidate/deferred/unsupported boundaries
  are enforced;
- update parser/report surfaces only if needed to consume or expose the resolved
  state accurately;
- update Proposal 018 and Proposal 012 closeout notes with the downstream
  meaning.

## Research Completion Standard

This issue inherits the 018-036 research. It is complete only when every 018-036
blocker has a durable KB state and downstream parser behavior is either updated
or explicitly unchanged for a recorded reason.

## Research Coverage

- [ ] 018-036 evidence packets checked before edits.
- [ ] KB state updated or explicitly confirmed for every Mac blocker.
- [ ] Parser-use authority reviewed for every changed fact.
- [ ] Proposal 012 downstream blocker wording reviewed.
- [ ] Second-pass review checked for accidental candidate-to-accepted leakage.

## Research Review

- [ ] Byte-entry status is accepted/parser-asserted only with evidence, otherwise
  formally deferred.
- [ ] Relocation/fixup status is accepted/parser-asserted only with evidence,
  otherwise formally deferred.
- [ ] Source-to-CODE fixture state is recorded without mixing MPW/Tools/Asm with
  unrelated source examples.
- [ ] Non-CODE payload semantics do not broaden beyond cited facts.
- [ ] Tests enforce the resulting fact-state boundaries.

## Required Sign-Off

- [ ] Platform executable KB validation passes.
- [ ] Platform executable format tests pass.
- [ ] Relevant Mac parser/listing tests pass if parser/report files changed.
- [ ] Proposal 018 and Proposal 012 record the final downstream state.

