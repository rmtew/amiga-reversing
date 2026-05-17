Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Make existing import/reimport paths cleanly drop obsolete target-local UI/manual state instead of partially refreshing targets. Reimport should delete stale UI state, not preserve old fallback locator models.

## Acceptance criteria

- [x] Existing import/reimport/profile-set code no longer copies or preserves `target_ui_edits.json`.
- [x] Reimport cleanup deletes `target_ui_edits.json`, `ui_preferences.json`, target-local Manual Action Log data, and obsolete generated local state identified during implementation.
- [x] Target-local files are inventoried and classified as source/import facts, UI/manual state, or intentional fixtures.
- [x] `target_seeded_metadata.json` is kept unless proven to encode obsolete UI/manual state.
- [x] `target_corrections.json` is explicitly classified before keep/delete behavior is finalized.
- [x] Profile-set target copying no longer includes obsolete UI/manual state; current code copies `target_ui_edits.json` and must stop.

## Implementation notes

Target-local files classified during implementation:

```text
source/import facts kept:
  source_binary.json
  target_metadata.json
  target_seeded_metadata.json
  target_corrections.json
  binary.bin
  decompression.json
  .project.json

UI/manual state dropped on import/reimport:
  target_ui_edits.json
  ui_preferences.json
  manual_actions.jsonl
```

No additional obsolete generated local-state files were found in tracked target
fixtures. `target_corrections.json` is source/import correction metadata, not UI
state, and remains preserved.

## Verification

```text
uv run python -m pytest tests\test_import_adf.py::test_import_adf_reimport_drops_obsolete_target_local_state_but_keeps_import_facts tests\test_full_reproduction_cache.py::test_profile_set_copy_preserves_import_facts_and_drops_obsolete_ui_state -q
uv run python -m pytest tests\test_import_adf.py tests\test_full_reproduction_cache.py -q
uv run ruff check amiga_reversing\amiga_disk\project.py amiga_reversing\disasm\profile_set_targets.py amiga_reversing\disasm\target_local_state.py tests\test_import_adf.py tests\test_full_reproduction_cache.py tests\test_full_reproduction_integration.py
```

## Files likely touched

- `amiga_reversing/disasm/profile_set_targets.py`
- import/reimport code paths found during inventory
- profile-set/import tests

## Blocked by

None - can start immediately.

## Required tests

- Focused import/reimport/profile-set tests proving obsolete UI/manual state is removed and source/import facts are preserved.
