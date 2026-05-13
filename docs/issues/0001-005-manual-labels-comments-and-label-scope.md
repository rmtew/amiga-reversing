# 0001-005 Manual Labels Comments And Label Scope

## Parent

PRD 0001: Manual Review Workflow

## What to build

Replace entity name/comment overrides with Manual Labels and Manual Comments projected from the Manual Action Log. Add Label Scope for generated labels, metadata or policy labels, and Manual Labels. Keep v1 manual UI defaulting to global labels, while the model supports explicit local ownership for future local labels.

Assembler Profile metadata owns local-label support such as local prefix, owner rule, reserved names, and required mode flags. Rendering must not emit local labels unless support and binding are proven.

## Acceptance criteria

- [x] Manual Labels affect rendering and UI naming but do not prove code or data without a Manual Seed.
- [x] Manual Comments attach notes to addresses or ranges without proving classification.
- [x] Labels or comments on unreconciled ranges create manual label/comment unreconciled review work.
- [x] Review item kinds include manual label unreconciled, manual comment unreconciled, and label scope conflict.
- [x] Global labels are unique in emitted source scope.
- [x] Local labels carry explicit internal owner ids; nearest-previous-label behavior is only an emission check.
- [x] Local label support is read from Assembler Profile metadata, not hardcoded.
- [x] Label scope conflicts are review items and block only when emitted source correctness or assembly is at risk.
- [x] CDP tests pass.
- [x] `cmd /c src\precommit.bat` passes.

## Completion

Completed on 2026-05-13.

Implemented Manual Labels and Manual Comments as Manual Action Log projections that flow into effective metadata and C backend policy without creating code or data classification. Added unreconciled annotation review items, label scope conflicts for duplicate/colliding/unsupported labels, entry comment metadata, seeded code-label C policy loading, and assembler-profile local-label metadata for vasm and Devpac.

Verification:

- `uv run python -m pytest tests\test_manual_action_log.py tests\test_manual_review_items.py tests\test_manual_seed_effective_metadata.py tests\test_disasm_projects.py tests\test_c_backend.py::test_generic_metadata_loader_omits_platform_specific_data -q`
- `uv run ruff check amiga_reversing\disasm\assembler_profiles.py amiga_reversing\disasm\manual_actions.py tests\test_manual_action_log.py`
- `uv run mypy amiga_reversing\disasm\assembler_profiles.py amiga_reversing\disasm\manual_actions.py`
- `M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests\test_web_e2e_cdp.py -q`
- `cmd /c src\precommit.bat`

## Blocked by

- 0001-001 Manual Action Log Projection
- 0001-004 Manual Review Item Generation
