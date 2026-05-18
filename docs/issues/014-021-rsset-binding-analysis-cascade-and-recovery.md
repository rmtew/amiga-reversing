Status: Investigation complete; implementation belongs to owning issues
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md
Related issues: docs/issues/014-011-app-slot-rsset-editing.md, docs/issues/014-002-durable-target-identities.md, docs/issues/014-004-command-catalog-coverage.md, docs/issues/014-005-verifier-coverage.md, docs/issues/014-006-loop-planner-command-selection.md, docs/issues/014-010-api-register-semantic-actions.md, docs/issues/014-012-structure-field-editing.md, docs/issues/014-013-correction-and-view-actions.md

Scope:
Specify numeric-displacement to RSSET binding, exploratory RSSET typing
reports, auto-analysis cascades, conflict feedback, and reversible cleanup.
This is an investigation/spec issue; production implementation stays in the
owning issues after the model is clear.

Problem:
Some base-relative values appear as raw numeric displacements even when local
evidence suggests they belong to an RSSET layout. A user or agent should be
able to bind the value to one chosen RSSET layout, optionally name/type the
field, and let analysis propagate to missed uses. That must not create unlinked
fields, silently apply incompatible platform/custom types, or leave stale
derived facts after a bad choice is undone.

Investigation result:
Add a first-class manual RSSET use-site binding fact. Do not force every raw
numeric displacement correction through immediate field creation. A binding
associates one source operand with one `(layout_name, base_symbol)` and one
displacement. Field creation/refinement is optional, verifier-gated, and owned
by the binding or by a follow-up type action so cleanup can retract only the
derived facts from that manual decision.

Chosen model:
- Bind-only: links a numeric use-site to an RSSET layout. If a field already
  exists at the displacement, the use-site can render the field symbol. If no
  field exists, the use-site remains raw or renders a linked gap marker while
  navigation/review shows the missing field.
- Bind-and-refine: creates or updates a linked RSSET field only when observed
  access width, base evidence, existing layout state, and verifier support
  reconcile.
- Type refinement: custom/platform type, parser role, enum/equate domain, or
  propagated typed field facts are separate refinement layers. They must block
  or produce review feedback when evidence is incompatible.
- Derived effects carry `owner_action_id` and `cascade_id` so unbind,
  remove-field, or clear-type actions retract only descendants of the selected
  manual action.

Owner identity:
- `owner_action_id` must be a durable Manual Action Log identity, not a row
  index, in-memory sequence number, or rendered text. Current Manual Action Log
  records already persist stable `action_id` values and reject duplicate ids on
  replay, so RSSET binding can use those action ids directly.
- A created binding action stores its own `rsset_binding_id` in the append-only
  payload. Corrective actions reference that id rather than depending on log
  position.
- `cascade_id` is derived from the owning action id plus cascade kind, for
  example `rsset_binding_id + ":selected_use"` or
  `rsset_binding_id + ":same_displacement"`. It is persisted on generated
  review items, xrefs, linked gaps, type-flow facts, and missed-use candidates.
- Replay rebuilds derived facts from append-only actions, then applies later
  removal/clear actions by matching `owner_action_id` or `cascade_id`.
- Verifiers must prove both positive projection and cleanup: generated
  descendants for one owner appear after replay, and only descendants matching
  the removed owner disappear after unbind or clear-type.

Durable identity:
- Numeric use-site identity:
  `(target, hunk, source_addr, operand_index, base_register, displacement,
  layout_name, base_symbol, base_evidence_id)`.
- `source_addr` is the instruction/source offset, not row index.
- `operand_index` must preserve zero.
- `base_evidence_id` names the register-base proof used to treat the register
  as an app/RSSET base, such as an entry register seed, library/app-base seed,
  platform inference, or selected manual binding.
- The chosen `(layout_name, base_symbol)` is part of the identity so the same
  displacement can be tested against another layout without mutating the first
  binding.

Manual Action Log actions:
- `create_manual_rsset_use_site_binding`: bind one numeric use-site to one
  layout. Payload includes durable identity, access width/kind, current
  rendered text, evidence summary, optional linked gap/review request, and
  optional field refinement.
- `remove_manual_rsset_use_site_binding`: unbind one use-site and retract
  generated descendants owned by the binding.
- `create_manual_rsset_binding_type_refinement`: apply custom/platform type,
  enum/equate domain, parser role, or propagated type-flow to a bound field.
- `remove_manual_rsset_binding_type_refinement`: clear owned type/domain
  descendants without deleting the base binding or unrelated RSSET fields.

Command catalog surface:
- `rsset.binding.report`: read-only exploratory report for a selected numeric
  base-relative operand.
- `rsset.binding.bind`: bind-only mutation.
- `rsset.binding.bind_refine`: bind plus linked RSSET field add/edit when
  verifier evidence reconciles.
- `rsset.binding.unbind`: remove selected binding and owned descendants.
- `rsset.binding.type_refine`: apply a custom/platform type or enum/equate
  domain to an existing binding.
- `rsset.binding.clear_type`: remove owned type/domain descendants.

Exploratory report fields:
- Source locator: target, hunk, source address, row text, operand index, and
  current rendered text.
- Operand facts: base register, numeric displacement, access width, access
  kind, address mode, signed displacement, and whether index/base suppression
  is present.
- Base evidence: register seed, inferred app base, platform API context,
  current confidence, and conflicting base candidates.
- Candidate layouts: `(layout_name, base_symbol)`, layout source, offset range,
  field at displacement, gap covering displacement, nearby fields, and xrefs.
- Type compatibility: observed width vs existing field size, storage kind,
  parser role, custom/platform type shape, enum/equate domain, and expected
  field path.
- Expected cascade: selected-use rendering, same-displacement missed-use
  candidates, generated xrefs, typed facts, review items, and cleanup owner.
- Verifier readiness: replay, rendered source, exact round-trip, xref,
  type-flow, removal, and missing-verifier blockers.

Projection and rendering:
- Effective metadata gains `rsset_use_site_bindings` and owned refinement
  projections.
- Bind-only projects the selected use-site into app-slot/RSSET navigation even
  when no field exists yet.
- If a field exists, selected-use rendering may switch from `$NNNN(a6)` to
  `field_name(a6)`.
- If no field exists, bind-only does not invent an unlinked `RS.*` field. It
  creates a linked gap/review item or leaves raw rendering with explicit report
  state.
- Bind-and-refine creates or updates an RSSET region only as an owned descendant
  of the binding, or by appending an existing `create_manual_rsset_layout_region`
  action with explicit binding-owner metadata.

Auto-analysis cascade:
- Same displacement + same base evidence can generate already-satisfied skips
  or planner candidates for other raw uses.
- Generated facts may include selected-use symbolic rendering, field/gap
  navigation updates, xrefs from field to uses, type-flow facts, review items
  for uncertain propagation, and missed-use candidates.
- Cascaded facts are owned by the binding/type action that produced them.
- Unbind removes selected-use rendering, generated xrefs, gap/review items, and
  missed-use candidates owned by that binding. It must not remove independently
  accepted RSSET fields or bindings from other source uses.

Conflict feedback:
- Base/layout ambiguity: block until the user/agent chooses one layout.
- Access width mismatch: block bind-and-refine, allow bind-only with review
  feedback if the base/layout evidence is otherwise strong.
- Existing field overlap or incompatible storage kind: block field update or
  require explicit replace semantics.
- Platform/custom type mismatch: block type refinement until `014-012` rendered
  typed-field verifier support exists and the type shape reconciles.
- Missing verifier: block mutation; report the owning issue.
- Round-trip risk: block any source-rendering effect.

Real target example:
GenAm has a raw byte displacement at `$0102(a6)` inside the main app RSSET
layout:

```asm
    RSSET 0
    RS.B 254
app_00FE RS.B 1
app_00FF RS.B 1
    RS.B 1
app_0101 RS.B 1
    RS.B 1
app_0103 RS.B 1
```

Current uses are raw numeric operands with no `app_slot_refs`:

```asm
sf.b $0102(a6)
tst.b $0102(a6)
st.b $0102(a6)
```

Concrete GenAm evidence:
- The current listing has nine `$0102(a6)` uses.
- All observed `$0102(a6)` uses are byte accesses: `sf.b`, `tst.b`, or `st.b`.
- Nearby offsets already render as app-slot fields, including `app_0101(a6)`
  and `app_0103(a6)`.
- The main candidate layout is `(layout_name="app",
  base_symbol="__amiga_app_base__")` from the `RSSET 0` app layout.
- `$0102` is currently a one-byte gap between `app_0101 RS.B 1` and
  `app_0103 RS.B 1`.

Expected binding result:
- `rsset.binding.report` shows one unambiguous candidate layout and a one-byte
  gap at `$0102`.
- `rsset.binding.bind` records the selected use-site and keeps raw rendering or
  linked-gap reporting until a field name is chosen.
- `rsset.binding.bind_refine` with symbol `app_0102`, size `1`, and storage
  kind `byte` creates a linked field and renders the selected use as
  `app_0102(a6)`.
- The cascade may propose the other eight `$0102(a6)` uses as already-safe
  binding candidates after the first verifier passes.
- Undo through `rsset.binding.unbind` removes selected-use rendering and any
  field/review descendants owned only by that binding, returning the selected
  source to `$0102(a6)` while leaving unrelated RSSET fields intact.

Implementation ownership:
- `014-011`: RSSET use-site binding model, Manual Action Log actions,
  effective metadata projection, command execution, selected-use rendering, and
  linked gap/field cleanup.
- `014-002`: durable identity details for numeric use-site locators,
  base-evidence ids, and any future non-MAL owner ids. Current MAL
  `action_id` values are sufficient for binding owner ids.
- `014-004`: command catalog exposure for report/bind/refine/unbind/type-clear.
- `014-005`: replay, rendered-source, removal, exact round-trip, xref, and
  type-flow verifier gates.
- `014-006`: planner feeds, already-satisfied skip behavior, and missed-use
  cascade reporting.
- `014-010`: type-flow effects from bound fields and API/register propagation.
- `014-012`: custom/platform type compatibility and rendered typed-field paths.
- `014-013`: corrective unbind/remove/clear-type semantics and stale derived
  fact cleanup.

Unsupported until follow-up implementation:
- Automatic broad binding of all matching displacements.
- Platform/custom type application without rendered typed-field verifier proof.
- Silent creation of RSSET fields from width-only evidence.
- Cleanup of derived facts that lack owner action ids.
- UI-only exploratory state as durable binding state.

Acceptance criteria:
- The issue identifies which implementation work stays in `014-011` versus
  identity/verifier/type/correction follow-ups in related issues.
- Proposal 014 matrix and RSSET row are updated with the chosen model and
  unsupported gaps.
- The investigation defines command names, Manual Action Log action names,
  durable identities, exploratory report fields, verifier expectations, and
  cleanup behavior.
- At least one real target example describes a raw displacement, candidate
  RSSET layouts, expected binding result, conflict checks, and undo result.
- No production code path is changed by this investigation-only issue.

Cleanup / deletion:
Delete after the chosen model is folded into `014-011` and related
implementation issues, with Proposal 014 updated to the final support state.
