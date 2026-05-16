# PRD 006: Manual Action Catalog, API, and CLI

## Status

Complete as of 2026-05-16.

## Purpose

Create a backend-owned **Manual Action Catalog** so LLMs, CLI callers, and Web UI surfaces all discover and invoke the same currently valid actions for a project, target, **Manual Review Item**, or **Listing Selection**.

## Scope

- Move review action eligibility out of web-only hardcoding such as `expandedReviewActions()` and into backend catalog generation.
- Expose catalog entries through HTTP APIs and thin CLI wrappers.
- Keep the **Manual Action Log** as the durable record for domain actions.
- Include transient navigation/open-panel commands in catalog responses when useful, but mark them as non-log actions.
- Keep non-review tooling commands such as source export and reproduction profile selection outside Manual Action Log semantics; command palette integration for those commands is covered by PRDs 008, 018, and 021.

## Requirements

- The backend returns catalog entries with stable action ids, labels, descriptions, enabled/disabled state, target context, parameter schema, optional default key binding, and whether the action appends to the **Manual Action Log**.
- Catalog queries support at least target-wide, review-item, row, and element contexts.
- Existing review actions are represented by catalog entries: create code/data seed, resolve review item, remove annotation, open reproduction report, rerun round-trip verification, acknowledge blockers, rename/remove labels, and label-scope changes.
- Manual action execution validates catalog action parameters before appending a log entry.
- CLI wrappers can list actions, show required parameters, and invoke actions against a project without needing browser state.
- No LLM-only protocol is introduced; LLM workflows use the same HTTP and CLI surfaces.
- Catalog output includes enough evidence/context for an agent to choose actions without scraping Web UI text.
- The command palette may combine Manual Action Catalog entries with non-manual **Target Tooling Commands**, but catalog action execution remains the path for manual domain actions.

## Non-Goals

- User-defined key binding persistence.
- Replacing the **Manual Action Log** storage model.
- Direct source-text editing.
- Owning every command palette command; target tooling commands are separate command types.
- Range-selection catalog semantics beyond row and element contexts; covered by PRD 014.

## Verification

- Backend unit tests for catalog eligibility per review item kind and listing context.
- Route tests for catalog query and action execution.
- CLI tests for list/show/invoke flows.
- Web source tests proving review buttons render from catalog output rather than hardcoded action rules.
- Round-trip verification remains mandatory for manual actions that affect source rendering before review can be marked clear.

## Issues

- [006-001: Review Item Action Catalog](../issues/006-001-review-item-action-catalog.md)
- [006-002: Catalog Action Execution](../issues/006-002-catalog-action-execution.md)
- [006-003: Target and Listing Action Contexts](../issues/006-003-target-and-listing-action-contexts.md)
- [006-004: Manual Action CLI](../issues/006-004-manual-action-cli.md)
- [006-005: PRD 006 Review and Tightening](../issues/006-005-prd-006-review-and-tightening.md)

## Open Questions

- Resolved: CLI command names are exposed through `amiga-manual-actions`
  list/show/invoke.
- Resolved: catalog responses include disabled/unavailable entries where the
  caller needs eligibility reasons.

## Completion Notes

- Backend catalog entries, execution payloads, HTTP routes, CLI list/show/invoke,
  and Review panel catalog rendering are implemented.
- Focused PRD006 verification passed on 2026-05-16:
  `uv run python -m pytest tests\test_manual_actions_cli.py tests\test_web_app_source.py tests\test_disasm_server.py -q -k "manual_actions_cli or manual_action_catalog or annotation_controls_use_manual_review_actions"`.

## Follow-On PRDs

- PRD 012 adds schema-rendered parameter collection for catalog actions.
- PRD 014 adds explicit range-selection catalog contexts.
- PRD 016 adds review-note catalog actions.
