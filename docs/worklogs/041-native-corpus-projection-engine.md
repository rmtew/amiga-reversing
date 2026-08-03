# Worklog: Proposal 041 Native Corpus Projection Engine

Status: Active research ledger. Current gate: R0 -- not started.

This is the required resume ledger for
[Proposal 041](../proposals/041-native-corpus-projection-engine.md). It tracks
progress and evidence; the proposal, code, and tests remain the authoritative
sources for architecture, behavior, and acceptance.

## Resume Rules

- Read the proposal and this worklog before beginning or resuming work.
- Record the active gate, one bounded next action, and any newly relevant
  invariant before changing code.
- At each meaningful boundary, record commands, result, artifacts or benchmark
  evidence, failures, decisions, and the next action.
- Mark completed items complete or remove them. Do not leave historical work
  phrased as pending.
- A gate completes only when its proposal proof and broad verification are
  recorded here and reproducible. A focused test, benchmark, or conversation
  assertion alone is insufficient.

## Durable Invariants

- The replacement is the sole production collector after R8: no fallback,
  compatibility switch, or retained old production path.
- The legacy stream/projector is a temporary test oracle only during migration.
- C analysis and canonical rows remain authoritative; Python is not a per-row
  JSON transport, parsing, or feature-reduction runtime in the final design.
- Corpus normal artifacts remain byte-identical during migration. Any later
  schema change needs a separate explicit, atomic, repo-wide contract update.
- The web/LLM/manual-action random-access listing remains a separate consumer
  of shared C semantic/canonical foundations, never a corpus fallback or second
  semantic authority.
- Do not suppress a broad failure. Classify it, add minimal coverage if needed,
  and repair it before advancing.

## Known Reference Baseline

Proposal 040 records these prior normal eight-worker results. They are context,
not R0 completion evidence: R0 requires fresh per-stage, per-target attribution
on the current revision.

| Measure | Recorded value | Gate/status |
| --- | --- | --- |
| Peak RSS | 8.47 GiB | Proposal 040 reference |
| File phase | 256.62 s | Passed the 286.07 s gate |
| Project phase | 367.19 s | Failed the 309.87 s gate |

## Current Gate: R0

### Required evidence

- Add non-semantic timers and allocation/copy counters for semantic planning,
  canonical typed-row production, JSON construction, FFI callback time, Python
  decode/projection, shard writing, sorting, and source-byte staging.
- Run clean representative and full-corpus measurements, including King and
  other observed project-tail targets.
- Capture scheduler/stack attribution with WPR's CPU Usage profile and inspect
  it in WPA. If available, collect matching Intel VTune counter evidence only
  as a diagnostic.
- Record the irreducible native analysis/render baseline, stronger local target,
  and exact projection budget before R1. The projection/staging/final-encoding
  budget is at most 5% of end-to-end time for targets with at least one second
  of native semantic work; R0 must set the fixed-cost budget for smaller
  targets.
- Prove instrumentation does not change normal artifacts.

### Next bounded action

Locate the current corpus build timing and collector boundaries, then propose
the smallest instrumentation patch and its focused tests. Do not begin typed
batch or reducer work until R0 attribution exists.

### Open observations and questions

- No per-stage R0 attribution has been recorded yet.
- The smaller-target fixed-cost projection budget is deliberately unset until
  R0 measures the unavoidable fixed costs.
- Identify the exact clean corpus-manifest invocation and add the checked
  comparison helper with isolated output/temporary paths before R1 comparison
  gates rely on it.

## Required Verification Commands

Run these from the repository root when their affected layer changes:

```powershell
$env:UV_CACHE_DIR = 'C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'
cmd /c src\build.bat --lock-held
.\src\build\m68k_c_unit_tests.exe
uv run pytest tests -q
uv run pytest src/tests -q
```

For every R1--R7 corpus comparison, use clean distinct output and temporary
directories; run once through the temporary oracle and once through the
candidate with `--workers 1`, then repeat with `--workers 8`. Compare every
declared normal artifact and coverage output byte-for-byte using the checked
comparison helper.

## Evidence Log

No Proposal 041 gate evidence has been recorded yet.

| Date | Gate | Action and command | Result | Evidence / next action |
| --- | --- | --- | --- | --- |
| 2026-08-04 | Setup | Created required resume ledger. | Ready for R0. | Start with the R0 bounded action above. |
