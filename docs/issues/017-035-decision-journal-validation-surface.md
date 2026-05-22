# 017-035: Decision Journal Validation Surface

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: explicit actor/tool interaction with Decision Journal records
- Blocked by: `017-034`
- Current proposal state: Decision Journal records can be validated in memory,
  and `017-034` made them durable target-local state through explicit
  `decision_journal.jsonl` read/append helpers.
- Desired proposal state after this issue: a human, LLM, CLI caller, or API
  caller can inspect and validate journal state without replaying or applying
  any decision.

## Protocol Delta

- Adds: explicit validation/inspection surface for the per-target Decision
  Journal.
- Changes: journal validity becomes queryable through a supported tool/API
  boundary instead of test-only helpers.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: active replay, C fact mutation, RSSET bind command
  activation, rendering, UI.

## Default Behavior

- Existing default reports/planner/render/verifier behavior remains unchanged.
- The new surface must be explicit: no automatic planner use and no implicit
  mutation during target load.
- Command name: add `decision-journal-report` to
  `python -m amiga_reversing.reversing_loop`.
- Required arguments: `--target <target-id>`.
- Optional arguments: `--dry-run-record <json-file>` to validate a proposed
  single decision record against the current journal chain without writing it.

## Output Contract

The command output must be JSON and stable enough for a human, LLM, CLI caller,
or future API wrapper to consume. It should include:

- `target_id`: requested target id.
- `path`: resolved `decision_journal.jsonl` path.
- `exists`: whether the journal file exists.
- `valid`: whole report validity.
- `record_count`: parsed valid-object record count.
- `diagnostics`: malformed JSONL and whole-chain diagnostics.
- `validation`: whole-chain validation result, including active and superseded
  decision ids.
- `next_prev`: `null` for an empty journal, otherwise the `sha256:<hash>` value
  a caller should place in the next record.
- `dry_run_record`: omitted unless `--dry-run-record` is provided; when present,
  it must include the loaded record, `status` (`valid` or `rejected`), and the
  validation/diagnostics for appending that record to the current chain.

The dry-run surface must not call `append_decision_record`; it validates the
candidate appended chain in memory only.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: `decision-journal-report` reports journal state, active
  decision IDs, superseded decision IDs, malformed records, and `next_prev`.
- Decision behavior: `--dry-run-record` can explain accept/defer/reject record
  validity without appending it or applying it.
- Command gate behavior: `rsset.binding.bind` remains blocked.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required.

## Implementation Slice

- C fact graph/query work: none.
- Python/API/report work: expose journal validation through
  `reversing_loop decision-journal-report`.
- Journal/replay work: validation/inspection only.
- Renderer/verifier work: none.
- Tests: focused coverage for missing journal report, valid journal report,
  invalid/malformed journal report, dry-run candidate record validation,
  dry-run rejection without writing, CLI JSON output, and no default behavior
  change.

## Research Completion Standard

Record trace blocks for inspected command/API surfaces, journal IO helpers,
planner/default behavior paths, target path resolution, and any relevant
Pandora proof commands.

## Research Coverage

- [ ] Existing reversing-loop command/API patterns checked.
- [ ] Journal IO from `017-034` checked.
- [ ] Target directory/path resolution checked.
- [ ] Planner/default report hooks searched to prove no accidental activation.
- [ ] Diagnostic shape checked for human/LLM/CLI usefulness.
- [ ] Pandora proof path defined and recorded.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed hooks.
- [ ] Proposal updated if the validation surface changes the protocol.
- [ ] Next issue scope follows from the validation surface.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] `decision-journal-report` tested for missing, valid, and invalid
  journals.
- [ ] `--dry-run-record` tested for valid and rejected records without writing.
- [ ] CLI JSON output tested.
- [ ] Decision/replay behavior explicitly deferred.
- [ ] Command gate refuses unsafe mutation.
- [ ] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
