Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Turn API, LVO, register-base, and struct-pointer semantic discoveries into
consumed source-converging actions.

Current evidence:
- `entry_register_seeds` are consumed by rendering and support `library_base`
  and `struct_ptr`.
- Command catalog exposes `semantic.library_base.<library>` helpers for A6 LVO
  contexts, using row API metadata when present and NDK library/function lookup
  otherwise.
- Command catalog exposes `semantic.register.struct_ptr` on register elements;
  execution writes a `struct_ptr` register seed with an explicit struct name.
- `semantic.lvo.*` commands append semantic hints; LVO hints for immediate
  operands now project to `_LVO*` symbol representations and render with NDK
  includes.
- `semantic.struct_offset.*` commands append semantic hints; struct-offset
  hints for immediate operands now project to NDK field symbol representations
  and render with includes.

Progress:
- Known LVO immediate constants are source-converging: Manual Action Log hint ->
  effective metadata -> rendered `_LVO*` symbol -> exact direct rebuild.
- Known struct-offset immediate constants are source-converging: Manual Action
  Log hint -> effective metadata -> rendered field symbol -> exact direct
  rebuild.
- A6 LVO library-base seeds are no longer exec-only; command execution records
  the selected library and named base struct when the NDK payload provides it.
- Register-selected struct-pointer seeds now use the existing Manual Action Log
  projection path and no longer default to `exec.library`.
- The loop planner now accepts explicit dynamic semantic command candidates for
  `semantic.library_base.*`, `semantic.lvo.*`, `semantic.struct_offset.*`,
  `semantic.equate.*`, and `semantic.register.struct_ptr`, routes them through
  selected listing element context, skips already-projected library-base and
  struct-pointer register seeds, and requires round-trip verification.
- Generic `run-one` now mines unresolved typed-access listing evidence into
  autonomous `semantic.register.struct_ptr` candidates when the same row exposes
  a selectable operand context for the base register, including memory operands
  whose register is supplied by operand metadata, skipping already-projected
  struct-pointer register seeds.
- Autonomous struct-pointer candidate skipping now reads effective target
  metadata as well as Manual Action Log projections, so seeded register-base
  facts from target metadata are not repeated.
- Generic `run-one` now verifies `semantic.register.struct_ptr` execution by
  checking the reloaded struct-pointer register seed rather than affected row
  metadata.
- Generic `run-one` now verifies `semantic.library_base.*` execution by checking
  the reloaded library-base register seed rather than affected row metadata.
- Register-seed verifiers now use the executed durable action payload as the
  expected seed before matching reloaded project state.
- Generic `run-one` now mines listing LVO API-call rows into autonomous
  `semantic.library_base.*` candidates and skips library-base seeds already in
  effective metadata or Manual Action Log projections.
- Real C listing rows now preserve the decoded base register and displacement
  on `_LVO*(a6)` symbol operand parts. Synthetic rows had `base_register`
  already, but real GenAm rows were missing it until the C JSON emitter copied
  the effective-address register from the IR.
- Generic `run-one` now pages through bounded listing windows instead of only
  sampling the first 2048 rows, so real GenAm direct LVO rows around row 8030
  can feed autonomous `semantic.library_base.*` work.
- `tests/test_agent_reversing_loop.py::test_agent_real_genam_autonomous_lvo_library_base_candidate_converges`
  proves real GenAm LVO evidence -> `semantic.library_base.exec.library` ->
  Manual Action Log register seed -> reloaded library-base state -> exact
  round-trip.
- Generic `run-one` now verifies `semantic.lvo.*`, `semantic.struct_offset.*`,
  and `semantic.equate.*` execution by checking reloaded semantic hint state
  rather than affected row metadata.
- Planner verifier summaries now name semantic state checks as
  `semantic_hint_state`, `library_base_register_seed`, or
  `struct_pointer_register_seed` instead of generic `round_trip`.
- API call semantics, evidence-scoped register lifetimes, typed field access
  semantics, and broader struct-pointer candidate generation remain open.
- Applying a struct/platform type should be able to feed type-flow analysis:
  propagated pointer/base types, rendered field paths at other references,
  interpreted field references where supported, and review items when
  propagation is uncertain or conflicts with existing facts. This must remain
  agent-visible through Manual Action Log and command catalog capabilities, not
  UI-only state. Data-block element type binding and its type-flow/review-item
  projection are owned by `014-019-data-block-type-binding-and-platform-structs.md`.
- RSSET binding type refinement from `014-021` also feeds this issue: a bound
  app/RSSET field may propagate pointer/base type facts only after the binding
  owner, base evidence, observed access width, rendered typed path, semantic
  reload, and exact round-trip are verified. Ambiguous propagation must create
  review feedback, not silent type-flow facts.

Acceptance criteria:
- Register/base identities cover entry-scoped and evidence-scoped lifetimes.
- LVO/API/struct-offset semantic choices project into effective metadata.
- Commands are available for supported libraries, registers, and struct pointer
  cases without hard-coded exec-only behavior.
- Loop planner support covers explicit semantic command candidates with
  source element context and round-trip verification.
- Verifiers prove rendered-source propagation through calls, arguments, return
  values, or stored state as applicable.

Required tests:
Register seed projection/render tests, semantic hint consumption tests, command
catalog tests, and loop verifier tests.
