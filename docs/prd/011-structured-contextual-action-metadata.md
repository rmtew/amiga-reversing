# PRD 011: Structured Contextual Action Metadata

## Status

Complete as of 2026-05-16.

## Problem Statement

Contextual Manual Action Catalog entries currently infer some semantic helper eligibility by parsing rendered listing text. This is brittle and inconsistent with the project rule that tooling should consume structured analysis facts rather than re-derive meaning from display strings.

The immediate user-facing failure was a selected label such as `abs_0_00010488:` being scanned as if it contained an immediate value, causing a catalog request error instead of a useful command palette. The deeper problem is architectural: row and element actions should be modeled from cached C listing metadata and analysis facts, not source-text scraping.

## Solution

Expose a structured **Listing Element Context** from the cached C listing artifact and use it as the sole basis for contextual catalog actions.

The command palette, Review dialog, API, and CLI should ask for actions using row and element identities that include structured values, operand indexes, symbols, access type, byte ranges, hunk/source offsets, and stable keys. Semantic helper matching for equates, LVOs, struct offsets, library bases, and value representations should consume these fields directly.

Rendered text remains display output only. It may be used for labels shown to the user, but not as input to decide what actions are valid.

## User Stories

1. As a reverser, I want pressing `p` on a label row to show valid commands without backend errors, so that labels that contain digits do not break the command palette.
2. As a reverser, I want immediate-value helper actions to appear only when the selected element is actually an immediate value, so that helper suggestions are trustworthy.
3. As a reverser, I want label, equate, app-slot, operand, data-literal, and comment elements to have distinct structured identities, so that contextual actions target the thing I selected.
4. As a reverser, I want the same selected element to survive a listing refresh when its stable identity still exists, so that reanalysis does not silently move actions to another target.
5. As a reverser, I want the UI to report when element precision is lost, so that I know an action may now apply only at row precision.
6. As an LLM agent, I want the action catalog API to return structured contexts and parameter evidence, so that I can choose actions without scraping source text or DOM text.
7. As an LLM agent, I want immediate candidate values to include width, signedness where known, operand index, and source location, so that I can distinguish byte literals, word offsets, long addresses, and branch displacements.
8. As an LLM agent, I want symbol references to include symbol name, reference role, operand index, and target kind, so that I can decide between follow-reference, detail-list, or semantic-helper actions.
9. As a CLI user, I want row and element catalog contexts to be serializable and stable, so that command-line workflows can invoke the same actions as the web UI.
10. As a web UI user, I want command palette actions to be based on the currently selected row or element, so that filtering and Enter execution are predictable.
11. As a web UI user, I want selecting an operand or literal to pass an element identity to the backend, so that representation changes affect the selected literal rather than the first parseable text fragment.
12. As a tool maintainer, I want contextual action eligibility in one structured module, so that web, CLI, and review flows do not duplicate interpretation rules.
13. As a tool maintainer, I want tests that prove numeric-looking labels are not treated as immediates, so that this class of failure stays fixed.
14. As a tool maintainer, I want tests that prove rendered text changes do not alter semantic helper eligibility, so that display formatting remains separate from behavior.
15. As a tool maintainer, I want C row payloads to expose missing operand/literal facts explicitly, so that Python catalog code does not grow disassembler knowledge.
16. As a tool maintainer, I want structured contexts to derive from generated/spec-driven analysis where instruction semantics are involved, so that no M68K knowledge is hardcoded downstream.
17. As a project reviewer, I want Manual Action Log payloads created from contextual actions to include enough provenance, so that future review can explain why an action was offered.
18. As a project reviewer, I want invalid element contexts to fail with clear errors, so that stale UI selections and stale CLI calls are diagnosable.
19. As a project reviewer, I want row-level actions and element-level actions to be clearly separated, so that ambiguous element operations cannot silently run at row precision.
20. As a future implementer, I want this work split so C payload enrichment, Python catalog modeling, web selection, and tests can be built independently.

## Implementation Decisions

- Add a deep **Listing Element Context** module that normalizes cached C row payloads into stable row and element contexts for the Manual Action Catalog.
- Treat rendered source text as presentation only. Catalog eligibility must not parse labels, operands, comments, or directive text to discover semantic values.
- Extend C listing row payloads where necessary to expose immediate/literal metadata, operand indexes, byte widths, data literal ranges, symbol references, equate references, app-slot references, typed accesses, and source context.
- Preserve the rule that downstream tools do not hardcode M68K instruction knowledge. If a contextual field depends on instruction decoding, the C analysis payload must derive it from generated/spec-driven decode metadata.
- Make row context and element context explicit API concepts. Row context can offer row/range actions. Element context can offer operand, literal, symbol, equate, app-slot, comment, or data-byte actions.
- Replace text-based semantic helper matching with structured value matching. Equate, LVO, and struct-offset helpers should consume selected element values only.
- Preserve Manual Seed, Manual Representation, Manual Register Seed, and Manual Semantic Hint separation.
- Add stable element identity fields such as row stable key, hunk, source offset, operand index, element kind, symbol name, access role, value, width, and byte span when available.
- Make stale or imprecise element contexts explicit. If an element cannot be found after refresh, the UI may fall back to row selection but must mark precision loss before executing element-only actions.
- Keep command palette behavior UI-only. Palette filtering and selected-entry movement should not determine action validity; validity comes from the catalog.
- Keep the CLI and API as first-class consumers. They should use the same structured contexts as the web UI.
- Remove the old text numeric scanner once structured values cover current semantic helper needs.

## Testing Decisions

- Tests should assert external behavior: catalog entries returned for structured contexts, action execution payloads, UI command palette behavior, and absence of backend errors.
- Backend route tests should cover label rows with numeric-looking names, immediate operands, data literals, symbol references, equate references, and stale/invalid contexts.
- C/backend tests should cover row payload enrichment where new structured element fields are introduced.
- Web/CDP tests should cover selecting an operand/literal/symbol, opening the command palette, and verifying catalog requests carry structured element context rather than inferred text.
- Regression tests should prove rendered text formatting changes do not change semantic helper eligibility for the same structured element.
- Existing Manual Action Catalog, command palette, and C backend tests are prior art for this work.
- `src\precommit.bat` remains required before marking implementation complete.

## Out of Scope

- New semantic domains beyond the equate, LVO, struct-offset, library-base, representation, and data-type helper families already planned.
- User-defined key-binding persistence.
- Replacing the disassembler, assembler, simulator, or effect predictor pipeline.
- Direct source-text substitution as a semantic helper mechanism.
- Full UI redesign of the command palette or Review dialog.

## Further Notes

This PRD is a corrective architectural follow-up to PRD 010. Its implementation is the structural fix: contextual action eligibility must stop parsing rendered text and must consume structured row and element metadata instead. A temporary production guard that prevents crashes before this PRD lands is not completion of this PRD and must not become a second eligibility path.

PRD 014 builds on this structured row and element metadata for range-selection catalog contexts.

PRD 017 builds on the same structured metadata for inline and palette-hosted parameter sessions.

## Completion Notes

- Structured row and element contexts are normalized in `listing_context.py`
  and consumed by `manual_action_catalog.py`.
- Semantic helper eligibility uses structured selected values; numeric-looking
  label text is covered by regression tests.
- Web selection sends structured element context and records precision loss
  when a selected element no longer resolves exactly.
- Focused PRD011 verification passed on 2026-05-16:
  `uv run python -m pytest tests\test_disasm_server.py tests\test_web_app_source.py tests\test_web_e2e_cdp.py -q -k "manual_action_catalog or structured_symbol_context or command_palette_applies_manual_representation or numeric_label or listing_navigation_indexes_instruction_typed_accesses or listing_navigation_indexes_unresolved_typed_accesses"`.

## Issues

- [011-001: C Listing Element Metadata](../issues/011-001-c-listing-element-metadata.md)
- [011-002: Structured Catalog Context Model](../issues/011-002-structured-catalog-context-model.md)
- [011-003: Replace Text-Based Semantic Matching](../issues/011-003-replace-text-based-semantic-matching.md)
- [011-004: Web Element Selection Uses Structured Context](../issues/011-004-web-element-selection-uses-structured-context.md)
- [011-005: PRD 011 Review and Tightening](../issues/011-005-prd-011-review-and-tightening.md)
