# Proposal 014: Source-Converging Manual Action Surface

Status: Draft.

This proposal defines the full manual-edit and command surface needed for LLM
and human reversing to move rendered target source toward human-quality
reconstructed source.

Proposal 010 proved the agentic loop harness: inspect, execute through normal
commands, verify, and report. GenAm work then exposed the next layer: the loop
can only be as useful as the source facts it can edit through supported Manual
Action Log commands. If a human reverser can reasonably improve the source, the
project needs a durable manual action, command-catalog exposure, loop access,
and verifier for that improvement.

## Clean Target Model

The desired surface is capability parity across the source model:

```text
auto-analysis fact or rendered-source construct
  -> durable target identity
  -> human manual edit need
  -> Manual Action Log action
  -> command catalog entry
  -> loop candidate/action
  -> verifier
  -> rendered source closer to recovered original intent
```

The loop must not gain private powers. It should use the same command catalog
and Manual Action Log paths as UI/manual workflows. If a capability is missing,
the correct result is a precise missing-capability report and an implementation
issue, not a temporary script or direct metadata write.

## Source-Converging Work

Source-converging work improves the rendered source in ways a human reverser
would recognize:

- clearer function, label, global, app-slot, and data names;
- named constants and equates instead of unexplained immediates;
- domain-appropriate immediate representations;
- code/data/string/table/structure classification;
- typed fields, structure layouts, and register-base facts;
- API/library semantics propagated through calls, arguments, return values, and
  stored state;
- review items resolved with type-specific evidence;
- comments only for concrete semantic discoveries that do not have a better
  structured representation.

Proof actions, placeholder notes, and "note that this exists" edits are out of
scope. They exercise the harness but do not converge the target source.

## Coverage Matrix

The first implementation step is an audit matrix. Each editable fact type gets
one row:

```text
Fact type
Auto-analysis source
Rendered-source effect
Human edit need
Durable target identity
Manual Action Log support
Command catalog support
Loop planner support
Verifier
Known gap / issue
```

Seed rows include:

| Fact type | Examples | Known concern |
| --- | --- | --- |
| Source labels/functions | `loc_0_00001000`, function entry labels | label rename exists in the loop but needs matrix placement |
| App/base-relative slots | `app_0234(a6)`, RSSET storage | needs add/edit/rename command support |
| Globals/static data symbols | hunk-local data labels | likely overlaps label/data symbol identities |
| Equates/constants | flags, modes, sizes, menu ids, magic values | needs add/edit/rename command support |
| Immediate representation | hex/decimal/binary/char/equate operand display | needs operand identity and representation verifier |
| Code/data seeds | force code/data, raw/scalar/string/table roles | command coverage and verifier audit required |
| Structured data/types/fields | records, field offsets, typed slots | identity and rendering support need audit |
| API/library semantics | library calls, arguments, returns | support varies; verifier must prove propagation |
| Register/base facts | app base, frame/base pointers, preserved registers | needs durable identity and verifier audit |
| Review items/resolution | orphan signals, typed gaps, suspected data | type-specific command/verifier coverage |
| Semantic comments | concrete discoveries with no structured home | allowed only when structured actions do not fit |

## Principles

- Build from the source model outward. Do not add commands just because one
  target exposed a local need.
- Every command needs a durable target identity that survives projection
  rebuilds.
- Every command needs a verifier: semantic reload, projection/rendered text,
  round-trip exactness, or a type-specific oracle.
- Manual Action Log remains the durable intervention model.
- Command catalog exposure is the supported automation surface.
- Loop planning ranks source-converging actions and reports why skipped actions
  were not chosen.
- Missing command support is a blocker, not permission for scripts or direct
  metadata writes.

## Implementation Slices

1. Build the source-convergence capability matrix.
2. Define or fill durable target identities for editable source constructs.
3. Add missing Manual Action Log actions.
4. Expose supported actions through the command catalog.
5. Add verifiers for every action family.
6. Teach the loop planner to use command-catalog capabilities instead of
   bespoke proof paths.
7. Run a GenAm trial that performs a non-comment source-converging action and
   stops only on the next precise missing capability.

## Non-Goals

- No private agent mutation APIs.
- No direct target metadata writes outside command/manual-action paths.
- No unsupported temporary scripts as a substitute for command coverage.
- No automatic decompiler promise.
- No broad speculative edit without local evidence and a verifier.

## Acceptance Criteria

- The matrix covers all current auto-analysis fact families and rendered-source
  constructs that a human reverser would edit.
- Each supported source-converging edit has Manual Action Log, command catalog,
  loop, and verifier coverage.
- Each unsupported but required edit has a specific issue with identity,
  command, and verifier requirements.
- Agent instructions point agents to the matrix and require missing-capability
  reports instead of workarounds.
- A target loop can continue with real source-converging work until it reaches a
  documented missing capability.

