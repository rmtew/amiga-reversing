# Proposal 002: Reproduction Profiles and Oracle Assemblers

## Converted PRDs

- [PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)
- [PRD 019: Tool Registry and Oracle Availability](../prd/019-tool-registry-and-oracle-availability.md)
- [PRD 020: Oracle Compatibility Reports](../prd/020-oracle-compatibility-reports.md)
- [PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)
- [PRD 022: Full Reproduction Validation Sweep](../prd/022-full-reproduction-validation-sweep.md)

## TODO Coverage

- `TODO.md` Unsorted: user-selectable assembler/reproduction profiles and tool availability.
- `TODO.md` Round-Trip Validation.

## Current State

- `docs/reproduction.md` defines the current exactness gate: facts_v2 direct platform rebuild with the project assembler backend.
- `amiga_reversing/disasm/reproduction.py` already models reproduction modes, container policy, relocation policy, comparison mode, CPU, backend, and oracle modes.
- The exactness assembler set is currently `{"our"}`. `vasm` and `devpac` are modeled as oracle modes, not as exactness gates.
- `amiga_reversing/disasm/assembler_profiles.py` already loads render profiles for `vasm` and `devpac`.
- Full reproduction reports are stamped with tool inputs, assembler path, backend, metadata hash, and reproduction options.

## Clean Near-Term Work

1. Add a project-visible reproduction profile summary.
   - Show selected mode, assembler, backend, CPU, comparison, and oracle modes in the Web UI reproduction panel.
   - Surface unavailable tools explicitly instead of silently hiding options.

2. Add profile editing through target tooling commands, API, and CLI.
   - Store edits as `reproduction_options` target UI edits or structured target metadata.
   - Keep Manual Action Log for domain review facts; reproduction profile preferences are target/tooling configuration.
   - Validate values against the existing typed sets in `reproduction.py`.

3. Add an oracle availability detector.
   - Check configured paths and PATH lookup for `vasm`, GenAm, and `vamos`.
   - Return a structured availability payload: found path, version if cheap, missing reason, and whether the tool is required or optional.
   - Stamp availability inputs into reproduction reports only when the oracle is requested.

4. Keep exactness semantics strict.
   - `our` remains the only exactness gate until another assembler can reproduce the same container semantics.
   - `vasm`/`devpac` oracle modes produce separate compatibility reports.
   - A target is not `EXACT` because an oracle assembled source; exactness remains byte/semantic comparison against the configured gate.

5. Re-run full reproduction validation for GenAm and Bloodwych.
   - Produce fresh reports after renderer/refactor changes.
   - Classify diffs as full-file exact, content/relocation semantic match, or real regression.
   - Record classifications in the report or a proposal follow-up note, not ad hoc console output.

## Better Version

- Split reproduction into named profiles:
  - `exact-framework`: current direct rebuild gate.
  - `source-vasm`: render source for vasm and compare payload/container result.
  - `source-devpac`: render source for DevPac/GenAm syntax and compare output.
  - `content-semantic`: compare payload and relocation semantics when full file shape differs.
- Make profile selection target-local and reviewable.
- Add a tool registry under project config for external assembler and GenAm-through-vamos paths, separate from Manual Action Log.
- Add report sections for each requested profile so UI can show gate exactness and scoped oracle comparison levels independently.

## Larger Architecture Notes

- The direct rebuild path is a correctness gate; external assemblers are compatibility oracles.
- User preferences for assembler/tool paths should live in project or workspace config, not target metadata, unless the target requires a specific assembler profile.
- The renderer should target an assembler profile explicitly rather than relying on a global default.
- Long term, exactness would benefit from a lower-level object model that can emit canonical and original-shaped containers independently of any source assembler.

## Verification

- Unit tests for reproduction option parsing and invalid profile rejection.
- Route tests for reading/updating target reproduction profiles.
- Web/CDP tests for changing profile selections and seeing stale/re-run state.
- Full reproduction integration for GenAm and Bloodwych with reports committed or archived under `bin/rebuilt` as generated artifacts.
- Tool availability tests using fake PATH entries and missing-tool cases.

## Review Sign-Off

Reviewed against `TODO.md` and current code on 2026-05-16. Scope is coherent as proposal work; no implementation is claimed here.
