# 0002-002 Symbolize Boot IO Request Setup

## Parent

[PRD 0002: Bootblock Runtime Address Model](../prd/0002-bootblock-runtime-address-model.md)

## What to build

Carry boot entry IO request type knowledge far enough through simple local save/load patterns that `DoIO` setup renders with IO field names instead of raw offsets. A bootblock that saves the entry `A1` pointer to local storage, reloads it, writes command, offset, length, and data fields, then calls `DoIO` should produce readable IO request field references.

This slice is complete when the Epic bootblock's `DoIO` setup is symbolized without target-specific special cases.

## Acceptance criteria

- [ ] Entry `A1` boot IO request seed is available at boot entry for local-offset bootblocks.
- [ ] Type propagation survives a proven local storage save and reload of the boot IO request pointer.
- [ ] IO request field writes render with symbolic field names for command, offset, length, and data destination.
- [ ] Exec `DoIO` calls remain named through the existing platform call path.
- [ ] Ambiguous or overwritten local storage does not propagate stale IO request type facts.
- [ ] A focused fixture covers save, reload, IO field writes, and `DoIO`.
- [ ] The Epic bootblock no longer shows the relevant IO request setup as raw `$001C/$0024/$0028/$002C(a1)` offsets.
- [ ] Relevant Python and C backend tests pass.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- [0002-001 Stop Bootblock Load Address From Emitting ORG](0002-001-stop-bootblock-load-org.md)
