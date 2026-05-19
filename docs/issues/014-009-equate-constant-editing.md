Status: Complete
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add target-local equate/constant add, edit, rename, remove, and use commands.

Current evidence:
- The source model supports constants/EQU.
- The command catalog can suggest `semantic.equate.*` from NDK constants.
- `create_manual_semantic_hint` now projects NDK `domain="equate"` hints with
  a known `symbol` into manual symbol representations, and rendering consumes
  them as symbolic immediates with include coverage.

Progress:
- Known NDK equate use sites are source-converging: Manual Action Log hint ->
  effective metadata -> rendered symbol -> exact direct rebuild.
- Target-local equate identities now exist as `target_equates` keyed by symbol
  name. `create_manual_target_equate`, `rename_manual_target_equate`, and
  `remove_manual_target_equate` replay into effective metadata.
- Target catalog exposes `target.equate.add/edit/rename/remove`; the loop
  accepts explicit target-equate candidates with target context, verifies
  the durable action payload against reloaded target-equate/rename/removal
  state, and requires exact round-trip.
- Target-equate semantic reload verification rejects sparse durable payloads:
  add/edit must include `name` and `value`, rename must include both old and new
  names, and removal remains keyed by `name`.
- C policy parsing now loads target-local equates before manual symbolic
  representations, emits rendered `EQU` definitions, and can render immediate
  use sites with those symbols. Focused C-backend coverage proves exact direct
  rebuild.
- Existing target-local equates are listed in C-backed navigation with
  definition/reference refs.
- Rename/remove projection now updates or prunes symbolic representations, so
  rendered source cannot retain dangling target-equate use sites.
- Planner command normalization strips report/provenance fields from
  target-equate CRUD parameter payloads, so already-satisfied checks compare
  only catalog-owned equate identity/value fields.
- Current C policy table caps target-local equates at 128 entries, matching the
  manual representation and generated runtime-ref slices used by interpreted
  data refs. Broader capacity should move this table out of the stack-heavy
  `M68kAnalysisPolicy`.

Follow-up:
- Target-local EQU definition value representation is tracked separately in
  `014-020-target-equate-value-representation.md`, so this completed issue
  remains scoped to target-local equate identity, CRUD, use-site binding, and
  rendered use-site verification.

Acceptance criteria:
- Equates have durable target-local identities.
- Manual actions replay into effective metadata and rendered source.
- Command catalog exposes add/edit/rename/remove/use operations.
- Verifier proves rendered EQU/use sites and round-trip exactness.

Required tests:
Manual action replay, command execution, source rendering, and verifier tests.

Completed evidence:
- `tests/test_manual_seed_effective_metadata.py` covers target-equate replay,
  rename propagation into symbolic representations, and remove pruning.
- `tests/test_c_backend.py` covers rendered `EQU` definitions, symbolic
  immediate use sites, C-backed equate navigation, rename rendering, remove
  fallback rendering, and exact direct rebuild.
