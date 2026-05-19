Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add Manual Action Log support for target-specific auto-analysis suppressions and
execution/runtime view edits that a reverser needs to fix wrong target state.
Do not use manual corrections as a substitute for fixing importer or analyzer
bugs that affect a whole class of targets.

Accepted review state:
Manual provenance overrides are correction actions. They require contradicted
evidence id, reason, path/lifetime scope, cleanup scope, and verifier proof
that only owned stale descendants were removed. Class-wide analyzer/importer
defects remain upstream bugs.

Current evidence:
- Target metadata supports `execution_views`, `absolute_code_labels`, and
  `suppressed_seeded_items`.
- `target_corrections.json` can suppress seeded items.
- Manual Action Log `suppress_seeded_item` now projects append-only
  target-specific suppressions into effective metadata for seeded entities,
  seeded code labels, and seeded code entrypoints.
- Listing rows are annotated with suppressible `target_seeded_metadata.json`
  source identities, and row command catalogs expose
  `correction.suppress_seeded_item.<kind>` for those rows.
- Manual Action Log `create_manual_execution_view` now projects target runtime
  views into replay state with `owner_action_id`; effective metadata consumes
  the view shape. `target.execution_view.add` appends it from target command
  context. `target.execution_view.edit` also emits the same name/range payload
  to replace a view by `(source_start, source_end, base_addr)`.
- Manual Action Log `remove_manual_execution_view` now removes target runtime
  views by `(source_start, source_end, base_addr)`, preserves existing view
  identity where present, stamps `cleanup_action_id`, and
  `target.execution_view.remove` appends it from target command context.
- Label commands cover some absolute labels, and execution-view add/edit/remove
  are exposed; broader correction workflows remain open.
- The loop planner now accepts explicit `target.execution_view.*` and
  `correction.suppress_seeded_item.*` command candidates, routes execution
  views through target context and seeded-item suppressions through row context,
  skips already-projected execution views/suppressions, and requires round-trip
  verification.
- Corrections must distinguish suppressing analyzer/imported facts from
  retracting descendants of a manual action. Manual-derived descendants should
  be removed by the owning corrective action; objectively wrong analyzer classes
  remain importer/analyzer bugs rather than per-target suppressions.
- Generic `run-one` now verifies `correction.suppress_seeded_item.*` execution
  by checking reloaded suppressed seeded item state rather than affected row
  metadata.
- Generic `run-one` now verifies `target.execution_view.*` execution by checking
  reloaded execution-view state, including owner/cleanup action ids, rather
  than target local-effect metadata.
- Execution-view verifier coverage now includes add/edit ownership and
  removed-view cleanup identities.
- Planner verifier summaries now report `suppressed_seeded_item` for seeded-item
  corrections and `execution_view_state` for execution-view commands.
- Provenance-backed `manual_override` writes now require and preserve cleanup
  scope, in addition to contradicted evidence id, reason, accepted source
  family/status, and path/lifetime scope. `owned_descendants` cleanup scope must
  name the same `source_evidence_id` as the contradicted evidence.
- High-level bootblock, resident, library/device, autoinit, and import
  relationship errors are usually importer/analyzer defects when they are
  objectively wrong for a class of targets. Those must stop as implementation
  bugs with regression tests, not become per-target Manual Action Log edits.
- `014-021` RSSET binding cleanup is correction-like but not analyzer
  suppression: unbind/remove/clear-type must retract only descendants owned by
  the selected manual binding or type action, leaving unrelated RSSET fields,
  analyzer-native facts, and independently accepted bindings intact.
- Post-`014-022` split: provenance manual overrides are allowed but must be
  explicit corrections, not casual edits. An override should record contradicted
  evidence, reason, path/lifetime scope, and cleanup ownership. Analyzer-class
  provenance bugs still remain implementation bugs, not target-specific
  suppressions.

Acceptance criteria:
- Target-specific suppressions/corrections and execution views have durable
  identities.
- Manual actions replay deterministically into effective metadata.
- Review/catalog commands can suppress wrong imported seeded facts and add/edit
  execution views. Seeded-item row suppression and execution-view add/edit/remove
  are exposed by durable identities, while broader reproduction/view correction
  commands remain open.
- Loop planner support covers explicit execution-view and seeded-item
  suppression command candidates.
- Verifiers prove source rendering, reproduction, and round-trip where
  applicable.
- The loop distinguishes importer/analyzer defects from target-specific manual
  suppressions and reports the former as upstream implementation blockers.
- Cleanup verifiers prove only the selected manual-derived descendants were
  retracted; unrelated analyzer-native and user-owned facts remain.
- Manual provenance overrides, when implemented by owning semantic issues, are
  distinguishable from analyzer/importer suppressions and verify scoped cleanup.
- Override boundary:
  target-local manual override is valid when evidence is path-specific,
  incomplete, or wrong only for this target/context. Analyzer/importer bug is
  indicated when the same class of fact is objectively wrong across targets or
  contradicts parser/import invariants; that should stop as implementation work
  with regression coverage, not become per-target Manual Action Log state.
- Manual provenance override actions must record contradicted evidence id,
  new source family/status, reason, path/lifetime scope, cleanup scope, and the
  owner action responsible for generated descendants. `owned_descendants`
  cleanup scope must match the contradicted evidence id. Cleanup verifier must
  remove stale descendants from the contradicted/overridden fact without
  removing analyzer-native or independently accepted facts.

Required tests:
Manual replay, command execution, source rendering, and reproduction/round-trip
tests.
