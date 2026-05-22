# 017-035: Decision Journal Validation Surface

Status: completed

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

- [x] Existing reversing-loop command/API patterns checked.
- [x] Journal IO from `017-034` checked.
- [x] Target directory/path resolution checked.
- [x] Planner/default report hooks searched to prove no accidental activation.
- [x] Diagnostic shape checked for human/LLM/CLI usefulness.
- [x] Pandora proof path defined and recorded.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed hooks.
- [x] Proposal updated if the validation surface changes the protocol.
- [x] Next issue scope follows from the validation surface.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] `decision-journal-report` tested for missing, valid, and invalid
  journals.
- [x] `--dry-run-record` tested for valid and rejected records without writing.
- [x] CLI JSON output tested.
- [x] Decision/replay behavior explicitly deferred.
- [x] Command gate refuses unsafe mutation.
- [x] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Implementation Trace

### Reversing-Loop Command Surface

- Files and functions inspected:
  - `amiga_reversing/reversing_loop.py`
  - `main`
  - `inspect_decision_journal`
  - `_load_decision_dry_run_record`
- Call/data flow summary: `main` now registers explicit
  `decision-journal-report --target <target-id> [--dry-run-record <json-file>]`.
  The command resolves the target directory, reads the Decision Journal report,
  optionally validates one proposed record in memory, prints JSON, and exits.
  It does not call command availability, command execution, planner selection,
  rendering, verifier, or Manual Action Log paths.
- Current ownership boundary: Python CLI/API report surface only. Decision
  replay into C facts remains absent.
- Protocol/v2 implication: journal validity is now queryable by humans, LLMs,
  CLI callers, and future API wrappers without activating decisions.
- Reuse/replace classification: reuse current JSON CLI pattern; replace no
  existing report.
- Searches/commands used:
  - `Select-String -Path amiga_reversing\reversing_loop.py,amiga_reversing\disasm\server.py,tests\test_reversing_loop.py -Pattern "decision|journal|subparsers|commands|route_request|append_decision|validate_decision" -Context 2,3`
- Open questions: none.

### Journal IO And Diagnostic Shape

- Files and functions inspected:
  - `amiga_reversing/disasm/decision_journal.py`
  - `decision_journal_report`
  - `dry_run_decision_record`
  - `read_decision_journal`
  - `validate_decision_journal_records`
- Call/data flow summary: `decision_journal_report` returns `path`, `exists`,
  `valid`, `record_count`, `diagnostics`, `validation`, and `next_prev`.
  `dry_run_decision_record` validates `[existing_records, candidate]` in memory
  and returns the candidate record, status, validation, and diagnostics. It does
  not call `append_decision_record`.
- Current ownership boundary: dry-run validation is read-only and file IO is
  limited to reading the existing journal and dry-run JSON file.
- Protocol/v2 implication: invalid records and malformed journals have one
  supported diagnostic surface.
- Reuse/replace classification: extend 017-034 IO helpers; no active replay.
- Searches/commands used:
  - `Get-Content amiga_reversing\disasm\decision_journal.py`
  - `uv run python -m pytest tests\test_decision_journal.py tests\test_reversing_loop.py -q -k "decision_journal or inspect_cli_reports_json"`
- Open questions: none.

### Default Behavior Boundary

- Files and functions inspected:
  - `amiga_reversing/reversing_loop.py`
  - `inspect_target`
  - `run_one_iteration`
  - `tests/test_reversing_loop.py`
- Call/data flow summary: tests prove default `inspect` does not add or consume
  Decision Journal state, while the CLI dry-run does not write
  `decision_journal.jsonl` or `manual_actions.jsonl`. Existing planner and
  command execution paths remain unchanged.
- Current ownership boundary: explicit command only.
- Protocol/v2 implication: Decision Journal validation is available without
  silently altering mutation readiness.
- Reuse/replace classification: no old code deleted; deletion remains deferred
  until replay/cutover work.
- Searches/commands used:
  - `uv run ruff check amiga_reversing\disasm\decision_journal.py amiga_reversing\reversing_loop.py tests\test_decision_journal.py tests\test_reversing_loop.py`
- Open questions: none.

## Pandora Proof

Decision Journal report command:

```powershell
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; $target='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'; $json = uv run python -m amiga_reversing.reversing_loop decision-journal-report --target $target; $rep = $json | ConvertFrom-Json; Write-Output ('journal_exists=' + $rep.exists); Write-Output ('journal_valid=' + $rep.valid); Write-Output ('journal_record_count=' + $rep.record_count); Write-Output ('journal_next_prev=' + $rep.next_prev); Write-Output ('journal_diagnostics_count=' + $rep.diagnostics.Count); Write-Output ('journal_active_ids=' + ($rep.validation.active_decision_ids -join ',')); Write-Output ('journal_superseded_ids=' + ($rep.validation.superseded_decision_ids -join ','))
```

Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Key output:

```text
journal_exists=False
journal_valid=True
journal_record_count=0
journal_next_prev=
journal_diagnostics_count=0
journal_active_ids=
journal_superseded_ids=
```

RSSET gate command:

```powershell
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; $target='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'; $json = uv run python -m amiga_reversing.reversing_loop rsset-candidate-report --target $target; $rep = $json | ConvertFrom-Json; $top = $rep.rsset_candidate_report.candidates[0]; Write-Output ('rsset safe_to_mutate=' + $rep.safe_to_mutate); Write-Output ('top_id=' + $top.candidate_id); Write-Output ('top_status=' + $top.status); Write-Output ('top_selected_addr={0:X8}' -f $top.selected_use.addr); Write-Output ('top_missing_gates=' + ($top.missing_gates -join ',')); Write-Output ('top_accepted_base_evidence_count=' + $top.evidence_search.accepted_base_evidence_count)
```

Key output:

```text
rsset safe_to_mutate=False
top_id=rsset-raw-a6:022E
top_status=blocked
top_selected_addr=000006E4
top_missing_gates=missing_accepted_base_evidence
top_accepted_base_evidence_count=0
```

Dry-run command:

```powershell
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; $target='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'; $json = uv run python -m amiga_reversing.reversing_loop run-one --target $target --dry-run; $rep = $json | ConvertFrom-Json; Write-Output ('dry_action=' + $rep.action); Write-Output ('dry_action_result_status=' + $rep.action_result.status); Write-Output ('dry_planner_status=' + $rep.planner.status); Write-Output ('dry_next_reason=' + $rep.next.reason)
```

Key output:

```text
dry_action=
dry_action_result_status=not_run
dry_planner_status=no_candidate
dry_next_reason=no locator-backed command candidate
```

Validation:

```text
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run python -m pytest tests\test_decision_journal.py tests\test_reversing_loop.py -q -k "decision_journal or inspect_cli_reports_json"
17 passed, 323 deselected

$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'; uv run ruff check amiga_reversing\disasm\decision_journal.py amiga_reversing\reversing_loop.py tests\test_decision_journal.py tests\test_reversing_loop.py
All checks passed!
```

## Review Notes

- Decision/replay behavior: explicitly deferred; this issue validates and
  reports only.
- Render/verifier/round-trip: not applicable because no output-affecting source
  path changed.
- Next issue scope: add an explicit append command/API for validated
  accept/defer/reject records, still without replaying them into C facts.
