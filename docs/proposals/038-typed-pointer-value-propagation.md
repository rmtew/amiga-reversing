# Proposal 038: Typed Pointer-Value Propagation and Symbolic Access Recovery

Status: Complete — 2026-07-29. The consumer model, canonical address-value ownership,
Proposal 039 corpus coverage, and bounded candidate-merge soundness are complete.

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
storage transfers, a later reload, and at least one typed consumer. Consumers
are first-class analysis facts, not test assertions or renderer heuristics: a
typed storage write, a proven local-function argument, a proven platform/API
input, or a proven indirect-callback input.
It deliberately stops when identity, target mapping, a call contract, or a
control-flow merge is not proven. That boundary makes unknown and ambiguous
values durable analysis states rather than candidates for a numeric or
symbolic fallback.

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
render planning, plus a separate durable consumer representation. The value
represents identity and provenance; the consumer records the independently
proven place at which that value is used. A value may have multiple consumers,
and a consumer references exactly one address-value fact, including a fact
whose terminal state is non-source, ambiguous, or invalid. They record:

- value origin: immediate, relocation, register, stack slot, static/global
  slot, pointer field, return value, or table element;
- address value or source/runtime mapping, addend, and address domain;
- pointee type/domain and pointer width;
- producing instruction and transfer provenance on the value; and
- consumer identity, kind, operand, pointee domain, and the durable storage or
  call-input contract that proves consumption, on the consumer record;
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
   function/API contracts. Observe a proven call input before its call can
   clobber the value; a locally preserved register is a transfer across that
   call, not a substitute consumer record.
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
3. Introduce one common typed-consumer model for pointer stores and proven
   call inputs. It must retain the contract that justified consumption rather
   than encoding a call as a synthetic store or using a store as proxy
   evidence for a call. This is the framework mechanism used by analysis,
   reporting, and render planning; fixtures verify it but are not a substitute
   for it.
4. Make the source-analysis export expose these facts and their producer/
   consumer chain without relying on rendered text.
5. Teach the shared symbolic resolver to consume address-value facts for
   instructions, relocations, structured fields, and chained lookups.
6. Add normal Manual Action command support only where a reviewer must supply
   a missing durable type/field contract. Manual actions record the contract,
   never a one-off instruction rendering.
7. Remove any old scalar-immediate special cases made redundant by the common
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
typed pointer consumer
  + address-valued producer
  + target-resolution result
  + render result
  + downstream propagation summary
```

Each row must identify the source/target by stable corpus identity and include:

- source kind: immediate, relocation, register, stack, field, return value,
  or table element;
- consumer kind: typed struct field, app slot, absolute slot, stack parameter,
  local-function argument, platform/API input, or indirect callback input,
  with its declared pointee domain and durable contract identity;
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

### Interim first-slice corpus audit — 2026-07-28

The same full, read-only build completed after the first implementation slice:
378 analysed inputs (319 file entries and 59 reconstructed project targets),
45 Pandora pointer-store rows, and stable xref identities for every row. The
source/destination/resolution counts are unchanged because this work preserves
analysis facts rather than inventing target evidence. Their producer facts are
now explicit:

```text
immediate producer provenance: 4
other producer provenance: unknown 28, field_pointer 9, app_slot 3, static_data 1
render outcome: symbolic 4; non-source 41; invalid 0
```

The four symbolic rows are the four immediate pointer stores. The report now
reads each outcome, origin, terminal state, and transfer depth from the durable
address-value fact; pointer-store-local producer markers have been deleted. It
includes Pandora's
`interaction_message_ptr` store at stable key `s0:0004D3D2:instruction`.
The remaining propagated stores retain their actual non-immediate provenance
and remain unresolved review opportunities when no producer expression is
proven. They are not numeric renderer fallbacks.

The concrete Pandora branch is narrower than an earlier review description:
`interact_with_chemist` writes `abs_0_0005CF4C` to
`world_object_shared_prefix_interaction_message_ptr(a5)` and branches to
`interact_with_hooligan_or_robomechanic`, but that destination does not reload
the field. The separately observed reload belongs to a different control-flow
path, so treating it as the same value would be a false interprocedural alias.
Pandora remains the real-target direct symbolic-store proof. A focused CFG
fixture supplies the required same-object field-store/reload/consumer proof.

### Current consumer-model corpus audit — 2026-07-28

After the common consumer model was added, the final fresh normal eight-worker
corpus build completed all 428 entries in 524.8 seconds. It produced 3,095,963 xrefs,
460,240 listing snippet rows, 241 type-flow rows, and 65 unresolved typed-field
rows. The read-only pointer-value report now reads consumer facts rather than
using pointer-store records as a proxy:

```text
typed address-value consumers: 71 across 8 targets
consumer kinds: storage 45, local_function_input 18, platform_api_input 8
callback_input: unavailable in the current corpus
producer origins: immediate 11, field_pointer 9, app_slot 3,
                  static_data 1, unknown 47
resolution: resolved 48, finite candidates 2, unknown target 18,
            external 2, invalid target 1
render outcome: symbolic 9, non-source 61, invalid 1
Pandora: 63 consumers, including the direct interaction_message_ptr store
```

The unavailable callback category is a corpus-coverage result, not a narrowed
semantic boundary: focused C fixtures exercise an accepted bounded callback
table contract, alongside local-function, generated platform/API, storage, and
unknown-call-negative consumers. The report has no
`needs_address_value_propagation` outcome. Its non-source, ambiguous, external,
and invalid rows retain their explicit terminal state rather than receiving a
numeric rendering fallback.

## Pandora Proof Scope

Use the world-object interaction/callback swath as the real-target direct
symbolic-store proof, beginning with
`world_object_shared_prefix_interaction_message_ptr` in
`interact_with_chemist`. Establish the target object/range only from existing
mapping, xrefs, and typed-flow evidence; do not manufacture a reload or a
consumer relationship when control flow does not prove it.

The combined proof must demonstrate Pandora's direct typed pointer store and a
focused same-object CFG field store/reload/consumer. It must remain valid for
other pointer-field types without code changes.

## Acceptance Criteria

- A fresh corpus baseline and post-change report expose the typed-pointer
  opportunity rows above, with stable identity, provenance, aggregate counts,
  and no source mutation side effect.
- The corpus audit records every observed typed-consumer opportunity with its
  stable identity, consumer contract, and classification. Pointer-store rows
  remain one consumer category. A category omitted because no analysed target
  has the required durable contract is reported as unavailable, never treated
  as a negative case or used to narrow the implementation.
- Focused C fixtures cover representative positive, negative-scalar, external,
  ambiguous, and propagated cases. Corpus rows are selected as real-target
  integration cases where available, rather than requiring the corpus alone to
  supply every category or relying solely on Pandora.
- Focused C fixtures cover a typed pointer-field immediate store, relocation
  pointer store, register copy, stack/global round trip, typed field reload,
  compatible and conflicting joins, a preserved local-call input, a proven
  generated platform/API input, a proven accepted callback input, call
  clobbering, and a chained lookup. The fixtures assert the shared consumer
  facts and the planner's stable-identity linkage; rendered text alone is not
  evidence of either.
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
- A candidate-set merge that exceeds the representable bounded set must clear
  the concrete address identity and produce an explicit non-symbolic terminal
  state. It must never retain a subset of candidates or preserve a previously
  resolved target as though the omitted paths did not exist.
- Renderer/source-quality evidence comes from the planned expression, not from
  a separate typed-flow-to-label path.
- Pandora renders the verified world-object pointer store as the planned source
  expression. Focused fixtures follow the same address value through a
  same-object field reload to a typed consumer and through a proven call-input
  consumer. They must reject a changed or unproven base-object identity or
  call contract rather than creating an interprocedural alias.
- Pandora has no duplicate declaration, synthetic label, dangling symbolic
  expression, or source-quality workaround introduced by the change.
- `M68kAddressValueIR` is the sole durable owner of an address value's source
  value, provenance, resolution, target, candidate set, terminal state, and
  render outcome. A storage record owns only its storage-specific destination
  contract and its link to that value; it cannot retain a second mutable copy
  of address-value state.
- Resolution is represented by a generically named address-value model. No
  call consumer, render-plan path, or generic resolver depends on a
  pointer-store-named type or enum.
- Focused C and relevant Python tests pass; Pandora source analysis, internal
  assembly, source quality, and exact full-file round trip pass.

## Required Deletions

- Per-target immediate-address rendering exceptions.
- Renderer-time tests that infer pointer meaning from raw immediate values.
- Scalar-only typed-flow paths that discard a compatible pointer value at a
  typed destination.
- Pointer-store-only consumer assumptions, including any representation that
  encodes a proven call input as a synthetic storage write.
- Duplicated address-value facts in `M68kPointerStoreIR`, including copied
  source values, resolution, targets, candidate sets, provenance, or render
  state.
- Pointer-store naming or types in the shared address-value resolution model.
- Partial candidate-set retention after a bounded merge overflow.
- Numeric fallback after a typed, renderable source-pointer classification has
  been made.
- Manual actions or comments whose only purpose is to force an instruction's
  printed operand text.

## Completed Consumer-Model Slice

The initial slices established durable address-value facts for typed pointer
stores, explicit terminal/render states, planned-expression validation, and
same-object typed-field propagation. The common consumer model and its shared
target materialisation are complete:

1. Introduce a durable typed-consumer record that is independent of
   `M68kPointerStoreIR`, and make it the sole common consumption surface for
   analysis export, corpus reporting, and render planning. It must identify
   the consumer instruction operand, consumer kind, pointee domain, and the
   exact durable contract that proved consumption. Storage writes remain
   storage-specific records linked to the common address-value fact;
   local-function arguments, platform/API inputs, and callback inputs must
   not be encoded as synthetic stores. Address-value identity/provenance and
   consumer identity are separate: one value may feed several consumers, but
   each consumer links to one concrete or explicitly terminal address value.
2. Observe only contract-proven call consumers before call invalidation. Use
   the existing durable local-function register contracts, generated platform
   call-input contracts, and accepted callback signatures where they prove a
   pointer input. Unknown calls, untyped inputs, and unresolved indirect calls
   create no consumer and invalidate state under the existing clobber rules.
   Do not introduce heuristic call summaries, register-name conventions, or
   caller/callee fallbacks.
3. Link every supported typed consumption to an explicit consumer record and
   preserve the bounded producer-to-consumer transfer chain through the
   supported register, stack, global, typed-field, relocation,
   compatible-join, and known-call rules. Record an explicit terminal state
   when a value is invalidated, ambiguous, external, unrepresentable, or lacks
   a proven transfer contract. Do not infer a chain from rendered source text.
4. Extend source-analysis JSON and the corpus audit to expose the complete
   stable fact and its consumer: producer/consumer identities, consumer kind
   and contract, value/domain, target resolution, propagation depth, terminal
   state/reason, render outcome, and fixture/review classification.
   `needs_address_value_propagation` is not a render outcome and must not
   survive in the post-completion report.
5. Keep one render-plan path. The planner consumes the durable consumer and
   its linked address-value fact by stable identity, rather than recovering
   pointer meaning from instruction text, store records, or test-only side
   channels. A consumer operand with a mapped, representable source target
   receives that single planned expression; a non-source consumer remains
   explicitly non-source. A contradictory source-render promise must produce
   the explicit export diagnostic, never a numeric operand. No renderer may
   discover consumer semantics from operand text or duplicate the analysis
   resolver.
6. Strengthen the focused C fixture matrix so every supported transfer and
   invalidation asserts the durable value and consumer records, terminal state,
   and planned output where applicable. Include a proven local call input, a
   generated platform/API input, and an accepted callback input, plus negative
   untyped and unknown-call cases. Regenerate the full read-only corpus report and
   demonstrate Pandora's direct symbolic store plus the focused same-object
   field-store/reload/consumer chain; do not manufacture an interprocedural
   Pandora chain that its control flow does not prove.
7. Replace the interim audit claim with a post-completion report only after
   these conditions pass. Preserve unresolved rows as review opportunities and
   report unavailable consumer categories explicitly rather than hiding them.

## Completed Main-Task Slice: Canonical Address-Value Ownership

The completed consumer-model slice exposed one remaining transitional shape:
`M68kPointerStoreIR` still persists a duplicate copy of source-value,
resolution, target, and candidate facts already owned by `M68kAddressValueIR`.
The shared resolver currently operates over both representations. That is not
backwards compatibility to retain: it is redundant mutable state, permits
drift, and leaves generic call consumers coupled to pointer-store terminology.

The final migration made the address-value model canonical end to end:

1. Introduce a generic address-value resolution enum/type, move all generic
   consumer, value, resolver, planner, JSON, and corpus code to it, and remove
   the pointer-store-named resolution type. Preserve semantic states and their
   explicit terminal meanings; this is a representation migration, not a
   change in evidence policy.
2. Reduce `M68kPointerStoreIR` to a storage-consumer detail: destination
   identity/type/contract, source and destination operand identity as needed
   for the storage instruction, and `address_value_id`. Delete its duplicated
   address-value provenance, resolution, mapped target, candidate, and render
   fields. Do not add adapters, aliases, deprecated fields, or compatibility
   serializers.
3. Construct the canonical address value once, then link the storage consumer
   and storage detail to that identity. General call consumers and storage
   consumers must follow the same construction and target-materialisation
   path. The resolver may visit each canonical value once; it must not
   materialise a parallel store copy.
4. Make JSON export, source-quality validation, render planning, and the
   corpus audit read canonical address values through consumers. Retain a
   storage-specific JSON projection only where it describes the destination
   contract; it must reference the value by stable id rather than repeat its
   facts.
5. Update focused C fixtures to assert one canonical value linked to one or
   more consumers, including storage plus call consumers. Add regression
   checks that no pointer-store-specific resolution type or duplicated
   address-value field remains. Regenerate the Pandora source and rerun the
   full exact round trip, source-quality export, relevant Python tests, and the
   read-only corpus report.

This migration introduced no compatibility support. `M68kPointerStoreIR` is
now only a storage-destination record linked by `address_value_id`; all value
facts are owned by `M68kAddressValueIR`, and all consumers use the generic
resolution model. The resolver visits the unified transient consumer
observation once before the canonical analysis facts are emitted.

### Completion evidence — 2026-07-28

- `src/build.bat` and all 580 C unit tests passed. The focused branch-merge
  fixture verifies candidate-set merging on the unified consumer observation;
  the storage record retains no candidate or resolution state.
- `tests/test_target_usage_manifest.py` passed (30 tests).
- Pandora regenerated with exact full-file round trip and zero diff ranges.
  Its source-quality export reports 45 canonical address values, 63 consumers,
  45 storage details, zero blockers, and no source refusal.
- A fresh normal eight-worker corpus build completed 428 entries in 544.5
  seconds. The read-only consumer report contains 71 consumers across 8
  targets: 45 storage, 18 local-function inputs, and 8 platform/API inputs;
  outcomes are 9 symbolic, 61 non-source, and 1 invalid. No callback input is
  present in the current corpus, while the focused callback fixture remains
  coverage for that supported contract.

## Completion: Bounded Candidate-Merge Soundness — 2026-07-29

Review of the canonical migration found a soundness gap in the transient
consumer observation: `typed_pointer_candidates_merge` reported failure when a
join exceeded its four-value exact-candidate capacity, but the unified consumer
path ignored that result. It could therefore retain an earlier subset, which
could falsely appear resolved or less ambiguous than the control flow proved.
This was neither a compatibility concern nor an acceptable numeric fallback:
it was an incomplete analysis fact that required an explicit terminal state.

The completion implementation:

1. Defines one safe overflow transfer outcome for an address-valued
   candidate set: clear concrete identity, target, and candidate locations;
   retain no subset; and record a durable non-source terminal state/reason
   that states the bounded candidate merge exceeded analysis capacity.
2. Applies that outcome in every address-value candidate merge path, including
   the unified storage/call consumer observation and typed-flow joins. Do not
   introduce a larger hidden cap, keep an arbitrary first candidate, or add a
   renderer-side recovery path.
3. Ensures planning, JSON export, source-quality validation, and corpus audit
   distinguish this terminal state from a resolved, finite, external, invalid,
   or ordinary unknown target. It must receive no symbolic expression, label,
   declaration, or numeric rendering workaround.
4. Adds a focused fixture for a five-way compatible pointer join that
   reaches a storage consumer and a proven call consumer. Assert that neither
   consumer retains a concrete source target or candidate subset, that the
   terminal reason is durable, and that rendering remains exact without a
   symbolic expression for the unproven value.
5. Passed the release C suite (including 582 IR tests), 30 manifest tests, a
   fresh exact Pandora regeneration with zero diff ranges, and a fresh
   eight-worker corpus build in 437.6 seconds. The corpus audit reports 70
   consumers across seven targets (45 storage, 18 local-function inputs, and
   seven platform/API inputs), with no production candidate-overflow row and
   no partially retained candidate outcome.

This is a correctness completion, not an extension task. The following
extensions remain separate.

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

   The main task consumes an already durable local-function, platform/API, or
   callback input contract as a consumer. This extension begins only where the
   framework must derive a new contract, preserve a return identity, or infer
   an escape; it must not be smuggled into the main task as a fallback summary.

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

### Implementation-ready extension subtasks

Every subtask extends the canonical address-value facts and the existing
render-plan path. None may add compatibility fields, heuristic recovery,
target-specific renderer exceptions, numeric fallback rendering, or a parallel
symbol mechanism.

#### A. Indexed, affine, and interior-address values

**Evidence and boundary.** Pandora `s0:0004D3F0:instruction` reads an indexed
pointer-table element (`abs_0_0005D416(pc,d0.w)`) before storing it in
`interaction_message_ptr`. The current model correctly stops because the
scaled index does not prove one source address.

**Work.** Add a durable address-expression fact containing base-object
identity, signed addend, element stride/type, and an index-domain proof. Add
transfer rules for effective-address formation, scaled indexes, and compatible
add/subtract operations. Validate bounds, alignment, overflow, and code/data
ownership before materialising a target.

**Investigation result (2026-07-29).** `M68kTableDescriptorIR`,
`M68kTableConsumerIR`, and `M68kTableEntryIR` already retain table range,
entry width/count, kind, target/consumer linkage, and mask/compare/loop index
domains; JSON already exports those facts. The new expression fact must link to
that existing table identity and its stable source coordinates, not copy table
bounds or introduce a second index classifier. Pandora's `andi.w #12,d0` plus
the four longword entries at `abs_0_0005D416` is the positive fixture.

**Acceptance.** Fixtures cover one indexed element, an in-range finite set, an
interior field address, and invalid/out-of-range cases. Rendering produces a
typed table-element or interior expression only for a proven identity; every
other case remains explicitly non-source. Pandora exports the table/index fact,
whether or not its present index domain is sufficient to render symbolically.

**Dependency and benefit.** This is the prerequisite for indexed work in D. It
turns raw address arithmetic into typed provenance and enables safe symbolic
indexed/interior operands without relaxing unsupported cases.

#### B. Function summaries and callback contracts

**Evidence and boundary.** Pandora `s0:000004B2:instruction` stores `a0` to
`app_vertical_blank_callback(a6)`, but no fact proves the origin of `a0`; its
non-symbolic output is therefore correct.

**Work.** Define durable function-summary facts for proven input contracts,
return identities, register preservation/clobbers, pointer escapes, and
callback signatures. Derive or accept them through the normal analysis/action
surface and apply them only at direct local calls and proven callback edges.
Unknown calls remain clobbers and create no inferred summary.

**Investigation result (2026-07-29).** The current policy already has durable
`M68kAnalysisFunctionRegisterContract` and
`M68kAnalysisCallbackTableSignature` facts; the Manual Action catalog projects
both into effective metadata. Typed flow applies those facts at function entry,
records their consumers before invalidation, and has conservative local,
platform, and callback-table clobber paths. It also exports narrowly recovered
local-call summaries for known Amiga OS-vector wrapper effects, but those are
inferred platform-effect records rather than durable target function
interfaces; they do not model pointer return identity, escapes, or a general
preservation contract. This subtask must add one target summary
fact/action/projection pipeline and, where the common representation subsumes
the wrapper-specific record, migrate it rather than extending input contracts
or retaining parallel summary models.

**Acceptance.** Fixtures prove a typed parameter, return, preserved value, and
escaped callback value, plus unknown-call, conflicting-summary, and missing-
signature negatives. A planned expression appears only when its complete call
chain is proven. Pandora retains the current callback-store result unless a
durable summary supplies the missing proof.

**Dependency and benefit.** Independent of A; composes with C and D. It makes
interprocedural pointer flow explicit and safely improves call, return, and
callback rendering.

#### C. Alias and control-flow refinement

**Evidence and boundary.** Pandora `s0:0004D410:instruction` and
`s0:0004D560:instruction` have finite candidate values for
`interaction_message_ptr`; the current model correctly does not select one.

**Work.** Introduce an identity/alias lattice distinguishing one proven object,
compatible unknown objects, finite candidate identities, candidate overflow,
and invalidated values. Refine register, stack, global-slot, field, and call
joins only from durable path evidence. Preserve provenance, cardinality, and
invalidation in canonical address-value facts.

**Investigation result (2026-07-29).** The current lattice is distributed
through `M68kRenderTypedRegValue`, `M68kRenderTypedStoredValue`,
`typed_reg_merge`, `typed_stored_value_merge`, and the stack/global/field-slot
merge callers. It already represents finite candidates and the explicit
overflow terminal, but not a first-class identity relation or a path predicate.
The extension must centralise the new relation in the shared typed value model
and make every existing merge/clobber path transfer it; it must not bolt a
second alias pass onto rendering.

**Acceptance.** Fixtures cover same-identity and compatible-domain joins,
finite candidates, predicate-refined resolution, clobber invalidation, and
candidate overflow. Only a single proven identity is rendered symbolically;
finite and overflow results never receive a symbolic target. Corpus reports
each lattice outcome distinctly.

**Dependency and benefit.** Composes with A and B but can start independently.
It reduces avoidable ambiguity while retaining the completed no-speculation
rule.

#### D. Pointer-table and chained-dereference recovery

**Evidence and boundary.** `s0:0004D3F0:instruction` is both an
address-expression and pointer-table case. Current analysis does not carry its
pointee identity through the load to the typed store.

**Work.** Consume the existing descriptor, consumer, entry, range-ownership,
and data-reference facts as one table-entry contract. Add typed load transfer
rules for object arrays, dispatch tables, and repeated field loads. Add only
the missing table-entry pointee and null/invalid-entry semantics, and validate
table bounds, entry representation, and pointee ownership before every
dereference.

**Investigation result (2026-07-29).** The renderer already recognises
pointer-table structured items and runtime pointer-table slots, and callback
dispatch has a narrow table-identity proof. Those paths are specialised and do
not yet yield a canonical address value for a general table load. The extension
must generalise that one proven table-entry-to-value transfer, then have the
existing consumer/planner path render it; it must remove rather than duplicate
any specialised value propagation made redundant by the common transfer.

**Acceptance.** Fixtures cover direct and indexed loads, null/invalid entries,
pointer-to-pointer chains, typed indirect calls, and dispatch targets. Rendering
uses the existing table/object symbols only for proven links. Pandora gets a
table-to-store proof or a precise missing-fact report.

**Dependency and benefit.** Indexed table loads require A; a direct-load slice
may stand alone. This enables readable table, object-array, dispatch, and
chained field reconstruction.

#### E. Composable struct-instance and embedded-layout recovery

**Evidence and boundary.** Pointer and field facts exist, but source ranges
need one general representation for prefixes, explicit gaps, embedded records,
arrays, and overlays. Pandora's world-position/world-object families are the
intended proof domain.

**Work.** Extend structured-data/layout facts with composition trees of
ordered, non-overlapping owned elements and explicitly declared overlays. Each
element carries source range, type/size, ownership, and evidence. Make pointer
and field analysis resolve through those elements; unknown bytes remain gaps.

**Investigation result (2026-07-29).** Current Manual Actions and effective
metadata already support flat data-block layouts, typed elements, custom
struct bindings, fixed-stride arrays, custom fields, generated gaps, and
range-ownership conflict checks. They do not represent parent/child element
identity, an embedded-instance edge, or a validated explicit overlay. Pandora
already contains the suitable minimum proof: the 12-byte world-position
descriptor records have the eight-byte `world_position_descriptor_prefix` and
an explicit remaining four-byte gap. The new model must extend those existing
layout identities with composition, not replace the data-block or RS renderer.

**Acceptance.** Fixtures cover prefix-plus-gap, embedded record, instance
array, permitted overlay, rejected conflicting overlap, and embedded
pointer/field resolution. Pandora proves one composed layout with exact byte
coverage and exact reassembly; source uses existing struct declarations and
data bindings without redundant labels.

**Dependency and benefit.** It consumes the canonical value/consumer model and
composes strongly with D, but can otherwise proceed independently. It converts
isolated field facts into accurate, readable object instances without inventing
layout.

### Research-backed sequencing and common completion gate

1. Start A with the Pandora four-entry masked pointer table, because its
   descriptor, entry range, and index domain are already independently proven.
   First establish a canonical expression that references those facts; do not
   attempt general chained loads in the same slice.
2. Run C as the companion typed-flow cleanup: centralise identity-state joins
   before A or B adds another source of propagated identity. Its fixtures must
   preserve the completed candidate-overflow behaviour.
3. Start D only after A has supplied the table-entry expression contract. A
   direct non-indexed table-load fixture may be implemented first, but its
   representation must be the same one used by the indexed Pandora proof.
4. B can proceed independently once its durable target-summary action and
   projection are designed. Reconcile the existing recovered OS-wrapper effect
   summary during that design instead of adding a second general call model.
5. E can proceed independently from one existing flat data-block layout. Its
   first slice is prefix plus explicit gap; embedded layouts and overlays follow
   only after that ownership model is exact.

Every completed subtask must retain exact source reassembly, pass focused C and
Python projection tests, export the new durable fact in source analysis JSON,
and demonstrate one real target result or an explicit evidence-backed reason
that the selected Pandora example remains non-symbolic. The full corpus audit
must show the new outcome category separately; it must not reclassify an
unsupported case as resolved to improve reporting.
