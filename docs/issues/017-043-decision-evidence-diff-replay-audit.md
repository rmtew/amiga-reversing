# 017-043: Decision Evidence Diff/Replay Audit

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: Decision Journal auditability after replay and semantic reload
- Blocked by: none after `017-040`
- Current proposal state: Decision Journal IO, validation, projection, RSSET
  evidence lanes, and one selected mutation path exist. Reviewers still need a
  protocol-level audit view that explains decision inputs, active/superseded
  state, replay result, and verifier effects without reverse-engineering
  several reports by hand.
- Desired proposal state after this issue: decision journal reports can show a
  compact diff/replay audit for selected decisions and explain whether each
  decision is active, stale, superseded, blocked, or source-effective.

## Protocol Delta

- Adds: decision evidence diff/replay audit packet.
- Changes: journal reports expose decision input evidence, replay classification,
  semantic reload status, source effect, verifier layers, and stale/superseded
  reasons in one protocol-shaped result.
- Replaces: ad hoc manual comparison across journal report, inspect report, and
  verifier output for supported selected decisions.
- Deletes: none unless a replaced temporary diagnostic surface is fully
  redundant.
- Leaves out of scope: UI, broad automatic decision acceptance, and new source
  mutations.

## Default Behavior

- Report-only audit must not append to `decision_journal.jsonl`.
- Report-only audit must not append to Manual Action Log.
- Planner/default mutation behavior must remain unchanged.

## Evidence Standard

The audit packet must show:

- decision id, action, fact type, candidate id, selected identity, and scope;
- active, superseded, rejected, deferred, stale, or malformed state;
- evidence refs and whether referenced packet identities still match;
- replay result after current semantic reload;
- rendered-source effect where a supported source-affecting decision exists;
- verifier layers and exact round-trip status where applicable;
- blockers that prevent replay, render, or mutation.

## Pandora Proof

- Use the real Pandora RSSET accept from `017-040` and binding from `017-039` as
  the primary audit case.
- Show the active accepted decision and its source-effective replay result.
- Include at least one synthetic or fixture stale/superseded/rejected/deferred
  decision in tests so the audit cannot treat all journal records as active.
- Do not mutate Pandora.

## Implementation Slice

- C fact graph/query work: none unless semantic reload needs a narrow query to
  prove current replay state.
- Python/API/report work: add the audit surface to the journal/report command or
  inspect evidence packet output.
- Journal/replay work: reuse active/superseded projection and add audit fields
  without changing append semantics.
- Renderer/verifier work: reference existing verifier outputs where available;
  report missing verifier gates instead of running mutation.
- Tests/proof: active RSSET audit, stale/superseded/rejected/deferred cases,
  malformed journal safety, no append, no planner mutation.

## Research Completion Standard

Record trace blocks for Decision Journal IO, projection, semantic reload,
existing verifier outputs, RSSET source-effective example, stale/superseded
handling, and report/API surface.

## Research Coverage

- [x] Decision Journal report and projection checked.
- [x] Active/superseded/rejected/deferred semantics checked.
- [ ] Semantic reload and current fact comparison path checked.
- [ ] Existing verifier layer outputs checked.
- [x] No-append/no-mutation behavior checked.
- [x] Pandora RSSET audit proof planned.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed journal/report hooks.
- [ ] Audit output reviewed for report-private model drift.
- [x] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Audit packet shape tested.
- [x] No append/no mutation behavior tested.
- [x] Pandora proof recorded.
- [ ] Audit source-effect and verifier layers are based on real replay/current
  semantic state, not fact-type inference.
- [ ] Public CLI/API/report audit output is tested at the supported boundary.
- [ ] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Added `audit` to `decision_journal_report`, with per-decision state,
  evidence-ref identity matching, replay classification, rendered-source effect,
  verifier layers, and blockers. The audit reads journal state only.
- Pandora proof: `decision-rsset-022e-accept-017-040` reported as `active`,
  replay `source_effective` / semantic reload `projected`, rendered-source
  effect `selected RSSET operand can be bound through rsset.binding.bind`, and
  verifier layers `decision_journal`, `semantic_reload`, `generated_source`,
  and `exact_round_trip`.
- Fixture coverage classifies active, superseded, deferred, and rejected
  decisions, and existing report tests prove `decision-journal-report` does not
  append to the Decision Journal or Manual Action Log.
- Verification: focused 369-test pytest run and changed-file `ruff check` both
  passed.

## Reopen Findings

- The audit currently infers `source_effective` for active
  `fact_type=rsset_app_base` accepts. Completion requires replay/current
  semantic-state evidence and real verifier-layer status, or explicit blockers
  when those checks are unavailable.
- The audit must not report generated-source or exact-round-trip layers as
  available/passed/required from inference alone. It must distinguish proven,
  unavailable, blocked, and not-applicable states.
- The supported `decision-journal-report`/API boundary must be tested, not only
  private audit helper behavior.
