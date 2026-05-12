# Virtual Reserved Arena Prototype

Parent issue: `docs/issues/005-002-virtual-reserved-arena-prototype.md`

## Prototype Scope

The prototype is test-only in `src/test_util_arena.c`.

It does not change `Arena`, production allocation behavior, workflow allocation behavior, or
public APIs. It uses Windows `VirtualAlloc`/`VirtualFree` directly inside the unit test to measure
the lifetime model without putting virtual reservation on the production path.

## Measurement

The measured allocation sequence matches the linked-block baseline from
`docs/arena-measurement-report.md`: allocate 32 bytes, then allocate 5000 bytes.

| Arena form | Used bytes | Capacity / committed bytes | Reserved bytes | Waste basis | Notes |
| --- | ---:| ---:| ---:| ---:| --- |
| Current linked-block arena | 5032 | 9096 | n/a | 4064 bytes capacity waste | One 4096-byte head block plus one 5000-byte block. |
| Virtual-reserved prototype | 5032 | page-aligned commit >= 5032 | 65536 | committed minus used | Contiguous address range; commit grows on demand. |

On normal Windows page sizing the prototype commits 8192 bytes for this sequence, so committed
waste is about 3160 bytes. The test asserts only page-aligned behavior, not a fixed page size.

The prototype keeps committed pages after reset and resets `used` to zero. That matches cheap reuse
but does not prove decommit policy, poisoning, or commit shrinking is worth production complexity.

## Fit Analysis

Locality: virtual reservation gives contiguous addresses and stable linear scans. That is attractive
for builders, parse staging, and other append-heavy workflows.

Reservation limits: each arena consumes address space up front. On 64-bit Windows this is usually
cheap, but large or many reservations can fail. Commit also fails independently and must be handled
at every growth point.

Platform assumptions: this prototype uses Windows `VirtualAlloc`. A production version would need a
separate POSIX `mmap` path or a project decision to keep the allocator Windows-only.

API impact: no public API changed in the prototype. A production migration would need either a new
arena implementation behind the existing API or an explicit opt-in factory, because reservation size,
commit policy, reset/decommit policy, and over-reserve behavior are allocator policy.

Failure modes: reserve failure, commit failure, address-space fragmentation, page-granularity waste,
and hard failure at reserve-size exhaustion. Growing beyond the reservation cannot preserve pointers
without changing the lifetime contract.

Rollback cost: rollback is low while the prototype stays test-only. Rollback cost becomes high if
production callers start depending on contiguous stable arena addresses or virtual-memory-specific
stats.

## Decision

Do not migrate the production arena yet. The prototype shows a plausible locality win and slightly
lower committed waste for the measured large transient case, but the current linked-block arena is
not a proven bottleneck. Keep virtual reservation as a measured option for a future workload with a
clear locality or capacity problem.
