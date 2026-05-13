# 0002-003 Materialize Bootblock Disk Read Stages

## Parent

[PRD 0002: Bootblock Runtime Address Model](../prd/0002-bootblock-runtime-address-model.md)

## What to build

Recognize concrete bootblock disk reads through typed IO request setup and `DoIO`, then materialize child stage targets only when the parent disk bytes can be sliced exactly. The generated child target should have a truthful source descriptor, load address, entrypoint when known, parent disk provenance, and metadata suitable for normal analysis and reproduction.

This slice is complete when a bootblock `CMD_READ` setup yields a concrete imported stage target instead of only raw literals in the listing.

## Acceptance criteria

- [ ] A typed IO request with `CMD_READ`, data destination, byte length, and disk offset produces a disk-read analysis fact.
- [ ] Disk-read facts include destination address, byte length, disk offset, command name, and source kind.
- [ ] Concrete disk-read facts materialize child targets only when the bytes are available from the parent disk image.
- [ ] Materialized child targets use `runtime_absolute` only when the read destination is a true load address for the child bytes.
- [ ] Inferred-only or incomplete reads do not create child targets.
- [ ] Target manifests list concrete bootblock-read child stages with stable names and provenance.
- [ ] A focused fixture verifies read fact extraction and child source descriptor generation.
- [ ] Relevant import, manifest, and C backend tests pass.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- [0002-002 Symbolize Boot IO Request Setup](0002-002-symbolize-boot-io-request-setup.md)
