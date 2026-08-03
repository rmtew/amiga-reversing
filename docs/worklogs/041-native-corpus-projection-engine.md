# Worklog: Proposal 041 Native Corpus Projection Engine

Status: Active research ledger. Current gate: R0 -- the instrumentation is
complete enough for the final clean measurements; baseline/oracle and profiling
evidence remain.

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

Run the current instrumented revision with clean one- and eight-worker outputs,
then compare every normal artifact byte-for-byte. Use the confirmed main
project virtual environment (which includes `machine68k`) for any Python
runtime dependency. Then obtain a clean pre-instrumentation oracle or checked
equivalent baseline, collect WPR CPU Usage, and set the final R0 target and
smaller-target fixed-cost budget. Do not begin typed batch or reducer work
until those R0 gaps are closed.

### Open observations and questions

- The current tracked `corpus/target_usage_*` artifacts predate the inherited
  Proposal 040 changes: their sizes differ from the clean R0 output, so they
  cannot prove instrumentation parity. A clean pre-instrumentation worktree
  build is required as the oracle.
- The full `src/tests` root currently terminates during
  `C99AssemblerCorpusTests::test_native_line_cpu_gating_accepts_expected_cases`
  without a pytest failure report. The R0 modules are not on that test's import
  path, but this is not yet proven independent; diagnose before claiming the
  relevant broad-suite gate.
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

| Date | Gate | Action and command | Result | Evidence / next action |
| --- | --- | --- | --- | --- |
| 2026-08-04 | Setup | Created required resume ledger. | Ready for R0. | Start with the R0 bounded action above. |
| 2026-08-04 | R0 | Added non-semantic source-staging, ctypes transport, JSON-decode, Python projection, event-byte/count, allocation, and per-target profile attribution. | Focused tests pass. | `uv run pytest tests/test_target_usage_manifest.py -q`: 45 passed; `uv run pytest src/tests/test_target_usage_manifest.py -q`: 65 passed. |
| 2026-08-04 | R0 | Ran `cmd /c src/build.bat --lock-held`, then `src/build/m68k_c_unit_tests.exe`, then `uv run pytest tests -q`. | Passed. | C unit suite passed; Python root: 1,376 passed, 58 skipped, 355 deselected. |
| 2026-08-04 | R0 | Clean isolated eight-worker build to `.tmp-041-r0-8` using `python -m src.scripts.target_usage_manifest build --workers 8` with every output path redirected there. | Completed all 378 stream targets (319 file + 59 project); 727.139s elapsed; 10.462GiB peak process memory. | Phases: file 196.220s, project 334.169s, reports 49.107s, artifact preparation 146.592s. Preserve command/output location until a checked benchmark helper replaces it. |
| 2026-08-04 | R0 | Inspected `.tmp-041-r0-8/target_usage_build_profile.json`. | Attribution established; R0 remains open. | King: 321.342s visit = 300.801s native + 19.553s Python projection + 1.003s JSON decode, 75.410MiB event JSON. Midwinter: 217.834s = 196.168s native + 21.029s projection + 0.759s decode, 68.970MiB. Need oracle comparison, one-worker, WPR, and target/budget decision. |
| 2026-08-04 | R0 | Ran `uv run pytest src/tests -q` and isolated the stop with `uv run pytest src/tests/test_c99_assembler_corpus.py::C99AssemblerCorpusTests::test_native_line_cpu_gating_accepts_expected_cases -vv -s`. | Process exited 1 during that C-backed test without pytest diagnostics. | Treat as unresolved broad-suite failure; reproduce/classify before R0 acceptance. |
| 2026-08-04 | R0 | Corrected the profile-output feedback loop: progress snapshots retain aggregate counters only, while detailed target profiles are written only in the final profile. Ran a second clean eight-worker build at `.tmp-041-r0-corrected-8`. | All eight normal artifacts are SHA-256-identical to `.tmp-041-r0-8`; the correction changes measurement overhead, not corpus semantics. | Corrected run: 659.984s elapsed, 8.47GiB peak; file 199.052s, project 267.950s, reports 48.384s, preparation 143.772s. King: 258.587s visit = 246.370s native + 11.570s projection + 0.661s decode. Midwinter II: 192.453s = 169.518s native + 22.230s projection + 0.834s decode. This is not a pre-instrumentation oracle. |
| 2026-08-04 | R0 | Added native canonical row-JSON and native row-callback timing, plus manifest-executable temporary-file materialization attribution. Rebuilt C and reran focused tests. | Passed. | `cmd /c src/build.bat --lock-held` and `src/build/m68k_c_unit_tests.exe` passed; `uv run pytest tests/test_target_usage_manifest.py -q`: 46 passed; `uv run pytest src/tests/test_target_usage_manifest.py -q`: 65 passed. Final clean corpus measurements must use this completed instrumentation. |
