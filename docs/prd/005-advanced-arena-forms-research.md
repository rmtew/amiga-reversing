# Advanced Arena Forms Research

## Status

Approved research PRD. Not implementation-ready until measurements justify a production migration.

## Problem

The current linked-block arena is a good baseline, but other arena forms may reduce memory overhead or improve locality for specific workloads. Moving to them without measurements risks adding allocator complexity before proving a bottleneck or lifetime gap.

## Goal

Evaluate advanced arena forms as possible future building blocks and decide, with measurements, whether any should become production work.

## Scope

- Evaluate virtual-reserved contiguous arenas.
- Evaluate growable pool allocators for fixed-size reusable nodes.
- Evaluate per-thread scratch arenas and conflict-avoidance rules.
- Evaluate frame/double-buffer-style arenas for repeated workflows.
- Compare against current linked-block **Workflow Arena**, **Scratch Mark**, **Result Arena**, and **Arena Builder** patterns.

## Non-Goals

- Do not migrate production code in this PRD.
- Do not replace the current arena implementation without an ADR.
- Do not add thread-local scratch arenas without proving concurrency/thread reuse needs.
- Do not optimize for benchmark noise alone.

## Prototype Containment

Prototypes must live outside the production allocation path unless explicitly enabled by a test or measurement-only build flag. They must not change public C APIs, Python/CLI behavior, or default workflow allocation behavior before the ADR decision.

## Acceptance

- Measurements identify current arena block counts, allocated bytes, wasted bytes, and hot allocation sites for representative workflows.
- Each arena form has a fit analysis covering lifetime model, API impact, failure modes, and expected benefit.
- Any recommended production migration has an ADR describing tradeoffs and rollback cost.
- If no form is justified, the PRD closes with a documented no-build decision.

## Later Task Slices

- Measurement harness/report.
- Virtual-reserved arena prototype.
- Pool allocator prototype.
- Scratch/frame arena fit analysis.
- ADR or no-build decision.

## Issues

- [005-001 Arena Measurement Report](../issues/005-001-arena-measurement-report.md)
- [005-002 Virtual Reserved Arena Prototype](../issues/005-002-virtual-reserved-arena-prototype.md)
- [005-003 Growable Pool Prototype](../issues/005-003-growable-pool-prototype.md)
- [005-004 Scratch and Frame Arena Fit Analysis](../issues/005-004-scratch-frame-arena-fit-analysis.md)
- [005-005 Advanced Arena Decision ADR](../issues/005-005-advanced-arena-decision-adr.md)
