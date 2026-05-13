# 0002-004 Materialize Post-Read Runtime Copy Handoffs

## Parent

[PRD 0002: Bootblock Runtime Address Model](../prd/0002-bootblock-runtime-address-model.md)

## What to build

Model post-read bootstrap copies and handoffs as runtime-copy candidates, then materialize ORG/runtime views only when source bytes, destination address, copy extent, and entrypoint evidence are all present. Proven handoff targets should become navigable symbols; weak low-memory trampolines should stay numeric or equated without disruptive ORG output.

This slice is complete when flows like Epic's read into `$1E200`, copy to `$864`, and jump through `$86C` are represented as real runtime views or symbols backed by concrete bytes.

## Acceptance criteria

- [ ] Analysis records post-read memory copy source, destination, and extent when the loop is proven.
- [ ] Runtime-copy candidates are linked to materialized read-stage bytes where possible.
- [ ] ORG is emitted only for runtime-copy ranges with concrete bytes and accepted entrypoint evidence.
- [ ] Absolute handoff targets inside proven copied ranges render as navigable runtime labels or equates.
- [ ] Weak low-memory helpers without full evidence do not emit ORG.
- [ ] The Epic `$1E200 -> $864` copy and `$86C` handoff are covered by a real-target or focused regression.
- [ ] Round-trip reproduction remains exact for affected regenerated source.
- [ ] Relevant C backend tests pass.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- [0002-003 Materialize Bootblock Disk Read Stages](0002-003-materialize-bootblock-disk-read-stages.md)
