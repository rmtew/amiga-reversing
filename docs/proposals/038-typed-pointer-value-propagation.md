# Proposal 038: Typed Pointer-Value Propagation and Symbolic Access Recovery

Status: In progress. Depends on Proposal 039 for corpus audit coverage.

## Problem

The analysis can know that a destination is a typed pointer field while still
treating an immediate written to it as an untyped scalar. For example, the
Pandora instruction:

```asm
move.l #$5CF4C,world_object_shared_prefix_interaction_message_ptr(a5)
```

writes a value to a known pointer field, yet the immediate can remain numeric
instead of being represented as an address to the corresponding source object.
That loses an object-graph edge, prevents typed propagation through later
loads/copies, and leaves the reconstructed source less meaningful than the
evidence permits.

This is a general analysis and rendering gap. It must not be fixed by naming
individual immediates, special-casing `world_object`, or adding renderer
fallbacks.

## Goal

Make a typed pointer destination a first-class semantic constraint on values
written to it. When a concrete immediate, relocation, or copied value is
stored into a proven pointer field, analysis must create an address-valued
fact with the field's pointee domain, propagate that fact through valid data
flow, and render it symbolically when it maps to representable source storage.

```text
typed pointer field + value-producing instruction
  -> typed address-value fact with provenance
  -> register / stack / global / field propagation
  -> concrete source target resolution
  -> Proposal 037 planned symbolic expression and declaration
  -> rendered source and source-quality evidence
```

No compatibility path, target-specific exception, or numeric fallback may hide
a failed symbolic representation of a value that analysis has classified as a
renderable typed pointer. Such a failure is an export diagnostic. Immediates
without pointer semantics remain numeric by an explicit semantic decision;
they are not speculative pointers.

### Main-task boundary

This proposal preserves proven address identity and pointee domain from value
creation through valid analysis transfer rules to a frozen render plan. It is
not a renderer-side operand rewrite: rendering consumes the planned expression
and must not rediscover pointer meaning from instruction text.

The completed path includes a direct source pointer, its lossless register and
storage transfers, a later reload, and at least one typed consumer or indirect
callback use when the relevant contract is proven. It deliberately stops when
identity, target mapping, a call contract, or a control-flow merge is not
proven. That boundary makes unknown and ambiguous values durable analysis
states rather than candidates for a numeric or symbolic fallback.

While implementing the main task, maintain the deferred-extension section
below. When analysis encounters an indexed address, interior pointer, alias,
call/return contract, callback signature, table indirection, or composite
layout concern beyond this boundary, record the concrete evidence, the current
safe stop condition, the required fact/model extension, and its relationship
to the address-value representation. Do not silently expand 038 or work
around the concern in rendering; refine the corresponding deferred task so a
subsequent proposal can implement it cleanly.

## Semantic Model

### Address-valued facts

Introduce one durable address-value representation used by both analysis and
render planning. It records:

- value origin: immediate, relocation, register, stack slot, static/global
  slot, pointer field, return value, or table element;
- address value or source/runtime mapping, addend, and address domain;
- pointee type/domain and pointer width;
- producing instruction and destination storage identity; and
- confidence and the complete chain of propagation provenance.

A pointer value is distinct from a numeric constant even when both have the
same bits. It is created only when a proven destination/producer contract
requires a pointer: a typed field, typed slot, known API parameter or return,
typed table element, relocation, or existing address-value fact.

### Writes and propagation

The analyser must interpret writes before discarding immediate semantics:

1. Resolve the destination storage and its declared type.
2. If it is a pointer field, classify a compatible produced value as an
   address-valued fact in the field's pointee domain.
3. Resolve a source or runtime target only through the normal address mapping
   and ownership model.
4. Propagate the value through lossless register copies, address formation,
   stack/global stores and reloads, typed field loads/stores, and known
   function/API contracts.
5. Merge only equivalent address values and compatible pointee domains.

Conflicting values or incompatible types produce an explicit ambiguous value
state. Unknown calls and clobbers invalidate the affected propagated state.
No value is retained merely because its bit pattern looks address-like.

### Rendering closure

Proposal 037 owns rendering closure. This proposal supplies semantic
address-value facts and asks the shared resolver for a planned expression.

- A mapped, representable target produces one planned symbolic expression and
  a canonical planned declaration if it targets source storage.
- An unmapped external/runtime-only pointer remains an explicitly classified
  non-source value with its reason; it does not invent source storage.
- A contradictory promise to render a source pointer is an invalid plan and
  refuses export. It cannot silently become a numeric operand.

Renderers do not infer pointer meaning from an immediate. They consume the
typed address-value fact and the frozen render plan.

## Framework Changes

1. Replace scalar-only immediate handling at typed destinations with the
   address-value model.
2. Extend typed-flow state, joins, invalidation, and provenance export to
   carry address values and pointee domains across registers, stack slots,
   globals, fields, table elements, calls, and returns.
3. Make the source-analysis export expose these facts and their producer/
   consumer chain without relying on rendered text.
4. Teach the shared symbolic resolver to consume address-value facts for
   instructions, relocations, structured fields, and chained lookups.
5. Add normal Manual Action command support only where a reviewer must supply
   a missing durable type/field contract. Manual actions record the contract,
   never a one-off instruction rendering.
6. Remove any old scalar-immediate special cases made redundant by the common
   typed address-value path.

The address-value fact is a pre-render analysis fact. It is available to
typed-flow reporting, object/data xrefs, field and table consumers, and
indirect-call/callback recovery before render planning consumes it. No second
renderer-only pointer inference path may be introduced.

## Corpus Opportunity Audit

Start implementation with a fresh indexed-corpus audit. The existing pointer
store facts and type-flow reports already expose much of the needed evidence,
but the corpus must gain a first-class, stable row for this proposal's complete
opportunity shape:

```text
typed pointer destination
  + address-valued producer
  + target-resolution result
  + render result
  + downstream propagation summary
```

Each row must identify the source/target by stable corpus identity and include:

- source kind: immediate, relocation, register, stack, field, return value,
  or table element;
- destination kind: struct field, app slot, absolute slot, or stack
  parameter, with its declared pointee domain;
- resolution: resolved, finite candidates, ambiguous, invalid, external, or
  no proven pointer contract;
- render outcome: symbolic, explicitly non-source, or invalid;
- propagation depth and terminal reason; and
- whether the record is a positive fixture candidate, a negative scalar case,
  or an unresolved review opportunity.

The audit is a measurement and fixture-selection surface, not an automatic
mutation mechanism. It must not create labels, types, Manual Actions, or
source changes. Corpus rows are derived from durable analysis facts and retain
the provenance needed to reproduce their classification.

Regenerate the corpus before implementation and save its aggregate counts and
representative stable rows as the Proposal 038 baseline. Use observed rows as
real-target regression and integration evidence; do not treat a category's
absence as evidence that it has no valid semantics, because a target may lack
the durable pointer contract needed to emit it. Select focused C fixtures for
the complete source/destination/propagation matrix, including categories not
yet observed in the corpus, and select Pandora only as one proof target.
Regenerate the same report after each major slice and report both resolved
gains and any new invalid/ambiguous cases.

### Superseded pre-039 baseline — 2026-07-28

A fresh, read-only full corpus build completed with 428 entries, 3,734,243
xrefs, 582,446 listing snippet rows, 230 type-flow report rows, and 56
unresolved typed-field rows. The typed-pointer opportunity report found:

```text
typed pointer-store rows: 0
targets with a pointer-store row: 0
source/destination/resolution/render/provenance categories: none
```

This is a meaningful baseline, not a zero-opportunity claim. The current
indexed corpus does not emit any `pointer_store` analysis fact for its
analysed executable inputs. Pandora is present as a derived raw-binary project
target, but that project-target catalog row deliberately records reproduction
and decompression metadata only; it does not run source analysis over the
reconstructed target. Therefore this corpus cannot yet supply the positive,
propagated, external, ambiguous, or scalar-negative fixture candidates required
by this proposal.

The audit command itself is intentionally derived and read-only. It records a
stable xref/listing locator when a pointer-store fact exists and streams the
xref artifact, so reporting remains bounded for a full corpus. It does not
create labels, types, Manual Actions, or source output.

Before implementation may claim corpus coverage, Proposal 039 must provide the
normal corpus analysis input model: analysable reconstructed project targets
and typed pointer-store facts must reach the common corpus stream. That is a
general source-analysis path with the same durable facts as executable inputs,
not a Pandora export, a manual fixture injection, or an inferred operand-text
scan. After that dependency is complete, regenerate this baseline and select
the required fixture categories from observed rows.

### Post-039 corpus baseline — 2026-07-28

Proposal 039 is complete and the fresh full corpus now includes reconstructed
raw-binary project targets in normal source analysis. The read-only
pointer-value opportunity report now contains 45 typed pointer-store rows for
one target (Pandora):

```text
source kinds: immediate 4, propagated 41
destination kinds: app_slot 24, struct_field 21
resolution: resolved 25, finite_candidate_targets 2, unknown_target 18
render outcome: symbolic_now 4, needs_address_value_propagation 21,
                not_symbolic 20
```

This is the implementation baseline for this proposal. It proves that the
common audit stream now carries observed positive opportunities, including the
Pandora world-object pointer-store class, without a target-specific corpus
path. It does not cover every semantic category: the current corpus has no
emitted relocation, stack, return-value, scalar-negative, or conflicting-join
pointer-store fixture. Those gaps are missing durable input contracts, not
negative evidence. Focused C fixtures must cover the full semantic matrix;
observed corpus rows remain the real-target integration and regression set.

### Post-implementation corpus audit — 2026-07-28

The same full, read-only build completed after the address-value implementation:
378 analysed inputs (319 file entries and 59 reconstructed project targets),
45 Pandora pointer-store rows, and stable xref identities for every row. The
source/destination/resolution counts are unchanged because this work preserves
analysis facts rather than inventing target evidence. Their producer facts are
now explicit:

```text
immediate provenance and renderable producer expression: 4
other provenance: unknown 28, field_pointer 9, app_slot 3, static_data 1
render outcome: symbolic_now 4, needs_address_value_propagation 21,
                not_symbolic 20
```

The four `symbolic_now` rows are the four direct immediate pointer stores.
They now expose `provenance_kind: immediate`, `provenance_operand_index: 0`,
and `has_renderable_source_expression: true`; this includes Pandora's
`interaction_message_ptr` store at stable key `s0:0004D3D2:instruction`.
The remaining propagated stores retain their actual non-immediate provenance
and remain non-symbolic when no renderable producer expression is proven. They
are unresolved review opportunities, not numeric renderer fallbacks.

Pandora also supplies the required downstream proof: `interact_with_chemist`
writes `abs_0_0005CF4C` to
`world_object_shared_prefix_interaction_message_ptr(a5)`, then transfers to
`interact_with_hooligan_or_robomechanic`, which reloads that typed field into
`a0` and passes it to `enqueue_status_message`. This is a field-store/reload/
typed-call-consumer chain; the direct producer is rendered only at its proven
immediate origin.

## Pandora Proof Scope

Use the world-object interaction/callback swath as the first proof, beginning
with `world_object_shared_prefix_interaction_data_ptr` in
`interact_with_chemist` and following its stores, reloads, consumers, and
indirect callback uses. Establish the target object/range only from existing
mapping, xrefs, and typed-flow evidence; do not manufacture a name because an
immediate is present.

The proof must demonstrate both a direct typed pointer store and at least one
subsequent propagated use. It must remain valid for other pointer-field types
without code changes.

## Acceptance Criteria

- Proposal 039's corpus coverage and observability acceptance criteria pass
  before this proposal claims corpus audit coverage or selects corpus fixtures.
- A fresh corpus baseline and post-change report expose the typed-pointer
  opportunity rows above, with stable identity, provenance, aggregate counts,
  and no source mutation side effect.
- The corpus audit records every observed pointer-store opportunity with its
  stable identity and classification. A category omitted because no analysed
  target has the required durable contract is reported as unavailable, never
  treated as a negative case or used to narrow the implementation.
- Focused C fixtures cover representative positive, negative-scalar, external,
  ambiguous, and propagated cases. Corpus rows are selected as real-target
  integration cases where available, rather than requiring the corpus alone to
  supply every category or relying solely on Pandora.
- Focused C fixtures cover a typed pointer-field immediate store, relocation
  pointer store, register copy, stack/global round trip, typed field reload,
  compatible and conflicting joins, call clobbering, and a chained lookup.
- The deferred-extension section is updated as relevant bounded-analysis
  concerns are encountered, with concrete trigger evidence and the required
  future model change; it contains no renderer workaround or unreviewed scope
  expansion of this proposal.
- A scalar immediate written to a non-pointer field remains numeric and creates
  no address-value fact or label obligation.
- A pointer-like immediate with no proven pointer contract remains numeric for
  an explicit reason; no heuristic address guessing is introduced.
- A mapped typed pointer produces a durable address-value fact with provenance,
  one planned symbolic expression, and a canonical declared source target.
- A typed pointer whose promised source target cannot be represented fails
  source export with a diagnostic; it does not regress to a numeric fallback.
- Address-valued facts propagate only through valid transfer rules and are
  invalidated by conflicts and clobbers.
- Renderer/source-quality evidence comes from the planned expression, not from
  a separate typed-flow-to-label path.
- Pandora renders the verified world-object pointer store as the planned source
  expression and follows the same address-value fact through at least one
  downstream reload and typed consumer or proven callback use.
- Pandora has no duplicate declaration, synthetic label, dangling symbolic
  expression, or source-quality workaround introduced by the change.
- Focused C and relevant Python tests pass; Pandora source analysis, internal
  assembly, source quality, and exact full-file round trip pass.

## Required Deletions

- Per-target immediate-address rendering exceptions.
- Renderer-time tests that infer pointer meaning from raw immediate values.
- Scalar-only typed-flow paths that discard a compatible pointer value at a
  typed destination.
- Numeric fallback after a typed, renderable source-pointer classification has
  been made.
- Manual actions or comments whose only purpose is to force an instruction's
  printed operand text.

## Remaining Main-Task Completion Slice

The first implementation slice established the important common path: a typed
destination can promote a concrete immediate to an address value, preserve its
producer provenance through supported transfers, and let the render plan attach
one exact symbolic source expression. It is not yet the complete durable
address-value model promised above. Complete this remaining slice before
marking the proposal implemented:

1. Replace the pointer-store-only provenance marker and
   `has_renderable_source_expression` Boolean with one durable address-value
   fact. For each supported value it must identify source value, address
   identity/domain, pointee domain, producer operand, and a bounded transfer
   chain from producer to typed destination or consumer.
2. Preserve that fact through the existing supported register, stack, global,
   typed-field, relocation, compatible-join, and known-call transfer rules.
   Record an explicit terminal state when a value is invalidated, ambiguous,
   external, unrepresentable, or lacks a proven transfer contract. Do not
   infer a chain from rendered source text.
3. Make source-analysis JSON and the corpus row expose the complete stable
   fact: source/destination identity, value/domain, target resolution,
   propagation depth, terminal state/reason, render outcome, and fixture or
   review classification. `needs_address_value_propagation` is not a render
   outcome and must be removed or replaced by a precise terminal state.
4. Have the render planner consume the address-value fact by identity. A
   renderable source target must plan exactly one source expression and
   declaration; a contradictory source-render promise must produce the
   explicit export diagnostic, never a numeric operand. Add focused proof of
   that invalid-plan path.
5. Strengthen the C fixture matrix so each supported transfer and invalidation
   asserts the durable fact and terminal state, not only the final pointer
   store or rendered text. Regenerate the full read-only corpus report and
   demonstrate the Pandora direct-store/reload/consumer chain from that same
   fact.
6. Replace the post-implementation audit claim with a post-completion report
   only after these conditions pass. Keep the current report as an interim
   baseline and preserve every unresolved row as a review opportunity.

## Non-Goals

- Treating every large or aligned immediate as a pointer.
- Inventing target objects for unmapped runtime/external addresses.
- Replacing the shared render planner or adding a second symbol mechanism.
- Recovering full composite object layouts in this proposal.
- Whole-program alias inference, speculative call summaries, or retaining an
  address value across an unknown clobber.

## Deferred Composable Extensions After Completion

These are extension tasks, not hidden completion criteria for this proposal.
They must consume the address-value facts and render plans established here;
they must not recreate a second pointer-analysis or symbol mechanism.

For each item encountered during the main task, add a short dated entry under
its heading or bullet recording: the stable fixture/corpus/Pandora evidence;
why the main-task transfer rules correctly stop; the additional durable fact or
analysis model required; the expected render-plan consequence; and any
dependency on another deferred item. This turns the section into a precise
handoff design record while preserving the main task's boundary.

1. **Indexed, affine, and interior-address values.** Preserve element type,
   bounds, and addends through scaled indexing and address formation, so an
   address can resolve as an array element, field, or interior source range
   rather than only `symbol+offset`.

   *2026-07-28 handoff:* Pandora `s0:0004D3F0:instruction` reads an indexed
   pointer-table element (`abs_0_0005D416(pc,d0.w)`) before storing it in
   `interaction_message_ptr`. The current main path correctly stops because
   the scaled index does not prove a single address identity. A future fact
   needs table identity, element type, index domain/bounds, and addend; the
   render-plan consequence is a typed table-element expression only when that
   proof exists. This composes with pointer-table recovery below.

2. **Function summaries and callback contracts.** Derive proven typed pointer
   parameters, returns, escapes, clobbers, and indirect callback signatures;
   apply summaries interprocedurally only when their contract is durable.

   *2026-07-28 handoff:* resolved callback-slot stores such as
   `s0:000004B2:instruction` (`move.l a0,app_vertical_blank_callback(a6)`) do
   not retain a producer expression. The current main path correctly leaves
   them non-symbolic: no call/return or callback contract proves where `a0`
   came from. A future summary must carry return identity, escapes, clobbers,
   and callback signature; only then may the common render plan express the
   originating source value.

3. **Alias and control-flow refinement.** Distinguish identical object
   identity, compatible but unknown pointer domains, finite candidate sets,
   and invalidated aliases across joins and calls.

   *2026-07-28 handoff:* Pandora `s0:0004D410:instruction` and
   `s0:0004D560:instruction` store finite candidate values to
   `interaction_message_ptr`. The current main path preserves the candidates
   and does not invent a label or select one. A future model needs durable
   candidate-set identity and alias/join refinement; its render consequence is
   a symbolic expression only after a single compatible identity is proven.

4. **Pointer-table and chained-dereference recovery.** Carry the same facts
   through pointer tables, dispatch tables, object arrays, and repeated loads
   so typed indirect calls and data accesses compose.

   *2026-07-28 handoff:* the `s0:0004D3F0:instruction` indexed table read is
   also the concrete pointer-table trigger. It must consume the table/index
   fact from the indexed-address extension rather than introducing a renderer
   exception or a second source-symbol mechanism.

5. **Composable struct-instance and embedded-layout recovery.** Model one
   source range as ordered typed elements—prefixes, gaps, embedded records,
   arrays, and explicit overlays—using the reliable object edges from this
   proposal rather than a target-specific layout renderer.
