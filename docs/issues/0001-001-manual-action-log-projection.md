# 0001-001 Manual Action Log Projection

## Parent

PRD 0001: Manual Review Workflow

## What to build

Build the first end-to-end Manual Action Log path. A target with no log has empty manual state. A target with a header-only log has empty manual state with pinned Target Identity. Ordered log actions project into current Manual Seeds, Manual Resolutions, Manual Labels, and Manual Comments. Sequence metadata is diagnostic only; file order is replay order.

This slice should expose projected manual state through the same project/listing path that analysis and UI will later consume, even if most action kinds initially project to inert state.

## Acceptance criteria

- [x] Missing Manual Action Log loads as empty manual state.
- [x] Header-only Manual Action Log loads as empty manual state with pinned Target Identity.
- [x] Action entries carry action id, sequence, timestamp, and optional undo relationship metadata.
- [x] Replay follows file order and reports sequence inconsistencies without changing replay order.
- [x] Undo actions project the prior action as inactive without deleting history.
- [x] Redo or compensating actions can restore a previously undone effect.
- [x] Projection exposes active and inactive action state for audit/debug output.
- [x] Malformed or unprojectable logs set Review State to `blocked`.
- [x] Target Identity mismatch is detected during log/header validation, prevents log projection, and emits a target-level `manual_action_log_target_mismatch` item from validation.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Implementation evidence

- Implemented in `amiga_reversing/disasm/manual_actions.py` and exposed on binary `ProjectRecord` payloads from `amiga_reversing/disasm/projects.py`.
- Covered by `tests/test_manual_action_log.py` and `test_get_project_exposes_manual_action_log_projection`.
- Verified with `uv run python -m pytest tests\test_manual_action_log.py tests\test_disasm_projects.py -q`.
- Verified with `uv run ruff check amiga_reversing\disasm\manual_actions.py amiga_reversing\disasm\projects.py tests\test_manual_action_log.py tests\test_disasm_projects.py`.
- Verified with `uv run mypy amiga_reversing\disasm\manual_actions.py amiga_reversing\disasm\projects.py`.
- Verified with `cmd /c src\precommit.bat`.
- Verified with `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`.

## Blocked by

None - can start immediately
