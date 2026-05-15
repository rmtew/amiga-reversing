# PRD 010: Semantic Helper Actions

## Purpose

Add Resource-inspired semantic helper actions for OS calls, equates, structs, value representations, and data typing without falling back to direct source-text substitution.

## Scope

- Provide catalog actions that attach user intent to selected values, operands, labels, or ranges.
- Trigger reanalysis when actions affect facts, type propagation, or source rendering.
- Keep value display choices separate from data classification.

## Requirements

- Assigning an OS call, LVO, equate, struct offset, or library-base interpretation appends a domain action and reruns analysis where needed.
- Semantic helper actions use project knowledge from `knowledge/amiga-os.md`, `knowledge/amiga-hardware.md`, parsed NDK data, and current analysis facts.
- Matching helpers are contextual: immediate values can search value-equivalent equates, LVOs, and struct offsets; library calls can use register/base evidence when present.
- Data type changes for byte/word/long/string/table/block classification remain **Manual Seed** actions.
- Value representation changes such as hex, binary, character, string delimiter style, or literal formatting use **Manual Representation** actions, not **Manual Seed** actions.
- Rendering consumes analysis facts, **Manual Seeds**, and **Manual Representation** projections rather than edited source text.
- Helper actions may be invoked from command palette, context menu, Review dialog suggestions, CLI, or API when their context is valid.

## Non-Goals

- Handcoded M68K instruction knowledge.
- Treating vasm, Musashi, or other oracles as production dependencies.
- Full custom user key-binding persistence.

## Verification

- Backend tests for helper eligibility and payload validation.
- Analysis tests for any helper action that propagates types or affects facts.
- Rendering tests for **Manual Representation** output.
- Round-trip verification for actions that alter rendered source.
- Web/CDP tests for at least one helper action through the command palette once exposed.

## Issues

- [010-001: Manual Representation Actions](../issues/010-001-manual-representation-actions.md)
- [010-002: Data Type Helper Actions](../issues/010-002-data-type-helper-actions.md)
- [010-003: Equate, LVO, and Struct Helper Matching](../issues/010-003-equate-lvo-struct-helper-matching.md)
- [010-004: Library Base OS Call Helper](../issues/010-004-library-base-os-call-helper.md)
- [010-005: PRD 010 Review and Tightening](../issues/010-005-prd-010-review-and-tightening.md)

## Open Questions

- Initial supported OS libraries, struct families, and equate namespaces.
- Exact schema for **Manual Representation** actions.
