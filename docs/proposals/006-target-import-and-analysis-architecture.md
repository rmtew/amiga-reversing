# Proposal 006: Target Import and Analysis Architecture

## TODO Coverage

- `TODO.md` Data Structure Enumeration.
- `TODO.md` Analysis Architecture.

## Current State

- C facts_v2 analysis already handles many jump-table shapes; `docs/plan-m68k-analysis.md` records recent table-candidate cleanup and says new table work should start from newly observed unresolved C statuses.
- Python strict typing is configured for `amiga_reversing/amiga_disk`, `amiga_reversing/disasm`, and `amiga_reversing/tools`.
- `source_binary.json` is the strict source descriptor for imported targets, including raw-binary targets.
- Import tests already cover AmigaDOS and several custom/non-DOS disk scenarios, but the current product path still treats first-class custom-track/raw-track support as future work.
- Resident/autoinit parsing exists in the platform file path and generated Amiga OS runtime tables include Exec symbols, but deeper runtime-built resident/device cases remain incomplete.
- `amiga_reversing.tools.check_mojibake` is an explicit-pattern check with focused tests.

## Clean Near-Term Work

1. Keep C orchestration split only where there is a real reuse boundary.
   - Leave tightly coupled facts_v2 analysis local until a second caller needs a lower-level API.
   - Extract only stable interfaces: decoded instruction stream, recovered table records, runtime-copy evidence, structured executable facts, and review signals.

2. Add whole-target integration checks above unit tests.
   - Pick a small GenAm/Bloodwych/Damocles-style set that exercises renderer, analysis, reproduction, review blockers, and runtime-copy cases.
   - Assert visible statuses and key output facts, not giant source snapshots.

3. Keep mypy focused.
   - Maintain strict typing on Python orchestration/web/tool adapters.
   - Do not widen mypy to generated C-adjacent data dumps unless there is a stable Python contract.

4. Add raw-binary project creation as a strict UI/API flow.
   - Require binary path, load address, entrypoint, CPU/platform, and source kind.
   - Write `source_binary.json` once validation passes.
   - Do not infer load/entry for user-created raw binaries.

5. Add file-signature KB only from trusted sources.
   - Store packer/cruncher/file signatures as structured KB entries with citation and confidence.
   - Use them to report likely formats and next actions, not to silently import bytes without a loader/materialization path.
   - Keep detection absent rather than heuristic when the KB has no trusted entry.

6. Keep non-DOS loader-stage creation evidence-based.
   - Auto-create a child target only when concrete bytes, load address, and entrypoint are materialized.
   - Inferred-only spans remain review evidence, not targets.
   - Replace sector-image heuristics with raw-track/custom-loader descriptors only when the input format supports that evidence.

7. Keep external reverse-engineering facts optional.
   - Import them through a separate workflow.
   - Never require them for tests, normal rendering, precommit, or target status.
   - Preserve provenance and allow removal without changing core analysis.

8. Extend resident/device structure analysis from primary metadata.
   - Parse Exec init/vector layouts and exported function names from NDK/primary-source KB data.
   - Make labels version-aware through OS KB metadata.
   - Runtime-built resident/device targets update source only after clean direct rebuild or explicit relocation semantics.

9. Keep mojibake checking narrow.
   - Extend explicit broken-pattern tests only when a real bad encoding appears.
   - Do not add broad punctuation bans.

10. Continue jump-table work from evidence.
   - Add new pattern support only for unresolved C statuses backed by target examples.
   - Keep generic indirect calls/jumps separate from table candidates.

## Better Version

- A target-import contract separates physical media evidence, extracted file/stage bytes, load metadata, entry metadata, and user-supplied raw-binary metadata.
- Analysis facts expose a small stable C API for higher-level tools while preserving current internal ownership.
- Whole-target checks become named benchmark scenarios with expected visible status, review blockers, reproduction result, and selected recovered facts.

## Larger Architecture Notes

- The simplest viable approach is one source descriptor model per target and one evidence path into analysis facts.
- Do not add normalisation layers or compatibility adapters around target source metadata. Invalid or missing evidence should fail explicitly.
- Loader-stage targets are outputs of materialized evidence, not guesses.
- Runtime-built executable structures need relocation/lifetime provenance before being written back as source facts.

## Verification

- API and CDP tests for Add Project raw-binary creation.
- Import tests for materialized loader-stage target creation and inferred-only non-creation.
- Whole-target integration tests for selected representative targets.
- C tests for any new jump-table or resident/device parsing patterns.
- Mojibake tests for each added explicit bad sequence.

## Review Sign-Off

Reviewed against `TODO.md` and current code on 2026-05-16. Scope is coherent as proposal work; no implementation is claimed here.
