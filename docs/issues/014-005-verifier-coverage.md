Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Define and implement verifier coverage for source-converging action families.

Out of scope:
Do not bless actions as loop-executable without an action-specific verifier.

Files likely touched:
- reversing loop verification code
- reproduction/round-trip helpers
- projection/source rendering tests
- proposal matrix

Acceptance criteria:
- Every supported action family has a verifier: semantic reload,
  projected/rendered source effect, round-trip exactness, or type-specific
  oracle.
- Verification failures name the failed layer and stop the loop.
- Output-affecting source changes require round-trip exactness or a documented
  unavailable-oracle stop.

Required tests:
Positive and negative verifier tests for each implemented action family.

Current evidence:
- Generic output-affecting manual mutations now run a round-trip verification
  layer after command execution, instead of only checking that a round-trip
  verifier is available before execution.
- Target-context mutations now use `/commands/execute` local effects as their
  projection verifier instead of requiring row affected-locator metadata.
- Target-context projection verification now requires a command-specific local
  effect kind and matching parameter payload, so unrelated local effects cannot
  satisfy the verifier.
- Seeded data-symbol rename has rendered definition-name plus exact
  direct-rebuild coverage in
  `test_real_dll_manual_data_symbol_rename_updates_rendered_seeded_entity`.
- Ordinary data-row symbol rename has rendered definition-name plus exact
  direct-rebuild coverage in
  `test_real_dll_manual_data_symbol_rename_renders_ordinary_data_row`.
- Data-symbol rename has rendered instruction use-site plus exact direct-rebuild
  coverage in
  `test_real_dll_manual_data_symbol_rename_updates_rendered_use_site`.
- Seeded data-symbol removal has rendered suppression plus exact direct-rebuild
  coverage in
  `test_real_dll_manual_data_symbol_remove_suppresses_rendered_seeded_entity`.
- Generic `run-one` `label.rename` execution now uses the label-specific
  verifier: Manual Action Log match, semantic label reload, projected label row,
  and exact round-trip.
- Generic `run-one` `comment.edit` execution now uses the projected-comment
  verifier instead of accepting affected-locator metadata alone.
- Generic `run-one` `data_symbol.rename` execution now verifies Manual Action
  Log replay, semantic reload, projected listing text/name, and exact
  round-trip instead of accepting affected-locator metadata alone.
- Generic `run-one` `data_symbol.remove` execution now verifies Manual Action
  Log replay, reloaded suppressed seeded item state, and exact round-trip
  instead of accepting affected-locator metadata alone.
- Generic `run-one` `correction.suppress_seeded_item.*` execution now verifies
  Manual Action Log replay, reloaded suppressed seeded item state, and exact
  round-trip instead of accepting affected-locator metadata alone.
- Generic `run-one` `target.execution_view.*` execution now verifies Manual
  Action Log replay, reloaded execution-view state, and exact round-trip instead
  of accepting target local-effect metadata alone.
- Planner verifier summaries now report `projected_data_symbol_name` for
  `data_symbol.rename` and `suppressed_seeded_item` for `data_symbol.remove`.
- Planner verifier summaries now report `suppressed_seeded_item` for seeded-item
  corrections and `execution_view_state` for execution-view commands.
- Planner verifier summaries now report `semantic_hint_state`,
  `library_base_register_seed`, and `struct_pointer_register_seed` for semantic
  hint/register-seed command families instead of generic `round_trip`.
- Generic `run-one` `target.equate.*` execution now verifies Manual Action Log
  replay, reloaded target-equate/rename/removal state, and exact round-trip
  instead of accepting target local-effect metadata alone.
- Target-equate verifiers derive the expected equate from the executed durable
  action payload, so matching project state plus a local-effect echo cannot hide
  a missing or mismatched action result.
- Generic `run-one` `semantic.register.struct_ptr` execution now verifies
  Manual Action Log replay, reloaded struct-pointer register seed, and exact
  round-trip instead of accepting affected-locator metadata alone.
- Generic `run-one` `semantic.library_base.*` execution now verifies Manual
  Action Log replay, reloaded library-base register seed, and exact round-trip
  instead of accepting affected-locator metadata alone.
- Register-seed verifiers now derive the expected seed from the executed
  durable action payload, so matching project state alone cannot satisfy a
  missing or mismatched action result.
- Generic `run-one` `semantic.lvo.*`, `semantic.struct_offset.*`, and
  `semantic.equate.*` execution now verifies Manual Action Log replay, reloaded
  semantic hint state, and exact round-trip instead of accepting affected-row
  metadata alone.

Cleanup / deletion:
Delete after the verifier column in the matrix has no unspecified supported
actions.
