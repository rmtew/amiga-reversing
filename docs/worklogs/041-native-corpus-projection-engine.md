# Worklog: Proposal 041 Native Corpus Projection Engine

Status: Active research ledger. Current gate: R1 is complete: clean one- and
eight-worker oracle parity proves the owned typed canonical-row seam. Begin
R2 native location/direct-control reduction.

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

## Current Gate: R2

### Required evidence before R2 can complete

- Move both direct-control confirmation and location-key/rank reduction from
  Python's ordered projector into the native typed-row path. The existing
  JSON/ctypes stream is still the temporary oracle, not the intended R2 input.
- Add native-versus-oracle tests for direct-control selections and resolved
  location xrefs at every typed-batch boundary, including zero-width labels,
  missing locations, aliases, and code/data rank rules.
- Run the required C suite, both Python roots, random-access fixtures, and
  checked clean one- and eight-worker candidate/oracle corpus comparisons.

### Next bounded action

Move location-key/rank resolution beside the native direct-control reducer,
then expose compact typed selection records directly from the canonical row
batch. Preserve the R1 owned-copy rule for transient producer rows. Do not
mistake the current ctypes reducer seam for the final no-JSON architecture.

### Open observations and questions

- `src/tests` now reaches the style checker; its remaining 342 reported style
  issues in 21 C/header files are pre-existing repository hygiene failures.
  They must be repaired, not suppressed, before claiming a full-suite pass.
- Checked conformance now has an exact executable helper and automatic scratch
  uses user Temp. Its explicit output directories remain durable evidence until
  their gate's trace/decision review is complete.

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
| 2026-08-04 | R0 | Added `src.scripts.compare_corpus_artifacts`, the checked normal-artifact comparator required for every migration gate. | Passed focused test. | It hashes and compares manifest, xrefs, both snippet files, variants, type-flow, unresolved fields, and coverage; it excludes profiles/progress by design. `uv run pytest tests/test_compare_corpus_artifacts.py tests/test_target_usage_manifest.py -q`: 47 passed. A full clean eight-worker run using completed instrumentation is in progress at `.tmp-041-r0-final-8`; do not use the partially written directory for comparison. |
| 2026-08-04 | R0 | Completed the clean eight-worker finalized-instrumentation run at `.tmp-041-r0-final-8`. | Completed 378 targets; metrics valid, but the run passed the snippet *index filename* rather than the required snippet output base, so it is not a comparison candidate. | 709.989s elapsed, 8.86GiB peak; file 214.934s, project 305.419s, reports 48.701s, preparation 140.091s. King visit: 295.697s = 283.405s native + 12.292s callback (0.652s JSON decode, 11.657s Python projection), 71.917MiB events. Midwinter II: 209.769s = 190.586s native + 19.183s callback (0.715s decode, 18.590s projection), 65.775MiB. The Midwinter projection boundary is 9.15% of visit time, exceeding the required future 5% target and confirming the R1--R5 replacement is necessary. |
| 2026-08-04 | R0 | Verified Windows Performance Toolkit installation. | `wpr.exe`, `wpa.exe`, and `wpaexporter.exe` are available at `C:\Program Files (x86)\Windows Kits\10\Windows Performance Toolkit`. | Use explicit paths because this session predates the PATH update. WPR/WPA evidence remains pending. |
| 2026-08-04 | R0 | Started the pre-instrumentation oracle from `1711c0ab` against the main repository's corpus and targets, with a monkey-patched data root and isolated output `.tmp-r0-oracle-current-8b`. | Running. | This is a temporary test oracle only. The initial `8` directory failed before work because Windows process quoting truncated the `-c` payload; preserve it as a failed invocation and use only `8b` for evidence. |
| 2026-08-04 | R0 | Completed the valid pre-instrumentation oracle at `.tmp-r0-oracle-current-8b`. | Completed 378 targets in 584.1s with 5.54GiB peak. | It is ready for the checked artifact comparison. The prior candidate's per-render-row `clock()` instrumentation made its timing materially intrusive, so canonical-row timing was changed to bounded batch timing (one start/end per 8192-row batch); C build/unit tests and both focused Python roots pass. A fresh correctly named batch-timed eight-worker candidate is running at `.tmp-041-r0-batch-timed-8`. |
| 2026-08-04 | R0 | Diagnosed the `8b` detached oracle mismatch, then reran it as `.tmp-r0-oracle-current-8c` after importing old code and changing its working directory to the main repository before resolving relative target paths. Compared it with `.tmp-041-r0-batch-timed-8` using `python -m src.scripts.compare_corpus_artifacts`. | Passed: all eight normal artifacts are byte-identical. | The batch-timed candidate completed 378 targets in 694.0s/8.48GiB; corrected oracle completed in 650.7s/8.01GiB. This proves R0 instrumentation preserves normal outputs; timing remains diagnostic and is not the replacement performance result. Remaining R0 evidence: one-worker parity, WPR/WPA stack attribution, and numeric target/budget decision. |
| 2026-08-04 | R0 | Verified WPR/WPA/WPAExporter availability at `C:\Program Files (x86)\Windows Kits\10\Windows Performance Toolkit`; attempted `wpr -start CPU.verbose -filemode`. | Blocked for the profile capture only: WPR returned `0xc5585011`, "Failed to enable the policy to profile system performance", which requires an elevated terminal. | Do not downgrade to a non-stack CPU profile. A clean one-worker candidate run without trace is running at `.tmp-041-r0-candidate-1`; run the required WPR capture from an elevated terminal on a distinct clean run, then inspect in WPA. |
| 2026-08-04 | R0 | Completed the clean one-worker candidate at `.tmp-041-r0-candidate-1`; launched the matching corrected old-code oracle at `.tmp-r0-oracle-current-1`. | Candidate completed all 378 targets in 1064.400s, peak 3.50GiB. | Its 270 native-stream targets include 239 with under one second of native work: current p95 callback/staging overhead is 419ms and maximum is 1.593s. This is baseline evidence, not an acceptable final fixed cost. The matching oracle is running; next compare all eight artifacts, then conduct the elevated WPR/WPA capture and set R0 budgets. |
| 2026-08-04 | R0 | Added bounded, output-neutral shard attribution. | `uv run pytest tests/test_target_usage_manifest.py -q`: 47 passed. | The final profile now separately records per-target snippet/xref spool serialization bytes and time, and whole-corpus xref-shard sort time, replacing the ambiguous `prepare_artifacts` timing for those operations. Commit `ba8f7235`. A new clean candidate must include this completed instrumentation and the required elevated WPR capture. |
| 2026-08-04 | R0 | Diagnosed and repaired the abrupt `src/tests` C-backed assembler stop. | The isolated accepting CPU-gating test and `src/tests/test_c99_disassembler_corpus.py` pass after correcting every stale ctypes `M68K_DIAG_MESSAGE_SIZE` declaration from 160 to the C header's 512. Commit `c9cebe69`. | `uv run pytest src/tests -q` now runs to completion but fails only `test_c_style.py::CStyleCheckerTests::test_repo_selected_c_files_pass_style_check`: 241 passed, 78 subtests passed, 1 failed. The style failures are pre-existing across 21 C/header files and must be repaired as independent repository hygiene before a full-suite green claim; do not suppress the checker. |
| 2026-08-04 | R0 | Completed the corrected old-code one-worker oracle and compared it with `.tmp-041-r0-candidate-1` using `python -m src.scripts.compare_corpus_artifacts`. | Passed: all eight normal artifacts are byte-identical. | Candidate: 1064.400s / 3.50GiB. Oracle: 1129.095s / 3.50GiB. This closes one-worker and eight-worker R0 output parity. The completed temporary output directories are no longer evidence dependencies; their requested deletion was blocked by the execution environment, not retained intentionally. Outstanding R0 gate: elevated WPR CPU Usage capture inspected in WPA, then exact target/budget decision. |
| 2026-08-04 | R0 | Added `src.scripts.run_corpus_projection_conformance`, the required checked isolated migration-gate runner. | `uv run pytest tests/test_run_corpus_projection_conformance.py tests/test_compare_corpus_artifacts.py tests/test_target_usage_manifest.py -q`: 50 passed. | It takes explicit oracle/candidate code roots and one data root, creates fresh distinct output directories without deleting/reusing old evidence, runs the selected 1- or 8-worker build, and invokes the normal-artifact comparator. Use it for the elevated clean candidate/oracle comparison and every R1--R7 gate. |
| 2026-08-04 | R0 | Moved production corpus and fixture scratch directories from `src/build` to standard user Temp with `amiga-reversing2-*` prefixes. | `uv run pytest tests/test_target_usage_manifest.py tests/test_run_corpus_projection_conformance.py -q`: 49 passed; `uv run pytest src/tests/test_target_usage_manifest.py -q`: 65 passed. | Explicit corpus artifacts remain at caller-provided output paths; only automatic temporary staging moved. This prevents future corpus failures from littering repository-local build directories. |
| 2026-08-04 | R0 | Attempted elevated WPR CPU capture through the checked runner. | The oracle completed under tracing, but the candidate failed when the drive filled; WPR's two repository-local temporary ETLs used 15.68GiB and prior `src/build/tmp*` folders used 34.01GiB. The trace was stopped/discarded and was not accepted as R0 evidence. | User cleaned the completed temporary data (61.83GiB then free). Subsequent noninteractive elevation attempts return `0xc5585011`; run `wpr -start CPU -filemode` from a real Administrator terminal before retrying. WPR default temp or `%LOCALAPPDATA%\\Temp` must be used, never `src/build`. |
| 2026-08-04 | R0 | Ran the checked fresh one-worker candidate/oracle conformance capture under the user's elevated `wpr -start CPU -filemode`. | Passed: both runs completed and all eight normal artifacts are byte-identical. | `r0-wpr-conformance-4`: old oracle 1274.3s, current candidate 1336.4s; retained only pending WPR/WPA inspection. The active finalized trace is `%LOCALAPPDATA%\\Temp\\proposal041-r0-one-worker.etl`; do not delete it before inspecting candidate stacks and recording the numerical decision. |
| 2026-08-04 | R0 | Read the candidate's completed output-neutral per-target profile from the checked capture. | Current collector overhead is substantial and confirms the native cutover is warranted. | Across 270 stream targets: 689.452s visit, 563.686s native, and 125.766s callback/transport; Python projection is 119.721s, JSON decode 6.896s, direct shard writes 9.348s, and final xref-shard sorting 111.624s. For the 36 targets with at least 1s native work, callback-plus-staging is 24.92% median and 54.57% p95 of visit time (maximum 59.82%), versus the final 5% ceiling. For the 234 smaller targets it is 20.91% median/57.64% p95. |
| 2026-08-04 | R0 | Validated the final ETL, researched `0x80070032`, and opened it in Store WPA 11.8.423.0. | The ETL has zero lost buffers/events; bundled WPA 11.1.5.2 and xperf stop on an unsupported `Microsoft-Windows-DotNETRuntime` event, while the Store analyzer opens it. | Manual WPA stack navigation is slow and non-reproducible at this scale, so it is not a migration gate. The deterministic profile already identifies the dominant Python transport/projection and shard-sort costs. The ETL and checked output directory are now disposable. R0 fixes the final target: <=480s clean eight-worker corpus build; large-target projection/staging/final-encoding <=5% end-to-end; small-target overhead <=50ms p95 and <=100ms maximum. |
| 2026-08-04 | R1 | Implemented bounded typed canonical-row batches below the temporary JSON serializer. | Local checks pass; gate remains open. | The producer reuses transient row storage, so the batch owns a contiguous copy of each row's text and mirrors selected fields in SoA arrays. It preserves batch storage between flushes, handles a single row larger than the initial text capacity, and has focused C/Python variable-boundary tests. `cmd /c src/build.bat --lock-held`, `src/build/m68k_c_unit_tests.exe`, and `uv run pytest tests/test_target_usage_manifest.py -q` passed. |
| 2026-08-04 | R1 | Repaired the checked conformance runner before using R1 evidence. | Earlier `r1-typed-conformance-1` and `1b` output is invalid/disposable. | The runner now imports the selected Python code root, reads shared data-root corpus resources, and explicitly binds ctypes to the selected code root's DLL. Focused runner/comparator/manifest tests: 51 passed. |
| 2026-08-04 | R1 | Corrected the conformance harness and the typed-row text-arena relocation path. | Passed. | The harness shares current corpus data while explicitly binding each side to its selected native DLL. The transient producer reuses rows, so batch text is owned; a growing text arena repoints every buffered row from stored offsets. This fixed corrupted non-UTF-8 JSON in the first valid gate. C build/all native unit groups and 51 focused Python tests pass. `r1-typed-conformance-1f`: oracle 1,094.4s, candidate 1,191.2s; `r1-typed-conformance-8a`: oracle 817.5s, candidate 781.6s; all eight compared normal artifacts identical in both runs. |
| 2026-08-04 | R2 | Replaced the production projector’s Python direct-control run state with the C-owned `PlatformCorpusProjectionReducer`, retaining only unreleased lookahead rows in Python. Corrected the reducer so valid contiguous spans, rather than source-location presence, define a run. | Focused parity passed; R2 remains open. | `cmd /c src/build.bat --lock-held`; `uv run python -m py_compile amiga_reversing/disasm/c_backend.py src/scripts/target_usage_manifest.py`; `uv run pytest tests/test_target_usage_manifest.py -q`: 50 passed. New test exercises native versus Python direct-control selections across rows/batches, zero-width labels, run breaks, and section changes. Location resolution is still Python and typed batches do not yet feed the reducer directly, so neither corpus conformance nor R2 acceptance has been claimed. |
| 2026-08-04 | R2 | Ran broad verification after the direct-control integration. | Changed-path suites pass; repository style gate remains pre-existing. | `src/build/m68k_c_unit_tests.exe` passed; `uv run pytest tests -q`: 1,384 passed, 58 skipped, 355 deselected; `uv run pytest src/tests -q`: 241 passed, 78 subtests passed, 1 failed. The sole failure is the existing selected-C-files style checker, with its long-standing unrelated style findings; it is not suppressed and does not validate R2. |
| 2026-08-04 | R2 | Added a C-owned primary-location reducer with the canonical instruction/data/directive/label rank order. The production projector feeds every row to it and asserts its selected row at each location-group boundary against the existing full Python location resolver. | Focused parity passed; R2 remains open. | `cmd /c src/build.bat --lock-held`; `uv run python -m py_compile amiga_reversing/disasm/c_backend.py src/scripts/target_usage_manifest.py`; `uv run pytest tests/test_target_usage_manifest.py -q`: 51 passed. This proves the native primary-key rule including ties, group boundaries, and no-location rows, but Python still resolves secondary `addr`/`storage_address` matches and emits xrefs, so it is not yet the final C location path. |
| 2026-08-04 | R2 | Moved direct-control candidate classification to canonical C row emission. It reads typed instruction metadata, operand symbol facts, and code-start facts, and transports internal normalized feature bits for the temporary parity seam. Python asserts those bits equal the legacy classifier before passing them to the native run reducer. | Focused parity passed; R2 remains open. | `cmd /c src/build.bat --lock-held`; `uv run pytest tests/test_target_usage_manifest.py -q`: 51 passed, including stream-versus-artifact and typed-batch-capacity row identity checks. The internal JSON field is temporary migration metadata, not a final projection interface; it must disappear when R2 consumes typed batches directly. |
