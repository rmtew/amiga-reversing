# 0001-005 Manual Labels Comments And Label Scope

## Parent

PRD 0001: Manual Review Workflow

## What to build

Replace entity name/comment overrides with Manual Labels and Manual Comments projected from the Manual Action Log. Add Label Scope for generated labels, metadata or policy labels, and Manual Labels. Keep v1 manual UI defaulting to global labels, while the model supports explicit local ownership for future local labels.

Assembler Profile metadata owns local-label support such as local prefix, owner rule, reserved names, and required mode flags. Rendering must not emit local labels unless support and binding are proven.

## Acceptance criteria

- [ ] Manual Labels affect rendering and UI naming but do not prove code or data without a Manual Seed.
- [ ] Manual Comments attach notes to addresses or ranges without proving classification.
- [ ] Labels or comments on unreconciled ranges create manual label/comment unreconciled review work.
- [ ] Review item kinds include manual label unreconciled, manual comment unreconciled, and label scope conflict.
- [ ] Global labels are unique in emitted source scope.
- [ ] Local labels carry explicit internal owner ids; nearest-previous-label behavior is only an emission check.
- [ ] Local label support is read from Assembler Profile metadata, not hardcoded.
- [ ] Label scope conflicts are review items and block only when emitted source correctness or assembly is at risk.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-001 Manual Action Log Projection
- 0001-004 Manual Review Item Generation
