# Proposal 037: Render Planning and Symbolic Source Closure

Status: In progress. Source-body expression and label planning is implemented;
header declaration closure remains required before this proposal is complete.

## Problem

The renderer currently mixes semantic analysis, symbolic-expression selection,
and declaration creation while it emits text. That causes two invalid states:

- analysis-only facts create labels with no rendered reference; and
- a real symbolic data expression discovers its label after the renderer has
  passed the label's source position.

This is framework architecture, not a target-specific problem.

## Goal

Add a general render-planning phase that decides every symbolic source
expression and every declaration before source text is emitted.

```text
analysis facts + policy + decoded ranges
  -> render lookup
  -> candidate source expressions
  -> shared symbolic-expression resolver
  -> frozen expression/declaration plan
  -> source emission and evidence
```

The renderer consumes the frozen plan. It must not materialize labels,
references, or source-quality obligations as a side effect of writing text.

The plan is the sole boundary between semantic analysis and source rendering.
There is no legacy mutable-lookup rendering mode, compatibility alias mode, or
numeric fallback that silently hides a failed planned symbolic expression.

## Render Plan Model

### Planned expression

Each non-comment symbolic expression has one planned record containing:

- source section, offset, and operand or data-element identity;
- expression category: instruction operand, relocation, data pointer, pointer
  table entry, lookup-table entry, relative expression, or equate;
- target section/offset and logical address when applicable;
- exact symbol expression and addend; and
- a required label declaration when the expression targets source storage.

Analysis facts are semantic input only. A propagated register value, stack
slot, store, or runtime mapping does not create a planned expression unless a
concrete source expression renders it.

### Planned declaration

Each emitted label, equate, or layout declaration has one planned declaration
with a canonical identity, an origin, and its complete rendered form or
rendered-form inputs. A name cannot denote incompatible declaration kinds.

When a target equate and a rendered source label describe the same logical
object, the source label is canonical and the equate is omitted. No alias is
emitted. A genuine collision is a plan error identifying both origins.

### Shared resolver

One resolver must be used by both planning and emission. It returns either a
complete symbolic expression or a numeric/source-safe decision with an
explicit reason. It covers:

- direct instruction operands and relocations;
- typed structured pointer fields;
- pointer-table and lookup-table entries;
- chained/table-derived targets when their source entry is rendered; and
- materialized runtime-address mappings and addends.

It cannot create a declaration without an expression, or an expression
without a declaration obligation.

The resolver result is a tagged outcome, not a nullable name:

- `symbolic`: exact source expression, target identity, and declaration need;
- `numeric`: the expression is intentionally numeric, with a stable reason;
- `invalid`: analysis promised a renderable symbolic expression but no valid
  source representation exists; this is a source-export diagnostic.

An `invalid` outcome refuses source export. It is never converted to a numeric
expression merely to complete a build.

## Required Completion: Header Declaration Closure

The current implementation plans body expressions and source labels, but the
header still has a second, preview-local declaration path. Target/platform
equates, generated runtime-address helpers, RS/layout output, and some runtime
aliases are collected or deduplicated while header text is being prepared.
That is not a render plan and cannot validate collisions against planned source
labels. This proposal is not complete until that path is removed.

The completed design has one plan-owned declaration collection with these
rules:

- declarations carry a kind, canonical identity, origin, ordering class, and
  sufficient structured payload to render them without consulting mutable
  preview declaration state;
- source labels, runtime aliases, `EQU` symbols, RS/layout symbols, and
  generated helper symbols claim names through the same namespace operation;
- include requirements are plan-owned header requirements with canonical
  identity and deterministic ordering; they are not accumulated in preview
  side storage;
- a source label supersedes a target equate only when both describe the same
  logical object. All other duplicate names, including an alias colliding with
  a source declaration, are planning errors that report both origins; and
- after plan freeze, header emission is a pure traversal of ordered plan
  records. It neither declares, deduplicates, resolves, nor conditionally
  suppresses a symbol.

The existing declaration kind model must therefore be used for `EQU` and
layout records rather than reserving those kinds unused beside a text-line
side channel. Runtime aliases are declarations in this model, not a parallel
array with an independent collision check. The instruction-access helper is
split into a planning operation and an emission/evidence-copy operation; no
boolean mode flags remain to select a legacy renderer path.

## Ownership and Ordering

`M68kRenderLookup` remains a read-only query/index over analysis, policy,
decoded ownership, and address mappings once planning begins. The new render
plan owns:

- planned expressions;
- planned declarations and the symbol namespace;
- planned source-label references, including storage and materialized-runtime
  alias labels; and
- immutable row-to-expression evidence.

Planning has two ordered passes:

1. Collect and resolve every candidate instruction and data expression,
   including every element of structured pointer and lookup tables.
2. Derive canonical declarations and validate name, target, and reference
   closure before any header, `EQU`, `ORG`, label, or section body is emitted.

This ordering is required for backward references, for forward references,
and for the rule that a materialized source label supersedes an equate at the
same logical address.

Every emitted source label, including durable labels and materialized runtime
aliases, has a planned label row. Interior planned labels are render
boundaries: a typed renderer may retain its form only when it can emit that
label at a valid element boundary; otherwise the body is split into safe data
rows. A body walk must never consume a structured range across a planned label.

The declaration namespace covers every emitted declaration category, not only
source-storage labels. `EQU`, RS/layout, include-dependent symbolic support,
storage labels, and runtime aliases all have plan records before their text is
emitted. No preview-local declaration list is an authority for naming,
deduplication, collision handling, or output ordering.

## Invariants

- Every emitted symbolic expression has exactly one planned expression.
- Every planned source target has its planned declaration before emission.
- Every emitted label is justified by a planned reference, an explicit durable
  label, an accepted code entry, or a non-code range root.
- Runtime facts and typed-flow facts cannot create declarations directly.
- Source-quality consumes render-plan evidence, never analysis-only guesses.
- Planning is deterministic for identical facts and policy.

## Migration

1. Add render-plan expression/declaration IR, immutable evidence rows, and
   namespace/closure validation.
2. Implement one resolver for all direct operands, relocations, typed fields,
   pointer tables, lookup tables, and runtime-mapped targets.
3. Make planning enumerate the same candidate elements as emission; no
   renderer may have a private target-resolution path.
4. Freeze the plan before headers, derive canonical declarations, then emit
   only frozen plan rows.
5. Move source-quality expected access and unreferenced-label checks to plan
   evidence and emitted rows.
6. Delete the mutable label/reference machinery from render-time paths and
   remove target-equate aliases superseded by source labels.
7. Move all header declarations into the plan namespace: target and platform
   equates, generated runtime-address helper equates, RS/layout declarations,
   and every emitted runtime alias. Emit their rows solely from the frozen
   plan, then remove preview-local declaration storage and its parallel
   deduplication rules.
8. Make instruction-access planning a single planning operation with no
   renderer-mode switches. Emission copies its planned evidence only.

No compatibility or fallback rendering path is retained.

## Required Deletions

The completed implementation removes, rather than retains beside the plan:

- renderer-time calls to `render_lookup_mark_label*` and
  `render_lookup_set_label` for source-expression discovery;
- renderer-time traversal of runtime-address facts to discover or format
  alias labels;
- preview-local declaration arrays and declaration-line storage used as a
  second declaration namespace;
- separate runtime-alias collision handling that does not consult the common
  declaration namespace;
- semantic runtime-reference and broad table label prepasses;
- ad hoc structured-pointer label planners;
- dual-mode renderer/planner symbol-access helpers and renderer-time evidence
  decisions that duplicate resolver logic;
- source-quality producers derived directly from runtime or typed-flow facts;
- target-equate emission that aliases a rendered source label; and
- parser diagnostics that classify declaration-kind conflicts as allocation
  failures.

The renderer may still record evidence, but only by copying the frozen plan
row it emitted. It cannot alter the plan or lookup.

## Acceptance Criteria

- A semantic runtime-address fact with no rendered expression creates neither
  label nor source-quality obligation.
- Fixtures cover direct operands, typed struct fields, pointer tables, lookup
  tables, chained lookups, forward/backward runtime-mapped targets, and
  materialized runtime aliases.
- A label/equate for one logical object emits only the canonical label.
- A genuine label/equate collision reports a symbol-kind diagnostic, never
  an allocation failure.
- Each planned `symbolic` result produces one matching emitted expression and
  every planned declaration is emitted exactly once; each `numeric` result is
  emitted numerically with its audited reason.
- Every emitted `EQU`, RS/layout declaration, source/storage label, and
  runtime alias is represented in one shared plan namespace. Cross-kind or
  alias/name conflicts fail planning with both origins; no preview-local
  declaration deduplication remains.
- Header rows are emitted solely from frozen plan records. A focused fixture
  covers a source label superseding a target equate, a runtime alias collision
  with a source declaration, and generated runtime-address helper equates.
- Pandora proves the model with the world-object data: `active_world_object_ptr_table`
  is a canonical source label rather than an `EQU` alias; world-object typed
  pointer fields such as `behavior_script_ptr` have declared symbolic targets;
  and every emitted world-object pointer-table entry has a declared target.
- Pandora has no dangling symbolic data expression, duplicate declaration,
  synthetic unreferenced label, or source-quality workaround.
- Existing C tests and relevant Python tests pass; new focused C/Python
  fixtures cover the plan and resolver outcomes; Pandora internal source
  assembly, source quality, and exact full-file round trip pass.

## Non-Goals

- Guessing symbols for arbitrary numeric values.
- Target-specific special cases.
- Preserving historical aliases or compatibility equates.
- Printing every analysis address as a symbol.
