Status: Ready
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Make existing import/reimport paths cleanly drop obsolete target-local UI/manual state instead of partially refreshing targets. Reimport should delete stale UI state, not preserve old fallback locator models.

## Acceptance criteria

- [ ] Existing import/reimport/profile-set code no longer copies or preserves `target_ui_edits.json`.
- [ ] Reimport cleanup deletes `target_ui_edits.json`, `ui_preferences.json`, target-local Manual Action Log data, and obsolete generated local state identified during implementation.
- [ ] Target-local files are inventoried and classified as source/import facts, UI/manual state, or intentional fixtures.
- [ ] `target_seeded_metadata.json` is kept unless proven to encode obsolete UI/manual state.
- [ ] `target_corrections.json` is explicitly classified before keep/delete behavior is finalized.
- [ ] Profile-set target copying no longer includes obsolete UI/manual state; current code copies `target_ui_edits.json` and must stop.

## Files likely touched

- `amiga_reversing/disasm/profile_set_targets.py`
- import/reimport code paths found during inventory
- profile-set/import tests

## Blocked by

None - can start immediately.

## Required tests

- Focused import/reimport/profile-set tests proving obsolete UI/manual state is removed and source/import facts are preserved.
